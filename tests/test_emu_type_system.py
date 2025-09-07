#!/usr/bin/env python3
"""
Test suite for EMU Type System
Tests EMUValue class, mathematical operations, unit conversions, and OOXML positioning
"""

import unittest
import math
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from tools.emu_types import (
        EMUValue, Point, Rectangle,
        EMUConversionError, EMUOverflowError,
        inches_to_emu, points_to_emu, cm_to_emu,
        emu_to_inches, emu_to_points, emu_to_cm
    )
except ImportError:
    # Module doesn't exist yet - that's expected for TDD
    pass


class TestEMUValue(unittest.TestCase):
    """Test EMUValue class for precise OOXML calculations"""
    
    def test_emu_value_creation(self):
        """Test EMUValue creation from different numeric types"""
        # From integer
        emu1 = EMUValue(914400)
        self.assertEqual(emu1.value, 914400)
        self.assertIsInstance(emu1.value, int)
        
        # From float (should convert to int)
        emu2 = EMUValue(914400.7)
        self.assertEqual(emu2.value, 914400)
        self.assertIsInstance(emu2.value, int)
        
        # From zero
        emu3 = EMUValue(0)
        self.assertEqual(emu3.value, 0)
        
        # From negative
        emu4 = EMUValue(-100000)
        self.assertEqual(emu4.value, -100000)
    
    def test_emu_value_from_string(self):
        """Test EMUValue creation from string representations"""
        emu1 = EMUValue("914400")
        self.assertEqual(emu1.value, 914400)
        
        emu2 = EMUValue("914400.5")
        self.assertEqual(emu2.value, 914400)  # Truncated to int
        
        with self.assertRaises(TypeError):
            EMUValue("not_a_number")
    
    def test_emu_value_arithmetic_operations(self):
        """Test arithmetic operations between EMUValue objects"""
        emu1 = EMUValue(1000000)
        emu2 = EMUValue(500000)
        
        # Addition
        result = emu1 + emu2
        self.assertIsInstance(result, EMUValue)
        self.assertEqual(result.value, 1500000)
        
        # Subtraction
        result = emu1 - emu2
        self.assertEqual(result.value, 500000)
        
        # Multiplication
        result = emu1 * 2
        self.assertEqual(result.value, 2000000)
        
        result = 2 * emu1
        self.assertEqual(result.value, 2000000)
        
        # Division
        result = emu1 / 2
        self.assertEqual(result.value, 500000)
        
        # Floor division
        result = emu1 // 3
        self.assertEqual(result.value, 333333)
        
        # Modulo
        result = emu1 % 300000
        self.assertEqual(result.value, 100000)
        
        # Power
        result = EMUValue(100) ** 2
        self.assertEqual(result.value, 10000)
    
    def test_emu_value_comparison_operations(self):
        """Test comparison operations between EMUValue objects"""
        emu1 = EMUValue(1000000)
        emu2 = EMUValue(500000)
        emu3 = EMUValue(1000000)
        
        # Equality
        self.assertTrue(emu1 == emu3)
        self.assertFalse(emu1 == emu2)
        
        # Inequality
        self.assertTrue(emu1 != emu2)
        self.assertFalse(emu1 != emu3)
        
        # Less than
        self.assertTrue(emu2 < emu1)
        self.assertFalse(emu1 < emu2)
        
        # Less than or equal
        self.assertTrue(emu2 <= emu1)
        self.assertTrue(emu1 <= emu3)
        
        # Greater than
        self.assertTrue(emu1 > emu2)
        self.assertFalse(emu2 > emu1)
        
        # Greater than or equal
        self.assertTrue(emu1 >= emu2)
        self.assertTrue(emu1 >= emu3)
    
    def test_emu_value_mixed_operations(self):
        """Test operations between EMUValue and numeric types"""
        emu = EMUValue(1000000)
        
        # With integers
        result = emu + 500000
        self.assertEqual(result.value, 1500000)
        self.assertIsInstance(result, EMUValue)
        
        result = 500000 + emu
        self.assertEqual(result.value, 1500000)
        self.assertIsInstance(result, EMUValue)
        
        # With floats
        result = emu * 1.5
        self.assertEqual(result.value, 1500000)
        
        # Comparisons with numbers
        self.assertTrue(emu > 500000)
        self.assertTrue(emu == 1000000)
        self.assertFalse(emu < 500000)
    
    def test_emu_value_string_representation(self):
        """Test string representations of EMUValue"""
        emu = EMUValue(914400)
        
        # String representation
        self.assertEqual(str(emu), "914400 EMU")
        
        # Repr representation
        self.assertEqual(repr(emu), "EMUValue(914400)")
        
        # For OOXML attributes
        self.assertEqual(emu.to_ooxml_attr(), "914400")
    
    def test_emu_value_type_validation(self):
        """Test type validation and error handling"""
        # Valid types
        EMUValue(100)
        EMUValue(100.5)
        EMUValue("100")
        
        # Invalid types
        with self.assertRaises(TypeError):
            EMUValue(None)
        
        with self.assertRaises(TypeError):
            EMUValue([1, 2, 3])
        
        with self.assertRaises(TypeError):
            EMUValue({"value": 100})
    
    def test_emu_value_overflow_protection(self):
        """Test overflow protection for very large values"""
        # Large but valid values
        large_emu = EMUValue(2**31 - 1)  # Max 32-bit signed integer
        self.assertEqual(large_emu.value, 2**31 - 1)
        
        # Extremely large values should raise overflow error
        with self.assertRaises(EMUOverflowError):
            EMUValue(2**63)  # Too large for practical OOXML use
    
    def test_emu_value_precision(self):
        """Test precision maintenance in calculations"""
        # Test that we maintain integer precision
        emu1 = EMUValue(914400)  # 1 inch
        emu2 = EMUValue(457200)  # 0.5 inches
        
        result = emu1 + emu2
        self.assertEqual(result.value, 1371600)  # Exactly 1.5 inches
        
        # Test division precision
        result = emu1 / 3
        self.assertEqual(result.value, 304800)  # 1/3 inch, truncated to int


