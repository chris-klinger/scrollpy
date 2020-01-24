"""
This module contains a generic class that will farm out program calls
to third-party programs using either Bio.Applications or Subprocess.

Consolidating into a single class for the purposes of reducing arg
validation and logging code.
"""

import os
import sys
import re
import errno
import subprocess
from subprocess import SubprocessError

from Bio.Align import Applications as AA
from Bio.Phylo import Applications as PA
from Bio.Application import ApplicationError

from scrollpy import scroll_log
from scrollpy import config
from scrollpy import BraceMessage
from scrollpy import FatalScrollPyError
from scrollpy import ValidationError
from scrollpy.util._util import modify_model_name



# Get module loggers
(console_logger, status_logger, file_logger, output_logger) = \
        scroll_log.get_module_loggers(__name__)


class Runner:

    # Tuple of valid methods
    _methods = None   # Override in subclass

    # Tuple of valid commands
    _commands = None  # Override in subclass

    def __init__(self, method, cmd, inpath, outpath, cmd_list=None, **kwargs):
        """
        Generic BaseClass for all third-party application running classes.
        Handles argument validation that will be the same across programs,
        such as checking file paths.

        Args:
            method (str): name of the method to run

            cmd (str): command (if executable is in PATH) or full path
                to the executable

            inpath (str): full path to input file

            outpath (str): full path for program output

            **kwargs: additional parameters for the program (optional)

        """
        try:
            if self._validate('method', method, self._validate_method):
                self.method = method
            if self._validate('command', cmd, self._validate_command,
                    method=method): # Should work; if not set, an Exception was raised
                self.cmd = cmd
            if self._validate('inpath', inpath, self._validate_inpath):
                self.inpath = inpath
            if self._validate('outpath', outpath, self._validate_outpath):
                self.outpath = outpath
        # except ValueError as e:
        except ValidationError as e:
            scroll_log.log_message(
                    BraceMessage(""),
                    1,
                    'ERROR',
                    console_logger, file_logger,
                    exc_obj=e,
                    )
            raise FatalScrollPyError
        # For finer control, can supply command list instead
        self.cmd_list = cmd_list
        # Should eventually validate kwargs? Or leave for BioPython?
        self.kwargs = kwargs


    def __repr__(self):
        return "{}({!r}, {!r}, {!r}, {!r}, {!r}, **{!r})".format(
                self.__class__.__name__,
                self.method,
                self.cmd,
                self.inpath,
                self.outpath,
                self.cmd_list,
                self.kwargs,
                )

    def __str__(self):
        return "{} for running {}".format(
                self.__class__.__name__,
                self.method,
                )


    def __call__(self):
        """Override in subclass"""
        raise NotImplementedError


    def _validate(self, name, value, validation_method, **kwargs):
        """
        Calls the required validation method to check input parameters
        during class instantiation (prior to program call).

        Args:
            name (str): name of the arg to validate

            value (str): value passed to the class constructor

            validation_method (str): name of the validation function

            **kwargs: additional parameter information (optional)

        Returns: True if parameter validation is successful; raises
            ValidationError if not.

        """
        if validation_method is not None: # was provided
            try:
                # "Self" argument here is implicit in passed function object
                is_valid = validation_method(value, **kwargs) # May raise exception
            except FileNotFoundError as e:
                scroll_log.log_message(
                        BraceMessage(""),
                        1,
                        'ERROR',
                        console_logger, file_logger,
                        exc_obj=e,
                        )
                is_valid=False
            except AttributeError as e:  # Indicates an inapropriate argument
                scroll_log.log_message(
                        BraceMessage(""),
                        1,
                        'ERROR',
                        console_logger, file_logger,
                        exc_obj=e,
                        )
                is_valid=False
            if not is_valid in (0, 1, True, False): # Truthy values
                scroll_log.log_message(
                        BraceMessage(
                            "Result of {} check on {} yielded unexpected value {}",
                                validation_method.__name__, value, is_valid),
                        1,
                        'ERROR',
                        console_logger, file_logger,
                        )
                is_valid=False
            elif is_valid:
                return True
            else:  # Validation method returned False or raised Exception
                raise ValidationError(value, name)
        # Raise error if no method provided
        else:
            raise ValidationError("No validation method provided")


    def _validate_method(self, method_name):
        """
        Checks whether the method provided is in class tuple.

        Args:
            method_name (str): name of the method

        Returns:
            True if method_name in self._methods; False otherwise

        """
        if not self._methods:
            raise NotImplementedError  #  Baseclass
        elif not method_name in self._methods:
            return False
        return True


    def _validate_command(self, command, method=None):
        """Override in subclass"""
        raise NotImplementedError


    def _validate_inpath(self, inpath):
        """
        Checks whether the specified input file actually exists.

        Args:
            inpath (str): full path to specified input file

        Returns:
            True if file exists; raises FileNotFoundError if not

        """
        if not os.path.exists(inpath):
            raise FileNotFoundError(
                    errno.ENOENT,  # File not found
                    os.strerror(errno.ENOENT),  # Obtain the right error message
                    inpath,  # File name
                    )
        elif os.path.isdir(inpath):
            raise AttributeError(
                    "Specified input file {} is a directory".format(inpath))
        else:  # File exists
            scroll_log.log_message(
                    BraceMessage("Confirmed input file {} exists", inpath),
                    2,
                    'INFO',
                    file_logger,
                    )
        return True


    def _validate_outpath(self, outpath):
        """
        Checks if specified output file already exists. If so, checks
        whether "no_clobber" is set in config file <do something>.

        Args:
            outpath (str): full path to specified output file

        Returns:
            True if output file can be created; raises FileNotFoundError
            if the specified directory does not exist.

        """
        # Gobal settings in config
        no_create = bool(config['ARGS']['no_create'])
        no_clobber = bool(config['ARGS']['no_clobber'])
        # Check whether it exists
        out_dir = os.path.dirname(outpath)
        if not os.path.exists(out_dir):
            if no_create:
                raise FileNotFoundError(
                        errno.ENOENT,  # File not found
                        os.strerror(errno.ENOENT),  # Obtain error message
                        out_dir,  # Directory name
                        )
            else:
                # Create output directory
                pass  # TO-DO!!!
        # Check whether the file already exists
        elif os.path.exists(outpath):
            if no_clobber:
                pass  # Need to get new outpath name
        else:  # Directory exists and file is fine; log it
            scroll_log.log_message(
                    BraceMessage("Confirmed output file {} can be created", outpath),
                    2,
                    'INFO',
                    file_logger,
                    )
        return True


