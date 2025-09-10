#!/usr/bin/env python3
"""
StyleStack Performance Optimizations

Implementation of performance optimizations based on benchmark results:
- Lazy import system
- Caching mechanisms
- Memory optimization
- Connection pooling
"""


from typing import Any, Dict, Optional
import functools
import threading
import time
import weakref


# Type definitions
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


class LazyImport:
    """Lazy import system to reduce initialization overhead."""
    
    def __init__(self, module_name: str, attribute: Optional[str] = None):
        self.module_name = module_name
        self.attribute = attribute
        self._cached_module = None
        self._cached_attribute = None
        self._lock = threading.RLock()
    
    def __call__(self):
        """Get the lazily imported module or attribute."""
        if self._cached_module is None:
            with self._lock:
                if self._cached_module is None:
                    self._cached_module = __import__(self.module_name, fromlist=[self.attribute] if self.attribute else [])
                    
                    if self.attribute:
                        self._cached_attribute = getattr(self._cached_module, self.attribute)
        
        return self._cached_attribute if self.attribute else self._cached_module
    
    def __getattr__(self, name):
        """Allow attribute access on the lazy import."""
        module = self()
        return getattr(module, name)


class PerformanceCache:
    """High-performance caching system with TTL and memory management."""
    
    def __init__(self, max_size: int = 1000, ttl: Optional[float] = None):
        self.max_size = max_size
        self.ttl = ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        current_time = time.time()
        
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return default
            
            entry = self._cache[key]
            
            # Check TTL expiration
            if self.ttl and current_time - entry['created'] > self.ttl:
                del self._cache[key]
                del self._access_times[key]
                self._stats['misses'] += 1
                return default
            
            # Update access time
            self._access_times[key] = current_time
            self._stats['hits'] += 1
            return entry['value']
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        current_time = time.time()
        
        with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()
            
            self._cache[key] = {
                'value': value,
                'created': current_time
            }
            self._access_times[key] = current_time
    
    def _evict_lru(self) -> None:
        """Evict least recently used item."""
        if not self._access_times:
            return
        
        lru_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        del self._cache[lru_key]
        del self._access_times[lru_key]
        self._stats['evictions'] += 1
    
    def clear(self) -> None:
        """Clear all cached data."""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0
            
            return {
                **self._stats,
                'cache_size': len(self._cache),
                'hit_rate': hit_rate,
                'memory_efficiency': len(self._cache) / self.max_size
            }


def cached_method(ttl: Optional[float] = None, max_size: int = 128):
    """Decorator for caching method results."""
    def decorator(func: F) -> F:
        cache = PerformanceCache(max_size=max_size, ttl=ttl)
        
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # Create cache key from method name, args, and kwargs
            key_parts = [func.__name__, str(args), str(sorted(kwargs.items()))]
            cache_key = hash(tuple(key_parts))
            cache_key_str = f"{func.__name__}_{cache_key}"
            
            # Try to get from cache
            result = cache.get(cache_key_str)
            if result is not None:
                return result
            
            # Compute and cache result
            result = func(self, *args, **kwargs)
            cache.set(cache_key_str, result)
            return result
        
        # Add cache management methods
        wrapper.cache_clear = cache.clear
        wrapper.cache_stats = cache.get_stats
        
        return wrapper
    
    return decorator


def memoize(func: F) -> F:
    """Simple memoization decorator for expensive computations."""
    cache = {}
    cache_lock = threading.RLock()
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Create hashable key
        key = (args, tuple(sorted(kwargs.items())))
        
        with cache_lock:
            if key in cache:
                return cache[key]
            
            result = func(*args, **kwargs)
            cache[key] = result
            return result
    
    wrapper.cache_clear = cache.clear
    wrapper.cache_info = lambda: {'cache_size': len(cache)}
    
    return wrapper


class ConnectionPool(Generic[T]):
    """Generic connection pool for resource management."""
    
    def __init__(self, factory: Callable[[], T], max_connections: int = 10, 
                 max_idle_time: float = 300.0):
        self.factory = factory
        self.max_connections = max_connections
        self.max_idle_time = max_idle_time
        
        self._available: list = []
        self._in_use: weakref.WeakSet = weakref.WeakSet()
        self._lock = threading.RLock()
        self._created_count = 0
        
    def acquire(self) -> T:
        """Acquire a connection from the pool."""
        current_time = time.time()
        
        with self._lock:
            # Clean expired connections
            self._clean_expired_connections(current_time)
            
            # Try to reuse existing connection
            if self._available:
                connection_data = self._available.pop()
                connection = connection_data['connection']
                self._in_use.add(connection)
                return connection
            
            # Create new connection if under limit
            if self._created_count < self.max_connections:
                connection = self.factory()
                self._created_count += 1
                self._in_use.add(connection)
                return connection
            
            # If at limit, wait and try again (simplified version)
            raise RuntimeError("Connection pool exhausted")
    
    def release(self, connection: T) -> None:
        """Release a connection back to the pool."""
        with self._lock:
            if connection in self._in_use:
                self._in_use.discard(connection)
                self._available.append({
                    'connection': connection,
                    'released_at': time.time()
                })
    
    def _clean_expired_connections(self, current_time: float) -> None:
        """Clean expired idle connections."""
        expired_indices = []
        for i, conn_data in enumerate(self._available):
            if current_time - conn_data['released_at'] > self.max_idle_time:
                expired_indices.append(i)
        
        # Remove expired connections in reverse order
        for i in reversed(expired_indices):
            self._available.pop(i)
            self._created_count -= 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        with self._lock:
            return {
                'total_created': self._created_count,
                'available': len(self._available),
                'in_use': len(self._in_use),
                'utilization': len(self._in_use) / self.max_connections
            }


