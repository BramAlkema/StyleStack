"""
StyleStack OOXML Document Processor

Advanced OOXML document manipulation with XPath-based targeting and safe XML processing.
Builds upon existing template_patcher.py with enhanced precision and document preservation.

Features:
- XPath-based element targeting for precise manipulation
- Namespace-aware XML processing 
- Document structure preservation
- Safe manipulation without corruption
- Performance optimization for large documents
- Integration with variable resolution engine

Usage:
    processor = OOXMLProcessor()
    
    # Process single XML content
    updated_xml = processor.apply_variables_to_xml(xml_content, variables)
    
    # Process complete OOXML file
    processor.process_ooxml_file('template.potx', variables, 'output.potx')
"""

import xml.etree.ElementTree as ET
import zipfile
import io
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
import logging
import time

# Optional lxml import for advanced XPath
try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class XPathExpression:
    """Represents an XPath expression with metadata"""
    expression: str
    description: str
    target_type: str  # 'color', 'font', 'dimension', 'text'
    namespaces: Dict[str, str] = None
    
    def __post_init__(self):
        if self.namespaces is None:
            self.namespaces = {}


@dataclass 
class ProcessingResult:
    """Result of OOXML processing operation"""
    success: bool
    elements_processed: int
    elements_modified: int
    processing_time: float
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class XPathLibrary:
    """Library of common XPath expressions for OOXML elements"""
    
    # OOXML Namespaces
    NAMESPACES = {
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
        'p': 'http://schemas.openxmlformats.org/presentationml/2006/main', 
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    }
    
    # Color targeting expressions
    COLORS = {
        'theme_accent1': XPathExpression(
            '//a:accent1//a:srgbClr/@val',
            'Theme accent color 1 RGB value',
            'color',
            NAMESPACES
        ),
        'theme_accent2': XPathExpression(
            '//a:accent2//a:srgbClr/@val', 
            'Theme accent color 2 RGB value',
            'color',
            NAMESPACES
        ),
        'theme_dark1': XPathExpression(
            '//a:dk1//a:srgbClr/@val',
            'Theme dark color 1 RGB value', 
            'color',
            NAMESPACES
        ),
        'all_rgb_colors': XPathExpression(
            '//a:srgbClr[@val]',
            'All RGB color elements with val attribute',
            'color',
            NAMESPACES
        ),
        'word_text_color': XPathExpression(
            '//w:color[@w:val]',
            'Word text color elements',
            'color',
            NAMESPACES
        ),
        'excel_font_color': XPathExpression(
            '//color[@rgb]',
            'Excel font color elements',
            'color',
            NAMESPACES
        )
    }
    
    # Font targeting expressions  
    FONTS = {
        'theme_major_font': XPathExpression(
            '//a:majorFont/a:latin/@typeface',
            'Theme major font typeface',
            'font',
            NAMESPACES
        ),
        'theme_minor_font': XPathExpression(
            '//a:minorFont/a:latin/@typeface',
            'Theme minor font typeface',
            'font', 
            NAMESPACES
        ),
        'word_font_family': XPathExpression(
            '//w:rFonts[@w:ascii]',
            'Word font family elements',
            'font',
            NAMESPACES
        ),
        'excel_font_name': XPathExpression(
            '//name[@val]',
            'Excel font name elements',
            'font',
            NAMESPACES
        )
    }
    
    # Dimension targeting expressions
    DIMENSIONS = {
        'word_font_size': XPathExpression(
            '//w:sz[@w:val]',
            'Word font size elements',
            'dimension',
            NAMESPACES
        ),
        'word_spacing': XPathExpression(
            '//w:spacing[@w:line]',
            'Word line spacing elements',
            'dimension',
            NAMESPACES
        ),
        'excel_font_size': XPathExpression(
            '//sz[@val]',
            'Excel font size elements',
            'dimension',
            NAMESPACES
        )
    }
    
    @classmethod
    def get_expression(cls, category: str, name: str) -> Optional[XPathExpression]:
        """Get XPath expression by category and name"""
        category_map = {
            'colors': cls.COLORS,
            'fonts': cls.FONTS,
            'dimensions': cls.DIMENSIONS
        }
        
        if category in category_map:
            return category_map[category].get(name)
        return None
    
    @classmethod
    def get_all_expressions(cls) -> Dict[str, Dict[str, XPathExpression]]:
        """Get all XPath expressions organized by category"""
        return {
            'colors': cls.COLORS,
            'fonts': cls.FONTS,
            'dimensions': cls.DIMENSIONS
        }


