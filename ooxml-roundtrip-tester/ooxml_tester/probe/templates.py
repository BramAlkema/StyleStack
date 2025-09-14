"""OOXML template classes for generating probe files."""

import zipfile
from pathlib import Path
from typing import List
from lxml import etree

# Import validation result - avoiding circular import
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of probe file validation - duplicate to avoid circular import."""
    is_valid: bool
    format: Optional[str] = None
    found_features: List[str] = None
    missing_features: List[str] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.found_features is None:
            self.found_features = []
        if self.missing_features is None:
            self.missing_features = []
        if self.errors is None:
            self.errors = []


class BaseTemplate:
    """Base template class for OOXML probe generation."""
    
    def __init__(self):
        """Initialize base template."""
        pass
    
    def create_probe(self, output_file: Path, features: List[str]) -> None:
        """Create probe file with specified features."""
        raise NotImplementedError("Subclasses must implement create_probe")
    
    def create_carrier_probe(self, output_file: Path, carriers: List[str]) -> None:
        """Create probe file targeting specific carriers."""
        raise NotImplementedError("Subclasses must implement create_carrier_probe")
    
    def validate_features(self, probe_file: Path, expected_features: List[str]) -> ValidationResult:
        """Validate features in probe file."""
        raise NotImplementedError("Subclasses must implement validate_features")


class DocxTemplate(BaseTemplate):
    """Template for generating Word document probes."""
    
    def create_probe(self, output_file: Path, features: List[str]) -> None:
        """Create DOCX probe file with specified features."""
        # Create ZIP file structure
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as docx_zip:
            # Content Types
            self._add_content_types(docx_zip, features)
            
            # Relationships
            self._add_main_rels(docx_zip)
            
            # Main document
            self._add_document(docx_zip, features)
            
            # Document relationships
            self._add_document_rels(docx_zip, features)
            
            # Styles (if requested)
            if 'styles' in features:
                self._add_styles(docx_zip)
            
            # Theme (if requested)
            if 'themes' in features:
                self._add_theme(docx_zip)
            
            # Numbering (if requested)
            if 'numbering' in features:
                self._add_numbering(docx_zip)
    
    def create_carrier_probe(self, output_file: Path, carriers: List[str]) -> None:
        """Create DOCX probe targeting specific StyleStack carriers."""
        # Create basic probe with theme and styles
        self.create_probe(output_file, ['themes', 'styles'])
        
        # TODO: Modify specific carrier elements based on carriers list
        # This would involve reading the ZIP, modifying XML, and writing back
    
    def validate_features(self, probe_file: Path, expected_features: List[str]) -> ValidationResult:
        """Validate features in DOCX probe file."""
        found_features = []
        missing_features = []
        errors = []
        
        try:
            with zipfile.ZipFile(probe_file, 'r') as docx_zip:
                files = docx_zip.namelist()
                
                # Check for styles
                if 'styles' in expected_features:
                    if 'word/styles.xml' in files:
                        found_features.append('styles')
                    else:
                        missing_features.append('styles')
                
                # Check for themes
                if 'themes' in expected_features:
                    if 'word/theme/theme1.xml' in files:
                        found_features.append('themes')
                    else:
                        missing_features.append('themes')
                
                # Check for numbering
                if 'numbering' in expected_features:
                    if 'word/numbering.xml' in files:
                        found_features.append('numbering')
                    else:
                        missing_features.append('numbering')
                
                # Check for tables by examining document content
                if 'tables' in expected_features:
                    document_xml = docx_zip.read('word/document.xml')
                    if b'<w:tbl' in document_xml:
                        found_features.append('tables')
                    else:
                        missing_features.append('tables')
                        
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return ValidationResult(is_valid=False, errors=errors)
        
        return ValidationResult(
            is_valid=len(missing_features) == 0 and len(errors) == 0,
            found_features=found_features,
            missing_features=missing_features,
            errors=errors
        )
    
    def _add_content_types(self, docx_zip: zipfile.ZipFile, features: List[str]) -> None:
        """Add Content_Types.xml file."""
        content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'''
        
        if 'styles' in features:
            content_types += '''
    <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'''
        
        if 'themes' in features:
            content_types += '''
    <Override PartName="/word/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'''
        
        if 'numbering' in features:
            content_types += '''
    <Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'''
        
        content_types += '''
</Types>'''
        
        docx_zip.writestr('[Content_Types].xml', content_types)
    
    def _add_main_rels(self, docx_zip: zipfile.ZipFile) -> None:
        """Add main relationships file."""
        rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''
        docx_zip.writestr('_rels/.rels', rels)
    
    def _add_document(self, docx_zip: zipfile.ZipFile, features: List[str]) -> None:
        """Add main document.xml file."""
        document = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r>
                <w:t>OOXML Probe Document</w:t>
            </w:r>
        </w:p>'''
        
        # Add table if requested
        if 'tables' in features:
            document += '''
        <w:tbl>
            <w:tblPr>
                <w:tblW w:w="5000" w:type="pct"/>
            </w:tblPr>
            <w:tblGrid>
                <w:gridCol w:w="2500"/>
                <w:gridCol w:w="2500"/>
            </w:tblGrid>
            <w:tr>
                <w:tc>
                    <w:p>
                        <w:r>
                            <w:t>Cell 1</w:t>
                        </w:r>
                    </w:p>
                </w:tc>
                <w:tc>
                    <w:p>
                        <w:r>
                            <w:t>Cell 2</w:t>
                        </w:r>
                    </w:p>
                </w:tc>
            </w:tr>
        </w:tbl>'''
        
        document += '''
    </w:body>
</w:document>'''
        
        docx_zip.writestr('word/document.xml', document)
    
    def _add_document_rels(self, docx_zip: zipfile.ZipFile, features: List[str]) -> None:
        """Add document relationships file."""
        rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'''
        
        rel_id = 1
        if 'styles' in features:
            rels += f'''
    <Relationship Id="rId{rel_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'''
            rel_id += 1
        
        if 'themes' in features:
            rels += f'''
    <Relationship Id="rId{rel_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>'''
            rel_id += 1
        
        if 'numbering' in features:
            rels += f'''
    <Relationship Id="rId{rel_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>'''
        
        rels += '''
</Relationships>'''
        
        docx_zip.writestr('word/_rels/document.xml.rels', rels)
    
    def _add_styles(self, docx_zip: zipfile.ZipFile) -> None:
        """Add styles.xml file."""
        styles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:style w:type="paragraph" w:styleId="Normal">
        <w:name w:val="Normal"/>
        <w:qFormat/>
    </w:style>
    <w:style w:type="character" w:styleId="DefaultParagraphFont">
        <w:name w:val="Default Paragraph Font"/>
        <w:uiPriority w:val="1"/>
        <w:semiHidden/>
    </w:style>
</w:styles>'''
        docx_zip.writestr('word/styles.xml', styles)
    
    def _add_theme(self, docx_zip: zipfile.ZipFile) -> None:
        """Add theme1.xml file."""
        theme = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="StyleStack Theme">
    <a:themeElements>
        <a:clrScheme name="StyleStack Colors">
            <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
            <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
            <a:dk2><a:srgbClr val="44546A"/></a:dk2>
            <a:lt2><a:srgbClr val="E7E6E6"/></a:lt2>
            <a:accent1><a:srgbClr val="4472C4"/></a:accent1>
            <a:accent2><a:srgbClr val="E84C3D"/></a:accent2>
            <a:accent3><a:srgbClr val="70AD47"/></a:accent3>
            <a:accent4><a:srgbClr val="FFC000"/></a:accent4>
            <a:accent5><a:srgbClr val="5B9BD5"/></a:accent5>
            <a:accent6><a:srgbClr val="A5A5A5"/></a:accent6>
            <a:hlink><a:srgbClr val="0563C1"/></a:hlink>
            <a:folHlink><a:srgbClr val="954F72"/></a:folHlink>
        </a:clrScheme>
        <a:fontScheme name="StyleStack Fonts">
            <a:majorFont>
                <a:latin typeface="Inter"/>
                <a:ea typeface=""/>
                <a:cs typeface=""/>
            </a:majorFont>
            <a:minorFont>
                <a:latin typeface="Inter"/>
                <a:ea typeface=""/>
                <a:cs typeface=""/>
            </a:minorFont>
        </a:fontScheme>
        <a:fmtScheme name="StyleStack Effects">
            <a:fillStyleLst>
                <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
                <a:gradFill rotWithShape="1"><a:gsLst><a:gs pos="0"><a:schemeClr val="phClr"><a:lumMod val="110000"/><a:satMod val="105000"/><a:tint val="67000"/></a:schemeClr></a:gs><a:gs pos="50000"><a:schemeClr val="phClr"><a:lumMod val="105000"/><a:satMod val="103000"/><a:tint val="73000"/></a:schemeClr></a:gs><a:gs pos="100000"><a:schemeClr val="phClr"><a:lumMod val="105000"/><a:satMod val="109000"/><a:tint val="81000"/></a:schemeClr></a:gs></a:gsLst><a:lin ang="5400000" scaled="0"/></a:gradFill>
                <a:gradFill rotWithShape="1"><a:gsLst><a:gs pos="0"><a:schemeClr val="phClr"><a:satMod val="103000"/><a:lumMod val="102000"/><a:tint val="94000"/></a:schemeClr></a:gs><a:gs pos="50000"><a:schemeClr val="phClr"><a:satMod val="110000"/><a:lumMod val="100000"/><a:shade val="100000"/></a:schemeClr></a:gs><a:gs pos="100000"><a:schemeClr val="phClr"><a:lumMod val="99000"/><a:satMod val="120000"/><a:shade val="78000"/></a:schemeClr></a:gs></a:gsLst><a:lin ang="5400000" scaled="0"/></a:gradFill>
            </a:fillStyleLst>
            <a:lnStyleLst>
                <a:ln w="6350" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/><a:miter lim="800000"/></a:ln>
                <a:ln w="12700" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/><a:miter lim="800000"/></a:ln>
                <a:ln w="19050" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/><a:miter lim="800000"/></a:ln>
            </a:lnStyleLst>
            <a:effectStyleLst>
                <a:effectStyle><a:effectLst/></a:effectStyle>
                <a:effectStyle><a:effectLst/></a:effectStyle>
                <a:effectStyle><a:effectLst><a:outerShdw blurRad="57150" dist="19050" dir="5400000" algn="ctr" rotWithShape="0"><a:srgbClr val="000000"><a:alpha val="63000"/></a:srgbClr></a:outerShdw></a:effectLst></a:effectStyle>
            </a:effectStyleLst>
            <a:bgFillStyleLst>
                <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
                <a:solidFill><a:schemeClr val="phClr"><a:tint val="95000"/><a:satMod val="170000"/></a:schemeClr></a:solidFill>
                <a:gradFill rotWithShape="1"><a:gsLst><a:gs pos="0"><a:schemeClr val="phClr"><a:tint val="93000"/><a:satMod val="150000"/><a:shade val="98000"/><a:lumMod val="102000"/></a:schemeClr></a:gs><a:gs pos="50000"><a:schemeClr val="phClr"><a:tint val="98000"/><a:satMod val="130000"/><a:shade val="90000"/><a:lumMod val="103000"/></a:schemeClr></a:gs><a:gs pos="100000"><a:schemeClr val="phClr"><a:shade val="63000"/><a:satMod val="120000"/></a:schemeClr></a:gs></a:gsLst><a:lin ang="5400000" scaled="0"/></a:gradFill>
            </a:bgFillStyleLst>
        </a:fmtScheme>
    </a:themeElements>
</a:theme>'''
        docx_zip.writestr('word/theme/theme1.xml', theme)
    
    def _add_numbering(self, docx_zip: zipfile.ZipFile) -> None:
        """Add numbering.xml file."""
        numbering = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:abstractNum w:abstractNumId="0">
        <w:multiLevelType w:val="hybridMultilevel"/>
        <w:lvl w:ilvl="0">
            <w:start w:val="1"/>
            <w:numFmt w:val="decimal"/>
            <w:lvlText w:val="%1."/>
            <w:lvlJc w:val="left"/>
            <w:pPr>
                <w:ind w:left="720" w:hanging="360"/>
            </w:pPr>
        </w:lvl>
    </w:abstractNum>
    <w:num w:numId="1">
        <w:abstractNumId w:val="0"/>
    </w:num>
</w:numbering>'''
        docx_zip.writestr('word/numbering.xml', numbering)


class PptxTemplate(BaseTemplate):
    """Template for generating PowerPoint presentation probes."""
    
    def create_probe(self, output_file: Path, features: List[str]) -> None:
        """Create PPTX probe file with specified features."""
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as pptx_zip:
            # Content Types
            self._add_content_types(pptx_zip, features)
            
            # Relationships
            self._add_main_rels(pptx_zip)
            
            # Presentation
            self._add_presentation(pptx_zip, features)
            
            # Presentation relationships
            self._add_presentation_rels(pptx_zip, features)
            
            # Theme (always needed)
            self._add_theme(pptx_zip)
            
            # Slide master (if requested)
            if 'masters' in features:
                self._add_slide_master(pptx_zip)
                self._add_slide_master_rels(pptx_zip)
            
            # Slide layout (if requested)
            if 'layouts' in features:
                self._add_slide_layout(pptx_zip)
                self._add_slide_layout_rels(pptx_zip)
            
            # Sample slide
            self._add_slide(pptx_zip, features)
            self._add_slide_rels(pptx_zip)
    
    def create_carrier_probe(self, output_file: Path, carriers: List[str]) -> None:
        """Create PPTX probe targeting specific StyleStack carriers."""
        self.create_probe(output_file, ['themes', 'masters'])
    
    def validate_features(self, probe_file: Path, expected_features: List[str]) -> ValidationResult:
        """Validate features in PPTX probe file."""
        found_features = []
        missing_features = []
        errors = []
        
        try:
            with zipfile.ZipFile(probe_file, 'r') as pptx_zip:
                files = pptx_zip.namelist()
                
                # Check for themes
                if 'themes' in expected_features:
                    if 'ppt/theme/theme1.xml' in files:
                        found_features.append('themes')
                    else:
                        missing_features.append('themes')
                
                # Check for masters
                if 'masters' in expected_features:
                    if 'ppt/slideMasters/slideMaster1.xml' in files:
                        found_features.append('masters')
                    else:
                        missing_features.append('masters')
                
                # Check for layouts
                if 'layouts' in expected_features:
                    if 'ppt/slideLayouts/slideLayout1.xml' in files:
                        found_features.append('layouts')
                    else:
                        missing_features.append('layouts')
                
                # Check for shapes by examining slide content
                if 'shapes' in expected_features:
                    if 'ppt/slides/slide1.xml' in files:
                        slide_xml = pptx_zip.read('ppt/slides/slide1.xml')
                        if b'<p:sp' in slide_xml:
                            found_features.append('shapes')
                        else:
                            missing_features.append('shapes')
                    else:
                        missing_features.append('shapes')
                        
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return ValidationResult(is_valid=False, errors=errors)
        
        return ValidationResult(
            is_valid=len(missing_features) == 0 and len(errors) == 0,
            found_features=found_features,
            missing_features=missing_features,
            errors=errors
        )
    
    def _add_content_types(self, pptx_zip: zipfile.ZipFile, features: List[str]) -> None:
        """Add Content_Types.xml file."""
        content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="xml" ContentType="application/xml"/>
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
    <Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
    <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'''
        
        if 'masters' in features:
            content_types += '''
    <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>'''
        
        if 'layouts' in features:
            content_types += '''
    <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>'''
        
        content_types += '''
</Types>'''
        
        pptx_zip.writestr('[Content_Types].xml', content_types)
    
    def _add_main_rels(self, pptx_zip: zipfile.ZipFile) -> None:
        """Add main relationships file."""
        rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>'''
        pptx_zip.writestr('_rels/.rels', rels)
    
    def _add_presentation(self, pptx_zip: zipfile.ZipFile, features: List[str]) -> None:
        """Add presentation.xml file."""
        presentation = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <p:sldMasterIdLst>'''
        
        if 'masters' in features:
            presentation += '''
        <p:sldMasterId id="2147483648" r:id="rId1"/>'''
        
        presentation += '''
    </p:sldMasterIdLst>
    <p:sldIdLst>
        <p:sldId id="256" r:id="rId2"/>
    </p:sldIdLst>
    <p:sldSz cx="9144000" cy="6858000"/>
    <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>'''
        
        pptx_zip.writestr('ppt/presentation.xml', presentation)
    
    def _add_presentation_rels(self, pptx_zip: zipfile.ZipFile, features: List[str]) -> None:
        """Add presentation relationships."""
        rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'''
        
        rel_id = 1
        if 'masters' in features:
            rels += f'''
    <Relationship Id="rId{rel_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'''
            rel_id += 1
        
        rels += f'''
    <Relationship Id="rId{rel_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/>'''
        rel_id += 1
        
        rels += f'''
    <Relationship Id="rId{rel_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>'''
        
        rels += '''
</Relationships>'''
        
        pptx_zip.writestr('ppt/_rels/presentation.xml.rels', rels)
    
    def _add_theme(self, pptx_zip: zipfile.ZipFile) -> None:
        """Add theme1.xml file (same as DOCX)."""
        theme = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="StyleStack Theme">
    <a:themeElements>
        <a:clrScheme name="StyleStack Colors">
            <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
            <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
            <a:dk2><a:srgbClr val="44546A"/></a:dk2>
            <a:lt2><a:srgbClr val="E7E6E6"/></a:lt2>
            <a:accent1><a:srgbClr val="4472C4"/></a:accent1>
            <a:accent2><a:srgbClr val="E84C3D"/></a:accent2>
            <a:accent3><a:srgbClr val="70AD47"/></a:accent3>
            <a:accent4><a:srgbClr val="FFC000"/></a:accent4>
            <a:accent5><a:srgbClr val="5B9BD5"/></a:accent5>
            <a:accent6><a:srgbClr val="A5A5A5"/></a:accent6>
            <a:hlink><a:srgbClr val="0563C1"/></a:hlink>
            <a:folHlink><a:srgbClr val="954F72"/></a:folHlink>
        </a:clrScheme>
        <a:fontScheme name="StyleStack Fonts">
            <a:majorFont>
                <a:latin typeface="Inter"/>
                <a:ea typeface=""/>
                <a:cs typeface=""/>
            </a:majorFont>
            <a:minorFont>
                <a:latin typeface="Inter"/>
                <a:ea typeface=""/>
                <a:cs typeface=""/>
            </a:minorFont>
        </a:fontScheme>
        <a:fmtScheme name="StyleStack Effects">
            <a:fillStyleLst>
                <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
                <a:gradFill rotWithShape="1"><a:gsLst><a:gs pos="0"><a:schemeClr val="phClr"><a:lumMod val="110000"/><a:satMod val="105000"/><a:tint val="67000"/></a:schemeClr></a:gs><a:gs pos="50000"><a:schemeClr val="phClr"><a:lumMod val="105000"/><a:satMod val="103000"/><a:tint val="73000"/></a:schemeClr></a:gs><a:gs pos="100000"><a:schemeClr val="phClr"><a:lumMod val="105000"/><a:satMod val="109000"/><a:tint val="81000"/></a:schemeClr></a:gs></a:gsLst><a:lin ang="5400000" scaled="0"/></a:gradFill>
                <a:gradFill rotWithShape="1"><a:gsLst><a:gs pos="0"><a:schemeClr val="phClr"><a:satMod val="103000"/><a:lumMod val="102000"/><a:tint val="94000"/></a:schemeClr></a:gs><a:gs pos="50000"><a:schemeClr val="phClr"><a:satMod val="110000"/><a:lumMod val="100000"/><a:shade val="100000"/></a:schemeClr></a:gs><a:gs pos="100000"><a:schemeClr val="phClr"><a:lumMod val="99000"/><a:satMod val="120000"/><a:shade val="78000"/></a:schemeClr></a:gs></a:gsLst><a:lin ang="5400000" scaled="0"/></a:gradFill>
            </a:fillStyleLst>
            <a:lnStyleLst>
                <a:ln w="6350" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/><a:miter lim="800000"/></a:ln>
                <a:ln w="12700" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/><a:miter lim="800000"/></a:ln>
                <a:ln w="19050" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/><a:miter lim="800000"/></a:ln>
            </a:lnStyleLst>
            <a:effectStyleLst>
                <a:effectStyle><a:effectLst/></a:effectStyle>
                <a:effectStyle><a:effectLst/></a:effectStyle>
                <a:effectStyle><a:effectLst><a:outerShdw blurRad="57150" dist="19050" dir="5400000" algn="ctr" rotWithShape="0"><a:srgbClr val="000000"><a:alpha val="63000"/></a:srgbClr></a:outerShdw></a:effectLst></a:effectStyle>
            </a:effectStyleLst>
            <a:bgFillStyleLst>
                <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
                <a:solidFill><a:schemeClr val="phClr"><a:tint val="95000"/><a:satMod val="170000"/></a:schemeClr></a:solidFill>
                <a:gradFill rotWithShape="1"><a:gsLst><a:gs pos="0"><a:schemeClr val="phClr"><a:tint val="93000"/><a:satMod val="150000"/><a:shade val="98000"/><a:lumMod val="102000"/></a:schemeClr></a:gs><a:gs pos="50000"><a:schemeClr val="phClr"><a:tint val="98000"/><a:satMod val="130000"/><a:shade val="90000"/><a:lumMod val="103000"/></a:schemeClr></a:gs><a:gs pos="100000"><a:schemeClr val="phClr"><a:shade val="63000"/><a:satMod val="120000"/></a:schemeClr></a:gs></a:gsLst><a:lin ang="5400000" scaled="0"/></a:gradFill>
            </a:bgFillStyleLst>
        </a:fmtScheme>
    </a:themeElements>
</a:theme>'''
        pptx_zip.writestr('ppt/theme/theme1.xml', theme)
    
    def _add_slide_master(self, pptx_zip: zipfile.ZipFile) -> None:
        """Add slide master."""
        slide_master = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
    <p:cSld>
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
    <p:sldLayoutIdLst>
        <p:sldLayoutId id="2147483649" r:id="rId1"/>
    </p:sldLayoutIdLst>
    <p:txStyles>
        <p:titleStyle>
            <a:lvl1pPr marL="0" algn="ctr" rtl="0" eaLnBrk="1" latinLnBrk="0" hangingPunct="1">
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
            <a:lvl1pPr marL="342900" indent="-342900" algn="l" rtl="0" eaLnBrk="1" latinLnBrk="0" hangingPunct="1">
                <a:buChar char="•"/>
                <a:buFont typeface="Arial"/>
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
    </p:txStyles>
</p:sldMaster>'''
        pptx_zip.writestr('ppt/slideMasters/slideMaster1.xml', slide_master)
    
    def _add_slide_master_rels(self, pptx_zip: zipfile.ZipFile) -> None:
        """Add slide master relationships."""
        rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
    <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>'''
        pptx_zip.writestr('ppt/slideMasters/_rels/slideMaster1.xml.rels', rels)
    
    def _add_slide_layout(self, pptx_zip: zipfile.ZipFile) -> None:
        """Add slide layout."""
        slide_layout = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" type="title" preserve="1">
    <p:cSld name="Title Slide">
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
    <p:clrMapOvr>
        <a:masterClrMapping/>
    </p:clrMapOvr>
</p:sldLayout>'''
        pptx_zip.writestr('ppt/slideLayouts/slideLayout1.xml', slide_layout)
    
    def _add_slide_layout_rels(self, pptx_zip: zipfile.ZipFile) -> None:
        """Add slide layout relationships."""
        rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>'''
        pptx_zip.writestr('ppt/slideLayouts/_rels/slideLayout1.xml.rels', rels)
    
    def _add_slide(self, pptx_zip: zipfile.ZipFile, features: List[str]) -> None:
        """Add sample slide."""
        slide = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <p:cSld>
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
            </p:grpSpPr>'''
        
        # Add shapes if requested
        if 'shapes' in features:
            slide += '''
            <p:sp>
                <p:nvSpPr>
                    <p:cNvPr id="2" name="Title 1"/>
                    <p:cNvSpPr>
                        <a:spLocks noGrp="1"/>
                    </p:cNvSpPr>
                    <p:nvPr>
                        <p:ph type="ctrTitle"/>
                    </p:nvPr>
                </p:nvSpPr>
                <p:spPr/>
                <p:txBody>
                    <a:bodyPr/>
                    <a:lstStyle/>
                    <a:p>
                        <a:r>
                            <a:rPr lang="en-US" smtClean="0"/>
                            <a:t>OOXML Probe Presentation</a:t>
                        </a:r>
                        <a:endParaRPr lang="en-US"/>
                    </a:p>
                </p:txBody>
            </p:sp>'''
        
        slide += '''
        </p:spTree>
    </p:cSld>
    <p:clrMapOvr>
        <a:masterClrMapping/>
    </p:clrMapOvr>
</p:sld>'''
        
        pptx_zip.writestr('ppt/slides/slide1.xml', slide)
    
    def _add_slide_rels(self, pptx_zip: zipfile.ZipFile) -> None:
        """Add slide relationships."""
        rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>'''
        pptx_zip.writestr('ppt/slides/_rels/slide1.xml.rels', rels)


class XlsxTemplate(BaseTemplate):
    """Template for generating Excel workbook probes."""
    
    def create_probe(self, output_file: Path, features: List[str]) -> None:
        """Create XLSX probe file with specified features."""
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as xlsx_zip:
            # Content Types
            self._add_content_types(xlsx_zip, features)
            
            # Relationships
            self._add_main_rels(xlsx_zip)
            
            # Workbook
            self._add_workbook(xlsx_zip, features)
            
            # Workbook relationships
            self._add_workbook_rels(xlsx_zip, features)
            
            # Styles (always needed for basic formatting)
            self._add_styles(xlsx_zip)
            
            # Worksheet
            self._add_worksheet(xlsx_zip, features)
            
            # Shared strings (if needed)
            self._add_shared_strings(xlsx_zip)
    
    def create_carrier_probe(self, output_file: Path, carriers: List[str]) -> None:
        """Create XLSX probe targeting specific StyleStack carriers."""
        self.create_probe(output_file, ['styles', 'formatting'])
    
    def validate_features(self, probe_file: Path, expected_features: List[str]) -> ValidationResult:
        """Validate features in XLSX probe file."""
        found_features = []
        missing_features = []
        errors = []
        
        try:
            with zipfile.ZipFile(probe_file, 'r') as xlsx_zip:
                files = xlsx_zip.namelist()
                
                # Check for styles
                if 'styles' in expected_features:
                    if 'xl/styles.xml' in files:
                        found_features.append('styles')
                    else:
                        missing_features.append('styles')
                
                # Check for tables by looking in worksheet
                if 'tables' in expected_features:
                    if 'xl/worksheets/sheet1.xml' in files:
                        sheet_xml = xlsx_zip.read('xl/worksheets/sheet1.xml')
                        if b'<tablePart' in sheet_xml:
                            found_features.append('tables')
                        else:
                            missing_features.append('tables')
                    else:
                        missing_features.append('tables')
                        
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return ValidationResult(is_valid=False, errors=errors)
        
        return ValidationResult(
            is_valid=len(missing_features) == 0 and len(errors) == 0,
            found_features=found_features,
            missing_features=missing_features,
            errors=errors
        )
    
    def _add_content_types(self, xlsx_zip: zipfile.ZipFile, features: List[str]) -> None:
        """Add Content_Types.xml file."""
        content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="xml" ContentType="application/xml"/>
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
    <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
    <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
    <Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
</Types>'''
        xlsx_zip.writestr('[Content_Types].xml', content_types)
    
    def _add_main_rels(self, xlsx_zip: zipfile.ZipFile) -> None:
        """Add main relationships file."""
        rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>'''
        xlsx_zip.writestr('_rels/.rels', rels)
    
    def _add_workbook(self, xlsx_zip: zipfile.ZipFile, features: List[str]) -> None:
        """Add workbook.xml file."""
        workbook = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <sheets>
        <sheet name="Sheet1" sheetId="1" r:id="rId1"/>
    </sheets>
</workbook>'''
        xlsx_zip.writestr('xl/workbook.xml', workbook)
    
    def _add_workbook_rels(self, xlsx_zip: zipfile.ZipFile, features: List[str]) -> None:
        """Add workbook relationships."""
        rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
    <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
    <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>
</Relationships>'''
        xlsx_zip.writestr('xl/_rels/workbook.xml.rels', rels)
    
    def _add_styles(self, xlsx_zip: zipfile.ZipFile) -> None:
        """Add styles.xml file."""
        styles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
    <fonts count="1">
        <font>
            <sz val="11"/>
            <color theme="1"/>
            <name val="Calibri"/>
            <family val="2"/>
            <scheme val="minor"/>
        </font>
    </fonts>
    <fills count="2">
        <fill>
            <patternFill patternType="none"/>
        </fill>
        <fill>
            <patternFill patternType="gray125"/>
        </fill>
    </fills>
    <borders count="1">
        <border>
            <left/>
            <right/>
            <top/>
            <bottom/>
            <diagonal/>
        </border>
    </borders>
    <cellStyleXfs count="1">
        <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
    </cellStyleXfs>
    <cellXfs count="1">
        <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    </cellXfs>
    <cellStyles count="1">
        <cellStyle name="Normal" xfId="0" builtinId="0"/>
    </cellStyles>
</styleSheet>'''
        xlsx_zip.writestr('xl/styles.xml', styles)
    
    def _add_worksheet(self, xlsx_zip: zipfile.ZipFile, features: List[str]) -> None:
        """Add worksheet file."""
        worksheet = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <sheetData>
        <row r="1">
            <c r="A1" t="inlineStr">
                <is>
                    <t>OOXML Probe Worksheet</t>
                </is>
            </c>
        </row>'''
        
        # Add table data if requested
        if 'tables' in features:
            worksheet += '''
        <row r="2">
            <c r="A2" t="inlineStr">
                <is>
                    <t>Column 1</t>
                </is>
            </c>
            <c r="B2" t="inlineStr">
                <is>
                    <t>Column 2</t>
                </is>
            </c>
        </row>
        <row r="3">
            <c r="A3" t="inlineStr">
                <is>
                    <t>Data 1</t>
                </is>
            </c>
            <c r="B3" t="inlineStr">
                <is>
                    <t>Data 2</t>
                </is>
            </c>
        </row>'''
        
        worksheet += '''
    </sheetData>
</worksheet>'''
        
        xlsx_zip.writestr('xl/worksheets/sheet1.xml', worksheet)
    
    def _add_shared_strings(self, xlsx_zip: zipfile.ZipFile) -> None:
        """Add shared strings file."""
        shared_strings = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="0" uniqueCount="0">
</sst>'''
        xlsx_zip.writestr('xl/sharedStrings.xml', shared_strings)