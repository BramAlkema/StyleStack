---
sidebar_position: 2
---

# Installation

StyleStack uses a fork-first distribution model designed for institutions that need to maintain their own customized templates while staying synchronized with community improvements.

## Prerequisites

### System Requirements
- **Python 3.9+** for building templates
- **Git** for version control and upstream sync
- **Office 2016+** or **LibreOffice 6.0+** for testing
- **GitHub account** for forking (recommended)

### Development Tools (Optional)
```bash
# Install development dependencies
pip install python-pptx python-docx openpyxl lxml
```

## Fork-First Installation

### Step 1: Fork the Repository

The fork-first model ensures your organization maintains control while benefiting from community updates.

**Via GitHub Web UI:**
1. Visit [https://github.com/stylestack/stylestack](https://github.com/stylestack/stylestack)
2. Click **Fork** in the top-right corner
3. Choose your organization account
4. Name your fork: `stylestack-[org-name]`

**Via GitHub CLI:**
```bash
# Fork to your organization
gh repo fork stylestack/stylestack --org your-org --clone

# Or fork to personal account
gh repo fork stylestack/stylestack --clone
```

### Step 2: Clone Your Fork

```bash
# Clone your fork
git clone https://github.com/your-org/stylestack-your-org.git
cd stylestack-your-org

# Set up upstream remote for sync
git remote add upstream https://github.com/stylestack/stylestack.git
git remote -v
```

### Step 3: Initial Build Test

```bash
# Test build system
python build.py --org test --channel present --products potx

# Verify output
ls -la BetterDefaults-test-present-*.potx
```

## Organizational Setup

### Directory Structure

Your fork will have this structure:
```
stylestack-your-org/
├─ core/                   # Community baseline (don't modify)
├─ org/your-org/          # Your customizations
│  ├─ patches.json        # JSON-based overrides
│  ├─ assets/            # Brand assets (logos, etc.)
│  └─ channels/          # Custom channel variants
├─ build.py              # Build orchestrator
└─ .github/workflows/    # CI/CD automation
```

### Create Organization Directory

```bash
# Create your org directory
mkdir -p org/your-org/assets
mkdir -p org/your-org/channels

# Initialize basic configuration
cat > org/your-org/patches.json << EOF
organization:
  name: "Your Organization"
  short_name: "your-org"
  
branding:
  primary_color: "#003366"
  secondary_color: "#0066CC"
  accent_color: "#FF6600"
  
fonts:
  heading: "Arial"
  body: "Calibri"
  
assets:
  logo: "assets/logo.png"
  watermark: "assets/watermark.png"
EOF
```

### Add Brand Assets

```bash
# Copy your organization's assets
cp /path/to/your-logo.png org/your-org/assets/logo.png
cp /path/to/watermark.png org/your-org/assets/watermark.png

# Verify assets
file org/your-org/assets/*
```

## Configuration Options

### patches.json Structure

```json
organization:
  name: "University of Example"
  short_name: "uoe"
  domain: "example.edu"
  
branding:
  primary_color: "#002856"     # Navy blue
  secondary_color: "#FFD700"   # Gold
  accent_color: "#C41E3A"      # Red
  
fonts:
  heading: "Montserrat"
  body: "Source Sans Pro"
  monospace: "Fira Code"
  
assets:
  logo: "assets/university-logo.png"
  seal: "assets/official-seal.png"
  watermark: "assets/draft-watermark.png"
  
accessibility:
  high_contrast: true
  dyslexic_friendly: true
  
compliance:
  gdpr: true
  ferpa: true          # For educational institutions
  hipaa: false
  
localization:
  primary_language: "en-US"
  supported_languages: ["en-US", "es-ES", "fr-FR"]
```

### Channel Customization

Create custom channels for different use cases:

```bash
# Academic presentation channel
cat > org/your-org/channels/academic.json << EOF
name: "Academic Presentations"
description: "For research presentations and lectures"
target_products: ["potx"]

overrides:
  slide_layouts:
    title_slide: "academic-title"
    content_slide: "academic-content"
  
  fonts:
    size_scale: 1.1  # Larger fonts for projection
    
  colors:
    emphasis: "#C41E3A"  # University red for highlights
EOF
```

## Build System Setup

### Local Builds

```bash
# Build templates for your organization
python build.py --org your-org --channel present --products potx dotx xltx

# Build specific channel
python build.py --org your-org --channel academic --products potx

# Build with debug output
python build.py --org your-org --channel present --products potx --verbose
```

### Automated Builds (CI/CD)

Enable GitHub Actions for automated builds:

```bash
# Copy CI template
cp .github/workflows/build-templates.yml.example .github/workflows/build-templates.yml

# Customize for your organization
sed -i 's/REPLACE_ORG/your-org/g' .github/workflows/build-templates.yml
```

Configure secrets in your GitHub repository:
- `RELEASE_TOKEN` - GitHub token for releases
- `ORG_CONFIG` - Base64 encoded org configuration (optional)

### Testing Installation

```bash
# Run validation tests
python tools/validate.py --org your-org --all-channels

# Test template loading
python tools/test-templates.py --org your-org --products potx dotx xltx
```

## Network/Enterprise Considerations

### Firewall Configuration

StyleStack requires these connections:
- **GitHub.com** (HTTPS) - Repository access and releases
- **PyPI.org** (HTTPS) - Python package dependencies
- **Fonts.google.com** (HTTPS) - Font downloads (if using Google Fonts)

### Proxy Configuration

```bash
# Configure Git for corporate proxy
git config --global http.proxy http://proxy.company.com:8080
git config --global https.proxy https://proxy.company.com:8080

# Configure pip for proxy
pip install --proxy http://proxy.company.com:8080 -r requirements.txt
```

### Air-Gapped Environments

For environments without internet access:
1. Download StyleStack release bundle
2. Include all Python dependencies
3. Bundle required fonts
4. Use local package index

```bash
# Create offline bundle
pip download -r requirements.txt -d vendor/
wget https://github.com/stylestack/stylestack/archive/main.zip
```

## Verification

### Template Installation Test

```bash
# Build and test templates
python build.py --org your-org --channel present --products potx dotx xltx

# Verify output files
ls -la BetterDefaults-your-org-*

# Test in Office applications
# (Manual step - open each template in respective app)
```

### Sync Test

```bash
# Test upstream synchronization
git fetch upstream
git log --oneline upstream/main ^main

# Test merge (dry run)
git merge --no-commit --no-ff upstream/main
git merge --abort
```

## Next Steps

- [Customize design tokens](../design-tokens/customization.md)
- [Add branding elements](../customization/branding.md)
- [Set up CI/CD pipeline](../deployment/ci-cd.md)
- [Learn fork management](../fork-management/customizing.md)

## Troubleshooting

**Build fails with permission errors:**
```bash
# Fix file permissions
chmod +x build.py
find . -name "*.py" -exec chmod +x {} \;
```

**Python dependencies missing:**
```bash
# Install with user flag if system install fails
pip install --user -r requirements.txt
```

**Git upstream sync issues:**
```bash
# Reset to clean state
git reset --hard HEAD
git clean -fd
git fetch upstream
```

**Template not loading in Office:**
- Verify file extensions (.potx, .dotx, .xltx)
- Check Office templates folder location
- Restart Office applications
- Review Office security settings