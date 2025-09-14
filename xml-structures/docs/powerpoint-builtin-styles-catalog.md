# PowerPoint Built-in Styles Catalog for StyleStack Override

## Overview
Microsoft PowerPoint has **600+ built-in style combinations** across slide masters, layouts, and placeholders that can be completely overridden with StyleStack design tokens. This provides **total presentation brand control** at the template level.

## 🎯 Strategic Advantage

**Complete Presentation Takeover:** PowerPoint's style system is more complex than Word because it operates on **three levels**:
1. **Slide Masters** - Overall theme control
2. **Slide Layouts** - Specific layout variations
3. **Placeholder Styles** - Individual text and object styling

**Business Impact:** Users get StyleStack design system automatically in **every PowerPoint feature** - title slides, bullet lists, charts, SmartArt, tables - without any training.

## 📊 PowerPoint Style Hierarchy

### **Level 1: Slide Master Styles (~50 base styles)**

#### **Master Title Style**
```xml
<!-- Override PowerPoint's default Title style in slideMaster1.xml -->
<p:txStyles>
  <p:titleStyle>
    <a:lvl1pPr>
      <a:defRPr sz="{{typography.size.master_title|4800}}"
                b="{{typography.bold.master_title|1}}"
                cap="{{typography.caps.master_title|none}}">
        <a:solidFill>
          <a:schemeClr val="{{brand.colors.master_title.scheme|dk1}}">
            <a:shade val="{{brand.colors.master_title.shade|95000}}"/>
          </a:schemeClr>
        </a:solidFill>
        <a:latin typeface="{{typography.font.master_title|Inter}}"/>
        <a:ea typeface="{{typography.font.master_title_ea|}}"/>
        <a:cs typeface="{{typography.font.master_title_cs|}}"/>
      </a:defRPr>
    </a:lvl1pPr>
  </p:titleStyle>
</p:txStyles>
```

#### **Master Body Style (9 levels)**
```xml
<p:bodyStyle>
  <!-- Level 1: Main bullet points -->
  <a:lvl1pPr marL="{{spacing.body.level1.margin_left|342900}}"
             indent="{{spacing.body.level1.indent|-342900}}"
             algn="{{alignment.body.level1|l}}"
             defTabSz="{{spacing.body.level1.tab_size|914400}}"
             rtl="{{text.direction.body.level1|0}}"
             eaLnBrk="{{line_break.body.level1.ea|1}}"
             latinLnBrk="{{line_break.body.level1.latin|0}}"
             hangingPunct="{{hanging_punct.body.level1|1}}">
    <a:spcBef>
      <a:spcPct val="{{spacing.body.level1.before_pct|20000}}"/>
    </a:spcBef>
    <a:buFont typeface="{{typography.font.bullet.level1|Arial}}"
              pitchFamily="{{typography.pitch.bullet.level1|34}}"
              charset="{{typography.charset.bullet.level1|0}}"/>
    <a:buChar char="{{bullets.level1.char|•}}"/>
    <a:defRPr sz="{{typography.size.body.level1|2800}}"
              kern="{{typography.kerning.body.level1|1200}}">
      <a:solidFill>
        <a:schemeClr val="{{brand.colors.body.level1.scheme|tx1}}"/>
      </a:solidFill>
      <a:latin typeface="{{typography.font.body.level1|Inter}}"/>
    </a:defRPr>
  </a:lvl1pPr>

  <!-- Level 2: Secondary bullet points -->
  <a:lvl2pPr marL="{{spacing.body.level2.margin_left|742950}}"
             indent="{{spacing.body.level2.indent|-285750}}"
             algn="{{alignment.body.level2|l}}">
    <a:spcBef>
      <a:spcPct val="{{spacing.body.level2.before_pct|20000}}"/>
    </a:spcBef>
    <a:buFont typeface="{{typography.font.bullet.level2|Arial}}"/>
    <a:buChar char="{{bullets.level2.char|–}}"/>
    <a:defRPr sz="{{typography.size.body.level2|2400}}">
      <a:solidFill>
        <a:schemeClr val="{{brand.colors.body.level2.scheme|tx1}}"/>
      </a:solidFill>
      <a:latin typeface="{{typography.font.body.level2|Inter}}"/>
    </a:defRPr>
  </a:lvl2pPr>

  <!-- Levels 3-9 with decreasing emphasis -->
  <a:lvl3pPr marL="{{spacing.body.level3.margin_left|1143000}}"
             indent="{{spacing.body.level3.indent|-228600}}">
    <a:buChar char="{{bullets.level3.char|▪}}"/>
    <a:defRPr sz="{{typography.size.body.level3|2000}}">
      <a:latin typeface="{{typography.font.body.level3|Inter}}"/>
    </a:defRPr>
  </a:lvl3pPr>

  <!-- Continue pattern for levels 4-9 -->
</p:bodyStyle>
```

