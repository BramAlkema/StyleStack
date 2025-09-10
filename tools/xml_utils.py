#!/usr/bin/env python3
"""
XML Utilities

Common XML processing utilities shared across StyleStack modules.
"""


from typing import Optional
import xml.etree.ElementTree as ET


def indent_xml(elem: ET.Element, level: int = 0) -> None:
    """Add proper indentation to XML elements for readable output.
    
    Args:
        elem: The XML element to indent
        level: Current indentation level (0 = root)
    """
    indent = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent
        for child in elem:
            indent_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = indent
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent


def format_xml_string(xml_content: str, include_declaration: bool = True) -> str:
    """Format XML string with proper indentation.
    
    Args:
        xml_content: Raw XML content string
        include_declaration: Whether to include XML declaration
        
    Returns:
        Properly formatted XML string
    """
    try:
        root = ET.fromstring(xml_content)
        indent_xml(root)
        xml_str = ET.tostring(root, encoding='unicode', method='xml')
        
        if include_declaration and not xml_str.startswith('<?xml'):
            xml_str = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + xml_str
            
        return xml_str
    except ET.ParseError:
        # Return original if parsing fails
        return xml_content


def safe_parse_xml(xml_content: str) -> Optional[ET.Element]:
    """Safely parse XML content, returning None on error.
    
    Args:
        xml_content: XML string to parse
        
    Returns:
        Parsed XML element or None if parsing fails
    """
    try:
        return ET.fromstring(xml_content)
    except ET.ParseError:
        return None