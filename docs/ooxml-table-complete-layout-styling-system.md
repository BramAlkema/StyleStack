# OOXML Table Complete Layout & Styling System

Tables in OOXML are complete layout systems - you can build entire documents using just tables with invisible borders, creating magazine-style layouts with precise control over every visual aspect.

## 1. Master Table Definition with All Properties

```xml
<w:tbl>
  <w:tblPr>
    <!-- Table positioning and alignment -->
    <w:tblpPr w:leftFromText="141" 
              w:rightFromText="141" 
              w:vertAnchor="page" 
              w:horzAnchor="margin"
              w:tblpXSpec="center"
              w:tblpY="1440"/>  <!-- 1 inch from top -->
    
    <!-- Table width and layout -->
    <w:tblW w:w="9639" w:type="dxa"/>  <!-- Exact width: 6.69 inches -->
    <w:tblLayout w:type="fixed"/>  <!-- Fixed layout for precision -->
    
    <!-- Table indentation -->
    <w:tblInd w:w="720" w:type="dxa"/>  <!-- 0.5 inch indent -->
    
    <!-- Cell spacing and margins -->
    <w:tblCellSpacing w:w="15" w:type="dxa"/>  <!-- Space between cells -->
    
    <!-- Default cell margins for entire table -->
    <w:tblCellMar>
      <w:top w:w="55" w:type="dxa"/>
      <w:left w:w="115" w:type="dxa"/>
      <w:bottom w:w="55" w:type="dxa"/>
      <w:right w:w="115" w:type="dxa"/>
    </w:tblCellMar>
    
    <!-- Visual properties -->
    <w:tblLook w:val="04A0" 
               w:firstRow="1" 
               w:lastRow="1" 
               w:firstColumn="1" 
               w:lastColumn="1"
               w:noHBand="0" 
               w:noVBand="0"/>
    
    <!-- Table shading -->
    <w:shd w:val="diagStripe" 
           w:color="E8E8E8" 
           w:fill="FFFFFF"/>
  </w:tblPr>
  
  <!-- Grid definition -->
  <w:tblGrid>
    <w:gridCol w:w="2880" w:type="dxa"/>  <!-- 2 inches -->
    <w:gridCol w:w="1440" w:type="dxa"/>  <!-- 1 inch -->
    <w:gridCol w:w="2160" w:type="dxa"/>  <!-- 1.5 inches -->
    <w:gridCol w:w="3159" w:type="dxa"/>  <!-- 2.19 inches -->
  </w:tblGrid>
</w:tbl>
```

## 2. Complex Border System

```xml
<w:tblPr>
  <!-- Table-level borders -->
  <w:tblBorders>
    <!-- Top border: double line -->
    <w:top w:val="double" 
           w:sz="12" 
           w:space="0" 
           w:color="2E7D32"
           w:themeColor="accent4"
           w:themeTint="99"/>
    
    <!-- Left border: custom dash -->
    <w:left w:val="dashDotStroked" 
            w:sz="24" 
            w:space="4" 
            w:color="1976D2"/>
    
    <!-- Bottom border: triple line -->
    <w:bottom w:val="triple" 
              w:sz="8" 
              w:space="0" 
              w:color="D32F2F"/>
    
    <!-- Right border: gradient effect (custom) -->
    <w:right w:val="single" 
             w:sz="36" 
             w:space="0">
      <w:color w:val="auto"/>
      <w:gradientFill>
        <w:stop position="0" color="FF0000"/>
        <w:stop position="100" color="0000FF"/>
      </w:gradientFill>
    </w:right>
    
    <!-- Inside borders -->
    <w:insideH w:val="dotted" 
               w:sz="6" 
               w:space="0" 
               w:color="999999"/>
    
    <w:insideV w:val="dashed" 
               w:sz="4" 
               w:space="0" 
               w:color="CCCCCC"/>
  </w:tblBorders>
</w:tblPr>
```

## 3. Advanced Conditional Formatting

