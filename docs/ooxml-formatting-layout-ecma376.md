# OOXML Formatting and Layout Features (ECMA-376)

# OOXML Formatting and Layout Features (ECMA-376)

## Text Styling and Typography (WordprocessingML and DrawingML)

Bold – The <w:b> element in WordprocessingML run properties toggles boldface on text (for non-complex scripts)[1]. In DrawingML (shapes/text boxes in PPTX or XLSX), bold is enabled via a b="1" attribute on the <a:rPr> (rich text run properties) element. (Applies to DOCX text runs; PPTX/XLSX shape text via DrawingML.)

Italic – The <w:i> element toggles italic styling on a text run[2]. (DrawingML uses an i="1" attribute on <a:rPr> for italic.) (DOCX runs; PPTX/XLSX shapes text.)

Underline – The <w:u> element underlines text. It has a w:val attribute to specify underline style (single, double, wave, etc.)[3]. (In DrawingML, u="solid" or other values on <a:rPr> achieve underlining.) (DOCX runs; PPTX/XLSX shapes text.)

Strikethrough/Double-Strikethrough – <w:strike> applies a single strikethrough and <w:dstrike> a double strikethrough on text[4]. (DOCX runs; PPTX/XLSX shapes text.)

All Caps/Small Caps – <w:caps> renders text in all capital letters, and <w:smallCaps> in small caps (lowercase shown as smaller capitals)[5]. (DOCX runs; not a direct DrawingML attribute, though similar effects can be emulated in presentations.)

Font Face and Size – <w:rFonts> sets the typeface for a run (fonts for Latin, East Asian, complex scripts, etc.), and <w:sz> sets font size (in half-points)[6][7]. <w:szCs> is the size for complex script text. (DOCX runs; in DrawingML, <a:rPr> has latin/ea font attributes and a sz attribute in 1/100 points for size.)

Color and Highlight – <w:color> sets the text color (RGB or theme color) of the run, and <w:highlight> marks a text highlight background (e.g. yellow)[8]. DrawingML uses <a:rPr> child <a:solidFill> (with <a:srgbClr>) for text color, and a separate <a:highlight> is not in DrawingML (Word’s highlight is typically not in PPTX). (DOCX; partial in PPTX/XLSX for text color via DrawingML fills.)

Spacing and Kerning – <w:spacing> adjusts character spacing (expanding or compressing the space between letters), and <w:kern> sets a minimum font size above which kerning is applied[9][10]. For example, <w:kern w:val="28"/> in a run means characters >=14pt will kern[10]. (DOCX; not explicitly in DrawingML text, which relies on font kerning by default.)

Position (Baseline Shift) – <w:position> raises or lowers text from the baseline by a specified half-point value (for superscript, subscript or custom offsets)[11]. (DOCX; in DrawingML, a baseline shift can be done via the baseline attribute in <a:rPr>.)

Subscript/Superscript – <w:vertAlign> with val="subscript" or val="superscript" visually offsets and scales text as subscript or superscript[12]. (DOCX; in DrawingML, achieved by baseline and font size adjustments since no direct vertAlign attribute.)

Shadow, Outline, Emboss, Imprint – <w:shadow> puts a drop-shadow on text, <w:outline> makes text characters outlined (hollow)[13], <w:emboss> and <w:imprint> create 3D embossed or engraved effects on text[14]. (DOCX; similar effects in PPTX via DrawingML text effects, e.g. <a:effectLst> with shadow.)

Emphasis Marks – <w:em> applies emphasis marks (dots/commas) above or below East Asian text[15]. (DOCX only – relevant to East Asian typography.)

Right-to-Left – <w:rtl> indicates the run text is right-to-left (for Arabic/Hebrew scripts)[16]. (DOCX; in DrawingML, <a:rPr rtl="1"> does similar.)

Language Tag – <w:lang> tags the run with language codes for spelling/grammar (e.g. <w:lang w:val="en-US"/>). This affects hyphenation and font substitution but not visual styling directly[17]. (DOCX only.)

Hidden Text – <w:vanish> hides the text from display/printing (it’s like having text with Hidden attribute)[18]. (DOCX only – not displayed; spreadsheets and slides have their own hide mechanisms.)

## Paragraph and Section Layout (WordprocessingML)

Paragraph Properties (WordprocessingML): Paragraph formatting is controlled by the <w:pPr> element[19]. Key paragraph-level features include:

Alignment/Justification – <w:jc> sets paragraph alignment: left, center, right, both (justified) etc.[19]. For example, <w:jc w:val="center"/> centers a paragraph[20]. (DOCX only; note PPTX shapes have their own text alignment in <a:pPr>.)

Indents – <w:ind> configures paragraph indentation (left indent, right indent, first line or hanging indent)[21][22]. E.g. w:left="720" would indent 0.5 inch. Mirror indents (<w:mirrorIndents/>) swap left/right on odd/even pages[23].

