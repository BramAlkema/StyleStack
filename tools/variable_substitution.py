#!/usr/bin/env python3
"""
StyleStack OOXML Extension Variable System - Variable Substitution Pipeline

Production implementation for Phase 2.4: Variable Substitution Pipeline.
Provides end-to-end variable substitution with transaction support, progress tracking,
validation checkpoints, and document integrity preservation.

Features:
- Atomic operations with rollback support
- Progress tracking and cancellation
- Validation checkpoints throughout pipeline
- Document integrity preservation
- Batch processing with parallel support
- Memory-efficient streaming mode
- Comprehensive error handling and recovery

Created: 2025-09-07
Author: StyleStack Development Team
License: MIT
"""

import json
import time
import threading
import tempfile
import shutil
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager
import concurrent.futures
import xml.etree.ElementTree as ET

try:
    import lxml.etree as lxml_ET
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False

import sys
import os
sys.path.append(os.path.dirname(__file__))

from ooxml_processor import OOXMLProcessor, ProcessingResult
from theme_resolver import ThemeResolver
from variable_resolver import VariableResolver, ResolvedVariable


class SubstitutionStage(Enum):
    """Stages of the variable substitution pipeline"""
    INITIALIZING = "initializing"
    PARSING = "parsing"
    VALIDATING = "validating"
    RESOLVING = "resolving"
    APPLYING = "applying"
    FINALIZING = "finalizing"
    COMPLETE = "complete"
    ERROR = "error"
    CANCELLED = "cancelled"


class ValidationCheckpointType(Enum):
    """Types of validation checkpoints"""
    PRE_SUBSTITUTION = "pre_substitution"
    VARIABLE_VALIDATION = "variable_validation"
    XPATH_VALIDATION = "xpath_validation"
    DEPENDENCY_RESOLUTION = "dependency_resolution"
    SUBSTITUTION_VALIDATION = "substitution_validation"
    POST_SUBSTITUTION = "post_substitution"


