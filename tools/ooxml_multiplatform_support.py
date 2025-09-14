"""
StyleStack Multi-Platform OOXML Inheritance Support

Specialized OOXML inheritance generation for PowerPoint (.potx), Word (.dotx), and Excel (.xltx)
with platform-specific style structures, namespaces, and inheritance patterns.

Features:
- PowerPoint (.potx) style masters with inheritance
- Word (.dotx) paragraph and character style inheritance
- Excel (.xltx) cell style inheritance with proper cascading
- Cross-platform compatibility and consistent behavior
- Platform-specific XML structure generation
- Namespace management for each Office application
"""

import logging
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
from pathlib import Path

try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    import xml.etree.ElementTree as ET
    LXML_AVAILABLE = False

from tools.style_inheritance_core import InheritedTypographyToken, InheritanceMode
from tools.ooxml_inheritance_generator import OOXMLInheritanceGenerator, OOXMLGenerationResult
from tools.ooxml_delta_serializer import OOXMLDeltaSerializer, PropertyDelta

logger = logging.getLogger(__name__)


@dataclass
class PlatformSpecification:
    """Platform-specific OOXML specifications"""
    platform_name: str
    file_extension: str
    primary_namespace: str
    namespace_prefix: str
    style_container: str
    style_element: str
    supported_inheritance: bool
    max_inheritance_depth: Optional[int] = None


class OOXMLPlatformHandler(ABC):
    """Abstract base class for platform-specific OOXML handlers"""

    def __init__(self, delta_serializer: OOXMLDeltaSerializer):
        self.delta_serializer = delta_serializer
        self.platform_spec = self.get_platform_specification()

    @abstractmethod
    def get_platform_specification(self) -> PlatformSpecification:
        """Get platform-specific specifications"""
        pass

    @abstractmethod
    def generate_inheritance_xml(self, token: InheritedTypographyToken,
                               base_style_id: str) -> str:
        """Generate platform-specific inheritance XML"""
        pass

    @abstractmethod
    def generate_complete_xml(self, token: InheritedTypographyToken) -> str:
        """Generate platform-specific complete style XML"""
        pass

    @abstractmethod
    def wrap_styles_in_container(self, style_xmls: List[str]) -> str:
        """Wrap individual styles in platform-specific container"""
        pass

    def validate_platform_compatibility(self, token: InheritedTypographyToken) -> List[str]:
        """Validate token compatibility with platform"""
        issues = []

        if not self.platform_spec.supported_inheritance and token.should_generate_delta():
            issues.append(f"Platform {self.platform_spec.platform_name} does not support inheritance")

        if (self.platform_spec.max_inheritance_depth and
            token.inheritance_depth and
            token.inheritance_depth > self.platform_spec.max_inheritance_depth):
            issues.append(f"Inheritance depth {token.inheritance_depth} exceeds platform limit")

        return issues


