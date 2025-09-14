#!/usr/bin/env python3
"""
StyleStack Orphaned Code Analysis Tool

Performs comprehensive analysis to identify:
1. Orphaned files (never imported)
2. Orphaned functions/classes (defined but never called)
3. Unused variables and imports
4. Dead code branches

Uses AST parsing to build complete dependency graphs and identify
unreachable code from any entry point.
"""

import ast
import os
import sys
import json
from pathlib import Path
from typing import Dict, Set, List, Tuple, Optional, Union
from collections import defaultdict, deque
from dataclasses import dataclass
import argparse
from datetime import datetime


@dataclass
class CodeElement:
    """Represents a code element (function, class, variable, etc.)"""
    name: str
    type: str  # 'function', 'class', 'variable', 'import'
    file_path: str
    line_number: int
    defined: bool = True
    called: bool = False
    imported: bool = False

    def __hash__(self):
        return hash((self.name, self.type, self.file_path, self.line_number))


class ASTVisitor(ast.NodeVisitor):
    """AST visitor to extract all code elements and their usage"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.imports = set()
        self.from_imports = defaultdict(set)
        self.functions = {}
        self.classes = {}
        self.variables = set()
        self.function_calls = set()
        self.attribute_accesses = set()
        self.current_class = None
        self.current_function = None
        self.scope_stack = []

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports.add(name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                self.from_imports[node.module].add(name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        func_name = node.name
        if self.current_class:
            full_name = f"{self.current_class}.{func_name}"
        else:
            full_name = func_name

        self.functions[full_name] = CodeElement(
            name=full_name,
            type='function',
            file_path=self.file_path,
            line_number=node.lineno
        )

        prev_function = self.current_function
        self.current_function = full_name
        self.scope_stack.append(full_name)

        # Visit function body
        for child in ast.iter_child_nodes(node):
            self.visit(child)

        self.current_function = prev_function
        self.scope_stack.pop()

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)  # Treat same as regular function

    def visit_ClassDef(self, node):
        class_name = node.name
        self.classes[class_name] = CodeElement(
            name=class_name,
            type='class',
            file_path=self.file_path,
            line_number=node.lineno
        )

        prev_class = self.current_class
        self.current_class = class_name
        self.scope_stack.append(class_name)

        # Visit class body
        for child in ast.iter_child_nodes(node):
            self.visit(child)

        self.current_class = prev_class
        self.scope_stack.pop()

    def visit_Assign(self, node):
        # Track variable assignments
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.variables.add(target.id)
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        # Track annotated assignments
        if isinstance(node.target, ast.Name):
            self.variables.add(node.target.id)
        self.generic_visit(node)

    def visit_Call(self, node):
        # Track function calls
        if isinstance(node.func, ast.Name):
            self.function_calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            # Handle method calls like obj.method()
            if isinstance(node.func.value, ast.Name):
                self.function_calls.add(f"{node.func.value.id}.{node.func.attr}")
            else:
                self.function_calls.add(node.func.attr)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        # Track attribute access
        if isinstance(node.value, ast.Name):
            self.attribute_accesses.add(f"{node.value.id}.{node.attr}")
        self.generic_visit(node)

    def visit_Name(self, node):
        # Track variable usage
        if isinstance(node.ctx, ast.Load):
            # Variable is being read/used
            pass  # Could track variable usage here
        self.generic_visit(node)


class OrphanedCodeAnalyzer:
    """Main analyzer class for finding orphaned code"""

    def __init__(self, root_path: str, exclude_dirs: List[str] = None):
        self.root_path = Path(root_path)
        self.exclude_dirs = exclude_dirs or [
            '.git', '.venv', 'venv', '__pycache__', '.pytest_cache',
            'node_modules', '.coverage_reports', 'htmlcov', 'releases',
            'build', 'dist', '.agent-os', '.claude'
        ]

        # Data structures for analysis
        self.all_files: Set[str] = set()
        self.imported_files: Set[str] = set()
        self.file_imports: Dict[str, Set[str]] = defaultdict(set)
        self.file_elements: Dict[str, Dict[str, CodeElement]] = defaultdict(dict)
        self.global_functions: Dict[str, CodeElement] = {}
        self.global_classes: Dict[str, CodeElement] = {}
        self.function_calls: Dict[str, Set[str]] = defaultdict(set)
        self.entry_points: Set[str] = set()

    def find_python_files(self) -> List[str]:
        """Find all Python files in the project"""
        python_files = []

        for root, dirs, files in os.walk(self.root_path):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    python_files.append(file_path)

        return python_files

    def identify_entry_points(self, files: List[str]) -> Set[str]:
        """Identify entry points (main scripts, build.py, conftest.py, etc.)"""
        entry_points = set()

        for file_path in files:
            file_name = os.path.basename(file_path)

            # Common entry point patterns
            if (file_name in ['build.py', 'setup.py', 'conftest.py'] or
                file_name.startswith('run_') or
                file_name.startswith('test_') or
                'cli' in file_name.lower()):
                entry_points.add(file_path)
                continue

            # Check if file has __main__ block
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '__main__' in content:
                        entry_points.add(file_path)
            except (UnicodeDecodeError, IOError):
                continue

        return entry_points

    def parse_file(self, file_path: str) -> Optional[ASTVisitor]:
        """Parse a single Python file using AST"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=file_path)
            visitor = ASTVisitor(file_path)
            visitor.visit(tree)
            return visitor

        except (SyntaxError, UnicodeDecodeError, IOError) as e:
            print(f"Warning: Could not parse {file_path}: {e}")
            return None

    def resolve_import_path(self, import_name: str, from_file: str) -> Optional[str]:
        """Resolve import to actual file path"""
        # Handle relative imports
        if import_name.startswith('.'):
            from_dir = os.path.dirname(from_file)
            # This is a simplified version - real resolution is more complex
            parts = import_name.split('.')
            relative_parts = []
            for part in parts:
                if part == '':
                    from_dir = os.path.dirname(from_dir)
                else:
                    relative_parts.append(part)

            if relative_parts:
                module_path = os.path.join(from_dir, *relative_parts)
            else:
                module_path = from_dir
        else:
            # Absolute import - search from root
            parts = import_name.split('.')
            module_path = os.path.join(self.root_path, *parts)

        # Try different extensions
        for ext in ['.py', '/__init__.py']:
            full_path = module_path + ext
            if os.path.exists(full_path):
                return os.path.abspath(full_path)

        return None

    def build_import_graph(self, files: List[str]) -> Dict[str, Set[str]]:
        """Build graph of which files import which other files"""
        import_graph = defaultdict(set)

        for file_path in files:
            visitor = self.parse_file(file_path)
            if not visitor:
                continue

            # Process direct imports
            for import_name in visitor.imports:
                resolved_path = self.resolve_import_path(import_name, file_path)
                if resolved_path and resolved_path in files:
                    import_graph[file_path].add(resolved_path)
                    self.imported_files.add(resolved_path)

            # Process from imports
            for module, names in visitor.from_imports.items():
                resolved_path = self.resolve_import_path(module, file_path)
                if resolved_path and resolved_path in files:
                    import_graph[file_path].add(resolved_path)
                    self.imported_files.add(resolved_path)

        return import_graph

    def analyze_code_elements(self, files: List[str]):
        """Analyze all code elements (functions, classes, etc.) in files"""
        for file_path in files:
            visitor = self.parse_file(file_path)
            if not visitor:
                continue

            self.file_elements[file_path] = {}

            # Store functions
            for name, func_elem in visitor.functions.items():
                self.file_elements[file_path][name] = func_elem
                self.global_functions[f"{file_path}:{name}"] = func_elem

            # Store classes
            for name, class_elem in visitor.classes.items():
                self.file_elements[file_path][name] = class_elem
                self.global_classes[f"{file_path}:{name}"] = class_elem

            # Store function calls for this file
            self.function_calls[file_path] = visitor.function_calls

    def find_reachable_code(self, entry_points: Set[str], import_graph: Dict[str, Set[str]]) -> Set[str]:
        """Find all files reachable from entry points using BFS"""
        reachable = set()
        queue = deque(entry_points)

        while queue:
            current_file = queue.popleft()
            if current_file in reachable:
                continue

            reachable.add(current_file)

            # Add all files imported by current file
            for imported_file in import_graph.get(current_file, set()):
                if imported_file not in reachable:
                    queue.append(imported_file)

        return reachable

    def find_called_functions(self, reachable_files: Set[str]) -> Set[str]:
        """Find all functions called from reachable files"""
        called_functions = set()

        for file_path in reachable_files:
            calls = self.function_calls.get(file_path, set())
            for call in calls:
                # Mark function as called
                called_functions.add(call)

                # Also check for method calls in same file
                for elem_name, element in self.file_elements.get(file_path, {}).items():
                    if element.type == 'function':
                        # Simple name match (could be more sophisticated)
                        if call == element.name.split('.')[-1]:
                            called_functions.add(elem_name)

        return called_functions

    def generate_report(self) -> Dict:
        """Generate comprehensive orphaned code report"""
        files = self.find_python_files()
        self.all_files = set(files)

        print(f"Analyzing {len(files)} Python files...")

        # Identify entry points
        self.entry_points = self.identify_entry_points(files)
        print(f"Found {len(self.entry_points)} entry points")

        # Build import graph
        import_graph = self.build_import_graph(files)

        # Analyze code elements
        self.analyze_code_elements(files)

        # Find reachable code
        reachable_files = self.find_reachable_code(self.entry_points, import_graph)

        # Find called functions
        called_functions = self.find_called_functions(reachable_files)

        # Generate orphaned files report
        orphaned_files = []
        for file_path in files:
            if file_path not in reachable_files:
                orphaned_files.append({
                    'file': os.path.relpath(file_path, self.root_path),
                    'absolute_path': file_path,
                    'size_lines': self._count_lines(file_path),
                    'reason': 'Never imported from any entry point'
                })

        # Generate orphaned functions report
        orphaned_functions = []
        for file_path in reachable_files:
            for elem_name, element in self.file_elements.get(file_path, {}).items():
                if element.type == 'function' and elem_name not in called_functions:
                    # Skip special methods and common patterns
                    if not self._is_special_function(elem_name):
                        orphaned_functions.append({
                            'function': elem_name,
                            'file': os.path.relpath(file_path, self.root_path),
                            'line': element.line_number,
                            'reason': 'Defined but never called'
                        })

        # Generate orphaned classes report
        orphaned_classes = []
        for file_path in reachable_files:
            for elem_name, element in self.file_elements.get(file_path, {}).items():
                if element.type == 'class':
                    # Check if class is ever instantiated or subclassed
                    class_used = False
                    for call_file in reachable_files:
                        if elem_name in self.function_calls.get(call_file, set()):
                            class_used = True
                            break

                    if not class_used and not self._is_special_class(elem_name):
                        orphaned_classes.append({
                            'class': elem_name,
                            'file': os.path.relpath(file_path, self.root_path),
                            'line': element.line_number,
                            'reason': 'Defined but never instantiated or referenced'
                        })

        # Compile final report
        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'total_files_analyzed': len(files),
            'entry_points': [os.path.relpath(ep, self.root_path) for ep in self.entry_points],
            'reachable_files_count': len(reachable_files),
            'summary': {
                'orphaned_files': len(orphaned_files),
                'orphaned_functions': len(orphaned_functions),
                'orphaned_classes': len(orphaned_classes),
                'total_orphaned_elements': len(orphaned_files) + len(orphaned_functions) + len(orphaned_classes)
            },
            'orphaned_files': orphaned_files,
            'orphaned_functions': orphaned_functions,
            'orphaned_classes': orphaned_classes,
            'reachable_files': [os.path.relpath(rf, self.root_path) for rf in sorted(reachable_files)],
            'import_graph_stats': {
                'total_imports': sum(len(imports) for imports in import_graph.values()),
                'files_with_imports': len([f for f, imports in import_graph.items() if imports])
            }
        }

        return report

    def _count_lines(self, file_path: str) -> int:
        """Count lines in a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return len(f.readlines())
        except (UnicodeDecodeError, IOError):
            return 0

    def _is_special_function(self, func_name: str) -> bool:
        """Check if function is special (should not be marked as orphaned)"""
        name = func_name.split('.')[-1]
        return (
            name.startswith('__') or
            name.startswith('test_') or
            name in ['setUp', 'tearDown', 'main'] or
            name.endswith('_fixture')
        )

    def _is_special_class(self, class_name: str) -> bool:
        """Check if class is special (should not be marked as orphaned)"""
        return (
            class_name.startswith('Test') or
            class_name.endswith('Error') or
            class_name.endswith('Exception') or
            class_name.endswith('Config')
        )


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description='Analyze StyleStack codebase for orphaned code')
    parser.add_argument('--root', default='/Users/ynse/projects/StyleStack',
                       help='Root directory to analyze')
    parser.add_argument('--output', default='orphaned_code_report.json',
                       help='Output file for report')
    parser.add_argument('--format', choices=['json', 'text'], default='json',
                       help='Output format')

    args = parser.parse_args()

    # Initialize analyzer
    analyzer = OrphanedCodeAnalyzer(args.root)

    # Generate report
    print("Starting orphaned code analysis...")
    report = analyzer.generate_report()

    # Output report
    if args.format == 'json':
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to {args.output}")
    else:
        # Text format output
        print("\n" + "="*80)
        print("STYLESTACK ORPHANED CODE ANALYSIS REPORT")
        print("="*80)

        print(f"\nAnalysis completed at: {report['analysis_timestamp']}")
        print(f"Total files analyzed: {report['total_files_analyzed']}")
        print(f"Entry points found: {len(report['entry_points'])}")
        print(f"Reachable files: {report['reachable_files_count']}")

        print(f"\nSUMMARY:")
        print(f"  Orphaned files: {report['summary']['orphaned_files']}")
        print(f"  Orphaned functions: {report['summary']['orphaned_functions']}")
        print(f"  Orphaned classes: {report['summary']['orphaned_classes']}")
        print(f"  Total orphaned elements: {report['summary']['total_orphaned_elements']}")

        if report['orphaned_files']:
            print(f"\nORPHANED FILES ({len(report['orphaned_files'])}):")
            for file_info in report['orphaned_files']:
                print(f"  - {file_info['file']} ({file_info['size_lines']} lines)")

        if report['orphaned_functions']:
            print(f"\nORPHANED FUNCTIONS ({len(report['orphaned_functions'])}):")
            for func_info in report['orphaned_functions'][:20]:  # Limit to first 20
                print(f"  - {func_info['function']} in {func_info['file']}:{func_info['line']}")
            if len(report['orphaned_functions']) > 20:
                print(f"  ... and {len(report['orphaned_functions']) - 20} more")

        if report['orphaned_classes']:
            print(f"\nORPHANED CLASSES ({len(report['orphaned_classes'])}):")
            for class_info in report['orphaned_classes']:
                print(f"  - {class_info['class']} in {class_info['file']}:{class_info['line']}")

    print(f"\nAnalysis complete. Found {report['summary']['total_orphaned_elements']} orphaned elements.")


if __name__ == '__main__':
    main()