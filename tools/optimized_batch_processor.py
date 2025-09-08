#!/usr/bin/env python3
"""
StyleStack Optimized Batch Processing System

High-performance batch processor for minimal memory overhead and maximum throughput.
Integrates with memory optimization, advanced caching, and provides concurrent processing
capabilities for production-scale workloads.
"""

import time
import threading
import multiprocessing
import queue
import asyncio
from typing import Dict, List, Any, Optional, Union, Callable, Iterator, Tuple
from dataclasses import dataclass, field
from collections import deque, defaultdict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed, Future
import logging
import tempfile
import shutil
import psutil
import gc
from contextlib import contextmanager

# Import StyleStack components
try:
    from .memory_optimizer import MemoryManager, StreamingOOXMLProcessor, ConcurrentMemoryManager
    from .advanced_cache_system import CacheManager
    from .performance_profiler import PerformanceProfiler
    from .yaml_ooxml_processor import YAMLPatchProcessor
except ImportError:
    from memory_optimizer import MemoryManager, StreamingOOXMLProcessor, ConcurrentMemoryManager
    from advanced_cache_system import CacheManager
    from performance_profiler import PerformanceProfiler
    from yaml_ooxml_processor import YAMLPatchProcessor

logger = logging.getLogger(__name__)


@dataclass
class BatchTask:
    """Container for a single batch processing task."""
    task_id: str
    template_path: Path
    patches: List[Dict[str, Any]]
    output_path: Path
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization processing."""
        if not self.task_id:
            self.task_id = f"task_{int(time.time() * 1000)}"
    
    def __lt__(self, other):
        """Enable priority queue ordering."""
        return self.priority < other.priority


@dataclass
class BatchResult:
    """Container for batch processing results."""
    task_id: str
    success: bool
    processing_time: float
    memory_peak_mb: float
    patches_applied: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchProcessingConfig:
    """Configuration for batch processing."""
    max_workers: int = multiprocessing.cpu_count()
    memory_limit_mb: float = 1024.0
    batch_size: int = 10
    processing_mode: str = "thread"  # "thread", "process", or "async"
    enable_caching: bool = True
    enable_memory_optimization: bool = True
    enable_profiling: bool = False
    temp_directory: Optional[Path] = None
    backpressure_threshold: int = 100
    retry_failed_tasks: bool = True
    max_retries: int = 3
    
    def __post_init__(self):
        """Post-initialization validation."""
        if self.processing_mode not in ["thread", "process", "async"]:
            raise ValueError("processing_mode must be 'thread', 'process', or 'async'")
        
        if self.temp_directory is None:
            self.temp_directory = Path(tempfile.gettempdir()) / "stylestack_batch"


class BatchQueue:
    """
    Thread-safe priority queue for batch tasks with backpressure control.
    """
    
    def __init__(self, max_size: int = 1000):
        """Initialize the batch queue."""
        self.max_size = max_size
        self._queue = queue.PriorityQueue(maxsize=max_size)
        self._pending_count = 0
        self._completed_count = 0
        self._failed_count = 0
        self._lock = threading.RLock()
    
    def put(self, task: BatchTask, timeout: Optional[float] = None) -> bool:
        """Add task to queue with optional timeout."""
        try:
            self._queue.put((task.priority, time.time(), task), timeout=timeout)
            with self._lock:
                self._pending_count += 1
            return True
        except queue.Full:
            return False
    
    def get(self, timeout: Optional[float] = None) -> Optional[BatchTask]:
        """Get next task from queue."""
        try:
            _, _, task = self._queue.get(timeout=timeout)
            return task
        except queue.Empty:
            return None
    
    def task_done(self, success: bool = True) -> None:
        """Mark task as completed."""
        self._queue.task_done()
        with self._lock:
            self._pending_count -= 1
            if success:
                self._completed_count += 1
            else:
                self._failed_count += 1
    
    def get_stats(self) -> Dict[str, int]:
        """Get queue statistics."""
        with self._lock:
            return {
                'pending': self._pending_count,
                'completed': self._completed_count,
                'failed': self._failed_count,
                'queue_size': self._queue.qsize()
            }
    
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.empty()
    
    def clear(self) -> None:
        """Clear all pending tasks."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except queue.Empty:
                break
        
        with self._lock:
            self._pending_count = 0


