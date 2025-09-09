# Troubleshooting

Common issues and solutions for StyleStack's GitHub-native licensing system.

## License Validation Errors

### ❌ "License required for [org-name]"

**What it means:** No valid license found for your organization name.

**Common causes:**
- License request not completed
- Organization name mismatch
- Encrypted license file missing or corrupted
- Repository secrets not configured

**Solutions:**

1. **Check license status:**
   ```bash
   python tools/github_license_manager.py validate --org "your-org-name"
   ```

2. **Verify organization name:**
   - Must match exactly (case sensitive)
   - Use same name as GitHub organization
   - Check for typos or extra characters

3. **Look for encrypted license file:**
   ```bash
   ls -la .github/licenses/
   # Should show: your-org-name.license.enc
   ```

4. **Re-run license request if needed:**
   - Go to Actions → "Request StyleStack License"
   - Follow the complete workflow

### ❌ "OIDC token not available"

**What it means:** GitHub Actions cannot generate identity token.

**Common causes:**
- Missing `id-token: write` permission
- Running outside GitHub Actions
- Workflow configuration error

**Solutions:**

1. **Add proper permissions to workflow:**
   ```json
   permissions:
     id-token: write  # Required for OIDC
     contents: write  # Required to save license
   ```

2. **Check workflow context:**
   ```json
   - name: Debug context
     run: |
       echo "GITHUB_ACTIONS: $GITHUB_ACTIONS"
       echo "ACTIONS_ID_TOKEN_REQUEST_TOKEN: $ACTIONS_ID_TOKEN_REQUEST_TOKEN"
   ```

3. **Verify workflow triggers:**
   - OIDC only works in GitHub Actions
   - Must be triggered by supported events
   - Cannot be used in `act` or local runners

### ❌ "Payment required"

**What it means:** Commercial organization needs paid license.

**Common causes:**
- Organization doesn't qualify for community tier
- Payment not completed
- License request pending payment

**Solutions:**

1. **Check community tier eligibility:**
   - Add `nonprofit`, `education`, `university` to org name
   - Ensure repository has OSS license file (`LICENSE`, `LICENSE.md`)
   - Verify license contains recognized OSS license text

2. **Complete payment process:**
   - Check email for payment instructions
   - Look for GitHub issue in upstream repository
   - Contact support@stylestack.dev for payment status

3. **Temporary workaround for testing:**
   ```bash
   export STYLESTACK_SKIP_LICENSE=true
   python build.py --org "test-org" --out template.potx
   ```

### ❌ "Invalid signature" or "License expired"

**What it means:** License file is corrupted or expired.

**Solutions:**

1. **Request fresh license:**
   - Delete existing license file: `rm .github/licenses/*.license.enc`
   - Re-run license request workflow
   - Wait for new license delivery

2. **Check license details:**
   ```bash
   python tools/github_license_manager.py validate --org "your-org"
   # Shows expiration date and validation details
   ```

3. **Verify file integrity:**
   ```bash
   # Check if file is corrupted
   file .github/licenses/your-org.license.enc
   # Should show "data" not "text" or "empty"
   ```

## Workflow Errors

### ❌ License request workflow fails

**Common errors and solutions:**

#### "Repository dispatch failed"

**Cause:** Missing permissions or network issues.

**Solution:**
```json
# Ensure proper permissions
permissions:
  contents: read
  actions: read
  id-token: write
```

#### "Python module not found"

**Cause:** Missing dependencies in workflow.

**Solution:**
```json
- name: Install dependencies
  run: |
    pip install PyJWT cryptography requests
```

#### "Invalid client payload"

**Cause:** Malformed JSON in repository dispatch.

**Solution:** Check workflow JSON syntax:
```json
client-payload: |
  {
    "requester": "${{ github.repository_owner }}",
    "tier": "${{ inputs.tier }}"
  }
```

### ❌ License receive workflow fails

#### "Cannot decrypt license"

