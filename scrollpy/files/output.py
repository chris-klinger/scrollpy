"""
This module contains a base class and two subclasses for writing output
to files.
"""

import os
import re

from scrollpy import config
from scrollpy.files import sequence_file

class BaseWriter:
    """Base writing class from which other writing classes derive.

    Args:
        sp_object (obj): either a ScrollPy or ScrollTree object to use
            for writing information.

        out_path (str): full path to the dir/file to write. Assumed that
            this path has already been checked (exists/is valid).

    Methods:
        write():
            Args:
                (self)

            Returns:
                raises NotImplementedError (sublass overrides)

        _filter():
            Args:
                (self)

            Returns:
                raises NotImplementedError (sublass overrides)
    """
    def __init__(self, sp_object, out_path):
        self.sp_object = sp_object
        self.out_path = out_path


    def write(self):
        raise NotImplementedError


    def _filter(self):
        raise NotImplementedError


class SeqWriter(BaseWriter):
    """SeqWriter subclass of BaseWriter baseclass.

    Methods:
        write():
            Args:
                (self)

            Returns:
                calls filter to return a list of ScrollSeq objects.
                    Creates an output file for each group and writes.

        _filter():
            Args:
                (self)

            Returns:
                returns a list of [group,[ScrollSeqObjs]] pairs to use
                    for writing.
    """
    def __init__(self, sp_object, out_path):
        BaseWriter.__init__(self, sp_object, out_path)


    def write(self):
        """Filters sequences and writes to one or more files."""
        write_list = self._filter()
        for group,seqs in write_list:
            outfile = self._get_filepath(group)
            sequence_file._sequence_list_to_file(
                    seqs,
                    outfile,
                    config['ARGS']['seqfmt']) # User-specified


    def _filter(self):
        """Returns only a number of sequences as specified by the user."""
        counts = {}
        seqs = {}
        num_seqs = int(config['ARGS']['number']) # configparser uses ALL strings
        for obj in self.sp_object.return_ordered_seqs():
            group = obj._group
            try:
                counts[group] += 1
                count = counts[group]
            except KeyError:
                count = 1 # first time
                counts[group] = count
            if count <= num_seqs:
                try:
                    seqs[group].append(obj)
                except KeyError:
                    seqs[group] = []
                    seqs[group].append(obj)
        return [(group,objs) for group,objs in seqs.items()]


    def _get_filepath(self, group):
        """Returns an appropriate filepath"""
        # Probably just use an external method once that is written?
        no_clobber = bool(config['ARGS']['no-clobber'])
        sep = config['ARGS']['filesep']
        suffix = config['ARGS']['suffix']
        if not suffix:
            suffix = ''
        #assert isinstance(group, str) # this should eventually be a string!
        basename = sep.join((str(group), 'sequences', suffix))
        basename = basename + '.fa' # Need to make more flexible eventually
        filepath = os.path.join(self.out_path, basename)
        if os.path.exists(filepath):
            if no_clobber:
                pass # DO SOMETHING
            else:
                pass # DO SOMETHING ELSE
        return filepath


class TableWriter(BaseWriter):
    """TableWriter subclass of BaseWriter baseclass.

    Methods:
        write():
            Args:
                (self)

            Returns:
                calls filter to return a list of lines to write.
                    Open the output file and writes the lines.

        _filter():
            Args:
                (self)

            Returns:
                returns a list: [header<sep>group<sep>distance]
    """
    def __init__(self, sp_object, out_path):
        BaseWriter.__init__(self, sp_object, out_path)


    def write(self):
        """Writes values to file"""
        lines = self._return()
        with open(self.out_path,'w') as o:
            for line in lines:
                o.write(line + "\n")


    def _filter(self):
        """Fetches object values and returns a formatted list"""
        to_write = []
        sep = config['ARGS']['tblsep']
        for obj in self.sp_object.return_ordered_seqs():
            header = obj.description
            group = obj._group # Problem to access directly?
            dist = obj._distance
            linevals = (header, group, dist)
            # Change values if they contain <sep>
            filtered = self._modify_values_based_on_sep(sep, *linevals)
            # Join values safely using <sep>
            to_write.append(sep.join(filtered))
        return to_write


    def _modify_values_based_on_sep(self, sep, *args):
        """Checks each value for presence of sep and changes accordingly"""
        new_values = []
        # Do we need more than two?
        ordered_chars = (' ', '_', ',', '|', '\t')
        to_replace = re.compile(str(sep))
        for char in ordered_chars:
            if char not in sep:
                replace_char = char
                break
        for arg in args:
            if sep in arg:
                arg = re.sub(to_replace, replace_char, arg)
            new_values.append(arg)
        return new_values

