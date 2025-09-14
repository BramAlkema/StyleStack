"""Compatibility matrix generation for StyleStack design token survival rates."""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from pathlib import Path

from ..analyze.carrier_analyzer import StyleStackCarrierAnalyzer, CarrierType, CarrierCategory
from ..analyze.tolerance_config import ToleranceConfiguration


class PlatformType(Enum):
    """Platform types for compatibility testing."""
    MICROSOFT_OFFICE = "microsoft_office"
    LIBREOFFICE = "libreoffice"
    GOOGLE_WORKSPACE = "google_workspace"
    APPLE_PAGES = "apple_pages"
    WPS_OFFICE = "wps_office"


class DocumentFormat(Enum):
    """Document formats for testing."""
    WORD = "word"
    POWERPOINT = "powerpoint"
    EXCEL = "excel"


@dataclass
class PlatformCompatibility:
    """Compatibility data for a specific platform."""
    platform: PlatformType
    version: Optional[str] = None
    document_format: Optional[DocumentFormat] = None
    total_carriers: int = 0
    preserved_carriers: int = 0
    modified_carriers: int = 0
    lost_carriers: int = 0
    survival_rate: float = 0.0
    critical_failures: List[str] = field(default_factory=list)
    test_timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.test_timestamp is None:
            self.test_timestamp = datetime.now()


