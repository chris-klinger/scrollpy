"""
Module containging test code for the main ScrollPy object.
"""

import os
import shutil
import unittest
from unittest.mock import Mock
from unittest.mock import patch
from configparser import DuplicateSectionError

from Bio import SeqIO

from scrollpy import config
from scrollpy import load_config_file
from scrollpy.scrollsaw._scrollpy import ScrollPy
from scrollpy.util import _mapping


cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
# cleaner to use realpath due to relative path
data_dir = os.path.realpath(os.path.join(cur_dir, '../../fixtures')) # /tests/


class TestScrollPy(unittest.TestCase):
    """New test suite to simplify ScrollPy testing"""

    @classmethod
    def setUpClass(cls):
        """Create a single scrollpy object for use"""
        test_sdict = {
                'group1' : ['seq1-1', 'seq1-2', 'seq1-3'],
                'group2' : ['seq2-1', 'seq2-2'],
                'group3' : ['seq3-1', 'seq3-2', 'seq3-3'],
                }
        test_dir = 'test_scrollpy'
        cls.sp_obj = ScrollPy(
                test_sdict,
                test_dir,
                align_method = 'Mafft',
                dist_method = 'RAxML',
                )

    def test_repr(self):
        """Tests the ScrollPy object's __repr__ method"""
        expected = "ScrollPy({!r}, 'test_scrollpy', **{})".format(
                self.sp_obj._seq_dict, self.sp_obj.kwargs)
        self.assertEqual(expected, repr(self.sp_obj))

    def test_str(self):
        """Tests the ScrollPy object's __str__ method"""
        expected = "ScrollPy object with 3 groups and 8 sequences"
        self.assertEqual(expected, str(self.sp_obj))

    @patch('scrollpy.scrollsaw._scrollpy.console_logger')
    @patch('scrollpy.scrollsaw._scrollpy.status_logger')
    @patch('scrollpy.scrollsaw._scrollpy.BraceMessage')
    @patch('scrollpy.util._logging.log_newlines')
    @patch('scrollpy.util._logging.log_message')
    @patch('scrollpy.scrollsaw._scrollpy.tempfile.TemporaryDirectory')
    @patch.object(ScrollPy, '_sort_distances')
    @patch.object(ScrollPy, '_make_collections')
    def test_call(self, mock_col, mock_sdist, mock_tmp, mock_log,
            mock_lnew, mock_bmsg, mock_sl, mock_cl):
        """Tests the ScrollPy object's __call__ method"""
        mock_bmsg.return_value = "Mock Message"
        col1 = Mock()
        col2 = Mock()
        col3 = Mock()
        self.sp_obj._collections = [col1, col2, col3]
        # Check for basic call
        self.sp_obj()
        # Check calls
        mock_col.assert_called_once()
        mock_sdist.assert_called_once()
        for test_mock in self.sp_obj._collections:
            test_mock.assert_called_once()
        mock_lnew.assert_any_call(mock_cl)
        mock_bmsg.assert_any_call(
                "Performing comparison {} of {}", 1, 3)
        mock_bmsg.assert_any_call(
                "Performing comparison {} of {}", 2, 3)
        mock_bmsg.assert_any_call(
                "Performing comparison {} of {}", 3, 3)
        mock_log.assert_any_call(
                "Mock Message",
                3,
                'INFO',
                mock_sl,
                )

    def test_return_ordered_seqs(self):
        """Tests the ScrollPy classes' return_ordered_seqs method"""
        self.sp_obj._ordered_seqs = 'Ordered'
        self.assertEqual('Ordered', self.sp_obj.return_ordered_seqs())

    @patch('scrollpy.scrollsaw._scrollpy.file_logger')
    @patch('scrollpy.scrollsaw._scrollpy.console_logger')
    @patch('scrollpy.scrollsaw._scrollpy.BraceMessage')
    @patch('scrollpy.util._logging.log_message')
    @patch('scrollpy.scrollsaw._scrollpy.ScrollCollection')
    def test_make_collections(self, mock_coll, mock_log,
            mock_bmsg, mock_cl, mock_fl):
        """Tests the ScrollPy classes' _make_collections method"""
        mock_bmsg.return_value = "Mock Message"
        # Test with a single object first
        self.sp_obj._collections = []  # Reset just in case
        self.sp_obj._groups = ['group1']
        self.sp_obj._make_collections()
        # Assert calls
        mock_bmsg.assert_called_once_with(
                "Adding collection object for single group {}", 'group1')
        mock_log.assert_called_once_with(
                "Mock Message",
                3,
                'INFO',
                mock_cl, mock_fl,
                )
        mock_coll.assert_called_once_with(
                self.sp_obj.target_dir,
                ['seq1-1', 'seq1-2', 'seq1-3'],  # sequence list
                'group1',
                )
        self.assertEqual(len(self.sp_obj._collections), 1)
        # Now, try with all three
        self.sp_obj._collections = []  # Reset just in case
        self.sp_obj._groups = ['group1', 'group2', 'group3']
        self.sp_obj._make_collections()
        # Assert calls
        mock_bmsg.assert_any_call(
                "Adding collection object for groups {} and {}", 'group1', 'group2')
        mock_bmsg.assert_any_call(
                "Adding collection object for groups {} and {}", 'group1', 'group3')
        mock_bmsg.assert_any_call(
                "Adding collection object for groups {} and {}", 'group2', 'group3')
        mock_coll.assert_any_call(
                self.sp_obj.target_dir,
                ['seq1-1','seq1-2','seq1-3','seq2-1','seq2-2'],
                'group1',
                opt_group='group2',
                )
        self.assertEqual(len(self.sp_obj._collections), 3)

    def test_sort_distances(self):
        """Tests a simple version of sorting sequences"""
        self.sp_obj._sort_distances()
        expected = ['seq1-1', 'seq1-2', 'seq1-3', 'seq2-1',
                'seq2-2', 'seq3-1', 'seq3-2', 'seq3-3']
        self.assertEqual(expected,
                self.sp_obj._ordered_seqs)

