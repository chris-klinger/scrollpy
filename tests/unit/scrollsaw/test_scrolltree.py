"""
This module tests the main ScrollTree class.
"""

import os
import unittest
from unittest.mock import Mock
from unittest.mock import patch


from scrollpy.scrollsaw._scrolltree import ScrollTree
from scrollpy.util import _mapping


cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
# cleaner to use realpath due to relative path
data_dir = os.path.realpath(os.path.join(cur_dir, '../../fixtures')) # /tests/


class TestScrollTree(unittest.TestCase):
    """Tests main function -> tree-based distance metric"""

    @classmethod
    def setUpClass(cls):
        """Get an instance"""
        mock_seq1 = Mock(**{'_distance' : 0})
        mock_seq1._node.name = 'seq1'
        mock_seq1.get_distance.return_value = 1
        mock_seq2 = Mock(**{'_distance' : 0})
        mock_seq2._node.name = 'seq2'
        mock_seq2.get_distance.return_value = 2
        mock_seq3 = Mock(**{'_distance' : 0})
        mock_seq3._node.name = 'seq3'
        mock_seq3.get_distance.return_value = 3
        cls.test_sdict = {
                'group1' : [mock_seq1, mock_seq2],
                'group2' : [mock_seq3],
                }

        cls.stree = ScrollTree(cls.test_sdict)

    def test_repr(self):
        """Tests the ScrollTree classes' __repr__ method"""
        expected = "ScrollTree({!r}, **{!r})".format(
                self.stree._seq_dict, self.stree.kwargs)
        self.assertEqual(expected, repr(self.stree))

    def test_str(self):
        """Tests the ScrollTree classes' __str__ method"""
        expected = "ScrollTree object with 2 groups and 3 sequences"
        self.assertEqual(expected, str(self.stree))

    @patch('scrollpy.scrollsaw._scrolltree.sf._cat_sequence_lists')
    @patch.object(ScrollTree, '_sort_distances')
    @patch.object(ScrollTree, '_get_all_pairwise_distances')
    def test_call(self, mock_gdists, mock_sdists, mock_cat):
        """Tests the ScrollTree classes' __call__ method"""
        # Run call
        self.stree()
        # Check assertions
        mock_gdists.assert_called_once()
        mock_sdists.assert_called_once()
        mock_cat.assert_called_once()

    @patch('scrollpy.scrollsaw._scrolltree.file_logger')
    @patch('scrollpy.scrollsaw._scrolltree.console_logger')
    @patch('scrollpy.scrollsaw._scrolltree.BraceMessage')
    @patch('scrollpy.util._logging.log_message')
    def test_get_all_pairwise_distances(self, mock_log, mock_bmsg, mock_cl, mock_fl):
        """Tests the ScrollTree classes' _get_all_pairwise_distances method"""
        mock_bmsg.return_value = "Mock Message"
        test_leaves = []
        for sublist in self.test_sdict.values():
            for leaf in sublist:
                test_leaves.append(leaf)
        self.stree._get_all_pairwise_distances(test_leaves)
        # Test assertions
        mock_bmsg.assert_called_once_with(
                "Calculating pairwise distances between all tree leaves")
        mock_log.assert_called_once_with(
                "Mock Message",
                2,
                'INFO',
                mock_cl, mock_fl,
                )
        expected = {'seq1.seq2': 1, 'seq1.seq3': 1, 'seq2.seq3': 2}
        self.assertEqual(expected, self.stree._cached)

    # No need to test _sort_distances -> same as for ScrollPy object

    # def test_call(self):
    #     """Run the object and check internal values"""
    #     self.stree()
    #     # Expected values
    #     expected_dict = {
    #             'NP_001025178.1' : 16.0,
    #             'NP_001229766.1' : 16.0,
    #             'NP_003929.4'    : 14.0,
    #             'NP_031373.2'    : 15.0,
    #             'NP_055670.1'    : 15.0,
    #             }
    #     expected_order = [
    #             'NP_003929.4','NP_031373.2','NP_055670.1',
    #             'NP_001025178.1','NP_001229766.1',
    #             ]
    #     # Check the LeafSeq objects themselves first
    #     leaf_dict = self.stree._seq_dict
    #     actual_dict = {}
    #     for k,leafseqs in leaf_dict.items():
    #         for leafseq in leafseqs:
    #             name = leafseq._node.name
    #             dist = leafseq._distance
    #             actual_dict[name] = dist
    #     self.assertEqual(actual_dict,expected_dict)
    #     # Check that order is as expected
    #     actual_order = [leafseq.name for leafseq in self.stree._ordered_seqs]
    #     self.assertEqual(actual_order,expected_order)
