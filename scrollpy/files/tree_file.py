"""
This module contains functions and classes for working with tree
objects in scrollpy.

Loading trees is supported through the ETE3 package
"""

import sys
import warnings

from ete3 import Tree
from ete3.parser.newick import NewickError

from scrollpy import scroll_log


# Get module loggers
(console_logger, status_logger, file_logger, output_logger) = \
        scroll_log.get_module_loggers(__name__)


def read_tree(inpath, tree_format):
    """Parses a plain text file containing a tree representation.

    Args:
        inpath (str): full path to input tree file
        tree_format (str): tree format, for example "newick"

    Returns:
        ETE3 tree object representing file's contents
    """
    if tree_format == 'newick':
        # ETE3 still opens in 'U' mode; suppress warning about deprecation
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                scroll_log.log_message(
                        scroll_log.BraceMessage(
                            "Trying to read Newick file {}", inpath),
                        2,
                        'INFO',
                        file_logger,
                        )
                return _read_newick_tree(inpath)
            except NewickError:
                scroll_log.log_message(
                        scroll_log.BraceMessage(
                            "Could not read Newick file {}; exiting", inpath),
                        1,
                        'ERROR',
                        console_logger, file_logger,
                        )
                sys.exit(0)  # Exit cleanly
    else:
        pass  # Add support for other file formats later?


def _read_newick_tree(inpath):
    """Called by read_tree with tree_format="newick"

    Args:
        inpath (str): full path to input tree file

    Returns:
        ETE3 tree object representing file's contents

    Raises:
        NewickError: unable to read the newick file's contents
    """
    # Try to load with strict format first
    try:
        tree = Tree(inpath, format=2)  # Strict branch+leaves+support
    except(NewickError):
        scroll_log.log_message(
                scroll_log.BraceMessage(
                    "Could not load tree with branches, leaves, and support\n"),
                1,
                'WARNING',
                file_logger,  # Don't bother writing to console
                )
    # Load a less strict format after
    try:
        tree = Tree(inpath, format=3)  # Strict branch+leaves
    except(NewickError):
        scroll_log.log_message(
                scroll_log.BraceMessage(
                    "Could not load tree with branches and leaves\n"),
                1,
                'WARNING',
                file_logger,
                )
    # Finally give up and try most flexible
    try:
        tree = Tree(inpath, format=0)  # Flexible with support values
    except(NewickError):
        scroll_log.log_message(
                scroll_log.BraceMessage(
                    "Could not load tree in flexible format\n"),
                1,
                'WARNING',
                file_logger,
                )
        raise NewickError  # Re-raise to signal could not load
    # If this point is reached, a tree is loaded
    return tree
