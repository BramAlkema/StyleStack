#!/usr/bin/env python3
"""
StyleStack Production Performance Monitoring and Alerting System

Production-ready monitoring system for StyleStack JSON-to-OOXML processing pipeline.
Provides real-time metrics, alerting, health checks, and comprehensive observability
for production deployments.
"""

import time
import threading
import logging
import json
import smtplib
import sqlite3
from typing import Dict, List, Any, Optional, Callable, NamedTuple, Union
from dataclasses import dataclass, field
from collections import deque, defaultdict
from pathlib import Path
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import psutil
import socket
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

# Import StyleStack components for monitoring
try:
    from .performance_profiler import PerformanceProfiler
    from .advanced_cache_system import CacheManager
    from .memory_optimizer import MemoryManager
    from .json_ooxml_processor import JSONPatchProcessor
except ImportError:
    from performance_profiler import PerformanceProfiler
    from advanced_cache_system import CacheManager
    from memory_optimizer import MemoryManager
    from json_ooxml_processor import JSONPatchProcessor

logger = logging.getLogger(__name__)


class AlertLevel:
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricThreshold:
    """Threshold configuration for a metric."""
    warning_threshold: float
    critical_threshold: float
    comparison: str = ">"  # ">", "<", "==", "!="
    duration_seconds: float = 60.0  # How long threshold must be breached
    
    def is_breached(self, value: float) -> Optional[str]:
        """Check if threshold is breached and return alert level."""
        if self.comparison == ">":
            if value > self.critical_threshold:
                return AlertLevel.CRITICAL
            elif value > self.warning_threshold:
                return AlertLevel.WARNING
        elif self.comparison == "<":
            if value < self.critical_threshold:
                return AlertLevel.CRITICAL
            elif value < self.warning_threshold:
                return AlertLevel.WARNING
        
        return None


@dataclass
class Alert:
    """Alert message container."""
    timestamp: float
    level: str
    metric_name: str
    current_value: float
    threshold_value: float
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            'timestamp': self.timestamp,
            'datetime': datetime.fromtimestamp(self.timestamp).isoformat(),
            'level': self.level,
            'metric_name': self.metric_name,
            'current_value': self.current_value,
            'threshold_value': self.threshold_value,
            'message': self.message,
            'metadata': self.metadata
        }


@dataclass
class HealthCheck:
    """Health check configuration."""
    name: str
    check_function: Callable[[], bool]
    interval_seconds: float = 60.0
    timeout_seconds: float = 10.0
    failure_threshold: int = 3  # Consecutive failures before alert
    
    def __post_init__(self):
        """Post-initialization setup."""
        self.last_check_time = 0.0
        self.last_success = True
        self.consecutive_failures = 0


