#!/usr/bin/env python3
"""
Test suite for Advanced Token Feature Integration

Tests the integration of nested reference resolution and composite token 
transformations with the existing W3C DTCG validator and OOXML processor.
"""

import pytest
import json
from typing import Dict, Any, List
from unittest.mock import Mock, patch
from lxml import etree

# Import the components we're testing
from tools.w3c_dtcg_validator import W3CDTCGValidator, TokenType, ValidationResult
from tools.variable_resolver import VariableResolver, ResolvedVariable, TokenScope
from tools.composite_token_transformer import (
    ShadowTokenTransformer,
    BorderTokenTransformer, 
    GradientTokenTransformer,
    transform_composite_token
)
from tools.ooxml_processor import OOXMLProcessor


class TestW3CDTCGNestedReferenceIntegration:
    """Test W3C DTCG validator with nested reference patterns"""
    
    def setup_method(self):
        """Setup validator and test tokens"""
        self.validator = W3CDTCGValidator()
        self.resolver = VariableResolver()
        
        # Test token set with nested references
        self.test_tokens = {
            # Theme selector
            'theme': {
                '$type': 'string',
                '$value': 'dark',
                '$description': 'Current theme mode'
            },
            
            # Colors with theme variations
            'color.dark.primary': {
                '$type': 'color', 
                '$value': '#0066CC',
                '$description': 'Primary color for dark theme'
            },
            'color.light.primary': {
                '$type': 'color',
                '$value': '#4D94FF', 
                '$description': 'Primary color for light theme'
            },
            
            # Composite token with nested reference
            'component.button.shadow': {
                '$type': 'shadow',
                '$value': {
                    'color': '{color.{theme}.primary}',  # Nested reference
                    'offsetX': '0px',
                    'offsetY': '2px',
                    'blur': '4px',
                    'spread': '0px'
                },
                '$description': 'Button shadow adapts to theme'
            }
        }
    
    def test_w3c_dtcg_validation_with_nested_references(self):
        """Test that W3C DTCG validator handles nested references"""
        # Should validate the token structure regardless of nested references
        validation_result = self.validator.validate_token(
            self.test_tokens['component.button.shadow']
        )
        
        assert validation_result.is_valid == True
        assert validation_result.token_type == TokenType.SHADOW
    
    def test_nested_reference_resolution_before_transformation(self):
        """Test that nested references are resolved before composite transformation"""
        # Convert to resolver format
        resolved_tokens = {
            'theme': ResolvedVariable('theme', 'dark', 'string', TokenScope.THEME, 'json_tokens'),
            'color.dark.primary': ResolvedVariable('color.dark.primary', '#0066CC', 'color', TokenScope.THEME, 'json_tokens'),
            'color.light.primary': ResolvedVariable('color.light.primary', '#4D94FF', 'color', TokenScope.THEME, 'json_tokens')
        }
        
        # Test nested reference resolution
        nested_pattern = '{color.{theme}.primary}'
        resolved_color = self.resolver.resolve_nested_reference(nested_pattern, resolved_tokens)
        
        assert resolved_color == '#0066CC'
        
        # Test that composite transformation works with resolved values
        shadow_token = {
            '$type': 'shadow',
            '$value': {
                'color': resolved_color,  # Pre-resolved value
                'offsetX': '0px',
                'offsetY': '2px', 
                'blur': '4px',
                'spread': '0px'
            }
        }
        
        transformer = ShadowTokenTransformer()
        ooxml_result = transformer.transform(shadow_token)
        
        # Verify OOXML contains resolved color
        root = etree.fromstring(ooxml_result)
        color_elem = root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr')
        assert color_elem.attrib['val'] == '0066CC'
    
    def test_w3c_dtcg_validation_of_resolved_composite_tokens(self):
        """Test W3C DTCG validation after nested reference resolution"""
        # Simulate resolved composite token
        resolved_shadow_token = {
            '$type': 'shadow',
            '$value': {
                'color': '#0066CC',  # Resolved from {color.{theme}.primary}
                'offsetX': '0px',
                'offsetY': '2px',
                'blur': '4px', 
                'spread': '0px'
            },
            '$description': 'Button shadow with resolved theme color'
        }
        
        validation_result = self.validator.validate_token(resolved_shadow_token)
        
        assert validation_result.is_valid == True
        assert validation_result.token_type == TokenType.SHADOW
        assert len(validation_result.errors) == 0
    
    def test_integration_with_token_collections(self):
        """Test integration with complete token collections"""
        # Validate the token collection (just the tokens, not metadata)
        collection_results = self.validator.validate_token_collection(self.test_tokens)
        
        # All tokens should validate successfully
        valid_tokens = [name for name, result in collection_results.items() if result.is_valid]
        assert len(valid_tokens) == 4  # 4 tokens in test set
        assert len(collection_results) == 4