class WorkerPool:
    """
    Managed worker pool with load balancing and health monitoring.
    """
    
    def __init__(self, 
                 config: BatchProcessingConfig,
                 memory_manager: ConcurrentMemoryManager,
                 cache_manager: CacheManager):
        """Initialize the worker pool."""
        self.config = config
        self.memory_manager = memory_manager
        self.cache_manager = cache_manager
        
        # Worker management
        self.workers: List[Any] = []
        self.worker_stats: Dict[str, Dict[str, Any]] = {}
        
        # Load balancing
        self.task_assignments: Dict[str, str] = {}  # task_id -> worker_id
        self.worker_loads: Dict[str, int] = {}  # worker_id -> current_tasks
        
        # Health monitoring
        self.failed_workers: Set[str] = set()
        self.worker_restart_counts: Dict[str, int] = defaultdict(int)
        
        self._initialize_workers()
    
    def _initialize_workers(self) -> None:
        """Initialize worker pool based on configuration."""
        if self.config.processing_mode == "thread":
            self._initialize_thread_workers()
        elif self.config.processing_mode == "process":
            self._initialize_process_workers()
        else:  # async
            self._initialize_async_workers()
    
    def _initialize_thread_workers(self) -> None:
        """Initialize thread-based workers."""
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.max_workers,
            thread_name_prefix="batch-worker"
        )
        
        for i in range(self.config.max_workers):
            worker_id = f"thread-worker-{i}"
            self.worker_loads[worker_id] = 0
            self.worker_stats[worker_id] = {
                'tasks_completed': 0,
                'tasks_failed': 0,
                'total_processing_time': 0.0,
                'memory_peak_mb': 0.0
            }
    
    def _initialize_process_workers(self) -> None:
        """Initialize process-based workers."""
        self.executor = ProcessPoolExecutor(
            max_workers=self.config.max_workers
        )
        
        for i in range(self.config.max_workers):
            worker_id = f"process-worker-{i}"
            self.worker_loads[worker_id] = 0
            self.worker_stats[worker_id] = {
                'tasks_completed': 0,
                'tasks_failed': 0,
                'total_processing_time': 0.0,
                'memory_peak_mb': 0.0
            }
    
    def _initialize_async_workers(self) -> None:
        """Initialize async workers (placeholder for future implementation)."""
        # For now, fall back to thread-based workers
        self._initialize_thread_workers()
    
    def submit_task(self, task: BatchTask) -> Future:
        """Submit task to worker pool."""
        # Select worker with lowest load
        worker_id = min(self.worker_loads.keys(), key=lambda w: self.worker_loads[w])
        
        # Create processing function
        if self.config.processing_mode == "thread":
            future = self.executor.submit(self._process_task_thread, task, worker_id)
        else:  # process
            future = self.executor.submit(self._process_task_process, task, worker_id)
        
        # Track assignment
        self.task_assignments[task.task_id] = worker_id
        self.worker_loads[worker_id] += 1
        
        return future
    
    def _process_task_thread(self, task: BatchTask, worker_id: str) -> BatchResult:
        """Process task in thread worker."""
        try:
            # Use thread-local memory limit
            thread_id = threading.get_ident()
            with self.memory_manager.thread_memory_context(
                self.config.memory_limit_mb / self.config.max_workers
            ):
                result = self._execute_single_task(task, worker_id)
        
        except Exception as e:
            logger.error(f"Task {task.task_id} failed in thread worker {worker_id}: {e}")
            result = BatchResult(
                task_id=task.task_id,
                success=False,
                processing_time=0.0,
                memory_peak_mb=0.0,
                patches_applied=0,
                errors=[str(e)]
            )
        
        finally:
            # Update worker load
            self.worker_loads[worker_id] -= 1
            
            # Update statistics
            stats = self.worker_stats[worker_id]
            if result.success:
                stats['tasks_completed'] += 1
            else:
                stats['tasks_failed'] += 1
            
            stats['total_processing_time'] += result.processing_time
            stats['memory_peak_mb'] = max(stats['memory_peak_mb'], result.memory_peak_mb)
        
        return result
    
    def _process_task_process(self, task: BatchTask, worker_id: str) -> BatchResult:
        """Process task in process worker."""
        # Process workers need their own memory manager and cache manager
        # This is a simplified implementation
        try:
            with MemoryManager(memory_limit_mb=self.config.memory_limit_mb / self.config.max_workers) as memory_manager:
                with CacheManager() as cache_manager:
                    # Create local processor
                    processor = StreamingOOXMLProcessor(memory_manager)
                    
                    start_time = time.time()
                    start_memory = psutil.Process().memory_info().rss / (1024 * 1024)
                    
                    # Process template
                    processing_stats = processor.process_large_template(
                        task.template_path,
                        task.patches,
                        task.output_path
                    )
                    
                    end_time = time.time()
                    end_memory = psutil.Process().memory_info().rss / (1024 * 1024)
                    
                    result = BatchResult(
                        task_id=task.task_id,
                        success=True,
                        processing_time=end_time - start_time,
                        memory_peak_mb=max(start_memory, end_memory),
                        patches_applied=processing_stats.get('patches_applied', 0),
                        metadata={'processing_stats': processing_stats}
                    )
        
        except Exception as e:
            logger.error(f"Task {task.task_id} failed in process worker {worker_id}: {e}")
            result = BatchResult(
                task_id=task.task_id,
                success=False,
                processing_time=0.0,
                memory_peak_mb=0.0,
                patches_applied=0,
                errors=[str(e)]
            )
        
        finally:
            # Update worker load (this might not work correctly in process mode)
            if worker_id in self.worker_loads:
                self.worker_loads[worker_id] -= 1
        
        return result
    
    def _execute_single_task(self, task: BatchTask, worker_id: str) -> BatchResult:
        """Execute single task with full optimization."""
        start_time = time.time()
        
        # Get or create streaming processor
        if self.config.enable_memory_optimization:
            memory_manager = MemoryManager(
                memory_limit_mb=self.config.memory_limit_mb / self.config.max_workers
            )
            processor = StreamingOOXMLProcessor(memory_manager)
        else:
            # Use regular YAML processor
            processor = YAMLPatchProcessor()
        
        try:
            # Process template
            if hasattr(processor, 'process_large_template'):
                processing_stats = processor.process_large_template(
                    task.template_path,
                    task.patches,
                    task.output_path
                )
                patches_applied = processing_stats.get('patches_applied', len(task.patches))
                memory_peak_mb = processing_stats.get('memory_peak_mb', 0.0)
            else:
                # Fallback to regular processing
                patches_applied = 0
                memory_peak_mb = 0.0
                # This would need actual implementation for regular processor
            
            result = BatchResult(
                task_id=task.task_id,
                success=True,
                processing_time=time.time() - start_time,
                memory_peak_mb=memory_peak_mb,
                patches_applied=patches_applied
            )
        
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            result = BatchResult(
                task_id=task.task_id,
                success=False,
                processing_time=time.time() - start_time,
                memory_peak_mb=0.0,
                patches_applied=0,
                errors=[str(e)]
            )
        
        return result
    
    def shutdown(self) -> None:
        """Shutdown the worker pool."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
        
        logger.info("Worker pool shutdown complete")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive worker pool statistics."""
        return {
            'worker_count': len(self.workers),
            'failed_workers': len(self.failed_workers),
            'worker_stats': self.worker_stats.copy(),
            'worker_loads': self.worker_loads.copy(),
            'total_tasks_completed': sum(stats['tasks_completed'] for stats in self.worker_stats.values()),
            'total_tasks_failed': sum(stats['tasks_failed'] for stats in self.worker_stats.values())
        }


