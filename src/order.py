class Order:
    def __init__(self, order_id, description, location=None):
        self.order_id = order_id
        self.description = description
        self.location = location
        self._priority = None  # Add priority attribute
        self.status = "pending"  # Initialize status as pending

    def __str__(self):
        return f"Order ID: {self.order_id}, Description: {self.description}, Location: {self.location}"

    def __lt__(self, other):
        # Required for priority queue comparison
        if not isinstance(other, Order):
            return NotImplemented
        return self.order_id < other.order_id

    def __eq__(self, other):
        if not isinstance(other, Order):
            return NotImplemented
        return self.order_id == other.order_id

    def get_status(self):
        return self.status
