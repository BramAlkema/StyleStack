"""
Test suite for StyleStack Token Parser System

Tests the parsing, validation, and resolution of token syntax like:
- {tokens.org.brandColor}
- {tokens.theme.accent1}
- {tokens.user.personalFont}
- {tokens.group.departmentLogo}

Validates type checking, circular dependency detection, and error handling.
"""

import pytest
from typing import Dict, List, Any, Optional
import re
from dataclasses import dataclass
from enum import Enum


class TokenType(Enum):
    """Supported token value types"""
    COLOR = "color"
    FONT = "font" 
    NUMBER = "number"
    TEXT = "text"
    DIMENSION = "dimension"  # EMU, points, etc.
    CALCULATED = "calculated"  # Computed from other tokens


class TokenScope(Enum):
    """Token hierarchy scopes"""
    CORE = "core"          # Community defaults
    FORK = "fork"          # Fork-level defaults  
    ORG = "org"            # Organization overrides
    GROUP = "group"        # Group/department overrides
    USER = "user"          # Personal preferences
    THEME = "theme"        # OOXML theme references


@dataclass
class TokenError:
    """Represents a token parsing or validation error"""
    token: str
    message: str
    line: Optional[int] = None
    column: Optional[int] = None


@dataclass
class ParsedToken:
    """Represents a successfully parsed token"""
    original: str           # Original token string like "{tokens.org.brandColor}"
    scope: TokenScope       # org, theme, user, etc.
    identifier: str         # brandColor, accent1, etc.
    type: Optional[TokenType] = None
    value: Optional[str] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class TokenParser:
    """
    Parses StyleStack token syntax with validation and error recovery.
    
    Supports hierarchical token resolution with type checking:
    - {tokens.org.brandColor} → organization brand color
    - {tokens.theme.accent1} → OOXML theme accent color
    - {tokens.user.personalFont} → user's preferred font
    """
    
    TOKEN_PATTERN = re.compile(r'\{tokens\.([^.}]+)\.([^}]+)\}')
    
    def __init__(self):
        self.errors: List[TokenError] = []
        self.parsed_tokens: List[ParsedToken] = []
        
    def parse(self, content: str) -> List[ParsedToken]:
        """Parse all tokens in content string"""
        self.errors.clear()
        self.parsed_tokens.clear()
        
        matches = self.TOKEN_PATTERN.finditer(content)
        
        for match in matches:
            try:
                token = self._parse_single_token(match)
                if token:
                    self.parsed_tokens.append(token)
            except Exception as e:
                self.errors.append(TokenError(
                    token=match.group(0),
                    message=str(e),
                    line=content[:match.start()].count('\n') + 1,
                    column=match.start() - content.rfind('\n', 0, match.start())
                ))
        
        return self.parsed_tokens
        
    def _parse_single_token(self, match: re.Match) -> Optional[ParsedToken]:
        """Parse a single token match"""
        full_token = match.group(0)
        scope_str = match.group(1)
        identifier = match.group(2)
        
        # Validate scope
        try:
            scope = TokenScope(scope_str)
        except ValueError:
            raise ValueError(f"Invalid token scope '{scope_str}'. Valid scopes: {[s.value for s in TokenScope]}")
            
        # Validate identifier format
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', identifier):
            raise ValueError(f"Invalid identifier '{identifier}'. Must start with letter and contain only letters, numbers, underscore")
            
        return ParsedToken(
            original=full_token,
            scope=scope,
            identifier=identifier
        )
    
    def validate_types(self, tokens: List[ParsedToken], type_definitions: Dict[str, TokenType]) -> List[TokenError]:
        """Validate token types against definitions"""
        validation_errors = []
        
        for token in tokens:
            key = f"{token.scope.value}.{token.identifier}"
            if key in type_definitions:
                token.type = type_definitions[key]
            else:
                validation_errors.append(TokenError(
                    token=token.original,
                    message=f"No type definition found for token '{key}'"
                ))
                
        return validation_errors
    
    def detect_circular_dependencies(self, tokens: List[ParsedToken]) -> List[TokenError]:
        """Detect circular dependencies in token references"""
        # Build dependency graph
        graph = {}
        for token in tokens:
            key = f"{token.scope.value}.{token.identifier}"
            graph[key] = token.dependencies or []
        
        # Find cycles using DFS
        visited = set()
        rec_stack = set()
        circular_errors = []
        
        def has_cycle(node: str, path: List[str]) -> bool:
            if node not in graph:
                return False
                
            if node in rec_stack:
                cycle_start = path.index(node)
                cycle_path = " → ".join(path[cycle_start:] + [node])
                circular_errors.append(TokenError(
                    token=f"{{tokens.{node.replace('.', '.', 1)}}}",
                    message=f"Circular dependency detected: {cycle_path}"
                ))
                return True
                
            if node in visited:
                return False
                
            visited.add(node)
            rec_stack.add(node)
            
            for dep in graph[node]:
                if has_cycle(dep, path + [node]):
                    return True
                    
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                has_cycle(node, [])
                
        return circular_errors


