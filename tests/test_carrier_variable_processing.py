#!/usr/bin/env python3
"""
StyleStack Variable-Based Carrier Architecture - Carrier Variable Processing Tests

Comprehensive test suite for carrier variable syntax parsing and resolution with 
{{carrier.property.value_emu}} format validation, EMU precision calculations,
and hierarchical design token precedence.

Created: 2025-09-12
Author: StyleStack Development Team  
License: MIT
"""

import unittest
import tempfile
import json
import time
import re
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))

# Test data for carrier variable validation
CARRIER_VARIABLE_PATTERNS = {
    'typography': {
        'heading1_font_size_emu': '{{typography.heading1.font_size_emu}}',
        'body_font_size_emu': '{{typography.body.font_size_emu}}',
        'body_line_height_emu': '{{typography.body.line_height_emu}}',
        'caption_font_size_emu': '{{typography.caption.font_size_emu}}'
    },
    'spacing': {
        'margin_top_emu': '{{spacing.margin.top_emu}}',
        'margin_bottom_emu': '{{spacing.margin.bottom_emu}}',
        'padding_left_emu': '{{spacing.padding.left_emu}}',
        'padding_right_emu': '{{spacing.padding.right_emu}}'
    },
    'color': {
        'primary_background': '{{color.primary.background}}',
        'secondary_text': '{{color.secondary.text}}',
        'accent_border': '{{color.accent.border}}'
    },
    'shapes': {
        'border_width_emu': '{{shapes.border.width_emu}}',
        'corner_radius_emu': '{{shapes.corner.radius_emu}}',
        'shadow_offset_emu': '{{shapes.shadow.offset_emu}}'
    }
}

# Expected EMU values with 360 EMU baseline grid alignment
EXPECTED_EMU_VALUES = {
    'typography.heading1.font_size_emu': 28800,  # 32pt = 28800 EMU (80 * 360)
    'typography.body.font_size_emu': 14400,     # 16pt = 14400 EMU (40 * 360)
    'typography.body.line_height_emu': 18000,   # 20pt = 18000 EMU (50 * 360)
    'typography.caption.font_size_emu': 10800,  # 12pt = 10800 EMU (30 * 360)
    'spacing.margin.top_emu': 7200,             # 8pt = 7200 EMU (20 * 360)
    'spacing.margin.bottom_emu': 7200,          # 8pt = 7200 EMU (20 * 360)
    'spacing.padding.left_emu': 3600,           # 4pt = 3600 EMU (10 * 360)
    'spacing.padding.right_emu': 3600,          # 4pt = 3600 EMU (10 * 360)
    'shapes.border.width_emu': 1800,            # 2pt = 1800 EMU (5 * 360)
    'shapes.corner.radius_emu': 1440,           # 1.6pt = 1440 EMU (4 * 360)
    'shapes.shadow.offset_emu': 720             # 0.8pt = 720 EMU (2 * 360)
}

# Design token hierarchy for testing precedence
DESIGN_SYSTEM_TOKENS = {
    'typography.heading1.font_size_emu': 28800,
    'typography.body.font_size_emu': 14400,
    'color.primary.background': '#4472C4',
    'spacing.margin.top_emu': 7200
}

CORPORATE_TOKENS = {
    'typography.body.font_size_emu': 15840,  # Override: 17.6pt = 15840 EMU (44 * 360)
    'color.primary.background': '#FF6B35',   # Brand color override
    'spacing.margin.top_emu': 5400           # Tighter spacing: 6pt = 5400 EMU (15 * 360)
}

CHANNEL_TOKENS = {
    'typography.body.font_size_emu': 16200,  # Presentation override: 18pt = 16200 EMU (45 * 360)
    'spacing.margin.top_emu': 9000           # Presentation spacing: 10pt = 9000 EMU (25 * 360)
}

TEMPLATE_TOKENS = {
    'typography.body.font_size_emu': 15120   # Final override: 16.8pt = 15120 EMU (42 * 360)
}


