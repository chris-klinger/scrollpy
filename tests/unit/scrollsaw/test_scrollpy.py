"""
Module containging test code for the main ScrollPy object.
"""

import os, unittest, shutil
from configparser import DuplicateSectionError

from Bio import SeqIO

from scrollpy import config
from scrollpy import load_config_file
from scrollpy.scrollsaw._scrollpy import ScrollPy
from scrollpy.util import _mapping


cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
# cleaner to use realpath due to relative path
data_dir = os.path.realpath(os.path.join(cur_dir, '../../fixtures')) # /tests/


class TestScrollPyOneFile(unittest.TestCase):
    """Tests generic methods that don't invoke any downstream calls"""

    def setUp(self):
        """Creates a new ScrollPy Object"""
        self.tmpdir = os.path.join(data_dir, 'ss-tmp')
        try:
            os.makedirs(self.tmpdir)
        except FileExistsError:
            pass
        # Populate ARGS values of config file
        load_config_file()
        try:
            config.add_section('ARGS')
        except DuplicateSectionError:
            pass
        # Now provide sufficient arg defaults
        config['ARGS']['dist_matrix'] = 'LG'
        config['ARGS']['no_clobber'] = 'True'

        # CHANGE ME TO CHANGE TEST
        #######################################
        self.infile = 'Hsap_AP1G_FourSeqs.fa' #
        #######################################

        self.infile_base = self.infile.split('.')[0]
        self.inpath = os.path.join(data_dir, self.infile)

        # Create seq_dict from mapping first
        mapping = _mapping.Mapping(
                self.inpath,
                infmt='fasta',
                treefmt='newick',
                test=True,  # Disable unique group names
                )
        seq_dict = mapping()

        self.sp = ScrollPy(
                seq_dict,
                self.tmpdir, # target_dir
                align='Mafft', # align_method
                distance='RAxML', # dist_method
                )


    def tearDown(self):
        """Remove tmp dir and all files"""
        shutil.rmtree(self.tmpdir)


    def test_make_collections_with_one(self):
        """Tests that collection are made ok"""
        self.sp._make_collections()
        self.assertEqual(len(self.sp._collections), 1)


    def test_sort_distances_in_order(self):
        """Tests sorting when objects are already in order"""
        scroll_seq_objs = self.sp._seq_dict[self.infile_base]
        dist = 0
        for obj in scroll_seq_objs:
            obj += dist
            dist += 1
        self.sp._sort_distances() # changes sp._ordered_seqs
        ordered_ids = []
        for obj in self.sp._ordered_seqs:
            ordered_ids.append(obj.id_num)
        self.assertEqual(ordered_ids, [1,2,3,4])


    def test_sort_distances_outof_order(self):
        """Tests sorting when objects are not already in order"""
        scroll_seq_objs = self.sp._seq_dict[self.infile_base]
        for _,d in zip(scroll_seq_objs, (3,1,4,2)):
            _ += d
        self.sp._sort_distances() # changes sp._ordered_seqs
        ordered_ids = []
        for obj in self.sp._ordered_seqs:
            ordered_ids.append(obj.id_num)
        self.assertEqual(ordered_ids, [2,4,1,3])


    def test_actual_call(self):
        """Tests whether a call to ScrollPy with one object works"""
        self.sp()
        self.assertEqual(len(self.sp._ordered_seqs), 4)
        ordered_ids = []
        for obj in self.sp._ordered_seqs:
            ordered_ids.append(obj.id_num)
        self.assertEqual(ordered_ids, [4,2,1,3])


class TestScrollPyTwoFiles(unittest.TestCase):
    """Tests each individual method with two files"""

    def setUp(self):
        """Creates a new ScrollPy Object"""
        self.tmpdir = os.path.join(data_dir, 'ss-tmp2')
        try:
            os.makedirs(self.tmpdir)
        except FileExistsError:
            pass

        # CHANGE ME TO CHANGE TEST
        ########################################
        self.infile1 = 'Hsap_AP1G_FourSeqs.fa' #
        self.infile2 = 'Tgon_AP1_FourSeqs.fa'  #
        ########################################

        self.infile1_base = self.infile1.split('.',1)[0]
        self.inpath1 = os.path.join(data_dir, self.infile1)

        self.infile2_base = self.infile2.split('.',1)[0]
        self.inpath2 = os.path.join(data_dir, self.infile2)

        # Create seq_dict from mapping first
        mapping = _mapping.Mapping(
                *(self.inpath1,self.inpath2),
                infmt='fasta',
                treefmt='newick',
                test=True,  # Disable unique group names
                )
        seq_dict = mapping()

        self.sp = ScrollPy(
                seq_dict,
                self.tmpdir, # target_dir
                align='Mafft', # align_method
                distance='RAxML', # dist_method
                )


    def tearDown(self):
        """Remove tmp dir and all files"""
        shutil.rmtree(self.tmpdir)


    def test_actual_call(self):
        """Tests whether a call to ScrollPy with two objects works"""
        self.sp()
        self.assertEqual(len(self.sp._ordered_seqs), 8)


class TestScrollPyThreeFiles(unittest.TestCase):
    """Tests each individual method with three files"""

    def setUp(self):
        """Creates a new ScrollPy Object"""
        self.tmpdir = os.path.join(data_dir, 'ss-tmp3')
        try:
            os.makedirs(self.tmpdir)
        except FileExistsError:
            pass

        # CHANGE ME TO CHANGE TEST
        ########################################
        self.infile1 = 'Hsap_AP1G_FourSeqs.fa' #
        self.infile2 = 'Tgon_AP1_FourSeqs.fa'  #
        self.infile3 = 'Ngru_AP1_FourSeqs.fa'  #
        ########################################

        self.infile1_base = self.infile1.split('.',1)[0]
        self.inpath1 = os.path.join(data_dir, self.infile1)

        self.infile2_base = self.infile2.split('.',1)[0]
        self.inpath2 = os.path.join(data_dir, self.infile2)

        self.infile3_base = self.infile3.split('.',1)[0]
        self.inpath3 = os.path.join(data_dir, self.infile3)

        # Create seq_dict from mapping first
        mapping = _mapping.Mapping(
                *(self.inpath1,self.inpath2,self.inpath3),
                infmt='fasta',
                treefmt='newick',
                test=True,  # Disable unique group names
                )
        seq_dict = mapping()

        self.sp = ScrollPy(
                seq_dict,
                self.tmpdir, # target_dir
                align='Mafft', # align_method
                distance='RAxML', # dist_method
                )


    def tearDown(self):
        """Remove tmp dir and all files"""
        shutil.rmtree(self.tmpdir)


    def test_actual_call(self):
        """Tests whether a call to ScrollPy with two objects works"""
        self.sp()
        self.assertEqual(len(self.sp._ordered_seqs), 12)


