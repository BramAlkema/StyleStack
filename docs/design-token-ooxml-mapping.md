# Design Token → OOXML Primitive Mapping

## Universal Design Token Schema

### Typography Tokens
```json
{
  "typography": {
    "font": {
      "primary": "Inter",
      "heading": "Inter",
      "body": "Inter",
      "monospace": "SF Mono"
    },
    "size": {
      "xs": "10",
      "sm": "12", 
      "base": "14",
      "lg": "16",
      "xl": "18",
      "2xl": "24",
      "3xl": "32"
    },
    "weight": {
      "normal": "400",
      "medium": "500",
      "semibold": "600",
      "bold": "700"
    },
    "lineHeight": {
      "tight": "1.2",
      "normal": "1.4",
      "relaxed": "1.6"
    }
  }
}
```

### Color Tokens
```json
{
  "color": {
    "primary": "#0EA5E9",
    "secondary": "#8B5CF6", 
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "neutral": {
      "50": "#F9FAFB",
      "100": "#F3F4F6",
      "800": "#1F2937",
      "900": "#111827"
    },
    "text": {
      "primary": "#111827",
      "secondary": "#6B7280",
      "inverse": "#FFFFFF"
    },
    "background": {
      "primary": "#FFFFFF",
      "secondary": "#F9FAFB",
      "success": "#ECFDF5",
      "warning": "#FFFBEB",
      "danger": "#FEF2F2"
    }
  }
}
```

### Spacing Tokens
```json
{
  "spacing": {
    "xs": "4",
    "sm": "8",
    "base": "16", 
    "lg": "24",
    "xl": "32",
    "2xl": "48"
  }
}
```

## Format-Specific Mappings

### PowerPoint (.potx) Mapping
| Design Token | OOXML Target | XPath | Transform |
|--------------|--------------|-------|-----------|
| `typography.font.primary` | `<a:latin typeface=""/>` | `//a:latin/@typeface` | Direct |
| `typography.size.base` | `<a:defRPr sz=""/>` | `//a:defRPr/@sz` | `size * 100` (to half-points) |
| `color.primary` | `<a:accent1><a:srgbClr val=""/>` | `//a:accent1/a:srgbClr/@val` | Remove `#` prefix |
| `color.text.primary` | `<a:schemeClr val="dk1"/>` | `//a:schemeClr[@val='dk1']` | Map to theme color |
| `spacing.lg` | `<p:sldSz cx=""/>` | `//p:sldSz/@cx` | Convert to EMUs |

### Word (.dotx) Mapping  
| Design Token | OOXML Target | XPath | Transform |
|--------------|--------------|-------|-----------|
| `typography.font.primary` | `<w:rFonts w:ascii=""/>` | `//w:rFonts/@w:ascii` | Direct |
| `typography.size.base` | `<w:sz w:val=""/>` | `//w:sz/@w:val` | `size * 2` (to half-points) |
| `typography.lineHeight.normal` | `<w:spacing w:line=""/>` | `//w:spacing/@w:line` | `lineHeight * size * 2` |
| `color.text.primary` | `<w:color w:val=""/>` | `//w:color/@w:val` | Remove `#`, convert to RGB |
| `spacing.base` | `<w:spacing w:before=""/>` | `//w:spacing/@w:before` | Convert to DXA (twentieths of point) |

### Excel (.xltx) Mapping
| Design Token | OOXML Target | XPath | Transform |
|--------------|--------------|-------|-----------|
| `typography.font.primary` | `<name val=""/>` | `//font/name/@val` | Direct |
| `typography.size.base` | `<sz val=""/>` | `//font/sz/@val` | Direct (points) |
| `color.text.primary` | `<color rgb=""/>` | `//font/color/@rgb` | `FF` + remove `#` |
| `color.background.success` | `<fgColor rgb=""/>` | `//fill/patternFill/fgColor/@rgb` | `FF` + remove `#` |
| `color.primary` | `<fgColor rgb=""/>` | `//fill[6]/patternFill/fgColor/@rgb` | `FF` + remove `#` |

## Cross-Format Patch Generation

### Typography Patch Generator
```python
def generate_typography_patches(tokens):
    """Generate typography patches for all formats."""
    patches = {
        'powerpoint': [
            {
                "operation": "set",
                "target": "//a:latin/@typeface",
                "value": tokens['typography']['font']['primary']
            },
            {
                "operation": "set", 
                "target": "//a:defRPr/@sz",
                "value": str(int(tokens['typography']['size']['base']) * 100)
            }
        ],
        'word': [
            {
                "operation": "set",
                "target": "//w:rFonts/@w:ascii",
                "value": tokens['typography']['font']['primary']
            },
            {
                "operation": "set",
                "target": "//w:sz/@w:val", 
                "value": str(int(tokens['typography']['size']['base']) * 2)
            }
        ],
        'excel': [
            {
                "operation": "set",
                "target": "//font/name/@val",
                "value": tokens['typography']['font']['primary']
            },
            {
                "operation": "set",
                "target": "//font/sz/@val",
                "value": tokens['typography']['size']['base']
            }
        ]
    }
    return patches
```

