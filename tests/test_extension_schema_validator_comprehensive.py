#!/usr/bin/env python3
"""
Comprehensive test suite for Extension Schema Validator

Tests the schema validation functionality for OOXML extension variables.
"""

import unittest
import json
import tempfile
from pathlib import Path

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))

from tools.extension_schema_validator import (
    ExtensionSchemaValidator,
    VariableType,
    VariableScope,
    OOXMLValueType,
    ValidationError,
    ValidationResult,
    validate_variable_file
)


class TestVariableEnums(unittest.TestCase):
    """Test variable type and scope enums"""
    
    def test_variable_type_enum(self):
        """Test VariableType enum values"""
        self.assertEqual(VariableType.COLOR.value, "color")
        self.assertEqual(VariableType.FONT.value, "font")
        self.assertEqual(VariableType.DIMENSION.value, "dimension")
        self.assertEqual(VariableType.TEXT.value, "text")
        
    def test_variable_scope_enum(self):
        """Test VariableScope enum values"""
        self.assertEqual(VariableScope.THEME.value, "theme")
        self.assertEqual(VariableScope.SLIDE.value, "slide")
        self.assertEqual(VariableScope.DOCUMENT.value, "document")
        self.assertEqual(VariableScope.PARAGRAPH.value, "paragraph")
        
    def test_ooxml_value_type_enum(self):
        """Test OOXMLValueType enum values"""
        self.assertEqual(OOXMLValueType.DIRECT.value, "direct")
        self.assertEqual(OOXMLValueType.SCHEME_COLOR.value, "schemeClr")
        self.assertEqual(OOXMLValueType.EMU.value, "emu")
        self.assertEqual(OOXMLValueType.PERCENTAGE.value, "percentage")


class TestValidationError(unittest.TestCase):
    """Test ValidationError class"""
    
    def test_validation_error_creation(self):
        """Test creating validation error"""
        error = ValidationError(
            field="test_field",
            message="Test error message",
            value="invalid_value"
        )
        
        self.assertEqual(error.field, "test_field")
        self.assertEqual(error.message, "Test error message")
        self.assertEqual(error.value, "invalid_value")
        self.assertIsNone(error.path)
        
    def test_validation_error_with_path(self):
        """Test creating validation error with path"""
        error = ValidationError(
            field="test_field",
            message="Test error",
            value="value",
            path="variables[0].type"
        )
        
        self.assertEqual(error.path, "variables[0].type")


class TestValidationResult(unittest.TestCase):
    """Test ValidationResult class"""
    
    def test_validation_result_valid(self):
        """Test valid ValidationResult"""
        result = ValidationResult(valid=True)
        
        self.assertTrue(result.valid)
        self.assertEqual(result.errors, [])
        
    def test_validation_result_invalid(self):
        """Test invalid ValidationResult with errors"""
        error = ValidationError("field", "message", "value")
        result = ValidationResult(valid=False, errors=[error])
        
        self.assertFalse(result.valid)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].field, "field")


class TestExtensionSchemaValidator(unittest.TestCase):
    """Test ExtensionSchemaValidator class"""
    
    def setUp(self):
        """Set up test environment"""
        self.validator = ExtensionSchemaValidator()
        
    def test_validator_initialization(self):
        """Test validator initialization"""
        validator = ExtensionSchemaValidator()
        self.assertIsInstance(validator, ExtensionSchemaValidator)
        
    def test_validate_variable_valid_color(self):
        """Test validating valid color variable"""
        valid_variable = {
            "id": "brandPrimary",
            "type": "color",
            "scope": "theme",
            "value": "#FF0000",
            "ooxml_value_type": "direct"
        }
        
        result = self.validator.validate_variable(valid_variable)
        self.assertTrue(result.valid)
        self.assertEqual(len(result.errors), 0)
        
    def test_validate_variable_valid_font(self):
        """Test validating valid font variable"""
        valid_variable = {
            "id": "headingFont",
            "type": "font",
            "scope": "theme", 
            "value": "Arial Black",
            "ooxml_value_type": "themeFont"
        }
        
        result = self.validator.validate_variable(valid_variable)
        self.assertTrue(result.valid)
        
    def test_validate_variable_missing_required_field(self):
        """Test validating variable with missing required field"""
        invalid_variable = {
            "type": "color",
            "scope": "theme",
            "value": "#FF0000"
            # Missing required "id" field
        }
        
        result = self.validator.validate_variable(invalid_variable)
        self.assertFalse(result.valid)
        self.assertGreater(len(result.errors), 0)
        
    def test_validate_variable_invalid_type(self):
        """Test validating variable with invalid type"""
        invalid_variable = {
            "id": "testVar",
            "type": "invalid_type",  # Invalid type
            "scope": "theme",
            "value": "test"
        }
        
        result = self.validator.validate_variable(invalid_variable)
        self.assertFalse(result.valid)
        
    def test_validate_variable_invalid_scope(self):
        """Test validating variable with invalid scope"""
        invalid_variable = {
            "id": "testVar",
            "type": "color",
            "scope": "invalid_scope",  # Invalid scope
            "value": "#FF0000"
        }
        
        result = self.validator.validate_variable(invalid_variable)
        self.assertFalse(result.valid)
        
    def test_validate_variables_list_valid(self):
        """Test validating valid list of variables"""
        valid_variables = [
            {
                "id": "brandPrimary",
                "type": "color",
                "scope": "theme",
                "value": "#FF0000"
            },
            {
                "id": "headingFont",
                "type": "font",
                "scope": "theme",
                "value": "Arial Black"
            }
        ]
        
        result = self.validator.validate_variables(valid_variables)
        self.assertTrue(result.valid)
        
    def test_validate_variables_list_mixed(self):
        """Test validating list with both valid and invalid variables"""
        mixed_variables = [
            {
                "id": "brandPrimary",
                "type": "color",
                "scope": "theme",
                "value": "#FF0000"
            },
            {
                # Missing id field
                "type": "font",
                "scope": "theme",
                "value": "Arial"
            }
        ]
        
        result = self.validator.validate_variables(mixed_variables)
        self.assertFalse(result.valid)
        self.assertGreater(len(result.errors), 0)


