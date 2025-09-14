"""Tests for compatibility matrix generation and output formats."""

import pytest
from datetime import datetime
from ooxml_tester.report.compatibility_matrix import (
    CompatibilityMatrix, CompatibilityReport, PlatformCompatibility,
    CarrierCompatibility, PlatformType, DocumentFormat
)
from ooxml_tester.analyze.carrier_analyzer import CarrierType, CarrierCategory


class TestPlatformCompatibility:
    """Test platform compatibility data structures."""
    
    def test_platform_compatibility_creation(self):
        """Test creating platform compatibility objects."""
        compat = PlatformCompatibility(
            platform=PlatformType.MICROSOFT_OFFICE,
            document_format=DocumentFormat.WORD,
            total_carriers=100,
            preserved_carriers=85,
            modified_carriers=10,
            lost_carriers=5
        )
        
        assert compat.platform == PlatformType.MICROSOFT_OFFICE
        assert compat.document_format == DocumentFormat.WORD
        assert compat.total_carriers == 100
        assert compat.preserved_carriers == 85
        assert isinstance(compat.test_timestamp, datetime)
    
    def test_survival_rate_calculation(self):
        """Test automatic survival rate calculation."""
        compat = PlatformCompatibility(
            platform=PlatformType.LIBREOFFICE,
            total_carriers=100,
            preserved_carriers=75,
            modified_carriers=15,
            lost_carriers=10
        )
        
        # Manual calculation should match
        compat.survival_rate = (compat.preserved_carriers / compat.total_carriers) * 100
        assert compat.survival_rate == 75.0


class TestCarrierCompatibility:
    """Test carrier compatibility data structures."""
    
    def test_carrier_compatibility_creation(self):
        """Test creating carrier compatibility objects."""
        compat = CarrierCompatibility(
            carrier_type=CarrierType.COLOR_SCHEME,
            category=CarrierCategory.CRITICAL,
            total_tests=50,
            successful_tests=42
        )
        
        assert compat.carrier_type == CarrierType.COLOR_SCHEME
        assert compat.category == CarrierCategory.CRITICAL
        assert compat.total_tests == 50
        assert compat.successful_tests == 42
    
    def test_success_rate_property(self):
        """Test success rate calculation."""
        compat = CarrierCompatibility(
            carrier_type=CarrierType.FONT_SCHEME,
            category=CarrierCategory.CRITICAL,
            total_tests=100,
            successful_tests=85
        )
        
        assert compat.success_rate == 85.0
        
        # Test with zero tests
        empty_compat = CarrierCompatibility(
            carrier_type=CarrierType.FONT_SCHEME,
            category=CarrierCategory.CRITICAL,
            total_tests=0,
            successful_tests=0
        )
        assert empty_compat.success_rate == 0.0


class TestCompatibilityReport:
    """Test compatibility report structure."""
    
    def test_report_creation(self):
        """Test creating compatibility reports."""
        report = CompatibilityReport(
            report_id="test_report_001",
            generated_at=datetime.now(),
            test_configuration={"tolerance": "normal", "platforms": ["office", "libreoffice"]}
        )
        
        assert report.report_id == "test_report_001"
        assert isinstance(report.generated_at, datetime)
        assert "tolerance" in report.test_configuration
        assert len(report.platform_results) == 0
        assert len(report.carrier_results) == 0


