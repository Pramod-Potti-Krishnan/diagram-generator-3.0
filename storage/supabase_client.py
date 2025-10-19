"""
Supabase Client and Storage Operations for Diagrams

Handles diagram storage in Supabase Storage buckets and provides
a singleton client for database operations.
"""

from typing import Optional, Dict, Any
from supabase import create_client, Client
import uuid
import os
from datetime import datetime
from config import get_settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Global client instance
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get or create the Supabase client instance (singleton pattern).
    
    Returns:
        Supabase client
        
    Raises:
        RuntimeError: If Supabase is not configured or connection fails
    """
    global _supabase_client
    
    if _supabase_client is None:
        settings = get_settings()
        
        # Check if Supabase is configured
        if not settings.supabase_url or settings.supabase_url == "https://test.supabase.co":
            logger.warning(
                "Supabase not configured. Storage features will be disabled. "
                "Please set SUPABASE_URL environment variable in Railway dashboard."
            )
            return None
        
        # Use service key if available for better permissions, otherwise use anon key
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or settings.supabase_anon_key
        
        if not supabase_key:
            logger.warning(
                "Supabase key missing. Storage features will be disabled. "
                "Please set SUPABASE_ANON_KEY or SUPABASE_SERVICE_KEY in Railway dashboard."
            )
            return None
        
        try:
            # Create client with service key for full access
            _supabase_client = create_client(
                settings.supabase_url,
                supabase_key
            )
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise RuntimeError(f"Cannot connect to Supabase: {str(e)}")
    
    return _supabase_client


class DiagramStorage:
    """
    Handles diagram storage in Supabase Storage.
    
    This class manages uploading SVG diagrams to Supabase Storage buckets
    and returns public URLs for access.
    """
    
    def __init__(self, settings=None):
        """
        Initialize diagram storage.
        
        Args:
            settings: Optional settings object, defaults to get_settings()
        """
        settings = settings or get_settings()
        self.client = get_supabase_client()
        self.bucket_name = getattr(settings, 'supabase_bucket', 'diagram-charts')
        self.is_public = getattr(settings, 'storage_public', True)
        self.enabled = self.client is not None
        
        if self.enabled:
            self._ensure_bucket()
        else:
            logger.info("DiagramStorage running without Supabase - using in-memory fallback only")
    
    def _ensure_bucket(self):
        """Ensure the storage bucket exists, create if not."""
        try:
            # List existing buckets
            buckets = self.client.storage.list_buckets()
            bucket_names = [b.name for b in buckets] if buckets else []
            
            if self.bucket_name not in bucket_names:
                # Create bucket
                self.client.storage.create_bucket(
                    self.bucket_name,
                    {"public": self.is_public}
                )
                logger.info(f"Created storage bucket: {self.bucket_name}")
            else:
                logger.debug(f"Storage bucket exists: {self.bucket_name}")
        except Exception as e:
            logger.warning(f"Could not ensure bucket exists: {e}")
            # Continue anyway - bucket might exist but we can't list
    
    async def upload_diagram(
        self,
        svg_content: str,
        diagram_type: str,
        session_id: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Upload SVG diagram to Supabase Storage and return public URL.
        
        Args:
            svg_content: SVG content as string
            diagram_type: Type of diagram (e.g., 'cycle_3_step')
            session_id: Session identifier
            user_id: User identifier
            metadata: Optional metadata to include
            
        Returns:
            Public URL to the uploaded diagram, or empty string if storage disabled
            
        Raises:
            Exception: If upload fails
        """

        # Log incoming SVG content size
        logger.info(f"upload_diagram called with SVG content size: {len(svg_content) if svg_content else 0} bytes")

        # Return empty string if Supabase is not configured
        if not self.enabled:
            logger.debug("Supabase storage disabled - returning empty URL")
            return ""
        
        # Generate unique file path
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        file_name = f"{user_id}/{session_id}/{diagram_type}_{timestamp}_{unique_id}.svg"
        
        try:
            # Prepare file options
            file_options = {
                "content-type": "image/svg+xml",
                "cache-control": "public, max-age=3600",
            }
            
            # Add metadata if provided
            if metadata:
                file_options["x-metadata"] = str(metadata)
            
            # Log before upload
            encoded_content = svg_content.encode('utf-8')
            logger.info(f"Uploading to Supabase: {file_name}, encoded size: {len(encoded_content)} bytes")

            # Upload to storage
            response = self.client.storage.from_(self.bucket_name).upload(
                file_name,
                encoded_content,
                file_options
            )

            logger.info(f"Supabase upload response: {response}")
            
            # Get public URL
            if self.is_public:
                url = self.client.storage.from_(self.bucket_name).get_public_url(file_name)
            else:
                # For private buckets, generate signed URL
                url_response = self.client.storage.from_(self.bucket_name).create_signed_url(
                    file_name,
                    expires_in=3600  # 1 hour expiry
                )
                url = url_response.get('signedURL', '')
            
            logger.info(f"Uploaded diagram to: {url}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to upload diagram: {e}")
            raise
    
    async def download_diagram(self, file_path: str) -> Optional[str]:
        """
        Download diagram from storage.
        
        Args:
            file_path: Path to file in bucket
            
        Returns:
            SVG content as string or None if not found
        """
        try:
            response = self.client.storage.from_(self.bucket_name).download(file_path)
            if response:
                return response.decode('utf-8')
            return None
        except Exception as e:
            logger.error(f"Failed to download diagram: {e}")
            return None
    
    async def delete_diagram(self, file_path: str) -> bool:
        """
        Delete diagram from storage.
        
        Args:
            file_path: Path to file in bucket
            
        Returns:
            True if deleted successfully
        """
        try:
            self.client.storage.from_(self.bucket_name).remove([file_path])
            logger.info(f"Deleted diagram: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete diagram: {e}")
            return False
    
    async def list_user_diagrams(self, user_id: str, limit: int = 100) -> list:
        """
        List all diagrams for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of results
            
        Returns:
            List of file metadata
        """
        try:
            response = self.client.storage.from_(self.bucket_name).list(
                path=user_id,
                options={"limit": limit, "sortBy": {"column": "created_at", "order": "desc"}}
            )
            return response if response else []
        except Exception as e:
            logger.error(f"Failed to list user diagrams: {e}")
            return []