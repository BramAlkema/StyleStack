# ODF Hidden Properties and Advanced Control Catalog

## Overview
This catalog documents **hidden properties and advanced XML attributes** in OpenDocument Format (ODF/ISO 26300) that provide precise design control beyond standard LibreOffice/OpenOffice interfaces. These properties enable StyleStack to achieve the same "impossible level of control" over ODF documents as with OOXML.

## Business Value
- **Complete Brand Takeover**: Control every visual aspect of ODF documents
- **Cross-Platform Consistency**: Match OOXML design token precision in LibreOffice ecosystem
- **Enterprise Compatibility**: Full control over documents in LibreOffice-using organizations
- **Competitive Advantage**: Access to properties unavailable through standard APIs

## Hidden Properties by Category

### 1. **Advanced Typography Control (fo: and style: namespaces)**

#### Micro-Typography Properties
```xml
<!-- Character-level micro-adjustments -->
<style:text-properties
    fo:letter-spacing="{{typography.character_spacing.precise|normal}}"
    fo:word-spacing="{{typography.word_spacing.precise|normal}}"
    style:letter-kerning="{{typography.kerning.enable|true}}"
    style:text-emphasize="{{typography.emphasis.style|none}}"
    style:text-combine="{{typography.text_combine|none}}"
    style:text-combine-start-char="{{typography.combine.start_char|}}"
    style:text-combine-end-char="{{typography.combine.end_char|}}"
    style:text-line-through-type="{{typography.strikethrough.type|none}}"
    style:text-line-through-style="{{typography.strikethrough.style|solid}}"
    style:text-line-through-width="{{typography.strikethrough.width|auto}}"
    style:text-line-through-color="{{typography.strikethrough.color|font-color}}"
    style:text-underline-type="{{typography.underline.type|none}}"
    style:text-underline-style="{{typography.underline.style|solid}}"
    style:text-underline-width="{{typography.underline.width|auto}}"
    style:text-underline-color="{{typography.underline.color|font-color}}"
    style:text-position="{{typography.position.vertical|normal}} {{typography.position.scale|100%}}"
    style:font-charset="{{typography.font.charset|76}}"
    style:font-pitch="{{typography.font.pitch|variable}}"
    style:font-relief="{{typography.font.relief|none}}"
    fo:text-transform="{{typography.text_transform|none}}"
    fo:font-variant="{{typography.font_variant|normal}}"
    style:text-rotation-angle="{{typography.rotation_angle|0}}"
    style:text-rotation-scale="{{typography.rotation_scale|line-height}}"
    style:text-scale="{{typography.text_scale|100%}}"
    loext:char-shading-value="{{typography.character_shading.value|transparent}}"
    css3t:text-decoration-skip="{{typography.decoration_skip|objects}}"
/>
```

#### Advanced Language and Hyphenation
```xml
<!-- Precise language control -->
<style:text-properties
    fo:language="{{localization.language.primary|en}}"
    fo:country="{{localization.country.primary|US}}"
    style:language-asian="{{localization.language.asian|zh}}"
    style:country-asian="{{localization.country.asian|CN}}"
    style:language-complex="{{localization.language.complex|hi}}"
    style:country-complex="{{localization.country.complex|IN}}"
    style:script-type="{{localization.script.type|latin}}"
    fo:hyphenate="{{typography.hyphenation.enable|false}}"
    fo:hyphenation-keep="{{typography.hyphenation.keep|auto}}"
    fo:hyphenation-remain-char-count="{{typography.hyphenation.remain_chars|2}}"
    fo:hyphenation-push-char-count="{{typography.hyphenation.push_chars|2}}"
    loext:hyphenation-no-caps="{{typography.hyphenation.no_caps|false}}"
    loext:hyphenation-no-last-word="{{typography.hyphenation.no_last_word|false}}"
    loext:hyphenation-word-char-count="{{typography.hyphenation.word_char_count|5}}"
    loext:hyphenation-zone="{{typography.hyphenation.zone|no-limit}}"
/>
```

