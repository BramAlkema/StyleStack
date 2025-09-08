---
sidebar_position: 1
---

# Design Tokens Overview

Design tokens are the foundation of StyleStack's consistent, scalable design system. They provide a structured way to manage colors, typography, spacing, and other design decisions across all Office templates while enabling organizational customization.

## What are Design Tokens?

Design tokens are named entities that store visual design attributes. Instead of hardcoding values like `#1E3A8A` or `18px` throughout templates, StyleStack uses semantic names like `{primary_color}` or `{body_font_size}`.

### Benefits

**Consistency:** Ensure the same blue appears everywhere it should  
**Maintainability:** Change one token value to update all instances  
**Scalability:** Add new products while maintaining visual coherence  
**Collaboration:** Designers and developers share a common vocabulary  
**Governance:** Control design decisions at the organizational level  

## Token Categories

### Color Tokens
```yaml
colors:
  primary: "#1E3A8A"        # Main brand color
  secondary: "#3B82F6"      # Supporting brand color  
  accent: "#F59E0B"         # Highlight/call-to-action
  neutral_dark: "#1F2937"   # Dark text/borders
  neutral_light: "#F3F4F6"  # Light backgrounds
  success: "#059669"        # Success states
  warning: "#D97706"        # Warning states  
  error: "#DC2626"          # Error states
```

### Typography Tokens
```yaml
fonts:
  heading: "Montserrat"     # Headlines and titles
  body: "Open Sans"         # Body text and paragraphs
  monospace: "Fira Code"    # Code and data
  
typography:
  scale_ratio: 1.25         # Modular scale multiplier
  base_size: "16pt"         # Base font size
  line_height: 1.5          # Body text line height
  heading_line_height: 1.2  # Heading line height
```

### Spacing Tokens
```yaml
spacing:
  unit: "8pt"              # Base spacing unit
  xs: "{unit * 0.5}"       # 4pt - tight spacing
  sm: "{unit}"             # 8pt - small spacing  
  md: "{unit * 2}"         # 16pt - medium spacing
  lg: "{unit * 3}"         # 24pt - large spacing
  xl: "{unit * 4}"         # 32pt - extra large
```

### Layout Tokens
```yaml
layout:
  page_margin: "{spacing.lg}"        # Standard page margins
  content_width: "8.5in"             # Page content width
  gutter: "{spacing.md}"             # Column gutters
  border_radius: "4pt"               # Rounded corners
  border_width: "1pt"                # Standard border width
```

## Token Resolution

StyleStack uses a hierarchical token resolution system that allows customization at multiple levels:

### 1. Core Tokens (Community Baseline)
```yaml
# core/tokens/base.yaml
colors:
  primary: "#2563EB"      # Community default blue
  text: "#1F2937"         # Dark gray for readability
fonts:
  body: "Inter"           # Modern, accessible font
```

### 2. Organization Tokens (Your Branding) 
```yaml  
# org/your-org/patches.yaml
colors:
  primary: "#1E3A8A"      # Override with your brand blue
  # text inherits from core
fonts:
  heading: "Montserrat"   # Override with your brand font
  # body inherits from core  
```

### 3. Channel Tokens (Use Case Variants)
```yaml
# org/your-org/channels/presentation.yaml
typography:
  base_size: "20pt"       # Larger fonts for projection
colors:
  accent: "#F59E0B"       # Brighter accent for slides
```

### Resolution Priority
1. **Channel tokens** (highest priority)
2. **Organization tokens** (medium priority)  
3. **Core tokens** (fallback)

## Token Types

### Simple Tokens
Direct value assignment:
```yaml
primary_color: "#1E3A8A"
heading_font: "Montserrat"
base_spacing: "8pt"
```

### Reference Tokens  
Reference other tokens:
```yaml
link_color: "{primary_color}"           # Use primary color
large_spacing: "{base_spacing * 3}"     # Calculate from base
text_on_primary: "{primary_color.contrast}"  # Auto-contrast
```

