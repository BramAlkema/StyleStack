"""
PowerPoint Positioning Calculator

This module provides responsive positioning calculations for PowerPoint layouts
using design token variables that resolve to precise EMU coordinates based on
aspect ratios and slide dimensions.
"""

import re
import json
from typing import Dict, Any, Union, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from tools.variable_resolver import VariableResolver
from tools.core.types import ProcessingResult


@dataclass
class AspectRatioMultiplier:
    """Aspect ratio multiplier for responsive positioning calculations"""
    
    def __init__(self, aspect_ratio: str):
        self.aspect_ratio = aspect_ratio
        self.width_multiplier = 1.0
        self.height_multiplier = 1.0
        
        # Standard PowerPoint slide dimensions in EMU
        if aspect_ratio == '16:9':
            self.slide_width_emu = 9144000   # Standard widescreen width
            self.slide_height_emu = 5143500  # Standard widescreen height
            self.width_multiplier = 1.0
            self.height_multiplier = 1.0
        elif aspect_ratio == '4:3':
            self.slide_width_emu = 9144000   # Same width as 16:9
            self.slide_height_emu = 6858000  # Taller height for 4:3
            self.width_multiplier = 1.0
            self.height_multiplier = 1.333   # 6858000 / 5143500
        elif aspect_ratio == '16:10':
            self.slide_width_emu = 9144000   # Same width as 16:9
            self.slide_height_emu = 5715000  # Intermediate height
            self.width_multiplier = 1.0
            self.height_multiplier = 1.111   # 5715000 / 5143500
        else:
            raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}")


@dataclass
class ParameterizedPosition:
    """Represents a position with design token variables"""
    
    def __init__(self, x: str, y: str, width: str, height: str):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def get_design_token_variables(self) -> List[str]:
        """Extract design token variables from position values"""
        variables = []
        pattern = r'\${[^}]+}'
        
        for value in [self.x, self.y, self.width, self.height]:
            matches = re.findall(pattern, value)
            variables.extend(matches)
        
        return list(set(variables))  # Remove duplicates
    
    def has_variables(self) -> bool:
        """Check if position contains design token variables"""
        return len(self.get_design_token_variables()) > 0


class EMUCalculator:
    """Utility class for EMU (English Metric Unit) calculations"""
    
    # Conversion constants
    EMU_PER_POINT = 12700
    EMU_PER_INCH = 914400
    POINTS_PER_INCH = 72
    
    @staticmethod
    def emu_to_points(emu_value: int) -> float:
        """Convert EMU to points"""
        return emu_value / EMUCalculator.EMU_PER_POINT
    
    @staticmethod
    def points_to_emu(points: float) -> int:
        """Convert points to EMU"""
        return int(points * EMUCalculator.EMU_PER_POINT)
    
    @staticmethod
    def percentage_to_emu_width(percentage: float, aspect_ratio: str) -> int:
        """Convert percentage to EMU width based on slide dimensions"""
        multiplier = AspectRatioMultiplier(aspect_ratio)
        return int(multiplier.slide_width_emu * percentage / 100.0)
    
    @staticmethod
    def percentage_to_emu_height(percentage: float, aspect_ratio: str) -> int:
        """Convert percentage to EMU height based on slide dimensions"""
        multiplier = AspectRatioMultiplier(aspect_ratio)
        return int(multiplier.slide_height_emu * percentage / 100.0)
    
    @staticmethod
    def inches_to_emu(inches: float) -> int:
        """Convert inches to EMU"""
        return int(inches * EMUCalculator.EMU_PER_INCH)


