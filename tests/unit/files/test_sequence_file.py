"""
Module for testing 'sequence_file.py' classes/functions.
"""

import os, unittest, shutil

from Bio import SeqIO

from scrollpy.files import sequence_file

# Relative path access to test data
cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
data_dir = os.path.join(cur_dir, '../../fixtures/') #/tests/fixtures/


class TestSequenceParsing(unittest.TestCase):
    """Tests '_get_sequences' function"""

    def test_one_sequence(self):
        """Tests that parsing one sequence works fine."""
        one_seq_file = os.path.join(data_dir,'Hsap_AP1G_OneSeq.fa')
        records = sequence_file._get_sequences(one_seq_file)
        self.assertEqual(len(records), 1)

    def test_four_sequences(self):
        """Tests that parsing four sequences works fine."""
        four_seqs_file = os.path.join(data_dir,'Hsap_AP1G_FourSeqs.fa')
        records = sequence_file._get_sequences(four_seqs_file)
        self.assertEqual(len(records), 4)


class TestSequenceConcatenation(unittest.TestCase):
    """Tests '_cat_sequence_lists' function"""

    def setUp(self):
        """Makes a temporary directory in 'tests/fixtures'"""
        self.tmpdir = os.path.join(data_dir, 'tmp')
        os.makedirs(self.tmpdir)

    def test_sequence_concatenation(self):
        """Makes a file and checks it"""
        one_seq_file = os.path.join(data_dir,'Hsap_AP1G_OneSeq.fa')
        four_seqs_file = os.path.join(data_dir,'Hsap_AP1G_FourSeqs.fa')
        one_record = sequence_file._get_sequences(one_seq_file)
        four_records = sequence_file._get_sequences(four_seqs_file)
        new_seq_file = sequence_file._cat_sequence_lists(
                self.tmpdir, one_record, four_records)
        # Parse created file and ensure it has five records
        new_records = [record for record in SeqIO.parse(new_seq_file, "fasta")]
        self.assertEqual(len(new_records), 5)

    def tearDown(self):
        """Removes the directory"""
        shutil.rmtree(self.tmpdir)


if __name__ == '__main__':
    unittest.main()