class CarrierVariablePatternValidator:
    """Validator for carrier variable syntax patterns"""
    
    # Regex pattern for carrier variable syntax: {{carrier.property.value_emu}}
    CARRIER_PATTERN = re.compile(r'\{\{([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)\}\}')
    EMU_PATTERN = re.compile(r'.*_emu$')
    
    @classmethod
    def is_valid_carrier_variable(cls, variable_text: str) -> bool:
        """Validate carrier variable syntax"""
        match = cls.CARRIER_PATTERN.match(variable_text)
        return match is not None
    
    @classmethod
    def extract_variable_path(cls, variable_text: str) -> Optional[str]:
        """Extract variable path from carrier variable"""
        match = cls.CARRIER_PATTERN.match(variable_text)
        return match.group(1) if match else None
    
    @classmethod
    def is_emu_variable(cls, variable_path: str) -> bool:
        """Check if variable represents EMU units"""
        return cls.EMU_PATTERN.match(variable_path) is not None
    
    @classmethod
    def validate_emu_precision(cls, value: int, baseline_grid: int = 360) -> tuple[bool, int]:
        """Validate EMU value aligns with baseline grid"""
        remainder = value % baseline_grid
        if remainder == 0:
            return True, 0
        else:
            # Calculate deviation from nearest grid line
            deviation = min(remainder, baseline_grid - remainder)
            return deviation < 1, deviation


class EMUCalculationEngine:
    """Engine for precise EMU calculations with baseline grid alignment"""
    
    BASELINE_GRID_EMU = 360  # 360 EMU = 1pt baseline grid
    MAX_DEVIATION_EMU = 1    # Maximum allowed deviation
    
    @classmethod
    def points_to_emu(cls, points: float) -> int:
        """Convert points to EMU with baseline grid alignment"""
        # 1 point = 360 EMU in our baseline grid system
        # For fractional points, use precise float multiplication then round to int
        precise_emu = points * cls.BASELINE_GRID_EMU
        
        # Round to nearest integer EMU value
        return int(round(precise_emu))
    
    @classmethod
    def emu_to_points(cls, emu: int) -> float:
        """Convert EMU to points"""
        return emu / cls.BASELINE_GRID_EMU
    
    @classmethod
    def validate_precision(cls, emu_value: int) -> tuple[bool, int]:
        """Validate EMU value precision against baseline grid"""
        return CarrierVariablePatternValidator.validate_emu_precision(
            emu_value, cls.BASELINE_GRID_EMU
        )


class HierarchicalTokenResolver:
    """Resolver for hierarchical design token precedence"""
    
    def __init__(self):
        self.token_layers = []
    
    def add_token_layer(self, layer_name: str, tokens: Dict[str, Any], precedence: int):
        """Add a token layer with precedence (higher number = higher precedence)"""
        self.token_layers.append({
            'name': layer_name,
            'tokens': tokens,
            'precedence': precedence
        })
        # Sort by precedence (highest first)
        self.token_layers.sort(key=lambda x: x['precedence'], reverse=True)
    
    def resolve_token(self, token_path: str) -> tuple[Optional[Any], Optional[str]]:
        """Resolve token value using hierarchical precedence"""
        for layer in self.token_layers:
            if token_path in layer['tokens']:
                return layer['tokens'][token_path], layer['name']
        return None, None
    
    def get_all_resolved_tokens(self) -> Dict[str, Any]:
        """Get all resolved tokens with precedence applied"""
        resolved = {}
        
        # Start with lowest precedence and override with higher precedence
        for layer in reversed(self.token_layers):
            resolved.update(layer['tokens'])
        
        return resolved


class TestCarrierVariableSyntaxValidation(unittest.TestCase):
    """Test suite for carrier variable syntax validation"""
    
    def setUp(self):
        """Set up test environment"""
        self.validator = CarrierVariablePatternValidator()
        self.emu_engine = EMUCalculationEngine()
    
    def test_valid_carrier_variable_patterns(self):
        """Test validation of valid carrier variable patterns"""
        valid_patterns = [
            '{{typography.heading1.font_size_emu}}',
            '{{spacing.margin.top_emu}}',
            '{{color.primary.background}}',
            '{{shapes.border.width_emu}}',
            '{{layout.column.width_emu}}'
        ]
        
        for pattern in valid_patterns:
            with self.subTest(pattern=pattern):
                self.assertTrue(
                    self.validator.is_valid_carrier_variable(pattern),
                    f"Pattern should be valid: {pattern}"
                )
    
    def test_invalid_carrier_variable_patterns(self):
        """Test validation of invalid carrier variable patterns"""
        invalid_patterns = [
            '{{typography.heading1}}',              # Missing third component
            '{{typography}}',                       # Missing second and third
            '{typography.heading1.font_size_emu}',  # Single braces
            '{{typography.heading1.font_size_emu}', # Missing closing brace
            '{{typography-heading1.font_size_emu}}', # Invalid separator
            '{{123.heading1.font_size_emu}}',       # Starting with number
            '{{typography..font_size_emu}}',        # Empty middle component
            '{{}}',                                 # Empty variable
            'typography.heading1.font_size_emu'     # No braces
        ]
        
        for pattern in invalid_patterns:
            with self.subTest(pattern=pattern):
                self.assertFalse(
                    self.validator.is_valid_carrier_variable(pattern),
                    f"Pattern should be invalid: {pattern}"
                )
    
    def test_variable_path_extraction(self):
        """Test extraction of variable paths from carrier variables"""
        test_cases = [
            ('{{typography.heading1.font_size_emu}}', 'typography.heading1.font_size_emu'),
            ('{{spacing.margin.top_emu}}', 'spacing.margin.top_emu'),
            ('{{color.primary.background}}', 'color.primary.background'),
            ('{{invalid pattern}}', None),
            ('not_a_variable', None)
        ]
        
        for variable_text, expected_path in test_cases:
            with self.subTest(variable=variable_text):
                actual_path = self.validator.extract_variable_path(variable_text)
                self.assertEqual(
                    actual_path, expected_path,
                    f"Expected path {expected_path}, got {actual_path}"
                )
    
    def test_emu_variable_detection(self):
        """Test detection of EMU unit variables"""
        emu_variables = [
            'typography.heading1.font_size_emu',
            'spacing.margin.top_emu',
            'shapes.border.width_emu'
        ]
        
        non_emu_variables = [
            'color.primary.background',
            'typography.font.family',
            'layout.column.count'
        ]
        
        for var in emu_variables:
            with self.subTest(variable=var):
                self.assertTrue(
                    self.validator.is_emu_variable(var),
                    f"Should be detected as EMU variable: {var}"
                )
        
        for var in non_emu_variables:
            with self.subTest(variable=var):
                self.assertFalse(
                    self.validator.is_emu_variable(var),
                    f"Should not be detected as EMU variable: {var}"
                )


