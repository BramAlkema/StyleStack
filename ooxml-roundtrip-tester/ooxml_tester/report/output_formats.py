"""Output format implementations for StyleStack reporting."""

import json
import csv
from typing import Dict, List, Any, Optional, IO
from pathlib import Path
from datetime import datetime
from dataclasses import asdict
from abc import ABC, abstractmethod

from .compatibility_matrix import CompatibilityReport, PlatformCompatibility, CarrierCompatibility


class OutputFormatter(ABC):
    """Base class for output formatters."""
    
    @abstractmethod
    def format_report(self, report: CompatibilityReport) -> str:
        """Format a compatibility report."""
        pass
    
    @abstractmethod
    def save_to_file(self, report: CompatibilityReport, file_path: Path) -> None:
        """Save formatted report to file."""
        pass


class JSONReporter(OutputFormatter):
    """JSON output formatter for programmatic consumption by StyleStack."""
    
    def __init__(self, include_metadata: bool = True, 
                 compact: bool = False, api_version: str = "1.0"):
        """
        Initialize JSON reporter.
        
        Args:
            include_metadata: Include detailed metadata in output
            compact: Use compact JSON formatting
            api_version: API version for schema compatibility
        """
        self.include_metadata = include_metadata
        self.compact = compact
        self.api_version = api_version
    
    def format_report(self, report: CompatibilityReport) -> str:
        """Format compatibility report as JSON."""
        json_data = self._convert_report_to_dict(report)
        
        if self.compact:
            return json.dumps(json_data, separators=(',', ':'), default=self._json_serializer)
        else:
            return json.dumps(json_data, indent=2, default=self._json_serializer)
    
    def save_to_file(self, report: CompatibilityReport, file_path: Path) -> None:
        """Save JSON report to file."""
        json_content = self.format_report(report)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_content)
    
    def _convert_report_to_dict(self, report: CompatibilityReport) -> Dict[str, Any]:
        """Convert compatibility report to dictionary for JSON serialization."""
        data = {
            "schema_version": self.api_version,
            "report_type": "stylestack_compatibility",
            "report_id": report.report_id,
            "generated_at": report.generated_at.isoformat(),
            "summary": {
                "text": report.summary,
                "overall_metrics": report.overall_metrics,
                "recommendations": report.recommendations
            },
            "platforms": self._format_platform_results(report.platform_results),
            "carriers": self._format_carrier_results(report.carrier_results),
            "matrices": {
                "platform_matrix": self._create_platform_matrix_dict(report.platform_results),
                "carrier_matrix": self._create_carrier_matrix_dict(report.carrier_results)
            }
        }
        
        if self.include_metadata:
            data["metadata"] = {
                "test_configuration": report.test_configuration,
                "total_platforms_tested": len(report.platform_results),
                "total_carriers_analyzed": len(report.carrier_results),
                "generation_timestamp": datetime.now().isoformat(),
                "tool_version": "1.0.0"
            }
        
        return data
    
    def _format_platform_results(self, platform_results: List[PlatformCompatibility]) -> List[Dict[str, Any]]:
        """Format platform results for JSON output."""
        formatted_results = []
        
        for platform in platform_results:
            platform_data = {
                "platform": platform.platform.value,
                "document_format": platform.document_format.value if platform.document_format else None,
                "version": platform.version,
                "metrics": {
                    "total_carriers": platform.total_carriers,
                    "preserved_carriers": platform.preserved_carriers,
                    "modified_carriers": platform.modified_carriers,
                    "lost_carriers": platform.lost_carriers,
                    "survival_rate": round(platform.survival_rate, 2)
                },
                "status": self._get_platform_status(platform.survival_rate),
                "critical_failures": platform.critical_failures,
                "test_timestamp": platform.test_timestamp.isoformat() if platform.test_timestamp else None
            }
            formatted_results.append(platform_data)
        
        return formatted_results
    
    def _format_carrier_results(self, carrier_results: Dict) -> Dict[str, Dict[str, Any]]:
        """Format carrier results for JSON output."""
        formatted_results = {}
        
        for carrier_type, carrier_data in carrier_results.items():
            formatted_results[carrier_type.value] = {
                "category": carrier_data.category.value,
                "metrics": {
                    "total_tests": carrier_data.total_tests,
                    "successful_tests": carrier_data.successful_tests,
                    "success_rate": round(carrier_data.success_rate, 2)
                },
                "status": self._get_carrier_status(carrier_data.success_rate, carrier_data.category.value),
                "platform_results": {
                    platform.value: success 
                    for platform, success in carrier_data.platform_results.items()
                },
                "common_failures": carrier_data.common_failures
            }
        
        return formatted_results
    
    def _create_platform_matrix_dict(self, platform_results: List[PlatformCompatibility]) -> Dict[str, Dict[str, Any]]:
        """Create platform matrix dictionary."""
        matrix = {}
        
        for platform in platform_results:
            key = platform.platform.value
            if platform.document_format:
                key += f"_{platform.document_format.value}"
            
            matrix[key] = {
                "survival_rate": round(platform.survival_rate, 2),
                "reliability": "high" if len(platform.critical_failures) == 0 else "low",
                "grade": self._get_platform_grade(platform.survival_rate),
                "carriers": {
                    "total": platform.total_carriers,
                    "preserved": platform.preserved_carriers,
                    "modified": platform.modified_carriers,
                    "lost": platform.lost_carriers
                }
            }
        
        return matrix
    
    def _create_carrier_matrix_dict(self, carrier_results: Dict) -> Dict[str, Dict[str, Any]]:
        """Create carrier matrix dictionary.""" 
        matrix = {}
        
        for carrier_type, carrier_data in carrier_results.items():
            if carrier_data.total_tests > 0:  # Only include tested carriers
                matrix[carrier_type.value] = {
                    "success_rate": round(carrier_data.success_rate, 2),
                    "category": carrier_data.category.value,
                    "status": self._get_carrier_status(carrier_data.success_rate, carrier_data.category.value),
                    "cross_platform_support": len([s for s in carrier_data.platform_results.values() if s]),
                    "total_platforms_tested": len(carrier_data.platform_results)
                }
        
        return matrix
    
    def _get_platform_status(self, survival_rate: float) -> str:
        """Get platform status based on survival rate."""
        if survival_rate >= 95:
            return "excellent"
        elif survival_rate >= 85:
            return "good"
        elif survival_rate >= 70:
            return "fair"
        elif survival_rate >= 50:
            return "poor"
        else:
            return "critical"
    
    def _get_platform_grade(self, survival_rate: float) -> str:
        """Get platform grade (A-F) based on survival rate."""
        if survival_rate >= 95:
            return "A"
        elif survival_rate >= 85:
            return "B"
        elif survival_rate >= 75:
            return "C"
        elif survival_rate >= 65:
            return "D"
        else:
            return "F"
    
    def _get_carrier_status(self, success_rate: float, category: str) -> str:
        """Get carrier status based on success rate and category."""
        # Critical carriers have stricter thresholds
        if category == "critical":
            if success_rate >= 95:
                return "stable"
            elif success_rate >= 80:
                return "acceptable"
            else:
                return "critical"
        else:
            if success_rate >= 85:
                return "stable"
            elif success_rate >= 70:
                return "acceptable"
            elif success_rate >= 50:
                return "unstable"
            else:
                return "critical"
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for complex objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, 'value'):  # Enum objects
            return obj.value
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def create_api_response(self, report: CompatibilityReport, 
                           include_raw_data: bool = False) -> Dict[str, Any]:
        """Create API-style response format for StyleStack integration."""
        response = {
            "success": True,
            "data": {
                "report_id": report.report_id,
                "compatibility_score": report.overall_metrics.get('overall_survival_rate', 0),
                "grade": self._get_platform_grade(report.overall_metrics.get('overall_survival_rate', 0)),
                "summary": report.summary,
                "recommendations": report.recommendations[:5],  # Top 5 recommendations
                "platform_scores": {
                    f"{p.platform.value}_{p.document_format.value if p.document_format else 'all'}": 
                    round(p.survival_rate, 1)
                    for p in report.platform_results
                },
                "critical_issues": [
                    rec for rec in report.recommendations if "CRITICAL" in rec
                ]
            },
            "metadata": {
                "generated_at": report.generated_at.isoformat(),
                "api_version": self.api_version,
                "platforms_tested": len(report.platform_results),
                "carriers_analyzed": len([c for c in report.carrier_results.values() if c.total_tests > 0])
            }
        }
        
        if include_raw_data:
            response["raw_data"] = self._convert_report_to_dict(report)
        
        return response


