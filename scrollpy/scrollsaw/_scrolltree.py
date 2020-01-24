"""
This module contains the main ScrollTree object
"""

from scrollpy import scroll_log
from scrollpy.files import sequence_file as sf


# Get module loggers
(console_logger, status_logger, file_logger, output_logger) = \
        scroll_log.get_module_loggers(__name__)


class ScrollTree:
    """Main ScrollTree object to filter based on branch length.

    Args:
        seq_dict (dict): if provided, a data structure mapping LeafSeq
            objects to distinct groups..
    """

    def __init__(self, seq_dict, **kwargs):
        self._seq_dict = seq_dict
        # Save kwargs for __repr__
        self.kwargs = kwargs
        # Internal defaults
        self._ordered_seqs = []
        self._cached = {}  # For faster leaf distance lookup


    def __repr__(self):
        return "{}({!r}, **{!r})".format(
                self.__class__.__name__,
                self._seq_dict,
                self.kwargs,
                )

    def __str__(self):
        num_groups = len(self._seq_dict.keys())
        # Each group in self._seq_dict is a list of ScrollSeq objects
        # _seq.dict.values() returns a list of lists, which chain flattens
        num_seqs = len(list(chain(*self._seq_dict.values())))
        # Return dimensions of ScrollPy
        return "{} object with {} groups and {} sequences".format(
                self.__class__.__name__,
                num_groups,
                num_seqs,
                )


    def __call__(self):
        """Runs tree-based ScrollSaw"""
        # Calculate distances for each group in mapping
        leaves = sf._cat_sequence_lists(*self._seq_dict.values())
        self._get_all_pairwise_distances(leaves)
        # Sort distances
        self._sort_distances()


    def return_ordered_seqs(self):
        """Returns ordered sequences following execution"""
        return self._ordered_seqs


    def _get_all_pairwise_distances(self, leaves):
        """Calculates all pairwise distances from each leaf to each other leaf
        and updates the internal LeafSeq distance attribute for each
        """
        scroll_log.log_message(
                scroll_log.BraceMessage(
                    "Calculating pairwise distances between all tree leaves\n"),
                2,
                'INFO',
                console_logger, file_logger,
                )
        for leaf in leaves:
            # Remove target leaf from list copy
            other_leaves = leaves[:]
            for oleaf in other_leaves:
                # Simply calling other_leaves.remove(leaf) does not work
                # Need to explicitly find matching names
                if leaf._node.name == oleaf._node.name:
                    other_leaves.remove(oleaf)
            # Now can get distances
            for oleaf in other_leaves:
                # Sort so bi-directional dist works
                search_string = "{}.{}".format(*tuple(
                    sorted([leaf._node.name, oleaf._node.name])))
                try:
                    dist = self._cached[search_string]  # Try fast lookup
                except KeyError:
                    dist = leaf.get_distance(oleaf)  # Else, calculate and store
                    self._cached[search_string] = dist
                leaf._distance += dist


    def _sort_distances(self):
        """Populates internal list with <group><header><dist> tuples"""
        all_seqs = []
        for k,v in self._seq_dict.items():
            all_seqs.extend(v)
        self._ordered_seqs = sorted(all_seqs)


