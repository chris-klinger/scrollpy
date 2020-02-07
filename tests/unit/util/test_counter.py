"""
Tests /util/_counter

"""

import os
import unittest

from scrollpy.util._counter import Counter


class TestCounter(unittest.TestCase):
    """Tests singleton-like counter object"""

    @classmethod
    def setUp(cls):
        """Create a single instance for testing"""
        cls.c = Counter()

    def tearDown(self):
        """Resets counter after each test"""
        self.c._reset_count()

    def test_repr(self):
        """Tests representation"""
        self.assertEqual(
                repr(self.c),
                "Counter",
                )

    def test_string(self):
        """Tests string representation"""
        self.assertEqual(
                str(self.c),
                "Counter: 1",
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
        c2 = Counter()
        self.c()  # Increase count
        self.assertEqual(
                c2.current_count(),
                2,
                )

