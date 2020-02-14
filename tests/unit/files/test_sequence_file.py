"""
Module for testing 'sequence_file.py' classes/functions.
"""

import os, unittest, shutil

from Bio import SeqIO

from scrollpy.sequences._scrollseq import ScrollSeq
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

    def test_one_and_four(self):
        """Tests combining two non-zero lists"""
        one_seq_file = os.path.join(data_dir,'Hsap_AP1G_OneSeq.fa')
        four_seqs_file = os.path.join(data_dir,'Hsap_AP1G_FourSeqs.fa')
        one_record = sequence_file._get_sequences(one_seq_file)
        four_records = sequence_file._get_sequences(four_seqs_file)
        self.assertEqual(len(sequence_file._cat_sequence_lists(
            one_record, four_records)), 5)


class TestSequenceWriting(unittest.TestCase):
    """Tests '_sequence_list_to_file' function"""

    def setUp(self):
        """Makes a temporary directory in 'tests/fixtures'"""
        self.tmpdir = os.path.join(data_dir, 'tmp')
        try:
            os.makedirs(self.tmpdir)
        except FileExistsError:
            pass # already made
        self.one_seq_file = os.path.join(data_dir,'Hsap_AP1G_OneSeq.fa')
        self.four_seqs_file = os.path.join(data_dir,'Hsap_AP1G_FourSeqs.fa')
        self.one_record = sequence_file._get_sequences(
                self.one_seq_file)
        self.four_records = sequence_file._get_sequences(
                self.four_seqs_file)
        self.cat_list = sequence_file._cat_sequence_lists(
                self.one_record,
                self.four_records)

    # Old way
    def test_sequence_writing(self):
        """Makes a file and checks it"""
        new_seq_file = sequence_file._sequence_list_to_dir(
                self.tmpdir, self.cat_list)
        # Parse created file and ensure it has five records
        new_records = [record for record in SeqIO.parse(new_seq_file, "fasta")]
        self.assertEqual(len(new_records), 5)

    # New way -> Requires ScrollSeq objects!
    def test_sequence_writing_by_descr(self):
        """Makes a file using sequence descriptions"""
        outpath = os.path.join(self.tmpdir, 'write_by_descr.fa')
        seq_objs = []
        ids = (1,2,3,4,5)
        for seq_record, id_num in zip(self.cat_list, ids):
            seq_objs.append(ScrollSeq(
                id_num,
                id_num, # group; here, same as id
                seq_record = seq_record))
        sequence_file._sequence_list_to_file(seq_objs, outpath)
        new_records = [record for record in SeqIO.parse(
            outpath, # This method doesn't return filepath!
            "fasta")]
        self.assertEqual(len(new_records), 5)

    def test_sequence_writing_by_id(self):
        """Makes a file using ID as header instead"""
        outpath = os.path.join(self.tmpdir, 'write_by_id.fa')
        seq_objs = []
        ids = (1,2,3,4,5)
        for seq_record, id_num in zip(self.cat_list, ids):
            seq_objs.append(ScrollSeq(
                id_num,
                id_num, # group; here, same as id
                seq_record = seq_record))
        sequence_file._sequence_list_to_file_by_id(seq_objs, outpath)
        new_records = [record for record in SeqIO.parse(
            outpath, # This method doesn't return filepath!
            "fasta")]
        self.assertEqual(len(new_records), 5)

    def tearDown(self):
        """Removes the directory"""
        shutil.rmtree(self.tmpdir)


if __name__ == '__main__':
    unittest.main()
