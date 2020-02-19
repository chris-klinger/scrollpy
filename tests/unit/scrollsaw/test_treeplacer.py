"""
Tests the scrollsaw/_treeplacer module.
"""

import os
import unittest
from unittest.mock import Mock
from unittest.mock import patch
from unittest.mock import mock_open
import shutil

from configparser import DuplicateSectionError

from scrollpy import config
from scrollpy import load_config_file
from scrollpy.scrollsaw._treeplacer import TreePlacer
from scrollpy.util._mapping import Mapping
from scrollpy.files import sequence_file as sf
from scrollpy.files import tree_file as tf
from scrollpy.files import align_file as af
from scrollpy import FatalScrollPyError
# from scrollpy.alignments import parser


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
        load_config_file()
        try:
            config.add_section('ARGS')
            config.add_section('ALIGNMENT')
            config.add_section('TREE')
        except DuplicateSectionError:
            pass
        # Provide defaults
        config['ARGS']['alignfmt'] = 'fasta'
        config['ARGS']['col_method'] = 'zorro'
        config['ARGS']['iter_method'] = 'hist'
        config['ARGS']['tree_method'] = 'Iqtree'
        config['ARGS']['tree_matrix'] = 'LG'
        config['ARGS']['no_clobber'] = False
        config['ARGS']['no_create'] = False
        config['ARGS']['filesep'] = '_'
        config['ARGS']['suffix'] = ''

        # Create seq_dict
        cls.align_file = os.path.join(data_dir,'Hsap_AP_EGADEZ.mfa')
        map_file = os.path.join(data_dir,'Hsap_AP_EGADEZ_mapping.txt')

        mapping = Mapping(
                [],  # Infiles
                alignfile=cls.align_file,
                mapfile=map_file,
                infmt='fasta',
                alignfmt='fasta',
                treefmt='newick',
                )
        cls.seq_dict = mapping()

        # Also parse and create seqdict
        cls.seqs_to_place = os.path.join(data_dir,'Hsap_AP_GA_renamed.fa')
        # cls.seqs_to_place = sf._get_sequences(seq_file)

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
                infiles = [],
                # Start of kwargs
                align_method='Mafft',
                tree_method='Iqtree',
                tree_matrix='LG',
                support=90,
                )

    def tearDown(self):
        """Remove temporary directory"""
        shutil.rmtree(self.tmpdir)

    def test_repr(self):
        """Tests the TreePlacer classes' __repr__ method"""
        expected = "TreePlacer({!r}, {!r}, {!r}, {!r}, [], **{})".format(
                self.placer._seq_dict,
                self.placer._alignment,
                self.placer._to_place,
                self.placer._outdir,
                self.placer.kwargs,
                )
        self.assertEqual(expected, repr(self.placer))

    def test_str(self):
        """Tests the TreePlacer classes' __str__ method"""
        expected = "TreePlacer using Mafft for alignment and Iqtree for "\
                "phylogeny reconstruction"
        self.assertEqual(expected, str(self.placer))

    @patch('scrollpy.scrollsaw._treeplacer.console_logger')
    @patch('scrollpy.scrollsaw._treeplacer.status_logger')
    @patch('scrollpy.scrollsaw._treeplacer.BraceMessage')
    @patch('scrollpy.util._logging.log_newlines')
    @patch('scrollpy.util._logging.log_message')
    @patch('scrollpy.util._tree.is_node_monophyletic')
    @patch('scrollpy.scrollsaw._treeplacer.tempfile.TemporaryDirectory')
    @patch.object(TreePlacer, '_add_classified_seq')
    @patch.object(TreePlacer, '_classify_monophyletic_node')
    @patch.object(TreePlacer, '_classify_node')
    @patch.object(TreePlacer, '_root_tree')
    @patch.object(TreePlacer, '_get_added_leaf')
    @patch.object(TreePlacer, '_update_tree_mappings')
    @patch.object(TreePlacer, '_make_new_files')
    def test_call(self, mock_nf, mock_tmap, mock_gaddl, mock_rt, mock_cnode,
            mock_cmnode, mock_addcs, mock_tmp, mock_ismono, mock_log,
            mock_lnew, mock_bmsg, mock_sl, mock_cl):
        """Tests the TreePlacer classes' __call__ method"""
        mock_bmsg.return_value = "Mock Message"
        # Test first under normal circumstances
        # Check for non-monophyletic nodes first
        mock_ismono.return_value = False
        self.placer()
        # Check all assert statements
        mock_bmsg.assert_any_call(
                "Placing sequence number {} of {}", 1, 2)
        mock_bmsg.assert_any_call(
                "Placing sequence number {} of {}", 2, 2)
        mock_log.assert_any_call(
                "Mock Message",
                3,
                'INFO',
                mock_sl,
                )
        mock_nf.assert_any_call(self.placer._to_place[0])
        mock_nf.assert_any_call(self.placer._to_place[1])
        mock_tmap.assert_any_call()
        mock_gaddl.assert_any_call()
        mock_rt.assert_called()
        mock_ismono.assert_called()
        mock_cnode.assert_called()
        mock_cmnode.assert_not_called()
        mock_addcs.assert_not_called()
        mock_lnew.assert_called_once_with(mock_cl)
        # Change to non-mono nodes
        mock_ismono.return_value = True
        mock_cmnode.return_value = ('_','_')
        self.placer()
        # Just check new assertions
        mock_cmnode.assert_called()
        mock_addcs.assert_called()
        # Finally, check quick for tmpdir
        self.placer._outdir = None
        self.placer()
        mock_tmp.assert_called_once()

    @patch('scrollpy.scrollsaw._treeplacer.file_logger')
    @patch('scrollpy.scrollsaw._treeplacer.console_logger')
    @patch('scrollpy.scrollsaw._treeplacer.BraceMessage')
    @patch('scrollpy.util._logging.log_message')
    @patch('scrollpy.scrollsaw._treeplacer.sf.seqfile_to_scrollseqs')
    def test_parse_sequences(self, mock_sf, mock_log, mock_bmsg, mock_cl, mock_fl):
        """Tests the _parse_sequences method"""
        mock_bmsg.return_value = "Mock Message"
        # Test easy case first
        self.placer._parse_sequences(self.seqs_to_place)
        mock_log.assert_not_called()
        # Throw an error
        test_exc = Exception()
        mock_sf.side_effect = test_exc
        with self.assertRaises(FatalScrollPyError):
            self.placer._parse_sequences(self.seqs_to_place)
        mock_bmsg.assert_called_once_with(
                "Failed to parse sequences for tree placing")
        mock_log.assert_called_once_with(
                "Mock Message",
                1,
                'ERROR',
                mock_cl, mock_fl,
                exc_obj=test_exc,
                )

    def test_return_classified_seqs(self):
        """Tests the return_classified_seqs method"""
        self.placer._classified = 'Classified'
        self.assertEqual('Classified', self.placer.return_classified_seqs())

    @patch('scrollpy.scrollsaw._treeplacer.af.afa_to_phylip')
    @patch.object(TreePlacer, '_make_tree')
    @patch.object(TreePlacer, '_add_seq_to_alignment')
    def test_make_new_files(self, mock_adds, mock_mt, mock_atp):
        """Tests the _make_new_files method"""
        test_seq = self.placer._to_place[0]
        expected_seq_name   = 'Hsap_AP1G_NP_001025178.1.fa'
        expected_align_name = 'Hsap_AP1G_NP_001025178.1.afa'
        expected_phy_name   = 'Hsap_AP1G_NP_001025178.1.phy'
        expected_tree_name  = 'Hsap_AP1G_NP_001025178.1.phy.contree'
        # Create the expected paths
        # Sequence name first
        expected_seq_path = os.path.join(
                self.tmpdir,
                expected_seq_name,
                )
        # Alignment next
        expected_align_path = os.path.join(
                self.tmpdir,
                expected_align_name,
                )
        # Phylip next
        expected_phy_path = os.path.join(
                self.tmpdir,
                expected_phy_name,
                )
        # Tree last
        expected_tree_path = os.path.join(
                self.tmpdir,
                expected_tree_name,
                )
        # Now run and check the instance values
        self.placer._make_new_files(test_seq)
        # Check instance values
        self.assertEqual(self.placer._current_seq_path, expected_seq_path)
        self.assertEqual(self.placer._current_align_path, expected_align_path)
        self.assertEqual(self.placer._current_phy_path, expected_phy_path)
        self.assertEqual(self.placer._current_tree_path, expected_tree_path)
        # Assert function calls
        mock_adds.assert_called_once()
        mock_atp.assert_called_once()
        mock_mt.assert_called_once()

    @patch('scrollpy.scrollsaw._treeplacer.Aligner')
    def test_add_seq_to_alignment(self, mock_aligner):
        """Tests the _add_seq_to_alignment method"""
        config['ALIGNMENT']['Mafft'] = 'path/to/mafft'
        test_seq = Mock()
        self.placer._current_seq_path = 'test/seq/path'
        self.placer._current_align_path = 'test/align/path'
        with patch('scrollpy.scrollsaw._treeplacer.open', mock_open()) as mo:
            self.placer._add_seq_to_alignment(test_seq)
        # Assert some calls
        mo.assert_called_once_with('test/seq/path','w')
        mock_aligner.assert_called_once_with(
                'MafftAdd',
                'path/to/mafft',  # Cmd
                inpath = 'test/seq/path',
                outpath = 'test/align/path',
                cmd_list = [
                    '--add',
                    self.placer._current_seq_path,
                    '--keeplength',
                    '--thread',
                    '-1',
                    self.placer._alignment,
                    ],
                )

    @patch('scrollpy.scrollsaw._treeplacer.TreeBuilder')
    def test_add_seq_to_alignment(self, mock_builder):
        """Tests the _make_tree method"""
        config['TREE']['Iqtree'] = 'path/to/iqtree'
        self.placer._current_phy_path = 'test/phy/path'
        self.placer._current_tree_path = 'test/tree/path'
        # Run and test assertions
        self.placer._make_tree()
        mock_builder.assert_called_once_with(
                'Iqtree',
                'path/to/iqtree',  # Cmd
                inpath = 'test/phy/path',
                outpath = 'test/tree/path',
                cmd_list = [
                    '-nt',
                    'AUTO',
                    '-s',
                    self.placer._current_phy_path,
                    '-m',
                    self.placer.tree_matrix,
                    '-bb',
                    '1000',
                    ],
                )

    @patch('scrollpy.util._util.flatten_dict_to_list')
    @patch('scrollpy.scrollsaw._treeplacer.Mapping')
    def test_update_tree_mappings(self, mock_map, mock_dtl):
        """Tests the _update_tree_mappings method"""
        # Mock some sequences
        oseq1 = Mock(**{'description':'seq1', '_group':'group1'})
        oseq2 = Mock(**{'description':'seq2', '_group':'group1'})
        oseq3 = Mock(**{'description':'seq3', '_group':'group2'})
        nseq1 = Mock(**{'description':'seq1'})
        nseq2 = Mock(**{'description':'seq2'})
        nseq3 = Mock(**{'description':'seq3'})
        nseq4 = Mock(**{'description':'seq4'})
        # Set the return values
        mock_slist = [oseq1, oseq2, oseq3]
        mock_tlist = [nseq1, nseq2, nseq3, nseq4]
        mock_dtl.side_effect = [mock_slist, mock_tlist]
        # Call it
        self.placer._update_tree_mappings()
        # Check the new dict
        expected_dict = {
                'group1' : [nseq1, nseq2],
                'group2' : [nseq3],
                }
        self.assertEqual(expected_dict, self.placer._leafseq_dict)

    @patch('scrollpy.scrollsaw._treeplacer.file_logger')
    @patch('scrollpy.scrollsaw._treeplacer.console_logger')
    @patch('scrollpy.scrollsaw._treeplacer.BraceMessage')
    @patch('scrollpy.util._logging.log_message')
    def test_get_added_leaf(self, mock_log, mock_bmsg, mock_cl, mock_fl):
        """Tests the _get_added_leaf method"""
        mock_bmsg.return_value = "Mock Message"
        # Can mock some sequences
        leaf1 = Mock()
        leaf1.configure_mock(**{'name' : 'leaf1'})
        leaf2 = Mock()
        leaf2.configure_mock(**{'name' : 'leaf2'})
        leaf3 = Mock()
        leaf3.configure_mock(**{'name' : 'leaf3'})
        leaf4 = Mock()
        leaf4.configure_mock(**{'name' : 'leaf4'})
        # Mock tree object as a list of leaves
        self.placer._current_tree_obj = [leaf1, leaf2, leaf3, leaf4]
        self.placer._original_leaves = ['leaf1', 'leaf2', 'leaf3']
        # Now check
        self.assertEqual('leaf4', self.placer._get_added_leaf())
        # Check when the result is expected as a failure
        self.placer._original_leaves = ['leaf1', 'leaf2']
        with self.assertRaises(FatalScrollPyError):
            self.placer._get_added_leaf()
        # Check assertions
        mock_bmsg.assert_called_once_with(
                "Detected more than one added sequence")
        mock_log.assert_called_once_with(
                "Mock Message",
                1,
                'ERROR',
                mock_cl, mock_fl,
                )

    @patch('scrollpy.scrollsaw._treeplacer._tree.get_group_outgroup')
    def test_root_tree(self, mock_group):
        """Tests the _root_tree method"""
        lseq1 = Mock(**{'_node' : 'node1'})
        lseq2 = Mock(**{'_node' : 'node2'})
        lseq3 = Mock(**{'_node' : 'node3'})
        lseq4 = Mock(**{'_node' : 'node4'})
        lseq5 = Mock(**{'_node' : 'node5'})
        self.placer._leafseq_dict = {
                'group1' : [lseq1, lseq2],
                'group2' : [lseq3, lseq4, lseq5],
                }
        # Test with appropriate call
        mock_group.side_effect = [False, True]
        test_leaf = 'test_leaf'
        mock_tobj = Mock()
        self.placer._current_tree_obj = mock_tobj
        self.placer._root_tree(test_leaf)
        # Now test assertions
        mock_group.assert_any_call(
                mock_tobj,
                'test_leaf',
                ['node1', 'node2'],
                )
        mock_group.assert_any_call(
                mock_tobj,
                'test_leaf',
                ['node3', 'node4', 'node5'],
                )
        mock_tobj.set_outgroup.assert_called_once_with(True)

    @patch('scrollpy.scrollsaw._treeplacer._tree.is_complete_group')
    @patch('scrollpy.scrollsaw._treeplacer._tree.is_node_monophyletic')
    @patch('scrollpy.scrollsaw._treeplacer._tree.get_node_groups')
    def test_classify_node(self, mock_ggroups, mock_ismono, mock_iscom):
        """Tests the _classify_node method"""
        mock_node = Mock(**{'support' : 90})
        test_node1 = Mock(**{'support' : 70})
        test_node2 = Mock(**{'support' : 80})
        mock_node.traverse.return_value = [test_node1, test_node2]
        mock_ggroups.side_effect = [
                ['group1', 'group2', 'group3'], ['group1'], ['group2']]
        self.placer._leafseq_dict = {
                'group1' : [Mock(), Mock()],
                'group2' : [Mock(), Mock(), Mock()],
                }
        mock_ismono.side_effect = [True, True]
        mock_iscom.side_effect = [True, False]
        # Run and test
        self.assertEqual(
                [90, 3, 'group1', 70, 'Group is complete',
                    'group2', 80, 'Group is incomplete'],
                self.placer._classify_node(mock_node),
                )

    # @patch('scrollpy.scrollsaw._treeplacer._tree.is_complete_group')
    # @patch('scrollpy.scrollsaw._treeplacer._tree.is_node_monophyletic')
    # @patch('scrollpy.scrollsaw._treeplacer._tree.get_node_groups')
    # def test_classify_monophyletic_node(self, mock_ggroups, mock_ismono, mock_iscom):
    #     """Tests the _classify_monophyletic_node method"""
    #     mock_node = Mock(**{'support' : 90})
    #     mock_ggroups.return_value =

    def test_add_classified_seq(self):
        """Tests the _add_classified_seq method"""
        test_seq1 = Mock()
        test_seq2 = Mock()
        test_seq3 = Mock()
        # Test adding one sequence
        expected = {'group1' : [test_seq1]}
        self.placer._add_classified_seq('group1', test_seq1)
        self.assertEqual(expected, self.placer._classified)
        # Test adding two sequences
        expected = {'group1':[test_seq1], 'group2':[test_seq2]}
        self.placer._add_classified_seq('group2', test_seq2)
        self.assertEqual(expected, self.placer._classified)
        # Test adding three sequences
        expected = {'group1':[test_seq1, test_seq3], 'group2':[test_seq2]}
        self.placer._add_classified_seq('group1', test_seq3)
        self.assertEqual(expected, self.placer._classified)
