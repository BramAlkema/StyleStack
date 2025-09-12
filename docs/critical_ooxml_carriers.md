# Critical OOXML Carriers Documentation

> **TL;DR**: If you set nothing else, set these essential carriers for professional templates

This document identifies the **absolute minimum** OOXML elements that must be set as StyleStack carriers to ensure templates look professional and work predictably across all Office applications.

## **1. THEME (Critical Foundation)**

### Color Scheme with Hyperlinks
```xml
<a:clrScheme name="StyleStack Colors">
  <a:dk1><a:srgbClr val="{{theme.color.dk1}}"/></a:dk1>
  <a:lt1><a:srgbClr val="{{theme.color.lt1}}"/></a:lt1>
  <a:dk2><a:srgbClr val="{{theme.color.dk2}}"/></a:dk2>
  <a:lt2><a:srgbClr val="{{theme.color.lt2}}"/></a:lt2>
  <a:accent1><a:srgbClr val="{{theme.color.accent1}}"/></a:accent1>
  <a:accent2><a:srgbClr val="{{theme.color.accent2}}"/></a:accent2>
  <a:accent3><a:srgbClr val="{{theme.color.accent3}}"/></a:accent3>
  <a:accent4><a:srgbClr val="{{theme.color.accent4}}"/></a:accent4>
  <a:accent5><a:srgbClr val="{{theme.color.accent5}}"/></a:accent5>
  <a:accent6><a:srgbClr val="{{theme.color.accent6}}"/></a:accent6>
  <!-- CRITICAL: Hyperlink colors -->
  <a:hlink><a:srgbClr val="{{theme.color.hlink}}"/></a:hlink>
  <a:folHlink><a:srgbClr val="{{theme.color.folHlink}}"/></a:folHlink>
</a:clrScheme>
```

### Font Scheme (Proper Major/Minor/EA/CS)
```xml
<a:fontScheme name="StyleStack Fonts">
  <a:majorFont>
    <a:latin typeface="{{theme.font.major.latin}}"/>
    <a:ea typeface="{{theme.font.major.ea}}"/>
    <a:cs typeface="{{theme.font.major.cs}}"/>
  </a:majorFont>
  <a:minorFont>
    <a:latin typeface="{{theme.font.minor.latin}}"/>
    <a:ea typeface="{{theme.font.minor.ea}}"/>
    <a:cs typeface="{{theme.font.minor.cs}}"/>
  </a:minorFont>
</a:fontScheme>
```

### Background Fill Style List (CRITICAL)
```xml
<a:fmtScheme name="StyleStack Effects">
  <a:fillStyleLst>
    <!-- 3 fill styles: subtle, moderate, intense -->
    <a:solidFill><a:schemeClr val="lt1"/></a:solidFill>
    <a:gradFill><!-- moderate gradient --></a:gradFill>
    <a:gradFill><!-- intense gradient --></a:gradFill>
  </a:fillStyleLst>
  
  <!-- CRITICAL: Background fills (referenced by bgRef idx) -->
  <a:bgFillStyleLst>
    <a:solidFill><a:schemeClr val="lt1"/></a:solidFill>
    <a:gradFill><!-- subtle bg gradient --></a:gradFill>
    <a:solidFill><a:schemeClr val="dk1"><a:tint val="95000"/></a:schemeClr></a:solidFill>
  </a:bgFillStyleLst>
</a:fmtScheme>
```

**Carrier Variables:**
```yaml
theme.color.hlink: "#1155CC"           # CRITICAL: hyperlink color
theme.color.folHlink: "#551A8B"        # CRITICAL: followed hyperlink
theme.font.major.latin: "Inter"        # Major font (headings)
theme.font.minor.latin: "Inter"        # Minor font (body text)
theme.font.major.ea: "Noto Sans CJK SC"    # East Asian major
theme.font.minor.ea: "Noto Sans CJK SC"    # East Asian minor  
theme.font.major.cs: "Arial"           # Complex Script major
theme.font.minor.cs: "Arial"           # Complex Script minor
```

---

## **2. POWERPOINT MASTER TEXT STYLES (Critical)**

### Levels 1-3 Fully Specified
```xml
<p:txStyles>
  <p:titleStyle>
    <a:lvl1pPr algn="{{master.title.align}}">
      <a:defRPr sz="{{master.title.size_emu}}" lang="{{master.title.lang}}"/>
    </a:lvl1pPr>
  </p:titleStyle>
  
  <p:bodyStyle>
    <!-- CRITICAL: Level 1 fully specified -->
    <a:lvl1pPr marL="{{master.level1.margin_emu}}" indent="{{master.level1.indent_emu}}">
      <a:buChar char="{{master.level1.bullet.char}}"/>
      <a:buFont typeface="{{master.level1.bullet.font}}"/>
      <a:defRPr sz="{{master.level1.size_emu}}" lang="{{master.level1.lang}}">
        <a:solidFill><a:schemeClr val="{{master.level1.color}}"/></a:solidFill>
      </a:defRPr>
    </a:lvl1pPr>
    
    <!-- CRITICAL: Level 2 fully specified -->
    <a:lvl2pPr marL="{{master.level2.margin_emu}}" indent="{{master.level2.indent_emu}}">
      <a:buChar char="{{master.level2.bullet.char}}"/>
      <a:defRPr sz="{{master.level2.size_emu}}" lang="{{master.level1.lang}}"/>
    </a:lvl2pPr>
    
    <!-- CRITICAL: Level 3 fully specified -->
    <a:lvl3pPr marL="{{master.level3.margin_emu}}" indent="{{master.level3.indent_emu}}">
      <a:buChar char="{{master.level3.bullet.char}}"/>
      <a:defRPr sz="{{master.level3.size_emu}}" lang="{{master.level1.lang}}"/>
    </a:lvl3pPr>
  </p:bodyStyle>
</p:txStyles>
```

