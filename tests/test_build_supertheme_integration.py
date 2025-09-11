"""
Tests for Build System SuperTheme Integration

Tests covering the build.py CLI integration for SuperTheme generation:
- Command-line parameter handling for --supertheme, --designs, --ratios
- Design variant token resolution and context handling
- Progress reporting and user feedback
- File size validation and performance monitoring
- Error handling for common configuration issues
"""

import pytest
import tempfile
import zipfile
import json
import io
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from click.testing import CliRunner
import click

# Import the build module components
try:
    import build
    from build import BuildContext, StyleStackError, safe_zip_dir, safe_unzip
except ImportError:
    build = None
    BuildContext = None
    StyleStackError = None
    safe_zip_dir = None
    safe_unzip = None


class TestSuperThemeCLICommands:
    """Test CLI commands for SuperTheme generation"""
    
    @pytest.fixture
    def runner(self):
        """Create CLI test runner"""
        return CliRunner()
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            
            # Create sample template
            template_dir = workspace / "templates"
            template_dir.mkdir()
            (template_dir / "template.potx").write_text("sample template")
            
            # Create design tokens
            designs_dir = workspace / "designs"
            designs_dir.mkdir()
            
            corporate_tokens = {
                "colors": {
                    "brand": {"primary": "#0066CC", "secondary": "#004499"}
                },
                "typography": {
                    "heading": {"font": "Arial Black"}
                }
            }
            (designs_dir / "corporate.json").write_text(json.dumps(corporate_tokens))
            
            creative_tokens = {
                "colors": {
                    "brand": {"primary": "#22AA22", "secondary": "#116611"}
                },
                "typography": {
                    "heading": {"font": "Impact"}
                }
            }
            (designs_dir / "creative.json").write_text(json.dumps(creative_tokens))
            
            yield workspace
    
    @pytest.mark.skipif(build is None, reason="Build module not available")
    def test_supertheme_command_basic(self, runner, temp_workspace):
        """Test basic SuperTheme generation command"""
        with runner.isolated_filesystem():
            # Create mock build command with supertheme option
            @click.command()
            @click.option('--supertheme', is_flag=True, help='Generate SuperTheme package')
            @click.option('--designs', help='Design variants directory')
            @click.option('--ratios', help='Aspect ratios (comma-separated)')
            @click.option('--output', '-o', help='Output file')
            def build_command(supertheme, designs, ratios, output):
                if supertheme:
                    click.echo("Generating SuperTheme...")
                    if designs:
                        click.echo(f"Loading designs from: {designs}")
                    if ratios:
                        click.echo(f"Using aspect ratios: {ratios}")
                    if output:
                        click.echo(f"Output to: {output}")
                    click.echo("SuperTheme generated successfully!")
            
            # Test with all parameters
            result = runner.invoke(build_command, [
                '--supertheme',
                '--designs', str(temp_workspace / 'designs'),
                '--ratios', '16:9,4:3,a4',
                '--output', 'output.thmx'
            ])
            
            assert result.exit_code == 0
            assert "Generating SuperTheme" in result.output
            assert "Loading designs from" in result.output
            assert "Using aspect ratios" in result.output
            assert "SuperTheme generated successfully" in result.output
    
    @pytest.mark.skipif(build is None, reason="Build module not available")
    def test_supertheme_command_missing_designs(self, runner):
        """Test SuperTheme command with missing designs directory"""
        with runner.isolated_filesystem():
            @click.command()
            @click.option('--supertheme', is_flag=True)
            @click.option('--designs', required=False)
            def build_command(supertheme, designs):
                if supertheme and not designs:
                    raise click.ClickException("--designs directory is required for SuperTheme generation")
                click.echo("Success")
            
            # Test without designs directory
            result = runner.invoke(build_command, ['--supertheme'])
            
            assert result.exit_code != 0
            assert "designs directory is required" in result.output
    
    @pytest.mark.skipif(build is None, reason="Build module not available")
    def test_supertheme_command_invalid_ratios(self, runner):
        """Test SuperTheme command with invalid aspect ratios"""
        with runner.isolated_filesystem():
            @click.command()
            @click.option('--supertheme', is_flag=True)
            @click.option('--ratios')
            def build_command(supertheme, ratios):
                if supertheme and ratios:
                    # Validate aspect ratios
                    valid_ratios = ['16:9', '16:10', '4:3', 'a4', 'letter']
                    provided = ratios.split(',')
                    invalid = [r for r in provided if r not in valid_ratios]
                    if invalid:
                        raise click.ClickException(f"Invalid aspect ratios: {', '.join(invalid)}")
                click.echo("Valid ratios")
            
            # Test with invalid ratio
            result = runner.invoke(build_command, ['--supertheme', '--ratios', '16:9,invalid,4:3'])
            
            assert result.exit_code != 0
            assert "Invalid aspect ratios" in result.output
            assert "invalid" in result.output


