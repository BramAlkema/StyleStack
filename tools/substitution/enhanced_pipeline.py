"""
Enhanced Variable Substitution Pipeline with Carrier Variable Support

This module extends the base substitution pipeline with carrier-specific variable
processing, EMU precision calculations, and hierarchical design token resolution.
"""

from typing import Any, Dict, List, Optional, Tuple
import time
import threading
import traceback
from contextlib import contextmanager
import uuid

from .types import (
    SubstitutionStage, ValidationCheckpointType, SubstitutionError, SubstitutionProgress,
    ValidationCheckpoint, SubstitutionResult, TransactionContext, OperationCancelledException,
    CancellationToken, ProgressReporter, SubstitutionConfig
)
from .pipeline import SubstitutionPipeline
from .validation import ValidationEngine
from .carrier_processor import CarrierVariableProcessor, CarrierVariableDefinition


class EnhancedSubstitutionConfig(SubstitutionConfig):
    """Enhanced configuration with carrier variable support"""
    
    def __init__(self, *args, **kwargs):
        # Extract carrier-specific kwargs before calling super
        carrier_kwargs = {
            'enable_carrier_variables': kwargs.pop('enable_carrier_variables', True),
            'enable_emu_validation': kwargs.pop('enable_emu_validation', True),
            'enable_hierarchical_tokens': kwargs.pop('enable_hierarchical_tokens', True),
            'carrier_variable_caching': kwargs.pop('carrier_variable_caching', True),
            'design_token_layers': kwargs.pop('design_token_layers', []),
            'emu_baseline_grid': kwargs.pop('emu_baseline_grid', 360),
            'emu_max_deviation': kwargs.pop('emu_max_deviation', 1)
        }
        
        # Call parent constructor with remaining kwargs
        super().__init__(*args, **kwargs)
        
        # Set carrier variable specific configuration
        self.enable_carrier_variables: bool = carrier_kwargs['enable_carrier_variables']
        self.enable_emu_validation: bool = carrier_kwargs['enable_emu_validation']
        self.enable_hierarchical_tokens: bool = carrier_kwargs['enable_hierarchical_tokens']
        self.carrier_variable_caching: bool = carrier_kwargs['carrier_variable_caching']
        
        # Design token layers (list of dicts with 'name', 'tokens', 'precedence')
        self.design_token_layers: List[Dict[str, Any]] = carrier_kwargs['design_token_layers']
        
        # EMU precision settings
        self.emu_baseline_grid: int = carrier_kwargs['emu_baseline_grid']
        self.emu_max_deviation: int = carrier_kwargs['emu_max_deviation']


class CarrierVariableValidationCheckpointType:
    """Extended validation checkpoints for carrier variables"""
    CARRIER_VARIABLE_SYNTAX = "carrier_variable_syntax"
    EMU_PRECISION_VALIDATION = "emu_precision_validation"
    TOKEN_HIERARCHY_RESOLUTION = "token_hierarchy_resolution"


