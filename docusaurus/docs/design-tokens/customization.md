---
sidebar_position: 3
---

# Token Customization

Learn how to customize design tokens for your organization while maintaining consistency and accessibility. This guide covers practical techniques for adapting StyleStack templates to your brand requirements.

## Customization Philosophy

StyleStack's customization approach follows these principles:

- **Override, don't replace** - Build on community defaults
- **Semantic naming** - Use purpose-driven token names  
- **Accessibility first** - Never compromise WCAG compliance
- **Progressive enhancement** - Layer customizations thoughtfully
- **Documentation** - Document the rationale behind changes

## Getting Started

### 1. Audit Your Brand Guidelines

Before customizing tokens, gather your organization's brand assets:

**Required Assets:**
- Brand color palette (primary, secondary, accent colors)
- Typography guidelines (fonts, sizes, hierarchy)  
- Logo files (PNG with transparency recommended)
- Style guide or brand manual

**Accessibility Audit:**
```bash
# Check color contrast ratios
python tools/accessibility-audit.py --colors "#1E40AF,#FFFFFF" --standard "AA"

# Verify font readability
python tools/font-audit.py --fonts "YourBrandFont" --min-size "12pt"
```

### 2. Create Organization Structure

```bash
# Set up your organization directory
mkdir -p org/your-org/{assets,channels}

# Create base configuration
touch org/your-org/patches.json
touch org/your-org/governance.json
```

## Color Customization

### Basic Color Override

```json
# org/your-org/patches.json
colors:
  # Brand colors
  primary: "#1E40AF"        # Your brand blue
  secondary: "#059669"      # Your brand green
  accent: "#F59E0B"         # Your brand orange
  
  # Maintain accessibility
  text_primary: "#0F172A"   # Keep dark text
  text_secondary: "#475569" # Keep medium contrast
```

### Advanced Color System

```json
colors:
  # Base brand colors
  brand:
    navy: "#1E40AF"
    gold: "#F59E0B"
    silver: "#6B7280"
    
  # Semantic mappings
  primary: "{brand.navy}"
  secondary: "{brand.silver}"  
  accent: "{brand.gold}"
  
  # Contextual variants
  primary_light: "{primary.lighten(20%)}"
  primary_dark: "{primary.darken(20%)}"
  primary_transparent: "{primary.alpha(50%)}"
  
  # State colors with brand influence
  success: "{brand.navy.mix(#059669, 30%)}"  # Mix brand with green
  warning: "{brand.gold}"                     # Use brand gold
  error: "#DC2626"                           # Keep standard red
```

### Color Accessibility

```json
# Automatic contrast checking
colors:
  primary: "#1E40AF"
  
accessibility:
  auto_contrast: true       # Automatically compute contrasting colors
  min_contrast_ratio: 4.5   # WCAG AA standard
  
# Generated automatically:
# text_on_primary: "#FFFFFF" (auto-calculated for contrast)
# text_on_secondary: "#000000"
```

### Color Validation

```bash
# Test color combinations
python tools/validate-colors.py --org your-org
```

Output:
```
✓ Primary/Text contrast: 4.8:1 (AA compliant)
✓ Secondary/Text contrast: 5.2:1 (AA compliant)
⚠ Accent/Background contrast: 3.1:1 (fails AA, passes A)
```

## Typography Customization

### Font Selection

```json
fonts:
  # Brand typography
  heading: "Montserrat"      # Modern, clean sans-serif
  body: "Open Sans"          # Highly readable
  accent: "Playfair Display" # Elegant serif for special emphasis
  monospace: "Fira Code"     # Code and data display
  
  # Font stacks with fallbacks
  heading_stack: "Montserrat, 'Helvetica Neue', Arial, sans-serif"
  body_stack: "Open Sans, 'Segoe UI', Roboto, sans-serif"
```

### Typography Scale

```json
typography:
  # Base settings
  scale_ratio: 1.25          # Major third (5:4 ratio)
  base_size: "16pt"          # Base font size
  
  # Line height
  line_height: 1.6           # Body text
  heading_line_height: 1.2   # Headings
  caption_line_height: 1.4   # Captions and small text
  
  # Font weights
  weights:
    light: 300
    regular: 400
    medium: 500
    bold: 700
    
  # Calculated sizes (using scale_ratio)
  sizes:
    xs: "{base_size / scale_ratio^2}"    # ~10pt
    sm: "{base_size / scale_ratio}"      # ~13pt  
    md: "{base_size}"                    # 16pt
    lg: "{base_size * scale_ratio}"      # ~20pt
    xl: "{base_size * scale_ratio^2}"    # ~25pt
    xxl: "{base_size * scale_ratio^3}"   # ~31pt
```

