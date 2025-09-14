"""Trend analysis for batch reporting across multiple test runs."""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import json
import statistics
from enum import Enum

from .compatibility_matrix import CompatibilityReport, PlatformCompatibility, CarrierCompatibility


class TrendDirection(Enum):
    """Direction of trend over time."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"


@dataclass
class TrendMetric:
    """A single metric tracked over time."""
    name: str
    values: List[float] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)

    @property
    def current_value(self) -> Optional[float]:
        """Get the most recent value."""
        return self.values[-1] if self.values else None

    @property
    def trend_direction(self) -> TrendDirection:
        """Calculate the overall trend direction."""
        if len(self.values) < 3:
            return TrendDirection.STABLE

        # Calculate trend using linear regression slope
        n = len(self.values)
        x_values = list(range(n))

        # Simple linear regression
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(self.values)

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, self.values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            return TrendDirection.STABLE

        slope = numerator / denominator

        # Calculate volatility (coefficient of variation)
        if y_mean > 0:
            cv = statistics.stdev(self.values) / y_mean
        else:
            cv = 0

        # Determine trend based on slope and volatility
        if cv > 0.15:  # High volatility threshold
            return TrendDirection.VOLATILE
        elif slope > 0.5:  # Significant positive trend
            return TrendDirection.IMPROVING
        elif slope < -0.5:  # Significant negative trend
            return TrendDirection.DECLINING
        else:
            return TrendDirection.STABLE

    @property
    def change_rate(self) -> float:
        """Calculate the rate of change between first and last values."""
        if len(self.values) < 2:
            return 0.0

        first_val = self.values[0]
        last_val = self.values[-1]

        if first_val == 0:
            return float('inf') if last_val > 0 else 0.0

        return ((last_val - first_val) / first_val) * 100


@dataclass
class PlatformTrend:
    """Trend data for a specific platform."""
    platform: str
    survival_rate: TrendMetric
    critical_failures: TrendMetric
    carrier_success_rate: TrendMetric
    test_count: TrendMetric


@dataclass
class CarrierTrend:
    """Trend data for a specific carrier type."""
    carrier_type: str
    success_rate: TrendMetric
    cross_platform_compatibility: TrendMetric
    failure_frequency: TrendMetric


@dataclass
class TrendAnalysisReport:
    """Comprehensive trend analysis report."""
    report_id: str
    generated_at: datetime
    analysis_period: Tuple[datetime, datetime]
    total_test_runs: int
    platform_trends: Dict[str, PlatformTrend] = field(default_factory=dict)
    carrier_trends: Dict[str, CarrierTrend] = field(default_factory=dict)
    overall_metrics: Dict[str, TrendMetric] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    risk_assessment: Dict[str, str] = field(default_factory=dict)


class TrendAnalyzer:
    """Analyzes trends across multiple test runs for batch reporting."""

    def __init__(self):
        self.reports_cache = []
        self.analysis_window_days = 30  # Default analysis window

    def load_reports_from_directory(self, reports_dir: Path,
                                   file_pattern: str = "*compatibility*.json") -> List[CompatibilityReport]:
        """Load compatibility reports from a directory."""
        reports = []

        for report_file in reports_dir.glob(file_pattern):
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)

                # Convert JSON data back to CompatibilityReport object
                report = self._deserialize_report(report_data)
                if report:
                    reports.append(report)

            except Exception as e:
                print(f"Warning: Failed to load report {report_file}: {e}")

        # Sort reports by generation time
        reports.sort(key=lambda r: r.generated_at)
        return reports

    def analyze_trends(self, reports: List[CompatibilityReport],
                      analysis_days: Optional[int] = None) -> TrendAnalysisReport:
        """Analyze trends across multiple compatibility reports."""
        if not reports:
            raise ValueError("No reports provided for trend analysis")

        analysis_days = analysis_days or self.analysis_window_days
        cutoff_date = datetime.now() - timedelta(days=analysis_days)

        # Filter reports within analysis window
        filtered_reports = [r for r in reports if r.generated_at >= cutoff_date]

        if not filtered_reports:
            # Use all reports if none in window
            filtered_reports = reports

        # Create trend analysis report
        trend_report = TrendAnalysisReport(
            report_id=f"trend_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            generated_at=datetime.now(),
            analysis_period=(filtered_reports[0].generated_at, filtered_reports[-1].generated_at),
            total_test_runs=len(filtered_reports)
        )

        # Analyze platform trends
        trend_report.platform_trends = self._analyze_platform_trends(filtered_reports)

        # Analyze carrier trends
        trend_report.carrier_trends = self._analyze_carrier_trends(filtered_reports)

        # Analyze overall metrics trends
        trend_report.overall_metrics = self._analyze_overall_trends(filtered_reports)

        # Generate insights and recommendations
        trend_report.insights = self._generate_insights(trend_report)
        trend_report.recommendations = self._generate_trend_recommendations(trend_report)
        trend_report.risk_assessment = self._assess_trend_risks(trend_report)

        return trend_report

    def _analyze_platform_trends(self, reports: List[CompatibilityReport]) -> Dict[str, PlatformTrend]:
        """Analyze trends for each platform."""
        platform_trends = {}

        # Collect platform data across all reports
        platform_data = {}

        for report in reports:
            for platform_result in report.platform_results:
                platform_key = f"{platform_result.platform.value}_{platform_result.document_format.value if platform_result.document_format else 'all'}"

                if platform_key not in platform_data:
                    platform_data[platform_key] = {
                        'survival_rates': [],
                        'critical_failures': [],
                        'carrier_success': [],
                        'test_counts': [],
                        'timestamps': []
                    }

                platform_data[platform_key]['survival_rates'].append(platform_result.survival_rate)
                platform_data[platform_key]['critical_failures'].append(len(platform_result.critical_failures))
                platform_data[platform_key]['test_counts'].append(platform_result.total_carriers)
                platform_data[platform_key]['timestamps'].append(report.generated_at)

                # Calculate carrier success rate for this platform
                carrier_success = 0.0
                if report.carrier_results:
                    success_rates = []
                    for carrier_result in report.carrier_results.values():
                        if platform_result.platform in carrier_result.platform_results:
                            success_rates.append(carrier_result.success_rate)

                    if success_rates:
                        carrier_success = statistics.mean(success_rates)

                platform_data[platform_key]['carrier_success'].append(carrier_success)

        # Create trend objects for each platform
        for platform_key, data in platform_data.items():
            platform_trends[platform_key] = PlatformTrend(
                platform=platform_key,
                survival_rate=TrendMetric(
                    name="survival_rate",
                    values=data['survival_rates'],
                    timestamps=data['timestamps']
                ),
                critical_failures=TrendMetric(
                    name="critical_failures",
                    values=data['critical_failures'],
                    timestamps=data['timestamps']
                ),
                carrier_success_rate=TrendMetric(
                    name="carrier_success_rate",
                    values=data['carrier_success'],
                    timestamps=data['timestamps']
                ),
                test_count=TrendMetric(
                    name="test_count",
                    values=data['test_counts'],
                    timestamps=data['timestamps']
                )
            )

        return platform_trends

    def _analyze_carrier_trends(self, reports: List[CompatibilityReport]) -> Dict[str, CarrierTrend]:
        """Analyze trends for each carrier type."""
        carrier_trends = {}

        # Collect carrier data across all reports
        carrier_data = {}

        for report in reports:
            for carrier_type, carrier_result in report.carrier_results.items():
                carrier_key = carrier_type.value

                if carrier_key not in carrier_data:
                    carrier_data[carrier_key] = {
                        'success_rates': [],
                        'cross_platform_compat': [],
                        'failure_frequencies': [],
                        'timestamps': []
                    }

                carrier_data[carrier_key]['success_rates'].append(carrier_result.success_rate)

                # Calculate cross-platform compatibility
                platform_success_count = sum(1 for success in carrier_result.platform_results.values() if success)
                total_platforms = len(carrier_result.platform_results)
                cross_platform_compat = (platform_success_count / total_platforms * 100) if total_platforms > 0 else 0
                carrier_data[carrier_key]['cross_platform_compat'].append(cross_platform_compat)

                # Calculate failure frequency
                failure_freq = (carrier_result.total_tests - carrier_result.successful_tests) if carrier_result.total_tests > 0 else 0
                carrier_data[carrier_key]['failure_frequencies'].append(failure_freq)

                carrier_data[carrier_key]['timestamps'].append(report.generated_at)

        # Create trend objects for each carrier
        for carrier_key, data in carrier_data.items():
            carrier_trends[carrier_key] = CarrierTrend(
                carrier_type=carrier_key,
                success_rate=TrendMetric(
                    name="success_rate",
                    values=data['success_rates'],
                    timestamps=data['timestamps']
                ),
                cross_platform_compatibility=TrendMetric(
                    name="cross_platform_compatibility",
                    values=data['cross_platform_compat'],
                    timestamps=data['timestamps']
                ),
                failure_frequency=TrendMetric(
                    name="failure_frequency",
                    values=data['failure_frequencies'],
                    timestamps=data['timestamps']
                )
            )

        return carrier_trends

    def _analyze_overall_trends(self, reports: List[CompatibilityReport]) -> Dict[str, TrendMetric]:
        """Analyze overall system trends."""
        overall_trends = {}

        # Collect overall metrics
        metrics_data = {
            'overall_survival_rate': [],
            'critical_carrier_success': [],
            'reliability_score': [],
            'platform_variance': [],
            'timestamps': []
        }

        for report in reports:
            metrics_data['timestamps'].append(report.generated_at)

            # Extract metrics with defaults
            metrics_data['overall_survival_rate'].append(
                report.overall_metrics.get('overall_survival_rate', 0.0)
            )
            metrics_data['critical_carrier_success'].append(
                report.overall_metrics.get('critical_carrier_success', 0.0)
            )
            metrics_data['reliability_score'].append(
                report.overall_metrics.get('reliability_score', 0.0)
            )
            metrics_data['platform_variance'].append(
                report.overall_metrics.get('platform_variance', 0.0)
            )

        # Create trend metrics
        for metric_name, values in metrics_data.items():
            if metric_name != 'timestamps':
                overall_trends[metric_name] = TrendMetric(
                    name=metric_name,
                    values=values,
                    timestamps=metrics_data['timestamps']
                )

        return overall_trends

    def _generate_insights(self, trend_report: TrendAnalysisReport) -> List[str]:
        """Generate insights from trend analysis."""
        insights = []

        # Overall system insights
        if 'overall_survival_rate' in trend_report.overall_metrics:
            survival_trend = trend_report.overall_metrics['overall_survival_rate']
            current_rate = survival_trend.current_value or 0
            change_rate = survival_trend.change_rate

            if survival_trend.trend_direction == TrendDirection.IMPROVING:
                insights.append(f"System compatibility is improving: {change_rate:+.1f}% change, current rate {current_rate:.1f}%")
            elif survival_trend.trend_direction == TrendDirection.DECLINING:
                insights.append(f"System compatibility is declining: {change_rate:+.1f}% change, current rate {current_rate:.1f}%")
            elif survival_trend.trend_direction == TrendDirection.VOLATILE:
                insights.append(f"System compatibility shows high volatility: current rate {current_rate:.1f}%")

        # Platform-specific insights
        declining_platforms = []
        improving_platforms = []

        for platform_name, platform_trend in trend_report.platform_trends.items():
            if platform_trend.survival_rate.trend_direction == TrendDirection.DECLINING:
                declining_platforms.append(platform_name)
            elif platform_trend.survival_rate.trend_direction == TrendDirection.IMPROVING:
                improving_platforms.append(platform_name)

        if declining_platforms:
            insights.append(f"Platforms showing declining compatibility: {', '.join(declining_platforms)}")

        if improving_platforms:
            insights.append(f"Platforms showing improved compatibility: {', '.join(improving_platforms)}")

        # Carrier-specific insights
        problematic_carriers = []
        stable_carriers = []

        for carrier_name, carrier_trend in trend_report.carrier_trends.items():
            if carrier_trend.success_rate.trend_direction == TrendDirection.DECLINING:
                problematic_carriers.append(carrier_name)
            elif (carrier_trend.success_rate.trend_direction == TrendDirection.STABLE and
                  (carrier_trend.success_rate.current_value or 0) >= 90):
                stable_carriers.append(carrier_name)

        if problematic_carriers:
            insights.append(f"Design token carriers with declining reliability: {', '.join(problematic_carriers)}")

        if len(stable_carriers) >= 5:
            insights.append(f"Strong stability in core design tokens: {len(stable_carriers)} carriers maintaining >90% success")

        # Test coverage insights
        test_run_count = trend_report.total_test_runs
        analysis_days = (trend_report.analysis_period[1] - trend_report.analysis_period[0]).days

        if analysis_days > 0:
            test_frequency = test_run_count / analysis_days
            if test_frequency < 0.2:  # Less than 1 test per 5 days
                insights.append(f"Low test frequency detected: {test_frequency:.2f} tests/day over {analysis_days} days")
            elif test_frequency > 2:  # More than 2 tests per day
                insights.append(f"High test frequency: {test_frequency:.1f} tests/day indicating active development")

        return insights

    def _generate_trend_recommendations(self, trend_report: TrendAnalysisReport) -> List[str]:
        """Generate recommendations based on trend analysis."""
        recommendations = []

        # Critical declining trends
        critical_issues = []
        for platform_name, platform_trend in trend_report.platform_trends.items():
            if (platform_trend.survival_rate.trend_direction == TrendDirection.DECLINING and
                (platform_trend.survival_rate.current_value or 0) < 75):
                critical_issues.append(platform_name)

        if critical_issues:
            recommendations.append(
                f"URGENT: Address critical compatibility regression on {', '.join(critical_issues)}"
            )

        # Volatile metrics
        volatile_carriers = []
        for carrier_name, carrier_trend in trend_report.carrier_trends.items():
            if carrier_trend.success_rate.trend_direction == TrendDirection.VOLATILE:
                volatile_carriers.append(carrier_name)

        if volatile_carriers:
            recommendations.append(
                f"Investigate volatile design token carriers for root cause: {', '.join(volatile_carriers[:3])}"
            )

        # Platform variance recommendations
        if 'platform_variance' in trend_report.overall_metrics:
            variance_trend = trend_report.overall_metrics['platform_variance']
            if (variance_trend.current_value or 0) > 20:
                recommendations.append(
                    "High platform variance detected - consider platform-specific optimization strategies"
                )

        # Test coverage recommendations
        if trend_report.total_test_runs < 5:
            recommendations.append(
                "Insufficient test data for reliable trend analysis - increase test frequency"
            )

        # Stability recommendations
        stable_platforms = []
        for platform_name, platform_trend in trend_report.platform_trends.items():
            if (platform_trend.survival_rate.trend_direction == TrendDirection.STABLE and
                (platform_trend.survival_rate.current_value or 0) >= 85):
                stable_platforms.append(platform_name)

        if len(stable_platforms) >= len(trend_report.platform_trends) * 0.8:
            recommendations.append(
                "Strong platform stability achieved - consider expanding test coverage to new scenarios"
            )

        return recommendations[:8]  # Limit to top 8 recommendations

    def _assess_trend_risks(self, trend_report: TrendAnalysisReport) -> Dict[str, str]:
        """Assess risks based on trend patterns."""
        risks = {}

        # Platform risks
        for platform_name, platform_trend in trend_report.platform_trends.items():
            survival_rate = platform_trend.survival_rate.current_value or 0
            trend_direction = platform_trend.survival_rate.trend_direction

            if survival_rate < 60:
                risks[platform_name] = "critical"
            elif survival_rate < 75 or trend_direction == TrendDirection.DECLINING:
                risks[platform_name] = "high"
            elif trend_direction == TrendDirection.VOLATILE:
                risks[platform_name] = "medium"
            else:
                risks[platform_name] = "low"

        # Carrier risks
        for carrier_name, carrier_trend in trend_report.carrier_trends.items():
            success_rate = carrier_trend.success_rate.current_value or 0
            trend_direction = carrier_trend.success_rate.trend_direction

            risk_key = f"carrier_{carrier_name}"

            if success_rate < 70:
                risks[risk_key] = "critical"
            elif success_rate < 85 or trend_direction == TrendDirection.DECLINING:
                risks[risk_key] = "high"
            elif trend_direction == TrendDirection.VOLATILE:
                risks[risk_key] = "medium"
            else:
                risks[risk_key] = "low"

        return risks

    def _deserialize_report(self, report_data: Dict[str, Any]) -> Optional[CompatibilityReport]:
        """Deserialize JSON data back to CompatibilityReport object."""
        try:
            # This is a simplified deserialization - in production you'd want more robust handling
            from datetime import datetime

            report = CompatibilityReport(
                report_id=report_data.get('report_id', ''),
                generated_at=datetime.fromisoformat(report_data.get('generated_at', datetime.now().isoformat())),
                test_configuration=report_data.get('test_configuration', {}),
                overall_metrics=report_data.get('overall_metrics', {}),
                summary=report_data.get('summary', ''),
                recommendations=report_data.get('recommendations', [])
            )

            return report
        except Exception:
            return None

    def generate_trend_report_json(self, trend_report: TrendAnalysisReport) -> str:
        """Generate JSON representation of trend analysis report."""
        def serialize_trend_metric(metric: TrendMetric) -> Dict[str, Any]:
            return {
                'name': metric.name,
                'current_value': metric.current_value,
                'trend_direction': metric.trend_direction.value,
                'change_rate': metric.change_rate,
                'values': metric.values,
                'timestamps': [ts.isoformat() for ts in metric.timestamps]
            }

        report_dict = {
            'report_id': trend_report.report_id,
            'generated_at': trend_report.generated_at.isoformat(),
            'analysis_period': {
                'start': trend_report.analysis_period[0].isoformat(),
                'end': trend_report.analysis_period[1].isoformat()
            },
            'total_test_runs': trend_report.total_test_runs,
            'platform_trends': {
                name: {
                    'platform': trend.platform,
                    'survival_rate': serialize_trend_metric(trend.survival_rate),
                    'critical_failures': serialize_trend_metric(trend.critical_failures),
                    'carrier_success_rate': serialize_trend_metric(trend.carrier_success_rate),
                    'test_count': serialize_trend_metric(trend.test_count)
                }
                for name, trend in trend_report.platform_trends.items()
            },
            'carrier_trends': {
                name: {
                    'carrier_type': trend.carrier_type,
                    'success_rate': serialize_trend_metric(trend.success_rate),
                    'cross_platform_compatibility': serialize_trend_metric(trend.cross_platform_compatibility),
                    'failure_frequency': serialize_trend_metric(trend.failure_frequency)
                }
                for name, trend in trend_report.carrier_trends.items()
            },
            'overall_metrics': {
                name: serialize_trend_metric(metric)
                for name, metric in trend_report.overall_metrics.items()
            },
            'insights': trend_report.insights,
            'recommendations': trend_report.recommendations,
            'risk_assessment': trend_report.risk_assessment
        }

        return json.dumps(report_dict, indent=2)