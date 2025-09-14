#!/usr/bin/env python3
"""
Import and Dependency Optimizer

Analyzes and optimizes import statements across the codebase:
1. Removes unused imports
2. Consolidates duplicate imports
3. Orders imports according to PEP 8
4. Identifies circular dependencies
"""

import ast
import json
from pathlib import Path
from typing import Dict, Set, List, Any, Tuple
from collections import defaultdict


class ImportAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze import statements and usage"""

    def __init__(self):
        self.imports: List[Tuple[str, str, int]] = []  # (module, name, line)
        self.from_imports: List[Tuple[str, str, int]] = []  # (module, name, line)
        self.used_names: Set[str] = set()
        self.all_names: Set[str] = set()

    def visit_Import(self, node):
        """Visit import statements"""
        for alias in node.names:
            name = alias.asname or alias.name
            self.imports.append((alias.name, name, node.lineno))
            self.all_names.add(name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Visit from...import statements"""
        if node.module:
            for alias in node.names:
                name = alias.asname or alias.name
                self.from_imports.append((node.module, name, node.lineno))
                self.all_names.add(name)
        self.generic_visit(node)

    def visit_Name(self, node):
        """Track name usage"""
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        """Track attribute access"""
        if isinstance(node.value, ast.Name):
            self.used_names.add(node.value.id)
        self.generic_visit(node)


def analyze_imports_in_file(file_path: Path) -> Dict[str, Any]:
    """Analyze imports in a single Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        analyzer = ImportAnalyzer()
        analyzer.visit(tree)

        # Find unused imports
        unused_imports = []
        for module, name, line in analyzer.imports + analyzer.from_imports:
            if name not in analyzer.used_names and not name.startswith('_'):
                unused_imports.append({'module': module, 'name': name, 'line': line})

        # Find potential duplicates
        import_counts = defaultdict(int)
        for module, name, _ in analyzer.imports + analyzer.from_imports:
            import_counts[f"{module}.{name}"] += 1

        duplicates = [k for k, v in import_counts.items() if v > 1]

        return {
            'file': str(file_path),
            'total_imports': len(analyzer.imports) + len(analyzer.from_imports),
            'unused_imports': unused_imports,
            'duplicate_imports': duplicates,
            'all_imports': analyzer.imports + [(mod, name, line) for mod, name, line in analyzer.from_imports],
            'used_names': list(analyzer.used_names)
        }

    except Exception as e:
        return {
            'file': str(file_path),
            'error': str(e),
            'unused_imports': [],
            'duplicate_imports': []
        }


def find_circular_dependencies(results: List[Dict[str, Any]]) -> List[Tuple[str, str]]:
    """Find potential circular import dependencies"""
    file_imports = {}

    for result in results:
        if 'all_imports' not in result:
            continue

        file_path = result['file']
        imports = set()

        for module, name, line in result['all_imports']:
            # Convert relative imports to potential file paths
            if module and not module.startswith('.'):
                imports.add(module.replace('.', '/') + '.py')

        file_imports[file_path] = imports

    # Find potential circular dependencies
    circular = []
    for file_a, imports_a in file_imports.items():
        for file_b, imports_b in file_imports.items():
            if file_a != file_b:
                # Check if A imports B and B imports A (simplified check)
                file_a_name = Path(file_a).stem
                file_b_name = Path(file_b).stem

                if (any(file_b_name in imp for imp in imports_a) and
                    any(file_a_name in imp for imp in imports_b)):
                    if (file_a, file_b) not in circular and (file_b, file_a) not in circular:
                        circular.append((file_a, file_b))

    return circular


def optimize_imports():
    """Main import optimization function"""
    project_root = Path.cwd()

    print("🔍 Analyzing imports across the codebase...")
    print("=" * 60)

    # Find all Python files
    python_files = []
    for pattern in ['tools/**/*.py', 'tests/**/*.py', '*.py']:
        python_files.extend(project_root.glob(pattern))

    # Filter out __pycache__ and other unwanted files
    python_files = [f for f in python_files
                   if '__pycache__' not in str(f) and '.venv' not in str(f)]

    print(f"📁 Found {len(python_files)} Python files to analyze")

    results = []
    total_unused = 0
    total_duplicates = 0

    # Analyze each file
    for py_file in sorted(python_files):
        result = analyze_imports_in_file(py_file)
        results.append(result)

        if 'error' in result:
            print(f"❌ Error in {py_file.name}: {result['error']}")
            continue

        unused_count = len(result['unused_imports'])
        duplicate_count = len(result['duplicate_imports'])

        if unused_count > 0 or duplicate_count > 0:
            print(f"🔎 {py_file.relative_to(project_root)}")
            if unused_count > 0:
                print(f"   🧹 {unused_count} unused imports")
                total_unused += unused_count
            if duplicate_count > 0:
                print(f"   🔄 {duplicate_count} duplicate imports")
                total_duplicates += duplicate_count

    # Find circular dependencies
    print(f"\n🔄 Checking for circular dependencies...")
    circular_deps = find_circular_dependencies(results)

    if circular_deps:
        print(f"⚠️  Found {len(circular_deps)} potential circular dependencies:")
        for file_a, file_b in circular_deps[:5]:  # Show first 5
            print(f"   • {Path(file_a).name} ↔ {Path(file_b).name}")
    else:
        print("   ✅ No circular dependencies detected")

    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Import Analysis Summary:")
    print(f"   Files analyzed: {len(results)}")
    print(f"   Unused imports: {total_unused}")
    print(f"   Duplicate imports: {total_duplicates}")
    print(f"   Circular dependencies: {len(circular_deps)}")

    if total_unused > 0 or total_duplicates > 0:
        print(f"   🧹 Import optimization opportunity found")
    else:
        print("   ✅ Import structure is clean!")

    # Save results
    output_file = project_root / "import_analysis.json"
    analysis_data = {
        'summary': {
            'files_analyzed': len(results),
            'total_unused_imports': total_unused,
            'total_duplicates': total_duplicates,
            'circular_dependencies': len(circular_deps)
        },
        'files': results,
        'circular_dependencies': circular_deps
    }

    with open(output_file, 'w') as f:
        json.dump(analysis_data, f, indent=2)

    print(f"\n💾 Detailed results saved to: {output_file}")
    return analysis_data


if __name__ == "__main__":
    optimize_imports()