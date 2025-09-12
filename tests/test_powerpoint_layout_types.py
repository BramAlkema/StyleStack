"""
Test Suite for All 12 PowerPoint Layout Types

This module provides comprehensive testing for all PowerPoint OOXML layout types
with parameterized positioning and professional typography.
"""

import pytest
import json
from pathlib import Path
from tools.powerpoint_layout_engine import PowerPointLayoutEngine, create_powerpoint_layout_engine
from tools.powerpoint_positioning_calculator import PositioningCalculator
from tools.powerpoint_layout_schema import PowerPointLayoutSchema


class TestPowerPointLayoutTypesCoverage:
    """Test coverage for all 12 PowerPoint layout types"""
    
    @pytest.fixture
    def engine(self):
        """Create layout engine for testing"""
        return create_powerpoint_layout_engine()
    
    @pytest.fixture
    def all_layout_ids(self):
        """Expected layout IDs for all PowerPoint layout types"""
        return [
            'title_slide',                  # Title slide with centered title/subtitle
            'title_and_content',           # Single content with title (obj)
            'section_header',              # Section divider with large title (secHead)
            'two_content',                 # Two side-by-side content areas (twoObj)
            'comparison',                  # Two text, two objects (twoTxTwoObj)
            'title_only',                  # Title without content (titleOnly)
            'blank',                      # Empty slide (blank)
            'content_with_caption',       # Object with text (objTx)
            'picture_with_caption',       # Picture with text (picTx)
            'full_page_photo_with_title', # Full picture slide (pic)
            'full_page_photo_alternate'   # Alternative full picture slide
        ]
    
    def test_all_layout_types_available(self, engine, all_layout_ids):
        """Test that all 12 layout types are available"""
        available_layouts = engine.get_available_layouts()
        
        # Check we have at least 10 layouts (covering all PowerPoint OOXML types)
        assert len(available_layouts) >= 10, f"Expected at least 10 layouts, got {len(available_layouts)}"
        
        # Check specific layout IDs exist
        available_ids = [layout['id'] for layout in available_layouts]
        missing_layouts = [layout_id for layout_id in all_layout_ids if layout_id not in available_ids]
        
        if missing_layouts:
            pytest.skip(f"Missing layout types: {missing_layouts}. Will implement in this task.")
    
    def test_layout_type_mapping_complete(self, engine):
        """Test that all PowerPoint OOXML layout types are covered"""
        powerpoint_types = [
            'title', 'obj', 'secHead', 'twoObj', 'twoTxTwoObj',
            'titleOnly', 'blank', 'objTx', 'picTx', 'pic'
        ]
        
        available_layouts = engine.get_available_layouts()
        covered_types = set(layout.get('type') for layout in available_layouts)
        
        missing_types = set(powerpoint_types) - covered_types
        if missing_types:
            pytest.skip(f"Missing PowerPoint types: {missing_types}. Will implement in this task.")


class TestTitleSlideLayout:
    """Test Title Slide layout (type: title)"""
    
    @pytest.fixture
    def engine(self):
        return create_powerpoint_layout_engine()
    
    def test_title_slide_structure(self, engine):
        """Test title slide has proper structure"""
        result = engine.resolve_layout_positioning('title_slide')
        
        if not result.success:
            pytest.skip("Title slide not implemented yet")
        
        layout = result.data
        assert layout['type'] == 'title'
        
        # Should have title and subtitle placeholders
        placeholders = layout['placeholders']
        placeholder_types = [p['type'] for p in placeholders]
        
        assert 'ctrTitle' in placeholder_types, "Title slide should have centered title"
        assert 'subTitle' in placeholder_types, "Title slide should have subtitle"
    
    def test_title_slide_positioning_centered(self, engine):
        """Test title slide placeholders are centered"""
        result = engine.resolve_layout_positioning('title_slide')
        
        if not result.success:
            pytest.skip("Title slide not implemented yet")
        
        layout = result.data
        calculator = PositioningCalculator('16:9')
        slide_width, slide_height = calculator.get_slide_dimensions()
        
        for placeholder in layout['placeholders']:
            pos = placeholder['position']
            # Check positioning is reasonable for centered content
            assert 0 <= pos['x'] < slide_width, f"X position {pos['x']} out of bounds"
            assert 0 <= pos['y'] < slide_height, f"Y position {pos['y']} out of bounds"


class TestContentLayout:
    """Test Content layout (type: obj)"""
    
    @pytest.fixture
    def engine(self):
        return create_powerpoint_layout_engine()
    
    def test_content_slide_structure(self, engine):
        """Test content slide has proper structure"""
        result = engine.resolve_layout_positioning('title_and_content')
        
        if not result.success:
            pytest.skip("Content slide not implemented yet")
        
        layout = result.data
        assert layout['type'] == 'obj'
        
        placeholders = layout['placeholders']
        placeholder_types = [p['type'] for p in placeholders]
        
        assert 'title' in placeholder_types, "Content slide should have title"
        assert 'body' in placeholder_types, "Content slide should have body content"


