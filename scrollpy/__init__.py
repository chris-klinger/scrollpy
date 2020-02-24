
import os
import sys
import math
from textwrap import TextWrapper

############################
# Populate Package Namespace
############################

# A list of TemporaryDirectory objects for cleanup
tmps_to_remove = []

# Utility functions
from scrollpy.util import _util as scrollutil
# Logging functionality
from scrollpy.util import _logging as scroll_log  # LOAD FIRST!!!
from scrollpy.util._logging import BraceMessage
# Custom exceptions
from scrollpy.util._exceptions import FatalScrollPyError
from scrollpy.util._exceptions import DuplicateSeqError
from scrollpy.util._exceptions import ValidationError
# Configuration and argument handling
from scrollpy.config._config import config
from scrollpy.config._config import load_config_file
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


##################
# PACKAGE METADATA
##################

_repo_url = "https://github.com/chris-klinger/scrollpy"

__project__ = "ScrollPy"
__version__ = "0.1.0"
__author__ = "Christen M. Klinger"
__email__ = "cklinger@ualberta.ca"
__license__ = "GNU General Public License"
__citation__ = "Klinger, C.M. (2020). {}: Utility Functions for Phylogenetic Analysis. "\
        "Available from: {}".format(__project__, _repo_url)


##########################################
# DATA FOR OTHER PACKAGES USED BY SCROLLPY
##########################################

_ete3_citation = \
        "Jaime Huerta-Cepas, Francois Serra and Peer Bork (2016)."\
        "ETE 3: Reconstruction, analysis and visualization of phylogenomic data. "\
        "Mol Biol Evol; doi: 10.1093/molbev/msw046."

_biopython_citation = \
        "Cock PA, Antao T, Chang JT, Chapman BA, Cox CJ, Dalke A, Friedberg I, "\
        "Hamelryck T, Kauff F, Wilczynski B and de Hoon MJL (2009). Biopython: "\
        "freely available Python tools for computational molecular biology "\
        "and bioinformatics. Bioinformatics, 25, 1422-1423."


####################################
# FUNCTIONS FOR WRITING PROJECT INFO
####################################

def get_text_wrapper(width=82, min_gap=1):
    """Obtains a TextWrapper object for wrapping output text.

    """
    width_reduction = min_gap*2 + 2  # Two to leave space for start/end chars
    return TextWrapper(
            width = (width - width_reduction),
            replace_whitespace=False,
            )


def get_textbox_lines(lines, wrapper=None, width=82, min_gap=1, top_left='+',
        top_right='+', bot_left='+', bot_right='+', middle='-', start='|', end='|'):
    """Obtain wrapped lines for displaying information in a border.

    For simplicity, the function assumes that all border and fill characters are
    a single character of the same length. This could be improved, but internal
    use allows this constraint to be met easily.

    Args:
        lines (list): Input lines to wrap and return
        wrapper (obj): TextWrapper object to use for wrapping the lines.
            Defaults to None.
        width (int) : Total width for each line. Defaults to 82.
        min_gap (int) : Minimum gap on either side of wrapped text.
            Defaults to 1.
        top_left (str): Character for the top left corner of the box.
        top_right (str): Character for the top right corner of the box.
        bot_left (str): Character for the bottom left corner of the box.
        bot_right (str): Character for the bottom right corner of the box.
        middle (str): Character to fill the first and last lines of the box.
        start (str): Character to use at the start of each middle line.
        end (str): Character to use at the end of each middle line.

    Returns:
        list: A list of all formatted lines for output.

    """
    output_lines = []  # Lines to return
    if not wrapper:
        wrapper = get_text_wrapper(width, min_gap)
    if width < 40:
        width = 40  # Minimum width for reasonable viewing
    mod_width = width - 2  # Account for start/end chars
    # First line is easy
    output_lines.append(top_left + (middle*mod_width) + top_right)
    # Subsequent lines require wrapping
    for line in lines:
        if line == '\n':  # Specified a blank line
            output_lines.append(start + ' '*mod_width + end)
        else:  # Line has actual text
            wrapped_lines = wrapper.wrap(line)  # May create more than one line
            for wline in wrapped_lines:
                llen = len(wline)
                diff = mod_width - llen  # Still require start/end chars
                gap = diff / 2  # Float
                if diff % 2 != 0:  # Fractional gap -> split the difference
                    start_gap = math.floor(gap)
                    end_gap = math.ceil(gap)
                else:  # Gap is even -> still need an int value
                    start_gap = int(gap)
                    end_gap = int(gap)
                # Now determine the final line
                output_lines.append(start + ' '*start_gap + wline + ' '*end_gap + end)
    # Last line is easy again
    output_lines.append(bot_left + (middle*mod_width) + top_right)

    return output_lines


