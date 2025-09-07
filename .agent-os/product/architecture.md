# StyleStack Architecture

## System Overview

StyleStack implements a **tokenized single source of truth design system** that transforms W3C-compliant design tokens through a 5-layer resolution system into publication-quality OOXML templates. The architecture prioritizes token-driven consistency while enabling organizational customization.

## Core Architecture Principles

### 1. Token-First Design
All styling decisions flow from design tokens - never raw values embedded in templates or patches. This ensures:
- Global design consistency
- Easy theme switching
- Centralized brand management
- Automated accessibility compliance

### 2. 5-Layer Resolution Hierarchy
```
Core (Community defaults)
 ↓
Fork (Specialized baselines)
 ↓  
Org (Brand overrides)
 ↓
Group (Department needs)
 ↓
Personal (Individual preferences)
```

### 3. YAML-to-OOXML Processing
Templates are generated through a declarative patch system that applies token-aware YAML patches to baseline OOXML templates.

## Technical Stack

### Core Technologies
- **Python 3.9+**: Build system and token processing
- **Click Framework**: CLI interface and command structure
- **PyYAML**: YAML parsing and token file processing
- **lxml**: XML processing and XPath operations for OOXML
- **JSON Schema**: W3C-compliant design token validation

### OOXML Libraries
- **python-pptx**: PowerPoint template generation
- **python-docx**: Word template generation  
- **openpyxl**: Excel template generation

### Quality & Testing
- **pytest**: Unit and integration testing
- **black**: Code formatting
- **mypy**: Static type checking
- **GitHub Actions**: CI/CD automation

## System Components

### 1. Design Token Engine

#### Token Resolution Pipeline
```python
# 5-layer resolution with token references
Core Tokens → Layer Overrides → Flattened Tokens → Reference Resolution → Final Values
```

#### Token Schema (W3C Compliant)
```yaml
colors:
  primary:
    500:
      value: "#0066CC"
      type: "color"
      description: "Primary brand color"
      $extensions:
        stylestack:
          contrast: 7.2  # WCAG AAA compliant
          emu: 0x0066CC  # OOXML hex value
```

#### Implementation: `tools/token_resolver.py`
- Material Web-inspired token architecture
- Dot-notation path resolution (`colors.primary.500`)
- Circular dependency prevention
- Multi-format export (YAML, JSON, CSS)

### 2. Build System

#### CLI Interface: `build.py`
```bash
python build.py --org acme --group marketing --channel present --products potx,dotx,xltx --verbose
```

#### Build Pipeline
1. **Token Resolution**: Resolve 5-layer token hierarchy
2. **Template Assembly**: Apply patches to core OOXML templates
3. **Token Injection**: Replace `{token.references}` with resolved values
4. **Quality Validation**: Accessibility and brand compliance checks
5. **Template Generation**: Output final .potx/.dotx/.xltx files

#### Implementation Status
- ✅ CLI framework and options
- ✅ Token resolution integration  
- 🚨 **Missing**: OOXML processing pipeline

### 3. OOXML Foundation

#### Core Template Structure
```
core/
├── ppt/           # PowerPoint master slides and theme
├── word/          # Word styles and document structure  
└── xl/            # Excel workbook and cell formats
```

#### Patch System
```yaml
# YAML patches reference tokens, never raw values
patches:
  theme:
    colors:
      accent1: "{colors.primary.500}"    # Token reference
      accent2: "{colors.secondary.400}"  # Token reference
  styles:
    heading1:
      font: "{typography.heading.family}"
      size: "{typography.heading.size}"
```

#### Implementation Status
- ✅ Core OOXML templates exist
- ✅ Patch system architecture defined
- 🚨 **Missing**: YAML-to-OOXML processing engine

### 4. Quality System

#### Validation Framework: `tools/validate-2026.py`
- **WCAG AAA Compliance**: Automated contrast ratio checking
- **Anti-Tacky Detection**: Ban unprofessional effects (bevel, glow)
- **Token Integrity**: Validate token references and schema compliance
- **EMU Precision**: Ensure exact positioning accuracy

#### CI/CD Pipeline: `.github/workflows/`
- **Matrix Testing**: Multiple layer combinations across products
- **Quality Gates**: XML linting, accessibility validation
- **Security Scanning**: Macro detection, secret scanning
- **Automated Releases**: Tag-triggered template distribution

## Data Flow Architecture

### Token Resolution Flow
```
1. Load core tokens from tokens/core/
2. Apply fork overrides from tokens/forks/
3. Apply org overrides from tokens/org/ 
4. Apply group overrides from tokens/org/groups/
5. Apply personal overrides from tokens/personal/
6. Apply channel overlays from tokens/channels/
7. Flatten nested structure to dot notation
8. Resolve {token.references} recursively
9. Export resolved tokens
```

