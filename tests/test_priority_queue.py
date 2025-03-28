import unittest
from src.priority_queue import PriorityQueue

class TestPriorityQueue(unittest.TestCase):
    def setUp(self):
        """Set up a PriorityQueue instance before each test."""
        self.pq = PriorityQueue()

    def test_push_and_pop(self):
        """Test adding and removing items in priority order."""
        self.pq.push("order1", 2)
        self.pq.push("order2", 1)
        self.pq.push("order3", 3)

        self.assertEqual(self.pq.pop(), "order2")
        self.assertEqual(self.pq.pop(), "order1")
        self.assertEqual(self.pq.pop(), "order3")

    def test_peek(self):
        """Test peeking at the highest-priority item."""
        self.pq.push("order1", 5)
        self.assertEqual(self.pq.peek(), "order1")
        self.pq.push("order2", 1)
        self.assertEqual(self.pq.peek(), "order2")

    def test_is_empty(self):
        """Test if the priority queue is initially empty and after pops."""
        self.assertTrue(self.pq.is_empty())
        self.pq.push("order1", 2)
        self.assertFalse(self.pq.is_empty())
        self.pq.pop()
        self.assertTrue(self.pq.is_empty())

    def test_size(self):
        """Test the size of the priority queue."""
        self.assertEqual(self.pq.size(), 0)
        self.pq.push("order1", 1)
        self.pq.push("order2", 2)
        self.assertEqual(self.pq.size(), 2)

if __name__ == "__main__":
    unittest.main()
