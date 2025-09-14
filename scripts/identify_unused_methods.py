#!/usr/bin/env python3
"""
Script to identify unused methods in core modules

Based on the dependency graph analysis, identifies methods that are:
1. Defined in the core modules
2. Not called anywhere in the codebase
3. Not part of public APIs or interfaces
4. Safe to remove without breaking functionality
"""

import ast
import json
from pathlib import Path
from typing import Dict, Set, List, Any


class MethodAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze method definitions and calls"""

    def __init__(self):
        self.defined_methods: Set[str] = set()
        self.called_methods: Set[str] = set()
        self.class_methods: Dict[str, Set[str]] = {}
        self.current_class = None

    def visit_FunctionDef(self, node):
        """Visit function definitions"""
        if self.current_class:
            method_name = f"{self.current_class}.{node.name}"
            self.class_methods.setdefault(self.current_class, set()).add(node.name)
        else:
            method_name = node.name

        self.defined_methods.add(method_name)
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
            # Method call: obj.method()
            self.called_methods.add(node.func.attr)
            if hasattr(node.func.value, 'id'):
                # Class method: ClassName.method()
                self.called_methods.add(f"{node.func.value.id}.{node.func.attr}")
        elif isinstance(node.func, ast.Name):
            # Function call: function()
            self.called_methods.add(node.func.id)

        self.generic_visit(node)

    def visit_Attribute(self, node):
        """Visit attribute access (for getattr, etc.)"""
        if isinstance(node.attr, str):
            self.called_methods.add(node.attr)
        self.generic_visit(node)


def analyze_file(file_path: Path) -> MethodAnalyzer:
    """Analyze a Python file and return method information"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()

        tree = ast.parse(source, filename=str(file_path))
        analyzer = MethodAnalyzer()
        analyzer.visit(tree)
        return analyzer
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return MethodAnalyzer()


def find_unused_methods_in_module(module_path: Path, project_root: Path) -> Dict[str, Any]:
    """Find unused methods in a specific module"""
    print(f"Analyzing {module_path.name}...")

    # Analyze the target module
    module_analyzer = analyze_file(module_path)

    # Get all defined methods
    defined = module_analyzer.defined_methods.copy()

    # Analyze all Python files in project to find method calls
    all_called = set()

    for py_file in project_root.rglob("*.py"):
        if py_file == module_path:
            continue  # Skip the module we're analyzing

        try:
            analyzer = analyze_file(py_file)
            all_called.update(analyzer.called_methods)
        except Exception as e:
            continue

    # Find methods that are defined but never called
    potentially_unused = set()
    definitely_unused = set()

    for method in defined:
        method_name = method.split('.')[-1]  # Get just the method name

        # Check if method is called anywhere
        is_called = (
            method in all_called or
            method_name in all_called or
            any(call.endswith(f".{method_name}") for call in all_called)
        )

        if not is_called:
            # Check if it's a special method
            if (method_name.startswith('__') and method_name.endswith('__')) or method_name in ['__init__', '__str__', '__repr__']:
                continue  # Skip special methods

            # Check if it's in __all__
            if method_name in ['__all__']:
                continue

            potentially_unused.add(method)

    # Read the actual file content to cross-reference
    try:
        content = module_path.read_text()

        for method in potentially_unused:
            method_name = method.split('.')[-1]

            # Check if method appears in strings (docstrings, etc.)
            if f"'{method_name}'" in content or f'"{method_name}"' in content:
                continue

            # Check if it's exported in __all__
            if f"'{method_name}'" in content and "__all__" in content:
                continue

            definitely_unused.add(method)

    except Exception as e:
        print(f"Error reading {module_path}: {e}")
        definitely_unused = potentially_unused

    return {
        "module": str(module_path),
        "total_methods": len(defined),
        "potentially_unused": sorted(potentially_unused),
        "definitely_unused": sorted(definitely_unused),
        "class_methods": {k: list(v) for k, v in module_analyzer.class_methods.items()}
    }


def main():
    """Main analysis function"""
    project_root = Path.cwd()

    # Core modules to analyze
    core_modules = [
        "tools/core/error_handling.py",
        "tools/core/validation.py",
        "tools/core/file_utils.py"
    ]

    results = {}
    total_unused = 0

    print("🔍 Analyzing core modules for unused methods...")
    print("=" * 60)

    for module_path in core_modules:
        full_path = project_root / module_path
        if full_path.exists():
            analysis = find_unused_methods_in_module(full_path, project_root)
            results[module_path] = analysis

            print(f"\n📄 {module_path}")
            print(f"   Total methods: {analysis['total_methods']}")
            print(f"   Definitely unused: {len(analysis['definitely_unused'])}")

            if analysis['definitely_unused']:
                print("   Unused methods:")
                for method in analysis['definitely_unused']:
                    print(f"     - {method}")
                    total_unused += 1
            else:
                print("   ✅ All methods are used")
        else:
            print(f"❌ Module not found: {module_path}")

    print("\n" + "=" * 60)
    print(f"📊 Analysis Summary:")
    print(f"   Total unused methods found: {total_unused}")

    if total_unused == 0:
        print("   ✅ All methods in core modules are actively used!")
        print("   ℹ️  The dependency graph analysis was correct - no cleanup needed.")
    else:
        print("   🧹 Methods identified for cleanup")

    # Save detailed results
    output_file = project_root / "unused_methods_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Detailed results saved to: {output_file}")

    return results


if __name__ == "__main__":
    main()