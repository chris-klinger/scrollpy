#!/usr/bin/env python3

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
This module contains code for implementing a single global object for
counting ScrollSeq/LeafSeq ID numbers. In order to ensure each ID number
is unique, need to be able to store Class attribute count data across
multiple instances of a class.
"""

# TO-DO
class ScrollCounter:
    """Presents a Singleton-like interface for global counting.

    As many instances as want can spawn and be tied to a single global
    class attribute. All lookup and update calls are tied to the class
    attribute and so are communicated across instances.

    """

    __count = 1

    def __init__(self):
        pass

    def __repr__(self):
        return "{}".format(self.__class__.__name__)

    def __str__(self):
        return "{}: {}".format(
                self.__class__.__name__,
                self.current_count(),  # Add current value
                )

    def __call__(self):
        """Increments Class counter and returns current value"""
        ScrollCounter.__count += 1


    def current_count(self):
        """Returns current value"""
        return ScrollCounter.__count


    def _reset_count(self):
        """Utility function for testing"""
        ScrollCounter.__count = 1
