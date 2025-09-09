#!/usr/bin/env python3
"""
StyleStack OOXML Extension Variable System - Variable Substitution Pipeline Tests

Comprehensive test suite for Phase 2.4: Variable Substitution Pipeline.
Tests end-to-end variable substitution workflows, atomic operations, rollback,
progress reporting, and document integrity validation.

Created: 2025-09-07
Author: StyleStack Development Team  
License: MIT
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
import time
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import xml.etree.ElementTree as ET

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))

from tools.substitution.pipeline import SubstitutionPipeline as VariableSubstitutionPipeline
from tools.substitution.types import (
    SubstitutionResult,
    SubstitutionProgress,
    SubstitutionError,
    TransactionContext,
    ValidationCheckpoint,
    ProgressReporter
)


class TestVariableSubstitutionPipeline(unittest.TestCase):
    """Test suite for Variable Substitution Pipeline"""
    
    def setUp(self):
        """Set up test environment"""
        self.pipeline = VariableSubstitutionPipeline(
            enable_transactions=True,
            enable_progress_reporting=True,
            validation_level='strict'
        )
        
        # Sample OOXML documents for testing
        self.sample_ppt_theme = '''<?xml version="1.0"?>
        <a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Test">
          <a:themeElements>
            <a:clrScheme name="Test">
              <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
              <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
              <a:accent1><a:srgbClr val="4472C4"/></a:accent1>
              <a:accent2><a:srgbClr val="70AD47"/></a:accent2>
              <a:accent3><a:srgbClr val="FFC000"/></a:accent3>
            </a:clrScheme>
            <a:fontScheme name="Test">
              <a:majorFont><a:latin typeface="Calibri Light"/></a:majorFont>
              <a:minorFont><a:latin typeface="Calibri"/></a:minorFont>
            </a:fontScheme>
          </a:themeElements>
        </a:theme>'''
        
        self.sample_word_styles = '''<?xml version="1.0"?>
        <w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:style w:type="paragraph" w:styleId="Heading1">
            <w:name w:val="heading 1"/>
            <w:rPr>
              <w:color w:val="2F5496"/>
              <w:sz w:val="32"/>
              <w:rFonts w:ascii="Calibri Light"/>
            </w:rPr>
          </w:style>
          <w:style w:type="paragraph" w:styleId="Normal">
            <w:name w:val="Normal"/>
            <w:rPr>
              <w:color w:val="000000"/>
              <w:sz w:val="22"/>
              <w:rFonts w:ascii="Calibri"/>
            </w:rPr>
          </w:style>
        </w:styles>'''
        
        self.sample_excel_theme = '''<?xml version="1.0"?>
        <a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
          <a:themeElements>
            <a:clrScheme name="Excel">
              <a:accent1><a:srgbClr val="5B9BD5"/></a:accent1>
              <a:accent2><a:srgbClr val="A5A5A5"/></a:accent2>
            </a:clrScheme>
          </a:themeElements>
        </a:theme>'''
        
        # Sample variables for testing
        self.test_variables = {
            'brandPrimary': {
                'id': 'brandPrimary',
                'type': 'color',
                'value': 'FF0000',
                'xpath': '//a:accent1//a:srgbClr',
                'scope': 'org',
                'source': 'extension'
            },
            'brandSecondary': {
                'id': 'brandSecondary', 
                'type': 'color',
                'value': '00FF00',
                'xpath': '//a:accent2//a:srgbClr',
                'scope': 'org',
                'source': 'extension'
            },
            'headingFont': {
                'id': 'headingFont',
                'type': 'font',
                'value': 'Arial Black',
                'xpath': '//a:majorFont//a:latin',
                'scope': 'org',
                'source': 'extension'
            },
            'bodyFont': {
                'id': 'bodyFont',
                'type': 'font', 
                'value': 'Arial',
                'xpath': '//a:minorFont//a:latin',
                'scope': 'org',
                'source': 'extension'
            },
            'headingColor': {
                'id': 'headingColor',
                'type': 'color',
                'value': 'CC0000',
                'xpath': '//w:style[@w:styleId="Heading1"]//w:color',
                'scope': 'channel',
                'source': 'yaml'
            }
        }


class TestEndToEndSubstitutionWorkflows(TestVariableSubstitutionPipeline):
    """Test end-to-end variable substitution workflows"""
    
    def test_single_document_substitution_workflow(self):
        """Test complete workflow for single document substitution"""
        # Test PowerPoint theme substitution
        result = self.pipeline.substitute_variables_in_document(
            document_content=self.sample_ppt_theme,
            variables=self.test_variables,
            document_type='powerpoint_theme'
        )
        
        self.assertTrue(result.success)
        self.assertGreater(result.variables_applied, 0)
        self.assertIn('FF0000', result.updated_content)  # brandPrimary applied
        self.assertIn('Arial Black', result.updated_content)  # headingFont applied
        self.assertNotIn('4472C4', result.updated_content)  # Original accent1 replaced
        
        # Verify document structure preserved
        updated_root = ET.fromstring(result.updated_content)
        original_root = ET.fromstring(self.sample_ppt_theme)
        self.assertEqual(len(list(updated_root.iter())), len(list(original_root.iter())))
        
        print(f"✅ Single document substitution: {result.variables_applied} variables applied in {result.processing_time:.3f}s")

    def test_multi_document_batch_substitution(self):
        """Test batch substitution across multiple document types"""
        documents = [
            ('ppt_theme.xml', self.sample_ppt_theme, 'powerpoint_theme'),
            ('word_styles.xml', self.sample_word_styles, 'word_styles'),
            ('excel_theme.xml', self.sample_excel_theme, 'excel_theme')
        ]
        
        batch_result = self.pipeline.substitute_variables_in_batch(
            documents=documents,
            variables=self.test_variables,
            parallel_processing=True
        )
        
        self.assertTrue(batch_result.success)
        self.assertEqual(len(batch_result.document_results), 3)
        
        # Verify each document processed successfully
        for doc_name, doc_result in batch_result.document_results.items():
            self.assertTrue(doc_result.success)
            self.assertGreater(doc_result.variables_applied, 0)
            
        total_variables = sum(r.variables_applied for r in batch_result.document_results.values())
        print(f"✅ Batch substitution: {total_variables} variables applied across {len(documents)} documents")

    def test_conditional_variable_substitution(self):
        """Test substitution with conditional variables and dependencies"""
        conditional_variables = self.test_variables.copy()
        conditional_variables.update({
            'conditionalColor': {
                'id': 'conditionalColor',
                'type': 'color',
                'value': '0000FF',
                'xpath': '//a:accent3//a:srgbClr',
                'scope': 'user',
                'source': 'extension',
                'conditions': [
                    {'variable': 'brandPrimary', 'operator': 'equals', 'value': 'FF0000'},
                    {'variable': 'headingFont', 'operator': 'contains', 'value': 'Arial'}
                ]
            }
        })
        
        result = self.pipeline.substitute_variables_in_document(
            document_content=self.sample_ppt_theme,
            variables=conditional_variables,
            evaluate_conditions=True
        )
        
        self.assertTrue(result.success)
        self.assertIn('0000FF', result.updated_content)  # Conditional variable applied
        
        print(f"✅ Conditional substitution: {result.variables_applied} variables (including conditional)")

    def test_hierarchical_variable_precedence(self):
        """Test variable precedence resolution in substitution"""
        hierarchical_variables = {
            'testColor_core': {
                'id': 'testColor',
                'type': 'color', 
                'value': 'AAAAAA',
                'xpath': '//a:accent1//a:srgbClr',
                'scope': 'core',
                'source': 'yaml',
                'hierarchy_level': 1
            },
            'testColor_org': {
                'id': 'testColor',
                'type': 'color',
                'value': 'BBBBBB', 
                'xpath': '//a:accent1//a:srgbClr',
                'scope': 'org',
                'source': 'extension',
                'hierarchy_level': 5
            },
            'testColor_user': {
                'id': 'testColor',
                'type': 'color',
                'value': 'CCCCCC',
                'xpath': '//a:accent1//a:srgbClr',
                'scope': 'user',
                'source': 'extension',
                'hierarchy_level': 9
            }
        }
        
        result = self.pipeline.substitute_variables_in_document(
            document_content=self.sample_ppt_theme,
            variables=hierarchical_variables,
            resolve_hierarchy=True
        )
        
        self.assertTrue(result.success)
        # Should use highest hierarchy level (user scope)
        self.assertIn('CCCCCC', result.updated_content) 
        self.assertNotIn('AAAAAA', result.updated_content)
        self.assertNotIn('BBBBBB', result.updated_content)
        
        print("✅ Hierarchical precedence: user-level variable took precedence")


class TestAtomicOperationsAndRollback(TestVariableSubstitutionPipeline):
    """Test atomic operations and error rollback mechanisms"""
    
    def test_transaction_commit_on_success(self):
        """Test transaction commits when all operations succeed"""
        with self.pipeline.create_transaction() as transaction:
            # Perform multiple operations
            result1 = transaction.substitute_in_document(
                self.sample_ppt_theme, 
                {'brandPrimary': self.test_variables['brandPrimary']}
            )
            result2 = transaction.substitute_in_document(
                self.sample_word_styles,
                {'headingColor': self.test_variables['headingColor']}
            )
            
            self.assertTrue(result1.success)
            self.assertTrue(result2.success)
            
        # Transaction should commit automatically
        self.assertTrue(transaction.committed)
        self.assertFalse(transaction.rolled_back)
        print("✅ Transaction committed successfully on all operations succeeding")

    def test_transaction_rollback_on_error(self):
        """Test transaction rolls back when operations fail"""
        try:
            with self.pipeline.create_transaction() as transaction:
                # First operation succeeds
                result1 = transaction.substitute_in_document(
                    self.sample_ppt_theme,
                    {'brandPrimary': self.test_variables['brandPrimary']}
                )
                self.assertTrue(result1.success)
                
                # Second operation fails (invalid XML)
                result2 = transaction.substitute_in_document(
                    '<invalid>xml</invalid>',
                    {'brandPrimary': self.test_variables['brandPrimary']}
                )
                
                # Force error to trigger rollback
                if not result2.success:
                    raise SubstitutionError("Substitution failed", result2.errors)
                    
        except SubstitutionError:
            pass  # Expected error
            
        # Transaction should roll back
        self.assertTrue(transaction.rolled_back)
        self.assertFalse(transaction.committed)
        print("✅ Transaction rolled back successfully on error")

    def test_partial_failure_recovery(self):
        """Test recovery from partial failures in batch operations"""
        documents = [
            ('valid1.xml', self.sample_ppt_theme, 'powerpoint_theme'),
            ('invalid.xml', '<invalid>xml</invalid>', 'powerpoint_theme'),  # Invalid XML
            ('valid2.xml', self.sample_word_styles, 'word_styles')
        ]
        
        batch_result = self.pipeline.substitute_variables_in_batch(
            documents=documents,
            variables=self.test_variables,
            continue_on_error=True,  # Don't stop on individual failures
            transaction_mode='per_document'  # Individual transactions
        )
        
        # Batch should partially succeed
        self.assertFalse(batch_result.success)  # Overall failure due to one doc
        self.assertEqual(len(batch_result.successful_documents), 2)
        self.assertEqual(len(batch_result.failed_documents), 1)
        
        # Valid documents should be processed
        self.assertIn('valid1.xml', batch_result.successful_documents)
        self.assertIn('valid2.xml', batch_result.successful_documents)
        self.assertIn('invalid.xml', batch_result.failed_documents)
        
        print(f"✅ Partial failure recovery: {len(batch_result.successful_documents)}/3 documents processed")

    def test_backup_and_restore_mechanism(self):
        """Test document backup and restore on rollback"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create temporary document file
            doc_path = Path(temp_dir) / "test_theme.xml"
            doc_path.write_text(self.sample_ppt_theme)
            
            original_content = doc_path.read_text()
            
            try:
                with self.pipeline.create_transaction(backup_files=True) as transaction:
                    # Modify document
                    result = transaction.substitute_in_file(
                        str(doc_path),
                        {'brandPrimary': self.test_variables['brandPrimary']}
                    )
                    self.assertTrue(result.success)
                    
                    # Verify file was modified
                    modified_content = doc_path.read_text()
                    self.assertNotEqual(original_content, modified_content)
                    self.assertIn('FF0000', modified_content)
                    
                    # Force rollback
                    raise SubstitutionError("Test rollback")
                    
            except SubstitutionError:
                pass  # Expected
                
            # Verify file was restored to original state
            restored_content = doc_path.read_text()
            self.assertEqual(original_content, restored_content)
            self.assertNotIn('FF0000', restored_content)
            
        print("✅ Backup and restore: file successfully restored after rollback")


