# Design Variants

Master the art of creating flexible, token-driven design systems that scale across multiple visual themes while maintaining consistency and brand compliance.

## Understanding Design Variants

Design variants are JSON-based configurations that define different visual treatments of your presentation themes. Each variant can specify colors, typography, spacing, and layout parameters that work seamlessly across all aspect ratios.

## Basic Design Variant Structure

### Minimal Example

```json
{
  "name": "Corporate Blue",
  "colors": {
    "brand": {
      "primary": "#0066CC"
    }
  }
}
```

### Complete Example

```json
{
  "name": "Corporate Professional",
  "description": "Professional corporate theme with blue color palette",
  "version": "1.2.0",
  "colors": {
    "brand": {
      "primary": "#0066CC",
      "secondary": "#4A90E2", 
      "accent": "#FF6B35",
      "success": "#27AE60",
      "warning": "#F39C12",
      "error": "#E74C3C"
    },
    "neutral": {
      "dark": "#2C3E50",
      "medium": "#7F8C8D",
      "light": "#ECF0F1",
      "white": "#FFFFFF"
    },
    "gradients": {
      "primary": {
        "start": "#0066CC",
        "end": "#004080",
        "direction": "135deg"
      }
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
          "aspectRatios.a4_landscape": "36pt",
          "aspectRatios.letter_landscape": "36pt"
        }
      },
      "line_height": "1.2",
      "letter_spacing": "-0.02em"
    },
    "subheading": {
      "font": "Montserrat",
      "weight": "400",
      "size": {
        "$aspectRatio": {
          "aspectRatios.widescreen_16_9": "32pt",
          "aspectRatios.traditional_4_3": "28pt",
          "aspectRatios.a4_landscape": "26pt",
          "aspectRatios.letter_landscape": "26pt"
        }
      }
    },
    "body": {
      "font": "Source Sans Pro",
      "weight": "400",
      "size": {
        "$aspectRatio": {
          "aspectRatios.widescreen_16_9": "20pt",
          "aspectRatios.traditional_4_3": "18pt",
          "aspectRatios.a4_landscape": "16pt",
          "aspectRatios.letter_landscape": "16pt"
        }
      },
      "line_height": "1.4"
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
    },
    "padding": {
      "small": "16pt",
      "medium": "24pt",
      "large": "32pt"
    }
  },
  "assets": {
    "logo": {
      "path": "assets/corporate_logo.png",
      "size": {
        "$aspectRatio": {
          "aspectRatios.widescreen_16_9": "2.5in",
          "aspectRatios.traditional_4_3": "2.2in"
        }
      }
    }
  }
}
```

## Token System Deep Dive

### Hierarchical Token Resolution

StyleStack resolves design tokens through a sophisticated hierarchy system:

```
1. Template-level overrides    (highest priority)
2. Channel-specific values     
3. Corporate brand defaults    
4. Global design system       (lowest priority)
```

**Example of hierarchical resolution:**
```json
{
  "colors": {
    "brand": {
      "primary": "#0066CC",                    // Global default
      "$channel": {
        "presentation": "#0052A3",             // Override for presentations
        "document": "#004080",                 // Override for documents
        "finance": "#1B4F72"                   // Override for finance channel
      },
      "$template": {
        "executive_summary": "#003366"         // Specific template override
      }
    }
  }
}
```

### Aspect Ratio Responsive Tokens

Create responsive designs that automatically adapt:

```json
{
  "layouts": {
    "title_slide": {
      "title_position": {
        "$aspectRatio": {
          "aspectRatios.widescreen_16_9": {
            "x": "1.5in",
            "y": "2in", 
            "width": "8in",
            "height": "1.5in"
          },
          "aspectRatios.traditional_4_3": {
            "x": "1.25in",
            "y": "1.75in",
            "width": "7.5in", 
            "height": "1.25in"
          }
        }
      }
    }
  }
}
```

### Conditional Logic System

Advanced conditional tokens for complex design logic:

```json
{
  "charts": {
    "bar_chart": {
      "layout": {
        "$conditional": {
          "if": {"$aspectRatio": "aspectRatios.widescreen_16_9"},
          "then": {
            "orientation": "horizontal",
            "legend_position": "right",
            "data_labels": true
          },
          "else": {
            "orientation": "vertical",
            "legend_position": "bottom",
            "data_labels": false
          }
        }
      }
    }
  }
}
```

