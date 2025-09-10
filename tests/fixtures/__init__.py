#!/usr/bin/env python3
"""
Advanced Fixture System Package

Provides hierarchical caching, smart dependency injection, and performance optimization
for StyleStack test suite. 

Import this module to enable advanced fixture capabilities:

    from tests.fixtures import *
    
Key features:
- Multi-scope caching (session/module/class/function)
- Lazy evaluation and resource cleanup
- Dependency injection
- Performance monitoring
- Cross-test isolation guarantees

Part of StyleStack 90% Coverage Initiative - Phase 1: Foundation Testing
"""

from .advanced_fixtures import (
    # Core fixture system
    HierarchicalCache,
    FixtureManager,
    CacheEntry,
    
    # Fixture manager instance
    _fixture_manager,
    _fixture_cache,
    
    # Utility functions
    get_fixture,
    invalidate_fixture_cache,
    get_cache_stats,
    
    # Factory functions
    create_temp_directory,
    create_mock_ooxml_processor,
    create_sample_design_tokens,
    create_mock_template_file,
    create_performance_monitor,
    
    # Pytest fixtures (automatically available when imported)
    sample_design_tokens,
    temp_dir,
    mock_ooxml_processor,
    mock_template_file,
    performance_monitor,
    configure_test_environment,
    cache_cleanup,
    benchmark_data,
    integration_environment,
)

__all__ = [
    'HierarchicalCache',
    'FixtureManager', 
    'CacheEntry',
    'get_fixture',
    'invalidate_fixture_cache',
    'get_cache_stats',
    'create_temp_directory',
    'create_mock_ooxml_processor',
    'create_sample_design_tokens',
    'create_mock_template_file',
    'create_performance_monitor',
    'sample_design_tokens',
    'temp_dir',
    'mock_ooxml_processor',
    'mock_template_file',
    'performance_monitor',
    'benchmark_data',
    'integration_environment',
]