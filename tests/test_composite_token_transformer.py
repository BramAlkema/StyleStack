#!/usr/bin/env python3
"""
Test suite for Composite Token Transformation Module

Tests the transformation of W3C DTCG composite tokens (shadows, borders, gradients)
into proper OOXML elements with EMU-accurate conversions.
"""

import pytest
from lxml import etree
from typing import Dict, Any
import math

# Import the transformer classes (will be implemented)
from tools.composite_token_transformer import (
    ShadowTokenTransformer,
    BorderTokenTransformer, 
    GradientTokenTransformer,
    CompositeTokenError
)
from tools.emu_types import EMUValue, Point, Rectangle


class TestShadowTokenTransformer:
    """Test shadow token transformation to OOXML effectLst elements"""
    
    def setup_method(self):
        """Setup transformer for testing"""
        self.transformer = ShadowTokenTransformer()
    
    def test_basic_shadow_transformation(self):
        """Test basic shadow token to OOXML transformation"""
        shadow_token = {
            "$type": "shadow",
            "$value": {
                "color": "#000000",
                "offsetX": "2px",
                "offsetY": "2px",
                "blur": "4px",
                "spread": "0px"
            },
            "$description": "Basic drop shadow"
        }
        
        ooxml_result = self.transformer.transform(shadow_token)
        
        # Parse the resulting XML
        root = etree.fromstring(ooxml_result)
        
        # Should be wrapped in effectLst
        assert root.tag.endswith('effectLst')
        
        # Should contain outerShdw element
        outer_shadow = root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}outerShdw')
        assert outer_shadow is not None
        
        # Check shadow attributes (converted to EMU)
        assert 'blurRad' in outer_shadow.attrib
        assert 'dist' in outer_shadow.attrib
        assert 'dir' in outer_shadow.attrib
        
        # Verify EMU conversion (4px = 50800 EMU)
        assert outer_shadow.attrib['blurRad'] == '50800'
        
        # Verify distance calculation (sqrt(2^2 + 2^2) * 12700)
        expected_dist = str(int(math.sqrt(4 + 4) * 12700))  # ~35921 EMU
        assert outer_shadow.attrib['dist'] == expected_dist
        
        # Should contain color element
        color_elem = outer_shadow.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr')
        assert color_elem is not None
        assert color_elem.attrib['val'] == '000000'
    
    def test_shadow_with_hex_color_variations(self):
        """Test shadow with different hex color formats"""
        color_variations = [
            ("#FF0000", "FF0000"),
            ("ff0000", "FF0000"),  # Should normalize to uppercase
            ("#f00", "FF0000"),     # Should expand 3-digit hex
            ("red", "FF0000")       # Should handle named colors
        ]
        
        for input_color, expected_hex in color_variations:
            shadow_token = {
                "$type": "shadow",
                "$value": {
                    "color": input_color,
                    "offsetX": "0px",
                    "offsetY": "0px",
                    "blur": "0px",
                    "spread": "0px"
                }
            }
            
            ooxml_result = self.transformer.transform(shadow_token)
            root = etree.fromstring(ooxml_result)
            color_elem = root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr')
            
            assert color_elem.attrib['val'] == expected_hex
    
    def test_inner_shadow_transformation(self):
        """Test inner shadow (negative spread) creates innerShdw"""
        inner_shadow_token = {
            "$type": "shadow",
            "$value": {
                "color": "#000000",
                "offsetX": "0px",
                "offsetY": "0px", 
                "blur": "4px",
                "spread": "-2px"  # Negative spread = inner shadow
            }
        }
        
        ooxml_result = self.transformer.transform(inner_shadow_token)
        root = etree.fromstring(ooxml_result)
        
        # Should create innerShdw instead of outerShdw
        inner_shadow = root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}innerShdw')
        assert inner_shadow is not None
        
        outer_shadow = root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}outerShdw')
        assert outer_shadow is None
    
    def test_shadow_direction_calculation(self):
        """Test correct angle calculation for shadow direction"""
        direction_tests = [
            # (offsetX, offsetY, expected_angle_degrees)
            ("2px", "0px", 0),      # Right = 0°
            ("0px", "2px", 90),     # Down = 90°  
            ("-2px", "0px", 180),   # Left = 180°
            ("0px", "-2px", 270),   # Up = 270°
            ("2px", "2px", 45),     # Down-right = 45°
        ]
        
        for offset_x, offset_y, expected_degrees in direction_tests:
            shadow_token = {
                "$type": "shadow",
                "$value": {
                    "color": "#000000",
                    "offsetX": offset_x,
                    "offsetY": offset_y,
                    "blur": "0px",
                    "spread": "0px"
                }
            }
            
            ooxml_result = self.transformer.transform(shadow_token)
            root = etree.fromstring(ooxml_result)
            outer_shadow = root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}outerShdw')
            
            # OOXML uses 60000ths of degree
            expected_ooxml_angle = str(expected_degrees * 60000)
            assert outer_shadow.attrib['dir'] == expected_ooxml_angle
    
    def test_shadow_emu_precision_conversion(self):
        """Test precise EMU conversions for various units"""
        unit_conversions = [
            ("1px", 12700),    # 1px = 12700 EMU
            ("1pt", 12700),    # 1pt = 12700 EMU  
            ("1in", 914400),   # 1in = 914400 EMU
            ("1mm", 36000),    # 1mm = 36000 EMU (approx)
        ]
        
        for input_value, expected_emu in unit_conversions:
            shadow_token = {
                "$type": "shadow",
                "$value": {
                    "color": "#000000",
                    "offsetX": "0px",
                    "offsetY": "0px",
                    "blur": input_value,
                    "spread": "0px"
                }
            }
            
            ooxml_result = self.transformer.transform(shadow_token)
            root = etree.fromstring(ooxml_result)
            outer_shadow = root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}outerShdw')
            
            assert outer_shadow.attrib['blurRad'] == str(expected_emu)
    
    def test_invalid_shadow_token_handling(self):
        """Test error handling for invalid shadow tokens"""
        invalid_tokens = [
            # Missing required properties
            {
                "$type": "shadow",
                "$value": {
                    "color": "#000000"
                    # Missing offsetX, offsetY, blur, spread
                }
            },
            # Invalid color format
            {
                "$type": "shadow", 
                "$value": {
                    "color": "invalid-color",
                    "offsetX": "0px",
                    "offsetY": "0px",
                    "blur": "0px",
                    "spread": "0px"
                }
            },
            # Invalid dimension format
            {
                "$type": "shadow",
                "$value": {
                    "color": "#000000",
                    "offsetX": "invalid-dimension",
                    "offsetY": "0px", 
                    "blur": "0px",
                    "spread": "0px"
                }
            }
        ]
        
        for invalid_token in invalid_tokens:
            with pytest.raises(CompositeTokenError):
                self.transformer.transform(invalid_token)


