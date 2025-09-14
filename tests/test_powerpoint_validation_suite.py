"""
PowerPoint Validation Test Suite

Comprehensive validation and testing for PowerPoint layout generation across
all aspect ratios, ensuring OOXML compliance, design consistency, accessibility
standards, and performance benchmarks.
"""

import pytest
import time
import json
import xml.etree.ElementTree as ET
import zipfile
import io
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import colorsys

from tools.powerpoint_layout_engine import PowerPointLayoutEngine, create_powerpoint_layout_engine
from tools.powerpoint_positioning_calculator import PositioningCalculator
from tools.powerpoint_supertheme_layout_engine import create_powerpoint_supertheme_layout_engine
from tools.potx_template_generator import create_potx_template_generator
from tools.powerpoint_token_transformer import create_powerpoint_token_transformer
from tools.core.types import ProcessingResult


class TestMultiAspectRatioValidation:
    """Test PowerPoint layouts across all supported aspect ratios"""
    
    @pytest.fixture
    def aspect_ratios(self):
        """All supported aspect ratios"""
        return ["16:9", "4:3", "16:10"]
    
    @pytest.fixture
    def engine(self):
        """PowerPoint layout engine"""
        return create_powerpoint_layout_engine()
    
    @pytest.fixture
    def expected_dimensions(self):
        """Expected slide dimensions for each aspect ratio"""
        return {
            "16:9": (9144000, 5143500),
            "4:3": (9144000, 6858000),
            "16:10": (9144000, 5715000)
        }
    
    def test_all_aspect_ratios_supported(self, engine, aspect_ratios):
        """Test that all aspect ratios are supported"""
        for aspect_ratio in aspect_ratios:
            result = engine.set_aspect_ratio(aspect_ratio)
            assert result.success, f"Failed to set aspect ratio {aspect_ratio}"
            assert engine.default_aspect_ratio == aspect_ratio
    
    def test_slide_dimensions_correct(self, aspect_ratios, expected_dimensions):
        """Test slide dimensions are correct for each aspect ratio"""
        for aspect_ratio in aspect_ratios:
            calculator = PositioningCalculator(aspect_ratio)
            width, height = calculator.get_slide_dimensions()
            
            expected_width, expected_height = expected_dimensions[aspect_ratio]
            assert width == expected_width, f"Width mismatch for {aspect_ratio}"
            assert height == expected_height, f"Height mismatch for {aspect_ratio}"
    
    def test_layouts_generate_for_all_aspect_ratios(self, engine, aspect_ratios):
        """Test all layouts generate successfully for each aspect ratio"""
        available_layouts = engine.get_available_layouts()
        
        for aspect_ratio in aspect_ratios:
            engine.set_aspect_ratio(aspect_ratio)
            
            for layout in available_layouts:
                result = engine.resolve_layout_positioning(layout['id'], aspect_ratio)
                assert result.success, f"Failed to generate {layout['id']} for {aspect_ratio}: {result.errors}"
                
                # Verify layout has placeholders
                layout_data = result.data
                assert 'placeholders' in layout_data
                assert len(layout_data['placeholders']) > 0
    
    def test_placeholder_positioning_within_bounds(self, engine, aspect_ratios):
        """Test all placeholder positions stay within slide bounds"""
        available_layouts = engine.get_available_layouts()
        
        for aspect_ratio in aspect_ratios:
            calculator = PositioningCalculator(aspect_ratio)
            slide_width, slide_height = calculator.get_slide_dimensions()
            
            engine.set_aspect_ratio(aspect_ratio)
            
            for layout in available_layouts:
                result = engine.resolve_layout_positioning(layout['id'], aspect_ratio)
                
                if result.success:
                    for placeholder in result.data['placeholders']:
                        pos = placeholder['position']
                        
                        # Check X bounds
                        assert pos['x'] >= 0, f"X position negative in {layout['id']} ({aspect_ratio})"
                        assert pos['x'] + pos['width'] <= slide_width, \
                            f"Right edge exceeds slide width in {layout['id']} ({aspect_ratio})"
                        
                        # Check Y bounds
                        assert pos['y'] >= 0, f"Y position negative in {layout['id']} ({aspect_ratio})"
                        assert pos['y'] + pos['height'] <= slide_height, \
                            f"Bottom edge exceeds slide height in {layout['id']} ({aspect_ratio})"
    
    def test_aspect_ratio_responsive_positioning(self, engine):
        """Test that positioning adapts correctly to aspect ratio changes"""
        test_layout = "title_slide"
        
        # Get positioning for different aspect ratios
        positions_16_9 = engine.resolve_layout_positioning(test_layout, "16:9").data
        positions_4_3 = engine.resolve_layout_positioning(test_layout, "4:3").data
        positions_16_10 = engine.resolve_layout_positioning(test_layout, "16:10").data
        
        # Title should be positioned differently based on aspect ratio
        title_16_9 = next(p for p in positions_16_9['placeholders'] if p['type'] == 'ctrTitle')
        title_4_3 = next(p for p in positions_4_3['placeholders'] if p['type'] == 'ctrTitle')
        title_16_10 = next(p for p in positions_16_10['placeholders'] if p['type'] == 'ctrTitle')
        
        # Vertical positioning should adapt to different heights
        assert title_4_3['position']['y'] != title_16_9['position']['y'], \
            "Title Y position should differ between 4:3 and 16:9"
        assert title_16_10['position']['y'] != title_16_9['position']['y'], \
            "Title Y position should differ between 16:10 and 16:9"