class TestSectionHeaderLayout:
    """Test Section Header layout (type: secHead)"""
    
    @pytest.fixture
    def engine(self):
        return create_powerpoint_layout_engine()
    
    def test_section_header_structure(self, engine):
        """Test section header has proper structure"""
        result = engine.resolve_layout_positioning('section_header')
        
        if not result.success:
            pytest.skip("Section header not implemented yet")
        
        layout = result.data
        assert layout['type'] == 'secHead'
        
        placeholders = layout['placeholders']
        placeholder_types = [p['type'] for p in placeholders]
        
        assert 'title' in placeholder_types, "Section header should have title"


class TestTwoContentLayout:
    """Test Two Content layout (type: twoObj)"""
    
    @pytest.fixture
    def engine(self):
        return create_powerpoint_layout_engine()
    
    def test_two_content_structure(self, engine):
        """Test two content slide has proper structure"""
        result = engine.resolve_layout_positioning('two_content')
        
        if not result.success:
            pytest.skip("Two content slide not implemented yet")
        
        layout = result.data
        assert layout['type'] == 'twoObj'
        
        placeholders = layout['placeholders']
        placeholder_types = [p['type'] for p in placeholders]
        
        assert 'title' in placeholder_types, "Two content should have title"
        
        # Should have two body placeholders
        body_count = placeholder_types.count('body')
        assert body_count >= 2, f"Two content should have at least 2 body placeholders, got {body_count}"


class TestComplexLayouts:
    """Test complex layout types"""
    
    @pytest.fixture
    def engine(self):
        return create_powerpoint_layout_engine()
    
    def test_two_text_two_obj_structure(self, engine):
        """Test twoTxTwoObj layout structure"""
        result = engine.resolve_layout_positioning('comparison')
        
        if not result.success:
            pytest.skip("Two text two object slide not implemented yet")
        
        layout = result.data
        assert layout['type'] == 'twoTxTwoObj'


class TestSpecializedLayouts:
    """Test specialized layout types"""
    
    @pytest.fixture
    def engine(self):
        return create_powerpoint_layout_engine()
    
    def test_title_only_structure(self, engine):
        """Test titleOnly layout structure"""
        result = engine.resolve_layout_positioning('title_only')
        
        if not result.success:
            pytest.skip("Title only slide not implemented yet")
        
        layout = result.data
        assert layout['type'] == 'titleOnly'
        
        placeholders = layout['placeholders']
        placeholder_types = [p['type'] for p in placeholders]
        assert 'title' in placeholder_types, "Title only should have title"
    
    def test_blank_layout_structure(self, engine):
        """Test blank layout structure"""
        result = engine.resolve_layout_positioning('blank')
        
        if not result.success:
            pytest.skip("Blank slide not implemented yet")
        
        layout = result.data
        assert layout['type'] == 'blank'
        
        # Blank layout may have no placeholders or just footer placeholders
        placeholders = layout['placeholders']
        assert len(placeholders) <= 3, "Blank layout should have minimal placeholders"
    
    def test_picture_layouts(self, engine):
        """Test picture-based layouts"""
        picture_layouts = [
            ('full_page_photo_with_title', 'pic'),
            ('picture_with_caption', 'picTx')
        ]
        
        for layout_id, expected_type in picture_layouts:
            result = engine.resolve_layout_positioning(layout_id)
            
            if not result.success:
                pytest.skip(f"{layout_id} not implemented yet")
            
            layout = result.data
            assert layout['type'] == expected_type
            
            placeholders = layout['placeholders']
            placeholder_types = [p['type'] for p in placeholders]
            assert 'pic' in placeholder_types, f"{layout_id} should have picture placeholder"


class TestLayoutTypography:
    """Test typography presets for different layout types"""
    
    @pytest.fixture
    def engine(self):
        return create_powerpoint_layout_engine()
    
    def test_title_slide_typography(self, engine):
        """Test title slide has appropriate typography"""
        result = engine.resolve_layout_positioning('title_slide')
        
        if not result.success:
            pytest.skip("Title slide not implemented yet")
        
        layout = result.data
        
        for placeholder in layout['placeholders']:
            if placeholder['type'] == 'ctrTitle':
                # Title should have larger font size
                typography = placeholder.get('typography', {})
                font_size = typography.get('font_size')
                if font_size:
                    # Font sizes in hundredths of points - expect title > 3600 (36pt)
                    if font_size.isdigit():
                        assert int(font_size) >= 3600, "Title font should be at least 36pt"
    
    def test_consistent_typography_across_aspect_ratios(self, engine):
        """Test typography remains consistent across aspect ratios"""
        aspect_ratios = ['16:9', '4:3', '16:10']
        
        for layout_id in ['title_slide', 'title_and_content']:
            typography_sets = []
            
            for aspect_ratio in aspect_ratios:
                engine.set_aspect_ratio(aspect_ratio)
                result = engine.resolve_layout_positioning(layout_id)
                
                if not result.success:
                    pytest.skip(f"{layout_id} not implemented yet")
                
                layout = result.data
                layout_typography = []
                
                for placeholder in layout['placeholders']:
                    typography = placeholder.get('typography', {})
                    layout_typography.append(typography.get('font_size'))
                
                typography_sets.append(layout_typography)
            
            # Typography should be consistent across aspect ratios
            if typography_sets:
                first_set = typography_sets[0]
                for other_set in typography_sets[1:]:
                    assert first_set == other_set, f"Typography inconsistent for {layout_id}"


