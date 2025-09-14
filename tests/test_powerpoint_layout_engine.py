"""
Tests for PowerPointLayoutEngine Core System

This module tests the main PowerPoint layout engine that provides the unified
interface for generating professional PowerPoint-compatible slide layouts.
"""

import pytest
import json
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from tools.powerpoint_layout_engine import PowerPointLayoutEngine, create_powerpoint_layout_engine
from tools.powerpoint_layout_schema import PowerPointLayoutSchema, ValidationResult
from tools.powerpoint_positioning_calculator import PositioningCalculator
from tools.powerpoint_placeholder_types import PlaceholderType, PlaceholderSize
from tools.core.types import ProcessingResult


class TestPowerPointLayoutEngineInitialization:
    """Test PowerPointLayoutEngine initialization and basic properties"""
    
    def test_engine_initialization_with_defaults(self):
        """Test engine initializes with default parameters"""
        engine = PowerPointLayoutEngine()
        
        assert engine is not None
        assert engine.default_aspect_ratio == '16:9'
        assert isinstance(engine.schema, PowerPointLayoutSchema)
        assert isinstance(engine.positioning_calculator, PositioningCalculator)
        assert engine.supported_aspect_ratios == ['16:9', '4:3', '16:10']
        assert len(engine.layout_templates) > 0
    
    def test_engine_initialization_with_custom_aspect_ratio(self):
        """Test engine initializes with custom aspect ratio"""
        engine = PowerPointLayoutEngine(default_aspect_ratio='4:3')
        
        assert engine.default_aspect_ratio == '4:3'
        assert engine.positioning_calculator.aspect_ratio == '4:3'
        assert engine.token_resolver.aspect_ratio == '4:3'
    
    def test_engine_initialization_with_custom_files(self):
        """Test engine handles custom schema and data files (non-existent files should raise error)"""
        with pytest.raises(Exception):  # Should raise LayoutValidationError for missing files
            PowerPointLayoutEngine(
                schema_file='/custom/schema.json',
                layout_data_file='/custom/layouts.json',
                default_aspect_ratio='16:10'
            )
    
    def test_factory_function_creates_engine(self):
        """Test factory function creates engine correctly"""
        engine = create_powerpoint_layout_engine('4:3')
        
        assert isinstance(engine, PowerPointLayoutEngine)
        assert engine.default_aspect_ratio == '4:3'
    
    def test_layout_templates_initialized(self):
        """Test that layout templates are properly initialized"""
        engine = PowerPointLayoutEngine()
        
        expected_templates = [
            'title_slide', 'title_and_content', 'section_header',
            'two_content', 'comparison', 'title_only', 'blank',
            'content_with_caption', 'picture_with_caption', 'full_page_photo'
        ]
        
        for template_id in expected_templates:
            assert template_id in engine.layout_templates
            assert callable(engine.layout_templates[template_id])
    
    def test_cache_initialized_empty(self):
        """Test that layout cache is initialized empty"""
        engine = PowerPointLayoutEngine()
        
        assert hasattr(engine, '_layout_cache')
        assert len(engine._layout_cache) == 0


class TestPowerPointLayoutEngineAspectRatio:
    """Test aspect ratio management functionality"""
    
    def test_set_aspect_ratio_success(self):
        """Test successfully setting a supported aspect ratio"""
        engine = PowerPointLayoutEngine()
        
        result = engine.set_aspect_ratio('4:3')
        
        assert result.success is True
        assert engine.default_aspect_ratio == '4:3'
        assert engine.positioning_calculator.aspect_ratio == '4:3'
        assert engine.token_resolver.aspect_ratio == '4:3'
        assert result.data == {'aspect_ratio': '4:3'}
    
    def test_set_aspect_ratio_unsupported(self):
        """Test setting unsupported aspect ratio fails"""
        engine = PowerPointLayoutEngine()
        
        result = engine.set_aspect_ratio('21:9')
        
        assert result.success is False
        assert len(result.errors) == 1
        assert 'Unsupported aspect ratio: 21:9' in result.errors[0]
        assert engine.default_aspect_ratio == '16:9'  # Should remain unchanged
    
    def test_set_aspect_ratio_clears_cache(self):
        """Test that setting aspect ratio clears the layout cache"""
        engine = PowerPointLayoutEngine()
        
        # Populate cache
        engine._layout_cache['test_key'] = {'test': 'data'}
        assert len(engine._layout_cache) == 1
        
        # Change aspect ratio
        result = engine.set_aspect_ratio('4:3')
        
        assert result.success is True
        assert len(engine._layout_cache) == 0  # Cache should be cleared
    
    def test_supported_aspect_ratios_constant(self):
        """Test that supported aspect ratios are correct"""
        engine = PowerPointLayoutEngine()
        
        expected_ratios = ['16:9', '4:3', '16:10']
        assert engine.supported_aspect_ratios == expected_ratios


