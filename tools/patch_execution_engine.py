"""
Patch Execution Engine

This module provides the core execution engine that orchestrates the application
of JSON patches to OOXML documents. It coordinates between the JSON parser and
patch processor, handles sequencing, dependencies, and execution context.

Part of the StyleStack JSON-to-OOXML Processing Engine.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import logging
from copy import deepcopy
import time

from lxml import etree
from .json_patch_parser import JSONPatchParser, ParsedPatch, ValidationLevel, PatchTarget
from .core.types import PatchResult, PatchOperationType
from .ooxml_processor import OOXMLProcessor as PatchProcessor

# Configure logging
logger = logging.getLogger(__name__)


class PatchErrorCode(Enum):
    """Error codes for patch execution engine."""
    INVALID_PATCH = 6001
    UNSUPPORTED_OPERATION = 6002


class StyleStackError(Exception):
    """Base exception with error codes for StyleStack."""
    def __init__(self, message: str, error_code: int, context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        super().__init__(f"[E{error_code:04d}] {message}")


class ExecutionMode(Enum):
    """Execution modes for patch application."""
    NORMAL = "normal"          # Apply patches to document
    DRY_RUN = "dry_run"       # Validate patches without applying
    VALIDATE_ONLY = "validate_only"  # Only validate patches and targets


@dataclass
class ExecutionContext:
    """Shared execution context for patch operations."""
    variables: Dict[str, Any] = field(default_factory=dict)
    applied_patches: List[Dict[str, Any]] = field(default_factory=list)
    execution_stats: Dict[str, Any] = field(default_factory=dict)
    document_cache: Dict[str, etree._Element] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize execution statistics."""
        if not self.execution_stats:
            self.execution_stats = {
                'start_time': None,
                'end_time': None,
                'total_patches': 0,
                'successful_patches': 0,
                'failed_patches': 0,
                'warnings_count': 0,
                'execution_time': 0.0
            }


@dataclass
class ExecutionResult:
    """Result of patch execution."""
    success: bool
    modified_document: Optional[etree._Element]
    patch_results: List[PatchResult]
    execution_context: ExecutionContext
    errors: List[str]
    warnings: List[str]
    execution_time: float
    dry_run: bool = False


@dataclass 
class BatchExecutionResult:
    """Result of executing multiple patch files."""
    success: bool
    results: List[ExecutionResult]
    total_patches: int
    successful_patches: int
    failed_patches: int
    total_execution_time: float


