import unittest
from src.priority_queue import PriorityQueue

class TestPriorityQueue(unittest.TestCase):
    def setUp(self):
        self.pq = PriorityQueue()

    def test_push_and_pop(self):
        self.pq.push("order1", 2)
        self.pq.push("order2", 1)
        self.pq.push("order3", 3)

        self.assertEqual(self.pq.pop(), "order2")
        self.assertEqual(self.pq.pop(), "order1")
        self.assertEqual(self.pq.pop(), "order3")

    def test_peek(self):
        self.pq.push("order1", 5)
        self.assertEqual(self.pq.peek(), "order1")
        self.pq.push("order2", 1)
        self.assertEqual(self.pq.peek(), "order2")

    def test_is_empty(self):
        self.assertTrue(self.pq.is_empty())
        self.pq.push("order1", 2)
        self.assertFalse(self.pq.is_empty())
        self.pq.pop()
        self.assertTrue(self.pq.is_empty())

if __name__ == "__main__":
    unittest.main()
