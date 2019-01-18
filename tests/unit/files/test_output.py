"""
Tests classes in the 'output.py' module.
"""

import os
import shutil
import unittest
from configparser import DuplicateSectionError

from scrollpy.files import output
from scrollpy import config
from scrollpy.scrollsaw._scrollpy import ScrollPy


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

    def setUp(self):
        """Create necessary objects"""
        # Make dir
        self.tmpdir = os.path.join(data_dir, 'out-tmp')
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
        self.sp = ScrollPy(
                self.tmpdir, #target dir
                'Mafft', # align_method
                'RAxML', # dist_method
                self.inpath)
        self.sp() # Run internal methods
        # Make SeqWriter object
        self.writer = output.SeqWriter(
                self.sp,     # object
                self.tmpdir, # file_path
                )


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
        # Call and test
        outpath = self.writer._get_filepath("group")
        self.assertEqual(outpath,
                os.path.join(self.tmpdir, 'group_sequences_awesome.fa'))


    def tearDown(self):
        """Removes the directory"""
        shutil.rmtree(self.tmpdir)


class TestTableWriter(unittest.TestCase):
    """Tests the TableWriter subclass"""

    def setUp(self):
        """Create necessary objects"""
        # Make dir
        self.tmpdir = os.path.join(data_dir, 'out-tmp')
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
        self.sp = ScrollPy(
                self.tmpdir, #target dir
                'Mafft', # align_method
                'RAxML', # dist_method
                self.inpath)
        #self.sp() # Run internal methods
        # Make SeqWriter object
        self.writer = output.TableWriter(
                self.sp,     # object
                self.tmpdir, # file_path
                )


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


    def tearDown(self):
        """Removes the directory"""
        shutil.rmtree(self.tmpdir)


if __name__ == '__main__':
    unittest.main()
