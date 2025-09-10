"""
StyleStack Token Parser

Production implementation for parsing and validating token syntax in OOXML templates.
Supports hierarchical token resolution with type checking and error recovery.

Token Syntax:
- {tokens.org.brandColor}     → Organization brand color
- {tokens.theme.accent1}      → OOXML theme accent color  
- {tokens.user.personalFont}  → User's preferred font
- {tokens.group.logo}         → Department/group assets
- {tokens.core.defaultSize}   → Community baseline values

Usage:
    parser = TokenParser()
    tokens = parser.parse(content)
    
    if parser.errors:
        for error in parser.errors:
            print(f"Error: {error.message}")
"""

from typing import Any, Dict, List, Optional, Union
import re
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class TokenType(Enum):
    """Supported token value types matching OOXML capabilities"""
    COLOR = "color"           # RGB, theme colors, scheme colors
    FONT = "font"             # Font family, theme fonts
    NUMBER = "number"         # Numeric values, percentages
    TEXT = "text"             # String values, labels
    DIMENSION = "dimension"   # EMU, points, pixels
    CALCULATED = "calculated" # Computed from other tokens
    BOOLEAN = "boolean"       # True/false flags
    REFERENCE = "reference"   # References to other elements


class TokenScope(Enum):
    """Token hierarchy scopes with resolution precedence (high to low)"""
    USER = "user"       # Personal preferences (highest precedence)
    GROUP = "group"     # Department/team overrides
    ORG = "org"         # Organization overrides  
    FORK = "fork"       # Fork-level defaults
    CORE = "core"       # Community baseline (lowest precedence)
    THEME = "theme"     # OOXML theme references (special)


@dataclass
class TokenError:
    """Represents a token parsing or validation error with location info"""
    token: str
    message: str
    error_type: str = "parse"
    line: Optional[int] = None
    column: Optional[int] = None
    context: Optional[str] = None
    
    def __str__(self) -> str:
        location = f"line {self.line}, col {self.column}" if self.line else "unknown location"
        return f"[{self.error_type.upper()}] {self.message} in '{self.token}' at {location}"


@dataclass
class VariableToken:
    """
    Represents a parsed and validated token with full metadata.
    
    This is the core data structure for token resolution and OOXML mapping.
    """
    original: str                    # Original token string: "{tokens.org.brandColor}"
    scope: TokenScope               # Hierarchy scope: org, user, theme, etc.
    identifier: str                 # Token identifier: brandColor, accent1, etc.
    type: Optional[TokenType] = None # Value type: color, font, number, etc.
    value: Optional[str] = None     # Resolved value
    default_value: Optional[str] = None # Fallback value
    dependencies: List[str] = field(default_factory=list) # Other tokens this depends on
    xpath: Optional[str] = None     # OOXML XPath for this token
    ooxml_mapping: Optional[Dict[str, Any]] = None # OOXML element mapping
    description: Optional[str] = None # Human-readable description
    
    @property
    def key(self) -> str:
        """Unique key for this token: scope.identifier"""
        return f"{self.scope.value}.{self.identifier}"
    
    @property
    def is_theme_reference(self) -> bool:
        """True if this token references OOXML theme elements"""
        return self.scope == TokenScope.THEME
        
    @property
    def precedence(self) -> int:
        """Precedence level for resolution (higher = more specific)"""
        precedence_map = {
            TokenScope.USER: 5,
            TokenScope.GROUP: 4,
            TokenScope.ORG: 3,
            TokenScope.FORK: 2,
            TokenScope.CORE: 1,
            TokenScope.THEME: 0  # Special case - not part of hierarchy
        }
        return precedence_map.get(self.scope, 0)
    
    def validate_type_constraints(self) -> List[str]:
        """Validate token value against type constraints"""
        errors = []
        
        if not self.type or not self.value:
            return errors
            
        if self.type == TokenType.COLOR:
            if not self._is_valid_color(self.value):
                errors.append(f"Invalid color format: '{self.value}'. Expected hex (#RRGGBB) or theme reference.")
                
        elif self.type == TokenType.NUMBER:
            try:
                float(self.value)
            except ValueError:
                errors.append(f"Invalid number format: '{self.value}'")
                
        elif self.type == TokenType.DIMENSION:
            if not re.match(r'^\d+(\.\d+)?(pt|px|em|%)$', self.value):
                errors.append(f"Invalid dimension format: '{self.value}'. Expected number with unit (pt, px, em, %)")
                
        elif self.type == TokenType.BOOLEAN:
            if self.value.lower() not in ['true', 'false', '1', '0']:
                errors.append(f"Invalid boolean format: '{self.value}'. Expected true/false or 1/0")
        
        return errors
    
    def _is_valid_color(self, color: str) -> bool:
        """Validate color format"""
        # Hex color
        if re.match(r'^#[0-9A-Fa-f]{6}$', color):
            return True
            
        # Theme color reference
        theme_colors = ['accent1', 'accent2', 'accent3', 'accent4', 'accent5', 'accent6',
                       'dk1', 'lt1', 'dk2', 'lt2', 'hlink', 'folHlink']
        if color in theme_colors:
            return True
            
        # Named colors (basic set)
        named_colors = ['black', 'white', 'red', 'green', 'blue', 'yellow', 'cyan', 'magenta']
        if color.lower() in named_colors:
            return True
            
        return False


