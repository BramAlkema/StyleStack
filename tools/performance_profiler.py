#!/usr/bin/env python3
"""
StyleStack Performance Profiling System

Comprehensive profiling tools to identify bottlenecks in the JSON-to-OOXML processing pipeline.
Provides detailed analysis of CPU usage, memory consumption, I/O operations, and processing patterns.
"""


from typing import Dict, List, Any, Optional, Callable, Union, NamedTuple
import time
try:
    import psutil
except ImportError:
    psutil = None  # Optional dependency for system monitoring
import tracemalloc
import pstats
import gc
import threading
import functools
import contextlib
import json
import sys
from dataclasses import dataclass, field
from collections import defaultdict, deque
from pathlib import Path
import logging
from datetime import datetime, timedelta
import weakref

# Configure logging
logger = logging.getLogger(__name__)


class ProfiledFunction(NamedTuple):
    """Container for function profiling data."""
    name: str
    call_count: int
    total_time: float
    average_time: float
    max_time: float
    min_time: float
    memory_usage: Optional[float] = None


@dataclass
class PerformanceSnapshot:
    """Snapshot of system performance at a specific point in time."""
    timestamp: float
    cpu_percent: float
    memory_usage_mb: float
    memory_percent: float
    io_counters: Optional[Dict[str, int]] = None
    thread_count: int = 0
    heap_size: int = 0
    garbage_objects: int = 0
    
    @classmethod
    def capture(cls) -> 'PerformanceSnapshot':
        """Capture current system performance metrics."""
        process = psutil.Process()
        
        # Get memory info
        memory_info = process.memory_info()
        memory_usage_mb = memory_info.rss / (1024 * 1024)
        
        # Get I/O counters if available
        io_counters = None
        try:
            io_info = process.io_counters()
            io_counters = {
                'read_count': io_info.read_count,
                'write_count': io_info.write_count,
                'read_bytes': io_info.read_bytes,
                'write_bytes': io_info.write_bytes
            }
        except (AttributeError, OSError):
            pass
        
        return cls(
            timestamp=time.time(),
            cpu_percent=process.cpu_percent(),
            memory_usage_mb=memory_usage_mb,
            memory_percent=process.memory_percent(),
            io_counters=io_counters,
            thread_count=process.num_threads(),
            heap_size=sys.getsizeof(gc.get_objects()),
            garbage_objects=len(gc.get_objects())
        )


@dataclass
class ProfilingSession:
    """Container for a complete profiling session."""
    session_id: str
    start_time: float
    end_time: Optional[float] = None
    snapshots: List[PerformanceSnapshot] = field(default_factory=list)
    function_profiles: Dict[str, ProfiledFunction] = field(default_factory=dict)
    memory_profile: Optional[Dict[str, Any]] = None
    cprofile_stats: Optional[pstats.Stats] = None
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """Get session duration in seconds."""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time
    
    @property
    def peak_memory_mb(self) -> float:
        """Get peak memory usage in MB."""
        if not self.snapshots:
            return 0.0
        return max(snapshot.memory_usage_mb for snapshot in self.snapshots)
    
    @property
    def average_cpu_percent(self) -> float:
        """Get average CPU usage percentage."""
        if not self.snapshots:
            return 0.0
        return sum(snapshot.cpu_percent for snapshot in self.snapshots) / len(self.snapshots)


