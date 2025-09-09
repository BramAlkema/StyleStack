"""
YAML-to-OOXML Patch Operations Engine - Compatibility Module

This module maintains backward compatibility after splitting the monolithic
yaml_ooxml_processor.py into focused helper modules.

New code should import from the specific modules:
- tools.core.types for data types and enums
- tools.xpath.targeting for XPath operations  
- tools.processing.yaml for YAML patch processing
- tools.processing.errors for error handling
"""

from typing import Dict, List, Any, Optional, Union, Callable, Set, Tuple
import logging
from lxml import etree

# Import from split modules
from tools.core.types import (
    PatchOperationType, InsertPosition, RecoveryStrategy, ErrorSeverity,
    PatchError, PatchResult, PatchOperation, XPathContext, ProcessingContext
)
from tools.xpath.targeting import XPathTargetingSystem
from tools.processing.yaml import YAMLPatchProcessor, PerformanceOptimizer
from tools.processing.errors import ErrorRecoveryHandler, PerformanceTimer

# Configure logging
logger = logging.getLogger(__name__)


# Backward compatibility aliases
XPathTargetingSystemBackwardCompatibility = XPathTargetingSystem


# Convenience functions for common operations

def apply_yaml_patches_to_ooxml(xml_content: str, patches: List[Dict[str, Any]]) -> tuple[str, List[PatchResult]]:
    """
    Convenience function to apply YAML patches to OOXML content.
    
    Args:
        xml_content: Raw XML content as string
        patches: List of patch operation dictionaries
        
    Returns:
        Tuple of (modified_xml_string, patch_results)
    """
    try:
        # Parse XML
        xml_doc = etree.fromstring(xml_content.encode('utf-8'))
        
        # Convert dict patches to PatchOperation objects
        patch_operations = []
        for patch_data in patches:
            try:
                patch_op = PatchOperation.from_dict(patch_data)
                patch_operations.append(patch_op)
            except ValueError as e:
                error_result = PatchResult(
                    success=False,
                    operation=patch_data.get('operation', 'unknown'),
                    target=patch_data.get('target', 'unknown'),
                    message=f"Invalid patch data: {e}",
                    severity=ErrorSeverity.ERROR
                )
                return xml_content, [error_result]
        
        # Apply patches
        processor = YAMLPatchProcessor()
        results = processor.process_patches(xml_doc, patch_operations)
        
        # Return modified XML
        modified_xml = etree.tostring(xml_doc, encoding='unicode', pretty_print=True)
        return modified_xml, results
        
    except etree.XMLSyntaxError as e:
        error_result = PatchResult(
            success=False,
            operation='parse',
            target='xml_content',
            message=f"XML parsing error: {e}",
            severity=ErrorSeverity.ERROR
        )
        return xml_content, [error_result]


def create_patch_operation(operation: str, target: str, value: Any, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to create a patch operation dictionary.
    
    Args:
        operation: The patch operation type (set, insert, extend, merge, relsAdd)
        target: XPath target expression
        value: The value to apply
        **kwargs: Additional options (position, merge_strategy, etc.)
        
    Returns:
        Dictionary representing the patch operation
    """
    patch_data = {
        'operation': operation,
        'target': target,
        'value': value
    }
    
    # Add optional parameters
    for key, value in kwargs.items():
        if value is not None:
            patch_data[key] = value
    
    return patch_data


# Backward compatibility for classes that may be imported directly
__all__ = [
    # Core types
    'PatchOperationType',
    'InsertPosition',
    'RecoveryStrategy', 
    'ErrorSeverity',
    'PatchError',
    'PatchResult',
    'PatchOperation',
    'XPathContext',
    'ProcessingContext',
    
    # Main classes
    'XPathTargetingSystem',
    'YAMLPatchProcessor',
    'PerformanceOptimizer',
    'ErrorRecoveryHandler',
    'PerformanceTimer',
    
    # Convenience functions
    'apply_yaml_patches_to_ooxml',
    'create_patch_operation',
    
    # Backward compatibility
    'XPathTargetingSystemBackwardCompatibility'
]