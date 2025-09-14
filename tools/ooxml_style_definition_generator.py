"""
StyleStack Enhanced OOXML Style Definition Generator

Advanced OOXML style definition generation with inheritance-aware style ordering,
style naming conventions, and parent style registration for correct resolution in Office.

Features:
- Inheritance-aware style definition XML generation
- Parent style registration in OOXML style sheets
- Style ordering for correct resolution in Office applications
- Style naming conventions that reflect inheritance relationships
- Integration with existing OOXMLProcessor and template systems
- Style ID generation and reference management for inheritance
- Cross-platform style sheet generation (Word, PowerPoint, Excel)
"""

import logging
import re
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path
from collections import OrderedDict

try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    import xml.etree.ElementTree as ET
    LXML_AVAILABLE = False

from tools.style_inheritance_core import (
    InheritedTypographyToken, BaseStyleDefinition, InheritanceMode
)
from tools.ooxml_inheritance_generator import OOXMLInheritanceGenerator, OOXMLPlatform
from tools.ooxml_delta_serializer import OOXMLDeltaSerializer

logger = logging.getLogger(__name__)


@dataclass
class StyleDefinition:
    """Complete OOXML style definition with inheritance metadata"""
    style_id: str
    style_name: str
    style_type: str  # "paragraph", "character", "table", "numbering"
    platform: str
    xml_content: str
    base_style_id: Optional[str] = None
    inheritance_depth: int = 0
    has_delta_properties: bool = False
    dependencies: List[str] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)


@dataclass
class StyleRegistry:
    """Registry for managing style definitions with dependency tracking"""
    styles: OrderedDict[str, StyleDefinition] = field(default_factory=OrderedDict)
    dependencies: Dict[str, Set[str]] = field(default_factory=dict)
    inheritance_chains: Dict[str, List[str]] = field(default_factory=dict)

    def add_style(self, style: StyleDefinition):
        """Add style to registry with dependency tracking"""
        self.styles[style.style_id] = style

        # Track dependencies
        if style.base_style_id:
            if style.style_id not in self.dependencies:
                self.dependencies[style.style_id] = set()
            self.dependencies[style.style_id].add(style.base_style_id)

            # Update inheritance chain
            base_chain = self.inheritance_chains.get(style.base_style_id, [style.base_style_id])
            self.inheritance_chains[style.style_id] = base_chain + [style.style_id]

    def get_sorted_styles(self) -> List[StyleDefinition]:
        """Get styles sorted by inheritance depth for proper OOXML ordering"""
        return sorted(self.styles.values(), key=lambda s: (s.inheritance_depth, s.style_id))

    def validate_dependencies(self) -> List[str]:
        """Validate all style dependencies are satisfied"""
        errors = []
        for style_id, deps in self.dependencies.items():
            for dep in deps:
                if dep not in self.styles and not self._is_builtin_style(dep):
                    errors.append(f"Style '{style_id}' depends on missing style '{dep}'")
        return errors

    def _is_builtin_style(self, style_id: str) -> bool:
        """Check if style is a built-in Office style"""
        builtin_styles = {"Normal", "Heading1", "Heading2", "Heading3", "Title", "DefaultParagraphFont"}
        return style_id in builtin_styles


class StyleNamingConventions:
    """Style naming conventions that reflect inheritance relationships"""

    @staticmethod
    def generate_style_name(token: InheritedTypographyToken, reflect_inheritance: bool = True) -> str:
        """Generate human-readable style name from token"""
        base_name = token.id.replace('_', ' ').replace('.', ' ').title()

        if reflect_inheritance and token.base_style and token.inheritance_depth > 0:
            # Add inheritance indicator for clarity
            base_style_name = token.base_style.replace('_', ' ').title()
            return f"{base_name} (from {base_style_name})"

        return base_name

    @staticmethod
    def generate_style_id(token: InheritedTypographyToken,
                         platform: str = "word",
                         avoid_conflicts: bool = True) -> str:
        """Generate OOXML-compatible style ID from token"""
        # Base ID from token
        base_id = re.sub(r'[^a-zA-Z0-9_]', '_', token.id)

        # Ensure starts with letter or underscore
        if base_id and not (base_id[0].isalpha() or base_id[0] == '_'):
            base_id = f"style_{base_id}"

        # Add platform prefix if needed for uniqueness
        if avoid_conflicts and platform != "word":
            base_id = f"{platform}_{base_id}"

        return base_id or "default_style"

    @staticmethod
    def suggest_inheritance_hierarchy_names(tokens: List[InheritedTypographyToken]) -> Dict[str, str]:
        """Suggest consistent naming for entire inheritance hierarchy"""
        suggestions = {}

        # Group by inheritance chains
        chains = {}
        for token in tokens:
            if token.inheritance_chain:
                root = token.inheritance_chain[0]
                if root not in chains:
                    chains[root] = []
                chains[root].append(token)

        # Generate consistent names for each chain
        for root, chain_tokens in chains.items():
            # Sort by inheritance depth
            chain_tokens.sort(key=lambda t: t.inheritance_depth or 0)

            for i, token in enumerate(chain_tokens):
                if i == 0:
                    # Root of chain
                    suggestions[token.id] = StyleNamingConventions.generate_style_name(token, False)
                else:
                    # Derived styles
                    level_indicator = f"Level {i + 1}" if i > 2 else ["", "Bold", "Emphasis", "Strong"][min(i, 3)]
                    base_name = suggestions.get(chain_tokens[0].id, "Base")
                    suggestions[token.id] = f"{base_name} {level_indicator}".strip()

        return suggestions


