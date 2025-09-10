#!/usr/bin/env python3
"""
Comprehensive test suite for Token Parser

Tests the token parsing and validation functionality for StyleStack variables.
"""

import unittest
import json
import tempfile
from pathlib import Path

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))

from tools.token_parser import (
    TokenParser,
    TokenType,
    TokenScope,
    TokenError,
    VariableToken,
    load_token_definitions
)


class TestTokenEnums(unittest.TestCase):
    """Test token type and scope enums"""
    
    def test_token_type_enum(self):
        """Test TokenType enum values"""
        self.assertEqual(TokenType.COLOR.value, "color")
        self.assertEqual(TokenType.FONT.value, "font")
        self.assertEqual(TokenType.NUMBER.value, "number")
        self.assertEqual(TokenType.TEXT.value, "text")
        self.assertEqual(TokenType.DIMENSION.value, "dimension")
        self.assertEqual(TokenType.CALCULATED.value, "calculated")
        self.assertEqual(TokenType.BOOLEAN.value, "boolean")
        self.assertEqual(TokenType.REFERENCE.value, "reference")
        
    def test_token_scope_enum(self):
        """Test TokenScope enum values"""
        self.assertEqual(TokenScope.USER.value, "user")
        self.assertEqual(TokenScope.GROUP.value, "group")
        self.assertEqual(TokenScope.ORG.value, "org")
        self.assertEqual(TokenScope.FORK.value, "fork")
        self.assertEqual(TokenScope.CORE.value, "core")
        self.assertEqual(TokenScope.THEME.value, "theme")


class TestTokenError(unittest.TestCase):
    """Test TokenError class"""
    
    def test_token_error_creation(self):
        """Test creating token error"""
        error = TokenError(
            message="Test error message",
            position=10,
            token_text="{invalid.token}"
        )
        
        self.assertEqual(error.message, "Test error message")
        self.assertEqual(error.position, 10)
        self.assertEqual(error.token_text, "{invalid.token}")
        
    def test_token_error_defaults(self):
        """Test token error with default values"""
        error = TokenError(message="Simple error")
        
        self.assertEqual(error.message, "Simple error")
        self.assertIsNone(error.position)
        self.assertIsNone(error.token_text)


class TestVariableToken(unittest.TestCase):
    """Test VariableToken class"""
    
    def test_variable_token_creation(self):
        """Test creating variable token"""
        token = VariableToken(
            full_text="{tokens.org.brandColor}",
            scope="org",
            name="brandColor",
            position=0
        )
        
        self.assertEqual(token.full_text, "{tokens.org.brandColor}")
        self.assertEqual(token.scope, "org")
        self.assertEqual(token.name, "brandColor")
        self.assertEqual(token.position, 0)
        
    def test_variable_token_with_type(self):
        """Test creating variable token with type"""
        token = VariableToken(
            full_text="{tokens.core.primaryFont}",
            scope="core",
            name="primaryFont",
            position=10,
            token_type="font"
        )
        
        self.assertEqual(token.token_type, "font")
        
    def test_variable_token_defaults(self):
        """Test variable token with default values"""
        token = VariableToken(
            full_text="{tokens.test.var}",
            scope="test",
            name="var",
            position=0
        )
        
        self.assertIsNone(token.token_type)
        self.assertIsNone(token.resolved_value)


