"""
Module containing a single container class for a group of sequences in
ScrollPy.
"""

import os

from scrollpy.util import _util
from scrollpy.files import sequence_file as sf
from scrollpy.align import align



class ScrollCollection:
    """A collection of sequences for use in ScrollPy.

    Args:
        outdir (str): full path to target directory for files

        seqs (lists): list of ScrollSeq objects

        group (str): name of the group to which the seqs belong

        align_method (str): string denoting alignment method to use
            Allowed values are: `Muscle`, `Clustalw`, `ClustalOmega`,
            `Prank`, `Mafft`, `Dialign`, `Probcons`, `TCoffee`,
            `MSAProbs`, `Generic`

        dist_method (str): string denoting distance calculation method
            to use. Allowed values are: `RAxML`, `PhyML`, `Generic`.

        opt_group (str): name of a second group (default: None)

        inpath (str): full path to input file (default:None)
    """
    def __init__(self, outdir, seq_list, group, align_method,
            dist_method, opt_group=None, inpath=None):
        self._outdir = outdir
        self.seq_list = seq_list
        self._group = group
        self._align_method = align_method
        self._aligned = None # Path to the aligned file
        self._dist_method = dist_method
        self._distance = None # Path to the distance file
        self._dist_obj = None # Parsed distance file/distance object
        self._opt_group = opt_group
        self._inpath = inpath # Means we don't need to create

    def __str__(self):
        """TO-DO"""
        pass

    def __repr__(self):
        """TO-DO"""
        pass

    def __call__(self):
        """A call implies aligning, calculating distances, and then
        either parsing the output file or retrieving from an object.
        """
        # First step: create sequence file (if necessary)
        seq_path = self._get_outpath('seqs')
        if seq_path != self._inpath: # Comparison works even if None?
            if _util.file_exists(seq_path):
                user_spec = _util.file_exists_user_spec(seq_path)
                if user_spec in ('y','Y'):
                    sf._sequence_list_to_file(self.seq_list, seq_path)
            else:
                sf._sequence_list_to_file(self.seq_list, seq_path)
        # Second step: align sequences and write to outfile
        aligner = align.Aligner(self.align_method,

    def _get_outpath(self, out_type):
        """A function to return full paths to files based on what the
        file is to be used for; mainly for convenience.
        """
        if (out_type == 'seqs' and self._inpath): # Brackets for emphasis
            return self._inpath # Don't need to re-make input file
        else:
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

