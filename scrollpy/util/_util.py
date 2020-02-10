"""Contains general utility functions for use throughout Scrollpy.

There is no pattern to the functions included in this module, in terms of
their function. Rather, they are used throughout other program modules and
therefore are defined once rather than in multiple places.

"""

import os
import sys
import errno
import itertools
import math
import datetime

# Use absolute imports here due to load order
from scrollpy.config._config import config


def file_exists(file_path):
    """Checks whether a file exists.

    Args:
        file_path (str): Full path to the file to check.

    Returns:
        True if the file exists; False otherwise.

    """
    if os.path.isfile(file_path):  # Specifically a FILE
        return True
    return False


def dir_exists(dir_path):
    """Checks whether a directory exists.

    Args:
        dir_path (str): Full path to the directory to check.

    Returns:
        True if the directory exists; False otherwise.

    """
    if os.path.isdir(dir_path):  # Specifically a DIR
        return True
    return False


def ensure_dir_exists(dir_path):
    """Given a path, try to make it.

    Args:
        dir_path (str): Full path to the directory to make.

    Raises:
        OSError: directory already exists or creation failed.

    """
    try:
        os.makedirs(dir_path)
    except OSError as e:
        if e.errno == errno.EEXIST:  # code 17; exists already
            if not os.path.isdir(dir_path):  # Somehow, is a file
                raise
        else:
            raise  # re-raise on any other kind of error


def is_value_ok_with_path(value):
    """Very simple check to make sure a value does not have path chars.

    Idea is that any path characters in a created filename may result in
    creation of unwanted directories and misplaced output files.

    Args:
        value (str): Value (could be a filename, path, or other type of
            value) to check.

    Returns:
        bool: True if path separator is not in the value; False
            otherwise.

    """
    if os.sep in value:
        return False
    return True


def make_ok_with_path(value):
    """Removes all instances of a disallowed character.

    Args:
        value (str): Values to be sanitized.

    Returns:
        str: A copy of the input value with all instance of the path
            character replaced with nothing.

    """
    return value.replace(os.sep,"")


def path_is_name_only(file_path):
    """Checks whether a path represents a dir or file only.

    In order for users to specify shorthand paths to subdirectories,
    check input values for target directories to determine if they
    represent full filepaths or just a single name, either with or
    without a trailing path separation character.

    Args:
        file_path (str): Provided filepath.

    Returns:
        bool: True if filepath represents only a single name; False
            if filepath is a full path.

    """
    if not file_path:  # May be passed as None
        return False
    file_path = file_path.lstrip(os.sep)  # Remove possible leading char
    # Otherwise actually check
    dirs,files = os.path.split(file_path)  # 2-length tuple
    if dirs == '':  # Empty string
        num_dirs = 0
    else:
        num_dirs = len(dirs.split(os.sep))  # os.sep is platform-specific
    if files == '':
        num_files = 0
    else:
        num_files = 1  # Only ever 0 or 1 file
    # Now check three possibilities
    if num_dirs == 0:  # E.g. 'outdir'
        return True
    elif num_dirs == 1 and num_files == 0:  # E.g. 'outdir/'
        return True
    return False  # Every other option is a full path


def get_filepath(outdir, name, filetype, **kwargs):
    """General use function to return a filepath based on input.

    Called throughout ScrollPy to retrieve a name of an expected output
    file, and ensure that the filepath is unique. Output directories
    are assumed to exist following initial program argument checking.

    Args:
        outdir (str): The target directory to output the file to.
        name (str): A basename for the output file.
        filetype (str): The general type of output file expected.
        **kwargs: Optional keyword arguments to hold additional filename
            information.

    Returns:
        str: The full path to the desired output file.

    """
    # Whether or not to overwrite identical filenames
    no_clobber = bool(config['ARGS']['no_clobber'])
    # Initial filename from function
    _filename = get_filename(name, **kwargs)
    _extension = get_file_extension(filetype, **kwargs)
    filename = _filename + _extension
    # Check to make sure there are no path chars
    if not is_value_ok_with_path(filename):
        filename = make_ok_with_path(filename)
    # Join to make full outpath
    _filepath = os.path.join(outdir, filename)
    # Check if ok -> change name/overwrite if existing file
    if file_exists(_filepath):
        if no_clobber:  # Do not overwrite
            filepath = get_nonredundant_filepath(
                    outdir,
                    filename,
                    )
        else:  # Intend to overwrite, remove file first
            try:
                os.remove(_filepath)
            except OSError:
                pass  # Should not happen
            filepath = _filepath
    else:  # Does not exist
        filepath = _filepath

    return filepath


