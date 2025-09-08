#!/usr/bin/env python3
"""
StyleStack Production Load Testing System

Comprehensive load testing system that simulates realistic production workloads
for hundreds of templates with sustained processing. Includes performance regression
testing to ensure optimizations don't introduce performance degradation.
"""

import time
import threading
import multiprocessing
import concurrent.futures
import queue
import random
import statistics
import json
import sqlite3
from typing import Dict, List, Any, Optional, Tuple, Callable, NamedTuple
from dataclasses import dataclass, field
from collections import deque, defaultdict
from pathlib import Path
from datetime import datetime, timedelta
import logging
import tempfile
import shutil
import psutil
import hashlib
import contextlib

# Import StyleStack components for load testing
try:
    from .performance_profiler import PerformanceProfiler
    from .advanced_cache_system import CacheManager
    from .memory_optimizer import MemoryManager, ConcurrentMemoryManager
    from .optimized_batch_processor import OptimizedBatchProcessor, BatchProcessingConfig, BatchTask
    from .performance_benchmarks import TemplateGenerator, PatchGenerator
    from .production_monitoring import ProductionMonitor
    from .concurrent_processing_validator import ConcurrentProcessingValidator
except ImportError:
    from performance_profiler import PerformanceProfiler
    from advanced_cache_system import CacheManager
    from memory_optimizer import MemoryManager, ConcurrentMemoryManager
    from optimized_batch_processor import OptimizedBatchProcessor, BatchProcessingConfig, BatchTask
    from performance_benchmarks import TemplateGenerator, PatchGenerator
    from production_monitoring import ProductionMonitor
    from concurrent_processing_validator import ConcurrentProcessingValidator

logger = logging.getLogger(__name__)


class LoadPattern(NamedTuple):
    """Definition of a load testing pattern."""
    name: str
    template_count: int
    concurrent_users: int
    requests_per_second: float
    duration_minutes: int
    complexity_level: int


@dataclass
class LoadTestMetrics:
    """Comprehensive metrics for load testing."""
    start_time: float
    end_time: Optional[float] = None
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_processing_time: float = 0.0
    peak_memory_mb: float = 0.0
    peak_cpu_percent: float = 0.0
    throughput_rps: float = 0.0
    average_response_time: float = 0.0
    p50_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    error_rate: float = 0.0
    memory_leak_detected: bool = False
    performance_degradation_detected: bool = False
    
    @property
    def duration_seconds(self) -> float:
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests


@dataclass
class RegressionTestResult:
    """Result of a performance regression test."""
    test_name: str
    baseline_metrics: LoadTestMetrics
    current_metrics: LoadTestMetrics
    performance_change_percent: float
    memory_change_percent: float
    throughput_change_percent: float
    regression_detected: bool
    acceptable_degradation_threshold: float = 5.0
    
    def is_regression(self) -> bool:
        """Check if this represents a performance regression."""
        return (self.performance_change_percent > self.acceptable_degradation_threshold or
                self.memory_change_percent > self.acceptable_degradation_threshold or
                self.throughput_change_percent < -self.acceptable_degradation_threshold)


