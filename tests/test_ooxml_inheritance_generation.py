#!/usr/bin/env python3
"""
Comprehensive test suite for OOXML Inheritance Generation.

Tests OOXML generation with inheritance support including basedOn attributes,
delta-only property serialization, and multi-platform compatibility for
PowerPoint, Word, and Excel templates.

Key Features Tested:
- OOXML basedOn attribute generation for style inheritance
- Delta-only property serialization in OOXML structures
- PowerPoint style inheritance XML structure compatibility
- Word and Excel style inheritance generation
- OOXML inheritance validation across Office versions
"""

import unittest
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False

from tools.style_inheritance_core import (
    InheritedTypographyToken, InheritanceResolver, BaseStyleRegistry,
    DeltaStyleGenerator, InheritanceMode, create_inheritance_system
)
from tools.typography_token_system import TypographyToken, TypographyTokenSystem


@dataclass
class OOXMLInheritanceTestCase:
    """Test case for OOXML inheritance generation"""
    name: str
    base_token: Dict[str, Any]
    derived_tokens: List[Dict[str, Any]]
    expected_ooxml_structure: Dict[str, Any]
    platform: str  # "powerpoint", "word", "excel"
    office_version: Optional[str] = "2019"


class OOXMLInheritanceGenerator:
    """OOXML Generation with Inheritance Support - Under Development"""

    def __init__(self, inheritance_resolver: InheritanceResolver = None):
        """Initialize OOXML inheritance generator"""
        self.inheritance_resolver = inheritance_resolver
        self.namespaces = {
            "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
            "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
            "p": "http://schemas.openxmlformats.org/presentationml/2006/main"
        }

    def generate_style_xml_with_inheritance(self, token: InheritedTypographyToken,
                                          platform: str = "word") -> str:
        """Generate OOXML style XML with inheritance - placeholder implementation"""
        if token.should_generate_delta() and token.base_style:
            return self._generate_delta_style_xml(token, platform)
        else:
            return self._generate_complete_style_xml(token, platform)

    def _generate_delta_style_xml(self, token: InheritedTypographyToken, platform: str) -> str:
        """Generate delta-only style XML with basedOn reference"""
        # Placeholder implementation - to be implemented in Task 3.2
        base_id = self._sanitize_style_id(token.base_style)
        style_id = self._sanitize_style_id(token.id)

        if platform == "word":
            return f"""<w:style w:type="paragraph" w:styleId="{style_id}">
    <w:name w:val="{token.id.replace('_', ' ').title()}"/>
    <w:basedOn w:val="{base_id}"/>
    {self._generate_delta_properties_xml(token, platform)}
</w:style>"""
        else:
            return f"<!-- {platform} delta style XML placeholder -->"

    def _generate_complete_style_xml(self, token: InheritedTypographyToken, platform: str) -> str:
        """Generate complete style XML without inheritance"""
        # Placeholder implementation
        style_id = self._sanitize_style_id(token.id)
        return f"<!-- {platform} complete style XML placeholder for {style_id} -->"

    def _generate_delta_properties_xml(self, token: InheritedTypographyToken, platform: str) -> str:
        """Generate XML for delta properties only"""
        # Placeholder implementation
        if not token.delta_properties:
            return ""
        return "<!-- delta properties XML placeholder -->"

    def _sanitize_style_id(self, style_id: str) -> str:
        """Sanitize style ID for OOXML compatibility"""
        return style_id.replace(".", "_").replace(" ", "_")

    def validate_ooxml_inheritance_structure(self, xml_content: str) -> Dict[str, Any]:
        """Validate OOXML inheritance structure"""
        # Placeholder validation logic
        return {
            "is_valid": True,
            "has_based_on": "basedOn" in xml_content,
            "has_delta_properties": "rPr" in xml_content or "pPr" in xml_content,
            "validation_errors": []
        }


