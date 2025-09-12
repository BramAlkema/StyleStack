"""
Interactive CLI features with Rich prompts and guided workflows.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.text import Text
from rich import print as rprint


class InteractiveCLI:
    """Interactive CLI with guided workflows and prompts."""
    
    def __init__(self, context):
        """Initialize interactive CLI."""
        self.context = context
        self.console = context.console
        self.config_manager = context.config_manager
        
    def run_interactive_session(self, **kwargs) -> bool:
        """Run interactive CLI session."""
        self.console.print("\n[bold cyan]🎨 StyleStack Interactive Mode[/bold cyan]\n")
        
        # Display welcome message
        self._display_welcome()
        
        try:
            while True:
                action = self._prompt_main_menu()
                
                if action == 'process':
                    self._interactive_template_processing()
                elif action == 'batch':
                    self._interactive_batch_processing()
                elif action == 'config':
                    self._interactive_configuration()
                elif action == 'help':
                    self._display_interactive_help()
                elif action == 'exit':
                    break
                
                # Ask if user wants to continue
                if not Confirm.ask("\nPerform another action?", default=True):
                    break
                    
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Interactive session cancelled[/yellow]")
            return False
        
        self.console.print("\n[green]✅ Interactive session completed[/green]")
        return True
    
    def _display_welcome(self) -> None:
        """Display welcome message."""
        welcome_text = """
[bold]Welcome to StyleStack Interactive Mode![/bold]

This guided workflow will help you:
• Process templates with corporate branding
• Configure batch processing operations  
• Set up and manage configurations
• Learn StyleStack features interactively

