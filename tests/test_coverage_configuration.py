#!/usr/bin/env python3
"""
Test Coverage Configuration

This module tests the code coverage measurement setup and validates
that pytest-cov is properly configured and functional.
"""

import pytest
import subprocess
import sys
import os
import json
from pathlib import Path
import tempfile
import configparser


@pytest.mark.unit
@pytest.mark.parallel_safe
class TestCoverageConfiguration:
    """Test coverage measurement configuration."""
    
    def test_pytest_cov_available(self):
        """Test that pytest-cov is available for import."""
        try:
            import pytest_cov
            assert pytest_cov is not None, "pytest-cov should be importable"
            
            # Test coverage module availability
            import coverage
            assert hasattr(coverage, 'Coverage'), "Coverage class should be available"
            
        except ImportError:
            pytest.skip("pytest-cov not installed")
    
    def test_coverage_configuration_files_exist(self):
        """Test that coverage configuration files exist."""
        project_root = Path(__file__).parent.parent
        
        config_files = [
            ".coveragerc",
            "pyproject.toml"
        ]
        
        for config_file in config_files:
            config_path = project_root / config_file
            assert config_path.exists(), f"Configuration file {config_file} should exist"
    
    def test_coveragerc_configuration(self):
        """Test .coveragerc configuration."""
        project_root = Path(__file__).parent.parent
        coveragerc = project_root / ".coveragerc"
        
        config = configparser.ConfigParser()
        config.read(coveragerc)
        
        # Check run configuration
        assert "run" in config.sections(), "Should have [run] section"
        run_config = config["run"]
        assert "source" in run_config, "Should specify source directory"
        assert "tools/" in run_config["source"], "Should include tools directory"
        assert "branch" in run_config, "Should enable branch coverage"
        assert run_config.getboolean("branch"), "Branch coverage should be enabled"
        
        # Check report configuration
        assert "report" in config.sections(), "Should have [report] section"
        report_config = config["report"]
        assert "show_missing" in report_config, "Should show missing lines"
        assert report_config.getboolean("show_missing"), "Should show missing lines"
    
    def test_pyproject_toml_coverage_config(self):
        """Test pyproject.toml coverage configuration."""
        project_root = Path(__file__).parent.parent
        pyproject = project_root / "pyproject.toml"
        
        content = pyproject.read_text()
        
        # Check for coverage configuration sections
        assert "[tool.coverage.run]" in content, "Should have coverage run configuration"
        assert "[tool.coverage.report]" in content, "Should have coverage report configuration"
        assert "[tool.coverage.html]" in content, "Should have HTML report configuration"
        assert "[tool.coverage.xml]" in content, "Should have XML report configuration"
        
        # Check for source specification
        assert 'source = ["tools"]' in content, "Should specify tools as source"
        assert "branch = true" in content, "Should enable branch coverage"
    
    def test_coverage_source_paths(self):
        """Test that coverage source paths are correctly configured."""
        project_root = Path(__file__).parent.parent
        tools_dir = project_root / "tools"
        
        assert tools_dir.exists(), "Tools directory should exist for coverage measurement"
        assert tools_dir.is_dir(), "Tools should be a directory"
        
        # Check for Python files in tools directory
        python_files = list(tools_dir.glob("**/*.py"))
        assert len(python_files) > 0, "Tools directory should contain Python files"
    
    def test_coverage_omit_patterns(self):
        """Test that coverage omit patterns are reasonable."""
        project_root = Path(__file__).parent.parent
        
        # Read omit patterns from .coveragerc
        config = configparser.ConfigParser()
        config.read(project_root / ".coveragerc")
        
        omit_raw = config.get("run", "omit", fallback="")
        omit_patterns = [line.strip() for line in omit_raw.split('\n') if line.strip()]
        
        # Should omit test files
        test_patterns = [p for p in omit_patterns if "test" in p.lower()]
        assert len(test_patterns) > 0, "Should omit test files from coverage"
        
        # Should omit virtual environment
        venv_patterns = [p for p in omit_patterns if "venv" in p.lower()]
        assert len(venv_patterns) > 0, "Should omit virtual environment"
        
        # Should omit build directories
        build_patterns = [p for p in omit_patterns if any(word in p.lower() for word in ["build", "dist"])]
        assert len(build_patterns) > 0, "Should omit build directories"
    
    @pytest.mark.slow
    def test_coverage_measurement_dry_run(self):
        """Test coverage measurement without actually running tests."""
        try:
            import coverage
            
            # Create coverage instance
            cov = coverage.Coverage(
                source=["tools"],
                branch=True,
                config_file=Path(__file__).parent.parent / ".coveragerc"
            )
            
            assert cov is not None, "Coverage instance should be created"
            
            # Test coverage configuration
            config = cov.get_option("run:source")
            assert "tools" in str(config), "Coverage should be configured for tools directory"
            
            # Test branch coverage setting
            branch_setting = cov.get_option("run:branch")
            assert branch_setting, "Branch coverage should be enabled"
            
        except ImportError:
            pytest.skip("coverage not installed")
    
    def test_coverage_report_formats(self):
        """Test that all required coverage report formats are configured."""
        project_root = Path(__file__).parent.parent
        
        # Check .coveragerc for report formats
        config = configparser.ConfigParser()
        config.read(project_root / ".coveragerc")
        
        # Should have HTML configuration
        assert "html" in config.sections(), "Should have HTML report configuration"
        html_config = config["html"]
        assert "directory" in html_config, "Should specify HTML report directory"
        
        # Should have XML configuration  
        assert "xml" in config.sections(), "Should have XML report configuration"
        xml_config = config["xml"]
        assert "output" in xml_config, "Should specify XML output file"
        
        # Should have JSON configuration
        assert "json" in config.sections(), "Should have JSON report configuration"
        json_config = config["json"]
        assert "output" in json_config, "Should specify JSON output file"


