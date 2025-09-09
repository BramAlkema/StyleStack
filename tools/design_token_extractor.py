#!/usr/bin/env python3
"""
StyleStack Design Token Extractor
Reverse engineer design tokens from existing Office and OpenOffice templates

This tool analyzes Office and OpenOffice files and extracts:
- Color palettes and usage patterns
- Typography hierarchies and styles  
- Layout patterns and spacing systems
- Brand asset locations and usage

Supported formats:
- Microsoft Office: .pptx, .potx, .ppsx (PowerPoint)
- OpenOffice/LibreOffice: .odp, .otp (Impress), .ods, .ots (Calc), .odt, .ott (Writer)
"""

import os
import json
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from collections import Counter, defaultdict
from lxml import etree as ET
import colorsys
import re

# Import existing StyleStack tools for comprehensive analysis
try:
    from .theme_resolver import ThemeResolver, Theme
    from .template_analyzer import TemplateAnalyzer, AnalysisResult
    from .ooxml_processor import OOXMLProcessor
except ImportError:
    # Fallback for standalone usage
    import sys
    sys.path.append(str(Path(__file__).parent))
    try:
        from theme_resolver import ThemeResolver, Theme
        from template_analyzer import TemplateAnalyzer, AnalysisResult
        from ooxml_processor import OOXMLProcessor
    except ImportError:
        print("⚠️  Warning: StyleStack analysis tools not available, using basic extraction only")
        ThemeResolver = None
        TemplateAnalyzer = None
        OOXMLProcessor = None

