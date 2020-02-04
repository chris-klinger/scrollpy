"""
Module dealing with converting between alignment files.

This module is intended to provide functions for onverting between
different types of aligned files.

"""

import sys

from scrollpy import scroll_log
from scrollpy import BraceMessage
from scrollpy import FatalScrollPyError
from scrollpy.util._util import non_blank_lines


# Get module loggers
(console_logger, status_logger, file_logger, output_logger) = \
        scroll_log.get_module_loggers(__name__)

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
    for line in non_blank_lines(alignment_file):
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
            # sys.exit("Sequence for {} has length {}, expected length {}".format(
            #     k,seq_length,target_length))
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

