"""
Tests classes in the 'output.py' module.
"""

import os
import shutil
import unittest
from unittest.mock import Mock
from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import mock_open
from configparser import DuplicateSectionError

from scrollpy.files import output
from scrollpy import config
from scrollpy import load_config_file
from scrollpy.scrollsaw._aligniter import AlignIter
from scrollpy.scrollsaw._scrollpy import ScrollPy
from scrollpy.util._mapping import Mapping


cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
# cleaner to use realpath due to relative path
data_dir = os.path.realpath(os.path.join(cur_dir, '../../fixtures')) # /tests/


class TestBaseWriter(unittest.TestCase):
    """Tests the BaseWriter base class"""

    def setUp(self):
        """Get an instance of BaseWriter"""
        self.writer = output.BaseWriter("","") # Mocked


    def test_write(self):
        with self.assertRaises(NotImplementedError):
            self.writer.write()


    def test_filter(self):
        with self.assertRaises(NotImplementedError):
            self.writer._filter()

class TestAlignWriter(unittest.TestCase):
    """Tests the AlignWriter concrete class"""

    @classmethod
    def setUpClass(cls):
        """Create an instance to use for tests"""
        with patch('scrollpy.files.output.AlignIter', spec=True) as mock_aiter:
            cls.writer = output.AlignWriter(
                    mock_aiter,
                    'outpath',
                    )

    @patch('scrollpy.files.output.file_logger')
    @patch('scrollpy.files.output.console_logger')
    @patch('scrollpy.files.output.BraceMessage')
    @patch('scrollpy.util._logging.log_message')
    @patch('scrollpy.files.output.config')
    @patch('scrollpy.util._util.get_filepath')
    @patch('scrollpy.files.output.af')
    def test_write(self, mock_af, mock_path, mock_config,
            mock_log, mock_bmsg, mock_cl, mock_fl):
        """Tests the AlignWriter classes' write method"""
        # Ensure the right method exists
        self.writer._sp_object.get_optimal_alignment.return_value = "AlignObj"
        mock_path.return_value = 'test outpath'
        # Populate config
        mock_config.__getitem__.return_value = {'alignfmt' : 'fasta'}
        # Now try writing
        self.writer.write()
        # Assert appropriate calls
        self.writer._sp_object.get_optimal_alignment.assert_called_once()
        mock_path.assert_called_once_with(
                'outpath',
                'optimal',
                'alignment',
                extra='alignment',
                )
        mock_af.write_alignment_file.assert_called_once_with(
                'AlignObj',
                'test outpath',
                'fasta',
                )
        # Now assume input object is not an AlignIter
        self.writer._sp_object = Mock()
        mock_bmsg.return_value = "Mock Message"
        self.writer.write()
        mock_bmsg.assert_called_once_with(
                "{} object cannot be written as alignment",
                type(self.writer._sp_object))
        mock_log.assert_called_once_with(
                "Mock Message",
                1,
                'ERROR',
                mock_cl, mock_fl,
                )

class TestSeqWriterScrollPy(unittest.TestCase):
    """Tests the SeqWriter concrete class with ScrollPy mock object"""

    @classmethod
    def setUpClass(cls):
        """Create an instance to use for tests"""
        with patch('scrollpy.files.output.ScrollPy', spec=True) as mock_spy:
            cls.writer = output.SeqWriter(
                    mock_spy,
                    'outpath',
                    )

    @patch('scrollpy.files.output.file_logger')
    @patch('scrollpy.files.output.console_logger')
    @patch('scrollpy.files.output.BraceMessage')
    @patch('scrollpy.util._logging.log_message')
    @patch('scrollpy.files.output.config')
    @patch('scrollpy.util._util.get_filepath')
    @patch('scrollpy.files.output.sf')
    def test_write(self, mock_sf, mock_path, mock_config,
            mock_log, mock_bmsg, mock_cl, mock_fl):
        """Tests the SeqWriter classes' write method"""
        # Temporarily suppress the _filter method
        with patch.object(self.writer, '_filter') as mock_filter:
            test_dict = {  # Emulate output from _filter function
                    'group1' : ['seq1-1', 'seq1-2'],
                    'group2' : ['seq2-1', 'seq2-2'],
                    }
            mock_filter.return_value = test_dict
            mock_path.return_value = 'test outpath'
            # Populate config
            mock_config.__getitem__.return_value = {'seqfmt' : 'fasta'}
            # Now try writing
            self.writer.write()
            # Assert appropriate calls
            mock_filter.assert_called_once_with(mode='some')
            for group in ('group1','group2'):
                mock_path.assert_any_call(
                        'outpath',
                        group,
                        'sequence',
                        extra='scrollsaw',
                        )
            mock_sf._sequence_list_to_file.assert_any_call(
                    ['seq1-1', 'seq1-2'],
                    'test outpath',
                    'fasta',
                    )
            mock_sf._sequence_list_to_file.assert_any_call(
                    ['seq2-1', 'seq2-2'],
                    'test outpath',
                    'fasta',
                    )
        # Now assume input object is not a ScrollPy object
        self.writer._sp_object = Mock()
        mock_bmsg.return_value = "Mock Message"
        self.writer.write()
        mock_bmsg.assert_called_once_with(
                "{} object does not support writing output sequences",
                type(self.writer._sp_object))
        mock_log.assert_called_once_with(
                "Mock Message",
                1,
                'ERROR',
                mock_cl, mock_fl,
                )

