"""
Modern Test Suite for Template Analyzer - Modular Architecture

Tests the new modular template analysis system with focus on:
- tools.analyzer.types (data structures)
- tools.analyzer.discovery (element discovery engine)  
- tools.analyzer.coverage (coverage analysis)
- tools.analyzer.complexity (complexity scoring)
- tools.template_analyzer (main coordinator)
"""

import unittest
import tempfile
import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

# Import new modular components
from tools.template_analyzer import TemplateAnalyzer
from tools.analyzer.types import (
    DesignElementType, AnalysisLevel, PriorityLevel,
    DesignElement, VariableCoverage, ComplexityScore,
    AnalysisResult, CoverageReport, AnalysisConfig
)
from tools.analyzer.discovery import ElementDiscoveryEngine
from tools.analyzer.coverage import CoverageAnalyzer
from tools.analyzer.complexity import ComplexityAnalyzer


class TestAnalyzerTypes(unittest.TestCase):
    """Test the core analyzer data types and enums."""
    
    def test_design_element_creation(self):
        """Test creating DesignElement objects."""
        element = DesignElement(
            element_type=DesignElementType.COLOR,
            xpath='//a:srgbClr/@val',
            current_value='FF0000',
            priority=PriorityLevel.HIGH,
            context={'slide': 1, 'shape': 'title'}
        )
        
        self.assertEqual(element.element_type, DesignElementType.COLOR)
        self.assertEqual(element.xpath, '//a:srgbClr/@val')
        self.assertEqual(element.current_value, 'FF0000')
        self.assertEqual(element.priority, PriorityLevel.HIGH)
    
    def test_variable_coverage_calculation(self):
        """Test VariableCoverage data structure."""
        coverage = VariableCoverage(
            total_elements=100,
            covered_elements=75,
            coverage_percentage=75.0,
            uncovered_elements=['color1', 'font2'],
            coverage_by_type={
                DesignElementType.COLOR: 0.8,
                DesignElementType.FONT: 0.7
            }
        )
        
        self.assertEqual(coverage.total_elements, 100)
        self.assertEqual(coverage.coverage_percentage, 75.0)
        self.assertEqual(len(coverage.uncovered_elements), 2)
    
    def test_complexity_score_creation(self):
        """Test ComplexityScore calculation."""
        score = ComplexityScore(
            complexity_score=7.5,
            total_elements=50,
            customizable_elements=35,
            element_diversity=12,
            factors={'layouts': 3, 'themes': 2, 'fonts': 4},
            category='Complex'
        )
        
        self.assertEqual(score.complexity_score, 7.5)
        self.assertEqual(score.category, 'Complex')
        self.assertEqual(score.factors['fonts'], 4)


class TestElementDiscoveryEngine(unittest.TestCase):
    """Test the element discovery engine."""
    
    def setUp(self):
        """Set up test environment."""
        self.discovery_engine = ElementDiscoveryEngine()
        
        # Sample PowerPoint slide XML
        self.sample_xml = """<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" 
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
    <p:cSld>
        <p:spTree>
            <p:sp>
                <p:txBody>
                    <a:p>
                        <a:r>
                            <a:rPr>
                                <a:solidFill>
                                    <a:srgbClr val="FF0000"/>
                                </a:solidFill>
                                <a:latin typeface="Arial"/>
                            </a:rPr>
                            <a:t>Sample Text</a:t>
                        </a:r>
                    </a:p>
                </a:txBody>
            </p:sp>
        </p:spTree>
    </p:cSld>
</p:sld>"""
    
    def test_discover_color_elements(self):
        """Test discovery of color design elements."""
        xml_doc = ET.fromstring(self.sample_xml)
        
        elements = self.discovery_engine.discover_elements(
            xml_doc, 
            element_types=[DesignElementType.COLOR]
        )
        
        # Should find the color element
        color_elements = [e for e in elements if e.element_type == DesignElementType.COLOR]
        self.assertGreater(len(color_elements), 0)
        
        # Check the discovered color element
        color_elem = color_elements[0]
        self.assertEqual(color_elem.element_type, DesignElementType.COLOR)
        self.assertIn('srgbClr', color_elem.xpath)
        self.assertEqual(color_elem.current_value, 'FF0000')
    
    def test_discover_font_elements(self):
        """Test discovery of font design elements."""
        xml_doc = ET.fromstring(self.sample_xml)
        
        elements = self.discovery_engine.discover_elements(
            xml_doc, 
            element_types=[DesignElementType.FONT]
        )
        
        # Should find the font element
        font_elements = [e for e in elements if e.element_type == DesignElementType.FONT]
        self.assertGreater(len(font_elements), 0)
        
        # Check the discovered font element
        font_elem = font_elements[0]
        self.assertEqual(font_elem.element_type, DesignElementType.FONT)
        self.assertIn('latin', font_elem.xpath)
        self.assertEqual(font_elem.current_value, 'Arial')
    
    def test_discover_all_elements(self):
        """Test discovery of all element types."""
        xml_doc = ET.fromstring(self.sample_xml)
        
        elements = self.discovery_engine.discover_elements(xml_doc)
        
        # Should find multiple types
        element_types = {e.element_type for e in elements}
        self.assertIn(DesignElementType.COLOR, element_types)
        self.assertIn(DesignElementType.FONT, element_types)
        
        # All elements should have required fields
        for element in elements:
            self.assertIsNotNone(element.xpath)
            self.assertIsNotNone(element.current_value)
            self.assertIsInstance(element.element_type, DesignElementType)


