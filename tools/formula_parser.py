#!/usr/bin/env python3
"""
Formula Parser Engine for Design Token Formula Evaluation System

Parses mathematical expressions containing variables, functions, and operators
into Abstract Syntax Trees for dependency analysis and evaluation.
"""


from typing import Dict, List, Set, Any, Union, Optional
import re
from enum import Enum
from dataclasses import dataclass


class TokenType(Enum):
    """Token types for lexical analysis"""
    # Literals
    NUMBER = "NUMBER"
    IDENTIFIER = "IDENTIFIER"
    
    # Operators
    PLUS = "PLUS"
    MINUS = "MINUS"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    MODULO = "MODULO"
    POWER = "POWER"
    EQUALS = "EQUALS"
    
    # Delimiters
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    COMMA = "COMMA"
    
    # Special
    EOF = "EOF"
    NEWLINE = "NEWLINE"


@dataclass
class Token:
    """Token representing a lexical unit"""
    type: TokenType
    value: Any
    position: int = 0
    line: int = 1
    column: int = 1
    
    def __str__(self) -> str:
        return f"Token({self.type.value}, {self.value})"


class FormulaError(Exception):
    """Base exception for formula processing errors"""
    def __init__(self, message: str, position: int = 0, line: int = 1, column: int = 1):
        self.message = message
        self.position = position
        self.line = line
        self.column = column
        super().__init__(f"Line {line}, Column {column}: {message}")


class SyntaxError(FormulaError):
    """Syntax error during parsing"""
    pass


class EvaluationError(FormulaError):
    """Error during expression evaluation"""
    pass


# Abstract Syntax Tree node classes
class ExpressionAST:
    """Base class for all AST nodes"""
    pass


@dataclass
class NumberAST(ExpressionAST):
    """AST node for numeric literals"""
    value: Union[int, float]
    
    def __str__(self) -> str:
        return f"Num({self.value})"


@dataclass
class VariableAST(ExpressionAST):
    """AST node for variable references"""
    name: str
    
    def __str__(self) -> str:
        return f"Var({self.name})"


@dataclass
class BinaryOpAST(ExpressionAST):
    """AST node for binary operations"""
    left: ExpressionAST
    operator: str
    right: ExpressionAST
    
    def __str__(self) -> str:
        return f"BinOp({self.left} {self.operator} {self.right})"


@dataclass
class UnaryOpAST(ExpressionAST):
    """AST node for unary operations"""
    operator: str
    operand: ExpressionAST
    
    def __str__(self) -> str:
        return f"UnaryOp({self.operator}{self.operand})"


@dataclass
class FunctionCallAST(ExpressionAST):
    """AST node for function calls"""
    name: str
    arguments: List[ExpressionAST]
    
    def __str__(self) -> str:
        args = ", ".join(str(arg) for arg in self.arguments)
        return f"Call({self.name}({args}))"