class TestBorderTokenTransformer:
    """Test border token transformation to OOXML line elements"""
    
    def setup_method(self):
        """Setup transformer for testing"""
        self.transformer = BorderTokenTransformer()
    
    def test_basic_border_transformation(self):
        """Test basic border token to OOXML transformation"""
        border_token = {
            "$type": "border",
            "$value": {
                "width": "1px",
                "style": "solid", 
                "color": "#E0E0E0"
            },
            "$description": "Default border"
        }
        
        ooxml_result = self.transformer.transform(border_token)
        root = etree.fromstring(ooxml_result)
        
        # Should be a line element
        assert root.tag.endswith('ln')
        
        # Check width attribute (converted to EMU)
        assert root.attrib['w'] == '12700'  # 1px = 12700 EMU
        
        # Check compound style for solid
        assert root.attrib.get('cmpd', 'sng') == 'sng'
        
        # Should contain solidFill element
        solid_fill = root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}solidFill')
        assert solid_fill is not None
        
        # Check color
        color_elem = solid_fill.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr')
        assert color_elem is not None
        assert color_elem.attrib['val'] == 'E0E0E0'
    
    def test_border_style_mappings(self):
        """Test various border styles map to correct OOXML compounds"""
        style_mappings = [
            ("solid", "sng"),
            ("dashed", "dash"),
            ("dotted", "dot"),
            ("double", "dbl"),
            ("groove", "sng"),    # Fallback to single
            ("ridge", "sng"),     # Fallback to single
            ("inset", "sng"),     # Fallback to single
            ("outset", "sng"),    # Fallback to single
        ]
        
        for css_style, ooxml_compound in style_mappings:
            border_token = {
                "$type": "border",
                "$value": {
                    "width": "1px",
                    "style": css_style,
                    "color": "#000000"
                }
            }
            
            ooxml_result = self.transformer.transform(border_token)
            root = etree.fromstring(ooxml_result)
            
            assert root.attrib.get('cmpd', 'sng') == ooxml_compound
    
    def test_border_width_conversions(self):
        """Test border width conversions to EMU"""
        width_tests = [
            ("1px", "12700"),
            ("2px", "25400"),
            ("0.5px", "6350"),
            ("1pt", "12700"),
            ("1mm", "36000"),
        ]
        
        for css_width, expected_emu in width_tests:
            border_token = {
                "$type": "border",
                "$value": {
                    "width": css_width,
                    "style": "solid",
                    "color": "#000000"
                }
            }
            
            ooxml_result = self.transformer.transform(border_token)
            root = etree.fromstring(ooxml_result)
            
            assert root.attrib['w'] == expected_emu
    
    def test_border_with_transparency(self):
        """Test border with alpha transparency"""
        border_token = {
            "$type": "border",
            "$value": {
                "width": "1px",
                "style": "solid",
                "color": "rgba(255, 0, 0, 0.5)"  # 50% transparent red
            }
        }
        
        ooxml_result = self.transformer.transform(border_token)
        root = etree.fromstring(ooxml_result)
        
        # Should have color with alpha
        color_elem = root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr')
        assert color_elem is not None
        assert color_elem.attrib['val'] == 'FF0000'
        
        # Should have alpha element
        alpha_elem = color_elem.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}alpha')
        assert alpha_elem is not None
        assert alpha_elem.attrib['val'] == '50000'  # 50% = 50000/100000
    
    def test_invisible_border_handling(self):
        """Test handling of invisible borders (none, hidden)"""
        invisible_styles = ["none", "hidden"]
        
        for style in invisible_styles:
            border_token = {
                "$type": "border",
                "$value": {
                    "width": "1px",
                    "style": style,
                    "color": "#000000"
                }
            }
            
            ooxml_result = self.transformer.transform(border_token)
            root = etree.fromstring(ooxml_result)
            
            # Should have width of 0 or no fill
            assert root.attrib.get('w', '0') == '0' or \
                   root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}noFill') is not None


