---
sidebar_position: 2
---

# Customizing Your Fork

Learn how to safely customize your StyleStack fork for organizational branding while maintaining the ability to sync with upstream improvements. This guide covers best practices for sustainable customization.

## Customization Principles

### The Golden Rules

1. **Never modify core files** - Keep `core/` directory untouched
2. **Only customize in org directory** - All changes go in `org/your-org/`
3. **Use the patch system** - Leverage YAML-based overrides
4. **Document everything** - Explain rationale for customizations
5. **Test thoroughly** - Validate across Office versions

### Safe vs Unsafe Modifications

✅ **Safe (encouraged):**
```
org/your-org/
├─ patches.yaml          # Brand customizations
├─ assets/              # Logo, images, fonts
├─ channels/            # Custom use cases
└─ governance.yaml      # Approval rules
```

❌ **Unsafe (avoid):**
```
core/                   # Community baseline
.github/workflows/      # CI/CD (except org-specific)
tools/                  # Build system utilities
```

## Brand Customization

### Logo and Visual Identity

```yaml
# org/your-org/patches.yaml
organization:
  name: "Acme Corporation"
  short_name: "acme"
  tagline: "Innovation Through Excellence"
  domain: "acme.com"

branding:
  # Primary brand colors
  primary_color: "#1E40AF"      # Corporate blue
  secondary_color: "#3B82F6"    # Light blue
  accent_color: "#F59E0B"       # Orange highlight
  
  # Brand assets
  logo: "assets/acme-logo.png"
  logo_white: "assets/acme-logo-white.png"
  watermark: "assets/draft-watermark.png"
  
  # Logo specifications
  logo_width: "180pt"
  logo_height: "54pt"
  logo_position: "bottom-right"
  
fonts:
  # Corporate typography
  heading: "Montserrat"         # Modern sans-serif
  body: "Open Sans"             # Readable body text
  monospace: "Fira Code"        # Code/data display
```

### Asset Management

```bash
# Organize brand assets
mkdir -p org/acme/assets/{logos,backgrounds,fonts,icons}

# Logo variants (recommended formats)
org/acme/assets/logos/
├─ acme-logo.png              # Primary logo (color, transparent)
├─ acme-logo-white.png        # White version for dark backgrounds
├─ acme-logo-black.png        # Black version for light backgrounds  
├─ acme-logo-mono.png         # Monochrome version
└─ acme-seal.png              # Official seal/emblem

# Backgrounds and textures
org/acme/assets/backgrounds/
├─ slide-background.png       # Branded slide background
├─ watermark.png              # Document watermark
└─ letterhead-bg.png          # Document header background

# Custom fonts (if licensed)
org/acme/assets/fonts/
├─ AcmeSans-Regular.ttf
├─ AcmeSans-Bold.ttf  
└─ AcmeSerif-Regular.ttf
```

### Asset Optimization

```bash
# Optimize images for template performance
python tools/optimize-assets.py --org acme --target-size 1MB --dpi 300

# Generate asset variants automatically
python tools/generate-variants.py --org acme --logo "assets/logos/acme-logo.png"
```

## Typography Customization

### Font Selection Strategy

```yaml
# org/acme/patches.yaml
fonts:
  # Web fonts (Google Fonts)
  heading: "Montserrat"
  body: "Open Sans"
  
  # Font stacks with fallbacks
  heading_stack: "Montserrat, 'Helvetica Neue', Arial, sans-serif"
  body_stack: "Open Sans, 'Segoe UI', Roboto, Arial, sans-serif"
  
  # Custom fonts (if licensed)
  brand_heading: "AcmeSans"
  brand_body: "AcmeSerif"
  
typography:
  # Size scale optimized for brand
  scale_ratio: 1.2              # Subtle contrast
  base_size: "16pt"             # Readable default
  
  # Line height for readability
  body_line_height: 1.6         # Comfortable reading
  heading_line_height: 1.2      # Tight headings
```

### Font Licensing Considerations

```yaml
# Document font licensing
fonts:
  licensing:
    google_fonts: ["Montserrat", "Open Sans"]  # Free for commercial use
    adobe_fonts: ["AcmeSans"]                  # Requires Adobe subscription
    custom_fonts: ["AcmeSerif"]                # Organizational license
    
  fallbacks:
    # Ensure fallbacks are universally available
    system_fonts: ["Arial", "Helvetica", "Calibri"]
```

## Color System Customization

### Brand Color Palette

