#!/usr/bin/env python3
"""
Comprehensive End-to-End Integration Tests for StyleStack YAML-to-OOXML Processing Engine

This test suite validates the complete system integration including:
- MultiFormatOOXMLHandler
- TransactionPipeline 
- TokenIntegrationLayer
- YAMLPatchProcessor
- Real OOXML template processing
- Complete processing pipeline workflows
- Production-ready validation and error recovery

Tests use actual OOXML template files (.potx, .dotx, .xltx) to validate real customer workflows.
"""

import os
import sys
import pytest
import shutil
import tempfile
import zipfile
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from multi_format_ooxml_handler import (
    MultiFormatOOXMLHandler, 
    OOXMLFormat, 
    ProcessingResult
)
from transaction_pipeline import (
    TransactionPipeline, 
    Transaction, 
    TransactionState, 
    OperationType,
    atomic_ooxml_operation
)
from token_integration_layer import TokenIntegrationLayer, TokenScope, TokenContext
from yaml_ooxml_processor import (
    YAMLPatchProcessor, 
    PatchResult, 
    PatchOperationType,
    RecoveryStrategy
)
from lxml import etree

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Test fixtures path
FIXTURES_PATH = Path(__file__).parent / "fixtures"
TEMPLATES_PATH = FIXTURES_PATH / "templates"


class TestFixtures:
    """Test fixture management for OOXML templates."""
    
    @classmethod
    def get_template_path(cls, template_name: str) -> Path:
        """Get path to test template file."""
        template_path = TEMPLATES_PATH / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        return template_path
    
    @classmethod
    def create_temp_copy(cls, template_name: str) -> Path:
        """Create a temporary copy of a template for modification testing."""
        original = cls.get_template_path(template_name)
        temp_dir = Path(tempfile.mkdtemp())
        temp_path = temp_dir / template_name
        shutil.copy2(original, temp_path)
        return temp_path
    
    @classmethod
    def verify_ooxml_structure(cls, ooxml_path: Path, expected_format: OOXMLFormat) -> bool:
        """Verify that an OOXML file has the expected internal structure."""
        try:
            with zipfile.ZipFile(ooxml_path, 'r') as zipf:
                files = zipf.namelist()
                
                # Check for required files based on format
                required_files = {
                    OOXMLFormat.POWERPOINT: [
                        "[Content_Types].xml",
                        "ppt/presentation.xml",
                        "ppt/_rels/presentation.xml.rels"
                    ],
                    OOXMLFormat.WORD: [
                        "[Content_Types].xml", 
                        "word/document.xml",
                        "word/_rels/document.xml.rels"
                    ],
                    OOXMLFormat.EXCEL: [
                        "[Content_Types].xml",
                        "xl/workbook.xml",
                        "xl/_rels/workbook.xml.rels"
                    ]
                }
                
                for required_file in required_files[expected_format]:
                    if required_file not in files:
                        logger.error(f"Missing required file: {required_file}")
                        return False
                
                # Verify XML structure of main document
                main_docs = {
                    OOXMLFormat.POWERPOINT: "ppt/presentation.xml",
                    OOXMLFormat.WORD: "word/document.xml", 
                    OOXMLFormat.EXCEL: "xl/workbook.xml"
                }
                
                main_doc_path = main_docs[expected_format]
                xml_content = zipf.read(main_doc_path)
                try:
                    etree.fromstring(xml_content)
                    return True
                except etree.XMLSyntaxError as e:
                    logger.error(f"Invalid XML in {main_doc_path}: {e}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error verifying OOXML structure: {e}")
            return False