class TestUnitConversions(unittest.TestCase):
    """Test unit conversion functions between EMU and other units"""
    
    def test_inches_to_emu_conversion(self):
        """Test conversion from inches to EMU"""
        # 1 inch = 914400 EMU
        result = inches_to_emu(1.0)
        self.assertEqual(result.value, 914400)
        
        # 0.5 inches
        result = inches_to_emu(0.5)
        self.assertEqual(result.value, 457200)
        
        # Fractional inches
        result = inches_to_emu(1.5)
        self.assertEqual(result.value, 1371600)
        
        # Zero inches
        result = inches_to_emu(0)
        self.assertEqual(result.value, 0)
    
    def test_points_to_emu_conversion(self):
        """Test conversion from points to EMU"""
        # 1 point = 12700 EMU
        result = points_to_emu(1.0)
        self.assertEqual(result.value, 12700)
        
        # 12 points (1/6 inch)
        result = points_to_emu(12.0)
        self.assertEqual(result.value, 152400)
        
        # 72 points (1 inch)
        result = points_to_emu(72.0)
        self.assertEqual(result.value, 914400)
    
    def test_cm_to_emu_conversion(self):
        """Test conversion from centimeters to EMU"""
        # 1 cm ≈ 360000 EMU
        result = cm_to_emu(1.0)
        self.assertEqual(result.value, 360000)
        
        # 2.54 cm (1 inch)
        result = cm_to_emu(2.54)
        expected = int(2.54 * 360000)
        self.assertEqual(result.value, expected)
    
    def test_emu_to_inches_conversion(self):
        """Test conversion from EMU to inches"""
        emu = EMUValue(914400)  # 1 inch
        result = emu_to_inches(emu)
        self.assertAlmostEqual(result, 1.0, places=6)
        
        emu = EMUValue(457200)  # 0.5 inches
        result = emu_to_inches(emu)
        self.assertAlmostEqual(result, 0.5, places=6)
    
    def test_emu_to_points_conversion(self):
        """Test conversion from EMU to points"""
        emu = EMUValue(12700)  # 1 point
        result = emu_to_points(emu)
        self.assertAlmostEqual(result, 1.0, places=6)
        
        emu = EMUValue(914400)  # 72 points (1 inch)
        result = emu_to_points(emu)
        self.assertAlmostEqual(result, 72.0, places=6)
    
    def test_emu_to_cm_conversion(self):
        """Test conversion from EMU to centimeters"""
        emu = EMUValue(360000)  # 1 cm
        result = emu_to_cm(emu)
        self.assertAlmostEqual(result, 1.0, places=6)
        
        emu = EMUValue(914400)  # 1 inch ≈ 2.54 cm
        result = emu_to_cm(emu)
        self.assertAlmostEqual(result, 2.54, places=2)
    
    def test_round_trip_conversions(self):
        """Test that conversions are consistent in both directions"""
        # Inches round trip
        original_inches = 1.25
        emu = inches_to_emu(original_inches)
        back_to_inches = emu_to_inches(emu)
        self.assertAlmostEqual(back_to_inches, original_inches, places=6)
        
        # Points round trip
        original_points = 36.0
        emu = points_to_emu(original_points)
        back_to_points = emu_to_points(emu)
        self.assertAlmostEqual(back_to_points, original_points, places=6)
        
        # Centimeters round trip
        original_cm = 5.0
        emu = cm_to_emu(original_cm)
        back_to_cm = emu_to_cm(emu)
        self.assertAlmostEqual(back_to_cm, original_cm, places=6)


