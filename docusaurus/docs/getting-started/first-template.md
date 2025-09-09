---
sidebar_position: 3
---

# Your First Template

Learn how to create, customize, and deploy your first StyleStack template. This guide walks through building a PowerPoint template with your organization's branding.

## Overview

You'll create a customized PowerPoint template that includes:
- Your organization's colors and fonts
- Brand-consistent slide layouts
- Accessibility-compliant design
- Professional styling that replaces Office defaults

## Step 1: Prepare Your Assets

### Required Assets
```
org/your-org/assets/
├─ logo.png           # Primary logo (recommended: 300x100px, PNG with transparency)
├─ logo-white.png     # White version for dark backgrounds  
├─ watermark.png      # Optional: Draft watermark (light opacity)
└─ background.png     # Optional: Branded slide background
```

### Asset Guidelines
- **Logo formats:** PNG with transparency preferred
- **Resolution:** 300 DPI for print quality
- **Color modes:** RGB for screen, CMYK versions for print
- **File sizes:** Keep under 1MB each for template performance

## Step 2: Define Your Brand Tokens

Create your organization's design token configuration:

```json
# org/your-org/patches.json
organization:
  name: "Acme Corporation"
  short_name: "acme"
  tagline: "Innovation Through Excellence"
  
branding:
  primary_color: "#1E3A8A"      # Corporate blue
  secondary_color: "#3B82F6"    # Lighter blue  
  accent_color: "#F59E0B"       # Orange accent
  neutral_dark: "#1F2937"       # Dark gray
  neutral_light: "#F3F4F6"      # Light gray
  
fonts:
  heading: "Montserrat"         # Bold, modern sans-serif
  body: "Open Sans"             # Readable body text
  accent: "Montserrat"          # For emphasis
  
typography:
  scale_ratio: 1.2              # Modular scale for font sizes
  line_height: 1.5              # Body text line height
  heading_line_height: 1.2      # Heading line height
```

## Step 3: Create Custom Channel

Define a custom channel for your organization's presentation style:

```json
# org/your-org/channels/corporate.json
name: "Corporate Presentations"
description: "Standard template for business presentations"
target_products: ["potx"]

# Layout preferences
layouts:
  title_slide:
    logo_position: "bottom-right"
    tagline_enabled: true
    
  content_slides:
    bullet_style: "modern"
    image_aspect_ratio: "16:9"
    
# Color scheme overrides
colors:
  slide_background: "#FFFFFF"
  text_primary: "{neutral_dark}"
  text_secondary: "{primary_color}"
  accent: "{accent_color}"
  
# Typography settings  
typography:
  title_size: "44pt"
  subtitle_size: "24pt" 
  body_size: "18pt"
  caption_size: "14pt"
```

## Step 4: Build Your Template

### Build Command
```bash
# Build your corporate PowerPoint template
python build.py --org acme --channel corporate --products potx

# Expected output
# BetterDefaults-acme-corporate-1.3.0.potx
```

### Build Process Details
The build system will:
1. **Load core baseline** - Community-maintained OOXML templates
2. **Apply organization patches** - Your branding and customizations  
3. **Process channel settings** - Corporate presentation preferences
4. **Inject assets** - Logos and brand elements
5. **Generate OOXML** - Create final .potx template file

### Verbose Build (for troubleshooting)
```bash
python build.py --org acme --channel corporate --products potx --verbose
```

## Step 5: Test Your Template

### Install and Test
1. **Double-click** `BetterDefaults-acme-corporate-1.3.0.potx`
2. **Save as template** in PowerPoint
3. **Create new presentation** using your template

### Verification Checklist
- ✅ Logo appears on title slide
- ✅ Corporate colors applied throughout
- ✅ Font families load correctly  
- ✅ Slide layouts are professional
- ✅ Accessibility contrast ratios met
- ✅ Consistent spacing and alignment

## Step 6: Customize Layouts

### Add Custom Slide Master
Edit your patches.json to customize slide layouts:

```json
# Add to org/your-org/patches.json
slide_masters:
  corporate:
    title_slide:
      background_color: "{primary_color}"
      logo_position: "bottom-center"
      text_color: "#FFFFFF"
      
    content_slide:
      header_color: "{primary_color}"
      bullet_color: "{accent_color}"
      
    section_slide:
      background_gradient: 
        - "{primary_color}"
        - "{secondary_color}"
      text_color: "#FFFFFF"
```