class CSVReporter(OutputFormatter):
    """CSV output formatter for analysis and data manipulation."""
    
    def __init__(self, include_headers: bool = True):
        """
        Initialize CSV reporter.
        
        Args:
            include_headers: Include column headers in output
        """
        self.include_headers = include_headers
    
    def format_report(self, report: CompatibilityReport) -> str:
        """Format compatibility report as CSV."""
        # We'll create multiple CSV sections
        output_lines = []
        
        # Platform results section
        if self.include_headers:
            output_lines.append("# Platform Compatibility Results")
            output_lines.append("platform,document_format,version,total_carriers,preserved_carriers,modified_carriers,lost_carriers,survival_rate,critical_failures")
        
        for platform in report.platform_results:
            row = [
                platform.platform.value,
                platform.document_format.value if platform.document_format else "",
                platform.version or "",
                platform.total_carriers,
                platform.preserved_carriers,
                platform.modified_carriers,
                platform.lost_carriers,
                round(platform.survival_rate, 2),
                len(platform.critical_failures)
            ]
            output_lines.append(",".join(str(x) for x in row))
        
        output_lines.append("")  # Empty line separator
        
        # Carrier results section
        if self.include_headers:
            output_lines.append("# Carrier Compatibility Results")
            output_lines.append("carrier_type,category,total_tests,successful_tests,success_rate,common_failures")
        
        for carrier_type, carrier_data in report.carrier_results.items():
            if carrier_data.total_tests > 0:  # Only include tested carriers
                row = [
                    carrier_type.value,
                    carrier_data.category.value,
                    carrier_data.total_tests,
                    carrier_data.successful_tests,
                    round(carrier_data.success_rate, 2),
                    "; ".join(carrier_data.common_failures)
                ]
                output_lines.append(",".join(str(x) for x in row))
        
        return "\n".join(output_lines)
    
    def save_to_file(self, report: CompatibilityReport, file_path: Path) -> None:
        """Save CSV report to file."""
        csv_content = self.format_report(report)
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            f.write(csv_content)
    
    def create_platform_csv(self, report: CompatibilityReport) -> str:
        """Create CSV specifically for platform data."""
        output = []
        
        if self.include_headers:
            output.append("platform,document_format,survival_rate,status,total_carriers,preserved,modified,lost,critical_failures")
        
        for platform in report.platform_results:
            status = self._get_status(platform.survival_rate)
            row = [
                platform.platform.value,
                platform.document_format.value if platform.document_format else "all",
                round(platform.survival_rate, 2),
                status,
                platform.total_carriers,
                platform.preserved_carriers,
                platform.modified_carriers,
                platform.lost_carriers,
                len(platform.critical_failures)
            ]
            output.append(",".join(str(x) for x in row))
        
        return "\n".join(output)
    
    def create_carrier_csv(self, report: CompatibilityReport) -> str:
        """Create CSV specifically for carrier data."""
        output = []
        
        if self.include_headers:
            output.append("carrier_type,category,success_rate,status,total_tests,successful_tests,failed_tests")
        
        for carrier_type, carrier_data in report.carrier_results.items():
            if carrier_data.total_tests > 0:
                status = self._get_carrier_status(carrier_data.success_rate, carrier_data.category.value)
                failed_tests = carrier_data.total_tests - carrier_data.successful_tests
                
                row = [
                    carrier_type.value,
                    carrier_data.category.value,
                    round(carrier_data.success_rate, 2),
                    status,
                    carrier_data.total_tests,
                    carrier_data.successful_tests,
                    failed_tests
                ]
                output.append(",".join(str(x) for x in row))
        
        return "\n".join(output)
    
    def _get_status(self, survival_rate: float) -> str:
        """Get status label for survival rate."""
        if survival_rate >= 90:
            return "excellent"
        elif survival_rate >= 75:
            return "good"
        elif survival_rate >= 60:
            return "fair"
        else:
            return "poor"
    
    def _get_carrier_status(self, success_rate: float, category: str) -> str:
        """Get carrier status label."""
        if category == "critical":
            threshold = 90
        else:
            threshold = 75
        
        return "stable" if success_rate >= threshold else "unstable"