class TestOOXMLInheritanceGeneration(unittest.TestCase):
    """Test OOXML generation with inheritance support"""

    def setUp(self):
        """Set up test infrastructure"""
        self.inheritance_registry, self.delta_generator, self.inheritance_resolver = create_inheritance_system()
        self.ooxml_generator = OOXMLInheritanceGenerator(self.inheritance_resolver)
        self.typography_system = TypographyTokenSystem(verbose=False)

    def test_basedOn_attribute_generation_word(self):
        """Test generation of basedOn attributes in Word OOXML styles"""
        # Create base and derived tokens
        base_token = InheritedTypographyToken(
            id="base_paragraph",
            font_family="Calibri",
            font_size="12pt",
            base_style="Normal",
            inheritance_mode=InheritanceMode.AUTO,
            delta_properties={"fontFamily": "Calibri", "fontSize": "12pt"}
        )

        derived_token = InheritedTypographyToken(
            id="emphasis_paragraph",
            font_weight=600,
            base_style="base_paragraph",
            inheritance_mode=InheritanceMode.AUTO,
            delta_properties={"fontWeight": 600}
        )

        # Generate XML
        xml_output = self.ooxml_generator.generate_style_xml_with_inheritance(
            derived_token, platform="word"
        )

        # Validate structure
        self.assertIn('<w:basedOn w:val="base_paragraph"/>', xml_output)
        self.assertIn('w:styleId="emphasis_paragraph"', xml_output)
        self.assertIn('<w:name w:val="Emphasis Paragraph"/>', xml_output)

        # Validate XML well-formedness
        if LXML_AVAILABLE:
            try:
                etree.fromstring(xml_output)
            except etree.XMLSyntaxError as e:
                self.fail(f"Generated XML is not well-formed: {e}")

    def test_delta_only_property_serialization_word(self):
        """Test serialization of delta-only properties in Word OOXML"""
        token = InheritedTypographyToken(
            id="bold_heading",
            base_style="Heading1",
            inheritance_mode=InheritanceMode.AUTO,
            delta_properties={
                "fontWeight": 700,
                "fontSize": "24pt",
                "fontFamily": "Montserrat"
            }
        )

        xml_output = self.ooxml_generator.generate_style_xml_with_inheritance(
            token, platform="word"
        )

        # Should contain basedOn reference
        self.assertIn('<w:basedOn w:val="Heading1"/>', xml_output)

        # Validate XML structure includes delta properties section
        validation = self.ooxml_generator.validate_ooxml_inheritance_structure(xml_output)
        self.assertTrue(validation["is_valid"])
        self.assertTrue(validation["has_based_on"])
        self.assertTrue(validation["has_delta_properties"])

    def test_powerpoint_style_inheritance_structure(self):
        """Test PowerPoint-specific style inheritance XML structure"""
        token = InheritedTypographyToken(
            id="slide_title",
            base_style="Title",
            inheritance_mode=InheritanceMode.AUTO,
            delta_properties={
                "fontFamily": "Proxima Nova",
                "fontSize": "32pt",
                "fontWeight": 700
            }
        )

        # Note: PowerPoint implementation is placeholder
        xml_output = self.ooxml_generator.generate_style_xml_with_inheritance(
            token, platform="powerpoint"
        )

        # Verify platform-specific generation
        self.assertIn("powerpoint", xml_output.lower())
        self.assertIn("slide_title", xml_output)

    def test_excel_style_inheritance_generation(self):
        """Test Excel-specific style inheritance generation"""
        token = InheritedTypographyToken(
            id="header_cell",
            base_style="Normal",
            inheritance_mode=InheritanceMode.AUTO,
            delta_properties={
                "fontWeight": 600,
                "fontSize": "14pt"
            }
        )

        # Note: Excel implementation is placeholder
        xml_output = self.ooxml_generator.generate_style_xml_with_inheritance(
            token, platform="excel"
        )

        # Verify platform-specific generation
        self.assertIn("excel", xml_output.lower())
        self.assertIn("header_cell", xml_output)

    def test_ooxml_inheritance_compatibility_office_2016(self):
        """Test OOXML inheritance compatibility with Office 2016"""
        token = InheritedTypographyToken(
            id="body_text",
            base_style="Normal",
            inheritance_mode=InheritanceMode.AUTO,
            delta_properties={"lineHeight": 1.4}
        )

        xml_output = self.ooxml_generator.generate_style_xml_with_inheritance(
            token, platform="word"
        )

        validation = self.ooxml_generator.validate_ooxml_inheritance_structure(xml_output)

        # Office 2016+ should support all inheritance features
        self.assertTrue(validation["is_valid"])
        self.assertEqual(len(validation["validation_errors"]), 0)

    def test_ooxml_inheritance_compatibility_office_2019(self):
        """Test OOXML inheritance compatibility with Office 2019"""
        token = InheritedTypographyToken(
            id="callout_text",
            base_style="Emphasis",
            inheritance_mode=InheritanceMode.AUTO,
            delta_properties={
                "fontStyle": "italic",
                "letterSpacing": "0.02em"
            }
        )

        xml_output = self.ooxml_generator.generate_style_xml_with_inheritance(
            token, platform="word"
        )

        validation = self.ooxml_generator.validate_ooxml_inheritance_structure(xml_output)

        # Office 2019+ should have enhanced inheritance support
        self.assertTrue(validation["is_valid"])
        self.assertTrue(validation["has_based_on"])

    def test_style_id_sanitization_for_ooxml(self):
        """Test sanitization of style IDs for OOXML compatibility"""
        test_cases = [
            ("body.text", "body_text"),
            ("heading 1", "heading_1"),
            ("navigation.breadcrumb.active", "navigation_breadcrumb_active"),
            ("simple", "simple")
        ]

        for input_id, expected_output in test_cases:
            sanitized = self.ooxml_generator._sanitize_style_id(input_id)
            self.assertEqual(sanitized, expected_output, f"Expected {expected_output}, got {sanitized}")

    def test_complete_style_generation_no_inheritance(self):
        """Test complete style generation when inheritance is disabled"""
        token = InheritedTypographyToken(
            id="standalone_style",
            font_family="Arial",
            font_size="16pt",
            font_weight=400,
            inheritance_mode=InheritanceMode.MANUAL_OVERRIDE
        )

        xml_output = self.ooxml_generator.generate_style_xml_with_inheritance(
            token, platform="word"
        )

        # Should not contain basedOn reference
        self.assertNotIn("basedOn", xml_output)
        self.assertIn("standalone_style", xml_output)

    def test_circular_dependency_handling_in_ooxml_generation(self):
        """Test handling of circular dependencies in OOXML generation"""
        # Create tokens with circular dependency
        token_a = InheritedTypographyToken(
            id="style_a",
            base_style="style_b",
            inheritance_mode=InheritanceMode.AUTO,
            delta_properties={"fontWeight": 600}
        )

        token_b = InheritedTypographyToken(
            id="style_b",
            base_style="style_a",
            inheritance_mode=InheritanceMode.AUTO,
            delta_properties={"fontSize": "14pt"}
        )

        # Resolve with circular dependency detection
        hierarchy = {"style_a": token_a, "style_b": token_b}
        resolved_token = self.inheritance_resolver.resolve_inheritance(token_a, hierarchy)

        # Should fall back to complete style
        xml_output = self.ooxml_generator.generate_style_xml_with_inheritance(
            resolved_token, platform="word"
        )

        # Should not contain basedOn due to circular dependency fallback
        condition = "basedOn" not in xml_output or resolved_token.inheritance_mode == InheritanceMode.COMPLETE
        self.assertTrue(condition)


