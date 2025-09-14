"""
StyleStack EMU Typography Token System

W3C DTCG-compliant typography tokens with EMU precision for grid-safe OOXML typography.
Extends StyleStack's existing token system with professional typography calculations.

Features:
- W3C DTCG typography token specification compliance
- EMU (English Metric Units) precision for OOXML consistency
- Baseline grid calculations with configurable grid sizes
- Token hierarchy resolution (Design System > Corporate > Channel > Template)
- Cross-platform font fallback with consistent metrics
- Accessibility compliance (WCAG AAA) built into calculations
"""

import math
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json
import logging

from tools.variable_resolver import ResolvedVariable, VariableResolver
from tools.token_parser import TokenType, TokenScope

# Import inheritance enums and types for enhanced typography token support
try:
    from tools.style_inheritance_core import InheritanceMode
except ImportError:
    # Fallback for environments without style inheritance core
    class InheritanceMode:
        AUTO = "auto"
        MANUAL_OVERRIDE = "manual_override"
        COMPLETE = "complete"
        DELTA = "delta"

logger = logging.getLogger(__name__)


# EMU Constants (English Metric Units)
EMU_PER_INCH = 914400
EMU_PER_POINT = EMU_PER_INCH / 72  # 12700 EMUs per point
EMU_PER_PIXEL = EMU_PER_INCH / 96  # 9525 EMUs per pixel (96 DPI)

# Standard baseline grids in EMUs
BASELINE_GRIDS_EMU = {
    "12pt": 12 * EMU_PER_POINT,  # 152400 EMUs
    "14pt": 14 * EMU_PER_POINT,  # 177800 EMUs
    "18pt": 18 * EMU_PER_POINT,  # 228600 EMUs
    "24pt": 24 * EMU_PER_POINT   # 304800 EMUs
}

# Typography scale ratios
TYPOGRAPHY_SCALES = {
    "minor_second": 1.067,
    "major_second": 1.125,
    "minor_third": 1.2,
    "major_third": 1.25,
    "perfect_fourth": 1.333,
    "augmented_fourth": 1.414,
    "perfect_fifth": 1.5,
    "golden_ratio": 1.618
}


