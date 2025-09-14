"""
Shared file utilities for StyleStack

This module eliminates the 15+ duplicated JSON loading and ZIP handling patterns
identified across the codebase, providing consistent error handling and fallbacks.

Based on duplication analysis findings:
- JSON loading patterns found in 15+ files
- ZIP file handling patterns found in 15+ files  
- File existence checking patterns found in 20+ files
"""

from .imports import (
    Path, json, zipfile, contextmanager, get_logger,
    JSON_DICT, FILE_PATH, Optional, Union, Any, List, Callable
)

logger = get_logger(__name__)


class FileOperationError(Exception):
    """Custom exception for file operation failures"""
    pass


class JSONError(FileOperationError):
    """Exception for JSON-related operations"""
    pass


class ZIPError(FileOperationError):
    """Exception for ZIP-related operations"""
    pass


# JSON Operations - Eliminates 15+ duplicate patterns
def safe_load_json(file_path: FILE_PATH, encoding: str = 'utf-8') -> JSON_DICT:
    """
    Safely load JSON from file with consistent error handling
    
    Replaces duplicate pattern found in:
    - tools/token_parser.py:454-456
    - tools/extension_schema_validator.py:111-113
    - tools/w3c_dtcg_validator.py:115-117
    - tools/token_resolver.py:43-45
    - tools/powerpoint_layout_schema.py:140-142
    + 10 more files
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise JSONError(f"Invalid JSON in file {file_path}: {e}")
    except Exception as e:
        raise JSONError(f"Failed to load JSON from {file_path}: {e}")


def safe_load_json_with_fallback(
    file_path: FILE_PATH, 
    fallback: JSON_DICT = None,
    encoding: str = 'utf-8'
) -> JSON_DICT:
    """
    Load JSON with fallback for missing files
    
    Common pattern for configuration files that may not exist
    """
    try:
        return safe_load_json(file_path, encoding)
    except (FileNotFoundError, JSONError) as e:
        logger.debug(f"JSON fallback used for {file_path}: {e}")
        return fallback or {}


def safe_save_json(
    data: JSON_DICT, 
    file_path: FILE_PATH, 
    encoding: str = 'utf-8',
    indent: int = 2
) -> None:
    """Safely save JSON to file with consistent formatting"""
    file_path = Path(file_path)
    
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(file_path, 'w', encoding=encoding) as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
    except Exception as e:
        raise JSONError(f"Failed to save JSON to {file_path}: {e}")


# ZIP/OOXML Operations - Eliminates 15+ duplicate patterns
@contextmanager
def safe_ooxml_reader(template_path: FILE_PATH):
    """
    Context manager for safe OOXML file reading
    
    Replaces duplicate pattern found in:
    - tools/ooxml_analyzer.py (5 occurrences)
    - tools/template_analyzer.py (2 occurrences)
    - tools/design_token_extractor.py (4 occurrences)
    - tools/supertheme_validator.py (8 occurrences)
    + more files
    """
    template_path = Path(template_path)
    
    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")
    
    if not zipfile.is_zipfile(template_path):
        raise ZIPError(f"File is not a valid ZIP archive: {template_path}")
    
    try:
        with zipfile.ZipFile(template_path, 'r') as zip_file:
            yield zip_file
    except zipfile.BadZipFile as e:
        raise ZIPError(f"Corrupted ZIP file {template_path}: {e}")
    except Exception as e:
        raise ZIPError(f"Failed to read ZIP file {template_path}: {e}")


@contextmanager
def safe_ooxml_writer(template_path: FILE_PATH, compression: int = zipfile.ZIP_DEFLATED):
    """Context manager for safe OOXML file writing"""
    template_path = Path(template_path)
    
    # Ensure parent directory exists
    template_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with zipfile.ZipFile(template_path, 'w', compression) as zip_file:
            yield zip_file
    except Exception as e:
        raise ZIPError(f"Failed to create ZIP file {template_path}: {e}")


def extract_xml_from_ooxml(template_path: FILE_PATH, xml_path: str) -> Optional[str]:
    """
    Extract specific XML file from OOXML package
    
    Common pattern for extracting presentation.xml, document.xml, etc.
    """
    try:
        with safe_ooxml_reader(template_path) as zip_file:
            return zip_file.read(xml_path).decode('utf-8')
    except KeyError:
        logger.debug(f"XML file {xml_path} not found in {template_path}")
        return None
    except Exception as e:
        logger.warning(f"Failed to extract {xml_path} from {template_path}: {e}")
        return None


def list_ooxml_contents(template_path: FILE_PATH) -> List[str]:
    """List all files in an OOXML package"""
    try:
        with safe_ooxml_reader(template_path) as zip_file:
            return zip_file.namelist()
    except Exception as e:
        logger.warning(f"Failed to list contents of {template_path}: {e}")
        return []


# File Existence and Validation - Eliminates 20+ duplicate patterns
def ensure_file_exists(file_path: FILE_PATH, operation_name: str = "operation") -> None:
    """
    Validate file exists with descriptive error
    
    Replaces duplicate pattern: if not file_path.exists(): ...
    Found in 20+ files across the codebase
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found for {operation_name}: {file_path}")


