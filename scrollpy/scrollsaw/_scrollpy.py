"""
This module contains the main ScrollPy object.
"""

import os
from itertools import combinations

from scrollpy.files import sequence_file as sf
from scrollpy.sequences._scrollseq import ScrollSeq
from scrollpy.sequence._collection import ScrollCollection
#from scrollpy.util import _util

class ScrollPy:
    """Main ScrollPy object; based on user input, run is variable.

    Args:
        target_dir (str): path to target directory for main output file.

        align_method (str): string denoting alignment method to use.
            Allowed values are: `Muscle`, `ClustalW`, `ClustalOmega`,
            `Prank`,`Mafft`,`Dialign`,`Probcons`,`Tcoffee`,`MSAProbs`,
            `Generic`.

        dist_method (str): string denoting distance calculation method
            to use. Allowed values are: `RAxML`,`PhyML`,`Generic`.

        pre_filter (bool): if True, combines all sequences and performs an
            initial filtering step that removes short sequences.
            Default: False.

        filter_method (str): string denoting filtering method to use.

        pre_split (bool): if True and only one input file provided, splits
            the sequences into several smaller groups before calculating
            distances based on pairwise similarity. Default: False.

        file_format (str): Format for input files

        *infiles (list): one or more files to use.

    """

    def __init__(self, target_dir, align_method, dist_method,
            pre_filter=False, filter_method=None, pre_split=False,
            file_format="fasta", *infiles):
        self.target_dir = target_dir
        self.align_method = align_method
        self.dist_method = dist_method
        self.pre_filter = pre_filter
        self.filter_method = filter_method
        self.pre_split = pre_split
        self.file_format = file_format
        if len(infiles) > 0:
            self.infiles = list(infiles)
        else:
            pass
            #raise some Error
        self._seq_dict = {}
        self._ordered_seqs = []
        self._groups = []
        self._group_counter = 1 # (possibly unused) counter for group IDs
        self._removed = [] # list of ScrollSeq objects removed
        self._id_counter = 1 # counter for creating unique sequence ids
        self._collections = []


    #def __str__(self):
    #    """TO-DO"""
    #    pass

    #def __repr__(self):
    #    """TO-DO"""
    #    pass

    def __call__(self):
        """Runs Scrollsaw"""
        pass # TO-DO


    def _parse_infiles(self):
        """Reads infiles to create ScrollSeq objects.

        Assumes that the input files have already been checked and are
        appropriate (no duplicates/empty/non-existent files).

        Args:
            (self.infiles)

        Returns:
            modifies internal _seq_dict and _groups variables
        """
        for file_path in self.infiles:
            group = os.path.basename(file_path).split('.',1)[0]
            if not len(group) > 0: # This should never happen in reality
                group = self._group_counter
                self._group_counter += 1
            # Files are unique, but need to check groups; two different
            # filepaths could lead to the same group name
            group = self._unique_group_name(group)
            # Now get SeqRecords using BioPython
            records = sf._get_sequences(file_path, self._file_format)
            scroll_seqs = self._make_scroll_seqs(file_path, group, records)
            # Update internal objects
            self._groups.append(group)
            self._seq_dict[group] = scroll_seqs


    def _unique_group_name(self, group, counter=0):
        """Utility function to ensure group names are unique.

        Args:
            group (str): group name

        Returns:
            unique group name
        """
        if group not in self._groups:
            return group
        else:
            counter += 1
            group_basename = group.split('_',1)[0]
            group = str(group_basename) + '_' + str(counter) # <group>_<num>
            return self._unique_group_name(group, counter)


    def _make_scroll_seqs(self, infile, group, *records):
        """Converts a series of SeqRecord objects into ScrollSeq objects.

        Args:
            infile (str): full path to the file of origin
            group (str): group to which the sequence belongs
            *records: iterable of SeqRecord objects to create ScrollSeq objects

        Returns:
            list of ScrollSeq objects
        """
        scroll_seqs = []
        for record in records:
            scroll_seqs.append(ScrollSeq(
                self._id_counter, # id_num
                infile,
                group,
                record)) # Bio.SeqRecord object
            self._id_counter += 1 # Needs to be unique
        return scroll_seqs


    def _filter_sequences(self, filter_method):
        """Calls the relevant filter_method on input sequences.

        Args:
            filter_method (str): name of method to use for filtering.

        Returns:
            modifies internal _seq_dict and _removed variables
        """
        pass # TO BE IMPLEMENTED


    def _split_sequences(self):
        """Attempts to split one group into smaller groups.

        Returns:
            modifies internal _seq_dict and _groups variables
        """
        pass # TO BE IMPLEMENTED


    def _make_collections(self):
        """Creates all possible pairwise ScrollCollection objects.

        Args:
            (self.infiles)
            (self._groups)

        Returns:
            a list of ScrollCollection objects
        """
        if len(self._groups) == 1: # only one group
            group = self._groups[0]
            inpath = self.infiles[0]
            self._collections.append(ScrollCollection(
                self.target_dir,
                self._seq_dict[group], # seq_list
                group,
                self.align_method,
                self.dist_method,
                inpath=inpath, # Still unsure whether or not to provide this
                ))
        for group1,group2 in combinations(self._groups,2): # pairwise
            seq_list = sf._cat_sequence_lists(
                self._seq_dict[group1],
                self._seq_dict[group2]) # Dict values are lists
            self._collections.append(ScrollCollection(
                self.target_dir,
                seq_list,
                group1,
                self.align_method,
                self.dist_method,
                opt_group = group2 # Arbitrary which group is the 'optional' one
                ))


    def _sort_distances(self):
        """Sorts all objects in an internal list.

        Args:
            (self._collections)

        Returns:
            A sorted list of ScrollSeq objects.
        """
        pass