### Template Generation Flow (Planned)
```
1. Load core OOXML templates from core/
2. Load YAML patches for current layer stack
3. Apply patches to OOXML DOM tree using XPath
4. Inject resolved token values into XML
5. Validate OOXML structure and accessibility
6. Package final template files
```

## Directory Structure

```
StyleStack/
├── build.py                    # Main build CLI
├── requirements.txt            # Python dependencies
├── 
├── core/                       # Core OOXML templates
│   ├── ppt/theme-2026.xml     # PowerPoint theme baseline
│   ├── word/styles-2026.xml   # Word styles baseline
│   └── xl/styles-2026.xml     # Excel formats baseline
│
├── tokens/                     # Design token system
│   ├── core/                  # Primitive tokens
│   │   ├── colors.yaml        # Color palette
│   │   ├── typography.yaml    # Font and text tokens  
│   │   ├── spacing.yaml       # Layout and spacing
│   │   └── meta.yaml          # System tokens
│   ├── schema/                # Token validation
│   │   └── token.schema.yaml  # W3C-compliant schema
│   └── channels/              # Template variants
│       ├── present.yaml       # Presentation mode
│       ├── doc.yaml           # Document mode  
│       └── finance.yaml       # Finance/accounting mode
│
├── forks/                     # Specialized baselines
│   └── enterprise-defaults/   # Corporate-focused fork
│
├── orgs/                      # Organizational overrides
│   └── acme/                  # ACME Corp example
│       ├── patches.yaml       # Brand overrides
│       ├── groups/            # Department-specific
│       │   ├── marketing/     # Marketing templates
│       │   └── finance/       # Finance templates
│       └── assets/            # Brand assets
│
├── personal/                  # Personal customizations
│   └── john-doe/              # Individual overrides
│
├── tools/                     # Utilities and validation
│   ├── token_resolver.py      # Token resolution engine
│   └── validate-2026.py       # Quality validation
│
├── .github/workflows/         # CI/CD automation
│   ├── ci.yml                # Build and test
│   ├── release.yml           # Release automation  
│   └── token-validation.yml  # Token schema validation
│
└── .agent-os/                # Agent OS integration
    └── product/              # Product documentation
```

## Integration Points

### Office Platform Integration (Planned)
- **Office.js Add-in**: Browser-based add-in for real-time token updates
- **VSTO Add-in**: Native Windows integration with Office desktop
- **Template Gallery**: Centralized template browsing and deployment

### LibreOffice Integration (Planned)  
- **Python-UNO Extension**: Native LibreOffice extension
- **Token-to-ODF Conversion**: OOXML tokens → OpenDocument format
- **Cross-Platform Consistency**: Same design system across Office/LibreOffice

### Google Workspace Integration (Planned)
- **Apps Script Templates**: Google Docs/Sheets/Slides generation
- **Token Sync Service**: Keep Google templates current with token changes
- **Workspace Add-on**: Unified template management

## Security Architecture

### Template Security
- **No Executable Code**: Generated templates contain no macros or scripts
- **Input Validation**: All token values validated against schema
- **Sandboxed Generation**: Template builds run in isolated environments

### Token Security
- **Schema Validation**: Prevent injection attacks through token validation
- **Access Control**: Role-based token and template management
- **Audit Logging**: Track all template generation and changes

## Performance Architecture

### Token Resolution Optimization
- **In-Memory Caching**: Resolved tokens cached for build performance
- **Lazy Loading**: Load tokens and patches on-demand
- **Reference Optimization**: Minimize token resolution iterations

### Build Performance
- **Incremental Builds**: Only rebuild changed templates
- **Parallel Processing**: Multi-threaded template generation
- **Asset Optimization**: Optimize embedded images and resources

## Critical Missing Component

### YAML-to-OOXML Processing Engine 🚨
The architecture is comprehensive and well-designed, but the core processing engine that transforms resolved design tokens into actual OOXML templates is not yet implemented. This is the critical missing piece that would make the entire system functional.

**Required Implementation:**
1. **XPath-based OOXML patching** - Apply YAML patches to XML DOM tree
2. **Token value injection** - Replace `{token.references}` with resolved values  
3. **Template assembly pipeline** - Combine core + patches + tokens → final template
4. **OOXML validation** - Ensure generated XML maintains Office compatibility

Once this processing engine is complete, StyleStack will transform from a well-architected foundation into a fully functional design system that delivers on its mission of replacing chaotic Office templates with tokenized consistency.