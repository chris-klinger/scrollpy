"""
This module contains code for testing the ScrollSeq class.
"""

import os, unittest

from Bio import SeqIO

from scrollpy.sequences import _scrollseq

cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
data_dir = os.path.join(cur_dir, '../../fixtures') # /tests/


class TestScrollSeq(unittest.TestCase):
    """Tests instance creation and attribute accesss"""

    def setUp(self):
        """Parses a file to provide a single SeqRecord"""
        one_seq_file_path = os.path.join(data_dir, 'Hsap_AP1G_OneSeq.fa')
        with open(one_seq_file_path, 'r') as i:
            self.SeqRecord = SeqIO.read(i, "fasta")
        self.seq_object = _scrollseq.ScrollSeq(one_seq_file_path, 'one',
                self.SeqRecord)

    # Test incrementing distance
    def test_iadd_float(self):
        """Tests the _increment_distance method"""
        self.seq_object += 2.0
        self.assertEqual(self.seq_object._distance, 2.0)

    def test_iadd_int(self):
        """Tests the _increment_distance method"""
        self.seq_object += 2
        self.assertEqual(self.seq_object._distance, 2.0)

    def test_iadd_goodstr(self):
        """Tests the _incrememnt_distance method with number string"""
        self.seq_object += '2'
        self.assertEqual(self.seq_object._distance, 2.0)

    def test_iadd_badstr(self):
        """Tests the _increment_distance method with text string.
        Should raise a ValueError when float casting
        """
        with self.assertRaises(ValueError):
            self.seq_object += 'two'

    def test_iadd_negative(self):
        """Tests the _incremenent_distance method with < 0.
        Should raise a ValueError.
        """
        with self.assertRaises(ValueError):
            self.seq_object += -1.0

    # Test accessing and altering accession (SeqRecord.id)
    def test_accession_access(self):
        """Tests initial setting/retrieval through property"""
        self.assertEqual(self.seq_object.accession, "NP_001025178.1")

    def test_accession_setting(self):
        """Ensure attempts to set raise AttributeError"""
        with self.assertRaises(AttributeError):
            self.seq_object.accession = "NewValue"

    def test_accession_deletion_delattr(self):
        """Ensure attempts to delete accessions raise AttributeError"""
        with self.assertRaises(AttributeError):
            delattr(self.seq_object, "accession")

    def test_accession_deletion_del(self):
        """Should not be able to delete through del either"""
        with self.assertRaises(AttributeError):
            del self.seq_object.accession

    @unittest.skip("This actually works; leave as is or prevent?")
    def test_accession_deletion_deldict(self):
        """Also should not be able to use dictionary"""
        with self.assertRaises(AttributeError):
            del self.seq_object.__dict__["_accession"]

if __name__ == '__main__':
    unittest.main()
