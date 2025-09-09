---
sidebar_position: 3
---

# Syncing with Upstream

Learn how to keep your StyleStack fork synchronized with community improvements while preserving your organizational customizations. This guide covers safe upstream integration strategies and conflict resolution.

## Why Sync with Upstream?

Staying synchronized with the upstream StyleStack repository provides:

- **Security updates** - Bug fixes and security patches
- **New features** - Latest template improvements and capabilities  
- **Accessibility improvements** - Enhanced WCAG compliance and usability
- **Office compatibility** - Support for new Office versions
- **Performance optimizations** - Faster builds and smaller templates
- **Community knowledge** - Benefit from collective improvements

## Sync Strategy Overview

### The Golden Rule
**Never modify core files** - Your customizations should only exist in `org/your-org/`, making upstream merges clean and predictable.

### Sync Frequency Recommendations

- **Critical security updates:** Immediately
- **Regular updates:** Monthly or quarterly
- **Major version updates:** After thorough testing
- **Breaking changes:** Plan migration carefully

## Setting Up Upstream Sync

### Verify Upstream Remote

```bash
# Check existing remotes
git remote -v

# Should show:
# origin     https://github.com/your-org/stylestack-your-org.git (fetch)
# origin     https://github.com/your-org/stylestack-your-org.git (push)
# upstream   https://github.com/stylestack/stylestack.git (fetch)  
# upstream   https://github.com/stylestack/stylestack.git (push)
```

### Add Upstream Remote (if missing)

```bash
# Add upstream remote
git remote add upstream https://github.com/stylestack/stylestack.git

# Configure upstream (fetch only)
git remote set-url --push upstream DISABLE

# Verify configuration
git remote -v
```

## Checking for Updates

### Manual Update Check

```bash
# Fetch latest upstream changes
git fetch upstream

# Compare your fork with upstream
git log --oneline --graph --decorate main..upstream/main

# See what files changed
git diff --name-only main..upstream/main

# Check for changes in core system
git diff --name-only main..upstream/main | grep "^core/"
```

### Automated Update Monitoring

```json
# .github/workflows/upstream-check.yml
name: Check Upstream Updates

on:
  schedule:
    - cron: '0 9 * * 1'  # Monday 9 AM
  workflow_dispatch:      # Manual trigger

jobs:
  check-upstream:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
          
      - name: Fetch upstream
        run: git fetch upstream
        
      - name: Check for updates
        id: check
        run: |
          COMMITS_BEHIND=$(git rev-list --count main..upstream/main)
          echo "commits_behind=$COMMITS_BEHIND" >> $GITHUB_OUTPUT
          
      - name: Notify if updates available
        if: steps.check.outputs.commits_behind != '0'
        run: |
          echo "::notice::Fork is ${{ steps.check.outputs.commits_behind }} commits behind upstream"
          # Add Slack/email notification here
```

## Safe Sync Process

### 1. Preparation Phase

```bash
# Ensure clean working directory
git status
# Should show: working tree clean

# Create backup branch
git branch backup-before-sync-$(date +%Y%m%d)

# Switch to main branch
git checkout main

# Verify no uncommitted changes
git diff --exit-code
```

### 2. Fetch and Analyze Updates

```bash
# Fetch upstream changes
git fetch upstream

# Analyze what's changed
git log --oneline --graph upstream/main ^main

# Check for breaking changes
git diff main..upstream/main --name-only | grep -E "(build\.py|tools/|\.github/workflows/)"

# Review core changes (should not conflict with org customizations)
git diff main..upstream/main core/
```

### 3. Test Merge (Dry Run)

```bash
# Test merge without committing
git merge --no-commit --no-ff upstream/main

# Check for conflicts
git status

# If conflicts exist, analyze them
git diff --name-only --diff-filter=U

# Abort test merge
git merge --abort
```

### 4. Perform the Sync

#### Scenario A: Clean Merge (No Conflicts)

```bash
# Merge upstream changes
git merge upstream/main -m "Sync with upstream: $(git log --oneline -1 upstream/main)"

# Push updated main branch
git push origin main

# Clean up backup branch (after verification)
git branch -d backup-before-sync-$(date +%Y%m%d)
```

#### Scenario B: Conflicts (Rare with Proper Fork Management)

