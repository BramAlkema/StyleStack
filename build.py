#!/usr/bin/env python3
"""
StyleStack OOXML patcher (PowerPoint/Word/Excel)
- Input: baseline template files (.potx/.dotx/.pptx from baseline-templates/)
- Tokens: YAML files merged core→channel→org→user
- Patches: YAML files merged core→channel→org→user (order matters)
- Output: deterministic .potx/.dotx/.xltx templates with comprehensive error handling

Usage examples:
  python build.py --baseline Normal.dotm --patch core/typography.yaml --tokens tokens/core.yaml --out dist/out.dotx
  python build.py --org acme --channel present --products potx,dotx,xltx --version 1.0.0
"""

import argparse, io, os, re, shutil, sys, tempfile, zipfile, pathlib, hashlib, time
import traceback, logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from lxml import etree as ET
import yaml
import click

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
    SOURCE_NOT_READABLE = 1002
    OUTPUT_PATH_INVALID = 1003
    TEMP_DIR_FAILED = 1004
    ZIP_EXTRACTION_FAILED = 1005
    ZIP_CREATION_FAILED = 1006
    
    # YAML/Token Errors (2xxx)
    YAML_PARSE_ERROR = 2001
    TOKEN_NOT_FOUND = 2002
    TOKEN_CIRCULAR_REF = 2003
    PATCH_FILE_INVALID = 2004
    
    # XML/OOXML Errors (3xxx)
    XML_PARSE_ERROR = 3001
    XML_XPATH_INVALID = 3002
    XML_NAMESPACE_ERROR = 3003
    OOXML_STRUCTURE_INVALID = 3004
    CONTENT_TYPE_ERROR = 3005
    
    # Validation Errors (4xxx)
    TEMPLATE_VALIDATION_FAILED = 4001
    BANNED_EFFECT_DETECTED = 4002
    BROKEN_RELATIONSHIP = 4003
    MISSING_REQUIRED_PARTS = 4004
    
    # Build Process Errors (5xxx)
    PATCH_APPLICATION_FAILED = 5001
    TOKEN_RESOLUTION_FAILED = 5002
    LAYER_MERGE_FAILED = 5003

@dataclass
class BuildContext:
    """Build context with comprehensive error tracking"""
    source_path: pathlib.Path
    output_path: pathlib.Path
    temp_dir: pathlib.Path
    tokens: Dict[str, Any] = field(default_factory=dict)
    patches_applied: List[str] = field(default_factory=list)
    errors: List[StyleStackError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, error: StyleStackError):
        self.errors.append(error)
        
    def add_warning(self, message: str):
        self.warnings.append(message)
        
    def has_errors(self) -> bool:
        return len(self.errors) > 0

# ---------- Namespaces ----------
NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
    "w15": "http://schemas.microsoft.com/office/word/2012/wordml",
    "s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "ct": "http://schemas.openxmlformats.org/package/2006/content-types",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

EMU_PER_IN = 914400
def inch(x: float) -> int: return int(round(x * EMU_PER_IN))

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

EPOCH_1980 = (1980,1,1,0,0,0)
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

# ---------- Enhanced Token System ----------
_TOKEN_RX = re.compile(r"\{tokens\.([a-zA-Z0-9_.-]+)\}")