class TestTokenParser:
    """Test suite for token parser functionality"""
    
    def test_basic_token_parsing(self):
        """Test parsing basic token syntax"""
        parser = TokenParser()
        content = "Color: {tokens.org.brandColor} Font: {tokens.theme.accent1}"
        
        tokens = parser.parse(content)
        
        assert len(tokens) == 2
        assert len(parser.errors) == 0
        
        # Check first token
        assert tokens[0].original == "{tokens.org.brandColor}"
        assert tokens[0].scope == TokenScope.ORG
        assert tokens[0].identifier == "brandColor"
        
        # Check second token  
        assert tokens[1].original == "{tokens.theme.accent1}"
        assert tokens[1].scope == TokenScope.THEME
        assert tokens[1].identifier == "accent1"
    
    def test_invalid_token_scope(self):
        """Test parsing with invalid scope"""
        parser = TokenParser()
        content = "{tokens.invalid.someColor}"
        
        tokens = parser.parse(content)
        
        assert len(tokens) == 0
        assert len(parser.errors) == 1
        assert "Invalid token scope 'invalid'" in parser.errors[0].message
    
    def test_invalid_identifier_format(self):
        """Test parsing with invalid identifier"""
        parser = TokenParser()
        test_cases = [
            "{tokens.org.123invalid}",  # Starts with number
            "{tokens.org.invalid-name}",  # Contains hyphen
            "{tokens.org.invalid.name}",  # Contains dot
            "{tokens.org.}",  # Empty identifier
        ]
        
        for content in test_cases:
            parser = TokenParser()  # Fresh parser for each test
            tokens = parser.parse(content)
            assert len(tokens) == 0, f"Should reject: {content}"
            assert len(parser.errors) == 1, f"Should have error for: {content}"
    
    def test_valid_token_scopes(self):
        """Test all valid token scopes"""
        parser = TokenParser()
        valid_tokens = [
            "{tokens.core.baseFont}",
            "{tokens.fork.defaultColor}",
            "{tokens.org.brandColor}",
            "{tokens.group.departmentLogo}",
            "{tokens.user.personalFont}",
            "{tokens.theme.accent1}"
        ]
        
        content = " ".join(valid_tokens)
        tokens = parser.parse(content)
        
        assert len(tokens) == 6
        assert len(parser.errors) == 0
        
        expected_scopes = [TokenScope.CORE, TokenScope.FORK, TokenScope.ORG, 
                          TokenScope.GROUP, TokenScope.USER, TokenScope.THEME]
        for i, token in enumerate(tokens):
            assert token.scope == expected_scopes[i]
    
    def test_complex_content_parsing(self):
        """Test parsing tokens embedded in complex content"""
        parser = TokenParser()
        content = '''
        <a:solidFill>
          <a:srgbClr val="{tokens.org.primaryColor}"/>
        </a:solidFill>
        <a:latin typeface="{tokens.theme.majorFont}"/>
        Size: {tokens.user.fontSize}pt
        '''
        
        tokens = parser.parse(content)
        
        assert len(tokens) == 3
        assert len(parser.errors) == 0
        
        identifiers = [t.identifier for t in tokens]
        assert "primaryColor" in identifiers
        assert "majorFont" in identifiers  
        assert "fontSize" in identifiers
    
    def test_type_validation(self):
        """Test token type validation against definitions"""
        parser = TokenParser()
        content = "{tokens.org.brandColor} {tokens.theme.majorFont} {tokens.user.fontSize}"
        
        tokens = parser.parse(content)
        
        type_definitions = {
            "org.brandColor": TokenType.COLOR,
            "theme.majorFont": TokenType.FONT,
            "user.fontSize": TokenType.NUMBER
        }
        
        errors = parser.validate_types(tokens, type_definitions)
        
        assert len(errors) == 0
        assert tokens[0].type == TokenType.COLOR
        assert tokens[1].type == TokenType.FONT
        assert tokens[2].type == TokenType.NUMBER
    
    def test_missing_type_definition(self):
        """Test validation with missing type definitions"""
        parser = TokenParser()
        content = "{tokens.org.unknownToken}"
        
        tokens = parser.parse(content)
        type_definitions = {}  # Empty definitions
        
        errors = parser.validate_types(tokens, type_definitions)
        
        assert len(errors) == 1
        assert "No type definition found" in errors[0].message
    
    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies"""
        parser = TokenParser()
        
        # Create tokens with circular references
        token_a = ParsedToken(
            original="{tokens.org.colorA}",
            scope=TokenScope.ORG,
            identifier="colorA",
            dependencies=["org.colorB"]
        )
        
        token_b = ParsedToken(
            original="{tokens.org.colorB}",
            scope=TokenScope.ORG, 
            identifier="colorB",
            dependencies=["org.colorA"]  # Circular reference
        )
        
        tokens = [token_a, token_b]
        errors = parser.detect_circular_dependencies(tokens)
        
        assert len(errors) == 1
        assert "Circular dependency detected" in errors[0].message
        assert "org.colorA → org.colorB" in errors[0].message
    
    def test_complex_dependency_chain(self):
        """Test complex dependency chains without cycles"""
        parser = TokenParser()
        
        tokens = [
            ParsedToken("{tokens.org.primary}", TokenScope.ORG, "primary", dependencies=["theme.accent1"]),
            ParsedToken("{tokens.theme.accent1}", TokenScope.THEME, "accent1", dependencies=["core.baseColor"]),
            ParsedToken("{tokens.core.baseColor}", TokenScope.CORE, "baseColor", dependencies=[])
        ]
        
        errors = parser.detect_circular_dependency(tokens)
        assert len(errors) == 0  # No circular dependencies
    
    def test_error_line_column_reporting(self):
        """Test accurate line and column error reporting"""
        parser = TokenParser()
        content = """Line 1
