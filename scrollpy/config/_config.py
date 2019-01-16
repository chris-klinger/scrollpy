"""
Loads the configuration file into a config variable.
"""

import os,sys

from configparser import ConfigParser
from configparser import DuplicateSectionError
from configparser import DuplicateOptionError

file_dir = os.path.dirname(os.path.realpath(__file__))
config_file = os.path.join(file_dir, '../../scrollpy.conf')
#config_file = "/Users/cklinger/git/scrollpy/scrollpy.conf"


config = ConfigParser(
        allow_no_value = True, # Unused methods can be anything
        strict = True, # Default but emphasized -> NO DUPLICATES
        empty_lines_in_values = False, # Preferably one value per line
        )

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