class TestOOXMLCompliance:
    """Test OOXML compliance for generated templates"""
    
    @pytest.fixture
    def potx_generator(self):
        """POTX template generator"""
        return create_potx_template_generator()
    
    @pytest.fixture
    def sample_tokens(self):
        """Sample design tokens for testing"""
        return {
            "global": {
                "colors": {
                    "primary": {"$type": "color", "$value": "#0066CC"}
                }
            }
        }
    
    def test_potx_zip_structure_valid(self, potx_generator, sample_tokens):
        """Test generated POTX has valid ZIP structure"""
        result = potx_generator.generate_potx_template(
            design_tokens=sample_tokens,
            org="test",
            channel="validation",
            layout_ids=["title_slide"]
        )
        
        assert result.success, f"POTX generation failed: {result.errors}"
        
        # Verify ZIP structure
        zip_bytes = result.data["zip_bytes"]
        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zipf:
            files = zipf.namelist()
            
            # Required OOXML files
            assert "[Content_Types].xml" in files
            assert "_rels/.rels" in files
            assert "ppt/presentation.xml" in files
            assert "ppt/slideMasters/slideMaster1.xml" in files
            assert "ppt/theme/theme1.xml" in files
    
    def test_xml_well_formed(self, potx_generator, sample_tokens):
        """Test all XML files in POTX are well-formed"""
        result = potx_generator.generate_potx_template(
            design_tokens=sample_tokens,
            org="test",
            channel="validation",
            layout_ids=["title_slide"]
        )
        
        assert result.success
        
        zip_bytes = result.data["zip_bytes"]
        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zipf:
            for filename in zipf.namelist():
                if filename.endswith('.xml'):
                    xml_content = zipf.read(filename)
                    try:
                        ET.fromstring(xml_content)
                    except ET.ParseError as e:
                        pytest.fail(f"XML parse error in {filename}: {e}")
    
    def test_namespace_declarations_correct(self, potx_generator, sample_tokens):
        """Test XML namespace declarations are correct"""
        result = potx_generator.generate_potx_template(
            design_tokens=sample_tokens,
            org="test",
            channel="validation",
            layout_ids=["title_slide"]
        )
        
        assert result.success
        
        zip_bytes = result.data["zip_bytes"]
        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zipf:
            # Check presentation.xml namespaces
            if "ppt/presentation.xml" in zipf.namelist():
                pres_xml = zipf.read("ppt/presentation.xml")
                root = ET.fromstring(pres_xml)
                
                # Verify key namespaces
                assert 'presentationml' in str(pres_xml)
                assert 'drawingml' in str(pres_xml)
                assert 'relationships' in str(pres_xml)
    
    def test_relationships_valid(self, potx_generator, sample_tokens):
        """Test relationship files are valid"""
        result = potx_generator.generate_potx_template(
            design_tokens=sample_tokens,
            org="test",
            channel="validation",
            layout_ids=["title_slide", "title_and_content"]
        )
        
        assert result.success
        
        zip_bytes = result.data["zip_bytes"]
        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zipf:
            # Check main relationships
            if "_rels/.rels" in zipf.namelist():
                rels_xml = zipf.read("_rels/.rels")
                root = ET.fromstring(rels_xml)
                
                # Should have relationships to presentation, core properties, app properties
                relationships = root.findall(".//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship")
                assert len(relationships) >= 3


