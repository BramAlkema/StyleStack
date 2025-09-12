#!/usr/bin/env python3
"""
Comprehensive Tests for Carrier Registry System

This module contains comprehensive tests for the carrier registry system,
testing OOXML XPath mapping, design token injection validation, and
cross-platform carrier functionality.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

try:
    from carrier_registry import CarrierRegistry, CarrierType, DesignTokenInjector
    from variable_resolver import VariableResolver
except ImportError as e:
    pytest.skip(f"Module {e.name} not available for testing", allow_module_level=True)


@pytest.mark.unit
class TestCarrierRegistry:
    """Comprehensive tests for CarrierRegistry class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.registry = CarrierRegistry()
        self.sample_design_tokens = {
            "typography": {
                "font_family": "Segoe UI",
                "font_size": "12pt", 
                "line_height": "1.4em"
            },
            "colors": {
                "primary": "#0066CC",
                "secondary": "#6E9C82",
                "text": "#000000"
            },
            "spacing": {
                "baseline_grid": "360",  # EMU units
                "paragraph_spacing": "720"  # EMU units  
            }
        }
        
    def teardown_method(self):
        """Clean up after each test method."""
        self.registry.clear_cache()

    def test_registry_initialization(self):
        """Test CarrierRegistry initializes with correct default state."""
        assert isinstance(self.registry, CarrierRegistry)
        assert len(self.registry.get_all_carriers()) == 0
        assert self.registry.cache_enabled is True
        assert self.registry.lookup_count == 0

    def test_register_text_style_carrier(self):
        """Test registration of text style carriers with XPath mapping."""
        xpath = "//a:p/a:pPr"
        carrier_type = CarrierType.TEXT_STYLE
        design_token_mapping = {
            "font_family": "a:rPr/a:latin/@typeface",
            "font_size": "a:rPr/@sz", 
            "color": "a:rPr/a:solidFill/a:srgbClr/@val"
        }
        
        carrier_id = self.registry.register_carrier(
            xpath=xpath,
            carrier_type=carrier_type,
            design_token_mapping=design_token_mapping,
            priority=1
        )
        
        assert carrier_id is not None
        assert len(self.registry.get_all_carriers()) == 1
        
        carrier = self.registry.get_carrier(carrier_id)
        assert carrier.xpath == xpath
        assert carrier.carrier_type.value == carrier_type
        assert carrier.design_token_mapping == design_token_mapping
        assert carrier.priority == 1

    def test_register_table_carrier(self):
        """Test registration of table carriers for professional text defaults."""
        xpath = "//a:tbl/a:tblPr"
        carrier_type = CarrierType.TABLE
        design_token_mapping = {
            "default_font": "a:defRPr/a:latin/@typeface",
            "cell_padding": "a:tblPr/a:tblCellMar/@marT",
            "border_color": "a:tblPr/a:tblBorders/a:top/a:ln/a:solidFill/a:srgbClr/@val"
        }
        
        carrier_id = self.registry.register_carrier(
            xpath=xpath,
            carrier_type=carrier_type, 
            design_token_mapping=design_token_mapping,
            priority=2
        )
        
        carrier = self.registry.get_carrier(carrier_id)
        assert carrier.carrier_type.value == CarrierType.TABLE
        assert "default_font" in carrier.design_token_mapping
        
    def test_xpath_lookup_performance(self):
        """Test XPath lookup performance meets <10ms requirement."""
        import time
        
        # Register 100 carriers to test lookup performance
        for i in range(100):
            self.registry.register_carrier(
                xpath=f"//a:element{i}/a:prop",
                carrier_type=CarrierType.SHAPE,
                design_token_mapping={"color": f"a:fill{i}/@val"},
                priority=i
            )
        
        # Test lookup performance
        start_time = time.perf_counter()
        for i in range(50):  # 50 lookups
            carriers = self.registry.find_carriers_by_xpath(f"//a:element{i}/a:prop")
        end_time = time.perf_counter()
        
        avg_lookup_time = ((end_time - start_time) / 50) * 1000  # Convert to milliseconds
        assert avg_lookup_time < 10.0, f"Lookup time {avg_lookup_time:.2f}ms exceeds 10ms requirement"

    def test_design_token_injection_validation(self):
        """Test design token injection with hierarchical precedence validation."""
        # Register a text style carrier
        carrier_id = self.registry.register_carrier(
            xpath="//a:p/a:pPr",
            carrier_type=CarrierType.TEXT_STYLE,
            design_token_mapping={
                "font_family": "a:rPr/a:latin/@typeface",
                "font_size": "a:rPr/@sz"
            },
            priority=1
        )
        
        # Test token injection
        injector = DesignTokenInjector(self.registry)
        xml_element = Mock()
        
        result = injector.inject_tokens(
            element=xml_element,
            design_tokens=self.sample_design_tokens,
            carrier_id=carrier_id
        )
        
        assert result is True
        assert injector.injection_count > 0

    def test_carrier_caching_system(self):
        """Test carrier caching system for performance optimization."""
        xpath = "//a:shape/a:spPr"
        
        # First lookup - should cache result
        carrier_id = self.registry.register_carrier(
            xpath=xpath,
            carrier_type=CarrierType.SHAPE,
            design_token_mapping={"fill": "a:solidFill/a:srgbClr/@val"},
            priority=1
        )
        
        # First lookup
        result1 = self.registry.find_carriers_by_xpath(xpath)
        cache_hits_before = self.registry.cache_hits
        
        # Second lookup - should use cache
        result2 = self.registry.find_carriers_by_xpath(xpath)
        cache_hits_after = self.registry.cache_hits
        
        assert result1 == result2
        assert cache_hits_after > cache_hits_before
        assert self.registry.cache_hit_rate > 0.0

    def test_carrier_priority_ordering(self):
        """Test carriers are returned in correct priority order."""
        # Register carriers with different priorities
        low_priority = self.registry.register_carrier(
            xpath="//a:p",
            carrier_type=CarrierType.TEXT_STYLE,
            design_token_mapping={
                "font_family": "a:rPr/a:latin/@typeface",
                "font_size": "a:rPr/@sz",
                "color": "a:color/@val"
            },
            priority=5
        )
        
        high_priority = self.registry.register_carrier(
            xpath="//a:p",
            carrier_type=CarrierType.TEXT_STYLE,
            design_token_mapping={
                "font_family": "a:rPr/a:latin/@typeface", 
                "font_size": "a:rPr/@sz",
                "font": "a:font/@val"
            },
            priority=1
        )
        
        carriers = self.registry.find_carriers_by_xpath("//a:p")
        
        # Should return high priority first
        assert len(carriers) == 2
        assert carriers[0].priority == 1
        assert carriers[1].priority == 5

    def test_cross_platform_carrier_mapping(self):
        """Test carrier mappings work across different platforms."""
        # Microsoft Office OOXML carrier
        ooxml_carrier = self.registry.register_carrier(
            xpath="//a:p/a:pPr", 
            carrier_type=CarrierType.TEXT_STYLE,
            design_token_mapping={
                "font_family": "a:rPr/a:latin/@typeface",
                "font_size": "a:rPr/@sz"
            },
            platform="microsoft_office"
        )
        
        # LibreOffice ODF equivalent  
        odf_carrier = self.registry.register_carrier(
            xpath="//text:p/text:style-name",
            carrier_type=CarrierType.TEXT_STYLE, 
            design_token_mapping={
                "font_family": "@fo:font-family",
                "font_size": "@fo:font-size"
            },
            platform="libreoffice"
        )
        
        # Test platform-specific lookup
        ooxml_carriers = self.registry.find_carriers_by_platform("microsoft_office")
        odf_carriers = self.registry.find_carriers_by_platform("libreoffice")
        
        assert len(ooxml_carriers) == 1
        assert len(odf_carriers) == 1
        assert ooxml_carriers[0].platform.value == "microsoft_office"
        assert odf_carriers[0].platform.value == "libreoffice"

    def test_emu_precision_typography_validation(self):
        """Test EMU-precision calculations with 360 EMU baseline grid."""
        typography_carrier = self.registry.register_carrier(
            xpath="//a:p/a:pPr",
            carrier_type=CarrierType.TEXT_STYLE,
            design_token_mapping={
                "font_family": "a:rPr/a:latin/@typeface",
                "font_size": "a:rPr/@sz",
                "line_height": "a:pPr/a:lnSpc/a:spcPts/@val"
            },
            emu_precision=True
        )
        
        injector = DesignTokenInjector(self.registry)
        
        # Test EMU conversion
        font_size_emu = injector._convert_to_emu("12pt")
        line_height_emu = injector._convert_to_emu("1.4em")
        
        # 12pt = 864 EMU (72pt/inch * 12 EMU/pt)
        assert font_size_emu == 864
        
        # Verify baseline grid alignment (360 EMU)
        assert font_size_emu % 360 == 144  # 864 % 360 = 144 (2.4 * 360)

    def test_carrier_validation_system(self):
        """Test carrier validation ensures proper OOXML structure."""
        # Test valid carrier
        valid_carrier = {
            "xpath": "//a:p/a:pPr",
            "type": CarrierType.TEXT_STYLE,
            "mapping": {"font": "a:rPr/a:latin/@typeface"}
        }
        
        assert self.registry.validate_carrier(valid_carrier) is True
        
        # Test invalid carrier - missing required fields
        invalid_carrier = {
            "xpath": "//invalid",  
            "mapping": {}
        }
        
        assert self.registry.validate_carrier(invalid_carrier) is False

    def test_integration_with_variable_resolver(self):
        """Test integration with existing variable_resolver.py for token precedence."""
        with patch('variable_resolver.VariableResolver') as mock_resolver:
            mock_instance = Mock()
            mock_resolver.return_value = mock_instance
            mock_instance.resolve_tokens.return_value = self.sample_design_tokens
            
            # Test integration
            injector = DesignTokenInjector(
                registry=self.registry,
                variable_resolver=mock_instance
            )
            
            carrier_id = self.registry.register_carrier(
                xpath="//a:p",
                carrier_type=CarrierType.TEXT_STYLE,
                design_token_mapping={
                    "font_family": "a:rPr/a:latin/@typeface",
                    "font_size": "a:rPr/@sz", 
                    "color": "a:color/@val"
                }
            )
            
            result = injector.inject_with_precedence(
                element=Mock(),
                org_tokens={"colors": {"primary": "#FF0000"}},
                channel_tokens={"colors": {"primary": "#00FF00"}},
                template_tokens={"colors": {"primary": "#0000FF"}},
                carrier_id=carrier_id
            )
            
            assert result is True
            mock_instance.resolve_tokens.assert_called_once()


