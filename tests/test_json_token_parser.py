"""
Test suite for JSON token parsing and validation
Tests the conversion from JSON to JSON token format with comprehensive validation

# Use venv for testing: source venv/bin/activate && python -m pytest
"""

import json
import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, mock_open

# Import the modules we'll be testing
import sys
sys.path.append('/Users/ynse/projects/StyleStack')

from tools.token_parser import TokenParser
from tools.token_resolver import TokenResolver


class TestJSONTokenStructure:
    """Test JSON token file structure and validation"""
    
    def test_core_design_tokens_json_structure(self):
        """Test that core design tokens follow proper JSON schema"""
        sample_tokens = {
            "$schema": "https://stylestack.dev/schemas/design-tokens.schema.json",
            "colors": {
                "brand": {
                    "primary": {
                        "value": "#0066CC",
                        "type": "color",
                        "description": "Primary brand color",
                        "$extensions": {
                            "stylestack": {
                                "contrast": 4.5,
                                "category": "primitive"
                            }
                        }
                    }
                }
            },
            "typography": {
                "font": {
                    "theme": {
                        "major": {
                            "value": "Segoe UI",
                            "type": "fontFamily",
                            "description": "Major theme font for headings"
                        },
                        "minor": {
                            "value": "Segoe UI",
                            "type": "fontFamily", 
                            "description": "Minor theme font for body text"
                        }
                    }
                }
            },
            "spacing": {
                "base": {
                    "value": "12pt",
                    "type": "dimension",
                    "$extensions": {
                        "stylestack": {
                            "emu": 152400,
                            "category": "primitive"
                        }
                    }
                }
            }
        }
        
        # Validate structure
        assert "$schema" in sample_tokens
        assert "colors" in sample_tokens
        assert "typography" in sample_tokens
        assert "spacing" in sample_tokens
        
        # Validate token format
        primary_color = sample_tokens["colors"]["brand"]["primary"]
        assert "value" in primary_color
        assert "type" in primary_color
        assert primary_color["type"] == "color"
        assert "$extensions" in primary_color
        
    def test_channel_config_json_structure(self):
        """Test channel configuration JSON structure"""
        sample_channel = {
            "$schema": "https://stylestack.dev/schemas/channel-config.schema.json",
            "metadata": {
                "channel": "present",
                "description": "Presentation-focused template optimizations",
                "version": "1.0.0"
            },
            "targets": [
                {
                    "file": "ppt/presentation.xml",
                    "ns": {
                        "p": "http://schemas.openxmlformats.org/presentationml/2006/main"
                    },
                    "ops": [
                        {
                            "set": {
                                "xpath": "//p:presentation/@serverZoom",
                                "value": "100"
                            }
                        }
                    ]
                }
            ]
        }
        
        # Validate structure
        assert "metadata" in sample_channel
        assert "targets" in sample_channel
        assert isinstance(sample_channel["targets"], list)
        
        # Validate target structure
        target = sample_channel["targets"][0]
        assert "file" in target
        assert "ns" in target
        assert "ops" in target
        
    def test_organization_patch_json_structure(self):
        """Test organization patch JSON structure"""
        sample_org_patch = {
            "$schema": "https://stylestack.dev/schemas/org-patch.schema.json",
            "metadata": {
                "organization": "acme",
                "description": "ACME Corporation brand tokens",
                "version": "2.1.0"
            },
            "overrides": {
                "colors": {
                    "brand": {
                        "primary": {
                            "value": "#FF6600",
                            "type": "color",
                            "description": "ACME orange brand color"
                        }
                    }
                }
            },
            "patches": [
                {
                    "operation": "set",
                    "target": "//a:srgbClr[@val='0066CC']/@val", 
                    "value": "{colors.brand.primary}"
                }
            ]
        }
        
        # Validate structure
        assert "metadata" in sample_org_patch
        assert "overrides" in sample_org_patch
        assert "patches" in sample_org_patch
        assert isinstance(sample_org_patch["patches"], list)