@pytest.mark.integration
@pytest.mark.parallel_safe
class TestCoverageIntegration:
    """Integration tests for coverage measurement."""
    
    @pytest.mark.slow
    def test_coverage_with_simple_test(self):
        """Test coverage measurement with a simple test."""
        
        # Create a simple Python module for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a simple module
            module_content = '''
def add(a, b):
    """Simple addition function."""
    return a + b

def subtract(a, b):
    """Simple subtraction function."""
    return a - b

def unused_function():
    """Function that won't be called in tests."""
    return "unused"
'''
            module_file = temp_path / "test_module.py"
            module_file.write_text(module_content)
            
            # Create a simple test
            test_content = '''
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from test_module import add, subtract

def test_add():
    assert add(2, 3) == 5

def test_subtract():
    assert subtract(5, 3) == 2
'''
            test_file = temp_path / "test_simple.py"
            test_file.write_text(test_content)
            
            # Run coverage measurement
            try:
                import coverage
                
                cov = coverage.Coverage(
                    source=[str(temp_path)],
                    branch=True
                )
                cov.start()
                
                # Import and use the module (simulating test execution)
                sys.path.insert(0, str(temp_path))
                try:
                    import test_module
                    result1 = test_module.add(2, 3)
                    result2 = test_module.subtract(5, 3)
                    assert result1 == 5
                    assert result2 == 2
                finally:
                    sys.path.remove(str(temp_path))
                
                cov.stop()
                cov.save()
                
                # Analyze coverage
                coverage_data = cov.get_data()
                files = coverage_data.measured_files()
                
                # Should have measured the test module
                test_module_files = [f for f in files if "test_module.py" in f]
                assert len(test_module_files) > 0, "Should measure coverage for test module"
                
                # Generate report
                report = cov.report(show_missing=True)
                assert report is not None, "Should generate coverage report"
                
            except ImportError:
                pytest.skip("coverage not installed")
    
    @pytest.mark.slow
    def test_pytest_cov_integration(self):
        """Test pytest-cov integration."""
        project_root = Path(__file__).parent.parent
        
        # Create a minimal test file to run coverage on
        test_cmd = [
            sys.executable, "-m", "pytest",
            "--cov=tests",  # Use tests directory for this integration test
            "--cov-report=term",
            "--cov-report=json:test_coverage.json",
            str(__file__ + "::TestCoverageConfiguration::test_pytest_cov_available"),
            "--verbose"
        ]
        
        try:
            result = subprocess.run(
                test_cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=project_root
            )
            
            # Should run successfully (even if coverage is low)
            assert result.returncode == 0, f"pytest-cov integration failed: {result.stderr}"
            
            # Should mention coverage in output
            assert "coverage" in result.stdout.lower() or "cov" in result.stdout.lower(), \
                "Coverage information should be in output"
            
            # Check if JSON report was generated
            json_report = project_root / "test_coverage.json"
            if json_report.exists():
                # Validate JSON report structure
                with open(json_report, 'r') as f:
                    coverage_data = json.load(f)
                
                assert "files" in coverage_data, "JSON report should contain files data"
                assert "totals" in coverage_data, "JSON report should contain totals"
                
                # Clean up
                json_report.unlink()
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("pytest-cov integration test could not be completed")
    
    def test_coverage_threshold_configuration(self):
        """Test coverage threshold configuration."""
        project_root = Path(__file__).parent.parent
        
        # Check pytest configuration for coverage thresholds
        pytest_ini = project_root / "pytest.ini"
        if pytest_ini.exists():
            content = pytest_ini.read_text()
            # Look for coverage fail-under setting
            if "--cov-fail-under" in content:
                # Extract threshold value
                lines = content.split('\n')
                for line in lines:
                    if "--cov-fail-under" in line:
                        # Should have a reasonable threshold
                        assert "80" in line or "85" in line or "90" in line, \
                            "Should have reasonable coverage threshold"
        
        # Check parallel configuration
        parallel_ini = project_root / "pytest-parallel.ini"
        if parallel_ini.exists():
            content = parallel_ini.read_text()
            if "--cov-fail-under" in content:
                # Should have threshold configured for parallel execution too
                assert any(threshold in content for threshold in ["80", "85", "90"]), \
                    "Parallel configuration should have coverage threshold"