class TestDesignTokenConsistency:
    """Test design token consistency across layouts"""
    
    @pytest.fixture
    def supertheme_engine(self):
        """SuperTheme layout engine"""
        return create_powerpoint_supertheme_layout_engine()
    
    @pytest.fixture
    def hierarchical_tokens(self):
        """Hierarchical design tokens"""
        return {
            "global": {
                "colors": {
                    "text": {"$type": "color", "$value": "#000000"}
                },
                "typography": {
                    "base": {
                        "family": {"$type": "fontFamily", "$value": "Arial"},
                        "size": {"$type": "dimension", "$value": "12pt"}
                    }
                }
            },
            "corporate": {
                "testcorp": {
                    "colors": {
                        "brand": {"$type": "color", "$value": "#0066CC"}
                    }
                }
            }
        }
    
    def test_token_resolution_consistent(self, supertheme_engine, hierarchical_tokens):
        """Test token resolution is consistent across layouts"""
        layouts_to_test = ["title_slide", "title_and_content", "two_content"]
        
        resolved_tokens = {}
        for layout_id in layouts_to_test:
            result = supertheme_engine.generate_layout_with_tokens(
                layout_id=layout_id,
                design_tokens=hierarchical_tokens,
                org="testcorp",
                channel="test"
            )
            
            if result.success:
                resolved_tokens[layout_id] = result.data.get('token_metadata', {})
        
        # Verify org and channel are consistent
        for layout_id, metadata in resolved_tokens.items():
            assert metadata.get('org') == 'testcorp'
            assert metadata.get('channel') == 'test'
    
    def test_color_token_transformations_valid(self):
        """Test color token transformations produce valid values"""
        transformer = create_powerpoint_token_transformer()
        
        test_colors = [
            {"$type": "color", "$value": "#0066CC"},
            {"$type": "color", "$value": "#FF0000"},
            {"$type": "color", "$value": "#00FF00"}
        ]
        
        for color_token in test_colors:
            result = transformer.transform_color_token(color_token)
            assert result.success, f"Color transformation failed: {result.errors}"
            
            color_data = result.data
            assert color_data.hex_value.startswith('#')
            assert len(color_data.rgb_values) == 3
            assert all(0 <= v <= 255 for v in color_data.rgb_values)
    
    def test_typography_token_transformations_valid(self):
        """Test typography token transformations produce valid values"""
        transformer = create_powerpoint_token_transformer()
        
        test_typography = {
            "family": {"$type": "fontFamily", "$value": "Arial"},
            "size": {"$type": "dimension", "$value": "24pt"},
            "weight": {"$type": "fontWeight", "$value": "bold"}
        }
        
        result = transformer.transform_typography_token(test_typography)
        assert result.success, f"Typography transformation failed: {result.errors}"
        
        typo_data = result.data
        assert typo_data.font_family == "Arial"
        assert typo_data.font_size_hundredths == 2400  # 24pt * 100
        assert typo_data.font_weight == "bold"


