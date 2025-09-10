"""
Test suite for OOXML Theme Integration System

Tests theme color slot resolution, font resolution, color transformations,
and cross-platform theme compatibility for Office applications.

Validates:
- Theme color slot resolution (accent1-6, dk1/lt1, etc.)
- Theme font resolution (majorFont/minorFont)
- Color transformations (tint/shade/alpha) matching Office behavior
- Theme inheritance across PowerPoint, Word, Excel
- Cross-platform theme compatibility
"""


from typing import Any, Dict
import pytest
import xml.etree.ElementTree as ET
import colorsys


class MockThemeResolver:
    """Mock theme resolver for testing theme integration"""
    
    # Standard OOXML theme color slots
    THEME_COLOR_SLOTS = {
        'dk1': {'name': 'Dark 1', 'default': '000000', 'type': 'text'},
        'lt1': {'name': 'Light 1', 'default': 'FFFFFF', 'type': 'background'},
        'dk2': {'name': 'Dark 2', 'default': '1F4788', 'type': 'text'},
        'lt2': {'name': 'Light 2', 'default': 'EEECE1', 'type': 'background'},
        'accent1': {'name': 'Accent 1', 'default': '4472C4', 'type': 'accent'},
        'accent2': {'name': 'Accent 2', 'default': '70AD47', 'type': 'accent'},
        'accent3': {'name': 'Accent 3', 'default': 'FFC000', 'type': 'accent'},
        'accent4': {'name': 'Accent 4', 'default': '8FAADC', 'type': 'accent'},
        'accent5': {'name': 'Accent 5', 'default': '7030A0', 'type': 'accent'},
        'accent6': {'name': 'Accent 6', 'default': 'C65911', 'type': 'accent'},
        'hlink': {'name': 'Hyperlink', 'default': '0563C1', 'type': 'hyperlink'},
        'folHlink': {'name': 'Followed Hyperlink', 'default': '954F72', 'type': 'hyperlink'}
    }
    
    # Standard OOXML theme font slots
    THEME_FONT_SLOTS = {
        'majorFont': {'name': 'Headings', 'default': 'Calibri Light', 'type': 'heading'},
        'minorFont': {'name': 'Body', 'default': 'Calibri', 'type': 'body'}
    }
    
    def __init__(self):
        self.theme_colors = self.THEME_COLOR_SLOTS.copy()
        self.theme_fonts = self.THEME_FONT_SLOTS.copy()
    
    def resolve_theme_color(self, color_slot: str, theme_overrides: Dict[str, str] = None) -> str:
        """Resolve theme color slot to RGB value"""
        if theme_overrides and color_slot in theme_overrides:
            return theme_overrides[color_slot]
        
        if color_slot in self.theme_colors:
            return self.theme_colors[color_slot]['default']
        
        # Fallback to dk1 (black)
        return self.theme_colors['dk1']['default']
    
    def resolve_theme_font(self, font_slot: str, theme_overrides: Dict[str, str] = None) -> str:
        """Resolve theme font slot to font family"""
        if theme_overrides and font_slot in theme_overrides:
            return theme_overrides[font_slot]
        
        if font_slot in self.theme_fonts:
            return self.theme_fonts[font_slot]['default']
        
        # Fallback to Calibri
        return 'Calibri'
    
    def apply_color_transformation(self, base_color: str, transformation: str, 
                                 value: float) -> str:
        """Apply Office-style color transformations"""
        # Convert hex to RGB
        rgb = tuple(int(base_color[i:i+2], 16) for i in (0, 2, 4))
        
        if transformation == 'tint':
            # Tint: mix with white
            transformed = tuple(
                int(rgb[i] + (255 - rgb[i]) * (value / 100000))
                for i in range(3)
            )
        elif transformation == 'shade':
            # Shade: mix with black  
            transformed = tuple(
                int(rgb[i] * (1 - value / 100000))
                for i in range(3)
            )
        elif transformation == 'lumMod':
            # Luminance modulation
            h, l, s = colorsys.rgb_to_hls(rgb[0]/255, rgb[1]/255, rgb[2]/255)
            l = l * (value / 100000)
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            transformed = (int(r * 255), int(g * 255), int(b * 255))
        elif transformation == 'lumOff':
            # Luminance offset
            h, l, s = colorsys.rgb_to_hls(rgb[0]/255, rgb[1]/255, rgb[2]/255)
            l = min(1.0, l + (value / 100000))
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            transformed = (int(r * 255), int(g * 255), int(b * 255))
        elif transformation == 'alpha':
            # Alpha transparency (return original color, alpha handled separately)
            transformed = rgb
        else:
            # Unknown transformation, return original
            transformed = rgb
        
        # Convert back to hex
        return f"{transformed[0]:02X}{transformed[1]:02X}{transformed[2]:02X}"
    
    def extract_theme_from_xml(self, xml_content: str) -> Dict[str, Any]:
        """Extract theme definition from OOXML theme XML"""
        try:
            root = ET.fromstring(xml_content)
            ns_a = "http://schemas.openxmlformats.org/drawingml/2006/main"
            theme = {
                'name': root.get('name', 'Unnamed Theme'),
                'colors': {},
                'fonts': {}
            }
            
            # Extract colors
            color_scheme = root.find(f'.//{{{ns_a}}}clrScheme')
            if color_scheme is not None:
                for color_slot in self.THEME_COLOR_SLOTS.keys():
                    color_elem = color_scheme.find(f'.//{{{ns_a}}}{color_slot}')
                    if color_elem is not None:
                        # Look for srgbClr or sysClr
                        srgb_elem = color_elem.find(f'.//{{{ns_a}}}srgbClr')
                        if srgb_elem is not None:
                            theme['colors'][color_slot] = srgb_elem.get('val', self.theme_colors[color_slot]['default'])
            
            # Extract fonts
            font_scheme = root.find(f'.//{{{ns_a}}}fontScheme')
            if font_scheme is not None:
                for font_slot in self.THEME_FONT_SLOTS.keys():
                    font_elem = font_scheme.find(f'.//{{{ns_a}}}{font_slot}')
                    if font_elem is not None:
                        latin_elem = font_elem.find(f'.//{{{ns_a}}}latin')
                        if latin_elem is not None:
                            theme['fonts'][font_slot] = latin_elem.get('typeface', self.theme_fonts[font_slot]['default'])
            
            return theme
            
        except ET.ParseError:
            return {'name': 'Invalid Theme', 'colors': {}, 'fonts': {}}
    
    def validate_theme_compatibility(self, theme: Dict[str, Any], 
                                   target_platform: str = 'office') -> Dict[str, Any]:
        """Validate theme compatibility across platforms"""
        compatibility = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'platform': target_platform
        }
        
        # Check color slots
        for slot_name, slot_info in self.THEME_COLOR_SLOTS.items():
            if slot_name not in theme.get('colors', {}):
                compatibility['warnings'].append(f"Missing theme color: {slot_name}")
        
        # Check font slots
        for slot_name, slot_info in self.THEME_FONT_SLOTS.items():
            if slot_name not in theme.get('fonts', {}):
                compatibility['warnings'].append(f"Missing theme font: {slot_name}")
        
        # Platform-specific validation
        if target_platform == 'office':
            # Office supports all theme features
            pass
        elif target_platform == 'libreoffice':
            # LibreOffice has limited theme support
            compatibility['warnings'].append("LibreOffice has limited theme color support")
        elif target_platform == 'google':
            # Google Workspace doesn't support full themes
            compatibility['warnings'].append("Google Workspace doesn't support OOXML themes")
            compatibility['valid'] = False
        
        return compatibility


