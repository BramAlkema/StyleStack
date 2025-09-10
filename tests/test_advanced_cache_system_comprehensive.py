#!/usr/bin/env python3
"""
Comprehensive test suite for Advanced Cache System

Tests the advanced caching functionality for StyleStack including LRU cache,
TTL handling, compression, and statistics tracking.
"""

import unittest
import time
import threading
import tempfile
import pickle
import json
from pathlib import Path
from unittest.mock import Mock, patch

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))

from tools.advanced_cache_system import (
    CacheEntry,
    CacheStats,
    LRUCache
)


class TestCacheEntry(unittest.TestCase):
    """Test CacheEntry functionality"""
    
    def test_cache_entry_creation(self):
        """Test creating cache entry"""
        entry = CacheEntry(
            value="test_value",
            timestamp=1234567890.0,
            access_count=5,
            size_bytes=100,
            ttl_seconds=300
        )
        
        self.assertEqual(entry.value, "test_value")
        self.assertEqual(entry.timestamp, 1234567890.0)
        self.assertEqual(entry.access_count, 5)
        self.assertEqual(entry.size_bytes, 100)
        self.assertEqual(entry.ttl_seconds, 300)
        
    def test_cache_entry_defaults(self):
        """Test cache entry with default values"""
        entry = CacheEntry(
            value="test",
            timestamp=time.time(),
            access_count=1,
            size_bytes=50
        )
        
        self.assertIsNone(entry.ttl_seconds)
        
    def test_cache_entry_replacement(self):
        """Test cache entry replacement functionality"""
        entry = CacheEntry(
            value="original",
            timestamp=time.time(),
            access_count=1,
            size_bytes=50
        )
        
        # Test _replace method
        updated_entry = entry._replace(access_count=5)
        self.assertEqual(updated_entry.access_count, 5)
        self.assertEqual(updated_entry.value, "original")


class TestCacheStats(unittest.TestCase):
    """Test CacheStats functionality"""
    
    def test_cache_stats_creation(self):
        """Test creating cache stats"""
        stats = CacheStats(
            hits=100,
            misses=25,
            evictions=5,
            size_bytes=1024,
            entry_count=50
        )
        
        self.assertEqual(stats.hits, 100)
        self.assertEqual(stats.misses, 25)
        self.assertEqual(stats.evictions, 5)
        self.assertEqual(stats.size_bytes, 1024)
        self.assertEqual(stats.entry_count, 50)
        
    def test_hit_rate_calculation(self):
        """Test hit rate calculation"""
        stats = CacheStats(hits=80, misses=20)
        self.assertAlmostEqual(stats.hit_rate, 0.8, places=2)
        
        # Test zero case
        stats_zero = CacheStats(hits=0, misses=0)
        self.assertEqual(stats_zero.hit_rate, 0.0)
        
    def test_miss_rate_calculation(self):
        """Test miss rate calculation"""
        stats = CacheStats(hits=80, misses=20)
        self.assertAlmostEqual(stats.miss_rate, 0.2, places=2)
        
    def test_default_stats(self):
        """Test default cache stats"""
        stats = CacheStats()
        self.assertEqual(stats.hits, 0)
        self.assertEqual(stats.misses, 0)
        self.assertEqual(stats.evictions, 0)
        self.assertEqual(stats.size_bytes, 0)
        self.assertEqual(stats.entry_count, 0)


