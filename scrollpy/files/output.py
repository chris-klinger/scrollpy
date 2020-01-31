"""
This module contains a base class and two subclasses for writing output
to files.
"""

import os
import re

from scrollpy import config
from scrollpy import scroll_log
from scrollpy import BraceMessage
from scrollpy.scrollsaw._aligniter import AlignIter
from scrollpy.scrollsaw._scrollpy import ScrollPy
from scrollpy.scrollsaw._scrolltree import ScrollTree
from scrollpy.scrollsaw._treeplacer import TreePlacer
from scrollpy.filter._new_filter import Filter
from scrollpy.files import sequence_file
from scrollpy.alignments import parser
from scrollpy.util import _util


# Get module loggers
(console_logger, status_logger, file_logger, output_logger) = \
        scroll_log.get_module_loggers(__name__)


class BaseWriter:
    """Base writing class from which other writing classes derive.

    Writers should expose a public method to write information, and have
    private methods for filtering data and obtaining an appropriate output
    file to write to.

    Args:
        sp_object (obj): A ScrollPy run object that has been previously
            called to fill its internal objects. Should be an instance of
            AlignIter, ScrollPy, ScrollTree, or TreePlacer.
        out_path (str): Full path to the dir/file to write. It is assumed
            that this path has already been validated.

    """
    def __init__(self, sp_object, out_path):
        self._sp_object = sp_object
        self._out_path = out_path


    def write(self):
        """Override in SubClass."""
        raise NotImplementedError

    def _filter(self):
        """Override in SubClass."""
        raise NotImplementedError

    def _get_filepath(self):
        """Override in SubClass."""
        raise NotImplementedError


class AlignWriter(BaseWriter):
    """SubClass of BaseWriter to handle writing alignments.

    Uses BioPython internally to write alignments in multiple formats.

    """
    def __init__(self, sp_object, out_path):
        """Delegate to BaseClass"""
        super().__init__(sp_object, out_path)
        # BaseWriter.__init__(self, sp_object, out_path)


    def write(self):
        """Obtain optimal alignment and write to file.

        Access the optimal alignment stored on AlignIter object through
        a public method and then call BioPython to write it to file.

        """
        target_obj = self._sp_object
        # If AlignIter, want optimal alignment
        if isinstance(target_obj,AlignIter):
            write_obj = target_obj.get_optimal_alignment()
            outfile = self._get_filepath(
                    'optimal',  # 'group'
                    align_type='alignment',
                    )
            parser.write_alignment_file(
                    write_obj,
                    outfile,
                    config['ARGS']['alignfmt'],  # User-specified
                    )
        # If none of these, raise error/log something
        else:
            # Raise an error as well? Or just log?
            scroll_log.log_message(
                    BraceMessage("{} object cannot be written "
                        "as alignment".format(type(target_obj))),
                    1,
                    'ERROR',
                    console_logger, file_logger,
                    )


    def _get_filepath(self, align_name, align_type):
        """Obtains the full path to an output file.

        Uses the name and type of the alignment to retrieve a filepath.

        If the output directory does not exist, create it unless the
        <no_create> config variable is set. If the output file exists,
        overwrite it unless the <no_clobber> config variable is set; if
        it is set, obtain a different filename instead.

        Args:
            align_name (str): Name to use for the output file.
            align_type (str): Format of the output alignment. For more
                details, see the BioPython Align.IO documentation.

        """
        # Probably just use an external method once that is written?
        no_clobber = bool(config['ARGS']['no_clobber'])
        sep = config['ARGS']['filesep']
        suffix = config['ARGS']['suffix']
        aformat = config['ARGS']['alignfmt']
        #assert isinstance(group, str) # this should eventually be a string!
        if (suffix == '') or (not isinstance(suffix, str)):
            basename = sep.join((str(align_name),align_type))
        else:  # It is a string
            basename = sep.join((str(align_name),align_type,suffix))
        if aformat == 'fasta':
            basename = basename + '.mfa' # Need to make more flexible eventually
        else:
            # Raise error?
            scroll_log.log_message(
                    BraceMessage("Unsupported alignment format {}".format(
                        aformat)),
                    1,
                    'ERROR',
                    console_logger, file_logger,
                    )
        filepath = os.path.join(self._out_path, basename)
        if os.path.exists(filepath):
            if no_clobber:
                dirname,filename = os.path.split(filepath)
                filepath = util.get_nonredundant_filepath(
                        dirname,
                        filename,
                        )
        return filepath


