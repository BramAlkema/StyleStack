"""Tests for XML parsing, normalization, and semantic comparison."""

import pytest
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from lxml import etree
import xml.etree.ElementTree as ET

from ooxml_tester.analyze.xml_parser import OOXMLParser, XMLNormalizer, SemanticComparator
from ooxml_tester.analyze.package_extractor import PackageExtractor
from ooxml_tester.core.exceptions import AnalysisError


class TestPackageExtractor:
    """Test OOXML package extraction and XML part isolation."""
    
    def test_extract_ooxml_package_basic(self):
        """Test basic OOXML package extraction."""
        extractor = PackageExtractor()
        
        # Create a minimal OOXML package for testing
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            
            with zipfile.ZipFile(temp_path, 'w') as zf:
                # Add minimal OOXML structure
                zf.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types/>')
                zf.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships/>')
                zf.writestr('word/document.xml', '<?xml version="1.0" encoding="UTF-8"?><document/>')
                zf.writestr('word/styles.xml', '<?xml version="1.0" encoding="UTF-8"?><styles/>')
        
        try:
            # Extract package
            extracted_parts = extractor.extract_package(temp_path)
            
            # Verify extraction
            assert 'word/document.xml' in extracted_parts
            assert 'word/styles.xml' in extracted_parts
            assert '[Content_Types].xml' in extracted_parts
            assert '_rels/.rels' in extracted_parts
            
            # Verify XML content is preserved
            assert b'<document/>' in extracted_parts['word/document.xml']
            assert b'<styles/>' in extracted_parts['word/styles.xml']
        finally:
            temp_path.unlink()
    
    def test_extract_powerpoint_package(self):
        """Test PowerPoint package extraction."""
        extractor = PackageExtractor()
        
        with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            
            with zipfile.ZipFile(temp_path, 'w') as zf:
                zf.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types/>')
                zf.writestr('ppt/presentation.xml', '<?xml version="1.0"?><presentation/>')
                zf.writestr('ppt/theme/theme1.xml', '<?xml version="1.0"?><theme/>')
                zf.writestr('ppt/slides/slide1.xml', '<?xml version="1.0"?><slide/>')
        
        try:
            extracted_parts = extractor.extract_package(temp_path)
            
            assert 'ppt/presentation.xml' in extracted_parts
            assert 'ppt/theme/theme1.xml' in extracted_parts
            assert 'ppt/slides/slide1.xml' in extracted_parts
        finally:
            temp_path.unlink()
    
    def test_extract_excel_package(self):
        """Test Excel package extraction."""
        extractor = PackageExtractor()
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            
            with zipfile.ZipFile(temp_path, 'w') as zf:
                zf.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types/>')
                zf.writestr('xl/workbook.xml', '<?xml version="1.0"?><workbook/>')
                zf.writestr('xl/styles.xml', '<?xml version="1.0"?><styleSheet/>')
                zf.writestr('xl/worksheets/sheet1.xml', '<?xml version="1.0"?><worksheet/>')
        
        try:
            extracted_parts = extractor.extract_package(temp_path)
            
            assert 'xl/workbook.xml' in extracted_parts
            assert 'xl/styles.xml' in extracted_parts
            assert 'xl/worksheets/sheet1.xml' in extracted_parts
        finally:
            temp_path.unlink()
    
    def test_extract_invalid_package(self):
        """Test handling of invalid OOXML packages."""
        extractor = PackageExtractor()
        
        # Test with non-existent file
        with pytest.raises(AnalysisError, match="File does not exist"):
            extractor.extract_package(Path("nonexistent.docx"))
        
        # Test with invalid ZIP file
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(b"Not a valid ZIP file")
        
        try:
            with pytest.raises(AnalysisError, match="Invalid OOXML package"):
                extractor.extract_package(temp_path)
        finally:
            temp_path.unlink()
    
    def test_filter_xml_parts(self):
        """Test filtering of XML parts from package."""
        extractor = PackageExtractor()
        
        sample_parts = {
            'word/document.xml': b'<document/>',
            'word/styles.xml': b'<styles/>',
            'word/media/image1.jpeg': b'binary_image_data',
            'docProps/core.xml': b'<coreProperties/>',
            'word/embeddings/oleObject1.bin': b'binary_ole_data'
        }
        
        xml_parts = extractor.filter_xml_parts(sample_parts)
        
        # Should only include XML files
        assert 'word/document.xml' in xml_parts
        assert 'word/styles.xml' in xml_parts
        assert 'docProps/core.xml' in xml_parts
        
        # Should exclude binary files
        assert 'word/media/image1.jpeg' not in xml_parts
        assert 'word/embeddings/oleObject1.bin' not in xml_parts


