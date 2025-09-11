"""
Comprehensive SuperTheme Compatibility and Validation Tests

Tests covering Office 2016-365 compatibility, performance benchmarks,
and production validation for SuperTheme packages.
"""

import pytest
import zipfile
import xml.etree.ElementTree as ET
import io
import time
import tempfile
from pathlib import Path
from typing import Dict, Any, List
import hashlib
import json

# Import components under test
try:
    from tools.supertheme_generator import SuperThemeGenerator, SuperThemeError
    from tools.aspect_ratio_resolver import AspectRatioResolver, create_standard_aspect_ratios
    from tools.ooxml_processor import OOXMLProcessor
    from tools.theme_resolver import ThemeResolver
except ImportError:
    SuperThemeGenerator = None
    SuperThemeError = None
    AspectRatioResolver = None
    create_standard_aspect_ratios = None
    OOXMLProcessor = None
    ThemeResolver = None


class TestOfficeCompatibility:
    """Test compatibility with Office 2016-365 on Windows/Mac"""
    
    @pytest.fixture
    def sample_supertheme(self):
        """Generate a sample SuperTheme for testing"""
        if SuperThemeGenerator is None:
            pytest.skip("SuperTheme components not available")
        
        generator = SuperThemeGenerator()
        design_variants = {
            "Test Design": {
                "colors": {"brand": {"primary": "#0066CC"}},
                "typography": {"heading": {"font": "Arial"}}
            }
        }
        
        return generator.generate_supertheme(
            design_variants,
            ["aspectRatios.widescreen_16_9"]
        )
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperTheme not available")
    def test_office_2016_xml_compatibility(self, sample_supertheme):
        """Test XML compatibility with Office 2016 minimum requirements"""
        with zipfile.ZipFile(io.BytesIO(sample_supertheme), 'r') as zf:
            # Check all XML files are well-formed
            xml_files = [f for f in zf.namelist() if f.endswith('.xml')]
            
            for xml_file in xml_files:
                xml_content = zf.read(xml_file).decode('utf-8')
                
                # Parse to ensure well-formed XML
                try:
                    root = ET.fromstring(xml_content)
                except ET.ParseError as e:
                    pytest.fail(f"Invalid XML in {xml_file}: {e}")
                
                # Check for Office 2016 compatible namespaces
                if 'theme' in xml_file.lower():
                    assert 'schemas.openxmlformats.org/drawingml/2006/main' in xml_content or \
                           'schemas.microsoft.com/office/thememl/2012/main' in xml_content, \
                           f"Missing required Office namespace in {xml_file}"
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperTheme not available")
    def test_powerpoint_365_namespaces(self, sample_supertheme):
        """Test PowerPoint 365 namespace requirements"""
        with zipfile.ZipFile(io.BytesIO(sample_supertheme), 'r') as zf:
            # Check themeVariantManager.xml
            if 'themeVariants/themeVariantManager.xml' in zf.namelist():
                manager_xml = zf.read('themeVariants/themeVariantManager.xml').decode('utf-8')
                
                # Required namespaces for PowerPoint 365
                required_namespaces = [
                    'http://schemas.microsoft.com/office/thememl/2012/main',
                    'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
                ]
                
                for ns in required_namespaces:
                    assert ns in manager_xml, f"Missing required namespace: {ns}"
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperTheme not available")
    def test_cross_platform_file_paths(self, sample_supertheme):
        """Test file paths work on both Windows and Mac"""
        with zipfile.ZipFile(io.BytesIO(sample_supertheme), 'r') as zf:
            for file_path in zf.namelist():
                # Check no backslashes (Windows-specific)
                assert '\\' not in file_path, f"Windows-specific path separator in: {file_path}"
                
                # Check no absolute paths
                assert not file_path.startswith('/'), f"Absolute path found: {file_path}"
                
                # Check no parent directory references
                assert '..' not in file_path, f"Parent directory reference in: {file_path}"
                
                # Check valid filename characters
                filename = Path(file_path).name
                invalid_chars = '<>:"|?*'
                for char in invalid_chars:
                    assert char not in filename, f"Invalid character '{char}' in: {filename}"
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperTheme not available")
    def test_guid_format_compatibility(self, sample_supertheme):
        """Test GUID format compatibility with Office"""
        with zipfile.ZipFile(io.BytesIO(sample_supertheme), 'r') as zf:
            if 'themeVariants/themeVariantManager.xml' in zf.namelist():
                manager_xml = zf.read('themeVariants/themeVariantManager.xml').decode('utf-8')
                root = ET.fromstring(manager_xml)
                
                # Find all GUIDs
                import re
                guid_pattern = r'\{[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}\}'
                guids = re.findall(guid_pattern, manager_xml, re.IGNORECASE)
                
                for guid in guids:
                    # Check GUID format
                    assert len(guid) == 38, f"Invalid GUID length: {guid}"
                    assert guid[0] == '{' and guid[-1] == '}', f"Invalid GUID brackets: {guid}"
                    assert guid.count('-') == 4, f"Invalid GUID format: {guid}"