Line 2 with {tokens.invalid.scope} 
Line 3"""
        
        tokens = parser.parse(content)
        
        assert len(parser.errors) == 1
        error = parser.errors[0]
        assert error.line == 2
        assert error.column > 0
        assert "invalid" in error.message
    
    def test_token_hierarchy_precedence(self):
        """Test understanding of token hierarchy for resolution precedence"""
        parser = TokenParser()
        content = """
        {tokens.user.brandColor}
        {tokens.group.brandColor}  
        {tokens.org.brandColor}
        {tokens.fork.brandColor}
        {tokens.core.brandColor}
        """
        
        tokens = parser.parse(content)
        
        assert len(tokens) == 5
        scopes = [t.scope for t in tokens]
        
        # Verify all hierarchy levels are represented
        assert TokenScope.USER in scopes
        assert TokenScope.GROUP in scopes
        assert TokenScope.ORG in scopes
        assert TokenScope.FORK in scopes
        assert TokenScope.CORE in scopes
    
    def test_theme_reference_tokens(self):
        """Test OOXML theme reference tokens"""
        parser = TokenParser()
        theme_tokens = [
            "{tokens.theme.accent1}",
            "{tokens.theme.accent2}",
            "{tokens.theme.dk1}",
            "{tokens.theme.lt1}",
            "{tokens.theme.majorFont}",
            "{tokens.theme.minorFont}"
        ]
        
        content = " ".join(theme_tokens)
        tokens = parser.parse(content)
        
        assert len(tokens) == 6
        assert all(t.scope == TokenScope.THEME for t in tokens)
        
        identifiers = [t.identifier for t in tokens]
        assert "accent1" in identifiers
        assert "majorFont" in identifiers
        assert "minorFont" in identifiers
    
    def test_performance_with_large_token_set(self):
        """Test parser performance with large number of tokens"""
        parser = TokenParser()
        
        # Generate large content with many tokens
        token_count = 1000
        tokens = []
        for i in range(token_count):
            tokens.append(f"{{tokens.org.color{i}}}")
        
        content = " ".join(tokens)
        
        import time
        start_time = time.time()
        parsed_tokens = parser.parse(content)
        end_time = time.time()
        
        assert len(parsed_tokens) == token_count
        assert len(parser.errors) == 0
        
        # Should parse 1000 tokens in under 1 second
        assert (end_time - start_time) < 1.0
    
    def test_malformed_token_recovery(self):
        """Test parser recovery from malformed tokens"""
        parser = TokenParser()
        content = """
        Valid: {tokens.org.validColor}
        Malformed: {tokens.invalid}  
        Another valid: {tokens.theme.accent1}
        Missing close: {tokens.org.incomplete
        """
        
        tokens = parser.parse(content)
        
        # Should successfully parse the valid tokens despite malformed ones
        assert len(tokens) >= 2  # At least the valid ones
        valid_identifiers = [t.identifier for t in tokens]
        assert "validColor" in valid_identifiers
        assert "accent1" in valid_identifiers


if __name__ == "__main__":
    # Run basic tests
    parser = TokenParser()
    
    # Test basic functionality
    test_content = "Color: {tokens.org.brandColor} Font: {tokens.theme.majorFont}"
    tokens = parser.parse(test_content)
    
    print(f"✅ Parsed {len(tokens)} tokens successfully")
    print(f"✅ Errors: {len(parser.errors)}")
    
    for token in tokens:
        print(f"  - {token.original} → {token.scope.value}.{token.identifier}")
    
    # Test type validation
    type_definitions = {
        "org.brandColor": TokenType.COLOR,
        "theme.majorFont": TokenType.FONT
    }
    
    validation_errors = parser.validate_types(tokens, type_definitions)
    print(f"✅ Type validation errors: {len(validation_errors)}")
    
    print("Token parser implementation complete!")