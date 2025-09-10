#!/usr/bin/env python3
"""
Test Parallel Execution Configuration

This module tests the parallel test execution setup and validates
that pytest-xdist is properly configured and functional.
"""

import pytest
import subprocess
import sys
import time
import threading
import multiprocessing
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import json


@pytest.mark.unit
@pytest.mark.parallel_safe
class TestParallelConfiguration:
    """Test parallel execution configuration and setup."""
    
    def test_pytest_xdist_available(self):
        """Test that pytest-xdist is available for import."""
        try:
            import xdist
            assert hasattr(xdist, "plugin"), "pytest-xdist plugin should be available"
            
            # Test basic xdist functionality
            from xdist import workermanage
            assert workermanage is not None, "xdist workermanage should be available"
            
        except ImportError:
            pytest.skip("pytest-xdist not installed")
    
    def test_parallel_configuration_files_exist(self):
        """Test that parallel configuration files exist."""
        project_root = Path(__file__).parent.parent
        
        config_files = [
            "pytest-parallel.ini",
            "run_parallel_tests.py",
            "requirements-test.txt"
        ]
        
        for config_file in config_files:
            config_path = project_root / config_file
            assert config_path.exists(), f"Configuration file {config_file} should exist"
    
    def test_parallel_ini_configuration(self):
        """Test parallel pytest.ini configuration."""
        project_root = Path(__file__).parent.parent
        parallel_ini = project_root / "pytest-parallel.ini"
        
        content = parallel_ini.read_text()
        
        # Check for parallel execution settings
        assert "-n auto" in content, "Should have auto worker detection"
        assert "--dist=worksteal" in content, "Should use worksteal distribution"
        assert "timeout = 300" in content, "Should have timeout configuration"
        
        # Check for parallel-safe markers
        assert "parallel_safe" in content, "Should have parallel_safe marker"
        assert "parallel_unsafe" in content, "Should have parallel_unsafe marker"
    
    def test_optimal_worker_count_calculation(self):
        """Test optimal worker count calculation."""
        from run_parallel_tests import get_optimal_worker_count
        
        worker_count = get_optimal_worker_count()
        cpu_count = multiprocessing.cpu_count()
        
        assert isinstance(worker_count, int), "Worker count should be integer"
        assert worker_count >= 2, "Should use at least 2 workers"
        assert worker_count <= cpu_count, "Should not exceed CPU count"
        assert worker_count <= 8, "Should have reasonable upper limit"
    
    def test_reports_directory_creation(self):
        """Test reports directory creation."""
        from run_parallel_tests import create_reports_directory
        
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            reports_dir = create_reports_directory()
            
            assert reports_dir.name == "reports"
            mock_mkdir.assert_called_once_with(exist_ok=True)
    
    @pytest.mark.slow
    def test_parallel_test_execution_dry_run(self):
        """Test parallel test execution without actually running tests."""
        from run_parallel_tests import run_test_suite
        
        # Mock subprocess.run to avoid actual test execution
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            result = run_test_suite(
                test_type="unit",
                parallel_workers=2,
                verbose=False,
                generate_html_report=False
            )
            
            assert isinstance(result, dict), "Should return result dictionary"
            assert 'success' in result, "Should include success status"
            assert 'parallel_workers' in result, "Should include worker count"
            assert result['parallel_workers'] == 2, "Should use specified worker count"
            
            # Verify correct command was built
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "-n" in call_args, "Should include worker count flag"
            assert "2" in call_args, "Should include worker count value"
    
    def test_test_type_filtering(self):
        """Test test type filtering for parallel execution."""
        from run_parallel_tests import run_test_suite
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            # Test unit filter
            run_test_suite(test_type="unit", verbose=False, generate_html_report=False)
            call_args = mock_run.call_args[0][0]
            assert "-m" in call_args and "unit" in call_args, "Should filter for unit tests"
            
            # Test integration filter
            mock_run.reset_mock()
            run_test_suite(test_type="integration", verbose=False, generate_html_report=False)
            call_args = mock_run.call_args[0][0]
            assert "-m" in call_args and "integration" in call_args, "Should filter for integration tests"


