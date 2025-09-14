"""
POTX Template Generator

This module generates complete PowerPoint template files (.potx) with embedded
StyleStack design tokens for live updates via Office add-ins. Integrates with
the PowerPoint SuperTheme layout engine to create professional templates.
"""

import zipfile
import io
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import json
import uuid

from tools.powerpoint_supertheme_layout_engine import PowerPointSuperThemeLayoutEngine, create_powerpoint_supertheme_layout_engine
from tools.core.types import ProcessingResult

# Import existing OOXML components
try:
    from tools.ooxml_processor import OOXMLProcessor
    from tools.variable_substitution import VariableSubstitution
    OOXML_COMPONENTS_AVAILABLE = True
except ImportError:
    OOXMLProcessor = None
    VariableSubstitution = None
    OOXML_COMPONENTS_AVAILABLE = False


class POTXTemplateGenerator:
    """Generates complete PowerPoint template files with embedded design tokens"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        
        # Initialize layout engine
        self.layout_engine = create_powerpoint_supertheme_layout_engine(verbose=verbose)
        
        # Initialize OOXML processor if available
        if OOXML_COMPONENTS_AVAILABLE:
            self.ooxml_processor = OOXMLProcessor()
            self.variable_substitution = VariableSubstitution()
        else:
            self.ooxml_processor = None
            self.variable_substitution = None
        
        # PowerPoint OOXML namespaces
        self.namespaces = {
            'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main', 
            'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
            'pr': 'http://schemas.openxmlformats.org/package/2006/relationships'
        }
        
        # Register namespaces for ElementTree
        for prefix, uri in self.namespaces.items():
            ET.register_namespace(prefix, uri)
    
    def generate_potx_template(self,
                             design_tokens: Dict[str, Any],
                             org: str,
                             channel: str,
                             template_name: Optional[str] = None,
                             layout_ids: Optional[List[str]] = None,
                             aspect_ratio: str = "16:9",
                             include_extension_variables: bool = True) -> ProcessingResult:
        """Generate complete POTX template with embedded design tokens"""
        try:
            if template_name is None:
                template_name = f"{org}-{channel}.potx"
            
            if self.verbose:
                print(f"🏗️  Generating POTX template: {template_name}")
            
            # Step 1: Generate token-enhanced layouts
            if layout_ids is None:
                # Use standard PowerPoint layout set
                layout_ids = ["title_slide", "title_and_content", "two_content", "section_header", "blank"]
            
            layouts_result = self.layout_engine.generate_all_layouts_with_tokens(
                design_tokens=design_tokens,
                org=org,
                channel=channel,
                aspect_ratio=aspect_ratio,
                layout_ids=layout_ids
            )
            
            if not layouts_result.success:
                return ProcessingResult(
                    success=False,
                    errors=[f"Layout generation failed: {layouts_result.errors}"]
                )
            
            enhanced_layouts = layouts_result.data["layouts"]
            
            # Step 2: Create POTX ZIP structure
            potx_zip = self._create_potx_zip_structure(
                enhanced_layouts=enhanced_layouts,
                template_name=template_name,
                aspect_ratio=aspect_ratio
            )
            
            if not potx_zip.success:
                return ProcessingResult(
                    success=False,
                    errors=[f"POTX ZIP creation failed: {potx_zip.errors}"]
                )
            
            # Step 3: Embed extension variables for live updates
            if include_extension_variables:
                extension_vars_result = self._embed_extension_variables(
                    potx_data=potx_zip.data,
                    design_tokens=design_tokens,
                    org=org,
                    channel=channel
                )
                
                if extension_vars_result.success:
                    potx_zip.data.update(extension_vars_result.data)
                else:
                    # Continue without extension variables if embedding fails
                    if self.verbose:
                        print(f"⚠️  Extension variable embedding failed: {extension_vars_result.errors}")
            
            return ProcessingResult(
                success=True,
                data={
                    "template_name": template_name,
                    "zip_bytes": potx_zip.data["zip_bytes"],
                    "layouts": enhanced_layouts,
                    "layout_count": len(enhanced_layouts),
                    "org": org,
                    "channel": channel,
                    "aspect_ratio": aspect_ratio,
                    "extension_variables": potx_zip.data.get("extension_variables", {}),
                    "generation_metadata": {
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "generator_version": "1.0.0",
                        "stylestack_integration": True
                    }
                }
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                errors=[f"POTX template generation error: {str(e)}"]
            )
    
    def _create_potx_zip_structure(self,
                                  enhanced_layouts: List[Dict[str, Any]],
                                  template_name: str,
                                  aspect_ratio: str) -> ProcessingResult:
        """Create the complete POTX ZIP file structure"""
        try:
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add standard POTX structure files
                self._add_content_types(zipf)
                self._add_app_properties(zipf, template_name)
                self._add_core_properties(zipf, template_name)
                self._add_rels(zipf)
                
                # Add presentation.xml
                presentation_xml = self._create_presentation_xml(enhanced_layouts, aspect_ratio)
                zipf.writestr("ppt/presentation.xml", presentation_xml)
                
                # Add presentation relationships
                self._add_presentation_rels(zipf, len(enhanced_layouts))
                
                # Add slide master
                slide_master_xml = self._create_slide_master(aspect_ratio)
                zipf.writestr("ppt/slideMasters/slideMaster1.xml", slide_master_xml)
                
                # Add slide master relationships
                self._add_slide_master_rels(zipf, len(enhanced_layouts))
                
                # Add slide layouts
                for i, layout in enumerate(enhanced_layouts, 1):
                    layout_xml = self._create_slide_layout_xml(layout, i)
                    zipf.writestr(f"ppt/slideLayouts/slideLayout{i}.xml", layout_xml)
                    
                    # Add layout relationships
                    layout_rels = self._create_slide_layout_rels(i)
                    zipf.writestr(f"ppt/slideLayouts/_rels/slideLayout{i}.xml.rels", layout_rels)
                
                # Add theme
                theme_xml = self._create_theme_xml()
                zipf.writestr("ppt/theme/theme1.xml", theme_xml)
                
                if self.verbose:
                    print(f"✅ Created POTX ZIP with {len(enhanced_layouts)} layouts")
            
            zip_buffer.seek(0)
            zip_bytes = zip_buffer.getvalue()
            
            return ProcessingResult(
                success=True,
                data={
                    "zip_bytes": zip_bytes,
                    "zip_size": len(zip_bytes),
                    "layout_count": len(enhanced_layouts)
                }
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                errors=[f"POTX ZIP structure creation error: {str(e)}"]
            )
    
    def _add_content_types(self, zipf: zipfile.ZipFile):
        """Add [Content_Types].xml to POTX"""
        content_types = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-presentationml.presentation.main+xml"/>
    <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-presentationml.slideMaster+xml"/>
    <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
    <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
    <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""
        zipf.writestr("[Content_Types].xml", content_types)
    
    def _add_app_properties(self, zipf: zipfile.ZipFile, template_name: str):
        """Add docProps/app.xml to POTX"""
        app_props = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
    <Application>StyleStack PowerPoint Template Generator</Application>
    <PresentationFormat>Template</PresentationFormat>
    <ScaleCrop>false</ScaleCrop>
    <Company>StyleStack</Company>
    <LinksUpToDate>false</LinksUpToDate>
    <SharedDoc>false</SharedDoc>
    <HyperlinksChanged>false</HyperlinksChanged>
    <AppVersion>1.0.0</AppVersion>
</Properties>"""
        zipf.writestr("docProps/app.xml", app_props)
    
    def _add_core_properties(self, zipf: zipfile.ZipFile, template_name: str):
        """Add docProps/core.xml to POTX"""
        now = datetime.utcnow().isoformat() + "Z"
        core_props = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <dc:title>{template_name}</dc:title>
    <dc:creator>StyleStack</dc:creator>
    <cp:lastModifiedBy>StyleStack Template Generator</cp:lastModifiedBy>
    <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
    <dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
    <cp:category>StyleStack Design System Template</cp:category>
    <cp:contentStatus>Final</cp:contentStatus>
