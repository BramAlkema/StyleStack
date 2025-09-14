"""
StyleStack Style Inheritance Core Infrastructure

Core components for explicit style inheritance following OOXML best practices.
Implements InheritanceResolver, BaseStyleRegistry, DeltaStyleGenerator, and
enhanced typography tokens with inheritance support.

Features:
- OOXML-style inheritance with basedOn references
- Delta-only style generation for efficiency
- Circular dependency detection and prevention
- EMU precision maintenance through inheritance chains
- Manual override support for complete style definitions
"""

import logging
from typing import Dict, Any, Optional, List, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import json

# Import existing typography system for integration
from tools.typography_token_system import (
    TypographyToken, EMUConversionEngine, BaselineGridEngine,
    TypographyTokenValidator
)

logger = logging.getLogger(__name__)


class InheritanceMode(Enum):
    """Inheritance modes for typography tokens"""
    AUTO = "auto"                    # Automatic inheritance with delta calculation
    MANUAL_OVERRIDE = "manual_override"  # Manual override with complete definition
    COMPLETE = "complete"            # Complete style definition, no inheritance
    DELTA = "delta"                  # Force delta-only generation


class CircularInheritanceError(Exception):
    """Exception raised when circular inheritance is detected"""
    def __init__(self, chain: List[str]):
        self.chain = chain
        super().__init__(f"Circular inheritance detected: {' → '.join(chain)}")


class MissingBaseStyleError(Exception):
    """Exception raised when referenced base style is not found"""
    def __init__(self, style_id: str, base_style: str):
        self.style_id = style_id
        self.base_style = base_style
        super().__init__(f"Base style '{base_style}' not found for style '{style_id}'")


@dataclass
class BaseStyleDefinition:
    """Canonical OOXML base style definition with EMU precision"""
    style_id: str
    style_type: str  # paragraph, character, table
    default_properties: Dict[str, Any]
    emu_calculated_properties: Dict[str, int]
    description: Optional[str] = None
    ooxml_attributes: Dict[str, str] = field(default_factory=dict)

    def get_property(self, key: str) -> Any:
        """Get property value with fallback"""
        return self.default_properties.get(key)

    def get_emu_property(self, key: str) -> Optional[int]:
        """Get EMU-calculated property value"""
        return self.emu_calculated_properties.get(key)


@dataclass
class InheritedTypographyToken(TypographyToken):
    """Enhanced typography token with inheritance support"""
    base_style: Optional[str] = None
    inheritance_mode: InheritanceMode = InheritanceMode.AUTO
    delta_properties: Dict[str, Any] = field(default_factory=dict)
    computed_full_style: Optional[Dict[str, Any]] = None
    inheritance_chain: List[str] = field(default_factory=list)

    # Inheritance metadata
    resolved_base_properties: Dict[str, Any] = field(default_factory=dict)
    inheritance_depth: int = 0
    has_circular_reference: bool = False

    def should_generate_delta(self) -> bool:
        """Determine if delta-style generation should be used"""
        return (
            self.base_style is not None and
            self.inheritance_mode in [InheritanceMode.AUTO, InheritanceMode.DELTA] and
            len(self.delta_properties) > 0 and
            not self.has_circular_reference
        )

    def is_complete_override(self) -> bool:
        """Check if token uses complete style override"""
        return self.inheritance_mode in [InheritanceMode.MANUAL_OVERRIDE, InheritanceMode.COMPLETE]

    def get_effective_property(self, key: str) -> Any:
        """Get effective property value considering inheritance"""
        # Check delta properties first
        if key in self.delta_properties:
            return self.delta_properties[key]

        # Fall back to resolved base properties
        if key in self.resolved_base_properties:
            return self.resolved_base_properties[key]

        # Fall back to token's direct properties
        return getattr(self, key, None)


