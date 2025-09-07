"""
OOXML Extension Manager for StyleStack Variables

Production implementation for reading, writing, and managing OOXML <extLst> 
elements to embed StyleStack variables directly in Office templates while
maintaining round-trip editing compatibility.

Features:
- Native OOXML extension list manipulation
- StyleStack variable embedding with JSON and XML formats
- Extension versioning and compatibility management
- Multiple extension coexistence support
- Office application compatibility preservation

Usage:
    manager = OOXMLExtensionManager()
    
    # Read extensions from OOXML file
    with zipfile.ZipFile('template.potx', 'r') as zf:
        theme_xml = zf.read('ppt/theme/theme1.xml').decode('utf-8')
        extensions = manager.read_extensions_from_xml(theme_xml)
    
    # Add StyleStack variables
    extension = StyleStackExtension(
        uri=STYLESTACK_EXTENSION_URI,
        variables=[{'id': 'brandColor', 'type': 'color', 'scope': 'org'}]
    )
    
    updated_xml = manager.write_extension_to_xml(theme_xml, extension)
"""

import xml.etree.ElementTree as ET
import json
import zipfile
import io
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
import uuid
from datetime import datetime
import logging


# Configure logging
logger = logging.getLogger(__name__)

# OOXML Namespace definitions for all Office document types
OOXML_NAMESPACES = {
    # Core DrawingML
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'a14': 'http://schemas.microsoft.com/office/drawing/2010/main',
    'a16': 'http://schemas.microsoft.com/office/drawing/2014/main',
    
    # PresentationML (PowerPoint)
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'p14': 'http://schemas.microsoft.com/office/powerpoint/2010/main',
    
    # WordprocessingML (Word)
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'w14': 'http://schemas.microsoft.com/office/word/2010/wordml',
    
    # SpreadsheetML (Excel) 
    'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
    'x14': 'http://schemas.microsoft.com/office/spreadsheetml/2009/9/main',
    
    # Common
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
    
    # StyleStack
    'stylestack': 'https://stylestack.org/extensions/variables/v1'
}

# StyleStack extension URIs for different versions
STYLESTACK_EXTENSION_URIS = {
    '1.0': 'https://stylestack.org/extensions/variables/v1.0',
    '1.1': 'https://stylestack.org/extensions/variables/v1.1',
    'latest': 'https://stylestack.org/extensions/variables/v1'
}

# Default extension URI
STYLESTACK_EXTENSION_URI = STYLESTACK_EXTENSION_URIS['latest']


@dataclass
class ExtensionMetadata:
    """Metadata for StyleStack extensions"""
    author: Optional[str] = None
    description: Optional[str] = None
    created: Optional[str] = None
    modified: Optional[str] = None
    version: str = "1.0"
    schema_version: str = "1.0"
    
    def __post_init__(self):
        if self.created is None:
            self.created = datetime.now().isoformat()
        if self.modified is None:
            self.modified = self.created