### Font Loading and Performance

```json
fonts:
  # Web fonts (Google Fonts)
  web_fonts:
    - family: "Inter"
      weights: [400, 500, 700]
      display: "swap"          # Improve loading performance
      
  # Local fonts (system installed)  
  system_fonts:
    - "SF Pro Display"         # macOS
    - "Segoe UI"              # Windows
    - "Ubuntu"                # Linux
    
  # Fallback strategy
  fallback_order:
    1: "web_fonts"            # Try web fonts first
    2: "system_fonts"         # Fall back to system fonts
    3: "generic"              # Final fallback to sans-serif
```

## Spacing and Layout

### Spacing System

```json
spacing:
  # Base unit (8pt grid)
  unit: "8pt"
  
  # Scale multipliers
  scale:
    xs: 0.25    # 2pt
    sm: 0.5     # 4pt
    md: 1       # 8pt  
    lg: 1.5     # 12pt
    xl: 2       # 16pt
    xxl: 3      # 24pt
    xxxl: 4     # 32pt
    
  # Calculated values
  xs: "{unit * scale.xs}"
  sm: "{unit * scale.sm}"
  md: "{unit * scale.md}"
  lg: "{unit * scale.lg}"
  xl: "{unit * scale.xl}"
  xxl: "{unit * scale.xxl}"
  xxxl: "{unit * scale.xxxl}"
```

### Layout Customization

```json
layout:
  # Page settings
  margins:
    top: "{spacing.xxl}"       # 24pt
    right: "{spacing.xxl}"     # 24pt
    bottom: "{spacing.xxl}"    # 24pt
    left: "{spacing.xxl}"      # 24pt
    
  # Content settings
  content_width: "8.5in"       # Standard page width
  line_length: "65ch"          # Optimal reading line length
  
  # Grid settings
  columns: 12                  # 12-column grid
  gutter: "{spacing.lg}"       # 12pt gutters
  
  # Border and radius
  border_width: "1pt"
  border_radius: "4pt"
  border_radius_large: "8pt"
```

## Asset Management

### Logo Integration

```json
assets:
  # Primary logo
  logo:
    path: "assets/logo.png"
    width: "200pt"
    height: "60pt"
    positioning: "bottom-right"
    
  # Logo variants
  logo_white:
    path: "assets/logo-white.png"
    usage: "dark_backgrounds"
    
  logo_monochrome:
    path: "assets/logo-mono.png"
    usage: "print_grayscale"
    
  # Official seal
  seal:
    path: "assets/official-seal.png"
    width: "80pt"
    height: "80pt"
    usage: "formal_documents"
```

### Asset Optimization

```bash
# Optimize assets for template use
python tools/optimize-assets.py --org your-org --format png --dpi 300

# Validate asset dimensions and file sizes  
python tools/validate-assets.py --org your-org
```

## Channel-Specific Customization

### Presentation Channel

```json
# org/your-org/channels/presentation.json
name: "Presentation Templates"
target_products: ["potx"]

typography:
  # Larger fonts for projection
  base_size: "20pt"           # Readable from distance
  title_size: "48pt"          # Large titles
  
colors:
  # High contrast for projection
  slide_background: "{primary}"
  text_on_slide: "#FFFFFF"
  accent_on_slide: "{accent}"
  
layout:
  # Presentation-specific layouts
  title_slide: "corporate_title"
  content_slide: "corporate_content"
  section_slide: "corporate_section"
```

### Document Channel

```json
# org/your-org/channels/document.json
name: "Document Templates"
target_products: ["dotx"]

typography:
  # Optimized for reading
  base_size: "12pt"           # Standard document size
  line_height: 1.6            # Comfortable reading
  
layout:
  # Generous margins for binding
  margins:
    left: "1.5in"             # Extra space for binding
    right: "1in"
    top: "1in"
    bottom: "1in"
```

## Advanced Customization Techniques

### Conditional Customization

