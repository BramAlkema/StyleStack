---
sidebar_position: 4
---

# Available Variables

Complete reference of all design tokens available in StyleStack. These variables can be customized at the organization and channel layers to match your brand requirements.

## Color Variables

### Base Colors

```yaml
colors:
  # Primary brand colors
  primary: "#2563EB"           # Main brand color
  secondary: "#64748B"         # Secondary brand color  
  accent: "#059669"            # Accent/highlight color
  
  # Neutral colors
  neutral_dark: "#0F172A"      # Dark neutral (Slate 900)
  neutral: "#64748B"           # Medium neutral (Slate 500)
  neutral_light: "#F1F5F9"     # Light neutral (Slate 100)
  
  # Background colors
  surface: "#FFFFFF"           # Main background
  surface_secondary: "#F8FAFC" # Secondary background (Slate 50)
  surface_tertiary: "#F1F5F9"  # Tertiary background (Slate 100)
```

### Text Colors

```yaml
colors:
  # Text hierarchy
  text_primary: "#0F172A"      # Primary text (high contrast)
  text_secondary: "#475569"    # Secondary text (medium contrast)
  text_muted: "#94A3B8"        # Muted text (low contrast)
  text_inverse: "#FFFFFF"      # Text on dark backgrounds
  
  # Link colors
  link_default: "{primary}"    # Default link color
  link_hover: "{primary.darken(10%)}"   # Hover state
  link_visited: "{primary.darken(20%)}" # Visited links
```

### Semantic Colors

```yaml
colors:
  # Status colors
  success: "#059669"           # Success states (Emerald 600)
  success_light: "#D1FAE5"     # Success backgrounds (Emerald 100)
  
  warning: "#D97706"           # Warning states (Amber 600)  
  warning_light: "#FEF3C7"     # Warning backgrounds (Amber 100)
  
  error: "#DC2626"             # Error states (Red 600)
  error_light: "#FEE2E2"       # Error backgrounds (Red 100)
  
  info: "#2563EB"              # Info states (Blue 600)
  info_light: "#DBEAFE"        # Info backgrounds (Blue 100)
```

### UI Component Colors

```yaml
colors:
  # Borders
  border_default: "#E2E8F0"    # Default borders (Slate 200)
  border_muted: "#F1F5F9"      # Subtle borders (Slate 100)
  border_strong: "#94A3B8"     # Prominent borders (Slate 400)
  
  # Interactive elements
  button_primary: "{primary}"   # Primary buttons
  button_secondary: "{neutral}" # Secondary buttons
  button_hover: "{primary.darken(10%)}" # Button hover states
  
  # Form elements
  input_background: "#FFFFFF"   # Input backgrounds
  input_border: "#D1D5DB"      # Input borders (Gray 300)
  input_focus: "{primary}"      # Focus states
```

### Extended Color Palette

```yaml
colors:
  # Generated color scales (50-900)
  primary_50: "{primary.lighten(45%)}"
  primary_100: "{primary.lighten(40%)}"
  primary_200: "{primary.lighten(30%)}"
  primary_300: "{primary.lighten(20%)}"
  primary_400: "{primary.lighten(10%)}"
  primary_500: "{primary}"              # Base
  primary_600: "{primary.darken(10%)}"
  primary_700: "{primary.darken(20%)}"
  primary_800: "{primary.darken(30%)}"
  primary_900: "{primary.darken(40%)}"
```

## Typography Variables

### Font Families

```yaml
fonts:
  # Core font stack
  heading: "Inter"             # Headlines and titles
  body: "Inter"                # Body text and paragraphs
  monospace: "JetBrains Mono"  # Code and data
  
  # Font stacks with fallbacks
  heading_stack: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
  body_stack: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
  monospace_stack: "JetBrains Mono, 'Fira Code', Consolas, 'Courier New', monospace"
```

### Font Sizes

