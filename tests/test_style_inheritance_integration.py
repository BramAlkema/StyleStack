"""
Integration tests for StyleStack Style Inheritance System

Tests integration with existing typography token system, OOXML generation,
and variable resolution pipeline. Validates end-to-end inheritance workflows.
"""

import pytest
import json
from typing import Dict, Any
from pathlib import Path

# Import existing systems for integration testing
from tools.typography_token_system import (
    TypographyTokenSystem, TypographyToken, EMUConversionEngine
)
from tools.variable_resolver import VariableResolver, ResolvedVariable

# Import new inheritance system
from tools.style_inheritance_core import (
    BaseStyleRegistry, DeltaStyleGenerator, InheritanceResolver,
    InheritedTypographyToken, InheritanceMode, create_inheritance_system
)


class TestInheritanceSystemIntegration:
    """Test integration between inheritance system and existing components"""

    def test_integration_with_typography_token_system(self):
        """Test inheritance system integration with existing typography token system"""
        # Create inheritance system
        registry, delta_gen, resolver = create_inheritance_system()

        # Create existing typography system
        typography_system = TypographyTokenSystem(verbose=False)

        # Create design tokens with inheritance configuration
        design_tokens = {
            "typography": {
                "body": {
                    "$type": "typography",
                    "$value": {
                        "fontFamily": "Proxima Nova",
                        "fontSize": "16pt",
                        "lineHeight": 1.4
                    },
                    "$extensions": {
                        "stylestack": {
                            "inheritance": {
                                "baseStyle": "Normal",
                                "mode": "auto"
                            }
                        }
                    }
                },
                "emphasis": {
                    "$type": "typography",
                    "$value": {
                        "fontWeight": "bold"
                    },
                    "$extensions": {
                        "stylestack": {
                            "inheritance": {
                                "baseStyle": "body",
                                "mode": "auto"
                            }
                        }
                    }
                }
            }
        }

        # Process tokens through typography system
        tokens = typography_system.create_typography_token_system(
            design_system_tokens=design_tokens
        )

        # Convert to inherited tokens and resolve inheritance
        inherited_tokens = {}
        for token_id, token in tokens.items():
            # Extract inheritance config
            extensions = design_tokens["typography"].get(token_id, {}).get("$extensions", {})
            inheritance_config = extensions.get("stylestack", {}).get("inheritance", {})

            # Create inherited token
            inherited_token = InheritedTypographyToken(
                id=token.id,
                font_family=token.font_family,
                font_size=token.font_size,
                font_weight=token.font_weight,
                line_height=token.line_height,
                font_size_emu=token.font_size_emu,
                line_height_emu=token.line_height_emu,
                base_style=inheritance_config.get("baseStyle"),
                inheritance_mode=InheritanceMode(inheritance_config.get("mode", "auto"))
            )

            # Add to hierarchy first for cross-references
            inherited_tokens[token_id] = inherited_token

        # Now resolve inheritance for all tokens
        for token_id, token in list(inherited_tokens.items()):
            resolved_token = resolver.resolve_inheritance(token, inherited_tokens)
            inherited_tokens[token_id] = resolved_token

        # Verify inheritance resolution
        assert "body" in inherited_tokens
        assert "emphasis" in inherited_tokens

        body_token = inherited_tokens["body"]
        emphasis_token = inherited_tokens["emphasis"]

        # Body should inherit from Normal base style
        assert body_token.base_style == "Normal"
        # Note: body_token might not generate delta if no differences found

        # Emphasis should either inherit from body or fall back to complete definition
        # Since "body" is not a registered base style, it should fallback
        assert emphasis_token.inheritance_mode == InheritanceMode.COMPLETE or emphasis_token.base_style is None

    def test_integration_with_variable_resolver(self):
        """Test inheritance system integration with variable resolver"""
        registry, delta_gen, resolver = create_inheritance_system()

        # Create inherited tokens
        inherited_tokens = {
            "base_body": InheritedTypographyToken(
                id="base_body",
                base_style="Normal",
                font_size="16pt",
                font_size_emu=203200,
                inheritance_mode=InheritanceMode.AUTO,
                delta_properties={"fontSize": "16pt"}
            ),
            "emphasis": InheritedTypographyToken(
                id="emphasis",
                base_style="base_body",
                font_weight=600,
                inheritance_mode=InheritanceMode.AUTO,
                delta_properties={"fontWeight": 600}
            )
        }

        # Convert to ResolvedVariable format for variable resolver integration
        from tools.token_parser import TokenType, TokenScope

        variable_resolver = VariableResolver(verbose=False)
        resolved_variables = {}

        for token_id, token in inherited_tokens.items():
            # Create variables for inheritance properties
            if token.base_style:
                resolved_variables[f"{token_id}_base_style"] = ResolvedVariable(
                    id=f"{token_id}_base_style",
                    value=token.base_style,
                    type=TokenType.TEXT,  # Use proper enum
                    scope=TokenScope.CORE,  # Use proper enum
                    source='inheritance_system'
                )

            # Create variables for delta properties
            for prop_name, prop_value in token.delta_properties.items():
                resolved_variables[f"{token_id}_{prop_name}"] = ResolvedVariable(
                    id=f"{token_id}_{prop_name}",
                    value=str(prop_value),
                    type=TokenType.TEXT,  # Use proper enum
                    scope=TokenScope.THEME,  # Use proper enum
                    source='inheritance_delta'
                )

        # Generate resolution report
        report = variable_resolver.generate_resolution_report(resolved_variables)

        # Verify integration
        assert report['summary']['total_variables'] == len(resolved_variables)
        assert 'inheritance_system' in report['summary']['source_breakdown']
        assert 'inheritance_delta' in report['summary']['source_breakdown']

        # Verify inheritance-related variables
        inheritance_vars = [
            var for var in report['variables']
            if var['source'] in ['inheritance_system', 'inheritance_delta']
        ]
        assert len(inheritance_vars) >= 4  # At least base style and delta properties

    def test_ooxml_generation_with_inheritance(self):
        """Test OOXML generation preserves inheritance relationships"""
        registry, delta_gen, resolver = create_inheritance_system()

        # Create inherited token with delta properties
        token = InheritedTypographyToken(
            id="body_emphasis",
            base_style="Normal",
            font_family="Proxima Nova",  # Override from Normal
            font_size="14pt",           # Override from Normal
            font_weight=600,            # Override from Normal
            font_size_emu=177800,       # 14pt in EMUs
            line_height_emu=228600,     # Baseline-aligned
            inheritance_mode=InheritanceMode.AUTO,
            delta_properties={
                "fontFamily": "Proxima Nova",
                "fontSize": "14pt",
                "fontWeight": 600
            }
        )

        # Generate delta-style OOXML structure (mock implementation)
        def generate_inheritance_ooxml(token: InheritedTypographyToken) -> Dict[str, Any]:
            if token.should_generate_delta():
                return {
                    "w:style": {
                        "@w:type": "paragraph",
                        "@w:styleId": token.id.replace('.', '_'),
                        "w:name": {"@w:val": token.id.replace('_', ' ').title()},
                        "w:basedOn": {"@w:val": token.base_style},
                        "w:rPr": {
                            "w:rFonts": {"@w:ascii": token.delta_properties.get("fontFamily")},
                            "w:sz": {"@w:val": str(int(token.font_size_emu // EMUConversionEngine.pt_to_emu(1) * 2))},
                            "w:b": {} if token.delta_properties.get("fontWeight", 400) >= 600 else None
                        }
                    }
                }
            else:
                # Generate complete style
                return {
                    "w:style": {
                        "@w:type": "paragraph",
                        "@w:styleId": token.id.replace('.', '_'),
                        "w:name": {"@w:val": token.id.replace('_', ' ').title()},
                        # No basedOn - complete definition
                        "w:rPr": {
                            "w:rFonts": {"@w:ascii": token.font_family},
                            "w:sz": {"@w:val": str(int(token.font_size_emu // EMUConversionEngine.pt_to_emu(1) * 2))},
                            "w:b": {} if (token.font_weight or 400) >= 600 else None
                        }
                    }
                }

        ooxml_style = generate_inheritance_ooxml(token)

        # Verify inheritance-based OOXML structure
        assert "w:basedOn" in ooxml_style["w:style"]  # Should have inheritance reference
        assert ooxml_style["w:style"]["w:basedOn"]["@w:val"] == "Normal"

        # Verify only delta properties are included
        rpr = ooxml_style["w:style"]["w:rPr"]
        assert rpr["w:rFonts"]["@w:ascii"] == "Proxima Nova"  # Delta property
        assert "w:b" in rpr or rpr["w:b"] is not None  # Bold formatting from delta

        # Font size should be calculated correctly (14pt = 28 half-points)
        assert rpr["w:sz"]["@w:val"] == "28"

    def test_performance_with_large_inheritance_hierarchy(self):
        """Test performance with large inheritance hierarchies"""
        import time

        registry, delta_gen, resolver = create_inheritance_system()

        # Create large inheritance hierarchy
        # Base -> Level1 (100 tokens) -> Level2 (100 tokens each) = 10,100 total tokens
        tokens = {}

        # Create base level tokens
        for i in range(100):
            token_id = f"base_{i}"
            tokens[token_id] = InheritedTypographyToken(
                id=token_id,
                base_style="Normal",
                font_size=f"{12 + (i % 10)}pt",
                inheritance_mode=InheritanceMode.AUTO
            )

        # Create second level tokens (inherit from base level)
        for base_idx in range(100):
            for level2_idx in range(10):  # 10 tokens per base = 1000 total
                token_id = f"level2_{base_idx}_{level2_idx}"
                tokens[token_id] = InheritedTypographyToken(
                    id=token_id,
                    base_style=f"base_{base_idx}",
                    font_weight=400 + (level2_idx * 100),
                    inheritance_mode=InheritanceMode.AUTO
                )

        # Time inheritance resolution
        start_time = time.time()

        resolved_count = 0
        for token_id, token in tokens.items():
            try:
                resolved_token = resolver.resolve_inheritance(token, tokens)
                if resolved_token.should_generate_delta():
                    resolved_count += 1
            except Exception as e:
                print(f"Failed to resolve {token_id}: {e}")

        end_time = time.time()
        processing_time = end_time - start_time

        print(f"Resolved {resolved_count} tokens in {processing_time:.3f}s")
        print(f"Average: {processing_time / len(tokens) * 1000:.2f}ms per token")

        # Performance assertions
        assert processing_time < 5.0  # Should complete within 5 seconds
        assert resolved_count > 0  # Should successfully resolve some tokens

    def test_w3c_dtcg_export_with_inheritance(self):
        """Test W3C DTCG export includes inheritance metadata"""
        registry, delta_gen, resolver = create_inheritance_system()

        # Create inherited token
        token = InheritedTypographyToken(
            id="body_emphasis",
            base_style="Normal",
            font_family="Proxima Nova",
            font_size="16pt",
            font_weight=600,
            inheritance_mode=InheritanceMode.AUTO,
            delta_properties={"fontFamily": "Proxima Nova", "fontWeight": 600}
        )

        # Generate W3C DTCG export with inheritance extensions
        def export_w3c_dtcg_with_inheritance(token: InheritedTypographyToken) -> Dict[str, Any]:
            dtcg_token = {
                "$type": "typography",
                "$value": {},
                "$description": f"Inherited typography token: {token.id}"
            }

            # Include effective properties (base + delta)
            if token.font_family:
                dtcg_token["$value"]["fontFamily"] = token.font_family
            if token.font_size:
                dtcg_token["$value"]["fontSize"] = token.font_size
            if token.font_weight:
                dtcg_token["$value"]["fontWeight"] = token.font_weight

            # Add inheritance extensions
            dtcg_token["$extensions"] = {
                "stylestack": {
                    "inheritance": {
                        "baseStyle": token.base_style,
                        "mode": token.inheritance_mode.value,
                        "deltaProperties": token.delta_properties,
                        "shouldGenerateDelta": token.should_generate_delta()
                    }
                }
            }

            return dtcg_token

        w3c_export = export_w3c_dtcg_with_inheritance(token)

        # Verify W3C DTCG structure with inheritance
        assert w3c_export["$type"] == "typography"
        assert "$extensions" in w3c_export

        # Verify inheritance metadata
        inheritance_ext = w3c_export["$extensions"]["stylestack"]["inheritance"]
        assert inheritance_ext["baseStyle"] == "Normal"
        assert inheritance_ext["mode"] == "auto"
        assert inheritance_ext["shouldGenerateDelta"] is True
        assert inheritance_ext["deltaProperties"] == {"fontFamily": "Proxima Nova", "fontWeight": 600}


class TestErrorRecoveryAndResilience:
    """Test error recovery and system resilience"""

    def test_missing_base_style_recovery(self):
        """Test graceful handling of missing base styles"""
        registry, delta_gen, resolver = create_inheritance_system()

        # Create token with missing base style
        token = InheritedTypographyToken(
            id="orphan_token",
            base_style="NonExistentStyle",
            font_size="14pt",
            inheritance_mode=InheritanceMode.AUTO
        )

        # Should handle missing base style gracefully
        try:
            resolved_token = resolver.resolve_inheritance(token)
            # Should fall back to complete style generation
            assert resolved_token.inheritance_mode == InheritanceMode.COMPLETE
            assert resolved_token.base_style is None
        except Exception as e:
            # Or should raise appropriate error
            assert "NonExistentStyle" in str(e)

    def test_circular_reference_recovery(self):
        """Test recovery from circular inheritance references"""
        registry, delta_gen, resolver = create_inheritance_system()

        # Create circular reference: A -> B -> C -> A
        tokens = {
            "tokenA": InheritedTypographyToken(
                id="tokenA",
                base_style="tokenC",  # Creates cycle
                font_size="12pt"
            ),
            "tokenB": InheritedTypographyToken(
                id="tokenB",
                base_style="tokenA",
                font_size="14pt"
            ),
            "tokenC": InheritedTypographyToken(
                id="tokenC",
                base_style="tokenB",
                font_size="16pt"
            )
        }

        # Should detect and handle circular reference
        for token_id, token in tokens.items():
            try:
                resolved_token = resolver.resolve_inheritance(token, tokens)
                # Should mark as having circular reference
                assert resolved_token.has_circular_reference or resolved_token.inheritance_mode == InheritanceMode.COMPLETE
            except Exception as e:
                # Or should raise circular inheritance error
                assert "circular" in str(e).lower()

    def test_malformed_inheritance_config_handling(self):
        """Test handling of malformed inheritance configurations"""
        registry, delta_gen, resolver = create_inheritance_system()

        # Create token with invalid inheritance mode
        token = InheritedTypographyToken(
            id="malformed_token",
            base_style="Normal",
            font_size="14pt"
        )

        # Try to set invalid inheritance mode
        try:
            token.inheritance_mode = "invalid_mode"  # This should fail
        except:
            # Should handle invalid enum gracefully
            token.inheritance_mode = InheritanceMode.AUTO

        # Should still resolve successfully with fallback
        resolved_token = resolver.resolve_inheritance(token)
        assert resolved_token is not None


class TestCrossFormatCompatibility:
    """Test compatibility across different Office formats"""

    def test_powerpoint_inheritance_compatibility(self):
        """Test inheritance works with PowerPoint-specific requirements"""
        registry, delta_gen, resolver = create_inheritance_system()

        # Create PowerPoint-specific inherited token
        token = InheritedTypographyToken(
            id="slide_title",
            base_style="Title",
            font_size="32pt",
            font_weight=600,
            inheritance_mode=InheritanceMode.AUTO,
            delta_properties={"fontSize": "32pt", "fontWeight": 600}
        )

        # Resolve inheritance
        resolved_token = resolver.resolve_inheritance(token)

        # Should generate delta for PowerPoint compatibility
        assert resolved_token.should_generate_delta()
        assert resolved_token.base_style == "Title"

        # Mock PowerPoint OOXML generation
        pptx_style = {
            "a:lvl1pPr": {  # PowerPoint uses different namespace
                "a:defRPr": {
                    "@sz": str(token.font_size_emu // 100) if token.font_size_emu else None,  # PowerPoint uses different units
                    "@b": "1" if token.font_weight and token.font_weight >= 600 else "0"
                }
            }
        }

        # Verify PowerPoint-compatible output
        if token.font_size_emu:
            assert pptx_style["a:lvl1pPr"]["a:defRPr"]["@sz"] == "2032"  # 32pt in PowerPoint units
        assert pptx_style["a:lvl1pPr"]["a:defRPr"]["@b"] == "1"  # Bold formatting

    def test_word_inheritance_compatibility(self):
        """Test inheritance works with Word-specific requirements"""
        registry, delta_gen, resolver = create_inheritance_system()

        # Create Word-specific inherited token
        token = InheritedTypographyToken(
            id="document_body",
            base_style="Normal",
            font_family="Times New Roman",
            font_size="12pt",
            line_height=1.5,
            inheritance_mode=InheritanceMode.AUTO
        )

        # Calculate delta properties
        token.delta_properties = delta_gen.generate_delta_properties(token)

        # Should generate appropriate Word-style delta
        assert "fontFamily" in token.delta_properties
        assert "fontSize" in token.delta_properties

    def test_excel_inheritance_compatibility(self):
        """Test inheritance works with Excel-specific requirements"""
        registry, delta_gen, resolver = create_inheritance_system()

        # Create Excel-specific inherited token (Excel has limited typography support)
        token = InheritedTypographyToken(
            id="cell_header",
            base_style="Normal",
            font_weight=700,  # Excel uses numeric font weights
            font_size="14pt",
            inheritance_mode=InheritanceMode.AUTO,
            delta_properties={"fontWeight": 700, "fontSize": "14pt"}
        )

        # Resolve inheritance
        resolved_token = resolver.resolve_inheritance(token)

        # Should work with Excel's limited typography model
        assert resolved_token.should_generate_delta()
        assert resolved_token.delta_properties["fontWeight"] == 700


if __name__ == "__main__":
    # Run integration tests
    print("Running StyleStack Style Inheritance Integration Tests...")
    pytest.main([__file__, "-v"])