# GitHub Actions Folder Watch Examples

## Trigger Events

The token extraction workflow triggers on:

```json
on:
  push:
    paths:
      # Microsoft Office formats
      - 'extract/**/*.pptx'
      - 'extract/**/*.potx'  
      - 'extract/**/*.ppsx'
      # OpenOffice/LibreOffice formats
      - 'extract/**/*.odp'
      - 'extract/**/*.otp'
      - 'extract/**/*.ods'
      - 'extract/**/*.ots'
      - 'extract/**/*.odt'
      - 'extract/**/*.ott'
```

## Example Workflows

### 1. Single File Drop

**Action**: Add Office or OpenOffice files
```bash
git add extract/my-presentation.pptx extract/slides.odp extract/report.odt
git commit -m "Add files for token extraction"
git push
```

**Result**: GitHub Actions automatically runs and commits:
```
extract/
├── my-presentation.pptx        # Microsoft Office
├── slides.odp                 # LibreOffice Impress  
├── report.odt                 # LibreOffice Writer
└── extracted/
    ├── my-presentation-tokens.json
    ├── slides-tokens.json
    ├── report-tokens.json
    └── [filename]-assets/
        ├── logos/
        │   └── company-logo.png
        ├── icons/
        │   ├── arrow-icon.svg
        │   └── check-icon.png
        └── images/
            └── hero-image.jpg
```

### 2. Batch Processing

**Action**: Add multiple files in one commit
```bash
git add extract/deck1.pptx extract/deck2.pptx extract/template.potx extract/slides.odp extract/calc.ods
git commit -m "Batch extract design tokens from Office and OpenOffice files"
git push
```

**Result**: All files processed in parallel, results auto-committed.

### 3. Organized Project Structure

**Setup**: 
```
extract/
├── marketing/
│   ├── campaign-deck.pptx      # Microsoft Office
│   └── slides.odp              # LibreOffice Impress
├── sales/
│   ├── pitch-template.potx     # PowerPoint template
│   └── calc-model.ods          # LibreOffice Calc
└── hr/
    ├── onboarding-slides.pptx  # PowerPoint
    └── handbook.odt            # LibreOffice Writer
```

**Result**: Each gets its own `extracted/` subfolder with organized outputs.

## Workflow Steps

1. **File Detection** - `tj-actions/changed-files` detects new Office and OpenOffice files
2. **Token Extraction** - Runs `design_token_extractor.py` on each file
3. **Asset Organization** - Creates structured output directories
4. **Auto-Commit** - Commits results with descriptive messages

## Output Structure

For each input file `example.pptx`, creates:

```
extract/
├── example.pptx                    # Original file
└── extracted/
    ├── example-tokens.json         # Design tokens
    └── example-assets/             # Brand assets
        ├── logos/                  # Company logos
        ├── icons/                  # UI/functional icons
        └── images/                 # Photos and graphics
```

## Manual Trigger

Force workflow execution without file changes:
```bash
# Trigger via GitHub UI: Actions > Design Token Extraction > Run workflow
# Or use GitHub CLI:
gh workflow run token-extraction.yml
```

## Advanced Configuration

### Custom Asset Directory
Modify the workflow to change asset organization:
```json
assets_dir="$output_dir/brand-assets/$base_name"
```

### Different Output Formats
Change from JSON to JSON:
```json
tokens_file="$output_dir/$base_name-tokens.json"
# Remove --output flag to use default JSON
```

### Analysis Reports  
Enable detailed analysis:
```json
python tools/design_token_extractor.py "$file" \
  --output "$tokens_file" \
  --extract-assets \
  --assets-dir "$assets_dir" \
  --analyze \
  --verbose \
  > "$output_dir/$base_name-analysis.log"
```

---

This folder-based workflow transforms StyleStack into a **"drop and extract"** system where designers can simply commit Office or OpenOffice files and automatically receive structured design tokens and organized brand assets! 🎯