class TestPoint(unittest.TestCase):
    """Test Point class for OOXML coordinate positioning"""
    
    def test_point_creation(self):
        """Test Point creation from EMUValue and numeric types"""
        # From EMUValue objects
        point1 = Point(EMUValue(100000), EMUValue(200000))
        self.assertEqual(point1.x.value, 100000)
        self.assertEqual(point1.y.value, 200000)
        
        # From numeric values (should convert to EMUValue)
        point2 = Point(100000, 200000)
        self.assertIsInstance(point2.x, EMUValue)
        self.assertIsInstance(point2.y, EMUValue)
        self.assertEqual(point2.x.value, 100000)
        self.assertEqual(point2.y.value, 200000)
    
    def test_point_operations(self):
        """Test Point arithmetic operations"""
        point1 = Point(100000, 200000)
        point2 = Point(50000, 75000)
        
        # Addition
        result = point1 + point2
        self.assertEqual(result.x.value, 150000)
        self.assertEqual(result.y.value, 275000)
        
        # Subtraction
        result = point1 - point2
        self.assertEqual(result.x.value, 50000)
        self.assertEqual(result.y.value, 125000)
        
        # Scaling
        result = point1 * 2
        self.assertEqual(result.x.value, 200000)
        self.assertEqual(result.y.value, 400000)
        
        result = point1 / 2
        self.assertEqual(result.x.value, 50000)
        self.assertEqual(result.y.value, 100000)
    
    def test_point_distance(self):
        """Test distance calculation between points"""
        point1 = Point(0, 0)
        point2 = Point(300000, 400000)  # 3:4:5 triangle in EMU
        
        distance = point1.distance_to(point2)
        self.assertEqual(distance.value, 500000)  # 5 * 100000
        
        # Distance to self should be zero
        distance = point1.distance_to(point1)
        self.assertEqual(distance.value, 0)
    
    def test_point_string_representation(self):
        """Test Point string representations"""
        point = Point(100000, 200000)
        
        self.assertEqual(str(point), "Point(100000 EMU, 200000 EMU)")
        self.assertEqual(repr(point), "Point(EMUValue(100000), EMUValue(200000))")
    
    def test_point_to_ooxml(self):
        """Test OOXML coordinate generation"""
        point = Point(100000, 200000)
        
        ooxml_dict = point.to_ooxml()
        expected = {"x": "100000", "y": "200000"}
        self.assertEqual(ooxml_dict, expected)