class TestGradientTokenTransformer:
    """Test gradient token transformation to OOXML gradFill elements"""
    
    def setup_method(self):
        """Setup transformer for testing"""
        self.transformer = GradientTokenTransformer()
    
    def test_linear_gradient_transformation(self):
        """Test linear gradient token to OOXML transformation"""
        gradient_token = {
            "$type": "gradient",
            "$value": {
                "type": "linear",
                "direction": "to bottom",
                "stops": [
                    {"position": "0%", "color": "#FFFFFF"},
                    {"position": "100%", "color": "#F5F5F5"}
                ]
            },
            "$description": "Subtle vertical gradient"
        }
        
        ooxml_result = self.transformer.transform(gradient_token)
        root = etree.fromstring(ooxml_result)
        
        # Should be gradFill element
        assert root.tag.endswith('gradFill')
        
        # Should have gradient stop list
        gs_list = root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}gsLst')
        assert gs_list is not None
        
        # Should have 2 gradient stops
        stops = gs_list.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}gs')
        assert len(stops) == 2
        
        # Check first stop
        first_stop = stops[0]
        assert first_stop.attrib['pos'] == '0'  # 0% = 0
        first_color = first_stop.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr')
        assert first_color.attrib['val'] == 'FFFFFF'
        
        # Check second stop
        second_stop = stops[1]
        assert second_stop.attrib['pos'] == '100000'  # 100% = 100000
        second_color = second_stop.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr')
        assert second_color.attrib['val'] == 'F5F5F5'
        
        # Should have linear element for direction
        linear = root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}lin')
        assert linear is not None
        assert linear.attrib['scaled'] == '1'
    
    def test_gradient_direction_mappings(self):
        """Test gradient direction mappings to OOXML angles"""
        direction_mappings = [
            ("to right", 0),      # 0° = right
            ("to bottom", 90),    # 90° = down  
            ("to left", 180),     # 180° = left
            ("to top", 270),      # 270° = up
            ("45deg", 45),        # Direct angle
            ("to bottom right", 45),   # Diagonal
            ("to top left", 225),      # Opposite diagonal
        ]
        
        for css_direction, expected_degrees in direction_mappings:
            gradient_token = {
                "$type": "gradient",
                "$value": {
                    "type": "linear",
                    "direction": css_direction,
                    "stops": [
                        {"position": "0%", "color": "#000000"},
                        {"position": "100%", "color": "#FFFFFF"}
                    ]
                }
            }
            
            ooxml_result = self.transformer.transform(gradient_token)
            root = etree.fromstring(ooxml_result)
            linear = root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}lin')
            
            # OOXML uses 60000ths of degree
            expected_ooxml_angle = str(expected_degrees * 60000)
            assert linear.attrib['ang'] == expected_ooxml_angle
    
    def test_radial_gradient_transformation(self):
        """Test radial gradient creates path element instead of linear"""
        radial_gradient_token = {
            "$type": "gradient",
            "$value": {
                "type": "radial",
                "direction": "circle",
                "stops": [
                    {"position": "0%", "color": "#FF0000"},
                    {"position": "100%", "color": "#0000FF"}
                ]
            }
        }
        
        ooxml_result = self.transformer.transform(radial_gradient_token)
        root = etree.fromstring(ooxml_result)
        
        # Should have path element for radial
        path = root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}path')
        assert path is not None
        assert path.attrib['path'] == 'circle'
        
        # Should not have linear element
        linear = root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}lin')
        assert linear is None
    
    def test_gradient_stop_position_conversion(self):
        """Test gradient stop position conversion to OOXML format"""
        position_tests = [
            ("0%", "0"),
            ("25%", "25000"), 
            ("50%", "50000"),
            ("75%", "75000"),
            ("100%", "100000"),
            ("0.5", "50000"),    # Decimal format
        ]
        
        for css_position, expected_ooxml in position_tests:
            gradient_token = {
                "$type": "gradient",
                "$value": {
                    "type": "linear",
                    "direction": "to right",
                    "stops": [
                        {"position": css_position, "color": "#000000"},
                        {"position": "100%", "color": "#FFFFFF"}
                    ]
                }
            }
            
            ooxml_result = self.transformer.transform(gradient_token)
            root = etree.fromstring(ooxml_result)
            stop = root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}gs')
            
            assert stop.attrib['pos'] == expected_ooxml
    
    def test_gradient_with_multiple_stops(self):
        """Test gradient with many color stops"""
        gradient_token = {
            "$type": "gradient",
            "$value": {
                "type": "linear",
                "direction": "to right",
                "stops": [
                    {"position": "0%", "color": "#FF0000"},
                    {"position": "25%", "color": "#00FF00"},
                    {"position": "50%", "color": "#0000FF"},
                    {"position": "75%", "color": "#FFFF00"},
                    {"position": "100%", "color": "#FF00FF"}
                ]
            }
        }
        
        ooxml_result = self.transformer.transform(gradient_token)
        root = etree.fromstring(ooxml_result)
        
        stops = root.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}gs')
        assert len(stops) == 5
        
        # Verify stops are in order
        positions = [int(stop.attrib['pos']) for stop in stops]
        assert positions == [0, 25000, 50000, 75000, 100000]


