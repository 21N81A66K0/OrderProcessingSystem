from collections import defaultdict
import threading
import json
import os
from src.notification_service import NotificationService, Notification, NotificationType, NotificationChannel

class InventoryManager:
    def __init__(self):
        self.lock = threading.Lock()  # For thread-safe operations
        self.inventory = defaultdict(dict)
        self.reorder_thresholds = {}
        self.notification_service = NotificationService()
        self.load_initial_inventory()

    def load_initial_inventory(self):
        """Initialize inventory with default values."""
        initial_inventory = {
            "Laptop": {"quantity": 50, "threshold": 10},
            "Phone": {"quantity": 100, "threshold": 20},
            "Shoes": {"quantity": 200, "threshold": 30},
            "Groceries": {"quantity": 500, "threshold": 100},
            "Furniture": {"quantity": 30, "threshold": 5}
        }
        
        with self.lock:
            for product, details in initial_inventory.items():
                self.inventory[product] = {
                    "quantity": details["quantity"],
                    "threshold": details["threshold"]
                }

    def check_availability(self, product_name, quantity=1):
        """Prevent orders for out-of-stock items."""
        with self.lock:
            if product_name in self.inventory:
                return self.inventory[product_name]["quantity"] >= quantity
            return False

    def update_inventory(self, product_name, quantity_change):
        """Maintain accurate inventory counts with thread safety."""
        with self.lock:
            if product_name in self.inventory:
                current_quantity = self.inventory[product_name]["quantity"]
                new_quantity = current_quantity + quantity_change
                
                if new_quantity < 0:
                    return False, "Insufficient inventory"
                
                self.inventory[product_name]["quantity"] = new_quantity
                
                # Generate alerts when inventory is low
                if new_quantity <= self.inventory[product_name]["threshold"]:
                    # Send low inventory notification
                    notification = Notification(
                        notification_type=NotificationType.INVENTORY_ALERT,
                        message=f"Low inventory alert for {product_name}! Current stock: {new_quantity}",
                        recipient_id="admin",
                        channel=NotificationChannel.SYSTEM_LOG
                    )
                    self.notification_service.send_notification(notification)
                    self._trigger_reorder_alert(product_name, new_quantity)
                
                return True, f"Inventory updated. New quantity: {new_quantity}"
            return False, "Product not found"

    def _trigger_reorder_alert(self, product_name, current_quantity):
        """Generate alerts for low inventory."""
        threshold = self.inventory[product_name]["threshold"]
        print(f"\n{'='*50}")
        print(f"ALERT: Low inventory for {product_name}")
        print(f"Current quantity: {current_quantity}")
        print(f"Reorder threshold: {threshold}")
        print("Please restock soon!")
        print(f"{'='*50}\n")

    def get_inventory_status(self, product_name):
        """Get current inventory status."""
        with self.lock:
            if product_name in self.inventory:
                return self.inventory[product_name]
            return None

    def bulk_update(self, updates):
        """Update multiple inventory items at once."""
        results = {}
        success = True

        with self.lock:
            for product_name, quantity_change in updates.items():
                update_success, message = self.update_inventory(product_name, quantity_change)
                results[product_name] = message
                if not update_success:
                    success = False

        return success, results

    def check_low_stock(self, product_name):
        """Check if a product is below its reorder threshold."""
        with self.lock:
            if product_name in self.inventory:
                current_quantity = self.inventory[product_name]["quantity"]
                threshold = self.inventory[product_name]["threshold"]
                return current_quantity <= threshold
            return False

    def notify_low_stock(self, product_name):
        """Send notification for low stock items."""
        with self.lock:
            if product_name in self.inventory:
                current_quantity = self.inventory[product_name]["quantity"]
                threshold = self.inventory[product_name]["threshold"]
                
                if current_quantity <= threshold:
                    notification = Notification(
                        notification_type=NotificationType.INVENTORY_ALERT,
                        message=f"Low stock alert for {product_name}. Current quantity: {current_quantity}",
                        recipient_id="admin",
                        channel=NotificationChannel.SYSTEM_LOG
                    )
                    self.notification_service.send_notification(notification)
                    return True
            return False