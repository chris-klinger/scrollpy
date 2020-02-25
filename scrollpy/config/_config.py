#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
Loads the configuration file into a config variable.

"""

import os
import sys
from configparser import ConfigParser
from configparser import DuplicateSectionError
from configparser import DuplicateOptionError

# Use absolute imports here due to import order
from scrollpy.util import _logging as scroll_log
from scrollpy.util._exceptions import FatalScrollPyError


file_dir = os.path.dirname(os.path.realpath(__file__))

config_file = os.path.realpath(os.path.join(file_dir, '../../_scrollpy.conf'))

config = ConfigParser(
        allow_no_value = True, # Unused methods can be anything
        strict = True, # Default but emphasized -> NO DUPLICATES
        empty_lines_in_values = False, # Preferably one value per line
        )

# Set up loggers
(console_logger, status_logger, file_logger, output_logger) = \
        scroll_log.get_module_loggers(__name__)


def load_config_file():
    """Populates internal config dictionary based on file.

    Open the configuration file and use it to populate config values. This
    variable is imported by other modules during program execution to
    provide user-specified values and/or sensible defaults.

    Raises:
        FatalScrollPyError: Raised if the specified config file cannot be
            opened, or if any duplicate sections and/or options are found
            in the file.

    """
    scroll_log.log_message(
            scroll_log.BraceMessage(
                "Loading config information from {}", config_file),
            2,
            'INFO',
            console_logger, file_logger,
            )
    try:
        with open(config_file, 'r') as cf:
            config.read_file(cf)
    except IOError as ie: # Could not find file
        scroll_log.log_message(
                scroll_log.BraceMessage(
                    "Could not find or open config file"),
                1,
                'ERROR',
                console_logger, file_logger,
                exc_obj=ie,
                )
        raise FatalScrollPyError
    # Check for duplicate sections
    except DuplicateSectionError as dse:
        scroll_log.log_message(
                scroll_log.BraceMessage(
                    "Duplicate config section {} detected", dse.section),
                1,
                'ERROR',
                console_logger, file_logger,
                exc_obj=dse,
                )
        raise FatalScrollPyError
    # Check for duplicate options
    except DuplicateOptionError as doe:
        scroll_log.log_message(
                scroll_log.BraceMessage(
                    "Duplicate config option {} detected", doe.option),
                1,
                'ERROR',
                console_logger, file_logger,
                exc_obj=doe,
                )
        raise FatalScrollPyError