@pytest.mark.unit
@pytest.mark.parallel_safe
class TestCoverageReporting:
    """Test coverage reporting functionality."""
    
    def test_html_report_configuration(self):
        """Test HTML coverage report configuration."""
        project_root = Path(__file__).parent.parent
        
        config = configparser.ConfigParser()
        config.read(project_root / ".coveragerc")
        
        if "html" in config.sections():
            html_config = config["html"]
            
            # Check directory setting
            if "directory" in html_config:
                html_dir = html_config["directory"]
                assert html_dir in ["htmlcov", "reports/htmlcov"], \
                    "HTML report directory should be reasonable"
            
            # Check title setting
            if "title" in html_config:
                title = html_config["title"]
                assert "StyleStack" in title, "Title should mention StyleStack"
    
    def test_xml_report_configuration(self):
        """Test XML coverage report configuration."""
        project_root = Path(__file__).parent.parent
        
        config = configparser.ConfigParser()
        config.read(project_root / ".coveragerc")
        
        if "xml" in config.sections():
            xml_config = config["xml"]
            
            # Check output setting
            if "output" in xml_config:
                output_file = xml_config["output"]
                assert output_file.endswith(".xml"), "XML output should have .xml extension"
                assert "coverage" in output_file.lower(), "XML output should mention coverage"
    
    def test_json_report_configuration(self):
        """Test JSON coverage report configuration."""
        project_root = Path(__file__).parent.parent
        
        config = configparser.ConfigParser()
        config.read(project_root / ".coveragerc")
        
        if "json" in config.sections():
            json_config = config["json"]
            
            # Check output setting
            if "output" in json_config:
                output_file = json_config["output"]
                assert output_file.endswith(".json"), "JSON output should have .json extension"
                assert "coverage" in output_file.lower(), "JSON output should mention coverage"
    
    def test_coverage_context_support(self):
        """Test coverage context support for parallel execution."""
        project_root = Path(__file__).parent.parent
        
        # Check pyproject.toml for context configuration
        pyproject = project_root / "pyproject.toml"
        content = pyproject.read_text()
        
        # Should support contexts for parallel execution
        if "[tool.coverage.run]" in content:
            # Look for context or concurrency settings
            assert any(setting in content for setting in [
                "context", "concurrency", "parallel"
            ]), "Should have parallel execution support"
    
    @pytest.mark.slow
    def test_coverage_report_generation_simulation(self):
        """Test coverage report generation simulation."""
        
        # Simulate coverage data structure
        mock_coverage_data = {
            "files": {
                "tools/example.py": {
                    "executed_lines": [1, 2, 3, 5, 7],
                    "missing_lines": [4, 6, 8],
                    "excluded_lines": [],
                    "summary": {
                        "covered_lines": 5,
                        "num_statements": 8,
                        "percent_covered": 62.5,
                        "missing_lines": 3
                    }
                }
            },
            "totals": {
                "covered_lines": 5,
                "num_statements": 8,
                "percent_covered": 62.5,
                "missing_lines": 3
            }
        }
        
        # Validate structure
        assert "files" in mock_coverage_data, "Coverage data should have files"
        assert "totals" in mock_coverage_data, "Coverage data should have totals"
        
        # Validate file data
        for filename, file_data in mock_coverage_data["files"].items():
            assert "executed_lines" in file_data, "File data should have executed lines"
            assert "missing_lines" in file_data, "File data should have missing lines" 
            assert "summary" in file_data, "File data should have summary"
            
            summary = file_data["summary"]
            assert "percent_covered" in summary, "Summary should have coverage percentage"
            assert 0 <= summary["percent_covered"] <= 100, "Coverage percentage should be valid"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])