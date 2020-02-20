"""
This module contains code for testing the ScrollSeq class.
"""

import os
import unittest
from unittest.mock import Mock
from unittest.mock import patch

from Bio import SeqIO

from scrollpy.sequences import _scrollseq
from scrollpy.util._util import split_input

cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
data_dir = os.path.join(cur_dir, '../../fixtures') # /tests/


class TestScrollSeq(unittest.TestCase):
    """Tests instance creation and attribute accesss"""

    def setUp(self):
        """Parses a file to provide a single SeqRecord"""
        one_seq_file_path = os.path.join(data_dir, 'Hsap_AP1G_OneSeq.fa')
        with open(one_seq_file_path, 'r') as i:
            self.record = SeqIO.read(i, "fasta")
        # Make a record
        self.seq_obj = _scrollseq.ScrollSeq(
                1, # ID
                'one', # group
                self.record, # SeqRecord
                )

    def test_repr(self):
        """Tests the __repr__ method"""
        expected = "ScrollSeq(1, 'one', {!r})".format(
                self.record)
        self.assertEqual(expected, repr(self.seq_obj))

    def test_str(self):
        """Tests the __str__ method"""
        # Test with an associated record
        test_seq = str(self.record)
        expected = "ScrollSeq #1 with {}".format(test_seq)
        self.assertEqual(expected, str(self.seq_obj))
        # Now test with no associated record
        self.seq_obj._record = None
        expected = "ScrollSeq #1 with no sequence"
        self.assertEqual(expected, str(self.seq_obj))

    # Test incrementing distance
    def test_iadd_float(self):
        """Tests the _increment_distance method"""
        self.seq_obj += 2.0
        self.assertEqual(self.seq_obj._distance, 2.0)

    def test_iadd_int(self):
        """Tests the _increment_distance method"""
        self.seq_obj += 2
        self.assertEqual(self.seq_obj._distance, 2.0)

    def test_iadd_goodstr(self):
        """Tests the _incrememnt_distance method with number string"""
        self.seq_obj += '2'
        self.assertEqual(self.seq_obj._distance, 2.0)

    def test_iadd_badstr(self):
        """Tests the _increment_distance method with text string.
        Should raise a ValueError when float casting
        """
        with self.assertRaises(ValueError):
            self.seq_obj += 'two'

    def test_iadd_negative(self):
        """Tests the _incremenent_distance method with < 0.
        Should raise a ValueError.
        """
        with self.assertRaises(ValueError):
            self.seq_obj += -1.0

    def test_less_than(self):
        """Tests the __lt__ method"""
        test_seq = _scrollseq.ScrollSeq(
                2, 'two')
        # Test when the comparison is good
        self.seq_obj._distance = 4.0
        test_seq._distance = 5.0
        self.assertTrue(self.seq_obj < test_seq)
        # Test when the comparison is bad
        test_seq._distance = 3.0
        self.assertFalse(self.seq_obj < test_seq)

    def test_equality(self):
        """Tests the __eq__ method"""
        test_seq = _scrollseq.ScrollSeq(
                2, 'two')
        # Test when the comparison is good
        self.seq_obj._distance = 4.0
        test_seq._distance = 4.0
        self.assertTrue(self.seq_obj == test_seq)
        # Test when the comparison is bad
        test_seq._distance = 5.0
        self.assertTrue(self.seq_obj != test_seq)

    def test_length(self):
        """Tests the __len__ method"""
        self.assertEqual(
                len(self.seq_obj),
                len(self.seq_obj._record),
                )

    @patch('scrollpy.sequences._scrollseq.SeqIO.write')
    def test_write(self, mock_write):
        """Tests the _write method"""
        self.seq_obj._write('test_obj')
        mock_write.assert_called_once_with(
                self.record,
                'test_obj',
                'fasta',
                )
        # Test without associated record
        self.seq_obj._record = None
        with self.assertRaises(AttributeError):
            self.seq_obj._write('test_obj')

    def test_write_by_id(self):
        """Tests the _write_by_id method"""
        mock_fobj = Mock()
        self.seq_obj._write_by_id(mock_fobj)
        # Test assertions
        mock_fobj.write.assert_any_call('>1' + '\n')
        for chunk in split_input(self.seq_obj.seq):
            mock_fobj.write.assert_any_call(chunk + '\n')
        # Test without associated record
        self.seq_obj._record = None
        with self.assertRaises(AttributeError):
            self.seq_obj._write_by_id('test_obj')

    def test_id_num_property(self):
        """Test id_num setter/getter/deleter"""
        self.assertEqual(1, self.seq_obj.id_num)
        with self.assertRaises(AttributeError):
            self.seq_obj.id_num = 2
        with self.assertRaises(AttributeError):
            del self.seq_obj.id_num

    def test_accession_property(self):
        """Test accession setter/getter/deleter"""
        self.assertEqual(self.seq_obj.accession, self.seq_obj._record.id)
        # Test without seq obj
        self.seq_obj._record = None
        self.assertEqual(self.seq_obj.accession, None)
        with self.assertRaises(AttributeError):
            self.seq_obj.accession = 'new'
        with self.assertRaises(AttributeError):
            del self.seq_obj.accession

    def test_name_property(self):
        """Test name setter/getter/deleter"""
        self.assertEqual(self.seq_obj.name, self.seq_obj._record.name)
        # Test without seq obj
        self.seq_obj._record = None
        self.assertEqual(self.seq_obj.name, None)
        with self.assertRaises(AttributeError):
            self.seq_obj.name = 'new'
        with self.assertRaises(AttributeError):
            del self.seq_obj.name

    def test_description_property(self):
        """Test description setter/getter/deleter"""
        self.assertEqual(self.seq_obj.description,
                self.seq_obj._record.description)
        # Test without seq obj
        self.seq_obj._record = None
        self.assertEqual(self.seq_obj.description, None)
        with self.assertRaises(AttributeError):
            self.seq_obj.description = 'new'
        with self.assertRaises(AttributeError):
            del self.seq_obj.description

    def test_seq_property(self):
        """Test seq setter/getter/deleter"""
        self.assertEqual(self.seq_obj.seq, self.seq_obj._record.seq)
        # Test without seq obj
        self.seq_obj._record = None
        self.assertEqual(self.seq_obj.seq, None)
        with self.assertRaises(AttributeError):
            self.seq_obj.seq = 'new'
        with self.assertRaises(AttributeError):
            del self.seq_obj.seq

if __name__ == '__main__':
    unittest.main()
