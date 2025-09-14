#!/usr/bin/env python3
"""
End-to-End Test Suite for Advanced Token Features

Tests complete real-world workflows including:
- Corporate theme switching with nested references
- Multi-format template generation with composite tokens
- Office document generation with advanced features
- Complex token hierarchies and dependencies
"""

import pytest
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Any, List
from lxml import etree
from unittest.mock import Mock, patch

# Import all the components for end-to-end testing
from tools.variable_resolver import VariableResolver, ResolvedVariable, TokenType, TokenScope
from tools.composite_token_transformer import (
    ShadowTokenTransformer,
    BorderTokenTransformer,
    GradientTokenTransformer,
    transform_composite_token
)
from tools.w3c_dtcg_validator import W3CDTCGValidator
from tools.ooxml_processor import OOXMLProcessor


class TestCorporateThemeSwitching:
    """Test complete corporate theme switching scenarios"""
    
    def setup_method(self):
        """Setup comprehensive corporate token system"""
        self.resolver = VariableResolver(enable_cache=True)
        self.validator = W3CDTCGValidator()
        
        # Corporate brand system with multiple themes
        self.corporate_tokens = {
            # Brand selector (dynamic)
            'brand': ResolvedVariable('brand', 'acme', TokenType.TEXT, TokenScope.ORG, 'brand_config'),
            'theme': ResolvedVariable('theme', 'light', TokenType.TEXT, TokenScope.THEME, 'theme_config'),
            'platform': ResolvedVariable('platform', 'office', TokenType.TEXT, TokenScope.ORG, 'platform_config'),
            
            # ACME Brand - Light Theme
            'color.acme.light.primary': ResolvedVariable('color.acme.light.primary', '#0066CC', TokenType.COLOR, TokenScope.ORG, 'acme_tokens'),
            'color.acme.light.secondary': ResolvedVariable('color.acme.light.secondary', '#4D94FF', TokenType.COLOR, TokenScope.ORG, 'acme_tokens'),
            'color.acme.light.surface': ResolvedVariable('color.acme.light.surface', '#FFFFFF', TokenType.COLOR, TokenScope.ORG, 'acme_tokens'),
            
            # ACME Brand - Dark Theme
            'color.acme.dark.primary': ResolvedVariable('color.acme.dark.primary', '#3399FF', TokenType.COLOR, TokenScope.ORG, 'acme_tokens'),
            'color.acme.dark.secondary': ResolvedVariable('color.acme.dark.secondary', '#66B2FF', TokenType.COLOR, TokenScope.ORG, 'acme_tokens'),
            'color.acme.dark.surface': ResolvedVariable('color.acme.dark.surface', '#1A1A1A', TokenType.COLOR, TokenScope.ORG, 'acme_tokens'),
            
            # TechCorp Brand - Light Theme  
            'color.techcorp.light.primary': ResolvedVariable('color.techcorp.light.primary', '#FF6B35', TokenType.COLOR, TokenScope.ORG, 'techcorp_tokens'),
            'color.techcorp.light.secondary': ResolvedVariable('color.techcorp.light.secondary', '#FF8A65', TokenType.COLOR, TokenScope.ORG, 'techcorp_tokens'),
            'color.techcorp.light.surface': ResolvedVariable('color.techcorp.light.surface', '#F5F5F5', TokenType.COLOR, TokenScope.ORG, 'techcorp_tokens'),
            
            # TechCorp Brand - Dark Theme
            'color.techcorp.dark.primary': ResolvedVariable('color.techcorp.dark.primary', '#FF7043', TokenType.COLOR, TokenScope.ORG, 'techcorp_tokens'),
            'color.techcorp.dark.secondary': ResolvedVariable('color.techcorp.dark.secondary', '#FF9575', TokenType.COLOR, TokenScope.ORG, 'techcorp_tokens'),
            'color.techcorp.dark.surface': ResolvedVariable('color.techcorp.dark.surface', '#2D2D2D', TokenType.COLOR, TokenScope.ORG, 'techcorp_tokens'),
            
            # Typography with nested references
            'font.{brand}.{platform}.heading': ResolvedVariable('font.acme.office.heading', 'Segoe UI Semibold', TokenType.FONT, TokenScope.ORG, 'acme_tokens'),
            'font.techcorp.office.heading': ResolvedVariable('font.techcorp.office.heading', 'Arial Bold', TokenType.FONT, TokenScope.ORG, 'techcorp_tokens'),
            
            # Spacing system
            'spacing.{brand}.small': ResolvedVariable('spacing.acme.small', '8px', TokenType.DIMENSION, TokenScope.ORG, 'acme_tokens'),
            'spacing.acme.small': ResolvedVariable('spacing.acme.small', '8px', TokenType.DIMENSION, TokenScope.ORG, 'acme_tokens'),
            'spacing.techcorp.small': ResolvedVariable('spacing.techcorp.small', '6px', TokenType.DIMENSION, TokenScope.ORG, 'techcorp_tokens'),
        }
    
    def test_brand_theme_switching(self):
        """Test complete brand and theme switching workflow"""
        # Component that adapts to current brand and theme
        adaptive_button = {
            'background': '{color.{brand}.{theme}.primary}',
            'border': '{color.{brand}.{theme}.secondary}',  
            'text': '{color.{brand}.{theme}.surface}',
            'shadow': '{shadow.{brand}.{theme}.default}'
        }
        
        # Test ACME Light theme
        self.corporate_tokens['brand'].value = 'acme'
        self.corporate_tokens['theme'].value = 'light'
        
        resolved_bg = self.resolver.resolve_nested_reference(adaptive_button['background'], self.corporate_tokens)
        assert resolved_bg == '#0066CC'
        
        resolved_border = self.resolver.resolve_nested_reference(adaptive_button['border'], self.corporate_tokens)  
        assert resolved_border == '#4D94FF'
        
        # Switch to TechCorp Dark theme
        self.corporate_tokens['brand'].value = 'techcorp'
        self.corporate_tokens['theme'].value = 'dark'
        
        resolved_bg = self.resolver.resolve_nested_reference(adaptive_button['background'], self.corporate_tokens)
        assert resolved_bg == '#FF7043'
        
        resolved_border = self.resolver.resolve_nested_reference(adaptive_button['border'], self.corporate_tokens)
        assert resolved_border == '#FF9575'
    
    def test_complex_nested_component_system(self):
        """Test complex component system with multiple nesting levels"""
        # Marketing component with adaptive styling
        marketing_card = {
            '$type': 'component',
            '$value': {
                'background': '{color.{brand}.{theme}.surface}',
                'title_color': '{color.{brand}.{theme}.primary}', 
                'subtitle_color': '{color.{brand}.{theme}.secondary}',
                'shadow': {
                    '$type': 'shadow',
                    '$value': {
                        'color': '{color.{brand}.{theme}.primary}',
                        'offsetX': '{spacing.{brand}.small}',
                        'offsetY': '{spacing.{brand}.small}',
                        'blur': '12px',
                        'spread': '0px'
                    }
                },
                'border': {
                    '$type': 'border',
                    '$value': {
                        'width': '2px',
                        'style': 'solid',
                        'color': '{color.{brand}.{theme}.secondary}'
                    }
                }
            }
        }
        
        # Test with ACME brand
        self.corporate_tokens['brand'].value = 'acme'
        self.corporate_tokens['theme'].value = 'light'
        
        # Resolve all nested references
        background = self.resolver.resolve_nested_reference(
            marketing_card['$value']['background'], self.corporate_tokens
        )
        assert background == '#FFFFFF'
        
        title_color = self.resolver.resolve_nested_reference(
            marketing_card['$value']['title_color'], self.corporate_tokens
        )
        assert title_color == '#0066CC'
        
        # Test shadow token with nested references
        shadow_color = self.resolver.resolve_nested_reference(
            marketing_card['$value']['shadow']['$value']['color'], self.corporate_tokens
        )
        assert shadow_color == '#0066CC'
        
        shadow_offset = self.resolver.resolve_nested_reference(
            marketing_card['$value']['shadow']['$value']['offsetX'], self.corporate_tokens
        )  
        assert shadow_offset == '8px'
    
    def test_w3c_dtcg_validation_with_corporate_tokens(self):
        """Test W3C DTCG validation with corporate token structure"""
        corporate_component = {
            '$type': 'shadow',
            '$value': {
                'color': '{color.{brand}.{theme}.primary}',
                'offsetX': '{spacing.{brand}.small}',
                'offsetY': '{spacing.{brand}.small}', 
                'blur': '4px',
                'spread': '0px'
            },
            '$description': 'Corporate brand-adaptive shadow component'
        }
        
        # Should validate successfully
        validation_result = self.validator.validate_token(corporate_component)
        assert validation_result.is_valid == True
        # W3C DTCG validator should recognize this as a shadow token type
        # Note: TokenType enum may not have SHADOW, but validator should detect it
        assert validation_result.token_type is not None


