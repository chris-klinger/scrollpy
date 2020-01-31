"""
New Module containing code for filtering sequences in ScrollPy.

Idea is to have a class module that delegates filtering to one or more
subclasses that implement specific methods to calculate and filter the
data. Subclasses should return a list of (<group>,<SeqObj>,<value>)
tuples for the main methods removal function.

This removal function will attempt to call removal on internal dict
object assuming the group has enough members to support removal

"""

import os
import contextlib
import itertools

# NumPy will be installed anyway...
from numpy import mean,median,std


from scrollpy import config
from scrollpy import scroll_log
from scrollpy import FatalScrollPyError
from scrollpy.alignments import align,parser
from scrollpy.files import sequence_file as sf
from scrollpy.util._util import decompose_sets
# Global list for removal
from scrollpy import tmps_to_remove


# Get module loggers
(console_logger, status_logger, file_logger, output_logger) = \
        scroll_log.get_module_loggers(__name__)


class Filter:
    """Main class to handle filtering ScrollSeq objects by length.

    Args:
        seq_dict (dict): Dictionary of <group>:[<ScrollSeqs>] pairs to
            filter.
        **kwargs: If specified, contains information dictating how
            filtering occurs; defaults to config values.

    """

    length_methods = ("ZSCORE", "MAD")
    identity_methods = ("IDENTITY")

    _config_vars = (
            'filter_method',
            'filter_by_group',
            'filter_threshold',
            )

    def __init__(self, seq_dict, **kwargs):
        """Sets values by arguments or through config."""
        self._seq_dict = seq_dict
        for var in _config_vars:
            try:
                value = kwargs[var]
            except KeyError:
                value = config["ARGS"][var]
            # Now set it
            setattr(self, ('_'+setting), value)
        # Internal defaults
        self._removed = {}  # Mirrors self._seq_dict


    def __repr__(self):
        return "{}({!r}, **{!r})".format(
                self.__class__.__name__,
                self.seq_dict,
                self.kwargs,
                )

    def __str__(self):
        return "{} {}".format(
                self._filter_method,
                self.__class__.__name__,
                )


    def __call__(self):
        """Performs filtering and returns filtered and removed sequences.

        Calls an instance of LengthFilter or IdentityFilter based on the
        filtering method and calls the resulting instance to actually
        perform the filtering.

        Returns:
            dict: Two dictionaries; the input dictionary with sequences
            removed, and a similar dictionary of removed sequences.

        """
        # First, determine appropriate subclass to call
        if self._filter_method.upper() in length_methods:
            filterer = LengthFilter
        elif self._filter_method.upper() in identity_methods:
            filterer = IdentityFilter
        else:  # Will we get here? Args should be filtered...
            # Log a warning??
            raise AttributeError  # Might change, just need to signal bad args
        # Determine whether to pool all Seq objects or go by group
        sequences = []
        sub_seq_list = []
        for group,seq_objs in self._seq_dict.items():
            if self._by_group:
                sequences.append(seq_objs)
            else:
                sub_seq_list.extend(seq_objs)
        if sub_seq_list:
            sequences.append(sub_seq_list)  # Creates a nested list
        # Now actually remove
        self._to_remove = []
        # First get all indices as a flat list
        for seq_list in sequences:  # One or more sub-lists
            removal_indices = filterer(
                    seq_list,
                    self._filter_method,
                    )
            self._to_remove.extend(removal_indices)
        # Then actually remove stuff
        self._remove_by_list()
        # Finally, return actual sequences remaining
        return (self._seq_dict,self._removed)


    def return_remaining_seqs(self):
        """Returns all sequences not removed as a dict.

        Simple access method for outside calls.

        Returns:
            dict: Original sequences remaining after filtering.

        """
        return self._seq_dict


    def return_removed_seqs(self):
        """Returns all sequences removed as a dict.

        Simple acccess method for outside calls.

        Returns:
            dict: Sequences removed during filtering.

        """
        return self._removed


    def _remove_by_list(self):
        """Remove values identified by filtering.

        Given a list of (<SeqObj>,<score>) tuples to remove, try to remove
        each from internal dict and add to removal dict. If too many
        entries for a given group exist, log a warning and pass silently.

        """
        for r_obj,score in self._to_remove:  # Assume subclass returns sorted
            group = self._get_group_for_seq_obj(r_obj)
            if self._group_lengths_ok(group):  # Still enough objects in group
                # Add to removal dict
                try:
                    self._removed[group].append(obj)
                except KeyError:
                    self._removed[group] = []
                    self._removed[group].append(obj)
                # Remove from seq dict
                seq_list = self._seq_dict[group]  # Iterate in place not safe; copy
                for i,s_obj in enumerate(seq_list):
                    if s_obj._id == r_obj._id:
                        del seq_list[i]
                self._seq_dict[group] = seq_list  # Replace old list
            else:
                scroll_log.log_message(
                        scroll_log.BraceMessage(
                            "Group length prevented filtering {} with "
                            "score {} from group {}",
                            r_obj.acession, score, group,
                            ),
                        1,
                        'WARNING',
                        file_logger,
                        )

    # Do we need this? -> SeqObj should have a ._group attribute!
    def _get_group_for_seq_obj(self, seq_obj):
        """Identifies the group for a given sequence object.

        Iterates through the internal dict until the sequence object is
        found, and then returns the corresponding group.

        Args:
            seq_obj: Sequence object.

        Returns:
            str: The name of the group the object is in.

        """
        group=None
        for group,objs in self._seq_dict.items():
            if seq_obj in objs:
                group=group
                break
        return group


    def _group_lengths_ok(self, group):
        """Determines whether more sequences could be removed from a group.

        Checks if removing an item would reduce the number of items in the
        group below a set threshold.

        Args:
            group (str): The name of the group.

        Returns:
            bool: True if more sequences can be removed; False otherwise.

        """
        if len(self._seq_dict[group]) > self._filter_threshold:
            return True  # > not >= because this is prior to removal!
        return False