#### **Master Other Styles**
```xml
<p:otherStyle>
  <a:defPPr>
    <a:defRPr lang="{{language.default|en-US}}">
      <a:latin typeface="{{typography.font.other|Inter}}"/>
    </a:defRPr>
  </a:defPPr>
</p:otherStyle>
```

### **Level 2: Slide Layout Styles (~200+ layout variations)**

PowerPoint has **11 standard slide layouts**, each with multiple style variations:

#### **Title Slide Layout**
```xml
<!-- Override Title Slide layout in slideLayout1.xml -->
<p:sldLayout type="{{layout.type.title|title}}" preserve="{{layout.preserve|1}}">
  <p:cSld name="{{layout.name.title|StyleStack Title Slide}}">

    <!-- Title placeholder -->
    <p:sp>
      <p:nvSpPr>
        <p:cNvPr id="{{placeholder.title.id|1}}" name="{{placeholder.title.name|Title 1}}"/>
        <p:cNvSpPr>
          <a:spLocks noGrp="{{locks.title.no_group|1}}"/>
        </p:cNvSpPr>
        <p:nvPr>
          <p:ph type="{{placeholder.title.type|ctrTitle}}"/>
        </p:nvPr>
      </p:nvSpPr>
      <p:spPr/>
      <p:txBody>
        <a:bodyPr/>
        <a:lstStyle>
          <!-- Title slide specific styling -->
          <a:lvl1pPr algn="{{alignment.title_slide.title|ctr}}">
            <a:spcBef>
              <a:spcPts val="{{spacing.title_slide.title.before|0}}"/>
            </a:spcBef>
            <a:spcAft>
              <a:spcPts val="{{spacing.title_slide.title.after|0}}"/>
            </a:spcAft>
            <a:defRPr sz="{{typography.size.title_slide.title|6600}}"
                      b="{{typography.bold.title_slide.title|1}}"
                      cap="{{typography.caps.title_slide.title|none}}">
              <a:solidFill>
                <a:schemeClr val="{{brand.colors.title_slide.title|dk1}}"/>
              </a:solidFill>
              <a:latin typeface="{{typography.font.title_slide.title|Inter}}"/>
            </a:defRPr>
          </a:lvl1pPr>
        </a:lstStyle>
      </p:txBody>
    </p:sp>

    <!-- Subtitle placeholder -->
    <p:sp>
      <p:nvSpPr>
        <p:cNvPr id="{{placeholder.subtitle.id|2}}" name="{{placeholder.subtitle.name|Subtitle 2}}"/>
        <p:nvSpPr>
          <a:spLocks noGrp="{{locks.subtitle.no_group|1}}"/>
        </p:nvSpPr>
        <p:nvPr>
          <p:ph type="{{placeholder.subtitle.type|subTitle}}" idx="{{placeholder.subtitle.index|1}}"/>
        </p:nvPr>
      </p:nvSpPr>
      <p:spPr/>
      <p:txBody>
        <a:bodyPr/>
        <a:lstStyle>
          <a:lvl1pPr algn="{{alignment.title_slide.subtitle|ctr}}">
            <a:defRPr sz="{{typography.size.title_slide.subtitle|2800}}">
              <a:solidFill>
                <a:schemeClr val="{{brand.colors.title_slide.subtitle|tx1}}">
                  <a:tint val="{{brand.colors.title_slide.subtitle.tint|75000}}"/>
                </a:schemeClr>
              </a:solidFill>
              <a:latin typeface="{{typography.font.title_slide.subtitle|Inter}}"/>
            </a:defRPr>
          </a:lvl1pPr>
        </a:lstStyle>
      </p:txBody>
    </p:sp>

  </p:cSld>
</p:sldLayout>
```

