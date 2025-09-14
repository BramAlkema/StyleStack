"""
Tests for PowerPoint Layout Schema and Parameterized Positioning System

This module tests the layout schema validation and parameterized positioning
calculations that form the foundation of the PowerPoint-compatible slide layout system.
"""

import pytest
import json
from typing import Dict, Any, List
from unittest.mock import Mock, patch

# Import the modules we're testing
from tools.powerpoint_layout_schema import (
    PowerPointLayoutSchema,
    PlaceholderDefinition,
    LayoutValidationError
)
from tools.powerpoint_positioning_calculator import (
    ParameterizedPosition,
    AspectRatioMultiplier,
    PositioningCalculator,
    EMUCalculator,
    DesignTokenResolver
)


class TestPowerPointLayoutSchema:
    """Test the PowerPoint layout schema validation and structure"""
    
    def test_schema_initialization(self):
        """Test that layout schema initializes with valid structure"""
        schema = PowerPointLayoutSchema()
        assert schema is not None
        assert hasattr(schema, 'layouts')
        assert hasattr(schema, 'aspect_ratios')
        assert hasattr(schema, 'placeholder_types')
    
    def test_schema_contains_all_12_layout_types(self):
        """Test that schema includes all 12 standard PowerPoint layout types"""
        schema = PowerPointLayoutSchema()
        expected_types = [
            'title', 'obj', 'secHead', 'twoObj', 'twoTxTwoObj',
            'titleOnly', 'blank', 'objTx', 'picTx', 'pic'
        ]
        
        layout_types = [layout['type'] for layout in schema.layouts]
        for expected_type in expected_types:
            assert expected_type in layout_types
    
    def test_schema_contains_proper_layout_names(self):
        """Test that schema includes professional PowerPoint layout names"""
        schema = PowerPointLayoutSchema()
        expected_names = [
            'Title Slide', 'Title and Content', 'Section Header',
            'Two Content', 'Comparison', 'Title Only', 'Blank',
            'Content with Caption', 'Picture with Caption', 'Full Page Photo'
        ]
        
        layout_names = [layout['name'] for layout in schema.layouts]
        for expected_name in expected_names:
            assert expected_name in layout_names
    
    def test_schema_validation_with_valid_json(self):
        """Test schema validation passes with valid layout JSON"""
        schema = PowerPointLayoutSchema()
        valid_layout = {
            'id': 'title_slide',
            'type': 'title',
            'name': 'Title Slide',
            'placeholders': [
                {
                    'type': 'ctrTitle',
                    'position': {
                        'x': '${positioning.title.center.x}',
                        'y': '${positioning.title.center.y}',
                        'width': '${positioning.title.width}',
                        'height': '${positioning.title.height}'
                    }
                }
            ]
        }
        
        result = schema.validate_layout(valid_layout)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_schema_validation_fails_with_invalid_json(self):
        """Test schema validation fails with invalid layout JSON"""
        schema = PowerPointLayoutSchema()
        invalid_layout = {
            'id': 'invalid',
            # Missing required 'type' field
            'name': 'Invalid Layout'
        }
        
        result = schema.validate_layout(invalid_layout)
        assert not result.is_valid
        assert len(result.errors) > 0
        assert 'type' in str(result.errors[0])


class TestParameterizedPosition:
    """Test parameterized positioning system with design tokens"""
    
    def test_parameterized_position_creation(self):
        """Test creating parameterized position with design token variables"""
        position = ParameterizedPosition(
            x='${positioning.content.left.x}',
            y='${positioning.content.top.y}',
            width='${positioning.content.width}',
            height='${positioning.content.height}'
        )
        
        assert position.x == '${positioning.content.left.x}'
        assert position.y == '${positioning.content.top.y}'
        assert position.width == '${positioning.content.width}'
        assert position.height == '${positioning.content.height}'
    
    def test_position_has_design_token_variables(self):
        """Test that position correctly identifies design token variables"""
        position = ParameterizedPosition(
            x='${positioning.title.x}',
            y='1000000',  # Fixed EMU value
            width='${positioning.title.width}',
            height='${positioning.title.height}'
        )
        
        variables = position.get_design_token_variables()
        expected_variables = [
            '${positioning.title.x}',
            '${positioning.title.width}',
            '${positioning.title.height}'
        ]
        
        for var in expected_variables:
            assert var in variables
        assert '1000000' not in variables  # Fixed value shouldn't be in variables


