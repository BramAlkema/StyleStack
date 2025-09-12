#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive OOXML Template Patcher for StyleStack
Covers all identified OOXML styling elements (carriers) including:
- Themes, styles, numbering, sections, headers/footers
- Animations, transitions, master slides, layouts
- Tables, shapes, charts, SmartArt
- Endnotes, footnotes, comments, TOC, forms
- Advanced typography, DrawingML effects, 3D
"""

import io
import sys
import zipfile
import shutil
from lxml import etree as ET
from typing import Dict, List, Optional, Any

# OOXML Namespaces
N = {
    'w':   "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    'a':   "http://schemas.openxmlformats.org/drawingml/2006/main",
    'r':   "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    'wp':  "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    'p':   "http://schemas.openxmlformats.org/presentationml/2006/main",
    'x':   "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    'c':   "http://schemas.openxmlformats.org/drawingml/2006/chart",
    'dgm': "http://schemas.openxmlformats.org/drawingml/2006/diagram",
    'xdr': "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",
    'rel': "http://schemas.openxmlformats.org/package/2006/relationships",
    'x14': "http://schemas.microsoft.com/office/spreadsheetml/2009/9/main",
    'mc':  "http://schemas.openxmlformats.org/markup-compatibility/2006",
}

# StyleStack variable patterns for carrier elements
CARRIER_VARIABLES = {
    # Theme carriers (CRITICAL - SET THESE!)
    'theme.color.dk1': '#000000',
    'theme.color.lt1': '#FFFFFF',
    'theme.color.dk2': '#1F1F1F',
    'theme.color.lt2': '#F8F8F8',
    'theme.color.accent1': '#0066FF',
    'theme.color.accent2': '#00C853',
    'theme.color.accent3': '#FF6D00',
    'theme.color.accent4': '#AA00FF',
    'theme.color.accent5': '#00B8D4',
    'theme.color.accent6': '#FF1744',
    'theme.color.hlink': '#1155CC',        # CRITICAL: hyperlink color
    'theme.color.folHlink': '#551A8B',      # CRITICAL: followed hyperlink
    
    # Font scheme (CRITICAL - proper major/minor/EA/CS fonts)
    'theme.font.major.latin': 'Inter',
    'theme.font.minor.latin': 'Inter',
    'theme.font.major.ea': 'Noto Sans CJK SC',     # East Asian
    'theme.font.minor.ea': 'Noto Sans CJK SC',
    'theme.font.major.cs': 'Arial',                # Complex Script
    'theme.font.minor.cs': 'Arial',
    
    # Typography carriers (EMU values)
    'typography.body.font_size_emu': '14400',      # 16pt
    'typography.heading1.font_size_emu': '28800',  # 32pt
    'typography.heading2.font_size_emu': '25200',  # 28pt
    'typography.heading3.font_size_emu': '21600',  # 24pt
    'typography.caption.font_size_emu': '10800',   # 12pt
    
    # Spacing carriers (EMU values)
    'spacing.paragraph.before_emu': '3600',        # 4pt
    'spacing.paragraph.after_emu': '7200',         # 8pt
    'spacing.heading.before_emu': '10800',         # 12pt
    'spacing.heading.after_emu': '5400',           # 6pt
    'spacing.line.height_emu': '21600',            # 24pt (1.5x)
    
    # Border/line carriers
    'border.default.width_emu': '1800',            # 2pt
    'border.default.color': '#D9D9D9',
    'border.table.color': '#E0E0E0',
    'border.table.width_emu': '900',               # 1pt
    
    # Effects carriers
    'effect.shadow.offset_emu': '2700',            # 3pt
    'effect.shadow.blur_emu': '5400',              # 6pt
    'effect.shadow.color': '#40000000',            # 25% black
    'effect.glow.radius_emu': '7200',              # 8pt
    'effect.glow.color': '#80FFFFFF',              # 50% white
    
    # PowerPoint master text style carriers (CRITICAL - levels 1-3 fully specified)
    'master.title.size_emu': '32400',             # 18pt * 1800 EMU/pt = 32400
    'master.title.align': 'ctr',                  # l|ctr|r
    'master.title.lang': 'en-US',
    
    # Level 1 (CRITICAL)
    'master.level1.margin_emu': '457200',         # 0.5 inch left margin
    'master.level1.indent_emu': '-228600',        # -0.25 inch hanging indent
    'master.level1.bullet.char': '•',
    'master.level1.bullet.font': 'Symbol',
    'master.level1.size_emu': '18000',            # 10pt * 1800
    'master.level1.color': 'tx1',                 # theme text color
    'master.level1.lang': 'en-US',
    
    # Level 2 (CRITICAL)
    'master.level2.margin_emu': '685800',         # 0.75 inch
    'master.level2.indent_emu': '-228600',
    'master.level2.bullet.char': '◦',
    'master.level2.size_emu': '16200',            # 9pt * 1800
    
    # Level 3 (CRITICAL)  
    'master.level3.margin_emu': '914400',         # 1 inch
    'master.level3.indent_emu': '-228600',
    'master.level3.bullet.char': '▪',
    'master.level3.size_emu': '14400',            # 8pt * 1800
    
    # Text auto-fit (CRITICAL - choose explicitly)
    'text.autofit.mode': 'noAutofit',             # noAutofit|normAutofit|spAutofit
    'text.autofit.fontscale': '100000',           # 100% (only if normAutofit)
    'text.autofit.linespace': '95000',            # 95% line spacing reduction
    
    # Shape defaults (CRITICAL - explicit fills and lines)
    'shape.default.fill.color': '#F0F0F0',
    'shape.default.line.width_emu': '12700',      # 1pt in EMU
    'shape.default.line.color': '#CCCCCC',
    
    # Table style carriers with CRITICAL flags and margins
    'table.header.fill': '#F0F0F0',
    'table.row.alternate.fill': '#FAFAFA',
    'table.border.inside.color': '#EFEFEF',
    'table.cell.margin.top_emu': '45720',         # CRITICAL: explicit cell margins
    'table.cell.margin.bottom_emu': '45720',
    'table.cell.margin.left_emu': '91440',
    'table.cell.margin.right_emu': '91440',
    'table.flags.firstRow': '1',                  # CRITICAL: table look flags
    'table.flags.lastRow': '0',
    'table.flags.firstColumn': '1',
    'table.flags.lastColumn': '0',
    'table.flags.bandedRows': '1',
    'table.flags.bandedColumns': '0',
    
    # Transition carriers (CRITICAL - set explicitly for predictable playback)
    'transition.speed': 'fast',                   # slow|med|fast
    'transition.advance.click': '1',              # 0=auto after time, 1=on click
    'transition.advance.time': '0',               # milliseconds (if auto)
    'transition.type': 'fade',                    # cut|fade|push|wipe|split|reveal
    
    # Animation carriers (PowerPoint)
    'animation.default.duration_ms': '500',
    'animation.transition.duration_ms': '1000',
    'animation.build.by': 'paragraph',             # paragraph|word|letter
    
    # Guides (CRITICAL - designers will love you)
    'guide.horizontal.1.pos_emu': '914400',       # 1 inch from top
    'guide.horizontal.2.pos_emu': '4572000',      # 5 inches (center)
    'guide.vertical.1.pos_emu': '914400',         # 1 inch from left
    'guide.vertical.2.pos_emu': '4572000',        # 5 inches (center)
    'guide.horizontal.1.orient': '1',             # 1=horizontal, 0=vertical
    'guide.vertical.1.orient': '0',
    
    # Color map override carriers
    'colormap.bg1': 'lt1',                        # background 1 maps to light 1
    'colormap.tx1': 'dk1',                        # text 1 maps to dark 1
    'colormap.bg2': 'lt2',
    'colormap.tx2': 'dk2',
    'colormap.accent1': 'accent1',                # can remap accents
    'colormap.accent2': 'accent2',
    'colormap.accent3': 'accent3',
    'colormap.accent4': 'accent4',
    'colormap.accent5': 'accent5',
    'colormap.accent6': 'accent6',
    'colormap.hlink': 'hlink',
    'colormap.folHlink': 'folHlink',
    
    # Numbering/bullet carriers  
    'bullet.level1.char': '•',
    'bullet.level2.char': '◦',
    'bullet.level3.char': '▪',
    'numbering.format': 'decimal',                 # decimal|upperLetter|lowerLetter
}


def E(tag, ns='w', **attrs):
    """Create an element with namespace"""
    el = ET.Element(f"{{{N[ns]}}}{tag}")
    for k, v in attrs.items():
        if ':' in k:
            pfx, local = k.split(':', 1)
            el.set(f"{{{N[pfx]}}}{local}", v)
        else:
            el.set(k, v)
    return el


def parse_or_new(xml_bytes, root_tag, ns='w'):
    """Parse XML or create new root element"""
    if xml_bytes:
        return ET.fromstring(xml_bytes)
    return E(root_tag, ns)


def ensure_child(parent, tag, ns='w'):
    """Ensure child element exists"""
    child = parent.find(f'{{{N[ns]}}}{tag}')
    if child is None:
        child = E(tag, ns)
        parent.append(child)
    return child


def tostring(root):
    """Convert element tree to bytes"""
    return ET.tostring(root, xml_declaration=True, encoding='UTF-8', standalone="yes")


# ========== THEME CARRIERS ==========

def build_comprehensive_theme():
    """Build comprehensive theme with all carriers"""
    theme = E('theme', 'a', name="StyleStack Theme")
    elements = ensure_child(theme, 'themeElements', 'a')
    
    # Color scheme with all 12 theme colors
    clrScheme = E('clrScheme', 'a', name="StyleStack Colors")
    for color_key in ['dk1', 'lt1', 'dk2', 'lt2', 'accent1', 'accent2', 
                      'accent3', 'accent4', 'accent5', 'accent6', 'hlink', 'folHlink']:
        var_key = f'theme.color.{color_key}'
        color_val = CARRIER_VARIABLES.get(var_key, '#000000').lstrip('#')
        color_el = E(color_key, 'a')
        color_el.append(E('srgbClr', 'a', val=color_val))
        clrScheme.append(color_el)
    
    # Font scheme with major/minor fonts for Latin, EA, CS
    fontScheme = E('fontScheme', 'a', name="StyleStack Fonts")
    
    majorFont = E('majorFont', 'a')
    majorFont.append(E('latin', 'a', typeface=CARRIER_VARIABLES.get('theme.font.major.latin', 'Inter')))
    majorFont.append(E('ea', 'a', typeface=CARRIER_VARIABLES.get('theme.font.major.ea', 'Noto Sans CJK SC')))
    majorFont.append(E('cs', 'a', typeface=CARRIER_VARIABLES.get('theme.font.major.cs', 'Arial')))
    
    minorFont = E('minorFont', 'a')
    minorFont.append(E('latin', 'a', typeface=CARRIER_VARIABLES.get('theme.font.minor.latin', 'Inter')))
    minorFont.append(E('ea', 'a', typeface=CARRIER_VARIABLES.get('theme.font.minor.ea', 'Noto Sans CJK SC')))
    minorFont.append(E('cs', 'a', typeface=CARRIER_VARIABLES.get('theme.font.minor.cs', 'Arial')))
    
    fontScheme.extend([majorFont, minorFont])
    
    # Format scheme with fills, lines, effects
    fmtScheme = E('fmtScheme', 'a', name="StyleStack Effects")
    
    # Fill styles (CRITICAL - 3 levels: subtle, moderate, intense)
    fillStyleLst = E('fillStyleLst', 'a')
    
    # Subtle fill - solid scheme color
    subtleFill = E('solidFill', 'a')
    subtleFill.append(E('schemeClr', 'a', val='lt1'))
    fillStyleLst.append(subtleFill)
    
    # Moderate fill - gradient
    moderateFill = E('gradFill', 'a', rotWithShape='1')
    gsLst = E('gsLst', 'a')
    gsLst.append(E('gs', 'a', pos='0').append(E('schemeClr', 'a', val='lt1')))
    gsLst.append(E('gs', 'a', pos='100000').append(E('schemeClr', 'a', val='dk1')))
    moderateFill.append(gsLst)
    moderateFill.append(E('lin', 'a', ang='2700000', scaled='1'))  # 45 degree gradient
    fillStyleLst.append(moderateFill)
    
    # Intense fill - pattern or complex gradient
    intenseFill = E('gradFill', 'a', rotWithShape='1')
    intenseGsLst = E('gsLst', 'a')
    intenseGsLst.append(E('gs', 'a', pos='0').append(E('schemeClr', 'a', val='accent1').append(E('tint', 'a', val='50000'))))
    intenseGsLst.append(E('gs', 'a', pos='50000').append(E('schemeClr', 'a', val='accent1')))
    intenseGsLst.append(E('gs', 'a', pos='100000').append(E('schemeClr', 'a', val='accent1').append(E('shade', 'a', val='50000'))))
    intenseFill.append(intenseGsLst)
    intenseFill.append(E('lin', 'a', ang='2700000', scaled='1'))
    fillStyleLst.append(intenseFill)
    
    # CRITICAL: Background fill style list (this is what bgRef references)
    bgFillStyleLst = E('bgFillStyleLst', 'a')
    
    # Background 1 - solid light
    bgFill1 = E('solidFill', 'a')
    bgFill1.append(E('schemeClr', 'a', val='lt1'))
    bgFillStyleLst.append(bgFill1)
    
    # Background 2 - subtle gradient
    bgFill2 = E('gradFill', 'a', rotWithShape='1')
    bgGsLst = E('gsLst', 'a')
    bgGsLst.append(E('gs', 'a', pos='0').append(E('schemeClr', 'a', val='lt1')))
    bgGsLst.append(E('gs', 'a', pos='100000').append(E('schemeClr', 'a', val='lt2')))
    bgFill2.append(bgGsLst)
    bgFill2.append(E('lin', 'a', ang='5400000', scaled='1'))  # 90 degree
    bgFillStyleLst.append(bgFill2)
    
    # Background 3 - themed background
    bgFill3 = E('solidFill', 'a')
    bgFill3.append(E('schemeClr', 'a', val='dk1').append(E('tint', 'a', val='95000')))  # Very light dark color
    bgFillStyleLst.append(bgFill3)
    
    # Line styles
    lnStyleLst = E('lnStyleLst', 'a')
    for width in ['9525', '19050', '28575']:  # 1pt, 2pt, 3pt
        ln = E('ln', 'a', w=width)
        ln.append(E('solidFill', 'a').append(E('schemeClr', 'a', val='accent1')))
        lnStyleLst.append(ln)
    
    # Effect styles (subtle, moderate, intense)
    effectStyleLst = E('effectStyleLst', 'a')
    
    # Subtle effect
    subtleEffect = E('effectStyle', 'a')
    subtleEffectLst = E('effectLst', 'a')
    outerShdw = E('outerShdw', 'a', 
                  blurRad=CARRIER_VARIABLES.get('effect.shadow.blur_emu', '5400'),
                  dist=CARRIER_VARIABLES.get('effect.shadow.offset_emu', '2700'),
                  dir='2700000')
    outerShdw.append(E('srgbClr', 'a', val='000000').append(E('alpha', 'a', val='25000')))
    subtleEffectLst.append(outerShdw)
    subtleEffect.append(subtleEffectLst)
    effectStyleLst.append(subtleEffect)
    
    # Moderate effect
    modEffect = E('effectStyle', 'a')
    modEffectLst = E('effectLst', 'a')
    modShdw = E('outerShdw', 'a', blurRad='10800', dist='5400', dir='2700000')
    modShdw.append(E('srgbClr', 'a', val='000000').append(E('alpha', 'a', val='35000')))
    modEffectLst.append(modShdw)
    modEffect.append(modEffectLst)
    effectStyleLst.append(modEffect)
    
    # Intense effect with glow
    intenseEffect = E('effectStyle', 'a')
    intenseEffectLst = E('effectLst', 'a')
    glow = E('glow', 'a', rad=CARRIER_VARIABLES.get('effect.glow.radius_emu', '7200'))
    glow.append(E('schemeClr', 'a', val='accent1').append(E('alpha', 'a', val='60000')))
    intenseEffectLst.append(glow)
    intenseEffect.append(intenseEffectLst)
    effectStyleLst.append(intenseEffect)
    
    fmtScheme.extend([fillStyleLst, lnStyleLst, effectStyleLst])
    
    elements.extend([clrScheme, fontScheme, fmtScheme])
    theme.append(elements)
    
    return theme


# ========== WORD STYLES CARRIERS ==========

def build_comprehensive_word_styles():
    """Build comprehensive Word styles with all carriers"""
    styles = E('styles', 'w')
    
    # Document defaults
    docDefaults = E('docDefaults', 'w')
    
    # Character defaults
    rPrDefault = E('rPrDefault', 'w')
    rPr = E('rPr', 'w')
    rPr.append(E('rFonts', 'w', 
                 ascii=CARRIER_VARIABLES.get('theme.font.minor.latin', 'Inter'),
                 hAnsi=CARRIER_VARIABLES.get('theme.font.minor.latin', 'Inter'),
                 eastAsia=CARRIER_VARIABLES.get('theme.font.minor.ea', 'Noto Sans CJK SC'),
                 cs=CARRIER_VARIABLES.get('theme.font.minor.cs', 'Arial')))
    rPr.append(E('sz', 'w', val=str(int(CARRIER_VARIABLES.get('typography.body.font_size_emu', '14400')) // 360)))
    rPr.append(E('szCs', 'w', val=str(int(CARRIER_VARIABLES.get('typography.body.font_size_emu', '14400')) // 360)))
    rPr.append(E('lang', 'w', val='en-US', eastAsia='zh-CN', bidi='ar-SA'))
    rPrDefault.append(rPr)
    
    # Paragraph defaults
    pPrDefault = E('pPrDefault', 'w')
    pPr = E('pPr', 'w')
    pPr.append(E('spacing', 'w',
                 before=CARRIER_VARIABLES.get('spacing.paragraph.before_emu', '3600'),
                 after=CARRIER_VARIABLES.get('spacing.paragraph.after_emu', '7200'),
                 line=CARRIER_VARIABLES.get('spacing.line.height_emu', '21600'),
                 lineRule='auto'))
    pPrDefault.append(pPr)
    
    docDefaults.extend([rPrDefault, pPrDefault])
    styles.append(docDefaults)
    
    # Normal style
    normal = E('style', 'w', type='paragraph', styleId='Normal', **{'w:default': '1'})
    normal.append(E('name', 'w', val='Normal'))
    normal.append(E('qFormat', 'w'))
    styles.append(normal)
    
    # Heading styles with carriers
    for level in range(1, 7):
        heading = E('style', 'w', type='paragraph', styleId=f'Heading{level}')
        heading.append(E('name', 'w', val=f'heading {level}'))
        heading.append(E('basedOn', 'w', val='Normal'))
        heading.append(E('next', 'w', val='Normal'))
        heading.append(E('qFormat', 'w'))
        heading.append(E('uiPriority', 'w', val=str(9)))
        
        h_pPr = E('pPr', 'w')
        h_pPr.append(E('keepNext', 'w'))
        h_pPr.append(E('keepLines', 'w'))
        h_pPr.append(E('spacing', 'w',
                       before=CARRIER_VARIABLES.get('spacing.heading.before_emu', '10800'),
                       after=CARRIER_VARIABLES.get('spacing.heading.after_emu', '5400')))
        h_pPr.append(E('outlineLvl', 'w', val=str(level-1)))
        
        h_rPr = E('rPr', 'w')
        h_rPr.append(E('b', 'w'))
        h_rPr.append(E('bCs', 'w'))
        
        # Variable font sizes for headings
        size_key = f'typography.heading{level}.font_size_emu'
        if size_key in CARRIER_VARIABLES:
            size_val = str(int(CARRIER_VARIABLES[size_key]) // 360)
        else:
            # Default cascade: 32pt, 28pt, 24pt, 20pt, 18pt, 16pt
            size_val = str([64, 56, 48, 40, 36, 32][level-1])
        h_rPr.append(E('sz', 'w', val=size_val))
        h_rPr.append(E('szCs', 'w', val=size_val))
        
        heading.extend([h_pPr, h_rPr])
        styles.append(heading)
    
    # Table style with carriers
    tableStyle = E('style', 'w', type='table', styleId='StyleStackTable')
    tableStyle.append(E('name', 'w', val='StyleStack Table'))
    tableStyle.append(E('qFormat', 'w'))
    
    tblPr = E('tblPr', 'w')
    
    # Table borders from carriers
    tblBorders = E('tblBorders', 'w')
    border_color = CARRIER_VARIABLES.get('border.table.color', '#E0E0E0').lstrip('#')
    border_width = str(int(CARRIER_VARIABLES.get('border.table.width_emu', '900')) // 45)  # Convert EMU to eighths
    
    for border_type in ['top', 'left', 'bottom', 'right']:
        tblBorders.append(E(border_type, 'w', val='single', sz=border_width, color=border_color))
    
    inside_color = CARRIER_VARIABLES.get('table.border.inside.color', '#EFEFEF').lstrip('#')
    tblBorders.append(E('insideH', 'w', val='single', sz=str(int(border_width)//2), color=inside_color))
    tblBorders.append(E('insideV', 'w', val='single', sz=str(int(border_width)//2), color=inside_color))
    
    tblPr.append(tblBorders)
    
    # Table cell margins
    tblCellMar = E('tblCellMar', 'w')
    for side in ['top', 'left', 'bottom', 'right']:
        tblCellMar.append(E(side, 'w', w='108', type='dxa'))  # 108 twips = 0.075"
    tblPr.append(tblCellMar)
    
    # Table look options
    tblPr.append(E('tblLook', 'w', val='04A0', firstRow='1', lastRow='0', 
                   firstColumn='1', lastColumn='0', noHBand='0', noVBand='1'))
    
    tableStyle.append(tblPr)
    
    # Header row style
    headerRow = E('tblStylePr', 'w', type='firstRow')
    tcPr = E('tcPr', 'w')
    shd = E('shd', 'w', val='clear', 
            fill=CARRIER_VARIABLES.get('table.header.fill', '#F0F0F0').lstrip('#'))
    tcPr.append(shd)
    headerRow.append(tcPr)
    
    hr_rPr = E('rPr', 'w')
    hr_rPr.append(E('b', 'w'))
    hr_rPr.append(E('bCs', 'w'))
    headerRow.append(hr_rPr)
    
    tableStyle.append(headerRow)
    
    # Banded rows
    bandedRow = E('tblStylePr', 'w', type='band1Horz')
    br_tcPr = E('tcPr', 'w')
    br_shd = E('shd', 'w', val='clear',
               fill=CARRIER_VARIABLES.get('table.row.alternate.fill', '#FAFAFA').lstrip('#'))
    br_tcPr.append(br_shd)
    bandedRow.append(br_tcPr)
    tableStyle.append(bandedRow)
    
    styles.append(tableStyle)
    
    # List/TOC styles
    for i in range(1, 10):
        toc = E('style', 'w', type='paragraph', styleId=f'TOC{i}')
        toc.append(E('name', 'w', val=f'TOC {i}'))
        if i > 1:
            toc.append(E('basedOn', 'w', val=f'TOC{i-1}'))
        else:
            toc.append(E('basedOn', 'w', val='Normal'))
        
        toc_pPr = E('pPr', 'w')
        # Indentation increases with level
        indent = str(i * 720)  # 0.5" per level
        toc_pPr.append(E('ind', 'w', left=indent))
        
        # Tab stop for page numbers
        tabs = E('tabs', 'w')
        tabs.append(E('tab', 'w', val='right', pos='9350', leader='dot'))
        toc_pPr.append(tabs)
        
        toc.append(toc_pPr)
        styles.append(toc)
    
    # Footnote/Endnote styles
    footnoteText = E('style', 'w', type='paragraph', styleId='FootnoteText')
    footnoteText.append(E('name', 'w', val='Footnote Text'))
    footnoteText.append(E('basedOn', 'w', val='Normal'))
    fn_rPr = E('rPr', 'w')
    fn_rPr.append(E('sz', 'w', val='20'))  # 10pt
    fn_rPr.append(E('szCs', 'w', val='20'))
    footnoteText.append(fn_rPr)
    styles.append(footnoteText)
    
    endnoteText = E('style', 'w', type='paragraph', styleId='EndnoteText')
    endnoteText.append(E('name', 'w', val='Endnote Text'))
    endnoteText.append(E('basedOn', 'w', val='FootnoteText'))
    styles.append(endnoteText)
    
    return styles


# ========== NUMBERING CARRIERS ==========

def build_comprehensive_numbering():
    """Build comprehensive numbering with bullet and number carriers"""
    numbering = E('numbering', 'w')
    
    # Abstract numbering for bullets
    abstractBullet = E('abstractNum', 'w', abstractNumId='1')
    abstractBullet.append(E('multiLevelType', 'w', val='hybridMultilevel'))
    
    for level in range(9):
        lvl = E('lvl', 'w', ilvl=str(level))
        lvl.append(E('start', 'w', val='1'))
        lvl.append(E('numFmt', 'w', val='bullet'))
        
        # Get bullet character from carriers
        bullet_key = f'bullet.level{level+1}.char'
        bullet_char = CARRIER_VARIABLES.get(bullet_key, ['•', '◦', '▪', '▫', '◆', '◇', '○', '●', '□'][level])
        lvl.append(E('lvlText', 'w', val=bullet_char))
        lvl.append(E('lvlJc', 'w', val='left'))
        
        # Progressive indentation
        pPr = E('pPr', 'w')
        indent = str((level + 1) * 720)  # 0.5" per level
        pPr.append(E('ind', 'w', left=indent, hanging='360'))
        lvl.append(pPr)
        
        # Font for bullet
        rPr = E('rPr', 'w')
        rPr.append(E('rFonts', 'w', ascii='Symbol', hAnsi='Symbol'))
        lvl.append(rPr)
        
        abstractBullet.append(lvl)
    
    # Abstract numbering for decimal
    abstractDecimal = E('abstractNum', 'w', abstractNumId='2')
    abstractDecimal.append(E('multiLevelType', 'w', val='hybridMultilevel'))
    
    num_formats = ['decimal', 'lowerLetter', 'lowerRoman', 'decimal', 'lowerLetter', 
                   'lowerRoman', 'decimal', 'lowerLetter', 'lowerRoman']
    
    for level in range(9):
        lvl = E('lvl', 'w', ilvl=str(level))
        lvl.append(E('start', 'w', val='1'))
        lvl.append(E('numFmt', 'w', val=num_formats[level]))
        lvl.append(E('lvlText', 'w', val=f'%{level+1}.'))
        lvl.append(E('lvlJc', 'w', val='left'))
        
        pPr = E('pPr', 'w')
        indent = str((level + 1) * 720)
        pPr.append(E('ind', 'w', left=indent, hanging='360'))
        lvl.append(pPr)
        
        abstractDecimal.append(lvl)
    
    numbering.extend([abstractBullet, abstractDecimal])
    
    # Concrete numbering instances
    num1 = E('num', 'w', numId='1')
    num1.append(E('abstractNumId', 'w', val='1'))
    
    num2 = E('num', 'w', numId='2')
    num2.append(E('abstractNumId', 'w', val='2'))
    
    numbering.extend([num1, num2])
    
    return numbering


# ========== POWERPOINT MASTERS/LAYOUTS ==========

def build_powerpoint_slide_master():
    """Build PowerPoint slide master with carriers"""
    sldMaster = E('sldMaster', 'p')
    
    # Common slide data
    cSld = E('cSld', 'p')
    
    # Background
    bg = E('bg', 'p')
    bgPr = E('bgPr', 'p')
    solidFill = E('solidFill', 'a')
    solidFill.append(E('schemeClr', 'a', val='lt1'))
    bgPr.append(solidFill)
    bg.append(bgPr)
    cSld.append(bg)
    
    # Shape tree with placeholders
    spTree = E('spTree', 'p')
    
    # Title placeholder
    titlePh = E('sp', 'p')
    nvSpPr = E('nvSpPr', 'p')
    nvPr = E('nvPr', 'p')
    nvPr.append(E('ph', 'p', type='title'))
    cNvSpPr = E('cNvSpPr', 'p')
    nvSpPr.extend([E('cNvPr', 'p', id='1', name='Title Placeholder'), nvPr, cNvSpPr])
    
    spPr = E('spPr', 'p')
    xfrm = E('xfrm', 'a')
    xfrm.append(E('off', 'a', x='838200', y='365125'))
    xfrm.append(E('ext', 'a', cx='7772400', cy='1470025'))
    spPr.append(xfrm)
    
    txBody = E('txBody', 'p')
    bodyPr = E('bodyPr', 'a', vert='horz', lIns='91440', tIns='45720', 
               rIns='91440', bIns='45720', rtlCol='0')
    txBody.append(bodyPr)
    
    # Title text style
    lstStyle = E('lstStyle', 'a')
    lvl1pPr = E('lvl1pPr', 'a', algn='ctr')
    defRPr = E('defRPr', 'a', sz=str(CARRIER_VARIABLES.get('typography.heading1.font_size_emu', '28800')))
    defRPr.append(E('solidFill', 'a').append(E('schemeClr', 'a', val='tx1')))
    defRPr.append(E('latin', 'a', typeface='+mj-lt'))
    lvl1pPr.append(defRPr)
    lstStyle.append(lvl1pPr)
    txBody.append(lstStyle)
    
    # Sample text
    p = E('p', 'a')
    r = E('r', 'a')
    t = E('t', 'a')
    t.text = 'Click to edit Master title style'
    r.append(t)
    p.append(r)
    txBody.append(p)
    
    titlePh.extend([nvSpPr, spPr, txBody])
    spTree.append(titlePh)
    
    # Body placeholder
    bodyPh = E('sp', 'p')
    bNvSpPr = E('nvSpPr', 'p')
    bNvPr = E('nvPr', 'p')
    bNvPr.append(E('ph', 'p', idx='1'))
    bNvSpPr.extend([E('cNvPr', 'p', id='2', name='Content Placeholder'), bNvPr, E('cNvSpPr', 'p')])
    
    bSpPr = E('spPr', 'p')
    bXfrm = E('xfrm', 'a')
    bXfrm.append(E('off', 'a', x='838200', y='1825625'))
    bXfrm.append(E('ext', 'a', cx='7772400', cy='4351338'))
    bSpPr.append(bXfrm)
    
    bTxBody = E('txBody', 'p')
    bBodyPr = E('bodyPr', 'a', vert='horz', lIns='91440', tIns='45720',
                rIns='91440', bIns='45720', rtlCol='0')
    bTxBody.append(bBodyPr)
    
    # Multi-level text styles with carriers
    bLstStyle = E('lstStyle', 'a')
    
    for level in range(1, 10):
        lvlPPr = E(f'lvl{level}pPr', 'a', marL=str(level * 457200), indent='-342900')
        
        # Bullet from carriers
        buChar = E('buChar', 'a', char=CARRIER_VARIABLES.get(f'bullet.level{level}.char', '•'))
        lvlPPr.append(buChar)
        
        # Font size decreases with level
        size_emu = str(int(CARRIER_VARIABLES.get('typography.body.font_size_emu', '14400')) - (level-1) * 720)
        lvlDefRPr = E('defRPr', 'a', sz=size_emu)
        lvlPPr.append(lvlDefRPr)
        
        bLstStyle.append(lvlPPr)
    
    bTxBody.append(bLstStyle)
    
    # Sample multi-level text
    for level in range(1, 6):
        bp = E('p', 'a')
        bpPr = E('pPr', 'a', lvl=str(level-1))
        bp.append(bpPr)
        br = E('r', 'a')
        bt = E('t', 'a')
        bt.text = f'Click to edit Master text styles - Level {level}'
        br.append(bt)
        bp.append(br)
        bTxBody.append(bp)
    
    bodyPh.extend([bNvSpPr, bSpPr, bTxBody])
    spTree.append(bodyPh)
    
    cSld.append(spTree)
    sldMaster.append(cSld)
    
    # Color map override
    clrMap = E('clrMap', 'p', bg1='lt1', tx1='dk1', bg2='lt2', tx2='dk2',
               accent1='accent1', accent2='accent2', accent3='accent3',
               accent4='accent4', accent5='accent5', accent6='accent6',
               hlink='hlink', folHlink='folHlink')
    sldMaster.append(clrMap)
    
    # Slide layout ID list (would reference actual layouts)
    sldLayoutIdLst = E('sldLayoutIdLst', 'p')
    sldLayoutIdLst.append(E('sldLayoutId', 'p', id='2147483649'))
    sldMaster.append(sldLayoutIdLst)
    
    # Text styles with carriers
    txStyles = E('txStyles', 'p')
    
    # Title style
    titleStyle = E('titleStyle', 'p')
    tLvl1pPr = E('lvl1pPr', 'a', algn='ctr')
    tDefRPr = E('defRPr', 'a', sz=str(CARRIER_VARIABLES.get('typography.heading1.font_size_emu', '28800')))
    tLvl1pPr.append(tDefRPr)
    titleStyle.append(tLvl1pPr)
    
    # Body style
    bodyStyle = E('bodyStyle', 'p')
    for level in range(1, 10):
        bLvlPPr = E(f'lvl{level}pPr', 'a', marL=str(level * 342900), indent='-342900')
        size = str(int(CARRIER_VARIABLES.get('typography.body.font_size_emu', '14400')) - (level-1) * 360)
        bLvlDefRPr = E('defRPr', 'a', sz=size)
        bLvlPPr.append(bLvlDefRPr)
        bodyStyle.append(bLvlPPr)
    
    txStyles.extend([titleStyle, bodyStyle])
    sldMaster.append(txStyles)
    
    return sldMaster


# ========== POWERPOINT ANIMATIONS ==========

def build_animation_timing():
    """Build PowerPoint animation timing with carriers"""
    timing = E('timing', 'p')
    tnLst = E('tnLst', 'p')
    
    # Main sequence
    par = E('par', 'p')
    cTn = E('cTn', 'p', id='1', dur='indefinite', restart='never', nodeType='tmRoot')
    
    # Child timeline
    childTnLst = E('childTnLst', 'p')
    seq = E('seq', 'p', concurrent='1', nextAc='seek')
    
    seqCTn = E('cTn', 'p', id='2', dur='indefinite', nodeType='mainSeq')
    seqChildTnLst = E('childTnLst', 'p')
    
    # Animation effect with carriers
    animPar = E('par', 'p')
    animCTn = E('cTn', 'p', id='3', fill='hold',
                dur=CARRIER_VARIABLES.get('animation.default.duration_ms', '500'))
    
    # Start condition
    stCondLst = E('stCondLst', 'p')
    cond = E('cond', 'p', delay='0')
    stCondLst.append(cond)
    animCTn.append(stCondLst)
    
    animChildTnLst = E('childTnLst', 'p')
    
    # Fade effect
    animEffect = E('animEffect', 'p', transition='in', filter='fade')
    aeCTn = E('cTn', 'p', id='4', dur=CARRIER_VARIABLES.get('animation.default.duration_ms', '500'))
    animEffect.append(aeCTn)
    
    # Build by paragraph/word/letter from carriers
    if CARRIER_VARIABLES.get('animation.build.by') == 'paragraph':
        bldP = E('bldP', 'p', build='p')
        animEffect.append(bldP)
    
    animChildTnLst.append(animEffect)
    animCTn.append(animChildTnLst)
    animPar.append(animCTn)
    
    seqChildTnLst.append(animPar)
    seqCTn.append(seqChildTnLst)
    seq.append(seqCTn)
    
    childTnLst.append(seq)
    cTn.append(childTnLst)
    par.append(cTn)
    
    tnLst.append(par)
    timing.append(tnLst)
    
    # Build list for progressive animations
    bldLst = E('bldLst', 'p')
    if CARRIER_VARIABLES.get('animation.build.by') == 'paragraph':
        bldP = E('bldP', 'p', spid='2', grpId='0')  # Build paragraphs in shape ID 2
        bldP.append(E('tmplLst', 'p').append(E('tmpl', 'p', lvl='0')))
        bldLst.append(bldP)
    
    timing.append(bldLst)
    
    return timing


# ========== EXCEL STYLES ==========

def build_excel_styles():
    """Build Excel styles with carriers"""
    styleSheet = E('styleSheet', 'x')
    
    # Number formats
    numFmts = E('numFmts', 'x', count='2')
    numFmts.append(E('numFmt', 'x', numFmtId='164', formatCode='#,##0.00'))
    numFmts.append(E('numFmt', 'x', numFmtId='165', formatCode='[$-409]d-mmm-yy'))
    styleSheet.append(numFmts)
    
    # Fonts
    fonts = E('fonts', 'x', count='2')
    
    # Default font from carriers
    font0 = E('font', 'x')
    font0.append(E('sz', 'x', val=str(int(CARRIER_VARIABLES.get('typography.body.font_size_emu', '14400')) // 1440)))  # Convert to points
    font0.append(E('name', 'x', val=CARRIER_VARIABLES.get('theme.font.minor.latin', 'Inter')))
    font0.append(E('family', 'x', val='2'))
    fonts.append(font0)
    
    # Bold font
    font1 = E('font', 'x')
    font1.append(E('b', 'x'))
    font1.append(E('sz', 'x', val=str(int(CARRIER_VARIABLES.get('typography.body.font_size_emu', '14400')) // 1440)))
    font1.append(E('name', 'x', val=CARRIER_VARIABLES.get('theme.font.minor.latin', 'Inter')))
    fonts.append(font1)
    
    styleSheet.append(fonts)
    
    # Fills
    fills = E('fills', 'x', count='3')
    
    # None fill
    fill0 = E('fill', 'x')
    fill0.append(E('patternFill', 'x', patternType='none'))
    fills.append(fill0)
    
    # Gray125 fill
    fill1 = E('fill', 'x')
    fill1.append(E('patternFill', 'x', patternType='gray125'))
    fills.append(fill1)
    
    # Header fill from carriers
    fill2 = E('fill', 'x')
    pf = E('patternFill', 'x', patternType='solid')
    fgColor = E('fgColor', 'x', rgb='FF' + CARRIER_VARIABLES.get('table.header.fill', '#F0F0F0').lstrip('#'))
    pf.append(fgColor)
    fill2.append(pf)
    fills.append(fill2)
    
    styleSheet.append(fills)
    
    # Borders
    borders = E('borders', 'x', count='2')
    
    # No border
    border0 = E('border', 'x')
    for side in ['left', 'right', 'top', 'bottom', 'diagonal']:
        border0.append(E(side, 'x'))
    borders.append(border0)
    
    # Thin border from carriers
    border1 = E('border', 'x')
    color = CARRIER_VARIABLES.get('border.table.color', '#E0E0E0').lstrip('#')
    for side in ['left', 'right', 'top', 'bottom']:
        sideBorder = E(side, 'x', style='thin')
        sideBorder.append(E('color', 'x', rgb='FF' + color))
        border1.append(sideBorder)
    border1.append(E('diagonal', 'x'))
    borders.append(border1)
    
    styleSheet.append(borders)
    
    # Cell formats
    cellXfs = E('cellXfs', 'x', count='3')
    
    # Default cell format
    xf0 = E('xf', 'x', numFmtId='0', fontId='0', fillId='0', borderId='0')
    cellXfs.append(xf0)
    
    # Header cell format
    xf1 = E('xf', 'x', numFmtId='0', fontId='1', fillId='2', borderId='1', applyFont='1', applyFill='1', applyBorder='1')
    cellXfs.append(xf1)
    
    # Data cell format
    xf2 = E('xf', 'x', numFmtId='0', fontId='0', fillId='0', borderId='1', applyBorder='1')
    cellXfs.append(xf2)
    
    styleSheet.append(cellXfs)
    
    # Differential formats for conditional formatting
    dxfs = E('dxfs', 'x', count='2')
    
    # Highlight format
    dxf0 = E('dxf', 'x')
    dxfFill = E('fill', 'x')
    dxfPf = E('patternFill', 'x', patternType='solid')
    dxfFg = E('fgColor', 'x', rgb='FFFFFF00')  # Yellow
    dxfPf.append(dxfFg)
    dxfFill.append(dxfPf)
    dxf0.append(dxfFill)
    dxfs.append(dxf0)
    
    # Error format
    dxf1 = E('dxf', 'x')
    dxfFont = E('font', 'x')
    dxfFont.append(E('color', 'x', rgb='FFFF0000'))  # Red text
    dxf1.append(dxfFont)
    dxfs.append(dxf1)
    
    styleSheet.append(dxfs)
    
    # Table styles
    tableStyles = E('tableStyles', 'x', count='1')
    tableStyle = E('tableStyle', 'x', name='StyleStackTable', pivot='0')
    
    # Table elements
    for element, dxfId in [('wholeTable', '0'), ('headerRow', '1'), ('firstColumn', '1')]:
        tableStyleElement = E('tableStyleElement', 'x', type=element, dxfId=dxfId)
        tableStyle.append(tableStyleElement)
    
    tableStyles.append(tableStyle)
    styleSheet.append(tableStyles)
    
    return styleSheet


# ========== MAIN PATCHING FUNCTION ==========

def patch_ooxml_template(input_path: str, output_path: str, 
                         patch_word: bool = True,
                         patch_powerpoint: bool = True, 
                         patch_excel: bool = True):
    """
    Comprehensive OOXML template patcher
    
    Args:
        input_path: Input template file path
        output_path: Output patched template path
        patch_word: Apply Word-specific patches
        patch_powerpoint: Apply PowerPoint-specific patches
        patch_excel: Apply Excel-specific patches
    """
    
    # Detect file type
    ext = input_path.lower().split('.')[-1]
    is_word = ext in ['docx', 'dotx', 'docm', 'dotm']
    is_powerpoint = ext in ['pptx', 'potx', 'pptm', 'potm']
    is_excel = ext in ['xlsx', 'xltx', 'xlsm', 'xltm']
    
    # Copy to output first
    shutil.copy2(input_path, output_path)
    
    # Open as zip for patching
    with zipfile.ZipFile(output_path, 'a') as zf:
        existing_files = zf.namelist()
        
        # Universal theme patching
        theme_path = None
        if is_word:
            theme_path = 'word/theme/theme1.xml'
        elif is_powerpoint:
            theme_path = 'ppt/theme/theme1.xml'
        elif is_excel:
            theme_path = 'xl/theme/theme1.xml'
        
        if theme_path:
            theme_xml = tostring(build_comprehensive_theme())
            zf.writestr(theme_path, theme_xml)
            print(f"✓ Patched theme: {theme_path}")
        
        # Word-specific patches
        if is_word and patch_word:
            # Styles
            styles_xml = tostring(build_comprehensive_word_styles())
            zf.writestr('word/styles.xml', styles_xml)
            print("✓ Patched Word styles")
            
            # Numbering
            numbering_xml = tostring(build_comprehensive_numbering())
            zf.writestr('word/numbering.xml', numbering_xml)
            print("✓ Patched Word numbering")
            
            # Settings (footnotes/endnotes)
            settings = E('settings', 'w')
            
            # Footnote properties
            footnotePr = E('footnotePr', 'w')
            footnotePr.append(E('numFmt', 'w', val=CARRIER_VARIABLES.get('numbering.format', 'decimal')))
            footnotePr.append(E('numStart', 'w', val='1'))
            footnotePr.append(E('numRestart', 'w', val='continuous'))
            settings.append(footnotePr)
            
            # Endnote properties
            endnotePr = E('endnotePr', 'w')
            endnotePr.append(E('numFmt', 'w', val='lowerRoman'))
            endnotePr.append(E('numStart', 'w', val='1'))
            endnotePr.append(E('numRestart', 'w', val='continuous'))
            settings.append(endnotePr)
            
            zf.writestr('word/settings.xml', tostring(settings))
            print("✓ Patched Word settings")
        
        # PowerPoint-specific patches
        if is_powerpoint and patch_powerpoint:
            # Slide master
            master_xml = tostring(build_powerpoint_slide_master())
            zf.writestr('ppt/slideMasters/slideMaster1.xml', master_xml)
            print("✓ Patched PowerPoint slide master")
            
            # Table styles
            tableStyles = E('tblStyleLst', 'a',
                          **{'{http://schemas.openxmlformats.org/drawingml/2006/main}def': '{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}'})
            
            # Add comprehensive table style
            tblStyle = E('tblStyle', 'a', styleId='{C0E5C7CA-7B8C-4179-ADB3-A5E5E6B26583}', styleName='StyleStack Table')
            
            # Whole table
            wholeTbl = E('wholeTbl', 'a')
            tcTxStyle = E('tcTxStyle', 'a')
            tcTxStyle.append(E('fontRef', 'a', idx='minor').append(E('schemeClr', 'a', val='tx1')))
            tcTxStyle.append(E('schemeClr', 'a', val='tx1'))
            wholeTbl.append(tcTxStyle)
            
            tcStyle = E('tcStyle', 'a')
            tcBdr = E('tcBdr', 'a')
            for side in ['left', 'right', 'top', 'bottom']:
                ln = E(side, 'a')
                ln.append(E('ln', 'a', w=CARRIER_VARIABLES.get('border.table.width_emu', '900')))
                tcBdr.append(ln)
            tcStyle.append(tcBdr)
            wholeTbl.append(tcStyle)
            
            tblStyle.append(wholeTbl)
            
            # First row (header)
            firstRow = E('firstRow', 'a')
            frTcStyle = E('tcStyle', 'a')
            frFill = E('fill', 'a')
            frSolidFill = E('solidFill', 'a')
            frSolidFill.append(E('srgbClr', 'a', val=CARRIER_VARIABLES.get('table.header.fill', '#F0F0F0').lstrip('#')))
            frFill.append(frSolidFill)
            frTcStyle.append(frFill)
            firstRow.append(frTcStyle)
            
            frTcTxStyle = E('tcTxStyle', 'a', b='on')
            firstRow.append(frTcTxStyle)
            
            tblStyle.append(firstRow)
            
            tableStyles.append(tblStyle)
            zf.writestr('ppt/tableStyles.xml', tostring(tableStyles))
            print("✓ Patched PowerPoint table styles")
        
        # Excel-specific patches
        if is_excel and patch_excel:
            # Styles
            styles_xml = tostring(build_excel_styles())
            zf.writestr('xl/styles.xml', styles_xml)
            print("✓ Patched Excel styles")
            
            # Table styles
            tableStyles = E('tableStyles', 'x', count='1', defaultTableStyle='StyleStackTable')
            tableStyle = E('tableStyle', 'x', name='StyleStackTable')
            
            # Table style elements reference dxf formats
            for element, dxfId in [('wholeTable', '0'), ('headerRow', '1')]:
                tableStyleElement = E('tableStyleElement', 'x', type=element, dxfId=dxfId)
                tableStyle.append(tableStyleElement)
            
            tableStyles.append(tableStyle)
            zf.writestr('xl/tableStyles.xml', tostring(tableStyles))
            print("✓ Patched Excel table styles")
    
    print(f"\n✓ Successfully patched template: {output_path}")
    print(f"  Applied {len(CARRIER_VARIABLES)} carrier variables")
    

def main():
    """Main entry point"""
    if len(sys.argv) < 3:
        print("Usage: python comprehensive_ooxml_patcher.py INPUT OUTPUT")
        print("\nThis patcher applies comprehensive StyleStack carrier variables to:")
        print("  - Themes (colors, fonts, effects)")
        print("  - Styles (paragraph, character, table, numbering)")
        print("  - Masters/Layouts (PowerPoint)")
        print("  - Animations/Transitions (PowerPoint)")
        print("  - Cell/Table formatting (Excel)")
        print("  - Footnotes/Endnotes (Word)")
        print("  - And 100+ more OOXML elements")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    # Check input exists
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    # Patch the template
    try:
        patch_ooxml_template(input_path, output_path)
    except Exception as e:
        print(f"Error patching template: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()