import unittest
import threading
from collections import defaultdict
from unittest.mock import patch, Mock
from src.inventory_manager import InventoryManager

class TestInventoryManager(unittest.TestCase):
    def setUp(self):
        self.inventory_manager = InventoryManager()
        # Initialize inventory with proper structure matching defaultdict
        self.test_products = defaultdict(dict, {
            "Laptop": {"quantity": 10, "threshold": 5},
            "Phone": {"quantity": 15, "threshold": 8},
            "Groceries": {"quantity": 50, "threshold": 20}
        })
        with self.inventory_manager.lock:
            self.inventory_manager.inventory = self.test_products

    def test_get_inventory_status(self):
        # Test existing product
        status = self.inventory_manager.get_inventory_status("Laptop")
        self.assertIsNotNone(status)
        if status:  # Safe access after None check
            self.assertEqual(status["quantity"], 10)
            self.assertEqual(status["threshold"], 5)

        # Test non-existing product
        status = self.inventory_manager.get_inventory_status("NonExistentProduct")
        self.assertIsNone(status)

    def test_check_availability(self):
        # Test sufficient quantity
        self.assertTrue(self.inventory_manager.check_availability("Laptop", 5))
        
        # Test insufficient quantity
        self.assertFalse(self.inventory_manager.check_availability("Laptop", 15))
        
        # Test non-existing product
        self.assertFalse(self.inventory_manager.check_availability("NonExistentProduct", 1))

        # Test boundary conditions
        self.assertTrue(self.inventory_manager.check_availability("Laptop", 10))  # Exact quantity
        self.assertFalse(self.inventory_manager.check_availability("Laptop", -1))  # Negative quantity

    def tearDown(self):
        # Clean up the inventory after each test
        with self.inventory_manager.lock:
            self.inventory_manager.inventory = defaultdict(dict)

    def test_update_inventory(self):
        # Test successful decrease
        success, _ = self.inventory_manager.update_inventory("Laptop", -2)
        self.assertTrue(success)
        status = self.inventory_manager.get_inventory_status("Laptop")
        self.assertIsNotNone(status)
        if status:  # Safe access after None check
            self.assertEqual(status["quantity"], 8)

        # Test successful increase
        success, _ = self.inventory_manager.update_inventory("Phone", 5)
        self.assertTrue(success)
        status = self.inventory_manager.get_inventory_status("Phone")
        self.assertIsNotNone(status)
        if status:  # Safe access after None check
            self.assertEqual(status["quantity"], 20)

        # Test invalid decrease (insufficient quantity)
        success, message = self.inventory_manager.update_inventory("Laptop", -10)
        self.assertFalse(success)
        self.assertIn("Insufficient", message)

        # Test non-existing product
        success, message = self.inventory_manager.update_inventory("NonExistentProduct", -1)
        self.assertFalse(success)
        self.assertIn("not found", message)

        # Test zero quantity update
        success, _ = self.inventory_manager.update_inventory("Laptop", 0)
        self.assertTrue(success)
        status = self.inventory_manager.get_inventory_status("Laptop")
        self.assertIsNotNone(status)
        if status:  # Safe access after None check
            self.assertEqual(status["quantity"], 8)

    def test_low_stock_alert(self):
        # Test product above threshold
        self.assertFalse(self.inventory_manager.check_low_stock("Laptop"))

        # Reduce quantity below threshold
        self.inventory_manager.update_inventory("Laptop", -6)
        self.assertTrue(self.inventory_manager.check_low_stock("Laptop"))

        # Test exact threshold
        self.inventory_manager.update_inventory("Phone", -7)  # Set to threshold
        self.assertTrue(self.inventory_manager.check_low_stock("Phone"))

    @patch('src.inventory_manager.InventoryManager.notify_low_stock')
    def test_low_stock_notification(self, mock_notify):
        # Test single notification
        self.inventory_manager.update_inventory("Laptop", -6)
        status = self.inventory_manager.get_inventory_status("Laptop")
        self.assertIsNotNone(status)
        if status:  # Safe access after None check
            mock_notify.assert_called_once_with("Laptop", status["quantity"])

        # Test multiple notifications
        mock_notify.reset_mock()
        self.inventory_manager.update_inventory("Phone", -8)
        status = self.inventory_manager.get_inventory_status("Phone")
        self.assertIsNotNone(status)
        if status:  # Safe access after None check
            mock_notify.assert_called_once_with("Phone", status["quantity"])

    def test_bulk_update(self):
        # Test successful bulk update
        updates = {
            "Laptop": -2,
            "Phone": 5,
            "Groceries": -10
        }
        success, results = self.inventory_manager.bulk_update(updates)
        self.assertTrue(success)
        status = self.inventory_manager.get_inventory_status("Laptop")
        self.assertIsNotNone(status)
        if status:  # Safe access after None check
            self.assertEqual(status["quantity"], 8)
        status = self.inventory_manager.get_inventory_status("Phone")
        self.assertIsNotNone(status)
        if status:  # Safe access after None check
            self.assertEqual(status["quantity"], 20)
        status = self.inventory_manager.get_inventory_status("Groceries")
        self.assertIsNotNone(status)
        if status:  # Safe access after None check
            self.assertEqual(status["quantity"], 40)

        # Test bulk update with invalid quantities
        invalid_updates = {
            "Laptop": -20,  # More than available
            "Phone": 5,
            "NonExistent": 1  # Non-existent product
        }
        success, results = self.inventory_manager.bulk_update(invalid_updates)
        self.assertFalse(success)
        self.assertIn("Insufficient", results["Laptop"])
        self.assertIn("not found", results["NonExistent"])
        
        # Verify no changes were made due to invalid update
        status = self.inventory_manager.get_inventory_status("Laptop")
        self.assertIsNotNone(status)
        if status:  # Safe access after None check
            self.assertEqual(status["quantity"], 8)
        status = self.inventory_manager.get_inventory_status("Phone")
        self.assertIsNotNone(status)
        if status:  # Safe access after None check
            self.assertEqual(status["quantity"], 20)

        # Test empty update dictionary
        success, results = self.inventory_manager.bulk_update({})
        self.assertTrue(success)
        self.assertEqual(results, {})

        # Test update with None values
        with self.assertRaises(ValueError):
            self.inventory_manager.bulk_update({"Laptop": None})

        # Test update with non-numeric values
        with self.assertRaises(ValueError):
            self.inventory_manager.bulk_update({"Laptop": "invalid"})

    def test_concurrent_updates(self):
        def update_product(product, amount, results):
            success, msg = self.inventory_manager.update_inventory(product, amount)
            results.append((success, msg))

        # Test concurrent updates to the same product
        results = []
        threads = [
            threading.Thread(target=update_product, args=("Laptop", -2, results)),
            threading.Thread(target=update_product, args=("Laptop", 3, results)),
            threading.Thread(target=update_product, args=("Laptop", -1, results))
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Verify all updates were processed and final quantity is correct
        status = self.inventory_manager.get_inventory_status("Laptop")
        self.assertIsNotNone(status)
        if status:  # Safe access after None check
            self.assertEqual(status["quantity"], 10)  # Initial 10 + (-2 + 3 - 1) = 10
        self.assertEqual(len(results), 3)  # All operations completed
        
        # Verify all operations were successful
        self.assertTrue(all(success for success, _ in results))

    def test_edge_cases(self):
        # Test update with zero quantity
        success, msg = self.inventory_manager.update_inventory("Laptop", 0)
        self.assertTrue(success)
        status = self.inventory_manager.get_inventory_status("Laptop")
        self.assertIsNotNone(status)
        if status:  # Safe access after None check
            self.assertEqual(status["quantity"], 10)

        # Test update with very large number
        success, msg = self.inventory_manager.update_inventory("Laptop", 1000000)
        self.assertTrue(success)
        status = self.inventory_manager.get_inventory_status("Laptop")
        self.assertIsNotNone(status)
        if status:  # Safe access after None check
            self.assertEqual(status["quantity"], 1000010)

        # Test update with very large negative number
        success, msg = self.inventory_manager.update_inventory("Laptop", -1000010)
        self.assertFalse(success)
        self.assertIn("Insufficient", msg)

if __name__ == "__main__":
    unittest.main()