class OOXMLStyleDefinitionGenerator:
    """Enhanced OOXML style definition generator with inheritance support"""

    def __init__(self, inheritance_generator: Optional[OOXMLInheritanceGenerator] = None):
        """Initialize enhanced style definition generator"""
        self.inheritance_generator = inheritance_generator or OOXMLInheritanceGenerator()
        self.delta_serializer = OOXMLDeltaSerializer()
        self.style_registry = StyleRegistry()
        self.naming_conventions = StyleNamingConventions()

        # Platform-specific XML containers
        self.xml_containers = {
            "word": {
                "root": "w:styles",
                "namespace": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
                "prefix": "w"
            },
            "powerpoint": {
                "root": "p:txStyles",
                "namespace": "http://schemas.openxmlformats.org/presentationml/2006/main",
                "prefix": "p"
            },
            "excel": {
                "root": "styleSheet",
                "namespace": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
                "prefix": "x"
            }
        }

        logger.info("🎨 Initialized Enhanced OOXML Style Definition Generator")

    def generate_style_definitions_for_hierarchy(self,
                                               tokens: List[InheritedTypographyToken],
                                               platform: str = "word") -> StyleRegistry:
        """Generate complete style definitions for inheritance hierarchy"""
        self.style_registry = StyleRegistry()  # Reset registry

        # Sort tokens by inheritance depth to ensure proper ordering
        sorted_tokens = sorted(tokens, key=lambda t: t.inheritance_depth or 0)

        # Generate naming suggestions for consistency
        naming_suggestions = self.naming_conventions.suggest_inheritance_hierarchy_names(tokens)

        for token in sorted_tokens:
            try:
                style_def = self._create_style_definition(token, platform, naming_suggestions)
                self.style_registry.add_style(style_def)
                logger.debug(f"Generated style definition for: {token.id}")
            except Exception as e:
                logger.error(f"Failed to generate style definition for {token.id}: {e}")

        # Validate dependencies
        validation_errors = self.style_registry.validate_dependencies()
        if validation_errors:
            logger.warning(f"Style dependency validation errors: {validation_errors}")

        return self.style_registry

    def _create_style_definition(self,
                               token: InheritedTypographyToken,
                               platform: str,
                               naming_suggestions: Dict[str, str]) -> StyleDefinition:
        """Create comprehensive style definition from token"""
        # Generate IDs and names
        style_id = self.naming_conventions.generate_style_id(token, platform)
        style_name = naming_suggestions.get(token.id) or self.naming_conventions.generate_style_name(token)

        # Generate OOXML content
        generation_result = self.inheritance_generator.generate_style_xml_with_inheritance(token, platform)

        # Determine style type based on platform and properties
        style_type = self._determine_style_type(token, platform)

        return StyleDefinition(
            style_id=style_id,
            style_name=style_name,
            style_type=style_type,
            platform=platform,
            xml_content=generation_result.xml_content,
            base_style_id=token.base_style,
            inheritance_depth=token.inheritance_depth or 0,
            has_delta_properties=generation_result.has_delta_properties,
            dependencies=self._extract_dependencies(token),
            validation_errors=generation_result.validation_errors
        )

    def _determine_style_type(self, token: InheritedTypographyToken, platform: str) -> str:
        """Determine OOXML style type based on token properties and platform"""
        if platform == "word":
            # Word supports paragraph, character, table, and numbering styles
            return "paragraph"  # Default for typography tokens
        elif platform == "powerpoint":
            return "text"
        elif platform == "excel":
            return "cell"
        else:
            return "unknown"

    def _extract_dependencies(self, token: InheritedTypographyToken) -> List[str]:
        """Extract style dependencies from token"""
        dependencies = []

        if token.base_style:
            dependencies.append(token.base_style)

        # Add any other dependencies from inheritance chain
        if token.inheritance_chain:
            dependencies.extend([style for style in token.inheritance_chain[:-1] if style != token.id])

        return list(set(dependencies))  # Remove duplicates

    def generate_complete_style_sheet(self,
                                    tokens: List[InheritedTypographyToken],
                                    platform: str = "word",
                                    include_builtin_styles: bool = True) -> str:
        """Generate complete OOXML style sheet with proper ordering and structure"""
        # Generate style definitions
        style_registry = self.generate_style_definitions_for_hierarchy(tokens, platform)

        # Get properly ordered styles
        ordered_styles = style_registry.get_sorted_styles()

        # Build XML content
        xml_parts = []

        # Add built-in style definitions if requested
        if include_builtin_styles:
            builtin_xml = self._generate_builtin_style_definitions(platform)
            if builtin_xml:
                xml_parts.extend(builtin_xml)

        # Add custom styles
        for style in ordered_styles:
            xml_parts.append(style.xml_content)

        # Wrap in platform-specific container
        return self._wrap_in_style_sheet_container(xml_parts, platform)

    def _generate_builtin_style_definitions(self, platform: str) -> List[str]:
        """Generate built-in style definitions for platform"""
        builtin_definitions = []

        if platform == "word":
            # Word built-in styles
            builtin_definitions = [
                '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>',
                '<w:style w:type="character" w:default="1" w:styleId="DefaultParagraphFont"><w:name w:val="Default Paragraph Font"/></w:style>',
                '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="Heading 1"/><w:basedOn w:val="Normal"/></w:style>'
            ]

        return builtin_definitions

    def _wrap_in_style_sheet_container(self, xml_parts: List[str], platform: str) -> str:
        """Wrap style definitions in platform-specific container"""
        if platform not in self.xml_containers:
            raise ValueError(f"Unsupported platform: {platform}")

        container = self.xml_containers[platform]
        namespace_attr = f' xmlns:{container["prefix"]}="{container["namespace"]}"'

        # Join all XML parts with proper indentation
        indented_content = '\n'.join(f'    {part}' for part in xml_parts)

        return f"""<{container["root"]}{namespace_attr}>
{indented_content}
</{container["root"]}>"""

    def optimize_style_sheet_for_office_versions(self,
                                               xml_content: str,
                                               target_version: str = "2019") -> str:
        """Optimize style sheet for specific Office versions"""
        if target_version in ["2016", "2019", "365"]:
            # Modern Office versions support full inheritance
            return xml_content
        elif target_version in ["2010", "2013"]:
            # Older versions may need compatibility adjustments
            return self._add_compatibility_attributes(xml_content)
        else:
            logger.warning(f"Unknown Office version: {target_version}")
            return xml_content

    def _add_compatibility_attributes(self, xml_content: str) -> str:
        """Add compatibility attributes for older Office versions"""
        # Add compatibility namespace if not present
        if 'mc:' not in xml_content and 'markup-compatibility' not in xml_content:
            xml_content = xml_content.replace(
                '<w:styles',
                '<w:styles xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"'
            )

        return xml_content

    def validate_style_sheet_structure(self, xml_content: str) -> Dict[str, Any]:
        """Validate complete style sheet structure"""
        validation_result = {
            "is_valid": True,
            "style_count": 0,
            "inheritance_styles": 0,
            "circular_dependencies": [],
            "missing_dependencies": [],
            "xml_errors": []
        }

        try:
            # Parse XML
            if LXML_AVAILABLE:
                root = etree.fromstring(xml_content.encode('utf-8'))
            else:
                root = ET.fromstring(xml_content)

            # Count styles
            styles = root.findall('.//*[@styleId]') if hasattr(root, 'findall') else []
            validation_result["style_count"] = len(styles)

            # Count inheritance styles (those with basedOn)
            inheritance_count = len([s for s in styles if s.find('.//*[@val]') is not None])
            validation_result["inheritance_styles"] = inheritance_count

        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["xml_errors"].append(str(e))

        return validation_result

    def generate_style_documentation(self, style_registry: StyleRegistry) -> str:
        """Generate documentation for style definitions"""
        doc_lines = ["# Style Definition Documentation", ""]

        for style in style_registry.get_sorted_styles():
            doc_lines.append(f"## {style.style_name} ({style.style_id})")
            doc_lines.append(f"- **Platform**: {style.platform}")
            doc_lines.append(f"- **Type**: {style.style_type}")
            doc_lines.append(f"- **Inheritance Depth**: {style.inheritance_depth}")

            if style.base_style_id:
                doc_lines.append(f"- **Inherits From**: {style.base_style_id}")

            if style.dependencies:
                doc_lines.append(f"- **Dependencies**: {', '.join(style.dependencies)}")

            if style.has_delta_properties:
                doc_lines.append("- **Uses Delta Properties**: Yes")

            if style.validation_errors:
                doc_lines.append(f"- **Validation Errors**: {len(style.validation_errors)}")

            doc_lines.append("")

        return '\n'.join(doc_lines)


# Export main classes
__all__ = [
    'OOXMLStyleDefinitionGenerator',
    'StyleDefinition',
    'StyleRegistry',
    'StyleNamingConventions'
]