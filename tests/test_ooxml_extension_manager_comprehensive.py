#!/usr/bin/env python3
"""
Comprehensive test suite for OOXML Extension Manager

Tests the core functionality of reading, writing, and managing OOXML <extLst> 
elements for embedding StyleStack variables in Office templates.
"""

import unittest
import tempfile
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))

from tools.ooxml_extension_manager import (
    OOXMLExtensionManager,
    StyleStackExtension, 
    ExtensionMetadata,
    STYLESTACK_EXTENSION_URI,
    OOXML_NAMESPACES
)


class TestExtensionMetadata(unittest.TestCase):
    """Test ExtensionMetadata dataclass"""
    
    def test_extension_metadata_creation(self):
        """Test creating extension metadata"""
        metadata = ExtensionMetadata(
            version="1.0.0",
            author="test_user",
            description="Test extension"
        )
        
        self.assertEqual(metadata.version, "1.0.0")
        self.assertEqual(metadata.author, "test_user")
        self.assertEqual(metadata.description, "Test extension")
        self.assertIsNotNone(metadata.created)
        
    def test_extension_metadata_defaults(self):
        """Test default values for extension metadata"""
        metadata = ExtensionMetadata()
        
        self.assertEqual(metadata.version, "1.0")
        self.assertIsNone(metadata.author)
        self.assertIsNone(metadata.description)
        self.assertIsNotNone(metadata.created)


class TestStyleStackExtension(unittest.TestCase):
    """Test StyleStackExtension dataclass"""
    
    def setUp(self):
        """Set up test data"""
        self.sample_variables = [
            {
                'id': 'brandPrimary',
                'type': 'color',
                'scope': 'org',
                'value': '#FF0000'
            },
            {
                'id': 'headingFont',
                'type': 'font',
                'scope': 'channel',
                'value': 'Arial Black'
            }
        ]
        
    def test_stylestack_extension_creation(self):
        """Test creating StyleStack extension"""
        extension = StyleStackExtension(
            uri=STYLESTACK_EXTENSION_URI,
            variables=self.sample_variables
        )
        
        self.assertEqual(extension.uri, STYLESTACK_EXTENSION_URI)
        self.assertEqual(len(extension.variables), 2)
        self.assertEqual(extension.variables[0]['id'], 'brandPrimary')
        self.assertIsInstance(extension.metadata, ExtensionMetadata)
        
    def test_stylestack_extension_defaults(self):
        """Test default values for StyleStack extension"""
        extension = StyleStackExtension()
        
        self.assertEqual(extension.uri, STYLESTACK_EXTENSION_URI)
        self.assertEqual(extension.variables, [])
        self.assertIsInstance(extension.metadata, ExtensionMetadata)
        
    def test_to_dict_conversion(self):
        """Test converting extension to dictionary"""
        extension = StyleStackExtension(
            uri=STYLESTACK_EXTENSION_URI,
            variables=self.sample_variables
        )
        
        extension_dict = extension.to_dict()
        
        self.assertIn('uri', extension_dict)
        self.assertIn('variables', extension_dict)
        self.assertIn('metadata', extension_dict)
        self.assertEqual(extension_dict['uri'], STYLESTACK_EXTENSION_URI)
        self.assertEqual(len(extension_dict['variables']), 2)
        
    def test_from_dict_creation(self):
        """Test creating extension from dictionary"""
        extension_dict = {
            'uri': STYLESTACK_EXTENSION_URI,
            'variables': self.sample_variables,
            'metadata': {
                'version': '2.0.0',
                'created_by': 'test_suite',
                'description': 'Test extension from dict'
            }
        }
        
        extension = StyleStackExtension.from_dict(extension_dict)
        
        self.assertEqual(extension.uri, STYLESTACK_EXTENSION_URI)
        self.assertEqual(len(extension.variables), 2)
        self.assertEqual(extension.metadata.version, '2.0.0')
        self.assertEqual(extension.metadata.created_by, 'test_suite')


