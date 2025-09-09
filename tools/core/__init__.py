"""StyleStack Core Types Module"""

from .types import (
    PatchOperationType,
    InsertPosition, 
    RecoveryStrategy,
    ErrorSeverity,
    PatchError,
    PatchResult,
    PatchOperation,
    XPathContext,
    ProcessingContext
)

__all__ = [
    'PatchOperationType',
    'InsertPosition',
    'RecoveryStrategy', 
    'ErrorSeverity',
    'PatchError',
    'PatchResult',
    'PatchOperation',
    'XPathContext',
    'ProcessingContext'
]