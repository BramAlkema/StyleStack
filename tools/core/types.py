"""
Core Types and Data Structures for StyleStack OOXML Processing

This module contains the fundamental enums and dataclasses used across
the OOXML patch processing system.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class PatchOperationType(Enum):
    """Supported YAML patch operations for OOXML manipulation."""
    SET = "set"
    INSERT = "insert" 
    EXTEND = "extend"
    MERGE = "merge"
    RELSADD = "relsAdd"


class InsertPosition(Enum):
    """Supported positions for insert operations."""
    APPEND = "append"
    PREPEND = "prepend"
    BEFORE = "before"
    AFTER = "after"


class RecoveryStrategy(Enum):
    """Error recovery strategies for failed patch operations."""
    FAIL_FAST = "fail_fast"           # Stop on first error
    SKIP_FAILED = "skip_failed"       # Skip failed operations, continue with others
    RETRY_WITH_FALLBACK = "retry_with_fallback"  # Try alternative approaches
    BEST_EFFORT = "best_effort"       # Apply what's possible, report what failed


class ErrorSeverity(Enum):
    """Severity levels for patch operation errors."""
    CRITICAL = "critical"    # Complete failure, cannot proceed
    ERROR = "error"          # Operation failed but others can continue  
    WARNING = "warning"      # Operation succeeded with issues
    INFO = "info"           # Informational message


class PatchError(Exception):
    """Exception raised when patch operations fail."""
    pass


@dataclass
class PatchResult:
    """Result of applying a single patch operation."""
    success: bool
    operation: str
    target: str
    message: str
    affected_elements: int = 0
    severity: ErrorSeverity = ErrorSeverity.INFO
    recovery_attempted: bool = False
    recovery_strategy: Optional[str] = None
    fallback_applied: bool = False
    exception_info: Optional[Dict[str, Any]] = None
    affected_files: Optional[List[str]] = None  # For transaction rollback support
    warnings: Optional[List[str]] = None  # For validation warnings


@dataclass
class PatchOperation:
    """Represents a single YAML patch operation."""
    operation: str
    target: str
    value: Any
    position: Optional[str] = None
    merge_strategy: Optional[str] = None
    
    @classmethod
    def from_dict(cls, patch_data: Dict[str, Any]) -> 'PatchOperation':
        """Create PatchOperation from dictionary data."""
        # Validate required fields
        if 'operation' not in patch_data:
            raise ValueError("PatchOperation requires 'operation' field")
        if 'target' not in patch_data:
            raise ValueError("PatchOperation requires 'target' field")
        if 'value' not in patch_data:
            raise ValueError("PatchOperation requires 'value' field")
            
        return cls(
            operation=patch_data['operation'],
            target=patch_data['target'],
            value=patch_data['value'],
            position=patch_data.get('position'),
            merge_strategy=patch_data.get('merge_strategy')
        )


@dataclass
class XPathContext:
    """Context information for XPath expression evaluation."""
    namespaces: Dict[str, str]
    document_root: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    functions: Optional[Dict[str, Any]] = None


@dataclass
class ProcessingContext:
    """Context for OOXML processing operations."""
    file_path: str
    document_type: str
    operation_count: int = 0
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []