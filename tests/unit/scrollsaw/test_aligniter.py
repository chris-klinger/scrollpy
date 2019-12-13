"""
Tests the scrollsaw/_aligniter module.
"""

import os
import unittest
import shutil
from configparser import DuplicateSectionError

from Bio import AlignIO

from scrollpy import config
from scrollpy import load_config_file
from scrollpy.scrollsaw._aligniter import AlignIter
from scrollpy.alignments import parser


cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
# cleaner to use realpath due to relative path
data_dir = os.path.realpath(os.path.join(cur_dir, '../../fixtures')) # /tests/


class TestAlignIter(unittest.TestCase):
    """Tests using a small alignment"""

    @classmethod
    def setUpClass(cls):
        """Load sensible config variables"""
        load_config_file()
        try:
            config.add_section('ARGS')
        except DuplicateSectionError:
            pass
        # Provide defaults
        config['ARGS']['alignfmt'] = 'fasta'
        config['ARGS']['col_method'] = 'zorro'
        config['ARGS']['iter_method'] = 'hist'
        config['ARGS']['tree_method'] = 'Iqtree'
        config['ARGS']['tree_matrix'] = 'LG'

        # Get tmpdir
        cls.tmpdir = os.path.join(data_dir,'align_tmp')
        try:
            os.makedirs(cls.tmpdir)
        except FileExistsError:
            pass
        # Specify file
        cls.alignment = os.path.join(
                data_dir,
                'Hsap_AP_EGADEZ.mfa',
                )


    def setUp(self):
        """Create identical instance for each test"""
        self.iter = AlignIter(
                self.alignment,
                self.tmpdir,
                )


    @classmethod
    def tearDownClass(cls):
        """Remove directory"""
        pass


    def test_get_optimal_alignment(self):
        """Checks instance lookup"""
        self.iter._optimal_alignment = "Optimal"
        self.assertEqual("Optimal",
                self.iter.get_optimal_alignment())


    def test_parse_alignment(self):
        """Tests parsing alignment"""
        # Run and check
        self.iter._parse_alignment()
        self.assertEqual(len(self.iter._align_obj),5)  # Num rows
        align_length = len(self.iter._align_obj[0])
        self.assertEqual(align_length,1372)  # Num columns


    def test_get_outpath(self):
        """Tests get_outpath method"""
        # Expected file names
        expected_column_name = 'Hsap_AP_EGADEZ_columns.txt'
        expected_phy_name    = 'Hsap_AP_EGADEZ_100.phy'
        expected_tree_name   = 'Hsap_AP_EGADEZ_100.phy.contree'
        # Run tests
        # Column name first; simple
        expected_column_path = os.path.join(
                self.tmpdir,
                expected_column_name,
                )
        self.assertEqual(self.iter._get_outpath('columns'),
                expected_column_path)
        # For other names, assume length is 100
        # Phylip next
        expected_phy_path = os.path.join(
                self.tmpdir,
                expected_phy_name,
                )
        self.assertEqual(self.iter._get_outpath('phylip',100),
                expected_phy_path)
        # Tree last
        expected_tree_path = os.path.join(
                self.tmpdir,
                expected_tree_name,
                )
        self.assertEqual(self.iter._get_outpath('tree',100),
                expected_tree_path)


    def test_calculate_columns(self):
        """Tests calculating columns"""
        column_path = self.iter._get_outpath('columns')
        if not os.path.exists(column_path):
            # Actually calculate columns
            self.iter._calculate_columns(column_path)
        # Easiest test, size of file > 0
        file_size = os.stat(column_path).st_size
        self.assertTrue(file_size > 0)


    def test_evaluate_columns(self):
        """Tests evaluating calculated columns"""
        column_path = self.iter._get_outpath('columns')
        if not os.path.exists(column_path):
            # Actually calculate columns
            self.iter._calculate_columns(column_path)
        columns = []
        with open(column_path,'r') as i:
            for i,line in enumerate(i.readlines()):
                line = line.strip('\n')
                val = float(line)
                columns.append([i,val])
        columns = sorted(
                columns,
                key=lambda x:x[1],
                )
        # Run instance method -> populate iter._columns
        self.iter._evaluate_columns(column_path)
        # Test
        self.assertEqual(columns,self.iter._columns)


    def test_calculate_num_columns(self):
        """Tests calculating works"""
        # Populate necessary instance values
        self.iter._parse_alignment()
        # May have to calculate columns
        column_path = self.iter._get_outpath('columns')
        if not os.path.exists(column_path):
            self.iter._calculate_columns(column_path)
        self.iter._evaluate_columns(column_path)
        # FINALLY calculate
        num_columns = self.iter._calculate_num_columns()
        self.assertEqual(num_columns,531)


    def test_remove_cols_from_align(self):
        """Test removing a series of indices from alignment object"""
        # Populate necessary instance values
        self.iter._parse_alignment()
        start_align = self.iter._align_obj
        orig_len = len(start_align[0])-1
        # Try to remove
        test_indices = [0, 10, 1371]
        self.iter._remove_cols_from_align(test_indices)
        # Need to test that each one is equal to the one after
        # It in the original alignment
        for i,index in enumerate(test_indices):
            adj = i+1
            start_col = start_align[:,index]
            if index == orig_len:  # Removed last value
                adj_col = start_align[:,index-1]  # Second last value
                new_col = self.iter._align_obj[:,-1]  # New last value
            else:
                adj_index = index+adj
                adj_col = start_align[:,adj_index]
                new_col = self.iter._align_obj[:,index]
            self.assertEqual(adj_col,new_col)


    def test_remove_cols_from_align(self):
        """Tests when the values are grouped at beginning/end"""
        # Populate necessary instance values
        self.iter._parse_alignment()
        start_align = self.iter._align_obj
        orig_len = len(start_align[0])-1
        # Try to remove
        test_indices = [0, 1, 2, 3, 4, 1368, 1369, 1370, 1371]
        self.iter._remove_cols_from_align(test_indices)
        # Compare sequences
        adj = start_align[:, 5:1368]
        for s1,s2 in zip(adj,self.iter._align_obj):
            # SeqRecords can't be directly compared
            # Compare .seq attrs instead
            self.assertEqual(s1.seq,s2.seq)


    def test_shift_cols(self):
        """Tests that column shifting works as expected"""
        # Mock some values
        self.iter._columns = [
                [0,'a'] , [1,'b'] , [3,'d']  , # Removed at 2
                [4,'e'] , [6,'g'] , [8,'i']  , # Removed at 5 and 7
                [10,'k'], [11,'l'], [12,'m'] , # Removed at 9
                ]
        indices = [9,7,2,5]  # Unsorted indices
        # Call method
        self.iter._shift_cols(indices)
        # Check values
        expected = [
                [0, 'a'], [1, 'b'], [2, 'd'],
                [3, 'e'], [4, 'g'], [5, 'i'],
                [6, 'k'], [7, 'l'], [8, 'm'],
                ]
        self.assertEqual(self.iter._columns,expected)


    def test_write_current_alignment(self):
        """Tests making tree"""
        # Populate necessary instance values
        self.iter._parse_alignment()
        column_path = self.iter._get_outpath('columns')
        if not os.path.exists(column_path):
            self.iter._calculate_columns(column_path)
        self.iter._evaluate_columns(column_path)
        self.iter._get_current_outpaths()
        # Write Alignment
        self.iter._write_current_alignment()
        # Now parse again
        new_obj = parser.parse_alignment_file(
                self.iter._current_phy_path,
                'phylip-relaxed',
                to_dict=False,
                )
        self.assertEqual(len(new_obj),5)


    @unittest.skip('For time')
    def test_make_tree(self):
        """Tests making tree"""
        # Populate necessary instance values
        self.iter._parse_alignment()
        column_path = self.iter._get_outpath('columns')
        if not os.path.exists(column_path):
            self.iter._calculate_columns(column_path)
        self.iter._evaluate_columns(column_path)
        self.iter._get_current_outpaths()
        # Write Alignment, if not exists
        if not os.path.exists(self.iter._current_phy_path):
            self.iter._write_current_alignment()
        # Make tree
        self.iter._make_tree()
        # Check file is not empty
        file_size = os.stat(
                self.iter._current_tree_path).st_size
        self.assertTrue(file_size > 0)


    def test_parse_tree(self):
        """Tests parsing tree"""
        self.iter._parse_alignment()
        self.iter._get_current_outpaths()
        # Write Alignment, if not exists
        if not os.path.exists(self.iter._current_phy_path):
            self.iter._write_current_alignment()
        # Make tree, if not exists
        if not os.path.exists(self.iter._current_tree_path):
            self.iter._make_tree()
        # Now parse it
        self.iter._parse_tree()
        # Check values
        leaves = [leaf for leaf in self.iter._current_tree_obj]
        self.assertEqual(len(leaves),5)


    def test_calculate_support(self):
        """Tests calculating  support"""
        self.iter._parse_alignment()
        self.iter._get_current_outpaths()
        # Write Alignment, if not exists
        if not os.path.exists(self.iter._current_phy_path):
            self.iter._write_current_alignment()
        # Make tree, if not exists
        if not os.path.exists(self.iter._current_tree_path):
            self.iter._make_tree()
        # Now parse it
        self.iter._parse_tree()
        # Calc the values
        self.iter._calculate_support()
        self.assertEqual(self.iter._current_support,136)


    def test_is_optimal(self):
        """Tests calculating optimal"""
        self.iter._all_supports = [100]
        self.assertFalse(self.iter._is_optimal())


    def test_evaluate_info(self):
        """Tests adding extra information to iter_info"""
        self.iter.iter_info = [
                [1,'_','_',40],
                [2,'_','_',30],
                [3,'_','_',90],
                [4,'_','_',40],
                [5,'_','_',10],
                ]
        # Run method
        self.iter._evaluate_info()
        expected_info = [
                [1,'_','_',40,"Sub-optimal"],
                [2,'_','_',30,"Sub-optimal"],
                [3,'_','_',90,"Optimal"],
                [4,'_','_',40,"Sub-optimal"],
                [5,'_','_',10,"Sub-optimal"],
                ]
        self.assertEqual(expected_info,
                self.iter.iter_info)