class TestXMLNormalizer:
    """Test XML normalization for consistent comparison."""
    
    def test_namespace_normalization(self):
        """Test normalization of XML namespaces."""
        normalizer = XMLNormalizer()
        
        xml_with_namespaces = '''<?xml version="1.0"?>
        <document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
            <w:body>
                <w:p>
                    <w:r>
                        <w:t>Hello World</w:t>
                    </w:r>
                </w:p>
            </w:body>
        </document>'''
        
        normalized = normalizer.normalize_namespaces(xml_with_namespaces.encode())
        
        # Verify namespace prefixes are consistent
        assert b'w:body' in normalized
        assert b'w:p' in normalized
        assert b'w:t' in normalized
        
        # Verify namespace declarations are preserved
        assert b'xmlns:w=' in normalized
        assert b'xmlns:r=' in normalized
    
    def test_attribute_ordering(self):
        """Test consistent attribute ordering."""
        normalizer = XMLNormalizer()
        
        xml_unordered = '''<?xml version="1.0"?>
        <element z="3" a="1" m="2" id="test"/>'''
        
        normalized = normalizer.normalize_attributes(xml_unordered.encode())
        
        # Parse to verify attribute ordering
        root = etree.fromstring(normalized)
        attrs = list(root.attrib.keys())
        
        # Should be in alphabetical order
        assert attrs == sorted(attrs)
    
    def test_whitespace_normalization(self):
        """Test whitespace normalization."""
        normalizer = XMLNormalizer()
        
        xml_with_whitespace = '''<?xml version="1.0"?>
        <document>
            
            <body>
                <paragraph>   Text with   extra   spaces   </paragraph>
                
                <empty>    </empty>
            </body>
            
        </document>'''
        
        normalized = normalizer.normalize_whitespace(xml_with_whitespace.encode())
        
        # Verify excess whitespace is removed
        assert b'   extra   spaces   ' not in normalized
        assert b'\n            \n' not in normalized
        
        # Verify meaningful content is preserved
        assert b'Text with extra spaces' in normalized or b'Text with   extra   spaces' in normalized
    
    def test_xml_formatting_consistency(self):
        """Test consistent XML formatting."""
        normalizer = XMLNormalizer()
        
        xml_mixed_formatting = '''<?xml version="1.0"?><document><body><p>Text</p></body></document>'''
        
        normalized = normalizer.format_consistently(xml_mixed_formatting.encode())
        
        # Verify consistent indentation and line breaks
        lines = normalized.decode().split('\n')
        assert len(lines) > 1  # Should be formatted with line breaks
        
        # Check for consistent indentation
        indented_lines = [line for line in lines if line.strip() and line.startswith('  ')]
        assert len(indented_lines) > 0  # Should have indented content
    
    def test_normalize_full_pipeline(self):
        """Test complete normalization pipeline."""
        normalizer = XMLNormalizer()
        
        xml_input = '''<?xml version="1.0" encoding="UTF-8"?>
        <document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                  z="last" a="first" m="middle">
            
            <w:body>
                <w:p   w:rsidR="value"   w:rsidP="other">
                    <w:r>
                        <w:t>   Text with   spaces   </w:t>
                    </w:r>
                </w:p>
            </w:body>
            
        </document>'''
        
        normalized = normalizer.normalize(xml_input.encode())
        
        # Verify it's valid XML
        root = etree.fromstring(normalized)
        assert root.tag.endswith('document')
        
        # Verify normalization was applied
        normalized_str = normalized.decode()
        assert 'xmlns:w=' in normalized_str
        
        # Should have consistent formatting
        lines = normalized_str.split('\n')
        assert len([line for line in lines if line.strip()]) >= 3


