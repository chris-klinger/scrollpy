"""
Tests /util/_counter

"""

import os
import unittest

from scrollpy.util._counter import ScrollCounter


class TestCounter(unittest.TestCase):
    """Tests singleton-like counter object"""

    @classmethod
    def setUpClass(cls):
        """Create a single instance for testing"""
        cls.c = ScrollCounter()

    def setUp(self):
        """Resets counter after each test"""
        self.c._reset_count()

    def test_repr(self):
        """Tests representation"""
        self.assertEqual(
                repr(self.c),
                "ScrollCounter",
                )

    def test_string(self):
        """Tests string representation"""
        self.assertEqual(
                str(self.c),
                "ScrollCounter: 1",
                )

    def test_counter_count(self):
        """Tests a single instance of counter"""
        self.assertEqual(
                self.c.current_count(),
                1,
                )

    def test_increment(self):
        """Tests that the counter increments correctly"""
        self.c()
        self.assertEqual(
                self.c.current_count(),
                2,
                )

    def test_shared_state(self):
        """Tests shared count value across instances"""
        c2 = ScrollCounter()
        self.c()  # Increase count
        self.assertEqual(
                c2.current_count(),
                2,
                )

