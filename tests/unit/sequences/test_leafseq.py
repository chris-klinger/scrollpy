"""
This module contains code for testing the ScrollSeq class.
"""

import os
import warnings
import unittest
from unittest.mock import Mock
from unittest.mock import patch

from Bio import SeqIO
from ete3 import Tree

from scrollpy import LeafSeq

cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
data_dir = os.path.join(cur_dir, '../../fixtures') # /tests/


class TestLeafSeq(unittest.TestCase):
    """Tests instance creation and attribute accesss"""

    @classmethod
    def setUpClass(cls):
        """Parses a file to provide a single LeafSeq"""
        # Get a leaf for the obj
        test_tree_path = os.path.join(
                data_dir,
                'Hsap_AP_EGADEZ.mfa.contree',
                )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cls.test_tree = Tree(test_tree_path, format=2)
        cls.test_leaf = cls.test_tree&'NP_001025178.1'
        # Get the corresponding sequence
        one_seq_file_path = os.path.join(
                data_dir,
                'Hsap_AP1G_OneSeq.fa',
                )
        with open(one_seq_file_path, 'r') as i:
            cls.record = SeqIO.read(i, "fasta")

    def setUp(self):
        """Make a new instace for each test"""
        self.tree_obj = LeafSeq(
                1, # ID
                'group1', # group
                self.test_leaf,  # Tree leaf
                self.record, # SeqRecord
                )

    def test_repr(self):
        """Tests the __repr__ method"""
        expected = "LeafSeq(1, 'group1', {!r}, {!r})".format(
                self.tree_obj._node, self.tree_obj._seq)
        self.assertEqual(expected, repr(self.tree_obj))

    def test_str(self):
        """Tests the __str__ method"""
        # Test when it has a sequence
        expected = "LeafSeq: {} {}".format(
                self.tree_obj._node, self.tree_obj._seq)
        self.assertEqual(expected, str(self.tree_obj))
        # Test when it has no sequence
        self.tree_obj._seq = None
        expected = "LeafSeq: {}".format(
                self.tree_obj._node)
        self.assertEqual(expected, str(self.tree_obj))

    def test_iadd(self):
        """Tests the __iadd__ method"""
        self.tree_obj += 2
        self.assertEqual(2.0, self.tree_obj._distance)
        # Check raising ValueError
        with self.assertRaises(ValueError):
            self.tree_obj += -2

    def test_less_than(self):
        """Tests the __lt__ method"""
        test_leaf = LeafSeq(2, 'two', 'node')
        # Test when the comparison is good
        self.tree_obj._distance = 4.0
        test_leaf._distance = 5.0
        self.assertTrue(self.tree_obj < test_leaf)
        # Test when the comparison is bad
        test_leaf._distance = 3.0
        self.assertFalse(self.tree_obj < test_leaf)

    def test_equality(self):
        """Tests the __eq__ method"""
        test_leaf = LeafSeq(2, 'two', 'node')
        # Test when the comparison is good
        self.tree_obj._distance = 4.0
        test_leaf._distance = 4.0
        self.assertTrue(self.tree_obj == test_leaf)
        # Test when the comparison is bad
        test_leaf._distance = 3.0
        self.assertFalse(self.tree_obj == test_leaf)

    def test_length(self):
        """Tests the __len__ method"""
        # Test when the obj has a sequence
        self.assertEqual(825, len(self.tree_obj))
        # Test when the obj has no sequence
        self.tree_obj._seq = None
        self.assertEqual(1, len(self.tree_obj))

    def test_getattr(self):
        """Tests the __getattr__ method"""
        # Test getting an attribute that is on a node
        self.assertEqual(
                self.tree_obj.children,
                self.tree_obj._node.children,
                )
        # Test getting an attribute that is on a seq
        self.assertEqual(
                self.tree_obj.description,
                self.tree_obj._seq.description,
                )
        # Test an attribute that isn't on either
        with self.assertRaises(AttributeError):
            print(self.tree_obj.foo)
        # Test a callable attribute
        some_func = Mock()
        setattr(self.tree_obj._node, 'test_func', some_func)
        self.assertEqual(
                self.tree_obj.test_func(1, 2, three=3),
                some_func(1, 2, three=3),
                )
        # Test callable when the arg is another LeafSeq
        test_leaf = LeafSeq(2, 'two', 'node')
        self.assertEqual(
                self.tree_obj.test_func(test_leaf),
                some_func('node'),  # Returns the func with _node arg
                )

    def test_write(self):
        """Tests the _write method"""
        mock_seq = Mock()
        self.tree_obj._seq = mock_seq
        mock_file = 'test/file/obj'
        self.tree_obj._write(mock_file)
        self.tree_obj._seq._write.assert_called_once_with(
                'test/file/obj',
                'fasta',
                )
        # Test without a seq obj
        self.tree_obj._seq = None
        with self.assertRaises(AttributeError):
            self.tree_obj._write(mock_file)

    def test_write_by_id(self):
        """Tests the _write method"""
        mock_seq = Mock()
        self.tree_obj._seq = mock_seq
        mock_file = 'test/file/obj'
        self.tree_obj._write_by_id(mock_file)
        self.tree_obj._seq._write_by_id.assert_called_once_with(
                'test/file/obj',
                )
        # Test without a seq obj
        self.tree_obj._seq = None
        with self.assertRaises(AttributeError):
            self.tree_obj._write_by_id(mock_file)

    def test_id_num(self):
        """Tests the id_num property"""
        self.assertEqual(1, self.tree_obj.id_num)
        # Test that setting raises AttributeError
        with self.assertRaises(AttributeError):
            self.tree_obj.id_num = 4
        # Test that deleting raises AttributeError
        with self.assertRaises(AttributeError):
            del self.tree_obj.id_num