class PerformanceProfiler:
    """
    Comprehensive performance profiler for StyleStack processing pipeline.
    
    Provides CPU profiling, memory tracking, I/O monitoring, and custom metrics.
    Supports both real-time monitoring and post-processing analysis.
    """
    
    def __init__(self, enable_memory_profiling: bool = True):
        """Initialize the performance profiler."""
        self.enable_memory_profiling = enable_memory_profiling
        
        # Active profiling sessions
        self.active_sessions: Dict[str, ProfilingSession] = {}
        
        # Global performance tracking
        self.global_function_times: Dict[str, List[float]] = defaultdict(list)
        self.global_memory_usage: deque = deque(maxlen=1000)  # Keep last 1000 measurements
        
        # Performance monitoring thread
        self._monitoring_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        self._monitor_interval = 1.0  # seconds
        
        # Memory profiling
        self._memory_profiler_active = False
        
        # Custom metrics tracking
        self.custom_counters: Dict[str, int] = defaultdict(int)
        self.custom_timers: Dict[str, List[float]] = defaultdict(list)
        self.custom_gauges: Dict[str, float] = {}
        
        # Weak references to track object lifecycle
        self.tracked_objects: weakref.WeakSet = weakref.WeakSet()
        
        logger.info("Performance profiler initialized")
    
    def start_session(self, session_id: str) -> str:
        """Start a new profiling session."""
        if session_id in self.active_sessions:
            logger.warning(f"Profiling session '{session_id}' already active")
            return session_id
        
        session = ProfilingSession(
            session_id=session_id,
            start_time=time.time()
        )
        
        self.active_sessions[session_id] = session
        
        # Start memory profiling if enabled
        if self.enable_memory_profiling:
            tracemalloc.start()
            self._memory_profiler_active = True
        
        # Take initial snapshot
        session.snapshots.append(PerformanceSnapshot.capture())
        
        logger.info(f"Started profiling session: {session_id}")
        return session_id
    
    def end_session(self, session_id: str) -> ProfilingSession:
        """End a profiling session and return results."""
        if session_id not in self.active_sessions:
            raise ValueError(f"No active session with ID: {session_id}")
        
        session = self.active_sessions[session_id]
        session.end_time = time.time()
        
        # Take final snapshot
        session.snapshots.append(PerformanceSnapshot.capture())
        
        # Capture memory profile if enabled
        if self._memory_profiler_active:
            current, peak = tracemalloc.get_traced_memory()
            session.memory_profile = {
                'current_mb': current / (1024 * 1024),
                'peak_mb': peak / (1024 * 1024),
                'snapshot_count': len(session.snapshots)
            }
            tracemalloc.stop()
            self._memory_profiler_active = False
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        
        logger.info(f"Ended profiling session: {session_id} (duration: {session.duration:.2f}s)")
        return session
    
    def profile_function(self, func: Optional[Callable] = None, *, 
                        name: Optional[str] = None,
                        track_memory: bool = False) -> Union[Callable, Any]:
        """
        Decorator or context manager to profile function execution.
        
        Can be used as:
        @profiler.profile_function
        def my_function(): ...
        
        Or:
        @profiler.profile_function(name="custom_name", track_memory=True)
        def my_function(): ...
        
        Or as context manager:
        with profiler.profile_function(name="operation"):
            # code to profile
        """
        
        def decorator(f: Callable) -> Callable:
            function_name = name or f.__name__
            
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                return self._profile_execution(f, function_name, track_memory, *args, **kwargs)
            
            return wrapper
        
        # If called as context manager
        if func is None:
            return _ProfilerContextManager(self, name or "anonymous", track_memory)
        
        # If called as simple decorator
        return decorator(func)
    
    def _profile_execution(self, func: Callable, function_name: str, 
                          track_memory: bool, *args, **kwargs) -> Any:
        """Execute function with profiling."""
        start_time = time.time()
        start_memory = None
        
        if track_memory and self.enable_memory_profiling:
            gc.collect()
            start_memory = psutil.Process().memory_info().rss
        
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            success = False
            raise
        finally:
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Track execution time
            self.global_function_times[function_name].append(execution_time)
            
            # Calculate memory usage if requested
            memory_delta = None
            if track_memory and start_memory is not None:
                end_memory = psutil.Process().memory_info().rss
                memory_delta = (end_memory - start_memory) / (1024 * 1024)  # MB
            
            # Update function profiles in active sessions
            for session in self.active_sessions.values():
                if function_name in session.function_profiles:
                    profile = session.function_profiles[function_name]
                    new_profile = ProfiledFunction(
                        name=function_name,
                        call_count=profile.call_count + 1,
                        total_time=profile.total_time + execution_time,
                        average_time=(profile.total_time + execution_time) / (profile.call_count + 1),
                        max_time=max(profile.max_time, execution_time),
                        min_time=min(profile.min_time, execution_time),
                        memory_usage=memory_delta
                    )
                else:
                    new_profile = ProfiledFunction(
                        name=function_name,
                        call_count=1,
                        total_time=execution_time,
                        average_time=execution_time,
                        max_time=execution_time,
                        min_time=execution_time,
                        memory_usage=memory_delta
                    )
                
                session.function_profiles[function_name] = new_profile
        
        return result
    
    def start_continuous_monitoring(self, interval: float = 1.0) -> None:
        """Start continuous system monitoring in background thread."""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            logger.warning("Continuous monitoring already active")
            return
        
        self._monitor_interval = interval
        self._stop_monitoring.clear()
        
        def monitoring_loop():
            while not self._stop_monitoring.wait(self._monitor_interval):
                snapshot = PerformanceSnapshot.capture()
                
                # Add snapshot to all active sessions
                for session in self.active_sessions.values():
                    session.snapshots.append(snapshot)
                
                # Track global memory usage
                self.global_memory_usage.append(snapshot.memory_usage_mb)
        
        self._monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self._monitoring_thread.start()
        
        logger.info(f"Started continuous monitoring with {interval}s interval")
    
    def stop_continuous_monitoring(self) -> None:
        """Stop continuous system monitoring."""
        if self._monitoring_thread:
            self._stop_monitoring.set()
            self._monitoring_thread.join(timeout=5.0)
            self._monitoring_thread = None
        
        logger.info("Stopped continuous monitoring")
    
    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment a custom counter metric."""
        self.custom_counters[name] += value
    
    def record_timer(self, name: str, value: float) -> None:
        """Record a timing measurement."""
        self.custom_timers[name].append(value)
    
    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge metric value."""
        self.custom_gauges[name] = value
    
    def track_object(self, obj: Any) -> None:
        """Track an object's lifecycle for memory leak detection."""
        self.tracked_objects.add(obj)
    
    def get_performance_summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        if session_id:
            if session_id not in self.active_sessions:
                raise ValueError(f"No active session: {session_id}")
            session = self.active_sessions[session_id]
            return self._generate_session_summary(session)
        else:
            return self._generate_global_summary()
    
    def _generate_session_summary(self, session: ProfilingSession) -> Dict[str, Any]:
        """Generate summary for specific session."""
        return {
            'session_id': session.session_id,
            'duration_seconds': session.duration,
            'peak_memory_mb': session.peak_memory_mb,
            'average_cpu_percent': session.average_cpu_percent,
            'snapshot_count': len(session.snapshots),
            'functions_profiled': len(session.function_profiles),
            'function_profiles': {
                name: {
                    'call_count': profile.call_count,
                    'total_time': profile.total_time,
                    'average_time': profile.average_time,
                    'max_time': profile.max_time,
                    'min_time': profile.min_time,
                    'memory_usage_mb': profile.memory_usage
                }
                for name, profile in session.function_profiles.items()
            },
            'memory_profile': session.memory_profile,
            'custom_metrics': session.custom_metrics
        }
    
    def _generate_global_summary(self) -> Dict[str, Any]:
        """Generate global performance summary."""
        return {
            'active_sessions': len(self.active_sessions),
            'global_function_stats': {
                name: {
                    'call_count': len(times),
                    'total_time': sum(times),
                    'average_time': sum(times) / len(times) if times else 0,
                    'max_time': max(times) if times else 0,
                    'min_time': min(times) if times else 0
                }
                for name, times in self.global_function_times.items()
            },
            'memory_usage_history': list(self.global_memory_usage),
            'custom_counters': dict(self.custom_counters),
            'custom_timers': {
                name: {
                    'count': len(times),
                    'total': sum(times),
                    'average': sum(times) / len(times) if times else 0,
                    'max': max(times) if times else 0,
                    'min': min(times) if times else 0
                }
                for name, times in self.custom_timers.items()
            },
            'custom_gauges': dict(self.custom_gauges),
            'tracked_objects_count': len(self.tracked_objects)
        }
    
    def export_performance_data(self, session_id: str, output_path: Path) -> None:
        """Export detailed performance data to JSON file."""
        if session_id not in self.active_sessions:
            raise ValueError(f"No active session: {session_id}")
        
        session = self.active_sessions[session_id]
        data = self._generate_session_summary(session)
        
        # Add detailed snapshots
        data['detailed_snapshots'] = [
            {
                'timestamp': snapshot.timestamp,
                'cpu_percent': snapshot.cpu_percent,
                'memory_usage_mb': snapshot.memory_usage_mb,
                'memory_percent': snapshot.memory_percent,
                'io_counters': snapshot.io_counters,
                'thread_count': snapshot.thread_count,
                'heap_size': snapshot.heap_size,
                'garbage_objects': snapshot.garbage_objects
            }
            for snapshot in session.snapshots
        ]
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Exported performance data to: {output_path}")
    
    def generate_bottleneck_report(self, session_id: str) -> Dict[str, Any]:
        """Analyze profiling data to identify performance bottlenecks."""
        if session_id not in self.active_sessions:
            raise ValueError(f"No active session: {session_id}")
        
        session = self.active_sessions[session_id]
        
        # Identify slowest functions
        slowest_functions = sorted(
            session.function_profiles.values(),
            key=lambda p: p.total_time,
            reverse=True
        )[:10]
        
        # Identify memory-intensive functions
        memory_intensive = [
            profile for profile in session.function_profiles.values()
            if profile.memory_usage and profile.memory_usage > 10  # > 10MB
        ]
        
        # Analyze CPU usage patterns
        cpu_spikes = [
            snapshot for snapshot in session.snapshots
            if snapshot.cpu_percent > 80
        ]
        
        # Analyze memory growth
        memory_growth = []
        if len(session.snapshots) >= 2:
            for i in range(1, len(session.snapshots)):
                growth = (session.snapshots[i].memory_usage_mb - 
                         session.snapshots[i-1].memory_usage_mb)
                if growth > 5:  # > 5MB growth
                    memory_growth.append({
                        'timestamp': session.snapshots[i].timestamp,
                        'growth_mb': growth,
                        'total_mb': session.snapshots[i].memory_usage_mb
                    })
        
        return {
            'session_id': session_id,
            'analysis_timestamp': time.time(),
            'bottlenecks': {
                'slowest_functions': [
                    {
                        'name': f.name,
                        'total_time': f.total_time,
                        'average_time': f.average_time,
                        'call_count': f.call_count
                    }
                    for f in slowest_functions
                ],
                'memory_intensive_functions': [
                    {
                        'name': f.name,
                        'memory_usage_mb': f.memory_usage,
                        'call_count': f.call_count
                    }
                    for f in memory_intensive
                ],
                'cpu_spikes': [
                    {
                        'timestamp': spike.timestamp,
                        'cpu_percent': spike.cpu_percent,
                        'memory_mb': spike.memory_usage_mb
                    }
                    for spike in cpu_spikes
                ],
                'memory_growth_events': memory_growth
            },
            'recommendations': self._generate_optimization_recommendations(session)
        }
    
    def _generate_optimization_recommendations(self, session: ProfilingSession) -> List[str]:
        """Generate optimization recommendations based on profiling data."""
        recommendations = []
        
        # Analyze function performance
        if session.function_profiles:
            slowest = max(session.function_profiles.values(), key=lambda p: p.total_time)
            if slowest.total_time > session.duration * 0.5:
                recommendations.append(
                    f"Function '{slowest.name}' consumes {slowest.total_time/session.duration*100:.1f}% "
                    f"of total execution time. Consider optimizing this function."
                )
        
        # Analyze memory usage
        peak_memory = session.peak_memory_mb
        if peak_memory > 500:  # > 500MB
            recommendations.append(
                f"Peak memory usage is {peak_memory:.1f}MB. Consider implementing "
                f"memory optimization strategies for large dataset processing."
            )
        
        # Analyze CPU usage
        avg_cpu = session.average_cpu_percent
        if avg_cpu > 80:
            recommendations.append(
                f"High CPU usage detected ({avg_cpu:.1f}% average). "
                f"Consider optimizing compute-intensive operations."
            )
        
        # Analyze I/O patterns
        if session.snapshots:
            io_heavy = any(
                snapshot.io_counters and 
                (snapshot.io_counters.get('read_bytes', 0) > 100 * 1024 * 1024 or
                 snapshot.io_counters.get('write_bytes', 0) > 100 * 1024 * 1024)
                for snapshot in session.snapshots
                if snapshot.io_counters
            )
            if io_heavy:
                recommendations.append(
                    "High I/O activity detected. Consider implementing I/O optimization "
                    "strategies such as batching, compression, or caching."
                )
        
        return recommendations


