"""
This module contains the main TreePlacer object.
"""

import tempfile


from scrollpy.files import tree_file as tf
from scrollpy.files import msa_file as mf
from scrollpy.util import _tree,_util


class TreePlacer:
    """Main TreePlacer object; based on user input, run is variable.

    Args:
        seq_dict (dict): starting dict produced from a Mapping

        alignment (obj): parsed BioPython alignment object

        to_place (list): list of parsed BioPython SeqRecord objects

        target_dir (str): path to target directory for output file(s)

    """

    # Class var list
    _config_vars = ('align_method', 'tree_method', 'tree_matrix', 'support')

    def __init__(self, seq_dict, alignment, to_place, target_dir, **kwargs):
        # Required
        self._seq_dict  = seq_dict   # Produced by Mapping
        self._alignment = alignment  # Should be the file handle
        self._to_place  = to_place   # Sequences to place in tree
        self._outdir    = target_dir
        # Optional vars or in config
        for var in self._config_vars:
            try:
                value = kwargs[var]
            except KeyError:
                value = config['ARGS'][var]
            setattr(self, var, value)
        # Internal cached value for LeafSeq objects
        self._leafseq_dict       = {}
        self._original_leafseqs  = []
        self._original_leaves    = []
        # Internal defaults; change each time through __call__ loop
        self._current_align_path = ""
        self._current_phy_path   = ""
        self._current_tree_path  = ""
        self._current_tree_obj   = None
        self._classified         = []  # Sequences and their classification for writing


    # def __repr__(self):
    #     """TO-DO"""
    #     pass


    # def __str__(self):
    #     """TO-DO"""
    #     pass


    def __call__(self):
        """Runs TreePlacer"""
        if not self._outdir:
            self._remove_tmp = True
            tmp_dir = tempfile.TemporaryDirectory()
            self._outdir = tmp_dir.name
        # Iter over sequences
        for seq_obj in self._to_place:
            # Create all neccessary files
            self._make_new_files(seq_obj)
            # Parse tree object and update internal mappings
            self._read_current_tree()
            if not self._original_leaves:
                self._update_tree_mappings()
            # Determine the right leaf
            added_leaf = self._get_added_leaf()
            # Start recording information
            leaf_info = []
            leaf_info.append(added_leaf)
            # Try to re-root tree
            new_tree = self._root_tree(added_leaf, new_tree)
            # Write new tree to output?
            # Get actual node
            added_node = new_tree&added_leaf
            first_ancestor = added_node.up
            # Now determine monophyly
            if not _tree.is_node_monophyletic(
                    first_ancestor,
                    self._original_leafseqs,
                    ):
                leaf_info.append('Not Monophyletic')
                # Not monophyletic, but could still get some info?
                info = self._classify_node(first_ancestor)
            else:
                leaf_info.append('Monophyletic')
                # Get some more information about the classification
                info = self._classify_monophyletic_node(first_ancestor)
        # Clean up
        if self._remove_tmp:
            tmp_dir.cleanup()


    def _make_new_files(self, seq_obj):
        """Calls other internal functions"""
        # Add to existing alignemnt
        self._current_align_path = self._get_outpath(seq_obj,'align')
        self._add_seq_to_alignment(seq_obj)
        # Convert to Phylip file
        self._current_phy_path = self._get_outpath(seq_obj,'phylip')
        mf.afa_to_phylip(self._current_align_path, self._current_phy_path)
        # Run IQ-TREE
        self._current_tree_path = self._get_outpath(seq_obj,'tree')
        self._make_tree()


    def _get_outpath(self, seq_obj, out_type):
        """Similar to other class functions - maybe this can be extrated?"""
        # Is name guaranteed to be unique?
        basename = seq_obj.name
        # Create a new subdir for each run?
        if out_type == 'align':
            outfile = basename + '.mfa'
        elif out_type == 'phylip':
            outfile = basename + '.phy'
        elif out_type == 'tree':
            outfile = basename + '.tre'
        # Get full path and return
        outpath = os.path.join(self._outdir, outfile)
        return outpath


    def _add_seq_to_alignment(self, seq_obj):
        """Calls MAFFT to add sequences to an existing alignment"""
        # First create a temporary file - removed after context manager
        with tempfile.NamedTemporaryFile() as seq_file:
            seq_obj._write(seq_file)  # Temporary input file
            if self.align_method == 'Mafft':
                # MAFFT for now, maybe add support for others later?
                method = 'MafftAdd'
                align_command = [
                        '--add',         # Adding to existing alignment
                        seq_file,        # Need file object for input
                        '--keeplength',  # Alignment length unchanged
                        '--thread',      # Use all possible cores
                        '-1',
                        self._alignment, # Starting alignment handle
                        ]
            elif self.align_method == 'Generic':
                pass  # Add eventually?
            aligner = align.Aligner(
                    method,  # Signal to Aligner that adding should happen
                    config['ALIGNMENT'][self.align_method],  # Cmd to execute
                    inpath = seq_file,  # Exists inside of context manager
                    outpath = self._current_align_path, # Should be a real path on the system
                    cmd_list = align_command,  # Fine-grained control
                    )
            aligner()  # Run command


    def _make_tree(self):
        """Calls IQ-TREE to construct a tree"""
        if self.tree_method == 'IQ-Tree':
            build_command = [
                    '-nt',  # Number of processors
                    'AUTO',
                    '-s',  # Input filename
                    phylip_path,
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


    def _read_current_tree(self):
        """Reads and sets attribute"""
        self._current_tree_obj = tf.read_tree(
                self._current_tree_path,
                'newick',  # IQ-Tree output is Newick
                )


    def _update_tree_mappings(self):
        """Creates a mapping based on new tree and mapping objects"""
        # Create a new Mapping
        mapping = Mapping(
                alignfile=self._alignment,
                treefile=self._current_tree_path,
                )
        tree_dict = mapping()  # Returns Mapping with LeafSeqs
        # Flatten both dicts
        seq_list = _util.flatten_dict_to_list(self._seq_dict)
        tree_list = _util.flatten_dict_to_list(tree_dict)
        # Get a list of just descriptions
        seq_descr = [record.description for record in seq_list]
        # Now match
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
            print("Could not map all original tree labels")
        # Made it to this point, should be fine
        self._original_leaves = [leaf.name for leaf in
                self._original_leafseqs]


    def _get_added_leaf(self):
        """Finds the added leaf in a tree object"""
        # Get all leaf names in current tree
        current_leaves = [leaf.name for leaf in self._current_tree_obj]
        # Added leaves are those not found initially
        added_leaves = [name for name in current_leaves
                if not name in self._original_leaves]
        if len(added_leaves) > 1:
            # FATAL ERROR! -> terminate execution eventually
            print("More than one added leaf!")
        # Return only value in list
        return added_leaves[0]


    def _root_tree(self, added_leaf, tree_obj):
        """Randomly selects a group to root on"""
        for group,leaves in self._leafseq_dict.items():
            # get_group_outgroup function needs TreeNode objects
            group_list = [leafseq._node for leafseq in leaves]
            # Now call function
            outgroup = get_group_outgroup(
                    tree_obj,
                    added_leaf,
                    group_list,  # TreeNode objects!
                    )
            if outgroup:  # Returns TreeNode or None
                tree_obj.set_outgroup(outgroup)
                break  # No need to check others


    def _classify_node(self, start_node):
        """Finds info about a non-monophyletic node"""
        pass


    def _classify_monophyletic_node(self, start_node):
        """Finds monophyly information about a node"""
        output_info = []
        # Get detailed information about first node
        node_groups = _tree.get_node_groups(
                start_node,
                self._original_leafseqs,
                )
        group = next(iter(node_groups))  # Single item
        output_info.append(group)  # Name of group
        output_info.append(first_ancestor.support)  # Bootstrap support
        # Now walk up
        last_ancestor = last_monophyletic_ancestor(
                start_node,
                self._original_leafseqs,
                )
        last_groups = get_node_groups(
                last_ancestor,
                self._original_leafseqs,
                )
        last_group = next(iter(last_groups))  # Single item
        output_info.append(last_group)
        output_info..append(last_ancestor.support)
        if (start_node.support >= self.support) or\
                (last_ancestor.support >= self.support):
            output_info.append('Possible Positive Hit')
        else:
            output_info.append('Not Classified')

        return output_info

