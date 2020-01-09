"""
This module contains functions to parse alignment files and
return a dictionary of header:sequence pairs
"""

from Bio import AlignIO


from scrollpy import scroll_log
from scrollpy.util._util import non_blank_lines


# Get module loggers
(console_logger, status_logger, file_logger, output_logger) = \
        scroll_log.get_module_loggers(__name__)


def parse_alignment_file(file_path, file_type, to_dict=True):
    """Opens and parses an alignment file depending on file type.

    Mostly a thin wrapper over Bio.AlignIO, but can fall back if parsing
    raises an exception and try manual parsing.

    Args:
        file_path (str): Path to alignment file to parse
        file_type (str): Name of alignment format; see Bio.AlignIO for
            details on support formats

    Returns:
        A dict of <header> : <sequence> pairs
    """
    try:
        alignment =  AlignIO.read(file_path,file_type)
    except ValueError:  # Not parsable
        scroll_log.log_message(
                scroll_log.BraceMessage(
                    "Could not read alignment from {}\n", file_path),
                1,
                'ERROR',
                console_logger, file_logger,
                exc_info=True,
                )
    # Eventually should get down to here
    if to_dict:
        return _bio_align_to_dict(alignment)
    return alignment


def _bio_align_to_dict(align_obj, align_dict=None):
    """Uses the sequence ID and sequence attribute to build a dict
    """
    return {record.id:str(record.seq) for record in align_obj}


def write_alignment_file(align_obj, file_path, file_type):
    """Uses Align.IO internally"""
    AlignIO.write(
            align_obj,
            file_path,
            file_type,  # E.g. 'fasta'
            )