class BaseStyleRegistry:
    """Registry of canonical OOXML base styles with EMU precision"""

    def __init__(self):
        self._styles: Dict[str, BaseStyleDefinition] = {}
        self._initialize_standard_styles()

    def _initialize_standard_styles(self):
        """Initialize standard OOXML base styles"""

        # Normal paragraph style (foundation for most paragraph styles)
        self._styles["Normal"] = BaseStyleDefinition(
            style_id="Normal",
            style_type="paragraph",
            default_properties={
                "fontFamily": "Calibri",
                "fontSize": "11pt",
                "fontWeight": 400,
                "lineHeight": 1.15,
                "color": "#000000",
                "textAlign": "left"
            },
            emu_calculated_properties={
                "fontSize": EMUConversionEngine.pt_to_emu(11),
                "lineHeight": EMUConversionEngine.pt_to_emu(11 * 1.15),
                "spacing": {
                    "after": EMUConversionEngine.pt_to_emu(8),
                    "line": EMUConversionEngine.pt_to_emu(12.65),
                    "lineRule": "auto"
                }
            },
            description="Default paragraph style for Office documents",
            ooxml_attributes={"w:type": "paragraph", "w:default": "1"}
        )

        # Default Paragraph Font (foundation for character styles)
        self._styles["DefaultParagraphFont"] = BaseStyleDefinition(
            style_id="DefaultParagraphFont",
            style_type="character",
            default_properties={
                "fontFamily": "Calibri",
                "fontSize": "11pt",
                "fontWeight": 400,
                "color": "#000000"
            },
            emu_calculated_properties={
                "fontSize": EMUConversionEngine.pt_to_emu(11)
            },
            description="Default character font for Office documents",
            ooxml_attributes={"w:type": "character", "w:default": "1"}
        )

        # Heading 1 base style
        self._styles["Heading1"] = BaseStyleDefinition(
            style_id="Heading1",
            style_type="paragraph",
            default_properties={
                "fontFamily": "Calibri Light",
                "fontSize": "16pt",
                "fontWeight": 400,
                "lineHeight": 1.15,
                "color": "#2F5496",
                "textAlign": "left"
            },
            emu_calculated_properties={
                "fontSize": EMUConversionEngine.pt_to_emu(16),
                "lineHeight": EMUConversionEngine.pt_to_emu(16 * 1.15),
                "spacing": {
                    "before": EMUConversionEngine.pt_to_emu(12),
                    "after": EMUConversionEngine.pt_to_emu(0),
                    "line": EMUConversionEngine.pt_to_emu(18.4),
                    "lineRule": "auto"
                }
            },
            description="Heading 1 style for document structure",
            ooxml_attributes={"w:type": "paragraph"}
        )

        # Title style
        self._styles["Title"] = BaseStyleDefinition(
            style_id="Title",
            style_type="paragraph",
            default_properties={
                "fontFamily": "Calibri Light",
                "fontSize": "28pt",
                "fontWeight": 400,
                "lineHeight": 1.15,
                "color": "#2F5496",
                "textAlign": "center"
            },
            emu_calculated_properties={
                "fontSize": EMUConversionEngine.pt_to_emu(28),
                "lineHeight": EMUConversionEngine.pt_to_emu(28 * 1.15),
                "spacing": {
                    "before": EMUConversionEngine.pt_to_emu(0),
                    "after": EMUConversionEngine.pt_to_emu(0),
                    "line": EMUConversionEngine.pt_to_emu(32.2),
                    "lineRule": "auto"
                }
            },
            description="Title style for document headers",
            ooxml_attributes={"w:type": "paragraph"}
        )

    def register_style(self, style: BaseStyleDefinition) -> None:
        """Register a new base style"""
        if style.style_id in self._styles:
            logger.warning(f"Overriding existing base style: {style.style_id}")
        self._styles[style.style_id] = style

    def get_style(self, style_id: str) -> Optional[BaseStyleDefinition]:
        """Get base style by ID"""
        return self._styles.get(style_id)

    def has_style(self, style_id: str) -> bool:
        """Check if base style exists"""
        return style_id in self._styles

    def list_styles(self, style_type: Optional[str] = None) -> List[BaseStyleDefinition]:
        """List all base styles, optionally filtered by type"""
        if style_type:
            return [style for style in self._styles.values() if style.style_type == style_type]
        return list(self._styles.values())

    def get_paragraph_styles(self) -> List[BaseStyleDefinition]:
        """Get all paragraph base styles"""
        return self.list_styles("paragraph")

    def get_character_styles(self) -> List[BaseStyleDefinition]:
        """Get all character base styles"""
        return self.list_styles("character")

    def validate_base_style(self, style_id: str) -> bool:
        """Validate that a base style exists and is properly configured"""
        style = self.get_style(style_id)
        if not style:
            return False

        # Validate required properties
        required_props = ["fontSize", "fontWeight"]
        for prop in required_props:
            if prop not in style.default_properties:
                logger.warning(f"Base style {style_id} missing required property: {prop}")
                return False

        return True


