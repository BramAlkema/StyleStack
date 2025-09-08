"""
YAML-to-OOXML Patch Operations Engine

This module provides the core XPath-based OOXML manipulation system that applies
YAML patches to Office template files (.potx, .dotx, .xltx).

Supports five patch operations:
- set: Replace attribute/text values  
- insert: Add new elements at specific positions
- extend: Add multiple elements (array-like operation)
- merge: Combine attributes/elements while preserving existing content
- relsAdd: Add OOXML relationship entries

Integration with StyleStack's design token system and Variable Resolution System.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import traceback
from lxml import etree
from lxml.etree import XPathEvalError


# Configure logging
logger = logging.getLogger(__name__)


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
            raise ValueError("Patch operation must specify 'operation' field")
        if 'target' not in patch_data:
            raise ValueError("Patch operation must specify 'target' field")
        if 'value' not in patch_data:
            raise ValueError("Patch operation must specify 'value' field")
        
        # Validate operation type
        operation = patch_data['operation']
        try:
            PatchOperationType(operation)
        except ValueError:
            valid_ops = [op.value for op in PatchOperationType]
            raise ValueError(f"Invalid operation '{operation}'. Must be one of: {valid_ops}")
        
        return cls(
            operation=operation,
            target=patch_data['target'],
            value=patch_data['value'],
            position=patch_data.get('position'),
            merge_strategy=patch_data.get('merge_strategy')
        )
    
    def validate(self) -> None:
        """Validate the patch operation parameters."""
        # Validate insert position if specified
        if self.operation == 'insert' and self.position:
            try:
                InsertPosition(self.position)
            except ValueError:
                valid_positions = [pos.value for pos in InsertPosition]
                raise ValueError(f"Invalid insert position '{self.position}'. Must be one of: {valid_positions}")


class XPathTargetingSystem:
    """
    Advanced XPath targeting system with namespace support and context awareness.
    
    Provides intelligent XPath resolution, namespace detection, and targeting validation
    for OOXML documents across PowerPoint, Word, and Excel formats.
    """
    
    def __init__(self):
        """Initialize the XPath targeting system."""
        # Standard OOXML namespaces
        self.base_namespaces = {
            # Drawing ML (shared across formats)
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
            'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
            
            # PowerPoint namespaces
            'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
            'p14': 'http://schemas.microsoft.com/office/powerpoint/2010/main',
            'p15': 'http://schemas.microsoft.com/office/powerpoint/2012/main',
            
            # Word namespaces  
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
            'w14': 'http://schemas.microsoft.com/office/word/2010/wordml',
            'w15': 'http://schemas.microsoft.com/office/word/2012/wordml',
            'w16': 'http://schemas.microsoft.com/office/word/2015/wordml',
            
            # Excel namespaces
            'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
            'x14': 'http://schemas.microsoft.com/office/spreadsheetml/2009/9/main',
            'x15': 'http://schemas.microsoft.com/office/spreadsheetml/2010/11/main',
            'xdr': 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing',
            
            # Package relationships
            'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
            'pkg': 'http://schemas.microsoft.com/office/2006/xmlPackage',
            
            # Office theme and styling
            'o': 'urn:schemas-microsoft-com:office:office',
            'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
            
            # Content types
            'ct': 'http://schemas.openxmlformats.org/package/2006/content-types',
            
            # Drawing Chart
            'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
            'cdr': 'http://schemas.openxmlformats.org/drawingml/2006/chartDrawing',
            
            # Compatibility and extended namespaces
            'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'dcterms': 'http://purl.org/dc/terms/',
            'dcmitype': 'http://purl.org/dc/dcmitype/',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            
            # LibreOffice/OpenOffice namespaces for cross-platform compatibility
            'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
            'style': 'urn:oasis:names:tc:opendocument:xmlns:style:1.0',
            'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
            'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
            'draw': 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0',
            'fo': 'urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0',
            'xlink': 'http://www.w3.org/1999/xlink',
            'svg': 'urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0',
            'chart': 'urn:oasis:names:tc:opendocument:xmlns:chart:1.0',
            'dr3d': 'urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0',
            'math': 'http://www.w3.org/1998/Math/MathML',
            'form': 'urn:oasis:names:tc:opendocument:xmlns:form:1.0',
            'script': 'urn:oasis:names:tc:opendocument:xmlns:script:1.0',
            'config': 'urn:oasis:names:tc:opendocument:xmlns:config:1.0',
            'manifest': 'urn:oasis:names:tc:opendocument:xmlns:manifest:1.0',
            
            # LibreOffice extended namespaces (newer versions)
            'loext': 'urn:org:documentfoundation:names:experimental:office:xmlns:loext:1.0',
            'calcext': 'urn:org:documentfoundation:names:experimental:calc:xmlns:calcext:1.0'
        }
        
        # Namespace aliases for common patterns
        self.namespace_aliases = {
            # Drawing ML aliases
            'drawing': 'a',
            'drawingml': 'a',
            
            # Application-specific aliases
            'powerpoint': 'p',
            'ppt': 'p',
            'presentation': 'p',
            'word': 'w',
            'doc': 'w',
            'excel': 'x',
            'xl': 'x',
            'spreadsheet': 'x',
            
            # Relationship aliases
            'relationship': 'r',
            'rel': 'r',
            'relationships': 'rel',
            
            # Chart aliases
            'chart': 'c',
            'chartdrawing': 'cdr',
            
            # OpenDocument/LibreOffice aliases
            'libreoffice': 'office',
            'openoffice': 'office',
            'odf': 'office',
            'opendocument': 'office',
            'odt': 'text',        # Writer document
            'ods': 'table',       # Calc spreadsheet  
            'odp': 'draw',        # Impress presentation
            'odg': 'draw',        # Draw graphics
            'odc': 'chart',       # Chart document
            'odb': 'office',      # Base database
            'odf_text': 'text',
            'odf_table': 'table',
            'odf_draw': 'draw',
            'odf_style': 'style',
            'calc': 'table',
            'writer': 'text',
            'impress': 'draw'
        }
        
        # Format-specific default namespaces for context-aware resolution
        self.format_defaults = {
            # Microsoft Office formats
            'potx': ['p', 'a', 'r'],  # PowerPoint defaults
            'pptx': ['p', 'a', 'r'], 
            'dotx': ['w', 'a', 'r'],  # Word defaults
            'docx': ['w', 'a', 'r'],
            'xltx': ['x', 'a', 'r'],  # Excel defaults
            'xlsx': ['x', 'a', 'r'],
            
            # OpenDocument/LibreOffice formats  
            'odt': ['text', 'office', 'style'],    # Writer text document
            'ods': ['table', 'office', 'style'],   # Calc spreadsheet
            'odp': ['draw', 'office', 'style'],    # Impress presentation
            'odg': ['draw', 'office', 'style'],    # Draw graphics
            'odc': ['chart', 'office', 'style'],   # Chart document
            'odb': ['office', 'form', 'script'],   # Base database
            'odf': ['office', 'style', 'text'],    # Generic OpenDocument
            
            # Additional cross-platform formats
            'rtf': ['w', 'a'],                     # Rich Text Format
            'html': ['text', 'office'],            # HTML with ODF elements
            'xml': ['office', 'style']             # Generic XML with ODF
        }
        
        # Cache for resolved namespaces per document
        self._namespace_cache = {}
        
        # XPath expression cache for performance
        self._xpath_cache = {}
        
        # Namespace usage statistics for optimization
        self._namespace_stats = {}
    
    def detect_document_namespaces(self, xml_doc: etree._Element) -> Dict[str, str]:
        """
        Automatically detect namespaces used in the document.
        
        Args:
            xml_doc: The XML document element
            
        Returns:
            Dictionary of namespace prefixes to URIs found in the document
        """
        doc_id = id(xml_doc)
        if doc_id in self._namespace_cache:
            return self._namespace_cache[doc_id]
        
        # Collect all namespaces from the document
        detected_namespaces = dict(self.base_namespaces)
        
        # Extract namespace declarations from root and descendants
        for elem in xml_doc.iter():
            # Add namespaces from this element
            if elem.nsmap:
                for prefix, uri in elem.nsmap.items():
                    if prefix is not None:  # Skip default namespace
                        detected_namespaces[prefix] = uri
                    elif uri and 'default' not in detected_namespaces:
                        detected_namespaces['default'] = uri
        
        # Cache the result
        self._namespace_cache[doc_id] = detected_namespaces
        return detected_namespaces
    
    def detect_document_format(self, xml_doc: etree._Element) -> str:
        """
        Detect the OOXML document format based on root element and namespaces.
        
        Args:
            xml_doc: The XML document element
            
        Returns:
            Format identifier (potx, dotx, xltx, etc.) or 'unknown'
        """
        root_tag = xml_doc.tag if xml_doc.tag else ""
        namespaces = self.detect_document_namespaces(xml_doc)
        
        # Check based on root element namespace - OOXML formats first
        if any(uri for prefix, uri in namespaces.items() 
               if 'presentationml' in uri or prefix == 'p'):
            return 'potx'
        elif any(uri for prefix, uri in namespaces.items() 
                 if 'wordprocessingml' in uri or prefix == 'w'):
            return 'dotx'
        elif any(uri for prefix, uri in namespaces.items() 
                 if 'spreadsheetml' in uri or prefix == 'x'):
            return 'xltx'
        
        # Check for OpenDocument/LibreOffice formats
        elif any(uri for prefix, uri in namespaces.items() 
                 if 'opendocument' in uri and 'text' in uri):
            return 'odt'
        elif any(uri for prefix, uri in namespaces.items() 
                 if 'opendocument' in uri and 'spreadsheet' in uri):
            return 'ods'
        elif any(uri for prefix, uri in namespaces.items() 
                 if 'opendocument' in uri and ('drawing' in uri or 'presentation' in uri)):
            return 'odp'
        elif any(uri for prefix, uri in namespaces.items() 
                 if 'opendocument' in uri and 'chart' in uri):
            return 'odc'
        elif any(uri for prefix, uri in namespaces.items() 
                 if 'opendocument' in uri):
            return 'odf'  # Generic OpenDocument
        
        # Fallback: check root element local name
        local_name = etree.QName(xml_doc).localname.lower()
        
        # OOXML root elements
        if local_name in ['presentation', 'slide', 'slidelayout', 'slidemaster']:
            return 'potx'
        elif local_name in ['document', 'wordprocessingml']:
            return 'dotx'  
        elif local_name in ['workbook', 'worksheet', 'chartsheet']:
            return 'xltx'
        
        # OpenDocument root elements
        elif local_name == 'document-content':
            # Need to check the office:mimetype or document type
            office_elem = xml_doc.find('.//{urn:oasis:names:tc:opendocument:xmlns:office:1.0}body')
            if office_elem is not None:
                for child in office_elem:
                    child_name = etree.QName(child).localname.lower()
                    if child_name == 'text':
                        return 'odt'
                    elif child_name == 'spreadsheet':
                        return 'ods'
                    elif child_name == 'presentation':
                        return 'odp'
                    elif child_name == 'drawing':
                        return 'odg'
                    elif child_name == 'chart':
                        return 'odc'
            return 'odf'
        elif local_name in ['office:document', 'office:document-content']:
            return 'odf'
            
        return 'unknown'
    
    def resolve_namespace_alias(self, alias: str) -> str:
        """
        Resolve a namespace alias to its standard prefix.
        
        Args:
            alias: The namespace alias to resolve
            
        Returns:
            Standard namespace prefix, or the original alias if not found
        """
        return self.namespace_aliases.get(alias.lower(), alias)
    
    def normalize_xpath_with_context(self, xpath_expr: str, xml_doc: etree._Element) -> str:
        """
        Normalize XPath expression with document format context and alias resolution.
        
        Args:
            xpath_expr: The original XPath expression
            xml_doc: The XML document for context
            
        Returns:
            Normalized XPath expression with proper namespace prefixes
        """
        format_type = self.detect_document_format(xml_doc)
        
        # Apply alias resolution
        normalized_expr = xpath_expr
        
        # Replace namespace aliases in XPath
        for alias, prefix in self.namespace_aliases.items():
            alias_pattern = f"{alias}:"
            prefix_pattern = f"{prefix}:"
            if alias_pattern in normalized_expr:
                normalized_expr = normalized_expr.replace(alias_pattern, prefix_pattern)
        
        # Add format-specific default namespace if path seems incomplete
        if format_type in self.format_defaults and not any(
            f"{prefix}:" in normalized_expr for prefix in ['a', 'p', 'w', 'x', 'r']
        ):
            # For simple element names, try adding the primary format namespace
            if normalized_expr.startswith('//') and ':' not in normalized_expr:
                primary_ns = self.format_defaults[format_type][0]
                # Convert //element to //ns:element
                if normalized_expr.count('/') >= 2:
                    parts = normalized_expr.split('/')
                    if len(parts) > 2 and parts[2] and not parts[2].startswith('@'):
                        parts[2] = f"{primary_ns}:{parts[2]}"
                        normalized_expr = '/'.join(parts)
        
        return normalized_expr
    
    def resolve_xpath_target(self, xml_doc: etree._Element, xpath_expr: str) -> List[Any]:
        """
        Resolve XPath expression with automatic namespace detection and intelligent fallbacks.
        
        Args:
            xml_doc: The XML document element
            xpath_expr: The XPath expression to resolve
            
        Returns:
            List of matching elements, attributes, or text nodes
            
        Raises:
            XPathEvalError: If the XPath expression is invalid
        """
        cache_key = (id(xml_doc), xpath_expr)
        if cache_key in self._xpath_cache:
            self._update_namespace_stats(xpath_expr, 'cache_hit')
            return self._xpath_cache[cache_key]
        
        # Get document-specific namespaces
        namespaces = self.detect_document_namespaces(xml_doc)
        
        # Normalize XPath with context-aware enhancements
        normalized_xpath = self.normalize_xpath_with_context(xpath_expr, xml_doc)
        
        try:
            # Attempt 1: Normalized XPath with full namespace context
            result = xml_doc.xpath(normalized_xpath, namespaces=namespaces)
            self._update_namespace_stats(xpath_expr, 'normalized_success')
            
        except XPathEvalError as e:
            # Fallback 1: Original XPath with detected namespaces
            try:
                logger.debug(f"Normalized XPath failed, trying original: {e}")
                result = xml_doc.xpath(xpath_expr, namespaces=namespaces)
                self._update_namespace_stats(xpath_expr, 'original_success')
                
            except XPathEvalError:
                # Fallback 2: Try with base namespaces only
                try:
                    logger.warning(f"XPath failed with detected namespaces, trying base namespaces: {e}")
                    result = xml_doc.xpath(xpath_expr, namespaces=self.base_namespaces)
                    self._update_namespace_stats(xpath_expr, 'base_ns_success')
                    
                except XPathEvalError:
                    # Fallback 3: Try simplified XPath without namespace prefixes
                    try:
                        logger.warning("XPath failed with base namespaces, trying simplified version")
                        simplified_xpath = self._simplify_xpath_namespaces(xpath_expr)
                        result = xml_doc.xpath(simplified_xpath, namespaces=namespaces)
                        self._update_namespace_stats(xpath_expr, 'simplified_success')
                        
                    except XPathEvalError:
                        # Fallback 4: Try format-specific namespace injection
                        try:
                            format_type = self.detect_document_format(xml_doc)
                            if format_type in self.format_defaults:
                                format_xpath = self._inject_format_namespaces(xpath_expr, format_type)
                                result = xml_doc.xpath(format_xpath, namespaces=namespaces)
                                self._update_namespace_stats(xpath_expr, 'format_injection_success')
                            else:
                                raise e
                        except XPathEvalError:
                            # Final fallback: raise the original error with context
                            self._update_namespace_stats(xpath_expr, 'failure')
                            raise XPathEvalError(
                                f"XPath resolution failed after all fallbacks: '{xpath_expr}'. "
                                f"Document format: {self.detect_document_format(xml_doc)}. "
                                f"Available namespaces: {list(namespaces.keys())}. "
                                f"Original error: {e}"
                            )
        
        # Cache successful result
        self._xpath_cache[cache_key] = result
        return result
    
    def _simplify_xpath_namespaces(self, xpath_expr: str) -> str:
        """
        Simplify XPath by removing namespace prefixes for basic fallback matching.
        
        Args:
            xpath_expr: Original XPath expression
            
        Returns:
            Simplified XPath without namespace prefixes
        """
        # Remove common namespace prefixes
        prefixes_to_remove = ['a:', 'p:', 'w:', 'x:', 'r:', 'rel:']
        simplified = xpath_expr
        
        for prefix in prefixes_to_remove:
            simplified = simplified.replace(prefix, '')
        
        return simplified
    
    def _inject_format_namespaces(self, xpath_expr: str, format_type: str) -> str:
        """
        Inject format-specific namespace prefixes into XPath expression.
        
        Args:
            xpath_expr: Original XPath expression
            format_type: Document format (potx, dotx, xltx)
            
        Returns:
            XPath expression with format-appropriate namespace prefixes injected
        """
        if format_type not in self.format_defaults:
            return xpath_expr
        
        default_prefixes = self.format_defaults[format_type]
        modified_xpath = xpath_expr
        
        # Inject primary namespace for unqualified element names
        if '//' in modified_xpath and ':' not in modified_xpath.split('/')[-1]:
            primary_ns = default_prefixes[0]
            parts = modified_xpath.split('/')
            
            # Find element names and add namespace prefix
            for i, part in enumerate(parts):
                if part and not part.startswith('@') and ':' not in part:
                    # Skip predicates in brackets
                    if '[' not in part or part.index('[') > 0:
                        element_name = part.split('[')[0] if '[' in part else part
                        if element_name and element_name not in ['*', '..', '.']:
                            remainder = part[len(element_name):]
                            parts[i] = f"{primary_ns}:{element_name}{remainder}"
            
            modified_xpath = '/'.join(parts)
        
        return modified_xpath
    
    def _update_namespace_stats(self, xpath_expr: str, result_type: str) -> None:
        """
        Update namespace usage statistics for optimization.
        
        Args:
            xpath_expr: The XPath expression that was resolved
            result_type: Type of resolution result (success type or failure)
        """
        if result_type not in self._namespace_stats:
            self._namespace_stats[result_type] = 0
        self._namespace_stats[result_type] += 1
        
        # Track XPath patterns for optimization
        pattern_key = f"pattern_{result_type}"
        if pattern_key not in self._namespace_stats:
            self._namespace_stats[pattern_key] = []
        
        # Store up to 10 examples of each pattern type
        if len(self._namespace_stats[pattern_key]) < 10:
            self._namespace_stats[pattern_key].append(xpath_expr)
    
    def get_namespace_stats(self) -> Dict[str, Any]:
        """
        Get namespace resolution statistics for performance analysis.
        
        Returns:
            Dictionary with resolution statistics and performance metrics
        """
        return dict(self._namespace_stats)


class ErrorRecoveryHandler:
    """
    Comprehensive error recovery system for YAML patch operations.
    
    Provides multiple recovery strategies, fallback mechanisms, and detailed
    error reporting to maximize successful patch application rates.
    """
    
    def __init__(self, recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY_WITH_FALLBACK):
        """
        Initialize error recovery handler.
        
        Args:
            recovery_strategy: Default recovery strategy to use
        """
        self.recovery_strategy = recovery_strategy
        self.fallback_handlers = {}
        self.recovery_stats = {
            'recovery_attempts': 0,
            'successful_recoveries': 0,
            'fallback_applications': 0,
            'unrecoverable_errors': 0
        }
        
        # Register default fallback handlers
        self._register_default_fallbacks()
    
    def _register_default_fallbacks(self):
        """Register default fallback strategies for common error patterns."""
        # XPath resolution fallbacks
        self.fallback_handlers['xpath_eval_error'] = self._xpath_fallback_handler
        self.fallback_handlers['target_not_found'] = self._target_fallback_handler
        self.fallback_handlers['invalid_xml'] = self._xml_fallback_handler
        self.fallback_handlers['namespace_error'] = self._namespace_fallback_handler
        self.fallback_handlers['attribute_error'] = self._attribute_fallback_handler
    
    def handle_error(self, 
                     exception: Exception, 
                     operation: str,
                     target: str,
                     value: Any,
                     xml_doc: etree._Element,
                     xpath_system: 'XPathTargetingSystem') -> PatchResult:
        """
        Handle a patch operation error with recovery strategies.
        
        Args:
            exception: The exception that occurred
            operation: The patch operation being performed
            target: The XPath target
            value: The value being applied
            xml_doc: The XML document
            xpath_system: The XPath targeting system
            
        Returns:
            PatchResult with recovery information
        """
        self.recovery_stats['recovery_attempts'] += 1
        
        # Determine error type and appropriate recovery strategy
        error_type = self._classify_error(exception)
        severity = self._assess_error_severity(exception, error_type)
        
        # Attempt recovery based on strategy
        if self.recovery_strategy in [RecoveryStrategy.RETRY_WITH_FALLBACK, RecoveryStrategy.BEST_EFFORT]:
            return self._attempt_recovery(
                error_type, exception, operation, target, value, xml_doc, xpath_system, severity
            )
        elif self.recovery_strategy == RecoveryStrategy.SKIP_FAILED:
            return self._skip_with_logging(exception, operation, target, severity)
        else:  # FAIL_FAST
            return self._fail_fast(exception, operation, target, severity)
    
    def _classify_error(self, exception: Exception) -> str:
        """Classify the type of error for appropriate recovery strategy."""
        if isinstance(exception, XPathEvalError):
            return 'xpath_eval_error'
        elif isinstance(exception, AttributeError) and 'has no attribute' in str(exception):
            return 'attribute_error'
        elif isinstance(exception, ValueError) and 'namespace prefix' in str(exception):
            return 'namespace_error'
        elif 'target not found' in str(exception).lower():
            return 'target_not_found'
        elif 'invalid xml' in str(exception).lower() or 'namespace prefix' in str(exception):
            return 'invalid_xml'
        else:
            return 'unknown_error'
    
    def _assess_error_severity(self, exception: Exception, error_type: str) -> ErrorSeverity:
        """Assess the severity of an error for recovery prioritization."""
        critical_patterns = ['corrupted document', 'invalid root', 'parse error']
        error_patterns = ['xpath syntax', 'invalid operation', 'missing required']
        warning_patterns = ['target not found', 'attribute missing', 'namespace']
        
        error_msg = str(exception).lower()
        
        if any(pattern in error_msg for pattern in critical_patterns):
            return ErrorSeverity.CRITICAL
        elif any(pattern in error_msg for pattern in error_patterns):
            return ErrorSeverity.ERROR
        elif any(pattern in error_msg for pattern in warning_patterns):
            return ErrorSeverity.WARNING
        else:
            return ErrorSeverity.ERROR  # Default to error for unknown issues
    
    def _attempt_recovery(self, 
                         error_type: str,
                         exception: Exception,
                         operation: str, 
                         target: str,
                         value: Any,
                         xml_doc: etree._Element,
                         xpath_system: 'XPathTargetingSystem',
                         severity: ErrorSeverity) -> PatchResult:
        """Attempt error recovery using registered fallback handlers."""
        if error_type in self.fallback_handlers:
            try:
                fallback_result = self.fallback_handlers[error_type](
                    exception, operation, target, value, xml_doc, xpath_system
                )
                
                if fallback_result.success:
                    self.recovery_stats['successful_recoveries'] += 1
                    fallback_result.recovery_attempted = True
                    fallback_result.fallback_applied = True
                    fallback_result.recovery_strategy = error_type
                    
                return fallback_result
                
            except Exception as recovery_exception:
                logger.warning(f"Recovery attempt failed: {recovery_exception}")
                return self._create_failed_result(
                    exception, operation, target, severity, recovery_attempted=True,
                    recovery_exception=recovery_exception
                )
        else:
            return self._create_failed_result(exception, operation, target, severity)
    
    def _xpath_fallback_handler(self, 
                               exception: Exception,
                               operation: str,
                               target: str, 
                               value: Any,
                               xml_doc: etree._Element,
                               xpath_system: 'XPathTargetingSystem') -> PatchResult:
        """Fallback handler for XPath evaluation errors."""
        try:
            # Try alternative XPath resolution strategies
            # context_info = xpath_system.get_xpath_context_info(xml_doc, target)
            
            # Generate alternative XPath expressions
            alternative_targets = []
            
            # Strategy 1: Try with namespace simplification
            simplified_target = xpath_system._simplify_xpath_namespaces(target)
            if simplified_target != target:
                alternative_targets.append(simplified_target)
            
            # Strategy 2: Try with format-specific namespace injection
            format_type = xpath_system.detect_document_format(xml_doc)
            if format_type in xpath_system.format_defaults:
                format_target = xpath_system._inject_format_namespaces(target, format_type)
                if format_target != target:
                    alternative_targets.append(format_target)
            
            # Try each alternative
            for alt_target in alternative_targets:
                try:
                    results = xpath_system.resolve_xpath_target(xml_doc, alt_target)
                    if results:
                        return PatchResult(
                            success=True,
                            operation=operation,
                            target=alt_target,
                            message=f"Recovered using alternative XPath: {alt_target}",
                            affected_elements=len(results),
                            severity=ErrorSeverity.WARNING
                        )
                except:
                    continue
            
            # No alternatives worked
            return PatchResult(
                success=False,
                operation=operation,
                target=target,
                message=f"XPath recovery failed: {exception}. Tried alternatives: {alternative_targets}",
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
    
    def _target_fallback_handler(self, 
                                exception: Exception,
                                operation: str,
                                target: str,
                                value: Any,
                                xml_doc: etree._Element,
                                xpath_system: 'XPathTargetingSystem') -> PatchResult:
        """Fallback handler for target not found errors."""
        try:
            # For certain operations, we can create missing elements
            if operation in ['set', 'insert']:
                # Try to find parent element and create missing child
                parent_xpath = '/'.join(target.split('/')[:-1]) if '/' in target else None
                
                if parent_xpath:
                    try:
                        parent_elements = xpath_system.resolve_xpath_target(xml_doc, parent_xpath)
                        if parent_elements:
                            # Parent exists, we could potentially create the missing element
                            return PatchResult(
                                success=False,
                                operation=operation,
                                target=target,
                                message=f"Target not found, but parent exists. Consider creating missing element first.",
                                severity=ErrorSeverity.WARNING
                            )
                    except:
                        pass
            
            return PatchResult(
                success=False,
                operation=operation,
                target=target,
                message=f"Target not found and no recovery possible: {exception}",
                severity=ErrorSeverity.ERROR
            )
            
        except Exception as e:
            return PatchResult(
                success=False,
                operation=operation,
                target=target,
                message=f"Target fallback handler failed: {e}",
                severity=ErrorSeverity.ERROR
            )
    
    def _xml_fallback_handler(self, 
                             exception: Exception,
                             operation: str,
                             target: str,
                             value: Any,
                             xml_doc: etree._Element,
                             xpath_system: 'XPathTargetingSystem') -> PatchResult:
        """Fallback handler for invalid XML errors."""
        try:
            if isinstance(value, str) and operation in ['insert', 'extend']:
                # Try to fix common XML issues
                fixed_value = self._attempt_xml_fix(value, xml_doc)
                if fixed_value != value:
                    return PatchResult(
                        success=False,  # Don't actually apply, just report the fix
                        operation=operation,
                        target=target,
                        message=f"XML fixed from '{value}' to '{fixed_value}'. Retry with corrected XML.",
                        severity=ErrorSeverity.WARNING
                    )
            
            return PatchResult(
                success=False,
                operation=operation,
                target=target,
                message=f"Invalid XML error: {exception}",
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
                                   xpath_system: 'XPathTargetingSystem') -> PatchResult:
        """Fallback handler for namespace-related errors."""
        # Use the enhanced namespace resolution
        try:
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
                                   xpath_system: 'XPathTargetingSystem') -> PatchResult:
        """Fallback handler for attribute-related errors."""
        return PatchResult(
            success=False,
            operation=operation,
            target=target,
            message=f"Attribute error: {exception}. Check target syntax and element structure.",
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
    
    def validate_xpath_syntax(self, xpath_expr: str) -> bool:
        """
        Validate XPath expression syntax without executing it.
        
        Args:
            xpath_expr: The XPath expression to validate
            
        Returns:
            True if syntax is valid, False otherwise
        """
        try:
            # Create a dummy element to test XPath compilation
            dummy_doc = etree.Element("test")
            etree.XPath(xpath_expr)
            return True
        except Exception:
            return False
    
    def get_xpath_context_info(self, xml_doc: etree._Element, xpath_expr: str) -> Dict[str, Any]:
        """
        Get detailed information about XPath expression context and resolution.
        
        Args:
            xml_doc: The XML document element
            xpath_expr: The XPath expression to analyze
            
        Returns:
            Dictionary with context information including namespaces, matches, and suggestions
        """
        info = {
            'xpath': xpath_expr,
            'is_valid_syntax': self.validate_xpath_syntax(xpath_expr),
            'detected_namespaces': self.detect_document_namespaces(xml_doc),
            'matches_found': 0,
            'target_type': None,
            'suggestions': []
        }
        
        try:
            matches = self.resolve_xpath_target(xml_doc, xpath_expr)
            info['matches_found'] = len(matches)
            
            if matches:
                first_match = matches[0]
                if isinstance(first_match, str):
                    info['target_type'] = 'text'
                elif hasattr(first_match, 'tag'):
                    info['target_type'] = 'element'
                else:
                    info['target_type'] = 'attribute'
        
        except XPathEvalError as e:
            info['error'] = str(e)
            info['suggestions'] = self._generate_xpath_suggestions(xpath_expr, xml_doc)
        
        return info
    
    def _generate_xpath_suggestions(self, failed_xpath: str, xml_doc: etree._Element) -> List[str]:
        """Generate helpful XPath suggestions for failed expressions."""
        suggestions = []
        
        # Common fixes
        if '//' not in failed_xpath and '/' in failed_xpath:
            suggestions.append(f"Try with descendant axis: {failed_xpath.replace('/', '//', 1)}")
        
        if '@' in failed_xpath and not failed_xpath.endswith(']'):
            # Attribute selection might need brackets
            suggestions.append("Ensure attribute selections use proper syntax: element[@attr='value']")
        
        # Namespace suggestions
        if ':' not in failed_xpath:
            suggestions.append("Consider adding namespace prefixes (e.g., 'a:', 'p:', 'w:')")
        
        return suggestions


class YAMLPatchProcessor:
    """
    Core YAML-to-OOXML patch processing engine.
    
    Applies YAML patch operations to OOXML documents using XPath targeting.
    Supports all major Office formats (.potx PowerPoint, .dotx Word, .xltx Excel).
    """
    
    def __init__(self, recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY_WITH_FALLBACK):
        """Initialize the patch processor with advanced XPath targeting and error recovery."""
        # Initialize XPath targeting system
        self.xpath_system = XPathTargetingSystem()
        
        # Initialize error recovery system
        self.error_handler = ErrorRecoveryHandler(recovery_strategy)
        
        # Quick access to namespaces for backward compatibility
        self.namespaces = self.xpath_system.base_namespaces
        
        # Statistics tracking
        self.stats = {
            'patches_applied': 0,
            'elements_modified': 0,
            'errors_encountered': 0,
            'xpath_cache_hits': 0,
            'namespace_detections': 0,
            'recoveries_attempted': 0,
            'recoveries_successful': 0
        }
    
    def apply_patch(self, xml_doc: etree._Element, patch_data: Dict[str, Any]) -> PatchResult:
        """
        Apply a single YAML patch to an OOXML document.
        
        Args:
            xml_doc: The OOXML document as lxml Element
            patch_data: Dictionary containing patch operation details
            
        Returns:
            PatchResult indicating success/failure and details
        """
        try:
            # Create and validate patch operation
            patch_op = PatchOperation.from_dict(patch_data)
            patch_op.validate()
            
            # Apply the specific operation
            if patch_op.operation == PatchOperationType.SET.value:
                return self._apply_set_operation(xml_doc, patch_op)
            elif patch_op.operation == PatchOperationType.INSERT.value:
                return self._apply_insert_operation(xml_doc, patch_op)
            elif patch_op.operation == PatchOperationType.EXTEND.value:
                return self._apply_extend_operation(xml_doc, patch_op)
            elif patch_op.operation == PatchOperationType.MERGE.value:
                return self._apply_merge_operation(xml_doc, patch_op)
            elif patch_op.operation == PatchOperationType.RELSADD.value:
                return self._apply_relsadd_operation(xml_doc, patch_op)
            else:
                raise PatchError(f"Unknown operation: {patch_op.operation}")
                
        except (PatchError, ValueError, XPathEvalError, Exception) as e:
            self.stats['errors_encountered'] += 1
            self.stats['recoveries_attempted'] += 1
            
            # Attempt error recovery
            recovery_result = self.error_handler.handle_error(
                e, 
                patch_data.get('operation', 'unknown'),
                patch_data.get('target', 'unknown'),
                patch_data.get('value'),
                xml_doc,
                self.xpath_system
            )
            
            if recovery_result.success:
                self.stats['recoveries_successful'] += 1
                logger.info(f"Successfully recovered from error: {recovery_result.message}")
            else:
                logger.error(f"Patch operation failed: {e}")
                
            return recovery_result
    
    def apply_patches(self, xml_doc: etree._Element, patches: List[Dict[str, Any]]) -> List[PatchResult]:
        """
        Apply multiple YAML patches to an OOXML document.
        
        Args:
            xml_doc: The OOXML document as lxml Element
            patches: List of patch operation dictionaries
            
        Returns:
            List of PatchResult objects for each patch
        """
        results = []
        
        for i, patch_data in enumerate(patches):
            logger.debug(f"Applying patch {i+1}/{len(patches)}: {patch_data.get('operation')} on {patch_data.get('target')}")
            result = self.apply_patch(xml_doc, patch_data)
            results.append(result)
            
            # Log result
            if result.success:
                logger.info(f"Patch {i+1} succeeded: {result.message}")
            else:
                logger.warning(f"Patch {i+1} failed: {result.message}")
        
        return results
    
    def _apply_set_operation(self, xml_doc: etree._Element, patch_op: PatchOperation) -> PatchResult:
        """Apply set operation to replace attribute or text values using advanced XPath targeting."""
        try:
            # Use advanced XPath targeting system
            targets = self.xpath_system.resolve_xpath_target(xml_doc, patch_op.target)
            
            if not targets:
                # Get context info for better error reporting
                context_info = self.xpath_system.get_xpath_context_info(xml_doc, patch_op.target)
                suggestions = context_info.get('suggestions', [])
                suggestion_text = f" Suggestions: {'; '.join(suggestions)}" if suggestions else ""
                raise PatchError(f"Target not found: {patch_op.target}.{suggestion_text}")
            
            affected_count = 0
            
            # Handle different target types based on XPath expression
            if '@' in patch_op.target:
                # Attribute targeting - XPath returns attribute values as strings
                # Extract attribute name and parent element
                attr_xpath = patch_op.target.rsplit('/@', 1)[0]
                attr_name = patch_op.target.split('@')[-1]
                parent_elements = self.xpath_system.resolve_xpath_target(xml_doc, attr_xpath)
                for parent in parent_elements:
                    parent.set(attr_name, str(patch_op.value))
                    affected_count += 1
            else:
                # Element or text targeting
                for target in targets:
                    if isinstance(target, str):
                        # Text node - need to update parent element's text
                        parent_xpath = patch_op.target.rsplit('/', 1)[0]
                        parent_elements = self.xpath_system.resolve_xpath_target(xml_doc, parent_xpath)
                        for parent in parent_elements:
                            parent.text = str(patch_op.value)
                            affected_count += 1
                    elif hasattr(target, 'tag'):
                        # Element - set text content
                        target.text = str(patch_op.value)
                        affected_count += 1
            
            self.stats['patches_applied'] += 1
            self.stats['elements_modified'] += affected_count
            
            return PatchResult(
                success=True,
                operation=patch_op.operation,
                target=patch_op.target,
                message=f"Set operation completed successfully",
                affected_elements=affected_count
            )
            
        except XPathEvalError as e:
            raise PatchError(f"XPath error in set operation: {e}")
    
    def _apply_insert_operation(self, xml_doc: etree._Element, patch_op: PatchOperation) -> PatchResult:
        """Apply insert operation to add new XML elements."""
        try:
            # Find target parent elements
            parent_elements = self.xpath_system.resolve_xpath_target(xml_doc, patch_op.target)
            
            if not parent_elements:
                # Get context info for better error reporting
                context_info = self.xpath_system.get_xpath_context_info(xml_doc, patch_op.target)
                suggestions = context_info.get('suggestions', [])
                suggestion_text = f" Suggestions: {'; '.join(suggestions)}" if suggestions else ""
                raise PatchError(f"Target not found for insert: {patch_op.target}.{suggestion_text}")
            
            # Parse the value as XML
            if isinstance(patch_op.value, str):
                try:
                    # Wrap in temporary root to handle fragments
                    wrapped_xml = f"<temp>{patch_op.value}</temp>"
                    temp_tree = etree.fromstring(wrapped_xml)
                    new_elements = list(temp_tree)
                except etree.XMLSyntaxError as e:
                    raise PatchError(f"Invalid XML in insert value: {e}")
            else:
                raise PatchError("Insert value must be XML string")
            
            affected_count = 0
            position = patch_op.position or 'append'
            
            for parent in parent_elements:
                for new_element in new_elements:
                    # Create a copy to avoid moving the same element
                    element_copy = etree.fromstring(etree.tostring(new_element))
                    
                    if position == 'append':
                        parent.append(element_copy)
                    elif position == 'prepend':
                        parent.insert(0, element_copy)
                    elif position == 'before':
                        parent.getparent().insert(
                            list(parent.getparent()).index(parent), 
                            element_copy
                        )
                    elif position == 'after':
                        parent.getparent().insert(
                            list(parent.getparent()).index(parent) + 1, 
                            element_copy
                        )
                    
                    affected_count += 1
            
            self.stats['patches_applied'] += 1
            self.stats['elements_modified'] += affected_count
            
            return PatchResult(
                success=True,
                operation=patch_op.operation,
                target=patch_op.target,
                message=f"Insert operation completed successfully ({position})",
                affected_elements=affected_count
            )
            
        except XPathEvalError as e:
            raise PatchError(f"XPath error in insert operation: {e}")
    
    def _apply_extend_operation(self, xml_doc: etree._Element, patch_op: PatchOperation) -> PatchResult:
        """Apply extend operation to add multiple elements (array-like operation)."""
        if not isinstance(patch_op.value, list):
            raise PatchError("Extend operation requires array/list value")
        
        total_affected = 0
        
        # Apply each value as a separate insert operation
        for value in patch_op.value:
            insert_patch = PatchOperation(
                operation='insert',
                target=patch_op.target,
                value=value,
                position=patch_op.position or 'append'
            )
            
            result = self._apply_insert_operation(xml_doc, insert_patch)
            if result.success:
                total_affected += result.affected_elements
            else:
                return result  # Return first failure
        
        return PatchResult(
            success=True,
            operation=patch_op.operation,
            target=patch_op.target,
            message=f"Extend operation completed successfully",
            affected_elements=total_affected
        )
    
    def _apply_merge_operation(self, xml_doc: etree._Element, patch_op: PatchOperation) -> PatchResult:
        """Apply merge operation to combine attributes/elements while preserving existing content."""
        try:
            # Find target elements
            target_elements = self.xpath_system.resolve_xpath_target(xml_doc, patch_op.target)
            
            if not target_elements:
                # Get context info for better error reporting
                context_info = self.xpath_system.get_xpath_context_info(xml_doc, patch_op.target)
                suggestions = context_info.get('suggestions', [])
                suggestion_text = f" Suggestions: {'; '.join(suggestions)}" if suggestions else ""
                raise PatchError(f"Target not found for merge: {patch_op.target}.{suggestion_text}")
            
            if not isinstance(patch_op.value, dict):
                raise PatchError("Merge operation requires dictionary value")
            
            affected_count = 0
            
            for target_element in target_elements:
                for key, value in patch_op.value.items():
                    if isinstance(value, dict):
                        # Create new child element with attributes
                        child_element = etree.SubElement(target_element, key)
                        for attr_name, attr_value in value.items():
                            child_element.set(attr_name, str(attr_value))
                    else:
                        # Set attribute directly
                        target_element.set(key, str(value))
                    
                    affected_count += 1
            
            self.stats['patches_applied'] += 1
            self.stats['elements_modified'] += affected_count
            
            return PatchResult(
                success=True,
                operation=patch_op.operation,
                target=patch_op.target,
                message=f"Merge operation completed successfully",
                affected_elements=affected_count
            )
            
        except XPathEvalError as e:
            raise PatchError(f"XPath error in merge operation: {e}")
    
    def _apply_relsadd_operation(self, xml_doc: etree._Element, patch_op: PatchOperation) -> PatchResult:
        """Apply relsAdd operation for OOXML relationship entries."""
        try:
            # Find relationships container
            rel_elements = self.xpath_system.resolve_xpath_target(xml_doc, patch_op.target)
            
            if not rel_elements:
                # Get context info for better error reporting
                context_info = self.xpath_system.get_xpath_context_info(xml_doc, patch_op.target)
                suggestions = context_info.get('suggestions', [])
                suggestion_text = f" Suggestions: {'; '.join(suggestions)}" if suggestions else ""
                raise PatchError(f"Relationships container not found: {patch_op.target}.{suggestion_text}")
            
            if not isinstance(patch_op.value, dict):
                raise PatchError("relsAdd operation requires dictionary value with Id, Type, Target")
            
            # Validate required relationship fields
            required_fields = ['Id', 'Type', 'Target']
            for field in required_fields:
                if field not in patch_op.value:
                    raise PatchError(f"relsAdd operation missing required field: {field}")
            
            affected_count = 0
            
            for rel_container in rel_elements:
                # Create new Relationship element
                rel_element = etree.SubElement(rel_container, "Relationship")
                rel_element.set("Id", patch_op.value['Id'])
                rel_element.set("Type", patch_op.value['Type'])
                rel_element.set("Target", patch_op.value['Target'])
                
                # Add optional attributes
                if 'TargetMode' in patch_op.value:
                    rel_element.set("TargetMode", patch_op.value['TargetMode'])
                
                affected_count += 1
            
            self.stats['patches_applied'] += 1
            self.stats['elements_modified'] += affected_count
            
            return PatchResult(
                success=True,
                operation=patch_op.operation,
                target=patch_op.target,
                message=f"relsAdd operation completed successfully",
                affected_elements=affected_count
            )
            
        except XPathEvalError as e:
            raise PatchError(f"XPath error in relsAdd operation: {e}")
    
    def get_statistics(self) -> Dict[str, int]:
        """Get processing statistics."""
        return self.stats.copy()
    
    def reset_statistics(self) -> None:
        """Reset processing statistics."""
        self.stats = {
            'patches_applied': 0,
            'elements_modified': 0,
            'errors_encountered': 0
        }
    
    def validate_xml_integrity(self, xml_doc: etree._Element) -> bool:
        """
        Validate that the OOXML document maintains structural integrity after patching.
        
        Args:
            xml_doc: The OOXML document to validate
            
        Returns:
            True if valid, False if integrity issues detected
        """
        try:
            # Basic XML well-formedness check
            xml_string = etree.tostring(xml_doc, encoding='unicode')
            etree.fromstring(xml_string)
            
            # Check for required OOXML structural elements (format-specific validation)
            root_tag = xml_doc.tag
            
            if 'presentationml' in root_tag:
                # PowerPoint validation - check for required slide elements
                return self._validate_powerpoint_structure(xml_doc)
            elif 'wordprocessingml' in root_tag:
                # Word validation - check for required document elements  
                return self._validate_word_structure(xml_doc)
            elif 'spreadsheetml' in root_tag:
                # Excel validation - check for required workbook elements
                return self._validate_excel_structure(xml_doc)
            else:
                # Generic XML validation passed
                return True
                
        except etree.XMLSyntaxError:
            logger.error("XML syntax error detected after patching")
            return False
    
    def _validate_powerpoint_structure(self, xml_doc: etree._Element) -> bool:
        """Validate PowerPoint slide structure."""
        required_elements = ['//p:cSld', '//p:spTree']
        for xpath in required_elements:
            if not self.xpath_system.resolve_xpath_target(xml_doc, xpath):
                logger.warning(f"PowerPoint structure missing: {xpath}")
                return False
        return True
    
    def _validate_word_structure(self, xml_doc: etree._Element) -> bool:
        """Validate Word document structure."""
        required_elements = ['//w:body']
        for xpath in required_elements:
            if not self.xpath_system.resolve_xpath_target(xml_doc, xpath):
                logger.warning(f"Word structure missing: {xpath}")
                return False
        return True
    
    def _validate_excel_structure(self, xml_doc: etree._Element) -> bool:
        """Validate Excel workbook structure."""
        # Basic structure validation - could be expanded
        return True  # Placeholder for Excel-specific validation


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
        
        # Apply patches
        processor = YAMLPatchProcessor()
        results = processor.apply_patches(xml_doc, patches)
        
        # Validate integrity
        if not processor.validate_xml_integrity(xml_doc):
            logger.warning("XML integrity validation failed after patching")
        
        # Return modified XML
        modified_xml = etree.tostring(xml_doc, encoding='unicode', pretty_print=True)
        return modified_xml, results
        
    except etree.XMLSyntaxError as e:
        error_result = PatchResult(
            success=False,
            operation='parse',
            target='xml_content',
            message=f"XML parsing error: {e}"
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