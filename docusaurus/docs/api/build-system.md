---
sidebar_position: 1
---

# Build System API

Complete reference for StyleStack's build system, including the main build script, configuration options, and programmatic usage. This API enables custom build workflows and integrations.

## Command Line Interface

### Basic Usage

```bash
# Build templates for organization
python build.py --org acme --channel presentation --products potx

# Build all channels for organization
python build.py --org acme --all-channels

# Build with validation and verbose output
python build.py --org acme --channel document --validate --verbose

# Build for multiple products
python build.py --org acme --channel corporate --products potx,dotx,xltx
```

### CLI Arguments

#### Required Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--org` | Organization identifier | `--org acme` |

#### Optional Arguments

| Argument | Short | Description | Default | Example |
|----------|-------|-------------|---------|---------|
| `--channel` | `-c` | Channel to build | `presentation` | `--channel academic` |
| `--products` | `-p` | Products to build | `potx,dotx,xltx` | `--products potx` |
| `--output-dir` | `-o` | Output directory | `./` | `--output-dir dist/` |
| `--validate` | `-v` | Run validation after build | `False` | `--validate` |
| `--verbose` | | Enable verbose logging | `False` | `--verbose` |
| `--debug` | | Enable debug mode | `False` | `--debug` |
| `--force` | `-f` | Force rebuild even if up-to-date | `False` | `--force` |
| `--dry-run` | | Show what would be built without building | `False` | `--dry-run` |
| `--all-channels` | | Build all available channels | `False` | `--all-channels` |

#### Advanced Options

| Argument | Description | Example |
|----------|-------------|---------|
| `--config` | Custom config file path | `--config custom-config.yaml` |
| `--template-dir` | Custom template directory | `--template-dir templates/` |
| `--cache-dir` | Build cache directory | `--cache-dir .cache/` |
| `--parallel` | Number of parallel build processes | `--parallel 4` |
| `--profile` | Enable build profiling | `--profile` |
| `--format` | Output format (ooxml, json, yaml) | `--format json` |

### Exit Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | Build completed successfully |
| 1 | General Error | Unspecified build error |
| 2 | Configuration Error | Invalid configuration or arguments |
| 3 | Validation Error | Template validation failed |
| 4 | File Not Found | Required files or directories missing |
| 5 | Permission Error | Insufficient permissions |
| 10 | Timeout Error | Build process timed out |

## Python API

### BuildSystem Class

```python
from stylestack import BuildSystem

# Initialize build system
builder = BuildSystem(
    org="acme",
    config_path="org/acme/patches.yaml",
    cache_dir=".cache"
)

# Build specific channel
result = builder.build_channel(
    channel="presentation",
    products=["potx"],
    output_dir="dist/"
)

# Build all channels
results = builder.build_all_channels()

# Validate existing templates
validation_result = builder.validate_templates("dist/*.potx")
```

#### Constructor Parameters

```python
class BuildSystem:
    def __init__(
        self,
        org: str,                    # Organization identifier
        config_path: str = None,     # Path to organization config
        cache_dir: str = ".cache",   # Build cache directory  
        verbose: bool = False,       # Enable verbose logging
        debug: bool = False,         # Enable debug mode
        parallel: int = None         # Number of parallel processes
    ):
```

#### Core Methods

```python
def build_channel(
    self,
    channel: str,                    # Channel name
    products: List[str],             # Product types to build
    output_dir: str = "./",          # Output directory
    validate: bool = True,           # Run validation
    force: bool = False              # Force rebuild
) -> BuildResult:
    """Build templates for specific channel"""

def build_all_channels(
    self,
    products: List[str] = None,      # Products (default: all)
    output_dir: str = "./",          # Output directory
    validate: bool = True            # Run validation
) -> List[BuildResult]:
    """Build all available channels"""

def validate_templates(
    self,
    template_pattern: str            # Glob pattern for templates
) -> ValidationResult:
    """Validate built templates"""

def get_available_channels(self) -> List[str]:
    """Get list of available channels for organization"""

def get_build_info(self) -> BuildInfo:
    """Get build system information and capabilities"""
```

### BuildResult Class

```python
@dataclass
class BuildResult:
    success: bool                    # Build success status
    channel: str                     # Channel name
    products: List[str]              # Built products
    output_files: List[str]          # Generated template files
    duration: float                  # Build duration in seconds
    warnings: List[str]              # Build warnings
    errors: List[str]                # Build errors
    metadata: Dict[str, Any]         # Additional metadata
    
    def is_successful(self) -> bool:
        return self.success and len(self.errors) == 0
        
    def get_output_files(self, product: str = None) -> List[str]:
        """Get output files, optionally filtered by product"""
        
    def get_summary(self) -> str:
        """Get human-readable build summary"""
```

### Configuration API

```python
from stylestack.config import ConfigManager

# Load organization configuration
config = ConfigManager.load_org_config("acme")

# Get resolved design tokens
tokens = config.get_resolved_tokens()

# Get channel configuration
channel_config = config.get_channel_config("presentation")

# Validate configuration
validation_result = config.validate()
```