## Design Variant Categories

### 1. Brand Variants

Different expressions of the same brand for various contexts:

**`corporate_formal.json`** - Executive presentations
```json
{
  "name": "Corporate Formal",
  "colors": {
    "brand": {"primary": "#1B4F72"},
    "neutral": {"dark": "#2C3E50"}
  },
  "typography": {
    "heading": {
      "font": "Times New Roman",
      "weight": "bold"
    }
  }
}
```

**`corporate_casual.json`** - Team meetings
```json
{
  "name": "Corporate Casual", 
  "colors": {
    "brand": {"primary": "#3498DB"},
    "neutral": {"dark": "#34495E"}
  },
  "typography": {
    "heading": {
      "font": "Open Sans",
      "weight": "600"
    }
  }
}
```

**`corporate_creative.json`** - Innovation workshops
```json
{
  "name": "Corporate Creative",
  "colors": {
    "brand": {"primary": "#9B59B6"},
    "accent": "#E67E22"
  },
  "typography": {
    "heading": {
      "font": "Montserrat",
      "weight": "700"
    }
  }
}
```

### 2. Functional Variants

Specialized designs for specific use cases:

**`financial_quarterly.json`** - Financial presentations
```json
{
  "name": "Financial Quarterly",
  "colors": {
    "data": {
      "positive": "#27AE60",
      "negative": "#E74C3C",
      "neutral": "#7F8C8D"
    }
  },
  "charts": {
    "emphasis": "data_driven",
    "colors": ["#2ECC71", "#E74C3C", "#3498DB", "#F39C12"]
  }
}
```

**`technical_documentation.json`** - Technical docs
```json
{
  "name": "Technical Documentation",
  "colors": {
    "code": {
      "background": "#F8F9FA", 
      "text": "#2C3E50",
      "keyword": "#9B59B6",
      "string": "#27AE60"
    }
  },
  "typography": {
    "code": {
      "font": "Fira Code",
      "size": "14pt"
    }
  }
}
```

### 3. Seasonal/Campaign Variants

Time-bound designs for special campaigns:

**`holiday_2024.json`** - Holiday campaign
```json
{
  "name": "Holiday 2024",
  "colors": {
    "seasonal": {
      "primary": "#C0392B",    // Holiday red
      "secondary": "#27AE60",   // Holiday green  
      "accent": "#F39C12"       // Gold accent
    }
  },
  "assets": {
    "seasonal_decorations": true,
    "holiday_fonts": ["Dancing Script", "Mountains of Christmas"]
  }
}
```

## Advanced Token Patterns

### 1. Token Inheritance

**Base variant (foundation):**
```json
{
  "name": "Corporate Base",
  "extends": "global_design_system_2025",
  "colors": {
    "brand": {
      "primary": "#0066CC",
      "secondary": "#4A90E2"
    }
  }
}
```

**Extended variant:**
```json
{
  "name": "Corporate Dark",
  "extends": "corporate_base.json",
  "colors": {
    "brand": {
      "primary": "#0080FF"      // Override only what changes
    },
    "background": "#1A1A1A",    // Add dark mode colors
    "text": "#FFFFFF"
  }
}
```

### 2. Token Computation

**Calculated color values:**
```json
{
  "colors": {
    "brand": {
      "primary": "#0066CC",
      "light": "$lighten(colors.brand.primary, 20%)",
      "dark": "$darken(colors.brand.primary, 15%)",
      "contrast": "$contrast(colors.brand.primary)"
    }
  }
}
```

**Dynamic spacing calculations:**
```json
{
  "spacing": {
    "base": "24pt",
    "small": "$multiply(spacing.base, 0.5)",    // 12pt
    "large": "$multiply(spacing.base, 2)",      // 48pt
    "responsive": {
      "$aspectRatio": {
        "aspectRatios.widescreen_16_9": "$multiply(spacing.base, 1.2)",
        "aspectRatios.traditional_4_3": "spacing.base"
      }
    }
  }
}
```

### 3. Token Validation

**Built-in validation:**
```json
{
  "$schema": "https://stylestack.com/schemas/design-variant.json",
  "name": "Validated Design",
  "colors": {
    "brand": {
      "primary": {
        "value": "#0066CC",
        "validation": {
          "contrast_ratio": ">=4.5",
          "accessibility": "WCAG_AA"
        }
      }
    }
  }
}
```

