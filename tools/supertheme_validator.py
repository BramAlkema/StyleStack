"""
StyleStack SuperTheme Package Validator

Comprehensive validation system for Microsoft SuperTheme packages (.thmx files).
Ensures compatibility with Office 2016-365 and validates structure integrity.

Features:
- Complete package structure validation
- XML schema compliance checking  
- Office namespace requirements verification
- GUID format validation
- File size and performance validation
- Cross-platform compatibility checks

Usage:
    validator = SuperThemeValidator()
    result = validator.validate_package(supertheme_bytes)
    if result.is_valid:
        print("SuperTheme package is valid!")
    else:
        for error in result.errors:
            print(f"Error: {error}")
"""

# Use shared utilities to eliminate duplication
from tools.core import (
    zipfile, Path, get_logger, List, Dict, Any, Optional, Tuple,
    ValidationResult, ValidationError as CoreValidationError,
    safe_ooxml_reader, error_boundary, handle_processing_error
)
import io
import re
import hashlib

# Use lxml for robust XML processing
try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    import xml.etree.ElementTree as etree
    LXML_AVAILABLE = False

logger = get_logger(__name__)


# Using shared ValidationResult from tools.core - eliminates duplicate class
# Extended with SuperTheme-specific metadata fields

class SuperThemeValidationResult(ValidationResult):
    """Extended validation result for SuperTheme packages"""
    
    def __init__(self):
        super().__init__()
        self.metadata.update({
            'package_size_mb': 0.0,
            'variant_count': 0,
            'file_count': 0
        })
    
    @property
    def package_size_mb(self) -> float:
        return self.metadata.get('package_size_mb', 0.0)
    
    @package_size_mb.setter 
    def package_size_mb(self, value: float):
        self.metadata['package_size_mb'] = value
    
    @property
    def variant_count(self) -> int:
        return self.metadata.get('variant_count', 0)
    
    @variant_count.setter
    def variant_count(self, value: int):
        self.metadata['variant_count'] = value
        
    @property
    def file_count(self) -> int:
        return self.metadata.get('file_count', 0)
    
    @file_count.setter
    def file_count(self, value: int):
        self.metadata['file_count'] = value
    
    def add_supertheme_error(self, category: str, message: str, file_path: str = None, **context):
        """Add SuperTheme-specific validation error"""
        full_context = {'category': category, 'file_path': file_path}
        full_context.update(context)
        self.add_error(
            field=category,
            message=message,
            code=f"SUPERTHEME_{category.upper()}",
            context=full_context
        )
    
    def add_supertheme_warning(self, category: str, message: str, file_path: str = None, **context):
        """Add SuperTheme-specific validation warning"""
        full_context = {'category': category, 'file_path': file_path}
        full_context.update(context)
        self.add_warning(
            field=category,
            message=message,
            code=f"SUPERTHEME_{category.upper()}",
            context=full_context
        )


