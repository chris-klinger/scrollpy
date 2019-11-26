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
from scrollpy.files import tree_file as tf
from scrollpy.files import msa_file as mf
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
        expected_seq_name   = 'Hsap_AP1G_NP_001025178.1.fa'
        expected_align_name = 'Hsap_AP1G_NP_001025178.1.mfa'
        expected_phy_name   = 'Hsap_AP1G_NP_001025178.1.phy'
        expected_tree_name  = 'Hsap_AP1G_NP_001025178.1.phy.contree'
        # Run tests
        # Sequence name first
        expected_seq_path = os.path.join(
                self.tmpdir,
                expected_seq_name,
                )
        self.assertEqual(self.placer._get_outpath(test_seq,'seq'),
                expected_seq_path)
        # Alignment next
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


    @unittest.skip('Skip for time constraints')
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


    @unittest.skip('Skip for time constraints')
    def test_make_tree(self):
        """Tests making a tree"""
        # Populate necessary attributes
        test_seq = self.placer._to_place[0]
        self.placer._current_seq_path = self.placer._get_outpath(
                test_seq,'seq')
        self.placer._current_align_path = self.placer._get_outpath(
                test_seq,'align')
        # Make alignment
        self.placer._add_seq_to_alignment(test_seq)
        self.placer._current_phy_path = self.placer._get_outpath(
                test_seq,'phylip')
        # Convert to phylip
        mf.afa_to_phylip(
                self.placer._current_align_path,
                self.placer._current_phy_path,
                )
        self.placer._current_tree_path = self.placer._get_outpath(
                test_seq,'tree')
        # Try to make tree
        self.placer._make_tree()
        # Read the tree
        tree = tf.read_tree(
                self.placer._current_tree_path,
                'newick',
                )
        leaves = [leaf.name for leaf in tree]
        self.assertTrue(test_seq.name in leaves)


    @unittest.skip('')
    def test_read_current_tree(self):
        """Tests parsing a pre-made tree"""
        # Set up
        test_seq = self.placer._to_place[0]
        tree_path = os.path.join(
                data_dir,
                'Hsap_AP1G_NP_001025178.1.phy.contree',
                )
        # Parse tree
        self.placer._current_tree_path = tree_path
        self.placer._read_current_tree()
        # Actual test
        leaves = [leaf.name for leaf in self.placer._current_tree_obj]
        self.assertTrue(test_seq.name in leaves)


    def test_update_tree_mapping(self):
        """Tests populating the object for a given object"""
        # Set up
        test_seq = self.placer._to_place[0]
        tree_path = os.path.join(
                data_dir,
                'Hsap_AP1G_NP_001025178.1.phy.contree',
                )
        self.placer._current_tree_path = tree_path
        # Run the actual method
        self.placer._update_tree_mappings()
        # Test
        self.assertTrue(test_seq.name not in self.placer._original_leaves)


    def test_get_added_leaf(self):
        """Tests checking for an added leaf"""
        # Set up
        test_seq = self.placer._to_place[0]
        tree_path = os.path.join(
                data_dir,
                'Hsap_AP1G_NP_001025178.1.phy.contree',
                )
        self.placer._current_tree_path = tree_path
        self.placer._update_tree_mappings()
        # Test
        self.assertEqual(
                self.placer._get_added_leaf(),
                test_seq.name,
                )


    def test_root_tree(self):
        """Tests rooting a tree"""
        # Set up
        test_seq = self.placer._to_place[0]
        tree_path = os.path.join(
                data_dir,
                'Hsap_AP1G_NP_001025178.1.phy.contree',
                )
        self.placer._current_tree_path = tree_path
        self.placer._update_tree_mappings()
        # Run the method
        added_leaf = test_seq.name
        self.placer._root_tree(added_leaf)
        # Get the tree structure
        all_leaves = [leaf for leaf in self.placer._current_tree_obj]
        root = self.placer._current_tree_obj.get_common_ancestor(all_leaves)
        # Check the left side of root
        left = root.children[0]
        left_names = ['NP_003929.4','NP_031373.2','NP_055670.1']
        self.assertEqual(([leaf.name for leaf in left]),left_names)
        # Check the right side of root
        right = root.children[1]
        right_names = ['NP_001229766.1','NP_001025178.1','Hsap_AP1G_NP_001025178.1']
        self.assertEqual(([leaf.name for leaf in right]),right_names)


    def test_classify_node(self):
        """Tests getting information about non-monophyletic nodes"""
        # Set up
        # Set up
        test_seq = self.placer._to_place[0]
        tree_path = os.path.join(
                data_dir,
                'Hsap_AP1G_NP_001025178.1.phy.contree',
                )
        self.placer._current_tree_path = tree_path
        self.placer._update_tree_mappings()
        # Re-root tree
        added_leaf = test_seq.name
        self.placer._root_tree(added_leaf)
        # Change group for one node
        old_list = self.placer._leafseq_dict['group1']
        for leafseq in old_list:
            if leafseq.name == 'NP_055670.1':
                leafseq._group = 'group4'
                old_list.remove(leafseq)
            self.placer._leafseq_dict['group4'] = [leafseq]
            self.placer._leafseq_dict['group1'] = old_list
        # Get common ancestor of non-monophyletic node
        test = self.placer._current_tree_obj&"NP_003929.4"
        test_node = test.up
        # Now get info
        info = self.placer._classify_node(test_node)
        expected = [
                75.0,                  # Starting node support
                2,                     # Number of groups under start node
                'group1',              # First group name
                1.0,                   # First group support (monophyletic)
                'Group is incomplete', # Group complete?
                'group4',              # As above, but for second group
                1.0,
                'Group is complete',
                ]
        self.assertEqual(info,expected)


    def test_classify_monophyletic_node(self):
        """Tests getting information about monophyletic nodes"""
        # Set up
        test_seq = self.placer._to_place[0]
        tree_path = os.path.join(
                data_dir,
                'Hsap_AP1G_NP_001025178.1.phy.contree',
                )
        self.placer._current_tree_path = tree_path
        self.placer._update_tree_mappings()
        # Re-root tree
        added_leaf = test_seq.name
        self.placer._root_tree(added_leaf)
        # Get information
        added_node = self.placer._current_tree_obj&added_leaf
        first_ancestor = added_node.up
        info = self.placer._classify_monophyletic_node(first_ancestor)
        # Check information
        expected = [
                'group2',                # Starting node group
                100.0,                   # Starting node support
                'Same node',             # Whether last ancestral is same as starting
                'NA',                    # Last ancestral support (if different)
                'Group is complete',     # Whether all group members present
                'Possible Positive Hit', # Support >= threshold?
                ]
        self.assertEqual(info,expected)

