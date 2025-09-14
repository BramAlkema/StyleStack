"""Tests for OOXML probe file generation."""

import pytest
import tempfile
import zipfile
from pathlib import Path
from lxml import etree

from ooxml_tester.probe.generator import ProbeGenerator
from ooxml_tester.core.config import Config


class TestProbeGeneration:
    """Test probe file creation with specific OOXML features."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)
    
    @pytest.fixture
    def probe_generator(self, config):
        """Create probe generator instance."""
        return ProbeGenerator(config)
    
    def test_docx_probe_generation(self, probe_generator, temp_dir):
        """Test Word document probe generation."""
        # Generate a Word probe with specific features
        probe_file = probe_generator.generate_docx_probe(
            output_dir=temp_dir,
            features=['styles', 'themes', 'numbering', 'tables'],
            filename='word_probe.docx'
        )
        
        # Verify file exists and is valid ZIP
        assert probe_file.exists()
        assert probe_file.suffix == '.docx'
        assert zipfile.is_zipfile(probe_file)
        
        # Verify OOXML structure
        with zipfile.ZipFile(probe_file, 'r') as docx_zip:
            # Check required files exist
            required_files = [
                '[Content_Types].xml',
                '_rels/.rels',
                'word/document.xml',
                'word/_rels/document.xml.rels',
                'word/styles.xml',
                'word/theme/theme1.xml'
            ]
            
            zip_files = docx_zip.namelist()
            for required_file in required_files:
                assert required_file in zip_files, f"Missing required file: {required_file}"
            
            # Verify document structure contains expected elements
            document_xml = docx_zip.read('word/document.xml')
            doc_root = etree.fromstring(document_xml)
            
            # Check for WordprocessingML namespace
            assert doc_root.tag.endswith('}document')
            assert 'http://schemas.openxmlformats.org/wordprocessingml/2006/main' in doc_root.nsmap.values()
            
            # Check for body content
            body = doc_root.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body')
            assert body is not None
    
    def test_pptx_probe_generation(self, probe_generator, temp_dir):
        """Test PowerPoint presentation probe generation."""
        # Generate a PowerPoint probe with specific features
        probe_file = probe_generator.generate_pptx_probe(
            output_dir=temp_dir,
            features=['masters', 'layouts', 'themes', 'shapes'],
            filename='powerpoint_probe.pptx'
        )
        
        # Verify file exists and is valid ZIP
        assert probe_file.exists()
        assert probe_file.suffix == '.pptx'
        assert zipfile.is_zipfile(probe_file)
        
        # Verify OOXML structure
        with zipfile.ZipFile(probe_file, 'r') as pptx_zip:
            # Check required files exist
            required_files = [
                '[Content_Types].xml',
                '_rels/.rels',
                'ppt/presentation.xml',
                'ppt/_rels/presentation.xml.rels',
                'ppt/theme/theme1.xml',
                'ppt/slideMasters/slideMaster1.xml'
            ]
            
            zip_files = pptx_zip.namelist()
            for required_file in required_files:
                assert required_file in zip_files, f"Missing required file: {required_file}"
            
            # Verify presentation structure
            presentation_xml = pptx_zip.read('ppt/presentation.xml')
            pres_root = etree.fromstring(presentation_xml)
            
            # Check for PresentationML namespace
            assert pres_root.tag.endswith('}presentation')
            assert 'http://schemas.openxmlformats.org/presentationml/2006/main' in pres_root.nsmap.values()
    
    def test_xlsx_probe_generation(self, probe_generator, temp_dir):
        """Test Excel workbook probe generation."""
        # Generate an Excel probe with specific features
        probe_file = probe_generator.generate_xlsx_probe(
            output_dir=temp_dir,
            features=['styles', 'tables', 'charts', 'formatting'],
            filename='excel_probe.xlsx'
        )
        
        # Verify file exists and is valid ZIP
        assert probe_file.exists()
        assert probe_file.suffix == '.xlsx'
        assert zipfile.is_zipfile(probe_file)
        
        # Verify OOXML structure
        with zipfile.ZipFile(probe_file, 'r') as xlsx_zip:
            # Check required files exist
            required_files = [
                '[Content_Types].xml',
                '_rels/.rels',
                'xl/workbook.xml',
                'xl/_rels/workbook.xml.rels',
                'xl/worksheets/sheet1.xml',
                'xl/styles.xml'
            ]
            
            zip_files = xlsx_zip.namelist()
            for required_file in required_files:
                assert required_file in zip_files, f"Missing required file: {required_file}"
            
            # Verify workbook structure
            workbook_xml = xlsx_zip.read('xl/workbook.xml')
            wb_root = etree.fromstring(workbook_xml)
            
            # Check for SpreadsheetML namespace
            assert wb_root.tag.endswith('}workbook')
            assert 'http://schemas.openxmlformats.org/spreadsheetml/2006/main' in wb_root.nsmap.values()
    
    def test_stylestack_carrier_probes(self, probe_generator, temp_dir):
        """Test probe generation targeting StyleStack carriers."""
        # Generate probes with StyleStack-specific features
        probe_file = probe_generator.generate_carrier_probe(
            output_dir=temp_dir,
            format='pptx',
            carriers=['theme.color.accent1', 'theme.font.major.latin', 'master.level1.size_emu'],
            filename='stylestack_probe.pptx'
        )
        
        assert probe_file.exists()
        assert zipfile.is_zipfile(probe_file)
        
        # Verify carrier-specific content
        with zipfile.ZipFile(probe_file, 'r') as pptx_zip:
            # Check theme contains color scheme
            theme_xml = pptx_zip.read('ppt/theme/theme1.xml')
            theme_root = etree.fromstring(theme_xml)
            
            # Look for color scheme elements
            color_scheme = theme_root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}clrScheme')
            assert color_scheme is not None
            
            # Look for font scheme elements
            font_scheme = theme_root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}fontScheme')
            assert font_scheme is not None
    
    def test_probe_feature_validation(self, probe_generator, temp_dir):
        """Test that generated probes contain expected OOXML features."""
        # Generate probe with specific features
        probe_file = probe_generator.generate_docx_probe(
            output_dir=temp_dir,
            features=['styles', 'numbering'],
            filename='feature_test.docx'
        )
        
        # Validate features are present
        validation_result = probe_generator.validate_probe(probe_file, ['styles', 'numbering'])
        
        assert validation_result.is_valid
        assert 'styles' in validation_result.found_features
        assert 'numbering' in validation_result.found_features
        assert len(validation_result.missing_features) == 0
    
    def test_batch_probe_generation(self, probe_generator, temp_dir):
        """Test batch generation of multiple probe files."""
        # Generate multiple probes
        probe_configs = [
            {'format': 'docx', 'features': ['styles', 'tables'], 'name': 'doc_probe_1'},
            {'format': 'pptx', 'features': ['themes', 'shapes'], 'name': 'ppt_probe_1'},
            {'format': 'xlsx', 'features': ['formatting', 'charts'], 'name': 'xl_probe_1'}
        ]
        
        probe_files = probe_generator.generate_batch(
            output_dir=temp_dir,
            probe_configs=probe_configs
        )
        
        # Verify all files were created
        assert len(probe_files) == 3
        for probe_file in probe_files:
            assert probe_file.exists()
            assert zipfile.is_zipfile(probe_file)
    
    def test_probe_file_naming(self, probe_generator, temp_dir):
        """Test probe file naming conventions."""
        # Test automatic naming
        probe_file = probe_generator.generate_docx_probe(
            output_dir=temp_dir,
            features=['styles']
        )
        
        # Should have timestamp-based name
        assert probe_file.name.startswith('probe_')
        assert probe_file.suffix == '.docx'
        
        # Test custom naming
        custom_probe = probe_generator.generate_docx_probe(
            output_dir=temp_dir,
            features=['styles'],
            filename='custom_name.docx'
        )
        
        assert custom_probe.name == 'custom_name.docx'
    
    def test_invalid_feature_handling(self, probe_generator, temp_dir):
        """Test handling of invalid or unsupported features."""
        with pytest.raises(ValueError) as excinfo:
            probe_generator.generate_docx_probe(
                output_dir=temp_dir,
                features=['invalid_feature', 'unsupported_feature']
            )
        
        assert "Unsupported features" in str(excinfo.value)
    
    def test_probe_generation_with_empty_features(self, probe_generator, temp_dir):
        """Test probe generation with minimal features."""
        # Should create basic valid OOXML file even with no specific features
        probe_file = probe_generator.generate_docx_probe(
            output_dir=temp_dir,
            features=[]
        )
        
        assert probe_file.exists()
        assert zipfile.is_zipfile(probe_file)
        
        # Should still have basic structure
        with zipfile.ZipFile(probe_file, 'r') as docx_zip:
            assert '[Content_Types].xml' in docx_zip.namelist()
            assert 'word/document.xml' in docx_zip.namelist()


class TestProbeValidation:
    """Test probe file validation functionality."""
    
    @pytest.fixture
    def probe_generator(self):
        """Create probe generator for validation tests."""
        return ProbeGenerator(Config())
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)
    
    def test_validate_existing_ooxml_file(self, probe_generator, temp_dir):
        """Test validation of existing OOXML files."""
        # Create a minimal valid DOCX for testing
        probe_file = probe_generator.generate_docx_probe(
            output_dir=temp_dir,
            features=['styles']
        )
        
        # Validate the file
        result = probe_generator.validate_ooxml_structure(probe_file)
        
        assert result.is_valid
        assert result.format == 'docx'
        assert len(result.errors) == 0
    
    def test_validate_corrupted_file(self, probe_generator, temp_dir):
        """Test validation of corrupted OOXML files."""
        # Create invalid file
        invalid_file = temp_dir / 'invalid.docx'
        invalid_file.write_text('This is not a valid OOXML file')
        
        # Validation should fail
        result = probe_generator.validate_ooxml_structure(invalid_file)
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert 'Not a valid ZIP file' in result.errors[0] or 'Invalid OOXML structure' in result.errors[0]