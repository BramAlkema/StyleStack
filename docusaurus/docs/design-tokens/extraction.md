# Design Token Extraction

StyleStack provides powerful reverse engineering capabilities to extract design tokens from existing Office templates. This feature allows you to modernize legacy templates and convert them into the StyleStack design system.

## Overview

The design token extraction system can analyze:
- **Microsoft Office** formats (.pptx, .docx, .xlsx)
- **LibreOffice** formats (.odp, .odt, .ods)
- **OpenDocument** formats (all ODF standards)

## Quick Start

### 1. Drop-and-Extract Workflow

The simplest way to extract design tokens is using our GitHub Actions powered workflow:

```bash
# Place your templates in the extract folder
cp presentation.pptx extract/
git add extract/presentation.pptx
git commit -m "Extract tokens from presentation"
git push
```

GitHub Actions will automatically:
1. Detect the new template
2. Extract comprehensive design tokens
3. Generate JSON configuration files
4. Commit results back to your repository

### 2. Local Extraction

For local development, use the design token extractor directly:

```bash
# Extract from a single template
python tools/design_token_extractor.py extract/presentation.pptx

# Extract multiple templates
python tools/design_token_extractor.py extract/*.pptx

# Custom output format and location
python tools/design_token_extractor.py input.pptx --output custom-tokens.json --format json
```

## Extraction Capabilities

### Typography Analysis
- Font families and fallbacks
- Font sizes in multiple units (pt, px, EMU)
- Line heights and letter spacing
- Font weights and styles
- OpenType feature detection

### Color System Extraction
- Theme colors and accent colors
- RGB, HSL, and Office color scheme mapping
- Color usage frequency analysis
- Accessibility contrast validation
- WCAG compliance assessment

### Layout and Spacing
- Margin and padding measurements
- Grid system detection
- Alignment and positioning rules
- Responsive breakpoint analysis

### Brand Asset Recognition
- Logo extraction and classification
- Icon system cataloging
- Image asset organization
- Vector graphics processing

## Advanced Features

### StyleStack Tools Integration

The extractor leverages existing StyleStack analysis tools:

```python
# Theme analysis with professional color transformations
theme_analysis = ThemeResolver().extract_theme_colors(template)

# Comprehensive template analysis
template_analysis = TemplateAnalyzer().analyze_template(template)

# EMU-based typography measurements
typography_metrics = extract_typography_with_emu_precision(template)
```

### Multi-Format Support

Extract tokens from diverse formats:

:::token
**Microsoft Office**
- PowerPoint (.pptx)
- Word (.docx) 
- Excel (.xlsx)
:::

:::accessibility
**LibreOffice**
- Impress (.odp)
- Writer (.odt)
- Calc (.ods)
:::

:::api
**OpenDocument Standard**
- All ODF formats (.odp, .odt, .ods, .odg, .odf)
- Cross-platform compatibility
- Open source template support
:::

## Output Format

The extractor generates comprehensive JSON files with hierarchical token structure:

```json
stylestack:
  version: "1.0.0"
  tokens:
    colors:
      primary: "#2563eb"
      secondary: "#64748b"
      accent: "#f59e0b"
    typography:
      font_families:
        sans: "Inter, sans-serif"
        serif: "Playfair Display, serif"
        mono: "JetBrains Mono, monospace"
      sizes:
        heading_1: "48pt"
        heading_2: "36pt"
        body: "16pt"
        caption: "14pt"
    spacing:
      baseline_grid: "24px"
      margins:
        slide: "72pt"
        document: "1in"
    brand_assets:
      logos:
        - path: "assets/logo-primary.svg"
          usage: "primary"
          dimensions: "200x60"
      icons:
        - path: "assets/icon-set/"
          count: 24
          format: "svg"
```

## GitHub Actions Integration

The extraction workflow is fully automated through GitHub Actions:

```json
name: Design Token Extraction
on:
  push:
    paths:
      - 'extract/**'

jobs:
  extract-tokens:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Extract Design Tokens
        run: python tools/design_token_extractor.py extract/
      - name: Commit Results
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add extracted/
          git commit -m "🎨 Extract design tokens" || exit 0
          git push
```

## Error Handling and Validation

The extraction system includes robust error handling:

- **Format Validation**: Ensures files are valid OOXML/ODF
- **Schema Validation**: Validates extracted tokens against JSON schemas
- **Accessibility Checks**: WCAG compliance validation
- **Fallback Systems**: Multiple extraction engines for reliability

## Best Practices

### Template Preparation
1. **Clean Templates**: Remove unused elements before extraction
2. **Consistent Naming**: Use descriptive names for styles and colors
3. **Master Layouts**: Ensure master slides/pages represent your design system

### Token Organization
1. **Hierarchical Structure**: Organize tokens by category (colors, typography, spacing)
2. **Semantic Naming**: Use purpose-based names (primary, secondary) over descriptive ones (blue, red)
3. **Version Control**: Track token evolution through git history

### Quality Assurance
1. **Manual Review**: Always review extracted tokens before deployment
2. **Test Generation**: Generate test templates to validate extraction quality
3. **Accessibility Audit**: Ensure extracted colors meet contrast requirements

## Integration with Build System

Extracted tokens integrate seamlessly with the StyleStack build system:

```bash
# Use extracted tokens in template generation
python build.py --tokens extracted/presentation-tokens.json --org acme --channel present

# Merge multiple token sources
python build.py --tokens base-tokens.json,extracted-tokens.json --output branded.potx
```

## Troubleshooting

### Common Issues

**File Format Errors**
- Ensure templates are saved in modern Office formats
- Check for password protection or encryption
- Validate file integrity with office applications

**Missing Assets**
- Embedded assets require additional extraction steps
- External references may not be available
- Check file permissions and accessibility

**Color Extraction Issues**
- Some custom colors may not map perfectly
- Theme-based colors require Office color scheme context
- Manual color mapping may be necessary for complex palettes

### Getting Help

For extraction issues:
1. Check the [troubleshooting guide](../licensing/troubleshooting.md)
2. Review extraction logs for detailed error messages
3. Open an issue on [GitHub](https://github.com/BramAlkema/StyleStack/issues) with sample templates

## Next Steps

After extracting design tokens:
1. **Review and Validate**: Manually check extracted tokens for accuracy
2. **Customize and Extend**: Add organization-specific overrides
3. **Generate Templates**: Use tokens to create new StyleStack templates
4. **Deploy and Distribute**: Share tokens across your design system

The extraction system transforms legacy Office templates into modern, maintainable design systems that can evolve with your brand and accessibility requirements.