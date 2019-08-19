"""
New Module containing code for filtering sequences in ScrollPy.

Idea is to have a class module that delegates filtering to one or more
subclasses that implement specific methods to calculate and filter the
data. Subclasses should return a list of (<group>,<SeqObj>,<value>)
tuples for the main methods removal function.

This removal function will attempt to call removal on internal dict
object assuming the group has enough members to support removal

"""


# NumPy will be installed anyway...
from numpy import mean,median,std


from scrollpy import config


class Filter:
    """Main class to handle filtering ScrollSeq objects by length.

    Args:
        seq_dict (dict): Dictionary of 'group':[<ScrollSeq>s] pairs to filter

    Returns:
        two dictionaries; the input dictionary with sequences removed, and
        a similar dictionary of removed sequences.
    """

    length_methods = ("ZSCORE", "MAD")
    identity_methods = ("IDENTITY")

    def __init__(self, seq_dict, **kwargs):
        self._seq_dict = seq_dict
        for setting in ("filter_method","by_group","outdir"):
            try:
                value = kwargs[setting]
            except KeyError:
                value = config["ARGS"][setting]
            # Now set it
            setattr(self, ('_'+setting), value)
        # Internal defaults
        self._removed = {}  # Mirrors self._seq_dict


    def __call__(self):
        """Filter and return"""
        # First, determine appropriate subclass to call
        if self._filter_method.upper() in length_methods:
            filterer = LengthFilter
        elif self._filter_method.upper() in identity_methods:
            filterer = IdentityFilter
        else:  # Will we get here? Args should be filtered...
            # Log a warning
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
                    self._outdir,
                    )
            self._to_remove.extend(removal_indices)
        # Then actually remove stuff
        self._remove_by_list()
        # Finally, return actual sequences remaining
        return (self._seq_dict,self._removed)


    def _remove_by_list(self):
        """Given a list of (<group>,<SeqObj>,<score>) tuples to remove,
        try to remove each from internal dict and add to removal dict;
        fails only if too many entries for a given group exist.
        """
        for group,r_obj,score in self._to_remove:  # Assume subclass returns sorted
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
                pass  # Log something here


    def _group_lengths_ok(self, group):
        """Checks if removing an item would reduce group length below threshold"""
        if len(self._seq_dict[group]) > self._filter_threshold:
            return True  # > not >= because this is prior to removal!
        return False


class GenericFilter:
    """Generic subclass that defines methods for returning indices.

    Args:
        seq_objs (list): List of ScrollSeq objects for filtering

    Returns:
        a single list of (<group>,<SeqObj>,<value>) members for use in
        parent classes removal methods.
    """
    def __init__(self, group_name, seq_list, method, **kwargs):
        self._name = group_name
        self._seq_list = seq_list
        self._method = method
        try:
            self._filter_threshold = kwargs["filter_threshold"]
        except KeyError:
            self._filter_threshold = config["ARGS"]["filter_method"]
        # Internal defaults
        self._indices = []
        self._to_remove = []


    def __call__(self):
        """Implement in subclass"""
        raise NotImplementedError


class LengthFilter(GenericFilter):
    """Subclass for filtering by length.
    """

    def __call__(self):
        """Create a list of lengths, calculate based on self._method,
        and then populate internal _to_remove list.
        """
        # Create lengths
        self._create_lengths()
        # Calculate the metrics and populate internal list
        removal_func = getattr(self, ("_remove_by_" + str(self._method)))
        removal_func()
        # Return back
        return self._to_remove


    def _create_lengths(self, ordered=False):
        """Populate internal _lengths and _indices"""
        unordered = []
        for seq_obj in self._seq_list:  # ScrollSeq objects
            unordered.append([obj,len(obj)])
        if ordered:  # Some methods require sorted lengths
            self._indices = sorted(
                    unordered,
                    key=lambda x:x[1],  # sort by sequence length
                    )
        else:
            self._indices = unordered[:]
        self._lengths = [x[1] for x in self._indices]


    def _get_removal_indices(self, values):
        """Add to internal list if values are above a threshold"""
        above = [(i,v) for i,v in enumerate(values) if v>=self._filter_threshold]
        for i,z-score in above:  # Index matches the original length and indices lists
            seq_obj,length = self._indices[i]
            self._to_remove.append(
                    self._name,  # Name of the actual group
                    seq_obj,
                    z-score,  # Scoring metric
                    )
        self._to_remove = sorted(self._to_remove,
                lambda x:x[2],
                reverse=True,  # Highest z-score removed first; furthest from average
                )


    @staticmethod
    def calculate_zscore(values):
        """Return an n-length list of z-scores"""
        smean = mean(values)
        s = std(values)
        return [((abs(x-smean))/s) for x in values]


    def _remove_by_zscore(self):
        """Calculates z-scores and removes all above a given threshold"""
        if not threshold:
            threshold = 2
        zscores = calculate_zscores(self._lengths)
        self._get_removal_indices(zscores)


    @staticmethod
    def calculate_mad(values):
        """Return an n-length list of modified z-scores"""
        pass


    def _remove_by_mad(self):
        """Calculates modified z-scores and removes all above a given threshold"""
        pass


