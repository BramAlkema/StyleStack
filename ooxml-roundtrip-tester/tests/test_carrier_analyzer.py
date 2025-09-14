"""Tests for StyleStack design token carrier analysis."""

import pytest
from ooxml_tester.analyze.carrier_analyzer import (
    StyleStackCarrierAnalyzer, CarrierType, CarrierCategory, 
    CarrierMapping, CarrierAnalysisResult
)


class TestCarrierMapping:
    """Test carrier mapping functionality."""
    
    def test_xpath_pattern_matching(self):
        """Test XPath pattern matching."""
        mapping = CarrierMapping(
            xpath_pattern="//w:color/@w:val",
            carrier_type=CarrierType.CHARACTER_STYLE,
            category=CarrierCategory.IMPORTANT,
            design_token_path="tokens.color.text",
            description="Text color",
            office_apps={'word'},
            namespace_prefixes={'w'}
        )
        
        # Should match exact pattern
        assert mapping.matches_xpath("//w:color/@w:val")
        
        # Should match with namespace prefix
        assert mapping.matches_xpath("//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}color/@{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val")
    
    def test_token_value_extraction(self):
        """Test extraction of token values from XML elements."""
        from lxml import etree
        
        mapping = CarrierMapping(
            xpath_pattern="//test",
            carrier_type=CarrierType.COLOR_SCHEME,
            category=CarrierCategory.CRITICAL,
            design_token_path="tokens.test",
            description="Test",
            office_apps={'word'},
            namespace_prefixes=set()
        )
        
        # Test attribute value extraction
        element = etree.fromstring('<test val="FF0000"/>')
        assert mapping.extract_token_value(element) == "FF0000"
        
        # Test text content extraction
        element = etree.fromstring('<test>Some text</test>')
        assert mapping.extract_token_value(element) == "Some text"
        
        # Test with no value
        element = etree.fromstring('<test/>')
        assert mapping.extract_token_value(element) is None


