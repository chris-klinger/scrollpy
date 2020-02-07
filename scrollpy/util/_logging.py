"""Contains classes for configuring console output and logging in ScrollPy.

Using the logging module, filters are applied to all input based on
verbosity and log level arguments defined by the user. The base logger is
configured to DEBUG, but usually only attaches one or two handlers with
ERROR level instead.

In practice, the verbosity of each output is controlled by a filter and is
based on the configuration defined by the user, whereby the decision to
output the message is based on whether it meets the 'verbosity' (for
output to the terminal) and/or 'log_level' (for output to the logfile)
settings. Each message has an associated value for its level.

This is facilitated by using a custom BraceMessage class, which also
allows client code to make use of the new {} style string formatting.


Attributes:
    rich_format: A logging.Formatter instance for logfile output
    raw_format: A logging.Formatter instance for stderr messages
    blank_format: A logging.Formatter instance for writing blank lines

"""

import os
import sys
import re
import shutil
import logging
from logging import StreamHandler
import traceback
import textwrap
import tempfile
import datetime

# Use absolute imports here due to import order
from scrollpy.util import _util as scrollutil
from scrollpy.config import _config as config


# Random utility funtion used in some classes
def _get_current_terminal_width():
    """Utility function that measures the terminal width.

    Returns:
        int: The width of the current terminal. If this value cannot be
            obtained, returns a fallback value of 80.

    """
    columns,lines = shutil.get_terminal_size(
            fallback=(80,20))
    return columns


# Use to output rich formatting to console/file
rich_format = logging.Formatter(
        # :^<N> centers in a space of N chars long
        fmt = "{asctime} | {name:^35} | {levelname:^10} | {message}",
        datefmt = '%Y-%m-%d %H:%M:%S',
        style = '{',
        )

# Simple formatting -> necessary?
#basic_format = logging.Formatter(
#        fmt = "{levelname:8s} | {message}",
#        style = '{',
#        )

# Use to output without formatting, e.g. program stderr messages
raw_format = logging.Formatter(
        fmt = "{message}",
        style = '{',
        )

# Use to write blank lines
blank_format = logging.Formatter(fmt="")


def get_console_logger(name):
    """Obtain the console logger for a module.

    The console logger is responsible for logging normal program progress
    calls to the console/terminal.

    Args:
        name (str): Name of the logger. Should be __name__.

    Returns:
        obj: A Logger instance, based on name.

    """
    name = "C." + str(name)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger


def get_status_logger(name):
    """Obtain the status logger for a module.

    The status logger is responsible for logging specific progress
    messages on a single line to the console.

    See get_console_logger docstring for more detail.

    """
    name = "S." + str(name)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger


def get_file_logger(name):
    """Obtain the file logger for a module.

    The file logger is responsible for logging to the logfile.

    See get_console_logger docstring for more detail.

    """
    name = "F." + str(name)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger


def get_output_logger(name):
    """Obtain the status logger for a module.

    The output logger is responsible for logging output of third-party
    applications to the logfile.

    See get_console_logger docstring for more detail.

    """
    name = "O." + str(name)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger


def get_module_loggers(mod_name):
    """Obtain all of the loggers for a given module.

    Primarily a convenience function to return all four possible logger
    objects based on a module's __name__ attribute.

    Args:
        mod_name: The name of the module (should be __name__).

    Returns:
        tuple: A tuple of four logger objects in the order console,
            status, file, and output logger.

    """
    c_logger = get_console_logger(mod_name)
    s_logger = get_status_logger(mod_name)
    f_logger = get_file_logger(mod_name)
    o_logger = get_output_logger(mod_name)
    # Return in specific order
    return (
            c_logger,  # Console
            s_logger,  # Status
            f_logger,  # File
            o_logger,  # Output
            )


