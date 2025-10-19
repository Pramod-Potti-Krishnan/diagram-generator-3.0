"""
Database Operations for Diagram Metadata

Manages storing and retrieving diagram metadata in Supabase database tables.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid
import hashlib
import json
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DiagramOperations:
    """
    Database operations for diagram metadata.
    
    Handles CRUD operations for diagram records and caching.
    """
    
    def __init__(self, client):
        """
        Initialize with Supabase client.
        
        Args:
            client: Supabase client instance (can be None if not configured)
        """
        self.client = client
        self.enabled = client is not None
        self.table = "generated_diagrams"
        self.cache_table = "diagram_cache"
        
        if not self.enabled:
            logger.info("DiagramOperations running without database - metadata will not be persisted")
    
    async def save_diagram_metadata(
        self,
        session_id: str,
        user_id: str,
        diagram_type: str,
        url: str,
        generation_method: str,
        request_params: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> str:
        """
        Save diagram metadata to database.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            diagram_type: Type of diagram
            url: Public URL to diagram in storage
            generation_method: Method used (svg_template, mermaid, python_chart)
            request_params: Original request parameters
            metadata: Generation metadata
            
        Returns:
            Diagram ID
            
        Raises:
            Exception: If save fails
        """
        
        diagram_id = str(uuid.uuid4())
        
        # Return ID without saving if database is not available
        if not self.enabled:
            logger.debug(f"Database disabled - returning diagram ID without persisting: {diagram_id}")
            return diagram_id
        
        # Convert datetime objects to ISO format strings
        import json
        
        def serialize_datetime(obj):
            """JSON serializer for datetime objects"""
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
        
        # Serialize request_params and metadata to handle datetime objects
        serialized_params = json.loads(json.dumps(request_params, default=serialize_datetime))
        serialized_metadata = json.loads(json.dumps(metadata, default=serialize_datetime))
        
        data = {
            "id": diagram_id,
            "session_id": session_id,
            "user_id": user_id,
            "diagram_type": diagram_type,
            "url": url,
            "generation_method": generation_method,
            "request_params": serialized_params,
            "metadata": serialized_metadata,
            "quality_score": metadata.get("quality_score"),
            "generation_time_ms": metadata.get("generation_time_ms"),
            "tokens_used": metadata.get("tokens_used"),
            "cache_hit": metadata.get("cache_hit", False),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        try:
            result = self.client.table(self.table).insert(data).execute()
            logger.info(f"Saved diagram metadata: {diagram_id}")
            
            # Also update cache table if this was a cache miss
            if not data["cache_hit"]:
                await self._update_cache_entry(diagram_id, request_params)
            
            return diagram_id
        except Exception as e:
            logger.error(f"Failed to save diagram metadata: {e}")
            raise
    
    async def get_diagram(self, diagram_id: str) -> Optional[Dict[str, Any]]:
        """
        Get diagram by ID.
        
        Args:
            diagram_id: Diagram identifier
            
        Returns:
            Diagram data or None if not found
        """
        try:
            result = self.client.table(self.table).select("*").eq("id", diagram_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to get diagram {diagram_id}: {e}")
            return None
    
    async def get_cached_diagram(self, request_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if a similar diagram exists in cache.
        
        Args:
            request_params: Request parameters to match
            
        Returns:
            Cached diagram data or None
        """
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(request_params)
            
            # Check cache table
            cache_result = self.client.table(self.cache_table).select("*").eq("cache_key", cache_key).execute()
            
            if cache_result.data:
                cache_entry = cache_result.data[0]
                
                # Check if not expired
                expires_at = datetime.fromisoformat(cache_entry["expires_at"])
                if expires_at > datetime.utcnow():
                    # Update hit count
                    self.client.table(self.cache_table).update({
                        "hit_count": cache_entry["hit_count"] + 1,
                        "last_accessed": datetime.utcnow().isoformat()
                    }).eq("cache_key", cache_key).execute()
                    
                    # Get the actual diagram
                    diagram = await self.get_diagram(cache_entry["diagram_id"])
                    if diagram:
                        logger.info(f"Cache hit for diagram {cache_entry['diagram_id']}")
                        return diagram
            
            return None
        except Exception as e:
            logger.error(f"Failed to check cache: {e}")
            return None
    
    async def search_similar_diagrams(
        self,
        diagram_type: str,
        user_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar diagrams by type and user.
        
        Args:
            diagram_type: Type of diagram
            user_id: User identifier
            limit: Maximum results
            
        Returns:
            List of similar diagrams
        """
        try:
            result = (
                self.client.table(self.table)
                .select("*")
                .eq("diagram_type", diagram_type)
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to search diagrams: {e}")
            return []
    
    async def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get usage statistics for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Statistics dictionary
        """
        try:
            # Get all user diagrams
            result = self.client.table(self.table).select("*").eq("user_id", user_id).execute()
            
            if not result.data:
                return {
                    "total_diagrams": 0,
                    "diagram_types": {},
                    "generation_methods": {},
                    "cache_hit_rate": 0
                }
            
            diagrams = result.data
            
            # Calculate statistics
            stats = {
                "total_diagrams": len(diagrams),
                "diagram_types": {},
                "generation_methods": {},
                "total_generation_time_ms": 0,
                "cache_hits": 0,
                "cache_hit_rate": 0
            }
            
            for diagram in diagrams:
                # Count by type
                dtype = diagram.get("diagram_type", "unknown")
                stats["diagram_types"][dtype] = stats["diagram_types"].get(dtype, 0) + 1
                
                # Count by method
                method = diagram.get("generation_method", "unknown")
                stats["generation_methods"][method] = stats["generation_methods"].get(method, 0) + 1
                
                # Sum generation time
                if diagram.get("generation_time_ms"):
                    stats["total_generation_time_ms"] += diagram["generation_time_ms"]
                
                # Count cache hits
                if diagram.get("cache_hit"):
                    stats["cache_hits"] += 1
            
            # Calculate cache hit rate
            if stats["total_diagrams"] > 0:
                stats["cache_hit_rate"] = stats["cache_hits"] / stats["total_diagrams"]
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get user statistics: {e}")
            return {}
    
    async def cleanup_old_diagrams(self, days: int = 30) -> int:
        """
        Clean up diagrams older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of deleted records
        """
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            # Delete old records
            result = self.client.table(self.table).delete().lt("created_at", cutoff_date).execute()
            
            count = len(result.data) if result.data else 0
            logger.info(f"Cleaned up {count} old diagrams")
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old diagrams: {e}")
            return 0
    
    def _generate_cache_key(self, request_params: Dict[str, Any]) -> str:
        """
        Generate a deterministic cache key from request parameters.
        
        Args:
            request_params: Request parameters
            
        Returns:
            MD5 hash as cache key
        """
        # Extract relevant fields for caching
        cache_data = {
            "diagram_type": request_params.get("diagram_type"),
            "content": request_params.get("content"),
            "theme": request_params.get("theme", {})
        }
        
        # Create deterministic string
        cache_str = json.dumps(cache_data, sort_keys=True)
        
        # Generate MD5 hash
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    async def _update_cache_entry(self, diagram_id: str, request_params: Dict[str, Any]):
        """
        Update or create cache entry for diagram.
        
        Args:
            diagram_id: Diagram identifier
            request_params: Request parameters
        """
        try:
            cache_key = self._generate_cache_key(request_params)
            expires_at = (datetime.utcnow() + timedelta(hours=24)).isoformat()
            
            # Try to update existing entry
            existing = self.client.table(self.cache_table).select("*").eq("cache_key", cache_key).execute()
            
            if existing.data:
                # Update existing
                self.client.table(self.cache_table).update({
                    "diagram_id": diagram_id,
                    "expires_at": expires_at,
                    "last_accessed": datetime.utcnow().isoformat()
                }).eq("cache_key", cache_key).execute()
            else:
                # Create new entry
                self.client.table(self.cache_table).insert({
                    "cache_key": cache_key,
                    "diagram_id": diagram_id,
                    "hit_count": 0,
                    "expires_at": expires_at,
                    "created_at": datetime.utcnow().isoformat(),
                    "last_accessed": datetime.utcnow().isoformat()
                }).execute()
                
        except Exception as e:
            logger.warning(f"Failed to update cache entry: {e}")