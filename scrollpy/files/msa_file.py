"""
Module dealing with converting between alignment files.

This module is intended to provide functions for onverting between
different types of aligned files.

"""


def afa_to_phylip(alignment_file, target_file):
    """Convert a standard FASTA alignment to phylip"""
    num_seqs = 0
    headers = []
    seq_dict = {}
    for line in nonblank_lines(alignment_file):
        if line.startswith('>'):
            header = line.strip('>').strip('\n')
            if header in headers:
                sys.exit("Found duplicate sequence header {} in alignment".format(line))
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
            sys.exit("Sequence for {} has length {}, expected length {}".format(
                k,seq_length,target_length))
    # Finally write file
    with open(target_file,'w') as o:
        o.write("{} {}\n".format(num_seqs,target_length))
        for header in headers:
            seq = seq_dict[header]
            # Cut it short if it is longer than 40 chars
            if len(header) > 40:
                header = header[:40]
            num_spaces = 41 - len(header)
            o.write(header + (' ' * num_spaces) + seq + '\n')


def phylip_to_afa(phylip_file, target_file):
    """Convert a standard Phylip file to an aligned FASTA file"""
    with open(phylip_file,'r') as i, open(target_file,'w') as o:
        line_counter = 1
        for line in i:
            if line_counter > 1:  # Skip first line
                header,seq = line.rsplit(maxsplit=1)
                o.write('>' + header + '\n')
                o.write(seq + '\n')
            line_counter += 1

