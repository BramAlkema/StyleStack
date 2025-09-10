"""
Variable Substitution Core Types and Data Structures

This module contains the core data types, enums, and dataclasses
used throughout the variable substitution system.
"""


from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone


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
    """Complete result of variable substitution operation"""
    success: bool
    substituted_content: Optional[str] = None
    variables_applied: int = 0
    variables_failed: int = 0
    processing_time: float = 0.0
    stage_timings: Dict[SubstitutionStage, float] = field(default_factory=dict)
    errors: List[SubstitutionError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validation_checkpoints_passed: List[ValidationCheckpointType] = field(default_factory=list)
    validation_checkpoints_failed: List[ValidationCheckpoint] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, error_type: str, message: str, stage: Optional[SubstitutionStage] = None, 
                  details: Optional[Dict[str, Any]] = None):
        """Add an error to the result"""
        self.errors.append(SubstitutionError(
            error_type=error_type,
            message=message,
            stage=stage,
            details=details
        ))
        self.success = False
    
    def add_warning(self, message: str):
        """Add a warning to the result"""
        self.warnings.append(message)
    
    def get_total_processing_time(self) -> float:
        """Get total processing time across all stages"""
        return sum(self.stage_timings.values())


@dataclass
class TransactionContext:
    """Context for transaction-based substitution operations"""
    transaction_id: str
    backup_content: Optional[str] = None
    checkpoint_states: Dict[str, Any] = field(default_factory=dict)
    operations_log: List[Dict[str, Any]] = field(default_factory=list)
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    
    def log_operation(self, operation: str, details: Optional[Dict[str, Any]] = None):
        """Log an operation in the transaction"""
        self.operations_log.append({
            'operation': operation,
            'details': details or {},
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    def save_checkpoint(self, checkpoint_name: str, state: Any):
        """Save a checkpoint state"""
        self.checkpoint_states[checkpoint_name] = state
    
    def restore_checkpoint(self, checkpoint_name: str) -> Any:
        """Restore a checkpoint state"""
        return self.checkpoint_states.get(checkpoint_name)


class OperationCancelledException(Exception):
    """Exception raised when operation is cancelled"""
    pass


@dataclass
class CancellationToken:
    """Token for cancellation control"""
    is_cancelled: bool = False
    
    def cancel(self):
        """Mark the operation as cancelled"""
        self.is_cancelled = True
    
    def check_cancelled(self):
        """Check if cancelled and raise exception if so"""
        if self.is_cancelled:
            raise OperationCancelledException("Operation was cancelled")


class ProgressReporter:
    """Base class for progress reporting"""
    
    def report_progress(self, progress: SubstitutionProgress):
        """Report progress information"""
        pass
    
    def report_error(self, error: SubstitutionError):
        """Report error information"""
        pass
    
    def report_completion(self, result: SubstitutionResult):
        """Report completion information"""
        pass


class DefaultProgressReporter(ProgressReporter):
    """Default progress reporter that prints to console"""
    
    def report_progress(self, progress: SubstitutionProgress):
        print(f"[{progress.current_stage.value.upper()}] {progress.progress_percentage}% - "
              f"{progress.variables_processed}/{progress.total_variables} variables processed")
    
    def report_error(self, error: SubstitutionError):
        stage_info = f" ({error.stage.value})" if error.stage else ""
        print(f"ERROR{stage_info}: {error.error_type} - {error.message}")
    
    def report_completion(self, result: SubstitutionResult):
        if result.success:
            print(f"✅ Substitution completed successfully in {result.processing_time:.2f}s")
            print(f"   Variables applied: {result.variables_applied}")
        else:
            print(f"❌ Substitution failed after {result.processing_time:.2f}s")
            print(f"   Errors: {len(result.errors)}, Warnings: {len(result.warnings)}")


@dataclass
class BatchSubstitutionConfig:
    """Configuration for batch substitution operations"""
    max_parallel_operations: int = 4
    enable_progress_reporting: bool = True
    enable_transactions: bool = True
    validation_checkpoints: List[str] = field(default_factory=lambda: [
        ValidationCheckpointType.VARIABLE_VALIDATION.value,
        ValidationCheckpointType.XPATH_VALIDATION.value,
        ValidationCheckpointType.POST_SUBSTITUTION.value
    ])
    preserve_structure: bool = True
    preserve_namespaces: bool = True
    resolve_hierarchy: bool = True
    evaluate_conditions: bool = True
    timeout_seconds: Optional[int] = None


@dataclass 
class SubstitutionConfig:
    """Configuration for single substitution operations"""
    enable_transactions: bool = True
    validation_checkpoints: List[str] = field(default_factory=lambda: [
        ValidationCheckpointType.VARIABLE_VALIDATION.value,
        ValidationCheckpointType.XPATH_VALIDATION.value,
        ValidationCheckpointType.POST_SUBSTITUTION.value
    ])
    preserve_structure: bool = True
    preserve_namespaces: bool = True
    resolve_hierarchy: bool = True
    evaluate_conditions: bool = True
    enable_progress_reporting: bool = False
    progress_reporter: Optional[ProgressReporter] = None
    cancellation_token: Optional[CancellationToken] = None
    timeout_seconds: Optional[int] = 300  # 5 minutes default
    
    def __post_init__(self):
        if self.enable_progress_reporting and not self.progress_reporter:
            self.progress_reporter = DefaultProgressReporter()