</cp:coreProperties>"""
        zipf.writestr("docProps/core.xml", core_props)
    
    def _add_rels(self, zipf: zipfile.ZipFile):
        """Add _rels/.rels to POTX"""
        rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
    <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
    <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""
        zipf.writestr("_rels/.rels", rels)
    
    def _create_presentation_xml(self, enhanced_layouts: List[Dict[str, Any]], aspect_ratio: str) -> str:
        """Create presentation.xml with slide dimensions"""
        # Get slide dimensions for aspect ratio
        from tools.powerpoint_positioning_calculator import PositioningCalculator
        calc = PositioningCalculator(aspect_ratio)
        width, height = calc.get_slide_dimensions()
        
        presentation = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" saveSubsetFonts="1" autoCompressPictures="0">
    <p:sldMasterIdLst>
        <p:sldMasterId id="2147483648" r:id="rId1"/>
    </p:sldMasterIdLst>
    <p:handoutMasterIdLst>
        <p:handoutMasterId r:id="rId2"/>
    </p:handoutMasterIdLst>
    <p:sldSz cx="{width}" cy="{height}" type="screen16x9"/>
    <p:notesSz cx="6858000" cy="9144000"/>
    <p:defaultTextStyle>
        <a:defPPr>
            <a:defRPr lang="en-US"/>
        </a:defPPr>
        <a:lvl1pPr marL="0" algn="l" defTabSz="914400" rtl="0" eaLnBrk="1" latinLnBrk="0" hangingPunct="1">
            <a:defRPr sz="1800" kern="1200">
                <a:solidFill>
                    <a:schemeClr val="tx1"/>
                </a:solidFill>
                <a:latin typeface="+mn-lt"/>
                <a:ea typeface="+mn-ea"/>
                <a:cs typeface="+mn-cs"/>
            </a:defRPr>
        </a:lvl1pPr>
    </p:defaultTextStyle>
</p:presentation>"""
        return presentation
    
    def _add_presentation_rels(self, zipf: zipfile.ZipFile, layout_count: int):
        """Add ppt/_rels/presentation.xml.rels"""
        rels_parts = [
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>',
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/handoutMaster" Target="handoutMasters/handoutMaster1.xml"/>'
        ]
        
        rels = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    {chr(10).join(rels_parts)}
