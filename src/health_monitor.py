import threading
import time
import psutil
from collections import deque
from typing import Dict, List, Optional
from enum import Enum
from src.notification_service import NotificationService, Notification, NotificationType, NotificationChannel

class ComponentStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"

class SystemMetrics:
    def __init__(self):
        self.cpu_usage = 0.0
        self.memory_usage = 0.0
        self.queue_sizes = {}
        self.response_times = deque(maxlen=100)  # Keep last 100 response times
        self.error_count = 0
        self.timestamp = time.time()

class HealthMonitor:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.component_status = {}
        self.system_metrics = SystemMetrics()
        self.notification_service = NotificationService()
        self.is_running = True
        self.metrics_history = deque(maxlen=1000)  # Keep last 1000 metric snapshots
        self.alert_thresholds = {
            "cpu_usage": 90.0,  # Alert if CPU usage > 90%
            "memory_usage": 90.0,  # Alert if memory usage > 90%
            "error_rate": 0.2,  # Alert if error rate > 20%
            "response_time": 5.0  # Alert if average response time > 5 seconds
        }
        self.last_alert_time = {}  # Track last alert time for each metric
        self.alert_cooldown = 60  # Cooldown period in seconds (increased to 1 minute)

        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_system)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

        self._initialized = True

    def register_component(self, component_name: str):
        """Register a new component for health monitoring."""
        with self._lock:
            self.component_status[component_name] = ComponentStatus.HEALTHY

    def _monitor_system(self):
        """Continuously monitor system metrics and component health."""
        while self.is_running:
            try:
                with self._lock:  # Ensure thread-safe metrics updates
                    # Update system metrics with error handling
                    try:
                        # Use interval=None for immediate CPU usage reading
                        self.system_metrics.cpu_usage = psutil.cpu_percent(interval=None)
                        mem = psutil.virtual_memory()
                        self.system_metrics.memory_usage = mem.percent
                    except Exception as e:
                        self.notification_service.send_notification(
                            Notification(
                                notification_type=NotificationType.INVENTORY_ALERT,
                                message=f"Error collecting system metrics: {e}",
                                recipient_id="admin",
                                channel=NotificationChannel.SYSTEM_LOG
                            )
                        )
                        self.system_metrics.cpu_usage = 0.0
                        self.system_metrics.memory_usage = 0.0
                    
                    self.system_metrics.timestamp = time.time()

                    # Create a proper deep copy of metrics
                    metrics_snapshot = SystemMetrics()
                    metrics_snapshot.cpu_usage = float(self.system_metrics.cpu_usage)
                    metrics_snapshot.memory_usage = float(self.system_metrics.memory_usage)
                    metrics_snapshot.queue_sizes = dict(self.system_metrics.queue_sizes)
                    metrics_snapshot.response_times = deque(
                        list(self.system_metrics.response_times),
                        maxlen=100
                    )
                    metrics_snapshot.error_count = int(self.system_metrics.error_count)
                    metrics_snapshot.timestamp = float(self.system_metrics.timestamp)
                    
                    # Maintain metrics history with proper synchronization
                    self.metrics_history.append(metrics_snapshot)

                    # Check for threshold violations
                    self._check_thresholds()

                    # Reset error count for next interval
                    self.system_metrics.error_count = 0

                # Add a small sleep to prevent excessive CPU usage
                time.sleep(1)

            except Exception as e:
                self.notification_service.send_notification(
                    Notification(
                        notification_type=NotificationType.INVENTORY_ALERT,
                        message=f"Critical error in health monitoring: {e}",
                        recipient_id="admin",
                        channel=NotificationChannel.SYSTEM_LOG
                    )
                )
                time.sleep(5)  # Wait longer on error

    def _check_thresholds(self):
        """Check if any metrics exceed defined thresholds."""
        # Check CPU usage
        if self.system_metrics.cpu_usage > self.alert_thresholds["cpu_usage"]:
            self._send_metric_alert("CPU Usage", self.system_metrics.cpu_usage)

        # Check memory usage
        if self.system_metrics.memory_usage > self.alert_thresholds["memory_usage"]:
            self._send_metric_alert("Memory Usage", self.system_metrics.memory_usage)

        # Check error rate
        total_requests = len(self.system_metrics.response_times)
        if total_requests > 0:
            error_rate = self.system_metrics.error_count / total_requests
            if error_rate > self.alert_thresholds["error_rate"]:
                self._send_metric_alert("Error Rate", error_rate * 100)

        # Check response time
        if self.system_metrics.response_times:
            avg_response_time = sum(self.system_metrics.response_times) / len(self.system_metrics.response_times)
            if avg_response_time > self.alert_thresholds["response_time"]:
                self.notify_degraded_performance("High average response time detected")

    def notify_degraded_performance(self, message: str):
        """Notify about degraded system performance."""
        notification = Notification(
            notification_type=NotificationType.INVENTORY_ALERT,  # Using INVENTORY_ALERT since PERFORMANCE is not defined
            message=message,
            recipient_id="admin",
            channel=NotificationChannel.SYSTEM_LOG
        )
        self.notification_service.send_notification(notification)

    def notify_queue_overflow(self, queue_name: str):
        """Notify about queue overflow condition."""
        notification = Notification(
            notification_type=NotificationType.INVENTORY_ALERT,
            message=f"Queue overflow detected in {queue_name}",
            recipient_id="admin",
            channel=NotificationChannel.SYSTEM_LOG
        )
        self.notification_service.send_notification(notification)

    def get_current_metrics(self) -> dict:
        """Get current system metrics."""
        metrics = {
            "cpu_usage": self.system_metrics.cpu_usage,
            "memory_usage": self.system_metrics.memory_usage,
            "queue_sizes": self.system_metrics.queue_sizes.copy(),
            "error_count": self.system_metrics.error_count
        }
        if self.system_metrics.response_times:
            metrics["avg_response_time"] = sum(self.system_metrics.response_times) / len(self.system_metrics.response_times)
        return metrics

    def calculate_system_health_score(self) -> float:
        """Calculate overall system health score between 0 and 100 with weighted metrics."""
        try:
            metrics = self.get_system_metrics()
            score = 100.0
            weights = {
                "component": 0.3,  # 30% weight for component health
                "cpu": 0.2,      # 20% weight for CPU usage
                "memory": 0.2,    # 20% weight for memory usage
                "errors": 0.15,   # 15% weight for error count
                "response": 0.15  # 15% weight for response time
            }

            # Component health score (30%)
            component_scores = {
                ComponentStatus.HEALTHY: 1.0,
                ComponentStatus.DEGRADED: 0.5,
                ComponentStatus.FAILED: 0.0
            }
            if self.component_status:
                component_score = sum(component_scores[status] for status in self.component_status.values()) / len(self.component_status)
                score -= (1 - component_score) * (weights["component"] * 100)

            # CPU usage score (20%)
            if metrics["cpu_usage"] > self.alert_thresholds["cpu_usage"]:
                cpu_penalty = min((metrics["cpu_usage"] - self.alert_thresholds["cpu_usage"]) / 10, 1.0)
                score -= cpu_penalty * (weights["cpu"] * 100)

            # Memory usage score (20%)
            if metrics["memory_usage"] > self.alert_thresholds["memory_usage"]:
                memory_penalty = min((metrics["memory_usage"] - self.alert_thresholds["memory_usage"]) / 10, 1.0)
                score -= memory_penalty * (weights["memory"] * 100)

            # Error count score (15%)
            if metrics["error_count"] > 0:
                error_penalty = min(metrics["error_count"] / 10, 1.0)
                score -= error_penalty * (weights["errors"] * 100)

            # Response time score (15%)
            if metrics.get("avg_response_time", 0) > self.alert_thresholds["response_time"]:
                response_penalty = min((metrics["avg_response_time"] - self.alert_thresholds["response_time"]) / 5, 1.0)
                score -= response_penalty * (weights["response"] * 100)

            return max(0.0, min(100.0, score))
        except Exception as e:
            print(f"Error calculating health score: {e}")
            return 0.0  # Return minimum score on error

    def update_component_status(self, component_name: str, status: ComponentStatus):
        """Update the status of a component and trigger notifications if needed."""
        if not isinstance(component_name, str) or not component_name.strip():
            raise ValueError("Component name must be a non-empty string")
        if not isinstance(status, ComponentStatus):
            raise ValueError("Status must be a valid ComponentStatus enum value")

        with self._lock:
            if component_name not in self.component_status:
                raise KeyError(f"Component {component_name} is not registered for monitoring")

            old_status = self.component_status[component_name]
            self.component_status[component_name] = status

            if status != old_status and status != ComponentStatus.HEALTHY:
                self._send_alert(component_name, status)

    def record_response_time(self, response_time: float):
        """Record response time for performance monitoring."""
        self.system_metrics.response_times.append(response_time)

    def record_error(self):
        """Record an error occurrence."""
        self.system_metrics.error_count += 1

    def update_queue_size(self, queue_name: str, size: int):
        """Update the size of a monitored queue."""
        self.system_metrics.queue_sizes[queue_name] = size

    def _send_alert(self, component_name: str, status: ComponentStatus):
        """Send alert notification for component status changes."""
        notification = Notification(
            notification_type=NotificationType.INVENTORY_ALERT,  # Using INVENTORY_ALERT for system alerts
            message=f"Component {component_name} status changed to {status.value}",
            recipient_id="admin",
            channel=NotificationChannel.SYSTEM_LOG
        )
        self.notification_service.send_notification(notification)

    def _send_metric_alert(self, metric_name: str, value: float):
        """Send alert notification for metric threshold violations with cooldown period."""
        current_time = time.time()
        if metric_name not in self.last_alert_time or \
           (current_time - self.last_alert_time.get(metric_name, 0)) >= self.alert_cooldown:
            notification = Notification(
                notification_type=NotificationType.INVENTORY_ALERT,
                message=f"System metric alert: {metric_name} is at {value:.2f}",
                recipient_id="admin",
                channel=NotificationChannel.SYSTEM_LOG
            )
            self.notification_service.send_notification(notification)
            self.last_alert_time[metric_name] = current_time

    def get_system_metrics(self):
        """Get current system metrics."""
        metrics = {
            "cpu_usage": self.system_metrics.cpu_usage,
            "memory_usage": self.system_metrics.memory_usage,
            "queue_sizes": self.system_metrics.queue_sizes,
            "avg_response_time": sum(self.system_metrics.response_times) / len(self.system_metrics.response_times) if self.system_metrics.response_times else 0.0,
            "error_count": self.system_metrics.error_count
        }
        return metrics

    def get_system_health_report(self):
        """Get a comprehensive system health report."""
        return {
            "component_status": self.component_status,
            "system_metrics": self.get_system_metrics(),
            "health_score": self.calculate_system_health_score()
        }

    def stop(self):
        """Stop the health monitoring service."""
        self.is_running = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join()