class PowerPointOOXMLHandler(OOXMLPlatformHandler):
    """PowerPoint-specific OOXML inheritance handler"""

    def get_platform_specification(self) -> PlatformSpecification:
        return PlatformSpecification(
            platform_name="PowerPoint",
            file_extension=".potx",
            primary_namespace="http://schemas.openxmlformats.org/presentationml/2006/main",
            namespace_prefix="p",
            style_container="p:txStyles",
            style_element="p:titleStyle",
            supported_inheritance=True,
            max_inheritance_depth=5
        )

    def generate_inheritance_xml(self, token: InheritedTypographyToken,
                               base_style_id: str) -> str:
        """Generate PowerPoint text style with inheritance"""
        style_level = self._determine_style_level(token)
        delta_props = self._build_powerpoint_delta_properties(token)

        return f"""<a:lvl{style_level}pPr xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
    <!-- Inherits from: {base_style_id} -->
    <a:defRPr>
{delta_props}
    </a:defRPr>
</a:lvl{style_level}pPr>"""

    def generate_complete_xml(self, token: InheritedTypographyToken) -> str:
        """Generate complete PowerPoint text style"""
        style_level = self._determine_style_level(token)
        complete_props = self._build_powerpoint_complete_properties(token)

        return f"""<a:lvl{style_level}pPr xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
    <a:defRPr>
{complete_props}
    </a:defRPr>
</a:lvl{style_level}pPr>"""

    def wrap_styles_in_container(self, style_xmls: List[str]) -> str:
        """Wrap PowerPoint styles in presentation container"""
        styles_content = '\n'.join(f'    {xml}' for xml in style_xmls)

        return f"""<p:txStyles xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
           xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
    <p:titleStyle>
{styles_content}
    </p:titleStyle>
    <p:bodyStyle>
{styles_content}
    </p:bodyStyle>
    <p:otherStyle>
{styles_content}
    </p:otherStyle>
</p:txStyles>"""

    def generate_slide_master_inheritance(self, tokens: List[InheritedTypographyToken]) -> str:
        """Generate PowerPoint slide master with inheritance-aware text styles"""
        title_styles = []
        body_styles = []
        other_styles = []

        for token in tokens:
            xml = self.generate_inheritance_xml(token, token.base_style or "Normal")

            # Categorize by usage context
            if "title" in token.id.lower():
                title_styles.append(xml)
            elif "body" in token.id.lower() or "paragraph" in token.id.lower():
                body_styles.append(xml)
            else:
                other_styles.append(xml)

        return f"""<p:sldMaster xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
            xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
    <p:txStyles>
        <p:titleStyle>
            {''.join(title_styles)}
        </p:titleStyle>
        <p:bodyStyle>
            {''.join(body_styles)}
        </p:bodyStyle>
        <p:otherStyle>
            {''.join(other_styles)}
        </p:otherStyle>
    </p:txStyles>
</p:sldMaster>"""

    def _determine_style_level(self, token: InheritedTypographyToken) -> int:
        """Determine PowerPoint style level (1-9) from token"""
        # Use inheritance depth or analyze token properties
        if token.inheritance_depth:
            return min(token.inheritance_depth + 1, 9)
        else:
            return 1  # Default to level 1

    def _build_powerpoint_delta_properties(self, token: InheritedTypographyToken) -> str:
        """Build PowerPoint-specific delta properties"""
        props = []

        if token.delta_properties:
            for prop, value in token.delta_properties.items():
                if prop == "fontSize" and value:
                    # PowerPoint uses hundredths of a point
                    points = self._extract_points(value)
                    if points:
                        props.append(f'        <a:sz val="{int(points * 100)}"/>')

                elif prop == "fontFamily" and value:
                    props.append(f'        <a:latin typeface="{value}"/>')
                    props.append(f'        <a:ea typeface="{value}"/>')
                    props.append(f'        <a:cs typeface="{value}"/>')

                elif prop == "fontWeight" and value:
                    if self._is_bold_weight(value):
                        props.append('        <a:b val="1"/>')

                elif prop == "fontStyle" and value == "italic":
                    props.append('        <a:i val="1"/>')

                elif prop == "color" and value:
                    color_hex = self._extract_color_hex(value)
                    if color_hex:
                        props.append(f'        <a:solidFill><a:srgbClr val="{color_hex}"/></a:solidFill>')

        return '\n'.join(props)

    def _build_powerpoint_complete_properties(self, token: InheritedTypographyToken) -> str:
        """Build PowerPoint-specific complete properties"""
        props = []

        # Font family
        if token.font_family:
            props.append(f'        <a:latin typeface="{token.font_family}"/>')
            props.append(f'        <a:ea typeface="{token.font_family}"/>')
            props.append(f'        <a:cs typeface="{token.font_family}"/>')

        # Font size
        if token.font_size:
            points = self._extract_points(token.font_size)
            if points:
                props.append(f'        <a:sz val="{int(points * 100)}"/>')

        # Font weight
        if token.font_weight and self._is_bold_weight(token.font_weight):
            props.append('        <a:b val="1"/>')

        # Font style
        if token.font_style == "italic":
            props.append('        <a:i val="1"/>')

        return '\n'.join(props)

    def _extract_points(self, size_value: Any) -> Optional[float]:
        """Extract numeric points from size value"""
        if isinstance(size_value, str) and size_value.endswith('pt'):
            try:
                return float(size_value[:-2])
            except ValueError:
                return None
        elif isinstance(size_value, (int, float)):
            return float(size_value)
        return None

    def _is_bold_weight(self, weight: Any) -> bool:
        """Check if weight represents bold"""
        if isinstance(weight, int):
            return weight >= 600
        elif isinstance(weight, str):
            return weight.lower() in ["bold", "semibold", "extrabold"]
        return False

    def _extract_color_hex(self, color_value: Any) -> Optional[str]:
        """Extract hex color value"""
        if isinstance(color_value, str):
            if color_value.startswith('#'):
                return color_value[1:]
            elif len(color_value) == 6 and all(c in '0123456789ABCDEFabcdef' for c in color_value):
                return color_value.upper()
        return None


