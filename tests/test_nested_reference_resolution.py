#!/usr/bin/env python3
"""
Test suite for Nested Reference Resolution Engine

Tests the enhanced variable resolver capability to handle nested/dynamic
token references like {color.{theme}.primary} with recursive resolution.
"""

import pytest
from typing import Dict, Any, List
from unittest.mock import Mock, patch

# Import the enhanced resolver (will be implemented)
from tools.variable_resolver import VariableResolver, ResolvedVariable, CircularReferenceError
from tools.token_parser import TokenType, TokenScope


class TestNestedReferencePatterns:
    """Test recognition and parsing of nested reference patterns"""
    
    def test_simple_nested_reference_pattern(self):
        """Test basic nested reference like {color.{theme}.primary}"""
        pattern = "{color.{theme}.primary}"
        resolver = VariableResolver()
        
        # Should recognize as nested pattern
        assert resolver._is_nested_reference(pattern) == True
        
        # Should extract inner and outer parts
        parts = resolver._parse_nested_reference(pattern)
        expected = {
            'base': 'color',
            'dynamic': 'theme',
            'property': 'primary',
            'full_pattern': pattern
        }
        assert parts == expected
    
    def test_multiple_nested_levels(self):
        """Test deeply nested references like {section.{type}.{size}.value}"""
        pattern = "{section.{type}.{size}.value}"
        resolver = VariableResolver()
        
        assert resolver._is_nested_reference(pattern) == True
        
        parts = resolver._parse_nested_reference(pattern)
        expected = {
            'base': 'section',
            'dynamic': 'type',
            'nested_dynamic': 'size',
            'property': 'value',
            'full_pattern': pattern
        }
        assert parts == expected
    
    def test_simple_reference_not_nested(self):
        """Test that simple references are not recognized as nested"""
        simple_patterns = [
            "{color.primary}",
            "{spacing.large}",
            "{font.heading}"
        ]
        
        resolver = VariableResolver()
        for pattern in simple_patterns:
            assert resolver._is_nested_reference(pattern) == False
    
    def test_invalid_nested_patterns(self):
        """Test that malformed nested patterns are rejected"""
        invalid_patterns = [
            "{color.{theme}",  # Missing closing brace
            "{color.theme}.primary}",  # Missing opening brace
            "{color.{}.primary}",  # Empty dynamic part
            "{{theme}.primary}",  # Missing base
            "{color.{theme}.}",  # Missing property
        ]
        
        resolver = VariableResolver()
        for pattern in invalid_patterns:
            with pytest.raises(ValueError, match="Invalid nested reference pattern"):
                resolver._parse_nested_reference(pattern)
    
    def test_nested_reference_regex_patterns(self):
        """Test the regex patterns used for nested reference detection"""
        resolver = VariableResolver()
        
        # Test various valid nested patterns
        valid_patterns = [
            "{color.{theme}.primary}",
            "{spacing.{scale}.large}",
            "{typography.{brand}.heading.fontSize}",
            "{effects.{platform}.shadow.blur}"
        ]
        
        for pattern in valid_patterns:
            assert resolver._nested_reference_regex.match(pattern) is not None
        
        # Test patterns that should not match
        invalid_patterns = [
            "{simple.reference}",
            "not.a.reference",
            "{malformed.{reference",
            "{another}.malformed}"
        ]
        
        for pattern in invalid_patterns:
            assert resolver._nested_reference_regex.match(pattern) is None


