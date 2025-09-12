"""
Test suite for enhanced CLI interface features.

Tests the rich CLI framework, progress bars, colored output, interactive prompts,
and improved error handling before implementation (TDD approach).
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from build import cli  # Main CLI entry point


class TestEnhancedCLIInterface:
    """Test enhanced CLI interface with rich output formatting."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.test_template = Path(self.temp_dir) / "test.potx"
        self.test_output = Path(self.temp_dir) / "output.potx"
        
    def test_rich_progress_bar_display(self):
        """Test that CLI displays rich progress bars during processing."""
        with patch('build.RichProgress') as mock_progress:
            mock_task = Mock()
            mock_progress.return_value.__enter__.return_value.add_task.return_value = mock_task
            
            result = self.runner.invoke(cli, [
                '--src', str(self.test_template),
                '--out', str(self.test_output),
                '--verbose'
            ])
            
            # Should create progress bar with template processing task
            mock_progress.assert_called_once()
            progress_instance = mock_progress.return_value.__enter__.return_value
            progress_instance.add_task.assert_called_with(
                "Processing template...", total=100
            )
    
    def test_colored_console_output(self):
        """Test that CLI uses rich colored console output."""
        with patch('build.Console') as mock_console:
            result = self.runner.invoke(cli, [
                '--src', str(self.test_template),
                '--out', str(self.test_output)
            ])
            
            # Should create rich console for colored output
            mock_console.assert_called_once()
            console_instance = mock_console.return_value
            
            # Should print status messages in color
            console_instance.print.assert_called()
            
    def test_enhanced_error_formatting(self):
        """Test that errors are displayed with rich formatting and context."""
        with patch('build.Console') as mock_console:
            # Simulate file not found error
            result = self.runner.invoke(cli, [
                '--src', 'nonexistent.potx',
                '--out', str(self.test_output)
            ])
            
            console_instance = mock_console.return_value
            
            # Should display formatted error with suggestions
            error_calls = [call for call in console_instance.print.call_args_list 
                          if 'error' in str(call).lower()]
            assert len(error_calls) > 0
            
    def test_cli_configuration_loading(self):
        """Test loading CLI configuration from YAML file."""
        config_file = Path(self.temp_dir) / "stylestack.yml"
        config_data = {
            'defaults': {
                'org': 'test-org',
                'channel': 'present',
                'verbose': True
            },
            'templates': {
                'input_dir': 'templates/',
                'output_dir': 'output/'
            }
        }
        
        with open(config_file, 'w') as f:
            import yaml
            yaml.dump(config_data, f)
            
        with patch('build.load_config') as mock_load_config:
            mock_load_config.return_value = config_data
            
            result = self.runner.invoke(cli, [
                '--config', str(config_file),
                '--src', str(self.test_template),
                '--out', str(self.test_output)
            ])
            
            mock_load_config.assert_called_with(str(config_file))
    
    def test_interactive_org_selection(self):
        """Test interactive organization selection prompt."""
        orgs = ['acme', 'globex', 'initech']
        
        with patch('build.prompt_org_selection') as mock_prompt:
            mock_prompt.return_value = 'acme'
            
            result = self.runner.invoke(cli, [
                '--src', str(self.test_template),
                '--out', str(self.test_output),
                '--interactive'
            ], input='1\n')  # Select first option
            
            mock_prompt.assert_called_once()
    
    def test_cli_help_with_examples(self):
        """Test that help displays examples and use cases."""
        result = self.runner.invoke(cli, ['--help'])
        
        # Should include examples section
        assert 'Examples:' in result.output
        assert 'python build.py --src template.potx' in result.output
        
    def test_command_auto_completion_setup(self):
        """Test that auto-completion can be set up."""
        with patch('build.setup_completion') as mock_setup:
            result = self.runner.invoke(cli, ['--setup-completion', 'bash'])
            mock_setup.assert_called_with('bash')


