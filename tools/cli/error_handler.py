"""
Enhanced error handling system with Rich formatting and actionable suggestions.
"""

import sys
import traceback
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.syntax import Syntax
from rich import print as rprint


class StyleStackCliError(Exception):
    """Base CLI error with Rich formatting support."""
    
    def __init__(self, 
                 message: str,
                 error_code: str = "CLI001",
                 suggestions: Optional[List[str]] = None,
                 context: Optional[Dict[str, Any]] = None,
                 fix_commands: Optional[List[str]] = None):
        self.message = message
        self.error_code = error_code
        self.suggestions = suggestions or []
        self.context = context or {}
        self.fix_commands = fix_commands or []
        super().__init__(message)


class StyleStackFileNotFoundError(StyleStackCliError):
    """File not found error with helpful suggestions."""
    
    def __init__(self, file_path: str, **kwargs):
        suggestions = kwargs.get('suggestions', [])
        if not suggestions:
            suggestions = [
                f"Check if the file path is correct: {file_path}",
                "Ensure the file exists and is accessible",
                "Try using an absolute path instead of relative path"
            ]
        
        super().__init__(
            message=f"File not found: {file_path}",
            error_code="CLI002",
            suggestions=suggestions,
            **kwargs
        )


class StyleStackValidationError(StyleStackCliError):
    """Validation error with specific field information."""
    
    def __init__(self, field: str, value: Any, valid_options: Optional[List[str]] = None, **kwargs):
        message = f"Invalid value for {field}: {value}"
        suggestions = kwargs.get('suggestions', [])
        
        if valid_options:
            message += f". Valid options: {', '.join(valid_options)}"
            suggestions.append(f"Use one of: {', '.join(valid_options)}")
        
        super().__init__(
            message=message,
            error_code="CLI003",
            suggestions=suggestions,
            context={'field': field, 'value': value, 'valid_options': valid_options},
            **kwargs
        )


class StyleStackPermissionError(StyleStackCliError):
    """Permission error with fix suggestions."""
    
    def __init__(self, file_path: str, **kwargs):
        fix_commands = [
            f"chmod +rw {file_path}",
            "sudo chown $USER:$USER " + str(file_path)
        ]
        
        suggestions = [
            "Check file and directory permissions",
            "Ensure you have write access to the output directory",
            "Run with appropriate permissions if necessary"
        ]
        
        super().__init__(
            message=f"Permission denied: {file_path}",
            error_code="CLI004",
            suggestions=suggestions,
            fix_commands=fix_commands,
            **kwargs
        )


