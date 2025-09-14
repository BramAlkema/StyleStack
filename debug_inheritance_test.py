#!/usr/bin/env python3
"""
Debug script to understand inheritance test failures
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from tools.style_inheritance_core import create_inheritance_system, create_inherited_token_from_config
from tools.typography_token_system import TypographyTokenSystem

def main():
    print("🔍 Debugging Inheritance Test Failures")
    print("=" * 50)

    # Create systems
    typography_system = TypographyTokenSystem(verbose=False)
    inheritance_registry, delta_generator, inheritance_resolver = create_inheritance_system()

    # Create base token
    base_config = {
        "fontFamily": "Calibri",
        "fontSize": "12pt",
        "inheritance": {"baseStyle": "Normal", "mode": "auto"}
    }

    # Create emphasis token that inherits from base
    emphasis_config = {
        "fontWeight": 600,
        "inheritance": {"baseStyle": "base", "mode": "auto"}
    }

    print("\n📝 Creating tokens...")
    base_token = create_inherited_token_from_config("base", base_config)
    emphasis_token = create_inherited_token_from_config("emphasis", emphasis_config)

    # Delta properties should now be auto-populated by create_inherited_token_from_config
    print(f"Emphasis delta_properties: {emphasis_token.delta_properties}")

    print(f"Base token: {base_token.id}, mode: {base_token.inheritance_mode}")
    print(f"Emphasis token: {base_token.id}, mode: {emphasis_token.inheritance_mode}")
    print(f"Emphasis inherits from: {emphasis_token.base_style}")

    # Calculate EMU values
    typography_system.hierarchy_resolver._calculate_emu_values(base_token)
    typography_system.hierarchy_resolver._calculate_emu_values(emphasis_token)

    print(f"\nEMU values calculated:")
    print(f"Base font_size_emu: {base_token.font_size_emu}")
    print(f"Emphasis font_size_emu: {emphasis_token.font_size_emu}")

    # Resolve base token first
    print(f"\n🔄 Resolving base token...")
    resolved_base = inheritance_resolver.resolve_inheritance(base_token, {})
    print(f"Resolved base: {resolved_base.id}, mode: {resolved_base.inheritance_mode}")
    print(f"Base delta properties: {resolved_base.delta_properties}")
    print(f"Base should_generate_delta: {resolved_base.should_generate_delta()}")

    # Create hierarchy and resolve emphasis token
    print(f"\n🔄 Resolving emphasis token...")
    token_hierarchy = {"base": resolved_base}
    print(f"Hierarchy keys: {list(token_hierarchy.keys())}")

    resolved_emphasis = inheritance_resolver.resolve_inheritance(emphasis_token, token_hierarchy)
    print(f"Resolved emphasis: {resolved_emphasis.id}, mode: {resolved_emphasis.inheritance_mode}")
    print(f"Emphasis base_style: {resolved_emphasis.base_style}")
    print(f"Emphasis delta properties: {resolved_emphasis.delta_properties}")
    print(f"Emphasis should_generate_delta: {resolved_emphasis.should_generate_delta()}")

    # Test OOXML generation
    print(f"\n📄 Testing OOXML generation...")

    def generate_inheritance_aware_ooxml(token):
        """Generate OOXML with inheritance awareness"""
        if token.should_generate_delta():
            # Delta-style with basedOn reference
            style = {
                "w:style": {
                    "@w:type": "paragraph",
                    "@w:styleId": token.id,
                    "w:name": {"@w:val": token.id.replace('_', ' ').title()},
                    "w:basedOn": {"@w:val": token.base_style}
                }
            }

            # Add only delta properties
            if token.delta_properties:
                rpr = {}
                if "fontWeight" in token.delta_properties and token.delta_properties["fontWeight"] >= 600:
                    rpr["w:b"] = {}
                if rpr:
                    style["w:style"]["w:rPr"] = rpr

            return style
        else:
            # Complete style definition
            return {
                "w:style": {
                    "@w:type": "paragraph",
                    "@w:styleId": token.id,
                    "w:name": {"@w:val": token.id.replace('_', ' ').title()},
                    "w:rPr": {
                        "w:rFonts": {"@w:ascii": token.get_effective_property("family") or "Calibri"},
                        "w:sz": {"@w:val": "24"}  # Default
                    }
                }
            }

    ooxml_style = generate_inheritance_aware_ooxml(resolved_emphasis)
    print(f"OOXML style: {ooxml_style}")

    if "w:basedOn" in ooxml_style.get("w:style", {}):
        print("✅ basedOn reference found!")
    else:
        print("❌ basedOn reference missing")
        print(f"   should_generate_delta: {resolved_emphasis.should_generate_delta()}")
        print(f"   base_style: {resolved_emphasis.base_style}")
        print(f"   delta_properties: {resolved_emphasis.delta_properties}")

if __name__ == "__main__":
    main()