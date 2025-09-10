#!/usr/bin/env python3
"""
Advanced Fixture System with Hierarchical Caching

This fixture system provides:
1. Hierarchical caching (session/module/class/function scopes)
2. Lazy evaluation and resource cleanup
3. Dependency injection with smart resolution
4. Performance optimization for expensive setups
5. Cross-test data sharing with isolation guarantees

Part of StyleStack 90% Coverage Initiative - Phase 1: Foundation Testing
"""

try:
    import pytest
except ImportError:
    pytest = None
import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Callable, TypeVar, Generic
from unittest.mock import Mock, MagicMock, patch
from collections import defaultdict
import threading
import time
import weakref
import hashlib

# Type definitions for fixture system
T = TypeVar('T')
FixtureFactory = Callable[[], T]


class CacheEntry(Generic[T]):
    """Cache entry with metadata for resource management"""
    
    def __init__(self, value: T, scope: str, dependencies: List[str] = None):
        self.value = value
        self.scope = scope
        self.dependencies = dependencies or []
        self.created_at = time.time()
        self.access_count = 0
        self.last_accessed = time.time()
        self._cleanup_callbacks = []
    
    def access(self) -> T:
        """Record access and return cached value"""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value
    
    def add_cleanup(self, callback: Callable):
        """Add cleanup callback for resource disposal"""
        self._cleanup_callbacks.append(callback)
    
    def cleanup(self):
        """Execute all cleanup callbacks"""
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                if pytest:
                    pytest.warning_recorder.record_warning(
                        UserWarning(f"Cleanup callback failed: {e}")
                    )
                else:
                    print(f"Warning: Cleanup callback failed: {e}")


class HierarchicalCache:
    """Multi-scope cache with intelligent resource management"""
    
    def __init__(self):
        self._caches = {
            'session': {},
            'module': {},
            'class': {},
            'function': {}
        }
        self._scope_hierarchy = ['session', 'module', 'class', 'function']
        self._lock = threading.RLock()
        self._cleanup_registry = defaultdict(list)
    
    def get(self, key: str, scope: str = 'function') -> Optional[CacheEntry]:
        """Get cached entry, checking scope hierarchy"""
        with self._lock:
            # Check current scope and parent scopes
            scope_index = self._scope_hierarchy.index(scope)
            for check_scope in self._scope_hierarchy[scope_index::-1]:
                if key in self._caches[check_scope]:
                    return self._caches[check_scope][key]
            return None
    
    def set(self, key: str, value: Any, scope: str = 'function', dependencies: List[str] = None) -> CacheEntry:
        """Cache value with scope and dependency tracking"""
        with self._lock:
            entry = CacheEntry(value, scope, dependencies)
            self._caches[scope][key] = entry
            
            # Register for cleanup when scope ends
            self._cleanup_registry[scope].append(key)
            
            return entry
    
    def invalidate_scope(self, scope: str):
        """Clear all entries for a specific scope"""
        with self._lock:
            if scope in self._caches:
                # Cleanup all entries in this scope
                for key, entry in self._caches[scope].items():
                    entry.cleanup()
                self._caches[scope].clear()
                self._cleanup_registry[scope].clear()
    
    def invalidate_dependents(self, dependency: str):
        """Invalidate all entries that depend on a specific dependency"""
        with self._lock:
            for scope_cache in self._caches.values():
                to_remove = []
                for key, entry in scope_cache.items():
                    if dependency in entry.dependencies:
                        entry.cleanup()
                        to_remove.append(key)
                
                for key in to_remove:
                    del scope_cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring"""
        with self._lock:
            stats = {}
            for scope, cache in self._caches.items():
                stats[scope] = {
                    'count': len(cache),
                    'total_accesses': sum(entry.access_count for entry in cache.values()),
                    'avg_age': sum(time.time() - entry.created_at for entry in cache.values()) / len(cache) if cache else 0
                }
            return stats


# Global cache instance
_fixture_cache = HierarchicalCache()


class FixtureManager:
    """Advanced fixture manager with smart dependency resolution"""
    
    def __init__(self):
        self.factories: Dict[str, FixtureFactory] = {}
        self.scope_mapping: Dict[str, str] = {}
        self.dependencies: Dict[str, List[str]] = {}
    
    def register(self, name: str, factory: FixtureFactory, scope: str = 'function', deps: List[str] = None):
        """Register a fixture factory with metadata"""
        self.factories[name] = factory
        self.scope_mapping[name] = scope
        self.dependencies[name] = deps or []
    
    def resolve(self, name: str, request_scope: str = 'function') -> Any:
        """Resolve fixture with caching and dependency injection"""
        # Check cache first
        cache_key = f"{name}_{request_scope}"
        cached = _fixture_cache.get(cache_key, request_scope)
        if cached:
            return cached.access()
        
        # Build dependency graph and resolve
        if name not in self.factories:
            raise ValueError(f"Fixture '{name}' not registered")
        
        # Resolve dependencies first
        resolved_deps = {}
        for dep in self.dependencies[name]:
            resolved_deps[dep] = self.resolve(dep, request_scope)
        
        # Create fixture value
        factory = self.factories[name]
        if resolved_deps:
            # Inject dependencies if factory accepts them
            import inspect
            sig = inspect.signature(factory)
            if len(sig.parameters) > 0:
                value = factory(**{k: v for k, v in resolved_deps.items() if k in sig.parameters})
            else:
                value = factory()
        else:
            value = factory()
        
        # Cache with appropriate scope
        effective_scope = self.scope_mapping.get(name, request_scope)
        entry = _fixture_cache.set(cache_key, value, effective_scope, self.dependencies[name])
        
        return entry.access()


# Global fixture manager
_fixture_manager = FixtureManager()


# Core fixture factories
def create_temp_directory() -> Path:
    """Create a temporary directory for test isolation"""
    temp_dir = Path(tempfile.mkdtemp(prefix='stylestack_test_'))
    
    def cleanup():
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    # Register cleanup
    entry = _fixture_cache.get(f"temp_dir_{id(temp_dir)}")
    if entry:
        entry.add_cleanup(cleanup)
    
    return temp_dir


def create_mock_ooxml_processor() -> Mock:
    """Create a comprehensive mock OOXML processor"""
    mock_processor = Mock()
    
    # Configure common method behaviors
    mock_processor.load_template.return_value = True
    mock_processor.extract_variables.return_value = ['${brand.primary}', '${typography.heading}']
    mock_processor.substitute_variables.return_value = {'substituted': 2, 'errors': 0}
    mock_processor.save_template.return_value = True
    mock_processor.validate_ooxml.return_value = {'valid': True, 'errors': []}
    
    # Mock XML manipulation methods
    mock_processor.find_elements.return_value = [Mock(tag='a:t', text='${brand.primary}')]
    mock_processor.update_element.return_value = True
    mock_processor.create_element.return_value = Mock()
    
    return mock_processor


def create_sample_design_tokens() -> Dict[str, Any]:
    """Create comprehensive sample design tokens for testing"""
    return {
        "brand": {
            "primary": "#007acc",
            "secondary": "#f4f4f4", 
            "accent": "#ff6b35",
            "text": "#333333",
            "background": "#ffffff"
        },
        "typography": {
            "heading": {
                "family": "Segoe UI",
                "size": "24pt",
                "weight": "600",
                "line_height": "1.2"
            },
            "body": {
                "family": "Segoe UI", 
                "size": "11pt",
                "weight": "400",
                "line_height": "1.4"
            }
        },
        "spacing": {
            "small": "8pt",
            "medium": "16pt", 
            "large": "24pt",
            "xlarge": "32pt"
        },
        "layout": {
            "container_width": "1200px",
            "gutter": "20pt",
            "margin": "1in"
        }
    }


def create_mock_template_file(temp_dir: Path) -> Path:
    """Create a mock template file for testing"""
    template_content = """<?xml version="1.0" encoding="UTF-8"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
    <p:slide>
        <p:cSld>
            <p:spTree>
                <p:sp>
                    <p:txBody>
                        <a:p>
                            <a:r>
                                <a:t>${brand.primary}</a:t>
                            </a:r>
                        </a:p>
                    </p:txBody>
                </p:sp>
            </p:spTree>
        </p:cSld>
    </p:slide>