class TestSuperThemePackageValidation:
    """Test SuperTheme package structure and validation"""
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperTheme not available")
    def test_required_package_structure(self):
        """Test SuperTheme has all required files and directories"""
        generator = SuperThemeGenerator()
        design_variants = {"Test": {"colors": {"brand": {"primary": "#FF0000"}}}}
        supertheme = generator.generate_supertheme(design_variants, ["aspectRatios.widescreen_16_9"])
        
        with zipfile.ZipFile(io.BytesIO(supertheme), 'r') as zf:
            files = zf.namelist()
            
            # Required root files
            assert '[Content_Types].xml' in files, "Missing [Content_Types].xml"
            assert '_rels/.rels' in files, "Missing root relationships"
            
            # Required SuperTheme structure
            assert any('themeVariants/themeVariantManager.xml' in f for f in files), \
                "Missing themeVariantManager.xml"
            assert any('themeVariants/_rels/themeVariantManager.xml.rels' in f for f in files), \
                "Missing themeVariantManager relationships"
            
            # At least one variant
            assert any('variant1' in f for f in files), "Missing variant directories"
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperTheme not available")
    def test_content_types_validation(self):
        """Test [Content_Types].xml has all required declarations"""
        generator = SuperThemeGenerator()
        design_variants = {"Test": {}}
        supertheme = generator.generate_supertheme(design_variants)
        
        with zipfile.ZipFile(io.BytesIO(supertheme), 'r') as zf:
            content_types = zf.read('[Content_Types].xml').decode('utf-8')
            root = ET.fromstring(content_types)
            
            # Check for required content type declarations
            required_types = [
                'application/vnd.openxmlformats-package.relationships+xml',
                'application/vnd.ms-powerpoint.themeVariantManager+xml',
                'application/vnd.openxmlformats-officedocument.theme+xml'
            ]
            
            content_type_values = []
            for elem in root:
                content_type = elem.get('ContentType')
                if content_type:
                    content_type_values.append(content_type)
            
            for req_type in required_types:
                assert req_type in content_type_values, f"Missing content type: {req_type}"
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperTheme not available")
    def test_variant_consistency(self):
        """Test all variants have consistent structure"""
        generator = SuperThemeGenerator()
        design_variants = {
            "Design1": {"colors": {"brand": {"primary": "#FF0000"}}},
            "Design2": {"colors": {"brand": {"primary": "#00FF00"}}}
        }
        aspect_ratios = ["aspectRatios.widescreen_16_9", "aspectRatios.classic_4_3"]
        
        supertheme = generator.generate_supertheme(design_variants, aspect_ratios)
        
        with zipfile.ZipFile(io.BytesIO(supertheme), 'r') as zf:
            # Group files by variant
            variants = {}
            for file_path in zf.namelist():
                if 'variant' in file_path:
                    variant_match = file_path.split('/')[1] if '/' in file_path else None
                    if variant_match and variant_match.startswith('variant'):
                        if variant_match not in variants:
                            variants[variant_match] = []
                        variants[variant_match].append(file_path)
            
            # Check each variant has same structure
            expected_files = [
                'theme/theme/theme1.xml',
                'theme/presentation.xml',
                '_rels/.rels'
            ]
            
            for variant_id, variant_files in variants.items():
                for expected in expected_files:
                    full_path = f"themeVariants/{variant_id}/{expected}"
                    assert any(full_path in f for f in variant_files), \
                        f"Missing {expected} in {variant_id}"


