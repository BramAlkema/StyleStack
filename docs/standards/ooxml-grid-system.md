# OOXML Universal Grid System Standard

## Core Constants

### Slide Dimensions (16:9)
- **Width**: 12,192,000 EMU (13.333")
- **Height**: 6,858,000 EMU (7.5")

### A4-Safe Content Box (10% margins)
- **Left**: 1,219,200 EMU
- **Top**: 685,800 EMU  
- **Width**: 9,753,600 EMU
- **Height**: 5,486,400 EMU

### 12-Column Grid System
- **Column Width**: 673,100 EMU
- **Gutter Width**: 152,400 EMU (~0.167")
- **Total Gutters**: 11 × 152,400 = 1,676,400 EMU
- **Total Columns**: 12 × 673,100 = 8,077,200 EMU

### Helper Functions
```
x(col) = 1,219,200 + (col-1) × (673,100 + 152,400)
width(N_cols) = N × 673,100 + (N-1) × 152,400
```

### Column Starting Positions
```
Col 1:  1,219,200 EMU
Col 2:  2,044,700 EMU
Col 3:  2,870,200 EMU
Col 4:  3,695,700 EMU
Col 5:  4,521,200 EMU
Col 6:  5,346,700 EMU
Col 7:  6,172,200 EMU
Col 8:  6,997,700 EMU
Col 9:  7,823,200 EMU
Col 10: 8,648,700 EMU
Col 11: 9,474,200 EMU
Col 12: 10,299,700 EMU
```

## PowerPoint Grid Implementation

### Master Slide Guides
```xml
<p:guideLst>
  <!-- Safe zone boundaries -->
  <p:guide orient="vert" pos="1219200"/>   <!-- Left margin -->
  <p:guide orient="vert" pos="10972800"/>  <!-- Right margin -->
  <p:guide orient="horz" pos="685800"/>    <!-- Top margin -->
  <p:guide orient="horz" pos="6172200"/>   <!-- Bottom margin -->
  
  <!-- 12-column grid -->
  <p:guide orient="vert" pos="1219200"/>   <!-- Col 1 -->
  <p:guide orient="vert" pos="2044700"/>   <!-- Col 2 -->
  <p:guide orient="vert" pos="2870200"/>   <!-- Col 3 -->
  <p:guide orient="vert" pos="3695700"/>   <!-- Col 4 -->
  <p:guide orient="vert" pos="4521200"/>   <!-- Col 5 -->
  <p:guide orient="vert" pos="5346700"/>   <!-- Col 6 -->
  <p:guide orient="vert" pos="6172200"/>   <!-- Col 7 -->
  <p:guide orient="vert" pos="6997700"/>   <!-- Col 8 -->
  <p:guide orient="vert" pos="7823200"/>   <!-- Col 9 -->
  <p:guide orient="vert" pos="8648700"/>   <!-- Col 10 -->
  <p:guide orient="vert" pos="9474200"/>   <!-- Col 11 -->
  <p:guide orient="vert" pos="10299700"/>  <!-- Col 12 -->
</p:guideLst>
```

### Standard Layout Patterns

#### Title Slide
- **Title**: Cols 2-11 (7,009,800 EMU wide)
- **Subtitle**: Cols 2-11, below title
- **Logo**: Cols 11-12, bottom-right

#### Title and Content
- **Title**: Cols 2-11, top
- **Content**: Cols 2-11, remaining height

#### Two Column
- **Title**: Cols 2-11
- **Left Content**: Cols 2-6 (3,175,500 EMU)
- **Right Content**: Cols 7-11 (3,175,500 EMU)

#### Comparison
- **Title**: Cols 2-11
- **Left Header**: Cols 2-6
- **Right Header**: Cols 7-11
- **Left Body**: Cols 2-6
- **Right Body**: Cols 7-11

#### Content with Caption
- **Title**: Cols 2-11
- **Visual**: Cols 2-8 (4,691,700 EMU)
- **Caption**: Cols 9-11 (2,134,100 EMU)

## Word Document Grid Implementation

### A4 Page Constants
- **Width**: 11,906,000 EMU (8.27")
- **Height**: 16,838,000 EMU (11.69")

### A4-Safe Content Box (Standard margins)
- **Left**: 1,440,000 EMU (1")
- **Top**: 1,440,000 EMU (1")
- **Right**: 1,440,000 EMU (1")
- **Bottom**: 1,440,000 EMU (1")
- **Content Width**: 9,026,000 EMU
- **Content Height**: 13,958,000 EMU

### 12-Column Grid for Word
```xml
<w:sectPr>
  <w:pgSz w:w="11906" w:h="16838" w:code="9"/> <!-- A4 -->
  <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>
  
  <!-- 12-column layout -->
  <w:cols w:num="12" w:sep="false">
    <w:col w:w="623"/>   <!-- Col 1 -->
    <w:col w:space="141" w:w="623"/>  <!-- Col 2 -->
    <w:col w:space="141" w:w="623"/>  <!-- Col 3 -->
    <w:col w:space="141" w:w="623"/>  <!-- Col 4 -->
    <w:col w:space="141" w:w="623"/>  <!-- Col 5 -->
    <w:col w:space="141" w:w="623"/>  <!-- Col 6 -->
    <w:col w:space="141" w:w="623"/>  <!-- Col 7 -->
    <w:col w:space="141" w:w="623"/>  <!-- Col 8 -->
    <w:col w:space="141" w:w="623"/>  <!-- Col 9 -->
    <w:col w:space="141" w:w="623"/>  <!-- Col 10 -->
    <w:col w:space="141" w:w="623"/>  <!-- Col 11 -->
    <w:col w:space="141" w:w="623"/>  <!-- Col 12 -->
  </w:cols>
</w:sectPr>
```

## Excel Spreadsheet Grid Implementation

### Standard Column Widths
```xml
<cols>
  <!-- 12-column grid mapped to Excel columns -->
  <col min="1" max="1" width="8.43" customWidth="1"/>   <!-- Margin -->
  <col min="2" max="2" width="11.29" customWidth="1"/>  <!-- Col 1 -->
  <col min="3" max="3" width="11.29" customWidth="1"/>  <!-- Col 2 -->
  <col min="4" max="4" width="11.29" customWidth="1"/>  <!-- Col 3 -->
  <col min="5" max="5" width="11.29" customWidth="1"/>  <!-- Col 4 -->
  <col min="6" max="6" width="11.29" customWidth="1"/>  <!-- Col 5 -->
  <col min="7" max="7" width="11.29" customWidth="1"/>  <!-- Col 6 -->
  <col min="8" max="8" width="11.29" customWidth="1"/>  <!-- Col 7 -->
  <col min="9" max="9" width="11.29" customWidth="1"/>  <!-- Col 8 -->
  <col min="10" max="10" width="11.29" customWidth="1"/> <!-- Col 9 -->
  <col min="11" max="11" width="11.29" customWidth="1"/> <!-- Col 10 -->
  <col min="12" max="12" width="11.29" customWidth="1"/> <!-- Col 11 -->
  <col min="13" max="13" width="11.29" customWidth="1"/> <!-- Col 12 -->
  <col min="14" max="14" width="8.43" customWidth="1"/>  <!-- Margin -->
</cols>
```

## Typography Baseline Grid

### Baseline Constants
- **Base Unit**: 411,520 EMU (18pt)
- **Minor Grid**: 205,760 EMU (9pt)
- **Major Grid**: 823,040 EMU (36pt)

### Font Size Scale (EMU)
```
Display:    914,400 EMU (72pt) - 2× Major
H1:         571,500 EMU (45pt) - 1.25× Major  
H2:         411,520 EMU (32pt) - 1× Major
H3:         308,640 EMU (24pt) - 0.75× Major
Body:       205,760 EMU (16pt) - 0.5× Major
Caption:    154,320 EMU (12pt) - 0.375× Major
```

### Vertical Rhythm
```xml
<!-- PowerPoint pseudo-baseline guides -->
<p:guideLst>
  <!-- Baseline grid at 18pt intervals -->
  <p:guide orient="horz" pos="685800"/>    <!-- Baseline 1 -->
  <p:guide orient="horz" pos="1097320"/>   <!-- Baseline 2 -->
  <p:guide orient="horz" pos="1508840"/>   <!-- Baseline 3 -->
  <p:guide orient="horz" pos="1920360"/>   <!-- Baseline 4 -->
  <p:guide orient="horz" pos="2331880"/>   <!-- Baseline 5 -->
  <p:guide orient="horz" pos="2743400"/>   <!-- Baseline 6 -->
  <p:guide orient="horz" pos="3154920"/>   <!-- Baseline 7 -->
  <p:guide orient="horz" pos="3566440"/>   <!-- Baseline 8 -->
  <p:guide orient="horz" pos="3977960"/>   <!-- Baseline 9 -->
  <p:guide orient="horz" pos="4389480"/>   <!-- Baseline 10 -->
  <p:guide orient="horz" pos="4801000"/>   <!-- Baseline 11 -->
  <p:guide orient="horz" pos="5212520"/>   <!-- Baseline 12 -->
  <p:guide orient="horz" pos="5624040"/>   <!-- Baseline 13 -->
  <p:guide orient="horz" pos="6035560"/>   <!-- Baseline 14 -->
</p:guideLst>
```

## Universal Grid Token System

```json
{
  "grid": {
    "columns": 12,
    "gutter_emu": 152400,
    "column_width_emu": 673100,
    "safe_zone": {
      "left_emu": 1219200,
      "top_emu": 685800,
      "width_emu": 9753600,
      "height_emu": 5486400
    },
    "baseline": {
      "unit_emu": 411520,
      "minor_emu": 205760,
      "major_emu": 823040
    }
  },
  
  "layouts": {
    "title_slide": {
      "title": {"cols": [2, 11], "baseline": [2, 4]},
      "subtitle": {"cols": [2, 11], "baseline": [5, 6]},
      "logo": {"cols": [11, 12], "baseline": [13, 14]}
    },
    "two_column": {
      "title": {"cols": [2, 11], "baseline": [1, 2]},
      "left": {"cols": [2, 6], "baseline": [3, 12]},
      "right": {"cols": [7, 11], "baseline": [3, 12]}
    }
  }
}
```

## Implementation Guidelines

### 1. Always Use Safe Zones
- 10% margins ensure content is never cut off
- Works for both screen (16:9) and print (A4)
- Professional appearance with breathing room

### 2. Snap to Grid
- All elements align to column boundaries
- Maintains visual rhythm and consistency
- Easier to create balanced layouts

### 3. Respect Baselines
- Text aligns to 18pt baseline grid
- Headers use major grid (36pt)
- Body text uses minor grid (9pt)

### 4. Responsive Scaling
- Grid proportions work at any size
- PDF export maintains alignment
- Print-safe at A4 dimensions

## Cross-Platform Mapping

### PowerPoint → Word
- 12,192,000 EMU width → 11,906,000 EMU (A4)
- Maintain 12-column structure
- Adjust gutters proportionally

### PowerPoint → Excel
- Map columns to Excel grid
- Use merged cells for layouts
- Maintain aspect ratios

### PowerPoint → Google Slides
- Convert EMU to points (÷ 12700)
- Use percentage-based positioning
- Maintain column relationships

## Benefits

1. **Universal Consistency** - Same grid across all Office apps
2. **Print Safety** - A4-compatible at 16:9 ratio
3. **Professional Quality** - Magazine-style layouts
4. **Accessibility** - Clear visual hierarchy
5. **Flexibility** - Works for any content type

This grid system provides the mathematical foundation for all StyleStack templates, ensuring perfect alignment and professional typography across every document type.