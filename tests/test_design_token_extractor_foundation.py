#!/usr/bin/env python3
"""
Foundation Tests for Design Token Extractor

Comprehensive test coverage for the design token extraction system,
focusing on core functionality and edge cases.

Part of StyleStack 90% Coverage Initiative - Phase 1: Foundation Testing
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from tests.fixtures import sample_design_tokens, temp_dir, mock_ooxml_processor
from tests.mocks import create_standard_mocks, get_mock

# Import the module under test
from tools.design_token_extractor import (
    DesignTokenExtractor,
    TokenExtractionError,
    TokenValidator,
    TokenTransformer
)


class TestDesignTokenExtractor:
    """Test suite for design token extractor core functionality"""
    
    def test_initialization(self):
        """Test extractor initialization with default settings"""
        extractor = DesignTokenExtractor()
        
        assert extractor is not None
        assert hasattr(extractor, 'extract_tokens')
        assert hasattr(extractor, 'validate_tokens')
        
    def test_initialization_with_config(self):
        """Test extractor initialization with custom configuration"""
        config = {
            'extraction_depth': 5,
            'include_metadata': True,
            'validate_schema': True
        }
        
        extractor = DesignTokenExtractor(config)
        assert extractor is not None
    
    def test_basic_token_extraction(self, sample_design_tokens):
        """Test basic token extraction from sample data"""
        extractor = DesignTokenExtractor()
        
        # Mock the extraction process
        with patch.object(extractor, '_extract_from_source') as mock_extract:
            mock_extract.return_value = sample_design_tokens
            
            result = extractor.extract_tokens('mock_source')
            
            assert isinstance(result, dict)
            assert 'brand' in result
            assert 'typography' in result
            assert result['brand']['primary'] == '#007acc'
    
    def test_token_extraction_with_validation(self, sample_design_tokens):
        """Test token extraction with built-in validation"""
        extractor = DesignTokenExtractor({'validate_schema': True})
        
        with patch.object(extractor, '_extract_from_source') as mock_extract, \
             patch.object(extractor, '_validate_token_schema') as mock_validate:
            
            mock_extract.return_value = sample_design_tokens
            mock_validate.return_value = True
            
            result = extractor.extract_tokens('mock_source')
            
            mock_validate.assert_called_once_with(sample_design_tokens)
            assert isinstance(result, dict)
    
    def test_token_extraction_error_handling(self):
        """Test error handling during token extraction"""
        extractor = DesignTokenExtractor()
        
        with patch.object(extractor, '_extract_from_source') as mock_extract:
            mock_extract.side_effect = Exception("Mock extraction error")
            
            with pytest.raises(TokenExtractionError):
                extractor.extract_tokens('invalid_source')
    
    def test_nested_token_extraction(self):
        """Test extraction of deeply nested tokens"""
        extractor = DesignTokenExtractor({'extraction_depth': 10})
        
        nested_tokens = {
            'theme': {
                'colors': {
                    'primary': {
                        'light': '#e3f2fd',
                        'main': '#2196f3',
                        'dark': '#1976d2'
                    }
                }
            }
        }
        
        with patch.object(extractor, '_extract_from_source') as mock_extract:
            mock_extract.return_value = nested_tokens
            
            result = extractor.extract_tokens('mock_source')
            
            assert result['theme']['colors']['primary']['main'] == '#2196f3'
    
    def test_token_filtering(self):
        """Test filtering tokens based on criteria"""
        extractor = DesignTokenExtractor({
            'include_patterns': ['brand.*', 'typography.*'],
            'exclude_patterns': ['*.deprecated.*']
        })
        
        tokens = {
            'brand': {'primary': '#007acc'},
            'typography': {'heading': 'Segoe UI'},
            'layout': {'margin': '1rem'},  # Should be filtered out
            'brand': {'deprecated': {'old_color': '#ff0000'}}  # Should be filtered out
        }
        
        with patch.object(extractor, '_extract_from_source') as mock_extract, \
             patch.object(extractor, '_apply_filters') as mock_filter:
            
            mock_extract.return_value = tokens
            mock_filter.return_value = {'brand': {'primary': '#007acc'}, 'typography': {'heading': 'Segoe UI'}}
            
            result = extractor.extract_tokens('mock_source')
            
            assert 'layout' not in result
            assert 'brand' in result
            assert 'typography' in result
    
    def test_metadata_extraction(self):
        """Test extraction of token metadata"""
        extractor = DesignTokenExtractor({'include_metadata': True})
        
        tokens_with_meta = {
            'brand': {
                'primary': {
                    'value': '#007acc',
                    'type': 'color',
                    'description': 'Primary brand color'
                }
            }
        }
        
        with patch.object(extractor, '_extract_from_source') as mock_extract:
            mock_extract.return_value = tokens_with_meta
            
            result = extractor.extract_tokens('mock_source')
            
            assert result['brand']['primary']['type'] == 'color'
            assert result['brand']['primary']['description'] == 'Primary brand color'


class TestTokenValidator:
    """Test suite for token validation functionality"""
    
    def test_validator_initialization(self):
        """Test validator initialization"""
        validator = TokenValidator()
        assert validator is not None
    
    def test_valid_token_schema(self, sample_design_tokens):
        """Test validation of valid token schema"""
        validator = TokenValidator()
        
        result = validator.validate_schema(sample_design_tokens)
        assert result is True
    
    def test_invalid_token_schema(self):
        """Test validation of invalid token schema"""
        validator = TokenValidator()
        
        invalid_tokens = {
            'invalid': None,
            'empty': {},
            'wrong_type': 'string_instead_of_object'
        }
        
        result = validator.validate_schema(invalid_tokens)
        assert result is False
    
    def test_token_value_validation(self):
        """Test validation of specific token values"""
        validator = TokenValidator()
        
        # Valid color values
        assert validator.validate_color('#007acc') is True
        assert validator.validate_color('rgb(0, 122, 204)') is True
        assert validator.validate_color('hsl(210, 100%, 40%)') is True
        
        # Invalid color values
        assert validator.validate_color('not-a-color') is False
        assert validator.validate_color('#gggggg') is False
    
    def test_typography_validation(self):
        """Test validation of typography tokens"""
        validator = TokenValidator()
        
        valid_typography = {
            'family': 'Segoe UI',
            'size': '16px',
            'weight': '400',
            'line_height': '1.5'
        }
        
        assert validator.validate_typography(valid_typography) is True
        
        invalid_typography = {
            'family': 123,  # Should be string
            'size': 'invalid-size'
        }
        
        assert validator.validate_typography(invalid_typography) is False
    
    def test_spacing_validation(self):
        """Test validation of spacing tokens"""
        validator = TokenValidator()
        
        valid_spacing = ['8px', '1rem', '2em', '16pt']
        invalid_spacing = ['8', 'invalid-unit', None]
        
        for value in valid_spacing:
            assert validator.validate_spacing(value) is True
        
        for value in invalid_spacing:
            assert validator.validate_spacing(value) is False
    
    def test_comprehensive_validation(self, sample_design_tokens):
        """Test comprehensive validation of all token types"""
        validator = TokenValidator()
        
        validation_result = validator.validate_comprehensive(sample_design_tokens)
        
        assert isinstance(validation_result, dict)
        assert 'valid' in validation_result
        assert 'errors' in validation_result
        assert 'warnings' in validation_result


class TestTokenTransformer:
    """Test suite for token transformation functionality"""
    
    def test_transformer_initialization(self):
        """Test transformer initialization"""
        transformer = TokenTransformer()
        assert transformer is not None
    
    def test_token_flattening(self, sample_design_tokens):
        """Test flattening nested tokens"""
        transformer = TokenTransformer()
        
        flattened = transformer.flatten_tokens(sample_design_tokens)
        
        assert isinstance(flattened, dict)
        assert 'brand.primary' in flattened
        assert 'typography.heading.family' in flattened
        assert flattened['brand.primary'] == '#007acc'
    
    def test_token_expansion(self):
        """Test expanding flattened tokens back to nested structure"""
        transformer = TokenTransformer()
        
        flattened = {
            'brand.primary': '#007acc',
            'brand.secondary': '#f4f4f4',
            'typography.heading.family': 'Segoe UI'
        }
        
        expanded = transformer.expand_tokens(flattened)
        
        assert expanded['brand']['primary'] == '#007acc'
        assert expanded['typography']['heading']['family'] == 'Segoe UI'
    
    def test_token_format_conversion(self):
        """Test converting token formats"""
        transformer = TokenTransformer()
        
        # Convert hex to RGB
        rgb_result = transformer.convert_color('#007acc', 'rgb')
        assert 'rgb(' in rgb_result
        
        # Convert px to rem
        rem_result = transformer.convert_size('16px', 'rem')
        assert 'rem' in rem_result
    
    def test_token_prefix_addition(self, sample_design_tokens):
        """Test adding prefixes to token names"""
        transformer = TokenTransformer()
        
        prefixed = transformer.add_prefix(sample_design_tokens, 'acme')
        
        assert 'acme.brand' in prefixed
        assert 'acme.typography' in prefixed
        assert prefixed['acme.brand']['primary'] == '#007acc'
    
    def test_token_filtering_by_type(self, sample_design_tokens):
        """Test filtering tokens by type"""
        transformer = TokenTransformer()
        
        # Add type metadata for testing
        typed_tokens = {
            'colors': {'primary': {'value': '#007acc', 'type': 'color'}},
            'typography': {'heading': {'value': 'Segoe UI', 'type': 'typography'}},
            'spacing': {'small': {'value': '8px', 'type': 'spacing'}}
        }
        
        color_tokens = transformer.filter_by_type(typed_tokens, 'color')
        
        assert 'colors' in color_tokens
        assert 'typography' not in color_tokens
        assert 'spacing' not in color_tokens


class TestTokenExtractionIntegration:
    """Integration tests for complete token extraction workflows"""
    
    def test_file_based_extraction(self, temp_dir):
        """Test extracting tokens from file sources"""
        extractor = DesignTokenExtractor()
        
        # Create a mock token file
        token_file = temp_dir / 'tokens.json'
        tokens = {
            'brand': {'primary': '#007acc'},
            'typography': {'body': 'Arial'}
        }
        token_file.write_text(json.dumps(tokens))
        
        # Mock file reading
        with patch.object(extractor, '_read_token_file') as mock_read:
            mock_read.return_value = tokens
            
            result = extractor.extract_from_file(str(token_file))
            
            assert result['brand']['primary'] == '#007acc'
    
    def test_ooxml_based_extraction(self, mock_ooxml_processor):
        """Test extracting tokens from OOXML documents"""
        extractor = DesignTokenExtractor()
        
        # Configure mock OOXML processor
        mock_ooxml_processor.extract_theme_colors.return_value = {
            'accent1': '#007acc',
            'accent2': '#f4f4f4'
        }
        
        with patch.object(extractor, '_get_ooxml_processor', return_value=mock_ooxml_processor):
            result = extractor.extract_from_ooxml('mock.potx')
            
            mock_ooxml_processor.load_template.assert_called_once_with('mock.potx')
            mock_ooxml_processor.extract_theme_colors.assert_called_once()
    
    def test_api_based_extraction(self):
        """Test extracting tokens from API sources"""
        extractor = DesignTokenExtractor()
        
        api_response = {
            'data': {
                'tokens': {
                    'brand': {'primary': '#007acc'},
                    'spacing': {'medium': '16px'}
                }
            }
        }
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = api_response
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            result = extractor.extract_from_api('https://api.tokens.com/v1/tokens')
            
            assert result['brand']['primary'] == '#007acc'
    
    def test_batch_extraction(self, temp_dir):
        """Test batch extraction from multiple sources"""
        extractor = DesignTokenExtractor()
        
        # Create multiple token files
        sources = []
        for i in range(3):
            token_file = temp_dir / f'tokens_{i}.json'
            tokens = {f'group_{i}': {f'token_{i}': f'value_{i}'}}
            token_file.write_text(json.dumps(tokens))
            sources.append(str(token_file))
        
        with patch.object(extractor, '_read_token_file') as mock_read:
            mock_read.side_effect = [
                {'group_0': {'token_0': 'value_0'}},
                {'group_1': {'token_1': 'value_1'}},
                {'group_2': {'token_2': 'value_2'}}
            ]
            
            result = extractor.extract_batch(sources)
            
            assert len(result) == 3
            assert 'group_0' in result[0]
            assert result[1]['group_1']['token_1'] == 'value_1'
    
    def test_extraction_with_transformation(self, sample_design_tokens):
        """Test extraction combined with transformation"""
        extractor = DesignTokenExtractor({
            'apply_transformations': True,
            'output_format': 'flat'
        })
        
        with patch.object(extractor, '_extract_from_source') as mock_extract, \
             patch.object(extractor, '_apply_transformations') as mock_transform:
            
            mock_extract.return_value = sample_design_tokens
            mock_transform.return_value = {
                'brand.primary': '#007acc',
                'typography.heading.family': 'Segoe UI'
            }
            
            result = extractor.extract_tokens('mock_source')
            
            mock_transform.assert_called_once_with(sample_design_tokens)
            assert 'brand.primary' in result


class TestTokenExtractionPerformance:
    """Performance-focused tests for token extraction"""
    
    def test_large_dataset_extraction(self, benchmark_data):
        """Test extraction performance with large datasets"""
        extractor = DesignTokenExtractor()
        
        # Use benchmark data as large token set
        large_tokens = benchmark_data['nested_structure']
        
        with patch.object(extractor, '_extract_from_source') as mock_extract:
            mock_extract.return_value = large_tokens
            
            import time
            start_time = time.time()
            result = extractor.extract_tokens('large_source')
            extraction_time = time.time() - start_time
            
            # Should complete within reasonable time (< 1 second for test data)
            assert extraction_time < 1.0
            assert isinstance(result, dict)
    
    def test_memory_efficient_extraction(self):
        """Test memory-efficient extraction for large datasets"""
        extractor = DesignTokenExtractor({'streaming_mode': True})
        
        # Mock streaming extraction
        with patch.object(extractor, '_extract_streaming') as mock_stream:
            mock_stream.return_value = iter([
                ('brand.primary', '#007acc'),
                ('typography.family', 'Segoe UI')
            ])
            
            result = extractor.extract_tokens_streaming('large_source')
            
            # Should return iterator for memory efficiency
            assert hasattr(result, '__iter__')
            tokens = dict(result)
            assert tokens['brand.primary'] == '#007acc'


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling scenarios"""
    
    def test_empty_token_extraction(self):
        """Test handling of empty token sources"""
        extractor = DesignTokenExtractor()
        
        with patch.object(extractor, '_extract_from_source') as mock_extract:
            mock_extract.return_value = {}
            
            result = extractor.extract_tokens('empty_source')
            
            assert result == {}
    
    def test_malformed_token_data(self):
        """Test handling of malformed token data"""
        extractor = DesignTokenExtractor()
        
        malformed_data = {
            'invalid': None,
            'circular_ref': {'self': None}
        }
        malformed_data['circular_ref']['self'] = malformed_data['circular_ref']
        
        with patch.object(extractor, '_extract_from_source') as mock_extract:
            mock_extract.return_value = malformed_data
            
            # Should handle malformed data gracefully
            result = extractor.extract_tokens('malformed_source')
            assert isinstance(result, dict)
    
    def test_unicode_token_handling(self):
        """Test handling of Unicode characters in tokens"""
        extractor = DesignTokenExtractor()
        
        unicode_tokens = {
            'brand': {'name': '🎨 Design System'},
            'typography': {'content': 'Héllö Wörld'},
            'emoji': {'success': '✅', 'error': '❌'}
        }
        
        with patch.object(extractor, '_extract_from_source') as mock_extract:
            mock_extract.return_value = unicode_tokens
            
            result = extractor.extract_tokens('unicode_source')
            
            assert result['brand']['name'] == '🎨 Design System'
            assert result['emoji']['success'] == '✅'
    
    def test_concurrent_extraction(self):
        """Test thread-safe concurrent extraction"""
        extractor = DesignTokenExtractor({'thread_safe': True})
        
        import threading
        import time
        
        results = []
        errors = []
        
        def extract_worker(source_id):
            try:
                with patch.object(extractor, '_extract_from_source') as mock_extract:
                    mock_extract.return_value = {f'token_{source_id}': f'value_{source_id}'}
                    
                    result = extractor.extract_tokens(f'source_{source_id}')
                    results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Run concurrent extractions
        threads = []
        for i in range(5):
            thread = threading.Thread(target=extract_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join(timeout=5)
        
        assert len(errors) == 0
        assert len(results) == 5


if __name__ == '__main__':
    # Run basic validation
    print("Testing Design Token Extractor Foundation...")
    
    # Test basic initialization
    extractor = DesignTokenExtractor()
    print("✅ Extractor initialized")
    
    # Test validator
    validator = TokenValidator()
    print("✅ Validator initialized")
    
    # Test transformer
    transformer = TokenTransformer()
    print("✅ Transformer initialized")
    
    print("Run with pytest for comprehensive testing")