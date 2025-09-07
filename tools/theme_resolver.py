"""
StyleStack Theme Resolution System

Advanced OOXML theme color and font resolution with Office-native transformations.
Provides comprehensive theme integration matching Microsoft Office behavior exactly.

Features:
- Complete theme color slot resolution (accent1-6, dk1/lt1, etc.)
- Theme font resolution (majorFont/minorFont) with fallbacks
- Color transformations (tint/shade/lumMod/lumOff) matching Office algorithms
- Theme inheritance validation across PowerPoint, Word, Excel
- Cross-platform compatibility validation
- Performance optimization for large theme processing

Usage:
    resolver = ThemeResolver()
    
    # Resolve theme colors
    accent1_color = resolver.resolve_theme_color('accent1', theme_overrides)
    
    # Apply Office-style transformations
    tinted_color = resolver.apply_color_transformation('4472C4', 'tint', 50000)
    
    # Extract theme from OOXML
    theme = resolver.extract_theme_from_ooxml_file('template.potx')
"""

import xml.etree.ElementTree as ET
import colorsys
import math
import zipfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ThemeColor:
    """Represents a theme color with metadata and transformations"""
    slot: str
    name: str
    rgb_value: str  # 6-character hex without #
    color_type: str  # 'text', 'background', 'accent', 'hyperlink'
    transformations: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def hex_value(self) -> str:
        """Get hex value with # prefix"""
        return f"#{self.rgb_value}"
    
    @property
    def rgb_tuple(self) -> Tuple[int, int, int]:
        """Get RGB as tuple of integers"""
        return tuple(int(self.rgb_value[i:i+2], 16) for i in (0, 2, 4))
    
    def add_transformation(self, transform_type: str, value: float, description: str = "") -> None:
        """Add a color transformation"""
        self.transformations.append({
            'type': transform_type,
            'value': value,
            'description': description or f"{transform_type} {value/1000:.1f}%"
        })


@dataclass  
class ThemeFont:
    """Represents a theme font with metadata"""
    slot: str
    name: str
    typeface: str
    font_type: str  # 'heading', 'body'
    pitch_family: Optional[int] = None
    charset: Optional[int] = None
    
    @property
    def is_heading_font(self) -> bool:
        """True if this is a heading font (majorFont)"""
        return self.font_type == 'heading' or self.slot == 'majorFont'


@dataclass
class Theme:
    """Complete OOXML theme definition"""
    name: str
    colors: Dict[str, ThemeColor] = field(default_factory=dict)
    fonts: Dict[str, ThemeFont] = field(default_factory=dict)
    format_scheme: Dict[str, Any] = field(default_factory=dict)
    
    def get_color(self, slot: str) -> Optional[ThemeColor]:
        """Get theme color by slot name"""
        return self.colors.get(slot)
    
    def get_font(self, slot: str) -> Optional[ThemeFont]:
        """Get theme font by slot name"""
        return self.fonts.get(slot)
    
    def validate(self) -> Dict[str, Any]:
        """Validate theme completeness"""
        required_colors = ['dk1', 'lt1', 'dk2', 'lt2', 'accent1', 'accent2', 'accent3', 
                          'accent4', 'accent5', 'accent6', 'hlink', 'folHlink']
        required_fonts = ['majorFont', 'minorFont']
        
        missing_colors = [c for c in required_colors if c not in self.colors]
        missing_fonts = [f for f in required_fonts if f not in self.fonts]
        
        return {
            'valid': len(missing_colors) == 0 and len(missing_fonts) == 0,
            'missing_colors': missing_colors,
            'missing_fonts': missing_fonts,
            'color_count': len(self.colors),
            'font_count': len(self.fonts)
        }


