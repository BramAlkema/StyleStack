#!/usr/bin/env python3
"""
Test suite for Formula Parser Engine
Tests tokenization, AST generation, dependency extraction, and validation
"""

import unittest
from typing import Dict, List, Set, Any
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from tools.formula_parser import (
        FormulaParser, 
        Token, TokenType, 
        ExpressionAST, BinaryOpAST, UnaryOpAST, VariableAST, FunctionCallAST, NumberAST,
        FormulaError, SyntaxError as FormulaSyntaxError
    )
except ImportError:
    # Module doesn't exist yet - that's expected for TDD
    pass


class TestTokenizer(unittest.TestCase):
    """Test tokenization of mathematical expressions"""
    
    def setUp(self):
        self.parser = FormulaParser()
    
    def test_basic_numbers(self):
        """Test tokenization of numeric literals"""
        tokens = self.parser.tokenize("123")
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].type, TokenType.NUMBER)
        self.assertEqual(tokens[0].value, 123)
        
        tokens = self.parser.tokenize("45.67")
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].type, TokenType.NUMBER)
        self.assertEqual(tokens[0].value, 45.67)
    
    def test_basic_operators(self):
        """Test tokenization of arithmetic operators"""
        test_cases = [
            ("+", TokenType.PLUS),
            ("-", TokenType.MINUS),
            ("*", TokenType.MULTIPLY),
            ("/", TokenType.DIVIDE),
            ("%", TokenType.MODULO),
            ("**", TokenType.POWER),
            ("=", TokenType.EQUALS)
        ]
        
        for operator, expected_type in test_cases:
            with self.subTest(operator=operator):
                tokens = self.parser.tokenize(operator)
                self.assertEqual(len(tokens), 1)
                self.assertEqual(tokens[0].type, expected_type)
    
    def test_parentheses(self):
        """Test tokenization of parentheses"""
        tokens = self.parser.tokenize("()")
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[0].type, TokenType.LPAREN)
        self.assertEqual(tokens[1].type, TokenType.RPAREN)
    
    def test_variables(self):
        """Test tokenization of variable names"""
        test_cases = [
            "SLIDE_W",
            "safe.inset_pct",
            "grid.cols",
            "x",
            "_private_var"
        ]
        
        for var_name in test_cases:
            with self.subTest(variable=var_name):
                tokens = self.parser.tokenize(var_name)
                self.assertEqual(len(tokens), 1)
                self.assertEqual(tokens[0].type, TokenType.IDENTIFIER)
                self.assertEqual(tokens[0].value, var_name)
    
    def test_function_calls(self):
        """Test tokenization of function calls"""
        tokens = self.parser.tokenize("x(2)")
        expected_types = [TokenType.IDENTIFIER, TokenType.LPAREN, TokenType.NUMBER, TokenType.RPAREN]
        self.assertEqual(len(tokens), 4)
        for i, expected_type in enumerate(expected_types):
            self.assertEqual(tokens[i].type, expected_type)
    
    def test_complex_expression(self):
        """Test tokenization of complex mathematical expression"""
        expression = "SAFE_L + (col - 1) * (COL_W + GUT)"
        tokens = self.parser.tokenize(expression)
        
        # Should tokenize correctly without throwing errors
        self.assertGreater(len(tokens), 0)
        
        # Check for presence of key tokens
        token_types = [t.type for t in tokens]
        self.assertIn(TokenType.IDENTIFIER, token_types)
        self.assertIn(TokenType.PLUS, token_types)
        self.assertIn(TokenType.LPAREN, token_types)
        self.assertIn(TokenType.MULTIPLY, token_types)
    
    def test_whitespace_handling(self):
        """Test that whitespace is properly ignored"""
        expressions = [
            "1+2",
            "1 + 2",
            "  1   +   2  ",
            "\t1\n+\r2\t"
        ]
        
        for expr in expressions:
            with self.subTest(expression=expr):
                tokens = self.parser.tokenize(expr)
                self.assertEqual(len(tokens), 3)
                self.assertEqual(tokens[0].type, TokenType.NUMBER)
                self.assertEqual(tokens[1].type, TokenType.PLUS)
                self.assertEqual(tokens[2].type, TokenType.NUMBER)