## Multi-Variant SuperTheme Generation

### Generating Multiple Variants

**Directory structure:**
```
my_design_variants/
├── corporate_blue.json
├── corporate_green.json
├── modern_purple.json
└── seasonal_holiday.json
```

**Generation command:**
```bash
python build.py --supertheme --designs my_design_variants --ratios 16:9,4:3 --out multi_variant.thmx
```

**Result**: SuperTheme with 8 variants (4 designs × 2 aspect ratios)

### Variant Organization Strategies

**By Department:**
```
designs/
├── executive/
│   ├── formal.json
│   └── board_meeting.json
├── marketing/
│   ├── campaign.json
│   └── social_media.json
└── engineering/
    ├── technical.json
    └── architecture.json
```

**By Use Case:**
```
designs/
├── presentations/
│   ├── keynote.json
│   └── team_update.json
├── documents/
│   ├── report.json
│   └── proposal.json
└── training/
    ├── workshop.json
    └── tutorial.json
```

## Best Practices

### 1. Consistent Naming Convention

**✅ Good naming:**
```json
{
  "name": "Corporate Primary Blue",          // Descriptive and specific
  "colors": {
    "brand_primary": "#0066CC",             // Semantic naming
    "brand_secondary": "#4A90E2",           
    "neutral_text": "#2C3E50"              // Purpose-based names
  }
}
```

**❌ Avoid:**
```json
{
  "name": "Blue Theme",                     // Too generic
  "colors": {
    "blue1": "#0066CC",                     // Non-semantic names  
    "blue2": "#4A90E2",
    "gray": "#2C3E50"
  }
}
```

### 2. Maintain Visual Hierarchy

**Establish clear relationships:**
```json
{
  "typography": {
    "h1": {"size": "44pt", "weight": "700"},
    "h2": {"size": "32pt", "weight": "600"},    // ~73% of h1
    "h3": {"size": "24pt", "weight": "600"},    // ~55% of h1
    "body": {"size": "18pt", "weight": "400"}   // ~41% of h1
  }
}
```

### 3. Design for Accessibility

**WCAG compliance:**
```json
{
  "colors": {
    "accessible_pairs": {
      "primary_on_white": {
        "foreground": "#0066CC",
        "background": "#FFFFFF",
        "contrast_ratio": "4.76"           // Meets WCAG AA (4.5:1)
      },
      "text_on_primary": {
        "foreground": "#FFFFFF",
        "background": "#0066CC", 
        "contrast_ratio": "8.18"          // Exceeds WCAG AAA (7:1)
      }
    }
  }
}
```

### 4. Test Across Devices

**Multi-device considerations:**
```json
{
  "responsive": {
    "high_dpi": {
      "font_adjustments": {
        "$conditional": {
          "if": {"$device": "retina"},
          "then": {"font_smoothing": "antialiased"},
          "else": {"font_smoothing": "auto"}
        }
      }
    }
  }
}
```

## Troubleshooting

### Common Issues

**❌ "Invalid JSON format"**
```bash
# Validate JSON syntax
python -m json.tool my_design.json
```

**❌ "Token resolution failed"**
```json
// Check for typos in token references
{
  "colors": {
    "primary": "#0066CC"
  },
  "typography": {
    "color": "colors.primary"      // ✅ Correct reference
    // "color": "color.primary"    // ❌ Typo would cause failure
  }
}
```

**❌ "Aspect ratio tokens not resolving"**
```json
// Ensure proper aspect ratio token format
{
  "size": {
    "$aspectRatio": {
      "aspectRatios.widescreen_16_9": "44pt",   // ✅ Correct format
      // "16:9": "44pt"                         // ❌ Wrong format
    }
  }
}
```

### Debugging Design Variants

**Enable verbose logging:**
```bash
python build.py --supertheme --designs my_designs --ratios 16:9 --out debug.thmx --verbose
```

**Validate individual variants:**
```python
import json
from tools.supertheme_generator import SuperThemeGenerator

# Test variant loading
with open('my_design.json', 'r') as f:
    variant = json.load(f)
    
generator = SuperThemeGenerator(verbose=True)
# Debug token resolution process
```

This comprehensive design variant system enables you to create sophisticated, scalable design systems that maintain consistency while providing the flexibility needed for diverse presentation requirements.