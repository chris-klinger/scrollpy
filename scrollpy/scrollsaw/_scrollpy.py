"""
This module contains the main ScrollPy object.
"""

import os
import tempfile
from itertools import combinations

from scrollpy import config
from scrollpy import scroll_log
from scrollpy import FatalScrollPyError
from scrollpy.files import sequence_file as sf
from scrollpy import ScrollSeq
from scrollpy import ScrollCollection
from scrollpy import Filter
# from scrollpy.sequences._scrollseq import ScrollSeq
# from scrollpy.sequences._collection import ScrollCollection
# from scrollpy.filter._filter import Filter
#from scrollpy.util import _util


# Get module loggers
(console_logger, status_logger, file_logger, output_logger) = \
        scroll_log.get_module_loggers(__name__)


class ScrollPy:
    """Main ScrollPy object; based on user input, run is variable.

    Args:
        seq_dict (dict): a dictionary of mapped group/object pairs

        target_dir (str): path to target directory for main output file.

    """
    # Class var list
    _config_vars = (
            'align_method',
            'dist_method',
            )

    def __init__(self, seq_dict, target_dir, **kwargs):
        # Required
        self._seq_dict = seq_dict
        self.target_dir = target_dir
        # Optional vars or in config
        for var in self._config_vars:
            try:
                value = kwargs[var]
            except KeyError:
                value = config['ARGS'][var]
            setattr(self, var, value)
        # Internal defaults
        self._groups = list(self._seq_dict.keys())
        self._ordered_seqs = []
        self._group_counter = 1  # (possibly unused) counter for group IDs
        self._collections = []
        self._remove_tmp = False


    #def __str__(self):
    #    """TO-DO"""
    #    pass

    #def __repr__(self):
    #    """TO-DO"""
    #    pass

    def __call__(self):
        """Runs Scrollsaw"""
        # If no tmpdir is None, make a temporary directory
        if not self.target_dir:
            self._remove_tmp = True  # Signal for removal
            # Var creation stalls garbage collection?
            tmp_dir = tempfile.TemporaryDirectory()
            #print("Target directory is: {}".format(tmp_dir.name))
            self.target_dir = tmp_dir.name
        # Try to run all steps; any uncaught errors close tmpdir
        try:
            # make collection objects
            self._make_collections()
            # actually run alignment/distance calculations
            total = len(self._collections)
            scroll_log.log_newlines(console_logger)
            for i,collection in enumerate(self._collections):
                scroll_log.log_message(
                        scroll_log.BraceMessage(
                            "Performing comparison {} of {}",
                            i+1, total),
                        3,
                        'INFO',
                        status_logger,
                        )
                collection()
            scroll_log.log_newlines(console_logger)
        finally:
            if self._remove_tmp:
                tmp_dir.cleanup()  # Remove temporary directory
        # If all steps ran, sort internal objects
        self._sort_distances()


    def return_ordered_seqs(self):
        """Returns all ScrollSeq objects in order as a list."""
        return self._ordered_seqs


    def _make_collections(self):
        """Creates all possible pairwise ScrollCollection objects.

        Args:
            (self.infiles)
            (self._groups)

        Returns:
            a list of ScrollCollection objects
        """
        if len(self._groups) == 1: # only one group
            group = self._groups[0]
            scroll_log.log_message(
                    scroll_log.BraceMessage(
                        "Adding collection object for single group {}", group),
                    3,
                    'INFO',
                    console_logger, file_logger,
                    )
            self._collections.append(ScrollCollection(
                self.target_dir,
                self._seq_dict[group], # seq_list
                group,
                # self.align,  # Alignment method
                # self.distance,  # Distance method
                ))
        for group1,group2 in combinations(self._groups,2): # pairwise
            scroll_log.log_message(
                    scroll_log.BraceMessage(
                        "Adding collection object for groups {} and {}\n",
                        group1, group2,
                        ),
                    3,
                    'INFO',
                    console_logger, file_logger,
                    )
            seq_list = sf._cat_sequence_lists(
                self._seq_dict[group1],
                self._seq_dict[group2]) # Dict values are lists
            self._collections.append(ScrollCollection(
                self.target_dir,
                seq_list,
                group1,
                # self.align,  # Alignment method
                # self.distance,  # Distance method
                opt_group = group2 # Arbitrary which group is the 'optional' one
                ))


    def _sort_distances(self):
        """Sorts all objects in an internal list.

        Args:
            (self._seq_dict)

        Returns:
            Creates an ordered list of ScrollSeq objects (self._ordered_seqs)
        """
        all_seqs = []
        for k,v in self._seq_dict.items():
            all_seqs.extend(v)
        self._ordered_seqs = sorted(all_seqs) # Sorts on ScrollSeq._distance
