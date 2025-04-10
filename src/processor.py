from queue import PriorityQueue
import threading
import time
from collections import defaultdict

class OrderProcessor:
    def __init__(self, num_threads=3):
        self.order_queue = PriorityQueue()
        self.is_running = True
        self.threads = []
        self.lock = threading.Lock()
        self.delivery_slots = defaultdict(list)
        
    def add_order(self, order, priority):
        """Add an order to the processing queue with its priority."""
        with self.lock:
            # Extract delivery time from order description
            delivery_time = int(order.description.split("in ")[-1].split(" ")[0])
            
            # Adjust priority based on delivery slot availability
            adjusted_priority = self._calculate_adjusted_priority(priority, delivery_time)
            
            # Add to delivery slots tracker
            self.delivery_slots[delivery_time].append((adjusted_priority, order))
            
            # Add to processing queue with adjusted priority
            self.order_queue.put((adjusted_priority, order))
            print(f"Order added: {order}")
            print(f"Current delivery slot ({delivery_time} hours) load: {len(self.delivery_slots[delivery_time])} orders")

    def _calculate_adjusted_priority(self, base_priority, delivery_time):
        """Calculate adjusted priority based on delivery slot load."""
        slot_load = len(self.delivery_slots[delivery_time])
        
        # Higher priority orders (lower numbers) get preference
        if base_priority <= 20:  # High priority orders (urgency 1-2)
            return base_priority
        else:
            # Lower priority orders might be delayed if slot is busy
            return base_priority + (slot_load * 5)

    def _process_orders_worker(self, thread_id):
        """Worker thread that continuously processes orders."""
        while self.is_running:
            try:
                if not self.order_queue.empty():
                    with self.lock:
                        priority, order = self.order_queue.get_nowait()
                        delivery_time = int(order.description.split("in ")[-1].split(" ")[0])
                        
                        print(f"\nThread {thread_id} processing:")
                        print(f"Order: {order}")
                        print(f"Priority Level: {'High' if priority <= 20 else 'Low'}")
                        print(f"Delivery Slot: {delivery_time} hours")
                        
                        # Remove from delivery slots tracker
                        self.delivery_slots[delivery_time] = [
                            o for o in self.delivery_slots[delivery_time] if o[1].order_id != order.order_id
                        ]
                        
                        # Simulate processing
                        time.sleep(2)
                        self.order_queue.task_done()
                else:
                    time.sleep(1)
            except Exception as e:
                print(f"Error in thread {thread_id}: {e}")

    def stop_processing(self):
        """Stop all processing threads."""
        self.is_running = False
        for thread in self.threads:
            thread.join()