```xml
<w:tblStylePr w:type="firstRow">
  <!-- First row special formatting -->
  <w:tcPr>
    <w:tcBorders>
      <w:bottom w:val="double" w:sz="6" w:color="000000"/>
    </w:tcBorders>
    <w:shd w:val="solid" w:color="auto" w:fill="1E88E5"/>
    <w:tcMar>
      <w:top w:w="144" w:type="dxa"/>     <!-- Extra padding -->
      <w:bottom w:w="144" w:type="dxa"/>
    </w:tcMar>
  </w:tcPr>
  <w:pPr>
    <w:jc w:val="center"/>
    <w:spacing w:before="60" w:after="60"/>
  </w:pPr>
  <w:rPr>
    <w:b/>
    <w:color w:val="FFFFFF"/>
    <w:sz w:val="26"/>  <!-- 13pt -->
    <w:szCs w:val="26"/>
    <w:caps/>
    <w:spacing w:val="20"/>  <!-- Letter spacing -->
  </w:rPr>
</w:tblStylePr>

<w:tblStylePr w:type="lastRow">
  <!-- Last row (totals) -->
  <w:tcPr>
    <w:tcBorders>
      <w:top w:val="double" w:sz="6" w:color="000000"/>
    </w:tcBorders>
    <w:shd w:val="solid" w:color="auto" w:fill="F5F5F5"/>
  </w:tcPr>
  <w:rPr>
    <w:b/>
    <w:sz w:val="24"/>
  </w:rPr>
</w:tblStylePr>

<w:tblStylePr w:type="firstColumn">
  <!-- First column (labels) -->
  <w:tcPr>
    <w:tcBorders>
      <w:right w:val="single" w:sz="12" w:color="E0E0E0"/>
    </w:tcBorders>
    <w:shd w:val="solid" w:color="auto" w:fill="FAFAFA"/>
    <w:tcMar>
      <w:left w:w="216" w:type="dxa"/>  <!-- Extra left padding -->
    </w:tcMar>
  </w:tcPr>
  <w:rPr>
    <w:b/>
    <w:color w:val="555555"/>
  </w:rPr>
</w:tblStylePr>

<w:tblStylePr w:type="band1Horz">
  <!-- Odd row banding -->
  <w:tcPr>
    <w:shd w:val="solid" w:color="auto" w:fill="F8F8F8"/>
  </w:tcPr>
</w:tblStylePr>

<w:tblStylePr w:type="band2Horz">
  <!-- Even row banding -->
  <w:tcPr>
    <w:shd w:val="solid" w:color="auto" w:fill="FFFFFF"/>
  </w:tcPr>
</w:tblStylePr>
```

## 4. Individual Cell Advanced Styling

```xml
<w:tc>
  <w:tcPr>
    <!-- Cell width -->
    <w:tcW w:w="2880" w:type="dxa"/>
    
    <!-- Cell-specific borders overriding table -->
    <w:tcBorders>
      <w:top w:val="nil"/>  <!-- Remove top border -->
      <w:left w:val="single" w:sz="24" w:color="FF5722">
        <!-- Custom shadow effect -->
        <w:shadow w:val="true" w:color="666666" w:fill="CCCCCC"/>
      </w:left>
      <w:bottom w:val="double" w:sz="8" w:color="4CAF50"/>
      <w:right w:val="dotDash" w:sz="12" w:color="2196F3"/>
      
      <!-- Diagonal borders -->
      <w:tl2br w:val="single" w:sz="12" w:color="9C27B0"/>
      <w:tr2bl w:val="single" w:sz="12" w:color="E91E63"/>
    </w:tcBorders>
    
    <!-- Cell margins override -->
    <w:tcMar>
      <w:top w:w="180" w:type="dxa"/>
      <w:left w:w="360" w:type="dxa"/>
      <w:bottom w:w="180" w:type="dxa"/>
      <w:right w:w="360" w:type="dxa"/>
    </w:tcMar>
    
    <!-- Cell shading with pattern -->
    <w:shd w:val="pct25" 
           w:color="003366" 
           w:fill="E6F2FF"
           w:themeFill="accent1"
           w:themeFillTint="33"/>
    
    <!-- Vertical alignment -->
    <w:vAlign w:val="center"/>
    
    <!-- Text direction -->
    <w:textDirection w:val="btLr"/>  <!-- Bottom to top, left to right -->
    
    <!-- No text wrapping -->
    <w:noWrap w:val="true"/>
    
    <!-- Cell fit text -->
    <w:tcFitText w:val="true"/>
    
    <!-- Hide cell mark -->
    <w:hideMark w:val="false"/>
  </w:tcPr>
</w:tc>
```

