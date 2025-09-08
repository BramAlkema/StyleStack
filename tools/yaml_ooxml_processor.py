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

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging
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
            
            # Word namespaces  
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
            'w14': 'http://schemas.microsoft.com/office/word/2010/wordml',
            'w15': 'http://schemas.microsoft.com/office/word/2012/wordml',
            
            # Excel namespaces
            'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
            'x14': 'http://schemas.microsoft.com/office/spreadsheetml/2009/9/main',
            'x15': 'http://schemas.microsoft.com/office/spreadsheetml/2010/11/main',
            
            # Package relationships
            'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
            'pkg': 'http://schemas.microsoft.com/office/2006/xmlPackage',
            
            # Office theme and styling
            'o': 'urn:schemas-microsoft-com:office:office',
            'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
            
            # Content types
            'ct': 'http://schemas.openxmlformats.org/package/2006/content-types'
        }
        
        # Cache for resolved namespaces per document
        self._namespace_cache = {}
        
        # XPath expression cache for performance
        self._xpath_cache = {}
    
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
            return self._xpath_cache[cache_key]
        
        # Get document-specific namespaces
        namespaces = self.detect_document_namespaces(xml_doc)
        
        try:
            # First attempt: exact XPath with detected namespaces
            result = xml_doc.xpath(xpath_expr, namespaces=namespaces)
            
        except XPathEvalError as e:
            # Fallback 1: Try with base namespaces only
            try:
                logger.warning(f"XPath failed with detected namespaces, trying base namespaces: {e}")
                result = xml_doc.xpath(xpath_expr, namespaces=self.base_namespaces)
                
            except XPathEvalError:
                # Fallback 2: Try without namespace prefixes (for simple paths)
                try:
                    logger.warning("XPath failed with base namespaces, trying without prefixes")
                    simplified_xpath = self._simplify_xpath_namespaces(xpath_expr)
                    result = xml_doc.xpath(simplified_xpath, namespaces=namespaces)
                    
                except XPathEvalError:
                    # Final fallback: raise the original error
                    raise e
        
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
    
    def __init__(self):
        """Initialize the patch processor with advanced XPath targeting."""
        # Initialize XPath targeting system
        self.xpath_system = XPathTargetingSystem()
        
        # Quick access to namespaces for backward compatibility
        self.namespaces = self.xpath_system.base_namespaces
        
        # Statistics tracking
        self.stats = {
            'patches_applied': 0,
            'elements_modified': 0,
            'errors_encountered': 0,
            'xpath_cache_hits': 0,
            'namespace_detections': 0
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
                
        except (PatchError, ValueError, XPathEvalError) as e:
            self.stats['errors_encountered'] += 1
            logger.error(f"Patch operation failed: {e}")
            return PatchResult(
                success=False,
                operation=patch_data.get('operation', 'unknown'),
                target=patch_data.get('target', 'unknown'),
                message=str(e)
            )
    
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