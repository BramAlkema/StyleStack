"""Core utilities and base classes for OOXML processing.

This module provides foundational components used across all other modules:
- OOXML package handling and ZIP operations
- XML processing and normalization utilities  
- Configuration management
- Logging infrastructure
- Error handling and exceptions
- Cross-platform file path utilities
"""

from .exceptions import (
    OOXMLTesterError,
    PackageError,
    ConversionError,
    ValidationError,
    PlatformError,
)

from .config import Config
from .logging import setup_logging, get_logger
from .utils import normalize_path, ensure_directory, cleanup_temp_files

__all__ = [
    "OOXMLTesterError",
    "PackageError", 
    "ConversionError",
    "ValidationError",
    "PlatformError",
    "Config",
    "setup_logging",
    "get_logger",
    "normalize_path",
    "ensure_directory",
    "cleanup_temp_files",
]