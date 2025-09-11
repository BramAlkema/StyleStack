"""
PowerPoint Layout Schema Validation System

This module provides schema validation and structure management for
PowerPoint-compatible slide layouts with parameterized positioning.
"""

import json
import uuid
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from pathlib import Path
from jsonschema import validate, ValidationError, Draft7Validator

from tools.powerpoint_positioning_calculator import ParameterizedPosition
from tools.core.types import ProcessingResult


class LayoutValidationError(Exception):
    """Exception raised when layout validation fails"""
    pass


@dataclass
class ValidationResult:
    """Result of layout validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


@dataclass 
class PlaceholderDefinition:
    """PowerPoint placeholder definition with Office metadata"""
    
    def __init__(
        self, 
        type: str,
        ph_type: str, 
        size: str,
        index: int,
        position: ParameterizedPosition,
        name: Optional[str] = None,
        typography: Optional[Dict[str, Any]] = None,
        shape_properties: Optional[Dict[str, Any]] = None
    ):
        self.type = type
        self.ph_type = ph_type
        self.size = size
        self.index = index
        self.position = position
        self.name = name or f"{ph_type.title()} {index}"
        self.typography = typography or {}
        self.shape_properties = shape_properties or {}
    
    def generate_office_metadata(self) -> Dict[str, Any]:
        """Generate Office-specific metadata for placeholder"""
        # Generate unique creation ID (UUID format used by Office)
        creation_id = f"{{{str(uuid.uuid4()).upper()}}}"
        
        metadata = {
            'creation_id': creation_id,
            'shape_locks': {
                'noGrp': '1'  # Prevent grouping with other shapes
            },
            'extensions': {
                'uri': '{FF2B5EF4-FFF2-40B4-BE49-F238E27FC236}',
                'namespace': 'http://schemas.microsoft.com/office/drawing/2014/main'
            }
        }
        
        # Add type-specific metadata
        if self.ph_type in ['ctrTitle', 'subTitle', 'title']:
            metadata['text_properties'] = {
                'anchor': self.typography.get('anchor', 'b'),
                'auto_fit': self.shape_properties.get('auto_fit', 'normal')
            }
        elif self.ph_type == 'pic':
            metadata['picture_properties'] = {
                'preserve_aspect_ratio': True,
                'fill_mode': 'stretch'
            }
        elif self.ph_type in ['dt', 'ftr', 'sldNum']:
            metadata['footer_properties'] = {
                'field_type': {
                    'dt': 'datetime4',
                    'ftr': 'text',
                    'sldNum': 'slidenum'
                }.get(self.ph_type, 'text')
            }
        
        return metadata
    
    def supports_powerpoint_type(self) -> bool:
        """Check if placeholder type is supported by PowerPoint"""
        supported_types = [
            'ctrTitle', 'subTitle', 'title', 'body', 'pic',
            'dt', 'ftr', 'sldNum', 'chart', 'tbl', 'media'
        ]
        return self.ph_type in supported_types
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert placeholder definition to dictionary"""
        return {
            'type': self.type,
            'ph_type': self.ph_type,
            'size': self.size,
            'index': self.index,
            'name': self.name,
            'position': {
                'x': self.position.x,
                'y': self.position.y,
                'width': self.position.width,
                'height': self.position.height
            },
            'typography': self.typography,
            'shape_properties': self.shape_properties
        }


