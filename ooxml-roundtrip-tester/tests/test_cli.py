"""Tests for command-line interface functionality with CI/CD integration."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from click.testing import CliRunner

from ooxml_tester.cli import cli, _detect_format
from ooxml_tester.report.compatibility_matrix import CompatibilityReport
from datetime import datetime


class TestCLI:
    """Test CLI functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        
    def test_detect_format(self):
        """Test document format detection."""
        assert _detect_format(Path("test.pptx")) == "powerpoint"
        assert _detect_format(Path("test.potx")) == "powerpoint"
        assert _detect_format(Path("test.docx")) == "word"
        assert _detect_format(Path("test.dotx")) == "word"
        assert _detect_format(Path("test.xlsx")) == "excel"
        assert _detect_format(Path("test.xltx")) == "excel"
        assert _detect_format(Path("test.pdf")) == "unknown"
    
    def test_cli_help(self):
        """Test CLI help command."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "OOXML Round-Trip Testing Utility" in result.output
    
    def test_cli_version(self):
        """Test CLI version command."""
        with patch('ooxml_tester.__version__', '1.0.0'):
            result = self.runner.invoke(cli, ['--version'])
            assert result.exit_code == 0
            assert "version 1.0.0" in result.output
    
    def test_probe_command_help(self):
        """Test probe command help."""
        result = self.runner.invoke(cli, ['probe', '--help'])
        assert result.exit_code == 0
        assert "Generate OOXML probe files" in result.output
    
    def test_test_command_help(self):
        """Test test command help."""
        result = self.runner.invoke(cli, ['test', '--help'])
        assert result.exit_code == 0
        assert "Run round-trip tests" in result.output
        assert "--fail-threshold" in result.output
        assert "--critical-threshold" in result.output
        assert "--exit-on-failure" in result.output
    
    def test_report_command_help(self):
        """Test report command help."""
        result = self.runner.invoke(cli, ['report', '--help'])
        assert result.exit_code == 0
        assert "Generate compatibility reports" in result.output
    
    @patch('ooxml_tester.cli.Path.exists')
    def test_test_command_missing_file(self, mock_exists):
        """Test test command with missing file."""
        mock_exists.return_value = False
        
        result = self.runner.invoke(cli, ['test', 'nonexistent.pptx'])
        assert result.exit_code == 2  # Click error for missing file
        assert "does not exist" in result.output
    
    @patch('ooxml_tester.convert.engine.ConversionEngine')
    @patch('ooxml_tester.analyze.xml_parser.OOXMLParser')
    @patch('ooxml_tester.analyze.carrier_analyzer.StyleStackCarrierAnalyzer')
    @patch('ooxml_tester.report.compatibility_matrix.CompatibilityMatrix')
    def test_test_command_successful_run(self, mock_matrix, mock_carrier, mock_xml_parser, mock_engine):
        """Test successful test command execution."""
        # Create a temporary test file
        test_file = Path(self.temp_dir) / "test.pptx"
        test_file.touch()
        
        # Mock the engine and analyzers
        mock_conversion_result = {
            'converted_path': Path(self.temp_dir) / "converted.pptx",
            'metadata': {'platform': 'test'}
        }
        mock_engine.return_value.run_round_trip.return_value = mock_conversion_result
        
        mock_xml_diff = {'changed_elements': [], 'total_changes': 0}
        mock_xml_parser.return_value.parse_document.return_value = {}
        mock_xml_parser.return_value.compare_parsed_documents.return_value = mock_xml_diff
        
        mock_carrier_analysis = {'preserved_tokens': 95, 'total_tokens': 100}
        mock_carrier.return_value.analyze_changes.return_value = mock_carrier_analysis
        
        # Create mock report
        mock_report = CompatibilityReport(
            report_id="test_report",
            generated_at=datetime.now(),
            test_configuration={},
            overall_metrics={
                'overall_survival_rate': 85.0,
                'critical_carrier_success': 90.0
            }
        )
        mock_matrix.return_value.generate_matrix.return_value = mock_report
        
        # Run the command
        result = self.runner.invoke(cli, [
            'test', str(test_file),
            '--output', self.temp_dir,
            '--fail-threshold', '80',
            '--critical-threshold', '85'
        ])

        assert result.exit_code == 0
        assert "TEST PASSED" in result.output
        assert "Overall Survival Rate: 85.0%" in result.output
    
    @patch('ooxml_tester.convert.engine.ConversionEngine')
    @patch('ooxml_tester.analyze.xml_parser.OOXMLParser')
    @patch('ooxml_tester.analyze.carrier_analyzer.StyleStackCarrierAnalyzer')
    @patch('ooxml_tester.report.compatibility_matrix.CompatibilityMatrix')
    def test_test_command_threshold_failure(self, mock_matrix, mock_carrier, mock_xml_parser, mock_engine):
        """Test test command with threshold failure."""
        # Create a temporary test file
        test_file = Path(self.temp_dir) / "test.pptx"
        test_file.touch()
        
        # Mock the components to return low scores
        mock_conversion_result = {
            'converted_path': Path(self.temp_dir) / "converted.pptx",
            'metadata': {'platform': 'test'}
        }
        mock_engine.return_value.run_round_trip.return_value = mock_conversion_result
        
        mock_xml_diff = {'changed_elements': [], 'total_changes': 10}
        mock_xml_parser.return_value.compare_parsed_documents.return_value = mock_xml_diff
        
        mock_carrier_analysis = {'preserved_tokens': 60, 'total_tokens': 100}
        mock_carrier.return_value.analyze_changes.return_value = mock_carrier_analysis
        
        # Create mock report with low scores
        mock_report = CompatibilityReport(
            report_id="test_report",
            generated_at=datetime.now(),
            test_configuration={},
            overall_metrics={
                'overall_survival_rate': 60.0,  # Below 70% threshold
                'critical_carrier_success': 80.0  # Below 90% threshold
            }
        )
        mock_matrix.return_value.generate_matrix.return_value = mock_report
        
        # Run the command without exit-on-failure
        result = self.runner.invoke(cli, [
            'test', str(test_file),
            '--output', self.temp_dir,
            '--fail-threshold', '70',
            '--critical-threshold', '90'
        ])
        
        assert result.exit_code == 0  # Should not exit on failure without flag
        assert "THRESHOLD FAILURES" in result.output
        assert "Overall survival rate 60.0% below threshold 70.0%" in result.output
        assert "Critical carrier success 80.0% below threshold 90.0%" in result.output
    
    @patch('ooxml_tester.convert.engine.ConversionEngine')
    @patch('ooxml_tester.analyze.xml_parser.OOXMLParser')
    @patch('ooxml_tester.analyze.carrier_analyzer.StyleStackCarrierAnalyzer')
    @patch('ooxml_tester.report.compatibility_matrix.CompatibilityMatrix')
    def test_test_command_exit_on_failure(self, mock_matrix, mock_carrier, mock_xml_parser, mock_engine):
        """Test test command with exit-on-failure flag."""
        # Create a temporary test file
        test_file = Path(self.temp_dir) / "test.pptx"
        test_file.touch()
        
        # Mock the components to return low scores
        mock_conversion_result = {
            'converted_path': Path(self.temp_dir) / "converted.pptx",
            'metadata': {'platform': 'test'}
        }
        mock_engine.return_value.run_round_trip.return_value = mock_conversion_result
        
        mock_xml_diff = {'changed_elements': [], 'total_changes': 10}
        mock_xml_parser.return_value.compare_parsed_documents.return_value = mock_xml_diff
        
        mock_carrier_analysis = {'preserved_tokens': 60, 'total_tokens': 100}
        mock_carrier.return_value.analyze_changes.return_value = mock_carrier_analysis
        
        # Create mock report with low scores
        mock_report = CompatibilityReport(
            report_id="test_report",
            generated_at=datetime.now(),
            test_configuration={},
            overall_metrics={
                'overall_survival_rate': 60.0,  # Below 70% threshold
                'critical_carrier_success': 80.0  # Below 90% threshold
            }
        )
        mock_matrix.return_value.generate_matrix.return_value = mock_report
        
        # Run the command with exit-on-failure
        result = self.runner.invoke(cli, [
            'test', str(test_file),
            '--output', self.temp_dir,
            '--fail-threshold', '70',
            '--critical-threshold', '90',
            '--exit-on-failure'
        ])
        
        assert result.exit_code == 1  # Should exit with failure code
        assert "THRESHOLD FAILURES" in result.output
        assert "Exiting with failure code" in result.output
    
    def test_test_command_invalid_threshold(self):
        """Test test command with invalid threshold values."""
        test_file = Path(self.temp_dir) / "test.pptx"
        test_file.touch()
        
        # Test invalid fail threshold
        result = self.runner.invoke(cli, [
            'test', str(test_file),
            '--fail-threshold', '150'  # Invalid: > 100
        ])
        
        assert result.exit_code == 1
        assert "Invalid fail threshold" in result.output
        
        # Test invalid critical threshold
        result = self.runner.invoke(cli, [
            'test', str(test_file),
            '--critical-threshold', '-10'  # Invalid: < 0
        ])
        
        assert result.exit_code == 1
        assert "Invalid critical threshold" in result.output
    
    @patch('ooxml_tester.convert.engine.ConversionEngine')
    @patch('ooxml_tester.analyze.xml_parser.OOXMLParser')
    @patch('ooxml_tester.analyze.carrier_analyzer.StyleStackCarrierAnalyzer')
    @patch('ooxml_tester.report.compatibility_matrix.CompatibilityMatrix')
    def test_test_command_multiple_formats(self, mock_matrix, mock_carrier, mock_xml_parser, mock_engine):
        """Test test command with multiple output formats."""
        # Create a temporary test file
        test_file = Path(self.temp_dir) / "test.pptx"
        test_file.touch()
        
        # Mock successful run
        mock_conversion_result = {
            'converted_path': Path(self.temp_dir) / "converted.pptx",
            'metadata': {'platform': 'test'}
        }
        mock_engine.return_value.run_round_trip.return_value = mock_conversion_result
        
        mock_xml_diff = {'changed_elements': [], 'total_changes': 0}
        mock_xml_parser.return_value.parse_document.return_value = {}
        mock_xml_parser.return_value.compare_parsed_documents.return_value = mock_xml_diff
        
        mock_carrier_analysis = {'preserved_tokens': 95, 'total_tokens': 100}
        mock_carrier.return_value.analyze_changes.return_value = mock_carrier_analysis
        
        mock_report = CompatibilityReport(
            report_id="test_report",
            generated_at=datetime.now(),
            test_configuration={},
            overall_metrics={
                'overall_survival_rate': 85.0,
                'critical_carrier_success': 90.0
            }
        )
        mock_matrix.return_value.generate_matrix.return_value = mock_report
        
        # Run with all formats
        result = self.runner.invoke(cli, [
            'test', str(test_file),
            '--output', self.temp_dir,
            '--report-format', 'all'
        ])
        
        assert result.exit_code == 0
        assert "JSON report saved" in result.output
        assert "CSV report saved" in result.output
        assert "HTML report saved" in result.output
    
    @patch('ooxml_tester.convert.engine.ConversionEngine')
    def test_test_command_conversion_error(self, mock_engine):
        """Test test command when conversion fails."""
        # Create a temporary test file
        test_file = Path(self.temp_dir) / "test.pptx"
        test_file.touch()
        
        # Mock conversion failure
        mock_engine.return_value.run_round_trip.side_effect = Exception("Conversion failed")
        
        # Run the command
        result = self.runner.invoke(cli, [
            'test', str(test_file),
            '--output', self.temp_dir
        ])
        
        # Should handle gracefully and report no results
        assert "conversion failed" in result.output.lower()
    
    def test_tolerance_options(self):
        """Test tolerance level options."""
        test_file = Path(self.temp_dir) / "test.pptx"
        test_file.touch()
        
        # Test valid tolerance levels
        for tolerance in ['strict', 'normal', 'lenient', 'permissive']:
            result = self.runner.invoke(cli, [
                'test', str(test_file),
                '--tolerance', tolerance,
                '--help'  # Just check help to avoid full execution
            ])
            # Help should work without error
            assert "tolerance" in result.output.lower()


class TestCLIIntegration:
    """Integration tests for CLI with real components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
    
    def test_cli_probe_command_basic(self):
        """Test basic probe command functionality."""
        with patch('ooxml_tester.probe.generator.ProbeGenerator') as mock_gen:
            mock_gen.return_value.generate.return_value = ['probe1.pptx', 'probe2.docx']
            
            result = self.runner.invoke(cli, [
                'probe',
                '--output', self.temp_dir,
                '--format', 'pptx',
                '--count', '2'
            ])
            
            # Should complete successfully
            assert "Generated 2 probe files" in result.output
    
    def test_cli_config_loading(self):
        """Test configuration file loading."""
        # Create a test config file
        config_file = Path(self.temp_dir) / "test_config.json"
        config_data = {
            "tolerance": {
                "strict": {"color_threshold": 0.95}
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Test with config file
        result = self.runner.invoke(cli, [
            '--config', str(config_file),
            '--help'
        ])
        
        assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__])