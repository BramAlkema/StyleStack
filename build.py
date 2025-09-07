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

# Import OOXML Extension Variable System components
try:
    from tools.variable_resolver import VariableResolver
    from tools.ooxml_processor import OOXMLProcessor
    from tools.theme_resolver import ThemeResolver
    from tools.variable_substitution import VariableSubstitutionPipeline
    from tools.extension_schema_validator import ExtensionSchemaValidator
    EXTENSION_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import OOXML Extension Variable System components: {e}")
    print("Extension variable features will be disabled.")
    VariableResolver = None
    OOXMLProcessor = None
    ThemeResolver = None
    VariableSubstitutionPipeline = None
    ExtensionSchemaValidator = None
    EXTENSION_SYSTEM_AVAILABLE = False

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

@dataclass
class BuildContext:
    """Build context with extension variable system support"""
    source_path: pathlib.Path
    output_path: pathlib.Path
    temp_dir: pathlib.Path
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
CONTENT_TYPES = {
    "potx": "application/vnd.openxmlformats-officedocument.presentationml.template.main+xml",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml",
    "dotx": "application/vnd.openxmlformats-officedocument.wordprocessingml.template.main+xml",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml",
    "xltx": "application/vnd.openxmlformats-officedocument.spreadsheetml.template.main+xml",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml",
}

def flip_content_type(content_types_path: pathlib.Path, target_format: str, context: BuildContext):
    """Convert between document and template formats with error handling"""
    import re
    
    try:
        if not content_types_path.exists():
            raise StyleStackError(
                "Content types file not found",
                ErrorCode.CONTENT_TYPE_ERROR.value,
                {"file": str(content_types_path)}
            )
        
        xml = content_types_path.read_text(encoding="utf-8")
        
        # Determine source and target content types
        if target_format == "potx":
            xml = re.sub(
                r'application/vnd\.openxmlformats-officedocument\.presentationml\.presentation\.main\+xml',
                CONTENT_TYPES["potx"],
                xml
            )
        elif target_format == "dotx":
            xml = re.sub(
                r'application/vnd\.openxmlformats-officedocument\.wordprocessingml\.document\.main\+xml',
                CONTENT_TYPES["dotx"],
                xml
            )
        elif target_format == "xltx":
            xml = re.sub(
                r'application/vnd\.openxmlformats-officedocument\.spreadsheetml\.sheet\.main\+xml',
                CONTENT_TYPES["xltx"],
                xml
            )
        else:
            raise StyleStackError(
                f"Unsupported template format: {target_format}",
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
    for p in xml_files:
        data = p.read_bytes()
        found_effects = [effect.decode() for effect in BANNED_EFFECTS if effect in data]
        if found_effects:
            raise StyleStackError(
                f"Banned effects found in {p}: {', '.join(found_effects)}",
                ErrorCode.BANNED_EFFECT_DETECTED.value,
                {"file": str(p), "effects": found_effects}
            )
    
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
    
    if broken_rels:
        raise StyleStackError(
            f"Broken relationships found: {len(broken_rels)} broken links",
            ErrorCode.BROKEN_RELATIONSHIP.value,
            {"broken": broken_rels[:10]}  # Limit to first 10
        )

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
            variable_resolver=context.variable_resolver,
            ooxml_processor=context.ooxml_processor,
            theme_resolver=context.theme_resolver
        )
        
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


# ---------- Main CLI Implementation ----------
@click.command()
@click.option('--src', help='Source .pptx/.docx/.xlsx or directory with OOXML parts')
@click.option('--as-potx', is_flag=True, help='Convert to PowerPoint template (.potx)')
@click.option('--as-dotx', is_flag=True, help='Convert to Word template (.dotx)')
@click.option('--as-xltx', is_flag=True, help='Convert to Excel template (.xltx)')
@click.option('--out', required=True, help='Output file path')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output with detailed error reporting')
@click.option('--org', help='Organization name for extension variable lookup')
@click.option('--channel', help='Channel name for extension variable lookup')
def main(src, as_potx, as_dotx, as_xltx, out, verbose, org, channel):
    """StyleStack OOXML Extension Variable System"""
    
    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')
    
    # Determine output format
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
        if ext in [".potx", ".dotx", ".xltx"]:
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
            temp_dir=tmp_dir
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
            
            if src_path and src_path.is_file() and src_path.suffix.lower() in [".pptx", ".docx", ".xlsx"]:
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

if __name__ == "__main__":
    main()