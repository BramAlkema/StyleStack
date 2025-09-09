"""
Multi-format OOXML Handler (Compatibility Module)

This module maintains backward compatibility after splitting the monolithic
multi_format_ooxml_handler.py into focused handler modules.

New code should import from the specific modules:
- tools.handlers.types for data types and enums
- tools.handlers.formats for format-specific processing
- tools.handlers.integration for token integration and compatibility
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple, IO
from pathlib import Path
import zipfile
import tempfile
import shutil
import time

from tools.yaml_ooxml_processor import YAMLPatchProcessor, RecoveryStrategy
from tools.token_integration_layer import TokenIntegrationLayer, TokenScope, TokenContext

# Import from split modules
from tools.handlers.types import (
    OOXMLFormat, OOXMLStructure, ProcessingResult, FormatConfiguration,
    ValidationIssue, ProcessingStatistics
)
from tools.handlers.formats import (
    FormatRegistry, FormatProcessor, create_format_processor
)
from tools.handlers.integration import TokenIntegrationManager, CompatibilityMatrix

# Configure logging
logger = logging.getLogger(__name__)


class MultiFormatOOXMLHandler:
    """
    Unified handler for processing multiple OOXML template formats - Main Interface.
    
    Coordinates format detection, processing, token integration, and compatibility
    checks across different OOXML formats (PowerPoint, Word, Excel).
    """
    
    def __init__(self, 
                 recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY_WITH_FALLBACK,
                 enable_token_integration: bool = True):
        """Initialize the multi-format handler."""
        self.recovery_strategy = recovery_strategy
        self.enable_token_integration = enable_token_integration
        
        # Initialize core components
        self.format_registry = FormatRegistry()
        self.token_manager = TokenIntegrationManager() if enable_token_integration else None
        self.compatibility_matrix = CompatibilityMatrix()
        
        # Create format-specific processors
        self.processors = {}
        self.format_processors = {}
        
        for format_type in OOXMLFormat:
            # YAML patch processor for backward compatibility
            processor = YAMLPatchProcessor(recovery_strategy)
            processor.template_type = format_type.value
            self.processors[format_type] = processor
            
            # Format-specific processor
            config = FormatConfiguration(
                format_type=format_type,
                recovery_strategy=recovery_strategy.value,
                enable_token_integration=enable_token_integration
            )
            format_processor = create_format_processor(format_type, config)
            self.format_processors[format_type] = format_processor
        
        # Processing statistics
        self.processing_stats = {
            'files_processed': 0,
            'patches_applied': 0,
            'errors_encountered': 0,
            'formats_processed': {fmt.value: 0 for fmt in OOXMLFormat}
        }
    
    def process_template(self, 
                        template_path: Union[str, Path],
                        patches: List[Dict[str, Any]],
                        output_path: Optional[Union[str, Path]] = None,
                        variables: Optional[Dict[str, Any]] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """
        Process an OOXML template with patches.
        
        Args:
            template_path: Path to the template file
            patches: List of patch operations
            output_path: Optional output path (defaults to temp file)
            variables: Variables for token resolution
            metadata: Metadata for processing context
            
        Returns:
            ProcessingResult with operation details
        """
        template_path = Path(template_path)
        
        try:
            # Detect format
            format_type = self.format_registry.detect_format(template_path)
            logger.info(f"Processing {format_type.value} template: {template_path}")
            
            # Validate template structure
            validation_result = self.format_registry.validate_template_structure(template_path, format_type)
            if not validation_result['valid']:
                return ProcessingResult(
                    success=False,
                    format_type=format_type,
                    processed_files=[],
                    errors=validation_result['errors'],
                    warnings=validation_result['warnings'],
                    statistics={}
                )
            
            # Setup output path
            if output_path is None:
                output_path = self._create_temp_output_path(template_path, format_type)
            else:
                output_path = Path(output_path)
            
            # Copy template to output location
            shutil.copy2(template_path, output_path)
            
            # Register tokens if enabled
            if self.enable_token_integration and self.token_manager:
                self.token_manager.register_format_tokens(
                    format_type, variables or {}, metadata or {}
                )
            
            # Process with format-specific handler
            result = self._process_format_specific(
                output_path, format_type, patches, variables or {}, metadata or {}
            )
            
            # Update statistics
            self.processing_stats['files_processed'] += 1
            self.processing_stats['formats_processed'][format_type.value] += 1
            self.processing_stats['patches_applied'] += len(patches)
            
            result.output_path = str(output_path)
            return result
            
        except Exception as e:
            logger.error(f"Template processing failed: {e}")
            self.processing_stats['errors_encountered'] += 1
            
            return ProcessingResult(
                success=False,
                format_type=OOXMLFormat.POWERPOINT,  # Default fallback
                processed_files=[],
                errors=[f"Processing failed: {e}"],
                warnings=[],
                statistics={}
            )
    
    def _process_format_specific(self,
                               template_path: Path,
                               format_type: OOXMLFormat,
                               patches: List[Dict[str, Any]],
                               variables: Dict[str, Any],
                               metadata: Dict[str, Any]) -> ProcessingResult:
        """Process template with format-specific optimizations."""
        errors = []
        warnings = []
        processed_files = []
        
        # Get format structure and processors
        structure = self.format_registry.get_structure(format_type)
        yaml_processor = self.processors[format_type]
        format_processor = self.format_processors[format_type]
        
        try:
            with zipfile.ZipFile(template_path, 'a') as zip_file:
                # Process main document
                main_doc_result = format_processor.process_zip_entry(
                    zip_file, structure.main_document_path, patches, yaml_processor
                )
                processed_files.append(structure.main_document_path)
                errors.extend(main_doc_result.get('errors', []))
                warnings.extend(main_doc_result.get('warnings', []))
                
                # Process theme files
                for theme_path in structure.theme_paths:
                    if theme_path in zip_file.namelist():
                        theme_result = format_processor.process_zip_entry(
                            zip_file, theme_path, patches, yaml_processor
                        )
                        processed_files.append(theme_path)
                        errors.extend(theme_result.get('errors', []))
                        warnings.extend(theme_result.get('warnings', []))
                
                # Process style files
                for style_path in structure.style_paths:
                    if style_path in zip_file.namelist():
                        style_result = format_processor.process_zip_entry(
                            zip_file, style_path, patches, yaml_processor
                        )
                        processed_files.append(style_path)
                        errors.extend(style_result.get('errors', []))
                        warnings.extend(style_result.get('warnings', []))
            
            # Compile statistics
            stats = format_processor.get_processing_statistics()
            
            success = len(errors) == 0
            
            return ProcessingResult(
                success=success,
                format_type=format_type,
                processed_files=processed_files,
                errors=errors,
                warnings=warnings,
                statistics=stats
            )
            
        except Exception as e:
            logger.error(f"Format-specific processing failed: {e}")
            return ProcessingResult(
                success=False,
                format_type=format_type,
                processed_files=processed_files,
                errors=errors + [f"Processing error: {str(e)}"],
                warnings=warnings,
                statistics={}
            )
    
    def validate_template_structure(self, template_path: Union[str, Path], 
                                   format_type: Optional[OOXMLFormat] = None) -> Dict[str, Any]:
        """Validate template structure against format requirements (backward compatibility)."""
        return self.format_registry.validate_template_structure(template_path, format_type)
    
    def get_compatibility_info(self, source_format: OOXMLFormat, 
                              target_format: OOXMLFormat) -> Dict[str, Any]:
        """Get compatibility information between formats (backward compatibility)."""
        return self.compatibility_matrix.get_compatibility_info(source_format, target_format)
    
    def check_cross_format_compatibility(self, source_format: OOXMLFormat, 
                                       target_format: OOXMLFormat) -> bool:
        """Check if formats are compatible (backward compatibility)."""
        return self.compatibility_matrix.is_compatible(source_format, target_format)
    
    def convert_tokens_for_format(self, tokens: Dict[str, Any], 
                                 source_format: OOXMLFormat,
                                 target_format: OOXMLFormat) -> Dict[str, Any]:
        """Convert tokens between formats (backward compatibility)."""
        if self.token_manager:
            return self.token_manager.resolve_cross_format_tokens(
                source_format, target_format, tokens
            )
        return tokens
    
    def _create_temp_output_path(self, template_path: Path, format_type: OOXMLFormat) -> Path:
        """Create temporary output path for processed template."""
        temp_dir = Path(tempfile.gettempdir())
        timestamp = str(int(time.time()))
        filename = f"{template_path.stem}_processed_{timestamp}.{format_type.value}"
        return temp_dir / filename
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics (backward compatibility)."""
        # Combine stats from all format processors
        combined_stats = dict(self.processing_stats)
        
        format_stats = {}
        for format_type, processor in self.format_processors.items():
            format_stats[format_type.value] = processor.get_processing_statistics()
        
        combined_stats['format_details'] = format_stats
        
        if self.token_manager:
            combined_stats['token_stats'] = {
                'registered_tokens': len(self.token_manager.get_all_tokens()),
                'format_tokens': {
                    fmt.value: len(tokens) 
                    for fmt, tokens in self.token_manager.get_all_tokens().items()
                }
            }
        
        return combined_stats
    
    def reset_statistics(self):
        """Reset processing statistics."""
        self.processing_stats = {
            'files_processed': 0,
            'patches_applied': 0,
            'errors_encountered': 0,
            'formats_processed': {fmt.value: 0 for fmt in OOXMLFormat}
        }
        
        for processor in self.format_processors.values():
            processor.reset_statistics()