class PatchExecutionEngine:
    """
    Core execution engine for applying JSON patches to OOXML documents.
    
    Features:
    - Sequential patch application with dependency resolution
    - Dry-run capability for testing patches
    - Shared execution context with variables and caching
    - Batch processing of multiple patch files
    - Comprehensive error handling and rollback
    - Performance monitoring and statistics
    """
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.LENIENT):
        """Initialize the execution engine."""
        self.parser = JSONPatchParser(validation_level)
        self.processor = PatchProcessor()
        self.validation_level = validation_level
        
        # Execution callbacks
        self.pre_patch_callbacks: List[Callable] = []
        self.post_patch_callbacks: List[Callable] = []
        self.progress_callback: Optional[Callable] = None
        
        # Global execution statistics
        self.global_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'total_patches_processed': 0,
            'average_execution_time': 0.0
        }
    
    def execute_patch_file(self, 
                          patch_file: Union[str, Path],
                          xml_document: etree._Element,
                          mode: ExecutionMode = ExecutionMode.NORMAL,
                          context: Optional[ExecutionContext] = None) -> ExecutionResult:
        """
        Execute a JSON patch file against an OOXML document.
        
        Args:
            patch_file: Path to the JSON patch file
            xml_document: Target OOXML document element
            mode: Execution mode (normal, dry_run, validate_only)
            context: Shared execution context (optional)
            
        Returns:
            ExecutionResult containing success status and details
        """
        start_time = time.time()
        errors = []
        warnings = []
        
        # Initialize context if not provided
        if context is None:
            context = ExecutionContext()
        
        context.execution_stats['start_time'] = start_time
        
        try:
            # Parse the patch file
            logger.info(f"Parsing patch file: {patch_file}")
            parse_result = self.parser.parse_file(patch_file)

            if parse_result.errors:
                if self.validation_level == ValidationLevel.STRICT:
                    raise StyleStackError(
                        "Invalid patch file",
                        PatchErrorCode.INVALID_PATCH.value,
                        {"errors": [error.message for error in parse_result.errors]}
                    )
                errors.extend([error.message for error in parse_result.errors])
                warnings.extend([warning.message for warning in parse_result.warnings])
                return self._create_failed_result(xml_document, context, errors, warnings, time.time() - start_time, mode == ExecutionMode.DRY_RUN)
            
            # Add any parse warnings
            warnings.extend([warning.message for warning in parse_result.warnings])
            
            # Update context with metadata and variables
            self._update_context_from_metadata(context, parse_result)
            
            # Apply additional variable substitution from shared context
            patches = self._resolve_context_variables(parse_result.targets, context)
            
            # Execute patches
            return self._execute_patches(
                patches,
                xml_document,
                mode,
                context,
                errors,
                warnings,
                start_time
            )
            
        except StyleStackError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing patch file {patch_file}: {e}")
            errors.append(f"Execution error: {e}")
            return self._create_failed_result(xml_document, context, errors, warnings, time.time() - start_time, mode == ExecutionMode.DRY_RUN)
    
    def execute_patch_content(self,
                             patch_content: str,
                             xml_document: etree._Element,
                             mode: ExecutionMode = ExecutionMode.NORMAL,
                             context: Optional[ExecutionContext] = None) -> ExecutionResult:
        """
        Execute JSON patch content against an OOXML document.
        
        Args:
            patch_content: JSON patch content as string
            xml_document: Target OOXML document element
            mode: Execution mode (normal, dry_run, validate_only)
            context: Shared execution context (optional)
            
        Returns:
            ExecutionResult containing success status and details
        """
        start_time = time.time()
        errors = []
        warnings = []
        
        # Initialize context if not provided
        if context is None:
            context = ExecutionContext()
        
        context.execution_stats['start_time'] = start_time
        
        try:
            # Parse the patch content
            logger.info("Parsing patch content")
            parse_result = self.parser.parse_content(patch_content)

            if parse_result.errors:
                if self.validation_level == ValidationLevel.STRICT:
                    raise StyleStackError(
                        "Invalid patch content",
                        PatchErrorCode.INVALID_PATCH.value,
                        {"errors": [error.message for error in parse_result.errors]}
                    )
                errors.extend([error.message for error in parse_result.errors])
                warnings.extend([warning.message for warning in parse_result.warnings])
                return self._create_failed_result(xml_document, context, errors, warnings, time.time() - start_time, mode == ExecutionMode.DRY_RUN)
            
            # Add any parse warnings
            warnings.extend([warning.message for warning in parse_result.warnings])
            
            # Update context with metadata and variables
            self._update_context_from_metadata(context, parse_result)
            
            # Apply additional variable substitution from shared context
            patches = self._resolve_context_variables(parse_result.targets, context)
            
            # Execute patches
            return self._execute_patches(
                patches,
                xml_document,
                mode,
                context,
                errors,
                warnings,
                start_time
            )
            
        except StyleStackError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing patch content: {e}")
            errors.append(f"Execution error: {e}")
            return self._create_failed_result(xml_document, context, errors, warnings, time.time() - start_time, mode == ExecutionMode.DRY_RUN)
    
    def execute_batch(self,
                     patch_files: List[Union[str, Path]],
                     xml_document: etree._Element,
                     mode: ExecutionMode = ExecutionMode.NORMAL,
                     shared_context: bool = True) -> BatchExecutionResult:
        """
        Execute multiple patch files in sequence.
        
        Args:
            patch_files: List of patch file paths
            xml_document: Target OOXML document element
            mode: Execution mode for all patches
            shared_context: Whether to share context between patches
            
        Returns:
            BatchExecutionResult containing results for all patches
        """
        start_time = time.time()
        results = []
        context = ExecutionContext() if shared_context else None
        
        total_patches = 0
        successful_patches = 0
        failed_patches = 0
        
        logger.info(f"Starting batch execution of {len(patch_files)} patch files")
        
        for i, patch_file in enumerate(patch_files):
            logger.info(f"Processing patch file {i+1}/{len(patch_files)}: {patch_file}")
            
            # Create new context for each file if not sharing
            file_context = context if shared_context else ExecutionContext()
            
            # Execute the patch file
            result = self.execute_patch_file(patch_file, xml_document, mode, file_context)
            results.append(result)
            
            # Update statistics
            patch_count = len(result.patch_results)
            total_patches += patch_count
            
            if result.success:
                successful_patches += patch_count
            else:
                failed_patches += patch_count
            
            # Update shared context if using shared context
            if shared_context:
                context = result.execution_context
            
            # Update progress callback if provided
            if self.progress_callback:
                self.progress_callback(i + 1, len(patch_files), patch_file, result.success)
            
            # If this execution failed and we're not in dry-run mode, consider stopping
            if not result.success and mode != ExecutionMode.DRY_RUN:
                logger.warning(f"Patch file {patch_file} failed, continuing with remaining files")
        
        total_time = time.time() - start_time
        overall_success = all(result.success for result in results)
        
        logger.info(f"Batch execution completed in {total_time:.2f}s. Success: {overall_success}")
        
        return BatchExecutionResult(
            success=overall_success,
            results=results,
            total_patches=total_patches,
            successful_patches=successful_patches,
            failed_patches=failed_patches,
            total_execution_time=total_time
        )
    
    def _execute_patches(self,
                        patches: List[Dict[str, Any]],
                        xml_document: etree._Element,
                        mode: ExecutionMode,
                        context: ExecutionContext,
                        errors: List[str],
                        warnings: List[str],
                        start_time: float) -> ExecutionResult:
        """Execute a list of patches against the document."""
        patch_results = []
        working_document = deepcopy(xml_document) if mode != ExecutionMode.VALIDATE_ONLY else xml_document
        
        context.execution_stats['total_patches'] = len(patches)
        
        # Validate-only mode: just check patches without applying
        if mode == ExecutionMode.VALIDATE_ONLY:
            return self._validate_patches_only(patches, xml_document, context, errors, warnings, start_time)
        
        logger.info(f"Executing {len(patches)} patches in {mode.value} mode")

        supported_ops = {op.value for op in PatchOperationType}

        for i, patch in enumerate(patches):
            logger.debug(f"Executing patch {i+1}/{len(patches)}: {patch.get('operation', 'unknown')}")

            operation = patch.get('operation')
            target = patch.get('target')
            value = patch.get('value')

            if not operation or not target or value is None:
                raise StyleStackError(
                    f"Invalid patch structure at index {i}",
                    PatchErrorCode.INVALID_PATCH.value
                )

            if operation not in supported_ops:
                raise StyleStackError(
                    f"Unsupported operation: {operation}",
                    PatchErrorCode.UNSUPPORTED_OPERATION.value
                )
            
            # Execute pre-patch callbacks
            for callback in self.pre_patch_callbacks:
                try:
                    callback(patch, context)
                except Exception as e:
                    logger.warning(f"Pre-patch callback failed: {e}")
            
            # Apply the patch
            if mode == ExecutionMode.DRY_RUN:
                # In dry-run mode, work on a copy for each patch
                test_document = deepcopy(working_document)
                result = self.processor.apply_patch(test_document, patch)
            else:
                # Normal mode: apply to working document
                result = self.processor.apply_patch(working_document, patch)
            
            patch_results.append(result)
            
            # Update context and statistics
            if result.success:
                context.execution_stats['successful_patches'] += 1
                context.applied_patches.append(patch)
                logger.debug(f"Patch {i+1} succeeded: {result.message}")
            else:
                context.execution_stats['failed_patches'] += 1
                errors.append(f"Patch {i+1} failed: {result.message}")
                logger.warning(f"Patch {i+1} failed: {result.message}")
            
            # Execute post-patch callbacks
            for callback in self.post_patch_callbacks:
                try:
                    callback(patch, result, context)
                except Exception as e:
                    logger.warning(f"Post-patch callback failed: {e}")
        
        # Finalize execution
        execution_time = time.time() - start_time
        context.execution_stats['end_time'] = time.time()
        context.execution_stats['execution_time'] = execution_time
        
        # Determine overall success
        success = all(result.success for result in patch_results)
        
        # Update global statistics
        self._update_global_stats(len(patches), success, execution_time)
        
        return ExecutionResult(
            success=success,
            modified_document=working_document if mode == ExecutionMode.NORMAL else None,
            patch_results=patch_results,
            execution_context=context,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time,
            dry_run=(mode == ExecutionMode.DRY_RUN)
        )
    
    def _validate_patches_only(self,
                              patches: List[Dict[str, Any]],
                              xml_document: etree._Element,
                              context: ExecutionContext,
                              errors: List[str],
                              warnings: List[str],
                              start_time: float) -> ExecutionResult:
        """Validate patches without applying them."""
        patch_results = []
        
        logger.info(f"Validating {len(patches)} patches (no application)")

        supported_ops = {op.value for op in PatchOperationType}

        for i, patch in enumerate(patches):
            operation = patch.get('operation')
            target = patch.get('target')
            value = patch.get('value')

            if not operation or not target or value is None:
                raise StyleStackError(
                    f"Invalid patch structure at index {i}",
                    PatchErrorCode.INVALID_PATCH.value
                )

            if operation not in supported_ops:
                raise StyleStackError(
                    f"Unsupported operation: {operation}",
                    PatchErrorCode.UNSUPPORTED_OPERATION.value
                )

            # Create a mock result for validation
            try:
                # Try to validate XPath target
                context_info = self.processor.xpath_system.get_xpath_context_info(xml_document, target)
                if context_info.get('is_valid_syntax', False) and 'error' not in context_info:
                    result = PatchResult(True, operation, target, f"Patch {i+1}: Validation passed", 0)
                else:
                    error_msg = context_info.get('error', 'Invalid XPath syntax or no matches found')
                    result = PatchResult(False, operation, target, f"Patch {i+1}: {error_msg}")
            except Exception as e:
                result = PatchResult(False, operation, target, f"Patch {i+1}: XPath validation error: {e}")

            patch_results.append(result)

            if result.success:
                context.execution_stats['successful_patches'] += 1
            else:
                context.execution_stats['failed_patches'] += 1
                errors.append(result.message)
        
        execution_time = time.time() - start_time
        context.execution_stats['execution_time'] = execution_time
        success = all(result.success for result in patch_results)
        
        return ExecutionResult(
            success=success,
            modified_document=None,
            patch_results=patch_results,
            execution_context=context,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time,
            dry_run=False
        )
    
    def _update_context_from_metadata(self, context: ExecutionContext, parse_result: ParsedPatch) -> None:
        """Update execution context with metadata from parsed patches."""
        if parse_result.metadata:
            # Add metadata variables to context
            if 'variables' in parse_result.metadata:
                context.variables.update(parse_result.metadata['variables'])
            
            # Store metadata for reference
            context.metadata.update({
                'version': parse_result.metadata.get('version'),
                'description': parse_result.metadata.get('description'),
                'author': parse_result.metadata.get('author'),
                'target_formats': parse_result.metadata.get('target_formats'),
                'dependencies': parse_result.metadata.get('dependencies')
            })
    
    def _resolve_context_variables(self, targets: List[PatchTarget], context: ExecutionContext) -> List[PatchTarget]:
        """Apply variable substitution from execution context to patches."""
        if not context.variables:
            return targets
        
        try:
            import re
            
            # Variable substitution pattern: ${variable_name}
            var_pattern = re.compile(r'\$\{([^}]+)\}')
            
            def substitute_value(value: Any) -> Any:
                if isinstance(value, str):
                    def replace_var(match):
                        var_name = match.group(1)
                        if var_name in context.variables:
                            return str(context.variables[var_name])
                        else:
                            # Keep original if not found in context
                            return match.group(0)
                    
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
            logger.warning(f"Context variable substitution failed: {e}")
            return patches
    
    def _create_failed_result(self,
                             xml_document: etree._Element,
                             context: ExecutionContext,
                             errors: List[str],
                             warnings: List[str],
                             execution_time: float,
                             dry_run: bool) -> ExecutionResult:
        """Create a failed execution result."""
        context.execution_stats['end_time'] = time.time()
        context.execution_stats['execution_time'] = execution_time
        
        return ExecutionResult(
            success=False,
            modified_document=None,
            patch_results=[],
            execution_context=context,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time,
            dry_run=dry_run
        )
    
    def _update_global_stats(self, patch_count: int, success: bool, execution_time: float) -> None:
        """Update global execution statistics."""
        self.global_stats['total_executions'] += 1
        self.global_stats['total_patches_processed'] += patch_count
        
        if success:
            self.global_stats['successful_executions'] += 1
        
        # Update average execution time
        total_execs = self.global_stats['total_executions']
        current_avg = self.global_stats['average_execution_time']
        self.global_stats['average_execution_time'] = ((current_avg * (total_execs - 1)) + execution_time) / total_execs
    
    def add_pre_patch_callback(self, callback: Callable[[Dict[str, Any], ExecutionContext], None]) -> None:
        """Add a callback to execute before each patch."""
        self.pre_patch_callbacks.append(callback)
    
    def add_post_patch_callback(self, callback: Callable[[Dict[str, Any], PatchResult, ExecutionContext], None]) -> None:
        """Add a callback to execute after each patch."""
        self.post_patch_callbacks.append(callback)
    
    def set_progress_callback(self, callback: Callable[[int, int, str, bool], None]) -> None:
        """Set a progress callback for batch operations."""
        self.progress_callback = callback
    
    def get_global_statistics(self) -> Dict[str, Any]:
        """Get global execution statistics."""
        return dict(self.global_stats)
    
    def reset_global_statistics(self) -> None:
        """Reset global execution statistics."""
        self.global_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'total_patches_processed': 0,
            'average_execution_time': 0.0
        }


