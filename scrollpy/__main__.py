#!/usr/bin/env python3

"""
Runs the main scrollpy program.
"""

import os
import sys
import argparse


import scrollpy
#from config._config import config

###########################
# Format header description
###########################

_name = scrollpy.__project__
_version = scrollpy.__version__
_author = scrollpy.__author__
_license = scrollpy.__license__
_citation = scrollpy.__citation__

_formatted_desc = "" # TO-DO

###############################
# Write out project information
###############################

def _write_project_information():
    """Writes out information about the project"""
    pass

########################
# Write out sample usage
########################

def _write_sample_usage():
    """Writes out some sample usage examples"""
    pass

def main():
    ##############
    # BEGIN TIMING
    ##############

    # TO-DO

    ########################
    # Command line arguments
    # ######################

    parser = argparse.ArgumentParser(
            description = _formatted_desc,
            formatter_class = argparse.HelpFormatter, # TO-DO
            #add_help = False, # is this what we want?
        )
    # Options for files
    file_options = parser.add_argument_group("File Options")
    file_options.add_argument("-i", "--infiles",
            nargs = '*',
            metavar = "Infile Paths",
            help = (
                "Path(s) to one or more input files. Can be blank. "
                "If using the '--tree-file' option, the headers in"
                "each file will be concatenated and assumed to represent"
                "all of the branch tips in the tree provided."
                ))
    file_options.add_argument("--infmt",
            nargs = '?',
            metavar = "Infile Type",
            default = "fasta",
            choices = ["fasta", "fasta-2line", "genbank"], # Work on this
            help = (
                "Format of ALL specified infiles (all must be the same), "
                "default to 'fasta'."
                ))
    file_options.add_argument("-q", "--seqtype",
            nargs = '?',
            metavar = "Sequence Type",
            default = "prot",
            choices = ["nucl", "prot"],
            help = (
                "Alphabet of ALL specified infiles."
                ))
    file_options.add_argument("-t", "--treefile",
            nargs = '?',
            metavar = "Treefile Path",
            help = (
                "Path to a file containing a tree object (optional). "
                "If provided, analysis defaults to reading branch lengths"
                "to calculate patristic distances."
                ))
    file_options.add_argument("--treefmt",
            nargs = '?',
            metavar = "Tree Format",
            default = "newick",
            choices = ["nexus", "newick", "phylip", "nexml"],
            help = (
                "Format of tree file, if supplied. Defaults to 'newick'."
                ))
    file_options.add_argument("-o", "--out",
            nargs = '?',
            metavar = "Target Output Directory",
            default = None,
            help = (
                "Target directory for output files. If the target directory "
                "does not exist, it is created unless the '--nocreate' flag "
                "is set. If target directory is not specified, or directory "
                "creation fails, defaults to the current directory."
                ))
    file_options.add_argument("--suffix",
            nargs = '?',
            metavar = "Output File Suffix",
            default = None,
            help = (
                "Optional argument to specify a common suffix to be added to "
                "all output files. This will be added to the default names "
                "in the form <name><sep><suffix><extension>, and the <sep> "
                "argument specified by '--filesep'."
                ))
    file_options.add_argument("--seqout",
            action = "store_true",
            help = (
                "Write output files containing optimal sequences. One file "
                "is written for each group, with up to '--numseqs' sequences "
                "in each group."
                ))
    file_options.add_argument("--seqfmt",
            nargs = '?',
            metavar = "Output Sequence Format",
            choices = ["fasta", "fasta-2line", "genbank"], # Work on this
            default = "fasta",
            help = (
                "Format to write sequences to. If not specified, or if an "
                "error is encountered during writing, defaults to 'fasta'."
                ))
    file_options.add_argument("--tblfmt",
            nargs = '?',
            metavar = "Output Table Format",
            choices = ["csv", "space-delim", "tab-delim", "sep"],
            default = "csv",
            help = (
                "Format to write summary information to. If 'sep' is specfified "
                "writes using character '--tblsep' as delimiter. If no sep is "
                "specified, or this option is not set, defaults to csv (',')."
                ))
    file_options.add_argument("-m", "--mapping",
            nargs = '?',
            metavar = "Optional Group Mapping",
            help = (
                "Path to a file containing a mapping of sequence headers/ tip "
                "labels to a pre-specified group. Format <id><tab><group>. If "
                "not all headers/labels are present in the file, the remaining "
                "items are gathered into their own group. Note: header/labels "
                "present must match those of the tree/sequence file(s) EXACTLY."
                ))
    file_options.add_argument("--filesep",
            nargs = '?',
            metavar = "Filepath Separator",
            help = (
                "Allows to set the delimiter in output filepaths."
                ))
    file_options.add_argument("--tblsep",
            nargs = '?',
            metavar = "Table Column Separator",
            help = (
                "Allows to set the delimiter for output table columns."
                ))
    file_options.add_argument("-x", "--no-create",
            action = "store_true",
            help = (
                "Prevents creation of output directory(ies). If an output "
                "directory is specified that does not exist and this option "
                "is set, ScrollPy will quit with an error message."
                ))
    file_options.add_argument("-y", "--no-clobber",
            action = "store_true",
            help = (
                "Prevents overwrite of target files with the same path. If "
                "this flag is set and a log file is encountered, the log "
                "file will instead write to a new file with an additional "
                "suffix. If any other kind of file is encountered, ScrollPy "
                "assumes it is correct and tries to use it as normal."
                ))
    # Options for Running
    run_options = parser.add_argument_group("Run Options")
    run_options.add_argument("-a", "--align",
            nargs = '?',
            choices = ["Muscle", "Mafft", "Generic"], # TO-DO
            default = "Mafft",
            metavar = "Alignment Method",
            help = (
                "Method to use for aligning sequences. Any other option than "
                "'Generic' requires that the corresponding option in the config "
                "file is set properly."
                ))
    run_options.add_argument("--align-matrix",
            nargs = '?',
            choices = ["Blosum62", "Pam250"], # TO-DO
            metavar = "Alignment Matrix",
            help = (
                "Specify a matrix to use for alignment, e.g. 'Blosum62'. If "
                "the called program does not accept the matrix, the default "
                "will be used instead. Default is to use the default specified "
                "by each program, or 'Blosum62' when using 'Generic'."
                ))
    run_options.add_argument("-d", "--distance",
            nargs = '?',
            choices = ["PhyML", "RAxML", "Generic"], # TO-DO
            metavar = "Distance Method",
            help = (
                "Method to use for calculating distances. Any other options than "
                "'Generic' requires that the corresponding option in the config "
                "file is set properly."
                ))
    run_options.add_argument("--dist-matrix",
            nargs = '?',
            choices = ["WAG", "LG", "JC"], # TO-DO
            metavar = "Distance Matrix",
            help = (
                "Specify a substitution matrix for distance calculations. If "
                "the called program does not accept the matrix, the default "
                "will be used instead. Default is to use the default specified "
                "by each program, or 'LG'/'GTR' when using 'Generic'."
                ))
    run_options.add_argument("-f", "--filter",
            action = "store_true",
            help = (
                "Specify pre-filtering of sequences prior to running ScrollPy. "
                "Filtering is performed according to '--filter-method' and "
                "filtered sequences can be output into a separate file for "
                "user inspection using the '--filter-out' option. If both the "
                "'--treefile' and '--infiles' options are set AND all labels "
                "present in '--treefile' are present in '--infiles', ScrollPy "
                "will also perform filtering of tree tip labels."
                ))
    run_options.add_argument("--filter-method",  # TO-DO
            nargs = '?',
            choices = ["one", "two"],
            default = "one",
            metavar = "Filtering Method",
            help = (
                "HELP TEXT FOR FILTERING METHOD"
                ))
    run_options.add_argument("--filter-out",
            action = "store_true",
            help = (
                "Outputs filtered sequences in the same format as specified for "
                "'--seqout'. Filtered sequences will be organized by group."
                ))
    run_options.add_argument("-s", "--split-seqs",
            action = "store_true",
            help = (
                "If a single file is used as input, and '--mapping' is not "
                "specified, attempt to split input sequence file into an "
                "optimal number of sub-groups based on pariwise similarity "
                "and given that each group must have at least two sequences."
                ))
    run_options.add_argument("--split-method",  # TO-DO
            nargs = '?',
            choices = ["one", "two"],
            default = "one",
            metavar = "Splitting Method",
            help = (
                "HELP TEXT FOR SPLITTING METHOD"
                ))
    run_options.add_argument("-n", "--number",
            nargs = '?',
            type = int,
            default = 3,
            metavar = "Number of Sequences",
            help = (
                "If '--seqout' is specified, at most '--number' of sequences "
                "from each group will be written to outfiles. If the value "
                "specified is less than or equal to zero, the default is used "
                "instead (Default is 3)."
                ))
    run_options.add_argument("--use-config",
            action = "store_true",
            help = (
                "This option allows the user finer control over external "
                "program runs by specifying the values of additional parameters "
                "to use in the config file. Values must be specified as they "
                "would appear on the command line under their own header "
                "within the config file. See docs for more information."
                ))
    # Options for Logging
    log_options = parser.add_argument_group("Log Options")
    log_options.add_argument("-l", "--logfile",
            nargs = '?',
            metavar = "Logfile Name",
            help = (
                "This option allows the user to specify a name for the logged "
                "output. If a full path is specified, ScrollPy attempts to "
                "place the file as specified; if ScrollPy cannot, or if only "
                "a name is specified, '--out' is used instead."
                ))
    log_options.add_argument("--no-log",
            action = "store_true",
            help = (
                "This option turns off logging."
                ))
    log_options.add_argument("--log-level",
            nargs = '?',
            type = int,
            choices = [1, 2, 3],
            default = 3,
            help = (
                "This option contols how much detail is contained in the logfile. "
                "Setting this option to '1' logs only the bare minimum, '2' logs "
                "more information, whereas '3' also logs output from external "
                "program calls (default)."
                ))
    log_options.add_argument("--no-sum",
            action = "store_true",
            help = (
                "This option turns off the automatic summary file generated on "
                "each run. Not recommended."
                ))
    # Options for displaying information
    info_options = parser.add_argument_group("User Information Options")
    info_options.add_argument("-v", "--verbosity",
            nargs = '?',
            type = int,
            choices = [1, 2, 3],
            default = 2,
            help = (
                "This option controls how much detail is output to the terminal "
                "during output run. '1' results in a very quiet run, while '2' "
                "(default) displays more information about the run and '3' "
                "displays output from external program calls."
                ))
    info_options.add_argument("--version",
            action = "store_true",
            help = "Display version information and quit.")
    info_options.add_argument("--usage",
            action = "store_true",
            help = "Display some common usage examples and quit.")
    info_options.add_argument("--citation",
            action = "store_true",
            help = "Display citation and quit.")
    # Parse all arguments
    args = parser.parse_args()

    #for arg in args:
    #    print(arg)




# CODE FOR VALIDATING INPUT FILES
#seen = set()
#        duplicates = []
#        non_existent = set()
#        for file_path in self.infiles:
#            if file_path in seen:
#                duplicates.append(file_path)
#            if not _util.file_exists(file_path):
#                non_existent.add(file_path)
#        if


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\n Keyboard Interrupt detected: terminating")
