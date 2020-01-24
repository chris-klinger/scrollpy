"""
This module contains code for obtaining various mappings in ScrollPy.

The end-goal of the process is to obtain a 'seq_dict' object that contains
{group:[<objects>],} entries, where the objects are either LeafSeq or
ScrollSeq objects. In cases where both a treefile and one or more sequence
files are provided, each LeafSeq object can also have a single ScrollSeq
object.

Mapping should fail unless a pure 1-to-1 relationship between:
    -labels specified in a mapfile and either tree labels or sequence
    desriptions
    -tree tip labels and sequence desriptions (if provided)

can be established; i.e. no partial data structures should exist.
"""

import os
import sys  # Temporarily
from contextlib import suppress

from scrollpy import config
from scrollpy import scroll_log
from scrollpy import DuplicateSeqError
from scrollpy import FatalScrollPyError
from scrollpy.files import sequence_file as sf
from scrollpy.alignments import parser as af
from scrollpy.files import tree_file as tf
from scrollpy.sequences._scrollseq import ScrollSeq
from scrollpy.sequences._leafseq import LeafSeq
from scrollpy.util._util import non_blank_lines
from scrollpy.util._align import affine_align,simple_score
from scrollpy.util._counter import Counter


# Get module loggers
(console_logger, status_logger, file_logger, output_logger) = \
        scroll_log.get_module_loggers(__name__)


