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

import os,errno,re

from Bio.Phylo import Applications
from Bio.Application import ApplicationError


class DistanceCalc:
    def __init__(self, method, cmd, model, inpath=None, outpath=None,
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
        if self._validate('method', method, self._validate_method):
            self.method = method
        if self._validate('command', cmd, self._validate_command,
                method=method):
            self.cmd = cmd
        self.model = model
        if self._validate('inpath', inpath, self._validate_inpath):
            self.inpath = inpath
        if self._validate('outpath', outpath, self._validate_outpath):
            self.outpath = outpath
        # TO-DO: handle logger
        self._logger = _logger
        # Validate kwargs eventually?
        self.kwargs = kwargs

    def __str__(self):
        """TO-DO"""
        pass

    def __repr__(self):
        """TO-DO"""
        pass

    def __call__(self):
        """Calls the underlying method for distance calculation.

        Either calls BioPython to call a third-party program using generic
        command line interface or calls internal method(s).
        """
        # Depending on method, delegate or handle
        if self.method == 'RAxML':
            # Specify distance calculation
            self.kwargs['-f'] = 'x'
            # Convert in and out file paths to RAxML arguments
            # Should eventually have a method to validate these
            self.kwargs['-s'] = self.inpath
            # RAxML is weird; if not curdir for outpath must specify using -w
            dirname, outname = os.path.split(self.outpath)
            self.kwargs['-w'] = dirname
            self.kwargs['-n'] = outname
            # Change model input to a usable command
            self.kwargs['-m'] = self._modify_model_name(self.model,'RAxML')
            # If a nuc model is specified other than GTR, need to add to kwargs
            if self.model in ['JC','K80','HKY85']:
                arg_string = '--' + self.model
                self.kwargs[arg_string] = ''  # just need to add the arg itself
            # Finally, call command line
            cmdline = Applications.RaxmlCommandline(
                self.cmd, **self.kwargs)
            #try:
            stdout, stderr = cmdline() # Log stderr eventually
            #except ApplicationError: # Raised if subprocess return code != 0
            #    print("Failed to run RAxML") # TO-DO
        # TO-DO: write for others!
        elif self.method == 'Generic':
            pass # TO-DO

    def _validate(self, name, value, validation_method, **kwargs):
        """Calls other validation methods for each parameter"""
        if validation_method is not None:
            # Implicit "self" argument
            is_valid = validation_method(value, **kwargs)
            if not is_valid in (0, 1, True, False): # Truthy values
                raise ValueError("Result of {} check on {} is \
                    an unexpected value".format(
                        validation_method.__name__, value))
            elif is_valid: # parameter passes
                return True
            else: # False
                raise ValueError("Invalid parameter {} for {} while \
                    calling distance calculation".format(value, name))
        # Raise error if no method provided? Will this ever happen?

    def _validate_method(self, method_name):
        """Returns True if method exists in class"""
        if not method_name in ('RAxML', 'Generic'): # For now
            return False
        return True

    def _validate_command(self, command, method=None):
        """Returns True if command makes sense for method"""
        if method == 'RAxML':
            path_char = os.sep
            if path_char in command: # Full path given
                cmd = os.path.basename(command)
            else:
                cmd = command
            raxml_pattern = re.compile(r"""raxml       # raxml
                                            HPC ?      # may not have this
                                            [-_|]      # should be a hyphen
                                            AVX|       # one of AVX/PTHREADS/SSE3
                                            PTHREADS|
                                            SSE3""",
                                            flags = re.X|re.I) # verbose/case-insensitive
            if not raxml_pattern.search(cmd): # at least one match
                print("PATTERN DID NOT MATCH")
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


    def _modify_model_name(self, model, program):
        """Returns an appropriate string for a model depending on program"""
        prot_models = ['LG', 'WAG']
        nuc_models = ['GTR','JC69','HKY85']

        if program == 'RAxML':
            if model in prot_models:  # Or use input alphabet variable?!
                return ''.join(('PROTGAMMA',model))
            return 'GTRGAMMA'  # This is true even for other nuc models!
