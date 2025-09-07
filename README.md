# StyleStack 2026 - Publication-Quality OOXML Templates

Revolutionary OOXML-native build system that delivers InDesign-level typography and layout capabilities through Microsoft Office templates.

## 🚀 2026 Revolution

**Beyond Office UI limitations** - Direct OOXML manipulation enables:
- **Modern Typography Engine** (Inter font stack, advanced kerning, OpenType features)
- **EMU-precision layout** (6pt baseline grids, professional spacing systems)
- **WCAG AAA accessibility** (7:1 contrast ratios, dyslexia-friendly settings)
- **Open XML PowerTools methodology** (comprehensive OOXML transformation engine)

## 🎨 Modern Typography System

StyleStack features publication-quality typography inspired by Open XML PowerTools:

### **Professional Typography Stack**
- **Inter Font Family** - Modern, accessible, optimized for screens and print
- **Advanced Kerning Engine** - Professional AV/AW/AY pair optimization
- **OpenType Features** - Ligatures, contextual alternates, tabular numbers
- **Modular Type Scale** - 1.250 (Major Third) ratio for visual harmony
- **Multi-Format Precision** - Exact OOXML unit conversion across Office apps

### **OOXML Unit Mastery**
```yaml
# PowerPoint: Twentieths of points (1pt = 20 units)
powerpoint:
  font_sizes:
    display: 977      # 48.83pt × 20
    
# Word: Half-points + Twips for spacing  
word:
  font_sizes:
    heading1: 78      # 39pt × 2
  line_spacing: 360   # 1.5 × 12pt × 20 twips
  
# Excel: Direct points
excel:
  font_sizes:
    header: 12        # 12pt
```

### **Professional Kerning**
```yaml
kerning_pairs:
  "AV": -32          # -0.08em in twentieths
  "T,": -24          # Punctuation optimization
  "P.": -16          # Professional spacing
```

## 5-Layer Architecture

StyleStack applies patches in this order:

1. **Core** - Community-maintained baseline (fonts, colors, accessibility)
2. **Fork** - Alternative "schools of thought" (enterprise-defaults, creative-suite)  
3. **Orgs** - Corporate branding (logos, brand colors, legal disclaimers)
4. **Group** - Department overrides (marketing styles, finance formats)
5. **Personal** - Individual preferences (font sizes, personal quirks)

```
Core → Fork → Org → Group → Personal → Output Template
```

## Directory Structure

```
StyleStack/
├─ core/                    # Community baseline templates
│  ├─ ppt/                  # PowerPoint masters, layouts, themes
│  ├─ word/                 # Word styles, numbering, themes
│  └─ xl/                   # Excel workbook, styles, themes
├─ forks/
│  ├─ enterprise-defaults/  # Conservative corporate fork
│  └─ creative-suite/       # Design-heavy alternative
├─ orgs/
│  └─ acme/
│     ├─ patches.yaml       # Corporate branding
│     ├─ assets/logo.png    # Brand assets
│     └─ groups/
│        ├─ marketing/      # Marketing department overrides
│        └─ finance/        # Finance department overrides
├─ personal/
│  └─ john-doe/            # Individual customizations
├─ channels/               # Template flavors
│  ├─ present.yaml         # Presentation mode
│  ├─ doc.yaml             # Document mode
│  └─ finance.yaml         # Accounting mode
└─ build.py               # CLI orchestrator
```

## Usage

```bash
# Full 5-layer build
python build.py --fork enterprise-defaults --org acme --group marketing --personal john-doe --channel present --products potx

# Output: StyleStack-enterprise-acme-marketing-johndoe-present-v1.0.0.potx
```

## Layer Examples

**Core:** Professional typography, accessible colors, modern layouts  
**Fork:** `enterprise-defaults` (conservative) vs `creative-suite` (bold)  
**Org:** ACME Corp logo, brand colors, legal disclaimers  
**Group:** Marketing (brand fonts) vs Finance (accounting formats)  
**Personal:** John prefers larger fonts, Jane likes minimal layouts

## Benefits

- **Community Core:** Everyone benefits from accessibility and typography improvements
- **Fork Governance:** Different "schools" can coexist without fragmenting community
- **Organizational:** Corporate branding without polluting upstream
- **Departmental:** Marketing vs Finance can have different needs
- **Personal:** Individual preferences without affecting team consistency