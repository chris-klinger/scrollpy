"""
Module containing code for filtering sequences in ScrollPy.

Idea is a single class that can call one or more methods. To keep
dependencies low, implement basic ones in code and rely on other
libraries for more complicated examples (or if required anyway,
change earlier ones to more complex.
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
    def __init__(self, seq_dict, **kwargs):
        self._seq_dict = seq_dict
        try:
            self._method = kwargs["filter_method"]
        except KeyError:
            self._method = config["ARGS"]["filter_method"]
        # Internal defaults
        self._removed = {}  # Mirrors self._seq_dict
        self._lengths = []  # Used for actual calculations
        self._indices = []  # Nested list of group,obj,length values


    def __call__(self):
        """Filter and return"""
        pass


    def _create_lengths(self, ordered=False):
        """Populate internal _lengths and _indices"""
        if ordered:  # Need to actually consider order
            unordered = []
            for group,seq_objs in self._seq_dict.items():
                for obj in seq_objs:
                    unordered.append([group,obj,len(obj)])
                self._indices = sorted(unordered,
                        key=lambda x:x[2])  # sort by sequence length
                self._lengths = [x[2] for x in self._indices]
        else:
            for group,seq_objs in self._seq_dict.items():
                for obj in seq_objs:
                    seq_length = len(obj)
                    self._indices.append([group,obj,seq_length])
                    self._lengths.append(seq_length)


    def _remove_by_index(self, index):
        """Remove specified index item if possible"""
        group = self._indices[index][0]
        if self._group_lengths_ok(group):
            obj = self._indices[index][1]
            # Add to 'removed'
            try:
                self._removed[group].append(obj)
            except KeyError:
                self._removed[group] = []
                self._removed[group].append(obj)
            # Delete from all other internals
            for l in (self._indices,self._lengths):
                del l[index]
            del self._indices
            self._seq_dict[group].remove(obj)
        else:
            raise ValueError  # Can't remove list item


    def _remove_by_indices(self, indices):
        """Given an iterable of indices, try to remove each one"""
        remaining = indices
        for index in indices:
            try:
                self._remove_by_index(index)
            except ValueError:
                pass  # Stop, but report something or other


    def _group_lengths_ok(self, group, threshold=2):
        """Checks if removing an item would reduce group length below threshold"""
        if len(self._seq_dict[group]) > threshold:
            return True  # > not >= because this is prior to removal!
        return False


    def _recursive_remove(values, threshold, above=None):
        """Recursively remove from a list"""
        if not above:
            above = [v for v in values if v>=threshold]
        if not above:
            return
        else:
            try:
                i = values.index(above[0])  # works even if two values are the same
                self._remove_by_index(i)
                del values[i]
                self._recursive_remove(values, threshold, above)
            except ValueError:
                pass  # print something?


    def _remove_by_zscore(self, threshold=None):
        """Calculates z-scores and removes all above a given threshold"""
        if not threshold:
            threshold = 3
        zscores = calculate_zscores(self._lengths)
        self._recursive_remove(zscores, threshold)


    def _remove_by_MAD(self, threshold=None):
        """Calculates modified z-scores and removes all above a given threshold"""
        pass


def calculate_zscores(values):
    """Return an n-length list of z-scores"""
    mean = mean(values)
    s = std(values)
    return [((abs(x-mean))/s) for x in values]


def calculate_MAD(values):
    """Return an n-length list of modified z-scores"""
    pass
