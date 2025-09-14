"""Tests for semantic diff engine and difference categorization."""

import pytest
from ooxml_tester.analyze.diff_engine import (
    SemanticDiffEngine, DiffCategory, DiffSeverity, 
    SemanticDifference, DiffSummary
)


class TestSemanticDiffEngine:
    """Test semantic diff engine capabilities."""
    
    def test_ignorable_differences_detection(self):
        """Test detection of ignorable differences (metadata, revision IDs)."""
        engine = SemanticDiffEngine()
        
        # Test Word documents with revision tracking differences
        original_xml = b'''<?xml version="1.0"?>
        <document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                <w:p w:rsidR="00123456" w:rsidP="00789ABC">
                    <w:r>
                        <w:t>Same content</w:t>
                    </w:r>
                </w:p>
            </w:body>
        </document>'''
        
        converted_xml = b'''<?xml version="1.0"?>
        <document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                <w:p w:rsidR="00FEDCBA" w:rsidP="00654321">
                    <w:r>
                        <w:t>Same content</w:t>
                    </w:r>
                </w:p>
            </w:body>
        </document>'''
        
        differences, summary = engine.analyze_differences(original_xml, converted_xml, 'word')
        
        # Should detect revision ID changes but mark them as ignorable
        rsid_diffs = [d for d in differences if 'rsid' in d.xpath.lower()]
        assert len(rsid_diffs) > 0
        assert all(d.severity == DiffSeverity.IGNORABLE for d in rsid_diffs)
        
        # Should have high preservation rate since only metadata changed
        assert summary.preservation_rate > 80.0
    
    def test_critical_content_changes_detection(self):
        """Test detection of critical content changes."""
        engine = SemanticDiffEngine()
        
        original_xml = b'''<?xml version="1.0"?>
        <document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                <w:p>
                    <w:r>
                        <w:t>Original text content</w:t>
                    </w:r>
                </w:p>
            </w:body>
        </document>'''
        
        converted_xml = b'''<?xml version="1.0"?>
        <document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                <w:p>
                    <w:r>
                        <w:t>Modified text content</w:t>
                    </w:r>
                </w:p>
            </w:body>
        </document>'''
        
        differences, summary = engine.analyze_differences(original_xml, converted_xml, 'word')
        
        # Should detect text change as critical
        text_diffs = [d for d in differences if d.category == DiffCategory.MODIFIED]
        assert len(text_diffs) > 0
        
        critical_diffs = [d for d in differences if d.severity == DiffSeverity.CRITICAL]
        assert len(critical_diffs) > 0
        assert len(summary.critical_changes) > 0
    
    def test_style_significance_assessment(self):
        """Test assessment of style change significance."""
        engine = SemanticDiffEngine()
        
        # Critical style change (color)
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
        
        differences, summary = engine.analyze_differences(original_xml, converted_xml, 'word')
        
        # Color change should be critical or major
        color_diffs = [d for d in differences if 'color' in d.xpath]
        assert len(color_diffs) > 0
        assert any(d.severity in [DiffSeverity.CRITICAL, DiffSeverity.MAJOR] for d in color_diffs)
    
    def test_structural_changes_detection(self):
        """Test detection of structural changes (added/removed elements)."""
        engine = SemanticDiffEngine()
        
        original_xml = b'''<?xml version="1.0"?>
        <document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                <w:p>
                    <w:r>
                        <w:t>Paragraph 1</w:t>
                    </w:r>
                </w:p>
            </w:body>
        </document>'''
        
        converted_xml = b'''<?xml version="1.0"?>
        <document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                <w:p>
                    <w:r>
                        <w:t>Paragraph 1</w:t>
                    </w:r>
                </w:p>
                <w:p>
                    <w:r>
                        <w:t>Paragraph 2</w:t>
                    </w:r>
                </w:p>
            </w:body>
        </document>'''
        
        differences, summary = engine.analyze_differences(original_xml, converted_xml, 'word')
        
        # Should detect added paragraph
        added_diffs = [d for d in differences if d.category == DiffCategory.ADDED]
        assert len(added_diffs) > 0
        
        # Should mark structural changes as significant
        struct_diffs = [d for d in differences if d.context and d.context.get('affects_structure')]
        assert len(struct_diffs) > 0
    
    def test_powerpoint_specific_analysis(self):
        """Test PowerPoint-specific difference analysis."""
        engine = SemanticDiffEngine()
        
        original_xml = b'''<?xml version="1.0"?>
        <sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
             xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
            <p:cSld>
                <p:spTree>
                    <p:sp>
                        <p:txBody>
                            <a:p>
                                <a:r>
                                    <a:t>Slide content</a:t>
                                </a:r>
                            </a:p>
                        </p:txBody>
                    </p:sp>
                </p:spTree>
            </p:cSld>
        </sld>'''
        
        converted_xml = b'''<?xml version="1.0"?>
        <sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
             xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
            <p:cSld>
                <p:spTree>
                    <p:sp>
                        <p:txBody>
                            <a:p>
                                <a:r>
                                    <a:t>Modified content</a:t>
                                </a:r>
                            </a:p>
                        </p:txBody>
                    </p:sp>
                </p:spTree>
            </p:cSld>
        </sld>'''
        
        differences, summary = engine.analyze_differences(original_xml, converted_xml, 'powerpoint')
        
        # Should properly analyze PowerPoint content
        assert len(differences) > 0
        
        # Should recognize this as content change
        content_diffs = [d for d in differences if d.context and d.context.get('affects_content')]
        assert len(content_diffs) > 0
    
    def test_excel_specific_analysis(self):
        """Test Excel-specific difference analysis."""
        engine = SemanticDiffEngine()
        
        original_xml = b'''<?xml version="1.0"?>
        <worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
            <sheetData>
                <row r="1">
                    <c r="A1">
                        <v>42</v>
                    </c>
                </row>
            </sheetData>
        </worksheet>'''
        
        converted_xml = b'''<?xml version="1.0"?>
        <worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
            <sheetData>
                <row r="1">
                    <c r="A1">
                        <v>43</v>
                    </c>
                </row>
            </sheetData>
        </worksheet>'''
        
        differences, summary = engine.analyze_differences(original_xml, converted_xml, 'excel')
        
        # Should detect cell value change as critical
        value_diffs = [d for d in differences if 'v' in d.xpath]
        assert len(value_diffs) > 0
        assert any(d.severity == DiffSeverity.CRITICAL for d in value_diffs)
    
    def test_difference_filtering(self):
        """Test filtering differences by severity and category."""
        engine = SemanticDiffEngine()
        
        # Create sample differences with various severities
        differences = [
            SemanticDifference(
                xpath='/test1', category=DiffCategory.MODIFIED, 
                severity=DiffSeverity.CRITICAL, description="Critical change"
            ),
            SemanticDifference(
                xpath='/test2', category=DiffCategory.MODIFIED, 
                severity=DiffSeverity.MAJOR, description="Major change"
            ),
            SemanticDifference(
                xpath='/test3', category=DiffCategory.ADDED, 
                severity=DiffSeverity.MINOR, description="Minor addition"
            ),
            SemanticDifference(
                xpath='/test4', category=DiffCategory.DROPPED, 
                severity=DiffSeverity.IGNORABLE, description="Ignorable noise"
            )
        ]
        
        # Filter by severity
        critical_only = engine.filter_differences(differences, DiffSeverity.CRITICAL)
        assert len(critical_only) == 1
        assert critical_only[0].severity == DiffSeverity.CRITICAL
        
        major_and_up = engine.filter_differences(differences, DiffSeverity.MAJOR)
        assert len(major_and_up) == 2
        
        # Filter by category
        modified_only = engine.filter_differences(
            differences, DiffSeverity.IGNORABLE, {DiffCategory.MODIFIED}
        )
        assert len(modified_only) == 2
        assert all(d.category == DiffCategory.MODIFIED for d in modified_only)
    
    def test_preservation_metrics_calculation(self):
        """Test calculation of preservation metrics."""
        engine = SemanticDiffEngine()
        
        # Create differences with context
        differences = [
            SemanticDifference(
                xpath='/content', category=DiffCategory.MODIFIED, 
                severity=DiffSeverity.CRITICAL, 
                context={'affects_content': True}
            ),
            SemanticDifference(
                xpath='/style', category=DiffCategory.MODIFIED, 
                severity=DiffSeverity.MAJOR, 
                context={'affects_styling': True}
            ),
            SemanticDifference(
                xpath='/structure', category=DiffCategory.ADDED, 
                severity=DiffSeverity.MAJOR, 
                context={'affects_structure': True}
            )
        ]
        
        metrics = engine.get_preservation_metrics(differences, 100)
        
        # Should have preservation metrics
        assert 'overall_preservation' in metrics
        assert 'content_preservation' in metrics
        assert 'style_preservation' in metrics
        assert 'structure_preservation' in metrics
        assert 'change_ratio' in metrics
        
        # Values should be reasonable
        assert 0 <= metrics['overall_preservation'] <= 1
        assert 0 <= metrics['content_preservation'] <= 1
        assert metrics['change_ratio'] > 0
    
    def test_difference_descriptions(self):
        """Test generation of human-readable difference descriptions."""
        engine = SemanticDiffEngine()
        
        original_xml = b'''<?xml version="1.0"?>
        <document>
            <element attr="old_value">Old text</element>
        </document>'''
        
        converted_xml = b'''<?xml version="1.0"?>
        <document>
            <element attr="new_value">New text</element>
        </document>'''
        
        differences, summary = engine.analyze_differences(original_xml, converted_xml)
        
        # Should have meaningful descriptions
        for diff in differences:
            assert diff.description is not None
            assert len(diff.description) > 0
            
            # Description should mention the change type
            if diff.old_value and diff.new_value:
                assert 'changed' in diff.description.lower()
                assert diff.old_value in diff.description
                assert diff.new_value in diff.description
    
    def test_summary_generation(self):
        """Test generation of difference summary."""
        engine = SemanticDiffEngine()
        
        original_xml = b'''<?xml version="1.0"?>
        <document>
            <p>Original content</p>
            <style color="red"/>
        </document>'''
        
        converted_xml = b'''<?xml version="1.0"?>
        <document>
            <p>Modified content</p>
            <style color="blue"/>
            <new_element>Added</new_element>
        </document>'''
        
        differences, summary = engine.analyze_differences(original_xml, converted_xml)
        
        # Summary should have all required fields
        assert summary.total_differences >= 0
        assert isinstance(summary.by_category, dict)
        assert isinstance(summary.by_severity, dict)
        assert isinstance(summary.critical_changes, list)
        assert 0 <= summary.preservation_rate <= 100
        
        # Should have entries for all categories and severities
        for category in DiffCategory:
            assert category in summary.by_category
        
        for severity in DiffSeverity:
            assert severity in summary.by_severity