### 2. **Advanced Paragraph Control**

#### Precision Line Spacing and Alignment
```xml
<!-- Micro-adjustments to paragraph layout -->
<style:paragraph-properties
    fo:line-height="{{layout.line_height.precise|normal}}"
    style:line-height-at-least="{{layout.line_height.minimum|0cm}}"
    style:line-spacing="{{layout.line_spacing.precise|0cm}}"
    fo:text-align="{{layout.alignment.horizontal|start}}"
    fo:text-align-last="{{layout.alignment.last_line|start}}"
    style:justify-single-word="{{layout.alignment.justify_single|false}}"
    style:text-autospace="{{layout.text_autospace|none}}"
    style:punctuation-wrap="{{layout.punctuation_wrap|simple}}"
    style:line-break="{{layout.line_break|normal}}"
    style:font-independent-line-spacing="{{layout.font_independent_spacing|false}}"
    style:vertical-align="{{layout.vertical_align|auto}}"
    text:number-lines="{{layout.line_numbering.enable|false}}"
    text:line-number="{{layout.line_numbering.start|0}}"
    fo:background-color="{{layout.paragraph.bg_color|transparent}}"
    style:background-transparency="{{layout.paragraph.bg_transparency|0%}}"
    fo:padding="{{layout.paragraph.padding|0cm}}"
    fo:padding-top="{{layout.paragraph.padding.top|0cm}}"
    fo:padding-bottom="{{layout.paragraph.padding.bottom|0cm}}"
    fo:padding-left="{{layout.paragraph.padding.left|0cm}}"
    fo:padding-right="{{layout.paragraph.padding.right|0cm}}"
    fo:border="{{layout.paragraph.border|none}}"
    fo:border-top="{{layout.paragraph.border.top|none}}"
    fo:border-bottom="{{layout.paragraph.border.bottom|none}}"
    fo:border-left="{{layout.paragraph.border.left|none}}"
    fo:border-right="{{layout.paragraph.border.right|none}}"
    style:border-line-width="{{layout.paragraph.border.line_width|0.05pt}}"
    style:border-line-width-top="{{layout.paragraph.border.line_width.top|0.05pt}}"
    style:shadow="{{layout.paragraph.shadow|none}}"
/>
```

#### Advanced Indentation and Tabs
```xml
<!-- Precise indentation control -->
<style:paragraph-properties
    fo:margin-left="{{layout.indentation.left|0cm}}"
    fo:margin-right="{{layout.indentation.right|0cm}}"
    fo:text-indent="{{layout.indentation.first_line|0cm}}"
    style:auto-text-indent="{{layout.indentation.auto|false}}"
    fo:margin-top="{{layout.spacing.before|0cm}}"
    fo:margin-bottom="{{layout.spacing.after|0cm}}"
    loext:contextual-spacing="{{layout.spacing.contextual|false}}"
    fo:keep-together="{{layout.keep.together|auto}}"
    fo:keep-with-next="{{layout.keep.with_next|auto}}"
    style:break-before="{{layout.break.before|auto}}"
    style:break-after="{{layout.break.after|auto}}"
    fo:break-before="{{layout.page_break.before|auto}}"
    fo:break-after="{{layout.page_break.after|auto}}"
    style:writing-mode="{{layout.writing_mode|lr-tb}}"
    style:writing-mode-automatic="{{layout.writing_mode.auto|false}}"
    style:snap-to-layout-grid="{{layout.grid.snap|true}}"
    style:register-true="{{layout.register|false}}"
/>

<!-- Advanced tab stops -->
<style:tab-stops>
    <style:tab-stop style:position="{{tabs.position.1|1.25cm}}"
                   style:type="{{tabs.type.1|left}}"
                   style:leader-style="{{tabs.leader.style.1|none}}"
                   style:leader-text="{{tabs.leader.text.1| }}"
                   style:leader-color="{{tabs.leader.color.1|#000000}}"
                   style:leader-width="{{tabs.leader.width.1|auto}}"
                   style:leader-type="{{tabs.leader.type.1|none}}"
    />
</style:tab-stops>
```