class TestNestedReferenceResolution:
    """Test the actual resolution of nested references"""
    
    def setup_method(self):
        """Setup test data for resolution tests"""
        self.resolver = VariableResolver()
        
        # Mock token context
        self.test_tokens = {
            # Theme selector tokens
            'theme': ResolvedVariable(
                id='theme',
                value='dark',
                type=TokenType.TEXT,
                scope=TokenScope.THEME,
                source='json_tokens'
            ),
            'scale': ResolvedVariable(
                id='scale',
                value='large',
                type=TokenType.TEXT,
                scope=TokenScope.THEME,
                source='json_tokens'
            ),
            
            # Target tokens that will be resolved
            'color.dark.primary': ResolvedVariable(
                id='color.dark.primary',
                value='#0066CC',
                type=TokenType.COLOR,
                scope=TokenScope.THEME,
                source='json_tokens'
            ),
            'color.light.primary': ResolvedVariable(
                id='color.light.primary',
                value='#4D94FF',
                type=TokenType.COLOR,
                scope=TokenScope.THEME,
                source='json_tokens'
            ),
            'spacing.large.base': ResolvedVariable(
                id='spacing.large.base',
                value='24px',
                type=TokenType.DIMENSION,
                scope=TokenScope.THEME,
                source='json_tokens'
            ),
            'spacing.small.base': ResolvedVariable(
                id='spacing.small.base',
                value='8px',
                type=TokenType.DIMENSION,
                scope=TokenScope.THEME,
                source='json_tokens'
            )
        }
    
    def test_basic_nested_resolution(self):
        """Test resolving basic nested reference"""
        pattern = "{color.{theme}.primary}"
        
        result = self.resolver.resolve_nested_reference(pattern, self.test_tokens)
        
        # Should resolve theme='dark', then color.dark.primary='#0066CC'
        assert result == '#0066CC'
    
    def test_nested_resolution_with_different_values(self):
        """Test that changing the dynamic variable changes the result"""
        pattern = "{spacing.{scale}.base}"
        
        # Test with scale='large'
        result_large = self.resolver.resolve_nested_reference(pattern, self.test_tokens)
        assert result_large == '24px'
        
        # Change scale to 'small'
        self.test_tokens['scale'].value = 'small'
        result_small = self.resolver.resolve_nested_reference(pattern, self.test_tokens)
        assert result_small == '8px'
    
    def test_multi_level_nested_resolution(self):
        """Test resolving references with multiple nested levels"""
        # Add more complex nested tokens
        self.test_tokens['platform'] = ResolvedVariable(
            id='platform',
            value='web',
            type=TokenType.TEXT,
            scope=TokenScope.THEME,
            source='json_tokens'
        )
        
        self.test_tokens['effects.web.dark.shadow'] = ResolvedVariable(
            id='effects.web.dark.shadow',
            value='0 2px 4px rgba(0,0,0,0.1)',
            type=TokenType.TEXT,
            scope=TokenScope.THEME,
            source='json_tokens'
        )
        
        pattern = "{effects.{platform}.{theme}.shadow}"
        result = self.resolver.resolve_nested_reference(pattern, self.test_tokens)
        assert result == '0 2px 4px rgba(0,0,0,0.1)'
    
    def test_missing_dynamic_variable_error(self):
        """Test error when dynamic variable doesn't exist"""
        pattern = "{color.{nonexistent}.primary}"
        
        with pytest.raises(KeyError, match="Dynamic variable 'nonexistent' not found"):
            self.resolver.resolve_nested_reference(pattern, self.test_tokens)
    
    def test_missing_target_token_error(self):
        """Test error when final constructed token doesn't exist"""
        pattern = "{color.{theme}.secondary}"  # secondary doesn't exist
        
        with pytest.raises(KeyError, match="Token 'color.dark.secondary' not found"):
            self.resolver.resolve_nested_reference(pattern, self.test_tokens)
    
    def test_circular_reference_detection(self):
        """Test detection of circular references in nested patterns"""
        # Create circular reference
        self.test_tokens['circular_a'] = ResolvedVariable(
            id='circular_a',
            value='{type.{circular_b}.value}',
            type=TokenType.TEXT,
            scope=TokenScope.THEME,
            source='json_tokens'
        )
        
        self.test_tokens['circular_b'] = ResolvedVariable(
            id='circular_b',
            value='circular_a',
            type=TokenType.TEXT,
            scope=TokenScope.THEME,
            source='json_tokens'
        )
        
        pattern = "{type.{circular_a}.value}"
        
        with pytest.raises(CircularReferenceError, match="Circular reference detected"):
            self.resolver.resolve_nested_reference(pattern, self.test_tokens)
    
    def test_resolution_depth_limiting(self):
        """Test that resolution depth is limited to prevent infinite recursion"""
        # Create deeply nested chain
        for i in range(10):
            self.test_tokens[f'level_{i}'] = ResolvedVariable(
                id=f'level_{i}',
                value=f'level_{i+1}' if i < 9 else 'final',
                type=TokenType.TEXT,
                scope=TokenScope.THEME,
                source='json_tokens'
            )
        
        # This should hit depth limit
        pattern = "{deeply.{level_0}.nested.value}"
        
        with pytest.raises(ValueError, match="Maximum nesting depth exceeded"):
            self.resolver.resolve_nested_reference(pattern, self.test_tokens)


