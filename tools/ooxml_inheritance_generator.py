"""
StyleStack OOXML Inheritance Generator

Generates OOXML style definitions with inheritance support including basedOn references,
delta-only property serialization, and multi-platform compatibility for PowerPoint,
Word, and Excel templates.

Features:
- OOXML inheritance structure generation with <w:basedOn> references
- Delta-only property serialization for efficient inheritance
- Multi-platform support (PowerPoint, Word, Excel)
- OOXML namespace handling and XML well-formedness validation
- Style ID sanitization for OOXML compatibility
- Integration with StyleStack inheritance resolution system
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    import xml.etree.ElementTree as ET
    LXML_AVAILABLE = False

from tools.style_inheritance_core import InheritedTypographyToken, InheritanceMode
from tools.ooxml_delta_serializer import OOXMLDeltaSerializer, OOXMLPropertyTarget

logger = logging.getLogger(__name__)


class OOXMLPlatform(Enum):
    """Supported OOXML platforms"""
    WORD = "word"
    POWERPOINT = "powerpoint"
    EXCEL = "excel"


@dataclass
class OOXMLNamespaces:
    """OOXML namespace definitions for different platforms"""
    word: Dict[str, str]
    powerpoint: Dict[str, str]
    excel: Dict[str, str]
    common: Dict[str, str]

    @classmethod
    def get_default_namespaces(cls) -> 'OOXMLNamespaces':
        """Get default OOXML namespaces for all platforms"""
        return cls(
            word={
                "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
                "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
                "w15": "http://schemas.microsoft.com/office/word/2012/wordml"
            },
            powerpoint={
                "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
                "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
                "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
            },
            excel={
                "x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
                "x14": "http://schemas.microsoft.com/office/spreadsheetml/2009/9/main",
                "x15": "http://schemas.microsoft.com/office/spreadsheetml/2010/11/main"
            },
            common={
                "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
                "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
                "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006"
            }
        )


@dataclass
class OOXMLGenerationResult:
    """Result of OOXML generation with validation info"""
    xml_content: str
    is_valid: bool
    has_based_on: bool
    has_delta_properties: bool
    validation_errors: List[str]
    platform: str
    style_id: str


class OOXMLInheritanceGenerator:
    """OOXML Generation with Inheritance Support"""

    def __init__(self, inheritance_resolver=None, use_lxml: bool = None):
        """Initialize OOXML inheritance generator

        Args:
            inheritance_resolver: InheritanceResolver instance for dependency resolution
            use_lxml: Force lxml usage (True), ElementTree (False), or auto-detect (None)
        """
        self.inheritance_resolver = inheritance_resolver
        self.use_lxml = use_lxml if use_lxml is not None else LXML_AVAILABLE
        self.namespaces = OOXMLNamespaces.get_default_namespaces()
        self.delta_serializer = OOXMLDeltaSerializer()

        # EMU conversion constants
        self.EMU_PER_POINT = 12700
        self.HALF_POINTS_PER_POINT = 2

        logger.info(f"🎨 Initialized OOXML Inheritance Generator (lxml: {self.use_lxml})")

    def generate_style_xml_with_inheritance(self, token: InheritedTypographyToken,
                                          platform: str = "word") -> OOXMLGenerationResult:
        """Generate OOXML style XML with inheritance support

        Args:
            token: InheritedTypographyToken with inheritance metadata
            platform: Target platform ('word', 'powerpoint', 'excel')

        Returns:
            OOXMLGenerationResult with generated XML and validation info
        """
        try:
            platform_enum = OOXMLPlatform(platform.lower())
        except ValueError:
            raise ValueError(f"Unsupported platform: {platform}")

        # Generate appropriate style XML based on inheritance mode
        if token.should_generate_delta() and token.base_style:
            xml_content = self._generate_delta_style_xml(token, platform_enum)
        else:
            xml_content = self._generate_complete_style_xml(token, platform_enum)

        # Validate generated XML
        validation = self.validate_ooxml_inheritance_structure(xml_content)

        return OOXMLGenerationResult(
            xml_content=xml_content,
            is_valid=validation["is_valid"],
            has_based_on=validation["has_based_on"],
            has_delta_properties=validation["has_delta_properties"],
            validation_errors=validation["validation_errors"],
            platform=platform,
            style_id=self._sanitize_style_id(token.id)
        )

    def _generate_delta_style_xml(self, token: InheritedTypographyToken,
                                platform: OOXMLPlatform) -> str:
        """Generate delta-only style XML with basedOn reference"""
        base_id = self._sanitize_style_id(token.base_style)
        style_id = self._sanitize_style_id(token.id)
        style_name = token.id.replace('_', ' ').title()

        if platform == OOXMLPlatform.WORD:
            return self._generate_word_delta_style(style_id, style_name, base_id, token)
        elif platform == OOXMLPlatform.POWERPOINT:
            return self._generate_powerpoint_delta_style(style_id, style_name, base_id, token)
        elif platform == OOXMLPlatform.EXCEL:
            return self._generate_excel_delta_style(style_id, style_name, base_id, token)
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    def _generate_complete_style_xml(self, token: InheritedTypographyToken,
                                   platform: OOXMLPlatform) -> str:
        """Generate complete style XML without inheritance"""
        style_id = self._sanitize_style_id(token.id)
        style_name = token.id.replace('_', ' ').title()

        if platform == OOXMLPlatform.WORD:
            return self._generate_word_complete_style(style_id, style_name, token)
        elif platform == OOXMLPlatform.POWERPOINT:
            return self._generate_powerpoint_complete_style(style_id, style_name, token)
        elif platform == OOXMLPlatform.EXCEL:
            return self._generate_excel_complete_style(style_id, style_name, token)
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    def _generate_word_delta_style(self, style_id: str, style_name: str,
                                 base_id: str, token: InheritedTypographyToken) -> str:
        """Generate Word paragraph style with delta properties using delta serializer"""
        # Calculate property deltas using the advanced serializer
        deltas = self.delta_serializer.calculate_property_deltas(
            base_token=None,  # Would need to resolve base token
            base_style=None,  # Would need to resolve base style
            target_token=token
        )

        # Serialize deltas to OOXML elements
        ooxml_elements = self.delta_serializer.serialize_deltas_to_ooxml(deltas, "word")

        # Build delta properties XML
        delta_xml_parts = []

        # Add run properties (rPr)
        if ooxml_elements[OOXMLPropertyTarget.RUN_PROPERTIES]:
            rpr_content = '\n        '.join(ooxml_elements[OOXMLPropertyTarget.RUN_PROPERTIES])
            delta_xml_parts.append(f"    <w:rPr>\n        {rpr_content}\n    </w:rPr>")

        # Add paragraph properties (pPr)
        if ooxml_elements[OOXMLPropertyTarget.PARAGRAPH_PROPERTIES]:
            ppr_content = '\n        '.join(ooxml_elements[OOXMLPropertyTarget.PARAGRAPH_PROPERTIES])
            delta_xml_parts.append(f"    <w:pPr>\n        {ppr_content}\n    </w:pPr>")

        # Fallback to legacy method if no deltas calculated
        if not delta_xml_parts and token.delta_properties:
            delta_xml_parts = self._generate_legacy_delta_properties(token)

        delta_properties_xml = '\n'.join(delta_xml_parts)

        return f"""<w:style w:type="paragraph" w:styleId="{style_id}">
    <w:name w:val="{style_name}"/>
    <w:basedOn w:val="{base_id}"/>
{delta_properties_xml}
</w:style>"""

    def _generate_legacy_delta_properties(self, token: InheritedTypographyToken) -> List[str]:
        """Generate delta properties using legacy method as fallback"""
        delta_xml_parts = []

        if token.delta_properties:
            rpr_parts = []
            ppr_parts = []

            for prop, value in token.delta_properties.items():
                rpr_part = self._convert_property_to_word_rpr(prop, value)
                if rpr_part:
                    rpr_parts.append(rpr_part)

                ppr_part = self._convert_property_to_word_ppr(prop, value)
                if ppr_part:
                    ppr_parts.append(ppr_part)

            if rpr_parts:
                delta_xml_parts.append(f"    <w:rPr>{''.join(rpr_parts)}</w:rPr>")
            if ppr_parts:
                delta_xml_parts.append(f"    <w:pPr>{''.join(ppr_parts)}</w:pPr>")

        return delta_xml_parts

    def _generate_word_complete_style(self, style_id: str, style_name: str,
                                    token: InheritedTypographyToken) -> str:
        """Generate complete Word paragraph style"""
        rpr_parts = []
        ppr_parts = []

        # Add all properties (not just deltas)
        properties = {
            "fontFamily": token.font_family,
            "fontSize": token.font_size,
            "fontWeight": token.font_weight,
            "fontStyle": token.font_style,
            "letterSpacing": token.letter_spacing,
            "lineHeight": token.line_height
        }

        for prop, value in properties.items():
            if value is not None:
                rpr_part = self._convert_property_to_word_rpr(prop, value)
                if rpr_part:
                    rpr_parts.append(rpr_part)

                ppr_part = self._convert_property_to_word_ppr(prop, value)
                if ppr_part:
                    ppr_parts.append(ppr_part)

        properties_xml_parts = []
        if rpr_parts:
            properties_xml_parts.append(f"    <w:rPr>{''.join(rpr_parts)}</w:rPr>")
        if ppr_parts:
            properties_xml_parts.append(f"    <w:pPr>{''.join(ppr_parts)}</w:pPr>")

        properties_xml = '\n'.join(properties_xml_parts)

        return f"""<w:style w:type="paragraph" w:styleId="{style_id}">
    <w:name w:val="{style_name}"/>
{properties_xml}
</w:style>"""

    def _convert_property_to_word_rpr(self, prop: str, value: Any) -> Optional[str]:
        """Convert typography property to Word run properties (rPr) XML"""
        if prop == "fontFamily" and value:
            return f'\n        <w:rFonts w:ascii="{value}" w:hAnsi="{value}"/>'
        elif prop == "fontSize" and value:
            half_points = self._convert_size_to_half_points(value)
            if half_points:
                return f'\n        <w:sz w:val="{half_points}"/>'
        elif prop == "fontWeight" and value:
            if isinstance(value, int) and value >= 600:
                return '\n        <w:b/>'
            elif value in ["bold", "semibold", "extrabold"]:
                return '\n        <w:b/>'
        elif prop == "fontStyle" and value == "italic":
            return '\n        <w:i/>'
        elif prop == "letterSpacing" and value:
            # Convert letter spacing to twentieths of a point
            if isinstance(value, str) and value.endswith('em'):
                em_value = float(value[:-2])
                # Rough conversion: 1em ≈ 12pt for letter spacing
                twentieths = int(em_value * 12 * 20)
                return f'\n        <w:spacing w:val="{twentieths}"/>'

        return None

    def _convert_property_to_word_ppr(self, prop: str, value: Any) -> Optional[str]:
        """Convert typography property to Word paragraph properties (pPr) XML"""
        if prop == "lineHeight" and value:
            if isinstance(value, (int, float)):
                # Relative line height (e.g., 1.4) - convert to line rule
                if token_font_size_emu := getattr(self, '_current_token_font_size_emu', None):
                    line_emu = int(token_font_size_emu * value)
                    return f'\n        <w:spacing w:line="{line_emu}" w:lineRule="exact"/>'
            elif isinstance(value, str) and value.endswith('pt'):
                # Absolute line height
                pt_value = float(value[:-2])
                line_emu = int(pt_value * self.EMU_PER_POINT)
                return f'\n        <w:spacing w:line="{line_emu}" w:lineRule="exact"/>'

        return None

    def _generate_powerpoint_delta_style(self, style_id: str, style_name: str,
                                       base_id: str, token: InheritedTypographyToken) -> str:
        """Generate PowerPoint text style with delta properties"""
        # PowerPoint uses different structure - placeholder implementation
        delta_properties = self._build_powerpoint_delta_properties(token.delta_properties or {})

        return f"""<a:lvl1pPr xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
    <!-- PowerPoint style: {style_name} based on {base_id} -->
    <a:defRPr>
{delta_properties}
    </a:defRPr>