class IdentityFilter(GenericFilter):
    """Subclass for filtering by inter-sequence similarity.
    """
    def __call__(self):
        """Create a list of tuples and then reduce down to those to be
        removed; add to internal list and then return.
        """
        # Make sequence file
        self._make_tmp_seqfile()
        # Align
        self._align_seqs()
        # Calculate identities and objects to remove
        self._remove_by_identity()
        # Return values to parent object
        return self._to_remove


    def _make_tmp_seqfile(self):
        """Writes all ScrollSeq objects to a temporary outfile for aligning
        """
        seq_path = self._get_filter_outpath('seqs')
        sf._sequence_list_to_file_by_id(self._seq_list,seq_path)
        self._seq_path = seq_path


    def _align_seqs(self):
        """Calls alignment program on temporary sequence file
        """
        msa_path = self._get_filter_outpath('align')
        alignger = align.Aligner(
                self._align_method,
                config['ALIGNMENT'][self._align_method],  # Cmd
                inpath = self._seq_path,
                outpath = msa_path,
                )
        aligner()  # May raise Application Error
        self._align_path = msa_path


    def _build_identity_list(self):
        """Parses alignment file and builds up a list of sequences that are at
        least <threshold> percent identical to each other.
        """
        self._align_dict = parse_alignment_file(self._align_path,
                file_type="fasta",  # Just for now -> make more modular eventualy
                )
        identity_set = set()
        for header1,header2 in itertools.combinations(
                self._align_dict.keys(),
                2,  # Pairwise
                ):
            zipped = zip(self._align_dict[header1], self._align_dict[header2])
            identical = sum((1 for res1,res2 in zipped if res1==res2))
            total = sum((1 for res1,res2 in zipped if not res1=='-' if not res2=='-'))
            if identical > total:
                raise ValueError  # Should never happen
            try:
                percent_identical = identical/total * 100
            except ZeroDivisionError:  # No aligned region
                percent_identical = 0
            if percent_identical >= self._filter_threshold:
                identity_set.add((header1,header2))  # Add as a tuple
        return identity_set


    def _remove_by_identity(self):
        """Recursively decompose identical tuple pairs and pick all IDs out of
        indices, add them to self._to_remove.
        """
        inital_set = self._build_identity_list()
        tuples_to_remove = _decompose_sets(initial_set)
        for_removal = []
        for tup in tuples_to_remove:
            for seq_id in tup:
                seq_obj = [seq_obj for seq_obj in self._seq_list if seq_obj._id == seq_id]
                for_removal.append(
                        self._name,  # Group
                        seq_obj,
                        len(seq_obj),
                        )
        self._to_remove = sorted(for_removal,
                key = lambda x:x[2],  # Sort by length
                reverse=True,  # Longest sequences first -> TO-DO, make changeable
                )[1:]  # Don't remove first entry


    @staticmethod
    def _decompose_sets(set_of_tuples, old_set_of_tuples=None, merged=None):
        """Recursively flatten a list of tuple identifiers to find all those that
        are at least <threshold> percent identical to at least one other member of
        the same set.
        """
        # Recurred versions or initialize new set
        old_set_of_tuples = old_set_of_tuples if old_set_of_tuples else set()
        merged = merged if merged else set()
        # Basecase 1
        if len(set_of_tuples) == 1:
            return set_of_tuples
        elif set_of_tuples == old_set_of_tuples:
            return set_of_tuples
        else:  # Do some work
            new_set_of_tuples = set()
            for tup1,tup2 in itertools.combinations(
                    set_of_tuples,
                    2,  # Pairwise combinations
                    ):
                merge = False
                for header1,header2 in itertools.product(tup1,tup2):
                    if header1 == header2:
                        merge = True
                        break
                if merge:
                    new_tup = set()
                    for tup in (tup1,tup2):
                        merged.add(tuple(sorted(tup)))  # Sort to avoid redundancy
                        try:
                            new_set_of_tuples.remove(tup)
                        except KeyError:
                            pass  # Not already in new set
                        for item in tup:
                            new_tup.add(item)
                    new_set_of_tuples.add(tuple(sorted(new_tup)))
                else:
                    for tup in (tup1,tup2):
                        if not tup in merged:
                            new_set_of_tuples.add(tuple(sorted(tup)))
            return _decompose_sets(new_set_of_tuples,set_of_tuples,merged)  # Recur


    def _get_filter_outpath(self, out_type):
        """Similar to Collection._get_outpath; returns a complete filepath
        based on the type of output required and self._name to avoid clobbering
        """
        basename = str(self._name)
        if out_type == 'seqs':
            outfile = basename + '.fa'
            outpath = os.path.join(self._outdir, outfile)
        elif out_type == 'align':
            outfile = basename + '.mfa'
            outpath = os.path.join(self._outdir, outfile)
        else:
            raise ValueError # Is this necessary?
        return outpath

