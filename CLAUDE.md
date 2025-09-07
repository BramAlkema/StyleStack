# StyleStack - OOXML Template Build System

StyleStack is an OOXML-native build system that helps developers, designers, and IT admins create consistent, accessible Office templates by providing layered, community-driven defaults that replace Microsoft's outdated 1995 styling.

## Quick Start

```bash
# Build templates for organization
python build.py --org acme --channel present --products potx dotx xltx

# Output: BetterDefaults-acme-present-1.3.0.potx, .dotx, .xltx
```

## Architecture

**Three-Layer System:**
- **Core:** Community-maintained baseline defaults (fonts, colors, accessibility)
- **Org:** Corporate overrides (logos, brand colors, disclaimers) 
- **User:** Personal customization preferences

**Multi-Platform Support:**
- Microsoft Office (.potx, .dotx, .xltx)
- LibreOffice (via UNO extensions)
- Google Workspace (via Apps Script)

## Project Structure

```
StyleStack/
├─ core/                   # Raw OOXML baseline templates
│  ├─ ppt/                 # PowerPoint masters, layouts, theme
│  ├─ word/                # Word styles.xml, numbering.xml, theme  
│  └─ xl/                  # Excel workbook.xml, styles.xml, theme
├─ org/acme/               # Corporate overrides
│  ├─ patches.yaml         # Declarative YAML patches
│  └─ assets/logo.png      # Brand assets
├─ channels/               # Template flavors
│  ├─ present.yaml         # Presentation mode
│  ├─ doc.yaml             # Document mode
│  └─ finance.yaml         # Finance/accounting mode
├─ tools/
│  ├─ patcher.py           # XPath/YAML patch engine
│  └─ validate.py          # Quality validation
├─ build.py                # Main CLI orchestrator
└─ .github/workflows/      # CI/CD automation
```

## Tech Stack

- **Python 3.9+** - Core build system and OOXML processing
- **python-pptx/docx/openpyxl** - Office format libraries
- **lxml** - XML parsing and XPath operations
- **GitHub Actions** - CI/CD for automated builds and releases
- **Multi-platform add-ins** - Office.js, Python-UNO, Apps Script

## Development Phases

1. **Core OOXML Build System** - Python CLI with YAML patches
2. **Quality & Automation** - CI/CD, validation, releases page
3. **Multi-Platform Add-ins** - Office/LibreOffice/Google integration  
4. **Community & Governance** - Contribution workflows
5. **Enterprise Features** - Bulk management, analytics

## Mission

Replace the chaos of custom Office templates with a versionable, community-driven system that provides better defaults while enabling organizational customization without upstream pollution.