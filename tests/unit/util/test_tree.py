"""
Tests /util/_tree
"""

import os
import unittest


from scrollpy.files import tree_file as tf
from scrollpy.util._mapping import Mapping
from scrollpy.util import _tree


cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
# cleaner to use realpath due to relative path
data_dir = os.path.realpath(os.path.join(cur_dir, '../../fixtures')) # /tests/


class TestTreeModule(unittest.TestCase):
    """Tests utility Tree functions with LeafSeq objects"""

    @classmethod
    def setUpClass(cls):
        """Creates the necessary mapping"""
        tree_file = os.path.join(
                data_dir,'Hsap_AP_EGADEZ_symmetric.tre')
        map_file  = os.path.join(
                data_dir,'Hsap_AP_EGADEZ_mapping.txt')

        # Get tree object
        cls.tree = tf.read_tree(tree_file,'newick')
        # Get seq_dict
        mapping = Mapping(
                treefile=tree_file,
                mapfile=map_file,
                infmt='fasta',  # Not needed
                treefmt='newick',
                )
        seq_dict = mapping()
        # Flatten into a list
        cls.leafseq_list = []
        for _,leaves in seq_dict.items():
            cls.leafseq_list.extend(leaves)


    def test_get_node_groups(self):
        """Tests that the function returns properly"""
        target_nodes = [
                'NP_003929.4','NP_031373.2','NP_055670.1',
                ]
        test_node = self.tree.get_common_ancestor(target_nodes)
        # Check node groups
        groups = _tree.get_node_groups(
                test_node,
                self.leafseq_list,
                )
        self.assertEqual(len(groups),1)
        self.assertEqual(('group1' in groups),True)


    def test_node_monophyly(self):
        """Tests that the function returns properly"""
        target_nodes = [
                'NP_003929.4','NP_031373.2','NP_055670.1',
                ]
        test_node = self.tree.get_common_ancestor(target_nodes)
        # Check node groups
        monophyletic = _tree.is_node_monophyletic(
                test_node,
                self.leafseq_list,
                )
        self.assertEqual(monophyletic,True)


    def test_last_monophyletic_ancestor(self):
        """Tests that the node retrieved is monophyletic"""
        expected_children = [
                'NP_003929.4','NP_031373.2','NP_055670.1',
                ]
        test_node = self.tree&"NP_003929.4"
        last_monophyletic = _tree.last_monophyletic_ancestor(
                test_node,
                self.leafseq_list,
                )
        actual_children = [node.name for node in last_monophyletic]
        self.assertEqual(expected_children,actual_children)


    def test_get_group_outgroup(self):
        """Tests that re-rooting works correctly"""
        # Target to actually search for
        target_leaf = 'NP_031373.2'
        # Nodes to at as the 'outgroup'
        group_names = ['NP_001025178.1','NP_001229766.1']
        # Test with both TreeNode and LeafSeq objects
        group_nodes = [self.tree&name for name in group_names]
        # For LeafSeq objects, have to retrieve actual _node attr!!!
        leafseq_nodes = [leafseq._node for leafseq in self.leafseq_list
                if leafseq.name in group_names]
        # # Actually run
        node_root = _tree.get_group_outgroup(
                self.tree,
                target_leaf,
                group_nodes,
                )
        leafseq_root = _tree.get_group_outgroup(
                self.tree,
                target_leaf,
                leafseq_nodes,
                )
        # Get children
        node_root_children = [leaf.name for leaf in node_root]
        leafseq_root_children = [leaf.name for leaf in leafseq_root]
        # Now test equality
        self.assertEqual(group_names,node_root_children)
        self.assertEqual(group_names,leafseq_root_children)

