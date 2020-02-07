"""
Module containing a single container class for a group of sequences in
ScrollPy.
"""

import os

from scrollpy import config
from scrollpy import scroll_log
from scrollpy.files import sequence_file as sf
# from scrollpy.alignments import align
from scrollpy import Aligner
from scrollpy import DistanceCalc
# from scrollpy.distances import distance, parser
# from scrollpy.distances import parser
from scrollpy.files import distance_file as df
#from scrollpy.config._config import config
from scrollpy import scrollutil


# Get module loggers
(console_logger, status_logger, file_logger, output_logger) = \
        scroll_log.get_module_loggers(__name__)


class ScrollCollection:
    """Main ScrolCollection object to comare sequences during scrollsaw.

    Each pairwise group of sequences (or a single group if only one is
    specified) forms the basis for a separate ScrollCollection instance.
    Running an instance takes care of all alignment and distance
    calculation calls.

    Args:
        outdir (str): The full path to target directory for files.
        seq_list (list): A list of ScrollSeq objects.
        group (str): The name of the group to which the seqs belong.
        opt_group (str): Optional name of a second sequence group, for
            use in pairwise comparisons. Defaults to None.
        **kwargs: Optional keyword arguments specifying aligning and
            distance parameters. If not specified, the corresponding
            values are obtained from the global config.

    """
    # Class var list
    _config_vars = (
            'align_method',
            'align_matrix',
            'dist_method',
            'dist_matrix',
            )

    def __init__(self, outdir, seq_list, group, opt_group=None, **kwargs):
        # Required
        self._outdir = outdir
        self.seq_list = seq_list
        self._group = group
        self._opt_group = opt_group  # Can be None
        # Optional vars or in config
        for var in self._config_vars:
            try:
                value = kwargs[var]
            except KeyError:
                value = config['ARGS'][var]
            setattr(self, var, value)
        # Store kwargs for __repr__
        self.kwargs = kwargs
        # Internal defaults
        self._seq_path = None # Path to unaligned sequence file
        self._dist_path = None # Path to the distance file
        self._dist_dict = None # Parsed distance file list


    def __repr__(self):
        return "{}({!r}, {!r}, {!r}, {!r}, **{!r})".format(
                self.__class__.__name__,
                self._outdir,
                self.seq_list,
                self._group,
                self._opt_group,
                self.kwargs,
                )

    def __str__(self):
        if self._opt_group:  # Two groups
            return "{} with two groups: {} and {}".format(
                    self.__class__.__name__,
                    self._group,
                    self._opt_group,
                    )
        else:
            return "{} with one group: {}".format(
                    self.__class__.__name__,
                    self._group,
                    )


    def __call__(self):
        """Runs all methods for a single collection.

        A call implies aligning, calculating distances, and then
        either parsing the output file or retrieving from an object.

        """
        # First step: create sequence file (if necessary)
        self._get_sequence_file()
        # Second step: align sequences and write to outfile
        self._get_alignment()
        # Third step: calculate distances
        self._get_distances()
        # Fourth step: parse distances
        self._parse_distances()
        # Final step: modify objects using distances
        self._increment_seq_distances()


    def _get_sequence_file(self):
        """Calls external methods to parse sequence file."""
        # seq_path = self._get_outpath('seqs')
        seq_path = scrollutil.get_filepath(
                self._outdir,          # Output directory
                self._group,           # Name
                'sequence',            # Type, for file extension
                extra=self._opt_group, # Extra for name; can be None
                seqfmt='fasta',        # Specify the file format
                )
        sf._sequence_list_to_file_by_id(self.seq_list, seq_path)
        self._seq_path = seq_path # Assign to self for other functions


    def _get_alignment(self):
        """Calls external method to build a sequence alignment.

        Creates and runs an instance of the Aligner class in order to
        build an alignment from the sequences.

        """
        msa_path = scrollutil.get_filepath(
                self._outdir,
                self._group,
                'alignment',
                extra=self._opt_group,
                alignfmt='fasta',
                )
        aligner = Aligner(
                self.align_method,
                config['ALIGNMENT'][self.align_method], # Cmd to execute
                inpath = self._seq_path,
                outpath = msa_path,
                )
        aligner() # Actually perform alignment; may raise ApplicationError
        self._align_path = msa_path # No errors -> assign to self for later


    def _get_distances(self):
        """Calls external method to build a sequence alignment.

        Creates and runs an instance of the Aligner class in order to
        build an alignment from the sequences.

        """
        dist_path = scrollutil.get_filepath(
                self._outdir,
                self._group,
                'distance',
                extra=self._opt_group,
                distfmt='raxml',
                )
        distcalc = DistanceCalc(
                self.dist_method,
                config['DISTANCE'][self.dist_method], # Cmd to execute
                inpath = self._align_path,
                outpath = dist_path,
                model = self.dist_matrix, # Model to use for distance
                )
        distcalc() # Actually calculates distances; may raise ApplicationError
        if self.dist_method == 'RAxML': # RAxML is weird; may need to generalize this
            suffix = os.path.split(dist_path)[1]
            dist_file_name = 'RAxML_distances.' + suffix
            actual_dist_file_path = os.path.join(self._outdir, dist_file_name)
            self._dist_path = actual_dist_file_path
        else:
            self._dist_path = dist_path # No errors -> assign to self for later


    def _parse_distances(self):
        """Calls external methods to parse distance file."""
        distances = df.parse_distance_file(
                self._dist_path,
                self.dist_method) # Tells the parser what type of file it is
        self._dist_dict = distances # List of tuples


    def _increment_seq_distances(self):
        """Updates ScrollSeq objects based on distances.

        Each pairwise distance should be added to each object instance;
        ScrollSeq class is overloaded to handle addition operations.

        """
        for seq_obj in self.seq_list:
            # Seqs written by ID, can modify if written by acc/desc later
            seq_obj += self._dist_dict[str(seq_obj.id_num)]