class TestSeqWriterScrollTree(unittest.TestCase):
    """Tests the SeqWriter concrete class with ScrollTree mock object"""

    @classmethod
    def setUpClass(cls):
        """Create an instance to use for tests"""
        with patch('scrollpy.files.output.ScrollTree', spec=True) as mock_stree:
            cls.writer = output.SeqWriter(
                    mock_stree,
                    'outpath',
                    )

    @patch('scrollpy.files.output.config')
    @patch('scrollpy.util._util.get_filepath')
    @patch('scrollpy.files.output.sf')
    def test_write(self, mock_sf, mock_path, mock_config):
        """Tests the SeqWriter classes' write method"""
        # Temporarily suppress the _filter method
        with patch.object(self.writer, '_filter') as mock_filter:
            test_dict = {  # Emulate output from _filter function
                    'group1' : ['seq1-1', 'seq1-2'],
                    'group2' : ['seq2-1', 'seq2-2'],
                    }
            mock_filter.return_value = test_dict
            mock_path.return_value = 'test outpath'
            # Populate config
            mock_config.__getitem__.return_value = {'seqfmt' : 'fasta'}
            # Now try writing
            self.writer.write()
            # Assert appropriate calls
            mock_filter.assert_called_once_with(mode='some')
            for group in ('group1','group2'):
                mock_path.assert_any_call(
                        'outpath',
                        group,
                        'sequence',
                        extra='scrollsaw',
                        )
            mock_sf._sequence_list_to_file.assert_any_call(
                    ['seq1-1', 'seq1-2'],
                    'test outpath',
                    'fasta',
                    )
            mock_sf._sequence_list_to_file.assert_any_call(
                    ['seq2-1', 'seq2-2'],
                    'test outpath',
                    'fasta',
                    )

class TestSeqWriterFilter(unittest.TestCase):
    """Tests the SeqWriter concrete class with Filter mock object"""

    @classmethod
    def setUpClass(cls):
        """Create an instance to use for tests"""
        with patch('scrollpy.files.output.Filter', spec=True) as mock_filter:
            cls.writer = output.SeqWriter(
                    mock_filter,
                    'outpath',
                    )

    @patch('scrollpy.files.output.config')
    @patch('scrollpy.util._util.get_filepath')
    @patch('scrollpy.files.output.sf')
    def test_write(self, mock_sf, mock_path, mock_config):
        """Tests the SeqWriter classes' write method"""
        # Temporarily suppress the _filter method
        with patch.object(self.writer, '_filter') as mock_filter:
            test_remaining = {  # Emulate output from _filter function
                    'group1' : ['seq1-1', 'seq1-2'],
                    'group2' : ['seq2-1', 'seq2-2'],
                    }
            test_removed = {
                    'group1' : ['seqrm1-1', 'seqrm1-2'],
                    'group2' : ['seqrm2-1', 'seqrm2-2'],
                    }
            mock_filter.side_effect = [test_remaining, test_removed]
            mock_path.return_value = 'test outpath'
            # Populate config
            mock_config.__getitem__.return_value = {'seqfmt' : 'fasta'}
            # Now try writing
            self.writer.write()
            # Assert appropriate calls
            mock_filter.assert_any_call(mode='remaining')
            mock_filter.assert_any_call(mode='removed')
            for seq_type in ('remaining', 'removed'):
                for group in ('group1','group2'):
                    mock_path.assert_any_call(
                            'outpath',
                            group,
                            'sequence',
                            extra=seq_type,
                            )
            mock_sf._sequence_list_to_file.assert_any_call(
                    ['seq1-1', 'seq1-2'],
                    'test outpath',
                    'fasta',
                    )
            mock_sf._sequence_list_to_file.assert_any_call(
                    ['seq2-1', 'seq2-2'],
                    'test outpath',
                    'fasta',
                    )
            mock_sf._sequence_list_to_file.assert_any_call(
                    ['seqrm1-1', 'seqrm1-2'],
                    'test outpath',
                    'fasta',
                    )
            mock_sf._sequence_list_to_file.assert_any_call(
                    ['seqrm2-1', 'seqrm2-2'],
                    'test outpath',
                    'fasta',
                    )

