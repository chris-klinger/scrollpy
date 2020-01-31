
############################
# Populate Package Namespace
############################

# Logging functionality
from scrollpy.util import _logging as scroll_log  # LOAD FIRST!!!
from scrollpy.util._logging import BraceMessage
# Configuration and argument handling
from scrollpy.config._config import config
from scrollpy.config._config import load_config_file
# Custom exceptions
from scrollpy.util._exceptions import FatalScrollPyError
from scrollpy.util._exceptions import DuplicateSeqError
from scrollpy.util._exceptions import ValidationError
# Classes to run external programs
from scrollpy.applications.runner import Aligner
from scrollpy.applications.runner import AlignEvaluator
from scrollpy.applications.runner import DistanceCalc
from scrollpy.applications.runner import TreeBuilder
# Internal data structure classes
from scrollpy.sequences._scrollseq import ScrollSeq
from scrollpy.sequences._leafseq import LeafSeq
from scrollpy.sequences._collection import ScrollCollection
# Main Runtime classes
from scrollpy.util._mapping import Mapping
from scrollpy.filter._new_filter import Filter
from scrollpy.scrollsaw._scrollpy import ScrollPy
from scrollpy.scrollsaw._scrolltree import ScrollTree
from scrollpy.scrollsaw._aligniter import AlignIter
from scrollpy.scrollsaw._treeplacer import TreePlacer
# Output classes
from scrollpy.files.output import AlignWriter
from scrollpy.files.output import SeqWriter
from scrollpy.files.output import TableWriter
# Utility functions
from scrollpy.util import _util as util


# A list of TemporaryDirectory objects for cleanup
tmps_to_remove = []


##################
# PACKAGE METADATA
##################

__project__ = "ScrollPy"
__version__ = "0.1.0"
__author__ = "Christen M. Klinger"
__license__ = "GNU General Public License"
__citation__ = "NA"

