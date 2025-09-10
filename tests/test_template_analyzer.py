#!/usr/bin/env python3
"""
StyleStack OOXML Extension Variable System - Template Analyzer Tests

Comprehensive test suite for Phase 3.1: Template Analysis & Variable Extraction.
Tests template analysis, variable coverage calculation, complexity scoring,
and design value discovery in OOXML templates.

Created: 2025-09-07
Author: StyleStack Development Team  
License: MIT
"""

import unittest
import tempfile
import json
import zipfile
from pathlib import Path

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))

from tools.template_analyzer import (
    TemplateAnalyzer,
    TemplateComplexity
)
from tools.analyzer.types import (
    DesignElement,
    VariableCoverage,
    AnalysisResult,
    CoverageReport,
    ComplexityScore,
    DesignElementType,
    AnalysisLevel
)


class TestTemplateAnalyzer(unittest.TestCase):
    """Test suite for Template Analyzer"""
    
    def setUp(self):
        """Set up test environment"""
        self.analyzer = TemplateAnalyzer(
            analysis_level=AnalysisLevel.COMPREHENSIVE,
            target_coverage=100.0,
            enable_complexity_scoring=True
        )
        
        # Sample OOXML template content for testing
        self.sample_ppt_theme = '''<?xml version="1.0"?>
        <a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">
          <a:themeElements>
            <a:clrScheme name="Office">
              <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
              <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
              <a:dk2><a:srgbClr val="44546A"/></a:dk2>
              <a:lt2><a:srgbClr val="E7E6E6"/></a:lt2>
              <a:accent1><a:srgbClr val="4472C4"/></a:accent1>
              <a:accent2><a:srgbClr val="70AD47"/></a:accent2>
              <a:accent3><a:srgbClr val="FFC000"/></a:accent3>
              <a:accent4><a:srgbClr val="ED7D31"/></a:accent4>
              <a:accent5><a:srgbClr val="A5A5A5"/></a:accent5>
              <a:accent6><a:srgbClr val="5B9BD5"/></a:accent6>
              <a:hlink><a:srgbClr val="0563C1"/></a:hlink>
              <a:folHlink><a:srgbClr val="954F72"/></a:folHlink>
            </a:clrScheme>
            <a:fontScheme name="Office">
              <a:majorFont>
                <a:latin typeface="Calibri Light" pitchFamily="34" charset="0"/>
                <a:ea typeface="" pitchFamily="34" charset="0"/>
                <a:cs typeface="" pitchFamily="34" charset="0"/>
              </a:majorFont>
              <a:minorFont>
                <a:latin typeface="Calibri" pitchFamily="34" charset="0"/>
                <a:ea typeface="" pitchFamily="34" charset="0"/>
                <a:cs typeface="" pitchFamily="34" charset="0"/>
              </a:minorFont>
            </a:fontScheme>
            <a:fmtScheme name="Office">
              <a:fillStyleLst>
                <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
                <a:gradFill rotWithShape="1">
                  <a:gsLst>
                    <a:gs pos="0"><a:schemeClr val="phClr"><a:lumMod val="110000"/><a:satMod val="105000"/><a:tint val="67000"/></a:schemeClr></a:gs>
                    <a:gs pos="50000"><a:schemeClr val="phClr"><a:lumMod val="105000"/><a:satMod val="103000"/><a:tint val="73000"/></a:schemeClr></a:gs>
                    <a:gs pos="100000"><a:schemeClr val="phClr"><a:lumMod val="105000"/><a:satMod val="109000"/><a:tint val="81000"/></a:schemeClr></a:gs>
                  </a:gsLst>
                  <a:lin ang="5400000" scaled="0"/>
                </a:gradFill>
                <a:gradFill rotWithShape="1">
                  <a:gsLst>
                    <a:gs pos="0"><a:schemeClr val="phClr"><a:satMod val="103000"/><a:lumMod val="102000"/><a:tint val="94000"/></a:schemeClr></a:gs>
                    <a:gs pos="50000"><a:schemeClr val="phClr"><a:satMod val="110000"/><a:lumMod val="100000"/><a:shade val="100000"/></a:schemeClr></a:gs>
                    <a:gs pos="100000"><a:schemeClr val="phClr"><a:lumMod val="99000"/><a:satMod val="120000"/><a:shade val="78000"/></a:schemeClr></a:gs>
                  </a:gsLst>
                  <a:lin ang="5400000" scaled="0"/>
                </a:gradFill>
              </a:fillStyleLst>
              <a:lnStyleLst>
                <a:ln w="6350" cap="flat" cmpd="sng" algn="ctr">
                  <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
                  <a:prstDash val="solid"/>
                  <a:miter lim="800000"/>
                </a:ln>
                <a:ln w="12700" cap="flat" cmpd="sng" algn="ctr">
                  <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
                  <a:prstDash val="solid"/>
                  <a:miter lim="800000"/>
                </a:ln>
                <a:ln w="19050" cap="flat" cmpd="sng" algn="ctr">
                  <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
                  <a:prstDash val="solid"/>
                  <a:miter lim="800000"/>
                </a:ln>
              </a:lnStyleLst>
              <a:effectStyleLst>
                <a:effectStyle>
                  <a:effectLst/>
                </a:effectStyle>
                <a:effectStyle>
                  <a:effectLst/>
                </a:effectStyle>
                <a:effectStyle>
                  <a:effectLst>
                    <a:outerShdw blurRad="57150" dist="19050" dir="5400000" algn="ctr" rotWithShape="0">
                      <a:srgbClr val="000000"><a:alpha val="63000"/></a:srgbClr>
                    </a:outerShdw>
                  </a:effectLst>
                </a:effectStyle>
              </a:effectStyleLst>
              <a:bgFillStyleLst>
                <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
                <a:solidFill><a:schemeClr val="phClr"><a:tint val="95000"/><a:satMod val="170000"/></a:schemeClr></a:solidFill>
                <a:gradFill rotWithShape="1">
                  <a:gsLst>
                    <a:gs pos="0"><a:schemeClr val="phClr"><a:tint val="93000"/><a:satMod val="150000"/><a:shade val="98000"/><a:lumMod val="102000"/></a:schemeClr></a:gs>
                    <a:gs pos="50000"><a:schemeClr val="phClr"><a:tint val="98000"/><a:satMod val="130000"/><a:shade val="90000"/><a:lumMod val="103000"/></a:schemeClr></a:gs>
                    <a:gs pos="100000"><a:schemeClr val="phClr"><a:shade val="63000"/><a:satMod val="120000"/></a:schemeClr></a:gs>
                  </a:gsLst>
                  <a:lin ang="5400000" scaled="0"/>
                </a:gradFill>
              </a:bgFillStyleLst>
            </a:fmtScheme>
          </a:themeElements>
        </a:theme>'''
        
        self.sample_ppt_slide_master = '''<?xml version="1.0"?>
        <p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
          <p:cSld>
            <p:bg>
              <p:bgRef idx="1001">
                <a:schemeClr val="bg1"/>
              </p:bgRef>
            </p:bg>
            <p:spTree>
              <p:nvGrpSpPr>
                <p:cNvPr id="1" name=""/>
                <p:cNvGrpSpPr/>
                <p:nvPr/>
              </p:nvGrpSpPr>
              <p:grpSpPr>
                <a:xfrm>
                  <a:off x="0" y="0"/>
                  <a:ext cx="0" cy="0"/>
                  <a:chOff x="0" y="0"/>
                  <a:chExt cx="0" cy="0"/>
                </a:xfrm>
              </p:grpSpPr>
              <p:sp>
                <p:nvSpPr>
                  <p:cNvPr id="2" name="Title 1"/>
                  <p:cNvSpPr>
                    <a:spLocks noGrp="1"/>
                  </p:cNvSpPr>
                  <p:nvPr>
                    <p:ph type="title"/>
                  </p:nvPr>
                </p:nvSpPr>
                <p:spPr>
                  <a:xfrm>
                    <a:off x="457200" y="274638"/>
                    <a:ext cx="8229600" cy="1143000"/>
                  </a:xfrm>
                </p:spPr>
                <p:txBody>
                  <a:bodyPr vert="horz" lIns="91440" tIns="45720" rIns="91440" bIns="45720" rtlCol="0" anchor="ctr"/>
                  <a:lstStyle/>
                  <a:p>
                    <a:r>
                      <a:rPr lang="en-US" altLang="ja-JP" sz="4400" b="1" cap="all" spc="-1" kern="1200">
                        <a:solidFill>
                          <a:schemeClr val="tx1"/>
                        </a:solidFill>
                        <a:latin typeface="+mj-lt"/>
                        <a:ea typeface="+mj-ea"/>
                        <a:cs typeface="+mj-cs"/>
                      </a:rPr>
                      <a:t>Click to edit Master title style</a:t>
                    </a:r>
                    <a:endParaRPr lang="en-US" altLang="ja-JP" sz="4400" b="1" cap="all" spc="-1" kern="1200">
                      <a:solidFill>
                        <a:schemeClr val="tx1"/>
                      </a:solidFill>
                      <a:latin typeface="+mj-lt"/>
                      <a:ea typeface="+mj-ea"/>
                      <a:cs typeface="+mj-cs"/>
                    </a:endParaRPr>
                  </a:p>
                </p:txBody>
              </p:sp>
              <p:sp>
                <p:nvSpPr>
                  <p:cNvPr id="3" name="Content Placeholder 2"/>
                  <p:cNvSpPr>
                    <a:spLocks noGrp="1"/>
                  </p:cNvSpPr>
                  <p:nvPr>
                    <p:ph idx="1"/>
                  </p:nvPr>
                </p:nvSpPr>
                <p:spPr>
                  <a:xfrm>
                    <a:off x="457200" y="1600200"/>
                    <a:ext cx="8229600" cy="4525963"/>
                  </a:xfrm>
                </p:spPr>
                <p:txBody>
                  <a:bodyPr vert="horz" lIns="91440" tIns="45720" rIns="91440" bIns="45720" rtlCol="0"/>
                  <a:lstStyle>
                    <a:lvl1pPr marL="342900" algn="l" defTabSz="457200" rtl="0" eaLnBrk="1" latinLnBrk="0" hangingPunct="1">
                      <a:defRPr sz="2400" kern="1200">
                        <a:solidFill>
                          <a:schemeClr val="tx1"/>
                        </a:solidFill>
                        <a:latin typeface="+mn-lt"/>
                        <a:ea typeface="+mn-ea"/>
                        <a:cs typeface="+mn-cs"/>
                      </a:defRPr>
                    </a:lvl1pPr>
                  </a:lstStyle>
                  <a:p>
                    <a:pPr lvl="0"/>
                    <a:r>
                      <a:rPr lang="en-US" altLang="ja-JP" sz="2400" kern="1200">
                        <a:solidFill>
                          <a:schemeClr val="tx1"/>
                        </a:solidFill>
                        <a:latin typeface="+mn-lt"/>
                        <a:ea typeface="+mn-ea"/>
                        <a:cs typeface="+mn-cs"/>
                      </a:rPr>
                      <a:t>Click to edit Master text styles</a:t>
                    </a:r>
                  </a:p>
                </p:txBody>
              </p:sp>
            </p:spTree>
          </p:cSld>
          <p:clrMapOvr>
            <a:masterClrMapping/>
          </p:clrMapOvr>
        </p:sldMaster>'''
        
        self.sample_word_styles = '''<?xml version="1.0"?>
        <w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:docDefaults>
            <w:rPrDefault>
              <w:rPr>
                <w:rFonts w:asciiTheme="minorHAnsi" w:eastAsiaTheme="minorEastAsia" w:hAnsiTheme="minorHAnsi" w:cstheme="minorBidi"/>
                <w:sz w:val="22"/>
                <w:szCs w:val="22"/>
                <w:lang w:val="en-US" w:eastAsia="en-US" w:bidi="ar-SA"/>
              </w:rPr>
            </w:rPrDefault>
            <w:pPrDefault>
              <w:pPr>
                <w:spacing w:after="160" w:line="259" w:lineRule="auto"/>
              </w:pPr>
            </w:pPrDefault>
          </w:docDefaults>
          <w:latentStyles w:defLockedState="0" w:defUIPriority="99" w:defSemiHidden="1" w:defUnhideWhenUsed="1" w:defQFormat="0" w:count="371">
            <w:lsdException w:name="Normal" w:semiHidden="0" w:uiPriority="0" w:unhideWhenUsed="0" w:qFormat="1"/>
            <w:lsdException w:name="heading 1" w:semiHidden="0" w:uiPriority="9" w:unhideWhenUsed="0" w:qFormat="1"/>
            <w:lsdException w:name="heading 2" w:uiPriority="9" w:qFormat="1"/>
            <w:lsdException w:name="heading 3" w:uiPriority="9" w:qFormat="1"/>
          </w:latentStyles>
          <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
            <w:name w:val="Normal"/>
            <w:qFormat/>
          </w:style>
          <w:style w:type="character" w:default="1" w:styleId="DefaultParagraphFont">
            <w:name w:val="Default Paragraph Font"/>
            <w:uiPriority w:val="1"/>
            <w:semiHidden/>
            <w:unhideWhenUsed/>
          </w:style>
          <w:style w:type="table" w:default="1" w:styleId="TableNormal">
            <w:name w:val="Normal Table"/>
            <w:uiPriority w:val="99"/>
            <w:semiHidden/>
            <w:unhideWhenUsed/>
            <w:tblPr>
              <w:tblInd w:w="0" w:type="dxa"/>
              <w:tblCellMar>
                <w:top w:w="0" w:type="dxa"/>
                <w:left w:w="108" w:type="dxa"/>
                <w:bottom w:w="0" w:type="dxa"/>
                <w:right w:w="108" w:type="dxa"/>
              </w:tblCellMar>
            </w:tblPr>
          </w:style>
          <w:style w:type="numbering" w:default="1" w:styleId="NoList">
            <w:name w:val="No List"/>
            <w:uiPriority w:val="99"/>
            <w:semiHidden/>
            <w:unhideWhenUsed/>
          </w:style>
          <w:style w:type="paragraph" w:styleId="Heading1">
            <w:name w:val="heading 1"/>
            <w:basedOn w:val="Normal"/>
            <w:next w:val="Normal"/>
            <w:link w:val="Heading1Char"/>
            <w:uiPriority w:val="9"/>
            <w:qFormat/>
            <w:rsid w:val="00E73907"/>
            <w:pPr>
              <w:keepNext/>
              <w:keepLines/>
              <w:spacing w:before="240" w:after="0" w:line="259" w:lineRule="auto"/>
              <w:outlineLvl w:val="0"/>
            </w:pPr>
            <w:rPr>
              <w:rFonts w:asciiTheme="majorHAnsi" w:eastAsiaTheme="majorEastAsia" w:hAnsiTheme="majorHAnsi" w:cstheme="majorBidi"/>
              <w:color w:val="2F5496" w:themeColor="accent1" w:themeShade="BF"/>
              <w:sz w:val="32"/>
              <w:szCs w:val="32"/>
            </w:rPr>
          </w:style>
          <w:style w:type="character" w:customStyle="1" w:styleId="Heading1Char">
            <w:name w:val="Heading 1 Char"/>
            <w:basedOn w:val="DefaultParagraphFont"/>
            <w:link w:val="Heading1"/>
            <w:uiPriority w:val="9"/>
            <w:rsid w:val="00E73907"/>
            <w:rPr>
              <w:rFonts w:asciiTheme="majorHAnsi" w:eastAsiaTheme="majorEastAsia" w:hAnsiTheme="majorHAnsi" w:cstheme="majorBidi"/>
              <w:color w:val="2F5496" w:themeColor="accent1" w:themeShade="BF"/>
              <w:sz w:val="32"/>
              <w:szCs w:val="32"/>
            </w:rPr>
          </w:style>
        </w:styles>'''
        
        self.sample_excel_styles = '''<?xml version="1.0"?>
        <styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
          <fonts count="2">
            <font>
              <sz val="11"/>
              <color theme="1"/>
              <name val="Calibri"/>
              <family val="2"/>
              <scheme val="minor"/>
            </font>
            <font>
              <sz val="11"/>
              <color theme="1"/>
              <name val="Calibri"/>
              <family val="2"/>
              <scheme val="minor"/>
              <b/>
            </font>
          </fonts>
          <fills count="3">
            <fill>
              <patternFill patternType="none"/>
            </fill>
            <fill>
              <patternFill patternType="gray125"/>
            </fill>
            <fill>
              <patternFill patternType="solid">
                <fgColor theme="4"/>
                <bgColor indexed="64"/>
              </patternFill>
            </fill>
          </fills>
          <borders count="2">
            <border>
              <left/>
              <right/>
              <top/>
              <bottom/>
              <diagonal/>
            </border>
            <border>
              <left style="thin">
                <color indexed="64"/>
              </left>
              <right style="thin">
                <color indexed="64"/>
              </right>
              <top style="thin">
                <color indexed="64"/>
              </top>
              <bottom style="thin">
                <color indexed="64"/>
              </bottom>
              <diagonal/>
            </border>
          </borders>
          <cellStyleXfs count="1">
            <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
          </cellStyleXfs>
          <cellXfs count="4">
            <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
            <xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>
            <xf numFmtId="0" fontId="0" fillId="2" borderId="0" xfId="0" applyFill="1"/>
            <xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"/>
          </cellXfs>
          <cellStyles count="1">
            <cellStyle name="Normal" xfId="0" builtinId="0"/>
          </cellStyles>
          <dxfs count="0"/>
          <tableStyles count="0" defaultTableStyle="TableStyleMedium2" defaultPivotStyle="PivotStyleLight16"/>
          <extLst>
            <ext uri="{EB79DEF2-80B8-43e5-95BD-54CBDDF9020C}" xmlns:x14="http://schemas.microsoft.com/office/spreadsheetml/2009/9/main">
              <x14:slicerStyles defaultSlicerStyle="SlicerStyleLight1"/>
            </ext>
            <ext uri="{9260A510-F301-46a8-8635-F512D64BE5F5}" xmlns:x15="http://schemas.microsoft.com/office/spreadsheetml/2010/11/main">
              <x15:timelineStyles defaultTimelineStyle="TimeSlicerStyleLight1"/>
            </ext>
          </extLst>
        </styleSheet>'''