class TestEMUCalculationPrecision(unittest.TestCase):
    """Test suite for EMU calculation precision and baseline grid alignment"""
    
    def setUp(self):
        """Set up test environment"""
        self.emu_engine = EMUCalculationEngine()
        self.validator = CarrierVariablePatternValidator()
    
    def test_points_to_emu_conversion(self):
        """Test precise conversion from points to EMU"""
        test_cases = [
            (12.0, 4320),    # 12pt = 4320 EMU (12 * 360)
            (16.0, 5760),    # 16pt = 5760 EMU (16 * 360)  
            (18.0, 6480),    # 18pt = 6480 EMU (18 * 360)
            (24.0, 8640),    # 24pt = 8640 EMU (24 * 360)
            (32.0, 11520),   # 32pt = 11520 EMU (32 * 360)
            (1.6, 576),      # 1.6pt = 576 EMU (1.6 * 360) 
            (0.8, 288)       # 0.8pt = 288 EMU (0.8 * 360)
        ]
        
        for points, expected_emu in test_cases:
            with self.subTest(points=points):
                actual_emu = self.emu_engine.points_to_emu(points)
                self.assertEqual(
                    actual_emu, expected_emu,
                    f"Points {points} should convert to {expected_emu} EMU, got {actual_emu}"
                )
    
    def test_emu_to_points_conversion(self):
        """Test conversion from EMU back to points"""
        test_cases = [
            (4320, 12.0),    # 4320 EMU = 12pt
            (5760, 16.0),    # 5760 EMU = 16pt
            (6480, 18.0),    # 6480 EMU = 18pt
            (8640, 24.0),    # 8640 EMU = 24pt
            (11520, 32.0),   # 11520 EMU = 32pt
            (360, 1.0),      # 360 EMU = 1pt (baseline)
            (720, 2.0)       # 720 EMU = 2pt
        ]
        
        for emu, expected_points in test_cases:
            with self.subTest(emu=emu):
                actual_points = self.emu_engine.emu_to_points(emu)
                self.assertAlmostEqual(
                    actual_points, expected_points, places=1,
                    msg=f"EMU {emu} should convert to {expected_points} points, got {actual_points}"
                )
    
    def test_baseline_grid_alignment(self):
        """Test EMU values align with 360 EMU baseline grid"""
        aligned_values = [
            360,    # 1pt baseline
            720,    # 2pt
            1080,   # 3pt
            1440,   # 4pt
            1800,   # 5pt
            3600,   # 10pt
            7200,   # 20pt
            14400,  # 40pt
            28800   # 80pt
        ]
        
        misaligned_values = [
            361,    # 1 EMU off
            719,    # 1 EMU off
            1081,   # 1 EMU off
            1439,   # 1 EMU off
            3601    # 1 EMU off
        ]
        
        for value in aligned_values:
            with self.subTest(value=value):
                is_aligned, deviation = self.validator.validate_emu_precision(value)
                self.assertTrue(
                    is_aligned,
                    f"Value {value} should be aligned with baseline grid"
                )
                self.assertEqual(
                    deviation, 0,
                    f"Aligned value {value} should have zero deviation"
                )
        
        for value in misaligned_values:
            with self.subTest(value=value):
                is_aligned, deviation = self.validator.validate_emu_precision(value)
                self.assertFalse(
                    is_aligned,
                    f"Value {value} should not be aligned with baseline grid"
                )
                self.assertGreaterEqual(
                    deviation, 1,
                    f"Misaligned value {value} should have deviation >= 1"
                )
    
    def test_precision_tolerance(self):
        """Test EMU precision tolerance within 1 EMU deviation"""
        # Values that should pass precision test (deviation < 1 EMU)
        precise_values = [
            360,   # Perfect alignment
            720,   # Perfect alignment
            1080   # Perfect alignment
        ]
        
        # Values that should fail precision test (deviation >= 1 EMU)
        imprecise_values = [
            361,   # 1 EMU deviation (fails)
            358,   # 2 EMU deviation (fails)  
            722,   # 2 EMU deviation (fails)
            1085   # 5 EMU deviation (fails)
        ]
        
        for value in precise_values:
            with self.subTest(value=value, test_type="precise"):
                is_precise, deviation = self.emu_engine.validate_precision(value)
                self.assertTrue(
                    is_precise,
                    f"Value {value} should pass precision test, deviation: {deviation}"
                )
        
        for value in imprecise_values:
            with self.subTest(value=value, test_type="imprecise"):
                is_precise, deviation = self.emu_engine.validate_precision(value)
                self.assertFalse(
                    is_precise,
                    f"Value {value} should fail precision test, deviation: {deviation}"
                )


