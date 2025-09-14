# StyleStack XML Structures Reference

## Overview
This directory contains **foundational XML structure definitions** for Office document formats. Each structure includes comprehensive design token integration for StyleStack variable substitution across both OOXML (ISO/IEC 29500) and ODF (ISO/IEC 26300) standards.

## 🏗️ Architecture

### **WHY WE NEED EXHAUSTIVE OOXML STRUCTURES WITH ALL TEMPLATABLE PARTS**

StyleStack's **Design Tokens as a Service** requires **every possible layoutable component** because:

1. **Corporate Brand Compliance**: Every shape, chart, table, header must follow brand guidelines
2. **Variable Substitution**: All text, colors, fonts, sizes need token replacement points
3. **Template Automation**: Macros enable smart templates that auto-update from StyleStack API
4. **Cross-Platform Consistency**: Same design tokens work across Word/Excel/PowerPoint/OpenDoc
5. **Future-Proofing**: Support all OOXML/ODF capabilities for enterprise workflows
6. **Round-Trip Testing**: Google Workspace compatibility requires complete OOXML coverage

## 🎯 Strategic Format Coverage

### **Phase 1: Core Foundation (COMPLETE ✅)**

**OOXML (ISO/IEC 29500) - Macro-Free Only:**
| Format | Purpose | Status |
|--------|---------|--------|
| **.dotx** | Word templates | ✅ Complete |
| **.potx** | PowerPoint templates | ✅ Complete |
| **.xltx** | Excel templates | ✅ Complete |
| **.thmx** | Office themes | ✅ Complete |

**ODF (ISO/IEC 26300):**
| Format | Purpose | Status |
|--------|---------|--------|
| **.odt** | Text documents | ✅ Complete |
| **.odp** | Presentations | ✅ Complete |
| **.ods** | Spreadsheets | ✅ Complete |
| **.odg** | Graphics | ✅ Complete |
| **.odf** | Mathematical formulas | ✅ Complete |

**Coverage: 9/9 Core Formats (100%)**

### **Phase 2: Business-Driven Extensions (Future)**

**High-Value Additions (Customer Demand):**
- **.pptx** - PowerPoint documents (presentation workflows)
- **.xlsx** - Excel workbooks (financial teams)
- **.docx** - Word documents (content creation)

**Email Templates (Corporate Communication):**
- **.oft** - Outlook templates (branded emails)
- **HTML Email** - Cross-platform email templates
- **Email Signatures** - Corporate signature templates

### **Excluded Formats (Strategic Decision):**

**❌ Macro-Enabled Formats:** `.dotm`, `.xlsm`, `.pptm`, `.docm`, `.potm`, `.ppsm`
- **Reason:** Security risks, enterprise IT restrictions, complexity overhead

**❌ Specialized/Niche:** `.odb`, `.odc`, `.odi`, `.odm`, `.oth`, `.mml`
- **Reason:** Low business impact, specialized use cases

**❌ Internal/Technical:** `.rels`, `.xml`, `.odcxml`
- **Reason:** Implementation details, not user formats

### Exhaustive Templatable Components Required

#### **Every Structure Must Include ALL These Layoutable Parts:**

**Document Structure:**
- Main content containers (body, slides, sheets, pages)
- Headers and footers (all variants: default, first page, even/odd)
- Master pages and slide masters
- Section breaks and page layout definitions
- Margins, orientation, size settings

**Typography & Text:**
- Character formatting (fonts, sizes, weights, styles)
- Paragraph formatting (spacing, alignment, indentation)
- Text boxes and shape text
- Bulleted and numbered lists (all nesting levels)
- Table of contents, indexes, captions
- Footnotes, endnotes, comments, track changes

**Visual Elements:**
- Tables (borders, shading, cell formatting, merged cells)
- Charts (all types: bar, line, pie, scatter, etc.)
- SmartArt diagrams (layouts, colors, styles)
- Shapes and drawing objects
- Images and media (embedding, linking, cropping)
- Background images and watermarks

**Layout Systems:**
- Multi-column layouts
- Text wrapping around objects
- Absolute and relative positioning
- Z-order and layering
- Grouping and alignment guides
- Snap-to-grid systems

**Interactive Elements:**
- Form controls (text boxes, dropdowns, checkboxes)
- Hyperlinks and bookmarks
- Cross-references and field codes
- Content controls and structured document tags
- ActiveX controls and embedded objects

**Presentation-Specific:**
- Slide transitions and animations
- Slide timing and auto-advance
- Speaker notes and handout masters
- Slide layouts and placeholders
- Action buttons and navigation