class TestSeqWriterTreePlacer(unittest.TestCase):
    """Tests the SeqWriter concrete class with TreePlacer mock object"""

    @classmethod
    def setUpClass(cls):
        """Create an instance to use for tests"""
        with patch('scrollpy.files.output.TreePlacer', spec=True) as mock_tplac:
            cls.writer = output.SeqWriter(
                    mock_tplac,
                    'outpath',
                    )

    @patch('scrollpy.files.output.config')
    @patch('scrollpy.util._util.get_filepath')
    @patch('scrollpy.files.output.sf')
    def test_write(self, mock_sf, mock_path, mock_config):
        """Tests the SeqWriter classes' write method"""
        # Temporarily suppress the _filter method
        with patch.object(self.writer, '_filter') as mock_filter:
            test_dict = {  # Emulate output from _filter function
                    'group1' : ['seq1-1', 'seq1-2'],
                    'group2' : ['seq2-1', 'seq2-2'],
                    }
            mock_filter.return_value = test_dict
            mock_path.return_value = 'test outpath'
            # Populate config
            mock_config.__getitem__.return_value = {'seqfmt' : 'fasta'}
            # Now try writing
            self.writer.write()
            # Assert appropriate calls
            mock_filter.assert_called_once_with(mode='classified')
            for group in ('group1','group2'):
                mock_path.assert_any_call(
                        'outpath',
                        group,
                        'sequence',
                        extra='classified',
                        )
            mock_sf._sequence_list_to_file.assert_any_call(
                    ['seq1-1', 'seq1-2'],
                    'test outpath',
                    'fasta',
                    )
            mock_sf._sequence_list_to_file.assert_any_call(
                    ['seq2-1', 'seq2-2'],
                    'test outpath',
                    'fasta',
                    )

class TestSeqWriterFilter(unittest.TestCase):
    """Tests the SeqWriter concrete class with a generic Mock"""

    @classmethod
    def setUpClass(cls):
        """Create an instance to use for tests"""
        cls.run_obj = Mock()
        cls.writer = output.SeqWriter(
                cls.run_obj,
                'outpath',
                )

    @patch('scrollpy.files.output.config')
    @patch('scrollpy.util._util.get_filepath')
    @patch('scrollpy.files.output.sf')
    def test_filter(self, mock_sf, mock_path, mock_config):
        """Tests the SeqWriter classes' _filter method"""
        # First test, mode = 'some'
        mock_config.__getitem__.return_value = {'number' : 2}
        mock_seq1 = Mock(**{'_group' : 'group1'})
        mock_seq2 = Mock(**{'_group' : 'group1'})
        mock_seq3 = Mock(**{'_group' : 'group1'})
        mock_seq4 = Mock(**{'_group' : 'group2'})
        mock_seq5 = Mock(**{'_group' : 'group2'})
        # Mock the return value for the associated object
        self.writer._sp_object.return_ordered_seqs.return_value = [
                mock_seq1, mock_seq2, mock_seq3, mock_seq4, mock_seq5,
                ]
        expected = {
                'group1' : [mock_seq1, mock_seq2],
                'group2' : [mock_seq4, mock_seq5],
                }
        # Check
        self.assertEqual(
                self.writer._filter(mode='some'),
                expected,
                )
        # Now check for the others -> just call a method
        self.writer._filter(mode='remaining')
        self.writer._sp_object.return_remaining_seqs.assert_called_once()
        self.writer._filter(mode='removed')
        self.writer._sp_object.return_removed_seqs.assert_called_once()
        self.writer._filter(mode='classified')
        self.writer._sp_object.return_classified_seqs.assert_called_once()