class WordOOXMLHandler(OOXMLPlatformHandler):
    """Word-specific OOXML inheritance handler"""

    def get_platform_specification(self) -> PlatformSpecification:
        return PlatformSpecification(
            platform_name="Word",
            file_extension=".dotx",
            primary_namespace="http://schemas.openxmlformats.org/wordprocessingml/2006/main",
            namespace_prefix="w",
            style_container="w:styles",
            style_element="w:style",
            supported_inheritance=True,
            max_inheritance_depth=10
        )

    def generate_inheritance_xml(self, token: InheritedTypographyToken,
                               base_style_id: str) -> str:
        """Generate Word paragraph style with inheritance"""
        style_id = self._sanitize_style_id(token.id)
        style_name = token.id.replace('_', ' ').title()
        style_type = self._determine_word_style_type(token)

        delta_props = self._build_word_delta_properties(token)

        return f"""<w:style w:type="{style_type}" w:styleId="{style_id}">
    <w:name w:val="{style_name}"/>
    <w:basedOn w:val="{base_style_id}"/>
{delta_props}
</w:style>"""

    def generate_complete_xml(self, token: InheritedTypographyToken) -> str:
        """Generate complete Word style"""
        style_id = self._sanitize_style_id(token.id)
        style_name = token.id.replace('_', ' ').title()
        style_type = self._determine_word_style_type(token)

        complete_props = self._build_word_complete_properties(token)

        return f"""<w:style w:type="{style_type}" w:styleId="{style_id}">
    <w:name w:val="{style_name}"/>
{complete_props}
</w:style>"""

    def wrap_styles_in_container(self, style_xmls: List[str]) -> str:
        """Wrap Word styles in styles container"""
        styles_content = '\n'.join(f'    {xml}' for xml in style_xmls)

        return f"""<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
{styles_content}
</w:styles>"""

    def _determine_word_style_type(self, token: InheritedTypographyToken) -> str:
        """Determine Word style type (paragraph, character, table, numbering)"""
        # Analyze token properties to determine appropriate type
        if hasattr(token, 'line_height') and token.line_height:
            return "paragraph"
        else:
            return "character"

    def _build_word_delta_properties(self, token: InheritedTypographyToken) -> str:
        """Build Word-specific delta properties"""
        rpr_props = []
        ppr_props = []

        if token.delta_properties:
            for prop, value in token.delta_properties.items():
                # Run properties (rPr)
                if prop == "fontFamily" and value:
                    rpr_props.append(f'        <w:rFonts w:ascii="{value}" w:hAnsi="{value}"/>')

                elif prop == "fontSize" and value:
                    half_points = self._points_to_half_points(value)
                    if half_points:
                        rpr_props.append(f'        <w:sz w:val="{half_points}"/>')

                elif prop == "fontWeight" and value:
                    if self._is_bold_weight(value):
                        rpr_props.append('        <w:b/>')

                elif prop == "fontStyle" and value == "italic":
                    rpr_props.append('        <w:i/>')

                elif prop == "letterSpacing" and value:
                    twentieths = self._em_to_twentieths(value)
                    if twentieths:
                        rpr_props.append(f'        <w:spacing w:val="{twentieths}"/>')

                # Paragraph properties (pPr)
                elif prop == "lineHeight" and value:
                    emu_value = self._line_height_to_emu(value, token.font_size)
                    if emu_value:
                        ppr_props.append(f'        <w:spacing w:line="{emu_value}" w:lineRule="exact"/>')

        # Build properties sections
        props_sections = []
        if rpr_props:
            props_sections.append(f"    <w:rPr>\n{''.join('\n' + prop for prop in rpr_props)}\n    </w:rPr>")
        if ppr_props:
            props_sections.append(f"    <w:pPr>\n{''.join('\n' + prop for prop in ppr_props)}\n    </w:pPr>")

        return '\n'.join(props_sections)

    def _build_word_complete_properties(self, token: InheritedTypographyToken) -> str:
        """Build Word-specific complete properties"""
        # Similar to delta properties but include all properties
        return self._build_word_delta_properties(token)  # Simplified for now

    def _sanitize_style_id(self, style_id: str) -> str:
        """Sanitize style ID for Word compatibility"""
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', style_id)
        if sanitized and not (sanitized[0].isalpha() or sanitized[0] == '_'):
            sanitized = f"style_{sanitized}"
        return sanitized or "default_style"

    def _points_to_half_points(self, size_value: Any) -> Optional[int]:
        """Convert points to Word half-points format"""
        if isinstance(size_value, str) and size_value.endswith('pt'):
            try:
                points = float(size_value[:-2])
                return int(points * 2)
            except ValueError:
                return None
        return None

    def _em_to_twentieths(self, spacing_value: Any) -> Optional[int]:
        """Convert em spacing to twentieths of a point"""
        if isinstance(spacing_value, str) and spacing_value.endswith('em'):
            try:
                em_value = float(spacing_value[:-2])
                # Rough conversion: 1em ≈ 12pt
                return int(em_value * 12 * 20)
            except ValueError:
                return None
        return None

    def _line_height_to_emu(self, line_height: Any, font_size: Any = None) -> Optional[int]:
        """Convert line height to EMU format"""
        if isinstance(line_height, str) and line_height.endswith('pt'):
            try:
                points = float(line_height[:-2])
                return int(points * 12700)  # EMU per point
            except ValueError:
                return None
        elif isinstance(line_height, (int, float)) and font_size:
            # Relative line height
            font_points = self._extract_points(font_size) or 12
            return int(line_height * font_points * 12700)
        return None

    def _is_bold_weight(self, weight: Any) -> bool:
        """Check if weight represents bold"""
        if isinstance(weight, int):
            return weight >= 600
        elif isinstance(weight, str):
            return weight.lower() in ["bold", "semibold", "extrabold"]
        return False

    def _extract_points(self, size_value: Any) -> Optional[float]:
        """Extract numeric points from size value"""
        if isinstance(size_value, str) and size_value.endswith('pt'):
            try:
                return float(size_value[:-2])
            except ValueError:
                return None
        elif isinstance(size_value, (int, float)):
            return float(size_value)
        return None


