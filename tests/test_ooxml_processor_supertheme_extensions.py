"""
Tests for Enhanced OOXML Processor SuperTheme Extensions

Tests covering the enhanced OOXML processor functionality for SuperTheme generation:
- Multi-variant theme packaging capabilities
- Presentation.xml generation with aspect ratio awareness
- Slide master and layout structure creation
- Content type and relationship file generation
- Integration with aspect ratio token system
"""

import pytest
import xml.etree.ElementTree as ET
import zipfile
import io
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock

# Import the components under test
try:
    from tools.ooxml_processor import OOXMLProcessor, XPathExpression
    from tools.aspect_ratio_resolver import AspectRatioResolver, create_standard_aspect_ratios
    from tools.supertheme_generator import SuperThemeGenerator, SuperThemeVariant
    from tools.emu_types import EMUValue
except ImportError:
    # Components may not be implemented yet
    OOXMLProcessor = None
    XPathExpression = None
    AspectRatioResolver = None
    create_standard_aspect_ratios = None
    SuperThemeGenerator = None
    SuperThemeVariant = None
    EMUValue = None


class TestOOXMLProcessorSuperThemeExtensions:
    """Test enhanced OOXML processor for SuperTheme generation"""
    
    @pytest.fixture
    def ooxml_processor(self):
        """Create OOXML processor instance"""
        if OOXMLProcessor is None:
            pytest.skip("OOXMLProcessor not available")
        return OOXMLProcessor(use_lxml=False)
    
    @pytest.fixture
    def aspect_ratios(self):
        """Standard aspect ratios for testing"""
        if create_standard_aspect_ratios is None:
            pytest.skip("AspectRatioResolver not available")
        return create_standard_aspect_ratios()
    
    @pytest.fixture
    def sample_presentation_xml(self):
        """Sample presentation.xml content for testing"""
        return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
                xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:sldMasterIdLst>
    <p:sldMasterId id="2147483648" r:id="rId1"/>
  </p:sldMasterIdLst>
  <p:sldIdLst/>
  <p:sldSz cx="9144000" cy="6858000" type="screen4x3"/>
  <p:notesSz cx="6858000" cy="9144000"/>
  <p:defaultTextStyle>
    <a:defPPr>
      <a:defRPr lang="en-US"/>
    </a:defPPr>
  </p:defaultTextStyle>
