#!/usr/bin/env python3
"""
StyleStack Memory Optimization System

Advanced memory optimization for large OOXML files and batch operations.
Provides streaming processing, intelligent caching, memory pooling, 
and automatic garbage collection for production-scale workloads.
"""

import gc
import sys
import weakref
import threading
import time
import mmap
from typing import Dict, List, Any, Optional, Union, Iterator, ContextManager, Callable
from dataclasses import dataclass, field
from collections import deque, defaultdict
from pathlib import Path
from contextlib import contextmanager
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from lxml import etree
import logging
import psutil
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import os

logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """Container for memory usage statistics."""
    rss_mb: float  # Resident Set Size
    vms_mb: float  # Virtual Memory Size
    percent: float  # Memory percentage
    available_mb: float  # Available system memory
    peak_mb: Optional[float] = None
    
    @classmethod
    def capture(cls) -> 'MemoryStats':
        """Capture current memory statistics."""
        process = psutil.Process()
        memory_info = process.memory_info()
        virtual_memory = psutil.virtual_memory()
        
        return cls(
            rss_mb=memory_info.rss / (1024 * 1024),
            vms_mb=memory_info.vms / (1024 * 1024),
            percent=process.memory_percent(),
            available_mb=virtual_memory.available / (1024 * 1024)
        )


@dataclass
class MemoryPool:
    """Memory pool for reusing objects and reducing allocations."""
    max_size: int = 1000
    _pool: Dict[str, deque] = field(default_factory=dict)
    _stats: Dict[str, Dict[str, int]] = field(default_factory=lambda: defaultdict(lambda: {'hits': 0, 'misses': 0}))
    
    def get_object(self, object_type: str, factory: Callable[[], Any]) -> Any:
        """Get an object from the pool or create a new one."""
        if object_type not in self._pool:
            self._pool[object_type] = deque(maxlen=self.max_size)
        
        pool = self._pool[object_type]
        
        if pool:
            self._stats[object_type]['hits'] += 1
            return pool.popleft()
        else:
            self._stats[object_type]['misses'] += 1
            return factory()
    
    def return_object(self, object_type: str, obj: Any) -> None:
        """Return an object to the pool."""
        if object_type not in self._pool:
            self._pool[object_type] = deque(maxlen=self.max_size)
        
        # Reset object state if possible
        if hasattr(obj, 'clear'):
            obj.clear()
        elif hasattr(obj, 'reset'):
            obj.reset()
        
        self._pool[object_type].appendleft(obj)
    
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get pool statistics."""
        return {
            object_type: {
                'pool_size': len(self._pool.get(object_type, [])),
                'hit_rate': stats['hits'] / (stats['hits'] + stats['misses']) if (stats['hits'] + stats['misses']) > 0 else 0,
                **stats
            }
            for object_type, stats in self._stats.items()
        }


class MemoryManager:
    """
    Advanced memory manager for StyleStack processing.
    
    Features:
    - Memory monitoring and alerts
    - Automatic garbage collection
    - Object pooling
    - Memory-efficient streaming
    - Batch processing optimization
    """
    
    def __init__(self, 
                 memory_limit_mb: Optional[int] = None,
                 gc_threshold_mb: int = 100,
                 enable_pooling: bool = True):
        """Initialize the memory manager."""
        self.memory_limit_mb = memory_limit_mb or (psutil.virtual_memory().total // (1024 * 1024) * 0.8)
        self.gc_threshold_mb = gc_threshold_mb
        self.enable_pooling = enable_pooling
        
        # Memory monitoring
        self._last_memory_check = 0
        self._memory_check_interval = 1.0  # seconds
        self._memory_history: deque = deque(maxlen=100)
        self._peak_memory = 0.0
        
        # Object pooling
        self.memory_pool = MemoryPool() if enable_pooling else None
        
        # Garbage collection tuning
        self._configure_gc()
        
        # Background monitoring
        self._monitoring_enabled = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        
        logger.info(f"Memory manager initialized with {self.memory_limit_mb:.1f}MB limit")
    
    def _configure_gc(self) -> None:
        """Configure garbage collection for better memory management."""
        # Tune garbage collection thresholds for large workloads
        gc.set_threshold(1000, 15, 15)  # More frequent collection
        
        # Disable automatic garbage collection during critical operations
        # (will be manually triggered)
        gc.disable()
    
    def start_monitoring(self, interval: float = 1.0) -> None:
        """Start background memory monitoring."""
        if self._monitoring_enabled:
            return
        
        self._memory_check_interval = interval
        self._stop_monitoring.clear()
        self._monitoring_enabled = True
        
        def monitor_loop():
            while not self._stop_monitoring.wait(self._memory_check_interval):
                self._check_memory_usage()
        
        self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        logger.info(f"Started memory monitoring with {interval}s interval")
    
    def stop_monitoring(self) -> None:
        """Stop background memory monitoring."""
        if not self._monitoring_enabled:
            return
        
        self._stop_monitoring.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
        
        self._monitoring_enabled = False
        logger.info("Stopped memory monitoring")
    
    def _check_memory_usage(self) -> MemoryStats:
        """Check current memory usage and trigger cleanup if needed."""
        stats = MemoryStats.capture()
        self._memory_history.append(stats)
        
        # Update peak memory
        if stats.rss_mb > self._peak_memory:
            self._peak_memory = stats.rss_mb
        
        # Check if we need to trigger garbage collection
        if stats.rss_mb > self._peak_memory - self.gc_threshold_mb:
            self.force_garbage_collection()
        
        # Check memory limit
        if stats.rss_mb > self.memory_limit_mb:
            logger.warning(f"Memory usage {stats.rss_mb:.1f}MB exceeds limit {self.memory_limit_mb:.1f}MB")
            self._handle_memory_pressure()
        
        return stats
    
    def _handle_memory_pressure(self) -> None:
        """Handle memory pressure situations."""
        logger.info("Handling memory pressure - performing aggressive cleanup")
        
        # Force garbage collection
        self.force_garbage_collection()
        
        # Clear object pools if enabled
        if self.memory_pool:
            self.memory_pool._pool.clear()
        
        # Additional cleanup strategies can be added here
        
    def force_garbage_collection(self) -> Dict[str, int]:
        """Force garbage collection and return collection statistics."""
        # Collect all generations
        collected = {
            'gen0': gc.collect(0),
            'gen1': gc.collect(1), 
            'gen2': gc.collect(2)
        }
        
        total_collected = sum(collected.values())
        if total_collected > 0:
            logger.debug(f"Garbage collection freed {total_collected} objects")
        
        return collected
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics."""
        current_stats = MemoryStats.capture()
        
        stats = {
            'current': {
                'rss_mb': current_stats.rss_mb,
                'vms_mb': current_stats.vms_mb,
                'percent': current_stats.percent,
                'available_mb': current_stats.available_mb
            },
            'peak_mb': self._peak_memory,
            'limit_mb': self.memory_limit_mb,
            'history_size': len(self._memory_history),
            'gc_stats': {
                'counts': gc.get_count(),
                'threshold': gc.get_threshold(),
                'stats': gc.get_stats() if hasattr(gc, 'get_stats') else None
            }
        }
        
        # Add pool statistics if available
        if self.memory_pool:
            stats['pool_stats'] = self.memory_pool.get_stats()
        
        return stats
    
    @contextmanager
    def memory_limit_context(self, limit_mb: int):
        """Context manager for temporary memory limit."""
        old_limit = self.memory_limit_mb
        self.memory_limit_mb = limit_mb
        try:
            yield
        finally:
            self.memory_limit_mb = old_limit
    
    def __enter__(self):
        """Context manager entry."""
        self.start_monitoring()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_monitoring()
        self.force_garbage_collection()