class TestDesignElementDiscovery(TestTemplateAnalyzer):
    """Test discovery of all customizable design elements"""
    
    def test_color_element_discovery_powerpoint(self):
        """Test discovery of color elements in PowerPoint themes"""
        analysis_result = self.analyzer.analyze_template_content(
            content=self.sample_ppt_theme,
            template_type='powerpoint_theme',
            file_name='theme1.xml'
        )
        
        self.assertTrue(analysis_result.success)
        
        # Should find all theme colors
        color_elements = [elem for elem in analysis_result.design_elements 
                         if elem.element_type == DesignElementType.COLOR]
        
        expected_colors = ['dk1', 'lt1', 'dk2', 'lt2', 'accent1', 'accent2', 
                          'accent3', 'accent4', 'accent5', 'accent6', 'hlink', 'folHlink']
        
        found_color_names = [elem.semantic_name for elem in color_elements]
        
        for expected in expected_colors:
            self.assertIn(expected, found_color_names)
            
        self.assertGreaterEqual(len(color_elements), 12)  # At least 12 theme colors
        print(f"✅ PowerPoint color discovery: found {len(color_elements)} color elements")

    def test_font_element_discovery_powerpoint(self):
        """Test discovery of font elements in PowerPoint themes"""
        analysis_result = self.analyzer.analyze_template_content(
            content=self.sample_ppt_theme,
            template_type='powerpoint_theme',
            file_name='theme1.xml'
        )
        
        font_elements = [elem for elem in analysis_result.design_elements 
                        if elem.element_type == DesignElementType.FONT]
        
        # Should find major and minor fonts
        font_categories = [elem.semantic_name for elem in font_elements]
        self.assertIn('majorFont', font_categories)
        self.assertIn('minorFont', font_categories)
        
        # Check font details
        major_font = next((elem for elem in font_elements if elem.semantic_name == 'majorFont'), None)
        self.assertIsNotNone(major_font)
        self.assertIn('Calibri Light', major_font.current_value)
        
        print(f"✅ PowerPoint font discovery: found {len(font_elements)} font elements")

    def test_gradient_element_discovery(self):
        """Test discovery of gradient fill elements"""
        analysis_result = self.analyzer.analyze_template_content(
            content=self.sample_ppt_theme,
            template_type='powerpoint_theme',
            file_name='theme1.xml'
        )
        
        gradient_elements = [elem for elem in analysis_result.design_elements 
                           if elem.element_type == DesignElementType.GRADIENT]
        
        self.assertGreater(len(gradient_elements), 0)
        
        # Check gradient properties
        first_gradient = gradient_elements[0]
        self.assertIsNotNone(first_gradient.xpath_expression)
        self.assertIn('gradFill', first_gradient.xpath_expression)
        
        print(f"✅ Gradient discovery: found {len(gradient_elements)} gradient elements")

    def test_effect_element_discovery(self):
        """Test discovery of effect style elements"""
        analysis_result = self.analyzer.analyze_template_content(
            content=self.sample_ppt_theme,
            template_type='powerpoint_theme',
            file_name='theme1.xml'
        )
        
        effect_elements = [elem for elem in analysis_result.design_elements 
                         if elem.element_type == DesignElementType.EFFECT]
        
        self.assertGreater(len(effect_elements), 0)
        
        # Should find shadow effects
        shadow_effects = [elem for elem in effect_elements 
                         if 'shadow' in elem.semantic_name.lower()]
        self.assertGreater(len(shadow_effects), 0)
        
        print(f"✅ Effect discovery: found {len(effect_elements)} effect elements")

    def test_slide_master_element_discovery(self):
        """Test discovery of elements in slide masters"""
        analysis_result = self.analyzer.analyze_template_content(
            content=self.sample_ppt_slide_master,
            template_type='powerpoint_slide_master',
            file_name='slideMaster1.xml'
        )
        
        self.assertTrue(analysis_result.success)
        
        # Should find text formatting elements
        text_elements = [elem for elem in analysis_result.design_elements 
                        if elem.element_type == DesignElementType.TEXT_FORMAT]
        
        self.assertGreater(len(text_elements), 0)
        
        # Should find size/dimension elements
        dimension_elements = [elem for elem in analysis_result.design_elements 
                            if elem.element_type == DesignElementType.DIMENSION]
        
        self.assertGreater(len(dimension_elements), 0)
        
        print(f"✅ Slide master discovery: found {len(analysis_result.design_elements)} total elements")

    def test_word_style_element_discovery(self):
        """Test discovery of elements in Word styles"""
        analysis_result = self.analyzer.analyze_template_content(
            content=self.sample_word_styles,
            template_type='word_styles',
            file_name='styles.xml'
        )
        
        self.assertTrue(analysis_result.success)
        
        # Should find style definitions
        style_elements = [elem for elem in analysis_result.design_elements 
                         if 'style' in elem.semantic_name.lower()]
        
        self.assertGreater(len(style_elements), 0)
        
        # Should find color elements
        color_elements = [elem for elem in analysis_result.design_elements 
                         if elem.element_type == DesignElementType.COLOR]
        
        self.assertGreater(len(color_elements), 0)
        
        # Check for heading styles
        heading_elements = [elem for elem in analysis_result.design_elements 
                          if 'heading' in elem.semantic_name.lower()]
        
        self.assertGreater(len(heading_elements), 0)
        
        print(f"✅ Word styles discovery: found {len(analysis_result.design_elements)} total elements")

    def test_excel_style_element_discovery(self):
        """Test discovery of elements in Excel styles"""
        analysis_result = self.analyzer.analyze_template_content(
            content=self.sample_excel_styles,
            template_type='excel_styles',
            file_name='styles.xml'
        )
        
        self.assertTrue(analysis_result.success)
        
        # Should find font definitions
        font_elements = [elem for elem in analysis_result.design_elements 
                        if elem.element_type == DesignElementType.FONT]
        
        self.assertGreater(len(font_elements), 0)
        
        # Should find fill patterns
        fill_elements = [elem for elem in analysis_result.design_elements 
                        if elem.element_type == DesignElementType.FILL]
        
        self.assertGreater(len(fill_elements), 0)
        
        # Should find border styles
        border_elements = [elem for elem in analysis_result.design_elements 
                          if elem.element_type == DesignElementType.BORDER]
        
        self.assertGreater(len(border_elements), 0)
        
        print(f"✅ Excel styles discovery: found {len(analysis_result.design_elements)} total elements")