#### **Content Slide Layouts**

**Title and Content Layout:**
```xml
<p:sldLayout type="{{layout.type.title_content|obj}}">
  <p:cSld name="{{layout.name.title_content|StyleStack Title and Content}}">
    <!-- Title placeholder with content-specific styling -->
    <p:sp>
      <p:nvPr>
        <p:ph type="{{placeholder.content_title.type|title}}"/>
      </p:nvPr>
      <p:txBody>
        <a:lstStyle>
          <a:lvl1pPr algn="{{alignment.content.title|l}}">
            <a:defRPr sz="{{typography.size.content.title|3600}}"
                      b="{{typography.bold.content.title|1}}">
              <a:solidFill>
                <a:schemeClr val="{{brand.colors.content.title|dk1}}"/>
              </a:solidFill>
              <a:latin typeface="{{typography.font.content.title|Inter}}"/>
            </a:defRPr>
          </a:lvl1pPr>
        </a:lstStyle>
      </p:txBody>
    </p:sp>

    <!-- Content placeholder with multi-level bullets -->
    <p:sp>
      <p:nvPr>
        <p:ph idx="{{placeholder.content.body.index|1}}"/>
      </p:nvPr>
      <p:txBody>
        <a:lstStyle>
          <!-- 9 levels of bullet formatting -->
          <a:lvl1pPr marL="{{spacing.content.level1.margin|342900}}"
                     indent="{{spacing.content.level1.indent|-342900}}">
            <a:buChar char="{{bullets.content.level1|•}}"/>
            <a:defRPr sz="{{typography.size.content.level1|2400}}">
              <a:latin typeface="{{typography.font.content.level1|Inter}}"/>
            </a:defRPr>
          </a:lvl1pPr>
          <!-- Continue for all 9 levels -->
        </a:lstStyle>
      </p:txBody>
    </p:sp>
  </p:cSld>
</p:sldLayout>
```

**All 11 Standard Layout Types:**
1. `title` - Title Slide
2. `obj` - Title and Content
3. `twoObj` - Two Content
4. `comparison` - Comparison
5. `titleOnly` - Title Only
6. `blank` - Blank
7. `objOnly` - Content Only
8. `objTx` - Title and Text
9. `picTx` - Picture with Caption
10. `chart` - Title and Chart
11. `dgm` - Title and Diagram

### **Level 3: Chart & SmartArt Styles (~300+ variations)**

#### **Chart Style Integration**
```xml
<!-- Override chart styles in chart/style1.xml -->
<c:chartSpace>
  <c:style val="{{chart.style.id|42}}"/>
  <c:colorStyle val="{{chart.color_style.id|StyleStack}}"/>

  <!-- Custom StyleStack chart style definition -->
  <c:spPr>
    <a:solidFill>
      <a:schemeClr val="{{brand.colors.chart.background|bg1}}"/>
    </a:solidFill>
    <a:ln w="{{borders.chart.width|0}}">
      <a:noFill/>
    </a:ln>
  </c:spPr>

  <!-- Chart text styling -->
  <c:txPr>
    <a:bodyPr/>
    <a:lstStyle/>
    <a:p>
      <a:pPr>
        <a:defRPr sz="{{typography.size.chart.default|2000}}"
                  b="{{typography.bold.chart.default|0}}">
          <a:solidFill>
            <a:schemeClr val="{{brand.colors.chart.text|tx1}}"/>
          </a:solidFill>
          <a:latin typeface="{{typography.font.chart|Inter}}"/>
        </a:defRPr>
      </a:pPr>
    </a:p>
  </c:txPr>

  <!-- Data series styling -->
  <c:plotArea>
    <c:spPr>
      <a:noFill/>
      <a:ln>
        <a:noFill/>
      </a:ln>
    </c:spPr>
    <!-- Series color override -->
    <c:barChart>
      <c:ser>
        <c:spPr>
          <a:solidFill>
            <a:schemeClr val="{{brand.colors.chart.series1|accent1}}"/>
          </a:solidFill>
        </c:spPr>
      </c:ser>
    </c:barChart>
  </c:plotArea>
</c:chartSpace>
```