class Aligner(Runner):

    # Tuple of valid methods
    _methods = (
            'Mafft',
            'MafftAdd',
            'Generic',
            )

    # Tuple of valid commands
    _commands = (
            'mafft',
            'mafft-linsi',
            )

    def __init__(self, method, cmd, inpath, outpath, cmd_list=None, **kwargs):
        """
        Subclass of Runner to handle running alignments.

        """
        super().__init__(method, cmd, inpath, outpath, cmd_list, **kwargs)



    def __call__(self):
        """
        Use BioPython commandline wrapper or SubProcess module to run
        third-party program and write/log output.

        """
        # Call separate internal method for each
        if self.method == 'Mafft':
            self._run_mafft()
        elif self.method == 'MafftAdd':  # Add to existing alignment
            self._run_mafftadd()
        # Other methods here eventually
        elif self.method == 'Generic':
            pass # To be implemented


    def _validate_command(self, command, method=None):
        """
        Determine whether the specified command makes sense for the method.

        Args:
            command (str): specified command to execute

            method (str): method to run the command with

        Returns:
            True if the command is valid, False otherwise

        """
        if not method:
            return False  # Somehow not set
        # method should be set; check
        if method == 'Mafft':
            path_char = os.sep
            if path_char in command: # Full path given
                cmd = os.path.basename(command)
            else:
                cmd = command
            if cmd not in ('mafft', 'mafft-linsi'):
                return False
        elif method == 'Generic':  # TO-DO
            if not command == 'None':
                return False
        return True


    def _run_mafft(self):
        """Use BioPython application wrapper to run Mafft"""
        # Log information
        scroll_log.log_message(
                BraceMessage( "Calling Mafft to align sequences"),
                2,
                'INFO',
                file_logger,
                )
        # Set up method
        # cmdline = Applications.MafftCommandline(
        cmdline = AA.MafftCommandline(
            self.cmd, input=self.inpath, **self.kwargs)
        # Try to run
        try:
            stdout, stderr = cmdline() # Need to log stderr eventually
        except ApplicationError as e: # Raised if subprocess return code != 0
            scroll_log.log_message(
                    BraceMessage("Failed to run Mafft"),  # Message necessary?
                    1,
                    'ERROR',
                    console_logger, file_logger,
                    exc_obj=e,
                    )
        # Capture information from program
        with open(self.outpath, 'w') as o:
            o.write(stdout)
        scroll_log.log_message(
                BraceMessage(stderr),
                3,
                'INFO',
                output_logger,
                )


    def _run_mafftadd(self):
        """Use SubProcess to run Mafft with non-standard arguments"""
        # Log information
        scroll_log.log_message(
                BraceMessage( "Calling Mafft to add sequences"),
                2,
                'INFO',
                file_logger,
                )
        # BioPython interface not flexible enough to handle --add for Mafft
        # Set up method using SubProcess instead
        self.cmd_list.insert(0, self.cmd)  # Add to list first
        # Try to run
        try:
            cmdline = subprocess.run(
                self.cmd_list,  # Full command for execution
                stdout=subprocess.PIPE,  # Returns bytes
                stderr=subprocess.PIPE,  # Returns bytes
                )
        except SubprocessError as e:  # Should be default base raised
            scroll_log.log_message(
                    BraceMessage("Failed to run Mafft"),
                    1,
                    'ERROR',
                    console_logger, file_logger,
                    exc_obj=e,
                    )
        # Capture information
        with open(self.outpath, 'w') as o:
            decoded_out = cmdline.stdout.decode()
            o.write(decoded_out)
        decoded_stderr = cmdline.stderr.decode()
        scroll_log.log_message(
                BraceMessage(decoded_stderr),
                3,
                'INFO',
                output_logger,
                )