### Rebuild with Changes
```bash
# Rebuild with new layouts
python build.py --org acme --channel corporate --products potx
```

## Step 7: Advanced Customizations

### Add Compliance Elements

```json
# Add regulatory compliance elements
compliance:
  gdpr:
    footer_text: "Confidential - GDPR Protected"
    privacy_notice: true
    
  sox:
    financial_disclaimer: "For internal use only"
    approval_required: true
```

### Multi-Language Support

```json
# Add localization
localization:
  primary_language: "en-US"
  supported_languages: ["en-US", "es-ES", "de-DE"]
  
  strings:
    en-US:
      confidential: "Confidential"
      draft: "Draft"
    es-ES:
      confidential: "Confidencial" 
      draft: "Borrador"
```

### Accessibility Enhancements

```json
# Improve accessibility
accessibility:
  high_contrast_mode: true
  dyslexic_friendly_fonts: true
  alt_text_required: true
  
  color_contrast:
    aa_compliant: true    # WCAG 2.1 AA
    aaa_preferred: true   # WCAG 2.1 AAA where possible
```

## Step 8: Create Template Variants

### Additional Channels
Create specialized variants for different use cases:

```bash
# External presentation channel
cat > org/acme/channels/external.json << EOF
name: "External Presentations"
description: "For client and public presentations"
target_products: ["potx"]

branding:
  logo_prominence: "high"
  contact_info: true
  
colors:
  slide_background: "{primary_color}"
  text_primary: "#FFFFFF"
EOF

# Build external variant
python build.py --org acme --channel external --products potx
```

### Word and Excel Templates
```bash
# Build complete office suite
python build.py --org acme --channel corporate --products potx dotx xltx

# Output:
# BetterDefaults-acme-corporate-1.3.0.potx (PowerPoint)
# BetterDefaults-acme-corporate-1.3.0.dotx (Word)
# BetterDefaults-acme-corporate-1.3.0.xltx (Excel)
```

## Step 9: Quality Validation

### Automated Testing
```bash
# Run template validation
python tools/validate.py --org acme --channel corporate --products potx

# Test accessibility compliance
python tools/validate.py --org acme --accessibility-check
```

### Manual Testing Checklist

**Visual Elements:**
- [ ] Logo placement and sizing
- [ ] Color consistency across slides
- [ ] Font loading and hierarchy
- [ ] Layout alignment and spacing

**Functionality:**
- [ ] All slide layouts available
- [ ] Theme colors work in shape fills
- [ ] Text styles apply correctly
- [ ] Animation compatibility

**Accessibility:**
- [ ] Color contrast ratios pass WCAG guidelines
- [ ] Font sizes meet minimum requirements  
- [ ] Focus indicators visible
- [ ] Screen reader compatibility

## Step 10: Distribution

### Version Control
```bash
# Commit your template configuration
git add org/acme/
git commit -m "Add Acme Corporation template configuration"

# Tag the version
git tag v1.0.0-acme
git push origin v1.0.0-acme
```

### Share with Team
```bash
# Create distribution package
zip -r acme-templates-v1.0.0.zip BetterDefaults-acme-*

# Upload to shared drive or internal repository
# Send installation instructions to team
```

## Troubleshooting

### Build Errors

**"Organization directory not found"**
```bash
# Verify directory structure
ls -la org/acme/
mkdir -p org/acme/assets
```

**"Asset file missing"**
```bash
# Check asset paths in patches.json
file org/acme/assets/logo.png
```

**"Invalid color format"**
```json
# Use hex colors with # prefix
primary_color: "#1E3A8A"  # Correct
primary_color: "1E3A8A"   # Wrong
```

### Template Issues

**Logo not appearing:**
- Verify PNG format and file size
- Check asset path in patches.json
- Ensure transparency preserved

**Colors not applying:**
- Validate hex color format
- Check for typos in color names
- Test with simple colors first

**Fonts not loading:**
- Install fonts system-wide before testing
- Use web-safe fallback fonts
- Check font licensing restrictions

## Next Steps

- [Learn design token hierarchy](../design-tokens/hierarchy.md)
- [Set up automated builds](../deployment/ci-cd.md)  
- [Explore organization examples](../examples/enterprise.md)
- [Add more customizations](../customization/branding.md)

## Resources

- [Design token reference](../design-tokens/variables.md)
- [OOXML processor docs](../api/ooxml-processor.md)
- [Community examples](https://github.com/stylestack/stylestack/discussions)
- [Template gallery](https://stylestack.github.io/gallery/)