"""
Test suite for YAML-to-OOXML Patch Operations Engine

Tests the core XPath-based OOXML manipulation system that applies YAML patches
to Office template files (.potx, .dotx, .xltx).
"""

import unittest
import tempfile
import zipfile
import os
from pathlib import Path
from lxml import etree
from tools.yaml_ooxml_processor import YAMLPatchProcessor, PatchOperation, PatchError


class TestYAMLPatchProcessor(unittest.TestCase):
    """Test the core YAML patch processing functionality."""
    
    def setUp(self):
        """Set up test environment with sample OOXML content."""
        self.processor = YAMLPatchProcessor()
        
        # Sample PowerPoint slide XML for testing
        self.sample_slide_xml = """<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" 
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" 
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
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
                </a:xfrm>
            </p:grpSpPr>
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
                <p:spPr>
                    <a:xfrm>
                        <a:off x="1219200" y="685800"/>
                        <a:ext cx="9753600" cy="1371600"/>
                    </a:xfrm>
                    <a:prstGeom prst="rect"/>
                    <a:solidFill>
                        <a:srgbClr val="FF0000"/>
                    </a:solidFill>
                </p:spPr>
                <p:txBody>
                    <a:bodyPr/>
                    <a:lstStyle/>
                    <a:p>
                        <a:r>
                            <a:rPr lang="en-US" sz="4400"/>
                            <a:t>Sample Title</a:t>
                        </a:r>
                    </a:p>
                </p:txBody>
            </p:sp>
        </p:spTree>
    </p:cSld>
</p:sld>"""
        
        # Sample Word document.xml for testing
        self.sample_word_xml = """
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:pPr>
                <w:pStyle w:val="Heading1"/>
            </w:pPr>
            <w:r>
                <w:rPr>
                    <w:color w:val="000000"/>
                    <w:sz w:val="28"/>
                </w:rPr>
                <w:t>Sample Heading</w:t>
            </w:r>
        </w:p>
        <w:p>
            <w:r>
                <w:rPr>
                    <w:color w:val="333333"/>
                </w:rPr>
                <w:t>Sample paragraph text.</w:t>
            </w:r>
        </w:p>
    </w:body>
</w:document>"""

        # Sample theme.xml for testing
        self.sample_theme_xml = """
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">
    <a:themeElements>
        <a:clrScheme name="Office">
            <a:dk1>
                <a:sysClr val="windowText" lastClr="000000"/>
            </a:dk1>
            <a:lt1>
                <a:sysClr val="window" lastClr="FFFFFF"/>
            </a:lt1>
            <a:accent1>
                <a:srgbClr val="4F81BD"/>
            </a:accent1>
            <a:accent2>
                <a:srgbClr val="C0504D"/>
            </a:accent2>
        </a:clrScheme>
        <a:fontScheme name="Office">
            <a:majorFont>
                <a:latin typeface="Calibri"/>
            </a:majorFont>
            <a:minorFont>
                <a:latin typeface="Calibri"/>
            </a:minorFont>
        </a:fontScheme>
    </a:themeElements>
</a:theme>"""

    def test_set_operation_basic(self):
        """Test basic set operation on XML element."""
        xml_doc = etree.fromstring(self.sample_slide_xml)
        
        patch = {
            'operation': 'set',
            'target': '//a:srgbClr/@val',
            'value': '00FF00'
        }
        
        result = self.processor.apply_patch(xml_doc, patch)
        
        # Verify the color was changed
        color_elements = xml_doc.xpath('//a:srgbClr/@val', namespaces={
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
        })
        self.assertEqual(color_elements[0], '00FF00')

    def test_set_operation_element_text(self):
        """Test set operation on element text content."""
        xml_doc = etree.fromstring(self.sample_slide_xml)
        
        patch = {
            'operation': 'set',
            'target': '//a:t/text()',
            'value': 'New Title Text'
        }
        
        result = self.processor.apply_patch(xml_doc, patch)
        
        # Verify the text was changed
        text_elements = xml_doc.xpath('//a:t/text()', namespaces={
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
        })
        self.assertEqual(str(text_elements[0]), 'New Title Text')

    def test_insert_operation_new_element(self):
        """Test insert operation adding new XML element."""
        xml_doc = etree.fromstring(self.sample_theme_xml)
        
        patch = {
            'operation': 'insert',
            'target': '//a:clrScheme',
            'value': '<a:accent3><a:srgbClr val="9BBB59"/></a:accent3>',
            'position': 'append'
        }
        
        result = self.processor.apply_patch(xml_doc, patch)
        
        # Verify the new accent color was added
        accent3_elements = xml_doc.xpath('//a:accent3/a:srgbClr/@val', namespaces={
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
        })
        self.assertEqual(len(accent3_elements), 1)
        self.assertEqual(accent3_elements[0], '9BBB59')

    def test_insert_operation_positions(self):
        """Test insert operation with different positions."""
        xml_doc = etree.fromstring(self.sample_word_xml)
        
        # Test prepend
        patch_prepend = {
            'operation': 'insert',
            'target': '//w:body',
            'value': '<w:p><w:r><w:t>Prepended paragraph</w:t></w:r></w:p>',
            'position': 'prepend'
        }
        
        result = self.processor.apply_patch(xml_doc, patch_prepend)
        
        # Verify prepended content
        first_para = xml_doc.xpath('//w:body/w:p[1]//w:t/text()', namespaces={
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        })[0]
        self.assertEqual(str(first_para), 'Prepended paragraph')

    def test_extend_operation_array_values(self):
        """Test extend operation for array-like values."""
        xml_doc = etree.fromstring(self.sample_theme_xml)
        
        patch = {
            'operation': 'extend',
            'target': '//a:clrScheme',
            'value': [
                '<a:accent3><a:srgbClr val="9BBB59"/></a:accent3>',
                '<a:accent4><a:srgbClr val="8064A2"/></a:accent4>'
            ]
        }
        
        result = self.processor.apply_patch(xml_doc, patch)
        
        # Verify both accent colors were added
        accent3 = xml_doc.xpath('//a:accent3/a:srgbClr/@val', namespaces={
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
        })
        accent4 = xml_doc.xpath('//a:accent4/a:srgbClr/@val', namespaces={
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
        })
        
        self.assertEqual(len(accent3), 1)
        self.assertEqual(len(accent4), 1)
        self.assertEqual(accent3[0], '9BBB59')
        self.assertEqual(accent4[0], '8064A2')

    def test_merge_operation_attributes(self):
        """Test merge operation for combining attributes."""
        xml_doc = etree.fromstring(self.sample_word_xml)
        
        patch = {
            'operation': 'merge',
            'target': '//w:rPr[1]',
            'value': {
                'w:b': {'w:val': '1'},  # Add bold
                'w:i': {'w:val': '1'}   # Add italic
            }
        }
        
        result = self.processor.apply_patch(xml_doc, patch)
        
        # Verify bold and italic were added while preserving existing formatting
        rpr_element = xml_doc.xpath('//w:rPr[1]', namespaces={
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        })[0]
        
        # Should have original color + size + new bold + italic
        children = list(rpr_element)
        self.assertGreaterEqual(len(children), 4)  # color, sz, b, i
        
        # Verify bold and italic elements exist
        bold = xml_doc.xpath('//w:rPr[1]/w:b', namespaces={
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        })
        italic = xml_doc.xpath('//w:rPr[1]/w:i', namespaces={
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        })
        self.assertEqual(len(bold), 1)
        self.assertEqual(len(italic), 1)

    def test_relsadd_operation_relationships(self):
        """Test relsAdd operation for OOXML relationships."""
        # Create mock relationships XML
        rels_xml = """
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
        
        xml_doc = etree.fromstring(rels_xml)
        
        patch = {
            'operation': 'relsAdd',
            'target': '//Relationships',
            'value': {
                'Id': 'rId2',
                'Type': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image',
                'Target': 'media/image1.png'
            }
        }
        
        result = self.processor.apply_patch(xml_doc, patch)
        
        # Verify the new relationship was added
        new_rel = xml_doc.xpath('//Relationship[@Id="rId2"]', namespaces={
            '': 'http://schemas.openxmlformats.org/package/2006/relationships'
        })
        self.assertEqual(len(new_rel), 1)
        self.assertEqual(new_rel[0].get('Target'), 'media/image1.png')

    def test_xpath_targeting_precision(self):
        """Test precise XPath targeting with multiple matches."""
        xml_doc = etree.fromstring(self.sample_word_xml)
        
        # Target only the first paragraph's color
        patch = {
            'operation': 'set',
            'target': '//w:p[1]//w:color/@w:val',
            'value': '0066CC'
        }
        
        result = self.processor.apply_patch(xml_doc, patch)
        
        # Verify only first paragraph color changed
        colors = xml_doc.xpath('//w:color/@w:val', namespaces={
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        })
        self.assertEqual(colors[0], '0066CC')    # First paragraph changed
        self.assertEqual(colors[1], '333333')   # Second paragraph unchanged

    def test_operation_validation(self):
        """Test validation of patch operations."""
        xml_doc = etree.fromstring(self.sample_slide_xml)
        
        # Test invalid operation type
        invalid_patch = {
            'operation': 'invalid_op',
            'target': '//a:srgbClr/@val',
            'value': '00FF00'
        }
        
        with self.assertRaises(PatchError) as cm:
            self.processor.apply_patch(xml_doc, invalid_patch)
        
        self.assertIn('Unknown operation', str(cm.exception))

    def test_xpath_error_handling(self):
        """Test handling of invalid XPath expressions."""
        xml_doc = etree.fromstring(self.sample_slide_xml)
        
        # Invalid XPath syntax
        invalid_patch = {
            'operation': 'set',
            'target': '//a:srgbClr/@val[[[',  # Invalid XPath
            'value': '00FF00'
        }
        
        with self.assertRaises(PatchError) as cm:
            self.processor.apply_patch(xml_doc, invalid_patch)
        
        self.assertIn('XPath error', str(cm.exception))

    def test_missing_target_handling(self):
        """Test handling when XPath target doesn't exist."""
        xml_doc = etree.fromstring(self.sample_slide_xml)
        
        # Target that doesn't exist
        patch = {
            'operation': 'set',
            'target': '//nonexistent:element/@attr',
            'value': 'value'
        }
        
        with self.assertRaises(PatchError) as cm:
            self.processor.apply_patch(xml_doc, patch)
        
        self.assertIn('Target not found', str(cm.exception))

    def test_conflict_resolution(self):
        """Test conflict resolution when multiple patches target same element."""
        xml_doc = etree.fromstring(self.sample_slide_xml)
        
        # Apply conflicting patches
        patch1 = {
            'operation': 'set',
            'target': '//a:srgbClr/@val',
            'value': '00FF00'
        }
        
        patch2 = {
            'operation': 'set',
            'target': '//a:srgbClr/@val',
            'value': 'FF0000'
        }
        
        # Apply both patches - second should override
        self.processor.apply_patch(xml_doc, patch1)
        self.processor.apply_patch(xml_doc, patch2)
        
        # Verify final value is from second patch
        color_value = xml_doc.xpath('//a:srgbClr/@val', namespaces={
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
        })[0]
        self.assertEqual(color_value, 'FF0000')

    def test_namespace_handling(self):
        """Test proper namespace handling in XPath operations."""
        xml_doc = etree.fromstring(self.sample_slide_xml)
        
        # Use namespace prefixes in XPath
        patch = {
            'operation': 'set',
            'target': '//p:cNvPr[@id="2"]/@name',
            'value': 'Updated Title'
        }
        
        result = self.processor.apply_patch(xml_doc, patch)
        
        # Verify namespace-aware update
        name_attr = xml_doc.xpath('//p:cNvPr[@id="2"]/@name', namespaces={
            'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'
        })[0]
        self.assertEqual(name_attr, 'Updated Title')

    def test_batch_patch_application(self):
        """Test applying multiple patches in sequence."""
        xml_doc = etree.fromstring(self.sample_slide_xml)
        
        patches = [
            {
                'operation': 'set',
                'target': '//a:srgbClr/@val',
                'value': '0066CC'
            },
            {
                'operation': 'set', 
                'target': '//a:t/text()',
                'value': 'Updated Title'
            },
            {
                'operation': 'set',
                'target': '//a:rPr/@sz',
                'value': '2200'
            }
        ]
        
        results = self.processor.apply_patches(xml_doc, patches)
        
        # Verify all patches were applied
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertTrue(result.success)
        
        # Verify final state
        color = xml_doc.xpath('//a:srgbClr/@val', namespaces={
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
        })[0]
        text = xml_doc.xpath('//a:t/text()', namespaces={
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
        })[0]
        size = xml_doc.xpath('//a:rPr/@sz', namespaces={
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
        })[0]
        
        self.assertEqual(color, '0066CC')
        self.assertEqual(str(text), 'Updated Title')
        self.assertEqual(size, '2200')

    def test_emu_value_handling(self):
        """Test handling of EMU values in OOXML coordinates."""
        xml_doc = etree.fromstring(self.sample_slide_xml)
        
        # Update position coordinates with EMU values
        patches = [
            {
                'operation': 'set',
                'target': '//a:xfrm/a:off/@x',
                'value': '2438400'  # 2 inches in EMU
            },
            {
                'operation': 'set',
                'target': '//a:xfrm/a:off/@y', 
                'value': '1219200'  # 1 inch in EMU
            }
        ]
        
        results = self.processor.apply_patches(xml_doc, patches)
        
        # Verify EMU coordinates were set
        x_coord = xml_doc.xpath('//a:xfrm/a:off/@x', namespaces={
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
        })[0]
        y_coord = xml_doc.xpath('//a:xfrm/a:off/@y', namespaces={
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'  
        })[0]
        
        self.assertEqual(x_coord, '2438400')
        self.assertEqual(y_coord, '1219200')


