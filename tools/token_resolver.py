#!/usr/bin/env python3
"""
StyleStack Design Token Resolution Engine

Material Web-inspired token resolution with layered overrides:
Core → Channel → Organization → Group → Personal

Resolves token references like {colors.primary.500} to actual values.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

import click
import jsonschema


class TokenResolver:
    """Design token resolution engine following Material Web patterns"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.tokens: Dict[str, Any] = {}
        self.resolved: Dict[str, str] = {}
        
    def load_core_tokens(self, tokens_dir: Path = None) -> Dict[str, Any]:
        """Load core primitive tokens"""
        if tokens_dir is None:
            tokens_dir = Path("tokens")
            
        core_dir = tokens_dir / "core"
        core_tokens = {}
        
        if self.verbose:
            click.echo(f"📁 Loading core tokens from {core_dir}")
        
        # Load all core token files
        schema_path = tokens_dir / "schema" / "design-tokens.schema.json"
        with open(schema_path, "r") as schema_file:
            schema = json.load(schema_file)
        validator = jsonschema.Draft7Validator(schema)

        for token_file in core_dir.glob("*.json"):
            if self.verbose:
                click.echo(f"   📄 {token_file.name}")

            with open(token_file, "r") as f:
                file_tokens = json.load(f)

            schema_ref = file_tokens.get("$schema", "")
            if "design-tokens.schema.json" not in schema_ref:
                # Skip files that don't declare the design tokens schema
                continue

            # Validate against schema
            validator.validate(file_tokens)

            # Remove schema reference
            del file_tokens["$schema"]
            core_tokens.update(file_tokens)
        
        return core_tokens
    
    def load_layer_overrides(self, layer_path: Path) -> Dict[str, Any]:
        """Load overrides from a layer (channel, org, group, personal)"""
        if not layer_path.exists():
            return {}
            
        if self.verbose:
            click.echo(f"   🔧 {layer_path}")
            
        with open(layer_path, 'r') as f:
            layer_data = json.load(f)
            
        return layer_data.get('overrides', {})
    
    def apply_overrides(self, base_tokens: Dict[str, Any], overrides: Dict[str, str]) -> Dict[str, Any]:
        """Apply layer overrides to base tokens using dot notation"""
        result = base_tokens.copy()
        
        for dot_path, new_value in overrides.items():
            self._set_nested_value(result, dot_path, new_value)
            
        return result
    
    def _set_nested_value(self, obj: Dict[str, Any], dot_path: str, value: Any):
        """Set nested dictionary value using dot notation path"""
        keys = dot_path.split('.')
        current = obj
        
        # Navigate to parent of target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
    
    def _get_nested_value(self, obj: Dict[str, Any], dot_path: str) -> Any:
        """Get nested dictionary value using dot notation path"""
        keys = dot_path.split('.')
        current = obj
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return None
    
    def flatten_tokens(self, tokens: Dict[str, Any], prefix: str = "") -> Dict[str, str]:
        """Flatten nested token structure to dot notation dictionary"""
        flattened = {}
        
        for key, value in tokens.items():
            current_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                if 'value' in value:
                    # This is a token with value
                    flattened[current_key] = value['value']
                else:
                    # This is a nested group, recurse
                    flattened.update(self.flatten_tokens(value, current_key))
            else:
                # Direct value
                flattened[current_key] = value
                
        return flattened
    
    def resolve_token_references(self, flattened: Dict[str, str]) -> Dict[str, str]:
        """Resolve token references like {colors.primary.500} to actual values"""
        resolved = {}
        max_iterations = 10  # Prevent infinite loops
        
        for iteration in range(max_iterations):
            changed = False
            
            for key, value in flattened.items():
                if isinstance(value, str) and '{' in value:
                    # Find token references in the value
                    resolved_value = self._resolve_references_in_string(value, flattened)
                    if resolved_value != value:
                        flattened[key] = resolved_value
                        changed = True
                
                resolved[key] = flattened[key]
            
            if not changed:
                break
                
        if iteration == max_iterations - 1:
            click.echo("⚠️  Warning: Maximum resolution iterations reached")
            
        return resolved
    
    def _resolve_references_in_string(self, text: str, token_dict: Dict[str, str]) -> str:
        """Resolve all token references in a string"""
        # Pattern to match {token.path.here}
        pattern = r'\{([^}]+)\}'
        
        def replace_token(match):
            token_path = match.group(1)
            if token_path in token_dict:
                return str(token_dict[token_path])
            else:
                if self.verbose:
                    click.echo(f"⚠️  Unresolved token reference: {token_path}")
                return match.group(0)  # Return original if not found
        
        return re.sub(pattern, replace_token, text)
    
    def resolve_tokens(self, 
                      fork: Optional[str] = None,
                      org: Optional[str] = None, 
                      group: Optional[str] = None,
                      personal: Optional[str] = None,
                      channel: Optional[str] = None) -> Dict[str, str]:
        """Resolve tokens with 5-layer architecture"""
        
        if self.verbose:
            click.echo("🎨 StyleStack Token Resolution")
            click.echo("   Core → Fork → Org → Group → Personal → Channel")
        
        tokens_dir = Path("tokens")
        
        # 1. Load core tokens (primitives)
        tokens = self.load_core_tokens(tokens_dir)
        
        # 2. Apply fork overrides
        if fork:
            fork_overrides = self.load_layer_overrides(tokens_dir / "forks" / f"{fork}.json")
            tokens = self.apply_overrides(tokens, fork_overrides)
        
        # 3. Apply org overrides
        if org:
            org_overrides = self.load_layer_overrides(tokens_dir / "org" / f"{org}.json")
            tokens = self.apply_overrides(tokens, org_overrides)
        
        # 4. Apply group overrides
        if org and group:
            group_overrides = self.load_layer_overrides(tokens_dir / "org" / org / "groups" / f"{group}.json")
            tokens = self.apply_overrides(tokens, group_overrides)
        
        # 5. Apply personal overrides
        if personal:
            personal_overrides = self.load_layer_overrides(tokens_dir / "personal" / f"{personal}.json")
            tokens = self.apply_overrides(tokens, personal_overrides)
        
        # 6. Apply channel overrides (last, highest priority)
        if channel:
            channel_overrides = self.load_layer_overrides(tokens_dir / "channels" / f"{channel}.json") 
            tokens = self.apply_overrides(tokens, channel_overrides)
        
        # 7. Flatten token structure
        flattened = self.flatten_tokens(tokens)
        
        # 8. Resolve token references
        resolved = self.resolve_token_references(flattened)
        
        if self.verbose:
            click.echo(f"✅ Resolved {len(resolved)} tokens")
        
        return resolved
    
    def export_tokens(self, resolved: Dict[str, str], format: str = "json") -> str:
        """Export resolved tokens in various formats"""
        if format == "json":
            return json.dumps(resolved, indent=2)
        elif format == "css":
            css_vars = []
            for key, value in resolved.items():
                css_var = f"  --{key.replace('.', '-')}: {value};"
                css_vars.append(css_var)
            return ":root {\n" + "\n".join(css_vars) + "\n}"
        else:
            raise ValueError(f"Unsupported format: {format}")


@click.command()
@click.option('--fork', help='Fork layer (e.g. enterprise-defaults)')
@click.option('--org', help='Organization layer (e.g. acme)')
@click.option('--group', help='Group layer (e.g. marketing)')
@click.option('--personal', help='Personal layer (e.g. john-doe)')
@click.option('--channel', help='Channel layer (e.g. present, doc, finance)')
@click.option('--format', default='json', type=click.Choice(['json', 'css']), help='Output format')
@click.option('--output', '-o', help='Output file (default: stdout)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def resolve(fork, org, group, personal, channel, format, output, verbose):
    """Resolve StyleStack design tokens with layered overrides"""
    
    resolver = TokenResolver(verbose=verbose)
    
    try:
        resolved_tokens = resolver.resolve_tokens(
            fork=fork,
            org=org, 
            group=group,
            personal=personal,
            channel=channel
        )
        
        output_content = resolver.export_tokens(resolved_tokens, format)
        
        if output:
            with open(output, 'w') as f:
                f.write(output_content)
            if verbose:
                click.echo(f"💾 Tokens saved to {output}")
        else:
            click.echo(output_content)
            
    except Exception as e:
        click.echo(f"❌ Token resolution failed: {e}")
        raise


if __name__ == '__main__':
    resolve()