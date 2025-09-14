"""
PowerPoint Placeholder Type Definitions

This module defines all PowerPoint placeholder types with their parameterized
dimensions, typography settings, and Office-specific metadata for professional
slide layout generation.
"""

from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid

from tools.powerpoint_positioning_calculator import ParameterizedPosition


class PlaceholderType(Enum):
    """Enumeration of PowerPoint placeholder types"""
    CENTER_TITLE = "ctrTitle"      # Centered title (title slide)
    SUB_TITLE = "subTitle"         # Subtitle (title slide)  
    TITLE = "title"                # Standard title
    BODY = "body"                  # Body text/content
    PICTURE = "pic"                # Picture/image
    DATE = "dt"                    # Date field
    FOOTER = "ftr"                 # Footer text
    SLIDE_NUMBER = "sldNum"        # Slide number field
    CHART = "chart"                # Chart/graph
    TABLE = "tbl"                  # Table
    MEDIA = "media"                # Media (video/audio)
    OBJECT = "obj"                 # Generic object


class PlaceholderSize(Enum):
    """Enumeration of PowerPoint placeholder sizes"""
    FULL = "full"                  # Full content area
    HALF = "half"                  # Half content area
    QUARTER = "quarter"            # Quarter content area
    CUSTOM = "custom"              # Custom dimensions


@dataclass
class TypographySettings:
    """Typography configuration for placeholders"""
    font_size: str = "1800"                # Size in hundredths of a point
    font_size_token: str = "${typography.body.size}"
    alignment: str = "l"                   # l=left, ctr=center, r=right, just=justify
    anchor: str = "t"                      # t=top, ctr=center, b=bottom
    bold: bool = False
    italic: bool = False
    bullet_style: str = "auto"             # auto, none, custom
    indent_level: int = 0                  # 0-9 indent levels
    margin_left: str = "0"                 # Left margin in EMU or token
    line_spacing: str = "100%"             # Line spacing percentage
    
    def to_ooxml_properties(self) -> Dict[str, Any]:
        """Convert to OOXML text properties"""
        props = {
            'size': self.font_size,
            'alignment': self.alignment,
            'anchor': self.anchor
        }
        
        if self.bold:
            props['bold'] = "1"
        if self.italic:
            props['italic'] = "1"
        if self.margin_left != "0":
            props['margin_left'] = self.margin_left
            
        return props


@dataclass
class ShapeProperties:
    """Shape configuration for placeholders"""
    no_group: bool = True                  # Prevent grouping
    no_select: bool = False                # Prevent selection
    no_resize: bool = False                # Prevent resizing
    no_move: bool = False                  # Prevent moving
    auto_fit: str = "none"                 # none, normal, shape
    fill_type: str = "none"                # none, solid, gradient, picture
    border_type: str = "none"              # none, solid, dashed
    border_width: str = "0"                # Border width in EMU
    shadow: bool = False                   # Drop shadow
    
    def to_ooxml_locks(self) -> Dict[str, str]:
        """Convert to OOXML shape locks"""
        locks = {}
        
        if self.no_group:
            locks['noGrp'] = "1"
        if self.no_select:
            locks['noSelect'] = "1"
        if self.no_resize:
            locks['noResize'] = "1"
        if self.no_move:
            locks['noMove'] = "1"
            
        return locks


@dataclass
class PlaceholderTemplate:
    """Complete placeholder template with all properties"""
    ph_type: PlaceholderType
    name: str
    size: PlaceholderSize
    position: ParameterizedPosition
    typography: TypographySettings = field(default_factory=TypographySettings)
    shape_properties: ShapeProperties = field(default_factory=ShapeProperties)
    index: int = 0
    required: bool = True                  # Required for layout type
    content_hint: str = ""                 # Hint text for users
    
    def generate_creation_id(self) -> str:
        """Generate Office creation ID"""
        return f"{{{str(uuid.uuid4()).upper()}}}"
    
    def to_layout_placeholder(self, index_override: Optional[int] = None) -> Dict[str, Any]:
        """Convert to layout placeholder format"""
        return {
            'id': f"{self.ph_type.value}_{self.index}",
            'name': self.name,
            'type': self.ph_type.value,
            'size': self.size.value,
            'index': index_override or self.index,
            'position': {
                'x': self.position.x,
                'y': self.position.y,
                'width': self.position.width,
                'height': self.position.height
            },
            'typography': self.typography.__dict__,
            'shape_properties': self.shape_properties.__dict__,
            'content_hint': self.content_hint
        }
    
    def to_ooxml_placeholder(self, shape_id: int) -> Dict[str, Any]:
        """Convert to OOXML placeholder format"""
        return {
            'shape_id': shape_id,
            'name': self.name,
            'creation_id': self.generate_creation_id(),
            'ph_type': self.ph_type.value,
            'size': self.size.value if self.size != PlaceholderSize.FULL else None,
            'index': self.index,
            'position': self.position,
            'typography': self.typography.to_ooxml_properties(),
            'shape_locks': self.shape_properties.to_ooxml_locks(),
            'auto_fit': self.shape_properties.auto_fit
        }


