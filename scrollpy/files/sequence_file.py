"""
Module dealing with sequence files.

This module is intended to provide functions for working with sequence
files, including to read, parse, and combine sequences for use in other
methods/classes within the program.

"""

import os,time
from datetime import datetime

from Bio import SeqIO

from scrollpy.sequences._scrollseq import ScrollSeq
from scrollpy.util._counter import Counter


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


def seqfile_to_scrollseqs(file_handle, file_format="fasta"):
    """Reads sequences from a file and returns relevant objects.

    Like _get_sequences(), but returns ScrollSeq objects instead of
    BioPython SeqRecord objects.

    Args:
        file_handle (str): Full path to sequence file.
        file_format (str): SeqIO-compatible format string.
            Defaults to "fasta".

    Returns:
        (list): List of ScrollSeq objects.

    """
    scroll_seqs = []
    # Get reference to global counter object
    counter = Counter()
    # Make ScrollSeqs
    for record in _get_sequences(file_handle, file_format):
        scroll_seq = ScrollSeq(
                counter(),  # Gets an ID number
                None,  # Group
                record,  # SeqRecord object
                )
        scroll_seqs.append(scroll_seq)
    return scroll_seqs


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

# Might not need this function anymore
def _sequence_list_to_dir(out_dir, seq_list):
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

# New function; assumes outpath is specified and doesn't worry about timestamp
def _sequence_list_to_file(seq_list, outpath, outfmt = "fasta"):
    """Simple function to write ScrollSeq objects to file.

    Uses Bio.SeqIO to write associated ScrollSeq.SeqRecord objects
    to a file in FASTA format.

    Arguments:
        seq_list (list): List of ScrollSeq objects
        outpath (str): Full outfile path

    Returns:
        None
    """
    with open(outpath, 'w') as o: # Assume outpath is already checked
        for seq_object in seq_list:
            seq_object._write(o, outfmt)
            #SeqIO.write(seq_object._record, o, "fasta")

def _sequence_list_to_file_by_id(seq_list, outpath):
    """Writes ScrollSeq objects to file using ID instead of description.

    No longer uses Bio.SeqIO but rather a simple FASTA-based formatter.

    Arguments:
        seq_list (list): List of ScrollSeq objects
        outpath (str): Full outfile path

    Returns:
        None
    """
    with open(outpath, 'w') as o:
        for seq_object in seq_list:
            seq_object._write_by_id(o)

