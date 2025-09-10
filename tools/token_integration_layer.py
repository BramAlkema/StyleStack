"""
Token Integration Layer

This module provides seamless integration between the Design Token Formula 
Evaluation system and the JSON-to-OOXML Processing Engine, enabling dynamic 
token resolution within OOXML patch operations.

Part of the StyleStack JSON-to-OOXML Processing Engine.
"""


from typing import Dict, List, Any, Optional, Union, Callable
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import re

from tools.formula_parser import FormulaParser, FormulaError
from tools.variable_resolver import VariableResolver as ProductionVariableResolver
from tools.formula_variable_resolver import FormulaVariableResolver
from tools.emu_types import EMUValue

# Configure logging
logger = logging.getLogger(__name__)

# Production EMU Type System for integration
class ProductionEMUTypeSystem:
    """Production EMU type system with comprehensive format support."""
    
    def __init__(self):
        """Initialize with format conversion support."""
        self.formula_parser = FormulaParser()
        
    def parse_value(self, expression: str) -> EMUValue:
        """
        Parse an EMU expression into an EMUValue with format support.
        
        Supports:
        - Direct values: "12700" -> 12700 EMU
        - Unit expressions: "1pt" -> 12700 EMU, "1in" -> 914400 EMU
        - Formulas: "=A1 + 10pt" -> computed EMU value
        """
        try:
            # Try parsing as formula first
            if expression.strip().startswith('='):
                result = self.formula_parser.parse_formula(expression[1:])
                if hasattr(result, 'value'):
                    emu_val = EMUValue(result.value)
                else:
                    emu_val = EMUValue(result)
            else:
                # Parse as unit expression or direct EMU value
                parsed_value = self._parse_unit_expression(expression)
                emu_val = EMUValue(parsed_value)
            
            # Add format methods for different OOXML contexts
            self._add_format_methods(emu_val)
            return emu_val
            
        except (ValueError, EMUConversionError, FormulaError) as e:
            raise EMUConversionError(f"Failed to parse EMU expression '{expression}': {e}")
    
    def _parse_unit_expression(self, expression: str) -> int:
        """Parse unit expression like '12pt', '1in', '2cm' into EMU value."""
        expr = expression.strip()
        
        # Try to extract number and unit
        import re
        match = re.match(r'^([0-9]*\.?[0-9]+)\s*(pt|in|cm|emu)?$', expr, re.IGNORECASE)
        
        if not match:
            # Try parsing as direct number
            try:
                return int(float(expr))
            except ValueError:
                raise ValueError(f"Invalid unit expression: '{expr}'")
        
        value_str, unit = match.groups()
        value = float(value_str)
        
        if unit is None or unit.lower() == 'emu':
            return int(value)
        elif unit.lower() == 'pt':
            return int(value * EMU_PER_POINT)
        elif unit.lower() == 'in':
            return int(value * EMU_PER_INCH)
        elif unit.lower() == 'cm':
            return int(value * EMU_PER_CM)
        else:
            raise ValueError(f"Unsupported unit: '{unit}'")
    
    def _add_format_methods(self, emu_val: EMUValue):
        """Add context-specific format methods to EMUValue."""
        def to_presentation_format():
            """Format for PowerPoint presentation contexts (points)."""
            points = emu_val.value / EMU_PER_POINT
            return f"{points:.0f}pt"
            
        def to_document_format():
            """Format for Word document contexts (points).""" 
            points = emu_val.value / EMU_PER_POINT
            return f"{points:.0f}pt"
            
        def to_spreadsheet_format():
            """Format for Excel spreadsheet contexts (EMU)."""
            return str(int(emu_val.value))
            
        # Dynamically add methods
        emu_val.to_presentation_format = to_presentation_format
        emu_val.to_document_format = to_document_format  
        emu_val.to_spreadsheet_format = to_spreadsheet_format

# Create aliases for backward compatibility
EMUError = EMUConversionError
EMUTypeSystem = ProductionEMUTypeSystem


class TokenScope(Enum):
    """Token resolution scope levels."""
    GLOBAL = "global"           # System-wide tokens
    TEMPLATE = "template"       # Template-specific tokens  
    DOCUMENT = "document"       # Document-instance tokens
    OPERATION = "operation"     # Operation-specific tokens


@dataclass
class TokenContext:
    """Context for token resolution operations."""
    scope: TokenScope
    template_type: str  # 'potx', 'dotx', 'xltx'
    variables: Dict[str, Any]
    metadata: Dict[str, Any]
    operation_data: Optional[Dict[str, Any]] = None