```yaml
typography:
  # Base settings
  base_size: "16pt"            # Base font size
  scale_ratio: 1.25            # Modular scale ratio (major third)
  
  # Size scale
  font_size_xs: "10pt"         # Extra small
  font_size_sm: "12pt"         # Small  
  font_size_base: "16pt"       # Base/default
  font_size_lg: "20pt"         # Large
  font_size_xl: "24pt"         # Extra large
  font_size_2xl: "30pt"        # 2X large
  font_size_3xl: "36pt"        # 3X large
  font_size_4xl: "48pt"        # 4X large
  font_size_5xl: "60pt"        # 5X large
  font_size_6xl: "72pt"        # 6X large
```

### Font Weights

```yaml
typography:
  # Weight scale
  font_weight_thin: 100
  font_weight_light: 300
  font_weight_normal: 400      # Regular/default
  font_weight_medium: 500
  font_weight_semibold: 600
  font_weight_bold: 700
  font_weight_extrabold: 800
  font_weight_black: 900
```

### Line Heights

```yaml
typography:
  # Line height ratios
  line_height_none: 1          # Tight headings
  line_height_tight: 1.2       # Headings
  line_height_snug: 1.375      # Subheadings
  line_height_normal: 1.5      # Body text
  line_height_relaxed: 1.625   # Comfortable reading
  line_height_loose: 2         # Very loose
```

### Letter Spacing

```yaml
typography:
  # Letter spacing (tracking)
  letter_spacing_tighter: "-0.05em"
  letter_spacing_tight: "-0.025em"  
  letter_spacing_normal: "0em"      # Default
  letter_spacing_wide: "0.025em"
  letter_spacing_wider: "0.05em"
  letter_spacing_widest: "0.1em"
```

## Spacing Variables

### Base Spacing Scale

```yaml
spacing:
  # Base unit (8pt grid)
  unit: "8pt"
  
  # Spacing scale
  spacing_0: "0pt"             # No spacing
  spacing_px: "1pt"            # 1 pixel
  spacing_0_5: "2pt"           # 0.5 * unit
  spacing_1: "4pt"             # 0.5 * unit  
  spacing_1_5: "6pt"           # 0.75 * unit
  spacing_2: "8pt"             # 1 * unit
  spacing_2_5: "10pt"          # 1.25 * unit
  spacing_3: "12pt"            # 1.5 * unit
  spacing_3_5: "14pt"          # 1.75 * unit
  spacing_4: "16pt"            # 2 * unit
  spacing_5: "20pt"            # 2.5 * unit
  spacing_6: "24pt"            # 3 * unit
  spacing_7: "28pt"            # 3.5 * unit
  spacing_8: "32pt"            # 4 * unit
  spacing_9: "36pt"            # 4.5 * unit
  spacing_10: "40pt"           # 5 * unit
  spacing_11: "44pt"           # 5.5 * unit
  spacing_12: "48pt"           # 6 * unit
  spacing_14: "56pt"           # 7 * unit
  spacing_16: "64pt"           # 8 * unit
  spacing_20: "80pt"           # 10 * unit
  spacing_24: "96pt"           # 12 * unit
  spacing_28: "112pt"          # 14 * unit
  spacing_32: "128pt"          # 16 * unit
```

### Semantic Spacing

```yaml
spacing:
  # Content spacing
  content_gap_xs: "{spacing_2}"      # 8pt - tight content
  content_gap_sm: "{spacing_4}"      # 16pt - normal content
  content_gap_md: "{spacing_6}"      # 24pt - comfortable spacing
  content_gap_lg: "{spacing_8}"      # 32pt - generous spacing
  
  # Component spacing
  component_gap_xs: "{spacing_1}"    # 4pt - tight components
  component_gap_sm: "{spacing_2}"    # 8pt - normal components  
  component_gap_md: "{spacing_4}"    # 16pt - spaced components
  component_gap_lg: "{spacing_6}"    # 24pt - loose components
```

## Layout Variables

### Page Layout