class TestBatchProcessingCapabilities:
    """Test batch processing functionality."""
    
    def setup_method(self):
        """Set up batch processing test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create multiple test templates
        self.templates = []
        for i in range(3):
            template = Path(self.temp_dir) / f"template_{i}.potx"
            self.templates.append(template)
            
    def test_batch_template_processing(self):
        """Test processing multiple templates in batch."""
        batch_config = {
            'templates': [
                {
                    'src': str(self.templates[0]),
                    'out': str(self.temp_dir / "output_0.potx"),
                    'org': 'acme',
                    'channel': 'present'
                },
                {
                    'src': str(self.templates[1]),
                    'out': str(self.temp_dir / "output_1.potx"),
                    'org': 'globex',
                    'channel': 'doc'
                }
            ]
        }
        
        batch_file = Path(self.temp_dir) / "batch.json"
        with open(batch_file, 'w') as f:
            json.dump(batch_config, f)
            
        with patch('build.BatchProcessor') as mock_processor:
            result = self.runner.invoke(cli, [
                '--batch', str(batch_file),
                '--verbose'
            ])
            
            mock_processor.assert_called_once_with(batch_config)
            
    def test_parallel_processing_with_threads(self):
        """Test parallel processing using thread pools."""
        with patch('build.ThreadPoolExecutor') as mock_executor:
            mock_executor.return_value.__enter__.return_value.map.return_value = []
            
            result = self.runner.invoke(cli, [
                '--batch', 'batch.json',
                '--parallel',
                '--max-workers', '4'
            ])
            
            mock_executor.assert_called_with(max_workers=4)
    
    def test_batch_progress_reporting(self):
        """Test progress reporting for batch operations."""
        with patch('build.BatchProgress') as mock_progress:
            result = self.runner.invoke(cli, [
                '--batch', 'batch.json',
                '--verbose'
            ])
            
            progress_instance = mock_progress.return_value
            progress_instance.update_progress.assert_called()
            
    def test_batch_operation_resume(self):
        """Test resuming interrupted batch operations."""
        checkpoint_file = Path(self.temp_dir) / ".stylestack_checkpoint"
        checkpoint_data = {
            'completed': ['template_0.potx'],
            'remaining': ['template_1.potx', 'template_2.potx'],
            'timestamp': '2025-01-11T10:00:00Z'
        }
        
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f)
            
        with patch('build.load_checkpoint') as mock_load:
            mock_load.return_value = checkpoint_data
            
            result = self.runner.invoke(cli, [
                '--batch', 'batch.json',
                '--resume'
            ])
            
            mock_load.assert_called_once()
    
    def test_batch_error_aggregation(self):
        """Test aggregation of errors across batch operations."""
        with patch('build.BatchErrorCollector') as mock_collector:
            result = self.runner.invoke(cli, [
                '--batch', 'batch.json'
            ])
            
            collector_instance = mock_collector.return_value
            collector_instance.collect_error.assert_called()


class TestEnhancedErrorHandling:
    """Test enhanced error handling with actionable suggestions."""
    
    def setup_method(self):
        """Set up error handling test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        
    def test_file_not_found_error_with_suggestions(self):
        """Test file not found errors include helpful suggestions."""
        with patch('build.StyleStackFileNotFoundError') as mock_error:
            mock_error.return_value.suggestions = [
                "Check if the file path is correct",
                "Ensure the template file has .potx extension",
                "Try using absolute path instead of relative path"
            ]
            
            result = self.runner.invoke(cli, [
                '--src', 'missing.potx',
                '--out', 'output.potx'
            ])
            
            assert result.exit_code != 0
            assert "suggestions" in result.output.lower()
            
    def test_invalid_org_error_with_available_orgs(self):
        """Test invalid org errors show available organizations."""
        with patch('build.list_available_orgs') as mock_list_orgs:
            mock_list_orgs.return_value = ['acme', 'globex', 'initech']
            
            with patch('build.StyleStackValidationError') as mock_error:
                result = self.runner.invoke(cli, [
                    '--src', 'template.potx',
                    '--out', 'output.potx',
                    '--org', 'invalid-org'
                ])
                
                mock_list_orgs.assert_called_once()
                assert result.exit_code != 0
                
    def test_permission_error_with_fix_suggestions(self):
        """Test permission errors include fix suggestions."""
        with patch('build.StyleStackPermissionError') as mock_error:
            mock_error.return_value.fix_suggestions = [
                "Run with sudo if necessary",
                "Check directory write permissions",
                "Ensure output directory exists"
            ]
            
            result = self.runner.invoke(cli, [
                '--src', 'template.potx',
                '--out', '/root/protected.potx'
            ])
            
            assert "fix_suggestions" in result.output.lower()
    
    def test_error_recovery_mechanisms(self):
        """Test automatic error recovery for common issues."""
        with patch('build.auto_fix_common_issues') as mock_fix:
            mock_fix.return_value = True
            
            result = self.runner.invoke(cli, [
                '--src', 'template.potx',
                '--out', 'output.potx',
                '--auto-fix'
            ])
            
            mock_fix.assert_called_once()
    
    def test_error_context_collection(self):
        """Test collection of detailed error context."""
        with patch('build.ErrorContextCollector') as mock_collector:
            result = self.runner.invoke(cli, [
                '--src', 'template.potx',
                '--out', 'output.potx'
            ])
            
            collector_instance = mock_collector.return_value
            collector_instance.collect_system_info.assert_called()
            collector_instance.collect_file_info.assert_called()


