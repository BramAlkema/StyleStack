# SuperThemes Troubleshooting

Comprehensive troubleshooting guide for common SuperTheme generation, validation, and deployment issues.

## Quick Diagnostic Commands

**Before diving into specific issues, run these diagnostic commands:**

```bash
# Check StyleStack installation
python -c "from tools.supertheme_generator import SuperThemeGenerator; print('✅ SuperTheme generator available')"

# Validate design variants syntax
find design_variants/ -name "*.json" -exec python -m json.tool {} \; > /dev/null && echo "✅ All JSON files valid"

# Test basic generation
python build.py --supertheme --designs design_variants/ --ratios 16:9 --out test.thmx --verbose

# Validate generated package
python -c "
from tools.supertheme_validator import SuperThemeValidator
with open('test.thmx', 'rb') as f:
    result = SuperThemeValidator().validate_package(f.read())
    print('✅ Valid' if result.is_valid else '❌ Invalid')
"
```

## Generation Issues

### 1. No Design Variants Found

**❌ Error:**
```
Error: No design variants found in directory: designs/
StyleStack SuperTheme Generator failed with exit code 1
```

**✅ Solutions:**

**Check directory structure:**
```bash
# Verify directory exists
ls -la designs/

# Check for JSON files
find designs/ -name "*.json" -type f

# Expected structure:
designs/
├── corporate_blue.json
├── modern_green.json
└── elegant_purple.json
```

**Verify JSON file format:**
```bash
# Test each JSON file
for file in designs/*.json; do
    echo "Checking $file..."
    python -m json.tool "$file" > /dev/null || echo "❌ Invalid JSON: $file"
done
```

**Fix file permissions:**
```bash
# Make files readable
chmod 644 designs/*.json

# Make directory accessible  
chmod 755 designs/
```

### 2. Invalid JSON Format

**❌ Error:**
```
Error: Invalid JSON in file: designs/corporate.json
JSONDecodeError: Expecting ',' delimiter: line 15 column 5 (char 342)
```

**✅ Solutions:**

**Common JSON syntax issues:**
```json
// ❌ Wrong: Trailing comma
{
  "name": "Corporate Blue",
  "colors": {
    "primary": "#0066CC",  // <- Remove this comma
  }
}

// ✅ Correct: No trailing comma
{
  "name": "Corporate Blue", 
  "colors": {
    "primary": "#0066CC"
  }
}

// ❌ Wrong: Comments not allowed
{
  "name": "Corporate Blue",  // This comment breaks JSON
  "colors": {
    "primary": "#0066CC"
  }
}

// ✅ Correct: No comments
{
  "name": "Corporate Blue",
  "colors": {
    "primary": "#0066CC"
  }
}
```

**Validate and fix JSON:**
```bash
# Validate JSON syntax
python -m json.tool designs/corporate.json

# Pretty-print to find issues
python -c "
import json
with open('designs/corporate.json', 'r') as f:
    try:
        data = json.load(f)
        print('✅ Valid JSON')
    except json.JSONDecodeError as e:
        print(f'❌ JSON Error: {e}')
"
```

### 3. Invalid Aspect Ratio Format

**❌ Error:**
```
Error: Invalid aspect ratio format: 16x9
Supported formats: 16:9, 4:3, a4, letter, or custom ratios like 21:9
```

**✅ Solutions:**

**Correct aspect ratio formats:**
```bash
# ✅ Correct formats
python build.py --supertheme --designs designs/ --ratios 16:9,4:3 --out theme.thmx
python build.py --supertheme --designs designs/ --ratios 16:9,a4,letter --out theme.thmx  
python build.py --supertheme --designs designs/ --ratios 21:9,1:1,2.39:1 --out theme.thmx

# ❌ Wrong formats
python build.py --supertheme --designs designs/ --ratios 16x9,4x3 --out theme.thmx      # Wrong separator
python build.py --supertheme --designs designs/ --ratios 16-9,4-3 --out theme.thmx      # Wrong separator
python build.py --supertheme --designs designs/ --ratios widescreen --out theme.thmx     # Use 16:9 instead
```