class DeltaStyleGenerator:
    """Generates delta-only style definitions by comparing with base styles"""

    def __init__(self, base_registry: BaseStyleRegistry):
        self.base_registry = base_registry

    def calculate_delta(self, token: InheritedTypographyToken,
                       base_style: BaseStyleDefinition) -> Dict[str, Any]:
        """Calculate property delta between token and base style"""
        delta = {}

        # Property mapping for comparison
        property_mapping = {
            'font_family': 'fontFamily',
            'font_size': 'fontSize',
            'font_weight': 'fontWeight',
            'line_height': 'lineHeight',
            'letter_spacing': 'letterSpacing',
            'font_style': 'fontStyle',
            'text_decoration': 'textDecoration',
            'text_transform': 'textTransform'
        }

        # Compare each property
        for token_attr, style_prop in property_mapping.items():
            token_value = getattr(token, token_attr)
            base_value = base_style.get_property(style_prop)

            # Only include in delta if values differ and token value exists
            if token_value is not None and token_value != base_value:
                delta[style_prop] = token_value

        return delta

    def calculate_emu_delta(self, token: InheritedTypographyToken,
                           base_style: BaseStyleDefinition) -> Dict[str, Any]:
        """Calculate EMU-precision delta for typography measurements"""
        emu_delta = {}

        # Font size EMU comparison
        if token.font_size_emu and token.font_size_emu != base_style.get_emu_property('fontSize'):
            emu_delta['fontSize'] = token.font_size_emu

        # Line height EMU comparison
        if token.line_height_emu and token.line_height_emu != base_style.get_emu_property('lineHeight'):
            emu_delta['lineHeight'] = token.line_height_emu

        # Letter spacing EMU comparison
        if token.letter_spacing_emu and token.letter_spacing_emu != base_style.get_emu_property('letterSpacing'):
            emu_delta['letterSpacing'] = token.letter_spacing_emu

        return emu_delta

    def generate_delta_properties(self, token: InheritedTypographyToken) -> Dict[str, Any]:
        """Generate complete delta properties for token"""
        if not token.base_style:
            return {}

        base_style = self.base_registry.get_style(token.base_style)
        if not base_style:
            raise MissingBaseStyleError(token.id, token.base_style)

        # Calculate standard property delta
        delta = self.calculate_delta(token, base_style)

        # Calculate EMU precision delta
        emu_delta = self.calculate_emu_delta(token, base_style)
        if emu_delta:
            delta['emu'] = emu_delta

        return delta

    def validate_delta_properties(self, delta: Dict[str, Any]) -> List[str]:
        """Validate delta properties for correctness"""
        errors = []

        # Check for empty delta
        if not delta:
            errors.append("Empty delta properties - inheritance may be unnecessary")

        # Check for EMU precision
        if 'emu' in delta:
            emu_props = delta['emu']
            for key, value in emu_props.items():
                if not isinstance(value, int) or value < 0:
                    errors.append(f"Invalid EMU value for {key}: {value}")

        return errors