class DesignTokenResolver:
    """Resolves design token variables to actual values"""
    
    def __init__(self, aspect_ratio: str = '16:9'):
        self.aspect_ratio = aspect_ratio
        self.multiplier = AspectRatioMultiplier(aspect_ratio)
        self.variable_resolver = VariableResolver()
        
        # Base design token values that can be referenced
        self.base_tokens = {
            'slide': {
                'width': self.multiplier.slide_width_emu,
                'height': self.multiplier.slide_height_emu
            },
            'margins': {
                'left': int(self.multiplier.slide_width_emu * 0.083),      # ~758K EMU
                'right': int(self.multiplier.slide_width_emu * 0.083),     # ~758K EMU
                'top': int(self.multiplier.slide_height_emu * 0.071),      # ~365K EMU for 16:9
                'bottom': int(self.multiplier.slide_height_emu * 0.071)    # ~365K EMU for 16:9
            },
            'gutters': {
                'horizontal': int(self.multiplier.slide_width_emu * 0.022),  # ~201K EMU
                'vertical': int(self.multiplier.slide_height_emu * 0.039)    # ~201K EMU for 16:9
            },
            'typography': {
                'title': {'size': '4400', 'size_large': '6000'},
                'subtitle': {'size': '2400'},
                'body': {'size': '1800'},
                'section_header': {'size': '6000'},
                'section_subtitle': {'size': '2400'},
                'comparison_header': {'size': '2000'},
                'caption': {'size': '1600'},
                'overlay_title': {'size': '4400'},
                'footer': {'size': '1200'}
            }
        }
        
        # Calculate content areas based on margins and gutters
        margin_width = self.base_tokens['margins']['left'] + self.base_tokens['margins']['right']
        gutter_horizontal = self.base_tokens['gutters']['horizontal']
        
        self.base_tokens['content_areas'] = {
            'full_width': self.multiplier.slide_width_emu - margin_width,
            'half_width': int((self.multiplier.slide_width_emu - margin_width - gutter_horizontal) / 2),
            'quarter_width': int((self.multiplier.slide_width_emu - margin_width - gutter_horizontal * 3) / 4)
        }
    
    def resolve_token_value(self, token: str) -> int:
        """Resolve a single design token to its EMU value"""
        if not token.startswith('${') or not token.endswith('}'):
            # Not a token, try to parse as integer
            try:
                return int(token)
            except ValueError:
                raise ValueError(f"Invalid token or numeric value: {token}")
        
        # Extract token path (remove ${ and })
        token_path = token[2:-1]
        
        # Handle mathematical expressions
        if any(op in token_path for op in ['+', '-', '*', '/', '%']):
            return self._evaluate_expression(token_path)
        
        # Navigate nested token structure
        try:
            return self._get_nested_value(self.base_tokens, token_path.split('.'))
        except (KeyError, TypeError) as e:
            # Fallback to variable resolver for custom tokens
            try:
                result = self.variable_resolver.resolve(token)
                return int(result) if isinstance(result, (str, int)) else 0
            except Exception:
                raise ValueError(f"Unable to resolve token: {token}") from e
    
    def _get_nested_value(self, data: Dict[str, Any], path: List[str]) -> int:
        """Navigate nested dictionary structure"""
        current = data
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                raise KeyError(f"Token path not found: {'.'.join(path)}")
        
        if isinstance(current, (int, float)):
            return int(current)
        elif isinstance(current, str):
            try:
                return int(current)
            except ValueError:
                raise ValueError(f"Token value is not numeric: {current}")
        else:
            raise TypeError(f"Token value is not numeric: {current}")
    
    def _evaluate_expression(self, expression: str) -> int:
        """Safely evaluate mathematical expressions in design tokens"""
        # Replace token references with their values
        pattern = r'\b([a-zA-Z_][a-zA-Z0-9_.]*)\b'
        
        def replace_token(match):
            token_path = match.group(1)
            try:
                value = self._get_nested_value(self.base_tokens, token_path.split('.'))
                return str(value)
            except (KeyError, TypeError):
                return match.group(0)  # Leave unchanged if not found
        
        # Replace tokens with values
        resolved_expression = re.sub(pattern, replace_token, expression)
        
        # Safely evaluate the mathematical expression
        try:
            # Only allow safe mathematical operations
            allowed_chars = set('0123456789+-*/%(). ')
            if not all(c in allowed_chars for c in resolved_expression):
                raise ValueError(f"Unsafe expression: {resolved_expression}")
            
            result = eval(resolved_expression)
            return int(result)
        except Exception as e:
            raise ValueError(f"Error evaluating expression '{expression}': {e}")


