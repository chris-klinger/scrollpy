"""
Contains classes for configuring console output and logging in ScrollPy.

Using the logging module, filters are applied to all input based on
verbosity and log level arguments defined by the user. The base logger
is configured to DEBUG, but usually only attaches one or two handlers
with ERROR level instead.

Verbosity of each is controlled by a filter and is based on the
configuration defined by the user.
"""

import os
import sys
import shutil
import logging
from logging import StreamHandler
import textwrap
import tempfile
import datetime


from scrollpy import util
from scrollpy import config


# Random utility funtion used in some classes
def _get_current_terminal_width():
    columns,lines = shutil.get_terminal_size(
            fallback=(80,20))
    return columns


# Use to output rich formatting to console/file
rich_format = logging.Formatter(
        # :^<N> centers in a space of N chars long
        fmt = "{asctime} | {name:^30} | {levelname:^10} | {message}",
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
    """Convenience function to return based on __name__"""
    name = "C." + str(name)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger


def get_status_logger(name):
    """Convenience function to return based on __name__"""
    name = "S." + str(name)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger


def get_file_logger(name):
    """Convenience function to return based on __name__"""
    name = "F." + str(name)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger


def get_output_logger(name):
    """Convenience function to return based on __name__"""
    name = "O." + str(name)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger


def get_module_loggers(mod_name):
    """Convenience function to return based on __name__"""
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
        create_dirs=True, no_clobber=False, sep='_'):
    """Returns the name to the logfile

    Checks whether a logfile is needed, and, if so, whether the desired
    file exists. If the specified dir does not exist, makes the dir
    recursively unless 'create_dirs' is False. If the specified file
    exists, replaces it unless 'no_clobber' is True, in which case a
    file with a numeric suffix is created. If needed but nothing is
    specified, creates a generic logfile in 'outdir'.

    Args:
        logging (bool): whether a logfile is needed

        logpath (str): specified name/path for logfile

        outdir (str): path to directory for output files

        create_dirs (bool): whether to create missing directories

        no_clobber (bool): whether to overwrite existing files

        sep (str): separator for filenames

    Returns:
        path to logfile; may be an instance of tempfile.TemporaryFile
    """
    if not_logging:
        return _get_temp_log_path()
    else:
        if logpath:
            # Whether a name or a path, of.path.join() takes care of details
            _logpath = os.path.join(outdir, logpath)
            if util.file_exists(_logpath):  # It is a file that exists; dirname also exists
                dirname,basename = os.path.split(_logpath)
            elif util.dir_exists(_logpath):  # It is a directory that exists
                dirname = _logpath
                basename = _get_generic_logname(sep)
            else:  # It might be either a file or a directory; it does not exist
                dirname,filename = os.path.split(_logpath)
                if not util.dir_exists(dirname):  # file does not exists; dir may
                    if not create_dirs:  # Can't create
                        return _get_temp_log_path()
                    else:
                        util.ensure_dir_exists(dirname)  # Might still specify a file
                if filename != '':  # Only dir
                    basename = _get_generic_logname(sep)
                else:
                    basename = filename
        else:  # logfile name not specified
            dirname = outdir
            basename = _get_generic_logname()
        # No matter what, now we need to get a path
        target_path = os.path.join(dirname,basename)
        if os.path.isfile(target_path):
            if no_clobber:  # Don't overwrite, make unique
                return util.get_nonredundant_filepath(
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


def _get_temp_log_path():
    """Returns path to a closes temp object -> Should be removed"""
    tmpfile = tempfile.NamedTemporaryFile(delete=False)  # Can close and not delete it
    tmpfile.close()  # Log handler trys to open file in mode='a'
    return tmpfile.name  # Path name


def _get_generic_logname(sep='_'):
    """Returns a string that should be unique"""
    now = datetime.datetime.now()
    fmtnow = ("{0:%Y-%m-%d-%H-%M-%S}".format(now))
    return sep.join(("scrollpy",fmtnow,"log.txt"))


def log_message(msg_obj, verbosity, level, *loggers, exc_info=None):
    """Log a message object to any number of loggers.

    Args:
        msg_obj (obj): BraceMessage obj to log

        level (string): Logging module level name, one of:
            'DEBUG','INFO','WARNING','ERROR','CRITICAL'

        *loggers (obj): one or more loggers to log the msg_obj

        exc_info (tuple): exception information
    """
    if exc_info:  # logging an exception
        for logger in loggers:
            if isinstance(logger.handler, logging.FileHandler):
                logger.exception(msg_obj,
                        exc_info=exc_info,
                        extra={'vlevel':verbosity})
            else:  # Writing to console instead
                logger.error(msg_obj,  # Do not include exc_info
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
    """
    Log a blank line on one or more loggers.

    Args:
        *loggers: one or more loggers to log a newline

    """
    if number < 1:
        raise ValueError
    else:
        for logger in loggers:
            # Get current formatter and replace with blank_format
            if not logger.handlers:  # Not the root logger
                target_name = '.'.join(logger.name.split('.')[:2])
                # print("Looking for parent logger {}".format(target_name))
                target_logger = logging.getLogger(target_name)
            else:
                target_logger = logger
            # print("Using target logger {}".format(target_logger.name))
            # print("Target logger has handlers {}".format(target_logger.handlers))
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
    """
    Subclass built-in StreamHandler to enable writing to the screen
    in place for status updates/messages, etc.
    """

    terminator='\r'

    def emit(self, record):
        """
        Emit a record.

        Follows exact same logic as original StreamHandler, but uses
        '\r' instead of '\n' as writing terminator and provides some
        additional logic to fill entire blank lines.

        """
        try:
            msg = self.format(record)
            stream = self.stream
            # Add necessary columns
            # columns,lines = shutil.get_terminal_size(
            #         fallback=(80,20))
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
    """Hack to use {} style formatting in Logging.

    Bonus advantage is that it can be unpacked with more
    ease and handled in filtering classes.

    When logged, the __str__ method is called in place of
    trying to format a plain string message.
    """
    def __init__(self, msg, *args, newline=False, lines=[], **kwargs):
        self.msg = msg
        self.lines = lines
        self.newline = newline
        self.args = args
        self.kwargs = kwargs
        self.wrapped = None  # Initialize to an empty string


    def __str__(self):
        """Writes formatted string if possible; msg if not"""
        if self.wrapped:
            return self.wrapped
        else:
            return self.msg.format(*self.args, **self.kwargs)


    def format_string(self, string):
        """Applies formatting and returns resulting string"""
        return string.format(*self.args, **self.kwargs)


    def get_msg(self):
        """Hide underlying interface"""
        return self.msg


    def add_wrapped(self, msg):
        """Adds a single wrapped message to self"""
        self.wrapped = msg


    def has_lines(self):
        """Hide underlying interface"""
        return len(self.lines) > 0


    def get_lines(self):
        """Hide underlying interface"""
        return self.lines


class GenericFilter:
    """Baseclass for each other Filter class to inherit from.

    Args:
        verbosity (int): argument specifying the filtering level

        silent (bool): if True, no output is produced, regardless
            of verbosity

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
        """Filter message based on set verbosity"""
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
        """Returns a wrapper for subsequent use on text"""
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

    Only includes a leader for WARNING or ERROR, not info
    """
    def __init__(self, verbosity, silent=False):
        term_width = _get_current_terminal_width()
        GenericFilter.__init__(self, verbosity, silent, term_width)


    def _modify_message(self, record):
        """Writes to stderr based on record.level:

            INFO    -> no header
            WARNING -> header
            ERROR   -> header + traceback?

        Uses textwrap.fill() to create a single line for writing; which
        is set to the 'formatted' attr of the Message object.
        """
        if record.exc_info:  # Has exception info
            self._format_exception(record)
        else:
            if record.msg.has_lines():
                self._format_lines(record)
            else:
                self._format_message(record)


    def _format_message(self, record):
        """Add a nice header to each message for console output"""
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
        """Adds a header to a string"""
        if level == 'INFO':
            header = 'ScrollPy: '
        elif level == 'WARNING':
            header = 'ScrollPy [WARNING]: '
        elif level == 'ERROR':  # But no exception info
            header = 'ScrollPy [ERROR]: '
        # Add header in front
        formatted = ' '.join((header, string))
        return (header,formatted)


    def _format_lines(self, record):
        """Useful for exception or other collection-based messages"""
        firstline = True
        to_join = []
        for line in record.msg.get_lines():
            line = record.msg.format_string(line)
            if firstline:
                header,new_msg = _add_header(record.levelname, line)
                to_join.append(new_msg)
            else:
                to_join.append(line)
            firstline = False
        joined = ' '.join(to_join)
        record.msg.add_wrapped(self._get_text_wrapper(
                header=header).fill(joined))


    def _format_exception(self, ex_info):
        """Takes captured traceback info and formats it nicely"""
        pass


class FileFilter(GenericFilter):
    """Class to handle logging messages to a logfile.

    By default, wraps string to 92 characters.

    Similar to ConsoleLogger.
    """
    def __init__(self, verbosity, silent=False):
        GenericFilter.__init__(self, verbosity, silent)
        self.width = 92


    def _modify_message(self, record):
        """Writes to file based on standard logging formatting:

        Uses textwrap.fill() to create a single line for writing; which
        is set to the 'formatted' attr of the Message object.
        """
        if record.exc_info:  # Has exception info
            self._format_exception(record)
        else:
            if record.msg.has_lines():
                self._format_lines(record)
            else:
                self._format_message(record)


    def _format_message(self, record):
        """Simply wraps the message"""
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
        """Don't need header, except for length

        Format is fmt = "{} | {} | {} | {}".format(asctime, name, levelname, message),
        datefmt = '%Y-%m-%d %H:%M:%S',
        typically something like:

        XXXX-XX-XX ZZ-ZZ-ZZ file.root.module WARNING <msg>

        Base it only on name? All output from one module will be at the
        same indentation level.
        """
        return record.name


    def _format_lines(self, record):
        """Useful for exception or other collection-based messages"""
        header = _get_header(record)
        joined = ' '.join(record.msg.get_lines())
        record.msg.add_wrapped(self._get_text_wrapper(
                header=header).fill(joined))


    def _format_exception(self, ex_info):
        """Takes captured traceback info and formats it nicely"""
        pass



class OutputFilter(GenericFilter):
    """Class to handle logging third party program output to log/stderr.

    Very simple - just return as 'formatted'
    """
    def __init__(self, verbosity, silent=False):
        GenericFilter.__init__(self, verbosity, silent)


    def _modify_message(self, record):
        """Even simpler than FileFilter, just return"""
        #message = record.msg.get_msg()  # Should be piped output
        #record.msg.add_wrapped(message)
        pass


