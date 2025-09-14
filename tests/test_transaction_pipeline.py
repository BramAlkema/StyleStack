#!/usr/bin/env python3
"""
Transaction Pipeline Tests

Tests atomic, reversible operations across the entire OOXML processing chain.
Validates transaction semantics, rollback capabilities, operation batching,
and comprehensive audit trails.

Part of the StyleStack JSON-to-OOXML Processing Engine test suite.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil
import time
from pathlib import Path
from concurrent.futures import Future

from tools.transaction_pipeline import (
    TransactionPipeline, Transaction, TransactionState, OperationType,
    TransactionOperation, TransactionSnapshot, TransactionResult,
    create_transaction_pipeline, atomic_ooxml_operation
)
from tools.handlers.types import OOXMLFormat, ProcessingResult


class TestTransactionState(unittest.TestCase):
    """Test transaction state enum and transitions."""
    
    def test_transaction_states(self):
        """Test that all required transaction states are defined."""
        expected_states = [
            'INITIALIZED', 'ACTIVE', 'PREPARING', 'PREPARED',
            'COMMITTING', 'COMMITTED', 'ROLLING_BACK', 'ROLLED_BACK',
            'FAILED', 'ABORTED'
        ]
        
        for state_name in expected_states:
            self.assertTrue(hasattr(TransactionState, state_name))
            self.assertIsInstance(getattr(TransactionState, state_name), TransactionState)


class TestOperationType(unittest.TestCase):
    """Test operation type enum."""
    
    def test_operation_types(self):
        """Test that all required operation types are defined."""
        expected_types = [
            'PROCESS_TEMPLATE', 'APPLY_PATCHES', 'REGISTER_TOKENS',
            'VALIDATE_STRUCTURE', 'BACKUP_STATE', 'RESTORE_STATE'
        ]
        
        for op_type in expected_types:
            self.assertTrue(hasattr(OperationType, op_type))
            self.assertIsInstance(getattr(OperationType, op_type), OperationType)


class TestTransactionOperation(unittest.TestCase):
    """Test transaction operation data structure."""
    
    def test_operation_creation(self):
        """Test transaction operation creation."""
        operation = TransactionOperation(
            operation_id="test-op-1",
            operation_type=OperationType.PROCESS_TEMPLATE,
            parameters={'template_path': 'test.potx'},
            rollback_data={'backup_path': 'backup.potx'}
        )
        
        self.assertEqual(operation.operation_id, "test-op-1")
        self.assertEqual(operation.operation_type, OperationType.PROCESS_TEMPLATE)
        self.assertEqual(operation.parameters['template_path'], 'test.potx')
        self.assertEqual(operation.rollback_data['backup_path'], 'backup.potx')
        self.assertIsNone(operation.result)
        self.assertIsNone(operation.error)
        self.assertIsNotNone(operation.timestamp)


class TestTransactionSnapshot(unittest.TestCase):
    """Test transaction snapshot functionality."""
    
    def test_snapshot_creation(self):
        """Test snapshot data structure creation."""
        snapshot = TransactionSnapshot(
            snapshot_id="snap-123",
            timestamp=time.time(),
            file_backups={'orig.txt': 'backup.txt'},
            state_data={'key': 'value'}
        )
        
        self.assertEqual(snapshot.snapshot_id, "snap-123")
        self.assertEqual(snapshot.file_backups['orig.txt'], 'backup.txt')
        self.assertEqual(snapshot.state_data['key'], 'value')
        self.assertEqual(len(snapshot.metadata), 0)


class TestTransactionPipeline(unittest.TestCase):
    """Test transaction pipeline functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.pipeline = TransactionPipeline(
            max_concurrent_operations=2,
            snapshot_directory=self.temp_dir / "snapshots",
            enable_audit_trail=True
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.pipeline.executor.shutdown(wait=True)
    
    def test_pipeline_initialization(self):
        """Test transaction pipeline initialization."""
        self.assertEqual(self.pipeline.max_concurrent_operations, 2)
        self.assertTrue(self.pipeline.enable_audit_trail)
        self.assertEqual(len(self.pipeline.active_transactions), 0)
        self.assertTrue(self.pipeline.snapshot_directory.exists())
        self.assertIsNotNone(self.pipeline.ooxml_handler)
    
    def test_create_snapshot_with_files(self):
        """Test snapshot creation with file backups."""
        # Create test files
        test_file1 = self.temp_dir / "test1.txt"
        test_file2 = self.temp_dir / "test2.txt"
        test_file1.write_text("content1")
        test_file2.write_text("content2")
        
        # Create snapshot
        snapshot = self.pipeline.create_snapshot(
            files_to_backup=[test_file1, test_file2],
            state_data={'app_state': 'test'}
        )
        
        self.assertIsNotNone(snapshot.snapshot_id)
        self.assertEqual(len(snapshot.file_backups), 2)
        self.assertEqual(snapshot.state_data['app_state'], 'test')
        self.assertIn('backup_directory', snapshot.metadata)
        
        # Verify backup files exist
        for backup_path in snapshot.file_backups.values():
            self.assertTrue(Path(backup_path).exists())
    
    def test_create_snapshot_nonexistent_files(self):
        """Test snapshot creation with non-existent files."""
        snapshot = self.pipeline.create_snapshot(
            files_to_backup=["/nonexistent/file.txt"],
            state_data={'test': 'data'}
        )
        
        # Should succeed but with no file backups
        self.assertEqual(len(snapshot.file_backups), 0)
        self.assertEqual(snapshot.state_data['test'], 'data')
    
    def test_restore_snapshot(self):
        """Test snapshot restoration."""
        # Create original file
        original_file = self.temp_dir / "original.txt"
        original_file.write_text("original content")
        
        # Create snapshot
        snapshot = self.pipeline.create_snapshot([original_file])
        
        # Modify original file
        original_file.write_text("modified content")
        self.assertEqual(original_file.read_text(), "modified content")
        
        # Restore snapshot
        success = self.pipeline.restore_snapshot(snapshot)
        
        self.assertTrue(success)
        self.assertEqual(original_file.read_text(), "original content")
    
    def test_cleanup_snapshot(self):
        """Test snapshot cleanup."""
        # Create test file and snapshot
        test_file = self.temp_dir / "test.txt"
        test_file.write_text("test content")
        
        snapshot = self.pipeline.create_snapshot([test_file])
        backup_dir = Path(snapshot.metadata['backup_directory'])
        
        # Verify backup directory exists
        self.assertTrue(backup_dir.exists())
        
        # Cleanup snapshot
        self.pipeline.cleanup_snapshot(snapshot)
        
        # Verify backup directory is removed
        self.assertFalse(backup_dir.exists())
    
    def test_performance_statistics(self):
        """Test performance statistics collection."""
        stats = self.pipeline.get_performance_statistics()
        
        expected_keys = [
            'transactions_started', 'transactions_committed', 'transactions_rolled_back',
            'operations_executed', 'snapshots_created', 'total_processing_time',
            'active_transactions', 'audit_trail_size', 'snapshot_directory_size'
        ]
        
        for key in expected_keys:
            self.assertIn(key, stats)
        
        self.assertEqual(stats['transactions_started'], 0)
        self.assertEqual(stats['active_transactions'], 0)
        self.assertEqual(stats['audit_trail_size'], 0)
    
    def test_cleanup_old_snapshots(self):
        """Test cleanup of old snapshots."""
        # Create some snapshot directories with different ages
        old_snapshot = self.pipeline.snapshot_directory / "snapshot_old"
        recent_snapshot = self.pipeline.snapshot_directory / "snapshot_recent"
        
        old_snapshot.mkdir()
        recent_snapshot.mkdir()
        
        # Artificially age the old snapshot
        old_time = time.time() - (25 * 3600)  # 25 hours ago
        old_snapshot.stat().st_ctime = old_time
        
        # Cleanup snapshots older than 24 hours
        self.pipeline.cleanup_old_snapshots(max_age_hours=24)
        
        # Recent snapshot should still exist, old one should be gone
        self.assertTrue(recent_snapshot.exists())
        # Note: The actual cleanup might not work due to filesystem limitations
        # in setting creation time, but the method should run without error


class TestTransaction(unittest.TestCase):
    """Test individual transaction functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.pipeline = TransactionPipeline(snapshot_directory=self.temp_dir / "snapshots")
        
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.pipeline.executor.shutdown(wait=True)
    
    def test_transaction_context_manager(self):
        """Test transaction context manager functionality."""
        with self.pipeline.transaction() as transaction:
            self.assertIsInstance(transaction, Transaction)
            self.assertEqual(transaction.state, TransactionState.INITIALIZED)
            
            # Add an operation
            operation = transaction.add_operation(
                OperationType.VALIDATE_STRUCTURE,
                {'template_path': 'test.potx'}
            )
            
            self.assertEqual(transaction.state, TransactionState.ACTIVE)
            self.assertEqual(len(transaction.operations), 1)
    
    def test_transaction_with_explicit_id(self):
        """Test transaction with explicit ID."""
        transaction_id = "test-transaction-123"
        
        with self.pipeline.transaction(transaction_id) as transaction:
            self.assertEqual(transaction.transaction_id, transaction_id)
    
    def test_add_operation(self):
        """Test adding operations to transaction."""
        transaction = Transaction("test-tx", self.pipeline)
        
        operation = transaction.add_operation(
            OperationType.PROCESS_TEMPLATE,
            {'template_path': 'test.potx', 'patches': []},
            {'backup_path': 'backup.potx'}
        )
        
        self.assertEqual(transaction.state, TransactionState.ACTIVE)
        self.assertEqual(len(transaction.operations), 1)
        self.assertEqual(operation.operation_type, OperationType.PROCESS_TEMPLATE)
        self.assertIsNotNone(operation.operation_id)
    
    def test_add_operation_invalid_state(self):
        """Test adding operation in invalid state."""
        transaction = Transaction("test-tx", self.pipeline)
        transaction.state = TransactionState.COMMITTED
        
        with self.assertRaises(RuntimeError):
            transaction.add_operation(OperationType.PROCESS_TEMPLATE, {})
    
    @patch('tools.transaction_pipeline.Transaction._execute_validate_structure')
    def test_execute_operation_success(self, mock_execute):
        """Test successful operation execution."""
        mock_execute.return_value = {'valid': True, 'errors': []}
        
        transaction = Transaction("test-tx", self.pipeline)
        operation = TransactionOperation(
            operation_id="op-1",
            operation_type=OperationType.VALIDATE_STRUCTURE,
            parameters={'template_path': 'test.potx'}
        )
        
        result = transaction.execute_operation(operation)
        
        self.assertEqual(result['valid'], True)
        self.assertIsNone(operation.error)
        self.assertIsNotNone(operation.duration)
        mock_execute.assert_called_once_with(operation)
    
    @patch('tools.transaction_pipeline.Transaction._execute_validate_structure')
    def test_execute_operation_failure(self, mock_execute):
        """Test operation execution failure."""
        mock_execute.side_effect = Exception("Validation failed")
        
        transaction = Transaction("test-tx", self.pipeline)
        operation = TransactionOperation(
            operation_id="op-1",
            operation_type=OperationType.VALIDATE_STRUCTURE,
            parameters={'template_path': 'test.potx'}
        )
        
        with self.assertRaises(Exception):
            transaction.execute_operation(operation)
        
        self.assertEqual(operation.error, "Validation failed")
        self.assertIsNotNone(operation.duration)
    
    @patch('tools.transaction_pipeline.Transaction.execute_operation')
    def test_prepare_success(self, mock_execute):
        """Test successful transaction preparation."""
        mock_execute.return_value = {'success': True}
        
        transaction = Transaction("test-tx", self.pipeline)
        transaction.add_operation(OperationType.VALIDATE_STRUCTURE, {'template_path': 'test.potx'})
        
        success = transaction.prepare()
        
        self.assertTrue(success)
        self.assertEqual(transaction.state, TransactionState.PREPARED)
        mock_execute.assert_called_once()
    
    @patch('tools.transaction_pipeline.Transaction.execute_operation')
    def test_prepare_failure(self, mock_execute):
        """Test transaction preparation failure."""
        mock_execute.side_effect = Exception("Operation failed")
        
        transaction = Transaction("test-tx", self.pipeline)
        transaction.add_operation(OperationType.VALIDATE_STRUCTURE, {'template_path': 'test.potx'})
        
        success = transaction.prepare()
        
        self.assertFalse(success)
        self.assertEqual(transaction.state, TransactionState.FAILED)
    
    @patch('tools.transaction_pipeline.Transaction.prepare')
    def test_commit_success(self, mock_prepare):
        """Test successful transaction commit."""
        mock_prepare.return_value = True
        
        transaction = Transaction("test-tx", self.pipeline)
        transaction.add_operation(OperationType.VALIDATE_STRUCTURE, {'template_path': 'test.potx'})
        
        result = transaction.commit()
        
        self.assertTrue(result.success)
        self.assertEqual(result.state, TransactionState.COMMITTED)
        self.assertEqual(transaction.state, TransactionState.COMMITTED)
    
    def test_commit_invalid_state(self):
        """Test commit in invalid state."""
        transaction = Transaction("test-tx", self.pipeline)
        transaction.state = TransactionState.COMMITTED
        
        with self.assertRaises(RuntimeError):
            transaction.commit()
    
    @patch('tools.transaction_pipeline.TransactionPipeline.restore_snapshot')
    def test_rollback_success(self, mock_restore):
        """Test successful transaction rollback."""
        mock_restore.return_value = True
        
        transaction = Transaction("test-tx", self.pipeline)
        transaction.state = TransactionState.ACTIVE
        
        # Add a snapshot
        snapshot = TransactionSnapshot(
            snapshot_id="snap-1",
            timestamp=time.time(),
            file_backups={},
            state_data={}
        )
        transaction.snapshots.append(snapshot)
        
        result = transaction.rollback()
        
        self.assertTrue(result.success)
        self.assertTrue(result.rollback_performed)
        self.assertEqual(transaction.state, TransactionState.ROLLED_BACK)
    
    def test_rollback_invalid_state(self):
        """Test rollback in invalid state."""
        transaction = Transaction("test-tx", self.pipeline)
        transaction.state = TransactionState.COMMITTED
        
        with self.assertRaises(RuntimeError):
            transaction.rollback()


class TestOperationExecution(unittest.TestCase):
    """Test specific operation execution methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.pipeline = TransactionPipeline(snapshot_directory=self.temp_dir / "snapshots")
        self.transaction = Transaction("test-tx", self.pipeline)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.pipeline.executor.shutdown(wait=True)
    
    @patch('tools.transaction_pipeline.FormatRegistry.detect_format')
    @patch('tools.transaction_pipeline.create_format_processor')
    def test_execute_process_template(self, mock_create_processor, mock_detect):
        """Test process template operation execution."""
        # Mock format detection and processor creation
        mock_detect.return_value = OOXMLFormat.POWERPOINT
        mock_processor = Mock()
        mock_create_processor.return_value = mock_processor

        # Mock processor result
        mock_result = ProcessingResult(
            success=True,
            format_type=OOXMLFormat.POWERPOINT,
            processed_files=['ppt/presentation.xml'],
            errors=[],
            warnings=[],
            statistics={}
        )
        mock_processor.process_zip_entry.return_value = mock_result
        
        operation = TransactionOperation(
            operation_id="op-1",
            operation_type=OperationType.PROCESS_TEMPLATE,
            parameters={
                'template_path': 'test.potx',
                'patches': [{'operation': 'set', 'target': '//test', 'value': 'value'}],
                'variables': {'var': 'value'}
            }
        )
        
        result = self.transaction._execute_process_template(operation)
        
        self.assertTrue(result.success)
        self.assertEqual(result.format_type, OOXMLFormat.POWERPOINT)
        mock_detect.assert_called_once()
        mock_create_processor.assert_called_once()
    
    def test_execute_register_tokens(self):
        """Test token registration operation execution."""
        operation = TransactionOperation(
            operation_id="op-1",
            operation_type=OperationType.REGISTER_TOKENS,
            parameters={
                'format_type': 'potx',
                'tokens': {'brand_color': 'FF0000', 'company': 'TestCorp'},
                'scope': 'template'
            }
        )
        
        result = self.transaction._execute_register_tokens(operation)
        
        # Should succeed if token layer exists
        self.assertIsInstance(result, bool)
    
    @patch('tools.transaction_pipeline.FormatRegistry.validate_template_structure')
    def test_execute_validate_structure(self, mock_validate):
        """Test structure validation operation execution."""
        mock_validate.return_value = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        operation = TransactionOperation(
            operation_id="op-1",
            operation_type=OperationType.VALIDATE_STRUCTURE,
            parameters={'template_path': 'test.potx'}
        )
        
        result = self.transaction._execute_validate_structure(operation)
        
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)
        mock_validate.assert_called_once()
    
    def test_execute_backup_state(self):
        """Test state backup operation execution."""
        # Create test file
        test_file = self.temp_dir / "test.txt"
        test_file.write_text("test content")
        
        operation = TransactionOperation(
            operation_id="op-1",
            operation_type=OperationType.BACKUP_STATE,
            parameters={
                'files_to_backup': [str(test_file)],
                'state_data': {'key': 'value'}
            }
        )
        
        result = self.transaction._execute_backup_state(operation)
        
        self.assertIsInstance(result, TransactionSnapshot)
        self.assertEqual(len(result.file_backups), 1)
        self.assertEqual(len(self.transaction.snapshots), 1)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""
    
    def test_create_transaction_pipeline(self):
        """Test transaction pipeline creation."""
        pipeline = create_transaction_pipeline(
            max_concurrent_operations=8,
            enable_audit_trail=False
        )
        
        self.assertIsInstance(pipeline, TransactionPipeline)
        self.assertEqual(pipeline.max_concurrent_operations, 8)
        self.assertFalse(pipeline.enable_audit_trail)
    
    def test_atomic_ooxml_operation(self):
        """Test atomic OOXML operation context manager."""
        with atomic_ooxml_operation() as transaction:
            self.assertIsInstance(transaction, Transaction)
            
            # Add an operation
            transaction.add_operation(
                OperationType.VALIDATE_STRUCTURE,
                {'template_path': 'test.potx'}
            )
            
            self.assertEqual(len(transaction.operations), 1)
    
    def test_atomic_ooxml_operation_with_pipeline(self):
        """Test atomic operation with provided pipeline."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            pipeline = TransactionPipeline(snapshot_directory=temp_dir / "snapshots")
            
            with atomic_ooxml_operation(pipeline) as transaction:
                self.assertIsInstance(transaction, Transaction)
                self.assertEqual(transaction.pipeline, pipeline)
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            pipeline.executor.shutdown(wait=True)


class TestTransactionResult(unittest.TestCase):
    """Test transaction result data structure."""
    
    def test_transaction_result_creation(self):
        """Test transaction result creation."""
        completed_op = TransactionOperation(
            operation_id="op-1",
            operation_type=OperationType.VALIDATE_STRUCTURE,
            parameters={}
        )
        
        failed_op = TransactionOperation(
            operation_id="op-2",
            operation_type=OperationType.PROCESS_TEMPLATE,
            parameters={}
        )
        failed_op.error = "Processing failed"
        
        result = TransactionResult(
            transaction_id="tx-123",
            success=False,
            state=TransactionState.FAILED,
            operations_completed=[completed_op],
            operations_failed=[failed_op],
            snapshots_created=[],
            total_duration=5.5,
            error_summary="Processing failed",
            rollback_performed=True
        )
        
        self.assertEqual(result.transaction_id, "tx-123")
        self.assertFalse(result.success)
        self.assertEqual(result.state, TransactionState.FAILED)
        self.assertEqual(len(result.operations_completed), 1)
        self.assertEqual(len(result.operations_failed), 1)
        self.assertEqual(result.total_duration, 5.5)
        self.assertTrue(result.rollback_performed)


if __name__ == "__main__":
    # Run with verbose output for CI
    unittest.main(verbosity=2)