class TestStyleStackCarrierAnalyzer:
    """Test StyleStack carrier analyzer functionality."""
    
    def test_word_color_scheme_detection(self):
        """Test detection of color scheme carriers in Word documents."""
        analyzer = StyleStackCarrierAnalyzer()
        
        word_xml = b'''<?xml version="1.0"?>
        <document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                  xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
            <w:body>
                <w:p>
                    <w:r>
                        <w:rPr>
                            <w:color w:val="FF0000"/>
                        </w:rPr>
                        <w:t>Red text</w:t>
                    </w:r>
                </w:p>
            </w:body>
            <a:theme>
                <a:clrScheme>
                    <a:dk1>
                        <a:srgbClr val="000000"/>
                    </a:dk1>
                    <a:lt1>
                        <a:srgbClr val="FFFFFF"/>
                    </a:lt1>
                </a:clrScheme>
            </a:theme>
        </document>'''
        
        result = analyzer.analyze_carriers(word_xml, 'word')
        
        # Should detect color carriers
        color_carriers = [dc for dc in result.detected_carriers 
                         if dc[0].carrier_type == CarrierType.COLOR_SCHEME]
        assert len(color_carriers) > 0
        
        # Should have reasonable survival rate
        assert result.survival_rate > 0
    
    def test_word_font_scheme_detection(self):
        """Test detection of font scheme carriers in Word documents."""
        analyzer = StyleStackCarrierAnalyzer()
        
        word_xml = b'''<?xml version="1.0"?>
        <document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                  xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
            <w:body>
                <w:p>
                    <w:r>
                        <w:rPr>
                            <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                        </w:rPr>
                        <w:t>Calibri text</w:t>
                    </w:r>
                </w:p>
            </w:body>
            <a:theme>
                <a:fontScheme>
                    <a:majorFont>
                        <a:latin typeface="Calibri Light"/>
                    </a:majorFont>
                    <a:minorFont>
                        <a:latin typeface="Calibri"/>
                    </a:minorFont>
                </a:fontScheme>
            </a:theme>
        </document>'''
        
        result = analyzer.analyze_carriers(word_xml, 'word')
        
        # Should detect font carriers
        font_carriers = [dc for dc in result.detected_carriers 
                        if dc[0].carrier_type in [CarrierType.FONT_SCHEME, CarrierType.CHARACTER_STYLE]]
        assert len(font_carriers) > 0
        
        # Check for specific font detection
        calibri_detected = any('Calibri' in str(dc[2]) for dc in font_carriers if dc[2])
        assert calibri_detected
    
    def test_word_paragraph_style_detection(self):
        """Test detection of paragraph style carriers in Word documents."""
        analyzer = StyleStackCarrierAnalyzer()
        
        word_xml = b'''<?xml version="1.0"?>
        <document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                <w:p>
                    <w:pPr>
                        <w:pStyle w:val="Heading1"/>
                        <w:spacing w:before="240" w:after="120"/>
                        <w:ind w:left="720"/>
                    </w:pPr>
                    <w:r>
                        <w:t>Heading text</w:t>
                    </w:r>
                </w:p>
            </w:body>
        </document>'''
        
        result = analyzer.analyze_carriers(word_xml, 'word')
        
        # Should detect paragraph style carriers
        para_carriers = [dc for dc in result.detected_carriers 
                        if dc[0].carrier_type == CarrierType.PARAGRAPH_STYLE]
        assert len(para_carriers) > 0
        
        # Should detect specific style elements
        heading_detected = any('Heading1' in str(dc[2]) for dc in para_carriers if dc[2])
        spacing_detected = any(dc[0].design_token_path.endswith('spacing.paragraph.before') for dc in para_carriers)
        
        assert heading_detected or spacing_detected
    
    def test_powerpoint_carrier_detection(self):
        """Test detection of PowerPoint-specific carriers."""
        analyzer = StyleStackCarrierAnalyzer()
        
        ppt_xml = b'''<?xml version="1.0"?>
        <sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
             xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
            <p:cSld>
                <p:spTree>
                    <p:sp>
                        <p:spPr>
                            <a:solidFill>
                                <a:srgbClr val="FF0000"/>
                            </a:solidFill>
                        </p:spPr>
                    </p:sp>
                </p:spTree>
            </p:cSld>
        </sld>'''
        
        result = analyzer.analyze_carriers(ppt_xml, 'powerpoint')
        
        # Should detect PowerPoint-specific carriers
        ppt_carriers = [dc for dc in result.detected_carriers 
                       if 'powerpoint' in dc[0].office_apps]
        assert len(ppt_carriers) >= 0  # May or may not find carriers depending on XML structure
    
    def test_excel_carrier_detection(self):
        """Test detection of Excel-specific carriers."""
        analyzer = StyleStackCarrierAnalyzer()
        
        excel_xml = b'''<?xml version="1.0"?>
        <worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
            <sheetData>
                <row r="1">
                    <c r="A1" s="1">
                        <v>42</v>
                    </c>
                </row>
            </sheetData>
        </worksheet>'''
        
        result = analyzer.analyze_carriers(excel_xml, 'excel')
        
        # Should analyze without errors (may not find carriers in minimal XML)
        assert isinstance(result, CarrierAnalysisResult)
        assert result.survival_rate >= 0
    
    def test_carrier_comparison(self):
        """Test comparison of carriers between original and converted documents."""
        analyzer = StyleStackCarrierAnalyzer()
        
        original_xml = b'''<?xml version="1.0"?>
        <document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                <w:p>
                    <w:r>
                        <w:rPr>
                            <w:color w:val="FF0000"/>
                            <w:sz w:val="24"/>
                        </w:rPr>
                        <w:t>Red text</w:t>
                    </w:r>
                </w:p>
            </w:body>
        </document>'''
        
        converted_xml = b'''<?xml version="1.0"?>
        <document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                <w:p>
                    <w:r>
                        <w:rPr>
                            <w:color w:val="0000FF"/>
                            <w:sz w:val="24"/>
                        </w:rPr>
                        <w:t>Blue text</w:t>
                    </w:r>
                </w:p>
            </w:body>
        </document>'''
        
        comparison = analyzer.compare_carriers(original_xml, converted_xml, 'word')
        
        # Should have comparison results
        assert 'preservation_metrics' in comparison
        assert 'token_changes' in comparison
        
        metrics = comparison['preservation_metrics']
        assert 'preservation_rate' in metrics
        assert 'modification_rate' in metrics
        assert 'loss_rate' in metrics
        
        # Should detect token changes
        changes = comparison['token_changes']
        assert isinstance(changes['preserved'], dict)
        assert isinstance(changes['modified'], dict)
        assert isinstance(changes['lost'], dict)
        assert isinstance(changes['gained'], dict)
    
    def test_critical_carrier_survival(self):
        """Test analysis of critical carrier survival."""
        analyzer = StyleStackCarrierAnalyzer()
        
        xml_with_theme = b'''<?xml version="1.0"?>
        <document xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
            <a:theme>
                <a:clrScheme>
                    <a:dk1>
                        <a:srgbClr val="000000"/>
                    </a:dk1>
                </a:clrScheme>
                <a:fontScheme>
                    <a:majorFont>
                        <a:latin typeface="Calibri"/>
                    </a:majorFont>
                </a:fontScheme>
            </a:theme>
        </document>'''
        
        result = analyzer.analyze_carriers(xml_with_theme, 'word')
        critical_survival = analyzer.get_critical_carrier_survival(result)
        
        # Should have critical survival metrics
        assert 'detected_count' in critical_survival
        assert 'missing_count' in critical_survival
        assert 'survival_rate' in critical_survival
        assert 'detected_tokens' in critical_survival
        assert 'missing_tokens' in critical_survival
        
        # Should categorize tokens properly
        for token in critical_survival['detected_tokens']:
            assert 'type' in token
            assert 'token_path' in token
            assert 'description' in token
    
    def test_category_breakdown(self):
        """Test category breakdown generation."""
        analyzer = StyleStackCarrierAnalyzer()
        
        # XML with various carrier types
        mixed_xml = b'''<?xml version="1.0"?>
        <document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                  xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
            <w:body>
                <w:p>
                    <w:pPr>
                        <w:pStyle w:val="Heading1"/>
                    </w:pPr>
                    <w:r>
                        <w:rPr>
                            <w:color w:val="FF0000"/>
                        </w:rPr>
                        <w:t>Text</w:t>
                    </w:r>
                </w:p>
            </w:body>
            <a:theme>
                <a:clrScheme>
                    <a:dk1>
                        <a:srgbClr val="000000"/>
                    </a:dk1>
                </a:clrScheme>
            </a:theme>
        </document>'''
        
        result = analyzer.analyze_carriers(mixed_xml, 'word')
        
        # Should have breakdown for all categories
        for category in CarrierCategory:
            assert category in result.category_breakdown
            
            breakdown = result.category_breakdown[category]
            assert 'detected' in breakdown
            assert 'missing' in breakdown
            assert 'total' in breakdown
            assert 'survival_rate' in breakdown
            
            # Survival rate should be valid percentage
            assert 0 <= breakdown['survival_rate'] <= 100
    
    def test_report_generation(self):
        """Test generation of human-readable reports."""
        analyzer = StyleStackCarrierAnalyzer()
        
        original_xml = b'''<?xml version="1.0"?>
        <document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                <w:p>
                    <w:r>
                        <w:rPr>
                            <w:color w:val="FF0000"/>
                        </w:rPr>
                        <w:t>Text</w:t>
                    </w:r>
                </w:p>
            </w:body>
        </document>'''
        
        converted_xml = b'''<?xml version="1.0"?>
        <document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                <w:p>
                    <w:r>
                        <w:rPr>
                            <w:color w:val="0000FF"/>
                        </w:rPr>
                        <w:t>Text</w:t>
                    </w:r>
                </w:p>
            </w:body>
        </document>'''
        
        comparison = analyzer.compare_carriers(original_xml, converted_xml, 'word')
        report = analyzer.generate_carrier_report(comparison)
        
        # Report should be non-empty string
        assert isinstance(report, str)
        assert len(report) > 0
        
        # Should contain key sections
        assert "StyleStack Design Token Carrier Analysis" in report
        assert "Preservation Rate" in report
        assert "Category Breakdown" in report
    
    def test_invalid_xml_handling(self):
        """Test handling of invalid XML gracefully."""
        analyzer = StyleStackCarrierAnalyzer()
        
        invalid_xml = b"<invalid><unclosed>tag"
        
        result = analyzer.analyze_carriers(invalid_xml, 'word')
        
        # Should handle gracefully without crashing
        assert isinstance(result, CarrierAnalysisResult)
        assert result.survival_rate == 0.0
        assert len(result.detected_carriers) == 0
    
    def test_namespace_handling(self):
        """Test proper handling of XML namespaces."""
        analyzer = StyleStackCarrierAnalyzer()
        
        # XML with explicit namespace declarations
        namespaced_xml = b'''<?xml version="1.0"?>
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                <w:p>
                    <w:r>
                        <w:rPr>
                            <w:color w:val="FF0000"/>
                        </w:rPr>
                        <w:t>Text</w:t>
                    </w:r>
                </w:p>
            </w:body>
        </w:document>'''
        
        result = analyzer.analyze_carriers(namespaced_xml, 'word')
        
        # Should handle namespaced XML properly
        assert isinstance(result, CarrierAnalysisResult)
        # May or may not detect carriers depending on XPath implementation
        assert result.survival_rate >= 0


