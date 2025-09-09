"""
XPath Targeting System for OOXML Processing

This module provides advanced XPath expression handling with namespace resolution,
validation, and optimization for OOXML document manipulation.
"""

from typing import Dict, List, Any, Optional, Set
import logging
from collections import defaultdict
from lxml import etree
from lxml.etree import XPathEvalError

from tools.core.types import XPathContext

logger = logging.getLogger(__name__)


class XPathTargetingSystem:
    """
    Advanced XPath targeting system with multi-format namespace support.
    
    Handles namespace resolution, collision detection, and XPath optimization
    for Microsoft Office and OpenDocument formats.
    """
    
    def __init__(self):
        # Base namespace definitions for OOXML and OpenDocument
        self.base_namespaces = {
            # Microsoft Office namespaces
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
            'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
            'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
            'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
            'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
            'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
            'cdr': 'http://schemas.openxmlformats.org/drawingml/2006/chartDrawing',
            'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
            'dgm': 'http://schemas.openxmlformats.org/drawingml/2006/diagram',
            'xdr': 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing',
            'thm15': 'http://schemas.microsoft.com/office/thememl/2012/main',
            
            # Theme and styling  
            'theme': 'http://schemas.openxmlformats.org/drawingml/2006/main',
            'styleSheet': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
            
            # Relationship namespaces
            'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
            
            # Content types
            'ct': 'http://schemas.openxmlformats.org/package/2006/content-types',
            
            # OpenDocument Format namespaces
            'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
            'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
            'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
            'draw': 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0',
            'style': 'urn:oasis:names:tc:opendocument:xmlns:style:1.0',
            'number': 'urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0',
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
    
    def detect_document_namespaces(self, xml_doc: etree._Element, custom_declarations: Dict[str, str] = None) -> Dict[str, str]:
        """
        Advanced namespace detection with collision resolution and custom declarations.
        
        Args:
            xml_doc: The XML document element
            custom_declarations: Custom namespace declarations from patches
            
        Returns:
            Dictionary of namespace prefixes to URIs with collision resolution
        """
        doc_id = id(xml_doc)
        custom_key = str(sorted(custom_declarations.items())) if custom_declarations else ""
        cache_key = f"{doc_id}:{hash(custom_key)}"
        
        if cache_key in self._namespace_cache:
            return self._namespace_cache[cache_key]
        
        # Start with base namespaces
        detected_namespaces = dict(self.base_namespaces)
        
        # Apply custom namespace declarations first (highest priority)
        if custom_declarations:
            for prefix, uri in custom_declarations.items():
                if prefix in detected_namespaces and detected_namespaces[prefix] != uri:
                    logger.warning(f"Custom namespace declaration overrides existing: {prefix} -> {uri}")
                detected_namespaces[prefix] = uri
        
        # Extract namespace declarations from document with collision resolution
        namespace_collisions = {}
        
        for elem in xml_doc.iter():
            if elem.nsmap:
                for prefix, uri in elem.nsmap.items():
                    if prefix is not None:
                        # Handle namespace prefix collisions
                        if prefix in detected_namespaces:
                            if detected_namespaces[prefix] != uri:
                                # Collision detected - resolve it
                                original_uri = detected_namespaces[prefix]
                                resolved_prefix = self._resolve_namespace_collision(
                                    prefix, uri, original_uri, namespace_collisions
                                )
                                detected_namespaces[resolved_prefix] = uri
                                namespace_collisions[prefix] = {
                                    'original': original_uri,
                                    'collision': uri,
                                    'resolved_prefix': resolved_prefix
                                }
                        else:
                            detected_namespaces[prefix] = uri
                    elif uri and 'default' not in detected_namespaces:
                        detected_namespaces['default'] = uri
        
        # Validate namespace URIs
        self._validate_namespace_uris(detected_namespaces)
        
        # Cache the result
        self._namespace_cache[cache_key] = detected_namespaces
        
        return detected_namespaces
    
    def _resolve_namespace_collision(self, prefix: str, new_uri: str, existing_uri: str, 
                                   collisions: Dict[str, Any]) -> str:
        """
        Resolve namespace prefix collisions by generating unique prefixes.
        
        Args:
            prefix: Original prefix with collision
            new_uri: New namespace URI causing collision
            existing_uri: Existing namespace URI
            collisions: Dictionary tracking collisions
            
        Returns:
            Resolved unique prefix for the new URI
        """
        # Generate unique prefix for the colliding namespace
        counter = 1
        resolved_prefix = f"{prefix}{counter}"
        
        while resolved_prefix in collisions or resolved_prefix in self.base_namespaces:
            counter += 1
            resolved_prefix = f"{prefix}{counter}"
        
        logger.debug(f"Resolved namespace collision: {prefix} -> {resolved_prefix} for URI {new_uri}")
        return resolved_prefix
    
    def _validate_namespace_uris(self, namespaces: Dict[str, str]):
        """
        Validate namespace URIs for common issues.
        
        Args:
            namespaces: Dictionary of namespace prefixes to URIs
        """
        for prefix, uri in namespaces.items():
            # Check for invalid URIs
            if not uri or not isinstance(uri, str):
                logger.warning(f"Invalid namespace URI for prefix '{prefix}': {uri}")
                continue
            
            # Check for common URI issues
            if uri.startswith('http://') and 'schemas' not in uri:
                logger.debug(f"Potentially invalid namespace URI for '{prefix}': {uri}")
            
            # Check for deprecated namespaces
            if 'office/2003' in uri or 'office/2000' in uri:
                logger.warning(f"Deprecated namespace detected for '{prefix}': {uri}")
    
    def validate_xpath_expression(self, xpath_expr: str, namespaces: Dict[str, str] = None) -> bool:
        """
        Validate XPath expression syntax and namespace usage.
        
        Args:
            xpath_expr: XPath expression to validate
            namespaces: Available namespace declarations
            
        Returns:
            True if valid, False otherwise
        """
        if not xpath_expr or not isinstance(xpath_expr, str):
            return False
        
        try:
            # Try to compile the XPath expression
            compiled_xpath = etree.XPath(xpath_expr, namespaces=namespaces or {})
            return True
        except XPathEvalError as e:
            logger.debug(f"Invalid XPath expression '{xpath_expr}': {e}")
            return False
        except Exception as e:
            logger.debug(f"Error validating XPath expression '{xpath_expr}': {e}")
            return False
    
    def get_xpath_context_info(self, xml_doc: etree._Element, xpath_expr: str) -> Dict[str, Any]:
        """
        Get context information for XPath expression evaluation.
        
        Args:
            xml_doc: XML document for context
            xpath_expr: XPath expression
            
        Returns:
            Context information including namespaces and validation status
        """
        return {
            'expression': xpath_expr,
            'namespaces': self.detect_document_namespaces(xml_doc),
            'document_root': xml_doc.tag if xml_doc is not None else None,
            'valid': self.validate_xpath_expression(xpath_expr, self.detect_document_namespaces(xml_doc))
        }