```yaml
layout:
  # Page dimensions
  page_width_letter: "8.5in"         # US Letter width
  page_height_letter: "11in"         # US Letter height
  page_width_a4: "210mm"             # A4 width
  page_height_a4: "297mm"            # A4 height
  
  # Margins
  margin_narrow: "0.5in"             # Narrow margins
  margin_normal: "1in"               # Standard margins
  margin_wide: "1.5in"               # Wide margins
  
  # Content areas
  content_width_narrow: "6in"       # Narrow content
  content_width_normal: "6.5in"     # Standard content
  content_width_wide: "7.5in"       # Wide content
```

### Grid System

```yaml
layout:
  # Grid settings
  grid_columns: 12                   # 12-column grid
  grid_gutter: "{spacing_6}"         # 24pt gutters
  grid_margin: "{spacing_8}"         # 32pt margins
  
  # Container widths
  container_sm: "640pt"              # Small container
  container_md: "768pt"              # Medium container
  container_lg: "1024pt"             # Large container
  container_xl: "1280pt"             # Extra large container
```

### Border and Radius

```yaml
layout:
  # Border widths
  border_width_0: "0pt"
  border_width_1: "1pt"              # Default border
  border_width_2: "2pt"              # Medium border
  border_width_4: "4pt"              # Thick border
  border_width_8: "8pt"              # Very thick border
  
  # Border radius
  border_radius_none: "0pt"
  border_radius_sm: "2pt"            # Small radius
  border_radius_default: "4pt"       # Default radius
  border_radius_md: "6pt"            # Medium radius
  border_radius_lg: "8pt"            # Large radius
  border_radius_xl: "12pt"           # Extra large radius
  border_radius_2xl: "16pt"          # 2X large radius
  border_radius_full: "9999pt"       # Fully rounded
```

## Shadow Variables

```yaml
shadows:
  # Elevation shadows
  shadow_sm: "0 1pt 2pt 0 rgba(0, 0, 0, 0.05)"           # Small shadow
  shadow_default: "0 1pt 3pt 0 rgba(0, 0, 0, 0.1), 0 1pt 2pt 0 rgba(0, 0, 0, 0.06)" # Default
  shadow_md: "0 4pt 6pt -1pt rgba(0, 0, 0, 0.1), 0 2pt 4pt -1pt rgba(0, 0, 0, 0.06)" # Medium
  shadow_lg: "0 10pt 15pt -3pt rgba(0, 0, 0, 0.1), 0 4pt 6pt -2pt rgba(0, 0, 0, 0.05)" # Large
  shadow_xl: "0 20pt 25pt -5pt rgba(0, 0, 0, 0.1), 0 10pt 10pt -5pt rgba(0, 0, 0, 0.04)" # XL
  shadow_2xl: "0 25pt 50pt -12pt rgba(0, 0, 0, 0.25)"    # 2X large
  shadow_inner: "inset 0 2pt 4pt 0 rgba(0, 0, 0, 0.06)"  # Inner shadow
```

## Animation Variables

```yaml
animation:
  # Duration
  duration_75: "75ms"               # Very fast
  duration_100: "100ms"             # Fast
  duration_150: "150ms"             # Quick
  duration_200: "200ms"             # Normal
  duration_300: "300ms"             # Medium
  duration_500: "500ms"             # Slow
  duration_700: "700ms"             # Slower
  duration_1000: "1000ms"           # Very slow
  
  # Easing functions
  ease_linear: "linear"
  ease_in: "cubic-bezier(0.4, 0, 1, 1)"
  ease_out: "cubic-bezier(0, 0, 0.2, 1)"
  ease_in_out: "cubic-bezier(0.4, 0, 0.2, 1)"
```

## Asset Variables

```yaml
assets:
  # Default asset paths
  logo_path: "assets/logo.png"
  logo_white_path: "assets/logo-white.png"
  favicon_path: "assets/favicon.png"
  background_path: "assets/background.png"
  watermark_path: "assets/watermark.png"
  
  # Asset dimensions
  logo_width: "200pt"
  logo_height: "60pt"
  favicon_size: "32pt"
  
  # Asset positioning
  logo_position: "bottom-right"
  watermark_position: "center"
  watermark_opacity: 0.1
```

## Accessibility Variables

