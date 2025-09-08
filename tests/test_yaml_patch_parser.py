"""
Test suite for YAML Patch Parser.

Tests comprehensive parsing, validation, and error handling capabilities
for YAML patch files in the StyleStack OOXML processing engine.
"""

import unittest
import tempfile
from pathlib import Path
from tools.yaml_patch_parser import (
    YAMLPatchParser, ValidationLevel, ParseError, PatchMetadata,
    parse_patch_file, parse_patch_content
)


class TestYAMLPatchParser(unittest.TestCase):
    """Test cases for YAML patch parser functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.parser = YAMLPatchParser(ValidationLevel.LENIENT)
    
    def test_basic_patch_parsing(self):
        """Test parsing a basic YAML patch file."""
        yaml_content = """
version: "1.0"
description: "Basic color patch"
patches:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "00FF00"
"""
        result = self.parser.parse_content(yaml_content)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.patches), 1)
        self.assertEqual(result.patches[0]['operation'], 'set')
        self.assertEqual(result.patches[0]['target'], '//a:srgbClr/@val')
        self.assertEqual(result.patches[0]['value'], '00FF00')
        self.assertEqual(result.metadata.version, '1.0')
        self.assertEqual(result.metadata.description, 'Basic color patch')
    
    def test_multiple_patch_operations(self):
        """Test parsing multiple patch operations."""
        yaml_content = """
patches:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "FF0000"
  - operation: insert
    target: "//a:clrScheme"
    value: "<a:accent3><a:srgbClr val='9BBB59'/></a:accent3>"
    position: append
  - operation: merge
    target: "//w:rPr"
    value:
      w:b: ""
      w:i: ""
"""
        result = self.parser.parse_content(yaml_content)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.patches), 3)
        
        # Verify each operation
        self.assertEqual(result.patches[0]['operation'], 'set')
        self.assertEqual(result.patches[1]['operation'], 'insert')
        self.assertEqual(result.patches[1]['position'], 'append')
        self.assertEqual(result.patches[2]['operation'], 'merge')
        self.assertIsInstance(result.patches[2]['value'], dict)
    
    def test_variable_substitution(self):
        """Test variable substitution in patch values."""
        yaml_content = """
variables:
  brand_color: "0066CC"
  company_name: "Acme Corp"
  
patches:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "${brand_color}"
  - operation: set
    target: "//w:t"
    value: "Welcome to ${company_name}"
"""
        result = self.parser.parse_content(yaml_content)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.patches), 2)
        self.assertEqual(result.patches[0]['value'], '0066CC')
        self.assertEqual(result.patches[1]['value'], 'Welcome to Acme Corp')
    
    def test_metadata_extraction(self):
        """Test extraction of patch file metadata."""
        yaml_content = """
version: "2.1"
description: "Corporate branding patch"
author: "IT Department"
target_formats:
  - potx
  - dotx
dependencies:
  - "base-theme.yaml"
  - "corporate-colors.yaml"
  
patches:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "336699"
"""
        result = self.parser.parse_content(yaml_content)
        
        self.assertTrue(result.success)
        self.assertEqual(result.metadata.version, '2.1')
        self.assertEqual(result.metadata.description, 'Corporate branding patch')
        self.assertEqual(result.metadata.author, 'IT Department')
        self.assertEqual(result.metadata.target_formats, ['potx', 'dotx'])
        self.assertEqual(result.metadata.dependencies, ['base-theme.yaml', 'corporate-colors.yaml'])
    
    def test_validation_strict_mode(self):
        """Test strict validation mode."""
        parser = YAMLPatchParser(ValidationLevel.STRICT)
        yaml_content = """
patches:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "FF0000"
target_formats:
  - invalid_format  # This should cause warning in strict mode
"""
        result = parser.parse_content(yaml_content)
        
        # In strict mode, warnings should cause failure
        self.assertFalse(result.success)
        self.assertTrue(any('Unsupported target formats' in w.message for w in result.warnings))
    
    def test_validation_permissive_mode(self):
        """Test permissive validation mode."""
        parser = YAMLPatchParser(ValidationLevel.PERMISSIVE)
        yaml_content = """
patches:
  - operation: invalid_operation  # This should normally be an error
    target: "//a:srgbClr/@val"
    value: "FF0000"
"""
        result = parser.parse_content(yaml_content)
        
        # In permissive mode, non-critical errors might be allowed
        # But operation validation is still critical
        self.assertFalse(result.success)
        self.assertTrue(any('Unsupported operation' in e.message for e in result.errors))
    
    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        yaml_content = """
patches:
  - operation: set
    # Missing target field
    value: "FF0000"
  - target: "//a:srgbClr/@val"
    # Missing operation field
    value: "00FF00"
"""
        result = self.parser.parse_content(yaml_content)
        
        self.assertFalse(result.success)
        self.assertEqual(len(result.errors), 2)
        self.assertTrue(any('Missing required' in e.message for e in result.errors))
    
    def test_invalid_operation_types(self):
        """Test handling of invalid operation types."""
        yaml_content = """
patches:
  - operation: invalid_op
    target: "//a:srgbClr/@val"
    value: "FF0000"
  - operation: another_bad_op
    target: "//w:t"
    value: "Hello"
"""
        result = self.parser.parse_content(yaml_content)
        
        self.assertFalse(result.success)
        self.assertEqual(len(result.errors), 2)
        for error in result.errors:
            self.assertIn('Unsupported operation', error.message)
    
    def test_operation_specific_validation(self):
        """Test operation-specific validation rules."""
        yaml_content = """
