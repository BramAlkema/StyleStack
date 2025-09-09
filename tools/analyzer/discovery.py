"""
Design Element Discovery System

This module provides pattern-based discovery of design elements
in OOXML templates with format-specific discovery patterns.
"""

from typing import Dict, List, Any, Optional, Set
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    import lxml.etree as lxml_ET
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False

from .types import DesignElement, DesignElementType, AnalysisContext


class ElementDiscoveryEngine:
    """
    Discovery engine for finding customizable design elements in OOXML files.
    
    Uses pattern-based discovery with format-specific patterns for
    PowerPoint, Word, and Excel templates.
    """
    
    def __init__(self, context: AnalysisContext):
        self.context = context
        
        # Discovery patterns by template type
        self.discovery_patterns = {
            'powerpoint_theme': self._get_powerpoint_theme_patterns(),
            'powerpoint_slide_master': self._get_powerpoint_slide_master_patterns(),
            'word_styles': self._get_word_styles_patterns(),
            'word_document': self._get_word_document_patterns(),
            'excel_styles': self._get_excel_styles_patterns(),
            'excel_workbook': self._get_excel_workbook_patterns()
        }
        
        # Element priority scoring
        self.element_priorities = {
            'brand_color': 10.0,
            'brand_font': 9.0,
            'primary_color': 8.5,
            'heading_style': 8.0,
            'accent_color': 7.5,
            'body_font': 7.0,
            'background_color': 6.5,
            'secondary_font': 6.0,
            'border': 5.0,
            'effect': 4.0,
            'decorative': 3.0
        }
    
    def discover_elements_in_file(self, file_path: str, xml_content: str) -> List[DesignElement]:
        """
        Discover design elements in a single XML file.
        
        Args:
            file_path: Path to the XML file within the template
            xml_content: Raw XML content
            
        Returns:
            List of discovered design elements
        """
        elements = []
        
        try:
            # Parse XML content
            if LXML_AVAILABLE:
                root = lxml_ET.fromstring(xml_content.encode('utf-8'))
                parser_type = 'lxml'
            else:
                root = ET.fromstring(xml_content)
                parser_type = 'etree'
            
            # Determine file type and get appropriate patterns
            file_type = self._determine_file_type(file_path)
            patterns = self.discovery_patterns.get(file_type, [])
            
            # Apply discovery patterns
            for pattern in patterns:
                discovered = self._apply_discovery_pattern(
                    root, pattern, file_path, parser_type
                )
                elements.extend(discovered)
            
            # Remove duplicates and enhance metadata
            elements = self._deduplicate_elements(elements)
            elements = self._enhance_element_metadata(elements, file_path)
            
        except ET.ParseError as e:
            # Log parsing error but continue
            self.context.processing_stats.setdefault('parse_errors', []).append(
                {'file': file_path, 'error': str(e)}
            )
        except Exception as e:
            # Log unexpected error
            self.context.processing_stats.setdefault('discovery_errors', []).append(
                {'file': file_path, 'error': str(e)}
            )
        
        return elements
    
    def _determine_file_type(self, file_path: str) -> str:
        """Determine the type of OOXML file for pattern selection."""
        path_lower = file_path.lower()
        
        if 'theme' in path_lower and '.xml' in path_lower:
            return 'powerpoint_theme' if 'ppt' in self.context.template_type else 'theme'
        elif 'slidemaster' in path_lower or 'slideMaster' in path_lower:
            return 'powerpoint_slide_master'
        elif 'styles.xml' in path_lower:
            if 'word' in self.context.template_type or 'dot' in self.context.template_type:
                return 'word_styles'
            else:
                return 'excel_styles'
        elif 'document.xml' in path_lower:
            return 'word_document'
        elif 'workbook.xml' in path_lower:
            return 'excel_workbook'
        elif 'slide' in path_lower and '.xml' in path_lower:
            return 'powerpoint_slide'
        else:
            return 'generic'
    
    def _apply_discovery_pattern(self, root: ET.Element, pattern: Dict[str, Any], 
                                file_path: str, parser_type: str) -> List[DesignElement]:
        """Apply a single discovery pattern to find elements."""
        elements = []
        xpath = pattern['xpath']
        
        try:
            # Find matching elements
            if parser_type == 'lxml' and LXML_AVAILABLE:
                matches = root.xpath(xpath, namespaces=self.context.namespaces)
            else:
                # Use ElementTree findall with namespace handling
                matches = self._findall_with_namespaces(root, xpath)
            
            # Process each match
            for i, match in enumerate(matches):
                element = self._create_design_element(
                    match, pattern, file_path, i
                )
                if element:
                    elements.append(element)
                    
        except Exception as e:
            # Log XPath error but continue
            self.context.processing_stats.setdefault('xpath_errors', []).append(
                {'xpath': xpath, 'file': file_path, 'error': str(e)}
            )
        
        return elements
    
    def _findall_with_namespaces(self, root: ET.Element, xpath: str) -> List[ET.Element]:
        """ElementTree findall with namespace handling."""
        # Simple XPath to ElementTree findall conversion
        # This is a simplified version - real implementation would be more robust
        if xpath.startswith('//'):
            # Convert //tagname to .//tagname
            tag = xpath[2:]
            if '/' in tag:
                # More complex xpath - use first part
                tag = tag.split('/')[0]
            
            # Handle namespaced tags
            if ':' in tag:
                prefix, local = tag.split(':', 1)
                if prefix in self.context.namespaces:
                    tag = f"{{{self.context.namespaces[prefix]}}}{local}"
            
            return root.findall(f".//{tag}")
        
        return []
    
    def _create_design_element(self, xml_element: ET.Element, pattern: Dict[str, Any],
                              file_path: str, index: int) -> Optional[DesignElement]:
        """Create a DesignElement from an XML element and pattern."""
        try:
            # Generate unique ID
            element_id = f"{file_path}_{pattern['element_type'].value}_{index}"
            
            # Extract current value
            value_attr = pattern.get('value_attribute')
            current_value = ""
            if value_attr:
                current_value = xml_element.get(value_attr, "")
            elif xml_element.text:
                current_value = xml_element.text.strip()
            
            # Generate semantic name
            semantic_name = self._generate_semantic_name(
                xml_element, pattern, current_value, index
            )
            
            # Generate XPath expression
            xpath_expr = self._generate_xpath_expression(xml_element, pattern)
            
            # Calculate priority score
            priority_score = self._calculate_priority_score(
                semantic_name, pattern['element_type'], current_value
            )
            
            return DesignElement(
                id=element_id,
                element_type=pattern['element_type'],
                semantic_name=semantic_name,
                current_value=current_value,
                xpath_expression=xpath_expr,
                file_location=file_path,
                is_customizable=pattern.get('is_customizable', True),
                priority_score=priority_score,
                usage_frequency=1,
                customization_impact=5.0,
                brand_relevance=self._calculate_brand_relevance(semantic_name),
                accessibility_impact=self._calculate_accessibility_impact(pattern['element_type']),
                cross_platform_compatible=True,
                office_versions_supported=['2016', '2019', '2021', 'O365'],
                metadata={
                    'pattern_type': pattern.get('pattern_type', 'standard'),
                    'discovery_method': 'xpath_pattern',
                    'file_type': self._determine_file_type(file_path)
                }
            )
            
        except Exception as e:
            # Log element creation error
            self.context.processing_stats.setdefault('element_creation_errors', []).append(
                {'file': file_path, 'error': str(e)}
            )
            return None
    
    def _generate_semantic_name(self, xml_element: ET.Element, pattern: Dict[str, Any],
                               current_value: str, index: int) -> str:
        """Generate a semantic name for the design element."""
        # Try pattern-based naming first
        name_pattern = pattern.get('semantic_name_pattern')
        if name_pattern and current_value:
            import re
            match = re.search(name_pattern, current_value)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        
        # Fall back to element type + index
        element_type = pattern['element_type'].value
        return f"{element_type}_{index + 1}"
    
    def _generate_xpath_expression(self, xml_element: ET.Element, pattern: Dict[str, Any]) -> str:
        """Generate XPath expression to target this specific element."""
        # This is a simplified version - real implementation would be more sophisticated
        return pattern['xpath']
    
    def _calculate_priority_score(self, semantic_name: str, element_type: DesignElementType,
                                 current_value: str) -> float:
        """Calculate priority score for the design element."""
        base_score = 5.0
        
        # Boost score for important elements
        name_lower = semantic_name.lower()
        for key, score in self.element_priorities.items():
            if key in name_lower:
                return score
        
        # Type-based scoring
        type_scores = {
            DesignElementType.COLOR: 7.0,
            DesignElementType.FONT: 6.5,
            DesignElementType.TEXT_FORMAT: 6.0,
            DesignElementType.BORDER: 4.0,
            DesignElementType.EFFECT: 3.0
        }
        
        return type_scores.get(element_type, base_score)
    
    def _calculate_brand_relevance(self, semantic_name: str) -> float:
        """Calculate brand relevance score."""
        brand_keywords = ['brand', 'primary', 'accent', 'logo', 'corporate']
        name_lower = semantic_name.lower()
        
        for keyword in brand_keywords:
            if keyword in name_lower:
                return 9.0
        
        return 5.0
    
    def _calculate_accessibility_impact(self, element_type: DesignElementType) -> float:
        """Calculate accessibility impact score."""
        high_impact_types = [DesignElementType.COLOR, DesignElementType.FONT, DesignElementType.TEXT_FORMAT]
        
        if element_type in high_impact_types:
            return 8.0
        
        return 3.0
    
    def _deduplicate_elements(self, elements: List[DesignElement]) -> List[DesignElement]:
        """Remove duplicate elements based on xpath and value."""
        seen = set()
        unique_elements = []
        
        for element in elements:
            key = (element.xpath_expression, element.current_value, element.file_location)
            if key not in seen:
                seen.add(key)
                unique_elements.append(element)
        
        return unique_elements
    
    def _enhance_element_metadata(self, elements: List[DesignElement], 
                                 file_path: str) -> List[DesignElement]:
        """Enhance elements with additional metadata."""
        for element in elements:
            element.metadata.update({
                'file_size': len(str(element.current_value)),
                'discovery_timestamp': str(self.context.processing_stats.get('start_time', '')),
                'file_type': self._determine_file_type(file_path)
            })
        
        return elements
    
    # Pattern definitions for different file types
    
    def _get_powerpoint_theme_patterns(self) -> List[Dict[str, Any]]:
        """Get PowerPoint theme discovery patterns"""
        return [
            {
                'xpath': '//a:srgbClr',
                'element_type': DesignElementType.COLOR,
                'value_attribute': 'val',
                'semantic_name_pattern': r'([a-fA-F0-9]{6})',
                'is_customizable': True
            },
            {
                'xpath': '//a:schemeClr',
                'element_type': DesignElementType.COLOR,
                'value_attribute': 'val',
                'semantic_name_pattern': r'([a-zA-Z0-9]+)',
                'is_customizable': True
            },
            {
                'xpath': '//a:latin',
                'element_type': DesignElementType.FONT,
                'value_attribute': 'typeface',
                'semantic_name_pattern': r'majorFont|minorFont|([a-zA-Z]+)',
                'is_customizable': True
            },
            {
                'xpath': '//a:gradFill',
                'element_type': DesignElementType.GRADIENT,
                'semantic_name_pattern': r'gradient(\d+)',
                'is_customizable': True
            },
            {
                'xpath': '//a:outerShdw',
                'element_type': DesignElementType.EFFECT,
                'semantic_name_pattern': r'shadow(\d+)',
                'is_customizable': True
            }
        ]
    
    def _get_powerpoint_slide_master_patterns(self) -> List[Dict[str, Any]]:
        """Get PowerPoint slide master discovery patterns"""
        return [
            {
                'xpath': '//a:solidFill/a:schemeClr',
                'element_type': DesignElementType.COLOR,
                'value_attribute': 'val',
                'is_customizable': True
            },
            {
                'xpath': '//a:rPr',
                'element_type': DesignElementType.TEXT_FORMAT,
                'semantic_name_pattern': r'textFormat(\d+)',
                'is_customizable': True
            },
            {
                'xpath': '//a:xfrm',
                'element_type': DesignElementType.DIMENSION,
                'semantic_name_pattern': r'dimension(\d+)',
                'is_customizable': False  # Usually not directly customizable
            }
        ]
    
    def _get_word_styles_patterns(self) -> List[Dict[str, Any]]:
        """Get Word styles discovery patterns"""
        return [
            {
                'xpath': '//w:color',
                'element_type': DesignElementType.COLOR,
                'value_attribute': 'val',
                'is_customizable': True
            },
            {
                'xpath': '//w:rFonts',
                'element_type': DesignElementType.FONT,
                'value_attribute': 'ascii',
                'is_customizable': True
            },
            {
                'xpath': '//w:sz',
                'element_type': DesignElementType.TEXT_FORMAT,
                'value_attribute': 'val',
                'is_customizable': True
            }
        ]
    
    def _get_word_document_patterns(self) -> List[Dict[str, Any]]:
        """Get Word document discovery patterns"""
        return [
            {
                'xpath': '//w:pStyle',
                'element_type': DesignElementType.TEXT_FORMAT,
                'value_attribute': 'val',
                'is_customizable': True
            }
        ]
    
    def _get_excel_styles_patterns(self) -> List[Dict[str, Any]]:
        """Get Excel styles discovery patterns"""
        return [
            {
                'xpath': '//color',
                'element_type': DesignElementType.COLOR,
                'value_attribute': 'theme',
                'is_customizable': True
            },
            {
                'xpath': '//name',
                'element_type': DesignElementType.FONT,
                'value_attribute': 'val',
                'is_customizable': True
            },
            {
                'xpath': '//patternFill',
                'element_type': DesignElementType.FILL,
                'value_attribute': 'patternType',
                'is_customizable': True
            },
            {
                'xpath': '//border',
                'element_type': DesignElementType.BORDER,
                'semantic_name_pattern': r'border(\d+)',
                'is_customizable': True
            }
        ]
    
    def _get_excel_workbook_patterns(self) -> List[Dict[str, Any]]:
        """Get Excel workbook discovery patterns"""
        return [
            {
                'xpath': '//cellStyle',
                'element_type': DesignElementType.TEXT_FORMAT,
                'value_attribute': 'name',
                'is_customizable': True
            }
        ]