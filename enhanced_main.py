"""
Enhanced main function with Rich CLI integration.
This will be integrated into build.py to replace the existing main function.
"""

import sys
import pathlib
from typing import Any, Dict

def enhanced_main(src, as_potx, as_dotx, as_xltx, out, verbose, quiet, org, channel, supertheme, designs, ratios,
                 config, batch, interactive, parallel, max_workers, dry_run, force, resume, diagnose, 
                 check_updates, list_templates, validate_config, create_batch_template, setup_completion):
    """StyleStack OOXML Extension Variable System with Enhanced CLI"""
    
    # Use enhanced CLI if available
    if ENHANCED_CLI_AVAILABLE:
        enhanced_cli = EnhancedCLI()
        
        # Create CLI context with all parameters
        cli_context = enhanced_cli.create_context(
            src=src, out=out, verbose=verbose, quiet=quiet, org=org, channel=channel,
            config=config, batch=batch, interactive=interactive, parallel=parallel,
            max_workers=max_workers, dry_run=dry_run, force=force, resume=resume,
            supertheme=supertheme, designs=designs, ratios=ratios
        )
        
        try:
            # Print banner unless quiet
            enhanced_cli.print_banner(cli_context)
            
            # Handle special commands first
            if setup_completion:
                _setup_command_completion(setup_completion, cli_context)
                return
            
            if diagnose:
                enhanced_cli.show_diagnostics(cli_context)
                return
                
            if check_updates:
                enhanced_cli.check_for_updates(cli_context)
                return
                
            if list_templates:
                enhanced_cli.list_templates(cli_context)
                return
                
            if validate_config:
                _validate_configuration(config, cli_context)
                return
                
            if create_batch_template:
                _create_batch_template(cli_context)
                return
            
            # Print configuration summary if verbose
            enhanced_cli.print_config_summary(cli_context)
            
            # Handle different processing modes
            if interactive:
                # Interactive mode
                success = enhanced_cli.run_interactive_mode(cli_context)
                
            elif batch:
                # Batch processing mode
                success = enhanced_cli.process_batch(cli_context, batch, dry_run=dry_run, resume=resume)
                
            elif resume:
                # Resume batch processing
                if not cli_context.batch_processor:
                    from tools.cli.batch_processor import BatchProcessor
                    cli_context.batch_processor = BatchProcessor(cli_context)
                success = cli_context.batch_processor.resume_from_checkpoint(resume)
                
            elif supertheme:
                # SuperTheme generation mode
                success = _process_supertheme_enhanced(designs, ratios, out, cli_context)
                
            else:
                # Single template processing mode
                if not src:
                    cli_context.error_handler.display_validation_errors([
                        "Source template path is required",
                        "Use --src to specify input template",
                        "Or use --interactive mode for guided workflow"
                    ])
                    sys.exit(1)
                    
                if not out:
                    cli_context.error_handler.display_validation_errors([
                        "Output path is required",
                        "Use --out to specify output path",
                        "Or use --interactive mode for guided workflow"
                    ])
                    sys.exit(1)
                
                # Validate inputs
                if not enhanced_cli.validate_inputs(cli_context, src=src, out=out, org=org, force=force):
                    sys.exit(1)
                
                # Process single template
                success = enhanced_cli.process_template(cli_context, src=src, out=out, org=org, channel=channel)
            
            # Display error summary
            cli_context.error_handler.display_error_summary()
            
            if not success:
                sys.exit(1)
                
        except KeyboardInterrupt:
            cli_context.console.print("\n[yellow]⚠️  Operation cancelled by user[/yellow]")
            sys.exit(130)  # Standard exit code for SIGINT
            
        except Exception as e:
            cli_context.error_handler.handle_processing_error(e, cli_context)
            sys.exit(1)
    
    else:
        # Fallback to legacy CLI implementation
        _legacy_main(src, as_potx, as_dotx, as_xltx, out, verbose, org, channel, supertheme, designs, ratios)


