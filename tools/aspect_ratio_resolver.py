"""
StyleStack Aspect Ratio Token Resolver

Token-based aspect ratio resolution system enabling flexible, user-defined aspect ratios
instead of hardcoded values. Supports international paper sizes, custom ratios, and 
conditional token resolution with EMU precision.

Features:
- Token-defined aspect ratios (no hardcoded limitations)
- International paper size support (A4, Letter, custom)
- EMU precision calculations from mm/inches/pixels
- Conditional token resolution with nested references
- Schema validation and error handling
- Performance optimization with caching

Usage:
    resolver = AspectRatioResolver()
    
    # Resolve tokens for specific aspect ratio
    resolved = resolver.resolve_aspect_ratio_tokens(
        tokens, aspect_ratio_token="aspectRatios.widescreen"
    )
    
    # Get aspect ratio token definition
    ratio_token = resolver.get_aspect_ratio_token(tokens, "aspectRatios.a4_landscape")
"""

from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
import re
import json
import logging
from pathlib import Path
import hashlib

# Import existing StyleStack components
from tools.emu_types import EMUValue, mm_to_emu, inches_to_emu, pixels_to_emu
from tools.token_parser import TokenType, TokenScope

logger = logging.getLogger(__name__)


@dataclass
class AspectRatioToken:
    """Represents a token-defined aspect ratio with metadata"""
    name: str
    width_emu: int
    height_emu: int
    powerpoint_type: str
    token_path: str
    description: Optional[str] = None
    source_unit: Optional[str] = None
    source_value: Optional[Dict[str, float]] = None
    precision: str = "exact"
    
    @property
    def ratio_decimal(self) -> float:
        """Get decimal aspect ratio (width/height)"""
        return self.width_emu / self.height_emu
    
    @property
    def is_portrait(self) -> bool:
        """True if height > width (portrait orientation)"""
        return self.height_emu > self.width_emu
    
    @property
    def is_landscape(self) -> bool:
        """True if width > height (landscape orientation)"""
        return self.width_emu > self.height_emu
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "name": self.name,
            "width": str(self.width_emu),
            "height": str(self.height_emu),
            "powerpoint_type": self.powerpoint_type,
            "description": self.description
        }


class AspectRatioTokenError(Exception):
    """Exception raised for aspect ratio token operation errors"""
    pass