class TestMultiFormatTemplateGeneration:
    """Test multi-format template generation with advanced tokens"""
    
    def setup_method(self):
        """Setup multi-format template system"""
        self.ooxml_processor = OOXMLProcessor()
        
        # Multi-platform token system
        self.platform_tokens = {
            'platform': ResolvedVariable('platform', 'office', TokenType.TEXT, TokenScope.ORG, 'config'),
            'format': ResolvedVariable('format', 'presentation', TokenType.TEXT, TokenScope.ORG, 'config'),
            
            # Office-specific tokens
            'color.office.presentation.accent': ResolvedVariable('color.office.presentation.accent', '#0078D4', TokenType.COLOR, TokenScope.ORG, 'office_tokens'),
            'color.office.document.accent': ResolvedVariable('color.office.document.accent', '#106EBE', TokenType.COLOR, TokenScope.ORG, 'office_tokens'),
            'color.office.spreadsheet.accent': ResolvedVariable('color.office.spreadsheet.accent', '#217346', TokenType.COLOR, TokenScope.ORG, 'office_tokens'),
            
            # LibreOffice tokens
            'color.libreoffice.presentation.accent': ResolvedVariable('color.libreoffice.presentation.accent', '#0369A1', TokenType.COLOR, TokenScope.ORG, 'libreoffice_tokens'),
            'color.libreoffice.document.accent': ResolvedVariable('color.libreoffice.document.accent', '#075985', TokenType.COLOR, TokenScope.ORG, 'libreoffice_tokens'),
            
            # Google Workspace tokens
            'color.google.presentation.accent': ResolvedVariable('color.google.presentation.accent', '#1A73E8', TokenType.COLOR, TokenScope.ORG, 'google_tokens'),
            'color.google.document.accent': ResolvedVariable('color.google.document.accent', '#1967D2', TokenType.COLOR, TokenScope.ORG, 'google_tokens'),
        }
    
    def test_cross_platform_color_adaptation(self):
        """Test color adaptation across different platforms"""
        resolver = VariableResolver()
        
        # Universal component that adapts to platform and format
        adaptive_accent = '{color.{platform}.{format}.accent}'
        
        # Test Office PowerPoint
        self.platform_tokens['platform'].value = 'office'
        self.platform_tokens['format'].value = 'presentation'
        
        office_color = resolver.resolve_nested_reference(adaptive_accent, self.platform_tokens)
        assert office_color == '#0078D4'
        
        # Test LibreOffice Impress  
        self.platform_tokens['platform'].value = 'libreoffice'
        self.platform_tokens['format'].value = 'presentation'
        
        libre_color = resolver.resolve_nested_reference(adaptive_accent, self.platform_tokens)
        assert libre_color == '#0369A1'
        
        # Test Google Slides
        self.platform_tokens['platform'].value = 'google'
        self.platform_tokens['format'].value = 'presentation'
        
        google_color = resolver.resolve_nested_reference(adaptive_accent, self.platform_tokens)
        assert google_color == '#1A73E8'
    
    def test_powerpoint_template_generation(self):
        """Test PowerPoint template generation with composite tokens"""
        # Corporate PowerPoint slide with advanced styling
        ppt_slide_xml = """
        <p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
               xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
            <p:cSld>
                <p:spTree>
                    <p:sp>
                        <p:nvSpPr>
                            <p:cNvPr id="2" name="Title"/>
                        </p:nvSpPr>
                        <p:spPr>
                            <a:xfrm>
                                <a:off x="914400" y="914400"/>
                                <a:ext cx="7315200" cy="914400"/>
                            </a:xfrm>
                            <a:prstGeom prst="rect"/>
                            <!-- Composite tokens will be inserted here -->
                        </p:spPr>
                        <p:txBody>
                            <a:bodyPr/>
                            <a:p>
                                <a:r>
                                    <a:rPr lang="en-US" sz="4000"/>
                                    <a:t>Corporate Title</a:t>
                                </a:r>
                            </a:p>
                        </p:txBody>
                    </p:sp>
                </p:spTree>
            </p:cSld>
        </p:sld>
        """
        
        # Composite tokens for the slide
        slide_tokens = {
            'corporate_shadow': {
                '$type': 'shadow',
                '$value': {
                    'color': '#0066CC',
                    'offsetX': '2px',
                    'offsetY': '2px',
                    'blur': '8px',
                    'spread': '0px'
                }
            },
            'corporate_border': {
                '$type': 'border',
                '$value': {
                    'width': '2px',
                    'style': 'solid',
                    'color': '#4D94FF'
                }
            }
        }
        
        # Process the slide with composite tokens
        updated_xml, result = self.ooxml_processor.apply_composite_tokens_to_xml(
            ppt_slide_xml, slide_tokens
        )
        
        # Verify processing succeeded
        assert result.success == True
        assert result.elements_processed > 0
        
        # Verify OOXML structure
        root = etree.fromstring(updated_xml)
        
        # Check for shadow effect
        shadow_effect = root.find('.//a:effectLst/a:outerShdw', root.nsmap)
        if shadow_effect is not None:
            assert 'blurRad' in shadow_effect.attrib
            assert shadow_effect.attrib['blurRad'] == '101600'  # 8px in EMU
        
        # Check for border line
        border_line = root.find('.//a:ln', root.nsmap)
        if border_line is not None:
            assert 'w' in border_line.attrib
            assert border_line.attrib['w'] == '25400'  # 2px in EMU
    
    def test_word_document_generation(self):
        """Test Word document generation with composite tokens"""
        # Word document paragraph with styling
        word_doc_xml = """
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                   xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
            <w:body>
                <w:p>
                    <w:pPr>
                        <w:spacing w:before="240" w:after="240"/>
                    </w:pPr>
                    <w:r>
                        <w:rPr>
                            <w:color w:val="000000"/>
                            <!-- Text effects will be applied here -->
                        </w:rPr>
                        <w:t>Corporate Heading</w:t>
                    </w:r>
                </w:p>
            </w:body>
        </w:document>
        """
        
        # Text shadow for Word
        text_effects = {
            'heading_shadow': {
                '$type': 'shadow',
                '$value': {
                    'color': '#333333',
                    'offsetX': '1px',
                    'offsetY': '1px', 
                    'blur': '2px',
                    'spread': '0px'
                }
            }
        }
        
        # Process document (limited support for Word text effects)
        updated_xml, result = self.ooxml_processor.apply_composite_tokens_to_xml(
            word_doc_xml, text_effects
        )
        
        # Should handle gracefully even if no targets found
        assert result.success == True