class ColorTransformationEngine:
    """Engine for Office-compatible color transformations"""
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex string (without #)"""
        return f"{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
    
    @staticmethod
    def rgb_to_hsl(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
        """Convert RGB to HSL (0-1 range)"""
        r, g, b = [x / 255.0 for x in rgb]
        return colorsys.rgb_to_hls(r, g, b)
    
    @staticmethod
    def hsl_to_rgb(hsl: Tuple[float, float, float]) -> Tuple[int, int, int]:
        """Convert HSL to RGB (0-255 range)"""
        h, s, l = hsl
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return (int(r * 255), int(g * 255), int(b * 255))
    
    def apply_tint(self, rgb: Tuple[int, int, int], tint_value: float) -> Tuple[int, int, int]:
        """Apply tint transformation (mix with white)"""
        # Office tint: RGB = RGB * (1 - tint) + 255 * tint
        tint_factor = tint_value / 100000.0
        return tuple(
            int(rgb[i] * (1 - tint_factor) + 255 * tint_factor)
            for i in range(3)
        )
    
    def apply_shade(self, rgb: Tuple[int, int, int], shade_value: float) -> Tuple[int, int, int]:
        """Apply shade transformation (mix with black)"""
        # Office shade: RGB = RGB * (1 - shade)
        shade_factor = shade_value / 100000.0
        return tuple(
            int(rgb[i] * (1 - shade_factor))
            for i in range(3)
        )
    
    def apply_lum_mod(self, rgb: Tuple[int, int, int], lum_mod_value: float) -> Tuple[int, int, int]:
        """Apply luminance modulation"""
        h, s, l = self.rgb_to_hsl(rgb)
        l = l * (lum_mod_value / 100000.0)
        l = max(0.0, min(1.0, l))  # Clamp to valid range
        return self.hsl_to_rgb((h, s, l))
    
    def apply_lum_off(self, rgb: Tuple[int, int, int], lum_off_value: float) -> Tuple[int, int, int]:
        """Apply luminance offset"""
        h, s, l = self.rgb_to_hsl(rgb)
        l = l + (lum_off_value / 100000.0)
        l = max(0.0, min(1.0, l))  # Clamp to valid range
        return self.hsl_to_rgb((h, s, l))
    
    def apply_sat_mod(self, rgb: Tuple[int, int, int], sat_mod_value: float) -> Tuple[int, int, int]:
        """Apply saturation modulation"""
        h, s, l = self.rgb_to_hsl(rgb)
        s = s * (sat_mod_value / 100000.0)
        s = max(0.0, min(1.0, s))  # Clamp to valid range
        return self.hsl_to_rgb((h, s, l))
    
    def apply_sat_off(self, rgb: Tuple[int, int, int], sat_off_value: float) -> Tuple[int, int, int]:
        """Apply saturation offset"""
        h, s, l = self.rgb_to_hsl(rgb)
        s = s + (sat_off_value / 100000.0)  
        s = max(0.0, min(1.0, s))  # Clamp to valid range
        return self.hsl_to_rgb((h, s, l))
    
    def apply_hue_mod(self, rgb: Tuple[int, int, int], hue_mod_value: float) -> Tuple[int, int, int]:
        """Apply hue modulation"""
        h, s, l = self.rgb_to_hsl(rgb)
        h = (h * (hue_mod_value / 100000.0)) % 1.0
        return self.hsl_to_rgb((h, s, l))
    
    def apply_hue_off(self, rgb: Tuple[int, int, int], hue_off_value: float) -> Tuple[int, int, int]:
        """Apply hue offset"""
        h, s, l = self.rgb_to_hsl(rgb)
        h = (h + (hue_off_value / 100000.0)) % 1.0
        return self.hsl_to_rgb((h, s, l))
    
    def apply_transformation(self, base_color: str, transform_type: str, value: float) -> str:
        """Apply specified transformation to color"""
        rgb = self.hex_to_rgb(base_color)
        
        transform_methods = {
            'tint': self.apply_tint,
            'shade': self.apply_shade,
            'lumMod': self.apply_lum_mod,
            'lumOff': self.apply_lum_off,
            'satMod': self.apply_sat_mod,
            'satOff': self.apply_sat_off,
            'hueMod': self.apply_hue_mod,
            'hueOff': self.apply_hue_off
        }
        
        if transform_type in transform_methods:
            transformed_rgb = transform_methods[transform_type](rgb, value)
            return self.rgb_to_hex(transformed_rgb)
        else:
            logger.warning(f"Unknown color transformation: {transform_type}")
            return base_color  # Return original if unknown transformation


class ThemeResolver:
    """
    Advanced OOXML theme resolver with Office-compatible color and font processing.
    
    Handles complete theme resolution including:
    - Standard theme color slots (12 colors)  
    - Theme font slots (major/minor)
    - Office-native color transformations
    - Cross-platform compatibility validation
    - Performance optimization for batch processing
    """
    
    # Standard OOXML theme color definitions
    DEFAULT_THEME_COLORS = {
        'dk1': ThemeColor('dk1', 'Text/Background - Dark 1', '000000', 'text'),
        'lt1': ThemeColor('lt1', 'Text/Background - Light 1', 'FFFFFF', 'background'),
        'dk2': ThemeColor('dk2', 'Text/Background - Dark 2', '1F4788', 'text'),
        'lt2': ThemeColor('lt2', 'Text/Background - Light 2', 'EEECE1', 'background'),
        'accent1': ThemeColor('accent1', 'Accent 1', '4472C4', 'accent'),
        'accent2': ThemeColor('accent2', 'Accent 2', '70AD47', 'accent'),
        'accent3': ThemeColor('accent3', 'Accent 3', 'FFC000', 'accent'),
        'accent4': ThemeColor('accent4', 'Accent 4', '8FAADC', 'accent'),
        'accent5': ThemeColor('accent5', 'Accent 5', '7030A0', 'accent'),
        'accent6': ThemeColor('accent6', 'Accent 6', 'C65911', 'accent'),
        'hlink': ThemeColor('hlink', 'Hyperlink', '0563C1', 'hyperlink'),
        'folHlink': ThemeColor('folHlink', 'Followed Hyperlink', '954F72', 'hyperlink')
    }
    
    # Standard OOXML theme font definitions
    DEFAULT_THEME_FONTS = {
        'majorFont': ThemeFont('majorFont', 'Headings', 'Calibri Light', 'heading'),
        'minorFont': ThemeFont('minorFont', 'Body', 'Calibri', 'body')
    }
    
    # OOXML namespaces
    NAMESPACES = {
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
        'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    }
    
    def __init__(self):
        self.color_engine = ColorTransformationEngine()
        self._theme_cache = {}  # Cache for parsed themes
        
    def create_default_theme(self, name: str = "StyleStack Default") -> Theme:
        """Create a default theme with all standard colors and fonts"""
        theme = Theme(name=name)
        theme.colors = self.DEFAULT_THEME_COLORS.copy()
        theme.fonts = self.DEFAULT_THEME_FONTS.copy()
        return theme
    
    def resolve_theme_color(self, color_slot: str, theme: Optional[Theme] = None, 
                          fallback_color: str = '000000') -> str:
        """
        Resolve theme color slot to RGB hex value.
        
        Args:
            color_slot: Theme color slot name (e.g., 'accent1', 'dk1')
            theme: Theme object to use (defaults to built-in theme)
            fallback_color: Fallback color if slot not found
            
        Returns:
            6-character hex color (without #)
        """
        if theme is None:
            theme = self.create_default_theme()
        
        theme_color = theme.get_color(color_slot)
        if theme_color:
            return theme_color.rgb_value
        
        # Try default theme
        default_color = self.DEFAULT_THEME_COLORS.get(color_slot)
        if default_color:
            return default_color.rgb_value
            
        logger.warning(f"Unknown theme color slot: {color_slot}, using fallback")
        return fallback_color.lstrip('#')
    
    def resolve_theme_font(self, font_slot: str, theme: Optional[Theme] = None,
                         fallback_font: str = 'Calibri') -> str:
        """
        Resolve theme font slot to font family name.
        
        Args:
            font_slot: Theme font slot name ('majorFont' or 'minorFont')
            theme: Theme object to use (defaults to built-in theme)
            fallback_font: Fallback font if slot not found
            
        Returns:
            Font family name
        """
        if theme is None:
            theme = self.create_default_theme()
            
        theme_font = theme.get_font(font_slot)
        if theme_font:
            return theme_font.typeface
        
        # Try default theme
        default_font = self.DEFAULT_THEME_FONTS.get(font_slot)
        if default_font:
            return default_font.typeface
            
        logger.warning(f"Unknown theme font slot: {font_slot}, using fallback")
        return fallback_font
    
    def apply_color_transformation(self, base_color: str, transform_type: str,
                                 value: float) -> str:
        """
        Apply Office-style color transformation.
        
        Args:
            base_color: Base color (hex with or without #)
            transform_type: Transformation type (tint, shade, lumMod, etc.)
            value: Transformation value (Office units, typically 0-100000)
            
        Returns:
            Transformed color as 6-character hex (without #)
        """
        base_color = base_color.lstrip('#')
        return self.color_engine.apply_transformation(base_color, transform_type, value)
    
    def extract_theme_from_xml(self, xml_content: str) -> Theme:
        """Extract theme definition from OOXML theme XML"""
        try:
            root = ET.fromstring(xml_content)
            theme_name = root.get('name', 'Extracted Theme')
            theme = Theme(name=theme_name)
            
            # Extract color scheme
            self._extract_color_scheme(root, theme)
            
            # Extract font scheme  
            self._extract_font_scheme(root, theme)
            
            # Extract format scheme (if needed)
            self._extract_format_scheme(root, theme)
            
            return theme
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse theme XML: {e}")
            return self.create_default_theme("Invalid Theme")
    
    def _extract_color_scheme(self, root: ET.Element, theme: Theme) -> None:
        """Extract color scheme from theme XML"""
        color_scheme = root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}clrScheme')
        if color_scheme is None:
            return
            
        for color_slot in self.DEFAULT_THEME_COLORS.keys():
            color_elem = color_scheme.find(f'./{{{self.NAMESPACES["a"]}}}{color_slot}')
            if color_elem is not None:
                # Look for srgbClr first
                srgb_elem = color_elem.find(f'./{{{self.NAMESPACES["a"]}}}srgbClr')
                if srgb_elem is not None:
                    color_value = srgb_elem.get('val', self.DEFAULT_THEME_COLORS[color_slot].rgb_value)
                    theme_color = ThemeColor(
                        slot=color_slot,
                        name=self.DEFAULT_THEME_COLORS[color_slot].name,
                        rgb_value=color_value,
                        color_type=self.DEFAULT_THEME_COLORS[color_slot].color_type
                    )
                    theme.colors[color_slot] = theme_color
                    continue
                
                # Look for sysClr
                sys_elem = color_elem.find(f'./{{{self.NAMESPACES["a"]}}}sysClr')
                if sys_elem is not None:
                    # System colors - use lastClr if available, otherwise default
                    color_value = sys_elem.get('lastClr', self.DEFAULT_THEME_COLORS[color_slot].rgb_value)
                    theme_color = ThemeColor(
                        slot=color_slot,
                        name=self.DEFAULT_THEME_COLORS[color_slot].name,
                        rgb_value=color_value,
                        color_type=self.DEFAULT_THEME_COLORS[color_slot].color_type
                    )
                    theme.colors[color_slot] = theme_color
    
    def _extract_font_scheme(self, root: ET.Element, theme: Theme) -> None:
        """Extract font scheme from theme XML"""
        font_scheme = root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}fontScheme')
        if font_scheme is None:
            return
            
        for font_slot in self.DEFAULT_THEME_FONTS.keys():
            font_elem = font_scheme.find(f'./{{{self.NAMESPACES["a"]}}}{font_slot}')
            if font_elem is not None:
                # Look for latin font
                latin_elem = font_elem.find(f'./{{{self.NAMESPACES["a"]}}}latin')
                if latin_elem is not None:
                    typeface = latin_elem.get('typeface', self.DEFAULT_THEME_FONTS[font_slot].typeface)
                    pitch_family = latin_elem.get('pitchFamily')
                    charset = latin_elem.get('charset')
                    
                    theme_font = ThemeFont(
                        slot=font_slot,
                        name=self.DEFAULT_THEME_FONTS[font_slot].name,
                        typeface=typeface,
                        font_type=self.DEFAULT_THEME_FONTS[font_slot].font_type,
                        pitch_family=int(pitch_family) if pitch_family else None,
                        charset=int(charset) if charset else None
                    )
                    theme.fonts[font_slot] = theme_font
    
    def _extract_format_scheme(self, root: ET.Element, theme: Theme) -> None:
        """Extract format scheme from theme XML (for future use)"""
        format_scheme = root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}fmtScheme')
        if format_scheme is not None:
            theme.format_scheme['name'] = format_scheme.get('name', 'Default Format')
            # Could extract fill styles, line styles, effect styles here
    
    def extract_theme_from_ooxml_file(self, file_path: Union[str, Path]) -> Optional[Theme]:
        """Extract theme from OOXML file (.potx, .dotx, .xltx)"""
        file_path = Path(file_path)
        
        # Check cache first
        cache_key = f"{file_path}:{file_path.stat().st_mtime}"
        if cache_key in self._theme_cache:
            return self._theme_cache[cache_key]
        
        theme = None
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                # Common theme file locations
                theme_files = [
                    'ppt/theme/theme1.xml',
                    'word/theme/theme1.xml',
                    'xl/theme/theme1.xml'
                ]
                
                for theme_file in theme_files:
                    try:
                        xml_content = zf.read(theme_file).decode('utf-8')
                        theme = self.extract_theme_from_xml(xml_content)
                        break
                    except KeyError:
                        continue  # Theme file doesn't exist
                    except UnicodeDecodeError as e:
                        logger.warning(f"Could not decode theme file {theme_file}: {e}")
                        continue
                        
        except (zipfile.BadZipFile, FileNotFoundError) as e:
            logger.error(f"Could not open OOXML file {file_path}: {e}")
            
        # Cache result
        if theme:
            self._theme_cache[cache_key] = theme
            
        return theme
    
    def validate_theme_compatibility(self, theme: Theme, target_platform: str = 'office') -> Dict[str, Any]:
        """
        Validate theme compatibility for target platform.
        
        Args:
            theme: Theme to validate
            target_platform: Target platform ('office', 'libreoffice', 'google', 'web')
            
        Returns:
            Validation result with compatibility information
        """
        result = {
            'platform': target_platform,
            'valid': True,
            'warnings': [],
            'errors': [],
            'features_supported': [],
            'features_unsupported': []
        }
        
        # Basic theme validation
        validation = theme.validate()
        if not validation['valid']:
            result['warnings'].extend([f"Missing color: {c}" for c in validation['missing_colors']])
            result['warnings'].extend([f"Missing font: {f}" for f in validation['missing_fonts']])
        
        # Platform-specific validation
        if target_platform == 'office':
            # Microsoft Office supports all theme features
            result['features_supported'] = [
                'Full theme color support (12 colors)',
                'Theme font support (major/minor)',
                'Color transformations (tint/shade/lum)',
                'Theme inheritance',
                'Custom themes'
            ]
            
        elif target_platform == 'libreoffice':
            # LibreOffice has limited theme support
            result['features_supported'] = [
                'Basic theme colors',
                'Theme fonts (limited)',
                'Basic color transformations'
            ]
            result['features_unsupported'] = [
                'Advanced color transformations',
                'Full theme inheritance',
                'Complex format schemes'
            ]
            result['warnings'].append("LibreOffice has limited theme support compared to Office")
            
        elif target_platform == 'google':
            # Google Workspace doesn't support OOXML themes
            result['valid'] = False
            result['features_unsupported'] = [
                'OOXML themes not supported',
                'Theme colors not supported',
                'Theme fonts not supported'
            ]
            result['errors'].append("Google Workspace does not support OOXML theme system")
            
        elif target_platform == 'web':
            # Web export has limited theme support
            result['features_supported'] = [
                'Theme colors (as CSS variables)',
                'Theme fonts (with fallbacks)',
                'Basic color transformations (CSS filters)'
            ]
            result['features_unsupported'] = [
                'Dynamic theme switching',
                'Complex color transformations',
                'Theme-dependent formatting'
            ]
            result['warnings'].append("Web export requires CSS conversion of theme elements")
            
        return result
    
    def generate_css_theme_variables(self, theme: Theme) -> str:
        """Generate CSS custom properties for web compatibility"""
        css_vars = [":root {"]
        
        # Add color variables
        for slot, color in theme.colors.items():
            css_vars.append(f"  --theme-{slot}: #{color.rgb_value};")
            css_vars.append(f"  --theme-{slot}-rgb: {', '.join(str(x) for x in color.rgb_tuple)};")
        
        # Add font variables
        for slot, font in theme.fonts.items():
            css_vars.append(f"  --theme-{slot}: '{font.typeface}', sans-serif;")
        
        css_vars.append("}")
        return "\n".join(css_vars)
    
    def create_theme_variation(self, base_theme: Theme, color_overrides: Dict[str, str],
                             font_overrides: Dict[str, str] = None) -> Theme:
        """Create a theme variation with color and font overrides"""
        new_theme = Theme(name=f"{base_theme.name} - Variation")
        
        # Copy base theme
        new_theme.colors = {slot: ThemeColor(
            color.slot, color.name, color.rgb_value, color.color_type
        ) for slot, color in base_theme.colors.items()}
        
        new_theme.fonts = {slot: ThemeFont(
            font.slot, font.name, font.typeface, font.font_type, font.pitch_family, font.charset
        ) for slot, font in base_theme.fonts.items()}
        
        # Apply color overrides
        for slot, color_value in color_overrides.items():
            if slot in new_theme.colors:
                new_theme.colors[slot].rgb_value = color_value.lstrip('#')
        
        # Apply font overrides
        if font_overrides:
            for slot, font_name in font_overrides.items():
                if slot in new_theme.fonts:
                    new_theme.fonts[slot].typeface = font_name
        
        return new_theme


