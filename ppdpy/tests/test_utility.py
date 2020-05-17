import unittest
from ppdpy.utility import listview


class TestListview(unittest.TestCase):
    def test_walk(self):
        tail = listview(range(100))
        for i in range(100):
            head, tail = tail.walk()
            self.assertEqual(head, i)
            self.assertEqual(len(tail), 99 - i)

    def test_empty(self):
        lv = listview([])
        self.assertEqual(len(lv), 0)
        val = True if lv else False
        self.assertFalse(val)

    def test_walk_to_empty(self):
        lv = listview([1, 2, 3])
        self.assertEqual(lv.h, 0)

        head, tail = lv.walk()
        self.assertEqual(tail.h, 1)
        self.assertEqual(head, 1)
        self.assertTrue(tail)

        head, tail = tail.walk()
        self.assertEqual(tail.h, 2)
        self.assertEqual(head, 2)
        self.assertTrue(tail)

        head, tail = tail.walk()
        self.assertEqual(head, 3)
        self.assertFalse(tail)

        with self.assertRaises(StopIteration):
            tail.walk()
