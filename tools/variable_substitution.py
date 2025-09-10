#!/usr/bin/env python3
"""
StyleStack OOXML Extension Variable System - Variable Substitution Pipeline (Compatibility Module)

This module maintains backward compatibility after splitting the monolithic
variable_substitution.py into focused substitution modules.

New code should import from the specific modules:
- tools.substitution.types for data types and enums
- tools.substitution.pipeline for core substitution pipeline
- tools.substitution.validation for validation engine
- tools.substitution.batch for batch processing
"""


from typing import Any, Dict, List, Optional, Callable
import json
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager
import concurrent.futures

import sys
import os
sys.path.append(os.path.dirname(__file__))

from tools.ooxml_processor import OOXMLProcessor, ProcessingResult
from tools.theme_resolver import ThemeResolver
from tools.variable_resolver import VariableResolver, ResolvedVariable

# Import from split modules
from tools.substitution.types import (
    SubstitutionStage, ValidationCheckpointType, SubstitutionError, SubstitutionProgress,
    ValidationCheckpoint, SubstitutionResult, TransactionContext, OperationCancelledException,
    CancellationToken, ProgressReporter, DefaultProgressReporter, BatchSubstitutionConfig,
    SubstitutionConfig
)
from tools.substitution.pipeline import SubstitutionPipeline
from tools.substitution.validation import ValidationEngine
from tools.substitution.batch import BatchSubstitutionEngine, BatchProgressReporter


class VariableSubstitutionPipeline:
    """
    Main variable substitution pipeline - Backward Compatibility Interface.
    
    Coordinates the substitution pipeline, validation, and batch processing
    components to provide complete variable substitution capabilities.
    """
    
    def __init__(self,
                 enable_transactions: bool = True,
                 enable_progress_reporting: bool = False,
                 validation_level: str = 'standard'):
        """
        Initialize the variable substitution pipeline.
        
        Args:
            enable_transactions: Enable transaction support with rollback
            enable_progress_reporting: Enable progress reporting
            validation_level: Validation level ('minimal', 'standard', 'comprehensive')
        """
        self.enable_transactions = enable_transactions
        self.enable_progress_reporting = enable_progress_reporting
        self.validation_level = validation_level
        
        # Initialize core components
        self.pipeline = SubstitutionPipeline()
        self.validation_engine = ValidationEngine()
        self.batch_engine = BatchSubstitutionEngine()
        
        # Configure validation checkpoints based on level
        self.validation_checkpoints = self._get_validation_checkpoints(validation_level)
        
        # Statistics tracking for backward compatibility
        self.statistics = {
            'substitutions_performed': 0,
            'variables_processed': 0,
            'errors_encountered': 0,
            'transactions_used': 0
        }
    
    def substitute_variables_in_document(self,
                                       document_content: str,
                                       variables: Dict[str, Any],
                                       preserve_structure: bool = True,
                                       preserve_namespaces: bool = True,
                                       resolve_hierarchy: bool = True,
                                       evaluate_conditions: bool = True,
                                       progress_reporter: Optional[ProgressReporter] = None,
                                       cancellation_token: Optional[CancellationToken] = None) -> SubstitutionResult:
        """
        Substitute variables in a document with full pipeline support.
        
        Args:
            document_content: Raw XML content of the document
            variables: Dictionary of variables to substitute
            preserve_structure: Preserve document structure during substitution
            preserve_namespaces: Preserve XML namespaces
            resolve_hierarchy: Enable hierarchical variable resolution
            evaluate_conditions: Enable conditional variable evaluation
            progress_reporter: Optional progress reporter
            cancellation_token: Optional cancellation token
            
        Returns:
            SubstitutionResult with detailed operation results
        """
        # Create configuration
        config = SubstitutionConfig(
            enable_transactions=self.enable_transactions,
            validation_checkpoints=self.validation_checkpoints,
            preserve_structure=preserve_structure,
            preserve_namespaces=preserve_namespaces,
            resolve_hierarchy=resolve_hierarchy,
            evaluate_conditions=evaluate_conditions,
            enable_progress_reporting=progress_reporter is not None,
            progress_reporter=progress_reporter,
            cancellation_token=cancellation_token
        )
        
        # Perform substitution
        result = self.pipeline.substitute_variables(
            document_content=document_content,
            variables=variables,
            config=config
        )
        
        # Update statistics
        self.statistics['substitutions_performed'] += 1
        self.statistics['variables_processed'] += len(variables)
        self.statistics['errors_encountered'] += len(result.errors)
        if self.enable_transactions:
            self.statistics['transactions_used'] += 1
        
        return result
    
    def process_batch_substitution(self,
                                 operations: List[Dict[str, Any]],
                                 max_parallel_operations: int = 4,
                                 progress_callback: Optional[Callable] = None,
                                 cancellation_token: Optional[CancellationToken] = None) -> List[SubstitutionResult]:
        """
        Process multiple substitution operations in batch.
        
        Args:
            operations: List of operation dictionaries
            max_parallel_operations: Maximum parallel operations
            progress_callback: Optional progress callback
            cancellation_token: Optional cancellation token
            
        Returns:
            List of SubstitutionResult objects
        """
        # Configure batch processing
        batch_config = BatchSubstitutionConfig(
            max_parallel_operations=max_parallel_operations,
            enable_progress_reporting=progress_callback is not None,
            enable_transactions=self.enable_transactions,
            validation_checkpoints=self.validation_checkpoints,
            preserve_structure=True,
            preserve_namespaces=True,
            resolve_hierarchy=True,
            evaluate_conditions=True
        )
        
        # Update batch engine configuration
        self.batch_engine.config = batch_config
        
        # Process batch
        results = self.batch_engine.process_batch(
            operations=operations,
            progress_callback=progress_callback,
            cancellation_token=cancellation_token
        )
        
        # Update statistics
        self.statistics['substitutions_performed'] += len(operations)
        for result in results:
            self.statistics['variables_processed'] += result.variables_applied + result.variables_failed
            self.statistics['errors_encountered'] += len(result.errors)
        
        return results
    
    @contextmanager
    def transaction_scope(self, document_content: str):
        """Context manager for transaction-based operations (backward compatibility)."""
        with self.pipeline.transaction_scope(document_content) as context:
            yield context
    
    def validate_variables(self, variables: Dict[str, Any]) -> ValidationCheckpoint:
        """Validate variable definitions (backward compatibility)."""
        return self.validation_engine.validate_variables(variables)
    
    def validate_document_content(self, document_content: str) -> ValidationCheckpoint:
        """Validate document content (backward compatibility)."""
        return self.validation_engine.validate_pre_substitution(document_content, {})
    
    def get_pipeline_statistics(self) -> Dict[str, Any]:
        """Get pipeline statistics (backward compatibility)."""
        # Combine stats from all components
        pipeline_stats = self.pipeline.get_pipeline_statistics()
        validation_stats = self.validation_engine.get_validation_statistics()
        batch_stats = self.batch_engine.get_batch_statistics()
        
        combined_stats = {
            # Backward compatibility stats
            'substitutions_performed': self.statistics['substitutions_performed'],
            'variables_processed': self.statistics['variables_processed'],
            'errors_encountered': self.statistics['errors_encountered'],
            'transactions_used': self.statistics['transactions_used'],
            
            # Pipeline stats
            'pipeline': pipeline_stats,
            'validation': validation_stats,
            'batch': batch_stats
        }
        
        return combined_stats
    
    def reset_statistics(self):
        """Reset all statistics."""
        self.statistics = {
            'substitutions_performed': 0,
            'variables_processed': 0,
            'errors_encountered': 0,
            'transactions_used': 0
        }
        
        self.pipeline.reset_statistics()
        self.validation_engine.reset_statistics()
        self.batch_engine.reset_statistics()
    
    def _get_validation_checkpoints(self, validation_level: str) -> List[str]:
        """Get validation checkpoints based on validation level."""
        if validation_level == 'minimal':
            return [
                ValidationCheckpointType.VARIABLE_VALIDATION.value
            ]
        elif validation_level == 'comprehensive':
            return [
                ValidationCheckpointType.PRE_SUBSTITUTION.value,
                ValidationCheckpointType.VARIABLE_VALIDATION.value,
                ValidationCheckpointType.XPATH_VALIDATION.value,
                ValidationCheckpointType.DEPENDENCY_RESOLUTION.value,
                ValidationCheckpointType.SUBSTITUTION_VALIDATION.value,
                ValidationCheckpointType.POST_SUBSTITUTION.value
            ]
        else:  # standard
            return [
                ValidationCheckpointType.VARIABLE_VALIDATION.value,
                ValidationCheckpointType.XPATH_VALIDATION.value,
                ValidationCheckpointType.POST_SUBSTITUTION.value
            ]


