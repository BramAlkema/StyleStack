"""XML parsing, normalization, and semantic comparison for OOXML documents."""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from lxml import etree
import xml.etree.ElementTree as ET
from ..core.exceptions import AnalysisError


@dataclass
class XMLDifference:
    """Represents a difference between two XML elements."""
    diff_type: str  # 'element_added', 'element_removed', 'attribute_changed', 'text_content'
    xpath: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    element_name: Optional[str] = None
    attribute_name: Optional[str] = None


@dataclass
class ComparisonResult:
    """Result of semantic XML comparison."""
    are_semantically_equal: bool
    similarity_score: float  # 0.0 to 1.0
    differences: List[XMLDifference]
    total_elements: int
    changed_elements: int


class XMLNormalizer:
    """Normalizes XML for consistent comparison."""
    
    def normalize(self, xml_content: bytes) -> bytes:
        """
        Apply complete normalization pipeline.
        
        Args:
            xml_content: Raw XML content
            
        Returns:
            Normalized XML content
        """
        try:
            # Parse and normalize namespaces
            normalized = self.normalize_namespaces(xml_content)
            
            # Normalize attributes
            normalized = self.normalize_attributes(normalized)
            
            # Normalize whitespace
            normalized = self.normalize_whitespace(normalized)
            
            # Format consistently
            normalized = self.format_consistently(normalized)
            
            return normalized
        except Exception as e:
            raise AnalysisError(f"Failed to normalize XML: {e}")
    
    def normalize_namespaces(self, xml_content: bytes) -> bytes:
        """Normalize namespace prefixes for consistent comparison."""
        try:
            # Parse with lxml to handle namespaces properly
            parser = etree.XMLParser(strip_cdata=False)
            root = etree.fromstring(xml_content, parser)
            
            # Get namespace map and create consistent prefixes
            nsmap = root.nsmap
            if nsmap:
                # Sort namespaces by URI for consistency
                sorted_namespaces = sorted(nsmap.items(), key=lambda x: x[1] or '')
                
                # Create new consistent prefix mapping
                prefix_map = {}
                for i, (prefix, uri) in enumerate(sorted_namespaces):
                    if uri:  # Skip None namespace
                        new_prefix = f"ns{i}" if prefix is None else prefix
                        prefix_map[uri] = new_prefix
                
                # Apply consistent prefixes
                self._apply_namespace_prefixes(root, prefix_map)
            
            return etree.tostring(root, encoding='utf-8')
        except Exception:
            # Fallback to returning original content
            return xml_content
    
    def _apply_namespace_prefixes(self, element, prefix_map: Dict[str, str]):
        """Apply consistent namespace prefixes to element tree."""
        # This is a simplified implementation
        # In practice, you'd need to rebuild the tree with new prefixes
        pass
    
    def normalize_attributes(self, xml_content: bytes) -> bytes:
        """Sort attributes alphabetically for consistent ordering."""
        try:
            root = etree.fromstring(xml_content)
            self._sort_attributes_recursive(root)
            return etree.tostring(root, encoding='utf-8')
        except Exception:
            return xml_content
    
    def _sort_attributes_recursive(self, element):
        """Recursively sort attributes in element tree."""
        # Sort current element's attributes
        if element.attrib:
            sorted_attrs = sorted(element.attrib.items())
            # Store children and text before clearing
            children = list(element)
            text = element.text
            tail = element.tail
            
            element.clear()
            element.attrib.update(sorted_attrs)
            
            # Restore text and children
            element.text = text
            element.tail = tail
            for child in children:
                element.append(child)
        
        # Recurse to children
        for child in element:
            self._sort_attributes_recursive(child)
    
    def normalize_whitespace(self, xml_content: bytes) -> bytes:
        """Normalize whitespace while preserving meaningful content."""
        try:
            # Convert to string for regex processing
            content = xml_content.decode('utf-8')
            
            # Normalize multiple spaces in text content (but not in attributes)
            # This is a simplified approach - production code would need more sophisticated handling
            content = re.sub(r'>\s+<', '><', content)  # Remove whitespace between tags
            content = re.sub(r'\s+', ' ', content)     # Normalize internal whitespace
            
            return content.encode('utf-8')
        except Exception:
            return xml_content
    
    def format_consistently(self, xml_content: bytes) -> bytes:
        """Apply consistent formatting with indentation."""
        try:
            root = etree.fromstring(xml_content)
            # Use lxml's pretty print for consistent formatting
            return etree.tostring(root, encoding='utf-8', pretty_print=True)
        except Exception:
            return xml_content