```bash
# Start merge
git merge upstream/main

# Conflicts should only occur in non-org files
# Resolve conflicts carefully

# For organization files, keep your version:
git checkout --ours org/your-org/patches.json

# For upstream files, accept their version:
git checkout --theirs .github/workflows/build-templates.yml.example

# Manually resolve complex conflicts in:
# - README.md (merge both versions)
# - CHANGELOG.md (preserve both histories)

# Stage resolved files
git add .

# Complete merge
git commit -m "Sync with upstream, resolve conflicts

- Merged upstream changes from $(git log --oneline -1 upstream/main)
- Preserved organizational customizations
- Resolved conflicts in favor of upstream for system files"

# Push changes
git push origin main
```

## Handling Specific Update Types

### Security Updates

```bash
# For urgent security updates
git fetch upstream
git log upstream/main ^main --grep="security\|CVE\|vulnerability" -i

# Priority merge for security fixes
git merge upstream/main
python build.py --org your-org --test-security
git push origin main

# Notify team immediately
echo "Security update applied" | notify-slack
```

### Breaking Changes

```bash
# For major version updates with breaking changes
git fetch upstream

# Check for breaking changes
git show upstream/main:CHANGELOG.md | grep -A 10 "BREAKING"

# Create feature branch for testing
git checkout -b upstream-sync-v2.0.0

# Merge and test
git merge upstream/main
python build.py --org your-org --all-channels --validate

# If tests pass, merge to main
git checkout main
git merge upstream-sync-v2.0.0
git push origin main

# Clean up
git branch -d upstream-sync-v2.0.0
```

### New Features

```bash
# Regular feature updates
git fetch upstream
git merge upstream/main

# Test new features with your org
python build.py --org your-org --verbose

# Update documentation if needed
# Update org-specific channels to use new features
```

## Conflict Resolution Strategies

### Understanding Conflict Sources

Most conflicts in a well-managed fork occur in:

1. **Documentation files** (README.md, CHANGELOG.md)
2. **Configuration files** (.github/workflows/)
3. **Build system updates** (rare, but possible)

### Resolution Guidelines

#### Documentation Conflicts

```bash
# README.md conflicts - merge both versions
# Keep upstream content + add org-specific sections

<<<<<<< HEAD
# StyleStack Templates - Your Organization

Custom templates for Your Organization.
=======
# StyleStack - OOXML Template Build System

Community-driven Office templates.
>>>>>>> upstream/main

# Resolve to:
# StyleStack - Your Organization Templates

# Based on StyleStack - OOXML Template Build System
# Custom templates for Your Organization.
```

#### Configuration Conflicts

```bash
# .github/workflows/ conflicts - prefer upstream, adapt org settings
# Generally accept upstream version and re-customize

git checkout --theirs .github/workflows/build-templates.yml.example
# Then re-apply your org-specific settings:
sed -i 's/REPLACE_ORG/your-org/g' .github/workflows/build-templates.yml.example
```

#### Build System Conflicts

```bash
# build.py conflicts - extremely rare with proper fork management
# Usually indicates upstream API changes requiring org config updates

# Check what changed in build system
git diff HEAD~1..upstream/main build.py tools/

# Update org configuration to match new API
# Test thoroughly before committing
python build.py --org your-org --validate
```

## Post-Sync Validation

### Automated Testing

```bash
# Build all organizational templates
python build.py --org your-org --all-channels --products potx dotx xltx

# Run full test suite
python tools/test-all.py --org your-org

# Validate accessibility compliance
python tools/validate-accessibility.py --org your-org

# Test template loading in Office
python tools/test-office-compatibility.py --org your-org
```

### Manual Verification

**Template Quality:**
- [ ] All organizational branding preserved
- [ ] Colors and fonts render correctly
- [ ] Logos and assets load properly
- [ ] Layout and spacing maintained

**Functionality:**
- [ ] Build system works without errors
- [ ] CI/CD pipeline continues to function
- [ ] All channels build successfully
- [ ] Template validation passes

**Compliance:**
- [ ] Accessibility standards maintained
- [ ] Regulatory requirements preserved  
- [ ] Document controls functional
- [ ] Privacy notices intact

## Sync Automation

### Automated Sync Workflow