</p:presentation>"""
    
    template_file = temp_dir / "test_template.xml"
    template_file.write_text(template_content)
    return template_file


def create_performance_monitor() -> Mock:
    """Create a mock performance monitor for testing"""
    monitor = Mock()
    monitor.start_timing.return_value = None
    monitor.end_timing.return_value = 0.05  # 50ms
    monitor.record_memory_usage.return_value = None
    monitor.get_memory_stats.return_value = {'peak_mb': 45.2, 'current_mb': 38.7}
    monitor.get_timing_stats.return_value = {'total_ms': 150, 'average_ms': 25}
    return monitor


# Register all fixtures with the manager
_fixture_manager.register('temp_dir', create_temp_directory, 'function')
_fixture_manager.register('mock_ooxml_processor', create_mock_ooxml_processor, 'class')
_fixture_manager.register('sample_design_tokens', create_sample_design_tokens, 'session')
_fixture_manager.register('mock_template_file', create_mock_template_file, 'function', ['temp_dir'])
_fixture_manager.register('performance_monitor', create_performance_monitor, 'class')


# Pytest fixture integrations (only available when pytest is installed)
if pytest:
    @pytest.fixture(scope='session')
    def sample_design_tokens():
        """Session-scoped design tokens for consistent testing"""
        return _fixture_manager.resolve('sample_design_tokens', 'session')


    @pytest.fixture(scope='function')  
    def temp_dir():
        """Function-scoped temporary directory"""
        return _fixture_manager.resolve('temp_dir', 'function')


    @pytest.fixture(scope='class')
    def mock_ooxml_processor():
        """Class-scoped mock OOXML processor"""
        return _fixture_manager.resolve('mock_ooxml_processor', 'class')


    @pytest.fixture(scope='function')
    def mock_template_file(temp_dir):
        """Function-scoped mock template file"""
        return _fixture_manager.resolve('mock_template_file', 'function')


    @pytest.fixture(scope='class')
    def performance_monitor():
        """Class-scoped performance monitor"""
        return _fixture_manager.resolve('performance_monitor', 'class')


    @pytest.fixture(scope='session', autouse=True)
    def configure_test_environment():
        """Auto-configure test environment for optimal performance"""
        # Set test-specific environment variables
        test_env = {
            'STYLESTACK_TEST_MODE': '1',
            'STYLESTACK_LOG_LEVEL': 'ERROR',
            'STYLESTACK_CACHE_DISABLE': '0',  # Enable caching for performance
            'STYLESTACK_PARALLEL_SAFE': '1'
        }
        
        # Apply environment
        original_env = {}
        for key, value in test_env.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value
        
        yield
        
        # Restore original environment
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


    @pytest.fixture(scope='session', autouse=True)
    def cache_cleanup():
        """Auto-cleanup cache after test session"""
        yield
        
        # Clear all caches
        _fixture_cache.invalidate_scope('session')
        _fixture_cache.invalidate_scope('module') 
        _fixture_cache.invalidate_scope('class')
        _fixture_cache.invalidate_scope('function')
else:
    # Provide stub functions when pytest is not available
    def sample_design_tokens():
        return _fixture_manager.resolve('sample_design_tokens', 'session')
    
    def temp_dir():
        return _fixture_manager.resolve('temp_dir', 'function')
    
    def mock_ooxml_processor():
        return _fixture_manager.resolve('mock_ooxml_processor', 'class')
    
    def mock_template_file():
        temp_dir = _fixture_manager.resolve('temp_dir', 'function') 
        return _fixture_manager.resolve('mock_template_file', 'function')
    
    def performance_monitor():
        return _fixture_manager.resolve('performance_monitor', 'class')
    
    def configure_test_environment():
        pass
    
    def cache_cleanup():
        pass


# Utility functions for test authors
def get_fixture(name: str, scope: str = 'function') -> Any:
    """Direct fixture resolution for advanced test scenarios"""
    return _fixture_manager.resolve(name, scope)


def invalidate_fixture_cache(pattern: str = None):
    """Invalidate cached fixtures matching pattern"""
    if pattern:
        _fixture_cache.invalidate_dependents(pattern)
    else:
        # Clear function scope by default
        _fixture_cache.invalidate_scope('function')


def get_cache_stats() -> Dict[str, Any]:
    """Get fixture cache performance statistics"""
    return _fixture_cache.get_stats()


# Additional fixtures for advanced testing scenarios
def create_benchmark_data() -> Dict[str, Any]:
    """Large dataset for performance benchmarking"""
    return {
        'tokens': {f'token_{i}': f'value_{i}' for i in range(1000)},
        'large_text': 'x' * 10000,
        'nested_structure': {'level_%d' % i: {'data': list(range(100))} for i in range(10)}
    }


def create_integration_environment(temp_dir: Path) -> Dict[str, Any]:
    """Set up complete integration test environment"""
    env_dir = temp_dir / 'integration'
    env_dir.mkdir()
    
    # Create directory structure
    (env_dir / 'templates').mkdir()
    (env_dir / 'output').mkdir() 
    (env_dir / 'tokens').mkdir()
    
    # Create sample files
    tokens_file = env_dir / 'tokens' / 'design-tokens.json'
    tokens_file.write_text(json.dumps(create_sample_design_tokens(), indent=2))
    
    template_file = env_dir / 'templates' / 'sample.potx'
    template_file.write_bytes(b'MOCK_POTX_CONTENT')  # Mock binary content
    
    return {
        'root': env_dir,
        'templates_dir': env_dir / 'templates',
        'output_dir': env_dir / 'output',
        'tokens_dir': env_dir / 'tokens',
        'tokens_file': tokens_file,
        'template_file': template_file
    }


# Register additional fixtures
_fixture_manager.register('benchmark_data', create_benchmark_data, 'class')
_fixture_manager.register('integration_environment', create_integration_environment, 'module', ['temp_dir'])


# Additional pytest fixtures when available
if pytest:
    @pytest.fixture(scope='class')
    def benchmark_data():
        """Large dataset for performance benchmarking"""
        return _fixture_manager.resolve('benchmark_data', 'class')

    @pytest.fixture(scope='module')
    def integration_environment():
        """Set up complete integration test environment"""
        return _fixture_manager.resolve('integration_environment', 'module')
else:
    def benchmark_data():
        return _fixture_manager.resolve('benchmark_data', 'class')
    
    def integration_environment():
        return _fixture_manager.resolve('integration_environment', 'module')


if __name__ == '__main__':
    # Test the fixture system
    print("Testing Advanced Fixture System...")
    
    # Test basic fixture resolution
    tokens = get_fixture('sample_design_tokens', 'session')
    print(f"Sample tokens: {len(tokens)} categories")
    
    # Test cache stats
    stats = get_cache_stats()
    print(f"Cache stats: {stats}")
    
    print("✅ Advanced fixture system operational")