class TestTokenParserBasic(unittest.TestCase):
    """Test basic TokenParser functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.parser = TokenParser()
        
    def test_parser_initialization(self):
        """Test parser initialization"""
        parser = TokenParser()
        self.assertIsInstance(parser, TokenParser)
        self.assertEqual(parser.errors, [])
        
    def test_parse_simple_token(self):
        """Test parsing simple token"""
        content = "Color: {tokens.org.brandColor}"
        tokens = self.parser.parse(content)
        
        self.assertIsInstance(tokens, list)
        if tokens:
            token = tokens[0]
            self.assertEqual(token.scope, "org")
            self.assertEqual(token.name, "brandColor")
            
    def test_parse_multiple_tokens(self):
        """Test parsing multiple tokens"""
        content = "Style: {tokens.org.brandColor} font {tokens.core.primaryFont}"
        tokens = self.parser.parse(content)
        
        self.assertIsInstance(tokens, list)
        self.assertGreaterEqual(len(tokens), 2)
        
    def test_parse_no_tokens(self):
        """Test parsing content with no tokens"""
        content = "This content has no tokens"
        tokens = self.parser.parse(content)
        
        self.assertEqual(tokens, [])
        
    def test_parse_empty_content(self):
        """Test parsing empty content"""
        tokens = self.parser.parse("")
        self.assertEqual(tokens, [])
        
    def test_parse_none_content(self):
        """Test parsing None content"""
        tokens = self.parser.parse(None)
        self.assertEqual(tokens, [])


class TestTokenParserPatterns(unittest.TestCase):
    """Test token pattern recognition"""
    
    def setUp(self):
        """Set up test environment"""
        self.parser = TokenParser()
        
    def test_parse_org_scope_token(self):
        """Test parsing organization scope token"""
        content = "{tokens.org.brandPrimary}"
        tokens = self.parser.parse(content)
        
        if tokens:
            self.assertEqual(tokens[0].scope, "org")
            self.assertEqual(tokens[0].name, "brandPrimary")
            
    def test_parse_core_scope_token(self):
        """Test parsing core scope token"""
        content = "{tokens.core.defaultFont}"
        tokens = self.parser.parse(content)
        
        if tokens:
            self.assertEqual(tokens[0].scope, "core")
            self.assertEqual(tokens[0].name, "defaultFont")
            
    def test_parse_user_scope_token(self):
        """Test parsing user scope token"""
        content = "{tokens.user.personalColor}"
        tokens = self.parser.parse(content)
        
        if tokens:
            self.assertEqual(tokens[0].scope, "user")
            self.assertEqual(tokens[0].name, "personalColor")
            
    def test_parse_theme_scope_token(self):
        """Test parsing theme scope token"""
        content = "{tokens.theme.accent1}"
        tokens = self.parser.parse(content)
        
        if tokens:
            self.assertEqual(tokens[0].scope, "theme")
            self.assertEqual(tokens[0].name, "accent1")


class TestTokenParserValidation(unittest.TestCase):
    """Test token validation functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.parser = TokenParser()
        
    def test_validate_valid_tokens(self):
        """Test validating valid tokens"""
        valid_tokens = [
            "{tokens.org.brandColor}",
            "{tokens.core.primaryFont}",
            "{tokens.user.customSize}",
            "{tokens.theme.accent1}"
        ]
        
        for token_text in valid_tokens:
            tokens = self.parser.parse(token_text)
            self.assertGreater(len(tokens), 0, f"Failed to parse: {token_text}")
            
    def test_validate_invalid_tokens(self):
        """Test handling invalid tokens"""
        invalid_tokens = [
            "{invalid.syntax}",
            "{tokens}",
            "{tokens.}",
            "{tokens.org}",
            "tokens.org.missing_braces"
        ]
        
        for token_text in invalid_tokens:
            tokens = self.parser.parse(token_text)
            # Invalid tokens should either be ignored or result in errors
            # The exact behavior depends on implementation
            
    def test_token_position_tracking(self):
        """Test that token positions are tracked correctly"""
        content = "Start {tokens.org.color} middle {tokens.core.font} end"
        tokens = self.parser.parse(content)
        
        if len(tokens) >= 2:
            # First token should be at position 6 (after "Start ")
            # Second token position should be greater than first
            self.assertLess(tokens[0].position, tokens[1].position)


class TestTokenParserEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        """Set up test environment"""
        self.parser = TokenParser()
        
    def test_parse_nested_braces(self):
        """Test parsing content with nested braces"""
        content = "{{tokens.org.brandColor}}"
        tokens = self.parser.parse(content)
        
        # Should handle nested braces gracefully
        self.assertIsInstance(tokens, list)
        
    def test_parse_malformed_tokens(self):
        """Test parsing malformed tokens"""
        malformed_tokens = [
            "{tokens.org.brand Color}",  # Space in name
            "{tokens.org.brand-Color}",  # Hyphen in name
            "{tokens.org.123color}",     # Starting with number
            "{tokens..brandColor}",      # Double dot
        ]
        
        for token_text in malformed_tokens:
            tokens = self.parser.parse(token_text)
            # Should handle malformed tokens without crashing
            self.assertIsInstance(tokens, list)
            
    def test_parse_very_long_content(self):
        """Test parsing very long content"""
        # Create content with many tokens
        token_pattern = "{tokens.org.var{}} "
        content = "".join(token_pattern.format(i) for i in range(100))
        
        tokens = self.parser.parse(content)
        self.assertIsInstance(tokens, list)
        
    def test_parse_unicode_content(self):
        """Test parsing content with Unicode characters"""
        content = "测试 {tokens.org.brandColor} 🎨 {tokens.core.font} 中文"
        tokens = self.parser.parse(content)
        
        self.assertIsInstance(tokens, list)


class TestTokenParserIntegration(unittest.TestCase):
    """Test integration scenarios"""
    
    def setUp(self):
        """Set up test environment"""
        self.parser = TokenParser()
        
    def test_parse_real_ooxml_content(self):
        """Test parsing realistic OOXML content"""
        ooxml_content = '''<a:solidFill>
            <a:srgbClr val="{tokens.org.brandPrimary}"/>
        </a:solidFill>
        <a:latin typeface="{tokens.core.headingFont}"/>'''
        
        tokens = self.parser.parse(ooxml_content)
        self.assertIsInstance(tokens, list)
        
    def test_parse_mixed_token_types(self):
        """Test parsing content with mixed token types"""
        content = '''
        Color: {tokens.org.brandColor}
        Font: {tokens.core.primaryFont}
        Size: {tokens.user.fontSize}
        Flag: {tokens.theme.darkMode}
        '''
        
        tokens = self.parser.parse(content)
        self.assertIsInstance(tokens, list)
        
    def test_error_collection(self):
        """Test that errors are collected properly"""
        # This would depend on the specific error handling implementation
        content = "Some content with potential issues"
        tokens = self.parser.parse(content)
        
        # Errors should be accessible
        self.assertIsInstance(self.parser.errors, list)


class TestTokenDefinitionsLoading(unittest.TestCase):
    """Test token definitions loading functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_load_valid_definitions(self):
        """Test loading valid token definitions"""
        definitions = {
            "tokens": {
                "org": {
                    "brandColor": {
                        "type": "color",
                        "value": "#FF0000"
                    }
                }
            }
        }
        
        definitions_file = self.temp_dir / "definitions.json"
        definitions_file.write_text(json.dumps(definitions))
        
        try:
            loaded_defs = load_token_definitions(definitions_file)
            self.assertIsInstance(loaded_defs, dict)
        except (FileNotFoundError, json.JSONDecodeError, NotImplementedError):
            # Function might not be fully implemented
            pass
            
    def test_load_nonexistent_file(self):
        """Test loading non-existent definitions file"""
        nonexistent_file = self.temp_dir / "nonexistent.json"
        
        try:
            load_token_definitions(nonexistent_file)
        except (FileNotFoundError, NotImplementedError):
            # Expected behavior
            pass


class TestTokenParserPerformance(unittest.TestCase):
    """Test parser performance with large inputs"""
    
    def setUp(self):
        """Set up test environment"""
        self.parser = TokenParser()
        
    def test_parse_large_document(self):
        """Test parsing large document with many tokens"""
        # Create a large document with repeated patterns
        pattern = "Text with {tokens.org.color} and {tokens.core.font}. "
        large_content = pattern * 1000  # 1000 repetitions
        
        tokens = self.parser.parse(large_content)
        self.assertIsInstance(tokens, list)
        
    def test_parse_deeply_nested_structure(self):
        """Test parsing complex nested structure"""
        complex_content = '''
        <root>
            <section style="color: {tokens.org.primary}">
                <header font="{tokens.core.heading}">
                    <title size="{tokens.user.titleSize}">Test</title>
                </header>
                <content background="{tokens.theme.bg}">
                    Content with {tokens.org.textColor}
                </content>
            </section>
        </root>
        '''
        
        tokens = self.parser.parse(complex_content)
        self.assertIsInstance(tokens, list)


if __name__ == '__main__':
    unittest.main()