class AlignEvaluator(Runner):

    # Tuple of valid methods
    _methods = (
            'zorro',
            )

    # Tuple of valid commands
    _commands = (
            'zorro',
            'zorro_mac',
            )

    def __init__(self, method, cmd, inpath, outpath, cmd_list=None, **kwargs):
        """
        Subclass of Runner to handle evaluating alignment columns.

        """
        super().__init__(method, cmd, inpath, outpath, cmd_list, **kwargs)


    def __call__(self):
        """
        Use BioPython commandline wrapper or SubProcess module to run
        third-party program and write/log output.

        """
        # Call separate internal method for each
        if self.method == 'zorro':
            self._run_zorro()
        # Other methods here eventually
        else:
            pass  # For now


    def _validate_command(self, command, method=None):
        """
        Determine whether the specified command makes sense for the method.

        Args:
            command (str): specified command to execute

            method (str): method to run the command with

        Returns:
            True if the command is valid, False otherwise

        """
        if not method:
            return False  # Somehow not set
        # method should be set; check
        if method == 'zorro':
            path_char = os.sep
            if path_char in command: # Full path given
                cmd = os.path.basename(command)
            else:
                cmd = command
            if cmd not in self._commands:
                return False
        else:  # Add more methods later
            return False
        return True


    def _run_zorro(self):
        """Use SubProcess to run Zorro"""
        # Log information
        scroll_log.log_message(
                BraceMessage( "Calling Zorro to evaluate alignment"),
                2,
                'INFO',
                file_logger,
                )
        # BioPython interface does not handle Zorro
        # Set up method using SubProcess instead
        self.cmd_list.insert(0, self.cmd)  # Add to list first
        # Try to run
        try:
            cmdline = subprocess.run(
                self.cmd_list,  # Full command for execution
                stdout=subprocess.PIPE,  # Returns bytes
                stderr=subprocess.PIPE,  # Returns bytes
                )
        except SubprocessError as e:  # Should be default base raised
            scroll_log.log_message(
                    BraceMessage("Failed to run Zorro"),
                    1,
                    'ERROR',
                    console_logger, file_logger,
                    exc_obj=e,
                    )
        # Capture information
        with open(self.outpath, 'w') as o:
            decoded_out = cmdline.stdout.decode()
            o.write(decoded_out)
        decoded_stderr = cmdline.stderr.decode()
        scroll_log.log_message(
                BraceMessage(decoded_stderr),
                3,
                'INFO',
                output_logger,
                )