[dim]Use Ctrl+C at any time to exit[/dim]
"""
        
        panel = Panel(welcome_text.strip(), title="Welcome", border_style="blue")
        self.console.print(panel)
    
    def _prompt_main_menu(self) -> str:
        """Display main menu and get user choice."""
        self.console.print("\n[bold]What would you like to do?[/bold]\n")
        
        choices = [
            ("process", "Process a single template"),
            ("batch", "Set up batch processing"),
            ("config", "Configure StyleStack settings"),
            ("help", "Show help and documentation"),
            ("exit", "Exit interactive mode")
        ]
        
        # Display choices
        for i, (key, description) in enumerate(choices, 1):
            self.console.print(f"  [cyan]{i}[/cyan]. {description}")
        
        # Get user choice
        while True:
            try:
                # IntPrompt expects string choices
                choice_str = Prompt.ask("\nSelect an option", choices=[str(i) for i in range(1, len(choices) + 1)])
                choice = int(choice_str)
                return choices[choice - 1][0]
            except (ValueError, IndexError):
                self.console.print("[red]Invalid choice. Please try again.[/red]")
    
    def _interactive_template_processing(self) -> None:
        """Interactive template processing workflow."""
        self.console.print("\n[bold cyan]📄 Template Processing[/bold cyan]\n")
        
        # Step 1: Select source template
        src_path = self._prompt_source_template()
        if not src_path:
            return
        
        # Step 2: Select output location
        out_path = self._prompt_output_location(src_path)
        
        # Step 3: Select organization
        org = self._prompt_organization()
        
        # Step 4: Select channel
        channel = self._prompt_channel()
        
        # Step 5: Additional options
        verbose = Confirm.ask("Enable verbose output?", default=False)
        
        # Display processing summary
        self._display_processing_summary(src_path, out_path, org, channel, verbose)
        
        if not Confirm.ask("Proceed with template processing?", default=True):
            self.console.print("[yellow]Template processing cancelled[/yellow]")
            return
        
        # Process template
        try:
            from build import process_single_template
            
            with self.context.progress_manager.create_progress() as progress:
                task = progress.add_task("Processing template...", total=100)
                
                progress.update(task, advance=30, description="Loading template...")
                
                success = process_single_template(
                    src=str(src_path),
                    out=str(out_path),
                    org=org,
                    channel=channel,
                    verbose=verbose
                )
                
                progress.update(task, completed=100, description="✅ Processing complete!")
                
            if success:
                self.console.print(f"\n[green]✅ Template processed successfully: {out_path}[/green]")
            else:
                self.console.print(f"\n[red]❌ Template processing failed[/red]")
                
        except Exception as e:
            self.context.error_handler.handle_processing_error(e, self.context)
    
    def _interactive_batch_processing(self) -> None:
        """Interactive batch processing setup."""
        self.console.print("\n[bold cyan]📦 Batch Processing Setup[/bold cyan]\n")
        
        # Choice: Load existing batch config or create new
        if self._has_existing_batch_configs():
            choice = Prompt.ask(
                "Load existing batch configuration or create new?",
                choices=["load", "create", "cancel"],
                default="load"
            )
            
            if choice == "cancel":
                return
            elif choice == "load":
                return self._load_existing_batch_config()
        else:
            choice = "create"
        
        # Create new batch configuration
        if choice == "create":
            self._create_batch_configuration()
    
    def _interactive_configuration(self) -> None:
        """Interactive configuration management."""
        self.console.print("\n[bold cyan]⚙️ Configuration Management[/bold cyan]\n")
        
        config_actions = [
            ("view", "View current configuration"),
            ("edit", "Edit configuration settings"),
            ("template", "Create configuration template"),
            ("reset", "Reset to defaults"),
            ("back", "Back to main menu")
        ]
        
        # Display configuration actions
        for i, (key, description) in enumerate(config_actions, 1):
            self.console.print(f"  [cyan]{i}[/cyan]. {description}")
        
        try:
            choice = IntPrompt.ask("\nSelect action", choices=list(range(1, len(config_actions) + 1)))
            action = config_actions[choice - 1][0]
            
            if action == "view":
                self._view_current_configuration()
            elif action == "edit":
                self._edit_configuration_settings()
            elif action == "template":
                self._create_configuration_template()
            elif action == "reset":
                self._reset_configuration()
                
        except (ValueError, IndexError):
            self.console.print("[red]Invalid choice[/red]")
    
    def _prompt_source_template(self) -> Optional[Path]:
        """Prompt user to select source template."""
        # List available templates
        available_templates = self._find_available_templates()
        
        if not available_templates:
            self.console.print("[yellow]No templates found in current directory[/yellow]")
            
            # Prompt for manual path entry
            manual_path = Prompt.ask("Enter template path manually (or press Enter to cancel)")
            if manual_path:
                path = Path(manual_path)
                if path.exists():
                    return path
                else:
                    self.console.print(f"[red]File not found: {path}[/red]")
            return None
        
        # Display available templates
        self.console.print("[bold]Available templates:[/bold]")
        for i, template in enumerate(available_templates, 1):
            size = self._format_file_size(template.stat().st_size)
            self.console.print(f"  [cyan]{i}[/cyan]. {template.name} ([dim]{size}[/dim])")
        
        # Add option for manual entry
        self.console.print(f"  [cyan]{len(available_templates) + 1}[/cyan]. Enter path manually")
        
        try:
            choice = IntPrompt.ask(
                "\nSelect template",
                choices=list(range(1, len(available_templates) + 2))
            )
            
            if choice <= len(available_templates):
                return available_templates[choice - 1]
            else:
                # Manual path entry
                manual_path = Prompt.ask("Enter template path")
                path = Path(manual_path)
                if path.exists():
                    return path
                else:
                    self.console.print(f"[red]File not found: {path}[/red]")
                    return None
                    
        except (ValueError, IndexError):
            self.console.print("[red]Invalid choice[/red]")
            return None
    
    def _prompt_output_location(self, src_path: Path) -> Path:
        """Prompt user for output location."""
        # Suggest default output path
        default_name = src_path.stem + "_branded" + src_path.suffix
        default_path = src_path.parent / default_name
        
        output_path = Prompt.ask(
            "Output file path",
            default=str(default_path)
        )
        
        path = Path(output_path)
        
        # Check if file already exists
        if path.exists():
            if not Confirm.ask(f"File exists: {path}. Overwrite?"):
                return self._prompt_output_location(src_path)  # Recursive retry
        
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        return path
    
    def _prompt_organization(self) -> Optional[str]:
        """Prompt user to select organization."""
        available_orgs = self.config_manager.list_available_orgs()
        
        if not available_orgs:
            self.console.print("[yellow]No organizations configured[/yellow]")
            
            manual_org = Prompt.ask("Enter organization name (or press Enter for none)", default="")
            return manual_org if manual_org else None
        
        # Display available organizations
        self.console.print("[bold]Available organizations:[/bold]")
        for i, org in enumerate(available_orgs, 1):
            self.console.print(f"  [cyan]{i}[/cyan]. {org}")
        
        # Add options for manual entry or none
        self.console.print(f"  [cyan]{len(available_orgs) + 1}[/cyan]. Enter manually")
        self.console.print(f"  [cyan]{len(available_orgs) + 2}[/cyan]. None")
        
        try:
            choice = IntPrompt.ask(
                "\nSelect organization",
                choices=list(range(1, len(available_orgs) + 3))
            )
            
            if choice <= len(available_orgs):
                return available_orgs[choice - 1]
            elif choice == len(available_orgs) + 1:
                return Prompt.ask("Enter organization name")
            else:
                return None
                
        except (ValueError, IndexError):
            self.console.print("[red]Invalid choice[/red]")
            return None
    
    def _prompt_channel(self) -> Optional[str]:
        """Prompt user to select channel."""
        available_channels = self.config_manager.list_available_channels()
        
        if not available_channels:
            self.console.print("[yellow]No channels configured[/yellow]")
            
            manual_channel = Prompt.ask("Enter channel name (or press Enter for none)", default="")
            return manual_channel if manual_channel else None
        
        # Display available channels
        self.console.print("[bold]Available channels:[/bold]")
        for i, channel in enumerate(available_channels, 1):
            self.console.print(f"  [cyan]{i}[/cyan]. {channel}")
        
        # Add options for manual entry or none
        self.console.print(f"  [cyan]{len(available_channels) + 1}[/cyan]. Enter manually")
        self.console.print(f"  [cyan]{len(available_channels) + 2}[/cyan]. None")
        
        try:
            choice = IntPrompt.ask(
                "\nSelect channel",
                choices=list(range(1, len(available_channels) + 3))
            )
            
            if choice <= len(available_channels):
                return available_channels[choice - 1]
            elif choice == len(available_channels) + 1:
                return Prompt.ask("Enter channel name")
            else:
                return None
                
        except (ValueError, IndexError):
            self.console.print("[red]Invalid choice[/red]")
            return None
    
    def _display_processing_summary(self, src: Path, out: Path, org: str, channel: str, verbose: bool) -> None:
        """Display processing summary before execution."""
        table = Table(title="Processing Summary", show_header=True)
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        
        table.add_row("Source Template", str(src))
        table.add_row("Output File", str(out))
        table.add_row("Organization", org or "None")
        table.add_row("Channel", channel or "None")
        table.add_row("Verbose Mode", str(verbose))
        
        self.console.print(table)
    
    def _find_available_templates(self) -> List[Path]:
        """Find available template files in current directory."""
        template_extensions = ['.potx', '.dotx', '.xltx', '.otp', '.ott', '.ots']
        templates = []
        
        current_dir = Path.cwd()
        
        for ext in template_extensions:
            templates.extend(current_dir.glob(f"*{ext}"))
            
        # Also check templates directory if configured
        templates_dir = self.context.config.get('paths', {}).get('templates')
        if templates_dir:
            templates_dir = Path(templates_dir)
            if templates_dir.exists():
                for ext in template_extensions:
                    templates.extend(templates_dir.glob(f"*{ext}"))
        
        return sorted(set(templates))
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def _has_existing_batch_configs(self) -> bool:
        """Check if existing batch configurations exist."""
        current_dir = Path.cwd()
        batch_files = list(current_dir.glob("batch*.json")) + list(current_dir.glob("batch*.yml"))
        return len(batch_files) > 0
    
    def _load_existing_batch_config(self) -> None:
        """Load and run existing batch configuration."""
        current_dir = Path.cwd()
        batch_files = list(current_dir.glob("batch*.json")) + list(current_dir.glob("batch*.yml"))
        
        if not batch_files:
            self.console.print("[yellow]No batch configuration files found[/yellow]")
            return
        
        # Display available batch files
        self.console.print("[bold]Available batch configurations:[/bold]")
        for i, batch_file in enumerate(batch_files, 1):
            self.console.print(f"  [cyan]{i}[/cyan]. {batch_file.name}")
        
        try:
            choice = IntPrompt.ask(
                "\nSelect batch configuration",
                choices=list(range(1, len(batch_files) + 1))
            )
            
            selected_file = batch_files[choice - 1]
            
            # Ask for processing options
            dry_run = Confirm.ask("Perform dry run first?", default=True)
            
            if dry_run:
                # Process in dry run mode
                if not self.context.batch_processor:
                    from .batch_processor import BatchProcessor
                    self.context.batch_processor = BatchProcessor(self.context)
                
                self.context.batch_processor.process_batch_file(str(selected_file), dry_run=True)
                
                # Ask if user wants to proceed with actual processing
                if not Confirm.ask("Proceed with actual processing?"):
                    return
            
            # Process batch
            self.context.batch_processor.process_batch_file(str(selected_file))
            
        except (ValueError, IndexError):
            self.console.print("[red]Invalid choice[/red]")
    
    def _create_batch_configuration(self) -> None:
        """Interactive batch configuration creation."""
        self.console.print("\n[bold]Creating new batch configuration[/bold]\n")
        
        templates = []
        
        while True:
            self.console.print(f"\n[bold]Template {len(templates) + 1}:[/bold]")
            
            # Get template details
            src = Prompt.ask("Source template path")
            if not Path(src).exists():
                self.console.print(f"[red]Warning: File not found: {src}[/red]")
                
            out = Prompt.ask("Output path")
            org = Prompt.ask("Organization (optional)", default="")
            channel = Prompt.ask("Channel (optional)", default="")
            priority = IntPrompt.ask("Priority (1=highest)", default=1)
            
            template_config = {
                "name": f"Template {len(templates) + 1}",
                "src": src,
                "out": out,
                "priority": priority
            }
            
            if org:
                template_config["org"] = org
            if channel:
                template_config["channel"] = channel
                
            templates.append(template_config)
            
            if not Confirm.ask("Add another template?", default=True):
                break
        
        # Get batch settings
        self.console.print("\n[bold]Batch Settings:[/bold]")
        parallel = Confirm.ask("Enable parallel processing?", default=True)
        
        if parallel:
            max_workers = IntPrompt.ask("Maximum workers", default=4)
        else:
            max_workers = 1
        
        # Create batch configuration
        batch_config = {
            "version": "1.0",
            "settings": {
                "parallel": parallel,
                "max_workers": max_workers,
                "checkpoint_interval": 10,
                "retry_failed": True
            },
            "templates": templates
        }
        
        # Save configuration
        config_name = Prompt.ask("Configuration file name", default="batch_config.json")
        if not config_name.endswith(('.json', '.yml', '.yaml')):
            config_name += '.json'
        
        config_path = Path(config_name)
        
        with open(config_path, 'w') as f:
            import json
            json.dump(batch_config, f, indent=2)
        
        self.console.print(f"\n[green]✅ Batch configuration saved: {config_path}[/green]")
        
        # Ask if user wants to run the batch now
        if Confirm.ask("Run batch processing now?", default=True):
            if not self.context.batch_processor:
                from .batch_processor import BatchProcessor
                self.context.batch_processor = BatchProcessor(self.context)
            
            self.context.batch_processor.process_batch_file(str(config_path))
    
    def _view_current_configuration(self) -> None:
        """Display current configuration."""
        config = self.context.config
        
        tree = Tree("StyleStack Configuration")
        
        for section, values in config.items():
            if isinstance(values, dict):
                section_node = tree.add(f"[bold cyan]{section}[/bold cyan]")
                for key, value in values.items():
                    section_node.add(f"{key}: [green]{value}[/green]")
            else:
                tree.add(f"[bold cyan]{section}[/bold cyan]: [green]{values}[/green]")
        
        self.console.print(tree)
    
    def _edit_configuration_settings(self) -> None:
        """Interactive configuration editing."""
        self.console.print("\n[bold]Configuration Settings Editor[/bold]\n")
        
        # Show editable settings
        editable_settings = [
            ("defaults.org", "Default organization"),
            ("defaults.channel", "Default channel"),
            ("defaults.verbose", "Default verbose mode"),
            ("defaults.parallel", "Default parallel processing"),
            ("defaults.max_workers", "Default max workers"),
            ("paths.templates", "Templates directory"),
            ("paths.output", "Output directory")
        ]
        
        for i, (key, description) in enumerate(editable_settings, 1):
            current_value = self.config_manager.get_config_value(key, "Not set")
            self.console.print(f"  [cyan]{i}[/cyan]. {description}: [dim]{current_value}[/dim]")
        
        try:
            choice = IntPrompt.ask(
                "\nSelect setting to edit",
                choices=list(range(1, len(editable_settings) + 1))
            )
            
            key, description = editable_settings[choice - 1]
            current_value = self.config_manager.get_config_value(key, "")
            
            new_value = Prompt.ask(f"New value for {description}", default=str(current_value))
            
            # Convert value to appropriate type
            if key.endswith(('.verbose', '.parallel')):
                new_value = new_value.lower() in ['true', 'yes', '1']
            elif key.endswith('.max_workers'):
                new_value = int(new_value)
            
            self.config_manager.set_config_value(key, new_value)
            self.console.print(f"[green]✅ Updated {description} to: {new_value}[/green]")
            
        except (ValueError, IndexError):
            self.console.print("[red]Invalid choice or value[/red]")
    
    def _create_configuration_template(self) -> None:
        """Create configuration template."""
        template_name = Prompt.ask("Template name")
        description = Prompt.ask("Template description", default="")
        
        # Use current configuration as template
        self.config_manager.save_config_template(template_name, self.context.config, description)
        
        self.console.print(f"[green]✅ Configuration template saved: {template_name}[/green]")
    
    def _reset_configuration(self) -> None:
        """Reset configuration to defaults."""
        if Confirm.ask("Reset all settings to defaults? This cannot be undone.", default=False):
            # Reload with defaults only
            self.context.config = self.config_manager._load_default_config()
            self.console.print("[green]✅ Configuration reset to defaults[/green]")
    
    def _display_interactive_help(self) -> None:
        """Display interactive help."""
        help_content = """
[bold cyan]StyleStack Interactive Mode Help[/bold cyan]

[bold]Navigation:[/bold]
• Use number keys to select menu options
• Press Ctrl+C to exit at any time
• Use Enter to accept default values

[bold]Template Processing:[/bold]
• Processes single templates with corporate branding
• Automatically detects available templates
• Guides through organization and channel selection

[bold]Batch Processing:[/bold]
• Set up multiple templates for bulk processing
• Configure parallel processing options
• Save configurations for reuse

[bold]Configuration:[/bold]
• View current settings and paths
• Edit default values interactively
• Create and manage configuration templates

[bold]Tips:[/bold]
• Use the [bold]--config[/bold] option to load saved configurations
• Set up organization and channel directories for auto-detection
• Use batch processing for large numbers of templates
"""
        
        panel = Panel(help_content.strip(), title="Interactive Help", border_style="blue")
        self.console.print(panel)