class EnhancedSubstitutionPipeline(SubstitutionPipeline):
    """
    Enhanced substitution pipeline with carrier variable support.
    
    Extends the base pipeline with semantic carrier variable processing,
    EMU precision calculations, and hierarchical design token resolution.
    """
    
    def __init__(self, enable_carrier_processing: bool = True):
        """Initialize the enhanced substitution pipeline"""
        super().__init__()
        
        self.enable_carrier_processing = enable_carrier_processing
        
        # Initialize carrier variable processor
        if enable_carrier_processing:
            self.carrier_processor = CarrierVariableProcessor(
                enable_emu_validation=True,
                enable_caching=True
            )
        else:
            self.carrier_processor = None
        
        # Enhanced statistics
        self.stats.update({
            'carrier_variables_processed': 0,
            'emu_values_validated': 0,
            'emu_validation_failures': 0,
            'token_layers_configured': 0,
            'hierarchical_resolutions': 0
        })
    
    def configure_design_token_layers(self, layers: List[Dict[str, Any]]):
        """Configure hierarchical design token layers"""
        if not self.carrier_processor:
            return
        
        for layer in layers:
            self.carrier_processor.add_design_token_layer(
                layer['name'],
                layer['tokens'],
                layer['precedence']
            )
        
        self.stats['token_layers_configured'] = len(layers)
    
    def substitute_variables(self,
                           document_content: str,
                           variables: Dict[str, Any],
                           config: Optional[EnhancedSubstitutionConfig] = None) -> SubstitutionResult:
        """
        Enhanced variable substitution with carrier variable support.
        
        Args:
            document_content: Raw XML content of the document
            variables: Dictionary of variables to substitute
            config: Enhanced substitution configuration
            
        Returns:
            SubstitutionResult with detailed operation results
        """
        if config is None:
            config = EnhancedSubstitutionConfig()
        
        # Configure design token layers if provided
        if config.design_token_layers and self.carrier_processor:
            self.configure_design_token_layers(config.design_token_layers)
        
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
            
            # Stage 2: Enhanced validation including carrier variables
            current_stage = SubstitutionStage.VALIDATING
            self._update_progress(config.progress_reporter, current_stage, 10, 0, len(variables))
            
            # Perform base validations
            validation_success = self._perform_base_validations(
                document_content, variables, config, result, current_stage
            )
            if not validation_success:
                return result
            
            # Stage 2.5: Carrier variable specific validations
            if config.enable_carrier_variables and self.carrier_processor:
                carrier_validation_success = self._perform_carrier_validations(
                    document_content, config, result, current_stage
                )
                if not carrier_validation_success:
                    return result
            
            # Stage 3: Enhanced variable resolution with carrier processing
            current_stage = SubstitutionStage.RESOLVING
            stage_start_time = time.time()
            self._update_progress(config.progress_reporter, current_stage, 30, 0, len(variables))
            
            # Check cancellation
            if config.cancellation_token:
                config.cancellation_token.check_cancelled()
            
            # Process carrier variables if enabled
            carrier_variables = []
            if config.enable_carrier_variables and self.carrier_processor:
                carrier_variables, carrier_errors = self._process_carrier_variables(
                    document_content, config
                )
                result.errors.extend(carrier_errors)
                self.stats['carrier_variables_processed'] += len(carrier_variables)
            
            # Resolve traditional variables
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
            
            # Stage 4: Enhanced variable application
            current_stage = SubstitutionStage.APPLYING
            stage_start_time = time.time()
            total_variables = len(resolved_variables) + len(carrier_variables)
            self._update_progress(config.progress_reporter, current_stage, 60, 0, total_variables)
            
            # Apply traditional variables
            updated_content = self._apply_variables_to_content(
                document_content,
                resolved_variables,
                config,
                result
            )
            
            if not updated_content and not result.success:
                return result
            
            # Apply carrier variables
            if config.enable_carrier_variables and self.carrier_processor and carrier_variables:
                updated_content, carrier_application_errors = self._apply_carrier_variables(
                    updated_content, carrier_variables
                )
                result.errors.extend(carrier_application_errors)
            
            result.substituted_content = updated_content
            result.stage_timings[SubstitutionStage.APPLYING] = time.time() - stage_start_time
            
            # Stage 5: Enhanced post-substitution validation
            current_stage = SubstitutionStage.FINALIZING
            stage_start_time = time.time()
            self._update_progress(config.progress_reporter, current_stage, 85, total_variables, total_variables)
            
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
            result.variables_applied = len([v for v in resolved_variables if v.get('applied', False)]) + len(carrier_variables)
            result.variables_failed = (len(resolved_variables) + len(carrier_variables)) - result.variables_applied
            
            self.stats['successful_substitutions'] += 1
            self.stats['total_variables_processed'] += total_variables
            
            self._update_progress(config.progress_reporter, current_stage, 100, total_variables, total_variables)
            
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
    
    def _perform_base_validations(self, document_content: str, variables: Dict[str, Any],
                                config: EnhancedSubstitutionConfig, result: SubstitutionResult,
                                current_stage: SubstitutionStage) -> bool:
        """Perform base validation checkpoints"""
        # Pre-substitution validation
        if ValidationCheckpointType.PRE_SUBSTITUTION.value in config.validation_checkpoints:
            checkpoint = self.validation_engine.validate_pre_substitution(
                document_content, variables
            )
            if not checkpoint.passed:
                result.validation_checkpoints_failed.append(checkpoint)
                result.add_error('pre_validation', checkpoint.message, current_stage, checkpoint.details)
                return False
            result.validation_checkpoints_passed.append(ValidationCheckpointType.PRE_SUBSTITUTION)
        
        # Variable validation
        if ValidationCheckpointType.VARIABLE_VALIDATION.value in config.validation_checkpoints:
            checkpoint = self.validation_engine.validate_variables(variables)
            if not checkpoint.passed:
                result.validation_checkpoints_failed.append(checkpoint)
                result.add_error('variable_validation', checkpoint.message, current_stage, checkpoint.details)
                return False
            result.validation_checkpoints_passed.append(ValidationCheckpointType.VARIABLE_VALIDATION)
        
        # XPath validation
        if ValidationCheckpointType.XPATH_VALIDATION.value in config.validation_checkpoints:
            checkpoint = self.validation_engine.validate_xpath_expressions(variables)
            if not checkpoint.passed:
                result.validation_checkpoints_failed.append(checkpoint)
                result.add_error('xpath_validation', checkpoint.message, current_stage, checkpoint.details)
                return False
            result.validation_checkpoints_passed.append(ValidationCheckpointType.XPATH_VALIDATION)
        
        return True
    
    def _perform_carrier_validations(self, document_content: str, config: EnhancedSubstitutionConfig,
                                   result: SubstitutionResult, current_stage: SubstitutionStage) -> bool:
        """Perform carrier variable specific validations"""
        if not self.carrier_processor:
            return True
        
        # Carrier variable syntax validation
        if CarrierVariableValidationCheckpointType.CARRIER_VARIABLE_SYNTAX in config.validation_checkpoints:
            carrier_variables = self.carrier_processor.pattern_matcher.find_carrier_variables(document_content)
            
            syntax_errors = []
            for variable_path in carrier_variables:
                full_variable = f'{{{{{variable_path}}}}}'
                if not self.carrier_processor.pattern_matcher.is_valid_carrier_variable(full_variable):
                    syntax_errors.append(f"Invalid carrier variable syntax: {full_variable}")
            
            if syntax_errors:
                checkpoint = ValidationCheckpoint(
                    checkpoint_type=CarrierVariableValidationCheckpointType.CARRIER_VARIABLE_SYNTAX,
                    passed=False,
                    message=f"Carrier variable syntax validation failed: {len(syntax_errors)} errors",
                    details={'syntax_errors': syntax_errors}
                )
                result.validation_checkpoints_failed.append(checkpoint)
                result.add_error('carrier_syntax_validation', checkpoint.message, current_stage, checkpoint.details)
                return False
            else:
                result.validation_checkpoints_passed.append(CarrierVariableValidationCheckpointType.CARRIER_VARIABLE_SYNTAX)
        
        return True
    
    def _process_carrier_variables(self, document_content: str,
                                 config: EnhancedSubstitutionConfig) -> Tuple[List[CarrierVariableDefinition], List[SubstitutionError]]:
        """Process carrier variables in document content"""
        if not self.carrier_processor:
            return [], []
        
        variables, errors = self.carrier_processor.process_carrier_variables(document_content)
        
        # Update statistics
        carrier_stats = self.carrier_processor.get_processing_statistics()
        self.stats['emu_values_validated'] += carrier_stats['emu_values_validated']
        self.stats['emu_validation_failures'] += carrier_stats['emu_validation_failures']
        self.stats['hierarchical_resolutions'] += carrier_stats['token_resolution_hits']
        
        return variables, errors
    
    def _apply_carrier_variables(self, content: str,
                               carrier_variables: List[CarrierVariableDefinition]) -> Tuple[str, List[SubstitutionError]]:
        """Apply carrier variables to content"""
        errors = []
        updated_content = content
        
        for variable_def in carrier_variables:
            try:
                variable_pattern = f'{{{{{variable_def.path}}}}}'
                
                # Convert value based on type
                if variable_def.variable_type.value == 'emu':
                    substitution_value = str(int(variable_def.value))
                else:
                    substitution_value = str(variable_def.value)
                
                # Perform substitution
                updated_content = updated_content.replace(variable_pattern, substitution_value)
                
            except Exception as e:
                error = SubstitutionError(
                    error_type="carrier_variable_application_error",
                    message=f"Failed to apply carrier variable {variable_def.path}: {str(e)}",
                    stage=SubstitutionStage.APPLYING,
                    details={'variable_path': variable_def.path, 'value': variable_def.value}
                )
                errors.append(error)
        
        return updated_content, errors
    
    def get_enhanced_pipeline_statistics(self) -> Dict[str, Any]:
        """Get enhanced pipeline processing statistics"""
        base_stats = self.get_pipeline_statistics()
        
        # Add carrier processing statistics
        if self.carrier_processor:
            carrier_stats = self.carrier_processor.get_processing_statistics()
            base_stats['carrier_processing'] = carrier_stats
        
        # Add enhanced stats
        base_stats.update({
            'carrier_variables_processed': self.stats['carrier_variables_processed'],
            'emu_values_validated': self.stats['emu_values_validated'],
            'emu_validation_failures': self.stats['emu_validation_failures'],
            'token_layers_configured': self.stats['token_layers_configured'],
            'hierarchical_resolutions': self.stats['hierarchical_resolutions']
        })
        
        # Calculate derived statistics
        if self.stats['emu_values_validated'] > 0:
            base_stats['emu_validation_success_rate'] = (
                (self.stats['emu_values_validated'] - self.stats['emu_validation_failures']) /
                self.stats['emu_values_validated']
            )
        else:
            base_stats['emu_validation_success_rate'] = 0.0
        
        return base_stats
    
    def reset_enhanced_statistics(self):
        """Reset enhanced pipeline statistics"""
        self.reset_statistics()
        
        self.stats.update({
            'carrier_variables_processed': 0,
            'emu_values_validated': 0,
            'emu_validation_failures': 0,
            'token_layers_configured': 0,
            'hierarchical_resolutions': 0
        })
        
        if self.carrier_processor:
            self.carrier_processor.reset_statistics()
    
    def clear_carrier_cache(self):
        """Clear carrier variable processing cache"""
        if self.carrier_processor:
            self.carrier_processor.clear_cache()