@dataclass
class CarrierCompatibility:
    """Compatibility data for a specific carrier type."""
    carrier_type: CarrierType
    category: CarrierCategory
    total_tests: int = 0
    successful_tests: int = 0
    platform_results: Dict[PlatformType, bool] = field(default_factory=dict)
    common_failures: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate across all tests."""
        if self.total_tests == 0:
            return 0.0
        return (self.successful_tests / self.total_tests) * 100


@dataclass
class StyleStackCarrierMatrix:
    """StyleStack design token carrier survival matrix."""
    carrier_survival_rates: Dict[str, Dict[str, float]] = field(default_factory=dict)
    platform_carrier_matrix: Dict[str, Dict[str, bool]] = field(default_factory=dict)
    critical_carrier_status: Dict[str, str] = field(default_factory=dict)
    design_token_mapping: Dict[str, List[str]] = field(default_factory=dict)
    risk_assessment: Dict[str, str] = field(default_factory=dict)


@dataclass
class CompatibilityReport:
    """Comprehensive compatibility report."""
    report_id: str
    generated_at: datetime
    test_configuration: Dict[str, Any]
    platform_results: List[PlatformCompatibility] = field(default_factory=list)
    carrier_results: Dict[CarrierType, CarrierCompatibility] = field(default_factory=dict)
    stylestack_matrix: Optional[StyleStackCarrierMatrix] = None
    overall_metrics: Dict[str, float] = field(default_factory=dict)
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)


class CompatibilityMatrix:
    """Generates compatibility matrices for StyleStack design tokens."""
    
    def __init__(self):
        self.carrier_analyzer = StyleStackCarrierAnalyzer()
        self.tolerance_config = ToleranceConfiguration()
        self.test_history = []
    
    def generate_matrix(self, test_results: List[Dict[str, Any]], 
                       report_config: Optional[Dict[str, Any]] = None) -> CompatibilityReport:
        """
        Generate compatibility matrix from test results.
        
        Args:
            test_results: List of test result dictionaries
            report_config: Optional configuration for report generation
            
        Returns:
            Comprehensive compatibility report
        """
        if report_config is None:
            report_config = {}
        
        report_id = f"compatibility_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        report = CompatibilityReport(
            report_id=report_id,
            generated_at=datetime.now(),
            test_configuration=report_config
        )
        
        # Process platform results
        platform_data = self._process_platform_results(test_results)
        report.platform_results = platform_data
        
        # Process carrier results
        carrier_data = self._process_carrier_results(test_results)
        report.carrier_results = carrier_data
        
        # Calculate overall metrics
        report.overall_metrics = self._calculate_overall_metrics(
            platform_data, carrier_data
        )
        
        # Generate StyleStack carrier matrix
        report.stylestack_matrix = self._generate_stylestack_matrix(
            platform_data, carrier_data, test_results
        )

        # Generate summary and recommendations
        report.summary = self._generate_summary(report.overall_metrics)
        report.recommendations = self._generate_recommendations(
            platform_data, carrier_data
        )

        return report
    
    def _process_platform_results(self, test_results: List[Dict[str, Any]]) -> List[PlatformCompatibility]:
        """Process test results by platform."""
        platform_data = {}
        
        for result in test_results:
            platform_name = result.get('platform', 'unknown')
            document_format = result.get('document_format', 'word')
            
            # Map platform names to enum
            try:
                platform = PlatformType(platform_name.lower())
            except ValueError:
                continue  # Skip unknown platforms
            
            try:
                doc_format = DocumentFormat(document_format.lower())
            except ValueError:
                doc_format = DocumentFormat.WORD
            
            key = (platform, doc_format)
            
            if key not in platform_data:
                platform_data[key] = PlatformCompatibility(
                    platform=platform,
                    document_format=doc_format,
                    version=result.get('platform_version')
                )
            
            # Aggregate data
            compat = platform_data[key]
            carrier_analysis = result.get('carrier_analysis', {})
            
            if carrier_analysis:
                compat.total_carriers += carrier_analysis.get('total_original_tokens', 0)
                compat.preserved_carriers += carrier_analysis.get('preserved_tokens', 0)
                compat.modified_carriers += carrier_analysis.get('modified_tokens', 0)
                compat.lost_carriers += carrier_analysis.get('lost_tokens', 0)
                
                # Update survival rate
                if compat.total_carriers > 0:
                    compat.survival_rate = (compat.preserved_carriers / compat.total_carriers) * 100
                
                # Collect critical failures
                critical_failures = result.get('critical_failures', [])
                compat.critical_failures.extend(critical_failures)
        
        return list(platform_data.values())
    
    def _process_carrier_results(self, test_results: List[Dict[str, Any]]) -> Dict[CarrierType, CarrierCompatibility]:
        """Process test results by carrier type."""
        carrier_data = {}
        
        # Initialize all carrier types
        for carrier_type in CarrierType:
            carrier_data[carrier_type] = CarrierCompatibility(
                carrier_type=carrier_type,
                category=self._get_carrier_category(carrier_type)
            )
        
        # Process results
        for result in test_results:
            platform_name = result.get('platform', 'unknown')
            try:
                platform = PlatformType(platform_name.lower())
            except ValueError:
                continue
            
            token_changes = result.get('token_changes', {})
            preserved = token_changes.get('preserved', {})
            modified = token_changes.get('modified', {})
            lost = token_changes.get('lost', {})
            
            # Map token paths to carrier types
            all_tokens = {**preserved, **modified, **lost}
            
            for token_path, value in all_tokens.items():
                carrier_type = self._map_token_to_carrier(token_path)
                if carrier_type and carrier_type in carrier_data:
                    compat = carrier_data[carrier_type]
                    compat.total_tests += 1
                    
                    # Token was preserved or only modified (not lost)
                    if token_path in preserved or token_path in modified:
                        compat.successful_tests += 1
                        compat.platform_results[platform] = True
                    else:
                        compat.platform_results[platform] = False
                        # Track common failures
                        failure_reason = f"Lost on {platform.value}"
                        if failure_reason not in compat.common_failures:
                            compat.common_failures.append(failure_reason)
        
        return carrier_data
    
    def _get_carrier_category(self, carrier_type: CarrierType) -> CarrierCategory:
        """Get the category for a carrier type."""
        # Map carrier types to categories
        critical_carriers = {
            CarrierType.COLOR_SCHEME,
            CarrierType.FONT_SCHEME,
            CarrierType.LAYOUT_MASTER
        }
        
        important_carriers = {
            CarrierType.PARAGRAPH_STYLE,
            CarrierType.CHARACTER_STYLE,
            CarrierType.TABLE_STYLE,
            CarrierType.LIST_STYLE
        }
        
        if carrier_type in critical_carriers:
            return CarrierCategory.CRITICAL
        elif carrier_type in important_carriers:
            return CarrierCategory.IMPORTANT
        else:
            return CarrierCategory.OPTIONAL
    
    def _map_token_to_carrier(self, token_path: str) -> Optional[CarrierType]:
        """Map a design token path to a carrier type."""
        # Simple mapping based on token path
        token_mapping = {
            'color': CarrierType.COLOR_SCHEME,
            'typography.fontFamily': CarrierType.FONT_SCHEME,
            'typography.fontSize': CarrierType.CHARACTER_STYLE,
            'typography.styles': CarrierType.PARAGRAPH_STYLE,
            'spacing': CarrierType.PARAGRAPH_STYLE,
            'table': CarrierType.TABLE_STYLE,
            'list': CarrierType.LIST_STYLE,
            'layout': CarrierType.LAYOUT_MASTER,
            'cell': CarrierType.CELL_STYLE
        }
        
        for key, carrier_type in token_mapping.items():
            if key in token_path:
                return carrier_type
        
        return None
    
    def _calculate_overall_metrics(self, platform_data: List[PlatformCompatibility],
                                  carrier_data: Dict[CarrierType, CarrierCompatibility]) -> Dict[str, float]:
        """Calculate overall compatibility metrics."""
        metrics = {}
        
        # Platform metrics
        if platform_data:
            total_survival_rate = sum(p.survival_rate for p in platform_data) / len(platform_data)
            metrics['overall_survival_rate'] = total_survival_rate
            
            # Best and worst platforms
            best_platform = max(platform_data, key=lambda p: p.survival_rate)
            worst_platform = min(platform_data, key=lambda p: p.survival_rate)
            
            metrics['best_platform_rate'] = best_platform.survival_rate
            metrics['worst_platform_rate'] = worst_platform.survival_rate
            metrics['platform_variance'] = best_platform.survival_rate - worst_platform.survival_rate
        
        # Carrier metrics
        if carrier_data:
            # Critical carrier success rates
            critical_carriers = [c for c in carrier_data.values() 
                               if c.category == CarrierCategory.CRITICAL]
            if critical_carriers:
                critical_success = sum(c.success_rate for c in critical_carriers) / len(critical_carriers)
                metrics['critical_carrier_success'] = critical_success
            
            # Overall carrier success
            all_success_rates = [c.success_rate for c in carrier_data.values() if c.total_tests > 0]
            if all_success_rates:
                metrics['overall_carrier_success'] = sum(all_success_rates) / len(all_success_rates)
        
        # Reliability metrics
        total_tests = sum(len(p.critical_failures) for p in platform_data)
        critical_failures = sum(1 for p in platform_data if p.critical_failures)
        
        if len(platform_data) > 0:
            metrics['reliability_score'] = ((len(platform_data) - critical_failures) / len(platform_data)) * 100
        
        return metrics
    
    def _generate_summary(self, metrics: Dict[str, float]) -> str:
        """Generate a summary of the compatibility report."""
        overall_rate = metrics.get('overall_survival_rate', 0)
        critical_success = metrics.get('critical_carrier_success', 0)
        reliability = metrics.get('reliability_score', 0)
        
        if overall_rate >= 90:
            grade = "Excellent"
        elif overall_rate >= 75:
            grade = "Good"
        elif overall_rate >= 60:
            grade = "Fair"
        else:
            grade = "Poor"
        
        summary = f"""
