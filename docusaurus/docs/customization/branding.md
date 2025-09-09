---
sidebar_position: 1
---

# Branding Integration

Learn how to integrate your organization's brand identity into StyleStack templates while maintaining professional quality and accessibility standards. This guide covers logo integration, color systems, typography, and brand consistency.

## Brand Asset Preparation

### Logo Requirements

#### File Formats and Specifications

**Primary Logo (Required):**
```
Format: PNG with transparency
Dimensions: 300-600px width (maintain aspect ratio)
Resolution: 300 DPI minimum
File size: <1MB for performance
Color mode: RGB for screen display
```

**Logo Variants (Recommended):**
```
org/your-org/assets/logos/
├─ primary-logo.png          # Full color on light backgrounds
├─ primary-logo-white.png    # White version for dark backgrounds  
├─ primary-logo-black.png    # Black version for light backgrounds
├─ logo-horizontal.png       # Horizontal layout variant
├─ logo-square.png           # Square/icon version
└─ logo-monochrome.png       # Single color version
```

#### Logo Optimization

```bash
# Optimize logos for template use
python tools/optimize-logo.py \
  --input "org/your-org/assets/logos/primary-logo.png" \
  --output "org/your-org/assets/logos/optimized/" \
  --max-size 1MB \
  --formats png,svg

# Generate logo variants automatically
python tools/generate-logo-variants.py \
  --source "primary-logo.png" \
  --output-dir "org/your-org/assets/logos/" \
  --variants "white,black,monochrome"
```

### Brand Colors

#### Color Palette Definition

```json
# org/your-org/patches.json
colors:
  # Primary brand colors (from brand guidelines)
  brand:
    primary: "#1E40AF"          # Corporate blue
    secondary: "#3B82F6"        # Light blue
    accent: "#F59E0B"           # Orange highlight
    neutral: "#6B7280"          # Corporate gray
    
  # Extended palette (generated from primary)
  brand_extended:
    primary_50: "#EFF6FF"       # Very light tint
    primary_100: "#DBEAFE"      # Light tint
    primary_200: "#BFDBFE"      # Medium light
    primary_500: "#1E40AF"      # Base (same as brand.primary)
    primary_700: "#1D4ED8"      # Dark
    primary_900: "#1E3A8A"      # Very dark
    
  # Semantic color mapping  
  primary: "{brand.primary}"
  secondary: "{brand.secondary}"
  accent: "{brand.accent}"
```

#### Color System Implementation

```json
# Advanced color system with brand intelligence
colors:
  # Brand color relationships
  brand_relationships:
    complementary: "{brand.primary.complement()}"     # Orange (opposite on color wheel)
    analogous_1: "{brand.primary.analogous(30)}"      # Blue-green
    analogous_2: "{brand.primary.analogous(-30)}"     # Blue-purple
    triadic_1: "{brand.primary.triadic(120)}"         # Red
    triadic_2: "{brand.primary.triadic(240)}"         # Green
    
  # Contextual brand colors
  success: "{brand.primary.mix(#10B981, 30%)}"        # Brand-influenced green
  warning: "{brand.accent}"                            # Use brand accent for warnings
  error: "#EF4444"                                    # Keep standard red for safety
  info: "{brand.secondary}"                           # Use secondary brand color
```

### Typography System

#### Brand Font Integration

```json
# org/your-org/patches.json
fonts:
  # Brand typography hierarchy
  brand:
    primary: "Montserrat"       # Primary brand font
    secondary: "Open Sans"      # Secondary brand font  
    accent: "Playfair Display"  # Accent font for special use
    
  # Font role mapping
  heading: "{fonts.brand.primary}"
  body: "{fonts.brand.secondary}"
  display: "{fonts.brand.accent}"       # For large titles, headers
  
  # Font stacks with fallbacks
  heading_stack: "Montserrat, 'Helvetica Neue', Arial, sans-serif"
  body_stack: "Open Sans, 'Segoe UI', Roboto, Arial, sans-serif"
  display_stack: "Playfair Display, Georgia, Times, serif"
```

#### Custom Font Loading

```json
# For organizations with licensed fonts
fonts:
  # Custom font files
  custom_fonts:
    - family: "AcmeSans"
      files:
        regular: "assets/fonts/AcmeSans-Regular.ttf"
        bold: "assets/fonts/AcmeSans-Bold.ttf"
        italic: "assets/fonts/AcmeSans-Italic.ttf"
      license: "Corporate license 2024-2027"
      
  # Font loading strategy
  loading:
    strategy: "progressive"     # Load web fonts first, fallback to system
    timeout: "3000ms"          # 3 second timeout
    display: "swap"            # Immediate fallback, swap when loaded
```

## Logo Integration

### PowerPoint Logo Placement

