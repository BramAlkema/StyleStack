#!/usr/bin/env python3
"""
Token Integration Layer Tests

Tests the integration between Design Token Formula Evaluation system
and JSON-to-OOXML Processing Engine, validating token resolution,
formula evaluation, and EMU type integration.

Part of the StyleStack JSON-to-OOXML Processing Engine test suite.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from lxml import etree
from tools.token_integration_layer import (
    TokenIntegrationLayer, TokenScope, TokenContext, TokenResolutionResult,
    create_default_integration_layer, integrate_tokens_with_processor
)
from tools.formula_parser import FormulaParser
from tools.emu_types import EMUValue


class TestTokenIntegrationLayer(unittest.TestCase):
    """Test cases for Token Integration Layer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.integration_layer = TokenIntegrationLayer()
        
        # Sample context
        self.test_context = TokenContext(
            scope=TokenScope.OPERATION,
            template_type='potx',
            variables={'brand_color': 'FF0000', 'company_name': 'AcmeCorp'},
            metadata={'version': '1.0', 'author': 'test'}
        )
        
        # Sample patch data for testing
        self.sample_patch = {
            'operation': 'set',
            'target': '//a:srgbClr/@val',
            'value': '${brand_color}'
        }
    
    def test_token_registration_and_retrieval(self):
        """Test token registration and scope-based retrieval."""
        # Register tokens at different scopes
        self.integration_layer.register_token('global_token', 'global_value', TokenScope.GLOBAL)
        self.integration_layer.register_token('template_token', 'template_value', TokenScope.TEMPLATE, 'potx')
        self.integration_layer.register_token('doc_token', 'doc_value', TokenScope.DOCUMENT)
        
        # Test retrieval with scope priority
        global_val = self.integration_layer._get_token_from_scope('global_token', TokenScope.GLOBAL, 'potx')
        template_val = self.integration_layer._get_token_from_scope('template_token', TokenScope.TEMPLATE, 'potx')
        doc_val = self.integration_layer._get_token_from_scope('doc_token', TokenScope.DOCUMENT, 'potx')
        
        self.assertEqual(global_val, 'global_value')
        self.assertEqual(template_val, 'template_value')
        self.assertEqual(doc_val, 'doc_value')
        
        # Test template-specific filtering
        no_match = self.integration_layer._get_token_from_scope('template_token', TokenScope.TEMPLATE, 'dotx')
        self.assertIsNone(no_match)
    
    def test_variable_token_resolution(self):
        """Test resolution of variable tokens (${token})."""
        # Register a token
        self.integration_layer.register_token('test_var', 'resolved_value', TokenScope.GLOBAL)
        
        # Test resolution
        result = self.integration_layer._resolve_variable_token('test_var', self.test_context)
        self.assertEqual(result, 'resolved_value')
        
        # Test fallback to context variables
        result = self.integration_layer._resolve_variable_token('brand_color', self.test_context)
        self.assertEqual(result, 'FF0000')
        
        # Test unresolvable token
        result = self.integration_layer._resolve_variable_token('unknown_token', self.test_context)
        self.assertEqual(result, '${unknown_token}')
    
    @patch('tools.token_integration_layer.FormulaParser')
    def test_formula_token_resolution(self, mock_parser_class):
        """Test resolution of formula tokens (@{formula})."""
        # Mock formula parser
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse.return_value = "parsed_formula"
        mock_parser.evaluate.return_value = 42
        
        integration_layer = TokenIntegrationLayer()
        
        # Test formula resolution
        result = integration_layer._resolve_formula_token('2 + 2', self.test_context)
        self.assertEqual(result, '42')
        
        # Verify parser was called correctly
        mock_parser.parse.assert_called_with('2 + 2')
        mock_parser.evaluate.assert_called_once()
    
    @patch('tools.token_integration_layer.EMUTypeSystem')
    def test_emu_token_resolution(self, mock_emu_class):
        """Test resolution of EMU tokens (#{expression})."""
        # Mock EMU system
        mock_emu = Mock()
        mock_emu_class.return_value = mock_emu
        mock_emu_value = Mock()
        mock_emu_value.to_presentation_format.return_value = '12pt'
        mock_emu.parse_value.return_value = mock_emu_value
        
        integration_layer = TokenIntegrationLayer()
        
        # Test EMU resolution for presentation format
        result = integration_layer._resolve_emu_token('12pt', self.test_context)
        self.assertEqual(result, '12pt')
        
        # Verify EMU system was called correctly
        mock_emu.parse_value.assert_called_with('12pt')
        mock_emu_value.to_presentation_format.assert_called_once()
    
    def test_string_token_resolution_mixed(self):
        """Test resolution of mixed token types in strings."""
        # Register test tokens
        self.integration_layer.register_token('prefix', 'ACME', TokenScope.GLOBAL)
        
        # Mock formula and EMU systems for complex test
        with patch.object(self.integration_layer.formula_parser, 'parse') as mock_parse, \
             patch.object(self.integration_layer.formula_parser, 'evaluate') as mock_eval, \
             patch.object(self.integration_layer.emu_system, 'parse_value') as mock_emu_parse:
            
            mock_eval.return_value = 100
            mock_emu_value = Mock()
            mock_emu_value.to_presentation_format.return_value = '14pt'
            mock_emu_parse.return_value = mock_emu_value
            
            # Test mixed string with multiple token types
            mixed_string = "${prefix}_${brand_color}_@{50 * 2}_#{14pt}"
            result = self.integration_layer._resolve_string_tokens(mixed_string, self.test_context)
            
            expected = "ACME_FF0000_100_14pt"
            self.assertEqual(result, expected)
    
    def test_patch_token_resolution(self):
        """Test resolution of tokens within patch operations."""
        # Register test token
        self.integration_layer.register_token('target_color', 'BLUE_VALUE', TokenScope.GLOBAL)
        
        # Patch with tokens in multiple fields
        patch_with_tokens = {
            'operation': 'set',
            'target': '//a:srgbClr/@val',
            'value': '${target_color}',
            'metadata': {
                'description': 'Setting color to ${target_color} for ${company_name}'
            }
        }
        
        resolved_patch = self.integration_layer.resolve_patch_tokens(patch_with_tokens, self.test_context)
        
        self.assertEqual(resolved_patch['value'], 'BLUE_VALUE')
        self.assertEqual(resolved_patch['metadata']['description'], 'Setting color to BLUE_VALUE for AcmeCorp')
    
    def test_processor_integration(self):
        """Test integration with JSON-to-OOXML processor."""
        # Create mock processor
        mock_processor = Mock(spec=JSONPatchProcessor)
        mock_processor.template_type = 'potx'
        mock_processor.variables = {'test_var': 'test_value'}
        mock_processor.metadata = {'version': '1.0'}
        
        original_apply_patch = Mock()
        mock_processor.apply_patch = original_apply_patch
        
        # Integrate token resolution
        self.integration_layer.integrate_with_processor(mock_processor)
        
        # Test that apply_patch was wrapped
        self.assertNotEqual(mock_processor.apply_patch, original_apply_patch)
        
        # Register a test token
        self.integration_layer.register_token('test_token', 'resolved', TokenScope.GLOBAL)
        
        # Test token resolution in patch application
        xml_doc = etree.fromstring('<root></root>')
        patch_data = {'operation': 'set', 'target': '//test', 'value': '${test_token}'}
        
        mock_processor.apply_patch(xml_doc, patch_data)
        
        # Verify that the original apply_patch was called with resolved tokens
        original_apply_patch.assert_called_once()
        called_args = original_apply_patch.call_args[0]
        resolved_patch = called_args[1]
        self.assertEqual(resolved_patch['value'], 'resolved')
    
    def test_explicit_token_resolution(self):
        """Test explicit token resolution with detailed results."""
        # Register test token
        self.integration_layer.register_token('explicit_test', 'explicit_value', TokenScope.GLOBAL)
        
        # Test explicit resolution
        result = self.integration_layer.resolve_token_explicit('explicit_test', self.test_context)
        
        self.assertIsInstance(result, TokenResolutionResult)
        self.assertTrue(result.success)
        self.assertEqual(result.resolved_value, 'explicit_value')
        self.assertEqual(result.original_token, 'explicit_test')
        self.assertEqual(len(result.errors), 0)
    
    def test_resolution_cache_functionality(self):
        """Test token resolution caching for performance."""
        # Register test token
        self.integration_layer.register_token('cached_token', 'cached_value', TokenScope.GLOBAL)
        
        # Clear cache to start fresh
        self.integration_layer.clear_cache()
        self.assertEqual(len(self.integration_layer.resolution_cache), 0)
        
        # Resolve token twice
        result1 = self.integration_layer._resolve_variable_token('cached_token', self.test_context)
        result2 = self.integration_layer._resolve_variable_token('cached_token', self.test_context)
        
        self.assertEqual(result1, result2)
        self.assertGreater(len(self.integration_layer.resolution_cache), 0)
    
    def test_resolution_hooks(self):
        """Test pre and post resolution hooks."""
        hook_calls = []
        
        def pre_hook(token, context):
            hook_calls.append(f"pre_{token}")
        
        def post_hook(result):
            hook_calls.append(f"post_{result.original_token}")
        
        # Add hooks
        self.integration_layer.add_resolution_hook(pre_hook, post_resolution=False)
        self.integration_layer.add_resolution_hook(post_hook, post_resolution=True)
        
        # Register and resolve token
        self.integration_layer.register_token('hook_test', 'hook_value', TokenScope.GLOBAL)
        result = self.integration_layer.resolve_token_explicit('hook_test', self.test_context)
        
        # Verify hooks were called
        self.assertIn('pre_hook_test', hook_calls)
        self.assertIn('post_hook_test', hook_calls)
    
    def test_resolution_statistics(self):
        """Test resolution performance statistics."""
        # Register some tokens
        self.integration_layer.register_token('stat_test1', 'value1', TokenScope.GLOBAL)
        self.integration_layer.register_token('stat_test2', 'value2', TokenScope.TEMPLATE, 'potx')
        
        # Resolve a token to populate cache
        self.integration_layer._resolve_variable_token('stat_test1', self.test_context)
        
        # Get statistics
        stats = self.integration_layer.get_resolution_statistics()
        
        self.assertIn('cache_size', stats)
        self.assertIn('registered_tokens_by_scope', stats)
        self.assertGreater(stats['registered_tokens_by_scope']['global'], 0)
        self.assertGreater(stats['cache_size'], 0)
    
    def test_template_type_specific_resolution(self):
        """Test template-type specific token resolution."""
        # Register template-specific tokens
        self.integration_layer.register_token('ppt_token', 'presentation_value', TokenScope.TEMPLATE, 'potx')
        self.integration_layer.register_token('word_token', 'document_value', TokenScope.TEMPLATE, 'dotx')
        self.integration_layer.register_token('excel_token', 'spreadsheet_value', TokenScope.TEMPLATE, 'xltx')
        
        # Test PowerPoint context
        ppt_context = TokenContext(TokenScope.TEMPLATE, 'potx', {}, {})
        result = self.integration_layer._resolve_variable_token('ppt_token', ppt_context)
        self.assertEqual(result, 'presentation_value')
        
        # Test Word context
        word_context = TokenContext(TokenScope.TEMPLATE, 'dotx', {}, {})
        result = self.integration_layer._resolve_variable_token('word_token', word_context)
        self.assertEqual(result, 'document_value')
        
        # Test Excel context  
        excel_context = TokenContext(TokenScope.TEMPLATE, 'xltx', {}, {})
        result = self.integration_layer._resolve_variable_token('excel_token', excel_context)
        self.assertEqual(result, 'spreadsheet_value')
    
    def test_nested_data_structure_resolution(self):
        """Test token resolution in nested data structures."""
        # Register test token
        self.integration_layer.register_token('nested_token', 'nested_value', TokenScope.GLOBAL)
        
        # Complex nested structure with tokens
        nested_data = {
            'level1': {
                'level2': ['${nested_token}', 'literal_value'],
                'another_field': '${nested_token}_suffix'
            },
            'simple_field': '${nested_token}'
        }
        
        resolved_data = self.integration_layer._resolve_value_tokens(nested_data, self.test_context)
        
        # Verify all tokens were resolved
        self.assertEqual(resolved_data['level1']['level2'][0], 'nested_value')
        self.assertEqual(resolved_data['level1']['another_field'], 'nested_value_suffix')
        self.assertEqual(resolved_data['simple_field'], 'nested_value')
        
        # Verify non-token values remain unchanged
        self.assertEqual(resolved_data['level1']['level2'][1], 'literal_value')


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions for common operations."""
    
    def test_create_default_integration_layer(self):
        """Test creation of default integration layer."""
        layer = create_default_integration_layer()
        
        self.assertIsInstance(layer, TokenIntegrationLayer)
        self.assertIsNotNone(layer.formula_parser)
        self.assertIsNotNone(layer.emu_system)
        self.assertIsNotNone(layer.variable_resolver)
    
    def test_integrate_tokens_with_processor(self):
        """Test integration with existing processor."""
        mock_processor = Mock(spec=JSONPatchProcessor)
        mock_processor.template_type = 'potx'
        mock_processor.variables = {}
        mock_processor.metadata = {}
        
        layer = integrate_tokens_with_processor(mock_processor)
        
        self.assertIsInstance(layer, TokenIntegrationLayer)
        # Verify integration occurred by checking that apply_patch method was wrapped
        self.assertIsNotNone(mock_processor.apply_patch)


if __name__ == "__main__":
    # Run with verbose output for CI
    unittest.main(verbosity=2)