Spacing – <w:spacing> controls space before/after paragraphs and line spacing within the paragraph[24]. Attributes w:before/w:after are spacing in twentieths of a point, and w:line for line spacing (with rules like auto, exact, at least).

Line Break Rules – <w:keepLines> prevents page-breaking within the paragraph (all lines kept together)[25], and <w:keepNext> keeps the paragraph on the same page as the following paragraph (no page break between)[26]. <w:widowControl> enables/disables widow-orphan control to avoid single lines at page top/bottom[27].

Page Breaks – <w:pageBreakBefore> forces the paragraph to start on a new page (equivalent to a manual page break before it)[28].

Borders and Shading – <w:pBdr> encloses <w:top>, <w:bottom>, <w:left>, <w:right> to draw borders on the paragraph’s sides[29]. <w:shd> applies background shading (color/pattern) behind the paragraph[30].

Tabs – <w:tabs> contains <w:tab> entries that define custom tab stop positions and alignment (left, center, right, decimal tabs) for the paragraph[31].

Outline Level – <w:outlineLvl> assigns an outline level (heading level) to the paragraph for TOC/hierarchy purposes[32] (impacts logical structure, not visual style except via associated styles).

Hyphenation – <w:suppressAutoHyphens> when true will prevent Word from automatically hyphenating that paragraph’s text[33].

Line Numbering – <w:suppressLineNumbers> if present will exclude the paragraph from line numbering in the document[34].

Text Direction – <w:bidi> marks the paragraph as a right-to-left paragraph (for bidirectional layout)[35]. <w:textDirection> can specify vertical text flow (e.g. tbRl for top-to-bottom right-to-left in table cells or textboxes)[36].

Framework and Grid – <w:framePr> holds frame text box settings if the paragraph is placed in a text frame (position, width, etc.)[37]. <w:snapToGrid> can align the paragraph’s lines to the document grid (often for East Asian documents)[24].

Contextual Spacing – <w:contextualSpacing> when on will ignore Space Before/After between consecutive paragraphs of the same style (no extra gap)[38].

East Asian Typography – <w:kinsoku> enables kinsoku (East Asian line-breaking rules)[39], <w:wordWrap> allows breaking long words at any character if needed[40], <w:overflowPunct> allows punctuation to hang outside margins[41], and <w:topLinePunct> compresses punctuation at start of lines[42]. These control fine typography for CJK text.

Section Properties (WordprocessingML): Sections (<w:sectPr>) define page-level layout for groups of paragraphs[43][44]. Important section features:

Page Size & Orientation – <w:pgSz> sets the page dimensions (e.g. width, height in twips) and orientation (w:orient="portrait" or "landscape")[45]. For instance, <w:pgSz w:w="12240" w:h="15840" w:orient="landscape"/> sets landscape orientation.

Margins – <w:pgMar> defines page margins (top, bottom, left, right in twips, plus gutter)[46]. E.g. w:top="1440" for a 1-inch top margin.

Columns – <w:cols> contains settings for multiple columns in a section (number of columns, spacing, line between)[47]. Individual <w:col> elements within can specify width for each column or even column breaks.

Header/Footer Reference – (Not a formatting feature per se, but section properties link to headers/footers for that section.)

Page Borders – <w:pgBorders> defines borders around the page area (top/bottom/left/right edges of the page)[48], often used for decorative page frames.

Page Numbering – <w:pgNumType> controls page number format and resets (e.g. format as roman numerals, or start at 1 for a new section)[49].

Line Numbering – <w:lnNumType> (if present) turns on line numbers in the margin, with attributes for numbering interval, start value, distance from text[50].

Columns Gutter – <w:cols w:space="720"/> for example sets space between columns. There is also a <w:rtlGutter> attribute if the gutter (binding) is on right side for RTL documents[51].

Section Break Type – <w:type> specifies the section break behavior (continuous, next page, even/odd page)[52].

Vertical Alignment – <w:vAlign> in sectPr sets vertical alignment of text on the page (e.g., center the text on the page vertically, often used for cover pages)[52].

Text Direction – <w:textDirection> at section level can declare all text in the section flows vertically (used for East Asian page layouts)[53].

Document Grid – <w:docGrid> defines a baseline grid or character grid for the section (common in East Asian layouts to align characters in columns)[54]. Attributes like type="lines" with linePitch (spacing) control grid spacing.

Paper Source – <w:paperSrc> holds printer tray info (which tray to use for first page, etc.) – not visual formatting, but part of section settings[48].

Even/Odd Page Margins – <w:mirrorMargins> (in the document settings) can be used in conjunction with section margins to treat left/right as inside/outside for book layout. Also <w:gutter> margin is an extra space for binding.

(All above are DOCX-specific. Google Docs/Workspace conversion fidelity tests would ensure these page and paragraph settings are preserved.)

## Table Layout and Formatting (WordprocessingML)

Tables in WordprocessingML are represented by <w:tbl> elements, with child <w:tblPr> for table properties and <w:tblGrid> for column grid definitions[55]. Key table formatting features include:

