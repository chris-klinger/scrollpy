"""
Tests the scrollsaw/_treeplacer module.
"""

import os
import unittest
import shutil


from scrollpy import config
from scrollpy import load_config_file
from scrollpy.scrollsaw._treeplacer import TreePlacer
from scrollpy.util._mapping import Mapping
from scrollpy.files import sequence_file as sf
from scrollpy.alignments import parser


cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
# cleaner to use realpath due to relative path
data_dir = os.path.realpath(os.path.join(cur_dir, '../../fixtures')) # /tests/


class TestTreePlacerAlignOnly(unittest.TestCase):
    """Tests the TreePlacer class when the starting seq_dict is created
    only from an alignment and a mapping file.

    """

    @classmethod
    def setUpClass(cls):
        """Create the initial mapping just once"""
        # Create seq_dict
        cls.align_file = os.path.join(data_dir,'Hsap_AP_EGADEZ.mfa')
        map_file = os.path.join(data_dir,'Hsap_AP_EGADEZ_mapping.txt')

        mapping = Mapping(
                alignfile=cls.align_file,
                mapfile=map_file,
                infmt='fasta',
                alignfmt='fasta',
                treefmt='newick',
                )
        cls.seq_dict = mapping()

        # Also parse and create seqdict
        seq_file = os.path.join(data_dir,'Hsap_AP_GA_renamed.fa')
        cls.seqs_to_place = sf._get_sequences(seq_file)

        # Load config to get access to paths
        load_config_file()


    def setUp(self):
        """Create an identical instance for each test"""
        # Create a new temporary directory on each run
        self.tmpdir = os.path.join(data_dir,'placer_tmp')
        try:
            os.makedirs(self.tmpdir)
        except FileExistsError:
            pass  # tmpdir still present

        self.placer = TreePlacer(
                self.seq_dict,
                self.align_file,  # Just need file handle
                self.seqs_to_place,
                self.tmpdir,
                # Start of kwargs
                align_method='Mafft',
                tree_method='Iqtree',
                tree_matrix='LG',
                support=90,
                )


    def tearDown(self):
        """Remove temporary directory"""
        shutil.rmtree(self.tmpdir)


    def test_get_outpath(self):
        """Tests the _get_outpath method"""
        test_seq = self.placer._to_place[0]
        expected_align_name = 'Hsap_AP1G_NP_001025178.1.mfa'
        expected_phy_name = 'Hsap_AP1G_NP_001025178.1.phy'
        expected_tree_name = 'Hsap_AP1G_NP_001025178.1.tre'
        # Run tests
        # Alignment name first
        expected_align_path = os.path.join(
                self.tmpdir,
                expected_align_name,
                )
        self.assertEqual(self.placer._get_outpath(test_seq,'align'),
                expected_align_path)
        # Phylip next
        expected_phy_path = os.path.join(
                self.tmpdir,
                expected_phy_name,
                )
        self.assertEqual(self.placer._get_outpath(test_seq,'phylip'),
                expected_phy_path)
        # Tree last
        expected_tree_path = os.path.join(
                self.tmpdir,
                expected_tree_name,
                )
        self.assertEqual(self.placer._get_outpath(test_seq,'tree'),
                expected_tree_path)


    def test_add_seq_to_alignment(self):
        """Tests that a seq_obj is properly added to the alignment"""
        # Populate necessary attributes
        test_seq = self.placer._to_place[0]
        self.placer._current_seq_path = self.placer._get_outpath(
                test_seq,'seq')
        self.placer._current_align_path = self.placer._get_outpath(
                test_seq,'align')
        # Run alignment
        self.placer._add_seq_to_alignment(test_seq)
        parsed = parser.parse_alignment_file(
                self.placer._current_align_path,
                'fasta',
                )
        # 'parsed' is a dict
        self.assertEqual(len(parsed.keys()),6)
        self.assertTrue(test_seq.name in parsed.keys())


    def test_make_tree(self):
        pass


    def test_read_current_tree(self):
        pass


    def test_update_tree_mapping(self):
        pass


    def test_get_added_leaf(self):
        pass


    def test_root_tree(self):
        pass


    def test_classify_node(self):
        pass


    def test_classify_monophyletic_node(self):
        pass

