#!/usr/bin/env python3
"""
Test dependency mapping for StyleStack test consolidation.
Maps imports and dependencies between test files to identify consolidation risks.
"""

import ast
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict, deque
# import networkx as nx  # Optional dependency
# import matplotlib.pyplot as plt  # Optional dependency


class TestDependencyMapper:
    """Maps dependencies between test files and modules"""
    
    def __init__(self, tests_directory: str = "tests"):
        self.tests_dir = Path(tests_directory)
        self.dependency_graph = {}  # Simple dict instead of nx.DiGraph()
        self.module_dependencies = defaultdict(set)
        self.test_dependencies = defaultdict(set)
        self.fixture_dependencies = defaultdict(set)
        self.shared_utilities = defaultdict(set)
    
    def analyze_all_dependencies(self) -> Dict[str, any]:
        """Analyze all dependency relationships"""
        print("🔍 Analyzing test dependencies...")
        
        test_files = self._discover_test_files()
        
        # Analyze each test file
        for test_file in test_files:
            self._analyze_test_file_dependencies(test_file)
        
        # Build dependency graph
        self._build_dependency_graph()
        
        # Identify dependency clusters
        clusters = self._identify_dependency_clusters()
        
        # Find shared dependencies
        shared_deps = self._find_shared_dependencies()
        
        # Detect circular dependencies
        circular_deps = self._detect_circular_dependencies()
        
        return {
            'total_test_files': len(test_files),
            'module_dependencies': dict(self.module_dependencies),
            'test_file_dependencies': dict(self.test_dependencies),
            'fixture_dependencies': dict(self.fixture_dependencies),
            'shared_utilities': dict(self.shared_utilities),
            'dependency_clusters': clusters,
            'shared_dependencies': shared_deps,
            'circular_dependencies': circular_deps,
            'consolidation_risks': self._assess_consolidation_risks()
        }
    
    def _discover_test_files(self) -> List[Path]:
        """Discover all test files"""
        test_files = []
        for pattern in ["test_*.py", "*_test.py"]:
            test_files.extend(self.tests_dir.rglob(pattern))
        
        return [f for f in test_files 
                if f.is_file() 
                and not f.name.startswith('__')
                and '__pycache__' not in str(f)]
    
    def _analyze_test_file_dependencies(self, test_file: Path):
        """Analyze dependencies for a single test file"""
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            test_name = str(test_file.relative_to(self.tests_dir))
            
            # Extract imports
            imports = self._extract_imports(tree)
            self.module_dependencies[test_name] = imports['modules']
            
            # Extract test-specific dependencies
            self.test_dependencies[test_name] = imports['test_imports']
            
            # Extract fixture usage
            fixtures = self._extract_fixture_usage(tree)
            self.fixture_dependencies[test_name] = fixtures
            
            # Extract shared utilities
            utilities = self._extract_utility_usage(tree, imports['modules'])
            self.shared_utilities[test_name] = utilities
            
        except Exception as e:
            print(f"Error analyzing {test_file}: {e}")
    
    def _extract_imports(self, tree: ast.AST) -> Dict[str, Set[str]]:
        """Extract import statements from AST"""
        modules = set()
        test_imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    modules.add(alias.name)
                    if 'test' in alias.name or alias.name.startswith('tests.'):
                        test_imports.add(alias.name)
                        
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    modules.add(node.module)
                    if 'test' in node.module or node.module.startswith('tests.'):
                        test_imports.add(node.module)
                    
                    # Add specific imports
                    for alias in node.names:
                        full_import = f"{node.module}.{alias.name}"
                        modules.add(full_import)
        
        return {
            'modules': modules,
            'test_imports': test_imports
        }
    
    def _extract_fixture_usage(self, tree: ast.AST) -> Set[str]:
        """Extract pytest fixture usage"""
        fixtures = set()
        
        for node in ast.walk(tree):
            # Function parameters (fixture injection)
            if isinstance(node, ast.FunctionDef):
                for arg in node.args.args:
                    # Common fixture patterns
                    if arg.arg in ['tmp_path', 'tmpdir', 'monkeypatch', 'capfd', 'caplog']:
                        fixtures.add(arg.arg)
                    elif arg.arg.endswith('_fixture') or 'mock' in arg.arg:
                        fixtures.add(arg.arg)
            
            # Fixture decorators
            elif isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Attribute):
                            if decorator.func.attr == 'fixture':
                                fixtures.add(f"@pytest.fixture:{node.name}")
        
        return fixtures
    
    def _extract_utility_usage(self, tree: ast.AST, imports: Set[str]) -> Set[str]:
        """Extract shared utility usage"""
        utilities = set()
        
        # Look for imports from helpers, mocks, fixtures directories
        for imp in imports:
            if any(util_dir in imp for util_dir in ['helpers', 'mocks', 'fixtures', 'utils']):
                utilities.add(imp)
        
        # Look for function calls to utility modules
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if any(util_name in str(node.func.value.__dict__ if hasattr(node.func.value, '__dict__') else '') 
                          for util_name in ['mock', 'fixture', 'helper']):
                        utilities.add(f"call:{node.func.attr}")
        
        return utilities
    
    def _build_dependency_graph(self):
        """Build simple dependency graph"""
        # Initialize graph structure
        for test_file in self.module_dependencies.keys():
            if test_file not in self.dependency_graph:
                self.dependency_graph[test_file] = {'deps': set(), 'fixtures': set()}
        
        # Add dependencies
        for test_file, deps in self.test_dependencies.items():
            for dep in deps:
                dep_file = self._find_test_file_for_module(dep)
                if dep_file:
                    self.dependency_graph[test_file]['deps'].add(dep_file)
        
        # Add fixture relationships
        fixture_groups = defaultdict(list)
        for test_file, fixtures in self.fixture_dependencies.items():
            for fixture in fixtures:
                fixture_groups[fixture].append(test_file)
        
        # Connect test files that share fixtures
        for fixture, test_files in fixture_groups.items():
            if len(test_files) > 1:
                for test_file in test_files:
                    if test_file in self.dependency_graph:
                        self.dependency_graph[test_file]['fixtures'].update(test_files)
    
    def _find_test_file_for_module(self, module_name: str) -> str:
        """Find test file that corresponds to a module import"""
        # Look for direct test file matches
        for test_file in self.module_dependencies.keys():
            test_base = Path(test_file).stem.replace('test_', '')
            if test_base in module_name or module_name.endswith(test_base):
                return test_file
        return None
    
    def _identify_dependency_clusters(self) -> Dict[str, List[str]]:
        """Identify clusters of strongly connected test files"""
        if not self.dependency_graph:
            return {}
        
        # Simple clustering based on shared fixtures and dependencies
        clusters = {}
        visited = set()
        cluster_id = 0
        
        for test_file in self.dependency_graph.keys():
            if test_file in visited:
                continue
            
            # Find connected files via fixtures or dependencies
            cluster = self._find_connected_files(test_file, visited)
            if len(cluster) > 1:
                clusters[f"cluster_{cluster_id}"] = list(cluster)
                cluster_id += 1
                visited.update(cluster)
        
        return clusters
    
    def _find_connected_files(self, start_file: str, visited: set) -> set:
        """Find all files connected to start_file"""
        connected = {start_file}
        queue = [start_file]
        local_visited = {start_file}
        
        while queue:
            current = queue.pop(0)
            if current not in self.dependency_graph:
                continue
                
            # Add files sharing fixtures
            for fixture_file in self.dependency_graph[current]['fixtures']:
                if fixture_file not in local_visited and fixture_file not in visited:
                    connected.add(fixture_file)
                    queue.append(fixture_file)
                    local_visited.add(fixture_file)
            
            # Add direct dependencies
            for dep_file in self.dependency_graph[current]['deps']:
                if dep_file not in local_visited and dep_file not in visited:
                    connected.add(dep_file)
                    queue.append(dep_file)
                    local_visited.add(dep_file)
        
        return connected
    
    def _find_shared_dependencies(self) -> Dict[str, List[str]]:
        """Find dependencies shared across multiple test files"""
        dependency_usage = defaultdict(list)
        
        # Count usage of each module dependency
        for test_file, deps in self.module_dependencies.items():
            for dep in deps:
                if not dep.startswith('test'):  # Exclude test-specific imports
                    dependency_usage[dep].append(test_file)
        
        # Filter to only shared dependencies (used by 2+ files)
        shared = {dep: files for dep, files in dependency_usage.items() if len(files) > 1}
        
        return shared
    
    def _detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies in test files"""
        cycles = []
        
        for test_file in self.dependency_graph.keys():
            visited = set()
            rec_stack = set()
            cycle = self._detect_cycle_dfs(test_file, visited, rec_stack, [])
            if cycle:
                cycles.append(cycle)
        
        return cycles
    
    def _detect_cycle_dfs(self, node: str, visited: set, rec_stack: set, path: list) -> list:
        """DFS-based cycle detection"""
        if node in rec_stack:
            # Found cycle, return the cycle path
            cycle_start = path.index(node)
            return path[cycle_start:] + [node]
        
        if node in visited:
            return None
        
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        # Check dependencies
        if node in self.dependency_graph:
            for dep in self.dependency_graph[node]['deps']:
                cycle = self._detect_cycle_dfs(dep, visited, rec_stack, path)
                if cycle:
                    return cycle
        
        rec_stack.remove(node)
        path.pop()
        return None
    
    def _assess_consolidation_risks(self) -> Dict[str, Dict[str, any]]:
        """Assess risks for consolidating specific test file groups"""
        risks = {}
        
        # Analyze each potential consolidation group
        from test_consolidation_analyzer import TestConsolidationAnalyzer
        analyzer = TestConsolidationAnalyzer()
        patterns = analyzer.detect_duplication_patterns()
        
        for pattern_name, pattern in patterns.items():
            files = [str(f.relative_to(self.tests_dir)) for f in pattern.files]
            
            # Calculate consolidation risk factors
            shared_deps = self._count_shared_dependencies(files)
            fixture_conflicts = self._check_fixture_conflicts(files) 
            circular_deps = self._check_circular_in_group(files)
            
            risk_level = "LOW"
            if circular_deps or fixture_conflicts > 2:
                risk_level = "HIGH"
            elif shared_deps < 3 or fixture_conflicts > 0:
                risk_level = "MEDIUM"
            
            risks[pattern_name] = {
                'risk_level': risk_level,
                'shared_dependencies': shared_deps,
                'fixture_conflicts': fixture_conflicts,
                'has_circular_deps': bool(circular_deps),
                'consolidation_complexity': len(files) * fixture_conflicts
            }
        
        return risks
    
    def _count_shared_dependencies(self, test_files: List[str]) -> int:
        """Count shared dependencies within a group of test files"""
        if len(test_files) < 2:
            return 0
        
        deps_sets = [self.module_dependencies.get(f, set()) for f in test_files]
        shared = set.intersection(*deps_sets) if deps_sets else set()
        
        return len(shared)
    
    def _check_fixture_conflicts(self, test_files: List[str]) -> int:
        """Check for fixture naming conflicts in a group"""
        all_fixtures = []
        for f in test_files:
            all_fixtures.extend(self.fixture_dependencies.get(f, set()))
        
        # Count duplicate fixture names
        fixture_counts = defaultdict(int)
        for fixture in all_fixtures:
            fixture_counts[fixture] += 1
        
        conflicts = sum(1 for count in fixture_counts.values() if count > 1)
        return conflicts
    
    def _check_circular_in_group(self, test_files: List[str]) -> bool:
        """Check if test files in group have circular dependencies"""
        # Check for cycles within this specific group
        for test_file in test_files:
            if test_file not in self.dependency_graph:
                continue
            
            # Check if any dependency is also in the group
            for dep in self.dependency_graph[test_file]['deps']:
                if dep in test_files and dep != test_file:
                    return True
        
        return False
    
    def save_dependency_analysis(self, output_path: str = "test_dependency_analysis.json"):
        """Save dependency analysis to JSON file"""
        analysis = self.analyze_all_dependencies()
        
        # Convert sets to lists for JSON serialization
        def convert_sets(obj):
            if isinstance(obj, set):
                return list(obj)
            elif isinstance(obj, dict):
                return {k: convert_sets(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_sets(item) for item in obj]
            else:
                return obj
        
        analysis_json = convert_sets(analysis)
        
        with open(output_path, 'w') as f:
            json.dump(analysis_json, f, indent=2)
        
        print(f"📄 Dependency analysis saved to {output_path}")
        return analysis_json


def main():
    """Main dependency analysis"""
    mapper = TestDependencyMapper()
    analysis = mapper.save_dependency_analysis()
    
    print("\n" + "="*60)
    print("🔗 TEST DEPENDENCY ANALYSIS COMPLETE")
    print("="*60)
    
    print(f"📁 Total test files analyzed: {analysis['total_test_files']}")
    print(f"🔗 Dependency clusters found: {len(analysis['dependency_clusters'])}")
    print(f"📚 Shared dependencies: {len(analysis['shared_dependencies'])}")
    print(f"🔄 Circular dependencies: {len(analysis['circular_dependencies'])}")
    
    print("\n🎯 CONSOLIDATION RISK ASSESSMENT:")
    for pattern, risk in analysis['consolidation_risks'].items():
        print(f"  {pattern}: {risk['risk_level']} risk ({risk['shared_dependencies']} shared deps)")


if __name__ == "__main__":
    main()