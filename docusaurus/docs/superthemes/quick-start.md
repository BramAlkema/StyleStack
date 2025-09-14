# SuperThemes Quick Start

Get started with StyleStack SuperThemes in under 5 minutes. This guide will walk you through creating your first multi-variant PowerPoint theme package.

## Prerequisites

- Python 3.8+ with StyleStack installed
- Basic understanding of JSON for design token configuration

## Step 1: Create Design Variants

Create a directory for your design variants and define your first design:

```bash
mkdir my_supertheme_designs
cd my_supertheme_designs
```

Create a design variant file `corporate_blue.json`:

```json
{
  "name": "Corporate Blue",
  "colors": {
    "brand": {
      "primary": "#0066CC",
      "secondary": "#4A90E2",
      "accent": "#FF6B35"
    },
    "neutral": {
      "dark": "#2C3E50",
      "medium": "#7F8C8D",
      "light": "#ECF0F1"
    }
  },
  "typography": {
    "heading": {
      "font": "Montserrat",
      "weight": "600",
      "size": {
        "$aspectRatio": {
          "aspectRatios.widescreen_16_9": "44pt",
          "aspectRatios.traditional_4_3": "40pt",
          "aspectRatios.a4_landscape": "38pt",
          "aspectRatios.letter_landscape": "38pt"
        }
      }
    },
    "body": {
      "font": "Source Sans Pro",
      "weight": "400",
      "size": {
        "$aspectRatio": {
          "aspectRatios.widescreen_16_9": "24pt",
          "aspectRatios.traditional_4_3": "22pt", 
          "aspectRatios.a4_landscape": "20pt",
          "aspectRatios.letter_landscape": "20pt"
        }
      }
    }
  },
  "spacing": {
    "margins": {
      "$aspectRatio": {
        "aspectRatios.widescreen_16_9": "72pt",
        "aspectRatios.traditional_4_3": "64pt",
        "aspectRatios.a4_landscape": "56pt",
        "aspectRatios.letter_landscape": "56pt"
      }
    }
  }
}
```

## Step 2: Generate Your SuperTheme

Use the StyleStack CLI to generate your SuperTheme package:

```bash
# Generate SuperTheme for all standard aspect ratios
python build.py --supertheme --designs my_supertheme_designs --ratios 16:9,4:3,a4,letter --out corporate_supertheme.thmx

# Generate for specific aspect ratios only
python build.py --supertheme --designs my_supertheme_designs --ratios 16:9,4:3 --out presentation_theme.thmx
```

**Expected Output:**
```
🎨 StyleStack SuperTheme Generator
📁 Loading design variants from: my_supertheme_designs
📐 Processing aspect ratios: 16:9, 4:3, A4, Letter
🔄 Generating design variants...
   ✅ Corporate Blue → 4 aspect ratio variants
📦 Packaging SuperTheme: corporate_supertheme.thmx
✅ Generated SuperTheme: 67 files, 0.03 MB
🔍 Validation: ✅ VALID (0 errors, 0 warnings)
```

## Step 3: Install in PowerPoint

1. **Copy to PowerPoint Themes Folder:**
   - **Windows**: `%AppData%\Microsoft\Templates\Document Themes`
   - **Mac**: `~/Library/Group Containers/UBF8T346G9.Office/User Content/Themes`

2. **Open PowerPoint** and create a new presentation

3. **Apply Your SuperTheme:**
   - Go to **Design** tab
   - Click **More** in the Themes gallery
   - Select your **Corporate Supertheme**

4. **Test Aspect Ratios:**
   - Go to **Design** → **Slide Size**
   - Switch between **Widescreen (16:9)** and **Standard (4:3)**
   - Notice how the theme adapts automatically!

## Step 4: Create Multiple Design Variants

Add more design variants to create a comprehensive theme family:

**Create `modern_green.json`:**
```json
{
  "name": "Modern Green",
  "colors": {
    "brand": {
      "primary": "#2ECC71",
      "secondary": "#27AE60",
      "accent": "#E67E22"
    }
  },
  "typography": {
    "heading": {
      "font": "Open Sans",
      "weight": "700"
    }
  }
}
```

**Create `elegant_purple.json`:**
```json
{
  "name": "Elegant Purple", 
  "colors": {
    "brand": {
      "primary": "#9B59B6",
      "secondary": "#8E44AD",
      "accent": "#F39C12"
    }
  },
  "typography": {
    "heading": {
      "font": "Playfair Display",
      "weight": "600"
    }
  }
}
```

**Regenerate with multiple variants:**
```bash
python build.py --supertheme --designs my_supertheme_designs --ratios 16:9,4:3,a4,letter --out multi_variant_supertheme.thmx
```

Your SuperTheme now contains 12 variants (3 designs × 4 aspect ratios)!

## Advanced Configuration

### Custom Aspect Ratios

Define custom aspect ratios for specialized presentations:

```bash
# Custom aspect ratio for ultra-wide screens
python build.py --supertheme --designs my_supertheme_designs --ratios 21:9 --out ultrawide_theme.thmx

# Multiple custom ratios
python build.py --supertheme --designs my_supertheme_designs --ratios 16:9,21:9,1:1 --out custom_ratios.thmx
```

### Token-Based Responsive Design

Use aspect ratio tokens to create truly responsive designs:

```json
{
  "layouts": {
    "title_slide": {
      "title_position": {
        "$aspectRatio": {
          "aspectRatios.widescreen_16_9": { "x": "1in", "y": "2in" },
          "aspectRatios.traditional_4_3": { "x": "0.8in", "y": "1.5in" },
          "aspectRatios.a4_landscape": { "x": "0.7in", "y": "1.3in" }
        }
      }
    }
  }
}
```

## Validation and Quality Assurance

StyleStack automatically validates your SuperThemes:

```bash
# Generate with verbose validation reporting
python build.py --supertheme --designs my_supertheme_designs --ratios 16:9,4:3 --out theme.thmx --verbose
```

**Validation checks include:**
- ✅ Office 2016-365 compatibility
- ✅ Package structure integrity
- ✅ XML schema compliance
- ✅ Cross-platform file path compatibility
- ✅ Performance optimization

## Troubleshooting

### Common Issues

**❌ "No design variants found"**
```bash
# Ensure JSON files are in the correct directory
ls my_supertheme_designs/*.json
```

**❌ "Invalid aspect ratio"**
```bash
# Use supported format: width:height
python build.py --supertheme --designs my_supertheme_designs --ratios 16:9,4:3  # ✅ Correct
python build.py --supertheme --designs my_supertheme_designs --ratios 16x9,4x3   # ❌ Wrong
```

**❌ PowerPoint doesn't show the theme**
- Check theme installation path
- Restart PowerPoint after copying theme files
- Verify .thmx file isn't corrupted (check file size > 0)

## Next Steps

🎉 **Congratulations!** You've created your first SuperTheme. Here's what to explore next:

- [**Architecture**](./architecture): Understand how SuperThemes work internally
- [**Design Variants**](./design-variants): Master advanced design token patterns  
- [**Aspect Ratios**](./aspect-ratios): Deep dive into responsive design systems
- [**Validation**](./validation): Learn about quality assurance features

## Example Repository

Check out our complete SuperTheme examples:
```bash
git clone https://github.com/stylestack/supertheme-examples
cd supertheme-examples
python build.py --supertheme --designs corporate --ratios 16:9,4:3 --out example.thmx
```