class TestHierarchicalTokenPrecedence(unittest.TestCase):
    """Test suite for hierarchical design token precedence resolution"""
    
    def setUp(self):
        """Set up test environment with token hierarchy"""
        self.resolver = HierarchicalTokenResolver()
        
        # Add layers in precedence order (higher number = higher precedence)
        self.resolver.add_token_layer('Design System', DESIGN_SYSTEM_TOKENS, 1)
        self.resolver.add_token_layer('Corporate', CORPORATE_TOKENS, 2)
        self.resolver.add_token_layer('Channel', CHANNEL_TOKENS, 3)
        self.resolver.add_token_layer('Template', TEMPLATE_TOKENS, 4)
    
    def test_single_layer_resolution(self):
        """Test token resolution from single layer"""
        # Token only in design system layer
        value, layer = self.resolver.resolve_token('color.primary.background')
        self.assertEqual(layer, 'Corporate')  # Should be overridden by corporate layer
        self.assertEqual(value, '#FF6B35')
        
        # Token only in design system (no overrides)
        value, layer = self.resolver.resolve_token('typography.heading1.font_size_emu')
        self.assertEqual(layer, 'Design System')
        self.assertEqual(value, 28800)
    
    def test_hierarchical_precedence_override(self):
        """Test hierarchical precedence with overrides"""
        # typography.body.font_size_emu exists in all layers
        value, layer = self.resolver.resolve_token('typography.body.font_size_emu')
        self.assertEqual(layer, 'Template')  # Highest precedence
        self.assertEqual(value, 15120)  # Template value
        
        # spacing.margin.top_emu exists in design system, corporate, and channel
        value, layer = self.resolver.resolve_token('spacing.margin.top_emu')
        self.assertEqual(layer, 'Channel')  # Highest available precedence
        self.assertEqual(value, 9000)  # Channel value
    
    def test_missing_token_resolution(self):
        """Test resolution of non-existent tokens"""
        value, layer = self.resolver.resolve_token('nonexistent.token.path')
        self.assertIsNone(value)
        self.assertIsNone(layer)
    
    def test_complete_resolved_token_set(self):
        """Test getting complete resolved token set with precedence"""
        resolved = self.resolver.get_all_resolved_tokens()
        
        # Verify precedence is applied correctly
        expected_resolved = {
            'typography.heading1.font_size_emu': 28800,  # Design System (no override)
            'typography.body.font_size_emu': 15120,      # Template (highest precedence)
            'color.primary.background': '#FF6B35',        # Corporate (overrides Design System)
            'spacing.margin.top_emu': 9000                # Channel (overrides Corporate and Design System)
        }
        
        for token_path, expected_value in expected_resolved.items():
            with self.subTest(token=token_path):
                self.assertIn(token_path, resolved)
                self.assertEqual(
                    resolved[token_path], expected_value,
                    f"Token {token_path} should resolve to {expected_value}, got {resolved[token_path]}"
                )


