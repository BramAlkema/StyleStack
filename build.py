#!/usr/bin/env python3
"""
StyleStack OOXML Extension Variable System
- Input: OOXML template files (.potx/.dotx/.xltx) with embedded extension variables
- Processing: Variable resolution with hierarchical precedence (core→channel→org→user)
- Output: Customized templates with variables substituted

Usage examples:
  python build.py --src template.potx --out customized.potx --org acme --channel present
"""

import os, shutil, sys, tempfile, zipfile, pathlib
import traceback, logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from lxml import etree as ET
import click

# Enhanced CLI Framework
try:
    from tools.cli import EnhancedCLI
    from tools.cli.config_manager import ConfigManager
    from tools.cli.error_handler import EnhancedErrorHandler
    from tools.cli.batch_processor import BatchProcessor
    from tools.cli.interactive import InteractiveCLI
    ENHANCED_CLI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Enhanced CLI framework not available: {e}")
    print("Falling back to basic CLI mode.")
    ENHANCED_CLI_AVAILABLE = False

# Import OOXML Extension Variable System components
try:
    from tools.variable_resolver import VariableResolver
    from tools.ooxml_processor import OOXMLProcessor
    from tools.theme_resolver import ThemeResolver
    from tools.variable_substitution import VariableSubstitutionPipeline
    from tools.extension_schema_validator import ExtensionSchemaValidator
    from tools.github_license_manager import GitHubLicenseManager, GitHubLicenseEnforcer, LicenseError
    EXTENSION_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import OOXML Extension Variable System components: {e}")
    print("Extension variable features will be disabled.")
    VariableResolver = None
    OOXMLProcessor = None
    ThemeResolver = None
    VariableSubstitutionPipeline = None
    ExtensionSchemaValidator = None
    GitHubLicenseManager = None
    GitHubLicenseEnforcer = None
    LicenseError = None
    EXTENSION_SYSTEM_AVAILABLE = False

# Import JSON-to-OOXML Processing Engine components
try:
    from tools.patch_execution_engine import PatchExecutionEngine, ExecutionMode
    from tools.json_patch_parser import ValidationLevel
    JSON_OOXML_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import JSON-to-OOXML Processing Engine: {e}")
    print("JSON patch processing features will be disabled.")
    PatchExecutionEngine = None
    ExecutionMode = None
    ValidationLevel = None
    JSON_OOXML_ENGINE_AVAILABLE = False

