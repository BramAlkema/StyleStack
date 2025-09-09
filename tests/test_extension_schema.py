#!/usr/bin/env python3
"""
Test suite for OOXML Extension Schema Validation

Tests the variable definition schema, validation system, and metadata management
for the StyleStack OOXML Extension Variable System.
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

# Test data and fixtures
class VariableType(Enum):
    COLOR = "color"
    FONT = "font" 
    DIMENSION = "dimension"
    POSITION = "position"
    TEXT = "text"
    BOOLEAN = "boolean"
    NUMBER = "number"

class VariableScope(Enum):
    THEME = "theme"
    SLIDE = "slide"
    SHAPE = "shape"
    PARAGRAPH = "paragraph"
    RUN = "run"

class OOXMLValueType(Enum):
    DIRECT = "direct"
    SCHEME_COLOR = "schemeClr"
    THEME_FONT = "themeFont"
    EMU = "emu"
    CALCULATED = "calculated"

@dataclass
class VariableDefinition:
    """Variable definition matching the schema"""
    id: str
    type: VariableType
    scope: VariableScope
    xpath: str
    ooxml_namespace: str
    ooxml_element: str
    ooxml_attribute: str
    ooxml_value_type: OOXMLValueType
    default_value: Any
    dependencies: List[str] = None
    description: str = ""

class TestExtensionSchemaValidation:
    """Test OOXML extension schema validation functionality"""
    
    def test_valid_color_variable_schema(self):
        """Test that valid color variable definitions pass schema validation"""
        color_var = {
            "id": "accent_primary",
            "type": "color",
            "scope": "theme", 
            "xpath": "//a:clrScheme/a:accent1/a:srgbClr/@val",
            "ooxml": {
                "namespace": "http://schemas.openxmlformats.org/drawingml/2006/main",
                "element": "srgbClr",
                "attribute": "val",
                "valueType": "schemeClr"
            },
            "defaultValue": "0066CC",
            "description": "Primary accent color for theme"
        }
        
        # Should pass validation
        assert self._validate_variable_schema(color_var) == True
        
    def test_valid_font_variable_schema(self):
        """Test that valid font variable definitions pass schema validation"""
        font_var = {
            "id": "heading_font",
            "type": "font",
            "scope": "theme",
            "xpath": "//a:fontScheme/a:majorFont/a:latin/@typeface", 
            "ooxml": {
                "namespace": "http://schemas.openxmlformats.org/drawingml/2006/main",
                "element": "latin",
                "attribute": "typeface",
                "valueType": "themeFont"
            },
            "defaultValue": "Segoe UI",
            "description": "Primary heading font"
        }
        
        assert self._validate_variable_schema(font_var) == True
        
    def test_valid_dimension_variable_schema(self):
        """Test that valid dimension variable definitions pass schema validation"""
        dimension_var = {
            "id": "slide_width",
            "type": "dimension", 
            "scope": "slide",
            "xpath": "//p:sldSz/@cx",
            "ooxml": {
                "namespace": "http://schemas.openxmlformats.org/presentationml/2006/main",
                "element": "sldSz",
                "attribute": "cx", 
                "valueType": "emu"
            },
            "defaultValue": "9144000",
            "description": "Slide width in EMU units"
        }
        
        assert self._validate_variable_schema(dimension_var) == True
        
    def test_invalid_variable_missing_required_fields(self):
        """Test that variables missing required fields fail validation"""
        invalid_vars = [
            # Missing id
            {
                "type": "color",
                "scope": "theme",
                "xpath": "//a:accent1/@val",
                "ooxml": {"namespace": "test", "element": "test", "valueType": "direct"}
            },
            # Missing type
            {
                "id": "test_var",
                "scope": "theme", 
                "xpath": "//a:accent1/@val",
                "ooxml": {"namespace": "test", "element": "test", "valueType": "direct"}
            },
            # Missing ooxml section
            {
                "id": "test_var",
                "type": "color",
                "scope": "theme",
                "xpath": "//a:accent1/@val"
            }
        ]
        
        for invalid_var in invalid_vars:
            assert self._validate_variable_schema(invalid_var) == False
            
    def test_invalid_variable_wrong_enum_values(self):
        """Test that variables with invalid enum values fail validation"""
        invalid_enums = [
            # Invalid type
            {
                "id": "test_var",
                "type": "invalid_type",
                "scope": "theme",
                "xpath": "//test",
                "ooxml": {"namespace": "test", "element": "test", "valueType": "direct"}
            },
            # Invalid scope  
            {
                "id": "test_var",
                "type": "color",
                "scope": "invalid_scope",
                "xpath": "//test",
                "ooxml": {"namespace": "test", "element": "test", "valueType": "direct"}
            },
            # Invalid valueType
            {
                "id": "test_var", 
                "type": "color",
                "scope": "theme",
                "xpath": "//test",
                "ooxml": {"namespace": "test", "element": "test", "valueType": "invalid_value_type"}
            }
        ]
        
        for invalid_var in invalid_enums:
            assert self._validate_variable_schema(invalid_var) == False
            
    def test_variable_id_naming_conventions(self):
        """Test that variable IDs follow proper naming conventions"""
        valid_ids = [
            "accent_primary",
            "heading1_font", 
            "slide_width",
            "margin_top",
            "text_color_dark"
        ]
        
        invalid_ids = [
            "123_invalid",  # Starts with number
            "invalid-dash", # Contains dash
            "invalid space", # Contains space
            "invalid@symbol", # Contains symbol
            "", # Empty string
            "a" * 100 # Too long
        ]
        
        for valid_id in valid_ids:
            assert self._validate_variable_id(valid_id) == True
            
        for invalid_id in invalid_ids:
            assert self._validate_variable_id(invalid_id) == False
            
    def test_dependency_validation(self):
        """Test that variable dependencies are properly validated"""
        # Variable with valid dependencies
        dependent_var = {
            "id": "calculated_size",
            "type": "dimension",
            "scope": "shape", 
            "xpath": "//a:ext/@cx",
            "dependencies": ["base_size", "scale_factor"],
            "ooxml": {"namespace": "test", "element": "test", "valueType": "calculated"}
        }
        
        # Should pass with proper dependency list
        assert self._validate_variable_dependencies(dependent_var, ["base_size", "scale_factor"]) == True
        
        # Should fail with missing dependencies
        assert self._validate_variable_dependencies(dependent_var, ["base_size"]) == False
        
    def test_xpath_validation(self):
        """Test that XPath expressions are valid"""
        valid_xpaths = [
            "//a:clrScheme/a:accent1/a:srgbClr/@val",
            "//p:sldSz/@cx",
            "//w:rPr/w:sz/@w:val",
            "//*[@id='title']/text()"
        ]
        
        invalid_xpaths = [
            "",  # Empty
            "not-xpath",  # Invalid syntax
            "//invalid[unclosed",  # Malformed
            "///@invalid"  # Invalid axis
        ]
        
        for valid_xpath in valid_xpaths:
            assert self._validate_xpath(valid_xpath) == True
            
        for invalid_xpath in invalid_xpaths:
            assert self._validate_xpath(invalid_xpath) == False

class TestVariableMetadataManagement:
    """Test variable metadata and management functionality"""
    
    def test_variable_collection_management(self):
        """Test managing collections of variables"""
        variables = [
            VariableDefinition(
                id="accent1",
                type=VariableType.COLOR,
                scope=VariableScope.THEME,
                xpath="//a:accent1/@val",
                ooxml_namespace="http://test",
                ooxml_element="accent1", 
                ooxml_attribute="val",
                ooxml_value_type=OOXMLValueType.SCHEME_COLOR,
                default_value="0066CC"
            ),
            VariableDefinition(
                id="title_font",
                type=VariableType.FONT,
                scope=VariableScope.THEME,
                xpath="//a:majorFont/@typeface",
                ooxml_namespace="http://test",
                ooxml_element="majorFont",
                ooxml_attribute="typeface", 
                ooxml_value_type=OOXMLValueType.THEME_FONT,
                default_value="Segoe UI"
            )
        ]
        
        # Test variable collection operations
        var_manager = self._create_variable_manager(variables)
        
        assert len(var_manager.get_all_variables()) == 2
        assert var_manager.get_variable("accent1") is not None
        assert var_manager.get_variable("nonexistent") is None
        assert len(var_manager.get_variables_by_type(VariableType.COLOR)) == 1
        assert len(var_manager.get_variables_by_scope(VariableScope.THEME)) == 2
        
    def test_variable_dependency_resolution(self):
        """Test dependency resolution for variables"""
        variables = [
            VariableDefinition(
                id="base_size",
                type=VariableType.DIMENSION,
                scope=VariableScope.THEME,
                xpath="//base/@size",
                ooxml_namespace="http://test",
                ooxml_element="base",
                ooxml_attribute="size",
                ooxml_value_type=OOXMLValueType.EMU,
                default_value="12700"
            ),
            VariableDefinition(
                id="scale_factor", 
                type=VariableType.NUMBER,
                scope=VariableScope.THEME,
                xpath="//scale/@factor",
                ooxml_namespace="http://test",
                ooxml_element="scale",
                ooxml_attribute="factor",
                ooxml_value_type=OOXMLValueType.DIRECT,
                default_value="1.5"
            ),
            VariableDefinition(
                id="scaled_size",
                type=VariableType.DIMENSION, 
                scope=VariableScope.SHAPE,
                xpath="//shape/@size",
                dependencies=["base_size", "scale_factor"],
                ooxml_namespace="http://test",
                ooxml_element="shape",
                ooxml_attribute="size",
                ooxml_value_type=OOXMLValueType.CALCULATED,
                default_value="19050"
            )
        ]
        
        var_manager = self._create_variable_manager(variables)
        
        # Test dependency resolution order
        resolution_order = var_manager.get_dependency_resolution_order()
        
        # Variables without dependencies should come first
        assert resolution_order[0] in ["base_size", "scale_factor"] 
        assert resolution_order[1] in ["base_size", "scale_factor"]
        # Dependent variable should come last
        assert resolution_order[2] == "scaled_size"
        
    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies"""
        variables_with_circular_deps = [
            VariableDefinition(
                id="var_a",
                type=VariableType.NUMBER,
                scope=VariableScope.THEME,
                xpath="//a",
                dependencies=["var_b"],
                ooxml_namespace="http://test",
                ooxml_element="a",
                ooxml_attribute="val",
                ooxml_value_type=OOXMLValueType.CALCULATED,
                default_value="1"
            ),
            VariableDefinition(
                id="var_b",
                type=VariableType.NUMBER,
                scope=VariableScope.THEME, 
                xpath="//b",
                dependencies=["var_a"],  # Circular dependency
                ooxml_namespace="http://test",
                ooxml_element="b",
                ooxml_attribute="val",
                ooxml_value_type=OOXMLValueType.CALCULATED,
                default_value="2"
            )
        ]
        
        var_manager = self._create_variable_manager(variables_with_circular_deps)
        
        # Should detect and raise error for circular dependency
        with pytest.raises(ValueError, match="circular dependency"):
            var_manager.get_dependency_resolution_order()

