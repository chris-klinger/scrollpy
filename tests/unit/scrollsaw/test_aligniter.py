"""
Tests the scrollsaw/_aligniter module.
"""

import os
import unittest
import shutil
from configparser import DuplicateSectionError


from scrollpy import config
from scrollpy import load_config_file
from scrollpy.scrollsaw._aligniter import AlignIter


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
        config['ARGS']['iter_method'] = 'zorro'
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
