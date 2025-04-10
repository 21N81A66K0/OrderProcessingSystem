import heapq

class PriorityQueue:
    def __init__(self):
        self.heap = []

    def push(self, item, priority):
        """Add an item to the priority queue as a tuple (priority, item)."""
        heapq.heappush(self.heap, (priority, item))

    def pop(self):
        """Remove and return the item with the highest priority."""
        if not self.is_empty():
            return heapq.heappop(self.heap)[1]
        raise IndexError("Pop from an empty priority queue")

    def peek(self):
        """Return the item with the highest priority without removing it."""
        if not self.is_empty():
            return self.heap[0][1]
        raise IndexError("Peek from an empty priority queue")

    def is_empty(self):
        """Check if the priority queue is empty."""
        return len(self.heap) == 0

    def size(self):
        """Return the number of items in the priority queue."""
        return len(self.heap)