```json
# Different tokens based on context
colors:
  primary:
    default: "#1E40AF"
    high_contrast: "#000080"   # Darker for accessibility
    print: "#000000"           # Black for print
    
typography:
  base_size:
    screen: "16pt"
    print: "12pt" 
    projection: "24pt"
```

### Dynamic Token Generation

```json
# Generate color palettes from base colors
color_generation:
  base_colors:
    primary: "#1E40AF"
    
  generated_palette:
    primary_50: "{primary.lighten(45%)}"   # Very light tint
    primary_100: "{primary.lighten(40%)}"  # Light tint
    primary_200: "{primary.lighten(30%)}"  # Medium light
    primary_300: "{primary.lighten(20%)}"  # Light
    primary_400: "{primary.lighten(10%)}"  # Slightly light
    primary_500: "{primary}"               # Base color
    primary_600: "{primary.darken(10%)}"   # Slightly dark
    primary_700: "{primary.darken(20%)}"   # Dark
    primary_800: "{primary.darken(30%)}"   # Very dark
    primary_900: "{primary.darken(40%)}"   # Darkest
```

### Token Validation and Testing

```json
# Token validation rules
validation:
  colors:
    contrast_ratio:
      min: 4.5                # WCAG AA
      preferred: 7.0          # WCAG AAA
      
  typography:
    font_size:
      min: "12pt"
      max: "72pt"
      
  spacing:
    unit_multiple: true       # Must be multiples of base unit
    
  assets:
    max_file_size: "1MB"
    required_formats: ["png"]
    min_resolution: 150       # DPI
```

## Testing Customizations

### Build and Test Workflow

```bash
# Build with custom tokens
python build.py --org your-org --channel presentation --products potx

# Validate output
python tools/validate.py --template "BetterDefaults-your-org-presentation-*.potx"

# Test accessibility
python tools/accessibility-test.py --template "BetterDefaults-your-org-*.potx"

# Visual regression testing
python tools/visual-test.py --org your-org --baseline core --compare current
```

### Manual Testing Checklist

**Visual Consistency:**
- [ ] Brand colors appear correctly
- [ ] Fonts load and display properly
- [ ] Logos are positioned and sized correctly
- [ ] Spacing follows grid system

**Accessibility:**
- [ ] Color contrast meets WCAG guidelines
- [ ] Font sizes meet minimum requirements
- [ ] Focus indicators are visible
- [ ] Alt text is provided for images

**Cross-Platform:**
- [ ] Works in Office 2016+
- [ ] Compatible with Office 365
- [ ] Functions in LibreOffice
- [ ] Displays correctly on different screen sizes

## Troubleshooting

### Common Issues

**Colors not applying:**
```json
# Ensure hex format is correct
colors:
  primary: "#1E40AF"    # Correct
  # primary: "1E40AF"   # Wrong - missing #
```

**Fonts not loading:**
```bash
# Check font installation
fc-list | grep "YourFont"

# Verify font file permissions
ls -la org/your-org/assets/fonts/
```

**Assets not appearing:**
```bash
# Verify asset paths
file org/your-org/assets/logo.png

# Check file permissions
chmod 644 org/your-org/assets/*.png
```

### Debug Mode

```bash
# Build with verbose output
python build.py --org your-org --verbose --debug

# Token resolution debugging
python tools/debug-tokens.py --org your-org --token "colors.primary"
```

## Best Practices

### Token Organization

```json
# Group related tokens
colors:
  # Brand colors
  brand_primary: "#1E40AF"
  brand_secondary: "#059669"
  
  # UI colors  
  ui_background: "#FFFFFF"
  ui_border: "#E5E7EB"
  
  # State colors
  state_success: "#059669"
  state_warning: "#F59E0B"
  state_error: "#DC2626"
```

### Documentation

```json
# Document token purposes
colors:
  primary: "#1E40AF"          # Main brand color for headers, buttons, links
  secondary: "#059669"        # Secondary actions, success states
  accent: "#F59E0B"           # Highlights, warnings, call-to-action elements
```

### Version Control

```bash
# Track token changes
git add org/your-org/patches.json
git commit -m "Update brand colors for Q4 2024 guidelines"

# Tag major customization releases
git tag v2.1.0-your-org
```

## Next Steps

- [Explore all available token variables](./variables.md)
- [Learn about fork management](../fork-management/customizing.md)
- [See customization examples](../examples/university.md)
- [Set up automated builds](../deployment/ci-cd.md)