class SemanticComparator:
    """Compares XML documents for semantic differences."""
    
    def __init__(self):
        self.normalizer = XMLNormalizer()
    
    def compare(self, xml1: bytes, xml2: bytes) -> ComparisonResult:
        """
        Compare two XML documents semantically.
        
        Args:
            xml1: First XML document
            xml2: Second XML document
            
        Returns:
            Comparison result with differences and similarity score
        """
        try:
            # Normalize both documents
            norm1 = self.normalizer.normalize(xml1)
            norm2 = self.normalizer.normalize(xml2)
            
            # Parse normalized documents
            root1 = etree.fromstring(norm1)
            root2 = etree.fromstring(norm2)
            
            # Find differences
            differences = self._find_differences(root1, root2)
            
            # Calculate similarity
            total_elements = self._count_elements(root1)
            changed_elements = len([d for d in differences 
                                  if d.diff_type in ['element_added', 'element_removed', 'text_content']])
            
            similarity_score = self._calculate_similarity(total_elements, len(differences))
            are_equal = len(differences) == 0
            
            return ComparisonResult(
                are_semantically_equal=are_equal,
                similarity_score=similarity_score,
                differences=differences,
                total_elements=total_elements,
                changed_elements=changed_elements
            )
        except Exception as e:
            raise AnalysisError(f"Failed to compare XML documents: {e}")
    
    def _find_differences(self, root1, root2, xpath_prefix="") -> List[XMLDifference]:
        """Find differences between two XML element trees."""
        differences = []
        
        # Compare element names
        if root1.tag != root2.tag:
            differences.append(XMLDifference(
                diff_type='element_changed',
                xpath=xpath_prefix or '/',
                old_value=root1.tag,
                new_value=root2.tag,
                element_name=root1.tag
            ))
        
        # Compare attributes
        attrs1 = root1.attrib
        attrs2 = root2.attrib
        
        for attr_name in set(attrs1.keys()) | set(attrs2.keys()):
            if attr_name in attrs1 and attr_name in attrs2:
                if attrs1[attr_name] != attrs2[attr_name]:
                    differences.append(XMLDifference(
                        diff_type='attribute_changed',
                        xpath=f"{xpath_prefix}/@{attr_name}",
                        old_value=attrs1[attr_name],
                        new_value=attrs2[attr_name],
                        attribute_name=attr_name
                    ))
            elif attr_name in attrs1:
                differences.append(XMLDifference(
                    diff_type='attribute_removed',
                    xpath=f"{xpath_prefix}/@{attr_name}",
                    old_value=attrs1[attr_name],
                    attribute_name=attr_name
                ))
            else:
                differences.append(XMLDifference(
                    diff_type='attribute_added',
                    xpath=f"{xpath_prefix}/@{attr_name}",
                    new_value=attrs2[attr_name],
                    attribute_name=attr_name
                ))
        
        # Compare text content
        text1 = (root1.text or '').strip()
        text2 = (root2.text or '').strip()
        if text1 != text2:
            differences.append(XMLDifference(
                diff_type='text_content',
                xpath=xpath_prefix + '/text()',
                old_value=text1,
                new_value=text2
            ))
        
        # Compare children
        children1 = list(root1)
        children2 = list(root2)
        
        # Simple child comparison - could be more sophisticated
        max_children = max(len(children1), len(children2))
        
        for i in range(max_children):
            child_xpath = f"{xpath_prefix}/{root1.tag}[{i+1}]"
            
            if i < len(children1) and i < len(children2):
                # Compare existing children recursively
                child_diffs = self._find_differences(children1[i], children2[i], child_xpath)
                differences.extend(child_diffs)
            elif i < len(children1):
                # Child removed
                differences.append(XMLDifference(
                    diff_type='element_removed',
                    xpath=child_xpath,
                    old_value=children1[i].tag,
                    element_name=children1[i].tag
                ))
            else:
                # Child added
                differences.append(XMLDifference(
                    diff_type='element_added',
                    xpath=child_xpath,
                    new_value=children2[i].tag,
                    element_name=children2[i].tag
                ))
        
        return differences
    
    def _count_elements(self, root) -> int:
        """Count total number of elements in tree."""
        count = 1  # Count self
        for child in root:
            count += self._count_elements(child)
        return count
    
    def _calculate_similarity(self, total_elements: int, num_differences: int) -> float:
        """Calculate similarity score based on differences."""
        if total_elements == 0:
            return 1.0
        
        # Simple similarity calculation
        similarity = 1.0 - (num_differences / max(total_elements, 1))
        return max(0.0, min(1.0, similarity))


