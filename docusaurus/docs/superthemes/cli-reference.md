# CLI Reference

Complete command-line interface reference for StyleStack SuperTheme generation, validation, and management.

## Overview

StyleStack provides a comprehensive CLI through the `build.py` script that supports SuperTheme generation alongside traditional OOXML template processing.

```bash
python build.py [OPTIONS]
```

## SuperTheme Commands

### Basic SuperTheme Generation

```bash
python build.py --supertheme --designs DESIGN_DIR --ratios RATIOS --out OUTPUT_FILE
```

**Parameters:**
- `--supertheme`: Enable SuperTheme generation mode
- `--designs`: Path to directory containing design variant JSON files
- `--ratios`: Comma-separated list of aspect ratios
- `--out`: Output SuperTheme file path (.thmx extension)

### Command Reference

#### --supertheme
**Description**: Enable Microsoft SuperTheme package (.thmx) generation mode.

**Usage**: `--supertheme`

**Example**:
```bash
python build.py --supertheme --designs corporate_designs --ratios 16:9,4:3 --out theme.thmx
```

#### --designs
**Description**: Directory containing design variant JSON files or path to single JSON file.

**Usage**: `--designs PATH`

**Supported formats**:
- Directory with multiple .json files
- Single .json file path
- Relative or absolute paths

**Examples**:
```bash
# Directory with multiple design variants
python build.py --supertheme --designs ./my_designs --ratios 16:9 --out multi.thmx

# Single design variant file
python build.py --supertheme --designs corporate_blue.json --ratios 16:9,4:3 --out single.thmx

# Absolute path
python build.py --supertheme --designs /path/to/designs --ratios 16:9 --out abs.thmx
```

#### --ratios
**Description**: Aspect ratios for SuperTheme generation (comma-separated).

**Usage**: `--ratios RATIO1,RATIO2,...`

**Supported formats**:
- Standard ratios: `16:9`, `4:3`, `a4`, `letter`
- Custom ratios: `21:9`, `16:10`, `1:1`, `9:16`
- Decimal ratios: `1.78:1`, `2.39:1`

**Examples**:
```bash
# Standard widescreen and traditional
python build.py --supertheme --designs designs/ --ratios 16:9,4:3 --out standard.thmx

# All standard formats
python build.py --supertheme --designs designs/ --ratios 16:9,4:3,a4,letter --out complete.thmx

# Custom ultra-wide and square
python build.py --supertheme --designs designs/ --ratios 21:9,1:1 --out custom.thmx

# Mixed standard and custom
python build.py --supertheme --designs designs/ --ratios 16:9,21:9,2.39:1 --out mixed.thmx
```

#### --out
**Description**: Output file path for generated SuperTheme package.

**Usage**: `--out FILEPATH`

**Requirements**:
- File extension should be `.thmx`
- Directory must exist or be creatable
- Write permissions required

**Examples**:
```bash
# Simple filename
python build.py --supertheme --designs designs/ --ratios 16:9 --out theme.thmx

# With directory structure
python build.py --supertheme --designs designs/ --ratios 16:9 --out themes/corporate.thmx

# Absolute path
python build.py --supertheme --designs designs/ --ratios 16:9 --out /output/theme.thmx
```

### Global Options

#### -v, --verbose
**Description**: Enable verbose output with detailed progress information.

**Usage**: `-v` or `--verbose`

**Output includes**:
- Design variant loading details
- Aspect ratio calculations
- Theme generation progress  
- Validation results
- Performance metrics

**Example**:
```bash
python build.py --supertheme --designs designs/ --ratios 16:9,4:3 --out theme.thmx --verbose
```

