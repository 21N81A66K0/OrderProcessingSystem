# src/processor.py
import threading
import time
from src.order import Order

class OrderProcessor:
    def __init__(self):
        self.orders = []
        self.lock = threading.Lock()

    def add_order(self, order):
        with self.lock:  # Ensures thread-safe addition of orders
            self.orders.append(order)
            print(f"Order added: {order}")

    def process_order(self):
        while True:
            with self.lock:  # Ensures thread-safe processing of orders
                if self.orders:
                    order = self.orders.pop(0)  # Process the first order in the list
                    print(f"Processing {order}")
            time.sleep(2)  # Simulates processing time

    def start_processing(self):
        # Spawn multiple threads to process orders
        for _ in range(3):  # You can adjust the number of threads
            thread = threading.Thread(target=self.process_order)
            thread.start()
