#!/usr/bin/env python3
"""
OOXML Extension Schema Validator

Validates variable definitions against the StyleStack extension variable schema.
Provides detailed error reporting and validation utilities.
"""


from typing import Any, Dict, List, Optional
import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import jsonschema
from jsonschema import validate, ValidationError, Draft7Validator
from lxml import etree as ET


class VariableType(Enum):
    COLOR = "color"
    FONT = "font"
    DIMENSION = "dimension"
    POSITION = "position"
    TEXT = "text"
    BOOLEAN = "boolean"
    NUMBER = "number"


class VariableScope(Enum):
    THEME = "theme"
    SLIDE = "slide"
    SHAPE = "shape"
    PARAGRAPH = "paragraph"
    RUN = "run"
    DOCUMENT = "document"
    WORKBOOK = "workbook"
    WORKSHEET = "worksheet"


class OOXMLValueType(Enum):
    DIRECT = "direct"
    SCHEME_COLOR = "schemeClr"
    THEME_FONT = "themeFont"
    EMU = "emu"
    CALCULATED = "calculated"
    PERCENTAGE = "percentage"
    BOOLEAN = "boolean"


@dataclass
class ValidationError:
    """Detailed validation error information"""
    field: str
    message: str
    value: Any = None
    severity: str = "error"  # "error", "warning", "info"
    code: str = ""
    suggestion: str = ""


@dataclass
class ValidationResult:
    """Complete validation result"""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    variable_id: Optional[str] = None
    
    def add_error(self, field: str, message: str, value: Any = None, code: str = "", suggestion: str = ""):
        """Add validation error"""
        self.errors.append(ValidationError(
            field=field, message=message, value=value, 
            severity="error", code=code, suggestion=suggestion
        ))
        self.is_valid = False
        
    def add_warning(self, field: str, message: str, value: Any = None, code: str = "", suggestion: str = ""):
        """Add validation warning"""
        self.warnings.append(ValidationError(
            field=field, message=message, value=value,
            severity="warning", code=code, suggestion=suggestion
        ))


