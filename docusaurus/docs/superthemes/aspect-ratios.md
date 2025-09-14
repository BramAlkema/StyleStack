# Aspect Ratios

Master the art of responsive design with StyleStack's sophisticated aspect ratio system. Create presentation themes that automatically adapt to any screen format with pixel-perfect precision.

## Understanding Aspect Ratios

An aspect ratio defines the proportional relationship between width and height of a presentation slide. StyleStack uses Microsoft Office's native **EMU (English Metric Units)** system for precise calculations that ensure perfect rendering across all Office versions.

### EMU Precision System

**Why EMUs Matter:**
- 1 inch = 914,400 EMUs (Office native units)
- 1 point = 12,700 EMUs  
- Exact calculations prevent rounding errors
- Consistent rendering across Windows, Mac, and Office Online

## Standard Aspect Ratios

### Widescreen 16:9 (Default)

**Dimensions**: 10,058,400 × 5,657,600 EMUs (11" × 6.1875")

The modern presentation standard, optimized for:
- ✅ HD displays and projectors
- ✅ Video conferencing (Zoom, Teams)
- ✅ YouTube and online sharing
- ✅ Modern laptop screens

**Usage:**
```bash
python build.py --supertheme --designs my_designs --ratios 16:9 --out widescreen.thmx
```

**Design Considerations:**
- More horizontal space for content
- Ideal for data visualization and charts
- Better for landscape imagery
- Standard for modern corporate presentations

### Traditional 4:3 (Legacy)

**Dimensions**: 9,144,000 × 6,858,000 EMUs (10" × 7.5")

The classic presentation format, still used for:
- ✅ Older projectors and displays
- ✅ Academic presentations
- ✅ Print handouts (better page utilization)
- ✅ Legacy corporate templates

**Usage:**
```bash
python build.py --supertheme --designs my_designs --ratios 4:3 --out traditional.thmx
```

**Design Considerations:**
- More vertical space for content
- Better for text-heavy presentations  
- Optimal for portrait imagery
- Familiar format for established audiences

### A4 Landscape (European Standard)

**Dimensions**: 10,826,771 × 7,677,165 EMUs (11.84" × 8.4")

Optimized for European document standards:
- ✅ A4 page printing without scaling
- ✅ European corporate compliance
- ✅ International document workflows
- ✅ ISO standard alignment

**Usage:**
```bash
python build.py --supertheme --designs my_designs --ratios a4 --out european.thmx
```

### Letter Landscape (US Standard)

**Dimensions**: 10,058,400 × 7,772,400 EMUs (11" × 8.5")

Tailored for US document standards:
- ✅ US Letter page printing
- ✅ American corporate workflows
- ✅ Legal document compliance
- ✅ North American market optimization

**Usage:**
```bash
python build.py --supertheme --designs my_designs --ratios letter --out american.thmx
```

## Custom Aspect Ratios

### Defining Custom Ratios

Create specialized formats for unique requirements:

```bash
# Ultra-wide display (21:9)
python build.py --supertheme --designs my_designs --ratios 21:9 --out ultrawide.thmx

# Square format for social media
python build.py --supertheme --designs my_designs --ratios 1:1 --out square.thmx

# Custom cinema format
python build.py --supertheme --designs my_designs --ratios 2.39:1 --out cinema.thmx

# Portrait orientation for mobile
python build.py --supertheme --designs my_designs --ratios 9:16 --out mobile.thmx
```

### Multiple Ratio Generation

Generate comprehensive theme packages supporting multiple formats:

```bash
# All standard formats
python build.py --supertheme --designs my_designs --ratios 16:9,4:3,a4,letter --out complete.thmx

# Mixed standard and custom
python build.py --supertheme --designs my_designs --ratios 16:9,21:9,1:1 --out mixed.thmx

# Specialized set for video content
python build.py --supertheme --designs my_designs --ratios 16:9,21:9,2.39:1 --out video.thmx
```