@dataclass
class TokenResolutionResult:
    """Result of token resolution operation."""
    success: bool
    resolved_value: Any
    original_token: str
    formula_used: Optional[str] = None
    emu_value: Optional[EMUValue] = None
    errors: List[str] = None
    context: Optional[TokenContext] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class TokenIntegrationLayer:
    """
    Integration layer between token systems and OOXML processing.
    
    Provides:
    - Dynamic token resolution in JSON patches
    - Formula evaluation with EMU type safety
    - Context-aware variable substitution
    - Multi-scope token resolution
    - Integration with OOXML processor
    """
    
    def __init__(self, 
                 formula_parser: Optional[FormulaParser] = None,
                 emu_system: Optional[ProductionEMUTypeSystem] = None,
                 variable_resolver: Optional[ProductionVariableResolver] = None):
        """Initialize the token integration layer with production systems."""
        self.formula_parser = formula_parser or FormulaParser()
        self.emu_system = emu_system or ProductionEMUTypeSystem()
        self.variable_resolver = variable_resolver or ProductionVariableResolver()
        self.formula_variable_resolver = FormulaVariableResolver()
        
        # Token pattern matching
        self.token_pattern = re.compile(r'\$\{([^}]+)\}')
        self.formula_pattern = re.compile(r'@\{([^}]+)\}')
        self.emu_pattern = re.compile(r'#\{([^}]+)\}')
        
        # Token registry by scope
        self.token_registry = {
            TokenScope.GLOBAL: {},
            TokenScope.TEMPLATE: {},
            TokenScope.DOCUMENT: {},
            TokenScope.OPERATION: {}
        }
        
        # Resolution cache for performance
        self.resolution_cache = {}
        self.cache_size_limit = 1000
        
        # Production variable resolution cache
        self._resolved_variables_cache: Dict[str, Any] = {}
        self._cache_context: Optional[str] = None
        
        # Integration hooks
        self.pre_resolution_hooks = []
        self.post_resolution_hooks = []
        
        # Statistics tracking
        self.resolution_stats = {
            'total_resolutions': 0,
            'cache_hits': 0,
            'formula_resolutions': 0,
            'variable_resolutions': 0,
            'emu_resolutions': 0,
            'errors': 0
        }
    
    def initialize_production_variables(self, 
                                      org: Optional[str] = None,
                                      channel: Optional[str] = None,
                                      extension_sources: Optional[List[Union[str, Path]]] = None) -> None:
        """
        Initialize production variable resolution with specific context.
        
        This method pre-resolves all variables using the production VariableResolver
        and caches them for efficient token resolution.
        
        Args:
            org: Organization identifier for variable resolution
            channel: Channel identifier for template-specific variables  
            extension_sources: OOXML files with extension variables
        """
        context_key = f"org:{org}|channel:{channel}|ext:{len(extension_sources or [])}"
        
        if self._cache_context == context_key:
            logger.debug("Using cached production variable resolution")
            return
            
        logger.info(f"Initializing production variable resolution: {context_key}")
        
        try:
            resolved_vars = self.variable_resolver.resolve_all_variables(
                org=org,
                channel=channel, 
                extension_sources=extension_sources
            )
            
            # Convert ResolvedVariable objects to simple values for token resolution
            self._resolved_variables_cache = {}
            for name, resolved_var in resolved_vars.items():
                self._resolved_variables_cache[name] = resolved_var.final_value
                
            self._cache_context = context_key
            logger.info(f"Cached {len(resolved_vars)} production variables")
            
        except Exception as e:
            logger.error(f"Failed to initialize production variables: {e}")
            # Fallback to empty cache
            self._resolved_variables_cache = {}
            self._cache_context = None
        
    def register_token(self, name: str, value: Any, scope: TokenScope, 
                      template_type: Optional[str] = None):
        """
        Register a token with specified scope and template type.
        
        Args:
            name: Token name
            value: Token value (can be formula, EMU expression, or literal)
            scope: Token resolution scope
            template_type: Template type filter ('potx', 'dotx', 'xltx')
        """
        scope_registry = self.token_registry[scope]
        
        if template_type:
            if template_type not in scope_registry:
                scope_registry[template_type] = {}
            scope_registry[template_type][name] = value
        else:
            scope_registry[name] = value
            
        logger.debug(f"Registered token '{name}' in {scope.value} scope for {template_type or 'all'} templates")
    
    def integrate_with_processor(self, processor: JSONPatchProcessor):
        """
        Integrate token resolution with JSON-to-OOXML processor.
        
        Args:
            processor: The processor to integrate with
        """
        # Add token resolution as a pre-processing step
        original_apply_patch = processor.apply_patch
        
        def token_aware_apply_patch(xml_doc, patch_data, context=None):
            # Create token context
            token_context = TokenContext(
                scope=TokenScope.OPERATION,
                template_type=getattr(processor, 'template_type', 'potx'),
                variables=getattr(processor, 'variables', {}),
                metadata=getattr(processor, 'metadata', {}),
                operation_data=patch_data
            )
            
            # Resolve tokens in patch data
            resolved_patch = self.resolve_patch_tokens(patch_data, token_context)
            
            # Apply the patch with resolved tokens
            return original_apply_patch(xml_doc, resolved_patch, context)
        
        processor.apply_patch = token_aware_apply_patch
        logger.info("Integrated token resolution with JSON-to-OOXML processor")
    
    def resolve_patch_tokens(self, patch_data: Dict[str, Any], 
                           context: TokenContext) -> Dict[str, Any]:
        """
        Resolve all tokens in a patch operation.
        
        Args:
            patch_data: Patch operation data
            context: Token resolution context
            
        Returns:
            Patch data with resolved tokens
        """
        resolved_patch = {}
        
        for key, value in patch_data.items():
            resolved_patch[key] = self._resolve_value_tokens(value, context)
            
        return resolved_patch
    
    def _resolve_value_tokens(self, value: Any, context: TokenContext) -> Any:
        """Recursively resolve tokens in any value type."""
        if isinstance(value, str):
            return self._resolve_string_tokens(value, context)
        elif isinstance(value, dict):
            return {k: self._resolve_value_tokens(v, context) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._resolve_value_tokens(item, context) for item in value]
        else:
            return value
    
    def _resolve_string_tokens(self, text: str, context: TokenContext) -> str:
        """Resolve tokens in a string value."""
        result = text
        
        # Resolve variable tokens: ${token_name}
        result = self.token_pattern.sub(
            lambda m: self._resolve_variable_token(m.group(1), context), result
        )
        
        # Resolve formula tokens: @{formula}
        result = self.formula_pattern.sub(
            lambda m: self._resolve_formula_token(m.group(1), context), result
        )
        
        # Resolve EMU tokens: #{emu_expression}
        result = self.emu_pattern.sub(
            lambda m: self._resolve_emu_token(m.group(1), context), result
        )
        
        return result
    
    def _resolve_variable_token(self, token_name: str, context: TokenContext) -> str:
        """Resolve a variable token."""
        cache_key = f"var_{token_name}_{context.scope.value}_{context.template_type}"
        
        if cache_key in self.resolution_cache:
            return str(self.resolution_cache[cache_key])
        
        # Try to resolve from token registry in scope priority order
        scopes_to_try = [
            context.scope,
            TokenScope.DOCUMENT,
            TokenScope.TEMPLATE,
            TokenScope.GLOBAL
        ]
        
        resolved_value = None
        for scope in scopes_to_try:
            resolved_value = self._get_token_from_scope(token_name, scope, context.template_type)
            if resolved_value is not None:
                break
        
        # Fallback to production variable resolver
        if resolved_value is None:
            try:
                # First try production resolved variables cache  
                if token_name in self._resolved_variables_cache:
                    resolved_value = self._resolved_variables_cache[token_name]
                    logger.debug(f"Resolved variable '{token_name}' from production cache")
                else:
                    # Legacy fallback for backward compatibility
                    resolved_value = context.variables.get(token_name, f"${{{token_name}}}")
                    logger.debug(f"Variable '{token_name}' not found in production cache, using fallback")
                    
            except Exception as e:
                logger.warning(f"Failed to resolve variable token '{token_name}': {e}")
                resolved_value = f"${{{token_name}}}"  # Return original if not found
        
        # Cache the result
        if len(self.resolution_cache) < self.cache_size_limit:
            self.resolution_cache[cache_key] = resolved_value
            
        return str(resolved_value)
    
    def _resolve_formula_token(self, formula: str, context: TokenContext) -> str:
        """Resolve a formula token."""
        cache_key = f"formula_{hash(formula)}_{context.template_type}"
        
        if cache_key in self.resolution_cache:
            return str(self.resolution_cache[cache_key])
        
        try:
            # Parse and evaluate formula
            parsed_formula = self.formula_parser.parse(formula)
            
            # Create evaluation context
            eval_context = {
                **context.variables,
                **context.metadata,
                'template_type': context.template_type,
                'scope': context.scope.value
            }
            
            result = self.formula_parser.evaluate(parsed_formula, eval_context)
            
            # Cache the result
            if len(self.resolution_cache) < self.cache_size_limit:
                self.resolution_cache[cache_key] = result
                
            return str(result)
            
        except FormulaError as e:
            logger.error(f"Formula evaluation failed for '{formula}': {e}")
            return f"@{{{formula}}}"  # Return original on error
    
    def _resolve_emu_token(self, emu_expression: str, context: TokenContext) -> str:
        """Resolve an EMU token."""
        cache_key = f"emu_{hash(emu_expression)}_{context.template_type}"
        
        if cache_key in self.resolution_cache:
            return str(self.resolution_cache[cache_key])
        
        try:
            # Parse EMU expression
            emu_value = self.emu_system.parse_value(emu_expression)
            
            # Convert to appropriate format for template type
            if context.template_type == 'potx':
                result = emu_value.to_presentation_format()
            elif context.template_type == 'dotx':
                result = emu_value.to_document_format()
            elif context.template_type == 'xltx':
                result = emu_value.to_spreadsheet_format()
            else:
                result = str(emu_value)
            
            # Cache the result
            if len(self.resolution_cache) < self.cache_size_limit:
                self.resolution_cache[cache_key] = result
                
            return str(result)
            
        except EMUError as e:
            logger.error(f"EMU evaluation failed for '{emu_expression}': {e}")
            return f"#{{{emu_expression}}}"  # Return original on error
    
    def _get_token_from_scope(self, token_name: str, scope: TokenScope, 
                            template_type: str) -> Optional[Any]:
        """Get token value from specific scope and template type."""
        scope_registry = self.token_registry[scope]
        
        # Try template-specific first
        if template_type in scope_registry:
            template_registry = scope_registry[template_type]
            if token_name in template_registry:
                return template_registry[token_name]
        
        # Try scope-wide
        if token_name in scope_registry:
            return scope_registry[token_name]
        
        return None
    
    def resolve_token_explicit(self, token: str, context: TokenContext) -> TokenResolutionResult:
        """
        Explicitly resolve a single token with full result information.
        
        Args:
            token: Token to resolve
            context: Resolution context
            
        Returns:
            Detailed resolution result
        """
        result = TokenResolutionResult(
            success=False,
            resolved_value=None,
            original_token=token,
            context=context
        )
        
        try:
            # Run pre-resolution hooks
            for hook in self.pre_resolution_hooks:
                hook(token, context)
            
            # Determine token type and resolve
            if self.token_pattern.match(f"${{{token}}}"):
                result.resolved_value = self._resolve_variable_token(token, context)
                result.success = True
            elif self.formula_pattern.match(f"@{{{token}}}"):
                result.resolved_value = self._resolve_formula_token(token, context)
                result.formula_used = token
                result.success = True
            elif self.emu_pattern.match(f"#{{{token}}}"):
                result.resolved_value = self._resolve_emu_token(token, context)
                result.emu_value = self.emu_system.parse_value(token)
                result.success = True
            else:
                result.errors.append(f"Unrecognized token format: {token}")
            
            # Run post-resolution hooks
            for hook in self.post_resolution_hooks:
                hook(result)
                
        except Exception as e:
            result.errors.append(f"Resolution failed: {e}")
            logger.error(f"Token resolution failed for '{token}': {e}")
        
        return result
    
    def add_resolution_hook(self, hook: Callable, post_resolution: bool = False):
        """Add a resolution hook for custom processing."""
        if post_resolution:
            self.post_resolution_hooks.append(hook)
        else:
            self.pre_resolution_hooks.append(hook)
    
    def clear_cache(self):
        """Clear the resolution cache."""
        self.resolution_cache.clear()
        logger.debug("Token resolution cache cleared")
    
    def get_resolution_statistics(self) -> Dict[str, Any]:
        """Get statistics about token resolution performance."""
        return {
            'cache_size': len(self.resolution_cache),
            'cache_limit': self.cache_size_limit,
            'registered_tokens_by_scope': {
                scope.value: len(registry) for scope, registry in self.token_registry.items()
            },
            'hooks_registered': {
                'pre_resolution': len(self.pre_resolution_hooks),
                'post_resolution': len(self.post_resolution_hooks)
            }
        }


# Convenience functions for common operations

def create_default_integration_layer() -> TokenIntegrationLayer:
    """Create a token integration layer with default configuration."""
    return TokenIntegrationLayer()

def integrate_tokens_with_processor(processor: JSONPatchProcessor) -> TokenIntegrationLayer:
    """
    Integrate token resolution with an existing JSON-to-OOXML processor.
    
    Args:
        processor: The processor to integrate with
        
    Returns:
        The integration layer instance for further configuration
    """
    integration_layer = create_default_integration_layer()
    integration_layer.integrate_with_processor(processor)
    return integration_layer