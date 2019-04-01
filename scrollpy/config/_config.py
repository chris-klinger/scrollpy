"""
Loads the configuration file into a config variable.
"""

import os,sys

from configparser import ConfigParser
from configparser import DuplicateSectionError
from configparser import DuplicateOptionError

#from scrollpy.util import logging as scroll_log
from scrollpy import scroll_log

file_dir = os.path.dirname(os.path.realpath(__file__))
config_file = os.path.realpath(os.path.join(file_dir, '../../_scrollpy.conf'))
#config_file = "/Users/cklinger/git/scrollpy/scrollpy.conf"


config = ConfigParser(
        allow_no_value = True, # Unused methods can be anything
        strict = True, # Default but emphasized -> NO DUPLICATES
        empty_lines_in_values = False, # Preferably one value per line
        )


# Set up loggers
#print("Name of config module is: {}".format(__name__))
console_logger = scroll_log.get_console_logger(__name__)
file_logger = scroll_log.get_file_logger(__name__)


def load_config_file():
#    """Populates config values"""
#    scroll_log.log_message(
#            scroll_log.BraceMessage("Loading configs from {}",config_file),
#            2,
#            'INFO',
#            console_logger, file_logger)
    try:
        with open(config_file, 'r') as cf:
            config.read_file(cf)
    except IOError as ie: # Could not find file
        print(ie)
        sys.exit(0)
    except DuplicateSectionError as dse:
        print(dse)
        print("Please remove duplicate {} section and re-run".format(
            dse.section))
        sys.exit(0)
    except DuplicateOptionError as doe:
        print(doe)
        print("Please remove duplicate {} option and re-run".format(
            doe.option))
        sys.exit(0)

