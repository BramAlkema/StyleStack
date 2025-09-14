"""Utility functions for OOXML Round-Trip Testing Utility."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Union
import platform

from .exceptions import OOXMLTesterError


def normalize_path(path: Union[str, Path]) -> Path:
    """Normalize a file path for cross-platform compatibility.
    
    Args:
        path: Input path as string or Path object
        
    Returns:
        Normalized Path object
    """
    if isinstance(path, str):
        path = Path(path)
    
    # Expand user directory and resolve relative paths
    return path.expanduser().resolve()


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        Path object for the directory
        
    Raises:
        OOXMLTesterError: If directory cannot be created
    """
    dir_path = normalize_path(path)
    
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    except PermissionError:
        raise OOXMLTesterError(f"Permission denied creating directory: {dir_path}")
    except OSError as e:
        raise OOXMLTesterError(f"Failed to create directory {dir_path}: {e}")


def cleanup_temp_files(temp_dirs: List[Union[str, Path]]) -> None:
    """Clean up temporary directories and files.
    
    Args:
        temp_dirs: List of temporary directory paths to clean up
    """
    for temp_dir in temp_dirs:
        temp_path = normalize_path(temp_dir)
        if temp_path.exists() and temp_path.is_dir():
            try:
                shutil.rmtree(temp_path)
            except (PermissionError, OSError):
                # Log warning but don't raise - cleanup is best effort
                pass


def create_temp_directory(prefix: str = "ooxml_tester_") -> Path:
    """Create a temporary directory.
    
    Args:
        prefix: Prefix for temporary directory name
        
    Returns:
        Path to created temporary directory
    """
    temp_dir = tempfile.mkdtemp(prefix=prefix)
    return Path(temp_dir)


def get_file_extension(file_path: Union[str, Path]) -> str:
    """Get file extension in lowercase.
    
    Args:
        file_path: Path to file
        
    Returns:
        File extension without dot (e.g., 'docx', 'pptx')
    """
    path = normalize_path(file_path)
    return path.suffix.lower().lstrip('.')


def is_office_file(file_path: Union[str, Path]) -> bool:
    """Check if file is an Office document.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if file is a supported Office format
    """
    extension = get_file_extension(file_path)
    office_extensions = {
        'docx', 'docm', 'dotx', 'dotm',  # Word
        'pptx', 'pptm', 'potx', 'potm',  # PowerPoint
        'xlsx', 'xlsm', 'xltx', 'xltm',  # Excel
        'odt', 'ods', 'odp',             # OpenDocument
    }
    return extension in office_extensions


def get_platform_info() -> dict:
    """Get information about the current platform.
    
    Returns:
        Dictionary with platform information
    """
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
    }


def find_executable(name: str, paths: Optional[List[str]] = None) -> Optional[Path]:
    """Find an executable in system PATH or specified paths.
    
    Args:
        name: Executable name
        paths: Optional list of additional paths to search
        
    Returns:
        Path to executable if found, None otherwise
    """
    # Try system PATH first
    system_path = shutil.which(name)
    if system_path:
        return Path(system_path)
    
    # Try additional paths
    if paths:
        for path_str in paths:
            path = Path(path_str)
            if path.is_file() and os.access(path, os.X_OK):
                return path
            
            # Also try with executable name appended
            exe_path = path / name
            if exe_path.is_file() and os.access(exe_path, os.X_OK):
                return exe_path
    
    return None


def validate_file_access(file_path: Union[str, Path], mode: str = 'r') -> bool:
    """Validate that a file can be accessed in the specified mode.
    
    Args:
        file_path: Path to file
        mode: Access mode ('r' for read, 'w' for write, 'rw' for both)
        
    Returns:
        True if file can be accessed in specified mode
    """
    path = normalize_path(file_path)
    
    if not path.exists():
        return False
    
    if 'r' in mode and not os.access(path, os.R_OK):
        return False
        
    if 'w' in mode and not os.access(path, os.W_OK):
        return False
    
    return True


def safe_filename(filename: str) -> str:
    """Create a safe filename by removing/replacing problematic characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename suitable for filesystem
    """
    # Replace problematic characters
    unsafe_chars = '<>:"/\\|?*'
    safe_name = filename
    
    for char in unsafe_chars:
        safe_name = safe_name.replace(char, '_')
    
    # Remove leading/trailing whitespace and dots
    safe_name = safe_name.strip('. ')
    
    # Ensure not empty
    if not safe_name:
        safe_name = "unnamed"
    
    return safe_name