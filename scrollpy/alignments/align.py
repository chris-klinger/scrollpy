"""
This module contains a generic class that will farm out alignment calls
to the relevant program using the BioPython command line application
tools, or internal methods (if implemented).

Class should (eventually) handle all details, including capturing output
in a file (if it is the program default) or redirecting stdout to the
relevant file if it is not. StdErr can be captured by a logging object
for detailed user interface.

More details to follow.
"""

import os,errno

from Bio.Align import Applications
from Bio.Application import ApplicationError


class Aligner:
    def __init__(self, method, cmd, inpath=None, outpath=None, _logger=None, **kwargs):
        """Class to handle farming out and managing alignments.

        Args:
            method (str): Name of method to use for alignment. Accepted
                values are `Muscle`, `Clustalw`, `ClustalOmega`, `Prank`,
                `Mafft`, `Dialign`, `Probcons`, `TCoffee`, `MSAProbs`,
                `Generic`.
            cmd (str): Command (if executable is on system PATH) or full
                path to the relevant executable
            inpath (str): Full path for input
            outpath (str): Full path to dump MSA to
            _logger (obj): Reference to a logger for logging (optional)
            **kwargs: Additional parameters specified for the relevant
                program (optional)
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
        """Calls the underlying alignment method.

        First, validate method, command, and outpath arguments as valid.
        Next, call the underlying method using BioPython commandline
        wrapper or internal method and handle stdout/stderr.
        """
        # Validate all parts of the input
        try:
            self._validate_method()
        except ValueError:
            print("Could not validate method name") # TO-DO
        try:
            self._validate_command()
        except ValueError:
            print("Could not validate align command") # TO-DO
        try:
            self._validate_inpath()
        except FileNotFoundError:
            print("Could not validate inpath") # TO-DO
        try:
            self._validate_outpath()
        except FileNotFoundError:
            print("Could not validate outpath") # TO-DO
        # Either delegate call to BioPython or run internal method
        if self.method == 'Mafft':
            cmdline = Applications.MafftCommandline(
                self.cmd, input=self.inpath, **self.kwargs)
            try:
                stdout, stderr = cmdline() # Need to log stderr eventually
            except ApplicationError: # Raised if subprocess return code != 0
                print("Failed to run MAFFT") # Should process better eventually
            with open(self.outpath, 'w') as o:
                o.write(stdout)
        elif self.method == 'Generic':
            pass # To be implemented

    def _validate_method(self):
        """Raises ValueError if not valid method"""
        if not self.method in ('Mafft', 'Generic'): # For now
            raise ValueError

    def _validate_command(self):
        """Raises ValueError if not valid command"""
        if self.method == 'Mafft':
            path_char = os.sep
            if path_char in self.cmd: # Full path given
                cmd = os.path.dirname(self.cmd)
            else:
                cmd = self.cmd
            if cmd not in ('mafft', 'mafft-linsi'):
                raise ValueError
        elif self.method == 'Generic':
            if not self.cmd == 'None':
                raise ValueError

    def _validate_inpath(self):
        """Raises FileNotFoundError if file does not exist"""
        if not os.path.exists(self.inpath):
            raise FileNotFoundError(
                errno.ENOENT, # File not found
                os.strerror(errno.ENOENT), # Obtain right error message
                self.inpath # File name
                )

    def _validate_outpath(self):
        """Quits if directory is non-existent; Should log if file exists"""
        out_dir = os.path.dirname(self.outpath)
        if not os.path.exists(out_dir):
            raise FileNotFoundError(
                errno.ENOENT, # File not found
                os.strerror(errno.ENOENT), # Obtain right error message
                out_dir # Actual name
                )
        if os.path.exists(self.outpath):
            pass # Will eventually hook this up to the logger


