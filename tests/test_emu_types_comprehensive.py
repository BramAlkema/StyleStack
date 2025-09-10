#!/usr/bin/env python3
"""
Comprehensive test suite for EMU Types

Tests the EMU (English Metric Units) type system for precise OOXML calculations.
"""

import unittest
import math

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))

from tools.emu_types import (
    EMUValue,
    EMUOverflowError,
    EMUConversionError,
    EMU_PER_INCH,
    EMU_PER_POINT,
    EMU_PER_CM,
    MAX_EMU_VALUE,
    MIN_EMU_VALUE
)


class TestEMUConstants(unittest.TestCase):
    """Test EMU constants and limits"""
    
    def test_emu_constants(self):
        """Test EMU conversion constants"""
        self.assertEqual(EMU_PER_INCH, 914400)
        self.assertEqual(EMU_PER_POINT, 12700)
        self.assertEqual(EMU_PER_CM, 360000)
        
    def test_emu_limits(self):
        """Test EMU value limits"""
        self.assertEqual(MAX_EMU_VALUE, 2**50)
        self.assertEqual(MIN_EMU_VALUE, -2**50)


class TestEMUExceptions(unittest.TestCase):
    """Test EMU exception classes"""
    
    def test_emu_overflow_error(self):
        """Test EMUOverflowError exception"""
        error = EMUOverflowError("Test overflow")
        self.assertIsInstance(error, OverflowError)
        
    def test_emu_conversion_error(self):
        """Test EMUConversionError exception"""
        error = EMUConversionError("Test conversion error")
        self.assertIsInstance(error, ValueError)


class TestEMUValueCreation(unittest.TestCase):
    """Test EMUValue creation and initialization"""
    
    def test_create_from_int(self):
        """Test creating EMUValue from integer"""
        emu = EMUValue(914400)
        self.assertEqual(emu.value, 914400)
        
    def test_create_from_float(self):
        """Test creating EMUValue from float"""
        emu = EMUValue(914400.5)
        self.assertEqual(emu.value, 914400)  # Should truncate to int
        
    def test_create_from_string_int(self):
        """Test creating EMUValue from string integer"""
        emu = EMUValue("914400")
        self.assertEqual(emu.value, 914400)
        
    def test_create_from_string_float(self):
        """Test creating EMUValue from string float"""
        emu = EMUValue("914400.7")
        self.assertEqual(emu.value, 914400)  # Should truncate to int
        
    def test_create_zero(self):
        """Test creating zero EMUValue"""
        emu = EMUValue(0)
        self.assertEqual(emu.value, 0)
        
    def test_create_negative(self):
        """Test creating negative EMUValue"""
        emu = EMUValue(-914400)
        self.assertEqual(emu.value, -914400)


class TestEMUValueConversions(unittest.TestCase):
    """Test EMUValue unit conversions"""
    
    def test_to_inches(self):
        """Test conversion to inches"""
        emu = EMUValue(914400)  # 1 inch
        self.assertAlmostEqual(emu.to_inches(), 1.0, places=6)
        
    def test_to_points(self):
        """Test conversion to points"""
        emu = EMUValue(12700)  # 1 point
        self.assertAlmostEqual(emu.to_points(), 1.0, places=6)
        
    def test_to_cm(self):
        """Test conversion to centimeters"""
        emu = EMUValue(360000)  # 1 cm
        self.assertAlmostEqual(emu.to_cm(), 1.0, places=6)
        
    def test_to_ooxml_attr(self):
        """Test conversion to OOXML attribute string"""
        emu = EMUValue(914400)
        self.assertEqual(emu.to_ooxml_attr(), "914400")


class TestEMUValueArithmetic(unittest.TestCase):
    """Test EMUValue arithmetic operations"""
    
    def test_addition_emu_emu(self):
        """Test adding two EMUValues"""
        emu1 = EMUValue(100)
        emu2 = EMUValue(200)
        result = emu1 + emu2
        self.assertEqual(result.value, 300)
        
    def test_addition_emu_int(self):
        """Test adding EMUValue and integer"""
        emu = EMUValue(100)
        result = emu + 200
        self.assertEqual(result.value, 300)
        
    def test_addition_int_emu(self):
        """Test adding integer and EMUValue"""
        emu = EMUValue(200)
        result = 100 + emu
        self.assertEqual(result.value, 300)
        
    def test_subtraction_emu_emu(self):
        """Test subtracting two EMUValues"""
        emu1 = EMUValue(300)
        emu2 = EMUValue(100)
        result = emu1 - emu2
        self.assertEqual(result.value, 200)
        
    def test_subtraction_emu_int(self):
        """Test subtracting integer from EMUValue"""
        emu = EMUValue(300)
        result = emu - 100
        self.assertEqual(result.value, 200)
        
    def test_subtraction_int_emu(self):
        """Test subtracting EMUValue from integer"""
        emu = EMUValue(100)
        result = 300 - emu
        self.assertEqual(result.value, 200)
        
    def test_multiplication_emu_emu(self):
        """Test multiplying two EMUValues"""
        emu1 = EMUValue(10)
        emu2 = EMUValue(20)
        result = emu1 * emu2
        self.assertEqual(result.value, 200)
        
    def test_multiplication_emu_int(self):
        """Test multiplying EMUValue by integer"""
        emu = EMUValue(10)
        result = emu * 20
        self.assertEqual(result.value, 200)
        
    def test_multiplication_int_emu(self):
        """Test multiplying integer by EMUValue"""
        emu = EMUValue(20)
        result = 10 * emu
        self.assertEqual(result.value, 200)
        
    def test_division_emu_emu(self):
        """Test dividing two EMUValues"""
        emu1 = EMUValue(200)
        emu2 = EMUValue(10)
        result = emu1 / emu2
        self.assertEqual(result.value, 20)
        
    def test_division_emu_int(self):
        """Test dividing EMUValue by integer"""
        emu = EMUValue(200)
        result = emu / 10
        self.assertEqual(result.value, 20)
        
    def test_division_int_emu(self):
        """Test dividing integer by EMUValue"""
        emu = EMUValue(10)
        result = 200 / emu
        self.assertEqual(result.value, 20)
        
    def test_floor_division(self):
        """Test floor division"""
        emu1 = EMUValue(25)
        emu2 = EMUValue(10)
        result = emu1 // emu2
        self.assertEqual(result.value, 2)
        
    def test_modulo(self):
        """Test modulo operation"""
        emu1 = EMUValue(25)
        emu2 = EMUValue(10)
        result = emu1 % emu2
        self.assertEqual(result.value, 5)
        
    def test_power(self):
        """Test power operation"""
        emu1 = EMUValue(5)
        emu2 = EMUValue(2)
        result = emu1 ** emu2
        self.assertEqual(result.value, 25)


