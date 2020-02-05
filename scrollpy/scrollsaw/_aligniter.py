"""
This module contains the main AlignIter object.
"""

import os
import tempfile
import bisect

import numpy as np
from numpy import mean,std

from Bio import AlignIO

from scrollpy import config
from scrollpy import scroll_log
from scrollpy import FatalScrollPyError
# from scrollpy.alignments.eval_align import AlignEvaluator
from scrollpy import AlignEvaluator
# from scrollpy.filter._new_filter import LengthFilter  # Don't need?!
# from scrollpy.trees.maketree import TreeBuilder
from scrollpy import TreeBuilder
from scrollpy.alignments import parser
from scrollpy.files import tree_file
from scrollpy.util import _util,_tree
# Global list for removal
from scrollpy import tmps_to_remove
from scrollpy import scrollutil


# Get module loggers
(console_logger, status_logger, file_logger, output_logger) = \
        scroll_log.get_module_loggers(__name__)


class AlignIter:
    """Main AlignIter object for selecting alignment columns.

    Alignment columns are evaluated using an external method and then
    selected for iterative removal. At each stage, a tree is constructed
    using a fast tree-building method to obtain an estimate of the tree
    quality. This measure is objective, but for now it is calculated as
    the sum of bootstrap supports across all nodes.

    Once no more columns can be removed, or once the resulting tree
    support falls below a given threshold, the iteration stops and the
    best-scoring alignment across iteration is considered 'optimal'.

    Args:
        alignment (str): The full path to the alignment file.
        target_dir (str): The full path to a directory for output files.
        num_columns (int): Optional argument specifying an explicit
            number of alignment columns to remove at each iteration. If
            not specified, the number if calculated. Defaults to None.
        **kwargs: Additional keyword arguments for specifying alignment
            and tree-building paramets. If not specified, these are
            obtained from global config.

    """

    # Class var list
    _config_vars = (
            'alignfmt',
            'col_method',
            'iter_method',
            'tree_method',
            'tree_matrix',
            )

    def __init__(self, alignment, target_dir, num_columns=None, **kwargs):
        # Required
        self._alignment   = alignment
        self._outdir      = target_dir
        self._num_columns = num_columns
        # Optional vars or in config
        for var in self._config_vars:
            try:
                value = kwargs[var]
            except KeyError:
                value = config['ARGS'][var]
            setattr(self, var, value)
        # Call function to set self._align_name
        self._set_alignment_name()
        # Keep kwargs for __repr__
        self.kwargs = kwargs
        # Internal default that does not change each time through __call__
        self._start_length       = None
        self._start_obj          = None
        self._start_cols         = []
        self._remove_tmp         = False
        # Internal defaults; change each time through __call__
        self._align_obj          = None  # Parsed BioPython object
        self._columns            = []
        self._current_phy_path   = ""
        self._current_tree_path  = ""
        self._current_tree_obj   = None
        self._current_support    = 0
        self._all_supports       = []
        # Optimal alignment/tree info
        self._optimal_alignment  = None  # Object
        self._optimal_support    = 0     # Total BS support
        # Collated information for output
        self.iter_info          = []


    def __repr__(self):
        return "{}({!r}, {!r}, {!r}, **{!r})".format(
                self.__class__.__name__,
                self._alignment,
                self._outdir,
                self._num_columns,
                self.kwargs,
                )

    def __str__(self):
        return "{} using {}".format(
                self.__class__.__name__,
                self.col_method,
                )


    def __call__(self):
        """Runs AlignIter.

        Calls other internal methods depending on instance variables.

        """
        if not self._outdir:
            self._remove_tmp = True
            tmp_dir = tempfile.TemporaryDirectory()
            self._outdir = tmp_dir.name
            tmps_to_remove.append(self._outdir)  # Later removal
        # Get alignment object
        self._parse_alignment()
        # Run program to evaluate columns
        # columns_outpath = self._get_outpath('columns')
        columns_outpath = scrollutil.get_filepath(
                self._outdir,
                self._align_name,
                'column',
                extra='columns',
                )
        self._calculate_columns(columns_outpath)
        # Parse output
        self._evaluate_columns(columns_outpath)
        # Run analysis
        if self.iter_method == 'hist':
            scroll_log.log_message(
                    scroll_log.BraceMessage(
                        "Running tree iteration using histogram method"),
                    2,
                    'INFO',
                    console_logger, file_logger,
                    )
            self._hist_run()
        elif self.iter_method == 'bisect':
            scroll_log.log_message(
                    scroll_log.BraceMessage(
                        "Running tree iteration using bisection method"),
                    2,
                    'INFO',
                    console_logger, file_logger,
                    )
            self._bisect_run()
        else:
            print("Could not run __call__")
        # Add easy lookup value to self.iter_info
        self._evaluate_info()
        # # Clean up  -> Moved to __main__.run_cleanup()
        # if self._remove_tmp:
        #     tmp_dir.cleanup()

    def _set_alignment_name(self):
        """Called on __init__ to set name for outpaths."""
        align_name = os.path.basename(self._alignment)
        self._align_name = align_name.rsplit('.',1)[0]


    def get_optimal_alignment(self):
        """Convenience access method for the optimal alignment."""
        return self._optimal_alignment


    def _parse_alignment(self):
        """Calls external methods to parse alignment file."""
        align_object = parser.parse_alignment_file(
                self._alignment,  # filepath
                self.alignfmt,   # alignment type
                to_dict=False,    # return actual object
                )
        # Now set to instance variable
        self._align_obj = align_object
        self._start_obj = self._align_obj


    def _parse_tree(self):
        """Calls external methods to parse tree file."""
        tree_obj = tree_file.read_tree(
                self._current_tree_path,
                'newick',
                )
        # Set to instance variable
        self._current_tree_obj = tree_obj


    def _write_current_alignment(self):
        """Uses BioPython methods to write alignment file."""
        AlignIO.write(
                self._align_obj,
                self._current_phy_path,
                'phylip-relaxed',
                )


    def _get_outpath(self, out_type, length=None):
        """Obtain the full path to an output file.

        Args:
            out_type (str): The type of output file needed. Should be
                one of <columns>, <phylip>, or <tree>.
            length (int): Optional current length of the alignment.
                Defaults to None.

        Returns:
            str: Full path to the output file.

        """
        align_name = os.path.basename(self._alignment)
        basename = align_name.rsplit('.',1)[0]
        # Outfile depends on out_type
        if out_type == 'columns':
            outfile = basename + '_columns.txt'
        elif out_type in ('phylip','tree'):
            if not length:
                raise ValueError  # Log it
            strlen = str(length)
            if out_type == 'phylip':
                outfile = basename + '_' + strlen + '.phy'
            elif out_type == 'tree':
                if self.tree_method == 'Iqtree':
                    outfile = basename + '_' + strlen + '.phy.contree'
        # Get full outpath and return
        outpath = os.path.join(self._outdir, outfile)
        return outpath


    def _calculate_columns(self, column_path):
        """Calls external method to evaluate alignment columns.

        Creates and runs an instance of the AlignEvaluator class in
        order to evaluate alignment columns.

        Args:
            column_path (str): Full path to the expected output file.

        """
        if self.col_method == 'zorro':
            # Very short command
            column_command = [
                    self._alignment,
                    ]
        elif self.col_method == 'Generic':
            pass  # Keep options open?
        evaluator = AlignEvaluator(
                self.col_method,
                config['ITER'][self.col_method],  # Actual cmd
                self._alignment,  # Alignment is infile
                column_path,  # Outpath
                cmd_list = column_command,
                )
        evaluator()


    def _evaluate_columns(self, column_path):
        """Calls external methods to parse column file."""
        columns = []
        if self.col_method == 'zorro':
            for i,line in enumerate(
                    _util.non_blank_lines(column_path)):
                val = float(line)
                columns.append([i,val])
        elif self.iter_method == 'Generic':
            pass
        # No return -> update internal value
        self._columns = sorted(
                columns,
                key=lambda x:x[1],
                )
        self._start_cols = self._columns[:]
        self._start_length = len(columns)


    def _hist_run(self):
        """Progressively remove low scoring columns by binning columns.

        At each iteration, calculates the binning of column scores using
        NumPy and removes a number of columns based on the lowest bin
        count and the fraction of columns remaining compared to the
        original alignment.

        Each iteration also checks whether the optimal alignment has
        likely been reached; this test depends on the current tree
        score and all previous scores.

        """
        # Enter loop
        optimal = False
        # Determine whether calculations are needed
        if not self._num_columns:
            calc_columns = True
        iter_num = 0
        while not optimal:
            scroll_log.log_message(
                    scroll_log.BraceMessage(
                        "Performing tree iteration {} of many", (iter_num+1)),
                    3,
                    'INFO',
                    status_logger,
                    )
            if iter_num >= 1:
                # Determine number of columns to remove
                if calc_columns:  # Calculate
                    self._num_columns = self._calculate_num_columns()
                # Remove them from the alignment
                self._remove_columns(self._num_columns)
            # Calculate lowest column score
            low_val = self._columns[0][1]

            # Determine outpath names
            self._get_current_outpaths()
            # Write new alignment to file
            self._write_current_alignment()
            # Build IQ-Tree
            self._make_tree()
            # Parse and add to internal object
            self._parse_tree()
            # Add up total BS support
            self._calculate_support()
            # Keep track of all support values
            self._all_supports.append(self._current_support)
            # Decide whether to continue
            if self._current_support > self._optimal_support:
                self._optimal_alignment = self._align_obj
                self._optimal_support = self._current_support
            else:
                # If function returns True, loop breaks
                optimal = self._is_optimal()

            # Write information to an internal list
            self.iter_info.append([
                iter_num,
                len(self._columns),  # Alignment length
                low_val,  # Lowest value
                self._current_support,  # Support for current tree
                ])

            # If not optimal, keep going
            iter_num += 1
        # Prevent final status_logger line being overwritten
        scroll_log.log_newlines(console_logger)


    def _bisect_run(self):
        """Progressively bisect an alignment to find a local max.

        At each iteration, bisects the remaining alignment based on the
        previous number of removed columns and tree score. In short, if
        the previous bisection increases the score, the upper half of the
        remaining bound is chosen; otherwise, the lower half is chosen.

        Unlike histogram runs, this method recurs until the number of
        removed columns no longer changes, without checking optimality
        criteria at the end of each iteration.

        """
        # Run first iteration
        scroll_log.log_message(
                scroll_log.BraceMessage(
                    "Performing tree iteration 1 of many"),
                3,
                'INFO',
                status_logger,
                )
        # Calculate lowest column score
        low_val = self._columns[0][1]
        # Determine outpath names
        self._get_current_outpaths()
        # Write new alignment to file
        self._write_current_alignment()
        # Build IQ-Tree
        self._make_tree()
        # Parse and add to internal object
        self._parse_tree()
        # Add up total BS support
        self._calculate_support()
        # Keep track of all support values
        self._all_supports.append(self._current_support)
        # Write information to an internal list
        self.iter_info.append([
            1,  # Iter num
            len(self._columns),  # Alignment length
            low_val,  # Lowest value
            self._current_support,  # Support for current tree
            ])
        # Recur until a final value is reached
        self._bisect_alignment(
                0,  # Start at first value
                self._start_length,  # Alignment length
                self._current_support,
                )
        # Prevent final status_logger ling being overwritten
        scroll_log.log_newlines(console_logger)


    def _bisect_alignment(self, start, stop, prev_support, iter_num=2):
        """Recursively bisect an alignment.

        A separate recursive function called from self._bisect_run().
        Each recursive call has a start and stop over the alignment
        columns as well as a reference to the previous tree score. The
        number of columns to be removed increases or decreases
        according to the new tree score.

        Args:
            start (int): The start value for the current iteration.
            stop (int): The stop value for the current iteration.
            prev_support (int): The tree score for the previous iteration.
            iter_num (int): A counter tracking the number of iterations
                that have ocurred.

        Returns:
            Recursive call returns when the number of columns calculated
                for removal is less than 1.

        """
        num_cols = (stop-start)/2
        if num_cols < 1:
            return
        else:
            scroll_log.log_message(
                    scroll_log.BraceMessage(
                        "Performing tree iteration {} of many", iter_num),
                    3,
                    'INFO',
                    status_logger,
                    )
            # Set up to remove
            num_cols = int(num_cols)
            rem_cols = start + num_cols
            # print("Removing {} columns".format(rem_cols))
            self._align_obj = self._start_obj   # Start fresh
            self._columns = self._start_cols[:] # Start fresh
            # Remove from alignemnt
            self._remove_columns(rem_cols)
            # print(len(self._columns))
            # Calculate lowest column score
            low_val = self._columns[0][1]
            # Determine outpath names
            self._get_current_outpaths()
            # Write new alignment to file
            self._write_current_alignment()
            # Build IQ-Tree
            self._make_tree()
            # Parse and add to internal object
            self._parse_tree()
            # Add up total BS support
            self._calculate_support()
            # Keep track of all support values
            self._all_supports.append(self._current_support)
            # Set optimal values if needed
            if self._current_support > self._optimal_support:
                self._optimal_alignment = self._align_obj
                self._optimal_support = self._current_support
            # Write information to an internal list
            self.iter_info.append([
                iter_num,
                len(self._columns),  # Alignment length
                low_val,  # Lowest value
                self._current_support,  # Support for current tree
                ])
            # Decide whether to take old/new start
            if self._current_support > prev_support:
                new_start = start + num_cols
                new_stop = stop
            else:
                new_start = start
                new_stop = stop - num_cols
            # print("New start is {}".format(new_start))
            # print("New stop is {}".format(new_stop))
            # Recur
            self._bisect_alignment(
                    new_start,
                    new_stop,
                    self._current_support,
                    iter_num+1,
                    )


    def _calculate_num_columns(self):
        """Calculates the number of columns to remove.

        Uses the NumPy.histogram method to bin the current alignment
        scores, and calculates a number to remove based on the size
        of the first bin and the fraction of alignment columns
        remaining (compared to the original length).

        """
        # Length of columns
        curr_length = len(self._columns)
        fraction_remaining = curr_length/self._start_length
        # Score data
        current_scores = [v for _,v in self._columns]
        # Bin the data based on Doane's metric
        hist,bins = np.histogram(
                current_scores,   # Actual data
                bins='doane',  # Use Doane's method
                )
        # Adjust number by bin count and remaining alignment length
        num = int(hist[0] * fraction_remaining)
        # print("Remove {} columns".format(num))
        # Always remove at least one position
        return max(num,1)


    def _remove_columns(self, number):
        """Removes a number of columns from the current alignment.

        Removing alignment columns is not straight-forward, as it
        requires updating indexes for all remaining column scores so that
        they still correspond to the right column in the alignment.

        Args:
            number (int): The number of columns to remove.

        """
        # Iter while keeping track of indices
        indices = []
        values = []
        for i in range(number):  # i gives index
            value = self._columns[i]  # Already sorted
            values.append(value)
            index = value[0]  # 1st value
            indices.append(index)
        # Actually remove from list
        for value in values:
            self._columns.remove(value)
        # Remove from alignment
        self._remove_cols_from_align(indices)
        # Important! Need to shift values in self._columns
        self._shift_cols(indices)


    def _remove_cols_from_align(self, indices):
        """Remove columns from an alignment by indices.

        Column removal is difficult because removing columns changes the
        real position of remaining columns. To simplify this process,
        build a separate alignment that is the sum of columns to keep by
        leveraging BioPython alignment slicing.

        Args:
            indices (list): A list of all alignment positions to remove.

        """
        # Build up a list of slice indices
        last_val = len(indices)-1
        previous = None
        slices = []
        for i,val in enumerate(sorted(indices)):  # Must be sorted!
            inner = []
            # Index could be 0, specifically check if previous is None!
            if previous is None:  # First value
                inner.append(val)
            else:  # Later values require two indices
                inner.append(previous+1)  # +1 offset for list indexing
                inner.append(val)
            slices.append(inner)
            previous = val
            # If last value, also need to append
            if i == last_val:
                slices.append([val+1])
        # Build up a replacement alignment
        first_slice = slices[0][0]  # Slices are lists
        # Need an Align obj to concatenate onto
        edited = self._align_obj[:, :first_slice]
        for _slice in slices[1:]:  # Remaining slices
            if len(_slice) == 2:  # In the middle
                edited += self._align_obj[:, _slice[0]:_slice[1]]
            else:  # Last slice
                edited += self._align_obj[:, _slice[0]:]
        # Finally, replace old object
        self._align_obj = edited


    def _shift_cols(self, indices):
        """Updates alignment column indices following removal.

        Rather than keep track of all shifting values as they are removed,
        sort remaining columns and place them in a new list based on
        their place in the previous list. Then shift the index itself by
        the change in position.

        Args:
            indices (list): A list of all remaining alignment positions.

        """
        # Sort so bisect works
        sorted_indices = sorted(indices)
        # Now iter over alignment columns
        new_cols = []
        for index,_ in self._columns:  # Already removed
            position = bisect.bisect(
                    sorted_indices,  # Place in sorted list
                    index,           # Based on old index
                    )
            # Based on number of values before the index in the
            # sorted list, move the index 'up' by that many
            index -= position
            new_cols.append([index,_])
        # Finally, replace old object
        self._columns = new_cols


    def _get_current_outpaths(self):
        """Determine current phylip/tree outpaths.

        Called during alignment iteration to obtain full filepaths based
        on current alignment length.

        Raises:
            FatalScrollPyError: Raised if either filepath cannot be
                obtained for any reason.

        """
        align_name = os.path.basename(self._alignment)
        basename = align_name.rsplit('.',1)[0]
        # Length of all sequences should be the same, use first one
        current_align_length = len(self._align_obj[0].seq)
        # Use to calculate current values
        # self._current_phy_path   = self._get_outpath(
        #         'phylip',
        #         length=current_align_length,
        #         )
        self._current_phy_path = scrollutil.get_filepath(
                self._outdir,
                self._align_name,
                'alignment',
                extra=current_align_length,
                alignfmt='phylip',
                )
        # self._current_tree_path  = self._get_outpath(
        #         'tree',
        #         length=current_align_length,
        #         )
        self._current_tree_path = scrollutil.get_filepath(
                self._outdir,
                self._align_name,
                'tree',
                extra=current_align_length,
                treefmt='iqtree',
                )


    def _make_tree(self):
        """Calls external methods to build a phylogeny."""
        if self.tree_method == 'Iqtree':
            build_command = [
                    '-nt',  # Number of processors
                    'AUTO',
                    '-s',  # Input filename
                    self._current_phy_path,
                    '-m',
                    self.tree_matrix,  # E.g. 'LG'
                    '-bb',  # Rapid bootstrapping
                    '1000',
                    ]
        elif self.tree_method == 'RAxML':
            pass  # Add support eventually?
        builder = TreeBuilder(
                self.tree_method,
                config['TREE'][self.tree_method],  # Cmd to execute
                inpath = self._current_phy_path,  # Should exist
                outpath = self._current_tree_path,  # Should be a real path
                cmd_list = build_command,  # Uses subprocess internally
                )
        builder()  # Run command


    def _calculate_support(self):
        """Adds support over all nodes."""
        self._current_support = _tree.get_total_support(
                self._current_tree_obj)
        # print("Current support is: {}".format(self._current_support))


    def _is_optimal(self):
        """Determines whether the current alignment is likely oprtimal.

        Called during each iteration of a histogram run. Compares the
        current tree support to all supports from previous iterations and
        determines whether it represent an outlier (|zscore| > 2).

        In order for the calculation to have meaning, there must be at
        least three previous values for comparison.

        Returns:
            True if the current tree is an outlier from previous trees;
                False otherwise.

        """
        if len(self._all_supports) <=3:
            # print("Getting more values")
            return False  # Need more values
        else:
            # Determine the mean/std dev of all values
            smean = mean(self._all_supports)
            # print("Mean value is {}".format(smean))
            std_dev = std(self._all_supports)
            # print("Std dev is {}".format(std_dev))
            # calculate z-score of most recent value
            z_low = (self._current_support-smean)/std_dev
            # print("Low Z-score is {}".format(z_low))
            z_high = (self._optimal_support-smean)/std_dev
            # print("High Z-score is {}".format(z_high))
            # Stop if below a specific threshold
            if z_low <= -2 or z_high >= 2:  # Make user-specified?
                return True
        # Otherwise, return False -> more iterations
        return False


    def _evaluate_info(self):
        """Determines whether each iteration is optimal or sub-optimal.

        Called prior to writing output, adds an extra value to each item
        in self.iter_info.

        """
        for i,sub_list in  enumerate(sorted(
            self.iter_info,
            key=lambda x:x[3],  # Tree support
            reverse=True,  # Largest first
            )):
            if i == 0:
                sub_list.append("Optimal")
            else:
                sub_list.append("Sub-optimal")

