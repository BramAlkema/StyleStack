"""
Test suite for CLI configuration management system.

Tests YAML configuration loading, validation, environment variables,
configuration merging, and template support before implementation (TDD approach).
"""

import pytest
import tempfile
import os
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from click.testing import CliRunner

from build import cli


class TestConfigurationLoading:
    """Test configuration file loading and parsing."""
    
    def setup_method(self):
        """Set up configuration loading test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        
        self.sample_config = {
            'version': '1.0',
            'defaults': {
                'org': 'acme',
                'channel': 'present',
                'verbose': True,
                'parallel': True,
                'max_workers': 4
            },
            'paths': {
                'templates': 'templates/',
                'output': 'output/',
                'orgs': 'orgs/',
                'channels': 'channels/'
            },
            'build': {
                'validation_level': 'comprehensive',
                'compression': True,
                'backup_originals': True
            },
            'batch': {
                'checkpoint_interval': 5,
                'retry_failed': True,
                'max_retries': 3
            },
            'logging': {
                'level': 'INFO',
                'format': 'structured',
                'file': 'stylestack.log'
            }
        }
        
    def test_yaml_config_file_loading(self):
        """Test loading YAML configuration files."""
        config_file = Path(self.temp_dir) / "stylestack.yml"
        with open(config_file, 'w') as f:
            yaml.dump(self.sample_config, f)
            
        with patch('build.load_yaml_config') as mock_load:
            mock_load.return_value = self.sample_config
            
            result = self.runner.invoke(cli, [
                '--config', str(config_file),
                '--src', 'template.potx',
                '--out', 'output.potx'
            ])
            
            mock_load.assert_called_with(str(config_file))
    
    def test_json_config_file_loading(self):
        """Test loading JSON configuration files."""
        config_file = Path(self.temp_dir) / "stylestack.json"
        with open(config_file, 'w') as f:
            import json
            json.dump(self.sample_config, f, indent=2)
            
        with patch('build.load_json_config') as mock_load:
            mock_load.return_value = self.sample_config
            
            result = self.runner.invoke(cli, [
                '--config', str(config_file),
                '--src', 'template.potx',
                '--out', 'output.potx'
            ])
            
            mock_load.assert_called_with(str(config_file))
    
    def test_toml_config_file_loading(self):
        """Test loading TOML configuration files."""
        config_file = Path(self.temp_dir) / "stylestack.toml"
        
        with patch('build.load_toml_config') as mock_load:
            mock_load.return_value = self.sample_config
            
            result = self.runner.invoke(cli, [
                '--config', str(config_file),
                '--src', 'template.potx', 
                '--out', 'output.potx'
            ])
            
            mock_load.assert_called_with(str(config_file))
    
    def test_config_file_format_detection(self):
        """Test automatic detection of configuration file format."""
        with patch('build.detect_config_format') as mock_detect:
            mock_detect.return_value = 'yaml'
            
            result = self.runner.invoke(cli, [
                '--config', 'stylestack.config',
                '--src', 'template.potx',
                '--out', 'output.potx'
            ])
            
            mock_detect.assert_called_with('stylestack.config')
    
    def test_config_file_not_found_error(self):
        """Test handling of missing configuration files."""
        with patch('build.StyleStackConfigError') as mock_error:
            result = self.runner.invoke(cli, [
                '--config', 'nonexistent.yml',
                '--src', 'template.potx',
                '--out', 'output.potx'
            ])
            
            assert result.exit_code != 0
            assert 'Configuration file not found' in result.output
    
    def test_invalid_config_syntax_error(self):
        """Test handling of invalid configuration file syntax."""
        invalid_config_file = Path(self.temp_dir) / "invalid.yml"
        with open(invalid_config_file, 'w') as f:
            f.write("invalid: yaml: syntax: error\n  - malformed")
            
        with patch('build.StyleStackConfigSyntaxError') as mock_error:
            result = self.runner.invoke(cli, [
                '--config', str(invalid_config_file),
                '--src', 'template.potx',
                '--out', 'output.potx'
            ])
            
            assert result.exit_code != 0
            assert 'Invalid configuration syntax' in result.output


class TestConfigurationValidation:
    """Test configuration schema validation and error handling."""
    
    def setup_method(self):
        """Set up configuration validation test fixtures."""
        self.runner = CliRunner()
        
    def test_config_schema_validation(self):
        """Test validation against configuration schema."""
        with patch('build.ConfigSchemaValidator') as mock_validator:
            mock_validator.return_value.validate.return_value = {
                'valid': True,
                'errors': [],
                'warnings': []
            }
            
            result = self.runner.invoke(cli, [
                '--config', 'stylestack.yml',
                '--validate-config'
            ])
            
            validator_instance = mock_validator.return_value
            validator_instance.validate.assert_called()
    
    def test_required_fields_validation(self):
        """Test validation of required configuration fields."""
        with patch('build.validate_required_fields') as mock_validate:
            mock_validate.return_value = {
                'missing': ['defaults.org', 'paths.templates'],
                'valid': False
            }
            
            result = self.runner.invoke(cli, [
                '--config', 'incomplete.yml',
                '--src', 'template.potx',
                '--out', 'output.potx'
            ])
            
            mock_validate.assert_called()
            assert 'Missing required fields' in result.output
    
    def test_field_type_validation(self):
        """Test validation of configuration field types."""
        with patch('build.validate_field_types') as mock_validate:
            mock_validate.return_value = {
                'type_errors': [
                    {'field': 'defaults.max_workers', 'expected': 'int', 'actual': 'str'}
                ],
                'valid': False
            }
            
            result = self.runner.invoke(cli, [
                '--config', 'invalid_types.yml',
                '--src', 'template.potx',
                '--out', 'output.potx'
            ])
            
            mock_validate.assert_called()
            assert 'Type validation failed' in result.output
    
    def test_path_validation(self):
        """Test validation of file and directory paths in configuration."""
        with patch('build.validate_config_paths') as mock_validate:
            mock_validate.return_value = {
                'invalid_paths': ['templates/', 'nonexistent/output/'],
                'valid': False
            }
            
            result = self.runner.invoke(cli, [
                '--config', 'invalid_paths.yml',
                '--validate-paths'
            ])
            
            mock_validate.assert_called()
            assert 'Invalid paths found' in result.output
    
    def test_cross_field_validation(self):
        """Test cross-field validation and consistency checks."""
        with patch('build.validate_config_consistency') as mock_validate:
            mock_validate.return_value = {
                'consistency_errors': [
                    'max_workers cannot be greater than available CPU cores'
                ],
                'valid': False
            }
            
            result = self.runner.invoke(cli, [
                '--config', 'inconsistent.yml',
                '--src', 'template.potx',
                '--out', 'output.potx'
            ])
            
            mock_validate.assert_called()
            assert 'Configuration consistency errors' in result.output


class TestEnvironmentVariableSupport:
    """Test configuration through environment variables."""
    
    def setup_method(self):
        """Set up environment variable test fixtures."""
        self.runner = CliRunner()
        
    def test_basic_env_var_loading(self):
        """Test loading configuration from environment variables."""
        env_vars = {
            'STYLESTACK_ORG': 'acme',
            'STYLESTACK_CHANNEL': 'present',
            'STYLESTACK_VERBOSE': 'true',
            'STYLESTACK_MAX_WORKERS': '6'
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('build.load_env_config') as mock_load_env:
                mock_load_env.return_value = {
                    'org': 'acme',
                    'channel': 'present',
                    'verbose': True,
                    'max_workers': 6
                }
                
                result = self.runner.invoke(cli, [
                    '--src', 'template.potx',
                    '--out', 'output.potx'
                ])
                
                mock_load_env.assert_called()
    
    def test_env_var_type_conversion(self):
        """Test automatic type conversion for environment variables."""
        env_vars = {
            'STYLESTACK_MAX_WORKERS': '8',
            'STYLESTACK_PARALLEL': 'true',
            'STYLESTACK_TIMEOUT': '30.5',
            'STYLESTACK_TAGS': 'tag1,tag2,tag3'
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('build.convert_env_types') as mock_convert:
                mock_convert.return_value = {
                    'max_workers': 8,
                    'parallel': True,
                    'timeout': 30.5,
                    'tags': ['tag1', 'tag2', 'tag3']
                }
                
                result = self.runner.invoke(cli, [
                    '--src', 'template.potx',
                    '--out', 'output.potx'
                ])
                
                mock_convert.assert_called()
    
    def test_env_var_prefix_support(self):
        """Test support for custom environment variable prefixes."""
        env_vars = {
            'MYCOMPANY_STYLESTACK_ORG': 'mycompany',
            'MYCOMPANY_STYLESTACK_CHANNEL': 'corporate'
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('build.load_prefixed_env_config') as mock_load:
                result = self.runner.invoke(cli, [
                    '--env-prefix', 'MYCOMPANY_STYLESTACK',
                    '--src', 'template.potx',
                    '--out', 'output.potx'
                ])
                
                mock_load.assert_called_with('MYCOMPANY_STYLESTACK')
    
    def test_env_var_validation_and_sanitization(self):
        """Test validation and sanitization of environment variables."""
        with patch('build.validate_env_vars') as mock_validate:
            mock_validate.return_value = {
                'valid': True,
                'sanitized': {
                    'org': 'acme-corp',  # Sanitized from 'Acme Corp!'
                    'max_workers': 4     # Bounded from 999
                }
            }
            
            result = self.runner.invoke(cli, [
                '--src', 'template.potx',
                '--out', 'output.potx'
            ])
            
            mock_validate.assert_called()


class TestConfigurationMerging:
    """Test configuration merging and inheritance."""
    
    def setup_method(self):
        """Set up configuration merging test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        
    def test_multiple_config_file_merging(self):
        """Test merging multiple configuration files."""
        base_config = {'defaults': {'org': 'base', 'channel': 'present'}}
        override_config = {'defaults': {'org': 'override', 'verbose': True}}
        
        base_file = Path(self.temp_dir) / "base.yml"
        override_file = Path(self.temp_dir) / "override.yml"
        
        with open(base_file, 'w') as f:
            yaml.dump(base_config, f)
        with open(override_file, 'w') as f:
            yaml.dump(override_config, f)
            
        with patch('build.merge_configs') as mock_merge:
            mock_merge.return_value = {
                'defaults': {
                    'org': 'override',  # Overridden
                    'channel': 'present',  # From base
                    'verbose': True  # New from override
                }
            }
            
            result = self.runner.invoke(cli, [
                '--config', str(base_file),
                '--config-override', str(override_file),
                '--src', 'template.potx',
                '--out', 'output.potx'
            ])
            
            mock_merge.assert_called_with([base_config, override_config])
    
    def test_cli_args_override_config_files(self):
        """Test CLI arguments override configuration file settings."""
        with patch('build.merge_cli_and_config') as mock_merge:
            mock_merge.return_value = {
                'org': 'cli-override',  # From CLI
                'channel': 'present',   # From config
                'verbose': True         # From CLI
            }
            
            result = self.runner.invoke(cli, [
                '--config', 'config.yml',
                '--org', 'cli-override',
                '--verbose',
                '--src', 'template.potx',
                '--out', 'output.potx'
            ])
            
            mock_merge.assert_called()
    
    def test_env_vars_override_precedence(self):
        """Test environment variables override configuration files but not CLI args."""
        with patch('build.apply_config_precedence') as mock_precedence:
            mock_precedence.return_value = {
                'org': 'cli-final',      # CLI wins
                'channel': 'env-override',  # Env wins over config
                'max_workers': 4         # Config default
            }
            
            result = self.runner.invoke(cli, [
                '--config', 'config.yml',
                '--org', 'cli-final',
                '--src', 'template.potx',
                '--out', 'output.potx'
            ])
            
            mock_precedence.assert_called()
    
    def test_deep_merge_of_nested_objects(self):
        """Test deep merging of nested configuration objects."""
        with patch('build.deep_merge_configs') as mock_deep_merge:
            mock_deep_merge.return_value = {
                'logging': {
                    'level': 'DEBUG',     # Overridden
                    'format': 'json',     # From base
                    'handlers': {
                        'file': True,     # From base
                        'console': False  # Overridden
                    }
                }
            }
            
            result = self.runner.invoke(cli, [
                '--config', 'base.yml',
                '--config-override', 'dev.yml',
                '--src', 'template.potx',
                '--out', 'output.potx'
            ])
            
            mock_deep_merge.assert_called()


