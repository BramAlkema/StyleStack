"""
Format-Specific Processing and Configuration

This module provides format-specific processing logic and configuration
for different OOXML template formats (PowerPoint, Word, Excel).
"""

import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import zipfile
from lxml import etree

from .types import OOXMLFormat, OOXMLStructure, FormatConfiguration, ProcessingResult, ValidationIssue

logger = logging.getLogger(__name__)


class FormatRegistry:
    """
    Registry for format-specific configurations and processing logic.
    
    Provides format detection, structure definitions, and processing
    optimization strategies for different OOXML formats.
    """
    
    # Format-specific structure definitions
    FORMAT_STRUCTURES = {
        OOXMLFormat.POWERPOINT: OOXMLStructure(
            main_document_path="ppt/presentation.xml",
            relationships_path="ppt/_rels/presentation.xml.rels",
            theme_paths=["ppt/theme/theme1.xml"],
            style_paths=[],  # Presentation.xml is already the main document, no separate style files
            content_paths=["ppt/slides/*.xml"],  # Pattern for slide files
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
    
    @classmethod
    def get_structure(cls, format_type: OOXMLFormat) -> OOXMLStructure:
        """Get structure definition for a format."""
        return cls.FORMAT_STRUCTURES.get(format_type)
    
    @classmethod
    def get_all_structures(cls) -> Dict[OOXMLFormat, OOXMLStructure]:
        """Get all format structures."""
        return cls.FORMAT_STRUCTURES.copy()
    
    @classmethod
    def detect_format(cls, template_path: Union[str, Path]) -> OOXMLFormat:
        """Detect format from template file."""
        return OOXMLFormat.from_path(template_path)
    
    @classmethod
    def validate_template_structure(cls, template_path: Union[str, Path], 
                                   format_type: Optional[OOXMLFormat] = None) -> Dict[str, Any]:
        """Validate template structure against format requirements."""
        if format_type is None:
            format_type = cls.detect_format(template_path)
        
        structure = cls.get_structure(format_type)
        issues = []
        
        try:
            with zipfile.ZipFile(template_path, 'r') as zip_file:
                file_list = zip_file.namelist()
                
                # Check main document
                if structure.main_document_path not in file_list:
                    issues.append(ValidationIssue(
                        severity='error',
                        message=f"Missing main document: {structure.main_document_path}",
                        file_path=str(template_path)
                    ))
                
                # Check relationships
                if structure.relationships_path not in file_list:
                    issues.append(ValidationIssue(
                        severity='warning',
                        message=f"Missing relationships file: {structure.relationships_path}",
                        file_path=str(template_path)
                    ))
                
                # Check content types
                if structure.content_types_path not in file_list:
                    issues.append(ValidationIssue(
                        severity='error',
                        message=f"Missing content types: {structure.content_types_path}",
                        file_path=str(template_path)
                    ))
                
                # Check theme files (warnings only)
                for theme_path in structure.theme_paths:
                    if theme_path not in file_list:
                        issues.append(ValidationIssue(
                            severity='info',
                            message=f"Theme file not found: {theme_path}",
                            file_path=str(template_path)
                        ))
                
                # Check style files (warnings only)
                for style_path in structure.style_paths:
                    if style_path not in file_list:
                        issues.append(ValidationIssue(
                            severity='info',
                            message=f"Style file not found: {style_path}",
                            file_path=str(template_path)
                        ))
        
        except zipfile.BadZipFile:
            issues.append(ValidationIssue(
                severity='error',
                message="Template file is not a valid ZIP/OOXML file",
                file_path=str(template_path)
            ))
        
        except Exception as e:
            issues.append(ValidationIssue(
                severity='error',
                message=f"Template validation error: {str(e)}",
                file_path=str(template_path)
            ))
        
        # Determine overall validity
        has_errors = any(issue.severity == 'error' for issue in issues)
        
        return {
            'valid': not has_errors,
            'format_type': format_type,
            'issues': issues,
            'errors': [issue.message for issue in issues if issue.severity == 'error'],
            'warnings': [issue.message for issue in issues if issue.severity == 'warning'],
            'info': [issue.message for issue in issues if issue.severity == 'info']
        }


class FormatProcessor:
    """
    Base class for format-specific processing operations.
    
    Provides common functionality for processing different OOXML formats
    with format-specific optimizations and error handling.
    """
    
    def __init__(self, format_type: OOXMLFormat, config: Optional[FormatConfiguration] = None):
        self.format_type = format_type
        self.config = config or FormatConfiguration(format_type)
        self.structure = FormatRegistry.get_structure(format_type)
        
        # Processing statistics
        self.stats = {
            'files_processed': 0,
            'patches_applied': 0,
            'errors_encountered': 0,
            'processing_time': 0.0
        }
    
    def process_zip_entry(self, zip_file: zipfile.ZipFile, entry_path: str,
                         patches: List[Dict[str, Any]], processor) -> Dict[str, Any]:
        """Process a single entry within an OOXML ZIP file."""
        result = {'errors': [], 'warnings': [], 'processed': False}
        
        try:
            if entry_path not in zip_file.namelist():
                result['warnings'].append(f"Entry not found in template: {entry_path}")
                return result
            
            # Read XML content
            xml_content = zip_file.read(entry_path).decode('utf-8')
            
            # Apply format-specific preprocessing
            xml_content = self._preprocess_xml_content(xml_content, entry_path)
            
            # Apply patches using the processor
            if patches:
                # Parse XML for processing
                try:
                    xml_doc = etree.fromstring(xml_content.encode('utf-8'))
                    
                    # Apply patches
                    patch_results = []
                    for patch in patches:
                        patch_result = processor.apply_patch(xml_doc, patch)
                        patch_results.append(patch_result)
                        
                        if not patch_result.success:
                            result['errors'].append(f"Patch failed in {entry_path}: {patch_result.message}")
                        elif patch_result.severity.value in ['warning', 'info']:
                            result['warnings'].append(f"Patch warning in {entry_path}: {patch_result.message}")
                    
                    # Convert back to string
                    modified_content = etree.tostring(xml_doc, encoding='unicode', pretty_print=True)
                    
                    # Apply format-specific postprocessing
                    modified_content = self._postprocess_xml_content(modified_content, entry_path)
                    
                    # Write back to ZIP
                    with zip_file.open(entry_path, 'w') as entry_file:
                        entry_file.write(modified_content.encode('utf-8'))
                    
                    result['processed'] = True
                    self.stats['patches_applied'] += len([r for r in patch_results if r.success])
                    
                except etree.XMLSyntaxError as e:
                    result['errors'].append(f"XML parsing error in {entry_path}: {str(e)}")
                
            self.stats['files_processed'] += 1
            
        except Exception as e:
            result['errors'].append(f"Processing error in {entry_path}: {str(e)}")
            self.stats['errors_encountered'] += 1
        
        return result
    
    def _preprocess_xml_content(self, xml_content: str, entry_path: str) -> str:
        """Apply format-specific preprocessing to XML content."""
        # Default implementation - can be overridden by subclasses
        return xml_content
    
    def _postprocess_xml_content(self, xml_content: str, entry_path: str) -> str:
        """Apply format-specific postprocessing to XML content."""
        # Default implementation - can be overridden by subclasses
        return xml_content
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics for this format processor."""
        stats = dict(self.stats)
        stats['format_type'] = self.format_type.value
        stats['success_rate'] = 1.0 - (stats['errors_encountered'] / max(stats['files_processed'], 1))
        return stats
    
    def reset_statistics(self):
        """Reset processing statistics."""
        self.stats = {
            'files_processed': 0,
            'patches_applied': 0,
            'errors_encountered': 0,
            'processing_time': 0.0
        }


class PowerPointProcessor(FormatProcessor):
    """Specialized processor for PowerPoint templates (.potx)."""
    
    def __init__(self, config: Optional[FormatConfiguration] = None):
        super().__init__(OOXMLFormat.POWERPOINT, config)
    
    def _preprocess_xml_content(self, xml_content: str, entry_path: str) -> str:
        """PowerPoint-specific preprocessing."""
        # Handle presentation-specific namespace issues
        if 'presentation.xml' in entry_path:
            # Ensure proper namespace declarations
            if 'xmlns:p=' not in xml_content:
                xml_content = xml_content.replace(
                    '<p:presentation',
                    '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
                )
        
        return xml_content
    
    def _postprocess_xml_content(self, xml_content: str, entry_path: str) -> str:
        """PowerPoint-specific postprocessing."""
        # Ensure consistent formatting for presentation files
        return xml_content


class WordProcessor(FormatProcessor):
    """Specialized processor for Word templates (.dotx)."""
    
    def __init__(self, config: Optional[FormatConfiguration] = None):
        super().__init__(OOXMLFormat.WORD, config)
    
    def _preprocess_xml_content(self, xml_content: str, entry_path: str) -> str:
        """Word-specific preprocessing."""
        # Handle document-specific namespace issues
        if 'document.xml' in entry_path:
            # Ensure proper namespace declarations
            if 'xmlns:w=' not in xml_content:
                xml_content = xml_content.replace(
                    '<w:document',
                    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
                )
        
        return xml_content


class ExcelProcessor(FormatProcessor):
    """Specialized processor for Excel templates (.xltx)."""
    
    def __init__(self, config: Optional[FormatConfiguration] = None):
        super().__init__(OOXMLFormat.EXCEL, config)
    
    def _preprocess_xml_content(self, xml_content: str, entry_path: str) -> str:
        """Excel-specific preprocessing."""
        # Handle workbook-specific namespace issues
        if 'workbook.xml' in entry_path:
            # Ensure proper namespace declarations
            if 'xmlns:x=' not in xml_content:
                xml_content = xml_content.replace(
                    '<workbook',
                    '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
                )
        
        return xml_content


def create_format_processor(format_type: OOXMLFormat, 
                           config: Optional[FormatConfiguration] = None) -> FormatProcessor:
    """Factory function to create format-specific processors."""
    processors = {
        OOXMLFormat.POWERPOINT: PowerPointProcessor,
        OOXMLFormat.WORD: WordProcessor,
        OOXMLFormat.EXCEL: ExcelProcessor
    }
    
    processor_class = processors.get(format_type, FormatProcessor)
    return processor_class(config)