class TestSemanticComparator:
    """Test semantic comparison of XML documents."""
    
    def test_identical_documents(self):
        """Test comparison of identical XML documents."""
        comparator = SemanticComparator()
        
        xml_content = '''<?xml version="1.0"?>
        <document>
            <body>
                <paragraph>Same content</paragraph>
            </body>
        </document>'''
        
        result = comparator.compare(xml_content.encode(), xml_content.encode())
        
        assert result.are_semantically_equal is True
        assert len(result.differences) == 0
        assert result.similarity_score == 1.0
    
    def test_whitespace_differences_ignored(self):
        """Test that whitespace differences are ignored in semantic comparison."""
        comparator = SemanticComparator()
        
        xml1 = '''<?xml version="1.0"?><document><body><p>Text</p></body></document>'''
        xml2 = '''<?xml version="1.0"?>
        <document>
            <body>
                <p>Text</p>
            </body>
        </document>'''
        
        result = comparator.compare(xml1.encode(), xml2.encode())
        
        assert result.are_semantically_equal is True
        assert result.similarity_score >= 0.95  # Should be very high
    
    def test_attribute_order_differences_ignored(self):
        """Test that attribute order differences are ignored."""
        comparator = SemanticComparator()
        
        xml1 = '''<?xml version="1.0"?><element a="1" b="2" c="3"/>'''
        xml2 = '''<?xml version="1.0"?><element c="3" a="1" b="2"/>'''
        
        result = comparator.compare(xml1.encode(), xml2.encode())
        
        assert result.are_semantically_equal is True
    
    def test_content_differences_detected(self):
        """Test detection of meaningful content differences."""
        comparator = SemanticComparator()
        
        xml1 = '''<?xml version="1.0"?><document><body><p>Original text</p></body></document>'''
        xml2 = '''<?xml version="1.0"?><document><body><p>Modified text</p></body></document>'''
        
        result = comparator.compare(xml1.encode(), xml2.encode())
        
        assert result.are_semantically_equal is False
        assert len(result.differences) > 0
        assert result.similarity_score < 1.0
        
        # Check difference details
        text_diff = next((diff for diff in result.differences 
                         if diff.diff_type == 'text_content'), None)
        assert text_diff is not None
        assert 'Original text' in text_diff.old_value
        assert 'Modified text' in text_diff.new_value
    
    def test_structural_differences_detected(self):
        """Test detection of structural differences."""
        comparator = SemanticComparator()
        
        xml1 = '''<?xml version="1.0"?><document><body><p>Text</p></body></document>'''
        xml2 = '''<?xml version="1.0"?><document><body><p>Text</p><div>New element</div></body></document>'''
        
        result = comparator.compare(xml1.encode(), xml2.encode())
        
        assert result.are_semantically_equal is False
        assert len(result.differences) > 0
        
        # Should detect element addition
        added_diff = next((diff for diff in result.differences 
                          if diff.diff_type == 'element_added'), None)
        assert added_diff is not None
    
    def test_attribute_differences_detected(self):
        """Test detection of attribute differences."""
        comparator = SemanticComparator()
        
        xml1 = '''<?xml version="1.0"?><element attr="value1"/>'''
        xml2 = '''<?xml version="1.0"?><element attr="value2"/>'''
        
        result = comparator.compare(xml1.encode(), xml2.encode())
        
        assert result.are_semantically_equal is False
        assert len(result.differences) > 0
        
        # Should detect attribute value change
        attr_diff = next((diff for diff in result.differences 
                         if diff.diff_type == 'attribute_changed'), None)
        assert attr_diff is not None
        assert attr_diff.old_value == 'value1'
        assert attr_diff.new_value == 'value2'
    
    def test_namespace_differences_handled(self):
        """Test handling of namespace differences."""
        comparator = SemanticComparator()
        
        xml1 = '''<?xml version="1.0"?>
        <document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body><w:p>Text</w:p></w:body>
        </document>'''
        
        xml2 = '''<?xml version="1.0"?>
        <document xmlns:word="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <word:body><word:p>Text</word:p></word:body>
        </document>'''
        
        result = comparator.compare(xml1.encode(), xml2.encode())
        
        # Should recognize as semantically equivalent despite different prefixes
        assert result.are_semantically_equal is True or result.similarity_score > 0.9
    
    def test_similarity_scoring(self):
        """Test similarity scoring calculation."""
        comparator = SemanticComparator()
        
        xml_base = '''<?xml version="1.0"?><doc><p>Text</p><p>More</p><p>Content</p></doc>'''
        xml_minor_change = '''<?xml version="1.0"?><doc><p>Text</p><p>Modified</p><p>Content</p></doc>'''
        xml_major_change = '''<?xml version="1.0"?><doc><div>Completely</div><div>Different</div></doc>'''
        
        result_minor = comparator.compare(xml_base.encode(), xml_minor_change.encode())
        result_major = comparator.compare(xml_base.encode(), xml_major_change.encode())
        
        # Minor change should have higher similarity than major change
        assert result_minor.similarity_score > result_major.similarity_score
        assert result_minor.similarity_score > 0.7  # Still quite similar
        assert result_major.similarity_score < 0.5  # Very different


