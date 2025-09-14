"""Exception classes for OOXML Round-Trip Testing Utility."""


class OOXMLTesterError(Exception):
    """Base exception for all OOXML Tester errors."""
    pass


class PackageError(OOXMLTesterError):
    """Error in OOXML package handling or ZIP operations."""
    pass


class ConversionError(OOXMLTesterError):
    """Error during document conversion process."""
    pass


class ValidationError(OOXMLTesterError):
    """Error in data validation or schema compliance."""
    pass


class PlatformError(OOXMLTesterError):
    """Error with platform-specific operations."""
    pass


class ConfigurationError(OOXMLTesterError):
    """Error in configuration loading or validation."""
    pass


class AnalysisError(OOXMLTesterError):
    """Error during document analysis or comparison."""
    pass


class ReportError(OOXMLTesterError):
    """Error during report generation."""
    pass