### 4. Output File Issues

**❌ Error:**
```
Error: Cannot write to output file: /protected/theme.thmx
Permission denied
```

**✅ Solutions:**

**Check output directory permissions:**
```bash
# Create output directory if needed
mkdir -p output_themes

# Check write permissions
touch output_themes/test.txt && rm output_themes/test.txt && echo "✅ Write permissions OK"

# Fix permissions if needed
chmod 755 output_themes/
```

**Use accessible output path:**
```bash
# Current directory (usually safe)
python build.py --supertheme --designs designs/ --ratios 16:9 --out theme.thmx

# User home directory
python build.py --supertheme --designs designs/ --ratios 16:9 --out ~/themes/theme.thmx

# Temporary directory
python build.py --supertheme --designs designs/ --ratios 16:9 --out /tmp/theme.thmx
```

## Validation Issues

### 1. Package Structure Errors

**❌ Error:**
```
❌ INVALID SuperTheme
Errors: 3
  • [structure] Missing required file: themeVariants/themeVariantManager.xml
  • [structure] Missing themeVariants/_rels/themeVariantManager.xml.rels
  • [content_types] Missing content type: application/vnd.ms-powerpoint.themeVariantManager+xml
```

**✅ Solutions:**

**Regenerate SuperTheme with verbose logging:**
```bash
python build.py --supertheme --designs designs/ --ratios 16:9 --out fixed.thmx --verbose
```

**Check generated package contents:**
```bash
# Extract package to inspect
mkdir temp_inspection
cd temp_inspection
unzip ../theme.thmx

# Check required files exist
ls -la
ls -la themeVariants/
ls -la themeVariants/_rels/
```

**Force regeneration with clean cache:**
```bash
# Clear any cached data
rm -rf __pycache__/
rm -rf tools/__pycache__/

# Regenerate
python build.py --supertheme --designs designs/ --ratios 16:9 --out clean.thmx --verbose
```

### 2. XML Namespace Issues  

**❌ Error:**
```
❌ INVALID SuperTheme  
Errors: 2
  • [namespaces] Missing drawingml namespace: http://schemas.openxmlformats.org/drawingml/2006/main
  • [namespaces] Missing presentationml namespace: http://schemas.openxmlformats.org/presentationml/2006/main
```

**✅ Solutions:**

This indicates a bug in the SuperTheme generator. Check StyleStack version and update:

```bash
# Check StyleStack version
git log --oneline -5

# Pull latest updates
git pull origin main

# Regenerate with updated code
python build.py --supertheme --designs designs/ --ratios 16:9 --out updated.thmx --verbose
```

### 3. Theme Element Warnings

**❌ Warning:**
```
⚠️ Warnings: 6
  • [theme] Missing themeElements in theme in themeVariants/variant1/theme/theme/theme1.xml
  • [theme] Missing clrScheme in theme in themeVariants/variant1/theme/theme/theme1.xml
  • [theme] Missing fontScheme in theme in themeVariants/variant1/theme/theme/theme1.xml
```

**✅ Solutions:**

These are typically warnings, not errors, but can be addressed:

**Enhance design variant definitions:**
```json
{
  "name": "Complete Design",
  "colors": {
    "brand": {
      "primary": "#0066CC",
      "secondary": "#4A90E2"
    },
    "neutral": {
      "dark": "#2C3E50",
      "light": "#ECF0F1"
    }
  },
  "typography": {
    "heading": {
      "font": "Montserrat",
      "weight": "600"
    },
    "body": {
      "font": "Source Sans Pro", 
      "weight": "400"
    }
  }
}
```

## PowerPoint Integration Issues

### 1. Theme Not Visible in PowerPoint

