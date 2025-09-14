"""
Carrier Variable Processing Module

This module provides carrier-specific variable processing with semantic resolution,
EMU precision calculations, and hierarchical design token precedence support.
"""

import re
from typing import Dict, Any, List, Optional, Tuple, Union
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from enum import Enum

from .types import SubstitutionError, SubstitutionStage


class CarrierVariableType(Enum):
    """Types of carrier variables"""
    EMU = "emu"           # EMU unit values (spacing, typography, shapes)
    COLOR = "color"       # Color values (hex, rgb, theme colors)
    TEXT = "text"         # Text content (font names, labels)
    NUMERIC = "numeric"   # Numeric values (counts, percentages)
    BOOLEAN = "boolean"   # Boolean flags
    REFERENCE = "reference"  # References to other variables


@dataclass
class CarrierVariableDefinition:
    """Definition of a carrier variable"""
    path: str                           # e.g., "typography.body.font_size_emu"
    variable_type: CarrierVariableType  # Type classification
    value: Any                          # Resolved value
    source_layer: Optional[str] = None  # Token layer source
    xpath: Optional[str] = None         # Target XPath for application
    validation_rules: Optional[Dict[str, Any]] = None  # Validation constraints


@dataclass
class EMUValidationResult:
    """Result of EMU value validation"""
    is_valid: bool
    value: int
    deviation: int
    baseline_grid: int
    error_message: Optional[str] = None


class CarrierVariablePatternMatcher:
    """Matcher for carrier variable syntax patterns"""
    
    # Enhanced pattern for carrier variables: {{carrier.property.value_emu}}
    CARRIER_PATTERN = re.compile(
        r'\{\{([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)\}\}'
    )
    
    # Pattern to detect EMU unit variables
    EMU_PATTERN = re.compile(r'.*_emu$')
    
    # Pattern to detect color variables
    COLOR_PATTERN = re.compile(r'.*\.(color|background|foreground|border|text)$')
    
    @classmethod
    def find_carrier_variables(cls, content: str) -> List[str]:
        """Find all carrier variables in content"""
        matches = cls.CARRIER_PATTERN.findall(content)
        return matches
    
    @classmethod
    def is_valid_carrier_variable(cls, variable_text: str) -> bool:
        """Validate carrier variable syntax"""
        return cls.CARRIER_PATTERN.match(variable_text) is not None
    
    @classmethod
    def classify_variable_type(cls, variable_path: str) -> CarrierVariableType:
        """Classify the type of carrier variable based on path"""
        if cls.EMU_PATTERN.match(variable_path):
            return CarrierVariableType.EMU
        elif cls.COLOR_PATTERN.match(variable_path):
            return CarrierVariableType.COLOR
        elif variable_path.endswith('_count') or variable_path.endswith('_percentage'):
            return CarrierVariableType.NUMERIC
        elif variable_path.endswith('_enabled') or variable_path.endswith('_visible'):
            return CarrierVariableType.BOOLEAN
        elif variable_path.startswith('ref.'):
            return CarrierVariableType.REFERENCE
        else:
            return CarrierVariableType.TEXT


class EMUCalculationEngine:
    """Engine for precise EMU calculations with baseline grid alignment"""
    
    BASELINE_GRID_EMU = 360      # 360 EMU = 1pt baseline grid
    MAX_DEVIATION_EMU = 1        # Maximum allowed deviation
    STANDARD_DPI = 72           # Standard DPI for calculations
    
    @classmethod
    def points_to_emu(cls, points: float) -> int:
        """Convert points to EMU with baseline grid alignment"""
        precise_emu = points * cls.BASELINE_GRID_EMU
        return int(round(precise_emu))
    
    @classmethod
    def emu_to_points(cls, emu: int) -> float:
        """Convert EMU to points"""
        return emu / cls.BASELINE_GRID_EMU
    
    @classmethod
    def validate_emu_precision(cls, emu_value: int) -> EMUValidationResult:
        """Validate EMU value precision against baseline grid"""
        remainder = emu_value % cls.BASELINE_GRID_EMU
        
        if remainder == 0:
            return EMUValidationResult(
                is_valid=True,
                value=emu_value,
                deviation=0,
                baseline_grid=cls.BASELINE_GRID_EMU
            )
        else:
            # Calculate deviation from nearest grid line
            deviation = min(remainder, cls.BASELINE_GRID_EMU - remainder)
            is_valid = deviation < cls.MAX_DEVIATION_EMU
            
            error_message = None
            if not is_valid:
                nearest_grid = emu_value - remainder if remainder < cls.BASELINE_GRID_EMU / 2 else emu_value + (cls.BASELINE_GRID_EMU - remainder)
                error_message = f"EMU value {emu_value} deviates {deviation} EMU from baseline grid. Nearest aligned value: {nearest_grid}"
            
            return EMUValidationResult(
                is_valid=is_valid,
                value=emu_value,
                deviation=deviation,
                baseline_grid=cls.BASELINE_GRID_EMU,
                error_message=error_message
            )
    
    @classmethod
    def align_to_baseline_grid(cls, emu_value: int) -> int:
        """Align EMU value to nearest baseline grid line"""
        remainder = emu_value % cls.BASELINE_GRID_EMU
        
        if remainder == 0:
            return emu_value
        
        if remainder < cls.BASELINE_GRID_EMU / 2:
            return emu_value - remainder
        else:
            return emu_value + (cls.BASELINE_GRID_EMU - remainder)


