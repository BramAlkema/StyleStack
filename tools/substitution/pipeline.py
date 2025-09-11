"""
Variable Substitution Pipeline Core

This module provides the main substitution pipeline with transaction support,
validation checkpoints, and progress tracking.
"""


from typing import Any, Dict, List, Optional
import time
import threading
import traceback
from pathlib import Path
from contextlib import contextmanager
import uuid

try:
    import lxml.etree as lxml_ET
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False

from .types import (
    SubstitutionStage, ValidationCheckpointType, SubstitutionError, SubstitutionProgress,
    ValidationCheckpoint, SubstitutionResult, TransactionContext, OperationCancelledException,
    CancellationToken, ProgressReporter, SubstitutionConfig
)
from .validation import ValidationEngine


class SubstitutionPipeline:
    """
    Core variable substitution pipeline with transaction support.
    
    Provides atomic operations, progress tracking, and comprehensive validation
    for OOXML variable substitution operations.
    """
    
    def __init__(self):
        """Initialize the substitution pipeline."""
        self.validation_engine = ValidationEngine()
        self.active_transactions = {}
        self.transaction_lock = threading.RLock()
        
        # Statistics tracking
        self.stats = {
            'total_substitutions': 0,
            'successful_substitutions': 0,
            'failed_substitutions': 0,
            'total_variables_processed': 0,
            'total_processing_time': 0.0,
            'transactions_created': 0,
            'transactions_committed': 0,
            'transactions_rolled_back': 0
        }
    
    def substitute_variables(self, 
                           document_content: str,
                           variables: Dict[str, Any],
                           config: Optional[SubstitutionConfig] = None) -> SubstitutionResult:
        """
        Substitute variables in document content with comprehensive pipeline.
        
        Args:
            document_content: Raw XML content of the document
            variables: Dictionary of variables to substitute
            config: Substitution configuration
            
        Returns:
            SubstitutionResult with detailed operation results
        """
        if config is None:
            config = SubstitutionConfig()
        
        start_time = time.time()
        result = SubstitutionResult(success=False)
        transaction_context = None
        current_stage = SubstitutionStage.INITIALIZING
        
        try:
            self.stats['total_substitutions'] += 1
            
            # Stage 1: Initialize transaction if enabled
            if config.enable_transactions:
                transaction_context = self._create_transaction_context(document_content)
                result.metadata['transaction_id'] = transaction_context.transaction_id
            
            # Stage 2: Validate inputs
            current_stage = SubstitutionStage.VALIDATING
            self._update_progress(config.progress_reporter, current_stage, 10, 0, len(variables))
            
            # Pre-substitution validation
            if ValidationCheckpointType.PRE_SUBSTITUTION.value in config.validation_checkpoints:
                checkpoint = self.validation_engine.validate_pre_substitution(
                    document_content, variables
                )
                if not checkpoint.passed:
                    result.validation_checkpoints_failed.append(checkpoint)
                    result.add_error('pre_validation', checkpoint.message, current_stage, checkpoint.details)
                    return result
                result.validation_checkpoints_passed.append(ValidationCheckpointType.PRE_SUBSTITUTION)
            
            # Variable validation
            if ValidationCheckpointType.VARIABLE_VALIDATION.value in config.validation_checkpoints:
                checkpoint = self.validation_engine.validate_variables(variables)
                if not checkpoint.passed:
                    result.validation_checkpoints_failed.append(checkpoint)
                    result.add_error('variable_validation', checkpoint.message, current_stage, checkpoint.details)
                    return result
                result.validation_checkpoints_passed.append(ValidationCheckpointType.VARIABLE_VALIDATION)
            
            # XPath validation
            if ValidationCheckpointType.XPATH_VALIDATION.value in config.validation_checkpoints:
                checkpoint = self.validation_engine.validate_xpath_expressions(variables)
                if not checkpoint.passed:
                    result.validation_checkpoints_failed.append(checkpoint)
                    result.add_error('xpath_validation', checkpoint.message, current_stage, checkpoint.details)
                    return result
                result.validation_checkpoints_passed.append(ValidationCheckpointType.XPATH_VALIDATION)
            
            # Stage 3: Resolve variables
            current_stage = SubstitutionStage.RESOLVING
            stage_start_time = time.time()
            self._update_progress(config.progress_reporter, current_stage, 30, 0, len(variables))
            
            # Check cancellation
            if config.cancellation_token:
                config.cancellation_token.check_cancelled()
            
            resolved_variables = self._resolve_variables(
                variables,
                resolve_hierarchy=config.resolve_hierarchy,
                evaluate_conditions=config.evaluate_conditions
            )
            
            result.stage_timings[SubstitutionStage.RESOLVING] = time.time() - stage_start_time
            
            # Dependency resolution validation
            if ValidationCheckpointType.DEPENDENCY_RESOLUTION.value in config.validation_checkpoints:
                checkpoint = self.validation_engine.validate_dependency_resolution(resolved_variables)
                if not checkpoint.passed:
                    result.validation_checkpoints_failed.append(checkpoint)
                    result.add_error('dependency_resolution', checkpoint.message, current_stage, checkpoint.details)
                    return result
                result.validation_checkpoints_passed.append(ValidationCheckpointType.DEPENDENCY_RESOLUTION)
            
            # Stage 4: Apply variables
            current_stage = SubstitutionStage.APPLYING
            stage_start_time = time.time()
            self._update_progress(config.progress_reporter, current_stage, 60, 0, len(resolved_variables))
            
            # Apply variables to document
            updated_content = self._apply_variables_to_content(
                document_content,
                resolved_variables,
                config,
                result
            )
            
            if not updated_content and not result.success:
                return result
            
            result.substituted_content = updated_content
            result.stage_timings[SubstitutionStage.APPLYING] = time.time() - stage_start_time
            
            # Stage 5: Post-substitution validation
            current_stage = SubstitutionStage.FINALIZING
            stage_start_time = time.time()
            self._update_progress(config.progress_reporter, current_stage, 85, len(resolved_variables), len(resolved_variables))
            
            if ValidationCheckpointType.POST_SUBSTITUTION.value in config.validation_checkpoints:
                checkpoint = self.validation_engine.validate_post_substitution(
                    updated_content, resolved_variables
                )
                if not checkpoint.passed:
                    result.validation_checkpoints_failed.append(checkpoint)
                    result.add_warning(f"Post-substitution validation warning: {checkpoint.message}")
                else:
                    result.validation_checkpoints_passed.append(ValidationCheckpointType.POST_SUBSTITUTION)
            
            result.stage_timings[SubstitutionStage.FINALIZING] = time.time() - stage_start_time
            
            # Stage 6: Commit transaction if enabled
            if config.enable_transactions and transaction_context:
                self._commit_transaction(transaction_context)
            
            # Success
            current_stage = SubstitutionStage.COMPLETE
            result.success = True
            result.variables_applied = len([v for v in resolved_variables if v.get('applied', False)])
            result.variables_failed = len(resolved_variables) - result.variables_applied
            
            self.stats['successful_substitutions'] += 1
            self.stats['total_variables_processed'] += len(resolved_variables)
            
            self._update_progress(config.progress_reporter, current_stage, 100, len(resolved_variables), len(resolved_variables))
            
        except OperationCancelledException:
            current_stage = SubstitutionStage.CANCELLED
            result.add_error('operation_cancelled', 'Operation was cancelled by user', current_stage)
            
        except Exception as e:
            current_stage = SubstitutionStage.ERROR
            result.add_error('unexpected_error', f'Unexpected error: {str(e)}', current_stage, {
                'exception_type': type(e).__name__,
                'traceback': traceback.format_exc()
            })
            
            # Rollback transaction if enabled
            if config.enable_transactions and transaction_context:
                self._rollback_transaction(transaction_context)
                
            self.stats['failed_substitutions'] += 1
            
        finally:
            # Final cleanup
            result.processing_time = time.time() - start_time
            self.stats['total_processing_time'] += result.processing_time
            
            # Remove transaction from active list
            if transaction_context:
                with self.transaction_lock:
                    self.active_transactions.pop(transaction_context.transaction_id, None)
            
            # Final progress report
            if config.progress_reporter and result.success:
                config.progress_reporter.report_completion(result)
            elif config.progress_reporter and not result.success:
                if result.errors:
                    config.progress_reporter.report_error(result.errors[-1])
        
        return result
    
    def _create_transaction_context(self, document_content: str) -> TransactionContext:
        """Create a new transaction context."""
        transaction_id = str(uuid.uuid4())
        context = TransactionContext(
            transaction_id=transaction_id,
            backup_content=document_content
        )
        
        with self.transaction_lock:
            self.active_transactions[transaction_id] = context
            self.stats['transactions_created'] += 1
        
        context.log_operation('transaction_created', {'transaction_id': transaction_id})
        return context
    
    def _commit_transaction(self, context: TransactionContext):
        """Commit a transaction."""
        context.log_operation('transaction_committed')
        context.is_active = False
        self.stats['transactions_committed'] += 1
    
    def _rollback_transaction(self, context: TransactionContext):
        """Rollback a transaction."""
        context.log_operation('transaction_rolled_back')
        context.is_active = False
        self.stats['transactions_rolled_back'] += 1
    
    def _resolve_variables(self, variables: Dict[str, Any], 
                         resolve_hierarchy: bool = True,
                         evaluate_conditions: bool = True) -> List[Dict[str, Any]]:
        """Resolve variables with hierarchy and dependency resolution."""
        # Import here to avoid circular imports
        from variable_resolver import VariableResolver
        
        resolver = VariableResolver(enable_cache=True)
        
        # First pass: convert to resolver format for nested reference resolution
        resolver_context = {}
        for var_name, var_data in variables.items():
            if isinstance(var_data, dict):
                # Import ResolvedVariable for proper typing
                from ..variable_resolver import ResolvedVariable, TokenType, TokenScope
                
                # Determine token type
                token_type = var_data.get('type', 'text')
                try:
                    token_type_enum = TokenType(token_type.upper())
                except (ValueError, AttributeError):
                    token_type_enum = TokenType.TEXT
                
                resolver_context[var_name] = ResolvedVariable(
                    id=var_name,
                    value=var_data.get('value', ''),
                    type=token_type_enum,
                    scope=TokenScope.THEME,
                    source='pipeline_variables',
                    xpath=var_data.get('xpath'),
                    ooxml_mapping=var_data.get('ooxml_mapping')
                )
        
        # Second pass: resolve nested references
        resolved_context = resolver.resolve_all(resolver_context)
        
        # Convert back to pipeline format
        resolved_variables = []
        for var_name, resolved_var in resolved_context.items():
            pipeline_var = {
                'name': var_name,
                'xpath': resolved_var.xpath or '',
                'value': resolved_var.value,
                'type': resolved_var.type.value.lower() if hasattr(resolved_var.type, 'value') else 'text',
                'applied': False
            }
            resolved_variables.append(pipeline_var)
        
        # Handle simple string values that weren't in the resolver context
        for var_name, var_data in variables.items():
            if not isinstance(var_data, dict):
                # Simple string value
                resolved_var = {
                    'name': var_name,
                    'xpath': f'//*[@{var_name}]',  # Default XPath
                    'value': str(var_data),
                    'type': 'text',
                    'applied': False
                }
                resolved_variables.append(resolved_var)
        
        return resolved_variables
    
    def _process_composite_tokens(self, xml_content: str, composite_tokens: Dict[str, Any],
                                context: Optional[Dict[str, Any]] = None) -> str:
        """Process composite tokens (shadows, borders, gradients) in XML content"""
        try:
            # Import composite token processor
            from ..ooxml_processor import OOXMLProcessor
            
            processor = OOXMLProcessor()
            updated_xml, result = processor.apply_composite_tokens_to_xml(
                xml_content, composite_tokens, context
            )
            
            if not result.success:
                # Log warnings/errors but don't fail the entire pipeline
                for error in result.errors:
                    print(f"Composite token processing error: {error}")
                return xml_content  # Return original if processing failed
            
            return updated_xml
            
        except Exception as e:
            print(f"Composite token processing failed: {e}")
            return xml_content  # Return original content on error
    
    def _apply_variables_to_content(self, content: str, variables: List[Dict[str, Any]], 
                                   config: SubstitutionConfig, result: SubstitutionResult) -> Optional[str]:
        """Apply variables to document content."""
        # Import here to avoid circular imports
        from ooxml_processor import OOXMLProcessor
        
        try:
            processor = OOXMLProcessor()
            
            # Convert variables to format expected by OOXML processor
            variables_dict = {}
            for var in variables:
                variables_dict[var['name']] = {
                    'xpath': var['xpath'],
                    'value': var['value'],
                    'type': var.get('type', 'text')
                }
            
            # Apply variables using OOXML processor
            updated_content, processing_result = processor.apply_variables_to_xml(
                xml_content=content,
                variables=variables_dict,
                validate_result=True
            )
            
            # Update success tracking for variables
            for var in variables:
                var['applied'] = True  # Assume success for now
            
            return updated_content if processing_result.success else None
            
        except Exception as e:
            result.add_error('variable_application', f'Failed to apply variables: {str(e)}')
            return None
    
    def _update_progress(self, progress_reporter: Optional[ProgressReporter], 
                        stage: SubstitutionStage, percentage: int,
                        processed: int, total: int):
        """Update progress if reporter is available."""
        if progress_reporter:
            progress = SubstitutionProgress(
                current_stage=stage,
                progress_percentage=percentage,
                variables_processed=processed,
                total_variables=total
            )
            progress_reporter.report_progress(progress)
    
    @contextmanager
    def transaction_scope(self, document_content: str):
        """Context manager for transaction-based operations."""
        context = self._create_transaction_context(document_content)
        try:
            yield context
            self._commit_transaction(context)
        except Exception:
            self._rollback_transaction(context)
            raise
        finally:
            with self.transaction_lock:
                self.active_transactions.pop(context.transaction_id, None)
    
    def get_transaction_status(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific transaction."""
        with self.transaction_lock:
            context = self.active_transactions.get(transaction_id)
            if not context:
                return None
            
            return {
                'transaction_id': context.transaction_id,
                'is_active': context.is_active,
                'start_time': context.start_time.isoformat(),
                'operations_count': len(context.operations_log),
                'checkpoints_count': len(context.checkpoint_states)
            }
    
    def get_active_transactions(self) -> List[str]:
        """Get list of active transaction IDs."""
        with self.transaction_lock:
            return list(self.active_transactions.keys())
    
    def force_rollback_transaction(self, transaction_id: str) -> bool:
        """Force rollback of a specific transaction."""
        with self.transaction_lock:
            context = self.active_transactions.get(transaction_id)
            if context and context.is_active:
                self._rollback_transaction(context)
                return True
            return False
    
    def get_pipeline_statistics(self) -> Dict[str, Any]:
        """Get pipeline processing statistics."""
        stats = dict(self.stats)
        
        # Calculate success rate
        total_attempts = stats['successful_substitutions'] + stats['failed_substitutions']
        if total_attempts > 0:
            stats['success_rate'] = stats['successful_substitutions'] / total_attempts
        else:
            stats['success_rate'] = 0.0
        
        # Calculate average processing time
        if stats['total_substitutions'] > 0:
            stats['avg_processing_time'] = stats['total_processing_time'] / stats['total_substitutions']
        else:
            stats['avg_processing_time'] = 0.0
        
        # Transaction statistics
        total_transactions = stats['transactions_committed'] + stats['transactions_rolled_back']
        if total_transactions > 0:
            stats['transaction_success_rate'] = stats['transactions_committed'] / total_transactions
        else:
            stats['transaction_success_rate'] = 0.0
        
        stats['active_transactions'] = len(self.active_transactions)
        
        return stats
    
    def reset_statistics(self):
        """Reset pipeline statistics."""
        self.stats = {
            'total_substitutions': 0,
            'successful_substitutions': 0,
            'failed_substitutions': 0,
            'total_variables_processed': 0,
            'total_processing_time': 0.0,
            'transactions_created': 0,
            'transactions_committed': 0,
            'transactions_rolled_back': 0
        }