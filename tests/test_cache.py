"""
Unit tests for cache_manager.py
Run with: pytest tests/test_cache.py
"""

import pytest
import time
from cache_manager import TLECacheManager


@pytest.fixture
def cache():
    """Fixture to create a fresh cache instance for each test."""
    return TLECacheManager(ttl_hours=24)


def test_cache_initialization(cache):
    """Test that cache initializes correctly."""
    assert cache is not None
    assert cache.ttl == 24 * 3600  # 24 hours in seconds


def test_cache_miss(cache):
    """Test cache miss scenario."""
    result = cache.get_tle_data([99999, 99998])
    assert result is None


def test_cache_set_and_get(cache):
    """Test cache write and read."""
    test_data = {
        '25544': {
            'OBJECT_NAME': 'ISS (ZARYA)',
            'TLE_LINE1': '1 25544U 98067A...',
            'TLE_LINE2': '2 25544  51.6416...'
        }
    }
    
    norad_ids = [25544]
    
    # Write to cache
    cache.set_tle_data(norad_ids, test_data)
    
    # Read from cache
    retrieved = cache.get_tle_data(norad_ids)
    
    assert retrieved is not None
    assert retrieved == test_data


def test_cache_key_consistency(cache):
    """Test that same NORAD IDs generate same cache key."""
    norad_ids_1 = [25544, 48274, 52740]
    norad_ids_2 = [52740, 25544, 48274]  # Different order
    
    key1 = cache._generate_key(norad_ids_1)
    key2 = cache._generate_key(norad_ids_2)
    
    # Should be the same (sorted internally)
    assert key1 == key2


def test_cache_expiration():
    """Test that cache entries expire after TTL."""
    # Create cache with very short TTL (0.5 seconds)
    short_cache = TLECacheManager(ttl_hours=0.5/3600)
    
    test_data = {'25544': {'name': 'ISS'}}
    short_cache.set_tle_data([25544], test_data)
    
    # Should be available immediately
    result1 = short_cache.get_tle_data([25544])
    assert result1 is not None
    
    # Wait for expiration
    time.sleep(1)
    
    # Should be expired
    result2 = short_cache.get_tle_data([25544])
    assert result2 is None


def test_cache_invalidation(cache):
    """Test manual cache invalidation."""
    # Add some data
    cache.set_tle_data([25544], {'25544': {'name': 'ISS'}})
    cache.set_tle_data([48274], {'48274': {'name': 'STARLINK'}})
    
    # Verify it's cached
    assert cache.get_tle_data([25544]) is not None
    
    # Invalidate all
    cache.invalidate_all()
    
    # Should be gone
    assert cache.get_tle_data([25544]) is None
    assert cache.get_tle_data([48274]) is None


def test_cache_stats(cache):
    """Test cache statistics."""
    # Add some entries
    cache.set_tle_data([25544], {'test': 'data1'})
    cache.set_tle_data([48274], {'test': 'data2'})
    
    stats = cache.get_cache_stats()
    
    assert stats['status'] == 'active'
    assert stats['total_keys'] >= 2
    assert 'used_memory_mb' in stats


def test_multiple_satellites(cache):
    """Test caching multiple satellites."""
    norad_ids = [25544, 48274, 52740, 55012, 56210]
    
    test_data = {
        str(nid): {'OBJECT_NAME': f'SAT-{nid}'}
        for nid in norad_ids
    }
    
    cache.set_tle_data(norad_ids, test_data)
    retrieved = cache.get_tle_data(norad_ids)
    
    assert len(retrieved) == len(test_data)
    assert all(str(nid) in retrieved for nid in norad_ids)


def test_cache_resilience_no_redis():
    """Test that cache gracefully handles Redis not being available."""
    # Use invalid Redis URL
    bad_cache = TLECacheManager(redis_url='redis://invalid:9999/0')
    
    # Should not crash
    result = bad_cache.get_tle_data([25544])
    assert result is None
    
    # Should not crash on write
    bad_cache.set_tle_data([25544], {'test': 'data'})
    
    # Stats should show disabled
    stats = bad_cache.get_cache_stats()
    assert stats['status'] == 'disabled'