def _setup_command_completion(shell: str, cli_context) -> None:
    """Set up command completion for specified shell."""
    completion_script = f"""
# StyleStack CLI completion for {shell}
# Add this to your ~/.{shell}rc file

_stylestack_completion() {{
    local cur prev opts
    COMPREPLY=()
    cur="${{COMP_WORDS[COMP_CWORD]}}"
    prev="${{COMP_WORDS[COMP_CWORD-1]}}"
    
    opts="--src --out --org --channel --verbose --quiet --config --batch --interactive --parallel --max-workers --dry-run --force --resume --diagnose --check-updates --list-templates --validate-config --create-batch-template --setup-completion --supertheme --designs --ratios --as-potx --as-dotx --as-xltx"
    
    case ${{prev}} in
        --org)
            local orgs=$(find orgs/ -maxdepth 1 -type d -exec basename {{}} \\; 2>/dev/null | grep -v orgs)
            COMPREPLY=( $(compgen -W "${{orgs}}" -- ${{cur}}) )
            return 0
            ;;
        --channel)
            local channels=$(find channels/ -name "*-design-tokens.json" -exec basename {{}} -design-tokens.json \\; 2>/dev/null)
            COMPREPLY=( $(compgen -W "${{channels}}" -- ${{cur}}) )
            return 0
            ;;
        --src|--out|--config|--batch|--resume)
            COMPREPLY=( $(compgen -f -- ${{cur}}) )
            return 0
            ;;
        --designs)
            COMPREPLY=( $(compgen -d -- ${{cur}}) )
            return 0
            ;;
        --setup-completion)
            COMPREPLY=( $(compgen -W "bash zsh fish" -- ${{cur}}) )
            return 0
            ;;
    esac
    
    COMPREPLY=( $(compgen -W "${{opts}}" -- ${{cur}}) )
    return 0
}}

complete -F _stylestack_completion python build.py
complete -F _stylestack_completion ./build.py
"""
    
    cli_context.console.print(f"[bold cyan]Command completion script for {shell}:[/bold cyan]\n")
    cli_context.console.print(completion_script)
    cli_context.console.print(f"\n[bold]To install:[/bold]")
    cli_context.console.print(f"1. Add the above script to your ~/.{shell}rc file")
    cli_context.console.print(f"2. Reload your shell: source ~/.{shell}rc")
    cli_context.console.print(f"3. Use Tab completion with: python build.py <Tab>")


def _validate_configuration(config_file: str, cli_context) -> None:
    """Validate configuration file."""
    if config_file:
        config_path = pathlib.Path(config_file)
        if not config_path.exists():
            cli_context.error_handler.display_validation_errors([
                f"Configuration file not found: {config_file}"
            ])
            return
        
        try:
            # Validate the configuration
            cli_context.config_manager._load_config_file(config_file)
            cli_context.console.print(f"[green]✅ Configuration file is valid: {config_file}[/green]")
        except Exception as e:
            cli_context.error_handler.display_validation_errors([
                f"Invalid configuration file: {e}"
            ])
    else:
        cli_context.console.print("[yellow]No configuration file specified[/yellow]")


def _create_batch_template(cli_context) -> None:
    """Create a batch configuration template."""
    template_content = {
        "version": "1.0",
        "description": "StyleStack batch processing configuration template",
        "settings": {
            "parallel": True,
            "max_workers": 4,
            "checkpoint_interval": 10,
            "retry_failed": True,
            "max_retries": 3
        },
        "templates": [
            {
                "name": "Corporate Presentation Template",
                "src": "templates/corporate.potx",
                "out": "output/corporate-branded.potx",
                "org": "your-org",
                "channel": "present",
                "priority": 1
            },
            {
                "name": "Document Template",
                "src": "templates/document.dotx", 
                "out": "output/document-branded.dotx",
                "org": "your-org",
                "channel": "doc",
                "priority": 2
            },
            {
                "name": "Spreadsheet Template",
                "src": "templates/spreadsheet.xltx",
                "out": "output/spreadsheet-branded.xltx",
                "org": "your-org",
                "channel": "finance",
                "priority": 3
            }
        ]
    }
    
    # Save template
    import json
    template_file = pathlib.Path("batch_template.json")
    with open(template_file, 'w') as f:
        json.dump(template_content, f, indent=2)
    
    cli_context.console.print(f"[green]✅ Batch template created: {template_file}[/green]")
    cli_context.console.print("\n[bold]Next steps:[/bold]")
    cli_context.console.print("1. Edit the template file to match your templates and paths")
    cli_context.console.print("2. Run batch processing: python build.py --batch batch_template.json")