Table Width and Alignment – <w:tblW> in <tblPr> sets the preferred table width (in absolute value or percent)[56]. The table can be aligned relative to page via <w:jc> inside <tblPr> (e.g., <w:jc w:val="center"/> to center the table between margins[57]).

Table Indent – <w:tblInd> indents the table from the margin by a specified value[58] (often used if table is not full-width).

Layout Mode – <w:tblLayout> controls table sizing mode[58]. w:type="fixed" for fixed column widths (no autofit) or "autofit" for Word’s automatic column width adjustment.

Table Style – <w:tblStyle> references a table style by name (which applies a set of formatting)[59]. The <w:tblLook> element stores flags for which style aspects apply (first row banding, last column, etc.)[60][61]. For example, firstRow, band1Horz attributes in tblLook indicate header row styling and horizontal banding are on.

Conditional Formatting (Banded Rows/Columns) – <w:tblLook> with attributes like firstRow, lastRow, band1Horz, band1Vert etc. controls which parts of the table get special formatting from the style (e.g., striped bands)[61]. This corresponds to design features like banded rows or highlight on first/last column in Word’s table styles.

Table Borders – <w:tblBorders> contains border definitions for the table’s outer edges and inner cell borders[29]. Child elements <w:top>, <bottom>, <left>, <right>, <insideH> (inside horizontal) and <insideV> (inside vertical) specify line style (w:val="single" etc.), thickness (w:sz in 1/8 point) and color[29][62].

Cell Spacing vs. Cell Margins – <w:tblCellSpacing> (in tblPr) adds spacing between table cells (like cell padding external to cell borders)[63]. In contrast, <w:tblCellMar> defines default cell margins (padding inside each cell) on each side[64]. For example, a table might have tblCellSpacing of 100 (twips) to separate cells, or cell margins of 50 twips on all sides for padding.

Table Positioning – <w:tblpPr> allows a table to float like an object, with positioning relative to page or text (similar to textboxes)[65]. It has attributes for distance from surrounding text, horizontal alignment or absolute position, etc. <w:tblOverlap> (yes/no) indicates if a floating table can overlap with text or other tables[66].

Row Height – <w:trHeight> in <trPr> sets a table row’s height[67]. It can specify an exact height or minimum height (via hRule attribute: exact or auto). If not set, height is determined by content. Example: <w:trHeight w:val="300" w:hRule="exact"/> for an exact height of 300 twips.

Header Rows – <w:tblHeader> in a <trPr> marks that row to repeat as a table header at the top of each page if the table spans multiple pages[68][69]. A row with <w:tblHeader/> will be repeated by Word on subsequent pages[68]. (Only the first continuous set of header rows from the table’s start are repeated[70].)

Allow Row Break Across Pages – <w:cantSplit> in <trPr> when set to true (<w:cantSplit/>) prevents Word from breaking that row across pages[71]. The entire row moves to next page if it doesn’t fit. By default, rows can split across pages.

Cell Width – <w:tcW> in <tcPr> specifies a cell’s preferred width (in twips or percentage) for that cell[72]. If not given, it may be determined by table layout algorithm or evenly from table width.

Cell Margins – <w:tcMar> in <tcPr> can override the default cell padding for an individual cell[73]. It contains <top>, <bottom>, etc., similar to tblCellMar but per cell.

Cell Borders & Shading – <w:tcBorders> in <tcPr> defines the borders for that table cell (same elements as table borders)[73]. <w:shd> in <tcPr> sets cell background color/pattern fill[74] (overrides table style shading).

Cell Alignment & Direction – <w:vAlign> in <tcPr> sets vertical alignment of content in the cell (top, center, bottom)[75]. <w:textDirection> in <tcPr> can rotate text in a cell (e.g., vertical text); values include tbRl (top-to-bottom right-to-left), btLr (bottom-to-top left-to-right), etc.[76].

No Wrap – <w:noWrap> in <tcPr> prevents word wrapping in the cell, so the cell’s width will expand with content on one line (or content may overflow)[77].

Fit Text – <w:tcFitText> in <tcPr> causes text in the cell to be compressed to fit the cell width (it shrinks the text size as needed)[78]. This is analogous to Excel’s “Shrink to fit”. Example: <w:tcFitText/> in a narrow cell will reduce font size to avoid overflow.

Vertical Merging – <w:vMerge> in <tcPr> enables vertically merged cells (row spans)[79]. The first cell of the span has <w:vMerge w:val="restart"/>, and cells to merge below have <w:vMerge w:val="continue"/>. This vertically joins those cells into one visual cell spanning multiple rows.

(Table features above are for DOCX. PPTX also supports tables via DrawingML, with similar concepts – e.g., cell margins, borders, etc., though represented differently. Google Workspace fidelity tests should ensure banding, cell spacing, alignments, etc., round-trip correctly.)

## Shape and DrawingML Features (DOCX/PPTX/XLSX)