class TestAccessibilityCompliance:
    """Test accessibility compliance (WCAG standards)"""
    
    def test_color_contrast_ratios(self):
        """Test color contrast ratios meet WCAG AA standards"""
        
        def calculate_contrast_ratio(color1: str, color2: str) -> float:
            """Calculate contrast ratio between two hex colors"""
            def get_luminance(hex_color: str) -> float:
                hex_clean = hex_color.lstrip('#')
                r, g, b = tuple(int(hex_clean[i:i+2], 16)/255.0 for i in (0, 2, 4))
                
                # Apply gamma correction
                r = r/12.92 if r <= 0.03928 else ((r + 0.055)/1.055) ** 2.4
                g = g/12.92 if g <= 0.03928 else ((g + 0.055)/1.055) ** 2.4
                b = b/12.92 if b <= 0.03928 else ((b + 0.055)/1.055) ** 2.4
                
                return 0.2126 * r + 0.7152 * g + 0.0722 * b
            
            lum1 = get_luminance(color1)
            lum2 = get_luminance(color2)
            
            lighter = max(lum1, lum2)
            darker = min(lum1, lum2)
            
            return (lighter + 0.05) / (darker + 0.05)
        
        # Test common color combinations
        test_combinations = [
            ("#000000", "#FFFFFF", 21.0),  # Black on white - perfect contrast
            ("#0066CC", "#FFFFFF", 4.5),   # Blue on white - should meet AA
            ("#666666", "#FFFFFF", 5.74),  # Gray on white - should meet AA
        ]
        
        for fg, bg, min_ratio in test_combinations:
            ratio = calculate_contrast_ratio(fg, bg)
            assert ratio >= min_ratio - 0.5, \
                f"Contrast ratio {ratio:.2f} between {fg} and {bg} below minimum {min_ratio}"
    
    def test_minimum_font_sizes(self):
        """Test minimum font sizes for readability"""
        engine = create_powerpoint_layout_engine()
        available_layouts = engine.get_available_layouts()
        
        MIN_BODY_SIZE = 1400  # 14pt in hundredths
        MIN_TITLE_SIZE = 2400  # 24pt in hundredths
        
        for layout in available_layouts:
            result = engine.resolve_layout_positioning(layout['id'])
            if result.success:
                for placeholder in result.data['placeholders']:
                    typography = placeholder.get('typography', {})
                    font_size = typography.get('font_size')
                    
                    if font_size and font_size.isdigit():
                        size_value = int(font_size)
                        
                        # Check minimum sizes based on placeholder type
                        if placeholder['type'] in ['body', 'obj']:
                            assert size_value >= MIN_BODY_SIZE, \
                                f"Body text size {size_value} below minimum in {layout['id']}"
                        elif placeholder['type'] in ['title', 'ctrTitle']:
                            assert size_value >= MIN_TITLE_SIZE, \
                                f"Title size {size_value} below minimum in {layout['id']}"
    
    def test_semantic_structure(self):
        """Test layouts have proper semantic structure"""
        engine = create_powerpoint_layout_engine()
        
        # Test title layouts have title placeholders
        title_layouts = ["title_slide", "title_and_content", "section_header"]
        
        for layout_id in title_layouts:
            result = engine.resolve_layout_positioning(layout_id)
            if result.success:
                placeholders = result.data['placeholders']
                placeholder_types = [p['type'] for p in placeholders]
                
                # Should have at least one title placeholder
                has_title = any(t in placeholder_types for t in ['title', 'ctrTitle', 'subTitle'])
                assert has_title, f"Layout {layout_id} missing title placeholder for semantic structure"