class TestOOXMLParser:
    """Test OOXML-specific parsing capabilities."""
    
    def test_parse_word_document(self):
        """Test parsing Word document XML."""
        parser = OOXMLParser()
        
        word_xml = '''<?xml version="1.0"?>
        <document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                <w:p>
                    <w:pPr>
                        <w:pStyle w:val="Heading1"/>
                    </w:pPr>
                    <w:r>
                        <w:rPr>
                            <w:b/>
                            <w:color w:val="FF0000"/>
                        </w:rPr>
                        <w:t>Heading Text</w:t>
                    </w:r>
                </w:p>
            </w:body>
        </document>'''
        
        parsed = parser.parse_word_document(word_xml.encode())
        
        # Verify parsing structure
        assert 'paragraphs' in parsed
        assert len(parsed['paragraphs']) == 1
        
        paragraph = parsed['paragraphs'][0]
        assert paragraph['style'] == 'Heading1'
        assert len(paragraph['runs']) == 1
        
        run = paragraph['runs'][0]
        assert run['text'] == 'Heading Text'
        assert run['bold'] is True
        assert run['color'] == 'FF0000'
    
    def test_parse_powerpoint_slide(self):
        """Test parsing PowerPoint slide XML."""
        parser = OOXMLParser()
        
        slide_xml = '''<?xml version="1.0"?>
        <sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
             xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
            <p:cSld>
                <p:spTree>
                    <p:sp>
                        <p:txBody>
                            <a:p>
                                <a:r>
                                    <a:rPr>
                                        <a:solidFill>
                                            <a:srgbClr val="0000FF"/>
                                        </a:solidFill>
                                    </a:rPr>
                                    <a:t>Slide Title</a:t>
                                </a:r>
                            </a:p>
                        </p:txBody>
                    </p:sp>
                </p:spTree>
            </p:cSld>
        </sld>'''
        
        parsed = parser.parse_powerpoint_slide(slide_xml.encode())
        
        # Verify parsing structure
        assert 'shapes' in parsed
        assert len(parsed['shapes']) == 1
        
        shape = parsed['shapes'][0]
        assert 'text_content' in shape
        assert len(shape['text_content']['paragraphs']) == 1
        
        paragraph = shape['text_content']['paragraphs'][0]
        run = paragraph['runs'][0]
        assert run['text'] == 'Slide Title'
        assert run['color'] == '0000FF'
    
    def test_parse_excel_worksheet(self):
        """Test parsing Excel worksheet XML."""
        parser = OOXMLParser()
        
        worksheet_xml = '''<?xml version="1.0"?>
        <worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
            <sheetData>
                <row r="1">
                    <c r="A1" s="1">
                        <v>42</v>
                    </c>
                    <c r="B1" t="str">
                        <v>Text Value</v>
                    </c>
                </row>
                <row r="2">
                    <c r="A2" s="2">
                        <f>A1*2</f>
                        <v>84</v>
                    </c>
                </row>
            </sheetData>
        </worksheet>'''
        
        parsed = parser.parse_excel_worksheet(worksheet_xml.encode())
        
        # Verify parsing structure
        assert 'rows' in parsed
        assert len(parsed['rows']) == 2
        
        # Check first row
        row1 = parsed['rows'][0]
        assert row1['row_number'] == 1
        assert len(row1['cells']) == 2
        
        cell_a1 = next(cell for cell in row1['cells'] if cell['reference'] == 'A1')
        assert cell_a1['value'] == '42'
        assert cell_a1['style_index'] == 1
        
        cell_b1 = next(cell for cell in row1['cells'] if cell['reference'] == 'B1')
        assert cell_b1['value'] == 'Text Value'
        assert cell_b1['data_type'] == 'str'
        
        # Check second row with formula
        row2 = parsed['rows'][1]
        cell_a2 = row2['cells'][0]
        assert cell_a2['formula'] == 'A1*2'
        assert cell_a2['value'] == '84'
    
    def test_extract_style_information(self):
        """Test extraction of style information from OOXML."""
        parser = OOXMLParser()
        
        styles_xml = '''<?xml version="1.0"?>
        <styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:style w:type="paragraph" w:styleId="Heading1">
                <w:name w:val="heading 1"/>
                <w:pPr>
                    <w:spacing w:before="240" w:after="120"/>
                    <w:jc w:val="left"/>
                </w:pPr>
                <w:rPr>
                    <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                    <w:sz w:val="32"/>
                    <w:color w:val="2F5496"/>
                </w:rPr>
            </w:style>
        </styles>'''
        
        styles = parser.extract_styles(styles_xml.encode())
        
        assert 'Heading1' in styles
        heading_style = styles['Heading1']
        
        assert heading_style['type'] == 'paragraph'
        assert heading_style['name'] == 'heading 1'
        assert heading_style['paragraph_properties']['spacing_before'] == '240'
        assert heading_style['paragraph_properties']['spacing_after'] == '120'
        assert heading_style['run_properties']['font_family'] == 'Calibri'
        assert heading_style['run_properties']['font_size'] == '32'
        assert heading_style['run_properties']['color'] == '2F5496'
    
    def test_error_handling_invalid_xml(self):
        """Test error handling for invalid XML."""
        parser = OOXMLParser()
        
        invalid_xml = b'<unclosed><tag>Invalid XML'
        
        with pytest.raises(AnalysisError, match="Invalid XML"):
            parser.parse_word_document(invalid_xml)
        
        with pytest.raises(AnalysisError, match="Invalid XML"):
            parser.parse_powerpoint_slide(invalid_xml)
        
        with pytest.raises(AnalysisError, match="Invalid XML"):
            parser.parse_excel_worksheet(invalid_xml)


