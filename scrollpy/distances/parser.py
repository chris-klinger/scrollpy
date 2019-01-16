"""
This module contains functions to parse distance files
and return their values in a data type.
"""

from scrollpy.util._util import non_blank_lines


def parse_distance_file(file_path, file_type):
    """Opens and parses a distance file depending on type.

    Most distance files will simply be some variant of:
        <name1> <sep> <name2> <sep> <distance>

    Args:
        file_path (str): Path to file with distances to parse.
        file_type (str): Name of the program that generated
            the distances. For details, see DistanceCalc class.

    Returns:
        List of tuples: ('name1', 'name2', 'distance')
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
        List of tuples: ('name1', 'name2', 'distance')
    """
    distances = []
    for line in non_blank_lines(file_path): # Generator
        n1,n2,d = line.strip('\n').split()
        distances.append((n1,n2,d)) # Nested
    return distances

def _parse_phyml_distances(file_path):
    pass

