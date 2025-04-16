from queue import PriorityQueue
import threading
import time
from collections import defaultdict
from notification_service import NotificationService, Notification, NotificationType, NotificationChannel

class OrderProcessor:
    def __init__(self, num_threads=3):
        self.order_queue = PriorityQueue()
        self.priority_queue = PriorityQueue()
        self.is_running = True
        self.threads = []
        self.lock = threading.Lock()
        self.delivery_slots = defaultdict(list)
        self.notification_service = NotificationService()

        # Create and start worker threads
        for i in range(num_threads):
            thread = threading.Thread(target=self._process_orders_worker, args=(i,))
            thread.daemon = True
            thread.start()
            self.threads.append(thread)

    def add_order(self, order, priority):
        """Add an order to the processing queue with its priority."""
        with self.lock:
            # Extract delivery time from order description
            delivery_time = int(order.description.split("in ")[-1].split(" ")[0])
            
            # Add to processing queue and priority queue
            self.order_queue.put((priority, id(order), order))
            self.priority_queue.put((priority, id(order), order))
            
            # Track order in delivery slots
            self.delivery_slots[delivery_time].append(order)
            
            # Send order placed notification
            notification = Notification(
                notification_type=NotificationType.ORDER_PLACED,
                message=f"New order received: {order.description}",
                recipient_id="admin",
                channel=NotificationChannel.SYSTEM_LOG
            )
            self.notification_service.send_notification(notification)
            print(f"Order added: {order}")
            print(f"Current delivery slot ({delivery_time} hours) load: {len(self.delivery_slots[delivery_time])} orders")

    def _process_orders_worker(self, thread_id):
        """Worker thread that continuously processes orders."""
        while self.is_running:
            try:
                if not self.order_queue.empty():
                    with self.lock:
                        _, _, order = self.order_queue.get_nowait()
                        print(f"Thread {thread_id} processing: {order}")
                        time.sleep(2)  # Simulate processing time
                        
                        # Send order status notification
                        notification = Notification(
                            notification_type=NotificationType.ORDER_STATUS,
                            message=f"Order {order.order_id} has been processed",
                            recipient_id="admin",
                            channel=NotificationChannel.SYSTEM_LOG
                        )
                        self.notification_service.send_notification(notification)
                        
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

    def process_order(self):
        """Process a single order from the priority queue."""
        if self.priority_queue.empty():
            raise AttributeError("No orders to process")
        
        _, _, order = self.priority_queue.get()
        order.status = "processed"
        return order

    def process_batch(self, batch_size):
        """Process a batch of orders."""
        for _ in range(batch_size):
            if not self.priority_queue.empty():
                self.process_single_order()

    def process_single_order(self):
        """Process a single order - helper method for batch processing."""
        if not self.priority_queue.empty():
            _, _, order = self.priority_queue.get()
            order.status = "processed"
            return order
