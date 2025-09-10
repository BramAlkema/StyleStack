#!/usr/bin/env python3
"""
OOXML Testing Fixtures

This module provides comprehensive fixtures for testing OOXML processing,
including sample OOXML documents, validation utilities, and test data generators.
"""


from typing import Any, Dict, List, Optional
import pytest
import tempfile
import shutil
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import Mock, MagicMock
import json


# OOXML Content Templates

POWERPOINT_PRESENTATION_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" 
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
                xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst>
    <p:sldMasterId id="2147483648" r:id="rId1"/>
  </p:sldMasterIdLst>
  <p:sldIdLst>
    <p:sldId id="256" r:id="rId2"/>
  </p:sldIdLst>
  <p:sldSz cx="9144000" cy="6858000"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>'''

POWERPOINT_SLIDE_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" 
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="2" name="Title 1"/>
          <p:cNvSpPr>
            <a:spLocks noGrp="1"/>
          </p:cNvSpPr>
          <p:nvPr>
            <p:ph type="ctrTitle"/>
          </p:nvPr>
        </p:nvSpPr>
        <p:spPr/>
        <p:txBody>
          <a:bodyPr/>
          <a:lstStyle/>
          <a:p>
            <a:r>
              <a:rPr lang="en-US" dirty="0" smtClean="0"/>
              <a:t>Sample Presentation Title</a:t>
            </a:r>
          </a:p>
        </p:txBody>
      </p:sp>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr>
    <a:masterClrMapping/>
  </p:clrMapOvr>
</p:sld>'''

WORD_DOCUMENT_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:body>
    <w:p>
      <w:pPr>
        <w:pStyle w:val="Title"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
          <w:sz w:val="28"/>
          <w:color w:val="1F4788"/>
        </w:rPr>
        <w:t>Sample Document Title</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
          <w:sz w:val="24"/>
          <w:color w:val="000000"/>
        </w:rPr>
        <w:t>This is a sample paragraph with formatting.</w:t>
      </w:r>
    </w:p>
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>
    </w:sectPr>
  </w:body>
</w:document>'''

EXCEL_WORKBOOK_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Sheet1" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>'''

EXCEL_WORKSHEET_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
           xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheetData>
    <row r="1">
      <c r="A1" t="inlineStr">
        <is>
          <t>Sample Workbook Title</t>
        </is>
      </c>
      <c r="B1" t="inlineStr">
        <is>
          <t>Column B</t>
        </is>
      </c>
    </row>
    <row r="2">
      <c r="A2" t="inlineStr">
        <is>
          <t>Row 2 Data</t>
        </is>
      </c>
      <c r="B2" s="1">
        <v>123.45</v>
      </c>
    </row>
  </sheetData>
</worksheet>'''

CONTENT_TYPES_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-presentationml.slide+xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-wordprocessingml.document.main+xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-spreadsheetml.worksheet+xml"/>
</Types>'''

