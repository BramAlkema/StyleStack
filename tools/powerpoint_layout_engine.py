"""
PowerPoint Layout Engine

This module provides the main interface for PowerPoint layout generation,
integrating the schema validation, positioning calculator, and placeholder 
type system into a unified layout engine.
"""

from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
import json

from tools.powerpoint_layout_schema import PowerPointLayoutSchema, ValidationResult
from tools.powerpoint_positioning_calculator import PositioningCalculator, DesignTokenResolver
from tools.powerpoint_placeholder_types import (
    PlaceholderFactory, StandardPlaceholderSets, PlaceholderType, PlaceholderSize,
    PlaceholderTemplate, ParameterizedPosition
)
from tools.core.types import ProcessingResult


class PowerPointLayoutEngine:
    """Main engine for PowerPoint layout generation and validation"""
    
    def __init__(
        self,
        schema_file: Optional[str] = None,
        layout_data_file: Optional[str] = None,
        default_aspect_ratio: str = '16:9'
    ):
        self.default_aspect_ratio = default_aspect_ratio
        
        # Initialize core components
        self.schema = PowerPointLayoutSchema(schema_file)
        self.positioning_calculator = PositioningCalculator(default_aspect_ratio)
        self.token_resolver = DesignTokenResolver(default_aspect_ratio)
        
        # Cache for resolved layouts
        self._layout_cache: Dict[str, Dict[str, Any]] = {}
        
        # Supported aspect ratios
        self.supported_aspect_ratios = ['16:9', '4:3', '16:10']
        
        # Initialize layout templates
        self._initialize_layout_templates()
    
    def _initialize_layout_templates(self):
        """Initialize standard layout templates"""
        self.layout_templates = {
            'title_slide': self._create_title_slide_template,
            'title_and_content': self._create_title_content_template,
            'section_header': self._create_section_header_template,
            'two_content': self._create_two_content_template,
            'comparison': self._create_comparison_template,
            'title_only': self._create_title_only_template,
            'blank': self._create_blank_template,
            'content_with_caption': self._create_content_caption_template,
            'picture_with_caption': self._create_picture_caption_template,
            'full_page_photo': self._create_full_page_photo_template
        }
    
    def set_aspect_ratio(self, aspect_ratio: str) -> ProcessingResult:
        """Set the aspect ratio for layout calculations"""
        if aspect_ratio not in self.supported_aspect_ratios:
            return ProcessingResult(
                success=False,
                errors=[f"Unsupported aspect ratio: {aspect_ratio}. Supported: {self.supported_aspect_ratios}"]
            )
        
        self.default_aspect_ratio = aspect_ratio
        self.positioning_calculator = PositioningCalculator(aspect_ratio)
        self.token_resolver = DesignTokenResolver(aspect_ratio)
        
        # Clear cache when aspect ratio changes
        self._layout_cache.clear()
        
        return ProcessingResult(success=True, data={'aspect_ratio': aspect_ratio})
    
    def get_available_layouts(self) -> List[Dict[str, Any]]:
        """Get list of available layout types"""
        layouts = []
        for layout in self.schema.layouts:
            layouts.append({
                'id': layout['id'],
                'name': layout['name'],
                'type': layout['type'],
                'description': layout.get('description', ''),
                'placeholder_count': len(layout.get('placeholders', []))
            })
        return layouts
    
    def validate_layout_definition(self, layout_id: str) -> ValidationResult:
        """Validate a specific layout definition"""
        layout = self.schema.get_layout_by_id(layout_id)
        if not layout:
            return ValidationResult(
                is_valid=False,
                errors=[f"Layout not found: {layout_id}"],
                warnings=[]
            )
        
        return self.schema.validate_layout(layout)
    
    def resolve_layout_positioning(
        self,
        layout_id: str,
        aspect_ratio: Optional[str] = None
    ) -> ProcessingResult:
        """Resolve layout positioning to EMU coordinates"""
        if aspect_ratio is None:
            aspect_ratio = self.default_aspect_ratio
        
        # Check cache first
        cache_key = f"{layout_id}_{aspect_ratio}"
        if cache_key in self._layout_cache:
            return ProcessingResult(
                success=True,
                data=self._layout_cache[cache_key],
                metadata={'cached': True, 'aspect_ratio': aspect_ratio}
            )
        
        # Get layout definition
        layout = self.schema.get_layout_by_id(layout_id)
        if not layout:
            return ProcessingResult(
                success=False,
                errors=[f"Layout not found: {layout_id}"]
            )
        
        # Create calculator for specific aspect ratio
        calculator = PositioningCalculator(aspect_ratio)
        
        try:
            # Resolve positioning
            resolved_layout = calculator.resolve_parameterized_layout(layout)
            
            # Validate positioning bounds
            validation_errors = []
            validation_warnings = []
            
            for placeholder in resolved_layout.get('placeholders', []):
                position = placeholder['position']
                validation_result = calculator.validate_position_bounds(position)
                
                if not validation_result.success:
                    validation_errors.extend(validation_result.errors)
                validation_warnings.extend(validation_result.warnings)
            
            # Cache the result
            self._layout_cache[cache_key] = resolved_layout
            
            return ProcessingResult(
                success=len(validation_errors) == 0,
                data=resolved_layout,
                errors=validation_errors,
                warnings=validation_warnings,
                metadata={
                    'aspect_ratio': aspect_ratio,
                    'slide_dimensions': calculator.get_slide_dimensions(),
                    'placeholder_count': len(resolved_layout.get('placeholders', []))
                }
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                errors=[f"Error resolving layout positioning: {str(e)}"]
            )
    
    def generate_layout_for_ooxml(
        self,
        layout_id: str,
        aspect_ratio: Optional[str] = None,
        layout_number: int = 1
    ) -> ProcessingResult:
        """Generate layout in OOXML-ready format"""
        resolution_result = self.resolve_layout_positioning(layout_id, aspect_ratio)
        
        if not resolution_result.success:
            return resolution_result
        
        resolved_layout = resolution_result.data
        
        try:
            # Convert to OOXML format
            ooxml_layout = {
                'layout_number': layout_number,
                'file_name': f'slideLayout{layout_number}.xml',
                'id': resolved_layout['id'],
                'name': resolved_layout['name'],
                'type': resolved_layout['type'],
                'preserve': True,
                'show_master_shapes': resolved_layout.get('master_relationship', {}).get('show_master_shapes', False),
                'placeholders': [],
                'relationships': {
                    'theme': '../theme/theme1.xml',
                    'master': '../slideMasters/slideMaster1.xml'
                }
            }
            
            # Process placeholders for OOXML
            shape_id = 2  # Start at 2 (1 is reserved for group)
            
            for placeholder_data in resolved_layout.get('placeholders', []):
                # Create placeholder template
                ph_type = PlaceholderType(placeholder_data['type'])
                position = ParameterizedPosition(
                    str(placeholder_data['position']['x']),
                    str(placeholder_data['position']['y']),
                    str(placeholder_data['position']['width']),
                    str(placeholder_data['position']['height'])
                )
                
                placeholder = PlaceholderTemplate(
                    ph_type=ph_type,
                    name=placeholder_data.get('name', f'{ph_type.value} {shape_id}'),
                    size=PlaceholderSize(placeholder_data.get('size', 'full')),
                    position=position,
                    index=placeholder_data.get('index', shape_id - 1)
                )
                
                # Convert to OOXML format
                ooxml_placeholder = placeholder.to_ooxml_placeholder(shape_id)
                ooxml_layout['placeholders'].append(ooxml_placeholder)
                
                shape_id += 1
            
            return ProcessingResult(
                success=True,
                data=ooxml_layout,
                metadata=resolution_result.metadata
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                errors=[f"Error generating OOXML layout: {str(e)}"]
            )
    
    def generate_all_layouts_for_ooxml(
        self,
        aspect_ratio: Optional[str] = None
    ) -> ProcessingResult:
        """Generate all 12 PowerPoint layouts for OOXML"""
        if aspect_ratio is None:
            aspect_ratio = self.default_aspect_ratio
        
        ooxml_layouts = []
        errors = []
        warnings = []
        
        layout_ids = [layout['id'] for layout in self.schema.layouts[:12]]  # First 12 layouts
        
        for i, layout_id in enumerate(layout_ids, 1):
            result = self.generate_layout_for_ooxml(layout_id, aspect_ratio, i)
            
            if result.success:
                ooxml_layouts.append(result.data)
                warnings.extend(result.warnings)
            else:
                errors.extend(result.errors)
        
        return ProcessingResult(
            success=len(errors) == 0,
            data={
                'layouts': ooxml_layouts,
                'count': len(ooxml_layouts),
                'aspect_ratio': aspect_ratio
            },
            errors=errors,
            warnings=warnings,
            metadata={
                'total_layouts_generated': len(ooxml_layouts),
                'aspect_ratio': aspect_ratio,
                'slide_dimensions': self.positioning_calculator.get_slide_dimensions()
            }
        )
    
    def _create_title_slide_template(self) -> List[PlaceholderTemplate]:
        """Create title slide template"""
        return StandardPlaceholderSets.create_title_slide_set()
    
    def _create_title_content_template(self) -> List[PlaceholderTemplate]:
        """Create title and content template"""
        return StandardPlaceholderSets.create_title_content_set()
    
    def _create_section_header_template(self) -> List[PlaceholderTemplate]:
        """Create section header template"""
        placeholders = [
            PlaceholderFactory.create_title_placeholder(
                "Title 1",
                ParameterizedPosition(
                    x="${margins.left}",
                    y="${slide.height * 0.332}",
                    width="${content_areas.full_width}",
                    height="${slide.height * 0.555}"
                ),
                typography_preset='section_header',
                index=0
            ),
            PlaceholderFactory.create_body_placeholder(
                "Text Placeholder 2",
                ParameterizedPosition(
                    x="${margins.left}",
                    y="${slide.height * 0.892}",
                    width="${content_areas.full_width}",
                    height="${slide.height * 0.292}"
                ),
                index=1
            )
        ]
        placeholders.extend(StandardPlaceholderSets.create_standard_footer_set())
        return placeholders
    
    def _create_two_content_template(self) -> List[PlaceholderTemplate]:
        """Create two content template"""
        return StandardPlaceholderSets.create_two_content_set()
    
    def _create_comparison_template(self) -> List[PlaceholderTemplate]:
        """Create comparison (4-quadrant) template"""
        placeholders = [
            PlaceholderFactory.create_title_placeholder(
                "Title 1",
                ParameterizedPosition(
                    x="${margins.left}",
                    y="${margins.top}",
                    width="${content_areas.full_width}",
                    height="${slide.height * 0.258}"
                ),
                index=0
            )
        ]
        
        # Left header and content
        placeholders.extend([
            PlaceholderTemplate(
                ph_type=PlaceholderType.BODY,
                name="Text Placeholder 2",
                size=PlaceholderSize.HALF,
                position=ParameterizedPosition(
                    x="${margins.left}",
                    y="${margins.top + slide.height * 0.258 + gutters.vertical}",
                    width="${content_areas.half_width}",
                    height="${slide.height * 0.108}"
                ),
                typography=PlaceholderFactory.TYPOGRAPHY_PRESETS['comparison_header'],
                index=1
            ),
            PlaceholderFactory.create_body_placeholder(
                "Content Placeholder 3",
                ParameterizedPosition(
                    x="${margins.left}",
                    y="${margins.top + slide.height * 0.258 + gutters.vertical + slide.height * 0.108 + gutters.vertical}",
                    width="${content_areas.half_width}",
                    height="${slide.height - margins.top - margins.bottom - slide.height * 0.258 - gutters.vertical * 3 - slide.height * 0.108}"
                ),
                size=PlaceholderSize.HALF,
                index=2
            )
        ])
        
        # Right header and content
        placeholders.extend([
            PlaceholderTemplate(
                ph_type=PlaceholderType.BODY,
                name="Text Placeholder 4",
                size=PlaceholderSize.QUARTER,
                position=ParameterizedPosition(
                    x="${margins.left + content_areas.half_width + gutters.horizontal}",
                    y="${margins.top + slide.height * 0.258 + gutters.vertical}",
                    width="${content_areas.half_width}",
                    height="${slide.height * 0.108}"
                ),
                typography=PlaceholderFactory.TYPOGRAPHY_PRESETS['comparison_header'],
                index=3
            ),
            PlaceholderFactory.create_body_placeholder(
                "Content Placeholder 5",
                ParameterizedPosition(
                    x="${margins.left + content_areas.half_width + gutters.horizontal}",
                    y="${margins.top + slide.height * 0.258 + gutters.vertical + slide.height * 0.108 + gutters.vertical}",
                    width="${content_areas.half_width}",
                    height="${slide.height - margins.top - margins.bottom - slide.height * 0.258 - gutters.vertical * 3 - slide.height * 0.108}"
                ),
                size=PlaceholderSize.QUARTER,
                index=4
            )
        ])
        
        placeholders.extend(StandardPlaceholderSets.create_standard_footer_set())
        return placeholders
    
    def _create_title_only_template(self) -> List[PlaceholderTemplate]:
        """Create title only template"""
        placeholders = [
            PlaceholderFactory.create_title_placeholder(
                "Title 1",
                ParameterizedPosition(
                    x="${margins.left}",
                    y="${margins.top}",
                    width="${content_areas.full_width}",
                    height="${slide.height - margins.top - margins.bottom - slide.height * 0.070}"
                ),
                index=0
            )
        ]
        placeholders.extend(StandardPlaceholderSets.create_standard_footer_set())
        return placeholders
    
    def _create_blank_template(self) -> List[PlaceholderTemplate]:
        """Create blank template (footer only)"""
        return StandardPlaceholderSets.create_standard_footer_set()
    
    def _create_content_caption_template(self) -> List[PlaceholderTemplate]:
        """Create content with caption template"""
        placeholders = [
            PlaceholderFactory.create_title_placeholder(
                "Title 1",
                ParameterizedPosition(
                    x="${margins.left}",
                    y="${margins.top}",
                    width="${content_areas.full_width}",
                    height="${slide.height * 0.258}"
                ),
                index=0
            ),
            PlaceholderFactory.create_body_placeholder(
                "Content Placeholder 2",
                ParameterizedPosition(
                    x="${margins.left}",
                    y="${margins.top + slide.height * 0.258 + gutters.vertical}",
                    width="${content_areas.half_width + gutters.horizontal * 0.2}",
                    height="${slide.height - margins.top - margins.bottom - slide.height * 0.258 - gutters.vertical * 2}"
                ),
                size=PlaceholderSize.HALF,
                index=1
            ),
            PlaceholderTemplate(
                ph_type=PlaceholderType.BODY,
                name="Text Placeholder 3",
                size=PlaceholderSize.HALF,
                position=ParameterizedPosition(
                    x="${margins.left + content_areas.half_width + gutters.horizontal * 1.2}",
                    y="${margins.top + slide.height * 0.258 + gutters.vertical}",
                    width="${content_areas.half_width - gutters.horizontal * 0.2}",
                    height="${slide.height - margins.top - margins.bottom - slide.height * 0.258 - gutters.vertical * 2}"
                ),
                typography=PlaceholderFactory.TYPOGRAPHY_PRESETS['caption_text'],
                index=2
            )
        ]
        placeholders.extend(StandardPlaceholderSets.create_standard_footer_set())
        return placeholders
    
    def _create_picture_caption_template(self) -> List[PlaceholderTemplate]:
        """Create picture with caption template"""
        return StandardPlaceholderSets.create_picture_caption_set()
    
    def _create_full_page_photo_template(self) -> List[PlaceholderTemplate]:
        """Create full page photo template"""
        placeholders = [
            PlaceholderFactory.create_picture_placeholder(
                "Picture Placeholder 5",
                ParameterizedPosition(
                    x="0",
                    y="0",
                    width="${slide.width}",
                    height="${slide.height}"
                ),
                size=PlaceholderSize.CUSTOM,
                index=13
            )
        ]
        placeholders.extend(StandardPlaceholderSets.create_standard_footer_set())
        return placeholders
    
    def get_layout_statistics(self) -> Dict[str, Any]:
        """Get statistics about the layout engine"""
        return {
            'supported_aspect_ratios': self.supported_aspect_ratios,
            'default_aspect_ratio': self.default_aspect_ratio,
            'available_layouts': len(self.schema.layouts),
            'cached_layouts': len(self._layout_cache),
            'supported_placeholder_types': len(PlaceholderType),
            'layout_templates': len(self.layout_templates),
            'schema_version': self.schema.layout_data.get('schema_version', 'unknown')
        }