```json
# org/your-org/channels/presentation.json
logo_configuration:
  slide_master:
    position: "bottom-right"
    size: 
      width: "2in"
      height: "0.6in"
    margin:
      right: "0.5in"
      bottom: "0.25in"
      
  title_slide:
    position: "center-bottom"
    size:
      width: "3in"
      height: "0.9in"
    margin:
      bottom: "1in"
      
  # Logo variants by slide type
  logo_variants:
    light_backgrounds: "primary-logo.png"
    dark_backgrounds: "primary-logo-white.png"
    section_slides: "logo-horizontal.png"
```

### Word Document Headers

```json
# org/your-org/channels/document.json
document_branding:
  header:
    logo:
      position: "right"
      size:
        width: "1.5in"
        height: "0.45in"
      margin:
        right: "0.5in"
        top: "0.25in"
        
    text:
      organization_name: "{organization.name}"
      font: "{fonts.heading}"
      size: "14pt"
      color: "{colors.primary}"
      
  footer:
    elements:
      - "page_number"
      - "document_title"  
      - "confidentiality_notice"
    font: "{fonts.body}"
    size: "9pt"
    color: "{colors.text_secondary}"
```

### Excel Branding

```json
# org/your-org/channels/finance.json
spreadsheet_branding:
  header_row:
    logo:
      cell: "A1"
      size: "fit_to_cell"
      max_height: "30pt"
      
    company_info:
      cells: "B1:D1"
      merge: true
      content: "{organization.name}"
      font: "{fonts.heading}"
      size: "16pt"
      
  theme_colors:
    # Map brand colors to Excel theme positions
    accent1: "{colors.primary}"
    accent2: "{colors.secondary}"
    accent3: "{colors.accent}"
    hyperlink: "{colors.primary}"
```

## Brand Consistency Guidelines

### Visual Hierarchy

```json
# org/your-org/brand-system.json
visual_hierarchy:
  # Logo prominence levels
  logo_prominence:
    high: 
      use_cases: ["external_presentations", "marketing_materials"]
      size_multiplier: 1.5
      positioning: "prominent"
      
    medium:
      use_cases: ["internal_presentations", "reports"]  
      size_multiplier: 1.0
      positioning: "standard"
      
    low:
      use_cases: ["internal_documents", "drafts"]
      size_multiplier: 0.7
      positioning: "subtle"
      
  # Typography hierarchy
  type_scale:
    display: "48pt"     # Hero headings
    h1: "36pt"          # Page titles
    h2: "24pt"          # Section headings
    h3: "20pt"          # Subsection headings
    h4: "16pt"          # Minor headings
    body: "14pt"        # Body text
    caption: "11pt"     # Captions, footnotes
```

### Brand Application Rules

```json
brand_rules:
  # Logo usage guidelines
  logo:
    minimum_size: "0.5in width"
    clear_space: "0.25in on all sides"
    backgrounds:
      approved: ["white", "light_gray", "primary_color"]
      prohibited: ["busy_images", "low_contrast_colors"]
      
  # Color usage guidelines  
  colors:
    primary_usage:
      - "headings_and_titles"
      - "call_to_action_elements"
      - "navigation_elements"
    secondary_usage:
      - "supporting_elements"
      - "background_accents" 
      - "border_elements"
    accent_usage:
      - "highlights_and_emphasis"
      - "warning_elements"
      - "interactive_states"
      
  # Typography guidelines
  typography:
    heading_font: "Always use brand primary font"
    body_font: "Use brand secondary font for readability"
    mixing_fonts: "Maximum 2 font families per document"
```

## Multi-Brand Management

### Brand Portfolio Support

```json
# org/your-org/multi-brand.json
brand_portfolio:
  brands:
    corporate:
      name: "Acme Corporation"
      colors:
        primary: "#1E40AF"
        secondary: "#3B82F6"
      logo: "assets/logos/acme-corporate.png"
      fonts:
        heading: "Montserrat"
        body: "Open Sans"
        
    consulting:
      name: "Acme Consulting"
      colors:
        primary: "#059669"
        secondary: "#10B981"
      logo: "assets/logos/acme-consulting.png"
      fonts:
        heading: "Inter" 
        body: "Inter"
        
    foundation:
      name: "Acme Foundation"
      colors:
        primary: "#7C3AED"
        secondary: "#A78BFA"  
      logo: "assets/logos/acme-foundation.png"
      fonts:
        heading: "Playfair Display"
        body: "Source Sans Pro"

  # Brand selection by channel
  channel_brand_mapping:
    corporate-presentation: "corporate"
    consulting-proposal: "consulting"
    foundation-report: "foundation"
```

### Brand Switching Logic

```json
# Conditional branding based on context
conditional_branding:
  rules:
    # Audience-based branding
    audience:
      internal:
        brand: "corporate"
        logo_prominence: "low"
      external_client:
        brand: "consulting"
        logo_prominence: "high"
      public_nonprofit:
        brand: "foundation"
        logo_prominence: "medium"
        
    # Department-based branding
    department:
      marketing: 
        brand: "corporate"
        emphasis: "brand_forward"
      finance:
        brand: "corporate"
        emphasis: "data_forward"
      hr:
        brand: "corporate" 
        emphasis: "people_forward"
```