RELS_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>'''


class OOXMLTestDocument:
    """Helper class for creating and managing OOXML test documents."""
    
    def __init__(self, doc_type: str, temp_dir: Path):
        self.doc_type = doc_type.lower()
        self.temp_dir = temp_dir
        self.file_path: Optional[Path] = None
        self.content_mapping = {
            'powerpoint': {
                'extension': '.pptx',
                'main_xml': 'ppt/presentation.xml',
                'main_content': POWERPOINT_PRESENTATION_XML,
                'additional_files': {
                    'ppt/slides/slide1.xml': POWERPOINT_SLIDE_XML,
                }
            },
            'word': {
                'extension': '.docx',
                'main_xml': 'word/document.xml',
                'main_content': WORD_DOCUMENT_XML,
                'additional_files': {}
            },
            'excel': {
                'extension': '.xlsx',
                'main_xml': 'xl/workbook.xml',
                'main_content': EXCEL_WORKBOOK_XML,
                'additional_files': {
                    'xl/worksheets/sheet1.xml': EXCEL_WORKSHEET_XML,
                }
            }
        }
    
    def create_document(self, filename: Optional[str] = None) -> Path:
        """Create a complete OOXML document with proper structure."""
        if self.doc_type not in self.content_mapping:
            raise ValueError(f"Unsupported document type: {self.doc_type}")
        
        config = self.content_mapping[self.doc_type]
        
        if filename is None:
            filename = f"test_document{config['extension']}"
        
        self.file_path = self.temp_dir / filename
        
        # Create OOXML ZIP structure
        with zipfile.ZipFile(self.file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add content types
            zipf.writestr('[Content_Types].xml', CONTENT_TYPES_XML)
            
            # Add relationships
            zipf.writestr('_rels/.rels', RELS_XML)
            
            # Add main content
            zipf.writestr(config['main_xml'], config['main_content'])
            
            # Add additional files
            for file_path, content in config['additional_files'].items():
                zipf.writestr(file_path, content)
                
            # Add required directory structure relationships
            if self.doc_type == 'powerpoint':
                ppt_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/>
</Relationships>'''
                zipf.writestr('ppt/_rels/presentation.xml.rels', ppt_rels)
        
        return self.file_path
    
    def get_xml_content(self, xml_path: str) -> str:
        """Extract specific XML content from the document."""
        if not self.file_path or not self.file_path.exists():
            raise FileNotFoundError("Document not created or not found")
        
        with zipfile.ZipFile(self.file_path, 'r') as zipf:
            try:
                return zipf.read(xml_path).decode('utf-8')
            except KeyError:
                raise FileNotFoundError(f"XML file {xml_path} not found in document")
    
    def modify_xml_content(self, xml_path: str, new_content: str):
        """Modify XML content in the document."""
        if not self.file_path or not self.file_path.exists():
            raise FileNotFoundError("Document not created or not found")
        
        # Read existing content
        temp_path = self.temp_dir / f"temp_{self.file_path.name}"
        
        with zipfile.ZipFile(self.file_path, 'r') as source_zip:
            with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as target_zip:
                for item in source_zip.infolist():
                    if item.filename == xml_path:
                        # Replace with new content
                        target_zip.writestr(item.filename, new_content)
                    else:
                        # Copy existing content
                        target_zip.writestr(item.filename, source_zip.read(item.filename))
        
        # Replace original with modified version
        temp_path.replace(self.file_path)
    
    def validate_structure(self) -> Dict[str, Any]:
        """Validate the OOXML document structure."""
        if not self.file_path or not self.file_path.exists():
            raise FileNotFoundError("Document not created or not found")
        
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'file_count': 0,
            'files': []
        }
        
        try:
            with zipfile.ZipFile(self.file_path, 'r') as zipf:
                file_list = zipf.namelist()
                validation_result['file_count'] = len(file_list)
                validation_result['files'] = file_list
                
                # Check required files
                required_files = ['[Content_Types].xml']
                config = self.content_mapping[self.doc_type]
                required_files.append(config['main_xml'])
                
                for required_file in required_files:
                    if required_file not in file_list:
                        validation_result['errors'].append(f"Missing required file: {required_file}")
                        validation_result['is_valid'] = False
                
                # Validate XML structure
                for xml_file in file_list:
                    if xml_file.endswith('.xml'):
                        try:
                            xml_content = zipf.read(xml_file).decode('utf-8')
                            ET.fromstring(xml_content)
                        except ET.ParseError as e:
                            validation_result['errors'].append(f"XML parse error in {xml_file}: {str(e)}")
                            validation_result['is_valid'] = False
                        except UnicodeDecodeError as e:
                            validation_result['errors'].append(f"Encoding error in {xml_file}: {str(e)}")
                            validation_result['is_valid'] = False
                            
        except zipfile.BadZipFile as e:
            validation_result['errors'].append(f"Invalid ZIP structure: {str(e)}")
            validation_result['is_valid'] = False
        
        return validation_result


@pytest.fixture
def ooxml_temp_workspace():
    """Provide a temporary workspace specifically for OOXML testing."""
    temp_dir = Path(tempfile.mkdtemp(prefix="ooxml_test_"))
    yield temp_dir
    
    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def powerpoint_document(ooxml_temp_workspace):
    """Create a test PowerPoint document."""
    doc = OOXMLTestDocument('powerpoint', ooxml_temp_workspace)
    file_path = doc.create_document('test_presentation.pptx')
    yield doc
    
    # Cleanup handled by ooxml_temp_workspace fixture


@pytest.fixture
def word_document(ooxml_temp_workspace):
    """Create a test Word document."""
    doc = OOXMLTestDocument('word', ooxml_temp_workspace)
    file_path = doc.create_document('test_document.docx')
    yield doc


