"""Tests for output format generators (JSON, CSV, HTML)."""

import pytest
import json
import csv
from io import StringIO
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from ooxml_tester.report.output_formats import (
    OutputFormatter, JSONReporter, CSVReporter, HTMLReporter
)
from ooxml_tester.report.compatibility_matrix import (
    CompatibilityReport, PlatformCompatibility, CarrierCompatibility,
    PlatformType, DocumentFormat, CarrierType, CarrierCategory
)


@pytest.fixture
def sample_platform_compatibility():
    """Create sample platform compatibility data."""
    return PlatformCompatibility(
        platform=PlatformType.MICROSOFT_OFFICE,
        version="16.0",
        document_format=DocumentFormat.POWERPOINT,
        total_carriers=100,
        preserved_carriers=85,
        modified_carriers=10,
        lost_carriers=5,
        survival_rate=85.0,
        critical_failures=["color_scheme_lost", "font_mapping_failed"],
        test_timestamp=datetime(2024, 1, 15, 10, 30, 0)
    )


@pytest.fixture
def sample_carrier_compatibility():
    """Create sample carrier compatibility data."""
    return CarrierCompatibility(
        carrier_type=CarrierType.COLOR_SCHEME,
        category=CarrierCategory.CRITICAL,
        total_tests=50,
        successful_tests=45,
        platform_results={
            PlatformType.MICROSOFT_OFFICE: True,
            PlatformType.LIBREOFFICE: False
        },
        common_failures=["RGB to theme color mapping failed"]
    )


@pytest.fixture
def sample_compatibility_report(sample_platform_compatibility, sample_carrier_compatibility):
    """Create sample compatibility report."""
    return CompatibilityReport(
        report_id="test_report_20240115_103000",
        generated_at=datetime(2024, 1, 15, 10, 30, 0),
        test_configuration={
            "tolerance_level": "normal",
            "platforms": ["microsoft_office", "libreoffice"],
            "document_formats": ["powerpoint", "word"]
        },
        platform_results=[sample_platform_compatibility],
        carrier_results={CarrierType.COLOR_SCHEME: sample_carrier_compatibility},
        overall_metrics={
            "overall_survival_rate": 85.0,
            "critical_carrier_success": 90.0,
            "reliability_score": 92.0
        },
        summary="StyleStack shows good compatibility across tested platforms.",
        recommendations=[
            "Consider optimizing templates for LibreOffice",
            "Review color scheme implementation"
        ]
    )


class TestOutputFormatter:
    """Test base OutputFormatter class."""
    
    def test_base_formatter_cannot_be_instantiated(self):
        """Test that base formatter cannot be instantiated directly."""
        with pytest.raises(TypeError):
            OutputFormatter()
    
    def test_abstract_methods_exist(self):
        """Test that abstract methods are properly defined."""
        # Verify abstract methods exist
        assert hasattr(OutputFormatter, 'format_report')
        assert hasattr(OutputFormatter, 'save_to_file')