class FormulaParser:
    """Main parser class for mathematical formulas"""
    
    def __init__(self):
        self.tokens: List[Token] = []
        self.current_token_index = 0
        self.current_token: Optional[Token] = None
        
        # Operator precedence (higher number = higher precedence)
        self.operator_precedence = {
            '=': 1,   # Assignment (lowest precedence)
            '+': 2,   # Addition
            '-': 2,   # Subtraction
            '*': 3,   # Multiplication
            '/': 3,   # Division
            '%': 3,   # Modulo
            '**': 4,  # Exponentiation (highest precedence)
        }
        
        # Token patterns for lexical analysis
        self.token_patterns = [
            (r'\d+\.\d+', TokenType.NUMBER, float),        # Float
            (r'\d+', TokenType.NUMBER, int),               # Integer
            (r'[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*', TokenType.IDENTIFIER, str),  # Variables with dot notation
            (r'\*\*', TokenType.POWER, str),               # Exponentiation (must come before single *)
            (r'\+', TokenType.PLUS, str),                  # Addition
            (r'-', TokenType.MINUS, str),                  # Subtraction
            (r'\*', TokenType.MULTIPLY, str),              # Multiplication
            (r'/', TokenType.DIVIDE, str),                 # Division
            (r'%', TokenType.MODULO, str),                 # Modulo
            (r'=', TokenType.EQUALS, str),                 # Equals
            (r'\(', TokenType.LPAREN, str),                # Left parenthesis
            (r'\)', TokenType.RPAREN, str),                # Right parenthesis
            (r',', TokenType.COMMA, str),                  # Comma
            (r'\s+', None, None),                          # Whitespace (ignored)
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [
            (re.compile(pattern), token_type, converter) 
            for pattern, token_type, converter in self.token_patterns
        ]
    
    def tokenize(self, text: str) -> List[Token]:
        """
        Tokenize input text into a list of tokens
        
        Args:
            text: Mathematical expression to tokenize
            
        Returns:
            List of Token objects
            
        Raises:
            SyntaxError: If invalid characters are encountered
        """
        tokens = []
        position = 0
        line = 1
        column = 1
        
        while position < len(text):
            matched = False
            
            for pattern, token_type, converter in self.compiled_patterns:
                match = pattern.match(text, position)
                if match:
                    value = match.group(0)
                    
                    # Skip whitespace tokens
                    if token_type is not None:
                        converted_value = converter(value) if converter else value
                        token = Token(token_type, converted_value, position, line, column)
                        tokens.append(token)
                    
                    # Update position tracking
                    position = match.end()
                    if '\n' in value:
                        line += value.count('\n')
                        column = len(value) - value.rfind('\n')
                    else:
                        column += len(value)
                    
                    matched = True
                    break
            
            if not matched:
                char = text[position]
                raise SyntaxError(f"Invalid character '{char}'", position, line, column)
        
        return tokens
    
    def parse(self, text: str) -> ExpressionAST:
        """
        Parse text into an Abstract Syntax Tree
        
        Args:
            text: Mathematical expression to parse
            
        Returns:
            Root AST node
            
        Raises:
            SyntaxError: If expression is malformed
        """
        self.tokens = self.tokenize(text)
        # Add EOF token for parsing
        if self.tokens:
            last_token = self.tokens[-1]
            self.tokens.append(Token(TokenType.EOF, None, last_token.position + 1, last_token.line, last_token.column + 1))
        else:
            self.tokens.append(Token(TokenType.EOF, None, 0, 1, 1))
        
        self.current_token_index = 0
        self.current_token = self.tokens[0] if self.tokens else None
        
        ast = self._parse_expression()
        
        # Ensure we've consumed all tokens except EOF
        if self.current_token and self.current_token.type != TokenType.EOF:
            # Check for specific error cases
            if self.current_token.type == TokenType.NUMBER:
                raise SyntaxError(
                    "Missing operator between expressions",
                    self.current_token.position,
                    self.current_token.line,
                    self.current_token.column
                )
            else:
                raise SyntaxError(
                    f"Unexpected token {self.current_token.type.value}",
                    self.current_token.position,
                    self.current_token.line,
                    self.current_token.column
                )
        
        return ast
    
    def _advance_token(self):
        """Move to the next token"""
        if self.current_token_index < len(self.tokens) - 1:
            self.current_token_index += 1
            self.current_token = self.tokens[self.current_token_index]
        else:
            self.current_token = None
    
    def _parse_expression(self, min_precedence: int = 1) -> ExpressionAST:
        """
        Parse expression with operator precedence using Pratt parsing
        
        Args:
            min_precedence: Minimum operator precedence to consider
            
        Returns:
            AST node for the expression
        """
        # Parse left side (primary expression)
        left = self._parse_primary()
        
        # Handle binary operators with precedence
        while (self.current_token and 
               self.current_token.type != TokenType.EOF and
               self._get_operator_precedence(self.current_token) >= min_precedence):
            
            operator_token = self.current_token
            operator = operator_token.value
            precedence = self._get_operator_precedence(operator_token)
            
            self._advance_token()  # consume operator
            
            # Check for incomplete expressions (operator at end)
            if not self.current_token or self.current_token.type == TokenType.EOF:
                raise SyntaxError(
                    f"Expected expression after '{operator}'",
                    operator_token.position,
                    operator_token.line,
                    operator_token.column
                )
            
            # Right associative operators (like **) use precedence, 
            # left associative use precedence + 1
            next_min_precedence = precedence + (1 if operator != '**' else 0)
            right = self._parse_expression(next_min_precedence)
            
            left = BinaryOpAST(left, operator, right)
        
        return left
    
    def _parse_primary(self) -> ExpressionAST:
        """
        Parse primary expressions (numbers, variables, function calls, parenthesized expressions)
        
        Returns:
            AST node for primary expression
        """
        if not self.current_token:
            raise SyntaxError("Unexpected end of expression", 0, 1, 1)
        
        token = self.current_token
        
        # Handle unary operators
        if token.type in (TokenType.PLUS, TokenType.MINUS):
            operator = token.value
            self._advance_token()
            operand = self._parse_primary()
            return UnaryOpAST(operator, operand)
        
        # Handle invalid operators at start
        if token.type in (TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO, TokenType.POWER):
            raise SyntaxError(
                f"Unexpected operator '{token.value}' at start of expression",
                token.position,
                token.line,
                token.column
            )
        
        # Handle numbers
        if token.type == TokenType.NUMBER:
            self._advance_token()
            return NumberAST(token.value)
        
        # Handle identifiers (variables or function calls)
        if token.type == TokenType.IDENTIFIER:
            name = token.value
            self._advance_token()
            
            # Check for function call
            if self.current_token and self.current_token.type == TokenType.LPAREN:
                return self._parse_function_call(name)
            else:
                return VariableAST(name)
        
        # Handle parenthesized expressions
        if token.type == TokenType.LPAREN:
            self._advance_token()  # consume '('
            expr = self._parse_expression()
            
            if not self.current_token or self.current_token.type != TokenType.RPAREN:
                raise SyntaxError(
                    "Expected ')' after expression",
                    self.current_token.position if self.current_token else 0,
                    self.current_token.line if self.current_token else 1,
                    self.current_token.column if self.current_token else 1
                )
            
            self._advance_token()  # consume ')'
            return expr
        
        raise SyntaxError(
            f"Unexpected token {token.type.value}",
            token.position,
            token.line,
            token.column
        )
    
    def _parse_function_call(self, function_name: str) -> FunctionCallAST:
        """
        Parse function call with arguments
        
        Args:
            function_name: Name of the function being called
            
        Returns:
            FunctionCallAST node
        """
        if not self.current_token or self.current_token.type != TokenType.LPAREN:
            raise SyntaxError("Expected '(' for function call")
        
        self._advance_token()  # consume '('
        
        arguments = []
        
        # Handle empty parameter list
        if self.current_token and self.current_token.type == TokenType.RPAREN:
            self._advance_token()  # consume ')'
            return FunctionCallAST(function_name, arguments)
        
        # Parse arguments
        while True:
            arguments.append(self._parse_expression())
            
            if not self.current_token:
                raise SyntaxError("Expected ')' or ',' in function call")
            
            if self.current_token.type == TokenType.RPAREN:
                self._advance_token()  # consume ')'
                break
            elif self.current_token.type == TokenType.COMMA:
                self._advance_token()  # consume ','
                continue
            else:
                raise SyntaxError(
                    f"Expected ')' or ',' but got {self.current_token.type.value}",
                    self.current_token.position,
                    self.current_token.line,
                    self.current_token.column
                )
        
        return FunctionCallAST(function_name, arguments)
    
    def _get_operator_precedence(self, token: Token) -> int:
        """Get operator precedence, return 0 if not an operator"""
        if token.type in (TokenType.PLUS, TokenType.MINUS, TokenType.MULTIPLY, 
                         TokenType.DIVIDE, TokenType.MODULO, TokenType.POWER, TokenType.EQUALS):
            return self.operator_precedence.get(token.value, 0)
        return 0
    
    def extract_dependencies(self, expression: str) -> Set[str]:
        """
        Extract all variable dependencies from an expression
        
        Args:
            expression: Mathematical expression to analyze
            
        Returns:
            Set of variable names that the expression depends on
        """
        try:
            ast = self.parse(expression)
            dependencies = set()
            self._extract_dependencies_from_ast(ast, dependencies)
            return dependencies
        except Exception:
            # If parsing fails, return empty set
            return set()
    
    def _extract_dependencies_from_ast(self, node: ExpressionAST, dependencies: Set[str]):
        """Recursively extract dependencies from AST nodes"""
        if isinstance(node, VariableAST):
            dependencies.add(node.name)
        elif isinstance(node, BinaryOpAST):
            self._extract_dependencies_from_ast(node.left, dependencies)
            self._extract_dependencies_from_ast(node.right, dependencies)
        elif isinstance(node, UnaryOpAST):
            self._extract_dependencies_from_ast(node.operand, dependencies)
        elif isinstance(node, FunctionCallAST):
            for arg in node.arguments:
                self._extract_dependencies_from_ast(arg, dependencies)
        # NumberAST has no dependencies
    
    def validate_syntax(self, expression: str) -> List[FormulaError]:
        """
        Validate expression syntax and return list of errors
        
        Args:
            expression: Expression to validate
            
        Returns:
            List of FormulaError objects (empty if valid)
        """
        errors = []
        
        try:
            self.parse(expression)
        except FormulaError as e:
            errors.append(e)
        except Exception as e:
            errors.append(FormulaError(str(e)))
        
        return errors
    
    def evaluate(self, ast: ExpressionAST, context: Dict[str, Any]) -> Union[int, float, 'EMUValue']:
        """
        Evaluate an AST with variable context
        
        Args:
            ast: Root AST node to evaluate
            context: Dictionary mapping variable names to values
            
        Returns:
            Numeric result of evaluation (supports EMUValue for precise OOXML calculations)
            
        Raises:
            EvaluationError: If variables are undefined or operations fail
        """
        if isinstance(ast, NumberAST):
            return ast.value
        
        elif isinstance(ast, VariableAST):
            if ast.name not in context:
                raise EvaluationError(f"Undefined variable '{ast.name}'")
            return context[ast.name]
        
        elif isinstance(ast, BinaryOpAST):
            left_val = self.evaluate(ast.left, context)
            right_val = self.evaluate(ast.right, context)
            
            try:
                if ast.operator == '+':
                    return left_val + right_val
                elif ast.operator == '-':
                    return left_val - right_val
                elif ast.operator == '*':
                    return left_val * right_val
                elif ast.operator == '/':
                    if right_val == 0:
                        raise EvaluationError("Division by zero")
                    return left_val / right_val
                elif ast.operator == '%':
                    if right_val == 0:
                        raise EvaluationError("Modulo by zero")
                    return left_val % right_val
                elif ast.operator == '**':
                    return left_val ** right_val
                else:
                    raise EvaluationError(f"Unknown binary operator '{ast.operator}'")
            except (ZeroDivisionError, OverflowError) as e:
                raise EvaluationError(str(e))
        
        elif isinstance(ast, UnaryOpAST):
            operand_val = self.evaluate(ast.operand, context)
            
            if ast.operator == '+':
                return operand_val
            elif ast.operator == '-':
                return -operand_val
            else:
                raise EvaluationError(f"Unknown unary operator '{ast.operator}'")
        
        elif isinstance(ast, FunctionCallAST):
            # Function calls will be handled by built-in functions in later tasks
            raise EvaluationError(f"Function '{ast.name}' not implemented")
        
        else:
            raise EvaluationError(f"Unknown AST node type {type(ast)}")


if __name__ == '__main__':
    # Simple test of the parser
    parser = FormulaParser()
    
    test_expressions = [
        "42",
        "SLIDE_W",
        "1 + 2 * 3",
        "(1 + 2) * 3",
        "SAFE_L + (col - 1) * (COL_W + GUT)",
        "x(2)",
        "rect(1, 2, 3, 4)"
    ]
    
    print("Formula Parser Test")
    print("==================")
    
    for expr in test_expressions:
        try:
            print(f"\nExpression: {expr}")
            
            # Tokenize
            tokens = parser.tokenize(expr)
            print(f"Tokens: {[str(t) for t in tokens[:-1]]}")  # Exclude EOF
            
            # Parse
            ast = parser.parse(expr)
            print(f"AST: {ast}")
            
            # Dependencies
            deps = parser.extract_dependencies(expr)
            print(f"Dependencies: {deps}")
            
        except Exception as e:
            print(f"Error: {e}")