Office Open XML uses DrawingML (<a:...> elements in the drawingml namespace) for shapes, images, text boxes, and other drawings. Key visual formatting features for shapes include:

Fills (Solid, Gradient, Pattern, Picture) – Shape fill is specified with child elements of <a:spPr> (shape properties). <a:solidFill> fills with a solid color (e.g., <a:srgbClr val="FF0000"/> for red). <a:gradFill> defines gradient fills with multiple <a:gs> (gradient stop) colors[80][81]. <a:pattFill> applies preset patterns with foreground/background colors. <a:blipFill> is used for picture/image fills (referencing an image).

Outlines (Line Properties) – The shape’s outline (border) is set by <a:ln> inside <a:spPr>. You can specify line color (<a:solidFill> inside <a:ln>), width (w attribute in points *12700, since units are EMUs), dash style (<a:prstDash val="dash"> for dashed lines, etc.), cap style, join style (miter, round, bevel)[82], and compound line (double lines etc.).

Effects – Shapes can have various effects defined in an <a:effectLst> inside <a:spPr>. Examples:

Shadow: <a:outerShdw> for a drop shadow outside the shape, or <a:innerShdw> for inner shadow[83]. Attributes include offset (dx, dy), blur radius, direction, distance, and color (<a:srgbClr> inside).

Glow: <a:glow> adds a colored halo glow around the shape edges[84][85]. The rad attribute sets the glow radius (blur size)[85], and a color child element defines glow color.

Reflection: <a:reflection> creates a mirrored reflection below the shape[86]. It has properties like transparency, blur and offset distance.

Soft Edges: <a:softEdge> applies a soft blur to shape edges (simulating feathered edges). The rad attribute sets the radius of the blur.

Bevel: There are 3D bevel effects for shape faces/edges via <a:bevelTop> and <a:bevelBottom> in the 3D shape properties (these give a raised or pressed 3D edge look with depth and contour).

3D Rotation: <a:scene3d> and <a:sp3d> can specify 3D rotation (X, Y, Z rotation angles) and perspective for the shape, often with an <a:scene3d><a:camera> and <a:lightRig> for lighting.

Other Effects: Grayscale (<a:grayscl>), transparency adjustments, blurs on entire shape (<a:blur> effect applies an even blur to the shape content[87]), and fill overlays exist as well.

Geometry & Rounded Corners – The shape’s geometry is defined by <a:prstGeom> (preset geometry) with a prst attribute (e.g., prst="rect" or prst="cloudCallout") and optional <a:avLst><a:gd name="adj" val="..."/> to adjust geometry parameters. Rounded rectangles, for example, use prst="roundRect" and an adjustment value for corner radius. If custom geometry is needed, <a:custGeom> can outline vector commands. A Boolean property <a:roundedCorners> can appear (for charts) to toggle drawing with rounded corners on the container[88].

Transformations (Position and Size) – Each shape has an <a:xfrm> specifying position and size. <a:off x=""/> and y="" set the shape’s top-left corner coordinates, and <a:ext cx=""/> and cy="" set the size (width, height) in EMUs. Additionally, rot attribute on <a:xfrm> rotates the shape (in degrees * 60000, since unit is 1/60000th deg). flipH/flipV attributes can mirror-flip the shape horizontally or vertically.

Text Box & Insets – If the shape contains text, <a:bodyPr> (body properties) element inside the shape defines text layout. It includes attributes for text margins inside the shape (e.g., lIns, tIns for left/top inset in points, stored in EMUs) and vertical alignment of text (anchor="ctr" for center, etc.). It also can set text flow direction and whether to wrap shape’s text.

Anchoring (WordprocessingML-specific) – In Word documents, drawings (shapes, images, text boxes) can be inline or floating. Inline shapes are represented by <w:drawing> containing a <wp:inline> element. Floating shapes use <wp:anchor> inside <w:drawing>[89]. The <wp:anchor> element has attributes and child elements controlling positioning:

Positioning: <wp:positionH> and <wp:positionV> specify horizontal and vertical alignment or offset relative to a reference (margin, page, column, etc.)[90]. For example, positionH could align the object center to page center, or position at an absolute X offset.

Wrapping: Child elements like <wp:wrapNone>, <wp:wrapSquare>, <wp:wrapTight>, <wp:wrapThrough>, <wp:wrapTopAndBottom> define how text flows around the object[91][92]. e.g., square wrapping flows text in a rectangle around the shape’s bounding box.

Overlap and Placement: Attributes allowOverlap="true" let a floating object overlap others[93][94]. behindDoc="true" renders it behind text (watermark-like)[95]. layoutInCell="true" (for shapes in tables) means if the anchor is in a table cell, the shape stays within that cell’s area[96][97]; if false, it can escape the cell boundaries.

Extent: <wp:extent cx, cy> gives the size of the shape in EMUs[98]. <wp:effectExtent> adds extra margins if effects (like glow/shadow) extend beyond the normal shape bounds[99].