**Carrier Variables:**
```yaml
# Title styling
master.title.size_emu: "32400"        # 18pt * 1800 EMU/pt
master.title.align: "ctr"             # l|ctr|r
master.title.lang: "en-US"

# Level 1 (CRITICAL)
master.level1.margin_emu: "457200"    # 0.5 inch left margin
master.level1.indent_emu: "-228600"   # -0.25 inch hanging indent  
master.level1.bullet.char: "•"
master.level1.bullet.font: "Symbol"
master.level1.size_emu: "18000"       # 10pt * 1800
master.level1.color: "tx1"            # theme text color
master.level1.lang: "en-US"

# Level 2 (CRITICAL)
master.level2.margin_emu: "685800"    # 0.75 inch
master.level2.indent_emu: "-228600"
master.level2.bullet.char: "◦"
master.level2.size_emu: "16200"       # 9pt * 1800

# Level 3 (CRITICAL)
master.level3.margin_emu: "914400"    # 1 inch
master.level3.indent_emu: "-228600" 
master.level3.bullet.char: "▪"
master.level3.size_emu: "14400"       # 8pt * 1800
```

---

## **3. TEXT AUTO-FIT (Critical Choice)**

### Every Placeholder Must Choose Explicitly
```xml
<p:txBody>
  <!-- CRITICAL: Choose auto-fit mode explicitly -->
  <a:bodyPr 
    wrap="none" 
    rtlCol="0"
    anchor="t"
    autofit="{{text.autofit.mode}}"
    fontScale="{{text.autofit.fontscale}}"
    lnSpcReduction="{{text.autofit.linespace}}">
  </a:bodyPr>
</p:txBody>
```

**Carrier Variables:**
```yaml
text.autofit.mode: "noAutofit"        # CRITICAL: noAutofit|normAutofit|spAutofit
text.autofit.fontscale: "100000"      # 100% (only if normAutofit)
text.autofit.linespace: "95000"       # 95% line spacing reduction
```

**Auto-fit Options:**
- `noAutofit` - Text overflows if too large (most predictable)
- `normAutofit` - Shrink font/line spacing to fit (can look terrible)
- `spAutofit` - Shrink only spaces between characters

---

## **4. SHAPE DEFAULTS (Critical Explicit Styling)**

### Every Shape Needs Explicit Fill and Line
```xml
<p:sp>
  <p:spPr>
    <!-- CRITICAL: Explicit fill, never rely on defaults -->
    <a:solidFill>
      <a:srgbClr val="{{shape.default.fill.color}}"/>
    </a:solidFill>
    
    <!-- CRITICAL: Explicit line width and color -->
    <a:ln w="{{shape.default.line.width_emu}}">
      <a:solidFill>
        <a:srgbClr val="{{shape.default.line.color}}"/>
      </a:solidFill>
    </a:ln>
  </p:spPr>
</p:sp>
```

**Carrier Variables:**
```yaml
shape.default.fill.color: "#F0F0F0"   # Light gray fill
shape.default.line.width_emu: "12700"  # 1pt in EMU
shape.default.line.color: "#CCCCCC"   # Light gray border
```

---

## **5. TABLE FLAGS + MARGINS (Critical Configuration)**

### Don't Rely on GUID Alone
```xml
<a:tbl>
  <!-- CRITICAL: Explicit table properties -->
  <a:tblPr 
    firstRow="{{table.flags.firstRow}}" 
    lastRow="{{table.flags.lastRow}}"
    firstCol="{{table.flags.firstColumn}}" 
    lastCol="{{table.flags.lastColumn}}"
    bandRow="{{table.flags.bandedRows}}" 
    bandCol="{{table.flags.bandedColumns}}">
    
    <!-- CRITICAL: Explicit cell margins -->
    <a:tblCellMar>
      <a:top w="{{table.cell.margin.top_emu}}" type="dxa"/>
      <a:left w="{{table.cell.margin.left_emu}}" type="dxa"/>
      <a:bottom w="{{table.cell.margin.bottom_emu}}" type="dxa"/>
      <a:right w="{{table.cell.margin.right_emu}}" type="dxa"/>
    </a:tblCellMar>
  </a:tblPr>
</a:tbl>
```