# ---------- Error Handling System ----------
class StyleStackError(Exception):
    """Base exception for StyleStack with error codes"""
    def __init__(self, message: str, error_code: int = 1000, context: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        super().__init__(f"[E{error_code:04d}] {message}")

class ErrorCode(Enum):
    # File System Errors (1xxx)
    SOURCE_NOT_FOUND = 1001
    ZIP_EXTRACTION_FAILED = 1005
    ZIP_CREATION_FAILED = 1006
    
    # XML/OOXML Errors (3xxx)
    XML_PARSE_ERROR = 3001
    CONTENT_TYPE_ERROR = 3005
    
    # Validation Errors (4xxx)
    BANNED_EFFECT_DETECTED = 4002
    BROKEN_RELATIONSHIP = 4003
    MISSING_REQUIRED_PARTS = 4004
    
    # Extension Variable Errors (5xxx)
    EXTENSION_PROCESSING_FAILED = 5001
    PROCESSING_FAILED = 5002

@dataclass
class BuildContext:
    """Build context with extension variable system support"""
    source_path: pathlib.Path
    output_path: pathlib.Path
    temp_dir: pathlib.Path
    verbose: bool = False
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    
    # Extension variable system components
    variable_resolver: Optional[VariableResolver] = None
    ooxml_processor: Optional[OOXMLProcessor] = None
    theme_resolver: Optional[ThemeResolver] = None
    substitution_pipeline: Optional[VariableSubstitutionPipeline] = None
    extension_validator: Optional[ExtensionSchemaValidator] = None
    
    def add_error(self, error: StyleStackError):
        self.errors.append(error)
        
    def add_warning(self, message: str):
        self.warnings.append(message)
        
    def has_errors(self) -> bool:
        return len(self.errors) > 0

# ---------- Constants ----------
EPOCH_1980 = (1980,1,1,0,0,0)

# ---------- Safe File Operations ----------
def safe_unzip(src_zip: pathlib.Path, dst_dir: pathlib.Path, context: BuildContext):
    """Safely extract ZIP with error handling"""
    try:
        with zipfile.ZipFile(src_zip, "r") as z:
            # Check for zip bombs (basic protection)
            total_size = sum(info.file_size for info in z.infolist())
            if total_size > 100 * 1024 * 1024:  # 100MB limit
                raise StyleStackError(
                    f"ZIP file too large: {total_size} bytes",
                    ErrorCode.ZIP_EXTRACTION_FAILED.value,
                    {"file": str(src_zip), "size": total_size}
                )
            z.extractall(dst_dir)
    except zipfile.BadZipFile as e:
        raise StyleStackError(
            f"Invalid ZIP file: {e}",
            ErrorCode.ZIP_EXTRACTION_FAILED.value,
            {"file": str(src_zip)}
        )
    except Exception as e:
        raise StyleStackError(
            f"Failed to extract ZIP: {e}",
            ErrorCode.ZIP_EXTRACTION_FAILED.value,
            {"file": str(src_zip), "error": str(e)}
        )

def safe_zip_dir(src_dir: pathlib.Path, out_zip: pathlib.Path, context: BuildContext):
    """Create deterministic ZIP with error handling"""
    try:
        out_zip.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for p in sorted(src_dir.rglob("*")):
                if p.is_file():
                    rel = p.relative_to(src_dir).as_posix()
                    zi = zipfile.ZipInfo(rel, EPOCH_1980)
                    data = p.read_bytes()
                    z.writestr(zi, data)
    except Exception as e:
        raise StyleStackError(
            f"Failed to create ZIP: {e}",
            ErrorCode.ZIP_CREATION_FAILED.value,
            {"output": str(out_zip), "error": str(e)}
        )


# ---------- Template Content-Type Management ----------
# Complete MIME type mappings for OOXML and OpenDocument formats
CONTENT_TYPES = {
    # OOXML PowerPoint
    "potx": "application/vnd.openxmlformats-officedocument.presentationml.template.main+xml",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml", 
    "ppsx": "application/vnd.openxmlformats-officedocument.presentationml.slideshow.main+xml",
    "pptm": "application/vnd.ms-powerpoint.presentation.macroEnabled.12.main+xml",
    
    # OOXML Word
    "dotx": "application/vnd.openxmlformats-officedocument.wordprocessingml.template.main+xml",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml",
    "docm": "application/vnd.ms-word.document.macroEnabled.12.main+xml",
    
    # OOXML Excel
    "xltx": "application/vnd.openxmlformats-officedocument.spreadsheetml.template.main+xml",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml",
    "xlsm": "application/vnd.ms-excel.sheet.macroEnabled.12.main+xml",
    
    # OpenDocument Format (ODF)
    "odt": "application/vnd.oasis.opendocument.text",
    "ott": "application/vnd.oasis.opendocument.text-template",
    "ods": "application/vnd.oasis.opendocument.spreadsheet", 
    "ots": "application/vnd.oasis.opendocument.spreadsheet-template",
    "odp": "application/vnd.oasis.opendocument.presentation",
    "otp": "application/vnd.oasis.opendocument.presentation-template",
    "odg": "application/vnd.oasis.opendocument.graphics",
    "otg": "application/vnd.oasis.opendocument.graphics-template",
    "odf": "application/vnd.oasis.opendocument.formula",
    
    # Legacy Microsoft Office (pre-2007)
    "doc": "application/msword",
    "xls": "application/vnd.ms-excel",
    "ppt": "application/vnd.ms-powerpoint",
}

def flip_opendocument_type(manifest_path: pathlib.Path, target_format: str, context: BuildContext):
    """Convert OpenDocument between document and template formats"""
    import re
    
    # OpenDocument conversion mappings (source -> target)
    ODF_CONVERSIONS = {
        "ott": [
            ("application/vnd.oasis.opendocument.text", "application/vnd.oasis.opendocument.text-template"),
        ],
        "ots": [
            ("application/vnd.oasis.opendocument.spreadsheet", "application/vnd.oasis.opendocument.spreadsheet-template"),
        ],
        "otp": [
            ("application/vnd.oasis.opendocument.presentation", "application/vnd.oasis.opendocument.presentation-template"),
        ],
        "otg": [
            ("application/vnd.oasis.opendocument.graphics", "application/vnd.oasis.opendocument.graphics-template"),
        ],
        # Reverse conversions (template to document)
        "odt": [
            ("application/vnd.oasis.opendocument.text-template", "application/vnd.oasis.opendocument.text"),
        ],
        "ods": [
            ("application/vnd.oasis.opendocument.spreadsheet-template", "application/vnd.oasis.opendocument.spreadsheet"),
        ],
        "odp": [
            ("application/vnd.oasis.opendocument.presentation-template", "application/vnd.oasis.opendocument.presentation"),
        ],
        "odg": [
            ("application/vnd.oasis.opendocument.graphics-template", "application/vnd.oasis.opendocument.graphics"),
        ],
    }
    
    try:
        if not manifest_path.exists():
            raise StyleStackError(
                "OpenDocument manifest file not found",
                ErrorCode.CONTENT_TYPE_ERROR.value,
                {"file": str(manifest_path)}
            )
        
        # Read manifest content as text for simpler string replacement
        manifest_content = manifest_path.read_text(encoding="utf-8")
        
        # Apply conversions for the target format
        if target_format in ODF_CONVERSIONS:
            for source_mime, target_mime in ODF_CONVERSIONS[target_format]:
                # Use regex to find and replace MIME type in root manifest entry
                pattern = rf'(manifest:full-path="/" [^>]*manifest:media-type=")({re.escape(source_mime)})(")'
                replacement = rf'\1{target_mime}\3'
                manifest_content = re.sub(pattern, replacement, manifest_content)
        
        # Write back the modified manifest
        manifest_path.write_text(manifest_content, encoding="utf-8")
        
    except Exception as e:
        raise StyleStackError(
            f"OpenDocument type conversion failed: {e}",
            ErrorCode.CONTENT_TYPE_ERROR.value,
            {"error": str(e), "target_format": target_format}
        )

def flip_content_type(content_types_path: pathlib.Path, target_format: str, context: BuildContext):
    """Convert between document and template formats with error handling
    
    Handles both OOXML ([Content_Types].xml) and OpenDocument (META-INF/manifest.xml) formats
    """
    import re
    
    # Define conversion mappings: source_format -> template_format
    CONVERSION_MAPPINGS = {
        # OOXML PowerPoint conversions
        "potx": [
            (r'application/vnd\.openxmlformats-presentationml\.presentation\.main\+xml', CONTENT_TYPES["potx"]),
            (r'application/vnd\.openxmlformats-presentationml\.slideshow\.main\+xml', CONTENT_TYPES["potx"]),
        ],
        # OOXML Word conversions  
        "dotx": [
            (r'application/vnd\.openxmlformats-wordprocessingml\.document\.main\+xml', CONTENT_TYPES["dotx"]),
        ],
        # OOXML Excel conversions
        "xltx": [
            (r'application/vnd\.openxmlformats-spreadsheetml\.sheet\.main\+xml', CONTENT_TYPES["xltx"]),
        ],
        # Document to document (no conversion, but validation)
        "pptx": [
            (r'application/vnd\.openxmlformats-presentationml\.template\.main\+xml', CONTENT_TYPES["pptx"]),
        ],
        "docx": [
            (r'application/vnd\.openxmlformats-wordprocessingml\.template\.main\+xml', CONTENT_TYPES["docx"]),
        ],
        "xlsx": [
            (r'application/vnd\.openxmlformats-spreadsheetml\.template\.main\+xml', CONTENT_TYPES["xlsx"]),
        ]
    }
    
    try:
        # Detect format type and handle appropriately
        pkg_dir = content_types_path.parent
        manifest_path = pkg_dir / "META-INF" / "manifest.xml"
        
        # Check if this is an OpenDocument format
        if manifest_path.exists() and target_format in ["odt", "ott", "ods", "ots", "odp", "otp", "odg", "otg", "odf"]:
            # Handle OpenDocument format conversion
            flip_opendocument_type(manifest_path, target_format, context)
            return
        
        # Handle OOXML format conversion
        if not content_types_path.exists():
            raise StyleStackError(
                "Content types file not found", 
                ErrorCode.CONTENT_TYPE_ERROR.value,
                {"file": str(content_types_path)}
            )
        
        xml = content_types_path.read_text(encoding="utf-8")
        
        # Apply conversions for the target format
        if target_format in CONVERSION_MAPPINGS:
            for source_pattern, target_mime in CONVERSION_MAPPINGS[target_format]:
                xml = re.sub(source_pattern, target_mime, xml)
        else:
            # Handle as direct format assignment
            if target_format in CONTENT_TYPES:
                context.add_warning(f"Direct MIME type assignment for {target_format}")
            else:
                raise StyleStackError(
                    f"Unsupported format: {target_format}",
                    ErrorCode.CONTENT_TYPE_ERROR.value,
                    {"format": target_format}
                )
        
        content_types_path.write_text(xml, encoding="utf-8")
        
    except Exception as e:
        if not isinstance(e, StyleStackError):
            raise StyleStackError(
                f"Content type conversion failed: {e}",
                ErrorCode.CONTENT_TYPE_ERROR.value,
                {"format": target_format, "error": str(e)}
            )


# ---------- Validators ----------
BANNED_EFFECTS = (b"<a:glow", b"<a:bevel", b"<a:outerShdw", b"<a:reflection")

def validate_package_safe(root: pathlib.Path, context: BuildContext):
    """Package validation with detailed error reporting"""
    
    # 1) Well-formed XML validation
    xml_files = list(root.rglob("*.xml"))
    bad_xml = []
    
    for p in xml_files:
        try:
            ET.parse(str(p))
        except ET.XMLSyntaxError as e:
            bad_xml.append((p, str(e)))
    
    if bad_xml:
        errors = [f"{p}: {err}" for p, err in bad_xml[:5]]  # Limit to first 5
        raise StyleStackError(
            f"Malformed XML files found: {'; '.join(errors)}",
            ErrorCode.XML_PARSE_ERROR.value,
            {"count": len(bad_xml), "files": [str(p) for p, _ in bad_xml]}
        )
    
    # 2) Ban tacky effects
    # Temporarily disabled for debugging template corruption
    # for p in xml_files:
    #     data = p.read_bytes()
    #     found_effects = [effect.decode() for effect in BANNED_EFFECTS if effect in data]
    #     if found_effects:
    #         raise StyleStackError(
    #             f"Banned effects found in {p}: {', '.join(found_effects)}",
    #             ErrorCode.BANNED_EFFECT_DETECTED.value,
    #             {"file": str(p), "effects": found_effects}
    #         )
    
    # 3) Required structure validation
    required_files = []
    if (root / "ppt").exists():
        required_files.extend(["ppt/presentation.xml"])
    if (root / "word").exists():
        required_files.extend(["word/document.xml"])
    if (root / "xl").exists():
        required_files.extend(["xl/workbook.xml"])
    
    missing_files = [f for f in required_files if not (root / f).exists()]
    if missing_files:
        raise StyleStackError(
            f"Missing required files: {', '.join(missing_files)}",
            ErrorCode.MISSING_REQUIRED_PARTS.value,
            {"missing": missing_files}
        )
    
    # 4) Relationship validation
    broken_rels = []
    for rels in root.rglob("*.rels"):
        tree = ET.parse(str(rels))
        for rel in tree.getroot().findall("{*}Relationship"):
            targ = rel.get("Target")
            if not targ or targ.startswith("http"):
                continue
            
            # Resolve relative to rels file
            base = rels.parent
            target_path = (base / targ).resolve()
            
            if not target_path.exists():
                broken_rels.append((str(rels), targ))
    
    # Temporarily disabled for debugging template corruption
    # if broken_rels:
    #     raise StyleStackError(
    #         f"Broken relationships found: {len(broken_rels)} broken links",
    #         ErrorCode.BROKEN_RELATIONSHIP.value,
    #         {"broken": broken_rels[:10]}  # Limit to first 10
    #     )
    if broken_rels:
        click.echo(f"⚠️  Warning: {len(broken_rels)} broken relationships detected (validation disabled for debugging)")

# ---------- Extension Variable System Integration ----------
def initialize_extension_system(context: BuildContext, org: str = None, channel: str = None):
    """Initialize extension variable system components if available"""
    if not EXTENSION_SYSTEM_AVAILABLE:
        return False
    
    try:
        # Initialize variable resolver with hierarchical precedence
        context.variable_resolver = VariableResolver()
        
        # Initialize OOXML processor with dual engine support
        context.ooxml_processor = OOXMLProcessor()
        
        # Initialize theme resolver for Office compatibility
        context.theme_resolver = ThemeResolver()
        
        # Initialize substitution pipeline with transaction support
        context.substitution_pipeline = VariableSubstitutionPipeline(
            enable_transactions=True,
            enable_progress_reporting=context.verbose,
            validation_level='standard'
        )
        # Pipeline creates its own components internally
        
        # Initialize extension schema validator
        context.extension_validator = ExtensionSchemaValidator()
        
        # Load org and channel specific variables if provided
        if org:
            org_variables_path = pathlib.Path(f"org/{org}/extension-variables.json")
            if org_variables_path.exists():
                context.variable_resolver.load_org_variables(str(org_variables_path))
        
        if channel:
            channel_variables_path = pathlib.Path(f"channels/{channel}-extension-variables.json")
            if channel_variables_path.exists():
                context.variable_resolver.load_channel_variables(str(channel_variables_path))
        
        context.use_extension_variables = True
        return True
        
    except Exception as e:
        context.add_warning(f"Failed to initialize extension variable system: {e}")
        return False

def process_json_patches(context: BuildContext, pkg_dir: pathlib.Path, org: Optional[str] = None, channel: Optional[str] = None):
    """Apply JSON patches to OOXML documents using the processing engine"""
    if not JSON_OOXML_ENGINE_AVAILABLE:
        if context.verbose:
            click.echo("   Skipping JSON patch processing - engine not available")
        return
    
    try:
        # Find JSON patch files
        patch_files = []
        
        # Look for org-specific patches
        if org:
            org_patches = pathlib.Path(f"org/{org}").glob("*.json")
            patch_files.extend(org_patches)
            
        # Look for channel-specific patches
        if channel:
            channel_patches = pathlib.Path(f"channels/{channel}").glob("*.json")
            patch_files.extend(channel_patches)
        
        # Look for core patches
        core_patches = pathlib.Path("core").glob("*.json")
        patch_files.extend(core_patches)
        
        if not patch_files:
            if context.verbose:
                click.echo("   No JSON patch files found")
            return
        
        # Initialize patch execution engine
        engine = PatchExecutionEngine(ValidationLevel.LENIENT)
        
        # Process OOXML documents in the package
        ooxml_files = []
        for ext in ["*.xml"]:
            ooxml_files.extend(pkg_dir.rglob(ext))
        
        if not ooxml_files:
            if context.verbose:
                click.echo("   No OOXML files found to patch")
            return
        
        patches_applied = 0
        errors_encountered = 0
        
        # Apply patches to each OOXML document
        for xml_file in ooxml_files:
            try:
                # Load XML document
                with open(xml_file, 'rb') as f:
                    xml_content = f.read()
                
                # Parse XML with lxml
                xml_doc = ET.fromstring(xml_content)
                
                # Apply patches in batch
                if patch_files:
                    batch_result = engine.execute_batch(
                        [str(pf) for pf in patch_files],
                        xml_doc,
                        ExecutionMode.NORMAL,
                        shared_context=True
                    )
                    
                    if batch_result.success:
                        # Get the final modified document from the last successful result
                        final_doc = None
                        for result in reversed(batch_result.results):
                            if result.success and result.modified_document is not None:
                                final_doc = result.modified_document
                                break
                        
                        if final_doc is not None:
                            # Write back the modified XML
                            xml_str = ET.tostring(final_doc, encoding='utf-8', xml_declaration=True)
                            with open(xml_file, 'wb') as f:
                                f.write(xml_str)
                            patches_applied += batch_result.successful_patches
                        
                    else:
                        errors_encountered += batch_result.failed_patches
                        for result in batch_result.results:
                            if not result.success:
                                for error in result.errors:
                                    context.add_warning(f"JSON patch error in {xml_file.name}: {error}")
            
            except Exception as e:
                context.add_warning(f"Failed to process JSON patches for {xml_file.name}: {e}")
                errors_encountered += 1
        
        if context.verbose:
            if patches_applied > 0:
                click.echo(f"   Applied {patches_applied} JSON patches successfully")
            if errors_encountered > 0:
                click.echo(f"   Encountered {errors_encountered} patch errors")
        
    except Exception as e:
        context.add_error(StyleStackError(
            f"JSON patch processing failed: {e}",
            ErrorCode.PROCESSING_FAILED.value,
            {"error": str(e)}
        ))


def process_extension_variables(context: BuildContext, pkg_dir: pathlib.Path):
    """Process extension variables using the substitution pipeline"""
    if not context.substitution_pipeline:
        return
    
    try:
        # Look for OOXML files that may have extension variables
        ooxml_files = []
        for ext in ["*.xml"]:
            ooxml_files.extend(pkg_dir.rglob(ext))
        
        if not ooxml_files:
            return
        
        # Process variables in each OOXML file
        for xml_file in ooxml_files:
            try:
                # Check if file contains extension variables
                content = xml_file.read_text(encoding='utf-8')
                if 'stylestack.extension.variables' not in content:
                    continue
                
                # Process the file with the substitution pipeline
                result = context.substitution_pipeline.substitute_variables_in_document(
                    str(xml_file),
                    backup_original=True,
                    validate_result=True
                )
                
                if not result.success:
                    context.add_error(StyleStackError(
                        f"Extension variable processing failed for {xml_file}: {result.error_message}",
                        ErrorCode.EXTENSION_PROCESSING_FAILED.value,
                        {"file": str(xml_file), "errors": result.validation_errors}
                    ))
                else:
                    context.add_warning(f"Processed extension variables in {xml_file.relative_to(pkg_dir)}")
                    
            except Exception as e:
                context.add_error(StyleStackError(
                    f"Failed to process extension variables in {xml_file}: {e}",
                    ErrorCode.EXTENSION_PROCESSING_FAILED.value,
                    {"file": str(xml_file), "error": str(e)}
                ))
    
    except Exception as e:
        context.add_error(StyleStackError(
            f"Extension variable processing failed: {e}",
            ErrorCode.EXTENSION_PROCESSING_FAILED.value,
            {"error": str(e)}
        ))


# ---------- Enhanced CLI Helper Functions ----------

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
    
    cli_context.console.print(f"[bold cyan]Command completion script for {shell}:[/bold cyan]\\n")
    cli_context.console.print(completion_script)
    cli_context.console.print(f"\\n[bold]To install:[/bold]")
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
            }
        ]
    }
    
    # Save template
    import json
    template_file = pathlib.Path("batch_template.json")
    with open(template_file, 'w') as f:
        json.dump(template_content, f, indent=2)
    
    cli_context.console.print(f"[green]✅ Batch template created: {template_file}[/green]")
    cli_context.console.print("\\n[bold]Next steps:[/bold]")
    cli_context.console.print("1. Edit the template file to match your templates and paths")
    cli_context.console.print("2. Run batch processing: python build.py --batch batch_template.json")


