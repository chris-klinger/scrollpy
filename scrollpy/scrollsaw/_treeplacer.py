"""
This module contains the main TreePlacer object.
"""

import os
import sys  # Temporarily necessary
import tempfile

from Bio import SeqIO

from scrollpy import config
from scrollpy import scroll_log
from scrollpy import FatalScrollPyError
from scrollpy.files import sequence_file as sf
from scrollpy.files import tree_file as tf
# from scrollpy.files import msa_file as mf
from scrollpy.files import align_file as af
from scrollpy.util import _tree,_util
from scrollpy import Aligner
from scrollpy import TreeBuilder
# from scrollpy.alignments.align import Aligner
# from scrollpy.trees.maketree import TreeBuilder
from scrollpy.util._mapping import Mapping
# List for tmpdir names, for later removal
from scrollpy import tmps_to_remove
from scrollpy import scrollutil


# Get module loggers
(console_logger, status_logger, file_logger, output_logger) = \
        scroll_log.get_module_loggers(__name__)


class TreePlacer:
    """Main TreePlacer object used to place sequences in a given tree.

    Assuming a mapping that matches each leaf in a tree to a known group
    of sequences (e.g. a monophyletic group), sequences can be added one
    at a time to the corresponding alignment for placement in the tree.

    For each sequence, it can be found in the tree, and its parent nodes
    traversed to classify it based on a support threshold.

    Args:
        seq_dict (dict): A dictionary of mapped group:object pairs.
        alignment (obj): A parsed BioPython alignment object.
        to_place (str): The full path to a file of sequences to place.
        target_dir (str): The full path to a directory for output file(s).
        infiles (list): The list of infiles to provided during initial
            program call. Defaults to an empty list.
        **kwargs: Optional arguments for alignment/tree parameters and a
            support threshold. If not specified, taken from global config.

    """

    # Class var list
    _config_vars = (
            'align_method',
            'tree_method',
            'tree_matrix',
            'support',
            )

    def __init__(self, seq_dict, alignment, to_place, target_dir, infiles=[], **kwargs):
        # Required
        self._seq_dict   = seq_dict   # Produced by Mapping
        self._alignment  = alignment  # Should be the file handle
        self._to_place   = self._parse_sequences(to_place)
        # self._to_place  = to_place   # Sequences to place in tree
        self._num_seqs   = len(self._to_place)
        self._outdir     = target_dir
        self._infiles    = infiles
        self._remove_tmp = False
        # Optional vars or in config
        for var in self._config_vars:
            try:
                value = kwargs[var]
            except KeyError:
                value = config['ARGS'][var]
            if var == 'support':
                value = int(value)
            setattr(self, var, value)
        # Save kwargs for __repr__
        self.kwargs = kwargs
        # Internal defaults; change each time through __call__ loop
        # Filepaths
        self._current_seq_path   = ""
        self._current_align_path = ""
        self._current_phy_path   = ""
        self._current_tree_path  = ""
        # Internal structures for Tree/LeafSeq objects
        self._current_tree_obj   = None
        self._leafseq_dict       = {}
        self._original_leafseqs  = []
        self._original_leaves    = []
        # Classification information
        self._classified         = {}  # Classified Seq objects
        self._monophyletic       = []  # Info on monophyletic sequences
        self._not_monophyletic   = []  # Info on non-monophyletic sequences


    def __repr__(self):
        return "{}({!r}, {!r}, {!r}, {!r}, {!r}, **{!r})".format(
                self.__class__.__name__,
                self._seq_dict,
                self._alignemnt,
                self._to_place,
                self._outdir,
                self._infiles,
                self.kwargs,
                )

    def __str__(self):
        return "{} using {} for alignment and {} for phylogeny reconstruction".format(
                self.__class__.__name__,
                self.align_method,
                self.tree_method,
                )


    def __call__(self):
        """Runs TreePlacer to place sequences.

        For each sequence, build a new alignment and tree object, parse
        the tree object, and identify where the added sequence falls in
        the tree. If the first parent node of the added sequence is
        monophyletic, attempt to classify. Otherwise, determine all
        groups that the sequence might be similar to.

        """
        if not self._outdir:
            self._remove_tmp = True
            tmp_dir = tempfile.TemporaryDirectory()
            self._outdir = tmp_dir.name
            tmps_to_remove.append(self._outdir)  # For later removal
        # Iter over sequences
        for i,seq_obj in enumerate(self._to_place):
            scroll_log.log_message(
                    scroll_log.BraceMessage(
                        "Placing sequence number {} of {}",
                        (i+1),self._num_seqs),
                    3,
                    'INFO',
                    status_logger,
                    )
            # Create all neccessary files
            self._make_new_files(seq_obj)
            # Parse tree object and update internal mappings
            self._update_tree_mappings()
            # Determine the right leaf
            added_leaf = self._get_added_leaf()
            # Start recording information
            leaf_info = []
            leaf_info.append(added_leaf)
            # Try to re-root tree
            self._root_tree(added_leaf)
            # Write new tree to output?
            # Get actual node
            added_node = self._current_tree_obj&added_leaf
            first_ancestor = added_node.up
            # Now determine monophyly
            if not _tree.is_node_monophyletic(
                    first_ancestor,
                    self._original_leafseqs,
                    ):
                leaf_info.append('Not Monophyletic')
                # Not monophyletic, but could still get some info?
                leaf_info.extend(self._classify_node(first_ancestor))
                # Add to internal list
                self._not_monophyletic.append(leaf_info)
            else:
                leaf_info.append('Monophyletic')
                # Get some more information about the classification
                group,info = self._classify_monophyletic_node(first_ancestor)
                leaf_info.extend(info)
                # Add to internal list
                self._monophyletic.append(leaf_info)
                # Set info on seq object and add to list
                self._add_classified_seq(group,seq_obj)
        # Clear line with status_logger information
        scroll_log.log_newlines(console_logger)
        # # Clean up -> Moved to __main__.run_cleanup()!
        # if self._remove_tmp:
        #     tmp_dir.cleanup()


    def _parse_sequences(self, seq_path):
        """Parses a file to return ccorresponding ScrollSeq objects.

        Args:
            seq_path (str): Full path to a file with sequences.

        Returns:
            list: A list of ScrollSeq objects.

        """
        try:
            # Need to worry about format?!
            return sf.seqfile_to_scrollseqs(seq_path)
        except:  # Make more specific eventually!
            scroll_log.log_message(
                    scroll_log.BraceMessage(
                        "Failed to parse sequences for tree placing"),
                    1,
                    'ERROR',
                    console_logger, file_logger,
                    )
            raise FatalScrollPyError


    def return_classified_seqs(self):
        """Returns all classified SrollSeq objects."""
        return self._classified


    def _make_new_files(self, seq_obj):
        """Makes all required files for each new sequence.

        Essentially a convenience function that calls several internal
        functions one at a time to first add a new sequence to an existing
        alignment, then convert the alignment to phylip and construct a
        phylogeny.

        Args:
            seq_obj (obj): The target sequence object.

        """
        basename = seq_obj.name
        # Create a new sequence file
        self._current_seq_path = scrollutil.get_filepath(
                self._outdir,
                basename,
                'sequence',
                seqfmt='fasta',
                )
        # Add to existing alignemnt
        self._current_align_path = scrollutil.get_filepath(
                self._outdir,
                basename,
                'alignment',
                alignfmt='fasta',
                )
        self._add_seq_to_alignment(seq_obj)
        # Convert to Phylip file
        self._current_phy_path = scrollutil.get_filepath(
                self._outdir,
                basename,
                'alignment',
                alignfmt='phylip',
                )
        af.afa_to_phylip(self._current_align_path, self._current_phy_path)
        # Run IQ-TREE
        self._current_tree_path = scrollutil.get_filepath(
                self._outdir,
                basename,
                'tree',
                treefmt='iqtree',
                )
        self._make_tree()


    def _add_seq_to_alignment(self, seq_obj):
        """Calls external method to add a sequence to an alignment.

        Creates and runs an instance of the Aligner class in order to
        add the sequence to an alignment. For now, only provide option
        to use MAFFT; more sequences could be added in future.

        Args:
            seq_obj (obj): The sequence to be added to the alignment.

        """
        with open(self._current_seq_path,'w') as seq_file:
            # seq_obj.write(seq_file)  # Temporary input file
            seq_obj._write(  # ScrollSeq _write method now
                    seq_file,
                    'fasta',  # Change to be flexible?
                    )
        if self.align_method == 'Mafft':
            # MAFFT for now, maybe add support for others later?
            method = 'MafftAdd'
            align_command = [
                    '--add',                # Adding to existing alignment
                    self._current_seq_path, # Input provided as string
                    '--keeplength',         # Alignment length unchanged
                    '--thread',             # Use all possible cores
                    '-1',
                    self._alignment,        # Starting alignment handle
                    ]
        elif self.align_method == 'Generic':
            pass  # Add eventually?
        aligner = Aligner(
                method,  # Signal to Aligner that adding should happen
                config['ALIGNMENT'][self.align_method],  # Cmd to execute
                inpath = self._current_seq_path,  # Exists inside of context manager
                outpath = self._current_align_path, # Should be a real path on the system
                cmd_list = align_command,  # Fine-grained control
                )
        aligner()  # Run command


    def _make_tree(self):
        """Calls external method to evaluate alignment columns.

        Creates and runs an instance of the TreeBuilder class in
        order to construct a phylogeny.

        """
        if self.tree_method == 'Iqtree':
            build_command = [
                    '-nt',  # Number of processors
                    'AUTO',
                    '-s',  # Input filename
                    self._current_phy_path,
                    '-m',
                    self.tree_matrix,  # E.g. 'LG'
                    '-bb',  # Rapid bootstrapping
                    '1000',
                    ]
        elif self.tree_method == 'RAxML':
            pass  # Add support eventually?
        builder = TreeBuilder(
                self.tree_method,
                config['TREE'][self.tree_method],  # Cmd to execute
                inpath = self._current_phy_path,  # Should exist
                outpath = self._current_tree_path,  # Should be a real path
                cmd_list = build_command,  # Uses subprocess internally
                )
        builder()  # Run command


    def _update_tree_mappings(self):
        """Creates a mapping based on new tree and mapping objects.

        In order to properly evaluate each separate tree, the associated
        node object for each LeafSeq needs to be updated each time. This
        also means associating each label with a label from the original
        mapping in order to identify the added sequence in each case.

        Raises:
            FatalScrollPyError: Raised if a 1-to-1 relationship between
                sequences in the original mapping and sequences in the
                new mapping cannot be established.

        """
        # Create a new Mapping
        mapping = Mapping(
                self._infiles,  # Infiles -> might be empty list
                # alignfile=self._alignment,
                alignfile=self._current_align_path,
                treefile=self._current_tree_path,
                infmt='fasta',
                alignfmt='fasta',
                treefmt='newick',
                )
        tree_dict = mapping()  # Returns Mapping with LeafSeqs
        # Reach into Mapping object and get tree
        self._current_tree_obj = mapping._tree_obj
        # Flatten both dicts
        seq_list = _util.flatten_dict_to_list(self._seq_dict)
        tree_list = _util.flatten_dict_to_list(tree_dict)
        # Get a list of just descriptions
        seq_descr = [record.description for record in seq_list]
        # Now match -> create new mapping each time!
        self._leafseq_dict = {}
        self._original_leafseqs = []
        self._original_leaves = []
        for leafseq in tree_list:
            try:
                # Get maching entry from original alignment
                index = seq_descr.index(leafseq.description)
                seq_obj = seq_list[index]
                # Update object with proper group attr
                right_group = seq_obj._group
                leafseq._group = right_group
                # Update internal dict
                try:
                    self._leafseq_dict[right_group].append(leafseq)
                except KeyError:
                    self._leafseq_dict[right_group] = []
                    self._leafseq_dict[right_group].append(leafseq)
                # Update internal list
                self._original_leafseqs.append(leafseq)
            except ValueError:
                pass  # Found added seq - do something?
        if len(seq_list) != len(self._original_leafseqs):
            # FATAL ERROR! -> terminate execution eventually
            scroll_log.log_message(
                    scroll_log.BraceMessage(
                        "Could not map all leaves to original tree"),
                    1,
                    'ERROR',
                    console_logger, file_logger,
                    )
            raise FatalScrollPyError
            # print("Could not map all original tree labels")
        # Made it to this point, should be fine
        self._original_leaves = [leaf.name for leaf in
                self._original_leafseqs]


    def _get_added_leaf(self):
        """Finds the added leaf in a tree object.

        Returns:
            str: The name attribute of the added leaf.

        """
        # Get all leaf names in current tree
        current_leaves = [leaf.name for leaf in self._current_tree_obj]
        # Added leaves are those not found initially
        added_leaves = [name for name in current_leaves
                if not name in self._original_leaves]
        if len(added_leaves) > 1:
            # FATAL ERROR! -> terminate execution eventually
            scroll_log.log_message(
                    scroll_log.BraceMessage(
                        "Detected more than one added sequence"),
                    1,
                    'ERROR',
                    console_logger, file_logger,
                    )
            raise FatalScrollPyError
            # print("More than one added leaf!")
        # Return only value in list
        return added_leaves[0]


    def _root_tree(self, added_leaf):
        """Randomly selects a group to root the tree on.

        In order for the node traversal to work as expected, it is
        useful to root the tree on a group that is irrelevant for the
        purposes of classifying the current leaf. This typically means
        a group that is not within the parent node of the added seq.

        """
        for group,leaves in self._leafseq_dict.items():
            # get_group_outgroup function needs TreeNode objects
            group_list = [leafseq._node for leafseq in leaves]
            outgroup = _tree.get_group_outgroup(
                    self._current_tree_obj,
                    added_leaf,
                    group_list,  # TreeNode objects!
                    )
            if outgroup:  # Returns TreeNode or None
                self._current_tree_obj.set_outgroup(outgroup)
                break  # No need to check others


    def _classify_node(self, start_node):
        """Details information about a non-monophyletic node.

        It may still be useful to know which groups a given sequence is
        familiar to, as well as whether those groups are complete under
        the starting (parental node). This can help determine whether the
        sequence in question places well, or disrupts the topology to a
        great extent.

        Starting with the parental node, check for the number of groups
        under the node, whether each of these is monophyletic and, if so,
        whether they are complete.

        Args:
            start_node (obj): An ETE3 tree Node object.

        Returns:
            list: A list of information useful for output. Includes at
                a minimum the starting node support, the number of groups
                under the node, and then any information for each
                monophyletic group under the node.

        """
        output_info = []
        # Starting from added_leaf ancestor
        # Support value first
        output_info.append(start_node.support)
        # Get information for all groups under the node
        node_groups = _tree.get_node_groups(
                start_node,
                self._original_leafseqs,
                )
        # Need to get node info for all groups
        group_count = len(node_groups)
        output_info.append(group_count)
        current_groups = set()
        for node in start_node.traverse():
            if _tree.is_node_monophyletic(
                    node,
                    self._original_leafseqs,
                    ):
                # Only care about monophyletic nodes
                associated_groups = _tree.get_node_groups(
                        node,
                        self._original_leafseqs,
                        )
                group = next(iter(associated_groups))  # Single item
                if group not in current_groups:
                    # First node only
                    support = node.support
                    target_leafseqs = self._leafseq_dict[group]
                    target_leaves = [leafseq._node for leafseq in target_leafseqs]
                    add_on = 'Group is incomplete'
                    if _tree.is_complete_group(
                            node,
                            target_leaves,
                            ):
                        add_on = 'Group is complete'
                    # Add to growing list
                    output_info.extend([group,support,add_on])
                    current_groups.add(group)
                    # Check if done
                    if len(current_groups) == group_count:
                        break

        return output_info


    def _classify_monophyletic_node(self, start_node):
        """Details information about a monophyletic node.

        If the first node encountered traversing towards the root from the
        added leaf is monophyletic, it is possible to identify the larger
        monophyletic group for classification purposes.

        Starting with the parental node, check the support and then walk
        back upwards progressively until the last monophyletic node is
        identified (and check if it is the same node or not). Depending on
        the support value for each of these nodes, a tentative identity
        assignment can be completed.

        Args:
            start_node (obj): An ETE3 tree Node object.

        Returns:
            tuple: A two member tuple, with the monophyletic group name
                and a list of information useful for output. The list
                includes the starting group, starting  node support,
                whether the last ancestral node is different and its
                support (or 'NA'), whether the group is complete, and
                a putative classification for the sequence.

        """
        output_info = []
        # Get detailed information about first node
        node_groups = _tree.get_node_groups(
                start_node,
                self._original_leafseqs,
                )
        group = next(iter(node_groups))  # Single item
        output_info.append(group)  # Name of group
        output_info.append(start_node.support)  # Bootstrap support
        # Now walk up
        last_ancestor = _tree.last_monophyletic_ancestor(
                start_node,
                self._original_leafseqs,
                )
        # Check if a more ancestral monophyletic node has been found
        same_node = False
        if last_ancestor == start_node:
            same_node = True
            output_info.append('Same node')
        else:
            output_info.append('Different node')
        if same_node:
            last_ancestor.support = start_node.support
            output_info.append('NA')
        else:
            output_info.append(last_ancestor.support)
        # Check whether the monophyletic ancestor is complete
        target_leafseqs = self._leafseq_dict[group]
        target_leaves = [leafseq._node for leafseq in target_leafseqs]
        if _tree.is_complete_group(
                last_ancestor,
                target_leaves,
                ):
            output_info.append('Group is complete')
        else:
            output_info.append('Group is incomplete')
        # Finally, check whether either node meets threshold
        if (start_node.support >= self.support) or\
                (last_ancestor.support >= self.support):
            output_info.append('Possible Positive Hit')
        else:
            output_info.append('Unlikely Positive Hit')

        return group,output_info


    def _add_classified_seq(self, group, seq_obj):
        """Adds classified sequence information to internal dict.

        Args:
            group (str): The group the sequence is classified into.
            seq_obj (obj): The actual sequence object.

        """
        seq_obj._group = group
        try:
            self._classified[group].append(seq_obj)
        except KeyError:
            self._classified[group] = []
            self._classified[group].append(seq_obj)