class TestProgressReportingAndCancellation(TestVariableSubstitutionPipeline):
    """Test progress tracking and cancellation mechanisms"""
    
    def test_progress_reporting_single_document(self):
        """Test progress reporting for single document processing"""
        progress_updates = []
        
        def progress_callback(progress: SubstitutionProgress):
            progress_updates.append({
                'stage': progress.current_stage,
                'progress': progress.progress_percentage,
                'variables_processed': progress.variables_processed,
                'timestamp': progress.timestamp
            })
            
        result = self.pipeline.substitute_variables_in_document(
            document_content=self.sample_ppt_theme,
            variables=self.test_variables,
            progress_callback=progress_callback
        )
        
        self.assertTrue(result.success)
        self.assertGreater(len(progress_updates), 0)
        
        # Verify progress progression
        self.assertEqual(progress_updates[0]['progress'], 0)  # Started at 0%
        self.assertEqual(progress_updates[-1]['progress'], 100)  # Ended at 100%
        
        # Verify stages are reported
        stages = [update['stage'] for update in progress_updates]
        expected_stages = ['parsing', 'resolving', 'applying', 'validating', 'complete']
        for stage in expected_stages:
            self.assertIn(stage, stages)
            
        print(f"✅ Progress reporting: {len(progress_updates)} updates across {len(set(stages))} stages")

    def test_progress_reporting_batch_processing(self):
        """Test progress reporting for batch document processing"""
        progress_updates = []
        
        def progress_callback(progress: SubstitutionProgress):
            progress_updates.append({
                'overall_progress': progress.overall_progress_percentage,
                'current_document': progress.current_document,
                'documents_completed': progress.documents_completed,
                'total_documents': progress.total_documents
            })
            
        documents = [
            ('doc1.xml', self.sample_ppt_theme, 'powerpoint_theme'),
            ('doc2.xml', self.sample_word_styles, 'word_styles'),
            ('doc3.xml', self.sample_excel_theme, 'excel_theme')
        ]
        
        batch_result = self.pipeline.substitute_variables_in_batch(
            documents=documents,
            variables=self.test_variables,
            progress_callback=progress_callback
        )
        
        self.assertTrue(batch_result.success)
        self.assertGreater(len(progress_updates), 0)
        
        # Verify batch progress tracking
        final_update = progress_updates[-1]
        self.assertEqual(final_update['overall_progress'], 100)
        self.assertEqual(final_update['documents_completed'], 3)
        self.assertEqual(final_update['total_documents'], 3)
        
        print(f"✅ Batch progress: tracked progress across {final_update['total_documents']} documents")

    def test_cancellation_mechanism(self):
        """Test operation cancellation via cancellation token"""
        cancellation_token = self.pipeline.create_cancellation_token()
        
        # Start long-running operation in separate thread
        def cancel_after_delay():
            time.sleep(0.1)  # Let operation start
            cancellation_token.cancel()
            
        cancel_thread = threading.Thread(target=cancel_after_delay)
        cancel_thread.start()
        
        # Create large variable set to slow down processing
        large_variables = {}
        for i in range(100):
            large_variables[f'var{i}'] = {
                'id': f'var{i}',
                'type': 'color',
                'value': f'{i:06X}',
                'xpath': f'//a:accent1//a:srgbClr[@test="{i}"]',
                'scope': 'test',
                'source': 'test'
            }
            
        result = self.pipeline.substitute_variables_in_document(
            document_content=self.sample_ppt_theme,
            variables=large_variables,
            cancellation_token=cancellation_token
        )
        
        cancel_thread.join()
        
        # Operation should be cancelled
        self.assertFalse(result.success)
        self.assertTrue(result.cancelled)
        self.assertIn('cancelled', str(result.errors[0]).lower())
        
        print("✅ Cancellation: operation successfully cancelled via token")

    def test_timeout_mechanism(self):
        """Test automatic timeout for long-running operations"""
        # Set very short timeout
        self.pipeline.set_operation_timeout(0.05)  # 50ms timeout
        
        # Create operation that will exceed timeout
        large_variables = {}
        for i in range(1000):  # Large number of variables
            large_variables[f'var{i}'] = {
                'id': f'var{i}',
                'type': 'color', 
                'value': f'{i:06X}',
                'xpath': f'//a:accent{(i%6)+1}//a:srgbClr',
                'scope': 'test',
                'source': 'test'
            }
            
        start_time = time.time()
        result = self.pipeline.substitute_variables_in_document(
            document_content=self.sample_ppt_theme,
            variables=large_variables
        )
        elapsed_time = time.time() - start_time
        
        # Should timeout quickly
        self.assertFalse(result.success)
        self.assertTrue(result.timed_out)
        self.assertLess(elapsed_time, 0.5)  # Should not take long to timeout
        
        print(f"✅ Timeout: operation timed out after {elapsed_time:.3f}s")