class DesignTokenExtractor:
    """Extract design tokens from Office and OpenOffice files"""
    
    # Office theme color indices
    THEME_COLORS = {
        '0': 'background1', '1': 'text1', '2': 'background2', '3': 'text2',
        '4': 'accent1', '5': 'accent2', '6': 'accent3', '7': 'accent4',
        '8': 'accent5', '9': 'accent6', '10': 'hyperlink', '11': 'followedHyperlink'
    }
    
    # Common font weight mappings
    FONT_WEIGHTS = {
        '400': 'normal', '700': 'bold', '600': 'semibold',
        'normal': 'normal', 'bold': 'bold'
    }
    
    def __init__(self, output_format='stylestack'):
        """
        Initialize extractor
        
        Args:
            output_format: 'stylestack', 'w3c', 'figma', or 'custom'
        """
        self.output_format = output_format
        self.extracted_colors = Counter()
        self.extracted_fonts = Counter()
        self.extracted_sizes = Counter()
        self.layout_patterns = []
        self.theme_info = {}
        self.extracted_images = []
        self.image_usage = Counter()
        
        # Initialize StyleStack analysis tools if available
        self.theme_resolver = ThemeResolver() if ThemeResolver else None
        self.template_analyzer = TemplateAnalyzer() if TemplateAnalyzer else None
        self.ooxml_processor = OOXMLProcessor() if OOXMLProcessor else None
        
        self.use_advanced_extraction = bool(self.theme_resolver and self.template_analyzer)
        
    def _detect_file_format(self, file_path: Path) -> str:
        """Detect file format based on extension and content"""
        extension = file_path.suffix.lower()
        
        # Microsoft Office formats (OOXML)
        if extension in ['.pptx', '.potx', '.ppsx']:
            return 'ooxml_presentation'
        elif extension in ['.docx', '.dotx']:
            return 'ooxml_document'
        elif extension in ['.xlsx', '.xltx']:
            return 'ooxml_spreadsheet'
            
        # OpenDocument formats (ODF)
        elif extension in ['.odp', '.otp']:
            return 'odf_presentation'
        elif extension in ['.odt', '.ott']:
            return 'odf_document'
        elif extension in ['.ods', '.ots']:
            return 'odf_spreadsheet'
            
        else:
            raise ValueError(f"Unsupported file format: {extension}")

    def extract_from_file(self, file_path: Path) -> Dict:
        """
        Extract design tokens from Office or OpenOffice files
        
        Args:
            file_path: Path to supported office file
            
        Returns:
            Dictionary of extracted design tokens
        """
        file_format = self._detect_file_format(file_path)
        
        if file_format.startswith('ooxml_'):
            return self._extract_from_ooxml(file_path, file_format)
        elif file_format.startswith('odf_'):
            return self._extract_from_odf(file_path, file_format)
        else:
            raise ValueError(f"Unsupported format: {file_format}")

    def _extract_from_ooxml(self, file_path: Path, format_type: str) -> Dict:
        """Extract tokens from OOXML formats (Microsoft Office)"""
        if self.use_advanced_extraction:
            return self._extract_with_stylestack_tools(file_path, format_type)
        else:
            return self._extract_basic_ooxml(file_path, format_type)

    def _extract_with_stylestack_tools(self, file_path: Path, format_type: str) -> Dict:
        """Enhanced extraction using StyleStack's advanced analysis tools"""
        print(f"🚀 Using advanced StyleStack extraction tools...")
        
        # Use TemplateAnalyzer for comprehensive analysis
        analysis_result = self.template_analyzer.analyze_complete_template(str(file_path))
        
        # Use ThemeResolver to extract theme information
        theme = self.theme_resolver.extract_theme_from_ooxml_file(file_path)
        
        # Convert analysis results to design tokens
        tokens = self._convert_analysis_to_tokens(analysis_result, theme, file_path)
        
        return tokens

    def _extract_basic_ooxml(self, file_path: Path, format_type: str) -> Dict:
        """Basic extraction (fallback when advanced tools unavailable)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract OOXML file
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                zip_file.extractall(temp_dir)
            
            temp_path = Path(temp_dir)
            
            # Extract different types of tokens
            self._extract_theme_colors(temp_path)
            self._extract_master_styles(temp_path)
            self._extract_content_analysis(temp_path)
            self._extract_layout_patterns(temp_path)
            self._extract_logos_and_images(temp_path)
            
            # Compile final token set
            return self._compile_tokens()

    def _convert_analysis_to_tokens(self, analysis: 'AnalysisResult', theme: Optional['Theme'], file_path: Path) -> Dict:
        """Convert StyleStack analysis results to design tokens format"""
        tokens = {
            "stylestack": {
                "version": "1.0.0",
                "extracted": True,
                "extraction_timestamp": "",
                "extraction_method": "advanced_stylestack_analysis",
                "tokens": {}
            }
        }
        
        token_data = tokens["stylestack"]["tokens"]
        
        # Debug: Check what we got from analysis
        print(f"📊 Analysis result type: {type(analysis)}")
        if hasattr(analysis, '__dict__'):
            print(f"📊 Analysis attributes: {list(analysis.__dict__.keys())}")
        print(f"🎨 Theme type: {type(theme)}")
        if theme and hasattr(theme, '__dict__'):
            print(f"🎨 Theme attributes: {list(theme.__dict__.keys())}")
        
        # Extract theme colors from advanced analysis
        if theme:
            color_tokens = {}
            # Try different possible attribute names
            colors_attr = None
            for attr_name in ['colors', 'color_scheme', 'theme_colors']:
                if hasattr(theme, attr_name):
                    colors_attr = getattr(theme, attr_name)
                    print(f"🎨 Found colors in theme.{attr_name}: {type(colors_attr)}")
                    break
            
            if colors_attr:
                if isinstance(colors_attr, dict):
                    for slot, color_info in colors_attr.items():
                        color_value = None
                        if isinstance(color_info, str):
                            color_value = color_info
                        elif hasattr(color_info, 'rgb_value'):
                            color_value = color_info.rgb_value
                        elif hasattr(color_info, 'value'):
                            color_value = color_info.value
                        
                        if color_value:
                            color_tokens[slot] = {
                                "value": color_value,
                                "type": "color",
                                "source": f"theme_slot_{slot}"
                            }
                
                if color_tokens:
                    token_data["colors"] = color_tokens
                    print(f"✅ Extracted {len(color_tokens)} color tokens")
        
        # Extract colors from design_elements
        if hasattr(analysis, 'design_elements') and analysis.design_elements:
            design_elements = analysis.design_elements
            print(f"🎨 Found {len(design_elements)} design elements")
            
            # Extract colors
            color_elements = [elem for elem in design_elements if elem.get('type') == 'color']
            if color_elements:
                color_tokens = {}
                for i, color_elem in enumerate(color_elements):
                    color_value = color_elem.get('value', color_elem.get('color'))
                    if color_value:
                        token_name = f"color_{i+1}"
                        if 'name' in color_elem:
                            token_name = color_elem['name']
                        elif 'theme_slot' in color_elem:
                            token_name = color_elem['theme_slot']
                        
                        color_tokens[token_name] = {
                            "value": color_value,
                            "type": "color",
                            "source": "design_elements_analysis"
                        }
                
                if color_tokens:
                    token_data["colors"] = color_tokens
                    print(f"✅ Extracted {len(color_tokens)} color tokens from design elements")
            
            # Extract typography
            font_elements = [elem for elem in design_elements if elem.get('type') in ['font', 'typography', 'text']]
            if font_elements:
                typography_tokens = {}
                font_families = set()
                font_sizes = Counter()
                
                for font_elem in font_elements:
                    if 'font_family' in font_elem:
                        font_families.add(font_elem['font_family'])
                    if 'font_size' in font_elem:
                        font_sizes[font_elem['font_size']] += 1
                    if 'size' in font_elem:
                        font_sizes[font_elem['size']] += 1
                
                if font_families:
                    primary_font = list(font_families)[0]
                    typography_tokens["font_family"] = {
                        "value": primary_font,
                        "type": "fontFamily",
                        "source": "design_elements_analysis"
                    }
                
                if font_sizes:
                    size_tokens = {}
                    for i, (size, count) in enumerate(font_sizes.most_common()):
                        size_tokens[f"size_{i+1}"] = {
                            "value": str(size),
                            "type": "fontSizes",
                            "usage_count": count,
                            "source": "design_elements_analysis"
                        }
                    typography_tokens["sizes"] = size_tokens
                
                if typography_tokens:
                    token_data["typography"] = typography_tokens
                    print(f"✅ Extracted typography tokens: {list(typography_tokens.keys())}")
        
        # Extract typography from analysis (fallback)
        if hasattr(analysis, 'fonts') and analysis.fonts:
            typography_tokens = {}
            
            # Process font families
            font_families = set()
            font_sizes = Counter()
            
            for font_info in analysis.fonts:
                if hasattr(font_info, 'font_family') and font_info.font_family:
                    font_families.add(font_info.font_family)
                if hasattr(font_info, 'font_size') and font_info.font_size:
                    font_sizes[font_info.font_size] += 1
            
            if font_families:
                primary_font = list(font_families)[0]  # Most common or first found
                typography_tokens["font_family"] = {
                    "value": primary_font,
                    "type": "fontFamily",
                    "source": "template_analysis"
                }
            
            if font_sizes:
                size_tokens = {}
                for i, (size, count) in enumerate(font_sizes.most_common()):
                    size_tokens[f"size_{i+1}"] = {
                        "value": size,
                        "type": "fontSizes",
                        "usage_count": count,
                        "source": "content_analysis"
                    }
                typography_tokens["sizes"] = size_tokens
            
            if typography_tokens:
                token_data["typography"] = typography_tokens
        
        # Extract spacing and layout from analysis
        if hasattr(analysis, 'layout_metrics'):
            spacing_tokens = {
                "note": "Extracted from comprehensive layout analysis"
            }
            # Add specific spacing values based on analysis
            token_data["spacing"] = spacing_tokens
        
        # Extract brand assets (keep existing image extraction)
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                zip_file.extractall(temp_dir)
            temp_path = Path(temp_dir)
            self._extract_logos_and_images(temp_path)
        
        if self.extracted_images:
            brand_assets = self._organize_brand_assets()
            if brand_assets:
                token_data["brand_assets"] = brand_assets
        
        return tokens

    def _organize_brand_assets(self) -> Dict:
        """Organize extracted images into brand asset categories"""
        logos = {}
        icons = {}
        other_images = {}
        
        for image_info in self.extracted_images:
            classification = image_info.get('classification', 'image')
            stem = image_info.get('stem', 'unknown')
            
            asset_data = {
                'filename': image_info['filename'],
                'format': image_info['format'],
                'size_bytes': image_info['size_bytes'],
                'relative_path': image_info['relative_path']
            }
            
            if 'dimensions' in image_info:
                asset_data['dimensions'] = image_info['dimensions']
            
            if classification in ['primary_logo', 'secondary_logo']:
                logos[stem] = asset_data
            elif classification in ['functional_icon', 'decorative_icon']:
                icons[stem] = asset_data
            else:
                other_images[stem] = asset_data
        
        brand_assets = {}
        if logos:
            brand_assets['logos'] = logos
        if icons:
            brand_assets['icons'] = icons  
        if other_images:
            brand_assets['images'] = other_images
            
        return brand_assets

    def _extract_from_odf(self, file_path: Path, format_type: str) -> Dict:
        """Extract tokens from ODF formats (OpenOffice/LibreOffice)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract ODF file (also ZIP-based)
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                zip_file.extractall(temp_dir)
            
            temp_path = Path(temp_dir)
            
            # ODF has different structure - extract from content.xml, styles.xml, etc.
            self._extract_odf_styles(temp_path)
            self._extract_odf_content(temp_path)
            self._extract_odf_images(temp_path)
            
            # Compile final token set
            return self._compile_tokens()

    def _extract_odf_styles(self, odf_dir: Path):
        """Extract styles from ODF styles.xml"""
        styles_file = odf_dir / "styles.xml"
        
        if not styles_file.exists():
            return
            
        try:
            tree = ET.parse(styles_file)
            root = tree.getroot()
            
            # ODF namespaces
            ns = {
                'style': 'urn:oasis:names:tc:opendocument:xmlns:style:1.0',
                'fo': 'urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0'
            }
            
            # Extract text styles for typography
            for style in root.findall('.//style:style[@style:family="text"]', ns):
                style_name = style.get('{urn:oasis:names:tc:opendocument:xmlns:style:1.0}name', '')
                
                # Extract font properties
                text_props = style.find('.//style:text-properties', ns)
                if text_props is not None:
                    font_family = text_props.get('{urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0}font-family', '')
                    font_size = text_props.get('{urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0}font-size', '')
                    font_color = text_props.get('{urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0}color', '')
                    
                    if font_family:
                        self.extracted_fonts[font_family] += 1
                    if font_size:
                        self.extracted_sizes[font_size] += 1
                    if font_color and font_color.startswith('#'):
                        self.extracted_colors[font_color.upper()] += 1
                        
        except Exception as e:
            print(f"Warning: Could not extract ODF styles: {e}")

    def _extract_odf_content(self, odf_dir: Path):
        """Extract content analysis from ODF content.xml"""
        content_file = odf_dir / "content.xml"
        
        if not content_file.exists():
            return
            
        try:
            tree = ET.parse(content_file)
            root = tree.getroot()
            
            # Basic content analysis for layout patterns
            # This is simplified - ODF content structure varies by application
            text_elements = root.findall('.//*')
            self.layout_patterns.append({
                'type': 'odf_content',
                'element_count': len(text_elements)
            })
                        
        except Exception as e:
            print(f"Warning: Could not extract ODF content: {e}")

    def _extract_odf_images(self, odf_dir: Path):
        """Extract images from ODF Pictures/ directory"""
        pictures_dir = odf_dir / "Pictures"
        
        if not pictures_dir.exists():
            return
            
        try:
            for image_file in pictures_dir.iterdir():
                if image_file.is_file():
                    image_info = self._analyze_image_file(image_file)
                    self.extracted_images.append(image_info)
                    
        except Exception as e:
            print(f"Warning: Could not extract ODF images: {e}")
    
    def _extract_theme_colors(self, pptx_dir: Path):
        """Extract colors from theme definition"""
        theme_file = pptx_dir / "ppt" / "theme" / "theme1.xml"
        
        if not theme_file.exists():
            return
            
        try:
            tree = ET.parse(theme_file)
            root = tree.getroot()
            
            # Extract theme color scheme
            ns = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
            
            color_scheme = root.find('.//a:clrScheme', ns)
            if color_scheme is not None:
                for color_elem in color_scheme:
                    color_name = color_elem.tag.split('}')[-1]  # Remove namespace
                    
                    # Look for srgbClr or sysClr
                    srgb = color_elem.find('.//a:srgbClr', ns)
                    if srgb is not None:
                        color_value = srgb.get('val', '')
                        if color_value:
                            self.theme_info[color_name] = f"#{color_value.upper()}"
                            
        except Exception as e:
            print(f"Warning: Could not extract theme colors: {e}")
    
    def _extract_master_styles(self, pptx_dir: Path):
        """Extract typography and styles from slide masters"""
        masters_dir = pptx_dir / "ppt" / "slideMasters"
        
        if not masters_dir.exists():
            return
            
        for master_file in masters_dir.glob("*.xml"):
            try:
                tree = ET.parse(master_file)
                root = tree.getroot()
                
                # Extract text styles
                self._analyze_text_elements(root)
                
            except Exception as e:
                print(f"Warning: Could not parse master {master_file}: {e}")
    
    def _extract_content_analysis(self, pptx_dir: Path):
        """Analyze actual slide content for usage patterns"""
        slides_dir = pptx_dir / "ppt" / "slides"
        
        if not slides_dir.exists():
            return
            
        for slide_file in slides_dir.glob("*.xml"):
            try:
                tree = ET.parse(slide_file)
                root = tree.getroot()
                
                # Analyze colors, fonts, and sizes in actual use
                self._analyze_text_elements(root)
                self._analyze_shape_styles(root)
                
            except Exception as e:
                print(f"Warning: Could not analyze slide {slide_file}: {e}")
    
    def _analyze_text_elements(self, root):
        """Analyze text elements for typography patterns"""
        ns = {
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
            'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'
        }
        
        # Find all text properties
        for text_elem in root.xpath('.//a:t', namespaces=ns):
            # Look for parent paragraph and run properties
            run_props = text_elem.xpath('ancestor::a:r/a:rPr', namespaces=ns)
            para_props = text_elem.xpath('ancestor::a:p/a:pPr', namespaces=ns)
            
            if run_props:
                rpr = run_props[0]
                
                # Extract font information
                latin_font = rpr.find('.//a:latin', ns)
                if latin_font is not None:
                    font_name = latin_font.get('typeface', '')
                    if font_name and font_name != '+mn-lt' and font_name != '+mj-lt':
                        self.extracted_fonts[font_name] += 1
                
                # Extract font size
                size_attr = rpr.get('sz')
                if size_attr:
                    # Convert from hundredths of a point to points
                    size_pt = int(size_attr) / 100
                    self.extracted_sizes[f"{size_pt}pt"] += 1
                
                # Extract colors
                self._extract_color_from_props(rpr)
    
    def _analyze_shape_styles(self, root):
        """Analyze shape styling for color usage"""
        ns = {
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
            'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'
        }
        
        # Find shape properties
        for shape_props in root.xpath('.//a:spPr', namespaces=ns):
            self._extract_color_from_props(shape_props)
    
    def _extract_color_from_props(self, props_elem):
        """Extract color information from properties element"""
        ns = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
        
        # Look for sRGB colors
        for srgb in props_elem.xpath('.//a:srgbClr', namespaces=ns):
            color_val = srgb.get('val', '')
            if color_val:
                self.extracted_colors[f"#{color_val.upper()}"] += 1
        
        # Look for scheme colors (theme references)
        for scheme_clr in props_elem.xpath('.//a:schemeClr', namespaces=ns):
            scheme_val = scheme_clr.get('val', '')
            if scheme_val in self.THEME_COLORS:
                theme_name = self.THEME_COLORS[scheme_val]
                if theme_name in self.theme_info:
                    self.extracted_colors[self.theme_info[theme_name]] += 1
    
    def _extract_layout_patterns(self, pptx_dir: Path):
        """Extract common layout and spacing patterns"""
        layouts_dir = pptx_dir / "ppt" / "slideLayouts"
        
        if not layouts_dir.exists():
            return
            
        for layout_file in layouts_dir.glob("*.xml"):
            try:
                tree = ET.parse(layout_file)
                root = tree.getroot()
                
                # Analyze positioning and spacing
                self._analyze_positioning(root)
                
            except Exception as e:
                print(f"Warning: Could not analyze layout {layout_file}: {e}")
    
    def _analyze_positioning(self, root):
        """Analyze object positioning for spacing patterns"""
        ns = {
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
            'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'
        }
        
        positions = []
        
        # Find all positioned elements
        for transform in root.xpath('.//a:xfrm', namespaces=ns):
            off_elem = transform.find('a:off', ns)
            ext_elem = transform.find('a:ext', ns)
            
            if off_elem is not None and ext_elem is not None:
                x = int(off_elem.get('x', '0'))
                y = int(off_elem.get('y', '0'))
                w = int(ext_elem.get('cx', '0'))
                h = int(ext_elem.get('cy', '0'))
                
                positions.append({
                    'x': x, 'y': y, 'width': w, 'height': h
                })
        
        if positions:
            self.layout_patterns.extend(positions)
    
    def _compile_tokens(self) -> Dict:
        """Compile extracted data into design tokens format"""
        if self.output_format == 'stylestack':
            return self._compile_stylestack_format()
        elif self.output_format == 'w3c':
            return self._compile_w3c_format()
        else:
            return self._compile_stylestack_format()
    
    def _compile_stylestack_format(self) -> Dict:
        """Compile in StyleStack format"""
        tokens = {
            "stylestack": {
                "version": "1.0.0",
                "extracted": True,
                "extraction_timestamp": "",
                "tokens": {}
            }
        }
        
        # Compile color palette
        if self.extracted_colors:
            sorted_colors = self.extracted_colors.most_common(10)
            color_tokens = {}
            
            for i, (color, usage) in enumerate(sorted_colors):
                if i == 0:
                    color_tokens["primary"] = {"value": color, "usage_count": usage}
                elif i == 1:
                    color_tokens["secondary"] = {"value": color, "usage_count": usage}
                else:
                    color_tokens[f"accent_{i-1}"] = {"value": color, "usage_count": usage}
            
            # Add theme colors
            for name, color in self.theme_info.items():
                if name not in ['lt1', 'dk1', 'lt2', 'dk2']:  # Skip text/background pairs
                    color_tokens[f"theme_{name}"] = {"value": color, "type": "theme"}
            
            tokens["stylestack"]["tokens"]["colors"] = color_tokens
        
        # Compile typography
        if self.extracted_fonts:
            font_family = self.extracted_fonts.most_common(1)[0][0]
            
            # Group sizes by usage to determine hierarchy
            common_sizes = self.extracted_sizes.most_common(5)
            size_tokens = {}
            
            for i, (size, usage) in enumerate(common_sizes):
                if '44' in size or '48' in size:  # Likely H1
                    size_tokens["h1"] = {"font_size": size, "usage_count": usage}
                elif '36' in size or '32' in size:  # Likely H2
                    size_tokens["h2"] = {"font_size": size, "usage_count": usage}
                elif '24' in size or '28' in size:  # Likely H3
                    size_tokens["h3"] = {"font_size": size, "usage_count": usage}
                elif '20' in size or '18' in size:  # Likely body
                    size_tokens["body"] = {"font_size": size, "usage_count": usage}
                else:
                    size_tokens[f"size_{i+1}"] = {"font_size": size, "usage_count": usage}
            
            tokens["stylestack"]["tokens"]["typography"] = {
                "font_family": {"value": font_family},
                "sizes": size_tokens
            }
        
        # Compile spacing (if we detected patterns)
        if self.layout_patterns:
            # Analyze common spacing patterns
            margins = self._analyze_common_margins()
            if margins:
                tokens["stylestack"]["tokens"]["spacing"] = {
                    "margins": margins,
                    "note": "Extracted from layout analysis"
                }
        
        # Compile logos and brand assets
        if self.extracted_images:
            logos = {}
            icons = {}
            other_images = {}
            
            for image in self.extracted_images:
                classification = image['classification']
                image_data = {
                    'filename': image['filename'],
                    'format': image['format'],
                    'size_bytes': image['size_bytes'],
                    'relative_path': image['relative_path']
                }
                
                if image['dimensions']:
                    image_data['dimensions'] = image['dimensions']
                
                if classification == 'primary_logo':
                    logos[image['stem']] = image_data
                elif classification in ['logo', 'icon']:
                    icons[image['stem']] = image_data
                else:
                    other_images[image['stem']] = image_data
            
            brand_assets = {}
            if logos:
                brand_assets['logos'] = logos
            if icons:
                brand_assets['icons'] = icons  
            if other_images:
                brand_assets['images'] = other_images
                
            if brand_assets:
                tokens["stylestack"]["tokens"]["brand_assets"] = brand_assets
        
        return tokens
    
    def _compile_w3c_format(self) -> Dict:
        """Compile in W3C Design Tokens Community Group format"""
        tokens = {}
        
        # W3C format has different structure
        if self.extracted_colors:
            colors = {}
            for i, (color, usage) in enumerate(self.extracted_colors.most_common(6)):
                key = "primary" if i == 0 else f"color-{i+1}"
                colors[key] = {
                    "$value": color,
                    "$type": "color",
                    "$description": f"Extracted color (used {usage} times)"
                }
            tokens["color"] = colors
        
        return tokens
    
    def _extract_logos_and_images(self, pptx_dir: Path):
        """Extract logos and brand images from OOXML package"""
        media_dir = pptx_dir / "ppt" / "media"
        
        if not media_dir.exists():
            return
            
        # Analyze image usage patterns
        self._analyze_image_usage(pptx_dir)
        
        # Extract image files and metadata
        for image_file in media_dir.iterdir():
            if image_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.svg', '.gif']:
                try:
                    image_info = self._analyze_image_file(image_file)
                    if image_info:
                        self.extracted_images.append(image_info)
                except Exception as e:
                    print(f"Warning: Could not analyze image {image_file}: {e}")
    
    def _analyze_image_usage(self, pptx_dir: Path):
        """Analyze how images are used throughout the presentation"""
        ns = {
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
            'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
            'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
        }
        
        # Check slide masters for logo usage
        masters_dir = pptx_dir / "ppt" / "slideMasters"
        if masters_dir.exists():
            for master_file in masters_dir.glob("*.xml"):
                self._count_image_references(master_file, "master", ns)
        
        # Check slide layouts for logo usage  
        layouts_dir = pptx_dir / "ppt" / "slideLayouts"
        if layouts_dir.exists():
            for layout_file in layouts_dir.glob("*.xml"):
                self._count_image_references(layout_file, "layout", ns)
        
        # Check actual slides
        slides_dir = pptx_dir / "ppt" / "slides"
        if slides_dir.exists():
            for slide_file in slides_dir.glob("*.xml"):
                self._count_image_references(slide_file, "slide", ns)
    
    def _count_image_references(self, xml_file: Path, context: str, ns: dict):
        """Count references to images in XML files"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Look for image references (blip elements)
            for blip in root.xpath('.//a:blip', namespaces=ns):
                embed_id = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                if embed_id:
                    # Weight master/layout usage higher (likely logos)
                    weight = 3 if context == "master" else 2 if context == "layout" else 1
                    self.image_usage[embed_id] += weight
                    
        except Exception as e:
            print(f"Warning: Could not analyze {xml_file}: {e}")
    
    def _analyze_image_file(self, image_file: Path) -> Dict:
        """Analyze individual image file for logo characteristics"""
        file_size = image_file.stat().st_size
        file_format = image_file.suffix.lower()[1:]  # Remove dot
        file_name = image_file.stem
        
        # Try to get image dimensions
        dimensions = self._get_image_dimensions(image_file)
        
        # Determine likely image type based on characteristics
        image_type = self._classify_image_type(file_name, file_format, file_size, dimensions)
        
        return {
            'filename': image_file.name,
            'stem': file_name,
            'format': file_format,
            'size_bytes': file_size,
            'dimensions': dimensions,
            'classification': image_type,
            'relative_path': f"ppt/media/{image_file.name}"
        }
    
    def _get_image_dimensions(self, image_file: Path) -> Optional[Dict]:
        """Get image dimensions if possible"""
        try:
            if image_file.suffix.lower() == '.svg':
                # For SVG, try to parse viewBox or width/height
                with open(image_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Look for viewBox
                    viewbox_match = re.search(r'viewBox=["\'][\d\s.]+\s+(\d+)\s+(\d+)["\']', content)
                    if viewbox_match:
                        return {
                            'width': int(viewbox_match.group(1)),
                            'height': int(viewbox_match.group(2)),
                            'unit': 'svg_units'
                        }
                    
                    # Look for width/height attributes
                    width_match = re.search(r'width=["\'](\d+)', content)
                    height_match = re.search(r'height=["\'](\d+)', content)
                    if width_match and height_match:
                        return {
                            'width': int(width_match.group(1)),
                            'height': int(height_match.group(1)),
                            'unit': 'px'
                        }
            else:
                # For raster images, would need PIL/Pillow
                # For now, return None and let classification work without dimensions
                return None
                
        except Exception:
            return None
    
    def _classify_image_type(self, filename: str, format: str, size_bytes: int, dimensions: Dict = None) -> str:
        """Classify image as logo, icon, photo, etc."""
        filename_lower = filename.lower()
        
        # Logo indicators
        logo_keywords = ['logo', 'brand', 'company', 'corp', 'mark', 'symbol']
        if any(keyword in filename_lower for keyword in logo_keywords):
            return 'primary_logo'
        
        # Icon indicators
        icon_keywords = ['icon', 'favicon', 'symbol']
        if any(keyword in filename_lower for keyword in icon_keywords):
            return 'icon'
        
        # SVG usually indicates logos or icons
        if format == 'svg':
            if dimensions and dimensions.get('width', 0) < 100:
                return 'icon'
            else:
                return 'logo'
        
        # Small images are likely icons
        if dimensions:
            width = dimensions.get('width', 0)
            height = dimensions.get('height', 0)
            if width <= 64 and height <= 64:
                return 'icon'
            elif max(width, height) <= 200:
                return 'logo'
        
        # Large files are likely photos/graphics
        if size_bytes > 500000:  # 500KB
            return 'graphic'
        
        # Default classification
        return 'image'
    
    def _analyze_common_margins(self) -> Dict:
        """Analyze positioning data for common margins"""
        if not self.layout_patterns:
            return {}
            
        # Convert EMUs to points (1 point = 12700 EMUs)
        margins = []
        for pos in self.layout_patterns:
            left_margin = pos['x'] / 12700
            top_margin = pos['y'] / 12700
            margins.append({'left': left_margin, 'top': top_margin})
        
        # Find most common values
        common_left = Counter(round(m['left']) for m in margins).most_common(1)
        common_top = Counter(round(m['top']) for m in margins).most_common(1)
        
        result = {}
        if common_left:
            result["left"] = f"{common_left[0][0]}pt"
        if common_top:
            result["top"] = f"{common_top[0][0]}pt"
            
        return result
    
    def extract_and_save(self, pptx_path: Path, output_path: Path = None, extract_assets: bool = False, assets_dir: Path = None) -> Dict:
        """
        Extract tokens and save to file
        
        Args:
            pptx_path: Input PowerPoint file
            output_path: Output JSON/JSON file (optional)
            extract_assets: Whether to extract image files
            assets_dir: Directory to save extracted images (optional)
            
        Returns:
            Extracted tokens dictionary
        """
        tokens = self.extract_from_file(pptx_path)
        
        # Extract actual image files if requested
        if extract_assets and self.extracted_images:
            if not assets_dir:
                assets_dir = output_path.parent / "assets" if output_path else Path("assets")
            
            assets_dir.mkdir(parents=True, exist_ok=True)
            self._extract_image_files(pptx_path, assets_dir, tokens)
        
        if output_path:
            # Determine format from extension
            if output_path.suffix.lower() in ['.json', '.yml']:
                import json
                with open(output_path, 'w') as f:
                    json.dump(tokens, f, indent=2, default_flow_style=False)
            else:
                with open(output_path, 'w') as f:
                    json.dump(tokens, f, indent=2)
            print(f"✅ Extracted tokens saved to {output_path}")
        
        return tokens
    
    def _extract_image_files(self, pptx_path: Path, assets_dir: Path, tokens: Dict):
        """Extract actual image files from OOXML package"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract PPTX again to get image files
            with zipfile.ZipFile(pptx_path, 'r') as zip_file:
                zip_file.extractall(temp_dir)
            
            temp_path = Path(temp_dir)
            media_dir = temp_path / "ppt" / "media"
            
            if not media_dir.exists():
                return
            
            extracted_count = 0
            brand_assets = tokens.get("stylestack", {}).get("tokens", {}).get("brand_assets", {})
            
            # Create category subdirectories
            for category in ['logos', 'icons', 'images']:
                if category in brand_assets:
                    (assets_dir / category).mkdir(parents=True, exist_ok=True)
            
            # Copy image files to appropriate directories
            for category, images in brand_assets.items():
                for stem, image_data in images.items():
                    src_file = media_dir / image_data['filename']
                    if src_file.exists():
                        # Create clean filename
                        clean_name = f"{stem}.{image_data['format']}"
                        dest_file = assets_dir / category / clean_name
                        
                        import shutil
                        shutil.copy2(src_file, dest_file)
                        
                        # Update token with extracted file path
                        image_data['extracted_path'] = str(dest_file.relative_to(assets_dir.parent))
                        extracted_count += 1
            
            print(f"✅ Extracted {extracted_count} image files to {assets_dir}")
    
    def analyze_brand_consistency(self, tokens: Dict) -> Dict:
        """
        Analyze brand consistency in extracted tokens
        
        Returns:
            Analysis report with recommendations
        """
        analysis = {
            "consistency_score": 0.0,
            "recommendations": [],
            "warnings": []
        }
        
        if "colors" in tokens.get("stylestack", {}).get("tokens", {}):
            colors = tokens["stylestack"]["tokens"]["colors"]
            
            # Check for too many colors (brand inconsistency)
            if len(colors) > 8:
                analysis["warnings"].append(
                    f"Found {len(colors)} different colors - consider consolidating for brand consistency"
                )
                analysis["consistency_score"] -= 0.2
            
            # Check for very similar colors (might be inconsistent usage)
            color_values = [data["value"] for data in colors.values() if isinstance(data, dict) and "value" in data]
            similar_colors = self._find_similar_colors(color_values)
            
            if similar_colors:
                analysis["recommendations"].extend([
                    f"Colors {c1} and {c2} are very similar - consider using one consistently"
                    for c1, c2 in similar_colors
                ])
        
        # Check typography consistency
        if "typography" in tokens.get("stylestack", {}).get("tokens", {}):
            typography = tokens["stylestack"]["tokens"]["typography"]
            
            # Check for font consistency
            if "font_family" in typography:
                font = typography["font_family"]["value"]
                if "," in font:  # Multiple fonts might indicate inconsistency
                    analysis["recommendations"].append(
                        f"Multiple fonts detected ({font}) - consider standardizing on one primary font"
                    )
        
        # Overall score
        base_score = 0.8
        analysis["consistency_score"] = max(0.0, base_score + analysis["consistency_score"])
        
        return analysis
    
    def _find_similar_colors(self, color_list: List[str]) -> List[Tuple[str, str]]:
        """Find colors that are very similar (might indicate inconsistency)"""
        similar_pairs = []
        
        for i, color1 in enumerate(color_list):
            for color2 in color_list[i+1:]:
                if self._color_similarity(color1, color2) > 0.9:
                    similar_pairs.append((color1, color2))
        
        return similar_pairs
    
    def _color_similarity(self, color1: str, color2: str) -> float:
        """Calculate similarity between two hex colors"""
        try:
            # Convert hex to RGB
            rgb1 = tuple(int(color1[1:][i:i+2], 16) for i in (0, 2, 4))
            rgb2 = tuple(int(color2[1:][i:i+2], 16) for i in (0, 2, 4))
            
            # Convert to HSV for better perceptual comparison
            hsv1 = colorsys.rgb_to_hsv(rgb1[0]/255, rgb1[1]/255, rgb1[2]/255)
            hsv2 = colorsys.rgb_to_hsv(rgb2[0]/255, rgb2[1]/255, rgb2[2]/255)
            
            # Calculate distance in HSV space
            h_diff = min(abs(hsv1[0] - hsv2[0]), 1 - abs(hsv1[0] - hsv2[0]))
            s_diff = abs(hsv1[1] - hsv2[1])
            v_diff = abs(hsv1[2] - hsv2[2])
            
            # Weight hue more heavily than saturation/value
            distance = (h_diff * 0.5) + (s_diff * 0.25) + (v_diff * 0.25)
            
            return 1 - distance
            
        except Exception:
            return 0.0