class TestDiffCategorizationRules:
    """Test specific categorization rules and edge cases."""
    
    def test_metadata_vs_content_distinction(self):
        """Test distinction between metadata and content changes."""
        engine = SemanticDiffEngine()
        
        # Metadata-heavy XML with some content
        original_xml = b'''<?xml version="1.0"?>
        <document created="2023-01-01" modified="2023-01-01">
            <metadata>
                <author>John Doe</author>
                <lastPrinted>2023-01-01T10:00:00</lastPrinted>
            </metadata>
            <content>
                <p>Important content here</p>
            </content>
        </document>'''
        
        converted_xml = b'''<?xml version="1.0"?>
        <document created="2023-01-01" modified="2023-12-01">
            <metadata>
                <author>Jane Smith</author>
                <lastPrinted>2023-12-01T15:30:00</lastPrinted>
            </metadata>
            <content>
                <p>Important content here</p>
            </content>
        </document>'''
        
        differences, summary = engine.analyze_differences(original_xml, converted_xml)
        
        # Metadata changes should be less severe than content changes
        metadata_diffs = [d for d in differences 
                         if any(meta in d.xpath.lower() 
                               for meta in ['created', 'modified', 'author', 'lastprinted'])]
        
        # Should have detected metadata changes but marked them appropriately
        assert len(metadata_diffs) > 0
        
        # Content should be preserved (high preservation rate)
        assert summary.preservation_rate > 70.0
    
    def test_namespace_handling_in_categorization(self):
        """Test proper handling of namespaces in categorization."""
        engine = SemanticDiffEngine()
        
        # Same content with different namespace prefixes
        original_xml = b'''<?xml version="1.0"?>
        <doc:document xmlns:doc="http://example.com/doc" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                <w:p>
                    <w:r>
                        <w:t>Content</w:t>
                    </w:r>
                </w:p>
            </w:body>
        </doc:document>'''
        
        converted_xml = b'''<?xml version="1.0"?>
        <document xmlns:word="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <word:body>
                <word:p>
                    <word:r>
                        <word:t>Content</word:t>
                    </word:r>
                </word:p>
            </word:body>
        </document>'''
        
        differences, summary = engine.analyze_differences(original_xml, converted_xml, 'word')
        
        # Should recognize semantic equivalence despite namespace differences
        # Most differences should be minor or ignorable
        significant_diffs = engine.filter_differences(differences, DiffSeverity.MAJOR)
        
        # Should not have many significant differences for equivalent content
        assert len(significant_diffs) <= len(differences) // 2


if __name__ == '__main__':
    pytest.main([__file__])