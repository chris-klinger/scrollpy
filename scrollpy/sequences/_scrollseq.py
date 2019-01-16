"""
This module contains a class for holding sequence information (as parsed
by BioPython) along with some sequence metadata.

Each sequence identified in either a treefile or a sequence file can
be modelled by one ScrollSeq object. Addition of each sequence to
the top-level ScrollPy object uses memoization to ensure that each
ScrollSeq object is referred to by a single unique ID.
"""

from Bio import SeqIO

from scrollpy.util._util import split_input

class ScrollSeq:
    """A basic sequence representation.

    Args:
        id_num (int): Unique ID number to assign to instance
        infile (str): full path to file of origin
        group (str): group to which the sequence belongs
        SeqRecord (obj): BioPython object (default: None)
    """
    def __init__(self, id_num, infile, group, SeqRecord=None,
            accession=None, name=None, description=None, seq=None): # property attrs
        self._id = id_num
        self._infile = infile
        self._group = group
        self._distance = 0.0 # Initialize float counter for distance
        self._record = SeqRecord
        # All remaining attributes are internal properties
        self._accession = accession
        self._name = name
        self._description = description
        self._seq = seq

    def __str__(self):
        """Default to BioPython str if present; otherwise basic"""
        if self._record:
            return self._record.__str__ # Does this work?
        else:
            pass # TO-DO

    def __repr__(self):
        """Probably need something here, not just parsed object"""
        pass # TO-DO

    def __iadd__(self, other):
        """Adds distance to internal float"""
        # Note, this could also throw an OverflowError if distance is very large
        distance = float(other) # Throws ValueError if conversion isn't possible
        if distance < 0.0:
            raise ValueError("Cannot add negative distance")
        self._distance += distance # Assuming no Error, increment counter
        return self

    # TO-DO: maybe implement lt/gt/etc. to allow for sorting?

    def _write(self, file_obj):
        """Writes internal sequence object as per Bio.SeqIO"""
        SeqIO.write(self._record, file_obj, "fasta")

    def _write_by_id(self, file_obj):
        """Writes internal sequence object using ID for header"""
        header = '>' + str(self.id_num)
        seq = str(self.seq)
        file_obj.write(header + '\n')
        for chunk in split_input(seq):
            file_obj.write(chunk + '\n')

    @property
    def id_num(self):
        """Ensure ID is set, raise AttributeError if not"""
        if not self._id:
            raise AttributeError(
                "Missing ID for ScrollSeq object {}.".format(
                    self.accession))
        return int(self._id)

    @id_num.setter
    def id_num(self):
        raise AttributeError("Cannot change ScrollSeq ID after instantiation")

    @id_num.deleter
    def id_num(self):
        raise AttributeError("Cannot delete ScollSeq ID")

    @property
    def accession(self):
        """Use SeqRecord.id, if it exists"""
        if not self._record:
            return None
        return self._record.id

    @accession.setter
    def accession(self, value):
        raise AttributeError("Cannot change accession on SeqRecord object")

    @accession.deleter
    def accession(self):
        raise AttributeError("Cannot remove accession from SeqRecord object")

    @property
    def name(self):
        """Use SeqRecord.name, if it exists"""
        if not self._record:
            return None
        return self._record.name

    @name.setter
    def name(self, value):
        raise AttributeError

    @name.deleter
    def name(self):
        raise AttributeError

    @property
    def description(self):
        if not self._record:
            return None
        return self._record.description

    @description.setter
    def description(self, value):
        raise AttributeError

    @description.deleter
    def description(self):
        raise AttributeError

    @property
    def seq(self):
        if not self._record:
            return None
        return self._record.seq # Note: returns a Seq object

    @seq.setter
    def seq(self, value):
        raise AttributeError

    @seq.deleter
    def seq(self):
        raise AttributeError
