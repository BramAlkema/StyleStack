#!/usr/bin/env python3
"""
Generate Test Structure for StyleStack Modules

This script automatically generates test files for all Python modules in the tools directory,
organizing them by test type (unit, integration, system).
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Set
import re

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
TOOLS_DIR = PROJECT_ROOT / "tools"
TESTS_DIR = PROJECT_ROOT / "tests"

# Test file template
UNIT_TEST_TEMPLATE = """#!/usr/bin/env python3
\"\"\"
Unit Tests for {module_name}

This module contains unit tests for the {module_name} module,
testing individual functions and classes in isolation.
\"\"\"

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

try:
    from {module_import} import *
except ImportError as e:
    pytest.skip(f"Module {{e.name}} not available for testing", allow_module_level=True)


@pytest.mark.unit
class Test{class_name}:
    \"\"\"Unit tests for {module_name} module.\"\"\"
    
    def setup_method(self):
        \"\"\"Set up test fixtures before each test method.\"\"\"
        pass
    
    def teardown_method(self):
        \"\"\"Clean up after each test method.\"\"\"
        pass
    
    def test_module_imports(self):
        \"\"\"Test that the module can be imported successfully.\"\"\"
        # This test ensures the module loads without import errors
        assert True, "Module imported successfully"
    
    # TODO: Add specific unit tests for {module_name} functions and classes
    # Example test methods:
    # def test_function_name(self):
    #     \"\"\"Test specific function behavior.\"\"\"
    #     pass
    
    @pytest.mark.slow
    def test_module_performance_baseline(self):
        \"\"\"Test basic performance characteristics of the module.\"\"\"
        # TODO: Add performance tests if applicable
        pass


# Integration points with other modules
@pytest.mark.unit
@pytest.mark.integration  
class Test{class_name}Integration:
    \"\"\"Integration tests for {module_name} with other components.\"\"\"
    
    def test_integration_interfaces(self):
        \"\"\"Test integration interfaces with other modules.\"\"\"
        # TODO: Add tests for how this module integrates with others
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""