class HierarchicalTokenResolver:
    """Resolver for hierarchical design token precedence"""
    
    def __init__(self):
        """Initialize the token resolver"""
        self.token_layers = []
        self.resolved_cache = {}
        self.cache_valid = False
    
    def add_token_layer(self, layer_name: str, tokens: Dict[str, Any], precedence: int):
        """Add a token layer with precedence (higher number = higher precedence)"""
        self.token_layers.append({
            'name': layer_name,
            'tokens': tokens,
            'precedence': precedence
        })
        
        # Sort by precedence (highest first)
        self.token_layers.sort(key=lambda x: x['precedence'], reverse=True)
        
        # Invalidate cache
        self.cache_valid = False
        self.resolved_cache = {}
    
    def resolve_token(self, token_path: str) -> Tuple[Optional[Any], Optional[str]]:
        """Resolve token value using hierarchical precedence"""
        for layer in self.token_layers:
            if token_path in layer['tokens']:
                return layer['tokens'][token_path], layer['name']
        return None, None
    
    def get_resolved_tokens(self) -> Dict[str, Any]:
        """Get all resolved tokens with precedence applied"""
        if self.cache_valid:
            return self.resolved_cache.copy()
        
        resolved = {}
        
        # Start with lowest precedence and override with higher precedence
        for layer in reversed(self.token_layers):
            resolved.update(layer['tokens'])
        
        self.resolved_cache = resolved
        self.cache_valid = True
        
        return resolved.copy()
    
    def clear_cache(self):
        """Clear the resolution cache"""
        self.resolved_cache = {}
        self.cache_valid = False


