import networkx as nx
from geopy.distance import geodesic
from collections import defaultdict

class RouteOptimizer:
    def __init__(self):
        # Initialize delivery locations (coordinates in Hyderabad)
        self.delivery_locations = {
            "Warehouse": (17.3850, 78.4867),  # Hyderabad center
            "Location A": (17.4350, 78.4980),  # Secunderabad
            "Location B": (17.4450, 78.4650),  # Kukatpally
            "Location C": (17.3750, 78.5240),  # LB Nagar
        }
        
        self.graph = self._build_graph()
        self.delivery_agents = {}
        self.agent_routes = defaultdict(list)

    def _build_graph(self):
        """Build graph with distances between locations."""
        graph = nx.Graph()
        
        # Add edges between all locations with real distances
        locations = list(self.delivery_locations.items())
        for i in range(len(locations)):
            for j in range(i + 1, len(locations)):
                loc1, coord1 = locations[i]
                loc2, coord2 = locations[j]
                distance = geodesic(coord1, coord2).kilometers
                graph.add_edge(loc1, loc2, weight=distance)
        
        return graph

    def optimize_route(self, orders, agent_id):
        """Optimize delivery route for given orders."""
        current_location = "Warehouse"
        route = [current_location]
        unvisited = set(orders)

        # Validate locations before processing
        valid_locations = [loc for loc in unvisited if loc in self.delivery_locations]
        if not valid_locations:
            print("No valid delivery locations found!")
            return [current_location]

        while valid_locations:
            # Find nearest unvisited location
            try:
                next_location = min(
                    valid_locations,
                    key=lambda x: nx.dijkstra_path_length(
                        self.graph, current_location, x
                    )
                )
                
                # Add shortest path to route
                path = nx.dijkstra_path(self.graph, current_location, next_location)
                route.extend(path[1:])  # Exclude current location to avoid duplicates
                
                current_location = next_location
                valid_locations.remove(next_location)
            except nx.NetworkXNoPath:
                print("No valid path found. Skipping location...")
                # Skip removing location as it was already handled in the try block
                continue

        # Return to warehouse
        final_path = nx.dijkstra_path(self.graph, current_location, "Warehouse")
        route.extend(final_path[1:])
        
        return route

    def assign_orders(self, orders):
        """Assign orders to available delivery agents."""
        if not self.delivery_agents:
            print("No delivery agents available!")
            return

        # Group orders by location
        location_orders = defaultdict(list)
        for order in orders:
            # Extract location from order description
            location = self._get_delivery_location(order)
            location_orders[location].append(order)

        # Assign orders to agents based on current load and location
        for location, orders in location_orders.items():
            agent_id = min(
                self.delivery_agents,
                key=lambda x: len(self.agent_routes[x])
            )
            route = self.optimize_route([location], agent_id)
            self.agent_routes[agent_id].extend(route)
            print(f"Assigned orders at {location} to Agent {agent_id}")
            print(f"Route: {' -> '.join(route)}")

    def add_delivery_agent(self, agent_id):
        """Add a new delivery agent."""
        self.delivery_agents[agent_id] = "Available"
        print(f"Added delivery agent {agent_id}")

    def _get_delivery_location(self, order):
        """Extract delivery location from order."""
        try:
            return order.location
        except AttributeError:
            # Fallback to default location if location not specified
            return "Location A"

    def remove_delivery_agent(self, agent_id):
        """Remove a delivery agent from the system."""
        if agent_id in self.delivery_agents:
            del self.delivery_agents[agent_id]
            if agent_id in self.agent_routes:
                del self.agent_routes[agent_id]
            return True
        return False

    def get_agent_workload(self, agent_id):
        """Get the current workload (number of assigned orders) for an agent."""
        if agent_id in self.agent_routes:
            return len(self.agent_routes[agent_id])
        return 0

    def optimize_routes(self, orders, agent_id=None):
        """Optimize routes for multiple orders, optionally for a specific agent."""
        if not orders:
            return []

        if agent_id and agent_id not in self.delivery_agents:
            raise ValueError(f"Agent {agent_id} not found")

        # Extract locations from orders
        locations = [self._get_delivery_location(order) for order in orders]
        
        # If agent_id is specified, optimize for that agent
        if agent_id:
            return self.optimize_route(locations, agent_id)
        
        # Otherwise, find the agent with the least workload
        available_agent = min(
            self.delivery_agents.keys(),
            key=lambda x: self.get_agent_workload(x)
        )
        return self.optimize_route(locations, available_agent)