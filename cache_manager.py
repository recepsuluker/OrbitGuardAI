"""
TLE Cache Manager - Redis-based caching for TLE data
Reduces Space-Track.org API calls by caching TLE data with 24-hour TTL
"""

import redis
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class TLECacheManager:
    """
    Redis-based cache manager for TLE data.
    
    Features:
    - Automatic cache key generation from NORAD IDs
    - 24-hour TTL (configurable)
    - JSON serialization
    - Cache hit/miss logging
    """
    
    def __init__(self, redis_url='redis://localhost:6379/0', ttl_hours=24):
        """
        Initialize cache manager.
        
        Args:
            redis_url: Redis connection URL
            ttl_hours: Time-to-live in hours (default: 24)
        """
        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            self.ttl = ttl_hours * 3600  # Convert to seconds
            # Test connection
            self.client.ping()
            logger.info(f"✅ Redis connected: {redis_url}")
        except redis.ConnectionError as e:
            logger.warning(f"❌ Redis connection failed: {e}")
            logger.warning("⚠️  Cache disabled - all requests will hit API")
            self.client = None
    
    def _generate_key(self, norad_ids: List[int]) -> str:
        """
        Generate unique cache key from NORAD ID list.
        
        Args:
            norad_ids: List of NORAD catalog IDs
            
        Returns:
            MD5 hash-based cache key
        """
        sorted_ids = sorted(norad_ids)
        hash_input = ','.join(map(str, sorted_ids))
        return f"tle:{hashlib.md5(hash_input.encode()).hexdigest()}"
    
    def get_tle_data(self, norad_ids: List[int]) -> Optional[Dict]:
        """
        Retrieve TLE data from cache.
        
        Args:
            norad_ids: List of NORAD catalog IDs
            
        Returns:
            Cached TLE data dict, or None if cache miss
        """
        if not self.client:
            return None
            
        key = self._generate_key(norad_ids)
        
        try:
            cached = self.client.get(key)
            
            if cached:
                data = json.loads(cached)
                cache_age = datetime.utcnow() - datetime.fromisoformat(data['cached_at'])
                logger.info(f"✅ Cache HIT: {len(norad_ids)} satellites (age: {cache_age})")
                return data['tle_data']
            
            logger.info(f"❌ Cache MISS: {len(norad_ids)} satellites")
            return None
        except Exception as e:
            logger.error(f"Cache read error: {e}")
            return None
    
    def set_tle_data(self, norad_ids: List[int], tle_data: Dict):
        """
        Store TLE data in cache.
        
        Args:
            norad_ids: List of NORAD catalog IDs
            tle_data: TLE data dictionary to cache
        """
        if not self.client:
            return
            
        key = self._generate_key(norad_ids)
        cache_entry = {
            'tle_data': tle_data,
            'cached_at': datetime.utcnow().isoformat(),
            'norad_ids': norad_ids
        }
        
        try:
            self.client.setex(key, self.ttl, json.dumps(cache_entry))
            logger.info(f"💾 Cached {len(norad_ids)} satellites (TTL: {self.ttl/3600:.1f}h)")
        except Exception as e:
            logger.error(f"Cache write error: {e}")
    
    def invalidate_all(self):
        """
        Clear all TLE cache entries.
        Useful for manual cache refresh.
        """
        if not self.client:
            return
            
        try:
            keys = self.client.keys("tle:*")
            if keys:
                self.client.delete(*keys)
                logger.info(f"🗑️  Deleted {len(keys)} cache entries")
            else:
                logger.info("No cache entries to delete")
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache stats (total_keys, total_memory, etc.)
        """
        if not self.client:
            return {"status": "disabled"}
            
        try:
            keys = self.client.keys("tle:*")
            info = self.client.info('memory')
            
            return {
                "status": "active",
                "total_keys": len(keys),
                "used_memory_mb": info['used_memory'] / (1024 * 1024),
                "ttl_hours": self.ttl / 3600
            }
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    # Test the cache manager
    logging.basicConfig(level=logging.INFO)
    
    cache = TLECacheManager()
    
    # Test data
    test_norad_ids = [25544, 48274, 52740]
    test_tle_data = {
        '25544': {'tle_line1': 'test1', 'tle_line2': 'test2'},
        '48274': {'tle_line1': 'test3', 'tle_line2': 'test4'},
    }
    
    # Test cache miss
    result = cache.get_tle_data(test_norad_ids)
    print(f"Cache miss result: {result}")
    
    # Test cache set
    cache.set_tle_data(test_norad_ids, test_tle_data)
    
    # Test cache hit
    result = cache.get_tle_data(test_norad_ids)
    print(f"Cache hit result: {result}")
    
    # Test stats
    stats = cache.get_cache_stats()
    print(f"Cache stats: {stats}")