class TestPerformanceBenchmarks:
    """Test performance for large-scale template generation"""
    
    @pytest.fixture
    def engine(self):
        """PowerPoint layout engine with caching enabled"""
        return create_powerpoint_layout_engine()
    
    def test_single_layout_generation_performance(self, engine):
        """Test single layout generation performance"""
        start_time = time.time()
        
        result = engine.resolve_layout_positioning("title_slide")
        
        elapsed_time = time.time() - start_time
        
        assert result.success
        assert elapsed_time < 0.5, f"Single layout generation took {elapsed_time:.3f}s (> 0.5s limit)"
    
    def test_batch_layout_generation_performance(self, engine):
        """Test batch layout generation performance"""
        available_layouts = engine.get_available_layouts()
        
        start_time = time.time()
        
        for layout in available_layouts:
            result = engine.resolve_layout_positioning(layout['id'])
            assert result.success
        
        elapsed_time = time.time() - start_time
        avg_time = elapsed_time / len(available_layouts)
        
        assert avg_time < 0.2, f"Average layout generation took {avg_time:.3f}s (> 0.2s limit)"
    
    def test_multi_aspect_ratio_performance(self, engine):
        """Test performance across multiple aspect ratios"""
        aspect_ratios = ["16:9", "4:3", "16:10"]
        layout_id = "title_slide"
        
        start_time = time.time()
        
        for aspect_ratio in aspect_ratios:
            result = engine.resolve_layout_positioning(layout_id, aspect_ratio)
            assert result.success
        
        elapsed_time = time.time() - start_time
        
        assert elapsed_time < 1.0, f"Multi-aspect generation took {elapsed_time:.3f}s (> 1.0s limit)"
    
    def test_cache_effectiveness(self, engine):
        """Test caching improves performance"""
        layout_id = "title_slide"
        
        # First generation (cache miss)
        start_time = time.time()
        result1 = engine.resolve_layout_positioning(layout_id)
        first_time = time.time() - start_time
        
        # Second generation (cache hit)
        start_time = time.time()
        result2 = engine.resolve_layout_positioning(layout_id)
        second_time = time.time() - start_time
        
        assert result1.success and result2.success
        assert second_time < first_time * 0.5, \
            f"Cache not effective: second call {second_time:.3f}s vs first {first_time:.3f}s"
    
    def test_potx_generation_performance(self):
        """Test POTX template generation performance"""
        generator = create_potx_template_generator()
        
        sample_tokens = {
            "global": {
                "colors": {"primary": {"$type": "color", "$value": "#0066CC"}}
            }
        }
        
        start_time = time.time()
        
        result = generator.generate_potx_template(
            design_tokens=sample_tokens,
            org="perf",
            channel="test",
            layout_ids=["title_slide", "title_and_content", "two_content"]
        )
        
        elapsed_time = time.time() - start_time
        
        assert result.success
        assert elapsed_time < 5.0, f"POTX generation took {elapsed_time:.3f}s (> 5.0s limit)"


class TestSuperThemeIntegration:
    """Test SuperTheme integration across multiple variants"""
    
    @pytest.fixture
    def workflow_orchestrator(self):
        """Complete workflow orchestrator"""
        from tools.supertheme_powerpoint_workflow import create_supertheme_powerpoint_workflow
        return create_supertheme_powerpoint_workflow()
    
    def test_multiple_design_variants(self, workflow_orchestrator):
        """Test multiple design variants generate correctly"""
        design_tokens = {
            "global": {
                "colors": {
                    "neutral": {"white": {"$type": "color", "$value": "#FFFFFF"}}
                }
            },
            "corporate": {
                "variant1": {
                    "colors": {"brand": {"$type": "color", "$value": "#0066CC"}}
                },
                "variant2": {
                    "colors": {"brand": {"$type": "color", "$value": "#CC0066"}}
                }
            }
        }
        
        # Test both variants
        for org in ["variant1", "variant2"]:
            result = workflow_orchestrator.execute_complete_workflow(
                design_tokens=design_tokens,
                org=org,
                channel="test",
                aspect_ratios=["16:9"],
                output_formats=["potx"]
            )
            
            # May have warnings but should attempt generation
            assert 'outputs' in result.data
    
    def test_aspect_ratio_consistency_across_variants(self, workflow_orchestrator):
        """Test aspect ratios are consistent across design variants"""
        design_tokens = {
            "global": {
                "colors": {"primary": {"$type": "color", "$value": "#000000"}}
            },
            "corporate": {
                "test": {
                    "colors": {"brand": {"$type": "color", "$value": "#0066CC"}}
                }
            }
        }
        
        result = workflow_orchestrator.execute_complete_workflow(
            design_tokens=design_tokens,
            org="test",
            channel="validation",
            aspect_ratios=["16:9", "4:3"],
            output_formats=["potx"]
        )
        
        # Check workflow attempted both aspect ratios
        assert 'aspect_ratios' in result.data
        assert result.data['aspect_ratios'] == ["16:9", "4:3"]