class AspectRatioResolver:
    """
    Resolves tokens with aspect ratio conditional values using token-defined aspect ratios.
    
    Supports:
    - Token-based aspect ratio definitions (no hardcoded values)
    - Conditional resolution with $aspectRatio syntax
    - International paper sizes with EMU precision
    - Nested token reference resolution
    - Performance optimization with caching
    """
    
    def __init__(self, verbose: bool = False, enable_cache: bool = True):
        self.verbose = verbose
        self.enable_cache = enable_cache
        
        # Resolution caches for performance
        self._aspect_ratio_cache: Dict[str, AspectRatioToken] = {}
        self._resolution_cache: Dict[str, Dict[str, Any]] = {}
        self._token_path_cache: Dict[str, Any] = {}
        
        # Token pattern matching
        self._aspect_ratio_token_pattern = re.compile(r'^\{aspectRatios\.([a-zA-Z][a-zA-Z0-9_]*)\}$')
        self._token_reference_pattern = re.compile(r'^\{([a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z][a-zA-Z0-9_]*)*)\}$')
        
        if verbose:
            logger.setLevel(logging.DEBUG)
    
    def resolve_aspect_ratio_tokens(self, 
                                  base_tokens: Dict[str, Any], 
                                  aspect_ratio_token: str) -> Dict[str, Any]:
        """
        Resolve tokens for specific aspect ratio using token-defined aspect ratios
        
        Args:
            base_tokens: Token structure with aspectRatios definitions and $aspectRatio conditions
            aspect_ratio_token: Token path to aspect ratio (e.g., "aspectRatios.widescreen")
            
        Returns:
            Resolved tokens with aspect ratio conditional values selected
            
        Raises:
            AspectRatioTokenError: If aspect ratio token not found or malformed
        """
        # Generate cache key
        cache_key = self._generate_cache_key(base_tokens, aspect_ratio_token)
        if self.enable_cache and cache_key in self._resolution_cache:
            if self.verbose:
                logger.debug(f"Cache hit for aspect ratio resolution: {aspect_ratio_token}")
            return self._resolution_cache[cache_key]
        
        # Validate aspect ratio token exists and is well-formed
        ratio_token = self.get_aspect_ratio_token(base_tokens, aspect_ratio_token)
        if not ratio_token:
            raise AspectRatioTokenError(f"Aspect ratio token not found: {aspect_ratio_token}")
        
        if self.verbose:
            logger.debug(f"Resolving tokens for aspect ratio: {ratio_token.name} ({ratio_token.width_emu}x{ratio_token.height_emu})")
        
        # Recursively resolve all tokens with aspect ratio conditions
        resolved = self._resolve_recursive(base_tokens, aspect_ratio_token, set())
        
        # Cache result
        if self.enable_cache:
            self._resolution_cache[cache_key] = resolved
        
        return resolved
    
    def get_aspect_ratio_token(self, tokens: Dict[str, Any], token_path: str) -> Optional[AspectRatioToken]:
        """
        Extract AspectRatioToken from token structure
        
        Args:
            tokens: Token structure containing aspectRatios definitions
            token_path: Path to aspect ratio token (e.g., "aspectRatios.widescreen")
            
        Returns:
            AspectRatioToken instance or None if not found
            
        Raises:
            AspectRatioTokenError: If token is malformed
        """
        # Check cache first
        cache_key = f"{hash(str(tokens))}:{token_path}"
        if self.enable_cache and cache_key in self._aspect_ratio_cache:
            return self._aspect_ratio_cache[cache_key]
        
        # Navigate to token using dot notation
        token_value = self._get_nested_value(tokens, token_path)
        if not token_value:
            return None
        
        # Validate token structure
        if not self._is_valid_aspect_ratio_token(token_value):
            raise AspectRatioTokenError(f"Malformed aspect ratio token: {token_path}")
        
        # Extract token data
        value_data = token_value["$value"]
        
        try:
            aspect_ratio_token = AspectRatioToken(
                name=value_data["name"],
                width_emu=int(value_data["width"]),
                height_emu=int(value_data["height"]), 
                powerpoint_type=value_data["powerpoint_type"],
                token_path=token_path,
                description=value_data.get("description")
            )
            
            # Extract extensions if present
            if "$extensions" in token_value:
                stylestack_ext = token_value["$extensions"].get("stylestack", {})
                if "emu" in stylestack_ext:
                    emu_data = stylestack_ext["emu"]
                    aspect_ratio_token.precision = emu_data.get("precision", "exact")
                    aspect_ratio_token.source_unit = emu_data.get("source_unit")
                    aspect_ratio_token.source_value = emu_data.get("source_value")
            
            # Cache result
            if self.enable_cache:
                self._aspect_ratio_cache[cache_key] = aspect_ratio_token
            
            return aspect_ratio_token
            
        except (KeyError, ValueError, TypeError) as e:
            raise AspectRatioTokenError(f"Error parsing aspect ratio token {token_path}: {e}")
    
    def list_available_aspect_ratios(self, tokens: Dict[str, Any]) -> List[AspectRatioToken]:
        """
        List all available aspect ratio tokens in token structure
        
        Args:
            tokens: Token structure containing aspectRatios
            
        Returns:
            List of AspectRatioToken instances
        """
        aspect_ratios = []
        
        if "aspectRatios" in tokens:
            for ratio_name in tokens["aspectRatios"].keys():
                token_path = f"aspectRatios.{ratio_name}"
                try:
                    ratio_token = self.get_aspect_ratio_token(tokens, token_path)
                    if ratio_token:
                        aspect_ratios.append(ratio_token)
                except AspectRatioTokenError:
                    if self.verbose:
                        logger.warning(f"Skipping malformed aspect ratio token: {token_path}")
                    continue
        
        return aspect_ratios
    
    def create_aspect_ratio_token_from_dimensions(self, 
                                                name: str,
                                                width_value: float,
                                                height_value: float,
                                                unit: str = "mm",
                                                powerpoint_type: str = "custom") -> Dict[str, Any]:
        """
        Create aspect ratio token from physical dimensions
        
        Args:
            name: Human-readable name
            width_value: Width in specified unit
            height_value: Height in specified unit  
            unit: Unit type ("mm", "inches", "pixels")
            powerpoint_type: PowerPoint slide size type
            
        Returns:
            Complete aspect ratio token structure
        """
        # Convert to EMU using existing unit converter
        if unit == "mm":
            width_emu = mm_to_emu(width_value).value
            height_emu = mm_to_emu(height_value).value
        elif unit == "inches":
            width_emu = inches_to_emu(width_value).value
            height_emu = inches_to_emu(height_value).value
        elif unit == "pixels":
            width_emu = pixels_to_emu(width_value).value
            height_emu = pixels_to_emu(height_value).value
        else:
            raise ValueError(f"Unsupported unit: {unit}")
        
        return {
            "$type": "aspectRatio",
            "$value": {
                "name": name,
                "width": str(width_emu),
                "height": str(height_emu),
                "powerpoint_type": powerpoint_type
            },
            "$extensions": {
                "stylestack": {
                    "emu": {
                        "precision": "exact",
                        "source_unit": unit,
                        "source_value": {
                            "width": width_value,
                            "height": height_value
                        }
                    }
                }
            }
        }
    
    # Helper methods
    
    def _resolve_recursive(self, 
                         obj: Any, 
                         aspect_ratio_token: str, 
                         visited: set) -> Any:
        """Recursively resolve aspect ratio conditions in token structure"""
        if isinstance(obj, dict):
            if "$aspectRatio" in obj:
                # Resolve aspect ratio conditional
                return self._resolve_aspect_ratio_conditional(obj["$aspectRatio"], aspect_ratio_token)
            else:
                # Recursively process dictionary
                resolved = {}
                for key, value in obj.items():
                    resolved[key] = self._resolve_recursive(value, aspect_ratio_token, visited)
                return resolved
        elif isinstance(obj, list):
            # Recursively process list
            return [self._resolve_recursive(item, aspect_ratio_token, visited) for item in obj]
        else:
            # Return primitive values as-is
            return obj
    
    def _resolve_aspect_ratio_conditional(self, 
                                        conditional: Dict[str, Any], 
                                        aspect_ratio_token: str) -> Any:
        """Resolve $aspectRatio conditional mapping"""
        # Look for exact aspect ratio token match
        aspect_ratio_key = f"{{{aspect_ratio_token}}}"
        
        if aspect_ratio_key in conditional:
            value = conditional[aspect_ratio_key]
            
            # Resolve token references in the value
            if isinstance(value, str) and self._token_reference_pattern.match(value):
                # This is a token reference - need to resolve it
                return self._resolve_token_reference(value)
            else:
                return value
        
        # Fallback to first available aspect ratio if exact match not found
        if conditional:
            first_key = next(iter(conditional.keys()))
            if self.verbose:
                logger.warning(f"Aspect ratio {aspect_ratio_token} not found in conditional, using fallback: {first_key}")
            value = conditional[first_key]
            
            if isinstance(value, str) and self._token_reference_pattern.match(value):
                return self._resolve_token_reference(value)
            else:
                return value
        
        raise AspectRatioTokenError(f"No aspect ratio conditions found for {aspect_ratio_token}")
    
    def _resolve_token_reference(self, token_ref: str) -> str:
        """Resolve token reference like {aspectRatios.widescreen.$value.width}"""
        # Extract path from token reference
        match = self._token_reference_pattern.match(token_ref)
        if not match:
            return token_ref
        
        token_path = match.group(1)
        
        # For now, return the token reference as-is
        # Full token reference resolution would integrate with variable_resolver.py
        return token_ref
    
    def _get_nested_value(self, obj: Dict[str, Any], dot_path: str) -> Any:
        """Get nested dictionary value using dot notation path"""
        keys = dot_path.split('.')
        current = obj
        
        try:
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None
            return current
        except (KeyError, TypeError):
            return None
    
    def _is_valid_aspect_ratio_token(self, token: Dict[str, Any]) -> bool:
        """Validate aspect ratio token structure"""
        try:
            return (
                token.get("$type") == "aspectRatio" and
                "$value" in token and
                isinstance(token["$value"], dict) and
                "name" in token["$value"] and
                "width" in token["$value"] and
                "height" in token["$value"] and
                "powerpoint_type" in token["$value"] and
                token["$value"]["width"].isdigit() and
                token["$value"]["height"].isdigit()
            )
        except (AttributeError, TypeError):
            return False
    
    def _generate_cache_key(self, tokens: Dict[str, Any], aspect_ratio_token: str) -> str:
        """Generate cache key for resolution results"""
        tokens_hash = hashlib.md5(json.dumps(tokens, sort_keys=True).encode()).hexdigest()
        return f"{tokens_hash}:{aspect_ratio_token}"


