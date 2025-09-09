"""
Batch Processing System for Variable Substitution

This module provides batch processing capabilities with parallel execution,
progress tracking, and comprehensive error handling.
"""

import time
import concurrent.futures
from typing import Dict, List, Any, Optional, Tuple, Callable
from pathlib import Path
import threading

from .types import (
    BatchSubstitutionConfig, SubstitutionResult, SubstitutionProgress, 
    SubstitutionStage, ProgressReporter, CancellationToken, OperationCancelledException
)
from .pipeline import SubstitutionPipeline


class BatchProgressReporter(ProgressReporter):
    """Progress reporter for batch operations with aggregated reporting."""
    
    def __init__(self, total_operations: int, callback: Optional[Callable] = None):
        self.total_operations = total_operations
        self.completed_operations = 0
        self.callback = callback
        self.lock = threading.Lock()
        self.operation_progress = {}  # Track individual operation progress
        
    def report_progress(self, progress: SubstitutionProgress):
        """Report progress for individual operation."""
        with self.lock:
            # Update individual operation progress
            op_id = progress.additional_info.get('operation_id', 'unknown')
            self.operation_progress[op_id] = progress
            
            # Calculate overall progress
            total_progress = sum(p.progress_percentage for p in self.operation_progress.values())
            avg_progress = total_progress / len(self.operation_progress) if self.operation_progress else 0
            
            overall_progress = SubstitutionProgress(
                current_stage=progress.current_stage,
                progress_percentage=int(avg_progress),
                variables_processed=sum(p.variables_processed for p in self.operation_progress.values()),
                total_variables=sum(p.total_variables for p in self.operation_progress.values()),
                documents_completed=self.completed_operations,
                total_documents=self.total_operations,
                overall_progress_percentage=int((self.completed_operations / self.total_operations) * 100)
            )
            
            if self.callback:
                self.callback(overall_progress)
    
    def report_completion(self, result: SubstitutionResult):
        """Report completion of individual operation."""
        with self.lock:
            self.completed_operations += 1
            
            if self.callback:
                # Report final progress
                overall_progress = SubstitutionProgress(
                    current_stage=SubstitutionStage.COMPLETE if result.success else SubstitutionStage.ERROR,
                    progress_percentage=100,
                    variables_processed=result.variables_applied,
                    total_variables=result.variables_applied + result.variables_failed,
                    documents_completed=self.completed_operations,
                    total_documents=self.total_operations,
                    overall_progress_percentage=int((self.completed_operations / self.total_operations) * 100)
                )
                self.callback(overall_progress)


