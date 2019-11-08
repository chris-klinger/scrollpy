"""
This module contains functions and classes for working with tree
objects in scrollpy.

Loading trees is supported through the ETE3 package
"""

import sys

from ete3 import Tree
from ete3.parser.newick import NewickError


def read_tree(inpath, tree_format):
    """Parses a plain text file containing a tree representation.

    Args:
        inpath (str): full path to input tree file
        tree_format (str): tree format, for example "newick"

    Returns:
        ETE3 tree object representing file's contents
    """
    if tree_format == 'newick':
        try:
            return _read_newick_tree(inpath)
        except NewickError:
            # Log something!!!
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
        pass  # Log eventually
    # Load a less strict format after
    try:
        tree = Tree(inpath, format=3)  # Strict branch+leaves
    except(NewickError):
        pass  # Log eventually
    # Finally give up and try most flexible
    try:
        tree = Tree(inpath, format=0)  # Flexible with support values
    except(NewickError):
        # Log something and freak out!!!
        raise NewickError  # Re-raise to signal could not load
    # If this point is reached, a tree is loaded
    return Tree
