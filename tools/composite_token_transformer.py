#!/usr/bin/env python3
"""
Composite Token Transformation Module

Transforms W3C DTCG composite tokens (shadows, borders, gradients) into 
proper OOXML elements with EMU-accurate conversions for Office compatibility.

This module provides specialized transformers for:
- Shadow tokens -> OOXML effectLst elements (outerShdw/innerShdw)
- Border tokens -> OOXML line elements with compound styles
- Gradient tokens -> OOXML gradFill elements (linear/radial)

All transformations include proper EMU conversions and namespace handling.
"""

import math
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from lxml import etree
import colorsys

from .emu_types import EMUValue, Point, Rectangle


class CompositeTokenError(Exception):
    """Exception raised for composite token transformation errors"""
    pass


class BaseTokenTransformer(ABC):
    """Base class for all composite token transformers"""
    
    # OOXML namespace constants
    DRAWINGML_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
    NSMAP = {'a': DRAWINGML_NS}
    
    def __init__(self):
        """Initialize transformer with OOXML namespace support"""
        self.parser = etree.XMLParser(ns_clean=True, recover=True)
    
    @abstractmethod
    def transform(self, token: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Transform token to OOXML string"""
        pass
    
    def _validate_token_structure(self, token: Dict[str, Any], expected_type: str) -> None:
        """Validate basic token structure"""
        if not isinstance(token, dict):
            raise CompositeTokenError(f"Token must be a dictionary, got {type(token)}")
        
        if token.get('$type') != expected_type:
            raise CompositeTokenError(f"Expected token type '{expected_type}', got '{token.get('$type')}'")
        
        if '$value' not in token:
            raise CompositeTokenError("Token missing required '$value' property")
        
        if not isinstance(token['$value'], dict):
            raise CompositeTokenError("Token '$value' must be an object")
        
        if not token['$value']:
            raise CompositeTokenError("Token '$value' cannot be empty")
    
    def _resolve_token_references(self, value: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Resolve token references in values like {color.primary}"""
        if not context or not isinstance(value, str):
            return value
        
        # Simple token reference resolution
        if value.startswith('{') and value.endswith('}'):
            token_key = value[1:-1]
            if token_key in context:
                return context[token_key]
        
        return value
    
    def _parse_dimension_to_emu(self, dimension: str) -> int:
        """Convert CSS dimension to EMU (English Metric Units)"""
        if not isinstance(dimension, str):
            raise CompositeTokenError(f"Invalid dimension format: {dimension}")
        
        # Remove whitespace and convert to lowercase
        dim = dimension.strip().lower()
        
        # Extract numeric value and unit
        match = re.match(r'^(-?\d*\.?\d+)(px|pt|in|mm|cm)?$', dim)
        if not match:
            raise CompositeTokenError(f"Invalid dimension format: {dimension}")
        
        value, unit = match.groups()
        value = float(value)
        unit = unit or 'px'  # Default to pixels
        
        # Convert to EMU based on unit
        conversions = {
            'px': 12700,    # 1px = 12700 EMU
            'pt': 12700,    # 1pt = 12700 EMU (72pt = 1in)
            'in': 914400,   # 1in = 914400 EMU
            'mm': 36000,    # 1mm ≈ 36000 EMU (25.4mm = 1in)
            'cm': 360000,   # 1cm = 360000 EMU
        }
        
        if unit not in conversions:
            raise CompositeTokenError(f"Unsupported dimension unit: {unit}")
        
        return int(value * conversions[unit])
    
    def _parse_color_to_hex(self, color: str) -> str:
        """Convert color value to 6-digit hex (without #)"""
        if not isinstance(color, str):
            raise CompositeTokenError(f"Invalid color format: {color}")
        
        color = color.strip()
        
        # Handle hex colors (with or without #)
        if color.startswith('#'):
            hex_color = color[1:]
        elif re.match(r'^[0-9a-fA-F]{3,6}$', color):
            hex_color = color
        else:
            hex_color = None
        
        if hex_color is not None:
            # Expand 3-digit hex to 6-digit
            if len(hex_color) == 3:
                hex_color = ''.join([c*2 for c in hex_color])
            if len(hex_color) == 6:
                return hex_color.upper()
        
        # Handle named colors (basic set)
        named_colors = {
            'red': 'FF0000',
            'green': '008000', 
            'blue': '0000FF',
            'white': 'FFFFFF',
            'black': '000000',
            'yellow': 'FFFF00',
            'cyan': '00FFFF',
            'magenta': 'FF00FF',
        }
        
        if color.lower() in named_colors:
            return named_colors[color.lower()]
        
        # Handle rgba format (extract rgb, ignore alpha for now)
        rgba_match = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*[\d.]+)?\)', color)
        if rgba_match:
            r, g, b = rgba_match.groups()
            return f"{int(r):02X}{int(g):02X}{int(b):02X}"
        
        raise CompositeTokenError(f"Unsupported color format: {color}")
    
    def _parse_alpha_from_color(self, color: str) -> Optional[int]:
        """Extract alpha value from rgba color (0-100000 for OOXML)"""
        if not isinstance(color, str):
            return None
        
        rgba_match = re.match(r'rgba\(\d+,\s*\d+,\s*\d+,\s*([\d.]+)\)', color.strip())
        if rgba_match:
            alpha_float = float(rgba_match.group(1))
            # Convert 0-1 alpha to 0-100000 for OOXML
            return int(alpha_float * 100000)
        
        return None
    
    def _create_ooxml_element(self, tag: str, attrib: Optional[Dict[str, str]] = None, 
                            nsmap: Optional[Dict[str, str]] = None) -> etree.Element:
        """Create OOXML element with proper namespace"""
        if nsmap is None:
            nsmap = self.NSMAP
        
        element = etree.Element(f"{{{self.DRAWINGML_NS}}}{tag}", attrib or {}, nsmap=nsmap)
        return element
    
    def _element_to_string(self, element: etree.Element) -> str:
        """Convert element to string with proper XML declaration"""
        return etree.tostring(element, encoding='unicode', pretty_print=True)