class TestJSONReporter:
    """Test JSON output formatter."""
    
    def test_json_reporter_init(self):
        """Test JSON reporter initialization."""
        reporter = JSONReporter()
        assert reporter is not None
        assert reporter.api_version == "1.0"
        assert reporter.include_metadata is True
        assert reporter.compact is False
    
    def test_format_basic_report(self, sample_compatibility_report):
        """Test basic JSON formatting."""
        reporter = JSONReporter()
        result = reporter.format_report(sample_compatibility_report)
        
        # Parse JSON to verify it's valid
        data = json.loads(result)
        
        # Verify structure
        assert "report_id" in data
        assert "generated_at" in data
        assert "schema_version" in data
        assert "metadata" in data
        assert "platforms" in data
        assert "carriers" in data
        assert "summary" in data
        
        # Verify specific values
        assert data["report_id"] == "test_report_20240115_103000"
        assert data["schema_version"] == "1.0"
        assert len(data["platforms"]) == 1
        assert len(data["carriers"]) == 1
    
    def test_format_with_metadata(self, sample_compatibility_report):
        """Test JSON formatting with metadata."""
        reporter = JSONReporter(include_metadata=True)
        result = reporter.format_report(sample_compatibility_report)
        
        data = json.loads(result)
        
        # Verify metadata
        assert "metadata" in data
        metadata = data["metadata"]
        assert "test_configuration" in metadata
        assert "total_platforms_tested" in metadata
        assert "generation_timestamp" in metadata
        assert "tool_version" in metadata
    
    def test_create_api_response(self, sample_compatibility_report):
        """Test API response formatting."""
        reporter = JSONReporter()
        response = reporter.create_api_response(sample_compatibility_report)
        
        # Verify API response structure
        assert "success" in response
        assert "data" in response
        assert "metadata" in response
        
        assert response["success"] is True
        assert "compatibility_score" in response["data"]
        assert "grade" in response["data"]
        
        # Verify metadata information
        metadata = response["metadata"]
        assert "api_version" in metadata
        assert "generated_at" in metadata
        assert "platforms_tested" in metadata
        assert "carriers_analyzed" in metadata
    
    def test_create_api_response_with_raw_data(self, sample_compatibility_report):
        """Test API response with raw data included."""
        reporter = JSONReporter()
        response = reporter.create_api_response(sample_compatibility_report, include_raw_data=True)
        
        assert "raw_data" in response
        raw_data = response["raw_data"]
        assert "metadata" in raw_data
        assert "platforms" in raw_data
    
    def test_format_platform_results(self, sample_platform_compatibility):
        """Test platform results formatting."""
        reporter = JSONReporter()
        results = reporter._format_platform_results([sample_platform_compatibility])
        
        assert len(results) == 1
        result = results[0]
        assert result["platform"] == "microsoft_office"
        assert result["document_format"] == "powerpoint"
        assert result["metrics"]["survival_rate"] == 85.0
        assert result["metrics"]["total_carriers"] == 100
        assert len(result["critical_failures"]) == 2
    
    def test_format_carrier_results(self, sample_carrier_compatibility):
        """Test carrier results formatting."""
        reporter = JSONReporter()
        carrier_dict = {sample_carrier_compatibility.carrier_type: sample_carrier_compatibility}
        results = reporter._format_carrier_results(carrier_dict)
        
        assert "color_scheme" in results
        result = results["color_scheme"]
        assert result["category"] == "critical"
        assert result["metrics"]["success_rate"] == 90.0
        assert result["metrics"]["total_tests"] == 50
        assert len(result["platform_results"]) == 2


class TestCSVReporter:
    """Test CSV output formatter."""
    
    def test_csv_reporter_init(self):
        """Test CSV reporter initialization."""
        reporter = CSVReporter()
        assert reporter is not None
        assert reporter.include_headers is True
    
    def test_format_basic_report(self, sample_compatibility_report):
        """Test basic CSV formatting."""
        reporter = CSVReporter()
        result = reporter.format_report(sample_compatibility_report)
        
        # Parse CSV to verify structure
        lines = result.strip().split('\n')
        assert len(lines) >= 3  # At least header comment + header + one data row
        
        # Check that platform and carrier data are included
        csv_content = result
        assert "microsoft_office" in csv_content
        assert "color_scheme" in csv_content
    
    def test_create_platform_csv(self, sample_compatibility_report):
        """Test platform CSV formatting."""
        reporter = CSVReporter()
        result = reporter.create_platform_csv(sample_compatibility_report)
        
        lines = result.strip().split('\n')
        assert len(lines) >= 2  # Header + data
        
        # Check header exists and data is present
        assert "platform,document_format,survival_rate" in lines[0]
        assert "microsoft_office" in result
        assert "85.0" in result
    
    def test_create_carrier_csv(self, sample_compatibility_report):
        """Test carrier CSV formatting."""
        reporter = CSVReporter()
        result = reporter.create_carrier_csv(sample_compatibility_report)
        
        lines = result.strip().split('\n')
        assert len(lines) >= 2  # Header + data
        
        # Check header exists and data is present
        assert "carrier_type,category,success_rate" in lines[0]
        assert "color_scheme" in result
        assert "90.0" in result
    
    def test_exclude_headers(self, sample_compatibility_report):
        """Test CSV without headers."""
        reporter = CSVReporter(include_headers=False)
        result = reporter.format_report(sample_compatibility_report)
        
        # Should not have header comments
        assert "# Platform Compatibility Results" not in result
        assert "# Carrier Compatibility Results" not in result


