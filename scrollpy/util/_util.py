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
        """For a given path, checks whether it is a file"""
        if os.path.isfile(file_path):
            return True
        return False