def safe_file_operation(
    file_path: FILE_PATH, 
    operation: Callable[[Path], Any], 
    default_value: Any = None,
    operation_name: str = "file operation"
) -> Any:
    """
    Safely perform file operation with fallback
    
    Generic wrapper for file operations with consistent error handling
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        logger.debug(f"File not found for {operation_name}: {file_path}")
        return default_value
    
    try:
        return operation(file_path)
    except Exception as e:
        logger.warning(f"File operation '{operation_name}' failed on {file_path}: {e}")
        return default_value


def get_file_hash(file_path: FILE_PATH, algorithm: str = 'md5') -> str:
    """Get hash of file contents for caching/comparison"""
    import hashlib
    
    file_path = Path(file_path)
    ensure_file_exists(file_path, "hash calculation")
    
    hash_obj = hashlib.new(algorithm)
    
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        raise FileOperationError(f"Failed to calculate hash for {file_path}: {e}")


def backup_file(file_path: FILE_PATH, backup_suffix: str = '.backup') -> Path:
    """Create a backup copy of a file"""
    import shutil
    
    file_path = Path(file_path)
    ensure_file_exists(file_path, "backup creation")
    
    backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)
    
    try:
        shutil.copy2(file_path, backup_path)
        logger.debug(f"Created backup: {backup_path}")
        return backup_path
    except Exception as e:
        raise FileOperationError(f"Failed to create backup of {file_path}: {e}")


def is_ooxml_file(file_path: FILE_PATH) -> bool:
    """Check if file is a valid OOXML template"""
    from .imports import OOXML_EXTENSIONS
    
    file_path = Path(file_path)
    
    # Check extension
    if file_path.suffix.lower() not in OOXML_EXTENSIONS:
        return False
    
    # Check if it's a valid ZIP file
    if not file_path.exists():
        return False
    
    try:
        return zipfile.is_zipfile(file_path)
    except Exception:
        return False


def get_template_format(file_path: FILE_PATH) -> Optional[str]:
    """
    Determine OOXML template format
    
    Returns: 'powerpoint', 'word', 'excel', or None
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()
    
    format_map = {
        '.potx': 'powerpoint', '.pptx': 'powerpoint',
        '.dotx': 'word', '.docx': 'word', 
        '.xltx': 'excel', '.xlsx': 'excel'
    }
    
    return format_map.get(suffix)


# Utility functions for common file patterns
def read_text_file(file_path: FILE_PATH, encoding: str = 'utf-8') -> str:
    """Read text file with consistent error handling"""
    file_path = Path(file_path)
    ensure_file_exists(file_path, "text file reading")
    
    try:
        return file_path.read_text(encoding=encoding)
    except Exception as e:
        raise FileOperationError(f"Failed to read text file {file_path}: {e}")


def write_text_file(
    file_path: FILE_PATH, 
    content: str, 
    encoding: str = 'utf-8',
    create_dirs: bool = True
) -> None:
    """Write text file with consistent error handling"""
    file_path = Path(file_path)
    
    if create_dirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        file_path.write_text(content, encoding=encoding)
    except Exception as e:
        raise FileOperationError(f"Failed to write text file {file_path}: {e}")


# Export all utility functions
__all__ = [
    # Exceptions
    'FileOperationError', 'JSONError', 'ZIPError',
    # JSON operations
    'safe_load_json', 'safe_load_json_with_fallback', 'safe_save_json',
    # OOXML/ZIP operations  
    'safe_ooxml_reader', 'safe_ooxml_writer', 'extract_xml_from_ooxml',
    'list_ooxml_contents', 'is_ooxml_file', 'get_template_format',
    # File utilities
    'ensure_file_exists', 'safe_file_operation', 'get_file_hash', 
    'backup_file', 'read_text_file', 'write_text_file'
]