def load_tokens_safe(paths: List[pathlib.Path], context: BuildContext) -> Dict[str, Any]:
    """Load and merge token files with comprehensive error handling"""
    merged: Dict[str, Any] = {}
    
    for p in paths:
        try:
            if not p.exists():
                context.add_warning(f"Token file not found: {p}")
                continue
                
            with open(p, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    context.add_warning(f"Empty token file: {p}")
                    continue
                    
                layer = yaml.safe_load(content)
                if layer is None:
                    context.add_warning(f"No tokens found in: {p}")
                    continue
                    
                merged = deep_merge(merged, layer)
                
        except yaml.YAMLError as e:
            raise StyleStackError(
                f"YAML parse error in {p}: {e}",
                ErrorCode.YAML_PARSE_ERROR.value,
                {"file": str(p), "error": str(e)}
            )
        except Exception as e:
            raise StyleStackError(
                f"Failed to load token file {p}: {e}",
                ErrorCode.YAML_PARSE_ERROR.value,
                {"file": str(p), "error": str(e)}
            )
    
    # Flatten tokens with circular reference detection
    flat = {}
    try:
        flatten_tokens_safe(merged, flat, prefix=[], visited=set())
    except RecursionError:
        raise StyleStackError(
            "Circular reference detected in tokens",
            ErrorCode.TOKEN_CIRCULAR_REF.value
        )
    
    return flat

def deep_merge(a, b):
    """Deep merge two dictionaries"""
    if isinstance(a, dict) and isinstance(b, dict):
        out = dict(a)
        for k, v in b.items():
            out[k] = deep_merge(a.get(k), v)
        return out
    return b

def flatten_tokens_safe(node, out: Dict[str, Any], prefix: List[str], visited: set):
    """Flatten tokens with circular reference detection"""
    key = ".".join(prefix)
    if key in visited:
        raise RecursionError(f"Circular reference: {key}")
    
    visited.add(key)
    
    try:
        if isinstance(node, dict) and "value" in node and len(node) <= 3:  # { value, type?, description? }
            out[key] = node["value"]
            return
            
        if isinstance(node, dict):
            for k, v in node.items():
                flatten_tokens_safe(v, out, prefix + [k], visited.copy())
        else:
            out[key] = node
    finally:
        visited.discard(key)

def resolve_tokens_safe(s: Any, tokens: Dict[str, Any], context: BuildContext) -> Any:
    """Resolve tokens with comprehensive error handling"""
    if not isinstance(s, str): 
        return s
        
    def repl(m):
        key = m.group(1)
        if key not in tokens:
            error = StyleStackError(
                f"Missing token: {key}",
                ErrorCode.TOKEN_NOT_FOUND.value,
                {"token": key, "available": list(tokens.keys())[:10]}
            )
            context.add_error(error)
            return f"{{MISSING:{key}}}"  # Fail gracefully
        return str(tokens[key])
    
    try:
        return _TOKEN_RX.sub(repl, s)
    except Exception as e:
        raise StyleStackError(
            f"Token resolution failed: {e}",
            ErrorCode.TOKEN_RESOLUTION_FAILED.value,
            {"string": s, "error": str(e)}
        )

# ---------- Enhanced XML Operations ----------
def load_xml_safe(path: pathlib.Path, context: BuildContext) -> Optional[ET._ElementTree]:
    """Load XML with comprehensive error handling"""
    try:
        if not path.exists():
            raise StyleStackError(
                f"XML file not found: {path}",
                ErrorCode.SOURCE_NOT_FOUND.value,
                {"file": str(path)}
            )
        
        return ET.parse(str(path))
        
    except ET.XMLSyntaxError as e:
        raise StyleStackError(
            f"XML parse error in {path}: {e}",
            ErrorCode.XML_PARSE_ERROR.value,
            {"file": str(path), "line": e.lineno, "error": str(e)}
        )
    except Exception as e:
        raise StyleStackError(
            f"Failed to load XML {path}: {e}",
            ErrorCode.XML_PARSE_ERROR.value,
            {"file": str(path), "error": str(e)}
        )

def save_xml_safe(tree: ET._ElementTree, path: pathlib.Path, context: BuildContext):
    """Save XML with error handling"""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        xml_bytes = ET.tostring(tree, xml_declaration=True, encoding="utf-8", standalone=True)
        path.write_bytes(xml_bytes)
    except Exception as e:
        raise StyleStackError(
            f"Failed to save XML {path}: {e}",
            ErrorCode.XML_PARSE_ERROR.value,
            {"file": str(path), "error": str(e)}
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

# ---------- Enhanced Patch Engine ----------
def apply_patches_safe(root: pathlib.Path, patch_files: List[pathlib.Path], tokens: Dict[str, Any], context: BuildContext):
    """Apply patches with comprehensive error handling"""
    for patch_path in patch_files:
        try:
            if not patch_path.exists():
                context.add_warning(f"Patch file not found: {patch_path}")
                continue
                
            spec = yaml.safe_load(patch_path.read_text(encoding="utf-8"))
            if not spec:
                context.add_warning(f"Empty patch file: {patch_path}")
                continue
                
            for tgt in spec.get("targets", []):
                try:
                    apply_single_patch_target(root, tgt, tokens, context, patch_path)
                    context.patches_applied.append(f"{patch_path.name}:{tgt.get('file', 'unknown')}")
                except StyleStackError as e:
                    e.context.update({"patch_file": str(patch_path), "target": tgt.get("file", "unknown")})
                    context.add_error(e)
                except Exception as e:
                    error = StyleStackError(
                        f"Patch application failed: {e}",
                        ErrorCode.PATCH_APPLICATION_FAILED.value,
                        {"patch_file": str(patch_path), "target": tgt.get("file", "unknown"), "error": str(e)}
                    )
                    context.add_error(error)
                    
        except yaml.YAMLError as e:
            raise StyleStackError(
                f"Invalid patch file {patch_path}: {e}",
                ErrorCode.PATCH_FILE_INVALID.value,
                {"file": str(patch_path), "error": str(e)}
            )
        except Exception as e:
            raise StyleStackError(
                f"Failed to process patch {patch_path}: {e}",
                ErrorCode.PATCH_APPLICATION_FAILED.value,
                {"file": str(patch_path), "error": str(e)}
            )

def apply_single_patch_target(root: pathlib.Path, tgt: Dict, tokens: Dict[str, Any], context: BuildContext, patch_path: pathlib.Path):
    """Apply a single patch target with error handling"""
    rel_file = tgt.get("file")
    if not rel_file:
        raise StyleStackError("Patch target missing 'file' field", ErrorCode.PATCH_FILE_INVALID.value)
    
    file_path = root / rel_file
    if not file_path.exists():
        raise StyleStackError(f"Patch target not found: {rel_file}", ErrorCode.SOURCE_NOT_FOUND.value)
    
    # Load XML with enhanced namespaces
    ns = dict(NS)
    ns.update(tgt.get("ns", {}))
    tree = load_xml_safe(file_path, context)
    
    # Check if strict mode is enabled
    strict = bool(tgt.get("strict", False))
    
    # Apply operations
    for op in tgt.get("ops", []):
        try:
            if "set" in op:
                _op_set_safe(tree, ns, op["set"], tokens, context, strict)
            elif "insert" in op:
                _op_insert_safe(tree, ns, op["insert"], tokens, context, strict)
            elif "remove" in op:
                _op_remove_safe(tree, ns, op["remove"], context, strict)
            elif "relsAdd" in op:
                _op_rels_add_safe(root / op["relsAdd"]["file"], op["relsAdd"]["items"], context)
            else:
                raise StyleStackError(f"Unknown operation: {list(op.keys())}", ErrorCode.PATCH_FILE_INVALID.value)
        except Exception as e:
            if not isinstance(e, StyleStackError):
                raise StyleStackError(
                    f"Operation failed: {e}",
                    ErrorCode.PATCH_APPLICATION_FAILED.value,
                    {"operation": list(op.keys())[0], "error": str(e)}
                )
            raise
    
    save_xml_safe(tree, file_path, context)

def _xpath_safe(tree, xp, ns, strict, context):
    """Safe XPath execution with error handling"""
    try:
        nodes = tree.xpath(xp, namespaces=ns)
        if strict and len(nodes) == 0:
            raise StyleStackError(f"XPath matched 0 nodes: {xp}", ErrorCode.XML_XPATH_INVALID.value)
        return nodes
    except ET.XPathEvalError as e:
        raise StyleStackError(f"Invalid XPath expression: {xp} - {e}", ErrorCode.XML_XPATH_INVALID.value)

def _op_set_safe(tree, ns, args, tokens, context, strict):
    """Safe set operation with error handling"""
    xp = args.get("xpath")
    if not xp:
        raise StyleStackError("Set operation missing 'xpath'", ErrorCode.PATCH_FILE_INVALID.value)
    
    val = resolve_tokens_safe(args.get("value", ""), tokens, context)
    nodes = _xpath_safe(tree, xp, ns, strict, context)
    
    for node in nodes:
        if isinstance(node, ET._ElementUnicodeResult) and node.is_attribute:
            parent = node.getparent()
            attrname = node.attrname
            parent.set(attrname, val)
        elif isinstance(node, ET._Element):
            node.text = val
        else:
            # Fallback: try to set attribute if xpath ends with /@attr
            m = re.search(r"/@([A-Za-z0-9:_-]+)$", xp)
            if m and isinstance(node, ET._Element):
                node.set(m.group(1), val)

def _op_insert_safe(tree, ns, args, tokens, context, strict):
    """Safe insert operation with error handling"""
    xp = args.get("xpath")
    if not xp:
        raise StyleStackError("Insert operation missing 'xpath'", ErrorCode.PATCH_FILE_INVALID.value)
    
    position = args.get("position", "last")
    xml_content = resolve_tokens_safe(args.get("xml", ""), tokens, context)
    
    try:
        frag = ET.fromstring(xml_content.encode("utf-8"))
    except ET.XMLSyntaxError as e:
        raise StyleStackError(f"Invalid XML fragment: {e}", ErrorCode.XML_PARSE_ERROR.value)
    
    targets = _xpath_safe(tree, xp, ns, strict, context)
    for t in targets:
        if position == "first":
            t.insert(0, frag)
        elif position == "before":
            t.addprevious(frag)
        elif position == "after":
            t.addnext(frag)
        else:
            t.append(frag)

def _op_remove_safe(tree, ns, args, context, strict):
    """Safe remove operation with error handling"""
    xp = args.get("xpath")
    if not xp:
        raise StyleStackError("Remove operation missing 'xpath'", ErrorCode.PATCH_FILE_INVALID.value)
    
    for node in _xpath_safe(tree, xp, ns, strict, context):
        parent = node.getparent()
        if parent is not None:
            parent.remove(node)

def _op_rels_add_safe(rels_path: pathlib.Path, items: List[Dict[str,str]], context: BuildContext):
    """Safe relationship addition with error handling"""
    try:
        if rels_path.exists():
            tree = ET.parse(str(rels_path))
            root = tree.getroot()
        else:
            root = ET.Element("Relationships", xmlns="http://schemas.openxmlformats.org/package/2006/relationships")
            tree = ET.ElementTree(root)
        
        existing = {rel.get("Id") for rel in root.findall("{*}Relationship")}
        
        for item in items:
            if not all(k in item for k in ["id", "type", "target"]):
                raise StyleStackError("Relationship item missing required fields", ErrorCode.PATCH_FILE_INVALID.value)
            
            if item["id"] in existing:
                continue
                
            rel = ET.SubElement(root, "Relationship")
            rel.set("Id", item["id"])
            rel.set("Type", item["type"])
            rel.set("Target", item["target"])
        
        save_xml_safe(tree, rels_path, context)
        
    except Exception as e:
        if not isinstance(e, StyleStackError):
            raise StyleStackError(f"Failed to add relationships: {e}", ErrorCode.PATCH_APPLICATION_FAILED.value)
        raise

# ---------- Enhanced Validators ----------
BANNED_EFFECTS = (b"<a:glow", b"<a:bevel", b"<a:outerShdw", b"<a:reflection")

def validate_package_safe(root: pathlib.Path, context: BuildContext):
    """Comprehensive package validation with detailed error reporting"""
    
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

# ---------- Main CLI Implementation ----------
@click.command()
@click.option('--src', help='Source .pptx/.docx/.xlsx or directory with OOXML parts')
@click.option('--patch', multiple=True, help='Patch YAML files in order (core→channel→org→user)')
@click.option('--tokens', multiple=True, help='Token YAML files in order (core→channel→org→user)')
@click.option('--as-potx', is_flag=True, help='Convert to PowerPoint template (.potx)')
@click.option('--as-dotx', is_flag=True, help='Convert to Word template (.dotx)')
@click.option('--as-xltx', is_flag=True, help='Convert to Excel template (.xltx)')
@click.option('--out', required=True, help='Output file path')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output with detailed error reporting')
def main(src, patch, tokens, as_potx, as_dotx, as_xltx, out, verbose):
    """StyleStack OOXML Template Build System with Comprehensive Error Handling"""
    
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
            
            # Stage 2: Load tokens
            if verbose and tokens:
                click.echo("🎨 Loading design tokens...")
            
            token_paths = [pathlib.Path(t) for t in tokens]
            context.tokens = load_tokens_safe(token_paths, context) if token_paths else {}
            
            if verbose and context.tokens:
                click.echo(f"   Loaded {len(context.tokens)} tokens")
            
            # Stage 3: Apply patches
            if verbose and patch:
                click.echo("🔧 Applying patches...")
            
            patch_paths = [pathlib.Path(p) for p in patch]
            if patch_paths:
                apply_patches_safe(pkg_dir, patch_paths, context.tokens, context)
            
            if verbose:
                click.echo(f"   Applied {len(context.patches_applied)} patches")
            
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
                    click.echo(f"   Tokens: {len(context.tokens)}")
                    click.echo(f"   Patches: {len(context.patches_applied)}")
        
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