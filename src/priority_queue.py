import heapq

class PriorityQueue:
    def __init__(self):
        """Initialize an empty priority queue using a heap."""
        self.heap = []

    def push(self, item, priority):
        """
        Add an item to the priority queue with a given priority.
        
        Args:
        item: The data to be stored (e.g., order details).
        priority: An integer where a lower value means higher priority.
        """
        heapq.heappush(self.heap, (priority, item))

    def pop(self):
        """
        Remove and return the item with the highest priority.
        
        Returns:
        The item with the lowest priority value (highest priority).
        """
        if not self.is_empty():
            return heapq.heappop(self.heap)[1]
        raise IndexError("Pop from an empty priority queue")

    def peek(self):
        """
        Return the item with the highest priority without removing it.
        
        Returns:
        The item with the lowest priority value (highest priority).
        """
        if not self.is_empty():
            return self.heap[0][1]
        raise IndexError("Peek from an empty priority queue")

    def is_empty(self):
        """
        Check if the priority queue is empty.
        
        Returns:
        True if empty, False otherwise.
        """
        return len(self.heap) == 0

    def size(self):
        """
        Get the number of items in the priority queue.
        
        Returns:
        An integer representing the size of the priority queue.
        """
        return len(self.heap)