## 5. PowerPoint Table Complete Layout

```xml
<a:tbl>
  <a:tblPr firstRow="1" lastRow="1" firstCol="1" lastCol="1" 
           bandRow="1" bandCol="1">
    <!-- Right-to-left table -->
    <a:rtl val="0"/>
    
    <!-- Table effects -->
    <a:effectLst>
      <a:outerShdw blurRad="63500" dist="50800" 
                   dir="2700000" algn="tl" rotWithShape="0">
        <a:srgbClr val="000000">
          <a:alpha val="40000"/>
        </a:srgbClr>
      </a:outerShdw>
    </a:effectLst>
    
    <!-- 3D table effects -->
    <a:scene3d>
      <a:camera prst="orthographicFront"/>
      <a:lightRig rig="threePt" dir="t">
        <a:rot lat="0" lon="0" rev="0"/>
      </a:lightRig>
    </a:scene3d>
    
    <!-- Table style reference -->
    <a:tableStyleId>{5940675A-B579-460E-94D1-54222C63F5DA}</a:tableStyleId>
  </a:tblPr>
  
  <!-- Grid with precise column widths -->
  <a:tblGrid>
    <a:gridCol w="2286000">
      <a:extLst>
        <a:ext uri="{Column Properties}">
          <a:minW val="1828800"/>  <!-- Min width -->
          <a:maxW val="2743200"/>  <!-- Max width -->
          <a:preferredW val="2286000"/>
        </a:ext>
      </a:extLst>
    </a:gridCol>
    <a:gridCol w="1828800"/>
    <a:gridCol w="2743200"/>
  </a:tblGrid>
</a:tbl>
```

## 6. Advanced Row Properties

```xml
<w:tr>
  <w:trPr>
    <!-- Row height rules -->
    <w:trHeight w:val="567" w:hRule="exact"/>  <!-- Exact height -->
    <!-- OR -->
    <w:trHeight w:val="567" w:hRule="atLeast"/>  <!-- Minimum height -->
    
    <!-- Row can't split across pages -->
    <w:cantSplit w:val="true"/>
    
    <!-- Hidden row -->
    <w:hidden w:val="false"/>
    
    <!-- Row is header (repeats on each page) -->
    <w:tblHeader w:val="true"/>
    
    <!-- Conditional formatting lookup -->
    <w:cnfStyle w:val="100000100000" 
                w:firstRow="1" 
                w:lastRow="0" 
                w:firstColumn="0" 
                w:lastColumn="0"/>
    
    <!-- Row-level shading -->
    <w:shd w:val="horzStripe" 
           w:color="auto" 
           w:fill="FFE0B2"
           w:themeFill="accent2"
           w:themeFillTint="66"/>
    
    <!-- Row change tracking -->
    <w:ins w:id="1" w:author="John Doe" w:date="2024-01-15T10:30:00Z"/>
  </w:trPr>
</w:tr>
```

## 7. Cell Merging with Complex Layouts

```xml
<w:tr>
  <!-- Merged cell spanning 3 columns and 2 rows -->
  <w:tc>
    <w:tcPr>
      <w:gridSpan w:val="3"/>  <!-- Horizontal merge -->
      <w:vMerge w:val="restart"/>  <!-- Start vertical merge -->
      
      <!-- Special border for merged cell -->
      <w:tcBorders>
        <w:top w:val="double" w:sz="12" w:color="FF5722"/>
        <w:left w:val="double" w:sz="12" w:color="FF5722"/>
        <w:bottom w:val="double" w:sz="12" w:color="FF5722"/>
        <w:right w:val="double" w:sz="12" w:color="FF5722"/>
      </w:tcBorders>
      
      <!-- Center content in large merged cell -->
      <w:vAlign w:val="center"/>
      
      <!-- Background gradient -->
      <w:shd w:val="clear" w:color="auto">
        <w:gradientFill w:angle="45">
          <w:stop w:position="0" w:color="FFE0B2"/>
          <w:stop w:position="100" w:color="FFCC80"/>
        </w:gradientFill>
      </w:shd>
    </w:tcPr>
    
    <w:p>
      <w:pPr><w:jc w:val="center"/></w:pPr>
      <w:r><w:t>MERGED HEADER</w:t></w:r>
    </w:p>
  </w:tc>
</w:tr>

<!-- Next row continuing merge -->
<w:tr>
  <w:tc>
    <w:tcPr>
      <w:gridSpan w:val="3"/>
      <w:vMerge/>  <!-- Continue vertical merge -->
    </w:tcPr>
  </w:tc>
</w:tr>
```

