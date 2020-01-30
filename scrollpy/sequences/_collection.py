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
from scrollpy.distances import parser
#from scrollpy.config._config import config


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
        seq_path = self._get_outpath('seqs')
        # As in _get_outpath(), eventually provide options to control this
        #if seq_path != self._inpath: # Comparison works even if None?
        #    if _util.file_exists(seq_path):
        #        user_spec = _util.file_exists_user_spec(seq_path)
        #        if user_spec in ('y','Y'):
        #            sf._sequence_list_to_file(self.seq_list, seq_path)
        #    else:
        #        sf._sequence_list_to_file(self.seq_list, seq_path)
        sf._sequence_list_to_file_by_id(self.seq_list, seq_path)
        self._seq_path = seq_path # Assign to self for other functions


    def _get_alignment(self):
        """Calls external method to build a sequence alignment.

        Creates and runs an instance of the Aligner class in order to
        build an alignment from the sequences.

        """
        msa_path = self._get_outpath('align')
        # aligner = align.Aligner(
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
        dist_path = self._get_outpath('distance')
        # distcalc = distance.DistanceCalc(self.dist_method,
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
        distances = parser.parse_distance_file(
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


    def _get_outpath(self, out_type):
        """Obtains the full path to an output file.

        Args:
            out_type (str): The type of output file needed. Should be
                one of <seqs>, <align>, or <distance>.

        Returns:
            str: Full path to the output file.

        """
        # Eventually want to give user option to leave sequence headers as is
        # or run using internal file generation and ScrollSeq.id_num
        # For now, just use ScrollSeq.id_num
        #if (out_type == 'seqs' and self._inpath): # Brackets for emphasis
        #    return self._inpath # Don't need to re-make input file
        #else:
        basename = ""
        if self._opt_group: # Two groups
            # TO-DO: allow user to specify separator?
            basename = str(self._group) + '_' + str(self._opt_group)
        else:
            basename = str(self._group)
        if out_type == 'seqs':
            outfile = basename + '.fa'
            outpath = os.path.join(self._outdir, outfile)
        elif out_type == 'align':
            outfile = basename + '.mfa'
            outpath = os.path.join(self._outdir, outfile)
        elif out_type == 'distance':
            # TO-DO: this should work for RAxML, but what about others?
            outpath = os.path.join(self._outdir, basename)
        else:
            raise ValueError # Is this necessary?
        return outpath

