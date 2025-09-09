---
sidebar_position: 1
---

# Creating a Fork

Learn how to properly fork StyleStack for your organization while maintaining the ability to sync with upstream improvements. This guide covers the fork-first distribution model that enables institutional customization without sacrificing community benefits.

## Why Fork?

StyleStack uses a **fork-first distribution model** because:

- **Ownership** - Your organization controls the template distribution
- **Customization** - Add branding without polluting upstream
- **Compliance** - Meet regulatory requirements specific to your industry
- **Governance** - Implement organizational approval workflows
- **Stability** - Control when to adopt upstream changes

## Prerequisites

### Required Accounts
- **GitHub account** (personal or organization)
- **Git** installed locally
- **GitHub CLI** (optional but recommended)

### Permissions Needed
- **Repository creation** rights in your organization
- **Admin access** to configure branch protection
- **Secrets management** for CI/CD setup

## Step 1: Fork the Repository

### Via GitHub Web Interface

1. **Visit the upstream repository:**
   ```
   https://github.com/stylestack/stylestack
   ```

2. **Click the Fork button** in the top-right corner

3. **Configure your fork:**
   - **Owner:** Select your organization account
   - **Repository name:** `stylestack-[your-org]` (recommended)
   - **Description:** "StyleStack templates for [Your Organization]"
   - **Public/Private:** Choose based on your needs

4. **Click "Create Fork"**

### Via GitHub CLI

```bash
# Fork to organization account
gh repo fork stylestack/stylestack \
  --org your-organization \
  --repo-name stylestack-your-org \
  --clone

# Fork to personal account  
gh repo fork stylestack/stylestack \
  --repo-name stylestack-your-org \
  --clone
```

## Step 2: Configure Local Repository

### Clone Your Fork

```bash
# Clone your fork
git clone https://github.com/your-organization/stylestack-your-org.git
cd stylestack-your-org

# Verify remote
git remote -v
# origin https://github.com/your-organization/stylestack-your-org.git (fetch)
# origin https://github.com/your-organization/stylestack-your-org.git (push)
```

### Add Upstream Remote

```bash
# Add upstream remote for syncing
git remote add upstream https://github.com/stylestack/stylestack.git

# Verify remotes
git remote -v
# origin     https://github.com/your-organization/stylestack-your-org.git (fetch)
# origin     https://github.com/your-organization/stylestack-your-org.git (push) 
# upstream   https://github.com/stylestack/stylestack.git (fetch)
# upstream   https://github.com/stylestack/stylestack.git (push)
```

### Test Sync Capability

```bash
# Fetch upstream changes
git fetch upstream

# Check for updates
git log --oneline upstream/main ^main

# Test merge (dry run)
git merge --no-commit --no-ff upstream/main
git merge --abort
```

## Step 3: Repository Configuration

### Branch Protection Rules

Set up branch protection for your main branch:

```bash
# Create branch protection rule via GitHub CLI
gh api repos/your-organization/stylestack-your-org/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["build-templates"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1}' \
  --field restrictions=null
```

Or configure via GitHub web interface:
1. **Settings → Branches → Add rule**
2. **Branch name pattern:** `main`
3. **Require pull request reviews before merging**
4. **Require status checks to pass before merging**
5. **Include administrators**

### Repository Settings

```bash
# Set default branch (if needed)
gh repo edit --default-branch main

# Add repository description and topics
gh repo edit --description "StyleStack templates for Your Organization" \
  --add-topic "office-templates" \
  --add-topic "ooxml" \
  --add-topic "design-system"
```

## Step 4: Initial Customization

### Create Organization Directory

```bash
# Create your organization's directory structure
mkdir -p org/your-org/{assets,channels}

# Create initial patches file
cat > org/your-org/patches.json << EOF
organization:
  name: "Your Organization"
  short_name: "your-org"
  domain: "your-org.com"
  
branding:
  primary_color: "#003366"
  secondary_color: "#0066CC"  
  accent_color: "#FF6600"
  
fonts:
  heading: "Arial"
  body: "Calibri"
  
assets:
  logo: "assets/logo.png"
EOF
```

### Add Placeholder Assets

```bash
# Create placeholder logo (replace with real logo later)
# This creates a simple 200x60 blue rectangle as placeholder
convert -size 200x60 xc:"#003366" -pointsize 16 -fill white \
  -gravity center -annotate +0+0 "YOUR ORG" \
  org/your-org/assets/logo.png

# Or copy your real logo
cp /path/to/your-logo.png org/your-org/assets/logo.png
```

