"""
Validation Engine for Variable Substitution

This module provides comprehensive validation for variable substitution
operations with various checkpoint types and validation strategies.
"""


from typing import Any, Dict, List
import re
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    import lxml.etree as lxml_ET
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False

from .types import ValidationCheckpoint, ValidationCheckpointType


class ValidationEngine:
    """
    Comprehensive validation engine for variable substitution operations.
    
    Provides validation at multiple checkpoints throughout the substitution
    pipeline to ensure data integrity and operation success.
    """
    
    def __init__(self):
        self.xpath_cache = {}
        self.validation_stats = {
            'validations_performed': 0,
            'validations_passed': 0,
            'validations_failed': 0
        }
        
        # Common validation patterns
        self.xpath_patterns = {
            'valid_xpath': re.compile(r'^[/\w\[\]@\.:=\-\s\'"()]+$'),
            'valid_variable_name': re.compile(r'^[a-zA-Z][a-zA-Z0-9_]*$'),
            'valid_hex_color': re.compile(r'^#?[0-9A-Fa-f]{6}$'),
            'valid_font_name': re.compile(r'^[a-zA-Z0-9\s\-]+$')
        }
        
        # OOXML namespace prefixes for validation
        self.ooxml_namespaces = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
            'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
            'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
            'xl': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
        }
    
    def validate_pre_substitution(self, document_content: str, variables: Dict[str, Any]) -> ValidationCheckpoint:
        """Validate conditions before starting substitution."""
        self.validation_stats['validations_performed'] += 1
        
        issues = []
        
        # Check if document content is valid XML
        try:
            ET.fromstring(document_content)
        except ET.ParseError as e:
            issues.append(f"Invalid XML document: {str(e)}")
        
        # Check if variables dictionary is valid
        if not isinstance(variables, dict):
            issues.append("Variables must be provided as a dictionary")
        elif len(variables) == 0:
            issues.append("No variables provided for substitution")
        
        # Check document size (basic sanity check)
        if len(document_content) > 50 * 1024 * 1024:  # 50MB
            issues.append("Document content is extremely large (>50MB)")
        elif len(document_content) < 100:  # Too small
            issues.append("Document content is suspiciously small (<100 chars)")
        
        # Check for obvious corruption patterns
        if '<<<<<<<' in document_content or '>>>>>>>' in document_content:
            issues.append("Document contains merge conflict markers")
        
        success = len(issues) == 0
        
        if success:
            self.validation_stats['validations_passed'] += 1
        else:
            self.validation_stats['validations_failed'] += 1
        
        return ValidationCheckpoint(
            checkpoint_type=ValidationCheckpointType.PRE_SUBSTITUTION,
            passed=success,
            message="Pre-substitution validation passed" if success else f"Pre-substitution validation failed: {'; '.join(issues)}",
            details={'issues': issues} if issues else None
        )
    
    def validate_variables(self, variables: Dict[str, Any]) -> ValidationCheckpoint:
        """Validate variable definitions and structure."""
        self.validation_stats['validations_performed'] += 1
        
        issues = []
        
        for var_name, var_data in variables.items():
            # Validate variable name
            if not self.xpath_patterns['valid_variable_name'].match(var_name):
                issues.append(f"Invalid variable name '{var_name}': must start with letter and contain only letters, numbers, underscore")
            
            # Validate variable data structure
            if isinstance(var_data, dict):
                # Check required fields
                if 'xpath' not in var_data:
                    issues.append(f"Variable '{var_name}' missing required 'xpath' field")
                
                if 'value' not in var_data:
                    issues.append(f"Variable '{var_name}' missing required 'value' field")
                
                # Validate specific field types
                if 'type' in var_data:
                    valid_types = ['text', 'color', 'font', 'number', 'dimension', 'boolean']
                    if var_data['type'] not in valid_types:
                        issues.append(f"Variable '{var_name}' has invalid type '{var_data['type']}'. Valid types: {valid_types}")
                
                # Type-specific validations
                if var_data.get('type') == 'color':
                    color_value = str(var_data.get('value', ''))
                    if not self.xpath_patterns['valid_hex_color'].match(color_value):
                        issues.append(f"Variable '{var_name}' has invalid color value '{color_value}'")
                
                elif var_data.get('type') == 'font':
                    font_value = str(var_data.get('value', ''))
                    if not self.xpath_patterns['valid_font_name'].match(font_value):
                        issues.append(f"Variable '{var_name}' has invalid font name '{font_value}'")
                
                elif var_data.get('type') == 'number':
                    try:
                        float(var_data.get('value', ''))
                    except (ValueError, TypeError):
                        issues.append(f"Variable '{var_name}' has non-numeric value for number type")
            
            elif not isinstance(var_data, (str, int, float, bool)):
                issues.append(f"Variable '{var_name}' has unsupported data type: {type(var_data)}")
        
        success = len(issues) == 0
        
        if success:
            self.validation_stats['validations_passed'] += 1
        else:
            self.validation_stats['validations_failed'] += 1
        
        return ValidationCheckpoint(
            checkpoint_type=ValidationCheckpointType.VARIABLE_VALIDATION,
            passed=success,
            message="Variable validation passed" if success else f"Variable validation failed: {'; '.join(issues)}",
            details={'issues': issues} if issues else None
        )
    
    def validate_xpath_expressions(self, variables: Dict[str, Any]) -> ValidationCheckpoint:
        """Validate XPath expressions in variables."""
        self.validation_stats['validations_performed'] += 1
        
        issues = []
        
        for var_name, var_data in variables.items():
            if isinstance(var_data, dict) and 'xpath' in var_data:
                xpath_expr = var_data['xpath']
                
                # Basic XPath syntax validation
                if not self.xpath_patterns['valid_xpath'].match(xpath_expr):
                    issues.append(f"Variable '{var_name}' has invalid XPath syntax: {xpath_expr}")
                    continue
                
                # Check for common XPath issues
                if xpath_expr.startswith('//') and xpath_expr.count('/') < 2:
                    issues.append(f"Variable '{var_name}' has potentially inefficient XPath (starts with //): {xpath_expr}")
                
                # Check for balanced brackets
                if xpath_expr.count('[') != xpath_expr.count(']'):
                    issues.append(f"Variable '{var_name}' has unbalanced brackets in XPath: {xpath_expr}")
                
                # Check for balanced parentheses
                if xpath_expr.count('(') != xpath_expr.count(')'):
                    issues.append(f"Variable '{var_name}' has unbalanced parentheses in XPath: {xpath_expr}")
                
                # Check for balanced quotes
                single_quotes = xpath_expr.count("'")
                double_quotes = xpath_expr.count('"')
                if single_quotes % 2 != 0:
                    issues.append(f"Variable '{var_name}' has unbalanced single quotes in XPath: {xpath_expr}")
                if double_quotes % 2 != 0:
                    issues.append(f"Variable '{var_name}' has unbalanced double quotes in XPath: {xpath_expr}")
                
                # Validate namespace prefixes
                self._validate_xpath_namespaces(var_name, xpath_expr, issues)
                
                # Try to compile XPath if lxml is available
                if LXML_AVAILABLE:
                    try:
                        lxml_ET.XPath(xpath_expr, namespaces=self.ooxml_namespaces)
                    except lxml_ET.XPathSyntaxError as e:
                        issues.append(f"Variable '{var_name}' has XPath syntax error: {str(e)}")
                    except Exception as e:
                        issues.append(f"Variable '{var_name}' has XPath compilation error: {str(e)}")
        
        success = len(issues) == 0
        
        if success:
            self.validation_stats['validations_passed'] += 1
        else:
            self.validation_stats['validations_failed'] += 1
        
        return ValidationCheckpoint(
            checkpoint_type=ValidationCheckpointType.XPATH_VALIDATION,
            passed=success,
            message="XPath validation passed" if success else f"XPath validation failed: {'; '.join(issues)}",
            details={'issues': issues} if issues else None
        )
    
    def validate_dependency_resolution(self, resolved_variables: List[Dict[str, Any]]) -> ValidationCheckpoint:
        """Validate that variable dependencies are properly resolved."""
        self.validation_stats['validations_performed'] += 1
        
        issues = []
        
        # Check for circular dependencies
        dependency_graph = {}
        for var in resolved_variables:
            var_name = var.get('name', 'unknown')
            dependencies = var.get('dependencies', [])
            dependency_graph[var_name] = dependencies
        
        # Simple circular dependency detection
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            if node in rec_stack:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in dependency_graph.get(node, []):
                if has_cycle(neighbor):
                    return True
            
            rec_stack.remove(node)
            return False
        
        for var_name in dependency_graph:
            if var_name not in visited:
                if has_cycle(var_name):
                    issues.append(f"Circular dependency detected involving variable '{var_name}'")
        
        # Check for unresolved dependencies
        resolved_names = set(var.get('name') for var in resolved_variables)
        for var in resolved_variables:
            var_name = var.get('name', 'unknown')
            dependencies = var.get('dependencies', [])
            for dep in dependencies:
                if dep not in resolved_names:
                    issues.append(f"Variable '{var_name}' has unresolved dependency '{dep}'")
        
        success = len(issues) == 0
        
        if success:
            self.validation_stats['validations_passed'] += 1
        else:
            self.validation_stats['validations_failed'] += 1
        
        return ValidationCheckpoint(
            checkpoint_type=ValidationCheckpointType.DEPENDENCY_RESOLUTION,
            passed=success,
            message="Dependency resolution validation passed" if success else f"Dependency resolution validation failed: {'; '.join(issues)}",
            details={'issues': issues} if issues else None
        )
    
    def validate_post_substitution(self, document_content: str, applied_variables: List[Dict[str, Any]]) -> ValidationCheckpoint:
        """Validate document after variable substitution."""
        self.validation_stats['validations_performed'] += 1
        
        issues = []
        warnings = []
        
        # Check if document is still valid XML
        try:
            root = ET.fromstring(document_content)
        except ET.ParseError as e:
            issues.append(f"Document is no longer valid XML after substitution: {str(e)}")
            # If XML is invalid, we can't perform further validations
            success = False
            self.validation_stats['validations_failed'] += 1
            
            return ValidationCheckpoint(
                checkpoint_type=ValidationCheckpointType.POST_SUBSTITUTION,
                passed=success,
                message=f"Post-substitution validation failed: {'; '.join(issues)}",
                details={'issues': issues, 'warnings': warnings}
            )
        
        # Check document structure integrity
        self._validate_document_structure(document_content, issues, warnings)
        
        # Check for successful variable application
        applied_count = len([v for v in applied_variables if v.get('applied', False)])
        total_count = len(applied_variables)
        
        if applied_count < total_count:
            warnings.append(f"Only {applied_count} of {total_count} variables were successfully applied")
        
        # Check for leftover variable placeholders
        leftover_placeholders = re.findall(r'\{\{[^}]+\}\}', document_content)
        if leftover_placeholders:
            warnings.append(f"Found {len(leftover_placeholders)} unresolved variable placeholders")
        
        # Check document size changes (basic sanity check)
        if len(document_content) < 50:  # Too small after substitution
            warnings.append("Document became very small after substitution - possible data loss")
        
        success = len(issues) == 0
        
        if success:
            self.validation_stats['validations_passed'] += 1
        else:
            self.validation_stats['validations_failed'] += 1
        
        return ValidationCheckpoint(
            checkpoint_type=ValidationCheckpointType.POST_SUBSTITUTION,
            passed=success,
            message="Post-substitution validation passed" if success else f"Post-substitution validation failed: {'; '.join(issues)}",
            details={'issues': issues, 'warnings': warnings}
        )
    
    def _validate_xpath_namespaces(self, var_name: str, xpath_expr: str, issues: List[str]):
        """Validate namespace prefixes in XPath expressions."""
        # Find namespace prefixes in XPath
        prefixes = re.findall(r'([a-zA-Z]+):', xpath_expr)
        
        for prefix in set(prefixes):  # Remove duplicates
            if prefix not in self.ooxml_namespaces:
                issues.append(f"Variable '{var_name}' uses unknown namespace prefix '{prefix}' in XPath")
    
    def _validate_document_structure(self, document_content: str, issues: List[str], warnings: List[str]):
        """Validate basic document structure integrity."""
        try:
            root = ET.fromstring(document_content)
            
            # Check for empty document
            if len(list(root.iter())) < 2:  # Root + at least one child
                warnings.append("Document has very few elements - possible structure loss")
            
            # Check for namespace preservation
            if not root.tag.startswith('{'):
                warnings.append("Root element appears to have lost namespace information")
            
            # Check for common OOXML root elements
            root_tag = root.tag.split('}')[-1] if '}' in root.tag else root.tag
            common_roots = ['document', 'presentation', 'workbook', 'slide', 'worksheet']
            
            if not any(root_name in root_tag.lower() for root_name in common_roots):
                warnings.append(f"Unexpected root element '{root_tag}' - may not be valid OOXML")
            
        except Exception as e:
            issues.append(f"Failed to validate document structure: {str(e)}")
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation engine statistics."""
        stats = dict(self.validation_stats)
        
        if stats['validations_performed'] > 0:
            stats['success_rate'] = stats['validations_passed'] / stats['validations_performed']
        else:
            stats['success_rate'] = 0.0
        
        return stats
    
    def reset_statistics(self):
        """Reset validation statistics."""
        self.validation_stats = {
            'validations_performed': 0,
            'validations_passed': 0,
            'validations_failed': 0
        }