# Convenience functions for backward compatibility

def create_progress_reporter(callback_function: Optional[Callable] = None) -> ProgressReporter:
    """Create a progress reporter (backward compatibility)."""
    if callback_function:
        class CallbackProgressReporter(ProgressReporter):
            def report_progress(self, progress: SubstitutionProgress):
                callback_function(progress)
        return CallbackProgressReporter()
    else:
        return DefaultProgressReporter()


def create_cancellation_token() -> CancellationToken:
    """Create a cancellation token (backward compatibility)."""
    return CancellationToken()


def substitute_variables_simple(document_content: str, 
                               variables: Dict[str, Any]) -> SubstitutionResult:
    """Simple variable substitution function (backward compatibility)."""
    pipeline = VariableSubstitutionPipeline(
        enable_transactions=False,
        enable_progress_reporting=False,
        validation_level='minimal'
    )
    
    return pipeline.substitute_variables_in_document(
        document_content=document_content,
        variables=variables
    )


# Backward compatibility exports
__all__ = [
    # Main class
    'VariableSubstitutionPipeline',
    
    # Types from substitution modules
    'SubstitutionStage',
    'ValidationCheckpointType',
    'SubstitutionError',
    'SubstitutionProgress',
    'ValidationCheckpoint',
    'SubstitutionResult',
    'TransactionContext',
    'OperationCancelledException',
    'CancellationToken',
    'ProgressReporter',
    'DefaultProgressReporter',
    'BatchSubstitutionConfig',
    'SubstitutionConfig',
    
    # Core components
    'SubstitutionPipeline',
    'ValidationEngine',
    'BatchSubstitutionEngine',
    'BatchProgressReporter',
    
    # Convenience functions
    'create_progress_reporter',
    'create_cancellation_token',
    'substitute_variables_simple'
]