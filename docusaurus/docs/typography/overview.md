# Typography System

StyleStack implements a professional typography system designed for Office templates with EMU-based precision, accessibility compliance, and cross-platform consistency.

## Design Philosophy

Typography is the foundation of professional documents. StyleStack's typography system is built on these principles:

- **Mathematical Precision**: Golden ratio (1.618) scaling for harmonious proportions
- **EMU-Based Measurements**: Native Office units for pixel-perfect rendering
- **Accessibility First**: WCAG AAA compliance built into every design decision
- **Cross-Platform Consistency**: Identical rendering across Microsoft Office, LibreOffice, and Google Workspace

## Typography Scale

### Golden Ratio Scaling System

StyleStack uses a mathematical approach to typography scaling based on the golden ratio:

```yaml
typography:
  scale: 1.618  # Golden Ratio
  base_size: 12pt  # Base text size
  sizes:
    caption: 9pt    # base ÷ 1.333
    body: 12pt      # base size  
    subhead: 15pt   # base × 1.25
    heading_4: 19pt # base × 1.618¹
    heading_3: 31pt # base × 1.618²
    heading_2: 50pt # base × 1.618³
    heading_1: 81pt # base × 1.618⁴
    display: 131pt  # base × 1.618⁵
```

### EMU Conversion

English Metric Units (EMU) provide the most precise measurements for Office templates:

```yaml
# 1 point = 12,700 EMU
# 1 pixel = 9,525 EMU (at 96 DPI)
emu_conversions:
  body_text: 152400  # 12pt
  heading_1: 1028700 # 81pt  
  line_spacing: 190500 # 15pt (1.25x body)
```

## Font System

### Primary Typefaces

StyleStack employs a three-font system for maximum versatility:

:::typography
**Sans-Serif Primary**
- **Family**: Inter
- **Usage**: Body text, UI elements, modern headings
- **Weights**: 100-900
- **Features**: Variable font, extensive language support
:::

:::typography
**Serif Display**
- **Family**: Playfair Display  
- **Usage**: Headlines, display text, elegant documents
- **Weights**: 400-900 (Regular to Black)
- **Features**: High contrast, sophisticated ligatures
:::

:::typography
**Monospace Code**
- **Family**: JetBrains Mono
- **Usage**: Code blocks, data tables, technical content
- **Weights**: 100-800
- **Features**: Programming ligatures, zero-width characters
:::

### Font Feature Settings

Advanced typography features are enabled by default:

```css
font-feature-settings: 
  'kern' 1,    /* Kerning */
  'liga' 1,    /* Standard ligatures */
  'calt' 1,    /* Contextual alternates */
  'pnum' 1,    /* Proportional numbers */
  'onum' 1,    /* Old-style numbers */
  'dlig' 1;    /* Discretionary ligatures */
```

## Line Height and Spacing

### Baseline Grid System

All typography aligns to a 24px baseline grid:

```yaml
baseline_grid: 24px
line_heights:
  tight: 1.25      # Headlines
  comfortable: 1.5  # Body text
  relaxed: 1.625   # Long-form reading
  loose: 2.0       # Code blocks
```

### Vertical Rhythm

Consistent vertical spacing creates visual harmony:

- **Paragraph Spacing**: 1 baseline unit (24px)
- **Heading Margins**: 2 baseline units above, 1 below
- **Section Breaks**: 3 baseline units
- **Page Margins**: 4 baseline units

## Letter Spacing and Tracking

### Optical Adjustments

Different text sizes require different letter spacing:

```yaml
letter_spacing:
  display_text: -0.05em  # Large headings
  headings: -0.025em     # Standard headings  
  body_text: 0em         # Normal text
  captions: 0.025em      # Small text
  uppercase: 0.1em       # All caps
```

### Language-Specific Adjustments

International typography considerations:

- **Latin Scripts**: Standard tracking values
- **Cyrillic**: Slightly tighter spacing (-0.01em)
- **Greek**: Maintain standard spacing
- **Extended Latin**: Account for accent marks

## Accessibility Standards

### WCAG AAA Compliance

All typography choices meet the highest accessibility standards:

:::accessibility
**Color Contrast**
- **Normal Text**: 7:1 minimum contrast ratio
- **Large Text**: 4.5:1 minimum contrast ratio
- **UI Elements**: 4.5:1 minimum contrast ratio
:::

:::accessibility
**Font Size Requirements**
- **Minimum Body**: 12pt (16px equivalent)
- **Minimum UI**: 11pt (14px equivalent)  
- **Zoom Support**: 200% without horizontal scrolling
:::

:::accessibility
**Reading Experience**
- **Line Length**: 45-75 characters optimal
- **Line Height**: 1.5x minimum for body text
- **Paragraph Spacing**: 1.5x line height minimum
:::

## Responsive Typography

### Fluid Scaling