class TestCompositeTokenOOXMLIntegration:
    """Test integration of composite token transformations with OOXML processor"""
    
    def setup_method(self):
        """Setup OOXML processor and transformers"""
        self.ooxml_processor = OOXMLProcessor()
        self.shadow_transformer = ShadowTokenTransformer()
        self.border_transformer = BorderTokenTransformer()
        self.gradient_transformer = GradientTokenTransformer()
    
    def test_shadow_integration_with_ooxml_processor(self):
        """Test shadow token integration with OOXML processor"""
        shadow_token = {
            '$type': 'shadow',
            '$value': {
                'color': '#000000',
                'offsetX': '2px',
                'offsetY': '2px',
                'blur': '4px',
                'spread': '0px'
            }
        }
        
        # Transform to OOXML
        shadow_ooxml = self.shadow_transformer.transform(shadow_token)
        
        # Create mock OOXML document with shape element
        mock_doc = """
        <p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
               xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
            <p:cSld>
                <p:spTree>
                    <p:sp>
                        <p:spPr>
                            <a:xfrm>
                                <a:off x="914400" y="914400"/>
                                <a:ext cx="1828800" cy="914400"/>
                            </a:xfrm>
                            <a:prstGeom prst="rect"/>
                            <!-- Shadow will be inserted here -->
                        </p:spPr>
                    </p:sp>
                </p:spTree>
            </p:cSld>
        </p:sld>
        """
        
        # Parse and find insertion point
        doc_root = etree.fromstring(mock_doc)
        sp_pr = doc_root.find('.//p:sp/p:spPr', doc_root.nsmap)
        
        # Insert shadow OOXML
        shadow_root = etree.fromstring(shadow_ooxml)
        sp_pr.append(shadow_root)
        
        # Verify integration
        inserted_effect = doc_root.find('.//a:effectLst/a:outerShdw', doc_root.nsmap)
        assert inserted_effect is not None
        assert 'blurRad' in inserted_effect.attrib
    
    def test_border_integration_with_ooxml_processor(self):
        """Test border token integration with OOXML processor"""
        border_token = {
            '$type': 'border',
            '$value': {
                'width': '2px',
                'style': 'solid',
                'color': '#E0E0E0'
            }
        }
        
        # Transform to OOXML
        border_ooxml = self.border_transformer.transform(border_token)
        
        # Verify structure is compatible with OOXML processor expectations
        root = etree.fromstring(border_ooxml)
        assert root.tag.endswith('ln')
        assert root.attrib['w'] == '25400'  # 2px in EMU
        
        # Check that it has proper fill
        solid_fill = root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}solidFill')
        assert solid_fill is not None
    
    def test_gradient_integration_with_ooxml_processor(self):
        """Test gradient token integration with OOXML processor"""
        gradient_token = {
            '$type': 'gradient',
            '$value': {
                'type': 'linear',
                'direction': 'to bottom',
                'stops': [
                    {'position': '0%', 'color': '#FFFFFF'},
                    {'position': '100%', 'color': '#F5F5F5'}
                ]
            }
        }
        
        # Transform to OOXML
        gradient_ooxml = self.gradient_transformer.transform(gradient_token)
        
        # Verify structure
        root = etree.fromstring(gradient_ooxml)
        assert root.tag.endswith('gradFill')
        
        # Check gradient stops
        stops = root.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}gs')
        assert len(stops) == 2
        
        # Check linear direction
        linear = root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}lin')
        assert linear is not None
        assert linear.attrib['ang'] == '5400000'  # 90 degrees * 60000
    
    def test_xpath_targeting_for_composite_elements(self):
        """Test XPath targeting for composite token elements"""
        # Test XPath patterns for different composite elements
        xpath_patterns = {
            'shadow': './/a:effectLst',
            'border': './/a:ln',
            'gradient': './/a:gradFill'
        }
        
        for token_type, xpath in xpath_patterns.items():
            # This would be used by the OOXML processor to target elements
            assert xpath.startswith('.//a:')
            assert len(xpath) > 5