def get_logfile(not_logging=False, logpath=None, outdir=None,
        no_create=False, no_clobber=False, sep='_'):
    """Returns the full path to a logfile for each program run.

    Checks whether a logfile is needed, and, if so, whether the desired
    file exists. If the specified dir does not exist, makes the dir
    recursively unless 'create_dirs' is False. If the specified file
    exists, replaces it unless 'no_clobber' is True, in which case a
    file with a numeric suffix is created. If needed but nothing is
    specified, creates a generic logfile in 'outdir'.

    Args:
        not_logging (bool): If the user has specified not to log.
            Default to False.
        logpath (str): Specified name/path for the logfile.
        outdir (str): Full path to the directory for output files.
        no_create (bool): Whether to create missing directories.
            Default to True.
        no_clobber (bool): Whether to overwrite existing files
        sep (str): separator for filenames

    Returns:
        path to logfile; may be an instance of tempfile.TemporaryFile

    """
    if not_logging:
        return _get_temp_log_path()
    else:
        dirname,basename = _get_real_logpath(
                logpath,
                outdir,
                sep,
                )
    # Check to make sure name is ok
    if not scrollutil.is_value_ok_with_path(basename):
        basename = scrollutil.make_ok_with_path(basename)
    # No matter what, now we need to get a path
    target_path = os.path.join(dirname,basename)
    # Check to see whether the directory exists
    if not scrollutil.dir_exists(dirname):
        # print("Directory does not exist")
        if no_create:  # Can't create new dirs
            return _get_temp_log_path()
        else:
            # print("Trying to make directory")
            scrollutil.ensure_dir_exists(dirname)  # Might still specify a file
    # Check filename itself
    if os.path.isfile(target_path):
        if no_clobber:  # Don't overwrite, make unique
            return scrollutil.get_nonredundant_filepath(
                    dirname,  # dir_path
                    basename,  # filename
                    )  # starting suffix = 1
        else:  # Try to replace
            try:
                os.remove(target_path)
            except OSError:
                sys.exit(1)  # This should not happen
            return target_path  # Replace old file
    # Return path if everything is ok
    return target_path


def _get_real_logpath(logpath=None, outdir=None, sep='_'):
    """Returns a directory and filename for a target logfile.

    Args:
        logpath (str): Specified name/path for the logfile.
        outdir (str): Full path to the directory for output files.
        sep (str): separator for filenames

    Returns:
        tuple: A 2-length tuple of (directory, filename).

    """
    if logpath:
        # Whether a name or a path, of.path.join() takes care of details
        _logpath = os.path.join(outdir, logpath)
        if scrollutil.file_exists(_logpath):
            # It is a file that exists; dirname also exists
            dirname,basename = os.path.split(_logpath)
        elif scrollutil.dir_exists(_logpath):
            # It is a directory that exists
            dirname = _logpath
            basename = _get_generic_logname(sep)
        else:  # It might be either a file or a directory; it does not exist
            dirname,filename = os.path.split(_logpath)
            if filename == '':  # Only dir
                basename = _get_generic_logname(sep)
            else:
                basename = filename
    else:  # logfile name not specified
        dirname = outdir
        basename = _get_generic_logname()

    return dirname,basename

def _get_temp_log_path():
    """Obtains the path to a temporary logfile.

    Returns:
        str: The full path to a temporary logfile. The file that the path
            refers to should is closed and must be reopened.

    """
    tmpfile = tempfile.NamedTemporaryFile(delete=False)  # Can close and not delete it
    tmpfile.close()  # Log handler trys to open file in mode='a'
    return tmpfile.name  # Path name


def _get_generic_logname(sep='_'):
    """Obtains a logfile name.

    Args:
        sep (str): The separator character used between name elements.
            Defaults to '_'.

    Returns:
        str: The logfile name.

    """
    now = datetime.datetime.now()
    fmtnow = ("{0:%Y-%m-%d-%H-%M-%S}".format(now))
    return sep.join(("scrollpy",fmtnow,"log.txt"))


def log_message(msg_obj, verbosity, level, *loggers, exc_obj=None):
    """Log a message object to any number of loggers.

    Args:
        msg_obj (obj): BraceMessage obj to log.
        verbosity (int): The relative urgency of the message.
        level (string): Logging module level name, one of:
            'DEBUG','INFO','WARNING','ERROR','CRITICAL'.
        *loggers: One or more loggers to log the msg_obj.
        exc_obj (obj): Exception object from a handling block.
            Defaults to None.

    """
    if exc_obj:  # logging an exception
        for logger in loggers:
            # Capture traceback information
            tb_obj = exc_obj.__traceback__
            # tb_str = traceback.format_tb(tb_obj)[0]
            tb_stack = traceback.extract_tb(tb_obj,1)[0]
            msg_obj.lines = [
                    "ScrollPy threw a {}".format(exc_obj.__class__.__name__),
                    "in module {}".format(tb_stack.filename),
                    "on line {}".format(tb_stack.lineno),
                    "while executing {}: ".format(tb_stack.name),
                    "{}".format(exc_obj.__str__()),
                    ]
            # Add necessary info to msg_obj
            # msg_obj.lines = tb_str.split(',')
            msg_obj.exception = True
            # Log as error with traceback info
            logger.error(msg_obj,
                    extra={'vlevel':verbosity})
    elif level == 'DEBUG':
        for logger in loggers:
            logger.debug(msg_obj,
                    extra={'vlevel':verbosity})
    elif level == 'INFO':
        for logger in loggers:
            logger.info(msg_obj,
                    extra={'vlevel':verbosity})
    elif level == 'WARNING':
        for logger in loggers:
            logger.warning(msg_obj,
                    extra={'vlevel':verbosity})
    elif level == 'ERROR':
        for logger in loggers:
            logger.error(msg_obj,
                    extra={'vlevel':verbosity})