class PlaceholderFactory:
    """Factory for creating PowerPoint placeholder templates"""
    
    # Standard typography presets
    TYPOGRAPHY_PRESETS = {
        'title_large': TypographySettings(
            font_size="6000",
            font_size_token="${typography.title.size_large}",
            alignment="l",
            anchor="b",
            bold=False
        ),
        'title_standard': TypographySettings(
            font_size="4400",
            font_size_token="${typography.title.size}",
            alignment="l",
            anchor="b",
            bold=False
        ),
        'subtitle': TypographySettings(
            font_size="2400", 
            font_size_token="${typography.subtitle.size}",
            alignment="l",
            anchor="t",
            bold=False
        ),
        'body_text': TypographySettings(
            font_size="1800",
            font_size_token="${typography.body.size}",
            alignment="l",
            anchor="t",
            bullet_style="auto"
        ),
        'section_header': TypographySettings(
            font_size="6000",
            font_size_token="${typography.section_header.size}",
            alignment="l",
            anchor="b",
            bold=False
        ),
        'comparison_header': TypographySettings(
            font_size="2000",
            font_size_token="${typography.comparison_header.size}",
            alignment="l",
            anchor="b",
            bold=True
        ),
        'caption_text': TypographySettings(
            font_size="1600",
            font_size_token="${typography.caption.size}",
            alignment="l",
            anchor="t",
            bullet_style="none"
        ),
        'overlay_title': TypographySettings(
            font_size="4400",
            font_size_token="${typography.overlay_title.size}",
            alignment="r",
            anchor="b",
            bold=False
        ),
        'footer_text': TypographySettings(
            font_size="1200",
            font_size_token="${typography.footer.size}",
            alignment="l",
            anchor="t"
        )
    }
    
    # Standard shape presets
    SHAPE_PRESETS = {
        'standard': ShapeProperties(
            no_group=True,
            auto_fit="none"
        ),
        'title': ShapeProperties(
            no_group=True,
            auto_fit="normal"
        ),
        'body': ShapeProperties(
            no_group=True,
            auto_fit="normal"
        ),
        'picture': ShapeProperties(
            no_group=True,
            auto_fit="shape",
            fill_type="picture"
        ),
        'footer': ShapeProperties(
            no_group=True,
            auto_fit="none",
            no_resize=True
        )
    }
    
    @classmethod
    def create_title_placeholder(
        cls,
        name: str,
        position: ParameterizedPosition,
        typography_preset: str = 'title_standard',
        index: int = 0
    ) -> PlaceholderTemplate:
        """Create title placeholder"""
        return PlaceholderTemplate(
            ph_type=PlaceholderType.TITLE,
            name=name,
            size=PlaceholderSize.FULL,
            position=position,
            typography=cls.TYPOGRAPHY_PRESETS[typography_preset],
            shape_properties=cls.SHAPE_PRESETS['title'],
            index=index,
            content_hint="Click to edit Master title style"
        )
    
    @classmethod
    def create_center_title_placeholder(
        cls,
        name: str,
        position: ParameterizedPosition,
        index: int = 0
    ) -> PlaceholderTemplate:
        """Create center title placeholder (title slide)"""
        return PlaceholderTemplate(
            ph_type=PlaceholderType.CENTER_TITLE,
            name=name,
            size=PlaceholderSize.FULL,
            position=position,
            typography=cls.TYPOGRAPHY_PRESETS['title_large'],
            shape_properties=cls.SHAPE_PRESETS['title'],
            index=index,
            content_hint="Click to edit Master title style"
        )
    
    @classmethod
    def create_subtitle_placeholder(
        cls,
        name: str,
        position: ParameterizedPosition,
        index: int = 1
    ) -> PlaceholderTemplate:
        """Create subtitle placeholder"""
        return PlaceholderTemplate(
            ph_type=PlaceholderType.SUB_TITLE,
            name=name,
            size=PlaceholderSize.FULL,
            position=position,
            typography=cls.TYPOGRAPHY_PRESETS['subtitle'],
            shape_properties=cls.SHAPE_PRESETS['standard'],
            index=index,
            content_hint="Click to edit Master subtitle style"
        )
    
    @classmethod
    def create_body_placeholder(
        cls,
        name: str,
        position: ParameterizedPosition,
        size: PlaceholderSize = PlaceholderSize.FULL,
        index: int = 1
    ) -> PlaceholderTemplate:
        """Create body/content placeholder"""
        return PlaceholderTemplate(
            ph_type=PlaceholderType.BODY,
            name=name,
            size=size,
            position=position,
            typography=cls.TYPOGRAPHY_PRESETS['body_text'],
            shape_properties=cls.SHAPE_PRESETS['body'],
            index=index,
            content_hint="Click to edit Master text styles"
        )
    
    @classmethod
    def create_picture_placeholder(
        cls,
        name: str,
        position: ParameterizedPosition,
        size: PlaceholderSize = PlaceholderSize.HALF,
        index: int = 1
    ) -> PlaceholderTemplate:
        """Create picture placeholder"""
        return PlaceholderTemplate(
            ph_type=PlaceholderType.PICTURE,
            name=name,
            size=size,
            position=position,
            typography=TypographySettings(),  # Pictures don't need typography
            shape_properties=cls.SHAPE_PRESETS['picture'],
            index=index,
            content_hint="Click icon to add picture"
        )
    
    @classmethod
    def create_footer_placeholder(
        cls,
        ph_type: PlaceholderType,
        name: str,
        position: ParameterizedPosition,
        index: int
    ) -> PlaceholderTemplate:
        """Create footer placeholder (date, footer, slide number)"""
        content_hints = {
            PlaceholderType.DATE: "Date will appear here",
            PlaceholderType.FOOTER: "Footer text",
            PlaceholderType.SLIDE_NUMBER: "Slide number will appear here"
        }
        
        return PlaceholderTemplate(
            ph_type=ph_type,
            name=name,
            size=PlaceholderSize.QUARTER,
            position=position,
            typography=cls.TYPOGRAPHY_PRESETS['footer_text'],
            shape_properties=cls.SHAPE_PRESETS['footer'],
            index=index,
            required=False,
            content_hint=content_hints.get(ph_type, "")
        )