class TestRectangle(unittest.TestCase):
    """Test Rectangle class for OOXML shape positioning"""
    
    def test_rectangle_creation(self):
        """Test Rectangle creation from coordinates and dimensions"""
        # From individual coordinates
        rect1 = Rectangle(100000, 200000, 300000, 400000)
        self.assertEqual(rect1.x.value, 100000)
        self.assertEqual(rect1.y.value, 200000)
        self.assertEqual(rect1.width.value, 300000)
        self.assertEqual(rect1.height.value, 400000)
        
        # From Point and EMUValue objects
        origin = Point(100000, 200000)
        width = EMUValue(300000)
        height = EMUValue(400000)
        rect2 = Rectangle.from_point_and_size(origin, width, height)
        self.assertEqual(rect2.x.value, 100000)
        self.assertEqual(rect2.y.value, 200000)
        self.assertEqual(rect2.width.value, 300000)
        self.assertEqual(rect2.height.value, 400000)
    
    def test_rectangle_properties(self):
        """Test Rectangle computed properties"""
        rect = Rectangle(100000, 200000, 300000, 400000)
        
        # Corner coordinates
        self.assertEqual(rect.left.value, 100000)
        self.assertEqual(rect.top.value, 200000)
        self.assertEqual(rect.right.value, 400000)  # x + width
        self.assertEqual(rect.bottom.value, 600000)  # y + height
        
        # Center point
        center = rect.center()
        self.assertEqual(center.x.value, 250000)  # x + width/2
        self.assertEqual(center.y.value, 400000)  # y + height/2
        
        # Area
        area = rect.area()
        self.assertEqual(area.value, 120000000000)  # width * height
    
    def test_rectangle_intersection(self):
        """Test Rectangle intersection calculations"""
        rect1 = Rectangle(100000, 100000, 200000, 200000)  # 100k-300k, 100k-300k
        rect2 = Rectangle(200000, 200000, 200000, 200000)  # 200k-400k, 200k-400k
        rect3 = Rectangle(250000, 250000, 100000, 100000)  # 250k-350k, 250k-350k
        
        # Overlapping rectangles
        self.assertTrue(rect1.intersects(rect2))
        self.assertTrue(rect1.intersects(rect3))
        self.assertTrue(rect2.intersects(rect3))
        
        # Non-overlapping rectangles
        rect4 = Rectangle(500000, 500000, 100000, 100000)
        self.assertFalse(rect1.intersects(rect4))
        
        # Intersection area
        intersection = rect1.intersection(rect2)
        if intersection:
            self.assertEqual(intersection.width.value, 100000)  # Overlap width
            self.assertEqual(intersection.height.value, 100000)  # Overlap height
    
    def test_rectangle_contains_point(self):
        """Test point containment within Rectangle"""
        rect = Rectangle(100000, 200000, 300000, 400000)
        
        # Points inside rectangle
        inside_point = Point(250000, 400000)
        self.assertTrue(rect.contains_point(inside_point))
        
        # Points on edges (should be considered inside)
        edge_point = Point(100000, 300000)
        self.assertTrue(rect.contains_point(edge_point))
        
        # Points outside rectangle
        outside_point = Point(50000, 100000)
        self.assertFalse(rect.contains_point(outside_point))
        
        # Corner points
        corner_point = Point(100000, 200000)  # Top-left corner
        self.assertTrue(rect.contains_point(corner_point))
    
    def test_rectangle_scaling(self):
        """Test Rectangle scaling operations"""
        rect = Rectangle(100000, 200000, 300000, 400000)
        
        # Uniform scaling
        scaled = rect.scale(2.0)
        self.assertEqual(scaled.x.value, 100000)  # Position unchanged
        self.assertEqual(scaled.y.value, 200000)
        self.assertEqual(scaled.width.value, 600000)  # Width doubled
        self.assertEqual(scaled.height.value, 800000)  # Height doubled
        
        # Non-uniform scaling
        scaled = rect.scale_xy(1.5, 0.5)
        self.assertEqual(scaled.width.value, 450000)  # Width * 1.5
        self.assertEqual(scaled.height.value, 200000)  # Height * 0.5
    
    def test_rectangle_to_ooxml(self):
        """Test OOXML coordinate generation for shapes"""
        rect = Rectangle(100000, 200000, 300000, 400000)
        
        # Standard OOXML format
        ooxml_dict = rect.to_ooxml()
        expected = {
            "x": "100000",
            "y": "200000",
            "cx": "300000",
            "cy": "400000"
        }
        self.assertEqual(ooxml_dict, expected)
        
        # PowerPoint specific format (uses off/ext)
        ppt_dict = rect.to_ooxml(format="ppt")
        expected_ppt = {
            "off": {"x": "100000", "y": "200000"},
            "ext": {"cx": "300000", "cy": "400000"}
        }
        self.assertEqual(ppt_dict, expected_ppt)
    
    def test_rectangle_string_representation(self):
        """Test Rectangle string representations"""
        rect = Rectangle(100000, 200000, 300000, 400000)
        
        expected_str = "Rectangle(100000 EMU, 200000 EMU, 300000 EMU × 400000 EMU)"
        self.assertEqual(str(rect), expected_str)
        
        expected_repr = "Rectangle(EMUValue(100000), EMUValue(200000), EMUValue(300000), EMUValue(400000))"
        self.assertEqual(repr(rect), expected_repr)