class PositioningCalculator:
    """Main positioning calculator for PowerPoint layouts"""
    
    def __init__(self, aspect_ratio: str = '16:9'):
        self.aspect_ratio = aspect_ratio
        self.multiplier = AspectRatioMultiplier(aspect_ratio)
        self.token_resolver = DesignTokenResolver(aspect_ratio)
    
    def resolve_position_token(self, token: str) -> int:
        """Resolve a single position token to EMU value"""
        return self.token_resolver.resolve_token_value(token)
    
    def resolve_parameterized_position(self, position: ParameterizedPosition) -> Dict[str, int]:
        """Resolve a parameterized position to actual EMU coordinates"""
        return {
            'x': self.resolve_position_token(position.x),
            'y': self.resolve_position_token(position.y),
            'width': self.resolve_position_token(position.width),
            'height': self.resolve_position_token(position.height)
        }
    
    def calculate_responsive_position(self, base_position: Dict[str, int]) -> Dict[str, int]:
        """Calculate responsive position based on aspect ratio multipliers"""
        return {
            'x': base_position['x'],  # X coordinates typically don't change
            'y': int(base_position['y'] * self.multiplier.height_multiplier),
            'width': base_position['width'],  # Width typically doesn't change
            'height': int(base_position['height'] * self.multiplier.height_multiplier)
        }
    
    def resolve_parameterized_layout(self, layout_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve complete parameterized layout to EMU values"""
        resolved_layout = layout_data.copy()
        
        if 'placeholders' in resolved_layout:
            resolved_placeholders = []
            
            for placeholder in resolved_layout['placeholders']:
                resolved_placeholder = placeholder.copy()
                
                if 'position' in placeholder:
                    position = ParameterizedPosition(
                        x=placeholder['position']['x'],
                        y=placeholder['position']['y'],
                        width=placeholder['position']['width'],
                        height=placeholder['position']['height']
                    )
                    
                    resolved_position = self.resolve_parameterized_position(position)
                    resolved_placeholder['position'] = resolved_position
                
                resolved_placeholders.append(resolved_placeholder)
            
            resolved_layout['placeholders'] = resolved_placeholders
        
        return resolved_layout
    
    def get_slide_dimensions(self) -> Tuple[int, int]:
        """Get slide dimensions for current aspect ratio"""
        return (self.multiplier.slide_width_emu, self.multiplier.slide_height_emu)
    
    def validate_position_bounds(self, position: Dict[str, int]) -> ProcessingResult:
        """Validate that position is within slide bounds"""
        slide_width, slide_height = self.get_slide_dimensions()
        
        errors = []
        warnings = []
        
        # Check bounds
        if position['x'] < 0:
            errors.append(f"X position {position['x']} is negative")
        if position['y'] < 0:
            errors.append(f"Y position {position['y']} is negative")
        if position['x'] + position['width'] > slide_width:
            errors.append(f"Position extends beyond slide width: {position['x'] + position['width']} > {slide_width}")
        if position['y'] + position['height'] > slide_height:
            errors.append(f"Position extends beyond slide height: {position['y'] + position['height']} > {slide_height}")
        
        # Check for very small dimensions
        if position['width'] < 10000:  # Less than ~0.01 inches
            warnings.append(f"Width {position['width']} may be too small")
        if position['height'] < 10000:  # Less than ~0.01 inches
            warnings.append(f"Height {position['height']} may be too small")
        
        return ProcessingResult(
            success=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            data={'validated_position': position}
        )


def create_positioning_calculator(aspect_ratio: str = '16:9') -> PositioningCalculator:
    """Factory function to create positioning calculator"""
    return PositioningCalculator(aspect_ratio)


def load_layout_definitions(layout_file: Optional[str] = None) -> Dict[str, Any]:
    """Load layout definitions from JSON file"""
    if layout_file is None:
        # Default to the layout file we created
        layout_file = Path(__file__).parent.parent / 'data' / 'powerpoint-layouts.json'
    
    with open(layout_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_layout_by_id(layout_id: str, aspect_ratio: str = '16:9') -> Optional[Dict[str, Any]]:
    """Get resolved layout by ID with EMU positioning"""
    layout_definitions = load_layout_definitions()
    calculator = PositioningCalculator(aspect_ratio)
    
    for layout in layout_definitions['layouts']:
        if layout['id'] == layout_id:
            return calculator.resolve_parameterized_layout(layout)
    
    return None


if __name__ == '__main__':
    # Demo usage
    print("🔧 PowerPoint Positioning Calculator Demo")
    
    # Test different aspect ratios
    for aspect_ratio in ['16:9', '4:3', '16:10']:
        print(f"\n📐 Testing {aspect_ratio} aspect ratio:")
        
        calculator = PositioningCalculator(aspect_ratio)
        width, height = calculator.get_slide_dimensions()
        print(f"   Slide dimensions: {width:,} x {height:,} EMU")
        
        # Test token resolution
        margin_left = calculator.resolve_position_token('${margins.left}')
        content_width = calculator.resolve_position_token('${content_areas.full_width}')
        print(f"   Margin left: {margin_left:,} EMU")
        print(f"   Content width: {content_width:,} EMU")
    
    # Test layout resolution
    print(f"\n🎨 Testing layout resolution:")
    title_layout = get_layout_by_id('title_slide', '16:9')
    if title_layout:
        print(f"   Title Slide layout resolved with {len(title_layout['placeholders'])} placeholders")
        for placeholder in title_layout['placeholders']:
            pos = placeholder['position']
            print(f"   - {placeholder['name']}: {pos['x']:,} x {pos['y']:,} ({pos['width']:,} x {pos['height']:,})")