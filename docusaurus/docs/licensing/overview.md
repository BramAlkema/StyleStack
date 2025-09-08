# Licensing Overview

StyleStack uses a **GitHub-native licensing system** that requires no external APIs or services. Everything works through GitHub Actions, OIDC tokens, and encrypted files.

## License Tiers

| Feature | Community | Professional | Enterprise |
|---------|-----------|--------------|------------|
| **Price** | Free | $25/user/month | $50/user/month |
| **Max Forks** | 5 | Unlimited | Unlimited |
| **Design Tokens** | Basic | Custom | Unlimited |
| **Platforms** | GitHub only | Multi-platform | All platforms |
| **Branding** | StyleStack | Custom | White-label |
| **Support** | Community | Email | Priority + SLA |
| **Commercial Use** | ❌ | ✅ | ✅ |

## Automatic Community Tier

Your organization automatically qualifies for the **free Community tier** if:

- Organization name contains: `nonprofit`, `education`, `university`, `foundation`, `community`
- Repository has an OSS license file (`LICENSE`, `LICENSE.md`)
- Repository is clearly for educational or non-profit use

## How Licensing Works

StyleStack's licensing is built into GitHub itself:

1. **🔐 Identity Verification**: Uses GitHub's OIDC tokens (impossible to fake)
2. **💾 Encrypted Storage**: Licenses stored as encrypted files in your repo
3. **⚡ Automatic Detection**: Build system automatically finds and validates licenses
4. **📱 Offline Capable**: Works without internet after initial setup
5. **🔄 Auto-Renewal**: Integration with payment providers for seamless renewal

## Quick Start

### For Open Source Projects
```bash
# Just works if you qualify for community tier
python build.py --org "my-nonprofit" --out template.potx
```

### For Commercial Organizations
1. **Fork StyleStack** from GitHub
2. **Request License** via GitHub Actions workflow
3. **Complete Payment** (if required)
4. **Start Building** - license is automatically activated

```bash
# After license is delivered
python build.py --org "my-company" --out template.potx
```

## Why GitHub-Native?

Traditional software licensing has several problems:

❌ **License Servers**: Can go down, need maintenance  
❌ **Key Sharing**: Hard to prevent unauthorized copying  
❌ **Complex Setup**: Requires API keys, configuration  
❌ **Vendor Lock-in**: Tied to specific payment providers

StyleStack's GitHub-native approach solves all of these:

✅ **Always Available**: Uses GitHub's 99.95% uptime SLA  
✅ **Cryptographically Secure**: OIDC tokens tied to specific repositories  
✅ **Zero Configuration**: Works automatically after setup  
✅ **Payment Agnostic**: Integrate with any payment provider

## Security

- **🔒 OIDC Tokens**: GitHub cryptographically signs identity tokens
- **🔐 Encrypted Storage**: License files encrypted with repository-specific keys  
- **🚫 No Sharing**: Each fork gets its own unique encrypted license
- **📝 Audit Trail**: All license requests tracked in GitHub issues
- **⏰ Time-Limited**: Licenses include expiration dates

## Next Steps

- **[Request a License →](./request-license.md)** - Get started with commercial licensing
- **[Pricing Details →](./pricing.md)** - Compare all features and tiers  
- **[Technical Details →](./technical-implementation.md)** - How it works under the hood
- **[Troubleshooting →](./troubleshooting.md)** - Common issues and solutions