class TestEMUValueComparisons(unittest.TestCase):
    """Test EMUValue comparison operations"""
    
    def test_equality_emu_emu(self):
        """Test equality between EMUValues"""
        emu1 = EMUValue(100)
        emu2 = EMUValue(100)
        self.assertTrue(emu1 == emu2)
        
    def test_equality_emu_int(self):
        """Test equality between EMUValue and integer"""
        emu = EMUValue(100)
        self.assertTrue(emu == 100)
        
    def test_inequality_emu_emu(self):
        """Test inequality between EMUValues"""
        emu1 = EMUValue(100)
        emu2 = EMUValue(200)
        self.assertTrue(emu1 != emu2)
        
    def test_less_than(self):
        """Test less than comparison"""
        emu1 = EMUValue(100)
        emu2 = EMUValue(200)
        self.assertTrue(emu1 < emu2)
        self.assertFalse(emu2 < emu1)
        
    def test_less_than_or_equal(self):
        """Test less than or equal comparison"""
        emu1 = EMUValue(100)
        emu2 = EMUValue(100)
        emu3 = EMUValue(200)
        self.assertTrue(emu1 <= emu2)
        self.assertTrue(emu1 <= emu3)
        
    def test_greater_than(self):
        """Test greater than comparison"""
        emu1 = EMUValue(200)
        emu2 = EMUValue(100)
        self.assertTrue(emu1 > emu2)
        self.assertFalse(emu2 > emu1)
        
    def test_greater_than_or_equal(self):
        """Test greater than or equal comparison"""
        emu1 = EMUValue(200)
        emu2 = EMUValue(200)
        emu3 = EMUValue(100)
        self.assertTrue(emu1 >= emu2)
        self.assertTrue(emu1 >= emu3)


class TestEMUValueEdgeCases(unittest.TestCase):
    """Test EMUValue edge cases and error conditions"""
    
    def test_division_by_zero(self):
        """Test division by zero handling"""
        emu = EMUValue(100)
        with self.assertRaises(ZeroDivisionError):
            result = emu / 0
            
    def test_large_values(self):
        """Test handling of large values"""
        emu = EMUValue(MAX_EMU_VALUE)
        self.assertEqual(emu.value, MAX_EMU_VALUE)
        
    def test_small_values(self):
        """Test handling of small values"""
        emu = EMUValue(MIN_EMU_VALUE)
        self.assertEqual(emu.value, MIN_EMU_VALUE)
        
    def test_precision_preservation(self):
        """Test that calculations maintain integer precision"""
        emu1 = EMUValue(EMU_PER_INCH)  # 1 inch
        emu2 = EMUValue(EMU_PER_POINT)  # 1 point
        
        # Complex calculation should maintain precision
        result = (emu1 * 2 + emu2 * 3) / 4
        expected = (EMU_PER_INCH * 2 + EMU_PER_POINT * 3) // 4
        self.assertEqual(result.value, expected)


class TestEMUValueRealWorldScenarios(unittest.TestCase):
    """Test EMUValue with real-world OOXML scenarios"""
    
    def test_page_dimensions(self):
        """Test typical page dimension calculations"""
        # Letter size page: 8.5" x 11"
        page_width = EMUValue(EMU_PER_INCH * 8.5)
        page_height = EMUValue(EMU_PER_INCH * 11)
        
        self.assertAlmostEqual(page_width.to_inches(), 8.5, places=6)
        self.assertAlmostEqual(page_height.to_inches(), 11.0, places=6)
        
    def test_font_size_calculations(self):
        """Test font size calculations in EMU"""
        # 12 point font
        font_size_12pt = EMUValue(EMU_PER_POINT * 12)
        
        self.assertAlmostEqual(font_size_12pt.to_points(), 12.0, places=6)
        
        # Double the font size
        font_size_24pt = font_size_12pt * 2
        self.assertAlmostEqual(font_size_24pt.to_points(), 24.0, places=6)
        
    def test_margin_calculations(self):
        """Test margin calculations"""
        # 1 inch margins
        margin = EMUValue(EMU_PER_INCH)
        
        # Calculate content area for letter size page with 1" margins
        page_width = EMUValue(EMU_PER_INCH * 8.5)
        content_width = page_width - (margin * 2)
        
        self.assertAlmostEqual(content_width.to_inches(), 6.5, places=6)


if __name__ == '__main__':
    unittest.main()