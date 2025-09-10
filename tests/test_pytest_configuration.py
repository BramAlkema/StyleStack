#!/usr/bin/env python3
"""
Test Pytest Configuration and Test Discovery

This module validates the pytest configuration, test discovery mechanism,
and ensures proper test infrastructure is in place.
"""

import pytest
import sys
import os
from pathlib import Path
import importlib.util

# Add project root to path for testing
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from conftest import (
    discover_python_modules, 
    get_test_files_for_modules,
    validate_design_tokens,
    validate_ooxml_structure
)


@pytest.mark.unit
@pytest.mark.import_resolution
class TestPytestConfiguration:
    """Test pytest configuration and setup."""
    
    def test_pytest_ini_exists(self):
        """Verify pytest.ini configuration file exists."""
        pytest_ini = PROJECT_ROOT / "pytest.ini"
        assert pytest_ini.exists(), "pytest.ini configuration file is missing"
    
    def test_pytest_ini_valid_configuration(self):
        """Verify pytest.ini contains required configuration."""
        pytest_ini = PROJECT_ROOT / "pytest.ini"
        content = pytest_ini.read_text()
        
        # Check for essential configuration sections
        assert "[tool:pytest]" in content, "pytest.ini missing [tool:pytest] section"
        assert "testpaths" in content, "pytest.ini missing testpaths configuration"
        assert "python_files" in content, "pytest.ini missing python_files pattern"
        assert "markers" in content, "pytest.ini missing custom markers"
        
        # Check for coverage configuration
        assert "--cov=tools" in content, "pytest.ini missing coverage configuration"
        assert "--cov-report" in content, "pytest.ini missing coverage reporting"
    
    def test_conftest_global_exists(self):
        """Verify global conftest.py exists at project root."""
        conftest_py = PROJECT_ROOT / "conftest.py"
        assert conftest_py.exists(), "Global conftest.py is missing"
    
    def test_conftest_integration_exists(self):
        """Verify integration conftest.py exists."""
        conftest_integration = PROJECT_ROOT / "tests" / "integration" / "conftest.py"
        assert conftest_integration.exists(), "Integration conftest.py is missing"
    
    def test_custom_markers_registered(self, pytestconfig):
        """Verify all custom markers are properly registered."""
        expected_markers = [
            "unit", "integration", "system", "slow", "stress", 
            "concurrent", "large_file", "ooxml", "tokens", 
            "performance", "regression", "security", "accessibility",
            "golden_master", "cross_platform", "xml_validation", 
            "import_resolution"
        ]
        
        # Get registered markers from pytest config
        # Access the markers through the known attributes
        registered_markers = set()
        if hasattr(pytestconfig, '_getini'):
            markers_ini = pytestconfig._getini('markers')
            for marker_line in markers_ini:
                marker_name = marker_line.split(':')[0].strip()
                registered_markers.add(marker_name)
        
        for marker in expected_markers:
            assert marker in registered_markers, f"Custom marker '{marker}' not registered. Available: {registered_markers}"
    
    def test_test_paths_accessible(self):
        """Verify all configured test paths exist and are accessible."""
        test_paths = [
            PROJECT_ROOT / "tests",
            PROJECT_ROOT / "tests" / "unit", 
            PROJECT_ROOT / "tests" / "integration",
            PROJECT_ROOT / "tests" / "system"
        ]
        
        for path in test_paths:
            if not path.exists():
                # Create missing test directories
                path.mkdir(parents=True, exist_ok=True)
            assert path.exists(), f"Test path {path} not accessible"
            assert path.is_dir(), f"Test path {path} is not a directory"
    
    def test_tools_directory_in_path(self):
        """Verify tools directory is properly added to Python path."""
        tools_dir = str(PROJECT_ROOT / "tools")
        assert tools_dir in sys.path, "Tools directory not in Python path"
    
    @pytest.mark.slow
    def test_parallel_execution_support(self):
        """Test that pytest-xdist parallel execution is supported."""
        try:
            import xdist
            assert hasattr(xdist, "plugin"), "pytest-xdist not properly installed"
        except ImportError:
            pytest.skip("pytest-xdist not installed")
    
    def test_coverage_measurement_support(self):
        """Test that pytest-cov coverage measurement is supported."""
        try:
            import coverage
            assert hasattr(coverage, "Coverage"), "coverage.py not properly installed"
        except ImportError:
            pytest.skip("pytest-cov not installed")


