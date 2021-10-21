#!/usr/bin/env python3

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
This module contains functions to parse distance files
and return their values in a data type.

"""

from scrollpy import scroll_log
from scrollpy import BraceMessage
from scrollpy import scrollutil
from scrollpy import FatalScrollPyError


# Get module loggers
(console_logger, status_logger, file_logger, output_logger) = \
        scroll_log.get_module_loggers(__name__)


def parse_distance_file(file_path, file_type):
    """Opens and parses a distance file depending on type.

    Most distance files will simply be some variant of:
        <name1> <sep> <name2> <sep> <distance>

    Args:
        file_path (str): Path to file with distances to parse.
        file_type (str): Name of the program that generated the
            distances. For details, see DistanceCalc class.

    Returns:
        dict: A dictionary of <name>:<distance> pairs.

    """
    if file_type == 'RAxML':
        return _parse_raxml_distances(file_path)
    elif file_type == 'PhyML':
        return _parse_phyml_distances(file_path)
    else:
        pass # TO-DO


def _parse_raxml_distances(file_path):
    """Parses a RAxML distance file.

    RAxML distance file structure is:
        <name1> <name2>\t<distance>

    Args:
        file_path (str): Path to file with distances to parse.

    Returns:
        dict: A dictionary of <name>:<distance> pairs.

    """
    distances = {}
    for line in scrollutil.non_blank_lines(file_path): # Generator
        n1,n2,d = line.strip('\n').split()
        for key in n1,n2:
            try:
                distances[key] += float(d)
            except KeyError:
                distances[key] = float(d)
    if len(distances.keys()) == 0:  # No distances
        scroll_log.log_message(
                BraceMessage(
                    "Could not read distances from {}", file_path),
                1,
                'ERROR',
                console_logger, file_logger,
                )
        raise FatalScrollPyError
    return distances

def _parse_phyml_distances(file_path):
    pass