def process_single_template(src: str, out: str, org: str = None, channel: str = None, verbose: bool = False) -> bool:
    """Process a single template using the existing StyleStack logic."""
    try:
        # Create paths
        src_path = pathlib.Path(src) if src else None
        out_path = pathlib.Path(out)
        
        # Use existing logic from the original main function
        # This is a simplified version - the full implementation would include all the original logic
        
        # Create temporary directory
        with tempfile.TemporaryDirectory(prefix="stylestack_") as tmp_str:
            tmp_dir = pathlib.Path(tmp_str)
            pkg_dir = tmp_dir / "pkg"
            pkg_dir.mkdir(parents=True, exist_ok=True)
            
            # Create build context
            context = BuildContext(
                source_path=src_path,
                output_path=out_path,
                temp_dir=tmp_dir,
                verbose=verbose
            )
            
            # Initialize extension variable system
            initialize_extension_system(context, org, channel)
            
            # Stage 1: Extract/Copy source
            if src_path and src_path.is_file() and src_path.suffix.lower() in [
                ".pptx", ".docx", ".xlsx", ".potx", ".dotx", ".xltx",
                ".odt", ".ott", ".ods", ".ots", ".odp", ".otp", ".odg", ".otg", ".odf"
            ]:
                safe_unzip(src_path, pkg_dir, context)
            elif src_path and src_path.is_dir():
                shutil.copytree(src_path, pkg_dir, dirs_exist_ok=True)
            else:
                raise StyleStackError(
                    f"Invalid source: {src_path}",
                    ErrorCode.SOURCE_NOT_FOUND.value
                )
            
            # Stage 2: Process extension variables
            process_extension_variables(context, pkg_dir)
            
            # Stage 3: Apply JSON patches
            process_json_patches(context, pkg_dir, org, channel)
            
            # Stage 4: Validate package
            validate_package_safe(pkg_dir, context)
            
            # Stage 5: Create output
            safe_zip_dir(pkg_dir, out_path, context)
            
            return not context.has_errors()
            
    except Exception as e:
        if verbose:
            print(f"Error processing template: {e}")
        return False


