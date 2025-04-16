import unittest
import time
from unittest.mock import patch, MagicMock
from src.order import Order
from src.processor import OrderProcessor
from src.notification_service import NotificationService, Notification

class TestOrderProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = OrderProcessor()
        self.test_orders = [
            Order(1, "Order 1"),
            Order(2, "Order 2"),
            Order(3, "Order 3")
        ]

    def test_add_order(self):
        order = Order(1, "Test Order")
        self.processor.add_order(order, priority=1)
        self.assertEqual(self.processor.order_queue.qsize(), 1)

        # Test adding multiple orders with different priorities
        self.processor.add_order(Order(2, "High Priority"), priority=3)
        self.processor.add_order(Order(3, "Low Priority"), priority=1)
        self.assertEqual(self.processor.order_queue.qsize(), 3)

    def test_process_order(self):
        # Add orders with different priorities
        self.processor.add_order(self.test_orders[0], priority=2)
        self.processor.add_order(self.test_orders[1], priority=1)
        self.processor.add_order(self.test_orders[2], priority=3)

        # Verify highest priority order is processed first
        processed_order = self.processor.process_order()
        self.assertEqual(processed_order.order_id, self.test_orders[2].order_id)
        self.assertEqual(self.processor.order_queue.qsize(), 2)

        # Process remaining orders
        processed_order = self.processor.process_order()
        self.assertEqual(processed_order.order_id, self.test_orders[0].order_id)
        processed_order = self.processor.process_order()
        self.assertEqual(processed_order.order_id, self.test_orders[1].order_id)

    def test_process_empty_queue(self):
        # Test processing when queue is empty
        with self.assertRaises(AttributeError):
            self.processor.process_order()

    def test_error_handling(self):
        # Test error handling in worker threads
        self.processor.notification_service = MagicMock()
        self.processor.notification_service.send_notification.side_effect = Exception("Test error")
        
        order = Order(1, "Error Test Order in 1 hours")
        self.processor.add_order(order, priority=1)
        
        # Allow time for processing
        time.sleep(2)
        
        # Verify system continues running despite errors
        self.assertTrue(self.processor.is_running)
        self.assertTrue(any(thread.is_alive() for thread in self.processor.threads))

    @patch('src.processor.OrderProcessor.process_single_order')
    def test_batch_processing(self, mock_process):
        # Add multiple orders
        for order in self.test_orders:
            self.processor.add_order(order, priority=1)

        # Test batch processing
        self.processor.process_batch(batch_size=2)
        self.assertEqual(mock_process.call_count, 2)
        self.assertEqual(self.processor.order_queue.qsize(), 1)

    def test_order_status_transitions(self):
        order = self.test_orders[0]
        self.processor.add_order(order, priority=1)

        # Test status transitions during processing
        self.assertEqual(order.get_status(), "pending")
        processed_order = self.processor.process_order()
        self.assertEqual(processed_order.get_status(), "processed")

    def tearDown(self):
        # Clean up resources
        self.processor.stop_processing()
        for thread in self.processor.threads:
            thread.join(timeout=1)

    def test_concurrent_processing(self):
        # Mock notification service to avoid external dependencies
        self.processor.notification_service = MagicMock()
        
        # Add multiple orders with different priorities
        priorities = [3, 1, 2]
        test_orders = [
            Order(1, "Order 1 in 2 hours"),
            Order(2, "Order 2 in 1 hours"),
            Order(3, "Order 3 in 3 hours")
        ]
        
        for order, priority in zip(test_orders, priorities):
            self.processor.add_order(order, priority=priority)

        # Allow time for concurrent processing
        time.sleep(2)

        # Verify queue is empty after processing
        self.assertTrue(self.processor.order_queue.empty())

        # Verify delivery slots are populated correctly
        self.assertEqual(len(self.processor.delivery_slots[1]), 1)
        self.assertEqual(len(self.processor.delivery_slots[2]), 1)
        self.assertEqual(len(self.processor.delivery_slots[3]), 1)

        # Verify notifications were sent
        self.assertTrue(self.processor.notification_service.send_notification.called)
        self.assertEqual(
            self.processor.notification_service.send_notification.call_count,
            len(test_orders)
        )

        # Test thread safety with rapid order additions
        for i in range(5):
            order = Order(i + 10, f"Concurrent Order {i} in 1 hours")
            self.processor.add_order(order, priority=1)

        # Verify no exceptions during concurrent operations
        time.sleep(2)
        self.assertTrue(self.processor.is_running)
        
        # Verify thread pool is still active
        active_threads = sum(1 for thread in self.processor.threads if thread.is_alive())
        self.assertEqual(active_threads, len(self.processor.threads))

if __name__ == "__main__":
    unittest.main()