@dataclass
class TypographyToken:
    """W3C DTCG-compliant typography token with EMU precision"""
    id: str
    font_family: Optional[Union[str, List[str]]] = None
    font_size: Optional[str] = None  # e.g., "16pt", "1.2rem"
    font_weight: Optional[Union[int, str]] = None
    line_height: Optional[Union[float, str]] = None
    letter_spacing: Optional[str] = None
    font_style: Optional[str] = None
    text_decoration: Optional[str] = None
    text_transform: Optional[str] = None

    # StyleStack EMU extensions
    font_size_emu: Optional[int] = None
    line_height_emu: Optional[int] = None
    letter_spacing_emu: Optional[int] = None
    baseline_grid_emu: Optional[int] = None

    # Accessibility extensions
    wcag_level: Optional[str] = None  # AA, AAA
    min_contrast_ratio: Optional[float] = None

    # OOXML-specific properties
    ooxml_properties: Dict[str, Any] = field(default_factory=dict)

    # Style inheritance extensions (optional - for enhanced typography tokens)
    base_style: Optional[str] = None
    inheritance_mode: Optional[str] = None  # "auto", "manual_override", "strict"
    delta_properties: Optional[Dict[str, Any]] = field(default_factory=dict)
    inheritance_chain: Optional[List[str]] = field(default_factory=list)
    inheritance_depth: Optional[int] = None

    def to_w3c_dtcg(self) -> Dict[str, Any]:
        """Convert to W3C DTCG typography token format"""
        token = {
            "$type": "typography",
            "$value": {},
            "$description": f"Grid-safe typography token: {self.id}"
        }

        if self.font_family:
            token["$value"]["fontFamily"] = self.font_family
        if self.font_size:
            token["$value"]["fontSize"] = self.font_size
        if self.font_weight:
            token["$value"]["fontWeight"] = self.font_weight
        if self.line_height:
            token["$value"]["lineHeight"] = self.line_height
        if self.letter_spacing:
            token["$value"]["letterSpacing"] = self.letter_spacing
        if self.font_style:
            token["$value"]["fontStyle"] = self.font_style
        if self.text_decoration:
            token["$value"]["textDecoration"] = self.text_decoration
        if self.text_transform:
            token["$value"]["textTransform"] = self.text_transform

        # StyleStack extensions
        if any([self.font_size_emu, self.line_height_emu, self.letter_spacing_emu, self.baseline_grid_emu]):
            token["$extensions"] = {
                "stylestack": {
                    "emu": {
                        "fontSize": self.font_size_emu,
                        "lineHeight": self.line_height_emu,
                        "letterSpacing": self.letter_spacing_emu,
                        "baselineGrid": self.baseline_grid_emu
                    }
                }
            }

        if self.wcag_level or self.min_contrast_ratio:
            if "$extensions" not in token:
                token["$extensions"] = {"stylestack": {}}
            token["$extensions"]["stylestack"]["accessibility"] = {
                "wcagLevel": self.wcag_level,
                "minContrastRatio": self.min_contrast_ratio
            }

        if self.ooxml_properties:
            if "$extensions" not in token:
                token["$extensions"] = {"stylestack": {}}
            token["$extensions"]["stylestack"]["ooxml"] = self.ooxml_properties

        # Add inheritance metadata to extensions if present
        if self.has_inheritance():
            if "$extensions" not in token:
                token["$extensions"] = {"stylestack": {}}
            elif "stylestack" not in token["$extensions"]:
                token["$extensions"]["stylestack"] = {}

            token["$extensions"]["stylestack"]["inheritance"] = {
                "baseStyle": self.base_style,
                "mode": self.inheritance_mode,
                "shouldGenerateDelta": self.should_generate_delta(),
                "inheritanceChain": self.inheritance_chain,
                "inheritanceDepth": self.inheritance_depth
            }

            if self.delta_properties:
                token["$extensions"]["stylestack"]["inheritance"]["deltaProperties"] = self.delta_properties

        return token

    def has_inheritance(self) -> bool:
        """Check if this token has inheritance configuration"""
        return self.base_style is not None or self.inheritance_mode is not None

    def should_generate_delta(self) -> bool:
        """Determine if this token should generate delta-only properties"""
        return (self.has_inheritance() and
                self.inheritance_mode in ["auto", "delta"] and
                bool(self.delta_properties))

    def get_effective_property(self, property_name: str) -> Any:
        """Get effective property value considering inheritance"""
        # Map property names to token attributes
        property_map = {
            "family": "font_family",
            "fontFamily": "font_family",
            "size": "font_size",
            "fontSize": "font_size",
            "weight": "font_weight",
            "fontWeight": "font_weight",
            "height": "line_height",
            "lineHeight": "line_height",
            "spacing": "letter_spacing",
            "letterSpacing": "letter_spacing",
            "style": "font_style",
            "fontStyle": "font_style"
        }

        attr_name = property_map.get(property_name, property_name)
        return getattr(self, attr_name, None)

    def to_inherited_token(self):
        """Convert to InheritedTypographyToken if inheritance core is available"""
        try:
            from tools.style_inheritance_core import InheritedTypographyToken, InheritanceMode as CoreInheritanceMode

            # Convert inheritance mode string to enum
            mode_map = {
                "auto": CoreInheritanceMode.AUTO,
                "manual_override": CoreInheritanceMode.MANUAL_OVERRIDE,
                "complete": CoreInheritanceMode.COMPLETE,
                "delta": CoreInheritanceMode.DELTA
            }

            inheritance_mode_enum = mode_map.get(self.inheritance_mode, CoreInheritanceMode.MANUAL_OVERRIDE)

            return InheritedTypographyToken(
                id=self.id,
                font_family=self.font_family,
                font_size=self.font_size,
                font_weight=self.font_weight,
                line_height=self.line_height,
                letter_spacing=self.letter_spacing,
                font_style=self.font_style,
                text_decoration=self.text_decoration,
                text_transform=self.text_transform,
                font_size_emu=self.font_size_emu,
                line_height_emu=self.line_height_emu,
                letter_spacing_emu=self.letter_spacing_emu,
                baseline_grid_emu=self.baseline_grid_emu,
                wcag_level=self.wcag_level,
                min_contrast_ratio=self.min_contrast_ratio,
                ooxml_properties=self.ooxml_properties,
                base_style=self.base_style,
                inheritance_mode=inheritance_mode_enum,
                delta_properties=self.delta_properties or {},
                inheritance_chain=self.inheritance_chain or [],
                inheritance_depth=self.inheritance_depth or 0
            )
        except ImportError:
            # Return self if inheritance core not available
            return self