```yaml
# org/acme/patches.yaml
colors:
  # Primary brand colors
  brand:
    navy: "#1E40AF"             # Corporate navy
    blue: "#3B82F6"             # Accent blue  
    orange: "#F59E0B"           # Highlight orange
    gray: "#6B7280"             # Neutral gray
    
  # Semantic color mapping
  primary: "{brand.navy}"
  secondary: "{brand.blue}"
  accent: "{brand.orange}"
  neutral: "{brand.gray}"
  
  # Generated color scales
  primary_light: "{primary.lighten(20%)}"
  primary_dark: "{primary.darken(20%)}"
  primary_transparent: "{primary.alpha(50%)}"
  
  # Contextual colors
  success: "{brand.blue.mix(#10B981, 30%)}"    # Brand-influenced green
  warning: "{brand.orange}"                     # Use brand orange
  error: "#EF4444"                             # Standard red (safety)
```

### Accessibility-First Colors

```yaml
colors:
  # Ensure WCAG compliance
  text_on_primary: auto         # Automatically white or black
  text_on_secondary: auto       # Based on contrast ratio
  
accessibility:
  contrast_validation: true     # Enable contrast checking
  min_contrast_ratio: 4.5       # WCAG AA standard
  
  # High contrast variants
  high_contrast:
    enabled: true
    primary: "{primary.darken(30%)}"
    text: "#000000"
```

## Layout and Spacing

### Grid System Customization

```yaml
# org/acme/patches.yaml
layout:
  # Corporate grid system
  spacing_unit: "12pt"          # Larger base unit
  
  # Page margins (generous for binding)
  margins:
    top: "1.5in"
    right: "1.25in"
    bottom: "1.5in"
    left: "1.5in"               # Extra space for binding
    
  # Content widths
  content_width: "7in"          # Conservative for readability
  line_length: "75ch"           # Longer lines acceptable for corp docs
```

### Slide Layouts

```yaml
# org/acme/channels/presentation.yaml
layouts:
  # Title slide customization
  title_slide:
    logo_position: "bottom-center"
    logo_size: "large"
    background: "{brand.navy}"
    text_color: "#FFFFFF"
    tagline_enabled: true
    
  # Content slide layouts  
  content_slide:
    header_bar: true            # Brand bar at top
    header_color: "{brand.navy}"
    logo_corner: true           # Small logo in corner
    
  # Section divider
  section_slide:
    background: "gradient"      # Navy to blue gradient
    text_alignment: "center"
    large_text: true
```

## Channel-Specific Customization

### Presentation Channel

```yaml
# org/acme/channels/corporate-presentation.yaml
name: "Corporate Presentations"
description: "For executive presentations and client meetings"
target_products: ["potx"]

branding:
  prominence: "high"            # Prominent branding
  logo_on_every_slide: true
  
typography:
  # Larger fonts for projection
  base_size: "24pt"
  title_size: "48pt"
  
colors:
  # High contrast for projection
  slide_background: "{brand.navy}"
  text_primary: "#FFFFFF"
  accent: "{brand.orange}"
  
templates:
  - "executive-summary"
  - "financial-overview"
  - "strategic-initiative"
  - "quarterly-results"
```

### Document Channel

```yaml
# org/acme/channels/corporate-document.yaml  
name: "Corporate Documents"
description: "For reports, memos, and formal documentation"
target_products: ["dotx"]

compliance:
  # Document requirements
  header_required: true
  footer_required: true
  page_numbers: true
  confidentiality_notice: true
  
formatting:
  # Professional document styling
  heading_numbering: true
  table_of_contents: true
  bibliography_style: "APA"
  
templates:
  - "executive-memo"
  - "technical-report" 
  - "policy-document"
  - "meeting-minutes"
```

### Finance Channel

```yaml
# org/acme/channels/finance.yaml
name: "Financial Templates"
description: "For financial reports and analysis"
target_products: ["xltx", "potx"]

formatting:
  # Financial number formatting
  currency_symbol: "$"
  decimal_places: 2
  thousands_separator: ","
  
  # Table styling
  alternating_rows: true
  header_emphasis: true
  total_row_highlight: true
  
colors:
  # Conservative colors for finance
  positive: "#10B981"          # Green for positive numbers
  negative: "#EF4444"          # Red for negative numbers
  neutral: "{brand.gray}"      # Gray for neutral data
```

## Compliance Customization

### Regulatory Requirements

```yaml
# org/acme/patches.yaml
compliance:
  # Industry regulations
  sox: true                    # Sarbanes-Oxley compliance
  gdpr: true                   # GDPR privacy compliance
  iso27001: true               # Information security
  
  # Automatic compliance elements
  confidentiality:
    footer_text: "CONFIDENTIAL - For Internal Use Only"
    watermark: "assets/confidential-watermark.png"
    
  document_control:
    version_tracking: true
    approval_workflow: true
    retention_policy: "7 years"
    
  accessibility:
    wcag_level: "AA"           # WCAG 2.1 AA compliance
    screen_reader_compatible: true
    alt_text_required: true
```

### Legal and Privacy

