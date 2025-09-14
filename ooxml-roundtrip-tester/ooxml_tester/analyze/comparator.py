"""Document comparator stub - to be implemented."""

from pathlib import Path


class DocumentComparator:
    """Compares OOXML documents for differences."""
    
    def __init__(self, config):
        self.config = config
    
    def compare(self, original: Path, converted: Path):
        """Compare two documents."""
        # Stub implementation
        return None