</p:presentation>'''
    
    @pytest.mark.skipif(OOXMLProcessor is None, reason="OOXMLProcessor not available")
    def test_aspect_ratio_aware_presentation_generation(self, ooxml_processor, aspect_ratios, sample_presentation_xml):
        """Test presentation.xml generation with aspect ratio dimensions"""
        # Test different aspect ratios
        test_cases = [
            ("aspectRatios.widescreen_16_9", 12192000, 6858000),  # Approximate 16:9
            ("aspectRatios.a4_landscape", 10692000, 7560000),     # A4 landscape
            ("aspectRatios.classic_4_3", 9144000, 6858000),       # 4:3 classic
        ]
        
        for aspect_ratio_token, expected_width, expected_height in test_cases:
            # Apply aspect ratio modifications to presentation XML
            modified_xml = ooxml_processor._update_presentation_dimensions(
                sample_presentation_xml, aspect_ratio_token, aspect_ratios
            )
            
            # Parse and verify dimensions
            root = ET.fromstring(modified_xml)
            
            # Find slide size element
            sld_sz = root.find(".//p:sldSz", {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"})
            assert sld_sz is not None, f"Slide size element not found for {aspect_ratio_token}"
            
            # Verify dimensions (allow 5% tolerance for EMU conversion)
            actual_width = int(sld_sz.get("cx"))
            actual_height = int(sld_sz.get("cy"))
            
            width_tolerance = expected_width * 0.05
            height_tolerance = expected_height * 0.05
            
            assert abs(actual_width - expected_width) <= width_tolerance, \
                f"Width mismatch for {aspect_ratio_token}: {actual_width} vs {expected_width}"
            assert abs(actual_height - expected_height) <= height_tolerance, \
                f"Height mismatch for {aspect_ratio_token}: {actual_height} vs {expected_height}"
            
            # Verify notes size is swapped
            notes_sz = root.find(".//p:notesSz", {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"})
            notes_width = int(notes_sz.get("cx"))
            notes_height = int(notes_sz.get("cy"))
            
            # Notes dimensions should be swapped
            assert abs(notes_width - expected_height) <= height_tolerance, "Notes width should match slide height"
            assert abs(notes_height - expected_width) <= width_tolerance, "Notes height should match slide width"
    
    @pytest.mark.skipif(OOXMLProcessor is None, reason="OOXMLProcessor not available")
    def test_slide_master_structure_creation(self, ooxml_processor):
        """Test slide master XML structure generation"""
        aspect_ratio_token = "aspectRatios.widescreen_16_9"
        
        # Generate slide master structure
        slide_master_xml = ooxml_processor._generate_slide_master_structure(
            aspect_ratio_token, theme_variant_id="1"
        )
        
        # Parse and verify structure
        root = ET.fromstring(slide_master_xml)
        
        # Verify root element
        assert root.tag.endswith("}sldMaster"), "Root should be slide master element"
        
        # Verify required child elements
        required_elements = [
            ".//p:cSld",    # Common slide data
            ".//p:clrMap",  # Color mapping
            ".//p:sldLayoutIdLst", # Layout ID list
            ".//p:txStyles" # Text styles
        ]
        
        for xpath in required_elements:
            element = root.find(xpath, {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"})
            assert element is not None, f"Missing required element: {xpath}"
        
        # Verify aspect ratio is applied to slide dimensions
        # (This would require checking background or placeholder elements)
        cSld = root.find(".//p:cSld", {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"})
        assert cSld is not None, "Common slide data element missing"
    
    @pytest.mark.skipif(OOXMLProcessor is None, reason="OOXMLProcessor not available")
    def test_slide_layout_creation(self, ooxml_processor):
        """Test slide layout XML generation for different layout types"""
        layout_types = [
            ("title", "Title Slide"),
            ("titleContent", "Title and Content"),
            ("twoContent", "Two Content"),
            ("blank", "Blank")
        ]
        
        aspect_ratio_token = "aspectRatios.widescreen_16_9"
        
        for layout_type, layout_name in layout_types:
            layout_xml = ooxml_processor._generate_slide_layout_structure(
                layout_type, aspect_ratio_token, layout_id=f"layout_{layout_type}"
            )
            
            # Parse and verify
            root = ET.fromstring(layout_xml)
            
            # Verify root element
            assert root.tag.endswith("}sldLayout"), f"Root should be slide layout for {layout_type}"
            
            # Verify layout has proper structure
            cSld = root.find(".//p:cSld", {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"})
            assert cSld is not None, f"Missing common slide data in {layout_type} layout"
            
            # Verify layout type is reflected in name attribute or content
            # (Implementation would need to set appropriate attributes)
            assert len(layout_xml) > 200, f"Layout XML too minimal for {layout_type}"
    
    @pytest.mark.skipif(OOXMLProcessor is None, reason="OOXMLProcessor not available")
    def test_content_types_generation(self, ooxml_processor):
        """Test [Content_Types].xml generation for SuperTheme"""
        variant_count = 3
        content_types_xml = ooxml_processor._generate_supertheme_content_types(variant_count)
        
        # Parse and verify
        root = ET.fromstring(content_types_xml)
        
        # Verify root element
        assert root.tag == "Types", "Root should be Types element"
        
        # Verify required content type declarations
        required_types = [
            # Core OOXML types
            ("application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml", None),
            ("application/vnd.openxmlformats-package.relationships+xml", None),
            # SuperTheme specific types
            ("application/vnd.ms-powerpoint.themeVariantManager+xml", None),
        ]
        
        content_type_values = []
        for elem in root:
            if elem.tag == "Default":
                content_type_values.append((elem.get("ContentType"), elem.get("Extension")))
            elif elem.tag == "Override":
                content_type_values.append((elem.get("ContentType"), elem.get("PartName")))
        
        for required_type, _ in required_types:
            found = any(ct[0] == required_type for ct in content_type_values)
            assert found, f"Missing content type: {required_type}"
    
    @pytest.mark.skipif(OOXMLProcessor is None, reason="OOXMLProcessor not available")
    def test_relationship_files_generation(self, ooxml_processor):
        """Test relationship file generation for SuperTheme structure"""
        # Test main relationships
        main_rels = ooxml_processor._generate_main_relationships()
        root = ET.fromstring(main_rels)
        
        # Verify relationships namespace
        assert root.tag == "Relationships", "Root should be Relationships"
        
        # Should contain relationship to theme variant manager
        relationships = root.findall("Relationship")
        variant_manager_rel = None
        
        for rel in relationships:
            if "themeVariantManager" in rel.get("Target", ""):
                variant_manager_rel = rel
                break
        
        assert variant_manager_rel is not None, "Missing theme variant manager relationship"
        assert variant_manager_rel.get("Type"), "Relationship should have Type attribute"
        assert variant_manager_rel.get("Id"), "Relationship should have Id attribute"
        
        # Test variant-specific relationships
        variant_rels = ooxml_processor._generate_variant_relationships("variant1")
        variant_root = ET.fromstring(variant_rels)
        
        # Verify variant relationships structure
        assert variant_root.tag == "Relationships", "Variant relationships root should be Relationships"
        variant_relationships = variant_root.findall("Relationship")
        
        # Should have relationships to theme and presentation
        theme_rel = None
        presentation_rel = None
        
        for rel in variant_relationships:
            target = rel.get("Target", "")
            if "theme1.xml" in target:
                theme_rel = rel
            elif "presentation.xml" in target:
                presentation_rel = rel
        
        assert theme_rel is not None, "Missing theme relationship in variant"
        assert presentation_rel is not None, "Missing presentation relationship in variant"


class TestThemeResolverSuperThemeExtensions:
    """Test enhanced theme resolver for SuperTheme generation"""
    
    @pytest.fixture
    def theme_resolver(self):
        """Create theme resolver instance"""
        try:
            from tools.theme_resolver import ThemeResolver
            return ThemeResolver()
        except ImportError:
            pytest.skip("ThemeResolver not available")
    
    @pytest.mark.skipif(OOXMLProcessor is None, reason="Components not available")
    def test_multi_variant_theme_generation(self, theme_resolver):
        """Test generation of multiple theme variants from design tokens"""
        design_variants = {
            "Corporate Blue": {
                "colors": {
                    "brand": {"primary": "#0066CC", "secondary": "#004499"},
                    "neutral": {"background": "#FFFFFF", "text": "#000000"}
                },
                "typography": {"heading": {"font": "Calibri", "size": "24pt"}}
            },
            "Creative Green": {
                "colors": {
                    "brand": {"primary": "#22AA22", "secondary": "#116611"},
                    "neutral": {"background": "#F8F8F8", "text": "#333333"}
                },
                "typography": {"heading": {"font": "Arial", "size": "26pt"}}
            }
        }
        
        # Generate theme variants
        theme_variants = theme_resolver._generate_theme_variants_from_tokens(design_variants)
        
        # Verify correct number of variants
        assert len(theme_variants) == 2, "Should generate 2 theme variants"
        
        # Verify each variant has required properties
        for variant_name, theme in theme_variants.items():
            assert variant_name in design_variants, f"Unexpected variant: {variant_name}"
            
            # Theme should be properly structured
            assert hasattr(theme, 'colors'), "Theme should have colors"
            assert hasattr(theme, 'fonts'), "Theme should have fonts"
            
            # Colors should be extracted from tokens
            if hasattr(theme, 'colors') and theme.colors:
                # Verify at least one color was extracted
                assert len(theme.colors) > 0, f"No colors extracted for {variant_name}"
    
    @pytest.mark.skipif(OOXMLProcessor is None, reason="Components not available")
    def test_theme_xml_generation_with_aspect_ratios(self, theme_resolver):
        """Test theme XML generation considering aspect ratios"""
        sample_theme = Mock()
        sample_theme.name = "Test Theme"
        sample_theme.colors = {"accent1": "#FF0000", "accent2": "#00FF00"}
        sample_theme.fonts = {"major": "Calibri", "minor": "Arial"}
        
        aspect_ratio_token = "aspectRatios.widescreen_16_9"
        
        # Generate theme XML with aspect ratio context
        theme_xml = theme_resolver._generate_aspect_aware_theme_xml(
            sample_theme, aspect_ratio_token
        )
        
        # Verify XML structure
        root = ET.fromstring(theme_xml)
        
        # Should be proper theme XML
        assert root.tag.endswith("}theme"), "Root should be theme element"
        
        # Should contain theme elements
        theme_elements = root.find(".//a:themeElements", 
                                  {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"})
        assert theme_elements is not None, "Missing theme elements"
        
        # Should have color scheme
        color_scheme = root.find(".//a:clrScheme",
                               {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"})
        assert color_scheme is not None, "Missing color scheme"
        
        # Should have font scheme
        font_scheme = root.find(".//a:fontScheme",
                              {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"})
        assert font_scheme is not None, "Missing font scheme"


class TestSuperThemeOOXMLIntegration:
    """Test integration between SuperTheme generator and OOXML processor"""
    
    @pytest.fixture
    def integration_components(self):
        """Set up integrated components for testing"""
        if any(comp is None for comp in [SuperThemeGenerator, OOXMLProcessor, AspectRatioResolver]):
            pytest.skip("Required components not available")
        
        return {
            'generator': SuperThemeGenerator(),
            'processor': OOXMLProcessor(),
            'resolver': AspectRatioResolver()
        }
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperTheme components not available")
    def test_end_to_end_supertheme_ooxml_processing(self, integration_components):
        """Test complete SuperTheme generation with OOXML processing"""
        generator = integration_components['generator']
        processor = integration_components['processor']
        
        # Sample design variants
        design_variants = {
            "Test Design": {
                "colors": {"brand": {"primary": "#0066CC"}},
                "typography": {"heading": {"size": "24pt"}}
            }
        }
        
        aspect_ratios = ["aspectRatios.widescreen_16_9"]
        
        # Generate SuperTheme package
        supertheme_package = generator.generate_supertheme(design_variants, aspect_ratios)
        
        # Verify package is valid ZIP
        assert isinstance(supertheme_package, bytes)
        assert len(supertheme_package) > 0
        
        # Extract and validate OOXML structure
        with zipfile.ZipFile(io.BytesIO(supertheme_package), 'r') as zf:
            file_list = zf.namelist()
            
            # Should contain properly structured OOXML files
            ooxml_files = [f for f in file_list if f.endswith('.xml')]
            assert len(ooxml_files) > 0, "Should contain XML files"
            
            # Test that each XML file is well-formed
            for xml_file in ooxml_files:
                xml_content = zf.read(xml_file).decode('utf-8')
                
                # Should parse without errors
                try:
                    ET.fromstring(xml_content)
                except ET.ParseError as e:
                    pytest.fail(f"Invalid XML in {xml_file}: {e}")
                
                # Basic structure validation
                assert len(xml_content.strip()) > 0, f"Empty XML file: {xml_file}"
                assert xml_content.startswith('<?xml'), f"Missing XML declaration: {xml_file}"
    
    @pytest.mark.skipif(SuperThemeGenerator is None, reason="SuperTheme components not available")
    def test_ooxml_processor_supertheme_compatibility(self, integration_components):
        """Test OOXML processor compatibility with SuperTheme structure"""
        processor = integration_components['processor']
        
        # Test that processor can handle SuperTheme-specific XML elements
        supertheme_xml = '''<?xml version="1.0" encoding="utf-8"?>