def get_filename(name, **kwargs):
    """Returns a filename based on input.

    Args:
        name (str): A basename for the output file.
        **kwargs: Optional keyword arguments to hold additional filename
            information.

    Returns:
        str: An output filename.

    """
    # Optional global config values
    filesep = config['ARGS']['filesep']  # Defaults to '_'
    suffix = config['ARGS']['suffix']    # May be None
    try:
        extra = str(kwargs['extra'])  # Expect str only? or list as well?
    # TypeError occurs, for example if suffix is None for some reason
    except (KeyError,TypeError):
        extra = None
    # Add extra, if necessary
    if extra:
        basename = filesep.join((name,extra))
    else:
        basename = name
    # Add suffix, if necessary
    if suffix != '':
        filename = filesep.join((basename,suffix))
    else:
        filename = basename

    return filename


def get_file_extension(filetype, **kwargs):
    """Returns a file extension based on input.

    Uses the input filetype argument to call one of several functions in
    the module to return a file extension. These modules may make use of
    an optional format argument in input kwargs.

    Args:
        filetype (str): The general type of output file expected.
        **kwargs: Optional keyword arguments to hold additional filename
            information.

    Returns:
        str: An output file extension.

    """
    name_function = "get_{}_extension".format(filetype)  # Based on type
    try:
        to_call = globals()[name_function]  # Find in module
    except KeyError:
        raise AttributeError  # Could not find for type
    # Call function to actually get extension
    extension = to_call(**kwargs)

    return extension


def get_sequence_extension(**kwargs):
    """Returns a file extension based on input.

    Args:
        **kwargs: Optional keyword arguments to hold additional
            information.

    Returns:
        str: An output file extension.

    """
    try:
        seqfmt = kwargs['seqfmt']  # Can be specified
    except KeyError:
        seqfmt = config['ARGS']['seqfmt'] # Use global if not
    # Format just controls extension
    if seqfmt == 'fasta':
        extension = '.fa'
    else:
        pass  # TO-DO: Add more!

    return extension


def get_alignment_extension(**kwargs):
    """See documentation for get_sequence_extension()"""
    try:
        alignfmt = kwargs['alignfmt']
    except KeyError:
        alignfmt = config['ARGS']['alignfmt']
    # Format just controls extension
    if alignfmt == 'fasta':
        extension = '.afa'
    elif alignfmt == 'phylip':  # Count phylip as alignment
        extension = '.phy'
    else:
        pass  # TO-DO

    return extension


def get_tree_extension(**kwargs):
    """See documentation for get_sequence_extension()"""
    try:
        treefmt = kwargs['treefmt']
    except KeyError:
        raise AttributeError
    if treefmt == 'iqtree':
        extension = '.phy.contree'
    else:
        pass  # Make more flexible eventually

    return extension


def get_distance_extension(**kwargs):
    """See documentation for get_sequence_extension()"""
    try:
        distfmt = kwargs['distfmt']
    except KeyError:
        raise AttributeError
    if distfmt == 'raxml':
        extension = ''  # No added extension
    else:
        pass  # Make more flexible eventually

    return extension


def get_column_extension(**kwargs):
    """See documentation for get_sequence_extension()"""
    return '.txt'  # Needs to be more flexible?


def get_table_extension(**kwargs):
    """See documentation for get_sequence_extension()"""
    # Specific global config value
    tblsep = config['ARGS']['tblsep']
    # Obtain file extention by tblsep
    if tblsep == ',':
        extension = '.csv'
    else:
        extension = '.txt' # Need to make more flexible eventually

    return extension