### 3. **Table Advanced Properties**

#### Hidden Table Cell Control
```xml
<!-- Advanced cell properties -->
<style:table-cell-properties
    fo:background-color="{{brand.colors.cell.background|transparent}}"
    fo:border="{{borders.cell.default|none}}"
    fo:border-top="{{borders.cell.top|none}}"
    fo:border-bottom="{{borders.cell.bottom|none}}"
    fo:border-left="{{borders.cell.left|none}}"
    fo:border-right="{{borders.cell.right|none}}"
    style:border-line-width="{{borders.cell.line_width|0.05pt}}"
    style:border-line-width-top="{{borders.cell.line_width.top|0.05pt}}"
    style:border-line-width-bottom="{{borders.cell.line_width.bottom|0.05pt}}"
    style:border-line-width-left="{{borders.cell.line_width.left|0.05pt}}"
    style:border-line-width-right="{{borders.cell.line_width.right|0.05pt}}"
    fo:padding="{{spacing.cell.padding|0cm}}"
    fo:padding-top="{{spacing.cell.padding.top|0cm}}"
    fo:padding-bottom="{{spacing.cell.padding.bottom|0cm}}"
    fo:padding-left="{{spacing.cell.padding.left|0cm}}"
    fo:padding-right="{{spacing.cell.padding.right|0cm}}"
    style:rotation-angle="{{layout.cell.rotation|0}}"
    style:rotation-align="{{layout.cell.rotation.align|none}}"
    style:cell-protect="{{protection.cell.protect|none}}"
    style:print-content="{{printing.cell.content|true}}"
    style:decimal-places="{{formatting.cell.decimal_places|2}}"
    style:repeat-content="{{layout.cell.repeat_content|false}}"
    style:shrink-to-fit="{{layout.cell.shrink_to_fit|false}}"
    style:text-align-source="{{layout.cell.text_align_source|fix}}"
    style:direction="{{layout.cell.direction|ltr}}"
    style:glyph-orientation-vertical="{{layout.cell.glyph_orientation.vertical|auto}}"
    style:shadow="{{effects.cell.shadow|none}}"
    style:background-transparency="{{effects.cell.bg_transparency|0%}}"
    loext:vertical-justify="{{layout.cell.vertical_justify|automatic}}"
/>
```

#### Advanced Table Layout Control
```xml
<!-- Table-wide properties -->
<style:table-properties
    style:width="{{layout.table.width|100%}}"
    table:align="{{layout.table.align|margins}}"
    fo:margin="{{spacing.table.margin|0cm}}"
    fo:margin-top="{{spacing.table.margin.top|0cm}}"
    fo:margin-bottom="{{spacing.table.margin.bottom|0cm}}"
    fo:margin-left="{{spacing.table.margin.left|0cm}}"
    fo:margin-right="{{spacing.table.margin.right|0cm}}"
    style:may-break-between-rows="{{layout.table.break_between_rows|true}}"
    style:page-number="{{layout.table.page_number|auto}}"
    fo:break-before="{{layout.table.break_before|auto}}"
    fo:break-after="{{layout.table.break_after|auto}}"
    fo:background-color="{{brand.colors.table.background|transparent}}"
    style:background-transparency="{{effects.table.bg_transparency|0%}}"
    style:shadow="{{effects.table.shadow|none}}"
    table:border-model="{{layout.table.border_model|collapsing}}"
    table:display="{{layout.table.display|true}}"
    style:writing-mode="{{layout.table.writing_mode|lr-tb}}"
    table:table-centering="{{layout.table.centering|none}}"
/>
```

### 4. **Drawing and Graphics Advanced Properties**