class TestTableWriter(unittest.TestCase):
    """Tests the TableWriter concrete class"""

    @classmethod
    def setUpClass(cls):
        """Create an instance to use for tests"""
        # Patch two objects directly
        with patch('scrollpy.files.output.ScrollPy', spec=True) as mock_spy:
            with patch('scrollpy.files.output.config') as mock_config:
                mock_config.__getitem__.return_value = {'tblsep' : ','}
                cls.writer = output.TableWriter(
                        mock_spy,
                        'outpath',
                        )

    @patch('scrollpy.files.output.file_logger')
    @patch('scrollpy.files.output.console_logger')
    @patch('scrollpy.files.output.BraceMessage')
    @patch('scrollpy.util._logging.log_message')
    @patch('scrollpy.util._util.get_filepath')
    def test_write(self, mock_path, mock_log, mock_bmsg, mock_cl, mock_fl):
        """Tests the SeqWriter classes' write method.

        Unlike for SeqWriter, just do this once.

        """
        # Temporarily suppress the _filter method
        with patch.object(self.writer, '_filter') as mock_filter:
            with patch.object(self.writer, '_write') as mock_write:
                test_lines = ['line1', 'line2']
                mock_filter.return_value = test_lines
                mock_path.return_value = 'test outpath'
                # Now try writing
                self.writer.write()
                # Assert appropriate calls
                mock_filter.assert_called_once_with(mode='distance')
                mock_path.assert_called_once_with(
                        'outpath',
                        'scrollpy',
                        'table',
                        extra='scrollsaw',
                        )
                mock_write.assert_called_once_with(
                        test_lines,
                        'test outpath',
                        table_type='scrollsaw',
                        )
        # Now assume input object is not a ScrollPy object
        self.writer._sp_object = Mock()
        mock_bmsg.return_value = "Mock Message"
        self.writer.write()
        mock_bmsg.assert_called_once_with(
                "{} object does not support writing output table(s)",
                type(self.writer._sp_object))
        mock_log.assert_called_once_with(
                "Mock Message",
                1,
                'ERROR',
                mock_cl, mock_fl,
                )

    def test_write(self):
        """Tests the TableWriter classes' _write method"""
        with patch.object(self.writer, '_modify_values_based_on_sep') as mock_mod:
            with patch('scrollpy.files.output.open', mock_open()) as mo:
                mock_mod.return_value = ['Modified', 'Scrollsaw']
                # Test for scrollsaw
                self.writer._write(
                        ['line1', 'line2', 'line3'],  # Lines
                        'outpath',
                        'scrollsaw',  # table_type
                        )
                mock_mod.assert_called_with(
                        ',', 'Sequence ID', 'Group', 'Distance')
                mo().write.assert_any_call('Modified,Scrollsaw')  # header
                mo().write.assert_any_call('line1\n')  # Similar for other lines
                # Test for filtered
                self.writer._write(
                        ['line1', 'line2', 'line3'],  # Lines
                        'outpath',
                        'filtered',  # table_type
                        )
                mock_mod.assert_called_with(
                        ',', 'Sequence ID', 'Group', 'Filter value')
                # Test for monophyletic
                self.writer._write(
                        ['line1', 'line2', 'line3'],  # Lines
                        'outpath',
                        'monophyletic',  # table_type
                        )
                # mock_mod.return_value = ['Modified', 'Scrollsaw']
                mock_mod.assert_called_with(
                        ',', 'Sequence ID', 'Monophyly', 'Group',
                        'First Ancestor Support', 'Last Ancestor Node',
                        'Last Ancestor Support', 'Group Completeness',
                        'Sequence Status',
                        )
                # Test for nonmonophyletic
                with patch.object(self.writer, '_get_max_groups') as mock_max:
                    mock_max.return_value = 1
                    self.writer._write(
                            ['line1', 'line2', 'line3'],  # Lines
                            'outpath',
                            'notmonophyletic',  # table_type
                            )
                    # mock_mod.return_value = ['Modified', 'Scrollsaw']
                    mock_mod.assert_called_with(
                            ',', 'Sequence ID', 'Monophyly',
                            'First Ancestor Support', 'Number of Groups',
                            'Group1', 'Group1 Support',
                            'Group1 Completeness',
                            )
                # Test for aligniter
                self.writer._write(
                        ['line1', 'line2', 'line3'],  # Lines
                        'outpath',
                        'aligniter',  # table_type
                        )
                # mock_mod.return_value = ['Modified', 'Scrollsaw']
                mock_mod.assert_called_with(
                        ',', 'Iteration', 'Alignment Length',
                        'Low Column Score', 'Tree Support',
                        'Optimal',
                        )
    @patch('scrollpy.util._util.flatten_dict_to_list')
    @patch('scrollpy.files.output.file_logger')
    @patch('scrollpy.files.output.console_logger')
    @patch('scrollpy.files.output.BraceMessage')
    @patch('scrollpy.util._logging.log_message')
    def test_filter(self, mock_log, mock_bmsg, mock_cl, mock_fl, mock_flat):
        """Tests the TableWriter classes' _filter method"""
        with patch.object(self.writer, '_modify_values_based_on_sep') as mock_mod:
            self.writer._sp_object = Mock()  # Original value is specced!
            mock_mod.return_value = ['Modified', 'Values']
            mock_bmsg.return_value = 'Mock Message'
            # Test for mode = 'distance' first
            # Test when it raises an error -> spec without description/name
            error_mock = Mock(spec = ['_group', '_distance'], **{
                '_group' : 'group1',
                '_distance' : 5,
                })
            self.writer._sp_object.return_ordered_seqs.return_value = [
                    error_mock,
                    ]
            self.writer._filter(mode='distance')
            mock_bmsg.assert_called_once_with(
                    "Could not identify accession for {}", error_mock)
            mock_log.assert_called_once_with(
                    'Mock Message',
                    2,
                    'WARNING',
                    mock_fl,
                    )
            # Now check when objects are good
            test_mock1 = Mock(**{
                'description' : 'Seq1', '_group' : 'group1',
                '_distance' : 5, '_fvalue' : 10,
                })
            test_mock2 = Mock(**{
                'description' : 'Seq2', '_group' : 'group2',
                '_distance' : 3, '_fvalue' : 8,
                })
            self.writer._sp_object.return_ordered_seqs.return_value = [
                    test_mock1, test_mock2,
                    ]
            self.writer._filter(mode='distance')
            mock_mod.assert_any_call(',', 'Seq1', 'group1', 5)
            mock_mod.assert_any_call(',', 'Seq2', 'group2', 3)
            # Test for filter
            self.writer._sp_object.return_all_seqs.return_value = []
            mock_flat.return_value = [test_mock1, test_mock2]
            self.writer._filter(mode='fvalue')
            mock_mod.assert_any_call(',', 'Seq1', 'group1', 10)
            mock_mod.assert_any_call(',', 'Seq2', 'group2', 8)

    def test_modify_values_based_on_sep(self):
        """Tests the TableWriter classes' _modify_values_based_on_sep method"""
        # Underscore -> should replace with a space
        values = ("_", "one_sep", "two__seps", "one _ sep")
        new_vals = self.writer._modify_values_based_on_sep(
                '_', # sep
                *values,
                )
        self.assertEqual(
                new_vals,
                [" ", "one sep", "two  seps", "one   sep"],
                )
        # Comma -> should replace with a space
        values = (",", "one,sep", "two,,seps", "one , sep")
        new_vals = self.writer._modify_values_based_on_sep(',', *values)
        self.assertEqual(
                new_vals,
                [" ", "one sep", "two  seps", "one   sep"],
                )
        # Unusual separator
        values = ("<>", "one<>sep", "two<><>seps", "one <> sep")
        new_vals = self.writer._modify_values_based_on_sep('<>', *values)
        self.assertEqual(
                new_vals,
                [" ", "one sep", "two  seps", "one   sep"],
                )
        # Separator also contains a space -> replace with underscore
        values = ("< >", "one< >sep", "two< >< >seps", "one < > sep")
        new_vals = self.writer._modify_values_based_on_sep('< >', *values)
        self.assertEqual(
                new_vals,
                ["_", "one_sep", "two__seps", "one _ sep"],
                )

    def test_get_max_groups(self):
        """Tests the TableWriter classes' _get_max_groups method"""
        # Test with just one item in lines
        test_lines = [
                ['_', '_', '_', '_', '_', '_'],
                ]
        self.assertEqual(
                self.writer._get_max_groups(test_lines, 2, 2),
                2,
                )
        # Test when raising a ValueError
        with self.assertRaises(ValueError):
            self.writer._get_max_groups(test_lines, 2, 3)
        # Test with more than one item in lines
        test_lines = [
                ['_', '_', '_', '_', '_', '_'],
                ['_', '_', '_', '_', '_', '_', '_', '_'],
                ]
        self.assertEqual(
                self.writer._get_max_groups(test_lines, 2, 2),
                3,
                )

