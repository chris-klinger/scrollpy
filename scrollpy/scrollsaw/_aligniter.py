"""
This module contains the main AlignIter object.
"""



class AlignIter:
    """Main AlignIter object; calls methods to select optimal columns.

    Args:
        alignment (str): alignment file handle

        target_dir (str): path to target directory for output file(s)

    """

    # Class var list
    _config_vars = ('alignfmt', 'iter_method', 'tree_method', 'tree_matrix')

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


    # def __repr__(self):
    #     """TO-DO"""
    #     pass


    # def __str__(self):
    #     """TO-DO"""
    #     pass


    def __call__(self):
        """Runs AlignIter"""
        if not self._outdir:
            self._remove_tmp = True
            tmp_dir = tempfile.TemporaryDirectory()
            self._outdir = tmp_dir.name
        # Get alignment object
        self._align_object = parser.parse_alignment_file(
                self._alignment,  # filepath
                self.alignfmt,   # alignment type
                to_dict=False,    # return actual object
                )
        # Run program to evaluate columns
        columns_outpath = self._get_outpath('columns')
        self._calculate_columns(columns_outpath)
        # Parse output
        self._evaluate_columns(columns_outpath)
        # Enter loop
        optimal = False
        number = self._num_columns  # None if not user-specified
        while not optimal:
            # Determine number of columns to remove
            if not number:  # Calculate
                number = self._calculate_num_columns()
            # Remove them from the alignment
            self._remove_columns(number)
            # Determine outpath names
            self._get_current_outpaths()
            # Write new alignment to file
            AlignIO.write(  # AlignIO interface!
                    self._align_obj,
                    self._current_phy_path,
                    "phylip-relaxed",  # Allows longer names
                    )
            # Build IQ-Tree
            self._make_tree()
            # Add up total BS support
            self._calculate_support()
            # Keep record of all support values
            self._all_suppports.append(self._current_support)
            # Decide whether to continue
            if self._current_support > self._optimal_suppport::
                self._optimal_alignment = self._align_obj
                self._optimal_support = self._current_support
            else:
                # If function returns True, loop breaks
                optimal = self._is_optimal()
        # Clean up
        if self._remove_tmp:
            tmp_dir.cleanup()


    def write_optimal_alignment(self):
        """User can request optimal alignment"""
        pass


    def _get_outpath(self, out_type, length=None):
        """Similar to other class functions"""
        align_name = os.path.basename(self._alignment)
        basename = align_name.rsplit('.',1)[0]
        # Outfile depends on out_type
        if out_type == 'columns':
            outfile = basename + '_columns.fa'
        elif out_type in ('phylip','tree'):
            if not length:
                raise ValueError  # Log it
            strlen = str(length)
            if out_type == 'phylip':
                outfile = basename + strlen + '.phy'
            elif out_type == 'tree':
                if self.tree_method == 'Iqtree':
                    outfile = basename + strlen + '.phy.contree'
        # Get full outpath and return
        outpath = os.path.join(self._outdir, outfile)
        return outpath


    def _calculate_columns(self, column_path):
        """Runs external program"""
        if self.iter_method == 'zorro':
            # Very short command
            column_command = [
                    self._alignment,
                    ]
        elif self.iter_method == 'Generic':
            pass  # Keep options open?
        evaluator = AlignEvaluator(
                self.iter_method,
                config['ITER'][self.iter_method],  # Actual cmd
                self._alignment,  # Alignment is infile
                column_path,  # Outpath
                cmd_list = column_command,
                )
        evaluator()


    def _evaluate_columns(self, column_path):
        """Parse output file into internal attribute"""
        columns = []
        if self.iter_method == 'zorro':
            for i,line in enumerate(
                    _util.non_blank_lines(column_path)):
                columns.append([i,line])
        elif self.iter_method == 'Generic':
            pass
        # No return -> update internal value
        self._columns = columns


    def _calculate_num_columns(self):
        """Calculate number of columns to remove based on values"""
        # Set this on instance later?!?
        threshold=-2  # I.e. 2 stddevs

        # Length of all sequences should be the same, use first one
        current_align_length = len(self._align_obj[0].seq)
        # Columns with statistically low scores
        scores = [v for _,v in self._columns]
        zscores = LengthFilter.calculate_zscore(scores)
        below = [v for v in enumerate(values) if v<=threshold]
        # Calculate based on remaining alignment length
        if not below:
            # No values are statistically low
            return 1  # Remove one at a time
        else:
            # // to return whole part only
            diff = current_align_length//len(below)
            return max(diff,1)  # Always remove at least one


    def _remove_columns(self, number):
        """Removes <number> of alignment columns from current object"""
        # Default sorting is low -> high
        sorted_columns = sorted(
                self._columns,
                key=lambda x:x[1],
                )
        # Iter while keeping track of indices
        indices = []
        values = []
        for i in range(number):  # i gives index
            value = sorted_columns[i]
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
        """Remove indices from alignment"""
        # Build up a list of slice indices
        last_val = len(indices)-1
        previous = None
        slices = []
        for i,val in enumerate(sorted(indices)):  # Must be sorted!
            inner = []
            if not previous:  # First value
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
        """Shifts all index,value pairs in internal list based on indices"""
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
        """Determine current phylip/tree outpath names"""
        pass


    def _make_tree(self):
        """Call tree program to make new tree"""
        pass


    def _calculate_support(self):
        """Add support over all nodes"""
        pass


    def _update_optimals(self):
        """Determine whether optimal values are updated"""
        pass


    def _is_optimal(self):
        """Determines whether to continue iterating"""
        pass