class TestASTParsing(unittest.TestCase):
    """Test Abstract Syntax Tree generation from tokens"""
    
    def setUp(self):
        self.parser = FormulaParser()
    
    def test_simple_number(self):
        """Test parsing single number"""
        ast = self.parser.parse("42")
        self.assertIsInstance(ast, NumberAST)
        self.assertEqual(ast.value, 42)
    
    def test_simple_variable(self):
        """Test parsing single variable"""
        ast = self.parser.parse("SLIDE_W")
        self.assertIsInstance(ast, VariableAST)
        self.assertEqual(ast.name, "SLIDE_W")
    
    def test_binary_operations(self):
        """Test parsing binary operations with correct precedence"""
        # Addition
        ast = self.parser.parse("1 + 2")
        self.assertIsInstance(ast, BinaryOpAST)
        self.assertEqual(ast.operator, "+")
        self.assertIsInstance(ast.left, NumberAST)
        self.assertIsInstance(ast.right, NumberAST)
        
        # Multiplication has higher precedence than addition
        ast = self.parser.parse("1 + 2 * 3")
        self.assertIsInstance(ast, BinaryOpAST)
        self.assertEqual(ast.operator, "+")
        self.assertIsInstance(ast.left, NumberAST)
        self.assertIsInstance(ast.right, BinaryOpAST)
        self.assertEqual(ast.right.operator, "*")
    
    def test_parentheses_precedence(self):
        """Test that parentheses override operator precedence"""
        ast = self.parser.parse("(1 + 2) * 3")
        self.assertIsInstance(ast, BinaryOpAST)
        self.assertEqual(ast.operator, "*")
        self.assertIsInstance(ast.left, BinaryOpAST)
        self.assertEqual(ast.left.operator, "+")
        self.assertIsInstance(ast.right, NumberAST)
    
    def test_unary_operations(self):
        """Test parsing unary operations"""
        ast = self.parser.parse("-42")
        self.assertIsInstance(ast, UnaryOpAST)
        self.assertEqual(ast.operator, "-")
        self.assertIsInstance(ast.operand, NumberAST)
    
    def test_function_calls(self):
        """Test parsing function calls with parameters"""
        # Single parameter
        ast = self.parser.parse("x(2)")
        self.assertIsInstance(ast, FunctionCallAST)
        self.assertEqual(ast.name, "x")
        self.assertEqual(len(ast.arguments), 1)
        self.assertIsInstance(ast.arguments[0], NumberAST)
        
        # Multiple parameters
        ast = self.parser.parse("rect(1, 2, 3, 4)")
        self.assertIsInstance(ast, FunctionCallAST)
        self.assertEqual(ast.name, "rect")
        self.assertEqual(len(ast.arguments), 4)
    
    def test_nested_expressions(self):
        """Test parsing nested expressions"""
        ast = self.parser.parse("SAFE_L + (col - 1) * (COL_W + GUT)")
        self.assertIsInstance(ast, BinaryOpAST)
        self.assertEqual(ast.operator, "+")
        
        # Left side should be a variable
        self.assertIsInstance(ast.left, VariableAST)
        
        # Right side should be a multiplication
        self.assertIsInstance(ast.right, BinaryOpAST)
        self.assertEqual(ast.right.operator, "*")


class TestDependencyExtraction(unittest.TestCase):
    """Test extraction of variable dependencies from expressions"""
    
    def setUp(self):
        self.parser = FormulaParser()
    
    def test_simple_variable_dependency(self):
        """Test extracting single variable dependency"""
        deps = self.parser.extract_dependencies("SLIDE_W")
        self.assertEqual(deps, {"SLIDE_W"})
    
    def test_multiple_variable_dependencies(self):
        """Test extracting multiple variable dependencies"""
        deps = self.parser.extract_dependencies("SLIDE_W + SLIDE_H")
        self.assertEqual(deps, {"SLIDE_W", "SLIDE_H"})
    
    def test_nested_dependencies(self):
        """Test extracting dependencies from nested expressions"""
        deps = self.parser.extract_dependencies("SAFE_L + (col - 1) * (COL_W + GUT)")
        expected = {"SAFE_L", "col", "COL_W", "GUT"}
        self.assertEqual(deps, expected)
    
    def test_function_parameter_dependencies(self):
        """Test extracting dependencies from function parameters"""
        deps = self.parser.extract_dependencies("x(col + 1)")
        self.assertEqual(deps, {"col"})
        
        deps = self.parser.extract_dependencies("rect(SAFE_L, SAFE_T, width, height)")
        expected = {"SAFE_L", "SAFE_T", "width", "height"}
        self.assertEqual(deps, expected)
    
    def test_no_dependencies(self):
        """Test expressions with no variable dependencies"""
        deps = self.parser.extract_dependencies("42")
        self.assertEqual(deps, set())
        
        deps = self.parser.extract_dependencies("1 + 2 * 3")
        self.assertEqual(deps, set())
    
    def test_duplicate_dependencies(self):
        """Test that duplicate dependencies are handled correctly"""
        deps = self.parser.extract_dependencies("x + x * x")
        self.assertEqual(deps, {"x"})