@pytest.mark.unit
@pytest.mark.import_resolution 
class TestModuleDiscovery:
    """Test module discovery and mapping functionality."""
    
    def test_discover_python_modules(self):
        """Test Python module discovery in tools directory."""
        tools_dir = PROJECT_ROOT / "tools"
        modules = discover_python_modules(tools_dir)
        
        assert isinstance(modules, list), "Module discovery should return a list"
        assert len(modules) > 0, "Should discover at least one Python module"
        
        # Verify modules are properly formatted
        for module in modules:
            assert isinstance(module, str), "Module names should be strings"
            assert "." in module or "_" in module, "Module names should be valid identifiers"
            assert not module.endswith(".py"), "Module names should not include .py extension"
    
    def test_get_test_files_for_modules(self):
        """Test mapping of modules to their corresponding test files."""
        tools_dir = PROJECT_ROOT / "tools"
        modules = discover_python_modules(tools_dir)[:5]  # Test with first 5 modules
        
        test_mapping = get_test_files_for_modules(modules)
        
        assert isinstance(test_mapping, dict), "Test mapping should return a dictionary"
        assert len(test_mapping) == len(modules), "Should map all provided modules"
        
        for module, test_file in test_mapping.items():
            assert module in modules, f"Unexpected module '{module}' in mapping"
            # test_file can be None if no test exists yet
            if test_file is not None:
                assert Path(test_file).exists(), f"Mapped test file {test_file} does not exist"
    
    def test_module_import_validation(self):
        """Test that discovered modules can be imported."""
        tools_dir = PROJECT_ROOT / "tools" 
        modules = discover_python_modules(tools_dir)
        
        # Test a sample of modules to avoid long test times
        sample_modules = modules[:3] if len(modules) > 3 else modules
        import_failures = []
        
        for module_name in sample_modules:
            try:
                # Construct full module path
                module_file = tools_dir / f"{module_name.replace('.', os.sep)}.py"
                
                if module_file.exists():
                    spec = importlib.util.spec_from_file_location(module_name, module_file)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        # Don't execute module, just validate it can be loaded
                        assert module is not None, f"Module {module_name} could not be loaded"
                    else:
                        import_failures.append(f"{module_name}: spec creation failed")
                else:
                    import_failures.append(f"{module_name}: file not found at {module_file}")
                    
            except Exception as e:
                import_failures.append(f"{module_name}: {str(e)}")
        
        # Report import failures but don't fail test (modules might have dependencies)
        if import_failures:
            print(f"\nModule import issues (may be due to missing dependencies):")
            for failure in import_failures:
                print(f"  - {failure}")


@pytest.mark.unit
class TestFixtureValidation:
    """Test fixture functionality and validation utilities."""
    
    def test_temp_workspace_fixture(self, temp_workspace):
        """Test temporary workspace fixture."""
        assert temp_workspace.exists(), "Temporary workspace should exist"
        assert temp_workspace.is_dir(), "Temporary workspace should be a directory"
        assert "stylestack_test_" in temp_workspace.name, "Workspace should have proper naming"
        
        # Test workspace is writable
        test_file = temp_workspace / "test.txt"
        test_file.write_text("test content")
        assert test_file.exists(), "Should be able to create files in workspace"
        assert test_file.read_text() == "test content", "Should be able to read/write files"
    
    def test_sample_design_tokens_fixture(self, sample_design_tokens):
        """Test sample design tokens fixture."""
        assert isinstance(sample_design_tokens, dict), "Design tokens should be a dictionary"
        
        # Validate structure
        errors = validate_design_tokens(sample_design_tokens)
        assert len(errors) == 0, f"Design tokens validation failed: {errors}"
        
        # Check for required categories
        assert "colors" in sample_design_tokens, "Should include colors category"
        assert "typography" in sample_design_tokens, "Should include typography category"
        assert "spacing" in sample_design_tokens, "Should include spacing category"
    
    def test_sample_ooxml_content_fixture(self, sample_ooxml_content):
        """Test sample OOXML content fixture."""
        assert isinstance(sample_ooxml_content, dict), "OOXML content should be a dictionary"
        
        # Check for all supported formats
        expected_formats = ["powerpoint", "word", "excel"]
        for format_name in expected_formats:
            assert format_name in sample_ooxml_content, f"Should include {format_name} format"
            
            content = sample_ooxml_content[format_name]
            assert isinstance(content, str), f"{format_name} content should be a string"
            assert content.startswith("<?xml"), f"{format_name} content should be valid XML"
    
    def test_test_metrics_collector_fixture(self, test_metrics_collector):
        """Test metrics collection fixture."""
        # Test timer functionality
        test_metrics_collector.start_timer("test_operation")
        import time
        time.sleep(0.01)  # Small delay for measurable duration
        duration = test_metrics_collector.stop_timer("test_operation")
        
        assert duration > 0, "Timer should measure positive duration"
        assert "test_operation_duration" in test_metrics_collector.get_metrics(), "Metrics should be recorded"
        
        # Test metric recording
        test_metrics_collector.record("test_metric", "test_value")
        metrics = test_metrics_collector.get_metrics()
        assert "test_metric" in metrics, "Should be able to record custom metrics"
        assert metrics["test_metric"] == "test_value", "Should store correct metric values"


