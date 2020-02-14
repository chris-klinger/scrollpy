"""
Tests functions in the 'tree_file.py' module
"""

import os
import unittest
from unittest.mock import Mock
from unittest.mock import patch
import warnings

from ete3.parser.newick import NewickError

from scrollpy.files import tree_file
from scrollpy.util._exceptions import FatalScrollPyError


# Relative path access to test data
cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
data_dir = os.path.join(cur_dir, '../../fixtures/') #/tests/fixtures/


class TestReadNewickTree(unittest.TestCase):
    """Tests '_read_newick_tree' function"""

    def test_load_newick_file(self):
        """Tests that parsing a real newick file works"""
        test_tree_file = os.path.join(data_dir,'Hsap_AP_EGADEZ.mfa.contree')
        with warnings.catch_warnings():  # Parser raises warnings in unit testing
            warnings.simplefilter("ignore")
            tree = tree_file._read_newick_tree(test_tree_file)
        self.assertNotEqual(tree,None)  # There is an object

    @patch('scrollpy.files.tree_file.file_logger')
    @patch('scrollpy.files.tree_file.console_logger')
    @patch('scrollpy.util._logging.BraceMessage')
    @patch('scrollpy.util._logging.log_message')
    @patch('scrollpy.files.tree_file._read_newick_tree')
    def test_read_tree(self, mock_readnew, mock_log, mock_bmsg,
            mock_cl, mock_fl):
        """Explicitly tests the read_tree function"""
        mock_bmsg.return_value = "Mock Message"
        # Test when reading raises an error
        mock_readnew.side_effect = NewickError('inpath')
        with self.assertRaises(FatalScrollPyError):
            tree_file.read_tree('inpath', 'newick')
        mock_bmsg.assert_any_call(
                "Trying to read Newick file {}", 'inpath')
        mock_bmsg.assert_any_call(
                "Could not read Newick file {}", 'inpath')
        mock_log.assert_any_call(
                "Mock Message",
                2,
                'INFO',
                mock_fl,
                )
        mock_log.assert_any_call(
                "Mock Message",
                1,
                'ERROR',
                mock_cl, mock_fl,
                )
        # Test when no error is raised
        # mock_readnew.return_value = 'Tree Obj'
        mock_readnew.side_effect = None
        mock_readnew.return_value = "Tree Object"
        self.assertEqual(
                tree_file.read_tree('inpath', 'newick'),
                'Tree Object',
                )


if __name__ == '__main__':
    unittest.main()