**❌ Issue:** SuperTheme doesn't appear in PowerPoint's Design gallery

**✅ Solutions:**

**Check installation location:**

**Windows:**
```cmd
# Copy to PowerPoint themes directory
copy theme.thmx "%AppData%\Microsoft\Templates\Document Themes\"

# Alternative location
copy theme.thmx "%ProgramFiles%\Microsoft Office\Templates\Document Themes\"
```

**Mac:**
```bash
# Copy to PowerPoint themes directory  
cp theme.thmx ~/Library/Group\ Containers/UBF8T346G9.Office/User\ Content/Themes/

# Alternative location
cp theme.thmx /Applications/Microsoft\ PowerPoint.app/Contents/Resources/DLC/Themes/
```

**Restart PowerPoint after copying themes.**

### 2. Theme Doesn't Switch Aspect Ratios

**❌ Issue:** Changing slide size doesn't update theme appearance

**✅ Solutions:**

**Verify variant count:**
```bash
# Check SuperTheme contains multiple variants
python -c "
from tools.supertheme_validator import SuperThemeValidator
with open('theme.thmx', 'rb') as f:
    result = SuperThemeValidator().validate_package(f.read())
    print(f'Variants: {result.variant_count}')
"
```

**Test with simple case:**
```bash
# Generate minimal test case
python build.py --supertheme --designs simple_design.json --ratios 16:9,4:3 --out test.thmx --verbose
```

**Check PowerPoint version:**
- SuperThemes require PowerPoint 2016 or later
- Office 365 recommended for best compatibility

### 3. Theme Colors Not Applying

**❌ Issue:** Custom colors from design variants not visible in PowerPoint

**✅ Solutions:**

**Verify color definitions in design variant:**
```json
{
  "colors": {
    "brand": {
      "primary": "#0066CC",    // Must be hex format
      "secondary": "#4A90E2"   // 6-digit hex required
    }
  }
}
```

**Check Office color format:**
```bash
# Hex colors should be 6 digits
# ✅ Correct: #0066CC
# ❌ Wrong: #06C (3 digits)
# ❌ Wrong: rgb(0, 102, 204)
```

## Performance Issues

### 1. Slow Generation

**❌ Issue:** SuperTheme generation takes too long

**✅ Solutions:**

**Check variant count:**
```bash
# Calculate total variants: designs × aspect_ratios
# 10 designs × 6 ratios = 60 variants (may be slow)
# 3 designs × 3 ratios = 9 variants (should be fast)

# Reduce variants for testing
python build.py --supertheme --designs designs/ --ratios 16:9 --out fast.thmx
```

**Monitor performance:**
```bash
# Use verbose mode to see timing
python build.py --supertheme --designs designs/ --ratios 16:9,4:3 --out theme.thmx --verbose

# Time the generation
time python build.py --supertheme --designs designs/ --ratios 16:9 --out theme.thmx
```

**Optimize design variants:**
```json
{
  // Remove complex calculations
  "typography": {
    "heading": {
      "size": "44pt"  // Simple value instead of complex aspect ratio logic
    }
  }
}
```

### 2. Large File Sizes

**❌ Issue:** Generated SuperTheme files are too large

**✅ Solutions:**

**Check file size:**
```bash
ls -lh theme.thmx
# Target: < 5MB recommended, < 10MB maximum
```

**Reduce variant count:**
```bash
# Generate fewer variants
python build.py --supertheme --designs designs/ --ratios 16:9,4:3 --out smaller.thmx

# Use fewer design variants
python build.py --supertheme --designs essential_designs/ --ratios 16:9,4:3 --out minimal.thmx
```

**Optimize design variants:**
```json
{
  // Remove unnecessary assets
  "assets": {
    // Remove large images or complex graphics
  },
  
  // Simplify complex tokens
  "spacing": {
    "margin": "24pt"  // Simple value instead of complex calculations
  }
}
```

## Platform-Specific Issues

