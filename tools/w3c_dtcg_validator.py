#!/usr/bin/env python3
"""
W3C DTCG Design Token Validator

Validates design tokens against the W3C Design Tokens Community Group specification
with StyleStack-specific extensions for enterprise Office integration.
"""

# Use shared utilities to eliminate duplication
from tools.core import (
    Any, Dict, List, Optional, Union, Path, get_logger,
    ValidationResult, ValidationError as CoreValidationError,
    safe_load_json, error_boundary, handle_processing_error
)
import re
import math
from enum import Enum
import jsonschema
from jsonschema import validate, ValidationError as JSONSchemaError, Draft7Validator

# Configure logging
logger = get_logger(__name__)


class TokenType(Enum):
    """W3C DTCG token types"""
    COLOR = "color"
    DIMENSION = "dimension"
    FONT_FAMILY = "fontFamily"
    FONT_WEIGHT = "fontWeight"
    FONT_SIZE = "fontSize"
    LINE_HEIGHT = "lineHeight"
    LETTER_SPACING = "letterSpacing"
    TYPOGRAPHY = "typography"
    SHADOW = "shadow"
    BORDER = "border"
    GRADIENT = "gradient"
    TRANSITION = "transition"
    CUBIC_BEZIER = "cubic-bezier"
    NUMBER = "number"
    DURATION = "duration"
    STROKE_STYLE = "strokeStyle"
    STRING = "string"


class Platform(Enum):
    """Supported platforms"""
    OFFICE = "office"
    LIBREOFFICE = "libreoffice"
    GOOGLE = "google"
    WEB = "web"
    PRINT = "print"


# Using shared ValidationResult from tools.core - eliminates duplicate class
# Extended with W3C DTCG-specific fields

class W3CDTCGValidationResult(ValidationResult):
    """Extended validation result for W3C DTCG tokens"""
    
    def __init__(self):
        super().__init__()
        self.metadata.update({
            'token_name': None,
            'token_type': None
        })
    
    @property
    def token_name(self) -> Optional[str]:
        return self.metadata.get('token_name')
    
    @token_name.setter
    def token_name(self, value: Optional[str]):
        self.metadata['token_name'] = value
    
    @property
    def token_type(self) -> Optional[TokenType]:
        return self.metadata.get('token_type')
    
    @token_type.setter
    def token_type(self, value: Optional[TokenType]):
        self.metadata['token_type'] = value
    
    def add_w3c_error(self, field: str, message: str, value: Any = None, code: str = "", suggestion: str = "", token_path: str = ""):
        """Add W3C DTCG-specific validation error"""
        full_context = {'token_path': token_path}
        self.add_error(
            field=field,
            message=message,
            value=value,
            code=f"W3C_DTCG_{code}" if code else "W3C_DTCG_ERROR",
            suggestion=suggestion,
            context=full_context
        )
    
    def add_w3c_warning(self, field: str, message: str, value: Any = None, code: str = "", suggestion: str = "", token_path: str = ""):
        """Add W3C DTCG-specific validation warning"""
        full_context = {'token_path': token_path}
        self.add_warning(
            field=field,
            message=message,
            value=value,
            code=f"W3C_DTCG_{code}" if code else "W3C_DTCG_WARNING",
            suggestion=suggestion,
            context=full_context
        )
        self.warnings.append(ValidationError(
            field=field, message=message, value=value,
            severity="warning", code=code, suggestion=suggestion, token_path=token_path
        ))