#### Shape Precision Control
```xml
<!-- Advanced shape properties -->
<style:graphic-properties
    draw:stroke="{{graphics.stroke.type|none}}"
    draw:stroke-width="{{graphics.stroke.width|0.05cm}}"
    draw:stroke-color="{{graphics.stroke.color|#000000}}"
    draw:stroke-opacity="{{graphics.stroke.opacity|100%}}"
    draw:stroke-linejoin="{{graphics.stroke.line_join|miter}}"
    draw:stroke-linecap="{{graphics.stroke.line_cap|butt}}"
    draw:stroke-dash="{{graphics.stroke.dash|none}}"
    draw:stroke-dash-names="{{graphics.stroke.dash_names|}}"
    draw:marker-start="{{graphics.marker.start|none}}"
    draw:marker-end="{{graphics.marker.end|none}}"
    draw:marker-start-width="{{graphics.marker.start_width|0.3cm}}"
    draw:marker-end-width="{{graphics.marker.end_width|0.3cm}}"
    draw:marker-start-center="{{graphics.marker.start_center|false}}"
    draw:marker-end-center="{{graphics.marker.end_center|false}}"
    draw:fill="{{graphics.fill.type|none}}"
    draw:fill-color="{{graphics.fill.color|#FFFFFF}}"
    draw:fill-gradient-name="{{graphics.fill.gradient_name|}}"
    draw:fill-hatch-name="{{graphics.fill.hatch_name|}}"
    draw:fill-image-name="{{graphics.fill.image_name|}}"
    draw:opacity="{{graphics.fill.opacity|100%}}"
    draw:fill-image-width="{{graphics.fill.image.width|1cm}}"
    draw:fill-image-height="{{graphics.fill.image.height|1cm}}"
    style:repeat="{{graphics.fill.repeat|no-repeat}}"
    draw:fill-image-ref-point="{{graphics.fill.image.ref_point|top-left}}"
    draw:fill-image-ref-point-x="{{graphics.fill.image.ref_x|0%}}"
    draw:fill-image-ref-point-y="{{graphics.fill.image.ref_y|0%}}"
    draw:tile-repeat-offset="{{graphics.fill.tile_offset|0%}}"
    draw:transparency="{{graphics.transparency|0%}}"
    draw:shadow="{{graphics.shadow.visible|hidden}}"
    draw:shadow-offset-x="{{graphics.shadow.offset.x|0.3cm}}"
    draw:shadow-offset-y="{{graphics.shadow.offset.y|0.3cm}}"
    draw:shadow-color="{{graphics.shadow.color|#808080}}"
    draw:shadow-opacity="{{graphics.shadow.opacity|100%}}"
/>
```

#### Advanced Text Frame Properties
```xml
<!-- Text frame precision control -->
<style:graphic-properties
    text:anchor-type="{{layout.frame.anchor|paragraph}}"
    text:anchor-page-number="{{layout.frame.anchor.page|0}}"
    svg:x="{{layout.frame.position.x|0cm}}"
    svg:y="{{layout.frame.position.y|0cm}}"
    svg:width="{{layout.frame.size.width|5cm}}"
    svg:height="{{layout.frame.size.height|1cm}}"
    style:rel-width="{{layout.frame.relative.width|100%}}"
    style:rel-height="{{layout.frame.relative.height|100%}}"
    fo:min-width="{{layout.frame.min.width|0cm}}"
    fo:min-height="{{layout.frame.min.height|0cm}}"
    fo:max-width="{{layout.frame.max.width|none}}"
    fo:max-height="{{layout.frame.max.height|none}}"
    style:wrap="{{layout.frame.wrap|none}}"
    style:number-wrapped-paragraphs="{{layout.frame.wrap.paragraphs|no-limit}}"
    style:wrap-contour="{{layout.frame.wrap.contour|false}}"
    style:wrap-contour-mode="{{layout.frame.wrap.contour_mode|full}}"
    style:run-through="{{layout.frame.run_through|foreground}}"
    style:flow-with-text="{{layout.frame.flow_with_text|false}}"
    style:horizontal-pos="{{layout.frame.horizontal.position|from-left}}"
    style:horizontal-rel="{{layout.frame.horizontal.relative|paragraph}}"
    style:vertical-pos="{{layout.frame.vertical.position|from-top}}"
    style:vertical-rel="{{layout.frame.vertical.relative|paragraph}}"
    fo:padding="{{spacing.frame.padding|0cm}}"
    fo:padding-top="{{spacing.frame.padding.top|0cm}}"
    fo:padding-bottom="{{spacing.frame.padding.bottom|0cm}}"
    fo:padding-left="{{spacing.frame.padding.left|0cm}}"
    fo:padding-right="{{spacing.frame.padding.right|0cm}}"
    fo:border="{{borders.frame.default|none}}"
    style:border-line-width="{{borders.frame.line_width|0.05pt}}"
    fo:background-color="{{graphics.frame.bg_color|transparent}}"
    style:background-transparency="{{graphics.frame.bg_transparency|0%}}"
    style:editable="{{layout.frame.editable|false}}"
    style:protect="{{protection.frame.protect|none}}"
/>
```

