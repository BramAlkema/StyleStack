#!/usr/bin/env python3
"""
Token Integration and Production Workflow Tests

This test suite validates the integration between the Design Token System and
the JSON-to-OOXML Processing Engine with real-world production workflows.
"""

import os
import sys
import pytest
import shutil
import tempfile
import zipfile
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from multi_format_ooxml_handler import MultiFormatOOXMLHandler, OOXMLFormat
from token_integration_layer import TokenIntegrationLayer, TokenScope, TokenContext
from transaction_pipeline import TransactionPipeline, OperationType

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test fixtures path
FIXTURES_PATH = Path(__file__).parent / "fixtures"
TEMPLATES_PATH = FIXTURES_PATH / "templates"


class TestTokenIntegrationWorkflows:
    """Test token integration with realistic production workflows."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.handler = MultiFormatOOXMLHandler(enable_token_integration=True)
        self.token_layer = TokenIntegrationLayer()
        
    def teardown_method(self):
        """Clean up test environment.""" 
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_temp_copy(self, template_name: str) -> Path:
        """Create a temporary copy of a template."""
        original = TEMPLATES_PATH / template_name
        if not original.exists():
            raise FileNotFoundError(f"Template not found: {original}")
        temp_path = self.temp_dir / template_name
        shutil.copy2(original, temp_path)
        return temp_path
    
    def test_corporate_branding_token_workflow(self):
        """Test corporate branding workflow using design tokens."""
        # Arrange: Corporate branding scenario
        template_path = self._create_temp_copy("test_presentation.potx")
        
        # Define design tokens for corporate branding
        design_tokens = {
            # Brand colors
            "brand.colors.primary": "#0066CC",
            "brand.colors.secondary": "#FF6B35", 
            "brand.colors.accent": "#00A86B",
            "brand.colors.neutral": "#333333",
            "brand.colors.background": "#F8F9FA",
            
            # Typography tokens
            "brand.typography.heading.family": "Calibri Light",
            "brand.typography.heading.size": "44pt",
            "brand.typography.body.family": "Calibri",
            "brand.typography.body.size": "18pt",
            
            # Spacing tokens (in EMU)
            "brand.spacing.slide.margin": "914400",  # 1 inch
            "brand.spacing.content.padding": "457200",  # 0.5 inch
            
            # Company information
            "company.name": "TechCorp Solutions",
            "company.tagline": "Innovation Through Technology",
            "company.year": "2024"
        }
        
        # Define patches that use design tokens
        branding_patches = [
            {
                "operation": "set",
                "target": "//p:sld//a:t[text()='Sample Presentation Title']",
                "value": "{{company.name}} - {{company.tagline}}"
            },
            {
                "operation": "set",
                "target": "//a:theme//a:clrScheme//a:accent1//a:srgbClr/@val",
                "value": "{{brand.colors.primary}}"
            },
            {
                "operation": "set",
                "target": "//a:theme//a:clrScheme//a:accent2//a:srgbClr/@val", 
                "value": "{{brand.colors.secondary}}"
            },
            {
                "operation": "set",
                "target": "//a:srgbClr[@val='000000']/@val",
                "value": "{{brand.colors.neutral}}"
            },
            {
                "operation": "insert",
                "target": "//p:sld//p:spTree",
                "value": '''<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
                    <p:nvSpPr>
                        <p:cNvPr id="1000" name="Company Footer"/>
                        <p:cNvSpPr/>
                        <p:nvPr/>
                    </p:nvSpPr>
                    <p:spPr>
                        <a:xfrm>
                            <a:off x="{{brand.spacing.slide.margin}}" y="6400000"/>
                            <a:ext cx="8000000" cy="400000"/>
                        </a:xfrm>
                        <a:prstGeom prst="rect"/>
                        <a:solidFill>
                            <a:srgbClr val="{{brand.colors.background}}"/>
                        </a:solidFill>
                    </p:spPr>
                    <p:txBody>
                        <a:bodyPr/>
                        <a:lstStyle/>
                        <a:p>
                            <a:pPr algn="ctr"/>
                            <a:r>
                                <a:rPr sz="1400">
                                    <a:solidFill>
                                        <a:srgbClr val="{{brand.colors.neutral}}"/>
                                    </a:solidFill>
                                    <a:latin typeface="{{brand.typography.body.family}}"/>
                                </a:rPr>
                                <a:t>© {{company.year}} {{company.name}} - All Rights Reserved</a:t>
                            </a:r>
                        </a:p>
                    </p:txBody>
                </p:sp>''',
                "position": "append"
            }
        ]
        
        # Act: Process with token integration
        result = self.handler.process_template(
            template_path=template_path,
            patches=branding_patches,
            variables=design_tokens,
            metadata={
                "workflow": "corporate_branding",
                "token_integration": True
            }
        )
        
        # Assert: Verify successful token substitution
        assert result.success, f"Corporate branding workflow failed: {result.errors}"
        
        # Verify token substitutions in output
        output_path = Path(result.output_path)
        with zipfile.ZipFile(output_path, 'r') as zipf:
            slide_content = zipf.read("ppt/slides/slide1.xml").decode('utf-8')
            
            # Verify company information was substituted
            assert "TechCorp Solutions - Innovation Through Technology" in slide_content
            assert "© 2024 TechCorp Solutions" in slide_content
            
            # Verify color tokens were applied
            theme_content = zipf.read("ppt/theme/theme1.xml").decode('utf-8')
            assert '0066CC' in theme_content or '0066cc' in theme_content.lower()
            assert 'FF6B35' in theme_content or 'ff6b35' in theme_content.lower()
            
            # Verify spacing tokens (EMU values)
            assert '914400' in slide_content  # Margin spacing
        
        logger.info("Corporate branding token workflow test completed successfully")
    
    def test_multi_format_token_consistency(self):
        """Test token consistency across multiple OOXML formats."""
        # Arrange: Templates for different formats
        templates = {
            OOXMLFormat.POWERPOINT: self._create_temp_copy("test_presentation.potx"),
            OOXMLFormat.WORD: self._create_temp_copy("test_document.dotx"),
            OOXMLFormat.EXCEL: self._create_temp_copy("test_workbook.xltx")
        }
        
        # Define consistent design tokens
        shared_tokens = {
            "project.name": "Q4 Business Review",
            "project.date": "December 2024",
            "project.status": "Final",
            "brand.color.primary": "2F5496",
            "brand.color.secondary": "70AD47",
            "brand.font.heading": "Calibri Light",
            "brand.font.body": "Calibri"
        }
        
        # Format-specific patches using shared tokens
        format_patches = {
            OOXMLFormat.POWERPOINT: [
                {
                    "operation": "set",
                    "target": "//p:sld//a:t[text()='Sample Presentation Title']",
                    "value": "{{project.name}} - {{project.status}}"
                },
                {
                    "operation": "set",
                    "target": "//a:srgbClr[@val='000000']/@val",
                    "value": "{{brand.color.primary}}"
                }
            ],
            OOXMLFormat.WORD: [
                {
                    "operation": "set",
                    "target": "//w:t[contains(text(), 'Sample Document Title')]",
                    "value": "{{project.name}} Document - {{project.date}}"
                },
                {
                    "operation": "set",
                    "target": "//w:color[@w:val='2F5496']/@w:val",
                    "value": "{{brand.color.secondary}}"
                }
            ],
            OOXMLFormat.EXCEL: [
                {
                    "operation": "set",
                    "target": "//worksheet//c[@r='A1']/v",
                    "value": "{{project.name}} - {{project.status}}"
                }
            ]
        }
        
        # Act: Process all formats with same token set
        results = {}
        for format_type, template_path in templates.items():
            patches = format_patches[format_type]
            
            result = self.handler.process_template(
                template_path=template_path,
                patches=patches,
                variables=shared_tokens,
                metadata={
                    "format": format_type.value,
                    "multi_format_test": True
                }
            )
            results[format_type] = result
        
        # Assert: All formats should process successfully
        for format_type, result in results.items():
            assert result.success, f"{format_type.value} processing failed: {result.errors}"
        
        # Verify token consistency across formats
        expected_title = "Q4 Business Review - Final"
        
        # PowerPoint verification
        ppt_path = Path(results[OOXMLFormat.POWERPOINT].output_path)
        with zipfile.ZipFile(ppt_path, 'r') as zipf:
            slide_content = zipf.read("ppt/slides/slide1.xml").decode('utf-8')
            assert expected_title in slide_content
            assert '2F5496' in slide_content or '2f5496' in slide_content.lower()
        
        # Word verification 
        word_path = Path(results[OOXMLFormat.WORD].output_path)
        with zipfile.ZipFile(word_path, 'r') as zipf:
            doc_content = zipf.read("word/document.xml").decode('utf-8')
            assert "Q4 Business Review Document - December 2024" in doc_content
            assert '70AD47' in doc_content or '70ad47' in doc_content.lower()
        
        # Excel verification
        excel_path = Path(results[OOXMLFormat.EXCEL].output_path)
        with zipfile.ZipFile(excel_path, 'r') as zipf:
            sheet_content = zipf.read("xl/worksheets/sheet1.xml").decode('utf-8')
            assert expected_title in sheet_content
        
        logger.info("Multi-format token consistency test completed successfully")
    
    def test_production_deployment_with_token_validation(self):
        """Test production deployment workflow with token validation."""
        # Arrange: Production scenario with validation
        template_path = self._create_temp_copy("test_presentation.potx")
        
        # Production token configuration with validation rules
        production_config = {
            "tokens": {
                "deployment.environment": "production",
                "deployment.version": "v2.1.0",
                "deployment.build": "build-2024-001",
                "content.title": "Production Release Notes",
                "content.subtitle": "System Updates and Features",
                "branding.approved_colors": ["0066CC", "FF6B35", "00A86B"],
                "branding.primary_color": "0066CC"
            },
            "validation_rules": {
                "required_tokens": [
                    "deployment.environment", 
                    "deployment.version",
                    "content.title"
                ],
                "color_validation": {
                    "allowed_colors": ["0066CC", "FF6B35", "00A86B", "333333"],
                    "format": "hex"
                }
            }
        }
        
        # Patches for production deployment
        production_patches = [
            {
                "operation": "set",
                "target": "//p:sld//a:t[text()='Sample Presentation Title']",
                "value": "{{content.title}} {{deployment.version}}"
            },
            {
                "operation": "set",
                "target": "//a:srgbClr[@val='000000']/@val",
                "value": "{{branding.primary_color}}"
            },
            {
                "operation": "insert",
                "target": "//p:sld//p:spTree",
                "value": '''<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
                    <p:nvSpPr>
                        <p:cNvPr id="2000" name="Deployment Info"/>
                        <p:cNvSpPr/>
                        <p:nvPr/>
                    </p:nvSpPr>
                    <p:spPr/>
                    <p:txBody>
                        <a:bodyPr/>
                        <a:lstStyle/>
                        <a:p>
                            <a:r>
                                <a:rPr>
                                    <a:solidFill>
                                        <a:srgbClr val="333333"/>
                                    </a:solidFill>
                                </a:rPr>
                                <a:t>Environment: {{deployment.environment}} | Build: {{deployment.build}}</a:t>
                            </a:r>
                        </a:p>
                    </p:txBody>
                </p:sp>''',
                "position": "append"
            }
        ]
        
        # Act: Process with production configuration using transaction pipeline
        with TransactionPipeline(enable_audit_trail=True) as pipeline:
            with pipeline.transaction() as transaction:
                # Step 1: Validate token configuration
                validation_result = self._validate_token_configuration(
                    production_config["tokens"], 
                    production_config["validation_rules"]
                )
                
                if not validation_result["valid"]:
                    raise ValueError(f"Token validation failed: {validation_result['errors']}")
                
                # Step 2: Backup original template
                transaction.add_operation(
                    OperationType.BACKUP_STATE,
                    {"files_to_backup": [str(template_path)]}
                )
                
                # Step 3: Apply production patches
                transaction.add_operation(
                    OperationType.APPLY_PATCHES,
                    {
                        "template_path": str(template_path),
                        "patches": production_patches,
                        "variables": production_config["tokens"]
                    }
                )
                
                # Step 4: Validate output structure
                transaction.add_operation(
                    OperationType.VALIDATE_STRUCTURE,
                    {"template_path": str(template_path)}
                )
                
                result = transaction.commit()
        
        # Assert: Production deployment should succeed
        assert result.success, f"Production deployment failed: {result.error_summary}"
        
        # Verify production-specific content
        with zipfile.ZipFile(template_path, 'r') as zipf:
            slide_content = zipf.read("ppt/slides/slide1.xml").decode('utf-8')
            
            # Verify version and title
            assert "Production Release Notes v2.1.0" in slide_content
            assert "Environment: production" in slide_content
            assert "Build: build-2024-001" in slide_content
            
            # Verify approved color was applied
            assert '0066CC' in slide_content or '0066cc' in slide_content.lower()
        
        # Verify audit trail
        audit_stats = pipeline.get_performance_statistics()
        assert audit_stats["transactions_committed"] == 1
        assert len(pipeline.audit_trail) > 0
        
        logger.info("Production deployment with token validation test completed successfully")
    
    def test_error_handling_invalid_tokens(self):
        """Test error handling with invalid or missing tokens.""" 
        # Arrange: Template with patches that reference invalid tokens
        template_path = self._create_temp_copy("test_presentation.potx")
        
        patches_with_invalid_tokens = [
            {
                "operation": "set",
                "target": "//p:sld//a:t[text()='Sample Presentation Title']",
                "value": "{{invalid.token.that.does.not.exist}}"
            },
            {
                "operation": "set",
                "target": "//a:srgbClr[@val='000000']/@val",
                "value": "{{another.missing.token}}"
            },
            {
                "operation": "set", 
                "target": "//p:sld//a:t[text()='Sample Presentation Title']",
                "value": "{{valid.token}}"  # This one should work
            }
        ]
        
        # Provide incomplete token set (missing some referenced tokens)
        incomplete_tokens = {
            "valid.token": "This Token Works",
            "present.token": "I am here"
            # Missing: invalid.token.that.does.not.exist, another.missing.token
        }
        
        # Act: Process with missing tokens (should handle gracefully)
        result = self.handler.process_template(
            template_path=template_path,
            patches=patches_with_invalid_tokens,
            variables=incomplete_tokens,
            metadata={"error_handling_test": True}
        )
        
        # Assert: Should handle missing tokens gracefully
        # Result may succeed with warnings, or fail with informative error
        if result.success:
            # If processing succeeded, verify that valid tokens were applied
            output_path = Path(result.output_path)
            with zipfile.ZipFile(output_path, 'r') as zipf:
                slide_content = zipf.read("ppt/slides/slide1.xml").decode('utf-8')
                # The valid token should have been substituted
                assert "This Token Works" in slide_content
        else:
            # If processing failed, should have informative error messages
            assert len(result.errors) > 0
            error_message = ' '.join(result.errors).lower()
            assert "token" in error_message or "variable" in error_message
        
        # Should have warnings about missing tokens
        if hasattr(result, 'warnings') and result.warnings:
            warning_text = ' '.join(result.warnings).lower()
            assert "token" in warning_text or "variable" in warning_text
        
        logger.info("Error handling for invalid tokens test completed")
    
    def test_token_formula_evaluation_workflow(self):
        """Test token formula evaluation in production workflow."""
        # Arrange: Template with formula-based tokens
        template_path = self._create_temp_copy("test_presentation.potx")
        
        # Define tokens that include formulas
        formula_tokens = {
            # Basic values
            "slide.width.inches": "10",
            "slide.height.inches": "7.5", 
            "margin.inches": "0.5",
            
            # Formula-based calculations (EMU values)
            "slide.width.emu": "={{slide.width.inches}} * 914400",  # Convert inches to EMU
            "slide.height.emu": "={{slide.height.inches}} * 914400",
            "margin.emu": "={{margin.inches}} * 914400",
            
            # Color calculations
            "brand.primary.red": "0",
            "brand.primary.green": "102", 
            "brand.primary.blue": "204",
            "brand.primary.hex": "={{brand.primary.red:02X}}{{brand.primary.green:02X}}{{brand.primary.blue:02X}}",
            
            # Text formatting
            "company.name": "TechCorp",
            "department": "Engineering",
            "full.title": "={{company.name}} {{department}} Presentation"
        }
        
        patches_with_formulas = [
            {
                "operation": "set",
                "target": "//p:presentation//p:sldSz/@cx",
                "value": "{{slide.width.emu}}"
            },
            {
                "operation": "set",
                "target": "//p:presentation//p:sldSz/@cy", 
                "value": "{{slide.height.emu}}"
            },
            {
                "operation": "set",
                "target": "//p:sld//a:t[text()='Sample Presentation Title']",
                "value": "{{full.title}}"
            },
            {
                "operation": "set",
                "target": "//a:srgbClr[@val='000000']/@val",
                "value": "{{brand.primary.hex}}"
            }
        ]
        
        # Act: Process with formula evaluation
        result = self.handler.process_template(
            template_path=template_path,
            patches=patches_with_formulas,
            variables=formula_tokens,
            metadata={"formula_evaluation": True}
        )
        
        # Assert: Formula evaluation should work
        assert result.success, f"Formula evaluation workflow failed: {result.errors}"
        
        # Verify calculated values were applied
        output_path = Path(result.output_path)
        with zipfile.ZipFile(output_path, 'r') as zipf:
            pres_content = zipf.read("ppt/presentation.xml").decode('utf-8')
            slide_content = zipf.read("ppt/slides/slide1.xml").decode('utf-8')
            
            # Verify EMU calculations (10 inches = 9144000 EMU, 7.5 inches = 6858000 EMU)
            assert 'cx="9144000"' in pres_content
            assert 'cy="6858000"' in pres_content
            
            # Verify text formula
            assert "TechCorp Engineering Presentation" in slide_content
            
            # Verify color formula (RGB 0,102,204 = hex 0066CC)
            assert '0066CC' in slide_content or '0066cc' in slide_content.lower()
        
        logger.info("Token formula evaluation workflow test completed successfully")
    
    def _validate_token_configuration(self, tokens: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validate token configuration against rules.""" 
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check required tokens
        if "required_tokens" in rules:
            for required_token in rules["required_tokens"]:
                if required_token not in tokens:
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"Required token missing: {required_token}")
        
        # Check color validation
        if "color_validation" in rules:
            color_rules = rules["color_validation"]
            allowed_colors = color_rules.get("allowed_colors", [])
            
            for token_name, token_value in tokens.items():
                if "color" in token_name.lower():
                    if isinstance(token_value, str) and len(token_value) == 6:
                        # Assume hex color
                        if token_value.upper() not in [c.upper() for c in allowed_colors]:
                            validation_result["warnings"].append(f"Color token {token_name} uses non-approved color: {token_value}")
        
        return validation_result


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])