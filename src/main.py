import time
import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from order import Order
from processor import OrderProcessor

# Product catalog for user selection
PRODUCTS = [
    {"id": 1, "name": "Laptop", "category": "Electronics"},
    {"id": 2, "name": "Phone", "category": "Electronics"},
    {"id": 3, "name": "Shoes", "category": "Clothing"},
    {"id": 4, "name": "Groceries", "category": "Food"},
    {"id": 5, "name": "Furniture", "category": "Home"}
]

def calculate_priority(urgency, delivery_time, category):
    """Calculate combined priority score based on urgency, delivery time, and product category."""
    category_weight = {"Electronics": 1, "Food": 2, "Clothing": 3, "Home": 4}
    return urgency * 10 + delivery_time * 2 + category_weight.get(category, 5)

def manual_order_input():
    """Allow users to manually select an order and its urgency."""
    print("\nAvailable Products:")
    for product in PRODUCTS:
        print(f"{product['id']}: {product['name']} ({product['category']})")

    try:
        product_id = int(input("\nSelect product by ID: "))
        urgency = int(input("Enter urgency level (1 = Highest priority, 5 = Lowest priority): "))
        delivery_time = int(input("Enter desired delivery time in hours: "))

        selected_product = next((p for p in PRODUCTS if p["id"] == product_id), None)
        if selected_product:
            description = f"{selected_product['name']} - {selected_product['category']} (Delivery: {delivery_time} hours)"
            priority = calculate_priority(urgency, delivery_time, selected_product["category"])
            return Order(order_id=random.randint(1000, 9999), description=description), priority
        else:
            print("Invalid product selection!")
            return None, None
    except ValueError:
        print("Invalid input! Please try again.")
        return None, None

def main():
    print("Starting order processing...")

    try:
        while True:
            print("\nWould you like to add an order? (Type 'yes' to proceed or 'exit' to stop)")
            user_input = input().strip().lower()
            if user_input == 'exit':
                print("\nExiting gracefully. Thank you for using the Order Processing System!")
                break
            elif user_input == 'yes':
                print("Order input simulated.")
            else:
                print("Invalid choice! Please type 'yes' or 'exit'.")
    except KeyboardInterrupt:
        print("\nExiting gracefully. Thank you for using the Order Processing System!")