#### ConfigManager Methods

```python
class ConfigManager:
    @staticmethod
    def load_org_config(org: str) -> OrgConfig:
        """Load organization configuration"""
    
    @staticmethod
    def load_channel_config(org: str, channel: str) -> ChannelConfig:
        """Load channel configuration"""
    
    @staticmethod
    def get_available_orgs() -> List[str]:
        """Get list of available organizations"""
    
    @staticmethod  
    def validate_config(config_path: str) -> ValidationResult:
        """Validate configuration file"""
```

### Token Resolution API

```python
from stylestack.tokens import TokenResolver

# Initialize token resolver
resolver = TokenResolver(org="acme", channel="presentation")

# Resolve single token
primary_color = resolver.resolve("colors.primary")

# Resolve all tokens
all_tokens = resolver.resolve_all()

# Get token hierarchy
hierarchy = resolver.get_token_hierarchy("colors.primary")

# Test token resolution
test_result = resolver.test_resolution()
```

## Template Processing API

### OOXML Processor

```python
from stylestack.ooxml import OOXMLProcessor

# Initialize processor
processor = OOXMLProcessor(
    template_path="core/ppt/presentation.potx",
    org_config=org_config
)

# Apply organization customizations
processor.apply_patches(patches)

# Process design tokens
processor.resolve_tokens(token_resolver)

# Generate final template
output_path = processor.generate("dist/custom-presentation.potx")
```

#### OOXMLProcessor Methods

```python
class OOXMLProcessor:
    def __init__(
        self,
        template_path: str,          # Path to base template
        org_config: OrgConfig        # Organization configuration
    ):
    
    def apply_patches(self, patches: Dict[str, Any]) -> None:
        """Apply YAML patches to template"""
    
    def resolve_tokens(self, resolver: TokenResolver) -> None:
        """Resolve design tokens in template"""
    
    def inject_assets(self, assets: Dict[str, str]) -> None:
        """Inject brand assets (logos, images)"""
    
    def generate(self, output_path: str) -> str:
        """Generate final template file"""
    
    def validate(self) -> ValidationResult:
        """Validate processed template"""
```

### Asset Management

```python
from stylestack.assets import AssetManager

# Initialize asset manager
assets = AssetManager(org="acme")

# Process logo for template
logo_data = assets.process_logo(
    "org/acme/assets/logo.png",
    target_size=(200, 60),
    format="png"
)

# Get all organization assets
all_assets = assets.get_org_assets()

# Optimize assets for performance
assets.optimize_all_assets(max_size="1MB", quality=85)
```

## Validation API

### Template Validator

```python
from stylestack.validation import TemplateValidator

# Initialize validator
validator = TemplateValidator(org="acme")

# Validate single template
result = validator.validate_template("dist/presentation.potx")

# Validate all templates
results = validator.validate_all_templates("dist/*.potx")

# Run specific validation checks
brand_result = validator.validate_brand_compliance("presentation.potx")
accessibility_result = validator.validate_accessibility("presentation.potx")
```

#### Validation Methods

```python
class TemplateValidator:
    def validate_template(self, template_path: str) -> ValidationResult:
        """Comprehensive template validation"""
    
    def validate_brand_compliance(self, template_path: str) -> ValidationResult:
        """Validate brand guideline compliance"""
    
    def validate_accessibility(
        self, 
        template_path: str,
        standard: str = "WCAG21AA"
    ) -> ValidationResult:
        """Validate accessibility compliance"""
    
    def validate_file_integrity(self, template_path: str) -> ValidationResult:
        """Validate OOXML file integrity"""
    
    def validate_cross_platform(self, template_path: str) -> ValidationResult:
        """Validate cross-platform compatibility"""
```

### ValidationResult Class

```python
@dataclass
class ValidationResult:
    success: bool                    # Overall validation success
    template_path: str               # Validated template path
    checks_passed: int               # Number of checks passed
    checks_failed: int               # Number of checks failed
    errors: List[ValidationError]    # Validation errors
    warnings: List[ValidationWarning] # Validation warnings
    score: float                     # Overall quality score (0-1)
    
    def is_valid(self) -> bool:
        return self.success
    
    def get_error_summary(self) -> str:
        """Get summary of validation errors"""
    
    def get_detailed_report(self) -> str:
        """Get detailed validation report"""
```

## Extension API

### Plugin System

```python
from stylestack.plugins import PluginManager

# Register custom plugin
@PluginManager.register("custom_processor")
class CustomProcessor:
    def process_template(self, template_path, config):
        # Custom processing logic
        pass

# Load and use plugins
plugin_manager = PluginManager()
plugin_manager.load_plugins("plugins/")
result = plugin_manager.execute("custom_processor", template_path, config)
```

### Custom Validators

```python
from stylestack.validation import BaseValidator

class CustomBrandValidator(BaseValidator):
    def validate(self, template_path: str) -> ValidationResult:
        # Custom validation logic
        errors = []
        warnings = []
        
        # Check custom brand requirements
        if not self._check_custom_requirement(template_path):
            errors.append(ValidationError("Custom requirement not met"))
        
        return ValidationResult(
            success=len(errors) == 0,
            template_path=template_path,
            errors=errors,
            warnings=warnings
        )

# Register custom validator
TemplateValidator.register_validator("custom_brand", CustomBrandValidator)
```

