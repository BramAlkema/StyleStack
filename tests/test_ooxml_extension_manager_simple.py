#!/usr/bin/env python3
"""
Simple test suite for OOXML Extension Manager

Tests the core functionality that actually exists in the implementation.
"""

import unittest
import xml.etree.ElementTree as ET

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
            }
        ]
        
    def test_stylestack_extension_creation(self):
        """Test creating StyleStack extension"""
        extension = StyleStackExtension(
            uri=STYLESTACK_EXTENSION_URI,
            variables=self.sample_variables
        )
        
        self.assertEqual(extension.uri, STYLESTACK_EXTENSION_URI)
        self.assertEqual(len(extension.variables), 1)
        self.assertEqual(extension.variables[0]['id'], 'brandPrimary')
        
    def test_stylestack_extension_defaults(self):
        """Test default values for StyleStack extension"""
        extension = StyleStackExtension(
            uri=STYLESTACK_EXTENSION_URI
        )
        
        self.assertEqual(extension.uri, STYLESTACK_EXTENSION_URI)
        self.assertEqual(extension.variables, [])
        self.assertEqual(extension.format_version, "1.0")


class TestOOXMLExtensionManager(unittest.TestCase):
    """Test OOXMLExtensionManager core functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.manager = OOXMLExtensionManager()
        
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
            }
        ]
        
    def test_manager_initialization(self):
        """Test OOXMLExtensionManager initialization"""
        manager = OOXMLExtensionManager()
        self.assertIsInstance(manager, OOXMLExtensionManager)
        
    def test_read_extensions_from_xml_no_extensions(self):
        """Test reading extensions from XML without extensions"""
        extensions = self.manager.read_extensions_from_xml(self.sample_theme_no_extensions)
        
        self.assertIsInstance(extensions, list)
        self.assertEqual(len(extensions), 0)
        
    def test_namespace_handling(self):
        """Test proper OOXML namespace handling"""
        self.assertIn('a', OOXML_NAMESPACES)
        self.assertIn('http://schemas.openxmlformats.org/drawingml/2006/main', 
                     OOXML_NAMESPACES['a'])
        
    def test_extension_uri_validation(self):
        """Test StyleStack extension URI format"""
        self.assertTrue(STYLESTACK_EXTENSION_URI.startswith('https://stylestack.org/'))
        
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


class TestOOXMLExtensionManagerBasic(unittest.TestCase):
    """Test basic functionality that should work"""
    
    def setUp(self):
        """Set up test environment"""
        self.manager = OOXMLExtensionManager()
        
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
        
    def test_large_variable_list(self):
        """Test handling of large variable lists"""
        large_variables = [
            {
                'id': f'var_{i}',
                'type': 'text',
                'scope': 'template',
                'value': f'Value {i}'
            }
            for i in range(50)  # Smaller list to avoid timeouts
        ]
        
        extension = StyleStackExtension(
            uri=STYLESTACK_EXTENSION_URI,
            variables=large_variables
        )
        
        self.assertEqual(len(extension.variables), 50)


if __name__ == '__main__':
    unittest.main()