class SeqWriter(BaseWriter):
    """SubClass of BaseWriter to handle writing alignments.

    Uses BioPython internally to write alignments in multiple formats.

    """
    def __init__(self, sp_object, out_path):
        """Delegate to BaseClass."""
        super().__init__(sp_object, out_path)
        # BaseWriter.__init__(self, sp_object, out_path)


    def write(self):
        """Writes sequences to one or more output files.

        First filters sequences using internal _filter method, and then
        creates an output file for each group to write to.

        """
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
            for value in ('remaining','removed'):
                write_list = self._filter(mode=value)
                for group,seqs in write_list:
                    outfile = self._get_filepath(
                            group,
                            seq_type=value,
                            )
                    sequence_file._sequence_list_to_file(
                            write_list,
                            outfile,
                            config['ARGS']['seqfmt'],  # User-specified
                            )
        # If TreePlacer, want all classified sequences
        elif isinstance(target_obj,TreePlacer):
            write_list = self._filter(mode='classified')
            for group,seqs in write_list:
                outfile = self._get_filepath(
                        group,
                        seq_type='classified',
                        )
                sequence_file._sequence_list_to_file(
                        write_list,
                        outfile,
                        config['ARGS']['seqfmt'],  # User-specified
                        )
        else:
            # Raise error?
            scroll_log.log_message(
                    BraceMessage("{} object does not support writing "
                        "output sequences".format(type(target_obj))),
                    1,
                    'ERROR',
                    console_logger, file_logger,
                    )


    def _filter(self, mode='some'):
        """Returns only a number of sequences as specified by the user.

        User has the option to limit the number of sequences output for
        group using the <number> config parameter.

        Args:
            mode (str, optional): If specified, controls which sequences
                to retrieve for writing. Possible options are <some>,
                <remaining>, <removed>, and <classified>. Defaults to some.

        Returns:
            list: A list of [group,[ScrollSeqObjs]] pairs to write.

        """
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
        elif mode == 'remaining':
            seqs = self._sp_object.return_remaining_seqs()
        elif mode == 'removed':
            seqs = self._sp_object.return_removed_seqs()
        elif mode == 'classified':
            seqs = self._sp_object.return_classified_seqs()

        return [(group,objs) for group,objs in seqs.items()]


    def _get_filepath(self, group, seq_type='scrollsaw'):
        """Obtains the full path to an output file.

        Uses the name and type of the alignment to retrieve a filepath.

        If the output directory does not exist, create it unless the
        <no_create> config variable is set. If the output file exists,
        overwrite it unless the <no_clobber> config variable is set; if
        it is set, obtain a different filename instead.

        Args:
            align_name (str): Name to use for the output file.
            align_type (str): Format of the output alignment. For more
                details, see the BioPython Align.IO documentation.

        """
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
            scroll_log.log_message(
                    BraceMessage("Unsupported sequence format {}".format(
                        aformat)),
                    1,
                    'ERROR',
                    console_logger, file_logger,
                    )
        filepath = os.path.join(self._out_path, basename)
        if os.path.exists(filepath):
            if no_clobber:
                dirname,filename = os.path.split(filepath)
                filepath = util.get_nonredundant_filepath(
                        dirname,
                        filename,
                        )
        return filepath