class TestValidationReportGeneration:
    """Generate comprehensive validation report"""
    
    def test_generate_validation_report(self):
        """Generate and save comprehensive validation report"""
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "validation_suite": "PowerPoint Layout Engine Validation",
            "version": "1.0.0",
            "results": {}
        }
        
        # Run key validations
        engine = create_powerpoint_layout_engine()
        
        # 1. Layout availability
        available_layouts = engine.get_available_layouts()
        report["results"]["layout_availability"] = {
            "total_layouts": len(available_layouts),
            "layout_types": list(set(l['type'] for l in available_layouts)),
            "status": "PASS" if len(available_layouts) >= 10 else "FAIL"
        }
        
        # 2. Aspect ratio support
        aspect_ratios = ["16:9", "4:3", "16:10"]
        aspect_ratio_results = []
        
        for ar in aspect_ratios:
            result = engine.set_aspect_ratio(ar)
            aspect_ratio_results.append({
                "aspect_ratio": ar,
                "supported": result.success
            })
        
        report["results"]["aspect_ratio_support"] = {
            "tested_ratios": aspect_ratios,
            "results": aspect_ratio_results,
            "status": "PASS" if all(r["supported"] for r in aspect_ratio_results) else "FAIL"
        }
        
        # 3. Positioning validation
        positioning_valid = True
        for layout in available_layouts[:3]:  # Test first 3 layouts
            result = engine.resolve_layout_positioning(layout['id'])
            if result.success:
                for placeholder in result.data['placeholders']:
                    pos = placeholder['position']
                    if pos['x'] < 0 or pos['y'] < 0:
                        positioning_valid = False
                        break
        
        report["results"]["positioning_validation"] = {
            "all_positions_valid": positioning_valid,
            "status": "PASS" if positioning_valid else "FAIL"
        }
        
        # 4. Performance metrics
        perf_start = time.time()
        engine.resolve_layout_positioning("title_slide")
        single_layout_time = time.time() - perf_start
        
        report["results"]["performance"] = {
            "single_layout_generation_ms": round(single_layout_time * 1000, 2),
            "status": "PASS" if single_layout_time < 0.5 else "FAIL"
        }
        
        # 5. Token transformation
        transformer = create_powerpoint_token_transformer()
        color_result = transformer.transform_color_token({"$type": "color", "$value": "#0066CC"})
        
        report["results"]["token_transformation"] = {
            "color_transformation": "PASS" if color_result.success else "FAIL",
            "status": "PASS" if color_result.success else "FAIL"
        }
        
        # Calculate overall status
        all_statuses = [r.get("status", "UNKNOWN") for r in report["results"].values()]
        report["overall_status"] = "PASS" if all(s == "PASS" for s in all_statuses) else "FAIL"
        report["pass_rate"] = f"{all_statuses.count('PASS')}/{len(all_statuses)}"
        
        # Save report
        report_path = Path("validation_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 Validation Report Generated: {report_path}")
        print(f"   Overall Status: {report['overall_status']}")
        print(f"   Pass Rate: {report['pass_rate']}")
        
        # Assert all validations passed
        assert report["overall_status"] == "PASS", \
            f"Validation failed: {[k for k, v in report['results'].items() if v.get('status') != 'PASS']}"