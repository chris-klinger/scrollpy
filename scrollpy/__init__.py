
############################
# Populate Package Namespace
############################

from scrollpy.util import _logging as scroll_log  # LOAD FIRST!!!
from scrollpy.config._config import config
from scrollpy.config._config import load_config_file
from scrollpy.util import _util as util
from scrollpy.scrollsaw._scrollpy import ScrollPy
from scrollpy.files.output import SeqWriter
from scrollpy.files.output import TableWriter

####################
# PACKAGE METADATA

__project__ = "ScrollPy"
__version__ = "0.1.0"
__author__ = "Christen M. Klinger"
__license__ = "GNU General Public License"
__citation__ = "NA"