class EnhancedErrorHandler:
    """Enhanced error handler with Rich UI and actionable suggestions."""
    
    def __init__(self, console: Console):
        """Initialize error handler with Rich console."""
        self.console = console
        self.error_count = 0
        self.warning_count = 0
        self.logger = logging.getLogger(__name__)
    
    def handle_processing_error(self, error: Exception, context: Any) -> None:
        """Handle processing errors with context-aware suggestions."""
        self.error_count += 1
        
        if isinstance(error, StyleStackCliError):
            self._display_styled_error(error)
        else:
            # Convert generic exceptions to styled errors
            styled_error = self._convert_generic_error(error, context)
            self._display_styled_error(styled_error)
    
    def display_validation_errors(self, errors: List[str]) -> None:
        """Display validation errors in a formatted panel."""
        if not errors:
            return
        
        error_text = Text()
        for i, error in enumerate(errors, 1):
            if error.startswith('  💡'):
                # Suggestion line
                error_text.append(f"{error}\n", style="dim cyan")
            else:
                # Regular error line
                error_text.append(f"{i}. {error}\n", style="red")
        
        panel = Panel(
            error_text.rstrip(),
            title="❌ Validation Errors",
            border_style="red",
            expand=False
        )
        
        self.console.print(panel)
        self.error_count += len([e for e in errors if not e.startswith('  💡')])
    
    def display_warnings(self, warnings: List[str]) -> None:
        """Display warnings in a formatted panel."""
        if not warnings:
            return
        
        warning_text = Text()
        for i, warning in enumerate(warnings, 1):
            warning_text.append(f"{i}. {warning}\n", style="yellow")
        
        panel = Panel(
            warning_text.rstrip(),
            title="⚠️  Warnings",
            border_style="yellow",
            expand=False
        )
        
        self.console.print(panel)
        self.warning_count += len(warnings)
    
    def _display_styled_error(self, error: StyleStackCliError) -> None:
        """Display a styled error with suggestions and fix commands."""
        # Create error header
        header = Text()
        header.append("❌ Error ", style="bold red")
        header.append(f"[{error.error_code}]", style="dim red")
        
        # Create error content
        content = Text()
        content.append(f"{error.message}\n\n", style="red")
        
        # Add context information if available
        if error.context:
            content.append("Context:\n", style="bold")
            for key, value in error.context.items():
                content.append(f"  {key}: {value}\n", style="dim")
            content.append("\n")
        
        # Add suggestions
        if error.suggestions:
            content.append("💡 Suggestions:\n", style="bold cyan")
            for suggestion in error.suggestions:
                content.append(f"  • {suggestion}\n", style="cyan")
            content.append("\n")
        
        # Add fix commands
        if error.fix_commands:
            content.append("🔧 Possible fixes:\n", style="bold green")
            for command in error.fix_commands:
                content.append(f"  $ {command}\n", style="green")
        
        # Display the error panel
        panel = Panel(
            content.rstrip(),
            title=header,
            border_style="red",
            expand=False
        )
        
        self.console.print(panel)
        
        # Log the error for debugging
        self.logger.error(f"[{error.error_code}] {error.message}", extra=error.context)
    
    def _convert_generic_error(self, error: Exception, context: Any) -> StyleStackCliError:
        """Convert generic exceptions to styled CLI errors."""
        error_type = type(error).__name__
        error_message = str(error)
        
        # File-related errors
        if isinstance(error, FileNotFoundError):
            return StyleStackFileNotFoundError(error.filename or "Unknown file")
        
        if isinstance(error, PermissionError):
            return StyleStackPermissionError(error.filename or "Unknown file")
        
        # Import errors
        if isinstance(error, ImportError):
            return StyleStackCliError(
                message=f"Missing dependency: {error_message}",
                error_code="CLI005",
                suggestions=[
                    "Install missing dependencies with: pip install -r requirements.txt",
                    "Check your Python environment setup",
                    "Verify all required packages are installed"
                ],
                fix_commands=["pip install -r requirements.txt"]
            )
        
        # JSON/YAML parsing errors
        if "JSON" in error_message or "YAML" in error_message:
            return StyleStackCliError(
                message=f"Configuration file parsing error: {error_message}",
                error_code="CLI006",
                suggestions=[
                    "Check configuration file syntax",
                    "Validate JSON/YAML format using an online validator",
                    "Look for missing commas, quotes, or brackets"
                ],
                context={'error_type': error_type}
            )
        
        # Generic error conversion
        suggestions = []
        fix_commands = []
        
        # Add context-aware suggestions
        if hasattr(context, 'verbose') and context.verbose:
            suggestions.append("Run with --verbose for more detailed error information")
        
        if "template" in error_message.lower():
            suggestions.extend([
                "Verify the template file is not corrupted",
                "Try with a different template file",
                "Check template file permissions"
            ])
        
        if "network" in error_message.lower() or "connection" in error_message.lower():
            suggestions.extend([
                "Check your internet connection",
                "Verify proxy settings if applicable",
                "Try again in a few minutes"
            ])
        
        return StyleStackCliError(
            message=f"{error_type}: {error_message}",
            error_code="CLI999",
            suggestions=suggestions,
            fix_commands=fix_commands,
            context={
                'error_type': error_type,
                'traceback': traceback.format_exc()
            }
        )
    
    def display_error_summary(self) -> None:
        """Display summary of errors and warnings encountered."""
        if self.error_count == 0 and self.warning_count == 0:
            self.console.print("✅ No errors or warnings", style="green")
            return
        
        summary = Text()
        
        if self.error_count > 0:
            summary.append(f"❌ {self.error_count} error(s)", style="red")
        
        if self.warning_count > 0:
            if self.error_count > 0:
                summary.append(" • ", style="dim")
            summary.append(f"⚠️  {self.warning_count} warning(s)", style="yellow")
        
        panel = Panel(
            summary,
            title="Summary",
            border_style="blue",
            expand=False
        )
        
        self.console.print(panel)
    
    def create_error_report(self) -> Dict[str, Any]:
        """Create detailed error report for debugging."""
        return {
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'python_version': sys.version,
            'platform': sys.platform,
            'working_directory': str(Path.cwd())
        }
    
    def suggest_common_fixes(self, error_type: str) -> List[str]:
        """Get common fixes for specific error types."""
        common_fixes = {
            'file_not_found': [
                "Check if the file path is correct",
                "Ensure the file exists and is accessible", 
                "Use absolute path instead of relative path",
                "Check current working directory with 'pwd' command"
            ],
            'permission_denied': [
                "Check file and directory permissions",
                "Ensure write access to output directory",
                "Run with appropriate user permissions",
                "Check if file is being used by another process"
            ],
            'invalid_template': [
                "Verify template file is not corrupted",
                "Try with a known good template file",
                "Check template file format and extension",
                "Ensure template contains valid OOXML structure"
            ],
            'configuration_error': [
                "Validate configuration file syntax",
                "Check for required configuration fields",
                "Verify file paths in configuration",
                "Use configuration validation command"
            ],
            'network_error': [
                "Check internet connection",
                "Verify proxy settings",
                "Check firewall settings",
                "Retry operation after some time"
            ]
        }
        
        return common_fixes.get(error_type, [
            "Check the error message for specific details",
            "Run with --verbose for more information",
            "Check the documentation for troubleshooting",
            "Report issue if problem persists"
        ])
    
    def display_troubleshooting_guide(self) -> None:
        """Display general troubleshooting guide."""
        guide_content = """
[bold cyan]StyleStack Troubleshooting Guide[/bold cyan]

[bold]Common Issues and Solutions:[/bold]

[dim]1. File Not Found Errors:[/dim]
   • Check file paths are correct (use absolute paths)
   • Ensure files exist and are accessible
   • Verify current working directory

[dim]2. Permission Errors:[/dim]
   • Check file and directory permissions
   • Ensure write access to output directories
   • Run with appropriate user permissions

[dim]3. Template Processing Errors:[/dim]
   • Verify template files are not corrupted
   • Check template file formats and extensions
   • Try with known good template files

[dim]4. Configuration Errors:[/dim]
   • Validate configuration file syntax
   • Check for required configuration fields
   • Use configuration validation commands

[bold]Getting Help:[/bold]
   • Run with --verbose for detailed output
   • Use --diagnose for system diagnostics
   • Check documentation at https://docs.stylestack.com
   • Report issues at https://github.com/stylestack/stylestack/issues
"""
        
        panel = Panel(
            guide_content.strip(),
            title="🔧 Troubleshooting Guide",
            border_style="blue"
        )
        
        self.console.print(panel)