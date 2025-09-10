#!/usr/bin/env python3
"""
Test OOXML Fixtures

This module tests the OOXML fixtures to ensure they work correctly
and provide the expected functionality for testing OOXML processing.
"""

import pytest
import xml.etree.ElementTree as ET
from pathlib import Path
from fixtures.ooxml_fixtures import (
    OOXMLTestDocument,
    create_minimal_ooxml_file,
    validate_ooxml_zip_structure,
    extract_and_parse_xml,
    POWERPOINT_PRESENTATION_XML,
    WORD_DOCUMENT_XML,
    EXCEL_WORKBOOK_XML
)


@pytest.mark.unit
@pytest.mark.ooxml
class TestOOXMLFixtures:
    """Test OOXML fixture functionality."""
    
    def test_ooxml_temp_workspace_fixture(self, ooxml_temp_workspace):
        """Test OOXML temporary workspace fixture."""
        assert ooxml_temp_workspace.exists()
        assert ooxml_temp_workspace.is_dir()
        
        # Test workspace is writable
        test_file = ooxml_temp_workspace / "test.txt"
        test_file.write_text("test content")
        assert test_file.exists()
    
    def test_powerpoint_document_fixture(self, powerpoint_document):
        """Test PowerPoint document fixture."""
        assert powerpoint_document.file_path is not None
        assert powerpoint_document.file_path.exists()
        assert powerpoint_document.file_path.suffix == '.pptx'
        
        # Validate structure
        validation = powerpoint_document.validate_structure()
        assert validation['is_valid'], f"Validation errors: {validation['errors']}"
        assert validation['file_count'] > 0
        assert '[Content_Types].xml' in validation['files']
    
    def test_word_document_fixture(self, word_document):
        """Test Word document fixture."""
        assert word_document.file_path is not None
        assert word_document.file_path.exists()
        assert word_document.file_path.suffix == '.docx'
        
        # Validate structure
        validation = word_document.validate_structure()
        assert validation['is_valid'], f"Validation errors: {validation['errors']}"
    
    def test_excel_document_fixture(self, excel_document):
        """Test Excel document fixture."""
        assert excel_document.file_path is not None
        assert excel_document.file_path.exists()
        assert excel_document.file_path.suffix == '.xlsx'
        
        # Validate structure
        validation = excel_document.validate_structure()
        assert validation['is_valid'], f"Validation errors: {validation['errors']}"
    
    def test_all_ooxml_documents_fixture(self, all_ooxml_documents):
        """Test all OOXML documents fixture."""
        expected_types = ['powerpoint', 'word', 'excel']
        
        assert len(all_ooxml_documents) == len(expected_types)
        
        for doc_type in expected_types:
            assert doc_type in all_ooxml_documents
            doc = all_ooxml_documents[doc_type]
            assert doc.file_path is not None
            assert doc.file_path.exists()
            
            validation = doc.validate_structure()
            assert validation['is_valid'], f"{doc_type} validation errors: {validation['errors']}"
    
    def test_ooxml_xml_samples_fixture(self, ooxml_xml_samples):
        """Test OOXML XML samples fixture."""
        expected_samples = [
            'powerpoint_presentation', 'powerpoint_slide',
            'word_document', 'excel_workbook', 'excel_worksheet',
            'content_types', 'relationships'
        ]
        
        for sample_name in expected_samples:
            assert sample_name in ooxml_xml_samples
            sample_content = ooxml_xml_samples[sample_name]
            assert isinstance(sample_content, str)
            assert sample_content.startswith('<?xml')
            
            # Validate XML is well-formed
            try:
                ET.fromstring(sample_content)
            except ET.ParseError:
                pytest.fail(f"Sample {sample_name} contains malformed XML")
    
    def test_ooxml_namespace_map_fixture(self, ooxml_namespace_map):
        """Test OOXML namespace map fixture."""
        expected_formats = ['powerpoint', 'word', 'excel', 'common']
        
        for format_name in expected_formats:
            assert format_name in ooxml_namespace_map
            namespaces = ooxml_namespace_map[format_name]
            assert isinstance(namespaces, dict)
            assert len(namespaces) > 0
            
            # Validate namespace URIs
            for prefix, uri in namespaces.items():
                assert isinstance(prefix, str)
                assert isinstance(uri, str)
                assert uri.startswith('http')
    
    def test_ooxml_validation_helpers_fixture(self, ooxml_validation_helpers):
        """Test OOXML validation helpers fixture."""
        helpers = ooxml_validation_helpers
        
        # Test XML structure validation
        valid_xml = POWERPOINT_PRESENTATION_XML
        assert helpers.validate_xml_structure(valid_xml, 'presentation')
        assert not helpers.validate_xml_structure('<invalid>', 'presentation')
        
        # Test text content extraction
        text_content = helpers.extract_text_content(WORD_DOCUMENT_XML)
        assert len(text_content) > 0
        
        # Test element counting
        element_count = helpers.count_elements(valid_xml, 'sldMasterId')
        assert element_count >= 0
        
        # Test namespace validation
        required_namespaces = ['http://schemas.openxmlformats.org/presentationml/2006/main']
        assert helpers.validate_namespace_declarations(valid_xml, required_namespaces)
    
    def test_ooxml_test_data_generator_fixture(self, ooxml_test_data_generator):
        """Test OOXML test data generator fixture."""
        generator = ooxml_test_data_generator
        
        # Test color variations
        variations = generator.generate_color_variations(POWERPOINT_PRESENTATION_XML, 3)
        assert len(variations) == 3
        assert all(isinstance(v, str) for v in variations)
        
        # Test text variations
        text_replacements = {'Sample': ['Test', 'Demo']}
        text_variations = generator.generate_text_variations(WORD_DOCUMENT_XML, text_replacements)
        assert len(text_variations) == 2
        
        # Test large document generation
        large_content = generator.generate_large_document_content('word', 10)
        assert isinstance(large_content, str)
        assert len(large_content) > len(WORD_DOCUMENT_XML)
    
    def test_corrupted_ooxml_samples_fixture(self, corrupted_ooxml_samples):
        """Test corrupted OOXML samples fixture."""
        expected_corruption_types = [
            'malformed_xml', 'invalid_namespace', 'missing_required_elements',
            'binary_content_in_xml', 'empty_content', 'encoding_issues'
        ]
        
        for corruption_type in expected_corruption_types:
            assert corruption_type in corrupted_ooxml_samples
            corrupted_content = corrupted_ooxml_samples[corruption_type]
            
            # These should fail XML parsing (except empty content)
            if corruption_type != 'empty_content':
                with pytest.raises(ET.ParseError):
                    ET.fromstring(corrupted_content)
    
    def test_ooxml_performance_test_data_fixture(self, ooxml_performance_test_data):
        """Test OOXML performance test data fixture."""
        expected_sizes = ['small_document', 'medium_document', 'large_document']
        
        for size in expected_sizes:
            assert size in ooxml_performance_test_data
            size_data = ooxml_performance_test_data[size]
            
            assert 'element_count' in size_data
            assert 'expected_processing_time' in size_data
            assert isinstance(size_data['element_count'], int)
            assert isinstance(size_data['expected_processing_time'], (int, float))
            assert size_data['element_count'] > 0
            assert size_data['expected_processing_time'] > 0


