import unittest
from unittest.mock import patch, Mock
from src.health_monitor import HealthMonitor, ComponentStatus, SystemMetrics

class TestHealthMonitor(unittest.TestCase):
    def setUp(self):
        self.health_monitor = HealthMonitor()
        self.test_components = ["order_processor", "route_optimizer", "inventory_manager"]
        for component in self.test_components:
            self.health_monitor.register_component(component)

    def tearDown(self):
        # Clean up resources and stop monitoring thread
        self.health_monitor.is_running = False
        if hasattr(self.health_monitor, 'monitor_thread'):
            self.health_monitor.monitor_thread.join(timeout=1)

    def test_register_component(self):
        # Test registering new component
        new_component = "notification_service"
        self.health_monitor.register_component(new_component)
        self.assertIn(new_component, self.health_monitor.component_status)
        self.assertEqual(self.health_monitor.component_status[new_component], ComponentStatus.HEALTHY)

        # Test registering duplicate component
        initial_count = len(self.health_monitor.component_status)
        self.health_monitor.register_component(new_component)
        self.assertEqual(len(self.health_monitor.component_status), initial_count)

    def test_update_component_status(self):
        # Test updating status of existing component
        component = "order_processor"
        self.health_monitor.update_component_status(component, ComponentStatus.HEALTHY)
        self.assertEqual(self.health_monitor.component_status[component], ComponentStatus.HEALTHY)

        # Test status transition sequence
        self.health_monitor.update_component_status(component, ComponentStatus.DEGRADED)
        self.assertEqual(self.health_monitor.component_status[component], ComponentStatus.DEGRADED)
        self.health_monitor.update_component_status(component, ComponentStatus.FAILED)
        self.assertEqual(self.health_monitor.component_status[component], ComponentStatus.FAILED)
        self.health_monitor.update_component_status(component, ComponentStatus.HEALTHY)
        self.assertEqual(self.health_monitor.component_status[component], ComponentStatus.HEALTHY)

        # Test updating non-existent component
        with self.assertRaises(KeyError):
            self.health_monitor.update_component_status("non_existent", ComponentStatus.HEALTHY)

    def test_record_response_time(self):
        # Test recording multiple response times
        test_times = [0.5, 1.0, 1.5]
        for time in test_times:
            self.health_monitor.record_response_time(time)

        metrics = self.health_monitor.get_current_metrics()  # Changed to get_current_metrics()
        self.assertIn("avg_response_time", metrics)
        self.assertEqual(metrics["avg_response_time"], sum(test_times) / len(test_times))

        # Test response time threshold
        with patch('src.health_monitor.HealthMonitor.notify_degraded_performance') as mock_notify:
            for _ in range(5):
                self.health_monitor.record_response_time(2.0)
            mock_notify.assert_called_with("High average response time detected")

    def test_update_queue_size(self):
        # Test updating multiple queue sizes
        test_queues = {
            "order_queue": 5,
            "processing_queue": 3,
            "delivery_queue": 7
        }
        for queue_name, size in test_queues.items():
            self.health_monitor.update_queue_size(queue_name, size)

        metrics = self.health_monitor.get_system_metrics()
        for queue_name, size in test_queues.items():
            self.assertEqual(metrics["queue_sizes"][queue_name], size)

        # Test queue size threshold alerts
        with patch('src.health_monitor.HealthMonitor.notify_queue_overflow') as mock_notify:
            self.health_monitor.update_queue_size("order_queue", 100)
            mock_notify.assert_called_with("order_queue")

    def test_system_metrics_monitoring(self):
        # Test CPU and memory monitoring with different thresholds
        test_cases = [
            (75.0, 70.0, False),  # Below threshold
            (85.0, 90.0, True),   # Memory above threshold
            (90.0, 75.0, True),   # CPU above threshold
            (95.0, 95.0, True)    # Both above threshold
        ]
        
        for cpu_value, mem_value, should_alert in test_cases:
            with patch('psutil.cpu_percent', return_value=cpu_value), \
                 patch('psutil.virtual_memory') as mock_memory, \
                 patch('src.health_monitor.HealthMonitor._send_metric_alert') as mock_alert:
                
                mock_memory.return_value.percent = mem_value
                self.health_monitor._monitor_system()
                
                if should_alert:
                    if cpu_value > self.health_monitor.alert_thresholds["cpu_usage"]:
                        mock_alert.assert_any_call("CPU Usage", cpu_value)
                    if mem_value > self.health_monitor.alert_thresholds["memory_usage"]:
                        mock_alert.assert_any_call("Memory Usage", mem_value)
                else:
                    mock_alert.assert_not_called()

    def test_metrics_history(self):
        # Test metrics history recording
        test_metrics = SystemMetrics()
        test_metrics.cpu_usage = 50.0
        test_metrics.memory_usage = 60.0
        test_metrics.queue_sizes = {"test_queue": 5}
        
        self.health_monitor.metrics_history.append(test_metrics)
        latest_metrics = self.health_monitor.metrics_history[-1]
        
        self.assertEqual(latest_metrics.cpu_usage, 50.0)
        self.assertEqual(latest_metrics.memory_usage, 60.0)
        self.assertEqual(latest_metrics.queue_sizes["test_queue"], 5)

    def test_get_system_health_report(self):
        # Setup complex test scenario
        component_statuses = {
            "order_processor": ComponentStatus.HEALTHY,
            "route_optimizer": ComponentStatus.DEGRADED,
            "inventory_manager": ComponentStatus.FAILED
        }
        for component, status in component_statuses.items():
            self.health_monitor.update_component_status(component, status)

        self.health_monitor.record_response_time(0.3)
        self.health_monitor.update_queue_size("order_queue", 3)
        self.health_monitor.update_queue_size("processing_queue", 5)

        # Get and verify health report
        report = self.health_monitor.get_system_health_report()

        # Verify component statuses
        self.assertIn("component_status", report)
        for component, status in component_statuses.items():
            self.assertEqual(report["component_status"][component], status)

        # Verify system metrics
        self.assertIn("system_metrics", report)
        self.assertIn("queue_sizes", report["system_metrics"])
        self.assertEqual(report["system_metrics"]["queue_sizes"]["order_queue"], 3)
        self.assertEqual(report["system_metrics"]["queue_sizes"]["processing_queue"], 5)
        self.assertIn("avg_response_time", report["system_metrics"])

    def test_system_health_score(self):
        # Test health score calculation
        self.health_monitor.update_component_status("order_processor", ComponentStatus.HEALTHY)
        self.health_monitor.update_component_status("route_optimizer", ComponentStatus.DEGRADED)
        self.health_monitor.update_component_status("inventory_manager", ComponentStatus.FAILED)

        health_score = self.health_monitor.calculate_system_health_score()
        self.assertIsInstance(health_score, float)
        self.assertGreaterEqual(health_score, 0.0)
        self.assertLessEqual(health_score, 1.0)

    def test_error_handling(self):
        # Test error handling in monitoring thread
        self.health_monitor.is_running = False  # Stop the monitoring thread
        if hasattr(self.health_monitor, 'monitor_thread'):
            self.health_monitor.monitor_thread.join(timeout=1)

        with patch('psutil.cpu_percent', side_effect=Exception("Test error")), \
             patch('builtins.print') as mock_print:
            self.health_monitor._monitor_system()
            mock_print.assert_called_with("Error in health monitoring: Test error")

if __name__ == "__main__":
    unittest.main()