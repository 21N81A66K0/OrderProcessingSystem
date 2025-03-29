
import time
from src.order import Order
from src.processor import OrderProcessor

def main():
    processor = OrderProcessor()

    # Simulate adding orders
    for i in range(1, 11):  # Create 10 sample orders
        order = Order(order_id=i, priority=i % 3, description=f"Order #{i}")
        processor.add_order(order)
        time.sleep(1)  # Simulates delay in order addition

    processor.start_processing()

if __name__ == "__main__":
    main()