### Color Patch Generator
```python
def generate_color_patches(tokens):
    """Generate color patches for all formats."""
    primary_color = tokens['color']['primary'].lstrip('#')
    text_color = tokens['color']['text']['primary'].lstrip('#')
    
    patches = {
        'powerpoint': [
            {
                "operation": "set",
                "target": "//a:accent1/a:srgbClr/@val",
                "value": primary_color
            },
            {
                "operation": "set",
                "target": "//a:solidFill/a:srgbClr/@val", 
                "value": text_color
            }
        ],
        'word': [
            {
                "operation": "set",
                "target": "//w:color/@w:val",
                "value": text_color
            }
        ],
        'excel': [
            {
                "operation": "set",
                "target": "//font/color/@rgb",
                "value": f"FF{text_color}"
            },
            {
                "operation": "set",
                "target": "//fill/patternFill/fgColor/@rgb",
                "value": f"FF{primary_color}"
            }
        ]
    }
    return patches
```

## Unit Conversion Utilities

### Typography Conversions
```python
def points_to_half_points(points):
    """Convert points to half-points (Word, PowerPoint sizes)."""
    return int(float(points) * 2)

def points_to_emu(points):
    """Convert points to EMUs (PowerPoint dimensions).""" 
    return int(float(points) * 12700)

def points_to_dxa(points):
    """Convert points to DXA/twentieths (Word spacing)."""
    return int(float(points) * 20)
```

### Color Conversions
```python
def hex_to_office_rgb(hex_color):
    """Convert hex to Office RGB format."""
    return hex_color.lstrip('#').upper()

def hex_to_excel_argb(hex_color):
    """Convert hex to Excel ARGB format."""
    return f"FF{hex_color.lstrip('#').upper()}"

def rgb_to_theme_color(rgb_value):
    """Map RGB values to Office theme color names."""
    theme_mapping = {
        '000000': 'dk1',    # Dark 1 (text)
        'FFFFFF': 'lt1',    # Light 1 (background)
        '1F2937': 'dk2',    # Dark 2
        'F9FAFB': 'lt2'     # Light 2
    }
    return theme_mapping.get(rgb_value.upper(), 'accent1')
```

## Validation Schema

### Design Token Validation
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StyleStack Design Tokens",
  "type": "object",
  "required": ["typography", "color", "spacing"],
  "properties": {
    "typography": {
      "type": "object",
      "required": ["font", "size"],
      "properties": {
        "font": {
          "type": "object",
          "properties": {
            "primary": {"type": "string", "minLength": 1},
            "heading": {"type": "string", "minLength": 1},
            "body": {"type": "string", "minLength": 1}
          }
        },
        "size": {
          "type": "object",
          "patternProperties": {
            "^(xs|sm|base|lg|xl|2xl|3xl)$": {
              "type": "string", 
              "pattern": "^[0-9]+$"
            }
          }
        }
      }
    },
    "color": {
      "type": "object",
      "properties": {
        "primary": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"},
        "secondary": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"}
      }
    }
  }
}
```

## Complete Integration Example

### StyleStack Template Processor
```python
class StyleStackProcessor:
    def __init__(self, design_tokens):
        self.tokens = design_tokens
        
    def process_template(self, template_path, output_path):
        """Apply design tokens to OOXML template."""
        format_type = self.detect_format(template_path)
        patches = self.generate_patches(format_type)
        
        handler = MultiFormatOOXMLHandler()
        result = handler.process_template(
            template_path=template_path,
            patches=patches,
            variables=self.tokens,
            metadata={'design_system': 'StyleStack'}
        )
        
        if result.success:
            shutil.move(result.output_path, output_path)
            
        return result
    
    def generate_patches(self, format_type):
        """Generate format-specific patches from design tokens."""
        generators = {
            'potx': self.generate_powerpoint_patches,
            'dotx': self.generate_word_patches, 
            'xltx': self.generate_excel_patches
        }
        
        generator = generators.get(format_type)
        if not generator:
            raise ValueError(f"Unsupported format: {format_type}")
            
        return generator()
```

This comprehensive mapping system enables StyleStack to:
1. **Universal Token Definition** - Single source of truth for design decisions
2. **Format-Specific Translation** - Automatic conversion to OOXML primitives
3. **Unit Conversion** - Handle different measurement systems across formats
4. **Validation** - Ensure token validity before processing
5. **Extensibility** - Easy addition of new formats and token types