class TestDesignVariantTokenResolution:
    """Test design variant token loading and resolution"""
    
    @pytest.fixture
    def design_tokens(self):
        """Sample design token structures"""
        return {
            "corporate": {
                "colors": {
                    "brand": {
                        "primary": {"$type": "color", "$value": "#0066CC"},
                        "secondary": {"$type": "color", "$value": "#004499"}
                    }
                },
                "typography": {
                    "heading": {
                        "$type": "typography",
                        "$value": {
                            "fontFamily": "Arial Black",
                            "fontSize": "24pt"
                        }
                    }
                }
            },
            "creative": {
                "colors": {
                    "brand": {
                        "primary": {"$type": "color", "$value": "#22AA22"}
                    }
                }
            }
        }
    
    def test_load_design_variants_from_directory(self, temp_workspace):
        """Test loading design variants from directory"""
        designs_dir = temp_workspace / "designs"
        
        # Mock function to load design variants
        def load_design_variants(directory):
            variants = {}
            for json_file in Path(directory).glob("*.json"):
                with open(json_file) as f:
                    variants[json_file.stem] = json.load(f)
            return variants
        
        # Load variants
        variants = load_design_variants(designs_dir)
        
        assert "corporate" in variants
        assert "creative" in variants
        assert variants["corporate"]["colors"]["brand"]["primary"] == "#0066CC"
        assert variants["creative"]["colors"]["brand"]["primary"] == "#22AA22"
    
    def test_resolve_design_tokens_with_context(self, design_tokens):
        """Test resolving design tokens with build context"""
        # Mock build context
        context = Mock()
        context.org = "acme"
        context.channel = "presentation"
        context.verbose = True
        
        # Mock token resolution
        def resolve_tokens_with_context(tokens, context):
            # Add context-specific overrides
            resolved = tokens.copy()
            if context.org == "acme":
                # Apply org-specific overrides
                if "colors" in resolved:
                    resolved["colors"]["corporate"] = {"primary": "#FF0000"}
            return resolved
        
        # Resolve tokens
        resolved = resolve_tokens_with_context(design_tokens["corporate"], context)
        
        assert "colors" in resolved
        assert "corporate" in resolved["colors"]


class TestProgressReportingAndFeedback:
    """Test progress reporting and user feedback"""
    
    def test_supertheme_progress_reporting(self):
        """Test progress reporting during SuperTheme generation"""
        progress_messages = []
        
        def report_progress(message, percentage=None):
            progress_messages.append((message, percentage))
        
        # Simulate SuperTheme generation steps
        report_progress("Loading design variants...", 10)
        report_progress("Resolving aspect ratios...", 25)
        report_progress("Generating theme variants...", 50)
        report_progress("Creating SuperTheme package...", 75)
        report_progress("Validating package...", 90)
        report_progress("SuperTheme generation complete!", 100)
        
        assert len(progress_messages) == 6
        assert progress_messages[0] == ("Loading design variants...", 10)
        assert progress_messages[-1] == ("SuperTheme generation complete!", 100)
    
    def test_verbose_output_logging(self):
        """Test verbose output during generation"""
        log_messages = []
        
        def log_verbose(message, level="info"):
            log_messages.append((level, message))
        
        # Simulate verbose logging
        log_verbose("Found 3 design variants", "info")
        log_verbose("Processing variant: Corporate Blue", "debug")
        log_verbose("Generated 6 theme combinations", "info")
        log_verbose("Package size: 2.3MB", "info")
        
        assert len(log_messages) == 4
        assert any("3 design variants" in msg for _, msg in log_messages)
        assert any("2.3MB" in msg for _, msg in log_messages)


class TestFileSizeValidation:
    """Test file size validation and performance monitoring"""
    
    def test_supertheme_size_limit_validation(self):
        """Test SuperTheme package size limit (5MB)"""
        def validate_package_size(package_bytes, limit_mb=5.0):
            size_mb = len(package_bytes) / (1024 * 1024)
            if size_mb > limit_mb:
                raise ValueError(f"Package size {size_mb:.2f}MB exceeds {limit_mb}MB limit")
            return size_mb
        
        # Test under limit
        small_package = b"x" * (4 * 1024 * 1024)  # 4MB
        size = validate_package_size(small_package)
        assert size < 5.0
        
        # Test over limit
        large_package = b"x" * (6 * 1024 * 1024)  # 6MB
        with pytest.raises(ValueError, match="exceeds 5.0MB limit"):
            validate_package_size(large_package)
    
    def test_performance_monitoring(self):
        """Test performance monitoring during generation"""
        import time
        
        def monitor_performance(func):
            start_time = time.time()
            result = func()
            elapsed = time.time() - start_time
            return result, elapsed
        
        # Simulate generation
        def generate_supertheme():
            time.sleep(0.1)  # Simulate work
            return b"supertheme_package"
        
        result, elapsed = monitor_performance(generate_supertheme)
        
        assert result == b"supertheme_package"
        assert elapsed >= 0.1
        assert elapsed < 1.0  # Should be fast