class MetricsCollector:
    """
    Comprehensive metrics collector for StyleStack performance monitoring.
    
    Collects system metrics, application metrics, and custom business metrics.
    """
    
    def __init__(self, collection_interval: float = 10.0):
        """Initialize the metrics collector."""
        self.collection_interval = collection_interval
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.current_metrics: Dict[str, Any] = {}
        
        # Threading
        self._collecting = False
        self._collection_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Component references for monitoring
        self.monitored_components: Dict[str, Any] = {}
        
        logger.info(f"Metrics collector initialized with {collection_interval}s interval")
    
    def register_component(self, name: str, component: Any) -> None:
        """Register a component for monitoring."""
        self.monitored_components[name] = component
        logger.debug(f"Registered component for monitoring: {name}")
    
    def start_collection(self) -> None:
        """Start metrics collection."""
        if self._collecting:
            return
        
        self._collecting = True
        self._stop_event.clear()
        
        def collection_loop():
            while not self._stop_event.wait(self.collection_interval):
                try:
                    self._collect_all_metrics()
                except Exception as e:
                    logger.error(f"Metrics collection error: {e}")
        
        self._collection_thread = threading.Thread(target=collection_loop, daemon=True)
        self._collection_thread.start()
        
        logger.info("Started metrics collection")
    
    def stop_collection(self) -> None:
        """Stop metrics collection."""
        if not self._collecting:
            return
        
        self._stop_event.set()
        if self._collection_thread:
            self._collection_thread.join(timeout=5.0)
        
        self._collecting = False
        logger.info("Stopped metrics collection")
    
    def _collect_all_metrics(self) -> None:
        """Collect all available metrics."""
        timestamp = time.time()
        
        # System metrics
        system_metrics = self._collect_system_metrics()
        
        # Application metrics
        app_metrics = self._collect_application_metrics()
        
        # Custom business metrics
        business_metrics = self._collect_business_metrics()
        
        # Combine all metrics
        all_metrics = {
            **system_metrics,
            **app_metrics,
            **business_metrics,
            'collection_timestamp': timestamp
        }
        
        # Update current metrics and history
        self.current_metrics = all_metrics
        
        for metric_name, value in all_metrics.items():
            if isinstance(value, (int, float)):
                self.metrics_history[metric_name].append((timestamp, value))
    
    def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect system-level metrics."""
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Process-specific metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            
            # Network I/O if available
            network_io = {}
            try:
                net_io = psutil.net_io_counters()
                network_io = {
                    'network_bytes_sent': net_io.bytes_sent,
                    'network_bytes_recv': net_io.bytes_recv,
                    'network_packets_sent': net_io.packets_sent,
                    'network_packets_recv': net_io.packets_recv
                }
            except (AttributeError, OSError):
                pass
            
            return {
                'cpu_percent': cpu_percent,
                'memory_total_mb': memory.total / (1024 * 1024),
                'memory_available_mb': memory.available / (1024 * 1024),
                'memory_used_mb': memory.used / (1024 * 1024),
                'memory_percent': memory.percent,
                'disk_total_gb': disk.total / (1024 * 1024 * 1024),
                'disk_free_gb': disk.free / (1024 * 1024 * 1024),
                'disk_used_percent': (disk.used / disk.total) * 100,
                'process_memory_rss_mb': process_memory.rss / (1024 * 1024),
                'process_memory_vms_mb': process_memory.vms / (1024 * 1024),
                'process_threads': process.num_threads(),
                **network_io
            }
        
        except Exception as e:
            logger.error(f"System metrics collection failed: {e}")
            return {}
    
    def _collect_application_metrics(self) -> Dict[str, float]:
        """Collect StyleStack application metrics."""
        app_metrics = {}
        
        try:
            # Cache manager metrics
            if 'cache_manager' in self.monitored_components:
                cache_stats = self.monitored_components['cache_manager'].get_comprehensive_stats()
                
                # Extract key cache metrics
                for cache_type, stats in cache_stats.items():
                    if isinstance(stats, dict):
                        if 'hit_rate' in stats:
                            app_metrics[f'{cache_type}_hit_rate'] = stats['hit_rate']
                        if 'entry_count' in stats:
                            app_metrics[f'{cache_type}_entries'] = stats['entry_count']
                        if 'size_mb' in stats:
                            app_metrics[f'{cache_type}_size_mb'] = stats['size_mb']
            
            # Memory manager metrics
            if 'memory_manager' in self.monitored_components:
                memory_stats = self.monitored_components['memory_manager'].get_memory_stats()
                
                if 'current' in memory_stats:
                    app_metrics['app_memory_rss_mb'] = memory_stats['current']['rss_mb']
                    app_metrics['app_memory_percent'] = memory_stats['current']['percent']
                
                if 'peak_mb' in memory_stats:
                    app_metrics['app_memory_peak_mb'] = memory_stats['peak_mb']
            
            # Performance profiler metrics
            if 'profiler' in self.monitored_components:
                profiler_stats = self.monitored_components['profiler'].get_performance_summary()
                
                if 'global_function_stats' in profiler_stats:
                    # Extract aggregated performance metrics
                    total_calls = sum(
                        stats.get('call_count', 0)
                        for stats in profiler_stats['global_function_stats'].values()
                    )
                    app_metrics['total_function_calls'] = total_calls
                    
                    avg_execution_time = sum(
                        stats.get('average_time', 0)
                        for stats in profiler_stats['global_function_stats'].values()
                    ) / len(profiler_stats['global_function_stats']) if profiler_stats['global_function_stats'] else 0
                    
                    app_metrics['average_function_execution_time'] = avg_execution_time
        
        except Exception as e:
            logger.error(f"Application metrics collection failed: {e}")
        
        return app_metrics
    
    def _collect_business_metrics(self) -> Dict[str, float]:
        """Collect business-specific metrics."""
        # This would be customized based on specific business requirements
        # For now, we'll collect some general processing metrics
        
        business_metrics = {}
        
        try:
            # Template processing rate (if available)
            # This would typically be tracked by the main application
            
            # Patch operation success rate
            # This would come from the JSON processor
            
            # Average processing time per template
            # This would be tracked by batch processors
            
            # Queue lengths and processing backlogs
            # This would come from batch processing queues
            
            pass  # Placeholder for actual business metric collection
        
        except Exception as e:
            logger.error(f"Business metrics collection failed: {e}")
        
        return business_metrics
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metric values."""
        return self.current_metrics.copy()
    
    def get_metric_history(self, metric_name: str, duration_minutes: int = 60) -> List[Tuple[float, float]]:
        """Get metric history for specified duration."""
        if metric_name not in self.metrics_history:
            return []
        
        cutoff_time = time.time() - (duration_minutes * 60)
        history = self.metrics_history[metric_name]
        
        return [(timestamp, value) for timestamp, value in history if timestamp > cutoff_time]
    
    def calculate_metric_statistics(self, metric_name: str, duration_minutes: int = 60) -> Dict[str, float]:
        """Calculate statistics for a metric over specified duration."""
        history = self.get_metric_history(metric_name, duration_minutes)
        
        if not history:
            return {}
        
        values = [value for _, value in history]
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': sum(values) / len(values),
            'current': values[-1] if values else 0
        }


