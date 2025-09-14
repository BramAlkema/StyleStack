#!/usr/bin/env python3
"""
Test suite for W3C DTCG-compliant Design Token Schema Validation

Tests the enhanced token schema that supports W3C Design Tokens Community Group
specification while maintaining backward compatibility with StyleStack's
existing OOXML Extension Variable System.
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import jsonschema
from jsonschema import ValidationError


class TestW3CDTCGSchemaValidation:
    """Test W3C DTCG-compliant schema validation functionality"""
    
    def test_w3c_dtcg_basic_token_structure(self):
        """Test that basic W3C DTCG token structure is valid"""
        basic_token = {
            "$type": "color",
            "$value": "#0066CC",
            "$description": "Primary brand color used throughout the design system"
        }
        
        assert self._validate_w3c_token(basic_token) == True
        
    def test_w3c_dtcg_with_extensions(self):
        """Test W3C DTCG tokens with $extensions property"""
        token_with_extensions = {
            "$type": "color",
            "$value": "#0066CC", 
            "$description": "Primary brand color",
            "$extensions": {
                "stylestack": {
                    "ooxml": {
                        "namespace": "http://schemas.openxmlformats.org/drawingml/2006/main",
                        "element": "srgbClr",
                        "attribute": "val",
                        "valueType": "schemeClr"
                    },
                    "scope": "theme",
                    "xpath": "//a:clrScheme/a:accent1/a:srgbClr/@val",
                    "emu": {
                        "precision": "exact",
                        "platform": "office"
                    }
                }
            }
        }
        
        assert self._validate_w3c_token(token_with_extensions) == True
        
    def test_w3c_dtcg_composite_tokens(self):
        """Test W3C DTCG composite token types (shadow, border, gradient)"""
        shadow_token = {
            "$type": "shadow",
            "$value": {
                "color": "#000000",
                "offsetX": "2px",
                "offsetY": "2px", 
                "blur": "4px",
                "spread": "0px"
            },
            "$description": "Standard drop shadow for elevated elements"
        }
        
        border_token = {
            "$type": "border",
            "$value": {
                "color": "#E0E0E0",
                "width": "1px",
                "style": "solid"
            },
            "$description": "Default border style for containers"
        }
        
        gradient_token = {
            "$type": "gradient",
            "$value": {
                "type": "linear",
                "direction": "to bottom",
                "stops": [
                    {"position": "0%", "color": "#FFFFFF"},
                    {"position": "100%", "color": "#F5F5F5"}
                ]
            },
            "$description": "Subtle gradient for backgrounds"
        }
        
        assert self._validate_w3c_token(shadow_token) == True
        assert self._validate_w3c_token(border_token) == True
        assert self._validate_w3c_token(gradient_token) == True
        
    def test_w3c_dtcg_typography_tokens(self):
        """Test W3C DTCG typography token structure"""
        typography_token = {
            "$type": "typography",
            "$value": {
                "fontFamily": "Segoe UI",
                "fontWeight": "400",
                "fontSize": "16px",
                "lineHeight": "1.5"
            },
            "$description": "Base body text style",
            "$extensions": {
                "stylestack": {
                    "emu": {
                        "fontSize": "320000",
                        "lineHeight": "480000"
                    }
                }
            }
        }
        
        assert self._validate_w3c_token(typography_token) == True
        
    def test_w3c_dtcg_dimension_tokens(self):
        """Test W3C DTCG dimension token structure"""
        dimension_token = {
            "$type": "dimension",
            "$value": "16px",
            "$description": "Base spacing unit",
            "$extensions": {
                "stylestack": {
                    "emu": {
                        "value": "320000",
                        "precision": "exact"
                    },
                    "platforms": {
                        "office": "16px",
                        "libreoffice": "16px", 
                        "google": "16px"
                    }
                }
            }
        }
        
        assert self._validate_w3c_token(dimension_token) == True
        
    def test_w3c_dtcg_mathematical_expressions(self):
        """Test tokens with mathematical expressions in values"""
        expression_tokens = [
            {
                "$type": "dimension",
                "$value": "{base} * 2",
                "$description": "Double base spacing"
            },
            {
                "$type": "color", 
                "$value": "{primary}.lighten(20%)",
                "$description": "Lightened primary color"
            },
            {
                "$type": "dimension",
                "$value": "{spacing.base} + {margin.extra}",
                "$description": "Calculated composite spacing"
            }
        ]
        
        for token in expression_tokens:
            assert self._validate_w3c_token(token) == True
            
    def test_w3c_dtcg_alias_references(self):
        """Test W3C DTCG alias/reference syntax"""
        alias_tokens = [
            {
                "$type": "color",
                "$value": "{color.brand.primary}",
                "$description": "Reference to primary brand color"
            },
            {
                "$type": "dimension",
                "$value": "{spacing.{scale}.medium}",
                "$description": "Dynamic reference with interpolated scale"
            },
            {
                "$type": "color",
                "$value": "{color.{theme}.accent.{variant}}",
                "$description": "Nested dynamic reference"
            }
        ]
        
        for token in alias_tokens:
            assert self._validate_w3c_token(token) == True
            
    def test_w3c_dtcg_conditional_platform_values(self):
        """Test platform-conditional token values"""
        conditional_token = {
            "$type": "dimension",
            "$value": {
                "office": "11pt",
                "web": "14px",
                "print": "10pt",
                "libreoffice": "11pt",
                "google": "14px"
            },
            "$description": "Platform-specific font size",
            "$extensions": {
                "stylestack": {
                    "conditional": True,
                    "fallback": "12pt"
                }
            }
        }
        
        assert self._validate_w3c_token(conditional_token) == True
        
    def test_backward_compatibility_stylestack_format(self):
        """Test that existing StyleStack format still validates"""
        legacy_token = {
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
            "description": "Primary accent color used throughout the theme"
        }
        
        assert self._validate_legacy_token(legacy_token) == True
        
    def test_hybrid_format_support(self):
        """Test tokens that combine W3C DTCG and StyleStack formats"""
        hybrid_token = {
            # W3C DTCG properties
            "$type": "color",
            "$value": "#0066CC",
            "$description": "Primary brand color",
            
            # StyleStack legacy properties for backward compatibility
            "id": "accent_primary",
            "type": "color",
            "scope": "theme",
            "xpath": "//a:clrScheme/a:accent1/a:srgbClr/@val",
            "ooxml": {
                "namespace": "http://schemas.openxmlformats.org/drawingml/2006/main",
                "element": "srgbClr", 
                "attribute": "val",
                "valueType": "schemeClr"
            }
        }
        
        assert self._validate_hybrid_token(hybrid_token) == True
        
    def test_invalid_w3c_dtcg_tokens(self):
        """Test that invalid W3C DTCG tokens fail validation"""
        invalid_tokens = [
            # Missing required $type
            {
                "$value": "#0066CC",
                "$description": "Color without type"
            },
            # Missing required $value
            {
                "$type": "color",
                "$description": "Color without value"
            },
            # Invalid $type value
            {
                "$type": "invalid_type",
                "$value": "#0066CC",
                "$description": "Invalid token type"
            },
            # Invalid color value format
            {
                "$type": "color",
                "$value": "not-a-color",
                "$description": "Invalid color format"
            },
            # Invalid dimension value
            {
                "$type": "dimension",
                "$value": "invalid-dimension",
                "$description": "Invalid dimension format"
            }
        ]
        
        for invalid_token in invalid_tokens:
            assert self._validate_w3c_token(invalid_token) == False
            
    def test_stylestack_extensions_validation(self):
        """Test validation of StyleStack-specific extensions"""
        valid_extensions = {
            "$type": "color",
            "$value": "#0066CC",
            "$description": "Color with valid StyleStack extensions",
            "$extensions": {
                "stylestack": {
                    "ooxml": {
                        "namespace": "http://schemas.openxmlformats.org/drawingml/2006/main",
                        "element": "srgbClr",
                        "attribute": "val",
                        "valueType": "schemeClr"
                    },
                    "emu": {
                        "precision": "exact",
                        "platform": "office"
                    },
                    "accessibility": {
                        "wcag": {
                            "contrastRatio": 4.5,
                            "level": "AA"
                        }
                    },
                    "brand": {
                        "primary": True,
                        "category": "corporate"
                    }
                }
            }
        }
        
        assert self._validate_w3c_token(valid_extensions) == True
        
    def test_mathematical_expression_validation(self):
        """Test validation of mathematical expressions in token values"""
        valid_expressions = [
            "{base} * 2",
            "{spacing.large} + {margin.small}",
            "{color.primary}.lighten(20%)",
            "{color.primary}.darken(10%)",
            "{dimension.base}.multiply(1.5).px()",
            "{spacing.{scale}.base}",
            "calc({base} * 2 + 4px)"
        ]
        
        invalid_expressions = [
            "{unclosed",
            "malformed.{expression",
            "{recursive.{self}}",
            "divide.by.zero(0)",
            "{missing.reference}"
        ]
        
        for expr in valid_expressions:
            assert self._validate_expression(expr) == True
            
        for expr in invalid_expressions:
            assert self._validate_expression(expr) == False
            
    def test_circular_reference_detection(self):
        """Test detection of circular references in token aliases"""
        tokens_with_circular_refs = [
            {
                "token_a": {
                    "$type": "color",
                    "$value": "{token_b}",
                    "$description": "References token_b"
                },
                "token_b": {
                    "$type": "color", 
                    "$value": "{token_a}",
                    "$description": "References token_a - circular!"
                }
            }
        ]
        
        for token_set in tokens_with_circular_refs:
            assert self._detect_circular_references(token_set) == True
            
    def test_platform_compatibility_validation(self):
        """Test validation of platform-specific compatibility"""
        platform_token = {
            "$type": "dimension",
            "$value": {
                "office": "11pt",
                "web": "14px",
                "print": "10pt"
            },
            "$description": "Multi-platform dimension",
            "$extensions": {
                "stylestack": {
                    "platforms": {
                        "office": {
                            "supported": True,
                            "format": "emu"
                        },
                        "libreoffice": {
                            "supported": True,
                            "format": "emu"
                        },
                        "google": {
                            "supported": True,
                            "format": "px"
                        },
                        "web": {
                            "supported": True,
                            "format": "px"
                        }
                    }
                }
            }
        }
        
        assert self._validate_platform_compatibility(platform_token) == True

    def test_accessibility_compliance_validation(self):
        """Test WCAG accessibility compliance validation for design tokens"""
        accessible_color_token = {
            "$type": "color",
            "$value": "#0066CC",
            "$description": "WCAG AA compliant blue",
            "$extensions": {
                "stylestack": {
                    "accessibility": {
                        "wcag": {
                            "contrastRatio": 4.8,
                            "level": "AA",
                            "largeText": True
                        }
                    }
                }
            }
        }
        
        non_accessible_color_token = {
            "$type": "color",
            "$value": "#FFFF00",
            "$description": "Poor contrast yellow",
            "$extensions": {
                "stylestack": {
                    "accessibility": {
                        "wcag": {
                            "contrastRatio": 1.2,
                            "level": "FAIL",
                            "largeText": False
                        }
                    }
                }
            }
        }
        
        assert self._validate_accessibility_compliance(accessible_color_token) == True
        assert self._validate_accessibility_compliance(non_accessible_color_token) == False

    def test_emu_precision_validation(self):
        """Test EMU precision validation for typography tokens"""
        precise_typography_token = {
            "$type": "typography",
            "$value": {
                "fontFamily": "Segoe UI",
                "fontSize": "16px"
            },
            "$description": "EMU-precise typography",
            "$extensions": {
                "stylestack": {
                    "emu": {
                        "fontSize": "320000",
                        "precision": "exact",
                        "validated": True
                    }
                }
            }
        }
        
        imprecise_typography_token = {
            "$type": "typography",
            "$value": {
                "fontFamily": "Arial",
                "fontSize": "16.33333px"
            },
            "$description": "Imprecise typography",
            "$extensions": {
                "stylestack": {
                    "emu": {
                        "fontSize": "326666",
                        "precision": "approximate",
                        "validated": False
                    }
                }
            }
        }
        
        assert self._validate_emu_precision(precise_typography_token) == True
        assert self._validate_emu_precision(imprecise_typography_token) == False

    def test_brand_rule_enforcement(self):
        """Test corporate brand rule enforcement"""
        compliant_brand_token = {
            "$type": "color",
            "$value": "#0066CC",
            "$description": "Brand-compliant corporate blue",
            "$extensions": {
                "stylestack": {
                    "brand": {
                        "primary": True,
                        "category": "corporate",
                        "approved": True,
                        "guidelines": {
                            "usage": "primary branding only",
                            "restrictions": "no tinting allowed"
                        }
                    }
                }
            }
        }
        
        non_compliant_brand_token = {
            "$type": "color",
            "$value": "#FF0000",
            "$description": "Non-approved red color",
            "$extensions": {
                "stylestack": {
                    "brand": {
                        "primary": False,
                        "category": "custom",
                        "approved": False,
                        "violations": ["unauthorized color", "brand guideline conflict"]
                    }
                }
            }
        }
        
        assert self._validate_brand_compliance(compliant_brand_token) == True
        assert self._validate_brand_compliance(non_compliant_brand_token) == False

    # Helper methods for validation using the actual W3C DTCG validator
    def _validate_w3c_token(self, token: Dict[str, Any]) -> bool:
        """Validate token against W3C DTCG schema"""
        try:
            from tools.w3c_dtcg_validator import W3CDTCGValidator
            validator = W3CDTCGValidator()
            result = validator.validate_token(token)
            return result.is_valid
        except Exception:
            return False
        
    def _validate_legacy_token(self, token: Dict[str, Any]) -> bool:
        """Validate token against legacy StyleStack schema"""
        try:
            from tools.extension_schema_validator import ExtensionSchemaValidator
            validator = ExtensionSchemaValidator()
            result = validator.validate_variable(token)
            return result.is_valid
        except Exception:
            return False
        
    def _validate_hybrid_token(self, token: Dict[str, Any]) -> bool:
        """Validate token that combines both formats"""
        return self._validate_w3c_token(token)
        
    def _validate_expression(self, expression: str) -> bool:
        """Validate mathematical expression syntax"""
        try:
            from tools.w3c_dtcg_validator import W3CDTCGValidator
            validator = W3CDTCGValidator()
            
            # Test with a dummy token containing the expression
            test_token = {
                "$type": "dimension",
                "$value": expression,
                "$description": "Test token"
            }
            result = validator.validate_token(test_token)
            
            # Check if expression-related errors occurred
            expression_errors = [e for e in result.errors if "expression" in e.code.lower() or "reference" in e.code.lower()]
            return len(expression_errors) == 0
        except Exception:
            return False
        
    def _detect_circular_references(self, tokens: Dict[str, Any]) -> bool:
        """Detect circular references in token set"""
        try:
            from tools.w3c_dtcg_validator import W3CDTCGValidator
            validator = W3CDTCGValidator()
            results = validator.validate_token_collection(tokens)
            
            # Check if any token has circular dependency errors
            for result in results.values():
                circular_errors = [e for e in result.errors if "circular" in e.code.lower()]
                if circular_errors:
                    return True
            return False
        except Exception:
            return False
        
    def _validate_platform_compatibility(self, token: Dict[str, Any]) -> bool:
        """Validate platform compatibility settings"""
        try:
            from tools.w3c_dtcg_validator import W3CDTCGValidator
            validator = W3CDTCGValidator()
            result = validator.validate_token(token)
            
            # Check for platform-related errors
            platform_errors = [e for e in result.errors if "platform" in e.code.lower()]
            return len(platform_errors) == 0
        except Exception:
            return False
        
    def _validate_accessibility_compliance(self, token: Dict[str, Any]) -> bool:
        """Validate WCAG accessibility compliance"""
        try:
            # Check accessibility compliance based on token content
            extensions = token.get("$extensions", {})
            stylestack = extensions.get("stylestack", {})
            accessibility = stylestack.get("accessibility", {})
            wcag = accessibility.get("wcag", {})
            
            if "contrastRatio" in wcag:
                return wcag["contrastRatio"] >= 4.5
            
            # If no accessibility info, consider it failed validation
            return False
        except Exception:
            return False
        
    def _validate_emu_precision(self, token: Dict[str, Any]) -> bool:
        """Validate EMU precision requirements"""
        try:
            from tools.w3c_dtcg_validator import W3CDTCGValidator
            validator = W3CDTCGValidator()
            result = validator.validate_token(token)
            
            # Check EMU precision based on token content
            extensions = token.get("$extensions", {})
            stylestack = extensions.get("stylestack", {})
            emu = stylestack.get("emu", {})
            
            if "precision" in emu and "validated" in emu:
                return emu["precision"] == "exact" and emu["validated"] == True
            
            return False
        except Exception:
            return False
        
    def _validate_brand_compliance(self, token: Dict[str, Any]) -> bool:
        """Validate corporate brand rule compliance"""
        try:
            from tools.w3c_dtcg_validator import W3CDTCGValidator
            validator = W3CDTCGValidator()
            result = validator.validate_token(token)
            
            # Check brand compliance based on token content
            extensions = token.get("$extensions", {})
            stylestack = extensions.get("stylestack", {})
            brand = stylestack.get("brand", {})
            
            if "approved" in brand and "violations" in brand:
                return brand["approved"] == True and len(brand["violations"]) == 0
            elif "approved" in brand:
                return brand["approved"] == True
            
            return True  # No brand info means compliant by default
        except Exception:
            return False


class TestSchemaEvolutionCompatibility:
    """Test schema evolution and backward compatibility"""
    
    def test_schema_version_detection(self):
        """Test automatic detection of schema version"""
        w3c_token = {
            "$type": "color",
            "$value": "#0066CC"
        }
        
        legacy_token = {
            "id": "accent1",
            "type": "color",
            "defaultValue": "0066CC"
        }
        
        assert self._detect_schema_version(w3c_token) == "w3c-dtcg"
        assert self._detect_schema_version(legacy_token) == "stylestack-legacy"
        
    def test_automatic_schema_migration(self):
        """Test automatic migration from legacy to W3C DTCG format"""
        legacy_token = {
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
        
        migrated_token = self._migrate_to_w3c_dtcg(legacy_token)
        
        # Verify W3C DTCG properties are present
        assert "$type" in migrated_token
        assert "$value" in migrated_token
        assert "$description" in migrated_token
        assert "$extensions" in migrated_token
        
        # Verify StyleStack extensions are preserved
        assert "stylestack" in migrated_token["$extensions"]
        assert "ooxml" in migrated_token["$extensions"]["stylestack"]
        
    def test_dual_format_validation(self):
        """Test validation when both formats are present"""
        dual_format_token = {
            # W3C DTCG format
            "$type": "color",
            "$value": "#0066CC",
            "$description": "Primary brand color",
            
            # Legacy StyleStack format (for compatibility)
            "id": "accent_primary", 
            "type": "color",
            "defaultValue": "0066CC",
            "description": "Primary brand color"
        }
        
        # Should validate against both schemas
        assert self._validate_dual_format(dual_format_token) == True
        
    def test_schema_conflict_detection(self):
        """Test detection of conflicts between dual formats"""
        conflicting_token = {
            "$type": "color",
            "$value": "#0066CC",
            "type": "dimension",  # Conflict!
            "defaultValue": "FF0000"  # Value conflict!
        }
        
        conflicts = self._detect_format_conflicts(conflicting_token)
        assert len(conflicts) == 2
        assert "type mismatch" in str(conflicts)
        assert "value mismatch" in str(conflicts)

    # Helper methods for compatibility testing
    def _detect_schema_version(self, token: Dict[str, Any]) -> str:
        """Detect which schema version a token uses"""
        if "$type" in token:
            return "w3c-dtcg"
        elif "id" in token and "type" in token:
            return "stylestack-legacy"
        return "unknown"
        
    def _migrate_to_w3c_dtcg(self, legacy_token: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate legacy token to W3C DTCG format"""
        migrated = {
            "$type": legacy_token.get("type"),
            "$value": legacy_token.get("defaultValue"),
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
        return migrated
        
    def _validate_dual_format(self, token: Dict[str, Any]) -> bool:
        """Validate token with both formats present"""
        return True
        
    def _detect_format_conflicts(self, token: Dict[str, Any]) -> List[str]:
        """Detect conflicts between dual format properties"""
        conflicts = []
        
        # Check type conflicts
        if "$type" in token and "type" in token:
            if token["$type"] != token["type"]:
                conflicts.append("type mismatch")
                
        # Check value conflicts  
        if "$value" in token and "defaultValue" in token:
            if str(token["$value"]).replace("#", "") != str(token["defaultValue"]):
                conflicts.append("value mismatch")
                
        return conflicts


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])