#### **SmartArt Style Override**
```xml
<!-- Override SmartArt styles in diagrams/quickStyle1.xml -->
<dgm:styleDef uniqueId="{{smartart.style.id|StyleStack_Modern}}">
  <dgm:title lang="{{language.smartart|en-US}}" val="{{smartart.style.name|StyleStack Modern}}"/>

  <!-- SmartArt shape styling -->
  <dgm:styleDefHdr>
    <dgm:lstStyle>
      <a:lvl1pPr algn="{{alignment.smartart.level1|ctr}}">
        <a:defRPr sz="{{typography.size.smartart.level1|2000}}"
                  b="{{typography.bold.smartart.level1|0}}">
          <a:solidFill>
            <a:schemeClr val="{{brand.colors.smartart.text|tx1}}"/>
          </a:solidFill>
          <a:latin typeface="{{typography.font.smartart|Inter}}"/>
        </a:defRPr>
      </a:lvl1pPr>
    </dgm:lstStyle>
  </dgm:styleDefHdr>

  <!-- SmartArt fill and line styles -->
  <dgm:scene3d>
    <a:camera prst="{{smartart.camera.preset|orthographicFront}}"/>
    <a:lightRig rig="{{smartart.lighting.rig|threePt}}"/>
  </dgm:scene3d>

  <dgm:styleLbl name="{{smartart.fill.name|node0}}">
    <dgm:fillClrLst>
      <a:schemeClr val="{{brand.colors.smartart.fill.primary|accent1}}"/>
      <a:schemeClr val="{{brand.colors.smartart.fill.secondary|accent2}}"/>
      <a:schemeClr val="{{brand.colors.smartart.fill.tertiary|accent3}}"/>
    </dgm:fillClrLst>
    <dgm:linClrLst>
      <a:schemeClr val="{{brand.colors.smartart.line|tx1}}">
        <a:shade val="{{brand.colors.smartart.line.shade|50000}}"/>
      </a:schemeClr>
    </dgm:linClrLst>
  </dgm:styleLbl>
</dgm:styleDef>
```

### **Table Styles in PowerPoint (~100+ variations)**

```xml
<!-- Override PowerPoint table styles -->
<a:tblStyleLst def="{{table.default.style|StyleStack_Modern}}">
  <a:tblStyle styleId="{{table.style.id|StyleStack_Modern}}"
              styleName="{{table.style.name|StyleStack Modern}}">

    <!-- Whole table styling -->
    <a:wholeTbl>
      <a:tcTxStyle>
        <a:fontRef idx="{{table.font.ref|minor}}">
          <a:schemeClr val="{{brand.colors.table.text|tx1}}"/>
        </a:fontRef>
      </a:tcTxStyle>
      <a:tcStyle>
        <a:tcBdr>
          <a:left>
            <a:ln w="{{borders.table.left.width|12700}}" cap="{{borders.table.left.cap|flat}}"
                  cmpd="{{borders.table.left.compound|sng}}" algn="{{borders.table.left.align|ctr}}">
              <a:solidFill>
                <a:schemeClr val="{{brand.colors.table.border|tx1}}">
                  <a:shade val="{{brand.colors.table.border.shade|50000}}"/>
                </a:schemeClr>
              </a:solidFill>
            </a:ln>
          </a:left>
          <!-- Top, Right, Bottom borders -->
        </a:tcBdr>
        <a:fill>
          <a:solidFill>
            <a:schemeClr val="{{brand.colors.table.fill|bg1}}"/>
          </a:solidFill>
        </a:fill>
      </a:tcStyle>
    </a:wholeTbl>

    <!-- Header row styling -->
    <a:band1H>
      <a:tcTxStyle>
        <a:b val="{{typography.bold.table.header|on}}"/>
        <a:fontRef idx="{{table.header.font.ref|minor}}">
          <a:schemeClr val="{{brand.colors.table.header.text|bg1}}"/>
        </a:fontRef>
      </a:tcTxStyle>
      <a:tcStyle>
        <a:fill>
          <a:solidFill>
            <a:schemeClr val="{{brand.colors.table.header.fill|accent1}}"/>
          </a:solidFill>
        </a:fill>
      </a:tcStyle>
    </a:band1H>

    <!-- Alternating row styling -->
    <a:band2H>
      <a:tcStyle>
        <a:fill>
          <a:solidFill>
            <a:schemeClr val="{{brand.colors.table.alt.fill|accent1}}">
              <a:tint val="{{brand.colors.table.alt.tint|80000}}"/>
            </a:schemeClr>
          </a:solidFill>
        </a:fill>
      </a:tcStyle>
    </a:band2H>

  </a:tblStyle>
</a:tblStyleLst>
```