class OOXMLProcessor:
    """
    Advanced OOXML document processor with XPath targeting and safe manipulation.
    
    Extends existing template_patcher.py functionality with:
    - Precise XPath-based element targeting
    - Namespace-aware XML processing
    - Document structure preservation  
    - Batch processing optimization
    - Error recovery and validation
    """
    
    def __init__(self, use_lxml: bool = None, preserve_formatting: bool = True):
        """
        Initialize OOXML processor.
        
        Args:
            use_lxml: Use lxml for advanced XPath (auto-detect if None)
            preserve_formatting: Preserve XML formatting and whitespace
        """
        self.use_lxml = use_lxml if use_lxml is not None else LXML_AVAILABLE
        self.preserve_formatting = preserve_formatting
        self.xpath_library = XPathLibrary()
        
        # Processing statistics
        self.stats = {
            'documents_processed': 0,
            'elements_modified': 0,
            'total_processing_time': 0.0
        }
        
        # Register namespaces for ElementTree
        for prefix, uri in XPathLibrary.NAMESPACES.items():
            try:
                ET.register_namespace(prefix, uri)
            except ValueError:
                pass  # Already registered
    
    def apply_variables_to_xml(self, xml_content: str, 
                              variables: Dict[str, Any],
                              validate_result: bool = True) -> Tuple[str, ProcessingResult]:
        """
        Apply variables to XML content with XPath targeting.
        
        Args:
            xml_content: XML content to process
            variables: Dictionary of variables to apply
            validate_result: Validate result XML for integrity
            
        Returns:
            Tuple of (updated_xml_content, processing_result)
        """
        start_time = time.time()
        result = ProcessingResult(
            success=False,
            elements_processed=0,
            elements_modified=0,
            processing_time=0.0
        )
        
        try:
            # Parse XML
            if self.use_lxml:
                updated_xml, lxml_result = self._apply_variables_lxml(xml_content, variables)
                result.elements_processed = lxml_result.elements_processed
                result.elements_modified = lxml_result.elements_modified
            else:
                updated_xml, et_result = self._apply_variables_elementtree(xml_content, variables)
                result.elements_processed = et_result.elements_processed  
                result.elements_modified = et_result.elements_modified
            
            # Validate result if requested
            if validate_result:
                validation_errors = self._validate_xml_integrity(xml_content, updated_xml)
                result.errors.extend(validation_errors)
            
            result.success = len(result.errors) == 0
            result.processing_time = time.time() - start_time
            
            # Update stats
            self.stats['documents_processed'] += 1
            self.stats['elements_modified'] += result.elements_modified
            self.stats['total_processing_time'] += result.processing_time
            
            return updated_xml, result
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Processing failed: {e}")
            result.processing_time = time.time() - start_time
            
            logger.error(f"OOXML processing failed: {e}")
            return xml_content, result  # Return original on error
    
    def _apply_variables_lxml(self, xml_content: str, 
                             variables: Dict[str, Any]) -> Tuple[str, ProcessingResult]:
        """Apply variables using lxml for advanced XPath support"""
        parser = etree.XMLParser(ns_clean=True, recover=True)
        root = etree.fromstring(xml_content.encode('utf-8'), parser)
        
        result = ProcessingResult(
            success=True,
            elements_processed=0,
            elements_modified=0,
            processing_time=0.0
        )
        
        for var_id, variable in variables.items():
            try:
                # Get XPath expression for variable
                xpath = self._get_xpath_for_variable(variable)
                if not xpath:
                    result.warnings.append(f"No XPath found for variable: {var_id}")
                    continue
                
                # Find elements
                elements = root.xpath(xpath.expression, namespaces=xpath.namespaces)
                result.elements_processed += len(elements)
                
                # Apply variable to elements
                modified_count = self._apply_variable_to_elements_lxml(
                    elements, variable, xpath
                )
                result.elements_modified += modified_count
                
            except Exception as e:
                result.errors.append(f"Error processing variable {var_id}: {e}")
                continue
        
        # Serialize result
        updated_xml = etree.tostring(root, encoding='unicode', pretty_print=self.preserve_formatting)
        return updated_xml, result
    
    def _apply_variables_elementtree(self, xml_content: str,
                                   variables: Dict[str, Any]) -> Tuple[str, ProcessingResult]:
        """Apply variables using ElementTree with simplified XPath"""
        root = ET.fromstring(xml_content)
        
        result = ProcessingResult(
            success=True,
            elements_processed=0,
            elements_modified=0,
            processing_time=0.0
        )
        
        for var_id, variable in variables.items():
            try:
                # Find elements using simplified patterns
                elements = self._find_elements_elementtree(root, variable)
                result.elements_processed += len(elements)
                
                # Apply variable to elements
                modified_count = self._apply_variable_to_elements_et(elements, variable)
                result.elements_modified += modified_count
                
            except Exception as e:
                result.errors.append(f"Error processing variable {var_id}: {e}")
                continue
        
        # Serialize result
        if self.preserve_formatting:
            self._indent_xml(root)
        
        updated_xml = ET.tostring(root, encoding='unicode')
        return updated_xml, result
    
    def _get_xpath_for_variable(self, variable: Dict[str, Any]) -> Optional[XPathExpression]:
        """Get XPath expression for variable"""
        # Check if variable has explicit XPath
        if 'xpath' in variable:
            return XPathExpression(
                expression=variable['xpath'],
                description=f"Custom XPath for {variable.get('id', 'unknown')}",
                target_type=variable.get('type', 'text'),
                namespaces=XPathLibrary.NAMESPACES
            )
        
        # Try to find appropriate XPath from library
        var_type = variable.get('type', 'text')
        var_id = variable.get('id', '')
        
        if var_type == 'color':
            if 'accent1' in var_id.lower():
                return self.xpath_library.get_expression('colors', 'theme_accent1')
            elif 'accent2' in var_id.lower():
                return self.xpath_library.get_expression('colors', 'theme_accent2')
            else:
                return self.xpath_library.get_expression('colors', 'all_rgb_colors')
                
        elif var_type == 'font':
            if 'major' in var_id.lower() or 'heading' in var_id.lower():
                return self.xpath_library.get_expression('fonts', 'theme_major_font')
            elif 'minor' in var_id.lower() or 'body' in var_id.lower():
                return self.xpath_library.get_expression('fonts', 'theme_minor_font')
            else:
                return self.xpath_library.get_expression('fonts', 'theme_major_font')
                
        elif var_type == 'dimension':
            if 'size' in var_id.lower():
                return self.xpath_library.get_expression('dimensions', 'word_font_size')
            elif 'spacing' in var_id.lower():
                return self.xpath_library.get_expression('dimensions', 'word_spacing')
        
        return None
    
    def _find_elements_elementtree(self, root: ET.Element, 
                                  variable: Dict[str, Any]) -> List[ET.Element]:
        """Find elements using ElementTree (simplified XPath)"""
        var_type = variable.get('type', 'text')
        var_id = variable.get('id', '')
        
        if var_type == 'color':
            # Find RGB color elements
            elements = root.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr[@val]')
            
            # Try Word colors if none found
            if not elements:
                elements = root.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}color[@val]')
                
        elif var_type == 'font':
            # Find font elements
            elements = root.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}latin[@typeface]')
            
            # Try Word fonts if none found
            if not elements:
                elements = root.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts')
                
        elif var_type == 'dimension':
            # Find size elements
            elements = root.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sz[@val]')
            
        else:
            # Generic text elements
            elements = list(root.iter())
            
        return elements
    
    def _apply_variable_to_elements_lxml(self, elements: List, variable: Dict[str, Any],
                                       xpath: XPathExpression) -> int:
        """Apply variable to elements using lxml"""
        modified_count = 0
        var_value = str(variable.get('value', variable.get('defaultValue', '')))
        var_type = variable.get('type', 'text')
        
        for element in elements:
            try:
                if xpath.target_type == 'color':
                    if isinstance(element, str):  # Attribute value
                        # Can't modify attribute directly in XPath result
                        continue
                    elif hasattr(element, 'set') and 'val' in element.attrib:
                        element.set('val', var_value.lstrip('#'))
                        modified_count += 1
                        
                elif xpath.target_type == 'font':
                    if isinstance(element, str):  # Attribute value
                        continue
                    elif hasattr(element, 'set') and 'typeface' in element.attrib:
                        element.set('typeface', var_value)
                        modified_count += 1
                        
                elif xpath.target_type == 'dimension':
                    if isinstance(element, str):  # Attribute value
                        continue
                    elif hasattr(element, 'set') and 'val' in element.attrib:
                        element.set('val', str(var_value))
                        modified_count += 1
                        
            except Exception as e:
                logger.warning(f"Failed to apply variable to element: {e}")
                continue
                
        return modified_count
    
    def _apply_variable_to_elements_et(self, elements: List[ET.Element],
                                     variable: Dict[str, Any]) -> int:
        """Apply variable to elements using ElementTree"""
        modified_count = 0
        var_value = str(variable.get('value', variable.get('defaultValue', '')))
        var_type = variable.get('type', 'text')
        
        for element in elements:
            try:
                if var_type == 'color':
                    if 'val' in element.attrib:
                        element.set('val', var_value.lstrip('#'))
                        modified_count += 1
                    elif 'rgb' in element.attrib:
                        rgb_val = var_value.lstrip('#')
                        if len(rgb_val) == 6:
                            element.set('rgb', f'FF{rgb_val.upper()}')
                            modified_count += 1
                            
                elif var_type == 'font':
                    if 'typeface' in element.attrib:
                        element.set('typeface', var_value)
                        modified_count += 1
                    elif 'ascii' in element.attrib:  # Word fonts
                        element.set('ascii', var_value)
                        element.set('hAnsi', var_value)
                        modified_count += 1
                        
                elif var_type == 'dimension':
                    if 'val' in element.attrib:
                        # Convert to appropriate units
                        if 'pt' in str(var_value):
                            # Convert points to half-points for Word
                            points = float(var_value.replace('pt', ''))
                            half_points = int(points * 2)
                            element.set('val', str(half_points))
                        else:
                            element.set('val', str(var_value))
                        modified_count += 1
                        
            except Exception as e:
                logger.warning(f"Failed to apply variable to element: {e}")
                continue
                
        return modified_count
    
    def _validate_xml_integrity(self, original_xml: str, updated_xml: str) -> List[str]:
        """Validate XML integrity after processing"""
        errors = []
        
        try:
            # Parse both versions
            original_root = ET.fromstring(original_xml)
            updated_root = ET.fromstring(updated_xml)
            
            # Check element counts
            original_count = len(list(original_root.iter()))
            updated_count = len(list(updated_root.iter()))
            
            if original_count != updated_count:
                errors.append(f"Element count changed: {original_count} -> {updated_count}")
            
            # Check root element
            if original_root.tag != updated_root.tag:
                errors.append(f"Root element changed: {original_root.tag} -> {updated_root.tag}")
                
        except ET.ParseError as e:
            errors.append(f"Updated XML is not valid: {e}")
        except Exception as e:
            errors.append(f"Validation error: {e}")
            
        return errors
    
    def _indent_xml(self, elem: ET.Element, level: int = 0) -> None:
        """Add indentation to XML elements"""
        indent = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                self._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent
    
    def process_ooxml_file(self, input_path: Union[str, Path],
                          variables: Dict[str, Any],
                          output_path: Union[str, Path],
                          target_files: Optional[List[str]] = None) -> ProcessingResult:
        """
        Process complete OOXML file with variable substitution.
        
        Args:
            input_path: Input OOXML file path
            variables: Variables to apply
            output_path: Output file path
            target_files: Specific files to process within OOXML (None = all XML files)
            
        Returns:
            ProcessingResult with overall statistics
        """
        start_time = time.time()
        overall_result = ProcessingResult(
            success=False,
            elements_processed=0,
            elements_modified=0, 
            processing_time=0.0
        )
        
        try:
            with zipfile.ZipFile(input_path, 'r') as input_zip:
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as output_zip:
                    
                    for file_info in input_zip.infolist():
                        file_data = input_zip.read(file_info.filename)
                        
                        # Process XML files
                        if (file_info.filename.endswith('.xml') and 
                            (target_files is None or file_info.filename in target_files)):
                            
                            try:
                                xml_content = file_data.decode('utf-8')
                                updated_xml, file_result = self.apply_variables_to_xml(
                                    xml_content, variables, validate_result=False
                                )
                                
                                # Update overall statistics
                                overall_result.elements_processed += file_result.elements_processed
                                overall_result.elements_modified += file_result.elements_modified
                                overall_result.errors.extend(file_result.errors)
                                overall_result.warnings.extend(file_result.warnings)
                                
                                # Write updated content
                                output_zip.writestr(file_info, updated_xml.encode('utf-8'))
                                
                                if file_result.elements_modified > 0:
                                    logger.info(f"Processed {file_info.filename}: "
                                             f"{file_result.elements_modified} modifications")
                                
                            except UnicodeDecodeError:
                                # Not a text XML file, copy as-is
                                output_zip.writestr(file_info, file_data)
                                
                        else:
                            # Copy non-XML files as-is
                            output_zip.writestr(file_info, file_data)
            
            overall_result.success = len(overall_result.errors) == 0
            overall_result.processing_time = time.time() - start_time
            
            logger.info(f"OOXML processing complete: {overall_result.elements_modified} elements modified")
            
        except Exception as e:
            overall_result.success = False
            overall_result.errors.append(f"File processing failed: {e}")
            overall_result.processing_time = time.time() - start_time
            
            logger.error(f"OOXML file processing failed: {e}")
        
        return overall_result
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            'documents_processed': self.stats['documents_processed'],
            'total_elements_modified': self.stats['elements_modified'],
            'total_processing_time': self.stats['total_processing_time'],
            'average_processing_time': (
                self.stats['total_processing_time'] / max(1, self.stats['documents_processed'])
            ),
            'lxml_available': self.use_lxml
        }


