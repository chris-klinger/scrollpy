"""
This module tests the main ScrollTree class.
"""

import os
import unittest


from scrollpy.scrollsaw._scrolltree import ScrollTree
from scrollpy.util import _mapping


cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
# cleaner to use realpath due to relative path
data_dir = os.path.realpath(os.path.join(cur_dir, '../../fixtures')) # /tests/


class TestScrollTree(unittest.TestCase):
    """Tests main function -> tree-based distance metric"""

    def setUp(self):
        """Creates Mapping and ScrollTree objects"""
        tree_file = os.path.join(data_dir,'Hsap_AP_EGADEZ_symmetric.tre')

        mapping = _mapping.Mapping(
                treefile=tree_file,
                infmt='fasta',  # Not necessary
                treefmt='newick',
                )
        # Create the seq_dict from mapping
        seq_dict = mapping()

        self.stree = ScrollTree(seq_dict)


    def test_call(self):
        """Run the object and check internal values"""
        self.stree()
        # Expected values
        expected_dict = {
                'NP_001025178.1' : 16.0,
                'NP_001229766.1' : 16.0,
                'NP_003929.4'    : 14.0,
                'NP_031373.2'    : 15.0,
                'NP_055670.1'    : 15.0,
                }
        expected_order = [
                'NP_003929.4','NP_031373.2','NP_055670.1',
                'NP_001025178.1','NP_001229766.1',
                ]
        # Check the LeafSeq objects themselves first
        leaf_dict = self.stree._seq_dict
        actual_dict = {}
        for k,leafseqs in leaf_dict.items():
            for leafseq in leafseqs:
                name = leafseq._node.name
                dist = leafseq._distance
                actual_dict[name] = dist
        self.assertEqual(actual_dict,expected_dict)
        # Check that order is as expected
        actual_order = [leafseq.name for leafseq in self.stree._ordered_seqs]
        self.assertEqual(actual_order,expected_order)