class EMUConversionEngine:
    """EMU conversion algorithms with grid-snapping precision"""

    @staticmethod
    def pt_to_emu(points: float) -> int:
        """Convert points to EMUs with proper rounding"""
        return round(points * EMU_PER_POINT)

    @staticmethod
    def px_to_emu(pixels: float, dpi: int = 96) -> int:
        """Convert pixels to EMUs with DPI consideration"""
        inches = pixels / dpi
        return round(inches * EMU_PER_INCH)

    @staticmethod
    def emu_to_pt(emus: int) -> float:
        """Convert EMUs to points"""
        return emus / EMU_PER_POINT

    @staticmethod
    def emu_to_px(emus: int, dpi: int = 96) -> float:
        """Convert EMUs to pixels"""
        inches = emus / EMU_PER_INCH
        return inches * dpi

    @staticmethod
    def parse_dimension_to_emu(dimension: str) -> Optional[int]:
        """Parse dimension string (e.g., '16pt', '1.2rem', '24px') to EMUs"""
        import re

        if not isinstance(dimension, str):
            return None

        # Remove whitespace
        dimension = dimension.strip().lower()

        # Match number and unit
        match = re.match(r'^(\d*\.?\d+)(pt|px|rem|em|%)?$', dimension)
        if not match:
            return None

        value = float(match.group(1))
        unit = match.group(2) or 'pt'  # Default to points

        if unit == 'pt':
            return EMUConversionEngine.pt_to_emu(value)
        elif unit == 'px':
            return EMUConversionEngine.px_to_emu(value)
        elif unit in ['rem', 'em']:
            # Assume 16pt base for rem/em conversion
            return EMUConversionEngine.pt_to_emu(value * 16)
        else:
            return None


class BaselineGridEngine:
    """Baseline grid calculations with configurable grid sizes"""

    def __init__(self, baseline_grid_emu: int = BASELINE_GRIDS_EMU["18pt"]):
        self.baseline_grid_emu = baseline_grid_emu
        self.baseline_grid_pt = EMUConversionEngine.emu_to_pt(baseline_grid_emu)

    def snap_to_baseline(self, value_emu: int) -> int:
        """Snap value to baseline grid multiples"""
        return round(value_emu / self.baseline_grid_emu) * self.baseline_grid_emu

    def calculate_line_height_for_font_size(self, font_size_emu: int,
                                          target_ratio: float = 1.4) -> int:
        """Calculate baseline-aligned line height for font size"""
        # Calculate ideal line height
        ideal_line_height = font_size_emu * target_ratio

        # Snap to baseline grid
        return self.snap_to_baseline(ideal_line_height)

    def calculate_spacing_before_after(self, line_height_emu: int,
                                     spacing_ratio: float = 0.5) -> Tuple[int, int]:
        """Calculate before/after spacing that maintains baseline grid"""
        total_spacing = int(line_height_emu * spacing_ratio)
        spacing_snapped = self.snap_to_baseline(total_spacing)

        # Split evenly between before and after
        before_spacing = spacing_snapped // 2
        after_spacing = spacing_snapped - before_spacing

        return (before_spacing, after_spacing)

    def calculate_indent(self, indent_ratio: float = 2.0) -> int:
        """Calculate indent aligned to baseline grid horizontal rhythm"""
        # Use baseline grid as horizontal rhythm unit
        indent_emu = int(self.baseline_grid_emu * indent_ratio)
        return self.snap_to_baseline(indent_emu)


