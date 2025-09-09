"""
Test suite for YAML-to-OOXML Patch Operations Engine (Modern Interface)

Tests the core XPath-based OOXML manipulation system that applies YAML patches
to Office template files (.potx, .dotx, .xltx) using the new modular interface.
"""

import unittest
import tempfile
import zipfile
import os
from pathlib import Path
from lxml import etree
from tools.processing.yaml import YAMLPatchProcessor
from tools.core.types import PatchOperation, PatchError, PatchOperationType


class TestYAMLPatchProcessor(unittest.TestCase):
    """Test the core YAML patch processing functionality with modern interface."""
    
    def setUp(self):
        """Set up test environment with sample OOXML content."""
        self.processor = YAMLPatchProcessor()
        
        # Sample PowerPoint slide XML for testing
        self.sample_slide_xml = """<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" 
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" 
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
    <p:cSld>
        <p:spTree>
            <p:sp>
                <p:txBody>
                    <a:p>
                        <a:r>
                            <a:rPr lang="en-US" sz="4400">
                                <a:solidFill>
                                    <a:srgbClr val="000000"/>
                                </a:solidFill>
                            </a:rPr>
                            <a:t>Sample Title</a:t>
                        </a:r>
                    </a:p>
                </p:txBody>
            </p:sp>
        </p:spTree>
    </p:cSld>
</p:sld>"""
    
    def _create_patch_operation(self, patch_dict):
        """Helper to convert patch dict to PatchOperation."""
        return PatchOperation.from_dict({
            'operation': patch_dict.get('op', 'set'),
            'target': patch_dict.get('xpath', ''),
            'value': patch_dict.get('value')
        })
    
    def _create_patch_operations(self, patch_dicts):
        """Helper to convert list of patch dicts to PatchOperation objects."""
        return [self._create_patch_operation(patch) for patch in patch_dicts]

    def test_set_operation_basic(self):
        """Test basic set operation on XML element."""
        xml_doc = etree.fromstring(self.sample_slide_xml)
        
        patch = {
            'op': 'set',
            'xpath': '//a:t',
            'value': 'New Title'
        }
        
        patch_operation = self._create_patch_operation(patch)
        namespaces = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
        result = self.processor._process_single_patch(xml_doc, patch_operation, namespaces)
        
        self.assertTrue(result.success)
        
        # Verify the change was applied
        title_text = xml_doc.xpath('//a:t/text()', namespaces={
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
        })[0]
        self.assertEqual(title_text, 'New Title')

    def test_set_operation_different_element(self):
        """Test set operation on a different element path."""
        # Create a more complex XML for this test
        complex_xml = """<root xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
    <section>
        <a:title>Original Title</a:title>
        <a:content>Original Content</a:content>
    </section>
</root>"""
        xml_doc = etree.fromstring(complex_xml)
        
        patch = {
            'op': 'set',
            'xpath': '//a:content',
            'value': 'Updated Content'
        }
        
        patch_operation = self._create_patch_operation(patch)
        namespaces = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
        result = self.processor._process_single_patch(xml_doc, patch_operation, namespaces)
        
        self.assertTrue(result.success)
        
        # Verify the content was changed
        content_text = xml_doc.xpath('//a:content/text()', namespaces={
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
        })[0]
        self.assertEqual(content_text, 'Updated Content')

    def test_batch_patch_application(self):
        """Test applying multiple patches in sequence."""
        xml_doc = etree.fromstring(self.sample_slide_xml)
        
        patches = [
            {
                'op': 'set',
                'xpath': '//a:t',
                'value': 'Updated Title'
            }
        ]
        
        patch_operations = self._create_patch_operations(patches)
        namespaces = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
        results = self.processor.process_patches(xml_doc, patch_operations, namespaces)
        
        # Verify all patches were applied
        self.assertEqual(len(results), 1)
        for result in results:
            self.assertTrue(result.success)
        
        # Verify final state
        text = xml_doc.xpath('//a:t/text()', namespaces={
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
        })[0]
        
        self.assertEqual(text, 'Updated Title')

    def test_invalid_xpath_handling(self):
        """Test error handling for invalid XPath expressions."""
        xml_doc = etree.fromstring(self.sample_slide_xml)
        
        invalid_patch = {
            'op': 'set',
            'xpath': '//invalid[xpath[',
            'value': 'test'
        }
        
        patch_operation = self._create_patch_operation(invalid_patch)
        result = self.processor._process_single_patch(xml_doc, patch_operation, {})
        
        self.assertFalse(result.success)
        self.assertIn('Invalid expression', result.message)


class TestPatchOperation(unittest.TestCase):
    """Test PatchOperation data structure."""
    
    def test_patch_operation_creation(self):
        """Test creating PatchOperation objects."""
        operation = PatchOperation.from_dict({
            'operation': 'set',
            'target': '//test',
            'value': 'test_value'
        })
        
        self.assertEqual(operation.operation, 'set')
        self.assertEqual(operation.target, '//test')
        self.assertEqual(operation.value, 'test_value')

    def test_patch_operation_optional_fields(self):
        """Test PatchOperation with optional fields."""
        operation = PatchOperation.from_dict({
            'operation': 'set',
            'target': '//test',
            'value': 'test_value'
        })
        
        self.assertEqual(operation.operation, 'set')
        self.assertEqual(operation.target, '//test')
        self.assertEqual(operation.value, 'test_value')


if __name__ == '__main__':
    unittest.main()