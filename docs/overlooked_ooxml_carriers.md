# Overlooked OOXML Carriers That Carry Ugly Defaults

> **TL;DR**: These OOXML parts get filled with system defaults if not explicitly set in base templates

## Visual Default Carriers (✅ Critical)

### **styles.xml** (Word/Excel) 
**What it carries:** Fonts, colors, sizes, spacing, table styles
**Ugly defaults if missed:**
- Times New Roman 12pt instead of brand fonts
- Black text on white instead of theme colors  
- Single line spacing instead of professional 1.15x
- Basic table borders instead of branded styles

**Base template carriers needed:**
```xml
<w:docDefaults>
  <w:rPrDefault>
    <w:rPr>
      <w:rFonts w:ascii="{{brand.font.body}}" w:hAnsi="{{brand.font.body}}"/>
      <w:sz w:val="{{text.size.body_halfpts}}"/>
      <w:color w:val="{{theme.color.text}}"/>
    </w:rPr>
  </w:rPrDefault>
  <w:pPrDefault>
    <w:pPr>
      <w:spacing w:line="{{text.line.spacing_240ths}}" w:lineRule="auto"/>
    </w:pPr>
  </w:pPrDefault>
</w:docDefaults>
```

### **theme/theme1.xml**
**What it carries:** Color/font/effect/background fill slots
**Ugly defaults if missed:**
- Office Blue accents instead of brand colors
- Calibri/Cambria instead of brand fonts
- Basic gradients instead of sophisticated fills

**Base template carriers needed:**
```xml
<a:fmtScheme name="{{brand.name}} Effects">
  <a:bgFillStyleLst>
    <a:solidFill><a:schemeClr val="lt1"/></a:solidFill>
    <a:gradFill rotWithShape="1">
      <a:gsLst>
        <a:gs pos="0"><a:schemeClr val="{{theme.bg.gradient.start}}"/></a:gs>
        <a:gs pos="100000"><a:schemeClr val="{{theme.bg.gradient.end}}"/></a:gs>
      </a:gsLst>
      <a:lin ang="{{theme.bg.gradient.angle}}" scaled="0"/>
    </a:gradFill>
  </a:bgFillStyleLst>
</a:fmtScheme>
```

### **slideMasters/*.xml** (PowerPoint)
**What it carries:** Background, placeholder txStyles, bullets  
**Ugly defaults if missed:**
- White slide backgrounds
- Bullet • instead of brand bullets
- 18pt/16pt/14pt instead of brand hierarchy

**Base template carriers needed:**
```xml
<p:cSld>
  <p:bg>
    <p:bgRef idx="{{slide.bg.fill.index}}">
      <a:schemeClr val="{{slide.bg.color}}"/>
    </p:bgRef>
  </p:bg>
</p:cSld>
<p:txStyles>
  <p:bodyStyle>
    <a:lvl1pPr marL="{{bullet.l1.margin_emu}}" indent="{{bullet.l1.indent_emu}}">
      <a:buChar char="{{bullet.l1.char}}"/>
      <a:buFont typeface="{{bullet.l1.font}}"/>
    </a:lvl1pPr>
  </p:bodyStyle>
</p:txStyles>
```

### **slideLayouts/*.xml** (PowerPoint)
**What it carries:** Placeholder positions, color remaps
**Ugly defaults if missed:**
- Generic placeholder positioning
- No color mapping = theme colors don't work right

**Base template carriers needed:**
```xml
<p:clrMapOvr>
  <a:overrideClrMapping 
    bg1="{{colormap.bg1}}" tx1="{{colormap.tx1}}"
    bg2="{{colormap.bg2}}" tx2="{{colormap.tx2}}"
    accent1="{{colormap.accent1}}" accent2="{{colormap.accent2}}"/>
</p:clrMapOvr>
```

### **slides/*.xml** 
**What it carries:** Shape geometry, fills, lines, animations
**Ugly defaults if missed:**
- No fill shapes = invisible
- No line = no borders
- Generic animations

**Base template carriers needed:**
```xml
<p:sp>
  <p:spPr>
    <a:solidFill>
      <a:srgbClr val="{{shape.default.fill}}"/>
    </a:solidFill>
    <a:ln w="{{shape.default.line.width}}">
      <a:solidFill><a:srgbClr val="{{shape.default.line.color}}"/></a:solidFill>
    </a:ln>
  </p:spPr>
</p:sp>
```

### **numbering.xml** (Word)
**What it carries:** Bullet/number glyph, indents
**Ugly defaults if missed:**
- Basic • bullets
- Generic indent spacing
- Wrong numbering formats

**Base template carriers needed:**
```xml
<w:abstractNum w:abstractNumId="0">
  <w:lvl w:ilvl="0">
    <w:numFmt w:val="{{numbering.l1.format}}"/>
    <w:lvlText w:val="{{numbering.l1.text}}"/>
    <w:lvlJc w:val="{{numbering.l1.justify}}"/>
    <w:pPr>
      <w:ind w:left="{{numbering.l1.indent}}" w:hanging="{{numbering.l1.hanging}}"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="{{numbering.l1.font}}" w:hAnsi="{{numbering.l1.font}}"/>
    </w:rPr>
  </w:lvl>
</w:abstractNum>
```

### **tableStyles.xml** (PowerPoint)
**What it carries:** Table look + default GUID
**Ugly defaults if missed:**
- Basic black lines
- No alternating row colors
- Generic cell padding

