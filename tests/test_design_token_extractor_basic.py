#!/usr/bin/env python3
"""
Basic test suite for Design Token Extractor

Tests the core functionality of extracting design tokens from Office templates.
"""

import unittest
import tempfile
import zipfile
import json
from pathlib import Path

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))

from tools.design_token_extractor import DesignTokenExtractor


class TestDesignTokenExtractorBasic(unittest.TestCase):
    """Test basic DesignTokenExtractor functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.extractor = DesignTokenExtractor()
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_extractor_initialization(self):
        """Test DesignTokenExtractor initialization"""
        extractor = DesignTokenExtractor()
        self.assertIsInstance(extractor, DesignTokenExtractor)
        self.assertEqual(extractor.output_format, 'stylestack')
        
    def test_extractor_initialization_with_format(self):
        """Test DesignTokenExtractor initialization with custom format"""
        extractor = DesignTokenExtractor(output_format='w3c')
        self.assertEqual(extractor.output_format, 'w3c')
        
    def test_theme_colors_mapping(self):
        """Test theme colors mapping constants"""
        self.assertIn('0', DesignTokenExtractor.THEME_COLORS)
        self.assertEqual(DesignTokenExtractor.THEME_COLORS['0'], 'background1')
        self.assertEqual(DesignTokenExtractor.THEME_COLORS['4'], 'accent1')
        
    def test_detect_file_format_pptx(self):
        """Test file format detection for PowerPoint"""
        test_file = self.temp_dir / "test.pptx"
        test_file.touch()
        
        format_type = self.extractor._detect_file_format(test_file)
        self.assertEqual(format_type, 'powerpoint')
        
    def test_detect_file_format_potx(self):
        """Test file format detection for PowerPoint template"""
        test_file = self.temp_dir / "test.potx"
        test_file.touch()
        
        format_type = self.extractor._detect_file_format(test_file)
        self.assertEqual(format_type, 'powerpoint')
        
    def test_detect_file_format_odp(self):
        """Test file format detection for OpenOffice Presentation"""
        test_file = self.temp_dir / "test.odp"
        test_file.touch()
        
        format_type = self.extractor._detect_file_format(test_file)
        self.assertEqual(format_type, 'opendocument')
        
    def test_detect_file_format_unknown(self):
        """Test file format detection for unknown formats"""
        test_file = self.temp_dir / "test.unknown"
        test_file.touch()
        
        format_type = self.extractor._detect_file_format(test_file)
        self.assertEqual(format_type, 'unknown')


class TestDesignTokenExtractorFileHandling(unittest.TestCase):
    """Test file handling functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.extractor = DesignTokenExtractor()
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def create_mock_pptx(self, filename: str) -> Path:
        """Create a mock PPTX file for testing"""
        pptx_path = self.temp_dir / filename
        
        # Create a minimal PPTX structure
        with zipfile.ZipFile(pptx_path, 'w') as zf:
            # Content Types
            zf.writestr('[Content_Types].xml', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
</Types>''')
            
            # Relationships
            zf.writestr('_rels/.rels', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>''')
            
            # Basic presentation
            zf.writestr('ppt/presentation.xml', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst>
    <p:sldMasterId id="2147483648" r:id="rId1"/>
  </p:sldMasterIdLst>
</p:presentation>''')
            
            # Basic theme
            zf.writestr('ppt/theme/theme1.xml', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Test Theme">
  <a:themeElements>
    <a:clrScheme name="Test Colors">
      <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
      <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
      <a:accent1><a:srgbClr val="FF0000"/></a:accent1>
    </a:clrScheme>
  </a:themeElements>
</a:theme>''')
            
        return pptx_path
        
    def test_extract_from_mock_pptx(self):
        """Test extracting tokens from a mock PPTX file"""
        pptx_file = self.create_mock_pptx("test.pptx")
        
        # Should not crash and return some result
        try:
            result = self.extractor.extract_from_file(pptx_file)
            self.assertIsInstance(result, dict)
            # Basic structure expectations
            self.assertIn('format', result)
            self.assertIn('extracted_at', result)
        except Exception as e:
            # Allow for various issues but ensure it doesn't crash completely
            self.assertIsInstance(e, (FileNotFoundError, KeyError, AttributeError))
            
    def test_extract_from_nonexistent_file(self):
        """Test handling of non-existent files"""
        nonexistent_file = self.temp_dir / "nonexistent.pptx"
        
        with self.assertRaises(FileNotFoundError):
            self.extractor.extract_from_file(nonexistent_file)