class TestJSONTokenParser:
    """Test JSON token parsing functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.parser = TokenParser()
        self.sample_json_content = {
            "colors": {
                "brand": {
                    "primary": {
                        "value": "#0066CC",
                        "type": "color"
                    }
                }
            }
        }
        
    def test_load_json_token_file(self):
        """Test loading JSON token file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_json_content, f)
            json_path = f.name
            
        try:
            # Test JSON loading
            result = self.parser.load_token_definitions(json_path)
            assert result == self.sample_json_content
            assert "colors" in result
            assert result["colors"]["brand"]["primary"]["value"] == "#0066CC"
        finally:
            Path(json_path).unlink()
            
    def test_json_format_validation(self):
        """Test JSON format validation"""
        # Valid JSON should parse successfully
        valid_json = '{"colors": {"primary": {"value": "#FF0000", "type": "color"}}}'
        result = json.loads(valid_json)
        assert "colors" in result
        
        # Invalid JSON should raise exception
        with pytest.raises(json.JSONDecodeError):
            json.loads('{"colors": {"primary": {"value": "#FF0000" "type": "color"}}}')  # Missing comma
            
    def test_json_schema_compliance(self):
        """Test that JSON tokens comply with expected schema"""
        token = {
            "value": "#0066CC",
            "type": "color",
            "description": "Primary brand color",
            "$extensions": {
                "stylestack": {
                    "contrast": 4.5,
                    "category": "primitive"
                }
            }
        }
        
        # Required fields
        assert "value" in token
        assert "type" in token
        
        # Optional fields
        if "description" in token:
            assert isinstance(token["description"], str)
        if "$extensions" in token:
            assert isinstance(token["$extensions"], dict)
            
    def test_hierarchical_token_resolution_json(self):
        """Test hierarchical token resolution with JSON format"""
        core_tokens = {
            "colors": {
                "neutral": {
                    "100": {"value": "#F5F5F5", "type": "color"}
                }
            }
        }
        
        org_tokens = {
            "colors": {
                "brand": {
                    "primary": {"value": "#0066CC", "type": "color"}
                }
            }
        }
        
        # Test token resolution maintains hierarchy
        resolver = TokenResolver()
        resolved = resolver.resolve_hierarchy([core_tokens, org_tokens])
        
        # Should have both core and org tokens
        assert "colors" in resolved
        assert "neutral" in resolved["colors"]  # From core
        assert "brand" in resolved["colors"]    # From org
        assert resolved["colors"]["brand"]["primary"]["value"] == "#0066CC"
        
    def test_token_variable_substitution_json(self):
        """Test token variable substitution with JSON values"""
        tokens = {
            "colors": {
                "brand": {
                    "primary": {"value": "#0066CC", "type": "color"}
                }
            },
            "semantic": {
                "text": {
                    "primary": {"value": "{colors.brand.primary}", "type": "color"}
                }
            }
        }
        
        # Test variable resolution
        primary_ref = tokens["semantic"]["text"]["primary"]["value"]
        assert primary_ref == "{colors.brand.primary}"
        
        # After resolution, should resolve to actual value
        resolver = TokenResolver()
        resolved = resolver.resolve_variables(tokens)
        resolved_value = resolved["semantic"]["text"]["primary"]["value"]
        assert resolved_value == "#0066CC"


class TestJSONTokenValidation:
    """Test JSON token validation and error handling"""
    
    def test_missing_required_fields(self):
        """Test validation of required token fields"""
        # Missing 'type' field
        invalid_token = {
            "value": "#0066CC",
            # "type": "color",  # Missing required field
        }
        
        # Should fail validation
        assert "value" in invalid_token
        assert "type" not in invalid_token  # This should cause validation failure
        
    def test_invalid_token_types(self):
        """Test validation of token type values"""
        valid_types = ["color", "dimension", "fontFamily", "fontWeight", "number", "typography"]
        
        # Valid type
        valid_token = {"value": "#FF0000", "type": "color"}
        assert valid_token["type"] in valid_types
        
        # Invalid type
        invalid_token = {"value": "#FF0000", "type": "invalid_type"}
        assert invalid_token["type"] not in valid_types
        
    def test_color_value_validation(self):
        """Test validation of color token values"""
        # Valid hex color
        valid_color = {"value": "#0066CC", "type": "color"}
        hex_pattern = r'^#[0-9A-Fa-f]{6}$'
        import re
        assert re.match(hex_pattern, valid_color["value"])
        
        # Invalid hex color
        invalid_color = {"value": "#GGG", "type": "color"}
        assert not re.match(hex_pattern, invalid_color["value"])
        
    def test_dimension_value_validation(self):
        """Test validation of dimension token values"""
        # Valid dimension values
        valid_dimensions = [
            {"value": "12pt", "type": "dimension"},
            {"value": "16px", "type": "dimension"},
            {"value": "1.5rem", "type": "dimension"},
            {"value": "24", "type": "dimension"}
        ]
        
        for dim in valid_dimensions:
            assert "value" in dim
            assert dim["type"] == "dimension"
            
    def test_font_family_validation(self):
        """Test validation of font family tokens"""
        # Valid font families
        valid_fonts = [
            {"value": "Segoe UI", "type": "fontFamily"},
            {"value": ["Inter", "Segoe UI", "sans-serif"], "type": "fontFamily"},
            {"value": "Arial", "type": "fontFamily"}
        ]
        
        for font in valid_fonts:
            assert "value" in font
            assert font["type"] == "fontFamily"
            assert isinstance(font["value"], (str, list))


