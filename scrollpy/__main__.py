#!/usr/bin/env python3

"""
Runs the main scrollpy program.
"""

import os
import sys
import argparse
import datetime
import logging


from scrollpy import scroll_log
from scrollpy import config
from scrollpy import load_config_file
from scrollpy import util
from scrollpy import Mapping
from scrollpy import Filter
from scrollpy import ScrollPy
from scrollpy import ScrollTree
from scrollpy import AlignIter
from scrollpy import AlignWriter
from scrollpy import SeqWriter
from scrollpy import TableWriter
# Import lookups
from scrollpy import __project__
from scrollpy import __version__
from scrollpy import __author__
from scrollpy import __license__
from scrollpy import __citation__

# Useful global
current_dir = os.getcwd()

##################################################################################
# FORMAT HEADER DESCRIPTION
##################################################################################

_name = __project__
_version = __version__
_author = __author__
_license = __license__
_citation = __citation__

_formatted_desc = ""  # TO-DO

##################################################################################
# PROJECT USAGE
##################################################################################

# Might not need this after all?
def _write_project_information():
    """Writes out information about the project"""
    pass

##################################################################################
# SAMPLE USAGE
##################################################################################

# def _write_sample_usage():
#    """Writes out some sample usage examples"""
#    pass

_usage = "Usage message"


