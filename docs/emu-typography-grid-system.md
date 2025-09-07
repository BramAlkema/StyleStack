# EMU Typography Grid System Architecture

> Comprehensive background on English Metric Units (EMUs) and OOXML typography grid systems for precise document layout control

## Table of Contents
- [Core EMU Mathematics](#core-emu-mathematics)
- [Word OOXML Typography Grid System](#word-ooxml-typography-grid-system)
- [PowerPoint OOXML Typography Grid System](#powerpoint-ooxml-typography-grid-system)
- [EMU Conversion Formulas](#emu-conversion-formulas)
- [Grid Implementation Examples](#grid-implementation-examples)

## Core EMU Mathematics

### Base EMU Definitions

EMUs (English Metric Units) are the fundamental unit in OOXML for precise positioning:

- **1 inch** = 914,400 EMUs
- **1 cm** = 360,000 EMUs  
- **1 mm** = 36,000 EMUs
- **1 point** = 12,700 EMUs
- **1 pixel** (@ 96 DPI) = 9,525 EMUs
- **1 twip** (1/20 point) = 635 EMUs

### Unit Conversion Table

| Measurement | Points | Twentieths (Word) | Hundredths (PPT) | EMUs | Inches |
|-------------|--------|------------------|------------------|------|---------|
| 6pt | 6 | 120 | 600 | 76,200 | 0.0833" |
| 9pt | 9 | 180 | 900 | 114,300 | 0.125" |
| 12pt | 12 | 240 | 1200 | 152,400 | 0.167" |
| 18pt | 18 | 360 | 1800 | 228,600 | 0.25" |
| 24pt | 24 | 480 | 2400 | 304,800 | 0.333" |
| 36pt | 36 | 720 | 3600 | 457,200 | 0.5" |
| 72pt | 72 | 1440 | 7200 | 914,400 | 1" |

## Word OOXML Typography Grid System

### Core Spacing Mathematics

Values are in **twentieths of a point**. A normal single-spaced paragraph has a `w:line` value of 240, or 12 points.

**Reference**: [SpacingBetweenLines.Line Property](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.spacingbetweenlines.line)

#### The Three Line Spacing Rules

```xml
<!-- lineRule="exact" - Forces precise line height, clips if content too large -->
<w:spacing w:line="360" w:lineRule="exact"/>

<!-- lineRule="atLeast" - Minimum height, expands if content requires -->
<w:spacing w:line="360" w:lineRule="atLeast"/>

<!-- lineRule="auto" - Value interpreted as 240ths of a line -->
<w:spacing w:line="240" w:lineRule="auto"/>
```

**Reference**: [SpacingBetweenLines Class](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.spacingbetweenlines)

### Building a Baseline Grid System

#### Document-Level Grid Definition

```xml
<w:docGrid 
  w:type="lines"
  w:linePitch="360"      <!-- Vertical grid every 18pt -->
  w:charSpace="0"/>      <!-- Horizontal grid (if needed) -->
```

#### Paragraph Spacing Formula

```xml
<w:spacing 
  w:line="[baseline × 20]"
  w:lineRule="exact"
  w:before="[n × baseline × 20]"
  w:after="[n × baseline × 20]"
  w:beforeLines="[n × 100]"    <!-- Alternative: in 100ths of lines -->
  w:afterLines="[n × 100]"/>
```

### Critical OOXML Spacing Behaviors

#### Paragraph Spacing Collision Rules

> "The resulting spacing between the first and second paragraph is 12 points, since that is the largest spacing requested between the two paragraphs"

**Reference**: [Working with paragraphs - Microsoft Learn](https://learn.microsoft.com/en-us/office/open-xml/working-with-paragraphs)

This means Word takes the **MAX** of:
- Previous paragraph's `w:after`
- Next paragraph's `w:before`
- Line spacing value

#### Text Positioning in Line Height

> "When the value of the lineRule attribute is either atLeast or exactly, the text shall be positioned as follows within that line height: When the line height is too small, the text shall be positioned at the bottom of the line (in other words, clipped from the top down). When the line height is too large, the text shall be centered in the available space"

**Reference**: [SpacingBetweenLines Class](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.spacingbetweenlines)

### Implementing Harmonious Ratios

For 12pt base font with 1.5 ratio (18pt baseline):

```xml
<!-- Body Text: 12/18 -->
<w:spacing w:line="360" w:lineRule="exact"/>

<!-- Subhead: 14/18 (fits single baseline) -->
<w:spacing w:line="360" w:lineRule="exact"/>

<!-- H2: 18/27 (1.5 baselines) -->
<w:spacing w:line="540" w:lineRule="exact"/>

<!-- H1: 24/36 (2 baselines) -->
<w:spacing w:line="720" w:lineRule="exact"/>
```

### Multi-Level Grid System

#### Primary Grid (Coarse)

```xml
<w:docGrid w:linePitch="720"/>  <!-- 36pt major grid -->
```

#### Paragraph Implementation (Fine)

```xml
<!-- All spacing in 180 unit (9pt) increments -->
<w:spacing 
  w:line="360"      <!-- 18pt: 2× fine grid -->
  w:before="180"    <!-- 9pt: 1× fine grid -->
  w:after="360"/>   <!-- 18pt: 2× fine grid -->
```

### Advanced Grid Alignments

#### Snap to Grid Control

```xml
<w:pPr>
  <w:snapToGrid w:val="true"/>  <!-- Forces alignment to docGrid -->
  <w:spacing w:line="360" w:lineRule="exact"/>
</w:pPr>
```

#### Asian Typography Grid (Additional Control)

```xml
<w:pPr>
  <w:adjustRightInd w:val="false"/>
  <w:snapToGrid w:val="true"/>
  <w:spacing w:line="360" w:lineRule="exact"/>
  <w:textAlignment w:val="baseline"/>  <!-- Baseline alignment -->
</w:pPr>
```

### Table Grid Integration

Tables need special handling to maintain grid:

```xml
<w:tblPr>
  <w:tblCellSpacing w:w="0" w:type="dxa"/>
  <w:tblInd w:w="0" w:type="dxa"/>
</w:tblPr>
<w:tcPr>
  <w:tcMar>
    <w:top w:w="180" w:type="dxa"/>     <!-- 9pt top padding -->
    <w:bottom w:w="180" w:type="dxa"/>  <!-- 9pt bottom padding -->
  </w:tcMar>
</w:tcPr>
```

### Handling Mixed Content

#### For inline elements that might break grid:

```xml
<!-- Superscript/Subscript -->
<w:rPr>
  <w:vertAlign w:val="superscript"/>
  <w:position w:val="6"/>  <!-- Twips offset, keeps line height -->
</w:rPr>

<!-- Images/Objects -->
<w:pPr>
  <w:spacing 
    w:line="720"          <!-- Multiple of baseline for image -->
    w:lineRule="exact"/>
</w:pPr>
```

### Precise Fractional Baselines

For typography requiring fractional baseline units:

```xml
<!-- 13.5pt line height (270 units) -->
<w:spacing w:line="270" w:lineRule="exact"/>

<!-- Maintain grid with compensating space -->
<w:spacing 
  w:line="270" 
  w:after="90"    <!-- Compensate: 270 + 90 = 360 (back on grid) -->
  w:lineRule="exact"/>
```

### East Asian Grid Features

```xml
<w:docGrid 
  w:type="linesAndChars"
  w:linePitch="360"        <!-- Vertical pitch -->
  w:charSpace="4320"/>     <!-- Character pitch for CJK -->

<w:pPr>
  <w:disableLineHeightGrid w:val="false"/>  <!-- Enable grid -->
  <w:lineUnitBefore="100"/>  <!-- Before in grid lines -->
  <w:lineUnitAfter="100"/>   <!-- After in grid lines -->
</w:pPr>
```

### Validation Rules

To maintain perfect grid:

1. All `w:line` values should be multiples of your base unit
2. All `w:before` and `w:after` should be multiples of base/2
3. Use `lineRule="exact"` for predictable spacing
4. Sum of (line + before + after) should equal n × baseline

## PowerPoint OOXML Typography Grid System

PowerPoint's OOXML structure differs significantly from Word's - it's based on **absolute positioning** rather than document flow, which actually makes certain grid implementations easier but introduces other challenges.

### Core Differences from Word

#### Coordinate System
- PowerPoint uses **EMUs** (English Metric Units): 1 point = 12,700 EMUs
- All positioning is **absolute** from slide origin (0,0)  
- Text boxes have **fixed positions and sizes**

### Text Container Structure

```xml
<p:sp>  <!-- Shape -->
  <p:nvSpPr>...</p:nvSpPr>
  <p:spPr>
    <a:xfrm>  <!-- Transform/Position -->
      <a:off x="914400" y="914400"/>  <!-- 1 inch from top-left -->
      <a:ext cx="7315200" cy="914400"/> <!-- Width × Height -->
    </a:xfrm>
  </p:spPr>
  <p:txBody>
    <a:bodyPr anchor="t" anchorCtr="0">  <!-- Top anchor -->
      <a:spAutoFit/>  <!-- Or noAutoFit for fixed -->
    </a:bodyPr>
    <a:p>  <!-- Paragraph -->
      <a:pPr>
        <a:spcBef>
          <a:spcPts val="600"/>  <!-- 6pt before (×100) -->
        </a:spcBef>
        <a:spcAft>
          <a:spcPts val="1200"/> <!-- 12pt after (×100) -->
        </a:spcAft>
        <a:lnSpc>
          <a:spcPts val="1800"/>  <!-- 18pt line spacing (×100) -->
        </a:lnSpc>
      </a:pPr>
    </a:p>
  </p:txBody>
</p:sp>
```

### PowerPoint Line Spacing System

Three spacing methods:

```xml
<!-- Exact points (most precise for grids) -->
<a:lnSpc>
  <a:spcPts val="1800"/>  <!-- 18pt exactly (×100) -->
</a:lnSpc>

<!-- Percentage of font size -->
<a:lnSpc>
  <a:spcPct val="150000"/>  <!-- 150% (×1000) -->
</a:lnSpc>

<!-- No spacing specified (uses font metrics) -->
```

### Building a Baseline Grid

#### Slide Master Grid Definition

```xml
<p:sldMaster>
  <p:cSld>
    <p:spTree>
      <!-- Invisible grid guides (optional visual aids) -->
      <p:graphicFrame>
        <a:graphic>
          <a:graphicData>
            <!-- Grid at 18pt intervals -->
            <p:guide orient="horz" pos="228600"/>   <!-- 18pt -->
            <p:guide orient="horz" pos="457200"/>   <!-- 36pt -->
            <p:guide orient="horz" pos="685800"/>   <!-- 54pt -->
            <!-- Continue for full slide... -->
          </a:graphicData>
        </a:graphic>
      </p:graphicFrame>
    </p:spTree>
  </p:cSld>
</p:sldMaster>
```

### Typography Styles in Theme

```xml
<!-- In theme1.xml -->
<a:fontScheme>
  <a:majorFont>
    <a:latin typeface="Arial"/>
  </a:majorFont>
  <a:minorFont>
    <a:latin typeface="Arial"/>
  </a:minorFont>
</a:fontScheme>

<!-- Text hierarchy styles -->
<p:txStyles>
  <p:titleStyle>
    <a:lvl1pPr>
      <a:defRPr sz="3600"/>  <!-- 36pt -->
      <a:lnSpc>
        <a:spcPts val="3600"/>  <!-- 36pt line spacing -->
      </a:lnSpc>
      <a:spcBef>
        <a:spcPts val="0"/>
      </a:spcBef>
      <a:spcAft>
        <a:spcPts val="1800"/>  <!-- 18pt after -->
      </a:spcAft>
    </a:lvl1pPr>
  </p:titleStyle>
  
  <p:bodyStyle>
    <a:lvl1pPr>
      <a:defRPr sz="1800"/>  <!-- 18pt -->
      <a:lnSpc>
        <a:spcPts val="2400"/>  <!-- 24pt line spacing -->
      </a:lnSpc>
    </a:lvl1pPr>
  </p:bodyStyle>
</p:txStyles>
```

### Absolute Positioning for Grid Alignment

Positioning text boxes on grid points:

```xml
<p:sp>
  <p:spPr>
    <a:xfrm>
      <!-- Position at grid intersection -->
      <a:off x="914400" y="914400"/>      <!-- 72pt, 72pt -->
      <!-- Height as multiple of baseline -->
      <a:ext cx="6858000" cy="1371600"/>  <!-- Width, 108pt height (6×18pt) -->
    </a:xfrm>
  </p:spPr>
  <p:txBody>
    <a:bodyPr anchor="t" vert="horz">
      <!-- Top alignment crucial for grid -->
      <a:normAutofit fontScale="100000" lnSpcReduction="0"/>
    </a:bodyPr>
  </p:txBody>
</p:sp>
```

### Multi-Level List Spacing

```xml
<a:lstStyle>
  <a:lvl1pPr marL="0" indent="0">
    <a:lnSpc><a:spcPts val="1800"/></a:lnSpc>
    <a:spcBef><a:spcPts val="0"/></a:spcBef>
    <a:spcAft><a:spcPts val="900"/></a:spcAft>  <!-- Half baseline -->
  </a:lvl1pPr>
  <a:lvl2pPr marL="457200" indent="-228600">   <!-- Indented -->
    <a:lnSpc><a:spcPts val="1800"/></a:lnSpc>  <!-- Same baseline -->
  </a:lvl2pPr>
</a:lstStyle>
```

### Vertical Alignment Solutions

Critical for baseline alignment:

> "Microsoft's decision to use baseline vertical bullet alignment instead of the text center has haunted us for decades" - [Edit OOXML with VBA - Cool Code - Brandwares](https://brandwares.com)

Fix bullet alignment:

```xml
<a:lvl1pPr marL="0" indent="0" algn="l" defTabSz="914400" 
           rtl="0" eaLnBrk="1" latinLnBrk="0" hangingPunct="1"
           fontAlgn="ctr">  <!-- Center align bullets to text -->
```

### Table Grid Integration

```xml
<a:tbl>
  <a:tblPr firstRow="1" bandRow="1">
    <a:tableStyleId>{GUID}</a:tableStyleId>
  </a:tblPr>
  <a:tblGrid>
    <a:gridCol w="2286000"/>  <!-- Column widths -->
  </a:tblGrid>
  <a:tr h="457200">  <!-- Row height: 36pt (2×18pt baseline) -->
    <a:tc>
      <a:tcPr marL="114300" marR="114300" 
              marT="114300" marB="114300">  <!-- 9pt margins -->
      </a:tcPr>
      <a:txBody>
        <a:bodyPr anchor="ctr"/>  <!-- Center vertically -->
        <a:p>
          <a:pPr>
            <a:lnSpc><a:spcPts val="1800"/></a:lnSpc>
          </a:pPr>
        </a:p>
      </a:txBody>
    </a:tc>
  </a:tr>
</a:tbl>
```

### Placeholder Inheritance System

```xml
<!-- In slideLayout.xml -->
<p:sp>
  <p:nvSpPr>
    <p:nvPr>
      <p:ph type="body" idx="1"/>  <!-- Placeholder type -->
    </p:nvPr>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm>
      <a:off x="457200" y="1143000"/>  <!-- On grid points -->
      <a:ext cx="8229600" cy="4572000"/>
    </a:xfrm>
  </p:spPr>
  <!-- Text properties inherited from master -->
</p:sp>
```

### Maintaining Grid Across Slides

Layout Coordinates System:

```xml
<!-- Define consistent zones -->
<p:sldLayout>
  <!-- Title zone: 0-72pt -->
  <p:sp>
    <a:off x="457200" y="0"/>
    <a:ext cx="8229600" cy="914400"/>  <!-- 72pt height -->
  </p:sp>
  
  <!-- Body zone: 90pt-450pt (with 18pt gap) -->
  <p:sp>
    <a:off x="457200" y="1143000"/>    <!-- 90pt from top -->
    <a:ext cx="8229600" cy="4572000"/>  <!-- 360pt height -->
  </p:sp>
</p:sldLayout>
```

### Text Autofit vs Grid

Three autofit behaviors:

```xml
<!-- No autofit - maintains grid -->
<a:bodyPr>
  <a:noAutofit/>
</a:bodyPr>

<!-- Shrink text - breaks grid -->
<a:bodyPr>
  <a:normAutofit fontScale="75000" lnSpcReduction="20000"/>
</a:bodyPr>

<!-- Resize shape - maintains internal grid -->
<a:bodyPr>
  <a:spAutoFit/>
</a:bodyPr>
```

### Smart Art and Grid Compliance

```xml
<p:graphicFrame>
  <a:graphic>
    <a:graphicData>
      <dgm:relIds>
        <!-- SmartArt with controlled spacing -->
        <dgm:sp>
          <dgm:style>
            <a:lnSpc><a:spcPts val="1800"/></a:lnSpc>
          </dgm:style>
        </dgm:sp>
      </dgm:relIds>
    </a:graphicData>
  </a:graphic>
</p:graphicFrame>
```

### Key Differences from Word

1. **Absolute positioning** makes grid snapping easier
2. **No flow between text boxes** - each is independent
3. **Placeholder system** allows style inheritance from masters
4. **Values in different units** (×100 for points, EMUs for position)
5. **Autofit behaviors** can break grids if not controlled
6. **Theme-based styling** rather than document styles

The advantage in PowerPoint is that once you position elements correctly on your grid, they stay there. The challenge is that you must manually position everything and there's no automatic flow to help maintain rhythm across content changes.

## EMU Conversion Formulas

### Conversion Formulas

**Points to EMUs:**
```
EMUs = Points × 12,700
```

**Inches to EMUs:**
```
EMUs = Inches × 914,400
```

**Pixels to EMUs (at standard 96 DPI):**
```
EMUs = Pixels × 9,525
```

**Twips to EMUs:**
```
EMUs = Twips × 635
```
*(1 twip = 1/20 point = 635 EMUs)*

### Where EMUs Are Used

#### Word OOXML

**Drawing Objects & Shapes:**
```xml
<wp:extent cx="2286000" cy="1143000"/>  <!-- 2.5" × 1.25" -->
<wp:positionH relativeFrom="column">
  <wp:posOffset>457200</wp:posOffset>   <!-- 0.5" offset -->
</wp:positionH>
```

**Images:**
```xml
<pic:spPr>
  <a:xfrm>
    <a:ext cx="5486400" cy="3657600"/>  <!-- 6" × 4" image -->
  </a:xfrm>
</pic:spPr>
```

**Tables (column widths):**
```xml
<w:tblGrid>
  <w:gridCol w="1800000"/>  <!-- ~1.97" column -->
</w:tblGrid>
```

**NOT used for:**
- Line spacing (uses twentieths of a point)
- Paragraph spacing (uses twentieths of a point)
- Font sizes (uses half-points)
- Margins (uses twentieths of a point)

#### PowerPoint OOXML

**Everything positional uses EMUs:**
```xml
<p:sp>
  <p:spPr>
    <a:xfrm>
      <a:off x="914400" y="914400"/>      <!-- Position: 1", 1" -->
      <a:ext cx="7315200" cy="914400"/>   <!-- Size: 8" × 1" -->
    </a:xfrm>
  </p:spPr>
</p:sp>
```

**Table dimensions:**
```xml
<a:tblGrid>
  <a:gridCol w="2286000"/>  <!-- 2.5" column -->
</a:tblGrid>
<a:tr h="457200">           <!-- 0.5" row height -->
```

**Margins and indents:**
```xml
<a:tcPr marL="114300" marT="114300">  <!-- 0.125" margins -->
<a:lvl1pPr marL="342900" indent="-342900">  <!-- 0.375" indent -->
```

**NOT used for:**
- Font sizes (uses hundredths of points: 1800 = 18pt)
- Line spacing values (uses hundredths of points)
- Spacing before/after (uses hundredths of points)

## Grid Implementation Examples

### Practical Grid Calculations

**For an 18pt baseline grid:**
```
18pt baseline = 228,600 EMUs

Grid positions:
0pt   = 0 EMUs
18pt  = 228,600 EMUs  
36pt  = 457,200 EMUs
54pt  = 685,800 EMUs
72pt  = 914,400 EMUs (1 inch)
90pt  = 1,143,000 EMUs
108pt = 1,371,600 EMUs
```

**For 12-column grid on 10" slide width:**
```
10 inches = 9,144,000 EMUs
Column width = 762,000 EMUs (no gutters)
With 12pt gutters = 152,400 EMUs each
Usable column = 609,600 EMUs
```

### Why EMUs?

EMUs provide:

1. **Integer precision** - no rounding errors
2. **Universal unit** - converts cleanly to metric and imperial
3. **Fine control** - can represent differences smaller than a pixel
4. **Cross-application consistency** - same unit across all Office apps

The key insight: EMUs let you position elements with sub-pixel precision while avoiding floating-point math errors that could accumulate and break your grid alignment.

## Calculating Margin Compensation for Perfect Grid Alignment

### The Core Problem

When text doesn't fill exact baseline multiples, you must add compensating space to "push" the next element back onto the grid.

### The Compensation Formula

```
Total Height = Line Height + Font Metrics + Compensation
Total Height MUST = n × Baseline Grid Unit

Therefore:
Compensation = (n × Baseline) - (Line Height + Internal Space)
```

### Word OOXML Calculations

For 18pt baseline grid (360 twentieths):

```xml
<!-- 14pt text that needs to fit 18pt grid -->
<w:pPr>
  <w:spacing 
    w:line="280"        <!-- 14pt line height -->
    w:lineRule="exact"
    w:after="80"/>      <!-- 4pt compensation (360-280=80) -->
</w:pPr>

<!-- 24pt heading spanning 36pt (2 baselines) -->
<w:pPr>
  <w:spacing 
    w:line="480"        <!-- 24pt line height -->
    w:lineRule="exact"
    w:after="240"/>     <!-- 12pt compensation (720-480=240) -->
</w:pPr>
```

### PowerPoint OOXML Calculations

Same 18pt baseline (228,600 EMUs):

```xml
<!-- 14pt text fitting 18pt grid -->
<a:pPr>
  <a:lnSpc>
    <a:spcPts val="1400"/>  <!-- 14pt -->
  </a:lnSpc>
  <a:spcAft>
    <a:spcPts val="400"/>   <!-- 4pt compensation -->
  </a:spcAft>
</a:pPr>
```

### Multi-Line Compensation Patterns

#### Pattern 1: Single-Line Elements

| Text Size | Lines | Target Height | Line Spacing | Compensation |
|-----------|-------|---------------|--------------|-------------|
| 10pt | 1 | 18pt | 10pt | 8pt after |
| 12pt | 1 | 18pt | 12pt | 6pt after |
| 14pt | 1 | 18pt | 14pt | 4pt after |
| 16pt | 1 | 18pt | 16pt | 2pt after |

#### Pattern 2: Multi-Line Blocks

| Text Size | Lines | Target Height | Line Spacing | Total Comp | Distribution |
|-----------|-------|---------------|--------------|------------|-------------|
| 12pt | 3 | 54pt (3×18) | 36pt (3×12) | 18pt | 9pt before/after |
| 14pt | 2 | 36pt (2×18) | 28pt (2×14) | 8pt | 4pt before/after |
| 20pt | 2 | 54pt (3×18) | 40pt (2×20) | 14pt | 7pt before/after |

### Compensation Distribution Strategies

#### Strategy 1: All After (Simplest)

```xml
<w:spacing 
  w:line="320"          <!-- 16pt -->
  w:lineRule="exact"
  w:before="0"
  w:after="40"/>        <!-- All 2pt compensation after -->
```

#### Strategy 2: Split Before/After (Centered)

```xml
<w:spacing 
  w:line="280"          <!-- 14pt -->
  w:lineRule="exact"
  w:before="40"         <!-- 2pt before -->
  w:after="40"/>        <!-- 2pt after -->
```

#### Strategy 3: Weighted Distribution

```xml
<!-- For headings: more space before -->
<w:spacing 
  w:line="480"          <!-- 24pt -->
  w:lineRule="exact"
  w:before="180"        <!-- 9pt (2/3 of compensation) -->
  w:after="60"/>        <!-- 3pt (1/3 of compensation) -->
```

### Calculating for Fractional Baselines

When text spans 1.5 baselines:
- 18pt baseline × 1.5 = 27pt target
- 20pt font with 24pt line height needs 3pt compensation

**Word OOXML:**
```xml
<w:spacing w:line="480" w:after="60"/>  <!-- 24pt + 3pt = 27pt -->
```

**PowerPoint:**
```xml
<a:lnSpc><a:spcPts val="2400"/></a:lnSpc>
<a:spcAft><a:spcPts val="300"/></a:spcAft>
```

### Complex Paragraph Calculations

#### For paragraphs with different internal spacing:

**Paragraph with 15pt font, 1.2× line height, on 18pt grid:**
- Font: 15pt
- Line height: 18pt (15 × 1.2)
- Already on grid! No compensation needed

**Paragraph with 13pt font, 1.3× line height:**
- Font: 13pt  
- Line height: 16.9pt
- Round to 17pt, need 1pt compensation per line
- For 3 lines: 51pt + 3pt = 54pt (exactly 3 baselines)

### Advanced Grid Alignment Table

For 12pt baseline (240 twentieths):

| Font | Line Height | Lines | Natural Height | Target Grid | Compensation | Word After | PPT After |
|------|-------------|-------|----------------|-------------|--------------|------------|-----------|
| 8pt | 10pt | 1 | 10pt | 12pt | 2pt | 40 | 200 |
| 9pt | 11pt | 1 | 11pt | 12pt | 1pt | 20 | 100 |
| 10pt | 12pt | 1 | 12pt | 12pt | 0pt | 0 | 0 |
| 11pt | 14pt | 1 | 14pt | 24pt | 10pt | 200 | 1000 |
| 10pt | 12pt | 2 | 24pt | 24pt | 0pt | 0 | 0 |
| 10pt | 12pt | 3 | 36pt | 36pt | 0pt | 0 | 0 |
| 11pt | 14pt | 2 | 28pt | 36pt | 8pt | 160 | 800 |

### Automation Formula

```python
def calculate_compensation(font_size, line_ratio, num_lines, baseline_grid):
    line_height = font_size * line_ratio
    natural_height = line_height * num_lines
    
    # Find next grid multiple
    grid_units = math.ceil(natural_height / baseline_grid)
    target_height = grid_units * baseline_grid
    
    # Calculate compensation
    total_compensation = target_height - natural_height
    
    # Convert to OOXML units
    word_units = total_compensation * 20  # twentieths
    ppt_units = total_compensation * 100   # hundredths
    emu_units = total_compensation * 12700 # EMUs
    
    return {
        'total_comp_pts': total_compensation,
        'word_spacing_after': word_units,
        'ppt_spacing_after': ppt_units,
        'emus': emu_units
    }
```

### The Key Insight

Perfect grid alignment requires thinking in **"grid slots"** - every text block must occupy exactly n baselines, using compensation margins to fill any gaps. This makes your document behave like traditional lead type, where everything snaps to invisible horizontal lines.

---

## Implementation Notes

This gives you mathematically precise typography control in Word and PowerPoint through OOXML, achieving what's impossible through the applications' standard user interfaces.

For more technical details, see:
- [Microsoft Learn - OOXML Documentation](https://learn.microsoft.com/en-us/office/open-xml/)
- [Brandwares - Advanced OOXML Techniques](https://brandwares.com)