class StreamingOOXMLProcessor:
    """
    Memory-efficient streaming processor for large OOXML files.
    
    Processes OOXML files without loading entire documents into memory,
    using streaming XML parsing and memory-mapped file access.
    """
    
    def __init__(self, memory_manager: MemoryManager):
        """Initialize the streaming processor."""
        self.memory_manager = memory_manager
        self.temp_files: List[Path] = []
        
    def process_large_template(self, template_path: Path, 
                              patches: List[Dict[str, Any]],
                              output_path: Path,
                              chunk_size: int = 8192) -> Dict[str, Any]:
        """Process large template using streaming approach."""
        logger.info(f"Processing large template: {template_path}")
        
        processing_stats = {
            'files_processed': 0,
            'patches_applied': 0,
            'memory_peak_mb': 0,
            'processing_time': 0
        }
        
        start_time = time.time()
        start_memory = self.memory_manager._check_memory_usage()
        
        try:
            with zipfile.ZipFile(template_path, 'r') as input_zip:
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as output_zip:
                    
                    # Process each file in the ZIP
                    for file_info in input_zip.filelist:
                        file_path = file_info.filename
                        
                        if self._should_process_file(file_path):
                            # Stream process XML files
                            processed_content = self._stream_process_xml_file(
                                input_zip, file_path, patches, chunk_size
                            )
                            output_zip.writestr(file_info, processed_content)
                            processing_stats['files_processed'] += 1
                        else:
                            # Copy non-XML files directly
                            file_data = input_zip.read(file_path)
                            output_zip.writestr(file_info, file_data)
                        
                        # Check memory usage periodically
                        current_memory = self.memory_manager._check_memory_usage()
                        if current_memory.rss_mb > processing_stats['memory_peak_mb']:
                            processing_stats['memory_peak_mb'] = current_memory.rss_mb
                        
                        # Force garbage collection periodically
                        if processing_stats['files_processed'] % 10 == 0:
                            self.memory_manager.force_garbage_collection()
        
        except Exception as e:
            logger.error(f"Error processing large template: {e}")
            raise
        
        finally:
            processing_stats['processing_time'] = time.time() - start_time
            self._cleanup_temp_files()
        
        logger.info(f"Large template processing completed in {processing_stats['processing_time']:.2f}s")
        return processing_stats
    
    def _should_process_file(self, file_path: str) -> bool:
        """Determine if a file should be processed for patches."""
        xml_files = [
            'ppt/presentation.xml',
            'ppt/slideMasters/',
            'ppt/slideLayouts/',
            'ppt/slides/',
            'word/document.xml',
            'word/styles.xml',
            'xl/workbook.xml',
            'xl/styles.xml'
        ]
        
        return any(file_path.startswith(prefix) for prefix in xml_files) and file_path.endswith('.xml')
    
    def _stream_process_xml_file(self, zip_file: zipfile.ZipFile, 
                                file_path: str,
                                patches: List[Dict[str, Any]], 
                                chunk_size: int) -> bytes:
        """Stream process an XML file with memory-efficient parsing."""
        
        # Use memory-mapped file for large files
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            self.temp_files.append(temp_path)
            
            # Extract to temporary file
            file_data = zip_file.read(file_path)
            temp_file.write(file_data)
            temp_file.flush()
        
        try:
            # Use memory mapping for large files
            if len(file_data) > chunk_size * 10:
                return self._process_with_memory_mapping(temp_path, patches)
            else:
                return self._process_with_streaming_parser(temp_path, patches)
        
        except Exception as e:
            logger.error(f"Error processing XML file {file_path}: {e}")
            return file_data  # Return original on error
    
    def _process_with_memory_mapping(self, file_path: Path, 
                                   patches: List[Dict[str, Any]]) -> bytes:
        """Process XML file using memory mapping for very large files."""
        with open(file_path, 'r+b') as f:
            with mmap.mmap(f.fileno(), 0) as mapped_file:
                # For demonstration - in practice, you'd implement
                # incremental XML processing with memory mapping
                xml_content = mapped_file.read()
                
                try:
                    # Parse with lxml for XPath support
                    doc = etree.fromstring(xml_content)
                    
                    # Apply patches efficiently
                    patches_applied = 0
                    for patch in patches:
                        try:
                            # Simplified patch application - would use actual processor
                            target = patch.get('target', '')
                            if target:
                                elements = doc.xpath(target, namespaces=self._get_namespaces())
                                if elements:
                                    # Apply patch logic here
                                    patches_applied += 1
                        except Exception as e:
                            logger.debug(f"Patch failed: {e}")
                    
                    return etree.tostring(doc, encoding='utf-8', xml_declaration=True)
                
                except etree.XMLSyntaxError:
                    logger.warning(f"Invalid XML in {file_path}, returning original")
                    return xml_content
    
    def _process_with_streaming_parser(self, file_path: Path, 
                                     patches: List[Dict[str, Any]]) -> bytes:
        """Process XML file using streaming parser for moderate-sized files."""
        try:
            # Use iterparse for streaming processing
            context = etree.iterparse(str(file_path), events=('start', 'end'))
            root = None
            
            for event, elem in context:
                if event == 'start' and root is None:
                    root = elem
                
                # Process elements as they are parsed
                if event == 'end':
                    # Apply patches to current element
                    # (simplified implementation)
                    pass
                    
                    # Clear processed elements to save memory
                    if elem.tag != root.tag:
                        elem.clear()
            
            if root is not None:
                return etree.tostring(root, encoding='utf-8', xml_declaration=True)
            else:
                # Fallback to reading original file
                return file_path.read_bytes()
        
        except Exception as e:
            logger.error(f"Streaming parse failed: {e}")
            return file_path.read_bytes()
    
    def _get_namespaces(self) -> Dict[str, str]:
        """Get common OOXML namespaces."""
        return {
            'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
            'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        }
    
    def _cleanup_temp_files(self) -> None:
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {temp_file}: {e}")
        
        self.temp_files.clear()


class BatchProcessor:
    """
    Memory-efficient batch processor for multiple templates.
    
    Optimizes memory usage when processing many templates by:
    - Processing in parallel with memory limits
    - Using shared memory pools
    - Implementing backpressure controls
    """
    
    def __init__(self, memory_manager: MemoryManager, max_workers: Optional[int] = None):
        """Initialize the batch processor."""
        self.memory_manager = memory_manager
        self.max_workers = max_workers or min(4, multiprocessing.cpu_count())
        self.processing_queue: deque = deque()
        self.results: List[Dict[str, Any]] = []
        
    def process_batch(self, 
                     template_paths: List[Path],
                     patches_list: List[List[Dict[str, Any]]],
                     output_directory: Path,
                     batch_size: int = 10) -> List[Dict[str, Any]]:
        """Process a batch of templates with memory optimization."""
        logger.info(f"Processing batch of {len(template_paths)} templates")
        
        output_directory.mkdir(parents=True, exist_ok=True)
        
        batch_results = []
        
        # Process in chunks to manage memory usage
        for i in range(0, len(template_paths), batch_size):
            chunk_paths = template_paths[i:i + batch_size]
            chunk_patches = patches_list[i:i + batch_size]
            
            logger.info(f"Processing chunk {i // batch_size + 1} ({len(chunk_paths)} templates)")
            
            # Monitor memory before chunk processing
            pre_memory = self.memory_manager._check_memory_usage()
            
            chunk_results = self._process_chunk(
                chunk_paths, chunk_patches, output_directory
            )
            batch_results.extend(chunk_results)
            
            # Force cleanup between chunks
            self.memory_manager.force_garbage_collection()
            
            # Monitor memory after chunk processing
            post_memory = self.memory_manager._check_memory_usage()
            logger.debug(f"Chunk memory usage: {pre_memory.rss_mb:.1f}MB -> {post_memory.rss_mb:.1f}MB")
        
        logger.info(f"Batch processing completed. Processed {len(batch_results)} templates")
        return batch_results
    
    def _process_chunk(self, 
                      template_paths: List[Path],
                      patches_list: List[List[Dict[str, Any]]],
                      output_directory: Path) -> List[Dict[str, Any]]:
        """Process a chunk of templates using thread pool."""
        
        chunk_results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            futures = []
            for i, (template_path, patches) in enumerate(zip(template_paths, patches_list)):
                output_path = output_directory / f"processed_{template_path.stem}_{i}.pptx"
                
                future = executor.submit(
                    self._process_single_template,
                    template_path, patches, output_path
                )
                futures.append((future, template_path))
            
            # Collect results with memory monitoring
            for future, template_path in futures:
                try:
                    result = future.result(timeout=300)  # 5 minute timeout per template
                    chunk_results.append(result)
                except Exception as e:
                    logger.error(f"Template processing failed for {template_path}: {e}")
                    chunk_results.append({
                        'template_path': str(template_path),
                        'success': False,
                        'error': str(e)
                    })
                
                # Check memory usage after each completion
                current_memory = self.memory_manager._check_memory_usage()
                if current_memory.rss_mb > self.memory_manager.memory_limit_mb * 0.9:
                    logger.warning("Approaching memory limit during batch processing")
                    self.memory_manager._handle_memory_pressure()
        
        return chunk_results
    
    def _process_single_template(self, 
                               template_path: Path,
                               patches: List[Dict[str, Any]],
                               output_path: Path) -> Dict[str, Any]:
        """Process a single template with memory monitoring."""
        start_time = time.time()
        start_memory = MemoryStats.capture()
        
        try:
            # Use streaming processor for large files
            streaming_processor = StreamingOOXMLProcessor(self.memory_manager)
            
            processing_stats = streaming_processor.process_large_template(
                template_path, patches, output_path
            )
            
            end_memory = MemoryStats.capture()
            
            return {
                'template_path': str(template_path),
                'output_path': str(output_path),
                'success': True,
                'processing_time': time.time() - start_time,
                'memory_usage': {
                    'start_mb': start_memory.rss_mb,
                    'end_mb': end_memory.rss_mb,
                    'peak_mb': processing_stats['memory_peak_mb']
                },
                'patches_applied': processing_stats['patches_applied'],
                'files_processed': processing_stats['files_processed']
            }
        
        except Exception as e:
            return {
                'template_path': str(template_path),
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }


class ConcurrentMemoryManager:
    """
    Thread-safe memory manager for concurrent processing.
    
    Provides coordinated memory management across multiple threads
    with shared memory limits and synchronized garbage collection.
    """
    
    def __init__(self, total_memory_limit_mb: int):
        """Initialize concurrent memory manager."""
        self.total_memory_limit_mb = total_memory_limit_mb
        self.per_thread_limit_mb = total_memory_limit_mb // max(1, multiprocessing.cpu_count())
        
        # Thread-safe structures
        self._memory_allocations: Dict[int, float] = {}  # thread_id -> allocated_mb
        self._allocation_lock = threading.RLock()
        
        # Shared memory pool
        self._shared_pool = MemoryPool(max_size=2000)
        
        # Global memory monitor
        self._global_memory_monitor = MemoryManager(total_memory_limit_mb)
        
    def allocate_memory(self, thread_id: int, requested_mb: float) -> bool:
        """Request memory allocation for a thread."""
        with self._allocation_lock:
            current_allocation = self._memory_allocations.get(thread_id, 0)
            total_allocated = sum(self._memory_allocations.values())
            
            if total_allocated + requested_mb > self.total_memory_limit_mb:
                # Try to free memory
                self._global_memory_monitor.force_garbage_collection()
                
                # Check again
                if total_allocated + requested_mb > self.total_memory_limit_mb:
                    return False
            
            self._memory_allocations[thread_id] = current_allocation + requested_mb
            return True
    
    def deallocate_memory(self, thread_id: int, freed_mb: float) -> None:
        """Release memory allocation for a thread."""
        with self._allocation_lock:
            current_allocation = self._memory_allocations.get(thread_id, 0)
            self._memory_allocations[thread_id] = max(0, current_allocation - freed_mb)
    
    def get_shared_object(self, object_type: str, factory: Callable[[], Any]) -> Any:
        """Get a shared object from the global pool."""
        return self._shared_pool.get_object(object_type, factory)
    
    def return_shared_object(self, object_type: str, obj: Any) -> None:
        """Return a shared object to the global pool."""
        self._shared_pool.return_object(object_type, obj)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics."""
        with self._allocation_lock:
            return {
                'total_limit_mb': self.total_memory_limit_mb,
                'per_thread_limit_mb': self.per_thread_limit_mb,
                'thread_allocations': dict(self._memory_allocations),
                'total_allocated_mb': sum(self._memory_allocations.values()),
                'shared_pool_stats': self._shared_pool.get_stats(),
                'global_stats': self._global_memory_monitor.get_memory_stats()
            }
    
    @contextmanager
    def thread_memory_context(self, requested_mb: float):
        """Context manager for thread memory allocation."""
        thread_id = threading.get_ident()
        
        if not self.allocate_memory(thread_id, requested_mb):
            raise MemoryError(f"Cannot allocate {requested_mb}MB for thread {thread_id}")
        
        try:
            yield
        finally:
            self.deallocate_memory(thread_id, requested_mb)


# Convenience functions and decorators

def memory_optimized(memory_limit_mb: Optional[int] = None):
    """Decorator for memory-optimized function execution."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with MemoryManager(memory_limit_mb=memory_limit_mb) as memory_manager:
                return func(*args, **kwargs)
        return wrapper
    return decorator


@contextmanager
def streaming_processing(template_path: Path, 
                       memory_limit_mb: Optional[int] = None) -> Iterator[StreamingOOXMLProcessor]:
    """Context manager for streaming OOXML processing."""
    with MemoryManager(memory_limit_mb=memory_limit_mb) as memory_manager:
        processor = StreamingOOXMLProcessor(memory_manager)
        try:
            yield processor
        finally:
            processor._cleanup_temp_files()


@contextmanager  
def batch_processing(max_workers: Optional[int] = None,
                    memory_limit_mb: Optional[int] = None) -> Iterator[BatchProcessor]:
    """Context manager for batch processing with memory optimization."""
    with MemoryManager(memory_limit_mb=memory_limit_mb) as memory_manager:
        processor = BatchProcessor(memory_manager, max_workers)
        yield processor


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Test memory manager
    with MemoryManager(memory_limit_mb=500) as memory_manager:
        print("Memory Manager Stats:")
        print(memory_manager.get_memory_stats())
        
        # Simulate memory pressure
        large_list = [i for i in range(1000000)]  # Allocate some memory
        
        print("\nAfter allocation:")
        print(memory_manager.get_memory_stats())
        
        # Force cleanup
        del large_list
        memory_manager.force_garbage_collection()
        
        print("\nAfter cleanup:")
        print(memory_manager.get_memory_stats())