class AlertManager:
    """
    Alert management system with multiple notification channels.
    
    Handles alert generation, deduplication, escalation, and delivery.
    """
    
    def __init__(self, 
                 alert_history_size: int = 10000,
                 deduplication_window_minutes: int = 5):
        """Initialize the alert manager."""
        self.alert_history_size = alert_history_size
        self.deduplication_window_seconds = deduplication_window_minutes * 60
        
        # Alert storage
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=alert_history_size)
        self.suppressed_alerts: Set[str] = set()
        
        # Threshold configurations
        self.metric_thresholds: Dict[str, MetricThreshold] = {}
        
        # Notification handlers
        self.notification_handlers: List[Callable[[Alert], None]] = []
        
        # Threading for alert processing
        self.alert_queue = deque()
        self.alert_lock = threading.RLock()
        
        self._setup_default_thresholds()
        
        logger.info("Alert manager initialized")
    
    def _setup_default_thresholds(self) -> None:
        """Setup default alert thresholds."""
        self.metric_thresholds.update({
            'cpu_percent': MetricThreshold(80.0, 95.0, ">", 120.0),
            'memory_percent': MetricThreshold(85.0, 95.0, ">", 300.0),
            'disk_used_percent': MetricThreshold(85.0, 95.0, ">", 600.0),
            'process_memory_rss_mb': MetricThreshold(1000.0, 2000.0, ">", 180.0),
            'cache_hit_rate': MetricThreshold(0.8, 0.6, "<", 300.0),
            'average_function_execution_time': MetricThreshold(1.0, 5.0, ">", 180.0)
        })
    
    def add_threshold(self, metric_name: str, threshold: MetricThreshold) -> None:
        """Add or update a metric threshold."""
        self.metric_thresholds[metric_name] = threshold
        logger.debug(f"Added threshold for {metric_name}: {threshold}")
    
    def add_notification_handler(self, handler: Callable[[Alert], None]) -> None:
        """Add a notification handler."""
        self.notification_handlers.append(handler)
        logger.debug("Added notification handler")
    
    def check_metrics(self, metrics: Dict[str, Any]) -> List[Alert]:
        """Check metrics against thresholds and generate alerts."""
        new_alerts = []
        current_time = time.time()
        
        for metric_name, threshold in self.metric_thresholds.items():
            if metric_name in metrics:
                value = metrics[metric_name]
                
                if isinstance(value, (int, float)):
                    alert_level = threshold.is_breached(value)
                    
                    if alert_level:
                        alert = Alert(
                            timestamp=current_time,
                            level=alert_level,
                            metric_name=metric_name,
                            current_value=value,
                            threshold_value=threshold.critical_threshold if alert_level == AlertLevel.CRITICAL else threshold.warning_threshold,
                            message=f"{metric_name} is {value} (threshold: {threshold.warning_threshold}/{threshold.critical_threshold})",
                            metadata={'threshold_config': threshold}
                        )
                        
                        # Check for deduplication
                        if not self._is_duplicate_alert(alert):
                            new_alerts.append(alert)
                            self._process_alert(alert)
        
        return new_alerts
    
    def _is_duplicate_alert(self, alert: Alert) -> bool:
        """Check if alert is a duplicate within deduplication window."""
        alert_key = f"{alert.metric_name}_{alert.level}"
        
        if alert_key in self.active_alerts:
            existing_alert = self.active_alerts[alert_key]
            
            # Check if within deduplication window
            if alert.timestamp - existing_alert.timestamp < self.deduplication_window_seconds:
                return True
        
        return False
    
    def _process_alert(self, alert: Alert) -> None:
        """Process a new alert."""
        alert_key = f"{alert.metric_name}_{alert.level}"
        
        with self.alert_lock:
            # Store in active alerts
            self.active_alerts[alert_key] = alert
            
            # Add to history
            self.alert_history.append(alert)
            
            # Send notifications
            for handler in self.notification_handlers:
                try:
                    handler(alert)
                except Exception as e:
                    logger.error(f"Notification handler failed: {e}")
        
        logger.warning(f"ALERT [{alert.level.upper()}]: {alert.message}")
    
    def resolve_alert(self, metric_name: str, level: str) -> bool:
        """Resolve an active alert."""
        alert_key = f"{metric_name}_{level}"
        
        with self.alert_lock:
            if alert_key in self.active_alerts:
                resolved_alert = self.active_alerts.pop(alert_key)
                logger.info(f"Resolved alert: {resolved_alert.message}")
                return True
        
        return False
    
    def get_active_alerts(self) -> List[Alert]:
        """Get list of active alerts."""
        with self.alert_lock:
            return list(self.active_alerts.values())
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history for specified hours."""
        cutoff_time = time.time() - (hours * 3600)
        
        with self.alert_lock:
            return [alert for alert in self.alert_history if alert.timestamp > cutoff_time]


class HealthCheckManager:
    """
    Health check management system.
    
    Manages and executes health checks for various system components.
    """
    
    def __init__(self):
        """Initialize the health check manager."""
        self.health_checks: Dict[str, HealthCheck] = {}
        self.health_status: Dict[str, bool] = {}
        self.health_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Threading
        self._checking = False
        self._check_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        self._setup_default_health_checks()
        
        logger.info("Health check manager initialized")
    
    def _setup_default_health_checks(self) -> None:
        """Setup default health checks."""
        # System health checks
        self.add_health_check(
            "disk_space",
            lambda: psutil.disk_usage('/').free > (1024 * 1024 * 1024),  # > 1GB free
            interval_seconds=300.0  # Check every 5 minutes
        )
        
        self.add_health_check(
            "memory_available",
            lambda: psutil.virtual_memory().percent < 95.0,  # < 95% memory usage
            interval_seconds=60.0
        )
    
    def add_health_check(self, name: str, check_function: Callable[[], bool], 
                        interval_seconds: float = 60.0, timeout_seconds: float = 10.0) -> None:
        """Add a health check."""
        health_check = HealthCheck(
            name=name,
            check_function=check_function,
            interval_seconds=interval_seconds,
            timeout_seconds=timeout_seconds
        )
        
        self.health_checks[name] = health_check
        self.health_status[name] = True  # Assume healthy initially
        
        logger.debug(f"Added health check: {name}")
    
    def start_monitoring(self) -> None:
        """Start health check monitoring."""
        if self._checking:
            return
        
        self._checking = True
        self._stop_event.clear()
        
        def monitoring_loop():
            while not self._stop_event.wait(10.0):  # Check every 10 seconds
                current_time = time.time()
                
                for name, health_check in self.health_checks.items():
                    # Check if it's time to run this health check
                    if current_time - health_check.last_check_time >= health_check.interval_seconds:
                        self._execute_health_check(name, health_check)
        
        self._check_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self._check_thread.start()
        
        logger.info("Started health check monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop health check monitoring."""
        if not self._checking:
            return
        
        self._stop_event.set()
        if self._check_thread:
            self._check_thread.join(timeout=5.0)
        
        self._checking = False
        logger.info("Stopped health check monitoring")
    
    def _execute_health_check(self, name: str, health_check: HealthCheck) -> None:
        """Execute a single health check."""
        health_check.last_check_time = time.time()
        
        try:
            # Execute check with timeout (simplified - would need proper timeout implementation)
            result = health_check.check_function()
            
            if result:
                health_check.last_success = True
                health_check.consecutive_failures = 0
                self.health_status[name] = True
            else:
                health_check.last_success = False
                health_check.consecutive_failures += 1
                
                # Update status if failure threshold exceeded
                if health_check.consecutive_failures >= health_check.failure_threshold:
                    self.health_status[name] = False
                    logger.error(f"Health check failed: {name} (consecutive failures: {health_check.consecutive_failures})")
            
            # Record in history
            self.health_history[name].append((health_check.last_check_time, result))
        
        except Exception as e:
            logger.error(f"Health check execution failed for {name}: {e}")
            health_check.last_success = False
            health_check.consecutive_failures += 1
            self.health_status[name] = False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        return {
            'overall_healthy': all(self.health_status.values()),
            'checks': {
                name: {
                    'healthy': status,
                    'consecutive_failures': self.health_checks[name].consecutive_failures,
                    'last_check_time': self.health_checks[name].last_check_time
                }
                for name, status in self.health_status.items()
            }
        }


