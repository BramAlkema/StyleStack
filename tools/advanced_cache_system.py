#!/usr/bin/env python3
"""
StyleStack Advanced Caching System

Enhanced caching system for XPath resolution, namespace detection, and operation results.
Provides intelligent cache management, persistence, and optimization for production workloads.
"""


from typing import Any, Dict, List, Optional, Set, Tuple, NamedTuple
import time
import json
import pickle
import hashlib
import threading
import weakref
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from lxml import etree
import logging
from datetime import datetime, timedelta
import sqlite3
import zlib
from dataclasses import dataclass
from collections import OrderedDict

logger = logging.getLogger(__name__)


class CacheEntry(NamedTuple):
    """Container for a cache entry with metadata."""
    value: Any
    timestamp: float
    access_count: int
    size_bytes: int
    ttl_seconds: Optional[float] = None


@dataclass
class CacheStats:
    """Statistics for cache performance."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size_bytes: int = 0
    entry_count: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    @property
    def miss_rate(self) -> float:
        return 1.0 - self.hit_rate


class LRUCache:
    """
    Enhanced LRU cache with TTL, size limits, and statistics.
    
    Features:
    - Time-based expiration (TTL)
    - Size-based eviction
    - Access frequency tracking
    - Thread-safe operations
    - Compression for large values
    """
    
    def __init__(self, 
                 max_size: int = 1000,
                 max_memory_mb: float = 100.0,
                 default_ttl_seconds: Optional[float] = None,
                 enable_compression: bool = True,
                 compression_threshold_bytes: int = 1024):
        """Initialize the LRU cache."""
        self.max_size = max_size
        self.max_memory_bytes = int(max_memory_mb * 1024 * 1024)
        self.default_ttl_seconds = default_ttl_seconds
        self.enable_compression = enable_compression
        self.compression_threshold_bytes = compression_threshold_bytes
        
        # Cache storage using OrderedDict for LRU ordering
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        
        # Statistics
        self.stats = CacheStats()
        
        # Background maintenance
        self._last_maintenance = time.time()
        self._maintenance_interval = 60.0  # seconds
        
        logger.debug(f"Initialized LRU cache with {max_size} entries, {max_memory_mb}MB limit")
    
    def get(self, key: str) -> Any:
        """Get value from cache."""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                
                # Check TTL expiration
                if self._is_expired(entry):
                    del self._cache[key]
                    self.stats.misses += 1
                    self.stats.evictions += 1
                    return None
                
                # Move to end (most recently used)
                self._cache.move_to_end(key)
                
                # Update access count and statistics
                updated_entry = entry._replace(access_count=entry.access_count + 1)
                self._cache[key] = updated_entry
                self.stats.hits += 1
                
                # Decompress if needed
                value = self._decompress_value(updated_entry.value)
                return value
            else:
                self.stats.misses += 1
                return None
    
    def put(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        """Put value into cache."""
        with self._lock:
            # Calculate value size and compress if needed
            compressed_value, size_bytes = self._compress_value(value)
            
            # Determine TTL
            effective_ttl = ttl_seconds or self.default_ttl_seconds
            
            # Create cache entry
            entry = CacheEntry(
                value=compressed_value,
                timestamp=time.time(),
                access_count=1,
                size_bytes=size_bytes,
                ttl_seconds=effective_ttl
            )
            
            # Remove existing entry if present
            if key in self._cache:
                old_entry = self._cache[key]
                self.stats.size_bytes -= old_entry.size_bytes
                del self._cache[key]
            
            # Add new entry
            self._cache[key] = entry
            self.stats.size_bytes += size_bytes
            self.stats.entry_count = len(self._cache)
            
            # Enforce size limits
            self._enforce_limits()
            
            # Periodic maintenance
            self._maybe_maintenance()
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                self.stats.size_bytes -= entry.size_bytes
                del self._cache[key]
                self.stats.entry_count = len(self._cache)
                self.stats.evictions += 1
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self.stats = CacheStats()
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry has expired."""
        if entry.ttl_seconds is None:
            return False
        
        age = time.time() - entry.timestamp
        return age > entry.ttl_seconds
    
    def _compress_value(self, value: Any) -> Tuple[Any, int]:
        """Compress value if it's large enough and compression is enabled."""
        if not self.enable_compression:
            # Estimate size without compression
            size_bytes = len(str(value).encode('utf-8'))
            return value, size_bytes
        
        # Serialize value to bytes
        try:
            if isinstance(value, (str, bytes)):
                data = value.encode('utf-8') if isinstance(value, str) else value
            else:
                data = pickle.dumps(value)
            
            # Compress if above threshold
            if len(data) >= self.compression_threshold_bytes:
                compressed_data = zlib.compress(data)
                return ('__compressed__', compressed_data), len(compressed_data)
            else:
                return value, len(data)
        
        except Exception as e:
            logger.warning(f"Failed to compress cache value: {e}")
            size_bytes = len(str(value).encode('utf-8'))
            return value, size_bytes
    
    def _decompress_value(self, stored_value: Any) -> Any:
        """Decompress value if it was compressed."""
        if (isinstance(stored_value, tuple) and 
            len(stored_value) == 2 and 
            stored_value[0] == '__compressed__'):
            
            try:
                decompressed_data = zlib.decompress(stored_value[1])
                # Try to unpickle, fallback to decode as string
                try:
                    return pickle.loads(decompressed_data)
                except:
                    return decompressed_data.decode('utf-8')
            except Exception as e:
                logger.warning(f"Failed to decompress cache value: {e}")
                return None
        
        return stored_value
    
    def _enforce_limits(self) -> None:
        """Enforce cache size and memory limits."""
        # Remove expired entries first
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self._cache.items():
            if self._is_expired(entry):
                expired_keys.append(key)
        
        for key in expired_keys:
            entry = self._cache[key]
            self.stats.size_bytes -= entry.size_bytes
            del self._cache[key]
            self.stats.evictions += 1
        
        # Enforce entry count limit (LRU eviction)
        while len(self._cache) > self.max_size:
            key, entry = self._cache.popitem(last=False)  # Remove least recently used
            self.stats.size_bytes -= entry.size_bytes
            self.stats.evictions += 1
        
        # Enforce memory limit (LRU eviction)
        while self.stats.size_bytes > self.max_memory_bytes:
            if not self._cache:
                break
            key, entry = self._cache.popitem(last=False)
            self.stats.size_bytes -= entry.size_bytes
            self.stats.evictions += 1
        
        # Update entry count
        self.stats.entry_count = len(self._cache)
    
    def _maybe_maintenance(self) -> None:
        """Perform periodic maintenance if needed."""
        current_time = time.time()
        if current_time - self._last_maintenance > self._maintenance_interval:
            self._enforce_limits()
            self._last_maintenance = current_time
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            return {
                'hits': self.stats.hits,
                'misses': self.stats.misses,
                'evictions': self.stats.evictions,
                'hit_rate': self.stats.hit_rate,
                'entry_count': self.stats.entry_count,
                'size_bytes': self.stats.size_bytes,
                'size_mb': self.stats.size_bytes / (1024 * 1024),
                'max_size': self.max_size,
                'max_memory_mb': self.max_memory_bytes / (1024 * 1024),
                'compression_enabled': self.enable_compression
            }
    
    def get_top_accessed_keys(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most frequently accessed cache keys."""
        with self._lock:
            items = [(key, entry.access_count) for key, entry in self._cache.items()]
            return sorted(items, key=lambda x: x[1], reverse=True)[:limit]


class XPathCache(LRUCache):
    """Specialized cache for XPath expressions and compiled objects."""
    
    def __init__(self, max_size: int = 500, max_memory_mb: float = 50.0):
        """Initialize XPath cache."""
        super().__init__(max_size=max_size, max_memory_mb=max_memory_mb, default_ttl_seconds=3600)
        self.compilation_stats = {'success': 0, 'errors': 0}
    
    def get_compiled_xpath(self, xpath_expression: str, namespaces: Optional[Dict[str, str]] = None) -> Optional[etree.XPath]:
        """Get or create compiled XPath expression."""
        # Create cache key including namespaces
        namespace_key = json.dumps(namespaces or {}, sort_keys=True)
        cache_key = f"xpath:{hashlib.md5((xpath_expression + namespace_key).encode()).hexdigest()}"
        
        # Try to get from cache
        compiled_xpath = self.get(cache_key)
        if compiled_xpath is not None:
            return compiled_xpath
        
        # Compile XPath expression
        try:
            compiled_xpath = etree.XPath(xpath_expression, namespaces=namespaces)
            self.put(cache_key, compiled_xpath)
            self.compilation_stats['success'] += 1
            return compiled_xpath
        except Exception as e:
            logger.debug(f"Failed to compile XPath '{xpath_expression}': {e}")
            self.compilation_stats['errors'] += 1
            return None
    
    def get_compilation_stats(self) -> Dict[str, int]:
        """Get XPath compilation statistics."""
        return self.compilation_stats.copy()


class NamespaceCache(LRUCache):
    """Specialized cache for namespace detection and mapping."""
    
    def __init__(self, max_size: int = 200, max_memory_mb: float = 20.0):
        """Initialize namespace cache."""
        super().__init__(max_size=max_size, max_memory_mb=max_memory_mb, default_ttl_seconds=1800)
    
    def get_document_namespaces(self, document_hash: str) -> Optional[Dict[str, str]]:
        """Get cached namespaces for a document."""
        return self.get(f"ns:{document_hash}")
    
    def cache_document_namespaces(self, document_hash: str, namespaces: Dict[str, str]) -> None:
        """Cache namespaces for a document."""
        self.put(f"ns:{document_hash}", namespaces)
    
    def extract_and_cache_namespaces(self, xml_doc: etree._Element) -> Dict[str, str]:
        """Extract namespaces from XML document and cache them."""
        # Create document hash for caching
        doc_string = etree.tostring(xml_doc, encoding='unicode')[:1000]  # First 1KB for hashing
        doc_hash = hashlib.md5(doc_string.encode()).hexdigest()
        
        # Check cache first
        cached_namespaces = self.get_document_namespaces(doc_hash)
        if cached_namespaces is not None:
            return cached_namespaces
        
        # Extract namespaces
        namespaces = {}
        
        # Get namespaces from root element
        if xml_doc.nsmap:
            for prefix, uri in xml_doc.nsmap.items():
                if prefix is not None:
                    namespaces[prefix] = uri
                else:
                    namespaces['default'] = uri
        
        # Add common OOXML namespaces if not present
        common_namespaces = {
            'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
            'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
            'sl': 'http://schemas.openxmlformats.org/schemaLibrary/2006/main'
        }
        
        for prefix, uri in common_namespaces.items():
            if prefix not in namespaces:
                # Check if URI is present in the document
                if uri in xml_doc.nsmap.values() or uri in doc_string:
                    namespaces[prefix] = uri
        
        # Cache the result
        self.cache_document_namespaces(doc_hash, namespaces)
        
        return namespaces


class OperationResultCache(LRUCache):
    """Specialized cache for patch operation results."""
    
    def __init__(self, max_size: int = 1000, max_memory_mb: float = 100.0):
        """Initialize operation result cache."""
        super().__init__(max_size=max_size, max_memory_mb=max_memory_mb, default_ttl_seconds=600)
        self.invalidation_patterns: Set[str] = set()
    
    def cache_operation_result(self, operation: str, target: str, value: Any, 
                             document_hash: str, result: Any) -> None:
        """Cache the result of a patch operation."""
        # Create comprehensive cache key
        value_hash = self._hash_value(value)
        cache_key = f"op:{operation}:{hashlib.md5(target.encode()).hexdigest()}:{value_hash}:{document_hash}"
        
        # Cache the result
        self.put(cache_key, result)
    
    def get_cached_operation_result(self, operation: str, target: str, value: Any, 
                                  document_hash: str) -> Any:
        """Get cached result of a patch operation."""
        value_hash = self._hash_value(value)
        cache_key = f"op:{operation}:{hashlib.md5(target.encode()).hexdigest()}:{value_hash}:{document_hash}"
        
        return self.get(cache_key)
    
    def _hash_value(self, value: Any) -> str:
        """Create hash for cache key from operation value."""
        if isinstance(value, (str, int, float, bool)):
            return hashlib.md5(str(value).encode()).hexdigest()[:16]
        elif isinstance(value, dict):
            # Sort keys for consistent hashing
            sorted_items = json.dumps(value, sort_keys=True)
            return hashlib.md5(sorted_items.encode()).hexdigest()[:16]
        elif isinstance(value, list):
            # Convert to string representation
            list_str = json.dumps(value, sort_keys=True)
            return hashlib.md5(list_str.encode()).hexdigest()[:16]
        else:
            # Fallback to string representation
            return hashlib.md5(str(value).encode()).hexdigest()[:16]
    
    def invalidate_target_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching a target pattern."""
        invalidated = 0
        keys_to_remove = []
        
        with self._lock:
            for key in self._cache.keys():
                if pattern in key:
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            if self.delete(key):
                invalidated += 1
        
        return invalidated


class PersistentCache:
    """
    Persistent cache using SQLite for long-term storage.
    
    Provides disk-based caching for expensive operations that should
    survive application restarts.
    """
    
    def __init__(self, cache_file: Path, max_size_mb: float = 500.0):
        """Initialize persistent cache."""
        self.cache_file = cache_file
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        
        # Ensure parent directory exists
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        logger.info(f"Initialized persistent cache: {cache_file}")
    
    def _init_database(self) -> None:
        """Initialize SQLite database schema."""
        with sqlite3.connect(self.cache_file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value BLOB NOT NULL,
                    timestamp REAL NOT NULL,
                    access_count INTEGER DEFAULT 1,
                    size_bytes INTEGER NOT NULL,
                    ttl_seconds REAL
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON cache_entries(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_access_count ON cache_entries(access_count)
            """)
    
    def get(self, key: str) -> Any:
        """Get value from persistent cache."""
        with sqlite3.connect(self.cache_file) as conn:
            cursor = conn.execute("""
                SELECT value, timestamp, access_count, ttl_seconds 
                FROM cache_entries 
                WHERE key = ?
            """, (key,))
            
            row = cursor.fetchone()
            if row is None:
                return None
            
            value_blob, timestamp, access_count, ttl_seconds = row
            
            # Check TTL expiration
            if ttl_seconds is not None:
                age = time.time() - timestamp
                if age > ttl_seconds:
                    # Delete expired entry
                    conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                    return None
            
            # Update access count
            conn.execute("""
                UPDATE cache_entries 
                SET access_count = access_count + 1 
                WHERE key = ?
            """, (key,))
            
            # Deserialize value
            try:
                return pickle.loads(value_blob)
            except Exception as e:
                logger.warning(f"Failed to deserialize cached value for key '{key}': {e}")
                return None
    
    def put(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        """Put value into persistent cache."""
        try:
            # Serialize value
            value_blob = pickle.dumps(value)
            size_bytes = len(value_blob)
            
            with sqlite3.connect(self.cache_file) as conn:
                # Insert or replace entry
                conn.execute("""
                    INSERT OR REPLACE INTO cache_entries 
                    (key, value, timestamp, access_count, size_bytes, ttl_seconds)
                    VALUES (?, ?, ?, 1, ?, ?)
                """, (key, value_blob, time.time(), size_bytes, ttl_seconds))
                
                # Enforce size limits
                self._enforce_size_limit(conn)
        
        except Exception as e:
            logger.error(f"Failed to cache value for key '{key}': {e}")
    
    def delete(self, key: str) -> bool:
        """Delete entry from persistent cache."""
        with sqlite3.connect(self.cache_file) as conn:
            cursor = conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
            return cursor.rowcount > 0
    
    def _enforce_size_limit(self, conn: sqlite3.Connection) -> None:
        """Enforce cache size limit by removing least recently used entries."""
        # Get current cache size
        cursor = conn.execute("SELECT SUM(size_bytes) FROM cache_entries")
        current_size = cursor.fetchone()[0] or 0
        
        if current_size <= self.max_size_bytes:
            return
        
        # Remove entries until under limit
        target_size = int(self.max_size_bytes * 0.8)  # Remove to 80% of limit
        
        cursor = conn.execute("""
            SELECT key, size_bytes 
            FROM cache_entries 
            ORDER BY access_count ASC, timestamp ASC
        """)
        
        removed_size = 0
        for key, size_bytes in cursor:
            if current_size - removed_size <= target_size:
                break
            
            conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
            removed_size += size_bytes
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with sqlite3.connect(self.cache_file) as conn:
            # Count entries
            cursor = conn.execute("SELECT COUNT(*) FROM cache_entries")
            entry_count = cursor.fetchone()[0]
            
            # Calculate total size
            cursor = conn.execute("SELECT SUM(size_bytes) FROM cache_entries")
            total_size = cursor.fetchone()[0] or 0
            
            # Get average access count
            cursor = conn.execute("SELECT AVG(access_count) FROM cache_entries")
            avg_access_count = cursor.fetchone()[0] or 0
        
        return {
            'entry_count': entry_count,
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'max_size_mb': self.max_size_bytes / (1024 * 1024),
            'average_access_count': avg_access_count,
            'cache_file': str(self.cache_file)
        }
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed entries."""
        current_time = time.time()
        
        with sqlite3.connect(self.cache_file) as conn:
            cursor = conn.execute("""
                DELETE FROM cache_entries 
                WHERE ttl_seconds IS NOT NULL 
                AND (timestamp + ttl_seconds) < ?
            """, (current_time,))
            
            return cursor.rowcount


class CacheManager:
    """
    Centralized cache manager for all StyleStack caching needs.
    
    Coordinates multiple cache instances and provides unified interface
    for cache operations, statistics, and maintenance.
    """
    
    def __init__(self, 
                 cache_directory: Optional[Path] = None,
                 enable_persistent_cache: bool = True,
                 total_memory_limit_mb: float = 500.0):
        """Initialize the cache manager."""
        self.cache_directory = cache_directory or Path.home() / '.stylestack' / 'cache'
        self.enable_persistent_cache = enable_persistent_cache
        
        # Initialize cache instances
        memory_per_cache = total_memory_limit_mb / 4  # Divide among cache types
        
        self.xpath_cache = XPathCache(max_memory_mb=memory_per_cache)
        self.namespace_cache = NamespaceCache(max_memory_mb=memory_per_cache)
        self.operation_cache = OperationResultCache(max_memory_mb=memory_per_cache * 2)
        
        # Persistent cache for expensive operations
        self.persistent_cache = None
        if enable_persistent_cache:
            persistent_cache_file = self.cache_directory / 'stylestack_cache.db'
            self.persistent_cache = PersistentCache(persistent_cache_file)
        
        # Background maintenance
        self._maintenance_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='cache-maint')
        self._last_global_maintenance = time.time()
        
        logger.info(f"Cache manager initialized with {total_memory_limit_mb}MB total limit")
    
    def get_compiled_xpath(self, xpath_expression: str, namespaces: Optional[Dict[str, str]] = None) -> Optional[etree.XPath]:
        """Get compiled XPath expression."""
        return self.xpath_cache.get_compiled_xpath(xpath_expression, namespaces)
    
    def get_document_namespaces(self, xml_doc: etree._Element) -> Dict[str, str]:
        """Get namespaces for XML document."""
        return self.namespace_cache.extract_and_cache_namespaces(xml_doc)
    
    def cache_operation_result(self, operation: str, target: str, value: Any, 
                             document_hash: str, result: Any) -> None:
        """Cache operation result."""
        self.operation_cache.cache_operation_result(operation, target, value, document_hash, result)
    
    def get_cached_operation_result(self, operation: str, target: str, value: Any, 
                                  document_hash: str) -> Any:
        """Get cached operation result."""
        return self.operation_cache.get_cached_operation_result(operation, target, value, document_hash)
    
    def cache_expensive_computation(self, key: str, value: Any, ttl_seconds: float = 3600) -> None:
        """Cache expensive computation result in persistent storage."""
        if self.persistent_cache:
            self.persistent_cache.put(key, value, ttl_seconds)
    
    def get_cached_computation(self, key: str) -> Any:
        """Get cached expensive computation result."""
        if self.persistent_cache:
            return self.persistent_cache.get(key)
        return None
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics from all caches."""
        stats = {
            'xpath_cache': self.xpath_cache.get_stats(),
            'namespace_cache': self.namespace_cache.get_stats(),
            'operation_cache': self.operation_cache.get_stats(),
            'cache_manager': {
                'total_memory_limit_mb': sum([
                    self.xpath_cache.max_memory_bytes,
                    self.namespace_cache.max_memory_bytes,
                    self.operation_cache.max_memory_bytes
                ]) / (1024 * 1024),
                'enable_persistent_cache': self.enable_persistent_cache
            }
        }
        
        # Add compilation stats from XPath cache
        stats['xpath_cache']['compilation_stats'] = self.xpath_cache.get_compilation_stats()
        
        # Add persistent cache stats if available
        if self.persistent_cache:
            stats['persistent_cache'] = self.persistent_cache.get_stats()
        
        return stats
    
    def clear_all_caches(self) -> None:
        """Clear all cache instances."""
        self.xpath_cache.clear()
        self.namespace_cache.clear()
        self.operation_cache.clear()
        
        logger.info("Cleared all caches")
    
    def perform_maintenance(self) -> Dict[str, int]:
        """Perform maintenance on all caches."""
        maintenance_stats = {}
        
        # Clean up expired entries
        maintenance_stats['xpath_cache_evictions'] = 0  # LRU handles this automatically
        maintenance_stats['namespace_cache_evictions'] = 0
        maintenance_stats['operation_cache_evictions'] = 0
        
        if self.persistent_cache:
            maintenance_stats['persistent_cache_expired'] = self.persistent_cache.cleanup_expired()
        
        self._last_global_maintenance = time.time()
        
        return maintenance_stats
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Perform final maintenance
        self.perform_maintenance()
        
        # Shutdown maintenance executor
        self._maintenance_executor.shutdown(wait=True)


# Global cache manager instance
_global_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create global cache manager instance."""
    global _global_cache_manager
    
    if _global_cache_manager is None:
        _global_cache_manager = CacheManager()
    
    return _global_cache_manager


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Test cache manager
    with CacheManager() as cache_manager:
        # Test XPath caching
        xpath_expr = "//p:sp[@id='1']//a:t"
        compiled_xpath = cache_manager.get_compiled_xpath(xpath_expr)
        print(f"Compiled XPath: {compiled_xpath}")
        
        # Test operation result caching
        cache_manager.cache_operation_result(
            "set", "//p:sp", {"test": "value"}, "doc123", "success"
        )
        
        cached_result = cache_manager.get_cached_operation_result(
            "set", "//p:sp", {"test": "value"}, "doc123"
        )
        print(f"Cached result: {cached_result}")
        
        # Get statistics
        stats = cache_manager.get_comprehensive_stats()
        print("\nCache Statistics:")
        print(json.dumps(stats, indent=2))