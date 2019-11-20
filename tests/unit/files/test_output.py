"""
Tests classes in the 'output.py' module.
"""

import os
import shutil
import unittest
from configparser import DuplicateSectionError

from scrollpy.files import output
from scrollpy import config
from scrollpy import load_config_file
from scrollpy.scrollsaw._scrollpy import ScrollPy
from scrollpy.util._mapping import Mapping


cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
# cleaner to use realpath due to relative path
data_dir = os.path.realpath(os.path.join(cur_dir, '../../fixtures')) # /tests/


class TestBaseWriter(unittest.TestCase):
    """Tests the base implementation"""

    def setUp(self):
        """Get an instance of BaseWriter"""
        self.writer = output.BaseWriter("","") # Mocked


    def test_write(self):
        with self.assertRaises(NotImplementedError):
            self.writer.write()


    def test_filter(self):
        with self.assertRaises(NotImplementedError):
            self.writer._filter()


class TestSeqWriterOneFile(unittest.TestCase):
    """Tests the seq writer class"""

    @classmethod
    def setUpClass(cls):
        """Create necessary objects"""
        # Make dir
        cls.tmpdir = os.path.join(data_dir, 'out-seq')
        try:
            os.makedirs(cls.tmpdir)
        except FileExistsError:
            print("Failed to make target directory")
            pass
        # Populate ARGS values of config file
        load_config_file()
        try:
            config.add_section('ARGS')
        except DuplicateSectionError:
            pass
        # Now provide sufficient arg defaults
        config['ARGS']['filter'] = 'False'
        config['ARGS']['filter_method'] = 'zscore'
        config['ARGS']['dist_matrix'] = 'LG'
        config['ARGS']['no_clobber'] = 'True'

        # CHANGE ME TO CHANGE TEST
        #######################################
        cls.infile = 'Hsap_AP1G_FourSeqs.fa' #
        #######################################
        cls.infile_base = cls.infile.split('.')[0]
        cls.inpath = os.path.join(data_dir, cls.infile)

        # Make Mapping
        mapping = Mapping(
                cls.inpath,
                infmt='fasta',
                treefmt='newick',
                )
        seq_dict = mapping()
        # Now make ScrollPy object
        cls.sp = ScrollPy(
                seq_dict,
                cls.tmpdir, #target dir
                align='Mafft', # align_method
                distance='RAxML', # dist_method
                )
        cls.sp() # Run internal methods


    def setUp(self):
        """Populate the SeqWriter brand new for each test"""
        # Make SeqWriter object
        self.writer = output.SeqWriter(
                self.sp,     # object
                self.tmpdir, # file_path
                )


    @classmethod
    def tearDownClass(self):
        """Removes the directory"""
        shutil.rmtree(self.tmpdir)


    def test_filter_equal(self):
        """Tests whether _filter returns the original seq list"""
        # Mock user input
        try:
            config.add_section('ARGS')
        except DuplicateSectionError:
            pass
        config.set('ARGS', 'number', '4') # i.e. config['ARGS']['number']
        # Test list
        new_list = self.writer._filter()
        self.assertEqual(len(new_list[0][1]), 4) # nested -> [(x,[])]


    def test_filter_less(self):
        """Tests whether _filter returns a smaller list"""
        # Mock user input
        try:
            config.add_section('ARGS')
        except DuplicateSectionError:
            pass
        config.set('ARGS', 'number', '2') # i.e. config['ARGS']['number']
        # Test list
        new_list = self.writer._filter()
        self.assertEqual(len(new_list[0][1]), 2) # nested -> [(x,[])]


    def test_filter_more(self):
        """Tests whether _filter handles N larger than actual number"""
        # Mock user input
        try:
            config.add_section('ARGS')
        except DuplicateSectionError:
            pass
        config.set('ARGS', 'number', '6') # i.e. config['ARGS']['number']
        # Test list
        new_list = self.writer._filter()
        self.assertEqual(len(new_list[0][1]), 4) # nested -> [(x,[])]


    def test_filter_removed_empty(self):
        """Tests that _filter returns an empty list for empty filter dict"""
        empty_list = self.writer._filter(removed=True)
        self.assertEqual(len(empty_list),0)


    def test_filter_removed_nonempty(self):
        """Tests that filter returns proper structure when non-empty"""
        mock_dict = {
                "group1":['obj1', 'obj2', 'obj3'],
                "group2":['obj4', 'obj5'],
                }
        self.writer._removed_seq_dict = mock_dict  # Add after __init__
        # Now test
        new_list = self.writer._filter(removed=True)
        self.assertEqual(len(new_list[0][1]), 3)  # First nested item
        self.assertEqual(len(new_list[1][1]), 2)  # Second nested item


    def test_get_filepath(self):
        """Tests returned filepath"""
        # Mock user input
        try:
            config.add_section('ARGS')
        except DuplicateSectionError:
            pass
        config.set('ARGS', 'no-clobber', 'False')
        config.set('ARGS', 'filesep', '_')
        config.set('ARGS', 'suffix', 'awesome')
        config.set('ARGS', 'seqfmt', 'fasta')
        # Call and test
        outpath = self.writer._get_filepath("group")
        self.assertEqual(outpath,
                os.path.join(self.tmpdir, 'group_sequences_awesome.fa'))


