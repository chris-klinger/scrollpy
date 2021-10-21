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
This module contains code for performing alignments within scrollpy without
relying on external code.

A simple binary comparison function is provided in this module; actual
substitution matrices are provided in /util/_matrices.
"""

import sys

import numpy as np


def create_affine_matrices(seq1, seq2, score_func, gap_open, gap_extend):
    """Creates underlying matrices for affine alignment"""
    # First, make zero-based matrices
    X = np.zeros(shape=(len(seq2) + 1,len(seq1) + 1))
    Y = np.zeros(shape=(len(seq2) + 1,len(seq1) + 1))
    M = np.zeros(shape=(len(seq2) + 1,len(seq1) + 1))
    # Build each
    # All insertions in one sequence
    for i in range(1, len(seq2) + 1):
        X[i,0] = -float("inf")  # Infinity
        Y[i,0] = gap_open + (i * gap_extend)
        M[i,0] = -float("inf")
    # All insertions in the other sequence
    for j in range(1, len(seq1) + 1):
        X[0,j] = gap_open + (j * gap_extend)
        Y[0,j] = -float("inf")
        M[0,j] = -float("inf")
    # Calculate actual match states
    for j in range(1, len(seq1) + 1):
        for i in range(1, len(seq2) + 1):
            X[i,j] = max((gap_open + gap_extend + M[i,j-1]), # Match plus gap
                        (gap_extend + X[i,j-1]), # Continue a gap
                        (gap_open + gap_extend + Y[i,j-1])) # Start a gap
            Y[i,j] = max((gap_open + gap_extend + M[i-1,j]),
                        (gap_open + gap_extend + X[i-1,j]),
                        (gap_extend + Y[i-1,j]))
            M[i,j] = max(score_func(seq2[i-1],seq1[j-1]) +\
                        M[i-1,j-1], X[i,j], Y[i,j]) # A match
    return X,Y,M


def affine_align(seq1, seq2, score_func, gap_open=-11, gap_extend=-1):
    """Perform global pairwise affine alignment"""
    align_seq1 = []
    align_seq2 = []
    # Create matrices
    X,Y,M = create_affine_matrices(
            seq1=seq1,
            seq2=seq2,
            score_func=score_func,
            gap_open=gap_open,
            gap_extend=gap_extend,
            )
    i,j = len(seq2),len(seq1)
    # Find alignment by dynamic programming
    while (i > 0 or j > 0): # Importantly, both need to hit zero!
        # Best score is a match
        if (i > 0 and j > 0 and M[i,j] == M[i-1,j-1] +\
            score_func(seq2[i-1],seq1[j-1])):
            align_seq1.append(seq1[j-1])
            align_seq2.append(seq2[i-1])
            # Decrement both counters
            i -= 1
            j -= 1
        # Gap in seq1
        elif (i > 0 and M[i,j] == Y[i,j]):
            align_seq1.append('-')
            align_seq2.append(seq2[i-1])
            # Decrement seq1 counter only
            i -= 1
        # Gap in seq2
        elif (j > 0 and M[i,j] == X[i,j]):
            align_seq1.append(seq1[j-1])
            align_seq2.append('-')
            # Decrement seq2 counter only
            j -= 1
        # Anything else
        else:
            break
    # Create seqs from lists
    aligned_seq1 = ''.join(reversed(align_seq1))
    aligned_seq2 = ''.join(reversed(align_seq2))
    # Return
    return aligned_seq1, aligned_seq2


def simple_score(r1, r2):
    """Returns 1 if equal, 0 if not"""
    if r1 == r2:
        return 1
    return 0