class TestCoverageAnalyzer(unittest.TestCase):
    """Test the coverage analysis engine."""
    
    def setUp(self):
        """Set up test environment."""
        self.coverage_analyzer = CoverageAnalyzer()
        
        # Sample design elements
        self.sample_elements = [
            DesignElement(
                element_type=DesignElementType.COLOR,
                xpath='//a:srgbClr/@val',
                current_value='FF0000',
                priority=PriorityLevel.HIGH
            ),
            DesignElement(
                element_type=DesignElementType.FONT,
                xpath='//a:latin/@typeface',
                current_value='Arial',
                priority=PriorityLevel.MEDIUM
            ),
            DesignElement(
                element_type=DesignElementType.COLOR,
                xpath='//a:srgbClr[2]/@val',
                current_value='00FF00',
                priority=PriorityLevel.LOW
            )
        ]
    
    def test_calculate_coverage_basic(self):
        """Test basic coverage calculation."""
        # Mock variables that cover some elements
        variables = {
            'primary_color': 'FF0000',
            'secondary_color': '00FF00'
        }
        
        coverage = self.coverage_analyzer.calculate_coverage(
            self.sample_elements, 
            variables
        )
        
        self.assertIsInstance(coverage, VariableCoverage)
        self.assertEqual(coverage.total_elements, 3)
        self.assertGreaterEqual(coverage.coverage_percentage, 0.0)
        self.assertLessEqual(coverage.coverage_percentage, 100.0)
    
    def test_coverage_by_element_type(self):
        """Test coverage breakdown by element type."""
        variables = {'primary_color': 'FF0000'}
        
        coverage = self.coverage_analyzer.calculate_coverage(
            self.sample_elements, 
            variables
        )
        
        # Should have coverage breakdown by type
        self.assertIn(DesignElementType.COLOR, coverage.coverage_by_type)
        self.assertIn(DesignElementType.FONT, coverage.coverage_by_type)
        
        # Coverage percentages should be valid
        for coverage_pct in coverage.coverage_by_type.values():
            self.assertGreaterEqual(coverage_pct, 0.0)
            self.assertLessEqual(coverage_pct, 1.0)
    
    def test_generate_coverage_report(self):
        """Test coverage report generation."""
        variables = {'primary_color': 'FF0000'}
        
        report = self.coverage_analyzer.generate_coverage_report(
            self.sample_elements,
            variables,
            template_name="test_template.potx"
        )
        
        self.assertIsInstance(report, CoverageReport)
        self.assertEqual(report.template_name, "test_template.potx")
        self.assertIsInstance(report.overall_coverage, VariableCoverage)
        self.assertGreater(len(report.recommendations), 0)