class TestComplexTokenHierarchies:
    """Test complex token hierarchies and dependencies"""
    
    def setup_method(self):
        """Setup complex hierarchical token system"""
        self.resolver = VariableResolver(enable_cache=True)
        
        # Multi-level organizational hierarchy
        self.hierarchy_tokens = {
            # Organization levels
            'org': ResolvedVariable('org', 'enterprise', TokenType.TEXT, TokenScope.ORG, 'org_config'),
            'division': ResolvedVariable('division', 'marketing', TokenType.TEXT, TokenScope.ORG, 'org_config'),
            'team': ResolvedVariable('team', 'digital', TokenType.TEXT, TokenScope.ORG, 'org_config'),
            'project': ResolvedVariable('project', 'campaign2024', TokenType.TEXT, TokenScope.ORG, 'org_config'),
            
            # Enterprise brand tokens (simplified)
            'brand.enterprise.primary': ResolvedVariable(
                'brand.enterprise.primary', '#E74C3C', TokenType.COLOR, TokenScope.ORG, 'brand_tokens'
            ),
            'brand.enterprise.secondary': ResolvedVariable(
                'brand.enterprise.secondary', '#F39C12', TokenType.COLOR, TokenScope.ORG, 'brand_tokens'
            ),
            
            # Campaign-specific overrides (simplified)
            'campaign.campaign2024.accent': ResolvedVariable(
                'campaign.campaign2024.accent', '#3498DB', TokenType.COLOR, TokenScope.GROUP, 'campaign_tokens'
            ),
            
            # Conditional tokens based on hierarchy (simplified)
            'style.enterprise.priority': ResolvedVariable(
                'style.enterprise.priority', 'high', TokenType.TEXT, TokenScope.ORG, 'style_tokens'
            ),
            
            # Composite components with hierarchical references (simplified)
            'component.enterprise.card': ResolvedVariable(
                'component.enterprise.card', 'elevated', TokenType.TEXT, TokenScope.GROUP, 'component_tokens'
            ),
        }
    
    def test_multi_level_hierarchy_resolution(self):
        """Test resolution across multiple organizational levels"""
        # Component that adapts to organizational hierarchy (simplified patterns)
        org_component = {
            'brand_color': '{brand.{org}.primary}',
            'accent_color': '{campaign.{project}.accent}', 
            'priority_level': '{style.{org}.priority}'
        }
        
        # Test hierarchical brand color resolution
        brand_color = self.resolver.resolve_nested_reference(
            org_component['brand_color'], self.hierarchy_tokens
        )
        assert brand_color == '#E74C3C'
        
        # Test project-specific override
        accent_color = self.resolver.resolve_nested_reference(
            org_component['accent_color'], self.hierarchy_tokens  
        )
        assert accent_color == '#3498DB'
        
        # Test style priority
        priority = self.resolver.resolve_nested_reference(
            org_component['priority_level'], self.hierarchy_tokens
        )
        assert priority == 'high'
    
    def test_conditional_token_resolution(self):
        """Test conditional token resolution based on hierarchy"""
        # Different component behaviors based on org structure (simplified)
        conditional_component = {
            'layout': '{component.{org}.card}',
            'emphasis': '{style.{org}.priority}'
        }
        
        layout = self.resolver.resolve_nested_reference(
            conditional_component['layout'], self.hierarchy_tokens
        )
        assert layout == 'elevated'
        
        # Test organizational structure change impact
        self.hierarchy_tokens['team'].value = 'traditional'
        
        # Should still resolve but potentially to different values
        # (would need corresponding tokens defined)
    
    def test_dependency_chain_resolution(self):
        """Test complex dependency chains in token resolution"""
        # Chain of dependencies (simplified patterns)
        dependency_chain = {
            'final_color': '{brand.{org}.primary}',
            'campaign_override': '{campaign.{project}.accent}',
            'fallback_color': '{brand.{org}.secondary}'
        }
        
        # Test that all levels resolve correctly
        final_color = self.resolver.resolve_nested_reference(
            dependency_chain['final_color'], self.hierarchy_tokens
        )
        assert final_color == '#E74C3C'
        
        campaign_color = self.resolver.resolve_nested_reference(
            dependency_chain['campaign_override'], self.hierarchy_tokens
        )
        assert campaign_color == '#3498DB'  # This is the actual value in campaign.campaign2024.accent
        
        fallback_color = self.resolver.resolve_nested_reference(
            dependency_chain['fallback_color'], self.hierarchy_tokens
        )
        assert fallback_color == '#F39C12'


