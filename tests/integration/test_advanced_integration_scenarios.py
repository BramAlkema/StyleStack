#!/usr/bin/env python3
"""
Advanced Integration Test Scenarios for StyleStack YAML-to-OOXML Processing Engine

This test suite covers complex real-world scenarios and edge cases:
- Cross-format template processing
- Large-scale batch operations
- Performance stress testing
- Memory management validation
- Concurrent processing scenarios
- Format migration workflows
- Production deployment simulation

Tests use actual OOXML template files and simulate real customer use cases.
"""

import os
import sys
import pytest
import shutil
import tempfile
import zipfile
import time
import threading
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import gc
import psutil
import json

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
    OperationType
)
from yaml_ooxml_processor import (
    YAMLPatchProcessor, 
    RecoveryStrategy,
    PatchResult
)
from lxml import etree

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test fixtures path
FIXTURES_PATH = Path(__file__).parent / "fixtures"
TEMPLATES_PATH = FIXTURES_PATH / "templates"


class PerformanceMonitor:
    """Monitor system performance during testing."""
    
    def __init__(self):
        self.start_time = None
        self.start_memory = None
        self.process = psutil.Process()
    
    def start(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        gc.collect()  # Force garbage collection for accurate baseline
    
    def stop(self) -> Dict[str, Any]:
        """Stop monitoring and return performance metrics."""
        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            "duration_seconds": end_time - self.start_time,
            "memory_start_mb": self.start_memory,
            "memory_end_mb": end_memory,
            "memory_delta_mb": end_memory - self.start_memory,
            "peak_memory_mb": self.process.memory_info().peak_wss / 1024 / 1024 if hasattr(self.process.memory_info(), 'peak_wss') else end_memory
        }