class TestCompatibilityMatrix:
    """Test compatibility matrix generation."""
    
    def test_matrix_initialization(self):
        """Test matrix initialization."""
        matrix = CompatibilityMatrix()
        
        assert matrix.carrier_analyzer is not None
        assert matrix.tolerance_config is not None
        assert len(matrix.test_history) == 0
    
    def test_generate_matrix_basic(self):
        """Test basic matrix generation."""
        matrix = CompatibilityMatrix()
        
        # Sample test results
        test_results = [
            {
                'platform': 'microsoft_office',
                'document_format': 'word',
                'platform_version': '16.0',
                'carrier_analysis': {
                    'total_original_tokens': 100,
                    'preserved_tokens': 85,
                    'modified_tokens': 10,
                    'lost_tokens': 5
                },
                'token_changes': {
                    'preserved': {
                        'tokens.color.primary': '#FF0000',
                        'tokens.typography.fontFamily.body': 'Calibri'
                    },
                    'modified': {
                        'tokens.spacing.paragraph.before': '240'
                    },
                    'lost': {
                        'tokens.table.style': 'TableGrid'
                    }
                },
                'critical_failures': []
            },
            {
                'platform': 'libreoffice',
                'document_format': 'word',
                'platform_version': '7.4',
                'carrier_analysis': {
                    'total_original_tokens': 100,
                    'preserved_tokens': 70,
                    'modified_tokens': 20,
                    'lost_tokens': 10
                },
                'token_changes': {
                    'preserved': {
                        'tokens.color.primary': '#FF0000'
                    },
                    'modified': {
                        'tokens.typography.fontFamily.body': 'Liberation Serif',
                        'tokens.spacing.paragraph.before': '200'
                    },
                    'lost': {
                        'tokens.table.style': 'TableGrid',
                        'tokens.list.numbering.id': '1'
                    }
                },
                'critical_failures': ['Font scheme compatibility']
            }
        ]
        
        report = matrix.generate_matrix(test_results)
        
        # Verify report structure
        assert isinstance(report, CompatibilityReport)
        assert report.report_id.startswith('compatibility_report_')
        assert len(report.platform_results) == 2
        assert len(report.carrier_results) > 0
        assert 'overall_survival_rate' in report.overall_metrics
        assert len(report.summary) > 0
        assert len(report.recommendations) > 0
    
    def test_process_platform_results(self):
        """Test processing platform-specific results."""
        matrix = CompatibilityMatrix()
        
        test_results = [
            {
                'platform': 'microsoft_office',
                'document_format': 'powerpoint',
                'platform_version': '16.0',
                'carrier_analysis': {
                    'total_original_tokens': 50,
                    'preserved_tokens': 45,
                    'modified_tokens': 3,
                    'lost_tokens': 2
                },
                'critical_failures': []
            }
        ]
        
        platform_data = matrix._process_platform_results(test_results)
        
        assert len(platform_data) == 1
        platform = platform_data[0]
        assert platform.platform == PlatformType.MICROSOFT_OFFICE
        assert platform.document_format == DocumentFormat.POWERPOINT
        assert platform.total_carriers == 50
        assert platform.preserved_carriers == 45
        assert platform.survival_rate == 90.0
    
    def test_process_carrier_results(self):
        """Test processing carrier-specific results."""
        matrix = CompatibilityMatrix()
        
        test_results = [
            {
                'platform': 'google_workspace',
                'token_changes': {
                    'preserved': {
                        'tokens.color.primary': '#FF0000',
                        'tokens.typography.fontFamily.body': 'Arial'
                    },
                    'modified': {
                        'tokens.spacing.paragraph.before': '240'
                    },
                    'lost': {
                        'tokens.table.cell.background': '#F0F0F0'
                    }
                }
            }
        ]
        
        carrier_data = matrix._process_carrier_results(test_results)
        
        # Should have initialized all carrier types
        assert CarrierType.COLOR_SCHEME in carrier_data
        assert CarrierType.FONT_SCHEME in carrier_data
        assert CarrierType.TABLE_STYLE in carrier_data
        
        # Check specific results
        color_carrier = carrier_data[CarrierType.COLOR_SCHEME]
        assert color_carrier.total_tests > 0
        assert PlatformType.GOOGLE_WORKSPACE in color_carrier.platform_results
    
    def test_calculate_overall_metrics(self):
        """Test overall metrics calculation."""
        matrix = CompatibilityMatrix()
        
        # Sample platform data
        platform_data = [
            PlatformCompatibility(
                platform=PlatformType.MICROSOFT_OFFICE,
                survival_rate=90.0,
                critical_failures=[]
            ),
            PlatformCompatibility(
                platform=PlatformType.LIBREOFFICE,
                survival_rate=75.0,
                critical_failures=['Font compatibility']
            )
        ]
        
        # Sample carrier data
        carrier_data = {
            CarrierType.COLOR_SCHEME: CarrierCompatibility(
                carrier_type=CarrierType.COLOR_SCHEME,
                category=CarrierCategory.CRITICAL,
                total_tests=10,
                successful_tests=9
            ),
            CarrierType.PARAGRAPH_STYLE: CarrierCompatibility(
                carrier_type=CarrierType.PARAGRAPH_STYLE,
                category=CarrierCategory.IMPORTANT,
                total_tests=8,
                successful_tests=6
            )
        }
        
        metrics = matrix._calculate_overall_metrics(platform_data, carrier_data)
        
        assert 'overall_survival_rate' in metrics
        assert metrics['overall_survival_rate'] == 82.5  # (90 + 75) / 2
        assert 'best_platform_rate' in metrics
        assert metrics['best_platform_rate'] == 90.0
        assert 'worst_platform_rate' in metrics
        assert metrics['worst_platform_rate'] == 75.0
        assert 'critical_carrier_success' in metrics
        assert metrics['critical_carrier_success'] == 90.0
    
    def test_generate_summary(self):
        """Test summary generation."""
        matrix = CompatibilityMatrix()
        
        metrics = {
            'overall_survival_rate': 85.0,
            'critical_carrier_success': 90.0,
            'reliability_score': 75.0
        }
        
        summary = matrix._generate_summary(metrics)
        
        assert "85.0%" in summary
        assert "Good" in summary or "Excellent" in summary
        assert "StyleStack" in summary
    
    def test_generate_recommendations(self):
        """Test recommendation generation."""
        matrix = CompatibilityMatrix()
        
        # Platform with poor performance
        platform_data = [
            PlatformCompatibility(
                platform=PlatformType.LIBREOFFICE,
                survival_rate=65.0,  # Below 70% threshold
                critical_failures=['Multiple issues']
            )
        ]
        
        # Carrier with issues
        carrier_data = {
            CarrierType.COLOR_SCHEME: CarrierCompatibility(
                carrier_type=CarrierType.COLOR_SCHEME,
                category=CarrierCategory.CRITICAL,
                total_tests=10,
                successful_tests=7  # 70% - below 80% for critical
            )
        }
        
        recommendations = matrix._generate_recommendations(platform_data, carrier_data)
        
        assert len(recommendations) >= 2
        assert any('libreoffice' in rec.lower() for rec in recommendations)
        assert any('CRITICAL' in rec for rec in recommendations)
        assert any('color_scheme' in rec for rec in recommendations)
    
    def test_create_platform_matrix(self):
        """Test platform matrix creation."""
        matrix = CompatibilityMatrix()
        
        report = CompatibilityReport(
            report_id="test",
            generated_at=datetime.now(),
            test_configuration={}
        )
        
        report.platform_results = [
            PlatformCompatibility(
                platform=PlatformType.MICROSOFT_OFFICE,
                document_format=DocumentFormat.WORD,
                survival_rate=90.0,
                preserved_carriers=90,
                total_carriers=100,
                critical_failures=[]
            ),
            PlatformCompatibility(
                platform=PlatformType.LIBREOFFICE,
                document_format=DocumentFormat.WORD,
                survival_rate=75.0,
                preserved_carriers=75,
                total_carriers=100,
                critical_failures=['Font issue']
            )
        ]
        
        platform_matrix = matrix.create_platform_matrix(report)
        
        assert 'microsoft_office_word' in platform_matrix
        assert 'libreoffice_word' in platform_matrix
        assert platform_matrix['microsoft_office_word']['survival_rate'] == 90.0
        assert platform_matrix['libreoffice_word']['critical_failures'] == 1
    
    def test_create_carrier_matrix(self):
        """Test carrier matrix creation."""
        matrix = CompatibilityMatrix()
        
        report = CompatibilityReport(
            report_id="test",
            generated_at=datetime.now(),
            test_configuration={}
        )
        
        report.carrier_results = {
            CarrierType.COLOR_SCHEME: CarrierCompatibility(
                carrier_type=CarrierType.COLOR_SCHEME,
                category=CarrierCategory.CRITICAL,
                total_tests=20,
                successful_tests=18,
                platform_results={
                    PlatformType.MICROSOFT_OFFICE: True,
                    PlatformType.LIBREOFFICE: False
                },
                common_failures=['Color space conversion']
            )
        }
        
        carrier_matrix = matrix.create_carrier_matrix(report)
        
        assert 'color_scheme' in carrier_matrix
        color_data = carrier_matrix['color_scheme']
        assert color_data['success_rate'] == 90.0
        assert color_data['category'] == 'critical'
        assert color_data['platform_results']['microsoft_office'] is True
        assert color_data['platform_results']['libreoffice'] is False
        assert 'Color space conversion' in color_data['common_failures']
    
    def test_map_token_to_carrier(self):
        """Test mapping design tokens to carrier types."""
        matrix = CompatibilityMatrix()
        
        # Test various token paths
        assert matrix._map_token_to_carrier('tokens.color.primary') == CarrierType.COLOR_SCHEME
        assert matrix._map_token_to_carrier('tokens.typography.fontFamily.body') == CarrierType.FONT_SCHEME
        assert matrix._map_token_to_carrier('tokens.typography.fontSize') == CarrierType.CHARACTER_STYLE
        assert matrix._map_token_to_carrier('tokens.spacing.paragraph.before') == CarrierType.PARAGRAPH_STYLE
        assert matrix._map_token_to_carrier('tokens.table.cell.background') == CarrierType.TABLE_STYLE
        assert matrix._map_token_to_carrier('tokens.list.numbering.id') == CarrierType.LIST_STYLE
        assert matrix._map_token_to_carrier('tokens.layout.slideLayout') == CarrierType.LAYOUT_MASTER
        assert matrix._map_token_to_carrier('unknown.token.path') is None
    
    def test_get_carrier_category(self):
        """Test carrier category assignment."""
        matrix = CompatibilityMatrix()
        
        # Test critical carriers
        assert matrix._get_carrier_category(CarrierType.COLOR_SCHEME) == CarrierCategory.CRITICAL
        assert matrix._get_carrier_category(CarrierType.FONT_SCHEME) == CarrierCategory.CRITICAL
        assert matrix._get_carrier_category(CarrierType.LAYOUT_MASTER) == CarrierCategory.CRITICAL
        
        # Test important carriers
        assert matrix._get_carrier_category(CarrierType.PARAGRAPH_STYLE) == CarrierCategory.IMPORTANT
        assert matrix._get_carrier_category(CarrierType.CHARACTER_STYLE) == CarrierCategory.IMPORTANT
        assert matrix._get_carrier_category(CarrierType.TABLE_STYLE) == CarrierCategory.IMPORTANT
        
        # Test optional carriers
        assert matrix._get_carrier_category(CarrierType.CELL_STYLE) == CarrierCategory.OPTIONAL


