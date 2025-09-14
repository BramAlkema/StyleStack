"""
Integration tests for Typography Token System with existing StyleStack infrastructure

Tests integration with variable_resolver, token_parser, and OOXML processing pipeline.
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any

from tools.typography_token_system import TypographyTokenSystem, TypographyToken
from tools.variable_resolver import VariableResolver, ResolvedVariable
from tools.token_parser import TokenType, TokenScope


class TestTypographyTokenIntegration:
    """Integration tests with existing StyleStack components"""

    def test_integration_with_variable_resolver(self):
        """Test typography tokens integrate with VariableResolver"""
        typography_system = TypographyTokenSystem(verbose=False)
        variable_resolver = VariableResolver(verbose=False)

        # Create sample typography tokens
        typography_tokens = {
            "body": TypographyToken(
                id="body",
                font_family="Proxima Nova",
                font_size="16pt",
                font_size_emu=203200,
                line_height_emu=457200,
                baseline_grid_emu=228600
            ),
            "heading": TypographyToken(
                id="heading",
                font_family="Proxima Nova",
                font_size="24pt",
                font_size_emu=304800,
                line_height_emu=685800,
                baseline_grid_emu=228600
            )
        }

        # Convert typography tokens to ResolvedVariable format
        resolved_variables = {}
        for token_id, token in typography_tokens.items():
            # Create variables for each typography property
            if token.font_family:
                resolved_variables[f"{token_id}_font_family"] = ResolvedVariable(
                    id=f"{token_id}_font_family",
                    value=token.font_family,
                    type=TokenType.FONT,
                    scope=TokenScope.CORE,
                    source='typography_tokens'
                )

            if token.font_size_emu:
                resolved_variables[f"{token_id}_font_size_emu"] = ResolvedVariable(
                    id=f"{token_id}_font_size_emu",
                    value=str(token.font_size_emu),
                    type=TokenType.DIMENSION,
                    scope=TokenScope.CORE,
                    source='typography_tokens'
                )

            if token.line_height_emu:
                resolved_variables[f"{token_id}_line_height_emu"] = ResolvedVariable(
                    id=f"{token_id}_line_height_emu",
                    value=str(token.line_height_emu),
                    type=TokenType.DIMENSION,
                    scope=TokenScope.CORE,
                    source='typography_tokens'
                )

        # Test resolution report generation
        report = variable_resolver.generate_resolution_report(resolved_variables)

        assert report['summary']['total_variables'] == len(resolved_variables)
        assert 'typography_tokens' in report['summary']['source_breakdown']

        # Verify typography-related variables were resolved
        font_vars = [v for v in report['variables'] if 'font' in v['id']]
        assert len(font_vars) >= 2  # Should have font family variables

    def test_ooxml_paragraph_style_generation(self):
        """Test OOXML paragraph style generation produces valid structure"""
        typography_system = TypographyTokenSystem(verbose=False)

        # Create comprehensive typography tokens
        tokens = {
            "body": TypographyToken(
                id="body",
                font_family="Proxima Nova",
                font_size="16pt",
                font_size_emu=203200,
                line_height_emu=457200,  # 2x baseline (228600)
                letter_spacing_emu=1270,
                font_weight=400,
                baseline_grid_emu=228600
            ),
            "heading_h1": TypographyToken(
                id="heading.h1",
                font_family=["Proxima Nova", "Arial", "sans-serif"],
                font_size="32pt",
                font_size_emu=406400,
                line_height_emu=685800,  # 3x baseline
                font_weight="bold",
                baseline_grid_emu=228600
            ),
            "caption": TypographyToken(
                id="caption",
                font_family="Arial",
                font_size="12pt",
                font_size_emu=152400,
                line_height_emu=228600,  # 1x baseline
                font_style="italic",
                baseline_grid_emu=228600
            )
        }

        # Generate OOXML paragraph styles
        ooxml_styles = typography_system.generate_ooxml_paragraph_styles(tokens)

        # Validate structure and baseline alignment
        assert len(ooxml_styles) == 3

        for style_id, style in ooxml_styles.items():
            # Verify required OOXML structure
            assert "w:pPr" in style  # Paragraph properties
            assert "w:rPr" in style  # Run properties

            # Verify line height is baseline-aligned
            line_height_emu = int(style["w:pPr"]["w:spacing"]["@w:line"])
            assert line_height_emu % 228600 == 0  # Must be multiple of baseline

            # Verify font size conversion to half-points
            font_size_half_points = int(style["w:rPr"]["w:sz"]["@w:val"])
            assert font_size_half_points > 0
            assert font_size_half_points % 2 == 0  # Should be even (full points)

        # Test specific style properties
        body_style = ooxml_styles["body"]
        assert body_style["w:rPr"]["w:rFonts"]["@w:ascii"] == "Proxima Nova"
        assert body_style["w:rPr"]["w:spacing"]["@w:val"] == "1270"  # Letter spacing

        heading_style = ooxml_styles["heading_h1"]
        assert "w:b" in heading_style["w:rPr"]  # Bold formatting
        assert heading_style["w:rPr"]["w:rFonts"]["@w:ascii"] == "Proxima Nova"

    def test_w3c_dtcg_export_compliance(self):
        """Test W3C DTCG export produces specification-compliant tokens"""
        typography_system = TypographyTokenSystem(verbose=False)

        # Create tokens with accessibility and EMU extensions
        tokens = {
            "accessible_body": TypographyToken(
                id="accessible_body",
                font_family="Proxima Nova",
                font_size="18pt",
                font_size_emu=228600,
                line_height=1.5,
                line_height_emu=457200,
                letter_spacing="0.02em",
                font_weight=400,
                wcag_level="AAA",
                min_contrast_ratio=7.0,
                ooxml_properties={"custom": "value"}
            )
        }

        # Export to W3C DTCG format
        w3c_export = typography_system.export_w3c_dtcg_tokens(tokens)

        # Validate W3C DTCG structure
        assert "typography" in w3c_export
        token_export = w3c_export["typography"]["accessible_body"]

        # Validate required W3C DTCG properties
        assert token_export["$type"] == "typography"
        assert "$value" in token_export
        assert "$description" in token_export

        # Validate typography values
        value = token_export["$value"]
        assert value["fontFamily"] == "Proxima Nova"
        assert value["fontSize"] == "18pt"
        assert value["lineHeight"] == 1.5
        assert value["letterSpacing"] == "0.02em"
        assert value["fontWeight"] == 400

        # Validate StyleStack extensions
        extensions = token_export["$extensions"]["stylestack"]

        # EMU extensions
        assert extensions["emu"]["fontSize"] == 228600
        assert extensions["emu"]["lineHeight"] == 457200

        # Accessibility extensions
        assert extensions["accessibility"]["wcagLevel"] == "AAA"
        assert extensions["accessibility"]["minContrastRatio"] == 7.0

        # OOXML extensions
        assert extensions["ooxml"]["custom"] == "value"

    def test_baseline_grid_consistency_across_tokens(self):
        """Test baseline grid consistency across different typography tokens"""
        typography_system = TypographyTokenSystem(baseline_grid_pt=18.0, verbose=False)

        # Create design system with various font sizes
        design_tokens = {
            "typography": {
                "small": {
                    "$type": "typography",
                    "$value": {"fontSize": "12pt", "lineHeight": 1.4}
                },
                "body": {
                    "$type": "typography",
                    "$value": {"fontSize": "16pt", "lineHeight": 1.5}
                },
                "large": {
                    "$type": "typography",
                    "$value": {"fontSize": "20pt", "lineHeight": 1.3}
                },
                "huge": {
                    "$type": "typography",
                    "$value": {"fontSize": "32pt", "lineHeight": 1.2}
                }
            }
        }

        # Create token system
        tokens = typography_system.create_typography_token_system(
            design_system_tokens=design_tokens
        )

        baseline_grid_emu = 228600  # 18pt baseline

        # Verify all tokens have consistent baseline grid
        for token_id, token in tokens.items():
            assert token.baseline_grid_emu == baseline_grid_emu

            # Verify line height is baseline-aligned
            if token.line_height_emu:
                assert token.line_height_emu % baseline_grid_emu == 0

            # Verify line height is reasonable for font size
            if token.font_size_emu and token.line_height_emu:
                line_height_ratio = token.line_height_emu / token.font_size_emu
                # Line height ratio should be reasonable, but baseline snapping may cause small fonts
                # to have slightly lower ratios due to grid constraints
                assert 0.8 <= line_height_ratio <= 2.5  # Allow wider range for baseline-snapped values

    def test_hierarchy_precedence_integration(self):
        """Test token hierarchy precedence with complex override scenarios"""
        typography_system = TypographyTokenSystem(verbose=False)

        # Design system foundation
        design_tokens = {
            "typography": {
                "body": {
                    "$type": "typography",
                    "$value": {
                        "fontFamily": "System Default",
                        "fontSize": "16pt",
                        "lineHeight": 1.4,
                        "fontWeight": 400
                    }
                }
            }
        }

        # Corporate brand overrides
        corporate_tokens = {
            "typography": {
                "body": {
                    "$type": "typography",
                    "$value": {
                        "fontFamily": "Proxima Nova",  # Override
                        "letterSpacing": "0.01em"     # Addition
                    }
                }
            }
        }

        # Channel-specific adjustments
        channel_tokens = {
            "typography": {
                "body": {
                    "$type": "typography",
                    "$value": {
                        "fontSize": "18pt",          # Override for accessibility
                        "fontWeight": 500            # Override for better readability
                    }
                }
            }
        }

        # Create token system with full hierarchy
        tokens = typography_system.create_typography_token_system(
            design_system_tokens=design_tokens,
            corporate_tokens=corporate_tokens,
            channel_tokens=channel_tokens
        )

        body_token = tokens["body"]

        # Verify precedence was applied correctly
        assert body_token.font_family == "Proxima Nova"  # Corporate override
        assert body_token.font_size == "18pt"            # Channel override
        assert body_token.font_weight == 500             # Channel override
        assert body_token.line_height == 1.4             # From design system
        assert body_token.letter_spacing == "0.01em"     # Corporate addition

        # Verify EMU calculations were performed
        assert body_token.font_size_emu is not None
        assert body_token.line_height_emu is not None
        assert body_token.baseline_grid_emu is not None

    def test_accessibility_validation_integration(self):
        """Test accessibility validation works with token system"""
        typography_system = TypographyTokenSystem(verbose=False)

        # Create tokens with accessibility requirements
        tokens_with_accessibility = {
            "typography": {
                "small_text_aa": {
                    "$type": "typography",
                    "$value": {"fontSize": "16pt"},  # Meets WCAG AA
                    "$extensions": {
                        "stylestack": {
                            "accessibility": {"wcagLevel": "AA"}
                        }
                    }
                },
                "small_text_aaa": {
                    "$type": "typography",
                    "$value": {"fontSize": "18pt"},  # Meets WCAG AAA
                    "$extensions": {
                        "stylestack": {
                            "accessibility": {"wcagLevel": "AAA"}
                        }
                    }
                },
                "too_small_aa": {
                    "$type": "typography",
                    "$value": {"fontSize": "14pt"},  # Violates WCAG AA
                    "$extensions": {
                        "stylestack": {
                            "accessibility": {"wcagLevel": "AA"}
                        }
                    }
                }
            }
        }

        # Create token system
        tokens = typography_system.create_typography_token_system(
            design_system_tokens=tokens_with_accessibility
        )

        # Test validation
        validation_results = typography_system.validator.validate_token_hierarchy(tokens)

        # Should have validation error for too_small_aa
        assert "too_small_aa" in validation_results
        errors = validation_results["too_small_aa"]
        assert any("WCAG AA minimum" in error for error in errors)

        # Should not have errors for compliant tokens
        assert "small_text_aa" not in validation_results
        assert "small_text_aaa" not in validation_results


# Performance and edge case tests
class TestTypographyTokenPerformance:
    """Performance and edge case tests for typography token system"""

    def test_large_token_hierarchy_performance(self):
        """Test performance with large number of typography tokens"""
        typography_system = TypographyTokenSystem(verbose=False)

        # Generate large token hierarchy
        design_tokens = {"typography": {}}

        # Create 100 different typography tokens
        for i in range(100):
            design_tokens["typography"][f"token_{i}"] = {
                "$type": "typography",
                "$value": {
                    "fontSize": f"{12 + i % 20}pt",
                    "lineHeight": 1.2 + (i % 10) * 0.1,
                    "fontWeight": 400 + (i % 5) * 100
                }
            }

        # Measure token creation time
        import time
        start_time = time.time()

        tokens = typography_system.create_typography_token_system(
            design_system_tokens=design_tokens
        )

        end_time = time.time()
        processing_time = end_time - start_time

        # Verify results
        assert len(tokens) == 100
        assert processing_time < 1.0  # Should process 100 tokens in under 1 second

        # Verify all tokens have EMU calculations
        for token in tokens.values():
            assert token.font_size_emu is not None
            assert token.baseline_grid_emu is not None

    def test_edge_case_font_sizes(self):
        """Test typography system with edge case font sizes"""
        typography_system = TypographyTokenSystem(verbose=False)

        edge_case_tokens = {
            "typography": {
                "tiny": {
                    "$type": "typography",
                    "$value": {"fontSize": "6pt"}  # Very small
                },
                "huge": {
                    "$type": "typography",
                    "$value": {"fontSize": "144pt"}  # Very large
                },
                "fractional": {
                    "$type": "typography",
                    "$value": {"fontSize": "13.5pt"}  # Fractional
                }
            }
        }

        tokens = typography_system.create_typography_token_system(
            design_system_tokens=edge_case_tokens
        )

        # Verify EMU calculations work for edge cases
        assert tokens["tiny"].font_size_emu > 0
        assert tokens["huge"].font_size_emu > 0
        assert tokens["fractional"].font_size_emu > 0

        # Verify baseline alignment
        for token in tokens.values():
            if token.line_height_emu:
                assert token.line_height_emu % token.baseline_grid_emu == 0

    def test_invalid_token_handling(self):
        """Test handling of invalid or malformed typography tokens"""
        typography_system = TypographyTokenSystem(verbose=False)

        # Mix of valid and invalid tokens
        mixed_tokens = {
            "typography": {
                "valid": {
                    "$type": "typography",
                    "$value": {"fontSize": "16pt"}
                },
                "invalid_size": {
                    "$type": "typography",
                    "$value": {"fontSize": "invalid"}
                },
                "missing_type": {
                    "$value": {"fontSize": "18pt"}  # Missing $type
                },
                "empty_value": {
                    "$type": "typography",
                    "$value": {}  # Empty value
                }
            }
        }

        # Should handle invalid tokens gracefully
        tokens = typography_system.create_typography_token_system(
            design_system_tokens=mixed_tokens
        )

        # Should still process valid tokens
        assert "valid" in tokens
        assert tokens["valid"].font_size == "16pt"

        # Invalid tokens might be skipped or have None EMU values
        for token_id, token in tokens.items():
            if token_id == "valid":
                assert token.font_size_emu is not None