**Causes:**
- Missing decryption key
- Repository moved/renamed  
- Corrupted encrypted data

**Solutions:**

1. **Verify repository context:**
   ```bash
   echo "Owner: $GITHUB_REPOSITORY_OWNER"
   echo "Repo: $GITHUB_REPOSITORY"
   # Must match license generation
   ```

2. **Check file permissions:**
   ```bash
   ls -la .github/licenses/
   # Files should be readable by Actions
   ```

3. **Manual decryption test:**
   ```bash
   python tools/github_license_manager.py validate --org "$GITHUB_REPOSITORY_OWNER"
   ```

#### "Git commit failed"

**Cause:** No changes to commit or permission issues.

**Solution:**
```json
- name: Commit with error handling
  run: |
    git add .github/licenses/*.enc || true
    git commit -m "Add encrypted license" || echo "No changes to commit"
    git push || echo "Push failed - check permissions"
```

## Local Development Issues

### ❌ "Cannot validate license locally"

**Causes:**
- Missing encrypted license file
- Environment variables not set
- Running outside repository context

**Solutions:**

1. **Use environment variable:**
   ```bash
   export STYLESTACK_LICENSE="[your-license-string]"
   python build.py --org "your-org" --out template.potx
   ```

2. **Skip license check for testing:**
   ```bash
   export STYLESTACK_SKIP_LICENSE=true
   python build.py --org "test-org" --out template.potx
   ```

3. **Copy license from GitHub:**
   - Download encrypted license from GitHub Actions artifacts
   - Place in `.github/licenses/your-org.license.enc`

### ❌ "Community tier not detected"

**Problem:** Organization should qualify for free tier but license is required.

**Solutions:**

1. **Check organization name:**
   ```bash
   # These automatically qualify:
   python build.py --org "my-nonprofit" --out template.potx
   python build.py --org "university-research" --out template.potx
   python build.py --org "education-foundation" --out template.potx
   ```

2. **Add OSS license to repository:**
   ```bash
   # Create LICENSE file with recognized license
   curl -s https://api.github.com/licenses/mit | jq -r .body > LICENSE
   ```

3. **Test community detection:**
   ```bash
   python tools/github_license_manager.py validate --org "your-nonprofit-org"
   # Should show "community" tier
   ```

## CI/CD Integration Issues

### ❌ License not found in GitHub Actions

**Common solutions:**

1. **Use repository secret:**
   ```json
   # In repository settings → Secrets and variables → Actions
   # Create secret: STYLESTACK_LICENSE
   
   - name: Build with license
     env:
       STYLESTACK_LICENSE: ${{ secrets.STYLESTACK_LICENSE }}
     run: python build.py --org "your-org" --out template.potx
   ```

2. **Use encrypted file (automatic):**
   ```json
   # No environment variables needed
   - name: Build with encrypted license
     run: python build.py --org "your-org" --out template.potx
   ```

3. **Check Actions logs:**
   ```json
   - name: Debug license detection
     run: |
       python tools/github_license_manager.py validate --org "your-org"
       ls -la .github/licenses/
   ```

### ❌ "License validation timeout"

**Causes:**
- Network issues during OIDC validation
- GitHub API rate limits
- Upstream repository unavailable

**Solutions:**

1. **Add timeout and retry:**
   ```json
   - name: Request license with retry
     uses: nick-invision/retry@v2
     with:
       timeout_minutes: 5
       max_attempts: 3
       command: |
         python tools/github_license_manager.py request --org "${{ github.repository_owner }}"
   ```

2. **Use cached license:**
   ```json
   - name: Cache license
     uses: actions/cache@v3
     with:
       path: .github/licenses/
       key: license-${{ github.repository_owner }}
   ```

## Advanced Troubleshooting

### Debug License Manager

