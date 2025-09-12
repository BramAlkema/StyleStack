#!/usr/bin/env python3
"""
Carrier System Integration with Variable Resolver

This module provides integration between the new Carrier Registry System
and the existing StyleStack Variable Resolver, enabling hierarchical
design token precedence through the carrier system.

Author: StyleStack Team  
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path

# Import StyleStack components
try:
    from variable_resolver import VariableResolver, ResolvedVariable, TokenType, TokenScope
    from carrier_registry import CarrierRegistry, CarrierDefinition, Platform
    from carrier_types import CarrierTypeRegistry
    from token_injection_engine import DesignTokenInjectionEngine, InjectionContext
except ImportError as e:
    logging.warning(f"Could not import StyleStack components: {e}")
    # Mock classes for testing
    VariableResolver = None
    ResolvedVariable = None
    CarrierRegistry = None
    CarrierDefinition = None
    Platform = None
    CarrierTypeRegistry = None
    DesignTokenInjectionEngine = None

logger = logging.getLogger(__name__)


@dataclass
class CarrierResolutionContext:
    """Context for carrier-based token resolution."""
    platform: str = "microsoft_office"
    document_type: str = "potx"
    org_name: str = ""
    channel_name: str = ""
    template_name: str = ""
    emu_precision: bool = True
    accessibility_mode: bool = True


class CarrierVariableIntegrator:
    """
    Integration layer between Carrier System and Variable Resolver.
    
    Provides hierarchical token resolution through carriers:
    Design System 2025 → Corporate → Channel → Template → Carrier-specific
    """
    
    def __init__(
        self,
        carrier_registry: 'CarrierRegistry',
        variable_resolver: 'VariableResolver',
        carrier_type_registry: 'CarrierTypeRegistry' = None
    ):
        """
        Initialize the integrator.
        
        Args:
            carrier_registry: Carrier registry instance
            variable_resolver: StyleStack variable resolver
            carrier_type_registry: Carrier type definitions
        """
        self.carrier_registry = carrier_registry
        self.variable_resolver = variable_resolver
        self.carrier_type_registry = carrier_type_registry
        
        # Create injection engine
        self.injection_engine = DesignTokenInjectionEngine(
            carrier_registry=carrier_registry,
            carrier_type_registry=carrier_type_registry,
            variable_resolver=variable_resolver
        ) if DesignTokenInjectionEngine else None
        
        logger.info("CarrierVariableIntegrator initialized")

    def resolve_tokens_for_carrier(
        self,
        carrier_id: str,
        context: CarrierResolutionContext,
        additional_tokens: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resolve design tokens specifically for a carrier using hierarchical precedence.
        
        Args:
            carrier_id: ID of the carrier to resolve tokens for
            context: Resolution context with org, channel, template info
            additional_tokens: Additional tokens to include in resolution
            
        Returns:
            Dictionary of resolved design tokens for the carrier
        """
        # Get carrier definition
        carrier = self.carrier_registry.get_carrier(carrier_id)
        if not carrier:
            logger.error(f"Carrier {carrier_id} not found")
            return {}
        
        # Build hierarchical token context for variable resolver
        token_context = self._build_token_context(context, additional_tokens or {})
        
        # Use variable resolver to resolve with precedence
        resolved_variables = self.variable_resolver.resolve_all(token_context)
        
        # Filter resolved variables to only those needed by this carrier
        carrier_tokens = self._filter_tokens_for_carrier(resolved_variables, carrier)
        
        # Convert back to simple dict format for injection engine
        return self._convert_resolved_variables_to_tokens(carrier_tokens)

    def resolve_all_carrier_tokens(
        self,
        context: CarrierResolutionContext,
        platform_filter: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Resolve tokens for all carriers applicable to a platform.
        
        Args:
            context: Resolution context
            platform_filter: Optional platform filter
            
        Returns:
            Dictionary mapping carrier_id to resolved tokens
        """
        results = {}
        
        # Get carriers for platform
        if platform_filter:
            if hasattr(Platform, platform_filter.upper()):
                platform_enum = getattr(Platform, platform_filter.upper())
                carriers = self.carrier_registry.find_carriers_by_platform(platform_enum)
            else:
                carriers = self.carrier_registry.find_carriers_by_platform(platform_filter)
        else:
            carriers = self.carrier_registry.get_all_carriers()
        
        # Resolve tokens for each carrier
        for carrier in carriers:
            try:
                resolved_tokens = self.resolve_tokens_for_carrier(
                    carrier.carrier_id,
                    context
                )
                results[carrier.carrier_id] = resolved_tokens
                
            except Exception as e:
                logger.error(f"Failed to resolve tokens for carrier {carrier.carrier_id}: {e}")
                results[carrier.carrier_id] = {}
        
        return results

    def apply_tokens_with_precedence(
        self,
        xml_element: Any,
        design_system_tokens: Dict[str, Any],
        corporate_tokens: Dict[str, Any],
        channel_tokens: Dict[str, Any],
        template_tokens: Dict[str, Any],
        context: CarrierResolutionContext
    ) -> List[Dict[str, Any]]:
        """
        Apply tokens to XML element using hierarchical precedence through carriers.
        
        Args:
            xml_element: XML element to modify
            design_system_tokens: Global foundation tokens
            corporate_tokens: Organization-specific tokens  
            channel_tokens: Channel-specific tokens
            template_tokens: Template-specific tokens
            context: Resolution context
            
        Returns:
            List of application results
        """
        if not self.injection_engine:
            logger.error("Injection engine not available")
            return []
        
        # Create injection context
        injection_context = InjectionContext(
            platform=getattr(Platform, context.platform.upper()) if Platform else context.platform,
            document_type=context.document_type,
            emu_precision=context.emu_precision,
            accessibility_mode=context.accessibility_mode
        )
        
        # Find applicable carriers for this element type
        applicable_carriers = self._find_applicable_carriers_for_element(xml_element, context)
        
        results = []
        
        for carrier in applicable_carriers:
            try:
                result = self.injection_engine.inject_with_hierarchical_precedence(
                    xml_element=xml_element,
                    design_system_tokens=design_system_tokens,
                    corporate_tokens=corporate_tokens,
                    channel_tokens=channel_tokens,
                    template_tokens=template_tokens,
                    carrier_id=carrier.carrier_id,
                    context=injection_context
                )
                
                # Convert InjectionResult to dict for compatibility
                results.append({
                    "carrier_id": result.carrier_id,
                    "success": result.success,
                    "tokens_applied": result.tokens_applied,
                    "processing_time_ms": result.processing_time_ms,
                    "errors": result.errors,
                    "warnings": result.warnings
                })
                
            except Exception as e:
                logger.error(f"Failed to apply tokens with carrier {carrier.carrier_id}: {e}")
                results.append({
                    "carrier_id": carrier.carrier_id,
                    "success": False,
                    "tokens_applied": 0,
                    "processing_time_ms": 0.0,
                    "errors": [str(e)],
                    "warnings": []
                })
        
        return results

    def get_token_precedence_chain(
        self,
        token_path: str,
        context: CarrierResolutionContext
    ) -> List[Dict[str, Any]]:
        """
        Get the precedence chain for a specific token path showing how it resolves.
        
        Args:
            token_path: Dot-separated token path (e.g., "typography.body.font_size")
            context: Resolution context
            
        Returns:
            List of precedence entries showing resolution chain
        """
        # Build context for resolution
        token_context = self._build_token_context(context, {})
        
        # Resolve all variables
        resolved_variables = self.variable_resolver.resolve_all(token_context)
        
        # Find variables that match the token path
        matching_variables = []
        for var_id, variable in resolved_variables.items():
            if token_path in var_id or var_id in token_path:
                matching_variables.append({
                    "variable_id": var_id,
                    "value": variable.value,
                    "source": variable.source,
                    "scope": variable.scope.name if hasattr(variable.scope, 'name') else str(variable.scope),
                    "hierarchy_level": variable.hierarchy_level,
                    "precedence_key": variable.precedence_key
                })
        
        # Sort by precedence (higher precedence first)
        matching_variables.sort(key=lambda x: x["precedence_key"], reverse=True)
        
        return matching_variables

    def validate_carrier_token_compatibility(
        self,
        carrier_id: str,
        design_tokens: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate that design tokens are compatible with a carrier's requirements.
        
        Args:
            carrier_id: ID of the carrier to validate against
            design_tokens: Design tokens to validate
            
        Returns:
            Validation result with errors and warnings
        """
        carrier = self.carrier_registry.get_carrier(carrier_id)
        if not carrier:
            return {
                "valid": False,
                "errors": [f"Carrier {carrier_id} not found"],
                "warnings": []
            }
        
        # Use carrier type registry for validation if available
        if self.carrier_type_registry:
            # Find carrier type definition
            carrier_type_def = None
            for type_name, type_def in self.carrier_type_registry.get_all_carrier_types().items():
                if carrier.carrier_type.value == type_name or type_name in carrier.carrier_id:
                    carrier_type_def = type_def
                    break
            
            if carrier_type_def:
                return self.carrier_type_registry.validate_design_tokens_for_carrier(
                    carrier_type_def.name,
                    design_tokens
                )
        
        # Basic validation if no type registry
        return self._basic_carrier_validation(carrier, design_tokens)

    def _build_token_context(
        self,
        context: CarrierResolutionContext,
        additional_tokens: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build token context for variable resolver."""
        token_context = {}
        
        # Add context information
        if context.org_name:
            token_context["org"] = context.org_name
        if context.channel_name:
            token_context["channel"] = context.channel_name
        if context.template_name:
            token_context["template"] = context.template_name
        
        # Add additional tokens
        token_context.update(additional_tokens)
        
        return token_context

    def _filter_tokens_for_carrier(
        self,
        resolved_variables: Dict[str, 'ResolvedVariable'],
        carrier: 'CarrierDefinition'
    ) -> Dict[str, 'ResolvedVariable']:
        """Filter resolved variables to only those needed by a carrier."""
        carrier_tokens = {}
        
        # Get token keys that this carrier needs
        required_token_keys = set(carrier.design_token_mapping.keys())
        
        for var_id, variable in resolved_variables.items():
            # Check if this variable matches any required token
            for token_key in required_token_keys:
                if self._token_matches(var_id, token_key):
                    carrier_tokens[var_id] = variable
                    break
        
        return carrier_tokens

    def _token_matches(self, variable_id: str, token_key: str) -> bool:
        """Check if a variable ID matches a token key pattern."""
        # Simple matching - could be enhanced with regex patterns
        return (
            token_key in variable_id or
            variable_id in token_key or
            variable_id.replace('_', '.') == token_key or
            token_key.replace('.', '_') == variable_id
        )

    def _convert_resolved_variables_to_tokens(
        self,
        resolved_variables: Dict[str, 'ResolvedVariable']
    ) -> Dict[str, Any]:
        """Convert resolved variables back to simple token dictionary."""
        tokens = {}
        
        for var_id, variable in resolved_variables.items():
            # Convert dot notation to nested structure
            keys = var_id.split('.')
            current = tokens
            
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            current[keys[-1]] = variable.value
        
        return tokens

    def _find_applicable_carriers_for_element(
        self,
        xml_element: Any,
        context: CarrierResolutionContext
    ) -> List['CarrierDefinition']:
        """Find carriers applicable to an XML element."""
        # This would analyze the XML element and return matching carriers
        # For now, return all carriers for the platform
        if hasattr(Platform, context.platform.upper()):
            platform_enum = getattr(Platform, context.platform.upper())
            return self.carrier_registry.find_carriers_by_platform(platform_enum)
        else:
            return self.carrier_registry.get_all_carriers()

    def _basic_carrier_validation(
        self,
        carrier: 'CarrierDefinition',
        design_tokens: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Basic validation when no carrier type registry is available."""
        errors = []
        warnings = []
        
        # Check if required token mappings have corresponding values
        for token_key in carrier.design_token_mapping.keys():
            if not self._token_exists_in_nested_dict(design_tokens, token_key):
                errors.append(f"Required token '{token_key}' not found in design tokens")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def _token_exists_in_nested_dict(self, tokens: Dict[str, Any], token_path: str) -> bool:
        """Check if a token path exists in nested dictionary."""
        keys = token_path.split('.')
        current = tokens
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return False
        
        return True


class CarrierTokenResolver:
    """
    Simplified token resolver specifically for carrier-based resolution.
    
    Provides a simpler interface for common carrier token resolution tasks.
    """
    
    def __init__(self, integrator: CarrierVariableIntegrator):
        """Initialize with integrator instance."""
        self.integrator = integrator

    def resolve_for_template(
        self,
        template_path: str,
        org_name: str = "",
        channel_name: str = "",
        platform: str = "microsoft_office"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Resolve tokens for all carriers applicable to a template.
        
        Args:
            template_path: Path to template file
            org_name: Organization name for token resolution
            channel_name: Channel name for token resolution  
            platform: Target platform
            
        Returns:
            Dictionary mapping carrier_id to resolved tokens
        """
        # Determine document type from file extension
        template_path_obj = Path(template_path)
        document_type = template_path_obj.suffix.lstrip('.')
        
        context = CarrierResolutionContext(
            platform=platform,
            document_type=document_type,
            org_name=org_name,
            channel_name=channel_name,
            template_name=template_path_obj.stem
        )
        
        return self.integrator.resolve_all_carrier_tokens(context, platform)

    def apply_to_document(
        self,
        xml_document: Any,
        design_system_tokens: Dict[str, Any],
        corporate_tokens: Dict[str, Any] = None,
        channel_tokens: Dict[str, Any] = None,
        template_tokens: Dict[str, Any] = None,
        platform: str = "microsoft_office",
        document_type: str = "potx"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Apply tokens to an entire document using carriers.
        
        Args:
            xml_document: XML document root element
            design_system_tokens: Global foundation tokens
            corporate_tokens: Organization tokens
            channel_tokens: Channel-specific tokens
            template_tokens: Template-specific tokens
            platform: Target platform
            document_type: Document type
            
        Returns:
            Dictionary mapping element types to application results
        """
        context = CarrierResolutionContext(
            platform=platform,
            document_type=document_type
        )
        
        # This would iterate through document elements and apply tokens
        # For now, return a simple structure
        results = {
            "document_root": self.integrator.apply_tokens_with_precedence(
                xml_document,
                design_system_tokens,
                corporate_tokens or {},
                channel_tokens or {},
                template_tokens or {},
                context
            )
        }
        
        return results


# Example usage and factory functions
def create_carrier_integrator(
    enable_caching: bool = True,
    verbose: bool = False
) -> Optional[CarrierVariableIntegrator]:
    """
    Factory function to create a fully configured CarrierVariableIntegrator.
    
    Args:
        enable_caching: Enable caching for performance
        verbose: Enable verbose logging
        
    Returns:
        Configured integrator or None if components unavailable
    """
    try:
        # Create components
        carrier_registry = CarrierRegistry(cache_enabled=enable_caching)
        variable_resolver = VariableResolver(verbose=verbose, enable_cache=enable_caching)
        carrier_type_registry = CarrierTypeRegistry()
        
        # Create integrator
        integrator = CarrierVariableIntegrator(
            carrier_registry=carrier_registry,
            variable_resolver=variable_resolver,
            carrier_type_registry=carrier_type_registry
        )
        
        return integrator
        
    except Exception as e:
        logger.error(f"Failed to create carrier integrator: {e}")
        return None


def create_token_resolver_for_template(template_path: str) -> Optional[CarrierTokenResolver]:
    """
    Factory function to create a token resolver for a specific template.
    
    Args:
        template_path: Path to the template file
        
    Returns:
        Configured token resolver or None if failed
    """
    integrator = create_carrier_integrator()
    if integrator:
        return CarrierTokenResolver(integrator)
    return None


if __name__ == "__main__":
    # Example usage
    integrator = create_carrier_integrator(verbose=True)
    
    if integrator:
        print("CarrierVariableIntegrator created successfully")
        
        # Example context
        context = CarrierResolutionContext(
            platform="microsoft_office",
            document_type="potx",
            org_name="acme",
            channel_name="present"
        )
        
        print(f"Context: {context}")
    else:
        print("Failed to create integrator - missing dependencies")