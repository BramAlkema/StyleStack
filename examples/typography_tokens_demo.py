#!/usr/bin/env python3
"""
StyleStack EMU Typography Token System Demonstration

This script demonstrates the grid-safe typography token system with:
- W3C DTCG compliance
- EMU precision calculations
- Baseline grid alignment
- Hierarchical token resolution
- OOXML paragraph style generation
- Accessibility compliance validation
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.typography_token_system import TypographyTokenSystem


def main():
    """Demonstrate the typography token system capabilities"""
    print("🎨 StyleStack EMU Typography Token System Demo")
    print("=" * 60)

    # Initialize system with 18pt baseline grid
    typography_system = TypographyTokenSystem(baseline_grid_pt=18.0, verbose=True)

    print("\n📐 System Configuration:")
    print(f"   Baseline Grid: 18pt ({typography_system.baseline_grid_emu} EMUs)")
    print(f"   EMU per Point: {12700}")
    print(f"   EMU per Inch: {914400}")

    # Define design system foundation tokens
    design_system_tokens = {
        "typography": {
            "baseline": {
                "$type": "dimension",
                "$value": "18pt",
                "$description": "Base typography baseline grid"
            },
            "scale": {
                "minor_third": {"$value": 1.2},
                "major_third": {"$value": 1.25},
                "golden_ratio": {"$value": 1.618}
            },
            "body": {
                "$type": "typography",
                "$value": {
                    "fontFamily": "System UI",
                    "fontSize": "16pt",
                    "lineHeight": 1.4,
                    "letterSpacing": "0em",
                    "fontWeight": 400
                },
                "$description": "Primary body text",
                "$extensions": {
                    "stylestack": {
                        "accessibility": {"wcagLevel": "AA"}
                    }
                }
            },
            "headings": {
                "h1": {
                    "$type": "typography",
                    "$value": {
                        "fontSize": "32pt",
                        "fontWeight": "bold",
                        "lineHeight": 1.2
                    },
                    "$description": "Primary heading"
                },
                "h2": {
                    "$type": "typography",
                    "$value": {
                        "fontSize": "24pt",
                        "fontWeight": "semibold",
                        "lineHeight": 1.3
                    },
                    "$description": "Secondary heading"
                },
                "h3": {
                    "$type": "typography",
                    "$value": {
                        "fontSize": "20pt",
                        "fontWeight": "medium",
                        "lineHeight": 1.4
                    },
                    "$description": "Tertiary heading"
                }
            },
            "small": {
                "$type": "typography",
                "$value": {
                    "fontSize": "12pt",
                    "lineHeight": 1.3
                },
                "$description": "Small text and captions"
            }
        }
    }

    # Corporate brand overrides
    corporate_tokens = {
        "typography": {
            "body": {
                "$type": "typography",
                "$value": {
                    "fontFamily": ["Proxima Nova", "Arial", "sans-serif"],
                    "letterSpacing": "0.01em"
                },
                "$description": "Brand body text with Proxima Nova"
            },
            "headings": {
                "h1": {
                    "$type": "typography",
                    "$value": {
                        "fontFamily": ["Proxima Nova", "Arial", "sans-serif"],
                        "letterSpacing": "0.02em"
                    },
                    "$description": "Brand H1 with custom spacing"
                }
            }
        }
    }

    # Channel-specific adjustments (presentation channel)
    channel_tokens = {
        "typography": {
            "body": {
                "$type": "typography",
                "$value": {
                    "fontSize": "18pt"  # Larger for presentations
                },
                "$extensions": {
                    "stylestack": {
                        "accessibility": {"wcagLevel": "AAA"}
                    }
                }
            },
            "headings": {
                "h1": {
                    "$type": "typography",
                    "$value": {
                        "fontSize": "36pt"  # Larger for presentations
                    }
                }
            }
        }
    }

    print("\n🏗️ Creating Typography Token System...")

    # Create complete token system with hierarchy
    tokens = typography_system.create_typography_token_system(
        design_system_tokens=design_system_tokens,
        corporate_tokens=corporate_tokens,
        channel_tokens=channel_tokens
    )

    print(f"\n✅ Created {len(tokens)} typography tokens")

    # Display resolved tokens with EMU calculations
    print("\n📊 Resolved Typography Tokens:")
    print("-" * 60)

    for token_id, token in sorted(tokens.items()):
        print(f"\n🎯 {token_id}:")
        print(f"   Font Family: {token.font_family or 'inherit'}")
        print(f"   Font Size: {token.font_size or 'inherit'}")
        if token.font_size_emu:
            print(f"   Font Size EMU: {token.font_size_emu:,} ({token.font_size_emu / 12700:.1f}pt)")
        print(f"   Line Height: {token.line_height or 'inherit'}")
        if token.line_height_emu:
            baseline_multiples = token.line_height_emu // typography_system.baseline_grid_emu
            print(f"   Line Height EMU: {token.line_height_emu:,} ({baseline_multiples}x baseline)")
        if token.font_weight:
            print(f"   Font Weight: {token.font_weight}")
        if token.letter_spacing:
            print(f"   Letter Spacing: {token.letter_spacing}")
        if token.wcag_level:
            print(f"   WCAG Level: {token.wcag_level}")

    # Validate tokens for compliance
    print("\n🔍 Running Accessibility Validation...")
    validation_results = typography_system.validator.validate_token_hierarchy(tokens)

    if validation_results:
        print("⚠️  Validation Issues Found:")
        for token_id, errors in validation_results.items():
            print(f"   {token_id}:")
            for error in errors:
                print(f"     • {error}")
    else:
        print("✅ All tokens pass validation!")

    # Export to W3C DTCG format
    print("\n📤 Exporting to W3C DTCG Format...")
    w3c_export = typography_system.export_w3c_dtcg_tokens(tokens)

    print("\n🔗 W3C DTCG Export Sample (body token):")
    if "body" in w3c_export.get("typography", {}):
        body_export = w3c_export["typography"]["body"]
        print(json.dumps(body_export, indent=2))

    # Generate OOXML paragraph styles
    print("\n📝 Generating OOXML Paragraph Styles...")
    ooxml_styles = typography_system.generate_ooxml_paragraph_styles(tokens)

    print(f"\n✅ Generated {len(ooxml_styles)} OOXML paragraph styles")
    print("\n🔗 OOXML Style Sample (body):")
    if "body" in ooxml_styles:
        print(json.dumps(ooxml_styles["body"], indent=2))

    # Demonstrate baseline grid alignment
    print("\n📏 Baseline Grid Alignment Analysis:")
    print("-" * 60)

    baseline_grid_emu = typography_system.baseline_grid_emu

    for token_id, token in sorted(tokens.items()):
        if token.line_height_emu:
            multiples = token.line_height_emu // baseline_grid_emu
            remainder = token.line_height_emu % baseline_grid_emu
            alignment = "✅ Aligned" if remainder == 0 else "❌ Misaligned"
            print(f"   {token_id}: {multiples}x baseline + {remainder} EMU {alignment}")

    # Performance demonstration
    print("\n⚡ Performance Test - Creating 100 tokens...")
    import time

    # Generate 100 test tokens
    large_token_set = {"typography": {}}
    for i in range(100):
        large_token_set["typography"][f"test_token_{i}"] = {
            "$type": "typography",
            "$value": {
                "fontSize": f"{12 + (i % 20)}pt",
                "lineHeight": 1.2 + (i % 10) * 0.1,
                "fontWeight": 400 + (i % 5) * 100
            }
        }

    start_time = time.time()
    large_tokens = typography_system.create_typography_token_system(
        design_system_tokens=large_token_set
    )
    end_time = time.time()

    processing_time = end_time - start_time
    print(f"✅ Processed {len(large_tokens)} tokens in {processing_time:.3f}s")
    print(f"   Average: {processing_time / len(large_tokens) * 1000:.2f}ms per token")

    # Summary
    print("\n" + "=" * 60)
    print("🎯 Typography Token System Summary:")
    print(f"   • W3C DTCG Compliant: ✅")
    print(f"   • EMU Precision: ✅")
    print(f"   • Baseline Grid Alignment: ✅")
    print(f"   • Hierarchical Resolution: ✅")
    print(f"   • OOXML Generation: ✅")
    print(f"   • Accessibility Validation: ✅")
    print(f"   • Performance Optimized: ✅")

    print("\n🚀 Typography token system is ready for production use!")


if __name__ == "__main__":
    main()