def get_nonredundant_filepath(dir_path, filename, suffix=1):
    """Given a directory and a filename, return a unique filename.

    Args:
        dir_path (str): Full path to the directory.
        filename (str): Name of the file to check.
        suffix (int): Integer value to append to create unique filenames.
            Defaults to 1.

    Returns:
        The full path to a unique filename.

    """
    test_path = os.path.join(dir_path, filename)
    if not os.path.isfile(test_path):
        return test_path  # Base case
    else:
        if suffix == 1:  # First time through
            _filename = filename + '.' + str(suffix)
        else:
            _tmpfile = filename.rsplit('.',1)[0]  # May be other periods
            _filename = _tmpfile + '.' + str(suffix)
        suffix += 1
        return get_nonredundant_filepath(dir_path, _filename, suffix)  # Recur


def check_input_paths(*paths):
    """Checks a series of paths for existence.

    Args:
        *paths (str): One or more (full) paths to check.

    Returns:
        list: A list of non-existent filepaths. May be empty.

    """
    bad_paths = []
    for path in paths:
        if not file_exists(path):
            bad_paths.append(path)
    return bad_paths


def check_duplicate_paths(*paths):
    """Checks a series of paths for duplicates.

    Args:
        *paths (str): One or more (full) paths to check.

    Returns:
        list: A list of duplicate filepaths. May be empty.

    """
    seen = set()
    duplicates = []
    for path in paths:
        if path in seen:
            duplicates.append(path)
        else:
            seen.add(path)
    return duplicates


def non_blank_lines(file_handle):
    """Creates a generator of non-empty lines in a file.

    Args:
        file_handle (str): Full path to the file.

    Yields:
        str: The next non-empty line in the file.
            Empty lines have only carriage returns, e.g. `\n`.

    """
    with open(file_handle,'r') as i:
        for line in i:
            line = line.strip()
            if line: # blank lines are not truthy
                yield line


def modify_model_name(model, program):
    """Modifies the name of an evolutionary model for use in a program.

    Some phylogenetic programs take model inputs in a format that
    requires more than just the model name itself (for example, RAxML
    modifies protein models with `PROTGAMMA` or similar).

    Args:
        model (str): The name of the evolutionary model to modify.
        program (str): The name of the program that will use the model.

    Returns:
        str: The modified model name for use in program call.

    """
    prot_models = ['LG', 'WAG']
    nuc_models = ['GTR','JC69','HKY85']

    if program == 'RAxML':
        if model in prot_models:  # Or use input alphabet variable?!
            return ''.join(('PROTGAMMA',model))
        return 'GTRGAMMA'  # This is true even for other nuc models!


def split_input(string, chunk_size=80):
    """Splits a string into a series of substrings.

    Sometimes writing long strings (like sequences) to output files would
    result in lines that run off a standard terminal window. This splits a
    long string into separate strings of at most a given length. The final
    sub-string is often less than the specified size.

    Args:
        string (str): String to split.
        chunk_size (int): Length of sub-strings to return. Default 80.

    Returns:
        list: A list of strings. If the input string is the same length or
            shorter than chunk_size, the list has only one item. If not,
            the final sub-string is at most chunk_size long.

    """
    num_chunks = len(string)//chunk_size # // floor division to emulate python 2 behaviour
    if (len(string) % chunk_size != 0):
        # This last chunk is not the same size, but string
        # slicing takes care of the details for us
        num_chunks += 1
    output = []
    for i in range(0, num_chunks):
        output.append(string[chunk_size*i:chunk_size*(i+1)])
    return output