class TestEMUErrorHandling(unittest.TestCase):
    """Test error handling for EMU type system"""
    
    def test_division_by_zero(self):
        """Test division by zero error handling"""
        emu = EMUValue(1000000)
        
        with self.assertRaises(ZeroDivisionError):
            emu / 0
        
        with self.assertRaises(ZeroDivisionError):
            emu // 0
        
        with self.assertRaises(ZeroDivisionError):
            emu % 0
    
    def test_invalid_conversions(self):
        """Test invalid unit conversion error handling"""
        with self.assertRaises(EMUConversionError):
            inches_to_emu("not_a_number")
        
        with self.assertRaises(EMUConversionError):
            points_to_emu(None)
        
        with self.assertRaises(EMUConversionError):
            cm_to_emu([1, 2, 3])
    
    def test_negative_dimensions(self):
        """Test handling of negative dimensions in shapes"""
        # Rectangles with negative dimensions should raise errors
        with self.assertRaises(ValueError):
            Rectangle(100000, 200000, -300000, 400000)  # Negative width
        
        with self.assertRaises(ValueError):
            Rectangle(100000, 200000, 300000, -400000)  # Negative height
        
        # But negative positions are allowed (for shapes extending off-screen)
        rect = Rectangle(-100000, -200000, 300000, 400000)
        self.assertEqual(rect.x.value, -100000)
    
    def test_extreme_values(self):
        """Test handling of extreme coordinate values"""
        # Very large coordinates (still within OOXML limits)
        large_emu = EMUValue(10**6)  # 1 meter approximately
        self.assertEqual(large_emu.value, 10**6)
        
        # Point with extreme coordinates
        extreme_point = Point(large_emu, large_emu)
        self.assertEqual(extreme_point.x.value, 10**6)
        
        # Rectangle with extreme dimensions
        extreme_rect = Rectangle(0, 0, large_emu, large_emu)
        self.assertEqual(extreme_rect.area().value, 10**12)


class TestEMUIntegrationWithFormulas(unittest.TestCase):
    """Test integration between EMU types and formula parser"""
    
    def test_emu_in_formula_context(self):
        """Test using EMUValue objects in formula evaluation context"""
        # This will be expanded when formula parser integration is implemented
        context = {
            "SLIDE_W": EMUValue(12192000),  # 13.33 inches
            "SLIDE_H": EMUValue(6858000),   # 7.5 inches
            "MARGIN": EMUValue(914400)      # 1 inch
        }
        
        # Test that EMUValue objects can be used as context values
        self.assertIsInstance(context["SLIDE_W"], EMUValue)
        self.assertEqual(context["SLIDE_W"].value, 12192000)
        
        # Test arithmetic with formula context
        safe_width = context["SLIDE_W"] - 2 * context["MARGIN"]
        self.assertIsInstance(safe_width, EMUValue)
        self.assertEqual(safe_width.value, 10363200)  # 13.33 - 2 = 11.33 inches
    
    def test_grid_calculations_with_emu(self):
        """Test grid system calculations using EMU types"""
        # Grid configuration in EMU
        slide_w = EMUValue(12192000)  # 13.33 inches
        safe_margin = EMUValue(1219200)  # 10% margin
        safe_w = slide_w - 2 * safe_margin
        
        cols = 12
        gutter = EMUValue(152400)  # 1/6 inch
        
        # Calculate column width
        total_gutters = (cols - 1) * gutter
        col_w = (safe_w - total_gutters) / cols
        
        # Verify calculations
        self.assertIsInstance(col_w, EMUValue)
        expected_col_w = (safe_w - total_gutters).value // cols  # Integer division
        self.assertEqual(col_w.value, expected_col_w)
        
        # Test column positioning
        def get_column_x(col_num):
            """Get X position for column (1-based)"""
            return safe_margin + (col_num - 1) * (col_w + gutter)
        
        col_2_x = get_column_x(2)
        self.assertIsInstance(col_2_x, EMUValue)
        # Should be margin + 1 * (col_w + gutter)
        expected_x = safe_margin + col_w + gutter
        self.assertEqual(col_2_x.value, expected_x.value)


if __name__ == '__main__':
    # Run the test suite
    unittest.main(verbosity=2)