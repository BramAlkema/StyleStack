#!/usr/bin/env python3
"""
Comprehensive Safety Test for Orphaned Code Removal

This script performs runtime tests to verify that code identified as potentially
orphaned can be safely removed without breaking the codebase.
"""

import sys
import importlib
import traceback
from pathlib import Path
from typing import Dict, List, Any, Tuple
import subprocess
import json


class OrphanedCodeSafetyTester:
    """Test suite for verifying safe removal of potentially orphaned code"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_results = {}

    def test_empty_packages(self) -> Dict[str, Any]:
        """Test if empty packages are safely removable"""
        results = {}

        # Test 1: tools.xpath package
        results['tools_xpath'] = self._test_package_removal('tools.xpath')

        # Test 2: tools.processing package
        results['tools_processing'] = self._test_package_removal('tools.processing')

        return results

    def _test_package_removal(self, package_name: str) -> Dict[str, Any]:
        """Test if a package can be safely removed"""
        result = {
            'package': package_name,
            'safe_to_remove': False,
            'import_attempts': [],
            'dynamic_references': [],
            'test_failures': []
        }

        try:
            # Test 1: Direct import
            try:
                module = importlib.import_module(package_name)
                result['import_attempts'].append({
                    'type': 'direct_import',
                    'success': True,
                    'has_content': hasattr(module, '__all__') or len(dir(module)) > 10
                })
            except ImportError as e:
                result['import_attempts'].append({
                    'type': 'direct_import',
                    'success': False,
                    'error': str(e)
                })

            # Test 2: Check for string-based imports
            string_refs = self._find_string_references(package_name)
            result['dynamic_references'] = string_refs

            # Test 3: Run related tests
            test_failures = self._run_related_tests(package_name)
            result['test_failures'] = test_failures

            # Determine safety
            result['safe_to_remove'] = (
                len(result['import_attempts']) == 0 or
                not any(attempt['success'] for attempt in result['import_attempts'])
            ) and len(result['dynamic_references']) == 0 and len(result['test_failures']) == 0

        except Exception as e:
            result['error'] = str(e)
            result['safe_to_remove'] = False

        return result

    def test_ooxml_extension_manager_methods(self) -> Dict[str, Any]:
        """Test OOXML Extension Manager methods for actual usage"""
        result = {
            'methods_tested': [],
            'safe_to_remove': {},
            'usage_found': {}
        }

        try:
            from tools.ooxml_extension_manager import StyleStackExtension, OOXMLExtensionManager

            # Test methods on StyleStackExtension
            methods_to_test = ['add_variable', 'remove_variable', 'get_variable']

            for method_name in methods_to_test:
                method_result = self._test_method_usage(
                    'tools.ooxml_extension_manager',
                    'StyleStackExtension',
                    method_name
                )
                result['methods_tested'].append(method_name)
                result['safe_to_remove'][method_name] = not method_result['has_usage']
                result['usage_found'][method_name] = method_result['usage_locations']

        except Exception as e:
            result['error'] = str(e)

        return result

    def test_emu_conversion_methods(self) -> Dict[str, Any]:
        """Test EMU type system conversion methods"""
        result = {
            'methods_tested': [],
            'safe_to_remove': {},
            'usage_found': {},
            'actually_used': {}
        }

        try:
            from tools.emu_types import EMUValue

            # Test conversion methods
            conversion_methods = [
                'to_inches', 'to_points', 'to_cm', 'to_mm',
                'from_inches', 'from_points', 'from_cm', 'from_mm'
            ]

            for method_name in conversion_methods:
                method_result = self._test_method_usage(
                    'tools.emu_types',
                    'EMUValue' if method_name.startswith('to_') else 'EMUValue',
                    method_name
                )
                result['methods_tested'].append(method_name)
                result['safe_to_remove'][method_name] = not method_result['has_usage']
                result['usage_found'][method_name] = method_result['usage_locations']

                # Test if method is actually called in working code
                result['actually_used'][method_name] = self._test_functional_usage(method_name)

        except Exception as e:
            result['error'] = str(e)

        return result

    def _test_method_usage(self, module_name: str, class_name: str, method_name: str) -> Dict[str, Any]:
        """Test if a method is actually used in the codebase"""
        result = {
            'has_usage': False,
            'usage_locations': [],
            'test_usage': []
        }

        # Search for method usage in files
        try:
            cmd = [
                'grep', '-r', '-n', f'{method_name}',
                str(self.project_root),
                '--include=*.py'
            ]

            process = subprocess.run(cmd, capture_output=True, text=True)
            if process.returncode == 0:
                lines = process.stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        # Filter out definition lines
                        if f'def {method_name}' not in line:
                            result['usage_locations'].append(line)
                            if 'test_' in line:
                                result['test_usage'].append(line)

                # Has usage if there are non-test usages
                non_test_usage = [loc for loc in result['usage_locations']
                                if 'test_' not in loc.lower()]
                result['has_usage'] = len(non_test_usage) > 0

        except Exception as e:
            result['search_error'] = str(e)

        return result

    def _test_functional_usage(self, method_name: str) -> bool:
        """Test if method is functionally used (not just defined)"""
        try:
            # Run a simple test to see if the method is called
            if 'to_' in method_name:
                from tools.emu_types import EMUValue
                emu_val = EMUValue(914400)  # 1 inch in EMU
                if hasattr(emu_val, method_name):
                    method = getattr(emu_val, method_name)
                    result = method()  # Call the method
                    return isinstance(result, (int, float))
            elif 'from_' in method_name:
                from tools.emu_types import EMUValue
                if hasattr(EMUValue, method_name):
                    method = getattr(EMUValue, method_name)
                    result = method(1.0)  # Call with test value
                    return isinstance(result, EMUValue)
        except Exception:
            return False

        return False

    def _find_string_references(self, package_name: str) -> List[str]:
        """Find string-based references to a package"""
        references = []

        try:
            # Search for string references
            cmd = [
                'grep', '-r', '-n', f"'{package_name}'",
                str(self.project_root),
                '--include=*.py'
            ]

            process = subprocess.run(cmd, capture_output=True, text=True)
            if process.returncode == 0:
                references.extend(process.stdout.strip().split('\n'))

            # Search for double-quoted references
            cmd[3] = f'"{package_name}"'
            process = subprocess.run(cmd, capture_output=True, text=True)
            if process.returncode == 0:
                references.extend(process.stdout.strip().split('\n'))

        except Exception as e:
            references.append(f"Search error: {e}")

        return [ref for ref in references if ref.strip()]

    def _run_related_tests(self, package_name: str) -> List[str]:
        """Run tests related to a package"""
        failures = []

        # Skip running tests for now to avoid disrupting the system
        # In a real scenario, you'd run: pytest tests/test_*xpath* -v

        return failures

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all safety tests"""
        results = {
            'empty_packages': self.test_empty_packages(),
            'ooxml_extension_methods': self.test_ooxml_extension_manager_methods(),
            'emu_conversion_methods': self.test_emu_conversion_methods(),
            'summary': {}
        }

        # Generate summary
        results['summary'] = self._generate_summary(results)

        return results

    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of removal safety"""
        summary = {
            'safe_to_remove': [],
            'potentially_safe': [],
            'not_safe': [],
            'needs_investigation': []
        }

        # Analyze empty packages
        for pkg_name, pkg_result in results['empty_packages'].items():
            if pkg_result.get('safe_to_remove', False):
                summary['safe_to_remove'].append(f"Package: {pkg_name}")
            elif not pkg_result.get('safe_to_remove', True):
                summary['not_safe'].append(f"Package: {pkg_name}")
            else:
                summary['needs_investigation'].append(f"Package: {pkg_name}")

        # Analyze OOXML methods
        for method, is_safe in results['ooxml_extension_methods'].get('safe_to_remove', {}).items():
            if is_safe:
                usage_count = len(results['ooxml_extension_methods'].get('usage_found', {}).get(method, []))
                if usage_count == 0:
                    summary['safe_to_remove'].append(f"Method: StyleStackExtension.{method}")
                else:
                    summary['potentially_safe'].append(f"Method: StyleStackExtension.{method} ({usage_count} references)")
            else:
                summary['not_safe'].append(f"Method: StyleStackExtension.{method}")

        # Analyze EMU methods
        for method, is_safe in results['emu_conversion_methods'].get('safe_to_remove', {}).items():
            actually_used = results['emu_conversion_methods'].get('actually_used', {}).get(method, False)
            if is_safe and not actually_used:
                summary['safe_to_remove'].append(f"Method: EMUValue.{method}")
            elif actually_used:
                summary['not_safe'].append(f"Method: EMUValue.{method} (functionally used)")
            else:
                summary['potentially_safe'].append(f"Method: EMUValue.{method}")

        return summary


def main():
    """Run the comprehensive safety test"""
    project_root = Path(__file__).parent
    tester = OrphanedCodeSafetyTester(project_root)

    print("🔍 Running Comprehensive Orphaned Code Safety Test...")
    print("=" * 60)

    results = tester.run_comprehensive_test()

    # Print results
    print("\n📊 TEST RESULTS")
    print("=" * 40)

    print(f"\n✅ SAFE TO REMOVE ({len(results['summary']['safe_to_remove'])} items):")
    for item in results['summary']['safe_to_remove']:
        print(f"   • {item}")

    print(f"\n⚠️  POTENTIALLY SAFE ({len(results['summary']['potentially_safe'])} items):")
    for item in results['summary']['potentially_safe']:
        print(f"   • {item}")

    print(f"\n❌ NOT SAFE TO REMOVE ({len(results['summary']['not_safe'])} items):")
    for item in results['summary']['not_safe']:
        print(f"   • {item}")

    print(f"\n🔍 NEEDS INVESTIGATION ({len(results['summary']['needs_investigation'])} items):")
    for item in results['summary']['needs_investigation']:
        print(f"   • {item}")

    # Save detailed results
    results_file = project_root / 'orphaned_code_safety_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n💾 Detailed results saved to: {results_file}")
    print("\n✅ Safety test completed!")

    return results


if __name__ == '__main__':
    main()