class TestOOXMLValueTypeHandling:
    """Test handling of different OOXML value types"""
    
    def test_color_value_types(self):
        """Test validation of color-related value types"""
        color_types = [
            ("schemeClr", True),   # Valid scheme color reference
            ("direct", True),      # Direct hex color value  
            ("calculated", True),  # Calculated color value
            ("invalid", False)     # Invalid color type
        ]
        
        for value_type, should_be_valid in color_types:
            result = self._validate_color_value_type(value_type)
            assert result == should_be_valid
            
    def test_dimension_value_types(self):
        """Test validation of dimension-related value types"""
        dimension_types = [
            ("emu", True),        # EMU units
            ("direct", True),     # Direct numeric value
            ("calculated", True), # Calculated dimension
            ("invalid", False)    # Invalid dimension type
        ]
        
        for value_type, should_be_valid in dimension_types:
            result = self._validate_dimension_value_type(value_type)
            assert result == should_be_valid
            
    def test_font_value_types(self):
        """Test validation of font-related value types"""
        font_types = [
            ("themeFont", True),  # Theme font reference
            ("direct", True),     # Direct font name
            ("invalid", False)    # Invalid font type
        ]
        
        for value_type, should_be_valid in font_types:
            result = self._validate_font_value_type(value_type)
            assert result == should_be_valid

