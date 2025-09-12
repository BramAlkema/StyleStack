"""
Configuration management system with YAML/JSON support and environment variables.
"""

import os
import yaml
import json
import toml
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from copy import deepcopy

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


@dataclass
class ConfigSource:
    """Configuration source information."""
    file_path: Optional[Path] = None
    env_vars: Dict[str, str] = field(default_factory=dict)
    cli_args: Dict[str, Any] = field(default_factory=dict)
    defaults: Dict[str, Any] = field(default_factory=dict)


class ConfigManager:
    """Configuration management with multiple sources and validation."""
    
    def __init__(self):
        """Initialize configuration manager."""
        self.config_file: Optional[Path] = None
        self.config_data: Dict[str, Any] = {}
        self.config_sources: List[ConfigSource] = []
        self.env_prefix = 'STYLESTACK'
        
        # Default configuration schema
        self.config_schema = {
            "type": "object",
            "properties": {
                "version": {"type": "string"},
                "defaults": {
                    "type": "object",
                    "properties": {
                        "org": {"type": "string"},
                        "channel": {"type": "string"},
                        "verbose": {"type": "boolean"},
                        "parallel": {"type": "boolean"},
                        "max_workers": {"type": "integer", "minimum": 1, "maximum": 32}
                    }
                },
                "paths": {
                    "type": "object",
                    "properties": {
                        "templates": {"type": "string"},
                        "output": {"type": "string"},
                        "orgs": {"type": "string"},
                        "channels": {"type": "string"}
                    }
                },
                "build": {
                    "type": "object",
                    "properties": {
                        "validation_level": {"type": "string", "enum": ["basic", "standard", "comprehensive"]},
                        "compression": {"type": "boolean"},
                        "backup_originals": {"type": "boolean"}
                    }
                },
                "batch": {
                    "type": "object", 
                    "properties": {
                        "checkpoint_interval": {"type": "integer", "minimum": 1},
                        "retry_failed": {"type": "boolean"},
                        "max_retries": {"type": "integer", "minimum": 0, "maximum": 10}
                    }
                },
                "logging": {
                    "type": "object",
                    "properties": {
                        "level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]},
                        "format": {"type": "string", "enum": ["simple", "structured", "json"]},
                        "file": {"type": "string"}
                    }
                }
            }
        }
    
    def load_config(self, 
                   config_file: Optional[str] = None,
                   env_prefix: str = 'STYLESTACK',
                   **cli_args) -> Dict[str, Any]:
        """Load configuration from multiple sources with precedence."""
        self.env_prefix = env_prefix
        self.config_data = {}
        self.config_sources = []
        
        # 1. Load default configuration
        defaults = self._load_default_config()
        self.config_sources.append(ConfigSource(defaults=defaults))
        
        # 2. Load configuration file if specified
        if config_file:
            file_config = self._load_config_file(config_file)
            if file_config:
                self.config_sources.append(ConfigSource(file_path=Path(config_file)))
        else:
            # Try to find default config files
            file_config = self._find_and_load_default_config_file()
        
        # 3. Load environment variables
        env_config = self._load_env_config(env_prefix)
        self.config_sources.append(ConfigSource(env_vars=env_config))
        
        # 4. Apply CLI arguments
        cli_config = self._process_cli_args(cli_args)
        self.config_sources.append(ConfigSource(cli_args=cli_config))
        
        # Merge all configurations with precedence: defaults < file < env < cli
        merged_config = self._merge_configurations([
            defaults,
            file_config or {},
            self._convert_env_to_config(env_config),
            cli_config
        ])
        
        # Validate merged configuration
        if JSONSCHEMA_AVAILABLE:
            self._validate_config(merged_config)
        
        self.config_data = merged_config
        return merged_config
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration values."""
        return {
            'version': '2026.1.0',
            'defaults': {
                'verbose': False,
                'parallel': True,
                'max_workers': 4,
                'validation_level': 'standard'
            },
            'paths': {
                'templates': 'templates/',
                'output': 'output/',
                'orgs': 'orgs/',
                'channels': 'channels/'
            },
            'build': {
                'validation_level': 'standard',
                'compression': True,
                'backup_originals': False
            },
            'batch': {
                'checkpoint_interval': 10,
                'retry_failed': True,
                'max_retries': 3
            },
            'logging': {
                'level': 'INFO',
                'format': 'simple'
            }
        }
    
    def _load_config_file(self, config_file: str) -> Optional[Dict[str, Any]]:
        """Load configuration from file (YAML, JSON, or TOML)."""
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                return None
            
            self.config_file = config_path
            
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Detect file format and parse accordingly
            if config_path.suffix.lower() in ['.yml', '.yaml']:
                return yaml.safe_load(content)
            elif config_path.suffix.lower() == '.json':
                return json.loads(content)
            elif config_path.suffix.lower() == '.toml':
                return toml.loads(content)
            else:
                # Try to auto-detect format
                try:
                    return yaml.safe_load(content)
                except yaml.YAMLError:
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        if 'toml' in globals():
                            return toml.loads(content)
                        raise ValueError(f"Unable to parse config file: {config_file}")
        
        except Exception as e:
            raise ConfigError(f"Failed to load config file {config_file}: {e}")
    
    def _find_and_load_default_config_file(self) -> Optional[Dict[str, Any]]:
        """Find and load default configuration files."""
        config_files = [
            'stylestack.yml',
            'stylestack.yaml', 
            'stylestack.json',
            'stylestack.toml',
            '.stylestack.yml',
            '.stylestack.yaml',
            '.stylestack.json',
            '.stylestack.toml'
        ]
        
        for config_file in config_files:
            config_path = Path(config_file)
            if config_path.exists():
                return self._load_config_file(str(config_path))
        
        return None
    
    def _load_env_config(self, prefix: str) -> Dict[str, str]:
        """Load configuration from environment variables."""
        env_config = {}
        prefix_with_underscore = f"{prefix}_"
        
        for key, value in os.environ.items():
            if key.startswith(prefix_with_underscore):
                config_key = key[len(prefix_with_underscore):].lower()
                env_config[config_key] = value
        
        return env_config
    
    def _convert_env_to_config(self, env_config: Dict[str, str]) -> Dict[str, Any]:
        """Convert environment variables to configuration structure."""
        config = {}
        
        for key, value in env_config.items():
            # Convert common boolean strings
            if value.lower() in ['true', 'yes', '1', 'on']:
                converted_value = True
            elif value.lower() in ['false', 'no', '0', 'off']:
                converted_value = False
            else:
                # Try to convert to int/float
                try:
                    if '.' in value:
                        converted_value = float(value)
                    else:
                        converted_value = int(value)
                except ValueError:
                    # Handle comma-separated lists
                    if ',' in value:
                        converted_value = [item.strip() for item in value.split(',')]
                    else:
                        converted_value = value
            
            # Map environment variables to config structure
            if key in ['org', 'channel', 'verbose', 'parallel', 'max_workers']:
                if 'defaults' not in config:
                    config['defaults'] = {}
                config['defaults'][key] = converted_value
            elif key in ['templates', 'output', 'orgs', 'channels']:
                if 'paths' not in config:
                    config['paths'] = {}
                config['paths'][key] = converted_value
            elif key in ['validation_level', 'compression', 'backup_originals']:
                if 'build' not in config:
                    config['build'] = {}
                config['build'][key] = converted_value
            elif key in ['checkpoint_interval', 'retry_failed', 'max_retries']:
                if 'batch' not in config:
                    config['batch'] = {}
                config['batch'][key] = converted_value
            elif key in ['level', 'format', 'file']:
                if 'logging' not in config:
                    config['logging'] = {}
                config['logging'][key] = converted_value
            else:
                config[key] = converted_value
        
        return config
    
    def _process_cli_args(self, cli_args: Dict[str, Any]) -> Dict[str, Any]:
        """Process CLI arguments into configuration structure."""
        config = {}
        
        # Map CLI arguments to configuration structure
        cli_to_config_mapping = {
            'org': ('defaults', 'org'),
            'channel': ('defaults', 'channel'),
            'verbose': ('defaults', 'verbose'),
            'parallel': ('defaults', 'parallel'),
            'max_workers': ('defaults', 'max_workers'),
            'validation_level': ('build', 'validation_level'),
            'log_level': ('logging', 'level'),
            'log_format': ('logging', 'format'),
            'log_file': ('logging', 'file')
        }
        
        for cli_key, value in cli_args.items():
            if value is not None and cli_key in cli_to_config_mapping:
                section, config_key = cli_to_config_mapping[cli_key]
                if section not in config:
                    config[section] = {}
                config[section][config_key] = value
        
        return config
    
    def _merge_configurations(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Deep merge multiple configuration dictionaries."""
        merged = {}
        
        for config in configs:
            if config:
                merged = self._deep_merge(merged, config)
        
        return merged
    
    def _deep_merge(self, base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = deepcopy(base)
        
        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validate configuration against schema."""
        if not JSONSCHEMA_AVAILABLE:
            return
        
        try:
            jsonschema.validate(config, self.config_schema)
        except jsonschema.ValidationError as e:
            raise ConfigValidationError(f"Configuration validation failed: {e.message}")
    
    def save_config_template(self, name: str, config: Dict[str, Any], description: str = "") -> None:
        """Save a configuration template for reuse."""
        templates_dir = Path.home() / '.stylestack' / 'templates'
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        template_data = {
            'name': name,
            'description': description,
            'created': str(Path.cwd()),
            'config': config
        }
        
        template_file = templates_dir / f"{name}.yml"
        with open(template_file, 'w') as f:
            yaml.dump(template_data, f, default_flow_style=False)
    
    def load_config_template(self, name: str) -> Dict[str, Any]:
        """Load a saved configuration template."""
        templates_dir = Path.home() / '.stylestack' / 'templates'
        template_file = templates_dir / f"{name}.yml"
        
        if not template_file.exists():
            raise ConfigError(f"Configuration template not found: {name}")
        
        with open(template_file, 'r') as f:
            template_data = yaml.safe_load(f)
        
        return template_data.get('config', {})
    
    def list_config_templates(self) -> List[Dict[str, str]]:
        """List available configuration templates."""
        templates_dir = Path.home() / '.stylestack' / 'templates'
        if not templates_dir.exists():
            return []
        
        templates = []
        for template_file in templates_dir.glob('*.yml'):
            try:
                with open(template_file, 'r') as f:
                    template_data = yaml.safe_load(f)
                templates.append({
                    'name': template_data.get('name', template_file.stem),
                    'description': template_data.get('description', ''),
                    'file': str(template_file)
                })
            except Exception:
                continue  # Skip invalid template files
        
        return templates
    
    def list_available_orgs(self) -> List[str]:
        """List available organizations from orgs directory."""
        orgs_path = Path(self.config_data.get('paths', {}).get('orgs', 'orgs/'))
        if not orgs_path.exists():
            return []
        
        orgs = []
        for org_dir in orgs_path.iterdir():
            if org_dir.is_dir() and (org_dir / 'design-tokens.json').exists():
                orgs.append(org_dir.name)
        
        return sorted(orgs)
    
    def list_available_channels(self) -> List[str]:
        """List available channels from channels directory."""
        channels_path = Path(self.config_data.get('paths', {}).get('channels', 'channels/'))
        if not channels_path.exists():
            return []
        
        channels = []
        for channel_file in channels_path.glob('*-design-tokens.json'):
            channel_name = channel_file.stem.replace('-design-tokens', '')
            channels.append(channel_name)
        
        return sorted(channels)
    
    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'defaults.org')."""
        keys = key_path.split('.')
        value = self.config_data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set_config_value(self, key_path: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        keys = key_path.split('.')
        config = self.config_data
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value


class ConfigError(Exception):
    """Configuration error exception."""
    pass


class ConfigValidationError(ConfigError):
    """Configuration validation error exception."""
    pass