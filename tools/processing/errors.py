"""
Error Recovery and Handling System for JSON Patch Operations

This module provides comprehensive error handling, recovery strategies,
and fallback mechanisms for OOXML processing operations.
"""

from typing import Dict, List, Any, Optional, Callable
import logging
import traceback
from collections import defaultdict
from lxml import etree
from lxml.etree import XPathEvalError

from tools.core.types import PatchResult, ErrorSeverity, RecoveryStrategy

logger = logging.getLogger(__name__)


class ErrorRecoveryHandler:
    """
    Advanced error recovery system with multiple fallback strategies.
    
    Handles XPath errors, namespace issues, XML parsing problems,
    and provides intelligent recovery mechanisms.
    """
    
    def __init__(self, recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY_WITH_FALLBACK):
        self.recovery_strategy = recovery_strategy
        self.recovery_stats = defaultdict(int)
        
        # Error type to handler mapping
        self.error_handlers = {
            XPathEvalError: self._xpath_fallback_handler,
            etree.XMLSyntaxError: self._xml_fallback_handler,
            AttributeError: self._attribute_fallback_handler,
            KeyError: self._namespace_fallback_handler,
            ValueError: self._value_fallback_handler
        }
    
    def handle_error(self, 
                    exception: Exception,
                    operation: str,
                    target: str,
                    value: Any,
                    xml_doc: etree._Element,
                    xpath_system: Any = None) -> PatchResult:
        """
        Handle errors with appropriate recovery strategy.
        
        Args:
            exception: The exception that occurred
            operation: The patch operation being performed
            target: The XPath target
            value: The value being applied
            xml_doc: The XML document
            xpath_system: XPath targeting system (optional)
            
        Returns:
            PatchResult with recovery outcome
        """
        self.recovery_stats['total_errors'] += 1
        exception_type = type(exception)
        
        # Determine severity based on exception type
        severity = self._determine_severity(exception_type)
        
        # Apply recovery strategy
        if self.recovery_strategy == RecoveryStrategy.FAIL_FAST:
            return self._fail_fast(exception, operation, target, severity)
        elif self.recovery_strategy == RecoveryStrategy.SKIP_FAILED:
            return self._skip_with_logging(exception, operation, target, severity)
        elif self.recovery_strategy == RecoveryStrategy.BEST_EFFORT:
            return self._best_effort_recovery(exception, operation, target, value, xml_doc, xpath_system)
        else:  # RETRY_WITH_FALLBACK
            return self._retry_with_fallback(exception, operation, target, value, xml_doc, xpath_system)
    
    def _determine_severity(self, exception_type: type) -> ErrorSeverity:
        """Determine error severity based on exception type."""
        critical_errors = (etree.XMLSyntaxError, MemoryError)
        warning_errors = (AttributeError, KeyError)
        
        if exception_type in critical_errors:
            return ErrorSeverity.CRITICAL
        elif exception_type in warning_errors:
            return ErrorSeverity.WARNING
        else:
            return ErrorSeverity.ERROR
    
    def _retry_with_fallback(self, 
                           exception: Exception,
                           operation: str,
                           target: str,
                           value: Any,
                           xml_doc: etree._Element,
                           xpath_system: Any) -> PatchResult:
        """Retry operation with fallback handlers."""
        self.recovery_stats['recovery_attempts'] += 1
        exception_type = type(exception)
        
        if exception_type in self.error_handlers:
            handler = self.error_handlers[exception_type]
            try:
                result = handler(exception, operation, target, value, xml_doc, xpath_system)
                if result.success:
                    self.recovery_stats['successful_recoveries'] += 1
                return result
            except Exception as recovery_exception:
                logger.warning(f"Recovery handler failed: {recovery_exception}")
                return self._create_failed_result(
                    exception, operation, target, ErrorSeverity.ERROR,
                    recovery_attempted=True, recovery_exception=recovery_exception
                )
        
        return self._create_failed_result(exception, operation, target, ErrorSeverity.ERROR)
    
    def _best_effort_recovery(self, 
                            exception: Exception,
                            operation: str,
                            target: str,
                            value: Any,
                            xml_doc: etree._Element,
                            xpath_system: Any) -> PatchResult:
        """Best effort recovery - try multiple strategies."""
        self.recovery_stats['recovery_attempts'] += 1
        
        # Try all available handlers until one succeeds
        for handler in self.error_handlers.values():
            try:
                result = handler(exception, operation, target, value, xml_doc, xpath_system)
                if result.success:
                    self.recovery_stats['successful_recoveries'] += 1
                    return result
            except Exception:
                continue
        
        # If no handler succeeded, return a detailed failure
        return self._create_failed_result(
            exception, operation, target, ErrorSeverity.ERROR,
            recovery_attempted=True
        )
    
    def _xpath_fallback_handler(self, 
                              exception: Exception,
                              operation: str,
                              target: str,
                              value: Any,
                              xml_doc: etree._Element,
                              xpath_system: Any) -> PatchResult:
        """Fallback handler for XPath evaluation errors."""
        try:
            # Try to normalize the XPath expression
            if xpath_system:
                # Attempt namespace-agnostic XPath
                normalized_target = xpath_system.convert_to_local_name_xpath(target)
                
                # Try the normalized XPath
                elements = xml_doc.xpath(normalized_target)
                if elements:
                    return PatchResult(
                        success=True,
                        operation=operation,
                        target=normalized_target,
                        message=f"XPath recovered using local-name() fallback",
                        affected_elements=len(elements),
                        severity=ErrorSeverity.WARNING,
                        recovery_attempted=True,
                        recovery_strategy="local_name_xpath"
                    )
            
            return PatchResult(
                success=False,
                operation=operation,
                target=target,
                message=f"XPath error: {exception}. Try using local-name() or check namespaces.",
                severity=ErrorSeverity.ERROR
            )
            
        except Exception as e:
            return PatchResult(
                success=False,
                operation=operation,
                target=target,
                message=f"XPath fallback handler failed: {e}",
                severity=ErrorSeverity.ERROR
            )
    
    def _xml_fallback_handler(self, 
                            exception: Exception,
                            operation: str,
                            target: str,
                            value: Any,
                            xml_doc: etree._Element,
                            xpath_system: Any) -> PatchResult:
        """Fallback handler for XML syntax errors."""
        try:
            # Try to fix common XML issues if the value is a string
            if isinstance(value, str) and '<' in value:
                fixed_xml = self._attempt_xml_fix(value, xml_doc)
                if fixed_xml != value:
                    # Try parsing the fixed XML
                    try:
                        etree.fromstring(fixed_xml)
                        return PatchResult(
                            success=True,
                            operation=operation,
                            target=target,
                            message=f"XML syntax recovered with fixes",
                            affected_elements=1,
                            severity=ErrorSeverity.WARNING,
                            recovery_attempted=True,
                            recovery_strategy="xml_fix"
                        )
                    except etree.XMLSyntaxError:
                        pass  # Fixed version still invalid
            
            return PatchResult(
                success=False,
                operation=operation,
                target=target,
                message=f"XML syntax error: {exception}",
                severity=ErrorSeverity.ERROR
            )
            
        except Exception as e:
            return PatchResult(
                success=False,
                operation=operation,
                target=target,
                message=f"XML fallback handler failed: {e}",
                severity=ErrorSeverity.ERROR
            )
    
    def _namespace_fallback_handler(self, 
                                   exception: Exception,
                                   operation: str,
                                   target: str,
                                   value: Any,
                                   xml_doc: etree._Element,
                                   xpath_system: Any) -> PatchResult:
        """Fallback handler for namespace-related errors."""
        try:
            if xpath_system:
                normalized_target = xpath_system.normalize_xpath_with_context(target, xml_doc)
                if normalized_target != target:
                    return PatchResult(
                        success=False,  # Don't apply, suggest correction
                        operation=operation,
                        target=normalized_target,
                        message=f"Namespace corrected from '{target}' to '{normalized_target}'",
                        severity=ErrorSeverity.WARNING
                    )
            
            return PatchResult(
                success=False,
                operation=operation,
                target=target,
                message=f"Namespace error: {exception}",
                severity=ErrorSeverity.ERROR
            )
            
        except Exception as e:
            return PatchResult(
                success=False,
                operation=operation,
                target=target,
                message=f"Namespace fallback handler failed: {e}",
                severity=ErrorSeverity.ERROR
            )
    
    def _attribute_fallback_handler(self, 
                                   exception: Exception,
                                   operation: str,
                                   target: str,
                                   value: Any,
                                   xml_doc: etree._Element,
                                   xpath_system: Any) -> PatchResult:
        """Fallback handler for attribute-related errors."""
        return PatchResult(
            success=False,
            operation=operation,
            target=target,
            message=f"Attribute error: {exception}. Check target syntax and element structure.",
            severity=ErrorSeverity.ERROR
        )
    
    def _value_fallback_handler(self, 
                              exception: Exception,
                              operation: str,
                              target: str,
                              value: Any,
                              xml_doc: etree._Element,
                              xpath_system: Any) -> PatchResult:
        """Fallback handler for value-related errors."""
        try:
            # Try to convert value to string if possible
            if value is not None:
                str_value = str(value)
                return PatchResult(
                    success=True,
                    operation=operation,
                    target=target,
                    message=f"Value converted to string: {str_value}",
                    affected_elements=1,
                    severity=ErrorSeverity.WARNING,
                    recovery_attempted=True,
                    recovery_strategy="value_string_conversion"
                )
        except Exception:
            pass
        
        return PatchResult(
            success=False,
            operation=operation,
            target=target,
            message=f"Value error: {exception}",
            severity=ErrorSeverity.ERROR
        )
    
    def _attempt_xml_fix(self, xml_string: str, xml_doc: etree._Element) -> str:
        """Attempt to fix common XML syntax issues."""
        fixed = xml_string
        
        # Get namespace declarations from document
        namespaces = xml_doc.nsmap
        
        # Try to add missing namespace declarations
        if namespaces:
            # Simple heuristic: add xmlns declarations for common prefixes found in the string
            common_prefixes = ['a:', 'p:', 'w:', 'x:', 'r:']
            for prefix_with_colon in common_prefixes:
                prefix = prefix_with_colon[:-1]  # Remove the colon
                if prefix_with_colon in fixed and prefix in namespaces:
                    # Add namespace declaration if not already present
                    ns_decl = f'xmlns:{prefix}="{namespaces[prefix]}"'
                    if ns_decl not in fixed and not fixed.startswith('<' + prefix + ':'):
                        # Insert namespace declaration in the first element
                        fixed = fixed.replace('<' + prefix + ':', f'<{prefix}: {ns_decl} ', 1)
        
        return fixed
    
    def _skip_with_logging(self, exception: Exception, operation: str, target: str, severity: ErrorSeverity) -> PatchResult:
        """Skip failed operation with detailed logging."""
        logger.warning(f"Skipping failed operation {operation} on {target}: {exception}")
        return self._create_failed_result(exception, operation, target, severity, recovery_attempted=False)
    
    def _fail_fast(self, exception: Exception, operation: str, target: str, severity: ErrorSeverity) -> PatchResult:
        """Fail fast strategy - immediately return error."""
        self.recovery_stats['unrecoverable_errors'] += 1
        return self._create_failed_result(exception, operation, target, severity, recovery_attempted=False)
    
    def _create_failed_result(self, 
                             exception: Exception, 
                             operation: str, 
                             target: str, 
                             severity: ErrorSeverity,
                             recovery_attempted: bool = False,
                             recovery_exception: Optional[Exception] = None) -> PatchResult:
        """Create a standardized failed result with exception information."""
        exception_info = {
            'type': type(exception).__name__,
            'message': str(exception),
            'traceback': traceback.format_exc()
        }
        
        if recovery_exception:
            exception_info['recovery_error'] = {
                'type': type(recovery_exception).__name__,
                'message': str(recovery_exception)
            }
        
        return PatchResult(
            success=False,
            operation=operation,
            target=target,
            message=f"Operation failed: {exception}",
            severity=severity,
            recovery_attempted=recovery_attempted,
            exception_info=exception_info
        )
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get error recovery statistics."""
        stats = dict(self.recovery_stats)
        if stats['recovery_attempts'] > 0:
            stats['recovery_success_rate'] = stats['successful_recoveries'] / stats['recovery_attempts']
        else:
            stats['recovery_success_rate'] = 0.0
        return stats


class PerformanceTimer:
    """Context manager for timing operations."""
    
    def __init__(self, timing_stats: Dict[str, List[float]], operation_type: str):
        self.timing_stats = timing_stats
        self.operation_type = operation_type
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            import time
            duration = time.time() - self.start_time
            if self.operation_type in self.timing_stats:
                self.timing_stats[self.operation_type].append(duration)
            else:
                self.timing_stats[self.operation_type] = [duration]