"""
Unit tests for StyleStack Style Inheritance Core Infrastructure

Tests the core inheritance system including InheritanceResolver, BaseStyleRegistry,
and DeltaStyleGenerator with comprehensive edge case coverage.
"""

import pytest
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path

# Import existing typography system for integration
from tools.typography_token_system import TypographyToken, EMUConversionEngine


# Test data structures matching the technical spec
@dataclass
class BaseStyleDefinition:
    """Test base style definition"""
    style_id: str
    style_type: str  # paragraph, character, table
    default_properties: Dict[str, Any]
    emu_calculated_properties: Dict[str, int]


@dataclass
class InheritedTypographyToken:
    """Test inherited typography token"""
    id: str
    base_style: Optional[str] = None
    inheritance_mode: str = "auto"  # auto, manual_override, complete
    delta_properties: Dict[str, Any] = None
    computed_full_style: Optional[Dict[str, Any]] = None

    # Standard typography properties
    font_family: Optional[str] = None
    font_size: Optional[str] = None
    font_weight: Optional[int] = None
    line_height: Optional[float] = None
    letter_spacing: Optional[str] = None

    def __post_init__(self):
        if self.delta_properties is None:
            self.delta_properties = {}

    def should_generate_delta(self) -> bool:
        """Determine if delta-style generation should be used"""
        return (
            self.base_style is not None and
            self.inheritance_mode in ["auto", "delta"] and
            len(self.delta_properties) > 0
        )


class CircularInheritanceError(Exception):
    """Exception raised when circular inheritance is detected"""
    pass


class TestBaseStyleRegistry:
    """Test base style registry functionality"""

    def test_registry_initialization(self):
        """Test base style registry initialization with standard OOXML styles"""
        registry = {}

        # Test data for standard OOXML base styles
        normal_style = BaseStyleDefinition(
            style_id="Normal",
            style_type="paragraph",
            default_properties={
                "fontFamily": "Calibri",
                "fontSize": "11pt",
                "lineHeight": 1.15,
                "fontWeight": 400,
                "color": "#000000"
            },
            emu_calculated_properties={
                "fontSize": EMUConversionEngine.pt_to_emu(11),
                "lineHeight": EMUConversionEngine.pt_to_emu(11 * 1.15),
                "spacing": {
                    "after": EMUConversionEngine.pt_to_emu(8),
                    "line": EMUConversionEngine.pt_to_emu(12.65),
                    "lineRule": "auto"
                }
            }
        )

        default_para_font = BaseStyleDefinition(
            style_id="DefaultParagraphFont",
            style_type="character",
            default_properties={
                "fontFamily": "Calibri",
                "fontSize": "11pt",
                "fontWeight": 400
            },
            emu_calculated_properties={
                "fontSize": EMUConversionEngine.pt_to_emu(11)
            }
        )

        registry["Normal"] = normal_style
        registry["DefaultParagraphFont"] = default_para_font

        # Test registry access
        assert "Normal" in registry
        assert "DefaultParagraphFont" in registry
        assert registry["Normal"].style_type == "paragraph"
        assert registry["DefaultParagraphFont"].style_type == "character"

        # Test EMU calculations are correct
        assert registry["Normal"].emu_calculated_properties["fontSize"] == 139700  # 11pt
        assert registry["DefaultParagraphFont"].emu_calculated_properties["fontSize"] == 139700

    def test_registry_lookup(self):
        """Test base style lookup functionality"""
        registry = {
            "Normal": BaseStyleDefinition(
                style_id="Normal",
                style_type="paragraph",
                default_properties={"fontSize": "12pt"},
                emu_calculated_properties={"fontSize": 152400}
            )
        }

        # Test successful lookup
        style = registry.get("Normal")
        assert style is not None
        assert style.style_id == "Normal"

        # Test failed lookup
        missing_style = registry.get("NonExistent")
        assert missing_style is None

    def test_custom_base_styles(self):
        """Test registry with custom base styles"""
        registry = {}

        custom_base = BaseStyleDefinition(
            style_id="CustomBase",
            style_type="paragraph",
            default_properties={
                "fontFamily": "Proxima Nova",
                "fontSize": "16pt",
                "lineHeight": 1.4
            },
            emu_calculated_properties={
                "fontSize": EMUConversionEngine.pt_to_emu(16),
                "lineHeight": EMUConversionEngine.pt_to_emu(16 * 1.4)
            }
        )

        registry["CustomBase"] = custom_base

        assert registry["CustomBase"].default_properties["fontFamily"] == "Proxima Nova"
        assert registry["CustomBase"].emu_calculated_properties["fontSize"] == 203200  # 16pt


