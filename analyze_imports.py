#!/usr/bin/env python3
"""
Import Analysis Tool for StyleStack Codebase
Analyzes all imports and dependencies across the codebase.
"""

import ast
import os
import sys
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Optional
import json

class ImportAnalyzer:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.imports_data = {}  # file -> {internal: [], external: []}
        self.dependency_graph = defaultdict(set)  # module -> set of modules it depends on
        self.reverse_deps = defaultdict(set)  # module -> set of modules that depend on it
        self.external_deps = Counter()
        self.internal_modules = set()
        
    def is_internal_import(self, module_name: str) -> bool:
        """Check if an import is internal to the StyleStack project."""
        # Check if it starts with tools. or is in the tools directory structure
        if module_name.startswith('tools.'):
            return True
        if module_name.startswith('.'):  # Relative imports
            return True
        # Check for direct tool module names
        tool_modules = [
            'variable_resolver', 'ooxml_processor', 'token_integration_layer',
            'theme_resolver', 'variable_substitution', 'template_analyzer',
            'json_patch_parser', 'multi_format_ooxml_handler', 'transaction_pipeline',
            'formula_parser', 'formula_variable_resolver', 'design_token_extractor',
            'emu_types', 'extension_schema_validator', 'template_patcher',
            'token_parser', 'token_resolver', 'ooxml_analyzer',
            'ooxml_extension_manager', 'advanced_cache_system',
            'performance_profiler', 'memory_optimizer', 'grid_generator'
        ]
        return module_name in tool_modules
    
    def extract_imports_from_file(self, file_path: Path) -> Dict:
        """Extract all imports from a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            imports = {'internal': [], 'external': []}
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name
                        if self.is_internal_import(module_name):
                            imports['internal'].append(module_name)
                        else:
                            imports['external'].append(module_name)
                            self.external_deps[module_name] += 1
                            
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module
                        imported_items = [alias.name for alias in node.names]
                        
                        if self.is_internal_import(module_name):
                            imports['internal'].append(f"{module_name} ({', '.join(imported_items)})")
                        else:
                            imports['external'].append(f"{module_name} ({', '.join(imported_items)})")
                            self.external_deps[module_name] += 1
                    else:
                        # Relative import like "from . import something"
                        imported_items = [alias.name for alias in node.names]
                        imports['internal'].append(f"relative ({', '.join(imported_items)})")
            
            return imports
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return {'internal': [], 'external': []}
    
    def build_dependency_graph(self):
        """Build the dependency graph from import data."""
        for file_path, imports in self.imports_data.items():
            module_name = self.get_module_name(file_path)
            self.internal_modules.add(module_name)
            
            for imp in imports['internal']:
                # Extract the base module name from import string
                if '(' in imp:
                    dep_module = imp.split('(')[0].strip()
                else:
                    dep_module = imp
                
                # Clean up module names
                if dep_module.startswith('tools.'):
                    dep_module = dep_module[6:]  # Remove 'tools.' prefix
                elif dep_module == 'relative':
                    continue  # Skip relative imports for graph
                
                self.dependency_graph[module_name].add(dep_module)
                self.reverse_deps[dep_module].add(module_name)
    
    def get_module_name(self, file_path: str) -> str:
        """Convert file path to module name."""
        rel_path = Path(file_path).relative_to(self.root_path / 'tools')
        module_parts = list(rel_path.parts[:-1]) + [rel_path.stem]
        if module_parts[-1] == '__init__':
            module_parts = module_parts[:-1]
        return '.'.join(module_parts) if module_parts else rel_path.stem
    
    def detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies using DFS."""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
                
            if node in visited:
                return
                
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.dependency_graph.get(node, []):
                if neighbor in self.internal_modules:
                    dfs(neighbor, path[:])
            
            rec_stack.remove(node)
            path.pop()
        
        for module in self.internal_modules:
            if module not in visited:
                dfs(module, [])
        
        return cycles
    
    def analyze_all_files(self):
        """Analyze imports in all Python files."""
        python_files = list(self.root_path.glob('tools/**/*.py'))
        
        for file_path in python_files:
            if file_path.name == '__pycache__':
                continue
                
            imports = self.extract_imports_from_file(file_path)
            self.imports_data[str(file_path)] = imports
        
        self.build_dependency_graph()
    
    def generate_report(self) -> Dict:
        """Generate comprehensive import analysis report."""
        circular_deps = self.detect_circular_dependencies()
        
        # Find critical path modules (most depended upon)
        critical_modules = sorted(
            self.reverse_deps.items(), 
            key=lambda x: len(x[1]), 
            reverse=True
        )[:10]
        
        # Find modules with most dependencies
        heavy_modules = sorted(
            self.dependency_graph.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:10]
        
        report = {
            'summary': {
                'total_files_analyzed': len(self.imports_data),
                'total_internal_modules': len(self.internal_modules),
                'total_external_dependencies': len(self.external_deps),
                'circular_dependencies_found': len(circular_deps)
            },
            'external_dependencies': dict(self.external_deps.most_common()),
            'internal_dependency_graph': {k: list(v) for k, v in self.dependency_graph.items()},
            'reverse_dependencies': {k: list(v) for k, v in self.reverse_deps.items()},
            'circular_dependencies': circular_deps,
            'critical_modules': [(mod, len(deps)) for mod, deps in critical_modules],
            'heavy_modules': [(mod, len(deps)) for mod, deps in heavy_modules],
            'detailed_imports': {}
        }
        
        # Add detailed import information for key modules
        key_modules = [
            'variable_resolver.py', 'ooxml_processor.py', 'token_integration_layer.py',
            'theme_resolver.py', 'variable_substitution.py', 'template_analyzer.py',
            'json_patch_parser.py', 'multi_format_ooxml_handler.py', 'transaction_pipeline.py'
        ]
        
        for file_path, imports in self.imports_data.items():
            if any(key_mod in file_path for key_mod in key_modules):
                report['detailed_imports'][file_path] = imports
        
        return report

def main():
    analyzer = ImportAnalyzer('/Users/ynse/projects/StyleStack')
    analyzer.analyze_all_files()
    report = analyzer.generate_report()
    
    # Save full report to JSON
    with open('/Users/ynse/projects/StyleStack/import_analysis.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("StyleStack Import Analysis Summary")
    print("=" * 50)
    print(f"Total files analyzed: {report['summary']['total_files_analyzed']}")
    print(f"Internal modules: {report['summary']['total_internal_modules']}")
    print(f"External dependencies: {report['summary']['total_external_dependencies']}")
    print(f"Circular dependencies: {report['summary']['circular_dependencies_found']}")
    
    print("\nTop External Dependencies:")
    for dep, count in list(report['external_dependencies'].items())[:10]:
        print(f"  {dep}: {count} usages")
    
    print("\nCritical Path Modules (most depended upon):")
    for mod, dep_count in report['critical_modules'][:5]:
        print(f"  {mod}: {dep_count} dependents")
    
    print("\nHeaviest Modules (most dependencies):")
    for mod, dep_count in report['heavy_modules'][:5]:
        print(f"  {mod}: {dep_count} dependencies")
    
    if report['circular_dependencies']:
        print("\nCircular Dependencies Found:")
        for i, cycle in enumerate(report['circular_dependencies']):
            print(f"  Cycle {i+1}: {' -> '.join(cycle)}")
    else:
        print("\nNo circular dependencies found!")
    
    print(f"\nDetailed analysis saved to: import_analysis.json")

if __name__ == "__main__":
    main()