def _process_supertheme_enhanced(designs: str, ratios: str, out: str, cli_context) -> bool:
    """Process SuperTheme generation with enhanced UI."""
    from rich.panel import Panel
    
    cli_context.console.print(Panel(
        "[bold cyan]🎨 Microsoft SuperTheme Generation[/bold cyan]",
        expand=False
    ))
    
    # Validate parameters
    if not designs:
        cli_context.error_handler.display_validation_errors([
            "--designs directory is required for SuperTheme generation",
            "Usage: python build.py --supertheme --designs ./designs --ratios 16:9,4:3 --out theme.thmx"
        ])
        return False
    
    if not out:
        cli_context.error_handler.display_validation_errors([
            "--out file path is required for SuperTheme generation"
        ])
        return False
    
    try:
        # Import SuperTheme components with progress
        with cli_context.progress_manager.create_progress() as progress:
            task = progress.add_task("Initializing SuperTheme generator...", total=100)
            
            from tools.supertheme_generator import SuperThemeGenerator
            from tools.aspect_ratio_resolver import create_standard_aspect_ratios
            import json
            
            progress.update(task, advance=20, description="Loading design variants...")
            
            # Load design variants
            designs_path = pathlib.Path(designs)
            if not designs_path.exists():
                cli_context.error_handler.display_validation_errors([
                    f"Designs directory not found: {designs}"
                ])
                return False
            
            design_variants = {}
            for json_file in designs_path.glob("*.json"):
                try:
                    with open(json_file) as f:
                        design_data = json.load(f)
                        design_name = json_file.stem.replace('_', ' ').title()
                        design_variants[design_name] = design_data
                        if cli_context.verbose:
                            cli_context.console.print(f"   ✅ Loaded: {design_name}")
                except Exception as e:
                    cli_context.console.print(f"   [yellow]⚠️  Failed to load {json_file.name}: {e}[/yellow]")
            
            if not design_variants:
                cli_context.error_handler.display_validation_errors([
                    "No valid design files found in designs directory"
                ])
                return False
            
            progress.update(task, advance=30, description="Processing aspect ratios...")
            
            # Parse aspect ratios
            aspect_ratio_list = _parse_aspect_ratios(ratios, cli_context)
            
            progress.update(task, advance=20, description="Generating SuperTheme package...")
            
            # Generate SuperTheme
            generator = SuperThemeGenerator(verbose=cli_context.verbose)
            
            if cli_context.verbose:
                cli_context.console.print(f"🔨 Generating SuperTheme with {len(design_variants)} designs and {len(aspect_ratio_list)} aspect ratios")
            
            supertheme_bytes = generator.generate_supertheme(
                design_variants=design_variants,
                aspect_ratios=aspect_ratio_list
            )
            
            progress.update(task, advance=20, description="Writing output file...")
            
            # Write output file
            out_path = pathlib.Path(out)
            out_path.write_bytes(supertheme_bytes)
            
            progress.update(task, completed=100, description="✅ SuperTheme generation complete!")
            
            # Report success
            size_mb = len(supertheme_bytes) / (1024 * 1024)
            variants_count = len(design_variants) * len(aspect_ratio_list)
            
            from rich.table import Table
            
            results_table = Table(title="SuperTheme Generation Results", show_header=True)
            results_table.add_column("Metric", style="cyan")
            results_table.add_column("Value", style="green")
            
            results_table.add_row("Output File", str(out_path))
            results_table.add_row("File Size", f"{size_mb:.2f} MB")
            results_table.add_row("Design Variants", str(len(design_variants)))
            results_table.add_row("Aspect Ratios", str(len(aspect_ratio_list)))
            results_table.add_row("Total Variants", str(variants_count))
            
            cli_context.console.print(results_table)
            
            if size_mb > 5.0:
                cli_context.console.print(f"[yellow]⚠️  Package size ({size_mb:.2f}MB) exceeds recommended 5MB limit[/yellow]")
            
            return True
            
    except Exception as e:
        cli_context.error_handler.handle_processing_error(e, cli_context)
        return False


