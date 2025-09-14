"""
StyleStack OOXML Delta Property Serialization System

Advanced delta-only property serialization for OOXML inheritance with EMU precision,
intelligent property filtering, and cross-platform compatibility.

Features:
- Delta-only property calculation and serialization
- EMU (English Metric Units) precision maintenance
- Intelligent property merging for complex attributes
- OOXML property filtering to exclude inherited values
- Cross-platform property mapping (Word, PowerPoint, Excel)
- Property validation and conflict resolution
"""

import logging
import math
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from tools.style_inheritance_core import InheritedTypographyToken, BaseStyleDefinition

logger = logging.getLogger(__name__)


class PropertyType(Enum):
    """Types of typography properties for serialization"""
    FONT_FAMILY = "fontFamily"
    FONT_SIZE = "fontSize"
    FONT_WEIGHT = "fontWeight"
    FONT_STYLE = "fontStyle"
    LINE_HEIGHT = "lineHeight"
    LETTER_SPACING = "letterSpacing"
    TEXT_DECORATION = "textDecoration"
    TEXT_TRANSFORM = "textTransform"
    COLOR = "color"
    BACKGROUND_COLOR = "backgroundColor"


class OOXMLPropertyTarget(Enum):
    """OOXML property targets for different element types"""
    RUN_PROPERTIES = "rPr"  # Word run properties
    PARAGRAPH_PROPERTIES = "pPr"  # Word paragraph properties
    TEXT_PROPERTIES = "defRPr"  # PowerPoint text properties
    CELL_PROPERTIES = "cellXf"  # Excel cell properties


@dataclass
class PropertyDelta:
    """Represents a calculated property delta"""
    property_name: str
    base_value: Any
    target_value: Any
    delta_type: str  # "change", "addition", "removal"
    emu_precision: Optional[int] = None
    platform_specific: Dict[str, Any] = None

    def __post_init__(self):
        if self.platform_specific is None:
            self.platform_specific = {}


@dataclass
class OOXMLPropertyMapping:
    """Mapping between typography properties and OOXML elements"""
    property_type: PropertyType
    ooxml_element: str
    attributes: Dict[str, str]
    target: OOXMLPropertyTarget
    platforms: Set[str]
    value_converter: Optional[callable] = None


class EMUConverter:
    """EMU (English Metric Units) conversion utilities with precision"""

    # EMU constants
    EMU_PER_INCH = 914400
    EMU_PER_POINT = 12700
    EMU_PER_PIXEL = 9525
    HALF_POINTS_PER_POINT = 2
    TWENTIETHS_PER_POINT = 20

    @staticmethod
    def points_to_emu(points: Union[float, str]) -> Optional[int]:
        """Convert points to EMU with precision"""
        if isinstance(points, str):
            if points.endswith('pt'):
                try:
                    points = float(points[:-2])
                except ValueError:
                    return None
            else:
                try:
                    points = float(points)
                except ValueError:
                    return None

        return round(points * EMUConverter.EMU_PER_POINT)

    @staticmethod
    def emu_to_points(emus: int) -> float:
        """Convert EMU to points with precision"""
        return emus / EMUConverter.EMU_PER_POINT

    @staticmethod
    def points_to_half_points(points: Union[float, str]) -> Optional[int]:
        """Convert points to Word half-points format"""
        if isinstance(points, str) and points.endswith('pt'):
            try:
                points = float(points[:-2])
            except ValueError:
                return None

        if isinstance(points, (int, float)):
            return int(points * EMUConverter.HALF_POINTS_PER_POINT)
        return None

    @staticmethod
    def points_to_twentieths(points: Union[float, str]) -> Optional[int]:
        """Convert points to twentieths format for spacing"""
        if isinstance(points, str) and points.endswith('pt'):
            try:
                points = float(points[:-2])
            except ValueError:
                return None

        if isinstance(points, (int, float)):
            return int(points * EMUConverter.TWENTIETHS_PER_POINT)
        return None

    @staticmethod
    def em_to_points(em_value: str, base_font_size: Union[float, str] = 16.0) -> Optional[float]:
        """Convert em units to points using base font size"""
        if not isinstance(em_value, str) or not em_value.endswith('em'):
            return None

        try:
            em_multiplier = float(em_value[:-2])
        except ValueError:
            return None

        if isinstance(base_font_size, str) and base_font_size.endswith('pt'):
            try:
                base_font_size = float(base_font_size[:-2])
            except ValueError:
                base_font_size = 16.0

        return em_multiplier * base_font_size