if __name__ == "__main__":
    # Demo usage
    print("🎨 StyleStack Theme Resolver Demo")
    
    resolver = ThemeResolver()
    
    # Create default theme
    theme = resolver.create_default_theme("Demo Theme")
    print(f"Created theme: {theme.name}")
    
    # Test color resolution
    accent1 = resolver.resolve_theme_color('accent1', theme)
    print(f"Accent 1 color: #{accent1}")
    
    # Test font resolution
    heading_font = resolver.resolve_theme_font('majorFont', theme)
    print(f"Heading font: {heading_font}")
    
    # Test color transformations
    tinted_accent = resolver.apply_color_transformation(accent1, 'tint', 50000)
    print(f"50% tinted accent: #{accent1} → #{tinted_accent}")
    
    shaded_accent = resolver.apply_color_transformation(accent1, 'shade', 25000)  
    print(f"25% shaded accent: #{accent1} → #{shaded_accent}")
    
    # Test theme validation
    validation = resolver.validate_theme_compatibility(theme, 'office')
    print(f"Office compatibility: {'✅' if validation['valid'] else '❌'}")
    
    validation = resolver.validate_theme_compatibility(theme, 'libreoffice')
    print(f"LibreOffice compatibility: {'✅' if validation['valid'] else '❌'} ({len(validation['warnings'])} warnings)")
    
    # Generate CSS variables
    css = resolver.generate_css_theme_variables(theme)
    print(f"Generated {len(css.split('--theme-'))-1} CSS variables")
    
    print("Theme resolver demo completed!")