## Responsive Design Tokens

### Aspect Ratio Conditional Tokens

Design elements that automatically adapt based on aspect ratio:

```json
{
  "typography": {
    "heading": {
      "size": {
        "$aspectRatio": {
          "aspectRatios.widescreen_16_9": "48pt",
          "aspectRatios.traditional_4_3": "44pt",
          "aspectRatios.a4_landscape": "40pt",
          "aspectRatios.letter_landscape": "40pt"
        }
      },
      "line_height": {
        "$aspectRatio": {
          "aspectRatios.widescreen_16_9": "1.2",
          "aspectRatios.traditional_4_3": "1.15",
          "aspectRatios.a4_landscape": "1.1",
          "aspectRatios.letter_landscape": "1.1"
        }
      }
    }
  }
}
```

### Layout Positioning

Responsive positioning system that adapts to screen dimensions:

```json
{
  "layouts": {
    "title_slide": {
      "title_position": {
        "$aspectRatio": {
          "aspectRatios.widescreen_16_9": {
            "x": "1.5in",
            "y": "2.0in",
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
      },
      "logo_position": {
        "$aspectRatio": {
          "aspectRatios.widescreen_16_9": {
            "x": "9.5in",
            "y": "0.5in",
            "width": "1in",
            "height": "0.5in"
          },
          "aspectRatios.traditional_4_3": {
            "x": "8.25in",
            "y": "0.5in", 
            "width": "1in",
            "height": "0.5in"
          }
        }
      }
    }
  }
}
```

### Spacing and Margins

Proportional spacing that maintains visual balance:

```json
{
  "spacing": {
    "margins": {
      "$aspectRatio": {
        "aspectRatios.widescreen_16_9": {
          "top": "0.75in",
          "bottom": "0.75in", 
          "left": "1in",
          "right": "1in"
        },
        "aspectRatios.traditional_4_3": {
          "top": "0.5in",
          "bottom": "0.5in",
          "left": "0.75in", 
          "right": "0.75in"
        }
      }
    },
    "content_padding": {
      "$aspectRatio": {
        "aspectRatios.widescreen_16_9": "48pt",
        "aspectRatios.traditional_4_3": "36pt",
        "aspectRatios.a4_landscape": "32pt"
      }
    }
  }
}
```

## Advanced Aspect Ratio Patterns

### Conditional Logic for Complex Layouts

```json
{
  "charts": {
    "bar_chart_layout": {
      "$conditional": {
        "if": {"$aspectRatio": "aspectRatios.widescreen_16_9"},
        "then": {
          "orientation": "horizontal",
          "legend_position": "right",
          "title_size": "24pt"
        },
        "else": {
          "orientation": "vertical",
          "legend_position": "bottom", 
          "title_size": {
            "$aspectRatio": {
              "aspectRatios.traditional_4_3": "22pt",
              "aspectRatios.a4_landscape": "20pt"
            }
          }
        }
      }
    }
  }
}
```

### Breakpoint System

Define responsive breakpoints for fine-tuned control:

```json
{
  "breakpoints": {
    "mobile": {"max_width": "aspectRatios.traditional_4_3"},
    "desktop": {"min_width": "aspectRatios.widescreen_16_9"},
    "ultrawide": {"min_width": "21:9"}
  },
  "typography": {
    "body": {
      "size": {
        "$breakpoint": {
          "mobile": "18pt",
          "desktop": "20pt", 
          "ultrawide": "22pt"
        }
      }
    }
  }
}
```

## Best Practices

### 1. Design for Multiple Ratios

**✅ Good Practice:**
```json
{
  "colors": {
    "brand": {"primary": "#0066CC"}  // Works across all ratios
  },
  "typography": {
    "heading": {
      "size": {
        "$aspectRatio": {
          "aspectRatios.widescreen_16_9": "44pt",
          "aspectRatios.traditional_4_3": "40pt"  // Optimized per ratio
        }
      }
    }
  }
}
```

