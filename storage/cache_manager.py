"""
Cache Management for Diagrams and Templates

Provides in-memory caching for frequently used diagrams and templates
to improve performance and reduce redundant generation.
"""

from typing import Dict, Any, Optional, List
import hashlib
import json
from datetime import datetime, timedelta
from collections import OrderedDict
import asyncio
from utils.logger import setup_logger

logger = setup_logger(__name__)


class CacheManager:
    """
    Manages in-memory cache for diagrams and templates.
    
    Uses LRU (Least Recently Used) eviction policy when cache is full.
    """
    
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 100):
        """
        Initialize cache manager.
        
        Args:
            ttl_seconds: Time-to-live for cache entries in seconds
            max_size: Maximum number of entries in cache
        """
        self.ttl = ttl_seconds
        self.max_size = max_size
        
        # Main cache for diagram results (LRU)
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        
        # Template cache (permanent during runtime)
        self.template_cache: Dict[str, str] = {}
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0
        }
        
        # Start cleanup task
        self._cleanup_task = None
    
    async def start(self):
        """Start background cleanup task."""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            logger.info("Cache manager started with background cleanup")
    
    async def stop(self):
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("Cache manager stopped")
    
    def _generate_key(self, request_data: Dict[str, Any]) -> str:
        """
        Generate deterministic cache key from request data.
        
        Args:
            request_data: Request parameters
            
        Returns:
            MD5 hash as cache key
        """
        # Extract cacheable fields
        key_data = {
            "diagram_type": request_data.get("diagram_type"),
            "content": request_data.get("content"),
            "theme": request_data.get("theme", {}),
            "constraints": request_data.get("constraints", {})
        }
        
        # Create deterministic string
        key_str = json.dumps(key_data, sort_keys=True)
        
        # Generate MD5 hash
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get cached diagram if exists and not expired.
        
        Args:
            request_data: Request parameters
            
        Returns:
            Cached result or None
        """
        key = self._generate_key(request_data)
        
        if key in self.cache:
            entry = self.cache[key]
            
            # Check expiration
            if datetime.utcnow() < entry["expires_at"]:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                
                # Update statistics
                entry["hit_count"] += 1
                entry["last_accessed"] = datetime.utcnow()
                self.stats["hits"] += 1
                
                logger.debug(f"Cache hit for key: {key[:8]}... (hits: {entry['hit_count']})")
                return entry["data"]
            else:
                # Expired, remove
                del self.cache[key]
                self.stats["expirations"] += 1
                logger.debug(f"Cache entry expired for key: {key[:8]}...")
        
        self.stats["misses"] += 1
        return None
    
    def set(self, request_data: Dict[str, Any], result: Dict[str, Any]):
        """
        Cache diagram result.
        
        Args:
            request_data: Request parameters
            result: Generation result to cache
        """
        key = self._generate_key(request_data)
        
        # Check cache size limit
        if len(self.cache) >= self.max_size:
            # Evict least recently used (first item)
            evicted_key = next(iter(self.cache))
            del self.cache[evicted_key]
            self.stats["evictions"] += 1
            logger.debug(f"Evicted cache entry: {evicted_key[:8]}...")
        
        # Add new entry (at end)
        self.cache[key] = {
            "data": result,
            "expires_at": datetime.utcnow() + timedelta(seconds=self.ttl),
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
            "hit_count": 0
        }
        
        logger.debug(f"Cached result for key: {key[:8]}...")
    
    def invalidate(self, request_data: Optional[Dict[str, Any]] = None):
        """
        Invalidate cache entries.
        
        Args:
            request_data: If provided, invalidate specific entry. 
                         If None, clear all cache.
        """
        if request_data:
            key = self._generate_key(request_data)
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"Invalidated cache entry: {key[:8]}...")
        else:
            count = len(self.cache)
            self.cache.clear()
            logger.info(f"Cleared all {count} cache entries")
    
    def clear_expired(self) -> int:
        """
        Remove expired entries.
        
        Returns:
            Number of entries removed
        """
        now = datetime.utcnow()
        expired_keys = [
            k for k, v in self.cache.items() 
            if v["expires_at"] < now
        ]
        
        for key in expired_keys:
            del self.cache[key]
            self.stats["expirations"] += 1
        
        if expired_keys:
            logger.debug(f"Cleared {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    async def _periodic_cleanup(self):
        """Background task to periodically clean expired entries."""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                self.clear_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")
    
    def cache_template(self, template_name: str, content: str):
        """
        Cache SVG template content.
        
        Args:
            template_name: Name of template
            content: SVG content
        """
        self.template_cache[template_name] = content
        logger.debug(f"Cached template: {template_name}")
    
    def get_template(self, template_name: str) -> Optional[str]:
        """
        Get cached template.
        
        Args:
            template_name: Name of template
            
        Returns:
            Template content or None
        """
        return self.template_cache.get(template_name)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Statistics dictionary
        """
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0
        
        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": round(hit_rate, 2),
            "evictions": self.stats["evictions"],
            "expirations": self.stats["expirations"],
            "current_size": len(self.cache),
            "max_size": self.max_size,
            "template_count": len(self.template_cache)
        }
    
    def get_cache_info(self) -> List[Dict[str, Any]]:
        """
        Get information about cached entries.
        
        Returns:
            List of cache entry information
        """
        info = []
        for key, entry in self.cache.items():
            info.append({
                "key": key[:8] + "...",
                "created_at": entry["created_at"].isoformat(),
                "expires_at": entry["expires_at"].isoformat(),
                "hit_count": entry["hit_count"],
                "size_bytes": len(json.dumps(entry["data"]))
            })
        return info