#    @classmethod
#    def setUpClass(cls):
#        """Create necessary objects"""
#        # Make dir
#        cls.tmpdir = os.path.join(data_dir, 'out-seq')
#        try:
#            os.makedirs(cls.tmpdir)
#        except FileExistsError:
#            print("Failed to make target directory")
#            pass
#        # Populate ARGS values of config file
#        load_config_file()
#        try:
#            config.add_section('ARGS')
#        except DuplicateSectionError:
#            pass
#        # Now provide sufficient arg defaults
#        config['ARGS']['filter'] = 'False'
#        config['ARGS']['filter_method'] = 'zscore'
#        config['ARGS']['dist_matrix'] = 'LG'
#        config['ARGS']['no_clobber'] = 'True'

#        # CHANGE ME TO CHANGE TEST
#        #######################################
#        cls.infile = 'Hsap_AP1G_FourSeqs.fa' #
#        #######################################
#        cls.infile_base = cls.infile.split('.')[0]
#        cls.inpath = os.path.join(data_dir, cls.infile)

#        # Make Mapping
#        mapping = Mapping(
#                cls.inpath,
#                infmt='fasta',
#                alignfmt='fasta',
#                treefmt='newick',
#                )
#        seq_dict = mapping()
#        # Now make ScrollPy object
#        cls.sp = ScrollPy(
#                seq_dict,
#                cls.tmpdir, #target dir
#                align='Mafft', # align_method
#                distance='RAxML', # dist_method
#                )
#        cls.sp() # Run internal methods