### 5. **Presentation Advanced Properties**

#### Slide Transition Control
```xml
<!-- Advanced slide transitions -->
<style:drawing-page-properties
    presentation:transition-type="{{transitions.type|none}}"
    presentation:transition-style="{{transitions.style|none}}"
    presentation:transition-speed="{{transitions.speed|medium}}"
    presentation:duration="{{transitions.duration|00:00:00}}"
    presentation:visibility="{{presentation.slide.visibility|visible}}"
    presentation:background-visible="{{presentation.background.visible|true}}"
    presentation:background-objects-visible="{{presentation.background.objects|true}}"
    presentation:display-header="{{presentation.header.display|false}}"
    presentation:display-footer="{{presentation.footer.display|true}}"
    presentation:display-page-number="{{presentation.page_number.display|true}}"
    presentation:display-date-time="{{presentation.date_time.display|true}}"
    draw:fill="{{presentation.slide.fill.type|none}}"
    draw:fill-color="{{presentation.slide.fill.color|#FFFFFF}}"
    draw:fill-gradient-name="{{presentation.slide.fill.gradient|}}"
    draw:fill-image-name="{{presentation.slide.fill.image|}}"
    smil:type="{{presentation.smil.type|fadeInOut}}"
    smil:subtype="{{presentation.smil.subtype|crossfade}}"
    smil:dur="{{presentation.smil.duration|1s}}"
    smil:direction="{{presentation.smil.direction|forward}}"
    smil:fadeColor="{{presentation.smil.fade_color|#000000}}"
/>
```

### 6. **Page Layout Advanced Properties**

#### Master Page Control
```xml
<!-- Advanced page layout properties -->
<style:page-layout-properties
    fo:page-width="{{layout.page.width|21cm}}"
    fo:page-height="{{layout.page.height|29.7cm}}"
    style:print-orientation="{{layout.page.orientation|portrait}}"
    fo:margin-top="{{layout.page.margin.top|2cm}}"
    fo:margin-bottom="{{layout.page.margin.bottom|2cm}}"
    fo:margin-left="{{layout.page.margin.left|2cm}}"
    fo:margin-right="{{layout.page.margin.right|2cm}}"
    style:writing-mode="{{layout.page.writing_mode|lr-tb}}"
    style:layout-grid-mode="{{layout.page.grid.mode|none}}"
    style:layout-grid-base-width="{{layout.page.grid.base_width|0.706cm}}"
    style:layout-grid-base-height="{{layout.page.grid.base_height|0.706cm}}"
    style:layout-grid-ruby-width="{{layout.page.grid.ruby_width|0.353cm}}"
    style:layout-grid-ruby-height="{{layout.page.grid.ruby_height|0.353cm}}"
    style:layout-grid-lines="{{layout.page.grid.lines|20}}"
    style:layout-grid-color="{{layout.page.grid.color|#C0C0C0}}"
    style:layout-grid-ruby-below="{{layout.page.grid.ruby_below|false}}"
    style:layout-grid-print="{{layout.page.grid.print|false}}"
    style:layout-grid-display="{{layout.page.grid.display|false}}"
    style:footnote-max-height="{{layout.page.footnote.max_height|0cm}}"
    style:num-format="{{layout.page.number.format|1}}"
    style:num-prefix="{{layout.page.number.prefix|}}"
    style:num-suffix="{{layout.page.number.suffix|}}"
    style:paper-tray-name="{{printing.paper.tray|default}}"
    style:first-page-number="{{layout.page.first_number|continue}}"
    style:scale-to="{{printing.scale.to|100%}}"
    style:scale-to-pages="{{printing.scale.pages|1}}"
    style:table-centering="{{printing.table.centering|both}}"
    loext:scale-to-X="{{printing.scale.x|1}}"
    loext:scale-to-Y="{{printing.scale.y|1}}"
/>
```