class TestConfigurationManagement:
    """Test CLI configuration management system."""
    
    def setup_method(self):
        """Set up configuration test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        
    def test_yaml_configuration_loading(self):
        """Test loading YAML configuration files."""
        config_file = Path(self.temp_dir) / "config.yml"
        config_data = {
            'defaults': {'org': 'acme', 'verbose': True},
            'paths': {'templates': 'templates/', 'output': 'output/'}
        }
        
        with open(config_file, 'w') as f:
            import yaml
            yaml.dump(config_data, f)
            
        with patch('build.ConfigLoader') as mock_loader:
            mock_loader.return_value.load.return_value = config_data
            
            result = self.runner.invoke(cli, [
                '--config', str(config_file)
            ])
            
            mock_loader.assert_called_once()
    
    def test_configuration_validation(self):
        """Test configuration schema validation."""
        with patch('build.ConfigValidator') as mock_validator:
            mock_validator.return_value.validate.return_value = True
            
            result = self.runner.invoke(cli, [
                '--config', 'config.yml'
            ])
            
            mock_validator.assert_called_once()
    
    def test_environment_variable_support(self):
        """Test configuration from environment variables."""
        with patch.dict(os.environ, {
            'STYLESTACK_ORG': 'acme',
            'STYLESTACK_CHANNEL': 'present',
            'STYLESTACK_VERBOSE': 'true'
        }):
            with patch('build.load_env_config') as mock_env_loader:
                result = self.runner.invoke(cli, [
                    '--src', 'template.potx',
                    '--out', 'output.potx'
                ])
                
                mock_env_loader.assert_called_once()
    
    def test_configuration_inheritance(self):
        """Test configuration merging and inheritance."""
        with patch('build.ConfigMerger') as mock_merger:
            result = self.runner.invoke(cli, [
                '--config', 'base.yml',
                '--config-override', 'override.yml'
            ])
            
            merger_instance = mock_merger.return_value
            merger_instance.merge.assert_called()


class TestCLIHelpAndDocumentation:
    """Test enhanced CLI help and documentation features."""
    
    def setup_method(self):
        """Set up help system test fixtures."""
        self.runner = CliRunner()
        
    def test_enhanced_help_with_examples(self):
        """Test help system includes practical examples."""
        result = self.runner.invoke(cli, ['--help'])
        
        assert 'Examples:' in result.output
        assert 'Basic template processing:' in result.output
        assert 'Batch processing:' in result.output
        assert 'Corporate branding:' in result.output
        
    def test_command_specific_help(self):
        """Test command-specific help with detailed usage."""
        result = self.runner.invoke(cli, ['batch', '--help'])
        
        assert 'Batch processing options:' in result.output
        assert '--parallel' in result.output
        assert '--max-workers' in result.output
        
    def test_built_in_tutorial_mode(self):
        """Test built-in tutorial and guided workflows."""
        with patch('build.TutorialRunner') as mock_tutorial:
            result = self.runner.invoke(cli, ['--tutorial'])
            
            mock_tutorial.assert_called_once()
            tutorial_instance = mock_tutorial.return_value
            tutorial_instance.run_interactive_tutorial.assert_called()
    
    def test_version_checking_and_updates(self):
        """Test version checking and update notifications."""
        with patch('build.check_for_updates') as mock_check:
            mock_check.return_value = {
                'current': '1.0.0',
                'latest': '1.1.0',
                'update_available': True
            }
            
            result = self.runner.invoke(cli, ['--check-updates'])
            
            mock_check.assert_called_once()
            assert 'update available' in result.output.lower()
    
    def test_diagnostic_commands(self):
        """Test diagnostic commands for troubleshooting."""
        with patch('build.run_diagnostics') as mock_diagnostics:
            mock_diagnostics.return_value = {
                'system': 'OK',
                'dependencies': 'OK',
                'templates': 'WARNING'
            }
            
            result = self.runner.invoke(cli, ['--diagnose'])
            
            mock_diagnostics.assert_called_once()
            assert 'System Status' in result.output


class TestInteractiveCLIFeatures:
    """Test interactive CLI features and user prompts."""
    
    def setup_method(self):
        """Set up interactive features test fixtures."""
        self.runner = CliRunner()
        
    def test_interactive_org_channel_selection(self):
        """Test interactive selection of org and channel."""
        with patch('build.interactive_selection') as mock_selection:
            mock_selection.side_effect = ['acme', 'present']
            
            result = self.runner.invoke(cli, [
                '--src', 'template.potx',
                '--out', 'output.potx',
                '--interactive'
            ], input='1\n2\n')
            
            assert mock_selection.call_count == 2
    
    def test_confirmation_prompts(self):
        """Test confirmation prompts for destructive operations."""
        with patch('build.confirm_overwrite') as mock_confirm:
            mock_confirm.return_value = True
            
            result = self.runner.invoke(cli, [
                '--src', 'template.potx',
                '--out', 'existing.potx',
                '--interactive'
            ], input='y\n')
            
            mock_confirm.assert_called_once()
    
    def test_progress_interaction(self):
        """Test interactive progress display with user controls."""
        with patch('build.InteractiveProgress') as mock_progress:
            result = self.runner.invoke(cli, [
                '--src', 'template.potx',
                '--out', 'output.potx',
                '--interactive-progress'
            ])
            
            progress_instance = mock_progress.return_value
            progress_instance.start.assert_called()