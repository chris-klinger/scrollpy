"""
Module dealing with sequence files.

This module is intended to provide functions for working with sequence
files, including to read, parse, and combine sequences for use in other
methods/classes within the program.

"""

import os,time
from datetime import datetime

from Bio import SeqIO


def _get_sequences(file_handle, file_format="fasta"):
    """Reads sequences from a file and returns relevant objects.

    This function takes a file handle with a given format for biological
    sequence data and returns a list of SeqRecord object for each, as
    outlined in the BioPython documentation. For a full list of
    supported formats, see:

        https://biopython.org/wiki/SeqIO

    Arguments:
        file_handle (str): Full path to the file to parse
        file_format (str): SeqIO-compatible format string.
            Defaults to "fasta"

    Returns:
        list: List of SeqRecord objects
    """
    with open(file_handle,'r') as i:
        records = [record for record in SeqIO.parse(i, file_format)]
    return records


def _cat_sequence_lists(*seq_lists):
    """Simple function to combine SeqRecord lists.

    This function takes one or more lists of SeqRecord objects and returns
    a single list containing all objects.

    Arguments:
        *seq_lists: A collection of iterables with SeqRecord objects

    Returns:
        A list of SeqRecord objects.
    """
    combined = []
    for seq_list in seq_lists:
        combined.extend(seq_list)
    return combined

def _sequence_list_to_file(out_dir, seq_list):
    """Simple function to write SeqRecord objects to file.

    Uses Bio.SeqIO to write a list of SeqRecord objects to a file in
    FASTA format for further use.

    Arguments:
        out_dir (str): Full path to the directory in which to place file
        seq_list (list): List of SeqRecord objects

    Returns:
        Full path to the output file
    """
    out_handle = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    out_path = os.path.join(out_dir, out_handle)
    with open(out_path, 'w') as o:
        SeqIO.write(seq_list, o, "fasta")
    return out_path

