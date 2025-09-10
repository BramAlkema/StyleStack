#!/usr/bin/env python3
"""
StyleStack Global Test Configuration

This file provides global pytest configuration, fixtures, and utilities for the
comprehensive testing architecture across unit, integration, and system tests.
"""

import os
import sys
import pytest
import tempfile
import shutil
import logging
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from unittest.mock import Mock, MagicMock

# Ensure tools directory is in Python path for all tests
PROJECT_ROOT = Path(__file__).parent
TOOLS_DIR = PROJECT_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

# Test configuration
TEST_DATA_DIR = PROJECT_ROOT / "tests" / "fixtures"
TEMP_DIR = PROJECT_ROOT / "tmp" / "test_workspace"


def pytest_configure(config):
    """Global pytest configuration."""
    # Add custom markers for comprehensive test categorization
    markers = [
        "unit: Unit tests for individual modules",
        "integration: Integration tests for component interaction", 
        "system: End-to-end system tests",
        "slow: Tests that take more than 5 seconds",
        "stress: Performance and stress tests",
        "concurrent: Multi-threading and parallel processing tests",
        "large_file: Tests processing large OOXML files",
        "ooxml: Tests related to OOXML processing",
        "tokens: Tests related to design token processing",
        "performance: Performance benchmarking tests", 
        "regression: Regression tests for known issues",
        "security: Security-related tests",
        "accessibility: WCAG compliance tests",
        "golden_master: Golden master regression tests",
        "cross_platform: Cross-platform compatibility tests",
        "xml_validation: XML structure validation tests",
        "import_resolution: Module import resolution tests"
    ]
    
    for marker in markers:
        config.addinivalue_line("markers", marker)
    
    # Configure test logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Create test workspace directory
    TEMP_DIR.mkdir(parents=True, exist_ok=True)


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add automatic markers and ordering."""
    
    # Auto-mark tests based on path and name patterns
    for item in items:
        test_path = str(item.fspath)
        test_name = item.name.lower()
        
        # Path-based markers
        if "/unit/" in test_path:
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in test_path:
            item.add_marker(pytest.mark.integration)
        elif "/system/" in test_path:
            item.add_marker(pytest.mark.system)
        
        # Name-based markers
        if any(keyword in test_name for keyword in ["slow", "large", "stress", "benchmark"]):
            item.add_marker(pytest.mark.slow)
        
        if "ooxml" in test_name:
            item.add_marker(pytest.mark.ooxml)
            
        if any(keyword in test_name for keyword in ["token", "design"]):
            item.add_marker(pytest.mark.tokens)
            
        if "performance" in test_name or "benchmark" in test_name:
            item.add_marker(pytest.mark.performance)
            
        if "concurrent" in test_name or "parallel" in test_name:
            item.add_marker(pytest.mark.concurrent)
            
        if "golden" in test_name or "regression" in test_name:
            item.add_marker(pytest.mark.golden_master)
            
        if any(keyword in test_name for keyword in ["import", "module", "discovery"]):
            item.add_marker(pytest.mark.import_resolution)


def pytest_runtest_setup(item):
    """Setup hook for individual test runs."""
    # Skip tests based on markers and environment
    if item.get_closest_marker("slow") and not item.config.getoption("--run-slow"):
        pytest.skip("slow test skipped (use --run-slow to run)")
    
    if item.get_closest_marker("stress") and not item.config.getoption("--run-stress"):
        pytest.skip("stress test skipped (use --run-stress to run)")


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-slow", action="store_true", default=False,
        help="Run slow tests"
    )
    parser.addoption(
        "--run-stress", action="store_true", default=False,
        help="Run stress/performance tests"
    )
    parser.addoption(
        "--test-data-dir", action="store", default=str(TEST_DATA_DIR),
        help="Directory containing test data"
    )
    parser.addoption(
        "--generate-fixtures", action="store_true", default=False,
        help="Generate missing test fixtures"
    )


# Session-level fixtures

@pytest.fixture(scope="session")
def project_root():
    """Project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session") 
def tools_dir():
    """Tools directory for module imports."""
    return TOOLS_DIR


@pytest.fixture(scope="session")
def test_session_info():
    """Test session information."""
    return {
        "session_id": f"test_session_{int(time.time())}",
        "start_time": time.time(),
        "python_version": sys.version,
        "platform": sys.platform,
        "cwd": os.getcwd()
    }


@pytest.fixture(scope="session")
def test_workspace_session():
    """Session-level test workspace."""
    session_workspace = TEMP_DIR / f"session_{int(time.time())}"
    session_workspace.mkdir(parents=True, exist_ok=True)
    
    yield session_workspace
    
    # Cleanup session workspace
    if session_workspace.exists():
        shutil.rmtree(session_workspace, ignore_errors=True)


# Function-level fixtures

@pytest.fixture
def temp_workspace():
    """Temporary workspace for individual tests."""
    test_workspace = tempfile.mkdtemp(prefix="stylestack_test_")
    workspace_path = Path(test_workspace)
    
    yield workspace_path
    
    # Cleanup
    if workspace_path.exists():
        shutil.rmtree(workspace_path, ignore_errors=True)


@pytest.fixture
def mock_file_system():
    """Mock file system operations for testing."""
    return {
        "read": MagicMock(),
        "write": MagicMock(), 
        "exists": MagicMock(return_value=True),
        "mkdir": MagicMock(),
        "rmdir": MagicMock(),
        "copy": MagicMock(),
        "move": MagicMock()
    }


