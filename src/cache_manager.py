"""
Cache Manager Module
File-based caching system with TTL support
"""

import json
import hashlib
import time
from pathlib import Path
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """File-based cache manager with TTL support"""
    
    def __init__(self, cache_dir: str = "./cache", 
                 default_ttl: int = 86400,
                 max_entries: int = 1000):
        """
        Initialize cache manager
        
        Args:
            cache_dir: Directory for cache files
            default_ttl: Default time-to-live in seconds (24 hours)
            max_entries: Maximum number of cache entries
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.default_ttl = default_ttl
        self.max_entries = max_entries
        
        # In-memory cache for frequently accessed items
        self._memory_cache: Dict[str, tuple] = {}
        
        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'writes': 0
        }
        
        logger.info(f"Cache manager initialized at {self.cache_dir}")
    
    def _get_cache_key(self, key: str) -> str:
        """
        Generate cache key hash
        
        Args:
            key: Original key
            
        Returns:
            Hashed key
        """
        return hashlib.md5(key.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, key: str) -> Path:
        """
        Get file path for cache key
        
        Args:
            key: Cache key
            
        Returns:
            Path to cache file
        """
        cache_key = self._get_cache_key(key)
        return self.cache_dir / f"{cache_key}.json"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        # Check memory cache first
        if key in self._memory_cache:
            value, expiry = self._memory_cache[key]
            if time.time() < expiry:
                self.stats['hits'] += 1
                logger.debug(f"Memory cache hit for key: {key[:50]}")
                return value
            else:
                # Remove expired entry
                del self._memory_cache[key]
        
        # Check file cache
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            self.stats['misses'] += 1
            logger.debug(f"Cache miss for key: {key[:50]}")
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check expiry
            if time.time() > cache_data['expiry']:
                logger.debug(f"Cache expired for key: {key[:50]}")
                cache_path.unlink()  # Delete expired cache
                self.stats['misses'] += 1
                return None
            
            # Store in memory cache for quick access
            self._memory_cache[key] = (cache_data['value'], cache_data['expiry'])
            
            self.stats['hits'] += 1
            logger.debug(f"File cache hit for key: {key[:50]}")
            return cache_data['value']
            
        except (json.JSONDecodeError, KeyError, IOError) as e:
            logger.warning(f"Error reading cache: {e}")
            # Delete corrupted cache
            cache_path.unlink(missing_ok=True)
            self.stats['misses'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        if ttl is None:
            ttl = self.default_ttl
        
        expiry = time.time() + ttl
        
        # Store in memory cache
        self._memory_cache[key] = (value, expiry)
        
        # Store in file cache
        cache_path = self._get_cache_path(key)
        
        cache_data = {
            'key': key,
            'value': value,
            'expiry': expiry,
            'created_at': time.time()
        }
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            self.stats['writes'] += 1
            logger.debug(f"Cached value for key: {key[:50]} (TTL: {ttl}s)")
            
            # Cleanup if too many entries
            self._cleanup_if_needed()
            
        except IOError as e:
            logger.error(f"Error writing cache: {e}")
    
    def delete(self, key: str):
        """
        Delete value from cache
        
        Args:
            key: Cache key
        """
        # Remove from memory cache
        self._memory_cache.pop(key, None)
        
        # Remove from file cache
        cache_path = self._get_cache_path(key)
        cache_path.unlink(missing_ok=True)
        
        logger.debug(f"Deleted cache for key: {key[:50]}")
    
    def clear(self):
        """Clear all cache"""
        # Clear memory cache
        self._memory_cache.clear()
        
        # Clear file cache
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
        
        logger.info("Cache cleared")
    
    def _cleanup_if_needed(self):
        """Cleanup old cache files if max entries exceeded"""
        cache_files = list(self.cache_dir.glob("*.json"))
        
        if len(cache_files) <= self.max_entries:
            return
        
        logger.info(f"Cleaning up cache (current: {len(cache_files)}, max: {self.max_entries})")
        
        # Sort by modification time (oldest first)
        cache_files.sort(key=lambda p: p.stat().st_mtime)
        
        # Remove oldest files
        num_to_remove = len(cache_files) - self.max_entries
        for cache_file in cache_files[:num_to_remove]:
            cache_file.unlink()
        
        logger.info(f"Removed {num_to_remove} old cache files")
    
    def cleanup_expired(self):
        """Remove all expired cache files"""
        current_time = time.time()
        removed = 0
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                if current_time > cache_data['expiry']:
                    cache_file.unlink()
                    removed += 1
                    
            except (json.JSONDecodeError, KeyError, IOError):
                # Remove corrupted files
                cache_file.unlink()
                removed += 1
        
        if removed > 0:
            logger.info(f"Cleaned up {removed} expired cache files")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        cache_files = list(self.cache_dir.glob("*.json"))
        
        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'writes': self.stats['writes'],
            'hit_rate': f"{hit_rate:.2f}%",
            'total_entries': len(cache_files),
            'memory_cache_size': len(self._memory_cache)
        }
    
    def get_cache_ttl_for_query(self, query: str) -> int:
        """
        Determine appropriate TTL based on query type
        
        Args:
            query: Search query
            
        Returns:
            TTL in seconds
        """
        query_lower = query.lower()
        
        # News/time-sensitive queries: 1 hour
        time_sensitive_keywords = ['latest', 'current', 'today', 'now', 'news', 'weather']
        if any(keyword in query_lower for keyword in time_sensitive_keywords):
            return 3600  # 1 hour
        
        # Statistical/historical data: 7 days
        static_keywords = ['history', 'statistics', 'data', 'report']
        if any(keyword in query_lower for keyword in static_keywords):
            return 604800  # 7 days
        
        # Default: 24 hours
        return 86400


# Singleton instance
_cache_instance = None

def get_cache_manager(cache_dir: str = "./cache", 
                      default_ttl: int = 86400,
                      max_entries: int = 1000) -> CacheManager:
    """
    Get or create global cache manager instance
    
    Args:
        cache_dir: Cache directory
        default_ttl: Default TTL
        max_entries: Max cache entries
        
    Returns:
        CacheManager instance
    """
    global _cache_instance
    
    if _cache_instance is None:
        _cache_instance = CacheManager(cache_dir, default_ttl, max_entries)
    
    return _cache_instance
