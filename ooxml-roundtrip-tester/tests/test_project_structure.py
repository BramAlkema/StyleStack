"""Tests for OOXML Round-Trip Tester project structure and organization."""

import os
import sys
from pathlib import Path
import pytest
import importlib.util


class TestProjectStructure:
    """Test project directory structure and module organization."""
    
    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent
    
    def test_project_root_structure(self, project_root):
        """Test that required project directories exist."""
        expected_dirs = [
            "ooxml_tester",           # Main package
            "ooxml_tester/core",      # Core module
            "ooxml_tester/probe",     # Probe generation module
            "ooxml_tester/convert",   # Conversion engine module
            "ooxml_tester/analyze",   # Analysis module
            "ooxml_tester/report",    # Reporting module
            "tests",                  # Test directory
            "docs",                   # Documentation
        ]
        
        for dir_name in expected_dirs:
            dir_path = project_root / dir_name
            assert dir_path.exists(), f"Missing required directory: {dir_name}"
            assert dir_path.is_dir(), f"Path exists but is not a directory: {dir_name}"
    
    def test_package_init_files(self, project_root):
        """Test that all Python packages have __init__.py files."""
        package_dirs = [
            "ooxml_tester",
            "ooxml_tester/core",
            "ooxml_tester/probe", 
            "ooxml_tester/convert",
            "ooxml_tester/analyze",
            "ooxml_tester/report",
        ]
        
        for package_dir in package_dirs:
            init_file = project_root / package_dir / "__init__.py"
            assert init_file.exists(), f"Missing __init__.py in {package_dir}"
            assert init_file.is_file(), f"__init__.py is not a file in {package_dir}"
    
    def test_main_cli_entry_point(self, project_root):
        """Test that main CLI entry point exists."""
        cli_file = project_root / "ooxml_tester" / "cli.py"
        assert cli_file.exists(), "Missing CLI entry point: ooxml_tester/cli.py"
        assert cli_file.is_file(), "CLI entry point is not a file"
    
    def test_configuration_files(self, project_root):
        """Test that configuration files exist."""
        config_files = [
            "requirements.txt",
            "setup.py",
            ".gitignore",
            "README.md",
        ]
        
        for config_file in config_files:
            file_path = project_root / config_file
            assert file_path.exists(), f"Missing configuration file: {config_file}"
            assert file_path.is_file(), f"Configuration path is not a file: {config_file}"
    
    def test_requirements_content(self, project_root):
        """Test that requirements.txt contains expected dependencies."""
        requirements_file = project_root / "requirements.txt"
        content = requirements_file.read_text()
        
        expected_deps = [
            "click",
            "lxml", 
            "python-docx",
            "python-pptx",
            "openpyxl",
            "pytest",
        ]
        
        for dep in expected_deps:
            assert dep in content, f"Missing dependency in requirements.txt: {dep}"
    
    def test_package_imports(self, project_root):
        """Test that main package modules can be imported."""
        # Add project root to Python path temporarily
        sys.path.insert(0, str(project_root))
        
        try:
            # Test main package import
            spec = importlib.util.spec_from_file_location(
                "ooxml_tester", 
                project_root / "ooxml_tester" / "__init__.py"
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                assert hasattr(module, "__version__"), "Package should have __version__ attribute"
        finally:
            # Clean up Python path
            sys.path.remove(str(project_root))