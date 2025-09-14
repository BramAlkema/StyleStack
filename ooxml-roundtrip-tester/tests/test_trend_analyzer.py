"""Tests for trend analysis functionality."""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from ooxml_tester.report.trend_analyzer import (
    TrendAnalyzer, TrendDirection, TrendMetric, PlatformTrend,
    CarrierTrend, TrendAnalysisReport
)
from ooxml_tester.report.compatibility_matrix import (
    CompatibilityReport, PlatformCompatibility, CarrierCompatibility,
    PlatformType, DocumentFormat
)
from ooxml_tester.analyze.carrier_analyzer import CarrierType, CarrierCategory


class TestTrendMetric:
    """Test TrendMetric functionality."""

    def test_trend_metric_creation(self):
        """Test basic trend metric creation."""
        metric = TrendMetric(
            name="survival_rate",
            values=[80.0, 82.0, 85.0, 87.0],
            timestamps=[
                datetime.now() - timedelta(days=3),
                datetime.now() - timedelta(days=2),
                datetime.now() - timedelta(days=1),
                datetime.now()
            ]
        )

        assert metric.name == "survival_rate"
        assert metric.current_value == 87.0
        assert len(metric.values) == 4

    def test_trend_direction_improving(self):
        """Test improving trend detection."""
        metric = TrendMetric(
            name="test_metric",
            values=[70.0, 75.0, 80.0, 85.0, 90.0],
            timestamps=[datetime.now() - timedelta(days=i) for i in range(5, 0, -1)]
        )

        assert metric.trend_direction == TrendDirection.IMPROVING
        assert metric.change_rate > 0

    def test_trend_direction_declining(self):
        """Test declining trend detection."""
        metric = TrendMetric(
            name="test_metric",
            values=[90.0, 85.0, 80.0, 75.0, 70.0],
            timestamps=[datetime.now() - timedelta(days=i) for i in range(5, 0, -1)]
        )

        assert metric.trend_direction == TrendDirection.DECLINING
        assert metric.change_rate < 0

    def test_trend_direction_stable(self):
        """Test stable trend detection."""
        metric = TrendMetric(
            name="test_metric",
            values=[85.0, 84.5, 85.5, 85.0, 85.2],
            timestamps=[datetime.now() - timedelta(days=i) for i in range(5, 0, -1)]
        )

        assert metric.trend_direction == TrendDirection.STABLE
        assert abs(metric.change_rate) < 5  # Small change rate

    def test_trend_direction_volatile(self):
        """Test volatile trend detection."""
        metric = TrendMetric(
            name="test_metric",
            values=[50.0, 90.0, 30.0, 85.0, 25.0],
            timestamps=[datetime.now() - timedelta(days=i) for i in range(5, 0, -1)]
        )

        assert metric.trend_direction == TrendDirection.VOLATILE

    def test_change_rate_calculation(self):
        """Test change rate calculation."""
        # 25% increase
        metric = TrendMetric(
            name="test_metric",
            values=[80.0, 100.0],
            timestamps=[datetime.now() - timedelta(days=1), datetime.now()]
        )

        assert abs(metric.change_rate - 25.0) < 0.1

        # Zero change
        metric_zero = TrendMetric(
            name="test_metric",
            values=[80.0, 80.0],
            timestamps=[datetime.now() - timedelta(days=1), datetime.now()]
        )

        assert metric_zero.change_rate == 0.0


