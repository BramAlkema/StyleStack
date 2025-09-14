"""
Test Enhanced Typography Token System Integration with Style Inheritance

Tests the integration between the core inheritance infrastructure and the existing
typography token system, ensuring seamless interoperability while maintaining
W3C DTCG compliance and EMU precision.

Key Integration Points:
- TypographyToken <-> InheritedTypographyToken compatibility
- Hierarchical token resolution with inheritance
- EMU precision maintenance through inheritance chains
- W3C DTCG export with inheritance metadata extensions
- OOXML generation with basedOn references and delta properties
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any, List

from tools.typography_token_system import (
    TypographyToken, TypographyTokenSystem, TypographyTokenHierarchyResolver,
    EMUConversionEngine, BaselineGridEngine
)
from tools.style_inheritance_core import (
    InheritedTypographyToken, InheritanceResolver, BaseStyleRegistry,
    DeltaStyleGenerator, InheritanceMode, create_inheritance_system,
    create_inherited_token_from_config
)


class TestEnhancedTypographyTokenIntegration:
    """Test integration between typography tokens and style inheritance"""

    def setup_method(self):
        """Set up test infrastructure"""
        self.typography_system = TypographyTokenSystem(verbose=False)
        self.inheritance_registry, self.delta_generator, self.inheritance_resolver = create_inheritance_system()

    def test_typography_token_to_inherited_conversion(self):
        """Test converting TypographyToken to InheritedTypographyToken"""
        # Create standard typography token
        typography_token = TypographyToken(
            id="body_text",
            font_family="Proxima Nova",
            font_size="16pt",
            font_weight=400,
            line_height=1.4,
            letter_spacing="0pt"
        )

        # Convert to inherited token with inheritance configuration
        inheritance_config = {
            "baseStyle": "Normal",
            "mode": "auto",
            "deltaProperties": {"fontFamily": "Proxima Nova", "fontSize": "16pt"}
        }

        inherited_token = InheritedTypographyToken(
            id=typography_token.id,
            font_family=typography_token.font_family,
            font_size=typography_token.font_size,
            font_weight=typography_token.font_weight,
            line_height=typography_token.line_height,
            letter_spacing=typography_token.letter_spacing,
            base_style="Normal",
            inheritance_mode=InheritanceMode.AUTO,
            delta_properties=inheritance_config["deltaProperties"]
        )

        # Verify conversion maintains all properties
        assert inherited_token.id == typography_token.id
        assert inherited_token.font_family == typography_token.font_family
        assert inherited_token.font_size == typography_token.font_size
        assert inherited_token.font_weight == typography_token.font_weight
        assert inherited_token.should_generate_delta() is True
        assert inherited_token.base_style == "Normal"

    def test_hierarchical_resolution_with_inheritance(self):
        """Test hierarchical token resolution with inheritance relationships"""
        # Design system tokens with inheritance specifications
        design_system_tokens = {
            "typography": {
                "base": {
                    "$type": "typography",
                    "$value": {
                        "fontFamily": "Calibri",
                        "fontSize": "12pt",
                        "fontWeight": 400,
                        "lineHeight": 1.2
                    },
                    "$extensions": {
                        "stylestack": {
                            "inheritance": {
                                "baseStyle": "Normal",
                                "mode": "auto"
                            }
                        }
                    }
                }
            }
        }

        # Corporate tokens that override design system
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
                            "inheritance": {
                                "baseStyle": "base",
                                "mode": "auto"
                            }
                        }
                    }
                },
                "heading": {
                    "$type": "typography",
                    "$value": {
                        "fontWeight": 600,
                        "fontSize": "24pt"
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

        # Resolve through hierarchy
        resolved_tokens = self.typography_system.hierarchy_resolver.resolve_typography_tokens(
            design_system_tokens=design_system_tokens,
            corporate_tokens=corporate_tokens
        )

        assert "base" in resolved_tokens
        assert "body" in resolved_tokens
        assert "heading" in resolved_tokens

        # Verify hierarchy merging worked correctly
        body_token = resolved_tokens["body"]
        assert body_token.font_family == "Proxima Nova"  # Corporate override
        assert body_token.font_size == "16pt"  # Corporate value
        assert body_token.line_height == 1.4  # Corporate value

        heading_token = resolved_tokens["heading"]
        assert heading_token.font_family == "Proxima Nova"  # Inherited from body
        assert heading_token.font_size == "24pt"  # Override value
        assert heading_token.font_weight == 600  # Override value

    def test_emu_precision_with_inheritance(self):
        """Test EMU precision maintenance through inheritance chains"""
        # Create token hierarchy with EMU values
        base_token_config = {
            "fontFamily": "Calibri",
            "fontSize": "18pt",  # 228600 EMUs
            "lineHeight": 1.2,
            "inheritance": {
                "baseStyle": "Normal",
                "mode": "auto"
            }
        }

        derived_token_config = {
            "fontSize": "20pt",  # 254000 EMUs - should be precise
            "fontWeight": 600,
            "inheritance": {
                "baseStyle": "base",
                "mode": "auto"
            }
        }

        # Create tokens
        base_token = create_inherited_token_from_config("base", base_token_config)
        derived_token = create_inherited_token_from_config("derived", derived_token_config)

        # Calculate EMU values
        self.typography_system.hierarchy_resolver._calculate_emu_values(base_token)
        self.typography_system.hierarchy_resolver._calculate_emu_values(derived_token)

        # Verify EMU precision
        assert base_token.font_size_emu == 18 * 12700  # 228600 EMUs
        assert derived_token.font_size_emu == 20 * 12700  # 254000 EMUs

        # Verify line height calculation respects baseline grid
        assert base_token.line_height_emu % 228600 == 0  # Snapped to 18pt baseline

    def test_w3c_dtcg_export_with_inheritance_metadata(self):
        """Test W3C DTCG export preserves inheritance metadata"""
        token_config = {
            "fontFamily": "Proxima Nova",
            "fontSize": "16pt",
            "fontWeight": 600,
            "inheritance": {
                "baseStyle": "Normal",
                "mode": "auto"
            }
        }

        # Create inherited token
        inherited_token = create_inherited_token_from_config("enhanced_body", token_config)

        # Resolve inheritance
        resolved_token = self.inheritance_resolver.resolve_inheritance(inherited_token, {})

        # Export to W3C DTCG with inheritance metadata
        w3c_export = self._export_w3c_dtcg_with_inheritance(resolved_token)

        # Verify standard W3C DTCG structure
        assert w3c_export["$type"] == "typography"
        assert "$value" in w3c_export
        assert w3c_export["$value"]["fontFamily"] == "Proxima Nova"
        assert w3c_export["$value"]["fontSize"] == "16pt"
        assert w3c_export["$value"]["fontWeight"] == 600

        # Verify StyleStack inheritance extensions
        assert "$extensions" in w3c_export
        assert "stylestack" in w3c_export["$extensions"]
        assert "inheritance" in w3c_export["$extensions"]["stylestack"]

        inheritance_data = w3c_export["$extensions"]["stylestack"]["inheritance"]
        assert inheritance_data["baseStyle"] == "Normal"
        assert inheritance_data["mode"] == "auto"
        assert inheritance_data["shouldGenerateDelta"] is True

    def test_ooxml_generation_with_inheritance_and_emu(self):
        """Test OOXML generation with inheritance and EMU precision"""
        # Create inheritance hierarchy
        base_config = {
            "fontFamily": "Calibri",
            "fontSize": "12pt",
            "inheritance": {"baseStyle": "Normal", "mode": "auto"}
        }

        emphasis_config = {
            "fontWeight": 600,
            "inheritance": {"baseStyle": "base", "mode": "auto"}
        }

        base_token = create_inherited_token_from_config("base", base_config)
        emphasis_token = create_inherited_token_from_config("emphasis", emphasis_config)

        # Calculate EMU values
        self.typography_system.hierarchy_resolver._calculate_emu_values(base_token)
        self.typography_system.hierarchy_resolver._calculate_emu_values(emphasis_token)

        # Resolve inheritance - include base token in hierarchy
        resolved_base = self.inheritance_resolver.resolve_inheritance(base_token, {})
        token_hierarchy = {"base": resolved_base}
        resolved_emphasis = self.inheritance_resolver.resolve_inheritance(emphasis_token, token_hierarchy)

        # Generate OOXML with inheritance awareness
        ooxml_style = self._generate_inheritance_aware_ooxml(resolved_emphasis)

        # Verify basedOn reference
        assert "w:basedOn" in ooxml_style["w:style"]
        assert ooxml_style["w:style"]["w:basedOn"]["@w:val"] == "base"

        # Verify only delta properties are included
        rpr = ooxml_style["w:style"]["w:rPr"]
        assert "w:b" in rpr  # Bold for fontWeight 600
        assert "w:rFonts" not in rpr  # Inherited from base
        assert "w:sz" not in rpr  # Inherited from base

    def test_cross_format_compatibility_with_inheritance(self):
        """Test inheritance works across PowerPoint, Word, and Excel formats"""
        token_configs = {
            "slide_title": {
                "fontFamily": "Proxima Nova",
                "fontSize": "32pt",
                "fontWeight": 700,
                "inheritance": {"baseStyle": "Title", "mode": "auto"}
            },
            "slide_body": {
                "fontFamily": "Proxima Nova",
                "fontSize": "18pt",
                "inheritance": {"baseStyle": "Normal", "mode": "auto"}
            },
            "document_heading": {
                "fontFamily": "Proxima Nova",
                "fontSize": "24pt",
                "fontWeight": 600,
                "inheritance": {"baseStyle": "Heading1", "mode": "auto"}
            }
        }

        # Create and resolve tokens
        resolved_tokens = {}
        for token_id, config in token_configs.items():
            token = create_inherited_token_from_config(token_id, config)
            self.typography_system.hierarchy_resolver._calculate_emu_values(token)
            resolved_token = self.inheritance_resolver.resolve_inheritance(token, {})
            resolved_tokens[token_id] = resolved_token

        # Verify all tokens resolved successfully
        assert len(resolved_tokens) == 3

        # Test PowerPoint-specific properties
        slide_title = resolved_tokens["slide_title"]
        assert slide_title.base_style == "Title"
        assert slide_title.should_generate_delta() is True

        # Test Word-specific properties
        document_heading = resolved_tokens["document_heading"]
        assert document_heading.base_style == "Heading1"
        assert document_heading.font_size == "24pt"

        # Generate OOXML for each format
        powerpoint_ooxml = self._generate_inheritance_aware_ooxml(slide_title)
        word_ooxml = self._generate_inheritance_aware_ooxml(document_heading)

        # Verify format-specific OOXML structure
        assert powerpoint_ooxml["w:style"]["w:basedOn"]["@w:val"] == "Title"
        assert word_ooxml["w:style"]["w:basedOn"]["@w:val"] == "Heading1"

    def test_error_handling_with_inheritance_and_typography(self):
        """Test error handling when combining inheritance with typography system"""
        # Test invalid inheritance configuration
        invalid_config = {
            "fontFamily": "Proxima Nova",
            "inheritance": {
                "baseStyle": "NonExistentStyle",
                "mode": "auto"
            }
        }

        invalid_token = create_inherited_token_from_config("invalid", invalid_config)

        # Should handle gracefully - fallback to complete mode
        resolved_token = self.inheritance_resolver.resolve_inheritance(invalid_token, {})
        assert resolved_token.inheritance_mode == InheritanceMode.COMPLETE

        # Test circular dependency
        token_a_config = {
            "inheritance": {"baseStyle": "token_b", "mode": "auto"}
        }
        token_b_config = {
            "inheritance": {"baseStyle": "token_a", "mode": "auto"}
        }

        token_a = create_inherited_token_from_config("token_a", token_a_config)
        token_b = create_inherited_token_from_config("token_b", token_b_config)

        hierarchy = {"token_a": token_a, "token_b": token_b}

        # Should detect and handle circular dependency
        resolved_a = self.inheritance_resolver.resolve_inheritance(token_a, hierarchy)
        assert resolved_a.inheritance_mode == InheritanceMode.COMPLETE

    def test_performance_optimization_with_inheritance(self):
        """Test performance optimizations in inheritance + typography integration"""
        # Create large hierarchy
        token_configs = {}
        for i in range(20):
            base_style = f"token_{i-1}" if i > 0 else "Normal"
            token_configs[f"token_{i}"] = {
                "fontFamily": f"Font{i}",
                "fontSize": f"{12 + i}pt",
                "inheritance": {"baseStyle": base_style, "mode": "auto"}
            }

        # Create and resolve all tokens
        resolved_tokens = {}
        for token_id, config in token_configs.items():
            token = create_inherited_token_from_config(token_id, config)
            resolved_tokens[token_id] = token

        # Resolve inheritance for entire hierarchy
        for token_id, token in resolved_tokens.items():
            resolved_token = self.inheritance_resolver.resolve_inheritance(token, resolved_tokens)
            resolved_tokens[token_id] = resolved_token

        # Verify cache effectiveness
        cache_stats = self.inheritance_resolver.get_cache_stats()
        assert cache_stats["cache_size"] > 0
        assert cache_stats["max_inheritance_depth"] == 20

        # Verify all tokens resolved
        assert all(token.inheritance_chain for token in resolved_tokens.values())

    def _export_w3c_dtcg_with_inheritance(self, token: InheritedTypographyToken) -> Dict[str, Any]:
        """Export token to W3C DTCG format with inheritance metadata"""
        dtcg_token = {
            "$type": "typography",
            "$value": {},
            "$description": f"Inherited typography token: {token.id}"
        }

        # Add effective properties (considering inheritance)
        properties = ["fontFamily", "fontSize", "fontWeight", "lineHeight", "letterSpacing"]
        for prop in properties:
            value = token.get_effective_property(prop.replace('font_', '').replace('_', ''))
            if value:
                dtcg_token["$value"][prop] = value

        # Add StyleStack inheritance extensions
        dtcg_token["$extensions"] = {
            "stylestack": {
                "inheritance": {
                    "baseStyle": token.base_style,
                    "mode": token.inheritance_mode.value,
                    "shouldGenerateDelta": token.should_generate_delta(),
                    "inheritanceChain": token.inheritance_chain,
                    "inheritanceDepth": token.inheritance_depth
                }
            }
        }

        if token.delta_properties:
            dtcg_token["$extensions"]["stylestack"]["inheritance"]["deltaProperties"] = token.delta_properties

        return dtcg_token

    def _generate_inheritance_aware_ooxml(self, token: InheritedTypographyToken) -> Dict[str, Any]:
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
                if "fontFamily" in token.delta_properties:
                    rpr["w:rFonts"] = {"@w:ascii": token.delta_properties["fontFamily"]}
                if "fontWeight" in token.delta_properties and token.delta_properties["fontWeight"] >= 600:
                    rpr["w:b"] = {}
                if "fontSize" in token.delta_properties:
                    # Convert to half-points for OOXML
                    font_size = token.delta_properties["fontSize"]
                    if isinstance(font_size, str) and font_size.endswith('pt'):
                        pt_value = float(font_size[:-2])
                        rpr["w:sz"] = {"@w:val": str(int(pt_value * 2))}

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
                        "w:rFonts": {"@w:ascii": token.font_family or "Calibri"},
                        "w:sz": {"@w:val": "22"}  # Default 11pt = 22 half-points
                    }
                }
            }


class TestInheritanceIntegrationWithTypographySystem:
    """Test integration of inheritance system with existing typography system components"""

    def setup_method(self):
        """Set up test environment"""
        self.typography_system = TypographyTokenSystem(verbose=False)
        self.inheritance_registry, self.delta_generator, self.inheritance_resolver = create_inheritance_system()

    def test_baseline_grid_inheritance(self):
        """Test baseline grid calculations work through inheritance"""
        # Create base token with specific baseline grid
        base_config = {
            "fontSize": "18pt",
            "lineHeight": 1.4,
            "inheritance": {"baseStyle": "Normal", "mode": "auto"}
        }

        derived_config = {
            "fontSize": "24pt",
            "inheritance": {"baseStyle": "base", "mode": "auto"}
        }

        base_token = create_inherited_token_from_config("base", base_config)
        derived_token = create_inherited_token_from_config("derived", derived_config)

        # Calculate EMU values with baseline grid
        baseline_engine = BaselineGridEngine(18 * 12700)  # 18pt grid
        self.typography_system.hierarchy_resolver.baseline_engine = baseline_engine

        self.typography_system.hierarchy_resolver._calculate_emu_values(base_token)
        self.typography_system.hierarchy_resolver._calculate_emu_values(derived_token)

        # Verify baseline grid alignment
        assert base_token.line_height_emu % (18 * 12700) == 0
        assert derived_token.line_height_emu % (18 * 12700) == 0

    def test_accessibility_compliance_through_inheritance(self):
        """Test WCAG compliance maintained through inheritance chains"""
        # Base accessible token
        accessible_config = {
            "fontSize": "18pt",  # WCAG AAA compliant
            "fontWeight": 400,
            "inheritance": {"baseStyle": "Normal", "mode": "auto"}
        }

        # Derived token that should maintain accessibility
        emphasis_config = {
            "fontWeight": 600,
            "inheritance": {"baseStyle": "accessible_base", "mode": "auto"}
        }

        accessible_base = create_inherited_token_from_config("accessible_base", accessible_config)
        emphasis_token = create_inherited_token_from_config("emphasis", emphasis_config)

        # Set WCAG level
        accessible_base.wcag_level = "AAA"

        # Resolve inheritance
        token_hierarchy = {"accessible_base": accessible_base}
        resolved_emphasis = self.inheritance_resolver.resolve_inheritance(emphasis_token, token_hierarchy)

        # Verify accessibility properties inherited
        effective_font_size = resolved_emphasis.get_effective_property("size")
        assert effective_font_size == "18pt"  # Should inherit WCAG-compliant size

        # Validate with typography system validator
        validator = self.typography_system.validator

        # Convert to TypographyToken for validation
        typography_token = TypographyToken(
            id=resolved_emphasis.id,
            font_size=resolved_emphasis.get_effective_property("size"),
            font_weight=resolved_emphasis.get_effective_property("weight"),
            wcag_level="AAA"
        )

        # Calculate EMU for validation
        self.typography_system.hierarchy_resolver._calculate_emu_values(typography_token)

        validation_errors = validator.validate_token(typography_token)
        assert len(validation_errors) == 0  # Should pass all validations

    def test_variable_resolver_integration(self):
        """Test integration with StyleStack variable resolver"""
        from tools.variable_resolver import ResolvedVariable
        from tools.token_parser import TokenType, TokenScope

        # Create inherited token that can be resolved as variable
        token_config = {
            "fontFamily": "Proxima Nova",
            "fontSize": "16pt",
            "fontWeight": 600,
            "inheritance": {"baseStyle": "Normal", "mode": "auto"}
        }

        inherited_token = create_inherited_token_from_config("body_emphasis", token_config)
        resolved_token = self.inheritance_resolver.resolve_inheritance(inherited_token, {})

        # Convert to ResolvedVariable format
        resolved_variable = ResolvedVariable(
            id="body_emphasis",
            value=resolved_token.get_effective_property("family") or "Calibri",
            type=TokenType.TEXT,
            scope=TokenScope.CORE,
            source="corporate",
            hierarchy_level=2,
            dependencies=[resolved_token.base_style] if resolved_token.base_style else []
        )

        # Verify variable resolver compatibility
        assert resolved_variable.id == "body_emphasis"
        assert resolved_variable.value in ["Proxima Nova", "Calibri"]
        assert resolved_token.base_style == "Normal"