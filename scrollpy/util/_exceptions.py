#!/usr/bin/env python3

###################################################################################
##
##  ScrollPy: Utility Functions for Phylogenetic Analysis
##
##  Developed by Christen M. Klinger (cklinger@ualberta.ca)
##
##  Please see LICENSE file for terms and conditions of usage.
##
##  Please cite as:
##
##  Klinger, C.M. (2020). ScrollPy: Utility Functions for Phylogenetic Analysis.
##  https://github.com/chris-klinger/scrollpy.
##
##  For full citation guidelines, please call ScrollPy using '--citation'
##
###################################################################################

"""
Contains exception classes for use throughout ScrollPy.

"""


class ScrollPyError(Exception):
    """Baseclass for all exceptions specific to the ScrollPy library.

    Args:
        msg (str): A message to be stored within the instance.
            Default None.

    """
    def __init__(self, msg=None):
        if not msg:
            # Provide a useful default
            msg = "A serious error occurred during ScrollPy execution."
        super().__init__(msg)


class FatalScrollPyError(ScrollPyError):
    """Error indicating that the program should terminate execution.

    Raised from within other blocks of code to signal the program to clean
    up and halt further execution.

    Note:
        Should only ever be caught by main().

    """
    def __init__(self, msg=None):
        if not msg:
            msg = "Scrollpy has encountered a fatal error; terminating..."
        super().__init__(msg)


class DuplicateSeqError(ScrollPyError):
    """Error indicating the presence of redundant sequences.

    Raised during sequence mapping when two or more labels are mapped to
    the same sequence object. These labels may or may not refer to the
    same (identical) sequences, but their mapping is not unique.

    Args:
        seq_name (str): Name of the duplcate sequence detected.
        msg (str): Optional message (see baseclass). Default None.

    Attributes:
        seq_name (str): Name of the duplicate sequence detected.

    """
    def __init__(self, seq_name, msg=None):
        if not msg:
            msg = "Duplicate sequence {} detected.".format(seq_name)
        super().__init__(msg)

        self.seq_name = seq_name


class ValidationError(ScrollPyError):
    """Error indicating that a parameter has failed a validation call.

    Raised from code blocks that perform validation on input parameters
    during program execution.

    Args:
        param (str): The name of the parameter passed.
        value: The value passed for the parameter. The parameter type is
            not set and will depend on the calling context.

    Attributes:
        param (str): The name of the parameter passed.
        value: The value passed for the parameter.

    """
    def __init__(self, param, value, msg=None):
        if not msg:
            msg = "Invalid parameter {} for {}".format(param,value)
        super().__init__(msg)

        self.param = param
        self.value = value
