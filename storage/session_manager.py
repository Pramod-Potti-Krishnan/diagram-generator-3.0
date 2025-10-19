"""
Session Management for Diagram Generation

Tracks diagram generation sessions and provides analytics.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DiagramSessionManager:
    """
    Manages diagram generation sessions.
    
    Tracks session lifecycle, diagram counts, and performance metrics.
    """
    
    def __init__(self, storage_client=None, db_operations=None):
        """
        Initialize session manager.
        
        Args:
            storage_client: Optional Supabase storage client
            db_operations: Optional database operations instance
        """
        self.storage_client = storage_client
        self.db_ops = db_operations
        
        # In-memory session tracking
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        # Cleanup task
        self._cleanup_task = None
        
        # Statistics
        self.global_stats = {
            "total_sessions": 0,
            "total_diagrams": 0,
            "total_generation_time_ms": 0,
            "active_sessions": 0
        }
    
    async def start(self):
        """Start background cleanup task."""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            logger.info("Session manager started with background cleanup")
    
    async def stop(self):
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("Session manager stopped")
    
    async def create_session(
        self,
        session_id: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create or retrieve a diagram session.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            metadata: Optional session metadata
            
        Returns:
            Session data
        """
        
        # Check if session exists
        if session_id in self.sessions:
            logger.debug(f"Retrieved existing session: {session_id}")
            return self.sessions[session_id]
        
        # Create new session
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "diagram_count": 0,
            "total_generation_time_ms": 0,
            "diagram_types": {},
            "generation_methods": {},
            "cache_hits": 0,
            "metadata": metadata or {},
            "active": True,
            "diagrams": []  # List of diagram IDs
        }
        
        self.sessions[session_id] = session
        self.global_stats["total_sessions"] += 1
        self.global_stats["active_sessions"] += 1
        
        # Persist to database if available
        if self.db_ops and hasattr(self.db_ops.client, 'table'):
            try:
                await self._persist_session(session)
            except Exception as e:
                logger.warning(f"Failed to persist session to database: {e}")
        
        logger.info(f"Created new diagram session: {session_id}")
        return session
    
    async def update_session(
        self,
        session_id: str,
        diagram_id: str,
        diagram_type: str,
        generation_method: str,
        generation_time_ms: int,
        cache_hit: bool = False
    ):
        """
        Update session with new diagram information.
        
        Args:
            session_id: Session identifier
            diagram_id: Generated diagram ID
            diagram_type: Type of diagram
            generation_method: Method used for generation
            generation_time_ms: Time taken to generate
            cache_hit: Whether result was from cache
        """
        
        if session_id not in self.sessions:
            logger.warning(f"Session not found for update: {session_id}")
            return
        
        session = self.sessions[session_id]
        
        # Update counters
        session["diagram_count"] += 1
        session["total_generation_time_ms"] += generation_time_ms
        session["updated_at"] = datetime.utcnow()
        
        # Track diagram types
        if diagram_type not in session["diagram_types"]:
            session["diagram_types"][diagram_type] = 0
        session["diagram_types"][diagram_type] += 1
        
        # Track generation methods
        if generation_method not in session["generation_methods"]:
            session["generation_methods"][generation_method] = 0
        session["generation_methods"][generation_method] += 1
        
        # Track cache hits
        if cache_hit:
            session["cache_hits"] += 1
        
        # Add to diagram list
        session["diagrams"].append(diagram_id)
        
        # Update last diagram info
        session["last_diagram_id"] = diagram_id
        session["last_diagram_type"] = diagram_type
        session["last_diagram_at"] = datetime.utcnow()
        
        # Update global statistics
        self.global_stats["total_diagrams"] += 1
        self.global_stats["total_generation_time_ms"] += generation_time_ms
        
        logger.debug(f"Updated session {session_id}: diagram #{session['diagram_count']}")
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None
        """
        return self.sessions.get(session_id)
    
    async def close_session(self, session_id: str):
        """
        Mark session as closed.
        
        Args:
            session_id: Session identifier
        """
        
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session["active"] = False
            session["closed_at"] = datetime.utcnow()
            
            # Update global stats
            self.global_stats["active_sessions"] = max(0, self.global_stats["active_sessions"] - 1)
            
            # Persist final state
            if self.db_ops:
                try:
                    await self._persist_session(session, final=True)
                except Exception as e:
                    logger.warning(f"Failed to persist session closure: {e}")
            
            logger.info(f"Closed diagram session: {session_id}")
    
    async def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """
        Get statistics for a specific session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session statistics
        """
        
        session = self.sessions.get(session_id)
        if not session:
            return {}
        
        # Calculate statistics
        duration = (
            session.get("closed_at", datetime.utcnow()) - session["created_at"]
        ).total_seconds()
        
        avg_generation_time = (
            session["total_generation_time_ms"] / session["diagram_count"]
            if session["diagram_count"] > 0 else 0
        )
        
        cache_hit_rate = (
            session["cache_hits"] / session["diagram_count"]
            if session["diagram_count"] > 0 else 0
        )
        
        return {
            "session_id": session_id,
            "user_id": session["user_id"],
            "duration_seconds": round(duration),
            "diagram_count": session["diagram_count"],
            "unique_diagram_types": len(session["diagram_types"]),
            "most_used_type": max(session["diagram_types"], key=session["diagram_types"].get) if session["diagram_types"] else None,
            "generation_methods": session["generation_methods"],
            "avg_generation_time_ms": round(avg_generation_time),
            "total_generation_time_ms": session["total_generation_time_ms"],
            "cache_hit_rate": round(cache_hit_rate, 2),
            "is_active": session["active"]
        }
    
    async def get_user_sessions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent sessions for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of sessions
            
        Returns:
            List of session summaries
        """
        
        user_sessions = [
            s for s in self.sessions.values() 
            if s["user_id"] == user_id
        ]
        
        # Sort by creation date (most recent first)
        user_sessions.sort(key=lambda s: s["created_at"], reverse=True)
        
        # Return limited summaries
        summaries = []
        for session in user_sessions[:limit]:
            summaries.append({
                "session_id": session["session_id"],
                "created_at": session["created_at"].isoformat(),
                "diagram_count": session["diagram_count"],
                "is_active": session["active"]
            })
        
        return summaries
    
    def get_global_statistics(self) -> Dict[str, Any]:
        """
        Get global statistics across all sessions.
        
        Returns:
            Global statistics
        """
        
        avg_generation_time = (
            self.global_stats["total_generation_time_ms"] / self.global_stats["total_diagrams"]
            if self.global_stats["total_diagrams"] > 0 else 0
        )
        
        return {
            "total_sessions": self.global_stats["total_sessions"],
            "active_sessions": self.global_stats["active_sessions"],
            "total_diagrams": self.global_stats["total_diagrams"],
            "avg_generation_time_ms": round(avg_generation_time),
            "total_generation_time_ms": self.global_stats["total_generation_time_ms"],
            "sessions_in_memory": len(self.sessions)
        }
    
    async def cleanup_inactive_sessions(self, inactive_hours: int = 24) -> int:
        """
        Clean up inactive sessions.
        
        Args:
            inactive_hours: Hours of inactivity before cleanup
            
        Returns:
            Number of sessions cleaned up
        """
        
        cutoff_time = datetime.utcnow() - timedelta(hours=inactive_hours)
        sessions_to_remove = []
        
        for session_id, session in self.sessions.items():
            # Check if inactive and old
            if not session["active"] and session.get("closed_at", session["updated_at"]) < cutoff_time:
                sessions_to_remove.append(session_id)
        
        # Remove sessions
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
        
        if sessions_to_remove:
            logger.info(f"Cleaned up {len(sessions_to_remove)} inactive sessions")
        
        return len(sessions_to_remove)
    
    async def _periodic_cleanup(self):
        """Background task to periodically clean inactive sessions."""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour
                await self.cleanup_inactive_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")
    
    async def _persist_session(self, session: Dict[str, Any], final: bool = False):
        """
        Persist session to database.
        
        Args:
            session: Session data
            final: Whether this is final persistence before closure
        """
        
        if not self.db_ops:
            return
        
        try:
            # Prepare data for database
            db_data = {
                "session_id": session["session_id"],
                "user_id": session["user_id"],
                "diagram_count": session["diagram_count"],
                "total_generation_time_ms": session["total_generation_time_ms"],
                "metadata": {
                    "diagram_types": session["diagram_types"],
                    "generation_methods": session["generation_methods"],
                    "cache_hits": session["cache_hits"],
                    "diagrams": session["diagrams"][-10:]  # Last 10 diagrams
                },
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if final:
                db_data["closed_at"] = session.get("closed_at", datetime.utcnow()).isoformat()
            
            # Use upsert (insert or update)
            result = self.db_ops.client.table("diagram_sessions").upsert(
                db_data,
                on_conflict="session_id"
            ).execute()
            
            logger.debug(f"Persisted session {session['session_id']} to database")
            
        except Exception as e:
            logger.error(f"Failed to persist session: {e}")