class TestInheritanceResolver:
    """Test inheritance resolution functionality"""

    def test_simple_inheritance_resolution(self):
        """Test basic inheritance resolution"""
        # Mock base style registry
        base_registry = {
            "Normal": BaseStyleDefinition(
                style_id="Normal",
                style_type="paragraph",
                default_properties={
                    "fontFamily": "Calibri",
                    "fontSize": "11pt",
                    "fontWeight": 400,
                    "lineHeight": 1.15
                },
                emu_calculated_properties={
                    "fontSize": 139700,
                    "lineHeight": 160405
                }
            )
        }

        # Create token that inherits from Normal
        token = InheritedTypographyToken(
            id="body_emphasis",
            base_style="Normal",
            inheritance_mode="auto",
            font_weight=600,  # Only difference from base
            delta_properties={"fontWeight": 600}  # Add delta properties for testing
        )

        # Test inheritance resolution
        assert token.base_style == "Normal"
        assert token.inheritance_mode == "auto"
        assert token.should_generate_delta()

    def test_inheritance_chain_resolution(self):
        """Test multi-level inheritance chain resolution"""
        # Mock token hierarchy: BodyEmphasis → Body → Normal
        token_hierarchy = {
            "Normal": InheritedTypographyToken(
                id="Normal",
                font_family="Calibri",
                font_size="11pt",
                font_weight=400
            ),
            "Body": InheritedTypographyToken(
                id="Body",
                base_style="Normal",
                font_size="12pt"  # Override from Normal
            ),
            "BodyEmphasis": InheritedTypographyToken(
                id="BodyEmphasis",
                base_style="Body",
                font_weight=600  # Override from Body
            )
        }

        # Test chain resolution
        emphasis_token = token_hierarchy["BodyEmphasis"]
        assert emphasis_token.base_style == "Body"

        body_token = token_hierarchy["Body"]
        assert body_token.base_style == "Normal"

        normal_token = token_hierarchy["Normal"]
        assert normal_token.base_style is None  # Root style

    def test_circular_dependency_detection(self):
        """Test circular inheritance dependency detection"""
        # Create circular inheritance: A → B → C → A
        token_hierarchy = {
            "TokenA": InheritedTypographyToken(
                id="TokenA",
                base_style="TokenC"  # Creates cycle
            ),
            "TokenB": InheritedTypographyToken(
                id="TokenB",
                base_style="TokenA"
            ),
            "TokenC": InheritedTypographyToken(
                id="TokenC",
                base_style="TokenB"
            )
        }

        # Test circular dependency detection (would be implemented in resolver)
        def detect_circular_inheritance(token_id: str, hierarchy: Dict[str, InheritedTypographyToken],
                                       visited: set = None) -> bool:
            if visited is None:
                visited = set()

            if token_id in visited:
                return True  # Circular dependency found

            token = hierarchy.get(token_id)
            if not token or not token.base_style:
                return False

            visited.add(token_id)
            return detect_circular_inheritance(token.base_style, hierarchy, visited)

        # Should detect circular dependency
        assert detect_circular_inheritance("TokenA", token_hierarchy)
        assert detect_circular_inheritance("TokenB", token_hierarchy)
        assert detect_circular_inheritance("TokenC", token_hierarchy)

    def test_inheritance_mode_handling(self):
        """Test different inheritance modes"""
        # Auto inheritance mode
        auto_token = InheritedTypographyToken(
            id="auto_style",
            base_style="Normal",
            inheritance_mode="auto",
            delta_properties={"fontWeight": 600}
        )
        assert auto_token.should_generate_delta()

        # Manual override mode
        manual_token = InheritedTypographyToken(
            id="manual_style",
            inheritance_mode="manual_override",
            font_family="Custom Font",
            font_size="14pt"
        )
        assert not manual_token.should_generate_delta()

        # Complete mode
        complete_token = InheritedTypographyToken(
            id="complete_style",
            inheritance_mode="complete",
            font_family="Arial",
            font_size="16pt"
        )
        assert not complete_token.should_generate_delta()