def write_citation(width=82, destination=None):
    """Writes a formatted citation.

    Need to inform user to also cite BioPython and ETE3, as well as to
    allow for ease of update for each of these data points.

    """
    if not destination:
        destination = sys.stdout
    to_write = [  # Lines
            "\n",
            "{} is free software. If any part of your analysis depends on {}, "\
                    "please cite:".format( __project__, __project__),
            "\n",
            "{}".format(__citation__),
            "\n",
            "{} makes use of other libraries. Please also cite:".format(__project__),
            "\n",
            "{}".format(_biopython_citation),
            "\n",
            "{}".format(_ete3_citation),
            "\n",
            "{} is provided under a {}".format(__project__, __license__),
            "\n",
            ]
    for wrapped_line in get_textbox_lines(to_write, width=width):
        destination.write(wrapped_line + "\n")


def write_description(width=82, destination=None):
    """Writes a formatted output description.

    """
    if not destination:
        destination = sys.stdout
    to_write = [  # Lines
            "\n",
            "{}: Utility Functions for Phylogenetic Analysis".format(__project__),
            "\n",
            "Version: {}".format(__version__),
            "\n",
            "Developed by {}".format(__author__),
            "Email: {}".format(__email__),
            "\n",
            "For information on available options type 'python -m scrollpy -h'",
            "For example usage please type 'python -m scrollpy --usage'",
            "\n",
            ]
    for wrapped_line in get_textbox_lines(to_write, width=width):
        destination.write(wrapped_line + "\n")


def write_usage(width=82, destination=None):
    """Writes formatted sample usage information.

    """
    if not destination:
        destination = sys.stdout
    to_write = [
            "\n",
            "{} USAGE".format(__project__.upper()),
            "\n",
            "{} compares sequences, both across aligned sequence space and tree "\
                    "space. The simplest mode is sequence-to-sequence comparison, "\
                    "as described in Elias et al (2012). J Cell Sci.".format(__project__),
            "\n",
            "(Use {} to compare sequences across one or more files)".format(__project__),
            "python -m scrollpy -i file1.fa file2.fa",
            "\n",
            "(Compare sequences and retrieve the top 4 sequences per group)",
            "python -m scrollpy -i *.fa --seqout --number 4",
            "\n",
            "By default, {} maps sequences into groups based on the file they originated "\
                    "from. This assignment can also be controlled manually by providing "\
                    "a separate tab-delimited file with <id><\\t><group> information on "\
                    "each line using the '-m' option".format(__project__),
            "\n",
            "(Compare sequences in one file across specified groups)",
            "python -m scrollpy -i file1.fa -m file1_mapping.txt",
            "\n",
            "{} also provides an option to filter sequences prior to running an analysis "\
                    "to remove unwanted sequences prior to an analysis using the '-f' "\
                    "option. The '--filter-method' option specifies length-based ('zscore') "\
                    "or identity-based ('identity') filtering".format(__project__),
            "\n",
            "(Filter sequences by inter-sequence identity prior to comparison)",
            "python -m scrollpy -i *.fa -f --filter-method identity",
            "\n",
            "(Filter sequences only and return remaining and removed sequences)",
            "python -m scrollpy -i *.fa -f --filter-out --filter-only",
            "\n",
            "{} can also compare sequences in a phylogeny and perform a similar all-vs-all "\
                    "comparison by branch lengths rather than pairwise genetic distance.".format(
                        __project__),
            "\n",
            "(Compare all tree leaves based on a supplied mapping)",
            "python -m scrollpy -t tree1.tre -m tree1_mapping.txt",
            "\n",
            "In addition to performing comparison of existing labels, {} can place sequences "\
                    "in an existing alignment and attempt to classify them based on which group "\
                    "they place in (using '--support' threshold bootstrap support).".format(
                        __project__),
            "\n",
            "(Place sequences in a tree by monophyletic nodes of >=80 BS support)",
            "python -m scrollpy -a start.afa -p -c place_seqs.fa --support 85",
            "\n",
            "Lastly, {} can iterate over a provided alignment to identify which high-scoring "\
                    "columns provide the best overall tree bootstrap support. The default, and "\
                    "therefore recommended, method relies on alignment bisection.".format(__project__),
            "\n",
            "(Iterate over alignment columns and return an 'optimal' alignment)",
            "python -m -a start.afa -e",
            "\n",
            "There are many more options to fine-tune {}. Two that may be most useful are the "\
                    "'-v' or '--verbosity' option, which controls the level of detail written "\
                    "to the screen during program runs, and '--silent', which suppreses all "\
                    "screen output.".format(__project__),
            "\n",
            "(Perform sequence comparison with very detailed screen output)",
            "python -m scrollpy -i *.fa -v 3",
            "\n",
            "\n",
            "For a more detailed explanation, as well as a complete list of available commands, "\
                    "please see the {} repository documentation, and/or run:".format(__project__),
            "\n",
            "python -m scrollpy -h/--help",
            "\n",
            ]
    for wrapped_line in get_textbox_lines(to_write, width=width):
        destination.write(wrapped_line + "\n")


def write_version(width=82, destination=None):
    """Simple reporting of version information.

    """
    if not destination:
        destination = sys.stdout
    destination.write("{} v{}\n".format(__project__, __version__))