class TestCarrierVariableIntegration(unittest.TestCase):
    """Integration tests combining syntax validation, EMU calculation, and token resolution"""
    
    def setUp(self):
        """Set up integrated test environment"""
        self.validator = CarrierVariablePatternValidator()
        self.emu_engine = EMUCalculationEngine()
        self.resolver = HierarchicalTokenResolver()
        
        # Set up token hierarchy
        self.resolver.add_token_layer('Design System', DESIGN_SYSTEM_TOKENS, 1)
        self.resolver.add_token_layer('Corporate', CORPORATE_TOKENS, 2)
        self.resolver.add_token_layer('Channel', CHANNEL_TOKENS, 3)
        self.resolver.add_token_layer('Template', TEMPLATE_TOKENS, 4)
    
    def test_end_to_end_carrier_variable_processing(self):
        """Test complete end-to-end carrier variable processing"""
        test_template = '''
        <w:rPr>
            <w:sz w:val="{{typography.body.font_size_emu}}"/>
            <w:spacing w:val="{{spacing.margin.top_emu}}"/>  
            <w:color w:val="{{color.primary.background}}"/>
        </w:rPr>
        '''
        
        # Extract all carrier variables
        variables = self.validator.CARRIER_PATTERN.findall(test_template)
        
        # Validate syntax
        for variable_path in variables:
            full_var = f'{{{{{variable_path}}}}}'
            self.assertTrue(
                self.validator.is_valid_carrier_variable(full_var),
                f"Variable should be valid: {full_var}"
            )
        
        # Resolve values using hierarchy
        resolved_values = {}
        for variable_path in variables:
            value, layer = self.resolver.resolve_token(variable_path)
            self.assertIsNotNone(value, f"Token should resolve: {variable_path}")
            resolved_values[variable_path] = value
            
            # Validate EMU precision if applicable
            if self.validator.is_emu_variable(variable_path):
                is_precise, deviation = self.emu_engine.validate_precision(value)
                self.assertTrue(
                    is_precise,
                    f"EMU variable {variable_path} should have precise alignment, deviation: {deviation}"
                )
        
        # Verify expected resolved values  
        expected_final_values = {
            'typography.body.font_size_emu': 15120,  # Template layer override
            'spacing.margin.top_emu': 9000,          # Channel layer override
            'color.primary.background': '#FF6B35'     # Corporate layer override
        }
        
        for variable_path, expected_value in expected_final_values.items():
            self.assertEqual(
                resolved_values[variable_path], expected_value,
                f"Variable {variable_path} should resolve to {expected_value}"
            )
    
    def test_batch_variable_validation(self):
        """Test batch validation of multiple carrier variables"""
        all_variables = []
        for category, patterns in CARRIER_VARIABLE_PATTERNS.items():
            all_variables.extend(patterns.values())
        
        valid_count = 0
        emu_count = 0
        
        for variable in all_variables:
            # Test syntax validation
            if self.validator.is_valid_carrier_variable(variable):
                valid_count += 1
                
                # Extract path and test EMU detection
                path = self.validator.extract_variable_path(variable)
                if path and self.validator.is_emu_variable(path):
                    emu_count += 1
        
        self.assertEqual(valid_count, len(all_variables), 
                        "All test variables should have valid syntax")
        self.assertGreater(emu_count, 0, 
                          "Should detect EMU variables in test set")
    
    def test_precision_validation_across_expected_values(self):
        """Test EMU precision validation across all expected values"""
        precise_count = 0
        total_emu_values = 0
        
        for variable_path, emu_value in EXPECTED_EMU_VALUES.items():
            if self.validator.is_emu_variable(variable_path):
                total_emu_values += 1
                is_precise, deviation = self.emu_engine.validate_precision(emu_value)
                
                if is_precise:
                    precise_count += 1
                else:
                    self.fail(
                        f"Expected EMU value for {variable_path} is not precise: "
                        f"{emu_value} EMU, deviation: {deviation}"
                    )
        
        self.assertGreater(total_emu_values, 0, "Should have EMU values to test")
        self.assertEqual(precise_count, total_emu_values, 
                        "All expected EMU values should be precise")


if __name__ == '__main__':
    # Create test loader and runner
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestCarrierVariableSyntaxValidation,
        TestEMUCalculationPrecision, 
        TestHierarchicalTokenPrecedence,
        TestCarrierVariableIntegration
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # Print summary
    print(f"\nTest Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, trace in result.failures:
            print(f"- {test}: {trace}")
    
    if result.errors:
        print("\nErrors:")
        for test, trace in result.errors:
            print(f"- {test}: {trace}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)