class TestCompositeTokenIntegration:
    """Test integration between different composite token types"""
    
    def test_shadow_with_border_combination(self):
        """Test that shadow and border can be combined"""
        shadow_transformer = ShadowTokenTransformer()
        border_transformer = BorderTokenTransformer()
        
        shadow_token = {
            "$type": "shadow",
            "$value": {
                "color": "#000000",
                "offsetX": "2px",
                "offsetY": "2px",
                "blur": "4px",
                "spread": "0px"
            }
        }
        
        border_token = {
            "$type": "border", 
            "$value": {
                "width": "1px",
                "style": "solid",
                "color": "#E0E0E0"
            }
        }
        
        shadow_ooxml = shadow_transformer.transform(shadow_token)
        border_ooxml = border_transformer.transform(border_token)
        
        # Both should be valid XML
        shadow_root = etree.fromstring(shadow_ooxml)
        border_root = etree.fromstring(border_ooxml)
        
        assert shadow_root is not None
        assert border_root is not None
    
    def test_composite_token_with_token_references(self):
        """Test composite tokens that reference other tokens"""
        shadow_token = {
            "$type": "shadow",
            "$value": {
                "color": "{color.primary}",  # Token reference
                "offsetX": "{spacing.small}",  # Token reference  
                "offsetY": "{spacing.small}",
                "blur": "{spacing.medium}",
                "spread": "0px"
            }
        }
        
        # Mock token context
        token_context = {
            "color.primary": "#0066CC",
            "spacing.small": "4px", 
            "spacing.medium": "8px"
        }
        
        transformer = ShadowTokenTransformer()
        
        # Should resolve references before transformation
        ooxml_result = transformer.transform(shadow_token, context=token_context)
        root = etree.fromstring(ooxml_result)
        
        # Verify resolved values
        color_elem = root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr')
        assert color_elem.attrib['val'] == '0066CC'


