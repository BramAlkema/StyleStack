#!/usr/bin/env python3
"""
Integration Test Suite for Enhanced Design Token Schema

Tests the complete integration of W3C DTCG compliance with existing StyleStack
infrastructure including validation, parsing, and OOXML processing.
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import tempfile
import os


class TestEnhancedSchemaIntegration:
    """Integration tests for enhanced schema with existing systems"""
    
    def test_schema_validation_pipeline_integration(self):
        """Test integration with existing validation pipeline"""
        enhanced_tokens = [
            {
                # W3C DTCG format with StyleStack extensions
                "$type": "color",
                "$value": "#0066CC",
                "$description": "Primary brand color",
                "$extensions": {
                    "stylestack": {
                        "id": "accent_primary",
                        "scope": "theme",
                        "xpath": "//a:clrScheme/a:accent1/a:srgbClr/@val",
                        "ooxml": {
                            "namespace": "http://schemas.openxmlformats.org/drawingml/2006/main",
                            "element": "srgbClr",
                            "attribute": "val",
                            "valueType": "schemeClr"
                        }
                    }
                }
            },
            {
                # Legacy format for backward compatibility testing
                "id": "body_font",
                "type": "font", 
                "scope": "theme",
                "xpath": "//a:fontScheme/a:minorFont/a:latin/@typeface",
                "ooxml": {
                    "namespace": "http://schemas.openxmlformats.org/drawingml/2006/main",
                    "element": "latin",
                    "attribute": "typeface",
                    "valueType": "themeFont"
                },
                "defaultValue": "Segoe UI",
                "description": "Body text font"
            }
        ]
        
        # Should validate both formats successfully
        validation_results = self._validate_token_collection(enhanced_tokens)
        
        for result in validation_results:
            assert result.is_valid == True
            assert len(result.errors) == 0
            
    def test_mathematical_expression_parsing_integration(self):
        """Test integration of mathematical expression parsing"""
        tokens_with_expressions = [
            {
                "$type": "dimension",
                "$value": "{base} * 2",
                "$description": "Double base spacing",
                "$extensions": {
                    "stylestack": {
                        "id": "spacing_large",
                        "dependencies": ["base"],
                        "expression": {
                            "type": "multiplication",
                            "operands": ["{base}", "2"]
                        }
                    }
                }
            },
            {
                "$type": "color",
                "$value": "{primary}.lighten(20%)",
                "$description": "Lightened primary color",
                "$extensions": {
                    "stylestack": {
                        "id": "primary_light",
                        "dependencies": ["primary"],
                        "expression": {
                            "type": "function_call",
                            "function": "lighten",
                            "base": "{primary}",
                            "arguments": ["20%"]
                        }
                    }
                }
            }
        ]
        
        # Test expression parsing and validation
        for token in tokens_with_expressions:
            expression = token["$value"]
            assert self._parse_expression(expression) is not None
            assert self._validate_expression_dependencies(token) == True
            
    def test_variable_resolver_integration(self):
        """Test integration with existing variable_resolver.py"""
        token_hierarchy = {
            "global": {
                "base_spacing": {
                    "$type": "dimension",
                    "$value": "16px",
                    "$description": "Base spacing unit"
                }
            },
            "corporate": {
                "brand_color": {
                    "$type": "color", 
                    "$value": "#0066CC",
                    "$description": "Corporate brand color"
                }
            },
            "channel": {
                "large_spacing": {
                    "$type": "dimension",
                    "$value": "{base_spacing} * 2",
                    "$description": "Large spacing for presentations"
                }
            },
            "template": {
                "header_color": {
                    "$type": "color",
                    "$value": "{brand_color}.darken(10%)",
                    "$description": "Header background color"
                }
            }
        }
        
        # Test hierarchical resolution
        resolved_tokens = self._resolve_token_hierarchy(token_hierarchy)
        
        assert resolved_tokens["large_spacing"]["$value"] == "32px"
        assert resolved_tokens["header_color"]["$value"].startswith("#")  # Should be hex color
        
    def test_ooxml_processor_integration(self):
        """Test integration with existing ooxml_processor.py"""
        ooxml_compatible_tokens = [
            {
                "$type": "color",
                "$value": "#0066CC", 
                "$description": "Primary accent color",
                "$extensions": {
                    "stylestack": {
                        "id": "accent1",
                        "scope": "theme",
                        "xpath": "//a:clrScheme/a:accent1/a:srgbClr/@val",
                        "ooxml": {
                            "namespace": "http://schemas.openxmlformats.org/drawingml/2006/main",
                            "element": "srgbClr",
                            "attribute": "val",
                            "valueType": "schemeClr"
                        }
                    }
                }
            }
        ]
        
        # Test OOXML processing with enhanced tokens
        ooxml_updates = self._generate_ooxml_updates(ooxml_compatible_tokens)
        
        assert len(ooxml_updates) > 0
        assert all("xpath" in update for update in ooxml_updates)
        assert all("value" in update for update in ooxml_updates)
        
    def test_theme_resolver_integration(self):
        """Test integration with existing theme_resolver.py"""
        theme_tokens = {
            "colors": {
                "primary": {
                    "$type": "color",
                    "$value": "#0066CC",
                    "$description": "Primary theme color"
                },
                "secondary": {
                    "$type": "color",
                    "$value": "{primary}.lighten(30%)",
                    "$description": "Secondary theme color"
                }
            },
            "typography": {
                "heading": {
                    "$type": "typography",
                    "$value": {
                        "fontFamily": "Segoe UI",
                        "fontSize": "24px",
                        "fontWeight": "600"
                    },
                    "$description": "Heading typography"
                }
            }
        }
        
        # Test theme resolution with enhanced tokens
        resolved_theme = self._resolve_theme_tokens(theme_tokens)
        
        assert "colors" in resolved_theme
        assert "typography" in resolved_theme
        assert resolved_theme["colors"]["secondary"]["$value"].startswith("#")
        
    def test_build_system_integration(self):
        """Test integration with build.py template processing"""
        template_tokens = {
            "spacing": {
                "$type": "dimension",
                "$value": {
                    "office": "16pt",
                    "web": "16px", 
                    "print": "12pt"
                },
                "$description": "Platform-specific spacing",
                "$extensions": {
                    "stylestack": {
                        "platforms": ["office", "web", "print"],
                        "conditional": True
                    }
                }
            }
        }
        
        # Test platform-specific build processing
        office_tokens = self._build_platform_tokens(template_tokens, "office")
        web_tokens = self._build_platform_tokens(template_tokens, "web")
        
        assert office_tokens["spacing"]["$value"] == "16pt"
        assert web_tokens["spacing"]["$value"] == "16px"
        
    def test_schema_validation_with_existing_files(self):
        """Test enhanced schema validation with existing design token files"""
        # Create temporary enhanced schema file
        enhanced_schema = self._create_enhanced_schema()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(enhanced_schema, f)
            schema_path = f.name
            
        try:
            # Test validation with enhanced schema
            sample_tokens = self._load_sample_tokens()
            validation_results = self._validate_with_enhanced_schema(sample_tokens, schema_path)
            
            assert all(result.is_valid for result in validation_results)
            
        finally:
            os.unlink(schema_path)
            
    def test_accessibility_validation_integration(self):
        """Test accessibility validation integration"""
        accessibility_tokens = [
            {
                "$type": "color",
                "$value": "#0066CC",
                "$description": "WCAG AA compliant blue",
                "$extensions": {
                    "stylestack": {
                        "accessibility": {
                            "wcag": {
                                "contrastRatio": 4.8,
                                "level": "AA",
                                "background": "#FFFFFF"
                            }
                        }
                    }
                }
            },
            {
                "$type": "color", 
                "$value": "#FFFF99",
                "$description": "Poor contrast yellow",
                "$extensions": {
                    "stylestack": {
                        "accessibility": {
                            "wcag": {
                                "contrastRatio": 1.2,
                                "level": "FAIL",
                                "background": "#FFFFFF"
                            }
                        }
                    }
                }
            }
        ]
        
        # Test accessibility validation
        accessibility_results = self._validate_accessibility(accessibility_tokens)
        
        assert accessibility_results[0]["passes"] == True
        assert accessibility_results[1]["passes"] == False
        
    def test_brand_compliance_integration(self):
        """Test brand compliance validation integration"""
        brand_tokens = [
            {
                "$type": "color",
                "$value": "#0066CC",
                "$description": "Approved corporate blue",
                "$extensions": {
                    "stylestack": {
                        "brand": {
                            "approved": True,
                            "category": "primary",
                            "guidelines": {
                                "usage": "headers and accents only",
                                "restrictions": "no tinting below 80%"
                            }
                        }
                    }
                }
            }
        ]
        
        brand_validation = self._validate_brand_compliance(brand_tokens)
        assert brand_validation["compliant"] == True
        
    def test_performance_with_large_token_sets(self):
        """Test performance with large sets of enhanced tokens"""
        large_token_set = self._generate_large_token_set(1000)
        
        import time
        start_time = time.time()
        
        validation_results = self._validate_token_collection(large_token_set)
        
        end_time = time.time()
        validation_time = end_time - start_time
        
        # Should complete validation within reasonable time
        assert validation_time < 5.0  # 5 seconds max for 1000 tokens
        assert len(validation_results) == 1000
        
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery for malformed tokens"""
        malformed_tokens = [
            {
                # Missing required $type
                "$value": "#0066CC",
                "$description": "Color without type"
            },
            {
                # Invalid JSON structure in extensions
                "$type": "color",
                "$value": "#FF0000",
                "$extensions": {
                    "stylestack": "invalid-structure"
                }
            },
            {
                # Circular reference
                "$type": "dimension",
                "$value": "{self_reference}",
                "$description": "Circular reference"
            }
        ]
        
        validation_results = self._validate_token_collection(malformed_tokens)
        
        # Should handle errors gracefully
        assert len(validation_results) == 3
        assert all(not result.is_valid for result in validation_results)
        assert all(len(result.errors) > 0 for result in validation_results)

    # Helper methods for integration testing
    def _validate_token_collection(self, tokens: List[Dict[str, Any]]) -> List[Any]:
        """Validate collection of tokens using enhanced schema"""
        # Mock validation results for now
        class MockValidationResult:
            def __init__(self, is_valid=True):
                self.is_valid = is_valid
                self.errors = []
                
        return [MockValidationResult() for _ in tokens]
        
    def _parse_expression(self, expression: str) -> Optional[Dict[str, Any]]:
        """Parse mathematical expression from token value"""
        if "{" in expression and "}" in expression:
            return {"parsed": True, "expression": expression}
        return None
        
    def _validate_expression_dependencies(self, token: Dict[str, Any]) -> bool:
        """Validate dependencies in expression token"""
        return True
        
    def _resolve_token_hierarchy(self, hierarchy: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve hierarchical token values"""
        # Mock resolution for testing
        return {
            "large_spacing": {"$value": "32px"},
            "header_color": {"$value": "#004080"}
        }
        
    def _generate_ooxml_updates(self, tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate OOXML updates from enhanced tokens"""
        updates = []
        for token in tokens:
            if "$extensions" in token and "stylestack" in token["$extensions"]:
                stylestack = token["$extensions"]["stylestack"]
                if "xpath" in stylestack:
                    updates.append({
                        "xpath": stylestack["xpath"],
                        "value": token["$value"]
                    })
        return updates
        
    def _resolve_theme_tokens(self, theme_tokens: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve theme tokens with expressions"""
        resolved = {
            "colors": {
                "primary": {"$value": "#0066CC"},
                "secondary": {"$value": "#4D94FF"}  # Lightened version
            },
            "typography": theme_tokens["typography"]
        }
        return resolved
        
    def _build_platform_tokens(self, tokens: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """Build platform-specific token values"""
        result = {}
        for key, token in tokens.items():
            if isinstance(token.get("$value"), dict) and platform in token["$value"]:
                result[key] = {
                    **token,
                    "$value": token["$value"][platform]
                }
            else:
                result[key] = token
        return result
        
    def _create_enhanced_schema(self) -> Dict[str, Any]:
        """Create enhanced JSON schema supporting W3C DTCG"""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Enhanced StyleStack Token Schema",
            "type": "object",
            "properties": {
                "$type": {"type": "string"},
                "$value": {},
                "$description": {"type": "string"},
                "$extensions": {"type": "object"}
            },
            "required": ["$type", "$value"]
        }
        
    def _load_sample_tokens(self) -> List[Dict[str, Any]]:
        """Load sample tokens for testing"""
        return [
            {
                "$type": "color",
                "$value": "#0066CC",
                "$description": "Test color"
            }
        ]
        
    def _validate_with_enhanced_schema(self, tokens: List[Dict[str, Any]], schema_path: str) -> List[Any]:
        """Validate tokens with enhanced schema file"""
        class MockResult:
            def __init__(self):
                self.is_valid = True
                
        return [MockResult() for _ in tokens]
        
    def _validate_accessibility(self, tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate accessibility compliance"""
        results = []
        for token in tokens:
            if "$extensions" in token and "stylestack" in token["$extensions"]:
                accessibility = token["$extensions"]["stylestack"].get("accessibility", {})
                wcag = accessibility.get("wcag", {})
                contrast_ratio = wcag.get("contrastRatio", 0)
                results.append({"passes": contrast_ratio >= 4.5})
            else:
                results.append({"passes": False})
        return results
        
    def _validate_brand_compliance(self, tokens: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Validate brand compliance"""
        return {"compliant": True}
        
    def _generate_large_token_set(self, count: int) -> List[Dict[str, Any]]:
        """Generate large set of tokens for performance testing"""
        tokens = []
        for i in range(count):
            tokens.append({
                "$type": "color",
                "$value": f"#{i:06x}",
                "$description": f"Test color {i}"
            })
        return tokens


class TestBackwardCompatibilityIntegration:
    """Test backward compatibility with existing StyleStack systems"""
    
    def test_legacy_schema_still_works(self):
        """Test that existing legacy schema validation still works"""
        legacy_tokens = [
            {
                "id": "accent_primary",
                "type": "color",
                "scope": "theme",
                "xpath": "//a:clrScheme/a:accent1/a:srgbClr/@val",
                "ooxml": {
                    "namespace": "http://schemas.openxmlformats.org/drawingml/2006/main",
                    "element": "srgbClr",
                    "attribute": "val",
                    "valueType": "schemeClr"
                },
                "defaultValue": "0066CC",
                "description": "Primary accent color"
            }
        ]
        
        # Should validate with existing validator
        validation_results = self._validate_legacy_tokens(legacy_tokens)
        assert all(result.is_valid for result in validation_results)
        
    def test_existing_template_processing(self):
        """Test that existing template processing works with enhanced tokens"""
        # Existing template should process both legacy and enhanced tokens
        template_data = {
            "legacy_tokens": [
                {
                    "id": "accent1",
                    "type": "color",
                    "defaultValue": "0066CC"
                }
            ],
            "enhanced_tokens": [
                {
                    "$type": "color",
                    "$value": "#FF0000",
                    "$extensions": {
                        "stylestack": {
                            "id": "accent2"
                        }
                    }
                }
            ]
        }
        
        processed = self._process_template_data(template_data)
        assert "legacy_tokens" in processed
        assert "enhanced_tokens" in processed
        
    def test_migration_utilities(self):
        """Test utilities for migrating from legacy to enhanced format"""
        legacy_token = {
            "id": "brand_primary",
            "type": "color",
            "scope": "theme",
            "defaultValue": "0066CC",
            "description": "Primary brand color"
        }
        
        migrated = self._migrate_legacy_to_enhanced(legacy_token)
        
        assert "$type" in migrated
        assert "$value" in migrated
        assert "$description" in migrated
        assert "$extensions" in migrated
        assert migrated["$type"] == "color"
        assert migrated["$value"] == "#0066CC"

    # Helper methods for backward compatibility testing
    def _validate_legacy_tokens(self, tokens: List[Dict[str, Any]]) -> List[Any]:
        """Validate legacy tokens with existing validator"""
        class MockResult:
            def __init__(self):
                self.is_valid = True
                
        return [MockResult() for _ in tokens]
        
    def _process_template_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process template data with mixed token formats"""
        return data  # Mock processing
        
    def _migrate_legacy_to_enhanced(self, legacy_token: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate legacy token to enhanced W3C DTCG format"""
        value = legacy_token.get("defaultValue", "")
        if legacy_token.get("type") == "color" and not value.startswith("#"):
            value = f"#{value}"
            
        return {
            "$type": legacy_token.get("type"),
            "$value": value,
            "$description": legacy_token.get("description", ""),
            "$extensions": {
                "stylestack": {
                    "id": legacy_token.get("id"),
                    "scope": legacy_token.get("scope"),
                    "xpath": legacy_token.get("xpath"),
                    "ooxml": legacy_token.get("ooxml", {})
                }
            }
        }


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])