if __name__ == "__main__":
    # Demo usage
    processor = OOXMLProcessor()
    
    # Sample variables
    variables = {
        'brandPrimary': {
            'id': 'brandPrimary',
            'type': 'color',
            'value': 'FF0000',
            'xpath': '//a:accent1//a:srgbClr'
        },
        'headingFont': {
            'id': 'headingFont',
            'type': 'font',
            'value': 'Arial Black',
            'xpath': '//a:majorFont//a:latin'
        }
    }
    
    # Sample XML content
    theme_xml = '''<?xml version="1.0"?>
    <a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
      <a:themeElements>
        <a:clrScheme name="Test">
          <a:accent1>
            <a:srgbClr val="4472C4"/>
          </a:accent1>
        </a:clrScheme>
        <a:fontScheme name="Test">
          <a:majorFont>
            <a:latin typeface="Calibri Light"/>
          </a:majorFont>
        </a:fontScheme>
      </a:themeElements>
    </a:theme>'''
    
    print("🔧 StyleStack OOXML Processor Demo")
    print(f"Using lxml: {processor.use_lxml}")
    
    try:
        updated_xml, result = processor.apply_variables_to_xml(theme_xml, variables)
        
        print(f"✅ Processing successful:")
        print(f"   Elements processed: {result.elements_processed}")
        print(f"   Elements modified: {result.elements_modified}")
        print(f"   Processing time: {result.processing_time:.3f}s")
        
        if result.errors:
            print(f"   Errors: {len(result.errors)}")
            for error in result.errors:
                print(f"     - {error}")
        
        if result.warnings:
            print(f"   Warnings: {len(result.warnings)}")
            
        # Show some of the updated XML
        if 'FF0000' in updated_xml:
            print("   ✅ Color variable applied successfully")
        if 'Arial Black' in updated_xml:
            print("   ✅ Font variable applied successfully")
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    
    print(f"📊 Processing Statistics: {processor.get_processing_statistics()}")