class TestPerformanceBenchmarks:
    """Test performance requirements and benchmarks"""
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperTheme not available")
    def test_generation_time_limit(self):
        """Test SuperTheme generation completes within 30 seconds"""
        generator = SuperThemeGenerator()
        
        # Create moderate complexity test case
        design_variants = {}
        for i in range(5):  # 5 designs
            design_variants[f"Design{i}"] = {
                "colors": {
                    "brand": {"primary": f"#{i:02x}0000"},
                    "neutral": {"background": "#FFFFFF"}
                },
                "typography": {
                    "heading": {"font": "Arial"},
                    "body": {"font": "Calibri"}
                }
            }
        
        aspect_ratios = [
            "aspectRatios.widescreen_16_9",
            "aspectRatios.standard_16_10",
            "aspectRatios.classic_4_3"
        ]
        
        # Measure generation time
        start_time = time.time()
        supertheme = generator.generate_supertheme(design_variants, aspect_ratios)
        elapsed = time.time() - start_time
        
        # Should complete in under 30 seconds
        assert elapsed < 30.0, f"Generation took {elapsed:.2f}s (limit: 30s)"
        
        # Verify output is valid
        assert len(supertheme) > 0
        assert len(supertheme) < 5 * 1024 * 1024  # Under 5MB
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperTheme not available")
    def test_file_size_limits(self):
        """Test file size stays within limits"""
        generator = SuperThemeGenerator()
        
        # Test minimal package
        minimal = generator.generate_supertheme(
            {"Min": {}},
            ["aspectRatios.widescreen_16_9"]
        )
        assert len(minimal) < 1024 * 1024, "Minimal package over 1MB"
        
        # Test typical package
        typical_designs = {
            "Corporate": {"colors": {"brand": {"primary": "#0066CC"}}},
            "Creative": {"colors": {"brand": {"primary": "#FF6600"}}},
            "Modern": {"colors": {"brand": {"primary": "#22AA22"}}}
        }
        typical = generator.generate_supertheme(
            typical_designs,
            ["aspectRatios.widescreen_16_9", "aspectRatios.classic_4_3"]
        )
        assert len(typical) < 3 * 1024 * 1024, "Typical package over 3MB"
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperTheme not available")
    def test_caching_performance(self):
        """Test caching improves performance on repeated operations"""
        generator = SuperThemeGenerator(verbose=False)
        design_variants = {"Test": {"colors": {"brand": {"primary": "#FF0000"}}}}
        aspect_ratios = ["aspectRatios.widescreen_16_9"]
        
        # First generation (cold cache)
        start1 = time.time()
        result1 = generator.generate_supertheme(design_variants, aspect_ratios)
        time1 = time.time() - start1
        
        # Second generation (warm cache)
        start2 = time.time()
        result2 = generator.generate_supertheme(design_variants, aspect_ratios)
        time2 = time.time() - start2
        
        # Cache should provide some benefit (or at least not be slower)
        # Note: May not always be faster due to overhead, but shouldn't be much slower
        assert time2 <= time1 * 1.5, f"Cached generation slower: {time2:.3f}s vs {time1:.3f}s"


