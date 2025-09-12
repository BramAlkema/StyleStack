"""
Test Suite for SuperTheme Generator Core Engine

Comprehensive tests for Microsoft PowerPoint SuperTheme generation including:
- Complete SuperTheme package creation
- Microsoft themeVariantManager.xml compliance
- Multi-design variant support with token-based aspect ratios
- ZIP package structure validation
- GUID management and relationship handling
- Office compatibility testing
"""

import pytest
import zipfile
import io
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from pathlib import Path
import json

# Import components to be implemented
try:
    from tools.supertheme_generator import SuperThemeGenerator
    from tools.aspect_ratio_resolver import AspectRatioResolver, create_standard_aspect_ratios
    from tools.theme_resolver import ThemeResolver, Theme
    from tools.emu_types import EMUValue
except ImportError:
    # Components will be implemented during this task
    SuperThemeGenerator = None
    AspectRatioResolver = None
    create_standard_aspect_ratios = None
    ThemeResolver = None
    Theme = None
    EMUValue = None


class TestSuperThemePackageGeneration:
    """Test complete SuperTheme package creation"""
    
    @pytest.fixture
    def sample_design_variants(self):
        """Sample design variant token structures"""
        return {
            "Corporate Blue": {
                "colors": {
                    "brand": {
                        "primary": {"$type": "color", "$value": "#0066CC"},
                        "secondary": {"$type": "color", "$value": "#4D94FF"}
                    }
                },
                "typography": {
                    "heading": {
                        "family": {"$type": "fontFamily", "$value": "Arial"},
                        "size": {
                            "$aspectRatio": {
                                "{aspectRatios.widescreen_16_9}": "44pt",
                                "{aspectRatios.a4_landscape}": "36pt"
                            }
                        }
                    }
                }
            },
            "Corporate Red": {
                "colors": {
                    "brand": {
                        "primary": {"$type": "color", "$value": "#CC0000"},
                        "secondary": {"$type": "color", "$value": "#FF4D4D"}
                    }
                },
                "typography": {
                    "heading": {
                        "family": {"$type": "fontFamily", "$value": "Arial"},
                        "size": {
                            "$aspectRatio": {
                                "{aspectRatios.widescreen_16_9}": "44pt",
                                "{aspectRatios.a4_landscape}": "36pt"
                            }
                        }
                    }
                }
            }
        }
    
    @pytest.fixture
    def sample_aspect_ratios(self):
        """Sample aspect ratio tokens"""
        if create_standard_aspect_ratios is None:
            pytest.skip("create_standard_aspect_ratios not implemented yet")
        return create_standard_aspect_ratios()
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperThemeGenerator not implemented yet")
    def test_supertheme_generator_initialization(self):
        """Test SuperTheme generator can be initialized"""
        generator = SuperThemeGenerator(verbose=True)
        
        assert generator is not None
        assert hasattr(generator, 'generate_supertheme')
        assert hasattr(generator, 'theme_resolver')
        assert hasattr(generator, 'aspect_resolver')
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperThemeGenerator not implemented yet") 
    def test_complete_supertheme_generation(self, sample_design_variants, sample_aspect_ratios):
        """Test complete SuperTheme package generation"""
        generator = SuperThemeGenerator(verbose=True)
        
        # Combine design variants with aspect ratios
        complete_tokens = sample_aspect_ratios.copy()
        complete_tokens.update(sample_design_variants)
        
        # Generate SuperTheme
        aspect_ratios = ["aspectRatios.widescreen_16_9", "aspectRatios.a4_landscape"]
        supertheme_package = generator.generate_supertheme(
            design_variants=sample_design_variants,
            aspect_ratios=aspect_ratios
        )
        
        # Verify package is valid ZIP
        assert isinstance(supertheme_package, bytes)
        assert len(supertheme_package) > 0
        
        # Verify ZIP can be opened
        with zipfile.ZipFile(io.BytesIO(supertheme_package), 'r') as zf:
            file_list = zf.namelist()
            
            # Check required SuperTheme structure
            assert '[Content_Types].xml' in file_list
            assert '_rels/.rels' in file_list
            assert 'themeVariants/themeVariantManager.xml' in file_list
            
            # Check variant directories exist
            variant_dirs = [f for f in file_list if f.startswith('themeVariants/variant') and f.endswith('/')]
            expected_variants = len(sample_design_variants) * len(aspect_ratios)
            assert len([d for d in variant_dirs if d != 'themeVariants/']) >= expected_variants
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperThemeGenerator not implemented yet")
    def test_supertheme_file_size_limit(self, sample_design_variants):
        """Test SuperTheme respects 5MB file size limit"""
        generator = SuperThemeGenerator()
        
        supertheme_package = generator.generate_supertheme(
            design_variants=sample_design_variants,
            aspect_ratios=["aspectRatios.widescreen_16_9"]
        )
        
        # Verify file size is under 5MB limit
        package_size_mb = len(supertheme_package) / (1024 * 1024)
        assert package_size_mb < 5.0, f"SuperTheme package {package_size_mb:.2f}MB exceeds 5MB limit"