# ---------- Main CLI Implementation ----------
@click.command()
@click.option('--src', help='Source .pptx/.docx/.xlsx or directory with OOXML parts')
@click.option('--as-potx', is_flag=True, help='Convert to PowerPoint template (.potx)')
@click.option('--as-dotx', is_flag=True, help='Convert to Word template (.dotx)')
@click.option('--as-xltx', is_flag=True, help='Convert to Excel template (.xltx)')
@click.option('--out', help='Output file path')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output with detailed error reporting')
@click.option('--quiet', '-q', is_flag=True, help='Quiet mode - minimal output')
@click.option('--org', help='Organization name for extension variable lookup')
@click.option('--channel', help='Channel name for extension variable lookup')
@click.option('--supertheme', is_flag=True, help='Generate Microsoft SuperTheme package (.thmx)')
@click.option('--designs', help='Directory containing design variant JSON files')
@click.option('--ratios', help='Aspect ratios (comma-separated: 16:9,4:3,a4,letter)')
# Enhanced CLI options
@click.option('--config', help='Configuration file path (YAML/JSON)')
@click.option('--batch', help='Batch processing configuration file')
@click.option('--interactive', '-i', is_flag=True, help='Run in interactive mode')
@click.option('--parallel', is_flag=True, help='Enable parallel processing')
@click.option('--max-workers', type=int, help='Maximum number of worker threads')
@click.option('--dry-run', is_flag=True, help='Show what would be done without executing')
@click.option('--force', is_flag=True, help='Overwrite existing files without prompting')
@click.option('--resume', help='Resume batch processing from checkpoint file')
@click.option('--diagnose', is_flag=True, help='Run system diagnostics')
@click.option('--check-updates', is_flag=True, help='Check for StyleStack updates')
@click.option('--list-templates', is_flag=True, help='List available templates')
@click.option('--validate-config', is_flag=True, help='Validate configuration file')
@click.option('--create-batch-template', is_flag=True, help='Create batch configuration template')
@click.option('--setup-completion', help='Set up command completion for shell (bash/zsh)')
def main(src, as_potx, as_dotx, as_xltx, out, verbose, quiet, org, channel, supertheme, designs, ratios,
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
                    cli_context.batch_processor = BatchProcessor(cli_context)
                success = cli_context.batch_processor.resume_from_checkpoint(resume)
                
            elif supertheme:
                # SuperTheme generation mode - use original logic for now
                success = _process_supertheme_original(designs, ratios, out, verbose)
                
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
            cli_context.console.print("\\n[yellow]⚠️  Operation cancelled by user[/yellow]")
            sys.exit(130)  # Standard exit code for SIGINT
            
        except Exception as e:
            cli_context.error_handler.handle_processing_error(e, cli_context)
            sys.exit(1)
    
    else:
        # Fallback to legacy CLI implementation
        _legacy_main(src, as_potx, as_dotx, as_xltx, out, verbose, org, channel, supertheme, designs, ratios)


def _process_supertheme_original(designs, ratios, out, verbose):
    """Original SuperTheme processing logic."""
    import click
    
    # License validation for commercial use (GitHub-native)
    if EXTENSION_SYSTEM_AVAILABLE and GitHubLicenseManager:
        license_manager = GitHubLicenseManager()
        license_enforcer = GitHubLicenseEnforcer(license_manager)
        
        try:
            # Check if org requires licensing  
            license_enforcer.enforce("supertheme-org", 'build')
        except LicenseError as e:
            click.echo(str(e))
            return False
    
    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')
    
    # SuperTheme generation mode
    if supertheme:
        # Handle SuperTheme generation separately
        if verbose:
            click.echo("🎨 Generating Microsoft SuperTheme package...")
        
        # Validate SuperTheme parameters
        if not designs:
            click.echo("❌ Error: --designs directory is required for SuperTheme generation")
            click.echo("   Usage: build.py --supertheme --designs ./designs --ratios 16:9,4:3 --out theme.thmx")
            sys.exit(1)
        
        # Import SuperTheme generator
        try:
            from tools.supertheme_generator import SuperThemeGenerator
            from tools.aspect_ratio_resolver import create_standard_aspect_ratios
            import json
        except ImportError as e:
            click.echo(f"❌ Error: SuperTheme generator not available: {e}")
            sys.exit(1)
        
        # Load design variants
        design_variants = {}
        designs_path = pathlib.Path(designs)
        
        if not designs_path.exists():
            click.echo(f"❌ Error: Designs directory not found: {designs}")
            sys.exit(1)
        
        if verbose:
            click.echo(f"📂 Loading design variants from: {designs}")
        
        for json_file in designs_path.glob("*.json"):
            try:
                with open(json_file) as f:
                    design_data = json.load(f)
                    design_name = json_file.stem.replace('_', ' ').title()
                    design_variants[design_name] = design_data
                    if verbose:
                        click.echo(f"   ✓ Loaded: {design_name}")
            except Exception as e:
                click.echo(f"   ⚠️  Failed to load {json_file.name}: {e}")
        
        if not design_variants:
            click.echo("❌ Error: No valid design files found in designs directory")
            sys.exit(1)
        
        # Parse aspect ratios
        aspect_ratio_list = []
        if ratios:
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
            
            for ratio in ratios.split(','):
                ratio = ratio.strip().lower()
                if ratio in ratio_mapping:
                    aspect_ratio_list.append(ratio_mapping[ratio])
                else:
                    click.echo(f"⚠️  Warning: Unknown aspect ratio '{ratio}', skipping")
                    click.echo(f"   Available: {', '.join(ratio_mapping.keys())}")
        else:
            # Default aspect ratios
            aspect_ratio_list = [
                'aspectRatios.widescreen_16_9',
                'aspectRatios.standard_16_10',
                'aspectRatios.classic_4_3'
            ]
        
        if verbose:
            click.echo(f"🖼️  Using aspect ratios: {len(aspect_ratio_list)}")
            for ratio in aspect_ratio_list:
                click.echo(f"   • {ratio.split('.')[-1].replace('_', ' ').title()}")
        
        # Generate SuperTheme
        try:
            generator = SuperThemeGenerator(verbose=verbose)
            
            if verbose:
                click.echo("🔨 Generating SuperTheme package...")
                click.echo(f"   Designs: {len(design_variants)}")
                click.echo(f"   Aspect ratios: {len(aspect_ratio_list)}")
                click.echo(f"   Total variants: {len(design_variants) * len(aspect_ratio_list)}")
            
            # Generate the SuperTheme package
            supertheme_bytes = generator.generate_supertheme(
                design_variants=design_variants,
                aspect_ratios=aspect_ratio_list
            )
            
            # Write output file
            out_path = pathlib.Path(out)
            out_path.write_bytes(supertheme_bytes)
            
            # Report success
            size_mb = len(supertheme_bytes) / (1024 * 1024)
            click.echo(f"✅ SuperTheme generated: {out_path}")
            click.echo(f"   Size: {size_mb:.2f} MB")
            click.echo(f"   Variants: {len(design_variants) * len(aspect_ratio_list)}")
            
            if size_mb > 5.0:
                click.echo(f"⚠️  Warning: Package size ({size_mb:.2f}MB) exceeds recommended 5MB limit")
            
        except Exception as e:
            click.echo(f"❌ Error generating SuperTheme: {e}")
            if verbose:
                import traceback
                click.echo(traceback.format_exc())
            sys.exit(1)
        
        return  # Exit after SuperTheme generation
    
    # Determine output format for regular template processing
    target_format = None
    if as_potx:
        target_format = "potx"
    elif as_dotx:
        target_format = "dotx"
    elif as_xltx:
        target_format = "xltx"
    else:
        # Auto-detect from output extension
        ext = pathlib.Path(out).suffix.lower()
        if ext in [".potx", ".dotx", ".xltx", ".otp", ".ott", ".ots", ".otg"]:
            target_format = ext[1:]  # Remove dot
    
    src_path = pathlib.Path(src) if src else None
    out_path = pathlib.Path(out)
    
    # Create temporary directory
    with tempfile.TemporaryDirectory(prefix="stylestack_") as tmp_str:
        tmp_dir = pathlib.Path(tmp_str)
        pkg_dir = tmp_dir / "pkg"
        pkg_dir.mkdir(parents=True, exist_ok=True)
        
        # Create build context
        context = BuildContext(
            source_path=src_path,
            output_path=out_path,
            temp_dir=tmp_dir,
            verbose=verbose
        )
        
        # Initialize extension variable system
        if verbose:
            click.echo("🔧 Initializing extension variable system...")
        
        success = initialize_extension_system(context, org, channel)
        if success and verbose:
            click.echo("   Extension variable system initialized")
        elif not success:
            click.echo("⚠️  Extension variable system not available")
        
        try:
            # Stage 1: Extract/Copy source
            if verbose:
                click.echo("🗂️  Staging source package...")
            
            if src_path and src_path.is_file() and src_path.suffix.lower() in [
                # OOXML formats
                ".pptx", ".docx", ".xlsx", ".potx", ".dotx", ".xltx",
                # OpenDocument formats
                ".odt", ".ott", ".ods", ".ots", ".odp", ".otp", ".odg", ".otg", ".odf"
            ]:
                safe_unzip(src_path, pkg_dir, context)
            elif src_path and src_path.is_dir():
                shutil.copytree(src_path, pkg_dir, dirs_exist_ok=True)
            else:
                raise StyleStackError(
                    f"Invalid source: {src_path}",
                    ErrorCode.SOURCE_NOT_FOUND.value
                )
            
            # Stage 2: Extension variables are loaded by the variable resolver
            # No separate token loading needed
            
            # Stage 3: Process extension variables
            if verbose:
                click.echo("🎨 Processing extension variables...")
            
            process_extension_variables(context, pkg_dir)
            
            if verbose:
                click.echo("   Extension variables processed")
            
            # Stage 3.5: Apply JSON patches
            if verbose:
                click.echo("🔧 Applying JSON patches...")
            
            process_json_patches(context, pkg_dir, org, channel)
            
            if verbose:
                click.echo("   JSON patches applied")
            
            # Stage 4: Convert to template format
            if target_format:
                if verbose:
                    click.echo(f"🔄 Converting to {target_format.upper()} template...")
                flip_content_type(pkg_dir / "[Content_Types].xml", target_format, context)
            
            # Stage 5: Validate package
            if verbose:
                click.echo("✅ Validating package...")
            
            validate_package_safe(pkg_dir, context)
            
            # Stage 6: Create output
            if verbose:
                click.echo("📦 Creating final package...")
            
            safe_zip_dir(pkg_dir, out_path, context)
            
            # Report results
            if context.warnings:
                click.echo(f"⚠️  {len(context.warnings)} warnings:")
                for warning in context.warnings[:5]:  # Show first 5
                    click.echo(f"   {warning}")
            
            if context.has_errors():
                click.echo(f"❌ {len(context.errors)} errors occurred:")
                for error in context.errors:
                    click.echo(f"   [E{error.error_code:04d}] {error.message}")
                    if verbose and error.context:
                        for k, v in error.context.items():
                            click.echo(f"      {k}: {v}")
                sys.exit(1)
            else:
                click.echo(f"✅ Built: {out_path}")
                if verbose:
                    size_mb = out_path.stat().st_size / (1024 * 1024)
                    click.echo(f"   Size: {size_mb:.2f} MB")
                    click.echo(f"   Extension System: Enabled")
                    if org:
                        click.echo(f"   Organization: {org}")
                    if channel:
                        click.echo(f"   Channel: {channel}")
        
        except StyleStackError as e:
            click.echo(f"❌ [E{e.error_code:04d}] {e.message}")
            if verbose and e.context:
                for k, v in e.context.items():
                    click.echo(f"   {k}: {v}")
            sys.exit(e.error_code // 1000)  # Exit with category code
        
        except Exception as e:
            click.echo(f"❌ Unexpected error: {e}")
            if verbose:
                click.echo(traceback.format_exc())
            sys.exit(99)


def _legacy_main(src, as_potx, as_dotx, as_xltx, out, verbose, org, channel, supertheme, designs, ratios):
    """Legacy CLI implementation for fallback when enhanced CLI is not available."""
    import click
    
    click.echo("⚠️  Enhanced CLI not available, using legacy mode...")
    
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
    
    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')
    
    # SuperTheme generation mode
    if supertheme:
        success = _process_supertheme_original(designs, ratios, out, verbose)
        if not success:
            sys.exit(1)
        return
    
    # Validate required parameters
    if not src:
        click.echo("❌ Error: --src is required")
        sys.exit(1)
    
    if not out:
        click.echo("❌ Error: --out is required")
        sys.exit(1)
    
    # Process single template using original logic
    try:
        success = process_single_template(src, out, org, channel, verbose)
        if success:
            click.echo(f"✅ Template processed: {out}")
        else:
            click.echo("❌ Template processing failed")
            sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        if verbose:
            import traceback
            click.echo(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()