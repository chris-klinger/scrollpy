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
    def __init__(self, method, cmd, inpath=None, outpath=None,
            _logger=None, **kwargs):
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
        if self._validate('method', method, self._validate_method):
            self.method = method
        if self._validate('command', cmd, self._validate_command,
                method=method): # Should work; if not set, an Exception was raised
            self.cmd = cmd
        if self._validate('inpath', inpath, self._validate_inpath):
            self.inpath = inpath
        if self._validate('outpath', outpath, self._validate_outpath):
            self.outpath = outpath
        # Check logger eventually?
        self._logger = _logger
        # Should eventually validate kwargs? Or leave for BioPython?
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

    def _validate(self, name, value, validation_method, **kwargs):
        """Calls other checking methods for each"""
        if validation_method is not None: # was provided
            # Should we keep validation inside class?
            # "Self" argument here is implicit in passed function object
            is_valid = validation_method(value, **kwargs) # May raise exception
            if not is_valid in (0, 1, True, False): # Truthy values
                raise ValueError("Result of {} check on {} is \
                    an unexpected value".format(
                        validation_method.__name__, value))
            elif is_valid:
                return True
            elif not is_valid: # Could just be "else"?
                raise ValueError("Invalid parameter {} for {} while \
                    calling alignment".format(value, name))
        # Raise error if no method provided?

    def _validate_method(self, method_name):
        """Returns True if method exists in class"""
        if not method_name in ('Mafft', 'Generic'): # For now
            return False
        return True

    def _validate_command(self, command, method=None):
        """Returns True if command makes sense for method"""
        if method == 'Mafft':
            path_char = os.sep
            if path_char in command: # Full path given
                cmd = os.path.basename(command)
            else:
                cmd = command
            if cmd not in ('mafft', 'mafft-linsi'):
                return False
        elif method == 'Generic':
            if not command == 'None':
                return False
        return True

    def _validate_inpath(self, inpath):
        """Raises FileNotFoundError if file does not exist"""
        if not os.path.exists(inpath):
            raise FileNotFoundError(
                errno.ENOENT, # File not found
                os.strerror(errno.ENOENT), # Obtain right error message
                inpath # File name
                )
        elif os.path.isdir(inpath):
            raise AttributeError("Cannot align {}; directory")
        return True

    def _validate_outpath(self, outpath):
        """Quits if directory is non-existent; Should log if file exists"""
        out_dir = os.path.dirname(outpath)
        if not os.path.exists(out_dir):
            raise FileNotFoundError(
                errno.ENOENT, # File not found
                os.strerror(errno.ENOENT), # Obtain right error message
                out_dir # Actual name
                )
        if os.path.exists(outpath):
            pass # Will eventually hook this up to the logger
        return True