class OOXMLDeltaSerializer:
    """Advanced delta-only property serialization for OOXML"""

    def __init__(self):
        """Initialize delta serializer with property mappings"""
        self.emu_converter = EMUConverter()
        self.property_mappings = self._initialize_property_mappings()

        # Properties that should always be compared with EMU precision
        self.emu_precision_properties = {
            PropertyType.FONT_SIZE,
            PropertyType.LINE_HEIGHT,
            PropertyType.LETTER_SPACING
        }

    def _initialize_property_mappings(self) -> Dict[PropertyType, List[OOXMLPropertyMapping]]:
        """Initialize OOXML property mappings for all platforms"""
        return {
            PropertyType.FONT_FAMILY: [
                OOXMLPropertyMapping(
                    property_type=PropertyType.FONT_FAMILY,
                    ooxml_element="w:rFonts",
                    attributes={"w:ascii": "{value}", "w:hAnsi": "{value}"},
                    target=OOXMLPropertyTarget.RUN_PROPERTIES,
                    platforms={"word"}
                ),
                OOXMLPropertyMapping(
                    property_type=PropertyType.FONT_FAMILY,
                    ooxml_element="a:latin",
                    attributes={"typeface": "{value}"},
                    target=OOXMLPropertyTarget.TEXT_PROPERTIES,
                    platforms={"powerpoint"}
                )
            ],
            PropertyType.FONT_SIZE: [
                OOXMLPropertyMapping(
                    property_type=PropertyType.FONT_SIZE,
                    ooxml_element="w:sz",
                    attributes={"w:val": "{value}"},
                    target=OOXMLPropertyTarget.RUN_PROPERTIES,
                    platforms={"word"},
                    value_converter=self.emu_converter.points_to_half_points
                ),
                OOXMLPropertyMapping(
                    property_type=PropertyType.FONT_SIZE,
                    ooxml_element="a:sz",
                    attributes={"val": "{value}"},
                    target=OOXMLPropertyTarget.TEXT_PROPERTIES,
                    platforms={"powerpoint"},
                    value_converter=lambda x: int(float(x[:-2]) * 100) if isinstance(x, str) and x.endswith('pt') else None
                )
            ],
            PropertyType.FONT_WEIGHT: [
                OOXMLPropertyMapping(
                    property_type=PropertyType.FONT_WEIGHT,
                    ooxml_element="w:b",
                    attributes={},
                    target=OOXMLPropertyTarget.RUN_PROPERTIES,
                    platforms={"word"},
                    value_converter=lambda x: None if (isinstance(x, int) and x >= 600) or x in ["bold", "semibold", "extrabold"] else False
                ),
                OOXMLPropertyMapping(
                    property_type=PropertyType.FONT_WEIGHT,
                    ooxml_element="a:b",
                    attributes={"val": "1"},
                    target=OOXMLPropertyTarget.TEXT_PROPERTIES,
                    platforms={"powerpoint"},
                    value_converter=lambda x: "1" if (isinstance(x, int) and x >= 600) or x in ["bold", "semibold", "extrabold"] else None
                )
            ],
            PropertyType.FONT_STYLE: [
                OOXMLPropertyMapping(
                    property_type=PropertyType.FONT_STYLE,
                    ooxml_element="w:i",
                    attributes={},
                    target=OOXMLPropertyTarget.RUN_PROPERTIES,
                    platforms={"word"},
                    value_converter=lambda x: None if x == "italic" else False
                ),
                OOXMLPropertyMapping(
                    property_type=PropertyType.FONT_STYLE,
                    ooxml_element="a:i",
                    attributes={"val": "1"},
                    target=OOXMLPropertyTarget.TEXT_PROPERTIES,
                    platforms={"powerpoint"},
                    value_converter=lambda x: "1" if x == "italic" else None
                )
            ],
            PropertyType.LINE_HEIGHT: [
                OOXMLPropertyMapping(
                    property_type=PropertyType.LINE_HEIGHT,
                    ooxml_element="w:spacing",
                    attributes={"w:line": "{value}", "w:lineRule": "exact"},
                    target=OOXMLPropertyTarget.PARAGRAPH_PROPERTIES,
                    platforms={"word"},
                    value_converter=self._convert_line_height_to_emu
                )
            ],
            PropertyType.LETTER_SPACING: [
                OOXMLPropertyMapping(
                    property_type=PropertyType.LETTER_SPACING,
                    ooxml_element="w:spacing",
                    attributes={"w:val": "{value}"},
                    target=OOXMLPropertyTarget.RUN_PROPERTIES,
                    platforms={"word"},
                    value_converter=self._convert_letter_spacing_to_twentieths
                )
            ]
        }

    def calculate_property_deltas(self, base_token: Optional[InheritedTypographyToken],
                                base_style: Optional[BaseStyleDefinition],
                                target_token: InheritedTypographyToken) -> List[PropertyDelta]:
        """Calculate property deltas between base and target tokens with EMU precision"""
        deltas = []

        # Get all properties to compare
        properties_to_check = {
            'fontFamily': (PropertyType.FONT_FAMILY, target_token.font_family),
            'fontSize': (PropertyType.FONT_SIZE, target_token.font_size),
            'fontWeight': (PropertyType.FONT_WEIGHT, target_token.font_weight),
            'fontStyle': (PropertyType.FONT_STYLE, target_token.font_style),
            'lineHeight': (PropertyType.LINE_HEIGHT, target_token.line_height),
            'letterSpacing': (PropertyType.LETTER_SPACING, target_token.letter_spacing)
        }

        for prop_name, (prop_type, target_value) in properties_to_check.items():
            if target_value is None:
                continue

            # Get base value from inheritance chain
            base_value = self._get_base_property_value(prop_name, base_token, base_style)

            # Calculate delta with appropriate precision
            if self._values_are_different(base_value, target_value, prop_type):
                delta = PropertyDelta(
                    property_name=prop_name,
                    base_value=base_value,
                    target_value=target_value,
                    delta_type="change" if base_value is not None else "addition"
                )

                # Add EMU precision for relevant properties
                if prop_type in self.emu_precision_properties:
                    delta.emu_precision = self._calculate_emu_precision(target_value, prop_type)

                deltas.append(delta)

        return deltas

    def serialize_deltas_to_ooxml(self, deltas: List[PropertyDelta], platform: str) -> Dict[OOXMLPropertyTarget, List[str]]:
        """Serialize property deltas to OOXML elements grouped by target"""
        ooxml_elements = {
            OOXMLPropertyTarget.RUN_PROPERTIES: [],
            OOXMLPropertyTarget.PARAGRAPH_PROPERTIES: [],
            OOXMLPropertyTarget.TEXT_PROPERTIES: [],
            OOXMLPropertyTarget.CELL_PROPERTIES: []
        }

        for delta in deltas:
            property_type = PropertyType(delta.property_name) if delta.property_name in [p.value for p in PropertyType] else None
            if not property_type or property_type not in self.property_mappings:
                continue

            mappings = self.property_mappings[property_type]
            platform_mappings = [m for m in mappings if platform in m.platforms]

            for mapping in platform_mappings:
                xml_element = self._generate_ooxml_element(delta, mapping)
                if xml_element:
                    ooxml_elements[mapping.target].append(xml_element)

        return ooxml_elements

    def _generate_ooxml_element(self, delta: PropertyDelta, mapping: OOXMLPropertyMapping) -> Optional[str]:
        """Generate OOXML element from property delta and mapping"""
        # Convert value using mapping converter
        converted_value = delta.target_value
        if mapping.value_converter:
            try:
                converted_value = mapping.value_converter(delta.target_value)
                if converted_value is False:  # Explicit false means don't include element
                    return None
                if converted_value is None and delta.target_value is not None:
                    return None  # Conversion failed
            except Exception as e:
                logger.warning(f"Value conversion failed for {delta.property_name}: {e}")
                return None

        # Handle boolean properties (like bold, italic)
        if not mapping.attributes:
            return f"<{mapping.ooxml_element}/>"

        # Handle properties with attributes
        element_parts = [mapping.ooxml_element]
        for attr_name, attr_template in mapping.attributes.items():
            if "{value}" in attr_template:
                attr_value = attr_template.format(value=converted_value)
                element_parts.append(f'{attr_name}="{attr_value}"')
            else:
                element_parts.append(f'{attr_name}="{attr_template}"')

        return f"<{' '.join(element_parts)}/>"

    def _get_base_property_value(self, prop_name: str, base_token: Optional[InheritedTypographyToken],
                               base_style: Optional[BaseStyleDefinition]) -> Any:
        """Get base property value from inheritance chain"""
        # First check base token
        if base_token:
            base_value = getattr(base_token, prop_name.replace('font_', '').replace('_', ''), None)
            if base_value is not None:
                return base_value

        # Then check base style definition
        if base_style:
            return base_style.default_properties.get(prop_name)

        return None

    def _values_are_different(self, base_value: Any, target_value: Any, prop_type: PropertyType) -> bool:
        """Compare values with appropriate precision for property type"""
        if base_value is None:
            return target_value is not None

        if target_value is None:
            return base_value is not None

        # EMU precision comparison for size/spacing properties
        if prop_type in self.emu_precision_properties:
            base_emu = self._convert_to_emu_for_comparison(base_value, prop_type)
            target_emu = self._convert_to_emu_for_comparison(target_value, prop_type)

            if base_emu is not None and target_emu is not None:
                return abs(base_emu - target_emu) > 1  # Allow 1 EMU tolerance

        # Standard comparison for other properties
        return base_value != target_value

    def _convert_to_emu_for_comparison(self, value: Any, prop_type: PropertyType) -> Optional[int]:
        """Convert value to EMU for precise comparison"""
        if prop_type == PropertyType.FONT_SIZE:
            return self.emu_converter.points_to_emu(value)
        elif prop_type == PropertyType.LINE_HEIGHT:
            if isinstance(value, str) and value.endswith('pt'):
                return self.emu_converter.points_to_emu(value)
            elif isinstance(value, (int, float)):
                # Relative line height - need font size context
                return None  # Cannot convert without font size context
        elif prop_type == PropertyType.LETTER_SPACING:
            if isinstance(value, str) and value.endswith('em'):
                # Convert em to points (rough approximation)
                points = self.emu_converter.em_to_points(value)
                return self.emu_converter.points_to_emu(points) if points else None
            elif isinstance(value, str) and value.endswith('pt'):
                return self.emu_converter.points_to_emu(value)

        return None

    def _calculate_emu_precision(self, value: Any, prop_type: PropertyType) -> Optional[int]:
        """Calculate EMU precision for property value"""
        return self._convert_to_emu_for_comparison(value, prop_type)

    def _convert_line_height_to_emu(self, value: Any) -> Optional[int]:
        """Convert line height value to EMU format"""
        if isinstance(value, str) and value.endswith('pt'):
            return self.emu_converter.points_to_emu(value)
        elif isinstance(value, (int, float)):
            # Relative line height requires font size context
            # This is a placeholder - actual implementation would need font size
            return int(value * 12 * self.emu_converter.EMU_PER_POINT)  # Assume 12pt base
        return None

    def _convert_letter_spacing_to_twentieths(self, value: Any) -> Optional[int]:
        """Convert letter spacing to twentieths of a point"""
        if isinstance(value, str) and value.endswith('em'):
            points = self.emu_converter.em_to_points(value)
            return self.emu_converter.points_to_twentieths(points) if points else None
        elif isinstance(value, str) and value.endswith('pt'):
            return self.emu_converter.points_to_twentieths(value)
        return None

    def optimize_delta_properties(self, deltas: List[PropertyDelta]) -> List[PropertyDelta]:
        """Optimize delta properties by removing redundant or conflicting properties"""
        optimized = []

        # Group deltas by property type for optimization
        property_groups = {}
        for delta in deltas:
            prop_type = delta.property_name
            if prop_type not in property_groups:
                property_groups[prop_type] = []
            property_groups[prop_type].append(delta)

        # Optimize each property group
        for prop_type, prop_deltas in property_groups.items():
            if len(prop_deltas) == 1:
                optimized.extend(prop_deltas)
            else:
                # Handle multiple deltas for same property (choose most specific)
                optimized.append(self._resolve_property_conflict(prop_deltas))

        return optimized

    def _resolve_property_conflict(self, conflicting_deltas: List[PropertyDelta]) -> PropertyDelta:
        """Resolve conflicts between multiple deltas for the same property"""
        # For now, take the last one (most recent)
        # In future, could implement more sophisticated conflict resolution
        return conflicting_deltas[-1]

    def generate_validation_report(self, deltas: List[PropertyDelta], platform: str) -> Dict[str, Any]:
        """Generate validation report for delta serialization"""
        report = {
            "total_deltas": len(deltas),
            "platforms_supported": [platform],
            "emu_precision_properties": 0,
            "unsupported_properties": [],
            "conversion_errors": [],
            "optimization_opportunities": []
        }

        for delta in deltas:
            # Count EMU precision properties
            if delta.emu_precision is not None:
                report["emu_precision_properties"] += 1

            # Check for unsupported properties
            property_type = PropertyType(delta.property_name) if delta.property_name in [p.value for p in PropertyType] else None
            if not property_type or property_type not in self.property_mappings:
                report["unsupported_properties"].append(delta.property_name)

        return report


# Export main classes
__all__ = [
    'OOXMLDeltaSerializer',
    'PropertyDelta',
    'PropertyType',
    'OOXMLPropertyTarget',
    'OOXMLPropertyMapping',
    'EMUConverter'
]