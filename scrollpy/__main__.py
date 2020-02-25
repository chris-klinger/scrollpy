#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
Runs the main scrollpy program.

"""

import os
import shutil
import sys
import argparse
import datetime
import logging

# Report project usage/information
from scrollpy import get_argparse_descr
from scrollpy import write_citation
from scrollpy import write_description
from scrollpy import write_usage
from scrollpy import write_version
# Logging
from scrollpy import scroll_log
from scrollpy import BraceMessage
# Config
from scrollpy import config
from scrollpy import load_config_file
# Exceptions
from scrollpy import FatalScrollPyError
# Execution classes
from scrollpy import Mapping
from scrollpy import Filter
from scrollpy import ScrollPy
from scrollpy import ScrollTree
from scrollpy import AlignIter
from scrollpy import TreePlacer
# Output classes
from scrollpy import AlignWriter
from scrollpy import SeqWriter
from scrollpy import TableWriter
# Utility
from scrollpy import scrollutil
# Global list for tmp dirs
from scrollpy import tmps_to_remove
# Import lookups
from scrollpy import __project__
from scrollpy import __version__
from scrollpy import __author__
from scrollpy import __license__
from scrollpy import __citation__

# Useful global
current_dir = os.getcwd()

##################################################################################
# GET MODULE LOGGER NAMES
##################################################################################

# In order to log messages outside of main(), logger names need to be
# defined as globals; actual loggers themselves are still configured
# in main() based on user input
name = 'scrollpy'  # can't use __name__ since it becomes __main__
(console_logger, status_logger, file_logger, output_logger) = \
        scroll_log.get_module_loggers(name)

##################################################################################
# MAIN FUNCTION FOR PROGRAM EXECUTION
##################################################################################

def main():
    ##############################################################################
    # BEGIN TIMING
    ##############################################################################

    main_start = datetime.datetime.now()

    #############################################################################
    # IF NO ARGUMENTS PASSED, PRINT DESCRIPTION
    #############################################################################

    # Used for all manual writing in main()
    term_width = min(82, scroll_log._get_current_terminal_width())
    # No arguments -> prompt user
    if len(sys.argv[1:]) == 0:
        write_description(term_width)
        sys.exit(0)

    ##############################################################################
    # COMMAND LINE ARGUMENT
    ##############################################################################

    parser = argparse.ArgumentParser(
            # description = _formatted_desc,
            description = get_argparse_descr(),
            formatter_class = argparse.HelpFormatter,  # TO-DO
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
            choices = ["nexus", "newick", "phylip", "nexml"],  # EXPAND?
            help = (
                "Format of tree file, if supplied. Defaults to 'newick'."
                ))
    file_options.add_argument("-a", "--alignment",
            nargs = '?',
            metavar = "Alignment Path",
            help = (
                "Path to a file containing an alignment (optional). "
                "Required if analysis is to place sequences or to iterate "
                "over an alignment to select optimal columns."
                ))
    file_options.add_argument("--alignfmt",
            nargs = '?',
            metavar = "Alignment Format",
            default = "fasta",
            choices = ["nexus", "clustal", "emboss"],  # EXPAND
            help = (
                "Format of alignment file, if supplied. Defaults to 'fasta'."
                ))
    file_options.add_argument("-c", "--toplace",
            nargs = '?',
            metavar = "Sequences to Place",
            help = (
                "Path to a file containing sequences to place (optional). "
                "If provided, file will be parsed assuming that the sequences "
                "are in the format specified by '--infmt' and consist of the "
                "same alphabet as specified by '--seqtype'."
                ))
    file_options.add_argument("-o", "--out",
            nargs = '?',
            metavar = "Target Output Directory",
            default = None,
            help = (
                "Target directory for output files. If the target directory "
                "does not exist, it is created unless the '--no-create' flag "
                "is set. If a single name is specified, e.g. 'out', it is "
                "created as a subdirectory of the current working directory. "
                "If target directory is not specified, or directory creation "
                "fails, defaults to the current directory."
                ))
    file_options.add_argument("--tmpout",
            nargs = '?',
            metavar = "Keep Temporary Output",
            default = None,
            help = (
                "Target directory for intermediate run files. If specified "
                "and does not exist, it is created unless the '--no-create' "
                "flag is set. If a single name is specified, e.g. 'tmpout', "
                "it is created as a subdirectory of the current working "
                "directory. If creation fails, tries to create /tmp/ in the "
                "current directory instead. If not specified, or if all creation "
                "attempts fail, a temporary directory is used and removed "
                "following execution."
                ))
    file_options.add_argument("--suffix",
            nargs = '?',
            metavar = "Output File Suffix",
            default = '',
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
            default = '_',
            help = (
                "Allows to set the delimiter in output filepaths."
                ))
    file_options.add_argument("--tblsep",
            nargs = '?',
            metavar = "Table Column Separator",
            default = ',',
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
    run_options.add_argument("--align-method",
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
    run_options.add_argument("--dist-method",
            nargs = '?',
            choices = ["PhyML", "RAxML", "Generic"], # TO-DO
            default = "RAxML",
            metavar = "Distance Method",
            help = (
                "Method to use for calculating distances. Any other options than "
                "'Generic' requires that the corresponding option in the config "
                "file is set properly."
                ))
    run_options.add_argument("--dist-matrix",
            nargs = '?',
            choices = ["WAG", "LG", "JC"], # TO-DO
            default = "LG",
            metavar = "Distance Matrix",
            help = (
                "Specify a substitution matrix for distance calculations. If "
                "the called program does not accept the matrix, the default "
                "will be used instead. Default is to use the default specified "
                "by each program, or 'LG'/'GTR' when using 'Generic'."
                ))
    run_options.add_argument("--tree-method",
            nargs = '?',
            choices = ["Iqtree", "RAxML"], # TO-DO
            default = "Iqtree",
            metavar = "Tree Method",
            help = (
                "Method to use for building trees. Regardless of which method is "
                "chosen, the corresponding option in the config file must be set "
                "properly in order for the program to run."
                ))
    run_options.add_argument("--tree-matrix",
            nargs = '?',
            choices = ["WAG", "LG", "JC"], # TO-DO
            default = "LG",
            metavar = "Tree Matrix",
            help = (
                "Specify a substitution matrix for tree building. If the "
                "called program does not accept the matrix, the default "
                "will be used instead. Default is to use the default specified "
                "by each program."
                ))
    run_options.add_argument("-p", "--placeseqs",
            action = "store_true",
            help = (
                "Analysis defaults to placing sequences in a given tree to "
                "classify them. Requires user also specifies a sequence file "
                "using '--toplace' and an alignment using '--alignment' at a "
                "minimum."
                ))
    run_options.add_argument("-e", "--iteralign",
            action = "store_true",
            help = (
                "Analysis defaults to iterating over an alignment to select "
                "optimal columns for tree building. Requires user also specify "
                "an input alignment using '--alignment'. Outputs the optimal "
                "alignment found in the same format specified for the input "
                "alignment, i.e. specified by the '--alignfmt' argument."
                ))
    run_options.add_argument("--iter-method",
            nargs = '?',
            choices = ["bisection", "histogram"],
            default = "bisection",
            metavar = "Alignment Iteration Method",
            help = (
                "Method to use to iterate over alignment columns; 'bisection' "
                "iteratively splits the alignment over half the remaining length "
                "and chooses high or low depending on the resulting tree score. "
                "The 'histogram' method bins all remaining columns at each step "
                "and removes a fraction of the first bin relative to the length "
                "of the alignment relative to its starting length."
                ))
    run_options.add_argument("--col-method",
            nargs = '?',
            choices = ["zorro"],  # WORK ON THIS
            default = "zorro",
            metavar = "Column Evaluation Method",
            help = (
                "Method to use for assigning scores to alignment columns."
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
            choices = ["zscore", "mad", "identity"],
            default = "zscore",
            metavar = "Filtering Method",
            help = (
                "Method to use for filtering input sequences. Choosing either "
                "'zscore' or 'mad' filters based on sequence length, using "
                "either standard z-score or median absolute deviation. Choosing "
                "'identity' filters based on the similarity of aligned sequences "
                "to each other. For all methods, the appropriate cutoff value "
                "can be specified used --filter-score."
                ))
    run_options.add_argument("--filter-score",
            nargs = '?',
            default = None,
            metavar = "Filtering Score",
            help = (
                "Score cutoff for determining which sequences to filter. If "
                "not set, it defaults to a different value depending on the "
                "'--filter-method' chosen."
                ))
    run_options.add_argument("--num-filter",
            nargs = '?',
            default = 3,
            metavar = "Filtering Threshold",
            help = (
                "Control the number of sequences filtering is required to leave "
                "while removing from one or more groups. If sequences would be "
                "removed but cannot be due to this threshold, a warning message "
                "is written to the logfile informing the user."
                ))
    run_options.add_argument("--filter-out",
            action = "store_true",
            help = (
                "Outputs filtered sequences in the same format as specified for "
                "'--seqout'. Filtered sequences will be organized by group."
                ))
    run_options.add_argument("--filter-only",
            action = "store_true",
            help = (
                "Filters sequences according to 'filter-method' and outputs the "
                "starting sequences and/or filtered sequences as specified by "
                "other arguments without running any other methods."
                ))
    run_options.add_argument("--filter-bygroup",
            action = "store_true",
            help = (
                "Whether to apply filtering to each group of sequences or to "
                "all sequences combined."
                ))
    # Possible future feature for implementation
    # run_options.add_argument("-s", "--split-seqs",
    #         action = "store_true",
    #         help = (
    #             "If a single file is used as input, and '--mapping' is not "
    #             "specified, attempt to split input sequence file into an "
    #             "optimal number of sub-groups based on pariwise similarity "
    #             "and given that each group must have at least two sequences."
    #             ))
    # run_options.add_argument("--split-method",  # TO-DO
    #         nargs = '?',
    #         choices = ["one", "two"],
    #         default = "one",
    #         metavar = "Splitting Method",
    #         help = (
    #             "HELP TEXT FOR SPLITTING METHOD"
    #             ))
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
    run_options.add_argument("--support",
            nargs = '?',
            choices = list(range(101)),
            type = int,
            default = 80,
            metavar = "Classification Tree Support",
            help = (
                "When placing sequences in a tree, the minimum node support "
                "value for the sequence to be considered 'classified'."
                ))
    # Using config values is a future TO-DO
    # run_options.add_argument("--use-config",
    #         action = "store_true",
    #         help = (
    #             "This option allows the user finer control over external "
    #             "program runs by specifying the values of additional parameters "
    #             "to use in the config file. Values must be specified as they "
    #             "would appear on the command line under their own header "
    #             "within the config file. See docs for more information."
    #             ))
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
    # Summary files are a future TO-DO
    # log_options.add_argument("--no-summ",
    #         action = "store_true",
    #         help = (
    #             "This option turns off the automatic summary file generated on "
    #             "each run. Not recommended."
    #             ))
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
                "displays real-time program execution updates."
                ))
    info_options.add_argument("--silent",
            action = "store_true",
            help = (
                "This option turns off all writing to the screen during program "
                "execution."
                ))
    info_options.add_argument("--version",
            action = "store_true",
            help = "Display version information and quit.",
            )
    info_options.add_argument("--usage",
            action = "store_true",
            help = "Display some common usage examples and quit.",
            )
    info_options.add_argument("--citation",
            action = "store_true",
            help = "Display citation and quit.",
            )

    # Parse all arguments
    args = parser.parse_args()
    # Modify output directory(ies) if they are a single name
    # Allows user to write a shorter outpath to the current dir
    # MAIN OUTPUT
    if scrollutil.path_is_name_only(args.out):
        # Sanitize any leading path chars
        sanitized_out = args.out.lstrip(os.sep)
        new_out = os.path.join(current_dir, sanitized_out)
        args.out = new_out
    # TEMP OUTPUT
    if scrollutil.path_is_name_only(args.tmpout):
        # Sanitize any leading path chars
        sanitized_tmpout = args.tmpout.lstrip(os.sep)
        new_tmpout = os.path.join(current_dir, sanitized_tmpout)
        args.tmpout = new_tmpout

    #############################################################################
    # SIMPLE USE CASES
    #############################################################################

    # VERSION information
    if args.version:
        write_version(term_width)  # term_width calculated at beginning of main()
        sys.exit (0)
    # CITATION information
    if args.citation:
        write_citation(term_width)
        sys.exit(0)
    # USAGE information
    if args.usage:
        write_usage(term_width)
        sys.exit(0)

    #############################################################################
    # CONFIGURE LOGGING
    #############################################################################

    # Add logging preferences to global config
    config.add_section("ARGS")
    config.set("ARGS", 'log_level', str(args.log_level))
    config.set("ARGS", 'verbosity', str(args.verbosity))

    # Set up loggers
    out = args.out if args.out else current_dir
    logfile_path = scroll_log.get_logfile(
            args.no_log,      # Whether to log to file
            # True,  # JUST FOR TESTING
            args.logfile,     # Logfile name/path
            out,         # Output directory
            args.no_create,   # Directory creation
            args.no_clobber,  # Replace existing file
            args.filesep,     # Separator for files
            )

    # Configure each logger; default level is 'INFO'
    # Configure console handler
    console_handler = logging.StreamHandler(stream = sys.stderr)
    console_handler.setFormatter(scroll_log.raw_format)
    console_handler.addFilter(
            scroll_log.ConsoleFilter(
                args.verbosity,
                args.silent,  # If set, no output will be logged
                ),
            )
    console_logger.addHandler(console_handler)

    # Configure status handler
    status_handler = scroll_log.StreamOverwriter(stream = sys.stderr)
    status_handler.setFormatter(scroll_log.raw_format)
    status_handler.addFilter(
            scroll_log.ConsoleFilter(
                args.verbosity,
                args.silent,  # If set, no output will be logged
                ),
            )
    status_logger.addHandler(status_handler)

    # Configure file handler
    file_handler = logging.FileHandler(filename = logfile_path)  # mode='a'
    file_handler.setFormatter(scroll_log.rich_format)
    file_handler.addFilter(
            scroll_log.FileFilter(
                args.log_level,
                args.no_log,  # If set, no output will be logged
                ),
            )
    file_logger.addHandler(file_handler)

    # Configure output handler
    output_handler = logging.FileHandler(filename = logfile_path)  # Same as file
    output_handler.setFormatter(scroll_log.raw_format)
    output_handler.addFilter(
            scroll_log.OutputFilter(
                args.log_level,
                args.no_log,  # If set, no output will be logged
                ),
            )
    output_logger.addHandler(output_handler)

    ##############################################################################
    # PARAMETER VALIDATION
    ##############################################################################

    # Indicate start time
    scroll_log.log_message(
            scroll_log.BraceMessage("Initialized at {}", main_start),  # msg
            2,  # verbosity level of message
            'INFO',  # level
            console_logger, file_logger,  # loggers
            )
    scroll_log.log_newlines(console_logger)

    # CHECK INPUT ARGS FOR RUN PARAMETERS -> MAKE SURE NO CLASHES

    # Make sure args don't clash
    if args.placeseqs and args.iteralign:
        scroll_log.log_message(
                BraceMessage(
                    "Cannot specify '--placeseqs' and '--iteralign' in same run"),
                1,
                'ERROR',
                console_logger, file_logger,
                )
        raise FatalScrollPyError
    if args.toplace and args.iteralign:
        scroll_log.log_message(
                BraceMessage(
                    "Cannot specify '--toplace' and '--iteralign' in same run"),
                1,
                'ERROR',
                console_logger, file_logger,
                )
        raise FatalScrollPyError
    # Check for placeseqs
    if args.placeseqs:
        if not args.alignment:
            scroll_log.log_message(
                    BraceMessage(
                        "No alignment file for placing sequences detected"),
                    1,
                    'ERROR',
                    console_logger, file_logger,
                    )
            raise FatalScrollPyError
        if not args.toplace:
            scroll_log.log_message(
                    BraceMessage(
                        "No sequences to place detected"),
                    1,
                    'ERROR',
                    console_logger, file_logger,
                    )
            raise FatalScrollPyError
    # Consider that user might specify -c without -p -> ambiguous!
    if args.toplace:
        if not args.placeseqs:
            scroll_log.log_message(
                    BraceMessage(
                        "Placement sequences detected; please specify --placeseqs as well"),
                    1,
                    'ERROR',
                    console_logger, file_logger,
                    )
            raise FatalScrollPyError
    # Check for iteralign
    if args.iteralign:
        if not args.alignment:
            scroll_log.log_message(
                    BraceMessage(
                        "No alignment to iterate over detected"),
                    1,
                    'ERROR',
                    console_logger, file_logger,
                    )
            raise FatalScrollPyError

    # CHECK INPUT FILEPATHS; MAKE SURE THEY EXIST

    all_paths = []
    # Sequence infile(s)
    if args.infiles:  # Nonetype if not called at all
        if len(args.infiles) > 0:  # list; zero-length if none specified
            for path in args.infiles:
                # os.path ensures correct full path
                real_path = os.path.realpath(os.path.join(current_dir,path))
                all_paths.append(real_path)
    else:
        args.infiles = []  # Empty list
    # Tree file, if supplied
    if args.treefile:  # Nonetype if not called at all
        real_path = os.path.realpath(os.path.join(current_dir,args.treefile))
        all_paths.append(real_path)  # Only one file
    # Alignment file, if supplied
    if args.alignment:
        real_path = os.path.realpath(os.path.join(current_dir,args.alignment))
        all_paths.append(real_path)
    # Seqs to place, if supplied
    if args.toplace:
        real_path = os.path.realpath(os.path.join(current_dir,args.toplace))
        all_paths.append(real_path)
    # Mapping file, if supplied
    if args.mapping:  # Nonetype if not called at all
        real_path = os.path.realpath(os.path.join(current_dir,args.mapping))
        all_paths.append(real_path)  # Only one file
    # Quit if no paths specified
    if len(all_paths) == 0: # No input files!
        scroll_log.log_message(
                BraceMessage(
                    "No input files detected; please try again"),  # msg
                1,  # verbosity level of message
                'ERROR',  # level
                console_logger, file_logger,  # loggers
                )
        raise FatalScrollPyError

    # Check for duplicates and quit if any exist
    duplicates = scrollutil.check_duplicate_paths(*all_paths)
    if len(duplicates) > 0:
        scroll_log.log_message(
                BraceMessage(
                    "Duplicate filepaths detected in input:"),  # msg
                1,  # verbosity level of message
                'ERROR',  # level
                console_logger, file_logger,  # loggers
                )
        for path in duplicates:
            scroll_log.log_message(
                    BraceMessage(
                        "Duplicate path {} detected", path),  # msg
                    1,  # verbosity level of message
                    'ERROR',  # level
                    console_logger, file_logger,  # loggers
                    )
            raise FatalScrollPyError

    # Check to make sure all paths are good!
    non_existent = scrollutil.check_input_paths(*all_paths)
    if len(non_existent) > 0:
        for path in non_existent:
            scroll_log.log_message(
                    BraceMessage(
                        "Non-existent filepath {} detected", path),
                    1,
                    'ERROR',
                    console_logger, file_logger,
                    )
            raise FatalScrollPyError

    # CHECK WHETHER OUTPUT DIRS EXIST; TRY TO MAKE IF NOT

    # Check whether the output directory exists; if not, try to make it
    if not args.out:
        args.out = current_dir
    else:
        if not args.no_create:
            try:
                scrollutil.ensure_dir_exists(args.out)
            except OSError:
                scroll_log.log_message(
                        BraceMessage(
                            "Failed to create output directory {}; using current "
                            "directory instead", args.out),
                        1,
                        'ERROR',
                        console_logger, file_logger,
                        )
                args.out = current_dir
        else:
            scroll_log.log_message(
                    BraceMessage(
                        "Did not attempt to create output directory {}; try "
                        "again with the '--no-create' flag turned off", args.out),
                    2,
                    'WARNING',
                    console_logger, file_logger,
                    )
            args.out = current_dir

    # Check whether temporary output is specified
    if args.tmpout:  # None otherwise
        if not args.no_create:
            try:
                scrollutil.ensure_dir_exists(args.tmpout)
            except OSError:
                scroll_log.log_message(
                        BraceMessage(
                            "Failed to create temporary directory {}; falling "
                            "back to 'tmp' in current directory", args.tmpout),
                        1,
                        'ERROR',
                        console_logger, file_logger,
                        )
                new_tmp = os.path.join(current_dir, '/tmp/')
                try:
                    scrollutil.ensure_dir_exists(new_tmp)
                except OSError:
                    scroll_log.log_message(
                            BraceMessage(
                                "Failed to create temporary directory {}; falling "
                                "back to system temp. Files may or may not be recoverable",
                                new_tmp),
                            1,
                            'ERROR',
                            console_logger, output_logger,
                            )
                    args.tmpout = None  # Fall back to tmp dir

    # MAKE SURE THAT FILE SUFFIX AND SEP ARGS ARE NOT PROBLEMATIC

    # Optional file suffix
    if args.suffix:  # Can be None
        if not scrollutil.is_value_ok_with_path(args.suffix):
            scroll_log.log_message(
                    BraceMessage(
                        "File suffix {} contains disallowed character {}. "
                        "ScrollPy will attemp to change it".format(
                            args.suffix, os.sep)),
                        1,
                        'ERROR',
                        console_logger, output_logger,
                        )
            new_suffix = scroll_util.make_ok_with_path(args.suffix)
            scroll_log.log_message(
                    BraceMessage("New file suffix is {}".format(new_suffix)),
                    2,
                    'WARNING',
                    console_logger, file_logger,
                    )

    # Optional file sep; underscore if not set
    if not scrollutil.is_value_ok_with_path(args.filesep):
        scroll_log.log_message(
                BraceMessage(
                    "Specified file separator {} is invalid, defaulting "
                    "to a single underscore ('_') instead".format(args.filesep)),
                1,
                'ERROR',
                console_logger, file_logger,
                )
        args.filesep = '_'

    # SET TBLSEP IF NOT SET BY USER

    tblfmt = args.tblfmt
    if tblfmt == 'csv':  # Default
        tblsep = ','
    elif tblfmt == 'space-delim':
        tblsep = ' '
    elif tblfmt == 'tab-delim':
        tblsep = '\t'
    else:  # Otherwise, user-specified
        if not isinstance(args.tblsep, str):  # Invalid value for sep
            scroll_log.log_message(
                    BraceMessage("Specified table separator {} "
                        "is invalid; defaulting to CSV format".format(
                            args.tblsep)),
                        1,
                        'ERROR',
                        console_logger, file_logger,
                        )
            tblsep = ','
        else:  # Specified sep is ok
            tblsep = args.tblsep
    # Finally, set the value
    args.tblsep = tblsep

    ##############################################################################
    # POPULATE GLOBAL CONFIG
    ##############################################################################

    # ADD PARAMS TO CONFIGS IF NECESSARY!!!
    vargs = vars(args)  # make dict-like for iter
    for arg,val in vargs.items():
        if arg not in ('infiles','treefile'):
            sarg = str(arg)  # ConfigParser demands strings
            sval = str(val)  # ConfigParser demands strings
            config.set("ARGS", sarg, sval)  # Assign to config dictionary!

    # Load from config file
    # Call this later so that we can configure logging first!
    load_config_file()
    scroll_log.log_newlines(console_logger)

    ##############################################################################
    # FUNCTIONS CALLED BY RUN CODE
    ##############################################################################

    def get_mapping_object():
        """Populates a mapping object for all sequence objects.

        Returns:
            obj: A populated Mapping object.

        """
        scroll_log.log_message(
                BraceMessage("Creating sequence mapping"),
                2,
                'INFO',
                console_logger, file_logger
                )
        mapping = Mapping(
                args.infiles,              # List to unpack
                alignfile=args.alignment,  # None if not provided
                treefile=args.treefile,    # None if not provided
                mapfile=args.mapping,      # None if not provided
                )
        return mapping


    def get_filter_object(seq_dict):
        """Populates a filtering object for sequence removal.

        Args:
            seq_dict (dict): A dictionary of mapped sequences.

        Returns:
            obj: A populated Filter object.

        """
        scroll_log.log_message(
                BraceMessage("Filtering input sequences"),
                2,
                'INFO',
                console_logger, file_logger,
                )
        seq_filter = Filter(  # Additional args should be in config already
                seq_dict,
                )
        # Call, and bind filtered seq_dict to 'start_seq_dict' var
        return seq_filter


    def get_analysis_object(seq_dict):
        """Determines which analysis object to run.

        Args:
            seq_dict (dict): A dictionary of mapped sequences.

        Returns:
            obj: A populated object for the analysis. This is one of
                AlignIter, ScrollPy, ScrollTree, or TreePlacer.

        """
        if args.placeseqs:  # TreePlacer
            scroll_log.log_message(
                    BraceMessage("Initializing tree placing analysis"),
                    2,
                    'INFO',
                    console_logger, file_logger,
                    )
            run_obj = TreePlacer(
                    seq_dict,       # Filtered or not
                    args.alignment, # Input alignment
                    args.toplace,   # Sequence file to place
                    args.tmpout,    # Tmp out
                    )
        elif args.iteralign:  # IterAlign
            scroll_log.log_message(
                    BraceMessage("Initializing alignment iteration analysis"),
                    2,
                    'INFO',
                    console_logger, file_logger,
                    )
            run_obj = AlignIter(
                    args.alignment,
                    args.tmpout,
                    )
        else:  # Distance-based analysis!
            if not args.treefile:  # Sequence-based analysis
                scroll_log.log_message(
                        BraceMessage(
                            "Initializing sequence-based scrollsaw analysis"),
                        2,
                        'INFO',
                        console_logger, file_logger,
                        )
                run_obj = ScrollPy(
                        seq_dict,    # Filtered or not
                        args.tmpout, # Actual program run uses tmp dir!
                        )
            else:  # Tree-based analysis
                scroll_log.log_message(
                        BraceMessage(
                            "Initializing tree-based scrollsaw analysis"),
                        2,
                        'INFO',
                        console_logger, file_logger,
                        )
                run_obj = ScrollTree(
                        seq_dict, # Filtered or not
                        )
        # Return the object to be run
        return run_obj


    def write_output_files(run_obj=None, filter_obj=None):
        """Creates necessary output objects and executes them.

        Args:
            run_obj (obj): An analysis object that has been called.
                Defaults to None.
            filter_obj (obj): A filter object that has been called.
                Defaults to None.

        """
        # Write to outfile(s); config handles gritty details
        scroll_log.log_message(
                BraceMessage("Writing output files"),
                2,
                'INFO',
                console_logger, file_logger,
                )
        # Write table file no matter what
        scroll_log.log_message(
                BraceMessage("Writing output table(s)"),
                2,
                'INFO',
                console_logger, file_logger,
                )
        if run_obj:
            run_tbl_writer = TableWriter(
                    run_obj,    # object to use
                    args.out,  # specified output location
                    )
            run_tbl_writer.write()
        if filter_obj:  # Can also have a table
            filter_tbl_writer = TableWriter(
                    filter_obj,    # object to use
                    args.out,  # specified output location
                    )
            filter_tbl_writer.write()
        # Write optimal alignment if AlignIter was performed
        if args.iteralign:
            if run_obj:
                scroll_log.log_message(
                        BraceMessage("Writing optimal output alignment"),
                        2,
                        'INFO',
                        console_logger, file_logger,
                        )
                align_writer = AlignWriter(
                        run_obj,
                        args.out,
                        )
                align_writer.write()
        # Write sequences, if requested
        if args.seqout:  # User requested sequences
            if run_obj:
                scroll_log.log_message(
                        BraceMessage("Writing output sequences"),
                        2,
                        'INFO',
                        console_logger, file_logger,
                        )
                seq_writer = SeqWriter(
                        run_obj,   # Object to use
                        args.out, # Specified output location
                        )
                seq_writer.write()
        if args.filter_out:  # User requested filtered sequences
            if filter_obj:
                scroll_log.log_message(
                        BraceMessage("Writing filtered sequences"),
                        2,
                        'INFO',
                        console_logger, file_logger,
                        )
                filter_writer = SeqWriter(
                        filter_obj,  # Filter object
                        args.out,    # Specified output location
                        )
                filter_writer.write()


    def finish_run():
        """Records run time information for a complete run.

        """
        # Finish timing and report back results
        main_end = datetime.datetime.now()
        scroll_log.log_message(
                BraceMessage("Finished analysis at {}", main_end),
                2,  # verbosity level of message
                'INFO',  # level
                console_logger, file_logger,  # loggers
                )
        # Subtraction creates a datetime.timedelta object
        analysis_time = main_end - main_start
        # Datetime timedelta objects are weird and only store days, seconds,
        # and microseconds as attrs; convert to include hours and minutes
        converted_total = scrollutil.time_list(analysis_time)
        scroll_log.log_message(
                scroll_log.BraceMessage(
                    "Analysis completed in {} days, {} hours, {} minutes, "
                    "{} seconds, and {} microseconds",
                    *converted_total,  # Tuple with 5 values; unpack
                    ),
                1,
                'INFO',
                console_logger, file_logger,
                )

    ##############################################################################
    # ACTUAL PROGRAM EXECUTION
    ##############################################################################

    # Actual program execution
    scroll_log.log_message(
        scroll_log.BraceMessage("Starting main program analysis"),
        2,
        'INFO',
        console_logger, file_logger
        )

    # Default starting values
    run_obj          = None
    filter_obj       = None
    start_seq_dict   = None
    removed_seq_dict = None

    # Begin by creating a mapping, unless run method is iteralign
    if not args.iteralign:
        map_obj = get_mapping_object()
        start_seq_dict = map_obj()

    # Filter if necessary
    if args.filter_only:
        args.filter=True
    if args.filter:  # Actually filter
        filter_obj = get_filter_object(start_seq_dict)
        start_seq_dict,removed_seq_dict = filter_obj()

    # Separate starting functionality from later functionality
    scroll_log.log_newlines(console_logger)

    # If filtering only, output directly from Filter
    if not args.filter_only:  # Actually run the analysis
        run_obj = get_analysis_object(start_seq_dict)
        # Run actual program execution now
        run_obj()

    # Write all possible output
    scroll_log.log_newlines(console_logger)
    write_output_files(run_obj, filter_obj)

    # Finally run the finishing code
    scroll_log.log_newlines(console_logger)
    finish_run()

##############################################################################
# DEFINE CLEANUP ACTIONS FOR PROGRAM TERMINATION
##############################################################################

def run_cleanup(successful=True):
    """Runs regardless of whether program run completes.

    If user does not specify a directory for temporary output, files are
    written throughout the program to one or more instances of Python's
    tempfile.TemporaryDirectory class. Attempt to cleanup each such
    instance prior to the program exiting.

    Args:
        successful (bool): Indicates whether the program ran to completion
            or was stopped early by an error.

    """
    for tmp_dir in tmps_to_remove:
        try:
            # tmp_dir.cleanup()
            shutil.rmtree(tmp_dir)
        except OSError:
            scroll_log.log_message(
                    BraceMessage("Failed to cleanup temporary directory "
                        "{}; may already have been deleted".format(tmp_dir)),
                    2,
                    'INFO',
                    file_logger,
                    )
    # Finally, exit the program
    if successful:
        sys.exit(0)  # Exit code means success
    else:
        sys.exit(1)  # Indicate something went wrong


if __name__ == '__main__':
    full_run = True  # Assume program runs fully
    try:
        main()
    except KeyboardInterrupt:
        scroll_log.log_newlines(console_logger)
        scroll_log.log_message(
                BraceMessage(
                    "Keyboard interrupt detected; exiting..."),
                1,
                'ERROR',
                console_logger, file_logger,
                )
        full_run = False  # Program ended before finishing
    except FatalScrollPyError:
        # Add newlines in case status logging was occuring prior to error
        scroll_log.log_newlines(console_logger)
        scroll_log.log_message(
                BraceMessage(
                    "ScrollPy has encountered a fatal error; exiting..."),
                1,
                'ERROR',
                console_logger, file_logger,
                )
        full_run = False  # Program ended before finishing
    # Add one more case in here
    except Exception as e:  # Something unexpected ends program
        scroll_log.log_newlines(console_logger)
        # Log the exception itself for debugging
        scroll_log.log_message(
                BraceMessage(""),
                1,
                'ERROR',
                console_logger, file_logger,
                exc_obj=e,
                )
        # Let the user know the program is exiting
        scroll_log.log_message(
                BraceMessage(
                    "ScrollPy has encountered an unexpected error; exiting..."),
                1,
                'ERROR',
                console_logger, file_logger,
                )
        full_run = False
    finally:
        # Whether there was an error or not, need to remove any remaining
        # temporary directories; user does not want output
        run_cleanup(full_run)