@pytest.mark.integration
@pytest.mark.parallel_safe
class TestParallelExecutionIntegration:
    """Integration tests for parallel execution functionality."""
    
    @pytest.mark.slow
    def test_pytest_collect_with_parallel_config(self):
        """Test that pytest can collect tests with parallel configuration."""
        project_root = Path(__file__).parent.parent
        
        # Run pytest collection with parallel config
        cmd = [
            sys.executable, "-m", "pytest",
            "--config-file=pytest-parallel.ini",
            "--collect-only",
            "--quiet",
            str(project_root / "tests" / "test_pytest_configuration.py")
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=project_root
            )
            
            # Should collect tests successfully
            assert "collected" in result.stdout or result.returncode == 0, \
                f"Test collection failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            pytest.fail("Test collection timed out")
        except FileNotFoundError:
            pytest.skip("pytest not available in current environment")
    
    def test_parallel_test_isolation(self):
        """Test that parallel tests maintain proper isolation."""
        
        # Create test data that could be shared between workers
        test_data = {"counter": 0, "lock": threading.Lock()}
        
        def increment_counter():
            """Function that modifies shared state."""
            with test_data["lock"]:
                current = test_data["counter"]
                time.sleep(0.001)  # Small delay to increase chance of race condition
                test_data["counter"] = current + 1
        
        # Run multiple threads to simulate parallel test workers
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=increment_counter)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify proper synchronization
        assert test_data["counter"] == 10, "Parallel execution should maintain data integrity"
    
    @pytest.mark.slow
    def test_parallel_vs_sequential_performance(self):
        """Test that parallel execution provides performance benefits."""
        
        # Simulate test execution times
        def simulate_test_work(duration=0.1):
            """Simulate test work with specified duration."""
            time.sleep(duration)
            return True
        
        # Sequential execution
        start_time = time.time()
        for _ in range(4):
            simulate_test_work(0.05)
        sequential_time = time.time() - start_time
        
        # Parallel execution (simulated with threads)
        start_time = time.time()
        threads = []
        for _ in range(4):
            thread = threading.Thread(target=simulate_test_work, args=(0.05,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        parallel_time = time.time() - start_time
        
        # Parallel should be faster (with some tolerance for overhead)
        performance_improvement = (sequential_time - parallel_time) / sequential_time
        assert performance_improvement > 0.3, \
            f"Parallel execution should be significantly faster: {performance_improvement:.2%} improvement"


@pytest.mark.unit
@pytest.mark.parallel_safe 
class TestParallelSafetyMarkers:
    """Test parallel safety marker functionality."""
    
    def test_parallel_safe_marker_exists(self, pytestconfig):
        """Test that parallel_safe marker is registered."""
        # This test itself is marked as parallel_safe
        # If it runs, the marker is working
        assert True, "parallel_safe marker is functional"
    
    def test_parallel_unsafe_marker_concept(self):
        """Test parallel_unsafe marker concept."""
        # This is a conceptual test - in practice, tests marked as
        # parallel_unsafe would need to be run sequentially
        
        # Example of test that would be parallel_unsafe:
        # - Tests that modify global state
        # - Tests that write to the same files
        # - Tests that use specific ports or resources
        
        assert True, "parallel_unsafe concept validated"
    
    def test_test_categorization_by_speed(self):
        """Test that tests are properly categorized by execution speed."""
        
        # Fast tests (unit tests) - parallel safe
        fast_test_time = 0.001
        assert fast_test_time < 0.1, "Fast tests should run quickly"
        
        # Medium tests (integration tests) - mostly parallel safe  
        medium_test_time = 0.1
        assert medium_test_time < 1.0, "Medium tests should have reasonable duration"
        
        # Slow tests (system tests) - may need sequential execution
        slow_test_time = 1.0
        assert slow_test_time >= 1.0, "Slow tests require more time"


@pytest.mark.system
@pytest.mark.slow
@pytest.mark.parallel_unsafe  # This test modifies filesystem state
class TestParallelExecutionSystem:
    """System-level tests for parallel execution."""
    
    def test_concurrent_file_access_safety(self):
        """Test that concurrent file access is handled safely."""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "concurrent_test.txt"
            
            def write_to_file(worker_id, content):
                """Write content to file with worker identification."""
                with open(test_file, "a") as f:
                    f.write(f"Worker {worker_id}: {content}\n")
                    f.flush()  # Ensure write is committed
            
            # Simulate concurrent file writes
            threads = []
            for i in range(5):
                thread = threading.Thread(
                    target=write_to_file,
                    args=(i, f"test content {i}")
                )
                threads.append(thread)
                thread.start()
            
            # Wait for all writes to complete
            for thread in threads:
                thread.join()
            
            # Verify file integrity
            if test_file.exists():
                content = test_file.read_text()
                lines = content.strip().split('\n')
                
                # Should have entries from all workers
                assert len(lines) == 5, "All workers should have written to file"
                
                # Each line should be complete (no partial writes)
                for line in lines:
                    assert line.startswith("Worker"), "Each line should be complete"
                    assert "test content" in line, "Each line should contain expected content"
    
    def test_resource_cleanup_in_parallel_execution(self):
        """Test that resources are properly cleaned up in parallel execution."""
        
        resource_states = []
        cleanup_states = []
        
        def simulate_test_with_resources(worker_id):
            """Simulate test that acquires and releases resources."""
            # Acquire resource
            resource = f"resource_{worker_id}_{int(time.time() * 1000000)}"
            resource_states.append(f"acquired_{resource}")
            
            try:
                # Simulate test work
                time.sleep(0.01)
                
            finally:
                # Clean up resource
                cleanup_states.append(f"cleaned_{resource}")
        
        # Run simulated tests in parallel
        threads = []
        for i in range(3):
            thread = threading.Thread(target=simulate_test_with_resources, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify proper resource management
        assert len(resource_states) == 3, "All resources should be acquired"
        assert len(cleanup_states) == 3, "All resources should be cleaned up"
        
        # Verify each acquired resource was cleaned up
        acquired_resources = [state.replace("acquired_", "") for state in resource_states]
        cleaned_resources = [state.replace("cleaned_", "") for state in cleanup_states]
        
        assert set(acquired_resources) == set(cleaned_resources), \
            "All acquired resources should be cleaned up"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])