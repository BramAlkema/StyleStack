"""
Helper functions for creating appropriate patches for different OOXML formats.

This module provides targeted patches that work with the actual structure
of OOXML documents, avoiding the issue of applying inappropriate patches
to the wrong file types.
"""

from typing import List, Dict, Any


def get_powerpoint_patches() -> List[Dict[str, Any]]:
    """Get patches appropriate for PowerPoint templates."""
    return [
        # For slides - text content  
        {
            "operation": "set",
            "target": "//a:t",  # More general text selector that works in slides
            "value": "Updated PowerPoint Text {{batch_id}}"
        },
        # For theme - color values
        {
            "operation": "set", 
            "target": "//a:srgbClr/@val",  # General color selector for themes
            "value": "FF6B35"
        }
    ]


def get_word_patches() -> List[Dict[str, Any]]:
    """Get patches appropriate for Word templates."""
    return [
        # For document - text content
        {
            "operation": "set",
            "target": "//w:t",  # General text selector for Word docs
            "value": "Updated Word Text {{batch_id}}"
        },
        # For styles - color values
        {
            "operation": "set",
            "target": "//w:color/@w:val",  # Color attribute in Word
            "value": "008000"
        }
    ]


def get_excel_patches() -> List[Dict[str, Any]]:
    """Get patches appropriate for Excel templates."""
    return [
        # For worksheets - cell values
        {
            "operation": "set",
            "target": "//c[@r='A1']/v",  # Specific cell value
            "value": "Updated Excel {{batch_id}}"
        },
        # For styles - font colors
        {
            "operation": "set",
            "target": "//font/color/@rgb",  # Font color in styles
            "value": "FF008000"
        }
    ]


def get_format_specific_patches(format_type: str) -> List[Dict[str, Any]]:
    """
    Get patches specific to a given format type.
    
    Args:
        format_type: One of 'potx', 'dotx', 'xltx'
        
    Returns:
        List of patch dictionaries appropriate for the format
    """
    patch_map = {
        'potx': get_powerpoint_patches(),
        'dotx': get_word_patches(),
        'xltx': get_excel_patches()
    }
    
    return patch_map.get(format_type, [])


def create_safe_patch_config(format_type: str, variables: Dict[str, str]) -> Dict[str, Any]:
    """
    Create a safe patch configuration for a specific format.
    
    This ensures patches are only applied to appropriate file types
    and targets that actually exist in the document structure.
    
    Args:
        format_type: The OOXML format type
        variables: Variables to use in patches
        
    Returns:
        Complete patch configuration dict
    """
    return {
        "format": format_type,
        "patches": get_format_specific_patches(format_type),
        "variables": variables,
        "validate_targets": True  # Enable target validation
    }