def log_newlines(*loggers, number=1):
    """ Log one or more blank lines on one or more loggers.

    Args:
        *loggers: One or more loggers to log a newline.
        number (int): The number of newlines to log. Defaults to 1.

    """
    if number < 1:
        raise ValueError
    else:
        for logger in loggers:
            # Get current formatter and replace with blank_format
            if not logger.handlers:  # Not the root logger
                target_name = '.'.join(logger.name.split('.')[:2])
                target_logger = logging.getLogger(target_name)
            else:
                target_logger = logger
            current_handler = target_logger.handlers[0]  # Each logger has only one handler
            current_formatter = current_handler.formatter
            current_handler.setFormatter(raw_format)
            # Now log newlines
            for i in range(number):
                logger.info(
                        BraceMessage(
                            "",            # Message is just an empty string
                            newline=True,  # newline=True tells Filters not to bother
                            ),
                        extra={'vlevel':1},
                        )
            # Reset formatter
            current_handler.setFormatter(current_formatter)


class StreamOverwriter(StreamHandler):
    """Subclasses logging.StreamHandler to write in place.

    Standard logging handlers append newline characters to each logged
    message internally. Subclassing and replacing the StreamHandler's
    terminator attribute overrides this behaviour.

    Attributes:
        terminator (str): Terminating character for logged messages.

    """

    terminator='\r'

    def emit(self, record):
        """ Emit a record.

        Follows exact same logic as the original StreamHandler, but uses
        '\r' instead of '\n' as the line terminator and provides some
        additional logic to fill entire blank lines.

        Args:
            record (obj): A BraceMessage object, or other record object
                that provides a __str__ method.

        """
        try:
            msg = self.format(record)
            stream = self.stream
            # Add necessary columns
            columns = _get_current_terminal_width()
            full_line = msg + ((columns - len(msg)) * ' ')
            # issue 35046: merged two stream.writes into one.
            stream.write(full_line + self.terminator)
            self.flush()
        except RecursionError:  # See issue 36272
            raise
        except Exception:
            self.handleError(record)


class BraceMessage:
    """Provides a message class for logging that uses brace formatting.

    When logged, the __str__ method is called, allowing the class to
    handle all of the necessary string formatting prior to the handler
    emitting the record.

    Args:
        msg (str): The string message to be logged, may or may not contain
            brace-style formatted values.
        *args: If the passed msg has brace placeholders, *args will be
            used to replace each in positional order.
        newline (bool): Whether the logging call is intended just to write
            one or more newlines. Defaults to False.
        exception (bool): Whether the message contains exception information.
            Defaults to False.
        lines (list): Information to write that is passed as a list rather
            than as a single string. Default to [].
        **kwargs: If the passed msg has named brace placeholders, **kwargs
            will be used to replace each.

    Attributes:
        msg (str): A string message to be logged.
        lines (list): A list of strings to be logged. May be empty.
        newline (bool): Whether newlines are being logged.
        exception (bool): Whether exception information is being logged.
        args: Values to be used for string formatting.
        kwargs: Values to be used for string formatting.
        wrapped: Stores a message that has been processed by a handler.

    """
    def __init__(self, msg, *args, newline=False, exception=False, lines=[], **kwargs):
        self.msg = msg
        self.lines = lines
        self.newline = newline
        self.exception = exception
        self.args = args
        self.kwargs = kwargs
        self.wrapped = None  # Initialize to an empty string


    def __str__(self):
        """Writes a formatted string if possible; self.msg if not"""
        if self.wrapped:
            return self.wrapped
        else:
            return self.msg.format(*self.args, **self.kwargs)


    def format_string(self, string):
        """Applies formatting and returns resulting string"""
        return string.format(*self.args, **self.kwargs)


    def get_msg(self):
        """Simple access method for external handlers"""
        return self.msg


    def add_wrapped(self, msg):
        """Adds a single wrapped message to self"""
        self.wrapped = msg


    def has_lines(self):
        """Simple access method for external handlers"""
        return len(self.lines) > 0


    def get_lines(self):
        """Simple access method for external handlers"""
        return self.lines