class TestCompositeTokenErrorHandling:
    """Test error handling and validation for composite tokens"""
    
    def test_unsupported_token_type_error(self):
        """Test error for unsupported composite token types"""
        unsupported_token = {
            "$type": "unsupported",
            "$value": {
                "property": "value"
            }
        }
        
        # Import the factory function
        from tools.composite_token_transformer import get_composite_token_transformer
        
        with pytest.raises(CompositeTokenError, match="Unsupported token type"):
            get_composite_token_transformer("unsupported")
    
    def test_malformed_token_structure_error(self):
        """Test error for malformed token structures"""
        malformed_tokens = [
            # Missing $value
            {
                "$type": "shadow"
            },
            # $value is not object
            {
                "$type": "shadow",
                "$value": "not an object"  
            },
            # Empty $value
            {
                "$type": "shadow",
                "$value": {}
            }
        ]
        
        transformer = ShadowTokenTransformer()
        
        for malformed_token in malformed_tokens:
            with pytest.raises(CompositeTokenError):
                transformer.transform(malformed_token)
    
    def test_invalid_emu_conversion_error(self):
        """Test error handling for invalid dimension values"""
        invalid_shadow = {
            "$type": "shadow",
            "$value": {
                "color": "#000000",
                "offsetX": "invalid-dimension",
                "offsetY": "2px", 
                "blur": "4px",
                "spread": "0px"
            }
        }
        
        transformer = ShadowTokenTransformer()
        
        with pytest.raises(CompositeTokenError, match="Invalid dimension"):
            transformer.transform(invalid_shadow)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])