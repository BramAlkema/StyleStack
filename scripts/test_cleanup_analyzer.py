#!/usr/bin/env python3
"""
Test Infrastructure Cleanup Analyzer

Identifies unused methods, fixtures, and utilities in test files for cleanup.
"""

import ast
import json
from pathlib import Path
from typing import Dict, Set, List, Any, Tuple
import re


class TestMethodAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze test methods and utilities"""

    def __init__(self):
        self.defined_methods: Set[str] = set()
        self.called_methods: Set[str] = set()
        self.test_methods: Set[str] = set()
        self.fixtures: Set[str] = set()
        self.helper_methods: Set[str] = set()
        self.class_methods: Dict[str, Set[str]] = {}
        self.current_class = None
        self.imports: Set[str] = set()

    def visit_FunctionDef(self, node):
        """Visit function definitions"""
        method_name = node.name

        if self.current_class:
            full_name = f"{self.current_class}.{node.name}"
            self.class_methods.setdefault(self.current_class, set()).add(node.name)
        else:
            full_name = node.name

        self.defined_methods.add(full_name)

        # Categorize methods
        if method_name.startswith('test_'):
            self.test_methods.add(full_name)
        elif any(decorator.id == 'fixture' if hasattr(decorator, 'id')
                else (hasattr(decorator, 'attr') and decorator.attr == 'fixture')
                for decorator in node.decorator_list
                if hasattr(decorator, 'id') or hasattr(decorator, 'attr')):
            self.fixtures.add(full_name)
        elif (method_name.startswith(('setup_', 'teardown_', 'create_', 'mock_', 'helper_'))
              or method_name in ('setUp', 'tearDown')):
            self.helper_methods.add(full_name)

        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """Visit class definitions"""
        old_class = self.current_class
        self.current_class = node.name
        self.class_methods[node.name] = set()
        self.generic_visit(node)
        self.current_class = old_class

    def visit_Call(self, node):
        """Visit method/function calls"""
        if isinstance(node.func, ast.Attribute):
            self.called_methods.add(node.func.attr)
        elif isinstance(node.func, ast.Name):
            self.called_methods.add(node.func.id)
        self.generic_visit(node)

    def visit_Import(self, node):
        """Track imports"""
        for alias in node.names:
            self.imports.add(alias.name)

    def visit_ImportFrom(self, node):
        """Track from imports"""
        if node.module:
            for alias in node.names:
                self.imports.add(f"{node.module}.{alias.name}")


def analyze_test_file(file_path: Path, project_root: Path) -> Dict[str, Any]:
    """Analyze a single test file for unused methods"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        analyzer = TestMethodAnalyzer()
        analyzer.visit(tree)

        # Find unused methods (defined but not called)
        unused_methods = []
        for method in analyzer.defined_methods:
            # Skip test methods (they're entry points)
            if method in analyzer.test_methods:
                continue

            method_name = method.split('.')[-1]

            # Check if method is called anywhere
            if (method_name not in analyzer.called_methods and
                method not in analyzer.called_methods and
                not method_name.startswith('__') and  # Skip dunder methods
                not method_name in ('setUp', 'tearDown')):  # Skip standard unittest methods
                unused_methods.append(method)

        return {
            'file': str(file_path.relative_to(project_root)),
            'total_methods': len(analyzer.defined_methods),
            'test_methods': len(analyzer.test_methods),
            'fixtures': len(analyzer.fixtures),
            'helper_methods': len(analyzer.helper_methods),
            'unused_methods': unused_methods,
            'imports': list(analyzer.imports),
            'class_methods': {k: list(v) for k, v in analyzer.class_methods.items()}
        }

    except Exception as e:
        return {
            'file': str(file_path.relative_to(project_root)),
            'error': str(e),
            'unused_methods': []
        }


def find_duplicate_utilities(results: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Find duplicate utility methods across test files"""
    method_files = {}
    duplicates = {}

    for result in results:
        if 'class_methods' in result:
            for class_name, methods in result['class_methods'].items():
                for method in methods:
                    if method.startswith(('create_', 'mock_', 'setup_', 'helper_')):
                        key = f"{class_name}.{method}"
                        if key not in method_files:
                            method_files[key] = []
                        method_files[key].append(result['file'])

    # Find methods that appear in multiple files
    for method, files in method_files.items():
        if len(files) > 1:
            duplicates[method] = files

    return duplicates


def main():
    """Main test cleanup analysis"""
    project_root = Path.cwd()
    test_dir = project_root / "tests"

    if not test_dir.exists():
        print("❌ Tests directory not found")
        return

    print("🔍 Analyzing test infrastructure for cleanup opportunities...")
    print("=" * 70)

    # Find all test files
    test_files = list(test_dir.glob("**/*.py"))
    test_files = [f for f in test_files if not f.name.startswith('__')]

    print(f"📁 Found {len(test_files)} test files to analyze")

    results = []
    total_unused = 0

    # Analyze each test file
    for test_file in sorted(test_files):
        print(f"🔎 Analyzing {test_file.relative_to(project_root)}...")
        result = analyze_test_file(test_file, project_root)
        results.append(result)

        if 'error' in result:
            print(f"   ❌ Error: {result['error']}")
            continue

        unused_count = len(result['unused_methods'])
        total_unused += unused_count

        if unused_count > 0:
            print(f"   🧹 {unused_count} unused methods found")
            for method in result['unused_methods'][:3]:  # Show first 3
                print(f"     - {method}")
            if unused_count > 3:
                print(f"     ... and {unused_count - 3} more")
        else:
            print("   ✅ No unused methods")

    # Find duplicates
    print(f"\n🔍 Checking for duplicate utilities...")
    duplicates = find_duplicate_utilities(results)

    if duplicates:
        print(f"📋 Found {len(duplicates)} duplicate utility methods:")
        for method, files in list(duplicates.items())[:5]:  # Show first 5
            print(f"   • {method} in {len(files)} files")
    else:
        print("   ✅ No duplicate utilities found")

    # Summary
    print("\n" + "=" * 70)
    print(f"📊 Test Infrastructure Analysis Summary:")
    print(f"   Files analyzed: {len(results)}")
    print(f"   Total unused methods: {total_unused}")
    print(f"   Duplicate utilities: {len(duplicates)}")

    if total_unused > 0:
        print(f"   🧹 Cleanup opportunity: {total_unused} methods can be removed")
    else:
        print("   ✅ Test infrastructure is clean!")

    # Save results
    output_file = project_root / "test_cleanup_analysis.json"
    analysis_data = {
        'summary': {
            'files_analyzed': len(results),
            'total_unused_methods': total_unused,
            'duplicate_utilities': len(duplicates)
        },
        'files': results,
        'duplicates': duplicates
    }

    with open(output_file, 'w') as f:
        json.dump(analysis_data, f, indent=2)

    print(f"\n💾 Detailed results saved to: {output_file}")
    return analysis_data


if __name__ == "__main__":
    main()