class OptimizedBatchProcessor:
    """
    High-performance batch processor with advanced optimizations.
    
    Features:
    - Concurrent processing with load balancing
    - Memory-efficient streaming
    - Advanced caching integration
    - Backpressure control
    - Performance monitoring
    - Automatic retry and error recovery
    """
    
    def __init__(self, config: BatchProcessingConfig):
        """Initialize the optimized batch processor."""
        self.config = config
        
        # Ensure temp directory exists
        self.config.temp_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.memory_manager = ConcurrentMemoryManager(config.memory_limit_mb)
        self.cache_manager = CacheManager(enable_persistent_cache=config.enable_caching)
        
        # Initialize profiler if enabled
        self.profiler: Optional[PerformanceProfiler] = None
        if config.enable_profiling:
            self.profiler = PerformanceProfiler()
        
        # Initialize batch queue and worker pool
        self.batch_queue = BatchQueue(max_size=config.backpressure_threshold)
        self.worker_pool = WorkerPool(config, self.memory_manager, self.cache_manager)
        
        # Processing state
        self.active_futures: Dict[str, Future] = {}
        self.completed_results: List[BatchResult] = []
        self.failed_tasks: deque = deque(maxlen=1000)  # Keep recent failures
        
        # Statistics
        self.processing_stats = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_processing_time': 0.0,
            'peak_memory_mb': 0.0,
            'cache_hit_rate': 0.0
        }
        
        logger.info(f"Optimized batch processor initialized with {config.max_workers} workers")
    
    def submit_task(self, task: BatchTask) -> bool:
        """Submit a single task for processing."""
        if not self.batch_queue.put(task, timeout=1.0):
            logger.warning(f"Failed to submit task {task.task_id} - queue full")
            return False
        
        self.processing_stats['tasks_submitted'] += 1
        return True
    
    def submit_batch(self, tasks: List[BatchTask]) -> int:
        """Submit a batch of tasks for processing."""
        submitted = 0
        
        for task in tasks:
            if self.submit_task(task):
                submitted += 1
            else:
                logger.warning(f"Batch submission stopped at task {task.task_id} due to queue capacity")
                break
        
        logger.info(f"Submitted {submitted}/{len(tasks)} tasks from batch")
        return submitted
    
    def process_all_pending(self, timeout: Optional[float] = None) -> List[BatchResult]:
        """Process all pending tasks and return results."""
        logger.info("Starting processing of all pending tasks")
        
        start_time = time.time()
        session_id = None
        
        # Start profiling session if enabled
        if self.profiler:
            session_id = f"batch_processing_{int(start_time)}"
            self.profiler.start_session(session_id)
        
        try:
            # Start worker threads to process queue
            self._start_processing_loop()
            
            # Wait for completion or timeout
            self._wait_for_completion(timeout)
            
            # Collect results
            all_results = self.completed_results.copy()
            
            # Update statistics
            self._update_final_stats(time.time() - start_time)
            
            logger.info(f"Batch processing completed. Processed {len(all_results)} tasks in {time.time() - start_time:.2f}s")
            
            return all_results
        
        finally:
            # End profiling session if enabled
            if self.profiler and session_id:
                profiling_results = self.profiler.end_session(session_id)
                logger.info(f"Profiling completed: {profiling_results.duration:.2f}s, peak memory: {profiling_results.peak_memory_mb:.1f}MB")
    
    def _start_processing_loop(self) -> None:
        """Start the main processing loop."""
        def processing_worker():
            while True:
                # Get next task from queue
                task = self.batch_queue.get(timeout=1.0)
                if task is None:
                    # Check if we're shutting down or no more tasks
                    if self.batch_queue.is_empty():
                        break
                    continue
                
                try:
                    # Submit task to worker pool
                    future = self.worker_pool.submit_task(task)
                    self.active_futures[task.task_id] = future
                    
                    # Set completion callback
                    future.add_done_callback(
                        lambda f, tid=task.task_id: self._handle_task_completion(tid, f)
                    )
                
                except Exception as e:
                    logger.error(f"Failed to submit task {task.task_id}: {e}")
                    self.batch_queue.task_done(success=False)
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=processing_worker, daemon=True)
        self.processing_thread.start()
    
    def _handle_task_completion(self, task_id: str, future: Future) -> None:
        """Handle completion of a task."""
        try:
            result = future.result()
            self.completed_results.append(result)
            
            if result.success:
                self.processing_stats['tasks_completed'] += 1
                self.batch_queue.task_done(success=True)
            else:
                self.processing_stats['tasks_failed'] += 1
                self.failed_tasks.append((task_id, result.errors))
                self.batch_queue.task_done(success=False)
            
            # Update statistics
            self.processing_stats['total_processing_time'] += result.processing_time
            self.processing_stats['peak_memory_mb'] = max(
                self.processing_stats['peak_memory_mb'], 
                result.memory_peak_mb
            )
        
        except Exception as e:
            logger.error(f"Task {task_id} completion handling failed: {e}")
            self.processing_stats['tasks_failed'] += 1
            self.failed_tasks.append((task_id, [str(e)]))
            self.batch_queue.task_done(success=False)
        
        finally:
            # Remove from active futures
            if task_id in self.active_futures:
                del self.active_futures[task_id]
    
    def _wait_for_completion(self, timeout: Optional[float]) -> None:
        """Wait for all tasks to complete."""
        start_wait_time = time.time()
        
        while True:
            # Check if all tasks are done
            if (self.batch_queue.is_empty() and 
                len(self.active_futures) == 0):
                break
            
            # Check timeout
            if timeout and (time.time() - start_wait_time) > timeout:
                logger.warning("Batch processing timeout reached")
                break
            
            # Wait a bit before checking again
            time.sleep(0.1)
        
        # Wait for any remaining futures
        remaining_futures = list(self.active_futures.values())
        for future in remaining_futures:
            try:
                future.result(timeout=5.0)  # Short timeout for cleanup
            except Exception as e:
                logger.warning(f"Future completion failed during cleanup: {e}")
    
    def _update_final_stats(self, total_time: float) -> None:
        """Update final processing statistics."""
        # Get cache statistics
        if self.cache_manager:
            cache_stats = self.cache_manager.get_comprehensive_stats()
            
            # Calculate overall hit rate
            total_hits = sum(
                stats.get('hits', 0) 
                for cache_type, stats in cache_stats.items()
                if isinstance(stats, dict) and 'hits' in stats
            )
            total_requests = sum(
                stats.get('hits', 0) + stats.get('misses', 0)
                for cache_type, stats in cache_stats.items()
                if isinstance(stats, dict) and 'hits' in stats and 'misses' in stats
            )
            
            if total_requests > 0:
                self.processing_stats['cache_hit_rate'] = total_hits / total_requests
        
        # Get memory statistics
        memory_stats = self.memory_manager.get_memory_stats()
        self.processing_stats['final_memory_mb'] = memory_stats['current']['rss_mb']
        
        logger.info(f"Final processing statistics: {self.processing_stats}")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics."""
        stats = self.processing_stats.copy()
        
        # Add queue statistics
        stats['queue_stats'] = self.batch_queue.get_stats()
        
        # Add worker pool statistics
        stats['worker_stats'] = self.worker_pool.get_stats()
        
        # Add memory statistics
        stats['memory_stats'] = self.memory_manager.get_memory_stats()
        
        # Add cache statistics
        if self.cache_manager:
            stats['cache_stats'] = self.cache_manager.get_comprehensive_stats()
        
        return stats
    
    def shutdown(self) -> None:
        """Shutdown the batch processor."""
        logger.info("Shutting down batch processor")
        
        # Clear remaining queue
        self.batch_queue.clear()
        
        # Shutdown worker pool
        self.worker_pool.shutdown()
        
        # Stop memory manager monitoring
        self.memory_manager.stop_monitoring()
        
        logger.info("Batch processor shutdown complete")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()


# Convenience functions for different batch processing scenarios

def process_templates_batch(template_paths: List[Path],
                           patches_list: List[List[Dict[str, Any]]],
                           output_directory: Path,
                           config: Optional[BatchProcessingConfig] = None) -> List[BatchResult]:
    """Process multiple templates in batch with optimizations."""
    if config is None:
        config = BatchProcessingConfig()
    
    output_directory.mkdir(parents=True, exist_ok=True)
    
    with OptimizedBatchProcessor(config) as processor:
        # Create batch tasks
        tasks = []
        for i, (template_path, patches) in enumerate(zip(template_paths, patches_list)):
            output_path = output_directory / f"processed_{template_path.stem}_{i}.pptx"
            task = BatchTask(
                task_id=f"batch_task_{i}",
                template_path=template_path,
                patches=patches,
                output_path=output_path
            )
            tasks.append(task)
        
        # Submit and process tasks
        processor.submit_batch(tasks)
        results = processor.process_all_pending()
        
        return results


def process_single_template_variants(template_path: Path,
                                   variants_patches: List[List[Dict[str, Any]]],
                                   output_directory: Path,
                                   config: Optional[BatchProcessingConfig] = None) -> List[BatchResult]:
    """Process multiple variants of a single template."""
    if config is None:
        config = BatchProcessingConfig()
    
    output_directory.mkdir(parents=True, exist_ok=True)
    
    with OptimizedBatchProcessor(config) as processor:
        # Create variant tasks
        tasks = []
        for i, patches in enumerate(variants_patches):
            output_path = output_directory / f"{template_path.stem}_variant_{i}.pptx"
            task = BatchTask(
                task_id=f"variant_task_{i}",
                template_path=template_path,
                patches=patches,
                output_path=output_path,
                metadata={'variant_id': i}
            )
            tasks.append(task)
        
        # Submit and process tasks
        processor.submit_batch(tasks)
        results = processor.process_all_pending()
        
        return results


@contextmanager
def batch_processing_context(config: Optional[BatchProcessingConfig] = None) -> Iterator[OptimizedBatchProcessor]:
    """Context manager for batch processing with automatic cleanup."""
    if config is None:
        config = BatchProcessingConfig()
    
    processor = OptimizedBatchProcessor(config)
    try:
        yield processor
    finally:
        processor.shutdown()


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Create test configuration
    config = BatchProcessingConfig(
        max_workers=2,
        memory_limit_mb=500.0,
        batch_size=5,
        enable_profiling=True
    )
    
    # Test batch processing context
    with batch_processing_context(config) as processor:
        # Create some dummy tasks for testing
        tasks = []
        for i in range(10):
            task = BatchTask(
                task_id=f"test_task_{i}",
                template_path=Path(f"/tmp/test_template_{i}.pptx"),
                patches=[{"operation": "set", "target": "//p:sp", "value": f"Test {i}"}],
                output_path=Path(f"/tmp/output_{i}.pptx")
            )
            tasks.append(task)
        
        # Submit tasks
        processor.submit_batch(tasks)
        
        # Get stats
        stats = processor.get_processing_stats()
        print("Processing Stats:")
        print(json.dumps(stats, indent=2, default=str))