Simple Pos: <wp:simplePos> can give a raw x,y offset if no specific alignment reference is used, though often Word uses the anchored positioning with alignment for floating.

These ensure that in Word, floating shapes (text boxes, images) maintain intended layout. In contrast, PPTX and XLSX do not use <wp:anchor> – their shapes are positioned in a coordinate space on the slide or sheet. PPTX shapes have a similar <a:xfrm> within <p:sp> (shape) specifying position on the slide.

Grouping and Ordering – Multiple shapes can be grouped (in DrawingML, a <grpSp> group shape with its own transform that contains child shapes). Stacking order (z-order) is implied by order in the drawing part; also, <wp:zIndex> in WordprocessingML anchor specifies layering among overlapping objects.

(These DrawingML features apply to Word (for text boxes, images, shapes within DOCX), PowerPoint (all content on slides is shapes), and Excel (shapes/charts on worksheets). Google’s converters need to preserve fills, outlines, effects (shadows, glow, etc.), rotations and anchor positions to maintain visual fidelity.)

## Chart Layout and Styling (DrawingML Charts)

Embedded charts in OOXML (e.g., in XLSX, PPTX, DOCX) use Chart DrawingML (c: namespace). The chart part defines series data and various layout elements. Key chart formatting features:

Chart and Plot Area – The <c:chart> element contains the <c:plotArea> which in turn holds the specific chart type elements and axes[100]. The plot area can have a fill and border: a <c:spPr> (shape properties) inside <c:plotArea> or <c:chartArea> controls the chart background fill (e.g., solid color or none) and outline of the plot area. For instance, a chart with a gray plot area might have <c:plotArea><c:spPr><a:solidFill><a:srgbClr val="EEEEEE"/></a:solidFill>….

Chart Title – <c:title> element defines the chart title text and formatting[101]. It contains <c:tx> (text) and can include its own <c:spPr> for the title’s shape (fill/line) and <c:txPr> for text properties (font size, color, alignment). The title can be positioned via <c:layout> (manual layout).

Legend – <c:legend> element controls the chart legend[102][103]. Inside it, <c:legendPos val="r"/> (for example) positions the legend (top, bottom, left, right, or top-right corner)[104]. There are also flags like <c:overlay val="1"/> to allow the legend to overlay the plot area. The legend can have a border/fill via <c:spPr> in legend, and individual legend entries (<c:legendEntry>) can be formatted or hidden.

Axes – Charts have category and value axes (e.g., <c:catAx>, <c:valAx> for X and Y axes):

Tick Marks: <c:majorTickMark> and <c:minorTickMark> elements set tick mark position for the axis (values: in, out, cross or none)[105][106].

Gridlines: <c:majorGridlines> and <c:minorGridlines> elements, if present, create grid lines. Each can have its own <c:spPr> to style the line (color, dash, thickness)[107][108]. For example, major gridlines might be solid light gray lines across the plot.

Axis Line: The axis itself can be formatted via <c:spPr> under the axis (to set line style for axis line).

Labels: <c:tickLblPos val="nextTo" places axis labels, and <c:numFmt formatCode="General"/> or specific code sets the number format for axis labels (e.g., "0%" for percentage)[109].

Scaling: <c:scaling> with <c:min>/<c:max> can define explicit axis bounds[110], and <c:orientation val="minMax"/> or "maxMin" sets axis direction (normal or reversed)[111].

Axis Titles: <c:title> within an axis element provides an axis title with similar substructure as chart title.

Data Series and Points – Each series is represented with <c:ser> inside the specific chart type container (e.g., <c:barChart><c:ser>...</c:ser></c:barChart>):

Series Styling: Within <c:ser>, a <c:spPr> element defines the appearance of that series’ graphical elements[107]. For a bar/column, spPr fill color determines bar color; for a line, spPr outline sets line color/style; for an area, it’s the area fill. For example, a series might have <c:spPr><a:solidFill><a:srgbClr val="4472C4"/></a:solidFill></c:spPr> to color bars blue.

Markers: For line (or scatter/radar) charts, <c:marker> within the series sets marker symbol (<c:symbol val="circle"/> etc.), size, and formatting. It can contain <c:spPr> for the marker’s fill/line (e.g., outline color of marker)[112].

Data Labels: A series can have <c:dLbls> (or individual <c:dLbl> per point) to show values or names on data points. <c:dLbls> has children like <c:dLblPos val="above"/> to position labels (above, below, center, inside end, etc. on bars) and boolean toggles <c:showVal/>, <c:showCatName/>, <c:showSerName/> to display the value, category name, or series name in labels[113][114]. For example, <c:showVal val="1"/> means show data values. Each data label (or the whole set) can be formatted with its own <c:spPr> (for text box fill/line) and <c:txPr> (text font size/color).

Error Bars, Trendlines: Series may include <c:errBars> (with plus/minus values and line style) or <c:trendline> (with type linear, moving avg, etc.) each with formatting; these are more specialized.

