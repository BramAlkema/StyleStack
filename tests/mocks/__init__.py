#!/usr/bin/env python3
"""
Centralized Mock System Package

Provides standardized, high-quality mocks for external dependencies used
throughout StyleStack testing. Reduces duplication and ensures consistency.

Key components:
- MockRegistry: Central mock management
- FileSystemMocker: Mock file system operations  
- OOXMLProcessorMocker: Advanced OOXML processor mocks
- GitMocker: Mock Git repository operations
- HTTPMocker: Mock HTTP requests and responses
- DatabaseMocker: Mock database operations

Usage:
    from tests.mocks import create_standard_mocks, get_mock, mock_external_dependencies
    
    # Create standard mocks
    mocks = create_standard_mocks()
    
    # Get specific mock
    processor = get_mock('ooxml_processor')
    
    # Use context manager
    with mock_external_dependencies(['requests', 'git']):
        # Test code with mocked dependencies
        pass

Part of StyleStack 90% Coverage Initiative - Phase 1: Foundation Testing
"""

from .external_dependencies import (
    # Core mock system
    MockRegistry,
    _mock_registry,
    
    # Specialized mockers
    FileSystemMocker,
    OOXMLProcessorMocker,
    GitMocker,
    HTTPMocker,
    DatabaseMocker,
    
    # Factory functions
    create_standard_mocks,
    
    # Utility functions
    get_mock,
    reset_all_mocks,
    get_mock_call_history,
    
    # Context manager
    mock_external_dependencies,
)

__all__ = [
    'MockRegistry',
    'FileSystemMocker',
    'OOXMLProcessorMocker', 
    'GitMocker',
    'HTTPMocker',
    'DatabaseMocker',
    'create_standard_mocks',
    'get_mock',
    'reset_all_mocks',
    'get_mock_call_history',
    'mock_external_dependencies',
]