class TestSchemaErrorHandling:
    """Test comprehensive error handling in schema validation"""
    
    def test_detailed_validation_errors(self):
        """Test that validation errors provide detailed information"""
        invalid_var = {
            "id": "123_bad_id",  # Invalid ID
            "type": "bad_type",  # Invalid type
            "scope": "bad_scope", # Invalid scope
            # Missing required ooxml section
        }
        
        errors = self._get_validation_errors(invalid_var)
        
        # Should have multiple specific errors
        assert len(errors) >= 3
        assert any("invalid ID" in error for error in errors)
        assert any("invalid type" in error for error in errors) 
        assert any("missing ooxml" in error for error in errors)
        
    def test_xpath_syntax_error_reporting(self):
        """Test detailed XPath syntax error reporting"""
        invalid_xpaths = [
            "//unclosed[bracket",
            "//invalid::axis",
            "//missing'quote"
        ]
        
        for xpath in invalid_xpaths:
            error = self._get_xpath_error(xpath)
            assert error is not None
            assert "syntax" in error.lower()
            assert xpath in error  # Should include the invalid xpath in error message

    # Helper methods for testing (to be implemented)
    def _validate_variable_schema(self, variable: Dict[str, Any]) -> bool:
        """Helper method to validate variable schema - to be implemented"""
        # This will be implemented in the actual schema validation system
        pass
        
    def _validate_variable_id(self, variable_id: str) -> bool:
        """Helper method to validate variable ID format - to be implemented"""
        pass
        
    def _validate_variable_dependencies(self, variable: Dict[str, Any], available_vars: List[str]) -> bool:
        """Helper method to validate variable dependencies - to be implemented"""
        pass
        
    def _validate_xpath(self, xpath: str) -> bool:
        """Helper method to validate XPath syntax - to be implemented"""
        pass
        
    def _create_variable_manager(self, variables: List[VariableDefinition]):
        """Helper method to create variable manager - to be implemented"""
        pass
        
    def _validate_color_value_type(self, value_type: str) -> bool:
        """Helper method to validate color value types - to be implemented"""
        pass
        
    def _validate_dimension_value_type(self, value_type: str) -> bool:
        """Helper method to validate dimension value types - to be implemented"""
        pass
        
    def _validate_font_value_type(self, value_type: str) -> bool:
        """Helper method to validate font value types - to be implemented"""
        pass
        
    def _get_validation_errors(self, variable: Dict[str, Any]) -> List[str]:
        """Helper method to get detailed validation errors - to be implemented"""
        pass
        
    def _get_xpath_error(self, xpath: str) -> str:
        """Helper method to get XPath syntax error - to be implemented"""
        pass

