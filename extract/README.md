# Design Token Extraction Workflow

> **Simple Drop & Extract**: Place Office or OpenOffice files in this folder and GitHub Actions will automatically extract design tokens and brand assets.

## How It Works

1. **Drop Files**: Add Office or OpenOffice files anywhere in this `extract/` folder
   - **Microsoft Office**: `.pptx`, `.potx`, `.ppsx` (PowerPoint)
   - **OpenOffice/LibreOffice**: `.odp`, `.otp` (Impress), `.ods`, `.ots` (Calc), `.odt`, `.ott` (Writer)
2. **Automatic Processing**: GitHub Actions detects new files and runs the extractor
3. **Results Generated**: Tokens and assets appear in `extracted/` subfolder
4. **Auto-Commit**: Results are automatically committed to the repository

## Folder Structure

```
extract/
├── my-presentation.pptx          # Microsoft PowerPoint
├── slides.odp                   # LibreOffice Impress
├── spreadsheet.ods              # LibreOffice Calc  
├── document.odt                 # LibreOffice Writer
├── extracted/                   # Auto-generated results
│   ├── my-presentation-tokens.yaml
│   ├── slides-tokens.yaml
│   ├── spreadsheet-tokens.yaml
│   ├── document-tokens.yaml
│   └── [filename]-assets/
│       ├── logos/
│       ├── icons/
│       └── images/
└── company-templates/
    ├── brand-deck.pptx          # Office formats
    ├── template.otp             # OpenOffice templates
    └── extracted/
        ├── brand-deck-tokens.yaml
        ├── template-tokens.yaml
        └── [filename]-assets/
```

## Usage Examples

### Basic Extraction
```bash
# Just drop your file:
extract/
└── quarterly-report.pptx

# Results appear automatically:
extract/
├── quarterly-report.pptx
└── extracted/
    ├── quarterly-report-tokens.yaml    # Design tokens
    └── quarterly-report-assets/        # Brand assets
        ├── logos/
        ├── icons/
        └── images/
```

### Organized Extraction
```bash
# Organize by project:
extract/
├── marketing/
│   ├── campaign-deck.pptx
│   └── extracted/
│       ├── campaign-deck-tokens.yaml
│       └── campaign-deck-assets/
└── sales/
    ├── pitch-deck.pptx
    └── extracted/
        ├── pitch-deck-tokens.yaml
        └── pitch-deck-assets/
```

## Output Formats

### Design Tokens (YAML)
```yaml
stylestack:
  version: 1.0.0
  extracted: true
  tokens:
    colors:
      primary: "#0066CC"
      secondary: "#FF6600"
    typography:
      font_family: "Helvetica Neue"
      sizes:
        heading: 24pt
        body: 12pt
    brand_assets:
      logos:
        company_logo:
          filename: "logo.png"
          classification: "primary_logo"
          dimensions:
            width: 200
            height: 80
```

### Extracted Assets
- **logos/**: Company logos and brand marks
- **icons/**: Functional and decorative icons
- **images/**: Photos, graphics, and diagrams

## Features

- ✅ **Automatic Processing** - No manual intervention needed
- ✅ **YAML Output** - Human-readable design token format
- ✅ **Asset Classification** - Smart categorization of images
- ✅ **Brand Consistency Analysis** - Automated quality scoring
- ✅ **Git Integration** - Results automatically committed
- ✅ **Organized Structure** - Clean folder organization

## Manual Extraction

You can also run the extractor manually:

```bash
# Basic extraction
python tools/design_token_extractor.py extract/my-file.pptx

# Full extraction with assets
python tools/design_token_extractor.py extract/my-file.pptx \
  --output extract/extracted/my-tokens.yaml \
  --extract-assets \
  --assets-dir extract/extracted/my-assets \
  --analyze \
  --verbose
```

## Supported Formats

### Microsoft Office
- `.pptx` - PowerPoint presentations
- `.potx` - PowerPoint templates  
- `.ppsx` - PowerPoint slide shows

### OpenOffice/LibreOffice  
- `.odp` - Impress presentations
- `.otp` - Impress templates
- `.ods` - Calc spreadsheets
- `.ots` - Calc templates
- `.odt` - Writer documents
- `.ott` - Writer templates

---

**🚀 Ready to extract?** Just drop your Office or OpenOffice files in this folder and watch the magic happen!