### 7. **List and Numbering Advanced Properties**

#### Comprehensive List Control
```xml
<!-- Advanced list style properties -->
<text:list-level-style-bullet text:level="{{lists.bullet.level|1}}"
                             text:style-name="{{lists.bullet.style_name|}}"
                             style:num-suffix="{{lists.bullet.suffix|.}}"
                             style:num-prefix="{{lists.bullet.prefix|}}"
                             text:bullet-char="{{lists.bullet.character|•}}"
                             text:bullet-relative-size="{{lists.bullet.relative_size|100%}}">
    <style:list-level-properties text:list-level-position-and-space-mode="{{lists.position.mode|label-alignment}}"
                               text:min-label-width="{{lists.position.min_label_width|0.635cm}}"
                               text:min-label-distance="{{lists.position.min_label_distance|0.318cm}}"
                               fo:text-align="{{lists.position.text_align|start}}">
        <style:list-level-label-alignment text:label-followed-by="{{lists.label.followed_by|listtab}}"
                                        text:list-tab-stop-position="{{lists.label.tab_stop|1.27cm}}"
                                        fo:text-indent="{{lists.label.text_indent|-0.635cm}}"
                                        fo:margin-left="{{lists.label.margin_left|1.27cm}}"
        />
    </style:list-level-properties>
    <style:text-properties fo:font-family="{{lists.bullet.font.family|Liberation Sans}}"
                         style:font-family-generic="{{lists.bullet.font.generic|swiss}}"
                         style:font-pitch="{{lists.bullet.font.pitch|variable}}"
                         fo:color="{{lists.bullet.color|#000000}}"
                         fo:font-size="{{lists.bullet.font.size|12pt}}"
                         fo:font-weight="{{lists.bullet.font.weight|normal}}"
    />
</text:list-level-style-bullet>
```

## Implementation Strategy

### 1. **Priority Levels**
- **P0 - Critical**: Typography, color, spacing controls
- **P1 - High**: Table, shape, layout properties
- **P2 - Medium**: Advanced effects, transitions
- **P3 - Low**: Specialized formatting, legacy support

### 2. **LibreOffice Version Compatibility**
- **Core Properties**: Compatible with LibreOffice 6.0+
- **Extended Properties (loext:)**: LibreOffice 7.0+
- **Experimental Properties**: Latest versions only

### 3. **Cross-Platform Testing**
- **LibreOffice Writer**: ODT text documents
- **LibreOffice Impress**: ODP presentations
- **LibreOffice Calc**: ODS spreadsheets
- **LibreOffice Draw**: ODG graphics
- **Apache OpenOffice**: Compatibility verification

## Business Impact Summary

These hidden ODF properties provide:

1. **Typography Precision**: Character-level spacing, kerning, and effects control
2. **Layout Excellence**: Micro-adjustments to paragraph, table, and page layout
3. **Professional Effects**: Advanced shadows, fills, and transitions
4. **Brand Compliance**: Complete visual control for corporate consistency
5. **Cross-Platform Parity**: Matching OOXML capabilities in LibreOffice ecosystem

**Result**: StyleStack achieves the same "impossible level of control" over ODF documents as Microsoft Office documents, ensuring consistent brand experience across all office suites.