### Computed Tokens
Generated through functions:
```yaml
colors:
  primary: "#1E3A8A"
  primary_light: "{primary.lighten(20%)}"    # Lighten by 20%
  primary_dark: "{primary.darken(20%)}"      # Darken by 20%  
  primary_transparent: "{primary.alpha(50%)}" # 50% transparency
```

### Conditional Tokens
Vary based on context:
```yaml
text_color:
  light_theme: "#1F2937"     # Dark text on light background
  dark_theme: "#F9FAFB"      # Light text on dark background
  high_contrast: "#000000"   # Pure black for accessibility
```

## Token Usage in Templates

### PowerPoint Slide Master
```xml
<!-- OOXML with token placeholders -->
<a:solidFill>
  <a:srgbClr val="{primary_color}"/>
</a:solidFill>

<a:latin typeface="{heading_font}"/>
<a:sz val="{title_font_size}"/>
```

### Word Styles
```xml
<w:rFonts w:ascii="{body_font}" w:hAnsi="{body_font}"/>
<w:color w:val="{text_color}"/>
<w:sz w:val="{body_font_size}"/>
```

### Excel Themes
```xml
<a:dk1>
  <a:srgbClr val="{neutral_dark}"/>
</a:dk1>
<a:accent1>
  <a:srgbClr val="{primary_color}"/>
</a:accent1>
```

## Token Governance

### Organization-Level Control
```yaml
# org/your-org/governance.yaml
token_overrides:
  allowed:
    - "colors.*"           # Allow all color customization
    - "fonts.heading"      # Allow heading font changes
    - "spacing.unit"       # Allow spacing adjustments
    
  restricted:
    - "accessibility.*"    # Maintain accessibility standards
    - "compliance.*"       # Preserve compliance requirements
```

### Channel-Level Restrictions
```yaml
# Channels can only modify specific tokens
channel_permissions:
  presentation:
    - "typography.base_size"  # Font size for projection
    - "colors.accent"         # Presentation accent color
    
  document:
    - "layout.page_margin"    # Document margins
    - "typography.line_height" # Reading line height
```

## Accessibility Considerations

### WCAG-Compliant Color Tokens
```yaml
# Automatic contrast checking
colors:
  primary: "#1E3A8A"
  text_on_primary: auto    # Automatically white or black
  
accessibility:
  contrast_ratio: "AA"     # WCAG 2.1 AA compliance (4.5:1)
  # contrast_ratio: "AAA"  # WCAG 2.1 AAA compliance (7:1)
```

### Font Size Accessibility
```yaml
typography:
  min_font_size: "12pt"    # Never smaller than 12pt
  reading_font_size: "14pt" # Comfortable reading size
  large_print: "18pt"      # Large print option
```

## Token Documentation

### Semantic Naming
Use descriptive, purpose-driven names:

✅ **Good:**
```yaml
primary_color: "#1E3A8A"
heading_font: "Montserrat"
content_spacing: "16pt"
```

❌ **Bad:**  
```yaml
blue: "#1E3A8A"
font1: "Montserrat"  
spacing16: "16pt"
```

### Token Comments
Document token purposes:
```yaml
colors:
  primary: "#1E3A8A"           # Main brand color, used for headers, buttons, links
  secondary: "#3B82F6"         # Supporting color for backgrounds, inactive states  
  accent: "#F59E0B"            # Call-to-action color, warnings, highlights
  neutral_dark: "#1F2937"      # Primary text color, high-contrast elements
```

## Next Steps

- [Understand the token hierarchy](./hierarchy.md)
- [Learn customization techniques](./customization.md)  
- [Explore available variables](./variables.md)
- [See practical examples](../examples/university.md)

## Advanced Topics

- **Token validation** - Ensure tokens meet accessibility standards
- **Token testing** - Verify tokens across different Office versions
- **Token migration** - Update tokens while preserving compatibility
- **Token automation** - Generate tokens from brand guidelines