"""
Base validation framework for StyleStack

This module eliminates the duplicate ValidationResult classes found in 4+ files
and provides a standardized validation framework across the codebase.

Replaces duplicate ValidationResult implementations in:
- tools/extension_schema_validator.py:64
- tools/supertheme_validator.py:56  
- tools/w3c_dtcg_validator.py:63
- tools/powerpoint_layout_schema.py:25
"""

from .imports import dataclass, field, List, Dict, Any, Optional, Union, get_logger

logger = get_logger(__name__)


@dataclass
class ValidationError:
    """
    Standardized validation error representation
    
    Replaces various error classes across validation modules
    """
    field: str
    message: str
    value: Any = None
    severity: str = "error"  # "error", "warning", "info"
    code: str = ""
    suggestion: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    line_number: Optional[int] = None
    
    def __str__(self) -> str:
        """Human-readable error representation"""
        parts = [f"{self.field}: {self.message}"]
        
        if self.value is not None:
            parts.append(f"(value: {self.value})")
            
        if self.line_number:
            parts.append(f"at line {self.line_number}")
            
        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")
            
        return " ".join(parts)


@dataclass
class ValidationResult:
    """
    Standardized validation result container
    
    Replaces duplicate ValidationResult classes across 4+ modules
    """
    is_valid: bool = True
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    info_messages: List[ValidationError] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    variable_id: Optional[str] = None  # For variable-specific validation
    
    def add_error(
        self, 
        field: str, 
        message: str, 
        value: Any = None,
        code: str = "",
        suggestion: str = "",
        context: Dict[str, Any] = None,
        line_number: Optional[int] = None
    ) -> None:
        """Add validation error and mark result as invalid"""
        error = ValidationError(
            field=field,
            message=message, 
            value=value,
            severity="error",
            code=code,
            suggestion=suggestion,
            context=context or {},
            line_number=line_number
        )
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(
        self,
        field: str,
        message: str,
        value: Any = None,
        code: str = "",
        suggestion: str = "",
        context: Dict[str, Any] = None,
        line_number: Optional[int] = None
    ) -> None:
        """Add validation warning (doesn't affect validity)"""
        warning = ValidationError(
            field=field,
            message=message,
            value=value, 
            severity="warning",
            code=code,
            suggestion=suggestion,
            context=context or {},
            line_number=line_number
        )
        self.warnings.append(warning)
    
    def add_info(
        self,
        field: str,
        message: str,
        value: Any = None,
        context: Dict[str, Any] = None
    ) -> None:
        """Add informational message"""
        info = ValidationError(
            field=field,
            message=message,
            value=value,
            severity="info", 
            context=context or {}
        )
        self.info_messages.append(info)
    
    @property
    def error_count(self) -> int:
        """Number of validation errors"""
        return len(self.errors)
    
    @property 
    def warning_count(self) -> int:
        """Number of validation warnings"""
        return len(self.warnings)
    
    @property
    def total_issues(self) -> int:
        """Total number of errors and warnings"""
        return len(self.errors) + len(self.warnings)
    
    def get_errors_by_field(self, field: str) -> List[ValidationError]:
        """Get all errors for a specific field"""
        return [error for error in self.errors if error.field == field]
    
    def get_errors_by_code(self, code: str) -> List[ValidationError]:
        """Get all errors with a specific error code"""
        return [error for error in self.errors if error.code == code]
    
    def merge(self, other: 'ValidationResult') -> None:
        """Merge another validation result into this one"""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.info_messages.extend(other.info_messages)
        
        if other.errors:
            self.is_valid = False
            
        # Merge metadata
        self.metadata.update(other.metadata)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary"""
        return {
            "is_valid": self.is_valid,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "errors": [
                {
                    "field": e.field,
                    "message": e.message,
                    "value": e.value,
                    "code": e.code,
                    "suggestion": e.suggestion,
                    "line_number": e.line_number
                }
                for e in self.errors
            ],
            "warnings": [
                {
                    "field": w.field, 
                    "message": w.message,
                    "value": w.value,
                    "code": w.code,
                    "suggestion": w.suggestion,
                    "line_number": w.line_number
                }
                for w in self.warnings
            ],
            "metadata": self.metadata
        }
    
    def format_summary(self) -> str:
        """Format validation result as human-readable summary"""
        if self.is_valid and not self.warnings:
            return "✅ Validation passed with no issues"
        
        lines = []
        
        if self.errors:
            lines.append(f"❌ {len(self.errors)} error(s):")
            for error in self.errors:
                lines.append(f"  • {error}")
        
        if self.warnings:
            lines.append(f"⚠️  {len(self.warnings)} warning(s):")
            for warning in self.warnings:
                lines.append(f"  • {warning}")
        
        if self.info_messages:
            lines.append(f"ℹ️  {len(self.info_messages)} info message(s):")
            for info in self.info_messages:
                lines.append(f"  • {info}")
        
        return "\n".join(lines)


class BaseValidator:
    """
    Base class for all validators
    
    Provides common validation patterns and error handling
    """
    
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self.logger = get_logger(f"{__name__}.{self.name}")
    
    def validate(self, data: Any, context: Dict[str, Any] = None) -> ValidationResult:
        """
        Main validation method - override in subclasses
        
        Args:
            data: Data to validate
            context: Additional validation context
            
        Returns:
            ValidationResult with errors/warnings
        """
        raise NotImplementedError("Subclasses must implement validate()")
    
    def _create_result(self) -> ValidationResult:
        """Create a new validation result"""
        return ValidationResult()
    
    def _validate_required_field(
        self, 
        data: Dict[str, Any], 
        field_name: str, 
        result: ValidationResult
    ) -> bool:
        """
        Validate that a required field exists and has a value
        
        Returns True if field is present and valid
        """
        if field_name not in data:
            result.add_error(
                field=field_name,
                message=f"Required field '{field_name}' is missing",
                code="MISSING_REQUIRED_FIELD"
            )
            return False
        
        value = data[field_name]
        if value is None or (isinstance(value, str) and not value.strip()):
            result.add_error(
                field=field_name,
                message=f"Required field '{field_name}' cannot be empty",
                value=value,
                code="EMPTY_REQUIRED_FIELD"
            )
            return False
        
        return True
    
    def _validate_field_type(
        self,
        data: Dict[str, Any],
        field_name: str,
        expected_type: type,
        result: ValidationResult,
        required: bool = False
    ) -> bool:
        """
        Validate field type
        
        Returns True if field type is correct or field is missing (when not required)
        """
        if field_name not in data:
            if required:
                result.add_error(
                    field=field_name,
                    message=f"Required field '{field_name}' is missing",
                    code="MISSING_REQUIRED_FIELD"
                )
                return False
            return True
        
        value = data[field_name]
        if not isinstance(value, expected_type):
            result.add_error(
                field=field_name,
                message=f"Field '{field_name}' must be of type {expected_type.__name__}",
                value=f"{type(value).__name__}: {value}",
                code="INVALID_FIELD_TYPE",
                suggestion=f"Convert value to {expected_type.__name__}"
            )
            return False
        
        return True
    
    def _validate_enum_value(
        self,
        data: Dict[str, Any], 
        field_name: str,
        valid_values: List[Any],
        result: ValidationResult,
        required: bool = False
    ) -> bool:
        """
        Validate field value is in allowed set
        
        Returns True if field value is valid or field is missing (when not required)
        """
        if field_name not in data:
            if required:
                result.add_error(
                    field=field_name,
                    message=f"Required field '{field_name}' is missing",
                    code="MISSING_REQUIRED_FIELD"
                )
                return False
            return True
        
        value = data[field_name]
        if value not in valid_values:
            result.add_error(
                field=field_name,
                message=f"Field '{field_name}' must be one of: {valid_values}",
                value=value,
                code="INVALID_ENUM_VALUE",
                suggestion=f"Use one of: {', '.join(map(str, valid_values))}"
            )
            return False
        
        return True


# Specialized validator mixins
class SchemaValidatorMixin:
    """Mixin for JSON schema validation capabilities"""
    
    def validate_against_schema(
        self, 
        data: Dict[str, Any], 
        schema: Dict[str, Any],
        result: ValidationResult
    ) -> None:
        """
        Validate data against JSON schema
        
        This is a simplified schema validator - for full JSON Schema support,
        consider using the jsonschema library
        """
        if "required" in schema:
            for field in schema["required"]:
                if field not in data:
                    result.add_error(
                        field=field,
                        message=f"Required property '{field}' is missing",
                        code="SCHEMA_REQUIRED_MISSING"
                    )
        
        if "properties" in schema:
            for field, field_schema in schema["properties"].items():
                if field in data:
                    self._validate_field_against_schema(
                        data[field], field, field_schema, result
                    )
    
    def _validate_field_against_schema(
        self,
        value: Any,
        field_name: str, 
        field_schema: Dict[str, Any],
        result: ValidationResult
    ) -> None:
        """Validate individual field against schema"""
        if "type" in field_schema:
            expected_type = field_schema["type"]
            if expected_type == "string" and not isinstance(value, str):
                result.add_error(
                    field=field_name,
                    message=f"Field must be a string",
                    value=value,
                    code="SCHEMA_TYPE_MISMATCH"
                )
            elif expected_type == "number" and not isinstance(value, (int, float)):
                result.add_error(
                    field=field_name,
                    message=f"Field must be a number", 
                    value=value,
                    code="SCHEMA_TYPE_MISMATCH"
                )


# Export all classes and functions
__all__ = [
    'ValidationError',
    'ValidationResult', 
    'BaseValidator',
    'SchemaValidatorMixin'
]