"""
This module contains a base class and two subclasses for writing output
to files.
"""

import os
import re

from scrollpy import config
from scrollpy.files import sequence_file
from scrollpy.util import _util


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
        self._sp_object = sp_object
        self._out_path = out_path


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
        # What we output depends on input object
        target_obj = self._sp_object
        # If ScrollPy/ScrollTree, want some number of sequences
        if isinstance(target_obj,ScrollPy) or isinstance(target_obj,ScrollTree):
            write_list = self._filter(mode='some')
            for group,seqs in write_list:
                outfile = self._get_filepath(
                        group,
                        seq_type='scrollsaw',
                        )
                sequence_file._sequence_list_to_file(
                        write_list,
                        outfile,
                        config['ARGS']['seqfmt'],  # User-specified
                        )
        # If Filter, want all removed sequences
        elif isinstance(target_obj,Filter):
            write_list = self._filter(mode='all')
            if removed_list:  # Not empty; filtering might not remove any
                for group,seqs in removed_list:
                    outfile = self._get_filepath(
                            group,
                            seq_type='filtered',
                            )
                    sequence_file._sequence_list_to_file(
                            write_list,
                            outfile,
                            config['ARGS']['seqfmt'],  # User-specified
                            )
        # If TreePlacer, want all classified sequences
        elif isinstance(target_obj,TreePlacer):
            write_list = self._filter(mode='all')
            if removed_list:
                for group,seqs in removed_list:
                    outfile = self._get_filepath(
                            group,
                            seq_type='classified',
                            )
                    sequence_file._sequence_list_to_file(
                            write_list,
                            outfile,
                            config['ARGS']['seqfmt'],  # User-specified
                            )
        # If none of these, raise error/log something
        else:
            pass  # Do something


    def _filter(self, mode='some'):
        """Returns only a number of sequences as specified by the user."""
        # Build up dictionary to return
        seqs = {}
        # If mode is 'some', need to filter
        if mode == 'some':
            counts = {}
            num_seqs = int(config['ARGS']['number']) # configparser uses ALL strings
            for obj in self._sp_object.return_ordered_seqs():
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
        # Otherwise, just get all
        elif mode == 'all':
            seqs = self._sp_object.return_all_seqs()

        return [(group,objs) for group,objs in seqs.items()]


    def _get_filepath(self, group, seq_type='scrollsaw'):
        """Returns an appropriate filepath"""
        # Probably just use an external method once that is written?
        no_clobber = bool(config['ARGS']['no_clobber'])
        sep = config['ARGS']['filesep']
        suffix = config['ARGS']['suffix']
        sformat = config['ARGS']['seqfmt']
        #assert isinstance(group, str) # this should eventually be a string!
        if (suffix == '') or (not isinstance(suffix, str)):
            basename = sep.join((str(group),seq_type))
        else:  # It is a string
            basename = sep.join((str(group),seq_type,suffix))
        if sformat == 'fasta':
            basename = basename + '.fa' # Need to make more flexible eventually
        else:
            pass  # TO-DO!!!
        filepath = os.path.join(self._out_path, basename)
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
        self._set_table_sep()  # Sets self._tblsep


    def write(self):
        """Writes values to file"""
        # Output based on object
        target_obj = self._sp_object
        # If ScrollPy/ScrollTree, want distance values
        if isinstance(target_obj,ScrollPy) or isinstance(target_obj,ScrollTree):
            lines = self._filter(mode='distance')
            outpath = self._get_filepath(table_type='scrollsaw')
            self._write(
                    lines,
                    outpath,
                    table_type='scrollsaw',
                    )
        # If Filter, want values seqs were filtered on
        elif isinstance(target_obj,Filter):
            lines = self._filter(mode='fvalue')
            outpath = self._get_filepath(table_type='filtered')
            self._write(
                    lines,
                    outpath,
                    table_type='filtered',
                    )
        # If TreePlacer, need to make two tables!
        elif isinstance(target_obj,TreePlacer):
            for value in ('monophyletic','notmonophyletic'):
                lines = self._filter(mode=value)
                outpath = self._get_filepath(table_type=value)
                self._write(
                        lines,
                        outpath,
                        table_type=value,
                        )
        # Else signal bad input
        else:
            pass  # Raise Error/log something


    def _write(self, lines, outpath, table_type):
        """Takes care of writing, including header columns"""
        # Get headers first
        if table_type == 'scrollsaw':
            header_list = [
                    'Sequence ID',
                    'Group',
                    'Distance',
                    ]
        elif table_type == 'filtered':
            header_list = [
                    'Sequence ID',
                    'Group',
                    'Filter value',
                    ]
        # Defined number of values
        elif table_type == 'monophyletic':
            header_list = [
                    'Sequence ID',
                    'Monophyly',
                    'Group',
                    'First Ancestor Support',
                    'Last Ancestor Node',
                    'Last Ancestor Support',
                    'Group Completeness',
                    'Sequence Status',
                    ]
        # More challenging, variable number of values
        elif table_type == 'notmonophyletic':
            header_list = [
                    'Sequence ID',
                    'Monophyly',
                    'First Ancestor Support',
                    'Number of Groups',
                    ]
            # I.e. how many groups are under any node?
            max_groups = self._get_max_groups(
                    lines,
                    4,  # Number of items before
                    3,  # Number of items per group
                    )
            # Make header columns for max number of groups
            for n in max_groups:
                header_list.extend.([
                        'Group{}'.format(n),
                        'Group{} Support'.format(n),
                        'Group{} Completeness'.format(n),
                        ])
        # Modify values based on tbl sep
        # Note, self._tblsep should be safely defined
        filtered = self._modify_values_based_on_sep(
                self._tblsep,
                *header_list,
                )
        # Join values safely using <sep>
        header = self._tblsep.join(filtered)
        # Then write lines
        with open(outpath,'w') as o:
            o.write(header)
            o.write('\n'*2)  # Leave a blank line
            for line in lines:
                o.write(line + '\n')


    def _filter(self, mode='distance'):
        """Fetches object values and returns a formatted list"""
        # Return a list of values regardless
        to_write = []  # Main list to return
        linevals = []  # List to accumulate intial values
        if mode == 'distance':
            for obj in self._sp_object.return_ordered_seqs():
                # Pick values
                header = obj.description
                group = obj._group # Problem to access directly?
                dist = obj._distance
                # Add to list
                lineval = (header, group, dist)  # Tuple
                linevals.append(lineval)
        elif mode == 'fvalue':
            # Object returns dict, not list -> flatten
            seqs = _util.flatten_dict_to_list(
                    self._sp_object.return_all_seqs())
            for obj in seqs:
                # Pick values
                header = obj.description
                group = obj._group
                fvalue = obj._fvalue  # Value based on filter metric
                # Add to list
                lineval = (header, group, fvalue)
                linevals.append(lineval)
        # Coming from TreePlacer, it is already a nested list
        elif mode == 'monophyletic':
            linevals = self._sp_object._monophyletic
        elif mode == 'notmonophyletic':
            linevals = self._sp_object._not_monophyletic

        # Filter all values and return
        for lineval in linevals:
            # Change values if they contain <sep>
            filtered = self._modify_values_based_on_sep(
                    self._tblsep,
                    *lineval,
                    )
            # Join values safely using <sep>
            to_write.append(self._tblsep.join(filtered))

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
            arg = str(arg)  # Needed for 'in' and also for writing
            if sep in arg:
                arg = re.sub(to_replace, replace_char, arg)
            new_values.append(arg)

        return new_values


    def _set_table_sep(self):
        """Utility function called during __init__"""
        # Separator dictated by format
        tblfmt = config['ARGS']['tblfmt']
        if tblfmt == 'csv':
            tblsep = ','
        elif tblfmt == 'space-delim':
            tblsep = ' '
        elif tblfmt == 'tab-delim':
            tblsep = '\t'
        else:
            # User-defined sep, if possible
            if tblfmt == 'sep':
                tblsep = config['ARGS']['tblsep']
                if not isinstance(tblsep, str):  # Invalid value for sep
                    # Log this eventually?!
                    tblsep = ','
            else:
                tblsep = ','
        # No return, just set instance value
        self._tblsep = tblsep


    def _get_filepath(self, table_type='scrollsaw'):
        """Returns an appropriate filepath"""
        # Probably just use an external method once that is written?
        no_clobber = bool(config['ARGS']['no_clobber'])
        sep = config['ARGS']['filesep']
        suffix = config['ARGS']['suffix']  # default ''
        #assert isinstance(group, str) # this should eventually be a string!
        if (suffix == '') or (not isinstance(suffix, str)):
            basename = sep.join(('scrollpy',table_type,'table'))
        else:  # It is a string
            basename = sep.join(('scrollpy',table_type,'table',suffix))
        if self._tblsep == ',':
            basename = basename + '.csv'
        else:
            basename = basename + '.txt' # Need to make more flexible eventually
        filepath = os.path.join(self._out_path, basename)
        if os.path.exists(filepath):
            if no_clobber:
                pass # DO SOMETHING
            else:
                pass # DO SOMETHING ELSE

        return filepath


    def _get_max_groups(self, lines, num_before, num_per_group):
        """Utility function; returns max number of expected groups"""
        max_groups = 0
        for item_list in lines:
            remaining = item_list[num_before:]
            num_groups = remaining/num_per_group
            if not num_groups.is_integer():  # I.e. whole number
                raise ValueError  # Expect whole number
            if num_groups > max_groups:
                max_groups = int(num_groups)

        return max_groups