class TestComplexityAnalyzer(unittest.TestCase):
    """Test the complexity analysis engine."""
    
    def setUp(self):
        """Set up test environment."""
        self.complexity_analyzer = ComplexityAnalyzer()
        
        # Sample design elements with varying complexity
        self.simple_elements = [
            DesignElement(
                element_type=DesignElementType.COLOR,
                xpath='//a:srgbClr/@val',
                current_value='FF0000',
                priority=PriorityLevel.HIGH
            )
        ]
        
        self.complex_elements = [
            DesignElement(
                element_type=DesignElementType.COLOR,
                xpath='//a:srgbClr/@val', 
                current_value='FF0000',
                priority=PriorityLevel.HIGH
            ),
            DesignElement(
                element_type=DesignElementType.FONT,
                xpath='//a:latin/@typeface',
                current_value='Arial', 
                priority=PriorityLevel.MEDIUM
            ),
            DesignElement(
                element_type=DesignElementType.GRADIENT,
                xpath='//a:gradFill/a:gsLst',
                current_value='complex_gradient',
                priority=PriorityLevel.HIGH
            ),
            DesignElement(
                element_type=DesignElementType.EFFECT,
                xpath='//a:effectLst/a:outerShdw',
                current_value='shadow_effect',
                priority=PriorityLevel.MEDIUM
            )
        ]
    
    def test_calculate_complexity_simple(self):
        """Test complexity calculation for simple template."""
        score = self.complexity_analyzer.calculate_complexity(self.simple_elements)
        
        self.assertIsInstance(score, ComplexityScore)
        self.assertLess(score.complexity_score, 5.0)  # Should be low complexity
        self.assertEqual(score.category, 'Simple')
        self.assertEqual(score.total_elements, 1)
    
    def test_calculate_complexity_complex(self):
        """Test complexity calculation for complex template."""
        score = self.complexity_analyzer.calculate_complexity(self.complex_elements)
        
        self.assertIsInstance(score, ComplexityScore)
        self.assertGreater(score.complexity_score, 3.0)  # Should be higher complexity
        self.assertIn(score.category, ['Moderate', 'Complex', 'Expert'])
        self.assertEqual(score.total_elements, 4)
        self.assertGreater(score.element_diversity, 1)
    
    def test_complexity_factors(self):
        """Test complexity factor breakdown."""
        score = self.complexity_analyzer.calculate_complexity(self.complex_elements)
        
        # Should have detailed factor breakdown
        self.assertIsInstance(score.factors, dict)
        self.assertGreater(len(score.factors), 0)
        
        # All factors should be numeric
        for factor_value in score.factors.values():
            self.assertIsInstance(factor_value, (int, float))


class TestTemplateAnalyzer(unittest.TestCase):
    """Test the main TemplateAnalyzer coordinator."""
    
    def setUp(self):
        """Set up test environment."""
        self.analyzer = TemplateAnalyzer()
        
        # Create a mock template file
        self.temp_dir = Path(tempfile.mkdtemp())
        self.template_path = self.temp_dir / "test_template.potx"
        
        # Create a minimal ZIP file that looks like a PowerPoint template
        with zipfile.ZipFile(self.template_path, 'w') as zf:
            # Add minimal content
            zf.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types/>')
            zf.writestr('ppt/presentation.xml', '''<?xml version="1.0"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
                xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
    <p:sldMasterIdLst>
        <p:sldMasterId id="1" r:id="rId1"/>
    </p:sldMasterIdLst>
</p:presentation>''')
            zf.writestr('ppt/slides/slide1.xml', '''<?xml version="1.0"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
    <p:cSld>
        <p:spTree>
            <p:sp>
                <p:txBody>
                    <a:p>
                        <a:r>
                            <a:rPr>
                                <a:solidFill>
                                    <a:srgbClr val="FF0000"/>
                                </a:solidFill>
                            </a:rPr>
                            <a:t>Test Text</a:t>
                        </a:r>
                    </a:p>
                </a:txBody>
            </p:sp>
        </p:spTree>
    </p:cSld>
</p:sld>''')
    
    def tearDown(self):
        """Clean up test files."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_analyze_template_basic(self):
        """Test basic template analysis."""
        result = self.analyzer.analyze_template(
            str(self.template_path),
            analysis_level=AnalysisLevel.BASIC
        )
        
        self.assertIsInstance(result, AnalysisResult)
        self.assertTrue(result.success)
        self.assertEqual(result.template_name, "test_template.potx")
        self.assertGreater(len(result.design_elements), 0)
    
    def test_analyze_template_comprehensive(self):
        """Test comprehensive template analysis."""
        result = self.analyzer.analyze_template(
            str(self.template_path),
            analysis_level=AnalysisLevel.COMPREHENSIVE
        )
        
        self.assertIsInstance(result, AnalysisResult)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.coverage_analysis)
        self.assertIsNotNone(result.complexity_analysis)
        self.assertGreater(len(result.design_elements), 0)
    
    def test_generate_coverage_report(self):
        """Test coverage report generation."""
        variables = {
            'primary_color': 'FF0000',
            'title_font': 'Arial'
        }
        
        report = self.analyzer.generate_coverage_report(
            str(self.template_path),
            variables
        )
        
        self.assertIsInstance(report, CoverageReport)
        self.assertEqual(report.template_name, "test_template.potx")
        self.assertIsInstance(report.overall_coverage, VariableCoverage)
    
    def test_analyze_with_config(self):
        """Test analysis with custom configuration."""
        config = AnalysisConfig(
            analysis_level=AnalysisLevel.STANDARD,
            element_types=[DesignElementType.COLOR, DesignElementType.FONT],
            include_complexity=True,
            include_coverage=False
        )
        
        result = self.analyzer.analyze_template(
            str(self.template_path),
            config=config
        )
        
        self.assertIsInstance(result, AnalysisResult)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.complexity_analysis)
        # Coverage analysis should be None since include_coverage=False
        self.assertIsNone(result.coverage_analysis)


if __name__ == '__main__':
    unittest.main()