#    def setUp(self):
#        """Populate the SeqWriter brand new for each test"""
#        # Make SeqWriter object
#        self.writer = output.SeqWriter(
#                self.sp,     # object
#                self.tmpdir, # file_path
#                )


#    @classmethod
#    def tearDownClass(self):
#        """Removes the directory"""
#        shutil.rmtree(self.tmpdir)


#    def test_filter_equal(self):
#        """Tests whether _filter returns the original seq list"""
#        # Mock user input
#        try:
#            config.add_section('ARGS')
#        except DuplicateSectionError:
#            pass
#        config.set('ARGS', 'number', '4') # i.e. config['ARGS']['number']
#        # Test list
#        new_list = self.writer._filter()
#        self.assertEqual(len(new_list[0][1]), 4) # nested -> [(x,[])]


#    def test_filter_less(self):
#        """Tests whether _filter returns a smaller list"""
#        # Mock user input
#        try:
#            config.add_section('ARGS')
#        except DuplicateSectionError:
#            pass
#        config.set('ARGS', 'number', '2') # i.e. config['ARGS']['number']
#        # Test list
#        new_list = self.writer._filter()
#        self.assertEqual(len(new_list[0][1]), 2) # nested -> [(x,[])]


#    def test_filter_more(self):
#        """Tests whether _filter handles N larger than actual number"""
#        # Mock user input
#        try:
#            config.add_section('ARGS')
#        except DuplicateSectionError:
#            pass
#        config.set('ARGS', 'number', '6') # i.e. config['ARGS']['number']
#        # Test list
#        new_list = self.writer._filter()
#        self.assertEqual(len(new_list[0][1]), 4) # nested -> [(x,[])]


#    @unittest.skip('For now')
#    def test_filter_removed_empty(self):
#        """Tests that _filter returns an empty list for empty filter dict"""
#        empty_list = self.writer._filter()
#        self.assertEqual(len(empty_list),0)