class PowerPointLayoutSchema:
    """PowerPoint layout schema validation and management"""
    
    def __init__(self, schema_file: Optional[str] = None):
        if schema_file is None:
            schema_file = Path(__file__).parent.parent / 'schemas' / 'powerpoint-layout-schema.json'
        
        self.schema_file = Path(schema_file)
        self.schema = self._load_schema()
        self.validator = Draft7Validator(self.schema)
        
        # Load layout data
        layout_file = Path(__file__).parent.parent / 'data' / 'powerpoint-layouts.json'
        with open(layout_file, 'r', encoding='utf-8') as f:
            self.layout_data = json.load(f)
        
        self.layouts = self.layout_data.get('layouts', [])
        self.aspect_ratios = ['16:9', '4:3', '16:10']  # Supported aspect ratios
        self.placeholder_types = [
            'ctrTitle', 'subTitle', 'title', 'body', 'pic',
            'dt', 'ftr', 'sldNum', 'chart', 'tbl', 'media'
        ]
    
    def _load_schema(self) -> Dict[str, Any]:
        """Load JSON schema from file"""
        try:
            with open(self.schema_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise LayoutValidationError(f"Schema file not found: {self.schema_file}")
        except json.JSONDecodeError as e:
            raise LayoutValidationError(f"Invalid JSON in schema file: {e}")
    
    def validate_layout(self, layout_data: Dict[str, Any]) -> ValidationResult:
        """Validate a single layout against the schema"""
        errors = []
        warnings = []
        
        try:
            # JSON schema validation - create temporary schema with definitions for $ref resolution
            temp_schema = {
                "definitions": self.schema['definitions'],
                **self.schema['definitions']['layout']
            }
            validate(instance=layout_data, schema=temp_schema)
            
            # Additional custom validation
            custom_validation = self._custom_validation(layout_data)
            errors.extend(custom_validation.errors)
            warnings.extend(custom_validation.warnings)
            
        except ValidationError as e:
            errors.append(f"Schema validation error: {e.message}")
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _custom_validation(self, layout_data: Dict[str, Any]) -> ValidationResult:
        """Perform custom validation beyond JSON schema"""
        errors = []
        warnings = []
        
        # Validate layout type
        layout_type = layout_data.get('type')
        valid_types = ['title', 'obj', 'secHead', 'twoObj', 'twoTxTwoObj', 
                      'titleOnly', 'blank', 'objTx', 'picTx', 'pic']
        if layout_type not in valid_types:
            errors.append(f"Invalid layout type: {layout_type}")
        
        # Validate placeholders
        placeholders = layout_data.get('placeholders', [])
        if not placeholders and layout_type != 'blank':
            warnings.append("Layout has no placeholders (except blank layouts)")
        
        placeholder_indices = []
        for placeholder in placeholders:
            # Check placeholder type
            ph_type = placeholder.get('type')
            if ph_type not in self.placeholder_types:
                errors.append(f"Unsupported placeholder type: {ph_type}")
            
            # Check for duplicate indices
            index = placeholder.get('index')
            if index in placeholder_indices:
                errors.append(f"Duplicate placeholder index: {index}")
            placeholder_indices.append(index)
            
            # Validate position
            position = placeholder.get('position', {})
            if not all(key in position for key in ['x', 'y', 'width', 'height']):
                errors.append(f"Incomplete position data for placeholder {placeholder.get('name', 'unnamed')}")
        
        # Layout-specific validation
        if layout_type == 'title' and not any(p.get('type') == 'ctrTitle' for p in placeholders):
            warnings.append("Title layout should have a ctrTitle placeholder")
        
        if layout_type == 'twoObj' and len([p for p in placeholders if p.get('type') == 'body']) < 2:
            warnings.append("Two content layout should have at least 2 body placeholders")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_all_layouts(self) -> Dict[str, ValidationResult]:
        """Validate all layouts in the schema"""
        results = {}
        
        for layout in self.layouts:
            layout_id = layout.get('id', 'unknown')
            results[layout_id] = self.validate_layout(layout)
        
        return results
    
    def get_layout_by_id(self, layout_id: str) -> Optional[Dict[str, Any]]:
        """Get layout definition by ID"""
        for layout in self.layouts:
            if layout.get('id') == layout_id:
                return layout
        return None
    
    def get_layouts_by_type(self, layout_type: str) -> List[Dict[str, Any]]:
        """Get all layouts of a specific type"""
        return [layout for layout in self.layouts if layout.get('type') == layout_type]
    
    def get_supported_aspect_ratios(self, layout_id: str) -> List[str]:
        """Get supported aspect ratios for a layout"""
        layout = self.get_layout_by_id(layout_id)
        if layout:
            return layout.get('aspect_ratio_support', self.aspect_ratios)
        return []
    
    def create_placeholder_definition(
        self,
        type: str,
        ph_type: str,
        size: str,
        index: int,
        x: str, y: str, width: str, height: str,
        **kwargs
    ) -> PlaceholderDefinition:
        """Create a placeholder definition with validation"""
        position = ParameterizedPosition(x, y, width, height)
        
        placeholder = PlaceholderDefinition(
            type=type,
            ph_type=ph_type,
            size=size,
            index=index,
            position=position,
            **kwargs
        )
        
        if not placeholder.supports_powerpoint_type():
            raise LayoutValidationError(f"Unsupported PowerPoint placeholder type: {ph_type}")
        
        return placeholder
    
    def generate_layout_summary(self) -> Dict[str, Any]:
        """Generate summary of all layouts in schema"""
        summary = {
            'total_layouts': len(self.layouts),
            'layout_types': {},
            'placeholder_types': set(),
            'aspect_ratio_support': {},
            'validation_results': {}
        }
        
        # Analyze layouts
        for layout in self.layouts:
            layout_type = layout.get('type', 'unknown')
            layout_id = layout.get('id', 'unknown')
            
            # Count layout types
            if layout_type not in summary['layout_types']:
                summary['layout_types'][layout_type] = 0
            summary['layout_types'][layout_type] += 1
            
            # Collect placeholder types
            for placeholder in layout.get('placeholders', []):
                summary['placeholder_types'].add(placeholder.get('type'))
            
            # Track aspect ratio support
            aspect_ratios = layout.get('aspect_ratio_support', [])
            for ar in aspect_ratios:
                if ar not in summary['aspect_ratio_support']:
                    summary['aspect_ratio_support'][ar] = 0
                summary['aspect_ratio_support'][ar] += 1
            
            # Validate layout
            summary['validation_results'][layout_id] = self.validate_layout(layout)
        
        # Convert set to list for JSON serialization
        summary['placeholder_types'] = list(summary['placeholder_types'])
        
        return summary
    
    def export_layout_for_ooxml(self, layout_id: str, aspect_ratio: str = '16:9') -> ProcessingResult:
        """Export layout in format suitable for OOXML generation"""
        try:
            from tools.powerpoint_positioning_calculator import PositioningCalculator
            
            layout = self.get_layout_by_id(layout_id)
            if not layout:
                return ProcessingResult(
                    success=False,
                    errors=[f"Layout not found: {layout_id}"],
                    data=None
                )
            
            # Resolve positioning for aspect ratio
            calculator = PositioningCalculator(aspect_ratio)
            resolved_layout = calculator.resolve_parameterized_layout(layout)
            
            # Add OOXML-specific metadata
            ooxml_layout = {
                'id': resolved_layout['id'],
                'name': resolved_layout['name'],
                'type': resolved_layout['type'],
                'ooxml_type': resolved_layout['type'],  # OOXML layout type attribute
                'preserve': True,
                'show_master_shapes': resolved_layout.get('master_relationship', {}).get('show_master_shapes', True),
                'placeholders': []
            }
            
            # Process placeholders for OOXML
            for placeholder in resolved_layout.get('placeholders', []):
                ph_def = PlaceholderDefinition(
                    type=placeholder['type'],
                    ph_type=placeholder['type'],  
                    size=placeholder['size'],
                    index=placeholder['index'],
                    position=ParameterizedPosition(
                        str(placeholder['position']['x']),
                        str(placeholder['position']['y']),
                        str(placeholder['position']['width']),
                        str(placeholder['position']['height'])
                    ),
                    name=placeholder.get('name'),
                    typography=placeholder.get('typography', {}),
                    shape_properties=placeholder.get('shape_properties', {})
                )
                
                ooxml_placeholder = ph_def.to_dict()
                ooxml_placeholder['office_metadata'] = ph_def.generate_office_metadata()
                ooxml_layout['placeholders'].append(ooxml_placeholder)
            
            return ProcessingResult(
                success=True,
                data=ooxml_layout,
                metadata={
                    'aspect_ratio': aspect_ratio,
                    'slide_dimensions': calculator.get_slide_dimensions()
                }
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                errors=[f"Export error: {str(e)}"],
                data=None
            )


def create_layout_schema(schema_file: Optional[str] = None) -> PowerPointLayoutSchema:
    """Factory function to create layout schema"""
    return PowerPointLayoutSchema(schema_file)


if __name__ == '__main__':
    # Demo usage
    print("📋 PowerPoint Layout Schema Demo")
    
    schema = PowerPointLayoutSchema()
    
    # Validate all layouts
    print(f"\n🔍 Validating {len(schema.layouts)} layouts:")
    validation_results = schema.validate_all_layouts()
    
    for layout_id, result in validation_results.items():
        status = "✅ VALID" if result.is_valid else "❌ INVALID"
        print(f"   {layout_id}: {status}")
        if result.errors:
            for error in result.errors:
                print(f"     - Error: {error}")
        if result.warnings:
            for warning in result.warnings:
                print(f"     - Warning: {warning}")
    
    # Generate summary
    print(f"\n📊 Layout Summary:")
    summary = schema.generate_layout_summary()
    print(f"   Total layouts: {summary['total_layouts']}")
    print(f"   Layout types: {dict(summary['layout_types'])}")
    print(f"   Placeholder types: {len(summary['placeholder_types'])}")
    print(f"   Aspect ratio support: {dict(summary['aspect_ratio_support'])}")
    
    # Test OOXML export
    print(f"\n🎨 Testing OOXML export:")
    for aspect_ratio in ['16:9', '4:3', '16:10']:
        result = schema.export_layout_for_ooxml('title_slide', aspect_ratio)
        if result.success:
            dimensions = result.metadata['slide_dimensions']
            print(f"   {aspect_ratio}: {dimensions[0]:,} x {dimensions[1]:,} EMU")