# Convenience functions for backward compatibility

def detect_ooxml_format(template_path: Union[str, Path]) -> OOXMLFormat:
    """Detect OOXML format from template path."""
    return FormatRegistry.detect_format(template_path)


def validate_ooxml_template(template_path: Union[str, Path], 
                           format_type: Optional[OOXMLFormat] = None) -> Dict[str, Any]:
    """Validate OOXML template structure."""
    return FormatRegistry.validate_template_structure(template_path, format_type)


def create_multi_format_handler(recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY_WITH_FALLBACK,
                               enable_token_integration: bool = True) -> MultiFormatOOXMLHandler:
    """Create a multi-format handler with specified configuration."""
    return MultiFormatOOXMLHandler(recovery_strategy, enable_token_integration)


def process_ooxml_template(template_path: Union[str, Path],
                          patches: List[Dict[str, Any]],
                          output_path: Optional[Union[str, Path]] = None,
                          variables: Optional[Dict[str, Any]] = None,
                          metadata: Optional[Dict[str, Any]] = None,
                          recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY_WITH_FALLBACK) -> ProcessingResult:
    """
    Convenience function to process an OOXML template with patches (backward compatibility).
    
    Args:
        template_path: Path to the template file
        patches: List of patch operations
        output_path: Optional output path (defaults to temp file)
        variables: Variables for token resolution
        metadata: Metadata for processing context
        recovery_strategy: Recovery strategy for error handling
        
    Returns:
        ProcessingResult with operation details
    """
    handler = MultiFormatOOXMLHandler(recovery_strategy, enable_token_integration=True)
    return handler.process_template(template_path, patches, output_path, variables, metadata)


# Backward compatibility exports
__all__ = [
    # Main class
    'MultiFormatOOXMLHandler',
    
    # Types from handler modules
    'OOXMLFormat',
    'OOXMLStructure',
    'ProcessingResult',
    'FormatConfiguration',
    'ValidationIssue',
    'ProcessingStatistics',
    
    # Core components
    'FormatRegistry',
    'FormatProcessor',
    'TokenIntegrationManager',
    'CompatibilityMatrix',
    
    # Convenience functions
    'detect_ooxml_format',
    'validate_ooxml_template',
    'create_multi_format_handler',
    'process_ooxml_template'
]