class TestVariableCoverageCalculation(TestTemplateAnalyzer):
    """Test variable coverage calculation and reporting"""
    
    def test_coverage_calculation_basic(self):
        """Test basic variable coverage calculation"""
        # Mock design elements
        design_elements = [
            DesignElement(
                id='theme_accent1',
                element_type=DesignElementType.COLOR,
                semantic_name='accent1',
                current_value='4472C4',
                xpath_expression='//a:accent1//a:srgbClr/@val',
                is_customizable=True,
                file_location='theme1.xml'
            ),
            DesignElement(
                id='theme_accent2',
                element_type=DesignElementType.COLOR,
                semantic_name='accent2', 
                current_value='70AD47',
                xpath_expression='//a:accent2//a:srgbClr/@val',
                is_customizable=True,
                file_location='theme1.xml'
            ),
            DesignElement(
                id='major_font',
                element_type=DesignElementType.FONT,
                semantic_name='majorFont',
                current_value='Calibri Light',
                xpath_expression='//a:majorFont//a:latin/@typeface',
                is_customizable=True,
                file_location='theme1.xml'
            )
        ]
        
        # Mock variables that cover some elements
        existing_variables = [
            {
                'id': 'brandPrimary',
                'type': 'color',
                'xpath': '//a:accent1//a:srgbClr/@val',
                'targets': ['theme_accent1']
            }
        ]
        
        coverage = self.analyzer.calculate_variable_coverage(
            design_elements=design_elements,
            existing_variables=existing_variables
        )
        
        self.assertIsInstance(coverage, VariableCoverage)
        self.assertEqual(coverage.total_elements, 3)
        self.assertEqual(coverage.covered_elements, 1)
        self.assertAlmostEqual(coverage.coverage_percentage, 33.33, places=2)
        
        print(f"✅ Basic coverage calculation: {coverage.coverage_percentage:.1f}% coverage")

    def test_coverage_by_element_type(self):
        """Test coverage calculation broken down by element type"""
        design_elements = [
            DesignElement(
                id='color1', element_type=DesignElementType.COLOR,
                semantic_name='accent1', current_value='4472C4',
                xpath_expression='//a:accent1', is_customizable=True
            ),
            DesignElement(
                id='color2', element_type=DesignElementType.COLOR,
                semantic_name='accent2', current_value='70AD47',
                xpath_expression='//a:accent2', is_customizable=True
            ),
            DesignElement(
                id='font1', element_type=DesignElementType.FONT,
                semantic_name='majorFont', current_value='Calibri',
                xpath_expression='//a:majorFont', is_customizable=True
            )
        ]
        
        existing_variables = [
            {
                'id': 'brandColor1',
                'type': 'color',
                'xpath': '//a:accent1',
                'targets': ['color1']
            },
            {
                'id': 'brandColor2',
                'type': 'color',
                'xpath': '//a:accent2', 
                'targets': ['color2']
            }
        ]
        
        coverage = self.analyzer.calculate_variable_coverage(
            design_elements=design_elements,
            existing_variables=existing_variables
        )
        
        # Check type-specific coverage
        self.assertIn(DesignElementType.COLOR, coverage.coverage_by_type)
        self.assertIn(DesignElementType.FONT, coverage.coverage_by_type)
        
        color_coverage = coverage.coverage_by_type[DesignElementType.COLOR]
        self.assertEqual(color_coverage['covered'], 2)
        self.assertEqual(color_coverage['total'], 2)
        self.assertEqual(color_coverage['percentage'], 100.0)
        
        font_coverage = coverage.coverage_by_type[DesignElementType.FONT]
        self.assertEqual(font_coverage['covered'], 0)
        self.assertEqual(font_coverage['total'], 1)
        self.assertEqual(font_coverage['percentage'], 0.0)
        
        print(f"✅ Coverage by type: Colors {color_coverage['percentage']:.0f}%, Fonts {font_coverage['percentage']:.0f}%")

    def test_coverage_report_generation(self):
        """Test comprehensive coverage report generation"""
        analysis_result = self.analyzer.analyze_template_content(
            content=self.sample_ppt_theme,
            template_type='powerpoint_theme',
            file_name='theme1.xml'
        )
        
        # Generate coverage report
        coverage_report = self.analyzer.generate_coverage_report(
            analysis_result=analysis_result,
            existing_variables=[],  # No existing variables
            target_coverage=100.0
        )
        
        self.assertIsInstance(coverage_report, CoverageReport)
        self.assertGreater(coverage_report.total_elements, 0)
        self.assertEqual(coverage_report.covered_elements, 0)  # No variables provided
        self.assertEqual(coverage_report.coverage_percentage, 0.0)
        
        # Should have recommendations for improvement
        self.assertGreater(len(coverage_report.recommended_variables), 0)
        
        # Should identify uncovered elements
        self.assertGreater(len(coverage_report.uncovered_elements), 0)
        
        print(f"✅ Coverage report: {len(coverage_report.recommended_variables)} variable recommendations")

    def test_coverage_gap_analysis(self):
        """Test identification of coverage gaps and recommendations"""
        # Create mixed coverage scenario
        design_elements = [
            DesignElement(
                id='critical_color',
                element_type=DesignElementType.COLOR,
                semantic_name='accent1',
                current_value='4472C4',
                xpath_expression='//a:accent1',
                is_customizable=True,
                priority_score=10  # High priority
            ),
            DesignElement(
                id='secondary_color',
                element_type=DesignElementType.COLOR,
                semantic_name='accent2',
                current_value='70AD47',
                xpath_expression='//a:accent2',
                is_customizable=True,
                priority_score=8
            ),
            DesignElement(
                id='decorative_element',
                element_type=DesignElementType.EFFECT,
                semantic_name='shadow',
                current_value='outerShdw',
                xpath_expression='//a:outerShdw',
                is_customizable=True,
                priority_score=3  # Low priority
            )
        ]
        
        partial_variables = [
            {
                'id': 'primaryBrand',
                'type': 'color',
                'xpath': '//a:accent1',
                'targets': ['critical_color']
            }
        ]
        
        coverage = self.analyzer.calculate_variable_coverage(
            design_elements=design_elements,
            existing_variables=partial_variables
        )
        
        # Should identify high-priority gaps
        high_priority_gaps = [elem for elem in coverage.uncovered_elements 
                             if elem.priority_score >= 8]
        
        self.assertGreater(len(high_priority_gaps), 0)
        
        # Should prioritize recommendations
        recommendations = coverage.get_prioritized_recommendations()
        self.assertGreater(len(recommendations), 0)
        
        # Higher priority elements should come first
        if len(recommendations) > 1:
            self.assertGreaterEqual(recommendations[0]['priority'], recommendations[1]['priority'])
            
        print(f"✅ Gap analysis: {len(high_priority_gaps)} high-priority gaps identified")

    def test_template_completeness_scoring(self):
        """Test overall template completeness scoring"""
        analysis_result = self.analyzer.analyze_template_content(
            content=self.sample_ppt_theme,
            template_type='powerpoint_theme',
            file_name='theme1.xml'
        )
        
        # Test with no variables (0% coverage)
        completeness_score = self.analyzer.calculate_template_completeness(
            analysis_result=analysis_result,
            existing_variables=[]
        )
        
        self.assertEqual(completeness_score['coverage_score'], 0.0)
        self.assertIn('element_diversity_score', completeness_score)
        self.assertIn('customization_potential_score', completeness_score)
        self.assertIn('overall_completeness', completeness_score)
        
        # Test with full coverage
        mock_complete_variables = []
        for elem in analysis_result.design_elements:
            if elem.is_customizable:
                mock_complete_variables.append({
                    'id': f'var_{elem.id}',
                    'type': elem.element_type.value,
                    'xpath': elem.xpath_expression,
                    'targets': [elem.id]
                })
                
        completeness_score = self.analyzer.calculate_template_completeness(
            analysis_result=analysis_result,
            existing_variables=mock_complete_variables
        )
        
        self.assertEqual(completeness_score['coverage_score'], 100.0)
        self.assertGreater(completeness_score['overall_completeness'], 80.0)
        
        print(f"✅ Completeness scoring: {completeness_score['overall_completeness']:.1f}% overall completeness")