class SuperThemeValidator:
    """
    Comprehensive SuperTheme package validator for Office compatibility.
    
    Validates:
    - Package structure and required files
    - XML schema compliance and well-formedness  
    - Office namespace requirements
    - GUID format compliance
    - File size limits
    - Cross-platform compatibility
    """
    
    # Required file patterns for valid SuperTheme
    REQUIRED_FILES = [
        "[Content_Types].xml",
        "_rels/.rels",
        "themeVariants/themeVariantManager.xml",
        "themeVariants/_rels/themeVariantManager.xml.rels"
    ]
    
    # Required namespaces for Office compatibility
    REQUIRED_NAMESPACES = {
        "supertheme": "http://schemas.microsoft.com/office/thememl/2012/main",
        "relationships": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "drawingml": "http://schemas.openxmlformats.org/drawingml/2006/main",
        "presentationml": "http://schemas.openxmlformats.org/presentationml/2006/main"
    }
    
    # Required content types
    REQUIRED_CONTENT_TYPES = [
        "application/vnd.openxmlformats-package.relationships+xml",
        "application/vnd.ms-powerpoint.themeVariantManager+xml",
        "application/vnd.openxmlformats-officedocument.theme+xml"
    ]
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize validator.
        
        Args:
            strict_mode: If True, apply stricter validation rules
        """
        self.strict_mode = strict_mode
        self.guid_pattern = re.compile(
            r'\{[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}\}',
            re.IGNORECASE
        )
    
    def validate_package(self, package_data: bytes) -> SuperThemeValidationResult:
        """
        Validate complete SuperTheme package.
        
        Args:
            package_data: SuperTheme package bytes
            
        Returns:
            ValidationResult with all validation findings
        """
        result = SuperThemeValidationResult()
        result.package_size_mb = len(package_data) / (1024 * 1024)
        
        try:
            # Basic ZIP validation
            with zipfile.ZipFile(io.BytesIO(package_data), 'r') as zf:
                result.file_count = len(zf.namelist())
                
                # Test ZIP integrity
                try:
                    zf.testzip()
                except Exception as e:
                    result.add_error("structure", f"ZIP integrity check failed: {e}")
                    return result
                
                # Validate package structure
                self._validate_package_structure(zf, result)
                
                # Validate content types
                self._validate_content_types(zf, result)
                
                # Validate theme variant manager
                self._validate_theme_variant_manager(zf, result)
                
                # Validate individual variants
                self._validate_theme_variants(zf, result)
                
                # Validate XML files
                self._validate_xml_files(zf, result)
                
                # Validate relationships
                self._validate_relationships(zf, result)
                
                # Performance and size validation
                self._validate_performance(zf, result)
                
                # Cross-platform compatibility
                self._validate_cross_platform(zf, result)
        
        except zipfile.BadZipFile:
            result.add_error("structure", "Invalid ZIP file format")
        except Exception as e:
            result.add_error("general", f"Validation failed: {e}")
        
        return result
    
    def _validate_package_structure(self, zf: zipfile.ZipFile, result: ValidationResult):
        """Validate required package structure"""
        file_list = zf.namelist()
        
        # Check required files
        for required_file in self.REQUIRED_FILES:
            if not any(required_file in f or f == required_file for f in file_list):
                result.add_error("structure", f"Missing required file: {required_file}")
        
        # Check for theme variants
        variant_dirs = set()
        for file_path in file_list:
            if 'themeVariants/variant' in file_path:
                parts = file_path.split('/')
                if len(parts) >= 2 and parts[1].startswith('variant'):
                    variant_dirs.add(parts[1])
        
        result.variant_count = len(variant_dirs)
        
        if result.variant_count == 0:
            result.add_error("structure", "No theme variants found in package")
        else:
            result.add_info("structure", f"Found {result.variant_count} theme variants")
        
        # Check each variant has required structure
        for variant_dir in variant_dirs:
            required_variant_files = [
                f"themeVariants/{variant_dir}/theme/theme/theme1.xml",
                f"themeVariants/{variant_dir}/theme/presentation.xml"
            ]
            
            for req_file in required_variant_files:
                if req_file not in file_list:
                    result.add_error("structure", f"Missing {req_file} in {variant_dir}")
    
    def _validate_content_types(self, zf: zipfile.ZipFile, result: ValidationResult):
        """Validate [Content_Types].xml"""
        try:
            content_types_xml = zf.read('[Content_Types].xml').decode('utf-8')
            if LXML_AVAILABLE:
                parser = etree.XMLParser(recover=True, remove_comments=False)
                root = etree.fromstring(content_types_xml.encode('utf-8'), parser)
            else:
                root = etree.fromstring(content_types_xml)
            
            # Extract all content types
            content_types = []
            for elem in root:
                content_type = elem.get('ContentType')
                if content_type:
                    content_types.append(content_type)
            
            # Check required content types
            for required_type in self.REQUIRED_CONTENT_TYPES:
                if required_type not in content_types:
                    result.add_error("content_types", 
                                   f"Missing content type: {required_type}")
            
            # Check for proper xmlns
            if 'xmlns=' not in content_types_xml:
                result.add_warning("content_types", "Missing xmlns declaration")
        
        except Exception as e:
            result.add_error("content_types", f"Failed to parse [Content_Types].xml: {e}")
    
    def _validate_theme_variant_manager(self, zf: zipfile.ZipFile, result: ValidationResult):
        """Validate themeVariantManager.xml"""
        try:
            manager_xml = zf.read('themeVariants/themeVariantManager.xml').decode('utf-8')
            if LXML_AVAILABLE:
                parser = etree.XMLParser(recover=True, remove_comments=False)
                root = etree.fromstring(manager_xml.encode('utf-8'), parser)
            else:
                root = etree.fromstring(manager_xml)
            
            # Check required namespaces
            for ns_name, ns_uri in self.REQUIRED_NAMESPACES.items():
                if ns_uri not in manager_xml:
                    result.add_error("namespaces", 
                                   f"Missing {ns_name} namespace: {ns_uri}",
                                   "themeVariants/themeVariantManager.xml")
            
            # Check for themeVariantLst
            variant_list = root.find('.//{http://schemas.microsoft.com/office/thememl/2012/main}themeVariantLst')
            if variant_list is None:
                # Try without namespace
                variant_list = root.find('.//themeVariantLst')
            
            if variant_list is None:
                result.add_error("structure", "Missing themeVariantLst element",
                               "themeVariants/themeVariantManager.xml")
            else:
                # Validate each variant entry
                variants = variant_list.findall('.//*[@vid]')
                if len(variants) == 0:
                    result.add_warning("structure", "No theme variants in manager",
                                     "themeVariants/themeVariantManager.xml")
                
                # Validate GUIDs
                for variant in variants:
                    guid = variant.get('vid')
                    if not self._is_valid_guid(guid):
                        result.add_error("guids", f"Invalid GUID format: {guid}",
                                       "themeVariants/themeVariantManager.xml")
        
        except Exception as e:
            result.add_error("parsing", f"Failed to parse themeVariantManager.xml: {e}")
    
    def _validate_theme_variants(self, zf: zipfile.ZipFile, result: ValidationResult):
        """Validate individual theme variants"""
        file_list = zf.namelist()
        variant_dirs = set()
        
        for file_path in file_list:
            if 'themeVariants/variant' in file_path:
                parts = file_path.split('/')
                if len(parts) >= 2 and parts[1].startswith('variant'):
                    variant_dirs.add(parts[1])
        
        for variant_dir in variant_dirs:
            # Validate theme XML
            theme_path = f"themeVariants/{variant_dir}/theme/theme/theme1.xml"
            if theme_path in file_list:
                try:
                    theme_xml = zf.read(theme_path).decode('utf-8')
                    if LXML_AVAILABLE:
                        parser = etree.XMLParser(recover=True, remove_comments=False)
                        theme_root = etree.fromstring(theme_xml.encode('utf-8'), parser)
                    else:
                        theme_root = etree.fromstring(theme_xml)
                    
                    # Check for required theme elements
                    required_elements = [
                        './/themeElements',
                        './/clrScheme',
                        './/fontScheme'
                    ]
                    
                    for element_path in required_elements:
                        if theme_root.find(element_path) is None:
                            # Try with namespace - fix the XPath construction
                            element_name = element_path.replace('.//', '')
                            ns_path = f'.//{{{self.REQUIRED_NAMESPACES["drawingml"]}}}{element_name}'
                            if theme_root.find(ns_path) is None:
                                result.add_warning("theme", 
                                                  f"Missing {element_name} in theme",
                                                  theme_path)
                
                except Exception as e:
                    result.add_error("parsing", f"Failed to parse theme XML: {e}", theme_path)
            
            # Validate presentation XML
            pres_path = f"themeVariants/{variant_dir}/theme/presentation.xml"
            if pres_path in file_list:
                try:
                    pres_xml = zf.read(pres_path).decode('utf-8')
                    if LXML_AVAILABLE:
                        parser = etree.XMLParser(recover=True, remove_comments=False)
                        pres_root = etree.fromstring(pres_xml.encode('utf-8'), parser)
                    else:
                        pres_root = etree.fromstring(pres_xml)
                    
                    # Check slide size is defined
                    slide_size = pres_root.find('.//sldSz')
                    if slide_size is None:
                        # Try with namespace
                        slide_size = pres_root.find(f'.//{{{self.REQUIRED_NAMESPACES["presentationml"]}}}sldSz')
                    
                    if slide_size is None:
                        result.add_warning("presentation", "Missing slide size definition", pres_path)
                    else:
                        # Validate dimensions
                        width = slide_size.get('cx')
                        height = slide_size.get('cy')
                        if not width or not height:
                            result.add_error("presentation", "Missing slide dimensions", pres_path)
                        elif not width.isdigit() or not height.isdigit():
                            result.add_error("presentation", "Invalid slide dimensions", pres_path)
                
                except Exception as e:
                    result.add_error("parsing", f"Failed to parse presentation XML: {e}", pres_path)
    
    def _validate_xml_files(self, zf: zipfile.ZipFile, result: ValidationResult):
        """Validate all XML files are well-formed"""
        xml_files = [f for f in zf.namelist() if f.endswith('.xml')]
        
        for xml_file in xml_files:
            try:
                xml_content = zf.read(xml_file).decode('utf-8')
                if LXML_AVAILABLE:
                    parser = etree.XMLParser(recover=True, remove_comments=False)
                    etree.fromstring(xml_content.encode('utf-8'), parser)
                else:
                    etree.fromstring(xml_content)
                
                # Check for XML declaration
                if not xml_content.strip().startswith('<?xml'):
                    result.add_warning("xml", f"Missing XML declaration", xml_file)
                
            except (etree.XMLSyntaxError if LXML_AVAILABLE else etree.ParseError) as e:
                result.add_error("xml", f"XML parse error: {e}", xml_file)
            except UnicodeDecodeError as e:
                result.add_error("encoding", f"Character encoding error: {e}", xml_file)
    
    def _validate_relationships(self, zf: zipfile.ZipFile, result: ValidationResult):
        """Validate relationship files"""
        rels_files = [f for f in zf.namelist() if f.endswith('.rels')]
        
        for rels_file in rels_files:
            try:
                rels_xml = zf.read(rels_file).decode('utf-8')
                if LXML_AVAILABLE:
                    parser = etree.XMLParser(recover=True, remove_comments=False)
                    root = etree.fromstring(rels_xml.encode('utf-8'), parser)
                else:
                    root = etree.fromstring(rels_xml)
                
                # Check namespace
                if self.REQUIRED_NAMESPACES["relationships"] not in rels_xml:
                    result.add_warning("relationships", "Missing relationships namespace", rels_file)
                
                # Check for at least one relationship
                relationships = root.findall('.//Relationship')
                if len(relationships) == 0:
                    # Try with namespace
                    ns_relationships = root.findall(f'.//{{{self.REQUIRED_NAMESPACES["relationships"]}}}Relationship')
                    if len(ns_relationships) == 0:
                        result.add_warning("relationships", "No relationships found", rels_file)
                    else:
                        relationships = ns_relationships
                
                # Validate relationship attributes
                for rel in relationships:
                    if not rel.get('Id'):
                        result.add_error("relationships", "Missing relationship Id", rels_file)
                    if not rel.get('Target'):
                        result.add_error("relationships", "Missing relationship Target", rels_file)
            
            except Exception as e:
                result.add_error("parsing", f"Failed to parse relationships: {e}", rels_file)
    
    def _validate_performance(self, zf: zipfile.ZipFile, result: ValidationResult):
        """Validate performance characteristics"""
        # File size validation
        if result.package_size_mb > 5.0:
            result.add_warning("performance", 
                             f"Package size {result.package_size_mb:.2f}MB exceeds 5MB recommendation")
        elif result.package_size_mb > 10.0:
            result.add_error("performance", 
                           f"Package size {result.package_size_mb:.2f}MB exceeds 10MB limit")
        
        # File count validation
        if result.file_count > 1000:
            result.add_warning("performance", 
                             f"High file count ({result.file_count}) may impact performance")
        
        # Check for large individual files
        for file_info in zf.infolist():
            file_size_mb = file_info.file_size / (1024 * 1024)
            if file_size_mb > 1.0:
                result.add_warning("performance", 
                                 f"Large file: {file_info.filename} ({file_size_mb:.2f}MB)")
    
    def _validate_cross_platform(self, zf: zipfile.ZipFile, result: ValidationResult):
        """Validate cross-platform compatibility"""
        for file_path in zf.namelist():
            # Check for Windows-specific path separators
            if '\\' in file_path:
                result.add_error("compatibility", f"Windows path separator in: {file_path}")
            
            # Check for absolute paths
            if file_path.startswith('/'):
                result.add_error("compatibility", f"Absolute path: {file_path}")
            
            # Check for parent directory references
            if '..' in file_path:
                result.add_error("compatibility", f"Parent directory reference: {file_path}")
            
            # Check filename for invalid characters
            filename = Path(file_path).name
            invalid_chars = '<>:"|?*'
            for char in invalid_chars:
                if char in filename:
                    result.add_error("compatibility", 
                                   f"Invalid character '{char}' in filename: {filename}")
    
    def _is_valid_guid(self, guid: str) -> bool:
        """Validate GUID format"""
        if not guid:
            return False
        return bool(self.guid_pattern.match(guid))
    
    def generate_validation_report(self, result: ValidationResult) -> str:
        """Generate human-readable validation report"""
        report = ["SuperTheme Validation Report", "=" * 40]
        
        # Summary
        status = "✅ VALID" if result.is_valid else "❌ INVALID"
        report.append(f"Status: {status}")
        report.append(f"Package Size: {result.package_size_mb:.2f} MB")
        report.append(f"Variants: {result.variant_count}")
        report.append(f"Files: {result.file_count}")
        report.append("")
        
        # Errors
        if result.errors:
            report.append(f"❌ Errors ({len(result.errors)}):")
            for error in result.errors:
                file_info = f" in {error.file_path}" if error.file_path else ""
                report.append(f"  • [{error.category}] {error.message}{file_info}")
            report.append("")
        
        # Warnings
        if result.warnings:
            report.append(f"⚠️  Warnings ({len(result.warnings)}):")
            for warning in result.warnings:
                file_info = f" in {warning.file_path}" if warning.file_path else ""
                report.append(f"  • [{warning.category}] {warning.message}{file_info}")
            report.append("")
        
        # Info
        if result.info:
            report.append(f"ℹ️  Information ({len(result.info)}):")
            for info in result.info:
                file_info = f" in {info.file_path}" if info.file_path else ""
                report.append(f"  • [{info.category}] {info.message}{file_info}")
            report.append("")
        
        if result.is_valid:
            report.append("🎉 SuperTheme package is valid and ready for use!")
        else:
            report.append("❌ SuperTheme package has validation errors that should be fixed.")
        
        return "\n".join(report)


if __name__ == "__main__":
    # Demo validation
    print("🔍 SuperTheme Validator Demo")
    
    # Example usage with generated SuperTheme
    try:
        from tools.supertheme_generator import SuperThemeGenerator
        
        generator = SuperThemeGenerator(verbose=True)
        design_variants = {
            "Demo Design": {
                "colors": {"brand": {"primary": "#0066CC"}},
                "typography": {"heading": {"font": "Arial"}}
            }
        }
        
        # Generate SuperTheme
        supertheme_bytes = generator.generate_supertheme(design_variants)
        
        # Validate it
        validator = SuperThemeValidator()
        result = validator.validate_package(supertheme_bytes)
        
        # Print report
        print(validator.generate_validation_report(result))
        
    except ImportError:
        print("SuperTheme generator not available for demo")
        print("Run: python -c \"from tools.supertheme_validator import SuperThemeValidator; print('Validator loaded successfully')\"")