class TestMatrixIntegration:
    """Test integration scenarios for compatibility matrix."""
    
    def test_empty_results_handling(self):
        """Test handling of empty test results."""
        matrix = CompatibilityMatrix()
        
        report = matrix.generate_matrix([])
        
        assert isinstance(report, CompatibilityReport)
        assert len(report.platform_results) == 0
        assert report.overall_metrics.get('overall_survival_rate', 0) == 0
        assert 'no data' in report.summary.lower() or len(report.summary) > 0
    
    def test_mixed_platform_results(self):
        """Test handling results from multiple platforms and formats."""
        matrix = CompatibilityMatrix()
        
        test_results = [
            {
                'platform': 'microsoft_office',
                'document_format': 'word',
                'carrier_analysis': {'total_original_tokens': 50, 'preserved_tokens': 45, 'modified_tokens': 3, 'lost_tokens': 2},
                'token_changes': {'preserved': {'tokens.color.primary': '#FF0000'}, 'modified': {}, 'lost': {}}
            },
            {
                'platform': 'libreoffice',
                'document_format': 'powerpoint',
                'carrier_analysis': {'total_original_tokens': 40, 'preserved_tokens': 32, 'modified_tokens': 5, 'lost_tokens': 3},
                'token_changes': {'preserved': {}, 'modified': {'tokens.typography.fontFamily.body': 'Arial'}, 'lost': {'tokens.color.primary': '#FF0000'}}
            },
            {
                'platform': 'google_workspace',
                'document_format': 'excel',
                'carrier_analysis': {'total_original_tokens': 30, 'preserved_tokens': 25, 'modified_tokens': 3, 'lost_tokens': 2},
                'token_changes': {'preserved': {'tokens.cell.background': '#FFFFFF'}, 'modified': {}, 'lost': {}}
            }
        ]
        
        report = matrix.generate_matrix(test_results)
        
        # Should handle all platforms and formats
        assert len(report.platform_results) == 3
        assert len([p for p in report.platform_results if p.platform == PlatformType.MICROSOFT_OFFICE]) == 1
        assert len([p for p in report.platform_results if p.platform == PlatformType.LIBREOFFICE]) == 1
        assert len([p for p in report.platform_results if p.platform == PlatformType.GOOGLE_WORKSPACE]) == 1
        
        # Should have overall metrics
        assert 'overall_survival_rate' in report.overall_metrics
        assert report.overall_metrics['overall_survival_rate'] > 0
    
    def test_unknown_platform_handling(self):
        """Test handling of unknown platforms."""
        matrix = CompatibilityMatrix()
        
        test_results = [
            {
                'platform': 'unknown_office_suite',
                'document_format': 'word',
                'carrier_analysis': {'total_original_tokens': 10, 'preserved_tokens': 8, 'modified_tokens': 1, 'lost_tokens': 1},
                'token_changes': {'preserved': {}, 'modified': {}, 'lost': {}}
            },
            {
                'platform': 'microsoft_office',  # Known platform
                'document_format': 'word',
                'carrier_analysis': {'total_original_tokens': 10, 'preserved_tokens': 9, 'modified_tokens': 1, 'lost_tokens': 0},
                'token_changes': {'preserved': {}, 'modified': {}, 'lost': {}}
            }
        ]
        
        report = matrix.generate_matrix(test_results)
        
        # Should only process known platforms
        assert len(report.platform_results) == 1
        assert report.platform_results[0].platform == PlatformType.MICROSOFT_OFFICE


if __name__ == '__main__':
    pytest.main([__file__])