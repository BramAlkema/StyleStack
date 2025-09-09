# PowerPoint (.potx) OOXML Primitives

## Core Design Token Mappings

### Colors
| Design Token | OOXML Primitive | XPath Target | Example |
|--------------|-----------------|--------------|---------|
| `color.primary` | `<a:srgbClr val=""/>` | `//a:srgbClr[@val]/@val` | `0EA5E9` |
| `color.text.primary` | `<a:schemeClr val="dk1"/>` | `//a:schemeClr[@val='dk1']/@val` | `dk1` |
| `color.background` | `<a:schemeClr val="lt1"/>` | `//a:schemeClr[@val='lt1']/@val` | `lt1` |
| `color.accent.1` | `<a:srgbClr val=""/>` | `//a:accent1/a:srgbClr/@val` | `0EA5E9` |

### Typography
| Design Token | OOXML Primitive | XPath Target | Example |
|--------------|-----------------|--------------|---------|
| `typography.font.primary` | `<a:latin typeface=""/>` | `//a:latin/@typeface` | `Inter` |
| `typography.size.body` | `<a:defRPr sz=""/>` | `//a:defRPr/@sz` | `2400` (24pt) |
| `typography.weight.bold` | `<a:defRPr b="1"/>` | `//a:defRPr[@b]` | `1` |

### Layout
| Design Token | OOXML Primitive | XPath Target | Example |
|--------------|-----------------|--------------|---------|
| `layout.slide.width` | `<p:sldSz cx=""/>` | `//p:sldSz/@cx` | `7772400` (A4 width) |
| `layout.slide.height` | `<p:sldSz cy=""/>` | `//p:sldSz/@cy` | `10986120` (A4 height) |

## OOXML Structure Examples

### Theme Definition (theme1.xml)
```xml
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="StyleStack Clean">
  <a:themeElements>
    <a:clrScheme name="StyleStack">
      <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
      <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
      <a:accent1><a:srgbClr val="{{color.primary}}"/></a:accent1>
      <a:accent2><a:srgbClr val="{{color.secondary}}"/></a:accent2>
    </a:clrScheme>
    
    <a:fontScheme name="StyleStack Typography">
      <a:majorFont>
        <a:latin typeface="{{typography.font.primary}}" pitchFamily="34" charset="0"/>
      </a:majorFont>
      <a:minorFont>
        <a:latin typeface="{{typography.font.body}}" pitchFamily="34" charset="0"/>
      </a:minorFont>
    </a:fontScheme>
  </a:themeElements>
</a:theme>
```

### Presentation Structure (presentation.xml)
```xml
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <!-- Slide dimensions controlled by design tokens -->
  <p:sldSz cx="{{layout.slide.width}}" cy="{{layout.slide.height}}" type="custom"/>
  
  <!-- Default typography -->
  <p:defaultTextStyle>
    <a:defPPr>
      <a:defRPr lang="en-US" sz="{{typography.size.body}}" kern="1200">
        <a:solidFill>
          <a:schemeClr val="tx1"/>
        </a:solidFill>
        <a:latin typeface="{{typography.font.body}}"/>
      </a:defRPr>
    </a:defPPr>
  </p:defaultTextStyle>
</p:presentation>
```

### Slide Content Structure (slide1.xml)
```xml
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:sp>
        <p:txBody>
          <a:p>
            <a:r>
              <a:rPr lang="en-US" sz="{{typography.size.heading}}">
                <a:solidFill>
                  <a:srgbClr val="{{color.text.heading}}"/>
                </a:solidFill>
                <a:latin typeface="{{typography.font.heading}}"/>
              </a:rPr>
              <a:t>{{content.title}}</a:t>
            </a:r>
          </a:p>
        </p:txBody>
      </p:sp>
    </p:spTree>
  </p:cSld>
</p:sld>
```

## XPath Targeting Patterns

### Color Manipulation
```xpath
# Direct color values
//a:srgbClr/@val
//a:accent1/a:srgbClr/@val
//a:solidFill/a:srgbClr/@val

# Theme color references
//a:schemeClr/@val
//a:solidFill/a:schemeClr/@val
```

### Typography Manipulation
```xpath
# Font families
//a:latin/@typeface
//a:majorFont/a:latin/@typeface
//a:minorFont/a:latin/@typeface

# Font sizes (in half-points)
//a:defRPr/@sz
//a:rPr/@sz

# Font weights
//a:defRPr[@b='1']
//a:rPr[@b='1']
```

### Layout Manipulation
```xpath
# Slide dimensions (in EMUs: English Metric Units)
//p:sldSz/@cx  # Width
//p:sldSz/@cy  # Height

# Text positioning
//p:sp/p:spPr/a:xfrm/a:off/@x
//p:sp/p:spPr/a:xfrm/a:off/@y
```

## Design Token Integration

### Patch Operations for PowerPoint
```json
[
  {
    "operation": "set",
    "target": "//a:accent1/a:srgbClr/@val",
    "value": "{{tokens.color.primary}}"
  },
  {
    "operation": "set", 
    "target": "//a:latin/@typeface",
    "value": "{{tokens.typography.font.primary}}"
  },
  {
    "operation": "set",
    "target": "//p:sldSz/@cx",
    "value": "{{tokens.layout.slide.width}}"
  }
]
```

### Common PowerPoint Elements
- **Shapes**: `//p:sp` - Text boxes, shapes, placeholders
- **Text Runs**: `//a:r` - Individual text formatting units
- **Paragraphs**: `//a:p` - Text paragraph containers
- **Theme Elements**: `//a:themeElements` - Global theme definitions
- **Master Elements**: `//p:sldMaster` - Slide master definitions