class GenericFilter:
    """Baseclass for each other Filter class to inherit from.

    Args:
        verbosity (int): Specifies the filtering level.
        silent (bool): Whether to produce output. Defaults to False.
        width (int): Width to wrap text to. Defaults to 78.

    Attributes:
        verbosity (int): Desired output level for filtering.
        silent (bool): If True, filter produces no output.
        width (int): The width that text will be wrapped to.

    Methods:
        filter (self, record): wrap message and return it, along with
            any of *args, **kwargs to be passed onto Handler.Formatter
            or return False if vlevel < self.verbosity

    """
    def __init__(self, verbosity, silent=False, width=78):
        self.verbosity = verbosity
        self.silent = silent
        self.width = width


    def filter(self, record):
        """Filter a record message based on set verbosity

        If a message has a lower verbosity level than the instance value,
        wrap the message and return it to be passed onto the Handler.

        Args:
            record (obj): A BraceMessage object.

        Returns:
            bool: False is silent is set to True or if the record's
                verbosity level is higher than the set value. Otherwise,
                modify the record message and return True.

        """
        if self.silent:
            return False
        elif record.vlevel <= self.verbosity:  # Opposite of logging levels
            self._modify_message(record)  # Try to format!
            return True
        return False


    def _modify_message(self, record):
        """Modify message in LogRecord, if necessary, and return"""
        raise AttributeError("Implement in subclass")


    def _format_message(self, record):
        """Format message; specially handles exc_info if present"""
        raise AttributeError("Implement in subclass")


    def _get_text_wrapper(self, width=None, header='ScrollPy'):
        """Obtains a text wrapping object for use on formatted text.

        Args:
            width (int): Specified width for text. Defaults to None.
            header (str): A header that has been added to the text, if
                necessary. Defaults to 'ScrollPy'.

        Returns:
            obj: An instance of textwrap.TextWrapper to wrap text.

        """
        if not width:
            width = self.width
        return textwrap.TextWrapper(
                width=width,         # normal term width?
                initial_indent='',   # first line
                subsequent_indent=(  # padding for each subsequent line
                    ' ' * (len(header) + 2)),
                )


    def _format_lines(self, lines):
        """Useful for exception or other collection-based messages"""
        raise AttributeError("Implement in sublass")


    def _format_exception(self, record):
        """Takes captured traceback info and formats it nicely"""
        raise AttributeError("Implement in sublass")


class ConsoleFilter(GenericFilter):
    """Class to filter console messages.

    By default, wraps string to 78 characters.

    Only includes a leader for WARNING or ERROR, not info.

    For more documentation, see baseclass docstring.

    """
    def __init__(self, verbosity, silent=False):
        term_width = _get_current_terminal_width()
        GenericFilter.__init__(self, verbosity, silent, term_width)


    def _modify_message(self, record):
        """Modify a message appropriately.

        Args:
            record (obj): The BraceMessage object to filter.

        """
        # if record.exc_info:  # Has exception info
        if record.msg.exception:
            self._format_exception(record)
        else:
            if record.msg.has_lines():
                self._format_lines(record)
            else:
                self._format_message(record)


    def _format_message(self, record):
        """Handle message formatting and wrapping.

        If the record is a newline, simply add the empty string to the
        record's wrapped attribute. Otherwise, add a header (if the level
        is 'WARNING' or 'ERROR', and then wrap text.

        Uses textwrap.fill() to create a single line for writing; which
        is set to the 'wrapped' attr of the Message object.

        Args:
            record (obj): The BraceMessage object to format.

        """
        _message = record.msg.get_msg()
        # If newline, don't add anything
        if record.msg.newline:
            record.msg.add_wrapped(_message)
        # Else, properly format and return
        else:
            message = record.msg.format_string(_message)
            # Add header in front
            header,new_msg = self._add_header(record.levelname, message)
            # Wrap to return a single string
            record.msg.add_wrapped(self._get_text_wrapper(
                    header=header).fill(new_msg))


    def _add_header(self, level, string):
        """Adds a header to the string based on the message level.

        The message is modified based on the level:

            INFO    -> no header
            WARNING -> header
            ERROR   -> header + traceback?

        Args:
            level (int): The message's associated logging level.
            string (str): The string to add a header to.

        Returns:
            str: Same as input string, but with a header prepended.

        """
        if level == 'INFO':
            header = 'ScrollPy: '
        elif level == 'WARNING':
            header = 'ScrollPy [WARNING]: '
        elif level == 'ERROR':  # But no exception info
            header = 'ScrollPy [ERROR]: '
        # Add header in front
        formatted = ''.join((header, string))
        return (header,formatted)


    # Is this necessary?
    def _format_lines(self, record):
        """Formats multiple lines into a single message.

        Args:
            record (obj): A BraceMessage object to format.

        """
        firstline = True
        to_join = []
        for line in record.msg.get_lines():
            line = record.msg.format_string(line)
            if firstline:
                header,new_msg = self._add_header(record.levelname, line)
                to_join.append(new_msg)
            else:
                to_join.append(line)
            firstline = False
        joined = ' '.join(to_join)
        record.msg.add_wrapped(self._get_text_wrapper(
                header=header).fill(joined))


    def _format_exception(self, record):
        """Formats an exception to display only some information.

        Captured exception information is already stored in the record's
        lines attribute. Extract only the associated msg attribute from
        the original exception and format it.

        Args:
            record (obj): A BraceMessage object to format.

        """
        lines = record.msg.get_lines()
        exc_msg = lines[-1]  # Last element
        # Add to the original message object
        _message = record.msg.get_msg()
        message = _message + exc_msg
        record.msg.msg = message
        # Now call normal formatting code
        self._format_message(record)