#    @unittest.skip('For now')
#    def test_filter_removed_nonempty(self):
#        """Tests that filter returns proper structure when non-empty"""
#        mock_dict = {
#                "group1":['obj1', 'obj2', 'obj3'],
#                "group2":['obj4', 'obj5'],
#                }
#        self.writer._removed_seq_dict = mock_dict  # Add after __init__
#        # Now test
#        new_list = self.writer._filter(removed=True)
#        self.assertEqual(len(new_list[0][1]), 3)  # First nested item
#        self.assertEqual(len(new_list[1][1]), 2)  # Second nested item


#    def test_get_filepath(self):
#        """Tests returned filepath"""
#        # Mock user input
#        try:
#            config.add_section('ARGS')
#        except DuplicateSectionError:
#            pass
#        config.set('ARGS', 'no-clobber', 'False')
#        config.set('ARGS', 'filesep', '_')
#        config.set('ARGS', 'suffix', 'awesome')
#        config.set('ARGS', 'seqfmt', 'fasta')
#        # Call and test
#        outpath = self.writer._get_filepath("group")
#        self.assertEqual(outpath,
#                os.path.join(self.tmpdir, 'group_scrollsaw_awesome.fa'))


#class TestTableWriter(unittest.TestCase):
#    """Tests the TableWriter subclass"""

#    def setUp(self):
#        """Create necessary objects"""
#        # Make dir
#        self.tmpdir = os.path.join(data_dir, 'out-table')
#        try:
#            os.makedirs(self.tmpdir)
#        except FileExistsError:
#            pass
#        # Populate ARGS values of config file
#        load_config_file()
#        try:
#            config.add_section('ARGS')
#        except DuplicateSectionError:
#            pass
#        # Now provide sufficient arg defaults
#        config['ARGS']['tblfmt'] = 'csv'
#        # Make ScrollPy object
#        # CHANGE ME TO CHANGE TEST
#        #######################################
#        self.infile = 'Hsap_AP1G_FourSeqs.fa' #
#        #######################################
#        self.infile_base = self.infile.split('.')[0]
#        self.inpath = os.path.join(data_dir, self.infile)

#        # Make mapping
#        mapping = Mapping(
#                self.inpath,
#                infmt='fasta',
#                alignfmt='fasta',
#                treefmt='newick',
#                )
#        seq_dict = mapping()

#        # Now make ScrollPy object
#        self.sp = ScrollPy(
#                seq_dict,
#                self.tmpdir, #target dir
#                align='Mafft', # align_method
#                distance='RAxML', # dist_method
#                )
#        #self.sp() # Run internal methods
#        # Make SeqWriter object
#        self.writer = output.TableWriter(
#                self.sp,     # object
#                self.tmpdir, # file_path
#                )


#    def tearDown(self):
#        """Removes the directory"""
#        shutil.rmtree(self.tmpdir)


#    def test_modifying_sep_underscore(self):
#        """Tests values with underscores"""
#        values = ("_", "one_sep", "two__seps", "one _ sep")
#        new_vals = self.writer._modify_values_based_on_sep(
#                '_', # sep
#                *values)
#        self.assertEqual(new_vals,
#                [" ", "one sep", "two  seps", "one   sep"])


#    def test_modifying_sep_comma(self):
#        """Tests values with commas"""
#        values = (",", "one,sep", "two,,seps", "one , sep")
#        new_vals = self.writer._modify_values_based_on_sep(
#                ',', *values)
#        self.assertEqual(new_vals,
#                [" ", "one sep", "two  seps", "one   sep"])


#    def test_modifying_compound_sep(self):
#        """Tests with a sep more than one character"""
#        values = ("<>", "one<>sep", "two<><>seps", "one <> sep")
#        new_vals = self.writer._modify_values_based_on_sep(
#                '<>', *values)
#        self.assertEqual(new_vals,
#                [" ", "one sep", "two  seps", "one   sep"])


#    def test_modifying_compound_with_space(self):
#        """Tests a sep with a space"""
#        values = ("< >", "one< >sep", "two< >< >seps", "one < > sep")
#        new_vals = self.writer._modify_values_based_on_sep(
#                '< >', *values)
#        self.assertEqual(new_vals,
#                ["_", "one_sep", "two__seps", "one _ sep"])



#if __name__ == '__main__':
#    unittest.main()
