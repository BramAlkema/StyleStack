# ODF Advanced Carriers: TOCs, Numbers, Bullets, Shapes & More

> **Addendum to ODF Carriers Comprehensive Documentation**

This document covers the advanced ODF carrier elements that were missing from the base documentation: Table of Contents (TOC), Numbering systems, Advanced bullet formatting, Shape and drawing elements, Footnotes/Endnotes, and other specialized ODF structures.

---

## Table of Contents

1. [Table of Contents Carriers](#table-of-contents-carriers)
2. [Advanced List and Numbering Carriers](#advanced-list-and-numbering-carriers)
3. [Shape and Drawing Carriers](#shape-and-drawing-carriers)
4. [Footnote and Endnote Carriers](#footnote-and-endnote-carriers)
5. [Index and Bibliography Carriers](#index-and-bibliography-carriers)
6. [Advanced Table Carriers](#advanced-table-carriers)
7. [Forms and Field Carriers](#forms-and-field-carriers)
8. [Mathematical Formula Carriers](#mathematical-formula-carriers)

---

## Table of Contents Carriers

### 1. **TABLE OF CONTENTS STRUCTURE** (Critical Document Navigation)

**TOC Definition and Formatting**
```xml
<text:table-of-content text:style-name="{{toc.style.name}}" text:name="{{toc.name}}">
  <!-- TOC Source Configuration -->
  <text:table-of-content-source text:outline-level="{{toc.outline.max.level}}"
                                text:use-outline-level="{{toc.use.outline.level}}"
                                text:use-index-marks="{{toc.use.index.marks}}"
                                text:use-index-source-styles="{{toc.use.index.styles}}">
    
    <!-- TOC Entry Template for Each Level -->
    <text:index-entry-template text:outline-level="1" text:style-name="{{toc.entry.level1.style}}">
      <text:index-entry-link-start text:style-name="{{toc.link.start.style}}"/>
      <text:index-entry-chapter/>
      <text:index-entry-text/>
      <text:index-entry-tab-stop style:type="{{toc.tab.stop.type}}"
                                 style:leader-char="{{toc.tab.leader.char}}"/>
      <text:index-entry-page-number/>
      <text:index-entry-link-end/>
    </text:index-entry-template>
    
    <text:index-entry-template text:outline-level="2" text:style-name="{{toc.entry.level2.style}}">
      <text:index-entry-link-start text:style-name="{{toc.link.start.style}}"/>
      <text:index-entry-chapter/>
      <text:index-entry-text/>
      <text:index-entry-tab-stop style:type="{{toc.tab.stop.type}}"
                                 style:leader-char="{{toc.tab.leader.char}}"/>
      <text:index-entry-page-number/>
      <text:index-entry-link-end/>
    </text:index-entry-template>
    
    <text:index-entry-template text:outline-level="3" text:style-name="{{toc.entry.level3.style}}">
      <text:index-entry-link-start text:style-name="{{toc.link.start.style}}"/>
      <text:index-entry-chapter/>
      <text:index-entry-text/>
      <text:index-entry-tab-stop style:type="{{toc.tab.stop.type}}"
                                 style:leader-char="{{toc.tab.leader.char}}"/>
      <text:index-entry-page-number/>
      <text:index-entry-link-end/>
    </text:index-entry-template>
  </text:table-of-content-source>
  
  <!-- TOC Body Content -->
  <text:index-body>
    <text:index-title text:style-name="{{toc.title.style}}" text:name="{{toc.title.name}}">
      <text:p text:style-name="{{toc.title.paragraph.style}}">{{toc.title.text}}</text:p>
    </text:index-title>
    
    <!-- TOC Entries (Generated Content) -->
    <text:p text:style-name="{{toc.entry.level1.style}}">
      <text:a xlink:type="simple" xlink:href="{{toc.entry.href}}" text:style-name="{{toc.link.style}}" text:visited-style-name="{{toc.link.visited.style}}">
        <text:bookmark-ref text:reference-format="{{toc.reference.format}}" text:ref-name="{{toc.reference.name}}">{{toc.entry.text}}</text:bookmark-ref>
      </text:a>
      <text:tab/>
      <text:bookmark-ref text:reference-format="page" text:ref-name="{{toc.reference.name}}">{{toc.page.number}}</text:bookmark-ref>
    </text:p>
  </text:index-body>
</text:table-of-content>
```

**Essential TOC Variables:**
```yaml
# TOC Structure
toc.style.name: "Table_20_of_20_Contents"      # Main TOC style
toc.name: "Table_20_of_20_Contents1"           # TOC identifier
toc.outline.max.level: "6"                     # Maximum heading level
toc.use.outline.level: "true"                  # Use heading levels
toc.use.index.marks: "false"                   # Use index marks
toc.use.index.styles: "false"                  # Use index styles

# TOC Entry Formatting
toc.entry.level1.style: "Contents_20_1"        # Level 1 entry style
toc.entry.level2.style: "Contents_20_2"        # Level 2 entry style
toc.entry.level3.style: "Contents_20_3"        # Level 3 entry style
toc.tab.stop.type: "right"                     # Tab stop alignment
toc.tab.leader.char: "."                       # Leader character (dots)

# TOC Links
toc.link.start.style: "Index_20_Link"          # Link start style
toc.link.style: "Internet_20_link"             # Link text style
toc.link.visited.style: "Visited_20_Internet_20_Link"  # Visited link style

# TOC Title
toc.title.style: "Index_20_Heading"            # Title container style
toc.title.paragraph.style: "Contents_20_Heading"  # Title paragraph style
toc.title.text: "Table of Contents"            # Title text
toc.reference.format: "text"                   # Reference format
```

**TOC Style Definitions:**
```xml
<!-- TOC Entry Styles -->
<style:style style:name="Contents_20_1" style:display-name="Contents 1" 
             style:family="paragraph" style:parent-style-name="Index" style:class="index">
  <style:paragraph-properties fo:margin-left="{{toc.level1.margin.left}}" 
                              fo:margin-right="{{toc.level1.margin.right}}" 
                              fo:text-indent="{{toc.level1.text.indent}}" 
                              fo:margin-top="{{toc.level1.margin.top}}" 
                              fo:margin-bottom="{{toc.level1.margin.bottom}}"/>
  <style:text-properties fo:font-size="{{toc.level1.font.size}}" 
                         fo:font-weight="{{toc.level1.font.weight}}" 
                         fo:color="{{toc.level1.color}}"/>
</style:style>

<style:style style:name="Contents_20_2" style:display-name="Contents 2" 
             style:family="paragraph" style:parent-style-name="Contents_20_1" style:class="index">
  <style:paragraph-properties fo:margin-left="{{toc.level2.margin.left}}" 
                              fo:text-indent="{{toc.level2.text.indent}}"/>
  <style:text-properties fo:font-size="{{toc.level2.font.size}}" 
                         fo:font-weight="{{toc.level2.font.weight}}"/>
</style:style>

<style:style style:name="Contents_20_Heading" style:display-name="Contents Heading" 
             style:family="paragraph" style:parent-style-name="Heading" style:class="index">
  <style:paragraph-properties fo:text-align="{{toc.heading.align}}" 
                              fo:margin-top="{{toc.heading.margin.top}}" 
                              fo:margin-bottom="{{toc.heading.margin.bottom}}"/>
  <style:text-properties fo:font-size="{{toc.heading.font.size}}" 
                         fo:font-weight="{{toc.heading.font.weight}}" 
                         fo:color="{{toc.heading.color}}"/>
</style:style>
```

**TOC Styling Variables:**
```yaml
# TOC Level 1 Formatting
toc.level1.margin.left: "0in"                  # Level 1 left margin
toc.level1.margin.right: "0in"                 # Level 1 right margin
toc.level1.text.indent: "0in"                  # Level 1 text indent
toc.level1.margin.top: "0.17in"                # Level 1 top margin
toc.level1.margin.bottom: "0in"                # Level 1 bottom margin
toc.level1.font.size: "12pt"                   # Level 1 font size
toc.level1.font.weight: "bold"                 # Level 1 font weight
toc.level1.color: "#000000"                    # Level 1 text color

# TOC Level 2 Formatting
toc.level2.margin.left: "0.2in"                # Level 2 left margin (indented)
toc.level2.text.indent: "0in"                  # Level 2 text indent
toc.level2.font.size: "11pt"                   # Level 2 font size
toc.level2.font.weight: "normal"               # Level 2 font weight

# TOC Heading Formatting
toc.heading.align: "center"                    # TOC title alignment
toc.heading.margin.top: "0.33in"               # TOC title top margin
toc.heading.margin.bottom: "0.17in"            # TOC title bottom margin
toc.heading.font.size: "16pt"                  # TOC title font size
toc.heading.font.weight: "bold"                # TOC title font weight
toc.heading.color: "#000000"                   # TOC title color
```

---

## Advanced List and Numbering Carriers

### 2. **OUTLINE NUMBERING SYSTEM** (Critical Document Structure)

**Multi-level Outline Numbering**
```xml
<text:outline-style style:name="{{outline.style.name}}">
  <!-- Level 1: 1, 2, 3, etc. -->
  <text:outline-level-style text:level="1" style:num-format="{{outline.level1.num.format}}">
    <style:list-level-properties text:space-before="{{outline.level1.space.before}}" 
                                 text:min-label-width="{{outline.level1.min.label.width}}" 
                                 text:min-label-distance="{{outline.level1.min.label.distance}}"/>
    <style:text-properties fo:font-family="{{outline.level1.font.family}}" 
                           fo:font-size="{{outline.level1.font.size}}" 
                           fo:font-weight="{{outline.level1.font.weight}}" 
                           fo:color="{{outline.level1.color}}"/>
  </text:outline-level-style>
  
  <!-- Level 2: 1.1, 1.2, 1.3, etc. -->
  <text:outline-level-style text:level="2" style:num-format="{{outline.level2.num.format}}" 
                            style:num-prefix="{{outline.level2.num.prefix}}" 
                            style:num-suffix="{{outline.level2.num.suffix}}">
    <style:list-level-properties text:space-before="{{outline.level2.space.before}}" 
                                 text:min-label-width="{{outline.level2.min.label.width}}" 
                                 text:min-label-distance="{{outline.level2.min.label.distance}}"/>
    <style:text-properties fo:font-family="{{outline.level2.font.family}}" 
                           fo:font-size="{{outline.level2.font.size}}" 
                           fo:font-weight="{{outline.level2.font.weight}}" 
                           fo:color="{{outline.level2.color}}"/>
  </text:outline-level-style>
  
  <!-- Level 3: 1.1.1, 1.1.2, 1.1.3, etc. -->
  <text:outline-level-style text:level="3" style:num-format="{{outline.level3.num.format}}" 
                            style:num-prefix="{{outline.level3.num.prefix}}" 
                            style:num-suffix="{{outline.level3.num.suffix}}">
    <style:list-level-properties text:space-before="{{outline.level3.space.before}}" 
                                 text:min-label-width="{{outline.level3.min.label.width}}" 
                                 text:min-label-distance="{{outline.level3.min.label.distance}}"/>
    <style:text-properties fo:font-family="{{outline.level3.font.family}}" 
                           fo:font-size="{{outline.level3.font.size}}" 
                           fo:font-weight="{{outline.level3.font.weight}}" 
                           fo:color="{{outline.level3.color}}"/>
  </text:outline-level-style>
</text:outline-style>
```

**Advanced List Styles**
```xml
<text:list-style style:name="{{list.style.name}}" style:display-name="{{list.style.display.name}}">
  <!-- Bullet Level 1 -->
  <text:list-level-style-bullet text:level="1" 
                                text:bullet-char="{{list.level1.bullet.char}}" 
                                style:num-suffix="{{list.level1.num.suffix}}" 
                                style:num-prefix="{{list.level1.num.prefix}}">
    <style:list-level-properties text:space-before="{{list.level1.space.before}}" 
                                 text:min-label-width="{{list.level1.min.label.width}}" 
                                 text:min-label-distance="{{list.level1.min.label.distance}}" 
                                 text:list-level-position-and-space-mode="{{list.level1.position.mode}}" 
                                 fo:text-align="{{list.level1.align}}" 
                                 fo:margin-left="{{list.level1.margin.left}}" 
                                 fo:text-indent="{{list.level1.text.indent}}"/>
    <style:text-properties fo:font-family="{{list.level1.font.family}}" 
                           fo:font-size="{{list.level1.font.size}}" 
                           fo:font-weight="{{list.level1.font.weight}}" 
                           fo:color="{{list.level1.color}}"/>
  </text:list-level-style-bullet>
  
  <!-- Bullet Level 2 -->
  <text:list-level-style-bullet text:level="2" 
                                text:bullet-char="{{list.level2.bullet.char}}" 
                                style:num-suffix="{{list.level2.num.suffix}}">
    <style:list-level-properties text:space-before="{{list.level2.space.before}}" 
                                 text:min-label-width="{{list.level2.min.label.width}}" 
                                 text:min-label-distance="{{list.level2.min.label.distance}}" 
                                 fo:margin-left="{{list.level2.margin.left}}" 
                                 fo:text-indent="{{list.level2.text.indent}}"/>
    <style:text-properties fo:font-family="{{list.level2.font.family}}" 
                           fo:font-size="{{list.level2.font.size}}" 
                           fo:color="{{list.level2.color}}"/>
  </text:list-level-style-bullet>
  
  <!-- Number Level 1: Decimal numbering -->
  <text:list-level-style-number text:level="1" 
                                style:num-format="{{list.number.level1.format}}" 
                                style:num-suffix="{{list.number.level1.suffix}}" 
                                style:num-prefix="{{list.number.level1.prefix}}">
    <style:list-level-properties text:space-before="{{list.number.level1.space.before}}" 
                                 text:min-label-width="{{list.number.level1.min.label.width}}"/>
    <style:text-properties fo:font-family="{{list.number.level1.font.family}}" 
                           fo:font-size="{{list.number.level1.font.size}}" 
                           fo:font-weight="{{list.number.level1.font.weight}}"/>
  </text:list-level-style-number>
</text:list-style>
```

**List and Numbering Variables:**
```yaml
# Outline Numbering
outline.style.name: "Outline"                  # Outline style name
outline.level1.num.format: "1"                 # Arabic numerals
outline.level1.space.before: "0in"             # Space before level 1
outline.level1.min.label.width: "0.25in"       # Minimum label width
outline.level1.min.label.distance: "0.1in"     # Distance from label
outline.level1.font.family: "Liberation Sans"  # Level 1 font
outline.level1.font.size: "12pt"               # Level 1 size
outline.level1.font.weight: "bold"             # Level 1 weight
outline.level1.color: "#000000"                # Level 1 color

outline.level2.num.format: "1"                 # Arabic numerals  
outline.level2.num.prefix: ""                  # No prefix
outline.level2.num.suffix: "."                 # Dot suffix
outline.level2.space.before: "0.25in"          # Indented from level 1
outline.level2.min.label.width: "0.3in"        # Wider label for "1.1"
outline.level2.font.weight: "normal"           # Normal weight

# Bullet Lists
list.style.name: "StyleStackBullets"           # List style name
list.style.display.name: "StyleStack Bullets" # Display name
list.level1.bullet.char: "●"                   # Solid bullet
list.level1.num.suffix: " "                    # Space after bullet
list.level1.space.before: "0.5in"              # Left margin
list.level1.min.label.width: "0.25in"          # Label width
list.level1.min.label.distance: "0.1in"        # Distance from text
list.level1.position.mode: "label-alignment"   # Position mode
list.level1.align: "left"                      # Bullet alignment
list.level1.margin.left: "0.5in"               # Left margin
list.level1.text.indent: "-0.25in"             # Hanging indent
list.level1.font.family: "Liberation Sans"     # Bullet font
list.level1.font.size: "12pt"                  # Bullet size
list.level1.color: "#000000"                   # Bullet color

list.level2.bullet.char: "◦"                   # Open bullet
list.level2.space.before: "0.75in"             # More indented
list.level2.margin.left: "0.75in"              # Margin matches
list.level2.text.indent: "-0.25in"             # Hanging indent

# Number Lists  
list.number.level1.format: "1"                 # Arabic numerals
list.number.level1.suffix: "."                 # Period suffix
list.number.level1.prefix: ""                  # No prefix
list.number.level1.space.before: "0.5in"       # Indentation
list.number.level1.min.label.width: "0.25in"   # Label width
list.number.level1.font.family: "Liberation Sans" # Number font
list.number.level1.font.size: "12pt"           # Number size
list.number.level1.font.weight: "normal"       # Number weight
```

---

## Shape and Drawing Carriers

### 3. **DRAWING AND SHAPE ELEMENTS** (Critical Graphics)

**Frame and Shape Container**
```xml
<draw:frame draw:name="{{shape.frame.name}}" 
            draw:style-name="{{shape.frame.style}}" 
            text:anchor-type="{{shape.anchor.type}}" 
            svg:x="{{shape.position.x}}" 
            svg:y="{{shape.position.y}}" 
            svg:width="{{shape.size.width}}" 
            svg:height="{{shape.size.height}}" 
            draw:z-index="{{shape.z.index}}">
  
  <!-- Text Box Content -->
  <draw:text-box fo:min-height="{{shape.textbox.min.height}}" 
                 fo:min-width="{{shape.textbox.min.width}}"
                 fo:max-height="{{shape.textbox.max.height}}" 
                 fo:max-width="{{shape.textbox.max.width}}">
    <text:p text:style-name="{{shape.text.style}}">{{shape.text.content}}</text:p>
  </draw:text-box>
</draw:frame>

<!-- Custom Shape (Rectangle, Circle, etc.) -->
<draw:custom-shape draw:name="{{customShape.name}}" 
                   draw:style-name="{{customShape.style}}" 
                   text:anchor-type="{{customShape.anchor.type}}" 
                   svg:x="{{customShape.position.x}}" 
                   svg:y="{{customShape.position.y}}" 
                   svg:width="{{customShape.size.width}}" 
                   svg:height="{{customShape.size.height}}">
  
  <!-- Shape Geometry -->
  <draw:enhanced-geometry draw:type="{{customShape.geometry.type}}" 
                          svg:viewBox="{{customShape.geometry.viewbox}}" 
                          draw:enhanced-path="{{customShape.geometry.path}}" 
                          draw:text-areas="{{customShape.text.areas}}" 
                          draw:glue-points="{{customShape.glue.points}}"/>
</draw:custom-shape>

<!-- Image Frame -->
<draw:frame draw:name="{{image.frame.name}}" 
            draw:style-name="{{image.frame.style}}" 
            text:anchor-type="{{image.anchor.type}}" 
            svg:x="{{image.position.x}}" 
            svg:y="{{image.position.y}}" 
            svg:width="{{image.size.width}}" 
            svg:height="{{image.size.height}}">
  
  <draw:image xlink:href="{{image.href}}" 
              xlink:type="{{image.link.type}}" 
              xlink:show="{{image.link.show}}" 
              xlink:actuate="{{image.link.actuate}}"
              draw:filter-name="{{image.filter.name}}"/>
</draw:frame>
```

**Shape Style Definitions**
```xml
<!-- Frame Style for Text Boxes -->
<style:style style:name="{{shape.frame.style}}" style:family="graphic">
  <style:graphic-properties fo:wrap-option="{{shape.wrap.option}}" 
                            fo:padding-top="{{shape.padding.top}}" 
                            fo:padding-bottom="{{shape.padding.bottom}}" 
                            fo:padding-left="{{shape.padding.left}}" 
                            fo:padding-right="{{shape.padding.right}}" 
                            draw:textarea-vertical-align="{{shape.text.vertical.align}}" 
                            draw:textarea-horizontal-align="{{shape.text.horizontal.align}}" 
                            draw:fill="{{shape.fill.type}}" 
                            draw:fill-color="{{shape.fill.color}}" 
                            draw:opacity="{{shape.fill.opacity}}" 
                            draw:stroke="{{shape.stroke.type}}" 
                            svg:stroke-width="{{shape.stroke.width}}" 
                            svg:stroke-color="{{shape.stroke.color}}" 
                            svg:stroke-opacity="{{shape.stroke.opacity}}" 
                            draw:stroke-linejoin="{{shape.stroke.linejoin}}" 
                            svg:stroke-linecap="{{shape.stroke.linecap}}" 
                            draw:stroke-dash="{{shape.stroke.dash}}" 
                            draw:marker-start="{{shape.marker.start}}" 
                            draw:marker-end="{{shape.marker.end}}" 
                            draw:auto-grow-width="{{shape.auto.grow.width}}" 
                            draw:auto-grow-height="{{shape.auto.grow.height}}" 
                            style:shrink-to-fit="{{shape.shrink.to.fit}}" 
                            draw:shadow="{{shape.shadow.type}}" 
                            draw:shadow-offset-x="{{shape.shadow.offset.x}}" 
                            draw:shadow-offset-y="{{shape.shadow.offset.y}}" 
                            draw:shadow-color="{{shape.shadow.color}}" 
                            draw:shadow-opacity="{{shape.shadow.opacity}}"/>
</style:style>

<!-- Custom Shape Style -->
<style:style style:name="{{customShape.style}}" style:family="graphic">
  <style:graphic-properties draw:fill="{{customShape.fill.type}}" 
                            draw:fill-color="{{customShape.fill.color}}" 
                            draw:fill-gradient-name="{{customShape.fill.gradient.name}}" 
                            draw:stroke="{{customShape.stroke.type}}" 
                            svg:stroke-width="{{customShape.stroke.width}}" 
                            svg:stroke-color="{{customShape.stroke.color}}" 
                            draw:stroke-dash="{{customShape.stroke.dash}}"/>
</style:style>
```

**Shape and Drawing Variables:**
```yaml
# Basic Frame Properties
shape.frame.name: "Frame1"                     # Frame identifier
shape.frame.style: "Graphics"                  # Graphics style
shape.anchor.type: "paragraph"                 # Anchor type
shape.position.x: "1in"                        # X position
shape.position.y: "1in"                        # Y position  
shape.size.width: "3in"                        # Shape width
shape.size.height: "2in"                       # Shape height
shape.z.index: "0"                             # Z-order

# Text Box Properties
shape.textbox.min.height: "1in"                # Minimum height
shape.textbox.min.width: "2in"                 # Minimum width
shape.textbox.max.height: "none"               # Maximum height
shape.textbox.max.width: "none"                # Maximum width
shape.text.style: "Graphics"                   # Text style
shape.text.content: "Sample Text"              # Default text

# Shape Styling
shape.wrap.option: "wrap"                      # Text wrapping
shape.padding.top: "0.1in"                     # Top padding
shape.padding.bottom: "0.1in"                  # Bottom padding
shape.padding.left: "0.1in"                    # Left padding
shape.padding.right: "0.1in"                   # Right padding
shape.text.vertical.align: "middle"            # Vertical alignment
shape.text.horizontal.align: "center"          # Horizontal alignment

# Fill Properties
shape.fill.type: "solid"                       # Fill type
shape.fill.color: "#E0E0E0"                    # Fill color
shape.fill.opacity: "100%"                     # Fill opacity

# Stroke Properties
shape.stroke.type: "solid"                     # Stroke type
shape.stroke.width: "0.02in"                   # Stroke width
shape.stroke.color: "#808080"                  # Stroke color
shape.stroke.opacity: "100%"                   # Stroke opacity
shape.stroke.linejoin: "miter"                 # Line join
shape.stroke.linecap: "butt"                   # Line cap
shape.stroke.dash: "none"                      # Dash pattern

# Auto-sizing
shape.auto.grow.width: "false"                 # Auto grow width
shape.auto.grow.height: "false"                # Auto grow height
shape.shrink.to.fit: "false"                   # Shrink to fit

# Shadow Properties
shape.shadow.type: "none"                      # Shadow type
shape.shadow.offset.x: "0.1in"                 # Shadow X offset
shape.shadow.offset.y: "0.1in"                 # Shadow Y offset
shape.shadow.color: "#808080"                  # Shadow color
shape.shadow.opacity: "50%"                    # Shadow opacity

# Custom Shapes
customShape.name: "CustomShape1"               # Custom shape name
customShape.style: "CustomGraphics"            # Custom shape style
customShape.geometry.type: "rectangle"         # Shape type
customShape.geometry.viewbox: "0 0 21600 21600" # View box
customShape.geometry.path: "M 0 0 L 21600 0 L 21600 21600 L 0 21600 Z" # Path
customShape.fill.type: "gradient"              # Fill type
customShape.fill.gradient.name: "Gradient1"    # Gradient name

# Image Properties
image.frame.name: "Image1"                     # Image frame name
image.href: "Pictures/image.jpg"               # Image path
image.link.type: "simple"                      # Link type
image.link.show: "embed"                       # Show type
image.link.actuate: "onLoad"                   # Load behavior
image.filter.name: ""                          # Filter name
```

---

## Footnote and Endnote Carriers

### 4. **FOOTNOTE AND ENDNOTE FORMATTING** (Critical Academic Features)

**Footnote Configuration**
```xml
<text:footnotes-configuration text:citation-style-name="{{footnote.citation.style}}" 
                               text:citation-body-style-name="{{footnote.citation.body.style}}" 
                               text:default-style-name="{{footnote.default.style}}" 
                               text:master-page-name="{{footnote.master.page}}" 
                               style:num-format="{{footnote.num.format}}" 
                               style:num-prefix="{{footnote.num.prefix}}" 
                               style:num-suffix="{{footnote.num.suffix}}" 
                               text:start-value="{{footnote.start.value}}" 
                               text:footnotes-position="{{footnote.position}}" 
                               text:start-numbering-at="{{footnote.start.numbering}}" 
                               text:increment-restart="{{footnote.increment.restart}}"/>

<!-- Footnote in Text -->
<text:note text:id="{{footnote.id}}" text:note-class="footnote">
  <text:note-citation text:style-name="{{footnote.citation.style}}">{{footnote.citation.text}}</text:note-citation>
  <text:note-body>
    <text:p text:style-name="{{footnote.body.style}}">{{footnote.body.text}}</text:p>
  </text:note-body>
</text:note>
```

**Endnote Configuration**
```xml
<text:endnotes-configuration text:citation-style-name="{{endnote.citation.style}}" 
                             text:citation-body-style-name="{{endnote.citation.body.style}}" 
                             text:default-style-name="{{endnote.default.style}}" 
                             text:master-page-name="{{endnote.master.page}}" 
                             style:num-format="{{endnote.num.format}}" 
                             style:num-prefix="{{endnote.num.prefix}}" 
                             style:num-suffix="{{endnote.num.suffix}}" 
                             text:start-value="{{endnote.start.value}}"
                             text:start-numbering-at="{{endnote.start.numbering}}"/>

<!-- Endnote in Text -->
<text:note text:id="{{endnote.id}}" text:note-class="endnote">
  <text:note-citation text:style-name="{{endnote.citation.style}}">{{endnote.citation.text}}</text:note-citation>
  <text:note-body>
    <text:p text:style-name="{{endnote.body.style}}">{{endnote.body.text}}</text:p>
  </text:note-body>
</text:note>
```

**Footnote and Endnote Styles**
```xml
<!-- Footnote Citation Style (superscript numbers) -->
<style:style style:name="{{footnote.citation.style}}" style:family="text">
  <style:text-properties style:text-position="{{footnote.citation.position}}" 
                         fo:font-size="{{footnote.citation.font.size}}" 
                         fo:color="{{footnote.citation.color}}"/>
</style:style>

<!-- Footnote Body Style -->
<style:style style:name="{{footnote.body.style}}" style:family="paragraph" 
             style:parent-style-name="Standard">
  <style:paragraph-properties fo:margin-left="{{footnote.body.margin.left}}" 
                              fo:text-indent="{{footnote.body.text.indent}}" 
                              fo:margin-top="{{footnote.body.margin.top}}" 
                              fo:margin-bottom="{{footnote.body.margin.bottom}}" 
                              style:line-height-at-least="{{footnote.body.line.height}}"/>
  <style:text-properties fo:font-size="{{footnote.body.font.size}}" 
                         fo:color="{{footnote.body.color}}"/>
</style:style>

<!-- Footnote Separator Style -->
<style:style style:name="{{footnote.separator.style}}" style:family="paragraph">
  <style:paragraph-properties fo:text-align="{{footnote.separator.align}}" 
                              fo:margin-top="{{footnote.separator.margin.top}}" 
                              fo:margin-bottom="{{footnote.separator.margin.bottom}}" 
                              fo:border-bottom="{{footnote.separator.border}}"/>
</style:style>
```

**Footnote and Endnote Variables:**
```yaml
# Footnote Configuration
footnote.citation.style: "Footnote_20_Symbol"          # Citation style
footnote.citation.body.style: "Footnote_20_Characters" # Citation body style
footnote.default.style: "Footnote"                     # Default footnote style
footnote.master.page: "Footnote"                       # Master page
footnote.num.format: "1"                               # Numbering format
footnote.num.prefix: ""                                # Number prefix
footnote.num.suffix: ""                                # Number suffix
footnote.start.value: "1"                              # Starting number
footnote.position: "page"                              # Position (page/document)
footnote.start.numbering: "page"                       # Restart numbering
footnote.increment.restart: "false"                    # Increment restart

# Footnote Appearance
footnote.citation.position: "super 58%"                # Superscript position
footnote.citation.font.size: "9pt"                     # Citation font size
footnote.citation.color: "#000000"                     # Citation color
footnote.body.margin.left: "0.2in"                     # Body left margin
footnote.body.text.indent: "-0.2in"                    # Body hanging indent
footnote.body.margin.top: "0in"                        # Body top margin
footnote.body.margin.bottom: "0.1in"                   # Body bottom margin
footnote.body.line.height: "120%"                      # Body line height
footnote.body.font.size: "9pt"                         # Body font size
footnote.body.color: "#000000"                         # Body color

# Footnote Separator
footnote.separator.align: "left"                       # Separator alignment
footnote.separator.margin.top: "0.1in"                 # Separator top margin
footnote.separator.margin.bottom: "0.05in"             # Separator bottom margin
footnote.separator.border: "0.5pt solid #000000"       # Separator border

# Endnote Configuration
endnote.citation.style: "Endnote_20_Symbol"            # Endnote citation style
endnote.citation.body.style: "Endnote_20_Characters"   # Endnote citation body
endnote.default.style: "Endnote"                       # Default endnote style
endnote.master.page: "Endnote"                         # Endnote master page
endnote.num.format: "i"                                # Roman numerals
endnote.num.prefix: "("                                # Parenthesis prefix
endnote.num.suffix: ")"                                # Parenthesis suffix
endnote.start.value: "1"                               # Starting value
endnote.start.numbering: "document"                    # Document numbering

# Endnote Appearance (similar to footnote but different positioning)
endnote.citation.position: "super 58%"                 # Superscript position
endnote.citation.font.size: "9pt"                      # Citation font size
endnote.citation.color: "#000000"                      # Citation color
endnote.body.font.size: "10pt"                         # Slightly larger body
endnote.body.color: "#000000"                          # Body color
```

---

## Index and Bibliography Carriers

### 5. **ALPHABETICAL INDEX AND BIBLIOGRAPHY** (Critical Reference Features)

**Alphabetical Index Structure**
```xml
<text:alphabetical-index text:style-name="{{index.style.name}}" text:name="{{index.name}}">
  <text:alphabetical-index-source text:main-entry-style-name="{{index.main.entry.style}}" 
                                  text:sort-algorithm="{{index.sort.algorithm}}" 
                                  text:language="{{index.language}}" 
                                  text:country="{{index.country}}" 
                                  text:alphabetical-separators="{{index.alphabetical.separators}}" 
                                  text:combine-entries="{{index.combine.entries}}" 
                                  text:combine-entries-with-dash="{{index.combine.with.dash}}" 
                                  text:combine-entries-with-pp="{{index.combine.with.pp}}" 
                                  text:use-keys-as-entries="{{index.use.keys.as.entries}}" 
                                  text:capitalize-entries="{{index.capitalize.entries}}" 
                                  text:comma-separated="{{index.comma.separated}}">
    
    <!-- Index Entry Template -->
    <text:index-entry-template text:outline-level="1" text:style-name="{{index.entry.level1.style}}">
      <text:index-entry-text/>
      <text:index-entry-tab-stop style:type="{{index.tab.stop.type}}" 
                                 style:leader-char="{{index.tab.leader.char}}"/>
      <text:index-entry-page-number/>
    </text:index-entry-template>
    
    <text:index-entry-template text:outline-level="2" text:style-name="{{index.entry.level2.style}}">
      <text:index-entry-text/>
      <text:index-entry-tab-stop style:type="{{index.tab.stop.type}}" 
                                 style:leader-char="{{index.tab.leader.char}}"/>
      <text:index-entry-page-number/>
    </text:index-entry-template>
  </text:alphabetical-index-source>
  
  <text:index-body>
    <text:index-title text:style-name="{{index.title.style}}" text:name="{{index.title.name}}">
      <text:p text:style-name="{{index.title.paragraph.style}}">{{index.title.text}}</text:p>
    </text:index-title>
    
    <!-- Generated index entries -->
    <text:p text:style-name="{{index.entry.level1.style}}">
      <text:span text:style-name="{{index.entry.text.style}}">{{index.entry.term}}</text:span>
      <text:tab/>
      <text:span text:style-name="{{index.page.number.style}}">{{index.page.number}}</text:span>
    </text:p>
  </text:index-body>
</text:alphabetical-index>
```

**Bibliography Structure**
```xml
<text:bibliography text:style-name="{{bibliography.style.name}}" text:name="{{bibliography.name}}">
  <text:bibliography-source>
    <!-- Bibliography Entry Template -->
    <text:index-entry-template text:bibliography-type="{{bibliography.type.article}}" 
                               text:style-name="{{bibliography.entry.article.style}}">
      <text:index-entry-bibliography text:bibliography-data-field="{{bibliography.field.author}}"/>
      <text:index-entry-span>, </text:index-entry-span>
      <text:index-entry-bibliography text:bibliography-data-field="{{bibliography.field.title}}"/>
      <text:index-entry-span>, </text:index-entry-span>
      <text:index-entry-bibliography text:bibliography-data-field="{{bibliography.field.journal}}"/>
      <text:index-entry-span>, </text:index-entry-span>
      <text:index-entry-bibliography text:bibliography-data-field="{{bibliography.field.year}}"/>
    </text:index-entry-template>
    
    <text:index-entry-template text:bibliography-type="{{bibliography.type.book}}" 
                               text:style-name="{{bibliography.entry.book.style}}">
      <text:index-entry-bibliography text:bibliography-data-field="{{bibliography.field.author}}"/>
      <text:index-entry-span>, </text:index-entry-span>
      <text:index-entry-bibliography text:bibliography-data-field="{{bibliography.field.title}}"/>
      <text:index-entry-span>, </text:index-entry-span>
      <text:index-entry-bibliography text:bibliography-data-field="{{bibliography.field.publisher}}"/>
      <text:index-entry-span>, </text:index-entry-span>
      <text:index-entry-bibliography text:bibliography-data-field="{{bibliography.field.year}}"/>
    </text:index-entry-template>
  </text:bibliography-source>
  
  <text:index-body>
    <text:index-title text:style-name="{{bibliography.title.style}}" text:name="{{bibliography.title.name}}">
      <text:p text:style-name="{{bibliography.title.paragraph.style}}">{{bibliography.title.text}}</text:p>
    </text:index-title>
  </text:index-body>
</text:bibliography>
```

**Index and Bibliography Variables:**
```yaml
# Alphabetical Index
index.style.name: "Alphabetical_20_Index"      # Index style name
index.name: "Alphabetical_20_Index1"           # Index identifier
index.main.entry.style: "Index"                # Main entry style
index.sort.algorithm: "alphanumeric"           # Sort algorithm
index.language: "en"                           # Language
index.country: "US"                            # Country
index.alphabetical.separators: "true"          # Use A, B, C separators
index.combine.entries: "true"                  # Combine same entries
index.combine.with.dash: "false"               # Use dash for ranges
index.combine.with.pp: "true"                  # Use "pp." for multiple pages
index.capitalize.entries: "false"              # Capitalize entries
index.comma.separated: "false"                 # Comma separated entries

# Index Formatting
index.entry.level1.style: "Index_20_1"         # Level 1 entry style
index.entry.level2.style: "Index_20_2"         # Level 2 entry style
index.tab.stop.type: "right"                   # Tab stop type
index.tab.leader.char: "."                     # Leader character
index.title.style: "Index_20_Heading"          # Title style
index.title.paragraph.style: "Index_20_Heading" # Title paragraph style
index.title.text: "Index"                      # Title text

# Bibliography
bibliography.style.name: "Bibliography"        # Bibliography style
bibliography.name: "Bibliography1"             # Bibliography identifier
bibliography.type.article: "article"           # Article type
bibliography.type.book: "book"                 # Book type
bibliography.entry.article.style: "Bibliography_20_1" # Article entry style
bibliography.entry.book.style: "Bibliography_20_1"    # Book entry style

# Bibliography Fields
bibliography.field.author: "author"            # Author field
bibliography.field.title: "title"              # Title field
bibliography.field.journal: "journal"          # Journal field
bibliography.field.publisher: "publisher"      # Publisher field
bibliography.field.year: "year"                # Year field
bibliography.title.text: "Bibliography"        # Bibliography title
```

---

## Advanced Table Carriers

### 6. **COMPLEX TABLE FORMATTING** (Critical Data Presentation)

**Table with Advanced Properties**
```xml
<table:table table:name="{{table.name}}" table:style-name="{{table.style.name}}">
  
  <!-- Table Columns Definition -->
  <table:table-column table:style-name="{{table.column1.style}}" 
                      table:number-columns-repeated="{{table.column1.repeated}}" 
                      table:default-cell-style-name="{{table.column1.cell.style}}"/>
  <table:table-column table:style-name="{{table.column2.style}}" 
                      table:number-columns-repeated="{{table.column2.repeated}}" 
                      table:default-cell-style-name="{{table.column2.cell.style}}"/>
  
  <!-- Table Header Row -->
  <table:table-header-rows>
    <table:table-row table:style-name="{{table.header.row.style}}">
      <table:table-cell table:style-name="{{table.header.cell.style}}" 
                        office:value-type="{{table.header.value.type}}">
        <text:p text:style-name="{{table.header.text.style}}">{{table.header.cell1.text}}</text:p>
      </table:table-cell>
      <table:table-cell table:style-name="{{table.header.cell.style}}" 
                        office:value-type="{{table.header.value.type}}">
        <text:p text:style-name="{{table.header.text.style}}">{{table.header.cell2.text}}</text:p>
      </table:table-cell>
    </table:table-row>
  </table:table-header-rows>
  
  <!-- Table Body Rows -->
  <table:table-row table:style-name="{{table.body.row.style}}">
    <table:table-cell table:style-name="{{table.body.cell.style}}" 
                      office:value-type="{{table.body.value.type}}" 
                      table:number-columns-spanned="{{table.cell.colspan}}" 
                      table:number-rows-spanned="{{table.cell.rowspan}}">
      <text:p text:style-name="{{table.body.text.style}}">{{table.body.cell.text}}</text:p>
    </table:table-cell>
    <table:covered-table-cell/> <!-- For spanned cells -->
  </table:table-row>
  
  <!-- Alternating Row Style -->
  <table:table-row table:style-name="{{table.alternating.row.style}}">
    <table:table-cell table:style-name="{{table.alternating.cell.style}}" 
                      office:value-type="{{table.alternating.value.type}}">
      <text:p text:style-name="{{table.alternating.text.style}}">{{table.alternating.cell.text}}</text:p>
    </table:table-cell>
  </table:table-row>
</table:table>
```

**Advanced Table Style Definitions**
```xml
<!-- Table Container Style -->
<style:style style:name="{{table.style.name}}" style:family="table">
  <style:table-properties style:width="{{table.width}}" 
                          table:align="{{table.align}}" 
                          fo:margin-left="{{table.margin.left}}" 
                          fo:margin-right="{{table.margin.right}}" 
                          fo:margin-top="{{table.margin.top}}" 
                          fo:margin-bottom="{{table.margin.bottom}}" 
                          fo:background-color="{{table.background.color}}" 
                          fo:keep-together="{{table.keep.together}}" 
                          fo:keep-with-next="{{table.keep.with.next}}" 
                          style:page-number="{{table.page.number}}" 
                          fo:break-before="{{table.break.before}}" 
                          fo:break-after="{{table.break.after}}" 
                          table:border-model="{{table.border.model}}" 
                          style:shadow="{{table.shadow}}"/>
</style:style>

<!-- Table Column Styles -->
<style:style style:name="{{table.column1.style}}" style:family="table-column">
  <style:table-column-properties style:column-width="{{table.column1.width}}" 
                                 style:rel-column-width="{{table.column1.relative.width}}" 
                                 fo:break-before="{{table.column1.break.before}}" 
                                 fo:break-after="{{table.column1.break.after}}"/>
</style:style>

<!-- Table Row Styles -->
<style:style style:name="{{table.header.row.style}}" style:family="table-row">
  <style:table-row-properties style:min-row-height="{{table.header.row.min.height}}" 
                              style:row-height="{{table.header.row.height}}" 
                              fo:keep-together="{{table.header.row.keep.together}}" 
                              fo:break-before="{{table.header.row.break.before}}" 
                              fo:break-after="{{table.header.row.break.after}}" 
                              style:use-optimal-row-height="{{table.header.row.optimal.height}}"/>
</style:style>

<style:style style:name="{{table.body.row.style}}" style:family="table-row">
  <style:table-row-properties style:min-row-height="{{table.body.row.min.height}}" 
                              style:row-height="{{table.body.row.height}}" 
                              fo:background-color="{{table.body.row.background}}" 
                              style:use-optimal-row-height="{{table.body.row.optimal.height}}"/>
</style:style>

<!-- Table Cell Styles -->
<style:style style:name="{{table.header.cell.style}}" style:family="table-cell">
  <style:table-cell-properties fo:padding="{{table.header.cell.padding}}" 
                               fo:border-left="{{table.header.cell.border.left}}" 
                               fo:border-right="{{table.header.cell.border.right}}" 
                               fo:border-top="{{table.header.cell.border.top}}" 
                               fo:border-bottom="{{table.header.cell.border.bottom}}" 
                               fo:background-color="{{table.header.cell.background}}" 
                               style:vertical-align="{{table.header.cell.vertical.align}}" 
                               style:text-align-source="{{table.header.cell.text.align.source}}" 
                               style:direction="{{table.header.cell.direction}}" 
                               style:rotation-angle="{{table.header.cell.rotation.angle}}" 
                               style:rotation-align="{{table.header.cell.rotation.align}}" 
                               style:shrink-to-fit="{{table.header.cell.shrink.to.fit}}" 
                               style:wrap-option="{{table.header.cell.wrap.option}}"/>
</style:style>
```

**Advanced Table Variables:**
```yaml
# Table Structure
table.name: "Table1"                            # Table identifier
table.style.name: "Table1"                     # Table style name
table.width: "100%"                            # Table width
table.align: "margins"                         # Table alignment
table.margin.left: "0in"                       # Left margin
table.margin.right: "0in"                      # Right margin
table.margin.top: "0.08in"                     # Top margin
table.margin.bottom: "0.08in"                  # Bottom margin
table.background.color: "transparent"          # Table background
table.keep.together: "auto"                    # Keep together
table.border.model: "collapsing"               # Border model
table.shadow: "none"                           # Table shadow

# Column Properties
table.column1.style: "Table1.A"                # Column 1 style
table.column1.width: "2in"                     # Column 1 width
table.column1.relative.width: "1*"             # Relative width
table.column1.repeated: "1"                    # Column repetition
table.column1.cell.style: "Table1.A1"          # Default cell style

table.column2.style: "Table1.B"                # Column 2 style
table.column2.width: "3in"                     # Column 2 width
table.column2.repeated: "1"                    # Column repetition
table.column2.cell.style: "Table1.B1"          # Default cell style

# Header Row Properties
table.header.row.style: "Table1.1"             # Header row style
table.header.row.min.height: "0.25in"          # Minimum height
table.header.row.height: "0.35in"              # Fixed height
table.header.row.optimal.height: "true"        # Use optimal height
table.header.row.keep.together: "always"       # Keep together

# Header Cell Properties
table.header.cell.style: "Table1.A1"           # Header cell style
table.header.value.type: "string"              # Value type
table.header.cell.padding: "0.08in"            # Cell padding
table.header.cell.border.left: "0.5pt solid #000000"    # Left border
table.header.cell.border.right: "0.5pt solid #000000"   # Right border
table.header.cell.border.top: "0.5pt solid #000000"     # Top border
table.header.cell.border.bottom: "1pt solid #000000"    # Bottom border
table.header.cell.background: "#E0E0E0"         # Header background
table.header.cell.vertical.align: "middle"     # Vertical alignment
table.header.text.style: "Table_20_Heading"    # Header text style
table.header.cell1.text: "Column 1"            # Header 1 text
table.header.cell2.text: "Column 2"            # Header 2 text

# Body Row Properties
table.body.row.style: "Table1.2"               # Body row style
table.body.row.min.height: "0.2in"             # Minimum height
table.body.row.background: "transparent"       # Row background
table.body.row.optimal.height: "true"          # Use optimal height

# Body Cell Properties
table.body.cell.style: "Table1.A2"             # Body cell style
table.body.value.type: "string"                # Value type
table.body.text.style: "Table_20_Contents"     # Body text style
table.cell.colspan: "1"                        # Column span
table.cell.rowspan: "1"                        # Row span

# Alternating Row Properties
table.alternating.row.style: "Table1.3"        # Alternating row style
table.alternating.cell.style: "Table1.A3"      # Alternating cell style
table.alternating.value.type: "string"         # Value type
table.alternating.text.style: "Table_20_Contents" # Alternating text style
```

---

## Forms and Field Carriers

### 7. **FORM CONTROLS AND FIELDS** (Critical Interactive Elements)

**Form Structure and Controls**
```xml
<form:form form:name="{{form.name}}" form:method="{{form.method}}" form:enctype="{{form.enctype}}">
  
  <!-- Text Input Field -->
  <draw:frame draw:name="{{form.text.field.name}}" text:anchor-type="{{form.text.anchor.type}}" 
              svg:x="{{form.text.position.x}}" svg:y="{{form.text.position.y}}" 
              svg:width="{{form.text.width}}" svg:height="{{form.text.height}}">
    <form:text form:name="{{form.text.control.name}}" 
               form:control-implementation="{{form.text.implementation}}" 
               form:id="{{form.text.id}}" 
               form:value="{{form.text.default.value}}" 
               form:current-value="{{form.text.current.value}}" 
               form:max-length="{{form.text.max.length}}" 
               form:readonly="{{form.text.readonly}}" 
               form:disabled="{{form.text.disabled}}" 
               form:printable="{{form.text.printable}}" 
               form:tab-index="{{form.text.tab.index}}"/>
  </draw:frame>
  
  <!-- Checkbox Control -->
  <draw:frame draw:name="{{form.checkbox.field.name}}" text:anchor-type="{{form.checkbox.anchor.type}}" 
              svg:x="{{form.checkbox.position.x}}" svg:y="{{form.checkbox.position.y}}" 
              svg:width="{{form.checkbox.width}}" svg:height="{{form.checkbox.height}}">
    <form:checkbox form:name="{{form.checkbox.control.name}}" 
                   form:control-implementation="{{form.checkbox.implementation}}" 
                   form:id="{{form.checkbox.id}}" 
                   form:current-state="{{form.checkbox.current.state}}" 
                   form:is-tristate="{{form.checkbox.tristate}}" 
                   form:value="{{form.checkbox.value}}" 
                   form:label="{{form.checkbox.label}}" 
                   form:visual-effect="{{form.checkbox.visual.effect}}" 
                   form:disabled="{{form.checkbox.disabled}}" 
                   form:printable="{{form.checkbox.printable}}" 
                   form:tab-index="{{form.checkbox.tab.index}}"/>
  </draw:frame>
  
  <!-- Radio Button Group -->
  <draw:frame draw:name="{{form.radio.field.name}}" text:anchor-type="{{form.radio.anchor.type}}" 
              svg:x="{{form.radio.position.x}}" svg:y="{{form.radio.position.y}}" 
              svg:width="{{form.radio.width}}" svg:height="{{form.radio.height}}">
    <form:radio form:name="{{form.radio.control.name}}" 
                form:control-implementation="{{form.radio.implementation}}" 
                form:id="{{form.radio.id}}" 
                form:current-selected="{{form.radio.current.selected}}" 
                form:selected="{{form.radio.selected}}" 
                form:value="{{form.radio.value}}" 
                form:label="{{form.radio.label}}" 
                form:visual-effect="{{form.radio.visual.effect}}" 
                form:disabled="{{form.radio.disabled}}" 
                form:printable="{{form.radio.printable}}" 
                form:tab-index="{{form.radio.tab.index}}"/>
  </draw:frame>
  
  <!-- Dropdown List -->
  <draw:frame draw:name="{{form.listbox.field.name}}" text:anchor-type="{{form.listbox.anchor.type}}" 
              svg:x="{{form.listbox.position.x}}" svg:y="{{form.listbox.position.y}}" 
              svg:width="{{form.listbox.width}}" svg:height="{{form.listbox.height}}">
    <form:listbox form:name="{{form.listbox.control.name}}" 
                  form:control-implementation="{{form.listbox.implementation}}" 
                  form:id="{{form.listbox.id}}" 
                  form:bound-column="{{form.listbox.bound.column}}" 
                  form:list-source="{{form.listbox.list.source}}" 
                  form:list-source-type="{{form.listbox.list.source.type}}" 
                  form:multiple="{{form.listbox.multiple}}" 
                  form:dropdown="{{form.listbox.dropdown}}" 
                  form:size="{{form.listbox.size}}" 
                  form:disabled="{{form.listbox.disabled}}" 
                  form:printable="{{form.listbox.printable}}" 
                  form:tab-index="{{form.listbox.tab.index}}">
      
      <!-- List Options -->
      <form:option form:current-selected="{{form.option1.selected}}" 
                   form:selected="{{form.option1.selected}}" 
                   form:value="{{form.option1.value}}" 
                   form:label="{{form.option1.label}}"/>
      <form:option form:current-selected="{{form.option2.selected}}" 
                   form:selected="{{form.option2.selected}}" 
                   form:value="{{form.option2.value}}" 
                   form:label="{{form.option2.label}}"/>
    </form:listbox>
  </draw:frame>
  
  <!-- Submit Button -->
  <draw:frame draw:name="{{form.button.field.name}}" text:anchor-type="{{form.button.anchor.type}}" 
              svg:x="{{form.button.position.x}}" svg:y="{{form.button.position.y}}" 
              svg:width="{{form.button.width}}" svg:height="{{form.button.height}}">
    <form:button form:name="{{form.button.control.name}}" 
                 form:control-implementation="{{form.button.implementation}}" 
                 form:id="{{form.button.id}}" 
                 form:button-type="{{form.button.type}}" 
                 form:label="{{form.button.label}}" 
                 form:image-data="{{form.button.image.data}}" 
                 form:disabled="{{form.button.disabled}}" 
                 form:printable="{{form.button.printable}}" 
                 form:tab-index="{{form.button.tab.index}}"/>
  </draw:frame>
</form:form>
```

**Forms and Field Variables:**
```yaml
# Form Container
form.name: "Form1"                              # Form identifier
form.method: "post"                             # Form method
form.enctype: "application/x-www-form-urlencoded" # Encoding type

# Text Input Field
form.text.field.name: "TextField1"             # Text field frame name
form.text.anchor.type: "paragraph"             # Anchor type
form.text.position.x: "1in"                    # X position
form.text.position.y: "1in"                    # Y position
form.text.width: "2in"                         # Field width
form.text.height: "0.25in"                     # Field height
form.text.control.name: "TextBox1"             # Control name
form.text.implementation: "ooo:com.sun.star.form.component.TextField" # Implementation
form.text.id: "control1"                       # Control ID
form.text.default.value: ""                    # Default value
form.text.current.value: ""                    # Current value
form.text.max.length: "50"                     # Maximum length
form.text.readonly: "false"                    # Read-only status
form.text.disabled: "false"                    # Disabled status
form.text.printable: "true"                    # Printable status
form.text.tab.index: "1"                       # Tab index

# Checkbox Control
form.checkbox.field.name: "CheckboxField1"     # Checkbox frame name
form.checkbox.anchor.type: "paragraph"         # Anchor type
form.checkbox.position.x: "1in"                # X position
form.checkbox.position.y: "1.5in"              # Y position
form.checkbox.width: "0.25in"                  # Checkbox width
form.checkbox.height: "0.25in"                 # Checkbox height
form.checkbox.control.name: "Checkbox1"        # Control name
form.checkbox.implementation: "ooo:com.sun.star.form.component.CheckBox" # Implementation
form.checkbox.id: "control2"                   # Control ID
form.checkbox.current.state: "unchecked"       # Current state
form.checkbox.tristate: "false"                # Tristate checkbox
form.checkbox.value: "true"                    # Checkbox value
form.checkbox.label: "Check this option"       # Checkbox label
form.checkbox.visual.effect: "look3d"          # Visual effect
form.checkbox.disabled: "false"                # Disabled status
form.checkbox.printable: "true"                # Printable status
form.checkbox.tab.index: "2"                   # Tab index

# Radio Button
form.radio.field.name: "RadioField1"           # Radio frame name
form.radio.anchor.type: "paragraph"            # Anchor type
form.radio.position.x: "1in"                   # X position
form.radio.position.y: "2in"                   # Y position
form.radio.width: "0.25in"                     # Radio width
form.radio.height: "0.25in"                    # Radio height
form.radio.control.name: "Radio1"              # Control name
form.radio.implementation: "ooo:com.sun.star.form.component.RadioButton" # Implementation
form.radio.id: "control3"                      # Control ID
form.radio.current.selected: "false"           # Current selected
form.radio.selected: "false"                   # Selected status
form.radio.value: "option1"                    # Radio value
form.radio.label: "Option 1"                   # Radio label
form.radio.visual.effect: "look3d"             # Visual effect
form.radio.disabled: "false"                   # Disabled status
form.radio.printable: "true"                   # Printable status
form.radio.tab.index: "3"                      # Tab index

# Dropdown List
form.listbox.field.name: "ListboxField1"       # Listbox frame name
form.listbox.anchor.type: "paragraph"          # Anchor type
form.listbox.position.x: "1in"                 # X position
form.listbox.position.y: "2.5in"               # Y position
form.listbox.width: "2in"                      # Listbox width
form.listbox.height: "0.25in"                  # Listbox height
form.listbox.control.name: "Listbox1"          # Control name
form.listbox.implementation: "ooo:com.sun.star.form.component.ListBox" # Implementation
form.listbox.id: "control4"                    # Control ID
form.listbox.bound.column: "1"                 # Bound column
form.listbox.list.source: ""                   # List source
form.listbox.list.source.type: "valuelist"     # Source type
form.listbox.multiple: "false"                 # Multiple selection
form.listbox.dropdown: "true"                  # Dropdown style
form.listbox.size: "1"                         # List size
form.listbox.disabled: "false"                 # Disabled status
form.listbox.printable: "true"                 # Printable status
form.listbox.tab.index: "4"                    # Tab index

# List Options
form.option1.selected: "false"                 # Option 1 selected
form.option1.value: "value1"                   # Option 1 value
form.option1.label: "Option 1"                 # Option 1 label
form.option2.selected: "true"                  # Option 2 selected
form.option2.value: "value2"                   # Option 2 value
form.option2.label: "Option 2"                 # Option 2 label

# Submit Button
form.button.field.name: "ButtonField1"         # Button frame name
form.button.anchor.type: "paragraph"           # Anchor type
form.button.position.x: "1in"                  # X position
form.button.position.y: "3in"                  # Y position
form.button.width: "1in"                       # Button width
form.button.height: "0.35in"                   # Button height
form.button.control.name: "Button1"            # Control name
form.button.implementation: "ooo:com.sun.star.form.component.CommandButton" # Implementation
form.button.id: "control5"                     # Control ID
form.button.type: "submit"                     # Button type
form.button.label: "Submit"                    # Button label
form.button.image.data: ""                     # Image data
form.button.disabled: "false"                  # Disabled status
form.button.printable: "true"                  # Printable status
form.button.tab.index: "5"                     # Tab index
```

---

## Mathematical Formula Carriers

### 8. **MATHEMATICAL FORMULAS AND EQUATIONS** (Critical Scientific Documents)

**Math Object Structure**
```xml
<draw:frame draw:name="{{math.frame.name}}" text:anchor-type="{{math.anchor.type}}" 
            svg:x="{{math.position.x}}" svg:y="{{math.position.y}}" 
            svg:width="{{math.width}}" svg:height="{{math.height}}" 
            draw:z-index="{{math.z.index}}">
  
  <draw:object xlink:href="{{math.object.href}}" 
               xlink:type="{{math.object.type}}" 
               xlink:show="{{math.object.show}}" 
               xlink:actuate="{{math.object.actuate}}"/>
  
  <!-- Math Formula Content -->
  <math:math xmlns:math="http://www.w3.org/1998/Math/MathML" 
             math:display="{{math.display.mode}}">
    
    <!-- Fraction Example -->
    <math:mfrac>
      <math:mrow>
        <math:mi>{{math.fraction.numerator.variable}}</math:mi>
        <math:mo>{{math.fraction.numerator.operator}}</math:mo>
        <math:mn>{{math.fraction.numerator.number}}</math:mn>
      </math:mrow>
      <math:mrow>
        <math:mi>{{math.fraction.denominator.variable}}</math:mi>
        <math:mo>{{math.fraction.denominator.operator}}</math:mo>
        <math:mn>{{math.fraction.denominator.number}}</math:mn>
      </math:mrow>
    </math:mfrac>
    
    <!-- Square Root Example -->
    <math:msqrt>
      <math:mrow>
        <math:msup>
          <math:mi>{{math.sqrt.base.variable}}</math:mi>
          <math:mn>{{math.sqrt.base.exponent}}</math:mn>
        </math:msup>
        <math:mo>{{math.sqrt.operator}}</math:mo>
        <math:msup>
          <math:mi>{{math.sqrt.second.variable}}</math:mi>
          <math:mn>{{math.sqrt.second.exponent}}</math:mn>
        </math:msup>
      </math:mrow>
    </math:msqrt>
    
    <!-- Integral Example -->
    <math:msubsup>
      <math:mo>∫</math:mo>
      <math:mi>{{math.integral.lower.limit}}</math:mi>
      <math:mi>{{math.integral.upper.limit}}</math:mi>
    </math:msubsup>
    <math:mi>{{math.integral.function}}</math:mi>
    <math:mo>d</math:mo>
    <math:mi>{{math.integral.variable}}</math:mi>
    
    <!-- Matrix Example -->
    <math:mfenced open="{{math.matrix.open.bracket}}" close="{{math.matrix.close.bracket}}">
      <math:mtable>
        <math:mtr>
          <math:mtd><math:mi>{{math.matrix.element.11}}</math:mi></math:mtd>
          <math:mtd><math:mi>{{math.matrix.element.12}}</math:mi></math:mtd>
        </math:mtr>
        <math:mtr>
          <math:mtd><math:mi>{{math.matrix.element.21}}</math:mi></math:mtd>
          <math:mtd><math:mi>{{math.matrix.element.22}}</math:mi></math:mtd>
        </math:mtr>
      </math:mtable>
    </math:mfenced>
  </math:math>
</draw:frame>
```

**Mathematical Formula Variables:**
```yaml
# Math Object Properties
math.frame.name: "Object1"                     # Math frame name
math.anchor.type: "paragraph"                  # Anchor type
math.position.x: "1in"                         # X position
math.position.y: "1in"                         # Y position
math.width: "3in"                              # Math object width
math.height: "1in"                             # Math object height
math.z.index: "0"                              # Z-order
math.object.href: "./Object 1/content.xml"     # Math object reference
math.object.type: "simple"                     # Link type
math.object.show: "embed"                      # Display mode
math.object.actuate: "onLoad"                  # Load behavior
math.display.mode: "block"                     # Display mode (block/inline)

# Fraction Components
math.fraction.numerator.variable: "a"          # Numerator variable
math.fraction.numerator.operator: "+"          # Numerator operator
math.fraction.numerator.number: "1"            # Numerator number
math.fraction.denominator.variable: "b"        # Denominator variable
math.fraction.denominator.operator: "-"        # Denominator operator
math.fraction.denominator.number: "2"          # Denominator number

# Square Root Components
math.sqrt.base.variable: "x"                   # Base variable
math.sqrt.base.exponent: "2"                   # Base exponent
math.sqrt.operator: "+"                        # Operator
math.sqrt.second.variable: "y"                 # Second variable
math.sqrt.second.exponent: "2"                 # Second exponent

# Integral Components
math.integral.lower.limit: "a"                 # Lower integration limit
math.integral.upper.limit: "b"                 # Upper integration limit
math.integral.function: "f(x)"                 # Function to integrate
math.integral.variable: "x"                    # Integration variable

# Matrix Components
math.matrix.open.bracket: "["                  # Opening bracket
math.matrix.close.bracket: "]"                 # Closing bracket
math.matrix.element.11: "a"                    # Matrix element (1,1)
math.matrix.element.12: "b"                    # Matrix element (1,2)
math.matrix.element.21: "c"                    # Matrix element (2,1)
math.matrix.element.22: "d"                    # Matrix element (2,2)
```

---

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Research ODF Table of Contents (TOC) carriers", "status": "completed", "activeForm": "Researching ODF Table of Contents (TOC) carriers"}, {"content": "Research ODF numbering and list carriers", "status": "completed", "activeForm": "Researching ODF numbering and list carriers"}, {"content": "Research ODF shape and drawing carriers", "status": "completed", "activeForm": "Researching ODF shape and drawing carriers"}, {"content": "Research ODF footnotes and endnotes carriers", "status": "completed", "activeForm": "Researching ODF footnotes and endnotes carriers"}, {"content": "Update ODF documentation with missing carriers", "status": "completed", "activeForm": "Updating ODF documentation with missing carriers"}]