class GenericFilter:
    """Generic subclass that defines methods for returning indices.

    Args:
        seq_objs (list): List of ScrollSeq objects for filtering.
        method (str): The method to use for filtering.
        **kwargs: Optional additional parameters for filtering.

    """
    def __init__(self, seq_list, method, **kwargs):
        self._seq_list = seq_list
        self._method = method
        try:
            self._filter_score = kwargs["filter_score"]
        except KeyError:
            self._filter_score = config["ARGS"]["filter_score"]
        # Store kwargs for __repr__
        self.kwargs = kwargs
        # Internal defaults
        self._indices = []
        self._to_remove = []


    def __repr__(self):
        return "{}({!r}, {!r}, **{!r})".format(
                self.__class__.__name__,
                self._seq_list,
                self._method,
                self.kwargs,
                )

    def __str__(self):
        return "{} employing {}".format(
                self.__class__.__name__,
                self._method,
                )

    def __call__(self):
        """Implement in subclass.

        Each call method should perform filtering and return a list of
        sequences for the calling class to remove.

        Returns:
            list: A single list of (<group>,<SeqObj>,<value>) members for
            use in parent class removal methods.

        """
        raise NotImplementedError


class LengthFilter(GenericFilter):
    """Subclass for filtering by length.

    Uses raw sequence lengths and a distribution to determine those that
    are significantly different from the average.

    """

    def __call__(self):
        """Filter based on length."""
        # Create lengths
        self._create_lengths()
        # Calculate the metrics and populate internal list
        removal_func = getattr(self, ("_remove_by_" + str(self._method)))
        removal_func()
        # Return back
        return self._to_remove


    def _create_lengths(self, ordered=False):
        """Obtains the lengths for all sequence objects.

        Populates internal _lengths and _indices. Sequences may either
        be sorted by length, or added in the input order.

        Args:
            ordered (bool): Whether to sort sequences by length.
                Defaults to False.

        """
        unordered = []
        for seq_obj in self._seq_list:  # ScrollSeq objects
            unordered.append([seq_obj,len(seq_obj)])
        if ordered:  # Some methods require sorted lengths
            self._indices = sorted(
                    unordered,
                    key=lambda x:x[1],  # sort by sequence length
                    )
        else:
            self._indices = unordered[:]
        self._lengths = [x[1] for x in self._indices]


    def _get_removal_indices(self, values):
        """Obtain indices of values to remove based on a threshold.

        For each value that exceeds the threshold, add to the internal
        self._to_remove attribute.

        Args:
            values (list): List of calculated values for filtering.

        """
        above = [(i,v) for i,v in enumerate(values) if v>=self._filter_score]
        for i,zscore in above:  # Index matches the original length and indices lists
            seq_obj,length = self._indices[i]
            # Note the actual filter value on seq_obj
            seq_obj._fvalue = zscore
            # Signal for removal
            self._to_remove.append((
                    seq_obj,
                    zscore,  # Scoring metric
                    ))
        self._to_remove = sorted(
                self._to_remove,
                key=lambda x:x[1],
                reverse=True,  # Highest z-score removed first; furthest from average
                )


    @staticmethod
    def calculate_zscore(values, absval=True):
        """Calculates Z-scores for sequence lengths.

        Args:
            values (list): Sequence lengths to calculate Z-scores.
            absval (bool): Whether to return |zscore| or the raw zscore,
                i.e. whether to ensure zscores are positive. Defaults to True.

        Returns:
            list: A list of calculated Z-scores.

        """
        smean = mean(values)
        s = std(values)
        if absval:
            return [((abs(x-smean))/s) for x in values]
        else:
            return [((x-smean)/s) for x in values]


    def _remove_by_zscore(self):
        """Calculates z-scores and removes all above a given threshold."""
        zscores = calculate_zscores(self._lengths)
        self._get_removal_indices(zscores)


    @staticmethod
    def calculate_mad(values):
        """Return an n-length list of modified z-scores"""
        pass  # TO-DO


    def _remove_by_mad(self):
        """Calculates modified z-scores and removes all above a given threshold"""
        pass  # TO-DO


