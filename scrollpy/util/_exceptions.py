"""
Contains exception classes for Scrollpy.

"""

class ScrollPyError(Exception):
    """
    Catch-all exception for errors specific to the ScrollPy library.

    """
    def __init__(self, msg=None):
        if not msg:
            # Provide a useful default
            msg = "A serious error occurred during ScrollPy execution."
        super().__init__(msg)


class FatalScrollPyError(ScrollPyError):
    """
    Raised from within other code blocks to signal that an error has
    occurred that cannot be recovered and the program should run any
    cleanup code before exiting.

    """
    def __init__(self, msg=None):
        if not msg:
            msg = "Scrollpy has encountered a fatal error; terminating..."
        super().__init__(msg)


class DuplicateSeqError(ScrollPyError):
    """
    Raised during sequence mapping when two or more labels are mapped to
    the same sequence object.

    """
    def __init__(self, seq_name, msg=None):
        if not msg:
            msg = "Duplicate sequence {} detected.".format(seq_name)
        super().__init__(msg)

        self.seq_name = seq_name


class ValidationError(ScrollPyError):
    """
    Raised during parameter validation.

    """
    def __init__(self, param, value, msg=None):
        if not msg:
            msg = "Invalid parameter {} for {}".format(param,value)
        super().__init__(msg)

        self.param = param
        self.value = value