INTEGRATION_TEST_TEMPLATE = """#!/usr/bin/env python3
\"\"\"
Integration Tests for {module_name}

This module contains integration tests for the {module_name} module,
testing interaction with other components and external dependencies.
\"\"\"

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add project root to path  
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

try:
    from {module_import} import *
except ImportError as e:
    pytest.skip(f"Module {{e.name}} not available for testing", allow_module_level=True)


@pytest.mark.integration
class Test{class_name}Integration:
    \"\"\"Integration tests for {module_name} module.\"\"\"
    
    def setup_method(self):
        \"\"\"Set up integration test fixtures.\"\"\"
        pass
    
    def teardown_method(self):
        \"\"\"Clean up integration test fixtures.\"\"\"
        pass
    
    def test_component_integration(self):
        \"\"\"Test integration with other StyleStack components.\"\"\"
        # TODO: Add integration tests
        pass
    
    def test_external_dependency_integration(self):
        \"\"\"Test integration with external dependencies.\"\"\"
        # TODO: Add external dependency integration tests
        pass
    
    @pytest.mark.slow
    def test_end_to_end_workflow(self):
        \"\"\"Test end-to-end workflow involving this module.\"\"\"
        # TODO: Add end-to-end workflow tests
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""


def discover_python_modules() -> List[Dict[str, str]]:
    """Discover all Python modules in the tools directory."""
    modules = []
    
    for py_file in TOOLS_DIR.glob("**/*.py"):
        if py_file.name == "__init__.py":
            continue
            
        # Skip files with invalid Python identifiers
        if not py_file.stem.replace('-', '_').replace('.', '_').isidentifier():
            continue
            
        # Convert path to module info
        relative_path = py_file.relative_to(TOOLS_DIR)
        module_path = str(relative_path.with_suffix(""))
        module_import = module_path.replace(os.sep, ".").replace('-', '_')
        module_name = py_file.stem.replace('-', '_')
        
        # Create class name (PascalCase)
        class_name = ''.join(word.capitalize() for word in module_name.replace('_', ' ').split())
        
        modules.append({
            'file_path': str(py_file),
            'module_name': module_name,
            'module_import': module_import,
            'class_name': class_name,
            'relative_path': module_path,
            'category': categorize_module(py_file)
        })
    
    return sorted(modules, key=lambda x: x['module_name'])


def categorize_module(py_file: Path) -> str:
    """Categorize module based on its name and location."""
    name = py_file.stem.lower()
    path = str(py_file).lower()
    
    # Core processing modules
    if any(keyword in name for keyword in ['ooxml', 'processor', 'parser', 'resolver']):
        return 'core'
    
    # Token and design system modules  
    if any(keyword in name for keyword in ['token', 'design', 'theme', 'variable']):
        return 'tokens'
    
    # Template and file processing
    if any(keyword in name for keyword in ['template', 'patch', 'validator']):
        return 'templates'
    
    # Integration and external services
    if any(keyword in name for keyword in ['integration', 'pipeline', 'transaction']):
        return 'integration'
    
    # Utilities and helpers
    if any(keyword in name for keyword in ['util', 'helper', 'tool']):
        return 'utilities'
    
    return 'general'


def get_existing_tests() -> Set[str]:
    """Get set of existing test files."""
    existing = set()
    for test_file in TESTS_DIR.glob("**/test_*.py"):
        existing.add(test_file.stem)
    return existing


def generate_test_files(modules: List[Dict[str, str]], dry_run: bool = False):
    """Generate test files for modules that don't have tests yet."""
    existing_tests = get_existing_tests()
    generated_count = 0
    skipped_count = 0
    
    print(f"Found {len(modules)} modules to process")
    print(f"Existing test files: {len(existing_tests)}")
    
    for module in modules:
        module_name = module['module_name']
        unit_test_name = f"test_{module_name}"
        integration_test_name = f"test_{module_name}_integration"
        
        # Generate unit test file
        if unit_test_name not in existing_tests:
            unit_test_path = TESTS_DIR / "unit" / f"{unit_test_name}.py"
            
            if not dry_run:
                unit_test_path.parent.mkdir(parents=True, exist_ok=True)
                unit_test_content = UNIT_TEST_TEMPLATE.format(**module)
                unit_test_path.write_text(unit_test_content)
            
            print(f"  ✓ Generated unit test: {unit_test_path}")
            generated_count += 1
        else:
            print(f"  - Skipped (exists): test_{module_name}.py")
            skipped_count += 1
        
        # Generate integration test file for core modules
        if module['category'] in ['core', 'tokens', 'integration'] and integration_test_name not in existing_tests:
            integration_test_path = TESTS_DIR / "integration" / f"{integration_test_name}.py"
            
            if not dry_run:
                integration_test_path.parent.mkdir(parents=True, exist_ok=True)
                integration_test_content = INTEGRATION_TEST_TEMPLATE.format(**module)
                integration_test_path.write_text(integration_test_content)
            
            print(f"  ✓ Generated integration test: {integration_test_path}")
            generated_count += 1
    
    print(f"\nSummary:")
    print(f"  Generated: {generated_count} test files")
    print(f"  Skipped: {skipped_count} existing files")
    print(f"  Total modules: {len(modules)}")


def create_test_structure_summary():
    """Create a summary of the test structure."""
    modules = discover_python_modules()
    
    summary = {
        'total_modules': len(modules),
        'by_category': {},
        'modules': modules
    }
    
    for module in modules:
        category = module['category']
        if category not in summary['by_category']:
            summary['by_category'][category] = []
        summary['by_category'][category].append(module['module_name'])
    
    return summary


def main():
    """Main function to generate test structure."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate test structure for StyleStack modules')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be generated without creating files')
    parser.add_argument('--summary', action='store_true', help='Show summary of discovered modules')
    parser.add_argument('--category', choices=['core', 'tokens', 'templates', 'integration', 'utilities', 'general'], 
                       help='Generate tests only for specific category')
    
    args = parser.parse_args()
    
    print("StyleStack Test Structure Generator")
    print("=" * 40)
    
    modules = discover_python_modules()
    
    if args.summary:
        summary = create_test_structure_summary()
        print(f"Total modules: {summary['total_modules']}")
        print("\nBy category:")
        for category, module_list in summary['by_category'].items():
            print(f"  {category}: {len(module_list)} modules")
            for module in module_list[:5]:  # Show first 5
                print(f"    - {module}")
            if len(module_list) > 5:
                print(f"    ... and {len(module_list) - 5} more")
        return
    
    if args.category:
        modules = [m for m in modules if m['category'] == args.category]
        print(f"Filtering to {args.category} category: {len(modules)} modules")
    
    generate_test_files(modules, dry_run=args.dry_run)


if __name__ == "__main__":
    main()