class TestValidationCheckpoints(TestVariableSubstitutionPipeline):
    """Test validation checkpoints throughout substitution process"""
    
    def test_pre_substitution_validation(self):
        """Test validation before substitution begins"""
        # Test with invalid XML
        invalid_xml = '<invalid><unclosed>xml</invalid>'
        
        result = self.pipeline.substitute_variables_in_document(
            document_content=invalid_xml,
            variables=self.test_variables,
            validation_checkpoints=['pre_substitution']
        )
        
        self.assertFalse(result.success)
        self.assertIn('xml_parsing', [error.error_type for error in result.errors])
        
        # Test with valid XML
        result = self.pipeline.substitute_variables_in_document(
            document_content=self.sample_ppt_theme,
            variables=self.test_variables,
            validation_checkpoints=['pre_substitution']
        )
        
        self.assertTrue(result.success)
        print("✅ Pre-substitution validation: XML parsing validated")

    def test_variable_validation_checkpoint(self):
        """Test variable validation checkpoint"""
        # Invalid variable (missing required fields)
        invalid_variables = {
            'invalidVar': {
                'id': 'invalidVar',
                # Missing 'type', 'value', 'xpath'
                'scope': 'org'
            }
        }
        
        result = self.pipeline.substitute_variables_in_document(
            document_content=self.sample_ppt_theme,
            variables=invalid_variables,
            validation_checkpoints=['variable_validation']
        )
        
        self.assertFalse(result.success)
        self.assertIn('variable_validation', [error.error_type for error in result.errors])
        
        print("✅ Variable validation checkpoint: invalid variables caught")

    def test_xpath_validation_checkpoint(self):
        """Test XPath expression validation"""
        invalid_xpath_variables = {
            'badXPath': {
                'id': 'badXPath',
                'type': 'color',
                'value': 'FF0000',
                'xpath': '//invalid[xpath[syntax',  # Invalid XPath
                'scope': 'org',
                'source': 'test'
            }
        }
        
        result = self.pipeline.substitute_variables_in_document(
            document_content=self.sample_ppt_theme,
            variables=invalid_xpath_variables,
            validation_checkpoints=['xpath_validation']
        )
        
        self.assertFalse(result.success)
        self.assertIn('xpath_validation', [error.error_type for error in result.errors])
        
        print("✅ XPath validation checkpoint: invalid XPath expressions caught")

    def test_post_substitution_validation(self):
        """Test validation after substitution is complete"""
        result = self.pipeline.substitute_variables_in_document(
            document_content=self.sample_ppt_theme,
            variables=self.test_variables,
            validation_checkpoints=['post_substitution']
        )
        
        self.assertTrue(result.success)
        
        # Verify validation checkpoints were executed
        self.assertIn('post_substitution', result.validation_checkpoints_passed)
        
        # Verify document integrity maintained
        updated_root = ET.fromstring(result.updated_content)
        self.assertIsNotNone(updated_root)
        
        print("✅ Post-substitution validation: document integrity verified")

    def test_comprehensive_validation_pipeline(self):
        """Test complete validation pipeline with all checkpoints"""
        all_checkpoints = [
            'pre_substitution',
            'variable_validation', 
            'xpath_validation',
            'dependency_resolution',
            'substitution_validation',
            'post_substitution'
        ]
        
        result = self.pipeline.substitute_variables_in_document(
            document_content=self.sample_ppt_theme,
            variables=self.test_variables,
            validation_checkpoints=all_checkpoints
        )
        
        self.assertTrue(result.success)
        
        # All checkpoints should pass
        for checkpoint in all_checkpoints:
            self.assertIn(checkpoint, result.validation_checkpoints_passed)
            
        print(f"✅ Comprehensive validation: all {len(all_checkpoints)} checkpoints passed")