Typography scales smoothly across different document sizes:

```css
/* Clamp function for responsive scaling */
font-size: clamp(1rem, 2.5vw, 2rem);

/* Document width breakpoints */
@media (max-width: 8.5in) { /* Letter paper */
  h1 { font-size: 36pt; }
}

@media (max-width: 5.83in) { /* A5 paper */
  h1 { font-size: 24pt; }
}
```

### Platform Considerations

Different platforms require subtle adjustments:

- **PowerPoint**: Optimize for projection and screen viewing
- **Word**: Prioritize reading comfort and print quality
- **Excel**: Focus on data clarity and scanning

## Code Typography

### Technical Documentation

Specialized typography for code and technical content:

```yaml
code_typography:
  font_family: "JetBrains Mono"
  font_size: 11pt        # Slightly smaller than body
  line_height: 1.4       # Tighter for code density
  background: "#f8fafc"  # Light gray background
  border_radius: 4px     # Subtle container
  padding: "2pt 4pt"     # Comfortable spacing
```

### Syntax Highlighting

Color-coded syntax for different languages:

- **Keywords**: `#0369a1` (Blue)
- **Strings**: `#059669` (Green)  
- **Comments**: `#6b7280` (Gray)
- **Numbers**: `#dc2626` (Red)
- **Functions**: `#7c3aed` (Purple)

## Implementation Examples

### PowerPoint Template

```xml
<!-- Master slide typography definition -->
<p:txBody>
  <a:bodyPr wrap="square" rtlCol="0"/>
  <a:lstStyle>
    <a:lvl1pPr algn="l" defTabSz="914400" rtl="0" eaLnBrk="1">
      <a:defRPr sz="1200" kern="1200">
        <a:solidFill>
          <a:srgbClr val="1F2937"/>
        </a:solidFill>
        <a:latin typeface="Inter"/>
        <a:ea typeface=""/>
        <a:cs typeface=""/>
      </a:defRPr>
    </a:lvl1pPr>
  </a:lstStyle>
</p:txBody>
```

### Word Document Styles

```xml
<!-- Heading 1 style definition -->
<w:style w:type="paragraph" w:styleId="Heading1">
  <w:name w:val="heading 1"/>
  <w:basedOn w:val="Normal"/>
  <w:next w:val="Normal"/>
  <w:qFormat/>
  <w:pPr>
    <w:keepNext/>
    <w:keepLines/>
    <w:spacing w:before="480" w:after="240"/>
  </w:pPr>
  <w:rPr>
    <w:rFonts w:ascii="Playfair Display" w:hAnsi="Playfair Display"/>
    <w:sz w:val="96"/> <!-- 48pt -->
    <w:szCs w:val="96"/>
    <w:color w:val="1F2937"/>
  </w:rPr>
</w:style>
```

## Best Practices

### Document Creation
1. **Start with Templates**: Use StyleStack templates as foundation
2. **Maintain Hierarchy**: Stick to defined heading levels
3. **Consistent Spacing**: Use template-defined paragraph styles
4. **Avoid Manual Formatting**: Rely on styles for consistency

### Brand Customization
1. **Font Substitution**: Replace default fonts while maintaining proportions
2. **Color Harmony**: Ensure new colors maintain contrast ratios
3. **Cultural Adaptation**: Adjust spacing for different writing systems
4. **Print Optimization**: Test typography at intended print sizes

### Quality Assurance
1. **Multi-Platform Testing**: Verify rendering across Office versions
2. **Accessibility Audits**: Regular contrast and readability checks
3. **Print Previews**: Ensure typography works in both digital and print
4. **User Feedback**: Gather input from actual document creators

## Advanced Features

### OpenType Features

StyleStack templates enable advanced typography features:

- **Contextual Alternates**: Automatic character substitution
- **Discretionary Ligatures**: Elegant letter combinations  
- **Stylistic Sets**: Alternative character designs
- **Number Styles**: Tabular vs. proportional figures

### Variable Fonts

Support for variable font technology:

- **Weight Axis**: Fine-tune font weight for perfect hierarchy
- **Width Axis**: Adjust character width for optimal fitting
- **Optical Size**: Automatic adjustments based on text size

### International Typography

Global document support:

- **Right-to-Left**: Arabic and Hebrew text flow
- **Vertical Writing**: East Asian document layouts
- **Complex Scripts**: Proper rendering for Indic languages
- **Font Fallbacks**: Graceful degradation for missing characters

## Future Enhancements

StyleStack typography system continues to evolve:

- **AI-Powered Spacing**: Automatic optical adjustments
- **Dynamic Scaling**: Context-aware font size optimization
- **Voice Optimization**: Typography optimized for screen readers
- **Print Production**: Advanced features for professional publishing

The typography system forms the foundation of professional document creation, ensuring every StyleStack template delivers exceptional reading experiences across all platforms and use cases.