class W3CDTCGValidator:
    """W3C DTCG compliant token validator with StyleStack extensions"""
    
    def __init__(self, schema_path: Optional[Path] = None):
        """Initialize validator with enhanced schema"""
        self.schema_path = schema_path or self._get_default_schema_path()
        self.schema = self._load_schema()
        self.validator = Draft7Validator(self.schema)
        
        # Color utilities for accessibility validation
        self._color_regex = re.compile(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')
        
        # Expression patterns for mathematical expressions
        self._expression_patterns = {
            'reference': re.compile(r'\{([a-zA-Z][a-zA-Z0-9._]*)\}'),
            'nested_reference': re.compile(r'\{([a-zA-Z][a-zA-Z0-9._]*)\.\{([a-zA-Z][a-zA-Z0-9._]*)\}\.([a-zA-Z][a-zA-Z0-9._]*)\}'),
            'function_call': re.compile(r'\{([a-zA-Z][a-zA-Z0-9._]*)\}\.([a-zA-Z]+)\(([^)]+)\)'),
            'arithmetic': re.compile(r'\{([a-zA-Z][a-zA-Z0-9._]*)\}\s*([+\-*/])\s*([0-9.]+|[{][a-zA-Z][a-zA-Z0-9._]*[}])'),
            'calc_function': re.compile(r'calc\(([^)]+)\)')
        }
        
    def _get_default_schema_path(self) -> Path:
        """Get default enhanced schema file path"""
        return Path(__file__).parent.parent / "schemas" / "enhanced-token.schema.json"
        
    def _load_schema(self) -> Dict[str, Any]:
        """Load enhanced JSON schema from file"""
        try:
            return safe_load_json(self.schema_path)
        except FileNotFoundError:
            raise ValueError(f"Enhanced schema file not found: {self.schema_path}")
        except Exception as e:
            raise ValueError(f"Failed to load schema: {e}")
    
    def validate_token(self, token: Dict[str, Any], token_path: str = "") -> W3CDTCGValidationResult:
        """Validate a single W3C DTCG token"""
        result = W3CDTCGValidationResult()
        result.token_name = token_path or token.get("$extensions", {}).get("stylestack", {}).get("id", "<unknown>")
        
        try:
            # Basic W3C DTCG schema validation
            self.validator.validate(token)
            
            # Set token type
            token_type_str = token.get('$type')
            if token_type_str:
                try:
                    result.token_type = TokenType(token_type_str)
                except ValueError:
                    result.token_type = None
            
            # Enhanced validations
            self._validate_token_type_consistency(token, result, token_path)
            self._validate_token_value(token, result, token_path)
            self._validate_mathematical_expressions(token, result, token_path)
            self._validate_nested_references(token, result, token_path)
            self._validate_stylestack_extensions(token, result, token_path)
            self._validate_accessibility_compliance(token, result, token_path)
            self._validate_emu_precision(token, result, token_path)
            self._validate_platform_compatibility(token, result, token_path)
            self._validate_brand_compliance(token, result, token_path)
            
            # Set final validation state
            result.is_valid = len(result.errors) == 0
            
        except jsonschema.ValidationError as e:
            result.add_error(
                field=".".join(str(x) for x in e.absolute_path),
                message=e.message,
                value=e.instance,
                code="SCHEMA_VALIDATION_ERROR",
                token_path=token_path
            )
            
        return result
    
    def validate_token_collection(self, tokens: Dict[str, Dict[str, Any]]) -> Dict[str, ValidationResult]:
        """Validate a collection of tokens with cross-validation"""
        results = {}
        
        # First pass: individual token validation
        for token_name, token in tokens.items():
            results[token_name] = self.validate_token(token, token_name)
        
        # Second pass: cross-token validation
        self._validate_token_references(tokens, results)
        self._validate_circular_dependencies(tokens, results)
        
        return results
    
    def _validate_token_type_consistency(self, token: Dict[str, Any], result: ValidationResult, token_path: str):
        """Validate token type consistency with value"""
        token_type = token.get("$type")
        token_value = token.get("$value")
        
        if not token_type or not token_value:
            return
            
        # Type-specific value validation
        if token_type == "color":
            self._validate_color_value(token_value, result, token_path)
        elif token_type == "dimension":
            self._validate_dimension_value(token_value, result, token_path)
        elif token_type == "typography":
            self._validate_typography_value(token_value, result, token_path)
        elif token_type == "shadow":
            self._validate_shadow_value(token_value, result, token_path)
        elif token_type == "border":
            self._validate_border_value(token_value, result, token_path)
        elif token_type == "gradient":
            self._validate_gradient_value(token_value, result, token_path)
    
    def _validate_color_value(self, value: Any, result: ValidationResult, token_path: str):
        """Validate color token value format"""
        if isinstance(value, str):
            # Check for hex color
            if self._color_regex.match(value):
                return
            
            # Check for reference or expression
            if self._is_token_reference_or_expression(value):
                return
                
            # Check for named colors (basic set)
            named_colors = ["transparent", "currentColor", "inherit"]
            if value.lower() in named_colors:
                return
                
            result.add_error(
                field="$value",
                message=f"Invalid color format: {value}",
                value=value,
                code="INVALID_COLOR_FORMAT",
                suggestion="Use hex format like '#0066CC' or token reference like '{brand.primary}'",
                token_path=token_path
            )
        elif isinstance(value, dict):
            # Platform-conditional color values
            self._validate_conditional_value(value, "color", result, token_path)
        else:
            result.add_error(
                field="$value",
                message="Color value must be string or object for conditional values",
                value=value,
                code="INVALID_COLOR_TYPE",
                token_path=token_path
            )
    
    def _validate_dimension_value(self, value: Any, result: ValidationResult, token_path: str):
        """Validate dimension token value format"""
        if isinstance(value, str):
            # Check for valid dimension units
            dimension_pattern = re.compile(r'^(\d+(?:\.\d+)?)(px|pt|em|rem|ex|ch|vw|vh|vmin|vmax|cm|mm|in|pc)$')
            if dimension_pattern.match(value):
                return
                
            # Check for EMU units (StyleStack specific)
            if re.match(r'^\d+$', value):
                return  # Pure EMU value
                
            # Check for reference or expression
            if self._is_token_reference_or_expression(value):
                return
                
            result.add_error(
                field="$value",
                message=f"Invalid dimension format: {value}",
                value=value,
                code="INVALID_DIMENSION_FORMAT", 
                suggestion="Use format like '16px', '12pt', or token reference",
                token_path=token_path
            )
        elif isinstance(value, (int, float)):
            if value < 0:
                result.add_warning(
                    field="$value",
                    message="Negative dimension value may cause rendering issues",
                    value=value,
                    code="NEGATIVE_DIMENSION_WARNING",
                    token_path=token_path
                )
        elif isinstance(value, dict):
            # Platform-conditional dimension values
            self._validate_conditional_value(value, "dimension", result, token_path)
    
    def _validate_typography_value(self, value: Any, result: ValidationResult, token_path: str):
        """Validate typography composite token value"""
        if not isinstance(value, dict):
            result.add_error(
                field="$value",
                message="Typography value must be an object",
                value=value,
                code="INVALID_TYPOGRAPHY_TYPE",
                token_path=token_path
            )
            return
            
        # Check required typography properties
        typography_props = ["fontFamily", "fontSize", "fontWeight", "lineHeight"]
        for prop in typography_props:
            if prop in value:
                if prop == "fontSize":
                    self._validate_dimension_value(value[prop], result, f"{token_path}.{prop}")
                elif prop == "fontWeight":
                    self._validate_font_weight(value[prop], result, f"{token_path}.{prop}")
    
    def _validate_font_weight(self, value: Any, result: ValidationResult, token_path: str):
        """Validate font weight value"""
        valid_weights = ["100", "200", "300", "400", "500", "600", "700", "800", "900",
                        "normal", "bold", "bolder", "lighter"]
        
        if isinstance(value, str):
            if value not in valid_weights and not self._is_token_reference_or_expression(value):
                result.add_error(
                    field="fontWeight",
                    message=f"Invalid font weight: {value}",
                    value=value,
                    code="INVALID_FONT_WEIGHT",
                    suggestion="Use numeric (100-900) or keyword (normal, bold) values",
                    token_path=token_path
                )
        elif isinstance(value, int):
            if value < 100 or value > 900 or value % 100 != 0:
                result.add_error(
                    field="fontWeight",
                    message="Font weight must be 100-900 in increments of 100",
                    value=value,
                    code="INVALID_FONT_WEIGHT_RANGE",
                    token_path=token_path
                )
    
    def _validate_shadow_value(self, value: Any, result: ValidationResult, token_path: str):
        """Validate shadow composite token value"""
        if not isinstance(value, dict):
            result.add_error(
                field="$value",
                message="Shadow value must be an object",
                value=value,
                code="INVALID_SHADOW_TYPE",
                token_path=token_path
            )
            return
            
        # Required shadow properties
        required_props = ["color", "offsetX", "offsetY", "blur"]
        for prop in required_props:
            if prop not in value:
                result.add_error(
                    field=f"$value.{prop}",
                    message=f"Missing required shadow property: {prop}",
                    code="MISSING_SHADOW_PROPERTY",
                    token_path=token_path
                )
            else:
                if prop == "color":
                    self._validate_color_value(value[prop], result, f"{token_path}.{prop}")
                else:
                    self._validate_dimension_value(value[prop], result, f"{token_path}.{prop}")
    
    def _validate_border_value(self, value: Any, result: ValidationResult, token_path: str):
        """Validate border composite token value"""
        if not isinstance(value, dict):
            result.add_error(
                field="$value",
                message="Border value must be an object",
                value=value,
                code="INVALID_BORDER_TYPE",
                token_path=token_path
            )
            return
            
        # Validate border properties
        if "width" in value:
            self._validate_dimension_value(value["width"], result, f"{token_path}.width")
        if "color" in value:
            self._validate_color_value(value["color"], result, f"{token_path}.color")
        if "style" in value:
            valid_styles = ["solid", "dashed", "dotted", "double", "groove", "ridge", "inset", "outset", "none", "hidden"]
            if value["style"] not in valid_styles and not self._is_token_reference_or_expression(value["style"]):
                result.add_error(
                    field="$value.style",
                    message=f"Invalid border style: {value['style']}",
                    value=value["style"],
                    code="INVALID_BORDER_STYLE",
                    suggestion=f"Use one of: {', '.join(valid_styles)}",
                    token_path=token_path
                )
    
    def _validate_gradient_value(self, value: Any, result: ValidationResult, token_path: str):
        """Validate gradient composite token value"""
        if not isinstance(value, dict):
            result.add_error(
                field="$value",
                message="Gradient value must be an object",
                value=value,
                code="INVALID_GRADIENT_TYPE",
                token_path=token_path
            )
            return
            
        # Validate gradient type
        if "type" in value:
            valid_types = ["linear", "radial", "conic"]
            if value["type"] not in valid_types:
                result.add_error(
                    field="$value.type",
                    message=f"Invalid gradient type: {value['type']}",
                    value=value["type"],
                    code="INVALID_GRADIENT_TYPE",
                    suggestion=f"Use one of: {', '.join(valid_types)}",
                    token_path=token_path
                )
        
        # Validate gradient stops
        if "stops" in value:
            if not isinstance(value["stops"], list) or len(value["stops"]) < 2:
                result.add_error(
                    field="$value.stops",
                    message="Gradient must have at least 2 stops",
                    value=value["stops"],
                    code="INSUFFICIENT_GRADIENT_STOPS",
                    token_path=token_path
                )
            else:
                for i, stop in enumerate(value["stops"]):
                    if isinstance(stop, dict):
                        if "color" in stop:
                            self._validate_color_value(stop["color"], result, f"{token_path}.stops[{i}].color")
                        if "position" in stop:
                            position_pattern = re.compile(r'^\d+(\.\d+)?%$')
                            if not position_pattern.match(str(stop["position"])):
                                result.add_error(
                                    field=f"$value.stops[{i}].position",
                                    message="Stop position must be a percentage (e.g., '50%')",
                                    value=stop["position"],
                                    code="INVALID_STOP_POSITION",
                                    token_path=token_path
                                )
    
    def _validate_conditional_value(self, value: Dict[str, Any], expected_type: str, result: ValidationResult, token_path: str):
        """Validate platform-conditional values"""
        valid_platforms = [p.value for p in Platform]
        
        for platform, platform_value in value.items():
            if platform not in valid_platforms:
                result.add_warning(
                    field=f"$value.{platform}",
                    message=f"Unknown platform: {platform}",
                    value=platform,
                    code="UNKNOWN_PLATFORM",
                    suggestion=f"Use one of: {', '.join(valid_platforms)}",
                    token_path=token_path
                )
            
            # Validate platform-specific value based on expected type
            if expected_type == "color":
                self._validate_color_value(platform_value, result, f"{token_path}.{platform}")
            elif expected_type == "dimension":
                self._validate_dimension_value(platform_value, result, f"{token_path}.{platform}")
    
    def _validate_token_value(self, token: Dict[str, Any], result: ValidationResult, token_path: str):
        """Validate token value against its type"""
        # This is handled by type-specific validation methods above
        pass
    
    def _validate_mathematical_expressions(self, token: Dict[str, Any], result: ValidationResult, token_path: str):
        """Validate mathematical expressions in token values"""
        value = token.get("$value")
        if not isinstance(value, str):
            return
            
        # Check for various expression types
        if self._expression_patterns['reference'].search(value):
            self._validate_token_references_in_value(value, result, token_path)
        
        if self._expression_patterns['arithmetic'].search(value):
            self._validate_arithmetic_expression(value, result, token_path)
            
        if self._expression_patterns['function_call'].search(value):
            self._validate_function_call(value, result, token_path)
    
    def _validate_nested_references(self, token: Dict[str, Any], result: ValidationResult, token_path: str):
        """Validate nested reference patterns in token values"""
        import re
        
        # Nested reference pattern: {base.{dynamic}.property}
        nested_pattern = re.compile(r'\{([^{}]+)\.\{([^{}]+)\}\.([^{}]+)\}')
        
        def validate_value_recursively(value, path="$value"):
            if isinstance(value, str):
                # Check for nested reference patterns
                nested_matches = nested_pattern.findall(value)
                for match in nested_matches:
                    base, dynamic, prop = match
                    
                    # Validate nested reference structure
                    if not base.strip():
                        result.add_error(
                            field=f"{path}.nested_reference",
                            message="Nested reference missing base path",
                            value=f"{{{base}.{{{dynamic}}}.{prop}}}",
                            code="NESTED_REF_INVALID_BASE",
                            suggestion="Provide a valid base path before the dynamic segment",
                            token_path=token_path
                        )
                    
                    if not dynamic.strip():
                        result.add_error(
                            field=f"{path}.nested_reference", 
                            message="Nested reference missing dynamic variable",
                            value=f"{{{base}.{{{dynamic}}}.{prop}}}",
                            code="NESTED_REF_INVALID_DYNAMIC",
                            suggestion="Provide a valid dynamic variable name",
                            token_path=token_path
                        )
                    
                    if not prop.strip():
                        result.add_error(
                            field=f"{path}.nested_reference",
                            message="Nested reference missing property path", 
                            value=f"{{{base}.{{{dynamic}}}.{prop}}}",
                            code="NESTED_REF_INVALID_PROPERTY",
                            suggestion="Provide a valid property path after the dynamic segment",
                            token_path=token_path
                        )
                    
                    # Check for invalid characters in segments
                    invalid_chars = re.compile(r'[^a-zA-Z0-9._-]')
                    for segment_name, segment_value in [("base", base), ("dynamic", dynamic), ("property", prop)]:
                        if invalid_chars.search(segment_value):
                            result.add_warning(
                                field=f"{path}.nested_reference.{segment_name}",
                                message=f"Nested reference {segment_name} contains potentially invalid characters",
                                value=segment_value,
                                code="NESTED_REF_INVALID_CHARS",
                                suggestion="Use only alphanumeric characters, dots, hyphens, and underscores",
                                token_path=token_path
                            )
                
                # Check for malformed nested patterns
                malformed_patterns = [
                    r'\{[^{}]*\{[^{}]*[^}]$',  # Missing closing brace
                    r'^[^{]*\}[^{}]*\}',       # Missing opening brace
                    r'\{\{[^}]*\}[^}]*\}',     # Double opening brace
                    r'\{[^{]*\{\}[^}]*\}',     # Empty dynamic segment
                ]
                
                for pattern in malformed_patterns:
                    if re.search(pattern, value):
                        result.add_error(
                            field=f"{path}.nested_reference",
                            message="Malformed nested reference pattern detected",
                            value=value,
                            code="NESTED_REF_MALFORMED", 
                            suggestion="Check brace matching and ensure proper nested reference syntax: {base.{dynamic}.property}",
                            token_path=token_path
                        )
                        break
            
            elif isinstance(value, dict):
                for key, subvalue in value.items():
                    validate_value_recursively(subvalue, f"{path}.{key}")
            
            elif isinstance(value, list):
                for i, subvalue in enumerate(value):
                    validate_value_recursively(subvalue, f"{path}[{i}]")
        
        # Validate the token value and any nested structures
        token_value = token.get("$value")
        if token_value is not None:
            validate_value_recursively(token_value)
    
    def _validate_token_references_in_value(self, value: str, result: ValidationResult, token_path: str):
        """Validate token references within a value"""
        references = self._expression_patterns['reference'].findall(value)
        
        for ref in references:
            if not self._is_valid_token_reference(ref):
                result.add_error(
                    field="$value",
                    message=f"Invalid token reference format: {{{ref}}}",
                    value=ref,
                    code="INVALID_TOKEN_REFERENCE",
                    suggestion="Use format like {brand.primary} or {spacing.large}",
                    token_path=token_path
                )
    
    def _validate_arithmetic_expression(self, value: str, result: ValidationResult, token_path: str):
        """Validate arithmetic expressions"""
        match = self._expression_patterns['arithmetic'].search(value)
        if match:
            operand1, operator, operand2 = match.groups()
            
            # Validate that operands are either numbers or valid token references
            if not (self._is_number(operand2) or self._is_token_reference_or_expression(operand2)):
                result.add_error(
                    field="$value",
                    message=f"Invalid arithmetic operand: {operand2}",
                    value=operand2,
                    code="INVALID_ARITHMETIC_OPERAND",
                    token_path=token_path
                )
    
    def _validate_function_call(self, value: str, result: ValidationResult, token_path: str):
        """Validate function calls in expressions"""
        match = self._expression_patterns['function_call'].search(value)
        if match:
            base_token, function_name, arguments = match.groups()
            
            # Validate function names
            valid_functions = ["lighten", "darken", "saturate", "desaturate", "adjust-hue", "complement", 
                             "multiply", "divide", "add", "subtract", "px", "pt", "em", "rem"]
            
            if function_name not in valid_functions:
                result.add_error(
                    field="$value",
                    message=f"Unknown function: {function_name}",
                    value=function_name,
                    code="UNKNOWN_FUNCTION",
                    suggestion=f"Use one of: {', '.join(valid_functions)}",
                    token_path=token_path
                )
    
    def _validate_stylestack_extensions(self, token: Dict[str, Any], result: ValidationResult, token_path: str):
        """Validate StyleStack-specific extensions"""
        extensions = token.get("$extensions", {})
        stylestack = extensions.get("stylestack", {})
        
        if not stylestack:
            return
            
        # Validate OOXML configuration
        if "ooxml" in stylestack:
            self._validate_ooxml_config(stylestack["ooxml"], result, token_path)
        
        # Validate EMU precision
        if "emu" in stylestack:
            self._validate_emu_config(stylestack["emu"], result, token_path)
        
        # Validate platform support
        if "platforms" in stylestack:
            self._validate_platform_config(stylestack["platforms"], result, token_path)
    
    def _validate_ooxml_config(self, ooxml_config: Dict[str, Any], result: ValidationResult, token_path: str):
        """Validate OOXML configuration in StyleStack extensions"""
        required_props = ["namespace", "element", "valueType"]
        
        for prop in required_props:
            if prop not in ooxml_config:
                result.add_error(
                    field=f"$extensions.stylestack.ooxml.{prop}",
                    message=f"Missing required OOXML property: {prop}",
                    code="MISSING_OOXML_PROPERTY",
                    token_path=token_path
                )
        
        # Validate namespace
        if "namespace" in ooxml_config:
            valid_namespaces = [
                "http://schemas.openxmlformats.org/drawingml/2006/main",
                "http://schemas.openxmlformats.org/presentationml/2006/main",
                "http://schemas.openxmlformats.org/wordprocessingml/2006/main", 
                "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
            ]
            if ooxml_config["namespace"] not in valid_namespaces:
                result.add_warning(
                    field="$extensions.stylestack.ooxml.namespace",
                    message="Unknown OOXML namespace",
                    value=ooxml_config["namespace"],
                    code="UNKNOWN_OOXML_NAMESPACE",
                    token_path=token_path
                )
    
    def _validate_emu_config(self, emu_config: Dict[str, Any], result: ValidationResult, token_path: str):
        """Validate EMU precision configuration"""
        if "precision" in emu_config:
            valid_precisions = ["exact", "approximate", "rounded"]
            if emu_config["precision"] not in valid_precisions:
                result.add_error(
                    field="$extensions.stylestack.emu.precision",
                    message=f"Invalid EMU precision: {emu_config['precision']}",
                    value=emu_config["precision"],
                    code="INVALID_EMU_PRECISION",
                    suggestion=f"Use one of: {', '.join(valid_precisions)}",
                    token_path=token_path
                )
    
    def _validate_platform_config(self, platform_config: Dict[str, Any], result: ValidationResult, token_path: str):
        """Validate platform support configuration"""
        valid_platforms = [p.value for p in Platform]
        
        for platform, config in platform_config.items():
            if platform not in valid_platforms:
                result.add_warning(
                    field=f"$extensions.stylestack.platforms.{platform}",
                    message=f"Unknown platform: {platform}",
                    value=platform,
                    code="UNKNOWN_PLATFORM_CONFIG",
                    token_path=token_path
                )
    
    def _validate_accessibility_compliance(self, token: Dict[str, Any], result: ValidationResult, token_path: str):
        """Validate WCAG accessibility compliance"""
        extensions = token.get("$extensions", {})
        stylestack = extensions.get("stylestack", {})
        accessibility = stylestack.get("accessibility", {})
        wcag = accessibility.get("wcag", {})
        
        if not wcag:
            return
            
        # Validate contrast ratio
        if "contrastRatio" in wcag:
            contrast = wcag["contrastRatio"]
            if not isinstance(contrast, (int, float)) or contrast < 1 or contrast > 21:
                result.add_error(
                    field="$extensions.stylestack.accessibility.wcag.contrastRatio",
                    message="Contrast ratio must be between 1 and 21",
                    value=contrast,
                    code="INVALID_CONTRAST_RATIO",
                    token_path=token_path
                )
            elif contrast < 4.5:
                result.add_warning(
                    field="$extensions.stylestack.accessibility.wcag.contrastRatio",
                    message="Contrast ratio below WCAG AA standard (4.5:1)",
                    value=contrast,
                    code="LOW_CONTRAST_WARNING",
                    suggestion="Consider increasing contrast for better accessibility",
                    token_path=token_path
                )
        
        # Validate WCAG level
        if "level" in wcag:
            valid_levels = ["A", "AA", "AAA", "FAIL"]
            if wcag["level"] not in valid_levels:
                result.add_error(
                    field="$extensions.stylestack.accessibility.wcag.level",
                    message=f"Invalid WCAG level: {wcag['level']}",
                    value=wcag["level"],
                    code="INVALID_WCAG_LEVEL",
                    suggestion=f"Use one of: {', '.join(valid_levels)}",
                    token_path=token_path
                )
    
    def _validate_emu_precision(self, token: Dict[str, Any], result: ValidationResult, token_path: str):
        """Validate EMU precision for typography tokens"""
        extensions = token.get("$extensions", {})
        stylestack = extensions.get("stylestack", {})
        emu = stylestack.get("emu", {})
        
        if not emu:
            return
            
        # Validate EMU values are proper integers
        for prop in ["fontSize", "lineHeight", "value"]:
            if prop in emu:
                emu_value = emu[prop]
                if isinstance(emu_value, str):
                    if not re.match(r'^\d+$', emu_value):
                        result.add_error(
                            field=f"$extensions.stylestack.emu.{prop}",
                            message=f"EMU value must be integer string: {emu_value}",
                            value=emu_value,
                            code="INVALID_EMU_VALUE",
                            token_path=token_path
                        )
                elif not isinstance(emu_value, int):
                    result.add_error(
                        field=f"$extensions.stylestack.emu.{prop}",
                        message=f"EMU value must be integer: {emu_value}",
                        value=emu_value,
                        code="INVALID_EMU_TYPE",
                        token_path=token_path
                    )
    
    def _validate_platform_compatibility(self, token: Dict[str, Any], result: ValidationResult, token_path: str):
        """Validate platform compatibility settings"""
        # Platform compatibility validation is handled in _validate_platform_config
        pass
    
    def _validate_brand_compliance(self, token: Dict[str, Any], result: ValidationResult, token_path: str):
        """Validate corporate brand rule compliance"""
        extensions = token.get("$extensions", {})
        stylestack = extensions.get("stylestack", {})
        brand = stylestack.get("brand", {})
        
        if not brand:
            return
            
        # Validate brand category
        if "category" in brand:
            valid_categories = ["corporate", "secondary", "neutral", "custom"]
            if brand["category"] not in valid_categories:
                result.add_error(
                    field="$extensions.stylestack.brand.category",
                    message=f"Invalid brand category: {brand['category']}",
                    value=brand["category"],
                    code="INVALID_BRAND_CATEGORY",
                    suggestion=f"Use one of: {', '.join(valid_categories)}",
                    token_path=token_path
                )
        
        # Check for brand violations
        if "violations" in brand and brand["violations"]:
            for violation in brand["violations"]:
                result.add_warning(
                    field="$extensions.stylestack.brand.violations",
                    message=f"Brand guideline violation: {violation}",
                    value=violation,
                    code="BRAND_VIOLATION_WARNING",
                    token_path=token_path
                )
    
    def _validate_token_references(self, tokens: Dict[str, Dict[str, Any]], results: Dict[str, ValidationResult]):
        """Validate that all token references exist"""
        all_token_names = set(tokens.keys())
        
        for token_name, token in tokens.items():
            result = results[token_name]
            
            # Extract references from token values
            references = self._extract_token_references(token)
            
            for ref in references:
                if ref not in all_token_names:
                    result.add_error(
                        field="$value",
                        message=f"Reference to non-existent token: {ref}",
                        value=ref,
                        code="MISSING_TOKEN_REFERENCE",
                        token_path=token_name
                    )
    
    def _validate_circular_dependencies(self, tokens: Dict[str, Dict[str, Any]], results: Dict[str, ValidationResult]):
        """Detect circular dependencies in token references"""
        dependency_graph = {}
        
        # Build dependency graph
        for token_name, token in tokens.items():
            references = self._extract_token_references(token)
            dependency_graph[token_name] = references
        
        # Check for circular dependencies
        for token_name in tokens:
            if self._has_circular_dependency(token_name, dependency_graph, set()):
                results[token_name].add_error(
                    field="dependencies",
                    message=f"Circular dependency detected for token: {token_name}",
                    code="CIRCULAR_DEPENDENCY",
                    token_path=token_name
                )
    
    def _extract_token_references(self, token: Dict[str, Any]) -> List[str]:
        """Extract all token references from a token"""
        references = []
        value = token.get("$value")
        
        if isinstance(value, str):
            # Simple references like {token.name}
            matches = self._expression_patterns['reference'].findall(value)
            references.extend(matches)
            
            # Nested references like {color.{theme}.primary}
            nested_matches = self._expression_patterns['nested_reference'].findall(value)
            for match in nested_matches:
                references.extend([match[0], match[1]])  # Base and nested reference
        
        # Check dependencies in StyleStack extensions
        extensions = token.get("$extensions", {})
        stylestack = extensions.get("stylestack", {})
        if "dependencies" in stylestack:
            references.extend(stylestack["dependencies"])
        
        return list(set(references))  # Remove duplicates
    
    def _has_circular_dependency(self, token_name: str, graph: Dict[str, List[str]], visited: set, path: set = None) -> bool:
        """Check for circular dependency using DFS"""
        if path is None:
            path = set()
            
        if token_name in path:
            return True
            
        if token_name in visited:
            return False
            
        visited.add(token_name)
        path.add(token_name)
        
        for dependency in graph.get(token_name, []):
            if self._has_circular_dependency(dependency, graph, visited, path):
                return True
        
        path.remove(token_name)
        return False
    
    def _is_token_reference_or_expression(self, value: str) -> bool:
        """Check if value is a token reference or mathematical expression"""
        return bool(
            self._expression_patterns['reference'].search(value) or
            self._expression_patterns['arithmetic'].search(value) or
            self._expression_patterns['function_call'].search(value) or
            self._expression_patterns['calc_function'].search(value)
        )
    
    def _is_valid_token_reference(self, ref: str) -> bool:
        """Validate token reference format"""
        return bool(re.match(r'^[a-zA-Z][a-zA-Z0-9._]*$', ref))
    
    def _is_number(self, value: str) -> bool:
        """Check if string represents a number"""
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def format_validation_report(self, results: Dict[str, ValidationResult]) -> str:
        """Format validation results as human-readable report"""
        report_lines = []
        
        # Summary
        total_tokens = len(results)
        valid_tokens = sum(1 for r in results.values() if r.is_valid)
        total_errors = sum(len(r.errors) for r in results.values())
        total_warnings = sum(len(r.warnings) for r in results.values())
        
        report_lines.append("W3C DTCG Design Token Validation Report")
        report_lines.append("=" * 50)
        report_lines.append(f"Total Tokens: {total_tokens}")
        report_lines.append(f"Valid Tokens: {valid_tokens}")
        report_lines.append(f"Invalid Tokens: {total_tokens - valid_tokens}")
        report_lines.append(f"Total Errors: {total_errors}")
        report_lines.append(f"Total Warnings: {total_warnings}")
        report_lines.append("")
        
        # Detailed results
        for token_name, result in results.items():
            if result.errors or result.warnings:
                report_lines.append(f"Token: {token_name}")
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


def validate_token_file(file_path: Path) -> Dict[str, ValidationResult]:
    """Validate tokens from a JSON file"""
    validator = W3CDTCGValidator()
    
    try:
        data = safe_load_json(file_path)
        
        # Handle different file formats
        if isinstance(data, dict):
            # Assume it's a collection of tokens
            return validator.validate_token_collection(data)
        else:
            raise ValueError("File must contain a dictionary of tokens")
        
    except Exception as e:
        # Return error result for file loading issues
        error_result = W3CDTCGValidationResult()
        error_result.add_error(
            field="file",
            message=f"Failed to load file: {e}",
            code="FILE_LOAD_ERROR"
        )
        return {"file_error": error_result}


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python w3c_dtcg_validator.py <token_file.json>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    results = validate_token_file(file_path)
    
    validator = W3CDTCGValidator()
    report = validator.format_validation_report(results)
    print(report)
    
    # Exit with error code if validation failed
    if any(not r.is_valid for r in results.values()):
        sys.exit(1)