Individual Points: <c:dPt> elements allow formatting a specific data point in a series. Each <c:dPt> can contain a <c:idx> to identify which point and a <c:spPr> to override that point’s fill/line (e.g., one bar in a series colored differently).

Chart Types – There are many chart type elements (within plotArea): <c:barChart>, <c:lineChart>, <c:pieChart>, <c:scatterChart>, <c:areaChart>, <c:bubbleChart>, etc.[115][116]. Each has specific sub-elements:

Bar/Column charts have <c:barDir val="col"/> or "bar", <c:gapWidth> (space between bars) and <c:overlap> (for overlapping series)[117].

Line charts have <c:smooth val="1"/> to turn on smooth curves[114].

Pie charts can have <c:firstSliceAng> (rotation of first slice) and optional explosion for pie-of-pie.

Scatter charts define axes for X and Y and use markers; bubble charts have bubble size data and <c:showNegBubbles/> toggle.

3D Charts: e.g., <c:surface3DChart>, <c:bar3DChart> have extra elements like <c:view3D> (perspective, rotation X/Y)[101] and walls/floor formatting (<c:sideWall>, <c:backWall>, <c:floor> each with <c:spPr> for 3D surface appearance)[118][119].

Chart Area and Plot Area Formatting – <c:chartSpace> is the root chart container. It can contain <c:spPr> for the chart area (the entire chart bounding box outside the plot). Additionally, <c:plotArea> as noted has its own <c:spPr>. There is also a Boolean <c:roundedCorners val="1"/> that can make the chart area corners rounded[120].

Text in Charts – Chart text (titles, axis labels, data labels, legend text) can be formatted using <c:txPr> which contains DrawingML text body markup (<a:bodyPr>, <a:lstStyle>, <a:p>). Within these, runs of text have <a:rPr> where you set font family (e.g., <a:latin typeface="Calibri"/>), font size (sz in 100ths of a point), color (solidFill), bold/italic (b,i attributes) etc. This parallels how shape text is formatted. For example, a chart title might have <c:txPr><a:bodyPr/><a:p><a:r><a:rPr lang="en-US" sz="1400" b="1"/><a:t>Sales 2025</a:t></a:r></a:p></c:txPr> to make it 14pt bold.

Data Table – If a chart has a data table (grid of values under the chart), <c:dTable> element is used with attributes like <c:showHorzBorder/>, <c:showVertBorder/>, <c:showOutline/> to toggle table gridlines[121]. The data table can also have <c:spPr> for its border and fill.

Embedded Charts in Excel (XLSX) – They appear in a separate chart part, but the SpreadsheetML worksheet has a <drawing> that references it. The chart’s position on a spreadsheet is given by an <xdr:twoCellAnchor> in the drawing, specifying from/to cell coordinates. In PPTX, charts are just another graphic frame on a slide with a specified size/position. These positioning elements ensure the chart appears at the right location in the document.

(Chart features apply to charts embedded in Word, PowerPoint, or Excel. Ensuring Google Workspace preserves series colors, axis options, legend placement, data label positions, etc., is crucial for round-trip fidelity[107][105].)

## Spreadsheet Layout (SpreadsheetML – XLSX)

Finally, Excel-specific formatting and layout features are defined in SpreadsheetML:

Column Widths – Columns are defined in the <cols> section with <col> elements. Each <col> can cover a range of columns via min and max attributes and set a width. The width attribute is the column width measured in Excel’s character units[122][123]. For example, <col min="5" max="5" width="9.14" customWidth="1"/> means column E has width ~9.14 characters and is custom-set[124]. customWidth="1" indicates the width isn’t the default[125]. There are also flags: bestFit (if Excel auto-fit calculated this width)[126], hidden="1" if the column is hidden, and collapsed for outline grouping state[127].

Row Heights – Rows in <sheetData> can include a ht attribute for height in points, and customHeight="1" if not default[128][129]. For instance, <row r="10" ht="24" customHeight="1"> sets row 10 to 24 points tall. Omitted means default height. hidden="1" on a row hides that row[130]. Rows also have outline grouping level (outlineLevel="…") and collapsed flag similar to columns for outlines (to show/hide grouped rows)[131][132].

Cell Number Formatting – The <numFmt> elements in the workbook’s style part (xl/styles.xml) define custom number formats. Cell styles (<xf> entries) then reference either a built-in number format ID or a custom numFmtId. This controls how cell values are displayed (e.g., date format, currency, percentage). For example, a date cell might have numFmtId="14" (built-in Excel date format) or a custom code like numFmtId="164" formatCode="[$€-407]#,##0.00" for Euro currency. This is crucial for visual representation of values (though not an XML element in sheet, it’s a formatting feature).

Cell Styles (XF) and Direct Formatting – The combination of <xf> records in styles part define the alignment, font, border, fill, etc., for cells. Each cell in <c r="A1"> can have a style index s="n" pointing to an <xf> which includes alignment, applyFont, applyFill flags, etc. This system means the visual style of each cell (including number format, font color, background color) is controlled by these style indices.