</Relationships>"""
        zipf.writestr("ppt/_rels/presentation.xml.rels", rels)
    
    def _create_slide_master(self, aspect_ratio: str) -> str:
        """Create slide master XML"""
        slide_master = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
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
        </p:spTree>
    </p:cSld>
    <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
    <p:txStyles>
        <p:titleStyle>
            <a:lvl1pPr algn="ctr" defTabSz="914400" rtl="0" eaLnBrk="1" latinLnBrk="0" hangingPunct="1">
                <a:defRPr sz="4400" kern="1200">
                    <a:solidFill>
                        <a:schemeClr val="tx1"/>
                    </a:solidFill>
                    <a:latin typeface="+mj-lt"/>
                    <a:ea typeface="+mj-ea"/>
                    <a:cs typeface="+mj-cs"/>
                </a:defRPr>
            </a:lvl1pPr>
        </p:titleStyle>
        <p:bodyStyle>
            <a:lvl1pPr marL="342900" indent="-342900" algn="l" defTabSz="914400" rtl="0" eaLnBrk="1" latinLnBrk="0" hangingPunct="1">
                <a:defRPr sz="2800" kern="1200">
                    <a:solidFill>
                        <a:schemeClr val="tx1"/>
                    </a:solidFill>
                    <a:latin typeface="+mn-lt"/>
                    <a:ea typeface="+mn-ea"/>
                    <a:cs typeface="+mn-cs"/>
                </a:defRPr>
            </a:lvl1pPr>
        </p:bodyStyle>
        <p:otherStyle>
            <a:defPPr>
                <a:defRPr lang="en-US"/>
            </a:defPPr>
        </p:otherStyle>
    </p:txStyles>
</p:sldMaster>"""
        return slide_master
    
    def _add_slide_master_rels(self, zipf: zipfile.ZipFile, layout_count: int):
        """Add slide master relationships"""
        rels_parts = []
        
        # Add layout relationships
        for i in range(1, layout_count + 1):
            rels_parts.append(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout{i}.xml"/>')
        
        # Add theme relationship
        rels_parts.append(f'<Relationship Id="rId{layout_count + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>')
        
        rels = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    {chr(10).join(rels_parts)}
</Relationships>"""
        zipf.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", rels)
    
    def _create_slide_layout_xml(self, layout: Dict[str, Any], layout_number: int) -> str:
        """Create slide layout XML from enhanced layout"""
        layout_type = layout.get("type", "obj")
        layout_name = layout.get("name", f"Layout {layout_number}")
        
        # Create placeholder elements
        placeholder_elements = []
        for i, placeholder in enumerate(layout.get("placeholders", [])):
            placeholder_xml = self._create_placeholder_xml(placeholder, i + 2)  # Start from id 2
            placeholder_elements.append(placeholder_xml)
        
        slide_layout = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="{layout_type}" preserve="1" showMasterSp="0">
    <p:cSld name="{layout_name}">
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
            {chr(10).join(placeholder_elements)}
        </p:spTree>
    </p:cSld>
</p:sldLayout>"""
        return slide_layout
    
    def _create_placeholder_xml(self, placeholder: Dict[str, Any], shape_id: int) -> str:
        """Create placeholder XML from placeholder definition"""
        ph_type = placeholder.get("type", "body")
        ph_name = placeholder.get("name", f"Placeholder {shape_id}")
        ph_index = placeholder.get("index", 0)
        
        # Get position
        position = placeholder.get("position", {})
        x = position.get("x", 457200)  # Default margins
        y = position.get("y", 274638)
        width = position.get("width", 8229600)
        height = position.get("height", 1143000)
        
        # Get typography if available
        typography = placeholder.get("typography", {})
        font_size = typography.get("font_size", "1800")
        
        placeholder_xml = f"""<p:sp>
    <p:nvSpPr>
        <p:cNvPr id="{shape_id}" name="{ph_name}"/>
        <p:cNvSpPr>
            <a:spLocks noGrp="1"/>
        </p:cNvSpPr>
        <p:nvPr>
            <p:ph type="{ph_type}" idx="{ph_index}"/>
        </p:nvPr>
    </p:nvSpPr>
    <p:spPr>
        <a:xfrm>
            <a:off x="{x}" y="{y}"/>
            <a:ext cx="{width}" cy="{height}"/>
        </a:xfrm>
        <a:prstGeom prst="rect">
            <a:avLst/>
        </a:prstGeom>
    </p:spPr>
    <p:txBody>
        <a:bodyPr/>
        <a:lstStyle/>
        <a:p>
            <a:pPr lvl="0"/>
            <a:r>
                <a:rPr lang="en-US" dirty="0" smtClean="0" sz="{font_size}"/>
                <a:t>Click to edit {ph_type}</a:t>
            </a:r>
            <a:endParaRPr lang="en-US" dirty="0" sz="{font_size}"/>
        </a:p>
    </p:txBody>
</p:sp>"""
        return placeholder_xml
    
    def _create_slide_layout_rels(self, layout_number: int) -> str:
        """Create slide layout relationships"""
        rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>"""
        return rels
    
    def _create_theme_xml(self) -> str:
        """Create basic theme XML"""
        theme = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="StyleStack Theme 1">
    <a:themeElements>
        <a:clrScheme name="StyleStack">
            <a:dk1>
                <a:sysClr val="windowText" lastClr="000000"/>
            </a:dk1>
            <a:lt1>
                <a:sysClr val="window" lastClr="FFFFFF"/>
            </a:lt1>
            <a:dk2>
                <a:srgbClr val="44546A"/>
            </a:dk2>
            <a:lt2>
                <a:srgbClr val="E7E6E6"/>
            </a:lt2>
            <a:accent1>
                <a:srgbClr val="0066CC"/>
            </a:accent1>
            <a:accent2>
                <a:srgbClr val="4D94FF"/>
            </a:accent2>
            <a:accent3>
                <a:srgbClr val="A5A5A5"/>
            </a:accent3>
            <a:accent4>
                <a:srgbClr val="FFC000"/>
            </a:accent4>
            <a:accent5>
                <a:srgbClr val="4472C4"/>
            </a:accent5>
            <a:accent6>
                <a:srgbClr val="70AD47"/>
            </a:accent6>
            <a:hlink>
                <a:srgbClr val="0563C1"/>
            </a:hlink>
            <a:folHlink>
                <a:srgbClr val="954F72"/>
            </a:folHlink>
        </a:clrScheme>
        <a:fontScheme name="StyleStack">
            <a:majorFont>
                <a:latin typeface="Arial"/>
                <a:ea typeface=""/>
                <a:cs typeface=""/>
            </a:majorFont>
            <a:minorFont>
                <a:latin typeface="Arial"/>
                <a:ea typeface=""/>
                <a:cs typeface=""/>
            </a:minorFont>
        </a:fontScheme>
        <a:fmtScheme name="StyleStack">
            <a:fillStyleLst>
                <a:solidFill>
                    <a:schemeClr val="phClr"/>
                </a:solidFill>
                <a:gradFill rotWithShape="1">
                    <a:gsLst>
                        <a:gs pos="0">
                            <a:schemeClr val="phClr">
                                <a:lumMod val="110000"/>
                                <a:satMod val="105000"/>
                                <a:tint val="67000"/>
                            </a:schemeClr>
                        </a:gs>
                        <a:gs pos="50000">
                            <a:schemeClr val="phClr">
                                <a:lumMod val="105000"/>
                                <a:satMod val="103000"/>
                                <a:tint val="73000"/>
                            </a:schemeClr>
                        </a:gs>
                        <a:gs pos="100000">
                            <a:schemeClr val="phClr">
                                <a:lumMod val="105000"/>
                                <a:satMod val="109000"/>
                                <a:tint val="81000"/>
                            </a:schemeClr>
                        </a:gs>
                    </a:gsLst>
                    <a:lin ang="5400000" scaled="0"/>
                </a:gradFill>
                <a:gradFill rotWithShape="1">
                    <a:gsLst>
                        <a:gs pos="0">
                            <a:schemeClr val="phClr">
                                <a:satMod val="103000"/>
                                <a:lumMod val="102000"/>
                                <a:tint val="94000"/>
                            </a:schemeClr>
                        </a:gs>
                        <a:gs pos="50000">
                            <a:schemeClr val="phClr">
                                <a:satMod val="110000"/>
                                <a:lumMod val="100000"/>
                                <a:shade val="100000"/>
                            </a:schemeClr>
                        </a:gs>
                        <a:gs pos="100000">
                            <a:schemeClr val="phClr">
                                <a:lumMod val="99000"/>
                                <a:satMod val="120000"/>
                                <a:shade val="78000"/>
                            </a:schemeClr>
                        </a:gs>
                    </a:gsLst>
                    <a:lin ang="5400000" scaled="0"/>
                </a:gradFill>
            </a:fillStyleLst>
            <a:lnStyleLst>
                <a:ln w="6350" cap="flat" cmpd="sng" algn="ctr">
                    <a:solidFill>
                        <a:schemeClr val="phClr"/>
                    </a:solidFill>
                    <a:prstDash val="solid"/>
                    <a:miter lim="800000"/>
                </a:ln>
                <a:ln w="12700" cap="flat" cmpd="sng" algn="ctr">
                    <a:solidFill>
                        <a:schemeClr val="phClr"/>
                    </a:solidFill>
                    <a:prstDash val="solid"/>
                    <a:miter lim="800000"/>
                </a:ln>
                <a:ln w="19050" cap="flat" cmpd="sng" algn="ctr">
                    <a:solidFill>
                        <a:schemeClr val="phClr"/>
                    </a:solidFill>
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
                            <a:srgbClr val="000000">
                                <a:alpha val="63000"/>
                            </a:srgbClr>
                        </a:outerShdw>
                    </a:effectLst>
                </a:effectStyle>
            </a:effectStyleLst>
            <a:bgFillStyleLst>
                <a:solidFill>
                    <a:schemeClr val="phClr"/>
                </a:solidFill>
                <a:solidFill>
                    <a:schemeClr val="phClr">
                        <a:tint val="95000"/>
                        <a:satMod val="170000"/>
                    </a:schemeClr>
                </a:solidFill>
                <a:gradFill rotWithShape="1">
                    <a:gsLst>
                        <a:gs pos="0">
                            <a:schemeClr val="phClr">
                                <a:tint val="93000"/>
                                <a:satMod val="150000"/>
                                <a:shade val="98000"/>
                                <a:lumMod val="102000"/>
                            </a:schemeClr>
                        </a:gs>
                        <a:gs pos="50000">
                            <a:schemeClr val="phClr">
                                <a:tint val="98000"/>
                                <a:satMod val="130000"/>
                                <a:shade val="90000"/>
                                <a:lumMod val="103000"/>
                            </a:schemeClr>
                        </a:gs>
                        <a:gs pos="100000">
                            <a:schemeClr val="phClr">
                                <a:shade val="63000"/>
                                <a:satMod val="120000"/>
                            </a:schemeClr>
                        </a:gs>
                    </a:gsLst>
                    <a:lin ang="5400000" scaled="0"/>
                </a:gradFill>
            </a:bgFillStyleLst>
        </a:fmtScheme>
    </a:themeElements>
    <a:objectDefaults/>
    <a:extraClrSchemeLst/>
    <a:extLst>
        <a:ext uri="{05A4C25C-085E-4340-85A3-A5531E510DB2}">
            <thm15:themeFamily xmlns:thm15="http://schemas.microsoft.com/office/thememl/2012/main" name="StyleStack" id="{62F939B6-93AF-4DB8-9C6B-D6C7DFDC589F}" vid="{4A3C46E8-61CC-4603-A589-7422A47A8E4A}"/>
        </a:ext>
    </a:extLst>
</a:theme>"""
        return theme
    
    def _embed_extension_variables(self,
                                 potx_data: Dict[str, Any],
                                 design_tokens: Dict[str, Any],
                                 org: str,
                                 channel: str) -> ProcessingResult:
        """Embed extension variables for live token updates"""
        try:
            # Create extension variables that Office add-ins can read
            extension_variables = {
                "stylestack.org": org,
                "stylestack.channel": channel,
                "stylestack.api_endpoint": "https://api.stylestack.io/v1/tokens",
                "stylestack.version": "1.0.0",
                "stylestack.last_update": datetime.utcnow().isoformat() + "Z"
            }
            
            # Add flattened token references for live updates
            flattened_tokens = self._flatten_design_tokens(design_tokens)
            for token_path, token_value in flattened_tokens.items():
                extension_variables[f"stylestack.tokens.{token_path}"] = token_value
            
            if self.verbose:
                print(f"✅ Created {len(extension_variables)} extension variables")
            
            return ProcessingResult(
                success=True,
                data={
                    "extension_variables": extension_variables,
                    "variable_count": len(extension_variables)
                }
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                errors=[f"Extension variable embedding error: {str(e)}"]
            )
    
    def _flatten_design_tokens(self, tokens: Dict[str, Any], prefix: str = "") -> Dict[str, str]:
        """Flatten hierarchical design tokens for extension variables"""
        flattened = {}
        
        def flatten_recursive(obj: Any, path: str):
            if isinstance(obj, dict):
                if "$value" in obj:
                    # This is a design token with a value
                    flattened[path] = obj["$value"]
                elif "$type" in obj and "$value" in obj:
                    # Design token with type and value
                    flattened[path] = obj["$value"]
                else:
                    # Continue flattening nested structure
                    for key, value in obj.items():
                        if not key.startswith("$"):  # Skip metadata keys
                            new_path = f"{path}.{key}" if path else key
                            flatten_recursive(value, new_path)
        
        flatten_recursive(tokens, prefix)
        return flattened


def create_potx_template_generator(verbose: bool = False) -> POTXTemplateGenerator:
    """Factory function to create POTX template generator"""
    return POTXTemplateGenerator(verbose=verbose)


if __name__ == '__main__':
    # Demo usage
    print("📋 POTX Template Generator Demo")
    
    generator = create_potx_template_generator(verbose=True)
    
    # Sample design tokens for demo
    sample_tokens = {
        "global": {
            "colors": {
                "neutral": {
                    "white": {"$type": "color", "$value": "#FFFFFF"},
                    "black": {"$type": "color", "$value": "#000000"}
                }
            }
        },
        "corporate": {
            "acme": {
                "colors": {
                    "brand": {
                        "primary": {"$type": "color", "$value": "#0066CC"},
                        "secondary": {"$type": "color", "$value": "#4D94FF"}
                    }
                },
                "typography": {
                    "title": {
                        "family": {"$type": "fontFamily", "$value": "Arial Bold"},
                        "size": {"$type": "dimension", "$value": "44pt"}
                    }
                }
            }
        },
        "channel": {
            "present": {
                "colors": {
                    "text": {"$type": "color", "$value": "#FFFFFF"},
                    "background": {"$type": "color", "$value": "#0066CC"}
                },
                "spacing": {
                    "margin": {"$type": "dimension", "$value": "0.5in"}
                }
            }
        }
    }
    
    print(f"\n🏗️  Generating POTX template...")
    
    result = generator.generate_potx_template(
        design_tokens=sample_tokens,
        org="acme",
        channel="present",
        layout_ids=["title_slide", "title_and_content", "two_content"]
    )
    
    if result.success:
        data = result.data
        print(f"   ✅ Generated: {data['template_name']}")
        print(f"   📏 ZIP size: {len(data['zip_bytes']):,} bytes")
        print(f"   🎨 Layouts: {data['layout_count']}")
        print(f"   🏢 Organization: {data['org']}")
        print(f"   📡 Channel: {data['channel']}")
        print(f"   📐 Aspect ratio: {data['aspect_ratio']}")
        print(f"   🔧 Extension variables: {len(data['extension_variables'])}")
        print(f"   ⏰ Generated: {data['generation_metadata']['timestamp']}")
        
        # Save demo file
        demo_path = Path("demo-acme-present.potx")
        with open(demo_path, "wb") as f:
            f.write(data["zip_bytes"])
        print(f"   💾 Saved demo file: {demo_path}")
        
    else:
        print(f"   ❌ Generation failed: {result.errors}")
    
    print(f"\n🎯 Demo complete!")