class ExtensionSchemaValidator:
    """Main validator for OOXML extension variables"""
    
    def __init__(self, schema_path: Optional[Path] = None):
        """Initialize validator with schema"""
        self.schema_path = schema_path or self._get_default_schema_path()
        self.schema = self._load_schema()
        self.validator = Draft7Validator(self.schema)
        
        # OOXML namespace mappings
        self.ooxml_namespaces = {
            "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
            "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
            "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
            "s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
        }
        
    def _get_default_schema_path(self) -> Path:
        """Get default schema file path"""
        return Path(__file__).parent.parent / "schemas" / "extension-variable.schema.json"
        
    def _load_schema(self) -> Dict[str, Any]:
        """Load JSON schema from file"""
        try:
            with open(self.schema_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise ValueError(f"Schema file not found: {self.schema_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON schema: {e}")
    
    def validate_variable(self, variable: Dict[str, Any]) -> ValidationResult:
        """Validate a single variable definition"""
        result = ValidationResult()
        
        # Set variable ID for context
        result.variable_id = variable.get("id", "<unknown>")
        
        try:
            # Basic schema validation
            self.validator.validate(variable)
            
            # Additional custom validations
            self._validate_variable_id(variable, result)
            self._validate_xpath_syntax(variable, result)
            self._validate_ooxml_integration(variable, result)
            self._validate_type_specific_rules(variable, result)
            self._validate_dependencies(variable, result)
            
            # Set final validation state
            result.is_valid = len(result.errors) == 0
            
        except ValidationError as e:
            result.add_error(
                field=".".join(str(x) for x in e.absolute_path),
                message=e.message,
                value=e.instance,
                code="SCHEMA_VALIDATION_ERROR"
            )
            
        return result
    
    def validate_variable_collection(self, variables: List[Dict[str, Any]]) -> List[ValidationResult]:
        """Validate a collection of variables"""
        results = []
        variable_ids = set()
        
        for i, variable in enumerate(variables):
            result = self.validate_variable(variable)
            
            # Check for duplicate IDs
            var_id = variable.get("id")
            if var_id:
                if var_id in variable_ids:
                    result.add_error(
                        field="id",
                        message=f"Duplicate variable ID: {var_id}",
                        value=var_id,
                        code="DUPLICATE_ID"
                    )
                else:
                    variable_ids.add(var_id)
            
            results.append(result)
        
        # Cross-validate dependencies
        self._validate_cross_dependencies(variables, results)
        
        return results
    
    def _validate_variable_id(self, variable: Dict[str, Any], result: ValidationResult):
        """Validate variable ID format and conventions"""
        var_id = variable.get("id")
        if not var_id:
            return
            
        # Pattern validation (already covered by schema, but with better error messages)
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9._]*$", var_id):
            result.add_error(
                field="id",
                message="Variable ID must start with a letter and contain only letters, numbers, dots, and underscores",
                value=var_id,
                code="INVALID_ID_FORMAT",
                suggestion="Use format like 'accent_primary' or 'heading.font'"
            )
        
        # Length validation
        if len(var_id) > 64:
            result.add_error(
                field="id",
                message="Variable ID too long (max 64 characters)",
                value=var_id,
                code="ID_TOO_LONG"
            )
        
        # Convention warnings
        if var_id.startswith("_"):
            result.add_warning(
                field="id", 
                message="Variable ID starting with underscore is discouraged",
                value=var_id,
                code="ID_CONVENTION_WARNING",
                suggestion="Use descriptive names without leading underscores"
            )
        
        if not re.search(r"[a-z]", var_id):
            result.add_warning(
                field="id",
                message="Variable ID with all uppercase letters is discouraged", 
                value=var_id,
                code="ID_CASE_WARNING",
                suggestion="Use snake_case or camelCase convention"
            )
    
    def _validate_xpath_syntax(self, variable: Dict[str, Any], result: ValidationResult):
        """Validate XPath expression syntax"""
        xpath = variable.get("xpath")
        if not xpath:
            return
            
        try:
            # Test XPath syntax by compiling it
            ET.XPath(xpath, namespaces=self.ooxml_namespaces)
        except ET.XPathSyntaxError as e:
            result.add_error(
                field="xpath",
                message=f"Invalid XPath syntax: {e}",
                value=xpath,
                code="INVALID_XPATH_SYNTAX",
                suggestion="Check XPath syntax and namespace prefixes"
            )
        except ET.XPathEvalError as e:
            result.add_error(
                field="xpath", 
                message=f"XPath evaluation error: {e}",
                value=xpath,
                code="XPATH_EVALUATION_ERROR"
            )
        
        # Warn about potentially inefficient XPath patterns
        if xpath.startswith("//") and "//" in xpath[2:]:
            result.add_warning(
                field="xpath",
                message="XPath with multiple '//' operators may be inefficient",
                value=xpath,
                code="XPATH_PERFORMANCE_WARNING",
                suggestion="Consider more specific path expressions"
            )
    
    def _validate_ooxml_integration(self, variable: Dict[str, Any], result: ValidationResult):
        """Validate OOXML integration details"""
        ooxml = variable.get("ooxml", {})
        var_type = variable.get("type")
        
        # Validate namespace URI
        namespace = ooxml.get("namespace")
        if namespace and namespace not in self.ooxml_namespaces.values():
            result.add_warning(
                field="ooxml.namespace",
                message="Namespace not in standard OOXML namespaces",
                value=namespace,
                code="UNKNOWN_NAMESPACE",
                suggestion="Verify this is a valid OOXML namespace"
            )
        
        # Validate element name format
        element = ooxml.get("element")
        if element and not re.match(r"^[a-zA-Z][a-zA-Z0-9]*$", element):
            result.add_error(
                field="ooxml.element",
                message="OOXML element name should contain only letters and numbers",
                value=element,
                code="INVALID_ELEMENT_NAME"
            )
        
        # Validate attribute name format (if present)
        attribute = ooxml.get("attribute")
        if attribute and not re.match(r"^[a-zA-Z][a-zA-Z0-9]*$", attribute):
            result.add_error(
                field="ooxml.attribute", 
                message="OOXML attribute name should contain only letters and numbers",
                value=attribute,
                code="INVALID_ATTRIBUTE_NAME"
            )
        
        # Validate value type compatibility
        value_type = ooxml.get("valueType")
        self._validate_value_type_compatibility(var_type, value_type, result)
    
    def _validate_value_type_compatibility(self, var_type: str, value_type: str, result: ValidationResult):
        """Validate that variable type is compatible with OOXML value type"""
        compatibility_map = {
            "color": ["direct", "schemeClr"],
            "font": ["direct", "themeFont"], 
            "dimension": ["direct", "emu", "calculated"],
            "position": ["direct", "emu", "calculated"],
            "boolean": ["direct", "boolean"],
            "number": ["direct", "calculated", "percentage"],
            "text": ["direct"]
        }
        
        if var_type and value_type:
            compatible_types = compatibility_map.get(var_type, [])
            if value_type not in compatible_types:
                result.add_error(
                    field="ooxml.valueType",
                    message=f"Value type '{value_type}' incompatible with variable type '{var_type}'",
                    value=value_type,
                    code="INCOMPATIBLE_VALUE_TYPE",
                    suggestion=f"Use one of: {', '.join(compatible_types)}"
                )
    
    def _validate_type_specific_rules(self, variable: Dict[str, Any], result: ValidationResult):
        """Validate type-specific rules for variables"""
        var_type = variable.get("type")
        default_value = variable.get("defaultValue")
        
        if var_type == "color" and default_value:
            self._validate_color_value(default_value, result)
        elif var_type == "dimension" and default_value:
            self._validate_dimension_value(default_value, result)
        elif var_type == "font" and default_value:
            self._validate_font_value(default_value, result)
    
    def _validate_color_value(self, color_value: Any, result: ValidationResult):
        """Validate color value format"""
        if isinstance(color_value, str):
            # Hex color validation
            if re.match(r"^[0-9A-Fa-f]{6}$", color_value):
                return  # Valid hex color
            
            # Theme color validation
            theme_colors = ["accent1", "accent2", "accent3", "accent4", "accent5", "accent6",
                          "bg1", "bg2", "tx1", "tx2", "hlink", "folHlink"]
            if color_value in theme_colors:
                return  # Valid theme color
                
            result.add_error(
                field="defaultValue",
                message="Color value must be 6-digit hex (e.g., '0066CC') or theme color reference",
                value=color_value,
                code="INVALID_COLOR_FORMAT",
                suggestion="Use format like '0066CC' or 'accent1'"
            )
    
    def _validate_dimension_value(self, dim_value: Any, result: ValidationResult):
        """Validate dimension value format"""
        if isinstance(dim_value, (int, float)) and dim_value >= 0:
            return  # Valid numeric dimension
        
        if isinstance(dim_value, str):
            # Check for dimension with units
            if re.match(r"^\d+(\.\d+)?(pt|in|mm|cm|px|emu)$", dim_value):
                return  # Valid dimension with units
            
            # Check for pure EMU number as string
            if re.match(r"^\d+$", dim_value):
                return  # Valid EMU as string
                
        result.add_error(
            field="defaultValue",
            message="Dimension must be positive number or string with units (e.g., '12pt', '1in', '914400')",
            value=dim_value,
            code="INVALID_DIMENSION_FORMAT",
            suggestion="Use format like '12pt', '1in', or EMU units like '914400'"
        )
    
    def _validate_font_value(self, font_value: Any, result: ValidationResult):
        """Validate font value"""
        if not isinstance(font_value, str) or len(font_value.strip()) == 0:
            result.add_error(
                field="defaultValue",
                message="Font value must be non-empty string",
                value=font_value,
                code="INVALID_FONT_FORMAT"
            )
    
    def _validate_dependencies(self, variable: Dict[str, Any], result: ValidationResult):
        """Validate variable dependencies"""
        dependencies = variable.get("dependencies", [])
        var_id = variable.get("id")
        
        if not dependencies:
            return
            
        # Check for self-dependency
        if var_id in dependencies:
            result.add_error(
                field="dependencies",
                message="Variable cannot depend on itself",
                value=dependencies,
                code="CIRCULAR_DEPENDENCY"
            )
        
        # Validate dependency ID format
        for dep_id in dependencies:
            if not isinstance(dep_id, str) or not re.match(r"^[a-zA-Z][a-zA-Z0-9._]*$", dep_id):
                result.add_error(
                    field="dependencies",
                    message=f"Invalid dependency ID format: {dep_id}",
                    value=dep_id,
                    code="INVALID_DEPENDENCY_ID"
                )
    
    def _validate_cross_dependencies(self, variables: List[Dict[str, Any]], results: List[ValidationResult]):
        """Validate cross-variable dependencies"""
        variable_ids = {var.get("id") for var in variables if var.get("id")}
        
        for i, variable in enumerate(variables):
            dependencies = variable.get("dependencies", [])
            result = results[i]
            
            # Check that all dependencies exist
            for dep_id in dependencies:
                if dep_id not in variable_ids:
                    result.add_error(
                        field="dependencies",
                        message=f"Dependency '{dep_id}' not found in variable collection",
                        value=dep_id,
                        code="MISSING_DEPENDENCY"
                    )
        
        # TODO: Implement circular dependency detection across multiple variables
        # This would require building a dependency graph and checking for cycles
    
    def format_validation_report(self, results: List[ValidationResult]) -> str:
        """Format validation results as human-readable report"""
        report_lines = []
        
        # Summary
        total_vars = len(results)
        valid_vars = sum(1 for r in results if r.is_valid)
        total_errors = sum(len(r.errors) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)
        
        report_lines.append("OOXML Extension Variable Validation Report")
        report_lines.append("=" * 50)
        report_lines.append(f"Total Variables: {total_vars}")
        report_lines.append(f"Valid Variables: {valid_vars}")
        report_lines.append(f"Invalid Variables: {total_vars - valid_vars}")
        report_lines.append(f"Total Errors: {total_errors}")
        report_lines.append(f"Total Warnings: {total_warnings}")
        report_lines.append("")
        
        # Detailed results
        for result in results:
            if result.errors or result.warnings:
                report_lines.append(f"Variable: {result.variable_id}")
                report_lines.append("-" * 30)
                
                for error in result.errors:
                    report_lines.append(f"  ERROR [{error.code}] {error.field}: {error.message}")
                    if error.value is not None:
                        report_lines.append(f"    Value: {error.value}")
                    if error.suggestion:
                        report_lines.append(f"    Suggestion: {error.suggestion}")
                
                for warning in result.warnings:
                    report_lines.append(f"  WARNING [{warning.code}] {warning.field}: {warning.message}")
                    if warning.suggestion:
                        report_lines.append(f"    Suggestion: {warning.suggestion}")
                
                report_lines.append("")
        
        return "\n".join(report_lines)