class TestThemeVariantManagerXML:
    """Test Microsoft themeVariantManager.xml generation and compliance"""
    
    @pytest.fixture
    def sample_theme_variants(self):
        """Sample theme variant data structure"""
        if Theme is None:
            pytest.skip("Theme not implemented yet")
        return {
            "Corporate Blue 16:9": (
                Theme(name="Corporate Blue 16:9"),
                "<presentation></presentation>",
                "aspectRatios.widescreen_16_9"
            ),
            "Corporate Blue A4": (
                Theme(name="Corporate Blue A4"),
                "<presentation></presentation>",
                "aspectRatios.a4_landscape"
            ),
            "Corporate Red 16:9": (
                Theme(name="Corporate Red 16:9"),
                "<presentation></presentation>",
                "aspectRatios.widescreen_16_9"
            )
        }
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperThemeGenerator not implemented yet")
    def test_theme_variant_manager_xml_structure(self, sample_theme_variants):
        """Test themeVariantManager.xml has correct Microsoft XML structure"""
        generator = SuperThemeGenerator()
        
        aspect_ratios = ["aspectRatios.widescreen_16_9", "aspectRatios.a4_landscape"]
        manager_xml = generator._generate_variant_manager(sample_theme_variants, aspect_ratios)
        
        # Parse XML and validate structure
        root = ET.fromstring(manager_xml)
        
        # Check Microsoft namespace
        assert root.tag.endswith('themeVariantManager')
        assert 'http://schemas.microsoft.com/office/thememl/2012/main' in root.tag
        
        # Check for themeVariantLst
        variant_list = root.find('.//{http://schemas.microsoft.com/office/thememl/2012/main}themeVariantLst')
        assert variant_list is not None
        
        # Check variant elements
        variants = variant_list.findall('.//{http://schemas.microsoft.com/office/thememl/2012/main}themeVariant')
        assert len(variants) >= len(sample_theme_variants)
        
        # Verify each variant has required attributes
        for variant in variants:
            assert 'name' in variant.attrib
            assert 'vid' in variant.attrib  # GUID
            assert 'cx' in variant.attrib   # Width EMU
            assert 'cy' in variant.attrib   # Height EMU
            assert variant.attrib['cx'].isdigit()
            assert variant.attrib['cy'].isdigit()
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperThemeGenerator not implemented yet") 
    def test_guid_consistency_for_design_groups(self, sample_theme_variants):
        """Test that variants of same design have consistent GUIDs"""
        generator = SuperThemeGenerator()
        
        aspect_ratios = ["aspectRatios.widescreen_16_9", "aspectRatios.a4_landscape"]
        manager_xml = generator._generate_variant_manager(sample_theme_variants, aspect_ratios)
        
        root = ET.fromstring(manager_xml)
        variants = root.findall('.//{http://schemas.microsoft.com/office/thememl/2012/main}themeVariant')
        
        # Group variants by design name
        design_guids = {}
        for variant in variants:
            name = variant.get('name')
            guid = variant.get('vid')
            design_name = name.rsplit(' ', 1)[0] if ' ' in name else name  # Remove aspect ratio
            
            if design_name not in design_guids:
                design_guids[design_name] = guid
            else:
                # Same design should have same GUID
                assert design_guids[design_name] == guid, f"Inconsistent GUID for design {design_name}"
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperThemeGenerator not implemented yet")
    def test_emu_dimensions_accuracy(self, sample_theme_variants):
        """Test EMU dimensions match aspect ratio specifications"""
        generator = SuperThemeGenerator()
        
        aspect_ratios = ["aspectRatios.widescreen_16_9", "aspectRatios.a4_landscape"]
        manager_xml = generator._generate_variant_manager(sample_theme_variants, aspect_ratios)
        
        root = ET.fromstring(manager_xml)
        variants = root.findall('.//{http://schemas.microsoft.com/office/thememl/2012/main}themeVariant')
        
        # Expected EMU dimensions (from aspect ratio resolver)
        expected_dimensions = {
            "16:9": {"width": 12192000, "height": 6858000},     # 13.33" × 7.5"
            "A4": {"width": 10692000, "height": 7560000}       # 297mm × 210mm
        }
        
        for variant in variants:
            name = variant.get('name')
            cx = int(variant.get('cx'))
            cy = int(variant.get('cy'))
            
            if "16:9" in name:
                assert cx == expected_dimensions["16:9"]["width"]
                assert cy == expected_dimensions["16:9"]["height"]
            elif "A4" in name:
                assert cx == expected_dimensions["A4"]["width"]
                assert cy == expected_dimensions["A4"]["height"]


