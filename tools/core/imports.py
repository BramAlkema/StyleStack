"""
Centralized imports for StyleStack tools

This module provides a single source for common imports used across the StyleStack
codebase, eliminating the 40+ duplicate import patterns identified in our analysis.

Usage:
    from tools.core.imports import *
    # or selectively:
    from tools.core.imports import COMMON_TYPES, Path, json
"""

# Standard library imports used across 40+ files
from typing import Any, Dict, List, Optional, Union, Tuple, Set, Callable, Type, Iterator, TYPE_CHECKING
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import json
import zipfile
import logging
import time
import hashlib
import re
import os
import sys
from contextlib import contextmanager
from collections import defaultdict, Counter

# XML processing imports with fallback
import xml.etree.ElementTree as ET
try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False

# Common type aliases used across multiple files
COMMON_TYPES = Union[str, Path]
JSON_DICT = Dict[str, Any]
FILE_PATH = Union[str, Path]
VALIDATION_ERRORS = List[str]

# Common constants
DEFAULT_ENCODING = 'utf-8'
OOXML_EXTENSIONS = {'.potx', '.dotx', '.xltx', '.pptx', '.docx', '.xlsx'}
LIBREOFFICE_EXTENSIONS = {'.otp', '.ott', '.ots', '.odp', '.odt', '.ods'}

# Configure logging for consistent behavior
def get_logger(name: str) -> logging.Logger:
    """Get a consistently configured logger"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

# Export commonly used items
__all__ = [
    # Types
    'Any', 'Dict', 'List', 'Optional', 'Union', 'Tuple', 'Set', 'Callable', 'Type', 'Iterator', 'TYPE_CHECKING',
    'dataclass', 'field', 'Enum', 'Path',
    # Modules
    'json', 'zipfile', 'logging', 'time', 'hashlib', 're', 'os', 'sys',
    'contextmanager', 'defaultdict', 'Counter',
    # XML
    'ET', 'etree', 'LXML_AVAILABLE',
    # Type aliases
    'COMMON_TYPES', 'JSON_DICT', 'FILE_PATH', 'VALIDATION_ERRORS',
    # Constants
    'DEFAULT_ENCODING', 'OOXML_EXTENSIONS', 'LIBREOFFICE_EXTENSIONS',
    # Utilities
    'get_logger'
]