**Carrier Variables:**
```yaml
table.flags.firstRow: "1"             # CRITICAL: header row formatting
table.flags.lastRow: "0"              # Total row formatting
table.flags.firstColumn: "1"          # First column formatting  
table.flags.lastColumn: "0"           # Last column formatting
table.flags.bandedRows: "1"           # Alternating row colors
table.flags.bandedColumns: "0"        # Alternating column colors

table.cell.margin.top_emu: "45720"    # CRITICAL: explicit margins
table.cell.margin.bottom_emu: "45720" # (0.032 inch = 45720 EMU)
table.cell.margin.left_emu: "91440"   # (0.064 inch = 91440 EMU)  
table.cell.margin.right_emu: "91440"
```

---

## **6. TRANSITIONS (Critical Predictability)**

### Set Explicitly So Playback is Predictable
```xml
<p:slide>
  <!-- CRITICAL: Explicit transition settings -->
  <p:transition 
    spd="{{transition.speed}}" 
    advClick="{{transition.advance.click}}"
    advTm="{{transition.advance.time}}">
    
    <!-- Optional: transition type -->
    <p:fade/>  <!-- or p:cut, p:push, p:wipe, etc. -->
  </p:transition>
</p:slide>
```

**Carrier Variables:**
```yaml
transition.speed: "fast"              # slow|med|fast
transition.advance.click: "1"         # 0=auto after time, 1=on click
transition.advance.time: "0"          # milliseconds (if auto)
transition.type: "fade"               # cut|fade|push|wipe|split|reveal
```

---

## **7. COLOR MAP OVERRIDES (Layout/Slide Level)**

### When Layout/Slide Swaps Theme Slots
```xml
<p:clrMapOvr>
  <a:overrideClrMapping 
    bg1="{{colormap.bg1}}" 
    tx1="{{colormap.tx1}}"
    bg2="{{colormap.bg2}}" 
    tx2="{{colormap.tx2}}"
    accent1="{{colormap.accent1}}" 
    accent2="{{colormap.accent2}}"
    accent3="{{colormap.accent3}}" 
    accent4="{{colormap.accent4}}"
    accent5="{{colormap.accent5}}" 
    accent6="{{colormap.accent6}}"
    hlink="{{colormap.hlink}}" 
    folHlink="{{colormap.folHlink}}"/>
</p:clrMapOvr>
```

**Carrier Variables:**
```yaml
colormap.bg1: "lt1"                   # background 1 → light 1
colormap.tx1: "dk1"                   # text 1 → dark 1  
colormap.bg2: "lt2"                   # background 2 → light 2
colormap.tx2: "dk2"                   # text 2 → dark 2
colormap.accent1: "accent1"           # can remap any accent
colormap.accent2: "accent2"
# ... etc for all accent colors
colormap.hlink: "hlink"               # hyperlink mapping
colormap.folHlink: "folHlink"         # followed hyperlink mapping
```

---

## **8. GUIDES ON MASTER (Designer Love)**

### Invisible Helpers for Perfect Alignment
```xml
<p:sldMaster>
  <p:cSld>
    <!-- CRITICAL: Designer guides -->
    <p:guides>
      <p:guide orient="{{guide.horizontal.1.orient}}" pos="{{guide.horizontal.1.pos_emu}}"/>
      <p:guide orient="{{guide.vertical.1.orient}}" pos="{{guide.vertical.1.pos_emu}}"/>
      <p:guide orient="{{guide.horizontal.2.orient}}" pos="{{guide.horizontal.2.pos_emu}}"/>
      <p:guide orient="{{guide.vertical.2.orient}}" pos="{{guide.vertical.2.pos_emu}}"/>
    </p:guides>
  </p:cSld>
</p:sldMaster>
```

**Carrier Variables:**
```yaml
# Guides (designers will love you, everyone else won't notice)
guide.horizontal.1.pos_emu: "914400"     # 1 inch from top
guide.horizontal.2.pos_emu: "4572000"    # 5 inches (center for 10" slide)
guide.vertical.1.pos_emu: "914400"       # 1 inch from left  
guide.vertical.2.pos_emu: "4572000"      # 5 inches (center)
guide.horizontal.1.orient: "1"           # 1=horizontal, 0=vertical
guide.vertical.1.orient: "0"
```

---

## **Summary: The Critical 8**

If you implement **nothing else** in StyleStack carriers, implement these 8 categories:

1. **Theme** - Color scheme with hlink/folHlink + proper font scheme + bgFillStyleLst
2. **Master Text Styles** - Levels 1-3 fully specified (margins, bullets, sizes, colors, lang)
3. **Text Auto-fit** - Explicit choice in every placeholder bodyPr
4. **Shape Defaults** - Explicit solidFill and ln w= on everything
5. **Table Flags + Margins** - Don't rely on GUID alone, set explicit properties
6. **Transitions** - Set explicitly for predictable playback
7. **Color Map Overrides** - When layouts/slides remap theme slots  
8. **Guides** - Designer alignment helpers on masters

**Result**: Professional templates that work consistently across Office versions and don't surprise users with unexpected formatting.