class TestTemplateComplexityAnalysis(TestTemplateAnalyzer):
    """Test template complexity analysis and scoring"""
    
    def test_basic_complexity_scoring(self):
        """Test basic complexity scoring calculation"""
        analysis_result = self.analyzer.analyze_template_content(
            content=self.sample_ppt_theme,
            template_type='powerpoint_theme',
            file_name='theme1.xml'
        )
        
        complexity = self.analyzer.calculate_template_complexity(analysis_result)
        
        self.assertIsInstance(complexity, ComplexityScore)
        self.assertGreater(complexity.total_elements, 0)
        self.assertGreater(complexity.customizable_elements, 0)
        self.assertGreaterEqual(complexity.complexity_score, 0.0)
        self.assertLessEqual(complexity.complexity_score, 10.0)
        
        print(f"✅ Basic complexity: {complexity.complexity_score:.2f}/10.0 complexity score")

    def test_complexity_factors(self):
        """Test individual complexity factors"""
        analysis_result = self.analyzer.analyze_template_content(
            content=self.sample_ppt_theme,
            template_type='powerpoint_theme',
            file_name='theme1.xml'
        )
        
        complexity = self.analyzer.calculate_template_complexity(analysis_result)
        
        # Check individual factors
        self.assertIn('element_count_factor', complexity.factors)
        self.assertIn('element_diversity_factor', complexity.factors)
        self.assertIn('customization_depth_factor', complexity.factors)
        self.assertIn('relationship_complexity_factor', complexity.factors)
        
        # All factors should be between 0 and 1
        for factor_name, factor_value in complexity.factors.items():
            self.assertGreaterEqual(factor_value, 0.0, f"{factor_name} should be >= 0")
            self.assertLessEqual(factor_value, 1.0, f"{factor_name} should be <= 1")
            
        print(f"✅ Complexity factors: {len(complexity.factors)} factors calculated")

    def test_complexity_comparison(self):
        """Test complexity comparison across different template types"""
        # Analyze PowerPoint theme (complex)
        ppt_analysis = self.analyzer.analyze_template_content(
            content=self.sample_ppt_theme,
            template_type='powerpoint_theme',
            file_name='theme1.xml'
        )
        ppt_complexity = self.analyzer.calculate_template_complexity(ppt_analysis)
        
        # Analyze Word styles (moderate complexity)
        word_analysis = self.analyzer.analyze_template_content(
            content=self.sample_word_styles,
            template_type='word_styles',
            file_name='styles.xml'
        )
        word_complexity = self.analyzer.calculate_template_complexity(word_analysis)
        
        # PowerPoint themes are typically more complex than Word styles
        self.assertGreater(ppt_complexity.total_elements, word_complexity.total_elements)
        
        print(f"✅ Complexity comparison: PPT {ppt_complexity.complexity_score:.2f} vs Word {word_complexity.complexity_score:.2f}")

    def test_complexity_categories(self):
        """Test complexity categorization (Simple/Moderate/Complex/Expert)"""
        analysis_result = self.analyzer.analyze_template_content(
            content=self.sample_ppt_theme,
            template_type='powerpoint_theme',
            file_name='theme1.xml'
        )
        
        complexity = self.analyzer.calculate_template_complexity(analysis_result)
        
        # Should have a category assignment
        self.assertIn('category', complexity.metadata)
        category = complexity.metadata['category']
        
        valid_categories = ['Simple', 'Moderate', 'Complex', 'Expert']
        self.assertIn(category, valid_categories)
        
        # Category should match score range
        if complexity.complexity_score < 3.0:
            expected_category = 'Simple'
        elif complexity.complexity_score < 6.0:
            expected_category = 'Moderate'
        elif complexity.complexity_score < 8.5:
            expected_category = 'Complex'
        else:
            expected_category = 'Expert'
            
        self.assertEqual(category, expected_category)
        
        print(f"✅ Complexity category: {category} ({complexity.complexity_score:.2f}/10.0)")

    def test_customization_impact_analysis(self):
        """Test analysis of customization impact on template complexity"""
        analysis_result = self.analyzer.analyze_template_content(
            content=self.sample_ppt_theme,
            template_type='powerpoint_theme',
            file_name='theme1.xml'
        )
        
        # Calculate impact of different customization scenarios
        impact_analysis = self.analyzer.analyze_customization_impact(
            analysis_result=analysis_result,
            customization_scenarios=[
                {'name': 'Colors Only', 'element_types': [DesignElementType.COLOR]},
                {'name': 'Fonts Only', 'element_types': [DesignElementType.FONT]},
                {'name': 'Colors + Fonts', 'element_types': [DesignElementType.COLOR, DesignElementType.FONT]},
                {'name': 'Full Customization', 'element_types': list(DesignElementType)}
            ]
        )
        
        self.assertGreater(len(impact_analysis), 0)
        
        # Verify impact scores make sense
        for scenario in impact_analysis:
            self.assertIn('name', scenario)
            self.assertIn('elements_affected', scenario)
            self.assertIn('complexity_increase', scenario)
            self.assertIn('recommended_skill_level', scenario)
            
        print(f"✅ Customization impact: analyzed {len(impact_analysis)} scenarios")