class _ProfilerContextManager:
    """Context manager for profiling code blocks."""
    
    def __init__(self, profiler: PerformanceProfiler, name: str, track_memory: bool):
        self.profiler = profiler
        self.name = name
        self.track_memory = track_memory
        self.start_time = None
        self.start_memory = None
    
    def __enter__(self):
        self.start_time = time.time()
        if self.track_memory and self.profiler.enable_memory_profiling:
            gc.collect()
            self.start_memory = psutil.Process().memory_info().rss
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        execution_time = end_time - self.start_time
        
        # Track execution time
        self.profiler.global_function_times[self.name].append(execution_time)
        
        # Calculate memory usage if requested
        memory_delta = None
        if self.track_memory and self.start_memory is not None:
            end_memory = psutil.Process().memory_info().rss
            memory_delta = (end_memory - self.start_memory) / (1024 * 1024)  # MB
        
        # Update function profiles in active sessions
        for session in self.profiler.active_sessions.values():
            if self.name in session.function_profiles:
                profile = session.function_profiles[self.name]
                new_profile = ProfiledFunction(
                    name=self.name,
                    call_count=profile.call_count + 1,
                    total_time=profile.total_time + execution_time,
                    average_time=(profile.total_time + execution_time) / (profile.call_count + 1),
                    max_time=max(profile.max_time, execution_time),
                    min_time=min(profile.min_time, execution_time),
                    memory_usage=memory_delta
                )
            else:
                new_profile = ProfiledFunction(
                    name=self.name,
                    call_count=1,
                    total_time=execution_time,
                    average_time=execution_time,
                    max_time=execution_time,
                    min_time=execution_time,
                    memory_usage=memory_delta
                )
            
            session.function_profiles[self.name] = new_profile