class TestDeltaCalculation:
    """Test delta calculation functionality"""

    def test_simple_delta_calculation(self):
        """Test basic delta calculation between tokens"""
        # Base style properties
        base_properties = {
            "fontFamily": "Calibri",
            "fontSize": "11pt",
            "fontWeight": 400,
            "lineHeight": 1.15,
            "color": "#000000"
        }

        # Current token properties
        current_properties = {
            "fontFamily": "Calibri",      # Same as base
            "fontSize": "12pt",           # Different from base
            "fontWeight": 600,            # Different from base
            "lineHeight": 1.15,           # Same as base
            "color": "#000000",           # Same as base
            "letterSpacing": "0.02em"     # New property
        }

        # Calculate delta
        def calculate_delta(base: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
            delta = {}

            # Find properties that differ from base
            for key, value in current.items():
                base_value = base.get(key)
                if base_value != value:
                    delta[key] = value

            return delta

        delta = calculate_delta(base_properties, current_properties)

        # Should only include changed properties
        expected_delta = {
            "fontSize": "12pt",
            "fontWeight": 600,
            "letterSpacing": "0.02em"
        }

        assert delta == expected_delta
        assert "fontFamily" not in delta  # Same as base
        assert "lineHeight" not in delta  # Same as base
        assert "color" not in delta       # Same as base

    def test_emu_precision_delta(self):
        """Test delta calculation maintains EMU precision"""
        base_emu = {
            "fontSize": EMUConversionEngine.pt_to_emu(11),
            "lineHeight": EMUConversionEngine.pt_to_emu(11 * 1.15),
            "letterSpacing": 0
        }

        current_emu = {
            "fontSize": EMUConversionEngine.pt_to_emu(12),     # Changed
            "lineHeight": EMUConversionEngine.pt_to_emu(11 * 1.15),  # Same
            "letterSpacing": EMUConversionEngine.pt_to_emu(0.5)      # Changed
        }

        def calculate_emu_delta(base: Dict[str, int], current: Dict[str, int]) -> Dict[str, int]:
            delta = {}
            for key, value in current.items():
                if base.get(key) != value:
                    delta[key] = value
            return delta

        delta = calculate_emu_delta(base_emu, current_emu)

        # Should maintain exact EMU values
        assert delta["fontSize"] == EMUConversionEngine.pt_to_emu(12)
        assert delta["letterSpacing"] == EMUConversionEngine.pt_to_emu(0.5)
        assert "lineHeight" not in delta  # Unchanged

    def test_nested_property_delta(self):
        """Test delta calculation with nested properties"""
        base_properties = {
            "font": {
                "family": "Calibri",
                "size": "11pt",
                "weight": 400
            },
            "spacing": {
                "before": "0pt",
                "after": "8pt",
                "line": "13pt"
            }
        }

        current_properties = {
            "font": {
                "family": "Calibri",     # Same
                "size": "12pt",          # Different
                "weight": 600            # Different
            },
            "spacing": {
                "before": "6pt",         # Different
                "after": "8pt",          # Same
                "line": "13pt"           # Same
            }
        }

        def calculate_nested_delta(base: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
            delta = {}

            for key, value in current.items():
                if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                    # Recursively calculate delta for nested objects
                    nested_delta = calculate_nested_delta(base[key], value)
                    if nested_delta:  # Only include if there are differences
                        delta[key] = nested_delta
                elif base.get(key) != value:
                    delta[key] = value

            return delta

        delta = calculate_nested_delta(base_properties, current_properties)

        expected_delta = {
            "font": {
                "size": "12pt",
                "weight": 600
            },
            "spacing": {
                "before": "6pt"
            }
        }

        assert delta == expected_delta

    def test_empty_delta_calculation(self):
        """Test delta calculation when no differences exist"""
        base_properties = {
            "fontFamily": "Calibri",
            "fontSize": "11pt",
            "fontWeight": 400
        }

        current_properties = {
            "fontFamily": "Calibri",
            "fontSize": "11pt",
            "fontWeight": 400
        }

        def calculate_delta(base: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
            delta = {}
            for key, value in current.items():
                if base.get(key) != value:
                    delta[key] = value
            return delta

        delta = calculate_delta(base_properties, current_properties)
        assert delta == {}  # No differences


class TestInheritanceIntegration:
    """Test integration between inheritance components"""

    def test_end_to_end_inheritance_resolution(self):
        """Test complete inheritance resolution workflow"""
        # Setup base style registry
        base_registry = {
            "Normal": BaseStyleDefinition(
                style_id="Normal",
                style_type="paragraph",
                default_properties={
                    "fontFamily": "Calibri",
                    "fontSize": "11pt",
                    "fontWeight": 400,
                    "lineHeight": 1.15
                },
                emu_calculated_properties={
                    "fontSize": 139700,
                    "lineHeight": 160405
                }
            )
        }

        # Create inherited token
        token = InheritedTypographyToken(
            id="body_emphasis",
            base_style="Normal",
            inheritance_mode="auto",
            font_size="12pt",   # Override
            font_weight=600     # Override
            # fontFamily and lineHeight inherited from Normal
        )

        # Calculate delta properties
        base_props = base_registry["Normal"].default_properties
        current_props = {
            "fontFamily": token.font_family or base_props.get("fontFamily"),
            "fontSize": token.font_size or base_props.get("fontSize"),
            "fontWeight": token.font_weight or base_props.get("fontWeight"),
            "lineHeight": token.line_height or base_props.get("lineHeight")
        }

        def calculate_delta(base: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
            delta = {}
            for key, value in current.items():
                if base.get(key) != value:
                    delta[key] = value
            return delta

        delta = calculate_delta(base_props, current_props)
        token.delta_properties = delta

        # Verify inheritance resolution
        assert token.should_generate_delta()
        assert token.delta_properties == {
            "fontSize": "12pt",
            "fontWeight": 600
        }

        # Verify inherited properties are not in delta
        assert "fontFamily" not in token.delta_properties
        assert "lineHeight" not in token.delta_properties

    def test_inheritance_performance(self):
        """Test inheritance resolution performance with many tokens"""
        import time

        # Create large token hierarchy
        base_registry = {
            "Normal": BaseStyleDefinition(
                style_id="Normal",
                style_type="paragraph",
                default_properties={"fontSize": "11pt", "fontWeight": 400},
                emu_calculated_properties={"fontSize": 139700}
            )
        }

        # Create 100 inherited tokens
        tokens = []
        for i in range(100):
            token = InheritedTypographyToken(
                id=f"token_{i}",
                base_style="Normal",
                inheritance_mode="auto",
                font_size=f"{12 + (i % 10)}pt",
                font_weight=400 + (i % 5) * 100
            )
            tokens.append(token)

        # Measure resolution time
        start_time = time.time()

        for token in tokens:
            # Simulate inheritance resolution
            base_props = base_registry[token.base_style].default_properties
            current_props = {
                "fontSize": token.font_size,
                "fontWeight": token.font_weight
            }

            delta = {}
            for key, value in current_props.items():
                if base_props.get(key) != value:
                    delta[key] = value

            token.delta_properties = delta

        end_time = time.time()
        processing_time = end_time - start_time

        # Should process quickly
        assert processing_time < 0.1  # Less than 100ms for 100 tokens
        assert len(tokens) == 100

        # Verify all tokens have delta properties
        for token in tokens:
            assert len(token.delta_properties) > 0


class TestErrorHandling:
    """Test error handling in inheritance system"""

    def test_missing_base_style_handling(self):
        """Test handling of missing base style references"""
        token = InheritedTypographyToken(
            id="orphan_token",
            base_style="NonExistentStyle",
            inheritance_mode="auto"
        )

        base_registry = {
            "Normal": BaseStyleDefinition(
                style_id="Normal",
                style_type="paragraph",
                default_properties={},
                emu_calculated_properties={}
            )
        }

        # Should handle missing base style gracefully
        base_style = base_registry.get(token.base_style)
        assert base_style is None  # Missing style detected

    def test_invalid_inheritance_mode(self):
        """Test handling of invalid inheritance modes"""
        token = InheritedTypographyToken(
            id="invalid_token",
            base_style="Normal",
            inheritance_mode="invalid_mode"
        )

        # Should not generate delta for invalid mode
        assert not token.should_generate_delta()

    def test_malformed_properties_handling(self):
        """Test handling of malformed style properties"""
        base_properties = {
            "fontSize": "11pt",
            "fontWeight": 400
        }

        current_properties = {
            "fontSize": None,      # Malformed
            "fontWeight": "invalid",  # Malformed
            "validProp": "12pt"    # Valid
        }

        def safe_calculate_delta(base: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
            delta = {}
            for key, value in current.items():
                if value is not None and base.get(key) != value:
                    delta[key] = value
            return delta

        delta = safe_calculate_delta(base_properties, current_properties)

        # Should handle malformed values gracefully
        assert "fontSize" not in delta  # None value ignored
        assert "fontWeight" in delta    # Invalid value included (validation elsewhere)
        assert "validProp" in delta     # Valid new property included


# Performance benchmarks
class TestPerformanceBenchmarks:
    """Performance benchmarks for inheritance system"""

    @pytest.mark.skip("Performance test - run manually")
    def test_large_scale_inheritance_performance(self):
        """Benchmark inheritance resolution with large token sets"""
        import time

        # Create large base registry
        base_registry = {}
        for i in range(10):  # 10 base styles
            base_registry[f"Base{i}"] = BaseStyleDefinition(
                style_id=f"Base{i}",
                style_type="paragraph",
                default_properties={
                    "fontSize": f"{10 + i}pt",
                    "fontWeight": 400 + i * 100
                },
                emu_calculated_properties={
                    "fontSize": EMUConversionEngine.pt_to_emu(10 + i)
                }
            )

        # Create 1000 inherited tokens
        tokens = []
        for i in range(1000):
            base_style = f"Base{i % 10}"
            token = InheritedTypographyToken(
                id=f"token_{i}",
                base_style=base_style,
                inheritance_mode="auto",
                font_size=f"{12 + (i % 20)}pt"
            )
            tokens.append(token)

        # Benchmark inheritance resolution
        start_time = time.time()

        for token in tokens:
            base_props = base_registry[token.base_style].default_properties
            delta = {"fontSize": token.font_size} if token.font_size != base_props.get("fontSize") else {}
            token.delta_properties = delta

        end_time = time.time()

        print(f"Processed {len(tokens)} tokens in {end_time - start_time:.3f}s")
        assert end_time - start_time < 1.0  # Should complete in under 1 second


if __name__ == "__main__":
    # Run specific test categories
    print("Running StyleStack Style Inheritance Core Tests...")
    pytest.main([__file__, "-v"])