class TokenParser:
    """
    Advanced token parser with validation, error recovery, and performance optimization.
    
    Features:
    - Comprehensive token syntax validation
    - Type checking and constraint validation
    - Circular dependency detection
    - Error recovery and detailed reporting
    - Performance optimization for large token sets
    """
    
    # Enhanced regex pattern with more precise matching
    TOKEN_PATTERN = re.compile(r'\{tokens\.([a-z][a-z0-9_]*)\.([a-zA-Z][a-zA-Z0-9_]*)\}')
    
    def __init__(self, variable_definitions: Optional[Dict[str, Any]] = None):
        """
        Initialize parser with optional variable definitions.
        
        Args:
            variable_definitions: Dictionary of token definitions for validation
        """
        self.errors: List[TokenError] = []
        self.parsed_tokens: List[VariableToken] = []
        self.variable_definitions = variable_definitions or {}
        self._validation_cache: Dict[str, bool] = {}
        
    def parse(self, content: str, source_file: Optional[str] = None) -> List[VariableToken]:
        """
        Parse all tokens in content with comprehensive validation.
        
        Args:
            content: Content to parse for tokens
            source_file: Optional source file path for error reporting
            
        Returns:
            List of successfully parsed VariableToken objects
        """
        self.errors.clear()
        self.parsed_tokens.clear()
        
        # Find all token matches
        matches = list(self.TOKEN_PATTERN.finditer(content))
        
        for match in matches:
            try:
                token = self._parse_single_token(match, content, source_file)
                if token:
                    self.parsed_tokens.append(token)
            except Exception as e:
                self._add_error(match, str(e), content, "parse")
        
        # Post-processing validation
        self._validate_token_definitions()
        self._detect_circular_dependencies()
        
        return self.parsed_tokens
    
    def _parse_single_token(self, match: re.Match, content: str, source_file: Optional[str]) -> Optional[VariableToken]:
        """Parse and validate a single token match"""
        full_token = match.group(0)
        scope_str = match.group(1)
        identifier = match.group(2)
        
        # Validate scope
        try:
            scope = TokenScope(scope_str)
        except ValueError:
            valid_scopes = [s.value for s in TokenScope]
            raise ValueError(f"Invalid scope '{scope_str}'. Valid scopes: {', '.join(valid_scopes)}")
        
        # Validate identifier format  
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', identifier):
            raise ValueError(f"Invalid identifier '{identifier}'. Must start with letter, contain only letters/numbers/underscore")
        
        # Create basic token
        token = VariableToken(
            original=full_token,
            scope=scope,
            identifier=identifier
        )
        
        # Enhance with definition data if available
        self._enhance_token_from_definition(token)
        
        return token
    
    def _enhance_token_from_definition(self, token: VariableToken) -> None:
        """Enhance token with data from variable definitions"""
        definition = self.variable_definitions.get(token.key)
        if not definition:
            return
            
        # Map definition properties to token
        if 'type' in definition:
            try:
                token.type = TokenType(definition['type'])
            except ValueError:
                self.errors.append(TokenError(
                    token=token.original,
                    message=f"Invalid type '{definition['type']}' in definition",
                    error_type="definition"
                ))
        
        token.default_value = definition.get('defaultValue')
        token.xpath = definition.get('xpath')  
        token.ooxml_mapping = definition.get('ooxml')
        token.description = definition.get('description')
        token.dependencies = definition.get('dependencies', [])
        
    def _validate_token_definitions(self) -> None:
        """Validate parsed tokens against their definitions"""
        for token in self.parsed_tokens:
            # Type constraint validation
            validation_errors = token.validate_type_constraints()
            for error_msg in validation_errors:
                self.errors.append(TokenError(
                    token=token.original,
                    message=error_msg,
                    error_type="validation"
                ))
            
            # Required field validation
            if token.type is None and token.key in self.variable_definitions:
                self.errors.append(TokenError(
                    token=token.original,
                    message="Missing type definition",
                    error_type="definition"
                ))
    
    def _detect_circular_dependencies(self) -> None:
        """Detect circular dependencies using DFS"""
        # Build dependency graph
        graph = {}
        for token in self.parsed_tokens:
            graph[token.key] = token.dependencies.copy()
        
        # DFS cycle detection
        WHITE, GRAY, BLACK = 0, 1, 2
        colors = {key: WHITE for key in graph}
        
        def dfs(node: str, path: List[str]) -> bool:
            if colors.get(node, WHITE) == GRAY:
                # Found cycle
                cycle_start = path.index(node) if node in path else 0
                cycle_path = ' → '.join(path[cycle_start:] + [node])
                
                self.errors.append(TokenError(
                    token=f"{{tokens.{node.replace('.', '.', 1)}}}",
                    message=f"Circular dependency: {cycle_path}",
                    error_type="dependency"
                ))
                return True
                
            if colors.get(node, WHITE) == BLACK:
                return False
                
            # Mark as visiting
            colors[node] = GRAY
            
            # Visit dependencies
            for dep in graph.get(node, []):
                if dfs(dep, path + [node]):
                    return True
            
            # Mark as visited
            colors[node] = BLACK
            return False
        
        # Check all nodes
        for node in graph:
            if colors.get(node, WHITE) == WHITE:
                dfs(node, [])
    
    def _add_error(self, match: re.Match, message: str, content: str, error_type: str = "parse") -> None:
        """Add error with location information"""
        line_number = content[:match.start()].count('\n') + 1
        line_start = content.rfind('\n', 0, match.start()) + 1
        column = match.start() - line_start + 1
        
        # Extract context line
        line_end = content.find('\n', match.start())
        if line_end == -1:
            line_end = len(content)
        context = content[line_start:line_end].strip()
        
        self.errors.append(TokenError(
            token=match.group(0),
            message=message,
            error_type=error_type,
            line=line_number,
            column=column,
            context=context
        ))
    
    def get_tokens_by_scope(self, scope: TokenScope) -> List[VariableToken]:
        """Get all tokens matching a specific scope"""
        return [token for token in self.parsed_tokens if token.scope == scope]
    
    def get_tokens_by_type(self, token_type: TokenType) -> List[VariableToken]:
        """Get all tokens matching a specific type"""
        return [token for token in self.parsed_tokens if token.type == token_type]
    
    def resolve_token_hierarchy(self, identifier: str) -> Optional[VariableToken]:
        """
        Resolve token by identifier using hierarchy precedence.
        Returns the highest precedence token matching the identifier.
        """
        matching_tokens = [t for t in self.parsed_tokens if t.identifier == identifier]
        if not matching_tokens:
            return None
            
        # Sort by precedence (highest first)
        matching_tokens.sort(key=lambda t: t.precedence, reverse=True)
        return matching_tokens[0]
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        return {
            'summary': {
                'total_tokens': len(self.parsed_tokens),
                'total_errors': len(self.errors),
                'error_types': self._count_errors_by_type(),
                'scopes_found': list(set(t.scope.value for t in self.parsed_tokens)),
                'types_found': list(set(t.type.value for t in self.parsed_tokens if t.type))
            },
            'tokens': [
                {
                    'original': t.original,
                    'scope': t.scope.value,
                    'identifier': t.identifier,
                    'type': t.type.value if t.type else None,
                    'has_definition': t.key in self.variable_definitions,
                    'precedence': t.precedence
                }
                for t in self.parsed_tokens
            ],
            'errors': [
                {
                    'token': e.token,
                    'message': e.message,
                    'type': e.error_type,
                    'line': e.line,
                    'column': e.column,
                    'context': e.context
                }
                for e in self.errors
            ],
            'hierarchy_analysis': self._analyze_token_hierarchy()
        }
    
    def _count_errors_by_type(self) -> Dict[str, int]:
        """Count errors by type"""
        counts = {}
        for error in self.errors:
            counts[error.error_type] = counts.get(error.error_type, 0) + 1
        return counts
    
    def _analyze_token_hierarchy(self) -> Dict[str, Any]:
        """Analyze token hierarchy coverage and conflicts"""
        identifier_groups = {}
        
        # Group tokens by identifier
        for token in self.parsed_tokens:
            if token.identifier not in identifier_groups:
                identifier_groups[token.identifier] = []
            identifier_groups[token.identifier].append(token)
        
        analysis = {
            'total_identifiers': len(identifier_groups),
            'identifiers_with_hierarchy': 0,
            'identifiers_with_conflicts': 0,
            'coverage_by_scope': {scope.value: 0 for scope in TokenScope}
        }
        
        for identifier, tokens in identifier_groups.items():
            if len(tokens) > 1:
                analysis['identifiers_with_hierarchy'] += 1
                
            # Check for type conflicts
            types = set(t.type for t in tokens if t.type)
            if len(types) > 1:
                analysis['identifiers_with_conflicts'] += 1
        
        # Count coverage by scope
        for token in self.parsed_tokens:
            analysis['coverage_by_scope'][token.scope.value] += 1
            
        return analysis


