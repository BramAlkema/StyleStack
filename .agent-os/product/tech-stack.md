# Technical Stack

## Core Technologies

**Application Framework:** Python 3.9+
- Primary build system (`python build.py`)
- OOXML processing and manipulation
- CLI orchestration and patch application

**Database System:** Git-based file storage
- Raw OOXML parts stored in `core/` directory
- YAML patch specifications for organizational/user overrides
- Version control via Git for all template components

**OOXML Processing Libraries:**
- `python-pptx` - PowerPoint template generation and manipulation
- `python-docx` - Word document template processing  
- `openpyxl` - Excel workbook and template handling
- `lxml` - XML parsing and XPath operations for patch application

**Build System:**
- Custom Python CLI (`build.py`) with multi-target support
- YAML-based declarative patch system for template customization
- XPath/XML manipulation for precise OOXML modifications

## Web Technologies

**JavaScript Framework:** Multi-platform Add-in System
- **Microsoft Office:** Office JavaScript API for Office 365/Desktop
- **LibreOffice:** Python-UNO bridge for macro-free template installation
- **Google Workspace:** Google Apps Script for Google Slides/Docs/Sheets
- Template version checking and automatic updates across all platforms

**Import Strategy:** Mixed module systems
- **Node.js:** For Microsoft Office add-in development
- **Python:** For LibreOffice UNO extensions and core build system
- **Google Apps Script:** For Google Workspace integration

**CSS Framework:** Platform-adaptive styling
- **OOXML:** Core template styling (not web CSS)
- **Releases Page:** Tailwind CSS for modern, responsive design
- **Add-in UIs:** Platform-native component styling

**UI Component Library:** Platform-specific UI
- **Microsoft Office:** Fluent UI for consistent Office styling
- **LibreOffice:** Native dialog components via Python-UNO
- **Google Workspace:** Google Apps Script HTML service for web UI
- **Releases Page:** Static HTML/CSS with GitHub API integration

## Infrastructure

**Application Hosting:** GitHub Pages + GitHub Releases
- **Releases Page:** Static site displaying latest builds, changelogs, download links
- **Artifacts:** Distributed via GitHub Releases API
- **Documentation:** Project docs and community guidelines

**Database Hosting:** n/a
- Template data stored in Git repositories
- No traditional database required

**Asset Hosting:** GitHub Releases
- Compiled template artifacts (.potx, .dotx, .xltx)
- Cryptographically signed releases with checksums
- CDN distribution via GitHub's release infrastructure

**Deployment Solution:** GitHub Actions CI/CD
- **ci.yml:** Automated builds on PR/push, matrix testing, quality validation
- **release.yml:** Triggered by v* tags, builds all combinations, signs artifacts
- Matrix builds for org × channel × product combinations  
- Automated release creation with checksums and signed templates
- Quality gates: accessibility checking, XML validation, style linting

## Development Tools

**Fonts Provider:** System fonts + Google Fonts
- Inter and Noto fonts for professional typography
- Fallback to system fonts for compatibility

**Icon Library:** Office built-in icons
- Leverage existing Office icon sets for consistency
- Custom icons embedded as image relationships in OOXML

**Validation Tools:**
- `xmllint` for OOXML structure validation
- Custom contrast ratio checking for accessibility
- Style linting to ban tacky effects (bevels, glows, 3D shadows)

**Security:**
- `cosign` for artifact signing (optional)
- Checksum generation for release integrity
- No macros or executable code in templates

## Repository Structure

**Code Repository URL:** https://github.com/[org]/StyleStack
- Main repository for community-maintained core defaults
- Forkable structure for organizational customizations
- Issue tracking for community collaboration

**Branching Strategy:**
- `main` branch for stable releases
- Feature branches for core improvements
- Organizational forks for branding customizations

**Release Management:**
- Semantic versioning (v1.3.0)
- Automated release notes generation
- Multi-artifact releases per version