```yaml
accessibility:
  # Contrast ratios
  contrast_ratio_aa: 4.5            # WCAG 2.1 AA standard
  contrast_ratio_aaa: 7.0           # WCAG 2.1 AAA standard
  
  # Font sizes
  min_font_size: "12pt"             # Minimum readable size
  comfortable_font_size: "16pt"     # Comfortable reading size
  large_font_size: "20pt"           # Large print size
  
  # Focus indicators
  focus_outline_width: "2pt"
  focus_outline_color: "{primary}"
  focus_outline_style: "solid"
  
  # Touch targets
  min_touch_target: "44pt"          # Minimum touch target size
  recommended_touch_target: "48pt"   # Recommended touch target
```

## Office-Specific Variables

### PowerPoint Variables

```yaml
powerpoint:
  # Slide dimensions
  slide_width: "10in"               # Standard slide width
  slide_height: "7.5in"             # Standard slide height
  slide_width_widescreen: "13.33in" # Widescreen width
  slide_height_widescreen: "7.5in"  # Widescreen height
  
  # Title sizes
  slide_title_size: "44pt"          # Main slide titles
  slide_subtitle_size: "24pt"       # Slide subtitles
  slide_content_size: "20pt"        # Slide content text
  
  # Slide margins
  slide_margin_top: "0.5in"
  slide_margin_bottom: "0.5in"
  slide_margin_left: "0.5in"
  slide_margin_right: "0.5in"
```

### Word Variables

```yaml
word:
  # Document settings
  line_height_body: 1.15            # Single line spacing
  line_height_title: 1.0            # Title line spacing
  
  # Heading sizes
  heading_1_size: "28pt"            # H1 size
  heading_2_size: "22pt"            # H2 size
  heading_3_size: "18pt"            # H3 size
  heading_4_size: "16pt"            # H4 size
  heading_5_size: "14pt"            # H5 size
  heading_6_size: "12pt"            # H6 size
  
  # Paragraph spacing
  paragraph_spacing_before: "6pt"
  paragraph_spacing_after: "6pt"
  
  # List settings
  bullet_indent: "0.25in"
  number_indent: "0.25in"
```

### Excel Variables

```yaml
excel:
  # Cell settings
  cell_height: "15pt"               # Default row height
  cell_width: "64pt"                # Default column width
  
  # Header settings
  header_height: "18pt"             # Header row height
  header_font_size: "11pt"          # Header font size
  header_font_weight: 700           # Bold headers
  
  # Border settings
  grid_border_width: "0.5pt"        # Grid line width
  grid_border_color: "{border_default}" # Grid line color
  
  # Alternating row colors
  row_even_background: "{surface}"
  row_odd_background: "{surface_secondary}"
```

## Usage Examples

### Token References

```yaml
# Reference other tokens
colors:
  primary: "#2563EB"
  link_color: "{primary}"           # Use primary color
  button_hover: "{primary.darken(10%)}" # Darker version
  
# Complex references
layout:
  content_padding: "{spacing_4} {spacing_6}" # "16pt 24pt"
  
# Conditional references
typography:
  heading_size:
    desktop: "{font_size_2xl}"      # 30pt
    mobile: "{font_size_xl}"        # 24pt
```

### Custom Variables

```yaml
# Add custom variables
custom:
  brand_gradient: "linear-gradient(45deg, {primary}, {secondary})"
  shadow_brand: "0 4pt 8pt {primary.alpha(20%)}"
  
# Use in templates
backgrounds:
  hero_background: "{custom.brand_gradient}"
```

## Variable Validation

```bash
# Validate all variables
python tools/validate-variables.py --org your-org

# Check specific variable types
python tools/validate-variables.py --type colors --org your-org
python tools/validate-variables.py --type typography --org your-org

# Test variable references
python tools/test-references.py --token "colors.primary" --org your-org
```

## Next Steps

- [Learn customization techniques](./customization.md)
- [Understand the token hierarchy](./hierarchy.md)  
- [See variables in action](../examples/university.md)
- [Explore API reference](../api/token-resolver.md)