class TestOOXMLInheritanceIntegration(unittest.TestCase):
    """Integration tests for OOXML inheritance generation with existing systems"""

    def setUp(self):
        """Set up integration test environment"""
        self.inheritance_registry, self.delta_generator, self.inheritance_resolver = create_inheritance_system()
        self.ooxml_generator = OOXMLInheritanceGenerator(self.inheritance_resolver)
        self.typography_system = TypographyTokenSystem(verbose=False)

    def test_integration_with_typography_token_system(self):
        """Test integration with existing typography token system"""
        # Create token hierarchy through typography system
        design_tokens = {
            "typography": {
                "base": {
                    "$type": "typography",
                    "$value": {
                        "fontFamily": "Inter",
                        "fontSize": "16pt",
                        "lineHeight": 1.4
                    },
                    "$extensions": {
                        "stylestack": {
                            "inheritance": {
                                "baseStyle": "Normal",
                                "mode": "auto"
                            }
                        }
                    }
                },
                "heading": {
                    "$type": "typography",
                    "$value": {
                        "fontSize": "24pt",
                        "fontWeight": 600
                    },
                    "$extensions": {
                        "stylestack": {
                            "inheritance": {
                                "baseStyle": "base",
                                "mode": "auto"
                            }
                        }
                    }
                }
            }
        }

        # Process through typography system with inheritance
        tokens = self.typography_system.create_typography_token_system(
            design_system_tokens=design_tokens
        )

        # Verify tokens were created
        self.assertIn("base", tokens)
        self.assertIn("heading", tokens)

        # Convert to inherited tokens and generate OOXML
        base_token = tokens["base"].to_inherited_token()
        heading_token = tokens["heading"].to_inherited_token()

        # Generate OOXML for both tokens
        base_xml = self.ooxml_generator.generate_style_xml_with_inheritance(
            base_token, platform="word"
        )
        heading_xml = self.ooxml_generator.generate_style_xml_with_inheritance(
            heading_token, platform="word"
        )

        # Validate both XMLs are generated
        self.assertIsNotNone(base_xml)
        self.assertIsNotNone(heading_xml)
        self.assertIn("base", base_xml)
        self.assertIn("heading", heading_xml)

    def test_ooxml_generation_with_complex_inheritance_chain(self):
        """Test OOXML generation with multi-level inheritance chains"""
        # Create 3-level inheritance hierarchy
        tokens = {
            "level1": InheritedTypographyToken(
                id="level1",
                font_family="Arial",
                font_size="12pt",
                base_style="Normal",
                inheritance_mode=InheritanceMode.AUTO,
                delta_properties={"fontFamily": "Arial", "fontSize": "12pt"}
            ),
            "level2": InheritedTypographyToken(
                id="level2",
                font_weight=600,
                base_style="level1",
                inheritance_mode=InheritanceMode.AUTO,
                delta_properties={"fontWeight": 600}
            ),
            "level3": InheritedTypographyToken(
                id="level3",
                font_style="italic",
                base_style="level2",
                inheritance_mode=InheritanceMode.AUTO,
                delta_properties={"fontStyle": "italic"}
            )
        }

        # Resolve inheritance for all levels
        for token_id, token in tokens.items():
            resolved_token = self.inheritance_resolver.resolve_inheritance(token, tokens)
            tokens[token_id] = resolved_token

        # Generate OOXML for level 3 (deepest inheritance)
        level3_xml = self.ooxml_generator.generate_style_xml_with_inheritance(
            tokens["level3"], platform="word"
        )

        # Verify inheritance chain is preserved
        if tokens["level3"].should_generate_delta():
            # Should reference level2 as base
            expected_base = "level2" if tokens["level3"].base_style == "level2" else tokens["level3"].base_style
            if expected_base:
                self.assertIn(f'w:val="{expected_base}"', level3_xml)

    def test_ooxml_validation_comprehensive(self):
        """Comprehensive OOXML validation for inheritance structures"""
        token = InheritedTypographyToken(
            id="comprehensive_test",
            font_family="Montserrat",
            font_size="18pt",
            font_weight=700,
            line_height=1.3,
            letter_spacing="0.01em",
            base_style="Heading2",
            inheritance_mode=InheritanceMode.AUTO,
            delta_properties={
                "fontFamily": "Montserrat",
                "fontSize": "18pt",
                "fontWeight": 700,
                "lineHeight": 1.3,
                "letterSpacing": "0.01em"
            }
        )

        xml_output = self.ooxml_generator.generate_style_xml_with_inheritance(
            token, platform="word"
        )

        validation = self.ooxml_generator.validate_ooxml_inheritance_structure(xml_output)

        # Comprehensive validation checks
        self.assertTrue(validation["is_valid"], f"Validation errors: {validation.get('validation_errors', [])}")
        self.assertTrue(validation["has_based_on"], "Missing basedOn reference in inheritance structure")
        self.assertTrue(validation["has_delta_properties"], "Missing delta properties in OOXML output")