</a:lvl1pPr>"""

    def _generate_powerpoint_complete_style(self, style_id: str, style_name: str,
                                          token: InheritedTypographyToken) -> str:
        """Generate complete PowerPoint text style"""
        properties = self._build_powerpoint_complete_properties(token)

        return f"""<a:lvl1pPr xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
    <!-- PowerPoint complete style: {style_name} -->
    <a:defRPr>
{properties}
    </a:defRPr>
</a:lvl1pPr>"""

    def _generate_excel_delta_style(self, style_id: str, style_name: str,
                                  base_id: str, token: InheritedTypographyToken) -> str:
        """Generate Excel cell style with delta properties"""
        delta_properties = self._build_excel_delta_properties(token.delta_properties or {})

        return f"""<cellXfs xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0">
        <!-- Excel style: {style_name} based on {base_id} -->
{delta_properties}
    </xf>
</cellXfs>"""

    def _generate_excel_complete_style(self, style_id: str, style_name: str,
                                     token: InheritedTypographyToken) -> str:
        """Generate complete Excel cell style"""
        properties = self._build_excel_complete_properties(token)

        return f"""<cellXfs xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0">
        <!-- Excel complete style: {style_name} -->
{properties}
    </xf>
</cellXfs>"""

    def _build_powerpoint_delta_properties(self, delta_properties: Dict[str, Any]) -> str:
        """Build PowerPoint-specific delta properties XML"""
        parts = []
        for prop, value in delta_properties.items():
            if prop == "fontSize" and value:
                # PowerPoint uses hundredths of a point
                points = self._extract_points_value(value)
                if points:
                    hundredths = int(points * 100)
                    parts.append(f'        <a:sz val="{hundredths}"/>')
            elif prop == "fontFamily" and value:
                parts.append(f'        <a:latin typeface="{value}"/>')
            elif prop == "fontWeight" and value:
                if isinstance(value, int) and value >= 600:
                    parts.append('        <a:b val="1"/>')

        return '\n'.join(parts)

    def _build_powerpoint_complete_properties(self, token: InheritedTypographyToken) -> str:
        """Build PowerPoint-specific complete properties XML"""
        parts = []
        if token.font_size:
            points = self._extract_points_value(token.font_size)
            if points:
                hundredths = int(points * 100)
                parts.append(f'        <a:sz val="{hundredths}"/>')

        if token.font_family:
            parts.append(f'        <a:latin typeface="{token.font_family}"/>')

        if token.font_weight and isinstance(token.font_weight, int) and token.font_weight >= 600:
            parts.append('        <a:b val="1"/>')

        return '\n'.join(parts)

    def _build_excel_delta_properties(self, delta_properties: Dict[str, Any]) -> str:
        """Build Excel-specific delta properties XML"""
        parts = []
        for prop, value in delta_properties.items():
            if prop == "fontWeight" and value:
                if isinstance(value, int) and value >= 600:
                    parts.append('        <font><b/></font>')

        return '\n'.join(parts)

    def _build_excel_complete_properties(self, token: InheritedTypographyToken) -> str:
        """Build Excel-specific complete properties XML"""
        parts = []
        if token.font_weight and isinstance(token.font_weight, int) and token.font_weight >= 600:
            parts.append('        <font><b/></font>')

        return '\n'.join(parts)

    def _convert_size_to_half_points(self, size_value: Any) -> Optional[int]:
        """Convert size value to Word half-points format"""
        if isinstance(size_value, str) and size_value.endswith('pt'):
            try:
                points = float(size_value[:-2])
                return int(points * self.HALF_POINTS_PER_POINT)
            except ValueError:
                return None
        return None

    def _extract_points_value(self, size_value: Any) -> Optional[float]:
        """Extract numeric points value from size string"""
        if isinstance(size_value, str) and size_value.endswith('pt'):
            try:
                return float(size_value[:-2])
            except ValueError:
                return None
        elif isinstance(size_value, (int, float)):
            return float(size_value)
        return None

    def _sanitize_style_id(self, style_id: str) -> str:
        """Sanitize style ID for OOXML compatibility"""
        # Replace dots and spaces with underscores
        sanitized = style_id.replace(".", "_").replace(" ", "_")
        # Remove any characters that aren't alphanumeric or underscore
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '', sanitized)
        # Ensure it starts with a letter or underscore
        if sanitized and not (sanitized[0].isalpha() or sanitized[0] == '_'):
            sanitized = f"style_{sanitized}"
        return sanitized or "default_style"

    def validate_ooxml_inheritance_structure(self, xml_content: str) -> Dict[str, Any]:
        """Validate OOXML inheritance structure"""
        validation_errors = []
        is_valid = True

        try:
            # Test XML well-formedness
            if self.use_lxml and LXML_AVAILABLE:
                etree.fromstring(xml_content.encode('utf-8'))
            else:
                ET.fromstring(xml_content)
        except Exception as e:
            validation_errors.append(f"XML syntax error: {e}")
            is_valid = False

        # Check for inheritance markers
        has_based_on = "basedOn" in xml_content
        has_delta_properties = any(tag in xml_content for tag in ["rPr", "pPr", "defRPr", "font"])

        # Additional structural validations
        if has_based_on and not re.search(r'w:basedOn\s+w:val="\w+"', xml_content):
            validation_errors.append("basedOn reference format is invalid")
            is_valid = False

        return {
            "is_valid": is_valid,
            "has_based_on": has_based_on,
            "has_delta_properties": has_delta_properties,
            "validation_errors": validation_errors
        }

    def generate_style_sheet_with_inheritance(self, tokens: List[InheritedTypographyToken],
                                            platform: str = "word") -> str:
        """Generate complete OOXML style sheet with inheritance hierarchy"""
        style_xmls = []

        # Sort tokens by inheritance depth to ensure proper ordering
        sorted_tokens = sorted(tokens, key=lambda t: t.inheritance_depth or 0)

        for token in sorted_tokens:
            result = self.generate_style_xml_with_inheritance(token, platform)
            if result.is_valid:
                style_xmls.append(result.xml_content)
            else:
                logger.warning(f"Invalid OOXML generated for token {token.id}: {result.validation_errors}")

        # Wrap in appropriate platform-specific container
        return self._wrap_styles_in_container(style_xmls, platform)

    def _wrap_styles_in_container(self, style_xmls: List[str], platform: str) -> str:
        """Wrap individual style XMLs in platform-specific container"""
        styles_content = '\n'.join(style_xmls)

        if platform.lower() == "word":
            return f"""<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
{styles_content}
</w:styles>"""
        elif platform.lower() == "powerpoint":
            return f"""<p:txStyles xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
{styles_content}
</p:txStyles>"""
        elif platform.lower() == "excel":
            return f"""<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
{styles_content}
</styleSheet>"""
        else:
            return styles_content


# Export main classes
__all__ = [
    'OOXMLInheritanceGenerator',
    'OOXMLPlatform',
    'OOXMLNamespaces',
    'OOXMLGenerationResult'
]