class DistanceCalc(Runner):

    # Tuple of valid methods
    _methods = (
            'RAxML',
            'Generic',
            )

    # Tuple of valid commands
    _commands = None  # RAxML works differently

    def __init__(self, method, cmd, inpath, outpath, cmd_list=None, **kwargs):
        """
        Subclass of Runner to handle running distance calculations.

        """
        super().__init__(method, cmd, inpath, outpath, cmd_list, **kwargs)
        try:
            self.model = kwargs['model']
        except KeyError:
            raise ValidationError(
                    "No evolutionary model provided for distance calculation")


    def __call__(self):
        """
        Use BioPython commandline wrapper or SubProcess module to run
        third-party program and write/log output.

        """
        # Call separate internal method for each
        if self.method == 'RAxML':
            self._run_raxml()
        # Other methods here eventually
        else:
            pass  # For now


    def _validate_command(self, command, method=None):
        """
        Determine whether the specified command makes sense for the method.

        Args:
            command (str): specified command to execute

            method (str): method to run the command with

        Returns:
            True if the command is valid, False otherwise

        """
        if not method:
            return False  # Somehow not set
        # method should be set; check
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
                raise AttributeError(
                        "Could not validate RAxML command {}".format(cmd))
        elif method == 'Generic':
            if not command == 'None':
                return False
        return True


    def _run_raxml(self):
        """Use SubProcess to run RAxML"""
        # Log information
        scroll_log.log_message(
                BraceMessage( "Calling RAxML to evaluate distances"),
                2,
                'INFO',
                file_logger,
                )
        # Set up method
        dirname,outname = os.path.split(self.outpath)
        # Specify distance calculation
        self.kwargs['-f'] = 'x'
        # Convert in and out file paths to RAxML arguments
        # Should eventually have a method to validate these
        self.kwargs['-s'] = self.inpath
        # RAxML is weird; if not curdir for outpath must specify using -w
        self.kwargs['-w'] = dirname
        self.kwargs['-n'] = outname
        # Change model input to a usable command
        self.kwargs['-m'] = modify_model_name(self.model,'RAxML')
        # If a nuc model is specified other than GTR, need to add to kwargs
        if self.model in ['JC','K80','HKY85']:
            arg_string = '--' + self.model
            self.kwargs[arg_string] = ''  # just need to add the arg itself
        # Call command line with modified args
        # cmdline = Applications.RaxmlCommandline(
        cmdline = PA.RaxmlCommandline(
            self.cmd,
            **self.kwargs,
            )
        # Try to run
        try:
            stdout, stderr = cmdline() # Need to log stderr eventually
        except ApplicationError as e: # Raised if subprocess return code != 0
            scroll_log.log_message(
                    BraceMessage("Failed to run RAxML"),  # Message necessary?
                    1,
                    'ERROR',
                    console_logger, file_logger,
                    exc_obj=e,
                    )
        # Capture information from program
        with open(self.outpath, 'w') as o:
            o.write(stdout)
        scroll_log.log_message(
                BraceMessage(stderr),
                3,
                'INFO',
                output_logger,
                )