# Global profiler instance for easy access
profiler = PerformanceProfiler()


# Convenience functions for common profiling tasks
def profile_json_processing(func: Callable) -> Callable:
    """Decorator specifically for profiling JSON processing functions."""
    return profiler.profile_function(func, name=f"json_processing.{func.__name__}", track_memory=True)


def profile_ooxml_operations(func: Callable) -> Callable:
    """Decorator specifically for profiling OOXML operations."""
    return profiler.profile_function(func, name=f"ooxml_operations.{func.__name__}", track_memory=True)


def profile_batch_operations(func: Callable) -> Callable:
    """Decorator specifically for profiling batch operations."""
    return profiler.profile_function(func, name=f"batch_operations.{func.__name__}", track_memory=True)


@contextlib.contextmanager
def profile_section(name: str, track_memory: bool = False):
    """Context manager for profiling code sections."""
    with profiler.profile_function(name=name, track_memory=track_memory):
        yield


def start_profiling_session(session_id: str) -> str:
    """Start a new profiling session."""
    return profiler.start_session(session_id)


def end_profiling_session(session_id: str) -> ProfilingSession:
    """End a profiling session and return results."""
    return profiler.end_session(session_id)


def get_bottleneck_report(session_id: str) -> Dict[str, Any]:
    """Generate a bottleneck analysis report."""
    return profiler.generate_bottleneck_report(session_id)


if __name__ == "__main__":
    # Example usage and testing
    import doctest
    doctest.testmod()
    
    # Quick performance test
    profiler = PerformanceProfiler()
    session_id = profiler.start_session("test_session")
    
    @profiler.profile_function(track_memory=True)
    def test_function():
        import time
        time.sleep(0.1)
        return [i**2 for i in range(1000)]
    
    # Run test function multiple times
    for _ in range(5):
        test_function()
    
    # Get performance summary
    summary = profiler.get_performance_summary(session_id)
    print("Performance Summary:")
    print(json.dumps(summary, indent=2, default=str))
    
    # Generate bottleneck report
    bottlenecks = profiler.generate_bottleneck_report(session_id)
    print("\nBottleneck Analysis:")
    print(json.dumps(bottlenecks, indent=2, default=str))
    
    profiler.end_session(session_id)