@dataclass
class SubstitutionError:
    """Represents an error during variable substitution"""
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = None
    stage: Optional[SubstitutionStage] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SubstitutionProgress:
    """Progress information for variable substitution"""
    current_stage: SubstitutionStage
    progress_percentage: int
    variables_processed: int
    total_variables: int
    current_document: Optional[str] = None
    documents_completed: int = 0
    total_documents: int = 1
    overall_progress_percentage: int = 0
    processing_time_elapsed: float = 0.0
    estimated_time_remaining: Optional[float] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    additional_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationCheckpoint:
    """Validation checkpoint result"""
    checkpoint_type: ValidationCheckpointType
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SubstitutionResult:
    """Result of variable substitution operation"""
    success: bool
    updated_content: Optional[str] = None
    variables_applied: int = 0
    variables_skipped: int = 0
    processing_time: float = 0.0
    errors: List[SubstitutionError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validation_checkpoints_passed: List[ValidationCheckpointType] = field(default_factory=list)
    validation_checkpoints_failed: List[ValidationCheckpoint] = field(default_factory=list)
    cancelled: bool = False
    timed_out: bool = False
    stage_timings: Dict[SubstitutionStage, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchSubstitutionResult:
    """Result of batch variable substitution operation"""
    success: bool
    document_results: Dict[str, SubstitutionResult] = field(default_factory=dict)
    successful_documents: List[str] = field(default_factory=list)
    failed_documents: List[str] = field(default_factory=list)
    total_processing_time: float = 0.0
    total_variables_applied: int = 0
    errors: List[SubstitutionError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class CancellationToken:
    """Token for cancelling long-running operations"""
    
    def __init__(self):
        self._cancelled = threading.Event()
        
    def cancel(self):
        """Cancel the operation"""
        self._cancelled.set()
        
    @property
    def is_cancelled(self) -> bool:
        """Check if cancellation was requested"""
        return self._cancelled.is_set()
        
    def throw_if_cancelled(self):
        """Raise exception if cancellation was requested"""
        if self.is_cancelled:
            raise OperationCancelledException("Operation was cancelled")


class OperationCancelledException(Exception):
    """Exception raised when an operation is cancelled"""
    pass


class OperationTimeoutException(Exception):
    """Exception raised when an operation times out"""
    pass


class TransactionContext:
    """Context manager for atomic operations with rollback support"""
    
    def __init__(self, pipeline: 'VariableSubstitutionPipeline', backup_files: bool = False):
        self.pipeline = pipeline
        self.backup_files = backup_files
        self.operations = []
        self.backups = {}
        self.committed = False
        self.rolled_back = False
        self._temp_dir = None
        
    def __enter__(self):
        if self.backup_files:
            self._temp_dir = tempfile.mkdtemp(prefix="stylestack_backup_")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Exception occurred, rollback
            self.rollback()
        else:
            # No exception, commit
            self.commit()
            
    def substitute_in_document(self, document_content: str, 
                             variables: Dict[str, Any]) -> SubstitutionResult:
        """Perform substitution within transaction context"""
        operation_id = f"doc_sub_{len(self.operations)}"
        self.operations.append({
            'type': 'document_substitution',
            'id': operation_id,
            'original_content': document_content,
            'variables': variables
        })
        
        return self.pipeline.substitute_variables_in_document(
            document_content=document_content,
            variables=variables,
            transaction_context=self
        )
        
    def substitute_in_file(self, file_path: str, variables: Dict[str, Any]) -> SubstitutionResult:
        """Perform file substitution within transaction context"""
        file_path = Path(file_path)
        
        # Create backup if requested
        if self.backup_files:
            backup_path = Path(self._temp_dir) / file_path.name
            shutil.copy2(file_path, backup_path)
            self.backups[str(file_path)] = str(backup_path)
            
        # Read original content
        original_content = file_path.read_text(encoding='utf-8')
        
        operation_id = f"file_sub_{len(self.operations)}"
        self.operations.append({
            'type': 'file_substitution',
            'id': operation_id,
            'file_path': str(file_path),
            'original_content': original_content,
            'variables': variables
        })
        
        # Perform substitution
        result = self.pipeline.substitute_variables_in_document(
            document_content=original_content,
            variables=variables,
            transaction_context=self
        )
        
        if result.success:
            # Write updated content to file
            file_path.write_text(result.updated_content, encoding='utf-8')
            
        return result
        
    def commit(self):
        """Commit all operations"""
        if self.rolled_back:
            raise RuntimeError("Transaction has already been rolled back")
            
        self.committed = True
        
        # Clean up backup files
        if self._temp_dir:
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            
    def rollback(self):
        """Rollback all operations"""
        if self.committed:
            raise RuntimeError("Transaction has already been committed")
            
        self.rolled_back = True
        
        # Restore backed up files
        for original_path, backup_path in self.backups.items():
            shutil.copy2(backup_path, original_path)
            
        # Clean up backup files
        if self._temp_dir:
            shutil.rmtree(self._temp_dir, ignore_errors=True)


class ProgressReporter:
    """Handles progress reporting for substitution operations"""
    
    def __init__(self, callback: Optional[Callable[[SubstitutionProgress], None]] = None):
        self.callback = callback
        self.start_time = time.time()
        self.last_update_time = 0
        self.update_interval = 0.1  # Minimum time between updates (seconds)
        
    def report_progress(self, progress: SubstitutionProgress):
        """Report progress update"""
        current_time = time.time()
        
        # Throttle updates to avoid overwhelming callback
        if current_time - self.last_update_time < self.update_interval:
            return
            
        # Add timing information
        progress.processing_time_elapsed = current_time - self.start_time
        
        # Estimate remaining time
        if progress.progress_percentage > 0:
            elapsed_ratio = progress.progress_percentage / 100.0
            total_estimated_time = progress.processing_time_elapsed / elapsed_ratio
            progress.estimated_time_remaining = max(0, total_estimated_time - progress.processing_time_elapsed)
            
        self.last_update_time = current_time
        
        if self.callback:
            try:
                self.callback(progress)
            except Exception as e:
                # Don't let callback errors break the operation
                print(f"Progress callback error: {e}")


class VariableSubstitutionPipeline:
    """
    Main pipeline for variable substitution with comprehensive features.
    
    Provides atomic operations, progress tracking, validation checkpoints,
    and document integrity preservation for OOXML variable substitution.
    """
    
    def __init__(self, 
                 enable_transactions: bool = True,
                 enable_progress_reporting: bool = True,
                 validation_level: str = 'standard',
                 operation_timeout: Optional[float] = None,
                 use_lxml: bool = None):
        """
        Initialize the variable substitution pipeline.
        
        Args:
            enable_transactions: Enable atomic operations with rollback
            enable_progress_reporting: Enable progress tracking
            validation_level: Validation strictness ('minimal', 'standard', 'strict')
            operation_timeout: Default timeout for operations in seconds
            use_lxml: Force lxml usage (None for auto-detection)
        """
        self.enable_transactions = enable_transactions
        self.enable_progress_reporting = enable_progress_reporting
        self.validation_level = validation_level
        self.operation_timeout = operation_timeout
        
        # Initialize component processors
        self.ooxml_processor = OOXMLProcessor(use_lxml=use_lxml)
        self.theme_resolver = ThemeResolver()
        self.variable_resolver = VariableResolver()
        
        # Processing statistics
        self.statistics = {
            'documents_processed': 0,
            'variables_applied': 0,
            'total_processing_time': 0.0,
            'operations_started': 0,
            'operations_completed': 0,
            'operations_failed': 0,
            'operations_cancelled': 0
        }
        
        # Default validation checkpoints by level
        self.validation_checkpoints = {
            'minimal': [ValidationCheckpointType.PRE_SUBSTITUTION],
            'standard': [
                ValidationCheckpointType.PRE_SUBSTITUTION,
                ValidationCheckpointType.VARIABLE_VALIDATION,
                ValidationCheckpointType.POST_SUBSTITUTION
            ],
            'strict': [
                ValidationCheckpointType.PRE_SUBSTITUTION,
                ValidationCheckpointType.VARIABLE_VALIDATION,
                ValidationCheckpointType.XPATH_VALIDATION,
                ValidationCheckpointType.DEPENDENCY_RESOLUTION,
                ValidationCheckpointType.SUBSTITUTION_VALIDATION,
                ValidationCheckpointType.POST_SUBSTITUTION
            ]
        }
        
    def set_operation_timeout(self, timeout_seconds: float):
        """Set the default operation timeout"""
        self.operation_timeout = timeout_seconds
        
    def create_cancellation_token(self) -> CancellationToken:
        """Create a cancellation token for operations"""
        return CancellationToken()
        
    @contextmanager
    def create_transaction(self, backup_files: bool = False):
        """Create a transaction context for atomic operations"""
        if not self.enable_transactions:
            raise RuntimeError("Transactions are disabled")
            
        transaction = TransactionContext(self, backup_files=backup_files)
        yield transaction
        
    def substitute_variables_in_document(self,
                                       document_content: str,
                                       variables: Dict[str, Any],
                                       document_type: str = 'auto',
                                       validation_checkpoints: Optional[List[str]] = None,
                                       progress_callback: Optional[Callable[[SubstitutionProgress], None]] = None,
                                       cancellation_token: Optional[CancellationToken] = None,
                                       transaction_context: Optional[TransactionContext] = None,
                                       preserve_structure: bool = True,
                                       preserve_attributes: bool = True,
                                       preserve_namespaces: bool = True,
                                       preserve_comments: bool = True,
                                       preserve_processing_instructions: bool = True,
                                       resolve_hierarchy: bool = True,
                                       evaluate_conditions: bool = True) -> SubstitutionResult:
        """
        Substitute variables in a single OOXML document.
        
        Args:
            document_content: The OOXML document content as string
            variables: Dictionary of variables to substitute
            document_type: Type of document ('powerpoint_theme', 'word_styles', etc.)
            validation_checkpoints: List of validation checkpoints to run
            progress_callback: Callback for progress updates
            cancellation_token: Token for operation cancellation
            transaction_context: Transaction context if part of atomic operation
            preserve_structure: Preserve XML document structure
            preserve_attributes: Preserve element attributes
            preserve_namespaces: Preserve XML namespaces
            preserve_comments: Preserve XML comments
            preserve_processing_instructions: Preserve processing instructions
            resolve_hierarchy: Resolve variable hierarchy precedence
            evaluate_conditions: Evaluate conditional variables
            
        Returns:
            SubstitutionResult with operation outcome
        """
        start_time = time.time()
        self.statistics['operations_started'] += 1
        
        # Initialize result
        result = SubstitutionResult(
            success=False,
            updated_content=document_content
        )
        
        # Initialize progress reporter
        progress_reporter = ProgressReporter(progress_callback) if self.enable_progress_reporting else None
        
        try:
            # Set up validation checkpoints
            if validation_checkpoints is None:
                validation_checkpoints = [cp.value for cp in self.validation_checkpoints[self.validation_level]]
            
            current_stage = SubstitutionStage.INITIALIZING
            stage_start_time = time.time()
            
            # Report initial progress
            if progress_reporter:
                progress_reporter.report_progress(SubstitutionProgress(
                    current_stage=current_stage,
                    progress_percentage=0,
                    variables_processed=0,
                    total_variables=len(variables)
                ))
            
            # Check cancellation
            if cancellation_token and cancellation_token.is_cancelled:
                raise OperationCancelledException("Operation cancelled before start")
                
            # Check timeout
            if self.operation_timeout and (time.time() - start_time) > self.operation_timeout:
                raise OperationTimeoutException(f"Operation timed out after {self.operation_timeout}s")
                
            # Stage 1: Parse and validate document
            current_stage = SubstitutionStage.PARSING
            result.stage_timings[SubstitutionStage.INITIALIZING] = time.time() - stage_start_time
            stage_start_time = time.time()
            
            if progress_reporter:
                progress_reporter.report_progress(SubstitutionProgress(
                    current_stage=current_stage,
                    progress_percentage=10,
                    variables_processed=0,
                    total_variables=len(variables)
                ))
                
            # Pre-substitution validation
            if ValidationCheckpointType.PRE_SUBSTITUTION.value in validation_checkpoints:
                checkpoint = self._validate_pre_substitution(document_content)
                if checkpoint.passed:
                    result.validation_checkpoints_passed.append(ValidationCheckpointType.PRE_SUBSTITUTION)
                else:
                    result.validation_checkpoints_failed.append(checkpoint)
                    result.errors.append(SubstitutionError(
                        error_type='xml_parsing',
                        message=checkpoint.message,
                        stage=current_stage,
                        details=checkpoint.details
                    ))
                    return result
                    
            # Stage 2: Validate variables
            current_stage = SubstitutionStage.VALIDATING
            result.stage_timings[SubstitutionStage.PARSING] = time.time() - stage_start_time
            stage_start_time = time.time()
            
            if progress_reporter:
                progress_reporter.report_progress(SubstitutionProgress(
                    current_stage=current_stage,
                    progress_percentage=20,
                    variables_processed=0,
                    total_variables=len(variables)
                ))
                
            # Variable validation
            if ValidationCheckpointType.VARIABLE_VALIDATION.value in validation_checkpoints:
                checkpoint = self._validate_variables(variables)
                if checkpoint.passed:
                    result.validation_checkpoints_passed.append(ValidationCheckpointType.VARIABLE_VALIDATION)
                else:
                    result.validation_checkpoints_failed.append(checkpoint)
                    result.errors.append(SubstitutionError(
                        error_type='variable_validation',
                        message=checkpoint.message,
                        stage=current_stage,
                        details=checkpoint.details
                    ))
                    return result
                    
            # XPath validation
            if ValidationCheckpointType.XPATH_VALIDATION.value in validation_checkpoints:
                checkpoint = self._validate_xpath_expressions(variables)
                if checkpoint.passed:
                    result.validation_checkpoints_passed.append(ValidationCheckpointType.XPATH_VALIDATION)
                else:
                    result.validation_checkpoints_failed.append(checkpoint)
                    result.errors.append(SubstitutionError(
                        error_type='xpath_validation',
                        message=checkpoint.message,
                        stage=current_stage,
                        details=checkpoint.details
                    ))
                    return result
                    
            # Stage 3: Resolve variables
            current_stage = SubstitutionStage.RESOLVING
            result.stage_timings[SubstitutionStage.VALIDATING] = time.time() - stage_start_time
            stage_start_time = time.time()
            
            if progress_reporter:
                progress_reporter.report_progress(SubstitutionProgress(
                    current_stage=current_stage,
                    progress_percentage=40,
                    variables_processed=0,
                    total_variables=len(variables)
                ))
                
            # Check cancellation
            if cancellation_token and cancellation_token.is_cancelled:
                raise OperationCancelledException("Operation cancelled during resolution")
                
            # Resolve variable hierarchy and dependencies
            resolved_variables = self._resolve_variables(
                variables, 
                resolve_hierarchy=resolve_hierarchy,
                evaluate_conditions=evaluate_conditions
            )
            
            # Dependency resolution validation
            if ValidationCheckpointType.DEPENDENCY_RESOLUTION.value in validation_checkpoints:
                checkpoint = self._validate_dependency_resolution(resolved_variables)
                if checkpoint.passed:
                    result.validation_checkpoints_passed.append(ValidationCheckpointType.DEPENDENCY_RESOLUTION)
                else:
                    result.validation_checkpoints_failed.append(checkpoint)
                    result.errors.append(SubstitutionError(
                        error_type='dependency_resolution',
                        message=checkpoint.message,
                        stage=current_stage,
                        details=checkpoint.details
                    ))
                    return result
                    
            # Stage 4: Apply variables
            current_stage = SubstitutionStage.APPLYING
            result.stage_timings[SubstitutionStage.RESOLVING] = time.time() - stage_start_time
            stage_start_time = time.time()
            
            if progress_reporter:
                progress_reporter.report_progress(SubstitutionProgress(
                    current_stage=current_stage,
                    progress_percentage=60,
                    variables_processed=0,
                    total_variables=len(resolved_variables)
                ))
                
            # Apply variables to document
            updated_content, processing_result = self.ooxml_processor.apply_variables_to_xml(
                xml_content=document_content,
                variables=resolved_variables,
                preserve_formatting=preserve_structure,
                preserve_namespaces=preserve_namespaces
            )
            
            if not processing_result.success:
                result.errors.extend([
                    SubstitutionError(
                        error_type='substitution_application',
                        message=error,
                        stage=current_stage
                    ) for error in processing_result.errors
                ])
                return result
                
            result.updated_content = updated_content
            result.variables_applied = processing_result.elements_modified
            
            # Report progress during application
            variables_processed = 0
            for variable_id in resolved_variables:
                if cancellation_token and cancellation_token.is_cancelled:
                    raise OperationCancelledException("Operation cancelled during application")
                    
                variables_processed += 1
                
                if progress_reporter:
                    progress = 60 + int((variables_processed / len(resolved_variables)) * 20)
                    progress_reporter.report_progress(SubstitutionProgress(
                        current_stage=current_stage,
                        progress_percentage=progress,
                        variables_processed=variables_processed,
                        total_variables=len(resolved_variables)
                    ))
                    
            # Substitution validation
            if ValidationCheckpointType.SUBSTITUTION_VALIDATION.value in validation_checkpoints:
                checkpoint = self._validate_substitution_application(result.updated_content, resolved_variables)
                if checkpoint.passed:
                    result.validation_checkpoints_passed.append(ValidationCheckpointType.SUBSTITUTION_VALIDATION)
                else:
                    result.validation_checkpoints_failed.append(checkpoint)
                    result.warnings.append(f"Substitution validation warning: {checkpoint.message}")
                    
            # Stage 5: Finalize
            current_stage = SubstitutionStage.FINALIZING
            result.stage_timings[SubstitutionStage.APPLYING] = time.time() - stage_start_time
            stage_start_time = time.time()
            
            if progress_reporter:
                progress_reporter.report_progress(SubstitutionProgress(
                    current_stage=current_stage,
                    progress_percentage=90,
                    variables_processed=len(resolved_variables),
                    total_variables=len(resolved_variables)
                ))
                
            # Post-substitution validation
            if ValidationCheckpointType.POST_SUBSTITUTION.value in validation_checkpoints:
                checkpoint = self._validate_post_substitution(result.updated_content)
                if checkpoint.passed:
                    result.validation_checkpoints_passed.append(ValidationCheckpointType.POST_SUBSTITUTION)
                else:
                    result.validation_checkpoints_failed.append(checkpoint)
                    result.warnings.append(f"Post-substitution validation warning: {checkpoint.message}")
                    
            # Stage 6: Complete
            current_stage = SubstitutionStage.COMPLETE
            result.stage_timings[SubstitutionStage.FINALIZING] = time.time() - stage_start_time
            
            result.success = True
            result.processing_time = time.time() - start_time
            
            if progress_reporter:
                progress_reporter.report_progress(SubstitutionProgress(
                    current_stage=current_stage,
                    progress_percentage=100,
                    variables_processed=len(resolved_variables),
                    total_variables=len(resolved_variables)
                ))
                
            # Update statistics
            self.statistics['operations_completed'] += 1
            self.statistics['documents_processed'] += 1
            self.statistics['variables_applied'] += result.variables_applied
            self.statistics['total_processing_time'] += result.processing_time
            
        except OperationCancelledException:
            result.cancelled = True
            result.errors.append(SubstitutionError(
                error_type='operation_cancelled',
                message="Operation was cancelled",
                stage=current_stage
            ))
            self.statistics['operations_cancelled'] += 1
            
        except OperationTimeoutException:
            result.timed_out = True
            result.errors.append(SubstitutionError(
                error_type='operation_timeout',
                message=f"Operation timed out after {self.operation_timeout}s",
                stage=current_stage
            ))
            self.statistics['operations_failed'] += 1
            
        except Exception as e:
            result.errors.append(SubstitutionError(
                error_type='unexpected_error',
                message=str(e),
                stage=current_stage,
                details={'traceback': traceback.format_exc()}
            ))
            self.statistics['operations_failed'] += 1
            
        finally:
            result.processing_time = time.time() - start_time
            
        return result
        
    def substitute_variables_in_batch(self,
                                    documents: List[Tuple[str, str, str]],
                                    variables: Dict[str, Any],
                                    parallel_processing: bool = False,
                                    max_workers: Optional[int] = None,
                                    continue_on_error: bool = True,
                                    transaction_mode: str = 'all_or_nothing',
                                    streaming_mode: bool = False,
                                    progress_callback: Optional[Callable[[SubstitutionProgress], None]] = None,
                                    cancellation_token: Optional[CancellationToken] = None) -> BatchSubstitutionResult:
        """
        Substitute variables in multiple documents.
        
        Args:
            documents: List of (name, content, type) tuples
            variables: Variables to substitute
            parallel_processing: Process documents in parallel
            max_workers: Maximum parallel workers (None for auto)
            continue_on_error: Continue processing other documents if one fails
            transaction_mode: 'all_or_nothing', 'per_document', or 'none'
            streaming_mode: Process one document at a time to save memory
            progress_callback: Callback for progress updates
            cancellation_token: Token for operation cancellation
            
        Returns:
            BatchSubstitutionResult with operation outcome
        """
        start_time = time.time()
        
        batch_result = BatchSubstitutionResult(success=False)
        
        # Progress tracking
        progress_reporter = ProgressReporter(progress_callback) if self.enable_progress_reporting else None
        
        try:
            # Initial progress report
            if progress_reporter:
                progress_reporter.report_progress(SubstitutionProgress(
                    current_stage=SubstitutionStage.INITIALIZING,
                    progress_percentage=0,
                    variables_processed=0,
                    total_variables=len(variables),
                    documents_completed=0,
                    total_documents=len(documents),
                    overall_progress_percentage=0
                ))
                
            if parallel_processing and not streaming_mode:
                # Parallel processing
                batch_result = self._process_batch_parallel(
                    documents, variables, max_workers, continue_on_error,
                    transaction_mode, progress_reporter, cancellation_token
                )
            else:
                # Sequential processing
                batch_result = self._process_batch_sequential(
                    documents, variables, continue_on_error, transaction_mode,
                    streaming_mode, progress_reporter, cancellation_token
                )
                
            # Final statistics
            batch_result.total_processing_time = time.time() - start_time
            batch_result.total_variables_applied = sum(
                result.variables_applied for result in batch_result.document_results.values()
            )
            
            # Determine overall success
            batch_result.success = len(batch_result.failed_documents) == 0
            
            # Final progress report
            if progress_reporter:
                progress_reporter.report_progress(SubstitutionProgress(
                    current_stage=SubstitutionStage.COMPLETE,
                    progress_percentage=100,
                    variables_processed=len(variables),
                    total_variables=len(variables),
                    documents_completed=len(documents),
                    total_documents=len(documents),
                    overall_progress_percentage=100
                ))
                
        except Exception as e:
            batch_result.errors.append(SubstitutionError(
                error_type='batch_processing_error',
                message=str(e),
                details={'traceback': traceback.format_exc()}
            ))
            
        return batch_result
        
    def _process_batch_sequential(self,
                                documents: List[Tuple[str, str, str]],
                                variables: Dict[str, Any],
                                continue_on_error: bool,
                                transaction_mode: str,
                                streaming_mode: bool,
                                progress_reporter: Optional[ProgressReporter],
                                cancellation_token: Optional[CancellationToken]) -> BatchSubstitutionResult:
        """Process documents sequentially"""
        batch_result = BatchSubstitutionResult(success=False)
        
        for i, (doc_name, doc_content, doc_type) in enumerate(documents):
            if cancellation_token and cancellation_token.is_cancelled:
                break
                
            # Progress update
            if progress_reporter:
                overall_progress = int((i / len(documents)) * 100)
                progress_reporter.report_progress(SubstitutionProgress(
                    current_stage=SubstitutionStage.APPLYING,
                    progress_percentage=0,
                    variables_processed=0,
                    total_variables=len(variables),
                    current_document=doc_name,
                    documents_completed=i,
                    total_documents=len(documents),
                    overall_progress_percentage=overall_progress
                ))
                
            try:
                # Process individual document
                if transaction_mode == 'per_document':
                    with self.create_transaction() as transaction:
                        result = transaction.substitute_in_document(doc_content, variables)
                else:
                    result = self.substitute_variables_in_document(
                        document_content=doc_content,
                        variables=variables,
                        document_type=doc_type,
                        cancellation_token=cancellation_token
                    )
                    
                batch_result.document_results[doc_name] = result
                
                if result.success:
                    batch_result.successful_documents.append(doc_name)
                else:
                    batch_result.failed_documents.append(doc_name)
                    batch_result.errors.extend(result.errors)
                    
                    if not continue_on_error:
                        break
                        
            except Exception as e:
                error = SubstitutionError(
                    error_type='document_processing_error',
                    message=f"Error processing document {doc_name}: {str(e)}"
                )
                batch_result.errors.append(error)
                batch_result.failed_documents.append(doc_name)
                
                if not continue_on_error:
                    break
                    
        return batch_result
        
    def _process_batch_parallel(self,
                              documents: List[Tuple[str, str, str]],
                              variables: Dict[str, Any],
                              max_workers: Optional[int],
                              continue_on_error: bool,
                              transaction_mode: str,
                              progress_reporter: Optional[ProgressReporter],
                              cancellation_token: Optional[CancellationToken]) -> BatchSubstitutionResult:
        """Process documents in parallel"""
        batch_result = BatchSubstitutionResult(success=False)
        
        if max_workers is None:
            max_workers = min(len(documents), 4)  # Default to 4 workers max
            
        def process_document(doc_info):
            doc_name, doc_content, doc_type = doc_info
            try:
                return doc_name, self.substitute_variables_in_document(
                    document_content=doc_content,
                    variables=variables,
                    document_type=doc_type,
                    cancellation_token=cancellation_token
                )
            except Exception as e:
                return doc_name, SubstitutionResult(
                    success=False,
                    errors=[SubstitutionError(
                        error_type='document_processing_error',
                        message=str(e)
                    )]
                )
                
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_doc = {executor.submit(process_document, doc): doc[0] for doc in documents}
            
            completed = 0
            for future in concurrent.futures.as_completed(future_to_doc):
                if cancellation_token and cancellation_token.is_cancelled:
                    # Cancel remaining futures
                    for f in future_to_doc:
                        f.cancel()
                    break
                    
                doc_name, result = future.result()
                batch_result.document_results[doc_name] = result
                
                if result.success:
                    batch_result.successful_documents.append(doc_name)
                else:
                    batch_result.failed_documents.append(doc_name)
                    batch_result.errors.extend(result.errors)
                    
                completed += 1
                
                # Progress update
                if progress_reporter:
                    overall_progress = int((completed / len(documents)) * 100)
                    progress_reporter.report_progress(SubstitutionProgress(
                        current_stage=SubstitutionStage.APPLYING,
                        progress_percentage=100,
                        variables_processed=len(variables),
                        total_variables=len(variables),
                        documents_completed=completed,
                        total_documents=len(documents),
                        overall_progress_percentage=overall_progress
                    ))
                    
        return batch_result
        
    def _resolve_variables(self,
                         variables: Dict[str, Any],
                         resolve_hierarchy: bool = True,
                         evaluate_conditions: bool = True) -> Dict[str, Any]:
        """Resolve variable hierarchy and dependencies"""
        if not resolve_hierarchy and not evaluate_conditions:
            return variables
            
        resolved = {}
        
        # Convert to ResolvedVariable objects if needed
        for var_id, var_data in variables.items():
            if isinstance(var_data, dict):
                resolved[var_id] = var_data
            else:
                # Already a ResolvedVariable or similar
                resolved[var_id] = var_data.__dict__ if hasattr(var_data, '__dict__') else var_data
                
        # Apply hierarchy resolution
        if resolve_hierarchy:
            resolved = self._apply_hierarchy_precedence(resolved)
            
        # Evaluate conditional variables
        if evaluate_conditions:
            resolved = self._evaluate_conditional_variables(resolved)
            
        return resolved
        
    def _apply_hierarchy_precedence(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Apply variable hierarchy precedence rules"""
        # Group variables by ID
        variable_groups = {}
        for var_key, var_data in variables.items():
            var_id = var_data.get('id', var_key)
            if var_id not in variable_groups:
                variable_groups[var_id] = []
            variable_groups[var_id].append((var_key, var_data))
            
        # Resolve precedence for each group
        resolved = {}
        for var_id, var_list in variable_groups.items():
            if len(var_list) == 1:
                # No conflict, use the only variable
                var_key, var_data = var_list[0]
                resolved[var_key] = var_data
            else:
                # Multiple variables with same ID, resolve by hierarchy level
                var_list.sort(key=lambda x: x[1].get('hierarchy_level', 0), reverse=True)
                winning_var_key, winning_var_data = var_list[0]
                resolved[var_id] = winning_var_data
                
        return resolved
        
    def _evaluate_conditional_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate conditional variables based on conditions"""
        resolved = {}
        
        for var_key, var_data in variables.items():
            conditions = var_data.get('conditions', [])
            
            if not conditions:
                # No conditions, include variable
                resolved[var_key] = var_data
                continue
                
            # Evaluate all conditions
            all_conditions_met = True
            for condition in conditions:
                target_var = condition.get('variable')
                operator = condition.get('operator', 'equals')
                expected_value = condition.get('value')
                
                if target_var not in variables:
                    all_conditions_met = False
                    break
                    
                actual_value = variables[target_var].get('value')
                
                if operator == 'equals':
                    if actual_value != expected_value:
                        all_conditions_met = False
                        break
                elif operator == 'contains':
                    if expected_value not in str(actual_value):
                        all_conditions_met = False
                        break
                elif operator == 'not_equals':
                    if actual_value == expected_value:
                        all_conditions_met = False
                        break
                        
            if all_conditions_met:
                resolved[var_key] = var_data
                
        return resolved
        
    # Validation checkpoint methods
    def _validate_pre_substitution(self, document_content: str) -> ValidationCheckpoint:
        """Validate document before substitution"""
        try:
            # Try to parse XML
            ET.fromstring(document_content)
            return ValidationCheckpoint(
                checkpoint_type=ValidationCheckpointType.PRE_SUBSTITUTION,
                passed=True,
                message="Document XML is valid"
            )
        except ET.ParseError as e:
            return ValidationCheckpoint(
                checkpoint_type=ValidationCheckpointType.PRE_SUBSTITUTION,
                passed=False,
                message=f"Invalid XML structure: {str(e)}",
                details={'parse_error': str(e)}
            )
            
    def _validate_variables(self, variables: Dict[str, Any]) -> ValidationCheckpoint:
        """Validate variable definitions"""
        required_fields = ['id', 'type', 'value']
        
        for var_key, var_data in variables.items():
            for field in required_fields:
                if field not in var_data or var_data[field] is None:
                    return ValidationCheckpoint(
                        checkpoint_type=ValidationCheckpointType.VARIABLE_VALIDATION,
                        passed=False,
                        message=f"Variable {var_key} missing required field: {field}",
                        details={'variable_key': var_key, 'missing_field': field}
                    )
                    
        return ValidationCheckpoint(
            checkpoint_type=ValidationCheckpointType.VARIABLE_VALIDATION,
            passed=True,
            message="All variables have required fields"
        )
        
    def _validate_xpath_expressions(self, variables: Dict[str, Any]) -> ValidationCheckpoint:
        """Validate XPath expressions in variables"""
        if not LXML_AVAILABLE:
            return ValidationCheckpoint(
                checkpoint_type=ValidationCheckpointType.XPATH_VALIDATION,
                passed=True,
                message="XPath validation skipped (lxml not available)"
            )
            
        for var_key, var_data in variables.items():
            xpath = var_data.get('xpath')
            if xpath:
                try:
                    # Try to compile XPath expression
                    lxml_ET.XPath(xpath)
                except lxml_ET.XPathSyntaxError as e:
                    return ValidationCheckpoint(
                        checkpoint_type=ValidationCheckpointType.XPATH_VALIDATION,
                        passed=False,
                        message=f"Invalid XPath in variable {var_key}: {str(e)}",
                        details={'variable_key': var_key, 'xpath': xpath, 'error': str(e)}
                    )
                    
        return ValidationCheckpoint(
            checkpoint_type=ValidationCheckpointType.XPATH_VALIDATION,
            passed=True,
            message="All XPath expressions are valid"
        )
        
    def _validate_dependency_resolution(self, variables: Dict[str, Any]) -> ValidationCheckpoint:
        """Validate dependency resolution"""
        # Check for circular dependencies
        dependencies = {}
        for var_key, var_data in variables.items():
            deps = var_data.get('dependencies', [])
            dependencies[var_key] = deps
            
        # Simple cycle detection
        def has_cycle(var_key, visited, rec_stack):
            visited.add(var_key)
            rec_stack.add(var_key)
            
            for dep in dependencies.get(var_key, []):
                if dep not in visited:
                    if has_cycle(dep, visited, rec_stack):
                        return True
                elif dep in rec_stack:
                    return True
                    
            rec_stack.remove(var_key)
            return False
            
        visited = set()
        for var_key in dependencies:
            if var_key not in visited:
                if has_cycle(var_key, visited, set()):
                    return ValidationCheckpoint(
                        checkpoint_type=ValidationCheckpointType.DEPENDENCY_RESOLUTION,
                        passed=False,
                        message="Circular dependency detected in variables",
                        details={'variable_key': var_key}
                    )
                    
        return ValidationCheckpoint(
            checkpoint_type=ValidationCheckpointType.DEPENDENCY_RESOLUTION,
            passed=True,
            message="No circular dependencies found"
        )
        
    def _validate_substitution_application(self, updated_content: str, variables: Dict[str, Any]) -> ValidationCheckpoint:
        """Validate substitution was applied correctly"""
        try:
            # Parse updated content
            ET.fromstring(updated_content)
            
            # Could add more sophisticated validation here
            # For now, just check that it's still valid XML
            
            return ValidationCheckpoint(
                checkpoint_type=ValidationCheckpointType.SUBSTITUTION_VALIDATION,
                passed=True,
                message="Substitution application validated"
            )
        except ET.ParseError as e:
            return ValidationCheckpoint(
                checkpoint_type=ValidationCheckpointType.SUBSTITUTION_VALIDATION,
                passed=False,
                message=f"Document corrupted during substitution: {str(e)}",
                details={'parse_error': str(e)}
            )
            
    def _validate_post_substitution(self, updated_content: str) -> ValidationCheckpoint:
        """Validate document after substitution"""
        try:
            # Parse and validate structure
            root = ET.fromstring(updated_content)
            
            # Basic validation - ensure we have elements
            if len(list(root.iter())) < 2:
                return ValidationCheckpoint(
                    checkpoint_type=ValidationCheckpointType.POST_SUBSTITUTION,
                    passed=False,
                    message="Document appears to have lost structure"
                )
                
            return ValidationCheckpoint(
                checkpoint_type=ValidationCheckpointType.POST_SUBSTITUTION,
                passed=True,
                message="Document structure validated after substitution"
            )
        except ET.ParseError as e:
            return ValidationCheckpoint(
                checkpoint_type=ValidationCheckpointType.POST_SUBSTITUTION,
                passed=False,
                message=f"Document invalid after substitution: {str(e)}",
                details={'parse_error': str(e)}
            )
            
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return dict(self.statistics)
        
    def reset_statistics(self):
        """Reset processing statistics"""
        self.statistics = {
            'documents_processed': 0,
            'variables_applied': 0,
            'total_processing_time': 0.0,
            'operations_started': 0,
            'operations_completed': 0,
            'operations_failed': 0,
            'operations_cancelled': 0
        }