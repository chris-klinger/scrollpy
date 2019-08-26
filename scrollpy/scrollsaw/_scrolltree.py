"""
This module contains the main ScrollTree object
"""

from scrollpy.files import sequence_file as sf


class ScrollTree:
    """Main ScrollTree object to filter based on branch length.

    Args:
        seq_dict (dict): if provided, a data structure mapping LeafSeq
            objects to distinct groups..
    """

    def __init__(self, seq_dict, **kwargs):
        self._seq_dict = seq_dict
        # Internal defaults
        self._ordered_seqs = []
        self._cached = {}  # For faster leaf distance lookup


    #def __str__(self):
    #    pass  # TO-DO


    #def __repr__(self):
    #    pass  # TO-DO


    def __call__(self):
        """Runs tree-based ScrollSaw"""
        # Calculate distances for each group in mapping
        leaves = sf._cat_sequence_lists(self._seq_dict.values())
        self._get_all_pairwise_distances(leaves)
        # Sort distances
        self._sort_distances()


    def _get_all_pairwise_distances(self, leaves):
        """Calculates all pairwise distances from each leaf to each other leaf
        and updates the internal LeafSeq distance attribute for each
        """
        for leaf in leaves:
            other_leaves = leaves[:].remove(leaf)
            for oleaf in other_leaves:
                search_string = "{}.{}".format(*tuple(
                    sorted([leaf.name, oleaf.name])))  # Sort so bi-directional dist works
                try:
                    dist = self._cached[search_string]  # Try fast lookup
                except KeyError:
                    dist = leaf.get_distance(oleaf)  # Else, calculate and store
                    cached[search_string] = dist
                leaf._distance += dist


    def _sort_distances(self):
        """Populates internal list with <group><header><dist> tuples"""
        all_seqs = []
        for k,v in self._seq_dict.items():
            all_seqs.extend(v)
        self._ordered_seqs = sorted(all_seqs)



"""
Pseudo-code

initialize an object with a mapping and a tree file
    somehow have to make sure that the mapping file matches the treefile?!
    -could allow partial matches or enforce strict
        -strict could mean that all tree labels are required to be present in
        the mapping or that an exact one-to-one match is required?

if sequence file(s) were included, try to map tip labels to sequence objects
    -here, it really should be the case that a one-to-one relationship is
    required

using the mapping, go through each group and calculate pairwise tree distances
for all members using a cached tree. Update internal "removed" dict based on
this.
"""