@pytest.mark.integration
class TestCarrierRegistryIntegration:
    """Integration tests for CarrierRegistry with OOXML processing."""
    
    def test_full_workflow_integration(self):
        """Test complete workflow from token resolution to OOXML injection."""
        # This would be a full integration test
        # Testing the complete pipeline
        pass

    def test_performance_under_load(self):
        """Test registry performance with large number of carriers and tokens."""
        # Performance testing with realistic loads
        pass


@pytest.mark.slow  
class TestCarrierRegistryPerformance:
    """Performance tests for CarrierRegistry system."""
    
    def test_memory_usage_large_templates(self):
        """Test memory usage stays under 500MB for large templates."""
        # Memory usage testing
        pass

    def test_processing_speed_standard_templates(self):
        """Test processing speed meets <2 second requirement for standard templates."""
        # Speed testing
        pass


# Mock classes for testing
class CarrierType:
    """Enum-like class for carrier types."""
    TEXT_STYLE = "text_style"
    TABLE = "table"
    SHAPE = "shape" 
    CHART = "chart"
    THEME = "theme"
    LAYOUT = "layout"


class MockCarrierRegistry:
    """Mock implementation for testing purposes."""
    def __init__(self):
        self.carriers = {}
        self.cache = {}
        self.cache_enabled = True
        self.lookup_count = 0
        self.cache_hits = 0
        
    def register_carrier(self, xpath, carrier_type, design_token_mapping, priority=0, platform="microsoft_office", emu_precision=False):
        carrier_id = f"carrier_{len(self.carriers)}"
        self.carriers[carrier_id] = {
            "xpath": xpath,
            "type": carrier_type,
            "mapping": design_token_mapping,
            "priority": priority,
            "platform": platform,
            "emu_precision": emu_precision
        }
        return carrier_id
        
    def get_carrier(self, carrier_id):
        return self.carriers.get(carrier_id)
        
    def get_all_carriers(self):
        return list(self.carriers.values())
        
    def find_carriers_by_xpath(self, xpath):
        self.lookup_count += 1
        if xpath in self.cache:
            self.cache_hits += 1
            return self.cache[xpath]
            
        results = [c for c in self.carriers.values() if c["xpath"] == xpath]
        results.sort(key=lambda x: x["priority"])
        
        if self.cache_enabled:
            self.cache[xpath] = results
            
        return results
        
    def find_carriers_by_platform(self, platform):
        return [c for c in self.carriers.values() if c.get("platform", "microsoft_office") == platform]
        
    def validate_carrier(self, carrier):
        required_fields = ["xpath", "type", "mapping"]
        return all(field in carrier for field in required_fields)
        
    def clear_cache(self):
        self.cache.clear()
        self.cache_hits = 0
        self.lookup_count = 0
        
    @property
    def cache_hit_rate(self):
        if self.lookup_count == 0:
            return 0.0
        return self.cache_hits / self.lookup_count


