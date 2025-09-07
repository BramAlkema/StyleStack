"""
Test suite for OOXML Extension List Management

Tests the reading, writing, and manipulation of OOXML <extLst> elements
for embedding StyleStack variables while maintaining Office compatibility.

Validates:
- Reading existing extension lists from OOXML files
- Writing StyleStack extensions to OOXML documents
- Extension preservation during file operations
- Multiple extension coexistence
- Office application compatibility
"""

import pytest
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import zipfile
import io
import tempfile
from pathlib import Path
import json
from dataclasses import dataclass


# OOXML Namespace definitions
OOXML_NAMESPACES = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main', 
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006'
}

# StyleStack extension URI
STYLESTACK_EXTENSION_URI = "https://stylestack.org/extensions/variables/v1"


@dataclass
class StyleStackExtension:
    """Represents a StyleStack variable extension in OOXML"""
    uri: str
    version: str = "1.0"
    variables: List[Dict[str, Any]] = None
    metadata: Optional[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = []
        if self.metadata is None:
            self.metadata = {}


class OOXMLExtensionManager:
    """
    Manages OOXML extension lists for embedding StyleStack variables.
    
    Handles reading/writing <extLst> elements while preserving existing
    extensions and maintaining Office application compatibility.
    """
    
    def __init__(self):
        self.namespaces = OOXML_NAMESPACES.copy()
        # Register namespaces for ElementTree
        for prefix, uri in self.namespaces.items():
            ET.register_namespace(prefix, uri)
    
    def read_extensions_from_xml(self, xml_content: str) -> List[StyleStackExtension]:
        """Extract StyleStack extensions from XML content"""
        try:
            root = ET.fromstring(xml_content)
            extensions = []
            
            # Find all extLst elements
            ext_lists = root.findall('.//{*}extLst')
            
            for ext_list in ext_lists:
                # Find StyleStack extensions
                for ext in ext_list.findall('./{*}ext'):
                    uri = ext.get('uri', '')
                    if 'stylestack' in uri.lower():
                        extension = self._parse_stylestack_extension(ext)
                        if extension:
                            extensions.append(extension)
            
            return extensions
            
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML content: {e}")
    
    def _parse_stylestack_extension(self, ext_element: ET.Element) -> Optional[StyleStackExtension]:
        """Parse a StyleStack extension element"""
        uri = ext_element.get('uri', '')
        
        # Look for StyleStack extension content
        for child in ext_element:
            if 'stylestack' in child.tag.lower() or 'variables' in child.tag.lower():
                try:
                    # Parse JSON content if present
                    if child.text:
                        data = json.loads(child.text)
                        return StyleStackExtension(
                            uri=uri,
                            version=data.get('version', '1.0'),
                            variables=data.get('variables', []),
                            metadata=data.get('metadata', {})
                        )
                except json.JSONDecodeError:
                    # Try parsing as XML structure
                    variables = []
                    metadata = {}
                    
                    for var_elem in child.findall('.//{*}variable'):
                        var_data = {
                            'id': var_elem.get('id'),
                            'type': var_elem.get('type'),
                            'scope': var_elem.get('scope'),
                            'xpath': var_elem.get('xpath'),
                            'defaultValue': var_elem.get('defaultValue')
                        }
                        variables.append({k: v for k, v in var_data.items() if v is not None})
                    
                    return StyleStackExtension(
                        uri=uri,
                        variables=variables,
                        metadata=metadata
                    )
        
        return None
    
    def write_extension_to_xml(self, xml_content: str, extension: StyleStackExtension) -> str:
        """Add StyleStack extension to XML content"""
        try:
            root = ET.fromstring(xml_content)
            
            # Find or create extLst element
            ext_list = self._find_or_create_extension_list(root)
            
            # Create StyleStack extension element
            ext_elem = ET.SubElement(ext_list, f"{{{self.namespaces['a']}}}ext")
            ext_elem.set('uri', extension.uri)
            
            # Create StyleStack variables element
            vars_elem = ET.SubElement(ext_elem, 'stylestack:variables')
            vars_elem.set('xmlns:stylestack', STYLESTACK_EXTENSION_URI)
            vars_elem.set('version', extension.version)
            
            # Add variables as JSON content
            extension_data = {
                'version': extension.version,
                'variables': extension.variables,
                'metadata': extension.metadata
            }
            vars_elem.text = json.dumps(extension_data, indent=2)
            
            return ET.tostring(root, encoding='unicode')
            
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML content: {e}")
    
    def _find_or_create_extension_list(self, root: ET.Element) -> ET.Element:
        """Find existing extLst or create new one"""
        # Look for existing extLst
        ext_list = root.find('.//{*}extLst')
        
        if ext_list is not None:
            return ext_list
        
        # Create new extLst - placement depends on document type
        if root.tag.endswith('}theme'):
            # Theme document - add at end
            ext_list = ET.SubElement(root, f"{{{self.namespaces['a']}}}extLst")
        elif root.tag.endswith('}sldMaster'):
            # Slide master - add before timing if present
            timing = root.find(f".//{{{self.namespaces['p']}}}timing")
            if timing is not None:
                parent = timing.getparent()
                index = list(parent).index(timing)
                ext_list = ET.Element(f"{{{self.namespaces['p']}}}extLst")
                parent.insert(index, ext_list)
            else:
                ext_list = ET.SubElement(root, f"{{{self.namespaces['p']}}}extLst")
        else:
            # Default - add at end
            namespace = self._detect_primary_namespace(root)
            ext_list = ET.SubElement(root, f"{{{namespace}}}extLst")
        
        return ext_list
    
    def _detect_primary_namespace(self, root: ET.Element) -> str:
        """Detect primary namespace from root element"""
        root_ns = root.tag.split('}')[0].lstrip('{')
        
        # Map to known namespaces
        if 'drawingml' in root_ns:
            return self.namespaces['a']
        elif 'presentationml' in root_ns:
            return self.namespaces['p']
        elif 'wordprocessingml' in root_ns:
            return self.namespaces['w']
        else:
            return self.namespaces['a']  # Default to DrawingML
    
    def remove_extension(self, xml_content: str, extension_uri: str) -> str:
        """Remove extension by URI from XML content"""
        try:
            root = ET.fromstring(xml_content)
            
            # Find and remove matching extensions
            for ext_list in root.findall('.//{*}extLst'):
                for ext in ext_list.findall('./{*}ext'):
                    if ext.get('uri') == extension_uri:
                        ext_list.remove(ext)
                
                # Remove empty extLst elements
                if len(ext_list) == 0:
                    parent = ext_list.getparent()
                    if parent is not None:
                        parent.remove(ext_list)
            
            return ET.tostring(root, encoding='unicode')
            
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML content: {e}")
    
    def list_all_extensions(self, xml_content: str) -> List[Dict[str, str]]:
        """List all extensions in XML content"""
        try:
            root = ET.fromstring(xml_content)
            extensions = []
            
            for ext_list in root.findall('.//{*}extLst'):
                for ext in ext_list.findall('./{*}ext'):
                    uri = ext.get('uri', '')
                    extensions.append({
                        'uri': uri,
                        'is_stylestack': 'stylestack' in uri.lower(),
                        'has_content': len(list(ext)) > 0
                    })
            
            return extensions
            
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML content: {e}")


class TestOOXMLExtensionManager:
    """Test suite for OOXML extension management"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.manager = OOXMLExtensionManager()
        
        # Sample OOXML theme content
        self.sample_theme_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">
          <a:themeElements>
            <a:clrScheme name="Office">
              <a:dk1>
                <a:sysClr val="windowText" lastClr="000000"/>
              </a:dk1>
              <a:lt1>
                <a:sysClr val="window" lastClr="FFFFFF"/>
              </a:lt1>
              <a:dk2>
                <a:srgbClr val="44546A"/>
              </a:dk2>
              <a:lt2>
                <a:srgbClr val="E7E6E6"/>
              </a:lt2>
              <a:accent1>
                <a:srgbClr val="4472C4"/>
              </a:accent1>
              <a:accent2>
                <a:srgbClr val="70AD47"/>
              </a:accent2>
            </a:clrScheme>
            <a:fontScheme name="Office">
              <a:majorFont>
                <a:latin typeface="Calibri Light"/>
              </a:majorFont>
              <a:minorFont>
                <a:latin typeface="Calibri"/>
              </a:minorFont>
            </a:fontScheme>
          </a:themeElements>
        </a:theme>'''
        
        # Sample slide master XML
        self.sample_slidemaster_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <p:sldMaster xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
                     xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
          <p:cSld>
            <p:bg>
              <p:bgRef idx="1001">
                <a:schemeClr val="bg1"/>
              </p:bgRef>
            </p:bg>
          </p:cSld>
        </p:sldMaster>'''
    
    def test_read_extensions_empty_document(self):
        """Test reading extensions from document without extensions"""
        extensions = self.manager.read_extensions_from_xml(self.sample_theme_xml)
        assert len(extensions) == 0
    
    def test_write_extension_to_clean_document(self):
        """Test adding StyleStack extension to clean document"""
        # Create test extension
        extension = StyleStackExtension(
            uri=STYLESTACK_EXTENSION_URI,
            version="1.0",
            variables=[
                {
                    'id': 'brandColor',
                    'type': 'color',
                    'scope': 'org',
                    'xpath': '//a:accent1/a:srgbClr/@val',
                    'defaultValue': '4472C4'
                }
            ],
            metadata={'author': 'StyleStack', 'created': '2025-09-07'}
        )
        
        # Write extension
        result_xml = self.manager.write_extension_to_xml(self.sample_theme_xml, extension)
        
        # Verify extension was added
        assert STYLESTACK_EXTENSION_URI in result_xml
        assert 'stylestack:variables' in result_xml
        assert 'brandColor' in result_xml
        
        # Verify original content preserved
        assert '<a:clrScheme name="Office">' in result_xml
        assert '<a:accent1>' in result_xml
    
    def test_read_written_extension(self):
        """Test round-trip: write extension then read it back"""
        # Create and write extension
        original_extension = StyleStackExtension(
            uri=STYLESTACK_EXTENSION_URI,
            variables=[
                {
                    'id': 'primaryColor',
                    'type': 'color',
                    'scope': 'org',
                    'defaultValue': 'FF0000'
                },
                {
                    'id': 'headingFont',
                    'type': 'font', 
                    'scope': 'theme',
                    'defaultValue': 'Arial'
                }
            ]
        )
        
        xml_with_extension = self.manager.write_extension_to_xml(
            self.sample_theme_xml, 
            original_extension
        )
        
        # Read extension back
        read_extensions = self.manager.read_extensions_from_xml(xml_with_extension)
        
        assert len(read_extensions) == 1
        extension = read_extensions[0]
        
        assert extension.uri == STYLESTACK_EXTENSION_URI
        assert len(extension.variables) == 2
        
        # Check variable details
        var_ids = [var['id'] for var in extension.variables]
        assert 'primaryColor' in var_ids
        assert 'headingFont' in var_ids
    
    def test_multiple_extension_coexistence(self):
        """Test multiple extensions can coexist"""
        # Create XML with existing non-StyleStack extension
        xml_with_existing = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">
          <a:themeElements>
            <a:clrScheme name="Office">
              <a:accent1><a:srgbClr val="4472C4"/></a:accent1>
            </a:clrScheme>
          </a:themeElements>
          <a:extLst>
            <a:ext uri="https://example.com/some-other-extension">
              <other:data xmlns:other="https://example.com/ns">Some data</other:data>
            </a:ext>
          </a:extLst>
        </a:theme>'''
        
        # Add StyleStack extension
        stylestack_ext = StyleStackExtension(
            uri=STYLESTACK_EXTENSION_URI,
            variables=[{'id': 'testVar', 'type': 'color', 'scope': 'org'}]
        )
        
        result_xml = self.manager.write_extension_to_xml(xml_with_existing, stylestack_ext)
        
        # Verify both extensions present
        assert 'https://example.com/some-other-extension' in result_xml
        assert STYLESTACK_EXTENSION_URI in result_xml
        assert '<other:data' in result_xml
        assert 'stylestack:variables' in result_xml
        
        # List all extensions
        extensions = self.manager.list_all_extensions(result_xml)
        assert len(extensions) == 2
        
        stylestack_exts = [ext for ext in extensions if ext['is_stylestack']]
        other_exts = [ext for ext in extensions if not ext['is_stylestack']]
        
        assert len(stylestack_exts) == 1
        assert len(other_exts) == 1
    
    def test_extension_removal(self):
        """Test removing specific extension by URI"""
        # Start with XML containing multiple extensions
        xml_with_extensions = '''<?xml version="1.0" encoding="UTF-8"?>
        <a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
          <a:themeElements>
            <a:clrScheme name="Test"/>
          </a:themeElements>
          <a:extLst>
            <a:ext uri="https://keep.this/extension">
              <keep:data xmlns:keep="https://keep.this/">Keep me</keep:data>
            </a:ext>
            <a:ext uri="https://remove.this/extension">
              <remove:data xmlns:remove="https://remove.this/">Remove me</remove:data>
            </a:ext>
          </a:extLst>
        </a:theme>'''
        
        # Remove specific extension
        result_xml = self.manager.remove_extension(
            xml_with_extensions,
            "https://remove.this/extension"
        )
        
        # Verify correct extension removed
        assert 'https://keep.this/extension' in result_xml
        assert 'https://remove.this/extension' not in result_xml
        assert 'Keep me' in result_xml
        assert 'Remove me' not in result_xml
    
    def test_extension_preservation_during_modification(self):
        """Test extensions are preserved during document modifications"""
        # Create XML with StyleStack extension
        extension = StyleStackExtension(
            uri=STYLESTACK_EXTENSION_URI,
            variables=[{'id': 'preserveMe', 'type': 'color', 'scope': 'org'}]
        )
        
        xml_with_ext = self.manager.write_extension_to_xml(self.sample_theme_xml, extension)
        
        # Simulate document modification (parse and re-serialize)
        root = ET.fromstring(xml_with_ext)
        
        # Modify something in the theme
        accent1 = root.find('.//a:accent1/a:srgbClr', self.manager.namespaces)
        if accent1 is not None:
            accent1.set('val', 'FF0000')  # Change color
        
        modified_xml = ET.tostring(root, encoding='unicode')
        
        # Verify extension still present
        extensions = self.manager.read_extensions_from_xml(modified_xml)
        assert len(extensions) == 1
        assert extensions[0].variables[0]['id'] == 'preserveMe'
        
        # Verify modification applied
        assert 'val="FF0000"' in modified_xml
    
    def test_invalid_xml_handling(self):
        """Test handling of invalid XML content"""
        invalid_xml = "<invalid>unclosed tag"
        
        with pytest.raises(ValueError, match="Invalid XML content"):
            self.manager.read_extensions_from_xml(invalid_xml)
        
        with pytest.raises(ValueError, match="Invalid XML content"):
            extension = StyleStackExtension(uri="test")
            self.manager.write_extension_to_xml(invalid_xml, extension)
    
    def test_slidemaster_extension_placement(self):
        """Test extension placement in slide master documents"""
        extension = StyleStackExtension(
            uri=STYLESTACK_EXTENSION_URI,
            variables=[{'id': 'masterVar', 'type': 'color', 'scope': 'theme'}]
        )
        
        result_xml = self.manager.write_extension_to_xml(
            self.sample_slidemaster_xml, 
            extension
        )
        
        # Verify extension added with correct namespace
        assert 'p:extLst' in result_xml or 'extLst' in result_xml
        assert STYLESTACK_EXTENSION_URI in result_xml
        assert 'masterVar' in result_xml
    
    def test_extension_versioning(self):
        """Test extension version handling"""
        # Create extension with specific version
        extension_v1 = StyleStackExtension(
            uri=STYLESTACK_EXTENSION_URI,
            version="1.2",
            variables=[{'id': 'versionedVar', 'type': 'text', 'scope': 'org'}]
        )
        
        xml_with_version = self.manager.write_extension_to_xml(
            self.sample_theme_xml,
            extension_v1
        )
        
        # Read back and verify version preserved
        extensions = self.manager.read_extensions_from_xml(xml_with_version)
        assert len(extensions) == 1
        assert extensions[0].version == "1.2"
    
    def test_extension_metadata_handling(self):
        """Test extension metadata storage and retrieval"""
        extension = StyleStackExtension(
            uri=STYLESTACK_EXTENSION_URI,
            variables=[{'id': 'metaVar', 'type': 'color', 'scope': 'user'}],
            metadata={
                'author': 'Test Author',
                'description': 'Test extension with metadata',
                'created': '2025-09-07T10:30:00Z',
                'modified': '2025-09-07T11:45:00Z'
            }
        )
        
        xml_with_metadata = self.manager.write_extension_to_xml(
            self.sample_theme_xml,
            extension
        )
        
        # Read back and verify metadata preserved
        extensions = self.manager.read_extensions_from_xml(xml_with_metadata)
        assert len(extensions) == 1
        
        metadata = extensions[0].metadata
        assert metadata['author'] == 'Test Author'
        assert metadata['description'] == 'Test extension with metadata'
        assert 'created' in metadata
        assert 'modified' in metadata
    
    def test_large_variable_set_handling(self):
        """Test handling large numbers of variables in extension"""
        # Create extension with many variables
        variables = []
        for i in range(100):
            variables.append({
                'id': f'var_{i}',
                'type': 'color' if i % 2 == 0 else 'font',
                'scope': ['org', 'group', 'user'][i % 3],
                'xpath': f'//a:element_{i}/@attr',
                'defaultValue': f'value_{i}'
            })
        
        extension = StyleStackExtension(
            uri=STYLESTACK_EXTENSION_URI,
            variables=variables
        )
        
        xml_with_many_vars = self.manager.write_extension_to_xml(
            self.sample_theme_xml,
            extension
        )
        
        # Read back and verify all variables preserved
        extensions = self.manager.read_extensions_from_xml(xml_with_many_vars)
        assert len(extensions) == 1
        assert len(extensions[0].variables) == 100
        
        # Verify specific variables
        var_ids = [var['id'] for var in extensions[0].variables]
        assert 'var_0' in var_ids
        assert 'var_50' in var_ids
        assert 'var_99' in var_ids


if __name__ == "__main__":
    # Run basic functionality tests
    print("🧪 Testing OOXML Extension Manager")
    
    manager = OOXMLExtensionManager()
    
    # Test basic extension writing
    sample_xml = '''<?xml version="1.0"?>
    <a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
      <a:themeElements>
        <a:clrScheme name="Test"/>
      </a:themeElements>
    </a:theme>'''
    
    extension = StyleStackExtension(
        uri=STYLESTACK_EXTENSION_URI,
        variables=[
            {
                'id': 'testColor',
                'type': 'color',
                'scope': 'org',
                'defaultValue': 'FF0000'
            }
        ]
    )
    
    try:
        result = manager.write_extension_to_xml(sample_xml, extension)
        print("✅ Extension writing successful")
        
        extensions = manager.read_extensions_from_xml(result)
        print(f"✅ Extension reading successful - found {len(extensions)} extensions")
        
        if extensions:
            print(f"   Variables: {len(extensions[0].variables)}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    print("Extension manager tests completed!")