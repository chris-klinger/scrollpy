"""
Module to hold utility functions.
"""

import os
import sys
import errno


def file_exists_user_spec(file_path):
    """If a file already exists that would be created, should warn the user
    and give them the option to either delete the old file or keep it.

    Alternatively, if the file exists, could just quit instead?

    For now, provide all the options?
    """
    good_input = False
    while not good_input:
        spec = input("Target file {} exists; overwrite? (y/Y/n/N/q/Q) --> ".format(
            file_path))
        spec = spec.strip() # Remove all whitespace
        if spec in ('y','Y','n','N','q','Q'):
            break
    if spec in ('q','Q'): # Exit requested, do immediately
        sys.exit("Quit execution; {} exists".format(file_path))
    return spec # Otherwise, let caller decide what to do


def file_exists(file_path):
    """Checks whether a file exists

    Args:
        file_path (str): Full path to file to check

    Returns:
        True if file exists; False otherwise
    """
    if os.path.isfile(file_path):  # Specifically a FILE
        return True
    return False


def dir_exists(dir_path):
    """Checks whether a directory exists

    Args:
        dir_path (str): Full path to dir to check

    Returns:
        True if dir exists; False otherwise
    """
    if os.path.isdir():  # Specifically a DIR
        return True
    return False


def ensure_dir_exists(dir_path):
    """Given a path, try to make it; quit execution if not possible.

    Args:
        dir_path (str): Full path to directory to make

    Returns:
        None; may raise OSError
    """
    try:
        os.makedirs(dir_path)
    except OSError as e:
        if e.errno == errno.EEXIST:  # code 17; exists already
            if not os.path.isdir(dir_path):  # Somehow, is a file
                raise
        else:
            raise  # re-raise on any other kind of error


def get_nonredundant_filepath(dir_path, filename, suffix=1):
    """Given a directory and a filename, return a unique filename.

    Args:
        dir_path (str): full path to the directory

        filename (str): name of file to check

        suffix (int): integer value to append to create unique filenames

    Returns:
        Full path to unique filename
    """
    test_path = os.path.join(dir_path, filename)
    if not os.path.isfile(test_path):
        return test_path  # Base case
    else:
        if suffix == 1:  # First time through
            _filename = filename + '.' + str(suffix)
        else:
            _filename = filename.split('.',1)[0]  # May be other periods
            _filename = filename + '.' + str(suffix)
        suffix += 1
        return get_nonredundant_filepath(dir_path, _filename, suffix)  # Recur


def check_input_paths(*paths):
    """Checks a series of paths for existence.

    Args:
        *paths (str): One or more (full) paths to check

    Returns:
        (Possibly empty) list of non-existent filepaths
    """
    bad_paths = []
    for path in paths:
        if not file_exists(path):
            bad_paths.append(path)
    return bad_paths


def check_duplicate_paths(*paths):
    """Checks a series of paths for duplicates.

    Args:
        *paths (str): One or more (full) paths to check

    Returns:
        (Possibly empty) list of duplicate filepaths
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
    """Function to generate lines with characters.

    Args:
        file_handle (str): Path to file (not open file object)

    Returns:
        iterator of all lines that are not '\n'.
    """
    with open(file_handle,'r') as i:
        for line in i:
            if line: # blank lines are not truthy
                yield line


def split_input(string, chunk_size=80):
    """Splits a string into a series of substrings.

    Args:
        string (str): String to split
        chunk_size (int): Length of sub-strings to return. Returns the
            original string if greater than the strings length. If not,
            the final sub-string is at most chunk_size long. Default:80.

    Returns:
        A list of sub-strings.
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

