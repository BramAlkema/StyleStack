#!/usr/bin/env python3
"""
StyleStack Enterprise License Manager
Handles licensing for commercial forks and enterprise deployments
"""

import os
import json
import hmac
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from pathlib import Path
import base64

class LicenseManager:
    """Manages enterprise licensing and subscription validation"""
    
    # License tiers
    TIERS = {
        'community': {
            'price': 0,
            'features': ['basic_tokens', 'github_deployment'],
            'api_calls': 1000,
            'support': 'community'
        },
        'professional': {
            'price': 25,
            'features': ['custom_tokens', 'multi_platform', 'api_access'],
            'api_calls': 10000,
            'support': 'email'
        },
        'enterprise': {
            'price': 50,
            'features': ['unlimited_tokens', 'all_platforms', 'api_access', 'sla'],
            'api_calls': -1,  # Unlimited
            'support': 'priority'
        }
    }
    
    def __init__(self, api_endpoint: str = None):
        """Initialize license manager"""
        self.api_endpoint = api_endpoint or os.getenv(
            'STYLESTACK_API', 
            'https://api.stylestack.dev'
        )
        self.cache_dir = Path.home() / '.stylestack' / 'licenses'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def validate_license(self, license_key: str, org_name: str) -> Tuple[bool, Dict]:
        """
        Validate a license key for an organization
        
        Returns:
            Tuple of (is_valid, license_info)
        """
        # Check for community/open source usage
        if self._is_open_source(org_name):
            return True, {
                'tier': 'community',
                'org': org_name,
                'expires': None,
                'features': self.TIERS['community']['features']
            }
        
        # Try local validation first (offline mode)
        local_valid, local_info = self._validate_local(license_key, org_name)
        if local_valid:
            return local_valid, local_info
            
        # Fall back to API validation
        try:
            return self._validate_online(license_key, org_name)
        except requests.RequestException:
            # If API is down, use cached license if valid
            return self._use_cached_license(license_key, org_name)
    
    def _is_open_source(self, org_name: str) -> bool:
        """Check if organization qualifies for free community tier"""
        # Check for common open source indicators
        exempt_orgs = [
            'nonprofit', 'education', 'university', 'school',
            'foundation', 'community', 'open-source', 'foss'
        ]
        return any(indicator in org_name.lower() for indicator in exempt_orgs)
    
    def _validate_local(self, license_key: str, org_name: str) -> Tuple[bool, Dict]:
        """Validate license key locally (for offline usage)"""
        try:
            # Decode license key (base64 encoded JSON)
            decoded = base64.b64decode(license_key).decode('utf-8')
            license_data = json.loads(decoded)
            
            # Verify signature
            expected_sig = self._generate_signature(
                license_data['org'],
                license_data['tier'],
                license_data['expires']
            )
            
            if not hmac.compare_digest(license_data['signature'], expected_sig):
                return False, {}
            
            # Check organization match
            if license_data['org'] != org_name:
                return False, {}
            
            # Check expiration
            expires = datetime.fromisoformat(license_data['expires'])
            if expires < datetime.now():
                return False, {'error': 'License expired'}
            
            return True, license_data
            
        except Exception:
            return False, {}
    
    def _validate_online(self, license_key: str, org_name: str) -> Tuple[bool, Dict]:
        """Validate license with online API"""
        response = requests.post(
            f"{self.api_endpoint}/v1/license/validate",
            json={
                'license_key': license_key,
                'org_name': org_name,
                'version': self._get_version()
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            # Cache the valid license
            self._cache_license(license_key, org_name, data)
            return True, data
        elif response.status_code == 402:
            return False, {'error': 'Payment required'}
        else:
            return False, {'error': 'Invalid license'}
    
    def _use_cached_license(self, license_key: str, org_name: str) -> Tuple[bool, Dict]:
        """Use cached license for offline validation"""
        cache_file = self.cache_dir / f"{org_name}.json"
        
        if not cache_file.exists():
            return False, {'error': 'No cached license'}
        
        try:
            with open(cache_file) as f:
                cached = json.load(f)
            
            # Allow 7-day grace period for cached licenses
            cached_date = datetime.fromisoformat(cached['cached_at'])
            grace_period = cached_date + timedelta(days=7)
            
            if datetime.now() < grace_period:
                return True, cached['license_info']
            else:
                return False, {'error': 'Cached license expired'}
                
        except Exception:
            return False, {'error': 'Cache read error'}
    
    def _cache_license(self, license_key: str, org_name: str, license_info: Dict):
        """Cache valid license for offline use"""
        cache_file = self.cache_dir / f"{org_name}.json"
        
        cache_data = {
            'license_key': license_key,
            'org_name': org_name,
            'license_info': license_info,
            'cached_at': datetime.now().isoformat()
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
    
    def _generate_signature(self, org: str, tier: str, expires: str) -> str:
        """Generate HMAC signature for license validation"""
        secret = os.getenv('STYLESTACK_SECRET', 'default-secret-change-in-production')
        message = f"{org}:{tier}:{expires}"
        return hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _get_version(self) -> str:
        """Get StyleStack version"""
        try:
            from importlib.metadata import version
            return version('stylestack')
        except Exception:
            return '1.0.0'
    
    def check_feature(self, license_info: Dict, feature: str) -> bool:
        """Check if a license includes a specific feature"""
        return feature in license_info.get('features', [])
    
    def get_api_limit(self, license_info: Dict) -> int:
        """Get API call limit for license tier"""
        tier = license_info.get('tier', 'community')
        return self.TIERS[tier]['api_calls']


class LicenseEnforcer:
    """Enforces licensing in build pipeline"""
    
    def __init__(self, license_manager: LicenseManager):
        self.license_manager = license_manager
        
    def enforce(self, org_name: str, operation: str = 'build'):
        """
        Enforce licensing for an operation
        
        Raises:
            LicenseError if license is invalid
        """
        license_key = os.getenv('STYLESTACK_LICENSE')
        
        # Skip enforcement for CI/CD testing
        if os.getenv('CI') == 'true' and not license_key:
            return
        
        # Validate license
        is_valid, license_info = self.license_manager.validate_license(
            license_key or '', 
            org_name
        )
        
        if not is_valid:
            error_msg = license_info.get('error', 'Invalid license')
            
            # Provide helpful error message
            if not license_key:
                print("\n" + "="*60)
                print("StyleStack Enterprise License Required")
                print("="*60)
                print(f"\nOrganization '{org_name}' requires a commercial license.")
                print("\nOptions:")
                print("1. Purchase a license at https://stylestack.dev/pricing")
                print("2. Set STYLESTACK_LICENSE environment variable")
                print("3. Use a community organization name (nonprofit, education)")
                print("\nFor more info: https://stylestack.dev/docs/licensing")
                print("="*60 + "\n")
            else:
                print(f"\n❌ License validation failed: {error_msg}")
                
            raise LicenseError(f"License required for {org_name}: {error_msg}")
        
        # Check operation permissions
        if operation == 'api' and not self.license_manager.check_feature(license_info, 'api_access'):
            raise LicenseError(f"API access not available in {license_info['tier']} tier")
        
        # Log successful validation
        print(f"✅ License validated: {license_info['tier']} tier for {org_name}")


class LicenseError(Exception):
    """License validation error"""
    pass


# CLI interface
if __name__ == '__main__':
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='StyleStack License Manager')
    parser.add_argument('command', choices=['validate', 'info', 'generate'])
    parser.add_argument('--org', required=True, help='Organization name')
    parser.add_argument('--key', help='License key')
    parser.add_argument('--tier', help='License tier for generation')
    
    args = parser.parse_args()
    
    manager = LicenseManager()
    
    if args.command == 'validate':
        key = args.key or os.getenv('STYLESTACK_LICENSE')
        is_valid, info = manager.validate_license(key or '', args.org)
        
        if is_valid:
            print(f"✅ Valid {info['tier']} license for {args.org}")
            print(f"   Features: {', '.join(info['features'])}")
            if info.get('expires'):
                print(f"   Expires: {info['expires']}")
        else:
            print(f"❌ Invalid license: {info.get('error', 'Unknown error')}")
            sys.exit(1)
            
    elif args.command == 'info':
        print("\nStyleStack License Tiers:")
        print("-" * 50)
        for tier, details in manager.TIERS.items():
            print(f"\n{tier.upper()}")
            print(f"  Price: ${details['price']}/user/month")
            print(f"  Features: {', '.join(details['features'])}")
            print(f"  API Calls: {details['api_calls'] if details['api_calls'] > 0 else 'Unlimited'}")
            print(f"  Support: {details['support']}")