class CarrierVariableProcessor:
    """Processor for carrier-specific variable resolution with semantic understanding"""
    
    def __init__(self, enable_emu_validation: bool = True, enable_caching: bool = True):
        """Initialize the carrier variable processor"""
        self.pattern_matcher = CarrierVariablePatternMatcher()
        self.emu_engine = EMUCalculationEngine()
        self.token_resolver = HierarchicalTokenResolver()
        self.enable_emu_validation = enable_emu_validation
        self.enable_caching = enable_caching
        
        # Processing cache
        self.variable_cache = {} if enable_caching else None
        
        # Statistics
        self.stats = {
            'variables_processed': 0,
            'emu_values_validated': 0,
            'emu_validation_failures': 0,
            'token_resolution_hits': 0,
            'token_resolution_misses': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def add_design_token_layer(self, layer_name: str, tokens: Dict[str, Any], precedence: int):
        """Add a design token layer for hierarchical resolution"""
        self.token_resolver.add_token_layer(layer_name, tokens, precedence)
        
        # Clear processing cache when token layers change
        if self.enable_caching:
            self.variable_cache = {}
    
    def process_carrier_variables(self, content: str) -> Tuple[List[CarrierVariableDefinition], List[SubstitutionError]]:
        """Process all carrier variables found in content"""
        variables = []
        errors = []
        
        # Find all carrier variables
        variable_paths = self.pattern_matcher.find_carrier_variables(content)
        
        for variable_path in variable_paths:
            try:
                # Check cache first
                if self.enable_caching and variable_path in self.variable_cache:
                    variables.append(self.variable_cache[variable_path])
                    self.stats['cache_hits'] += 1
                    continue
                
                self.stats['cache_misses'] += 1
                
                # Process individual variable
                variable_def = self._process_single_variable(variable_path)
                
                if variable_def:
                    variables.append(variable_def)
                    
                    # Cache result
                    if self.enable_caching:
                        self.variable_cache[variable_path] = variable_def
                else:
                    error = SubstitutionError(
                        error_type="variable_resolution_failed",
                        message=f"Failed to resolve carrier variable: {variable_path}",
                        stage=SubstitutionStage.RESOLVING
                    )
                    errors.append(error)
                    self.stats['token_resolution_misses'] += 1
                
            except Exception as e:
                error = SubstitutionError(
                    error_type="variable_processing_error",
                    message=f"Error processing carrier variable {variable_path}: {str(e)}",
                    stage=SubstitutionStage.RESOLVING,
                    details={'variable_path': variable_path, 'exception': str(e)}
                )
                errors.append(error)
        
        self.stats['variables_processed'] += len(variable_paths)
        return variables, errors
    
    def _process_single_variable(self, variable_path: str) -> Optional[CarrierVariableDefinition]:
        """Process a single carrier variable"""
        # Classify variable type
        variable_type = self.pattern_matcher.classify_variable_type(variable_path)
        
        # Resolve value from token hierarchy
        resolved_value, source_layer = self.token_resolver.resolve_token(variable_path)
        
        if resolved_value is None:
            return None
        
        self.stats['token_resolution_hits'] += 1
        
        # Create variable definition
        variable_def = CarrierVariableDefinition(
            path=variable_path,
            variable_type=variable_type,
            value=resolved_value,
            source_layer=source_layer
        )
        
        # Perform type-specific processing
        if variable_type == CarrierVariableType.EMU and self.enable_emu_validation:
            self._validate_emu_variable(variable_def)
        elif variable_type == CarrierVariableType.COLOR:
            self._process_color_variable(variable_def)
        
        return variable_def
    
    def _validate_emu_variable(self, variable_def: CarrierVariableDefinition):
        """Validate EMU variable for precision and alignment"""
        self.stats['emu_values_validated'] += 1
        
        try:
            emu_value = int(variable_def.value)
            validation_result = self.emu_engine.validate_emu_precision(emu_value)
            
            if not validation_result.is_valid:
                self.stats['emu_validation_failures'] += 1
                
                # Store validation information
                variable_def.validation_rules = {
                    'emu_validation': {
                        'is_valid': False,
                        'deviation': validation_result.deviation,
                        'error_message': validation_result.error_message,
                        'suggested_value': self.emu_engine.align_to_baseline_grid(emu_value)
                    }
                }
            else:
                variable_def.validation_rules = {
                    'emu_validation': {
                        'is_valid': True,
                        'deviation': 0,
                        'baseline_aligned': True
                    }
                }
                
        except (ValueError, TypeError) as e:
            self.stats['emu_validation_failures'] += 1
            variable_def.validation_rules = {
                'emu_validation': {
                    'is_valid': False,
                    'error_message': f"Invalid EMU value format: {variable_def.value}",
                    'conversion_error': str(e)
                }
            }
    
    def _process_color_variable(self, variable_def: CarrierVariableDefinition):
        """Process color variable for format validation"""
        color_value = str(variable_def.value).strip()
        
        # Basic color format validation
        is_hex = re.match(r'^#[0-9A-Fa-f]{6}$', color_value)
        is_theme = color_value.startswith('theme:') or color_value in ['windowText', 'window']
        is_rgb = color_value.startswith('rgb(') and color_value.endswith(')')
        
        variable_def.validation_rules = {
            'color_validation': {
                'is_valid': bool(is_hex or is_theme or is_rgb),
                'format_detected': 'hex' if is_hex else ('theme' if is_theme else ('rgb' if is_rgb else 'unknown')),
                'normalized_value': color_value.upper() if is_hex else color_value
            }
        }
    
    def substitute_in_content(self, content: str) -> Tuple[str, List[SubstitutionError]]:
        """Substitute carrier variables in content with resolved values"""
        errors = []
        updated_content = content
        
        # Process all carrier variables
        variables, processing_errors = self.process_carrier_variables(content)
        errors.extend(processing_errors)
        
        # Perform substitutions
        for variable_def in variables:
            variable_pattern = f'{{{{{variable_def.path}}}}}'
            
            # Convert value to string for substitution
            if variable_def.variable_type == CarrierVariableType.EMU:
                # EMU values are substituted as integers
                substitution_value = str(int(variable_def.value))
            else:
                substitution_value = str(variable_def.value)
            
            # Perform substitution
            updated_content = updated_content.replace(variable_pattern, substitution_value)
        
        return updated_content, errors
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        stats = dict(self.stats)
        
        # Calculate derived statistics
        total_variables = stats['variables_processed']
        if total_variables > 0:
            stats['token_resolution_success_rate'] = stats['token_resolution_hits'] / total_variables
            stats['emu_validation_success_rate'] = (
                (stats['emu_values_validated'] - stats['emu_validation_failures']) / 
                max(stats['emu_values_validated'], 1)
            )
        else:
            stats['token_resolution_success_rate'] = 0.0
            stats['emu_validation_success_rate'] = 0.0
        
        if self.enable_caching:
            total_cache_attempts = stats['cache_hits'] + stats['cache_misses']
            if total_cache_attempts > 0:
                stats['cache_hit_rate'] = stats['cache_hits'] / total_cache_attempts
            else:
                stats['cache_hit_rate'] = 0.0
        
        return stats
    
    def reset_statistics(self):
        """Reset processing statistics"""
        self.stats = {
            'variables_processed': 0,
            'emu_values_validated': 0,
            'emu_validation_failures': 0,
            'token_resolution_hits': 0,
            'token_resolution_misses': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def clear_cache(self):
        """Clear processing cache"""
        if self.enable_caching:
            self.variable_cache = {}
        self.token_resolver.clear_cache()