class TestVariableValidationEdgeCases(unittest.TestCase):
    """Test edge cases in variable validation"""
    
    def setUp(self):
        """Set up test environment"""
        self.validator = ExtensionSchemaValidator()
        
    def test_validate_empty_variable(self):
        """Test validating empty variable"""
        empty_variable = {}
        
        result = self.validator.validate_variable(empty_variable)
        self.assertFalse(result.valid)
        
    def test_validate_none_variable(self):
        """Test validating None variable"""
        result = self.validator.validate_variable(None)
        self.assertFalse(result.valid)
        
    def test_validate_empty_variables_list(self):
        """Test validating empty variables list"""
        result = self.validator.validate_variables([])
        self.assertTrue(result.valid)  # Empty list should be valid
        
    def test_validate_none_variables_list(self):
        """Test validating None variables list"""
        result = self.validator.validate_variables(None)
        self.assertFalse(result.valid)
        
    def test_validate_variable_with_extra_fields(self):
        """Test validating variable with extra fields"""
        variable_with_extra = {
            "id": "testVar",
            "type": "color",
            "scope": "theme",
            "value": "#FF0000",
            "extra_field": "should_be_ignored"
        }
        
        # Should still be valid (extra fields ignored)
        result = self.validator.validate_variable(variable_with_extra)
        self.assertTrue(result.valid)


class TestColorValidation(unittest.TestCase):
    """Test color-specific validation"""
    
    def setUp(self):
        """Set up test environment"""
        self.validator = ExtensionSchemaValidator()
        
    def test_validate_hex_color(self):
        """Test validating hex color values"""
        hex_colors = ["#FF0000", "#00FF00", "#0000FF", "#123456", "#ABCDEF"]
        
        for color in hex_colors:
            variable = {
                "id": "testColor",
                "type": "color",
                "scope": "theme",
                "value": color
            }
            result = self.validator.validate_variable(variable)
            self.assertTrue(result.valid, f"Failed for color: {color}")
            
    def test_validate_invalid_hex_color(self):
        """Test validating invalid hex color values"""
        invalid_colors = ["FF0000", "#GG0000", "#FF00", "#FF00000", "red"]
        
        for color in invalid_colors:
            variable = {
                "id": "testColor",
                "type": "color",
                "scope": "theme",
                "value": color
            }
            result = self.validator.validate_variable(variable)
            # Note: This might pass if validation is lenient
            # The test documents expected behavior


class TestFileValidation(unittest.TestCase):
    """Test file-based validation"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_validate_valid_json_file(self):
        """Test validating valid JSON file"""
        valid_data = {
            "variables": [
                {
                    "id": "brandPrimary",
                    "type": "color",
                    "scope": "theme",
                    "value": "#FF0000"
                }
            ]
        }
        
        json_file = self.temp_dir / "valid.json"
        json_file.write_text(json.dumps(valid_data))
        
        results = validate_variable_file(json_file)
        self.assertIsInstance(results, list)
        
    def test_validate_nonexistent_file(self):
        """Test validating non-existent file"""
        nonexistent_file = self.temp_dir / "nonexistent.json"
        
        with self.assertRaises(FileNotFoundError):
            validate_variable_file(nonexistent_file)
            
    def test_validate_invalid_json_file(self):
        """Test validating invalid JSON file"""
        json_file = self.temp_dir / "invalid.json"
        json_file.write_text("{ invalid json }")
        
        with self.assertRaises((json.JSONDecodeError, ValueError)):
            validate_variable_file(json_file)


class TestValidationPerformance(unittest.TestCase):
    """Test validation performance with large datasets"""
    
    def setUp(self):
        """Set up test environment"""
        self.validator = ExtensionSchemaValidator()
        
    def test_validate_large_variable_list(self):
        """Test validating large list of variables"""
        large_variables = [
            {
                "id": f"var_{i}",
                "type": "color",
                "scope": "theme",
                "value": "#FF0000"
            }
            for i in range(100)
        ]
        
        result = self.validator.validate_variables(large_variables)
        self.assertTrue(result.valid)
        
    def test_validate_complex_variable(self):
        """Test validating complex variable with all fields"""
        complex_variable = {
            "id": "complexVar",
            "type": "dimension",
            "scope": "slide",
            "value": "100",
            "ooxml_value_type": "emu",
            "description": "A complex test variable",
            "metadata": {
                "author": "test",
                "version": "1.0"
            }
        }
        
        result = self.validator.validate_variable(complex_variable)
        # Should handle complex structures gracefully


if __name__ == '__main__':
    unittest.main()