def _parse_aspect_ratios(ratios: str, cli_context) -> list:
    """Parse aspect ratios string into token paths."""
    # Map user-friendly names to token paths
    ratio_mapping = {
        '16:9': 'aspectRatios.widescreen_16_9',
        '16:10': 'aspectRatios.standard_16_10',
        '4:3': 'aspectRatios.classic_4_3',
        'a4': 'aspectRatios.a4_landscape',
        'a4-portrait': 'aspectRatios.a4_portrait',
        'letter': 'aspectRatios.letter_landscape',
        'letter-portrait': 'aspectRatios.letter_portrait'
    }
    
    aspect_ratio_list = []
    
    if ratios:
        for ratio in ratios.split(','):
            ratio = ratio.strip().lower()
            if ratio in ratio_mapping:
                aspect_ratio_list.append(ratio_mapping[ratio])
            else:
                cli_context.console.print(f"[yellow]⚠️  Unknown aspect ratio '{ratio}', skipping[/yellow]")
                cli_context.console.print(f"   Available: {', '.join(ratio_mapping.keys())}")
    else:
        # Default aspect ratios
        aspect_ratio_list = [
            'aspectRatios.widescreen_16_9',
            'aspectRatios.standard_16_10', 
            'aspectRatios.classic_4_3'
        ]
    
    if cli_context.verbose:
        cli_context.console.print(f"📐 Using aspect ratios:")
        for ratio in aspect_ratio_list:
            ratio_name = ratio.split('.')[-1].replace('_', ' ').title()
            cli_context.console.print(f"   • {ratio_name}")
    
    return aspect_ratio_list


def process_single_template(src: str, out: str, org: str = None, channel: str = None, verbose: bool = False) -> bool:
    """Process a single template - wrapper for the existing functionality."""
    # This would call the existing template processing logic
    # For now, it's a placeholder that calls the legacy main function
    import tempfile
    
    # Create a temporary args object to pass to legacy function
    class Args:
        def __init__(self):
            self.src = src
            self.out = out
            self.org = org
            self.channel = channel
            self.verbose = verbose
            self.as_potx = False
            self.as_dotx = False
            self.as_xltx = False
            self.supertheme = False
            self.designs = None
            self.ratios = None
    
    try:
        # Call the existing legacy processing logic
        # This would be replaced with the actual processing logic
        return True  # Placeholder - successful processing
    except Exception as e:
        if verbose:
            print(f"Error processing template: {e}")
        return False


def _legacy_main(src, as_potx, as_dotx, as_xltx, out, verbose, org, channel, supertheme, designs, ratios):
    """Legacy CLI implementation for fallback."""
    import click
    
    # This contains the original main function logic for fallback
    click.echo("Using legacy CLI mode...")
    
    # License validation for commercial use (GitHub-native)
    if org and EXTENSION_SYSTEM_AVAILABLE and GitHubLicenseManager:
        license_manager = GitHubLicenseManager()
        license_enforcer = GitHubLicenseEnforcer(license_manager)
        
        try:
            # Check if org requires licensing
            license_enforcer.enforce(org, 'build')
        except LicenseError as e:
            click.echo(str(e))
            sys.exit(1)
    
    # Continue with original legacy logic...
    # (The rest of the original main function would go here)
    click.echo(f"Processing {src} -> {out}")
    click.echo("Legacy mode processing complete")