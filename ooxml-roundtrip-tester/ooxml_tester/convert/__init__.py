"""Cross-platform document conversion engine.

This module handles document conversion across different Office platforms:
- Microsoft Office automation (COM/AppleScript)
- LibreOffice automation (UNO API)
- Google Workspace integration (Apps Script API)
- Platform detection and adapter pattern
- Conversion result validation
"""

from .engine import ConversionEngine

# Stub classes - to be implemented
class Platform:
    pass

class MicrosoftOfficePlatform:
    pass

class LibreOfficePlatform:
    pass

class GoogleWorkspacePlatform:
    pass

class ConversionAdapter:
    pass

class OfficeAdapter:
    pass

class LibreOfficeAdapter:
    pass

class GoogleAdapter:
    pass

__all__ = [
    "ConversionEngine",
    "Platform",
    "MicrosoftOfficePlatform",
    "LibreOfficePlatform", 
    "GoogleWorkspacePlatform",
    "ConversionAdapter",
    "OfficeAdapter",
    "LibreOfficeAdapter",
    "GoogleAdapter",
]