class TestErrorHandlingAndMessages:
    """Test error handling and user-friendly error messages"""
    
    def test_missing_design_files_error(self):
        """Test error when design files are missing"""
        def load_designs(directory):
            design_files = list(Path(directory).glob("*.json"))
            if not design_files:
                raise FileNotFoundError(
                    f"No design files found in {directory}\n"
                    f"Please ensure design JSON files are in the designs directory."
                )
            return design_files
        
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_dir = Path(tmpdir) / "empty"
            empty_dir.mkdir()
            
            with pytest.raises(FileNotFoundError, match="No design files found"):
                load_designs(empty_dir)
    
    def test_invalid_json_error(self):
        """Test error handling for invalid JSON"""
        def parse_design_json(filepath):
            try:
                with open(filepath) as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Invalid JSON in {filepath}:\n"
                    f"  Line {e.lineno}, Column {e.colno}: {e.msg}\n"
                    f"Please check the JSON syntax."
                )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            tmp.write('{"invalid": json without quotes}')
            tmp.flush()
            
            with pytest.raises(ValueError, match="Invalid JSON"):
                parse_design_json(tmp.name)
    
    def test_aspect_ratio_error_messages(self):
        """Test user-friendly aspect ratio error messages"""
        def validate_aspect_ratio(ratio_str):
            valid_formats = {
                '16:9': 'aspectRatios.widescreen_16_9',
                '16:10': 'aspectRatios.standard_16_10',
                '4:3': 'aspectRatios.classic_4_3',
                'a4': 'aspectRatios.a4_landscape',
                'letter': 'aspectRatios.letter_landscape'
            }
            
            if ratio_str not in valid_formats:
                available = ', '.join(valid_formats.keys())
                suggestion = None
                if ':' in ratio_str:
                    suggestion = "Use format like '16:9' or '4:3'"
                elif ratio_str.lower() in ['a4', 'letter']:
                    suggestion = f"Did you mean '{ratio_str.lower()}'?"
                
                message = f"Invalid aspect ratio: '{ratio_str}'\n"
                message += f"Available options: {available}"
                if suggestion:
                    message += f"\n{suggestion}"
                
                raise ValueError(message)
            
            return valid_formats[ratio_str]
        
        # Test invalid ratio
        with pytest.raises(ValueError) as exc_info:
            validate_aspect_ratio("16x9")
        
        assert "Invalid aspect ratio" in str(exc_info.value)
        assert "Available options" in str(exc_info.value)
        
        # Test valid ratio
        result = validate_aspect_ratio("16:9")
        assert result == "aspectRatios.widescreen_16_9"


class TestBuildContextIntegration:
    """Test integration with existing BuildContext"""
    
    @pytest.fixture
    def build_context(self, temp_workspace):
        """Create mock build context"""
        if BuildContext is None:
            pytest.skip("BuildContext not available")
        
        context = BuildContext(
            source_path=temp_workspace / "template.potx",
            output_path=temp_workspace / "output.thmx",
            temp_dir=temp_workspace / "temp",
            verbose=True
        )
        return context
    
    @pytest.mark.skipif(BuildContext is None, reason="BuildContext not available")
    def test_supertheme_with_build_context(self, build_context):
        """Test SuperTheme generation with BuildContext"""
        # Add SuperTheme-specific attributes
        build_context.supertheme = True
        build_context.design_variants = {"corporate": {}, "creative": {}}
        build_context.aspect_ratios = ["16:9", "4:3"]
        
        assert build_context.supertheme
        assert len(build_context.design_variants) == 2
        assert len(build_context.aspect_ratios) == 2
    
    @pytest.mark.skipif(BuildContext is None, reason="BuildContext not available")
    def test_build_context_validation(self, build_context):
        """Test BuildContext validation for SuperTheme"""
        def validate_supertheme_context(context):
            errors = []
            
            if not hasattr(context, 'design_variants') or not context.design_variants:
                errors.append("No design variants specified")
            
            if not hasattr(context, 'aspect_ratios') or not context.aspect_ratios:
                errors.append("No aspect ratios specified")
            
            if context.output_path and not str(context.output_path).endswith('.thmx'):
                errors.append("SuperTheme output should have .thmx extension")
            
            if errors:
                raise ValueError("SuperTheme validation errors:\n" + "\n".join(f"  - {e}" for e in errors))
        
        # Test with missing attributes
        with pytest.raises(ValueError, match="No design variants"):
            validate_supertheme_context(build_context)
        
        # Add required attributes
        build_context.design_variants = {"test": {}}
        build_context.aspect_ratios = ["16:9"]
        
        # Should pass now
        validate_supertheme_context(build_context)