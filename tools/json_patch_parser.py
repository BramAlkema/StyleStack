"""
JSON Patch Parser

This module provides a comprehensive parser for JSON patch files that define 
OOXML template modifications. It validates patch structure, resolves references,
and provides intelligent error reporting.

Part of the StyleStack JSON-to-OOXML Processing Engine.
"""

import json
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
    """Represents a parsing or validation error"""
    level: str  # 'error', 'warning'
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    context: Optional[str] = None


@dataclass
class PatchOperation:
    """Represents a single OOXML patch operation"""
    operation_type: str  # 'set', 'insert', 'remove', 'replace'
    xpath: str
    value: Optional[str] = None
    position: Optional[str] = None  # For insert operations
    condition: Optional[str] = None
    description: Optional[str] = None


@dataclass
class PatchTarget:
    """Represents a target file and its operations"""
    file_path: str
    namespace_map: Dict[str, str]
    operations: List[PatchOperation]


@dataclass  
class ParsedPatch:
    """Complete parsed patch with metadata and targets"""
    metadata: Dict[str, Any]
    targets: List[PatchTarget]
    errors: List[ParseError]
    warnings: List[ParseError]


class JSONPatchParser:
    """Parser for JSON patch files defining OOXML template modifications"""
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.LENIENT):
        self.validation_level = validation_level
        self.errors: List[ParseError] = []
        self.warnings: List[ParseError] = []
    
    def parse_file(self, patch_file: Path) -> ParsedPatch:
        """Parse a JSON patch file"""
        try:
            with open(patch_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return self.parse_patch_data(data, str(patch_file))
        except json.JSONDecodeError as e:
            error = ParseError(
                level='error',
                message=f"Invalid JSON syntax: {e.msg}",
                line=e.lineno,
                column=e.colno,
                context=str(patch_file)
            )
            return ParsedPatch(
                metadata={},
                targets=[],
                errors=[error],
                warnings=[]
            )
        except Exception as e:
            error = ParseError(
                level='error',
                message=f"Failed to read patch file: {str(e)}",
                context=str(patch_file)
            )
            return ParsedPatch(
                metadata={},
                targets=[],
                errors=[error],
                warnings=[]
            )
    
    def parse_content(self, patch_content: str, context: str = "") -> ParsedPatch:
        """Parse patch content from a JSON string"""
        try:
            data = json.loads(patch_content)
            return self.parse_patch_data(data, context)
        except json.JSONDecodeError as e:
            error = ParseError(
                level='error',
                message=f"Invalid JSON syntax: {e.msg}",
                line=e.lineno,
                column=e.colno,
                context=context
            )
            return ParsedPatch(
                metadata={},
                targets=[],
                errors=[error],
                warnings=[]
            )
        except Exception as e:
            error = ParseError(
                level='error',
                message=f"Failed to parse content: {str(e)}",
                context=context
            )
            return ParsedPatch(
                metadata={},
                targets=[],
                errors=[error],
                warnings=[]
            )

    def parse_patch_data(self, data: Dict[str, Any], context: str = "") -> ParsedPatch:
        """Parse patch data from a dictionary"""
        self.errors.clear()
        self.warnings.clear()
        
        # Validate top-level structure
        self._validate_patch_structure(data, context)
        
        # Extract metadata
        metadata = data.get('metadata', {})
        self._validate_metadata(metadata, context)
        
        # Parse targets
        targets = []
        targets_data = data.get('targets', [])
        
        for i, target_data in enumerate(targets_data):
            target = self._parse_target(target_data, f"{context}[targets][{i}]")
            if target:
                targets.append(target)
        
        return ParsedPatch(
            metadata=metadata,
            targets=targets,
            errors=self.errors.copy(),
            warnings=self.warnings.copy()
        )
    
    def _validate_patch_structure(self, data: Dict[str, Any], context: str) -> None:
        """Validate basic patch file structure"""
        required_fields = ['metadata', 'targets']
        
        for field in required_fields:
            if field not in data:
                self._add_error(f"Missing required field '{field}'", context)
        
        # Validate schema reference if present
        if '$schema' in data:
            schema_url = data['$schema']
            if not schema_url.endswith('org-patch.schema.json') and \
               not schema_url.endswith('channel-config.schema.json'):
                self._add_warning(f"Unexpected schema reference: {schema_url}", context)
    
    def _validate_metadata(self, metadata: Dict[str, Any], context: str) -> None:
        """Validate metadata section"""
        if not metadata:
            self._add_error("Empty metadata section", context)
            return
        
        # Check for required metadata fields based on patch type
        if 'org' in metadata or 'organization' in metadata:
            # Organization patch
            required = ['version']
            if 'org' in metadata:
                required.append('org')
            elif 'organization' in metadata:
                required.append('organization')
        elif 'channel' in metadata:
            # Channel patch  
            required = ['channel', 'version']
        else:
            self._add_warning("Patch type unclear from metadata", f"{context}[metadata]")
            required = ['version']
        
        for field in required:
            if field not in metadata:
                self._add_error(f"Missing required metadata field '{field}'", f"{context}[metadata]")
    
    def _parse_target(self, target_data: Dict[str, Any], context: str) -> Optional[PatchTarget]:
        """Parse a single target definition"""
        if not isinstance(target_data, dict):
            self._add_error("Target must be an object", context)
            return None
        
        # Validate required fields
        if 'file' not in target_data:
            self._add_error("Target missing required 'file' field", context)
            return None
        
        if 'ops' not in target_data:
            self._add_error("Target missing required 'ops' field", context)
            return None
        
        file_path = target_data['file']
        namespace_map = target_data.get('ns', {})
        
        # Parse operations
        operations = []
        ops_data = target_data['ops']
        
        if not isinstance(ops_data, list):
            self._add_error("Target 'ops' must be an array", context)
            return None
        
        for i, op_data in enumerate(ops_data):
            op = self._parse_operation(op_data, f"{context}[ops][{i}]")
            if op:
                operations.append(op)
        
        return PatchTarget(
            file_path=file_path,
            namespace_map=namespace_map,
            operations=operations
        )
    
    def _parse_operation(self, op_data: Dict[str, Any], context: str) -> Optional[PatchOperation]:
        """Parse a single patch operation"""
        if not isinstance(op_data, dict):
            self._add_error("Operation must be an object", context)
            return None
        
        # Determine operation type
        op_types = ['set', 'insert', 'remove', 'replace', 'conditional']
        found_ops = [op for op in op_types if op in op_data]
        
        if len(found_ops) == 0:
            self._add_error(f"Operation missing type. Must have one of: {', '.join(op_types)}", context)
            return None
        
        if len(found_ops) > 1:
            self._add_error(f"Operation has multiple types: {', '.join(found_ops)}", context)
            return None
        
        op_type = found_ops[0]
        op_details = op_data[op_type]
        
        # Parse operation details
        if op_type == 'conditional':
            return self._parse_conditional_operation(op_details, context)
        else:
            return self._parse_simple_operation(op_type, op_details, context)
    
    def _parse_simple_operation(self, op_type: str, op_details: Dict[str, Any], context: str) -> Optional[PatchOperation]:
        """Parse a simple (non-conditional) operation"""
        if not isinstance(op_details, dict):
            self._add_error(f"Operation '{op_type}' details must be an object", context)
            return None
        
        # Validate required fields based on operation type
        if op_type in ['set', 'remove']:
            required_fields = ['xpath']
            if op_type == 'set':
                required_fields.append('value')
        elif op_type in ['insert', 'replace']:
            required_fields = ['xpath', 'element'] if op_type == 'replace' else ['xpath', 'element']
        
        for field in required_fields:
            if field not in op_details:
                self._add_error(f"Operation '{op_type}' missing required field '{field}'", context)
                return None
        
        # Extract operation data
        xpath = op_details['xpath']
        value = op_details.get('value') or op_details.get('element')
        position = op_details.get('position')
        condition = op_details.get('condition')
        description = op_details.get('description')
        
        # Validate XPath
        if not xpath or not isinstance(xpath, str):
            self._add_error("XPath expression must be a non-empty string", context)
            return None
        
        return PatchOperation(
            operation_type=op_type,
            xpath=xpath,
            value=value,
            position=position,
            condition=condition,
            description=description
        )
    
    def _parse_conditional_operation(self, op_details: Dict[str, Any], context: str) -> Optional[PatchOperation]:
        """Parse a conditional operation"""
        if not isinstance(op_details, dict):
            self._add_error("Conditional operation details must be an object", context)
            return None
        
        if 'condition' not in op_details:
            self._add_error("Conditional operation missing 'condition' field", context)
            return None
        
        if 'then' not in op_details:
            self._add_error("Conditional operation missing 'then' field", context)
            return None
        
        # For now, return a simplified representation
        # Full conditional logic would require more complex parsing
        condition = op_details['condition']
        
        return PatchOperation(
            operation_type='conditional',
            xpath='',  # Will be determined from 'then' operation
            condition=condition,
            description=f"Conditional: {condition}"
        )
    
    def _add_error(self, message: str, context: str) -> None:
        """Add an error to the error list"""
        error = ParseError(
            level='error',
            message=message,
            context=context
        )
        self.errors.append(error)
    
    def _add_warning(self, message: str, context: str) -> None:
        """Add a warning to the warning list"""
        warning = ParseError(
            level='warning',
            message=message,
            context=context
        )
        self.warnings.append(warning)
    
    def has_errors(self) -> bool:
        """Check if parsing resulted in errors"""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if parsing resulted in warnings"""  
        return len(self.warnings) > 0


def parse_json_patch_file(file_path: Path, validation_level: ValidationLevel = ValidationLevel.LENIENT) -> ParsedPatch:
    """Convenience function to parse a JSON patch file"""
    parser = JSONPatchParser(validation_level)
    return parser.parse_file(file_path)