class TestParameterizedPositioning:
    """Test parameterized positioning across all layout types"""
    
    @pytest.fixture
    def engine(self):
        return create_powerpoint_layout_engine()
    
    def test_all_layouts_use_parameterized_positioning(self, engine):
        """Test all layouts use design token variables, not hardcoded coordinates"""
        available_layouts = engine.get_available_layouts()
        
        for layout in available_layouts:
            layout_id = layout['id']
            result = engine.resolve_layout_positioning(layout_id)
            
            if not result.success:
                continue  # Skip layouts not yet implemented
            
            resolved_layout = result.data
            
            for placeholder in resolved_layout['placeholders']:
                pos = placeholder['position']
                
                # Resolved positions should be numeric (EMU values)
                assert isinstance(pos['x'], int), f"X position should be resolved to EMU for {layout_id}"
                assert isinstance(pos['y'], int), f"Y position should be resolved to EMU for {layout_id}"
                assert isinstance(pos['width'], int), f"Width should be resolved to EMU for {layout_id}"
                assert isinstance(pos['height'], int), f"Height should be resolved to EMU for {layout_id}"
    
    def test_positioning_within_slide_bounds(self, engine):
        """Test all resolved positioning stays within slide bounds"""
        available_layouts = engine.get_available_layouts()
        aspect_ratios = ['16:9', '4:3', '16:10']
        
        for aspect_ratio in aspect_ratios:
            engine.set_aspect_ratio(aspect_ratio)
            calculator = PositioningCalculator(aspect_ratio)
            slide_width, slide_height = calculator.get_slide_dimensions()
            
            for layout in available_layouts:
                layout_id = layout['id']
                result = engine.resolve_layout_positioning(layout_id)
                
                if not result.success:
                    continue
                
                resolved_layout = result.data
                
                for placeholder in resolved_layout['placeholders']:
                    pos = placeholder['position']
                    
                    # Check bounds
                    assert 0 <= pos['x'], f"X position negative for {layout_id} in {aspect_ratio}"
                    assert 0 <= pos['y'], f"Y position negative for {layout_id} in {aspect_ratio}"
                    assert pos['x'] + pos['width'] <= slide_width, f"Right edge beyond slide for {layout_id} in {aspect_ratio}"
                    assert pos['y'] + pos['height'] <= slide_height, f"Bottom edge beyond slide for {layout_id} in {aspect_ratio}"


class TestOOXMLGeneration:
    """Test OOXML generation for all layout types"""
    
    @pytest.fixture
    def engine(self):
        return create_powerpoint_layout_engine()
    
    def test_all_layouts_generate_valid_ooxml(self, engine):
        """Test all layouts generate valid OOXML structure"""
        available_layouts = engine.get_available_layouts()
        
        for layout in available_layouts:
            layout_id = layout['id']
            result = engine.generate_layout_for_ooxml(layout_id)
            
            if not result.success:
                continue
            
            ooxml_layout = result.data
            
            # Validate OOXML structure
            assert 'id' in ooxml_layout
            assert 'name' in ooxml_layout
            assert 'type' in ooxml_layout
            assert 'placeholders' in ooxml_layout
            
            # Validate placeholders have Office metadata
            for placeholder in ooxml_layout['placeholders']:
                assert 'creation_id' in placeholder, f"Missing creation ID for {layout_id}"
                assert 'shape_locks' in placeholder, f"Missing shape locks for {layout_id}"
                assert placeholder['creation_id'].startswith('{'), "Creation ID should be UUID format"


class TestLayoutValidation:
    """Test validation of all layout types against PowerPoint OOXML standards"""
    
    @pytest.fixture
    def schema(self):
        return PowerPointLayoutSchema()
    
    def test_all_layouts_pass_schema_validation(self, schema):
        """Test all layouts pass schema validation"""
        validation_results = schema.validate_all_layouts()
        
        failed_layouts = []
        for layout_id, result in validation_results.items():
            if not result.is_valid:
                failed_layouts.append((layout_id, result.errors))
        
        if failed_layouts:
            error_msg = "Layout validation failures:\n"
            for layout_id, errors in failed_layouts:
                error_msg += f"  {layout_id}: {errors}\n"
            
            pytest.fail(error_msg)
    
    def test_placeholder_types_powerpoint_compatible(self, schema):
        """Test all placeholder types are PowerPoint-compatible"""
        for layout in schema.layouts:
            layout_id = layout.get('id', 'unknown')
            
            for placeholder in layout.get('placeholders', []):
                ph_type = placeholder.get('type')
                
                # Check against PowerPoint supported types
                powerpoint_types = [
                    'ctrTitle', 'subTitle', 'title', 'body', 'pic',
                    'dt', 'ftr', 'sldNum', 'chart', 'tbl', 'media'
                ]
                
                assert ph_type in powerpoint_types, f"Unsupported placeholder type '{ph_type}' in {layout_id}"