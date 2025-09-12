"""
Shared error handling utilities for StyleStack

This module eliminates the 100+ repetitive exception handling patterns
found across the codebase, providing consistent error handling and logging.

Based on duplication analysis findings:
- "except Exception as e:" with logging appears 100+ times
- Identical error message formatting patterns
- Repeated validation error collection logic
"""

from .imports import (
    contextmanager, get_logger, List, Dict, Any, Optional, Callable, Union, 
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from .validation import ValidationResult

logger = get_logger(__name__)


class StyleStackError(Exception):
    """Base exception for all StyleStack errors"""
    def __init__(self, message: str, context: Dict[str, Any] = None):
        super().__init__(message)
        self.context = context or {}


class ProcessingError(StyleStackError):
    """Exception for processing pipeline errors"""
    pass


class TemplateError(StyleStackError):
    """Exception for template-related errors"""
    pass


class TokenResolutionError(StyleStackError):  
    """Exception for token resolution errors"""
    pass


class ValidationError(StyleStackError):
    """Exception for validation errors"""
    pass


def handle_processing_error(
    operation_name: str, 
    error: Exception, 
    context: Dict[str, Any] = None
) -> str:
    """
    Standardized error handling with context
    
    Replaces patterns like:
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        return f"Error: {e}"
    
    Found in 100+ locations across the codebase
    """
    context = context or {}
    error_msg = f"{operation_name} failed: {error}"
    
    # Log with context
    logger.error(error_msg, extra={'context': context, 'exception': str(error)})
    
    return error_msg


@contextmanager
def error_boundary(
    operation_name: str, 
    error_collector: List[str] = None,
    reraise: bool = True,
    context: Dict[str, Any] = None
):
    """
    Error boundary context manager for consistent error collection
    
    Replaces repetitive try/except blocks with error collection
    
    Usage:
        errors = []
        with error_boundary("template processing", errors):
            # risky operation
            process_template()
        
        if errors:
            print(f"Errors encountered: {errors}")
    """
    try:
        yield
    except Exception as e:
        error_msg = handle_processing_error(operation_name, e, context)
        
        if error_collector is not None:
            error_collector.append(error_msg)
        
        if reraise:
            raise
        else:
            logger.debug(f"Error suppressed in error boundary: {error_msg}")


@contextmanager  
def validation_boundary(validation_result: 'ValidationResult', field_name: str = "unknown"):
    """
    Error boundary specifically for validation operations
    
    Captures exceptions and converts them to validation errors
    """
    try:
        yield
    except Exception as e:
        validation_result.add_error(
            field=field_name,
            message=f"Validation failed: {e}",
            code="VALIDATION_EXCEPTION",
            suggestion="Check input data format and try again"
        )


def safe_execute(
    operation: Callable[[], Any],
    operation_name: str,
    default_value: Any = None,
    context: Dict[str, Any] = None
) -> Any:
    """
    Safely execute operation with fallback
    
    Common pattern for operations that should not fail the entire pipeline
    """
    try:
        return operation()
    except Exception as e:
        handle_processing_error(operation_name, e, context)
        return default_value


def collect_errors(operations: List[tuple]) -> List[str]:
    """
    Execute multiple operations and collect all errors
    
    Args:
        operations: List of (operation_callable, operation_name) tuples
        
    Returns:
        List of error messages from failed operations
    """
    errors = []
    
    for operation, name in operations:
        with error_boundary(name, errors, reraise=False):
            operation()
    
    return errors


class ErrorCollector:
    """
    Utility class for collecting and managing errors during processing
    
    Replaces manual error list management patterns
    """
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.context: Dict[str, Any] = {}
    
    def add_error(self, message: str, operation: str = "", context: Dict[str, Any] = None):
        """Add an error with optional context"""
        if operation:
            message = f"{operation}: {message}"
        
        self.errors.append(message)
        
        if context:
            self.context.update(context)
        
        logger.error(message, extra={'context': context or {}})
    
    def add_warning(self, message: str, operation: str = ""):
        """Add a warning"""
        if operation:
            message = f"{operation}: {message}"
            
        self.warnings.append(message)
        logger.warning(message)
    
    def execute_with_error_handling(
        self, 
        operation: Callable[[], Any],
        operation_name: str,
        context: Dict[str, Any] = None
    ) -> Any:
        """Execute operation and collect any errors"""
        try:
            return operation()
        except Exception as e:
            self.add_error(str(e), operation_name, context)
            return None
    
    def has_errors(self) -> bool:
        """Check if any errors were collected"""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if any warnings were collected"""
        return len(self.warnings) > 0
    
    def get_summary(self) -> str:
        """Get summary of all collected errors and warnings"""
        summary_parts = []
        
        if self.errors:
            summary_parts.append(f"Errors ({len(self.errors)}):")
            for error in self.errors:
                summary_parts.append(f"  • {error}")
        
        if self.warnings:
            summary_parts.append(f"Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                summary_parts.append(f"  • {warning}")
        
        return "\n".join(summary_parts) if summary_parts else "No errors or warnings"
    
    def clear(self):
        """Clear all collected errors and warnings"""
        self.errors.clear()
        self.warnings.clear()
        self.context.clear()


def format_exception_details(e: Exception) -> Dict[str, Any]:
    """
    Format exception details for logging and debugging
    
    Returns structured information about the exception
    """
    import traceback
    
    return {
        "exception_type": type(e).__name__,
        "exception_message": str(e),
        "traceback": traceback.format_exc(),
        "args": getattr(e, 'args', [])
    }


def create_user_friendly_error(
    technical_error: str, 
    operation: str,
    suggestions: List[str] = None
) -> str:
    """
    Convert technical error messages to user-friendly ones
    
    Common pattern for CLI tools that need helpful error messages
    """
    suggestions = suggestions or []
    
    message_parts = [
        f"Failed to {operation}.",
        f"Technical details: {technical_error}"
    ]
    
    if suggestions:
        message_parts.append("Suggestions:")
        for suggestion in suggestions:
            message_parts.append(f"  • {suggestion}")
    
    return "\n".join(message_parts)


# Decorators for common error handling patterns
def catch_and_log(operation_name: str, default_return: Any = None):
    """
    Decorator to catch exceptions and log them
    
    Usage:
        @catch_and_log("template processing", default_return=[])
        def process_templates():
            # risky code
            return processed_templates
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handle_processing_error(operation_name, e)
                return default_return
        return wrapper
    return decorator


def retry_on_failure(max_attempts: int = 3, delay: float = 0.1):
    """
    Decorator to retry operations on failure
    
    Usage:
        @retry_on_failure(max_attempts=3, delay=0.5)
        def flaky_operation():
            # operation that might fail
            return result
    """
    import time
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.debug(f"Attempt {attempt + 1} failed, retrying: {e}")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_attempts} attempts failed: {e}")
            
            raise last_exception
        return wrapper
    return decorator


# Export all error handling utilities
__all__ = [
    # Exceptions
    'StyleStackError', 'ProcessingError', 'TemplateError', 
    'TokenResolutionError', 'ValidationError',
    # Functions
    'handle_processing_error', 'safe_execute', 'collect_errors',
    'format_exception_details', 'create_user_friendly_error',
    # Context managers
    'error_boundary', 'validation_boundary',
    # Classes
    'ErrorCollector',
    # Decorators
    'catch_and_log', 'retry_on_failure'
]