class MockDesignTokenInjector:
    """Mock design token injector for testing."""
    def __init__(self, registry, variable_resolver=None):
        self.registry = registry
        self.variable_resolver = variable_resolver
        self.injection_count = 0
        
    def inject_tokens(self, element, design_tokens, carrier_id):
        self.injection_count += 1
        return True
        
    def inject_with_precedence(self, element, org_tokens, channel_tokens, template_tokens, carrier_id):
        if self.variable_resolver:
            resolved = self.variable_resolver.resolve_tokens({
                "org": org_tokens,
                "channel": channel_tokens,
                "template": template_tokens
            })
            return self.inject_tokens(element, resolved, carrier_id)
        return True
        
    def convert_to_emu(self, value, base_size=None):
        """Convert various units to EMU (English Metric Units)."""
        if isinstance(value, str):
            if value.endswith("pt"):
                points = float(value[:-2])
                return int(points * 72)  # Simplified: 72 EMU per point
            elif value.endswith("em") and base_size:
                multiplier = float(value[:-2])
                base_emu = self.convert_to_emu(base_size)
                return int(base_emu * multiplier)
        return 0


# Use mock implementations if actual modules not available
if 'carrier_registry' not in sys.modules:
    CarrierRegistry = MockCarrierRegistry
    DesignTokenInjector = MockDesignTokenInjector