class TestLRUCache(unittest.TestCase):
    """Test LRU Cache functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.cache = LRUCache(max_size=10, max_memory_mb=1.0)
        
    def tearDown(self):
        """Clean up test environment"""
        self.cache.clear()
        
    def test_lru_cache_initialization(self):
        """Test LRU cache initialization"""
        cache = LRUCache(
            max_size=100,
            max_memory_mb=5.0,
            default_ttl_seconds=300,
            enable_compression=True,
            compression_threshold_bytes=512
        )
        
        self.assertEqual(cache.max_size, 100)
        self.assertEqual(cache.max_memory_bytes, 5.0 * 1024 * 1024)
        self.assertEqual(cache.default_ttl_seconds, 300)
        self.assertTrue(cache.enable_compression)
        self.assertEqual(cache.compression_threshold_bytes, 512)
        
    def test_basic_put_get_operations(self):
        """Test basic put and get operations"""
        # Put value
        self.cache.put("key1", "value1")
        
        # Get value
        result = self.cache.get("key1")
        self.assertEqual(result, "value1")
        
        # Get non-existent key
        result = self.cache.get("nonexistent")
        self.assertIsNone(result)
        
    def test_lru_eviction_policy(self):
        """Test LRU eviction policy"""
        # Fill cache to capacity
        for i in range(10):
            self.cache.put(f"key{i}", f"value{i}")
            
        # Add one more item to trigger eviction
        self.cache.put("key10", "value10")
        
        # First item should be evicted
        result = self.cache.get("key0")
        self.assertIsNone(result)
        
        # Last item should still be there
        result = self.cache.get("key10")
        self.assertEqual(result, "value10")
        
    def test_lru_access_pattern(self):
        """Test LRU access pattern behavior"""
        # Fill cache to exact capacity
        for i in range(10):
            self.cache.put(f"key{i}", f"value{i}")
            
        # Access an early key to make it recently used
        self.cache.get("key1")
        
        # Add one more item to trigger eviction
        self.cache.put("key_new", "value_new")
        
        # key1 should still be there (recently accessed)
        self.assertIsNotNone(self.cache.get("key1"))
        
        # Some early key should be evicted (depends on implementation)
        # We'll just check that the cache size is maintained
        self.assertLessEqual(len(self.cache._cache), self.cache.max_size)
        
    def test_ttl_expiration(self):
        """Test TTL-based expiration"""
        # Put item with short TTL
        self.cache.put("expiring_key", "expiring_value", ttl_seconds=0.1)
        
        # Should be available immediately
        result = self.cache.get("expiring_key")
        self.assertEqual(result, "expiring_value")
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Should be expired
        result = self.cache.get("expiring_key")
        self.assertIsNone(result)
        
    def test_cache_statistics(self):
        """Test cache statistics tracking"""
        # Start with clean stats
        self.assertEqual(self.cache.stats.hits, 0)
        self.assertEqual(self.cache.stats.misses, 0)
        
        # Miss
        self.cache.get("nonexistent")
        self.assertEqual(self.cache.stats.misses, 1)
        
        # Put and hit
        self.cache.put("key1", "value1")
        self.cache.get("key1")
        self.assertEqual(self.cache.stats.hits, 1)
        
        # Multiple hits
        self.cache.get("key1")
        self.cache.get("key1")
        self.assertEqual(self.cache.stats.hits, 3)
        
    def test_delete_operation(self):
        """Test delete operation"""
        # Put value
        self.cache.put("key1", "value1")
        self.assertIsNotNone(self.cache.get("key1"))
        
        # Delete value
        result = self.cache.delete("key1")
        self.assertTrue(result)
        self.assertIsNone(self.cache.get("key1"))
        
        # Delete non-existent key
        result = self.cache.delete("nonexistent")
        self.assertFalse(result)
        
    def test_clear_operation(self):
        """Test clear operation"""
        # Add some entries
        for i in range(5):
            self.cache.put(f"key{i}", f"value{i}")
            
        # Verify entries exist
        self.assertEqual(self.cache.stats.entry_count, 5)
        
        # Clear cache
        self.cache.clear()
        
        # Verify cache is empty
        self.assertEqual(self.cache.stats.entry_count, 0)
        self.assertEqual(self.cache.stats.hits, 0)
        self.assertEqual(self.cache.stats.misses, 0)
        
    def test_compression_functionality(self):
        """Test value compression"""
        # Test with compression enabled
        cache_with_compression = LRUCache(
            max_size=10,
            enable_compression=True,
            compression_threshold_bytes=10
        )
        
        # Large value that should be compressed
        large_value = "x" * 100
        cache_with_compression.put("large_key", large_value)
        
        # Should retrieve original value
        result = cache_with_compression.get("large_key")
        self.assertEqual(result, large_value)
        
        # Test with compression disabled
        cache_no_compression = LRUCache(
            max_size=10,
            enable_compression=False
        )
        
        cache_no_compression.put("key", large_value)
        result = cache_no_compression.get("key")
        self.assertEqual(result, large_value)
        
    def test_compression_threshold(self):
        """Test compression threshold behavior"""
        cache = LRUCache(
            max_size=10,
            enable_compression=True,
            compression_threshold_bytes=50
        )
        
        # Small value (below threshold)
        small_value = "small"
        cache.put("small_key", small_value)
        
        # Large value (above threshold) 
        large_value = "x" * 100
        cache.put("large_key", large_value)
        
        # Both should be retrievable correctly
        self.assertEqual(cache.get("small_key"), small_value)
        self.assertEqual(cache.get("large_key"), large_value)
        
    def test_memory_size_tracking(self):
        """Test memory size tracking"""
        # Put some values
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2" * 10)
        
        # Size should be tracked
        self.assertGreater(self.cache.stats.size_bytes, 0)
        self.assertEqual(self.cache.stats.entry_count, 2)
        
        # Delete one entry
        self.cache.delete("key1")
        self.assertEqual(self.cache.stats.entry_count, 1)
        
    def test_memory_limit_enforcement(self):
        """Test memory limit enforcement"""
        # Create cache with very small memory limit
        small_cache = LRUCache(max_size=100, max_memory_mb=0.001)  # 1KB
        
        # Add large values
        for i in range(10):
            large_value = "x" * 200  # 200 bytes each
            small_cache.put(f"key{i}", large_value)
            
        # Cache should respect memory limit
        self.assertLessEqual(small_cache.stats.size_bytes, small_cache.max_memory_bytes * 1.1)
        
    def test_thread_safety(self):
        """Test thread safety of LRU cache"""
        results = []
        errors = []
        
        def worker(thread_id):
            try:
                for i in range(10):
                    key = f"thread_{thread_id}_key_{i}"
                    value = f"thread_{thread_id}_value_{i}"
                    
                    self.cache.put(key, value)
                    result = self.cache.get(key)
                    results.append(result == value)
            except Exception as e:
                errors.append(e)
                
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
            
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
            
        # Check results
        self.assertEqual(len(errors), 0)
        self.assertTrue(all(results))
        
    def test_access_count_tracking(self):
        """Test access count tracking"""
        self.cache.put("key1", "value1")
        
        # First access
        self.cache.get("key1")
        entry = self.cache._cache["key1"]
        self.assertEqual(entry.access_count, 2)  # 1 from put, 1 from get
        
        # Second access
        self.cache.get("key1")
        entry = self.cache._cache["key1"]
        self.assertEqual(entry.access_count, 3)
        
    def test_is_expired_method(self):
        """Test _is_expired method"""
        # Entry without TTL
        entry_no_ttl = CacheEntry(
            value="test",
            timestamp=time.time(),
            access_count=1,
            size_bytes=10
        )
        self.assertFalse(self.cache._is_expired(entry_no_ttl))
        
        # Entry with non-expired TTL
        entry_fresh = CacheEntry(
            value="test",
            timestamp=time.time(),
            access_count=1,
            size_bytes=10,
            ttl_seconds=60
        )
        self.assertFalse(self.cache._is_expired(entry_fresh))
        
        # Entry with expired TTL
        entry_expired = CacheEntry(
            value="test",
            timestamp=time.time() - 120,  # 2 minutes ago
            access_count=1,
            size_bytes=10,
            ttl_seconds=60  # 1 minute TTL
        )
        self.assertTrue(self.cache._is_expired(entry_expired))
        
    def test_enforce_limits_method(self):
        """Test _enforce_limits method"""
        # Fill cache beyond size limit
        for i in range(15):  # Max size is 10
            self.cache.put(f"key{i}", f"value{i}")
            
        # Should not exceed max size
        self.assertLessEqual(len(self.cache._cache), self.cache.max_size)
        
    def test_maybe_maintenance_method(self):
        """Test _maybe_maintenance method"""
        # Set maintenance interval to very small value
        self.cache._maintenance_interval = 0.001
        self.cache._last_maintenance = time.time() - 1  # Force maintenance
        
        # Add entry to trigger maintenance
        self.cache.put("key1", "value1")
        
        # Maintenance should have been called
        self.assertGreater(self.cache._last_maintenance, time.time() - 1)
        
    def test_data_types_support(self):
        """Test support for different data types"""
        test_data = [
            ("string", "hello world"),
            ("integer", 42),
            ("list", [1, 2, 3, "four"]),
            ("dict", {"key": "value", "nested": {"data": True}}),
            ("tuple", (1, 2, "three")),
            ("bytes", b"byte data"),
            ("none", None),
            ("boolean", True)
        ]
        
        for key, value in test_data:
            self.cache.put(key, value)
            result = self.cache.get(key)
            self.assertEqual(result, value, f"Failed for {key}: {value}")
            
    def test_large_value_handling(self):
        """Test handling of large values"""
        # Very large string
        large_string = "x" * 10000  # 10KB
        self.cache.put("large_string", large_string)
        self.assertEqual(self.cache.get("large_string"), large_string)
        
        # Large dict
        large_dict = {f"key{i}": f"value{i}" * 100 for i in range(100)}
        self.cache.put("large_dict", large_dict)
        self.assertEqual(self.cache.get("large_dict"), large_dict)
        
    def test_cache_replacement_behavior(self):
        """Test cache replacement behavior"""
        # Put initial value
        self.cache.put("key1", "original_value")
        self.assertEqual(self.cache.get("key1"), "original_value")
        
        # Replace with new value
        self.cache.put("key1", "new_value")
        self.assertEqual(self.cache.get("key1"), "new_value")
        
        # Should not increase entry count
        self.assertEqual(self.cache.stats.entry_count, 1)


class TestCacheIntegration(unittest.TestCase):
    """Test integrated cache scenarios"""
    
    def test_realistic_usage_pattern(self):
        """Test realistic cache usage patterns"""
        cache = LRUCache(max_size=100, max_memory_mb=1.0, default_ttl_seconds=60)
        
        # Simulate realistic usage
        # 1. Initial data loading
        for i in range(50):
            cache.put(f"user:{i}", {"id": i, "name": f"User{i}", "data": list(range(10))})
            
        # 2. Frequent access to some items
        hot_keys = [f"user:{i}" for i in range(10)]
        for _ in range(5):
            for key in hot_keys:
                cache.get(key)
                
        # 3. Add more data (should evict cold items)
        for i in range(50, 80):
            cache.put(f"user:{i}", {"id": i, "name": f"User{i}", "data": list(range(10))})
            
        # 4. Verify hot items are still there
        for key in hot_keys:
            self.assertIsNotNone(cache.get(key))
            
        # 5. Check hit rate
        self.assertGreater(cache.stats.hit_rate, 0.5)
        
    def test_concurrent_performance(self):
        """Test concurrent cache performance"""
        cache = LRUCache(max_size=1000)
        
        def worker_reads():
            for i in range(100):
                cache.get(f"key{i % 50}")
                
        def worker_writes():
            for i in range(100):
                cache.put(f"key{i}", f"value{i}")
                
        # Pre-populate cache
        for i in range(50):
            cache.put(f"key{i}", f"value{i}")
            
        # Start concurrent workers
        threads = []
        for _ in range(3):
            threads.append(threading.Thread(target=worker_reads))
            threads.append(threading.Thread(target=worker_writes))
            
        start_time = time.time()
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()
        end_time = time.time()
        
        # Should complete in reasonable time
        self.assertLess(end_time - start_time, 5.0)
        
        # Should have reasonable hit rate
        self.assertGreater(cache.stats.hit_rate, 0.3)


class TestCacheEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def test_empty_key_handling(self):
        """Test handling of empty keys"""
        cache = LRUCache()
        
        # Empty string key
        cache.put("", "empty_key_value")
        self.assertEqual(cache.get(""), "empty_key_value")
        
    def test_special_character_keys(self):
        """Test keys with special characters"""
        cache = LRUCache()
        special_keys = [
            "key with spaces",
            "key/with/slashes",
            "key.with.dots",
            "key-with-dashes",
            "key_with_underscores",
            "key@with#symbols$",
            "키 with unicode 🚀"
        ]
        
        for key in special_keys:
            cache.put(key, f"value_for_{key}")
            self.assertEqual(cache.get(key), f"value_for_{key}")
            
    def test_zero_size_cache(self):
        """Test cache with zero max size"""
        cache = LRUCache(max_size=0)
        
        # Should handle gracefully
        cache.put("key1", "value1")
        # With zero size, nothing should be stored
        self.assertIsNone(cache.get("key1"))
        
    def test_negative_ttl(self):
        """Test negative TTL values"""
        cache = LRUCache()
        
        # Negative TTL should expire immediately
        cache.put("key1", "value1", ttl_seconds=-1)
        self.assertIsNone(cache.get("key1"))
        
    def test_very_large_ttl(self):
        """Test very large TTL values"""
        cache = LRUCache()
        
        # Very large TTL
        cache.put("key1", "value1", ttl_seconds=999999999)
        self.assertEqual(cache.get("key1"), "value1")


if __name__ == '__main__':
    unittest.main()