import unittest
from src.order import Order
from src.processor import OrderProcessor

class TestOrderProcessor(unittest.TestCase):
    def test_add_order(self):
        processor = OrderProcessor()
        order = Order(1, "Test Order")
        processor.add_order(order, priority=1)
        self.assertEqual(processor.priority_queue.size(), 1)

    def test_process_order(self):
        processor = OrderProcessor()
        order1 = Order(1, "Order 1")
        order2 = Order(2, "Order 2")
        processor.add_order(order1, priority=2)
        processor.add_order(order2, priority=1)

        # Simulate processing
        processor.process_order()  # Processes one order
        self.assertEqual(processor.priority_queue.size(), 1)

if __name__ == "__main__":
    unittest.main()
