"""
Tests /sequences/_collection.py
"""

import os, unittest, shutil

from scrollpy.sequences._scrollseq import ScrollSeq
from scrollpy.sequences._collection import ScrollCollection
from scrollpy.files import sequence_file as sf

cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
# cleaner to use realpath due to relative path
data_dir = os.path.realpath(os.path.join(cur_dir, '../../fixtures')) # /tests/


class TestScrollCollection(unittest.TestCase):
    """Tests each individual method"""

    def setUp(self):
        """Creates a new ScrollCollection Object"""
        ids = (1,2,3,4)
        infile = os.path.join(data_dir, 'Hsap_AP1G_FourSeqs.fa')
        records = sf._get_sequences(infile)
        self.seq_list = []
        for id_num, seq_record in zip(ids, records):
            self.seq_list.append(ScrollSeq(
                id_num, # ID
                infile, # infile
                id_num, # Group; not important here
                SeqRecord = seq_record))
        self.tmpdir = os.path.join(data_dir, 'tmp')
        try:
            os.makedirs(self.tmpdir)
        except FileExistsError:
            pass # tmpdir still present
        self.collection = ScrollCollection(
                self.tmpdir, # outdir
                self.seq_list, # sequence list
                'one', # group
                'Mafft', # align_method
                'RAxML',# dist_method
                )

    def test_file_creation(self):
        """Tests internal file creation method"""
        expected_file = os.path.join(self.tmpdir, 'one.fa')
        self.collection._get_sequence_file()
        self.assertTrue(os.path.exists(expected_file))

    def test_file_alignment(self):
        """Tests internal call to alignment"""
        expected_file = os.path.join(self.tmpdir, 'one.mfa')
        self.collection._get_sequence_file()
        self.collection._get_alignment()
        self.assertTrue(os.path.exists(expected_file))

    def test_file_distance(self):
        """Tests internal call to distance"""
        expected_file = os.path.join(self.tmpdir, 'RAxML_distances.one')
        self.collection._get_sequence_file()
        self.collection._get_alignment()
        self.collection._get_distances()
        self.assertTrue(os.path.exists(expected_file))

    def test_distance_parsing(self):
        """Tests storage of parsed distance"""
        self.collection._get_sequence_file()
        self.collection._get_alignment()
        self.collection._get_distances()
        self.collection._parse_distances()
        self.assertTrue(len(self.collection._dist_dict.keys()) > 0)

    def test_collection_call(self):
        """Tests that call properly executes all of the above"""
        self.collection()
        self.assertTrue(len(self.collection._dist_dict.keys()) > 0)

    def tearDown(self):
        """Remove temporary directory"""
        shutil.rmtree(self.tmpdir)