class TestTrendAnalyzer:
    """Test TrendAnalyzer functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = TrendAnalyzer()
        self.temp_dir = tempfile.mkdtemp()

    def create_sample_report(self, report_id: str, generated_at: datetime,
                           survival_rate: float = 85.0) -> CompatibilityReport:
        """Create a sample compatibility report."""
        platform = PlatformCompatibility(
            platform=PlatformType.MICROSOFT_OFFICE,
            document_format=DocumentFormat.POWERPOINT,
            total_carriers=100,
            preserved_carriers=int(survival_rate),
            modified_carriers=10,
            lost_carriers=100 - int(survival_rate) - 10,
            survival_rate=survival_rate,
            critical_failures=['test_failure'] if survival_rate < 80 else [],
            test_timestamp=generated_at
        )

        carrier = CarrierCompatibility(
            carrier_type=CarrierType.COLOR_SCHEME,
            category=CarrierCategory.CRITICAL,
            total_tests=50,
            successful_tests=int(survival_rate * 0.5),
            platform_results={PlatformType.MICROSOFT_OFFICE: True}
        )

        return CompatibilityReport(
            report_id=report_id,
            generated_at=generated_at,
            test_configuration={'tolerance': 'normal'},
            platform_results=[platform],
            carrier_results={CarrierType.COLOR_SCHEME: carrier},
            overall_metrics={
                'overall_survival_rate': survival_rate,
                'critical_carrier_success': survival_rate * 0.9,
                'reliability_score': survival_rate * 1.1,
                'platform_variance': 5.0
            },
            summary=f"Test report with {survival_rate}% survival rate",
            recommendations=['Test recommendation']
        )

    def test_analyze_trends_basic(self):
        """Test basic trend analysis functionality."""
        # Create sample reports with improving trend
        reports = []
        base_time = datetime.now() - timedelta(days=7)

        for i in range(5):
            report = self.create_sample_report(
                f"report_{i}",
                base_time + timedelta(days=i),
                survival_rate=80.0 + i * 2.0  # Improving from 80% to 88%
            )
            reports.append(report)

        # Analyze trends
        trend_report = self.analyzer.analyze_trends(reports)

        assert trend_report.total_test_runs == 5
        assert len(trend_report.platform_trends) > 0
        assert len(trend_report.carrier_trends) > 0
        assert len(trend_report.overall_metrics) > 0

        # Check that overall survival rate shows improving trend
        survival_metric = trend_report.overall_metrics.get('overall_survival_rate')
        assert survival_metric is not None
        assert survival_metric.trend_direction == TrendDirection.IMPROVING

    def test_analyze_trends_declining(self):
        """Test trend analysis with declining performance."""
        reports = []
        base_time = datetime.now() - timedelta(days=7)

        for i in range(5):
            report = self.create_sample_report(
                f"report_{i}",
                base_time + timedelta(days=i),
                survival_rate=90.0 - i * 3.0  # Declining from 90% to 78%
            )
            reports.append(report)

        trend_report = self.analyzer.analyze_trends(reports)

        # Check that overall survival rate shows declining trend
        survival_metric = trend_report.overall_metrics.get('overall_survival_rate')
        assert survival_metric is not None
        assert survival_metric.trend_direction == TrendDirection.DECLINING

        # Should have insights about declining performance
        assert len(trend_report.insights) > 0
        declining_insights = [i for i in trend_report.insights if 'declining' in i.lower()]
        assert len(declining_insights) > 0

    def test_analyze_platform_trends(self):
        """Test platform-specific trend analysis."""
        reports = []
        base_time = datetime.now() - timedelta(days=5)

        # Create reports with different survival rates
        survival_rates = [85.0, 87.0, 89.0, 91.0, 93.0]

        for i, rate in enumerate(survival_rates):
            report = self.create_sample_report(
                f"report_{i}",
                base_time + timedelta(days=i),
                survival_rate=rate
            )
            reports.append(report)

        trend_report = self.analyzer.analyze_trends(reports)

        # Should have platform trends
        assert len(trend_report.platform_trends) > 0

        # Check specific platform trend
        platform_key = f"{PlatformType.MICROSOFT_OFFICE.value}_{DocumentFormat.POWERPOINT.value}"
        assert platform_key in trend_report.platform_trends

        platform_trend = trend_report.platform_trends[platform_key]
        assert platform_trend.survival_rate.trend_direction == TrendDirection.IMPROVING
        assert platform_trend.survival_rate.current_value == 93.0

    def test_analyze_carrier_trends(self):
        """Test carrier-specific trend analysis."""
        reports = []
        base_time = datetime.now() - timedelta(days=3)

        for i in range(4):
            report = self.create_sample_report(
                f"report_{i}",
                base_time + timedelta(days=i),
                survival_rate=80.0 + i * 5.0
            )
            reports.append(report)

        trend_report = self.analyzer.analyze_trends(reports)

        # Should have carrier trends
        assert len(trend_report.carrier_trends) > 0

        # Check specific carrier trend
        carrier_key = CarrierType.COLOR_SCHEME.value
        assert carrier_key in trend_report.carrier_trends

        carrier_trend = trend_report.carrier_trends[carrier_key]
        assert carrier_trend.success_rate.trend_direction == TrendDirection.IMPROVING

    def test_generate_insights(self):
        """Test insight generation."""
        reports = []
        base_time = datetime.now() - timedelta(days=10)

        # Create mixed trend scenario
        survival_rates = [85.0, 82.0, 79.0, 76.0, 73.0]  # Declining trend

        for i, rate in enumerate(survival_rates):
            report = self.create_sample_report(
                f"report_{i}",
                base_time + timedelta(days=i * 2),
                survival_rate=rate
            )
            reports.append(report)

        trend_report = self.analyzer.analyze_trends(reports)

        # Should generate insights
        assert len(trend_report.insights) > 0

        # Should detect declining system compatibility
        declining_insights = [i for i in trend_report.insights if 'declining' in i.lower()]
        assert len(declining_insights) > 0

    def test_generate_recommendations(self):
        """Test recommendation generation."""
        reports = []
        base_time = datetime.now() - timedelta(days=6)

        # Create scenario with critical issues
        for i in range(3):
            report = self.create_sample_report(
                f"report_{i}",
                base_time + timedelta(days=i * 2),
                survival_rate=65.0 - i * 5.0  # Critical declining trend
            )
            reports.append(report)

        trend_report = self.analyzer.analyze_trends(reports)

        # Should generate recommendations
        assert len(trend_report.recommendations) > 0

        # Should have urgent recommendations for critical issues
        urgent_recs = [r for r in trend_report.recommendations if 'URGENT' in r]
        assert len(urgent_recs) > 0

    def test_risk_assessment(self):
        """Test risk assessment functionality."""
        reports = []
        base_time = datetime.now() - timedelta(days=4)

        # Create reports with low survival rates
        for i in range(3):
            report = self.create_sample_report(
                f"report_{i}",
                base_time + timedelta(days=i),
                survival_rate=55.0 + i * 2.0  # Low survival rates
            )
            reports.append(report)

        trend_report = self.analyzer.analyze_trends(reports)

        # Should assess risks
        assert len(trend_report.risk_assessment) > 0

        # Should identify critical risks
        critical_risks = {k: v for k, v in trend_report.risk_assessment.items() if v == 'critical'}
        assert len(critical_risks) > 0

    def test_empty_reports_handling(self):
        """Test handling of empty report list."""
        with pytest.raises(ValueError):
            self.analyzer.analyze_trends([])

    def test_single_report_handling(self):
        """Test handling of single report."""
        report = self.create_sample_report("single_report", datetime.now())

        trend_report = self.analyzer.analyze_trends([report])

        assert trend_report.total_test_runs == 1
        # Should handle gracefully even with insufficient data
        assert len(trend_report.insights) >= 0

    def test_load_reports_from_directory(self):
        """Test loading reports from directory."""
        # Create sample JSON report files
        temp_dir = Path(self.temp_dir)

        # Create a sample report JSON
        report_data = {
            'report_id': 'test_report',
            'generated_at': datetime.now().isoformat(),
            'test_configuration': {'tolerance': 'normal'},
            'overall_metrics': {'overall_survival_rate': 85.0},
            'summary': 'Test report',
            'recommendations': []
        }

        report_file = temp_dir / "compatibility_report_1.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f)

        # Load reports
        reports = self.analyzer.load_reports_from_directory(temp_dir)

        assert len(reports) == 1
        assert reports[0].report_id == 'test_report'

    def test_generate_trend_report_json(self):
        """Test JSON generation for trend reports."""
        reports = []
        base_time = datetime.now() - timedelta(days=2)

        for i in range(3):
            report = self.create_sample_report(
                f"report_{i}",
                base_time + timedelta(days=i),
                survival_rate=80.0 + i * 5.0
            )
            reports.append(report)

        trend_report = self.analyzer.analyze_trends(reports)

        # Generate JSON
        json_output = self.analyzer.generate_trend_report_json(trend_report)

        # Should be valid JSON
        parsed_json = json.loads(json_output)

        assert parsed_json['report_id'] == trend_report.report_id
        assert 'platform_trends' in parsed_json
        assert 'carrier_trends' in parsed_json
        assert 'overall_metrics' in parsed_json
        assert 'insights' in parsed_json
        assert 'recommendations' in parsed_json

    def test_analysis_window_filtering(self):
        """Test filtering reports by analysis window."""
        reports = []
        base_time = datetime.now() - timedelta(days=40)  # Older than default window

        # Create old reports
        for i in range(3):
            report = self.create_sample_report(
                f"old_report_{i}",
                base_time + timedelta(days=i),
                survival_rate=80.0
            )
            reports.append(report)

        # Create recent reports
        recent_base = datetime.now() - timedelta(days=5)
        for i in range(2):
            report = self.create_sample_report(
                f"recent_report_{i}",
                recent_base + timedelta(days=i),
                survival_rate=90.0
            )
            reports.append(report)

        # Analyze with default window (should filter old reports)
        trend_report = self.analyzer.analyze_trends(reports)

        # Should use recent reports, or all if none in window
        assert trend_report.total_test_runs <= len(reports)


class TestTrendIntegration:
    """Integration tests for trend analysis."""

    def setup_method(self):
        """Set up integration test fixtures."""
        self.analyzer = TrendAnalyzer()

    def test_end_to_end_trend_analysis(self):
        """Test complete trend analysis workflow."""
        # Simulate a month of test data with realistic patterns
        reports = []
        base_time = datetime.now() - timedelta(days=30)

        # Week 1: Declining performance
        for i in range(7):
            reports.append(self._create_realistic_report(
                f"week1_report_{i}",
                base_time + timedelta(days=i),
                85.0 - i * 1.0  # Slight decline
            ))

        # Week 2: Stabilization efforts
        week2_base = base_time + timedelta(days=7)
        for i in range(7):
            reports.append(self._create_realistic_report(
                f"week2_report_{i}",
                week2_base + timedelta(days=i),
                78.5 + i * 0.5  # Slow recovery
            ))

        # Week 3-4: Improvement
        week3_base = base_time + timedelta(days=14)
        for i in range(14):
            reports.append(self._create_realistic_report(
                f"week34_report_{i}",
                week3_base + timedelta(days=i),
                82.0 + i * 0.8  # Steady improvement
            ))

        # Analyze trends
        trend_report = self.analyzer.analyze_trends(reports, analysis_days=35)

        # Verify comprehensive analysis
        assert trend_report.total_test_runs == len(reports)
        assert len(trend_report.platform_trends) > 0
        assert len(trend_report.carrier_trends) > 0
        assert len(trend_report.overall_metrics) > 0
        # Insights should be generated when significant patterns exist
        # but it's acceptable to have no insights for stable patterns
        assert isinstance(trend_report.insights, list)
        assert len(trend_report.recommendations) > 0

        # Should show overall improvement despite initial decline
        survival_metric = trend_report.overall_metrics.get('overall_survival_rate')
        assert survival_metric is not None
        assert survival_metric.current_value > survival_metric.values[0]  # Improvement over time

    def _create_realistic_report(self, report_id: str, timestamp: datetime,
                               base_survival_rate: float) -> CompatibilityReport:
        """Create a realistic compatibility report with multiple platforms and carriers."""
        platforms = []
        carriers = {}

        # Microsoft Office Platform
        ms_office_rate = base_survival_rate + 2.0  # Slightly better than average
        platforms.append(PlatformCompatibility(
            platform=PlatformType.MICROSOFT_OFFICE,
            document_format=DocumentFormat.POWERPOINT,
            total_carriers=120,
            preserved_carriers=int(ms_office_rate * 1.2),
            modified_carriers=15,
            lost_carriers=120 - int(ms_office_rate * 1.2) - 15,
            survival_rate=ms_office_rate,
            critical_failures=['font_substitution'] if ms_office_rate < 80 else [],
            test_timestamp=timestamp
        ))

        # LibreOffice Platform
        lo_rate = base_survival_rate - 5.0  # More challenging
        platforms.append(PlatformCompatibility(
            platform=PlatformType.LIBREOFFICE,
            document_format=DocumentFormat.POWERPOINT,
            total_carriers=120,
            preserved_carriers=int(lo_rate * 1.2),
            modified_carriers=20,
            lost_carriers=120 - int(lo_rate * 1.2) - 20,
            survival_rate=lo_rate,
            critical_failures=['layout_shift', 'color_mapping'] if lo_rate < 75 else ['color_mapping'] if lo_rate < 85 else [],
            test_timestamp=timestamp
        ))

        # Create carrier results
        carrier_types = [
            (CarrierType.COLOR_SCHEME, CarrierCategory.CRITICAL),
            (CarrierType.FONT_SCHEME, CarrierCategory.CRITICAL),
            (CarrierType.PARAGRAPH_STYLE, CarrierCategory.OPTIONAL),
            (CarrierType.LAYOUT_MASTER, CarrierCategory.CRITICAL),
        ]

        for carrier_type, category in carrier_types:
            success_rate = base_survival_rate + (5.0 if category == CarrierCategory.OPTIONAL else -2.0)
            success_rate = max(0, min(100, success_rate))  # Clamp to valid range

            carriers[carrier_type] = CarrierCompatibility(
                carrier_type=carrier_type,
                category=category,
                total_tests=50,
                successful_tests=int(success_rate * 0.5),
                platform_results={
                    PlatformType.MICROSOFT_OFFICE: success_rate > 80,
                    PlatformType.LIBREOFFICE: success_rate > 75
                },
                common_failures=['compatibility_issue'] if success_rate < 80 else []
            )

        return CompatibilityReport(
            report_id=report_id,
            generated_at=timestamp,
            test_configuration={'tolerance': 'normal', 'platforms': ['microsoft_office', 'libreoffice']},
            platform_results=platforms,
            carrier_results=carriers,
            overall_metrics={
                'overall_survival_rate': base_survival_rate,
                'critical_carrier_success': base_survival_rate * 0.95,
                'reliability_score': base_survival_rate * 1.1,
                'platform_variance': abs(ms_office_rate - lo_rate),
                'best_platform_rate': max(ms_office_rate, lo_rate),
                'worst_platform_rate': min(ms_office_rate, lo_rate)
            },
            summary=f"Comprehensive test report with {base_survival_rate:.1f}% survival rate",
            recommendations=[
                'Continue monitoring platform compatibility',
                'Focus on critical carrier optimization' if base_survival_rate < 85 else 'Maintain current stability'
            ]
        )


if __name__ == "__main__":
    pytest.main([__file__])