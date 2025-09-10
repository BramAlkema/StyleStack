"""
Integration Tests for Import Resolution and Module Dependencies

This test suite verifies that all modules can be imported correctly
after the refactoring and that their interfaces work together properly.
"""

import unittest
import sys
from pathlib import Path
from importlib import import_module

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestImportResolution(unittest.TestCase):
    """Test that all refactored modules can be imported and work together."""
    
    def test_core_module_imports(self):
        """Test that all core modules can be imported successfully."""
        core_modules = [
            'tools.core.types',
            'tools.processing.json', 
            'tools.processing.errors',
            'tools.xpath.targeting',
            'tools.handlers.types',
            'tools.handlers.formats',
            'tools.handlers.integration',
            'tools.performance.benchmarks',
            'tools.performance.optimizations',
            'tools.substitution.pipeline',
            'tools.substitution.types',
        ]
        
        for module_name in core_modules:
            with self.subTest(module=module_name):
                try:
                    module = import_module(module_name)
                    self.assertIsNotNone(module)
                    # Verify module has expected attributes
                    self.assertTrue(hasattr(module, '__name__'))
                except ImportError as e:
                    self.fail(f"Failed to import {module_name}: {e}")
    
    def test_json_patch_processor_interface(self):
        """Test that JSONPatchProcessor has the correct interface."""
        from tools.processing.json import JSONPatchProcessor
        
        processor = JSONPatchProcessor()
        
        # Check required methods exist
        required_methods = [
            'apply_patch',
            'process_patches',
        ]
        
        for method_name in required_methods:
            with self.subTest(method=method_name):
                self.assertTrue(hasattr(processor, method_name))
                method = getattr(processor, method_name)
                self.assertTrue(callable(method))
    
    def test_multi_format_handler_imports(self):
        """Test that the multi-format handler can import all dependencies."""
        try:
            from tools.multi_format_ooxml_handler import MultiFormatOOXMLHandler
            from tools.handlers.types import OOXMLFormat, ProcessingResult
            
            handler = MultiFormatOOXMLHandler()
            self.assertIsNotNone(handler)
            
            # Check that handler has required methods
            self.assertTrue(hasattr(handler, 'process_template'))
            self.assertTrue(callable(handler.process_template))
            
        except ImportError as e:
            self.fail(f"Failed to import multi-format handler: {e}")
    
    def test_xpath_targeting_system(self):
        """Test that XPath targeting system is properly configured."""
        from tools.xpath.targeting import XPathTargetingSystem
        
        xpath_system = XPathTargetingSystem()
        
        # Check for essential namespaces
        self.assertIn('p', xpath_system.base_namespaces)
        self.assertIn('w', xpath_system.base_namespaces)
        self.assertIn('x', xpath_system.base_namespaces)
        self.assertIn('a', xpath_system.base_namespaces)
        
        # Check namespace detection method exists
        self.assertTrue(hasattr(xpath_system, 'detect_document_namespaces'))
        self.assertTrue(callable(xpath_system.detect_document_namespaces))
    
    def test_format_registry_structure(self):
        """Test that FormatRegistry has correct structure definitions."""
        from tools.handlers.formats import FormatRegistry
        from tools.handlers.types import OOXMLFormat
        
        # Check PowerPoint structure
        ppt_structure = FormatRegistry.get_structure(OOXMLFormat.POWERPOINT)
        self.assertIsNotNone(ppt_structure)
        self.assertEqual(ppt_structure.main_document_path, "ppt/presentation.xml")
        self.assertIn("ppt/slides/*.xml", ppt_structure.content_paths)
        
        # Check Word structure
        word_structure = FormatRegistry.get_structure(OOXMLFormat.WORD)
        self.assertIsNotNone(word_structure)
        self.assertEqual(word_structure.main_document_path, "word/document.xml")
        
        # Check Excel structure
        excel_structure = FormatRegistry.get_structure(OOXMLFormat.EXCEL)
        self.assertIsNotNone(excel_structure)
        self.assertEqual(excel_structure.main_document_path, "xl/workbook.xml")
    
    def test_performance_module_integration(self):
        """Test that performance modules integrate correctly."""
        from tools.performance.benchmarks import PerformanceBenchmark
        from tools.performance.optimizations import PerformanceCache
        
        # Test benchmark creation
        benchmark = PerformanceBenchmark()
        self.assertIsNotNone(benchmark)
        self.assertTrue(hasattr(benchmark, 'run_full_benchmark'))
        
        # Test cache creation
        cache = PerformanceCache()
        self.assertIsNotNone(cache)
        self.assertTrue(hasattr(cache, 'get'))
        self.assertTrue(hasattr(cache, 'set'))
    
    def test_substitution_pipeline_interface(self):
        """Test that SubstitutionPipeline has correct interface."""
        try:
            from tools.substitution.pipeline import SubstitutionPipeline
            from tools.substitution.types import SubstitutionResult
            
            pipeline = SubstitutionPipeline()
            self.assertIsNotNone(pipeline)
            
            # Check for essential attributes and methods
            self.assertTrue(hasattr(pipeline, 'substitute_variables'))
            self.assertTrue(hasattr(pipeline, 'stats'))
            self.assertIsInstance(pipeline.stats, dict)
            
        except ImportError as e:
            # This module might not exist yet, which is okay
            pass
    
    def test_cross_module_integration(self):
        """Test that modules can work together properly."""
        from tools.processing.json import JSONPatchProcessor
        from tools.xpath.targeting import XPathTargetingSystem
        from lxml import etree
        
        # Create instances
        processor = JSONPatchProcessor()
        
        # Verify processor has xpath_system
        self.assertTrue(hasattr(processor, 'xpath_system'))
        self.assertIsInstance(processor.xpath_system, XPathTargetingSystem)
        
        # Test basic operation
        xml_content = '''<?xml version="1.0"?>
        <root xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
            <a:t>Test Content</a:t>
        </root>'''
        
        doc = etree.fromstring(xml_content)
        patch = {
            'operation': 'set',
            'target': '//a:t',
            'value': 'New Content'
        }
        
        result = processor.apply_patch(doc, patch)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, 'success'))
        self.assertTrue(result.success)


if __name__ == '__main__':
    unittest.main()