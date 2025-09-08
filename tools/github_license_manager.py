#!/usr/bin/env python3
"""
StyleStack GitHub-Native License Manager
Uses GitHub Actions OIDC tokens and encrypted secrets for licensing
No external API required - everything stays within GitHub
"""

import os
import json
import base64
import hashlib
import hmac
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
import subprocess
import jwt
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class GitHubLicenseManager:
    """
    Manages licenses using GitHub-native features:
    - OIDC tokens for identity verification
    - Repository secrets for license storage
    - Encrypted files for offline validation
    """
    
    LICENSE_DIR = Path(".github/licenses")
    PUBLIC_KEY_FILE = LICENSE_DIR / "public_key.pem"
    
    # License tiers (same as before but GitHub-native)
    TIERS = {
        'community': {
            'price': 0,
            'features': ['basic_tokens', 'github_deployment'],
            'max_forks': 5,
            'support': 'community'
        },
        'professional': {
            'price': 25,
            'features': ['custom_tokens', 'multi_platform', 'unlimited_forks'],
            'max_forks': -1,
            'support': 'email'
        },
        'enterprise': {
            'price': 50,
            'features': ['unlimited_tokens', 'all_platforms', 'white_label', 'sla'],
            'max_forks': -1,
            'support': 'priority'
        }
    }
    
    def __init__(self, repo_owner: str = None, repo_name: str = None):
        """Initialize GitHub license manager"""
        self.repo_owner = repo_owner or os.getenv('GITHUB_REPOSITORY_OWNER')
        self.repo_name = repo_name or os.getenv('GITHUB_REPOSITORY', '').split('/')[-1]
        self.is_fork = os.getenv('GITHUB_EVENT_NAME') == 'fork' or self._check_if_fork()
        
        # Ensure license directory exists
        self.LICENSE_DIR.mkdir(parents=True, exist_ok=True)
        
    def _check_if_fork(self) -> bool:
        """Check if current repository is a fork"""
        try:
            # Use GitHub CLI if available
            result = subprocess.run(
                ['gh', 'repo', 'view', '--json', 'isFork'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get('isFork', False)
        except Exception:
            pass
        
        # Check for upstream remote
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'upstream'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def validate_license(self, org_name: str) -> Tuple[bool, Dict]:
        """
        Validate license for an organization
        Checks in order:
        1. Environment variable (CI/CD)
        2. Encrypted license file
        3. GitHub secret
        4. Community tier eligibility
        """
        
        # Check for community/open source usage
        if self._is_open_source(org_name):
            return True, {
                'tier': 'community',
                'org': org_name,
                'expires': None,
                'features': self.TIERS['community']['features'],
                'source': 'community'
            }
        
        # 1. Check environment variable (for CI/CD)
        env_license = os.getenv('STYLESTACK_LICENSE')
        if env_license:
            valid, info = self._validate_license_string(env_license, org_name)
            if valid:
                info['source'] = 'environment'
                return valid, info
        
        # 2. Check encrypted license file
        license_file = self.LICENSE_DIR / f"{org_name}.license.enc"
        if license_file.exists():
            valid, info = self._validate_encrypted_file(license_file, org_name)
            if valid:
                info['source'] = 'encrypted_file'
                return valid, info
        
        # 3. Check GitHub secret (in Actions context)
        if os.getenv('GITHUB_ACTIONS'):
            secret_license = os.getenv(f'LICENSE_{org_name.upper().replace("-", "_")}')
            if secret_license:
                valid, info = self._validate_license_string(secret_license, org_name)
                if valid:
                    info['source'] = 'github_secret'
                    return valid, info
        
        return False, {'error': 'No valid license found', 'org': org_name}
    
    def _is_open_source(self, org_name: str) -> bool:
        """Check if organization qualifies for free community tier"""
        exempt_keywords = [
            'nonprofit', 'ngo', 'foundation', 'university', 'college',
            'school', 'education', 'edu', 'academic', 'research',
            'community', 'open-source', 'foss', 'libre', 'free'
        ]
        org_lower = org_name.lower()
        
        # Check for keywords
        if any(keyword in org_lower for keyword in exempt_keywords):
            return True
        
        # Check if repo itself is open source (has LICENSE file)
        if Path('LICENSE').exists() or Path('LICENSE.md').exists():
            with open(Path('LICENSE') if Path('LICENSE').exists() else Path('LICENSE.md')) as f:
                license_text = f.read().lower()
                oss_licenses = ['mit', 'apache', 'gpl', 'bsd', 'mpl', 'lgpl']
                if any(lic in license_text for lic in oss_licenses):
                    return True
        
        return False
    
    def _validate_license_string(self, license_str: str, org_name: str) -> Tuple[bool, Dict]:
        """Validate a license string (base64 encoded JSON with signature)"""
        try:
            # Decode license
            decoded = base64.b64decode(license_str).decode('utf-8')
            license_data = json.loads(decoded)
            
            # Verify organization matches
            if license_data.get('org') != org_name:
                return False, {'error': 'Organization mismatch'}
            
            # Verify signature
            message = f"{license_data['org']}:{license_data['tier']}:{license_data.get('expires', '')}"
            expected_sig = self._generate_signature(message)
            
            if not hmac.compare_digest(license_data.get('signature', ''), expected_sig):
                return False, {'error': 'Invalid signature'}
            
            # Check expiration
            if license_data.get('expires'):
                expires = datetime.fromisoformat(license_data['expires'])
                if expires < datetime.now():
                    return False, {'error': 'License expired'}
            
            return True, {
                'tier': license_data['tier'],
                'org': license_data['org'],
                'expires': license_data.get('expires'),
                'features': self.TIERS[license_data['tier']]['features']
            }
            
        except Exception as e:
            return False, {'error': f'Invalid license format: {str(e)}'}
    
    def _validate_encrypted_file(self, license_file: Path, org_name: str) -> Tuple[bool, Dict]:
        """Validate an encrypted license file"""
        try:
            # Read encrypted content
            with open(license_file, 'rb') as f:
                encrypted_data = f.read()
            
            # Decrypt using repository secret (must be set in GitHub Actions)
            decryption_key = os.getenv('STYLESTACK_DECRYPTION_KEY')
            if not decryption_key:
                # Try to derive from repository information
                decryption_key = self._derive_decryption_key()
            
            if not decryption_key:
                return False, {'error': 'No decryption key available'}
            
            # Decrypt the license
            decrypted = self._decrypt_data(encrypted_data, decryption_key)
            
            # Validate the decrypted license
            return self._validate_license_string(decrypted, org_name)
            
        except Exception as e:
            return False, {'error': f'Failed to decrypt license: {str(e)}'}
    
    def _generate_signature(self, message: str) -> str:
        """Generate HMAC signature for license validation"""
        # Use GitHub repository ID as part of the secret for uniqueness
        repo_id = os.getenv('GITHUB_REPOSITORY_ID', 'default')
        secret = f"stylestack-{repo_id}-{self.repo_owner}"
        
        return hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _derive_decryption_key(self) -> Optional[str]:
        """Derive decryption key from repository information"""
        # This is used when running locally or in non-Actions environment
        if not self.repo_owner:
            return None
        
        # Create a deterministic key based on repo info
        key_material = f"{self.repo_owner}:{self.repo_name}:stylestack"
        return hashlib.sha256(key_material.encode()).hexdigest()[:32]
    
    def _decrypt_data(self, encrypted_data: bytes, key: str) -> str:
        """Decrypt data using AES"""
        # Ensure key is 32 bytes
        key_bytes = key.encode()[:32].ljust(32, b'\0')
        
        # Extract IV (first 16 bytes) and ciphertext
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        
        # Decrypt
        cipher = Cipher(
            algorithms.AES(key_bytes),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Remove padding and decode
        padding_length = decrypted[-1]
        return decrypted[:-padding_length].decode('utf-8')
    
    def request_license_via_oidc(self, tier: str = 'professional') -> bool:
        """
        Request a license from upstream using OIDC token
        This is called from GitHub Actions workflow
        """
        if not os.getenv('GITHUB_ACTIONS'):
            print("❌ OIDC license requests only work in GitHub Actions")
            return False
        
        # Get OIDC token
        token = os.getenv('ACTIONS_ID_TOKEN_REQUEST_TOKEN')
        if not token:
            print("❌ OIDC token not available. Ensure 'id-token: write' permission is set")
            return False
        
        # Create license request payload
        payload = {
            'requester': self.repo_owner,
            'repository': f"{self.repo_owner}/{self.repo_name}",
            'tier': tier,
            'oidc_token': token,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save request for upstream to process
        request_file = self.LICENSE_DIR / f"license_request_{self.repo_owner}.json"
        with open(request_file, 'w') as f:
            json.dump(payload, f, indent=2)
        
        print(f"✅ License request created for {tier} tier")
        print(f"   Request file: {request_file}")
        print("   Upstream will process this via repository_dispatch")
        
        return True
    
    def generate_license(self, org_name: str, tier: str, expires_days: int = 365) -> str:
        """
        Generate a license for an organization
        This is called by upstream to create licenses for forks
        """
        license_data = {
            'org': org_name,
            'tier': tier,
            'issued': datetime.now().isoformat(),
            'expires': (datetime.now() + timedelta(days=expires_days)).isoformat(),
            'issuer': 'StyleStack',
            'version': '1.0'
        }
        
        # Add signature
        message = f"{license_data['org']}:{license_data['tier']}:{license_data['expires']}"
        license_data['signature'] = self._generate_signature(message)
        
        # Encode as base64
        license_json = json.dumps(license_data, separators=(',', ':'))
        return base64.b64encode(license_json.encode()).decode()
    
    def save_encrypted_license(self, license_str: str, org_name: str):
        """Save an encrypted license file for offline use"""
        # Derive encryption key
        encryption_key = self._derive_decryption_key()
        if not encryption_key:
            raise ValueError("Cannot derive encryption key")
        
        # Encrypt the license
        key_bytes = encryption_key.encode()[:32].ljust(32, b'\0')
        iv = os.urandom(16)
        
        cipher = Cipher(
            algorithms.AES(key_bytes),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Add padding
        license_bytes = license_str.encode()
        padding_length = 16 - (len(license_bytes) % 16)
        padded_data = license_bytes + bytes([padding_length]) * padding_length
        
        # Encrypt
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # Save encrypted file
        license_file = self.LICENSE_DIR / f"{org_name}.license.enc"
        with open(license_file, 'wb') as f:
            f.write(iv + ciphertext)
        
        print(f"✅ Encrypted license saved to {license_file}")


class GitHubLicenseEnforcer:
    """Enforces licensing in build pipeline using GitHub-native features"""
    
    def __init__(self, license_manager: GitHubLicenseManager):
        self.license_manager = license_manager
        
    def enforce(self, org_name: str, operation: str = 'build'):
        """
        Enforce licensing for an operation
        
        Raises:
            LicenseError if license is invalid
        """
        # Skip enforcement in GitHub Actions for the upstream repo
        if os.getenv('GITHUB_ACTIONS') and not self.license_manager.is_fork:
            return
        
        # Skip for CI testing with special env var
        if os.getenv('STYLESTACK_SKIP_LICENSE') == 'true':
            return
        
        # Validate license
        is_valid, license_info = self.license_manager.validate_license(org_name)
        
        if not is_valid:
            error_msg = license_info.get('error', 'Invalid license')
            
            print("\n" + "="*60)
            print("StyleStack Enterprise License Required")
            print("="*60)
            print(f"\nOrganization '{org_name}' requires a commercial license.")
            print(f"Error: {error_msg}")
            print("\nTo obtain a license:")
            print("1. Run the fork-setup workflow in GitHub Actions")
            print("2. Select your desired tier (professional/enterprise)")
            print("3. Complete payment at https://stylestack.dev/pricing")
            print("4. License will be automatically delivered via GitHub")
            print("\nFor open source projects:")
            print("- Add 'nonprofit', 'education', or 'community' to your org name")
            print("- Or ensure your repository has an OSS LICENSE file")
            print("="*60 + "\n")
            
            raise LicenseError(f"License required for {org_name}: {error_msg}")
        
        # Log successful validation
        source = license_info.get('source', 'unknown')
        tier = license_info.get('tier', 'unknown')
        print(f"✅ License validated: {tier} tier for {org_name} (source: {source})")


class LicenseError(Exception):
    """License validation error"""
    pass


# CLI interface
if __name__ == '__main__':
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='StyleStack GitHub License Manager')
    parser.add_argument('command', choices=['validate', 'request', 'generate', 'save'])
    parser.add_argument('--org', required=True, help='Organization name')
    parser.add_argument('--tier', help='License tier', default='professional')
    parser.add_argument('--license', help='License string')
    
    args = parser.parse_args()
    
    manager = GitHubLicenseManager()
    
    if args.command == 'validate':
        is_valid, info = manager.validate_license(args.org)
        
        if is_valid:
            print(f"✅ Valid {info['tier']} license for {args.org}")
            print(f"   Source: {info.get('source', 'unknown')}")
            print(f"   Features: {', '.join(info['features'])}")
            if info.get('expires'):
                print(f"   Expires: {info['expires']}")
        else:
            print(f"❌ Invalid license: {info.get('error', 'Unknown error')}")
            sys.exit(1)
            
    elif args.command == 'request':
        success = manager.request_license_via_oidc(args.tier)
        sys.exit(0 if success else 1)
        
    elif args.command == 'generate':
        license_str = manager.generate_license(args.org, args.tier)
        print(f"Generated license for {args.org}:")
        print(license_str)
        
    elif args.command == 'save':
        if not args.license:
            print("❌ --license required for save command")
            sys.exit(1)
        manager.save_encrypted_license(args.license, args.org)