class TestStressAndPerformance(TestVariableSubstitutionPipeline):
    """Test stress scenarios and performance benchmarks"""
    
    def test_large_document_processing(self):
        """Test processing of large OOXML documents"""
        # Generate large document with many elements
        large_theme_parts = [
            '<?xml version="1.0"?>',
            '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Large">',
            '  <a:themeElements>',
            '    <a:clrScheme name="Large">'
        ]
        
        # Add 500 color elements
        for i in range(500):
            color_val = f'{i:06X}'
            large_theme_parts.extend([
                f'      <a:accent{(i%6)+1}>',
                f'        <a:srgbClr val="{color_val}"/>',
                f'      </a:accent{(i%6)+1}>'
            ])
            
        large_theme_parts.extend([
            '    </a:clrScheme>',
            '  </a:themeElements>',
            '</a:theme>'
        ])
        
        large_document = '\n'.join(large_theme_parts)
        
        # Large variable set
        large_variables = {}
        for i in range(100):
            large_variables[f'color{i}'] = {
                'id': f'color{i}',
                'type': 'color',
                'value': f'{(i*100):06X}'[:6],
                'xpath': f'//a:accent{(i%6)+1}//a:srgbClr',
                'scope': 'test',
                'source': 'test'
            }
            
        start_time = time.time()
        result = self.pipeline.substitute_variables_in_document(
            document_content=large_document,
            variables=large_variables
        )
        processing_time = time.time() - start_time
        
        self.assertTrue(result.success)
        self.assertLess(processing_time, 10.0)  # Should complete within 10 seconds
        
        print(f"✅ Large document stress test: ~{len(large_document)} chars, {len(large_variables)} variables in {processing_time:.3f}s")

    def test_concurrent_batch_processing(self):
        """Test concurrent processing of multiple document batches"""
        # Create multiple batches
        batches = []
        for batch_id in range(5):
            batch_documents = [
                (f'batch{batch_id}_doc1.xml', self.sample_ppt_theme, 'powerpoint_theme'),
                (f'batch{batch_id}_doc2.xml', self.sample_word_styles, 'word_styles')
            ]
            batches.append(batch_documents)
            
        # Process batches concurrently
        import concurrent.futures
        
        def process_batch(batch_documents):
            return self.pipeline.substitute_variables_in_batch(
                documents=batch_documents,
                variables=self.test_variables,
                parallel_processing=True
            )
            
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(process_batch, batch) for batch in batches]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
        processing_time = time.time() - start_time
        
        # All batches should succeed
        for result in results:
            self.assertTrue(result.success)
            
        total_documents = sum(len(result.document_results) for result in results)
        print(f"✅ Concurrent processing: {total_documents} documents across {len(batches)} batches in {processing_time:.3f}s")

    def test_memory_efficiency(self):
        """Test memory efficiency with large datasets"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process many documents with streaming mode
        documents = []
        for i in range(50):
            documents.append((f'doc{i}.xml', self.sample_ppt_theme, 'powerpoint_theme'))
            
        result = self.pipeline.substitute_variables_in_batch(
            documents=documents,
            variables=self.test_variables,
            streaming_mode=True,  # Process one at a time to save memory
            parallel_processing=False
        )
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        self.assertTrue(result.success)
        self.assertLess(memory_increase, 100)  # Should not use more than 100MB additional
        
        print(f"✅ Memory efficiency: processed {len(documents)} documents with {memory_increase:.1f}MB memory increase")


class TestDocumentIntegrity(TestVariableSubstitutionPipeline):
    """Test document integrity maintenance throughout substitution"""
    
    def test_xml_structure_preservation(self):
        """Test XML document structure is preserved"""
        original_root = ET.fromstring(self.sample_ppt_theme)
        original_element_count = len(list(original_root.iter()))
        original_namespace_count = len(set(elem.tag.split('}')[0] + '}' if '}' in elem.tag else '' 
                                        for elem in original_root.iter()))
        
        result = self.pipeline.substitute_variables_in_document(
            document_content=self.sample_ppt_theme,
            variables=self.test_variables,
            preserve_structure=True
        )
        
        self.assertTrue(result.success)
        
        updated_root = ET.fromstring(result.updated_content)
        updated_element_count = len(list(updated_root.iter()))
        updated_namespace_count = len(set(elem.tag.split('}')[0] + '}' if '}' in elem.tag else ''
                                        for elem in updated_root.iter()))
        
        # Structure should be preserved
        self.assertEqual(original_element_count, updated_element_count)
        self.assertEqual(original_namespace_count, updated_namespace_count)
        
        print("✅ XML structure preservation: element count and namespaces preserved")

    def test_attribute_preservation(self):
        """Test element attributes are preserved during substitution"""
        # Create XML with many attributes
        xml_with_attributes = '''<?xml version="1.0"?>
        <a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" 
                 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
                 name="Test" version="1.0">
          <a:themeElements>
            <a:clrScheme name="Test" id="colorScheme1">
              <a:accent1 custom="true" priority="high">
                <a:srgbClr val="4472C4" lastClr="original"/>
              </a:accent1>
            </a:clrScheme>
          </a:themeElements>
        </a:theme>'''
        
        original_root = ET.fromstring(xml_with_attributes)
        original_attributes = {}
        for elem in original_root.iter():
            if elem.attrib:
                original_attributes[elem.tag] = dict(elem.attrib)
                
        result = self.pipeline.substitute_variables_in_document(
            document_content=xml_with_attributes,
            variables={'brandPrimary': self.test_variables['brandPrimary']},
            preserve_attributes=True
        )
        
        self.assertTrue(result.success)
        
        updated_root = ET.fromstring(result.updated_content)
        updated_attributes = {}
        for elem in updated_root.iter():
            if elem.attrib:
                updated_attributes[elem.tag] = dict(elem.attrib)
                
        # Most attributes should be preserved (except modified ones)
        for tag in original_attributes:
            if tag in updated_attributes:
                # Check non-value attributes are preserved
                for attr, value in original_attributes[tag].items():
                    if attr not in ['val', 'lastClr']:  # These may change
                        self.assertEqual(updated_attributes[tag].get(attr), value)
                        
        print("✅ Attribute preservation: non-target attributes preserved")

    def test_namespace_handling(self):
        """Test proper namespace handling during substitution"""
        # XML with multiple namespaces
        multi_ns_xml = '''<?xml version="1.0"?>
        <a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
                 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
          <a:themeElements>
            <a:clrScheme name="Multi">
              <a:accent1>
                <a:srgbClr val="4472C4"/>
              </a:accent1>
            </a:clrScheme>
          </a:themeElements>
          <r:relationships>
            <r:relationship id="rel1" target="theme.xml"/>
          </r:relationships>
        </a:theme>'''
        
        result = self.pipeline.substitute_variables_in_document(
            document_content=multi_ns_xml,
            variables={'brandPrimary': self.test_variables['brandPrimary']},
            preserve_namespaces=True
        )
        
        self.assertTrue(result.success)
        
        # Verify all namespaces preserved
        for ns_prefix in ['xmlns:a', 'xmlns:r', 'xmlns:p']:
            self.assertIn(ns_prefix, result.updated_content)
            
        # Verify namespace-prefixed elements preserved
        updated_root = ET.fromstring(result.updated_content)
        ns_elements = [elem.tag for elem in updated_root.iter() if '}' in elem.tag]
        self.assertGreater(len(ns_elements), 0)
        
        print("✅ Namespace handling: all namespaces and prefixed elements preserved")

    def test_comment_and_processing_instruction_preservation(self):
        """Test XML comments and processing instructions are preserved"""
        xml_with_comments = '''<?xml version="1.0" encoding="UTF-8"?>
        <?xml-stylesheet type="text/xsl" href="theme.xsl"?>
        <!-- StyleStack Theme Definition -->
        <a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Test">
          <!-- Color scheme definition -->
          <a:themeElements>
            <a:clrScheme name="Test">
              <!-- Primary brand color -->
              <a:accent1><a:srgbClr val="4472C4"/></a:accent1>
            </a:clrScheme>
          </a:themeElements>
          <!-- End theme elements -->
        </a:theme>
        <!-- End theme definition -->'''
        
        result = self.pipeline.substitute_variables_in_document(
            document_content=xml_with_comments,
            variables={'brandPrimary': self.test_variables['brandPrimary']},
            preserve_comments=True,
            preserve_processing_instructions=True
        )
        
        self.assertTrue(result.success)
        
        # Verify comments preserved
        self.assertIn('<!-- StyleStack Theme Definition -->', result.updated_content)
        self.assertIn('<!-- Color scheme definition -->', result.updated_content)
        self.assertIn('<!-- Primary brand color -->', result.updated_content)
        
        # Verify processing instruction preserved  
        self.assertIn('<?xml-stylesheet', result.updated_content)
        
        print("✅ Comment/PI preservation: XML comments and processing instructions preserved")


if __name__ == '__main__':
    # Configure test runner
    unittest.main(
        verbosity=2,
        testLoader=unittest.TestLoader(),
        warnings='ignore'  # Suppress ResourceWarning from tempfile
    )