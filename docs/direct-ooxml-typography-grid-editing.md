# Direct OOXML Editing for Perfect Typography Grids

> Complete implementation guide for bulletproof typography grid systems through direct OOXML manipulation

## Table of Contents
- [Global Grid Constants in Document Settings](#global-grid-constants-in-document-settings)
- [Mathematically Perfect Styles](#mathematically-perfect-styles)
- [PowerPoint Master Slide Grid System](#powerpoint-master-slide-grid-system)
- [Advanced Grid Compensation System](#advanced-grid-compensation-system)
- [Automatic Table Grid Alignment](#automatic-table-grid-alignment)
- [Smart Grid Preservation Rules](#smart-grid-preservation-rules)
- [Master Control Pattern](#master-control-pattern)
- [Implementation Benefits](#implementation-benefits)

## Global Grid Constants in Document Settings

### Word: docPr/settings.xml

```xml
<w:settings>
  <!-- Define baseline grid -->
  <w:docGrid w:type="lines" w:linePitch="360"/>  <!-- 18pt baseline -->
  
  <!-- Force all paragraphs to snap -->
  <w:defaultTabStop w:val="360"/>
  <w:characterSpacingControl w:val="doNotCompress"/>
  
  <!-- Create custom document variables for grid -->
  <w:docVars>
    <w:docVar w:name="baselineGrid" w:val="360"/>
    <w:docVar w:name="halfGrid" w:val="180"/>
    <w:docVar w:name="doubleGrid" w:val="720"/>
  </w:docVars>
</w:settings>
```

### PowerPoint: presentation.xml relationships

```xml
<p:presentation>
  <p:sldSz cx="9144000" cy="6858000"/>  <!-- 10" × 7.5" -->
  <p:notesSz cx="6858000" cy="9144000"/>
  
  <!-- Grid stored in custom properties -->
  <p:custDataLst>
    <p:custData r:id="rId99">
      <p:customXml>
        <grid baseline="228600" half="114300" double="457200"/>
      </p:customXml>
    </p:custData>
  </p:custDataLst>
</p:presentation>
```

## Mathematically Perfect Styles

### Word styles.xml - Complete Grid System

```xml
<w:styles>
  <!-- Base paragraph style with grid -->
  <w:style w:type="paragraph" w:styleId="GridBase">
    <w:name w:val="Grid Base"/>
    <w:qFormat/>
    <w:pPr>
      <w:spacing 
        w:line="360" 
        w:lineRule="exact"
        w:before="0"
        w:after="0"/>
      <w:snapToGrid w:val="true"/>
    </w:pPr>
    <w:rPr>
      <w:sz w:val="24"/>  <!-- 12pt -->
    </w:rPr>
  </w:style>

  <!-- Body text: 12pt/18pt -->
  <w:style w:type="paragraph" w:styleId="Body" w:basedOn="GridBase">
    <w:name w:val="Body Grid"/>
    <w:pPr>
      <w:spacing 
        w:line="360"
        w:lineRule="exact"
        w:before="0"
        w:after="0"/>
    </w:pPr>
  </w:style>

  <!-- Small text: 10pt/18pt with compensation -->
  <w:style w:type="paragraph" w:styleId="Small">
    <w:name w:val="Small Grid"/>
    <w:pPr>
      <w:spacing 
        w:line="300"        <!-- 15pt actual -->
        w:lineRule="exact"
        w:before="30"       <!-- 1.5pt compensation -->
        w:after="30"/>      <!-- 1.5pt compensation -->
    </w:pPr>
    <w:rPr>
      <w:sz w:val="20"/>    <!-- 10pt -->
    </w:rPr>
  </w:style>

  <!-- H3: 14pt/18pt -->
  <w:style w:type="paragraph" w:styleId="Heading3">
    <w:name w:val="Heading 3 Grid"/>
    <w:pPr>
      <w:spacing 
        w:line="360"
        w:lineRule="exact"
        w:before="180"      <!-- Half baseline before -->
        w:after="180"/>     <!-- Half baseline after -->
    </w:pPr>
    <w:rPr>
      <w:sz w:val="28"/>    <!-- 14pt -->
    </w:rPr>
  </w:style>

  <!-- H2: 18pt/27pt (1.5 baselines) -->
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="Heading 2 Grid"/>
    <w:pPr>
      <w:spacing 
        w:line="540"        <!-- 27pt -->
        w:lineRule="exact"
        w:before="360"      <!-- Full baseline before -->
        w:after="180"/>     <!-- Half baseline after -->
    </w:pPr>
    <w:rPr>
      <w:sz w:val="36"/>    <!-- 18pt -->
    </w:rPr>
  </w:style>

  <!-- H1: 24pt/36pt (2 baselines) -->
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="Heading 1 Grid"/>
    <w:pPr>
      <w:spacing 
        w:line="720"        <!-- 36pt -->
        w:lineRule="exact"
        w:before="360"      <!-- Full baseline before -->
        w:after="360"/>     <!-- Full baseline after -->
    </w:pPr>
    <w:rPr>
      <w:sz w:val="48"/>    <!-- 24pt -->
    </w:rPr>
  </w:style>

  <!-- Special: Quote with 16pt/24pt -->
  <w:style w:type="paragraph" w:styleId="Quote">
    <w:name w:val="Quote Grid"/>
    <w:pPr>
      <w:spacing 
        w:line="480"        <!-- 24pt for 16pt font -->
        w:lineRule="exact"
        w:before="240"      <!-- 12pt before -->
        w:after="240"/>     <!-- 12pt after -->
      <w:ind w:left="720" w:right="720"/>  <!-- 36pt indents -->
    </w:pPr>
    <w:rPr>
      <w:sz w:val="32"/>    <!-- 16pt -->
      <w:i/>                <!-- Italic -->
    </w:rPr>
  </w:style>
</w:styles>
```

## PowerPoint Master Slide Grid System

### slideMaster1.xml

```xml
<p:sldMaster>
  <p:cSld>
    <p:bg>
      <!-- Optional: visible grid background -->
      <p:bgPr>
        <a:effectLst>
          <!-- Grid pattern effect -->
        </a:effectLst>
      </p:bgPr>
    </p:bg>
    <p:spTree>
      <!-- Define placeholder zones on grid -->
      <!-- Title zone: 0-72pt (4 baselines) -->
      <p:sp>
        <p:nvSpPr>
          <p:nvPr>
            <p:ph type="title"/>
          </p:nvPr>
        </p:nvSpPr>
        <p:spPr>
          <a:xfrm>
            <a:off x="914400" y="457200"/>       <!-- 1", 0.5" -->
            <a:ext cx="7315200" cy="914400"/>    <!-- 8" × 1" -->
          </a:xfrm>
        </p:spPr>
        <p:txBody>
          <a:bodyPr anchor="b" anchorCtr="0"/>   <!-- Bottom align -->
          <a:lstStyle>
            <a:lvl1pPr>
              <a:defRPr sz="3600"/>               <!-- 36pt -->
              <a:lnSpc>
                <a:spcPts val="3600"/>            <!-- 36pt line height -->
              </a:lnSpc>
            </a:lvl1pPr>
          </a:lstStyle>
        </p:txBody>
      </p:sp>
      
      <!-- Body zone: starts at 90pt (5 baselines) -->
      <p:sp>
        <p:nvSpPr>
          <p:nvPr>
            <p:ph type="body" idx="1"/>
          </p:nvPr>
        </p:nvSpPr>
        <p:spPr>
          <a:xfrm>
            <a:off x="914400" y="1143000"/>      <!-- 1", 1.25" -->
            <a:ext cx="7315200" cy="4572000"/>   <!-- 8" × 5" -->
          </a:xfrm>
        </p:spPr>
        <p:txBody>
          <a:bodyPr anchor="t"/>                  <!-- Top align -->
          <a:lstStyle>
            <!-- All levels with grid alignment -->
            <a:lvl1pPr marL="0">
              <a:lnSpc>
                <a:spcPts val="1800"/>            <!-- 18pt -->
              </a:lnSpc>
              <a:spcBef>
                <a:spcPts val="0"/>
              </a:spcBef>
              <a:spcAft>
                <a:spcPts val="900"/>             <!-- Half baseline -->
              </a:spcAft>
            </a:lvl1pPr>
          </a:lstStyle>
        </p:txBody>
      </p:sp>
    </p:spTree>
  </p:cSld>
  
  <!-- Define text styles for entire presentation -->
  <p:txStyles>
    <p:titleStyle>
      <a:lvl1pPr algn="l" defTabSz="914400" rtl="0" eaLnBrk="1" 
                 fontAlgn="base" latinLnBrk="0" hangingPunct="1">
        <a:lnSpc>
          <a:spcPts val="3600"/>
        </a:lnSpc>
        <a:defRPr sz="3600" kern="1200">
          <a:solidFill>
            <a:schemeClr val="tx1"/>
          </a:solidFill>
        </a:defRPr>
      </a:lvl1pPr>
    </p:titleStyle>
  </p:txStyles>
</p:sldMaster>
```

## Advanced Grid Compensation System

### Custom compensation calculator in document.xml

```xml
<!-- Embed compensation table as custom XML -->
<w:customXml>
  <w:gridCompensation baseline="360">
    <!-- Pre-calculated compensations -->
    <w:comp fontSize="8" lineHeight="160" lines="1" target="360" after="200"/>
    <w:comp fontSize="9" lineHeight="180" lines="1" target="360" after="180"/>
    <w:comp fontSize="10" lineHeight="200" lines="1" target="360" after="160"/>
    <w:comp fontSize="11" lineHeight="220" lines="1" target="360" after="140"/>
    <w:comp fontSize="13" lineHeight="260" lines="1" target="360" after="100"/>
    <w:comp fontSize="14" lineHeight="280" lines="1" target="360" after="80"/>
    <w:comp fontSize="15" lineHeight="300" lines="1" target="360" after="60"/>
    <w:comp fontSize="16" lineHeight="320" lines="1" target="360" after="40"/>
    <w:comp fontSize="17" lineHeight="340" lines="1" target="360" after="20"/>
    <!-- Multi-line compensations -->
    <w:comp fontSize="11" lineHeight="220" lines="2" target="720" after="280"/>
    <w:comp fontSize="11" lineHeight="220" lines="3" target="1080" after="420"/>
  </w:gridCompensation>
</w:customXml>
```

## Automatic Table Grid Alignment

### For tables that maintain grid

```xml
<w:tbl>
  <w:tblPr>
    <w:tblLayout w:type="fixed"/>
    <!-- Row height in exact grid multiples -->
    <w:tblStyleRowBandSize w:val="2"/>  <!-- 2 baselines per row -->
  </w:tblPr>
  <w:tr>
    <w:trPr>
      <w:trHeight w:val="720" w:hRule="exact"/>  <!-- 36pt exactly -->
    </w:trPr>
    <w:tc>
      <w:tcPr>
        <w:tcMar>
          <!-- Margins to maintain internal grid -->
          <w:top w:val="90" w:type="dxa"/>       <!-- 4.5pt -->
          <w:bottom w:val="90" w:type="dxa"/>    <!-- 4.5pt -->
        </w:tcMar>
        <w:vAlign w:val="center"/>
      </w:tcPr>
      <w:p>
        <w:pPr>
          <w:spacing w:line="540" w:lineRule="exact"/>  <!-- 27pt -->
        </w:pPr>
      </w:p>
    </w:tc>
  </w:tr>
</w:tbl>
```

## Smart Grid Preservation Rules

### Add processing instructions

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<?mso-application progid="Word.Document"?>
<?grid-system baseline="360" strict="true"?>

<w:document>
  <!-- Document content with grid rules -->
  <w:body>
    <w:sectPr>
      <!-- Grid enforcement -->
      <w:docGrid w:type="lines" w:linePitch="360" w:charSpace="0"/>
      <w:formProt w:val="false"/>
      <w:textDirection w:val="lrTb"/>
    </w:sectPr>
  </w:body>
</w:document>
```

## Master Control Pattern

### Create a grid control structure

```xml
<w:document>
  <w:gridControl>
    <w:baseline val="360"/>
    <w:rules>
      <w:rule name="heading" breaks="before,after" multiple="2"/>
      <w:rule name="list" breaks="after" multiple="1"/>
      <w:rule name="image" align="center" padding="adaptive"/>
    </w:rules>
    <w:fallback>
      <w:compensation mode="after" distribute="weighted"/>
    </w:fallback>
  </w:gridControl>
</w:document>
```

## Typography Grid Style Library

### Complete Word Style Definitions for Different Grid Systems

#### 12pt Baseline Grid (240 units)

```xml
<w:styles>
  <!-- 12pt Baseline Styles -->
  <w:style w:type="paragraph" w:styleId="Grid12Body">
    <w:name w:val="Body 12pt Grid"/>
    <w:pPr>
      <w:spacing w:line="240" w:lineRule="exact" w:before="0" w:after="0"/>
    </w:pPr>
    <w:rPr>
      <w:sz w:val="24"/>  <!-- 12pt -->
    </w:rPr>
  </w:style>
  
  <w:style w:type="paragraph" w:styleId="Grid12Small">
    <w:name w:val="Small 12pt Grid"/>
    <w:pPr>
      <w:spacing w:line="200" w:lineRule="exact" w:before="20" w:after="20"/>
    </w:pPr>
    <w:rPr>
      <w:sz w:val="20"/>  <!-- 10pt -->
    </w:rPr>
  </w:style>
  
  <w:style w:type="paragraph" w:styleId="Grid12H3">
    <w:name w:val="H3 12pt Grid"/>
    <w:pPr>
      <w:spacing w:line="240" w:lineRule="exact" w:before="120" w:after="120"/>
    </w:pPr>
    <w:rPr>
      <w:sz w:val="28"/>  <!-- 14pt -->
      <w:b/>
    </w:rPr>
  </w:style>
  
  <w:style w:type="paragraph" w:styleId="Grid12H2">
    <w:name w:val="H2 12pt Grid"/>
    <w:pPr>
      <w:spacing w:line="360" w:lineRule="exact" w:before="240" w:after="120"/>
    </w:pPr>
    <w:rPr>
      <w:sz w:val="32"/>  <!-- 16pt -->
      <w:b/>
    </w:rPr>
  </w:style>
  
  <w:style w:type="paragraph" w:styleId="Grid12H1">
    <w:name w:val="H1 12pt Grid"/>
    <w:pPr>
      <w:spacing w:line="480" w:lineRule="exact" w:before="240" w:after="240"/>
    </w:pPr>
    <w:rPr>
      <w:sz w:val="36"/>  <!-- 18pt -->
      <w:b/>
    </w:rPr>
  </w:style>
</w:styles>
```

#### 18pt Baseline Grid (360 units)

```xml
<w:styles>
  <!-- 18pt Baseline Styles -->
  <w:style w:type="paragraph" w:styleId="Grid18Body">
    <w:name w:val="Body 18pt Grid"/>
    <w:pPr>
      <w:spacing w:line="360" w:lineRule="exact" w:before="0" w:after="0"/>
    </w:pPr>
    <w:rPr>
      <w:sz w:val="24"/>  <!-- 12pt -->
    </w:rPr>
  </w:style>
  
  <w:style w:type="paragraph" w:styleId="Grid18Large">
    <w:name w:val="Large 18pt Grid"/>
    <w:pPr>
      <w:spacing w:line="360" w:lineRule="exact" w:before="0" w:after="0"/>
    </w:pPr>
    <w:rPr>
      <w:sz w:val="36"/>  <!-- 18pt -->
    </w:rPr>
  </w:style>
  
  <w:style w:type="paragraph" w:styleId="Grid18H2">
    <w:name w:val="H2 18pt Grid"/>
    <w:pPr>
      <w:spacing w:line="540" w:lineRule="exact" w:before="360" w:after="180"/>
    </w:pPr>
    <w:rPr>
      <w:sz w:val="36"/>  <!-- 18pt -->
      <w:b/>
    </w:rPr>
  </w:style>
  
  <w:style w:type="paragraph" w:styleId="Grid18H1">
    <w:name w:val="H1 18pt Grid"/>
    <w:pPr>
      <w:spacing w:line="720" w:lineRule="exact" w:before="360" w:after="360"/>
    </w:pPr>
    <w:rPr>
      <w:sz w:val="48"/>  <!-- 24pt -->
      <w:b/>
    </w:rPr>
  </w:style>
</w:styles>
```

### PowerPoint Theme Grid Styles

#### Complete text hierarchy for presentations

```xml
<p:txStyles>
  <!-- Title Style with Grid -->
  <p:titleStyle>
    <a:lvl1pPr algn="l" defTabSz="914400" rtl="0" eaLnBrk="1" 
               fontAlgn="base" latinLnBrk="0" hangingPunct="1">
      <a:lnSpc>
        <a:spcPts val="3600"/>  <!-- 36pt line height -->
      </a:lnSpc>
      <a:spcBef>
        <a:spcPts val="1800"/>  <!-- 18pt before -->
      </a:spcBef>
      <a:spcAft>
        <a:spcPts val="1800"/>  <!-- 18pt after -->
      </a:spcAft>
      <a:defRPr sz="3600" kern="1200" b="1">  <!-- 36pt, bold -->
        <a:solidFill>
          <a:schemeClr val="tx1"/>
        </a:solidFill>
      </a:defRPr>
    </a:lvl1pPr>
  </p:titleStyle>
  
  <!-- Body Style with Multi-Level Grid -->
  <p:bodyStyle>
    <!-- Level 1: 18pt on 18pt grid -->
    <a:lvl1pPr marL="0" indent="0" algn="l">
      <a:lnSpc>
        <a:spcPts val="1800"/>
      </a:lnSpc>
      <a:spcBef>
        <a:spcPts val="0"/>
      </a:spcBef>
      <a:spcAft>
        <a:spcPts val="900"/>  <!-- Half baseline after -->
      </a:spcAft>
      <a:defRPr sz="1800">
        <a:solidFill>
          <a:schemeClr val="tx1"/>
        </a:solidFill>
      </a:defRPr>
    </a:lvl1pPr>
    
    <!-- Level 2: Indented, same grid -->
    <a:lvl2pPr marL="457200" indent="-228600" algn="l">  <!-- 0.5" margin, -0.25" indent -->
      <a:lnSpc>
        <a:spcPts val="1800"/>
      </a:lnSpc>
      <a:spcAft>
        <a:spcPts val="900"/>
      </a:spcAft>
      <a:defRPr sz="1600">  <!-- Slightly smaller -->
        <a:solidFill>
          <a:schemeClr val="tx1"/>
        </a:solidFill>
      </a:defRPr>
    </a:lvl2pPr>
    
    <!-- Level 3: More indented -->
    <a:lvl3pPr marL="914400" indent="-228600" algn="l">  <!-- 1" margin -->
      <a:lnSpc>
        <a:spcPts val="1800"/>
      </a:lnSpc>
      <a:spcAft>
        <a:spcPts val="900"/>
      </a:spcAft>
      <a:defRPr sz="1400">
        <a:solidFill>
          <a:schemeClr val="tx1"/>
        </a:solidFill>
      </a:defRPr>
    </a:lvl3pPr>
  </p:bodyStyle>
  
  <!-- Other text styles -->
  <p:otherStyle>
    <a:lvl1pPr algn="l">
      <a:lnSpc>
        <a:spcPts val="1800"/>
      </a:lnSpc>
      <a:defRPr sz="1800">
        <a:solidFill>
          <a:schemeClr val="tx1"/>
        </a:solidFill>
      </a:defRPr>
    </a:lvl1pPr>
  </p:otherStyle>
</p:txStyles>
```

## Advanced Grid Validation Rules

### Grid compliance checker embedded in OOXML

```xml
<w:customXml>
  <w:gridValidation>
    <w:rules>
      <!-- All line heights must be multiples of baseline -->
      <w:rule type="lineHeight" 
              test="@w:line mod 360 = 0" 
              message="Line height must be multiple of 18pt"/>
      
      <!-- Before + after spacing must maintain grid -->
      <w:rule type="spacing" 
              test="(@w:before + @w:after + @w:line) mod 360 = 0"
              message="Total paragraph height must align to grid"/>
      
      <!-- Table rows must span grid multiples -->
      <w:rule type="tableRow" 
              test="w:trHeight/@w:val mod 360 = 0"
              message="Table rows must be multiples of baseline"/>
              
      <!-- Images must align to grid positions -->
      <w:rule type="image" 
              test="wp:positionV/wp:posOffset mod 228600 = 0"
              message="Images must align to grid positions"/>
    </w:rules>
  </w:gridValidation>
</w:customXml>
```

## Implementation Benefits

### The Key Advantages

1. **Mathematical precision** - No UI rounding errors
2. **Bulk updates** - Change baseline globally
3. **Guaranteed consistency** - Styles can't be overridden accidentally
4. **Version control friendly** - Plain text XML
5. **Automation ready** - Script can validate/fix grid alignment
6. **Cross-document** - Share styles.xml across documents
7. **Professional grade** - Typography control equivalent to InDesign or LaTeX

### Performance Characteristics

- **File size**: Minimal overhead (~2-3KB for complete style system)
- **Processing speed**: Native XML parsing, faster than programmatic styling
- **Memory usage**: Styles loaded once, applied efficiently
- **Compatibility**: Works across all Word/PowerPoint versions supporting OOXML

### Integration with Brand Systems

This approach enables:

- **Corporate template libraries** with enforced grid systems
- **Brand compliance automation** through XML validation
- **Cross-platform consistency** (Word, PowerPoint, online versions)
- **Designer-developer workflows** with precise specifications
- **Scalable typography systems** across large document sets

This approach gives you typography control equivalent to InDesign or LaTeX, just with more manual calculation upfront, but with the power of automation through your OOXML Brand Compliance Platform.

---

## Implementation Notes

Direct OOXML editing provides the foundation for your platform's **Layout Grid System** and **Typography Intelligence** engines to achieve pixel-perfect baseline alignment that's impossible through standard Office interfaces.

The mathematical precision and automation capabilities make this approach ideal for enterprise brand compliance systems requiring consistent typography across thousands of documents.