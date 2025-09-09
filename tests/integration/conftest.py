#!/usr/bin/env python3
"""
Pytest Configuration for StyleStack Integration Tests

This file provides shared fixtures, configuration, and utilities for the comprehensive
end-to-end integration test suite.
"""

import pytest
import tempfile
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import time
import sys

# Add tools directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from tools.multi_format_ooxml_handler import MultiFormatOOXMLHandler
from tools.transaction_pipeline import TransactionPipeline

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Test constants
FIXTURES_PATH = Path(__file__).parent / "fixtures"
TEMPLATES_PATH = FIXTURES_PATH / "templates"

def pytest_configure(config):
    """Configure pytest for integration testing."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "stress: mark test as stress/performance test"
    )
    config.addinivalue_line(
        "markers", "concurrent: mark test as concurrent/threading test"
    )
    config.addinivalue_line(
        "markers", "large_file: mark test as large file processing test"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Mark slow tests
        if any(keyword in item.name.lower() for keyword in ["large", "stress", "concurrent", "batch"]):
            item.add_marker(pytest.mark.slow)
        
        # Mark stress tests
        if "stress" in item.name.lower():
            item.add_marker(pytest.mark.stress)
        
        # Mark concurrent tests
        if "concurrent" in item.name.lower():
            item.add_marker(pytest.mark.concurrent)
        
        # Mark large file tests
        if "large" in item.name.lower():
            item.add_marker(pytest.mark.large_file)

@pytest.fixture(scope="session")
def test_session_id():
    """Provide a unique session ID for this test run."""
    return f"integration_test_{int(time.time())}"

@pytest.fixture(scope="session")
def templates_available():
    """Verify that test templates are available before running tests."""
    required_templates = [
        "test_presentation.potx",
        "test_document.dotx", 
        "test_workbook.xltx",
        "large_test_presentation.potx"
    ]
    
    missing_templates = []
    for template in required_templates:
        template_path = TEMPLATES_PATH / template
        if not template_path.exists():
            missing_templates.append(template)
    
    if missing_templates:
        pytest.skip(f"Required test templates not found: {missing_templates}. Run create_test_templates.py first.")
    
    return True

@pytest.fixture(scope="function")
def temp_workspace():
    """Provide a temporary workspace directory for each test."""
    temp_dir = Path(tempfile.mkdtemp(prefix="stylestack_test_"))
    yield temp_dir
    
    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture(scope="function") 
def ooxml_handler():
    """Provide a fresh MultiFormatOOXMLHandler for each test."""
    return MultiFormatOOXMLHandler(enable_token_integration=True)

@pytest.fixture(scope="function")
def transaction_pipeline():
    """Provide a fresh TransactionPipeline for each test."""
    return TransactionPipeline(enable_audit_trail=True)

@pytest.fixture(scope="function")
def json_processor():
    """Provide a fresh JSONPatchProcessor for each test."""
    return JSONPatchProcessor()

@pytest.fixture(scope="function")
def template_factory(temp_workspace, templates_available):
    """Factory for creating temporary copies of test templates."""
    
    def create_template_copy(template_name: str, custom_name: Optional[str] = None) -> Path:
        """Create a temporary copy of a test template."""
        source_path = TEMPLATES_PATH / template_name
        if not source_path.exists():
            raise FileNotFoundError(f"Template not found: {source_path}")
        
        target_name = custom_name or template_name
        target_path = temp_workspace / target_name
        shutil.copy2(source_path, target_path)
        return target_path
    
    return create_template_copy

@pytest.fixture(scope="function")
def sample_json_patches():
    """Provide sample JSON patches for testing."""
    return {
        "powerpoint": [
            {
                "operation": "set",
                "target": "//p:sld//a:t[text()='Sample Presentation Title']",
                "value": "Test Title {{test_id}}"
            },
            {
                "operation": "set",
                "target": "//a:srgbClr[@val='000000']/@val",
                "value": "FF0000"
            }
        ],
        "word": [
            {
                "operation": "set",
                "target": "//w:t[contains(text(), 'Sample Document Title')]",
                "value": "Test Document {{test_id}}"
            },
            {
                "operation": "set",
                "target": "//w:color[@w:val='2F5496']/@w:val",
                "value": "008000"
            }
        ],
        "excel": [
            {
                "operation": "set",
                "target": "//worksheet//c[@r='A1']/v",
                "value": "Test Workbook {{test_id}}"
            },
            {
                "operation": "insert",
                "target": "//worksheet//sheetData",
                "value": '<row xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" r="20"><c r="A20" t="str"><v>Test Row {{timestamp}}</v></c></row>',
                "position": "append"
            }
        ]
    }

@pytest.fixture(scope="function")
def test_variables():
    """Provide test variables for patch processing."""
    return {
        "test_id": f"TEST_{int(time.time())}",
        "timestamp": str(int(time.time())),
        "company_name": "StyleStack Testing Inc",
        "environment": "integration_test",
        "version": "1.0.0"
    }

class TestMetrics:
    """Helper class for collecting test metrics."""
    
    def __init__(self):
        self.start_time = None
        self.metrics = {}
    
    def start_timing(self):
        """Start timing measurement."""
        self.start_time = time.time()
    
    def record_metric(self, name: str, value: Any):
        """Record a test metric."""
        self.metrics[name] = value
    
    def stop_timing(self) -> float:
        """Stop timing and return duration."""
        if self.start_time is None:
            return 0.0
        duration = time.time() - self.start_time
        self.metrics['duration_seconds'] = duration
        return duration
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        return self.metrics.copy()

@pytest.fixture(scope="function")
def test_metrics():
    """Provide test metrics collection."""
    return TestMetrics()

# Utility functions for tests

def verify_ooxml_structure(file_path: Path, expected_format: str) -> bool:
    """Verify OOXML file structure."""
    try:
        import zipfile
        with zipfile.ZipFile(file_path, 'r') as zipf:
            files = zipf.namelist()
            
            # Check for required files
            if "[Content_Types].xml" not in files:
                return False
            
            format_specific_checks = {
                "potx": "ppt/presentation.xml",
                "dotx": "word/document.xml",
                "xltx": "xl/workbook.xml"
            }
            
            required_file = format_specific_checks.get(expected_format)
            if required_file and required_file not in files:
                return False
            
            return True
    except Exception:
        return False

def extract_xml_content(ooxml_path: Path, xml_file_path: str) -> Optional[str]:
    """Extract XML content from OOXML file."""
    try:
        import zipfile
        with zipfile.ZipFile(ooxml_path, 'r') as zipf:
            if xml_file_path in zipf.namelist():
                return zipf.read(xml_file_path).decode('utf-8')
        return None
    except Exception:
        return None

# Pytest hooks for custom reporting

def pytest_runtest_setup(item):
    """Setup hook for individual test runs."""
    logging.info(f"Starting test: {item.name}")

def pytest_runtest_teardown(item, nextitem):
    """Teardown hook for individual test runs."""
    logging.info(f"Completed test: {item.name}")

@pytest.fixture(autouse=True)
def test_isolation():
    """Ensure test isolation by cleaning up any global state."""
    # Reset any global state before each test
    yield
    # Cleanup after each test
    import gc
    gc.collect()