StyleStack Compatibility Analysis Summary:

Overall Design Token Survival Rate: {overall_rate:.1f}% ({grade})
Critical Carrier Success Rate: {critical_success:.1f}%
Platform Reliability Score: {reliability:.1f}%

The StyleStack design system shows {grade.lower()} compatibility across tested platforms.
        """.strip()
        
        return summary
    
    def _generate_recommendations(self, platform_data: List[PlatformCompatibility],
                                 carrier_data: Dict[CarrierType, CarrierCompatibility]) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        # Platform-specific recommendations
        poor_platforms = [p for p in platform_data if p.survival_rate < 70]
        for platform in poor_platforms:
            recommendations.append(
                f"Consider optimizing templates for {platform.platform.value} "
                f"(current survival rate: {platform.survival_rate:.1f}%)"
            )
        
        # Carrier-specific recommendations
        failing_carriers = [c for c in carrier_data.values() 
                           if c.success_rate < 50 and c.total_tests > 0]
        for carrier in failing_carriers:
            recommendations.append(
                f"Review {carrier.carrier_type.value} implementation "
                f"(success rate: {carrier.success_rate:.1f}%)"
            )
        
        # Critical carrier recommendations
        critical_issues = [c for c in carrier_data.values() 
                          if c.category == CarrierCategory.CRITICAL and c.success_rate < 80]
        for carrier in critical_issues:
            recommendations.append(
                f"CRITICAL: Fix {carrier.carrier_type.value} compatibility issues "
                f"(success rate: {carrier.success_rate:.1f}%)"
            )
        
        if not recommendations:
            recommendations.append("Compatibility looks good across all tested platforms and carriers.")
        
        return recommendations
    
    def create_platform_matrix(self, report: CompatibilityReport) -> Dict[str, Dict[str, float]]:
        """Create platform compatibility matrix."""
        matrix = {}
        
        for platform_result in report.platform_results:
            platform_key = f"{platform_result.platform.value}"
            if platform_result.document_format:
                platform_key += f"_{platform_result.document_format.value}"
            
            matrix[platform_key] = {
                'survival_rate': platform_result.survival_rate,
                'preserved_carriers': platform_result.preserved_carriers,
                'total_carriers': platform_result.total_carriers,
                'critical_failures': len(platform_result.critical_failures)
            }
        
        return matrix
    
    def create_carrier_matrix(self, report: CompatibilityReport) -> Dict[str, Dict[str, Any]]:
        """Create carrier compatibility matrix."""
        matrix = {}
        
        for carrier_type, carrier_result in report.carrier_results.items():
            matrix[carrier_type.value] = {
                'success_rate': carrier_result.success_rate,
                'category': carrier_result.category.value,
                'total_tests': carrier_result.total_tests,
                'platform_results': {
                    platform.value: success 
                    for platform, success in carrier_result.platform_results.items()
                },
                'common_failures': carrier_result.common_failures
            }

        return matrix

    def _generate_stylestack_matrix(self, platform_data: List[PlatformCompatibility],
                                   carrier_data: Dict, test_results: List[Dict[str, Any]]) -> StyleStackCarrierMatrix:
        """Generate StyleStack-specific carrier compatibility matrix with design token mappings."""
        matrix = StyleStackCarrierMatrix()

        # Map each carrier type to StyleStack design tokens
        carrier_design_tokens = {
            'color_scheme': ['color.background', 'color.primary', 'color.secondary', 'color.accent'],
            'typography': ['font.family.body', 'font.family.heading', 'font.size.base', 'font.weight.normal'],
            'spacing': ['spacing.xs', 'spacing.sm', 'spacing.md', 'spacing.lg', 'spacing.xl'],
            'layout': ['layout.grid.columns', 'layout.breakpoint.md', 'layout.container.width'],
            'theme': ['theme.mode', 'theme.contrast', 'theme.accessibility.high-contrast'],
            'borders': ['border.radius.sm', 'border.radius.md', 'border.width.thin', 'border.color.default'],
            'shadows': ['shadow.sm', 'shadow.md', 'shadow.lg', 'shadow.color'],
            'animation': ['animation.duration.fast', 'animation.easing.ease-out'],
            'icons': ['icon.size.sm', 'icon.color.primary', 'icon.stroke.width'],
            'shapes': ['shape.corner.radius', 'shape.fill.opacity', 'shape.stroke.width'],
            'tables': ['table.border.color', 'table.header.background', 'table.row.alternate'],
            'media': ['media.aspect.ratio', 'media.border.radius'],
            'forms': ['form.input.border', 'form.label.color', 'form.focus.outline'],
            'navigation': ['nav.link.color', 'nav.active.background', 'nav.hover.color'],
            'branding': ['brand.logo.height', 'brand.color.primary', 'brand.font.family'],
            'accessibility': ['a11y.focus.ring', 'a11y.contrast.ratio', 'a11y.text.size'],
            'print': ['print.margin.top', 'print.color.mode', 'print.font.size']
        }

        # Calculate survival rates for each carrier across platforms
        for carrier_type, carrier_result in carrier_data.items():
            carrier_name = carrier_type.value.lower()
            matrix.carrier_survival_rates[carrier_name] = {}
            matrix.platform_carrier_matrix[carrier_name] = {}

            # Map design tokens to this carrier
            if carrier_name in carrier_design_tokens:
                matrix.design_token_mapping[carrier_name] = carrier_design_tokens[carrier_name]
            else:
                matrix.design_token_mapping[carrier_name] = [f"{carrier_name}.default"]

            # Calculate platform-specific survival rates
            for platform_result in platform_data:
                platform_name = platform_result.platform.value

                # Calculate survival rate for this carrier on this platform
                if carrier_result.total_tests > 0:
                    platform_success = carrier_result.platform_results.get(
                        platform_result.platform, False
                    )
                    survival_rate = carrier_result.success_rate if platform_success else 0.0
                else:
                    survival_rate = 0.0

                matrix.carrier_survival_rates[carrier_name][platform_name] = survival_rate
                matrix.platform_carrier_matrix[carrier_name][platform_name] = survival_rate >= 75.0

            # Determine critical status
            if carrier_result.category.value == 'critical':
                if carrier_result.success_rate >= 90:
                    matrix.critical_carrier_status[carrier_name] = 'stable'
                elif carrier_result.success_rate >= 75:
                    matrix.critical_carrier_status[carrier_name] = 'warning'
                else:
                    matrix.critical_carrier_status[carrier_name] = 'critical'
            else:
                matrix.critical_carrier_status[carrier_name] = 'non-critical'

            # Risk assessment based on success rate and cross-platform compatibility
            cross_platform_support = sum(matrix.platform_carrier_matrix[carrier_name].values())
            total_platforms = len(matrix.platform_carrier_matrix[carrier_name])

            if carrier_result.success_rate >= 90 and cross_platform_support == total_platforms:
                matrix.risk_assessment[carrier_name] = 'low'
            elif carrier_result.success_rate >= 75 and cross_platform_support >= total_platforms * 0.7:
                matrix.risk_assessment[carrier_name] = 'medium'
            else:
                matrix.risk_assessment[carrier_name] = 'high'

        return matrix

    def get_stylestack_recommendations(self, matrix: StyleStackCarrierMatrix) -> List[str]:
        """Generate StyleStack-specific recommendations from carrier matrix."""
        recommendations = []

        # Check for high-risk carriers
        high_risk_carriers = [
            carrier for carrier, risk in matrix.risk_assessment.items()
            if risk == 'high'
        ]

        if high_risk_carriers:
            recommendations.append(
                f"HIGH PRIORITY: Review design tokens for high-risk carriers: {', '.join(high_risk_carriers)}"
            )

        # Check for critical carrier failures
        critical_failures = [
            carrier for carrier, status in matrix.critical_carrier_status.items()
            if status == 'critical'
        ]

        if critical_failures:
            recommendations.append(
                f"CRITICAL: Address failing critical carriers: {', '.join(critical_failures)}"
            )

        # Check for platform-specific issues
        platform_issues = {}
        for carrier, platform_results in matrix.platform_carrier_matrix.items():
            for platform, success in platform_results.items():
                if not success:
                    if platform not in platform_issues:
                        platform_issues[platform] = []
                    platform_issues[platform].append(carrier)

        for platform, failing_carriers in platform_issues.items():
            if len(failing_carriers) >= 3:  # Multiple carrier failures on one platform
                recommendations.append(
                    f"Platform-specific issue detected on {platform}: "
                    f"Multiple carrier failures ({', '.join(failing_carriers[:3])})"
                )

        # Check for design token coverage gaps
        low_coverage_tokens = []
        for carrier, tokens in matrix.design_token_mapping.items():
            if matrix.risk_assessment.get(carrier, 'high') == 'high' and len(tokens) > 3:
                low_coverage_tokens.extend(tokens[:2])  # Take first 2 tokens as examples

        if low_coverage_tokens:
            recommendations.append(
                f"Design token coverage review needed for: {', '.join(set(low_coverage_tokens))}"
            )

        return recommendations[:10]  # Limit to top 10 recommendations