**❌ Avoid:**
```json
{
  "typography": {
    "heading": {"size": "44pt"}  // Fixed size doesn't adapt
  }
}
```

### 2. Maintain Proportional Relationships

**Maintain visual hierarchy across formats:**
```json
{
  "typography": {
    "h1": {
      "size": {
        "$aspectRatio": {
          "aspectRatios.widescreen_16_9": "44pt",
          "aspectRatios.traditional_4_3": "40pt"
        }
      }
    },
    "h2": {
      "size": {
        "$aspectRatio": {
          "aspectRatios.widescreen_16_9": "32pt",  // 44pt × 0.73
          "aspectRatios.traditional_4_3": "29pt"   // 40pt × 0.73
        }
      }
    }
  }
}
```

### 3. Test Across All Target Ratios

**Comprehensive Testing Strategy:**
```bash
# Generate test theme with all target ratios
python build.py --supertheme --designs test_design --ratios 16:9,4:3,a4,letter --out test.thmx

# Test in PowerPoint:
# 1. Apply theme
# 2. Switch between Design → Slide Size options  
# 3. Verify visual consistency
# 4. Check text readability
# 5. Validate layout integrity
```

### 4. Consider Content Density

**Adapt content density to available space:**
```json
{
  "content": {
    "bullets_per_slide": {
      "$aspectRatio": {
        "aspectRatios.widescreen_16_9": 6,     // More horizontal space
        "aspectRatios.traditional_4_3": 5,     // More vertical space  
        "aspectRatios.a4_landscape": 7,        // Larger overall area
        "aspectRatios.letter_landscape": 7
      }
    }
  }
}
```

## Performance Optimization

### Efficient Token Resolution

**Cache aspect ratio calculations:**
```python
@lru_cache(maxsize=128)
def get_aspect_ratio_token(self, ratio_key):
    return self._calculate_dimensions(ratio_key)
```

**Batch process multiple ratios:**
```python
def generate_all_variants(self, design_variants, aspect_ratios):
    # Process all ratios for each design in batch
    # Reuse theme calculations across ratios
    # Optimize memory usage
```

### Package Size Optimization

**Monitor variant count impact:**
- 1 design × 4 ratios = 4 variants (~0.02MB)
- 5 designs × 4 ratios = 20 variants (~0.1MB)  
- 10 designs × 6 ratios = 60 variants (~0.5MB)

**Optimization strategies:**
- Share common theme elements across variants
- Use efficient GUID generation for variants
- Optimize XML structure and whitespace

## Troubleshooting

### Common Issues

**❌ "Aspect ratio not supported"**
```bash
# Check ratio format
python build.py --supertheme --designs my_designs --ratios 16:9     # ✅ Correct
python build.py --supertheme --designs my_designs --ratios 16x9     # ❌ Wrong format
python build.py --supertheme --designs my_designs --ratios 1.78:1   # ✅ Decimal ratios OK
```

**❌ Theme doesn't switch properly in PowerPoint**
- Verify variant count matches ratio count
- Check themeVariantManager.xml structure
- Ensure GUID uniqueness across variants

**❌ Text appears too small/large**
- Review aspect ratio token values
- Test on actual target displays
- Adjust base font sizes proportionally

### Validation and Debugging

**Enable verbose validation:**
```bash
python build.py --supertheme --designs my_designs --ratios 16:9,4:3 --out debug.thmx --verbose
```

**Check variant generation:**
```python
# Inspect generated SuperTheme
from tools.supertheme_validator import SuperThemeValidator

validator = SuperThemeValidator()
with open('debug.thmx', 'rb') as f:
    result = validator.validate_package(f.read())
    
print(f"Variants found: {result.variant_count}")
print(validator.generate_validation_report(result))
```

This comprehensive aspect ratio system ensures your SuperThemes deliver professional results across any presentation format, maintaining visual consistency and optimal readability regardless of display requirements.