def load_token_definitions(definitions_path: Union[str, Path]) -> Dict[str, Any]:
    """Load token definitions from JSON file"""
    path = Path(definitions_path)
    
    if not path.exists():
        return {}
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Flatten nested variable definitions
    definitions = {}
    
    def flatten_variables(obj, prefix=''):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict) and 'type' in value and 'scope' in value:
                    # This is a variable definition
                    var_key = f"{value['scope']}.{value.get('id', key)}"
                    definitions[var_key] = value
                elif isinstance(value, dict):
                    # Continue flattening
                    flatten_variables(value, new_key)
    
    flatten_variables(data)
    return definitions


if __name__ == "__main__":
    # Demo usage
    parser = TokenParser()
    
    sample_content = """
    <a:solidFill>
        <a:srgbClr val="{tokens.org.primaryColor}"/>
    </a:solidFill>
    <a:latin typeface="{tokens.theme.majorFont}"/>
    Font size: {tokens.user.fontSize}pt
    Background: {tokens.group.backgroundColor}
    """
    
    print("🔍 Parsing sample content...")
    tokens = parser.parse(sample_content)
    
    print(f"✅ Found {len(tokens)} tokens")
    for token in tokens:
        print(f"  - {token.original} → {token.scope.value}.{token.identifier}")
    
    if parser.errors:
        print(f"\n❌ {len(parser.errors)} errors found:")
        for error in parser.errors:
            print(f"  - {error}")
    
    # Generate validation report
    report = parser.generate_validation_report()
    print(f"\n📊 Validation Report:")
    print(f"  - Total tokens: {report['summary']['total_tokens']}")
    print(f"  - Total errors: {report['summary']['total_errors']}")
    print(f"  - Scopes found: {', '.join(report['summary']['scopes_found'])}")