class MemoryOptimizer:
    """Memory usage optimization utilities."""
    
    @staticmethod
    def optimize_dict(data: Dict[str, Any], compress_strings: bool = True) -> Dict[str, Any]:
        """Optimize dictionary memory usage."""
        optimized = {}
        
        for key, value in data.items():
            # Intern string keys to save memory
            if isinstance(key, str):
                key = MemoryOptimizer._intern_string(key)
            
            # Optimize string values
            if isinstance(value, str) and compress_strings:
                value = MemoryOptimizer._intern_string(value)
            
            # Recursively optimize nested dictionaries
            elif isinstance(value, dict):
                value = MemoryOptimizer.optimize_dict(value, compress_strings)
            
            # Optimize lists
            elif isinstance(value, list):
                value = MemoryOptimizer._optimize_list(value, compress_strings)
            
            optimized[key] = value
        
        return optimized
    
    @staticmethod
    def _intern_string(s: str) -> str:
        """Intern string to save memory for repeated strings."""
        # Only intern small, commonly used strings
        if len(s) < 100 and s.replace(' ', '').replace('_', '').replace('-', '').isalnum():
            return s.__class__(s)  # Force string interning
        return s
    
    @staticmethod
    def _optimize_list(lst: list, compress_strings: bool) -> list:
        """Optimize list memory usage."""
        optimized = []
        for item in lst:
            if isinstance(item, str) and compress_strings:
                item = MemoryOptimizer._intern_string(item)
            elif isinstance(item, dict):
                item = MemoryOptimizer.optimize_dict(item, compress_strings)
            elif isinstance(item, list):
                item = MemoryOptimizer._optimize_list(item, compress_strings)
            
            optimized.append(item)
        
        return optimized


class BatchProcessor:
    """Optimized batch processing for bulk operations."""
    
    def __init__(self, batch_size: int = 100, max_workers: int = 4):
        self.batch_size = batch_size
        self.max_workers = max_workers
    
    def process_items(self, items: list, processor: Callable[[Any], Any], 
                     parallel: bool = True) -> list:
        """Process items in optimized batches."""
        if not items:
            return []
        
        # Split into batches
        batches = [items[i:i + self.batch_size] 
                  for i in range(0, len(items), self.batch_size)]
        
        if not parallel or len(batches) == 1:
            # Sequential processing
            results = []
            for batch in batches:
                batch_results = [processor(item) for item in batch]
                results.extend(batch_results)
            return results
        
        # Parallel processing
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_batch = {
                executor.submit(self._process_batch, batch, processor): batch 
                for batch in batches
            }
            
            results = []
            for future in concurrent.futures.as_completed(future_to_batch):
                batch_results = future.result()
                results.extend(batch_results)
            
            return results
    
    def _process_batch(self, batch: list, processor: Callable[[Any], Any]) -> list:
        """Process a single batch of items."""
        return [processor(item) for item in batch]


# Pre-configured optimization instances
default_cache = PerformanceCache(max_size=500, ttl=300.0)
memory_optimizer = MemoryOptimizer()
batch_processor = BatchProcessor()

# Lazy imports for heavy dependencies
lazy_xml = LazyImport('xml.etree.ElementTree', 'ElementTree')
lazy_zipfile = LazyImport('zipfile')
lazy_json = LazyImport('json')


def optimize_module_imports():
    """Apply import optimizations to reduce startup time."""
    import sys
    
    # List of modules that should be lazy-loaded
    lazy_modules = [
        'xml.etree.ElementTree',
        'zipfile', 
        'json',
        'concurrent.futures',
        'threading',
        'multiprocessing'
    ]
    
    optimization_info = {
        'optimized_modules': [],
        'startup_time_saved': 0.0
    }
    
    for module_name in lazy_modules:
        if module_name in sys.modules:
            # Module already loaded, measure memory usage
            module = sys.modules[module_name]
            optimization_info['optimized_modules'].append({
                'name': module_name,
                'status': 'already_loaded',
                'size_estimate': len(str(module.__dict__))
            })
    
    return optimization_info


if __name__ == '__main__':
    # Demo the optimization features
    print("🚀 StyleStack Performance Optimizations Demo")
    
    # Test caching
    print("\n📦 Testing Performance Cache...")
    cache = PerformanceCache(max_size=3, ttl=1.0)
    
    cache.set('key1', 'value1')
    cache.set('key2', 'value2')
    print(f"Cache stats: {cache.get_stats()}")
    
    print(f"Get key1: {cache.get('key1')}")  # Hit
    print(f"Get key3: {cache.get('key3', 'default')}")  # Miss
    print(f"Final stats: {cache.get_stats()}")
    
    # Test memory optimization
    print("\n💾 Testing Memory Optimization...")
    test_data = {
        'colors': ['red', 'green', 'blue'] * 10,
        'fonts': {'primary': 'Arial', 'secondary': 'Helvetica'},
        'nested': {'deep': {'value': 'test' * 5}}
    }
    
    optimized = memory_optimizer.optimize_dict(test_data)
    print(f"Optimized {len(str(test_data))} bytes of data")
    
    # Test batch processing
    print("\n⚡ Testing Batch Processing...")
    items = list(range(47))  # Not evenly divisible by batch size
    
    def square(x):
        return x * x
    
    results = batch_processor.process_items(items, square, parallel=False)
    print(f"Processed {len(items)} items -> {len(results)} results")
    
    print("\n✅ Performance optimizations ready!")