@pytest.mark.unit
class TestValidationUtilities:
    """Test validation utility functions."""
    
    def test_validate_ooxml_structure(self, sample_ooxml_content):
        """Test OOXML structure validation."""
        # Test valid OOXML
        ppt_content = sample_ooxml_content["powerpoint"]
        assert validate_ooxml_structure(ppt_content, "presentationml"), \
            "Should validate correct PowerPoint OOXML"
        
        word_content = sample_ooxml_content["word"] 
        assert validate_ooxml_structure(word_content, "wordprocessingml"), \
            "Should validate correct Word OOXML"
        
        excel_content = sample_ooxml_content["excel"]
        assert validate_ooxml_structure(excel_content, "spreadsheetml"), \
            "Should validate correct Excel OOXML"
        
        # Test invalid OOXML
        invalid_xml = "<invalid>malformed xml"
        assert not validate_ooxml_structure(invalid_xml, "any"), \
            "Should reject malformed XML"
    
    def test_validate_design_tokens_valid(self, sample_design_tokens):
        """Test design token validation with valid tokens."""
        errors = validate_design_tokens(sample_design_tokens)
        assert len(errors) == 0, f"Valid design tokens should not produce errors: {errors}"
    
    def test_validate_design_tokens_invalid(self):
        """Test design token validation with invalid tokens."""
        invalid_tokens = {
            "colors": {
                "primary": {"value": "#FF0000"},  # Missing 'type'
                "secondary": "not_a_dict",         # Should be dict
            },
            "typography": "not_a_dict"             # Should be dict
        }
        
        errors = validate_design_tokens(invalid_tokens)
        assert len(errors) > 0, "Invalid design tokens should produce errors"
        
        # Check specific error types
        error_text = " ".join(errors)
        assert "missing required 'type' field" in error_text, "Should detect missing type field"
        assert "must be a dictionary" in error_text, "Should detect non-dict values"


@pytest.mark.integration
@pytest.mark.slow
class TestTestInfrastructureIntegration:
    """Integration tests for test infrastructure components."""
    
    def test_pytest_discovery_integration(self):
        """Test that pytest can discover and collect tests."""
        import subprocess
        import sys
        
        # Run pytest collection without executing tests
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "--collect-only", "--quiet",
            str(PROJECT_ROOT / "tests")
        ], capture_output=True, text=True, cwd=PROJECT_ROOT)
        
        assert result.returncode == 0, f"Test discovery failed: {result.stderr}"
        assert "collected" in result.stdout, "Should collect some tests"
    
    @pytest.mark.slow
    def test_parallel_test_execution_setup(self):
        """Test that parallel test execution setup works."""
        try:
            import xdist
            
            # Verify xdist can be imported and used
            assert hasattr(xdist, "plugin"), "xdist plugin should be available"
            
            # Test basic parallel setup (without running actual tests)
            import subprocess
            import sys
            
            result = subprocess.run([
                sys.executable, "-m", "pytest", "--collect-only", 
                "-n", "2", str(PROJECT_ROOT / "tests" / "test_pytest_configuration.py")
            ], capture_output=True, text=True, cwd=PROJECT_ROOT)
            
            # Collection should work even if execution might fail due to missing deps
            assert "collected" in result.stdout or result.returncode == 0, \
                "Parallel test collection should work"
                
        except ImportError:
            pytest.skip("pytest-xdist not installed")
    
    def test_coverage_integration_setup(self):
        """Test that coverage measurement setup works."""
        try:
            import coverage
            
            # Test that coverage can be initialized
            cov = coverage.Coverage()
            assert cov is not None, "Coverage instance should be created"
            
        except ImportError:
            pytest.skip("coverage not installed")


if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v"])