class TestPowerPointLayoutEngineLayoutManagement:
    """Test layout discovery and management functionality"""
    
    def test_get_available_layouts(self):
        """Test getting list of available layouts"""
        engine = PowerPointLayoutEngine()
        
        layouts = engine.get_available_layouts()
        
        assert isinstance(layouts, list)
        assert len(layouts) > 0
        
        # Check structure of layout info
        for layout in layouts:
            assert 'id' in layout
            assert 'name' in layout
            assert 'type' in layout
            assert 'description' in layout
            assert 'placeholder_count' in layout
            assert isinstance(layout['placeholder_count'], int)
    
    def test_get_available_layouts_contains_expected_layouts(self):
        """Test that available layouts contain expected PowerPoint layouts"""
        engine = PowerPointLayoutEngine()
        
        layouts = engine.get_available_layouts()
        layout_ids = [layout['id'] for layout in layouts]
        
        expected_layouts = ['title_slide', 'title_and_content', 'two_content', 'comparison']
        for expected_layout in expected_layouts:
            assert expected_layout in layout_ids
    
    def test_validate_layout_definition_success(self):
        """Test validating existing layout definition"""
        engine = PowerPointLayoutEngine()
        
        result = engine.validate_layout_definition('title_slide')
        
        assert isinstance(result, ValidationResult)
        # We expect this to be valid based on our schema
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_layout_definition_not_found(self):
        """Test validating non-existent layout"""
        engine = PowerPointLayoutEngine()
        
        result = engine.validate_layout_definition('nonexistent_layout')
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert 'Layout not found: nonexistent_layout' in result.errors[0]


class TestPowerPointLayoutEnginePositioning:
    """Test layout positioning resolution functionality"""
    
    def test_resolve_layout_positioning_success(self):
        """Test successfully resolving layout positioning"""
        engine = PowerPointLayoutEngine()
        
        result = engine.resolve_layout_positioning('title_slide', '16:9')
        
        assert result.success is True
        assert result.data is not None
        assert 'placeholders' in result.data
        assert len(result.data['placeholders']) > 0
        
        # Check metadata
        assert 'aspect_ratio' in result.metadata
        assert 'slide_dimensions' in result.metadata
        assert 'placeholder_count' in result.metadata
        assert result.metadata['aspect_ratio'] == '16:9'
    
    def test_resolve_layout_positioning_uses_default_aspect_ratio(self):
        """Test resolving positioning uses default aspect ratio when none specified"""
        engine = PowerPointLayoutEngine()
        engine.set_aspect_ratio('4:3')
        
        result = engine.resolve_layout_positioning('title_slide')
        
        assert result.success is True
        assert result.metadata['aspect_ratio'] == '4:3'
    
    def test_resolve_layout_positioning_not_found(self):
        """Test resolving positioning for non-existent layout"""
        engine = PowerPointLayoutEngine()
        
        result = engine.resolve_layout_positioning('nonexistent_layout', '16:9')
        
        assert result.success is False
        assert len(result.errors) == 1
        assert 'Layout not found: nonexistent_layout' in result.errors[0]
    
    def test_resolve_layout_positioning_caching(self):
        """Test that resolved layouts are cached for performance"""
        engine = PowerPointLayoutEngine()
        
        # First call should resolve and cache
        result1 = engine.resolve_layout_positioning('title_slide', '16:9')
        assert result1.success is True
        assert 'cached' not in result1.metadata  # First call not cached
        
        # Second call should use cache
        result2 = engine.resolve_layout_positioning('title_slide', '16:9')
        assert result2.success is True
        assert result2.metadata.get('cached') is True
        
        # Results should be identical
        assert result1.data == result2.data
    
    def test_resolve_layout_positioning_validates_bounds(self):
        """Test that positioning resolution validates placeholder bounds"""
        engine = PowerPointLayoutEngine()
        
        result = engine.resolve_layout_positioning('title_slide', '16:9')
        
        assert result.success is True
        
        # Check that all placeholders have valid positions
        for placeholder in result.data['placeholders']:
            position = placeholder['position']
            assert position['x'] >= 0
            assert position['y'] >= 0
            assert position['width'] > 0
            assert position['height'] > 0
    
    def test_resolve_layout_positioning_different_aspect_ratios(self):
        """Test resolving same layout for different aspect ratios"""
        engine = PowerPointLayoutEngine()
        
        result_16_9 = engine.resolve_layout_positioning('title_slide', '16:9')
        result_4_3 = engine.resolve_layout_positioning('title_slide', '4:3')
        
        assert result_16_9.success is True
        assert result_4_3.success is True
        
        # Slide dimensions should be different
        dims_16_9 = result_16_9.metadata['slide_dimensions']
        dims_4_3 = result_4_3.metadata['slide_dimensions']
        assert dims_16_9 != dims_4_3
        assert dims_4_3[1] > dims_16_9[1]  # 4:3 should be taller