**Sample verbose output**:
```
🎨 StyleStack SuperTheme Generator
📁 Loading design variants from: designs/
   ✅ Loaded: Corporate Blue (corporate_blue.json)
   ✅ Loaded: Modern Green (modern_green.json) 
   ✅ Loaded: Elegant Purple (elegant_purple.json)
📐 Processing aspect ratios: 16:9, 4:3
   ✅ 16:9 → 10058400×5657600 EMUs (widescreen)
   ✅ 4:3 → 9144000×6858000 EMUs (traditional)
🔄 Generating design variants...
   ✅ Corporate Blue → 2 aspect ratio variants (0.1s)
   ✅ Modern Green → 2 aspect ratio variants (0.1s)
   ✅ Elegant Purple → 2 aspect ratio variants (0.1s)
📋 Generating themeVariantManager.xml for 6 variants
📦 Packaging SuperTheme: theme.thmx
   📄 Adding core files: [Content_Types].xml, relationships
   🎨 Adding 6 theme variants
   📐 Adding aspect ratio configurations
✅ Generated SuperTheme: 67 files, 0.08 MB
🔍 Validation: ✅ VALID (0 errors, 0 warnings)
⚡ Performance: 0.34s generation, 6 variants
```

## Advanced Usage

### Multiple Aspect Ratio Scenarios

**Presentation-focused package:**
```bash
python build.py --supertheme \
  --designs presentation_themes/ \
  --ratios 16:9,4:3 \
  --out presentation_supertheme.thmx \
  --verbose
```

**Document-focused package:**
```bash
python build.py --supertheme \
  --designs document_themes/ \
  --ratios a4,letter \
  --out document_supertheme.thmx
```

**Video content package:**
```bash
python build.py --supertheme \
  --designs video_themes/ \
  --ratios 16:9,21:9,2.39:1 \
  --out video_supertheme.thmx
```

**Mobile-first package:**
```bash
python build.py --supertheme \
  --designs mobile_themes/ \
  --ratios 9:16,1:1,4:5 \
  --out mobile_supertheme.thmx
```

### Batch Generation Workflows

**Generate multiple SuperThemes:**
```bash
# Corporate themes
python build.py --supertheme --designs corporate/ --ratios 16:9,4:3 --out corporate.thmx

# Marketing themes  
python build.py --supertheme --designs marketing/ --ratios 16:9,1:1 --out marketing.thmx

# Technical themes
python build.py --supertheme --designs technical/ --ratios 16:9,4:3,a4 --out technical.thmx
```

**Scripted batch generation:**
```bash
#!/bin/bash
# batch_generate.sh

DESIGNS_DIR="design_variants"
OUTPUT_DIR="superthemes"

# Create output directory
mkdir -p $OUTPUT_DIR

# Generate for each department
for dept in corporate marketing technical finance; do
  echo "Generating SuperTheme for $dept..."
  python build.py --supertheme \
    --designs "$DESIGNS_DIR/$dept" \
    --ratios 16:9,4:3,a4 \
    --out "$OUTPUT_DIR/${dept}_supertheme.thmx" \
    --verbose
done

echo "Batch generation complete!"
```

### Integration with CI/CD

**GitHub Actions workflow:**
```yaml
name: SuperTheme Generation

on:
  push:
    branches: [main]
    paths: ['design_variants/**']

jobs:
  generate-superthemes:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        
    - name: Generate Corporate SuperTheme
      run: |
        python build.py --supertheme \
          --designs design_variants/corporate \
          --ratios 16:9,4:3,a4,letter \
          --out corporate_supertheme.thmx \
          --verbose
          
    - name: Validate SuperTheme
      run: |
        python -m tools.supertheme_validator corporate_supertheme.thmx
        
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: superthemes
        path: "*.thmx"
```

## Error Handling

### Common Errors and Solutions

#### Design Variants Not Found

**Error**:
```
Error: No design variants found in directory: designs/
```

**Solutions**:
```bash
# Check directory exists and contains .json files
ls -la designs/

# Verify JSON file format
python -m json.tool designs/corporate.json

# Use absolute path if relative path issues
python build.py --supertheme --designs /absolute/path/to/designs --ratios 16:9 --out theme.thmx
```

#### Invalid Aspect Ratio Format

**Error**:
```
Error: Invalid aspect ratio format: 16x9
```

**Solutions**:
```bash
# Use colon separator
python build.py --supertheme --designs designs/ --ratios 16:9,4:3 --out theme.thmx  # ✅ Correct

# Not multiplication symbol
python build.py --supertheme --designs designs/ --ratios 16x9,4x3 --out theme.thmx  # ❌ Wrong
```

#### Output Directory Issues

