class Order:
    def __init__(self, order_id, description):
        self.order_id = order_id
        self.description = description

    def __str__(self):
        return f"Order ID: {self.order_id}, Description: {self.description}"