class TestPowerPointLayoutEngineOOXMLGeneration:
    """Test OOXML generation functionality"""
    
    def test_generate_layout_for_ooxml_success(self):
        """Test successfully generating layout for OOXML"""
        engine = PowerPointLayoutEngine()
        
        result = engine.generate_layout_for_ooxml('title_slide', '16:9', 1)
        
        assert result.success is True
        assert result.data is not None
        
        ooxml_layout = result.data
        assert ooxml_layout['layout_number'] == 1
        assert ooxml_layout['file_name'] == 'slideLayout1.xml'
        assert ooxml_layout['id'] == 'title_slide'
        assert 'placeholders' in ooxml_layout
        assert len(ooxml_layout['placeholders']) > 0
        assert 'relationships' in ooxml_layout
    
    def test_generate_layout_for_ooxml_placeholder_structure(self):
        """Test OOXML placeholder structure is correct"""
        engine = PowerPointLayoutEngine()
        
        result = engine.generate_layout_for_ooxml('title_slide', '16:9', 1)
        
        assert result.success is True
        placeholders = result.data['placeholders']
        
        # Check placeholder structure
        for placeholder in placeholders:
            assert 'shape_id' in placeholder
            assert 'name' in placeholder
            assert 'creation_id' in placeholder
            assert 'ph_type' in placeholder
            assert 'index' in placeholder
            assert 'position' in placeholder
            assert 'typography' in placeholder
            assert 'shape_locks' in placeholder
    
    def test_generate_layout_for_ooxml_shape_ids_sequential(self):
        """Test that OOXML generation assigns sequential shape IDs"""
        engine = PowerPointLayoutEngine()
        
        result = engine.generate_layout_for_ooxml('title_slide', '16:9', 1)
        
        assert result.success is True
        placeholders = result.data['placeholders']
        
        # Shape IDs should start at 2 and increment
        shape_ids = [p['shape_id'] for p in placeholders]
        expected_ids = list(range(2, 2 + len(placeholders)))
        assert shape_ids == expected_ids
    
    def test_generate_layout_for_ooxml_not_found(self):
        """Test generating OOXML for non-existent layout"""
        engine = PowerPointLayoutEngine()
        
        result = engine.generate_layout_for_ooxml('nonexistent_layout', '16:9', 1)
        
        assert result.success is False
        assert len(result.errors) > 0
    
    def test_generate_all_layouts_for_ooxml_success(self):
        """Test generating all layouts for OOXML"""
        engine = PowerPointLayoutEngine()
        
        result = engine.generate_all_layouts_for_ooxml('16:9')
        
        assert result.success is True
        assert result.data is not None
        
        data = result.data
        assert 'layouts' in data
        assert 'count' in data
        assert 'aspect_ratio' in data
        assert data['aspect_ratio'] == '16:9'
        assert data['count'] > 0
        assert len(data['layouts']) == data['count']
    
    def test_generate_all_layouts_for_ooxml_layout_numbers(self):
        """Test that all layouts get sequential layout numbers"""
        engine = PowerPointLayoutEngine()
        
        result = engine.generate_all_layouts_for_ooxml('16:9')
        
        assert result.success is True
        layouts = result.data['layouts']
        
        # Layout numbers should be sequential starting from 1
        layout_numbers = [layout['layout_number'] for layout in layouts]
        expected_numbers = list(range(1, len(layouts) + 1))
        assert layout_numbers == expected_numbers
    
    def test_generate_all_layouts_for_ooxml_uses_default_aspect_ratio(self):
        """Test generating all layouts uses default aspect ratio"""
        engine = PowerPointLayoutEngine()
        engine.set_aspect_ratio('4:3')
        
        result = engine.generate_all_layouts_for_ooxml()
        
        assert result.success is True
        assert result.data['aspect_ratio'] == '4:3'


