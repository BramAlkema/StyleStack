#!/usr/bin/env python3
"""
Multi-format OOXML Handler Tests

Tests unified handling and processing across different OOXML template formats:
PowerPoint (.potx), Word (.dotx), and Excel (.xltx). Validates format detection,
structure validation, and cross-format compatibility.

Part of the StyleStack YAML-to-OOXML Processing Engine test suite.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import tempfile
import zipfile
import shutil
from pathlib import Path
from lxml import etree

from tools.multi_format_ooxml_handler import (
    MultiFormatOOXMLHandler, OOXMLFormat, OOXMLStructure, ProcessingResult,
    create_multi_format_handler, process_ooxml_template
)
from tools.yaml_ooxml_processor import RecoveryStrategy


class TestOOXMLFormat(unittest.TestCase):
    """Test OOXML format detection and handling."""
    
    def test_format_from_extension(self):
        """Test format detection from file extensions."""
        self.assertEqual(OOXMLFormat.from_extension("potx"), OOXMLFormat.POWERPOINT)
        self.assertEqual(OOXMLFormat.from_extension("dotx"), OOXMLFormat.WORD)
        self.assertEqual(OOXMLFormat.from_extension("xltx"), OOXMLFormat.EXCEL)
        
        # Test with dots
        self.assertEqual(OOXMLFormat.from_extension(".potx"), OOXMLFormat.POWERPOINT)
        
        # Test case insensitive
        self.assertEqual(OOXMLFormat.from_extension("POTX"), OOXMLFormat.POWERPOINT)
        
        # Test invalid format
        with self.assertRaises(ValueError):
            OOXMLFormat.from_extension("invalid")
    
    def test_format_from_path(self):
        """Test format detection from file paths."""
        self.assertEqual(OOXMLFormat.from_path("template.potx"), OOXMLFormat.POWERPOINT)
        self.assertEqual(OOXMLFormat.from_path("/path/to/doc.dotx"), OOXMLFormat.WORD)
        self.assertEqual(OOXMLFormat.from_path(Path("sheet.xltx")), OOXMLFormat.EXCEL)


class TestOOXMLStructure(unittest.TestCase):
    """Test OOXML structure definitions."""
    
    def test_structure_creation(self):
        """Test OOXMLStructure creation and defaults."""
        structure = OOXMLStructure(
            main_document_path="test/doc.xml",
            relationships_path="test/_rels/doc.xml.rels"
        )
        
        self.assertEqual(structure.main_document_path, "test/doc.xml")
        self.assertEqual(structure.relationships_path, "test/_rels/doc.xml.rels")
        self.assertEqual(structure.content_types_path, "[Content_Types].xml")
        self.assertEqual(structure.theme_paths, [])
        self.assertEqual(structure.style_paths, [])
        self.assertEqual(structure.required_namespaces, {})


class TestMultiFormatOOXMLHandler(unittest.TestCase):
    """Test multi-format OOXML handler functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = MultiFormatOOXMLHandler()
        
        # Sample patches for testing
        self.sample_patches = [
            {
                'operation': 'set',
                'target': '//a:srgbClr/@val',
                'value': 'FF0000'
            }
        ]
    
    def test_handler_initialization(self):
        """Test handler initialization with different configurations."""
        # Default initialization
        handler1 = MultiFormatOOXMLHandler()
        self.assertEqual(handler1.recovery_strategy, RecoveryStrategy.RETRY_WITH_FALLBACK)
        self.assertTrue(handler1.enable_token_integration)
        self.assertEqual(len(handler1.processors), 3)  # One for each format
        
        # Custom initialization
        handler2 = MultiFormatOOXMLHandler(
            recovery_strategy=RecoveryStrategy.FAIL_FAST,
            enable_token_integration=False
        )
        self.assertEqual(handler2.recovery_strategy, RecoveryStrategy.FAIL_FAST)
        self.assertFalse(handler2.enable_token_integration)
        self.assertEqual(len(handler2.token_layers), 0)
    
    def test_format_structure_definitions(self):
        """Test that format structures are correctly defined."""
        # Test PowerPoint structure
        ppt_structure = self.handler.FORMAT_STRUCTURES[OOXMLFormat.POWERPOINT]
        self.assertEqual(ppt_structure.main_document_path, "ppt/presentation.xml")
        self.assertIn("ppt/theme/theme1.xml", ppt_structure.theme_paths)
        self.assertIn('p', ppt_structure.required_namespaces)
        
        # Test Word structure
        word_structure = self.handler.FORMAT_STRUCTURES[OOXMLFormat.WORD]
        self.assertEqual(word_structure.main_document_path, "word/document.xml")
        self.assertIn("word/styles.xml", word_structure.style_paths)
        self.assertIn('w', word_structure.required_namespaces)
        
        # Test Excel structure
        excel_structure = self.handler.FORMAT_STRUCTURES[OOXMLFormat.EXCEL]
        self.assertEqual(excel_structure.main_document_path, "xl/workbook.xml")
        self.assertIn("xl/styles.xml", excel_structure.style_paths)
        self.assertIn('x', excel_structure.required_namespaces)
    
    def test_compatibility_matrix(self):
        """Test cross-format compatibility matrix."""
        matrix = self.handler.compatibility_matrix
        
        # Color operations should be compatible across formats
        self.assertTrue(matrix['color_operations']['potx_to_dotx'])
        self.assertTrue(matrix['color_operations']['dotx_to_xltx'])
        
        # Font operations should be compatible
        self.assertTrue(matrix['font_operations']['xltx_to_potx'])
        
        # Theme operations should not be compatible
        self.assertFalse(matrix['theme_operations']['potx_to_dotx'])
    
    @patch('tools.multi_format_ooxml_handler.zipfile.ZipFile')
    @patch('tools.multi_format_ooxml_handler.shutil.copy2')
    def test_validate_template_structure_valid(self, mock_copy, mock_zipfile):
        """Test template structure validation for valid template."""
        # Mock valid PowerPoint template
        mock_zip = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip
        mock_zip.namelist.return_value = [
            "ppt/presentation.xml",
            "ppt/_rels/presentation.xml.rels",
            "[Content_Types].xml",
            "ppt/theme/theme1.xml"
        ]
        
        # Mock valid XML content
        valid_xml = '''<?xml version="1.0"?>
        <p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
                       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
        </p:presentation>'''
        mock_zip.read.return_value = valid_xml.encode('utf-8')
        
        with tempfile.NamedTemporaryFile(suffix='.potx') as temp_file:
            result = self.handler.validate_template_structure(temp_file.name, OOXMLFormat.POWERPOINT)
        
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)
    
    @patch('tools.multi_format_ooxml_handler.zipfile.ZipFile')
    def test_validate_template_structure_invalid(self, mock_zipfile):
        """Test template structure validation for invalid template."""
        # Mock invalid template missing required files
        mock_zip = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip
        mock_zip.namelist.return_value = [
            "[Content_Types].xml"  # Missing main document and relationships
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.potx') as temp_file:
            result = self.handler.validate_template_structure(temp_file.name, OOXMLFormat.POWERPOINT)
        
        self.assertFalse(result['valid'])
        self.assertGreater(len(result['errors']), 0)
        self.assertIn("ppt/presentation.xml", result['missing_files'])
    
    @patch('tools.multi_format_ooxml_handler.MultiFormatOOXMLHandler._process_format_specific')
    @patch('tools.multi_format_ooxml_handler.MultiFormatOOXMLHandler.validate_template_structure')
    @patch('tools.multi_format_ooxml_handler.shutil.copy2')
    def test_process_template_success(self, mock_copy, mock_validate, mock_process):
        """Test successful template processing."""
        # Mock validation success
        mock_validate.return_value = {'valid': True, 'errors': [], 'warnings': []}
        
        # Mock processing success
        mock_process.return_value = ProcessingResult(
            success=True,
            format_type=OOXMLFormat.POWERPOINT,
            processed_files=["ppt/presentation.xml"],
            errors=[],
            warnings=[],
            statistics={}
        )
        
        with tempfile.NamedTemporaryFile(suffix='.potx') as temp_file:
            result = self.handler.process_template(
                temp_file.name,
                self.sample_patches,
                variables={'brand_color': 'FF0000'}
            )
        
        self.assertTrue(result.success)
        self.assertEqual(result.format_type, OOXMLFormat.POWERPOINT)
        self.assertIsNotNone(result.output_path)
    
    @patch('tools.multi_format_ooxml_handler.MultiFormatOOXMLHandler.validate_template_structure')
    def test_process_template_validation_failure(self, mock_validate):
        """Test template processing with validation failure."""
        # Mock validation failure
        mock_validate.return_value = {
            'valid': False,
            'errors': ['Missing required file: ppt/presentation.xml'],
            'warnings': []
        }
        
        with tempfile.NamedTemporaryFile(suffix='.potx') as temp_file:
            result = self.handler.process_template(temp_file.name, self.sample_patches)
        
        self.assertFalse(result.success)
        self.assertIn('Template validation failed', result.errors[0])
    
    def test_create_temp_output_path(self):
        """Test temporary output path creation."""
        template_path = Path("test_template.potx")
        output_path = self.handler._create_temp_output_path(template_path, OOXMLFormat.POWERPOINT)
        
        self.assertTrue(output_path.name.startswith("test_template_processed_"))
        self.assertTrue(output_path.name.endswith(".potx"))
    
    def test_register_format_tokens(self):
        """Test format-specific token registration."""
        if not self.handler.enable_token_integration:
            self.skipTest("Token integration not enabled")
        
        token_layer = self.handler.token_layers[OOXMLFormat.POWERPOINT]
        
        # Test token registration
        variables = {'company': 'TestCorp'}
        metadata = {'version': '1.0'}
        
        self.handler._register_format_tokens(
            token_layer, OOXMLFormat.POWERPOINT, variables, metadata
        )
        
        # Verify format-specific tokens were registered
        stats = token_layer.get_resolution_statistics()
        self.assertGreater(stats['registered_tokens_by_scope']['template'], 0)
        self.assertGreater(stats['registered_tokens_by_scope']['document'], 0)
    
    def test_processing_statistics(self):
        """Test processing statistics collection."""
        initial_stats = self.handler.get_processing_statistics()
        
        self.assertEqual(initial_stats['files_processed'], 0)
        self.assertEqual(initial_stats['patches_applied'], 0)
        self.assertEqual(initial_stats['errors_encountered'], 0)
        self.assertIn('potx', initial_stats['formats_processed'])
        
        # Simulate processing
        self.handler.processing_stats['files_processed'] = 5
        self.handler.processing_stats['patches_applied'] = 20
        
        updated_stats = self.handler.get_processing_statistics()
        self.assertEqual(updated_stats['files_processed'], 5)
        self.assertEqual(updated_stats['patches_applied'], 20)
    
    def test_reset_statistics(self):
        """Test statistics reset functionality."""
        # Set some statistics
        self.handler.processing_stats['files_processed'] = 10
        self.handler.processing_stats['patches_applied'] = 50
        
        # Reset statistics
        self.handler.reset_statistics()
        
        stats = self.handler.get_processing_statistics()
        self.assertEqual(stats['files_processed'], 0)
        self.assertEqual(stats['patches_applied'], 0)
    
    @patch('tools.multi_format_ooxml_handler.etree.fromstring')
    @patch('tools.multi_format_ooxml_handler.etree.tostring')
    def test_process_zip_entry(self, mock_tostring, mock_fromstring):
        """Test processing of individual ZIP entries."""
        # Mock XML processing
        mock_doc = MagicMock()
        mock_fromstring.return_value = mock_doc
        mock_tostring.return_value = b'<modified>content</modified>'
        
        # Mock processor
        mock_processor = MagicMock()
        mock_processor.apply_patches.return_value = [
            MagicMock(success=True, error=None, warnings=[])
        ]
        
        # Create a test ZIP file
        with tempfile.NamedTemporaryFile() as temp_file:
            with zipfile.ZipFile(temp_file.name, 'w') as zip_file:
                zip_file.writestr('test.xml', '<original>content</original>')
            
            with zipfile.ZipFile(temp_file.name, 'a') as zip_file:
                result = self.handler._process_zip_entry(
                    zip_file, 'test.xml', self.sample_patches, mock_processor
                )
        
        self.assertEqual(len(result['errors']), 0)
        mock_processor.apply_patches.assert_called_once()
    
    def test_format_specific_processing_structures(self):
        """Test that each format has appropriate processing structure."""
        for format_type in OOXMLFormat:
            structure = self.handler.FORMAT_STRUCTURES[format_type]
            processor = self.handler.processors[format_type]
            
            # Verify structure completeness
            self.assertIsNotNone(structure.main_document_path)
            self.assertIsNotNone(structure.relationships_path)
            self.assertIsNotNone(structure.required_namespaces)
            
            # Verify processor configuration
            self.assertEqual(processor.template_type, format_type.value)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""
    
    def test_create_multi_format_handler(self):
        """Test multi-format handler creation."""
        handler1 = create_multi_format_handler()
        self.assertIsInstance(handler1, MultiFormatOOXMLHandler)
        self.assertTrue(handler1.enable_token_integration)
        
        handler2 = create_multi_format_handler(enable_token_integration=False)
        self.assertFalse(handler2.enable_token_integration)
    
    @patch('tools.multi_format_ooxml_handler.MultiFormatOOXMLHandler.process_template')
    def test_process_ooxml_template(self, mock_process):
        """Test convenience function for template processing."""
        mock_process.return_value = ProcessingResult(
            success=True,
            format_type=OOXMLFormat.POWERPOINT,
            processed_files=[],
            errors=[],
            warnings=[],
            statistics={}
        )
        
        result = process_ooxml_template(
            'test.potx',
            [{'operation': 'set', 'target': '//test', 'value': 'value'}],
            variables={'var': 'value'}
        )
        
        self.assertTrue(result.success)
        mock_process.assert_called_once()


class TestProcessingResult(unittest.TestCase):
    """Test ProcessingResult data structure."""
    
    def test_processing_result_creation(self):
        """Test ProcessingResult creation and defaults."""
        result = ProcessingResult(
            success=True,
            format_type=OOXMLFormat.POWERPOINT,
            processed_files=None,  # Test default handling
            errors=None,
            warnings=None,
            statistics=None
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.format_type, OOXMLFormat.POWERPOINT)
        self.assertEqual(result.processed_files, [])
        self.assertEqual(result.errors, [])
        self.assertEqual(result.warnings, [])
        self.assertEqual(result.statistics, {})
        self.assertIsNone(result.output_path)


if __name__ == "__main__":
    # Run with verbose output for CI
    unittest.main(verbosity=2)