```json
# .github/workflows/auto-sync.yml
name: Auto Sync Upstream

on:
  schedule:
    - cron: '0 2 * * 1'  # Monday 2 AM
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}
          
      - name: Configure Git
        run: |
          git config user.name "StyleStack Bot"
          git config user.email "bot@your-org.com"
          
      - name: Add upstream remote
        run: git remote add upstream https://github.com/stylestack/stylestack.git
        
      - name: Fetch upstream
        run: git fetch upstream
        
      - name: Check for updates
        id: check
        run: |
          if git merge-tree $(git merge-base main upstream/main) main upstream/main | grep -q .; then
            echo "conflicts=true" >> $GITHUB_OUTPUT
          else
            echo "conflicts=false" >> $GITHUB_OUTPUT
          fi
          
      - name: Auto-merge if no conflicts
        if: steps.check.outputs.conflicts == 'false'
        run: |
          git merge upstream/main -m "Auto-sync with upstream $(date +%Y-%m-%d)"
          
      - name: Test build
        run: python build.py --org your-org --validate
        
      - name: Push if tests pass
        if: steps.check.outputs.conflicts == 'false'
        run: git push origin main
        
      - name: Create PR if conflicts
        if: steps.check.outputs.conflicts == 'true'
        run: |
          git checkout -b auto-sync-$(date +%Y%m%d)
          git push origin auto-sync-$(date +%Y%m%d)
          gh pr create --title "Upstream sync with conflicts" \
            --body "Automated sync detected conflicts. Manual review required."
```

### Notification System

```bash
# scripts/notify-sync.sh
#!/bin/bash

SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
ORG_NAME="Your Organization"

if [ "$1" = "success" ]; then
    MESSAGE="✅ $ORG_NAME StyleStack templates synced successfully with upstream"
elif [ "$1" = "conflicts" ]; then  
    MESSAGE="⚠️ $ORG_NAME StyleStack sync has conflicts. Manual review required."
elif [ "$1" = "failure" ]; then
    MESSAGE="❌ $ORG_NAME StyleStack sync failed. Check build logs."
fi

curl -X POST -H 'Content-type: application/json' \
    --data "{\"text\":\"$MESSAGE\"}" \
    "$SLACK_WEBHOOK"
```

## Troubleshooting Sync Issues

### Common Problems

**Problem: "Failed to merge upstream/main"**
```bash
# Solution: Check for uncommitted changes
git status
git stash push -m "WIP before upstream sync"
git merge upstream/main
git stash pop
```

**Problem: "Conflicts in core/ directory"**
```bash
# This should never happen with proper fork management
# Indicates core files were modified locally

# Solution: Reset core files to upstream version
git checkout upstream/main -- core/
git add core/
git commit -m "Reset core files to upstream version"
```

**Problem: "Build fails after sync"**
```bash
# Solution: Check for API changes
git diff HEAD~1..upstream/main build.py tools/
python build.py --org your-org --debug --verbose

# Update org configuration if needed
# Consult upstream CHANGELOG for migration guides
```

**Problem: "Templates look different after sync"**
```bash
# Solution: Check for design token changes
git diff HEAD~1..upstream/main core/tokens/
python tools/compare-tokens.py --before HEAD~1 --after HEAD --org your-org

# Update org overrides if needed
```

## Best Practices

### Sync Timing
- **Avoid Fridays** - Issues need time to resolve
- **Test first** - Use staging/dev environment
- **Communicate** - Notify team before major syncs
- **Plan ahead** - Schedule syncs around important deadlines

### Risk Mitigation
- **Backup before sync** - Create safety branches
- **Test thoroughly** - Validate all organizational templates
- **Document changes** - Keep sync logs and rationale
- **Rollback plan** - Know how to revert if needed

### Team Coordination
- **Sync ownership** - Designate sync responsibility
- **Review process** - Peer review for complex syncs
- **Communication** - Share sync results with stakeholders
- **Training** - Ensure team understands sync process

## Emergency Procedures

### Rollback Process

```bash
# If sync causes critical issues
git log --oneline -10  # Find pre-sync commit

# Reset to previous state
git reset --hard <pre-sync-commit-hash>

# Force push (use with caution)
git push origin main --force-with-lease

# Notify team
echo "Rolled back StyleStack sync due to critical issues" | notify-team
```

### Hotfix Process

```bash
# For urgent fixes needed before full sync
git checkout -b hotfix-urgent-issue
git cherry-pick <upstream-commit-with-fix>
python build.py --org your-org --validate
git checkout main
git merge hotfix-urgent-issue
git push origin main
```

## Next Steps

- [Set up governance processes](./governance.md)
- [Implement automated deployment](../deployment/ci-cd.md)
- [Learn advanced customization](./customizing.md)
- [Explore enterprise examples](../examples/enterprise.md)