# Integration test data
SAMPLE_VARIABLES_CONFIG = """
variables:
  theme_colors:
    accent1:
      id: "accent_primary"
      type: "color" 
      scope: "theme"
      xpath: "//a:clrScheme/a:accent1/a:srgbClr/@val"
      ooxml:
        namespace: "http://schemas.openxmlformats.org/drawingml/2006/main"
        element: "srgbClr"
        attribute: "val"
        valueType: "schemeClr"
      defaultValue: "0066CC"
      
  theme_fonts:
    major_font:
      id: "heading_font"
      type: "font"
      scope: "theme"
      xpath: "//a:fontScheme/a:majorFont/a:latin/@typeface"
      ooxml:
        namespace: "http://schemas.openxmlformats.org/drawingml/2006/main"
        element: "latin"
        attribute: "typeface"
        valueType: "themeFont"
      defaultValue: "Segoe UI"
      
  layout_dimensions:
    slide_width:
      id: "slide_width"
      type: "dimension"
      scope: "slide"
      xpath: "//p:sldSz/@cx"
      ooxml:
        namespace: "http://schemas.openxmlformats.org/presentationml/2006/main"
        element: "sldSz"
        attribute: "cx"
        valueType: "emu"
      defaultValue: "9144000"
"""

class TestIntegration:
    """Integration tests for complete schema validation pipeline"""
    
    def test_full_variable_config_validation(self):
        """Test validation of complete variable configuration"""
        config = json.safe_load(SAMPLE_VARIABLES_CONFIG)
        
        # Should successfully validate the complete configuration
        assert self._validate_full_config(config) == True
        
    def test_variable_extraction_from_ooxml(self):
        """Test extracting variables from OOXML templates"""
        # This will test the complete pipeline of finding <extLst> elements
        # and extracting variable definitions
        pass
        
    def _validate_full_config(self, config: Dict[str, Any]) -> bool:
        """Helper method for full config validation - to be implemented"""
        pass

if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])