```bash
# Enable debug logging
export STYLESTACK_DEBUG=true
python tools/github_license_manager.py validate --org "your-org"

# Check all license sources
python -c "
from tools.github_license_manager import GitHubLicenseManager
manager = GitHubLicenseManager()
print('Checking all sources...')

# Environment
import os
print(f'ENV: {bool(os.getenv(\"STYLESTACK_LICENSE\"))}')

# File
from pathlib import Path  
license_file = Path('.github/licenses/your-org.license.enc')
print(f'FILE: {license_file.exists()}')

# Secret (in Actions)
secret_name = 'LICENSE_YOUR_ORG'  
print(f'SECRET: {bool(os.getenv(secret_name))}')
"
```

### Validate OIDC Token

```bash
# In GitHub Actions, decode token manually
python -c "
import jwt
import os
token = os.getenv('ACTIONS_ID_TOKEN_REQUEST_TOKEN')
if token:
    claims = jwt.decode(token, options={'verify_signature': False})
    print('OIDC Claims:')
    for k, v in claims.items():
        print(f'  {k}: {v}')
else:
    print('No OIDC token available')
"
```

### Check File Encryption

```bash
# Verify encrypted file structure  
python -c "
import os
from pathlib import Path

license_file = Path('.github/licenses/your-org.license.enc')
if license_file.exists():
    data = license_file.read_bytes()
    print(f'File size: {len(data)} bytes')
    print(f'IV (first 16 bytes): {data[:16].hex()}')
    print(f'Has ciphertext: {len(data) > 16}')
else:
    print('No encrypted license file found')
"
```

## Getting Help

### Self-Service Options

1. **Check documentation:**
   - [Licensing Overview](./overview.md)
   - [Request License Guide](./request-license.md)
   - [Technical Implementation](./technical-implementation.md)

2. **Search existing issues:**
   - [GitHub Issues](https://github.com/BramAlkema/StyleStack/issues)
   - Use labels: `licensing`, `troubleshooting`

3. **Community support:**
   - [GitHub Discussions](https://github.com/BramAlkema/StyleStack/discussions)
   - Discord: [stylestack-community](https://discord.gg/stylestack)

### Professional Support

**Professional tier** (48h response):
- Email: support@stylestack.dev
- Include: organization name, error logs, workflow runs

**Enterprise tier** (4h SLA):  
- Priority support: enterprise@stylestack.dev
- Slack/Teams integration available
- Video call support

### Create Support Ticket

When contacting support, include:

1. **Organization details:**
   - Organization name
   - Repository URL  
   - License tier (if known)

2. **Error information:**
   - Complete error message
   - Workflow run URL
   - Steps to reproduce

3. **Environment:**
   - GitHub Actions or local development
   - Operating system (if local)
   - Python version

4. **Debug output:**
   ```bash
   python tools/github_license_manager.py validate --org "your-org" 2>&1 | tee debug.log
   ```

**Template:**
```
Subject: License Issue - [Organization Name]

Organization: my-company
Repository: https://github.com/my-company/StyleStack
Tier: Professional
Environment: GitHub Actions

Issue Description:
[Detailed description of the problem]

Error Message:
[Complete error output]

Steps to Reproduce:
1. [Step one]
2. [Step two]  
3. [Step three]

Expected Behavior:
[What should happen]

Additional Context:
[Any other relevant information]
```

## Known Issues & Workarounds

### GitHub API Rate Limits

**Issue:** OIDC token validation fails during high traffic.

**Workaround:**
```json
- name: Wait and retry
  run: |
    sleep $((RANDOM % 30 + 10))  # Random delay 10-40s
    python tools/github_license_manager.py request --org "${{ github.repository_owner }}"
```

### Repository Transfer Issues  

**Issue:** License becomes invalid after repository transfer.

**Resolution:** 
- New owner must request fresh license
- Original license automatically invalidated for security

### Large Organization Licensing

**Issue:** Multiple repositories need individual licenses.

**Solution:** Contact enterprise@stylestack.dev for:
- Volume licensing programs
- Centralized license management
- SSO integration options

---

*Still having issues? Check our [FAQ](./overview.md#frequently-asked-questions) or [contact support](#getting-help).*