## 8. Nested Table with Different Style

```xml
<w:tc>
  <w:tcPr>
    <w:tcW w:w="5760" w:type="dxa"/>
    <!-- Remove padding for nested table -->
    <w:tcMar>
      <w:top w:w="0" w:type="dxa"/>
      <w:left w:w="0" w:type="dxa"/>
      <w:bottom w:w="0" w:type="dxa"/>
      <w:right w:w="0" w:type="dxa"/>
    </w:tcMar>
  </w:tcPr>
  
  <!-- Nested table -->
  <w:tbl>
    <w:tblPr>
      <!-- Different style for nested table -->
      <w:tblStyle w:val="NestedTableStyle"/>
      
      <!-- No borders for clean nesting -->
      <w:tblBorders>
        <w:top w:val="none"/>
        <w:left w:val="none"/>
        <w:bottom w:val="none"/>
        <w:right w:val="none"/>
        <w:insideH w:val="single" w:sz="4" w:color="E0E0E0"/>
        <w:insideV w:val="none"/>
      </w:tblBorders>
      
      <!-- Tighter margins in nested table -->
      <w:tblCellMar>
        <w:top w:w="30" w:type="dxa"/>
        <w:left w:w="60" w:type="dxa"/>
        <w:bottom w:w="30" w:type="dxa"/>
        <w:right w:w="60" w:type="dxa"/>
      </w:tblCellMar>
    </w:tblPr>
  </w:tbl>
</w:tc>
```

## 9. Advanced PowerPoint Cell Styling

```xml
<a:tc>
  <!-- Row span -->
  <a:tcPr rowSpan="2" 
          marL="114300" marR="114300" 
          marT="57150" marB="57150"
          vert="vert270"
          anchor="ctr"
          anchorCtr="1"
          horzOverflow="clip">
    
    <!-- Cell fill with gradient -->
    <a:gradFill flip="none" rotWithShape="1">
      <a:gsLst>
        <a:gs pos="0">
          <a:schemeClr val="accent1">
            <a:tint val="50000"/>
          </a:schemeClr>
        </a:gs>
        <a:gs pos="100000">
          <a:schemeClr val="accent1">
            <a:shade val="50000"/>
          </a:schemeClr>
        </a:gs>
      </a:gsLst>
      <a:lin ang="2700000" scaled="1"/>
    </a:gradFill>
    
    <!-- Cell borders -->
    <a:lnL w="12700" cap="flat" cmpd="sng" algn="ctr">
      <a:solidFill>
        <a:schemeClr val="accent2"/>
      </a:solidFill>
    </a:lnL>
    <a:lnR w="12700">
      <a:solidFill>
        <a:schemeClr val="accent2"/>
      </a:solidFill>
    </a:lnR>
    <a:lnT w="25400">
      <a:solidFill>
        <a:schemeClr val="dk1"/>
      </a:solidFill>
    </a:lnT>
    <a:lnB w="25400">
      <a:solidFill>
        <a:schemeClr val="dk1"/>
      </a:solidFill>
    </a:lnB>
    
    <!-- Diagonal lines -->
    <a:lnTlToBr w="12700">
      <a:solidFill>
        <a:srgbClr val="FF0000"/>
      </a:solidFill>
    </a:lnTlToBr>
  </a:tcPr>
  
  <a:txBody>
    <a:bodyPr rtlCol="0" anchor="ctr">
      <a:spAutoFit/>
    </a:bodyPr>
  </a:txBody>
</a:tc>
```