@pytest.mark.unit
@pytest.mark.ooxml
class TestOOXMLTestDocument:
    """Test OOXMLTestDocument class functionality."""
    
    def test_create_powerpoint_document(self, ooxml_temp_workspace):
        """Test creating PowerPoint document."""
        doc = OOXMLTestDocument('powerpoint', ooxml_temp_workspace)
        file_path = doc.create_document()
        
        assert file_path.exists()
        assert file_path.suffix == '.pptx'
        assert validate_ooxml_zip_structure(file_path)
    
    def test_create_word_document(self, ooxml_temp_workspace):
        """Test creating Word document."""
        doc = OOXMLTestDocument('word', ooxml_temp_workspace)
        file_path = doc.create_document()
        
        assert file_path.exists()
        assert file_path.suffix == '.docx'
        assert validate_ooxml_zip_structure(file_path)
    
    def test_create_excel_document(self, ooxml_temp_workspace):
        """Test creating Excel document."""
        doc = OOXMLTestDocument('excel', ooxml_temp_workspace)
        file_path = doc.create_document()
        
        assert file_path.exists()
        assert file_path.suffix == '.xlsx'
        assert validate_ooxml_zip_structure(file_path)
    
    def test_get_xml_content(self, ooxml_temp_workspace):
        """Test getting XML content from document."""
        doc = OOXMLTestDocument('powerpoint', ooxml_temp_workspace)
        doc.create_document()
        
        xml_content = doc.get_xml_content('ppt/presentation.xml')
        assert isinstance(xml_content, str)
        assert '<?xml' in xml_content
        assert 'presentation' in xml_content
    
    def test_modify_xml_content(self, ooxml_temp_workspace):
        """Test modifying XML content in document."""
        doc = OOXMLTestDocument('word', ooxml_temp_workspace)
        doc.create_document()
        
        original_content = doc.get_xml_content('word/document.xml')
        modified_content = original_content.replace('Sample Document Title', 'Modified Title')
        
        doc.modify_xml_content('word/document.xml', modified_content)
        
        new_content = doc.get_xml_content('word/document.xml')
        assert 'Modified Title' in new_content
        assert 'Sample Document Title' not in new_content
    
    def test_validate_structure(self, ooxml_temp_workspace):
        """Test structure validation."""
        doc = OOXMLTestDocument('excel', ooxml_temp_workspace)
        doc.create_document()
        
        validation = doc.validate_structure()
        
        assert isinstance(validation, dict)
        assert 'is_valid' in validation
        assert 'errors' in validation
        assert 'warnings' in validation
        assert 'file_count' in validation
        assert 'files' in validation
        
        assert validation['is_valid'] is True
        assert len(validation['errors']) == 0
        assert validation['file_count'] > 0
        assert isinstance(validation['files'], list)
    
    def test_unsupported_document_type(self, ooxml_temp_workspace):
        """Test error handling for unsupported document types."""
        with pytest.raises(ValueError, match="Unsupported document type"):
            doc = OOXMLTestDocument('unsupported', ooxml_temp_workspace)
            doc.create_document()


