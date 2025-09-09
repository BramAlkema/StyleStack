"""
Multi-Format OOXML Handler Core Types

This module contains the core data types, enums, and dataclasses
used throughout the multi-format OOXML handling system.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class OOXMLFormat(Enum):
    """Supported OOXML template formats."""
    POWERPOINT = "potx"
    WORD = "dotx" 
    EXCEL = "xltx"
    
    @classmethod
    def from_extension(cls, extension: str) -> 'OOXMLFormat':
        """Get format from file extension."""
        ext = extension.lower().lstrip('.')
        for format_type in cls:
            if format_type.value == ext:
                return format_type
        raise ValueError(f"Unsupported OOXML format: {extension}")
    
    @classmethod
    def from_path(cls, path: Union[str, Path]) -> 'OOXMLFormat':
        """Get format from file path."""
        return cls.from_extension(Path(path).suffix)


@dataclass
class OOXMLStructure:
    """Defines the internal structure of an OOXML format."""
    main_document_path: str
    relationships_path: str
    content_types_path: str = "[Content_Types].xml"
    theme_paths: List[str] = None
    style_paths: List[str] = None
    required_namespaces: Dict[str, str] = None
    
    def __post_init__(self):
        if self.theme_paths is None:
            self.theme_paths = []
        if self.style_paths is None:
            self.style_paths = []
        if self.required_namespaces is None:
            self.required_namespaces = {}


@dataclass
class ProcessingResult:
    """Result of multi-format processing operation."""
    success: bool
    format_type: OOXMLFormat
    processed_files: List[str]
    errors: List[str]
    warnings: List[str]
    statistics: Dict[str, Any]
    output_path: Optional[str] = None
    
    def __post_init__(self):
        if self.processed_files is None:
            self.processed_files = []
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.statistics is None:
            self.statistics = {}


@dataclass
class FormatConfiguration:
    """Configuration for format-specific processing."""
    format_type: OOXMLFormat
    enable_validation: bool = True
    enable_token_integration: bool = True
    preserve_formatting: bool = True
    recovery_strategy: str = "best_effort"
    custom_namespaces: Optional[Dict[str, str]] = None
    processing_options: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.custom_namespaces is None:
            self.custom_namespaces = {}
        if self.processing_options is None:
            self.processing_options = {}


@dataclass
class ValidationIssue:
    """Represents a validation issue found during processing."""
    severity: str  # 'error', 'warning', 'info'
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class ProcessingStatistics:
    """Statistics from processing operations."""
    files_processed: int = 0
    patches_applied: int = 0
    tokens_resolved: int = 0
    processing_time: float = 0.0
    validation_issues: List[ValidationIssue] = None
    
    def __post_init__(self):
        if self.validation_issues is None:
            self.validation_issues = []