class IdentityFilter(GenericFilter):
    """Subclass for filtering by sequence similarity.

    Applies pairwise sequence similarities to build up a set of all
    sequences that are above a certain similarity score. These are then
    decomposed into a smaller number of larger sequence groups.

    """
    def __init__(self, seq_list, method, outdir=None, **kwargs):
        """Delegates to BaseClass.

        Similar to the BaseClass __init__ method, but allows an additional
        <outdir> argument for producing aligned files between sequence
        groups.

        Args:
            outdir (str): Optional full path to output directory. If not
                specified, use a temporary directory. Defaults to None.

        """
        super().__init__(seq_list, method, **kwargs)
        if not outdir:
            import tempfile
            tmp_dir = tempfile.TemporaryDirectory()
            self._target_dir = tmp_dir.name  # TO-DO: give user option to keep?
            tmps_to_remove.append(self._target_dir)
        else:
            self._target_dir = outdir
        try:
            self._align_method = kwargs['align_method']
        except KeyError:
            self._align_method = config['ARGS']['align']


    def __call__(self):
        """Filter based on similarity."""
        # Make sequence file
        self._make_tmp_seqfile()
        # Align
        self._align_seqs()
        # Calculate identities and objects to remove
        self._remove_by_identity()
        # Remove temporary directory, if it still exists
        with contextlib.suppress(FileNotFoundError):
            self._target_dir.cleanup()
        # Return values to parent object
        return self._to_remove


    def _make_tmp_seqfile(self):
        """Writes all ScrollSeq objects to a temporary outfile.

        Sequences need to be written prior to aligning, as some programs
        (for example MAFFT) do not allow for sequences to be fed in
        through a pipe such as stdin.

        """
        seq_path = self._get_filter_outpath('seqs')
        sf._sequence_list_to_file_by_id(self._seq_list,seq_path)
        self._seq_path = seq_path


    def _align_seqs(self):
        """Calls alignment program on temporary sequence file."""
        msa_path = self._get_filter_outpath('align')
        aligner = align.Aligner(
                self._align_method,
                config['ALIGNMENT'][self._align_method],  # Cmd
                inpath = self._seq_path,
                outpath = msa_path,
                )
        aligner()  # May raise Application Error
        self._align_path = msa_path


    def _build_identity_set(self):
        """Builds a set of similar sequences from an alignment.

        Parses alignment file and builds up a set of sequences that are at
        least <threshold> percent identical to each other.

        Raises:
            FatalScrollPyError: Raised if the number of identical residues
                between two sequences is more than the total number.

        """
        self._align_dict = parser.parse_alignment_file(
                self._align_path,
                file_type="fasta",  # Just for now -> make more modular eventualy
                )
        identity_set = set()
        for header1,header2 in itertools.combinations(
                self._align_dict.keys(),
                2,  # Pairwise
                ):
            zipped = zip(self._align_dict[header1], self._align_dict[header2])
            idents,totals = [],[]
            for res1,res2 in zipped:
                if res1!='-' and res2!='-':
                    totals.append(1)
                    if res1==res2:
                        idents.append(1)
            identical = sum(idents)
            total = sum(totals)
            if identical > total:
                scroll_log.log_message(
                        scroll_log.BraceMessage(
                            "Fatal error when totalling identical positions for {} and {}",
                            header1, header2,
                            ),
                        1,
                        'ERROR',
                        console_logger, file_logger,
                        )
                raise FatalScrollPyError
            try:
                percent_identical = identical/total * 100
            except ZeroDivisionError:  # No aligned region
                scroll_log.log_message(
                        scroll_log.BraceMessage(
                            "No aligned region detected between {} and {}",
                            header1, header2,
                            ),
                        1,
                        'WARNING',
                        file_logger,
                        )
                percent_identical = 0
            if percent_identical >= self._filter_score:
                identity_set.add((header1,header2))  # Add as a tuple
                # Also add exact value to object
                for header in (header1,header2):
                    self._add_filter_score_to_obj(
                            header,
                            percent_identical,
                            )

        return identity_set


    def _add_filter_score_to_obj(self, header, score):
        """Adds a score to an object based on sequence header.

        Score is added directly to seq_obj._fvalue.

        Args:
            header (str): The sequence header.
            score (int): The similarity score for the object.

        """
        for seq_obj in self._seq_list:
            if seq_obj._id in header:
                seq_obj._fvalue = score


    def _remove_by_identity(self):
        """Select sequences for removal based on similarity.

        Recursively decomposes identical tuple pairs and pick all IDs out
        of the indices to add them to self._to_remove.

        """
        initial_set = self._build_identity_set()
        tuples_to_remove = decompose_sets(initial_set)
        for_removal = []
        for tup in tuples_to_remove:
            pairs = [(seq_obj,len(seq_obj)) for seq_obj in
                    self._seq_list if seq_obj._id in tup]
            for pair in sorted(
                    pairs,
                    key=lambda x:x[1],  # Sort by length
                    reverse=True,  # Longest first
                    )[1:]:  # Keep first entry
                self._to_remove.append(pair)


    def _get_filter_outpath(self, out_type):
        """Obtains a sensible outpath for sequences.

        File extension is determined by the type of output specified
        (align/seqs).

        Args:
            out_type (str): Specifies the output file extension.

        Returns:
            str: Full path to the output file.

        """
        basename = "filter_seqs"
        if out_type == 'seqs':
            outfile = basename + '.fa'
            outpath = os.path.join(self._target_dir, outfile)
        elif out_type == 'align':
            outfile = basename + '.mfa'
            outpath = os.path.join(self._target_dir, outfile)
        else:
            raise ValueError # Is this necessary?
        return outpath

