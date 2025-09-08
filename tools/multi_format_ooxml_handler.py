"""
Multi-format OOXML Handler

Provides unified handling and processing across different OOXML template formats:
PowerPoint (.potx), Word (.dotx), and Excel (.xltx). Abstracts format-specific 
differences while maintaining full compatibility with each format's unique features.

Part of the StyleStack YAML-to-OOXML Processing Engine.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple, IO
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import zipfile
import tempfile
import shutil
import time
from lxml import etree

from .yaml_ooxml_processor import YAMLPatchProcessor, RecoveryStrategy
from .token_integration_layer import TokenIntegrationLayer, TokenScope, TokenContext

# Configure logging
logger = logging.getLogger(__name__)


class OOXMLFormat(Enum):
    """Supported OOXML template formats."""
    POWERPOINT = "potx"
    WORD = "dotx" 
    EXCEL = "xltx"
    
    @classmethod
    def from_extension(cls, extension: str) -> 'OOXMLFormat':
        """Get format from file extension."""
        ext = extension.lower().lstrip('.')
        for format_type in cls:
            if format_type.value == ext:
                return format_type
        raise ValueError(f"Unsupported OOXML format: {extension}")
    
    @classmethod
    def from_path(cls, path: Union[str, Path]) -> 'OOXMLFormat':
        """Get format from file path."""
        return cls.from_extension(Path(path).suffix)


@dataclass
class OOXMLStructure:
    """Defines the internal structure of an OOXML format."""
    main_document_path: str
    relationships_path: str
    content_types_path: str = "[Content_Types].xml"
    theme_paths: List[str] = None
    style_paths: List[str] = None
    required_namespaces: Dict[str, str] = None
    
    def __post_init__(self):
        if self.theme_paths is None:
            self.theme_paths = []
        if self.style_paths is None:
            self.style_paths = []
        if self.required_namespaces is None:
            self.required_namespaces = {}


@dataclass
class ProcessingResult:
    """Result of multi-format processing operation."""
    success: bool
    format_type: OOXMLFormat
    processed_files: List[str]
    errors: List[str]
    warnings: List[str]
    statistics: Dict[str, Any]
    output_path: Optional[str] = None
    
    def __post_init__(self):
        if self.processed_files is None:
            self.processed_files = []
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.statistics is None:
            self.statistics = {}


class MultiFormatOOXMLHandler:
    """
    Unified handler for processing multiple OOXML template formats.
    
    Features:
    - Format detection and validation
    - Unified patch processing across formats
    - Format-specific optimizations
    - Cross-format compatibility checks
    - Integrated token resolution
    - Comprehensive error handling
    """
    
    # Format-specific structure definitions
    FORMAT_STRUCTURES = {
        OOXMLFormat.POWERPOINT: OOXMLStructure(
            main_document_path="ppt/presentation.xml",
            relationships_path="ppt/_rels/presentation.xml.rels",
            theme_paths=["ppt/theme/theme1.xml"],
            style_paths=["ppt/presentation.xml"],
            required_namespaces={
                'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
                'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
                'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
            }
        ),
        OOXMLFormat.WORD: OOXMLStructure(
            main_document_path="word/document.xml",
            relationships_path="word/_rels/document.xml.rels",
            theme_paths=["word/theme/theme1.xml"],
            style_paths=["word/styles.xml", "word/numbering.xml"],
            required_namespaces={
                'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
                'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
                'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
            }
        ),
        OOXMLFormat.EXCEL: OOXMLStructure(
            main_document_path="xl/workbook.xml",
            relationships_path="xl/_rels/workbook.xml.rels",
            theme_paths=["xl/theme/theme1.xml"],
            style_paths=["xl/styles.xml"],
            required_namespaces={
                'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
                'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
                'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
            }
        )
    }
    
    def __init__(self, 
                 recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY_WITH_FALLBACK,
                 enable_token_integration: bool = True):
        """Initialize the multi-format handler."""
        self.recovery_strategy = recovery_strategy
        self.enable_token_integration = enable_token_integration
        
        # Create format-specific processors
        self.processors = {}
        self.token_layers = {}
        
        for format_type in OOXMLFormat:
            processor = YAMLPatchProcessor(recovery_strategy)
            processor.template_type = format_type.value
            self.processors[format_type] = processor
            
            if enable_token_integration:
                token_layer = TokenIntegrationLayer()
                token_layer.integrate_with_processor(processor)
                self.token_layers[format_type] = token_layer
        
        # Processing statistics
        self.processing_stats = {
            'files_processed': 0,
            'patches_applied': 0,
            'errors_encountered': 0,
            'formats_processed': {fmt.value: 0 for fmt in OOXMLFormat}
        }
        
        # Format compatibility matrix
        self.compatibility_matrix = self._build_compatibility_matrix()
        
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
            format_type = OOXMLFormat.from_path(template_path)
            logger.info(f"Processing {format_type.value} template: {template_path}")
            
            # Validate template structure
            validation_result = self.validate_template_structure(template_path, format_type)
            if not validation_result['valid']:
                return ProcessingResult(
                    success=False,
                    format_type=format_type,
                    processed_files=[],
                    errors=[f"Template validation failed: {validation_result['errors']}"],
                    warnings=[],
                    statistics={}
                )
            
            # Setup output path
            if output_path is None:
                output_path = self._create_temp_output_path(template_path, format_type)
            else:
                output_path = Path(output_path)
            
            # Copy template to output location
            shutil.copy2(template_path, output_path)
            
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
        
        # Get format structure and processor
        structure = self.FORMAT_STRUCTURES[format_type]
        processor = self.processors[format_type]
        
        # Setup token context if enabled
        if self.enable_token_integration:
            token_context = TokenContext(
                scope=TokenScope.TEMPLATE,
                template_type=format_type.value,
                variables=variables,
                metadata=metadata
            )
            
            token_layer = self.token_layers[format_type]
            # Register template-specific tokens
            self._register_format_tokens(token_layer, format_type, variables, metadata)
        
        try:
            with zipfile.ZipFile(template_path, 'a') as zip_file:
                # Process main document
                main_doc_result = self._process_zip_entry(
                    zip_file, structure.main_document_path, patches, processor
                )
                processed_files.append(structure.main_document_path)
                errors.extend(main_doc_result.get('errors', []))
                warnings.extend(main_doc_result.get('warnings', []))
                
                # Process theme files
                for theme_path in structure.theme_paths:
                    if theme_path in zip_file.namelist():
                        theme_result = self._process_zip_entry(
                            zip_file, theme_path, patches, processor
                        )
                        processed_files.append(theme_path)
                        errors.extend(theme_result.get('errors', []))
                        warnings.extend(theme_result.get('warnings', []))
                
                # Process style files
                for style_path in structure.style_paths:
                    if style_path in zip_file.namelist():
                        style_result = self._process_zip_entry(
                            zip_file, style_path, patches, processor
                        )
                        processed_files.append(style_path)
                        errors.extend(style_result.get('errors', []))
                        warnings.extend(style_result.get('warnings', []))
            
            # Get processor statistics
            stats = processor.get_comprehensive_stats()
            
            return ProcessingResult(
                success=len(errors) == 0,
                format_type=format_type,
                processed_files=processed_files,
                errors=errors,
                warnings=warnings,
                statistics=stats
            )
            
        except Exception as e:
            logger.error(f"Format-specific processing failed for {format_type.value}: {e}")
            return ProcessingResult(
                success=False,
                format_type=format_type,
                processed_files=processed_files,
                errors=[f"Processing failed: {e}"] + errors,
                warnings=warnings,
                statistics={}
            )
    
    def _process_zip_entry(self,
                          zip_file: zipfile.ZipFile,
                          entry_path: str,
                          patches: List[Dict[str, Any]],
                          processor: YAMLPatchProcessor) -> Dict[str, Any]:
        """Process a single XML file within the OOXML archive with streaming optimization."""
        result = {'errors': [], 'warnings': []}
        
        try:
            # Get file info for memory optimization
            zip_info_entry = zip_file.getinfo(entry_path)
            file_size = zip_info_entry.file_size
            
            # Use streaming processing for large files (>10MB)
            if file_size > 10 * 1024 * 1024:  # 10MB threshold
                logger.debug(f"Using streaming processing for large file: {entry_path} ({file_size} bytes)")
                result.update(self._process_large_zip_entry(zip_file, entry_path, patches, processor, zip_info_entry))
            else:
                # Standard processing for smaller files
                result.update(self._process_standard_zip_entry(zip_file, entry_path, patches, processor, zip_info_entry))
            
        except Exception as e:
            result['errors'].append(f"Failed to process {entry_path}: {e}")
            logger.error(f"ZIP entry processing failed for {entry_path}: {e}")
        
        return result
    
    def _process_standard_zip_entry(self, 
                                   zip_file: zipfile.ZipFile, 
                                   entry_path: str,
                                   patches: List[Dict[str, Any]], 
                                   processor: YAMLPatchProcessor,
                                   zip_info_entry: zipfile.ZipInfo) -> Dict[str, Any]:
        """Standard processing for smaller ZIP entries."""
        result = {'errors': [], 'warnings': []}
        
        try:
            # Read the XML content
            xml_content = zip_file.read(entry_path)
            xml_doc = etree.fromstring(xml_content)
            
            # Apply patches
            patch_results = processor.apply_patches(xml_doc, patches)
            
            # Collect any errors/warnings from patch results
            for patch_result in patch_results:
                if not patch_result.success:
                    result['errors'].append(f"{entry_path}: {patch_result.error}")
                if patch_result.warnings:
                    result['warnings'].extend([f"{entry_path}: {w}" for w in patch_result.warnings])
            
            # Write back the modified XML with memory-efficient serialization
            self._update_zip_entry_optimized(zip_file, entry_path, xml_doc, zip_info_entry)
            
        except Exception as e:
            result['errors'].append(f"Standard processing failed for {entry_path}: {e}")
            logger.error(f"Standard ZIP entry processing failed for {entry_path}: {e}")
        
        return result
    
    def _process_large_zip_entry(self,
                                zip_file: zipfile.ZipFile,
                                entry_path: str,
                                patches: List[Dict[str, Any]],
                                processor: YAMLPatchProcessor,
                                zip_info_entry: zipfile.ZipInfo) -> Dict[str, Any]:
        """Streaming processing for large ZIP entries to minimize memory usage."""
        result = {'errors': [], 'warnings': []}
        
        try:
            # Use streaming XML parsing for large files
            with tempfile.NamedTemporaryFile() as temp_input:
                # Extract to temporary file for streaming processing
                with zip_file.open(entry_path, 'r') as zip_entry:
                    # Stream copy in chunks to avoid loading entire file into memory
                    chunk_size = 64 * 1024  # 64KB chunks
                    while True:
                        chunk = zip_entry.read(chunk_size)
                        if not chunk:
                            break
                        temp_input.write(chunk)
                
                temp_input.flush()
                temp_input.seek(0)
                
                # Parse XML incrementally for large documents
                try:
                    # Use iterparse for memory-efficient XML parsing
                    events = ("start", "end")
                    context = etree.iterparse(temp_input.name, events=events)
                    context = iter(context)
                    
                    # Get root element
                    event, root = next(context)
                    
                    # Apply patches using streaming approach
                    patch_results = processor.apply_patches(root, patches)
                    
                    # Collect results
                    for patch_result in patch_results:
                        if not patch_result.success:
                            result['errors'].append(f"{entry_path}: {patch_result.error}")
                        if patch_result.warnings:
                            result['warnings'].extend([f"{entry_path}: {w}" for w in patch_result.warnings])
                    
                    # Write back with streaming serialization
                    self._update_zip_entry_streaming(zip_file, entry_path, root, zip_info_entry)
                    
                except etree.XMLSyntaxError as xml_err:
                    # Fall back to standard processing if streaming fails
                    logger.warning(f"Streaming XML parsing failed for {entry_path}, falling back to standard processing: {xml_err}")
                    temp_input.seek(0)
                    xml_content = temp_input.read()
                    xml_doc = etree.fromstring(xml_content)
                    
                    patch_results = processor.apply_patches(xml_doc, patches)
                    for patch_result in patch_results:
                        if not patch_result.success:
                            result['errors'].append(f"{entry_path}: {patch_result.error}")
                        if patch_result.warnings:
                            result['warnings'].extend([f"{entry_path}: {w}" for w in patch_result.warnings])
                    
                    self._update_zip_entry_optimized(zip_file, entry_path, xml_doc, zip_info_entry)
                    
        except Exception as e:
            result['errors'].append(f"Streaming processing failed for {entry_path}: {e}")
            logger.error(f"Streaming ZIP entry processing failed for {entry_path}: {e}")
        
        return result
    
    def _update_zip_entry_optimized(self, 
                                   zip_file: zipfile.ZipFile,
                                   entry_path: str,
                                   xml_doc: etree._Element,
                                   original_zip_info: zipfile.ZipInfo):
        """Update ZIP entry with memory-optimized XML serialization."""
        # Create new ZIP info preserving original metadata
        zip_info = zipfile.ZipInfo(entry_path)
        zip_info.external_attr = original_zip_info.external_attr or (0o644 << 16)
        zip_info.compress_type = original_zip_info.compress_type
        
        # Serialize XML with memory optimization
        with tempfile.SpooledTemporaryFile(max_size=1024*1024) as temp_buffer:  # 1MB in-memory buffer
            # Write XML to temporary buffer
            temp_buffer.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
            etree.ElementTree(xml_doc).write(temp_buffer, encoding='utf-8', xml_declaration=False)
            
            temp_buffer.seek(0)
            modified_content = temp_buffer.read()
            
            # Update ZIP with optimized content
            zip_file.writestr(zip_info, modified_content)
    
    def _update_zip_entry_streaming(self,
                                   zip_file: zipfile.ZipFile,
                                   entry_path: str, 
                                   xml_root: etree._Element,
                                   original_zip_info: zipfile.ZipInfo):
        """Update ZIP entry using streaming approach for large documents."""
        # Create new ZIP info preserving original metadata
        zip_info = zipfile.ZipInfo(entry_path)
        zip_info.external_attr = original_zip_info.external_attr or (0o644 << 16) 
        zip_info.compress_type = original_zip_info.compress_type
        
        # Stream XML serialization to minimize memory usage
        with tempfile.NamedTemporaryFile() as temp_file:
            # Write XML declaration
            temp_file.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
            
            # Stream XML content
            etree.ElementTree(xml_root).write(
                temp_file, 
                encoding='utf-8', 
                xml_declaration=False,
                pretty_print=False  # Disable pretty printing to save memory
            )
            
            temp_file.flush()
            
            # Stream content back to ZIP
            with open(temp_file.name, 'rb') as temp_read:
                zip_file.writestr(zip_info, temp_read.read())
    
    def validate_template_structure(self, 
                                  template_path: Union[str, Path],
                                  format_type: OOXMLFormat) -> Dict[str, Any]:
        """Validate that a template has the expected structure for its format."""
        template_path = Path(template_path)
        structure = self.FORMAT_STRUCTURES[format_type]
        
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'missing_files': [],
            'extra_files': []
        }
        
        try:
            with zipfile.ZipFile(template_path, 'r') as zip_file:
                file_list = zip_file.namelist()
                
                # Check for required files
                required_files = [
                    structure.main_document_path,
                    structure.relationships_path,
                    structure.content_types_path
                ]
                
                for required_file in required_files:
                    if required_file not in file_list:
                        validation_result['missing_files'].append(required_file)
                        validation_result['errors'].append(f"Missing required file: {required_file}")
                        validation_result['valid'] = False
                
                # Check theme and style files (warnings only)
                for theme_path in structure.theme_paths:
                    if theme_path not in file_list:
                        validation_result['warnings'].append(f"Missing theme file: {theme_path}")
                
                for style_path in structure.style_paths:
                    if style_path not in file_list:
                        validation_result['warnings'].append(f"Missing style file: {style_path}")
                
                # Validate XML structure of main document
                try:
                    main_content = zip_file.read(structure.main_document_path)
                    main_doc = etree.fromstring(main_content)
                    
                    # Check for required namespaces
                    doc_namespaces = main_doc.nsmap
                    for prefix, uri in structure.required_namespaces.items():
                        if prefix not in doc_namespaces:
                            validation_result['warnings'].append(
                                f"Missing namespace prefix '{prefix}' for {uri}"
                            )
                        elif doc_namespaces[prefix] != uri:
                            validation_result['warnings'].append(
                                f"Namespace mismatch for '{prefix}': expected {uri}, got {doc_namespaces[prefix]}"
                            )
                            
                except Exception as e:
                    validation_result['errors'].append(f"Invalid main document XML: {e}")
                    validation_result['valid'] = False
        
        except Exception as e:
            validation_result['errors'].append(f"Template validation failed: {e}")
            validation_result['valid'] = False
        
        return validation_result
    
    def _register_format_tokens(self,
                               token_layer: TokenIntegrationLayer,
                               format_type: OOXMLFormat,
                               variables: Dict[str, Any],
                               metadata: Dict[str, Any]):
        """Register format-specific tokens for processing."""
        # Register format-specific default tokens
        format_tokens = {
            OOXMLFormat.POWERPOINT: {
                'slide_width': '10in',
                'slide_height': '7.5in',
                'default_font': 'Calibri',
                'title_size': '44pt'
            },
            OOXMLFormat.WORD: {
                'page_width': '8.5in', 
                'page_height': '11in',
                'default_font': 'Calibri',
                'body_size': '11pt'
            },
            OOXMLFormat.EXCEL: {
                'default_font': 'Calibri',
                'cell_size': '11pt',
                'header_font': 'Calibri Bold'
            }
        }
        
        # Register format-specific tokens
        for token_name, token_value in format_tokens.get(format_type, {}).items():
            token_layer.register_token(
                token_name, token_value, TokenScope.TEMPLATE, format_type.value
            )
        
        # Register variables as document-scope tokens
        for var_name, var_value in variables.items():
            token_layer.register_token(
                var_name, var_value, TokenScope.DOCUMENT
            )
    
    def _create_temp_output_path(self, 
                                template_path: Path, 
                                format_type: OOXMLFormat) -> Path:
        """Create a temporary output path for processing."""
        temp_dir = Path(tempfile.gettempdir())
        base_name = template_path.stem
        timestamp = int(time.time() * 1000) % 1000000  # Last 6 digits for uniqueness
        
        output_name = f"{base_name}_processed_{timestamp}.{format_type.value}"
        return temp_dir / output_name
    
    def _build_compatibility_matrix(self) -> Dict[str, Dict[str, bool]]:
        """Build compatibility matrix for cross-format operations."""
        # Define which operations are compatible across formats
        return {
            'color_operations': {
                'potx_to_dotx': True,   # PowerPoint colors work in Word
                'potx_to_xltx': True,   # PowerPoint colors work in Excel
                'dotx_to_potx': True,   # Word colors work in PowerPoint
                'dotx_to_xltx': True,   # Word colors work in Excel
                'xltx_to_potx': True,   # Excel colors work in PowerPoint
                'xltx_to_dotx': True    # Excel colors work in Word
            },
            'font_operations': {
                'potx_to_dotx': True,   # Font operations are cross-compatible
                'potx_to_xltx': True,
                'dotx_to_potx': True,
                'dotx_to_xltx': True,
                'xltx_to_potx': True,
                'xltx_to_dotx': True
            },
            'theme_operations': {
                'potx_to_dotx': False,  # Theme structures differ significantly
                'potx_to_xltx': False,
                'dotx_to_potx': False,
                'dotx_to_xltx': False,
                'xltx_to_potx': False,
                'xltx_to_dotx': False
            }
        }
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics."""
        return {
            **self.processing_stats,
            'supported_formats': [fmt.value for fmt in OOXMLFormat],
            'processors_active': len(self.processors),
            'token_integration_enabled': self.enable_token_integration
        }
    
    def reset_statistics(self):
        """Reset processing statistics."""
        self.processing_stats = {
            'files_processed': 0,
            'patches_applied': 0,
            'errors_encountered': 0,
            'formats_processed': {fmt.value: 0 for fmt in OOXMLFormat}
        }
        
        # Reset processor statistics
        for processor in self.processors.values():
            processor.reset_stats()


# Convenience functions

def create_multi_format_handler(enable_token_integration: bool = True) -> MultiFormatOOXMLHandler:
    """Create a multi-format handler with default configuration."""
    return MultiFormatOOXMLHandler(enable_token_integration=enable_token_integration)

def process_ooxml_template(template_path: Union[str, Path],
                          patches: List[Dict[str, Any]],
                          output_path: Optional[Union[str, Path]] = None,
                          variables: Optional[Dict[str, Any]] = None) -> ProcessingResult:
    """
    Convenience function to process an OOXML template.
    
    Args:
        template_path: Path to the template file
        patches: List of patch operations
        output_path: Optional output path
        variables: Variables for token resolution
        
    Returns:
        ProcessingResult with operation details
    """
    handler = create_multi_format_handler()
    return handler.process_template(template_path, patches, output_path, variables)