class InheritanceResolver:
    """Resolves typography token inheritance relationships with cycle detection"""

    def __init__(self, base_registry: BaseStyleRegistry,
                 delta_generator: Optional[DeltaStyleGenerator] = None):
        self.base_registry = base_registry
        self.delta_generator = delta_generator or DeltaStyleGenerator(base_registry)
        self._resolution_cache: Dict[str, InheritedTypographyToken] = {}
        self.max_inheritance_depth = 10

    def resolve_inheritance(self, token: TypographyToken,
                          token_hierarchy: Optional[Dict[str, TypographyToken]] = None,
                          inheritance_config: Optional[Dict[str, Any]] = None) -> InheritedTypographyToken:
        """
        Resolve inheritance for a typography token

        Args:
            token: Typography token to resolve inheritance for
            token_hierarchy: Dictionary of all tokens for chain resolution
            inheritance_config: Optional inheritance configuration override

        Returns:
            InheritedTypographyToken with resolved inheritance
        """
        if token_hierarchy is None:
            token_hierarchy = {}

        # Convert to inherited token if needed
        if isinstance(token, InheritedTypographyToken):
            inherited_token = token
        else:
            inherited_token = self._convert_to_inherited_token(token, inheritance_config)

        # Check cache first
        cache_key = self._generate_cache_key(inherited_token, token_hierarchy)
        if cache_key in self._resolution_cache:
            return self._resolution_cache[cache_key]

        try:
            # Determine inheritance mode and base style
            self._analyze_inheritance_configuration(inherited_token, inheritance_config)

            # Handle different inheritance modes
            if inherited_token.inheritance_mode == InheritanceMode.MANUAL_OVERRIDE:
                resolved_token = self._create_complete_style_token(inherited_token)
            elif inherited_token.inheritance_mode == InheritanceMode.COMPLETE:
                resolved_token = self._create_complete_style_token(inherited_token)
            else:
                # Auto or delta mode - resolve inheritance chain
                resolved_token = self._resolve_inheritance_chain(inherited_token, token_hierarchy)

            # Cache result
            self._resolution_cache[cache_key] = resolved_token
            return resolved_token

        except CircularInheritanceError as e:
            logger.error(f"Circular inheritance detected for token {inherited_token.id}: {e}")
            inherited_token.has_circular_reference = True
            return self._create_fallback_token(inherited_token)

        except MissingBaseStyleError as e:
            logger.error(f"Missing base style for token {inherited_token.id}: {e}")
            return self._create_fallback_token(inherited_token)

    def _convert_to_inherited_token(self, token: TypographyToken,
                                  inheritance_config: Optional[Dict[str, Any]]) -> InheritedTypographyToken:
        """Convert regular TypographyToken to InheritedTypographyToken"""
        return InheritedTypographyToken(
            id=token.id,
            font_family=token.font_family,
            font_size=token.font_size,
            font_weight=token.font_weight,
            line_height=token.line_height,
            letter_spacing=token.letter_spacing,
            font_style=token.font_style,
            text_decoration=token.text_decoration,
            text_transform=token.text_transform,
            font_size_emu=token.font_size_emu,
            line_height_emu=token.line_height_emu,
            letter_spacing_emu=token.letter_spacing_emu,
            baseline_grid_emu=token.baseline_grid_emu,
            wcag_level=token.wcag_level,
            min_contrast_ratio=token.min_contrast_ratio,
            ooxml_properties=token.ooxml_properties
        )

    def _analyze_inheritance_configuration(self, token: InheritedTypographyToken,
                                         inheritance_config: Optional[Dict[str, Any]]):
        """Analyze and apply inheritance configuration to token"""
        if inheritance_config:
            # Apply explicit configuration
            if 'baseStyle' in inheritance_config:
                token.base_style = inheritance_config['baseStyle']
            if 'mode' in inheritance_config:
                token.inheritance_mode = InheritanceMode(inheritance_config['mode'])
        else:
            # Infer inheritance configuration
            if not token.base_style:
                token.base_style = self._infer_base_style(token)
            if token.inheritance_mode is None:
                token.inheritance_mode = InheritanceMode.AUTO

    def _infer_base_style(self, token: InheritedTypographyToken) -> str:
        """Infer appropriate base style using OOXML conventions"""
        token_id_lower = token.id.lower()

        # Title styles
        if 'title' in token_id_lower:
            return "Title"

        # Heading styles
        if any(heading in token_id_lower for heading in ['heading', 'h1', 'h2', 'h3', 'display']):
            return "Heading1"

        # Character-level styles inherit from DefaultParagraphFont
        if any(char_style in token_id_lower for char_style in ['emphasis', 'strong', 'code', 'link']):
            return "DefaultParagraphFont"

        # Default to Normal for paragraph-level styles
        return "Normal"

    def _resolve_inheritance_chain(self, token: InheritedTypographyToken,
                                 token_hierarchy: Dict[str, TypographyToken]) -> InheritedTypographyToken:
        """Resolve complete inheritance chain with cycle detection"""
        inheritance_chain = []
        current_token = token
        visited_tokens = set()

        # Build inheritance chain
        while current_token and current_token.base_style:
            # Check for circular reference
            if current_token.id in visited_tokens:
                chain_cycle = inheritance_chain[inheritance_chain.index(current_token.id):]
                raise CircularInheritanceError(chain_cycle)

            visited_tokens.add(current_token.id)
            inheritance_chain.append(current_token.id)

            # Check depth limit
            if len(inheritance_chain) > self.max_inheritance_depth:
                logger.warning(f"Inheritance depth limit exceeded for token {token.id}")
                break

            # Move to base style or token
            if current_token.base_style in token_hierarchy:
                # Inheriting from another token
                base_token = token_hierarchy[current_token.base_style]
                if isinstance(base_token, InheritedTypographyToken):
                    current_token = base_token
                else:
                    current_token = self._convert_to_inherited_token(base_token, None)
            elif self.base_registry.has_style(current_token.base_style):
                # Inheriting from base style - end of chain
                break
            else:
                # Missing base style
                raise MissingBaseStyleError(token.id, current_token.base_style)

        # Set inheritance metadata
        token.inheritance_chain = inheritance_chain
        token.inheritance_depth = len(inheritance_chain)

        # Resolve base properties
        token.resolved_base_properties = self._resolve_base_properties(token)

        # Calculate delta properties
        token.delta_properties = self.delta_generator.generate_delta_properties(token)

        return token

    def _resolve_base_properties(self, token: InheritedTypographyToken) -> Dict[str, Any]:
        """Resolve final base properties from inheritance chain"""
        if not token.base_style:
            return {}

        base_style = self.base_registry.get_style(token.base_style)
        if base_style:
            return base_style.default_properties.copy()

        return {}

    def _create_complete_style_token(self, token: InheritedTypographyToken) -> InheritedTypographyToken:
        """Create token with complete style definition (no inheritance)"""
        token.inheritance_mode = InheritanceMode.COMPLETE
        token.base_style = None
        token.delta_properties = {}
        return token

    def _create_fallback_token(self, token: InheritedTypographyToken) -> InheritedTypographyToken:
        """Create fallback token when inheritance resolution fails"""
        logger.warning(f"Creating fallback token for {token.id}")
        return self._create_complete_style_token(token)

    def _generate_cache_key(self, token: InheritedTypographyToken,
                          token_hierarchy: Dict[str, TypographyToken]) -> str:
        """Generate cache key for inheritance resolution"""
        hierarchy_hash = hash(tuple(sorted(token_hierarchy.keys())))
        mode_value = token.inheritance_mode.value if isinstance(token.inheritance_mode, InheritanceMode) else str(token.inheritance_mode)
        return f"{token.id}:{token.base_style}:{mode_value}:{hierarchy_hash}"

    def validate_inheritance_tree(self, tokens: Dict[str, InheritedTypographyToken]) -> List[str]:
        """Validate entire inheritance tree for issues"""
        errors = []

        for token_id, token in tokens.items():
            try:
                # Check for circular references
                self._check_circular_inheritance(token_id, tokens)

                # Check for missing base styles
                if token.base_style and not self.base_registry.has_style(token.base_style) and token.base_style not in tokens:
                    errors.append(f"Token {token_id}: Missing base style '{token.base_style}'")

                # Validate delta properties
                if token.delta_properties:
                    delta_errors = self.delta_generator.validate_delta_properties(token.delta_properties)
                    for error in delta_errors:
                        errors.append(f"Token {token_id}: {error}")

            except CircularInheritanceError as e:
                errors.append(f"Token {token_id}: {str(e)}")

        return errors

    def _check_circular_inheritance(self, token_id: str, tokens: Dict[str, InheritedTypographyToken],
                                  visited: Optional[Set[str]] = None) -> bool:
        """Check for circular inheritance in token hierarchy"""
        if visited is None:
            visited = set()

        if token_id in visited:
            return True  # Circular dependency found

        token = tokens.get(token_id)
        if not token or not token.base_style:
            return False

        visited.add(token_id)

        # Check if base style is another token
        if token.base_style in tokens:
            return self._check_circular_inheritance(token.base_style, tokens, visited.copy())

        return False

    def clear_cache(self):
        """Clear inheritance resolution cache"""
        self._resolution_cache.clear()

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'cache_size': len(self._resolution_cache),
            'max_inheritance_depth': self.max_inheritance_depth
        }