Borders – Cell borders are defined in style part <borders> (a set of <border> entries). A border entry has child <left>, <right>, <top>, <bottom>, <diagonal> each with style and color attributes. A cell style <xf> references a border by index. There’s also a concept of diagonalUp/diagonalDown for diagonal lines through cells.

Fills (Cell Shading) – Fills (background cell color/pattern) are listed in <fills> with <fill><patternFill patternType="...">…</patternFill></fill>. Solid fills use patternType="solid" and a <fgColor rgb="FFFF0000"/> for red, for example[133]. The cell’s style XF references the fill index. Conditional formatting can override cell fill as well.

Alignment – The <alignment> element (within cell <xf> or within a <dxf> for conditional formatting) controls text alignment in cells[133][134]:

Horizontal Alignment: horizontal attribute can be left, center, right, fill (repeat text to fill cell), justify, centerContinuous (center across selection), or distributed[135][136].

Vertical Alignment: vertical can be top, center, bottom, justify, distributed[137].

Text Wrap: wrapText="1" means wrap text onto multiple lines within the cell[138].

Shrink to Fit: shrinkToFit="1" will automatically reduce font size so that text fits in the cell without wrapping[139].

Indent: indent="N" indents the cell text N levels (each level ~3 spaces width)[140]. (Indent works with horizontal align left or distributed)[141].

Text Rotation: textRotation="90" rotates text 90° up, 180 would appear upside-down, and a special value 255 indicates vertical text (characters stacked top-to-bottom)[142][143]. The spec defines 0-180 as degrees; for 91-180 it calculates as an orientation downwards[144].

Reading Order: readingOrder="2" for Right-to-Left (Hebrew/Arabic), 1 for LTR, 0 for context-dependent[145].

Justify Last Line: justifyLastLine="1" (mostly for East Asian distributed alignment – it stretches the last line as well)[146].

These alignment attributes ensure cell content is visually positioned as desired[147][148].

Fonts – Fonts are defined in the styles part <fonts> (name, family, size, color, bold, italic, underline etc.), and cell styles reference a font by index. For example, a font entry might have <sz val="11"/> (11pt), <color theme="1"/> (themed color or <color rgb="FF0000"/> for red), <b/> for bold, <i/> for italic, <u/> for single underline. Different script fonts (East Asian <eastAsian> or complex script) can be specified too.

Conditional Formatting – <conditionalFormatting> elements in the worksheet define rules and formatting for cell ranges. Each <cfRule> can have a type (e.g., type="colorScale", "iconSet", "dataBar", or formula-based like "expression"). Notable visual formats:

Color Scale: type="colorScale" uses a <colorScale> element with 2 or 3 <cfvo> (value points like min, midpoint, max) and corresponding <color> for each[149]. This produces a gradient fill in the cell background from one color to another according to value.

Icon Set: type="iconSet" uses an <iconSet> element with attributes like iconSet="3Arrows" (choice of icon style) and child <cfvo> thresholds[150][151]. It displays symbols (up/down arrows, traffic lights, etc.) in the cell based on the cell’s value percentile or cutoff[152]. Attributes reverse="1" or showValue="0" can reverse icon order or hide the numeric value[153].

Data Bar: type="dataBar" uses a <dataBar> element with <cfvo> for min/max and <color> for the bar color. This draws a gradient or solid bar in the cell proportional to the value. E.g., a blue data bar from 0 to 100%.

Each of these rules can have priority (order of precedence) and can be set to stop if true. The formatting specifics (colors, icons, etc.) are all captured in these elements and must round-trip.

Merged Cells – A <mergeCells> collection in a worksheet lists merged cell ranges. Each <mergeCell> has a ref="A1:C1" for example, indicating cells A1 through C1 are merged into one cell. Visually, the content in the top-left of the merge range is displayed centered across the merged area. The OOXML consumer (Excel) uses this to render multi-column or multi-row headers. In the file, the cell content resides in the first cell, and others are blank but merged.

Print Layout Settings – Not asked explicitly, but relevant layout: <pageMargins> (in worksheet) sets print margins; <pageSetup> for orientation (portrait/landscape) and scaling; <rowBreaks>/<colBreaks> for manual page breaks. These impact printed appearance.

Gridlines and Headings – Workbook settings can turn off gridline or heading display, but those aren’t formatting of content, more UI.

Sheet Background – Excel allows a background image (<picture> in sheetViews), not exactly OOXML content to preserve in Google, but note.

Hidden/Very Hidden Sheets or Rows/Cols – As noted, rows and cols have a hidden attribute. Entire sheets can be hidden via workbook settings (<sheetState state="hidden">). This is about visibility rather than format, but relevant if testing fidelity (hidden content should remain hidden).

