"""
This module contains code for implementing a single global object for
counting ScrollSeq/LeafSeq ID numbers. In order to ensure each ID number
is unique, need to be able to store Class attribute count data across
multiple instances of a class.
"""


class Counter:
    """
    Presents a Singleton-like interface for global counting. As many
    instances as want can spawn and be tied to a single global class
    attribute.

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
        Counter.__count += 1


    def current_count(self):
        """Returns current value"""
        return Counter.__count

