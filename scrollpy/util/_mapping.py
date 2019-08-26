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
from contextlib import suppress

from scrollpy import config
from scrollpy.files import sequence_file as sf
from scrollpy.files import tree_file as tf
from scrollpy.sequences._scrollseq import ScrollSeq
from scrollpy.sequences._leafseq import LeafSeq
from scrollpy.util._util import non_blank_lines


class Mapping:
    """A class to create a single seq_dict object from input files.

    Args:
        infiles (iter): path(s) to one or more input files

        treefile (str): path to a tree file (default: None)

        mapfile (str): path to a mapping file (default: None)
    """
    # Class var list
    _config_vars = ('infmt', 'treefmt')

    def __init__(self, *infiles, treefile=None, mapfile=None, **kwargs):
        self._infiles = infiles
        self._treefile = treefile
        self._mapfile = mapfile
        # Optional vars or in config
        for var in _config_vars:
            try:
                value = kwargs[var]
            except KeyError:
                value = configs['ARGS'][var]
            self.setattr(var, value)
        # Internal counter
        self._counter = 1
        # Internal defaults
        self._records = {}
        self._record_list = []
        self._seq_descriptions = []
        self._leaves = []
        self._leaf_names = []
        self._mapping = {}
        self._seq_dict = {}
        # Internal structures for tracking mapped labels
        self._found_seqs = set()
        self._found_leaves = set()
        self._duplicates = set()


    def __call__(self):
        """Run internal functions to create an internal _seq_dict object"""
        # Parse input files
        self._parse_infiles()
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
            pass  # Do something!!!
        # Return seq dict
        return self._seq_dict()


    def _parse_infiles(self):
        """Parse files into record objects"""
        for filepath in self._infiles:
            # Get group from filename
            group = os.path.basename(file_path).split('.',1)[0]
            if not len(group) > 0:  # This should never happen in reality
                raise ValueError  # Mapping cannot be completed
            # Filepaths are unique, but group names are not guaranteed to be
            group = _unique_group_name(group)
            # Get SeqRecords using BioPython
            records = sf._get_sequences(
                    file_path,
                    self.infmt,
                    )
            for record in records:
                try:
                    self._records[group].append(record.description)
                except KeyError:
                    self._records[group] = []
                    self._records[group].append(record.description)
                # Keep flat objects as well
                self._records.append(record)
                self._seq_descriptions.append(record.description)


    def _unique_group_name(group, counter=1, seen=set()):
        """Utility function to ensure group names are unique.

        Args:
            group (str): group name; must be hashable

        Returns:
            unique group name
        """
        group = str(group)  # In case it is an int
        if group not in seen
            seen.add(group)
            return group
        else:
            if counter == 1: # First time, add
                group = group + '.' + str(counter)
            if counter > 1:
                group_basename = group.split('.',1)[0] # In case it is an int
                group = group_basename + '.' + str(counter) # <group>.<num>
            counter += 1
            return _unique_group_name(group, counter)


    def _parse_treefile(self):
        """Parse tree file, if it exists"""
        tree = tf.read_tree(
                self._treefile,
                self.treefmt,
                )
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
        for line in non_blank_lines(self._map_file):
            map_id,group = line.split('\t')
            try:
                self._mapping[group].append(map_id)
            except KeyError:
                self._mapping[group] = []
                self._mapping[group].append(map_id)


    def _create_mapping_from_seqs(self):
        """Alias internal records dict as self._mapping"""
        self._mapping = self._records  # Just alias


    def _create_seq_dict(self):
        """Creates a seq_dict based on a mapping"""
        for group,labels in self._mapping.items():
            self._seq_dict[group] = []
            for label in labels:
                try:
                    scrollseq_obj = None
                    leafseq_obj = None
                    with suppress(KeyError):  # Try to get ScrollSeq obj
                        scrollseq_obj = self._get_scrollseq(
                            group=group,
                            label=label,
                            )
                    with suppress(KeyError):  # Try to get LeafSeq obj
                        leafseq_obj = self._get_leafseq(
                            group=group,
                            label=label,
                            )
                    # Increment counter after making all objects
                    self._counter += 1
                    # Associate Seq with Leaf, if Leaf exists
                    if leafseq_obj:
                        leafseq_obj._seq = scrollseq_obj
                        self._seq_dict[group].append(leafseq_obj)
                    else:
                        self._seq_dict[group].append(scrollseq_obj)
                except ValueError:  # Indicates a duplicate sequence
                    self._duplicates.add(label)


    def _get_scrollseq(self, group, label):
        """Tries to retrieve a SeqRecord object by label; if successful,
        build an associated ScrollSeq object and return it.
        """
        if not self._record_list:  # Empty list; no records
            raise KeyError  # Caught by handling function
        else:
            matched_seq = get_best_name_match(label, self._seq_descriptions)
            if matched_seq in self._found_seqs:
                raise ValueError  # Indicates duplicate
            # Otherwise, get associated record by index
            index = self._seq_descriptions.index(matched_seq)
            record = self._record_list[index]
            # Add to seen
            self._found_seqs.add(matched_seq)
            # Make and return
            return ScrollSeq(
                    id_num = self._counter,
                    group = group,
                    seq_record = record,
                    )


    def _get_leafseq(self, group, label):
        """Tries to retrieve a TreeNode object by label; if successful,
        build an associated LeafSeq object and return it.
        """
        if not self._leaves:  # No associated tree object
            raise KeyError
        else:
            matched_leaf = get_best_name_match(label, self._leaf_names)
            if matched_leaf in self._found_leaves:
                raise ValueError
            # Otherwise, get associated node by index
            index = self._leaf_names.index(matched_leaf)
            node = self._leaves[index]
            # Add to seen
            self._found_leaves.add(matched_leaf)
            # Make and return
            return LeafSeq(
                    id_num = self._counter,
                    group = group,
                    tree_node = node,
                    )


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
        pairs = []
        for name in name_set:
            if len(name) == len(target_name):
                pairs.append((target_name,name))
            else:  # Harder, try to align
                pass

