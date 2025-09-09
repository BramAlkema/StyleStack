# Word (.dotx) OOXML Primitives

## Core Design Token Mappings

### Typography
| Design Token | OOXML Primitive | XPath Target | Example |
|--------------|-----------------|--------------|---------|
| `typography.font.primary` | `<w:rFonts w:ascii=""/>` | `//w:rFonts/@w:ascii` | `Liberation Sans` |
| `typography.font.heading` | `<w:rFonts w:hAnsi=""/>` | `//w:rFonts/@w:hAnsi` | `Liberation Sans` |
| `typography.size.body` | `<w:sz w:val=""/>` | `//w:sz/@w:val` | `24` (12pt) |
| `typography.size.heading` | `<w:sz w:val=""/>` | `//w:style[@w:styleId='Heading']//w:sz/@w:val` | `28` (14pt) |
| `typography.weight.bold` | `<w:b/>` | `//w:b` | Present |

### Spacing & Layout
| Design Token | OOXML Primitive | XPath Target | Example |
|--------------|-----------------|--------------|---------|
| `spacing.line.height` | `<w:spacing w:line=""/>` | `//w:spacing/@w:line` | `17` |
| `spacing.paragraph.before` | `<w:spacing w:before=""/>` | `//w:spacing/@w:before` | `85` |
| `spacing.paragraph.after` | `<w:spacing w:after=""/>` | `//w:spacing/@w:after` | `34` |

### Colors
| Design Token | OOXML Primitive | XPath Target | Example |
|--------------|-----------------|--------------|---------|
| `color.text.primary` | `<w:color w:val=""/>` | `//w:color/@w:val` | `000000` |
| `color.highlight` | `<w:highlight w:val=""/>` | `//w:highlight/@w:val` | `yellow` |

## OOXML Structure Examples

### Document Defaults (styles.xml)
```xml
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="{{typography.font.body}}" 
                  w:hAnsi="{{typography.font.body}}" 
                  w:cs="{{typography.font.body}}"/>
        <w:sz w:val="{{typography.size.body}}"/>
        <w:szCs w:val="{{typography.size.body}}"/>
        <w:lang w:val="en-US"/>
      </w:rPr>
    </w:rPrDefault>
    <w:pPrDefault>
      <w:spacing w:line="{{spacing.line.height}}" w:lineRule="exact"/>
    </w:pPrDefault>
  </w:docDefaults>
</w:styles>
```

### Paragraph Styles with Inheritance
```xml
<!-- Base Standard style -->
<w:style w:type="paragraph" w:default="1" w:styleId="Standard">
  <w:name w:val="Standard"/>
  <w:qFormat/>
  <w:pPr>
    <w:spacing w:line="{{spacing.line.height}}" w:lineRule="exact"/>
  </w:pPr>
  <w:rPr>
    <w:rFonts w:ascii="{{typography.font.body}}" 
              w:hAnsi="{{typography.font.body}}"/>
    <w:sz w:val="{{typography.size.body}}"/>
    <w:szCs w:val="{{typography.size.body}}"/>
  </w:rPr>
</w:style>

<!-- Heading inherits from Standard -->
<w:style w:type="paragraph" w:styleId="Heading">
  <w:name w:val="Heading"/>
  <w:basedOn w:val="Standard"/>
  <w:next w:val="Text_body"/>
  <w:qFormat/>
  <w:pPr>
    <w:spacing w:before="{{spacing.heading.before}}" 
               w:after="{{spacing.heading.after}}" 
               w:line="{{spacing.heading.line}}" 
               w:lineRule="exact"/>
    <w:keepNext/>
  </w:pPr>
  <w:rPr>
    <w:rFonts w:ascii="{{typography.font.heading}}" 
              w:hAnsi="{{typography.font.heading}}"/>
    <w:sz w:val="{{typography.size.heading}}"/>
    <w:szCs w:val="{{typography.size.heading}}"/>
  </w:rPr>
</w:style>
```