class TestMicrosoftTemplateValidation(TestTemplateAnalyzer):
    """Test validation against Microsoft template patterns"""
    
    def test_office_theme_compliance(self):
        """Test compliance with Office theme structure"""
        analysis_result = self.analyzer.analyze_template_content(
            content=self.sample_ppt_theme,
            template_type='powerpoint_theme',
            file_name='theme1.xml'
        )
        
        # Check for required Office theme elements
        validation_result = self.analyzer.validate_office_compliance(analysis_result)
        
        self.assertTrue(validation_result['is_compliant'])
        self.assertIn('required_elements_present', validation_result)
        self.assertIn('structure_valid', validation_result)
        
        # Should have all required theme color slots
        color_elements = [elem for elem in analysis_result.design_elements 
                         if elem.element_type == DesignElementType.COLOR]
        
        required_theme_colors = ['dk1', 'lt1', 'dk2', 'lt2', 'accent1', 'accent2', 
                               'accent3', 'accent4', 'accent5', 'accent6', 'hlink', 'folHlink']
        
        found_colors = [elem.semantic_name for elem in color_elements]
        
        for required_color in required_theme_colors:
            self.assertIn(required_color, found_colors)
            
        print(f"✅ Office compliance: {len(required_theme_colors)} required theme colors found")

    def test_accessibility_compliance_check(self):
        """Test accessibility compliance validation"""
        analysis_result = self.analyzer.analyze_template_content(
            content=self.sample_ppt_theme,
            template_type='powerpoint_theme',
            file_name='theme1.xml'
        )
        
        accessibility_check = self.analyzer.validate_accessibility_compliance(analysis_result)
        
        self.assertIn('contrast_ratios', accessibility_check)
        self.assertIn('color_blind_friendly', accessibility_check)
        self.assertIn('font_readability', accessibility_check)
        self.assertIn('overall_accessibility_score', accessibility_check)
        
        # Should identify potential accessibility issues
        if accessibility_check['issues']:
            self.assertIsInstance(accessibility_check['issues'], list)
            
        print(f"✅ Accessibility check: {accessibility_check['overall_accessibility_score']:.1f}/10.0 score")

    def test_cross_platform_compatibility(self):
        """Test cross-platform compatibility validation"""
        analysis_result = self.analyzer.analyze_template_content(
            content=self.sample_ppt_theme,
            template_type='powerpoint_theme',
            file_name='theme1.xml'
        )
        
        compatibility_check = self.analyzer.validate_cross_platform_compatibility(analysis_result)
        
        self.assertIn('office_versions', compatibility_check)
        self.assertIn('libreoffice_compatible', compatibility_check)
        self.assertIn('google_workspace_compatible', compatibility_check)
        self.assertIn('web_compatible', compatibility_check)
        
        # Should provide specific compatibility ratings
        for platform, rating in compatibility_check['office_versions'].items():
            self.assertIn(rating, ['Full', 'Partial', 'Limited', 'Not Supported'])
            
        print(f"✅ Cross-platform compatibility: {len(compatibility_check['office_versions'])} platforms checked")

    def test_template_best_practices(self):
        """Test validation against template design best practices"""
        analysis_result = self.analyzer.analyze_template_content(
            content=self.sample_ppt_theme,
            template_type='powerpoint_theme',
            file_name='theme1.xml'
        )
        
        best_practices_check = self.analyzer.validate_best_practices(analysis_result)
        
        self.assertIn('design_consistency', best_practices_check)
        self.assertIn('customization_friendliness', best_practices_check)
        self.assertIn('performance_impact', best_practices_check)
        self.assertIn('maintainability', best_practices_check)
        
        # Should provide actionable recommendations
        if 'recommendations' in best_practices_check:
            for recommendation in best_practices_check['recommendations']:
                self.assertIn('category', recommendation)
                self.assertIn('message', recommendation)
                self.assertIn('priority', recommendation)
                
        print(f"✅ Best practices: {len(best_practices_check.get('recommendations', []))} recommendations")