patches:
  - operation: insert
    target: "//a:clrScheme"
    value: "<a:accent3/>"
    position: invalid_position  # Should be append, prepend, before, or after
  - operation: relsAdd
    target: "//Relationships"
    value:
      # Missing required relationship fields
      Id: "rId1"
      # Missing Type and Target
"""
        result = self.parser.parse_content(yaml_content)
        
        self.assertFalse(result.success)
        self.assertTrue(any('Invalid insert position' in e.message for e in result.errors))
        self.assertTrue(any('missing required fields' in e.message for e in result.errors))
    
    def test_yaml_syntax_errors(self):
        """Test handling of YAML syntax errors."""
        yaml_content = """
patches:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "FF0000"
    invalid_yaml: [unclosed list
"""
        result = self.parser.parse_content(yaml_content)
        
        self.assertFalse(result.success)
        self.assertTrue(any('YAML syntax error' in e.message for e in result.errors))
    
    def test_empty_content(self):
        """Test handling of empty or null content."""
        result = self.parser.parse_content("")
        self.assertFalse(result.success)
        
        result = self.parser.parse_content("null")
        self.assertFalse(result.success)
        
        result = self.parser.parse_content("# Just a comment")
        self.assertFalse(result.success)
    
    def test_file_parsing(self):
        """Test parsing from actual files."""
        yaml_content = """
version: "1.0"
patches:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "336699"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_file = f.name
        
        try:
            result = self.parser.parse_file(temp_file)
            self.assertTrue(result.success)
            self.assertEqual(len(result.patches), 1)
            self.assertEqual(result.metadata.version, '1.0')
        finally:
            Path(temp_file).unlink()
    
    def test_file_not_found(self):
        """Test handling of non-existent files."""
        result = self.parser.parse_file("nonexistent_file.yaml")
        
        self.assertFalse(result.success)
        self.assertTrue(any('File not found' in e.message for e in result.errors))
    
    def test_alternative_patch_structures(self):
        """Test parsing patches in various YAML structures."""
        # Patches at root level
        yaml_content1 = """
operation: set
target: "//a:srgbClr/@val"
value: "FF0000"
"""
        result1 = self.parser.parse_content(yaml_content1)
        self.assertTrue(result1.success)
        self.assertEqual(len(result1.patches), 1)
        
        # Patches under 'operations' key
        yaml_content2 = """
operations:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "FF0000"
"""
        result2 = self.parser.parse_content(yaml_content2)
        self.assertTrue(result2.success)
        self.assertEqual(len(result2.patches), 1)
    
    def test_undefined_variable_handling(self):
        """Test handling of undefined variables in substitution."""
        yaml_content = """
variables:
  defined_var: "value"
  
patches:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "${undefined_var}"
  - operation: set
    target: "//w:t"
    value: "${defined_var}"
"""
        result = self.parser.parse_content(yaml_content)
        
        # Should still succeed but with warnings
        self.assertTrue(result.success)
        self.assertTrue(any('Undefined variable' in w.message for w in result.warnings))
        
        # Undefined variables should remain as-is
        self.assertEqual(result.patches[0]['value'], '${undefined_var}')
        self.assertEqual(result.patches[1]['value'], 'value')
    
    def test_complex_nested_substitution(self):
        """Test complex variable substitution scenarios."""
        yaml_content = """
variables:
  color: "0066CC"
  opacity: "50"
  
patches:
  - operation: insert
    target: "//a:clrScheme"
    value: |
      <a:accent3>
        <a:srgbClr val="${color}">
          <a:alpha val="${opacity}000"/>
        </a:srgbClr>
      </a:accent3>
"""
        result = self.parser.parse_content(yaml_content)
        
        self.assertTrue(result.success)
        self.assertIn('val="0066CC"', result.patches[0]['value'])
        self.assertIn('val="50000"', result.patches[0]['value'])
    
    def test_extend_operation_validation(self):
        """Test validation specific to extend operations."""
        yaml_content = """
patches:
  - operation: extend
    target: "//a:clrScheme"
    value:
      - "<a:accent3><a:srgbClr val='9BBB59'/></a:accent3>"
      - "<a:accent4><a:srgbClr val='8064A2'/></a:accent4>"
  - operation: extend
    target: "//a:clrScheme"
    value: "not_an_array"  # Should warn about non-array value
"""
        result = self.parser.parse_content(yaml_content)
        
        self.assertTrue(result.success)  # Should succeed with warnings
        self.assertTrue(any('should have array value' in w.message for w in result.warnings))
    
    def test_merge_operation_validation(self):
        """Test validation specific to merge operations."""
        yaml_content = """
patches:
  - operation: merge
    target: "//w:rPr"
    value:
      w:b: ""
      w:i: ""
  - operation: merge
    target: "//w:rPr"
    value: "not_a_dict"  # Should warn about non-dict value
"""
        result = self.parser.parse_content(yaml_content)
        
        self.assertTrue(result.success)  # Should succeed with warnings
        self.assertTrue(any('should have dictionary value' in w.message for w in result.warnings))


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions for common parsing operations."""
    
    def test_parse_patch_content_function(self):
        """Test the parse_patch_content convenience function."""
        yaml_content = """
patches:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "FF0000"
"""
        result = parse_patch_content(yaml_content, ValidationLevel.STRICT)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.patches), 1)
    
    def test_parse_patch_file_function(self):
        """Test the parse_patch_file convenience function."""
        yaml_content = """
patches:
  - operation: set
    target: "//a:srgbClr/@val"
    value: "336699"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_file = f.name
        
        try:
            result = parse_patch_file(temp_file, ValidationLevel.LENIENT)
            self.assertTrue(result.success)
            self.assertEqual(len(result.patches), 1)
        finally:
            Path(temp_file).unlink()


if __name__ == '__main__':
    unittest.main()