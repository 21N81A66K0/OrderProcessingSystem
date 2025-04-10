import threading
import time
from src.priority_queue import PriorityQueue

class OrderProcessor:
    def __init__(self):
        self.priority_queue = PriorityQueue()
        self.lock = threading.Lock()  # Ensures thread-safe access

    def add_order(self, order, priority):
        """Add an order to the priority queue safely."""
        with self.lock:
            self.priority_queue.push(order, priority)
            print(f"Order added: {order}")

    def process_order(self):
        """Process orders concurrently using threads."""
        while True:
            with self.lock:
                if not self.priority_queue.is_empty():
                    order = self.priority_queue.pop()
                    print(f"Processing {order}")
            time.sleep(2)  # Simulate processing delay

    def start_processing(self):
        """Start multiple threads to process orders."""
        for _ in range(3):  # Adjust the number of threads as needed
            thread = threading.Thread(target=self.process_order)
            thread.daemon = True  # Threads stop when the main process stops
            thread.start()
