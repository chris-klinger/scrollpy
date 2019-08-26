"""
This module contains a class for holding both node and sequence information
for leaves in an ETE tree object.

A parsed ETE tree's leaves can be used to build an equivalent set of LeafSeq
objects, which wrap behaviour of both ETE tree nodes and BioPython sequence
objects to allow the same kind of populating, sorting, and output behaviour
as currently exists for ScrollSeq objects.
"""

from functools import total_ordering


@total_ordering
class LeafSeq:
    """Represents a terminal leaf node and associated sequene (optional).

    Args:
        id_num (int): unique ID number to assign to instance
        group (str): group to which the sequence belongs
        tree_node  (obj): ETE TreeNode object
        seq_obj (obj): ScrollSeq object (default: None)
    """
    def __init__(self, id_num, group, tree_node, seq_obj=None):
        self._id = id_num
        self._group = group
        self._node = tree_node
        self._seq = seq_obj  # Can be None
        # Internal defaults
        self._distance = 0.0  # Initialize float counter for distance


    def __str__(self):
        """Use constituent objects"""
        if self._seq:
            return "{} : {}".format(self._node, self._seq)
        else:
            return "{}".format(self._node)


    def __repr__(self):
        """Use constituent objects"""
        return "LeafSeq({!r}, {!r}, {!r}, {!r})".format(
                self._id, self._group, self._node, self._seq)


    def __iadd__(self, other):
        """Adds distance to internal float"""
        # Note, this could also throw an OverflowError if distance is very large
        distance = float(other) # Throws ValueError if conversion isn't possible
        if distance < 0.0:
            raise ValueError("Cannot add negative distance")
        self._distance += distance # Assuming no Error, increment counter
        return self


    def __lt__(self, other):
        return self._distance < other


    def __eq__(self):
        return self._distance == other


    def __len__(self):
        """Differs depending on whether there is a sequence"""
        if self._seq:
            return len(self._seq)
        else:
            return len(self._node)


    def __getattr__(self):
        """Delegate calls to underlying object(s)"""
        underlying_obj = None
        try:
            attr = getattr(self._node, name)
            underlying_obj = self._node
        except AttributeError:
            try:
                attr = getattr(self._seq, name)
                underlying_obj = self._seq
            except AttributeError:
                raise AttributeError(
                    "LeafSeq object {} has no attribute {}".format(
                        self, name))
        if callable(attr):  # User wanted a function
            def wrapped_func(*args, **kwargs):
                new_args = []
                for arg in args:
                    if isinstance(arg, SeqNode):  # I.e. comparing two nodes
                        arg = arg._node  # Replace with node attr of other object
                    new_args.append(arg)
                ret = attr(*new_args, **kwargs)  # Wrap old func with new args
                return ret
            return wrapped_func
        else:
            return attr


    def _write(self, file_obj, outfmt="fasta"):
        """Delegate to underlying ScrollSeq object or raise AttributeError if
        instance has no sequence object set.
        """
        if self._seq:
            self._seq._write(file_obj, outfmt)
        else:
            raise AttributeError("LeafSeq object {} missing associated
                    ScrollSeq object".format(self))


    def _write_by_id(self, file_obj):
        """As above, delegate or raise AttributeError"""
        if self._seq:
            self._seq._write_by_id(file_obj)
        else:
            raise AttributeError("LeafSeq object {} missing associated
                    ScrollSeq object".format(self))


    @property
    def id_num(self):
        """Ensure ID is set; raise AttributeError if not"""
        if not self._id:
            raise AttributeError(
                "Missing ID for LeafSeq object {}".format(self))
        return int(self._id)


    @id_num.setter
    def id_num(self):
        raise AttributeError("Cannot change LeafSeq ID after instantiation")


    @id_num.deleter
    def id_num(self):
        raise AttributeError("Cannot delete LeafSeq ID")