**Base template carriers needed:**
```xml
<a:tblStyleId>{{table.style.guid}}</a:tblStyleId>
<a:tblPr firstRow="{{table.header.enabled}}" bandRow="{{table.banded.enabled}}">
  <a:tblCellMar>
    <a:top w="{{table.cell.margin.top}}"/>
    <a:left w="{{table.cell.margin.left}}"/>
    <a:bottom w="{{table.cell.margin.bottom}}"/>
    <a:right w="{{table.cell.margin.right}}"/>
  </a:tblCellMar>
</a:tblPr>
```

### **xl/styles.xml** (Excel)
**What it carries:** Fonts, fills, borders, table/cell style refs
**Ugly defaults if missed:**
- Calibri 11pt everywhere
- No cell borders
- Basic table formatting

**Base template carriers needed:**
```xml
<fonts>
  <font>
    <name val="{{excel.font.default}}"/>
    <sz val="{{excel.font.size}}"/>
    <color rgb="{{excel.font.color}}"/>
  </font>
</fonts>
<cellStyleXfs>
  <xf fontId="0" fillId="0" borderId="0"/>
</cellStyleXfs>
```

### **notesMaster/handoutMaster**
**What it carries:** Footer text style & placement  
**Ugly defaults if missed:**
- Generic footer fonts
- Wrong footer positioning
- No brand consistency in notes/handouts

**Base template carriers needed:**
```xml
<p:ph type="ftr">
  <p:txBody>
    <a:bodyPr anchor="{{footer.anchor}}" wrap="none"/>
    <a:p>
      <a:pPr algn="{{footer.align}}"/>
      <a:r>
        <a:rPr lang="{{footer.lang}}" sz="{{footer.size_emu}}">
          <a:solidFill><a:schemeClr val="{{footer.color}}"/></a:solidFill>
          <a:latin typeface="{{footer.font}}"/>
        </a:rPr>
        <a:t>{{footer.text}}</a:t>
      </a:r>
    </a:p>
  </p:txBody>
</p:ph>
```

## Settings/Behavior Carriers (⚙️ Functional)

### **settings.xml** (Word)
**What it carries:** Footnote styles, zoom, compat, language
**Weird behavior if missed:**
- Wrong default language = spell check issues
- Wrong zoom = user UX issues  
- Compatibility mode = formatting breaks

**Base template carriers needed:**
```xml
<w:settings>
  <w:defaultTabStop w:val="{{word.tab.default}}"/>
  <w:characterSpacingControl w:val="{{word.spacing.control}}"/>
  <w:compat>
    <w:compatSetting w:name="compatibilityMode" w:val="{{word.compat.mode}}"/>
  </w:compat>
  <w:themeFontLang w:val="{{word.lang.default}}"/>
  <w:zoom w:percent="{{word.zoom.default}}"/>
</w:settings>
```

## Critical Color/Layout Carriers (⚡ Layout-Breaking)

### **clrMapOvr** (any slideish part)
**What it carries:** Theme slot remaps
**Layout breaks if missed:** Your brand colors drift to Office defaults

**Base template carriers needed:**
```xml
<p:clrMapOvr>
  <a:overrideClrMapping 
    bg1="{{remap.bg1}}" tx1="{{remap.tx1}}"
    bg2="{{remap.bg2}}" tx2="{{remap.tx2}}" 
    accent1="{{remap.accent1}}" accent2="{{remap.accent2}}"
    accent3="{{remap.accent3}}" accent4="{{remap.accent4}}"
    accent5="{{remap.accent5}}" accent6="{{remap.accent6}}"
    hlink="{{remap.hyperlink}}" folHlink="{{remap.hyperlink.visited}}"/>
</p:clrMapOvr>
```

### **bodyPr / rPr / pPr** 
**What it carries:** Autoshape text behavior, font/size/spacing
**Layout breaks if missed:**
- Text overflows shapes
- Wrong autofit behavior  
- Inconsistent typography

**Base template carriers needed:**
```xml
<!-- bodyPr: Text box behavior -->
<a:bodyPr 
  wrap="{{text.wrap.mode}}" 
  anchor="{{text.anchor.position}}"
  lIns="{{text.inset.left}}" rIns="{{text.inset.right}}"
  tIns="{{text.inset.top}}" bIns="{{text.inset.bottom}}">
  <a:{{text.autofit.mode}}/>
</a:bodyPr>

<!-- rPr: Run properties -->
<a:rPr lang="{{text.lang}}" sz="{{text.size_emu}}" b="{{text.bold}}" i="{{text.italic}}">
  <a:solidFill><a:schemeClr val="{{text.color}}"/></a:solidFill>
  <a:latin typeface="{{text.font}}"/>
</a:rPr>

<!-- pPr: Paragraph properties -->  
<a:pPr algn="{{para.align}}" marL="{{para.margin.left}}" indent="{{para.indent}}">
  <a:lnSpc><a:spcPts val="{{para.line.spacing}}"/></a:lnSpc>
  <a:spcBef><a:spcPts val="{{para.space.before}}"/></a:spcBef>
  <a:spcAft><a:spcPts val="{{para.space.after}}"/></a:spcAft>
</a:pPr>
```

## Summary: Don't Let OOXML Fill These With Defaults

**If you don't set these explicitly in your base templates, Office will:**
- Use system fonts instead of brand fonts
- Apply basic colors instead of theme colors  
- Create generic spacing instead of professional typography
- Generate ugly table styles instead of branded ones
- Position elements poorly instead of using design guides
- Break color consistency across slides/documents
- Make text behave unpredictably in shapes

**Solution:** Embed all these structures in your base templates with `{{carrier.property.value}}` placeholders that get resolved at build time.