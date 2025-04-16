import time
import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from order import Order
from processor import OrderProcessor
from route_optimizer import RouteOptimizer
from inventory_manager import InventoryManager
from health_monitor import HealthMonitor, ComponentStatus

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
    category_weight = {
        "Food": 1,        # Food gets highest priority due to perishable nature
        "Electronics": 2,
        "Clothing": 3,
        "Home": 4
    }
    
    # Base priority calculation
    base_priority = urgency * 10
    
    # Time-sensitive adjustment
    time_priority = delivery_time * 2
    
    # Category weight (lower number = higher priority)
    category_priority = category_weight.get(category, 5)
    
    # Final priority (lower number = higher priority)
    final_priority = base_priority + time_priority + category_priority
    
    # For food items with same delivery time, give additional priority
    if category == "Food" and delivery_time <= 2:
        final_priority -= 5
        
    return final_priority

def manual_order_input():
    print("\nAvailable Products:")
    for product in PRODUCTS:
        # Show detailed inventory status
        inventory_status = inventory_manager.get_inventory_status(product["name"])
        quantity = inventory_status["quantity"] if inventory_status else "N/A"
        threshold = inventory_status["threshold"] if inventory_status else "N/A"
        print(f"{product['id']}: {product['name']} ({product['category']})")
        print(f"   Stock: {quantity} | Reorder Threshold: {threshold}")

    try:
        product_id = int(input("\nSelect product by ID: "))
        quantity = int(input("Enter quantity needed: "))
        urgency = int(input("Enter urgency level (1 = Highest priority, 5 = Lowest priority): "))
        delivery_time = int(input("Enter desired delivery time in hours: "))

        selected_product = next((p for p in PRODUCTS if p["id"] == product_id), None)
        if selected_product:
            # Check inventory availability for requested quantity
            inventory_status = inventory_manager.get_inventory_status(selected_product["name"])
            if not inventory_manager.check_availability(selected_product["name"], quantity):
                if inventory_status:
                    current_stock = inventory_status["quantity"]
                    print(f"\nSorry, insufficient stock! Available quantity: {current_stock}")
                else:
                    print("\nSorry, product not found in inventory!")
                return None, None

            # Update inventory with requested quantity
            success, message = inventory_manager.update_inventory(selected_product["name"], -quantity)
            if not success:
                print(message)
                return None, None

            # Show updated inventory status
            inventory_status = inventory_manager.get_inventory_status(selected_product["name"])
            new_stock = inventory_status["quantity"] if inventory_status else 0
            print(f"\nInventory updated - Current stock for {selected_product['name']}: {new_stock}")

            # Let user select delivery location
            print("\nSelect delivery location:")
            locations = ["Location A", "Location B", "Location C"]
            for idx, loc in enumerate(locations, 1):
                print(f"{idx}: {loc}")
            try:
                loc_choice = int(input("Enter location number (1-3): "))
                if 1 <= loc_choice <= 3:
                    location = locations[loc_choice - 1]
                else:
                    print("Invalid location choice! Using default Location A")
                    location = "Location A"
            except ValueError:
                print("Invalid input! Using default Location A")
                location = "Location A"

            description = f"{selected_product['name']} - {selected_product['category']} (Quantity: {quantity}, Will be delivered in {delivery_time} hours)"
            priority = calculate_priority(urgency, delivery_time, selected_product["category"])
            return Order(order_id=random.randint(1000, 9999), description=description, location=location), priority
        else:
            print("Invalid product selection!")
            return None, None
    except ValueError:
        print("Invalid input! Please try again.")
        return None, None

def main():
    print("Starting order processing...")
    
    # Initialize health monitoring
    health_monitor = HealthMonitor()
    
    # Initialize core components
    processor = OrderProcessor(num_threads=3)
    route_optimizer = RouteOptimizer()
    global inventory_manager
    inventory_manager = InventoryManager()
    
    # Register components for health monitoring
    health_monitor.register_component("order_processor")
    health_monitor.register_component("route_optimizer")
    health_monitor.register_component("inventory_manager")
    
    # Update initial component status
    health_monitor.update_component_status("order_processor", ComponentStatus.HEALTHY)
    health_monitor.update_component_status("route_optimizer", ComponentStatus.HEALTHY)
    health_monitor.update_component_status("inventory_manager", ComponentStatus.HEALTHY)
    
    # Add some delivery agents
    for i in range(3):
        route_optimizer.add_delivery_agent(f"Agent_{i+1}")

    try:
        # Print initial system health
        print("\nInitial System Health:")
        print(health_monitor.get_system_health_report())
        
        while True:
            print("\nWould you like to add an order? (Type 'yes' to proceed, 'health' for system status, or 'exit' to stop)")
            user_input = input().strip().lower()
            
            if user_input == 'exit':
                print("\nStopping order processing...")
                processor.stop_processing()
                print("\nExiting gracefully. Thank you for using the Order Processing System!")
                break
            elif user_input == 'yes':
                order, priority = manual_order_input()
                if order and priority:
                    # Monitor order processing performance
                    start_time = time.time()
                    processor.add_order(order, priority)
                    health_monitor.record_response_time(time.time() - start_time)
                    
                    print(f"\nOrder {order.order_id} has been successfully processed!")
                    print(f"Order Details: {order.description}")
                    print(f"Priority Level: {priority}")
                    
                    # Optimize delivery routes
                    route_optimizer.assign_orders([order])
                    
                    # Update queue metrics
                    health_monitor.update_queue_size("order_queue", processor.order_queue.qsize())
                    
                    print("\nWhat would you like to do next?")
                    print("1. Place another order")
                    print("2. Check system health")
                    print("3. Exit")
                    
                    while True:
                        choice = input("Enter your choice (1-3): ").strip()
                        if choice == "1":
                            break
                        elif choice == "2":
                            health_report = health_monitor.get_system_health_report()
                            print("\nCurrent System Health:")
                            print(f"Component Status: {health_report['component_status']}")
                            print(f"System Metrics: {health_report['system_metrics']}")
                            print("\nWould you like to:")
                            print("1. Place an order")
                            print("2. Exit")
                            sub_choice = input("Enter your choice (1-2): ").strip()
                            if sub_choice == "1":
                                break
                            elif sub_choice == "2":
                                print("\nStopping order processing...")
                                processor.stop_processing()
                                print("\nExiting gracefully. Thank you for using the Order Processing System!")
                                return
                        elif choice == "3":
                            print("\nStopping order processing...")
                            processor.stop_processing()
                            print("\nExiting gracefully. Thank you for using the Order Processing System!")
                            return
                        else:
                            print("Invalid choice! Please enter 1, 2, or 3.")
            elif user_input == 'health':
                health_report = health_monitor.get_system_health_report()
                print("\nCurrent System Health:")
                print(f"Component Status: {health_report['component_status']}")
                print(f"System Metrics: {health_report['system_metrics']}")
            else:
                print("Invalid choice! Please type 'yes', 'health' or 'exit'.")
    except KeyboardInterrupt:
        print("\nStopping order processing...")
        processor.stop_processing()
        health_monitor.stop()
        print("\nExiting gracefully. Thank you for using the Order Processing System!")

if __name__ == "__main__":
    main()