@pytest.mark.unit
@pytest.mark.ooxml
class TestOOXMLUtilities:
    """Test OOXML utility functions."""
    
    def test_create_minimal_ooxml_file(self, ooxml_temp_workspace):
        """Test creating minimal OOXML file."""
        file_path = ooxml_temp_workspace / "minimal.pptx"
        created_path = create_minimal_ooxml_file(file_path, 'powerpoint')
        
        assert created_path.exists()
        assert created_path == file_path
        assert validate_ooxml_zip_structure(created_path)
    
    def test_validate_ooxml_zip_structure_valid(self, powerpoint_document):
        """Test ZIP structure validation with valid file."""
        assert validate_ooxml_zip_structure(powerpoint_document.file_path)
    
    def test_validate_ooxml_zip_structure_invalid(self, ooxml_temp_workspace):
        """Test ZIP structure validation with invalid file."""
        # Create invalid file
        invalid_file = ooxml_temp_workspace / "invalid.pptx"
        invalid_file.write_text("This is not a ZIP file")
        
        assert not validate_ooxml_zip_structure(invalid_file)
        
        # Test non-existent file
        non_existent = ooxml_temp_workspace / "nonexistent.pptx"
        assert not validate_ooxml_zip_structure(non_existent)
    
    def test_extract_and_parse_xml_valid(self, word_document):
        """Test XML extraction and parsing with valid document."""
        root = extract_and_parse_xml(word_document.file_path, 'word/document.xml')
        
        assert root is not None
        assert isinstance(root, ET.Element)
        assert 'document' in root.tag
    
    def test_extract_and_parse_xml_invalid(self, ooxml_temp_workspace):
        """Test XML extraction with invalid conditions."""
        # Create invalid ZIP file
        invalid_file = ooxml_temp_workspace / "invalid.docx"
        invalid_file.write_text("Not a ZIP")
        
        # Should return None for invalid ZIP
        result = extract_and_parse_xml(invalid_file, 'word/document.xml')
        assert result is None
        
        # Test with valid ZIP but non-existent XML file
        valid_doc = OOXMLTestDocument('word', ooxml_temp_workspace)
        valid_doc.create_document('valid.docx')
        
        result = extract_and_parse_xml(valid_doc.file_path, 'nonexistent.xml')
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])