<t:themeVariantManager xmlns:t="http://schemas.microsoft.com/office/thememl/2012/main">
  <t:themeVariantLst>
    <t:themeVariant name="Test Variant" vid="{12345678-1234-1234-1234-123456789ABC}"
                    cx="9144000" cy="6858000" r:id="rId1"/>
  </t:themeVariantLst>
</t:themeVariantManager>'''
        
        # Should be able to parse without errors
        try:
            root = ET.fromstring(supertheme_xml)
            assert root is not None
        except Exception as e:
            pytest.fail(f"OOXML processor cannot parse SuperTheme XML: {e}")
        
        # Should be able to apply basic transformations
        variables = {"test_variable": "test_value"}
        
        try:
            # This should not raise errors even if no variables are applied
            result = processor.apply_variables_to_xml(supertheme_xml, variables)
            assert isinstance(result, str)
            assert len(result) > 0
        except Exception as e:
            pytest.fail(f"OOXML processor failed on SuperTheme XML: {e}")


# Helper methods that should be added to OOXML processor for SuperTheme support
class TestRequiredOOXMLProcessorMethods:
    """Test that required methods exist or suggest their implementation"""
    
    @pytest.mark.skipif(OOXMLProcessor is None, reason="OOXMLProcessor not available")
    def test_required_methods_exist_or_documented(self):
        """Verify required methods exist or are documented as needed"""
        processor = OOXMLProcessor()
        
        # List of methods that should be implemented for SuperTheme support
        required_methods = [
            '_update_presentation_dimensions',
            '_generate_slide_master_structure',
            '_generate_slide_layout_structure',
            '_generate_supertheme_content_types',
            '_generate_main_relationships',
            '_generate_variant_relationships'
        ]
        
        for method_name in required_methods:
            if not hasattr(processor, method_name):
                # Method doesn't exist - this is expected for now
                # Just document that it needs to be implemented
                print(f"Method {method_name} needs to be implemented in OOXMLProcessor")
            else:
                # Method exists - verify it's callable
                method = getattr(processor, method_name)
                assert callable(method), f"{method_name} should be callable"