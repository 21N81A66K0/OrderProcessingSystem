import time
from queue import PriorityQueue

class OrderProcessor:
    def __init__(self):
        self.order_queue = PriorityQueue()

    def add_order(self, order, priority):
        """Add an order to the processing queue with its priority."""
        self.order_queue.put((priority, order))
        print(f"Order added: {order}")

    def process_order(self):
        """Process the next order in the queue."""
        if not self.order_queue.empty():
            priority, order = self.order_queue.get()
            print(f"Processing {order}")  # The order will now use the updated format

def process_order(self):
    """Process orders concurrently using threads."""
    while True:
        with self.lock:
            if not self.priority_queue.is_empty():
                order = self.priority_queue.pop()
                # Extract delivery time from the order description
                delivery_time = self.extract_delivery_time(order.description)
                print(f"Processing {order} | Delivery: in {delivery_time}")
        time.sleep(2)  # Simulate processing delay

def extract_delivery_time(self, description):
    """Extract delivery time from the order description."""
    # Example: "Laptop - Electronics (Delivery: 3 hours)"
    start_idx = description.find("Delivery: in") + len("Delivery: in")
    end_idx = description.find("hours", start_idx)
    return description[start_idx:end_idx].strip()