### Windows Issues

**PowerShell Execution Policy:**
```powershell
# If scripts don't run
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run StyleStack
python build.py --supertheme --designs designs/ --ratios 16:9 --out theme.thmx
```

**Path Issues:**
```cmd
# Use forward slashes or escaped backslashes
python build.py --supertheme --designs "C:/projects/designs" --ratios 16:9 --out theme.thmx

# Or escaped backslashes  
python build.py --supertheme --designs "C:\\projects\\designs" --ratios 16:9 --out theme.thmx
```

### Mac Issues

**Python Version:**
```bash
# Check Python version
python3 --version

# Use python3 if python points to old version
python3 build.py --supertheme --designs designs/ --ratios 16:9 --out theme.thmx
```

**File Permissions:**
```bash
# Fix file permissions
chmod +x build.py
chmod 644 designs/*.json
```

### Linux Issues

**Missing Dependencies:**
```bash
# Install required packages
pip install lxml elementtree

# Check dependencies
python -c "import lxml; print('✅ lxml available')"
```

## Advanced Troubleshooting

### Debug Mode Investigation

**Enable maximum debugging:**
```python
# debug_generation.py
import logging
from tools.supertheme_generator import SuperThemeGenerator

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Create generator with verbose mode
generator = SuperThemeGenerator(verbose=True)

# Load design variants manually
import json
with open('designs/corporate.json', 'r') as f:
    design_variant = json.load(f)

# Generate with debug info
try:
    result = generator.generate_supertheme(
        {'corporate': design_variant},
        ['aspectRatios.widescreen_16_9']
    )
    print(f"✅ Generated {len(result)} bytes")
except Exception as e:
    print(f"❌ Generation failed: {e}")
    import traceback
    traceback.print_exc()
```

### Package Inspection

**Examine generated package structure:**
```bash
# Extract package
mkdir -p inspection/
cd inspection/
unzip ../theme.thmx

# Check structure
find . -type f | sort

# Examine XML files
for xml in $(find . -name "*.xml"); do
    echo "=== $xml ==="
    xmllint --format "$xml" 2>/dev/null || cat "$xml"
    echo
done
```

### Memory Usage Analysis

**Monitor memory during generation:**
```python
# memory_test.py
import psutil
import os
from tools.supertheme_generator import SuperThemeGenerator

def monitor_memory():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # MB

print(f"Initial memory: {monitor_memory():.1f} MB")

generator = SuperThemeGenerator()
print(f"After generator creation: {monitor_memory():.1f} MB")

# Load test design
with open('designs/corporate.json') as f:
    design_variant = json.load(f)
    
result = generator.generate_supertheme(
    {'test': design_variant},
    ['aspectRatios.widescreen_16_9']
)

print(f"After generation: {monitor_memory():.1f} MB")
print(f"Package size: {len(result)/1024/1024:.2f} MB")
```

## Getting Help

### Community Resources

**GitHub Issues:**
- Search existing issues: `https://github.com/stylestack/stylestack/issues`
- Create new issue with reproduction steps
- Include StyleStack version and error messages

**Debugging Information to Include:**
```bash
# Collect system information
python --version
pip list | grep lxml
ls -la designs/
python build.py --supertheme --designs designs/ --ratios 16:9 --out debug.thmx --verbose 2>&1 | tee debug.log
```

**Minimal Reproduction Case:**
```bash
# Create minimal failing case
mkdir minimal_repro
cd minimal_repro

# Create simple design variant
cat > design.json << EOF
{
  "name": "Test Design",
  "colors": {
    "brand": {"primary": "#0066CC"}
  }
}
EOF

# Test generation
python ../build.py --supertheme --designs design.json --ratios 16:9 --out test.thmx --verbose
```

This comprehensive troubleshooting guide should help you resolve most SuperTheme issues. For persistent problems, collect the debugging information above and create an issue in the StyleStack repository.