def decompose_sets(set_of_tuples, old_set_of_tuples=None, merged=None):
    """Merges sets of tuples based on comparing tuple members.

    Recurisvely flatten tuples within a set by comparing each member of a
    tuple with each member of every other tuple. If the membership test
    passes, the two tuples are merged (ignoring any additional redundant
    members).

    Allows for pairwise comparisons of similarity between all members of a
    large group (for example, sequences in an alignment), to be grouped
    into the largest possible groups in which each member has at least one
    other member that is at least X% similar to each other, depending on
    the functional call used to generate the original pair-wise tuples.

    Args:
        set_of_tuples (set): A set of tuples to process.
        old_set_of_tuples(set): Holds a reference to the previous value
            of set_of_tuples during recursive calls. Default None.
        merged (set): Avoids aggregating redundant new tuples during
            each recursive call. Default None.

    Returns:
        set: The final set of merged tuples. The number of tuples in the
            final set is bounded as 1<n<O, where O is the number of
            tuples in the original set passed as a function argument.

    """
    # Recurred versions or initialize new set
    old_set_of_tuples = old_set_of_tuples if old_set_of_tuples else set()
    merged = merged if merged else set()
    # Basecase 1
    if len(set_of_tuples) == 1:
        return set_of_tuples
    elif set_of_tuples == old_set_of_tuples:
        return set_of_tuples
    else:  # Do some work
        new_set_of_tuples = set()
        for tup1,tup2 in itertools.combinations(
                set_of_tuples,
                2,  # Pairwise combinations
                ):
            merge = False
            for header1,header2 in itertools.product(tup1,tup2):
                if header1 == header2:
                    merge = True
                    break
            if merge:
                new_tup = set()
                for tup in (tup1,tup2):
                    merged.add(tuple(sorted(tup)))  # Sort to avoid redundancy
                    try:
                        new_set_of_tuples.remove(tup)
                    except KeyError:
                        pass  # Not already in new set
                    for item in tup:
                        new_tup.add(item)
                new_set_of_tuples.add(tuple(sorted(new_tup)))
            else:
                for tup in (tup1,tup2):
                    if not tup in merged:
                        new_set_of_tuples.add(tuple(sorted(tup)))
        return decompose_sets(new_set_of_tuples,set_of_tuples,merged)  # Recur


# This could probably be replaced by itertools.chain()
def flatten_dict_to_list(input_dict):
    """Gathers all values from across dictionary keys.

    Args:
        input_dict (dict): A dictionary to flatten.

    Returns:
        list: A list of all values across dictionary keys.

    """
    out_list = []
    for _,v in input_dict.items():
        for item in v:
            out_list.append(item)
    return out_list


def time_list(t_delta):
    """Returns a tuple of time increments from a timedelta object.

    By implementation, datetime.timedelta objects in Python only store
    days, seconds, and microseconds. In order to output total runtime to
    users in a more friendly way, need to convert these values to smaller
    increments (e.g. minutes, hours, etc.).

    Args:
        t_delta (obj): A datetime.timedelta object.

    Returns:
        tuple: A tuple of time increments in order of
            days, hours, minutes, seconds, and microseconds.

    """
    hours = 0
    minutes = 0
    if t_delta.seconds != 0:
        hours,minutes,seconds = calculate_real_time(t_delta)
    else:
        seconds = t_delta.seconds
    # Return everything
    return (t_delta.days,  # Unchanged from input
            hours,
            minutes,
            seconds,  # May be different from input object
            t_delta.microseconds,
            )


def calculate_real_time(t_delta):
    """ Calculates minutes and hours from a timedelta object.

    Args:
        t_delta (obj): A datetime.timedelta object.

    Returns:
        tuple: A tuple of hours, minutes, and seconds.

    """
    seconds = t_delta.seconds
    if seconds <= 59:  # If 60, it would be 1 min
        return (0,0,seconds)  # No larger increments can be made
    else:
        minutes,seconds = _split_time(seconds)
        if minutes <= 59:  # If 60, it would be 1 hour
            return (0,minutes,seconds)
        else:
            hours,minutes = _split_time(minutes)
            return (hours,minutes,seconds)


def _split_time(value, divisible=60):
    """ Splits time values to get a whole and remainder.

    Args:
        value (int): An initial value for the smaller increment.
        divisible (int): The number of smaller increments required to make
            up one larger increment. Default 60.

    Returns:
        tuple: A tuple of whole, remainder increment values.

    """
    d_value = value/divisible  # Create a float no matter what
    remainder,whole = math.modf(d_value)  # Unpack is reverse of expected
    # Remainder is a fraction of the divisible
    true_remainder = round(remainder * divisible)  # Round required!
    return (int(whole),int(true_remainder))  # Return as ints