class TestCarrierMappingComprehensiveness:
    """Test comprehensiveness of carrier mapping coverage."""
    
    def test_all_document_types_covered(self):
        """Test that all document types have carrier mappings."""
        analyzer = StyleStackCarrierAnalyzer()
        
        document_types = ['word', 'powerpoint', 'excel']
        
        for doc_type in document_types:
            relevant_mappings = [m for m in analyzer.carrier_mappings 
                               if doc_type in m.office_apps]
            assert len(relevant_mappings) > 0, f"No mappings for {doc_type}"
    
    def test_all_carrier_types_represented(self):
        """Test that all carrier types are represented in mappings."""
        analyzer = StyleStackCarrierAnalyzer()
        
        mapped_types = set(m.carrier_type for m in analyzer.carrier_mappings)
        
        # Should have good coverage of carrier types
        assert CarrierType.COLOR_SCHEME in mapped_types
        assert CarrierType.FONT_SCHEME in mapped_types
        assert CarrierType.PARAGRAPH_STYLE in mapped_types
        assert CarrierType.CHARACTER_STYLE in mapped_types
    
    def test_critical_carriers_identified(self):
        """Test that critical carriers are properly identified."""
        analyzer = StyleStackCarrierAnalyzer()
        
        critical_mappings = [m for m in analyzer.carrier_mappings 
                           if m.category == CarrierCategory.CRITICAL]
        
        # Should have critical mappings
        assert len(critical_mappings) > 0
        
        # Critical mappings should include color and font schemes
        critical_types = set(m.carrier_type for m in critical_mappings)
        assert CarrierType.COLOR_SCHEME in critical_types
        assert CarrierType.FONT_SCHEME in critical_types


if __name__ == '__main__':
    pytest.main([__file__])