**Spreadsheet-Specific:**
- Cell formatting (numbers, dates, currencies)
- Conditional formatting rules
- Data validation and input restrictions
- Pivot tables and data analysis
- Formulas and calculated fields
- Named ranges and data connections

**Advanced Features:**
- VBA macros and code modules (for .dotm/.potm/.xltm)
- Custom XML parts and schemas
- Document properties and metadata
- Protection and security settings
- Print settings and page setup
- Collaboration features

#### **Why Every Component Matters for StyleStack:**

1. **Brand Consistency**: Every visual element needs design token control
2. **Template Flexibility**: Corporate users need all Office capabilities
3. **Automation Power**: Macros enable smart, self-updating templates
4. **Cross-Platform**: Same tokens work across all formats
5. **Future Growth**: Support enterprise workflows and integrations
6. **Quality Assurance**: Complete coverage ensures no gaps in RTT testing

## 📁 Directory Structure

```
xml-structures/
├── README.md                           # This technical reference
├── ooxml/                              # OOXML (ISO/IEC 29500)
│   ├── word-dotx/                      # Word template structure
│   ├── presentation-potx/              # PowerPoint template structure
│   ├── spreadsheet-xltx/               # Excel template structure
│   ├── theme-thmx/                     # Office theme structure
│   └── graphics/                       # Drawing/graphics structures
└── odf/                                # ODF (ISO/IEC 26300)
    ├── text-odt/                       # OpenDocument Text structure
    ├── presentation-odp/               # OpenDocument Presentation structure
    ├── spreadsheet-ods/                # OpenDocument Spreadsheet structure
    ├── graphics-odg/                   # OpenDocument Graphics structure
    └── formula-odf/                    # OpenDocument Formula structure
```

## 🎯 Word Template (.dotx) - COMPLETE ✅

### Directory Structure
```
ooxml/word-document-styles.xml
├── [Content_Types].xml                 # Content type definitions for all parts
├── _rels/
│   └── .rels                          # Package relationships
├── docProps/
│   ├── app.xml                        # Application properties
│   ├── core.xml                       # Core document properties
│   └── custom.xml                     # Custom properties
├── customXml/                         # Custom XML parts
│   ├── item1.xml                      # Custom XML data
│   └── itemProps1.xml                 # Custom XML properties
└── word/
    ├── _rels/
    │   └── document.xml.rels           # Document relationships
    ├── document.xml                    # Main document content
    ├── styles.xml                      # Comprehensive style definitions
    ├── numbering.xml                   # List and numbering definitions
    ├── settings.xml                    # Document settings
    ├── webSettings.xml                 # Web-specific settings
    ├── fontTable.xml                   # Font definitions
    ├── theme/
    │   └── theme1.xml                  # StyleStack Modern theme
    ├── header1.xml                     # Default header
    ├── header2.xml                     # First page header
    ├── header3.xml                     # Even page header
    ├── footer1.xml                     # Default footer
    ├── footer2.xml                     # First page footer
    ├── footer3.xml                     # Even page footer
    ├── footnotes.xml                   # Footnote definitions
    ├── endnotes.xml                    # Endnote definitions
    ├── comments.xml                    # Comment definitions
    ├── glossary/
    │   ├── document.xml                # Building blocks document
    │   └── styles.xml                  # Building blocks styles
    ├── charts/
    │   ├── chart1.xml                  # Chart definition
    │   ├── style1.xml                  # Chart style
    │   └── colors1.xml                 # Chart colors
    ├── diagrams/
    │   ├── layout1.xml                 # SmartArt layout
    │   ├── data1.xml                   # SmartArt data
    │   ├── colors1.xml                 # SmartArt colors
    │   └── quickStyle1.xml             # SmartArt styles
    ├── embeddings/
    │   └── oleObject1.bin              # Embedded OLE object
    ├── activeX/
    │   └── activeX1.xml                # ActiveX control
    ├── media/
    │   ├── image1.png                  # Image resources
    │   └── image2.jpg                  # Image resources
    └── vmlDrawing1.vml                 # VML drawing objects
```

### Layoutable Components - Word (.dotx)

#### Document Structure
- **Main Document** (`document.xml`): Complete document with paragraphs, tables, sections
- **Headers/Footers** (`header*.xml`, `footer*.xml`): All header/footer variants
- **Footnotes/Endnotes** (`footnotes.xml`, `endnotes.xml`): Note definitions
- **Comments** (`comments.xml`): Review comments and annotations

