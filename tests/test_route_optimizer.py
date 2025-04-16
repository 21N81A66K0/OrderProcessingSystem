import unittest
from src.route_optimizer import RouteOptimizer
from src.order import Order

class TestRouteOptimizer(unittest.TestCase):
    def setUp_basic_agents(self):
        self.route_optimizer = RouteOptimizer()
        # Add test delivery agents
        self.test_agents = ["Agent_1", "Agent_2", "Agent_3"]
        for agent in self.test_agents:
            self.route_optimizer.add_delivery_agent(agent)

    def test_add_delivery_agent(self):
        # Test adding a new agent
        new_agent = "Agent_4"
        self.route_optimizer.add_delivery_agent(new_agent)
        self.assertIn(new_agent, self.route_optimizer.delivery_agents)

        # Test adding duplicate agent
        initial_count = len(self.route_optimizer.delivery_agents)
        self.route_optimizer.add_delivery_agent(new_agent)
        self.assertEqual(len(self.route_optimizer.delivery_agents), initial_count)

    def test_remove_delivery_agent(self):
        # Test removing existing agent
        agent_to_remove = "Agent_1"
        self.route_optimizer.remove_delivery_agent(agent_to_remove)
        self.assertNotIn(agent_to_remove, self.route_optimizer.delivery_agents)

        # Test removing non-existent agent
        initial_count = len(self.route_optimizer.delivery_agents)
        self.route_optimizer.remove_delivery_agent("NonExistentAgent")
        self.assertEqual(len(self.route_optimizer.delivery_agents), initial_count)

    def test_assign_orders(self):
        # Create test orders with locations
        orders = [
            Order(1, "Order 1 - Electronics", "Location A"),
            Order(2, "Order 2 - Food", "Location B"),
            Order(3, "Order 3 - Clothing", "Location C"),
            Order(4, "Order 4 - Books", "Location A"),
            Order(5, "Order 5 - Groceries", "Location B")
        ]

        # Test order assignment
        assignments = self.route_optimizer.assign_orders(orders)
        
        # Verify all orders are assigned
        assigned_orders = []
        if self.route_optimizer.agent_routes:
            for agent_id, agent_orders in self.route_optimizer.agent_routes.items():
                assigned_orders.extend(agent_orders)
        self.assertEqual(len(assigned_orders), len(orders))
        
        # Verify unique order assignments
        order_ids = [order.order_id for order in assigned_orders]
        self.assertEqual(len(order_ids), len(set(order_ids)))

        # Verify assignments are distributed among available agents
        agent_workloads = self.route_optimizer.agent_routes
        if agent_workloads:
            workloads = [len(routes) for routes in agent_workloads.values()]
            max_workload = max(workloads) if workloads else 0
            min_workload = min(workloads) if workloads else 0
            # Ensure no agent has more than 2 orders more than any other agent
            self.assertLessEqual(max_workload - min_workload, 2)

            # Verify location-based assignment efficiency
            for agent_orders in agent_workloads.values():
                if len(agent_orders) > 1:
                    # Check if orders with same locations are assigned to same agent
                    location_groups = {}
                    for order in agent_orders:
                        if order and hasattr(order, 'location'):
                            location = order.location
                            if location:
                                if location not in location_groups:
                                    location_groups[location] = 0
                                location_groups[location] += 1
                    # At least one location should have multiple orders
                    if location_groups:
                        self.assertTrue(any(count > 1 for count in location_groups.values()))

    def test_get_agent_workload(self):
        # Test initial workload
        for agent in self.test_agents:
            self.assertEqual(self.route_optimizer.get_agent_workload(agent), 0)

        # Add orders and test workload
        orders = [Order(1, "Test Order", "Location A")]
        assignments = self.route_optimizer.assign_orders(orders)
        self.assertIsNotNone(assignments, "Assignment should not be None")
        if assignments:
            assigned_agent = list(assignments.keys())[0]
            self.assertEqual(self.route_optimizer.get_agent_workload(assigned_agent), 1)

    def setUp(self):
        self.route_optimizer = RouteOptimizer()
        # Add test delivery agents
        self.test_agents = ["Agent_1", "Agent_2", "Agent_3"]
        for agent in self.test_agents:
            self.route_optimizer.add_delivery_agent(agent)
            
        # Initialize test locations
        self.test_locations = ["Location A", "Location B", "Location C"]
        
        # Verify graph initialization
        self.assertIsNotNone(self.route_optimizer.graph)
        self.assertTrue(self.route_optimizer.graph.has_node("Warehouse"))
        for loc in self.test_locations:
            self.assertTrue(self.route_optimizer.graph.has_node(loc))

    def test_optimize_routes(self):
        # Create test orders with locations
        orders = [
            Order(1, "Order 1", "Location A"),
            Order(2, "Order 2", "Location B"),
            Order(3, "Order 3", "Location C")
        ]

        # Test route optimization
        optimized_routes = self.route_optimizer.optimize_routes(orders)
        self.assertIsNotNone(optimized_routes, "Optimized routes should not be None")
        
        # Verify all orders are included in routes
        routed_orders = []
        if optimized_routes:
            for route in optimized_routes:
                routed_orders.extend(route)
        self.assertEqual(len(routed_orders), len(orders))
        
        # Verify each order appears exactly once in routes
        order_ids = [order.order_id for order in routed_orders]
        self.assertEqual(len(order_ids), len(set(order_ids)))

        # Verify route optimization logic
        if optimized_routes:
            for agent_id, route in enumerate(optimized_routes):
                if not route:
                    continue
                # Verify route starts and ends at warehouse
                self.assertEqual(route[0], "Warehouse")
                self.assertEqual(route[-1], "Warehouse")
                
                # Verify route continuity
                for i in range(len(route) - 1):
                    loc1, loc2 = route[i], route[i + 1]
                    self.assertTrue(self.route_optimizer.graph.has_edge(loc1, loc2))
                    
                # Calculate and verify total route distance
                total_distance = sum(self.route_optimizer.graph[route[i]][route[i+1]]["weight"]
                                    for i in range(len(route)-1))
                
                # Verify route efficiency
                route_orders = [order for order in orders if order.location and order.location in route]
                direct_distances = [self.route_optimizer.graph["Warehouse"][order.location]["weight"]
                                  for order in route_orders]
                min_possible_distance = 2 * sum(direct_distances)  # Round trip
                self.assertLess(total_distance, min_possible_distance * 1.5)

if __name__ == "__main__":
    unittest.main()