class TestConfigurationTemplates:
    """Test configuration templates for common use cases."""
    
    def setup_method(self):
        """Set up configuration template test fixtures."""
        self.runner = CliRunner()
        
    def test_preset_configuration_templates(self):
        """Test loading preset configuration templates."""
        with patch('build.load_config_template') as mock_template:
            mock_template.return_value = {
                'name': 'development',
                'description': 'Development environment settings',
                'config': {
                    'defaults': {'verbose': True, 'parallel': False},
                    'logging': {'level': 'DEBUG'}
                }
            }
            
            result = self.runner.invoke(cli, [
                '--config-template', 'development',
                '--src', 'template.potx',
                '--out', 'output.potx'
            ])
            
            mock_template.assert_called_with('development')
    
    def test_custom_config_template_creation(self):
        """Test creating custom configuration templates."""
        with patch('build.create_config_template') as mock_create:
            result = self.runner.invoke(cli, [
                '--save-config-template', 'my-preset',
                '--template-description', 'My custom preset',
                '--org', 'acme',
                '--channel', 'present',
                '--verbose'
            ])
            
            mock_create.assert_called_with(
                name='my-preset',
                description='My custom preset',
                config={'org': 'acme', 'channel': 'present', 'verbose': True}
            )
    
    def test_config_template_listing(self):
        """Test listing available configuration templates."""
        with patch('build.list_config_templates') as mock_list:
            mock_list.return_value = [
                {'name': 'development', 'description': 'Dev environment'},
                {'name': 'production', 'description': 'Prod environment'},
                {'name': 'ci-cd', 'description': 'CI/CD pipeline'}
            ]
            
            result = self.runner.invoke(cli, ['--list-config-templates'])
            
            mock_list.assert_called()
            assert 'development' in result.output
            assert 'production' in result.output
            assert 'ci-cd' in result.output
    
    def test_config_template_validation(self):
        """Test validation of configuration templates."""
        with patch('build.validate_config_template') as mock_validate:
            mock_validate.return_value = {
                'valid': True,
                'warnings': ['Template uses deprecated setting']
            }
            
            result = self.runner.invoke(cli, [
                '--validate-config-template', 'old-template'
            ])
            
            mock_validate.assert_called_with('old-template')