#class TestScrollPyOneFile(unittest.TestCase):
#    """Tests generic methods that don't invoke any downstream calls"""

#    def setUp(self):
#        """Creates a new ScrollPy Object"""
#        self.tmpdir = os.path.join(data_dir, 'ss-tmp')
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
#        config['ARGS']['dist_matrix'] = 'LG'
#        config['ARGS']['no_clobber'] = 'True'
#        config['ARGS']['align_matrix'] = 'Blosum62'
#        config['ARGS']['align_method'] = 'Mafft'
#        config['ARGS']['dist_method'] = 'RAxML'
#        config['ARGS']['no_clobber'] = False
#        config['ARGS']['no_create'] = False

#        # CHANGE ME TO CHANGE TEST
#        #######################################
#        self.infile = 'Hsap_AP1G_FourSeqs.fa' #
#        #######################################

#        self.infile_base = self.infile.split('.')[0]
#        self.inpath = os.path.join(data_dir, self.infile)

#        # Create seq_dict from mapping first
#        mapping = _mapping.Mapping(
#                [self.inpath],
#                infmt='fasta',
#                alignfmt='fasta',
#                treefmt='newick',
#                test=True,  # Disable unique group names
#                )
#        seq_dict = mapping()

#        self.sp = ScrollPy(
#                seq_dict,
#                self.tmpdir, # target_dir
#                align='Mafft', # align_method
#                distance='RAxML', # dist_method
#                )


#    def tearDown(self):
#        """Remove tmp dir and all files"""
#        shutil.rmtree(self.tmpdir)


#    def test_make_collections_with_one(self):
#        """Tests that collection are made ok"""
#        self.sp._make_collections()
#        self.assertEqual(len(self.sp._collections), 1)


#    def test_sort_distances_in_order(self):
#        """Tests sorting when objects are already in order"""
#        scroll_seq_objs = self.sp._seq_dict[self.infile_base]
#        dist = 0
#        for obj in scroll_seq_objs:
#            obj += dist
#            dist += 1
#        self.sp._sort_distances() # changes sp._ordered_seqs
#        ordered_ids = []
#        for obj in self.sp._ordered_seqs:
#            ordered_ids.append(obj.id_num)
#        self.assertEqual(ordered_ids, [1,2,3,4])