class TypographyTokenHierarchyResolver:
    """Hierarchical typography token resolution with precedence"""

    def __init__(self, variable_resolver: Optional[VariableResolver] = None, enable_inheritance: bool = True):
        self.variable_resolver = variable_resolver or VariableResolver(verbose=True)
        self.baseline_engine = BaselineGridEngine()
        self.enable_inheritance = enable_inheritance

        # Initialize inheritance system if available and enabled
        self.inheritance_registry = None
        self.delta_generator = None
        self.inheritance_resolver = None

        if self.enable_inheritance:
            try:
                from tools.style_inheritance_core import create_inheritance_system
                self.inheritance_registry, self.delta_generator, self.inheritance_resolver = create_inheritance_system()
            except ImportError:
                self.enable_inheritance = False

    def resolve_typography_tokens(self,
                                design_system_tokens: Optional[Dict[str, Any]] = None,
                                corporate_tokens: Optional[Dict[str, Any]] = None,
                                channel_tokens: Optional[Dict[str, Any]] = None,
                                template_tokens: Optional[Dict[str, Any]] = None) -> Dict[str, TypographyToken]:
        """
        Resolve typography tokens through hierarchy with precedence.

        Hierarchy (lowest to highest precedence):
        1. Design System tokens (global foundation)
        2. Corporate tokens (brand overrides)
        3. Channel tokens (use-case specialization)
        4. Template tokens (final overrides)
        """
        resolved_tokens = {}

        # Layer 1: Design System tokens
        if design_system_tokens:
            ds_tokens = self._extract_typography_tokens(design_system_tokens, "design_system")
            resolved_tokens.update(ds_tokens)

        # Layer 2: Corporate tokens
        if corporate_tokens:
            corp_tokens = self._extract_typography_tokens(corporate_tokens, "corporate")
            resolved_tokens = self._merge_typography_tokens(resolved_tokens, corp_tokens)

        # Layer 3: Channel tokens
        if channel_tokens:
            channel_typo_tokens = self._extract_typography_tokens(channel_tokens, "channel")
            resolved_tokens = self._merge_typography_tokens(resolved_tokens, channel_typo_tokens)

        # Layer 4: Template tokens
        if template_tokens:
            template_typo_tokens = self._extract_typography_tokens(template_tokens, "template")
            resolved_tokens = self._merge_typography_tokens(resolved_tokens, template_typo_tokens)

        # Calculate EMU values and grid alignment
        for token in resolved_tokens.values():
            self._calculate_emu_values(token)

        # Resolve inheritance relationships if enabled
        if self.enable_inheritance and self.inheritance_resolver:
            resolved_tokens = self._resolve_inheritance_relationships(resolved_tokens)

        return resolved_tokens

    def _extract_typography_tokens(self, token_data: Dict[str, Any],
                                 source: str) -> Dict[str, TypographyToken]:
        """Extract typography tokens from token data structure"""
        typography_tokens = {}

        # Find typography section
        typography_section = token_data.get("typography", {})
        if not typography_section:
            return typography_tokens

        # Process nested typography tokens
        self._process_typography_section(typography_section, "", source, typography_tokens)

        return typography_tokens

    def _process_typography_section(self, section: Dict[str, Any], prefix: str,
                                  source: str, output: Dict[str, TypographyToken]):
        """Recursively process typography token sections"""
        for key, value in section.items():
            current_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                if "$type" in value and value["$type"] == "typography":
                    # This is a typography token definition
                    token = self._create_typography_token(current_key, value, source)
                    output[current_key] = token
                elif "$value" in value and isinstance(value["$value"], dict):
                    # This is a W3C DTCG typography token
                    token = self._create_typography_token_from_dtcg(current_key, value, source)
                    output[current_key] = token
                else:
                    # This is a nested section
                    self._process_typography_section(value, current_key, source, output)

    def _create_typography_token(self, token_id: str, token_data: Dict[str, Any],
                               source: str) -> TypographyToken:
        """Create TypographyToken from token data"""
        # Extract W3C DTCG properties
        value_data = token_data.get("$value", {})

        token = TypographyToken(
            id=token_id,
            font_family=value_data.get("fontFamily"),
            font_size=value_data.get("fontSize"),
            font_weight=value_data.get("fontWeight"),
            line_height=value_data.get("lineHeight"),
            letter_spacing=value_data.get("letterSpacing"),
            font_style=value_data.get("fontStyle"),
            text_decoration=value_data.get("textDecoration"),
            text_transform=value_data.get("textTransform")
        )

        # Extract StyleStack extensions
        extensions = token_data.get("$extensions", {}).get("stylestack", {})
        emu_data = extensions.get("emu", {})

        token.font_size_emu = emu_data.get("fontSize")
        token.line_height_emu = emu_data.get("lineHeight")
        token.letter_spacing_emu = emu_data.get("letterSpacing")
        token.baseline_grid_emu = emu_data.get("baselineGrid")

        # Extract accessibility data
        accessibility_data = extensions.get("accessibility", {})
        token.wcag_level = accessibility_data.get("wcagLevel")
        token.min_contrast_ratio = accessibility_data.get("minContrastRatio")

        # Extract OOXML properties
        token.ooxml_properties = extensions.get("ooxml", {})

        # Extract inheritance data if present
        inheritance_data = extensions.get("inheritance", {})
        if inheritance_data:
            token.base_style = inheritance_data.get("baseStyle")
            token.inheritance_mode = inheritance_data.get("mode")
            token.delta_properties = inheritance_data.get("deltaProperties", {})
            token.inheritance_chain = inheritance_data.get("inheritanceChain", [])
            token.inheritance_depth = inheritance_data.get("inheritanceDepth")

        return token

    def _create_typography_token_from_dtcg(self, token_id: str, dtcg_token: Dict[str, Any],
                                         source: str) -> TypographyToken:
        """Create TypographyToken from W3C DTCG format"""
        return self._create_typography_token(token_id, dtcg_token, source)

    def _merge_typography_tokens(self, base_tokens: Dict[str, TypographyToken],
                               override_tokens: Dict[str, TypographyToken]) -> Dict[str, TypographyToken]:
        """Merge typography tokens with override precedence"""
        merged = base_tokens.copy()

        for token_id, override_token in override_tokens.items():
            if token_id in merged:
                # Merge properties, giving precedence to override
                base_token = merged[token_id]
                merged_token = TypographyToken(id=token_id)

                # Merge all properties with override precedence
                for attr in ['font_family', 'font_size', 'font_weight', 'line_height',
                           'letter_spacing', 'font_style', 'text_decoration', 'text_transform',
                           'font_size_emu', 'line_height_emu', 'letter_spacing_emu',
                           'baseline_grid_emu', 'wcag_level', 'min_contrast_ratio']:
                    override_value = getattr(override_token, attr)
                    base_value = getattr(base_token, attr)
                    setattr(merged_token, attr, override_value if override_value is not None else base_value)

                # Merge OOXML properties
                merged_ooxml = base_token.ooxml_properties.copy()
                merged_ooxml.update(override_token.ooxml_properties)
                merged_token.ooxml_properties = merged_ooxml

                merged[token_id] = merged_token
            else:
                merged[token_id] = override_token

        return merged

    def _calculate_emu_values(self, token: TypographyToken):
        """Calculate EMU values from string dimensions"""
        # Calculate font size EMU
        if token.font_size and token.font_size_emu is None:
            token.font_size_emu = EMUConversionEngine.parse_dimension_to_emu(token.font_size)

        # Calculate line height EMU
        if token.line_height and token.line_height_emu is None:
            if isinstance(token.line_height, (int, float)):
                # Relative line height (e.g., 1.4)
                if token.font_size_emu:
                    ideal_line_height = token.font_size_emu * token.line_height
                    token.line_height_emu = self.baseline_engine.snap_to_baseline(ideal_line_height)
            else:
                # Absolute line height (e.g., "24pt")
                token.line_height_emu = EMUConversionEngine.parse_dimension_to_emu(str(token.line_height))
                if token.line_height_emu:
                    token.line_height_emu = self.baseline_engine.snap_to_baseline(token.line_height_emu)

        # Calculate letter spacing EMU
        if token.letter_spacing and token.letter_spacing_emu is None:
            token.letter_spacing_emu = EMUConversionEngine.parse_dimension_to_emu(token.letter_spacing)

        # Set default baseline grid if not specified
        if token.baseline_grid_emu is None:
            token.baseline_grid_emu = self.baseline_engine.baseline_grid_emu

    def _resolve_inheritance_relationships(self, tokens: Dict[str, TypographyToken]) -> Dict[str, TypographyToken]:
        """Resolve inheritance relationships between typography tokens"""
        if not self.enable_inheritance or not self.inheritance_resolver:
            return tokens

        resolved_tokens = {}

        # Convert TypographyTokens with inheritance to InheritedTypographyTokens
        inherited_tokens = {}
        for token_id, token in tokens.items():
            if token.has_inheritance():
                inherited_token = token.to_inherited_token()
                inherited_tokens[token_id] = inherited_token
            else:
                # Keep non-inheritance tokens as-is
                resolved_tokens[token_id] = token

        # Resolve inheritance for tokens that have inheritance relationships
        for token_id, inherited_token in inherited_tokens.items():
            try:
                # Create hierarchy for this token resolution
                token_hierarchy = inherited_tokens.copy()

                # Resolve inheritance
                resolved_inherited_token = self.inheritance_resolver.resolve_inheritance(
                    inherited_token, token_hierarchy
                )

                # Convert back to TypographyToken with resolved inheritance data
                resolved_token = self._convert_inherited_to_typography_token(resolved_inherited_token)
                resolved_tokens[token_id] = resolved_token

            except Exception as e:
                logger.warning(f"Failed to resolve inheritance for token {token_id}: {e}")
                # Fallback to original token without inheritance
                fallback_token = tokens[token_id]
                fallback_token.inheritance_mode = "manual_override"
                resolved_tokens[token_id] = fallback_token

        return resolved_tokens

    def _convert_inherited_to_typography_token(self, inherited_token) -> TypographyToken:
        """Convert InheritedTypographyToken back to TypographyToken with resolved data"""
        # Get effective properties from the inherited token
        typography_token = TypographyToken(
            id=inherited_token.id,
            font_family=inherited_token.get_effective_property("family"),
            font_size=inherited_token.get_effective_property("size"),
            font_weight=inherited_token.get_effective_property("weight"),
            line_height=inherited_token.get_effective_property("height"),
            letter_spacing=inherited_token.get_effective_property("spacing"),
            font_style=inherited_token.get_effective_property("style"),
            text_decoration=inherited_token.text_decoration,
            text_transform=inherited_token.text_transform,
            font_size_emu=inherited_token.font_size_emu,
            line_height_emu=inherited_token.line_height_emu,
            letter_spacing_emu=inherited_token.letter_spacing_emu,
            baseline_grid_emu=inherited_token.baseline_grid_emu,
            wcag_level=inherited_token.wcag_level,
            min_contrast_ratio=inherited_token.min_contrast_ratio,
            ooxml_properties=inherited_token.ooxml_properties.copy() if inherited_token.ooxml_properties else {},
            # Preserve inheritance metadata
            base_style=inherited_token.base_style,
            inheritance_mode=inherited_token.inheritance_mode.value if hasattr(inherited_token.inheritance_mode, 'value') else str(inherited_token.inheritance_mode),
            delta_properties=inherited_token.delta_properties.copy() if inherited_token.delta_properties else {},
            inheritance_chain=inherited_token.inheritance_chain.copy() if inherited_token.inheritance_chain else [],
            inheritance_depth=inherited_token.inheritance_depth
        )

        return typography_token