@pytest.fixture
def excel_document(ooxml_temp_workspace):
    """Create a test Excel document."""
    doc = OOXMLTestDocument('excel', ooxml_temp_workspace)
    file_path = doc.create_document('test_workbook.xlsx')
    yield doc


@pytest.fixture
def all_ooxml_documents(ooxml_temp_workspace):
    """Create test documents for all OOXML formats."""
    documents = {
        'powerpoint': OOXMLTestDocument('powerpoint', ooxml_temp_workspace),
        'word': OOXMLTestDocument('word', ooxml_temp_workspace),
        'excel': OOXMLTestDocument('excel', ooxml_temp_workspace)
    }
    
    for doc_type, doc in documents.items():
        doc.create_document()
    
    yield documents


@pytest.fixture
def ooxml_xml_samples():
    """Provide sample OOXML XML content for testing."""
    return {
        'powerpoint_presentation': POWERPOINT_PRESENTATION_XML,
        'powerpoint_slide': POWERPOINT_SLIDE_XML,
        'word_document': WORD_DOCUMENT_XML,
        'excel_workbook': EXCEL_WORKBOOK_XML,
        'excel_worksheet': EXCEL_WORKSHEET_XML,
        'content_types': CONTENT_TYPES_XML,
        'relationships': RELS_XML
    }


@pytest.fixture
def ooxml_namespace_map():
    """Provide OOXML namespace mappings for XPath queries."""
    return {
        'powerpoint': {
            'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
            'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
        },
        'word': {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
            'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
        },
        'excel': {
            'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
            'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
        },
        'common': {
            'ct': 'http://schemas.openxmlformats.org/package/2006/content-types',
            'rel': 'http://schemas.openxmlformats.org/package/2006/relationships'
        }
    }


@pytest.fixture
def ooxml_validation_helpers():
    """Provide helper functions for OOXML validation."""
    
    class OOXMLValidationHelpers:
        
        @staticmethod
        def validate_xml_structure(xml_content: str, expected_root_tag: str) -> bool:
            """Validate XML structure and root tag."""
            try:
                root = ET.fromstring(xml_content)
                return expected_root_tag in root.tag
            except ET.ParseError:
                return False
        
        @staticmethod
        def extract_text_content(xml_content: str, xpath: str = None) -> List[str]:
            """Extract text content from XML."""
            try:
                root = ET.fromstring(xml_content)
                if xpath:
                    # Simple XPath-like extraction (limited)
                    elements = root.findall('.//' + xpath.split('/')[-1])
                else:
                    elements = root.findall('.//t')  # Common text elements
                
                return [elem.text for elem in elements if elem.text]
            except ET.ParseError:
                return []
        
        @staticmethod
        def count_elements(xml_content: str, element_tag: str) -> int:
            """Count specific elements in XML."""
            try:
                root = ET.fromstring(xml_content)
                return len(root.findall(f'.//{element_tag}'))
            except ET.ParseError:
                return 0
        
        @staticmethod
        def validate_namespace_declarations(xml_content: str, required_namespaces: List[str]) -> bool:
            """Validate that required namespaces are declared."""
            for namespace in required_namespaces:
                if namespace not in xml_content:
                    return False
            return True
        
        @staticmethod
        def extract_relationships(rels_xml: str) -> Dict[str, str]:
            """Extract relationship mappings from relationships XML."""
            try:
                root = ET.fromstring(rels_xml)
                relationships = {}
                for rel in root.findall('.//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'):
                    rel_id = rel.get('Id')
                    target = rel.get('Target')
                    if rel_id and target:
                        relationships[rel_id] = target
                return relationships
            except ET.ParseError:
                return {}
    
    return OOXMLValidationHelpers()