class TestPerformanceAndScaling:
    """Test performance characteristics of XML analysis."""
    
    def test_large_document_handling(self):
        """Test handling of large XML documents."""
        parser = OOXMLParser()
        normalizer = XMLNormalizer()
        
        # Generate a large XML document
        large_xml_parts = ['<?xml version="1.0"?><document>']
        for i in range(1000):
            large_xml_parts.append(f'<paragraph id="{i}">Content {i}</paragraph>')
        large_xml_parts.append('</document>')
        large_xml = ''.join(large_xml_parts).encode()
        
        # Test normalization performance
        normalized = normalizer.normalize(large_xml)
        assert len(normalized) > 0
        
        # Verify it's still valid XML
        root = etree.fromstring(normalized)
        assert len(root) == 1000
    
    def test_memory_usage_with_multiple_documents(self):
        """Test memory usage with multiple document processing."""
        comparator = SemanticComparator()
        
        # Process multiple small documents
        base_xml = '''<?xml version="1.0"?><doc><p>Base content</p></doc>'''
        
        results = []
        for i in range(100):
            variant_xml = f'''<?xml version="1.0"?><doc><p>Content {i}</p></doc>'''
            result = comparator.compare(base_xml.encode(), variant_xml.encode())
            results.append(result)
        
        # All should complete successfully
        assert len(results) == 100
        assert all(not result.are_semantically_equal for result in results)
    
    @patch('ooxml_tester.analyze.xml_parser.etree.fromstring')
    def test_xml_parsing_timeout_protection(self, mock_fromstring):
        """Test protection against XML parsing timeouts."""
        parser = OOXMLParser()
        
        # Simulate a hanging parser
        mock_fromstring.side_effect = Exception("Parser timeout simulation")
        
        with pytest.raises(AnalysisError):
            parser.parse_word_document(b'<document/>')


if __name__ == '__main__':
    pytest.main([__file__])