@dataclass
class StyleStackExtension:
    """
    Represents a StyleStack variable extension in OOXML.
    
    Contains variables definitions that will be embedded in OOXML
    documents using the native extension mechanism.
    """
    uri: str
    variables: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Optional[ExtensionMetadata] = None
    format_version: str = "1.0"
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = ExtensionMetadata()
        
        # Ensure URI is valid
        if not self.uri or not self.uri.startswith('http'):
            self.uri = STYLESTACK_EXTENSION_URI
    
    def add_variable(self, variable: Dict[str, Any]) -> None:
        """Add a variable to the extension"""
        # Validate required fields
        required_fields = ['id', 'type', 'scope']
        for field in required_fields:
            if field not in variable:
                raise ValueError(f"Variable missing required field: {field}")
        
        self.variables.append(variable)
        self.metadata.modified = datetime.now().isoformat()
    
    def remove_variable(self, variable_id: str) -> bool:
        """Remove variable by ID"""
        original_count = len(self.variables)
        self.variables = [v for v in self.variables if v.get('id') != variable_id]
        
        if len(self.variables) < original_count:
            self.metadata.modified = datetime.now().isoformat()
            return True
        return False
    
    def get_variable(self, variable_id: str) -> Optional[Dict[str, Any]]:
        """Get variable by ID"""
        for var in self.variables:
            if var.get('id') == variable_id:
                return var
        return None
    
    def to_json(self) -> str:
        """Serialize extension to JSON"""
        data = {
            'uri': self.uri,
            'format_version': self.format_version,
            'metadata': asdict(self.metadata),
            'variables': self.variables
        }
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_data: str) -> 'StyleStackExtension':
        """Deserialize extension from JSON"""
        try:
            data = json.loads(json_data)
            
            metadata_data = data.get('metadata', {})
            metadata = ExtensionMetadata(**metadata_data)
            
            return cls(
                uri=data.get('uri', STYLESTACK_EXTENSION_URI),
                variables=data.get('variables', []),
                metadata=metadata,
                format_version=data.get('format_version', '1.0')
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON data: {e}")


class OOXMLExtensionManager:
    """
    Advanced OOXML extension manager with versioning and compatibility.
    
    Handles the complete lifecycle of StyleStack extensions in OOXML documents:
    - Reading existing extensions from various OOXML file types
    - Writing new extensions with proper namespace handling
    - Version management and backward compatibility
    - Extension coexistence with other Office add-ins
    - Document structure preservation
    """
    
    def __init__(self, preserve_formatting: bool = True):
        """
        Initialize extension manager.
        
        Args:
            preserve_formatting: Whether to preserve XML formatting and whitespace
        """
        self.namespaces = OOXML_NAMESPACES.copy()
        self.preserve_formatting = preserve_formatting
        
        # Register namespaces for ElementTree
        for prefix, uri in self.namespaces.items():
            try:
                ET.register_namespace(prefix, uri)
            except ValueError:
                # Namespace already registered
                pass
        
        # File type detection patterns
        self.file_patterns = {
            'theme': ['theme/theme1.xml', 'theme1.xml'],
            'slidemaster': ['slideMasters/slideMaster', 'slidemaster'],
            'layout': ['slideLayouts/slideLayout', 'slidelayout'],
            'slide': ['slides/slide', 'slide'],
            'document': ['document.xml'],
            'styles': ['styles.xml'],
            'workbook': ['workbook.xml'],
            'worksheet': ['worksheets/sheet']
        }
    
    def read_extensions_from_ooxml_file(self, file_path: Union[str, Path]) -> Dict[str, List[StyleStackExtension]]:
        """
        Read all StyleStack extensions from an OOXML file.
        
        Args:
            file_path: Path to OOXML file (.potx, .dotx, .xltx, etc.)
            
        Returns:
            Dictionary mapping file paths to lists of extensions found
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"OOXML file not found: {file_path}")
        
        extensions_by_file = {}
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                # Check common extension locations
                files_to_check = self._get_extension_files(zf)
                
                for internal_path in files_to_check:
                    try:
                        xml_content = zf.read(internal_path).decode('utf-8')
                        extensions = self.read_extensions_from_xml(xml_content)
                        
                        if extensions:
                            extensions_by_file[internal_path] = extensions
                            logger.info(f"Found {len(extensions)} StyleStack extensions in {internal_path}")
                            
                    except (KeyError, UnicodeDecodeError) as e:
                        logger.debug(f"Could not read {internal_path}: {e}")
                        continue
                        
        except zipfile.BadZipFile:
            raise ValueError(f"Invalid OOXML file: {file_path}")
        
        return extensions_by_file
    
    def _get_extension_files(self, zf: zipfile.ZipFile) -> List[str]:
        """Get list of files that might contain extensions"""
        all_files = zf.namelist()
        extension_files = []
        
        # Add files that commonly contain extensions
        common_paths = [
            'ppt/theme/theme1.xml',
            'ppt/slideMasters/slideMaster1.xml',
            'word/theme/theme1.xml', 
            'word/styles.xml',
            'xl/theme/theme1.xml',
            'xl/styles.xml'
        ]
        
        for path in common_paths:
            if path in all_files:
                extension_files.append(path)
        
        # Also check any file ending with .xml that might have extensions
        for file_path in all_files:
            if (file_path.endswith('.xml') and 
                'extLst' in file_path.lower() or 
                any(pattern in file_path for pattern in ['theme', 'master', 'style'])):
                if file_path not in extension_files:
                    extension_files.append(file_path)
        
        return extension_files
    
    def read_extensions_from_xml(self, xml_content: str) -> List[StyleStackExtension]:
        """
        Extract StyleStack extensions from XML content.
        
        Args:
            xml_content: Raw XML content from OOXML document
            
        Returns:
            List of StyleStack extensions found
        """
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML content: {e}")
        
        extensions = []
        
        # Find all extLst elements
        ext_lists = root.findall('.//{*}extLst')
        
        for ext_list in ext_lists:
            # Find extensions with StyleStack URIs
            for ext in ext_list.findall('./{*}ext'):
                uri = ext.get('uri', '')
                
                if self._is_stylestack_uri(uri):
                    try:
                        extension = self._parse_stylestack_extension(ext, uri)
                        if extension:
                            extensions.append(extension)
                            logger.debug(f"Parsed StyleStack extension: {uri}")
                    except Exception as e:
                        logger.warning(f"Failed to parse StyleStack extension {uri}: {e}")
                        continue
        
        return extensions
    
    def _is_stylestack_uri(self, uri: str) -> bool:
        """Check if URI is a StyleStack extension URI"""
        return (uri and 
                ('stylestack.org' in uri.lower() or 
                 'stylestack' in uri.lower() and 'variables' in uri.lower()))
    
    def _parse_stylestack_extension(self, ext_element: ET.Element, uri: str) -> Optional[StyleStackExtension]:
        """Parse a StyleStack extension element"""
        # Look for StyleStack extension content
        for child in ext_element:
            # Try JSON format first
            if child.text and child.text.strip().startswith('{'):
                try:
                    return StyleStackExtension.from_json(child.text.strip())
                except ValueError:
                    pass
            
            # Try XML format
            if 'variables' in child.tag.lower() or 'stylestack' in child.tag.lower():
                return self._parse_xml_format_extension(child, uri)
        
        # Fallback: empty extension
        return StyleStackExtension(uri=uri)
    
    def _parse_xml_format_extension(self, element: ET.Element, uri: str) -> StyleStackExtension:
        """Parse XML format StyleStack extension"""
        variables = []
        metadata_dict = {}
        
        # Parse metadata
        for meta_elem in element.findall('.//{*}metadata'):
            for attr_name, attr_value in meta_elem.attrib.items():
                metadata_dict[attr_name] = attr_value
        
        # Parse variables
        for var_elem in element.findall('.//{*}variable'):
            var_data = dict(var_elem.attrib)
            
            # Parse nested elements
            for child in var_elem:
                tag_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                if child.text:
                    var_data[tag_name] = child.text.strip()
                elif child.attrib:
                    var_data[tag_name] = dict(child.attrib)
            
            if var_data:  # Only add if variable has data
                variables.append(var_data)
        
        # Create metadata object
        metadata = ExtensionMetadata(**metadata_dict) if metadata_dict else ExtensionMetadata()
        
        return StyleStackExtension(
            uri=uri,
            variables=variables,
            metadata=metadata
        )
    
    def write_extension_to_xml(self, xml_content: str, extension: StyleStackExtension, 
                             format: str = 'json') -> str:
        """
        Add StyleStack extension to XML content.
        
        Args:
            xml_content: Original XML content
            extension: StyleStack extension to add
            format: 'json' or 'xml' format for extension data
            
        Returns:
            Updated XML content with extension added
        """
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML content: {e}")
        
        # Find or create extLst element
        ext_list = self._find_or_create_extension_list(root)
        
        # Remove existing StyleStack extension with same URI
        self._remove_existing_stylestack_extension(ext_list, extension.uri)
        
        # Create new extension element
        ext_elem = self._create_extension_element(ext_list, extension, format)
        
        # Generate updated XML
        if self.preserve_formatting:
            return self._format_xml_output(root)
        else:
            return ET.tostring(root, encoding='unicode')
    
    def _find_or_create_extension_list(self, root: ET.Element) -> ET.Element:
        """Find existing extLst or create new one in appropriate location"""
        # Look for existing extLst
        ext_list = root.find('.//{*}extLst')
        if ext_list is not None:
            return ext_list
        
        # Create new extLst based on document type
        return self._create_extension_list_for_document_type(root)
    
    def _create_extension_list_for_document_type(self, root: ET.Element) -> ET.Element:
        """Create extLst element appropriate for document type"""
        root_tag = root.tag.lower()
        
        if 'theme' in root_tag:
            # Theme document - add after themeElements
            theme_elements = root.find('.//{*}themeElements')
            if theme_elements is not None:
                parent = theme_elements.getparent() or root
                index = list(parent).index(theme_elements) + 1
                ext_list = ET.Element(f"{{{self.namespaces['a']}}}extLst")
                parent.insert(index, ext_list)
            else:
                ext_list = ET.SubElement(root, f"{{{self.namespaces['a']}}}extLst")
                
        elif 'sldmaster' in root_tag or 'slidemaster' in root_tag:
            # Slide master - add at appropriate location
            ext_list = ET.SubElement(root, f"{{{self.namespaces['p']}}}extLst")
            
        elif 'document' in root_tag:
            # Word document
            ext_list = ET.SubElement(root, f"{{{self.namespaces['w']}}}extLst")
            
        elif 'workbook' in root_tag or 'worksheet' in root_tag:
            # Excel
            ext_list = ET.SubElement(root, f"{{{self.namespaces['x']}}}extLst")
            
        else:
            # Default to DrawingML namespace
            ext_list = ET.SubElement(root, f"{{{self.namespaces['a']}}}extLst")
        
        return ext_list
    
    def _remove_existing_stylestack_extension(self, ext_list: ET.Element, uri: str) -> None:
        """Remove existing StyleStack extension with same URI"""
        for ext in ext_list.findall('./{*}ext'):
            if ext.get('uri') == uri:
                ext_list.remove(ext)
                logger.debug(f"Removed existing StyleStack extension: {uri}")
    
    def _create_extension_element(self, ext_list: ET.Element, extension: StyleStackExtension, 
                                format: str) -> ET.Element:
        """Create extension element with specified format"""
        # Determine namespace for ext element
        parent_ns = ext_list.tag.split('}')[0].lstrip('{')
        ext_elem = ET.SubElement(ext_list, f"{{{parent_ns}}}ext")
        ext_elem.set('uri', extension.uri)
        
        if format == 'json':
            # JSON format - compact and widely supported
            data_elem = ET.SubElement(ext_elem, f"{{{self.namespaces['stylestack']}}}variables")
            data_elem.set('xmlns:stylestack', self.namespaces['stylestack'])
            data_elem.text = extension.to_json()
            
        else:
            # XML format - more verbose but structured
            vars_elem = ET.SubElement(ext_elem, f"{{{self.namespaces['stylestack']}}}variables")
            vars_elem.set('xmlns:stylestack', self.namespaces['stylestack'])
            vars_elem.set('version', extension.format_version)
            
            # Add metadata
            if extension.metadata:
                meta_elem = ET.SubElement(vars_elem, f"{{{self.namespaces['stylestack']}}}metadata")
                meta_dict = asdict(extension.metadata)
                for key, value in meta_dict.items():
                    if value is not None:
                        meta_elem.set(key, str(value))
            
            # Add variables
            for variable in extension.variables:
                var_elem = ET.SubElement(vars_elem, f"{{{self.namespaces['stylestack']}}}variable")
                for key, value in variable.items():
                    if isinstance(value, (str, int, float, bool)):
                        var_elem.set(key, str(value))
                    elif isinstance(value, dict):
                        # Nested object as child element
                        child_elem = ET.SubElement(var_elem, key)
                        for child_key, child_value in value.items():
                            child_elem.set(child_key, str(child_value))
        
        return ext_elem
    
    def _format_xml_output(self, root: ET.Element) -> str:
        """Format XML output with proper indentation"""
        # Add indentation
        self._indent_xml(root)
        
        # Generate XML with declaration
        xml_str = ET.tostring(root, encoding='unicode')
        
        # Add XML declaration if not present
        if not xml_str.startswith('<?xml'):
            xml_str = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + xml_str
        
        return xml_str
    
    def _indent_xml(self, elem: ET.Element, level: int = 0) -> None:
        """Add indentation to XML elements"""
        indent = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                self._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent
    
    def remove_extension(self, xml_content: str, extension_uri: str) -> str:
        """Remove extension by URI from XML content"""
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML content: {e}")
        
        removed_count = 0
        
        # Find and remove matching extensions
        for ext_list in root.findall('.//{*}extLst'):
            for ext in ext_list.findall('./{*}ext'):
                if ext.get('uri') == extension_uri:
                    ext_list.remove(ext)
                    removed_count += 1
            
            # Remove empty extLst elements
            if len(ext_list) == 0:
                parent = ext_list.getparent()
                if parent is not None:
                    parent.remove(ext_list)
        
        logger.info(f"Removed {removed_count} extensions with URI: {extension_uri}")
        
        if self.preserve_formatting:
            return self._format_xml_output(root)
        else:
            return ET.tostring(root, encoding='unicode')
    
    def list_all_extensions(self, xml_content: str) -> List[Dict[str, Any]]:
        """List all extensions in XML content with details"""
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML content: {e}")
        
        extensions = []
        
        for ext_list in root.findall('.//{*}extLst'):
            for ext in ext_list.findall('./{*}ext'):
                uri = ext.get('uri', '')
                
                extension_info = {
                    'uri': uri,
                    'is_stylestack': self._is_stylestack_uri(uri),
                    'has_content': len(list(ext)) > 0,
                    'element_count': len(list(ext)),
                    'attributes': dict(ext.attrib)
                }
                
                # If it's a StyleStack extension, get more details
                if extension_info['is_stylestack']:
                    try:
                        stylestack_ext = self._parse_stylestack_extension(ext, uri)
                        if stylestack_ext:
                            extension_info.update({
                                'variable_count': len(stylestack_ext.variables),
                                'version': stylestack_ext.metadata.version if stylestack_ext.metadata else 'unknown',
                                'format_version': stylestack_ext.format_version
                            })
                    except Exception:
                        pass
                
                extensions.append(extension_info)
        
        return extensions
    
    def validate_extension_compatibility(self, xml_content: str) -> Dict[str, Any]:
        """Validate extension compatibility and structure"""
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            return {'valid': False, 'errors': [f'Invalid XML: {e}']}
        
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'extensions': [],
            'compatibility': {
                'office_2016': True,
                'office_2019': True,
                'office_365': True,
                'libreoffice': False  # Extensions not fully supported
            }
        }
        
        # Check extension structure
        for ext_list in root.findall('.//{*}extLst'):
            for ext in ext_list.findall('./{*}ext'):
                uri = ext.get('uri', '')
                
                if not uri:
                    validation_result['errors'].append('Extension missing required uri attribute')
                    validation_result['valid'] = False
                    continue
                
                if self._is_stylestack_uri(uri):
                    # Validate StyleStack extension
                    ext_validation = self._validate_stylestack_extension(ext, uri)
                    validation_result['extensions'].append(ext_validation)
                    
                    if not ext_validation['valid']:
                        validation_result['valid'] = False
                        validation_result['errors'].extend(ext_validation['errors'])
                    
                    if ext_validation['warnings']:
                        validation_result['warnings'].extend(ext_validation['warnings'])
        
        return validation_result
    
    def _validate_stylestack_extension(self, ext_element: ET.Element, uri: str) -> Dict[str, Any]:
        """Validate individual StyleStack extension"""
        result = {
            'uri': uri,
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            extension = self._parse_stylestack_extension(ext_element, uri)
            
            if not extension:
                result['valid'] = False
                result['errors'].append('Could not parse StyleStack extension content')
                return result
            
            # Validate variables
            if not extension.variables:
                result['warnings'].append('Extension contains no variables')
            
            for i, variable in enumerate(extension.variables):
                # Check required fields
                required_fields = ['id', 'type', 'scope']
                for field in required_fields:
                    if field not in variable:
                        result['errors'].append(f'Variable {i} missing required field: {field}')
                        result['valid'] = False
                
                # Validate variable types
                valid_types = ['color', 'font', 'number', 'text', 'dimension', 'boolean', 'calculated']
                if 'type' in variable and variable['type'] not in valid_types:
                    result['warnings'].append(f'Variable {i} has unknown type: {variable["type"]}')
                
                # Validate scopes
                valid_scopes = ['core', 'fork', 'org', 'group', 'user', 'theme']
                if 'scope' in variable and variable['scope'] not in valid_scopes:
                    result['warnings'].append(f'Variable {i} has unknown scope: {variable["scope"]}')
        
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f'Extension validation error: {e}')
        
        return result


if __name__ == "__main__":
    # Demo usage
    print("🔧 StyleStack OOXML Extension Manager")
    
    manager = OOXMLExtensionManager()
    
    # Sample theme XML
    sample_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="StyleStack">
      <a:themeElements>
        <a:clrScheme name="StyleStack">
          <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
          <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
          <a:accent1><a:srgbClr val="4472C4"/></a:accent1>
        </a:clrScheme>
      </a:themeElements>
    </a:theme>'''
    
    # Create test extension
    extension = StyleStackExtension(
        uri=STYLESTACK_EXTENSION_URI,
        variables=[
            {
                'id': 'brandPrimary',
                'type': 'color',
                'scope': 'org',
                'xpath': '//a:accent1/a:srgbClr/@val',
                'defaultValue': '4472C4',
                'description': 'Primary brand color'
            },
            {
                'id': 'headingFont',
                'type': 'font',
                'scope': 'theme',
                'xpath': '//a:majorFont/a:latin/@typeface',
                'defaultValue': 'Calibri Light',
                'description': 'Main heading font'
            }
        ]
    )
    
    try:
        # Write extension to XML
        updated_xml = manager.write_extension_to_xml(sample_xml, extension)
        print("✅ Extension writing successful")
        
        # Read extensions back
        extensions = manager.read_extensions_from_xml(updated_xml)
        print(f"✅ Found {len(extensions)} extensions")
        
        if extensions:
            ext = extensions[0]
            print(f"   URI: {ext.uri}")
            print(f"   Variables: {len(ext.variables)}")
            print(f"   Version: {ext.metadata.version}")
        
        # Validate compatibility
        validation = manager.validate_extension_compatibility(updated_xml)
        print(f"✅ Extension validation: {'PASSED' if validation['valid'] else 'FAILED'}")
        
        if validation['errors']:
            for error in validation['errors']:
                print(f"   Error: {error}")
        
        if validation['warnings']:
            for warning in validation['warnings']:
                print(f"   Warning: {warning}")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    
    print("Extension manager demo completed!")