@pytest.fixture
def sample_design_tokens():
    """Sample design tokens for testing."""
    return {
        "colors": {
            "primary": {"value": "#1F4788", "type": "color"},
            "secondary": {"value": "#70AD47", "type": "color"},
            "background": {"value": "#FFFFFF", "type": "color"}
        },
        "typography": {
            "heading": {"value": "Calibri 24pt 700", "type": "typography"},
            "body": {"value": "Calibri 12pt 400", "type": "typography"}
        },
        "spacing": {
            "small": {"value": "8", "type": "dimension"},
            "medium": {"value": "16", "type": "dimension"}, 
            "large": {"value": "24", "type": "dimension"}
        }
    }


@pytest.fixture
def sample_ooxml_content():
    """Sample OOXML content for testing."""
    return {
        "powerpoint": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" 
                xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst>
    <p:sldMasterId id="2147483648" r:id="rId1"/>
  </p:sldMasterIdLst>
</p:presentation>''',
        
        "word": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:r>
        <w:t>Sample document content</w:t>
      </w:r>
    </w:p>
  </w:body>
</w:document>''',
        
        "excel": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheets>
    <sheet name="Sheet1" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>'''
    }


@pytest.fixture
def test_metrics_collector():
    """Test metrics collection utility."""
    
    class TestMetrics:
        def __init__(self):
            self.metrics = {}
            self.timers = {}
        
        def start_timer(self, name: str):
            self.timers[name] = time.time()
        
        def stop_timer(self, name: str) -> float:
            if name in self.timers:
                duration = time.time() - self.timers[name]
                self.metrics[f"{name}_duration"] = duration
                del self.timers[name]
                return duration
            return 0.0
        
        def record(self, name: str, value: Any):
            self.metrics[name] = value
        
        def get_metrics(self) -> Dict[str, Any]:
            return self.metrics.copy()
        
        def export_json(self, filepath: Union[str, Path]):
            with open(filepath, 'w') as f:
                json.dump(self.metrics, f, indent=2)
    
    return TestMetrics()


# Import resolution fixtures

@pytest.fixture
def mock_import_system():
    """Mock import system for testing module resolution."""
    
    class MockImportSystem:
        def __init__(self):
            self.available_modules = set()
            self.failed_imports = set()
        
        def add_module(self, module_name: str):
            self.available_modules.add(module_name)
        
        def remove_module(self, module_name: str):
            self.available_modules.discard(module_name)
            self.failed_imports.add(module_name)
        
        def can_import(self, module_name: str) -> bool:
            return module_name in self.available_modules
        
        def get_import_failures(self) -> List[str]:
            return list(self.failed_imports)
    
    return MockImportSystem()


# Test validation utilities

def validate_ooxml_structure(content: str, expected_namespace: str) -> bool:
    """Validate OOXML content structure."""
    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(content)
        # Check if expected namespace is in the root tag or namespace declarations
        return (expected_namespace in root.tag or 
                expected_namespace in content or
                any(expected_namespace in ns for ns in root.nsmap.values() if hasattr(root, 'nsmap')))
    except (ET.ParseError, AttributeError):
        return False


def validate_design_tokens(tokens: Dict[str, Any]) -> List[str]:
    """Validate design token structure and return errors."""
    errors = []
    
    for category, category_tokens in tokens.items():
        if not isinstance(category_tokens, dict):
            errors.append(f"Category '{category}' must be a dictionary")
            continue
            
        for token_name, token_data in category_tokens.items():
            if not isinstance(token_data, dict):
                errors.append(f"Token '{category}.{token_name}' must be a dictionary")
                continue
                
            if "value" not in token_data:
                errors.append(f"Token '{category}.{token_name}' missing required 'value' field")
                
            if "type" not in token_data:
                errors.append(f"Token '{category}.{token_name}' missing required 'type' field")
    
    return errors


# Module discovery and testing

def discover_python_modules(root_dir: Path = None) -> List[str]:
    """Discover all Python modules in the project."""
    if root_dir is None:
        root_dir = TOOLS_DIR
    
    modules = []
    for py_file in root_dir.glob("**/*.py"):
        if py_file.name == "__init__.py":
            continue
        
        # Skip files with invalid Python identifiers (like 'validate-2026.py')
        if not py_file.stem.replace('-', '_').replace('.', '_').isidentifier():
            continue
            
        # Convert path to module name
        relative_path = py_file.relative_to(root_dir)
        module_name = str(relative_path.with_suffix("")).replace(os.sep, ".").replace('-', '_')
        modules.append(module_name)
    
    return sorted(modules)


def get_test_files_for_modules(modules: List[str]) -> Dict[str, Optional[str]]:
    """Map modules to their corresponding test files."""
    test_mapping = {}
    tests_dir = PROJECT_ROOT / "tests"
    
    for module in modules:
        # Convert module name to test file pattern
        test_patterns = [
            f"test_{module.replace('.', '_')}.py",
            f"test_{module.split('.')[-1]}.py",
            f"{module.replace('.', '_')}_test.py"
        ]
        
        test_file = None
        for pattern in test_patterns:
            for test_path in tests_dir.glob(f"**/{pattern}"):
                test_file = str(test_path)
                break
            if test_file:
                break
        
        test_mapping[module] = test_file
    
    return test_mapping


# Cleanup and final setup

@pytest.fixture(autouse=True)
def ensure_clean_state():
    """Ensure clean state before and after each test."""
    # Pre-test cleanup
    import gc
    gc.collect()
    
    yield
    
    # Post-test cleanup
    gc.collect()


def pytest_sessionfinish(session, exitstatus):
    """Session cleanup and reporting."""
    # Clean up session-level resources
    if TEMP_DIR.exists():
        try:
            shutil.rmtree(TEMP_DIR, ignore_errors=True)
        except Exception:
            pass
    
    # Report session statistics
    if hasattr(session.config, '_test_stats'):
        print(f"\nTest session statistics: {session.config._test_stats}")