## Batch Operations API

### Bulk Building

```python
from stylestack.batch import BatchBuilder

# Initialize batch builder
batch = BatchBuilder()

# Add build jobs
batch.add_job("acme", "presentation", ["potx"])
batch.add_job("acme", "document", ["dotx"])
batch.add_job("university", "academic", ["potx", "dotx"])

# Execute batch build
results = batch.execute(parallel=4, timeout=300)

# Get batch summary
summary = batch.get_summary(results)
```

### Mass Updates

```python
from stylestack.batch import MassUpdater

# Update multiple organizations
updater = MassUpdater()

# Update brand colors across all organizations
updater.update_token("colors.primary", "#1E40AF", orgs=["acme", "university"])

# Apply patch to multiple organizations
patch = {"fonts.heading": "Montserrat"}
updater.apply_patch(patch, orgs=["acme", "university"])

# Execute updates
results = updater.execute()
```

## Monitoring and Metrics API

### Build Metrics

```python
from stylestack.metrics import MetricsCollector

# Initialize metrics collector
metrics = MetricsCollector()

# Track build performance
with metrics.timer("build_duration"):
    build_result = builder.build_channel("presentation", ["potx"])

# Record custom metrics
metrics.counter("templates_built").inc()
metrics.histogram("template_size_bytes").observe(file_size)

# Export metrics
prometheus_metrics = metrics.export_prometheus()
json_metrics = metrics.export_json()
```

### Usage Analytics

```python
from stylestack.analytics import UsageTracker

# Track template usage
tracker = UsageTracker()
tracker.track_download("acme", "presentation.potx", user_id="12345")
tracker.track_usage("acme", "presentation.potx", event="opened")

# Generate analytics reports
report = tracker.generate_report(
    org="acme",
    period="monthly",
    metrics=["downloads", "usage", "user_engagement"]
)
```

## Error Handling

### Exception Types

```python
from stylestack.exceptions import (
    StyleStackError,           # Base exception
    ConfigurationError,        # Configuration issues
    ValidationError,          # Validation failures
    BuildError,               # Build process errors
    TemplateNotFoundError,    # Template file not found
    AssetNotFoundError,       # Asset file not found
    TokenResolutionError      # Token resolution failures
)

try:
    result = builder.build_channel("presentation", ["potx"])
except ConfigurationError as e:
    print(f"Configuration error: {e}")
except BuildError as e:
    print(f"Build failed: {e}")
except StyleStackError as e:
    print(f"General StyleStack error: {e}")
```

### Error Recovery

```python
from stylestack.recovery import ErrorRecovery

# Attempt build with automatic error recovery
recovery = ErrorRecovery()
result = recovery.build_with_recovery(
    org="acme",
    channel="presentation",
    products=["potx"],
    max_retries=3,
    fallback_strategy="use_defaults"
)
```

## Integration Examples

### GitHub Actions Integration

```python
# tools/github-actions-build.py
import os
import json
from stylestack import BuildSystem

def main():
    org = os.environ["INPUT_ORG"]
    channel = os.environ["INPUT_CHANNEL"]
    products = os.environ["INPUT_PRODUCTS"].split(",")
    
    builder = BuildSystem(org=org, verbose=True)
    result = builder.build_channel(channel, products)
    
    # Set GitHub Actions outputs
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.write(f"success={result.is_successful()}\n")
        f.write(f"output_files={json.dumps(result.output_files)}\n")
        f.write(f"duration={result.duration}\n")
    
    return 0 if result.is_successful() else 1

if __name__ == "__main__":
    exit(main())
```

### Custom Build Pipeline

```python
# custom_pipeline.py
from stylestack import BuildSystem, ConfigManager, TemplateValidator

class CustomPipeline:
    def __init__(self, org):
        self.org = org
        self.builder = BuildSystem(org=org)
        self.validator = TemplateValidator(org=org)
        
    def run_pipeline(self):
        # 1. Validate configuration
        config = ConfigManager.load_org_config(self.org)
        if not config.validate().is_valid():
            raise ConfigurationError("Invalid organization configuration")
            
        # 2. Build templates
        results = self.builder.build_all_channels()
        
        # 3. Validate templates
        for result in results:
            for template_file in result.output_files:
                validation = self.validator.validate_template(template_file)
                if not validation.is_valid():
                    print(f"Validation failed for {template_file}")
                    
        # 4. Generate reports
        self._generate_build_report(results)
        
        return all(r.is_successful() for r in results)

# Usage
pipeline = CustomPipeline("acme")
success = pipeline.run_pipeline()
```

## Next Steps

- [Learn token resolution API](./token-resolver.md)
- [Explore OOXML processor details](./ooxml-processor.md)
- [Review CLI command reference](./cli.md)
- [See integration examples](../examples/enterprise.md)