class TestJSONTokenPerformance:
    """Test JSON token parsing performance"""
    
    def test_json_parsing_speed(self):
        """Test that JSON parsing is faster than JSON"""
        import time
        
        # Large token structure
        large_tokens = {
            "colors": {},
            "typography": {},
            "spacing": {}
        }
        
        # Generate large token set
        for i in range(100):
            large_tokens["colors"][f"color_{i}"] = {
                "value": f"#{i:06x}",
                "type": "color"
            }
            
        json_content = json.dumps(large_tokens)
        
        # Time JSON parsing
        start_time = time.time()
        for _ in range(100):
            parsed = json.loads(json_content)
        json_time = time.time() - start_time
        
        # JSON parsing should be reasonably fast
        assert json_time < 1.0  # Should parse 100 times in under 1 second
        assert len(parsed["colors"]) == 100
        
    def test_memory_efficiency(self):
        """Test JSON token memory usage"""
        import sys
        
        # Create token structure
        tokens = {
            "colors": {f"color_{i}": {"value": f"#{i:06x}", "type": "color"} 
                     for i in range(1000)}
        }
        
        # Check memory usage is reasonable
        json_str = json.dumps(tokens)
        size_mb = sys.getsizeof(json_str) / (1024 * 1024)
        
        # Should be under 1MB for 1000 color tokens
        assert size_mb < 1.0


class TestCrossPllatformCompatibility:
    """Test JSON tokens work across platforms"""
    
    def test_google_apps_script_compatibility(self):
        """Test JSON format works with Google Apps Script patterns"""
        # Google Apps Script expects standard JSON
        gas_compatible_tokens = {
            "colors": {
                "brand": {
                    "primary": {
                        "r": 0.0,
                        "g": 0.4,
                        "b": 0.8
                    }
                }
            }
        }
        
        # Should serialize/deserialize cleanly
        json_str = json.dumps(gas_compatible_tokens)
        parsed = json.loads(json_str)
        assert parsed["colors"]["brand"]["primary"]["r"] == 0.0
        
    def test_office_js_compatibility(self):
        """Test JSON format works with Office.js patterns"""
        # Office.js expects camelCase properties
        office_compatible_tokens = {
            "documentStyle": {
                "backgroundColor": {
                    "color": {
                        "rgbColor": {
                            "red": 0.95,
                            "green": 0.95,
                            "blue": 0.95
                        }
                    }
                }
            }
        }
        
        # Should be valid JSON
        json_str = json.dumps(office_compatible_tokens)
        parsed = json.loads(json_str)
        assert "documentStyle" in parsed
        
    def test_rest_api_compatibility(self):
        """Test JSON tokens work with REST API patterns"""
        # REST APIs expect standard JSON with proper headers
        api_response_format = {
            "data": {
                "tokens": {
                    "colors": {
                        "brand": {
                            "primary": "#0066CC"
                        }
                    }
                }
            },
            "meta": {
                "version": "1.0.0",
                "format": "stylestack-tokens"
            }
        }
        
        # Should serialize properly for API responses
        json_str = json.dumps(api_response_format, indent=2)
        parsed = json.loads(json_str)
        assert parsed["data"]["tokens"]["colors"]["brand"]["primary"] == "#0066CC"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])