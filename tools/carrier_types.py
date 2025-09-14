#!/usr/bin/env python3
"""
Carrier Type Definitions for StyleStack OOXML Templates

This module defines comprehensive carrier types for all major OOXML structural
elements including text styles, tables, shapes, charts, themes, and layouts.
Each carrier type includes XPath patterns, design token mappings, and
platform-specific variations.

Author: StyleStack Team
Version: 1.0.0
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import json


@dataclass 
class CarrierTypeDefinition:
    """Complete definition for a carrier type including all platform variations."""
    name: str
    description: str
    ooxml_xpaths: List[str]  # Microsoft Office OOXML XPath expressions
    odf_xpaths: List[str]    # LibreOffice ODF XPath expressions  
    google_selectors: List[str]  # Google Workspace JSON selectors
    required_tokens: List[str]   # Required design tokens for this carrier
    optional_tokens: List[str]   # Optional design tokens
    validation_rules: Dict[str, Any]
    examples: Dict[str, str] = field(default_factory=dict)


class ProfessionalCarrierTypes:
    """
    Professional carrier type definitions that eliminate Office ugly defaults
    and provide publication-quality typography and design.
    """
    
    # Text Style Carriers - Professional Typography
    TEXT_HEADING_1 = CarrierTypeDefinition(
        name="text_heading_1",
        description="Primary heading styles with professional typography hierarchy",
        ooxml_xpaths=[
            "//a:p[a:pPr/a:pStyle[@val='Heading1']]/a:pPr",
            "//a:p[a:pPr/a:lvl/@val='0']/a:pPr",
            "//a:txBody/a:p[position()=1]/a:pPr"  # First paragraph as heading
        ],
        odf_xpaths=[
            "//text:p[@text:style-name='Heading_20_1']",
            "//text:h[@text:outline-level='1']"
        ],
        google_selectors=[
            "paragraphStyle.namedStyleType='HEADING_1'",
            "paragraphStyle.headingId"
        ],
        required_tokens=[
            "typography.heading1.font_family",
            "typography.heading1.font_size", 
            "typography.heading1.line_height",
            "typography.heading1.color"
        ],
        optional_tokens=[
            "typography.heading1.font_weight",
            "typography.heading1.letter_spacing",
            "typography.heading1.margin_before",
            "typography.heading1.margin_after"
        ],
        validation_rules={
            "min_font_size_emu": 1440,  # 20pt minimum for H1
            "baseline_grid_alignment": 360,
            "contrast_ratio_minimum": 7.0  # WCAG AAA
        }
    )
    
    TEXT_BODY = CarrierTypeDefinition(
        name="text_body",
        description="Body text with professional typography replacing Arial defaults",
        ooxml_xpaths=[
            "//a:p[a:pPr/a:pStyle[@val='Normal']]/a:pPr",
            "//a:p[not(a:pPr/a:pStyle)]/a:pPr",  # Default paragraphs
            "//a:p/a:r/a:rPr"  # Run properties
        ],
        odf_xpaths=[
            "//text:p[@text:style-name='Standard']",
            "//text:p[not(@text:style-name)]"
        ],
        google_selectors=[
            "paragraphStyle.namedStyleType='NORMAL_TEXT'",
            "textStyle.fontSize",
            "textStyle.foregroundColor"
        ],
        required_tokens=[
            "typography.body.font_family",
            "typography.body.font_size",
            "typography.body.line_height", 
            "typography.body.color"
        ],
        optional_tokens=[
            "typography.body.margin_before",
            "typography.body.margin_after",
            "typography.body.text_indent"
        ],
        validation_rules={
            "font_size_emu_range": [720, 1080],  # 10pt-15pt range
            "line_height_ratio_range": [1.2, 1.8],
            "professional_fonts_only": True
        }
    )

    # Table Carriers - Professional Table Defaults
    TABLE_DEFAULT_STYLE = CarrierTypeDefinition(
        name="table_default_style", 
        description="Professional table defaults eliminating ugly Arial formatting",
        ooxml_xpaths=[
            "//a:tbl/a:tblPr",
            "//a:tbl/a:tr/a:tc/a:txBody/a:p/a:pPr",  # Table cell text
            "//a:tbl/@*[contains(name(), 'defRPr')]"  # Default run properties
        ],
        odf_xpaths=[
            "//table:table/table:table-row/table:table-cell",
            "//table:table-template"
        ],
        google_selectors=[
            "table.tableRows.tableCells.content.paragraph",
            "table.tableStyle"
        ],
        required_tokens=[
            "tables.default.font_family",
            "tables.default.font_size",
            "tables.default.line_height",
            "tables.default.cell_padding",
            "tables.default.border_color"
        ],
        optional_tokens=[
            "tables.default.header_background",
            "tables.default.alternating_row_color",
            "tables.default.border_width"
        ],
        validation_rules={
            "eliminate_arial": True,
            "professional_cell_padding": True,
            "consistent_typography": True,
            "accessible_contrast": 7.0
        },
        examples={
            "before": "Arial 11pt, inconsistent padding, ugly borders",
            "after": "Professional typography, proper spacing, clean borders"
        }
    )

    # Shape and Graphics Carriers
    SHAPE_DEFAULT_STYLE = CarrierTypeDefinition(
        name="shape_default_style",
        description="Professional shape formatting with brand-consistent styling",
        ooxml_xpaths=[
            "//a:sp/a:spPr",  # Shape properties
            "//a:sp/a:txBody/a:p/a:pPr",  # Text in shapes
            "//a:sp/a:spPr/a:solidFill/a:srgbClr",  # Fill colors
            "//a:sp/a:spPr/a:ln/a:solidFill/a:srgbClr"  # Line colors
        ],
        odf_xpaths=[
            "//draw:frame/draw:text-box",
            "//draw:custom-shape"
        ],
        google_selectors=[
            "pageElements.shape.shapeProperties.shapeBackgroundFill",
            "pageElements.shape.shapeProperties.outline"
        ],
        required_tokens=[
            "shapes.default.fill_color", 
            "shapes.default.border_color",
            "shapes.default.border_width",
            "shapes.text.font_family",
            "shapes.text.font_size"
        ],
        optional_tokens=[
            "shapes.default.shadow",
            "shapes.default.corner_radius",
            "shapes.effects.glow"
        ],
        validation_rules={
            "brand_color_compliance": True,
            "accessibility_contrast": 4.5,  # WCAG AA for graphics
            "professional_effects_only": True
        }
    )

    # Chart Carriers - Professional Chart Styling
    CHART_DEFAULT_STYLE = CarrierTypeDefinition(
        name="chart_default_style",
        description="Professional chart styling with accessible colors and typography",
        ooxml_xpaths=[
            "//c:chart/c:plotArea/c:*/c:ser/c:dPt/c:spPr",  # Data point styling
            "//c:chart/c:legend/c:txPr/a:p/a:pPr",  # Legend text
            "//c:chart/c:title/c:tx/a:rich/a:p/a:pPr",  # Chart title
            "//c:chartSpace/c:spPr"  # Chart area properties
        ],
        odf_xpaths=[
            "//chart:chart/chart:plot-area",
            "//chart:legend"
        ],
        google_selectors=[
            "chart.chartType",
            "chart.spec.title.textFormat",
            "chart.spec.legend.textFormat"
        ],
        required_tokens=[
            "charts.colors.data_series",  # Array of colors for data series
            "charts.typography.title.font_family",
            "charts.typography.title.font_size",
            "charts.typography.axis.font_family",
            "charts.typography.axis.font_size"
        ],
        optional_tokens=[
            "charts.background_color",
            "charts.grid_color", 
            "charts.legend.position"
        ],
        validation_rules={
            "colorblind_friendly_palette": True,
            "high_contrast_compliance": True,
            "professional_typography": True
        }
    )

    # Theme Carriers - Professional Color Schemes
    THEME_COLOR_SCHEME = CarrierTypeDefinition(
        name="theme_color_scheme",
        description="Professional theme colors supporting multiple variants (light/dark)",
        ooxml_xpaths=[
            "//a:theme/a:themeElements/a:clrScheme",
            "//a:theme/a:themeElements/a:clrScheme/a:dk1",  # Dark 1
            "//a:theme/a:themeElements/a:clrScheme/a:lt1",  # Light 1
            "//a:theme/a:themeElements/a:clrScheme/a:accent1",  # Accent colors
            "//a:extraClrSchemeLst/a:extraClrScheme/a:clrScheme"  # Additional themes
        ],
        odf_xpaths=[
            "//office:styles/style:default-style",
            "//office:automatic-styles/style:style"
        ],
        google_selectors=[
            "namedStyles.NORMAL_TEXT.textStyle.foregroundColor",
            "namedStyles.HEADING_1.textStyle.foregroundColor"
        ],
        required_tokens=[
            "theme.colors.dark1",      # Primary dark color
            "theme.colors.light1",     # Primary light color
            "theme.colors.dark2",      # Secondary dark
            "theme.colors.light2",     # Secondary light
            "theme.colors.accent1",    # Primary brand color
            "theme.colors.accent2",    # Secondary brand color
            "theme.colors.hyperlink",
            "theme.colors.followed_hyperlink"
        ],
        optional_tokens=[
            "theme.colors.accent3",
            "theme.colors.accent4", 
            "theme.colors.accent5",
            "theme.colors.accent6",
            "theme.variants.dark_mode",
            "theme.variants.high_contrast"
        ],
        validation_rules={
            "wcag_aaa_contrast": 7.0,
            "color_profile": "sRGB IEC61966-2.1",
            "multiple_theme_support": True
        }
    )

    # Master Slide and Layout Carriers
    MASTER_SLIDE_LAYOUT = CarrierTypeDefinition(
        name="master_slide_layout", 
        description="Professional master slide layouts with consistent branding",
        ooxml_xpaths=[
            "//p:sldMaster/p:cSld/p:spTree/p:sp",  # Master slide shapes
            "//p:sldLayout/p:cSld/p:spTree/p:sp",  # Layout shapes
            "//p:ph[@type='title']/p:txBody/a:p/a:pPr",  # Title placeholders
            "//p:ph[@type='body']/p:txBody/a:p/a:pPr"   # Body placeholders
        ],
        odf_xpaths=[
            "//style:master-page",
            "//presentation:page-layout"
        ],
        google_selectors=[
            "layouts.layoutProperties.masterObjectId",
            "layouts.placeholders"
        ],
        required_tokens=[
            "layouts.master.background_color",
            "layouts.title.font_family",
            "layouts.title.font_size",
            "layouts.body.font_family",
            "layouts.body.font_size",
            "layouts.brand.logo_position"
        ],
        optional_tokens=[
            "layouts.master.background_image",
            "layouts.footer.text",
            "layouts.slide_number.position"
        ],
        validation_rules={
            "brand_consistency": True,
            "professional_spacing": True,
            "accessibility_compliance": True
        }
    )

    # Advanced Typography Carriers
    PROFESSIONAL_TYPOGRAPHY = CarrierTypeDefinition(
        name="professional_typography",
        description="EMU-precision typography with kerning and optical spacing",
        ooxml_xpaths=[
            "//a:rPr[@kern]",  # Kerning properties
            "//a:rPr/@sz",     # Font size in EMU
            "//a:pPr/a:lnSpc", # Line spacing
            "//a:pPr/a:spcBef", # Space before
            "//a:pPr/a:spcAft"  # Space after
        ],
        odf_xpaths=[
            "//style:text-properties[@fo:font-size]",
            "//style:paragraph-properties[@fo:line-height]"
        ],
        google_selectors=[
            "textStyle.fontSize",
            "paragraphStyle.lineSpacing",
            "textStyle.weightedFontFamily"
        ],
        required_tokens=[
            "typography.precision.baseline_grid",  # 360 EMU
            "typography.precision.font_size_emu",
            "typography.precision.line_height_emu",
            "typography.precision.kerning_enabled"
        ],
        optional_tokens=[
            "typography.precision.optical_spacing",
            "typography.precision.mathematical_ratios",
            "typography.precision.golden_ratio"
        ],
        validation_rules={
            "emu_baseline_alignment": 360,
            "mathematical_proportions": True,
            "professional_kerning": True,
            "optical_spacing": True
        }
    )


class CarrierTypeRegistry:
    """Registry for managing all carrier type definitions."""
    
    def __init__(self):
        """Initialize the registry with professional carrier types."""
        self.carrier_types = {}
        self._register_professional_types()
    
    def _register_professional_types(self):
        """Register all professional carrier types."""
        professional_types = [
            ProfessionalCarrierTypes.TEXT_HEADING_1,
            ProfessionalCarrierTypes.TEXT_BODY,
            ProfessionalCarrierTypes.TABLE_DEFAULT_STYLE,
            ProfessionalCarrierTypes.SHAPE_DEFAULT_STYLE,
            ProfessionalCarrierTypes.CHART_DEFAULT_STYLE,
            ProfessionalCarrierTypes.THEME_COLOR_SCHEME,
            ProfessionalCarrierTypes.MASTER_SLIDE_LAYOUT,
            ProfessionalCarrierTypes.PROFESSIONAL_TYPOGRAPHY
        ]
        
        for carrier_type in professional_types:
            self.carrier_types[carrier_type.name] = carrier_type
    
    def get_carrier_type(self, name: str) -> Optional[CarrierTypeDefinition]:
        """Get a carrier type by name."""
        return self.carrier_types.get(name)
    
    def get_all_carrier_types(self) -> Dict[str, CarrierTypeDefinition]:
        """Get all registered carrier types."""
        return self.carrier_types.copy()
    
    def get_carrier_types_by_platform(self, platform: str) -> List[CarrierTypeDefinition]:
        """Get carrier types that support a specific platform."""
        platform_carriers = []
        
        for carrier_type in self.carrier_types.values():
            if platform.lower() == "microsoft_office" and carrier_type.ooxml_xpaths:
                platform_carriers.append(carrier_type)
            elif platform.lower() == "libreoffice" and carrier_type.odf_xpaths:
                platform_carriers.append(carrier_type)
            elif platform.lower() == "google_workspace" and carrier_type.google_selectors:
                platform_carriers.append(carrier_type)
        
        return platform_carriers
    
    def validate_design_tokens_for_carrier(
        self, 
        carrier_name: str, 
        design_tokens: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate design tokens against carrier requirements.
        
        Args:
            carrier_name: Name of the carrier type
            design_tokens: Design tokens to validate
            
        Returns:
            Dictionary with validation results
        """
        carrier_type = self.get_carrier_type(carrier_name)
        if not carrier_type:
            return {"valid": False, "error": f"Carrier type '{carrier_name}' not found"}
        
        results = {
            "valid": True,
            "missing_required": [],
            "missing_optional": [],
            "validation_errors": []
        }
        
        # Check required tokens
        for required_token in carrier_type.required_tokens:
            if not self._token_exists(design_tokens, required_token):
                results["missing_required"].append(required_token)
                results["valid"] = False
        
        # Check optional tokens (for completeness)
        for optional_token in carrier_type.optional_tokens:
            if not self._token_exists(design_tokens, optional_token):
                results["missing_optional"].append(optional_token)
        
        # Apply validation rules
        validation_errors = self._validate_rules(carrier_type, design_tokens)
        if validation_errors:
            results["validation_errors"].extend(validation_errors)
            results["valid"] = False
        
        return results
    
    def _token_exists(self, design_tokens: Dict[str, Any], token_path: str) -> bool:
        """Check if a token path exists in the design tokens."""
        keys = token_path.split('.')
        current = design_tokens
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return False
        
        return True
    
    def _validate_rules(
        self, 
        carrier_type: CarrierTypeDefinition, 
        design_tokens: Dict[str, Any]
    ) -> List[str]:
        """Validate design tokens against carrier-specific rules."""
        errors = []
        
        for rule_name, rule_value in carrier_type.validation_rules.items():
            # Example validation rules
            if rule_name == "eliminate_arial":
                # Check that Arial is not used
                font_tokens = self._extract_font_tokens(design_tokens)
                if any("arial" in str(font).lower() for font in font_tokens):
                    errors.append("Arial fonts detected - should use professional typography")
            
            elif rule_name == "wcag_aaa_contrast":
                # Validate color contrast ratios
                colors = self._extract_color_tokens(design_tokens)
                # Implementation would check actual contrast ratios
                pass
            
            elif rule_name == "emu_baseline_alignment":
                # Validate EMU alignment to baseline grid
                emu_values = self._extract_emu_tokens(design_tokens)
                baseline = rule_value
                for emu_val in emu_values:
                    if isinstance(emu_val, (int, float)) and emu_val % baseline != 0:
                        errors.append(f"EMU value {emu_val} not aligned to {baseline} baseline grid")
        
        return errors
    
    def _extract_font_tokens(self, design_tokens: Dict[str, Any]) -> List[str]:
        """Extract all font-related tokens from design tokens."""
        fonts = []
        
        def extract_fonts(obj, key=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if "font" in k.lower():
                        fonts.append(str(v))
                    extract_fonts(v, k)
            elif isinstance(obj, list):
                for item in obj:
                    extract_fonts(item, key)
        
        extract_fonts(design_tokens)
        return fonts
    
    def _extract_color_tokens(self, design_tokens: Dict[str, Any]) -> List[str]:
        """Extract all color tokens from design tokens."""
        colors = []
        
        def extract_colors(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if "color" in k.lower() or k.lower().startswith("#"):
                        colors.append(str(v))
                    extract_colors(v)
            elif isinstance(obj, list):
                for item in obj:
                    extract_colors(item)
        
        extract_colors(design_tokens)
        return colors
    
    def _extract_emu_tokens(self, design_tokens: Dict[str, Any]) -> List[Union[int, float]]:
        """Extract EMU values from design tokens."""
        emu_values = []
        
        def extract_emu(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if "emu" in k.lower() or "size" in k.lower():
                        try:
                            emu_values.append(float(v))
                        except (ValueError, TypeError):
                            pass
                    extract_emu(v)
            elif isinstance(obj, list):
                for item in obj:
                    extract_emu(item)
        
        extract_emu(design_tokens)
        return emu_values

    def export_carrier_types(self, file_path: str):
        """Export all carrier type definitions to JSON."""
        export_data = {}
        
        for name, carrier_type in self.carrier_types.items():
            export_data[name] = {
                "name": carrier_type.name,
                "description": carrier_type.description,
                "ooxml_xpaths": carrier_type.ooxml_xpaths,
                "odf_xpaths": carrier_type.odf_xpaths,
                "google_selectors": carrier_type.google_selectors,
                "required_tokens": carrier_type.required_tokens,
                "optional_tokens": carrier_type.optional_tokens,
                "validation_rules": carrier_type.validation_rules,
                "examples": carrier_type.examples
            }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)


# Example usage and testing
if __name__ == "__main__":
    # Create registry and test
    registry = CarrierTypeRegistry()
    
    print(f"Registered {len(registry.get_all_carrier_types())} professional carrier types:")
    for name, carrier_type in registry.get_all_carrier_types().items():
        print(f"  - {name}: {carrier_type.description}")
    
    # Test design token validation
    sample_tokens = {
        "typography": {
            "body": {
                "font_family": "Segoe UI",
                "font_size": "12pt",
                "line_height": "1.4em",
                "color": "#000000"
            }
        }
    }
    
    validation_result = registry.validate_design_tokens_for_carrier("text_body", sample_tokens)
    print(f"\nValidation result: {validation_result}")