class TestAspectRatioMultiplier:
    """Test aspect ratio responsive positioning multipliers"""
    
    def test_aspect_ratio_multiplier_16_9(self):
        """Test aspect ratio multiplier for 16:9 widescreen"""
        multiplier = AspectRatioMultiplier('16:9')
        
        # 16:9 should be base ratio with 1.0 multipliers
        assert multiplier.width_multiplier == 1.0
        assert multiplier.height_multiplier == 1.0
        assert multiplier.slide_width_emu == 9144000  # PowerPoint 16:9 width
        assert multiplier.slide_height_emu == 5143500  # PowerPoint 16:9 height
    
    def test_aspect_ratio_multiplier_4_3(self):
        """Test aspect ratio multiplier for 4:3 standard"""
        multiplier = AspectRatioMultiplier('4:3')
        
        # 4:3 should have different dimensions
        assert multiplier.slide_width_emu == 9144000  # Standard PowerPoint width
        assert multiplier.slide_height_emu == 6858000  # Standard PowerPoint 4:3 height
        
        # Width multiplier should be 1.0, height should be > 1.0
        assert multiplier.width_multiplier == 1.0
        assert multiplier.height_multiplier > 1.0
    
    def test_aspect_ratio_multiplier_16_10(self):
        """Test aspect ratio multiplier for 16:10 widescreen"""
        multiplier = AspectRatioMultiplier('16:10')
        
        # 16:10 should have intermediate height
        assert multiplier.slide_width_emu == 9144000
        assert 5143500 < multiplier.slide_height_emu < 6858000  # Between 16:9 and 4:3
    
    def test_invalid_aspect_ratio_raises_error(self):
        """Test that invalid aspect ratio raises appropriate error"""
        with pytest.raises(ValueError, match="Unsupported aspect ratio"):
            AspectRatioMultiplier('21:9')


class TestPositioningCalculator:
    """Test positioning calculator for design token resolution"""
    
    def test_calculator_initialization(self):
        """Test positioning calculator initializes with aspect ratio"""
        calculator = PositioningCalculator(aspect_ratio='16:9')
        assert calculator is not None
        assert calculator.aspect_ratio == '16:9'
    
    @patch('tools.variable_resolver.VariableResolver.resolve')
    def test_resolve_design_token_to_emu(self, mock_resolve):
        """Test resolving design token variable to EMU coordinates"""
        mock_resolve.return_value = '2000000'  # 2 million EMU
        
        calculator = PositioningCalculator(aspect_ratio='16:9')
        result = calculator.resolve_position_token('${positioning.title.x}')
        
        assert result == 2000000
        mock_resolve.assert_called_once()
    
    def test_calculate_responsive_position(self):
        """Test calculating responsive position based on aspect ratio"""
        calculator = PositioningCalculator(aspect_ratio='4:3')
        
        # Mock base position for 16:9
        base_position = {
            'x': 1000000,
            'y': 500000,
            'width': 8000000,
            'height': 1000000
        }
        
        responsive_position = calculator.calculate_responsive_position(base_position)
        
        # For 4:3, Y positions should be adjusted for taller slide
        assert responsive_position['x'] == base_position['x']  # X unchanged
        assert responsive_position['y'] >= base_position['y']  # Y may be adjusted
        assert responsive_position['width'] == base_position['width']  # Width unchanged
        assert responsive_position['height'] >= base_position['height']  # Height may scale
    
    def test_resolve_parameterized_layout(self):
        """Test resolving complete parameterized layout to EMU values"""
        calculator = PositioningCalculator(aspect_ratio='16:9')
        
        parameterized_layout = {
            'placeholders': [
                {
                    'type': 'title',
                    'position': {
                        'x': '${positioning.title.x}',
                        'y': '${positioning.title.y}',
                        'width': '${positioning.title.width}',
                        'height': '${positioning.title.height}'
                    }
                }
            ]
        }
        
        # Mock the variable resolver to return specific EMU values
        with patch.object(calculator, 'resolve_position_token') as mock_resolve:
            mock_resolve.side_effect = lambda token: {
                '${positioning.title.x}': 755000,
                '${positioning.title.y}': 1122000,
                '${positioning.title.width}': 9464000,
                '${positioning.title.height}': 2388000
            }[token]
            
            resolved_layout = calculator.resolve_parameterized_layout(parameterized_layout)
            
            placeholder = resolved_layout['placeholders'][0]
            assert placeholder['position']['x'] == 755000
            assert placeholder['position']['y'] == 1122000
            assert placeholder['position']['width'] == 9464000
            assert placeholder['position']['height'] == 2388000


