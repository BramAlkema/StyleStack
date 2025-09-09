# Excel (.xltx) OOXML Primitives

## Core Design Token Mappings

### Typography
| Design Token | OOXML Primitive | XPath Target | Example |
|--------------|-----------------|--------------|---------|
| `typography.font.primary` | `<name val=""/>` | `//font/name/@val` | `Liberation Sans` |
| `typography.size.body` | `<sz val=""/>` | `//font/sz/@val` | `10` |
| `typography.size.heading` | `<sz val=""/>` | `//font[3]/sz/@val` | `18` |
| `typography.weight.bold` | `<b/>` | `//font/b` | Present |

### Colors
| Design Token | OOXML Primitive | XPath Target | Example |
|--------------|-----------------|--------------|---------|
| `color.text.primary` | `<color rgb=""/>` | `//font/color/@rgb` | `FF000000` |
| `color.background.good` | `<fgColor rgb=""/>` | `//fill[3]/patternFill/fgColor/@rgb` | `FFCCFFCC` |
| `color.background.warning` | `<fgColor rgb=""/>` | `//fill[4]/patternFill/fgColor/@rgb` | `FFFFFFCC` |
| `color.background.error` | `<fgColor rgb=""/>` | `//fill[5]/patternFill/fgColor/@rgb` | `FFCC0000` |

### Cell Formatting
| Design Token | OOXML Primitive | XPath Target | Example |
|--------------|-----------------|--------------|---------|
| `border.style.thin` | `<border><left style=""/>` | `//border/left/@style` | `thin` |
| `cell.alignment.horizontal` | `<alignment horizontal=""/>` | `//alignment/@horizontal` | `general` |
| `cell.alignment.vertical` | `<alignment vertical=""/>` | `//alignment/@vertical` | `bottom` |

## OOXML Structure Examples

### Font Definitions (styles.xml)
```xml
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="6">
    <!-- Default font -->
    <font>
      <sz val="{{typography.size.body}}"/>
      <name val="{{typography.font.primary}}"/>
      <family val="2"/>
    </font>
    
    <!-- Bold variant -->
    <font>
      <sz val="{{typography.size.body}}"/>
      <name val="{{typography.font.primary}}"/>
      <family val="2"/>
      <b/>
    </font>
    
    <!-- Heading font -->
    <font>
      <sz val="{{typography.size.heading}}"/>
      <name val="{{typography.font.heading}}"/>
      <family val="2"/>
      <b/>
    </font>
    
    <!-- Status fonts -->
    <font>
      <sz val="{{typography.size.body}}"/>
      <name val="{{typography.font.primary}}"/>
      <family val="2"/>
      <color rgb="{{color.status.success}}"/>
    </font>
  </fonts>
</styleSheet>
```

### Fill Patterns and Colors
```xml
<fills count="8">
  <!-- Default fills -->
  <fill><patternFill patternType="none"/></fill>
  <fill><patternFill patternType="gray125"/></fill>
  
  <!-- Status-based fills -->
  <fill>
    <patternFill patternType="solid">
      <fgColor rgb="{{color.status.success.background}}"/>
    </patternFill>
  </fill>
  <fill>
    <patternFill patternType="solid">
      <fgColor rgb="{{color.status.warning.background}}"/>
    </patternFill>
  </fill>
  <fill>
    <patternFill patternType="solid">
      <fgColor rgb="{{color.status.error.background}}"/>
    </patternFill>
  </fill>
  
  <!-- Brand accent fills -->
  <fill>
    <patternFill patternType="solid">
      <fgColor rgb="{{color.brand.primary}}"/>
    </patternFill>
  </fill>
</fills>
```

### Border Definitions
```xml
<borders count="2">
  <border/>
  <border>
    <left style="{{border.style.default}}"/>
    <right style="{{border.style.default}}"/>
    <top style="{{border.style.default}}"/>
    <bottom style="{{border.style.default}}"/>
  </border>
</borders>
```

### Cell Format Definitions
```xml
<cellXfs count="8">
  <!-- Default format -->
  <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
  
  <!-- Heading formats -->
  <xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="true"/>
  
  <!-- Status formats -->
  <xf numFmtId="0" fontId="4" fillId="2" borderId="0" xfId="0" 
      applyFont="true" applyFill="true"/>
  <xf numFmtId="0" fontId="0" fillId="3" borderId="0" xfId="0" 
      applyFill="true"/>
  <xf numFmtId="0" fontId="5" fillId="4" borderId="0" xfId="0" 
      applyFont="true" applyFill="true"/>
</cellXfs>
```