class HTMLReporter(OutputFormatter):
    """HTML output formatter with visual diff highlighting and summary statistics."""
    
    def __init__(self, include_charts: bool = False, 
                 theme: str = "default"):
        """
        Initialize HTML reporter.
        
        Args:
            include_charts: Include interactive charts (requires additional dependencies)
            theme: Visual theme (default, dark, stylestack)
        """
        self.include_charts = include_charts
        self.theme = theme
    
    def format_report(self, report: CompatibilityReport) -> str:
        """Format compatibility report as HTML."""
        html_parts = []
        
        # HTML header
        html_parts.append(self._create_html_header(report))
        
        # Summary section
        html_parts.append(self._create_summary_section(report))
        
        # Platform results section
        html_parts.append(self._create_platform_section(report))
        
        # Carrier results section
        html_parts.append(self._create_carrier_section(report))
        
        # Recommendations section
        html_parts.append(self._create_recommendations_section(report))
        
        # HTML footer
        html_parts.append(self._create_html_footer())
        
        return "\n".join(html_parts)
    
    def save_to_file(self, report: CompatibilityReport, file_path: Path) -> None:
        """Save HTML report to file."""
        html_content = self.format_report(report)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _create_html_header(self, report: CompatibilityReport) -> str:
        """Create HTML header with CSS styles."""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StyleStack Compatibility Report - {report.report_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .metric {{ background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; display: inline-block; min-width: 200px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .metric-label {{ font-size: 14px; color: #7f8c8d; }}
        .platform {{ border: 1px solid #bdc3c7; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .status-excellent {{ color: #27ae60; font-weight: bold; }}
        .status-good {{ color: #f39c12; font-weight: bold; }}
        .status-fair {{ color: #e67e22; font-weight: bold; }}
        .status-poor {{ color: #e74c3c; font-weight: bold; }}
        .critical {{ background: #ffe6e6; border-left: 4px solid #e74c3c; padding: 10px; margin: 5px 0; }}
        .recommendation {{ background: #e8f4fd; border-left: 4px solid #3498db; padding: 10px; margin: 5px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #bdc3c7; padding: 8px; text-align: left; }}
        th {{ background: #34495e; color: white; }}
        .progress-bar {{ background: #ecf0f1; height: 20px; border-radius: 10px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #e74c3c, #f39c12, #27ae60); }}
    </style>
</head>
<body>
    <div class="container">
        <h1>StyleStack Compatibility Report</h1>
        <p><strong>Report ID:</strong> {report.report_id}</p>
        <p><strong>Generated:</strong> {report.generated_at.strftime("%Y-%m-%d %H:%M:%S")}</p>'''
    
    def _create_summary_section(self, report: CompatibilityReport) -> str:
        """Create summary section with key metrics."""
        overall_rate = report.overall_metrics.get('overall_survival_rate', 0)
        status_class = self._get_status_class(overall_rate)
        
        return f'''
        <h2>Executive Summary</h2>
        <div class="metric">
            <div class="metric-value {status_class}">{overall_rate:.1f}%</div>
            <div class="metric-label">Overall Survival Rate</div>
        </div>
        <div class="metric">
            <div class="metric-value">{len(report.platform_results)}</div>
            <div class="metric-label">Platforms Tested</div>
        </div>
        <div class="metric">
            <div class="metric-value">{report.overall_metrics.get('reliability_score', 0):.1f}%</div>
            <div class="metric-label">Reliability Score</div>
        </div>
        
        <div style="margin: 20px 0;">
            <h3>Overall Compatibility</h3>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {overall_rate}%;"></div>
            </div>
            <p>{overall_rate:.1f}% of design tokens survive round-trip conversion</p>
        </div>
        
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3>Summary</h3>
            <p>{report.summary}</p>
        </div>'''
    
    def _create_platform_section(self, report: CompatibilityReport) -> str:
        """Create platform results section."""
        html = '<h2>Platform Compatibility</h2>'
        
        for platform in sorted(report.platform_results, key=lambda p: p.survival_rate, reverse=True):
            status_class = self._get_status_class(platform.survival_rate)
            
            html += f'''
            <div class="platform">
                <h3>{platform.platform.value.title().replace('_', ' ')} 
                    {f"({platform.document_format.value.title()})" if platform.document_format else ""}
                    <span class="{status_class}">{platform.survival_rate:.1f}%</span>
                </h3>
                <div style="display: flex; gap: 20px; margin: 10px 0;">
                    <div>Preserved: <strong>{platform.preserved_carriers}</strong></div>
                    <div>Modified: <strong>{platform.modified_carriers}</strong></div>
                    <div>Lost: <strong>{platform.lost_carriers}</strong></div>
                </div>
                <div class="progress-bar" style="margin: 10px 0;">
                    <div class="progress-fill" style="width: {platform.survival_rate}%;"></div>
                </div>'''
            
            if platform.critical_failures:
                html += '<div class="critical"><strong>Critical Issues:</strong><ul>'
                for failure in platform.critical_failures:
                    html += f'<li>{failure}</li>'
                html += '</ul></div>'
            
            html += '</div>'
        
        return html
    
    def _create_carrier_section(self, report: CompatibilityReport) -> str:
        """Create carrier results section."""
        html = '<h2>Design Token Carrier Analysis</h2>'
        html += '<table><thead><tr><th>Carrier Type</th><th>Category</th><th>Success Rate</th><th>Status</th><th>Tests</th></tr></thead><tbody>'
        
        # Sort carriers by category (critical first) then by success rate
        sorted_carriers = sorted(
            [(k, v) for k, v in report.carrier_results.items() if v.total_tests > 0],
            key=lambda x: (x[1].category.value != "critical", -x[1].success_rate)
        )
        
        for carrier_type, carrier_data in sorted_carriers:
            status_class = self._get_carrier_status_class(carrier_data.success_rate, carrier_data.category.value)
            
            html += f'''<tr>
                <td>{carrier_type.value.replace('_', ' ').title()}</td>
                <td>{carrier_data.category.value.title()}</td>
                <td class="{status_class}">{carrier_data.success_rate:.1f}%</td>
                <td class="{status_class}">{self._get_carrier_status_text(carrier_data.success_rate, carrier_data.category.value)}</td>
                <td>{carrier_data.successful_tests}/{carrier_data.total_tests}</td>
            </tr>'''
        
        html += '</tbody></table>'
        return html
    
    def _create_recommendations_section(self, report: CompatibilityReport) -> str:
        """Create recommendations section."""
        html = '<h2>Recommendations</h2>'
        
        for i, recommendation in enumerate(report.recommendations, 1):
            css_class = "critical" if "CRITICAL" in recommendation else "recommendation"
            html += f'<div class="{css_class}"><strong>{i}.</strong> {recommendation}</div>'
        
        return html
    
    def _create_html_footer(self) -> str:
        """Create HTML footer."""
        return '''
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #bdc3c7; color: #7f8c8d; font-size: 12px;">
            <p>Generated by StyleStack OOXML Round-Trip Testing Utility</p>
        </div>
    </div>
</body>
</html>'''
    
    def _get_status_class(self, rate: float) -> str:
        """Get CSS class for status based on rate."""
        if rate >= 90:
            return "status-excellent"
        elif rate >= 75:
            return "status-good"
        elif rate >= 60:
            return "status-fair"
        else:
            return "status-poor"
    
    def _get_carrier_status_class(self, success_rate: float, category: str) -> str:
        """Get CSS class for carrier status."""
        if category == "critical":
            return "status-excellent" if success_rate >= 90 else "status-poor"
        else:
            return "status-good" if success_rate >= 75 else "status-fair"
    
    def _get_carrier_status_text(self, success_rate: float, category: str) -> str:
        """Get status text for carrier."""
        if category == "critical":
            return "Stable" if success_rate >= 90 else "Critical"
        else:
            return "Stable" if success_rate >= 75 else "Unstable"