class TestAdvancedIntegrationScenarios:
    """Advanced integration test scenarios for production-ready validation."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.handler = MultiFormatOOXMLHandler(enable_token_integration=True)
        self.pipeline = TransactionPipeline(enable_audit_trail=True)
        self.monitor = PerformanceMonitor()
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Force cleanup
        gc.collect()
    
    def _create_temp_copy(self, template_name: str) -> Path:
        """Create a temporary copy of a template."""
        original = TEMPLATES_PATH / template_name
        if not original.exists():
            raise FileNotFoundError(f"Template not found: {original}")
        temp_path = self.temp_dir / template_name
        shutil.copy2(original, temp_path)
        return temp_path
    
    def test_cross_format_batch_processing(self):
        """Test batch processing across multiple OOXML formats simultaneously."""
        # Arrange: Create multiple templates of different formats
        templates = [
            self._create_temp_copy("test_presentation.potx"),
            self._create_temp_copy("test_document.dotx"), 
            self._create_temp_copy("test_workbook.xltx"),
            # Create additional copies for batch testing
            self._create_temp_copy("test_presentation.potx"),
            self._create_temp_copy("test_document.dotx")
        ]
        
        # Define format-specific patch sets
        patch_configs = [
            # PowerPoint patches
            {
                "format": "potx",
                "patches": [
                    {"operation": "set", "target": "//p:sld//a:t", "value": "Batch PowerPoint {{batch_id}}"},
                    {"operation": "set", "target": "//a:accent1//a:srgbClr/@val", "value": "FF6B35"}
                ]
            },
            # Word patches  
            {
                "format": "dotx",
                "patches": [
                    {"operation": "set", "target": "//w:t[contains(text(), 'Sample')]", "value": "Batch Word {{batch_id}}"},
                    {"operation": "set", "target": "//w:color[@w:val='2F5496']/@w:val", "value": "008000"}
                ]
            },
            # Excel patches
            {
                "format": "xltx", 
                "patches": [
                    {"operation": "set", "target": "//worksheet//c[@r='A1']/v", "value": "Batch Excel {{batch_id}}"},
                    {"operation": "insert", "target": "//worksheet//sheetData", 
                     "value": '<row xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" r="10"><c r="A10" t="str"><v>Batch Process {{timestamp}}</v></c></row>',
                     "position": "append"}
                ]
            }
        ]
        
        self.monitor.start()
        
        # Act: Process all templates in batch
        results = []
        for i, template_path in enumerate(templates):
            # Determine format and get appropriate patches
            format_type = OOXMLFormat.from_path(template_path)
            patch_config = next(pc for pc in patch_configs if pc["format"] == format_type.value)
            
            variables = {
                "batch_id": f"B{i+1:03d}",
                "timestamp": str(int(time.time())),
                "format": format_type.value
            }
            
            result = self.handler.process_template(
                template_path=template_path,
                patches=patch_config["patches"],
                variables=variables,
                metadata={"batch_processing": True, "batch_index": i}
            )
            results.append(result)
        
        performance_metrics = self.monitor.stop()
        
        # Assert: All processing should succeed
        for i, result in enumerate(results):
            assert result.success, f"Batch item {i} failed: {result.errors}"
            assert result.output_path is not None
        
        # Verify performance is reasonable
        assert performance_metrics["duration_seconds"] < 120, f"Batch processing took too long: {performance_metrics['duration_seconds']:.2f}s"
        assert performance_metrics["memory_delta_mb"] < 500, f"Memory usage too high: {performance_metrics['memory_delta_mb']:.1f}MB"
        
        # Verify cross-format statistics
        stats = self.handler.get_processing_statistics()
        assert stats['files_processed'] == len(templates)
        assert stats['formats_processed']['potx'] >= 2  # Two PowerPoint files
        assert stats['formats_processed']['dotx'] >= 2  # Two Word files
        assert stats['formats_processed']['xltx'] >= 1  # One Excel file
        
        logger.info(f"Cross-format batch processing completed. Performance: {performance_metrics}, Stats: {stats}")
    
    def test_concurrent_template_processing(self):
        """Test concurrent processing of multiple templates with thread safety."""
        # Arrange: Prepare multiple template copies
        num_concurrent = 8
        templates = []
        for i in range(num_concurrent):
            template_path = self._create_temp_copy(f"concurrent_test_{i}.potx")
            shutil.copy2(TEMPLATES_PATH / "test_presentation.potx", template_path)
            templates.append(template_path)
        
        # Define patches with unique identifiers
        def create_patches_for_thread(thread_id: int) -> List[Dict[str, Any]]:
            return [
                {
                    "operation": "set",
                    "target": "//p:sld//a:t[text()='Sample Presentation Title']",
                    "value": f"Concurrent Test Thread {thread_id}"
                },
                {
                    "operation": "set",
                    "target": "//a:srgbClr[@val='000000']/@val", 
                    "value": f"{thread_id:02d}{thread_id:02d}{thread_id:02d}"  # Unique color per thread
                }
            ]
        
        self.monitor.start()
        results = []
        errors = []
        
        # Act: Process templates concurrently
        def process_template_thread(thread_id: int, template_path: Path) -> Optional[ProcessingResult]:
            try:
                # Each thread gets its own handler to test thread safety
                thread_handler = MultiFormatOOXMLHandler(enable_token_integration=True)
                
                result = thread_handler.process_template(
                    template_path=template_path,
                    patches=create_patches_for_thread(thread_id),
                    variables={"thread_id": thread_id, "concurrent_test": True},
                    metadata={"concurrent_processing": True, "thread": thread_id}
                )
                return result
            except Exception as e:
                errors.append(f"Thread {thread_id} failed: {e}")
                return None
        
        # Use ThreadPoolExecutor for concurrent execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = []
            for i, template_path in enumerate(templates):
                future = executor.submit(process_template_thread, i, template_path)
                futures.append(future)
            
            # Collect results
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
        
        performance_metrics = self.monitor.stop()
        
        # Assert: All concurrent processing should succeed
        assert len(errors) == 0, f"Concurrent processing errors: {errors}"
        assert len(results) == num_concurrent, f"Expected {num_concurrent} results, got {len(results)}"
        
        # Verify all results are successful
        for i, result in enumerate(results):
            assert result.success, f"Concurrent result {i} failed: {result.errors}"
        
        # Verify each template was processed correctly
        for i, result in enumerate(results):
            output_path = Path(result.output_path)
            with zipfile.ZipFile(output_path, 'r') as zipf:
                slide_content = zipf.read("ppt/slides/slide1.xml").decode('utf-8')
                # Should contain the thread-specific content
                assert f"Concurrent Test Thread" in slide_content
        
        # Performance should be reasonable for concurrent processing
        assert performance_metrics["duration_seconds"] < 180, f"Concurrent processing took too long: {performance_metrics['duration_seconds']:.2f}s"
        
        logger.info(f"Concurrent processing test completed. {num_concurrent} threads, Performance: {performance_metrics}")
    
    def test_memory_management_large_scale_processing(self):
        """Test memory management during large-scale processing operations."""
        # Arrange: Use large template and create memory-intensive operations
        template_path = self._create_temp_copy("large_test_presentation.potx")
        
        # Create many patches that will process different parts of the large file
        patches = []
        for slide_num in range(1, 51):  # All 50 slides
            patches.extend([
                {
                    "operation": "set",
                    "target": f"//p:sld[{slide_num}]//a:t[contains(text(), 'Large Template Slide')]",
                    "value": f"Memory Test Slide {slide_num} - {{test_iteration}}"
                },
                {
                    "operation": "insert",
                    "target": f"//p:sld[{slide_num}]//p:spTree",
                    "value": f'''<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
                        <p:nvSpPr>
                            <p:cNvPr id="{1000 + slide_num}" name="Memory Test Shape {slide_num}"/>
                            <p:cNvSpPr/>
                            <p:nvPr/>
                        </p:nvSpPr>
                        <p:spPr/>
                        <p:txBody>
                            <a:bodyPr/>
                            <a:lstStyle/>
                            <a:p>
                                <a:r>
                                    <a:t>Memory test content for slide {slide_num}. This content is designed to test memory management during large-scale OOXML processing operations.</a:t>
                                </a:r>
                            </a:p>
                        </p:txBody>
                    </p:sp>''',
                    "position": "append"
                }
            ])
        
        # Monitor memory usage across multiple iterations
        memory_snapshots = []
        
        # Act: Process the same large template multiple times
        for iteration in range(3):
            self.monitor.start()
            
            # Force garbage collection before each iteration
            gc.collect()
            
            variables = {
                "test_iteration": f"Iter_{iteration+1}",
                "memory_test": True,
                "large_scale": True
            }
            
            result = self.handler.process_template(
                template_path=template_path,
                patches=patches,
                variables=variables,
                metadata={"memory_test": True, "iteration": iteration}
            )
            
            perf_metrics = self.monitor.stop()
            memory_snapshots.append(perf_metrics)
            
            # Assert: Each iteration should succeed
            assert result.success, f"Memory test iteration {iteration} failed: {result.errors}"
            
            # Clean up output to prevent disk space issues
            if result.output_path and Path(result.output_path).exists():
                Path(result.output_path).unlink()
        
        # Assert: Memory usage should remain stable across iterations
        memory_deltas = [snapshot["memory_delta_mb"] for snapshot in memory_snapshots]
        avg_memory_delta = sum(memory_deltas) / len(memory_deltas)
        
        # Memory usage should not grow significantly between iterations
        assert avg_memory_delta < 200, f"Average memory usage too high: {avg_memory_delta:.1f}MB"
        
        # Check for memory leaks (memory should not increase significantly between iterations)
        if len(memory_snapshots) > 1:
            first_peak = memory_snapshots[0]["memory_end_mb"]
            last_peak = memory_snapshots[-1]["memory_end_mb"]
            memory_growth = last_peak - first_peak
            assert memory_growth < 100, f"Potential memory leak detected: {memory_growth:.1f}MB growth"
        
        logger.info(f"Memory management test completed. Memory deltas: {memory_deltas}, Average: {avg_memory_delta:.1f}MB")
    
    def test_production_deployment_simulation(self):
        """Simulate production deployment scenario with realistic workload."""
        # Arrange: Create a realistic production workload
        production_templates = [
            ("corporate_presentation.potx", "test_presentation.potx"),
            ("monthly_report.dotx", "test_document.dotx"),
            ("financial_dashboard.xltx", "test_workbook.xltx"),
            ("quarterly_slides.potx", "large_test_presentation.potx")  # Large file
        ]
        
        # Copy templates with production names
        template_paths = []
        for prod_name, source_name in production_templates:
            prod_path = self.temp_dir / prod_name
            shutil.copy2(TEMPLATES_PATH / source_name, prod_path)
            template_paths.append(prod_path)
        
        # Define production-like patch configurations
        production_configs = [
            {
                "name": "corporate_branding",
                "templates": ["corporate_presentation.potx"],
                "patches": [
                    {"operation": "set", "target": "//a:accent1//a:srgbClr/@val", "value": "{{brand_color}}"},
                    {"operation": "set", "target": "//p:sld//a:t[contains(text(), 'Sample')]", "value": "{{company_name}} {{document_title}}"},
                    {"operation": "insert", "target": "//p:sld//p:spTree", 
                     "value": '''<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
                         <p:nvSpPr><p:cNvPr id="999" name="Company Logo"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
                         <p:spPr/>
                         <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>{{company_name}} - {{year}}</a:t></a:r></a:p></p:txBody>
                     </p:sp>''', 
                     "position": "append"}
                ],
                "variables": {
                    "brand_color": "0066CC",
                    "company_name": "TechCorp Inc", 
                    "document_title": "Quarterly Review",
                    "year": "2024"
                }
            },
            {
                "name": "document_standardization", 
                "templates": ["monthly_report.dotx"],
                "patches": [
                    {"operation": "set", "target": "//w:t[contains(text(), 'Sample Document')]", "value": "{{report_type}} - {{period}}"},
                    {"operation": "set", "target": "//w:color[@w:val='2F5496']/@w:val", "value": "{{text_color}}"}
                ],
                "variables": {
                    "report_type": "Monthly Status Report",
                    "period": "Q4 2024", 
                    "text_color": "333333"
                }
            },
            {
                "name": "dashboard_customization",
                "templates": ["financial_dashboard.xltx"],
                "patches": [
                    {"operation": "set", "target": "//worksheet//c[@r='A1']/v", "value": "{{dashboard_title}}"},
                    {"operation": "set", "target": "//worksheet//c[@r='B2']/v", "value": "{{current_quarter}}"}
                ],
                "variables": {
                    "dashboard_title": "Financial Dashboard Q4 2024",
                    "current_quarter": "Q4"
                }
            },
            {
                "name": "large_presentation_update",
                "templates": ["quarterly_slides.potx"], 
                "patches": [
                    {"operation": "set", "target": "//p:sld[1]//a:t[contains(text(), 'Large Template')]", "value": "{{presentation_title}}"}
                    # Only one patch for large file to keep test reasonable
                ],
                "variables": {
                    "presentation_title": "Q4 Business Review - TechCorp"
                }
            }
        ]
        
        self.monitor.start()
        
        # Act: Execute production deployment simulation
        deployment_results = []
        
        with TransactionPipeline(enable_audit_trail=True) as pipeline:
            for config in production_configs:
                for template_name in config["templates"]:
                    template_path = self.temp_dir / template_name
                    
                    with pipeline.transaction() as transaction:
                        # Backup operation
                        transaction.add_operation(
                            OperationType.BACKUP_STATE,
                            {"files_to_backup": [str(template_path)]}
                        )
                        
                        # Validation operation
                        transaction.add_operation(
                            OperationType.VALIDATE_STRUCTURE,
                            {"template_path": str(template_path)}
                        )
                        
                        # Patch application
                        transaction.add_operation(
                            OperationType.APPLY_PATCHES,
                            {
                                "template_path": str(template_path),
                                "patches": config["patches"],
                                "variables": config["variables"]
                            }
                        )
                        
                        # Process the transaction
                        result = transaction.commit()
                        deployment_results.append({
                            "config_name": config["name"],
                            "template": template_name,
                            "result": result
                        })
        
        performance_metrics = self.monitor.stop()
        
        # Assert: All production operations should succeed
        failed_deployments = []
        for deployment in deployment_results:
            if not deployment["result"].success:
                failed_deployments.append(deployment)
        
        assert len(failed_deployments) == 0, f"Production deployment failures: {failed_deployments}"
        
        # Verify production-level performance
        assert performance_metrics["duration_seconds"] < 300, f"Production simulation took too long: {performance_metrics['duration_seconds']:.2f}s"
        
        # Verify all files were processed correctly
        for deployment in deployment_results:
            template_path = self.temp_dir / deployment["template"]
            format_type = OOXMLFormat.from_path(template_path)
            
            # Basic structure verification
            with zipfile.ZipFile(template_path, 'r') as zipf:
                file_list = zipf.namelist()
                assert "[Content_Types].xml" in file_list
                
                # Format-specific verification
                if format_type == OOXMLFormat.POWERPOINT:
                    assert "ppt/presentation.xml" in file_list
                elif format_type == OOXMLFormat.WORD:
                    assert "word/document.xml" in file_list
                elif format_type == OOXMLFormat.EXCEL:
                    assert "xl/workbook.xml" in file_list
        
        # Verify transaction audit trail
        pipeline_stats = pipeline.get_performance_statistics()
        assert pipeline_stats["transactions_committed"] == len(deployment_results)
        
        logger.info(f"Production deployment simulation completed. Performance: {performance_metrics}, Pipeline Stats: {pipeline_stats}")
    
    def test_stress_testing_edge_cases(self):
        """Stress test with edge cases and boundary conditions.""" 
        # Arrange: Create various stress test scenarios
        template_path = self._create_temp_copy("test_presentation.potx")
        
        stress_scenarios = [
            {
                "name": "extremely_long_text",
                "patches": [
                    {
                        "operation": "set",
                        "target": "//p:sld//a:t[text()='Sample Presentation Title']",
                        "value": "A" * 10000  # 10KB of text
                    }
                ]
            },
            {
                "name": "many_small_operations", 
                "patches": [
                    {"operation": "set", "target": f"//p:sld//a:t[text()='Sample Presentation Title']", "value": f"Test {i}"}
                    for i in range(100)  # 100 small operations on same element
                ]
            },
            {
                "name": "complex_xml_insertion",
                "patches": [
                    {
                        "operation": "insert",
                        "target": "//p:sld//p:spTree",
                        "value": '''<p:grpSp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
                            <p:nvGrpSpPr>
                                <p:cNvPr id="2000" name="Stress Test Group"/>
                                <p:cNvGrpSpPr/>
                                <p:nvPr/>
                            </p:nvGrpSpPr>
                            <p:grpSpPr>
                                <a:xfrm>
                                    <a:off x="0" y="0"/>
                                    <a:ext cx="5000000" cy="3000000"/>
                                    <a:chOff x="0" y="0"/>
                                    <a:chExt cx="5000000" cy="3000000"/>
                                </a:xfrm>
                            </p:grpSpPr>''' + 
                            ''.join([f'''<p:sp>
                                <p:nvSpPr>
                                    <p:cNvPr id="{3000 + i}" name="Stress Shape {i}"/>
                                    <p:cNvSpPr/>
                                    <p:nvPr/>
                                </p:nvSpPr>
                                <p:spPr>
                                    <a:xfrm>
                                        <a:off x="{i * 500000}" y="{i * 200000}"/>
                                        <a:ext cx="400000" cy="150000"/>
                                    </a:xfrm>
                                    <a:prstGeom prst="rect"/>
                                </p:spPr>
                                <p:txBody>
                                    <a:bodyPr/>
                                    <a:lstStyle/>
                                    <a:p><a:r><a:t>Shape {i}</a:t></a:r></a:p>
                                </a:txBody>
                            </p:sp>''' for i in range(20)]) + 
                        '''</p:grpSp>''',
                        "position": "append"
                    }
                ]
            }
        ]
        
        # Act: Execute stress test scenarios
        stress_results = []
        
        for scenario in stress_scenarios:
            logger.info(f"Executing stress test: {scenario['name']}")
            
            # Create a fresh copy for each stress test
            stress_template = self._create_temp_copy(f"stress_{scenario['name']}.potx")
            shutil.copy2(template_path, stress_template)
            
            self.monitor.start()
            
            try:
                result = self.handler.process_template(
                    template_path=stress_template,
                    patches=scenario["patches"],
                    variables={"stress_test": scenario["name"]},
                    metadata={"stress_testing": True}
                )
                
                perf_metrics = self.monitor.stop()
                
                stress_results.append({
                    "scenario": scenario["name"], 
                    "success": result.success,
                    "errors": result.errors,
                    "performance": perf_metrics
                })
                
            except Exception as e:
                perf_metrics = self.monitor.stop()
                stress_results.append({
                    "scenario": scenario["name"],
                    "success": False,
                    "errors": [str(e)],
                    "performance": perf_metrics
                })
        
        # Assert: Evaluate stress test results
        for result in stress_results:
            scenario_name = result["scenario"]
            
            # All scenarios should complete (though some may have warnings)
            if not result["success"] and result["errors"]:
                # Log errors but don't fail the test for expected stress conditions
                logger.warning(f"Stress scenario '{scenario_name}' had errors: {result['errors']}")
            
            # Performance should be reasonable even under stress
            duration = result["performance"]["duration_seconds"]
            memory_delta = result["performance"]["memory_delta_mb"]
            
            assert duration < 120, f"Stress scenario '{scenario_name}' took too long: {duration:.2f}s"
            assert memory_delta < 500, f"Stress scenario '{scenario_name}' used too much memory: {memory_delta:.1f}MB"
        
        logger.info(f"Stress testing completed. Results: {json.dumps(stress_results, indent=2)}")
    
    def test_format_migration_workflow(self):
        """Test workflow for migrating content between different OOXML formats."""
        # Arrange: Create templates of different formats
        source_ppt = self._create_temp_copy("test_presentation.potx")
        target_word = self._create_temp_copy("test_document.dotx")
        
        # Define migration patches (extract content from PowerPoint, adapt for Word)
        extraction_patches = [
            {
                "operation": "set",
                "target": "//p:sld//a:t[text()='Sample Presentation Title']",
                "value": "Migration Source Content"
            }
        ]
        
        adaptation_patches = [
            {
                "operation": "set",
                "target": "//w:t[contains(text(), 'Sample Document Title')]",
                "value": "Migrated: Migration Source Content"
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
                            <w:b/>
                            <w:color w:val="0066CC"/>
                        </w:rPr>
                        <w:t>Content migrated from PowerPoint template. This demonstrates cross-format content migration capabilities.</w:t>
                    </w:r>
                </w:p>''',
                "position": "append"
            }
        ]
        
        # Act: Execute migration workflow using transaction pipeline
        with self.pipeline.transaction() as migration_transaction:
            # Step 1: Process source template
            migration_transaction.add_operation(
                OperationType.APPLY_PATCHES,
                {
                    "template_path": str(source_ppt),
                    "patches": extraction_patches
                }
            )
            
            # Step 2: Process target template
            migration_transaction.add_operation(
                OperationType.APPLY_PATCHES,
                {
                    "template_path": str(target_word),
                    "patches": adaptation_patches
                }
            )
            
            # Step 3: Validate both templates
            migration_transaction.add_operation(
                OperationType.VALIDATE_STRUCTURE,
                {"template_path": str(source_ppt)}
            )
            
            migration_transaction.add_operation(
                OperationType.VALIDATE_STRUCTURE,
                {"template_path": str(target_word)}
            )
            
            result = migration_transaction.commit()
        
        # Assert: Migration should succeed
        assert result.success, f"Format migration failed: {result.error_summary}"
        assert result.state == TransactionState.COMMITTED
        
        # Verify source template was updated
        with zipfile.ZipFile(source_ppt, 'r') as zipf:
            slide_content = zipf.read("ppt/slides/slide1.xml").decode('utf-8')
            assert "Migration Source Content" in slide_content
        
        # Verify target template received migrated content
        with zipfile.ZipFile(target_word, 'r') as zipf:
            doc_content = zipf.read("word/document.xml").decode('utf-8')
            assert "Migrated: Migration Source Content" in doc_content
            assert "Content migrated from PowerPoint template" in doc_content
        
        logger.info("Format migration workflow test completed successfully")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])  # Stop on first failure for debugging