def main():
    ##############################################################################
    # BEGIN TIMING
    ##############################################################################

    main_start = datetime.datetime.now()

    ##############################################################################
    # COMMAND LINE ARGUMENT
    ##############################################################################

    parser = argparse.ArgumentParser(
            description = _formatted_desc,
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
                "is set. If target directory is not specified, or directory "
                "creation fails, defaults to the current directory."
                ))
    file_options.add_argument("--tmpout",
            nargs = '?',
            metavar = "Keep Temporary Output",
            default = None,
            help = (
                "Target directory for intermediate run files. If specified "
                "and does not exist, it is created unless the '--no-create' "
                "flag is set. If creation fails, tries to create /tmp/ in the "
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
            choices = ["hist","bisect"],
            default = "hist",
            metavar = "Column selection method",
            help = (
                "HELP TEXT FOR ITER METHOD"
                ))
    run_options.add_argument("--col-method",
            nargs = '?',
            choices = ["zorro"],  # WORK ON THIS
            default = "zorro",
            metavar = "Column Evaluation Method",
            help = (
                "HELP TEXT FOR ITERATING HERE"
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
            choices = ["zscore", "mad"],
            default = "zscore",
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
    run_options.add_argument("--filter-only",
            action = "store_true",
            help = (
                "Filters sequences according to 'filter-method' and outputs the "
                "starting sequences and/or filtered sequences as specified by "
                "other arguments without running any other methods."
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
    log_options.add_argument("--no-summ",
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

    # info_options.add_argument("--spinner",
    #         action = "store_true")

    # Parse all arguments
    args = parser.parse_args()

    #############################################################################
    # CONFIGURE LOGGING
    #############################################################################

    # Add logging preferences to global config
    config.add_section("ARGS")
    config.set("ARGS", 'log_level', str(args.log_level))
    config.set("ARGS", 'verbosity', str(args.verbosity))

    # Set up loggers
    name = 'scrollpy'  # can't use __name__ since it becomes __main__
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

    # Get loggers and configure each; default level is 'INFO'

    # Configure console handler
    console_handler = logging.StreamHandler(stream = sys.stderr)
    console_handler.setFormatter(scroll_log.raw_format)
    console_handler.addFilter(
            scroll_log.ConsoleFilter(
                args.verbosity,
                ),
            )
    # Create console logger and add handler to it
    console_logger = scroll_log.get_console_logger(name)
    console_logger.addHandler(console_handler)

    # Configure status handler
    status_handler = scroll_log.StreamOverwriter(stream = sys.stderr)
    status_handler.setFormatter(scroll_log.raw_format)
    status_handler.addFilter(
            scroll_log.ConsoleFilter(
                args.verbosity,
                ),
            )
    # Create status logger and add handler to it
    status_logger = scroll_log.get_status_logger(name)
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
    # Create file logger and add handler to it
    file_logger = scroll_log.get_file_logger(name)
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
    # Create output logger and add handler to it
    output_logger = scroll_log.get_output_logger(name)
    output_logger.addHandler(output_handler)


    #############################################################################
    # SIMPLE USE CASES
    #############################################################################

    # Check to see if any of 'citation'/'usage'/'version' present
    if args.version:
        scroll_log.log_message(
            scroll_log.BraceMessage("Version {}\n", _version),  # msg
            1,  # verbosity level of message
            'INFO',  # level
            console_logger,  # loggers
            )
        # print(_version)  # Move to logging!
        sys.exit (0)
    if args.citation:
        scroll_log.log_message(
            scroll_log.BraceMessage("Version {}\n", _citation),  # msg
            1,  # verbosity level of message
            'INFO',  # level
            console_logger,  # loggers
            )
        # print(_citation)  # Move to logging!
        sys.exit(0)
    if args.usage:
        scroll_log.log_message(
            scroll_log.BraceMessage("Version {}\n", _usage),  # msg
            1,  # verbosity level of message
            'INFO',  # level
            console_logger,  # loggers
            )
        # print(_usage)
        sys.exit(0)

    # Testing status logger - delete eventually
    # if args.spinner:
    #     import time
    #     for i in range(10):
    #         scroll_log.log_message(
    #             scroll_log.BraceMessage("Displaying {} of 9\r",i),
    #             1,
    #             'INFO',
    #             status_logger,
    #             )
    #         # display(
    #         #     "Displaying {} ".format(i),
    #         #     rewritable=True,
    #         # )
    #         time.sleep(1)
    #     sys.exit(0)


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
    scroll_log.log_newlines(console_logger, file_logger, number=2)

    # Check the filepaths for appropriateness
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
    # Mapping file, if supplied
    if args.mapping:  # Nonetype if not called at all
        real_path = os.path.realpath(os.path.join(current_dir,args.mapping))
        all_paths.append(real_path)  # Only one file
    # Quit if no paths specified
    if len(all_paths) == 0: # No input files!
        scroll_log.log_message(
                scroll_log.BraceMessage(
                    "No input files detected; please try again"),  # msg
                1,  # verbosity level of message
                'ERROR',  # level
                console_logger, file_logger,  # loggers
                )
        sys.exit(0)

    # Check for duplicates and quit if any exist
    duplicates = util.check_duplicate_paths(*all_paths)
    if len(duplicates) > 0:
        scroll_log.log_message(
                scroll_log.BraceMessage(
                    "Duplicate filepaths detected in input:\n"),  # msg
                1,  # verbosity level of message
                'ERROR',  # level
                console_logger, file_logger,  # loggers
                )
        for path in duplicates:
            scroll_log.log_message(
                    scroll_log.BraceMessage(
                        "Duplicate path {} detected\n", path),  # msg
                    1,  # verbosity level of message
                    'ERROR',  # level
                    console_logger, file_logger,  # loggers
                    )
        sys.exit(0)

    # Check to make sure all paths are good!
    non_existent = util.check_input_paths(*all_paths)
    if len(non_existent) > 0:
        for path in non_existent:
            scroll_log.log_message(
                    scroll_log.BraceMessage(
                        "Non-existent filepath {} detected\n", path),
                    1,
                    'ERROR',
                    console_logger, file_logger,
                    )
        sys.exit(0)

    # Check whether the output directory exists; if not, try to make it
    if not args.out:
        args.out = current_dir
    else:
        if not args.no_create:
            try:
                util.ensure_dir_exists(args.out)
            except OSError:
                scroll_log.log_message(
                        scroll_log.BraceMessage(
                            "Failed to create output directory {}; using current "
                            "directory instead\n", args.out),
                        1,
                        'ERROR',
                        console_logger, file_logger,
                        )
                args.out = current_dir
        else:
            scroll_log.log_message(
                    scroll_log.BraceMessage(
                        "Did not attempt to create output directory {}; try "
                        "again with the '--no-create' flag turned off\n", args.out),
                    1,
                    'WARNING',
                    console_logger, file_logger,
                    )
            args.out = current_dir

    # Check whether temporary output is specified
    if args.tmpout:  # None otherwise
        if not args.no_create:
            try:
                util.ensure_dir_exists(args.tmpout)
            except OSError:
                scroll_log.log_message(
                        scroll_log.BraceMessage(
                            "Failed to create temporary directory {}; falling "
                            "back to 'tmp' in current directory", args.tmpout),
                        1,
                        'ERROR',
                        console_logger, file_logger,
                        )
                new_tmp = os.path.join(current_dir, '/tmp/')
                try:
                    util.ensure_dir_exists(new_tmp)
                except OSError:
                    scroll_log.log_message(
                            scroll_log.BraceMessage(
                                "Failed to create temporary directory {}; falling "
                                "back to system temp. Files may or may not be recoverable\n",
                                new_tmp),
                            1,
                            'ERROR',
                            console_logger, output_logger,
                            )
                    args.tmpout = None  # Fall back to tmp dir

    # Need to check all other parameters here...

    ##############################################################################
    # POPULATE GLOBAL CONFIG
    ##############################################################################

    # ADD PARAMS TO CONFIGS IF NECESSARY!!!
    #config.add_section("ARGS")
    vargs = vars(args)  # make dict-like for iter
    for arg,val in vargs.items():
        if arg not in ('infiles','treefile'):
            sarg = str(arg)  # ConfigParser demands strings
            sval = str(val)  # ConfigParser demands strings
            config.set("ARGS", sarg, sval)  # Assign to config dictionary!

    # Load from config file
    # Call this later so that we can configure logging first!
    load_config_file()
#    print("Config Arguments")
#    for key in config["ARGS"]:
#        print("{} : {}".format(key, config["ARGS"][key]))
#    print("Config Alignment")
#    for key in config["ALIGNMENT"]:
#        print("{} : {}".format(key, config["ALIGNMENT"][key]))
#    print("Config Distance")
#    for key in config["DISTANCE"]:
#        print("{} : {}".format(key, config["DISTANCE"][key]))

    ##############################################################################
    # ACTUAL PROGRAM EXECUTION
    ##############################################################################

    # Actual program execution
    scroll_log.log_message(
        scroll_log.BraceMessage("Starting main program analysis\n"),  # msg
        2,  # verbosity level of message
        'INFO',  # level
        console_logger, file_logger  # loggers
        )

    # SOMEWHERE HERE: CHECK INPUT ARGS

    # Begin by creating a mapping, unless iteralign
    if not args.iteralign:
        scroll_log.log_message(
                scroll_log.BraceMessage("Creating sequence mapping\n"),
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
        start_seq_dict = mapping()  # Run to get mapped seq_dict

    # Filter if necessary
    # Ensure that filtering only still calls filter!
    if args.filter_only:
        args.filter=True
    # Actually filter
    removed_seq_dict=None  # If not filtering
    if args.filter:
        scroll_log.log_message(
                scroll_log.BraceMessage("Filtering input sequences\n"),
                2,
                'INFO',
                console_logger, file_logger,
                )
        seq_filter = Filter(  # Additional args should be in config already
                start_seq_dict,
                )
        # Call, and bind filtered seq_dict to 'start_seq_dict' var
        start_seq_dict,removed_seq_dict = seq_filter()
    # If filtering only, output directly from Filter
    if args.filter_only:
        pass

    # Run actual program execution now
    if args.placeseqs:  # TreePlacer
        scroll_log.log_message(
                scroll_log.BraceMessage("Initializing tree placing analysis\n"),
                1,
                'INFO',
                console_logger, file_logger,
                )
        RunObj = TreePlacer(
                start_seq_dict, # Filtered or not
                args.alignment, # Input alignment
                args.toplace,   # Sequence file to place
                args.tmpout,    # Tmp out
                )
    elif args.iteralign:  # IterAlign
        scroll_log.log_message(
                scroll_log.BraceMessage("Initializing alignment iteration analysis\n"),
                1,
                'INFO',
                console_logger, file_logger,
                )
        RunObj = AlignIter(
                args.alignment,
                args.tmpout,
                )
        alignout = True  # Signal to output an alignment
    else:  # Distance-based analysis!
        if not args.treefile:  # Sequence-based analysis
            scroll_log.log_message(
                    scroll_log.BraceMessage(
                        "Initializing sequence-based scrollsaw analysis"),
                    1,
                    'INFO',
                    console_logger, file_logger,
                    )
            RunObj = ScrollPy(
                    start_seq_dict, # Filtered or not
                    args.tmpout,    # Actual program run uses tmp dir!
                    )
        else:  # Tree-based analysis
            scroll_log.log_message(
                    scroll_log.BraceMessage(
                        "Initializing tree-based scrollsaw analysis"),
                    1,
                    'INFO',
                    console_logger, file_logger,
                    )
            RunObj = ScrollTree(
                    start_seq_dict, # Filtered or not
                    )
    # Perform the actual program execution
    RunObj()

    # Write to outfile(s); config handles gritty details
    scroll_log.log_message(
            scroll_log.BraceMessage(
                "Writing output files"),
            2,
            'INFO',
            console_logger, file_logger,
            )
    # Write table file no matter what
    tbl_writer = TableWriter(
            RunObj,    # object to use
            args.out,  # specified output location
            )
    try:
        tbl_writer.write()
    except:  # Dangerous; Change!!!
        scroll_log.log_message(  # Log exception instead?!?
                scroll_log.BraceMessage(
                    "Failed to write output table"),
                1,
                'ERROR',
                console_logger, file_logger,
                )

    # Write optimal alignment, if AlignIter was performed
    if alignout:
        align_writer = AlignWriter(
                RunObj,
                args.out,
                )
        align_writer.write()

    # Write sequences, if requested
    if args.seqout:  # User requested sequences
        seq_writer = SeqWriter(
                RunObj,   # Object to use
                args.out, # Specified output location
                )
        #try:
        seq_writer.write()
        #except:  # Dangerous; Change!!!
        #    print("Unexpected error when writing sequence files")  # Logging!

    if args.filter_out:  # User requested filtered sequences
        filter_writer = SeqWriter(
                seq_filter,  # Filter object
                args.out,    # Specified output location
                )
        filter_writer.write()
    # Something about a summary file? -> TO_DO

    # Finish timing and report back results
    main_end = datetime.datetime.now()
    scroll_log.log_message(
            scroll_log.BraceMessage(
                "Finished analysis at {} \n", main_end),
            2,  # verbosity level of message
            'INFO',  # level
            console_logger, file_logger,  # loggers
            )

    analysis_time = main_end - main_start
    # Datetime timedelta objects are weird and only store days, seconds,
    # and microseconds as attrs; convert to include hours and minutes
    converted_total = util.time_list(analysis_time)
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


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\n Keyboard Interrupt detected: terminating")
