# tests/test_processor.py
import unittest
from src.order import Order
from src.processor import OrderProcessor

class TestOrderProcessor(unittest.TestCase):
    def test_add_order(self):
        processor = OrderProcessor()
        order = Order(1, 1, "Test Order")
        processor.add_order(order)
        self.assertEqual(len(processor.orders), 1)

    def test_process_order(self):
        processor = OrderProcessor()
        order1 = Order(1, 1, "Order 1")
        order2 = Order(2, 2, "Order 2")
        processor.add_order(order1)
        processor.add_order(order2)
        
        # Start processing (simulate for testing)
        processor.process_order()
        self.assertEqual(len(processor.orders), 1)  # One order should be processed

if __name__ == '__main__':
    unittest.main()