class TestOOXMLExtensionManager(unittest.TestCase):
    """Test OOXMLExtensionManager core functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.manager = OOXMLExtensionManager()
        
        # Sample OOXML theme with existing extensions
        self.sample_theme_with_extensions = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Test Theme">
          <a:themeElements>
            <a:clrScheme name="Test Colors">
              <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
              <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
            </a:clrScheme>
          </a:themeElements>
          <a:extLst>
            <a:ext uri="{StyleStack-12345678-1234-1234-1234-123456789012}">
              <ss:variables xmlns:ss="http://stylestack.io/variables">
                <ss:variable id="brandPrimary" type="color" scope="org" value="#FF0000"/>
              </ss:variables>
            </a:ext>
          </a:extLst>
        </a:theme>'''
        
        # Sample OOXML theme without extensions
        self.sample_theme_no_extensions = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Test Theme">
          <a:themeElements>
            <a:clrScheme name="Test Colors">
              <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
              <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
            </a:clrScheme>
          </a:themeElements>
        </a:theme>'''
        
        # Sample variables for testing
        self.sample_variables = [
            {
                'id': 'brandPrimary',
                'type': 'color',
                'scope': 'org',
                'value': '#FF0000'
            },
            {
                'id': 'headingFont', 
                'type': 'font',
                'scope': 'channel',
                'value': 'Arial Black'
            }
        ]
        
    def test_manager_initialization(self):
        """Test OOXMLExtensionManager initialization"""
        manager = OOXMLExtensionManager()
        
        # Check that manager is initialized properly
        self.assertIsInstance(manager, OOXMLExtensionManager)
        
    def test_read_extensions_from_xml_with_extensions(self):
        """Test reading extensions from XML with existing extensions"""
        extensions = self.manager.read_extensions_from_xml(self.sample_theme_with_extensions)
        
        self.assertIsInstance(extensions, list)
        self.assertGreater(len(extensions), 0)
        
        # Check first extension
        if extensions:
            extension = extensions[0]
            self.assertIsInstance(extension, StyleStackExtension)
            
    def test_read_extensions_from_xml_no_extensions(self):
        """Test reading extensions from XML without extensions"""
        extensions = self.manager.read_extensions_from_xml(self.sample_theme_no_extensions)
        
        self.assertIsInstance(extensions, list)
        self.assertEqual(len(extensions), 0)
        
    def test_write_extension_to_xml_new_extension(self):
        """Test writing new extension to XML"""
        extension = StyleStackExtension(
            uri=STYLESTACK_EXTENSION_URI,
            variables=self.sample_variables
        )
        
        updated_xml = self.manager.write_extension_to_xml(
            self.sample_theme_no_extensions, 
            extension
        )
        
        self.assertIsInstance(updated_xml, str)
        self.assertIn('extLst', updated_xml)
        self.assertIn(STYLESTACK_EXTENSION_URI, updated_xml)
        
    def test_write_extension_to_xml_update_existing(self):
        """Test updating existing extension in XML"""
        new_variables = [
            {
                'id': 'newVariable',
                'type': 'text',
                'scope': 'template',
                'value': 'New Value'
            }
        ]
        
        extension = StyleStackExtension(
            uri=STYLESTACK_EXTENSION_URI,
            variables=new_variables
        )
        
        updated_xml = self.manager.write_extension_to_xml(
            self.sample_theme_with_extensions,
            extension
        )
        
        self.assertIsInstance(updated_xml, str)
        self.assertIn('newVariable', updated_xml)
        
    def test_remove_extension_from_xml(self):
        """Test removing extension from XML"""
        updated_xml = self.manager.remove_extension_from_xml(
            self.sample_theme_with_extensions,
            STYLESTACK_EXTENSION_URI
        )
        
        self.assertIsInstance(updated_xml, str)
        self.assertNotIn(STYLESTACK_EXTENSION_URI, updated_xml)
        
    def test_xml_parsing_error_handling(self):
        """Test handling of malformed XML"""
        malformed_xml = '''<?xml version="1.0"?><invalid>xml</content>'''
        
        # Should handle errors gracefully
        extensions = self.manager.read_extensions_from_xml(malformed_xml)
        self.assertEqual(extensions, [])
        
    def test_namespace_handling(self):
        """Test proper OOXML namespace handling"""
        self.assertIn('a', OOXML_NAMESPACES)
        self.assertIn('http://schemas.openxmlformats.org/drawingml/2006/main', 
                     OOXML_NAMESPACES['a'])
        
    def test_extension_uri_validation(self):
        """Test StyleStack extension URI format"""
        self.assertTrue(STYLESTACK_EXTENSION_URI.startswith('http://stylestack.io/'))
        
    def test_variables_validation(self):
        """Test variables structure validation"""
        extension = StyleStackExtension(
            uri=STYLESTACK_EXTENSION_URI,
            variables=self.sample_variables
        )
        
        for var in extension.variables:
            self.assertIn('id', var)
            self.assertIn('type', var) 
            self.assertIn('scope', var)
            self.assertIn('value', var)


class TestOOXMLExtensionManagerEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        """Set up test environment"""
        self.manager = OOXMLExtensionManager()
        
    def test_empty_xml_handling(self):
        """Test handling of empty XML"""
        extensions = self.manager.read_extensions_from_xml("")
        self.assertEqual(extensions, [])
        
    def test_none_xml_handling(self):
        """Test handling of None XML input"""
        extensions = self.manager.read_extensions_from_xml(None)
        self.assertEqual(extensions, [])
        
    def test_invalid_uri_handling(self):
        """Test handling of invalid URIs"""
        extension = StyleStackExtension(
            uri="invalid-uri",
            variables=[]
        )
        
        # Should still work but may generate warnings
        self.assertEqual(extension.uri, "invalid-uri")
        
    def test_large_variable_list(self):
        """Test handling of large variable lists"""
        large_variables = [
            {
                'id': f'var_{i}',
                'type': 'text',
                'scope': 'template',
                'value': f'Value {i}'
            }
            for i in range(100)
        ]
        
        extension = StyleStackExtension(
            uri=STYLESTACK_EXTENSION_URI,
            variables=large_variables
        )
        
        self.assertEqual(len(extension.variables), 100)
        
    def test_unicode_handling(self):
        """Test handling of Unicode characters in variables"""
        unicode_variables = [
            {
                'id': 'unicodeVar',
                'type': 'text',
                'scope': 'template', 
                'value': '测试 Unicode 🎨'
            }
        ]
        
        extension = StyleStackExtension(
            uri=STYLESTACK_EXTENSION_URI,
            variables=unicode_variables
        )
        
        self.assertEqual(extension.variables[0]['value'], '测试 Unicode 🎨')


if __name__ == '__main__':
    unittest.main()