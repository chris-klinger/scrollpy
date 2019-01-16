"""
Module to hold utility functions.
"""

import os, sys


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
        if os.path.isfile(file_path):
            return True
        return False


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

