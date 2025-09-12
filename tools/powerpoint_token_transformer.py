"""
PowerPoint Token Transformer

This module provides transformation utilities for converting StyleStack design tokens
into PowerPoint-compatible OOXML formats, including colors, typography, and spacing
transformations with proper EMU precision.
"""

import re
import colorsys
from typing import Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass

from tools.core.types import ProcessingResult


@dataclass
class ColorTransformation:
    """Result of color token transformation"""
    hex_value: str
    rgb_values: Tuple[int, int, int]
    ooxml_srgb: str
    ooxml_rgb: str
    hsl_values: Tuple[float, float, float]


@dataclass
class TypographyTransformation:
    """Result of typography token transformation"""
    font_family: Optional[str]
    font_size_hundredths: Optional[int]  # PowerPoint uses hundredths of points
    font_weight: Optional[str]
    ooxml_font_ref: Optional[str]


@dataclass
class SpacingTransformation:
    """Result of spacing token transformation"""
    emu_value: int
    inch_value: float
    point_value: float
    ooxml_dimension: str


class PowerPointTokenTransformer:
    """Transforms design tokens into PowerPoint OOXML-compatible formats"""
    
    def __init__(self):
        # EMU conversion factors
        self.EMU_PER_INCH = 914400
        self.EMU_PER_POINT = 12700
        self.EMU_PER_CM = 360000
        self.EMU_PER_MM = 36000
        
        # PowerPoint font weight mappings
        self.font_weight_mapping = {
            "100": "thin",
            "200": "extraLight", 
            "300": "light",
            "400": "regular",
            "500": "medium",
            "600": "semiBold",
            "700": "bold",
            "800": "extraBold",
            "900": "black",
            "normal": "regular",
            "bold": "bold"
        }
        
        # PowerPoint color scheme positions
        self.color_scheme_positions = {
            "accent1": 0,
            "accent2": 1, 
            "accent3": 2,
            "accent4": 3,
            "accent5": 4,
            "accent6": 5,
            "hyperlink": 6,
            "followedHyperlink": 7,
            "background1": 8,
            "text1": 9,
            "background2": 10,
            "text2": 11
        }
    
    def transform_color_token(self, color_token: Dict[str, Any]) -> ProcessingResult:
        """Transform color design token to PowerPoint OOXML format"""
        try:
            if not isinstance(color_token, dict) or "$value" not in color_token:
                return ProcessingResult(
                    success=False,
                    errors=["Invalid color token structure"]
                )
            
            color_value = color_token["$value"]
            
            # Handle different color formats
            if isinstance(color_value, str):
                if color_value.startswith("#"):
                    return self._transform_hex_color(color_value)
                elif color_value.startswith("rgb("):
                    return self._transform_rgb_color(color_value)
                elif color_value.startswith("hsl("):
                    return self._transform_hsl_color(color_value)
                else:
                    # Try to resolve as color reference
                    return self._transform_color_reference(color_value)
            
            return ProcessingResult(
                success=False,
                errors=[f"Unsupported color format: {color_value}"]
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                errors=[f"Color transformation error: {str(e)}"]
            )
    
    def _transform_hex_color(self, hex_color: str) -> ProcessingResult:
        """Transform hex color to PowerPoint format"""
        # Remove # and validate
        hex_clean = hex_color.lstrip('#')
        if len(hex_clean) != 6:
            return ProcessingResult(
                success=False,
                errors=[f"Invalid hex color format: {hex_color}"]
            )
        
        try:
            # Convert to RGB values
            r = int(hex_clean[0:2], 16)
            g = int(hex_clean[2:4], 16) 
            b = int(hex_clean[4:6], 16)
            
            # Convert to HSL for additional formats
            h, l, s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)
            
            # Create transformation result
            transformation = ColorTransformation(
                hex_value=hex_color.upper(),
                rgb_values=(r, g, b),
                ooxml_srgb=f'<a:srgbClr val="{hex_clean.upper()}"/>',
                ooxml_rgb=f'<a:scrgbClr r="{r*256}" g="{g*256}" b="{b*256}"/>',
                hsl_values=(h*360, s*100, l*100)
            )
            
            return ProcessingResult(
                success=True,
                data=transformation
            )
            
        except ValueError as e:
            return ProcessingResult(
                success=False,
                errors=[f"Invalid hex color value: {hex_color}"]
            )
    
    def _transform_rgb_color(self, rgb_color: str) -> ProcessingResult:
        """Transform rgb() color to PowerPoint format"""
        # Extract RGB values using regex
        rgb_match = re.match(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', rgb_color)
        if not rgb_match:
            return ProcessingResult(
                success=False,
                errors=[f"Invalid RGB color format: {rgb_color}"]
            )
        
        r, g, b = map(int, rgb_match.groups())
        
        # Convert to hex and use hex transformer
        hex_color = f"#{r:02X}{g:02X}{b:02X}"
        return self._transform_hex_color(hex_color)
    
    def _transform_hsl_color(self, hsl_color: str) -> ProcessingResult:
        """Transform hsl() color to PowerPoint format"""
        # Extract HSL values using regex
        hsl_match = re.match(r'hsl\(\s*(\d+)\s*,\s*(\d+)%\s*,\s*(\d+)%\s*\)', hsl_color)
        if not hsl_match:
            return ProcessingResult(
                success=False,
                errors=[f"Invalid HSL color format: {hsl_color}"]
            )
        
        h, s, l = map(int, hsl_match.groups())
        
        # Convert HSL to RGB
        r, g, b = colorsys.hls_to_rgb(h/360.0, l/100.0, s/100.0)
        r, g, b = int(r*255), int(g*255), int(b*255)
        
        # Convert to hex and use hex transformer
        hex_color = f"#{r:02X}{g:02X}{b:02X}"
        return self._transform_hex_color(hex_color)
    
    def _transform_color_reference(self, color_ref: str) -> ProcessingResult:
        """Transform color reference token (placeholder for now)"""
        # This would integrate with token resolution system
        return ProcessingResult(
            success=False,
            errors=[f"Color reference resolution not implemented: {color_ref}"],
            warnings=["Color references require token resolution system integration"]
        )
    
    def transform_typography_token(self, typography_token: Dict[str, Any]) -> ProcessingResult:
        """Transform typography design token to PowerPoint OOXML format"""
        try:
            transformation = TypographyTransformation(
                font_family=None,
                font_size_hundredths=None,
                font_weight=None,
                ooxml_font_ref=None
            )
            
            # Handle different typography properties
            if isinstance(typography_token, dict):
                # Font family
                if "family" in typography_token:
                    family_result = self._transform_font_family(typography_token["family"])
                    if family_result.success:
                        transformation.font_family = family_result.data
                
                # Font size
                if "size" in typography_token:
                    size_result = self._transform_font_size(typography_token["size"])
                    if size_result.success:
                        transformation.font_size_hundredths = size_result.data
                
                # Font weight
                if "weight" in typography_token:
                    weight_result = self._transform_font_weight(typography_token["weight"])
                    if weight_result.success:
                        transformation.font_weight = weight_result.data
                
                # Generate OOXML font reference
                transformation.ooxml_font_ref = self._generate_ooxml_font_reference(transformation)
            
            elif isinstance(typography_token, str):
                # Handle single value (could be size, family, etc.)
                if typography_token.endswith("pt") or typography_token.endswith("px"):
                    size_result = self._transform_font_size(typography_token)
                    if size_result.success:
                        transformation.font_size_hundredths = size_result.data
                else:
                    transformation.font_family = typography_token
            
            return ProcessingResult(
                success=True,
                data=transformation
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                errors=[f"Typography transformation error: {str(e)}"]
            )
    
    def _transform_font_family(self, family_token: Union[str, Dict[str, Any]]) -> ProcessingResult:
        """Transform font family token"""
        if isinstance(family_token, dict) and "$value" in family_token:
            return ProcessingResult(success=True, data=family_token["$value"])
        elif isinstance(family_token, str):
            return ProcessingResult(success=True, data=family_token)
        else:
            return ProcessingResult(success=False, errors=["Invalid font family token"])
    
    def _transform_font_size(self, size_token: Union[str, Dict[str, Any]]) -> ProcessingResult:
        """Transform font size to PowerPoint hundredths of points"""
        try:
            # Extract size value
            if isinstance(size_token, dict) and "$value" in size_token:
                size_value = size_token["$value"]
            elif isinstance(size_token, str):
                size_value = size_token
            else:
                return ProcessingResult(success=False, errors=["Invalid font size token"])
            
            # Parse size value
            if size_value.endswith("pt"):
                points = float(size_value[:-2])
                hundredths = int(points * 100)
                return ProcessingResult(success=True, data=hundredths)
            elif size_value.endswith("px"):
                # Convert pixels to points (assuming 96 DPI)
                pixels = float(size_value[:-2])
                points = pixels * 0.75  # 96 DPI to points conversion
                hundredths = int(points * 100)
                return ProcessingResult(success=True, data=hundredths)
            elif size_value.replace(".", "").isdigit():
                # Assume points if no unit
                points = float(size_value)
                hundredths = int(points * 100)
                return ProcessingResult(success=True, data=hundredths)
            else:
                return ProcessingResult(success=False, errors=[f"Unsupported font size format: {size_value}"])
                
        except (ValueError, TypeError) as e:
            return ProcessingResult(success=False, errors=[f"Font size parsing error: {str(e)}"])
    
    def _transform_font_weight(self, weight_token: Union[str, Dict[str, Any]]) -> ProcessingResult:
        """Transform font weight to PowerPoint format"""
        if isinstance(weight_token, dict) and "$value" in weight_token:
            weight_value = weight_token["$value"]
        elif isinstance(weight_token, str):
            weight_value = weight_token
        else:
            return ProcessingResult(success=False, errors=["Invalid font weight token"])
        
        # Map to PowerPoint weight
        weight_value_str = str(weight_value).lower()
        if weight_value_str in self.font_weight_mapping:
            return ProcessingResult(success=True, data=self.font_weight_mapping[weight_value_str])
        else:
            return ProcessingResult(success=False, errors=[f"Unsupported font weight: {weight_value}"])
    
    def _generate_ooxml_font_reference(self, typography: TypographyTransformation) -> str:
        """Generate OOXML font reference"""
        ooxml_parts = []
        
        if typography.font_size_hundredths:
            ooxml_parts.append(f'sz="{typography.font_size_hundredths}"')
        
        if typography.font_weight and typography.font_weight != "regular":
            ooxml_parts.append(f'b="1"' if typography.font_weight in ["bold", "semiBold", "extraBold", "black"] else 'b="0"')
        
        attributes = " ".join(ooxml_parts)
        
        ooxml = f'<a:rPr {attributes}>'
        if typography.font_family:
            ooxml += f'<a:latin typeface="{typography.font_family}"/>'
        ooxml += '</a:rPr>'
        
        return ooxml
    
    def transform_spacing_token(self, spacing_token: Dict[str, Any]) -> ProcessingResult:
        """Transform spacing design token to EMU values"""
        try:
            if not isinstance(spacing_token, dict) or "$value" not in spacing_token:
                return ProcessingResult(
                    success=False,
                    errors=["Invalid spacing token structure"]
                )
            
            spacing_value = spacing_token["$value"]
            
            # Handle different dimension formats
            if isinstance(spacing_value, str):
                return self._transform_dimension_string(spacing_value)
            elif isinstance(spacing_value, (int, float)):
                # Assume points if no unit specified
                return self._transform_dimension_string(f"{spacing_value}pt")
            else:
                return ProcessingResult(
                    success=False,
                    errors=[f"Unsupported spacing format: {spacing_value}"]
                )
                
        except Exception as e:
            return ProcessingResult(
                success=False,
                errors=[f"Spacing transformation error: {str(e)}"]
            )
    
    def _transform_dimension_string(self, dimension: str) -> ProcessingResult:
        """Transform dimension string to EMU values"""
        try:
            # Parse dimension
            if dimension.endswith("in"):
                value = float(dimension[:-2])
                emu_value = int(value * self.EMU_PER_INCH)
                inch_value = value
                point_value = value * 72
            elif dimension.endswith("pt"):
                value = float(dimension[:-2]) 
                emu_value = int(value * self.EMU_PER_POINT)
                inch_value = value / 72
                point_value = value
            elif dimension.endswith("cm"):
                value = float(dimension[:-2])
                emu_value = int(value * self.EMU_PER_CM)
                inch_value = value / 2.54
                point_value = value * 28.35  # Approximate
            elif dimension.endswith("mm"):
                value = float(dimension[:-2])
                emu_value = int(value * self.EMU_PER_MM)
                inch_value = value / 25.4
                point_value = value * 2.835  # Approximate
            elif dimension.replace(".", "").isdigit():
                # Assume points if no unit
                value = float(dimension)
                emu_value = int(value * self.EMU_PER_POINT)
                inch_value = value / 72
                point_value = value
            else:
                return ProcessingResult(
                    success=False,
                    errors=[f"Unsupported dimension format: {dimension}"]
                )
            
            transformation = SpacingTransformation(
                emu_value=emu_value,
                inch_value=inch_value,
                point_value=point_value,
                ooxml_dimension=str(emu_value)
            )
            
            return ProcessingResult(
                success=True,
                data=transformation
            )
            
        except (ValueError, TypeError) as e:
            return ProcessingResult(
                success=False,
                errors=[f"Dimension parsing error: {str(e)}"]
            )
    
    def create_theme_color_reference(self, color_position: str) -> ProcessingResult:
        """Create PowerPoint theme color reference"""
        try:
            if color_position in self.color_scheme_positions:
                position_id = self.color_scheme_positions[color_position]
                ooxml_ref = f'<a:schemeClr val="{color_position}"/>'
                
                return ProcessingResult(
                    success=True,
                    data={
                        "position": color_position,
                        "position_id": position_id,
                        "ooxml_reference": ooxml_ref
                    }
                )
            else:
                return ProcessingResult(
                    success=False,
                    errors=[f"Unknown color scheme position: {color_position}"]
                )
                
        except Exception as e:
            return ProcessingResult(
                success=False,
                errors=[f"Theme color reference error: {str(e)}"]
            )
    
    def transform_tokens_for_layout(self, layout_tokens: Dict[str, Any]) -> ProcessingResult:
        """Transform all design tokens for a PowerPoint layout"""
        try:
            transformed_tokens = {
                "colors": {},
                "typography": {},
                "spacing": {},
                "ooxml_elements": []
            }
            
            errors = []
            warnings = []
            
            # Transform colors
            if "colors" in layout_tokens:
                for color_name, color_token in layout_tokens["colors"].items():
                    result = self.transform_color_token(color_token)
                    if result.success:
                        transformed_tokens["colors"][color_name] = result.data
                    else:
                        errors.extend(result.errors or [])
                        warnings.extend(result.warnings or [])
            
            # Transform typography
            if "typography" in layout_tokens:
                for typo_name, typo_token in layout_tokens["typography"].items():
                    result = self.transform_typography_token(typo_token)
                    if result.success:
                        transformed_tokens["typography"][typo_name] = result.data
                    else:
                        errors.extend(result.errors or [])
                        warnings.extend(result.warnings or [])
            
            # Transform spacing
            if "spacing" in layout_tokens:
                for spacing_name, spacing_token in layout_tokens["spacing"].items():
                    result = self.transform_spacing_token(spacing_token)
                    if result.success:
                        transformed_tokens["spacing"][spacing_name] = result.data
                    else:
                        errors.extend(result.errors or [])
                        warnings.extend(result.warnings or [])
            
            return ProcessingResult(
                success=len(errors) == 0,
                data=transformed_tokens,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                errors=[f"Layout token transformation error: {str(e)}"]
            )


def create_powerpoint_token_transformer() -> PowerPointTokenTransformer:
    """Factory function to create PowerPoint token transformer"""
    return PowerPointTokenTransformer()


if __name__ == '__main__':
    # Demo usage
    print("🎨 PowerPoint Token Transformer Demo")
    
    transformer = PowerPointTokenTransformer()
    
    # Test color transformation
    print(f"\n🎯 Color Transformation:")
    color_token = {"$type": "color", "$value": "#0066CC"}
    color_result = transformer.transform_color_token(color_token)
    if color_result.success:
        color_data = color_result.data
        print(f"   Hex: {color_data.hex_value}")
        print(f"   RGB: {color_data.rgb_values}")
        print(f"   OOXML: {color_data.ooxml_srgb}")
    
    # Test typography transformation
    print(f"\n✏️  Typography Transformation:")
    typography_token = {
        "family": {"$type": "fontFamily", "$value": "Arial"},
        "size": {"$type": "dimension", "$value": "44pt"},
        "weight": {"$type": "fontWeight", "$value": "bold"}
    }
    typography_result = transformer.transform_typography_token(typography_token)
    if typography_result.success:
        typo_data = typography_result.data
        print(f"   Family: {typo_data.font_family}")
        print(f"   Size (hundredths): {typo_data.font_size_hundredths}")
        print(f"   Weight: {typo_data.font_weight}")
        print(f"   OOXML: {typo_data.ooxml_font_ref}")
    
    # Test spacing transformation
    print(f"\n📏 Spacing Transformation:")
    spacing_token = {"$type": "dimension", "$value": "0.75in"}
    spacing_result = transformer.transform_spacing_token(spacing_token)
    if spacing_result.success:
        spacing_data = spacing_result.data
        print(f"   EMU: {spacing_data.emu_value:,}")
        print(f"   Inches: {spacing_data.inch_value}")
        print(f"   Points: {spacing_data.point_value}")
    
    # Test complete layout transformation
    print(f"\n🏗️  Complete Layout Transformation:")
    layout_tokens = {
        "colors": {
            "primary": {"$type": "color", "$value": "#0066CC"},
            "text": {"$type": "color", "$value": "#000000"}
        },
        "typography": {
            "title": {
                "family": {"$type": "fontFamily", "$value": "Arial Bold"},
                "size": {"$type": "dimension", "$value": "44pt"}
            }
        },
        "spacing": {
            "margin": {"$type": "dimension", "$value": "0.5in"}
        }
    }
    
    layout_result = transformer.transform_tokens_for_layout(layout_tokens)
    if layout_result.success:
        print(f"   ✅ Transformed {len(layout_result.data['colors'])} colors")
        print(f"   ✅ Transformed {len(layout_result.data['typography'])} typography tokens") 
        print(f"   ✅ Transformed {len(layout_result.data['spacing'])} spacing tokens")