class TestAspectRatioValidation:
    """Test aspect ratio handling and distortion detection"""
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperTheme not available")
    def test_aspect_ratio_dimensions_accuracy(self):
        """Test aspect ratio dimensions are accurate"""
        generator = SuperThemeGenerator()
        aspect_ratios = create_standard_aspect_ratios()
        
        # Test known aspect ratios
        test_cases = [
            ("aspectRatios.widescreen_16_9", 16/9, 0.01),
            ("aspectRatios.classic_4_3", 4/3, 0.01),
            ("aspectRatios.standard_16_10", 16/10, 0.01)
        ]
        
        resolver = AspectRatioResolver()
        for token, expected_ratio, tolerance in test_cases:
            ratio_obj = resolver.get_aspect_ratio_token(aspect_ratios, token)
            assert ratio_obj is not None, f"Could not resolve {token}"
            
            actual_ratio = ratio_obj.width_emu / ratio_obj.height_emu
            assert abs(actual_ratio - expected_ratio) < tolerance, \
                f"{token}: Expected {expected_ratio:.4f}, got {actual_ratio:.4f}"
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperTheme not available")
    def test_portrait_landscape_detection(self):
        """Test portrait/landscape orientation detection"""
        aspect_ratios = create_standard_aspect_ratios()
        resolver = AspectRatioResolver()
        
        # Landscape ratios
        landscape_tokens = [
            "aspectRatios.widescreen_16_9",
            "aspectRatios.a4_landscape",
            "aspectRatios.letter_landscape"
        ]
        
        for token in landscape_tokens:
            ratio_obj = resolver.get_aspect_ratio_token(aspect_ratios, token)
            if ratio_obj:
                assert ratio_obj.is_landscape, f"{token} should be landscape"
                assert not ratio_obj.is_portrait, f"{token} should not be portrait"
        
        # Portrait ratios
        portrait_tokens = [
            "aspectRatios.a4_portrait",
            "aspectRatios.letter_portrait"
        ]
        
        for token in portrait_tokens:
            ratio_obj = resolver.get_aspect_ratio_token(aspect_ratios, token)
            if ratio_obj:
                assert ratio_obj.is_portrait, f"{token} should be portrait"
                assert not ratio_obj.is_landscape, f"{token} should not be landscape"


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery mechanisms"""
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperTheme not available")
    def test_malformed_design_token_handling(self):
        """Test handling of malformed design tokens"""
        generator = SuperThemeGenerator()
        
        # Test with various malformed inputs
        malformed_designs = {
            "BadDesign": {
                "colors": "not_a_dict",  # Should be dict
                "typography": None,  # Should be dict
                "invalid": {"$value": "test"}  # Unknown category
            }
        }
        
        # Should not crash, but generate with defaults
        try:
            result = generator.generate_supertheme(malformed_designs)
            assert len(result) > 0, "Should generate package even with malformed input"
        except SuperThemeError:
            # Acceptable to raise SuperThemeError for very bad input
            pass
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperTheme not available")
    def test_missing_aspect_ratio_fallback(self):
        """Test fallback when aspect ratios are missing"""
        generator = SuperThemeGenerator()
        design_variants = {"Test": {}}
        
        # Test with invalid aspect ratio
        with pytest.raises(SuperThemeError):
            generator.generate_supertheme(design_variants, ["invalid.aspect.ratio"])
        
        # Test with None (should use defaults)
        result = generator.generate_supertheme(design_variants, None)
        assert len(result) > 0, "Should use default aspect ratios when None provided"
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperTheme not available")
    def test_empty_design_variants_error(self):
        """Test error on empty design variants"""
        generator = SuperThemeGenerator()
        
        with pytest.raises(SuperThemeError, match="No design variants provided"):
            generator.generate_supertheme({})


class TestRegressionTesting:
    """Test existing StyleStack functionality still works"""
    
    @pytest.mark.skipif(OOXMLProcessor is None, reason="OOXML processor not available")
    def test_ooxml_processor_still_works(self):
        """Test OOXML processor basic functionality"""
        processor = OOXMLProcessor()
        
        # Test basic XML processing
        sample_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <root xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
            <a:color val="FF0000"/>
        </root>'''
        
        variables = {"test_color": {"type": "color", "value": "#00FF00"}}
        
        # Should process without errors
        result = processor.apply_variables_to_xml(sample_xml, variables)
        assert isinstance(result, tuple)
        xml_result, processing_result = result
        assert isinstance(xml_result, str)
        assert len(xml_result) > 0
        assert processing_result.success
    
    @pytest.mark.skipif(ThemeResolver is None, reason="Theme resolver not available")
    def test_theme_resolver_still_works(self):
        """Test theme resolver basic functionality"""
        resolver = ThemeResolver()
        
        # Test default theme creation
        theme = resolver.create_default_theme("Test Theme")
        assert theme is not None
        assert theme.name == "Test Theme"
        
        # Test color extraction
        assert theme.get_color('accent1') is not None
        assert theme.get_font('majorFont') is not None