"""
YAML Patch Parser

This module provides a comprehensive parser for YAML patch files that define 
OOXML template modifications. It validates patch structure, resolves references,
and provides intelligent error reporting.

Part of the StyleStack YAML-to-OOXML Processing Engine.
"""

import yaml
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import logging
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation strictness levels for patch parsing."""
    STRICT = "strict"      # Fail on any validation issue
    LENIENT = "lenient"    # Warn on minor issues, fail on major ones
    PERMISSIVE = "permissive"  # Only fail on syntax errors


@dataclass
class ParseError:
    """Represents a parsing or validation error."""
    level: str  # 'error', 'warning', 'info'
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    context: Optional[str] = None


@dataclass
class PatchMetadata:
    """Metadata extracted from a patch file."""
    version: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    target_formats: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    variables: Optional[Dict[str, Any]] = None


@dataclass 
class ParseResult:
    """Result of parsing a YAML patch file."""
    success: bool
    patches: List[Dict[str, Any]]
    metadata: PatchMetadata
    errors: List[ParseError]
    warnings: List[ParseError]
    raw_content: Dict[str, Any]


class YAMLPatchParser:
    """
    Comprehensive parser for YAML patch files.
    
    Supports:
    - Multi-document YAML files
    - Patch validation and normalization
    - Variable resolution and substitution
    - Dependency checking
    - Format-specific validation
    """
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.LENIENT):
        """Initialize the parser with specified validation level."""
        self.validation_level = validation_level
        self.supported_operations = {'set', 'insert', 'extend', 'merge', 'relsAdd'}
        self.supported_formats = {'potx', 'dotx', 'xltx'}
        self.required_fields = {'operation', 'target', 'value'}
        
        # Schema definitions for validation
        self.operation_schemas = {
            'set': {'required': ['operation', 'target', 'value']},
            'insert': {'required': ['operation', 'target', 'value'], 'optional': ['position']},
            'extend': {'required': ['operation', 'target', 'value']},
            'merge': {'required': ['operation', 'target', 'value'], 'optional': ['merge_strategy']},
            'relsAdd': {'required': ['operation', 'target', 'value']}
        }
    
    def parse_file(self, file_path: Union[str, Path]) -> ParseResult:
        """
        Parse a YAML patch file from disk.
        
        Args:
            file_path: Path to the YAML patch file
            
        Returns:
            ParseResult containing patches, metadata, and any errors/warnings
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return ParseResult(
                    success=False,
                    patches=[],
                    metadata=PatchMetadata(),
                    errors=[ParseError('error', f"File not found: {file_path}")],
                    warnings=[],
                    raw_content={}
                )
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            return self.parse_content(content, str(file_path))
            
        except Exception as e:
            logger.error(f"Failed to parse patch file {file_path}: {e}")
            return ParseResult(
                success=False,
                patches=[],
                metadata=PatchMetadata(),
                errors=[ParseError('error', f"Failed to read file: {e}")],
                warnings=[],
                raw_content={}
            )
    
    def parse_content(self, content: str, source_name: str = "<string>") -> ParseResult:
        """
        Parse YAML patch content from string.
        
        Args:
            content: YAML content to parse
            source_name: Name of the source for error reporting
            
        Returns:
            ParseResult containing parsed data and validation results
        """
        errors = []
        warnings = []
        
        try:
            # Parse YAML content
            raw_data = yaml.safe_load(content)
            
            if raw_data is None:
                return ParseResult(
                    success=False,
                    patches=[],
                    metadata=PatchMetadata(),
                    errors=[ParseError('error', "Empty or invalid YAML content")],
                    warnings=[],
                    raw_content={}
                )
            
            # Extract metadata and patches
            metadata = self._extract_metadata(raw_data, errors, warnings)
            patches = self._extract_patches(raw_data, errors, warnings)
            
            # Validate patches
            if patches:
                self._validate_patches(patches, errors, warnings)
            
            # Apply variable substitution if metadata contains variables
            if metadata.variables and patches:
                patches = self._apply_variable_substitution(patches, metadata.variables, errors, warnings)
            
            # Determine success based on error level and validation settings
            success = self._determine_success(errors, warnings)
            
            return ParseResult(
                success=success,
                patches=patches,
                metadata=metadata,
                errors=errors,
                warnings=warnings,
                raw_content=raw_data
            )
            
        except yaml.YAMLError as e:
            error_msg = f"YAML syntax error: {e}"
            if hasattr(e, 'problem_mark'):
                mark = e.problem_mark
                error_msg += f" (line {mark.line + 1}, column {mark.column + 1})"
                
            return ParseResult(
                success=False,
                patches=[],
                metadata=PatchMetadata(),
                errors=[ParseError('error', error_msg)],
                warnings=[],
                raw_content={}
            )
        
        except Exception as e:
            logger.error(f"Unexpected error parsing YAML content: {e}")
            return ParseResult(
                success=False,
                patches=[],
                metadata=PatchMetadata(),
                errors=[ParseError('error', f"Unexpected parsing error: {e}")],
                warnings=[],
                raw_content={}
            )
    
    def _extract_metadata(self, data: Dict[str, Any], errors: List[ParseError], warnings: List[ParseError]) -> PatchMetadata:
        """Extract metadata from parsed YAML data."""
        metadata_fields = ['version', 'description', 'author', 'target_formats', 'dependencies', 'variables']
        metadata_data = {}
        
        for field in metadata_fields:
            if field in data:
                metadata_data[field] = data[field]
        
        # Validate target formats if specified
        if 'target_formats' in metadata_data:
            formats = metadata_data['target_formats']
            if not isinstance(formats, list):
                formats = [formats]
            
            invalid_formats = [f for f in formats if f not in self.supported_formats]
            if invalid_formats:
                warnings.append(ParseError(
                    'warning',
                    f"Unsupported target formats: {invalid_formats}. Supported: {list(self.supported_formats)}"
                ))
        
        return PatchMetadata(**metadata_data)
    
    def _extract_patches(self, data: Dict[str, Any], errors: List[ParseError], warnings: List[ParseError]) -> List[Dict[str, Any]]:
        """Extract patch operations from parsed YAML data."""
        patches = []
        
        # Look for patches in various locations
        if 'patches' in data:
            patches_data = data['patches']
        elif 'operations' in data:
            patches_data = data['operations']
        else:
            # Check if the root level itself is a single patch operation
            if isinstance(data, dict) and 'operation' in data:
                patches_data = [data]
            else:
                # Try to find patch operations at root level
                potential_patches = []
                for key, value in data.items():
                    if isinstance(value, dict) and 'operation' in value:
                        potential_patches.append(value)
                    elif isinstance(value, list) and all(isinstance(item, dict) and 'operation' in item for item in value):
                        potential_patches.extend(value)
                
                if potential_patches:
                    patches_data = potential_patches
                else:
                    errors.append(ParseError('error', "No patch operations found in YAML file"))
                    return []
        
        # Normalize patches to list
        if not isinstance(patches_data, list):
            if isinstance(patches_data, dict):
                patches_data = [patches_data]
            else:
                errors.append(ParseError('error', "Patches must be a list or single operation"))
                return []
        
        # Validate each patch operation
        for i, patch in enumerate(patches_data):
            if not isinstance(patch, dict):
                errors.append(ParseError('error', f"Patch {i+1} must be a dictionary"))
                continue
            
            patches.append(patch)
        
        return patches
    
    def _validate_patches(self, patches: List[Dict[str, Any]], errors: List[ParseError], warnings: List[ParseError]) -> None:
        """Validate patch operations against schema."""
        for i, patch in enumerate(patches):
            patch_num = i + 1
            
            # Check for required operation field
            if 'operation' not in patch:
                errors.append(ParseError('error', f"Patch {patch_num}: Missing required 'operation' field"))
                continue
            
            operation = patch['operation']
            if operation not in self.supported_operations:
                errors.append(ParseError(
                    'error',
                    f"Patch {patch_num}: Unsupported operation '{operation}'. Supported: {list(self.supported_operations)}"
                ))
                continue
            
            # Validate against operation-specific schema
            schema = self.operation_schemas.get(operation, {})
            required_fields = schema.get('required', [])
            
            # Check required fields
            for field in required_fields:
                if field not in patch:
                    errors.append(ParseError('error', f"Patch {patch_num}: Missing required field '{field}' for operation '{operation}'"))
            
            # Check target field format
            if 'target' in patch:
                target = patch['target']
                if not isinstance(target, str):
                    errors.append(ParseError('error', f"Patch {patch_num}: Target must be a string XPath expression"))
                elif not target.strip():
                    errors.append(ParseError('error', f"Patch {patch_num}: Target cannot be empty"))
            
            # Operation-specific validation
            self._validate_operation_specific(patch, patch_num, operation, errors, warnings)
    
    def _validate_operation_specific(self, patch: Dict[str, Any], patch_num: int, operation: str, 
                                   errors: List[ParseError], warnings: List[ParseError]) -> None:
        """Perform operation-specific validation."""
        if operation == 'insert':
            # Validate position if specified
            if 'position' in patch:
                position = patch['position']
                valid_positions = ['append', 'prepend', 'before', 'after']
                if position not in valid_positions:
                    errors.append(ParseError(
                        'error',
                        f"Patch {patch_num}: Invalid insert position '{position}'. Valid: {valid_positions}"
                    ))
        
        elif operation == 'extend':
            # Extend operation requires array value
            if 'value' in patch and not isinstance(patch['value'], list):
                warnings.append(ParseError(
                    'warning',
                    f"Patch {patch_num}: Extend operation should have array value"
                ))
        
        elif operation == 'merge':
            # Merge operation should have dictionary value
            if 'value' in patch and not isinstance(patch['value'], dict):
                warnings.append(ParseError(
                    'warning',
                    f"Patch {patch_num}: Merge operation should have dictionary value"
                ))
        
        elif operation == 'relsAdd':
            # Relationship operations need specific fields
            if 'value' in patch:
                value = patch['value']
                if isinstance(value, dict):
                    required_rel_fields = ['Id', 'Type', 'Target']
                    missing_fields = [f for f in required_rel_fields if f not in value]
                    if missing_fields:
                        errors.append(ParseError(
                            'error',
                            f"Patch {patch_num}: relsAdd operation missing required fields: {missing_fields}"
                        ))
    
    def _apply_variable_substitution(self, patches: List[Dict[str, Any]], variables: Dict[str, Any],
                                   errors: List[ParseError], warnings: List[ParseError]) -> List[Dict[str, Any]]:
        """Apply variable substitution to patch operations."""
        try:
            import re
            
            # Variable substitution pattern: ${variable_name}
            var_pattern = re.compile(r'\$\{([^}]+)\}')
            
            def substitute_value(value: Any) -> Any:
                if isinstance(value, str):
                    def replace_var(match):
                        var_name = match.group(1)
                        if var_name in variables:
                            return str(variables[var_name])
                        else:
                            warnings.append(ParseError(
                                'warning',
                                f"Undefined variable: ${{{var_name}}}"
                            ))
                            return match.group(0)  # Return original if not found
                    
                    return var_pattern.sub(replace_var, value)
                elif isinstance(value, dict):
                    return {k: substitute_value(v) for k, v in value.items()}
                elif isinstance(value, list):
                    return [substitute_value(item) for item in value]
                else:
                    return value
            
            # Apply substitution to each patch
            substituted_patches = []
            for patch in patches:
                substituted_patch = substitute_value(patch)
                substituted_patches.append(substituted_patch)
            
            return substituted_patches
            
        except Exception as e:
            errors.append(ParseError('error', f"Variable substitution failed: {e}"))
            return patches
    
    def _determine_success(self, errors: List[ParseError], warnings: List[ParseError]) -> bool:
        """Determine if parsing was successful based on validation level."""
        if self.validation_level == ValidationLevel.STRICT:
            return len(errors) == 0 and len(warnings) == 0
        elif self.validation_level == ValidationLevel.LENIENT:
            return len(errors) == 0
        else:  # PERMISSIVE
            # Only fail on critical errors (syntax errors, missing required fields, invalid operations)
            critical_keywords = ['syntax', 'missing required', 'unsupported operation']
            critical_errors = [e for e in errors if any(keyword in e.message.lower() for keyword in critical_keywords)]
            return len(critical_errors) == 0
    
    def validate_xpath_targets(self, patches: List[Dict[str, Any]]) -> List[ParseError]:
        """
        Validate XPath expressions in patch targets.
        
        Args:
            patches: List of patch operations to validate
            
        Returns:
            List of validation errors found in XPath expressions
        """
        errors = []
        
        try:
            from lxml import etree
            
            for i, patch in enumerate(patches):
                patch_num = i + 1
                
                if 'target' not in patch:
                    continue
                
                target = patch['target']
                try:
                    # Test XPath compilation
                    etree.XPath(target)
                except etree.XPathSyntaxError as e:
                    errors.append(ParseError(
                        'error',
                        f"Patch {patch_num}: Invalid XPath syntax in target '{target}': {e}"
                    ))
                except Exception as e:
                    errors.append(ParseError(
                        'warning',
                        f"Patch {patch_num}: XPath validation warning for target '{target}': {e}"
                    ))
        
        except ImportError:
            # lxml not available - skip XPath validation
            pass
        
        return errors


# Convenience functions for common use cases

def parse_patch_file(file_path: Union[str, Path], validation_level: ValidationLevel = ValidationLevel.LENIENT) -> ParseResult:
    """
    Parse a YAML patch file with specified validation level.
    
    Args:
        file_path: Path to the YAML patch file
        validation_level: Validation strictness level
        
    Returns:
        ParseResult containing parsed patches and validation results
    """
    parser = YAMLPatchParser(validation_level)
    return parser.parse_file(file_path)


def parse_patch_content(content: str, validation_level: ValidationLevel = ValidationLevel.LENIENT) -> ParseResult:
    """
    Parse YAML patch content from string.
    
    Args:
        content: YAML content to parse
        validation_level: Validation strictness level
        
    Returns:
        ParseResult containing parsed patches and validation results
    """
    parser = YAMLPatchParser(validation_level)
    return parser.parse_content(content)