### Named Cell Styles
```xml
<cellStyles count="7">
  <cellStyle name="Normal" xfId="0" builtinId="0"/>
  <cellStyle name="Heading" xfId="1" builtinId="16"/>
  <cellStyle name="Heading 1" xfId="2"/>
  <cellStyle name="Heading 2" xfId="3"/>
  <cellStyle name="Good" xfId="4"/>
  <cellStyle name="Warning" xfId="5"/>
  <cellStyle name="Bad" xfId="6"/>
</cellStyles>
```

### Worksheet Content (sheet1.xml)
```xml
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    <row r="1">
      <c r="A1" s="1" t="inlineStr">
        <is><t>{{content.heading}}</t></is>
      </c>
    </row>
    <row r="2">
      <c r="A2" s="0" t="inlineStr">
        <is><t>{{content.body}}</t></is>
      </c>
    </row>
    <row r="3">
      <c r="A3" s="4" t="inlineStr">
        <is><t>{{content.status.success}}</t></is>
      </c>
    </row>
  </sheetData>
</worksheet>
```

## XPath Targeting Patterns

### Font Manipulation
```xpath
# Font properties
//font/name/@val          # Font family
//font/sz/@val             # Font size
//font/color/@rgb          # Font color
//font/b                   # Bold formatting
//font/i                   # Italic formatting

# Specific font targeting
//font[1]/name/@val        # First font definition
//font[position()=2]/sz/@val  # Second font size
```

### Fill and Background Colors
```xpath
# Solid fills
//fill/patternFill[@patternType='solid']/fgColor/@rgb

# Specific fill targeting
//fill[3]/patternFill/fgColor/@rgb  # Third fill definition
//fills/fill[position()=4]          # Fourth fill element
```

### Cell Format Targeting
```xpath
# Cell format references
//cellXfs/xf/@fontId       # Font reference
//cellXfs/xf/@fillId       # Fill reference
//cellXfs/xf/@borderId     # Border reference

# Alignment properties
//xf/alignment/@horizontal
//xf/alignment/@vertical
```

### Border Formatting
```xpath
# Border styles
//border/left/@style
//border/right/@style
//border/top/@style
//border/bottom/@style

# Border colors
//border/left/color/@rgb
//border/right/color/@rgb
```

## Design Token Integration

### Patch Operations for Excel
```json
[
  {
    "operation": "set",
    "target": "//font/name/@val",
    "value": "{{tokens.typography.font.primary}}"
  },
  {
    "operation": "set",
    "target": "//font[3]/sz/@val",
    "value": "{{tokens.typography.size.heading}}"
  },
  {
    "operation": "set",
    "target": "//fill[3]/patternFill/fgColor/@rgb",
    "value": "{{tokens.color.status.success.background}}"
  },
  {
    "operation": "set",
    "target": "//border/left/@style",
    "value": "{{tokens.border.style.default}}"
  }
]
```

### Excel Format Architecture

#### Font System
1. **Font Definitions** - Reusable font configurations
2. **Font References** - Cell formats point to font IDs
3. **Inheritance** - Fonts can share properties with variants

#### Fill System
1. **Pattern Types** - `none`, `solid`, `gray125`, etc.
2. **Color Definitions** - Foreground and background colors
3. **Status Colors** - Semantic color meanings (good/warning/bad)

#### Style Application Chain
1. **Cell Format** (`cellXfs`) - Combines font, fill, border
2. **Named Styles** (`cellStyles`) - User-friendly style names
3. **Cell Application** - Worksheet cells reference format IDs

## Semantic Color System

### Status-Based Colors
- **Good/Success** - Green backgrounds and text (`#CCFFCC`, `#006600`)
- **Warning/Caution** - Yellow backgrounds (`#FFFFCC`)
- **Error/Danger** - Red backgrounds and white text (`#CC0000`, `#FFFFFF`)

### Professional Typography
- **Base Font**: Liberation Sans (OpenOffice compatibility)
- **Size Hierarchy**: 10pt body, 18pt major headings, 12pt subheadings
- **Font Weights**: Regular and bold variants
- **Color System**: High contrast for accessibility

### Brand Integration Points
- **Accent Colors** - Primary brand colors in fills
- **Typography** - Brand font families
- **Status Colors** - Brand-aligned semantic colors
- **Border Styles** - Consistent line weights and styles

## Common Excel Elements
- **Worksheets**: `//worksheet` - Individual sheet content
- **Cells**: `//c` - Individual cell elements
- **Rows**: `//row` - Row containers
- **Cell Values**: `//v`, `//is/t` - Cell content
- **Formulas**: `//f` - Excel formulas
- **Charts**: External chart files referenced by worksheets