class TestAdvancedConfigurationFeatures:
    """Test advanced configuration features."""
    
    def setup_method(self):
        """Set up advanced configuration test fixtures."""
        self.runner = CliRunner()
        
    def test_conditional_configuration_sections(self):
        """Test conditional configuration sections based on environment."""
        with patch('build.process_conditional_config') as mock_conditional:
            mock_conditional.return_value = {
                'defaults': {'org': 'prod-org'},  # Production settings
                'logging': {'level': 'WARNING'}
            }
            
            result = self.runner.invoke(cli, [
                '--config', 'conditional.yml',
                '--environment', 'production',
                '--src', 'template.potx',
                '--out', 'output.potx'
            ])
            
            mock_conditional.assert_called_with('production')
    
    def test_configuration_variable_interpolation(self):
        """Test variable interpolation in configuration files."""
        with patch('build.interpolate_config_variables') as mock_interpolate:
            mock_interpolate.return_value = {
                'paths': {
                    'templates': '/home/user/stylestack/templates',  # Expanded from ${HOME}
                    'output': '/tmp/stylestack-output-2025-01-11'   # Expanded with date
                }
            }
            
            result = self.runner.invoke(cli, [
                '--config', 'interpolated.yml',
                '--src', 'template.potx',
                '--out', 'output.potx'
            ])
            
            mock_interpolate.assert_called()
    
    def test_configuration_includes_and_imports(self):
        """Test configuration file includes and imports."""
        with patch('build.process_config_includes') as mock_includes:
            mock_includes.return_value = {
                'base_config': {'from': 'base.yml'},
                'logging_config': {'from': 'logging.yml'},
                'merged_result': 'full_config'
            }
            
            result = self.runner.invoke(cli, [
                '--config', 'main.yml',  # Contains includes
                '--src', 'template.potx',
                '--out', 'output.potx'
            ])
            
            mock_includes.assert_called()
    
    def test_configuration_profiles_and_contexts(self):
        """Test configuration profiles for different contexts."""
        with patch('build.load_config_profile') as mock_profile:
            mock_profile.return_value = {
                'profile': 'corporate',
                'settings': {
                    'defaults': {'org': 'corporate', 'channel': 'business'},
                    'validation': {'level': 'strict'},
                    'security': {'enable_audit': True}
                }
            }
            
            result = self.runner.invoke(cli, [
                '--profile', 'corporate',
                '--src', 'template.potx',
                '--out', 'output.potx'
            ])
            
            mock_profile.assert_called_with('corporate')
    
    def test_dynamic_configuration_generation(self):
        """Test dynamic configuration generation based on runtime context."""
        with patch('build.generate_dynamic_config') as mock_dynamic:
            mock_dynamic.return_value = {
                'auto_detected': {
                    'max_workers': 8,      # Based on CPU cores
                    'memory_limit': '4GB', # Based on available RAM
                    'temp_dir': '/tmp/stylestack-12345'  # Unique temp dir
                }
            }
            
            result = self.runner.invoke(cli, [
                '--auto-config',
                '--src', 'template.potx',
                '--out', 'output.potx'
            ])
            
            mock_dynamic.assert_called()