class TableWriter(BaseWriter):
    """SubClass of BaseWriter to handle writing alignments.

    Uses BioPython internally to write alignments in multiple formats.

    """
    def __init__(self, sp_object, out_path):
        """Delegate to BaseClass.

        Unlike other SubClasses, TableWriter also calls a single internal
        function to set the self._tblsep attribute.

        """
        super().__init__(sp_object, out_path)
        # BaseWriter.__init__(self, sp_object, out_path)
        self._set_table_sep()  # Sets self._tblsep


    def write(self):
        """Writes table values to a file.

        Depending on the type of run object provided as input, obtain
        different information by calling internal _filter method. Then
        create an output file and write lines to it.

        """
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
                if lines:  # Not every analysis will have both
                    outpath = self._get_filepath(table_type=value)
                    self._write(
                            lines,
                            outpath,
                            table_type=value,
                            )
        # If AlignIter, want information on alignments itered over
        elif isinstance(target_obj,AlignIter):
            lines = self._filter(mode='aligniter')
            outpath = self._get_filepath(table_type='aligniter')
            self._write(
                    lines,
                    outpath,
                    table_type='aligniter',
                    )
        else:
            # Raise error?
            scroll_log.log_message(
                    BraceMessage("{} object does not support writing "
                        "output table(s)".format(type(target_obj))),
                    1,
                    'ERROR',
                    console_logger, file_logger,
                    )


    def _write(self, lines, outpath, table_type):
        """Called by write to actually write table values to file.

        Extra layer of abstraction to handle writing header lines to each
        column of the table file.

        Args:
            lines (list): Pre-formatted lines to write.
            outpath (str): Full path to the target output file.
            table_type (str): Which form of table is required; controls
                how headers are written. Possible options are <scrollsaw>,
                <filtered>, <monophyletic>, and <notmonophyletic>.

        """
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
            for n in range(max_groups):
                header_list.extend([
                        'Group{}'.format(n+1),
                        'Group{} Support'.format(n+1),
                        'Group{} Completeness'.format(n+1),
                        ])
        # Back to fixed number of values
        elif table_type == 'aligniter':
            header_list = [
                    'Iteration',
                    'Alignment Length',
                    'Low Column Score',
                    'Tree Support',
                    'Optimal',
                    ]
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
        """Fetches object values and returns a formatted list.

        Depending on what values are requested, obtain them from run
        object and then ensure that any values corresponding to the
        table separator are sanitized prior to passing to write().

        Args:
            mode (str): Corresponds to the input run object. Possible
                values are <distance>, <fvalue>, <monophyletic>,
                <notmonophyletic>, and <aligniter>. Defaults to distance.

        Returns:
            list: A list of [header<sep>group<sep>distance] values.

        """
        # Return a list of values regardless
        to_write = []  # Main list to return
        linevals = []  # List to accumulate intial values
        if mode == 'distance':
            for obj in self._sp_object.return_ordered_seqs():
                # Pick values
                # Description may or may not be available
                header = None
                try:
                    header = obj.description
                except AttributeError:
                    # Backup -> try to get TreeNode name
                    try:
                        # Should delegate for either Leaf or ScrollSeq?
                        header = obj.name
                        # header = obj._node.name
                    except AttributeError:
                        scroll_log.log_message(
                                BraceMessage("Could not identify accession "
                                    "for {}".format(obj)),
                                2,
                                'WARNING',
                                file_logger,
                                )
                if not header:
                    header = 'N/A'
                # These should always be available
                # If not, AttributeError is raised -> should log!!!
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
        # For AlignIter, allow object to return list
        elif mode == 'aligniter':
            linevals = self._sp_object.iter_info

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
        """Sanitizes values based on separator.

        User defines a separator character for table output, which may be
        present in some output values. As this would make subsequent
        parsing of the table file difficult, replace each instance of the
        separator with a different value.

        The replacement character is chosen from a list as the first
        character which is not the separator in the order ' ', '_', ',',
        '|', '\t'.

        Args:
            sep (str): Separator for the table.
            *args: Iterable of values to sanitize.

        Returns:
            list: A list of values in *args, with each instance of the
                table separator replaced.

        """
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
        """Obtain the table separator based on config values.

        This is a utility function called during instantiation that uses
        the <tblfmt> config value to set self._tblsep.

        """
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
                    scroll_log.log_message(
                            BraceMessage("Specified table separator {} "
                                "is invalid; defaulting to CSV format".format(
                                    tblsep)),
                                2,
                                'WARNING',
                                console_logger, file_logger,
                                )
                    tblsep = ','
            else:
                tblsep = ','
        # No return, just set instance value
        self._tblsep = tblsep


    def _get_filepath(self, table_type='scrollsaw'):
        """Obtains the full path to an output file.

        Uses the name and type of the alignment to retrieve a filepath.

        If the output directory does not exist, create it unless the
        <no_create> config variable is set. If the output file exists,
        overwrite it unless the <no_clobber> config variable is set; if
        it is set, obtain a different filename instead.

        Args:
            align_name (str): Name to use for the output file.
            align_type (str): Format of the output alignment. For more
                details, see the BioPython Align.IO documentation.

        """
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
                dirname,filename = os.path.split(filepath)
                filepath = util.get_nonredundant_filepath(
                        dirname,
                        filename,
                        )
        return filepath


    def _get_max_groups(self, lines, num_before, num_per_group):
        """Returns the maxinum number of groups under all nodes.

        This function is called when writing output for non-monophyletic
        node classifications, where the number of groups under a parent
        node can be variable.

        Args:
            num_before (int): The number of entries in a given list of
                values that are common to all lists.
            num_per_group (int): The number of entries that correspond to
                a single entity (i.e. node).

        Returns:
            int: The maximum number of groups that will be written.

        """
        max_groups = 0
        for item_list in lines:
            remaining = item_list[num_before:]
            num_groups = remaining/num_per_group
            if not num_groups.is_integer():  # I.e. whole number
                raise ValueError  # Expect whole number
            if num_groups > max_groups:
                max_groups = int(num_groups)

        return max_groups

