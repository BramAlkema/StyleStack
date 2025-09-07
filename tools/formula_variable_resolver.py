"""
Formula-based Variable Resolution System for StyleStack Design Tokens

This module provides dependency graph analysis, topological sorting, 
and hierarchical variable resolution specifically for design token formulas
that integrate with the Formula Parser Engine and EMU Type System.
"""

from typing import Dict, Set, List, Any, Optional, Union, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
import copy

from .formula_parser import FormulaParser
from .emu_types import EMUValue


class CircularDependencyError(Exception):
    """Raised when circular dependencies are detected in variable resolution."""
    pass


class VariableNotFoundError(Exception):
    """Raised when a required variable is not found in any layer."""
    pass


@dataclass
class VariableDefinition:
    """Represents a variable definition with metadata."""
    name: str
    value: Union[str, int, float, EMUValue]
    layer: str  # core, org, channel, user
    source_file: Optional[str] = None
    dependencies: Set[str] = field(default_factory=set)
    resolved_value: Optional[Union[int, float, EMUValue]] = None
    is_resolved: bool = False


class DependencyGraph:
    """Builds and manages dependency graphs for variable resolution."""
    
    def __init__(self):
        self.nodes: Set[str] = set()
        self.edges: Dict[str, Set[str]] = defaultdict(set)  # variable -> dependencies
        self.reverse_edges: Dict[str, Set[str]] = defaultdict(set)  # variable -> dependents
    
    def add_variable(self, name: str, dependencies: Set[str]):
        """Add a variable and its dependencies to the graph."""
        self.nodes.add(name)
        self.edges[name] = dependencies.copy()
        
        for dep in dependencies:
            self.nodes.add(dep)
            self.reverse_edges[dep].add(name)
    
    def get_dependencies(self, name: str) -> Set[str]:
        """Get direct dependencies of a variable."""
        return self.edges.get(name, set())
    
    def get_dependents(self, name: str) -> Set[str]:
        """Get variables that depend on this variable."""
        return self.reverse_edges.get(name, set())
    
    def detect_cycles(self) -> List[List[str]]:
        """Detect circular dependencies using DFS."""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs_visit(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for dependency in self.edges[node]:
                if dependency in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(dependency)
                    cycle = path[cycle_start:] + [dependency]
                    cycles.append(cycle)
                elif dependency not in visited:
                    dfs_visit(dependency, path.copy())
            
            rec_stack.remove(node)
        
        for node in self.nodes:
            if node not in visited:
                dfs_visit(node, [])
        
        return cycles
    
    def topological_sort(self) -> List[str]:
        """Return variables in topological order (dependencies first)."""
        # Check for cycles first
        cycles = self.detect_cycles()
        if cycles:
            cycle_strs = [" → ".join(cycle) for cycle in cycles]
            raise CircularDependencyError(f"Circular dependencies detected: {'; '.join(cycle_strs)}")
        
        # Kahn's algorithm - but we need to reverse the logic since our edges
        # go from node -> dependencies, but we need dependencies first
        
        # Calculate in-degree: how many variables depend on this variable
        in_degree = {node: len(self.reverse_edges[node]) for node in self.nodes}
        
        # Start with nodes that no other nodes depend on (leaves)
        queue = deque([node for node in self.nodes if in_degree[node] == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            # For each dependency of this node, reduce its in-degree
            for dep in self.edges[node]:
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)
        
        if len(result) != len(self.nodes):
            # This shouldn't happen if cycle detection worked correctly
            raise CircularDependencyError("Failed to resolve all dependencies")
        
        # Reverse the result since we want dependencies first
        return result[::-1]


class FormulaVariableResolver:
    """
    Formula-based variable resolver with dependency tracking and caching.
    
    Supports layered variable definitions:
    - core: Community baseline defaults
    - org: Corporate overrides  
    - channel: Template flavor overrides
    - user: Personal customization
    """
    
    def __init__(self):
        self.parser = FormulaParser()
        self.variables: Dict[str, VariableDefinition] = {}
        self.layer_priority = ['core', 'org', 'channel', 'user']  # lowest to highest priority
        self.resolved_cache: Dict[str, Union[int, float, EMUValue]] = {}
        self.resolution_in_progress: Set[str] = set()
    
    def add_layer(self, layer: str, variables: Dict[str, Union[str, int, float]], source_file: Optional[str] = None):
        """Add variables from a specific layer."""
        if layer not in self.layer_priority:
            raise ValueError(f"Invalid layer '{layer}'. Must be one of: {self.layer_priority}")
        
        for name, value in variables.items():
            # Extract dependencies if value is a formula
            dependencies = set()
            if isinstance(value, str):
                # Check if this string looks like a formula (not a literal value)
                is_likely_formula = (
                    # Contains mathematical operators or parentheses
                    any(char in value for char in '+-*/()')
                    # OR looks like a variable reference (uppercase, underscores, numbers)
                    or (value.replace('_', '').replace('.', '').isalnum() 
                        and value.isupper() 
                        and not value.startswith('#')
                        and len(value) > 1)
                )
                
                if is_likely_formula:
                    try:
                        dependencies = self.parser.extract_dependencies(value)
                    except Exception:
                        # If parsing fails, treat as literal string
                        pass
            
            # Override existing variable or create new one
            self.variables[name] = VariableDefinition(
                name=name,
                value=value,
                layer=layer,
                source_file=source_file,
                dependencies=dependencies
            )
        
        # Clear cache when variables are modified
        self.resolved_cache.clear()
    
    def get_variable_definition(self, name: str) -> Optional[VariableDefinition]:
        """Get the highest-priority definition of a variable."""
        return self.variables.get(name)
    
    def build_dependency_graph(self) -> DependencyGraph:
        """Build dependency graph from all variables."""
        graph = DependencyGraph()
        
        for var_def in self.variables.values():
            graph.add_variable(var_def.name, var_def.dependencies)
        
        return graph
    
    def resolve_variable(self, name: str, context: Optional[Dict[str, Any]] = None) -> Union[int, float, EMUValue]:
        """
        Resolve a single variable, handling dependencies recursively.
        
        Args:
            name: Variable name to resolve
            context: Additional context variables (e.g., runtime parameters)
        
        Returns:
            Resolved numeric value or EMUValue
        """
        # Check cache first
        if name in self.resolved_cache:
            return self.resolved_cache[name]
        
        # Check for circular dependency
        if name in self.resolution_in_progress:
            raise CircularDependencyError(f"Circular dependency detected involving variable '{name}'")
        
        # Get variable definition
        var_def = self.get_variable_definition(name)
        if not var_def:
            # Check context for runtime variables
            if context and name in context:
                value = context[name]
                if isinstance(value, (int, float, EMUValue)):
                    self.resolved_cache[name] = value
                    return value
            
            raise VariableNotFoundError(f"Variable '{name}' not found in any layer")
        
        # Mark as in progress
        self.resolution_in_progress.add(name)
        
        try:
            # If already resolved, return cached value
            if var_def.is_resolved and var_def.resolved_value is not None:
                result = var_def.resolved_value
                self.resolved_cache[name] = result
                return result
            
            # Handle different value types
            value = var_def.value
            
            if isinstance(value, (int, float)):
                result = value
            elif isinstance(value, EMUValue):
                result = value
            elif isinstance(value, str):
                # Check if this looks like a formula (has dependencies) or is a literal string
                if var_def.dependencies:
                    # Has dependencies, try to parse and evaluate as formula
                    try:
                        ast = self.parser.parse(value)
                        
                        # Build evaluation context with resolved dependencies
                        eval_context = {}
                        for dep_name in var_def.dependencies:
                            dep_value = self.resolve_variable(dep_name, context)
                            eval_context[dep_name] = dep_value
                        
                        # Add runtime context
                        if context:
                            eval_context.update(context)
                        
                        result = self.parser.evaluate(ast, eval_context)
                    except CircularDependencyError:
                        # Re-raise circular dependency errors without wrapping
                        raise
                    except Exception as e:
                        raise ValueError(f"Failed to evaluate formula for variable '{name}': {value}. Error: {e}")
                else:
                    # No dependencies, treat as literal string value
                    result = value
            else:
                raise ValueError(f"Unsupported value type for variable '{name}': {type(value)}")
            
            # Cache and mark as resolved
            var_def.resolved_value = result
            var_def.is_resolved = True
            self.resolved_cache[name] = result
            
            return result
        
        finally:
            # Remove from in-progress set
            self.resolution_in_progress.remove(name)
    
    def resolve_all(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Union[int, float, EMUValue]]:
        """
        Resolve all variables in dependency order.
        
        Args:
            context: Additional context variables
            
        Returns:
            Dictionary mapping variable names to resolved values
        """
        # Build dependency graph and get resolution order
        graph = self.build_dependency_graph()
        resolution_order = graph.topological_sort()
        
        results = {}
        
        # Resolve variables in dependency order
        for var_name in resolution_order:
            if var_name in self.variables:  # Only resolve our defined variables
                try:
                    results[var_name] = self.resolve_variable(var_name, context)
                except VariableNotFoundError:
                    # Skip variables that aren't defined (might be context-only)
                    continue
        
        return results
    
    def invalidate_cache(self, variable_names: Optional[Set[str]] = None):
        """
        Invalidate cached values for specific variables or all variables.
        
        Args:
            variable_names: Set of variable names to invalidate, or None for all
        """
        if variable_names is None:
            # Clear entire cache
            self.resolved_cache.clear()
            for var_def in self.variables.values():
                var_def.resolved_value = None
                var_def.is_resolved = False
        else:
            # Build dependency graph to find all affected variables
            graph = self.build_dependency_graph()
            
            # Find all variables that depend on the invalidated ones
            affected = set(variable_names)
            queue = deque(variable_names)
            
            while queue:
                var_name = queue.popleft()
                dependents = graph.get_dependents(var_name)
                for dependent in dependents:
                    if dependent not in affected:
                        affected.add(dependent)
                        queue.append(dependent)
            
            # Clear cache for affected variables
            for var_name in affected:
                if var_name in self.resolved_cache:
                    del self.resolved_cache[var_name]
                if var_name in self.variables:
                    self.variables[var_name].resolved_value = None
                    self.variables[var_name].is_resolved = False
    
    def get_dependency_info(self) -> Dict[str, Any]:
        """Get detailed dependency information for debugging."""
        graph = self.build_dependency_graph()
        
        return {
            'variables': {name: {
                'layer': var_def.layer,
                'value': str(var_def.value),
                'dependencies': list(var_def.dependencies),
                'dependents': list(graph.get_dependents(name)),
                'is_resolved': var_def.is_resolved,
                'resolved_value': str(var_def.resolved_value) if var_def.resolved_value is not None else None
            } for name, var_def in self.variables.items()},
            'resolution_order': graph.topological_sort()
        }