class ShadowTokenTransformer(BaseTokenTransformer):
    """Transform shadow tokens to OOXML effectLst elements"""
    
    def transform(self, token: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Transform shadow token to OOXML effectLst with outerShdw/innerShdw"""
        self._validate_token_structure(token, 'shadow')
        
        shadow_value = token['$value']
        required_props = ['color', 'offsetX', 'offsetY', 'blur', 'spread']
        
        for prop in required_props:
            if prop not in shadow_value:
                raise CompositeTokenError(f"Shadow token missing required property: {prop}")
        
        # Resolve token references
        color = self._resolve_token_references(shadow_value['color'], context)
        offset_x = self._resolve_token_references(shadow_value['offsetX'], context)
        offset_y = self._resolve_token_references(shadow_value['offsetY'], context)
        blur = self._resolve_token_references(shadow_value['blur'], context)
        spread = self._resolve_token_references(shadow_value['spread'], context)
        
        # Create effectLst container
        effect_lst = self._create_ooxml_element('effectLst')
        
        # Determine shadow type based on spread
        spread_emu = self._parse_dimension_to_emu(spread)
        is_inner = spread_emu < 0
        
        # Create shadow element
        shadow_elem = self._create_ooxml_element(
            'innerShdw' if is_inner else 'outerShdw',
            self._calculate_shadow_attributes(offset_x, offset_y, blur)
        )
        
        # Add color element
        color_elem = self._create_color_element(color)
        shadow_elem.append(color_elem)
        
        effect_lst.append(shadow_elem)
        
        return self._element_to_string(effect_lst)
    
    def _calculate_shadow_attributes(self, offset_x: str, offset_y: str, blur: str) -> Dict[str, str]:
        """Calculate shadow attributes for OOXML"""
        offset_x_emu = self._parse_dimension_to_emu(offset_x)
        offset_y_emu = self._parse_dimension_to_emu(offset_y)
        blur_emu = self._parse_dimension_to_emu(blur)
        
        # Calculate distance from offset
        distance_emu = int(math.sqrt(offset_x_emu**2 + offset_y_emu**2))
        
        # Calculate direction in OOXML format (60000ths of degree)
        if offset_x_emu == 0 and offset_y_emu == 0:
            direction = 0
        else:
            angle_radians = math.atan2(offset_y_emu, offset_x_emu)
            angle_degrees = math.degrees(angle_radians)
            if angle_degrees < 0:
                angle_degrees += 360
            direction = int(angle_degrees * 60000)
        
        return {
            'blurRad': str(blur_emu),
            'dist': str(distance_emu),
            'dir': str(direction)
        }
    
    def _create_color_element(self, color: str) -> etree.Element:
        """Create OOXML color element with optional alpha"""
        hex_color = self._parse_color_to_hex(color)
        color_elem = self._create_ooxml_element('srgbClr', {'val': hex_color})
        
        # Add alpha if present
        alpha = self._parse_alpha_from_color(color)
        if alpha is not None:
            alpha_elem = self._create_ooxml_element('alpha', {'val': str(alpha)})
            color_elem.append(alpha_elem)
        
        return color_elem


class BorderTokenTransformer(BaseTokenTransformer):
    """Transform border tokens to OOXML line elements"""
    
    # CSS to OOXML style mappings
    STYLE_MAPPINGS = {
        'solid': 'sng',
        'dashed': 'dash',  # Note: OOXML uses prstDash for actual dash pattern
        'dotted': 'dot',   # Note: OOXML uses prstDash for actual dot pattern  
        'double': 'dbl',
        'groove': 'sng',   # Fallback to single
        'ridge': 'sng',    # Fallback to single
        'inset': 'sng',    # Fallback to single
        'outset': 'sng',   # Fallback to single
        'none': 'sng',     # Will be handled with width=0 or noFill
        'hidden': 'sng',   # Will be handled with width=0 or noFill
    }
    
    def transform(self, token: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Transform border token to OOXML line element"""
        self._validate_token_structure(token, 'border')
        
        border_value = token['$value']
        required_props = ['width', 'style', 'color']
        
        for prop in required_props:
            if prop not in border_value:
                raise CompositeTokenError(f"Border token missing required property: {prop}")
        
        # Resolve token references
        width = self._resolve_token_references(border_value['width'], context)
        style = self._resolve_token_references(border_value['style'], context)
        color = self._resolve_token_references(border_value['color'], context)
        
        # Create line element
        width_emu = self._parse_dimension_to_emu(width)
        is_invisible = style in ['none', 'hidden']
        
        line_attrs = {
            'w': '0' if is_invisible else str(width_emu),
            'cmpd': self.STYLE_MAPPINGS.get(style, 'sng')
        }
        
        line_elem = self._create_ooxml_element('ln', line_attrs)
        
        if is_invisible:
            # Add noFill for invisible borders
            no_fill = self._create_ooxml_element('noFill')
            line_elem.append(no_fill)
        else:
            # Add solid fill with color
            solid_fill = self._create_ooxml_element('solidFill')
            color_elem = self._create_color_element(color)
            solid_fill.append(color_elem)
            line_elem.append(solid_fill)
        
        return self._element_to_string(line_elem)
    
    def _create_color_element(self, color: str) -> etree.Element:
        """Create OOXML color element with optional alpha"""
        hex_color = self._parse_color_to_hex(color)
        color_elem = self._create_ooxml_element('srgbClr', {'val': hex_color})
        
        # Add alpha if present
        alpha = self._parse_alpha_from_color(color)
        if alpha is not None:
            alpha_elem = self._create_ooxml_element('alpha', {'val': str(alpha)})
            color_elem.append(alpha_elem)
        
        return color_elem


class GradientTokenTransformer(BaseTokenTransformer):
    """Transform gradient tokens to OOXML gradFill elements"""
    
    # CSS gradient direction mappings to OOXML angles (degrees)
    DIRECTION_MAPPINGS = {
        'to right': 0,
        'to bottom right': 45,
        'to bottom': 90,
        'to bottom left': 135,
        'to left': 180,
        'to top left': 225,
        'to top': 270,
        'to top right': 315,
    }
    
    def transform(self, token: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Transform gradient token to OOXML gradFill element"""
        self._validate_token_structure(token, 'gradient')
        
        gradient_value = token['$value']
        required_props = ['type', 'stops']
        
        for prop in required_props:
            if prop not in gradient_value:
                raise CompositeTokenError(f"Gradient token missing required property: {prop}")
        
        gradient_type = gradient_value['type']
        direction = gradient_value.get('direction', 'to bottom')
        stops = gradient_value['stops']
        
        if not isinstance(stops, list) or len(stops) < 2:
            raise CompositeTokenError("Gradient must have at least 2 color stops")
        
        # Create gradFill element
        grad_fill = self._create_ooxml_element('gradFill', {'flip': 'none', 'rotWithShape': '1'})
        
        # Add gradient stop list
        gs_list = self._create_ooxml_element('gsLst')
        
        for stop in stops:
            if not isinstance(stop, dict) or 'position' not in stop or 'color' not in stop:
                raise CompositeTokenError("Invalid gradient stop format")
            
            position = self._parse_gradient_position(stop['position'])
            color = self._resolve_token_references(stop['color'], context)
            
            gs_elem = self._create_ooxml_element('gs', {'pos': str(position)})
            color_elem = self._create_color_element(color)
            gs_elem.append(color_elem)
            gs_list.append(gs_elem)
        
        grad_fill.append(gs_list)
        
        # Add gradient type-specific elements
        if gradient_type == 'linear':
            angle = self._parse_gradient_direction(direction)
            lin_elem = self._create_ooxml_element('lin', {
                'ang': str(angle * 60000),  # Convert to 60000ths of degree
                'scaled': '1'
            })
            grad_fill.append(lin_elem)
        elif gradient_type == 'radial':
            path_elem = self._create_ooxml_element('path', {'path': 'circle'})
            grad_fill.append(path_elem)
        else:
            raise CompositeTokenError(f"Unsupported gradient type: {gradient_type}")
        
        return self._element_to_string(grad_fill)
    
    def _parse_gradient_position(self, position: Union[str, float]) -> int:
        """Convert gradient position to OOXML format (0-100000)"""
        if isinstance(position, (int, float)):
            # Assume 0-1 range
            return int(position * 100000)
        
        if isinstance(position, str):
            position = position.strip()
            
            # Handle percentage
            if position.endswith('%'):
                percent = float(position[:-1])
                return int(percent * 1000)  # Convert to 0-100000
            
            # Handle decimal
            try:
                decimal = float(position)
                return int(decimal * 100000)
            except ValueError:
                pass
        
        raise CompositeTokenError(f"Invalid gradient position format: {position}")
    
    def _parse_gradient_direction(self, direction: str) -> int:
        """Parse gradient direction to angle in degrees"""
        direction = direction.strip().lower()
        
        # Check direct angle (e.g., "45deg", "90deg")
        angle_match = re.match(r'^(\d+)deg$', direction)
        if angle_match:
            return int(angle_match.group(1))
        
        # Check direction mappings
        if direction in self.DIRECTION_MAPPINGS:
            return self.DIRECTION_MAPPINGS[direction]
        
        raise CompositeTokenError(f"Unsupported gradient direction: {direction}")
    
    def _create_color_element(self, color: str) -> etree.Element:
        """Create OOXML color element with optional alpha"""
        hex_color = self._parse_color_to_hex(color)
        color_elem = self._create_ooxml_element('srgbClr', {'val': hex_color})
        
        # Add alpha if present  
        alpha = self._parse_alpha_from_color(color)
        if alpha is not None:
            alpha_elem = self._create_ooxml_element('alpha', {'val': str(alpha)})
            color_elem.append(alpha_elem)
        
        return color_elem


# Factory function for getting appropriate transformer
def get_composite_token_transformer(token_type: str) -> BaseTokenTransformer:
    """Get appropriate transformer for token type"""
    transformers = {
        'shadow': ShadowTokenTransformer,
        'border': BorderTokenTransformer, 
        'gradient': GradientTokenTransformer,
    }
    
    if token_type not in transformers:
        raise CompositeTokenError(f"Unsupported token type: {token_type}")
    
    return transformers[token_type]()


def transform_composite_token(token: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
    """Transform any composite token to OOXML"""
    if not isinstance(token, dict) or '$type' not in token:
        raise CompositeTokenError("Invalid token structure")
    
    token_type = token['$type']
    transformer = get_composite_token_transformer(token_type)
    
    return transformer.transform(token, context)