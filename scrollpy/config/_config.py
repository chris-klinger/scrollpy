"""
Loads the configuration file into a config variable.
"""

import os,sys

from configparser import ConfigParser
from configparser import DuplicateSectionError
from configparser import DuplicateOptionError

from scrollpy import scroll_log


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
    """Populates config values"""
    scroll_log.log_message(
            scroll_log.BraceMessage("Loading config information from {}",config_file),
            2,
            'INFO',
            console_logger, file_logger,
            )
    # Keep track of multiple possible duplicates
    duplicate_sections = []
    duplicate_options  = []
    try:
        with open(config_file, 'r') as cf:
            config.read_file(cf)
    except IOError as ie: # Could not find file
        scroll_log.log_message(
                scroll_log.BraceMessage(
                    "Could not find or open config file; exiting"),
                1,
                'ERROR',
                console_logger, file_logger,
                exc_info=True,
                )
        sys.exit(0)
    # Check for duplicates
    except DuplicateSectionError as dse:
        dupliate_sections.append(dse.section)
        scroll_log.log_message(
                scroll_log.BraceMessage(
                    "Dupliate config section {} detected\n", dse.section),
                1,
                'ERROR',
                console_logger, file_logger,
                )
    except DuplicateOptionError as doe:
        dupliate_options.append(doe.option)
        scroll_log.log_message(
                scroll_log.BraceMessage(
                    "Dupliate config option {} detected\n", doe.option),
                1,
                'ERROR',
                console_logger, file_logger,
                )
    # If any duplicates exist, report and exit
    num_dup_sections = len(duplicate_sections)
    num_dup_options  = len(duplicate_options)
    # If both exist
    if duplicate_sections and duplicate_options:  # Empty lists are False
        scroll_log.log_message(
                scroll_log.BraceMessage(
                    "Identified {} duplicate config section(s) and {} dupliate options; exiting\n",
                    num_dup_sections, num_dup_options,
                    ),
                1,
                'ERROR',
                console_logger, file_logger,
                )
        sys.exit(0)
    # Duplicate setions only
    elif duplicate_sections:
        scroll_log.log_message(
                scroll_log.BraceMessag(
                    "Identified {} duplicate config sections; exiting\n",
                    num_dup_sections,
                    ),
                1,
                'ERROR',
                console_logger, file_logger,
                )
        sys.exit(0)
    # Duplicate options only
    elif duplicate_options:
        scroll_log.log_message(
                scroll_log.BraceMessage(
                    "Identified {} duplicate config options; exiting\n",
                    num_dup_options,
                    ),
                1,
                'ERROR',
                console_logger, file_logger,
                )
        sys.exit(0)