class TestHTMLReporter:
    """Test HTML output formatter."""
    
    def test_html_reporter_init(self):
        """Test HTML reporter initialization."""
        reporter = HTMLReporter()
        assert reporter is not None
        assert reporter.include_charts is False
        assert reporter.theme == "default"
    
    def test_format_basic_report(self, sample_compatibility_report):
        """Test basic HTML formatting."""
        reporter = HTMLReporter()
        result = reporter.format_report(sample_compatibility_report)
        
        # Verify HTML structure
        assert "<!DOCTYPE html>" in result
        assert "<html" in result  # Could be <html lang="en">
        assert "<head>" in result
        assert "<body>" in result
        assert "</html>" in result
        
        # Verify content sections
        assert "StyleStack Compatibility Report" in result
        assert "Platform Compatibility" in result
        assert "Design Token Carrier Analysis" in result
        assert "Executive Summary" in result
    
    def test_format_with_embedded_css(self, sample_compatibility_report):
        """Test HTML formatting contains CSS."""
        reporter = HTMLReporter()
        result = reporter.format_report(sample_compatibility_report)
        
        # CSS is always included in current implementation
        assert "<style>" in result
        assert "</style>" in result
        assert "body {" in result  # CSS should include body styling
    
    def test_format_with_charts(self, sample_compatibility_report):
        """Test HTML formatting with charts enabled."""
        reporter = HTMLReporter(include_charts=True)
        result = reporter.format_report(sample_compatibility_report)
        
        # Basic HTML structure should still be there
        assert "<!DOCTYPE html>" in result
        assert "StyleStack Compatibility Report" in result
    
    def test_html_sections_created(self, sample_compatibility_report):
        """Test that all HTML sections are properly created."""
        reporter = HTMLReporter()
        result = reporter.format_report(sample_compatibility_report)
        
        # Verify all expected sections exist
        assert "Executive Summary" in result
        assert "Platform Compatibility" in result
        assert "Design Token Carrier Analysis" in result
        assert "Recommendations" in result
        
        # Check for specific data
        result_lower = result.lower()
        assert "microsoft" in result_lower and "office" in result_lower
        assert "85.0%" in result
        assert "color" in result_lower and "scheme" in result_lower


class TestIntegration:
    """Integration tests for output formatters."""
    
    def test_all_formatters_process_same_report(self, sample_compatibility_report):
        """Test that all formatters can process the same report."""
        json_reporter = JSONReporter()
        csv_reporter = CSVReporter()
        html_reporter = HTMLReporter()
        
        # All should process without errors
        json_result = json_reporter.format_report(sample_compatibility_report)
        csv_result = csv_reporter.format_report(sample_compatibility_report)
        html_result = html_reporter.format_report(sample_compatibility_report)
        
        # Results should be non-empty strings
        assert len(json_result) > 0
        assert len(csv_result) > 0
        assert len(html_result) > 0
        
        # JSON should be valid
        json.loads(json_result)
        
        # CSV should be valid (can be parsed as lines)
        lines = csv_result.split('\n')
        assert len(lines) > 0
        
        # HTML should contain basic structure
        assert "<html" in html_result
    
    def test_empty_report_handling(self):
        """Test handling of empty/minimal reports."""
        empty_report = CompatibilityReport(
            report_id="empty_test",
            generated_at=datetime.now(),
            test_configuration={}
        )
        
        json_reporter = JSONReporter()
        csv_reporter = CSVReporter()
        html_reporter = HTMLReporter()
        
        # All should handle empty report gracefully
        json_result = json_reporter.format_report(empty_report)
        csv_result = csv_reporter.format_report(empty_report)
        html_result = html_reporter.format_report(empty_report)
        
        # Results should still be valid format
        json.loads(json_result)
        assert len(csv_result) > 0
        assert "<html" in html_result
    
    def test_large_report_performance(self, sample_platform_compatibility, sample_carrier_compatibility):
        """Test performance with large reports."""
        # Create large report with many platforms and carriers
        from ooxml_tester.analyze.carrier_analyzer import CarrierType
        
        large_report = CompatibilityReport(
            report_id="large_test",
            generated_at=datetime.now(),
            test_configuration={},
            platform_results=[sample_platform_compatibility] * 10,
            carrier_results={CarrierType.COLOR_SCHEME: sample_carrier_compatibility},
            overall_metrics={"test_metric": 85.0}
        )
        
        json_reporter = JSONReporter()
        csv_reporter = CSVReporter()
        html_reporter = HTMLReporter()
        
        import time
        
        # Test JSON performance
        start = time.time()
        json_result = json_reporter.format_report(large_report)
        json_time = time.time() - start
        
        # Test CSV performance  
        start = time.time()
        csv_result = csv_reporter.format_report(large_report)
        csv_time = time.time() - start
        
        # Test HTML performance
        start = time.time()
        html_result = html_reporter.format_report(large_report)
        html_time = time.time() - start
        
        # Performance should be reasonable (under 1 second each)
        assert json_time < 1.0
        assert csv_time < 1.0
        assert html_time < 1.0
        
        # Results should be substantial
        assert len(json_result) > 1000
        assert len(csv_result) > 500
        assert len(html_result) > 2000


if __name__ == "__main__":
    pytest.main([__file__])