class ProductionLoadTester:
    """
    Comprehensive production load testing system.
    
    Simulates realistic production workloads with hundreds of templates,
    concurrent processing, and sustained load over time.
    """
    
    def __init__(self, 
                 output_directory: Path,
                 enable_monitoring: bool = True,
                 enable_profiling: bool = True):
        """Initialize the production load tester."""
        self.output_directory = output_directory
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        self.enable_monitoring = enable_monitoring
        self.enable_profiling = enable_profiling
        
        # Test components
        self.template_generator = TemplateGenerator()
        self.patch_generator = PatchGenerator()
        
        # Monitoring and profiling
        self.monitor: Optional[ProductionMonitor] = None
        self.profiler: Optional[PerformanceProfiler] = None
        
        # Test results
        self.test_results: List[Dict[str, Any]] = []
        self.baseline_results: Dict[str, LoadTestMetrics] = {}
        
        # Load patterns
        self.load_patterns = self._define_load_patterns()
        
        logger.info(f"Production load tester initialized with output directory: {output_directory}")
    
    def _define_load_patterns(self) -> List[LoadPattern]:
        """Define various load testing patterns."""
        return [
            LoadPattern("light_load", 50, 2, 1.0, 10, 1),
            LoadPattern("moderate_load", 150, 5, 5.0, 15, 2),
            LoadPattern("heavy_load", 300, 10, 10.0, 20, 3),
            LoadPattern("peak_load", 500, 20, 20.0, 30, 4),
            LoadPattern("sustained_load", 200, 8, 8.0, 60, 2),
            LoadPattern("burst_load", 100, 15, 25.0, 5, 3),
            LoadPattern("stress_test", 1000, 50, 50.0, 10, 5)
        ]
    
    def run_comprehensive_load_test(self) -> Dict[str, Any]:
        """Run comprehensive load testing across all patterns."""
        logger.info("Starting comprehensive production load testing...")
        
        start_time = time.time()
        all_results = {}
        
        # Setup monitoring and profiling
        if self.enable_monitoring:
            self.monitor = ProductionMonitor(
                metrics_interval=5.0,
                enable_alerts=True,
                enable_health_checks=True
            )
            
            # Setup database for monitoring
            db_path = self.output_directory / "load_test_monitoring.db"
            self.monitor.setup_database(db_path)
        
        if self.enable_profiling:
            self.profiler = PerformanceProfiler()
        
        try:
            # Start monitoring
            if self.monitor:
                self.monitor.start_monitoring()
            
            # Run each load pattern
            for pattern in self.load_patterns:
                logger.info(f"Running load pattern: {pattern.name}")
                
                pattern_results = self._run_single_load_pattern(pattern)
                all_results[pattern.name] = pattern_results
                
                # Brief pause between patterns to allow system recovery
                time.sleep(30)
        
        except Exception as e:
            logger.error(f"Load testing failed: {e}")
            all_results['error'] = str(e)
        
        finally:
            # Stop monitoring
            if self.monitor:
                self.monitor.stop_monitoring()
        
        # Generate comprehensive report
        total_duration = time.time() - start_time
        
        comprehensive_results = {
            'test_start_time': start_time,
            'test_duration_seconds': total_duration,
            'patterns_tested': len(self.load_patterns),
            'pattern_results': all_results,
            'summary_statistics': self._calculate_summary_statistics(all_results),
            'system_impact_analysis': self._analyze_system_impact(all_results),
            'recommendations': self._generate_load_test_recommendations(all_results)
        }
        
        # Save results
        self._save_load_test_results(comprehensive_results)
        
        logger.info(f"Comprehensive load testing completed in {total_duration:.2f}s")
        
        return comprehensive_results
    
    def _run_single_load_pattern(self, pattern: LoadPattern) -> Dict[str, Any]:
        """Run a single load testing pattern."""
        logger.info(f"Executing load pattern '{pattern.name}': {pattern.template_count} templates, "
                   f"{pattern.concurrent_users} users, {pattern.requests_per_second} RPS for {pattern.duration_minutes}min")
        
        # Initialize metrics
        metrics = LoadTestMetrics(start_time=time.time())
        
        # Start profiling session
        session_id = None
        if self.profiler:
            session_id = f"load_test_{pattern.name}_{int(metrics.start_time)}"
            self.profiler.start_session(session_id)
        
        # Generate test templates and patches
        test_templates = self._generate_test_data(pattern)
        
        # Response time tracking
        response_times = deque(maxlen=10000)  # Keep last 10k response times
        
        # Error tracking
        errors = []
        
        # Memory tracking
        memory_samples = []
        
        try:
            # Setup batch processor
            config = BatchProcessingConfig(
                max_workers=pattern.concurrent_users,
                memory_limit_mb=2048,
                batch_size=max(10, pattern.template_count // 20),
                processing_mode="thread",
                enable_caching=True,
                enable_memory_optimization=True,
                enable_profiling=False  # We handle profiling at higher level
            )
            
            with OptimizedBatchProcessor(config) as batch_processor:
                # Submit templates for processing
                tasks = self._create_batch_tasks(test_templates, pattern)
                
                # Process with sustained load
                results = self._execute_sustained_load(
                    batch_processor, tasks, pattern, response_times, errors, memory_samples
                )
                
                # Collect processor statistics
                processor_stats = batch_processor.get_processing_stats()
        
        except Exception as e:
            logger.error(f"Load pattern execution failed: {e}")
            errors.append(f"Pattern execution failed: {str(e)}")
            results = []
        
        # Finalize metrics
        metrics.end_time = time.time()
        metrics.total_requests = len(test_templates)
        metrics.successful_requests = len([r for r in results if r.get('success', False)])
        metrics.failed_requests = len([r for r in results if not r.get('success', False)])
        
        if response_times:
            response_time_list = list(response_times)
            metrics.average_response_time = statistics.mean(response_time_list)
            metrics.p50_response_time = statistics.median(response_time_list)
            sorted_times = sorted(response_time_list)
            metrics.p95_response_time = sorted_times[int(len(sorted_times) * 0.95)]
            metrics.p99_response_time = sorted_times[int(len(sorted_times) * 0.99)]
        
        metrics.throughput_rps = metrics.successful_requests / metrics.duration_seconds if metrics.duration_seconds > 0 else 0
        metrics.error_rate = metrics.failed_requests / metrics.total_requests if metrics.total_requests > 0 else 0
        
        if memory_samples:
            metrics.peak_memory_mb = max(memory_samples)
            # Simple memory leak detection - check if memory usage increased significantly
            if len(memory_samples) > 10:
                initial_avg = statistics.mean(memory_samples[:5])
                final_avg = statistics.mean(memory_samples[-5:])
                metrics.memory_leak_detected = (final_avg - initial_avg) > 100  # > 100MB increase
        
        # End profiling session
        profiling_results = None
        if self.profiler and session_id:
            profiling_results = self.profiler.end_session(session_id)
        
        # Compile pattern results
        pattern_results = {
            'pattern': pattern,
            'metrics': metrics,
            'response_times': list(response_times)[-1000:],  # Keep last 1000 for analysis
            'errors': errors,
            'memory_samples': memory_samples[-100:],  # Keep last 100 memory samples
            'profiling_results': profiling_results,
            'processor_stats': processor_stats if 'processor_stats' in locals() else {}
        }
        
        return pattern_results
    
    def _generate_test_data(self, pattern: LoadPattern) -> List[Tuple[Path, List[Dict[str, Any]]]]:
        """Generate test templates and patches for load pattern."""
        test_data = []
        
        # Create temporary directory for this pattern
        pattern_dir = self.output_directory / f"temp_{pattern.name}"
        pattern_dir.mkdir(exist_ok=True)
        
        for i in range(pattern.template_count):
            # Create workload configuration for template generation
            from .performance_benchmarks import WorkloadConfig, WorkloadType
            
            workload_config = WorkloadConfig(
                workload_type=WorkloadType.MEDIUM_TEMPLATE,
                slide_count=random.randint(5, 20),
                element_count_per_slide=random.randint(10, 30),
                patch_count=random.randint(20, 100),
                complexity_level=pattern.complexity_level,
                nested_element_depth=random.randint(2, 6)
            )
            
            # Generate template
            template_path = self.template_generator.generate_pptx_template(workload_config, pattern_dir)
            
            # Generate patches
            patches = self.patch_generator.generate_patches(workload_config)
            
            test_data.append((template_path, patches))
        
        return test_data
    
    def _create_batch_tasks(self, test_templates: List[Tuple[Path, List[Dict[str, Any]]]], 
                          pattern: LoadPattern) -> List[BatchTask]:
        """Create batch tasks from test templates."""
        tasks = []
        
        output_dir = self.output_directory / f"outputs_{pattern.name}"
        output_dir.mkdir(exist_ok=True)
        
        for i, (template_path, patches) in enumerate(test_templates):
            output_path = output_dir / f"processed_{template_path.stem}_{i}.pptx"
            
            task = BatchTask(
                task_id=f"{pattern.name}_task_{i}",
                template_path=template_path,
                patches=patches,
                output_path=output_path,
                priority=random.randint(1, 5),
                metadata={
                    'pattern_name': pattern.name,
                    'template_index': i,
                    'patch_count': len(patches)
                }
            )
            
            tasks.append(task)
        
        return tasks
    
    def _execute_sustained_load(self, batch_processor: OptimizedBatchProcessor,
                              tasks: List[BatchTask], pattern: LoadPattern,
                              response_times: deque, errors: List[str],
                              memory_samples: List[float]) -> List[Dict[str, Any]]:
        """Execute sustained load with rate limiting and monitoring."""
        
        # Calculate timing for rate limiting
        target_interval = 1.0 / pattern.requests_per_second if pattern.requests_per_second > 0 else 0.1
        end_time = time.time() + (pattern.duration_minutes * 60)
        
        results = []
        submitted_tasks = []
        
        # Memory monitoring thread
        def memory_monitor():
            while time.time() < end_time:
                try:
                    memory_mb = psutil.Process().memory_info().rss / (1024 * 1024)
                    memory_samples.append(memory_mb)
                except:
                    pass
                time.sleep(5.0)
        
        memory_thread = threading.Thread(target=memory_monitor, daemon=True)
        memory_thread.start()
        
        # Submit tasks with rate limiting
        task_index = 0
        while time.time() < end_time and task_index < len(tasks):
            batch_start = time.time()
            
            # Submit batch of tasks
            batch_size = min(pattern.concurrent_users, len(tasks) - task_index)
            batch_tasks = tasks[task_index:task_index + batch_size]
            
            for task in batch_tasks:
                request_start = time.time()
                
                try:
                    # Submit task (this is asynchronous)
                    success = batch_processor.submit_task(task)
                    
                    if success:
                        submitted_tasks.append(task)
                        response_time = time.time() - request_start
                        response_times.append(response_time)
                    else:
                        errors.append(f"Failed to submit task {task.task_id}")
                
                except Exception as e:
                    errors.append(f"Task submission error: {str(e)}")
                
                # Rate limiting
                elapsed = time.time() - request_start
                if elapsed < target_interval:
                    time.sleep(target_interval - elapsed)
            
            task_index += batch_size
            
            # Brief pause between batches
            batch_elapsed = time.time() - batch_start
            if batch_elapsed < 1.0:
                time.sleep(1.0 - batch_elapsed)
        
        # Wait for all submitted tasks to complete (with timeout)
        logger.info(f"Waiting for {len(submitted_tasks)} tasks to complete...")
        
        completion_timeout = time.time() + 300  # 5 minute timeout
        while time.time() < completion_timeout:
            stats = batch_processor.get_processing_stats()
            
            if stats['tasks_completed'] + stats['tasks_failed'] >= len(submitted_tasks):
                break
            
            time.sleep(1.0)
        
        # Collect final results
        final_stats = batch_processor.get_processing_stats()
        
        # Create mock results based on statistics (since we don't have access to individual results)
        for i in range(final_stats['tasks_completed']):
            results.append({'success': True, 'task_index': i})
        
        for i in range(final_stats['tasks_failed']):
            results.append({'success': False, 'task_index': i, 'error': 'Processing failed'})
        
        return results
    
    def _calculate_summary_statistics(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics across all load patterns."""
        if not all_results or 'error' in all_results:
            return {'error': 'No valid results to analyze'}
        
        # Aggregate metrics across patterns
        total_requests = 0
        total_successful = 0
        total_failed = 0
        all_response_times = []
        all_throughputs = []
        all_error_rates = []
        peak_memory_overall = 0
        
        for pattern_name, pattern_result in all_results.items():
            if isinstance(pattern_result, dict) and 'metrics' in pattern_result:
                metrics = pattern_result['metrics']
                
                total_requests += metrics.total_requests
                total_successful += metrics.successful_requests
                total_failed += metrics.failed_requests
                
                if 'response_times' in pattern_result:
                    all_response_times.extend(pattern_result['response_times'])
                
                all_throughputs.append(metrics.throughput_rps)
                all_error_rates.append(metrics.error_rate)
                
                peak_memory_overall = max(peak_memory_overall, metrics.peak_memory_mb)
        
        summary = {
            'total_requests_across_patterns': total_requests,
            'total_successful_requests': total_successful,
            'total_failed_requests': total_failed,
            'overall_success_rate': total_successful / total_requests if total_requests > 0 else 0,
            'peak_memory_mb_overall': peak_memory_overall,
            'patterns_completed': len([r for r in all_results.values() if isinstance(r, dict) and 'metrics' in r])
        }
        
        if all_response_times:
            summary.update({
                'average_response_time_overall': statistics.mean(all_response_times),
                'median_response_time_overall': statistics.median(all_response_times),
                'p95_response_time_overall': sorted(all_response_times)[int(len(all_response_times) * 0.95)],
                'p99_response_time_overall': sorted(all_response_times)[int(len(all_response_times) * 0.99)]
            })
        
        if all_throughputs:
            summary.update({
                'average_throughput_rps': statistics.mean(all_throughputs),
                'peak_throughput_rps': max(all_throughputs)
            })
        
        if all_error_rates:
            summary.update({
                'average_error_rate': statistics.mean(all_error_rates),
                'max_error_rate': max(all_error_rates)
            })
        
        return summary
    
    def _analyze_system_impact(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze system impact of load testing."""
        impact_analysis = {
            'memory_leaks_detected': False,
            'performance_degradation_detected': False,
            'system_stability': 'stable',
            'resource_utilization': 'normal',
            'bottlenecks_identified': []
        }
        
        # Analyze each pattern for issues
        for pattern_name, pattern_result in all_results.items():
            if isinstance(pattern_result, dict) and 'metrics' in pattern_result:
                metrics = pattern_result['metrics']
                
                # Check for memory leaks
                if metrics.memory_leak_detected:
                    impact_analysis['memory_leaks_detected'] = True
                    impact_analysis['bottlenecks_identified'].append(
                        f"Memory leak detected in pattern {pattern_name}"
                    )
                
                # Check for high error rates
                if metrics.error_rate > 0.05:  # > 5% error rate
                    impact_analysis['system_stability'] = 'unstable'
                    impact_analysis['bottlenecks_identified'].append(
                        f"High error rate ({metrics.error_rate:.2%}) in pattern {pattern_name}"
                    )
                
                # Check for performance issues
                if metrics.average_response_time > 10.0:  # > 10 second average response
                    impact_analysis['performance_degradation_detected'] = True
                    impact_analysis['bottlenecks_identified'].append(
                        f"Slow response times ({metrics.average_response_time:.2f}s) in pattern {pattern_name}"
                    )
                
                # Check resource utilization
                if metrics.peak_memory_mb > 2048:  # > 2GB peak memory
                    impact_analysis['resource_utilization'] = 'high'
        
        return impact_analysis
    
    def _generate_load_test_recommendations(self, all_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on load test results."""
        recommendations = []
        
        summary = self._calculate_summary_statistics(all_results)
        impact = self._analyze_system_impact(all_results)
        
        # Performance recommendations
        if summary.get('overall_success_rate', 0) < 0.95:
            recommendations.append(
                f"Success rate is {summary.get('overall_success_rate', 0):.2%}. "
                f"Investigate and fix error causes before production deployment."
            )
        
        if summary.get('average_response_time_overall', 0) > 5.0:
            recommendations.append(
                f"Average response time is {summary.get('average_response_time_overall', 0):.2f}s. "
                f"Consider optimizing processing pipeline."
            )
        
        # Memory recommendations
        if impact['memory_leaks_detected']:
            recommendations.append(
                "Memory leaks detected. Review memory management and garbage collection."
            )
        
        if summary.get('peak_memory_mb_overall', 0) > 4096:
            recommendations.append(
                f"Peak memory usage is {summary.get('peak_memory_mb_overall', 0):.0f}MB. "
                f"Consider optimizing memory usage or increasing system resources."
            )
        
        # Stability recommendations
        if impact['system_stability'] == 'unstable':
            recommendations.append(
                "System stability issues detected. Review error logs and implement proper error handling."
            )
        
        # Throughput recommendations
        if summary.get('average_throughput_rps', 0) < 1.0:
            recommendations.append(
                f"Low throughput ({summary.get('average_throughput_rps', 0):.2f} RPS). "
                f"Consider scaling horizontally or optimizing processing."
            )
        
        # General recommendations
        if not recommendations:
            recommendations.append(
                "All load tests completed successfully. System appears ready for production deployment."
            )
        
        return recommendations
    
    def _save_load_test_results(self, results: Dict[str, Any]) -> None:
        """Save comprehensive load test results."""
        timestamp = int(time.time())
        
        # Save detailed JSON report
        json_file = self.output_directory / f"load_test_results_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save summary report
        summary_file = self.output_directory / f"load_test_summary_{timestamp}.txt"
        
        with open(summary_file, 'w') as f:
            f.write("StyleStack Production Load Test Report\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Test Duration: {results['test_duration_seconds']:.2f} seconds\n")
            f.write(f"Patterns Tested: {results['patterns_tested']}\n\n")
            
            summary = results.get('summary_statistics', {})
            if summary and 'error' not in summary:
                f.write("Summary Statistics:\n")
                f.write("-" * 20 + "\n")
                f.write(f"Total Requests: {summary.get('total_requests_across_patterns', 0)}\n")
                f.write(f"Successful: {summary.get('total_successful_requests', 0)}\n")
                f.write(f"Failed: {summary.get('total_failed_requests', 0)}\n")
                f.write(f"Success Rate: {summary.get('overall_success_rate', 0):.2%}\n")
                f.write(f"Average Response Time: {summary.get('average_response_time_overall', 0):.2f}s\n")
                f.write(f"Peak Memory: {summary.get('peak_memory_mb_overall', 0):.1f}MB\n")
                f.write(f"Average Throughput: {summary.get('average_throughput_rps', 0):.2f} RPS\n\n")
            
            # Pattern results
            f.write("Pattern Results:\n")
            f.write("-" * 15 + "\n")
            for pattern_name, pattern_result in results.get('pattern_results', {}).items():
                if isinstance(pattern_result, dict) and 'metrics' in pattern_result:
                    metrics = pattern_result['metrics']
                    f.write(f"{pattern_name}:\n")
                    f.write(f"  Success Rate: {metrics.success_rate:.2%}\n")
                    f.write(f"  Avg Response Time: {metrics.average_response_time:.2f}s\n")
                    f.write(f"  Throughput: {metrics.throughput_rps:.2f} RPS\n")
                    f.write(f"  Peak Memory: {metrics.peak_memory_mb:.1f}MB\n\n")
            
            # Recommendations
            f.write("Recommendations:\n")
            f.write("-" * 15 + "\n")
            for rec in results.get('recommendations', []):
                f.write(f"- {rec}\n")
        
        logger.info(f"Load test results saved to: {json_file}")
        logger.info(f"Load test summary saved to: {summary_file}")


class PerformanceRegressionTester:
    """
    Performance regression testing framework.
    
    Compares current performance against baseline metrics to detect
    performance regressions introduced by code changes.
    """
    
    def __init__(self, baseline_db_path: Path, output_directory: Path):
        """Initialize the regression tester."""
        self.baseline_db_path = baseline_db_path
        self.output_directory = output_directory
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize baseline database
        self._init_baseline_db()
        
        logger.info(f"Performance regression tester initialized")
    
    def _init_baseline_db(self) -> None:
        """Initialize baseline database schema."""
        with sqlite3.connect(self.baseline_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS baselines (
                    test_name TEXT PRIMARY KEY,
                    timestamp REAL,
                    metrics_json TEXT,
                    system_info TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS regression_tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    test_name TEXT,
                    baseline_metrics_json TEXT,
                    current_metrics_json TEXT,
                    regression_detected BOOLEAN,
                    performance_change_percent REAL,
                    memory_change_percent REAL,
                    throughput_change_percent REAL
                )
            """)
    
    def store_baseline(self, test_name: str, metrics: LoadTestMetrics) -> None:
        """Store baseline performance metrics."""
        system_info = {
            'cpu_count': multiprocessing.cpu_count(),
            'memory_gb': psutil.virtual_memory().total / (1024**3),
            'platform': 'production'  # Would be detected in real implementation
        }
        
        with sqlite3.connect(self.baseline_db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO baselines 
                (test_name, timestamp, metrics_json, system_info)
                VALUES (?, ?, ?, ?)
            """, (
                test_name,
                time.time(),
                json.dumps(metrics.__dict__, default=str),
                json.dumps(system_info)
            ))
        
        logger.info(f"Stored baseline for test: {test_name}")
    
    def get_baseline(self, test_name: str) -> Optional[LoadTestMetrics]:
        """Retrieve baseline metrics for a test."""
        with sqlite3.connect(self.baseline_db_path) as conn:
            cursor = conn.execute("""
                SELECT metrics_json FROM baselines WHERE test_name = ?
            """, (test_name,))
            
            row = cursor.fetchone()
            if row:
                metrics_data = json.loads(row[0])
                # Reconstruct LoadTestMetrics object
                metrics = LoadTestMetrics(start_time=0)  # Will be overwritten
                metrics.__dict__.update(metrics_data)
                return metrics
        
        return None
    
    def run_regression_test(self, test_name: str, current_metrics: LoadTestMetrics) -> RegressionTestResult:
        """Run regression test comparing current metrics to baseline."""
        baseline_metrics = self.get_baseline(test_name)
        
        if not baseline_metrics:
            logger.warning(f"No baseline found for test: {test_name}")
            # Create a dummy baseline for comparison
            baseline_metrics = LoadTestMetrics(start_time=0)
        
        # Calculate performance changes
        performance_change = self._calculate_percentage_change(
            baseline_metrics.average_response_time,
            current_metrics.average_response_time
        )
        
        memory_change = self._calculate_percentage_change(
            baseline_metrics.peak_memory_mb,
            current_metrics.peak_memory_mb
        )
        
        throughput_change = self._calculate_percentage_change(
            baseline_metrics.throughput_rps,
            current_metrics.throughput_rps,
            inverse=True  # Higher throughput is better
        )
        
        # Create regression test result
        result = RegressionTestResult(
            test_name=test_name,
            baseline_metrics=baseline_metrics,
            current_metrics=current_metrics,
            performance_change_percent=performance_change,
            memory_change_percent=memory_change,
            throughput_change_percent=throughput_change,
            regression_detected=False  # Will be set by is_regression()
        )
        
        result.regression_detected = result.is_regression()
        
        # Store regression test result
        self._store_regression_result(result)
        
        return result
    
    def _calculate_percentage_change(self, baseline: float, current: float, inverse: bool = False) -> float:
        """Calculate percentage change from baseline to current."""
        if baseline == 0:
            return 0.0
        
        change = ((current - baseline) / baseline) * 100
        
        # For inverse metrics (like throughput), we want to flip the sign
        # so that decreases are positive (bad) and increases are negative (good)
        if inverse:
            change = -change
        
        return change
    
    def _store_regression_result(self, result: RegressionTestResult) -> None:
        """Store regression test result in database."""
        with sqlite3.connect(self.baseline_db_path) as conn:
            conn.execute("""
                INSERT INTO regression_tests 
                (timestamp, test_name, baseline_metrics_json, current_metrics_json,
                 regression_detected, performance_change_percent, memory_change_percent, throughput_change_percent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                time.time(),
                result.test_name,
                json.dumps(result.baseline_metrics.__dict__, default=str),
                json.dumps(result.current_metrics.__dict__, default=str),
                result.regression_detected,
                result.performance_change_percent,
                result.memory_change_percent,
                result.throughput_change_percent
            ))
    
    def generate_regression_report(self, test_results: List[RegressionTestResult]) -> Dict[str, Any]:
        """Generate comprehensive regression test report."""
        regressions_detected = [r for r in test_results if r.regression_detected]
        
        report = {
            'timestamp': time.time(),
            'total_tests': len(test_results),
            'regressions_detected': len(regressions_detected),
            'regression_rate': len(regressions_detected) / len(test_results) if test_results else 0,
            'test_results': [
                {
                    'test_name': r.test_name,
                    'regression_detected': r.regression_detected,
                    'performance_change_percent': r.performance_change_percent,
                    'memory_change_percent': r.memory_change_percent,
                    'throughput_change_percent': r.throughput_change_percent,
                    'baseline_response_time': r.baseline_metrics.average_response_time,
                    'current_response_time': r.current_metrics.average_response_time,
                    'baseline_memory_mb': r.baseline_metrics.peak_memory_mb,
                    'current_memory_mb': r.current_metrics.peak_memory_mb,
                    'baseline_throughput_rps': r.baseline_metrics.throughput_rps,
                    'current_throughput_rps': r.current_metrics.throughput_rps
                }
                for r in test_results
            ],
            'recommendations': self._generate_regression_recommendations(test_results)
        }
        
        return report
    
    def _generate_regression_recommendations(self, test_results: List[RegressionTestResult]) -> List[str]:
        """Generate recommendations based on regression test results."""
        recommendations = []
        
        regressions = [r for r in test_results if r.regression_detected]
        
        if regressions:
            recommendations.append(f"{len(regressions)} performance regression(s) detected.")
            
            # Specific recommendations for different types of regressions
            for regression in regressions:
                if regression.performance_change_percent > 10:
                    recommendations.append(
                        f"Test '{regression.test_name}': Response time increased by {regression.performance_change_percent:.1f}%. "
                        f"Review recent changes affecting processing performance."
                    )
                
                if regression.memory_change_percent > 10:
                    recommendations.append(
                        f"Test '{regression.test_name}': Memory usage increased by {regression.memory_change_percent:.1f}%. "
                        f"Check for memory leaks or inefficient memory usage."
                    )
                
                if regression.throughput_change_percent > 10:
                    recommendations.append(
                        f"Test '{regression.test_name}': Throughput decreased by {regression.throughput_change_percent:.1f}%. "
                        f"Investigate bottlenecks in processing pipeline."
                    )
        else:
            recommendations.append("No performance regressions detected. All tests perform within acceptable limits.")
        
        return recommendations


def run_production_load_test(output_directory: Path = Path("load_test_results")) -> Dict[str, Any]:
    """Convenience function to run production load testing."""
    tester = ProductionLoadTester(output_directory)
    return tester.run_comprehensive_load_test()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run production load test
    logger.info("Starting StyleStack production load testing...")
    
    results = run_production_load_test()
    
    # Print summary
    if 'summary_statistics' in results and 'error' not in results['summary_statistics']:
        summary = results['summary_statistics']
        print("\nProduction Load Test Results:")
        print("=" * 40)
        print(f"Total Requests: {summary.get('total_requests_across_patterns', 0)}")
        print(f"Success Rate: {summary.get('overall_success_rate', 0):.2%}")
        print(f"Average Response Time: {summary.get('average_response_time_overall', 0):.2f}s")
        print(f"Peak Memory Usage: {summary.get('peak_memory_mb_overall', 0):.1f}MB")
        print(f"Average Throughput: {summary.get('average_throughput_rps', 0):.2f} RPS")
    
    print(f"\nRecommendations:")
    for rec in results.get('recommendations', []):
        print(f"  - {rec}")
    
    print(f"\nDetailed results saved to load test output directory.")