# StyleStack - Design Tokens as a Service for Office Templates

StyleStack is a **Design System as a Service** platform that delivers professionally designed, accessible, brand-compliant Office templates through hierarchical design tokens distributed via embedded Office add-ins.

## Quick Start

```bash
# Build templates with embedded design system add-ins
python build.py --src template.potx --org acme --channel present --out branded.potx

# Templates automatically update design tokens when users open documents
```

## Vision: Design Tokens as a Service

**Revolutionary Distribution Model:**
- **Embedded Add-ins**: Office.js add-ins embedded in .dotx/.potx/.xltx templates
- **Smart Updates**: Templates check for design system updates when documents open
- **Corporate Subscriptions**: Enterprise customers subscribe to automatic design excellence
- **Zero Maintenance**: IT departments get continuously updated, compliant templates

## Architecture: Hierarchical Design Tokens

**Four-Layer Token Inheritance:**
- **Design System 2025**: Global foundation (typography, accessibility, grids)
- **Corporate Layer**: Brand overrides (colors, fonts, logos) 
- **Channel Layer**: Use-case specialization (presentation, document, finance)
- **Template Layer**: Final resolved variables in OOXML extension format

**Add-in Distribution Flow:**
```
StyleStack API → Office Add-in → Template Variables → Document Creation
```

## Project Structure (Current - OOXML Extension Variable System)

```
StyleStack/
├─ tools/                          # OOXML Extension Variable System (Phase 1-4 Complete)
│  ├─ variable_resolver.py         # Hierarchical token resolution
│  ├─ ooxml_processor.py          # XPath-based OOXML manipulation
│  ├─ theme_resolver.py           # Office-compatible color transformations
│  ├─ variable_substitution.py    # Transaction-based variable pipeline
│  ├─ template_analyzer.py        # 100% variable coverage analysis
│  └─ extension_schema_validator.py # JSON schema validation
├─ schemas/                        # Extension variable schemas
│  └─ extension-variable.schema.json
├─ tests/                          # Comprehensive test coverage
│  ├─ test_variable_resolver.py
│  ├─ test_ooxml_processor.py
│  ├─ test_theme_resolver.py
│  ├─ test_variable_substitution.py
│  ├─ test_template_analyzer.py
│  └─ test_build_integration.py
├─ templates/                       # Multi-platform template sources
│  ├─ microsoft/                   # Office templates
│  │  ├─ presentation.potx         # PowerPoint template
│  │  ├─ document.dotx            # Word template  
│  │  └─ spreadsheet.xltx         # Excel template
│  ├─ libreoffice/                # LibreOffice templates
│  │  ├─ presentation.otp         # Impress template
│  │  ├─ document.ott             # Writer template
│  │  └─ spreadsheet.ots          # Calc template
│  ├─ google/                     # Google Workspace templates
│  │  ├─ presentation.json        # Google Slides template data
│  │  ├─ document.json            # Google Docs template data
│  │  └─ spreadsheet.json         # Google Sheets template data
│  └─ opendocument/               # ODF standard templates
│     ├─ presentation.odp         # OpenDocument Presentation
│     ├─ document.odt             # OpenDocument Text
│     ├─ spreadsheet.ods          # OpenDocument Spreadsheet
│     ├─ graphics.odg             # OpenDocument Graphics
│     └─ formula.odf              # OpenDocument Formula
├─ org/{{org}}/                    # Corporate design tokens
│  ├─ design-tokens.json          # Brand-specific token overrides
│  └─ subscription.json           # Subscription and update policies
├─ channels/                       # Channel-specific tokens
│  ├─ present-design-tokens.json
│  ├─ document-design-tokens.json
│  └─ finance-design-tokens.json
├─ build.py                        # Multi-platform build system
├─ publishers/                     # Platform-specific publishers
│  ├─ google_workspace_publisher.py
│  ├─ microsoft_store_publisher.py
│  └─ libreoffice_store_publisher.py
└─ .github/workflows/              # Multi-platform CI/CD
   ├─ extension-variable-validation.yml
   ├─ google-workspace-publish.yml
   └─ template-store-sync.yml
```

## Tech Stack Evolution

**Current Foundation (Complete):**
- **OOXML Extension Variable System** - Variable resolution with hierarchical precedence
- **Transaction-Based Pipeline** - Atomic operations with rollback support
- **GitHub Actions Integration** - Comprehensive CI/CD validation
- **Multi-Platform Support** - Microsoft Office, LibreOffice, Google Workspace

**Format Support:**
- **Microsoft Office**: .potx, .dotx, .xltx (PowerPoint, Word, Excel templates)
- **LibreOffice**: .otp, .ott, .ots (Impress, Writer, Calc templates)  
- **OpenDocument**: .odp, .odt, .ods, .odg, .odf (Full ODF standard)
- **Google Workspace**: JSON-based template data for Slides, Docs, Sheets

**Next: Design Tokens Service (2025):**
- **Multi-Platform Add-ins** - Office.js, LibreOffice UNO, Google Apps Script
- **Template Store Publishing** - Automated publishing to Google Templates, Microsoft Store
- **StyleStack API** - Token distribution service with CDN
- **Typography Intelligence** - EMU-based professional typography  
- **Accessibility Engine** - WCAG AAA compliance built-in
- **Corporate Subscriptions** - Enterprise design system management

## Development Roadmap

### ✅ **Phase 1-4: OOXML Extension Variable System (Complete)**
- Foundation infrastructure with hierarchical variable resolution
- OOXML processing with dual-engine support (lxml + ElementTree)  
- Office-compatible theme transformations
- Transaction-based substitution pipeline with validation
- Template analysis with 100% variable coverage capability
- Build system integration with backward compatibility

### 🚀 **Phase 5: Multi-Platform Distribution (2025 Q1-Q2)**
1. **Google Workspace Integration** - Apps Script add-ins for Slides, Docs, Sheets
2. **LibreOffice UNO Extensions** - Native extensions for Impress, Writer, Calc
3. **Template Store Publishing** - Automated publishing to Google Templates, Microsoft Store
4. **Cross-Platform Token Resolution** - Universal design tokens across all formats

### 🎯 **Phase 6: Design Tokens Service (2025 Q2-Q3)**
1. **Add-in Infrastructure** - Multi-platform add-in framework
2. **Typography Intelligence** - EMU-based professional typography engine  
3. **Corporate Subscriptions** - Enterprise token management and distribution
4. **Brand Compliance** - Real-time validation and monitoring

### 📈 **Phase 7: Advanced Features (2025 Q3-Q4)**
1. **Print Production** - CMYK, bleed, crop marks, PDF/X compliance
2. **Multi-Language** - International typography and RTL support
3. **Analytics Platform** - Usage insights and design system adoption metrics

## Business Model: SaaS Revenue

**Subscription Tiers:**
- **Basic** ($10/user/month): Global design system access
- **Professional** ($25/user/month): Brand customization + advanced templates  
- **Enterprise** ($50/user/month): Custom design systems + compliance monitoring

**Revenue Target**: $10M ARR by year 2 with 200 enterprise customers

## Mission Evolution

**From Build Tool to Design Platform:**
Replace Microsoft's outdated 1995 styling with a continuously updated, professionally designed, accessible design system delivered through intelligent Office templates that automatically maintain brand compliance while reducing IT maintenance to zero.

**Vision**: Every Office document created from StyleStack templates looks professionally designed, meets accessibility standards, and maintains perfect brand compliance without user effort or IT intervention.