#### Typography & Styling
- **Styles** (`styles.xml`): 25+ comprehensive paragraph, character, table, and numbering styles
- **Theme** (`theme/theme1.xml`): StyleStack Modern color scheme, typography, and format scheme
- **Font Table** (`fontTable.xml`): Font definitions and fallbacks
- **Numbering** (`numbering.xml`): List and outline numbering schemes

#### Content Elements
- **Tables**: Complete table with borders, shading, cell margins
- **Lists**: Bulleted and numbered lists with multiple levels
- **Charts**: Chart definitions with styles and colors
- **SmartArt**: Diagram layouts, data, colors, and styles
- **Images**: PNG/JPEG image support with relationships
- **Embedded Objects**: OLE object embedding
- **ActiveX Controls**: Form controls and interactive elements
- **VML Drawings**: Legacy drawing objects

#### Layout & Formatting
- **Section Properties**: Page size, margins, columns, headers/footers
- **Page Setup**: Orientation, size, margins, gutters
- **Columns**: Multi-column layouts
- **Page Breaks**: Manual and automatic page breaks
- **Tabs**: Tab stops and alignment
- **Spacing**: Line spacing, paragraph spacing, indentation

#### Internationalization
- **Multi-Script Support**: 35+ international writing scripts supported in theme
- **Language Settings**: Language and region specifications
- **Right-to-Left**: RTL text support for Arabic, Hebrew, etc.

## 🎨 StyleStack Modern Design System

All OOXML structures implement the **StyleStack Modern Design System**:

### Color Palette
- **Primary**: `#0EA5E9` (Sky Blue)
- **Secondary**: `#8B5CF6` (Violet)
- **Success**: `#10B981` (Emerald)
- **Warning**: `#F59E0B` (Amber)
- **Error**: `#EF4444` (Red)
- **Neutral**: `#6B7280` (Gray)
- **Dark**: `#1F2937` (Dark Gray)
- **Light**: `#F9FAFB` (Light Gray)

### Typography
- **Primary Font**: Inter (Modern, accessible, professional)
- **International Support**: Noto Sans family for all scripts
- **Hierarchy**: Title (44pt), H1 (32pt), H2 (28pt), Body (22pt)
- **Accessibility**: WCAG AAA compliant contrast ratios

### Layout Principles
- **Professional Spacing**: Consistent margins and padding
- **Grid System**: 720 twip base unit for alignment
- **Responsive**: Adapts to different page sizes
- **Print-Ready**: Optimized for professional printing

## 🔧 StyleStack Integration

### Variable Substitution Points
Each OOXML file contains **variable substitution markers**:
- `{{variable_name}}` - Simple variable replacement
- `{{#if condition}}` - Conditional content
- `{{#each items}}` - Repeating content
- `{{&html_content}}` - Rich content insertion

### Build System Integration
These structures are used by `build.py`:
```bash
python build.py --src word/comprehensive-dotx --org acme --channel present --out document.docx
```

### Extension Variable System
Supports the StyleStack Extension Variable System:
- **Hierarchical Tokens**: Design System → Corporate → Channel → Template
- **Theme Inheritance**: Corporate branding overrides
- **Component Library**: Reusable styled components

## 🚀 Usage Instructions

### 1. Template Development
Use these structures as base templates for new document types:
```bash
cp -r xml-structures/word/comprehensive-dotx my-new-template
# Edit files as needed
# Add variables: {{company_name}}, {{brand_color}}
```

### 2. StyleStack Build Process
```bash
# Build with variables
python build.py \\
  --src xml-structures/word/comprehensive-dotx \\
  --org acme \\
  --channel document \\
  --out output.docx
```

### 3. Variable Extraction
Extract variables from existing templates:
```bash
python tools/template_analyzer.py \\
  --analyze xml-structures/word/comprehensive-dotx \\
  --output variables.json
```

## 📝 Development Guidelines

### Adding New Components
1. **Study the OOXML Spec**: Reference ECMA-376 for proper structure
2. **Follow StyleStack Patterns**: Use consistent variable naming
3. **Test Thoroughly**: Verify in Word, compatibility mode, etc.
4. **Document Variables**: Update this README with new substitution points

### File Naming Conventions
- **Core Files**: Use exact OOXML spec names (`document.xml`, `styles.xml`)
- **Multiple Files**: Use numbered suffixes (`header1.xml`, `chart1.xml`)
- **Media Files**: Descriptive names in `media/` folder

### Variable Naming
- **Snake Case**: `{{company_name}}`, `{{brand_color}}`
- **Hierarchical**: `{{corporate.logo_url}}`, `{{channel.template_type}}`
- **Conditional**: `{{#if show_header}}`, `{{#unless hide_footer}}`