### Test Initial Build

```bash
# Test build with your organization
python build.py --org your-org --channel present --products potx

# Verify output
ls -la BetterDefaults-your-org-present-*.potx
```

## Step 5: Governance Setup

### Create Governance Configuration

```json
# org/your-org/governance.json
governance:
  # Approval requirements
  approvers:
    brand_changes:
      - "brand-manager"
      - "design-lead"
    compliance_changes:
      - "compliance-officer"
      - "legal-counsel"
    technical_changes:
      - "tech-lead"
      - "senior-developer"
  
  # Automatic approval for certain changes
  auto_approve:
    - "assets/*"              # Asset updates
    - "channels/*.json"       # Channel modifications
  
  # Restricted changes requiring special approval
  restricted:
    - "core/*"                # Core modifications forbidden
    - "accessibility/*"       # Accessibility changes restricted
  
  # Notification settings
  notifications:
    slack_webhook: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    email_list: ["team@your-org.com"]
```

### Set Up Review Templates

```bash
# Create PR template
mkdir -p .github
cat > .github/pull_request_template.md << EOF
## Changes Summary

Brief description of template changes.

## Type of Change
- [ ] Brand/Design updates
- [ ] New channel/variant
- [ ] Asset updates
- [ ] Bug fix
- [ ] Upstream sync

## Testing Checklist
- [ ] Built successfully for all target products
- [ ] Accessibility validation passed
- [ ] Visual review completed
- [ ] Tested in target Office applications

## Approvals Required
- [ ] Brand Manager (for brand changes)
- [ ] Compliance Officer (for regulatory changes)
- [ ] Technical Lead (for system changes)

## Additional Notes
Any additional context or special instructions.
EOF
```

## Step 6: CI/CD Configuration

### GitHub Actions Setup

```bash
# Copy CI configuration
cp .github/workflows/build-templates.yml.example .github/workflows/build-templates.yml

# Customize for your organization
sed -i 's/REPLACE_ORG/your-org/g' .github/workflows/build-templates.yml
```

### Repository Secrets

Configure secrets in GitHub repository settings:

```bash
# Set up secrets via CLI
gh secret set RELEASE_TOKEN --body "$GITHUB_TOKEN"

# Or via web interface:
# Settings → Secrets and variables → Actions → New repository secret
```

Required secrets:
- `RELEASE_TOKEN` - GitHub token for releases
- `SLACK_WEBHOOK` - Slack notifications (optional)
- `ORG_CONFIG` - Base64 encoded org config (optional)

### Test CI/CD Pipeline

```bash
# Commit initial setup
git add org/your-org/ .github/
git commit -m "Initial organization setup for your-org

- Add organization configuration
- Set up governance rules  
- Configure CI/CD pipeline"

# Push and trigger build
git push origin main

# Check workflow status
gh run list --limit 1
```

## Step 7: Documentation Setup

### Update README

```bash
# Create organization-specific README
cat > README-your-org.md << EOF
# StyleStack Templates - Your Organization

This repository contains customized Office templates for Your Organization, based on the StyleStack template system.

## Quick Start

1. Download the latest templates from [Releases](../../releases/latest)
2. Install in Office applications
3. Create professional documents with consistent branding

## Template Variants

- **Presentation** - For meetings and presentations
- **Document** - For reports and documentation  
- **Finance** - For financial reports and spreadsheets

## Support

For questions or issues:
- IT Support: support@your-org.com
- Template Requests: design-team@your-org.com
- Technical Issues: [GitHub Issues](../../issues)

EOF
```

### Create Contribution Guide

```bash
cat > CONTRIBUTING-your-org.md << EOF
# Contributing to Your Org Templates

## Making Changes

1. Create feature branch from main
2. Make changes in org/your-org/ directory only
3. Test changes with build.py
4. Submit pull request with proper approvals

## Approval Requirements

- Brand changes: Requires brand manager approval
- Compliance changes: Requires compliance officer approval
- Technical changes: Requires tech lead approval

## Testing Requirements

All changes must:
- Build successfully for all products
- Pass accessibility validation
- Be tested in target Office applications
- Include visual review documentation

EOF
```

## Step 8: Team Access Setup

### Repository Permissions