class Mapping:
    """A class to create a single seq_dict object from input files.

    Args:
        infiles (iter): path(s) to one or more input files

        alignfile (str): path to an alignment file (default: None)

        treefile (str): path to a tree file (default: None)

        mapfile (str): path to a mapping file (default: None)
    """
    # Class var list
    _config_vars = (
            'infmt',
            'alignfmt',
            'treefmt',
            )

    def __init__(self, infiles, alignfile=None, treefile=None, mapfile=None, **kwargs):
        self._infiles = infiles
        self._alignfile = alignfile
        self._treefile = treefile
        self._mapfile = mapfile
        # Optional vars or in config
        for var in self._config_vars:
            try:
                value = kwargs[var]
            except KeyError:
                value = config['ARGS'][var]
            setattr(self, var, value)
        # Keep kwargs for __repr__
        self.kwargs = kwargs
        # Internal counter
        self._counter = Counter()
        # Internal defaults
        self._records = {}
        self._record_list = []
        self._seq_descriptions = []
        self._align_records = []
        self._align_descriptions = []
        self._tree_obj = None
        self._leaves = []
        self._leaf_names = []
        self._mapping = {}
        self._seq_dict = {}
        # Internal structures for tracking mapped labels
        self._found_seqs = set()
        self._found_leaves = set()
        self._duplicates = set()
        # Test var
        try:
            self._test = kwargs['test']
        except KeyError:
            self._test = False  # False by default


    def __repr__(self):
        return "{}({!r}, {!r}, {!r}, {!r}, **{!r})".format(
                self.__class__.__name__,
                self._infiles,
                self._alignfile,
                self._treefile,
                self._mapfile,
                self.kwargs,
                )

    def __str__(self):
        # Determine num of each
        num_infiles = len(self._infiles)
        num_alignfiles = 1 if self._alignfile else 0
        num_treefiles = 1 if self._treefile else 0
        num_mapfile = 1 if self._mapfile else 0
        # Report numbers in __str__
        return "{} with {} input files, {} alignment file(s), "
            "{} tree file(s), and {} mapping file(s)".format(
                self.__class__.__name__,
                num_infiles,
                num_alignfiles,
                num_treefiles,
                num_mapfiles,
                )

    def __call__(self):
        """Run internal functions to create an internal _seq_dict object"""
        # Parse input files
        self._parse_infiles(self._test)
        if self._alignfile:
            self._parse_alignfile()
        if self._treefile:
            self._parse_treefile()
        # Create a mapping
        if self._mapfile:
            self._create_mapping_from_mapfile()
        elif self._infiles:
            self._create_mapping_from_seqs()
        else:
            self._create_mapping_from_tree()
        # Populate seq_dict based on mapping
        self._create_seq_dict()
        # Check to make sure no duplicates were found
        if self._duplicates:
            for label in self._duplicates:
                scroll_log.log_message(
                        scroll_log.BraceMessage(
                            "Found duplicate sequence {} while creating mapping", label),
                        1,
                        'ERROR',
                        console_logger, file_logger,
                        )
            scroll_log.log_message(
                    scroll_log.BraceMessage(
                        "FATAL -> found duplicate sequence(s) in input"),
                    1,
                    'ERROR',
                    console_logger, file_logger,
                    )
            raise FatalScrollPyError
        # Return seq dict
        return self._seq_dict


    def _parse_infiles(self, _test=False):
        """Parse files into record objects"""
        for filepath in self._infiles:
            # Get group from filename
            group = os.path.basename(filepath).split('.',1)[0]
            if not len(group) > 0:  # This should never happen in reality
                scroll_log.log_message(
                        scroll_log.BraceMessage(
                            "FATAL -> could not identify group for mapping"),
                        1,
                        'ERROR',
                        console_logger, file_logger,
                        )
                raise FatalScrollPyError
            # Filepaths are unique, but group names are not guaranteed to be
            if _test:
                group = _unique_group_name(group, seen={})
            else:
                group = _unique_group_name(group)
            # Get SeqRecords using BioPython
            records = sf._get_sequences(
                    filepath,
                    self.infmt,
                    )
            for record in records:
                desc = record.description
                try:
                    self._records[group].append(desc)
                except KeyError:
                    self._records[group] = []
                    self._records[group].append(desc)
                # Keep flat objects as well
                self._record_list.append(record)
                self._seq_descriptions.append(desc)


    def _parse_alignfile(self):
        """Parse an alignment file into record objects"""
        alignment = af.parse_alignment_file(
                self._alignfile,
                self.alignfmt,
                to_dict=False,  # Return raw Align object
                )
        self._align_records = [record for record in alignment]
        self._align_descriptions = [record.description for
                record in self._align_records]


    def _parse_treefile(self):
        """Parse tree file, if it exists"""
        tree = tf.read_tree(
                self._treefile,
                self.treefmt,
                )
        self._tree_obj = tree
        self._leaves = [leaf for leaf in tree]
        self._leaf_names = [leaf.name for leaf in self._leaves]


    def _create_mapping_from_mapfile(self):
        """Parses a mapping file and returns a dict.

        Args:
            map_file (str): filepath to mapping file with expected format
                <id><tab><group>

        Returns:
            a mapping dict of group:[<labels>] pairs
        """
        for line in non_blank_lines(self._mapfile):
            line = line.strip('\n')  # Remove newlines
            map_id,group = line.split('\t')
            map_id = map_id.rstrip()  # Trailing whitespace
            group = group.rstrip()  # Trailing whitespace
            try:
                self._mapping[group].append(map_id)
            except KeyError:
                self._mapping[group] = []
                self._mapping[group].append(map_id)


    def _create_mapping_from_seqs(self):
        """Alias internal records dict as self._mapping"""
        self._mapping = self._records  # Just alias


    def _create_mapping_from_tree(self):
        """Simple mapping, one group and all tree labels"""
        group = os.path.basename(self._treefile).split('.',1)[0]
        if not len(group) > 0:  # This should never happen in reality
                scroll_log.log_message(
                        scroll_log.BraceMessage(
                            "FATAL -> could not identify group for mapping"),
                        1,
                        'ERROR',
                        console_logger, file_logger,
                        )
                raise FatalScrollPyError
        self._mapping[group] = self._leaf_names  # Alias leaf labels


    def _create_seq_dict(self, log=False):
        """Creates a seq_dict based on a mapping"""
        for group,labels in self._mapping.items():
            self._seq_dict[group] = []
            for label in labels:
                scroll_log.log_message(
                        scroll_log.BraceMessage(
                            "Matching label {} to mapping",label),
                        2,
                        'INFO',
                        file_logger,
                        )
                try:
                    scrollseq_obj = None
                    leafseq_obj = None
                    with suppress(KeyError):
                        # LeafSeq objects
                        leafseq_obj = self._get_leafseq(
                            group=group,
                            label=label,
                            )
                    # Can't nest this all in one 'with' block?
                    with suppress(KeyError):
                        # Sequences can come from alignment and/or seqfiles
                        if self._alignfile:
                            scrollseq_obj = self._get_alignseq(
                                    group=group,
                                    label=label,
                                    )
                        else:
                            scrollseq_obj = self._get_scrollseq(
                                group=group,
                                label=label,
                                )
                    # Increment counter after making all objects
                    self._counter()  # Calling increases count
                    # Associate Seq with Leaf, if Leaf exists
                    if leafseq_obj:
                        leafseq_obj._seq = scrollseq_obj
                        self._seq_dict[group].append(leafseq_obj)
                    else:
                        self._seq_dict[group].append(scrollseq_obj)
                # except ValueError:  # Indicates a duplicate sequence
                except DuplicateSeqError:
                    self._duplicates.add(label)


    def _get_alignseq(self, group, label):
        """Tries to retrieve a SeqRecord object from within a Bio.Align
        object by label; if successful, build a ScrollSeq object.

        May want to strip the gap characters eventually, but for now
        just leave it, as it is unclear if there is any reason to.
        """
        if not self._align_records:
            raise KeyError  # Caught by handling function
        else:
            matched_seq = get_best_name_match(
                    label,
                    self._align_descriptions,  # Desc attr of all align records
                    )
            if matched_seq in self._found_seqs:  # Uses same as seqfiles
                # Duplicate mapping; not allowed
                raise DuplicateSeqError(label)  # Caught by handling function
                # raise ValueError  # Caught by handling function
            # Otherwise, get associated record
            index = self._align_descriptions.index(matched_seq)
            record = self._align_records[index]
            # Add to seen
            self._found_seqs.add(matched_seq)
            # Make and return
            return ScrollSeq(
                    id_num = self._counter.current_count(),
                    group = group,
                    seq_record = record
                    )


    def _get_scrollseq(self, group, label):
        """Tries to retrieve a SeqRecord object by label; if successful,
        build an associated ScrollSeq object and return it.
        """
        if not self._record_list:  # Empty list; no records
            raise KeyError  # Caught by handling function
        else:
            matched_seq = get_best_name_match(label, self._seq_descriptions)
            if matched_seq in self._found_seqs:
                # Duplicate mapping
                raise DuplicateSeqError(label)  # Caught by handling function
                # raise ValueError  # Caught by handling function
            # Otherwise, get associated record by index
            index = self._seq_descriptions.index(matched_seq)
            record = self._record_list[index]
            # Add to seen
            self._found_seqs.add(matched_seq)
            # Make and return
            return ScrollSeq(
                    id_num = self._counter.current_count(),
                    group = group,
                    seq_record = record,
                    )


    def _get_leafseq(self, group, label):
        """Tries to retrieve a TreeNode object by label; if successful,
        build an associated LeafSeq object and return it.
        """
        if not self._leaves:  # No associated tree object
            raise KeyError  # Caught by handling function
        else:
            # print("Looking for {}".format(label))
            matched_leaf = get_best_name_match(label, self._leaf_names)
            # print("Matched leaf is {}".format(matched_leaf))
            if matched_leaf in self._found_leaves:
                # Duplicate mapping
                raise DuplicateSeqError(label)  # Caught by handling function
                # raise ValueError # Caught by handling function
            # Otherwise, get associated node by index
            index = self._leaf_names.index(matched_leaf)
            node = self._leaves[index]
            # Add to seen
            self._found_leaves.add(matched_leaf)
            # Make and return
            return LeafSeq(
                    id_num = self._counter.current_count(),
                    group = group,
                    tree_node = node,
                    )


