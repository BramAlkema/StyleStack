"""OOXML Round-Trip Testing Utility.

A comprehensive testing framework for validating OOXML document compatibility
across different Office platforms through round-trip conversion analysis.
"""

__version__ = "0.1.0"
__author__ = "StyleStack Team"
__description__ = "OOXML Round-Trip Testing Utility"

# Core package imports
from . import core
from . import probe  
from . import convert
from . import analyze
from . import report

__all__ = [
    "core",
    "probe", 
    "convert",
    "analyze",
    "report",
    "__version__",
]