class ExcelOOXMLHandler(OOXMLPlatformHandler):
    """Excel-specific OOXML inheritance handler"""

    def get_platform_specification(self) -> PlatformSpecification:
        return PlatformSpecification(
            platform_name="Excel",
            file_extension=".xltx",
            primary_namespace="http://schemas.openxmlformats.org/spreadsheetml/2006/main",
            namespace_prefix="x",
            style_container="cellXfs",
            style_element="xf",
            supported_inheritance=False,  # Excel has limited inheritance support
            max_inheritance_depth=1
        )

    def generate_inheritance_xml(self, token: InheritedTypographyToken,
                               base_style_id: str) -> str:
        """Generate Excel cell style with reference to base style"""
        # Excel uses style references rather than true inheritance
        delta_props = self._build_excel_delta_properties(token)

        return f"""<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0">
    <!-- Based on: {base_style_id} -->
{delta_props}
</xf>"""

    def generate_complete_xml(self, token: InheritedTypographyToken) -> str:
        """Generate complete Excel cell style"""
        complete_props = self._build_excel_complete_properties(token)

        return f"""<xf numFmtId="0" fontId="0" fillId="0" borderId="0">
{complete_props}
</xf>"""

    def wrap_styles_in_container(self, style_xmls: List[str]) -> str:
        """Wrap Excel styles in styleSheet container"""
        styles_content = '\n'.join(f'    {xml}' for xml in style_xmls)

        return f"""<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
    <fonts count="{len(style_xmls)}">
        <!-- Font definitions go here -->
    </fonts>
    <cellXfs count="{len(style_xmls)}">
{styles_content}
    </cellXfs>
</styleSheet>"""

    def _build_excel_delta_properties(self, token: InheritedTypographyToken) -> str:
        """Build Excel-specific delta properties"""
        props = []

        if token.delta_properties:
            # Excel properties are more limited
            if any(prop in token.delta_properties for prop in ["fontWeight", "fontStyle"]):
                props.append('    <applyFont val="1"/>')

        return '\n'.join(props)

    def _build_excel_complete_properties(self, token: InheritedTypographyToken) -> str:
        """Build Excel-specific complete properties"""
        props = []

        # Excel cell formatting is primarily handled through separate font, fill, and border definitions
        if any([token.font_family, token.font_size, token.font_weight, token.font_style]):
            props.append('    <applyFont val="1"/>')

        return '\n'.join(props)


