"""Configuration management for OOXML Round-Trip Testing Utility."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from .exceptions import ConfigurationError


@dataclass
class PlatformConfig:
    """Configuration for a specific platform."""
    name: str
    enabled: bool = True
    executable_path: Optional[str] = None
    timeout: int = 120  # seconds
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OutputConfig:
    """Configuration for output formatting and reporting."""
    format: str = "html"
    verbose: bool = False
    include_screenshots: bool = True
    diff_threshold: float = 0.01
    template: Optional[str] = None


@dataclass
class LoggingConfig:
    """Configuration for logging system."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None
    console: bool = True


class Config:
    """Main configuration class for OOXML Tester."""
    
    def __init__(self):
        """Initialize with default configuration."""
        self.platforms = self._default_platforms()
        self.output = OutputConfig()
        self.logging = LoggingConfig()
        self.temp_dir = Path.cwd() / "temp"
        self.office_paths = self._default_office_paths()
        
    def _default_platforms(self) -> Dict[str, PlatformConfig]:
        """Get default platform configurations."""
        return {
            "office": PlatformConfig(
                name="Microsoft Office",
                enabled=True,
                timeout=180
            ),
            "libreoffice": PlatformConfig(
                name="LibreOffice",
                enabled=True,
                timeout=120
            ),
            "google": PlatformConfig(
                name="Google Workspace",
                enabled=False,  # Requires API setup
                timeout=300
            )
        }
    
    def _default_office_paths(self) -> Dict[str, str]:
        """Get default office application paths."""
        import platform
        system = platform.system()
        
        if system == "Windows":
            return {
                "word": "C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE",
                "powerpoint": "C:\\Program Files\\Microsoft Office\\root\\Office16\\POWERPNT.EXE",
                "excel": "C:\\Program Files\\Microsoft Office\\root\\Office16\\EXCEL.EXE",
                "libreoffice": "C:\\Program Files\\LibreOffice\\program\\soffice.exe"
            }
        elif system == "Darwin":  # macOS
            return {
                "word": "/Applications/Microsoft Word.app",
                "powerpoint": "/Applications/Microsoft PowerPoint.app", 
                "excel": "/Applications/Microsoft Excel.app",
                "libreoffice": "/Applications/LibreOffice.app/Contents/MacOS/soffice"
            }
        else:  # Linux
            return {
                "libreoffice": "/usr/bin/libreoffice",
                "openoffice": "/usr/bin/openoffice"
            }
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> 'Config':
        """Load configuration from file."""
        config = cls()
        
        if config_path:
            config_file = Path(config_path)
            if not config_file.exists():
                raise ConfigurationError(f"Configuration file not found: {config_path}")
                
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                config._load_from_dict(data)
            except yaml.YAMLError as e:
                raise ConfigurationError(f"Invalid YAML in config file: {e}")
            except Exception as e:
                raise ConfigurationError(f"Error loading config file: {e}")
        
        # Override with environment variables
        config._load_from_env()
        
        return config
    
    def _load_from_dict(self, data: Dict[str, Any]) -> None:
        """Load configuration from dictionary."""
        if "platforms" in data:
            for name, platform_data in data["platforms"].items():
                if name in self.platforms:
                    platform = self.platforms[name]
                    platform.enabled = platform_data.get("enabled", platform.enabled)
                    platform.executable_path = platform_data.get("executable_path", platform.executable_path)
                    platform.timeout = platform_data.get("timeout", platform.timeout)
                    platform.options = platform_data.get("options", platform.options)
        
        if "output" in data:
            output_data = data["output"]
            self.output.format = output_data.get("format", self.output.format)
            self.output.verbose = output_data.get("verbose", self.output.verbose)
            self.output.include_screenshots = output_data.get("include_screenshots", self.output.include_screenshots)
            self.output.diff_threshold = output_data.get("diff_threshold", self.output.diff_threshold)
            self.output.template = output_data.get("template", self.output.template)
        
        if "logging" in data:
            logging_data = data["logging"]
            self.logging.level = logging_data.get("level", self.logging.level)
            self.logging.format = logging_data.get("format", self.logging.format)
            self.logging.file = logging_data.get("file", self.logging.file)
            self.logging.console = logging_data.get("console", self.logging.console)
        
        if "temp_dir" in data:
            self.temp_dir = Path(data["temp_dir"])
        
        if "office_paths" in data:
            self.office_paths.update(data["office_paths"])
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # Platform overrides
        for platform_name in self.platforms:
            env_var = f"OOXML_TESTER_{platform_name.upper()}_ENABLED"
            if env_var in os.environ:
                self.platforms[platform_name].enabled = os.environ[env_var].lower() == "true"
        
        # Output overrides
        if "OOXML_TESTER_OUTPUT_FORMAT" in os.environ:
            self.output.format = os.environ["OOXML_TESTER_OUTPUT_FORMAT"]
        
        if "OOXML_TESTER_VERBOSE" in os.environ:
            self.output.verbose = os.environ["OOXML_TESTER_VERBOSE"].lower() == "true"
        
        # Logging overrides
        if "OOXML_TESTER_LOG_LEVEL" in os.environ:
            self.logging.level = os.environ["OOXML_TESTER_LOG_LEVEL"]
        
        # Temp directory override
        if "OOXML_TESTER_TEMP_DIR" in os.environ:
            self.temp_dir = Path(os.environ["OOXML_TESTER_TEMP_DIR"])
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Check temp directory is writable
        try:
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            test_file = self.temp_dir / "test_write"
            test_file.touch()
            test_file.unlink()
        except Exception:
            issues.append(f"Temp directory not writable: {self.temp_dir}")
        
        # Validate platform executables
        for name, platform in self.platforms.items():
            if platform.enabled and platform.executable_path:
                path = Path(platform.executable_path)
                if not path.exists():
                    issues.append(f"Platform executable not found: {name} - {platform.executable_path}")
        
        # Validate logging configuration
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.logging.level not in valid_log_levels:
            issues.append(f"Invalid log level: {self.logging.level}")
        
        return issues
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "platforms": {
                name: {
                    "name": platform.name,
                    "enabled": platform.enabled,
                    "executable_path": platform.executable_path,
                    "timeout": platform.timeout,
                    "options": platform.options
                }
                for name, platform in self.platforms.items()
            },
            "output": {
                "format": self.output.format,
                "verbose": self.output.verbose,
                "include_screenshots": self.output.include_screenshots,
                "diff_threshold": self.output.diff_threshold,
                "template": self.output.template
            },
            "logging": {
                "level": self.logging.level,
                "format": self.logging.format,
                "file": self.logging.file,
                "console": self.logging.console
            },
            "temp_dir": str(self.temp_dir),
            "office_paths": self.office_paths
        }