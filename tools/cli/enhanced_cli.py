"""
Enhanced CLI framework with Rich UI components, progress bars, and improved error handling.
"""

import os
import sys
import click
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from rich.console import Console
from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, MofNCompleteColumn
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import print as rprint
from rich.syntax import Syntax
from rich.tree import Tree

from .config_manager import ConfigManager
from .error_handler import EnhancedErrorHandler
from .progress_manager import ProgressManager
from .batch_processor import BatchProcessor
from .interactive import InteractiveCLI


@dataclass
class CLIContext:
    """Enhanced CLI context with rich console support."""
    console: Console
    config_manager: ConfigManager
    error_handler: EnhancedErrorHandler
    progress_manager: ProgressManager
    batch_processor: Optional[BatchProcessor] = None
    interactive_cli: Optional[InteractiveCLI] = None
    verbose: bool = False
    quiet: bool = False
    config: Dict[str, Any] = None


class EnhancedCLI:
    """Enhanced CLI framework with Rich UI components."""
    
    def __init__(self):
        """Initialize enhanced CLI with Rich components."""
        self.console = Console()
        self.config_manager = ConfigManager()
        self.error_handler = EnhancedErrorHandler(self.console)
        self.progress_manager = ProgressManager(self.console)
        self.batch_processor = None
        self.interactive_cli = None
        
    def create_context(self, **kwargs) -> CLIContext:
        """Create CLI context with configuration."""
        # Load configuration
        config = self.config_manager.load_config(
            config_file=kwargs.get('config'),
            env_prefix=kwargs.get('env_prefix', 'STYLESTACK'),
            **kwargs
        )
        
        # Create context
        context = CLIContext(
            console=self.console,
            config_manager=self.config_manager,
            error_handler=self.error_handler,
            progress_manager=self.progress_manager,
            verbose=kwargs.get('verbose', False),
            quiet=kwargs.get('quiet', False),
            config=config
        )
        
        # Initialize optional components
        if kwargs.get('batch') or kwargs.get('interactive'):
            context.batch_processor = BatchProcessor(context)
            
        if kwargs.get('interactive'):
            context.interactive_cli = InteractiveCLI(context)
            
        return context
    
    def print_banner(self, context: CLIContext):
        """Print StyleStack banner with version info."""
        if context.quiet:
            return
            
        banner = Text()
        banner.append("🎨 ", style="bright_blue")
        banner.append("StyleStack", style="bold bright_blue")
        banner.append(" CLI", style="bright_white")
        
        version_info = context.config.get('version', '2026.1.0')
        banner.append(f" v{version_info}", style="dim")
        
        context.console.print(Panel(banner, expand=False, border_style="blue"))
    
    def print_config_summary(self, context: CLIContext):
        """Print configuration summary if verbose."""
        if not context.verbose or context.quiet:
            return
            
        table = Table(title="Configuration Summary", show_header=True)
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        table.add_column("Source", style="dim")
        
        # Add key configuration values
        config_items = [
            ('Organization', context.config.get('org', 'None'), 'CLI/Config'),
            ('Channel', context.config.get('channel', 'None'), 'CLI/Config'),
            ('Parallel Processing', str(context.config.get('parallel', False)), 'Config'),
            ('Max Workers', str(context.config.get('max_workers', 4)), 'Config'),
            ('Verbose Mode', str(context.verbose), 'CLI'),
        ]
        
        for setting, value, source in config_items:
            table.add_row(setting, value, source)
        
        context.console.print(table)
        context.console.print()
    
    def validate_inputs(self, context: CLIContext, **kwargs) -> bool:
        """Validate CLI inputs with enhanced error messages."""
        errors = []
        warnings = []
        
        # Check source file
        if kwargs.get('src'):
            src_path = Path(kwargs['src'])
            if not src_path.exists():
                errors.append(f"Source file not found: {src_path}")
                self._add_file_suggestions(errors, src_path)
        
        # Check output path
        if kwargs.get('out'):
            out_path = Path(kwargs['out'])
            if out_path.exists() and not kwargs.get('force'):
                if not Confirm.ask(f"Output file exists: {out_path}. Overwrite?"):
                    errors.append("Operation cancelled by user")
        
        # Check organization
        if kwargs.get('org'):
            available_orgs = self.config_manager.list_available_orgs()
            if available_orgs and kwargs['org'] not in available_orgs:
                errors.append(f"Invalid organization: {kwargs['org']}")
                errors.append(f"Available organizations: {', '.join(available_orgs)}")
        
        # Display errors and warnings
        if errors:
            context.error_handler.display_validation_errors(errors)
            return False
            
        if warnings:
            context.error_handler.display_warnings(warnings)
        
        return True
    
    def _add_file_suggestions(self, errors: List[str], file_path: Path):
        """Add helpful file path suggestions."""
        suggestions = []
        
        # Check if file exists with different extension
        if file_path.suffix:
            stem = file_path.stem
            parent = file_path.parent
            similar_files = list(parent.glob(f"{stem}.*"))
            if similar_files:
                suggestions.append(f"Similar files found: {', '.join(f.name for f in similar_files[:3])}")
        
        # Check current directory files
        if not file_path.is_absolute():
            cwd_files = [f for f in Path.cwd().iterdir() if f.is_file() and f.suffix in ['.potx', '.dotx', '.xltx']]
            if cwd_files:
                suggestions.append(f"Office templates in current directory: {', '.join(f.name for f in cwd_files[:3])}")
        
        if suggestions:
            errors.extend(f"  💡 {suggestion}" for suggestion in suggestions)
    
    def process_template(self, context: CLIContext, **kwargs) -> bool:
        """Process single template with progress tracking."""
        try:
            # Create progress task
            with context.progress_manager.create_progress() as progress:
                task = progress.add_task("Processing template...", total=100)
                
                # Simulate processing steps with progress updates
                progress.update(task, advance=20, description="Loading template...")
                
                # Import the main processing function
                from build import process_single_template
                
                progress.update(task, advance=30, description="Resolving variables...")
                
                # Process the template
                result = process_single_template(
                    src=kwargs['src'],
                    out=kwargs['out'],
                    org=kwargs.get('org'),
                    channel=kwargs.get('channel'),
                    verbose=context.verbose
                )
                
                progress.update(task, advance=50, description="Finalizing output...")
                
                # Complete progress
                progress.update(task, completed=100, description="✅ Template processed successfully!")
                
                return result
                
        except Exception as e:
            context.error_handler.handle_processing_error(e, context)
            return False
    
    def process_batch(self, context: CLIContext, batch_file: str, **kwargs) -> bool:
        """Process batch of templates."""
        if not context.batch_processor:
            context.batch_processor = BatchProcessor(context)
            
        return context.batch_processor.process_batch_file(batch_file, **kwargs)
    
    def run_interactive_mode(self, context: CLIContext, **kwargs) -> bool:
        """Run interactive CLI mode."""
        if not context.interactive_cli:
            context.interactive_cli = InteractiveCLI(context)
            
        return context.interactive_cli.run_interactive_session(**kwargs)
    
    def print_help_with_examples(self, context: CLIContext):
        """Print enhanced help with examples."""
        help_text = """
[bold cyan]StyleStack CLI - Professional OOXML Template Processing[/bold cyan]

[bold]EXAMPLES:[/bold]

[dim]Basic template processing:[/dim]
  python build.py --src template.potx --out branded.potx --org acme --channel present

[dim]Batch processing:[/dim]
  python build.py --batch templates.json --parallel --max-workers 4

[dim]Corporate branding:[/dim]
  python build.py --src template.potx --out corporate.potx --org acme --config corporate.yml

[dim]Interactive mode:[/dim]
  python build.py --interactive

[dim]SuperTheme generation:[/dim]
  python build.py --supertheme --designs designs/ --ratios 16:9,4:3 --out theme.thmx

[bold]CONFIGURATION:[/bold]

Create a [cyan]stylestack.yml[/cyan] configuration file:
"""
        
        context.console.print(help_text)
        
        # Show sample configuration
        sample_config = {
            'defaults': {
                'org': 'your-org',
                'channel': 'present',
                'verbose': True
            },
            'paths': {
                'templates': 'templates/',
                'output': 'output/'
            }
        }
        
        syntax = Syntax(yaml.dump(sample_config, default_flow_style=False), "yaml", theme="monokai")
        context.console.print(Panel(syntax, title="Sample Configuration"))
    
    def show_diagnostics(self, context: CLIContext) -> Dict[str, str]:
        """Run and display system diagnostics."""
        diagnostics = {
            'Python Version': sys.version.split()[0],
            'Platform': sys.platform,
            'Working Directory': str(Path.cwd()),
            'Config File': str(context.config_manager.config_file) if context.config_manager.config_file else 'None',
            'Available Organizations': ', '.join(context.config_manager.list_available_orgs()) or 'None',
            'Template Directory': context.config.get('paths', {}).get('templates', 'Not configured'),
            'Output Directory': context.config.get('paths', {}).get('output', 'Not configured')
        }
        
        # Check dependencies
        try:
            import lxml
            diagnostics['LXML Version'] = lxml.__version__
        except ImportError:
            diagnostics['LXML Version'] = 'Not installed'
            
        try:
            from rich import __version__ as rich_version
            diagnostics['Rich Version'] = rich_version
        except ImportError:
            diagnostics['Rich Version'] = 'Not installed'
        
        # Display diagnostics table
        table = Table(title="System Diagnostics", show_header=True)
        table.add_column("Component", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        
        for component, status in diagnostics.items():
            table.add_row(component, status)
        
        context.console.print(table)
        return diagnostics
    
    def check_for_updates(self, context: CLIContext) -> Dict[str, Any]:
        """Check for StyleStack updates."""
        # Mock update check - in real implementation would check GitHub releases
        current_version = context.config.get('version', '2026.1.0')
        
        update_info = {
            'current': current_version,
            'latest': '2026.1.1',  # Mock latest version
            'update_available': True,
            'changelog': [
                'Enhanced CLI with Rich UI',
                'Improved batch processing',
                'Better error handling'
            ]
        }
        
        if update_info['update_available']:
            panel_content = f"""
[bold green]Update Available![/bold green]

Current version: [dim]{update_info['current']}[/dim]
Latest version:  [bold]{update_info['latest']}[/bold]

[bold]What's new:[/bold]
""" + '\n'.join(f"  • {item}" for item in update_info['changelog'])

            context.console.print(Panel(panel_content, title="StyleStack Update", border_style="green"))
            
            # Only ask if running in interactive terminal
            try:
                if sys.stdin.isatty() and Confirm.ask("Would you like to visit the release page?"):
                    import webbrowser
                    webbrowser.open("https://github.com/yourusername/stylestack/releases/latest")
            except (EOFError, KeyboardInterrupt):
                # Non-interactive mode, just show the message
                pass
        else:
            context.console.print("[green]✅ StyleStack is up to date![/green]")
        
        return update_info
    
    def list_templates(self, context: CLIContext, template_dir: Optional[str] = None) -> List[Path]:
        """List available templates with details."""
        if not template_dir:
            template_dir = context.config.get('paths', {}).get('templates', 'templates/')
        
        template_path = Path(template_dir)
        if not template_path.exists():
            context.console.print(f"[red]Template directory not found: {template_path}[/red]")
            return []
        
        # Find template files
        template_extensions = ['.potx', '.dotx', '.xltx', '.otp', '.ott', '.ots']
        templates = []
        
        for ext in template_extensions:
            templates.extend(template_path.glob(f"*{ext}"))
            templates.extend(template_path.glob(f"**/*{ext}"))
        
        if not templates:
            context.console.print(f"[yellow]No templates found in: {template_path}[/yellow]")
            return []
        
        # Display templates in a table
        table = Table(title="Available Templates", show_header=True)
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Type", style="green")
        table.add_column("Size", style="dim")
        table.add_column("Modified", style="dim")
        
        for template in sorted(templates):
            template_type = self._get_template_type(template.suffix)
            size = self._format_file_size(template.stat().st_size)
            modified = self._format_timestamp(template.stat().st_mtime)
            
            table.add_row(template.name, template_type, size, modified)
        
        context.console.print(table)
        return templates
    
    def _get_template_type(self, extension: str) -> str:
        """Get human-readable template type from extension."""
        type_map = {
            '.potx': 'PowerPoint Template',
            '.dotx': 'Word Template', 
            '.xltx': 'Excel Template',
            '.otp': 'LibreOffice Presentation Template',
            '.ott': 'LibreOffice Text Template',
            '.ots': 'LibreOffice Spreadsheet Template'
        }
        return type_map.get(extension.lower(), 'Unknown')
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp in human-readable format."""
        import datetime
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M")


def create_enhanced_cli() -> EnhancedCLI:
    """Factory function to create enhanced CLI instance."""
    return EnhancedCLI()