class BatchSubstitutionEngine:
    """
    Batch processing engine for variable substitution operations.
    
    Provides parallel processing, progress tracking, and comprehensive
    error handling for multiple document substitution operations.
    """
    
    def __init__(self, config: Optional[BatchSubstitutionConfig] = None):
        self.config = config or BatchSubstitutionConfig()
        self.pipeline = SubstitutionPipeline()
        
        # Statistics tracking
        self.batch_stats = {
            'batches_processed': 0,
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'total_processing_time': 0.0,
            'avg_parallel_efficiency': 0.0
        }
    
    def process_batch(self, 
                     operations: List[Dict[str, Any]],
                     progress_callback: Optional[Callable] = None,
                     cancellation_token: Optional[CancellationToken] = None) -> List[SubstitutionResult]:
        """
        Process a batch of substitution operations.
        
        Args:
            operations: List of operation dictionaries, each containing:
                       - document_content: Document XML content
                       - variables: Variables to substitute
                       - operation_id: Optional unique identifier
            progress_callback: Optional callback for progress updates
            cancellation_token: Optional cancellation token
            
        Returns:
            List of SubstitutionResult objects
        """
        start_time = time.time()
        results = []
        
        try:
            self.batch_stats['batches_processed'] += 1
            self.batch_stats['total_operations'] += len(operations)
            
            # Setup batch progress reporter
            batch_reporter = None
            if self.config.enable_progress_reporting and progress_callback:
                batch_reporter = BatchProgressReporter(len(operations), progress_callback)
            
            # Determine execution strategy
            if self.config.max_parallel_operations > 1 and len(operations) > 1:
                results = self._process_parallel(operations, batch_reporter, cancellation_token)
            else:
                results = self._process_sequential(operations, batch_reporter, cancellation_token)
            
            # Update statistics
            successful = len([r for r in results if r.success])
            failed = len(results) - successful
            
            self.batch_stats['successful_operations'] += successful
            self.batch_stats['failed_operations'] += failed
            
        except Exception as e:
            # Create error result for all operations if batch fails completely
            for i, operation in enumerate(operations):
                error_result = SubstitutionResult(success=False)
                error_result.add_error('batch_error', f'Batch processing failed: {str(e)}')
                error_result.metadata['operation_id'] = operation.get('operation_id', f'op_{i}')
                results.append(error_result)
            
            self.batch_stats['failed_operations'] += len(operations)
        
        finally:
            processing_time = time.time() - start_time
            self.batch_stats['total_processing_time'] += processing_time
            
            # Calculate parallel efficiency if applicable
            if self.config.max_parallel_operations > 1 and len(operations) > 1:
                expected_sequential_time = sum(r.processing_time for r in results if r.processing_time > 0)
                if expected_sequential_time > 0:
                    efficiency = expected_sequential_time / processing_time
                    self.batch_stats['avg_parallel_efficiency'] = (
                        (self.batch_stats['avg_parallel_efficiency'] * (self.batch_stats['batches_processed'] - 1) + efficiency) 
                        / self.batch_stats['batches_processed']
                    )
        
        return results
    
    def _process_sequential(self, 
                          operations: List[Dict[str, Any]], 
                          batch_reporter: Optional[BatchProgressReporter],
                          cancellation_token: Optional[CancellationToken]) -> List[SubstitutionResult]:
        """Process operations sequentially."""
        results = []
        
        for i, operation in enumerate(operations):
            # Check for cancellation
            if cancellation_token:
                cancellation_token.check_cancelled()
            
            # Create individual progress reporter
            individual_reporter = None
            if batch_reporter:
                individual_reporter = IndividualOperationReporter(
                    operation.get('operation_id', f'op_{i}'),
                    batch_reporter
                )
            
            # Configure substitution
            from .types import SubstitutionConfig
            sub_config = SubstitutionConfig(
                enable_transactions=self.config.enable_transactions,
                validation_checkpoints=self.config.validation_checkpoints,
                preserve_structure=self.config.preserve_structure,
                preserve_namespaces=self.config.preserve_namespaces,
                resolve_hierarchy=self.config.resolve_hierarchy,
                evaluate_conditions=self.config.evaluate_conditions,
                enable_progress_reporting=individual_reporter is not None,
                progress_reporter=individual_reporter,
                cancellation_token=cancellation_token,
                timeout_seconds=self.config.timeout_seconds
            )
            
            # Process individual operation
            result = self.pipeline.substitute_variables(
                document_content=operation['document_content'],
                variables=operation['variables'],
                config=sub_config
            )
            
            # Add operation metadata
            result.metadata['operation_id'] = operation.get('operation_id', f'op_{i}')
            result.metadata['batch_index'] = i
            
            results.append(result)
            
            # Report completion
            if batch_reporter:
                batch_reporter.report_completion(result)
        
        return results
    
    def _process_parallel(self, 
                        operations: List[Dict[str, Any]], 
                        batch_reporter: Optional[BatchProgressReporter],
                        cancellation_token: Optional[CancellationToken]) -> List[SubstitutionResult]:
        """Process operations in parallel."""
        results = [None] * len(operations)  # Maintain order
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_parallel_operations) as executor:
            # Submit all operations
            future_to_index = {}
            
            for i, operation in enumerate(operations):
                # Create individual progress reporter
                individual_reporter = None
                if batch_reporter:
                    individual_reporter = IndividualOperationReporter(
                        operation.get('operation_id', f'op_{i}'),
                        batch_reporter
                    )
                
                # Configure substitution
                from .types import SubstitutionConfig
                sub_config = SubstitutionConfig(
                    enable_transactions=self.config.enable_transactions,
                    validation_checkpoints=self.config.validation_checkpoints,
                    preserve_structure=self.config.preserve_structure,
                    preserve_namespaces=self.config.preserve_namespaces,
                    resolve_hierarchy=self.config.resolve_hierarchy,
                    evaluate_conditions=self.config.evaluate_conditions,
                    enable_progress_reporting=individual_reporter is not None,
                    progress_reporter=individual_reporter,
                    cancellation_token=cancellation_token,
                    timeout_seconds=self.config.timeout_seconds
                )
                
                future = executor.submit(
                    self._process_single_operation,
                    operation,
                    sub_config,
                    i
                )
                future_to_index[future] = i
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_index):
                if cancellation_token and cancellation_token.is_cancelled:
                    # Cancel remaining futures
                    for remaining_future in future_to_index:
                        remaining_future.cancel()
                    break
                
                try:
                    result = future.result(timeout=self.config.timeout_seconds)
                    index = future_to_index[future]
                    results[index] = result
                    
                    # Report completion
                    if batch_reporter:
                        batch_reporter.report_completion(result)
                        
                except concurrent.futures.TimeoutError:
                    index = future_to_index[future]
                    error_result = SubstitutionResult(success=False)
                    error_result.add_error('timeout', 'Operation timed out')
                    error_result.metadata['operation_id'] = operations[index].get('operation_id', f'op_{index}')
                    error_result.metadata['batch_index'] = index
                    results[index] = error_result
                    
                except Exception as e:
                    index = future_to_index[future]
                    error_result = SubstitutionResult(success=False)
                    error_result.add_error('parallel_processing_error', f'Parallel processing error: {str(e)}')
                    error_result.metadata['operation_id'] = operations[index].get('operation_id', f'op_{index}')
                    error_result.metadata['batch_index'] = index
                    results[index] = error_result
        
        # Handle any None results (cancelled operations)
        for i, result in enumerate(results):
            if result is None:
                cancelled_result = SubstitutionResult(success=False)
                cancelled_result.add_error('cancelled', 'Operation was cancelled')
                cancelled_result.metadata['operation_id'] = operations[i].get('operation_id', f'op_{i}')
                cancelled_result.metadata['batch_index'] = i
                results[i] = cancelled_result
        
        return results
    
    def _process_single_operation(self, operation: Dict[str, Any], 
                                config, index: int) -> SubstitutionResult:
        """Process a single operation (for parallel execution)."""
        result = self.pipeline.substitute_variables(
            document_content=operation['document_content'],
            variables=operation['variables'],
            config=config
        )
        
        # Add operation metadata
        result.metadata['operation_id'] = operation.get('operation_id', f'op_{index}')
        result.metadata['batch_index'] = index
        
        return result
    
    def get_batch_statistics(self) -> Dict[str, Any]:
        """Get batch processing statistics."""
        stats = dict(self.batch_stats)
        
        # Calculate success rate
        total_ops = stats['successful_operations'] + stats['failed_operations']
        if total_ops > 0:
            stats['success_rate'] = stats['successful_operations'] / total_ops
        else:
            stats['success_rate'] = 0.0
        
        # Calculate average processing time per operation
        if stats['total_operations'] > 0:
            stats['avg_processing_time_per_operation'] = stats['total_processing_time'] / stats['total_operations']
        else:
            stats['avg_processing_time_per_operation'] = 0.0
        
        # Calculate average batch size
        if stats['batches_processed'] > 0:
            stats['avg_batch_size'] = stats['total_operations'] / stats['batches_processed']
        else:
            stats['avg_batch_size'] = 0.0
        
        return stats
    
    def reset_statistics(self):
        """Reset batch processing statistics."""
        self.batch_stats = {
            'batches_processed': 0,
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'total_processing_time': 0.0,
            'avg_parallel_efficiency': 0.0
        }


class IndividualOperationReporter(ProgressReporter):
    """Progress reporter for individual operations within a batch."""
    
    def __init__(self, operation_id: str, batch_reporter: BatchProgressReporter):
        self.operation_id = operation_id
        self.batch_reporter = batch_reporter
    
    def report_progress(self, progress: SubstitutionProgress):
        """Report progress for this individual operation."""
        # Add operation ID to progress
        progress.additional_info['operation_id'] = self.operation_id
        self.batch_reporter.report_progress(progress)
    
    def report_error(self, error):
        """Report error for this individual operation."""
        # Errors are handled by the batch reporter through completion
        pass
    
    def report_completion(self, result: SubstitutionResult):
        """Report completion for this individual operation."""
        self.batch_reporter.report_completion(result)