class TestNestedReferenceCache:
    """Test memoization and caching of nested reference resolutions"""
    
    def setup_method(self):
        """Setup resolver with cache for testing"""
        self.resolver = VariableResolver(enable_cache=True)
        
        self.test_tokens = {
            'theme': ResolvedVariable(
                id='theme',
                value='dark',
                type=TokenType.TEXT,
                scope=TokenScope.THEME,
                source='json_tokens'
            ),
            'color.dark.primary': ResolvedVariable(
                id='color.dark.primary',
                value='#0066CC',
                type=TokenType.COLOR,
                scope=TokenScope.THEME,
                source='json_tokens'
            )
        }
    
    def test_cache_hit_performance(self):
        """Test that repeated resolutions use cache"""
        pattern = "{color.{theme}.primary}"
        
        # First resolution - cache miss
        with patch.object(self.resolver, '_resolve_token_path') as mock_resolve:
            mock_resolve.return_value = '#0066CC'
            result1 = self.resolver.resolve_nested_reference(pattern, self.test_tokens)
            assert result1 == '#0066CC'
            assert mock_resolve.call_count == 1
        
        # Second resolution - should use cache
        with patch.object(self.resolver, '_resolve_token_path') as mock_resolve:
            result2 = self.resolver.resolve_nested_reference(pattern, self.test_tokens)
            assert result2 == '#0066CC'
            assert mock_resolve.call_count == 0  # Should not be called due to cache
    
    def test_cache_invalidation_on_context_change(self):
        """Test that cache is invalidated when token context changes"""
        pattern = "{color.{theme}.primary}"
        
        # First resolution
        result1 = self.resolver.resolve_nested_reference(pattern, self.test_tokens)
        assert result1 == '#0066CC'
        
        # Change theme value
        self.test_tokens['theme'].value = 'light'
        self.test_tokens['color.light.primary'] = ResolvedVariable(
            id='color.light.primary',
            value='#4D94FF',
            type=TokenType.COLOR,
            scope=TokenScope.THEME,
            source='json_tokens'
        )
        
        # Should resolve to new value (cache should be invalidated)
        result2 = self.resolver.resolve_nested_reference(pattern, self.test_tokens)
        assert result2 == '#4D94FF'
    
    def test_cache_key_generation(self):
        """Test that cache keys are generated correctly for different patterns"""
        patterns = [
            "{color.{theme}.primary}",
            "{color.{theme}.secondary}",
            "{spacing.{scale}.large}"
        ]
        
        resolver = VariableResolver(enable_cache=True)
        
        # Each pattern should generate different cache keys
        cache_keys = []
        for pattern in patterns:
            key = resolver._generate_cache_key(pattern, self.test_tokens)
            cache_keys.append(key)
        
        # All keys should be unique
        assert len(set(cache_keys)) == len(cache_keys)