class TestTableWriter(unittest.TestCase):
    """Tests the TableWriter subclass"""

    def setUp(self):
        """Create necessary objects"""
        # Make dir
        self.tmpdir = os.path.join(data_dir, 'out-table')
        try:
            os.makedirs(self.tmpdir)
        except FileExistsError:
            pass
        # Make ScrollPy object
        # CHANGE ME TO CHANGE TEST
        #######################################
        self.infile = 'Hsap_AP1G_FourSeqs.fa' #
        #######################################
        self.infile_base = self.infile.split('.')[0]
        self.inpath = os.path.join(data_dir, self.infile)

        # Make mapping
        mapping = Mapping(
                self.inpath,
                infmt='fasta',
                treefmt='newick',
                )
        seq_dict = mapping()

        # Now make ScrollPy object
        self.sp = ScrollPy(
                seq_dict,
                self.tmpdir, #target dir
                align='Mafft', # align_method
                distance='RAxML', # dist_method
                )
        #self.sp() # Run internal methods
        # Make SeqWriter object
        self.writer = output.TableWriter(
                self.sp,     # object
                self.tmpdir, # file_path
                )


    def tearDown(self):
        """Removes the directory"""
        shutil.rmtree(self.tmpdir)


    def test_modifying_sep_underscore(self):
        """Tests values with underscores"""
        values = ("_", "one_sep", "two__seps", "one _ sep")
        new_vals = self.writer._modify_values_based_on_sep(
                '_', # sep
                *values)
        self.assertEqual(new_vals,
                [" ", "one sep", "two  seps", "one   sep"])


    def test_modifying_sep_comma(self):
        """Tests values with commas"""
        values = (",", "one,sep", "two,,seps", "one , sep")
        new_vals = self.writer._modify_values_based_on_sep(
                ',', *values)
        self.assertEqual(new_vals,
                [" ", "one sep", "two  seps", "one   sep"])


    def test_modifying_compound_sep(self):
        """Tests with a sep more than one character"""
        values = ("<>", "one<>sep", "two<><>seps", "one <> sep")
        new_vals = self.writer._modify_values_based_on_sep(
                '<>', *values)
        self.assertEqual(new_vals,
                [" ", "one sep", "two  seps", "one   sep"])


    def test_modifying_compound_with_space(self):
        """Tests a sep with a space"""
        values = ("< >", "one< >sep", "two< >< >seps", "one < > sep")
        new_vals = self.writer._modify_values_based_on_sep(
                '< >', *values)
        self.assertEqual(new_vals,
                ["_", "one_sep", "two__seps", "one _ sep"])



if __name__ == '__main__':
    unittest.main()