class TestSuperThemeZIPStructure:
    """Test SuperTheme ZIP package structure compliance"""
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperThemeGenerator not implemented yet")
    def test_content_types_xml(self):
        """Test [Content_Types].xml is properly generated"""
        generator = SuperThemeGenerator()
        
        design_variants = {"Test Design": {"colors": {"primary": "#FF0000"}}}
        supertheme_package = generator.generate_supertheme(design_variants, ["aspectRatios.widescreen_16_9"])
        
        with zipfile.ZipFile(io.BytesIO(supertheme_package), 'r') as zf:
            content_types_xml = zf.read('[Content_Types].xml').decode('utf-8')
            
            # Parse and validate Content_Types.xml
            root = ET.fromstring(content_types_xml)
            assert root.tag.endswith('Types')
            
            # Should contain required content type definitions
            overrides = root.findall('.//Override')
            part_names = [o.get('PartName') for o in overrides]
            
            assert '/themeVariants/themeVariantManager.xml' in part_names
            assert any('/themeVariants/variant' in name for name in part_names)
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperThemeGenerator not implemented yet")
    def test_relationship_files_structure(self):
        """Test _rels relationship files are properly created"""
        generator = SuperThemeGenerator()
        
        design_variants = {"Test Design": {"colors": {"primary": "#FF0000"}}}
        supertheme_package = generator.generate_supertheme(design_variants, ["aspectRatios.widescreen_16_9"])
        
        with zipfile.ZipFile(io.BytesIO(supertheme_package), 'r') as zf:
            file_list = zf.namelist()
            
            # Main relationships
            assert '_rels/.rels' in file_list
            
            # Theme variant relationships
            assert 'themeVariants/_rels/themeVariantManager.xml.rels' in file_list
            
            # Individual variant relationships
            variant_rels = [f for f in file_list if 'themeVariants/variant' in f and '_rels' in f]
            assert len(variant_rels) > 0
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperThemeGenerator not implemented yet")
    def test_variant_directory_structure(self):
        """Test each variant has complete directory structure"""
        generator = SuperThemeGenerator()
        
        design_variants = {
            "Design A": {"colors": {"primary": "#FF0000"}},
            "Design B": {"colors": {"primary": "#00FF00"}}
        }
        aspect_ratios = ["aspectRatios.widescreen_16_9", "aspectRatios.a4_landscape"]
        
        supertheme_package = generator.generate_supertheme(design_variants, aspect_ratios)
        
        with zipfile.ZipFile(io.BytesIO(supertheme_package), 'r') as zf:
            file_list = zf.namelist()
            
            # Count variant directories
            variant_dirs = set()
            for file_path in file_list:
                if file_path.startswith('themeVariants/variant') and '/' in file_path[len('themeVariants/variant'):]:
                    variant_num = file_path.split('/')[1]  # variant1, variant2, etc.
                    variant_dirs.add(variant_num)
            
            # Should have variant for each design × aspect ratio combination
            expected_variants = len(design_variants) * len(aspect_ratios)
            assert len(variant_dirs) == expected_variants
            
            # Each variant should have complete structure
            for variant_dir in variant_dirs:
                required_files = [
                    f'themeVariants/{variant_dir}/theme/theme/theme1.xml',
                    f'themeVariants/{variant_dir}/theme/presentation.xml',
                    f'themeVariants/{variant_dir}/_rels/.rels'
                ]
                
                for required_file in required_files:
                    assert required_file in file_list, f"Missing {required_file} in {variant_dir}"