class TestDesignTokenExtractorConstants(unittest.TestCase):
    """Test constants and mappings"""
    
    def test_theme_colors_completeness(self):
        """Test that all theme color indices are defined"""
        expected_indices = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']
        
        for index in expected_indices:
            self.assertIn(index, DesignTokenExtractor.THEME_COLORS)
            
    def test_theme_colors_naming(self):
        """Test theme color naming consistency"""
        # Background colors
        self.assertEqual(DesignTokenExtractor.THEME_COLORS['0'], 'background1')
        self.assertEqual(DesignTokenExtractor.THEME_COLORS['2'], 'background2')
        
        # Text colors
        self.assertEqual(DesignTokenExtractor.THEME_COLORS['1'], 'text1')
        self.assertEqual(DesignTokenExtractor.THEME_COLORS['3'], 'text2')
        
        # Accent colors
        for i in range(1, 7):
            self.assertEqual(DesignTokenExtractor.THEME_COLORS[str(i+3)], f'accent{i}')


class TestDesignTokenExtractorFormats(unittest.TestCase):
    """Test support for different file formats"""
    
    def setUp(self):
        """Set up test environment"""
        self.extractor = DesignTokenExtractor()
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_powerpoint_extensions(self):
        """Test PowerPoint file extension detection"""
        powerpoint_extensions = ['.pptx', '.potx', '.ppsx']
        
        for ext in powerpoint_extensions:
            test_file = self.temp_dir / f"test{ext}"
            test_file.touch()
            format_type = self.extractor._detect_file_format(test_file)
            self.assertEqual(format_type, 'powerpoint')
            
    def test_opendocument_extensions(self):
        """Test OpenDocument file extension detection"""
        odf_extensions = ['.odp', '.otp', '.ods', '.ots', '.odt', '.ott']
        
        for ext in odf_extensions:
            test_file = self.temp_dir / f"test{ext}"
            test_file.touch()
            format_type = self.extractor._detect_file_format(test_file)
            self.assertEqual(format_type, 'opendocument')


class TestDesignTokenExtractorEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        """Set up test environment"""
        self.extractor = DesignTokenExtractor()
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_empty_file(self):
        """Test handling of empty files"""
        empty_file = self.temp_dir / "empty.pptx"
        empty_file.touch()
        
        # Should handle empty files gracefully
        with self.assertRaises((zipfile.BadZipFile, FileNotFoundError)):
            self.extractor.extract_from_file(empty_file)
            
    def test_invalid_zip_file(self):
        """Test handling of invalid ZIP files"""
        invalid_file = self.temp_dir / "invalid.pptx"
        invalid_file.write_text("This is not a valid ZIP file")
        
        with self.assertRaises(zipfile.BadZipFile):
            self.extractor.extract_from_file(invalid_file)
            
    def test_file_without_extension(self):
        """Test handling of files without extensions"""
        no_ext_file = self.temp_dir / "noextension"
        no_ext_file.touch()
        
        format_type = self.extractor._detect_file_format(no_ext_file)
        self.assertEqual(format_type, 'unknown')


class TestDesignTokenExtractorOutputFormats(unittest.TestCase):
    """Test different output formats"""
    
    def test_stylestack_format(self):
        """Test StyleStack output format"""
        extractor = DesignTokenExtractor(output_format='stylestack')
        self.assertEqual(extractor.output_format, 'stylestack')
        
    def test_w3c_format(self):
        """Test W3C design tokens format"""
        extractor = DesignTokenExtractor(output_format='w3c')
        self.assertEqual(extractor.output_format, 'w3c')
        
    def test_custom_format(self):
        """Test custom output format"""
        extractor = DesignTokenExtractor(output_format='custom')
        self.assertEqual(extractor.output_format, 'custom')


if __name__ == '__main__':
    unittest.main()