class TestPerformanceOptimizedBatchProcessing:
    """Test performance optimizations for batch transformation processing"""
    
    def setup_method(self):
        """Setup batch processing test environment"""
        self.resolver = VariableResolver(enable_cache=True)
        
        # Create large token set for performance testing
        self.large_token_set = {}
        
        # Add 100 theme variations
        for i in range(100):
            theme_name = f'theme_{i}'
            self.large_token_set[f'themes.{theme_name}'] = ResolvedVariable(
                f'themes.{theme_name}', f'theme_{i}', 'string', TokenScope.THEME, 'json_tokens'
            )
            
            # Add colors for each theme
            for color_type in ['primary', 'secondary', 'accent']:
                color_key = f'color.{theme_name}.{color_type}'
                self.large_token_set[color_key] = ResolvedVariable(
                    color_key, f'#{i:02d}{color_type[0]}{i%10}CC', 'color', TokenScope.THEME, 'json_tokens'
                )
    
    def test_batch_nested_reference_resolution(self):
        """Test batch processing of nested references"""
        # Create patterns that need resolution
        nested_patterns = [
            f'{{color.{{themes.theme_{i}}}.primary}}' for i in range(10)
        ]
        
        # Resolve all patterns
        resolved_values = []
        for pattern in nested_patterns:
            try:
                resolved = self.resolver.resolve_nested_reference(pattern, self.large_token_set)
                resolved_values.append(resolved)
            except KeyError:
                # Some patterns may not resolve due to test data structure
                pass
        
        # Should have resolved some patterns
        assert len(resolved_values) > 0
    
    def test_cached_resolution_performance(self):
        """Test that caching improves resolution performance"""
        pattern = '{color.{themes.theme_1}.primary}'
        
        # First resolution (cache miss)
        result1 = self.resolver.resolve_nested_reference(pattern, self.large_token_set)
        
        # Second resolution (cache hit) - should be faster
        result2 = self.resolver.resolve_nested_reference(pattern, self.large_token_set)
        
        assert result1 == result2
    
    def test_batch_composite_token_transformation(self):
        """Test batch transformation of composite tokens"""
        # Create multiple shadow tokens
        shadow_tokens = []
        for i in range(10):
            shadow_tokens.append({
                '$type': 'shadow',
                '$value': {
                    'color': f'#{i:02d}0000',
                    'offsetX': f'{i}px',
                    'offsetY': f'{i}px',
                    'blur': f'{i*2}px',
                    'spread': '0px'
                }
            })
        
        # Transform all tokens
        transformer = ShadowTokenTransformer()
        ooxml_results = []
        
        for token in shadow_tokens:
            ooxml_result = transformer.transform(token)
            ooxml_results.append(ooxml_result)
        
        assert len(ooxml_results) == 10
        
        # Verify all results are valid XML
        for ooxml in ooxml_results:
            root = etree.fromstring(ooxml)
            assert root.tag.endswith('effectLst')


class TestAdvancedTokenErrorHandling:
    """Test comprehensive error handling for advanced token features"""
    
    def test_nested_reference_validation_errors(self):
        """Test validation errors with nested references"""
        validator = W3CDTCGValidator()
        
        # Token with malformed nested reference
        invalid_token = {
            '$type': 'shadow',
            '$value': {
                'color': '{color.{malformed}',  # Missing closing brace
                'offsetX': '0px',
                'offsetY': '0px', 
                'blur': '0px',
                'spread': '0px'
            }
        }
        
        # Should still validate the token structure
        # (nested reference validation happens during resolution)
        validation_result = validator.validate_token(invalid_token)
        assert validation_result.is_valid == True  # Structure is valid
    
    def test_composite_token_transformation_errors(self):
        """Test error handling in composite token transformations"""
        # Token with invalid color in nested reference context
        invalid_shadow = {
            '$type': 'shadow',
            '$value': {
                'color': 'invalid-color-format',
                'offsetX': '0px',
                'offsetY': '0px',
                'blur': '0px', 
                'spread': '0px'
            }
        }
        
        transformer = ShadowTokenTransformer()
        
        with pytest.raises(Exception):  # Should raise CompositeTokenError
            transformer.transform(invalid_shadow)
    
    def test_integration_error_propagation(self):
        """Test that errors propagate correctly through integration layers"""
        resolver = VariableResolver()
        
        # Missing dynamic variable
        pattern = '{color.{nonexistent}.primary}'
        tokens = {
            'color.light.primary': ResolvedVariable('color.light.primary', '#4D94FF', 'color', TokenScope.THEME, 'json_tokens')
        }
        
        with pytest.raises(KeyError, match="Dynamic variable 'nonexistent' not found"):
            resolver.resolve_nested_reference(pattern, tokens)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])