"""OOXML probe file generation module.

This module generates test probe files with specific features to validate
round-trip compatibility across different Office platforms:
- Template-based probe generation
- Feature-specific test documents
- Carrier variable insertion
- Multi-format output (docx, pptx, xlsx)
"""

from .generator import ProbeGenerator

# Stub classes - to be implemented
class TemplateManager:
    pass

class FeatureSet:
    pass

class ThemeFeatures:
    pass

class StyleFeatures:
    pass

class TableFeatures:
    pass

class ShapeFeatures:
    pass

__all__ = [
    "ProbeGenerator",
    "TemplateManager", 
    "FeatureSet",
    "ThemeFeatures",
    "StyleFeatures",
    "TableFeatures", 
    "ShapeFeatures",
]