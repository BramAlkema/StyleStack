"""
Test suite for Formula Variable Resolver

Tests dependency graph resolution, topological sorting, hierarchical 
variable overrides, and integration with Formula Parser and EMU types.
"""

import unittest
from tools.formula_variable_resolver import (
    FormulaVariableResolver, DependencyGraph, VariableDefinition,
    CircularDependencyError, VariableNotFoundError
)
from tools.emu_types import EMUValue


class TestDependencyGraph(unittest.TestCase):
    """Test dependency graph construction and analysis."""
    
    def setUp(self):
        self.graph = DependencyGraph()
    
    def test_add_variable_with_dependencies(self):
        """Test adding variables with dependencies."""
        self.graph.add_variable("A", {"B", "C"})
        self.graph.add_variable("B", {"D"})
        self.graph.add_variable("C", set())
        self.graph.add_variable("D", set())
        
        self.assertEqual(self.graph.get_dependencies("A"), {"B", "C"})
        self.assertEqual(self.graph.get_dependencies("B"), {"D"})
        self.assertEqual(self.graph.get_dependencies("C"), set())
        self.assertEqual(self.graph.get_dependencies("D"), set())
    
    def test_get_dependents(self):
        """Test finding variables that depend on others."""
        self.graph.add_variable("A", {"B"})
        self.graph.add_variable("C", {"B"})
        self.graph.add_variable("B", set())
        
        dependents_of_b = self.graph.get_dependents("B")
        self.assertEqual(dependents_of_b, {"A", "C"})
    
    def test_detect_cycles_no_cycle(self):
        """Test cycle detection with no cycles."""
        self.graph.add_variable("A", {"B"})
        self.graph.add_variable("B", {"C"})
        self.graph.add_variable("C", set())
        
        cycles = self.graph.detect_cycles()
        self.assertEqual(len(cycles), 0)
    
    def test_detect_cycles_simple_cycle(self):
        """Test cycle detection with simple cycle."""
        self.graph.add_variable("A", {"B"})
        self.graph.add_variable("B", {"A"})
        
        cycles = self.graph.detect_cycles()
        self.assertEqual(len(cycles), 1)
        # Cycle should contain both A and B
        cycle = cycles[0]
        self.assertIn("A", cycle)
        self.assertIn("B", cycle)
    
    def test_detect_cycles_complex_cycle(self):
        """Test cycle detection with complex cycle."""
        self.graph.add_variable("A", {"B"})
        self.graph.add_variable("B", {"C"})
        self.graph.add_variable("C", {"A"})
        
        cycles = self.graph.detect_cycles()
        self.assertEqual(len(cycles), 1)
        cycle = cycles[0]
        self.assertIn("A", cycle)
        self.assertIn("B", cycle)
        self.assertIn("C", cycle)
    
    def test_topological_sort_simple(self):
        """Test topological sort with simple dependencies."""
        self.graph.add_variable("A", {"B"})
        self.graph.add_variable("B", {"C"})
        self.graph.add_variable("C", set())
        
        order = self.graph.topological_sort()
        
        # C should come before B, B should come before A
        c_idx = order.index("C")
        b_idx = order.index("B")
        a_idx = order.index("A")
        
        self.assertLess(c_idx, b_idx)
        self.assertLess(b_idx, a_idx)
    
    def test_topological_sort_with_cycle(self):
        """Test topological sort fails with cycles."""
        self.graph.add_variable("A", {"B"})
        self.graph.add_variable("B", {"A"})
        
        with self.assertRaises(CircularDependencyError):
            self.graph.topological_sort()
    
    def test_topological_sort_complex(self):
        """Test topological sort with complex dependencies."""
        # D -> C -> A, D -> B -> A
        self.graph.add_variable("A", {"B", "C"})
        self.graph.add_variable("B", {"D"})
        self.graph.add_variable("C", {"D"})
        self.graph.add_variable("D", set())
        
        order = self.graph.topological_sort()
        
        # D must come first
        # B and C can be in any order but both after D
        # A must come last
        d_idx = order.index("D")
        b_idx = order.index("B")
        c_idx = order.index("C")
        a_idx = order.index("A")
        
        self.assertLess(d_idx, b_idx)
        self.assertLess(d_idx, c_idx)
        self.assertLess(b_idx, a_idx)
        self.assertLess(c_idx, a_idx)