```yaml
compliance:
  legal:
    # Copyright and trademark notices
    copyright_notice: "© 2024 Acme Corporation. All rights reserved."
    trademark_policy: "assets/trademark-guidelines.pdf"
    
  privacy:
    # Privacy protection measures  
    data_classification: true
    gdpr_notice: "This document may contain personal data protected under GDPR"
    retention_schedule: "assets/retention-schedule.pdf"
```

## Advanced Customization

### Multi-Brand Support

```yaml
# org/acme/patches.yaml
multi_brand:
  enabled: true
  
  brands:
    acme_corp:
      name: "Acme Corporation"
      colors:
        primary: "#1E40AF"
      logo: "assets/acme-logo.png"
      
    acme_consulting:
      name: "Acme Consulting"  
      colors:
        primary: "#059669"
      logo: "assets/consulting-logo.png"
      
  # Brand selection via channel
  brand_mapping:
    corporate: "acme_corp"
    consulting: "acme_consulting"
```

### Conditional Customization

```yaml
# Different settings based on context
customization:
  conditions:
    # Internal vs external templates
    audience:
      internal:
        branding_intensity: "subtle"
        confidentiality_notices: true
      external:
        branding_intensity: "prominent"
        contact_information: true
        
    # Regional variations
    region:
      north_america:
        currency: "$"
        date_format: "MM/DD/YYYY"
      europe:
        currency: "€"
        date_format: "DD/MM/YYYY"
```

### Dynamic Content

```yaml
# org/acme/dynamic.yaml
dynamic_content:
  # Auto-updated elements
  quarterly_data:
    source: "api.acme.com/quarterly-data"
    update_frequency: "monthly"
    
  employee_directory:
    source: "hr-system/directory"
    fields: ["name", "title", "department", "photo"]
    
  # Variable content
  placeholders:
    current_quarter: "Q4 2024"
    fiscal_year: "FY 2024"
    ceo_name: "Jane Smith"
    ceo_title: "Chief Executive Officer"
```

## Testing Customizations

### Automated Testing

```bash
# Build and validate all customizations
python build.py --org acme --all-channels --validate

# Test specific customization aspects
python tools/test-branding.py --org acme
python tools/test-compliance.py --org acme --regulation sox
python tools/test-accessibility.py --org acme --level AA
```

### Manual Testing Checklist

**Visual Consistency:**
- [ ] Brand colors applied consistently
- [ ] Logos positioned correctly  
- [ ] Typography hierarchy clear
- [ ] Spacing follows brand guidelines

**Functional Testing:**
- [ ] All templates build successfully
- [ ] Assets load in Office applications
- [ ] Colors display correctly on different screens
- [ ] Fonts render properly across platforms

**Compliance Testing:**
- [ ] Required legal notices present
- [ ] Accessibility standards met
- [ ] Document controls functional
- [ ] Privacy requirements satisfied

### Cross-Platform Validation

```bash
# Test across Office versions
python tools/test-office-versions.py --org acme --versions "2016,2019,365"

# Test cross-platform compatibility  
python tools/test-platforms.py --org acme --platforms "windows,mac,web"

# LibreOffice compatibility
python tools/test-libreoffice.py --org acme
```

## Version Control Best Practices

### Branching Strategy

```bash
# Feature branches for customizations
git checkout -b feature/quarterly-brand-update
git checkout -b feature/new-presentation-channel
git checkout -b compliance/gdpr-requirements

# Keep changes focused and atomic
git add org/acme/patches.yaml
git commit -m "Update brand colors for Q1 2024 guidelines"
```

### Change Documentation

```yaml
# Document customization rationale
# org/acme/CHANGELOG.md
## v2.1.0 - 2024-01-15

### Brand Updates
- Updated primary color to match new brand guidelines (#1234567)
- Added new presentation channel for investor relations
- Updated logo to include new tagline

### Compliance
- Added GDPR compliance notices to document templates
- Implemented SOX controls for financial templates

### Rationale
Brand refresh approved by CMO on 2024-01-10. Colors tested for
accessibility compliance and approved by legal team.
```

## Troubleshooting Common Issues

### Build Failures

```bash
# Debug customization issues
python build.py --org acme --debug --verbose

# Validate configuration syntax
python tools/validate-config.py --org acme

# Check asset availability
python tools/check-assets.py --org acme
```

### Merge Conflicts

```bash
# When syncing with upstream
git fetch upstream
git merge upstream/main

# Resolve conflicts in org files only
git checkout --ours org/acme/patches.yaml
git add org/acme/patches.yaml
git commit -m "Resolve upstream merge, keep org customizations"
```

## Next Steps

- [Learn upstream synchronization](./syncing-upstream.md)
- [Set up governance processes](./governance.md)
- [Deploy customized templates](../deployment/ci-cd.md)
- [Explore advanced examples](../examples/enterprise.md)