# Factory functions for easy instantiation
def create_inheritance_system() -> Tuple[BaseStyleRegistry, DeltaStyleGenerator, InheritanceResolver]:
    """Create complete inheritance system with all components"""
    base_registry = BaseStyleRegistry()
    delta_generator = DeltaStyleGenerator(base_registry)
    inheritance_resolver = InheritanceResolver(base_registry, delta_generator)

    return base_registry, delta_generator, inheritance_resolver


def create_inherited_token_from_config(token_id: str,
                                     config: Dict[str, Any]) -> InheritedTypographyToken:
    """Create InheritedTypographyToken from configuration dictionary"""
    inheritance_config = config.get('inheritance', {})

    token = InheritedTypographyToken(
        id=token_id,
        font_family=config.get('fontFamily'),
        font_size=config.get('fontSize'),
        font_weight=config.get('fontWeight'),
        line_height=config.get('lineHeight'),
        letter_spacing=config.get('letterSpacing'),
        font_style=config.get('fontStyle'),
        text_decoration=config.get('textDecoration'),
        text_transform=config.get('textTransform'),
        base_style=inheritance_config.get('baseStyle'),
        inheritance_mode=InheritanceMode(inheritance_config.get('mode', 'auto'))
    )

    # Auto-populate delta_properties from the provided properties if inheritance is enabled
    if token.base_style and token.inheritance_mode in [InheritanceMode.AUTO, InheritanceMode.DELTA]:
        delta_props = {}
        for prop in ['fontFamily', 'fontSize', 'fontWeight', 'lineHeight', 'letterSpacing', 'fontStyle']:
            config_key = prop
            if config_key == 'fontFamily':
                config_key = 'fontFamily'
            elif config_key == 'fontSize':
                config_key = 'fontSize'
            elif config_key == 'fontWeight':
                config_key = 'fontWeight'
            elif config_key == 'lineHeight':
                config_key = 'lineHeight'
            elif config_key == 'letterSpacing':
                config_key = 'letterSpacing'
            elif config_key == 'fontStyle':
                config_key = 'fontStyle'

            if config_key in config:
                delta_props[prop] = config[config_key]

        if delta_props:
            token.delta_properties = delta_props

    return token