class TestNestedReferenceIntegration:
    """Test integration with existing variable resolution system"""
    
    def test_integration_with_simple_references(self):
        """Test that nested references work alongside simple references"""
        resolver = VariableResolver()
        
        # Value containing both simple and nested references
        mixed_value = "Color: {color.{theme}.primary}, Size: {spacing.large}"
        
        test_tokens = {
            'theme': ResolvedVariable('theme', 'dark', TokenType.TEXT, TokenScope.THEME, 'json_tokens'),
            'color.dark.primary': ResolvedVariable('color.dark.primary', '#0066CC', TokenType.COLOR, TokenScope.THEME, 'json_tokens'),
            'spacing.large': ResolvedVariable('spacing.large', '24px', TokenType.DIMENSION, TokenScope.THEME, 'json_tokens')
        }
        
        result = resolver._resolve_token_references_in_value(mixed_value, test_tokens)
        expected = "Color: #0066CC, Size: 24px"
        assert result == expected
    
    def test_integration_with_formula_parser(self):
        """Test nested references work with mathematical expressions"""
        resolver = VariableResolver()
        
        # Expression with nested reference
        expression = "{spacing.{scale}.base} * 2"
        
        test_tokens = {
            'scale': ResolvedVariable('scale', 'large', TokenType.TEXT, TokenScope.THEME, 'json_tokens'),
            'spacing.large.base': ResolvedVariable('spacing.large.base', '16', TokenType.DIMENSION, TokenScope.THEME, 'json_tokens')
        }
        
        # Should resolve nested reference first, then evaluate expression
        result = resolver._resolve_token_references_in_value(expression, test_tokens)
        # After nested resolution: "16 * 2"
        # Note: Actual math evaluation would be handled by formula parser
        assert "16" in result
    
    def test_nested_references_in_ooxml_context(self):
        """Test nested references work with OOXML variable mapping"""
        resolver = VariableResolver()
        
        # OOXML-mapped variable with nested reference
        ooxml_variable = ResolvedVariable(
            id='theme_color',
            value='{color.{theme}.primary}',
            type=TokenType.COLOR,
            scope=TokenScope.THEME,
            source='extension_variables',
            xpath='//a:clrScheme/a:accent1/a:srgbClr/@val',
            ooxml_mapping={
                'namespace': 'http://schemas.openxmlformats.org/drawingml/2006/main',
                'element': 'srgbClr',
                'attribute': 'val'
            }
        )
        
        test_tokens = {
            'theme_color': ooxml_variable,
            'theme': ResolvedVariable('theme', 'dark', TokenType.TEXT, TokenScope.THEME, 'json_tokens'),
            'color.dark.primary': ResolvedVariable('color.dark.primary', '#0066CC', TokenType.COLOR, TokenScope.THEME, 'json_tokens')
        }
        
        resolved = resolver.resolve_all(test_tokens)
        
        # The theme_color should have resolved nested reference
        assert resolved['theme_color'].value == '#0066CC'
        assert resolved['theme_color'].xpath is not None  # Should preserve OOXML mapping


class TestNestedReferenceErrorHandling:
    """Test comprehensive error handling for nested references"""
    
    def test_detailed_error_messages(self):
        """Test that error messages provide helpful context"""
        resolver = VariableResolver()
        
        test_tokens = {
            'theme': ResolvedVariable('theme', 'dark', TokenType.TEXT, TokenScope.THEME, 'json_tokens')
        }
        
        pattern = "{color.{theme}.nonexistent}"
        
        try:
            resolver.resolve_nested_reference(pattern, test_tokens)
            assert False, "Should have raised an exception"
        except KeyError as e:
            error_msg = str(e)
            assert 'color.dark.nonexistent' in error_msg
            assert 'constructed from pattern' in error_msg
            assert pattern in error_msg
    
    def test_graceful_degradation(self):
        """Test graceful handling of partial resolution failures"""
        resolver = VariableResolver(strict_mode=False)
        
        test_tokens = {
            'theme': ResolvedVariable('theme', 'unknown', TokenType.TEXT, TokenScope.THEME, 'json_tokens')
        }
        
        pattern = "{color.{theme}.primary}"
        
        # In non-strict mode, should return original pattern if resolution fails
        result = resolver.resolve_nested_reference(pattern, test_tokens)
        assert result == pattern  # Should return original pattern
    
    def test_validation_of_resolution_chain(self):
        """Test validation of the entire resolution chain"""
        resolver = VariableResolver()
        
        # Test invalid resolution chain
        invalid_chains = [
            ("{color.{}.primary}", "Empty dynamic variable"),
            ("{.{theme}.primary}", "Empty base path"),
            ("{color.{theme}.}", "Empty property"),
        ]
        
        for pattern, expected_error in invalid_chains:
            with pytest.raises(ValueError, match=expected_error):
                resolver._validate_nested_pattern(pattern)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])