"""
Tests scrollpy.util._util.py

"""

import os
import unittest
import datetime
from unittest.mock import Mock
from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import mock_open

from scrollpy import config, load_config_file
from scrollpy.util import _util as scroll_util


cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
# cleaner to use realpath due to relative path
data_dir = os.path.realpath(os.path.join(cur_dir, '../../fixtures')) # /tests/


class TestUtil(unittest.TestCase):
    """Tests util's standalone functions"""

    @patch('scrollpy.util._util.os.path')
    def test_file_exists(self, mock_path):
        """Tests file_exists function"""
        # Tests when path is not a file
        mock_path.isfile.return_value = False
        self.assertFalse(scroll_util.file_exists(""))
        # Tests when path is a file
        mock_path.isfile.return_value = True
        self.assertTrue(scroll_util.file_exists(""))

    @patch('scrollpy.util._util.os.makedirs')
    def test_ensure_dir_exists_good(self, mock_mkdirs):
        """Tests that ensure_dir_exists normally works"""
        mock_mkdirs.return_value = None
        scroll_util.ensure_dir_exists("fake_dir")
        mock_mkdirs.assert_called_once_with("fake_dir")

    @patch('scrollpy.util._util.os.path')
    @patch('scrollpy.util._util.os.makedirs')
    def test_ensure_dir_exists_bad(self, mock_mkdirs, mock_path):
        """Tests that ensure_dir_exists throws OSErrors as expected"""
        e1 = OSError(17, 'EEXIST')  # Code 17, file exists
        e2 = OSError(17, 'EEXIST')  # Code 17, file exists
        e3 = OSError(1,  'EPERM')   # Code 1, operation not permitted
        mock_mkdirs.side_effect = [e1, e2, e3]
        # Test when os.path.isdir() is False -> is a file
        mock_path.isdir.return_value = False
        with self.assertRaises(OSError):
            scroll_util.ensure_dir_exists("non-existent_dir")
        # Test when os.path.isdir() is True -> is a dir
        mock_path.isdir.return_value = True
        self.assertEqual(None,  # Expect no Exception; func returns None
                scroll_util.ensure_dir_exists("non-existent_dir"))
        # Test an errno other than 17 -> should raise
        with self.assertRaises(OSError):
            scroll_util.ensure_dir_exists("non-existent_dir")

    @patch('scrollpy.util._util.os')
    def test_is_value_ok_with_path_badvalue(self, mock_os):
        """Tests that bad chars are reported"""
        # Base sep value
        mock_os.sep = '/'
        self.assertFalse(scroll_util.is_value_ok_with_path('bad/name'))
        # Good sep value
        mock_os.sep = '\\'
        self.assertTrue(scroll_util.is_value_ok_with_path('bad/name'))

    def test_path_is_name_only(self):
        """Tests the path_is_name_only function"""
        # Simplest case -> path is None
        self.assertFalse(scroll_util.path_is_name_only(None))
        # Test with no path char
        test_path1 = "somefile.txt"
        self.assertTrue(scroll_util.path_is_name_only(test_path1))
        # Test with leading path char
        test_path2 = "{}somefile.txt".format(os.sep)
        self.assertTrue(scroll_util.path_is_name_only(test_path2))
        # Test with trailing path char
        test_path3 = "somename{}".format(os.sep)
        self.assertTrue(scroll_util.path_is_name_only(test_path3))
        # Test a more full path
        test_path4 = os.sep.join(('dir','path','filename.txt'))
        self.assertFalse(scroll_util.path_is_name_only(test_path4))

    @patch('scrollpy.util._util.get_nonredundant_filepath')
    @patch('scrollpy.util._util.file_exists')
    @patch('scrollpy.util._util.os')
    @patch('scrollpy.util._util.make_ok_with_path')
    @patch('scrollpy.util._util.is_value_ok_with_path')
    @patch('scrollpy.util._util.get_file_extension')
    @patch('scrollpy.util._util.get_filename')
    @patch('scrollpy.util._util.config')
    def test_get_filepath(self, mock_config, mock_fname, mock_fext, mock_isok,
            mock_makeok, mock_os, mock_file_exists, mock_nrpath):
        """Tests the get_filepath function"""
        # Some starting defaults
        # Set __getitem__ to mimic [] indexing
        mock_config.__getitem__.return_value = {'no_clobber':True}
        mock_fname.return_value = "somefile"
        mock_fext.return_value = ".txt"
        # Simple case, file does not already exist
        mock_isok.return_value = True
        mock_os.path.join.return_value = "dir1/somefile.txt"
        mock_file_exists.return_value = False
        self.assertEqual(
                scroll_util.get_filepath('dir1', 'somefile', 'fasta'),
                'dir1/somefile.txt',
                )
        # Simple case, but pretend filename is not ok
        mock_isok.return_value = False
        mock_makeok.return_value = 'somefile.txt'
        self.assertEqual(  # Return value does not change
                scroll_util.get_filepath('dir1', 'somefile', 'fasta'),
                'dir1/somefile.txt',
                )
        mock_makeok.assert_called_once_with('somefile.txt')  # But this is called
        # More complicated -> file exists already
        # Tests assuming no_clobber is set
        mock_isok.return_value = True  # Skip this block again
        mock_file_exists.return_value = True  # File exists now
        mock_nrpath.return_value = 'dir1/non_redundant_path.txt'
        self.assertEqual(
                scroll_util.get_filepath('dir1', 'somefile', 'fasta'),
                'dir1/non_redundant_path.txt',
                )
        # Now pretend no_clobber is not set -> check os.remove is called
        mock_config['ARGS']['no_clobber'] = False
        mock_os.remove.return_value = None  # Doesn't matter
        self.assertEqual(  # Return value does not change
                scroll_util.get_filepath('dir1', 'somefile', 'fasta'),
                'dir1/somefile.txt',
                )
        mock_os.remove.assert_called_once_with('dir1/somefile.txt')

    @patch('scrollpy.util._util.config')
    def test_get_filename(self, mock_config):
        """Tests the get_filename function"""
        # Some starting defaults
        # Set __getitem__ to mimic [] indexing
        mock_config.__getitem__.return_value = {
                'filesep' : '_',
                'suffix' : 'suffix',
                }
        # Test with both a valid <extra> and <suffix>
        self.assertEqual(
                scroll_util.get_filename('basename', extra='extra'),
                'basename_extra_suffix',
                )
        # Test with no <extra>
        self.assertEqual(
                scroll_util.get_filename('basename'),
                'basename_suffix',
                )
        # Test with no <suffix>
        mock_config.__getitem__.return_value = {
                'filesep' : '_',
                'suffix' : '',  # Default
                }
        self.assertEqual(
                scroll_util.get_filename('basename', extra='extra'),
                'basename_extra',
                )
        # Test with no <extra> or <suffix>
        self.assertEqual(
                scroll_util.get_filename('basename'),
                'basename',
                )

    @patch('scrollpy.util._util.get_table_extension')
    @patch('scrollpy.util._util.get_column_extension')
    @patch('scrollpy.util._util.get_distance_extension')
    @patch('scrollpy.util._util.get_tree_extension')
    @patch('scrollpy.util._util.get_alignment_extension')
    @patch('scrollpy.util._util.get_sequence_extension')
    def test_get_file_extension(self, mock_s_ext, mock_a_ext, mock_t_ext,
            mock_d_ext, mock_c_ext, mock_b_ext):
        """Tests that get_file_extension farms out calls correctly"""
        # Set return values for all of them
        mock_s_ext.return_value = "sequence_extension"
        mock_a_ext.return_value = "alignment_extension"
        mock_t_ext.return_value = "tree_extension"
        mock_d_ext.return_value = "distance_extension"
        mock_c_ext.return_value = "column_extension"
        mock_b_ext.return_value = "table_extension"
        # Test one at a time
        self.assertEqual(
                scroll_util.get_file_extension("sequence"),
                "sequence_extension",
                )
        self.assertEqual(
                scroll_util.get_file_extension("alignment"),
                "alignment_extension",
                )
        self.assertEqual(
                scroll_util.get_file_extension("tree"),
                "tree_extension",
                )
        self.assertEqual(
                scroll_util.get_file_extension("distance"),
                "distance_extension",
                )
        self.assertEqual(
                scroll_util.get_file_extension("column"),
                "column_extension",
                )
        self.assertEqual(
                scroll_util.get_file_extension("table"),
                "table_extension",
                )
        # Finally, test one that does not exist
        with self.assertRaises(AttributeError):
            scroll_util.get_file_extension("unknown")

    @patch('scrollpy.util._util.config')
    def test_get_sequence_extension(self, mock_config):
        """Tests the get_sequence_extension function"""
        # Test with specifying seqfmt
        self.assertEqual(
                scroll_util.get_sequence_extension(**{'seqfmt':'fasta'}),
                '.fa',
                )
        # Test specifying it in config instead
        mock_config.__getitem__.return_value = {
                'seqfmt' : 'fasta',
                }
        self.assertEqual(
                scroll_util.get_sequence_extension(),
                '.fa',
                )

    @patch('scrollpy.util._util.config')
    def test_get_alignment_extension(self, mock_config):
        """Tests the get_alignment_extension function"""
        # Test with specifying fasta
        self.assertEqual(
                scroll_util.get_alignment_extension(**{'alignfmt':'fasta'}),
                '.afa',
                )
        # Test with specifying phylip
        self.assertEqual(
                scroll_util.get_alignment_extension(**{'alignfmt':'phylip'}),
                '.phy',
                )
        # Test specifying it in config instead
        mock_config.__getitem__.return_value = {
                'alignfmt' : 'fasta',
                }
        self.assertEqual(
                scroll_util.get_alignment_extension(),
                '.afa',
                )

    @patch('scrollpy.util._util.config')
    def test_get_tree_extension(self, mock_config):
        """Tests the get_tree_extension function"""
        # Test with specifying seqfmt
        self.assertEqual(
                scroll_util.get_tree_extension(**{'treefmt':'iqtree'}),
                '.phy.contree',
                )
        # No config value -> raises AttributeError if not specified
        with self.assertRaises(AttributeError):
            scroll_util.get_tree_extension()

    @patch('scrollpy.util._util.config')
    def test_get_distance_extension(self, mock_config):
        """Tests the get_distance_extension function"""
        # Test with specifying seqfmt
        self.assertEqual(
                scroll_util.get_distance_extension(**{'distfmt':'raxml'}),
                '',  # No added extension
                )
        # No config value -> raises AttributeError if not specified
        with self.assertRaises(AttributeError):
            scroll_util.get_distance_extension()

    def test_get_column_extension(self):
        """Tests get_column_extension method, just returns"""
        self.assertEqual(scroll_util.get_column_extension(), '.txt')

    @patch('scrollpy.util._util.config')
    def test_get_table_extension(self, mock_config):
        """Tests the get_distance_extension function"""
        # Ignores kwargs, just uses config
        # Only two options, '.csv' or '.txt'
        mock_config.__getitem__.return_value = {'tblsep' : ','}
        self.assertEqual(scroll_util.get_table_extension(), '.csv')
        # Only two options, '.csv' or '.txt'
        mock_config.__getitem__.return_value = {'tblsep' : '\t'}
        self.assertEqual(scroll_util.get_table_extension(), '.txt')

    @patch('scrollpy.util._util.os.path.isfile')
    def test_get_nonredundant_filepath(self, mock_isfile):
        """Tests the get_nonredundant_filepath function"""
        # Simple case, file does not exit
        mock_isfile.side_effect = (False,)
        self.assertEqual(
                scroll_util.get_nonredundant_filepath(
                    'dir1', 'filename.txt',),
                os.path.join('dir1','filename.txt'))
        # Check when the filepath is redundant
        mock_isfile.side_effect = (True, False)
        self.assertEqual(
                scroll_util.get_nonredundant_filepath(
                    'dir1', 'filename.txt',),
                os.path.join('dir1','filename.txt.1'))
        # Check when the filepath is redundant twice
        mock_isfile.side_effect = (True, True, False)
        self.assertEqual(
                scroll_util.get_nonredundant_filepath(
                    'dir1', 'filename.txt',),
                os.path.join('dir1','filename.txt.2'))

    @patch('scrollpy.util._util.file_exists')
    def test_check_input_paths(self, mock_exists):
        """Tests the check_input_paths function"""
        # Check with all good paths
        mock_exists.side_effect = (True,)
        self.assertEqual(len(scroll_util.check_input_paths('_')),0)
        # Check with all bad paths
        mock_exists.side_effect = (False, False, False)
        self.assertEqual(len(scroll_util.check_input_paths(
            '_', '_', '_')), 3)

    def test_check_duplicate_paths(self):
        """Tests the check_duplicate_paths function"""
        # Check with no duplicates
        self.assertEqual(
                len(scroll_util.check_duplicate_paths(
                    'file_path1',
                    'file_path2',
                    'file_path3',
                    'file_path4',
                    )), 0)
        # Check with two duplicate paths, one each
        self.assertEqual(
                len(scroll_util.check_duplicate_paths(
                    'file_path1',
                    'file_path1',
                    'file_path2',
                    'file_path2',
                    )), 2)
        # Check with one duplicate path, two instances
        self.assertEqual(
                len(scroll_util.check_duplicate_paths(
                    'file_path1',
                    'file_path1',
                    'file_path1',
                    'file_path4',
                    )), 2)

    def test_non_blank_lines(self):
        """Tests iterator of non-blank lines"""
        # Just make sure it only returns real lines
        data = "line1\n\nline2\nsome_other_line\n\n"
        with patch('__main__.open', mock_open()):
            with open('test_mock_file','w') as tf:
                tf.write(data)
        self.assertEqual(
                list(scroll_util.non_blank_lines('test_mock_file')),
                ['line1','line2','some_other_line'],
                )

    def test_modify_model_name(self):
        """Tests the modify_model_name function"""
        self.assertEqual(
                scroll_util.modify_model_name('LG', 'RAxML'),
                'PROTGAMMALG',
                )

    def test_split_input(self):
        """Tests the split_input function"""
        # Need to make a test string
        line1 = '*'*80  # Default line size is 80
        line2 = '^'*40
        test_str = line1 + line2
        expected_list = [line1, line2]
        self.assertEqual(
                scroll_util.split_input(test_str),
                expected_list,
                )

    def test_decompose_sets(self):
        """Tests the decompose_sets function"""
        # Simplest way to test the function is just whether it works
        # Test case 1, not all will merge
        test_set1 = set()
        test_set1.add(('tup1','tup2'))
        test_set1.add(('tup1','tup3'))
        test_set1.add(('tup4','tup5'))  # This won't merge
        expected_set1 = {('tup1','tup2','tup3'),('tup4','tup5')}
        self.assertEqual(
                scroll_util.decompose_sets(test_set1),
                expected_set1,
                )
        test_set2 = set()
        test_set2.add(('tup1','tup2'))
        test_set2.add(('tup3','tup4'))
        test_set2.add(('tup1','tup5'))
        test_set2.add(('tup2','tup3'))
        test_set2.add(('tup3','tup6'))  # These should all merge
        expected_set2 = {('tup1','tup2','tup3','tup4','tup5','tup6')}
        self.assertEqual(
                scroll_util.decompose_sets(test_set2),
                expected_set2,
                )

    def test_flatten_dict_to_list(self):
        """Tests the flatten_dict_to_list function"""
        test_dict = {
                'k1': ['v1','v2','v3'],
                'k2': ['v4','v5'],
                }
        self.assertEqual(
                sorted(scroll_util.flatten_dict_to_list(test_dict)),  # Sorted
                ['v1', 'v2', 'v3', 'v4', 'v5'],
                )

    @patch('scrollpy.util._util.calculate_real_time')
    def test_time_list(self, mock_calc):
        """Tests the time_list function"""
        mock_tdelt = Mock()
        mock_tdelt.configure_mock(**{
            'days':0,
            'hours':1,
            'minutes':20,
            'seconds':40,
            'microseconds':30,
            })
        mock_calc.return_value = (1,20,40)
        self.assertEqual(scroll_util.time_list(mock_tdelt),
                (0, 1, 20, 40, 30),  # Days, hours, minutes, seconds, microseconds
                )

    def test_calculare_real_time(self):
        """Tests the calculate_real_time function"""
        # First test case, less and 1 min
        mock_tdelt = Mock(seconds=42)
        self.assertEqual(
                scroll_util.calculate_real_time(mock_tdelt),
                (0, 0, 42),  # Hours, minutes, seconds
                )
        # Second test case, 1 min exactly
        mock_tdelt = Mock(seconds=60)
        self.assertEqual(
                scroll_util.calculate_real_time(mock_tdelt),
                (0, 1, 0),  # Hours, minutes, seconds
                )
        # Last test case, hours, mins, and seconds
        mock_tdelt = Mock(seconds=4000)
        self.assertEqual(
                scroll_util.calculate_real_time(mock_tdelt),
                (1, 6, 40),  # Hours, minutes, seconds
                )


    def test_split_time(self):
        """Tests the _spit_time function"""
        # First test case, dividing 60 should give 1
        self.assertEqual(
                scroll_util._split_time(60),
                (1, 0),  # I.e. 60 secs is 1 min
                )
        # Second test case, a minute and a half
        self.assertEqual(
                scroll_util._split_time(90),
                (1, 30),
                )
        # Check 1 min and 59 seconds
        self.assertEqual(
                scroll_util._split_time(119),
                (1, 59),
                )
