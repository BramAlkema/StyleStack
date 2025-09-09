"""
Test suite for Patch Execution Engine.

Tests comprehensive execution, coordination, and orchestration capabilities
for the JSON-to-OOXML patch processing system.

IMPORTANT: Always run tests using venv:
    source .venv/bin/activate && python tests/test_patch_execution_engine.py
    OR: .venv/bin/python tests/test_patch_execution_engine.py
"""

import unittest
import tempfile
from pathlib import Path
from lxml import etree

from tools.patch_execution_engine import (
    PatchExecutionEngine, ExecutionMode, ExecutionContext,
    execute_patch_file, execute_patch_content
)
from tools.json_patch_parser import ValidationLevel


class TestPatchExecutionEngine(unittest.TestCase):
    """Test cases for patch execution engine functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.engine = PatchExecutionEngine(ValidationLevel.LENIENT)
        
        # Sample OOXML document for testing
        self.sample_xml = """<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" 
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
                </a:xfrm>
            </p:grpSpPr>
            <p:sp>
                <p:spPr>
                    <a:solidFill>
                        <a:srgbClr val="FF0000"/>
                    </a:solidFill>
                </p:spPr>
            </p:sp>
        </p:spTree>
    </p:cSld>
</p:sld>"""
    
    def test_execute_patch_content_normal_mode(self):
        """Test executing patch content in normal mode."""
        xml_doc = etree.fromstring(self.sample_xml)
        
        patch_content = """{
  "metadata": {
    "version": "1.0",
    "description": "Change color to green"
  },
  "targets": [
    {
      "file": "slide.xml",
      "ops": [
        {
          "set": {
            "xpath": "//a:srgbClr/@val",
            "value": "00FF00"
          }
        }
      ]
    }
  ]
}"""
        
        result = self.engine.execute_patch_content(patch_content, xml_doc, ExecutionMode.NORMAL)
        
        self.assertTrue(result.success)
        self.assertFalse(result.dry_run)
        self.assertEqual(len(result.patch_results), 1)
        self.assertTrue(result.patch_results[0].success)
        self.assertIsNotNone(result.modified_document)
        
        # Verify the color was actually changed
        modified_color = result.modified_document.xpath('//a:srgbClr/@val', namespaces={
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
        })
        self.assertEqual(modified_color[0], '00FF00')
    
    def test_execute_patch_content_dry_run_mode(self):
        """Test executing patch content in dry-run mode."""
        xml_doc = etree.fromstring(self.sample_xml)
        
        patch_content = """
patches:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "0066CC"
"""
        
        result = self.engine.execute_patch_content(patch_content, xml_doc, ExecutionMode.DRY_RUN)
        
        self.assertTrue(result.success)
        self.assertTrue(result.dry_run)
        self.assertEqual(len(result.patch_results), 1)
        self.assertTrue(result.patch_results[0].success)
        self.assertIsNone(result.modified_document)  # No document returned in dry-run
        
        # Original document should be unchanged
        original_color = xml_doc.xpath('//a:srgbClr/@val', namespaces={
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
        })
        self.assertEqual(original_color[0], 'FF0000')  # Still original color
    
    def test_execute_patch_content_validate_only_mode(self):
        """Test executing patch content in validate-only mode."""
        xml_doc = etree.fromstring(self.sample_xml)
        
        patch_content = """
patches:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "336699"
  - operation: set
    target: "//invalid:xpath"
    value: "test"
"""
        
        result = self.engine.execute_patch_content(patch_content, xml_doc, ExecutionMode.VALIDATE_ONLY)
        
        self.assertFalse(result.success)  # Should fail due to invalid XPath
        self.assertFalse(result.dry_run)
        self.assertEqual(len(result.patch_results), 2)
        self.assertTrue(result.patch_results[0].success)   # First patch valid
        self.assertFalse(result.patch_results[1].success)  # Second patch invalid
        self.assertIsNone(result.modified_document)
    
    def test_multiple_patches_execution(self):
        """Test executing multiple patches in sequence."""
        xml_doc = etree.fromstring(self.sample_xml)
        
        patch_content = """
