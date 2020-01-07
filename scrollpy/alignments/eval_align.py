"""
This module contains a generic class that will farm out alignment reliability
calls to the relevant program using subprocess.

Class needs to handle all details, including capturing output (file or
stdout, depending on program), capturing stderr to logging, etc.

"""


import os
import subprocess
from subprocess import SubprocessError


class AlignEvaluator:

    def __init__(self, method, cmd, inpath, outpath,  cmd_list=None, **kwargs):
        if self._validate('method', method, self._validate_method):
            self.method = method
        if self._validate('command', cmd, self._validate_command,
                method=method): # Should work; if not set, an Exception was raised
            self.cmd = cmd
        if self._validate('inpath', inpath, self._validate_inpath):
            self.inpath = inpath
        if self._validate('outpath', outpath, self._validate_outpath):
            self.outpath = outpath
        # For finer control, can supply command list instead
        self.cmd_list = cmd_list
        # Should eventually validate kwargs? Or leave for BioPython?
        self.kwargs = kwargs


    # def __repr__(self):
    #     """TO-DO"""
    #     pass


    # def __str__(self):
    #     """TO-DO"""
    #     pass


    def __call__(self):
        """Call method and capture output"""
        if self.method == 'zorro':
            self.cmd_list.insert(0, self.cmd)  # I.e. 'zorro_mac'
            try:
                cmdline = subprocess.run(
                        self.cmd_list,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        )
            except SubproccessError:
                print("Failed to run Zorro")  # Log eventually
            # Output file from stdout
            with open(self.outpath,'w') as o:
                decoded_out = cmdline.stdout.decode()
                o.write(decoded_out)
        # Add other options eventually
        else:
            print("Trying to run{}".format(self.method))


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
        if not method_name in ('zorro', 'Generic'): # For now
            return False
        return True


    def _validate_command(self, command, method=None):
        """Returns True if command makes sense for method"""
        if method == 'zorro':
            path_char = os.sep
            if path_char in command: # Full path given
                cmd = os.path.basename(command)
            else:
                cmd = command
            if cmd not in ('zorro','zorro_mac'):
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
            raise AttributeError("Cannot build tree with {}; directory")
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