class FileFilter(GenericFilter):
    """Class to handle logging messages to a logfile.

    By default, wraps string to 128 characters.

    Similar to ConsoleLogger.

    """
    def __init__(self, verbosity, silent=False):
        GenericFilter.__init__(self, verbosity, silent)
        self.width = 128


    def _modify_message(self, record):
        """Modify a message appropriately.

        Args:
            record (obj): The BraceMessage object to filter.

        """
        if record.exc_info:  # Has exception info
            self._format_exception(record)
        else:
            if record.msg.has_lines():
                self._format_lines(record)
            else:
                self._format_message(record)


    def _format_message(self, record):
        """Handle message formatting and wrapping.

        If the record is a newline, simply add the empty string to the
        record's wrapped attribute. Otherwise, add a header (if the level
        is 'WARNING' or 'ERROR', and then wrap text.

        Uses textwrap.fill() to create a single line for writing; which
        is set to the 'wrapped' attr of the Message object.

        Args:
            record (obj): The BraceMessage object to format.

        """
        _message = record.msg.get_msg()
        # Do not apply formatting if newline
        if record.msg.newline:
            record.msg.add_wrapped(_message)
        # Else, format and return full thing
        else:
            message = record.msg.format_string(_message)
            # Figure out what the header is
            header = self._get_header(record)
            # Wrap to return a single string
            record.msg.add_wrapped(self._get_text_wrapper(
                    header=header).fill(message))


    def _get_header(self, record):
        """Obtains a full header that mirrors rich formatting.

        In order for the text wrapping to work properly, need to obtain
        a string that is the same as the rich_format Formatter defined in
        this module.

        Format is fmt = "{} | {} | {} | {}".format(
            asctime, name, levelname, message)
        Where the datefmt = '%Y-%m-%d %H:%M:%S'.

        This is typically something like:

        XXXX-XX-XX ZZ-ZZ-ZZ file.root.module WARNING <msg>

        Args:
            record (obj): A BraceMessage object to be formatted.

        Returns:
            str: A string representing the corresponding header in the
                logfile; importantly, it has the same length.

        """
        # return record.name
        now = datetime.datetime.now()
        fmtnow = ("{0:%Y-%m-%d-%H-%M-%S}".format(now))
        return "{asctime} | {name:^35} | {levelname:^10} |".format(
                asctime=fmtnow,
                name=record.name,
                levelname='WARNING',  # Longest levelname option
                )


    def _format_lines(self, record):
        """Formats multiple lines into a single message.

        Args:
            record (obj): A BraceMessage object to format.

        """
        header = self._get_header(record)
        joined = ' '.join(record.msg.get_lines())
        record.msg.add_wrapped(self._get_text_wrapper(
                header=header).fill(joined))


    def _format_exception(self, record):
        """Formats an exception to include all of the information.

        Captured exception information is already stored in the record's
        lines attribute. Unlike ConsoleFilter class, FileFilter objects
        will simply format all captured information.

        Args:
            record (obj): A BraceMessage object to format.

        """
        # Simple; just call _format_lines
        self._format_lines(record)


class OutputFilter(GenericFilter):
    """Class to handle logging third party program output to log/stderr.

    Very simple - just return as 'formatted'.

    """
    def __init__(self, verbosity, silent=False):
        GenericFilter.__init__(self, verbosity, silent)


    def _modify_message(self, record):
        """Even simpler than FileFilter, just return"""
        pass