@pytest.fixture
def ooxml_test_data_generator():
    """Generate various test data for OOXML processing."""
    
    class OOXMLTestDataGenerator:
        
        def __init__(self):
            self.color_values = ['FF0000', '00FF00', '0000FF', '1F4788', '70AD47', 'FFC000']
            self.font_families = ['Calibri', 'Arial', 'Times New Roman', 'Helvetica']
            self.font_sizes = [8, 10, 12, 14, 16, 18, 24, 28, 36]
        
        def generate_color_variations(self, base_xml: str, count: int = 5) -> List[str]:
            """Generate XML variations with different colors."""
            variations = []
            for i, color in enumerate(self.color_values[:count]):
                # Simple color replacement
                variation = base_xml.replace('1F4788', color).replace('000000', color)
                variations.append(variation)
            return variations
        
        def generate_text_variations(self, base_xml: str, text_replacements: Dict[str, List[str]]) -> List[str]:
            """Generate XML variations with different text content."""
            variations = []
            for old_text, new_texts in text_replacements.items():
                for new_text in new_texts:
                    variation = base_xml.replace(old_text, new_text)
                    variations.append(variation)
            return variations
        
        def generate_structure_variations(self, base_xml: str) -> Dict[str, str]:
            """Generate structural variations of XML."""
            variations = {}
            
            # Add extra elements
            root = ET.fromstring(base_xml)
            
            # Variation 1: Add extra paragraph/slide/row
            extra_element_xml = base_xml  # Would implement element insertion
            variations['extra_element'] = extra_element_xml
            
            # Variation 2: Remove some elements (simplified)
            minimal_xml = base_xml  # Would implement element removal
            variations['minimal'] = minimal_xml
            
            return variations
        
        def generate_large_document_content(self, doc_type: str, element_count: int = 100) -> str:
            """Generate content for large document testing."""
            if doc_type == 'powerpoint':
                # Generate slides
                base_slide = POWERPOINT_SLIDE_XML
                # Would generate multiple slides
                return base_slide
            elif doc_type == 'word':
                # Generate paragraphs
                base_paragraph = '<w:p><w:r><w:t>Generated paragraph {}</w:t></w:r></w:p>'
                paragraphs = [base_paragraph.format(i) for i in range(element_count)]
                return WORD_DOCUMENT_XML.replace(
                    '<w:sectPr>',
                    ''.join(paragraphs) + '<w:sectPr>'
                )
            elif doc_type == 'excel':
                # Generate rows
                base_row = '<row r="{0}"><c r="A{0}" t="inlineStr"><is><t>Row {0} Data</t></is></c></row>'
                rows = [base_row.format(i) for i in range(1, element_count + 1)]
                return EXCEL_WORKSHEET_XML.replace(
                    '</sheetData>',
                    ''.join(rows) + '</sheetData>'
                )
            
            return ""
    
    return OOXMLTestDataGenerator()


@pytest.fixture
def corrupted_ooxml_samples():
    """Provide samples of corrupted OOXML for error testing."""
    return {
        'malformed_xml': '<?xml version="1.0"?><root><unclosed>',
        'invalid_namespace': POWERPOINT_PRESENTATION_XML.replace(
            'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"',
            'xmlns:p="http://invalid.namespace.example.com"'
        ),
        'missing_required_elements': '''<?xml version="1.0" encoding="UTF-8"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <!-- Missing required elements -->
</p:presentation>''',
        'binary_content_in_xml': 'This is not XML content but binary data: \x00\x01\x02\x03',
        'empty_content': '',
        'encoding_issues': 'Invalid UTF-8: \xff\xfe\xfd'
    }


@pytest.fixture
def ooxml_performance_test_data():
    """Provide test data for performance testing."""
    return {
        'small_document': {
            'element_count': 10,
            'expected_processing_time': 0.1  # seconds
        },
        'medium_document': {
            'element_count': 100,
            'expected_processing_time': 0.5  # seconds  
        },
        'large_document': {
            'element_count': 1000,
            'expected_processing_time': 2.0  # seconds
        }
    }


# Utility functions for OOXML testing

def create_minimal_ooxml_file(file_path: Path, doc_type: str = 'powerpoint'):
    """Create a minimal valid OOXML file for testing."""
    doc = OOXMLTestDocument(doc_type, file_path.parent)
    return doc.create_document(file_path.name)


def validate_ooxml_zip_structure(file_path: Path) -> bool:
    """Validate basic OOXML ZIP structure."""
    try:
        with zipfile.ZipFile(file_path, 'r') as zipf:
            file_list = zipf.namelist()
            return '[Content_Types].xml' in file_list and '_rels/.rels' in file_list
    except (zipfile.BadZipFile, FileNotFoundError):
        return False


def extract_and_parse_xml(ooxml_path: Path, xml_internal_path: str) -> Optional[ET.Element]:
    """Extract and parse XML from OOXML file."""
    try:
        with zipfile.ZipFile(ooxml_path, 'r') as zipf:
            xml_content = zipf.read(xml_internal_path).decode('utf-8')
            return ET.fromstring(xml_content)
    except (zipfile.BadZipFile, KeyError, ET.ParseError, UnicodeDecodeError):
        return None