class TestFullTemplateAnalysis(TestTemplateAnalyzer):
    """Test complete template analysis workflows"""
    
    def test_complete_powerpoint_template_analysis(self):
        """Test complete analysis of a PowerPoint template"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock .potx file
            potx_path = Path(temp_dir) / 'test_template.potx'
            
            with zipfile.ZipFile(potx_path, 'w') as zf:
                zf.writestr('ppt/theme/theme1.xml', self.sample_ppt_theme)
                zf.writestr('ppt/slideMasters/slideMaster1.xml', self.sample_ppt_slide_master)
                zf.writestr('[Content_Types].xml', '''<?xml version="1.0"?>
                <Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
                  <Default Extension="xml" ContentType="application/xml"/>
                  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
                </Types>''')
                
            # Analyze complete template
            complete_analysis = self.analyzer.analyze_complete_template(str(potx_path))
            
            self.assertTrue(complete_analysis.success)
            self.assertGreater(len(complete_analysis.files_analyzed), 0)
            self.assertGreater(len(complete_analysis.design_elements), 0)
            
            # Should have coverage analysis
            self.assertIsNotNone(complete_analysis.coverage_analysis)
            
            # Should have complexity analysis
            self.assertIsNotNone(complete_analysis.complexity_analysis)
            
            print(f"✅ Complete PowerPoint analysis: {len(complete_analysis.design_elements)} elements across {len(complete_analysis.files_analyzed)} files")

    def test_template_comparison_analysis(self):
        """Test comparison analysis between templates"""
        # Create two different templates for comparison
        template1_analysis = self.analyzer.analyze_template_content(
            content=self.sample_ppt_theme,
            template_type='powerpoint_theme',
            file_name='theme1.xml'
        )
        
        # Create modified theme for comparison
        modified_theme = self.sample_ppt_theme.replace('4472C4', 'FF0000').replace('Calibri Light', 'Arial Black')
        template2_analysis = self.analyzer.analyze_template_content(
            content=modified_theme,
            template_type='powerpoint_theme',
            file_name='theme1_modified.xml'
        )
        
        # Perform comparison
        comparison_result = self.analyzer.compare_templates(
            template1_analysis, 
            template2_analysis,
            comparison_name='Original vs Modified'
        )
        
        self.assertIn('differences', comparison_result)
        self.assertIn('similarities', comparison_result)
        self.assertIn('complexity_comparison', comparison_result)
        self.assertIn('customization_recommendations', comparison_result)
        
        # Should detect the color and font changes
        differences = comparison_result['differences']
        self.assertGreater(len(differences), 0)
        
        print(f"✅ Template comparison: found {len(differences)} differences")

    def test_variable_recommendation_generation(self):
        """Test automatic variable recommendation generation"""
        analysis_result = self.analyzer.analyze_template_content(
            content=self.sample_ppt_theme,
            template_type='powerpoint_theme',
            file_name='theme1.xml'
        )
        
        # Generate variable recommendations
        recommendations = self.analyzer.generate_variable_recommendations(
            analysis_result=analysis_result,
            target_coverage=95.0,
            prioritize_by=['usage_frequency', 'customization_impact', 'brand_relevance']
        )
        
        self.assertGreater(len(recommendations), 0)
        
        # Check recommendation structure
        for recommendation in recommendations:
            self.assertIn('variable_id', recommendation)
            self.assertIn('variable_type', recommendation)
            self.assertIn('xpath_expression', recommendation)
            self.assertIn('semantic_name', recommendation)
            self.assertIn('priority_score', recommendation)
            self.assertIn('rationale', recommendation)
            
        # Should prioritize high-impact elements
        high_priority_recs = [rec for rec in recommendations if rec['priority_score'] >= 8.0]
        self.assertGreater(len(high_priority_recs), 0)
        
        print(f"✅ Variable recommendations: {len(recommendations)} total, {len(high_priority_recs)} high-priority")

    def test_100_percent_coverage_analysis(self):
        """Test achieving 100% variable coverage analysis"""
        analysis_result = self.analyzer.analyze_template_content(
            content=self.sample_ppt_theme,
            template_type='powerpoint_theme',
            file_name='theme1.xml'
        )
        
        # Generate complete variable set for 100% coverage
        complete_variable_set = self.analyzer.generate_complete_variable_set(
            analysis_result=analysis_result,
            naming_convention='stylestack_v1',
            include_low_priority=True
        )
        
        self.assertGreater(len(complete_variable_set), 0)
        
        # Verify 100% coverage
        coverage = self.analyzer.calculate_variable_coverage(
            design_elements=analysis_result.design_elements,
            existing_variables=complete_variable_set
        )
        
        # Should achieve or be very close to 100% coverage
        self.assertGreaterEqual(coverage.coverage_percentage, 95.0)
        
        # Verify all customizable elements are covered
        customizable_elements = [elem for elem in analysis_result.design_elements if elem.is_customizable]
        covered_element_ids = set()
        for var in complete_variable_set:
            covered_element_ids.update(var.get('targets', []))
            
        customizable_element_ids = {elem.id for elem in customizable_elements}
        uncovered_elements = customizable_element_ids - covered_element_ids
        
        # Should have minimal uncovered elements
        self.assertLessEqual(len(uncovered_elements), len(customizable_elements) * 0.05)  # Allow 5% uncovered
        
        print(f"✅ 100% coverage analysis: {coverage.coverage_percentage:.1f}% coverage with {len(complete_variable_set)} variables")


if __name__ == '__main__':
    # Configure test runner
    unittest.main(
        verbosity=2,
        testLoader=unittest.TestLoader(),
        warnings='ignore'
    )