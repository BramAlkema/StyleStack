"""OOXML probe file generator for round-trip testing."""

import datetime
import zipfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..core.exceptions import ValidationError, OOXMLTesterError
from ..core.utils import ensure_directory, safe_filename
from .templates import DocxTemplate, PptxTemplate, XlsxTemplate


@dataclass
class ValidationResult:
    """Result of probe file validation."""
    is_valid: bool
    format: Optional[str] = None
    found_features: List[str] = None
    missing_features: List[str] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.found_features is None:
            self.found_features = []
        if self.missing_features is None:
            self.missing_features = []
        if self.errors is None:
            self.errors = []


class ProbeGenerator:
    """Generates OOXML probe files for testing compatibility."""
    
    # Supported features by format
    SUPPORTED_FEATURES = {
        'docx': [
            'styles', 'themes', 'numbering', 'tables', 'headers_footers',
            'sections', 'fields', 'images', 'hyperlinks', 'comments',
            'track_changes', 'forms', 'footnotes', 'endnotes'
        ],
        'pptx': [
            'masters', 'layouts', 'themes', 'shapes', 'animations',
            'transitions', 'charts', 'tables', 'images', 'notes',
            'handouts', 'custom_properties', 'hyperlinks'
        ],
        'xlsx': [
            'styles', 'tables', 'charts', 'formatting', 'formulas',
            'pivot_tables', 'data_validation', 'conditional_formatting',
            'images', 'hyperlinks', 'worksheets', 'named_ranges', 'themes'
        ]
    }
    
    # StyleStack carrier mappings
    STYLESTACK_CARRIERS = {
        'theme.color.accent1': {'formats': ['docx', 'pptx', 'xlsx'], 'xpath': '//a:accent1'},
        'theme.color.accent2': {'formats': ['docx', 'pptx', 'xlsx'], 'xpath': '//a:accent2'},
        'theme.font.major.latin': {'formats': ['docx', 'pptx', 'xlsx'], 'xpath': '//a:majorFont/a:latin'},
        'theme.font.minor.latin': {'formats': ['docx', 'pptx', 'xlsx'], 'xpath': '//a:minorFont/a:latin'},
        'master.level1.size_emu': {'formats': ['pptx'], 'xpath': '//a:lvl1pPr/a:defRPr/@sz'},
        'master.level1.margin_emu': {'formats': ['pptx'], 'xpath': '//a:lvl1pPr/@marL'},
        'table.flags.firstRow': {'formats': ['docx', 'pptx'], 'xpath': '//a:tblPr/@firstRow'},
        'shape.default.fill.color': {'formats': ['pptx'], 'xpath': '//a:solidFill/a:srgbClr/@val'}
    }
    
    def __init__(self, config):
        """Initialize probe generator with configuration."""
        self.config = config
        self._templates = {
            'docx': DocxTemplate(),
            'pptx': PptxTemplate(), 
            'xlsx': XlsxTemplate()
        }
    
    def generate(self, output_dir: Path, format: str, features: List[str], count: int) -> List[str]:
        """Generate probe files (legacy interface for CLI)."""
        ensure_directory(output_dir)
        
        if format == 'all':
            formats = ['docx', 'pptx', 'xlsx']
        else:
            formats = [format]
        
        generated_files = []
        
        for fmt in formats:
            for i in range(count):
                if fmt == 'docx':
                    probe_file = self.generate_docx_probe(
                        output_dir=output_dir,
                        features=features,
                        filename=f'probe_{fmt}_{i+1}.{fmt}'
                    )
                elif fmt == 'pptx':
                    probe_file = self.generate_pptx_probe(
                        output_dir=output_dir,
                        features=features,
                        filename=f'probe_{fmt}_{i+1}.{fmt}'
                    )
                elif fmt == 'xlsx':
                    probe_file = self.generate_xlsx_probe(
                        output_dir=output_dir,
                        features=features,
                        filename=f'probe_{fmt}_{i+1}.{fmt}'
                    )
                
                generated_files.append(str(probe_file))
        
        return generated_files
    
    def generate_docx_probe(self, output_dir: Path, features: List[str], 
                           filename: Optional[str] = None) -> Path:
        """Generate Word document probe with specific features."""
        ensure_directory(output_dir)
        
        # Validate features
        self._validate_features('docx', features)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'probe_docx_{timestamp}.docx'
        
        filename = safe_filename(filename)
        output_file = output_dir / filename
        
        # Generate DOCX content using template
        template = self._templates['docx']
        template.create_probe(output_file, features)
        
        return output_file
    
    def generate_pptx_probe(self, output_dir: Path, features: List[str],
                           filename: Optional[str] = None) -> Path:
        """Generate PowerPoint presentation probe with specific features.""" 
        ensure_directory(output_dir)
        
        # Validate features
        self._validate_features('pptx', features)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'probe_pptx_{timestamp}.pptx'
        
        filename = safe_filename(filename)
        output_file = output_dir / filename
        
        # Generate PPTX content using template
        template = self._templates['pptx']
        template.create_probe(output_file, features)
        
        return output_file
    
    def generate_xlsx_probe(self, output_dir: Path, features: List[str],
                           filename: Optional[str] = None) -> Path:
        """Generate Excel workbook probe with specific features."""
        ensure_directory(output_dir)
        
        # Validate features
        self._validate_features('xlsx', features)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'probe_xlsx_{timestamp}.xlsx'
        
        filename = safe_filename(filename)
        output_file = output_dir / filename
        
        # Generate XLSX content using template
        template = self._templates['xlsx']
        template.create_probe(output_file, features)
        
        return output_file
    
    def generate_carrier_probe(self, output_dir: Path, format: str, 
                              carriers: List[str], filename: Optional[str] = None) -> Path:
        """Generate probe targeting specific StyleStack carriers."""
        ensure_directory(output_dir)
        
        # Validate format
        if format not in self.SUPPORTED_FEATURES:
            raise ValueError(f"Unsupported format: {format}")
        
        # Validate carriers for format
        valid_carriers = []
        for carrier in carriers:
            if carrier in self.STYLESTACK_CARRIERS:
                carrier_info = self.STYLESTACK_CARRIERS[carrier]
                if format in carrier_info['formats']:
                    valid_carriers.append(carrier)
        
        if not valid_carriers:
            raise ValueError(f"No valid carriers for format {format}")
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'carrier_probe_{format}_{timestamp}.{format}'
        
        filename = safe_filename(filename)
        output_file = output_dir / filename
        
        # Generate carrier-specific content
        template = self._templates[format]
        template.create_carrier_probe(output_file, valid_carriers)
        
        return output_file
    
    def generate_batch(self, output_dir: Path, probe_configs: List[Dict[str, Any]]) -> List[Path]:
        """Generate multiple probe files from configuration list."""
        ensure_directory(output_dir)
        
        generated_files = []
        
        for config in probe_configs:
            format = config['format']
            features = config.get('features', [])
            name = config.get('name', None)
            
            if name:
                filename = f"{name}.{format}"
            else:
                filename = None
            
            if format == 'docx':
                probe_file = self.generate_docx_probe(output_dir, features, filename)
            elif format == 'pptx':
                probe_file = self.generate_pptx_probe(output_dir, features, filename)
            elif format == 'xlsx':
                probe_file = self.generate_xlsx_probe(output_dir, features, filename)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            generated_files.append(probe_file)
        
        return generated_files
    
    def validate_probe(self, probe_file: Path, expected_features: List[str]) -> ValidationResult:
        """Validate that probe file contains expected features."""
        if not probe_file.exists():
            return ValidationResult(
                is_valid=False,
                errors=[f"Probe file does not exist: {probe_file}"]
            )
        
        # Determine format from extension
        format = probe_file.suffix.lower().lstrip('.')
        if format not in self.SUPPORTED_FEATURES:
            return ValidationResult(
                is_valid=False,
                errors=[f"Unsupported file format: {format}"]
            )
        
        try:
            # Basic ZIP validation
            if not zipfile.is_zipfile(probe_file):
                return ValidationResult(
                    is_valid=False,
                    format=format,
                    errors=["Not a valid ZIP file"]
                )
            
            # Use template to validate features
            template = self._templates[format]
            validation_result = template.validate_features(probe_file, expected_features)
            validation_result.format = format
            
            return validation_result
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                format=format,
                errors=[f"Validation error: {str(e)}"]
            )
    
    def validate_ooxml_structure(self, ooxml_file: Path) -> ValidationResult:
        """Validate basic OOXML file structure."""
        if not ooxml_file.exists():
            return ValidationResult(
                is_valid=False,
                errors=[f"File does not exist: {ooxml_file}"]
            )
        
        # Determine format
        format = ooxml_file.suffix.lower().lstrip('.')
        
        try:
            # Basic ZIP validation
            if not zipfile.is_zipfile(ooxml_file):
                return ValidationResult(
                    is_valid=False,
                    format=format,
                    errors=["Not a valid ZIP file"]
                )
            
            # Check for required OOXML files
            with zipfile.ZipFile(ooxml_file, 'r') as zip_file:
                files = zip_file.namelist()
                
                # Required files for all OOXML formats
                required_files = ['[Content_Types].xml', '_rels/.rels']
                
                # Format-specific required files
                if format == 'docx':
                    required_files.extend(['word/document.xml'])
                elif format == 'pptx':
                    required_files.extend(['ppt/presentation.xml'])
                elif format == 'xlsx':
                    required_files.extend(['xl/workbook.xml'])
                
                missing_files = [f for f in required_files if f not in files]
                
                if missing_files:
                    return ValidationResult(
                        is_valid=False,
                        format=format,
                        errors=[f"Missing required files: {', '.join(missing_files)}"]
                    )
            
            return ValidationResult(
                is_valid=True,
                format=format
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                format=format,
                errors=[f"Structure validation error: {str(e)}"]
            )
    
    def _validate_features(self, format: str, features: List[str]) -> None:
        """Validate that features are supported for the given format."""
        if format not in self.SUPPORTED_FEATURES:
            raise ValueError(f"Unsupported format: {format}")
        
        supported = self.SUPPORTED_FEATURES[format]
        unsupported = [f for f in features if f not in supported]
        
        if unsupported:
            raise ValueError(f"Unsupported features for {format}: {', '.join(unsupported)}")
    
    def get_supported_features(self, format: str) -> List[str]:
        """Get list of supported features for a format."""
        return self.SUPPORTED_FEATURES.get(format, [])
    
    def get_supported_carriers(self, format: str) -> List[str]:
        """Get list of supported StyleStack carriers for a format."""
        carriers = []
        for carrier, info in self.STYLESTACK_CARRIERS.items():
            if format in info['formats']:
                carriers.append(carrier)
        return carriers