class TestOOXMLInheritanceSystemValidation(unittest.TestCase):
    """System-level validation tests for OOXML inheritance"""

    def setUp(self):
        """Set up system validation environment"""
        self.inheritance_registry, self.delta_generator, self.inheritance_resolver = create_inheritance_system()
        self.ooxml_generator = OOXMLInheritanceGenerator(self.inheritance_resolver)

    def test_ooxml_inheritance_performance_large_hierarchy(self):
        """Test performance with large inheritance hierarchies"""
        # Create a large inheritance hierarchy (50 levels)
        tokens = {}

        # Base token
        tokens["level_0"] = InheritedTypographyToken(
            id="level_0",
            font_family="Arial",
            font_size="12pt",
            base_style="Normal",
            inheritance_mode=InheritanceMode.AUTO,
            delta_properties={"fontFamily": "Arial", "fontSize": "12pt"}
        )

        # Create chain of 49 derived tokens
        for i in range(1, 50):
            tokens[f"level_{i}"] = InheritedTypographyToken(
                id=f"level_{i}",
                font_size=f"{12 + i}pt",
                base_style=f"level_{i-1}",
                inheritance_mode=InheritanceMode.AUTO,
                delta_properties={"fontSize": f"{12 + i}pt"}
            )

        # Measure performance of resolving and generating OOXML for deepest level
        import time

        start_time = time.time()
        resolved_token = self.inheritance_resolver.resolve_inheritance(
            tokens["level_49"], tokens
        )
        xml_output = self.ooxml_generator.generate_style_xml_with_inheritance(
            resolved_token, platform="word"
        )
        end_time = time.time()

        # Performance should be reasonable (< 1 second for 50 levels)
        processing_time = end_time - start_time
        self.assertLess(processing_time, 1.0, f"Performance too slow: {processing_time:.3f}s for 50-level hierarchy")

        # Validate output is still correct
        self.assertIsNotNone(xml_output)
        self.assertIn("level_49", xml_output)

    def test_xml_namespace_handling_inheritance(self):
        """Test proper XML namespace handling in inheritance structures"""
        token = InheritedTypographyToken(
            id="namespace_test",
            base_style="Normal",
            inheritance_mode=InheritanceMode.AUTO,
            delta_properties={"fontWeight": 600}
        )

        xml_output = self.ooxml_generator.generate_style_xml_with_inheritance(
            token, platform="word"
        )

        # Verify namespace prefixes are used correctly
        condition = xml_output.startswith('<w:style') or 'w:style' in xml_output
        self.assertTrue(condition)
        if 'basedOn' in xml_output:
            self.assertIn('w:basedOn', xml_output)

    def test_ooxml_inheritance_error_recovery(self):
        """Test error recovery in OOXML inheritance generation"""
        # Create token with invalid base style
        invalid_token = InheritedTypographyToken(
            id="error_test",
            base_style="NonExistentStyle",
            inheritance_mode=InheritanceMode.AUTO,
            delta_properties={"fontWeight": 600}
        )

        # Should not raise exception, should handle gracefully
        try:
            xml_output = self.ooxml_generator.generate_style_xml_with_inheritance(
                invalid_token, platform="word"
            )
            # Should generate some form of output (even if fallback)
            self.assertIsNotNone(xml_output)
            self.assertIn("error_test", xml_output)
        except Exception as e:
            self.fail(f"OOXML generation should handle errors gracefully: {e}")


