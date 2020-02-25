#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###################################################################################
##
##  ScrollPy: Utility Functions for Phylogenetic Analysis
##
##  Developed by Christen M. Klinger (cklinger@ualberta.ca)
##
##  Please see LICENSE file for terms and conditions of usage.
##
##  Please cite as:
##
##  Klinger, C.M. (2020). ScrollPy: Utility Functions for Phylogenetic Analysis.
##  https://github.com/chris-klinger/scrollpy.
##
##  For full citation guidelines, please call ScrollPy using '--citation'
##
###################################################################################

"""
This module contains a class for holding sequence information (as parsed
by BioPython) along with some sequence metadata.

Each sequence identified in either a treefile or a sequence file can
be modelled by one ScrollSeq object. Addition of each sequence to
the top-level ScrollPy object uses memoization to ensure that each
ScrollSeq object is referred to by a single unique ID.
"""

from functools import total_ordering

from Bio import SeqIO

from scrollpy import scrollutil


@total_ordering
class ScrollSeq:
    """Represents a sequence in ScrollPy.

    Each ScrollSeq object is a thin wrapper over an underlying BioPython
    sequence object to allow for associating extra parameters such as ID,
    group, and distance.

    Args:
        id_num (int): Unique ID number to assign to instance.
        group (str): Group to which the sequence belongs.
        seq_record (obj): BioPython sequence object. Defaults to None.

    """
    def __init__(self, id_num, group, seq_record=None):
        self._id = id_num
        self._group = group
        self._record = seq_record
        # Internal defaults
        self._distance = 0.0 # Initialize float counter for distance
        self._fvalue = None  # Value used to filter
        # self._record = seq_record


    def __repr__(self):
        return "{}({!r}, {!r}, {!r})".format(
                self.__class__.__name__,
                self._id,
                self._group,
                self._record,
                )


    def __str__(self):
        # Either use sequence or record there is none
        if self._record:
            str_seq = self._record.__str__()
        else:
            str_seq = "no sequence"
        # Return string has same format either way
        return "{} #{} with {}".format(
                self.__class__.__name__,
                self._id,
                str_seq,
                )


    def __iadd__(self, other):
        """Adds distance to internal float.

        Adds distances during pairwise sequence comparisons by incrementing
        internal distance counter.

        Raises:
            ValueError: Raised if the value to be added is negative.

        """
        # Note, this could also throw an OverflowError if distance is very large
        distance = float(other) # Throws ValueError if conversion isn't possible
        if distance < 0.0:
            raise ValueError("Cannot add negative distance")
        self._distance += distance # Assuming no Error, increment counter
        return self


    def __lt__(self, other):
        return self._distance < other


    def __eq__(self, other):
        return self._distance == other


    def __len__(self):
        return len(self.seq)


    def _write(self, file_obj, outfmt = "fasta"):
        """Writes an associated sequence to a file.

        Uses BioPython Seq object writing method internally, if an
        associated sequence exists for the instance.

        Raises:
            AttributeError: Raised if no sequence object is set for the
                instance.

        """
        if self._record:
            SeqIO.write(self._record, file_obj, outfmt)
        else:
            raise AttributeError("No Associated SeqRecord for ScrollSeq "
                    "object {}".format(self))


    def _write_by_id(self, file_obj):
        """Writes an associated sequence to a file.

        BioPython sequence writing is not flexible enough to handle using
        different headers, so write using a simple internal method.

        Raises:
            AttributeError: Raised if no sequence object is set for the
                instance.

        """
        if self._record:
            header = '>' + str(self.id_num)
            seq = str(self.seq)
            file_obj.write(header + '\n')
            for chunk in scrollutil.split_input(seq):
                file_obj.write(chunk + '\n')
        else:
            raise AttributeError("No Associated SeqRecord for ScrollSeq "
                    "object {}".format(self))


    @property
    def id_num(self):
        """Obtains an ID number for the instance.

        Returns:
            int: The ID number for the instance.

        Raises:
            AttributeError: Raised if self._id is Nonetype. Each instance
                requires a unique ID.

        """
        if not self._id:
            raise AttributeError(
                "Missing ID for ScrollSeq object {}.".format(
                    self.accession))
        return int(self._id)


    @id_num.setter
    def id_num(self, value):
        """Prevents changing ScrollSeq ID after instantiation.

        Raises:
            AttributeError: Raised on any set call.

        """
        raise AttributeError("Cannot change ScrollSeq ID after instantiation")


    @id_num.deleter
    def id_num(self):
        """Prevents deleting ScrollSeq ID at any time.

        Raises:
            AttributeError: Raised on any delattr call.

        """
        raise AttributeError("Cannot delete ScollSeq ID")


    @property
    def accession(self):
        """Obtains an accession number for the instance.

        If an associated record exists, its accession is stored under the
        record.id attribute.

        Returns:
            int: The record.id attribute of an associated SeqRecord object
                if one exists, None otherwise.

        """
        if not self._record:
            return None
        return self._record.id


    @accession.setter
    def accession(self, value):
        """Prevents changing accesstion attribute of associated SeqRecord.

        Raises:
            AttributeError: Raised on any set call.

        """
        raise AttributeError("Cannot change accession on SeqRecord object")


    @accession.deleter
    def accession(self):
        """Prevents deleting accesstion attribute of associated SeqRecord.

        Raises:
            AttributeError: Raised on any set call.

        """
        raise AttributeError("Cannot remove accession from SeqRecord object")


    @property
    def name(self):
        """Obtains a name for the instance.

        If an associated record exists, its name is stored under the
        record.name attribute.

        Returns:
            str: The record.name attribute of an associated SeqRecord
                object if one exists, None otherwise.

        """
        if not self._record:
            return None
        return self._record.name


    @name.setter
    def name(self, value):
        """Prevents changing name attribute of associated SeqRecord.

        Raises:
            AttributeError: Raised on any set call.

        """
        raise AttributeError("Cannot change name of SeqRecord object")


    @name.deleter
    def name(self):
        """Prevents deleting name attribute of associated SeqRecord.

        Raises:
            AttributeError: Raised on any set call.

        """
        raise AttributeError("Cannot delete name of SeqRecord object")


    @property
    def description(self):
        """Obtains a description for the instance.

        If an associated record exists, its description is stored under the
        record.description attribute.

        Returns:
            str: The record.description attribute of an associated SeqRecord
                object if one exists, None otherwise.

        """
        if not self._record:
            return None
        return self._record.description


    @description.setter
    def description(self, value):
        """Prevents changing description attribute of associated SeqRecord.

        Raises:
            AttributeError: Raised on any set call.

        """
        raise AttributeError("Cannot change description of SeqRecord object")


    @description.deleter
    def description(self):
        """Prevents deleting description attribute of associated SeqRecord.

        Raises:
            AttributeError: Raised on any set call.

        """
        raise AttributeError("Cannot delete description of SeqRecord object")


    @property
    def seq(self):
        """Obtains the associated sequence for the instance.

        If an associated record exists, its sequence is stored under the
        record.seq attribute.

        Returns:
            obj: The record.seq attribute of an associated SeqRecord
                object if one exists, None otherwise.

        """
        if not self._record:
            return None
        return self._record.seq # Note: returns a Seq object


    @seq.setter
    def seq(self, value):
        """Prevents changing seq attribute of associated SeqRecord.

        Raises:
            AttributeError: Raised on any set call.

        """
        raise AttributeError("Cannot change sequence of SeqRecord object")


    @seq.deleter
    def seq(self):
        """Prevents deleting seq attribute of associated SeqRecord.

        Raises:
            AttributeError: Raised on any set call.

        """
        raise AttributeError("Cannot delete sequence of SeqRecord object")