**Error**:
```
Error: Cannot write to output file: /nonexistent/theme.thmx
```

**Solutions**:
```bash
# Create output directory
mkdir -p output_themes
python build.py --supertheme --designs designs/ --ratios 16:9 --out output_themes/theme.thmx

# Check permissions
ls -la output_directory/

# Use current directory
python build.py --supertheme --designs designs/ --ratios 16:9 --out theme.thmx
```

#### JSON Parsing Errors

**Error**:
```
Error: Invalid JSON in file: designs/corporate.json
```

**Solutions**:
```bash
# Validate JSON syntax
python -m json.tool designs/corporate.json

# Check for common JSON issues:
# - Missing commas
# - Trailing commas
# - Unquoted keys
# - Invalid escape characters
```

## Performance Optimization

### Command-Line Performance Tips

**For large variant sets:**
```bash
# Use fewer aspect ratios for faster generation
python build.py --supertheme --designs large_set/ --ratios 16:9 --out fast.thmx

# Generate in batches for memory efficiency
python build.py --supertheme --designs batch1/ --ratios 16:9,4:3 --out batch1.thmx
python build.py --supertheme --designs batch2/ --ratios 16:9,4:3 --out batch2.thmx
```

**Monitor performance:**
```bash
# Use verbose mode to see timing
python build.py --supertheme --designs designs/ --ratios 16:9,4:3 --out theme.thmx --verbose

# Time the generation
time python build.py --supertheme --designs designs/ --ratios 16:9,4:3 --out theme.thmx
```

## Debugging and Troubleshooting

### Debug Mode

**Enable maximum verbosity:**
```bash
python build.py --supertheme \
  --designs designs/ \
  --ratios 16:9,4:3 \
  --out debug.thmx \
  --verbose
```

### Validation Testing

**Test generated SuperTheme:**
```bash
# Generate with validation
python build.py --supertheme --designs designs/ --ratios 16:9 --out test.thmx --verbose

# Standalone validation
python -c "
from tools.supertheme_validator import SuperThemeValidator
validator = SuperThemeValidator()
with open('test.thmx', 'rb') as f:
    result = validator.validate_package(f.read())
print(validator.generate_validation_report(result))
"
```

### File System Debugging

**Check generated package contents:**
```bash
# Extract and examine SuperTheme
mkdir extracted_theme
cd extracted_theme
unzip ../theme.thmx

# View package structure
tree .

# Examine specific files
cat "[Content_Types].xml"
cat "themeVariants/themeVariantManager.xml"
```

## Best Practices

### 1. File Organization

**✅ Recommended structure:**
```
project/
├── design_variants/
│   ├── corporate/
│   │   ├── blue.json
│   │   ├── green.json
│   │   └── purple.json
│   ├── seasonal/
│   │   ├── holiday.json
│   │   └── summer.json
│   └── functional/
│       ├── financial.json
│       └── technical.json
├── output/
│   ├── corporate_themes.thmx
│   ├── seasonal_themes.thmx
│   └── functional_themes.thmx
└── scripts/
    └── generate_all.sh
```

### 2. Command Patterns

**✅ Development workflow:**
```bash
# 1. Quick test with single ratio
python build.py --supertheme --designs designs/ --ratios 16:9 --out test.thmx

# 2. Full generation with validation
python build.py --supertheme --designs designs/ --ratios 16:9,4:3,a4 --out full.thmx --verbose

# 3. Production generation
python build.py --supertheme --designs designs/ --ratios 16:9,4:3,a4,letter --out production.thmx
```

### 3. Error Prevention

**✅ Validation before generation:**
```bash
# Validate design variants first
find designs/ -name "*.json" -exec python -m json.tool {} \; > /dev/null

# Check output directory exists
mkdir -p output/

# Generate with error checking
python build.py --supertheme --designs designs/ --ratios 16:9,4:3 --out output/theme.thmx --verbose
if [ $? -eq 0 ]; then
    echo "✅ SuperTheme generation successful"
else
    echo "❌ SuperTheme generation failed"
    exit 1
fi
```

This comprehensive CLI reference provides everything you need to effectively use StyleStack's SuperTheme generation capabilities in development, testing, and production environments.