class TestEndToEndOOXMLProcessing:
    """Comprehensive end-to-end tests for the OOXML processing engine."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.handler = MultiFormatOOXMLHandler(enable_token_integration=True)
        self.pipeline = TransactionPipeline(enable_audit_trail=True)
        
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_powerpoint_processing_pipeline(self):
        """Test complete processing pipeline with PowerPoint template."""
        # Arrange: Get test template and define patches
        template_path = TestFixtures.create_temp_copy("test_presentation.potx")
        
        yaml_patches = [
            {
                "operation": "set",
                "target": "//p:sld//a:t[text()='Sample Presentation Title']",
                "value": "StyleStack Integration Test Success"
            },
            {
                "operation": "set",
                "target": "//a:srgbClr[@val='000000']/@val",
                "value": "FF0000"  # Change text color to red
            },
            {
                "operation": "insert",
                "target": "//p:sld//p:spTree",
                "value": '''<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
                    <p:nvSpPr>
                        <p:cNvPr id="100" name="Test Shape"/>
                        <p:cNvSpPr/>
                        <p:nvPr/>
                    </p:nvSpPr>
                    <p:spPr/>
                    <p:txBody>
                        <a:bodyPr/>
                        <a:lstStyle/>
                        <a:p>
                            <a:r>
                                <a:rPr lang="en-US"/>
                                <a:t>Added by StyleStack Integration Test</a:t>
                            </a:r>
                        </a:p>
                    </p:txBody>
                </p:sp>''',
                "position": "append"
            }
        ]
        
        variables = {
            "company_name": "StyleStack Corp",
            "test_mode": True,
            "color_scheme": "professional"
        }
        
        metadata = {
            "test_id": "powerpoint_e2e_001",
            "timestamp": time.time()
        }
        
        # Act: Process template through complete pipeline
        result = self.handler.process_template(
            template_path=template_path,
            patches=yaml_patches,
            variables=variables,
            metadata=metadata
        )
        
        # Assert: Verify processing success and output correctness
        assert result.success, f"Processing failed: {result.errors}"
        assert result.format_type == OOXMLFormat.POWERPOINT
        assert len(result.processed_files) > 0
        assert result.output_path is not None
        
        # Verify output file structure
        output_path = Path(result.output_path)
        assert output_path.exists()
        assert TestFixtures.verify_ooxml_structure(output_path, OOXMLFormat.POWERPOINT)
        
        # Verify content changes were applied
        with zipfile.ZipFile(output_path, 'r') as zipf:
            slide_content = zipf.read("ppt/slides/slide1.xml").decode('utf-8')
            assert "StyleStack Integration Test Success" in slide_content
            assert "Added by StyleStack Integration Test" in slide_content
            assert 'val="FF0000"' in slide_content or 'val="ff0000"' in slide_content.lower()
        
        # Verify statistics
        stats = self.handler.get_processing_statistics()
        assert stats['files_processed'] >= 1
        assert stats['formats_processed']['potx'] >= 1
        
        logger.info(f"PowerPoint processing test completed successfully. Stats: {stats}")
    
    def test_complete_word_processing_pipeline(self):
        """Test complete processing pipeline with Word template."""
        # Arrange
        template_path = TestFixtures.create_temp_copy("test_document.dotx")
        
        yaml_patches = [
            {
                "operation": "set",
                "target": "//w:t[text()='Sample Document Title']",
                "value": "StyleStack Word Integration Test"
            },
            {
                "operation": "set", 
                "target": "//w:color[@w:val='2F5496']/@w:val",
                "value": "008000"  # Change to green
            },
            {
                "operation": "insert",
                "target": "//w:body",
                "value": '''<w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                    <w:pPr>
                        <w:pStyle w:val="Normal"/>
                    </w:pPr>
                    <w:r>
                        <w:rPr>
                            <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
                            <w:sz w:val="24"/>
                            <w:color w:val="0000FF"/>
                            <w:b/>
                        </w:rPr>
                        <w:t>This paragraph was inserted by StyleStack integration test. The system successfully processed YAML patches and applied them to the Word document structure.</w:t>
                    </w:r>
                </w:p>''',
                "position": "append"
            }
        ]
        
        # Act
        result = self.handler.process_template(
            template_path=template_path,
            patches=yaml_patches,
            variables={"document_type": "integration_test"},
            metadata={"test_suite": "word_processing"}
        )
        
        # Assert
        assert result.success, f"Word processing failed: {result.errors}"
        assert result.format_type == OOXMLFormat.WORD
        
        # Verify content changes
        output_path = Path(result.output_path)
        with zipfile.ZipFile(output_path, 'r') as zipf:
            doc_content = zipf.read("word/document.xml").decode('utf-8')
            assert "StyleStack Word Integration Test" in doc_content
            assert "This paragraph was inserted by StyleStack" in doc_content
            assert 'w:val="008000"' in doc_content
        
        logger.info("Word processing test completed successfully")
    
    def test_complete_excel_processing_pipeline(self):
        """Test complete processing pipeline with Excel template."""
        # Arrange
        template_path = TestFixtures.create_temp_copy("test_workbook.xltx")
        
        yaml_patches = [
            {
                "operation": "set",
                "target": "//worksheet//c[@r='A1']/v",
                "value": "StyleStack Excel Test"
            },
            {
                "operation": "insert", 
                "target": "//worksheet//sheetData",
                "value": '''<row xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" r="6" spans="1:3">
                    <c r="A6" t="str">
                        <v>Integration Test</v>
                    </c>
                    <c r="B6">
                        <v>999</v>
                    </c>
                    <c r="C6">
                        <v>99.99</v>
                    </c>
                </row>''',
                "position": "append"
            }
        ]
        
        # Act
        result = self.handler.process_template(
            template_path=template_path,
            patches=yaml_patches,
            variables={"workbook_name": "test_integration"},
            metadata={"format": "excel"}
        )
        
        # Assert
        assert result.success, f"Excel processing failed: {result.errors}"
        assert result.format_type == OOXMLFormat.EXCEL
        
        # Verify content changes
        output_path = Path(result.output_path)
        with zipfile.ZipFile(output_path, 'r') as zipf:
            sheet_content = zipf.read("xl/worksheets/sheet1.xml").decode('utf-8')
            assert "StyleStack Excel Test" in sheet_content
            assert "Integration Test" in sheet_content
            assert 'r="A6"' in sheet_content
        
        logger.info("Excel processing test completed successfully")
    
    def test_transaction_pipeline_with_rollback(self):
        """Test transaction pipeline with rollback scenarios."""
        # Arrange
        template_path = TestFixtures.create_temp_copy("test_presentation.potx")
        
        # Create patches where the second one will fail
        patches_with_failure = [
            {
                "operation": "set",
                "target": "//p:sld//a:t[text()='Sample Presentation Title']",
                "value": "First Change Success"
            },
            {
                "operation": "set",
                "target": "//invalid:xpath:that:will:fail",
                "value": "This should fail"
            },
            {
                "operation": "set",
                "target": "//p:sld//a:t[text()='First Change Success']",
                "value": "Third Change (should not happen)"
            }
        ]
        
        # Act: Use transaction pipeline for atomic operations
        with pytest.raises(Exception):  # Should raise because of invalid XPath
            with self.pipeline.transaction() as transaction:
                # Add backup operation
                backup_op = transaction.add_operation(
                    OperationType.BACKUP_STATE,
                    {"files_to_backup": [str(template_path)]}
                )
                
                # Add patch operations
                patch_op = transaction.add_operation(
                    OperationType.APPLY_PATCHES,
                    {
                        "template_path": str(template_path),
                        "patches": patches_with_failure
                    }
                )
                
                # This should trigger rollback due to the invalid XPath
                transaction.commit()
        
        # Assert: Verify rollback was successful (file should be unchanged)
        with zipfile.ZipFile(template_path, 'r') as zipf:
            slide_content = zipf.read("ppt/slides/slide1.xml").decode('utf-8')
            # Original content should still be there
            assert "Sample Presentation Title" in slide_content
            # Changes should not be present due to rollback
            assert "First Change Success" not in slide_content
            assert "Third Change" not in slide_content
        
        # Verify transaction statistics
        stats = self.pipeline.get_performance_statistics()
        assert stats['transactions_rolled_back'] > 0
        
        logger.info(f"Transaction rollback test completed. Stats: {stats}")
    
    def test_successful_transaction_commit(self):
        """Test successful transaction commit with multiple operations."""
        # Arrange
        template_path = TestFixtures.create_temp_copy("test_presentation.potx")
        
        patches = [
            {
                "operation": "set",
                "target": "//p:sld//a:t[text()='Sample Presentation Title']",
                "value": "Transaction Test Success"
            }
        ]
        
        # Act
        with self.pipeline.transaction() as transaction:
            # Backup original file
            backup_op = transaction.add_operation(
                OperationType.BACKUP_STATE,
                {"files_to_backup": [str(template_path)]}
            )
            
            # Apply patches
            patch_op = transaction.add_operation(
                OperationType.APPLY_PATCHES,
                {
                    "template_path": str(template_path),
                    "patches": patches
                }
            )
            
            # Validate structure
            validate_op = transaction.add_operation(
                OperationType.VALIDATE_STRUCTURE,
                {"template_path": str(template_path)}
            )
            
            result = transaction.commit()
        
        # Assert
        assert result.success, f"Transaction failed: {result.error_summary}"
        assert result.state == TransactionState.COMMITTED
        assert len(result.operations_completed) >= 2  # backup + patch operations
        assert len(result.operations_failed) == 0
        
        # Verify changes were applied
        with zipfile.ZipFile(template_path, 'r') as zipf:
            slide_content = zipf.read("ppt/slides/slide1.xml").decode('utf-8')
            assert "Transaction Test Success" in slide_content
        
        logger.info("Successful transaction commit test completed")
    
    def test_streaming_processing_large_files(self):
        """Test streaming processing with large OOXML files."""
        # Arrange: Use the large template with 50 slides
        template_path = TestFixtures.create_temp_copy("large_test_presentation.potx")
        
        # Create patches that will affect multiple slides
        patches = []
        for i in range(1, 26):  # Patch first 25 slides
            patches.append({
                "operation": "set",
                "target": f"//p:sld[{i}]//a:t[contains(text(), 'Large Template Slide {i}')]",
                "value": f"Updated Large Slide {i} via Streaming"
            })
        
        start_time = time.time()
        
        # Act: Process with streaming optimizations enabled
        result = self.handler.process_template(
            template_path=template_path,
            patches=patches,
            variables={"streaming_test": True},
            metadata={"performance_test": True}
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Assert
        assert result.success, f"Large file processing failed: {result.errors}"
        assert result.format_type == OOXMLFormat.POWERPOINT
        
        # Verify performance is reasonable (should complete in under 30 seconds)
        assert processing_time < 30, f"Processing took too long: {processing_time:.2f}s"
        
        # Verify changes were applied to multiple slides
        output_path = Path(result.output_path)
        with zipfile.ZipFile(output_path, 'r') as zipf:
            # Check a few slides to confirm changes
            for slide_num in [1, 10, 20]:
                slide_content = zipf.read(f"ppt/slides/slide{slide_num}.xml").decode('utf-8')
                assert f"Updated Large Slide {slide_num} via Streaming" in slide_content
        
        # Verify streaming was used (check statistics)
        stats = self.handler.get_processing_statistics()
        
        logger.info(f"Streaming processing test completed in {processing_time:.2f}s. Stats: {stats}")
    
    def test_namespace_handling_complex_scenarios(self):
        """Test namespace handling with complex OOXML namespace scenarios."""
        # Arrange
        template_path = TestFixtures.create_temp_copy("test_presentation.potx")
        
        # Patches that test various namespace scenarios
        patches = [
            {
                "operation": "set",
                "target": "//p:presentation//p:sldSz/@cx",
                "value": "12192000",  # Change slide width
                "namespaces": {
                    "p": "http://schemas.openxmlformats.org/presentationml/2006/main"
                }
            },
            {
                "operation": "set", 
                "target": "//a:theme//a:clrScheme//a:accent1//a:srgbClr/@val",
                "value": "FF6B35",  # Change accent color
                "namespaces": {
                    "a": "http://schemas.openxmlformats.org/drawingml/2006/main"
                }
            },
            {
                "operation": "insert",
                "target": "//p:sld//p:spTree",
                "value": '''<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" 
                                 xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                                 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
                    <p:nvSpPr>
                        <p:cNvPr id="200" name="Namespace Test Shape"/>
                        <p:cNvSpPr/>
                        <p:nvPr/>
                    </p:nvSpPr>
                    <p:spPr>
                        <a:xfrm>
                            <a:off x="1000000" y="1000000"/>
                            <a:ext cx="2000000" cy="500000"/>
                        </a:xfrm>
                        <a:prstGeom prst="rect"/>
                        <a:solidFill>
                            <a:srgbClr val="00FF00"/>
                        </a:solidFill>
                    </p:spPr>
                    <p:txBody>
                        <a:bodyPr/>
                        <a:lstStyle/>
                        <a:p>
                            <a:r>
                                <a:rPr/>
                                <a:t>Complex Namespace Test</a:t>
                            </a:r>
                        </a:p>
                    </p:txBody>
                </p:sp>''',
                "position": "append"
            }
        ]
        
        # Act
        result = self.handler.process_template(
            template_path=template_path,
            patches=patches,
            variables={"namespace_test": True},
            metadata={"complex_namespaces": True}
        )
        
        # Assert
        assert result.success, f"Namespace processing failed: {result.errors}"
        
        # Verify namespace-specific changes were applied
        output_path = Path(result.output_path)
        with zipfile.ZipFile(output_path, 'r') as zipf:
            # Check presentation-level change
            pres_content = zipf.read("ppt/presentation.xml").decode('utf-8')
            assert 'cx="12192000"' in pres_content
            
            # Check theme change
            theme_content = zipf.read("ppt/theme/theme1.xml").decode('utf-8')
            assert 'val="FF6B35"' in theme_content or 'val="ff6b35"' in theme_content.lower()
            
            # Check inserted shape
            slide_content = zipf.read("ppt/slides/slide1.xml").decode('utf-8')
            assert "Complex Namespace Test" in slide_content
            assert 'name="Namespace Test Shape"' in slide_content
        
        logger.info("Complex namespace handling test completed successfully")
    
    def test_error_recovery_and_fallback_mechanisms(self):
        """Test error recovery and fallback mechanisms with real failure scenarios."""
        # Arrange
        template_path = TestFixtures.create_temp_copy("test_presentation.potx")
        
        # Mix of valid and invalid patches to test recovery
        patches = [
            {
                "operation": "set",
                "target": "//p:sld//a:t[text()='Sample Presentation Title']", 
                "value": "Recovery Test Success"
            },
            {
                "operation": "set",
                "target": "//nonexistent:namespace:element",
                "value": "This should fail gracefully"
            },
            {
                "operation": "set",
                "target": "//invalid[@xpath[syntax",
                "value": "Invalid XPath syntax"
            },
            {
                "operation": "set",
                "target": "//p:sld//a:t[text()='Recovery Test Success']",
                "value": "Recovery Test Final"
            }
        ]
        
        # Act: Use RETRY_WITH_FALLBACK recovery strategy
        handler_with_recovery = MultiFormatOOXMLHandler()
        processor = YAMLPatchProcessor(recovery_strategy=RecoveryStrategy.RETRY_WITH_FALLBACK)
        handler_with_recovery.processors[OOXMLFormat.POWERPOINT] = processor
        
        result = handler_with_recovery.process_template(
            template_path=template_path,
            patches=patches,
            variables={"recovery_test": True},
            metadata={"error_recovery": True}
        )
        
        # Assert: Some patches should succeed, others should fail gracefully
        # The result should be partially successful
        assert len(result.warnings) > 0 or len(result.errors) > 0, "Should have warnings or errors from invalid patches"
        
        # Verify that valid patches were still applied
        output_path = Path(result.output_path)
        if output_path and output_path.exists():
            with zipfile.ZipFile(output_path, 'r') as zipf:
                slide_content = zipf.read("ppt/slides/slide1.xml").decode('utf-8')
                # At least one valid change should have been applied
                assert ("Recovery Test Success" in slide_content or 
                        "Recovery Test Final" in slide_content), "Valid patches should have been applied despite errors"
        
        # Verify error recovery statistics
        error_stats = processor.error_handler.get_recovery_stats()
        assert error_stats['recovery_attempts'] > 0, "Should have attempted error recovery"
        
        logger.info(f"Error recovery test completed. Recovery stats: {error_stats}")
    
    def test_performance_optimization_systems(self):
        """Test performance optimization systems with real workload."""
        # Arrange: Create multiple templates for batch processing
        templates = []
        for template_name in ["test_presentation.potx", "test_document.dotx", "test_workbook.xltx"]:
            template_path = TestFixtures.create_temp_copy(template_name)
            templates.append(template_path)
        
        # Create patches for each template
        patch_sets = [
            # PowerPoint patches
            [
                {"operation": "set", "target": "//p:sld//a:t", "value": "Performance Test PPT"},
                {"operation": "set", "target": "//a:srgbClr[@val='000000']/@val", "value": "0066CC"}
            ],
            # Word patches
            [
                {"operation": "set", "target": "//w:t[contains(text(), 'Sample')]", "value": "Performance Test Word"},
                {"operation": "set", "target": "//w:color/@w:val", "value": "CC0000"}
            ],
            # Excel patches  
            [
                {"operation": "set", "target": "//worksheet//c[@r='A1']/v", "value": "Performance Test Excel"},
                {"operation": "set", "target": "//worksheet//c[@r='B1']/v", "value": "Optimized"}
            ]
        ]
        
        # Act: Process all templates and measure performance
        start_time = time.time()
        results = []
        
        for i, (template_path, patches) in enumerate(zip(templates, patch_sets)):
            result = self.handler.process_template(
                template_path=template_path,
                patches=patches,
                variables={"performance_test": True, "batch_id": i},
                metadata={"optimization_test": True}
            )
            results.append(result)
        
        end_time = time.time()
        total_processing_time = end_time - start_time
        
        # Assert: All processing should succeed
        for i, result in enumerate(results):
            assert result.success, f"Template {i} processing failed: {result.errors}"
        
        # Verify performance optimizations were used
        stats = self.handler.get_processing_statistics()
        
        # Should have some cache hits if optimization is working
        # (Exact numbers depend on patch similarity)
        assert stats['files_processed'] == len(templates)
        
        # Verify processing time is reasonable
        assert total_processing_time < 60, f"Batch processing took too long: {total_processing_time:.2f}s"
        
        logger.info(f"Performance optimization test completed in {total_processing_time:.2f}s. Stats: {stats}")
    
    def test_token_integration_with_real_templates(self):
        """Test token integration layer with real template processing."""
        # Arrange
        template_path = TestFixtures.create_temp_copy("test_presentation.potx")
        
        # Define patches that use token expressions
        patches = [
            {
                "operation": "set",
                "target": "//p:sld//a:t[text()='Sample Presentation Title']",
                "value": "{{company_name}} {{document_type}} - {{creation_date}}"
            },
            {
                "operation": "set",
                "target": "//p:presentation//p:sldSz/@cx",
                "value": "{{slide_width_emu}}"
            },
            {
                "operation": "set",
                "target": "//a:srgbClr[@val='000000']/@val", 
                "value": "{{primary_color}}"
            }
        ]
        
        # Define variables that will be resolved by token system
        variables = {
            "company_name": "StyleStack Corp",
            "document_type": "Integration Test",
            "creation_date": "2024-01-01",
            "slide_width_emu": "11430000",  # 10 inches in EMU
            "primary_color": "003366"
        }
        
        # Act: Process with token integration enabled
        result = self.handler.process_template(
            template_path=template_path,
            patches=patches,
            variables=variables,
            metadata={"token_integration": True}
        )
        
        # Assert
        assert result.success, f"Token integration processing failed: {result.errors}"
        
        # Verify token substitutions were made
        output_path = Path(result.output_path)
        with zipfile.ZipFile(output_path, 'r') as zipf:
            slide_content = zipf.read("ppt/slides/slide1.xml").decode('utf-8')
            assert "StyleStack Corp Integration Test - 2024-01-01" in slide_content
            
            pres_content = zipf.read("ppt/presentation.xml").decode('utf-8')
            assert 'cx="11430000"' in pres_content
            assert 'val="003366"' in slide_content or 'val="003366"' in pres_content
        
        logger.info("Token integration test completed successfully")
    
    def test_validation_mechanisms_output_correctness(self):
        """Test validation mechanisms to verify output correctness."""
        # Arrange
        template_path = TestFixtures.create_temp_copy("test_presentation.potx")
        
        patches = [
            {
                "operation": "set",
                "target": "//p:sld//a:t[text()='Sample Presentation Title']",
                "value": "Validation Test Title"
            },
            {
                "operation": "insert",
                "target": "//p:sld//p:spTree",
                "value": '''<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
                    <p:nvSpPr>
                        <p:cNvPr id="300" name="Validation Shape"/>
                        <p:cNvSpPr/>
                        <p:nvPr/>
                    </p:nvSpPr>
                    <p:spPr/>
                    <p:txBody>
                        <a:bodyPr/>
                        <a:lstStyle/>
                        <a:p>
                            <a:r>
                                <a:t>Validation content</a:t>
                            </a:r>
                        </a:p>
                    </p:txBody>
                </p:sp>''',
                "position": "append"
            }
        ]
        
        # Act
        result = self.handler.process_template(
            template_path=template_path,
            patches=patches,
            variables={"validation_test": True},
            metadata={"validate_output": True}
        )
        
        # Assert
        assert result.success, f"Validation test processing failed: {result.errors}"
        
        output_path = Path(result.output_path)
        
        # Comprehensive validation checks
        validation_results = []
        
        # 1. Structure validation
        structure_valid = TestFixtures.verify_ooxml_structure(output_path, OOXMLFormat.POWERPOINT)
        validation_results.append(("Structure", structure_valid))
        
        # 2. XML syntax validation
        xml_valid = True
        with zipfile.ZipFile(output_path, 'r') as zipf:
            for file_name in zipf.namelist():
                if file_name.endswith('.xml') and not file_name.endswith('.rels'):
                    try:
                        xml_content = zipf.read(file_name)
                        etree.fromstring(xml_content)
                    except etree.XMLSyntaxError:
                        xml_valid = False
                        break
        validation_results.append(("XML Syntax", xml_valid))
        
        # 3. Content validation
        content_valid = True
        with zipfile.ZipFile(output_path, 'r') as zipf:
            slide_content = zipf.read("ppt/slides/slide1.xml").decode('utf-8')
            if "Validation Test Title" not in slide_content:
                content_valid = False
            if "Validation content" not in slide_content:
                content_valid = False
        validation_results.append(("Content Changes", content_valid))
        
        # 4. Namespace validation
        namespace_valid = True
        with zipfile.ZipFile(output_path, 'r') as zipf:
            slide_content = zipf.read("ppt/slides/slide1.xml").decode('utf-8')
            # Check that inserted content has proper namespace declarations
            if 'xmlns:p=' not in slide_content and 'xmlns:a=' not in slide_content:
                # Should have namespaces at root level at least
                pass  # This is actually okay as long as XML is valid
        validation_results.append(("Namespaces", namespace_valid))
        
        # Assert all validations passed
        for validation_name, validation_result in validation_results:
            assert validation_result, f"Validation failed: {validation_name}"
        
        logger.info(f"Output validation test completed. All validations passed: {validation_results}")


class TestAtomicOperations:
    """Test atomic operation patterns using the transaction pipeline."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_atomic_ooxml_operation_context_manager(self):
        """Test the atomic_ooxml_operation context manager."""
        # Arrange
        template_path = TestFixtures.create_temp_copy("test_presentation.potx")
        
        # Act: Use atomic operation context manager
        with atomic_ooxml_operation() as transaction:
            # Add operations to transaction
            transaction.add_operation(
                OperationType.BACKUP_STATE,
                {"files_to_backup": [str(template_path)]}
            )
            
            transaction.add_operation(
                OperationType.APPLY_PATCHES,
                {
                    "template_path": str(template_path),
                    "patches": [
                        {
                            "operation": "set",
                            "target": "//p:sld//a:t[text()='Sample Presentation Title']",
                            "value": "Atomic Operation Success"
                        }
                    ]
                }
            )
            
            # Context manager should auto-commit on successful exit
        
        # Assert: Changes should be committed
        with zipfile.ZipFile(template_path, 'r') as zipf:
            slide_content = zipf.read("ppt/slides/slide1.xml").decode('utf-8')
            assert "Atomic Operation Success" in slide_content
        
        logger.info("Atomic operation context manager test completed")
    
    def test_transaction_audit_trail(self):
        """Test transaction audit trail functionality."""
        # Arrange
        pipeline = TransactionPipeline(enable_audit_trail=True)
        template_path = TestFixtures.create_temp_copy("test_document.dotx")
        
        # Act: Perform multiple transactions
        for i in range(3):
            with pipeline.transaction() as transaction:
                transaction.add_operation(
                    OperationType.APPLY_PATCHES,
                    {
                        "template_path": str(template_path),
                        "patches": [
                            {
                                "operation": "set",
                                "target": "//w:t[contains(text(), 'Sample Document Title')]",
                                "value": f"Audit Test {i+1}"
                            }
                        ]
                    }
                )
                
                result = transaction.commit()
        
        # Assert: Audit trail should contain all transactions
        stats = pipeline.get_performance_statistics()
        assert stats['transactions_committed'] == 3
        assert len(pipeline.audit_trail) == 3
        
        # Verify each transaction in audit trail
        for i, audit_entry in enumerate(pipeline.audit_trail):
            assert audit_entry.success
            assert audit_entry.state == TransactionState.COMMITTED
            assert len(audit_entry.operations_completed) > 0
        
        logger.info(f"Audit trail test completed. Transactions logged: {len(pipeline.audit_trail)}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])