patches:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "00FF00"
  - operation: set
    target: "//p:cNvPr/@name"
    value: "Updated Shape"
  - operation: set
    target: "//a:off/@x"
    value: "100"
"""
        
        result = self.engine.execute_patch_content(patch_content, xml_doc, ExecutionMode.NORMAL)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.patch_results), 3)
        self.assertTrue(all(patch.success for patch in result.patch_results))
        
        # Verify all changes were applied
        modified_doc = result.modified_document
        namespaces = {
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
            'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'
        }
        
        color = modified_doc.xpath('//a:srgbClr/@val', namespaces=namespaces)[0]
        name = modified_doc.xpath('//p:cNvPr/@name', namespaces=namespaces)[0]
        x_pos = modified_doc.xpath('//a:off/@x', namespaces=namespaces)[0]
        
        self.assertEqual(color, '00FF00')
        self.assertEqual(name, 'Updated Shape')
        self.assertEqual(x_pos, '100')
    
    def test_execution_context_variables(self):
        """Test execution context variable handling."""
        xml_doc = etree.fromstring(self.sample_xml)
        
        patch_content = """
variables:
  brand_color: "0066CC"
  shape_name: "Corporate Logo"
  
patches:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "${brand_color}"
  - operation: set
    target: "//p:cNvPr/@name"
    value: "${shape_name}"
"""
        
        result = self.engine.execute_patch_content(patch_content, xml_doc, ExecutionMode.NORMAL)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.patch_results), 2)
        
        # Check that variables were applied to context
        self.assertIn('brand_color', result.execution_context.variables)
        self.assertEqual(result.execution_context.variables['brand_color'], '0066CC')
        
        # Verify substituted values were applied
        modified_doc = result.modified_document
        namespaces = {
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
            'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'
        }
        
        color = modified_doc.xpath('//a:srgbClr/@val', namespaces=namespaces)[0]
        name = modified_doc.xpath('//p:cNvPr/@name', namespaces=namespaces)[0]
        
        self.assertEqual(color, '0066CC')
        self.assertEqual(name, 'Corporate Logo')
    
    def test_execution_context_metadata(self):
        """Test execution context metadata extraction."""
        xml_doc = etree.fromstring(self.sample_xml)
        
        patch_content = """
version: "2.1"
description: "Corporate branding update"
author: "IT Department"
target_formats:
  - potx
  - dotx
  
patches:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "336699"
"""
        
        result = self.engine.execute_patch_content(patch_content, xml_doc, ExecutionMode.NORMAL)
        
        self.assertTrue(result.success)
        
        # Check metadata in context
        metadata = result.execution_context.metadata
        self.assertEqual(metadata['version'], '2.1')
        self.assertEqual(metadata['description'], 'Corporate branding update')
        self.assertEqual(metadata['author'], 'IT Department')
        self.assertEqual(metadata['target_formats'], ['potx', 'dotx'])
    
    def test_execution_statistics(self):
        """Test execution statistics tracking."""
        xml_doc = etree.fromstring(self.sample_xml)
        
        patch_content = """
patches:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "FF6600"
  - operation: set
    target: "//nonexistent:element/@attr"
    value: "test"
"""
        
        result = self.engine.execute_patch_content(patch_content, xml_doc, ExecutionMode.NORMAL)
        
        self.assertFalse(result.success)  # Should fail due to second patch
        
        # Check execution statistics
        stats = result.execution_context.execution_stats
        self.assertEqual(stats['total_patches'], 2)
        self.assertEqual(stats['successful_patches'], 1)
        self.assertEqual(stats['failed_patches'], 1)
        self.assertGreater(stats['execution_time'], 0)
        self.assertIsNotNone(stats['start_time'])
        self.assertIsNotNone(stats['end_time'])
    
    def test_file_execution(self):
        """Test executing patches from a file."""
        xml_doc = etree.fromstring(self.sample_xml)
        
        patch_content = """