### Document Content (document.xml)
```xml
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:pPr>
        <w:pStyle w:val="Heading"/>
      </w:pPr>
      <w:r>
        <w:t>{{content.title}}</w:t>
      </w:r>
    </w:p>
    
    <w:p>
      <w:pPr>
        <w:pStyle w:val="Text_body"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:color w:val="{{color.text.body}}"/>
        </w:rPr>
        <w:t>{{content.body}}</w:t>
      </w:r>
    </w:p>
  </w:body>
</w:document>
```

### Table Styles
```xml
<w:style w:type="table" w:default="1" w:styleId="TableNormal">
  <w:name w:val="Normal Table"/>
  <w:uiPriority w:val="99"/>
  <w:tblPr>
    <w:tblCellMar>
      <w:top w:w="{{spacing.table.cell.top}}" w:type="dxa"/>
      <w:left w:w="{{spacing.table.cell.left}}" w:type="dxa"/>
      <w:bottom w:w="{{spacing.table.cell.bottom}}" w:type="dxa"/>
      <w:right w:w="{{spacing.table.cell.right}}" w:type="dxa"/>
    </w:tblCellMar>
  </w:tblPr>
</w:style>
```

## XPath Targeting Patterns

### Typography Manipulation
```xpath
# Font families
//w:rFonts/@w:ascii
//w:rFonts/@w:hAnsi
//w:rFonts/@w:cs

# Font sizes (in half-points)
//w:sz/@w:val
//w:szCs/@w:val

# Font formatting
//w:b          # Bold
//w:i          # Italic
//w:u/@w:val   # Underline
```

### Paragraph Formatting
```xpath
# Paragraph styles
//w:pStyle/@w:val

# Spacing
//w:spacing/@w:line     # Line height
//w:spacing/@w:before   # Space before
//w:spacing/@w:after    # Space after

# Alignment
//w:jc/@w:val          # Justification
```

### Style Hierarchy
```xpath
# Style definitions
//w:style[@w:type='paragraph']
//w:style[@w:type='character']
//w:style[@w:type='table']

# Style inheritance
//w:basedOn/@w:val      # Parent style
//w:next/@w:val         # Next paragraph style
```

## Design Token Integration

### Patch Operations for Word
```json
[
  {
    "operation": "set",
    "target": "//w:rFonts/@w:ascii",
    "value": "{{tokens.typography.font.primary}}"
  },
  {
    "operation": "set",
    "target": "//w:style[@w:styleId='Heading']//w:sz/@w:val",
    "value": "{{tokens.typography.size.heading}}"
  },
  {
    "operation": "set",
    "target": "//w:spacing/@w:line",
    "value": "{{tokens.spacing.line.height}}"
  },
  {
    "operation": "set",
    "target": "//w:color/@w:val",
    "value": "{{tokens.color.text.primary}}"
  }
]
```

### Style Inheritance Chain
1. **Document Defaults** (`w:docDefaults`) - Foundation settings
2. **Named Styles** (`w:style`) - Reusable style definitions
3. **Paragraph Properties** (`w:pPr`) - Paragraph-level overrides
4. **Run Properties** (`w:rPr`) - Character-level overrides

### Common Word Elements
- **Paragraphs**: `//w:p` - Text paragraph containers
- **Text Runs**: `//w:r` - Individual formatting units
- **Text Content**: `//w:t` - Actual text content
- **Style References**: `//w:pStyle` - Style application
- **Tables**: `//w:tbl` - Table structures
- **Headers/Footers**: `//w:hdr`, `//w:ftr` - Page headers and footers

## Professional Typography Features

### LibreOffice-Inspired Defaults
- **Base Font**: Liberation Sans (open source, professional)
- **Font Size**: 12pt body, 14pt headings
- **Line Height**: Exact spacing for consistent grids
- **Kerning**: Enabled for improved readability

### Semantic Style Hierarchy
- **Standard** - Base paragraph style
- **Heading** - Primary heading style
- **Text body** - Body text with spacing
- **List** - List item formatting
- **Caption** - Figure/table captions