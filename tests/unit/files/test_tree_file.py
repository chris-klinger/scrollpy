"""
Tests functions in the 'tree_file.py' module
"""

import os
import unittest
import warnings

from scrollpy.files import tree_file


# Relative path access to test data
cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
data_dir = os.path.join(cur_dir, '../../fixtures/') #/tests/fixtures/


class TestReadNewickTree(unittest.TestCase):
    """Tests '_read_newick_tree' function"""

    def test_load_newick_file(self):
        """Tests that parsing a newick file works"""
        test_tree_file = os.path.join(data_dir,'Hsap_AP_EGADEZ.mfa.contree')
        with warnings.catch_warnings():  # Parser raises warnings in unit testing
            warnings.simplefilter("ignore")
            tree = tree_file._read_newick_tree(test_tree_file)
        self.assertNotEqual(tree,None)  # There is an object


if __name__ == '__main__':
    unittest.main()