## ⚠️ CRITICAL: EXHAUSTIVE STRUCTURE REQUIREMENT

**Important Note for Future Development:**

> 🔍 **EVERY NOOK AND CRANNY REQUIREMENT**: The current implementation focuses on core design token integration, but we WILL need to revisit ALL structures to capture **every possible templatable property** in OOXML/ODF formats. This includes:
>
> ### Obscure Properties That Must Be Captured:
> - **Undocumented Shading**: Complex gradient algorithms, texture fills, pattern overlays, shadow variations
> - **Micro-Typography Controls**: Character-level kerning, letter-spacing, word-spacing, line-height variations
> - **Advanced Language Settings**: Script-specific font fallbacks, text direction controls, hyphenation rules
> - **Hidden Theme Properties**: Super theme inheritance, advanced color transformations
> - **Shape Typography**: Line height properties within shapes impossible to access via UI
> - **Conditional Logic**: Complex business rules, data-driven formatting, field calculations
> - **Print Production**: CMYK colors, bleed settings, crop marks, spot colors, PDF/X compliance
> - **Accessibility Metadata**: Screen reader hints, navigation structures, alt-text hierarchies
> - **Platform Extensions**: Microsoft/Google/LibreOffice vendor-specific XML attributes
> - **Undocumented XML**: Attributes that work but aren't in official schemas
>
> **Every single property that can be set in raw OOXML/ODF and survives round-trip conversions must be identified and integrated with design token variables.**
>
> This exhaustive approach is what gives StyleStack its **120% platform capability access** competitive advantage vs the ~60% exposed through standard UIs and APIs.

## 🗺️ Development Roadmap

### ✅ Phase 1: Core Foundation (COMPLETE - January 2025)
**Strategic Format Coverage**
- [x] **OOXML Templates**: Word (.dotx), PowerPoint (.potx), Excel (.xltx), Theme (.thmx)
- [x] **ODF Documents**: Text (.odt), Presentation (.odp), Spreadsheet (.ods), Graphics (.odg), Formula (.odf)
- [x] **Design Token Integration**: Comprehensive variable substitution throughout all structures
- [x] **StyleStack Modern Theme**: Professional typography, brand-compliant color palette
- [x] **Cross-Platform Compatibility**: Both Microsoft Office and LibreOffice ecosystems

**Result**: 9/9 core formats complete (100% coverage)

### 🔄 Phase 2: Business-Driven Extensions (2025 Q2-Q3)
**High-Value Format Additions**
- [ ] **.pptx/.xlsx/.docx**: Document formats (vs templates) for workflow integration
- [ ] **Email Templates**: Outlook (.oft), HTML email, corporate signatures
- [ ] **Advanced Graphics**: Enhanced drawing capabilities, vector graphics

**"Every Nook and Cranny" Deep Dive**
- [ ] **Exhaustive Property Mapping**: Identify every templatable OOXML/ODF attribute
- [ ] **Obscure Styling Controls**: Complex gradients, micro-typography, undocumented properties
- [ ] **Platform-Specific Extensions**: Microsoft/LibreOffice vendor attributes
- [ ] **Print Production**: CMYK, bleed, crop marks, spot colors, PDF/X compliance

### 🎯 Phase 3: Platform Distribution (2025 Q3-Q4)
**Design Tokens as a Service**
- [ ] **Add-in Framework**: Office.js, LibreOffice UNO, Google Apps Script
- [ ] **Template Store Publishing**: Microsoft Store, Google Templates automation
- [ ] **Corporate Subscriptions**: Enterprise token management and distribution
- [ ] **Real-time Synchronization**: Live design token updates

### 📈 Phase 4: Advanced Features (2026+)
**Enterprise Integration**
- [ ] **AI Design Compliance**: Automated brand guideline monitoring
- [ ] **Analytics Platform**: Usage insights and adoption metrics
- [ ] **Workflow Automation**: Enterprise document lifecycle management
- [ ] **International Expansion**: Multi-language, RTL, cultural formatting

## 🎯 Quality Assurance

Each OOXML structure must pass:
- [ ] **Office Compatibility**: Opens correctly in Word/Excel/PowerPoint
- [ ] **StyleStack Build**: Processes successfully with `build.py`
- [ ] **Variable Substitution**: All variables resolve correctly
- [ ] **Theme Consistency**: StyleStack Modern design applied throughout
- [ ] **Accessibility**: WCAG AAA compliance verified
- [ ] **International**: Multi-language and RTL support tested

---

**Last Updated**: September 2024
**Version**: 1.0.0
**Maintainer**: StyleStack Core Team
**License**: MIT