class StandardPlaceholderSets:
    """Pre-defined placeholder sets for common layout patterns"""
    
    @staticmethod
    def create_standard_footer_set() -> List[PlaceholderTemplate]:
        """Create standard footer placeholder set (date, footer, slide number)"""
        return [
            PlaceholderFactory.create_footer_placeholder(
                PlaceholderType.DATE,
                "Date Placeholder",
                ParameterizedPosition(
                    x="${margins.left}",
                    y="${slide.height - margins.bottom}",
                    width="${slide.width * 0.354}",
                    height="${slide.height * 0.070}"
                ),
                index=10
            ),
            PlaceholderFactory.create_footer_placeholder(
                PlaceholderType.FOOTER,
                "Footer Placeholder",
                ParameterizedPosition(
                    x="${slide.width * 0.5}",
                    y="${slide.height - margins.bottom}",
                    width="${slide.width * 0.25}",
                    height="${slide.height * 0.070}"
                ),
                index=11
            ),
            PlaceholderFactory.create_footer_placeholder(
                PlaceholderType.SLIDE_NUMBER,
                "Slide Number Placeholder",
                ParameterizedPosition(
                    x="${slide.width * 0.75}",
                    y="${slide.height - margins.bottom}",
                    width="${slide.width * 0.167}",
                    height="${slide.height * 0.070}"
                ),
                index=12
            )
        ]
    
    @staticmethod
    def create_title_slide_set() -> List[PlaceholderTemplate]:
        """Create title slide placeholder set"""
        placeholders = [
            PlaceholderFactory.create_center_title_placeholder(
                "Title 1",
                ParameterizedPosition(
                    x="${margins.left}",
                    y="${slide.height * 0.218}",
                    width="${content_areas.full_width}",
                    height="${slide.height * 0.464}"
                ),
                index=0
            ),
            PlaceholderFactory.create_subtitle_placeholder(
                "Subtitle 2",
                ParameterizedPosition(
                    x="${margins.left}",
                    y="${slide.height * 0.700}",
                    width="${content_areas.full_width}",
                    height="${slide.height * 0.210}"
                ),
                index=1
            )
        ]
        placeholders.extend(StandardPlaceholderSets.create_standard_footer_set())
        return placeholders
    
    @staticmethod
    def create_title_content_set() -> List[PlaceholderTemplate]:
        """Create title and content placeholder set"""
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
                    width="${content_areas.full_width}",
                    height="${slide.height - margins.top - margins.bottom - slide.height * 0.258 - gutters.vertical * 2}"
                ),
                index=1
            )
        ]
        placeholders.extend(StandardPlaceholderSets.create_standard_footer_set())
        return placeholders
    
    @staticmethod
    def create_two_content_set() -> List[PlaceholderTemplate]:
        """Create two content placeholder set"""
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
                    width="${content_areas.half_width}",
                    height="${slide.height - margins.top - margins.bottom - slide.height * 0.258 - gutters.vertical * 2}"
                ),
                size=PlaceholderSize.HALF,
                index=1
            ),
            PlaceholderFactory.create_body_placeholder(
                "Content Placeholder 3",
                ParameterizedPosition(
                    x="${margins.left + content_areas.half_width + gutters.horizontal}",
                    y="${margins.top + slide.height * 0.258 + gutters.vertical}",
                    width="${content_areas.half_width}",
                    height="${slide.height - margins.top - margins.bottom - slide.height * 0.258 - gutters.vertical * 2}"
                ),
                size=PlaceholderSize.HALF,
                index=2
            )
        ]
        placeholders.extend(StandardPlaceholderSets.create_standard_footer_set())
        return placeholders
    
    @staticmethod
    def create_picture_caption_set() -> List[PlaceholderTemplate]:
        """Create picture with caption placeholder set"""
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
            PlaceholderFactory.create_picture_placeholder(
                "Picture Placeholder 2",
                ParameterizedPosition(
                    x="${margins.left}",
                    y="${margins.top + slide.height * 0.258 + gutters.vertical}",
                    width="${content_areas.half_width + gutters.horizontal * 0.2}",
                    height="${slide.height - margins.top - margins.bottom - slide.height * 0.258 - gutters.vertical * 2}"
                ),
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
                shape_properties=PlaceholderFactory.SHAPE_PRESETS['body'],
                index=2,
                content_hint="Click to add caption text"
            )
        ]
        placeholders.extend(StandardPlaceholderSets.create_standard_footer_set())
        return placeholders


