# Missing OOXML Primitives Audit

## Current Baseline Templates Status

### Word (`oo-style-word-styles.xml`) - 107 lines
**Current styles (7 total):**
- Standard (default paragraph)
- Heading  
- Text body
- List
- Caption
- DefaultParagraphFont (character)
- TableNormal (table)

**Missing Critical Styles:**
- Title, Subtitle (document structure)
- Heading 1-6 (hierarchical headings)
- Normal, Body Text, Body Text 2, Body Text 3
- Strong, Emphasis, Intense Emphasis
- Quote, Intense Quote, Subtle Emphasis
- Book Title, Article Title
- TOC Heading, TOC 1-9 (table of contents)
- Header, Footer (page structure)
- Footnote Text, Footnote Reference
- Hyperlink, FollowedHyperlink
- Index 1-9 (index styles)
- Bibliography, Endnote Text
- **~50+ table styles** (Grid tables, List tables, Colorful tables)
- **~20+ list styles** (Numbered, Bulleted, Multi-level)

### PowerPoint (`minimal-ppt-theme.xml`) - 66 lines  
**Current elements:**
- Basic theme colors (12 colors)
- Single font scheme (Inter)
- Minimal format scheme

**Missing Critical Elements:**
- **Table styles** (none exist!)
- **Chart styles** (none exist!)
- **Master slide layouts** (none exist!)
- **Shape styles** (basic shapes, callouts, arrows)
- **Effect styles** (shadows, reflections, glows)
- **Background styles** (gradients, patterns, textures)

### Excel (`oo-style-excel-styles.xml`) - 116 lines
**Current styles:**
- 6 fonts, 8 fills, 2 borders, 8 cell formats, 7 named styles

**Missing Critical Elements:**
- **Number formats** (currency, percentage, date/time)
- **Chart styles** (none exist!)
- **Pivot table styles** (none exist!)
- **Conditional formatting styles**
- **Data bar styles**
- **Icon set styles**
- **Color scale styles**

## What LibreOffice/Word Actually Have

### LibreOffice Writer Default Styles
- **45+ paragraph styles**
- **25+ character styles** 
- **15+ page styles**
- **12+ frame styles**
- **20+ list styles**
- **30+ table styles**

### Microsoft Word Default Styles
- **50+ paragraph styles**
- **30+ character styles**
- **15+ table styles**
- **10+ list styles**
- Plus built-in themes with color variations

### PowerPoint Built-in Elements
- **20+ slide master layouts**
- **50+ table styles**
- **30+ chart styles**
- **100+ shape styles**
- **20+ effect presets**

## Impact on Design Token Patching

**Current Problem:**
```xpath
//w:style[@w:styleId='Title']  # FAILS - Title style doesn't exist
//w:style[@w:styleId='Heading1']  # FAILS - Heading1 style doesn't exist
//a:tblStyleLst/a:tblStyle[@styleId='ModernGrid']  # FAILS - No table styles exist
```

**What We Need:**
- Complete style libraries in baseline templates
- All OOXML primitives that design tokens target
- Professional-quality defaults that can be patched

## Required Baseline Template Expansion

### Word Styles Expansion
- Add all LibreOffice default paragraph styles
- Add all character styles (Strong, Emphasis, etc.)
- Add table styles (Grid tables, List tables, etc.)
- Add TOC styles (TOC 1-9, TOC Heading)
- Add bibliography, footnote, index styles

### PowerPoint Template Expansion  
- Add slide master layouts (Title Slide, Two Content, etc.)
- Add complete table style library
- Add chart style definitions
- Add shape style library
- Add effect presets

### Excel Template Expansion
- Add number format library
- Add chart style definitions  
- Add pivot table styles
- Add conditional formatting styles

## Estimated Work

- **Word styles**: ~200 additional styles
- **PowerPoint elements**: ~100 additional style elements
- **Excel styles**: ~50 additional style elements
- **Total baseline expansion**: 350+ OOXML primitives to add