## 10. Table with Custom Background Pattern

```xml
<w:tblPr>
  <!-- Pattern fills -->
  <w:shd w:val="diagCross" 
         w:color="BDBDBD" 
         w:fill="FFFFFF"/>
  
  <!-- Alternative patterns -->
  <!-- w:val options: 
       clear (none), solid, horzStripe, vertStripe, 
       reverseDiagStripe, diagStripe, horzCross, 
       diagCross, thinHorzStripe, thinVertStripe,
       thinReverseDiagStripe, thinDiagStripe, 
       thinHorzCross, thinDiagCross, pct5, pct10, 
       pct12, pct15, pct20, pct25, pct30, pct35,
       pct37, pct40, pct45, pct50, pct55, pct60,
       pct62, pct65, pct70, pct75, pct80, pct85,
       pct87, pct90, pct95 -->
</w:tblPr>

<!-- Individual cell with image background -->
<w:tc>
  <w:tcPr>
    <w:shd w:val="clear" w:color="auto">
      <w:background w:bgType="image">
        <v:background id="_x0000_s1025">
          <v:fill r:id="rId10" o:title="Background" 
                  recolor="t" type="frame"/>
        </v:background>
      </w:background>
    </w:shd>
  </w:tcPr>
</w:tc>
```

## 11. Smart Table Layout Properties

```xml
<w:tblPr>
  <!-- Auto-resize to fit content -->
  <w:tblLayout w:type="autofit"/>
  
  <!-- But with constraints -->
  <w:tblpPr>
    <w:tblpPgWidth w:val="8400"/>  <!-- Max width -->
    <w:tblpPgHeight w:val="10800"/>  <!-- Max height -->
  </w:tblpPr>
  
  <!-- Table overlap -->
  <w:tblOverlap w:val="overlap"/>
  
  <!-- Allow row to break across pages -->
  <w:allowBreakAcrossPage w:val="true"/>
  
  <!-- Auto resize to fit contents -->
  <w:autofit w:val="true"/>
  
  <!-- Table caption -->
  <w:tblCaption w:val="Table 1: Sales Performance Q4 2024"/>
  
  <!-- Table description for accessibility -->
  <w:tblDescription w:val="Quarterly sales data showing regional performance"/>
</w:tblPr>
```

## 12. Performance-Based Cell Coloring

```xml
<!-- Cell with conditional formatting based on value -->
<w:tc>
  <w:tcPr>
    <!-- Dynamic shading based on performance -->
    <w:conditionalFormatting>
      <w:cfRule type="cellValue" priority="1" operator="greaterThan">
        <w:formula>100</w:formula>
        <w:shd w:val="solid" w:color="auto" w:fill="C8E6C9"/>  <!-- Green -->
      </w:cfRule>
      <w:cfRule type="cellValue" priority="2" operator="between">
        <w:formula>50</w:formula>
        <w:formula>100</w:formula>
        <w:shd w:val="solid" w:color="auto" w:fill="FFF9C4"/>  <!-- Yellow -->
      </w:cfRule>
      <w:cfRule type="cellValue" priority="3" operator="lessThan">
        <w:formula>50</w:formula>
        <w:shd w:val="solid" w:color="auto" w:fill="FFCDD2"/>  <!-- Red -->
      </w:cfRule>
    </w:conditionalFormatting>
  </w:tcPr>
</w:tc>
```

## Key Table Layout Powers

- **Multi-level borders** - Table, row, and cell-specific borders
- **Complex shading** - Gradients, patterns, images
- **Conditional formatting** - By position, value, or custom rules
- **Precise spacing** - Table, row, and cell margins independently
- **3D effects** - Shadows, bevels, reflections
- **Smart merging** - Complex span patterns
- **Nested layouts** - Tables within tables with different rules
- **Dynamic sizing** - Autofit with constraints
- **Accessibility** - Captions and descriptions
- **Change tracking** - Row and cell-level revisions

Tables in OOXML are complete layout systems - you can build entire documents using just tables with invisible borders, creating magazine-style layouts with precise control over every visual aspect.