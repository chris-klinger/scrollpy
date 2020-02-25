"""
Tests the scrollsaw/_aligniter module.
"""

import os
import unittest
from unittest.mock import Mock
from unittest.mock import MagicMock
from unittest.mock import patch
import shutil
from configparser import DuplicateSectionError

from Bio import AlignIO

from scrollpy import config
from scrollpy import load_config_file
from scrollpy.scrollsaw._aligniter import AlignIter
# from scrollpy.alignments import parser
from scrollpy.files import align_file as af


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
            config.add_section('ITER')
            config.add_section('TREE')
        except DuplicateSectionError:
            pass
        # Provide defaults
        config['ARGS']['alignfmt'] = 'fasta'
        config['ARGS']['col_method'] = 'zorro'
        config['ARGS']['iter_method'] = 'histogram'
        config['ARGS']['tree_method'] = 'Iqtree'
        config['ARGS']['tree_matrix'] = 'LG'
        config['ARGS']['no_clobber'] = False
        config['ARGS']['no_create'] = False
        config['ARGS']['verbosity'] = '3'
        # Filepaths
        config['ITER']['zorro'] = 'path/to/zorro'
        config['TREE']['Iqtree'] = 'path/to/iqtree'

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
                target_dir=self.tmpdir,
                )

    @classmethod
    def tearDownClass(cls):
        """Remove directory"""
        try:
            shutil.rmtree(cls.tmpdir)
        except FileNotFoundError:
            pass

    def test_repr(self):
        """Tests the AlignIter classes' __repr__ method"""
        expected = "AlignIter({!r}, {!r}, None, **{})".format(
                type(self).alignment,
                type(self).tmpdir,
                self.iter.kwargs,
                )
        self.assertEqual(
                expected,
                repr(self.iter),
                )

    def test_str(self):
        """Tests the AlignIter classes' __str__  method"""
        expected = "AlignIter using zorro"
        self.assertEqual(
                expected,
                str(self.iter),
                )

    @patch('scrollpy.scrollsaw._aligniter.file_logger')
    @patch('scrollpy.scrollsaw._aligniter.console_logger')
    @patch('scrollpy.scrollsaw._aligniter.BraceMessage')
    @patch('scrollpy.util._logging.log_message')
    @patch('scrollpy.util._util.get_filepath')
    @patch.object(AlignIter, '_evaluate_info')
    @patch.object(AlignIter, '_bisect_run')
    @patch.object(AlignIter, '_hist_run')
    @patch.object(AlignIter, '_evaluate_columns')
    @patch.object(AlignIter, '_calculate_columns')
    @patch.object(AlignIter, '_parse_alignment')
    def test_call(self, mock_parse, mock_calc, mock_eval, mock_hrun, mock_brun,
            mock_info, mock_path, mock_log, mock_bmsg, mock_cl, mock_fl):
        """Tests the AlignIter classes' __call__ method"""
        # General test log message
        mock_bmsg.return_value = "Mock Message"
        # Test when no outdir is specified
        self.iter._outdir = None
        self.iter()
        # Test calls
        mock_parse.assert_called_once()
        mock_path.assert_called_once_with(
                self.iter._outdir,
                self.iter._align_name,
                'column',
                extra='columns',
                )
        mock_calc.assert_called_once()
        mock_eval.assert_called_once()
        mock_info.assert_called_once()
        # Test when the iter method is hist
        self.iter.iter_method = 'histogram'
        self.iter()
        mock_bmsg.assert_any_call(
                "Running tree iteration using histogram method")
        mock_log.assert_any_call(
                "Mock Message",
                2,
                'INFO',
                mock_cl, mock_fl,
                )
        mock_hrun.assert_any_call()
        # Test when the iter method is bisection
        self.iter.iter_method = 'bisection'
        self.iter()
        mock_bmsg.assert_any_call(
                "Running tree iteration using bisection method")
        mock_log.assert_any_call(
                "Mock Message",
                2,
                'INFO',
                mock_cl, mock_fl,
                )
        mock_brun.assert_any_call()

    def test_set_alignment_name(self):
        """Tests the AlignIter classes' _set_alignment_name method"""
        expected = 'Hsap_AP_EGADEZ'
        self.iter._set_alignment_name()
        self.assertEqual(expected,
                self.iter._align_name)

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

    @patch('scrollpy.files.tree_file.read_tree')
    def test_parse_tree(self, mock_tparse):
        """Tests the AlignIter classes' _parse_tree method"""
        mock_tparse.return_value = 'Test Tree'
        self.iter._parse_tree()
        # Check calls and assignments
        mock_tparse.assert_called_once_with(
                self.iter._current_tree_path,
                'newick',
                )
        self.assertEqual('Test Tree',
                self.iter._current_tree_obj)

    @patch('scrollpy.scrollsaw._aligniter.AlignIO')
    def test_write_current_alignment(self, mock_aio):
        """Tests the AlignIter classes' _write_current_alignment method"""
        self.iter._write_current_alignment()
        mock_aio.write.assert_called_once_with(
                self.iter._align_obj,
                self.iter._current_phy_path,
                'phylip-relaxed',
                )

    @patch('scrollpy.scrollsaw._aligniter.AlignEvaluator')
    def test_calculate_columns(self, mock_eval):
        """Tests calculating columns"""
        test_path = 'test_column_path'
        self.iter._calculate_columns(test_path)
        mock_eval.assert_called_once_with(
                self.iter.col_method,
                'path/to/zorro',  # Mock cmd
                self.iter._alignment,
                'test_column_path',
                cmd_list=[self.iter._alignment],
                )

    def test_evaluate_columns(self):
        """Tests evaluating calculated columns"""
        column_path = os.path.join(
                data_dir,
                'Hsap_AP_EGADEZ_colscores.txt',
                )
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

    def _return_new_cols(self):
        """Hack to work around side_effect"""
        try:
            num_calls = self._return_new_cols.__dict__['num_calls']
            print("Retrieved cols from dict")
        except KeyError:
            print("KeyError on value access")
            num_calls = 0
        num_calls += 1
        if num_calls == 1:
            self.iter._columns = [
                [1, 4], [3, 6],
                [4, 4], [5, 9]]
        elif num_calls == 2:
            self.iter._columns = [
                [3, 6], [5, 9]]
        self._return_new_cols.__dict__['num_calls'] = num_calls

    def _return_new_values(self):
        """Hack to work around side_effect"""
        try:
            num_calls = self._return_new_values.__dict__['num_calls']
            print("Retireved values from dict")
        except KeyError:
            print("KeyError on value access")
            num_calls = 0
        num_calls += 1
        if num_calls == 1:
            self.iter._current_support = 95
        elif num_calls == 2:
            self.iter._current_support = 90
        elif num_calls == 3:
            self.iter._current_support = 60
        self._return_new_values.__dict__['num_calls'] = num_calls

    @patch('scrollpy.scrollsaw._aligniter.console_logger')
    @patch('scrollpy.scrollsaw._aligniter.status_logger')
    @patch('scrollpy.scrollsaw._aligniter.BraceMessage')
    @patch('scrollpy.util._logging.log_newlines')
    @patch('scrollpy.util._logging.log_message')
    @patch.object(AlignIter, '_is_optimal')
    @patch.object(AlignIter, '_calculate_support')
    @patch.object(AlignIter, '_parse_tree')
    @patch.object(AlignIter, '_make_tree')
    @patch.object(AlignIter, '_write_current_alignment')
    @patch.object(AlignIter, '_get_current_outpaths')
    @patch.object(AlignIter, '_remove_columns')
    @patch.object(AlignIter, '_calculate_num_columns')
    def test_hist_run(self, mock_calcn, mock_rmc, mock_paths, mock_wca, mock_mt, mock_pt,
            mock_calcs, mock_opt, mock_log, mock_lnew, mock_bmsg, mock_sl, mock_cl):
        """Tests the AlignIter classes' _hist_run method"""
        mock_bmsg.return_value = "Mock Message"
        # Test when not calculating columns
        self.iter._num_columns = 2
        self.iter._columns = [
                [0, 1], [1, 4],
                [2, 3], [3, 6],
                [4, 4], [5, 9],
                ]
        # mock_rmc.return_value = self._return_new_cols
        # mock_rmc.side_effect = self._return_new_cols
        # mock_rmc.side_effect = [
        #         self._return_new_cols(),
        #         self._return_new_cols(),
        #         ]
        # mock_calcs.return_value = self._return_new_values()
        # mock_calcs.side_effect = [
        #         self._return_new_values(),
        #         self._return_new_values(),
        #         ]
        mock_opt.side_effect = [False, True]
        self.iter._hist_run()
        # Test calls
        mock_rmc.assert_any_call(2)
        mock_paths.assert_any_call()
        mock_wca.assert_any_call()
        mock_mt.assert_any_call()
        mock_pt.assert_any_call()
        mock_calcs.assert_any_call()
        mock_opt.assert_any_call()
        # Test logging calls
        mock_bmsg.assert_any_call(
                "Performing tree iteration {} of many", 1)
        mock_bmsg.assert_any_call(
                "Performing tree iteration {} of many", 2)
        mock_log.assert_any_call(
                "Mock Message",
                3,
                'INFO',
                mock_sl,
                )
        # print()
        # print(self.iter.iter_info)
        # Check whether or not the internal list is updated or not
        # expected = [
        #         [0, 6, 1, 95],
        #         [1, 4, 4, 90],
        #         [1, 2, 5, 60],
        #         ]
        # self.assertEqual(expected, self.iter.iter_info)

    def test_calculate_num_columns(self):
        """Tests calculating works"""
        column_path = os.path.join(
                data_dir,
                'Hsap_AP_EGADEZ_colscores.txt',
                )
        if not os.path.exists(column_path):
            self.iter._calculate_columns(column_path)
        self.iter._evaluate_columns(column_path)
        # FINALLY calculate
        num_columns = self.iter._calculate_num_columns()
        self.assertEqual(num_columns,531)

    def test_remove_cols_from_align_easy(self):
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

    def test_remove_cols_from_align_hard(self):
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

    @patch('scrollpy.scrollsaw._aligniter.os.path.basename')
    @patch('scrollpy.util._util.get_filepath')
    def test_get_current_outpaths(self, mock_path, mock_bname):
        """Tests the AlignIter classes' _get_current_outpaths method"""
        mock_bname.return_value = '.phy'
        mock_seq = Mock(**{'seq': 'AGTC'})  # len(seq) = 4
        self.iter._align_obj = [mock_seq]
        self.iter._get_current_outpaths()
        mock_path.assert_any_call(
                self.iter._outdir,
                self.iter._align_name,
                'alignment',
                extra=4,
                alignfmt='phylip',
                )
        mock_path.assert_any_call(
                self.iter._outdir,
                self.iter._align_name,
                'tree',
                extra=4,
                phylip_ext='.phy',
                treefmt='iqtree',
                )

    @patch('scrollpy.scrollsaw._aligniter.TreeBuilder')
    def test_make_tree(self, mock_builder):
        """Tests the AlignIter classes' _make_tree method"""
        self.iter._make_tree()
        mock_builder.assert_called_once_with(
                self.iter.tree_method,
                'path/to/iqtree',
                inpath=self.iter._current_phy_path,
                outpath=self.iter._current_tree_path,
                cmd_list=[
                    '-nt',  # Number of processors
                    'AUTO',
                    '-s',  # Input filename
                    self.iter._current_phy_path,
                    '-m',
                    self.iter.tree_matrix,  # E.g. 'LG'
                    '-bb',  # Rapid bootstrapping
                    '1000',
                    ],
                )

    def test_calculate_support(self):
        """Tests calculating  support"""
        self.iter._current_tree_path = os.path.join(
                data_dir,
                'Hsap_AP_EGADEZ.mfa.contree',
                )
        # Make tree, if not exists
        if not os.path.exists(self.iter._current_tree_path):
            self.iter._make_tree()
        # Now parse it
        self.iter._parse_tree()
        # Calc the values
        self.iter._calculate_support()
        self.assertEqual(self.iter._current_support,141)

    def test_is_optimal(self):
        """Tests calculating optimal"""
        # Simple case -> less than 3 support values
        self.iter._all_supports = [100]
        self.assertFalse(self.iter._is_optimal())
        # Now check when supports are off by a lot
        self.iter._current_support = [20]
        self.iter._all_supports = [100, 95, 98, 90, 92]
        self.assertTrue(self.iter._is_optimal())

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
