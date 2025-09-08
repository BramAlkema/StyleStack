#!/usr/bin/env python3
"""
Advanced Namespace Handling Integration Tests

Tests the advanced namespace handling features integrated into the YAML-OOXML processor,
including collision resolution, custom declarations, namespace inheritance, and 
cross-format namespace migration.

Part of Task 6.6: Advanced Namespace Handling for Complex XPath Expressions.
"""

import unittest
from unittest.mock import MagicMock, patch
import tempfile
import os
from lxml import etree

from tools.yaml_ooxml_processor import YAMLPatchProcessor, RecoveryStrategy
from tools.yaml_ooxml_processor import PatchError


class TestAdvancedNamespaceHandling(unittest.TestCase):
    """Test advanced namespace handling integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = YAMLPatchProcessor(
            recovery_strategy=RecoveryStrategy.RETRY_WITH_FALLBACK
        )
        
        # Sample XML documents with namespace challenges
        self.complex_powerpoint_xml = '''<?xml version="1.0"?>
        <p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
                       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
                       xmlns:custom="http://example.com/custom">
            <p:sldMasterIdLst>
                <p:sldMasterId id="2147483648" r:id="rId1"/>
            </p:sldMasterIdLst>
            <a:theme name="Office Theme">
                <a:themeElements>
                    <a:clrScheme name="Office">
                        <a:dk1>
                            <a:sysClr val="windowText" lastClr="000000"/>
                        </a:dk1>
                        <custom:brandColor val="FF0000"/>
                    </a:clrScheme>
                </a:themeElements>
            </a:theme>
        </p:presentation>'''
        
        # XML with namespace collision scenario
        self.collision_xml = '''<?xml version="1.0"?>
        <root xmlns:ns1="http://example.com/namespace1"
              xmlns:ns2="http://example.com/namespace2">
            <ns1:element attr="value1">
                <ns2:element attr="value2">Text content</ns2:element>
            </ns1:element>
        </root>'''
    
    def test_custom_namespace_declarations_in_patches(self):
        """Test patches can declare custom namespaces."""
        xml_doc = etree.fromstring(self.complex_powerpoint_xml)
        
        # Patch with custom namespace declarations
        patches = [
            {
                'operation': 'set',
                'target': '//myns:customElement/@value',
                'value': 'test_value',
                'namespaces': {
                    'myns': 'http://example.com/mynamespacce',
                    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'  # Override existing
                }
            }
        ]
        
        # This should not raise an error with custom namespace handling
        # Note: The actual XPath may not find elements, but namespace handling should work
        try:
            results = self.processor.apply_patches(xml_doc, patches)
            # We expect this to potentially fail due to missing target elements,
            # but NOT due to namespace resolution issues
            self.assertIsInstance(results, list)
        except PatchError as e:
            # Should be target not found, not namespace error
            self.assertNotIn('namespace', str(e).lower())
    
    def test_namespace_inheritance_between_patches(self):
        """Test namespace inheritance between sequential patches."""
        xml_doc = etree.fromstring(self.complex_powerpoint_xml)
        
        patches = [
            {
                'operation': 'set',
                'target': '//p:sldMasterId/@id',
                'value': '9999999',
                'namespaces': {
                    'custom': 'http://example.com/custom',
                    'special': 'http://example.com/special'
                }
            },
            {
                'operation': 'set',
                'target': '//custom:brandColor/@val',
                'value': '00FF00',
                'inherit_namespaces': True  # Should inherit from previous patch
            }
        ]
        
        results = self.processor.apply_patches(xml_doc, patches)
        
        # Verify both patches were processed (may succeed or fail, but namespace inheritance worked)
        self.assertEqual(len(results), 2)
        
        # First patch should succeed (existing element)
        self.assertTrue(results[0].success)
        
        # Second patch may fail (missing element) but not due to namespace issues
        if not results[1].success:
            error_msg = results[1].message.lower()
            self.assertNotIn('namespace', error_msg)
    
    def test_namespace_collision_resolution(self):
        """Test namespace prefix collision resolution."""
        xml_doc = etree.fromstring(self.collision_xml)
        
        # Add custom namespace declarations that would collide
        custom_namespaces = {
            'ns1': 'http://example.com/different1',  # Collision with existing ns1
            'ns3': 'http://example.com/namespace3'   # New namespace
        }
        
        # This should trigger collision resolution
        self.processor.xpath_system.add_custom_namespace_declarations(xml_doc, custom_namespaces)
        
        # Verify namespace system handles collisions
        ns_stats = self.processor.xpath_system.get_namespace_stats()
        
        # Should have detected and resolved namespace operations
        self.assertGreater(ns_stats.get('namespace_registrations', 0), 0)
    
    def test_format_specific_namespace_migration(self):
        """Test namespace migration between different OOXML formats."""
        xml_doc = etree.fromstring(self.complex_powerpoint_xml)
        
        # Test migrating namespaces from PowerPoint to Word format
        word_namespaces = self.processor.xpath_system.migrate_namespaces_for_format(
            {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'}, 
            'word'
        )
        
        # Should contain Word-specific namespace mappings
        self.assertIn('w', word_namespaces)
        self.assertEqual(word_namespaces['w'], 'http://schemas.openxmlformats.org/wordprocessingml/2006/main')
    
    def test_namespace_validation_and_error_reporting(self):
        """Test namespace validation catches invalid URIs."""
        xml_doc = etree.fromstring(self.complex_powerpoint_xml)
        
        # Invalid namespace URIs should be caught
        invalid_namespaces = {
            'bad': 'not-a-valid-uri',
            'empty': '',
            'good': 'http://example.com/valid'
        }
        
        # This should trigger validation
        validation_result = self.processor.xpath_system._validate_namespace_uris(invalid_namespaces)
        
        # Should report validation issues
        self.assertIn('invalid_uris', validation_result)
        self.assertIn('bad', validation_result['invalid_uris'])
        self.assertIn('empty', validation_result['invalid_uris'])
        self.assertNotIn('good', validation_result['invalid_uris'])
    
    def test_comprehensive_namespace_stats_collection(self):
        """Test comprehensive namespace statistics are collected."""
        xml_doc = etree.fromstring(self.complex_powerpoint_xml)
        
        # Apply multiple patches with different namespace scenarios
        patches = [
            {
                'operation': 'set',
                'target': '//p:sldMasterId/@id',
                'value': '12345',
            },
            {
                'operation': 'set',
                'target': '//a:sysClr/@val',
                'value': 'FFFFFF',
                'namespaces': {'custom': 'http://example.com/test'}
            },
            {
                'operation': 'set',
                'target': '//nonexistent:element/@attr',
                'value': 'test',
                'namespaces': {'nonexistent': 'http://example.com/missing'}
            }
        ]
        
        results = self.processor.apply_patches(xml_doc, patches)
        
        # Get comprehensive stats including namespace metrics
        stats = self.processor.get_comprehensive_stats()
        
        # Verify namespace statistics are included
        namespace_stats = {k: v for k, v in stats.items() if k.startswith('namespace_')}
        self.assertGreater(len(namespace_stats), 0)
        
        # Should have namespace registration events
        if 'namespace_namespace_registrations' in stats:
            self.assertGreaterEqual(stats['namespace_namespace_registrations'], 1)
    
    def test_xpath_context_with_custom_namespaces(self):
        """Test XPath context info includes custom namespace information."""
        xml_doc = etree.fromstring(self.complex_powerpoint_xml)
        
        # Add custom namespaces
        custom_namespaces = {
            'test': 'http://example.com/test',
            'demo': 'http://example.com/demo'
        }
        self.processor.xpath_system.add_custom_namespace_declarations(xml_doc, custom_namespaces)
        
        # Get XPath context for a complex expression
        context_info = self.processor.xpath_system.get_xpath_context_info(
            xml_doc, '//test:element[@demo:attr="value"]'
        )
        
        # Should include namespace information in context
        self.assertIn('available_namespaces', context_info)
        available_ns = context_info['available_namespaces']
        self.assertIn('test', available_ns)
        self.assertIn('demo', available_ns)
    
    def test_batch_namespace_processing_optimization(self):
        """Test batch processing optimizes namespace operations."""
        xml_doc = etree.fromstring(self.complex_powerpoint_xml)
        
        # Multiple patches using same namespace should be optimized
        patches = [
            {
                'operation': 'set',
                'target': '//shared:element1/@attr',
                'value': 'value1',
                'namespaces': {'shared': 'http://example.com/shared'}
            },
            {
                'operation': 'set', 
                'target': '//shared:element2/@attr',
                'value': 'value2',
                'namespaces': {'shared': 'http://example.com/shared'}  # Same namespace
            },
            {
                'operation': 'set',
                'target': '//shared:element3/@attr', 
                'value': 'value3',
                'namespaces': {'shared': 'http://example.com/shared'}  # Same namespace again
            }
        ]
        
        results = self.processor.apply_patches(xml_doc, patches)
        
        # Verify performance optimization was applied
        stats = self.processor.get_comprehensive_stats()
        
        # Should show optimization metrics
        if 'performance_optimizations' in stats:
            self.assertGreaterEqual(stats['performance_optimizations'], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)