class TreeBuilder(Runner):

    # Tuple of valid methods
    _methods = (
            'Iqtree',
            'RAxML',
            )

    # Tuple of valid commands
    _commands = (
            'iqtree',
            )

    def __init__(self, method, cmd, inpath, outpath, cmd_list=None, **kwargs):
        """
        Subclass of Runner to handle running tree building

        """
        super().__init__(method, cmd, inpath, outpath, cmd_list, **kwargs)
        try:
            self.model = kwargs['model']
        except KeyError:
            self.model = None


    def __call__(self):
        """
        Use BioPython commandline wrapper or SubProcess module to run
        third-party program and write/log output.

        """
        # Call separate internal method for each
        if self.method == 'Iqtree':
            self._run_iqtree()
        elif self.method == 'RAxML':
            self._run_raxml()
        # Other methods here eventually
        else:
            pass  # For now


    def _validate_command(self, command, method=None):
        """
        Determine whether the specified command makes sense for the method.

        Args:
            command (str): specified command to execute

            method (str): method to run the command with

        Returns:
            True if the command is valid, False otherwise

        """
        if not method:
            return False  # Somehow not set
        if method == 'Iqtree':
            path_char = os.sep
            if path_char in command: # Full path given
                cmd = os.path.basename(command)
            else:
                cmd = command
            if cmd not in ('iqtree'):
                return False
        # method should be set; check
        elif method == 'RAxML':
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
                return False
        elif method == 'Generic':
            if not command == 'None':
                return False
        return True


    def _run_iqtree(self):
        """Use SubProcess to run Iqtree"""
        # Log information
        scroll_log.log_message(
                BraceMessage("Calling IQ-Tree to build phylogeny"),
                2,
                'INFO',
                file_logger,
                )
        # Set up method using SubProcess
        self.cmd_list.insert(0, self.cmd)  # Add to list first
        # Try to run
        try:
            cmdline = subprocess.run(
                self.cmd_list,  # Full command for execution
                stdout=subprocess.PIPE,  # Returns bytes
                stderr=subprocess.PIPE,  # Returns bytes
                )
        except SubprocessError as e:  # Should be default base raised
            scroll_log.log_message(
                    BraceMessage("Failed to run IQ-Tree"),
                    1,
                    'ERROR',
                    console_logger, file_logger,
                    exc_obj=e,
                    )
        # Capture information
        # OUTPUT FILE IS THE SUMMARY FILE!
        # with open(self.outpath, 'w') as o:
        #     decoded_out = cmdline.stdout.decode()
        #     o.write(decoded_out)
        decoded_stderr = cmdline.stderr.decode()
        scroll_log.log_message(
                BraceMessage(decoded_stderr),
                3,
                'INFO',
                output_logger,
                )


    def _run_raxml(self):  # TO-DO: Fix this!!!
        """Use SubProcess to run RAxML"""
        # Log information
        scroll_log.log_message(
                BraceMessage( "Calling RAxML to build phylogeny"),
                2,
                'INFO',
                file_logger,
                )
        # Set up method
        # Specify ML search + rapid bootstrap
        self.kwargs['-f'] = 'a'
        # Convert in and out file paths to RAxML arguments
        # Should eventually have a method to validate these
        self.kwargs['-s'] = self.inpath
        # RAxML is weird; if not curdir for outpath must specify using -w
        self.kwargs['-w'] = dirname
        self.kwargs['-n'] = outname
        # Change model input to a usable command
        self.kwargs['-m'] = modify_model_name(self.model,'RAxML')
        # If a nuc model is specified other than GTR, need to add to kwargs
        if self.model in ['JC','K80','HKY85']:
            arg_string = '--' + self.model
            self.kwargs[arg_string] = ''  # just need to add the arg itself
        # Call command line with modified args
        # cmdline = Applications.RaxmlCommandline(
        cmdline = PA.RaxmlCommandline(
            self.cmd,
            **self.kwargs,
            )
        # Try to run
        try:
            stdout, stderr = cmdline() # Need to log stderr eventually
        except ApplicationError as e: # Raised if subprocess return code != 0
            scroll_log.log_message(
                    BraceMessage("Failed to run RAxML"),  # Message necessary?
                    1,
                    'ERROR',
                    console_logger, file_logger,
                    exc_obj=e,
                    )
        # Capture information from program
        with open(self.outpath, 'w') as o:
            o.write(stdout)
        scroll_log.log_message(
                BraceMessage(stderr),
                3,
                'INFO',
                output_logger,
                )
