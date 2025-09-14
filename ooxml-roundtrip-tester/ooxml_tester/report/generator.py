"""Report generator stub - to be implemented."""

from pathlib import Path


class ReportGenerator:
    """Generates compatibility reports."""
    
    def __init__(self, config):
        self.config = config
    
    def generate(self, input_dir: Path, output_file: Path, format: str, template: str) -> Path:
        """Generate compatibility report."""
        # Stub implementation
        return output_file