#    def test_sort_distances_outof_order(self):
#        """Tests sorting when objects are not already in order"""
#        scroll_seq_objs = self.sp._seq_dict[self.infile_base]
#        for _,d in zip(scroll_seq_objs, (3,1,4,2)):
#            _ += d
#        self.sp._sort_distances() # changes sp._ordered_seqs
#        ordered_ids = []
#        for obj in self.sp._ordered_seqs:
#            ordered_ids.append(obj.id_num)
#        self.assertEqual(ordered_ids, [2,4,1,3])


#    def test_actual_call(self):
#        """Tests whether a call to ScrollPy with one object works"""
#        self.sp()
#        self.assertEqual(len(self.sp._ordered_seqs), 4)
#        ordered_ids = []
#        for obj in self.sp._ordered_seqs:
#            ordered_ids.append(obj.id_num)
#        self.assertEqual(ordered_ids, [4,2,1,3])


#class TestScrollPyTwoFiles(unittest.TestCase):
#    """Tests each individual method with two files"""

#    def setUp(self):
#        """Creates a new ScrollPy Object"""
#        self.tmpdir = os.path.join(data_dir, 'ss-tmp2')
#        try:
#            os.makedirs(self.tmpdir)
#        except FileExistsError:
#            pass

#        # CHANGE ME TO CHANGE TEST
#        ########################################
#        self.infile1 = 'Hsap_AP1G_FourSeqs.fa' #
#        self.infile2 = 'Tgon_AP1_FourSeqs.fa'  #
#        ########################################

#        self.infile1_base = self.infile1.split('.',1)[0]
#        self.inpath1 = os.path.join(data_dir, self.infile1)

#        self.infile2_base = self.infile2.split('.',1)[0]
#        self.inpath2 = os.path.join(data_dir, self.infile2)

#        # Create seq_dict from mapping first
#        mapping = _mapping.Mapping(
#                [self.inpath1,self.inpath2],
#                infmt='fasta',
#                alignfmt='fasta',
#                treefmt='newick',
#                test=True,  # Disable unique group names
#                )
#        seq_dict = mapping()

#        self.sp = ScrollPy(
#                seq_dict,
#                self.tmpdir, # target_dir
#                align='Mafft', # align_method
#                distance='RAxML', # dist_method
#                )


#    def tearDown(self):
#        """Remove tmp dir and all files"""
#        shutil.rmtree(self.tmpdir)


#    def test_actual_call(self):
#        """Tests whether a call to ScrollPy with two objects works"""
#        self.sp()
#        self.assertEqual(len(self.sp._ordered_seqs), 8)


#class TestScrollPyThreeFiles(unittest.TestCase):
#    """Tests each individual method with three files"""

#    def setUp(self):
#        """Creates a new ScrollPy Object"""
#        self.tmpdir = os.path.join(data_dir, 'ss-tmp3')
#        try:
#            os.makedirs(self.tmpdir)
#        except FileExistsError:
#            pass

#        # CHANGE ME TO CHANGE TEST
#        ########################################
#        self.infile1 = 'Hsap_AP1G_FourSeqs.fa' #
#        self.infile2 = 'Tgon_AP1_FourSeqs.fa'  #
#        self.infile3 = 'Ngru_AP1_FourSeqs.fa'  #
#        ########################################

#        self.infile1_base = self.infile1.split('.',1)[0]
#        self.inpath1 = os.path.join(data_dir, self.infile1)

#        self.infile2_base = self.infile2.split('.',1)[0]
#        self.inpath2 = os.path.join(data_dir, self.infile2)

#        self.infile3_base = self.infile3.split('.',1)[0]
#        self.inpath3 = os.path.join(data_dir, self.infile3)

#        # Create seq_dict from mapping first
#        mapping = _mapping.Mapping(
#                [self.inpath1,self.inpath2,self.inpath3],
#                infmt='fasta',
#                alignfmt='fasta',
#                treefmt='newick',
#                test=True,  # Disable unique group names
#                )
#        seq_dict = mapping()

#        self.sp = ScrollPy(
#                seq_dict,
#                self.tmpdir, # target_dir
#                align='Mafft', # align_method
#                distance='RAxML', # dist_method
#                )


#    def tearDown(self):
#        """Remove tmp dir and all files"""
#        shutil.rmtree(self.tmpdir)


#    def test_actual_call(self):
#        """Tests whether a call to ScrollPy with two objects works"""
#        self.sp()
#        self.assertEqual(len(self.sp._ordered_seqs), 12)


