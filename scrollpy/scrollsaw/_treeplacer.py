"""
This module contains the main TreePlacer object.
"""


from scrollpy.files import tree_file as tf
from scrollpy.files import msa_file as mf
from scrollpy.util import _tree


class TreePlacer:
    """Main TreePlacer object; based on user input, run is variable.

    Args:
        seq_dict (dict): a dictionary of mapped group/object pairs

        alignment (obj): parsed BioPython alignment object

        target_dir (str): path to target directory for output file(s)
    """

    # Class var list
    _config_vars = ('align_method', 'distance_method')

    def __init__(self, seq_dict, alignment, to_place, target_dir, **kwargs):
        # Required
        self._seq_dict  = seq_dict
        self._alignment = alignment
        self._to_place  = to_place   # Sequences to place in tree
        self.target_dir = target_dir
        # Optional vars or in config
        for var in self._config_vars:
            try:
                value = kwargs[var]
            except KeyError:
                value = config['ARGS'][var]
            setattr(self, var, value)
        # Internal defaults
        self._leafseqs = []  # Need to populate from seq_dict?
        self._starting_leaves = []  # Need to populate from seq_dict?
        self._classified = {}


    # def __repr__(self):
    #     """TO-DO"""
    #     pass


    # def __str__(self):
    #     """TO-DO"""
    #     pass


    def __call__(self):
        """Runs TreePlacer"""
        for seq_obj in self._to_place:
            # Add to existing alignemnt
            new_align_path = self._get_outpath('align')
            self._add_seq_to_alignment(new_align_path)
            # Convert to Phylip file
            new_phy_path = self._get_outpath('phylip')
            mf.afa_to_phylip(new_align_path, new_phy_path)
            # Run IQ-TREE
            new_tree_path = self._get_outpath('tree')
            self._make_tree(new_phy_path)
            # Parse tree object
            new_tree = tf.read_tree(new_tree_path)
            new_leaves = [leaf.name for leaf in new_tree
                    if not leaf.name in leaf_names]
            if len(new_leaves) > 1:
                pass  # Log something
            added_leaf = new_leaves[0]
            # Try to re-root tree
            new_tree = self._root_tree(new_tree)
            # Write new tree to output?
            # Get actual node
            added_node = new_tree&added_leaf
            # Now determine monophyly
            if not _tree.is_node_monophyletic(added_node, self.leafseqs):
                pass  # Not monophyletic
            else:
                self._classify_node()  # Look in more detail


    def _get_outpath(self, out_type):
        """Similar to other class functions - maybe this can be extrated?"""
        pass


    def _add_seq_to_alignment(self, outpath):
        """Calls MAFFT to add sequences to an existing alignment"""
        pass


    def _make_tree(self, outpath):
        """Calls IQ-TREE to construct a tree"""
        pass


    def _root_tree(self, tree_obj):
        """Randomly selects a group to root on"""
        pass


    def _classify_node(self):
        """Finds monophyly information about a node"""
        pass