# Utility functions for common aspect ratios

def create_standard_aspect_ratios() -> Dict[str, Dict[str, Any]]:
    """
    Create standard aspect ratio token definitions using existing unit converters
    
    Returns:
        Dictionary with common aspect ratios (presentation, document, international)
    """
    resolver = AspectRatioResolver()
    
    return {
        "aspectRatios": {
            "widescreen_16_9": resolver.create_aspect_ratio_token_from_dimensions(
                "16:9 Widescreen", 13.33, 7.5, "inches", "screen16x9"
            ),
            "standard_16_10": resolver.create_aspect_ratio_token_from_dimensions(
                "16:10 Standard", 12.0, 7.5, "inches", "screen16x10"
            ),
            "classic_4_3": resolver.create_aspect_ratio_token_from_dimensions(
                "4:3 Classic", 10.0, 7.5, "inches", "screen4x3"
            ),
            "a4_landscape": resolver.create_aspect_ratio_token_from_dimensions(
                "A4 Landscape", 297, 210, "mm", "custom"
            ),
            "a4_portrait": resolver.create_aspect_ratio_token_from_dimensions(
                "A4 Portrait", 210, 297, "mm", "custom"
            ),
            "letter_landscape": resolver.create_aspect_ratio_token_from_dimensions(
                "Letter Landscape", 11.0, 8.5, "inches", "custom"
            ),
            "letter_portrait": resolver.create_aspect_ratio_token_from_dimensions(
                "Letter Portrait", 8.5, 11.0, "inches", "custom"
            )
        }
    }


if __name__ == "__main__":
    # Example usage and testing
    resolver = AspectRatioResolver(verbose=True)
    
    # Create sample tokens with aspect ratios
    tokens = create_standard_aspect_ratios()
    tokens.update({
        "layout": {
            "slide": {
                "width": {
                    "$aspectRatio": {
                        "{aspectRatios.widescreen_16_9}": "{aspectRatios.widescreen_16_9.$value.width}",
                        "{aspectRatios.a4_landscape}": "{aspectRatios.a4_landscape.$value.width}"
                    }
                }
            }
        }
    })
    
    # Test resolution
    resolved = resolver.resolve_aspect_ratio_tokens(tokens, "aspectRatios.widescreen_16_9")
    print(f"Resolved layout width: {resolved['layout']['slide']['width']}")
    
    # List available aspect ratios
    ratios = resolver.list_available_aspect_ratios(tokens)
    print(f"Available aspect ratios: {[r.name for r in ratios]}")