# Convenience functions for common use cases

def execute_patch_file(patch_file: Union[str, Path],
                      xml_document: etree._Element,
                      mode: ExecutionMode = ExecutionMode.NORMAL,
                      validation_level: ValidationLevel = ValidationLevel.LENIENT) -> ExecutionResult:
    """
    Execute a patch file against an OOXML document.
    
    Args:
        patch_file: Path to the JSON patch file
        xml_document: Target OOXML document element
        mode: Execution mode
        validation_level: Validation strictness level
        
    Returns:
        ExecutionResult containing success status and details
    """
    engine = PatchExecutionEngine(validation_level)
    return engine.execute_patch_file(patch_file, xml_document, mode)


def execute_patch_content(patch_content: str,
                         xml_document: etree._Element,
                         mode: ExecutionMode = ExecutionMode.NORMAL,
                         validation_level: ValidationLevel = ValidationLevel.LENIENT) -> ExecutionResult:
    """
    Execute patch content against an OOXML document.
    
    Args:
        patch_content: JSON patch content as string
        xml_document: Target OOXML document element
        mode: Execution mode
        validation_level: Validation strictness level
        
    Returns:
        ExecutionResult containing success status and details
    """
    engine = PatchExecutionEngine(validation_level)
    return engine.execute_patch_content(patch_content, xml_document, mode)