def _unique_group_name(group, seen={}):
        """Utility function to ensure group names are unique.

        Args:
            group (str): group name; must be hashable

        Returns:
            unique group name
        """
        group = str(group)  # In case it is an int
        if group not in seen.keys():
            seen[group] = 1
            return group
        else:
            # Copy group var before rest of else block changes it
            orig_group = group
            counter = seen[group]
            if counter == 1: # First time, add
                group = group + '.' + str(counter)
            elif counter > 1:
                group_basename = group.split('.',1)[0] # In case it is an int
                group = group_basename + '.' + str(counter) # <group>.<num>
            counter += 1
            # Update counter for the original group name only!
            seen[orig_group] = counter
            return _unique_group_name(group)


def get_best_name_match(target_name, name_set):
    """Find the best match between target_name and each name in a list.

    Try the fastest approach first: membership testing. Otherwise, compare
    between names to find the best match. If the length is unequal, tries
    to align first using a simple binary match/no match scoring scheme.
    Then iters through zipped name pair and calculates a sore.

    Args:
        target_name (str): name to find a match for

        name_set (set): all possible names to search

    Returns:
        best match in name_set for target_name
    """
    # Easiest case -> membership testing
    if target_name in name_set:
        return target_name
    else:  # Harder, find best match overall
        unaligned,aligned = _make_aligned_seq_pairs(
                target_name, name_set)
        # Go through each
        best_pair = compare_pairs(aligned)
        best_index = aligned.index(best_pair)
        _,best_name = unaligned[best_index]
        return best_name


def _make_aligned_seq_pairs(target_name, name_set):
    """Creates a list of aligned names for comparison.

    Pairs are left as-is if they are the same length; otherwise, they
    are aligned using a simple identity-based metric.

    Args:
        target_name (str): name to match/align to

        name_set (set): all possible names to search

    Returns:
        a list of original and matched/aligned names for comparison
    """
    unaligned = []
    aligned = []
    for name in name_set:
        # No matter what add to unaligned
        unaligned.append((target_name,name))
        if len(name) == len(target_name):
            # Easy, just append
            aligned.append((target_name,name))
        else:  # Harder, try to align
            aligned1,aligned2 = affine_align(
                    seq1=target_name,
                    seq2=name,
                    score_func=simple_score,
                    )
            aligned.append((aligned1,aligned2))
    return unaligned,aligned


def compare_pairs(seq_pairs):
    """Returns the highest scoring pair among pairs"""
    best_pair = None
    high_score = 0
    for s1,s2 in seq_pairs:
        score = 0
        for r1,r2 in zip(s1,s2):  # Same length; pairwise comp
            score += simple_score(r1,r2)
        if score > high_score:
            high_score = score
            best_pair = (s1,s2)
    return best_pair