class TestOfficeDocumentGeneration:
    """Test complete Office document generation workflows"""
    
    def test_powerpoint_presentation_workflow(self):
        """Test complete PowerPoint presentation generation"""
        # Simulate complete presentation build workflow
        presentation_tokens = {
            'brand': 'acme',
            'theme': 'corporate', 
            'presentation_type': 'quarterly_review'
        }
        
        # Presentation-wide design system
        design_system = {
            'title_shadow': {
                '$type': 'shadow',
                '$value': {
                    'color': '#1A1A1A',
                    'offsetX': '1px',
                    'offsetY': '2px',
                    'blur': '4px', 
                    'spread': '0px'
                }
            },
            'card_border': {
                '$type': 'border',
                '$value': {
                    'width': '1px',
                    'style': 'solid',
                    'color': '#E0E0E0'
                }
            },
            'background_gradient': {
                '$type': 'gradient',
                '$value': {
                    'type': 'linear',
                    'direction': 'to bottom',
                    'stops': [
                        {'position': '0%', 'color': '#FFFFFF'},
                        {'position': '100%', 'color': '#F8F9FA'}
                    ]
                }
            }
        }
        
        # Transform all composite tokens
        shadow_transformer = ShadowTokenTransformer()
        border_transformer = BorderTokenTransformer()
        gradient_transformer = GradientTokenTransformer()
        
        title_shadow_ooxml = shadow_transformer.transform(design_system['title_shadow'])
        card_border_ooxml = border_transformer.transform(design_system['card_border'])
        bg_gradient_ooxml = gradient_transformer.transform(design_system['background_gradient'])
        
        # Verify all transformations succeed
        assert '<a:effectLst' in title_shadow_ooxml
        assert '<a:ln' in card_border_ooxml  
        assert '<a:gradFill' in bg_gradient_ooxml
        
        # Verify EMU conversions
        shadow_root = etree.fromstring(title_shadow_ooxml)
        outer_shadow = shadow_root.find('.//a:outerShdw', shadow_root.nsmap)
        assert outer_shadow is not None
        assert outer_shadow.attrib['blurRad'] == '50800'  # 4px = 50800 EMU
    
    def test_excel_workbook_workflow(self):
        """Test Excel workbook generation with data visualization styling"""
        # Excel-specific composite tokens for charts and data
        excel_tokens = {
            'chart_shadow': {
                '$type': 'shadow',
                '$value': {
                    'color': '#000000',
                    'offsetX': '3px',
                    'offsetY': '3px',
                    'blur': '6px',
                    'spread': '1px'
                }
            },
            'data_border': {
                '$type': 'border', 
                '$value': {
                    'width': '0.5px',
                    'style': 'solid',
                    'color': '#D0D0D0'
                }
            }
        }
        
        # Test Excel-specific EMU precision
        shadow_transformer = ShadowTokenTransformer()
        chart_shadow_ooxml = shadow_transformer.transform(excel_tokens['chart_shadow'])
        
        root = etree.fromstring(chart_shadow_ooxml)
        outer_shadow = root.find('.//a:outerShdw', root.nsmap)
        
        # Verify precise EMU calculations for Excel
        assert outer_shadow.attrib['blurRad'] == '76200'  # 6px = 76200 EMU
        
        # Distance calculation: sqrt(3^2 + 3^2) * 12700 = ~53862 EMU
        distance = int(outer_shadow.attrib['dist'])
        expected_distance = int((3**2 + 3**2)**0.5 * 12700)
        assert abs(distance - expected_distance) < 100  # Allow small rounding differences
    
    def test_template_archive_generation(self):
        """Test complete template archive (.potx, .dotx, .xltx) generation"""
        # Simulate building a complete OOXML template archive
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create mock OOXML structure
            ooxml_structure = {
                '[Content_Types].xml': '<?xml version="1.0"?><Types></Types>',
                '_rels/.rels': '<?xml version="1.0"?><Relationships></Relationships>',
                'ppt/presentation.xml': '<?xml version="1.0"?><p:presentation></p:presentation>',
                'ppt/theme/theme1.xml': self._create_theme_xml_with_tokens()
            }
            
            # Build the archive structure
            for file_path, content in ooxml_structure.items():
                full_path = temp_path / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content, encoding='utf-8')
            
            # Create template archive
            template_path = temp_path / 'corporate_template.potx'
            with zipfile.ZipFile(template_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file_path in ooxml_structure.keys():
                    zip_file.write(temp_path / file_path, file_path)
            
            # Verify archive was created
            assert template_path.exists()
            assert template_path.stat().st_size > 0
            
            # Verify archive structure
            with zipfile.ZipFile(template_path, 'r') as zip_file:
                file_list = zip_file.namelist()
                assert '[Content_Types].xml' in file_list
                assert 'ppt/theme/theme1.xml' in file_list
    
    def _create_theme_xml_with_tokens(self) -> str:
        """Create theme XML with embedded token references"""
        return '''<?xml version="1.0" encoding="UTF-8"?>
        <a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Corporate Theme">
            <a:themeElements>
                <a:clrScheme name="Corporate Colors">
                    <a:accent1>
                        <a:srgbClr val="0066CC"/>
                    </a:accent1>
                    <a:accent2>
                        <a:srgbClr val="4D94FF"/>
                    </a:accent2>
                </a:clrScheme>
                <a:fontScheme name="Corporate Fonts">
                    <a:majorFont>
                        <a:latin typeface="Segoe UI Semibold"/>
                    </a:majorFont>
                    <a:minorFont>
                        <a:latin typeface="Segoe UI"/>
                    </a:minorFont>
                </a:fontScheme>
            </a:themeElements>
        </a:theme>'''


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])