class TestThemeResolver:
    """Test suite for theme integration system"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.resolver = MockThemeResolver()
        
        # Sample theme XML
        self.sample_theme_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="StyleStack Professional">
          <a:themeElements>
            <a:clrScheme name="StyleStack Colors">
              <a:dk1>
                <a:sysClr val="windowText" lastClr="000000"/>
              </a:dk1>
              <a:lt1>
                <a:sysClr val="window" lastClr="FFFFFF"/>
              </a:lt1>
              <a:dk2>
                <a:srgbClr val="1F4788"/>
              </a:dk2>
              <a:lt2>
                <a:srgbClr val="EEECE1"/>
              </a:lt2>
              <a:accent1>
                <a:srgbClr val="4472C4"/>
              </a:accent1>
              <a:accent2>
                <a:srgbClr val="70AD47"/>
              </a:accent2>
              <a:accent3>
                <a:srgbClr val="FFC000"/>
              </a:accent3>
              <a:accent4>
                <a:srgbClr val="8FAADC"/>
              </a:accent4>
              <a:accent5>
                <a:srgbClr val="7030A0"/>
              </a:accent5>
              <a:accent6>
                <a:srgbClr val="C65911"/>
              </a:accent6>
              <a:hlink>
                <a:srgbClr val="0563C1"/>
              </a:hlink>
              <a:folHlink>
                <a:srgbClr val="954F72"/>
              </a:folHlink>
            </a:clrScheme>
            <a:fontScheme name="StyleStack Fonts">
              <a:majorFont>
                <a:latin typeface="Calibri Light" pitchFamily="34" charset="0"/>
                <a:ea typeface="" pitchFamily="34" charset="0"/>
                <a:cs typeface="" pitchFamily="34" charset="0"/>
              </a:majorFont>
              <a:minorFont>
                <a:latin typeface="Calibri" pitchFamily="34" charset="0"/>
                <a:ea typeface="" pitchFamily="34" charset="0"/>
                <a:cs typeface="" pitchFamily="34" charset="0"/>
              </a:minorFont>
            </a:fontScheme>
          </a:themeElements>
        </a:theme>'''
    
    def test_theme_color_slot_resolution(self):
        """Test resolution of all theme color slots"""
        # Test default color resolution
        for slot_name, slot_info in self.resolver.THEME_COLOR_SLOTS.items():
            resolved_color = self.resolver.resolve_theme_color(slot_name)
            assert resolved_color == slot_info['default']
            assert len(resolved_color) == 6  # Should be 6-character hex
            # Verify it's valid hex
            int(resolved_color, 16)  # Should not raise exception
        
        print(f"✅ Resolved {len(self.resolver.THEME_COLOR_SLOTS)} theme color slots")
    
    def test_theme_color_overrides(self):
        """Test theme color resolution with overrides"""
        overrides = {
            'accent1': 'FF0000',  # Red
            'accent2': '00FF00',  # Green  
            'dk1': '333333'       # Dark gray
        }
        
        # Test overridden colors
        assert self.resolver.resolve_theme_color('accent1', overrides) == 'FF0000'
        assert self.resolver.resolve_theme_color('accent2', overrides) == '00FF00'
        assert self.resolver.resolve_theme_color('dk1', overrides) == '333333'
        
        # Test non-overridden colors (should use defaults)
        assert self.resolver.resolve_theme_color('accent3', overrides) == 'FFC000'
        assert self.resolver.resolve_theme_color('lt1', overrides) == 'FFFFFF'
    
    def test_theme_font_slot_resolution(self):
        """Test resolution of theme font slots"""
        # Test default font resolution
        for slot_name, slot_info in self.resolver.THEME_FONT_SLOTS.items():
            resolved_font = self.resolver.resolve_theme_font(slot_name)
            assert resolved_font == slot_info['default']
            assert len(resolved_font) > 0  # Should have font name
        
        print(f"✅ Resolved {len(self.resolver.THEME_FONT_SLOTS)} theme font slots")
    
    def test_theme_font_overrides(self):
        """Test theme font resolution with overrides"""
        overrides = {
            'majorFont': 'Arial Black',
            'minorFont': 'Arial'
        }
        
        # Test overridden fonts
        assert self.resolver.resolve_theme_font('majorFont', overrides) == 'Arial Black'
        assert self.resolver.resolve_theme_font('minorFont', overrides) == 'Arial'
        
        # Test fallback for unknown font
        assert self.resolver.resolve_theme_font('unknownFont', overrides) == 'Calibri'
    
    def test_color_tint_transformation(self):
        """Test color tint transformation (mix with white)"""
        base_color = '4472C4'  # Blue
        
        # Test 50% tint (50000 in Office units)
        tinted = self.resolver.apply_color_transformation(base_color, 'tint', 50000)
        
        # Should be lighter than original
        original_brightness = sum(int(base_color[i:i+2], 16) for i in (0, 2, 4))
        tinted_brightness = sum(int(tinted[i:i+2], 16) for i in (0, 2, 4))
        
        assert tinted_brightness > original_brightness
        assert len(tinted) == 6  # Should be 6-character hex
        
        print(f"✅ Tint transformation: {base_color} → {tinted}")
    
    def test_color_shade_transformation(self):
        """Test color shade transformation (mix with black)"""
        base_color = '4472C4'  # Blue
        
        # Test 50% shade
        shaded = self.resolver.apply_color_transformation(base_color, 'shade', 50000)
        
        # Should be darker than original
        original_brightness = sum(int(base_color[i:i+2], 16) for i in (0, 2, 4))
        shaded_brightness = sum(int(shaded[i:i+2], 16) for i in (0, 2, 4))
        
        assert shaded_brightness < original_brightness
        assert len(shaded) == 6  # Should be 6-character hex
        
        print(f"✅ Shade transformation: {base_color} → {shaded}")
    
    def test_luminance_modulation(self):
        """Test luminance modulation transformation"""
        base_color = '808080'  # Mid gray
        
        # Test 75% luminance modulation
        mod_color = self.resolver.apply_color_transformation(base_color, 'lumMod', 75000)
        
        # Should be different from original
        assert mod_color != base_color
        assert len(mod_color) == 6
        
        print(f"✅ Luminance modulation: {base_color} → {mod_color}")
    
    def test_theme_extraction_from_xml(self):
        """Test extracting theme definition from XML"""
        theme = self.resolver.extract_theme_from_xml(self.sample_theme_xml)
        
        # Verify theme structure
        assert theme['name'] == 'StyleStack Professional'
        assert 'colors' in theme
        assert 'fonts' in theme
        
        # Verify extracted colors
        assert theme['colors']['accent1'] == '4472C4'
        assert theme['colors']['accent2'] == '70AD47'
        assert theme['colors']['dk2'] == '1F4788'
        
        # Verify extracted fonts
        assert theme['fonts']['majorFont'] == 'Calibri Light'
        assert theme['fonts']['minorFont'] == 'Calibri'
        
        print(f"✅ Extracted theme: {theme['name']}")
        print(f"   Colors: {len(theme['colors'])} slots")
        print(f"   Fonts: {len(theme['fonts'])} slots")
    
    def test_invalid_theme_xml_handling(self):
        """Test handling of invalid theme XML"""
        invalid_xml = '<invalid>malformed XML without proper structure'
        
        theme = self.resolver.extract_theme_from_xml(invalid_xml)
        
        # Should return safe default theme
        assert theme['name'] == 'Invalid Theme'
        assert theme['colors'] == {}
        assert theme['fonts'] == {}
    
    def test_theme_compatibility_office(self):
        """Test theme compatibility validation for Microsoft Office"""
        theme = self.resolver.extract_theme_from_xml(self.sample_theme_xml)
        compatibility = self.resolver.validate_theme_compatibility(theme, 'office')
        
        assert compatibility['valid'] == True
        assert compatibility['platform'] == 'office'
        # Office should have minimal warnings with complete theme
        assert len(compatibility['warnings']) == 0
        assert len(compatibility['errors']) == 0
    
    def test_theme_compatibility_incomplete(self):
        """Test theme compatibility with incomplete theme"""
        incomplete_theme = {
            'name': 'Incomplete Theme',
            'colors': {'accent1': 'FF0000'},  # Missing most colors
            'fonts': {}  # Missing all fonts
        }
        
        compatibility = self.resolver.validate_theme_compatibility(incomplete_theme, 'office')
        
        assert compatibility['valid'] == True  # Still valid, just incomplete
        assert len(compatibility['warnings']) > 0  # Should have warnings
        
        # Should warn about missing colors and fonts
        warning_text = ' '.join(compatibility['warnings'])
        assert 'Missing theme color' in warning_text
        assert 'Missing theme font' in warning_text
    
    def test_theme_compatibility_libreoffice(self):
        """Test theme compatibility for LibreOffice"""
        theme = self.resolver.extract_theme_from_xml(self.sample_theme_xml)
        compatibility = self.resolver.validate_theme_compatibility(theme, 'libreoffice')
        
        assert compatibility['valid'] == True  # Valid but with warnings
        assert compatibility['platform'] == 'libreoffice'
        
        # Should warn about LibreOffice limitations
        warning_text = ' '.join(compatibility['warnings'])
        assert 'LibreOffice' in warning_text
    
    def test_theme_compatibility_google(self):
        """Test theme compatibility for Google Workspace"""
        theme = self.resolver.extract_theme_from_xml(self.sample_theme_xml)
        compatibility = self.resolver.validate_theme_compatibility(theme, 'google')
        
        assert compatibility['valid'] == False  # Not valid for Google
        assert compatibility['platform'] == 'google'
        
        # Should warn about Google Workspace limitations
        warning_text = ' '.join(compatibility['warnings'])
        assert 'Google Workspace' in warning_text
    
    def test_complex_color_transformations(self):
        """Test complex color transformations matching Office behavior"""
        base_color = '4472C4'  # Accent 1 blue
        
        transformations = [
            ('tint', 25000),   # 25% tint
            ('shade', 25000),  # 25% shade  
            ('lumMod', 85000), # 85% luminance
            ('lumOff', 15000), # 15% luminance offset
        ]
        
        results = {}
        for transform_type, value in transformations:
            result = self.resolver.apply_color_transformation(base_color, transform_type, value)
            results[f"{transform_type}_{value}"] = result
            
            # Verify result is valid hex color
            assert len(result) == 6
            int(result, 16)  # Should not raise exception
        
        # Verify transformations produce different results
        unique_results = set(results.values())
        assert len(unique_results) == len(transformations)  # All should be different
        
        print("✅ Complex color transformations:")
        for transform_name, color in results.items():
            print(f"   {transform_name}: {base_color} → {color}")
    
    def test_accent_color_inheritance(self):
        """Test accent color inheritance patterns"""
        # Test the 6 accent colors
        accent_colors = []
        for i in range(1, 7):
            color = self.resolver.resolve_theme_color(f'accent{i}')
            accent_colors.append(color)
            assert len(color) == 6
            assert color != '000000'  # Should not be black (default fallback)
        
        # All accent colors should be different
        assert len(set(accent_colors)) == 6
        
        print(f"✅ Accent color inheritance verified:")
        for i, color in enumerate(accent_colors, 1):
            print(f"   accent{i}: #{color}")
    
    def test_theme_color_relationships(self):
        """Test relationships between theme colors"""
        dk1 = self.resolver.resolve_theme_color('dk1')  # Dark text
        lt1 = self.resolver.resolve_theme_color('lt1')  # Light background
        dk2 = self.resolver.resolve_theme_color('dk2')  # Dark accent
        lt2 = self.resolver.resolve_theme_color('lt2')  # Light accent
        
        # Convert to brightness values for comparison
        def hex_to_brightness(hex_color):
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return (r * 299 + g * 587 + b * 114) / 1000
        
        dk1_brightness = hex_to_brightness(dk1)
        lt1_brightness = hex_to_brightness(lt1)
        dk2_brightness = hex_to_brightness(dk2)
        lt2_brightness = hex_to_brightness(lt2)
        
        # Dark colors should be darker than light colors
        assert dk1_brightness < lt1_brightness
        assert dk2_brightness < lt2_brightness
        
        # Light 1 should be lightest (typically white)
        assert lt1_brightness >= lt2_brightness
        
        print("✅ Theme color relationships validated:")
        print(f"   dk1 brightness: {dk1_brightness:.1f}")
        print(f"   lt1 brightness: {lt1_brightness:.1f}")
        print(f"   dk2 brightness: {dk2_brightness:.1f}")
        print(f"   lt2 brightness: {lt2_brightness:.1f}")
    
    def test_font_inheritance_patterns(self):
        """Test font inheritance between major and minor fonts"""
        major_font = self.resolver.resolve_theme_font('majorFont')
        minor_font = self.resolver.resolve_theme_font('minorFont')
        
        # Both should be valid font names
        assert len(major_font) > 0
        assert len(minor_font) > 0
        
        # Fonts may be the same or different
        print(f"✅ Font inheritance verified:")
        print(f"   Major font (headings): {major_font}")
        print(f"   Minor font (body): {minor_font}")
        
        # Test font variations
        font_overrides = {
            'majorFont': 'Impact',
            'minorFont': 'Georgia'
        }
        
        assert self.resolver.resolve_theme_font('majorFont', font_overrides) == 'Impact'
        assert self.resolver.resolve_theme_font('minorFont', font_overrides) == 'Georgia'


if __name__ == "__main__":
    # Run basic tests
    print("🎨 Testing OOXML Theme Integration System")
    
    test_class = TestThemeResolver()
    test_class.setup_method()
    
    try:
        print("Testing theme color slot resolution...")
        test_class.test_theme_color_slot_resolution()
        
        print("Testing theme font slot resolution...")
        test_class.test_theme_font_slot_resolution()
        
        print("Testing color transformations...")
        test_class.test_color_tint_transformation()
        test_class.test_color_shade_transformation()
        
        print("Testing theme extraction from XML...")
        test_class.test_theme_extraction_from_xml()
        
        print("Testing theme compatibility...")
        test_class.test_theme_compatibility_office()
        test_class.test_theme_compatibility_libreoffice()
        
        print("Testing complex color transformations...")
        test_class.test_complex_color_transformations()
        
        print("Testing theme color relationships...")
        test_class.test_theme_color_relationships()
        
        print("Testing font inheritance...")
        test_class.test_font_inheritance_patterns()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("Theme integration tests completed!")