## Brand Compliance and Quality Control

### Automated Brand Validation

```bash
# Brand compliance checking
python tools/brand-validator.py \
  --org your-org \
  --templates "*.potx,*.dotx,*.xltx" \
  --standards "brand-guidelines.json"

# Logo quality check
python tools/logo-validator.py \
  --logos "org/your-org/assets/logos/*" \
  --min-resolution 300 \
  --max-size 1MB \
  --required-formats png
```

### Brand Audit Reports

```python
# tools/brand-audit.py
class BrandAuditor:
    def __init__(self, org):
        self.org = org
        self.guidelines = load_brand_guidelines(org)
        
    def audit_templates(self):
        results = {
            'logo_compliance': self.check_logo_usage(),
            'color_compliance': self.check_color_accuracy(),
            'typography_compliance': self.check_font_usage(),
            'layout_compliance': self.check_layout_standards()
        }
        return self.generate_report(results)
        
    def check_color_accuracy(self):
        """Verify colors match brand guidelines within tolerance"""
        tolerance = 0.05  # 5% color deviation allowed
        # Implementation details...
```

### Quality Gates

```json
# .github/workflows/brand-quality-gate.yml
name: Brand Quality Gate

on:
  pull_request:
    paths: ['org/your-org/**']

jobs:
  brand-validation:
    runs-on: ubuntu-latest
    steps:
      - name: Validate Logo Assets
        run: python tools/validate-logos.py --org your-org
        
      - name: Check Color Compliance
        run: python tools/check-colors.py --org your-org --tolerance 5%
        
      - name: Typography Validation
        run: python tools/validate-fonts.py --org your-org
        
      - name: Build Templates
        run: python build.py --org your-org --validate
        
      - name: Visual Regression Test
        run: python tools/visual-test.py --org your-org --compare-to main
```

## Advanced Branding Features

### Dynamic Branding

```json
# Event-based branding changes
dynamic_branding:
  events:
    holiday_season:
      period: "2024-12-01 to 2024-12-31"
      modifications:
        accent_color: "#C41E3A"  # Holiday red
        logo_variant: "holiday-logo.png"
        
    company_anniversary:
      period: "2024-06-15 to 2024-06-22"
      modifications:
        accent_color: "#FFD700"  # Gold accent
        tagline: "Celebrating 25 Years"
        
    conference_branding:
      trigger: "conference_mode"
      modifications:
        logo: "conference-logo.png"
        colors:
          primary: "#1A202C"    # Conference theme
          accent: "#ED8936"
```

### Personalization Features

```json
# User-level customization within brand constraints
personalization:
  allowed_modifications:
    - "accent_color_selection"   # From approved palette
    - "layout_preferences"       # Predefined layouts only
    - "signature_block"          # Personal contact info
    
  restrictions:
    - "no_primary_color_changes"
    - "no_logo_modifications"
    - "no_font_changes"
    
  user_profiles:
    sales_team:
      default_channel: "client-presentation"
      signature_template: "sales-signature.html"
    executive_team:
      default_channel: "executive-presentation"
      logo_prominence: "high"
```

### Brand Evolution Support

```json
# Support for gradual brand transitions
brand_evolution:
  transition_period: "2024-01-01 to 2024-06-30"
  
  legacy_brand:
    colors:
      primary: "#1E3A8A"      # Old blue
    logo: "legacy-logo.png"
    
  new_brand:
    colors:
      primary: "#1E40AF"      # New blue  
    logo: "new-logo.png"
    
  # Gradual transition strategy
  rollout_phases:
    phase_1: "External materials first"
    phase_2: "Internal presentations" 
    phase_3: "All templates updated"
```

## Troubleshooting Brand Issues

### Common Problems

**Logo not displaying:**
```bash
# Check logo file paths
ls -la org/your-org/assets/logos/
# Verify file formats and sizes
file org/your-org/assets/logos/*.png
# Test logo loading
python tools/test-logo-loading.py --org your-org
```

**Colors not matching brand guidelines:**
```bash
# Validate color values
python tools/color-validator.py --org your-org --reference brand-colors.json
# Check color space conversion
python tools/color-space-check.py --colors "#1E40AF,#3B82F6"
```

**Fonts not loading correctly:**
```bash
# Check font availability
fc-list | grep -i "montserrat"
# Validate font files
python tools/font-validator.py --fonts org/your-org/assets/fonts/
```

### Brand Consistency Issues

**Visual inconsistencies across templates:**
- Run comprehensive brand audit
- Check for template inheritance issues
- Verify color profile consistency
- Test across different Office versions

**Performance issues with branded assets:**
- Optimize logo file sizes
- Use appropriate image formats
- Consider vectorized assets for scalability
- Implement asset caching strategies

## Next Steps

- [Implement localization features](./localization.md)
- [Set up compliance requirements](./compliance.md)  
- [Enhance accessibility](./accessibility.md)
- [Deploy branded templates](../deployment/ci-cd.md)