class TestFormulaVariableResolver(unittest.TestCase):
    """Test formula variable resolution with hierarchical layers."""
    
    def setUp(self):
        self.resolver = FormulaVariableResolver()
    
    def test_add_layer_simple(self):
        """Test adding variables to a layer."""
        variables = {
            "WIDTH": 1000,
            "HEIGHT": 600,
            "AREA": "WIDTH * HEIGHT"
        }
        
        self.resolver.add_layer("core", variables)
        
        width_def = self.resolver.get_variable_definition("WIDTH")
        self.assertIsNotNone(width_def)
        self.assertEqual(width_def.value, 1000)
        self.assertEqual(width_def.layer, "core")
        
        area_def = self.resolver.get_variable_definition("AREA")
        self.assertIsNotNone(area_def)
        self.assertEqual(area_def.dependencies, {"WIDTH", "HEIGHT"})
    
    def test_add_layer_invalid_layer(self):
        """Test adding variables to invalid layer."""
        with self.assertRaises(ValueError):
            self.resolver.add_layer("invalid", {})
    
    def test_resolve_variable_simple_value(self):
        """Test resolving simple numeric variable."""
        self.resolver.add_layer("core", {"WIDTH": 1000})
        
        result = self.resolver.resolve_variable("WIDTH")
        self.assertEqual(result, 1000)
    
    def test_resolve_variable_formula(self):
        """Test resolving variable with formula."""
        variables = {
            "WIDTH": 1000,
            "HEIGHT": 600,
            "AREA": "WIDTH * HEIGHT"
        }
        self.resolver.add_layer("core", variables)
        
        result = self.resolver.resolve_variable("AREA")
        self.assertEqual(result, 600000)
    
    def test_resolve_variable_with_context(self):
        """Test resolving variable with runtime context."""
        self.resolver.add_layer("core", {"RESULT": "BASE * 2"})
        
        context = {"BASE": 50}
        result = self.resolver.resolve_variable("RESULT", context)
        self.assertEqual(result, 100)
    
    def test_resolve_variable_not_found(self):
        """Test resolving non-existent variable."""
        with self.assertRaises(VariableNotFoundError):
            self.resolver.resolve_variable("NONEXISTENT")
    
    def test_resolve_variable_circular_dependency(self):
        """Test resolving variable with circular dependency."""
        variables = {
            "A": "B + 1",
            "B": "A + 1"
        }
        self.resolver.add_layer("core", variables)
        
        with self.assertRaises(CircularDependencyError):
            self.resolver.resolve_variable("A")
    
    def test_resolve_variable_caching(self):
        """Test variable resolution caching."""
        variables = {
            "BASE": 100,
            "DOUBLE": "BASE * 2"
        }
        self.resolver.add_layer("core", variables)
        
        # First resolution should compute and cache
        result1 = self.resolver.resolve_variable("DOUBLE")
        self.assertEqual(result1, 200)
        
        # Second resolution should use cache
        result2 = self.resolver.resolve_variable("DOUBLE")
        self.assertEqual(result2, 200)
        
        # Verify cache is used
        self.assertIn("DOUBLE", self.resolver.resolved_cache)
    
    def test_resolve_all_simple(self):
        """Test resolving all variables."""
        variables = {
            "WIDTH": 1000,
            "HEIGHT": 600,
            "AREA": "WIDTH * HEIGHT",
            "PERIMETER": "2 * (WIDTH + HEIGHT)"
        }
        self.resolver.add_layer("core", variables)
        
        results = self.resolver.resolve_all()
        
        expected = {
            "WIDTH": 1000,
            "HEIGHT": 600,
            "AREA": 600000,
            "PERIMETER": 3200
        }
        
        self.assertEqual(results, expected)
    
    def test_resolve_all_with_context(self):
        """Test resolving all variables with context."""
        variables = {
            "RESULT": "INPUT * 3"
        }
        self.resolver.add_layer("core", variables)
        
        context = {"INPUT": 10}
        results = self.resolver.resolve_all(context)
        
        self.assertEqual(results["RESULT"], 30)
    
    def test_layer_priority_override(self):
        """Test layer priority system overriding variables."""
        # Add base layer
        self.resolver.add_layer("core", {"COLOR": "blue"})
        
        # Override in higher priority layer
        self.resolver.add_layer("org", {"COLOR": "red"})
        
        color_def = self.resolver.get_variable_definition("COLOR")
        self.assertEqual(color_def.value, "red")
        self.assertEqual(color_def.layer, "org")
    
    def test_emu_value_integration(self):
        """Test integration with EMUValue types."""
        from tools.emu_types import inches_to_emu
        
        variables = {
            "BASE_WIDTH": inches_to_emu(1.0).value,
            "DOUBLE_WIDTH": "BASE_WIDTH * 2"
        }
        self.resolver.add_layer("core", variables)
        
        result = self.resolver.resolve_variable("DOUBLE_WIDTH")
        self.assertEqual(result, 914400 * 2)
    
    def test_complex_formula_with_dependencies(self):
        """Test complex formula with multiple dependencies."""
        variables = {
            "SLIDE_W": 12192000,
            "SLIDE_H": 6858000,
            "SAFE_L": 1219200,
            "SAFE_T": 685800,
            "COL_W": 673100,
            "GUT": 152400,
            "GRID_X": "SAFE_L + (col - 1) * (COL_W + GUT)"
        }
        self.resolver.add_layer("core", variables)
        
        context = {"col": 2}
        result = self.resolver.resolve_variable("GRID_X", context)
        expected = 1219200 + (2 - 1) * (673100 + 152400)
        self.assertEqual(result, expected)
    
    def test_invalidate_cache_all(self):
        """Test invalidating entire cache."""
        variables = {
            "BASE": 100,
            "DOUBLE": "BASE * 2"
        }
        self.resolver.add_layer("core", variables)
        
        # Resolve and cache
        self.resolver.resolve_variable("DOUBLE")
        self.assertIn("DOUBLE", self.resolver.resolved_cache)
        
        # Invalidate all
        self.resolver.invalidate_cache()
        self.assertNotIn("DOUBLE", self.resolver.resolved_cache)
        
        # Verify variable definition is marked as unresolved
        double_def = self.resolver.get_variable_definition("DOUBLE")
        self.assertFalse(double_def.is_resolved)
    
    def test_invalidate_cache_specific(self):
        """Test invalidating specific variables and their dependents."""
        variables = {
            "BASE": 100,
            "DOUBLE": "BASE * 2",
            "TRIPLE": "BASE * 3",
            "INDEPENDENT": 500
        }
        self.resolver.add_layer("core", variables)
        
        # Resolve all
        results = self.resolver.resolve_all()
        self.assertEqual(len(self.resolver.resolved_cache), 4)
        
        # Invalidate BASE (should affect DOUBLE and TRIPLE but not INDEPENDENT)
        self.resolver.invalidate_cache({"BASE"})
        
        # BASE, DOUBLE, and TRIPLE should be cleared
        self.assertNotIn("BASE", self.resolver.resolved_cache)
        self.assertNotIn("DOUBLE", self.resolver.resolved_cache)
        self.assertNotIn("TRIPLE", self.resolver.resolved_cache)
        
        # INDEPENDENT should remain cached
        self.assertIn("INDEPENDENT", self.resolver.resolved_cache)
    
    def test_build_dependency_graph(self):
        """Test building dependency graph."""
        variables = {
            "A": "B + C",
            "B": "D * 2",
            "C": 100,
            "D": 50
        }
        self.resolver.add_layer("core", variables)
        
        graph = self.resolver.build_dependency_graph()
        
        self.assertEqual(graph.get_dependencies("A"), {"B", "C"})
        self.assertEqual(graph.get_dependencies("B"), {"D"})
        self.assertEqual(graph.get_dependencies("C"), set())
        self.assertEqual(graph.get_dependencies("D"), set())
    
    def test_get_dependency_info(self):
        """Test getting dependency information for debugging."""
        variables = {
            "WIDTH": 1000,
            "HEIGHT": 600,
            "AREA": "WIDTH * HEIGHT"
        }
        self.resolver.add_layer("core", variables)
        
        # Resolve one variable
        self.resolver.resolve_variable("WIDTH")
        
        info = self.resolver.get_dependency_info()
        
        self.assertIn("variables", info)
        self.assertIn("resolution_order", info)
        
        # Check variable info
        width_info = info["variables"]["WIDTH"]
        self.assertEqual(width_info["layer"], "core")
        self.assertEqual(width_info["value"], "1000")
        self.assertEqual(width_info["dependencies"], [])
        self.assertTrue(width_info["is_resolved"])
        
        area_info = info["variables"]["AREA"]
        self.assertEqual(sorted(area_info["dependencies"]), ["HEIGHT", "WIDTH"])
        
        # Check resolution order
        order = info["resolution_order"]
        width_idx = order.index("WIDTH")
        height_idx = order.index("HEIGHT")
        area_idx = order.index("AREA")
        
        self.assertLess(width_idx, area_idx)
        self.assertLess(height_idx, area_idx)
    
    def test_formula_error_handling(self):
        """Test handling of formula evaluation errors."""
        variables = {
            "INVALID": "UNDEFINED_VAR + 1"
        }
        self.resolver.add_layer("core", variables)
        
        with self.assertRaises(ValueError) as cm:
            self.resolver.resolve_variable("INVALID")
        
        self.assertIn("Failed to evaluate formula", str(cm.exception))
        self.assertIn("INVALID", str(cm.exception))
    
    def test_non_formula_string_handling(self):
        """Test handling of string values that aren't formulas."""
        variables = {
            "COLOR": "blue",
            "FONT": "Arial",
            "HEX_COLOR": "#FF6600"
        }
        self.resolver.add_layer("core", variables)
        
        # These should be treated as literal strings (no dependencies = literal)
        result = self.resolver.resolve_variable("COLOR")
        self.assertEqual(result, "blue")
        
        result = self.resolver.resolve_variable("FONT")
        self.assertEqual(result, "Arial")
        
        result = self.resolver.resolve_variable("HEX_COLOR")
        self.assertEqual(result, "#FF6600")


if __name__ == "__main__":
    unittest.main()