All the above elements and attributes are non-deprecated parts of the ECMA-376 (ISO/IEC 29500) specification and directly affect visual presentation. They should be included in “torture test” documents to verify that Google Workspace can preserve these properties on import/export. By structuring DOCX, PPTX, and XLSX with combinations of these features – from intricate text styling (kerning, small caps)[6], paragraph keeps and breaks[154], complex table layouts (cell merges, repeats)[68], shape effects (glows, shadows)[84], chart formatting (custom series colors, axis options)[107], to rich spreadsheet cell formats (conditional formatting icons, rotated text)[155][150] – one can stress-test the fidelity of Office Open XML support in conversion tools. Each feature’s spec reference ensures it’s implemented according to the standard, avoiding deprecated legacy constructs.

Sources:

ECMA-376 1st ed. Part 4 (Markup Language Reference) – WordprocessingML (sections on run properties, paragraph properties, tables)[1][19][56], DrawingML (shapes, effects)[84][156], SpreadsheetML (alignment, columns, rows)[157][122], and DrawingML-Charts (chart elements)[103][107]. These define the behavior and allowed values of the above features in OOXML.

[1] b (Bold)

https://c-rex.net/samples/ooxml/e1/Part4/OOXML_P4_DOCX_b_topic_ID0EP6EO.html

[2] [3] [4] [5] [6] [7] [8] [9] [10] [11] [12] [13] [14] [15] [16] [17] [18] kern (Font Kerning)

https://c-rex.net/samples/ooxml/e1/part4/OOXML_P4_DOCX_kern_topic_ID0EKUNO.html

[19] [20] [21] [22] [23] [24] [25] [26] [27] [28] [30] [31] [32] [33] [34] [35] [36] [37] [38] [39] [40] [41] [42] [154] Paragraphs

https://c-rex.net/samples/ooxml/e1/Part4/OOXML_P4_DOCX_Paragraphs_topic_ID0EADBI.html

[29] [55] [56] [58] [59] [60] [72] [75] [76] [78] [79] Tables

https://c-rex.net/samples/ooxml/e1/Part4/OOXML_P4_DOCX_Tables_topic_ID0ETOIQ.html

[43] [44] [45] [46] [47] [48] [49] [50] [51] [52] [53] [54] Sections

https://c-rex.net/samples/ooxml/e1/Part4/OOXML_P4_DOCX_Sections_topic_ID0ECA3S.html

[57] Office Open XML (OOXML) - Word Processing - Table Alignment

http://officeopenxml.com/WPtableAlignment.php

[61] [63] [64] [65] [66] [67] [68] [69] [70] [71] [73] [74] [77] tblHeader (Repeat Table Row on Every New Page)

https://c-rex.net/samples/ooxml/e1/Part4/OOXML_P4_DOCX_tblHeader_topic_ID0EYTHR.html

[62] Office Open XML (OOXML) - Word Processing - Table Borders

http://officeopenxml.com/WPtableBorders.php

[80] [81] [82] [83] [84] [85] [86] glow (Glow Effect)

https://c-rex.net/samples/ooxml/e1/Part4/OOXML_P4_DOCX_glow_topic_ID0EJKXMB.html

[87] blur (Blur Effect) - C-REX

https://c-rex.net/samples/ooxml/e1/Part4/OOXML_P4_DOCX_blur_topic_ID0EB3PMB.html

[88] [100] [101] [102] [103] [104] [105] [106] [109] [110] [111] [113] [114] [115] [116] [117] [118] [119] [120] [121] chart (Chart)

https://c-rex.net/samples/ooxml/e1/part4/OOXML_P4_DOCX_chart_topic_ID0EY6WPB.html

[89] [90] [91] [92] [93] [94] [95] [96] [97] [98] [99] [156] anchor (Anchor for Floating DrawingML Object)

https://c-rex.net/samples/ooxml/e1/Part4/OOXML_P4_DOCX_anchor_topic_ID0EOB1OB.html

[107] [108] [112] spPr (Shape Properties)

https://c-rex.net/samples/ooxml/e1/part4/OOXML_P4_DOCX_spPr_topic_ID0EE3DRB.html

[122] [123] [124] [125] [126] [127] col (Column Width & Formatting)

https://c-rex.net/samples/ooxml/e1/Part4/OOXML_P4_DOCX_col_topic_ID0ELFQ4.html

[128] [129] [130] [131] [132] row (Row)

https://c-rex.net/samples/ooxml/e1/part4/OOXML_P4_DOCX_row_topic_ID0EIKD5.html

[133] [134] [135] [136] [137] [138] [139] [140] [141] [142] [143] [144] [145] [146] [147] [148] [155] [157] alignment (Alignment)

https://c-rex.net/samples/ooxml/e1/part4/OOXML_P4_DOCX_alignment_topic_ID0EQT25.html

[149] colorScale (Color Scale) - C-REX

https://c-rex.net/samples/ooxml/e1/part4/OOXML_P4_DOCX_colorScale_topic_ID0EGRR4.html

[150] [151] [152] [153] iconSet (Icon Set)

https://c-rex.net/samples/ooxml/e1/part4/OOXML_P4_DOCX_iconSet_topic_ID0EDA24.html