def create_powerpoint_layout_engine(
    aspect_ratio: str = '16:9',
    schema_file: Optional[str] = None
) -> PowerPointLayoutEngine:
    """Factory function to create PowerPoint layout engine"""
    engine = PowerPointLayoutEngine(
        schema_file=schema_file,
        default_aspect_ratio=aspect_ratio
    )
    return engine


if __name__ == '__main__':
    # Demo usage
    print("🏗️ PowerPoint Layout Engine Demo")
    
    # Create engine
    engine = PowerPointLayoutEngine()
    
    # Get statistics
    stats = engine.get_layout_statistics()
    print(f"\n📊 Engine Statistics:")
    print(f"   Supported aspect ratios: {stats['supported_aspect_ratios']}")
    print(f"   Available layouts: {stats['available_layouts']}")
    print(f"   Placeholder types: {stats['supported_placeholder_types']}")
    print(f"   Layout templates: {stats['layout_templates']}")
    
    # Test layout generation
    print(f"\n🎨 Testing layout generation:")
    result = engine.resolve_layout_positioning('title_slide', '16:9')
    if result.success:
        layout = result.data
        print(f"   Title slide resolved: {len(layout['placeholders'])} placeholders")
        print(f"   Slide dimensions: {result.metadata['slide_dimensions'][0]:,} x {result.metadata['slide_dimensions'][1]:,} EMU")
    
    # Test OOXML generation
    print(f"\n🔧 Testing OOXML generation:")
    ooxml_result = engine.generate_layout_for_ooxml('title_slide', '16:9', 1)
    if ooxml_result.success:
        ooxml_layout = ooxml_result.data
        print(f"   OOXML layout generated: {ooxml_layout['file_name']}")
        print(f"   Layout type: {ooxml_layout['type']}")
        print(f"   Placeholders: {len(ooxml_layout['placeholders'])}")
    
    # Test all layouts generation
    print(f"\n🎯 Testing all layouts generation:")
    all_layouts_result = engine.generate_all_layouts_for_ooxml('16:9')
    if all_layouts_result.success:
        data = all_layouts_result.data
        print(f"   Generated {data['count']} layouts successfully")
        print(f"   Aspect ratio: {data['aspect_ratio']}")
    
    # Test different aspect ratios
    print(f"\n📐 Testing aspect ratio changes:")
    for ar in ['4:3', '16:10']:
        result = engine.set_aspect_ratio(ar)
        if result.success:
            stats = engine.get_layout_statistics()
            print(f"   Set to {ar}: default = {stats['default_aspect_ratio']}")