class OOXMLParser:
    """OOXML-specific parsing capabilities."""
    
    def parse_word_document(self, document_xml: bytes) -> Dict[str, Any]:
        """Parse Word document XML into structured data."""
        try:
            root = etree.fromstring(document_xml)
            
            # Extract paragraphs
            paragraphs = []
            
            # Find body element (handle namespaces)
            body = self._find_element_with_namespace(root, 'body')
            if body is not None:
                # Find all paragraph elements
                paragraph_elements = self._find_elements_with_namespace(body, 'p')
                
                for p_elem in paragraph_elements:
                    paragraph = self._parse_word_paragraph(p_elem)
                    paragraphs.append(paragraph)
            
            return {
                'document_type': 'word',
                'paragraphs': paragraphs
            }
        except Exception as e:
            raise AnalysisError(f"Invalid XML: {e}")
    
    def _parse_word_paragraph(self, p_elem) -> Dict[str, Any]:
        """Parse a Word paragraph element."""
        paragraph = {
            'style': None,
            'runs': []
        }
        
        # Extract paragraph style
        ppr = self._find_element_with_namespace(p_elem, 'pPr')
        if ppr is not None:
            pstyle = self._find_element_with_namespace(ppr, 'pStyle')
            if pstyle is not None:
                paragraph['style'] = self._get_attr_with_namespace(pstyle, 'val')
        
        # Extract runs
        run_elements = self._find_elements_with_namespace(p_elem, 'r')
        for r_elem in run_elements:
            run = self._parse_word_run(r_elem)
            paragraph['runs'].append(run)
        
        return paragraph
    
    def _parse_word_run(self, r_elem) -> Dict[str, Any]:
        """Parse a Word run element."""
        run = {
            'text': '',
            'bold': False,
            'color': None
        }
        
        # Extract run properties
        rpr = self._find_element_with_namespace(r_elem, 'rPr')
        if rpr is not None:
            # Check for bold
            bold_elem = self._find_element_with_namespace(rpr, 'b')
            run['bold'] = bold_elem is not None
            
            # Check for color
            color_elem = self._find_element_with_namespace(rpr, 'color')
            if color_elem is not None:
                run['color'] = self._get_attr_with_namespace(color_elem, 'val')
        
        # Extract text
        text_elem = self._find_element_with_namespace(r_elem, 't')
        if text_elem is not None and text_elem.text:
            run['text'] = text_elem.text
        
        return run
    
    def parse_powerpoint_slide(self, slide_xml: bytes) -> Dict[str, Any]:
        """Parse PowerPoint slide XML into structured data."""
        try:
            root = etree.fromstring(slide_xml)
            
            shapes = []
            
            # Find slide content
            csld = self._find_element_with_namespace(root, 'cSld')
            if csld is not None:
                sptree = self._find_element_with_namespace(csld, 'spTree')
                if sptree is not None:
                    # Find shape elements
                    shape_elements = self._find_elements_with_namespace(sptree, 'sp')
                    
                    for sp_elem in shape_elements:
                        shape = self._parse_powerpoint_shape(sp_elem)
                        shapes.append(shape)
            
            return {
                'document_type': 'powerpoint',
                'shapes': shapes
            }
        except Exception as e:
            raise AnalysisError(f"Invalid XML: {e}")
    
    def _parse_powerpoint_shape(self, sp_elem) -> Dict[str, Any]:
        """Parse a PowerPoint shape element."""
        shape = {
            'text_content': {'paragraphs': []}
        }
        
        # Find text body
        txbody = self._find_element_with_namespace(sp_elem, 'txBody')
        if txbody is not None:
            # Find paragraphs
            p_elements = self._find_elements_with_namespace(txbody, 'p')
            
            for p_elem in p_elements:
                paragraph = self._parse_powerpoint_paragraph(p_elem)
                shape['text_content']['paragraphs'].append(paragraph)
        
        return shape
    
    def _parse_powerpoint_paragraph(self, p_elem) -> Dict[str, Any]:
        """Parse a PowerPoint paragraph element."""
        paragraph = {'runs': []}
        
        # Find run elements (using drawing namespace)
        r_elements = self._find_elements_with_namespace(p_elem, 'r')
        
        for r_elem in r_elements:
            run = self._parse_powerpoint_run(r_elem)
            paragraph['runs'].append(run)
        
        return paragraph
    
    def _parse_powerpoint_run(self, r_elem) -> Dict[str, Any]:
        """Parse a PowerPoint run element."""
        run = {
            'text': '',
            'color': None
        }
        
        # Extract run properties
        rpr = self._find_element_with_namespace(r_elem, 'rPr')
        if rpr is not None:
            # Check for color (solid fill)
            solidfill = self._find_element_with_namespace(rpr, 'solidFill')
            if solidfill is not None:
                srgbclr = self._find_element_with_namespace(solidfill, 'srgbClr')
                if srgbclr is not None:
                    run['color'] = srgbclr.get('val')
        
        # Extract text
        text_elem = self._find_element_with_namespace(r_elem, 't')
        if text_elem is not None and text_elem.text:
            run['text'] = text_elem.text
        
        return run
    
    def parse_excel_worksheet(self, worksheet_xml: bytes) -> Dict[str, Any]:
        """Parse Excel worksheet XML into structured data."""
        try:
            root = etree.fromstring(worksheet_xml)
            
            rows = []
            
            # Find sheet data
            sheetdata = self._find_element_with_namespace(root, 'sheetData')
            if sheetdata is not None:
                # Find row elements
                row_elements = self._find_elements_with_namespace(sheetdata, 'row')
                
                for row_elem in row_elements:
                    row = self._parse_excel_row(row_elem)
                    rows.append(row)
            
            return {
                'document_type': 'excel',
                'rows': rows
            }
        except Exception as e:
            raise AnalysisError(f"Invalid XML: {e}")
    
    def _parse_excel_row(self, row_elem) -> Dict[str, Any]:
        """Parse an Excel row element."""
        row = {
            'row_number': int(row_elem.get('r', 0)),
            'cells': []
        }
        
        # Find cell elements
        cell_elements = self._find_elements_with_namespace(row_elem, 'c')
        
        for c_elem in cell_elements:
            cell = self._parse_excel_cell(c_elem)
            row['cells'].append(cell)
        
        return row
    
    def _parse_excel_cell(self, c_elem) -> Dict[str, Any]:
        """Parse an Excel cell element."""
        cell = {
            'reference': c_elem.get('r', ''),
            'style_index': c_elem.get('s'),
            'data_type': c_elem.get('t'),
            'value': '',
            'formula': None
        }
        
        # Convert style index to int if present
        if cell['style_index']:
            cell['style_index'] = int(cell['style_index'])
        
        # Extract formula
        f_elem = self._find_element_with_namespace(c_elem, 'f')
        if f_elem is not None and f_elem.text:
            cell['formula'] = f_elem.text
        
        # Extract value
        v_elem = self._find_element_with_namespace(c_elem, 'v')
        if v_elem is not None and v_elem.text:
            cell['value'] = v_elem.text
        
        return cell
    
    def extract_styles(self, styles_xml: bytes) -> Dict[str, Dict[str, Any]]:
        """Extract style information from styles XML."""
        try:
            root = etree.fromstring(styles_xml)
            styles = {}
            
            # Find style elements
            style_elements = self._find_elements_with_namespace(root, 'style')
            
            for style_elem in style_elements:
                style_id = self._get_attr_with_namespace(style_elem, 'styleId')
                if style_id:
                    style_data = self._parse_style_element(style_elem)
                    styles[style_id] = style_data
            
            return styles
        except Exception as e:
            raise AnalysisError(f"Invalid XML: {e}")
    
    def _parse_style_element(self, style_elem) -> Dict[str, Any]:
        """Parse a style element."""
        style = {
            'type': self._get_attr_with_namespace(style_elem, 'type'),
            'name': '',
            'paragraph_properties': {},
            'run_properties': {}
        }
        
        # Extract style name
        name_elem = self._find_element_with_namespace(style_elem, 'name')
        if name_elem is not None:
            style['name'] = self._get_attr_with_namespace(name_elem, 'val')
        
        # Extract paragraph properties
        ppr = self._find_element_with_namespace(style_elem, 'pPr')
        if ppr is not None:
            style['paragraph_properties'] = self._parse_paragraph_properties(ppr)
        
        # Extract run properties
        rpr = self._find_element_with_namespace(style_elem, 'rPr')
        if rpr is not None:
            style['run_properties'] = self._parse_run_properties(rpr)
        
        return style
    
    def _parse_paragraph_properties(self, ppr_elem) -> Dict[str, Any]:
        """Parse paragraph properties."""
        props = {}
        
        # Extract spacing
        spacing = self._find_element_with_namespace(ppr_elem, 'spacing')
        if spacing is not None:
            props['spacing_before'] = self._get_attr_with_namespace(spacing, 'before')
            props['spacing_after'] = self._get_attr_with_namespace(spacing, 'after')
        
        # Extract justification
        jc = self._find_element_with_namespace(ppr_elem, 'jc')
        if jc is not None:
            props['justification'] = self._get_attr_with_namespace(jc, 'val')
        
        return props
    
    def _parse_run_properties(self, rpr_elem) -> Dict[str, Any]:
        """Parse run properties."""
        props = {}
        
        # Extract fonts
        rfonts = self._find_element_with_namespace(rpr_elem, 'rFonts')
        if rfonts is not None:
            props['font_family'] = self._get_attr_with_namespace(rfonts, 'ascii')
        
        # Extract size
        sz = self._find_element_with_namespace(rpr_elem, 'sz')
        if sz is not None:
            props['font_size'] = self._get_attr_with_namespace(sz, 'val')
        
        # Extract color
        color = self._find_element_with_namespace(rpr_elem, 'color')
        if color is not None:
            props['color'] = self._get_attr_with_namespace(color, 'val')
        
        return props
    
    def _find_element_with_namespace(self, parent, local_name: str):
        """Find element handling namespaces."""
        # Try to find with any namespace
        for child in parent:
            if child.tag.endswith(f"}}{local_name}") or child.tag == local_name:
                return child
        return None
    
    def _find_elements_with_namespace(self, parent, local_name: str):
        """Find all elements with local name, handling namespaces."""
        elements = []
        for child in parent:
            if child.tag.endswith(f"}}{local_name}") or child.tag == local_name:
                elements.append(child)
        return elements
    
    def _get_namespaced_attr(self, local_name: str) -> str:
        """Get attribute name handling namespaces."""
        # For simplicity, return the local name - lxml handles namespace resolution
        return local_name
    
    def _get_attr_with_namespace(self, element, local_name: str) -> Optional[str]:
        """Get attribute value handling namespaces."""
        # Try different namespace variations
        for attr_name in element.attrib:
            if attr_name == local_name or attr_name.endswith(f"}}{local_name}"):
                return element.attrib[attr_name]
        return None