version: "1.0"
patches:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "9966CC"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(patch_content)
            temp_file = f.name
        
        try:
            result = self.engine.execute_patch_file(temp_file, xml_doc, ExecutionMode.NORMAL)
            
            self.assertTrue(result.success)
            self.assertEqual(len(result.patch_results), 1)
            self.assertTrue(result.patch_results[0].success)
            
            # Verify the change was applied
            modified_color = result.modified_document.xpath('//a:srgbClr/@val', namespaces={
                'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
            })
            self.assertEqual(modified_color[0], '9966CC')
        finally:
            Path(temp_file).unlink()
    
    def test_file_not_found_error(self):
        """Test handling of non-existent patch files."""
        xml_doc = etree.fromstring(self.sample_xml)
        
        result = self.engine.execute_patch_file("nonexistent_file.json", xml_doc, ExecutionMode.NORMAL)
        
        self.assertFalse(result.success)
        self.assertTrue(any('File not found' in error for error in result.errors))
        self.assertEqual(len(result.patch_results), 0)
    
    def test_batch_execution(self):
        """Test batch execution of multiple patch files."""
        xml_doc = etree.fromstring(self.sample_xml)
        
        # Create multiple patch files
        patch1_content = """
patches:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "FF0000"
"""
        
        patch2_content = """
patches:
  - operation: set
    target: "//p:cNvPr/@name"
    value: "Batch Test"
"""
        
        patch3_content = """
patches:
  - operation: set
    target: "//a:off/@x"
    value: "200"
"""
        
        temp_files = []
        try:
            for i, content in enumerate([patch1_content, patch2_content, patch3_content]):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    f.write(content)
                    temp_files.append(f.name)
            
            result = self.engine.execute_batch(temp_files, xml_doc, ExecutionMode.NORMAL)
            
            self.assertTrue(result.success)
            self.assertEqual(len(result.results), 3)
            self.assertTrue(all(res.success for res in result.results))
            self.assertEqual(result.total_patches, 3)
            self.assertEqual(result.successful_patches, 3)
            self.assertEqual(result.failed_patches, 0)
            self.assertGreater(result.total_execution_time, 0)
        
        finally:
            for temp_file in temp_files:
                Path(temp_file).unlink()
    
    def test_shared_context_in_batch(self):
        """Test shared context between batch executions."""
        xml_doc = etree.fromstring(self.sample_xml)
        
        # First patch defines variables
        patch1_content = """
variables:
  test_color: "336699"
  
patches:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "${test_color}"
"""
        
        # Second patch uses the same variables (should work with shared context)
        patch2_content = """
patches:
  - operation: set
    target: "//p:cNvPr/@name"
    value: "Color: ${test_color}"
"""
        
        temp_files = []
        try:
            for content in [patch1_content, patch2_content]:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    f.write(content)
                    temp_files.append(f.name)
            
            # Execute with shared context
            result = self.engine.execute_batch(temp_files, xml_doc, ExecutionMode.NORMAL, shared_context=True)
            
            self.assertTrue(result.success)
            self.assertEqual(len(result.results), 2)
            self.assertTrue(all(res.success for res in result.results))
            
            # Check that second patch could access variables from first
            final_doc = result.results[-1].modified_document
            name = final_doc.xpath('//p:cNvPr/@name', namespaces={
                'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'
            })[0]
            self.assertEqual(name, 'Color: 336699')
        
        finally:
            for temp_file in temp_files:
                Path(temp_file).unlink()
    
    def test_callback_functionality(self):
        """Test pre and post patch callbacks."""
        xml_doc = etree.fromstring(self.sample_xml)
        
        # Track callback invocations
        callback_data = {'pre_calls': 0, 'post_calls': 0, 'patches': []}
        
        def pre_patch_callback(patch, context):
            callback_data['pre_calls'] += 1
            callback_data['patches'].append(patch.get('operation', 'unknown'))
        
        def post_patch_callback(patch, result, context):
            callback_data['post_calls'] += 1
        
        self.engine.add_pre_patch_callback(pre_patch_callback)
        self.engine.add_post_patch_callback(post_patch_callback)
        
        patch_content = """
patches:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "FF9900"
  - operation: set
    target: "//p:cNvPr/@name"
    value: "Callback Test"
"""
        
        result = self.engine.execute_patch_content(patch_content, xml_doc, ExecutionMode.NORMAL)
        
        self.assertTrue(result.success)
        self.assertEqual(callback_data['pre_calls'], 2)
        self.assertEqual(callback_data['post_calls'], 2)
        self.assertEqual(callback_data['patches'], ['set', 'set'])
    
    def test_global_statistics(self):
        """Test global statistics tracking."""
        xml_doc = etree.fromstring(self.sample_xml)
        
        # Reset statistics
        self.engine.reset_global_statistics()
        
        patch_content = """
patches:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "CCCCCC"
"""
        
        # Execute a few times
        for _ in range(3):
            self.engine.execute_patch_content(patch_content, xml_doc, ExecutionMode.NORMAL)
        
        stats = self.engine.get_global_statistics()
        
        self.assertEqual(stats['total_executions'], 3)
        self.assertEqual(stats['successful_executions'], 3)
        self.assertEqual(stats['total_patches_processed'], 3)
        self.assertGreater(stats['average_execution_time'], 0)
    
    def test_error_handling_invalid_patch(self):
        """Test error handling for invalid patches."""
        xml_doc = etree.fromstring(self.sample_xml)
        
        # Invalid JSON content
        invalid_patch_content = """
patches:
  - operation: invalid_operation
    target: "//a:srgbClr/@val"
    value: "FF0000"
"""
        
        result = self.engine.execute_patch_content(invalid_patch_content, xml_doc, ExecutionMode.NORMAL)
        
        self.assertFalse(result.success)
        self.assertTrue(any('Unsupported operation' in error for error in result.errors))
    
    def test_progress_callback(self):
        """Test progress callback in batch execution."""
        xml_doc = etree.fromstring(self.sample_xml)
        
        progress_data = {'calls': 0, 'files': []}
        
        def progress_callback(current, total, filename, success):
            progress_data['calls'] += 1
            progress_data['files'].append(filename)
        
        self.engine.set_progress_callback(progress_callback)
        
        # Create test files
        patch_content = """
patches:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "AABBCC"
"""
        
        temp_files = []
        try:
            for i in range(2):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    f.write(patch_content)
                    temp_files.append(f.name)
            
            result = self.engine.execute_batch(temp_files, xml_doc, ExecutionMode.NORMAL)
            
            self.assertTrue(result.success)
            self.assertEqual(progress_data['calls'], 2)
            self.assertEqual(len(progress_data['files']), 2)
        
        finally:
            for temp_file in temp_files:
                Path(temp_file).unlink()


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions for patch execution."""
    
    def setUp(self):
        """Set up test environment."""
        self.sample_xml = """<a:srgbClr val="FF0000" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"/>"""
    
    def test_execute_patch_content_function(self):
        """Test the execute_patch_content convenience function."""
        xml_doc = etree.fromstring(self.sample_xml)
        
        patch_content = """
patches:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "00FF00"
"""
        
        result = execute_patch_content(patch_content, xml_doc, ExecutionMode.NORMAL, ValidationLevel.STRICT)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.patch_results), 1)
        
        # Verify the change
        modified_color = result.modified_document.xpath('//a:srgbClr/@val', namespaces={
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
        })
        self.assertEqual(modified_color[0], '00FF00')
    
    def test_execute_patch_file_function(self):
        """Test the execute_patch_file convenience function."""
        xml_doc = etree.fromstring(self.sample_xml)
        
        patch_content = """
patches:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "0066CC"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(patch_content)
            temp_file = f.name
        
        try:
            result = execute_patch_file(temp_file, xml_doc, ExecutionMode.DRY_RUN, ValidationLevel.LENIENT)
            
            self.assertTrue(result.success)
            self.assertTrue(result.dry_run)
            self.assertEqual(len(result.patch_results), 1)
        finally:
            Path(temp_file).unlink()


if __name__ == '__main__':
    unittest.main()