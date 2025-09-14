# ODF Carriers & Parts: Comprehensive Documentation for LibreOffice Templates

> **Complete reference for StyleStack's OpenDocument Format (ODF) carrier variable system**

This document provides comprehensive coverage of ODF carriers, parts, and the variable substitution system that enables StyleStack's design-as-code approach for LibreOffice and OpenOffice templates.

---

## Table of Contents

1. [ODF Overview & Architecture](#odf-overview--architecture)
2. [Critical ODF Carriers](#critical-odf-carriers)
3. [ODF File Structure & Parts](#odf-file-structure--parts)
4. [ODF to OOXML Mapping](#odf-to-ooxml-mapping)
5. [Base Template Structure](#base-template-structure)
6. [Variable Resolution in ODF](#variable-resolution-in-odf)
7. [Implementation Guidelines](#implementation-guidelines)
8. [Cross-Platform Compatibility](#cross-platform-compatibility)

---

## ODF Overview & Architecture

### Key Differences from OOXML
- **ZIP-based structure** like OOXML, but different internal organization
- **XML namespaces** use different prefixes and URIs
- **Styling system** separates styles.xml from content.xml more strictly
- **Template variables** use LibreOffice-specific placeholder syntax
- **Font handling** includes complex script and East Asian font specifications

### ODF Carrier Philosophy
- **Pre-embedded Templates** - All structures with `{{carrier.property.value}}` placeholders
- **Namespace Consistency** - Proper XML namespace declarations throughout
- **Style Inheritance** - Leverage ODF's hierarchical style system
- **Cross-Platform Compatibility** - Works with LibreOffice, OpenOffice, and ODF-compatible editors

---

## Critical ODF Carriers

> **The Essential ODF Elements** that must be set to avoid ugly defaults

### 1. **FONT FACE DECLARATIONS** (Critical Foundation)

**Font definitions in styles.xml**
```xml
<office:font-face-decls>
  <!-- Body/Minor Font -->
  <style:font-face style:name="MinorFont" 
                   svg:font-family="{{typography.font.theme.minor}}" 
                   style:font-family-generic="{{typography.font.theme.minor.generic}}" 
                   style:font-pitch="{{typography.font.theme.minor.pitch}}"/>
  
  <!-- Heading/Major Font -->
  <style:font-face style:name="MajorFont" 
                   svg:font-family="{{typography.font.theme.major}}" 
                   style:font-family-generic="{{typography.font.theme.major.generic}}" 
                   style:font-pitch="{{typography.font.theme.major.pitch}}"/>
  
  <!-- East Asian Fonts -->
  <style:font-face style:name="MinorFontEA" 
                   svg:font-family="{{typography.font.theme.minor.eastAsian}}"/>
  <style:font-face style:name="MajorFontEA" 
                   svg:font-family="{{typography.font.theme.major.eastAsian}}"/>
  
  <!-- Complex Script Fonts -->
  <style:font-face style:name="MinorFontCS" 
                   svg:font-family="{{typography.font.theme.minor.complexScript}}"/>
  <style:font-face style:name="MajorFontCS" 
                   svg:font-family="{{typography.font.theme.major.complexScript}}"/>
</office:font-face-decls>
```

**Essential Variables:**
```yaml
typography.font.theme.minor: "Liberation Sans"          # Body text font
typography.font.theme.major: "Liberation Sans"          # Heading font
typography.font.theme.minor.generic: "swiss"            # Font family generic
typography.font.theme.minor.pitch: "variable"           # Font pitch
typography.font.theme.minor.eastAsian: "Noto Sans CJK SC"  # East Asian
typography.font.theme.minor.complexScript: "Arial"      # Complex scripts
```

### 2. **DEFAULT PARAGRAPH STYLE** (Critical Typography)

**Base paragraph formatting**
```xml
<style:default-style style:family="paragraph">
  <style:paragraph-properties 
    fo:language="{{typography.language.primary}}" 
    fo:country="{{typography.language.country}}" 
    style:language-asian="{{typography.language.eastAsian}}" 
    fo:hyphenate="{{typography.hyphenation.enabled}}" 
    fo:margin-top="{{spacing.paragraph.top}}" 
    fo:margin-bottom="{{spacing.paragraph.bottom}}" 
    style:line-height-at-least="{{typography.lineHeight.minimum}}" 
    style:writing-mode="{{typography.writingMode}}"/>
  
  <style:text-properties 
    fo:font-family="MinorFont" 
    fo:font-size="{{typography.size.body}}" 
    fo:color="{{color.text.primary}}" 
    style:font-family-asian="MinorFontEA" 
    style:font-size-asian="{{typography.size.body}}" 
    style:font-family-complex="MinorFontCS" 
    style:font-size-complex="{{typography.size.body}}" 
    style:letter-kerning="{{typography.kerning.enabled}}"/>
</style:default-style>
```

**Essential Variables:**
```yaml
typography.language.primary: "en"              # Primary language
typography.language.country: "US"              # Country code
typography.language.eastAsian: "zh"            # East Asian language
typography.hyphenation.enabled: "true"         # Enable hyphenation
spacing.paragraph.top: "0pt"                   # Paragraph top margin
spacing.paragraph.bottom: "6pt"                # Paragraph bottom margin
typography.lineHeight.minimum: "120%"          # Minimum line height
typography.size.body: "11pt"                   # Body text size
color.text.primary: "#000000"                  # Primary text color
typography.kerning.enabled: "true"             # Enable letter kerning
```

### 3. **HEADING STYLES HIERARCHY** (Critical Structure)

**Heading 1 through 3 definitions**
```xml
<style:style style:name="Heading_20_1" style:display-name="Heading 1" 
             style:family="paragraph" 
             style:parent-style-name="Heading" 
             style:outline-level="1">
  <style:paragraph-properties 
    fo:margin-top="{{spacing.heading1.top}}" 
    fo:margin-bottom="{{spacing.heading1.bottom}}" 
    style:line-height-at-least="{{typography.lineHeight.heading1}}" 
    fo:text-align="{{typography.alignment.heading1}}" 
    fo:keep-with-next="{{typography.keepWithNext.heading1}}" 
    fo:break-before="{{page.break.before.heading1}}"/>
  
  <style:text-properties 
    fo:font-family="MajorFont" 
    fo:font-size="{{typography.size.h1}}" 
    fo:font-weight="{{typography.weight.heading1}}" 
    fo:color="{{color.heading.primary}}" 
    style:font-family-asian="MajorFontEA" 
    style:font-size-asian="{{typography.size.h1}}" 
    style:font-family-complex="MajorFontCS" 
    style:font-size-complex="{{typography.size.h1}}"/>
</style:style>
```

**Essential Variables:**
```yaml
spacing.heading1.top: "18pt"                   # Heading 1 top margin
spacing.heading1.bottom: "12pt"                # Heading 1 bottom margin
typography.lineHeight.heading1: "130%"         # Heading 1 line height
typography.alignment.heading1: "left"          # Heading 1 alignment
typography.size.h1: "18pt"                     # Heading 1 font size
typography.weight.heading1: "bold"             # Heading 1 font weight
color.heading.primary: "#1f4788"               # Heading 1 color
```

### 4. **LIST STYLES** (Critical Bullets & Numbering)

**Multi-level list definitions**
```xml
<style:style style:name="List_20_1" style:display-name="List 1" 
             style:family="paragraph" 
             style:parent-style-name="Text_20_body" 
             style:class="list">
  <style:paragraph-properties 
    fo:margin-left="{{spacing.list1.marginLeft}}" 
    fo:margin-right="{{spacing.list1.marginRight}}" 
    fo:text-indent="{{spacing.list1.textIndent}}" 
    fo:margin-top="{{spacing.list1.top}}" 
    fo:margin-bottom="{{spacing.list1.bottom}}"/>
</style:style>

<!-- List numbering definitions -->
<text:list-style style:name="StyleStackBullets">
  <text:list-level-style-bullet text:level="1" 
    text:bullet-char="{{list.level1.bullet.char}}"
    style:num-suffix="{{list.level1.suffix}}"
    style:num-prefix="{{list.level1.prefix}}">
    <style:list-level-properties 
      text:space-before="{{list.level1.spaceBefore}}"
      text:min-label-width="{{list.level1.minLabelWidth}}"
      text:min-label-distance="{{list.level1.minLabelDistance}}"/>
    <style:text-properties 
      fo:font-family="{{list.level1.font}}"
      fo:font-size="{{list.level1.size}}"
      fo:color="{{list.level1.color}}"/>
  </text:list-level-style-bullet>
</text:list-style>
```

**Essential Variables:**
```yaml
spacing.list1.marginLeft: "0.5in"              # List 1 left margin
spacing.list1.textIndent: "-0.25in"            # List 1 hanging indent
list.level1.bullet.char: "●"                   # Level 1 bullet character
list.level1.spaceBefore: "0.25in"              # Space before bullet
list.level1.minLabelWidth: "0.25in"            # Minimum label width
list.level1.font: "Liberation Sans"            # Bullet font
list.level1.size: "11pt"                       # Bullet size
list.level1.color: "#000000"                   # Bullet color
```

### 5. **TABLE STYLES** (Critical Table Formatting)

**Table and cell style definitions**
```xml
<style:style style:name="TableStyle1" style:family="table">
  <style:table-properties 
    style:width="{{table.width}}" 
    fo:margin-left="{{table.marginLeft}}" 
    fo:margin-right="{{table.marginRight}}" 
    fo:background-color="{{color.table.background}}" 
    table:align="{{table.alignment}}" 
    style:writing-mode="{{typography.writingMode.table}}"/>
</style:style>

<style:style style:name="TableCell1" style:family="table-cell">
  <style:table-cell-properties 
    fo:padding="{{table.cell.padding}}" 
    fo:border-left="{{table.cell.borderLeft}}" 
    fo:border-right="{{table.cell.borderRight}}" 
    fo:border-top="{{table.cell.borderTop}}" 
    fo:border-bottom="{{table.cell.borderBottom}}" 
    fo:background-color="{{color.table.cell.background}}" 
    style:vertical-align="{{table.cell.verticalAlign}}"/>
</style:style>

<style:style style:name="Table_20_Heading" style:display-name="Table Heading" 
             style:family="paragraph">
  <style:text-properties 
    fo:font-weight="{{typography.weight.tableHeading}}" 
    fo:color="{{color.table.heading}}"/>
</style:style>
```

**Essential Variables:**
```yaml
table.width: "100%"                             # Table width
table.marginLeft: "auto"                        # Table left margin
table.marginRight: "auto"                       # Table right margin
color.table.background: "transparent"           # Table background
table.alignment: "margins"                      # Table alignment
table.cell.padding: "0.1in"                     # Cell padding
table.cell.borderLeft: "0.5pt solid #000000"    # Cell left border
table.cell.borderRight: "0.5pt solid #000000"   # Cell right border
table.cell.borderTop: "0.5pt solid #000000"     # Cell top border
table.cell.borderBottom: "0.5pt solid #000000"  # Cell bottom border
color.table.cell.background: "transparent"      # Cell background
table.cell.verticalAlign: "middle"              # Cell vertical alignment
typography.weight.tableHeading: "bold"          # Table heading weight
color.table.heading: "#000000"                  # Table heading color
```

### 6. **HYPERLINK STYLES** (Critical Link Appearance)

**Link and visited link definitions**
```xml
<style:style style:name="Internet_20_link" style:display-name="Internet Link" 
             style:family="text">
  <style:text-properties 
    fo:color="{{color.link.primary}}" 
    style:text-underline-style="{{typography.link.underlineStyle}}" 
    style:text-underline-width="{{typography.link.underlineWidth}}" 
    style:text-underline-color="{{color.link.underline}}"/>
</style:style>

<style:style style:name="Visited_20_Internet_20_Link" 
             style:display-name="Visited Internet Link" 
             style:family="text">
  <style:text-properties 
    fo:color="{{color.link.visited}}" 
    style:text-underline-style="{{typography.link.visited.underlineStyle}}" 
    style:text-underline-color="{{color.link.visited.underline}}"/>
</style:style>
```

**Essential Variables:**
```yaml
color.link.primary: "#0000EE"                   # Primary link color
typography.link.underlineStyle: "solid"         # Link underline style
typography.link.underlineWidth: "auto"          # Link underline width
color.link.underline: "#0000EE"                 # Link underline color
color.link.visited: "#551A8B"                   # Visited link color
typography.link.visited.underlineStyle: "solid" # Visited underline style
color.link.visited.underline: "#551A8B"         # Visited underline color
```

### 7. **PAGE LAYOUT** (Critical Page Setup)

**Page dimensions and margins**
```xml
<style:page-layout style:name="PageLayout1">
  <style:page-layout-properties 
    fo:page-width="{{page.width}}" 
    fo:page-height="{{page.height}}" 
    style:print-orientation="{{page.orientation}}" 
    fo:margin-top="{{page.margin.top}}" 
    fo:margin-bottom="{{page.margin.bottom}}" 
    fo:margin-left="{{page.margin.left}}" 
    fo:margin-right="{{page.margin.right}}" 
    style:writing-mode="{{typography.writingMode.page}}">
    
    <!-- Header Style -->
    <style:header-style>
      <style:header-footer-properties 
        fo:min-height="{{page.header.minHeight}}" 
        fo:margin-bottom="{{page.header.marginBottom}}" 
        fo:background-color="{{color.page.header.background}}"/>
    </style:header-style>
    
    <!-- Footer Style -->
    <style:footer-style>
      <style:header-footer-properties 
        fo:min-height="{{page.footer.minHeight}}" 
        fo:margin-top="{{page.footer.marginTop}}" 
        fo:background-color="{{color.page.footer.background}}"/>
    </style:footer-style>
  </style:page-layout-properties>
</style:page-layout>
```

**Essential Variables:**
```yaml
page.width: "8.5in"                             # Page width (Letter)
page.height: "11in"                             # Page height (Letter)
page.orientation: "portrait"                    # Page orientation
page.margin.top: "1in"                          # Top margin
page.margin.bottom: "1in"                       # Bottom margin
page.margin.left: "1in"                         # Left margin
page.margin.right: "1in"                        # Right margin
page.header.minHeight: "0.5in"                  # Header minimum height
page.header.marginBottom: "0.25in"              # Header bottom margin
page.footer.minHeight: "0.5in"                  # Footer minimum height
page.footer.marginTop: "0.25in"                 # Footer top margin
color.page.header.background: "transparent"     # Header background
color.page.footer.background: "transparent"     # Footer background
```

### 8. **PRESENTATION LAYOUTS** (For ODP files)

**Slide master and layout definitions**
```xml
<style:presentation-page-layout style:name="Master1-PPL1" 
                                style:display-name="Title Slide">
  <presentation:placeholder presentation:object="title" 
    svg:x="{{layout.title.x}}" svg:y="{{layout.title.y}}" 
    svg:width="{{layout.title.width}}" svg:height="{{layout.title.height}}"/>
  <presentation:placeholder presentation:object="subtitle" 
    svg:x="{{layout.subtitle.x}}" svg:y="{{layout.subtitle.y}}" 
    svg:width="{{layout.subtitle.width}}" svg:height="{{layout.subtitle.height}}"/>
  <presentation:placeholder presentation:object="footer" 
    svg:x="{{layout.footer.x}}" svg:y="{{layout.footer.y}}" 
    svg:width="{{layout.footer.width}}" svg:height="{{layout.footer.height}}"/>
</style:presentation-page-layout>

<!-- Drawing page properties -->
<style:style style:family="drawing-page" style:name="slideBackground">
  <style:drawing-page-properties 
    draw:fill="{{slide.background.fill.type}}" 
    draw:fill-color="{{slide.background.fill.color}}" 
    presentation:background-visible="{{slide.background.visible}}" 
    presentation:display-header="{{slide.header.visible}}" 
    presentation:display-footer="{{slide.footer.visible}}" 
    presentation:display-page-number="{{slide.pageNumber.visible}}"/>
</style:style>
```

**Essential Variables:**
```yaml
# Slide dimensions (13.33" x 7.5" = 16:9 ratio)
layout.title.x: "1.67in"                        # Title X position
layout.title.y: "1.23in"                        # Title Y position  
layout.title.width: "10in"                      # Title width
layout.title.height: "2.61in"                   # Title height
layout.subtitle.x: "1.67in"                     # Subtitle X position
layout.subtitle.y: "3.94in"                     # Subtitle Y position
layout.subtitle.width: "10in"                   # Subtitle width
layout.subtitle.height: "1.81in"                # Subtitle height
slide.background.fill.type: "solid"             # Background fill type
slide.background.fill.color: "#FFFFFF"          # Background color
slide.background.visible: "true"                # Background visibility
slide.footer.visible: "false"                   # Footer visibility
slide.pageNumber.visible: "false"               # Page number visibility
```

---

## ODF File Structure & Parts

### LibreOffice Presentation (.odp) Structure
```
presentation.odp (ZIP archive)
├── mimetype                    # File type identifier
├── META-INF/
│   └── manifest.xml           # Archive manifest
├── content.xml                # Document content and automatic styles
├── styles.xml                 # Named styles and page layouts
├── meta.xml                   # Document metadata
└── settings.xml               # Application settings
```

### LibreOffice Writer (.odt) Structure  
```
document.odt (ZIP archive)
├── mimetype                   # File type identifier  
├── META-INF/
│   └── manifest.xml          # Archive manifest
├── content.xml               # Document content and automatic styles
├── styles.xml                # Named styles and page layouts
├── meta.xml                  # Document metadata
└── settings.xml              # Application settings
```

### LibreOffice Calc (.ods) Structure
```
spreadsheet.ods (ZIP archive)
├── mimetype                  # File type identifier
├── META-INF/
│   └── manifest.xml         # Archive manifest  
├── content.xml              # Spreadsheet content and automatic styles
├── styles.xml               # Named styles and page layouts
├── meta.xml                 # Document metadata
└── settings.xml             # Application settings
```

### Key Files and Their Roles

#### **styles.xml** - Named Styles Repository
- **Font face declarations** - Theme font definitions
- **Default styles** - Base formatting for all content
- **Named styles** - Headings, lists, tables, characters
- **Page layouts** - Margins, headers, footers, orientation
- **Presentation layouts** - Slide master layouts (ODP only)

#### **content.xml** - Document Content & Automatic Styles  
- **Document body** - Actual content (text, shapes, tables)
- **Automatic styles** - Styles generated by LibreOffice during editing
- **Master pages** - Page sequence and layout application

#### **META-INF/manifest.xml** - Archive Contents
- **File inventory** - Lists all files in the ZIP archive
- **Media types** - MIME types for each file
- **Encryption info** - If document is password protected

---

## ODF to OOXML Mapping

### Font Declarations
| ODF | OOXML | Purpose |
|-----|-------|---------|
| `<style:font-face style:name="MinorFont" svg:font-family=""/>` | `<a:minorFont><a:latin typeface=""/></a:minorFont>` | Body text font |
| `<style:font-face style:name="MajorFont" svg:font-family=""/>` | `<a:majorFont><a:latin typeface=""/></a:majorFont>` | Heading font |
| `style:font-family-asian="MinorFontEA"` | `<a:ea typeface=""/>` | East Asian fonts |
| `style:font-family-complex="MinorFontCS"` | `<a:cs typeface=""/>` | Complex script fonts |

### Color Specifications
| ODF | OOXML | Purpose |
|-----|-------|---------|
| `fo:color="#000000"` | `<a:srgbClr val="000000"/>` | Direct color specification |
| `fo:background-color=""` | `<a:solidFill><a:srgbClr val=""/></a:solidFill>` | Background colors |
| Color scheme theme | `<a:clrScheme><a:accent1><a:srgbClr val=""/></a:accent1></a:clrScheme>` | Theme color slots |

### Typography Properties
| ODF | OOXML | Purpose |
|-----|-------|---------|
| `fo:font-size="12pt"` | `<a:defRPr sz="2400"/>` | Font size (ODF: points, OOXML: EMU/1800) |
| `fo:font-weight="bold"` | `<a:defRPr b="1"/>` | Bold formatting |
| `fo:font-style="italic"` | `<a:defRPr i="1"/>` | Italic formatting |
| `style:text-underline-style="solid"` | `<a:defRPr u="sng"/>` | Underline style |

### Layout and Spacing
| ODF | OOXML | Purpose |
|-----|-------|---------|
| `fo:margin-left="0.5in"` | `<a:lvl1pPr marL="457200"/>` | Left margin (ODF: inches, OOXML: EMU) |
| `fo:text-indent="-0.25in"` | `<a:lvl1pPr indent="-228600"/>` | Text indent |
| `style:line-height-at-least="120%"` | `<a:lnSpc><a:spcPct val="120000"/></a:lnSpc>` | Line spacing |

### List and Bullet Formatting
| ODF | OOXML | Purpose |
|-----|-------|---------|
| `text:bullet-char="●"` | `<a:buChar char="●"/>` | Bullet character |
| `style:num-prefix=""` | Bullet formatting | Prefix before bullet |
| `style:num-suffix=" "` | Bullet spacing | Suffix after bullet |
| `text:space-before="0.25in"` | `<a:lvl1pPr marL=""/>` | Space before bullet |

### Table Formatting  
| ODF | OOXML | Purpose |
|-----|-------|---------|
| `fo:border="0.5pt solid #000000"` | `<a:ln w="6350"><a:solidFill><a:srgbClr val="000000"/></a:solidFill></a:ln>` | Table borders |
| `fo:padding="0.1in"` | `<a:tblCellMar><a:left w="91440"/></a:tblCellMar>` | Cell padding |
| `style:vertical-align="middle"` | Table cell vertical alignment | Cell content alignment |

---

## Base Template Structure

### Writer Base Template (.ott) with Carriers

```xml
<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
                        xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
                        xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0">
  
  <!-- CARRIERS: Font Face Declarations -->
  <office:font-face-decls>
    <style:font-face style:name="MinorFont" 
                     svg:font-family="{{typography.font.theme.minor}}"/>
    <style:font-face style:name="MajorFont" 
                     svg:font-family="{{typography.font.theme.major}}"/>
    <style:font-face style:name="MinorFontEA" 
                     svg:font-family="{{typography.font.theme.minor.eastAsian}}"/>
    <style:font-face style:name="MajorFontEA" 
                     svg:font-family="{{typography.font.theme.major.eastAsian}}"/>
  </office:font-face-decls>
  
  <!-- CARRIERS: Named Styles -->
  <office:styles>
    <!-- Default paragraph with comprehensive language support -->
    <style:default-style style:family="paragraph">
      <style:paragraph-properties 
        fo:language="{{typography.language.primary}}" 
        fo:country="{{typography.language.country}}"
        fo:margin-top="{{spacing.paragraph.top}}" 
        fo:margin-bottom="{{spacing.paragraph.bottom}}"
        style:line-height-at-least="{{typography.lineHeight.minimum}}"/>
      
      <style:text-properties 
        fo:font-family="MinorFont" 
        fo:font-size="{{typography.size.body}}" 
        fo:color="{{color.text.primary}}"
        style:font-family-asian="MinorFontEA" 
        style:font-family-complex="MinorFontCS"/>
    </style:default-style>
    
    <!-- Heading hierarchy with carriers -->
    <style:style style:name="Heading_20_1" style:family="paragraph" style:outline-level="1">
      <style:paragraph-properties 
        fo:margin-top="{{spacing.heading1.top}}" 
        fo:margin-bottom="{{spacing.heading1.bottom}}"/>
      <style:text-properties 
        fo:font-family="MajorFont" 
        fo:font-size="{{typography.size.h1}}" 
        fo:font-weight="{{typography.weight.heading1}}" 
        fo:color="{{color.heading.primary}}"/>
    </style:style>
  </office:styles>
  
  <!-- CARRIERS: Page Layout -->
  <office:automatic-styles>
    <style:page-layout style:name="PageLayout1">
      <style:page-layout-properties 
        fo:page-width="{{page.width}}" 
        fo:page-height="{{page.height}}" 
        style:print-orientation="{{page.orientation}}" 
        fo:margin-top="{{page.margin.top}}" 
        fo:margin-bottom="{{page.margin.bottom}}" 
        fo:margin-left="{{page.margin.left}}" 
        fo:margin-right="{{page.margin.right}}">
        
        <style:header-style>
          <style:header-footer-properties 
            fo:min-height="{{page.header.minHeight}}" 
            fo:margin-bottom="{{page.header.marginBottom}}"/>
        </style:header-style>
        
        <style:footer-style>
          <style:header-footer-properties 
            fo:min-height="{{page.footer.minHeight}}" 
            fo:margin-top="{{page.footer.marginTop}}"/>
        </style:footer-style>
      </style:page-layout-properties>
    </style:page-layout>
  </office:automatic-styles>
  
  <!-- CARRIERS: Master Pages -->
  <office:master-styles>
    <style:master-page style:name="Standard" style:page-layout-name="PageLayout1">
      <style:header>
        <text:p><text:span>{{content.header.text}}</text:span></text:p>
      </style:header>
      <style:footer>
        <text:p>
          <text:span>{{content.footer.text}}</text:span>
          <text:tab/>
          <text:page-number>{{content.footer.pageNumber}}</text:page-number>
        </text:p>
      </style:footer>
    </style:master-page>
  </office:master-styles>
</office:document-styles>
```

### Calc Base Template (.ots) with Carriers

```xml
<!-- Simplified ODS styles.xml structure with key carriers -->
<office:document-styles>
  <office:font-face-decls>
    <style:font-face style:name="MinorFont" 
                     svg:font-family="{{typography.font.theme.minor}}"/>
  </office:font-face-decls>
  
  <office:styles>
    <!-- Default cell style -->
    <style:default-style style:family="table-cell">
      <style:table-cell-properties 
        fo:background-color="{{color.cell.background}}"
        fo:border="{{table.cell.border}}"
        style:vertical-align="{{table.cell.verticalAlign}}"/>
      <style:text-properties 
        fo:font-family="MinorFont" 
        fo:font-size="{{typography.size.body}}" 
        fo:color="{{color.text.primary}}"/>
    </style:default-style>
    
    <!-- Header cell style -->
    <style:style style:name="Table_20_Heading" style:family="table-cell">
      <style:table-cell-properties 
        fo:background-color="{{color.table.header.background}}"
        fo:border="{{table.header.border}}"/>
      <style:text-properties 
        fo:font-weight="{{typography.weight.tableHeading}}" 
        fo:color="{{color.table.heading}}"/>
    </style:style>
  </office:styles>
</office:document-styles>
```

### Impress Base Template (.otp) with Carriers

```xml
<!-- Simplified ODP styles.xml structure -->
<office:document-styles>
  <office:styles>
    <!-- Presentation page layouts -->
    <style:presentation-page-layout style:name="TitleSlide">
      <presentation:placeholder presentation:object="title" 
        svg:x="{{layout.title.x}}" svg:y="{{layout.title.y}}" 
        svg:width="{{layout.title.width}}" svg:height="{{layout.title.height}}"/>
      <presentation:placeholder presentation:object="subtitle" 
        svg:x="{{layout.subtitle.x}}" svg:y="{{layout.subtitle.y}}" 
        svg:width="{{layout.subtitle.width}}" svg:height="{{layout.subtitle.height}}"/>
    </style:presentation-page-layout>
    
    <!-- Default graphic style for shapes -->
    <style:default-style style:family="graphic">
      <style:graphic-properties 
        draw:fill="{{shape.default.fill.type}}" 
        draw:fill-color="{{shape.default.fill.color}}" 
        draw:stroke="{{shape.default.stroke.type}}" 
        svg:stroke-width="{{shape.default.stroke.width}}" 
        svg:stroke-color="{{shape.default.stroke.color}}"/>
    </style:default-style>
  </office:styles>
</office:document-styles>
```

---

## Variable Resolution in ODF

### Template Variable Processing Steps

1. **Base Template Loading** - Load .ott/.ots/.otp template files
2. **XML Parsing** - Parse styles.xml and content.xml files  
3. **Variable Detection** - Find `{{carrier.property.value}}` placeholders
4. **Design Token Resolution** - Resolve hierarchical token values
5. **Substitution** - Replace placeholders with resolved values
6. **Validation** - Ensure output XML is valid ODF
7. **Archive Rebuild** - Repackage as valid ZIP archive

### Variable Resolution Hierarchy

```yaml
# Design System (global foundation)
typography.font.theme.minor: "Liberation Sans"
color.text.primary: "#000000"
spacing.paragraph.bottom: "6pt"

# Corporate (brand overrides)  
org.acme.typography.font.theme.minor: "Arial"
org.acme.color.text.primary: "#1f4788"

# Channel (use-case specialization)
channel.finance.color.text.primary: "#006600"

# Template (final overrides)
template.writer.spacing.paragraph.bottom: "8pt"
```

### Unit Conversion Requirements

ODF uses different units than OOXML:

| Measurement | ODF Format | OOXML Format | Conversion |
|-------------|------------|--------------|------------|
| Font Size | `12pt` | `21600` EMU | pt × 1800 |
| Margins | `1in` | `914400` EMU | in × 914400 |
| Line Spacing | `120%` | `120000` | % × 1000 |
| Border Width | `0.5pt` | `6350` EMU | pt × 12700 |

---

## Implementation Guidelines

### Do's ✅

1. **Always declare font faces** - Never rely on LibreOffice defaults
2. **Set explicit language attributes** - Ensure proper spell checking and hyphenation
3. **Define complete heading hierarchy** - Levels 1-6 for proper document structure
4. **Specify table cell properties** - Borders, padding, alignment, background
5. **Include East Asian and Complex Script fonts** - Support international content
6. **Set explicit page layouts** - Margins, orientation, header/footer dimensions
7. **Test with actual LibreOffice** - Verify rendering matches expectations
8. **Validate ODF compliance** - Use ODF validators to ensure standards compliance

### Don'ts ❌

1. **Don't mix ODF and OOXML syntax** - Each format has distinct XML structures
2. **Don't rely on LibreOffice auto-generation** - Automatic styles can be inconsistent
3. **Don't skip font declarations** - Missing fonts default to ugly system fonts
4. **Don't forget namespace declarations** - Required for valid ODF documents
5. **Don't hardcode measurements** - Use carrier variables for all dimensions
6. **Don't ignore list formatting** - Poor bullets make documents look amateur
7. **Don't skip validation** - Invalid ODF files may not open correctly

### Best Practices

1. **Start with font face declarations** - Foundation for all typography
2. **Build complete style hierarchy** - Default → Named → Character styles
3. **Test with complex content** - Tables, lists, mixed formatting
4. **Verify cross-platform compatibility** - Test on LibreOffice and OpenOffice
5. **Document carrier mappings** - Maintain clear variable → ODF relationships
6. **Use semantic style names** - `Heading_20_1` not `a95`
7. **Implement proper inheritance** - Leverage ODF's parent-style-name system

---

## Cross-Platform Compatibility

### LibreOffice vs OpenOffice Differences

| Feature | LibreOffice | OpenOffice | Recommendation |
|---------|-------------|------------|----------------|
| ODF Version | 1.3+ support | 1.2 primarily | Target ODF 1.2 for compatibility |
| Font handling | Better font fallbacks | Limited fallbacks | Always specify fallback fonts |
| Typography | Advanced typography | Basic typography | Use conservative typography settings |
| Extensions | Modern extensions | Legacy extensions | Avoid extension-dependent features |

### Font Compatibility Matrix

| Font Category | LibreOffice Default | OpenOffice Default | StyleStack Recommendation |
|---------------|--------------------|--------------------|---------------------------|
| Latin | Liberation Sans | Arial | Liberation Sans (cross-platform) |
| East Asian | Noto Sans CJK | MS Gothic | Noto Sans CJK SC |
| Complex Script | Arial Unicode MS | Arial Unicode MS | Arial (broad compatibility) |
| Monospace | Liberation Mono | Courier New | Liberation Mono |

### Template Validation Checklist

- [ ] **Font faces declared** for all script types
- [ ] **Language attributes set** for proper localization  
- [ ] **Page layout defined** with explicit dimensions
- [ ] **Default paragraph style** with comprehensive properties
- [ ] **Heading hierarchy** complete (1-6 levels)
- [ ] **List styles defined** with proper bullet formatting
- [ ] **Table styles complete** with borders, padding, alignment
- [ ] **Hyperlink styles** for normal and visited links
- [ ] **Character styles** for emphasis, strong, citation
- [ ] **Master pages configured** with headers/footers
- [ ] **XML validity confirmed** using ODF validator
- [ ] **Cross-platform tested** on LibreOffice and OpenOffice

---

## Summary

This comprehensive guide covers everything needed to implement StyleStack's ODF carrier system for LibreOffice and OpenOffice templates:

- **8 Critical ODF carrier categories** that transform templates from basic to professional
- **Complete file structure analysis** showing where carriers get embedded
- **ODF to OOXML mapping tables** for cross-platform consistency  
- **Base template structures** for Writer, Calc, and Impress
- **Variable resolution process** enabling design-as-code workflows
- **Implementation guidelines** for building robust, cross-platform templates
- **Compatibility matrix** ensuring templates work across LibreOffice and OpenOffice

**Result**: Professional, brand-compliant LibreOffice templates that work consistently across all ODF-compatible applications with the same carrier variable system used for Microsoft Office.