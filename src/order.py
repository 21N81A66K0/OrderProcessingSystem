# src/order.py
class Order:
    def __init__(self, order_id, priority, description):
        self.order_id = order_id
        self.priority = priority
        self.description = description

    def __str__(self):
        return f"Order ID: {self.order_id}, Priority: {self.priority}, Description: {self.description}"
