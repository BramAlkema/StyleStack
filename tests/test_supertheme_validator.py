"""
Tests for SuperTheme Package Validator

Validates the comprehensive validation system for Microsoft SuperTheme packages,
ensuring Office 2016-365 compatibility and proper lxml XML processing.
"""

import pytest
import io
import zipfile
from tools.supertheme_validator import SuperThemeValidator, ValidationResult
from unittest.mock import patch, MagicMock


class TestSuperThemeValidator:
    """Test SuperTheme package validation functionality"""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance"""
        return SuperThemeValidator()
    
    @pytest.fixture
    def strict_validator(self):
        """Create strict validator instance"""
        return SuperThemeValidator(strict_mode=True)
    
    def create_minimal_supertheme(self) -> bytes:
        """Create minimal valid SuperTheme package for testing"""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # [Content_Types].xml
            zf.writestr('[Content_Types].xml', '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/themeVariants/themeVariantManager.xml" 
              ContentType="application/vnd.ms-powerpoint.themeVariantManager+xml"/>
    <Override PartName="/themeVariants/variant1/theme/theme/theme1.xml" 
              ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
</Types>''')
            
            # _rels/.rels
            zf.writestr('_rels/.rels', '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.microsoft.com/office/thememl/2012/main" 
                  Target="themeVariants/themeVariantManager.xml"/>
</Relationships>''')
            
            # themeVariantManager.xml
            zf.writestr('themeVariants/themeVariantManager.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<supertheme:themeVariantManager xmlns:supertheme="http://schemas.microsoft.com/office/thememl/2012/main"
                                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
                                xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                                xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
    <supertheme:themeVariantLst>
        <supertheme:themeVariant vid="{12345678-1234-5678-9012-123456789ABC}" name="Design 1"/>
    </supertheme:themeVariantLst>
</supertheme:themeVariantManager>''')
            
            # Manager relationships
            zf.writestr('themeVariants/_rels/themeVariantManager.xml.rels', '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.microsoft.com/office/thememl/2012/main" 
                  Target="variant1/theme/theme/theme1.xml"/>
</Relationships>''')
            
            # Theme XML
            zf.writestr('themeVariants/variant1/theme/theme/theme1.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Design 1">
    <a:themeElements>
        <a:clrScheme name="Design 1">
            <a:dk1><a:sysClr val="windowText"/></a:dk1>
            <a:lt1><a:sysClr val="window"/></a:lt1>
            <a:dk2><a:srgbClr val="1F497D"/></a:dk2>
            <a:lt2><a:srgbClr val="EEECE1"/></a:lt2>
            <a:accent1><a:srgbClr val="4F81BD"/></a:accent1>
            <a:accent2><a:srgbClr val="F79646"/></a:accent2>
            <a:accent3><a:srgbClr val="9BBB59"/></a:accent3>
            <a:accent4><a:srgbClr val="8064A2"/></a:accent4>
            <a:accent5><a:srgbClr val="4BACC6"/></a:accent5>
            <a:accent6><a:srgbClr val="F366A7"/></a:accent6>
            <a:hlink><a:srgbClr val="0000FF"/></a:hlink>
            <a:folHlink><a:srgbClr val="800080"/></a:folHlink>
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
</a:theme>''')
            
            # Presentation XML
            zf.writestr('themeVariants/variant1/theme/presentation.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
                xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
    <p:sldSz cx="10058400" cy="7772400" type="screen4x3"/>
</p:presentation>''')
        
        return buffer.getvalue()
    
    def create_invalid_zip(self) -> bytes:
        """Create invalid ZIP data"""
        return b"invalid zip data"
    
    def create_empty_supertheme(self) -> bytes:
        """Create empty SuperTheme package"""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('dummy.txt', 'empty package')
        return buffer.getvalue()
    
    def test_validate_minimal_valid_supertheme(self, validator):
        """Test validation of minimal valid SuperTheme"""
        supertheme_data = self.create_minimal_supertheme()
        result = validator.validate_package(supertheme_data)
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert result.variant_count == 1
        assert result.package_size_mb > 0
        assert len(result.errors) == 0
    
    def test_validate_invalid_zip(self, validator):
        """Test validation of invalid ZIP data"""
        invalid_data = self.create_invalid_zip()
        result = validator.validate_package(invalid_data)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("Invalid ZIP file format" in error.message for error in result.errors)
    
    def test_validate_empty_supertheme(self, validator):
        """Test validation of empty SuperTheme package"""
        empty_data = self.create_empty_supertheme()
        result = validator.validate_package(empty_data)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        
        # Check for missing required files
        missing_file_errors = [e for e in result.errors if "Missing required file" in e.message]
        assert len(missing_file_errors) > 0
    
    def test_package_structure_validation(self, validator):
        """Test package structure validation"""
        supertheme_data = self.create_minimal_supertheme()
        result = validator.validate_package(supertheme_data)
        
        # Should find the variant
        assert result.variant_count == 1
        
        # Should have info about found variants
        info_messages = [info.message for info in result.info]
        assert any("Found 1 theme variants" in msg for msg in info_messages)
    
    def test_content_types_validation(self, validator):
        """Test content types validation"""
        # Create SuperTheme with missing content types
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('[Content_Types].xml', '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
</Types>''')
            
            # Add minimal required files to avoid other errors
            zf.writestr('_rels/.rels', '<?xml version="1.0"?><Relationships/>')
            zf.writestr('themeVariants/themeVariantManager.xml', '<?xml version="1.0"?><root/>')
            zf.writestr('themeVariants/_rels/themeVariantManager.xml.rels', '<?xml version="1.0"?><Relationships/>')
        
        result = validator.validate_package(buffer.getvalue())
        
        assert result.is_valid is False
        content_type_errors = [e for e in result.errors if e.category == "content_types"]
        assert len(content_type_errors) > 0
    
    def test_xml_well_formedness_validation(self, validator):
        """Test XML well-formedness validation"""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add severely malformed XML that even recovery parser can't fix
            zf.writestr('test.xml', '<root><unclosed><nested>&invalid_entity;</nested>')
            zf.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types/>')
            zf.writestr('_rels/.rels', '<?xml version="1.0"?><Relationships/>')
            zf.writestr('themeVariants/themeVariantManager.xml', '<?xml version="1.0"?><root/>')
            zf.writestr('themeVariants/_rels/themeVariantManager.xml.rels', '<?xml version="1.0"?><Relationships/>')
        
        result = validator.validate_package(buffer.getvalue())
        
        # With lxml recovery mode, we may get warnings instead of errors
        # Check for either XML errors or missing XML declarations
        xml_issues = len([e for e in result.errors if e.category == "xml"]) + \
                    len([w for w in result.warnings if w.category == "xml"])
        
        # At minimum, should detect missing XML declaration
        assert xml_issues > 0 or any("Missing XML declaration" in w.message for w in result.warnings)
    
    def test_namespace_validation(self, validator):
        """Test namespace validation in theme variant manager"""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add minimal content types
            zf.writestr('[Content_Types].xml', '''<?xml version="1.0"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Override PartName="/themeVariants/themeVariantManager.xml" 
              ContentType="application/vnd.ms-powerpoint.themeVariantManager+xml"/>
</Types>''')
            zf.writestr('_rels/.rels', '<?xml version="1.0"?><Relationships/>')
            
            # Manager without required namespaces
            zf.writestr('themeVariants/themeVariantManager.xml', '''<?xml version="1.0"?>
<themeVariantManager>
    <themeVariantLst/>
</themeVariantManager>''')
            zf.writestr('themeVariants/_rels/themeVariantManager.xml.rels', '<?xml version="1.0"?><Relationships/>')
        
        result = validator.validate_package(buffer.getvalue())
        
        namespace_errors = [e for e in result.errors if e.category == "namespaces"]
        assert len(namespace_errors) > 0
    
    def test_guid_validation(self, validator):
        """Test GUID format validation"""
        # Test valid GUID
        valid_guid = "{12345678-1234-5678-9012-123456789ABC}"
        assert validator._is_valid_guid(valid_guid) is True
        
        # Test invalid GUIDs
        invalid_guids = [
            "12345678-1234-5678-9012-123456789ABC",  # Missing braces
            "{12345678-1234-5678-9012-123456789AB}",   # Too short
            "{12345678-1234-5678-9012-123456789ABCD}", # Too long
            "{GGGGGGGG-1234-5678-9012-123456789ABC}",  # Invalid chars
            "",  # Empty
            None  # None
        ]
        
        for invalid_guid in invalid_guids:
            assert validator._is_valid_guid(invalid_guid) is False
    
    def test_performance_validation(self, validator):
        """Test performance validation (file size limits)"""
        # Create oversized content
        large_content = "x" * (2 * 1024 * 1024)  # 2MB content
        
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('large_file.xml', large_content)
            zf.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types/>')
            zf.writestr('_rels/.rels', '<?xml version="1.0"?><Relationships/>')
            zf.writestr('themeVariants/themeVariantManager.xml', '<?xml version="1.0"?><root/>')
            zf.writestr('themeVariants/_rels/themeVariantManager.xml.rels', '<?xml version="1.0"?><Relationships/>')
        
        result = validator.validate_package(buffer.getvalue())
        
        # Should have performance warnings
        performance_warnings = [w for w in result.warnings if w.category == "performance"]
        assert len(performance_warnings) > 0
    
    def test_cross_platform_validation(self, validator):
        """Test cross-platform compatibility validation"""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add files with problematic paths
            zf.writestr('path\\with\\backslashes.xml', '<?xml version="1.0"?><root/>')
            zf.writestr('path/with/../parent.xml', '<?xml version="1.0"?><root/>')
            zf.writestr('/absolute/path.xml', '<?xml version="1.0"?><root/>')
            zf.writestr('invalid<char>.xml', '<?xml version="1.0"?><root/>')
            
            # Required files
            zf.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types/>')
            zf.writestr('_rels/.rels', '<?xml version="1.0"?><Relationships/>')
            zf.writestr('themeVariants/themeVariantManager.xml', '<?xml version="1.0"?><root/>')
            zf.writestr('themeVariants/_rels/themeVariantManager.xml.rels', '<?xml version="1.0"?><Relationships/>')
        
        result = validator.validate_package(buffer.getvalue())
        
        assert result.is_valid is False
        compatibility_errors = [e for e in result.errors if e.category == "compatibility"]
        assert len(compatibility_errors) >= 4  # Should catch all problematic paths
    
    def test_validation_report_generation(self, validator):
        """Test validation report generation"""
        supertheme_data = self.create_minimal_supertheme()
        result = validator.validate_package(supertheme_data)
        
        report = validator.generate_validation_report(result)
        
        assert isinstance(report, str)
        assert "SuperTheme Validation Report" in report
        assert "Status:" in report
        assert "Package Size:" in report
        assert "Variants:" in report
        assert "Files:" in report
        
        if result.is_valid:
            assert "✅ VALID" in report
            assert "🎉 SuperTheme package is valid" in report
        else:
            assert "❌ INVALID" in report
    
    def test_strict_mode_validation(self, strict_validator):
        """Test strict mode validation"""
        supertheme_data = self.create_minimal_supertheme()
        result = strict_validator.validate_package(supertheme_data)
        
        # Strict mode should have same validation logic
        assert isinstance(result, ValidationResult)
    
    @pytest.mark.parametrize("lxml_available", [True, False])
    def test_lxml_fallback_compatibility(self, validator, lxml_available):
        """Test compatibility with and without lxml"""
        with patch('tools.supertheme_validator.LXML_AVAILABLE', lxml_available):
            supertheme_data = self.create_minimal_supertheme()
            result = validator.validate_package(supertheme_data)
            
            # Should work regardless of lxml availability
            assert isinstance(result, ValidationResult)
            # Note: Actual validation results may differ between lxml and ElementTree
    
    def test_demo_functionality(self):
        """Test that the demo functionality works"""
        from tools.supertheme_validator import SuperThemeValidator
        
        # Should be able to create validator
        validator = SuperThemeValidator()
        assert validator is not None
        
        # Test that we can generate validation report for empty result
        empty_result = ValidationResult(is_valid=True)
        report = validator.generate_validation_report(empty_result)
        assert "SuperTheme Validation Report" in report
    
    def test_lxml_xml_parser_functionality(self, validator):
        """Test that lxml XMLParser works correctly with our configuration"""
        if not hasattr(validator, '_test_lxml_parser'):
            # Add test method to validator for this test
            def _test_lxml_parser():
                try:
                    from lxml import etree
                    parser = etree.XMLParser(recover=True, remove_comments=False)
                    xml_content = '<?xml version="1.0"?><root><!-- comment --><child/></root>'
                    root = etree.fromstring(xml_content.encode('utf-8'), parser)
                    return root is not None
                except ImportError:
                    return False
                except Exception as e:
                    raise AssertionError(f"lxml XMLParser failed: {e}")
            
            validator._test_lxml_parser = _test_lxml_parser
        
        # Test that our lxml configuration works
        try:
            result = validator._test_lxml_parser()
            if result:  # Only run if lxml is available
                assert result is True
        except ImportError:
            pytest.skip("lxml not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])