class TestPatchOperation(unittest.TestCase):
    """Test the PatchOperation data class and validation."""
    
    def test_patch_operation_creation(self):
        """Test creating PatchOperation instances."""
        patch_data = {
            'operation': 'set',
            'target': '//a:srgbClr/@val',
            'value': '00FF00'
        }
        
        op = PatchOperation.from_dict(patch_data)
        
        self.assertEqual(op.operation, 'set')
        self.assertEqual(op.target, '//a:srgbClr/@val')
        self.assertEqual(op.value, '00FF00')

    def test_patch_operation_validation(self):
        """Test validation of patch operation parameters."""
        # Missing required fields
        with self.assertRaises(ValueError):
            PatchOperation.from_dict({})
        
        # Invalid operation type
        with self.assertRaises(ValueError):
            PatchOperation.from_dict({
                'operation': 'invalid',
                'target': '//element',
                'value': 'test'
            })

    def test_patch_operation_optional_fields(self):
        """Test handling of optional fields in patch operations."""
        patch_data = {
            'operation': 'insert',
            'target': '//parent',
            'value': '<child>content</child>',
            'position': 'after'
        }
        
        op = PatchOperation.from_dict(patch_data)
        
        self.assertEqual(op.position, 'after')
    


if __name__ == "__main__":
    unittest.main()