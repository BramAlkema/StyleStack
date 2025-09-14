# OOXML Round-Trip Testing Utility

A comprehensive testing framework for validating OOXML document compatibility across different Office platforms through round-trip conversion analysis.

## Overview

This utility helps ensure that Office templates and documents maintain formatting integrity when processed through different platforms:

- **Microsoft Office** (Windows/macOS)
- **LibreOffice/OpenOffice** (Cross-platform)  
- **Google Workspace** (Web-based)

## Key Features

- **Probe Generation**: Create test documents with specific OOXML features
- **Cross-Platform Conversion**: Automated round-trip testing across office suites
- **Comprehensive Analysis**: Structural, semantic, and visual difference detection
- **Multiple Report Formats**: JSON, CSV, HTML, and PDF output options
- **Carrier Variable Validation**: Verify StyleStack design token substitution

## Installation

```bash
pip install -e .
```

## Quick Start

```bash
# Generate probe files
ooxml-tester probe --output ./probes --format pptx --features themes,styles

# Run round-trip tests
ooxml-tester test --input ./probes --platforms office,libreoffice

# Generate compatibility report  
ooxml-tester report --format html --output ./reports
```

## Documentation

- [Architecture Overview](docs/architecture.md)
- [Platform Support](docs/platforms.md)
- [API Reference](docs/api.md)

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=ooxml_tester
```

## License

MIT License - see [LICENSE](LICENSE) for details.