class TestSuperThemeErrorHandling:
    """Test error handling and validation in SuperTheme generation"""
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperThemeGenerator not implemented yet")
    def test_empty_design_variants_error(self):
        """Test error when no design variants provided"""
        generator = SuperThemeGenerator()
        
        with pytest.raises(ValueError, match="No design variants provided"):
            generator.generate_supertheme({}, ["aspectRatios.widescreen_16_9"])
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperThemeGenerator not implemented yet")
    def test_invalid_aspect_ratio_error(self):
        """Test error when invalid aspect ratio token provided"""
        generator = SuperThemeGenerator()
        
        design_variants = {"Test Design": {"colors": {"primary": "#FF0000"}}}
        
        with pytest.raises(ValueError, match="Invalid aspect ratio token"):
            generator.generate_supertheme(design_variants, ["aspectRatios.nonexistent"])
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperThemeGenerator not implemented yet")
    def test_malformed_design_tokens_error(self):
        """Test error handling for malformed design variant tokens"""
        generator = SuperThemeGenerator()
        
        malformed_variants = {
            "Malformed Design": {
                "colors": "invalid_structure"  # Should be object, not string
            }
        }
        
        with pytest.raises(ValueError, match="Malformed design variant"):
            generator.generate_supertheme(malformed_variants, ["aspectRatios.widescreen_16_9"])


class TestSuperThemePerformance:
    """Test SuperTheme generation performance and optimization"""
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperThemeGenerator not implemented yet")
    def test_generation_time_under_30_seconds(self):
        """Test SuperTheme generation completes within 30 seconds for 12 variants"""
        import time
        
        generator = SuperThemeGenerator()
        
        # Create large variant set (4 designs × 3 aspect ratios = 12 variants)
        design_variants = {
            f"Design {i}": {
                "colors": {
                    "primary": f"#{i:02d}{i:02d}{i:02d}",
                    "secondary": f"#{i+1:02d}{i+1:02d}{i+1:02d}"
                }
            }
            for i in range(1, 5)
        }
        
        aspect_ratios = [
            "aspectRatios.widescreen_16_9",
            "aspectRatios.standard_16_10", 
            "aspectRatios.classic_4_3"
        ]
        
        start_time = time.time()
        supertheme_package = generator.generate_supertheme(design_variants, aspect_ratios)
        generation_time = time.time() - start_time
        
        assert generation_time < 30.0, f"SuperTheme generation took {generation_time:.2f}s (limit: 30s)"
        assert len(supertheme_package) > 0
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperThemeGenerator not implemented yet")
    def test_caching_improves_performance(self):
        """Test that caching improves repeated generation performance"""
        import time
        
        generator = SuperThemeGenerator()
        design_variants = {"Test Design": {"colors": {"primary": "#FF0000"}}}
        aspect_ratios = ["aspectRatios.widescreen_16_9"]
        
        # First generation (cold cache)
        start_time = time.time()
        generator.generate_supertheme(design_variants, aspect_ratios)
        first_time = time.time() - start_time
        
        # Second generation (warm cache)
        start_time = time.time()
        generator.generate_supertheme(design_variants, aspect_ratios)
        second_time = time.time() - start_time
        
        # Second generation should be faster (or at least not significantly slower)
        assert second_time <= first_time * 1.2, "Caching did not improve performance"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])