class TestPowerPointLayoutEngineStatistics:
    """Test engine statistics and information functionality"""
    
    def test_get_layout_statistics(self):
        """Test getting layout engine statistics"""
        engine = PowerPointLayoutEngine()
        
        stats = engine.get_layout_statistics()
        
        assert isinstance(stats, dict)
        expected_keys = [
            'supported_aspect_ratios', 'default_aspect_ratio', 'available_layouts',
            'cached_layouts', 'supported_placeholder_types', 'layout_templates', 'schema_version'
        ]
        
        for key in expected_keys:
            assert key in stats
    
    def test_get_layout_statistics_values(self):
        """Test layout statistics contain correct values"""
        engine = PowerPointLayoutEngine()
        
        stats = engine.get_layout_statistics()
        
        assert stats['supported_aspect_ratios'] == ['16:9', '4:3', '16:10']
        assert stats['default_aspect_ratio'] == '16:9'
        assert stats['available_layouts'] > 0
        assert stats['cached_layouts'] == 0  # Initially empty
        assert stats['supported_placeholder_types'] > 0
        assert stats['layout_templates'] > 0
    
    def test_get_layout_statistics_after_caching(self):
        """Test statistics reflect cached layouts"""
        engine = PowerPointLayoutEngine()
        
        # Generate some layouts to populate cache
        engine.resolve_layout_positioning('title_slide', '16:9')
        engine.resolve_layout_positioning('title_slide', '4:3')
        
        stats = engine.get_layout_statistics()
        assert stats['cached_layouts'] == 2


class TestPowerPointLayoutEngineErrorHandling:
    """Test error handling and edge cases"""
    
    def test_engine_handles_missing_schema_gracefully(self):
        """Test engine handles missing schema files gracefully"""
        with pytest.raises((FileNotFoundError, Exception)):
            PowerPointLayoutEngine(schema_file='/nonexistent/schema.json')
    
    def test_resolve_positioning_handles_invalid_calculator(self):
        """Test positioning resolution handles calculator errors"""
        engine = PowerPointLayoutEngine()
        
        # Mock the PositioningCalculator class to raise exception during resolution
        with patch('tools.powerpoint_layout_engine.PositioningCalculator') as mock_calc_class:
            mock_calc_instance = Mock()
            mock_calc_instance.resolve_parameterized_layout.side_effect = Exception("Calculator error")
            mock_calc_class.return_value = mock_calc_instance
            
            result = engine.resolve_layout_positioning('title_slide', '16:9')
            
            assert result.success is False
            assert len(result.errors) > 0
            assert "Error resolving layout positioning" in result.errors[0]
    
    def test_generate_ooxml_handles_conversion_errors(self):
        """Test OOXML generation handles conversion errors"""
        engine = PowerPointLayoutEngine()
        
        # Mock placeholder template creation to fail
        with patch('tools.powerpoint_layout_engine.PlaceholderTemplate', 
                  side_effect=Exception("Template error")):
            result = engine.generate_layout_for_ooxml('title_slide', '16:9', 1)
            
            assert result.success is False
            assert len(result.errors) > 0
            assert "Error generating OOXML layout" in result.errors[0]


class TestPowerPointLayoutEngineIntegration:
    """Test integration with other components"""
    
    def test_engine_integrates_with_schema_validator(self):
        """Test engine properly integrates with schema validator"""
        engine = PowerPointLayoutEngine()
        
        # Test that validation works through engine
        result = engine.validate_layout_definition('title_slide')
        assert isinstance(result, ValidationResult)
    
    def test_engine_integrates_with_positioning_calculator(self):
        """Test engine properly integrates with positioning calculator"""
        engine = PowerPointLayoutEngine()
        
        # Test that positioning calculation works through engine
        result = engine.resolve_layout_positioning('title_slide', '16:9')
        assert result.success is True
        assert 'slide_dimensions' in result.metadata
    
    def test_engine_integrates_with_placeholder_system(self):
        """Test engine properly integrates with placeholder system"""
        engine = PowerPointLayoutEngine()
        
        # Test that OOXML generation includes proper placeholder metadata
        result = engine.generate_layout_for_ooxml('title_slide', '16:9', 1)
        assert result.success is True
        
        placeholders = result.data['placeholders']
        for placeholder in placeholders:
            assert 'shape_locks' in placeholder
            assert 'creation_id' in placeholder
            assert len(placeholder['creation_id']) > 0


if __name__ == '__main__':
    pytest.main([__file__])