class TestConfigurationSecurity:
    """Test configuration security and validation."""
    
    def setup_method(self):
        """Set up configuration security test fixtures."""
        self.runner = CliRunner()
        
    def test_sensitive_data_protection(self):
        """Test protection of sensitive data in configuration."""
        with patch('build.protect_sensitive_config') as mock_protect:
            result = self.runner.invoke(cli, [
                '--config', 'secure.yml',
                '--protect-sensitive',
                '--src', 'template.potx',
                '--out', 'output.potx'
            ])
            
            mock_protect.assert_called()
    
    def test_configuration_encryption_support(self):
        """Test support for encrypted configuration files."""
        with patch('build.decrypt_config_file') as mock_decrypt:
            mock_decrypt.return_value = {'decrypted': 'config'}
            
            result = self.runner.invoke(cli, [
                '--config', 'encrypted.yml.enc',
                '--config-key', 'encryption_key',
                '--src', 'template.potx',
                '--out', 'output.potx'
            ])
            
            mock_decrypt.assert_called()
    
    def test_configuration_integrity_verification(self):
        """Test configuration file integrity verification."""
        with patch('build.verify_config_integrity') as mock_verify:
            mock_verify.return_value = {
                'verified': True,
                'checksum': 'abc123',
                'signature_valid': True
            }
            
            result = self.runner.invoke(cli, [
                '--config', 'signed.yml',
                '--verify-config',
                '--src', 'template.potx',
                '--out', 'output.potx'
            ])
            
            mock_verify.assert_called()
    
    def test_configuration_access_control(self):
        """Test access control for configuration files."""
        with patch('build.check_config_permissions') as mock_permissions:
            mock_permissions.return_value = {
                'readable': True,
                'secure_permissions': True,
                'owner_only': True
            }
            
            result = self.runner.invoke(cli, [
                '--config', 'restricted.yml',
                '--check-permissions',
                '--src', 'template.potx',
                '--out', 'output.potx'
            ])
            
            mock_permissions.assert_called()