class TestPlaceholderDefinition:
    """Test placeholder type definitions with parameterized dimensions"""
    
    def test_placeholder_definition_creation(self):
        """Test creating placeholder definition with all required fields"""
        placeholder = PlaceholderDefinition(
            type='title',
            ph_type='ctrTitle',
            size='full',
            index=0,
            position=ParameterizedPosition(
                x='${positioning.title.x}',
                y='${positioning.title.y}',
                width='${positioning.title.width}',
                height='${positioning.title.height}'
            )
        )
        
        assert placeholder.type == 'title'
        assert placeholder.ph_type == 'ctrTitle'
        assert placeholder.size == 'full'
        assert placeholder.index == 0
        assert isinstance(placeholder.position, ParameterizedPosition)
    
    def test_placeholder_supports_all_powerpoint_types(self):
        """Test that placeholder definitions support all PowerPoint placeholder types"""
        supported_types = [
            'ctrTitle', 'subTitle', 'title', 'body', 'pic',
            'dt', 'ftr', 'sldNum', 'chart', 'tbl', 'media'
        ]
        
        for ph_type in supported_types:
            placeholder = PlaceholderDefinition(
                type='content',
                ph_type=ph_type,
                size='half',
                index=1,
                position=ParameterizedPosition('0', '0', '100', '100')
            )
            assert placeholder.ph_type == ph_type
    
    def test_placeholder_generates_office_metadata(self):
        """Test that placeholder definition generates proper Office metadata"""
        placeholder = PlaceholderDefinition(
            type='title',
            ph_type='ctrTitle',
            size='full',
            index=0,
            position=ParameterizedPosition('0', '0', '100', '100')
        )
        
        metadata = placeholder.generate_office_metadata()
        
        assert 'creation_id' in metadata
        assert 'shape_locks' in metadata
        assert metadata['shape_locks']['noGrp'] == '1'
        assert len(metadata['creation_id']) > 0  # Should generate UUID


class TestEMUCalculator:
    """Test EMU (English Metric Unit) calculation utilities"""
    
    def test_emu_to_points_conversion(self):
        """Test converting EMU to points"""
        # 1 point = 12700 EMU
        emu_value = 127000  # 10 points
        points = EMUCalculator.emu_to_points(emu_value)
        assert points == 10.0
    
    def test_points_to_emu_conversion(self):
        """Test converting points to EMU"""
        points = 12.0
        emu_value = EMUCalculator.points_to_emu(points)
        assert emu_value == 152400  # 12 * 12700
    
    def test_percentage_to_emu_width(self):
        """Test converting percentage to EMU width based on slide dimensions"""
        # For 16:9 slide width of 9144000 EMU
        percentage = 50.0  # 50%
        emu_width = EMUCalculator.percentage_to_emu_width(percentage, '16:9')
        assert emu_width == 4572000  # Half of slide width
    
    def test_percentage_to_emu_height(self):
        """Test converting percentage to EMU height based on slide dimensions"""
        # For 16:9 slide height of 5143500 EMU
        percentage = 25.0  # 25%
        emu_height = EMUCalculator.percentage_to_emu_height(percentage, '16:9')
        assert emu_height == 1285875  # Quarter of slide height


if __name__ == '__main__':
    pytest.main([__file__])