def validate_variable_file(file_path: Path) -> List[ValidationResult]:
    """Validate variables from JSON or JSON file"""
    validator = ExtensionSchemaValidator()
    
    try:
        with open(file_path, 'r') as f:
            if file_path.suffix.lower() in ['.json', '.yml']:
                data = json.safe_load(f)
            else:
                data = json.load(f)
        
        # Handle different file formats
        if isinstance(data, dict) and "variables" in data:
            variables = []
            for category, vars_dict in data["variables"].items():
                for var_name, var_def in vars_dict.items():
                    if not var_def.get("id"):
                        var_def["id"] = var_name
                    variables.append(var_def)
        elif isinstance(data, list):
            variables = data
        else:
            raise ValueError("File must contain either a list of variables or a 'variables' object")
        
        return validator.validate_variable_collection(variables)
        
    except Exception as e:
        # Return error result for file loading issues
        result = ValidationResult()
        result.add_error(
            field="file",
            message=f"Failed to load file: {e}",
            code="FILE_LOAD_ERROR"
        )
        return [result]


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python extension_schema_validator.py <variable_file.json>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    results = validate_variable_file(file_path)
    
    validator = ExtensionSchemaValidator()
    report = validator.format_validation_report(results)
    print(report)
    
    # Exit with error code if validation failed
    if any(not r.is_valid for r in results):
        sys.exit(1)