# CLI interface
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract design tokens from Office and OpenOffice files')
    parser.add_argument('input', help='Input Office file (.pptx/.potx/.ppsx/.odp/.otp/.ods/.ots/.odt/.ott)')
    parser.add_argument('--output', '-o', help='Output JSON/JSON file')
    parser.add_argument('--format', choices=['stylestack', 'w3c', 'figma'], 
                       default='stylestack', help='Output format')
    parser.add_argument('--analyze', '-a', action='store_true', 
                       help='Include brand consistency analysis')
    parser.add_argument('--extract-assets', action='store_true',
                       help='Extract logo and image files')
    parser.add_argument('--assets-dir', help='Directory for extracted assets')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Create extractor
    extractor = DesignTokenExtractor(output_format=args.format)
    
    # Extract tokens
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path.with_suffix('.design-tokens.json')
    
    print(f"🔍 Extracting design tokens from {input_path}")
    
    # Handle asset extraction parameters
    assets_dir = Path(args.assets_dir) if args.assets_dir else None
    tokens = extractor.extract_and_save(
        input_path, 
        output_path, 
        extract_assets=args.extract_assets,
        assets_dir=assets_dir
    )
    
    # Display summary
    if args.verbose:
        token_data = tokens.get("stylestack", {}).get("tokens", {})
        
        if "colors" in token_data:
            print(f"   Colors found: {len(token_data['colors'])}")
            
        if "typography" in token_data:
            typography = token_data["typography"]
            if "font_family" in typography:
                print(f"   Primary font: {typography['font_family']['value']}")
            if "sizes" in typography:
                print(f"   Font sizes: {len(typography['sizes'])}")
        
        if "brand_assets" in token_data:
            brand_assets = token_data["brand_assets"]
            total_assets = sum(len(assets) for assets in brand_assets.values())
            print(f"   Brand assets: {total_assets} found")
            for category, assets in brand_assets.items():
                if assets:
                    print(f"     {category}: {len(assets)}")
    
    # Display asset extraction results
    if args.extract_assets:
        print(f"\n📁 Assets extracted to: {assets_dir or 'assets/'}")
    
    # Run analysis if requested
    if args.analyze:
        print("\n🔬 Analyzing brand consistency...")
        analysis = extractor.analyze_brand_consistency(tokens)
        
        print(f"   Consistency score: {analysis['consistency_score']:.1f}/1.0")
        
        if analysis['recommendations']:
            print("\n💡 Recommendations:")
            for rec in analysis['recommendations']:
                print(f"   • {rec}")
        
        if analysis['warnings']:
            print("\n⚠️  Warnings:")
            for warning in analysis['warnings']:
                print(f"   • {warning}")
    
    print("✅ Extraction complete!")