class TypographyTokenValidator:
    """Validates typography tokens for W3C DTCG compliance and accessibility"""

    def __init__(self):
        self.wcag_minimum_sizes = {
            "AA": 16,   # 16pt minimum for WCAG AA
            "AAA": 18   # 18pt minimum for WCAG AAA
        }

    def validate_token(self, token: TypographyToken) -> List[str]:
        """Validate typography token, return list of validation errors"""
        errors = []

        # Validate W3C DTCG compliance
        if not token.id:
            errors.append("Token ID is required")

        # Validate EMU precision
        if token.font_size_emu and token.font_size_emu <= 0:
            errors.append("Font size EMU must be positive")

        if token.line_height_emu and token.line_height_emu <= 0:
            errors.append("Line height EMU must be positive")

        # Validate accessibility compliance
        if token.wcag_level and token.font_size_emu:
            min_size = self.wcag_minimum_sizes.get(token.wcag_level)
            if min_size:
                font_size_pt = EMUConversionEngine.emu_to_pt(token.font_size_emu)
                if font_size_pt < min_size:
                    errors.append(f"Font size {font_size_pt}pt below WCAG {token.wcag_level} minimum of {min_size}pt")

        # Validate baseline grid alignment
        if token.line_height_emu and token.baseline_grid_emu:
            if token.line_height_emu % token.baseline_grid_emu != 0:
                errors.append("Line height is not aligned to baseline grid")

        return errors

    def validate_token_hierarchy(self, tokens: Dict[str, TypographyToken]) -> Dict[str, List[str]]:
        """Validate entire typography token hierarchy"""
        validation_results = {}

        for token_id, token in tokens.items():
            errors = self.validate_token(token)
            if errors:
                validation_results[token_id] = errors

        return validation_results