class ProductionMonitor:
    """
    Main production monitoring system.
    
    Coordinates metrics collection, alerting, health checks, and provides
    comprehensive observability for StyleStack production deployments.
    """
    
    def __init__(self,
                 metrics_interval: float = 10.0,
                 enable_alerts: bool = True,
                 enable_health_checks: bool = True,
                 data_retention_hours: int = 168):  # 1 week
        """Initialize the production monitor."""
        self.metrics_interval = metrics_interval
        self.enable_alerts = enable_alerts
        self.enable_health_checks = enable_health_checks
        self.data_retention_hours = data_retention_hours
        
        # Initialize components
        self.metrics_collector = MetricsCollector(metrics_interval)
        self.alert_manager = AlertManager() if enable_alerts else None
        self.health_check_manager = HealthCheckManager() if enable_health_checks else None
        
        # Monitoring state
        self.monitoring_active = False
        self.start_time = time.time()
        
        # Database for persistence
        self.db_path: Optional[Path] = None
        
        logger.info("Production monitor initialized")
    
    def register_component(self, name: str, component: Any) -> None:
        """Register a component for monitoring."""
        self.metrics_collector.register_component(name, component)
        
        # Add component-specific health checks
        if hasattr(component, 'health_check'):
            if self.health_check_manager:
                self.health_check_manager.add_health_check(
                    f"{name}_health",
                    component.health_check
                )
    
    def setup_database(self, db_path: Path) -> None:
        """Setup database for metric persistence."""
        self.db_path = db_path
        
        # Create database schema
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    timestamp REAL,
                    metric_name TEXT,
                    value REAL,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON metrics(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metric_name ON metrics(metric_name)
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    timestamp REAL,
                    level TEXT,
                    metric_name TEXT,
                    current_value REAL,
                    message TEXT,
                    metadata TEXT
                )
            """)
        
        logger.info(f"Database setup complete: {db_path}")
    
    def add_email_alerts(self, smtp_server: str, smtp_port: int,
                        sender_email: str, sender_password: str,
                        recipient_emails: List[str]) -> None:
        """Add email notification for alerts."""
        if not self.alert_manager:
            return
        
        def send_email_alert(alert: Alert):
            try:
                msg = MimeMultipart()
                msg['From'] = sender_email
                msg['To'] = ', '.join(recipient_emails)
                msg['Subject'] = f"StyleStack Alert [{alert.level.upper()}]: {alert.metric_name}"
                
                body = f"""
                Alert Details:
                - Metric: {alert.metric_name}
                - Level: {alert.level.upper()}
                - Current Value: {alert.current_value}
                - Threshold: {alert.threshold_value}
                - Time: {datetime.fromtimestamp(alert.timestamp).isoformat()}
                - Message: {alert.message}
                
                Metadata: {json.dumps(alert.metadata, indent=2)}
                """
                
                msg.attach(MimeText(body, 'plain'))
                
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(sender_email, sender_password)
                text = msg.as_string()
                server.sendmail(sender_email, recipient_emails, text)
                server.quit()
                
            except Exception as e:
                logger.error(f"Failed to send email alert: {e}")
        
        self.alert_manager.add_notification_handler(send_email_alert)
        logger.info("Email alerts configured")
    
    def add_webhook_alerts(self, webhook_url: str, timeout: int = 10) -> None:
        """Add webhook notification for alerts."""
        if not self.alert_manager:
            return
        
        def send_webhook_alert(alert: Alert):
            try:
                payload = json.dumps(alert.to_dict()).encode('utf-8')
                
                req = urllib.request.Request(
                    webhook_url,
                    data=payload,
                    headers={'Content-Type': 'application/json'}
                )
                
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    if response.status != 200:
                        logger.warning(f"Webhook returned status {response.status}")
                
            except Exception as e:
                logger.error(f"Failed to send webhook alert: {e}")
        
        self.alert_manager.add_notification_handler(send_webhook_alert)
        logger.info(f"Webhook alerts configured: {webhook_url}")
    
    def start_monitoring(self) -> None:
        """Start all monitoring services."""
        if self.monitoring_active:
            return
        
        logger.info("Starting production monitoring...")
        
        # Start metrics collection
        self.metrics_collector.start_collection()
        
        # Start health checks
        if self.health_check_manager:
            self.health_check_manager.start_monitoring()
        
        # Start alert checking
        if self.alert_manager:
            self._start_alert_checking()
        
        self.monitoring_active = True
        
        logger.info("Production monitoring started successfully")
    
    def stop_monitoring(self) -> None:
        """Stop all monitoring services."""
        if not self.monitoring_active:
            return
        
        logger.info("Stopping production monitoring...")
        
        # Stop metrics collection
        self.metrics_collector.stop_collection()
        
        # Stop health checks
        if self.health_check_manager:
            self.health_check_manager.stop_monitoring()
        
        # Stop alert checking
        self._stop_alert_checking()
        
        self.monitoring_active = False
        
        logger.info("Production monitoring stopped")
    
    def _start_alert_checking(self) -> None:
        """Start alert checking loop."""
        if not self.alert_manager:
            return
        
        def alert_checking_loop():
            while self.monitoring_active:
                try:
                    current_metrics = self.metrics_collector.get_current_metrics()
                    if current_metrics:
                        alerts = self.alert_manager.check_metrics(current_metrics)
                        
                        # Store alerts in database if configured
                        if self.db_path and alerts:
                            self._store_alerts(alerts)
                
                except Exception as e:
                    logger.error(f"Alert checking failed: {e}")
                
                time.sleep(30.0)  # Check every 30 seconds
        
        self._alert_thread = threading.Thread(target=alert_checking_loop, daemon=True)
        self._alert_thread.start()
    
    def _stop_alert_checking(self) -> None:
        """Stop alert checking."""
        # Alert thread will stop when monitoring_active becomes False
        pass
    
    def _store_alerts(self, alerts: List[Alert]) -> None:
        """Store alerts in database."""
        if not self.db_path:
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                for alert in alerts:
                    conn.execute("""
                        INSERT INTO alerts 
                        (timestamp, level, metric_name, current_value, message, metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        alert.timestamp,
                        alert.level,
                        alert.metric_name,
                        alert.current_value,
                        alert.message,
                        json.dumps(alert.metadata)
                    ))
        
        except Exception as e:
            logger.error(f"Failed to store alerts: {e}")
    
    def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data."""
        current_metrics = self.metrics_collector.get_current_metrics()
        
        dashboard = {
            'timestamp': time.time(),
            'monitoring_uptime_seconds': time.time() - self.start_time,
            'monitoring_active': self.monitoring_active,
            'current_metrics': current_metrics,
            'metric_statistics': {},
            'active_alerts': [],
            'health_status': {},
            'system_overview': {
                'cpu_percent': current_metrics.get('cpu_percent', 0),
                'memory_percent': current_metrics.get('memory_percent', 0),
                'disk_used_percent': current_metrics.get('disk_used_percent', 0),
                'process_memory_mb': current_metrics.get('process_memory_rss_mb', 0)
            }
        }
        
        # Add metric statistics
        key_metrics = ['cpu_percent', 'memory_percent', 'process_memory_rss_mb']
        for metric in key_metrics:
            dashboard['metric_statistics'][metric] = self.metrics_collector.calculate_metric_statistics(metric)
        
        # Add active alerts
        if self.alert_manager:
            dashboard['active_alerts'] = [alert.to_dict() for alert in self.alert_manager.get_active_alerts()]
        
        # Add health status
        if self.health_check_manager:
            dashboard['health_status'] = self.health_check_manager.get_health_status()
        
        return dashboard
    
    def export_monitoring_report(self, output_path: Path, hours: int = 24) -> None:
        """Export comprehensive monitoring report."""
        dashboard_data = self.get_monitoring_dashboard()
        
        # Add historical data
        report = dashboard_data.copy()
        
        # Add alert history
        if self.alert_manager:
            alert_history = self.alert_manager.get_alert_history(hours)
            report['alert_history'] = [alert.to_dict() for alert in alert_history]
        
        # Add metric trends
        key_metrics = ['cpu_percent', 'memory_percent', 'process_memory_rss_mb']
        report['metric_trends'] = {}
        
        for metric in key_metrics:
            history = self.metrics_collector.get_metric_history(metric, hours * 60)
            report['metric_trends'][metric] = [
                {'timestamp': ts, 'value': val} for ts, val in history
            ]
        
        # Save report
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Monitoring report exported to: {output_path}")
    
    def __enter__(self):
        """Context manager entry."""
        self.start_monitoring()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_monitoring()


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Create production monitor
    monitor = ProductionMonitor(
        metrics_interval=5.0,
        enable_alerts=True,
        enable_health_checks=True
    )
    
    # Setup database for testing
    db_path = Path("monitoring_test.db")
    monitor.setup_database(db_path)
    
    # Register some test components
    cache_manager = CacheManager()
    memory_manager = MemoryManager()
    
    monitor.register_component("cache_manager", cache_manager)
    monitor.register_component("memory_manager", memory_manager)
    
    # Test monitoring for a short period
    with monitor:
        print("Monitoring started...")
        time.sleep(30)  # Monitor for 30 seconds
        
        # Get dashboard data
        dashboard = monitor.get_monitoring_dashboard()
        print("\nMonitoring Dashboard:")
        print(json.dumps(dashboard, indent=2, default=str))
        
        # Export report
        report_path = Path("monitoring_report.json")
        monitor.export_monitoring_report(report_path)
        print(f"\nReport exported to: {report_path}")
    
    print("Monitoring test completed.")