class MultiPlatformOOXMLGenerator:
    """Multi-platform OOXML inheritance generator"""

    def __init__(self):
        """Initialize multi-platform generator"""
        self.delta_serializer = OOXMLDeltaSerializer()
        self.handlers = {
            "powerpoint": PowerPointOOXMLHandler(self.delta_serializer),
            "word": WordOOXMLHandler(self.delta_serializer),
            "excel": ExcelOOXMLHandler(self.delta_serializer)
        }

        logger.info("🎨 Initialized Multi-Platform OOXML Generator")

    def generate_for_platform(self, tokens: List[InheritedTypographyToken],
                            platform: str) -> str:
        """Generate OOXML for specific platform"""
        if platform not in self.handlers:
            raise ValueError(f"Unsupported platform: {platform}")

        handler = self.handlers[platform]
        style_xmls = []

        for token in tokens:
            # Validate platform compatibility
            issues = handler.validate_platform_compatibility(token)
            if issues:
                logger.warning(f"Platform compatibility issues for {token.id}: {issues}")

            # Generate appropriate XML
            if token.should_generate_delta() and token.base_style:
                xml = handler.generate_inheritance_xml(token, token.base_style)
            else:
                xml = handler.generate_complete_xml(token)

            style_xmls.append(xml)

        return handler.wrap_styles_in_container(style_xmls)

    def generate_for_all_platforms(self, tokens: List[InheritedTypographyToken]) -> Dict[str, str]:
        """Generate OOXML for all supported platforms"""
        results = {}

        for platform_name in self.handlers.keys():
            try:
                results[platform_name] = self.generate_for_platform(tokens, platform_name)
            except Exception as e:
                logger.error(f"Failed to generate OOXML for {platform_name}: {e}")
                results[platform_name] = f"<!-- Error generating {platform_name} OOXML: {e} -->"

        return results

    def get_platform_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Get capabilities summary for all platforms"""
        capabilities = {}

        for platform_name, handler in self.handlers.items():
            spec = handler.platform_spec
            capabilities[platform_name] = {
                "file_extension": spec.file_extension,
                "supports_inheritance": spec.supported_inheritance,
                "max_inheritance_depth": spec.max_inheritance_depth,
                "primary_namespace": spec.primary_namespace,
                "style_container": spec.style_container
            }

        return capabilities


# Export main classes
__all__ = [
    'MultiPlatformOOXMLGenerator',
    'PowerPointOOXMLHandler',
    'WordOOXMLHandler',
    'ExcelOOXMLHandler',
    'OOXMLPlatformHandler',
    'PlatformSpecification'
]