class TypographyTokenSystem:
    """Main typography token system combining all components"""

    def __init__(self, baseline_grid_pt: float = 18.0, verbose: bool = False):
        self.verbose = verbose
        self.baseline_grid_emu = EMUConversionEngine.pt_to_emu(baseline_grid_pt)
        self.baseline_engine = BaselineGridEngine(self.baseline_grid_emu)
        self.hierarchy_resolver = TypographyTokenHierarchyResolver()
        self.validator = TypographyTokenValidator()

        if self.verbose:
            logger.info(f"🎨 Initialized Typography Token System with {baseline_grid_pt}pt baseline grid")

    def create_typography_token_system(self,
                                     design_system_path: Optional[Path] = None,
                                     design_system_tokens: Optional[Dict[str, Any]] = None,
                                     corporate_tokens: Optional[Dict[str, Any]] = None,
                                     channel_tokens: Optional[Dict[str, Any]] = None,
                                     template_tokens: Optional[Dict[str, Any]] = None) -> Dict[str, TypographyToken]:
        """Create complete typography token system with hierarchy resolution"""

        # Load design system tokens if path provided, otherwise use provided tokens
        if design_system_path and design_system_path.exists():
            with open(design_system_path) as f:
                design_system_tokens = json.load(f)

        # Resolve typography tokens through hierarchy
        resolved_tokens = self.hierarchy_resolver.resolve_typography_tokens(
            design_system_tokens=design_system_tokens,
            corporate_tokens=corporate_tokens,
            channel_tokens=channel_tokens,
            template_tokens=template_tokens
        )

        # Validate tokens
        validation_results = self.validator.validate_token_hierarchy(resolved_tokens)

        if validation_results and self.verbose:
            logger.warning(f"⚠️ Typography token validation found {len(validation_results)} issues:")
            for token_id, errors in validation_results.items():
                for error in errors:
                    logger.warning(f"   {token_id}: {error}")

        if self.verbose:
            logger.info(f"✅ Created typography token system with {len(resolved_tokens)} tokens")

        return resolved_tokens

    def export_w3c_dtcg_tokens(self, tokens: Dict[str, TypographyToken]) -> Dict[str, Any]:
        """Export tokens in W3C DTCG format"""
        w3c_tokens = {"typography": {}}

        for token_id, token in tokens.items():
            # Build nested structure
            parts = token_id.split('.')
            current = w3c_tokens["typography"]

            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            current[parts[-1]] = token.to_w3c_dtcg()

        return w3c_tokens

    def generate_ooxml_paragraph_styles_with_inheritance(self, tokens: Dict[str, TypographyToken]) -> Dict[str, Dict[str, Any]]:
        """Generate OOXML paragraph style definitions with inheritance support"""
        paragraph_styles = {}

        for token_id, token in tokens.items():
            style_id = token_id.replace('.', '_')

            # Create base style structure
            style = {
                "w:style": {
                    "@w:type": "paragraph",
                    "@w:styleId": style_id,
                    "w:name": {"@w:val": token_id.replace('_', ' ').title()}
                }
            }

            # Add inheritance basedOn reference if present
            if token.has_inheritance() and token.should_generate_delta():
                # Delta-style with basedOn reference
                if token.base_style:
                    base_style_id = token.base_style.replace('.', '_') if '.' in token.base_style else token.base_style
                    style["w:style"]["w:basedOn"] = {"@w:val": base_style_id}

                # Add only delta properties
                self._add_delta_properties_to_ooxml_style(style, token)
            else:
                # Complete style definition (no inheritance or manual override)
                self._add_complete_properties_to_ooxml_style(style, token)

            paragraph_styles[style_id] = style

        return paragraph_styles

    def _add_delta_properties_to_ooxml_style(self, style: Dict[str, Any], token: TypographyToken):
        """Add only delta (changed) properties to OOXML style"""
        if not token.delta_properties:
            return

        rpr = {}
        ppr = {}

        # Process delta properties
        for prop, value in token.delta_properties.items():
            if prop == "fontFamily":
                rpr["w:rFonts"] = {"@w:ascii": value}
            elif prop == "fontSize":
                if isinstance(value, str) and value.endswith('pt'):
                    pt_value = float(value[:-2])
                    rpr["w:sz"] = {"@w:val": str(int(pt_value * 2))}
            elif prop == "fontWeight":
                if isinstance(value, int) and value >= 600:
                    rpr["w:b"] = {}
                elif value in ["bold", "semibold", "extrabold"]:
                    rpr["w:b"] = {}
            elif prop == "fontStyle" and value == "italic":
                rpr["w:i"] = {}
            elif prop == "letterSpacing":
                if token.letter_spacing_emu:
                    rpr["w:spacing"] = {"@w:val": str(int(token.letter_spacing_emu))}
            elif prop == "lineHeight":
                if token.line_height_emu:
                    ppr["w:spacing"] = {
                        "@w:line": str(int(token.line_height_emu)),
                        "@w:lineRule": "exact"
                    }

        # Add properties to style
        if rpr:
            style["w:style"]["w:rPr"] = rpr
        if ppr:
            style["w:style"]["w:pPr"] = ppr

    def _add_complete_properties_to_ooxml_style(self, style: Dict[str, Any], token: TypographyToken):
        """Add complete properties to OOXML style (no inheritance)"""
        rpr = {}
        ppr = {}

        # Font properties
        if token.font_family:
            rpr["w:rFonts"] = {
                "@w:ascii": token.font_family if isinstance(token.font_family, str) else token.font_family[0]
            }

        if token.font_size_emu:
            rpr["w:sz"] = {
                "@w:val": str(int(token.font_size_emu // EMU_PER_POINT * 2))  # Half-points
            }

        if token.font_weight:
            if isinstance(token.font_weight, int) and token.font_weight >= 600:
                rpr["w:b"] = {}
            elif token.font_weight in ["bold", "semibold", "extrabold"]:
                rpr["w:b"] = {}

        if token.font_style == "italic":
            rpr["w:i"] = {}

        if token.letter_spacing_emu:
            rpr["w:spacing"] = {
                "@w:val": str(int(token.letter_spacing_emu))
            }

        # Paragraph properties
        if token.line_height_emu:
            ppr["w:spacing"] = {
                "@w:line": str(int(token.line_height_emu)),
                "@w:lineRule": "exact"
            }

        # Add properties to style
        if rpr:
            style["w:style"]["w:rPr"] = rpr
        if ppr:
            style["w:style"]["w:pPr"] = ppr

    def generate_ooxml_paragraph_styles(self, tokens: Dict[str, TypographyToken]) -> Dict[str, Dict[str, Any]]:
        """Generate OOXML paragraph style definitions from typography tokens (legacy method)"""
        paragraph_styles = {}

        for token_id, token in tokens.items():
            if token.font_size_emu and token.line_height_emu:
                style = {
                    "w:pPr": {
                        "w:spacing": {
                            "@w:line": str(int(token.line_height_emu)),
                            "@w:lineRule": "exact"
                        }
                    },
                    "w:rPr": {
                        "w:sz": {
                            "@w:val": str(int(token.font_size_emu // EMU_PER_POINT * 2))  # Half-points
                        }
                    }
                }

                if token.font_family:
                    style["w:rPr"]["w:rFonts"] = {
                        "@w:ascii": token.font_family if isinstance(token.font_family, str) else token.font_family[0]
                    }

                if token.font_weight:
                    if isinstance(token.font_weight, int) and token.font_weight >= 600:
                        style["w:rPr"]["w:b"] = {}
                    elif token.font_weight in ["bold", "semibold", "extrabold"]:
                        style["w:rPr"]["w:b"] = {}

                if token.letter_spacing_emu:
                    style["w:rPr"]["w:spacing"] = {
                        "@w:val": str(int(token.letter_spacing_emu))
                    }

                paragraph_styles[token_id.replace('.', '_')] = style

        return paragraph_styles


# Export main classes for easy importing
__all__ = [
    'TypographyToken',
    'EMUConversionEngine',
    'BaselineGridEngine',
    'TypographyTokenHierarchyResolver',
    'TypographyTokenValidator',
    'TypographyTokenSystem'
]


if __name__ == "__main__":
    # Demo usage
    system = TypographyTokenSystem(verbose=True)

    # Example tokens
    corporate_tokens = {
        "typography": {
            "body": {
                "$type": "typography",
                "$value": {
                    "fontFamily": "Proxima Nova",
                    "fontSize": "16pt",
                    "lineHeight": 1.4,
                    "letterSpacing": "0pt"
                },
                "$extensions": {
                    "stylestack": {
                        "accessibility": {"wcagLevel": "AA"}
                    }
                }
            },
            "heading": {
                "$type": "typography",
                "$value": {
                    "fontFamily": "Proxima Nova",
                    "fontSize": "24pt",
                    "fontWeight": "bold",
                    "lineHeight": 1.3
                }
            }
        }
    }

    # Create token system
    tokens = system.create_typography_token_system(corporate_tokens=corporate_tokens)

    # Export W3C DTCG format
    w3c_export = system.export_w3c_dtcg_tokens(tokens)
    print("✅ W3C DTCG Export:", json.dumps(w3c_export, indent=2))

    # Generate OOXML styles
    ooxml_styles = system.generate_ooxml_paragraph_styles(tokens)
    print("✅ OOXML Paragraph Styles:", json.dumps(ooxml_styles, indent=2))