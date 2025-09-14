"""
Unit tests for StyleStack EMU Typography Token System

Tests W3C DTCG compliance, EMU conversion accuracy, baseline grid alignment,
and hierarchical token resolution.
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any

from tools.typography_token_system import (
    TypographyToken,
    EMUConversionEngine,
    BaselineGridEngine,
    TypographyTokenHierarchyResolver,
    TypographyTokenValidator,
    TypographyTokenSystem,
    EMU_PER_POINT,
    EMU_PER_INCH,
    BASELINE_GRIDS_EMU
)


class TestEMUConversionEngine:
    """Test EMU conversion algorithms with precision requirements"""

    def test_pt_to_emu_conversion(self):
        """Test point-to-EMU conversion with sub-pixel precision"""
        # Test standard point sizes
        assert EMUConversionEngine.pt_to_emu(12) == 152400  # 12 * 12700
        assert EMUConversionEngine.pt_to_emu(16) == 203200  # 16 * 12700
        assert EMUConversionEngine.pt_to_emu(18) == 228600  # 18 * 12700
        assert EMUConversionEngine.pt_to_emu(24) == 304800  # 24 * 12700

        # Test fractional points
        assert EMUConversionEngine.pt_to_emu(12.5) == 158750
        assert abs(EMUConversionEngine.pt_to_emu(16.75) - 212675) <= 100  # Allow small rounding differences

    def test_px_to_emu_conversion(self):
        """Test pixel-to-EMU conversion with DPI consideration"""
        # Test 96 DPI (default)
        assert EMUConversionEngine.px_to_emu(16) == 152400  # 16px at 96 DPI = 12pt
        assert EMUConversionEngine.px_to_emu(24) == 228600  # 24px at 96 DPI = 18pt

        # Test 72 DPI
        assert EMUConversionEngine.px_to_emu(12, dpi=72) == 152400  # 12px at 72 DPI = 12pt
        assert EMUConversionEngine.px_to_emu(18, dpi=72) == 228600  # 18px at 72 DPI = 18pt

    def test_emu_to_pt_conversion(self):
        """Test EMU-to-point conversion accuracy"""
        assert abs(EMUConversionEngine.emu_to_pt(152400) - 12.0) < 0.001
        assert abs(EMUConversionEngine.emu_to_pt(203200) - 16.0) < 0.001
        assert abs(EMUConversionEngine.emu_to_pt(228600) - 18.0) < 0.001

    def test_emu_to_px_conversion(self):
        """Test EMU-to-pixel conversion with DPI"""
        assert abs(EMUConversionEngine.emu_to_px(152400, dpi=96) - 16.0) < 0.001
        assert abs(EMUConversionEngine.emu_to_px(228600, dpi=96) - 24.0) < 0.001

    def test_parse_dimension_to_emu(self):
        """Test dimension string parsing with various units"""
        # Point dimensions
        assert EMUConversionEngine.parse_dimension_to_emu("12pt") == 152400
        assert EMUConversionEngine.parse_dimension_to_emu("16pt") == 203200
        assert EMUConversionEngine.parse_dimension_to_emu("18pt") == 228600

        # Pixel dimensions
        assert EMUConversionEngine.parse_dimension_to_emu("16px") == 152400
        assert EMUConversionEngine.parse_dimension_to_emu("24px") == 228600

        # Relative dimensions (assuming 16pt base)
        assert EMUConversionEngine.parse_dimension_to_emu("1rem") == 203200  # 16pt
        assert EMUConversionEngine.parse_dimension_to_emu("1.5em") == 304800  # 24pt

        # Invalid dimensions
        assert EMUConversionEngine.parse_dimension_to_emu("invalid") is None
        assert EMUConversionEngine.parse_dimension_to_emu("") is None
        assert EMUConversionEngine.parse_dimension_to_emu(None) is None

    def test_conversion_roundtrip_accuracy(self):
        """Test roundtrip conversion accuracy"""
        original_pt = 16.5
        emu = EMUConversionEngine.pt_to_emu(original_pt)
        converted_pt = EMUConversionEngine.emu_to_pt(emu)
        assert abs(original_pt - converted_pt) < 0.001

        original_px = 22.75
        emu = EMUConversionEngine.px_to_emu(original_px)
        converted_px = EMUConversionEngine.emu_to_px(emu)
        assert abs(original_px - converted_px) < 0.001


class TestBaselineGridEngine:
    """Test baseline grid calculations and snapping algorithms"""

    def test_baseline_grid_initialization(self):
        """Test baseline grid engine initialization with different grid sizes"""
        # Default 18pt grid
        engine = BaselineGridEngine()
        assert engine.baseline_grid_emu == BASELINE_GRIDS_EMU["18pt"]
        assert abs(engine.baseline_grid_pt - 18.0) < 0.001

        # Custom 24pt grid
        engine_24 = BaselineGridEngine(BASELINE_GRIDS_EMU["24pt"])
        assert engine_24.baseline_grid_emu == BASELINE_GRIDS_EMU["24pt"]
        assert abs(engine_24.baseline_grid_pt - 24.0) < 0.001

    def test_snap_to_baseline(self):
        """Test baseline grid snapping algorithm"""
        engine = BaselineGridEngine(BASELINE_GRIDS_EMU["18pt"])  # 228600 EMUs

        # Test exact multiples
        assert engine.snap_to_baseline(228600) == 228600  # 1x baseline
        assert engine.snap_to_baseline(457200) == 457200  # 2x baseline
        assert engine.snap_to_baseline(685800) == 685800  # 3x baseline

        # Test snapping behavior
        assert engine.snap_to_baseline(200000) == 228600  # Snap up to 1x
        assert engine.snap_to_baseline(300000) == 228600  # Snap down to 1x
        assert engine.snap_to_baseline(400000) == 457200  # Snap up to 2x
        assert engine.snap_to_baseline(500000) == 457200  # Snap down to 2x

    def test_calculate_line_height_for_font_size(self):
        """Test baseline-aligned line height calculation"""
        engine = BaselineGridEngine(BASELINE_GRIDS_EMU["18pt"])

        # Test 16pt font (203200 EMUs)
        font_size_16pt = 203200
        line_height = engine.calculate_line_height_for_font_size(font_size_16pt, 1.4)

        # 16pt * 1.4 = 22.4pt = 284480 EMUs
        # Should snap to nearest baseline multiple
        expected = engine.snap_to_baseline(284480)
        assert line_height == expected
        assert line_height % engine.baseline_grid_emu == 0  # Must be baseline-aligned

    def test_calculate_spacing_before_after(self):
        """Test before/after spacing calculation maintaining baseline grid"""
        engine = BaselineGridEngine(BASELINE_GRIDS_EMU["18pt"])

        line_height = 457200  # 2x baseline (36pt)
        before, after = engine.calculate_spacing_before_after(line_height, 0.5)

        # Total spacing should be baseline-aligned
        total_spacing = before + after
        assert total_spacing % engine.baseline_grid_emu == 0

        # Should split relatively evenly
        assert abs(before - after) <= engine.baseline_grid_emu

    def test_calculate_indent(self):
        """Test indent calculation with horizontal baseline rhythm"""
        engine = BaselineGridEngine(BASELINE_GRIDS_EMU["18pt"])

        indent = engine.calculate_indent(2.0)

        # Should be baseline-aligned
        assert indent % engine.baseline_grid_emu == 0

        # Should be approximately 2x baseline
        expected_range = (engine.baseline_grid_emu, 3 * engine.baseline_grid_emu)
        assert expected_range[0] <= indent <= expected_range[1]


class TestTypographyToken:
    """Test typography token data structure and W3C DTCG compliance"""

    def test_typography_token_creation(self):
        """Test typography token creation with all properties"""
        token = TypographyToken(
            id="body",
            font_family="Proxima Nova",
            font_size="16pt",
            font_weight=400,
            line_height=1.4,
            letter_spacing="0pt",
            font_size_emu=203200,
            line_height_emu=457200,
            wcag_level="AA"
        )

        assert token.id == "body"
        assert token.font_family == "Proxima Nova"
        assert token.font_size == "16pt"
        assert token.font_weight == 400
        assert token.line_height == 1.4
        assert token.font_size_emu == 203200
        assert token.line_height_emu == 457200
        assert token.wcag_level == "AA"

    def test_to_w3c_dtcg_format(self):
        """Test W3C DTCG format export"""
        token = TypographyToken(
            id="heading",
            font_family="Arial",
            font_size="24pt",
            font_weight="bold",
            line_height=1.3,
            letter_spacing="0.02em",
            font_size_emu=304800,
            line_height_emu=685800,
            wcag_level="AAA",
            min_contrast_ratio=7.0
        )

        dtcg_token = token.to_w3c_dtcg()

        # Validate structure
        assert dtcg_token["$type"] == "typography"
        assert "$value" in dtcg_token
        assert "$description" in dtcg_token

        # Validate values
        value = dtcg_token["$value"]
        assert value["fontFamily"] == "Arial"
        assert value["fontSize"] == "24pt"
        assert value["fontWeight"] == "bold"
        assert value["lineHeight"] == 1.3
        assert value["letterSpacing"] == "0.02em"

        # Validate extensions
        extensions = dtcg_token["$extensions"]["stylestack"]
        assert extensions["emu"]["fontSize"] == 304800
        assert extensions["emu"]["lineHeight"] == 685800
        assert extensions["accessibility"]["wcagLevel"] == "AAA"
        assert extensions["accessibility"]["minContrastRatio"] == 7.0

    def test_font_family_as_list(self):
        """Test font family as list (font stack)"""
        token = TypographyToken(
            id="system",
            font_family=["Proxima Nova", "Arial", "sans-serif"]
        )

        dtcg_token = token.to_w3c_dtcg()
        assert dtcg_token["$value"]["fontFamily"] == ["Proxima Nova", "Arial", "sans-serif"]


class TestTypographyTokenValidator:
    """Test typography token validation for compliance and accessibility"""

    def test_valid_token_validation(self):
        """Test validation of valid typography token"""
        validator = TypographyTokenValidator()

        token = TypographyToken(
            id="valid_body",
            font_size="16pt",
            font_size_emu=203200,
            line_height_emu=457200,  # 2x baseline (aligned)
            baseline_grid_emu=228600,  # 18pt baseline
            wcag_level="AA"
        )

        errors = validator.validate_token(token)
        assert len(errors) == 0

    def test_invalid_token_validation(self):
        """Test validation of invalid typography token"""
        validator = TypographyTokenValidator()

        # Token with multiple validation issues
        token = TypographyToken(
            id="",  # Missing ID
            font_size_emu=-100,  # Negative font size
            line_height_emu=200000,  # Not baseline-aligned
            baseline_grid_emu=228600,
            wcag_level="AA"
        )

        errors = validator.validate_token(token)
        assert len(errors) >= 3  # Should have multiple errors

        # Check specific errors
        error_messages = ' '.join(errors)
        assert "Token ID is required" in error_messages
        assert "Font size EMU must be positive" in error_messages
        assert "not aligned to baseline grid" in error_messages

    def test_wcag_accessibility_validation(self):
        """Test WCAG accessibility compliance validation"""
        validator = TypographyTokenValidator()

        # WCAG AA violation (font too small)
        token_aa_violation = TypographyToken(
            id="small_text",
            font_size_emu=EMUConversionEngine.pt_to_emu(14),  # 14pt < 16pt minimum
            wcag_level="AA"
        )

        errors = validator.validate_token(token_aa_violation)
        assert any("WCAG AA minimum" in error for error in errors)

        # WCAG AAA violation (font too small)
        token_aaa_violation = TypographyToken(
            id="small_text",
            font_size_emu=EMUConversionEngine.pt_to_emu(16),  # 16pt < 18pt minimum
            wcag_level="AAA"
        )

        errors = validator.validate_token(token_aaa_violation)
        assert any("WCAG AAA minimum" in error for error in errors)

    def test_baseline_grid_alignment_validation(self):
        """Test baseline grid alignment validation"""
        validator = TypographyTokenValidator()

        # Misaligned line height
        token = TypographyToken(
            id="misaligned",
            line_height_emu=200000,  # Not a multiple of 228600
            baseline_grid_emu=228600  # 18pt baseline
        )

        errors = validator.validate_token(token)
        assert any("not aligned to baseline grid" in error for error in errors)

        # Aligned line height
        aligned_token = TypographyToken(
            id="aligned",
            line_height_emu=457200,  # 2x baseline (228600 * 2)
            baseline_grid_emu=228600
        )

        errors = validator.validate_token(aligned_token)
        baseline_errors = [e for e in errors if "baseline grid" in e]
        assert len(baseline_errors) == 0

    def test_token_hierarchy_validation(self):
        """Test validation of entire token hierarchy"""
        validator = TypographyTokenValidator()

        tokens = {
            "valid_token": TypographyToken(
                id="valid",
                font_size_emu=203200,
                line_height_emu=457200,
                baseline_grid_emu=228600
            ),
            "invalid_token": TypographyToken(
                id="",  # Missing ID
                font_size_emu=-100  # Invalid size
            )
        }

        results = validator.validate_token_hierarchy(tokens)

        assert "valid_token" not in results  # Valid token should not appear
        assert "invalid_token" in results  # Invalid token should appear
        assert len(results["invalid_token"]) >= 2  # Should have multiple errors


class TestTypographyTokenHierarchyResolver:
    """Test hierarchical typography token resolution with precedence"""

    def test_single_layer_resolution(self):
        """Test resolution with single token layer"""
        resolver = TypographyTokenHierarchyResolver()

        design_tokens = {
            "typography": {
                "body": {
                    "$type": "typography",
                    "$value": {
                        "fontFamily": "Arial",
                        "fontSize": "16pt",
                        "lineHeight": 1.4
                    }
                }
            }
        }

        resolved = resolver.resolve_typography_tokens(design_system_tokens=design_tokens)

        assert "body" in resolved
        assert resolved["body"].font_family == "Arial"
        assert resolved["body"].font_size == "16pt"
        assert resolved["body"].line_height == 1.4
        assert resolved["body"].font_size_emu == EMUConversionEngine.pt_to_emu(16)

    def test_hierarchical_token_resolution(self):
        """Test token resolution with hierarchy precedence"""
        resolver = TypographyTokenHierarchyResolver()

        design_tokens = {
            "typography": {
                "body": {
                    "$type": "typography",
                    "$value": {
                        "fontFamily": "Arial",
                        "fontSize": "16pt"
                    }
                }
            }
        }

        corporate_tokens = {
            "typography": {
                "body": {
                    "$type": "typography",
                    "$value": {
                        "fontFamily": "Proxima Nova",  # Override font family
                        "fontWeight": "400"  # Add new property
                    }
                }
            }
        }

        channel_tokens = {
            "typography": {
                "body": {
                    "$type": "typography",
                    "$value": {
                        "fontSize": "18pt"  # Override font size
                    }
                }
            }
        }

        resolved = resolver.resolve_typography_tokens(
            design_system_tokens=design_tokens,
            corporate_tokens=corporate_tokens,
            channel_tokens=channel_tokens
        )

        # Should have merged properties with correct precedence
        body_token = resolved["body"]
        assert body_token.font_family == "Proxima Nova"  # Corporate override
        assert body_token.font_size == "18pt"  # Channel override
        assert body_token.font_weight == "400"  # Corporate addition
        assert body_token.font_size_emu == EMUConversionEngine.pt_to_emu(18)

    def test_nested_typography_tokens(self):
        """Test resolution of nested typography token structure"""
        resolver = TypographyTokenHierarchyResolver()

        tokens = {
            "typography": {
                "headings": {
                    "h1": {
                        "$type": "typography",
                        "$value": {"fontSize": "32pt"}
                    },
                    "h2": {
                        "$type": "typography",
                        "$value": {"fontSize": "24pt"}
                    }
                },
                "body": {
                    "$type": "typography",
                    "$value": {"fontSize": "16pt"}
                }
            }
        }

        resolved = resolver.resolve_typography_tokens(design_system_tokens=tokens)

        assert "headings.h1" in resolved
        assert "headings.h2" in resolved
        assert "body" in resolved
        assert resolved["headings.h1"].font_size == "32pt"
        assert resolved["headings.h2"].font_size == "24pt"
        assert resolved["body"].font_size == "16pt"


class TestTypographyTokenSystem:
    """Test complete typography token system integration"""

    def test_system_initialization(self):
        """Test typography token system initialization"""
        system = TypographyTokenSystem(baseline_grid_pt=18.0, verbose=False)

        assert system.baseline_grid_emu == EMUConversionEngine.pt_to_emu(18)
        assert isinstance(system.baseline_engine, BaselineGridEngine)
        assert isinstance(system.hierarchy_resolver, TypographyTokenHierarchyResolver)
        assert isinstance(system.validator, TypographyTokenValidator)

    def test_create_typography_token_system(self):
        """Test complete token system creation with validation"""
        system = TypographyTokenSystem(verbose=False)

        corporate_tokens = {
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
                            "accessibility": {"wcagLevel": "AA"}
                        }
                    }
                },
                "heading": {
                    "$type": "typography",
                    "$value": {
                        "fontFamily": "Proxima Nova",
                        "fontSize": "24pt",
                        "fontWeight": "bold"
                    }
                }
            }
        }

        tokens = system.create_typography_token_system(corporate_tokens=corporate_tokens)

        assert len(tokens) == 2
        assert "body" in tokens
        assert "heading" in tokens

        # Validate EMU calculations were performed
        body_token = tokens["body"]
        assert body_token.font_size_emu is not None
        assert body_token.line_height_emu is not None
        assert body_token.baseline_grid_emu is not None

    def test_export_w3c_dtcg_tokens(self):
        """Test W3C DTCG token export"""
        system = TypographyTokenSystem(verbose=False)

        tokens = {
            "body": TypographyToken(
                id="body",
                font_family="Arial",
                font_size="16pt",
                font_size_emu=203200
            ),
            "heading.h1": TypographyToken(
                id="heading.h1",
                font_family="Arial",
                font_size="32pt",
                font_size_emu=406400
            )
        }

        w3c_export = system.export_w3c_dtcg_tokens(tokens)

        assert "typography" in w3c_export
        assert "body" in w3c_export["typography"]
        assert "heading" in w3c_export["typography"]
        assert "h1" in w3c_export["typography"]["heading"]

        # Validate structure
        body_token = w3c_export["typography"]["body"]
        assert body_token["$type"] == "typography"
        assert body_token["$value"]["fontFamily"] == "Arial"
        assert body_token["$value"]["fontSize"] == "16pt"

    def test_generate_ooxml_paragraph_styles(self):
        """Test OOXML paragraph style generation"""
        system = TypographyTokenSystem(verbose=False)

        tokens = {
            "body": TypographyToken(
                id="body",
                font_family="Proxima Nova",
                font_size="16pt",
                font_size_emu=203200,
                line_height_emu=457200,
                letter_spacing_emu=1270,
                font_weight=400
            ),
            "heading": TypographyToken(
                id="heading",
                font_family="Arial",
                font_size="24pt",
                font_size_emu=304800,
                line_height_emu=685800,
                font_weight="bold"
            )
        }

        ooxml_styles = system.generate_ooxml_paragraph_styles(tokens)

        assert "body" in ooxml_styles
        assert "heading" in ooxml_styles

        # Validate OOXML structure for body
        body_style = ooxml_styles["body"]
        assert "w:pPr" in body_style
        assert "w:rPr" in body_style

        # Check spacing (line height)
        assert body_style["w:pPr"]["w:spacing"]["@w:line"] == "457200"
        assert body_style["w:pPr"]["w:spacing"]["@w:lineRule"] == "exact"

        # Check font size (in half-points)
        expected_sz = str(16 * 2)  # 16pt = 32 half-points
        assert body_style["w:rPr"]["w:sz"]["@w:val"] == expected_sz

        # Check font family
        assert body_style["w:rPr"]["w:rFonts"]["@w:ascii"] == "Proxima Nova"

        # Check letter spacing
        assert body_style["w:rPr"]["w:spacing"]["@w:val"] == "1270"

        # Validate bold heading
        heading_style = ooxml_styles["heading"]
        assert "w:b" in heading_style["w:rPr"]  # Bold formatting


# Integration test fixtures
@pytest.fixture
def sample_design_system_tokens():
    """Sample design system tokens for testing"""
    return {
        "typography": {
            "scales": {
                "minor_third": {"$value": 1.2},
                "major_third": {"$value": 1.25}
            },
            "baseline": {"$value": "18pt"},
            "body": {
                "$type": "typography",
                "$value": {
                    "fontFamily": "System",
                    "fontSize": "16pt",
                    "lineHeight": 1.4,
                    "letterSpacing": "0em"
                },
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
                    }
                },
                "h2": {
                    "$type": "typography",
                    "$value": {
                        "fontSize": "24pt",
                        "fontWeight": "semibold",
                        "lineHeight": 1.3
                    }
                }
            }
        }
    }


@pytest.fixture
def sample_corporate_tokens():
    """Sample corporate brand tokens for testing"""
    return {
        "typography": {
            "body": {
                "$type": "typography",
                "$value": {
                    "fontFamily": "Proxima Nova"  # Brand font override
                }
            },
            "headings": {
                "h1": {
                    "$type": "typography",
                    "$value": {
                        "fontFamily": "Proxima Nova",
                        "letterSpacing": "0.02em"  # Brand spacing
                    }
                }
            }
        }
    }


class TestTokenSystemIntegration:
    """Integration tests for complete typography token system"""

    def test_full_system_integration(self, sample_design_system_tokens, sample_corporate_tokens):
        """Test complete system with design system and corporate overrides"""
        system = TypographyTokenSystem(baseline_grid_pt=18.0, verbose=False)

        tokens = system.create_typography_token_system(
            design_system_tokens=sample_design_system_tokens,
            corporate_tokens=sample_corporate_tokens
        )

        # Verify hierarchy resolution worked
        assert "body" in tokens
        assert "headings.h1" in tokens
        assert "headings.h2" in tokens

        # Verify corporate overrides were applied
        body_token = tokens["body"]
        assert body_token.font_family == "Proxima Nova"  # Corporate override
        assert body_token.font_size == "16pt"  # From design system
        assert body_token.wcag_level == "AA"  # From design system

        h1_token = tokens["headings.h1"]
        assert h1_token.font_family == "Proxima Nova"  # Corporate override
        assert h1_token.letter_spacing == "0.02em"  # Corporate addition
        assert h1_token.font_size == "32pt"  # From design system

        # Verify EMU calculations
        assert all(token.font_size_emu is not None for token in tokens.values())
        assert all(token.baseline_grid_emu == system.baseline_grid_emu for token in tokens.values())

    def test_w3c_dtcg_roundtrip(self, sample_design_system_tokens):
        """Test W3C DTCG export and import roundtrip"""
        system = TypographyTokenSystem(verbose=False)

        # Create tokens
        original_tokens = system.create_typography_token_system(
            design_system_tokens=sample_design_system_tokens
        )

        # Export to W3C DTCG
        w3c_export = system.export_w3c_dtcg_tokens(original_tokens)

        # Re-import (simulate)
        reimported_tokens = system.create_typography_token_system(
            design_system_tokens=w3c_export
        )

        # Verify key properties maintained
        for token_id in original_tokens.keys():
            if token_id in reimported_tokens:
                original = original_tokens[token_id]
                reimported = reimported_tokens[token_id]

                assert original.font_family == reimported.font_family
                assert original.font_size == reimported.font_size
                assert original.font_weight == reimported.font_weight

    def test_ooxml_generation_integration(self, sample_design_system_tokens):
        """Test OOXML paragraph style generation integration"""
        system = TypographyTokenSystem(verbose=False)

        tokens = system.create_typography_token_system(
            design_system_tokens=sample_design_system_tokens
        )

        # Generate OOXML styles
        ooxml_styles = system.generate_ooxml_paragraph_styles(tokens)

        # Verify all tokens with font sizes generated styles
        tokens_with_sizes = {k: v for k, v in tokens.items() if v.font_size_emu}
        assert len(ooxml_styles) == len(tokens_with_sizes)

        # Verify baseline alignment in generated styles
        baseline_engine = BaselineGridEngine(system.baseline_grid_emu)
        for style_id, style in ooxml_styles.items():
            line_height_emu = int(style["w:pPr"]["w:spacing"]["@w:line"])
            assert line_height_emu % system.baseline_grid_emu == 0  # Must be baseline-aligned