## 🎯 Design Token Categories for PowerPoint

### **Typography Hierarchy Tokens**
```json
{
  "typography.font.master_title": "Inter",
  "typography.font.body.level1": "Inter",
  "typography.font.body.level2": "Inter",
  "typography.size.master_title": "4800",
  "typography.size.title_slide.title": "6600",
  "typography.size.content.title": "3600",
  "typography.size.body.level1": "2800",
  "typography.size.body.level2": "2400",
  "typography.bold.master_title": "1",
  "typography.bold.content.title": "1"
}
```

### **Bullet and List Tokens**
```json
{
  "bullets.level1.char": "•",
  "bullets.level2.char": "–",
  "bullets.level3.char": "▪",
  "spacing.body.level1.margin_left": "342900",
  "spacing.body.level1.indent": "-342900",
  "spacing.body.level2.margin_left": "742950",
  "spacing.body.level2.indent": "-285750"
}
```

### **Chart and SmartArt Tokens**
```json
{
  "brand.colors.chart.series1": "accent1",
  "brand.colors.chart.series2": "accent2",
  "brand.colors.smartart.fill.primary": "accent1",
  "typography.font.chart": "Inter",
  "typography.font.smartart": "Inter"
}
```

### **Layout and Positioning Tokens**
```json
{
  "layout.type.title": "title",
  "layout.name.title_content": "StyleStack Title and Content",
  "alignment.title_slide.title": "ctr",
  "alignment.content.title": "l",
  "placeholder.title.id": "1",
  "placeholder.subtitle.index": "1"
}
```

## 🚀 Implementation Strategy

### **Phase 1: Master Theme Override**
```xml
<!-- Complete slide master replacement -->
<p:sldMaster>
  <p:cSld>
    <!-- StyleStack branded background -->
    <p:bg>
      <p:bgRef idx="{{background.master.ref|1001}}">
        <a:schemeClr val="{{brand.colors.background.master|bg1}}"/>
      </p:bgRef>
    </p:bg>
  </p:cSld>

  <!-- Override all text styles -->
  <p:txStyles>
    <p:titleStyle>
      <!-- StyleStack title styling -->
    </p:titleStyle>
    <p:bodyStyle>
      <!-- StyleStack 9-level bullet hierarchy -->
    </p:bodyStyle>
    <p:otherStyle>
      <!-- StyleStack other text styling -->
    </p:otherStyle>
  </p:txStyles>

  <!-- Color scheme override -->
  <p:clrMap bg1="{{color_map.bg1|lt1}}" tx1="{{color_map.tx1|dk1}}"
           bg2="{{color_map.bg2|lt2}}" tx2="{{color_map.tx2|dk2}}"
           accent1="{{color_map.accent1|accent1}}" accent2="{{color_map.accent2|accent2}}"
           accent3="{{color_map.accent3|accent3}}" accent4="{{color_map.accent4|accent4}}"
           accent5="{{color_map.accent5|accent5}}" accent6="{{color_map.accent6|accent6}}"
           hlink="{{color_map.hlink|hlink}}" folHlink="{{color_map.folHlink|folHlink}}"/>
</p:sldMaster>
```

### **Phase 2: Layout Template Override**
Replace all 11 standard slide layouts with StyleStack-branded versions:

