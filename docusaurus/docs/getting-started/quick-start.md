---
sidebar_position: 1
---

# Quick Start

Get up and running with StyleStack templates in under 5 minutes. StyleStack provides modern, accessible Office templates that replace Microsoft's outdated 1995 styling with community-driven defaults.

## What You'll Get

StyleStack templates include:
- **Modern typography** - Contemporary fonts optimized for readability
- **Accessible colors** - WCAG-compliant color schemes
- **Professional layouts** - Clean, consistent design patterns
- **Brand flexibility** - Easy customization for your organization

## Option 1: Use Community Templates (Fastest)

Download pre-built templates from the latest release:

```bash
# Download community templates
curl -L https://github.com/stylestack/stylestack/releases/latest/download/BetterDefaults-community-1.3.0.zip -o templates.zip
unzip templates.zip
```

You'll get:
- `BetterDefaults-community-present-1.3.0.potx` - PowerPoint template
- `BetterDefaults-community-doc-1.3.0.dotx` - Word template  
- `BetterDefaults-community-finance-1.3.0.xltx` - Excel template

## Option 2: Fork and Customize (Recommended)

For organizational use, fork the repository to add your branding:

```bash
# Fork the repository (via GitHub UI or CLI)
gh repo fork stylestack/stylestack --clone

# Navigate to your fork
cd stylestack

# Build custom templates
python build.py --org mycompany --channel present --products potx dotx xltx
```

## Installing Templates

### PowerPoint (.potx)
1. Double-click the `.potx` file
2. Save as template: **File → Save As → PowerPoint Template**
3. Choose location: **Templates** folder

### Word (.dotx)
1. Double-click the `.dotx` file  
2. Save as template: **File → Save As → Word Template**
3. Access via: **File → New → Personal**

### Excel (.xltx)
1. Double-click the `.xltx` file
2. Save as template: **File → Save As → Excel Template** 
3. Access via: **File → New → Personal**

## First Use

### Create a Presentation
1. Open PowerPoint
2. **File → New → Personal**
3. Select **BetterDefaults** template
4. Start with modern, accessible slides

### Create a Document  
1. Open Word
2. **File → New → Personal**
3. Select **BetterDefaults** template
4. Professional styling applied automatically

### Create a Spreadsheet
1. Open Excel
2. **File → New → Personal** 
3. Select **BetterDefaults** template
4. Clean, readable formatting ready to use

## Verify Installation

Check that templates include:
- ✅ Modern fonts (not Times New Roman/Calibri)
- ✅ Accessible color contrast
- ✅ Professional slide layouts (PowerPoint)
- ✅ Consistent heading styles (Word)
- ✅ Clean table formatting (Excel)

## Next Steps

- **Need customization?** → [Fork and customize](../fork-management/creating-fork.md)
- **Adding branding?** → [Branding guide](../customization/branding.md)
- **Setting up CI/CD?** → [Automated builds](../deployment/ci-cd.md)
- **Questions?** → Check our [examples](../examples/university.md)

## Troubleshooting

**Templates not appearing?**
- Ensure saved in correct Templates folder
- Restart Office applications
- Check file permissions

**Fonts not loading?**
- Install required fonts system-wide
- Check font licensing for your organization
- Use fallback fonts in customization

**Colors look different?**
- Verify display calibration
- Check Office theme settings
- Review WCAG contrast requirements

## Support

- 📖 [Full documentation](../design-tokens/overview.md)
- 💬 [Community discussions](https://github.com/stylestack/stylestack/discussions)
- 🐛 [Report issues](https://github.com/stylestack/stylestack/issues)