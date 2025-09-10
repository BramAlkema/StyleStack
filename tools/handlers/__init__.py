from tools.handlers.types import OOXMLFormat
"""StyleStack Multi-Format OOXML Handlers Module"""

from .types import (
    OOXMLFormat, OOXMLStructure, ProcessingResult, 
    FormatConfiguration, ValidationIssue, ProcessingStatistics
)
from .formats import (
    FormatRegistry, FormatProcessor, PowerPointProcessor, 
    WordProcessor, ExcelProcessor, create_format_processor
)
from .integration import TokenIntegrationManager, CompatibilityMatrix

__all__ = [
    # Types
    'OOXMLFormat',
    'OOXMLStructure', 
    'ProcessingResult',
    'FormatConfiguration',
    'ValidationIssue',
    'ProcessingStatistics',
    
    # Format handling
    'FormatRegistry',
    'FormatProcessor',
    'PowerPointProcessor',
    'WordProcessor', 
    'ExcelProcessor',
    'create_format_processor',
    
    # Integration and compatibility
    'TokenIntegrationManager',
    'CompatibilityMatrix'
]