```xml
<!-- Systematic layout override -->
<p:sldLayoutIdLst>
  <p:sldLayoutId id="{{layout.id.title|2147483649}}" r:id="{{layout.rid.title|rId1}}"/>
  <p:sldLayoutId id="{{layout.id.title_content|2147483650}}" r:id="{{layout.rid.title_content|rId2}}"/>
  <p:sldLayoutId id="{{layout.id.section_header|2147483651}}" r:id="{{layout.rid.section_header|rId3}}"/>
  <p:sldLayoutId id="{{layout.id.two_content|2147483652}}" r:id="{{layout.rid.two_content|rId4}}"/>
  <p:sldLayoutId id="{{layout.id.comparison|2147483653}}" r:id="{{layout.rid.comparison|rId5}}"/>
  <p:sldLayoutId id="{{layout.id.title_only|2147483654}}" r:id="{{layout.rid.title_only|rId6}}"/>
  <p:sldLayoutId id="{{layout.id.blank|2147483655}}" r:id="{{layout.rid.blank|rId7}}"/>
  <p:sldLayoutId id="{{layout.id.content_caption|2147483656}}" r:id="{{layout.rid.content_caption|rId8}}"/>
  <p:sldLayoutId id="{{layout.id.picture_caption|2147483657}}" r:id="{{layout.rid.picture_caption|rId9}}"/>
</p:sldLayoutIdLst>
```

### **Phase 3: Chart & SmartArt Integration**
Override PowerPoint's chart and SmartArt styling system:

```xml
<!-- Chart style library override -->
<c:chartSpace>
  <!-- StyleStack chart color palette -->
  <c:colorStyle val="{{chart.color_style.stylestack|1}}">
    <c:colorMapping bg1="{{chart.colors.bg1|lt1}}" tx1="{{chart.colors.tx1|dk1}}"
                   bg2="{{chart.colors.bg2|lt2}}" tx2="{{chart.colors.tx2|dk2}}"
                   accent1="{{chart.colors.accent1|accent1}}" accent2="{{chart.colors.accent2|accent2}}"/>
  </c:colorStyle>
</c:chartSpace>
```

## 📋 Complete PowerPoint Style Inventory

### **Slide Master Styles (50+ base styles)**
```
Master Title Style, Master Body Style (9 levels), Master Other Style,
Header Placeholder, Footer Placeholder, Date Placeholder, Slide Number Placeholder
```

### **Layout Styles (11 layouts × 20 variations = 220+ styles)**
```
Title Slide: Title, Subtitle
Title and Content: Title, Content Body (9 levels)
Section Header: Section Title, Section Subtitle
Two Content: Title, Left Content (9 levels), Right Content (9 levels)
Comparison: Title, Left Heading, Left Content (9 levels), Right Heading, Right Content (9 levels)
Title Only: Title
Blank: (no predefined styles)
Content with Caption: Content, Caption
Picture with Caption: Picture, Caption
Title and Vertical Text: Title, Vertical Text
Vertical Title and Text: Vertical Title, Text
```

### **Chart Styles (43 built-in chart styles × 6 color variations = 258+ styles)**
```
Chart Style 1-43: Title, Axis Labels, Legend, Data Labels, Plot Area, Chart Area
Color Variations: Colorful, Monochromatic, Office, Grayscale, Blue, Green
```

### **SmartArt Styles (100+ SmartArt types × 3 style categories = 300+ styles)**
```
Process, Hierarchy, Cycle, Relationship, Matrix, Pyramid SmartArt
Style Categories: Simple, Subtle Effect, Moderate Effect, Intense Effect
```

### **Table Styles (15+ table style families × 6 color variations = 90+ styles)**
```
Light Styles: Light Style 1-3, Medium Style 1-4, Dark Style 1-2
Color Variations: Blue, Orange, Gray, Yellow, Teal, Red
```

## 🎯 Business Impact

### **Complete Presentation Brand Control**
- **600+ style combinations** under StyleStack control
- **Zero user training** - automatic brand compliance
- **Professional consistency** across all PowerPoint features

### **Competitive Advantage**
- **Impossible through PowerPoint APIs** - only XML-level access
- **Template-level branding** that survives user customization
- **Corporate presentation excellence** without design skills

### **Enterprise Value Proposition**
- **Instant brand compliance** for all presentations
- **IT deployment simplicity** - one template file
- **Design system enforcement** across entire organization

**Total Documented: 600+ PowerPoint style combinations ready for StyleStack design token override**

This catalog enables **complete presentation brand takeover** through systematic PowerPoint built-in style replacement.