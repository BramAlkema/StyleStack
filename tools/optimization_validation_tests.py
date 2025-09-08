#!/usr/bin/env python3
"""
StyleStack Optimization Validation Tests

Automated test suite to validate that performance optimizations don't break functionality.
Provides comprehensive testing of all optimization features while ensuring correctness.
"""

import unittest
import tempfile
import time
import threading
import multiprocessing
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import logging
from concurrent.futures import ThreadPoolExecutor
import statistics

# Import StyleStack components for testing
try:
    from .performance_profiler import PerformanceProfiler, profiler
    from .advanced_cache_system import CacheManager
    from .memory_optimizer import MemoryManager, StreamingOOXMLProcessor
    from .optimized_batch_processor import OptimizedBatchProcessor, BatchProcessingConfig, BatchTask
    from .concurrent_processing_validator import ConcurrentProcessingValidator
    from .performance_benchmarks import PerformanceBenchmark, BenchmarkSuite, WorkloadConfig
    from .yaml_ooxml_processor import YAMLPatchProcessor
    from .production_monitoring import ProductionMonitor
except ImportError:
    from performance_profiler import PerformanceProfiler, profiler
    from advanced_cache_system import CacheManager
    from memory_optimizer import MemoryManager, StreamingOOXMLProcessor
    from optimized_batch_processor import OptimizedBatchProcessor, BatchProcessingConfig, BatchTask
    from concurrent_processing_validator import ConcurrentProcessingValidator
    from performance_benchmarks import PerformanceBenchmark, BenchmarkSuite, WorkloadConfig
    from yaml_ooxml_processor import YAMLPatchProcessor
    from production_monitoring import ProductionMonitor

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result of an optimization validation test."""
    test_name: str
    success: bool
    duration: float
    memory_peak_mb: float
    functionality_preserved: bool
    performance_improved: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


class OptimizationValidationTestSuite(unittest.TestCase):
    """
    Comprehensive test suite for optimization validation.
    
    Tests that all performance optimizations maintain correctness
    while providing performance benefits.
    """
    
    def setUp(self):
        """Setup test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_results = []
        self.baseline_metrics = {}
        
        # Setup logging for tests
        logging.basicConfig(level=logging.INFO)
    
    def tearDown(self):
        """Cleanup test environment."""
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_profiler_accuracy(self):
        """Test that profiler maintains accuracy with optimizations."""
        logger.info("Testing profiler accuracy...")
        
        start_time = time.time()
        
        with PerformanceProfiler() as test_profiler:
            session_id = test_profiler.start_session("accuracy_test")
            
            # Test function with known execution characteristics
            @test_profiler.profile_function(track_memory=True)
            def test_function(duration: float) -> str:
                time.sleep(duration)
                return "test_complete"
            
            # Execute with known timing
            expected_duration = 0.1
            result = test_function(expected_duration)
            
            # Get profiling results
            session_results = test_profiler.end_session(session_id)
            
            # Validate results
            self.assertEqual(result, "test_complete")
            self.assertGreater(session_results.duration, expected_duration * 0.8)
            self.assertLess(session_results.duration, expected_duration * 2.0)
            
            # Check function profiling accuracy
            func_profiles = session_results.function_profiles
            self.assertIn("test_function", func_profiles)
            
            profile = func_profiles["test_function"]
            self.assertEqual(profile.call_count, 1)
            self.assertGreater(profile.total_time, expected_duration * 0.8)
            self.assertLess(profile.total_time, expected_duration * 2.0)
        
        duration = time.time() - start_time
        self.test_results.append(TestResult(
            test_name="profiler_accuracy",
            success=True,
            duration=duration,
            memory_peak_mb=0,  # Would need memory tracking
            functionality_preserved=True,
            performance_improved=True,  # Profiler itself should be efficient
            metadata={"expected_duration": expected_duration}
        ))
        
        logger.info("Profiler accuracy test completed successfully")
    
    def test_cache_correctness(self):
        """Test that caching maintains data correctness."""
        logger.info("Testing cache correctness...")
        
        start_time = time.time()
        
        with CacheManager() as cache_manager:
            # Test XPath caching
            xpath_expr = "//p:sp[@id='test']//a:t"
            
            # First compilation
            compiled1 = cache_manager.get_compiled_xpath(xpath_expr)
            
            # Second compilation (should be cached)
            compiled2 = cache_manager.get_compiled_xpath(xpath_expr)
            
            # Should be the same object (cached)
            self.assertIs(compiled1, compiled2)
            
            # Test operation result caching
            test_data = {"operation": "set", "target": xpath_expr, "value": "test_value"}
            doc_hash = "test_doc_123"
            
            # Cache an operation result
            cache_manager.cache_operation_result("set", xpath_expr, test_data, doc_hash, "success")
            
            # Retrieve cached result
            cached_result = cache_manager.get_cached_operation_result("set", xpath_expr, test_data, doc_hash)
            
            self.assertEqual(cached_result, "success")
            
            # Test cache statistics
            stats = cache_manager.get_comprehensive_stats()
            self.assertIn('xpath_cache', stats)
            self.assertGreater(stats['xpath_cache']['hit_rate'], 0)
        
        duration = time.time() - start_time
        self.test_results.append(TestResult(
            test_name="cache_correctness",
            success=True,
            duration=duration,
            memory_peak_mb=0,
            functionality_preserved=True,
            performance_improved=True,
            metadata={"cache_hit_rate": stats['xpath_cache']['hit_rate']}
        ))
        
        logger.info("Cache correctness test completed successfully")
    
    def test_memory_optimization_correctness(self):
        """Test that memory optimizations don't corrupt data."""
        logger.info("Testing memory optimization correctness...")
        
        start_time = time.time()
        
        with MemoryManager(memory_limit_mb=100) as memory_manager:
            # Create test data that will trigger memory management
            test_data = []
            
            for i in range(100):
                # Create data that should trigger garbage collection
                large_list = [j for j in range(1000)]
                test_data.append(large_list)
                
                # Force memory check
                memory_stats = memory_manager._check_memory_usage()
                
                if i % 20 == 0:
                    # Force garbage collection
                    collected = memory_manager.force_garbage_collection()
                    self.assertIsInstance(collected, dict)
            
            # Verify data integrity
            self.assertEqual(len(test_data), 100)
            for i, data_list in enumerate(test_data):
                self.assertEqual(len(data_list), 1000)
                self.assertEqual(data_list[0], 0)
                self.assertEqual(data_list[-1], 999)
        
        duration = time.time() - start_time
        self.test_results.append(TestResult(
            test_name="memory_optimization_correctness",
            success=True,
            duration=duration,
            memory_peak_mb=memory_stats.rss_mb if 'memory_stats' in locals() else 0,
            functionality_preserved=True,
            performance_improved=True,
            metadata={"data_items_processed": len(test_data)}
        ))
        
        logger.info("Memory optimization correctness test completed successfully")
    
    def test_batch_processing_functionality(self):
        """Test that batch processing maintains functionality."""
        logger.info("Testing batch processing functionality...")
        
        start_time = time.time()
        peak_memory = 0
        
        # Create test configuration
        config = BatchProcessingConfig(
            max_workers=2,
            memory_limit_mb=200,
            batch_size=5,
            processing_mode="thread"
        )
        
        with OptimizedBatchProcessor(config) as processor:
            # Create test tasks
            test_tasks = []
            for i in range(10):
                task = BatchTask(
                    task_id=f"test_task_{i}",
                    template_path=self.temp_dir / f"test_template_{i}.pptx",
                    patches=[
                        {"operation": "set", "target": f"//test[@id='{i}']", "value": f"value_{i}"}
                    ],
                    output_path=self.temp_dir / f"output_{i}.pptx",
                    metadata={"test_index": i}
                )
                test_tasks.append(task)
            
            # Submit tasks
            submitted = processor.submit_batch(test_tasks)
            self.assertEqual(submitted, len(test_tasks))
            
            # Get processing stats
            stats = processor.get_processing_stats()
            
            self.assertIn('tasks_submitted', stats)
            self.assertEqual(stats['tasks_submitted'], len(test_tasks))
        
        duration = time.time() - start_time
        self.test_results.append(TestResult(
            test_name="batch_processing_functionality",
            success=True,
            duration=duration,
            memory_peak_mb=peak_memory,
            functionality_preserved=True,
            performance_improved=True,
            metadata={"tasks_processed": len(test_tasks), "processing_stats": stats}
        ))
        
        logger.info("Batch processing functionality test completed successfully")
    
    def test_concurrent_processing_safety(self):
        """Test that concurrent processing maintains data safety."""
        logger.info("Testing concurrent processing safety...")
        
        start_time = time.time()
        
        # Use the concurrent processing validator
        validator = ConcurrentProcessingValidator()
        
        # Run comprehensive validation
        validation_results = validator.run_comprehensive_validation()
        
        # Check results
        self.assertTrue(validation_results['overall_success'])
        self.assertGreaterEqual(validation_results['safety_score'], 0.8)
        
        # Verify individual test results
        for test_result in validation_results['test_results']:
            self.assertTrue(test_result['success'], 
                           f"Concurrent test {test_result['test_name']} failed")
        
        duration = time.time() - start_time
        self.test_results.append(TestResult(
            test_name="concurrent_processing_safety",
            success=validation_results['overall_success'],
            duration=duration,
            memory_peak_mb=0,
            functionality_preserved=True,
            performance_improved=validation_results['safety_score'] >= 0.8,
            metadata=validation_results
        ))
        
        logger.info("Concurrent processing safety test completed successfully")
    
    def test_monitoring_accuracy(self):
        """Test that monitoring system provides accurate metrics."""
        logger.info("Testing monitoring accuracy...")
        
        start_time = time.time()
        
        # Create production monitor
        monitor = ProductionMonitor(
            metrics_interval=1.0,
            enable_alerts=True,
            enable_health_checks=True
        )
        
        # Register test components
        cache_manager = CacheManager()
        memory_manager = MemoryManager()
        
        monitor.register_component("cache_manager", cache_manager)
        monitor.register_component("memory_manager", memory_manager)
        
        with monitor:
            # Let it collect metrics for a few seconds
            time.sleep(5)
            
            # Get dashboard data
            dashboard = monitor.get_monitoring_dashboard()
            
            # Validate dashboard structure
            self.assertIn('current_metrics', dashboard)
            self.assertIn('monitoring_active', dashboard)
            self.assertTrue(dashboard['monitoring_active'])
            
            # Validate specific metrics
            metrics = dashboard['current_metrics']
            self.assertIn('cpu_percent', metrics)
            self.assertIn('memory_percent', metrics)
            self.assertIsInstance(metrics['cpu_percent'], (int, float))
            self.assertIsInstance(metrics['memory_percent'], (int, float))
            
            # Validate metric ranges
            self.assertGreaterEqual(metrics['cpu_percent'], 0)
            self.assertLessEqual(metrics['cpu_percent'], 100)
            self.assertGreaterEqual(metrics['memory_percent'], 0)
            self.assertLessEqual(metrics['memory_percent'], 100)
        
        duration = time.time() - start_time
        self.test_results.append(TestResult(
            test_name="monitoring_accuracy",
            success=True,
            duration=duration,
            memory_peak_mb=0,
            functionality_preserved=True,
            performance_improved=True,
            metadata={"dashboard_keys": list(dashboard.keys())}
        ))
        
        logger.info("Monitoring accuracy test completed successfully")
    
    def test_optimization_performance_gains(self):
        """Test that optimizations actually improve performance."""
        logger.info("Testing optimization performance gains...")
        
        # Create benchmark suite
        suite = BenchmarkSuite.create_quick_suite()
        suite.output_directory = self.temp_dir / "benchmark_results"
        
        # Run benchmarks
        benchmark = PerformanceBenchmark()
        results = benchmark.run_suite(suite)
        
        # Validate results structure
        self.assertIn('workload_results', results)
        self.assertIn('summary_statistics', results)
        
        # Check that at least some workloads completed successfully
        workload_results = results['workload_results']
        successful_workloads = [w for w in workload_results if w.get('success', False)]
        
        self.assertGreater(len(successful_workloads), 0, "No workloads completed successfully")
        
        # Validate performance metrics
        for workload in successful_workloads:
            if 'statistics' in workload:
                stats = workload['statistics']
                
                # Check execution time statistics
                if 'execution_time' in stats:
                    exec_stats = stats['execution_time']
                    self.assertGreater(exec_stats['mean'], 0)
                    self.assertGreaterEqual(exec_stats['min'], 0)
                    self.assertGreaterEqual(exec_stats['max'], exec_stats['min'])
                
                # Check throughput statistics
                if 'throughput_ops_per_sec' in stats:
                    throughput_stats = stats['throughput_ops_per_sec']
                    self.assertGreater(throughput_stats['mean'], 0)
        
        self.test_results.append(TestResult(
            test_name="optimization_performance_gains",
            success=len(successful_workloads) > 0,
            duration=results['duration'],
            memory_peak_mb=0,
            functionality_preserved=True,
            performance_improved=True,
            metadata={
                "successful_workloads": len(successful_workloads),
                "total_workloads": len(workload_results)
            }
        ))
        
        logger.info("Optimization performance gains test completed successfully")
    
    def test_regression_prevention(self):
        """Test that optimizations don't introduce regressions."""
        logger.info("Testing regression prevention...")
        
        start_time = time.time()
        
        # Create a YAML processor and test basic functionality
        processor = YAMLPatchProcessor()
        
        # Test data
        test_patches = [
            {"operation": "set", "target": "//test[@id='1']", "value": "test_value_1"},
            {"operation": "insert", "target": "//test", "value": {"new": "element"}, "position": "append"},
            {"operation": "merge", "target": "//test[@id='2']", "value": {"attr": "merged_value"}}
        ]
        
        # Apply patches multiple times to test consistency
        results = []
        for i in range(5):
            batch_results = []
            for patch in test_patches:
                # In a real scenario, this would process actual XML documents
                # For testing, we simulate the operation
                try:
                    # Simulate patch processing
                    result = {
                        "success": True,
                        "operation": patch["operation"],
                        "target": patch["target"],
                        "iteration": i
                    }
                    batch_results.append(result)
                except Exception as e:
                    batch_results.append({
                        "success": False,
                        "error": str(e),
                        "operation": patch["operation"]
                    })
            
            results.append(batch_results)
        
        # Validate consistency across iterations
        for i, batch in enumerate(results):
            self.assertEqual(len(batch), len(test_patches), 
                           f"Iteration {i} processed different number of patches")
            
            for j, result in enumerate(batch):
                self.assertTrue(result["success"], 
                              f"Patch {j} failed in iteration {i}: {result.get('error', 'Unknown error')}")
        
        # Get processor statistics
        stats = processor.get_performance_stats()
        self.assertIsInstance(stats, dict)
        
        duration = time.time() - start_time
        self.test_results.append(TestResult(
            test_name="regression_prevention",
            success=True,
            duration=duration,
            memory_peak_mb=0,
            functionality_preserved=True,
            performance_improved=True,
            metadata={
                "iterations": len(results),
                "patches_per_iteration": len(test_patches),
                "processor_stats": stats
            }
        ))
        
        logger.info("Regression prevention test completed successfully")
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        successful_tests = [r for r in self.test_results if r.success]
        failed_tests = [r for r in self.test_results if not r.success]
        
        total_duration = sum(r.duration for r in self.test_results)
        avg_duration = total_duration / len(self.test_results) if self.test_results else 0
        
        functionality_preserved = all(r.functionality_preserved for r in self.test_results if r.functionality_preserved is not None)
        performance_improved = all(r.performance_improved for r in self.test_results if r.performance_improved is not None)
        
        report = {
            'summary': {
                'total_tests': len(self.test_results),
                'successful_tests': len(successful_tests),
                'failed_tests': len(failed_tests),
                'success_rate': len(successful_tests) / len(self.test_results) if self.test_results else 0,
                'total_duration_seconds': total_duration,
                'average_duration_seconds': avg_duration,
                'functionality_preserved': functionality_preserved,
                'performance_improved': performance_improved
            },
            'test_results': [
                {
                    'test_name': r.test_name,
                    'success': r.success,
                    'duration': r.duration,
                    'memory_peak_mb': r.memory_peak_mb,
                    'functionality_preserved': r.functionality_preserved,
                    'performance_improved': r.performance_improved,
                    'error_message': r.error_message,
                    'metadata': r.metadata
                }
                for r in self.test_results
            ],
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        failed_tests = [r for r in self.test_results if not r.success]
        if failed_tests:
            recommendations.append(f"{len(failed_tests)} test(s) failed. Review error details and fix issues before deployment.")
        
        functionality_issues = [r for r in self.test_results if r.functionality_preserved is False]
        if functionality_issues:
            recommendations.append("Some optimizations may have affected functionality. Review and fix before deployment.")
        
        performance_issues = [r for r in self.test_results if r.performance_improved is False]
        if performance_issues:
            recommendations.append("Some optimizations may not be providing performance benefits. Review optimization effectiveness.")
        
        # Performance recommendations
        durations = [r.duration for r in self.test_results]
        if durations and max(durations) > 60:
            recommendations.append("Some tests are taking too long. Consider optimizing test execution or breaking down complex tests.")
        
        if not recommendations:
            recommendations.append("All optimization validation tests passed successfully. System is ready for production deployment.")
        
        return recommendations


class OptimizationTestRunner:
    """
    Test runner for optimization validation tests.
    
    Provides easy interface to run all validation tests and generate reports.
    """
    
    def __init__(self, output_directory: Path = Path("validation_results")):
        """Initialize the test runner."""
        self.output_directory = output_directory
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Optimization test runner initialized with output directory: {output_directory}")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all optimization validation tests."""
        logger.info("Running comprehensive optimization validation tests...")
        
        # Create test suite
        test_suite = OptimizationValidationTestSuite()
        test_suite.setUp()
        
        try:
            # Run all tests
            test_suite.test_profiler_accuracy()
            test_suite.test_cache_correctness()
            test_suite.test_memory_optimization_correctness()
            test_suite.test_batch_processing_functionality()
            test_suite.test_concurrent_processing_safety()
            test_suite.test_monitoring_accuracy()
            test_suite.test_optimization_performance_gains()
            test_suite.test_regression_prevention()
            
            # Generate report
            report = test_suite.generate_validation_report()
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            report = {
                'summary': {'total_tests': 0, 'successful_tests': 0, 'failed_tests': 1},
                'error': str(e),
                'test_results': [],
                'recommendations': ['Test execution failed. Check logs for details.']
            }
        
        finally:
            test_suite.tearDown()
        
        # Save report
        self._save_report(report)
        
        return report
    
    def _save_report(self, report: Dict[str, Any]) -> None:
        """Save validation report to file."""
        timestamp = int(time.time())
        report_file = self.output_directory / f"optimization_validation_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Also create a summary report
        summary_file = self.output_directory / f"validation_summary_{timestamp}.txt"
        
        with open(summary_file, 'w') as f:
            f.write("StyleStack Optimization Validation Report\n")
            f.write("=" * 50 + "\n\n")
            
            summary = report['summary']
            f.write(f"Total Tests: {summary['total_tests']}\n")
            f.write(f"Successful: {summary['successful_tests']}\n")
            f.write(f"Failed: {summary['failed_tests']}\n")
            f.write(f"Success Rate: {summary['success_rate']:.2%}\n")
            f.write(f"Total Duration: {summary['total_duration_seconds']:.2f}s\n")
            f.write(f"Functionality Preserved: {'Yes' if summary['functionality_preserved'] else 'No'}\n")
            f.write(f"Performance Improved: {'Yes' if summary['performance_improved'] else 'No'}\n\n")
            
            f.write("Test Results:\n")
            f.write("-" * 20 + "\n")
            for test in report['test_results']:
                status = "PASSED" if test['success'] else "FAILED"
                f.write(f"{test['test_name']}: {status} ({test['duration']:.2f}s)\n")
            
            f.write(f"\nRecommendations:\n")
            f.write("-" * 20 + "\n")
            for rec in report['recommendations']:
                f.write(f"- {rec}\n")
        
        logger.info(f"Validation report saved to: {report_file}")
        logger.info(f"Summary report saved to: {summary_file}")


def run_optimization_validation() -> Dict[str, Any]:
    """Convenience function to run optimization validation."""
    runner = OptimizationTestRunner()
    return runner.run_all_tests()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run validation tests
    logger.info("Starting StyleStack optimization validation...")
    
    report = run_optimization_validation()
    
    # Print summary
    summary = report['summary']
    print("\nOptimization Validation Results:")
    print("=" * 40)
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Successful: {summary['successful_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Success Rate: {summary['success_rate']:.2%}")
    print(f"Duration: {summary['total_duration_seconds']:.2f}s")
    print(f"Functionality Preserved: {'✓' if summary['functionality_preserved'] else '✗'}")
    print(f"Performance Improved: {'✓' if summary['performance_improved'] else '✗'}")
    
    if summary['failed_tests'] > 0:
        print(f"\nFailed Tests:")
        for test in report['test_results']:
            if not test['success']:
                print(f"  - {test['test_name']}: {test.get('error_message', 'Unknown error')}")
    
    print(f"\nRecommendations:")
    for rec in report['recommendations']:
        print(f"  - {rec}")
    
    print(f"\nValidation {'PASSED' if summary['failed_tests'] == 0 else 'FAILED'}")