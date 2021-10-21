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
A new module for dealing with both alignment file parsing and converting
between different alignment types.

"""

from Bio import AlignIO


from scrollpy import scroll_log
from scrollpy import BraceMessage
from scrollpy import scrollutil
from scrollpy import FatalScrollPyError


# Get module loggers
(console_logger, status_logger, file_logger, output_logger) = \
        scroll_log.get_module_loggers(__name__)


#####################
# PARSING FUNCTIONS #
#####################

def parse_alignment_file(file_path, file_type, to_dict=True):
    """Opens and parses an alignment file depending on file type.

    Mostly a thin wrapper over Bio.AlignIO, but can fall back if parsing
    raises an exception and try manual parsing.

    Args:
        file_path (str): Path to alignment file to parse.
        file_type (str): Name of alignment format; see Bio.AlignIO for
            details on supported formats.
        to_dict (bool): Whether to return a dictionary representing the
            alignment instead of an object. Defaults to True.

    Returns:
        dict: A dictionary of <header>:<sequence> pairs if to_dict is
            True.
        obj: A BioPython alignment object is to_dict is False.

    """
    try:
        alignment =  AlignIO.read(file_path,file_type)
    except ValueError as e:  # Not parsable
        scroll_log.log_message(
                BraceMessage(
                    "Could not read alignment from {} ", file_path),
                1,
                'ERROR',
                console_logger, file_logger,
                exc_obj=e,
                )
        raise FatalScrollPyError
    # Eventually should get down to here
    if to_dict:
        return _bio_align_to_dict(alignment)
    return alignment


def _bio_align_to_dict(align_obj): #align_dict=None):
    """Uses the sequence ID and sequence attribute to build a dict.

    Args:
        align_obj (obj): BioPython alignment object.

    Returns:
        dict: A dictionary of <header>:<sequence> pairs.

    """
    return {record.id:str(record.seq) for record in align_obj}


def write_alignment_file(align_obj, file_path, file_type):
    """Writes an alignment object to a target file.

    Uses Align.IO functionality internally.

    Args:
        align_obj (obj): BioPython alignment object.
        file_path (str): Full path to the target file.
        file_type (str): Name of the alignment file to write. See the
            Bio.AlignIO documentation for supported formats.

    """
    AlignIO.write(
            align_obj,
            file_path,
            file_type,  # E.g. 'fasta'
            )


def write_align_obj_by_int(align_obj, file_path):
    """Writes a FASTA-formatted representation with integer headers.

    Zorro has an issue handling some input sequence names throughout its
    run, but all that is required in the end is the column scores. To
    mitigate this issue, write a temporary file where all the header names
    are replaced with an increasing count of ints.

    Args:
        align_obj (obj): Biopython alignment object.
        file_path (str): Full path to the target file.

    """
    with open(file_path,'w') as o:
        for i,record in enumerate(align_obj):
            o.write(">" + str(i+1) + "\n")
            for chunk in scrollutil.split_input(str(record.seq)):
                o.write(chunk + "\n")


########################
# CONVERSION FUNCTIONS #
########################


# These functions could probably be replaced by BioPython?
def afa_to_phylip(alignment_file, target_file):
    """Convert a standard FASTA alignment to phylip.

    Maintains sequences length at 40 characters, and checks to ensure the
    resulting sequence headers and lengths are the same in the resulting
    file as in the input alignment file.

    Args:
        alignment_file (str): Full path to alignment file.
        target_file (str): Full path to desired output file.

    Raises:
        FatalScrollPyError: Raised if either duplicate sequence headers
            exist in the input file, or if the sequence lengths differ
            between input and output files.

    """
    num_seqs = 0
    headers = []
    seq_dict = {}
    for line in scrollutil.non_blank_lines(alignment_file):
        if line.startswith('>'):
            header = line.strip('>').strip('\n')
            if header in headers:
                scroll_log.log_message(
                        BraceMessage(
                            "Found duplicate sequence header {}"
                            "in alignment".format(line)),
                        1,
                        'ERROR',
                        console_logger, file_logger,
                        )
                raise FatalScrollPyError
                # sys.exit("Found duplicate sequence header {} in alignment".format(line))
            headers.append(header)
            seq_dict[header] = ''
            num_seqs += 1
        else:
            line = line.strip('\n')
            seq_dict[header] += line  # Add to sequence
    # Check whether any of the lengths are not the same
    target_length = None
    for k,v in seq_dict.items():
        seq_length = len(v)
        target_length = seq_length if not target_length else target_length
        if seq_length != target_length:
            scroll_log.log_message(
                    BraceMessage("Sequence for {} has length {},"
                        "expected length {}".format(
                            k,             # The sequence header/ID
                            seq_length,    # Actual length
                            target_length, # Expected length
                            ),
                        1,
                        'ERROR',
                        console_logger, file_logger,
                        ))
            raise FatalScrollPyError
    # Finally write file
    with open(target_file,'w') as o:
        o.write("{} {}\n".format(num_seqs,target_length))
        for header in headers:
            seq = seq_dict[header]
            # IQ-TREE splits on spaces?
            header = header.split()[0]  # Is this bad?
            # Cut it short if it is longer than 40 chars
            if len(header) > 40:
                header = header[:40]
            num_spaces = 41 - len(header)
            o.write(header + (' ' * num_spaces) + seq + '\n')


# These functions could probably be replaced by BioPython?
def phylip_to_afa(phylip_file, target_file):
    """Convert a standard Phylip file to an aligned FASTA file.

    Args:
        phylip_file (str): Full path to phylip file.
        target_file (str): Full path to target FASTA file.

    """
    with open(phylip_file,'r') as i, open(target_file,'w') as o:
        line_counter = 1
        for line in i:
            if line_counter > 1:  # Skip first line
                header,seq = line.rsplit(maxsplit=1)
                o.write('>' + header + '\n')
                o.write(seq + '\n')
            line_counter += 1

