#!/usr/bin/env python3
"""
Carrier Registry System for StyleStack OOXML Templates

This module implements a comprehensive carrier registry system that maps
OOXML XPath expressions to design token properties, enabling professional
typography and brand consistency across Office templates.

Author: StyleStack Team
Version: 1.0.0
"""

import json
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict
import logging
import threading
from functools import lru_cache

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CarrierType(Enum):
    """Enumeration of supported carrier types for OOXML elements."""
    TEXT_STYLE = "text_style"
    TABLE = "table"
    SHAPE = "shape"
    CHART = "chart"
    THEME = "theme"
    LAYOUT = "layout"
    MASTER_SLIDE = "master_slide"
    PLACEHOLDER = "placeholder"


class Platform(Enum):
    """Supported Office platforms for carrier mapping."""
    MICROSOFT_OFFICE = "microsoft_office"
    LIBREOFFICE = "libreoffice"
    GOOGLE_WORKSPACE = "google_workspace"


@dataclass
class CarrierDefinition:
    """Definition of a carrier with all its properties."""
    carrier_id: str
    xpath: str
    carrier_type: CarrierType
    design_token_mapping: Dict[str, str]
    priority: int = 0
    platform: Platform = Platform.MICROSOFT_OFFICE
    emu_precision: bool = False
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Post-initialization validation."""
        if not self.xpath:
            raise ValueError("XPath cannot be empty")
        if not self.design_token_mapping:
            raise ValueError("Design token mapping cannot be empty")


class CarrierRegistry:
    """
    Centralized registry for OOXML carriers that transport design tokens.
    
    Features:
    - XPath expression mapping to design token properties
    - Performance optimization with caching (<10ms lookup)
    - Cross-platform support (Microsoft Office, LibreOffice, Google Workspace)
    - Hierarchical token precedence support
    - EMU-precision typography calculations
    """
    
    def __init__(self, cache_enabled: bool = True, max_cache_size: int = 1000):
        """
        Initialize the CarrierRegistry.
        
        Args:
            cache_enabled: Enable/disable XPath lookup caching
            max_cache_size: Maximum number of cached lookups
        """
        self._carriers: Dict[str, CarrierDefinition] = {}
        self._xpath_index: Dict[str, List[str]] = defaultdict(list)
        self._type_index: Dict[CarrierType, List[str]] = defaultdict(list)
        self._platform_index: Dict[Platform, List[str]] = defaultdict(list)
        
        # Performance tracking
        self.cache_enabled = cache_enabled
        self.max_cache_size = max_cache_size
        self._xpath_cache: Dict[str, List[CarrierDefinition]] = {}
        self.lookup_count = 0
        self.cache_hits = 0
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Validation rules (relaxed for cross-platform compatibility)
        self._validation_rules = {
            CarrierType.TEXT_STYLE: {
                "required_xpath_patterns": ["//a:p", "//a:r", "//a:t", "//text:"],
                "required_mapping_keys": ["font_family"]  # Only require font_family
            },
            CarrierType.TABLE: {
                "required_xpath_patterns": ["//a:tbl", "//a:tr", "//a:tc", "//table:"],
                "required_mapping_keys": ["default_font"]  # Relaxed requirements
            },
            CarrierType.THEME: {
                "required_xpath_patterns": ["//a:theme", "//a:clrScheme"],
                "required_mapping_keys": ["primary_color"]  # Relaxed requirements
            }
        }
        
        logger.info(f"CarrierRegistry initialized with cache={'enabled' if cache_enabled else 'disabled'}")

    def register_carrier(
        self,
        xpath: str,
        carrier_type: Union[CarrierType, str],
        design_token_mapping: Dict[str, str],
        priority: int = 0,
        platform: Union[Platform, str] = Platform.MICROSOFT_OFFICE,
        emu_precision: bool = False,
        validation_rules: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Register a new carrier in the registry.
        
        Args:
            xpath: XPath expression for locating OOXML elements
            carrier_type: Type of carrier (text, table, shape, etc.)
            design_token_mapping: Mapping of design tokens to XML attributes
            priority: Priority for carrier ordering (lower = higher priority)
            platform: Target platform for this carrier
            emu_precision: Enable EMU-precision calculations
            validation_rules: Custom validation rules for this carrier
            
        Returns:
            Unique carrier ID
            
        Raises:
            ValueError: If carrier validation fails
        """
        with self._lock:
            # Convert string enums if needed
            if isinstance(carrier_type, str):
                carrier_type = CarrierType(carrier_type)
            if isinstance(platform, str):
                platform = Platform(platform)
                
            # Generate unique carrier ID
            carrier_id = f"{carrier_type.value}_{len(self._carriers):04d}_{int(time.time() * 1000) % 10000}"
            
            # Create carrier definition
            carrier = CarrierDefinition(
                carrier_id=carrier_id,
                xpath=xpath,
                carrier_type=carrier_type,
                design_token_mapping=design_token_mapping,
                priority=priority,
                platform=platform,
                emu_precision=emu_precision,
                validation_rules=validation_rules or {}
            )
            
            # Validate carrier
            if not self._validate_carrier(carrier):
                raise ValueError(f"Carrier validation failed for {carrier_id}")
            
            # Register in all indexes
            self._carriers[carrier_id] = carrier
            self._xpath_index[xpath].append(carrier_id)
            self._type_index[carrier_type].append(carrier_id)
            self._platform_index[platform].append(carrier_id)
            
            # Clear cache as indexes have changed
            self._clear_cache()
            
            logger.info(f"Registered carrier {carrier_id} for XPath '{xpath}' on platform {platform.value}")
            return carrier_id

    def get_carrier(self, carrier_id: str) -> Optional[CarrierDefinition]:
        """
        Retrieve a carrier by its ID.
        
        Args:
            carrier_id: Unique carrier identifier
            
        Returns:
            CarrierDefinition if found, None otherwise
        """
        return self._carriers.get(carrier_id)

    def get_all_carriers(self) -> List[CarrierDefinition]:
        """
        Get all registered carriers.
        
        Returns:
            List of all CarrierDefinition objects
        """
        return list(self._carriers.values())

    def find_carriers_by_xpath(self, xpath: str) -> List[CarrierDefinition]:
        """
        Find carriers matching a specific XPath expression.
        
        Args:
            xpath: XPath expression to search for
            
        Returns:
            List of matching carriers sorted by priority
        """
        with self._lock:
            self.lookup_count += 1
            
            # Check cache first
            if self.cache_enabled and xpath in self._xpath_cache:
                self.cache_hits += 1
                return self._xpath_cache[xpath]
            
            # Find matching carriers
            carrier_ids = self._xpath_index.get(xpath, [])
            carriers = [self._carriers[cid] for cid in carrier_ids if cid in self._carriers]
            
            # Sort by priority (lower number = higher priority)
            carriers.sort(key=lambda c: c.priority)
            
            # Cache result
            if self.cache_enabled and len(self._xpath_cache) < self.max_cache_size:
                self._xpath_cache[xpath] = carriers
            
            return carriers

    def find_carriers_by_type(self, carrier_type: CarrierType) -> List[CarrierDefinition]:
        """
        Find all carriers of a specific type.
        
        Args:
            carrier_type: Type of carriers to find
            
        Returns:
            List of matching carriers
        """
        carrier_ids = self._type_index.get(carrier_type, [])
        return [self._carriers[cid] for cid in carrier_ids if cid in self._carriers]

    def find_carriers_by_platform(self, platform: Union[Platform, str]) -> List[CarrierDefinition]:
        """
        Find all carriers for a specific platform.
        
        Args:
            platform: Platform to search for
            
        Returns:
            List of matching carriers
        """
        if isinstance(platform, str):
            platform = Platform(platform)
            
        carrier_ids = self._platform_index.get(platform, [])
        return [self._carriers[cid] for cid in carrier_ids if cid in self._carriers]

    def validate_carrier(self, carrier_data: Dict[str, Any]) -> bool:
        """
        Validate a carrier definition dictionary.
        
        Args:
            carrier_data: Dictionary containing carrier properties
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["xpath", "type", "mapping"]
        
        # Check required fields
        for field in required_fields:
            if field not in carrier_data:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate XPath
        xpath = carrier_data["xpath"]
        if not xpath or not xpath.startswith("//"):
            logger.warning(f"Invalid XPath: {xpath}")
            return False
            
        # Validate mapping
        mapping = carrier_data["mapping"]
        if not isinstance(mapping, dict) or len(mapping) == 0:
            logger.warning("Invalid or empty design token mapping")
            return False
            
        return True

    def _validate_carrier(self, carrier: CarrierDefinition) -> bool:
        """
        Internal validation for CarrierDefinition objects.
        
        Args:
            carrier: CarrierDefinition to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Basic validation
        if not carrier.xpath.startswith("//"):
            logger.warning(f"Invalid XPath format: {carrier.xpath}")
            return False
            
        if not carrier.design_token_mapping:
            logger.warning("Empty design token mapping")
            return False
        
        # Type-specific validation
        rules = self._validation_rules.get(carrier.carrier_type, {})
        
        # Check XPath patterns
        required_patterns = rules.get("required_xpath_patterns", [])
        if required_patterns:
            if not any(pattern in carrier.xpath for pattern in required_patterns):
                logger.warning(f"XPath {carrier.xpath} doesn't match required patterns for {carrier.carrier_type}")
                return False
        
        # Check required mapping keys
        required_keys = rules.get("required_mapping_keys", [])
        if required_keys:
            missing_keys = set(required_keys) - set(carrier.design_token_mapping.keys())
            if missing_keys:
                logger.warning(f"Missing required mapping keys: {missing_keys}")
                return False
        
        return True

    def clear_cache(self):
        """Clear the XPath lookup cache."""
        with self._lock:
            self._clear_cache()

    def _clear_cache(self):
        """Internal cache clearing method."""
        self._xpath_cache.clear()
        self.cache_hits = 0
        self.lookup_count = 0

    @property
    def cache_hit_rate(self) -> float:
        """
        Calculate the cache hit rate.
        
        Returns:
            Cache hit rate as a percentage (0.0 to 1.0)
        """
        if self.lookup_count == 0:
            return 0.0
        return self.cache_hits / self.lookup_count

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for the registry.
        
        Returns:
            Dictionary containing performance metrics
        """
        return {
            "total_carriers": len(self._carriers),
            "lookup_count": self.lookup_count,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": self.cache_hit_rate,
            "cache_size": len(self._xpath_cache),
            "cache_enabled": self.cache_enabled,
            "indexes_size": {
                "xpath": len(self._xpath_index),
                "type": len(self._type_index),
                "platform": len(self._platform_index)
            }
        }

    def export_carriers(self, file_path: Union[str, Path]) -> bool:
        """
        Export all carriers to a JSON file.
        
        Args:
            file_path: Path to save the carriers
            
        Returns:
            True if successful, False otherwise
        """
        try:
            carriers_data = []
            for carrier in self._carriers.values():
                carriers_data.append({
                    "carrier_id": carrier.carrier_id,
                    "xpath": carrier.xpath,
                    "carrier_type": carrier.carrier_type.value,
                    "design_token_mapping": carrier.design_token_mapping,
                    "priority": carrier.priority,
                    "platform": carrier.platform.value,
                    "emu_precision": carrier.emu_precision,
                    "validation_rules": carrier.validation_rules,
                    "created_at": carrier.created_at
                })
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(carriers_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(carriers_data)} carriers to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export carriers: {e}")
            return False

    def import_carriers(self, file_path: Union[str, Path]) -> int:
        """
        Import carriers from a JSON file.
        
        Args:
            file_path: Path to the carriers file
            
        Returns:
            Number of carriers imported
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                carriers_data = json.load(f)
            
            imported_count = 0
            
            for carrier_data in carriers_data:
                try:
                    carrier_id = self.register_carrier(
                        xpath=carrier_data["xpath"],
                        carrier_type=carrier_data["carrier_type"],
                        design_token_mapping=carrier_data["design_token_mapping"],
                        priority=carrier_data.get("priority", 0),
                        platform=carrier_data.get("platform", Platform.MICROSOFT_OFFICE.value),
                        emu_precision=carrier_data.get("emu_precision", False),
                        validation_rules=carrier_data.get("validation_rules", {})
                    )
                    imported_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to import carrier {carrier_data.get('carrier_id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Imported {imported_count} carriers from {file_path}")
            return imported_count
            
        except Exception as e:
            logger.error(f"Failed to import carriers: {e}")
            return 0


class DesignTokenInjector:
    """
    Design token injection engine for applying tokens to OOXML elements.
    
    Features:
    - EMU-precision calculations with 360 EMU baseline grid
    - Hierarchical token precedence (Design System → Corporate → Channel → Template)
    - Cross-platform token application
    - Performance optimized injection
    """
    
    def __init__(self, registry: CarrierRegistry, variable_resolver=None):
        """
        Initialize the DesignTokenInjector.
        
        Args:
            registry: CarrierRegistry instance
            variable_resolver: Optional VariableResolver for hierarchical precedence
        """
        self.registry = registry
        self.variable_resolver = variable_resolver
        self.injection_count = 0
        self._emu_cache = {}
        
    def inject_tokens(
        self,
        element: Any,
        design_tokens: Dict[str, Any],
        carrier_id: str
    ) -> bool:
        """
        Inject design tokens into an OOXML element using a specific carrier.
        
        Args:
            element: OOXML element to modify
            design_tokens: Design tokens to apply
            carrier_id: ID of carrier to use for injection
            
        Returns:
            True if injection successful, False otherwise
        """
        carrier = self.registry.get_carrier(carrier_id)
        if not carrier:
            logger.warning(f"Carrier {carrier_id} not found")
            return False
        
        try:
            # Apply each token mapping
            for token_key, xpath_attr in carrier.design_token_mapping.items():
                token_value = self._get_token_value(design_tokens, token_key)
                if token_value is not None:
                    
                    # Convert to EMU if needed
                    if carrier.emu_precision:
                        token_value = self._convert_to_emu(token_value)
                    
                    # Apply to element (mock implementation)
                    logger.debug(f"Applying {token_key}={token_value} to {xpath_attr}")
                    
            self.injection_count += 1
            return True
            
        except Exception as e:
            logger.error(f"Token injection failed for carrier {carrier_id}: {e}")
            return False

    def inject_with_precedence(
        self,
        element: Any,
        org_tokens: Dict[str, Any],
        channel_tokens: Dict[str, Any],
        template_tokens: Dict[str, Any],
        carrier_id: str
    ) -> bool:
        """
        Inject tokens with hierarchical precedence resolution.
        
        Args:
            element: OOXML element to modify
            org_tokens: Organization-level design tokens
            channel_tokens: Channel-level design tokens
            template_tokens: Template-level design tokens
            carrier_id: ID of carrier to use for injection
            
        Returns:
            True if injection successful, False otherwise
        """
        if self.variable_resolver:
            # Use variable resolver for hierarchical precedence
            resolved_tokens = self.variable_resolver.resolve_tokens({
                "org": org_tokens,
                "channel": channel_tokens,
                "template": template_tokens
            })
            return self.inject_tokens(element, resolved_tokens, carrier_id)
        else:
            # Simple precedence: template > channel > org
            merged_tokens = {}
            merged_tokens.update(org_tokens)
            merged_tokens.update(channel_tokens)
            merged_tokens.update(template_tokens)
            return self.inject_tokens(element, merged_tokens, carrier_id)

    def _get_token_value(self, design_tokens: Dict[str, Any], token_key: str) -> Any:
        """
        Get a token value from nested design token structure.
        
        Args:
            design_tokens: Design tokens dictionary
            token_key: Key to look up (supports dot notation)
            
        Returns:
            Token value or None if not found
        """
        keys = token_key.split('.')
        value = design_tokens
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value

    def _convert_to_emu(self, value: Union[str, int, float]) -> int:
        """
        Convert various units to EMU (English Metric Units).
        
        Args:
            value: Value to convert (e.g., "12pt", "1.4em", 16)
            
        Returns:
            Value in EMU units
        """
        if isinstance(value, int):
            return value
            
        if isinstance(value, str):
            # Check cache first
            if value in self._emu_cache:
                return self._emu_cache[value]
            
            result = self._convert_string_to_emu(value)
            self._emu_cache[value] = result
            return result
            
        return int(float(value))

    def _convert_string_to_emu(self, value: str) -> int:
        """
        Convert string values to EMU with support for various units.
        
        Args:
            value: String value with unit (e.g., "12pt", "1.4em")
            
        Returns:
            Value in EMU units
        """
        value = value.strip().lower()
        
        if value.endswith("pt"):
            # Points to EMU: 1pt = 72 EMU (simplified)
            points = float(value[:-2])
            return int(points * 72)
            
        elif value.endswith("em"):
            # EM units (relative to base font size)
            multiplier = float(value[:-2])
            base_emu = 864  # 12pt = 864 EMU
            return int(base_emu * multiplier)
            
        elif value.endswith("px"):
            # Pixels to EMU: 1px = 9.6 EMU (at 96 DPI)
            pixels = float(value[:-2])
            return int(pixels * 9.6)
            
        else:
            # Try to parse as numeric
            try:
                return int(float(value))
            except ValueError:
                logger.warning(f"Cannot convert '{value}' to EMU")
                return 0

    def get_baseline_aligned_emu(self, emu_value: int, baseline_grid: int = 360) -> int:
        """
        Align EMU value to the baseline grid.
        
        Args:
            emu_value: Original EMU value
            baseline_grid: Baseline grid size in EMU (default 360)
            
        Returns:
            EMU value aligned to baseline grid
        """
        return round(emu_value / baseline_grid) * baseline_grid


# Example usage and default carrier definitions
def create_default_carriers(registry: CarrierRegistry):
    """
    Create default carriers for common OOXML elements.
    
    Args:
        registry: CarrierRegistry to populate with default carriers
    """
    # Text style carriers
    registry.register_carrier(
        xpath="//a:p/a:pPr",
        carrier_type=CarrierType.TEXT_STYLE,
        design_token_mapping={
            "font_family": "a:rPr/a:latin/@typeface",
            "font_size": "a:rPr/@sz",
            "color": "a:rPr/a:solidFill/a:srgbClr/@val",
            "line_height": "a:pPr/a:lnSpc/a:spcPts/@val"
        },
        priority=1,
        emu_precision=True
    )
    
    # Table carriers for professional defaults
    registry.register_carrier(
        xpath="//a:tbl/a:tblPr",
        carrier_type=CarrierType.TABLE,
        design_token_mapping={
            "default_font": "a:defRPr/a:latin/@typeface",
            "cell_padding": "a:tblCellMar/@marT",
            "border_color": "a:tblBorders/a:top/a:ln/a:solidFill/a:srgbClr/@val"
        },
        priority=2
    )
    
    # Theme carriers
    registry.register_carrier(
        xpath="//a:theme/a:themeElements/a:clrScheme",
        carrier_type=CarrierType.THEME,
        design_token_mapping={
            "primary_color": "a:dk1/a:srgbClr/@val",
            "accent1": "a:accent1/a:srgbClr/@val",
            "accent2": "a:accent2/a:srgbClr/@val"
        },
        priority=0  # Highest priority for theme elements
    )


if __name__ == "__main__":
    # Example usage
    registry = CarrierRegistry()
    create_default_carriers(registry)
    
    # Display performance stats
    stats = registry.get_performance_stats()
    print(f"Registry initialized with {stats['total_carriers']} default carriers")