def get_placeholder_template_by_type(
    ph_type: PlaceholderType,
    name: str,
    position: ParameterizedPosition,
    **kwargs
) -> PlaceholderTemplate:
    """Get placeholder template by type with default settings"""
    
    if ph_type == PlaceholderType.CENTER_TITLE:
        return PlaceholderFactory.create_center_title_placeholder(name, position, **kwargs)
    elif ph_type == PlaceholderType.TITLE:
        return PlaceholderFactory.create_title_placeholder(name, position, **kwargs)
    elif ph_type == PlaceholderType.SUB_TITLE:
        return PlaceholderFactory.create_subtitle_placeholder(name, position, **kwargs)
    elif ph_type == PlaceholderType.BODY:
        return PlaceholderFactory.create_body_placeholder(name, position, **kwargs)
    elif ph_type == PlaceholderType.PICTURE:
        return PlaceholderFactory.create_picture_placeholder(name, position, **kwargs)
    elif ph_type in [PlaceholderType.DATE, PlaceholderType.FOOTER, PlaceholderType.SLIDE_NUMBER]:
        return PlaceholderFactory.create_footer_placeholder(ph_type, name, position, **kwargs)
    else:
        # Generic placeholder for other types
        return PlaceholderTemplate(
            ph_type=ph_type,
            name=name,
            size=kwargs.get('size', PlaceholderSize.FULL),
            position=position,
            index=kwargs.get('index', 0)
        )


if __name__ == '__main__':
    # Demo usage
    print("🎯 PowerPoint Placeholder Types Demo")
    
    # Test placeholder creation
    title_pos = ParameterizedPosition("${margins.left}", "${margins.top}", "${content_areas.full_width}", "${slide.height * 0.258}")
    title_placeholder = PlaceholderFactory.create_title_placeholder("Demo Title", title_pos)
    
    print(f"\n📝 Created title placeholder:")
    print(f"   Type: {title_placeholder.ph_type.value}")
    print(f"   Name: {title_placeholder.name}")
    print(f"   Typography: {title_placeholder.typography.font_size} pt, {title_placeholder.typography.alignment} aligned")
    print(f"   Content hint: {title_placeholder.content_hint}")
    
    # Test standard sets
    print(f"\n🎨 Standard placeholder sets:")
    title_slide_set = StandardPlaceholderSets.create_title_slide_set()
    print(f"   Title slide: {len(title_slide_set)} placeholders")
    
    two_content_set = StandardPlaceholderSets.create_two_content_set()
    print(f"   Two content: {len(two_content_set)} placeholders")
    
    picture_set = StandardPlaceholderSets.create_picture_caption_set()
    print(f"   Picture caption: {len(picture_set)} placeholders")
    
    # Test OOXML conversion
    ooxml_placeholder = title_placeholder.to_ooxml_placeholder(2)
    print(f"\n🔧 OOXML conversion:")
    print(f"   Shape ID: {ooxml_placeholder['shape_id']}")
    print(f"   Creation ID: {ooxml_placeholder['creation_id']}")
    print(f"   Typography props: {len(ooxml_placeholder['typography'])} properties")
    print(f"   Shape locks: {len(ooxml_placeholder['shape_locks'])} locks")