class TestSyntaxValidation(unittest.TestCase):
    """Test syntax validation and error reporting"""
    
    def setUp(self):
        self.parser = FormulaParser()
    
    def test_valid_expressions(self):
        """Test that valid expressions pass validation"""
        valid_expressions = [
            "42",
            "SLIDE_W",
            "1 + 2",
            "x(2)",
            "SAFE_L + (col - 1) * (COL_W + GUT)",
            "(1 + 2) * 3 / 4 - 5"
        ]
        
        for expr in valid_expressions:
            with self.subTest(expression=expr):
                errors = self.parser.validate_syntax(expr)
                self.assertEqual(len(errors), 0)
    
    def test_invalid_expressions(self):
        """Test that invalid expressions are caught"""
        invalid_expressions = [
            "1 +",           # Incomplete operation
            "1 2",           # Missing operator
            ")",             # Unmatched parenthesis
            "(",             # Unmatched parenthesis
            "x(",            # Incomplete function call
            "* 5"            # Invalid operator at start
        ]
        
        for expr in invalid_expressions:
            with self.subTest(expression=expr):
                errors = self.parser.validate_syntax(expr)
                self.assertGreater(len(errors), 0)
    
    def test_error_messages(self):
        """Test that error messages are descriptive"""
        errors = self.parser.validate_syntax("1 +")
        self.assertGreater(len(errors), 0)
        self.assertIn("expected", errors[0].message.lower())
    
    def test_error_positions(self):
        """Test that error positions are accurate"""
        errors = self.parser.validate_syntax("1 +")
        self.assertGreater(len(errors), 0)
        # Error should be around position of +
        self.assertGreater(errors[0].position, 1)


class TestFormulaEvaluation(unittest.TestCase):
    """Test evaluation of parsed expressions with variable context"""
    
    def setUp(self):
        self.parser = FormulaParser()
        self.context = {
            "SLIDE_W": 12192000,
            "SLIDE_H": 6858000,
            "SAFE_L": 1219200,
            "COL_W": 673100,
            "GUT": 152400,
            "col": 2
        }
    
    def test_number_evaluation(self):
        """Test evaluation of numeric literals"""
        ast = self.parser.parse("42")
        result = self.parser.evaluate(ast, self.context)
        self.assertEqual(result, 42)
    
    def test_variable_evaluation(self):
        """Test evaluation of variables from context"""
        ast = self.parser.parse("SLIDE_W")
        result = self.parser.evaluate(ast, self.context)
        self.assertEqual(result, 12192000)
    
    def test_arithmetic_evaluation(self):
        """Test evaluation of arithmetic operations"""
        test_cases = [
            ("1 + 2", 3),
            ("10 - 3", 7),
            ("4 * 5", 20),
            ("15 / 3", 5),
            ("17 % 5", 2),
            ("2 ** 3", 8)
        ]
        
        for expr, expected in test_cases:
            with self.subTest(expression=expr):
                ast = self.parser.parse(expr)
                result = self.parser.evaluate(ast, self.context)
                self.assertEqual(result, expected)
    
    def test_variable_arithmetic(self):
        """Test evaluation with variables and arithmetic"""
        ast = self.parser.parse("SLIDE_W + SLIDE_H")
        result = self.parser.evaluate(ast, self.context)
        self.assertEqual(result, 12192000 + 6858000)
    
    def test_complex_expression_evaluation(self):
        """Test evaluation of complex nested expressions"""
        # This mimics the grid column position formula: SAFE_L + (col-1) * (COL_W + GUT)
        ast = self.parser.parse("SAFE_L + (col - 1) * (COL_W + GUT)")
        result = self.parser.evaluate(ast, self.context)
        
        # Manual calculation: 1219200 + (2-1) * (673100 + 152400) = 1219200 + 825500 = 2044700
        expected = 1219200 + (2 - 1) * (673100 + 152400)
        self.assertEqual(result, expected)
    
    def test_undefined_variable_error(self):
        """Test that undefined variables raise appropriate errors"""
        ast = self.parser.parse("UNDEFINED_VAR")
        with self.assertRaises(FormulaError):
            self.parser.evaluate(ast, self.context)
    
    def test_division_by_zero_error(self):
        """Test that division by zero is handled"""
        ast = self.parser.parse("1 / 0")
        with self.assertRaises(FormulaError):
            self.parser.evaluate(ast, self.context)


class TestErrorHandling(unittest.TestCase):
    """Test comprehensive error handling throughout the parser"""
    
    def setUp(self):
        self.parser = FormulaParser()
    
    def test_tokenizer_error_handling(self):
        """Test that tokenizer handles invalid characters gracefully"""
        # Test with various invalid characters
        invalid_inputs = ["@", "#", "$", "~", "`"]
        
        for invalid_char in invalid_inputs:
            with self.subTest(char=invalid_char):
                with self.assertRaises(FormulaSyntaxError):
                    self.parser.tokenize(invalid_char)
    
    def test_parser_error_recovery(self):
        """Test parser error recovery and reporting"""
        # Parser should provide meaningful errors for malformed expressions
        malformed_expressions = [
            "(((",
            ")))",
            "1 2 3",
            "* 5"
        ]
        
        for expr in malformed_expressions:
            with self.subTest(expression=expr):
                with self.assertRaises(FormulaSyntaxError):
                    self.parser.parse(expr)
    
    def test_evaluation_error_context(self):
        """Test that evaluation errors include context information"""
        context = {"x": 10}
        ast = self.parser.parse("y + 5")  # y is undefined
        
        try:
            self.parser.evaluate(ast, context)
            self.fail("Expected FormulaError")
        except FormulaError as e:
            self.assertIn("y", str(e))
            self.assertIn("undefined", str(e).lower())


if __name__ == '__main__':
    # Run the test suite
    unittest.main(verbosity=2)