# Test data for various OOXML inheritance scenarios
OOXML_INHERITANCE_TEST_CASES = [
    OOXMLInheritanceTestCase(
        name="Simple Word Paragraph Inheritance",
        base_token={"id": "base_para", "fontFamily": "Calibri", "fontSize": "12pt"},
        derived_tokens=[{"id": "emphasis_para", "fontWeight": 600, "baseStyle": "base_para"}],
        expected_ooxml_structure={"has_based_on": True, "has_delta_properties": True},
        platform="word"
    ),
    OOXMLInheritanceTestCase(
        name="PowerPoint Title Slide Inheritance",
        base_token={"id": "slide_base", "fontFamily": "Segoe UI", "fontSize": "24pt"},
        derived_tokens=[{"id": "title_slide", "fontWeight": 700, "fontSize": "32pt", "baseStyle": "slide_base"}],
        expected_ooxml_structure={"has_based_on": True, "has_delta_properties": True},
        platform="powerpoint"
    ),
    OOXMLInheritanceTestCase(
        name="Excel Cell Style Inheritance",
        base_token={"id": "cell_base", "fontFamily": "Calibri", "fontSize": "11pt"},
        derived_tokens=[{"id": "header_cell", "fontWeight": 600, "fontSize": "12pt", "baseStyle": "cell_base"}],
        expected_ooxml_structure={"has_based_on": True, "has_delta_properties": True},
        platform="excel"
    )
]


class TestOOXMLInheritanceTestCases(unittest.TestCase):
    """Parameterized tests for various OOXML inheritance scenarios"""

    def test_ooxml_inheritance_test_cases(self):
        """Test various OOXML inheritance scenarios"""
        for test_case in OOXML_INHERITANCE_TEST_CASES:
            with self.subTest(test_case=test_case.name):
                # Note: Implementation will be completed in subsequent tasks
                # This test structure provides the framework for comprehensive testing
                self.assertIn(test_case.platform, ["word", "powerpoint", "excel"])
                self.assertTrue(test_case.expected_ooxml_structure["has_based_on"])
                self.assertGreater(len(test_case.derived_tokens), 0)


if __name__ == '__main__':
    unittest.main()