# Export main classes
__all__ = [
    'BaseStyleDefinition',
    'InheritedTypographyToken',
    'BaseStyleRegistry',
    'DeltaStyleGenerator',
    'InheritanceResolver',
    'InheritanceMode',
    'CircularInheritanceError',
    'MissingBaseStyleError',
    'create_inheritance_system',
    'create_inherited_token_from_config'
]


if __name__ == "__main__":
    # Demo usage
    print("🎨 StyleStack Style Inheritance Core Demo")
    print("=" * 50)

    # Create inheritance system
    registry, delta_gen, resolver = create_inheritance_system()

    print(f"📋 Base Style Registry: {len(registry.list_styles())} styles loaded")
    for style in registry.list_styles():
        print(f"   - {style.style_id} ({style.style_type})")

    # Create sample inherited token
    token_config = {
        'fontFamily': 'Proxima Nova',
        'fontSize': '14pt',
        'fontWeight': 600,
        'inheritance': {
            'baseStyle': 'Normal',
            'mode': 'auto'
        }
    }

    token = create_inherited_token_from_config('body_emphasis', token_config)
    resolved_token = resolver.resolve_inheritance(token)

    print(f"\n🔧 Resolved Token: {resolved_token.id}")
    print(f"   Base Style: {resolved_token.base_style}")
    print(f"   Inheritance Mode: {resolved_token.inheritance_mode.value}")
    print(f"   Should Generate Delta: {resolved_token.should_generate_delta()}")
    print(f"   Delta Properties: {resolved_token.delta_properties}")

    print("\n✅ Style inheritance core infrastructure ready!")