"""
This module contains a generic class to farm out distance calls to the
relevant program using the BioPython command line application tools,
or internal methods (if implemented).

One class will handle all calling details, including either tracking
output file (if it is program default) or redirecting stdout to a file
if it is not. StdErr can be captured by a logging object for detailed
user inspection.
    -> May need to refactor when considering distances from trees?

Another class will handle reading the actual distance files, likely
calling other class instances to provide program-specific parsing. If
it is implemented, internal distance method can interface directly with
this class without first having to write to a file(?)
"""

import os,errno

from Bio.Phylo import Applications
from Bio.Application import ApplicationError


class DistanceCalc:
    def __init__(self, method, cmd, inpath=None, outpath=None,
            _logger=None, **kwargs):
        """Class to handle farming out and managing distance calculations.

        Args:
            method (str): Name of method to use to calculate distances.
                Accepted values are `RAxML`, `PhyML`, `Generic`. Additional
                support for other formats might be extended later.
            cmd (str): Command (if executable is on system PATH) or full
                path to the relevant executable.
            inpath (str): Full path to input file
            outpath (str): Full path to dump distances to
            _logger (obj): Reference to a logger for logging (optional)
            **kwargs: Additional parameters specified for the relevant
                program (optional?)
        """
        self.method = method
        self.cmd = cmd
        self.inpath = inpath
        self.outpath = outpath
        self._logger = _logger
        self.kwargs = kwargs

    def __str__(self):
        """TO-DO"""
        pass

    def __repr__(self):
        """TO-DO"""
        pass

    def __call__(self):
        """Calls the underlying method for distance calculation.

        First,