```bash
# Add team with appropriate permissions
gh api orgs/your-organization/teams/design-team/repos/your-organization/stylestack-your-org \
  --method PUT \
  --field permission=push

# Add individual collaborators  
gh repo add-collaborator your-organization/stylestack-your-org \
  --permission write username
```

### Branch Permissions

Configure who can:
- **Push to main:** Only via pull requests
- **Merge PRs:** Team leads and maintainers
- **Admin access:** Repository owners and admins

## Step 9: Release Strategy

### Versioning Strategy

```json
# .github/release-strategy.json
versioning:
  scheme: "semantic"        # major.minor.patch
  prefix: "v"              # v1.2.3
  org_suffix: "-your-org"  # v1.2.3-your-org
  
releases:
  schedule: "monthly"       # Regular release schedule
  channels:
    - "stable"             # Production releases
    - "beta"               # Preview releases
  
automation:
  auto_release: true       # Automatic releases on main merge
  generate_notes: true     # Auto-generate release notes
```

### Initial Release

```bash
# Create first release
git tag v1.0.0-your-org
git push origin v1.0.0-your-org

# Create release via CLI
gh release create v1.0.0-your-org \
  --title "Your Org Templates v1.0.0" \
  --notes "Initial release of customized StyleStack templates for Your Organization" \
  BetterDefaults-your-org-*.potx \
  BetterDefaults-your-org-*.dotx \
  BetterDefaults-your-org-*.xltx
```

## Step 10: Monitoring and Maintenance

### Health Checks

```bash
# Set up repository health monitoring
cat > .github/workflows/health-check.yml << EOF
name: Repository Health Check

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check upstream sync status
        run: |
          git fetch upstream
          BEHIND=\$(git rev-list --count main..upstream/main)
          echo "Repository is \$BEHIND commits behind upstream"
          if [ \$BEHIND -gt 10 ]; then
            echo "Warning: Repository is significantly behind upstream"
          fi
      - name: Validate organization config
        run: python tools/validate.py --org your-org
EOF
```

### Update Notifications

```bash
# Set up Slack notifications for updates
cat > scripts/notify-updates.py << EOF
import requests
import os

def notify_slack(message):
    webhook = os.environ.get('SLACK_WEBHOOK')
    if webhook:
        requests.post(webhook, json={'text': message})

# Use in CI/CD workflows
notify_slack("New StyleStack templates released for Your Organization")
EOF
```

## Common Issues and Solutions

### Fork Sync Issues

**Problem:** Fork gets out of sync with upstream
```bash
# Solution: Regular sync process
git fetch upstream
git checkout main  
git merge upstream/main
git push origin main
```

**Problem:** Merge conflicts during sync
```bash
# Solution: Resolve conflicts carefully
git fetch upstream
git merge upstream/main
# Resolve conflicts in organization-specific files only
git commit -m "Sync with upstream, resolve conflicts"
```

### Build Failures

**Problem:** Build fails after upstream sync
```bash
# Solution: Check for breaking changes
python tools/validate.py --org your-org --verbose
python build.py --org your-org --debug
```

### Permission Issues

**Problem:** Team members can't access repository
```bash
# Solution: Check and update permissions
gh repo list-collaborators your-organization/stylestack-your-org
gh api orgs/your-organization/teams --jq '.[].name'
```

## Best Practices

### Repository Management
- **Regular syncing** with upstream (weekly/monthly)
- **Clear branching strategy** (feature branches from main)
- **Comprehensive testing** before merging
- **Documentation** for all customizations

### Governance
- **Approval workflows** for different types of changes
- **Automated testing** in CI/CD pipeline
- **Regular reviews** of organizational requirements
- **Compliance monitoring** for regulated industries

### Security
- **Limit repository access** to necessary team members
- **Use branch protection** rules
- **Regularly audit** permissions and access
- **Monitor** for sensitive data in commits

## Next Steps

- [Learn customization techniques](./customizing.md)
- [Set up upstream synchronization](./syncing-upstream.md)
- [Establish governance processes](./governance.md)
- [Deploy to your organization](../deployment/ci-cd.md)

## Resources

- [GitHub Fork Documentation](https://docs.github.com/en/get-started/quickstart/fork-a-repo)
- [Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/managing-a-branch-protection-rule)
- [GitHub Actions for CI/CD](https://docs.github.com/en/actions)
- [StyleStack Community Discussions](https://github.com/stylestack/stylestack/discussions)