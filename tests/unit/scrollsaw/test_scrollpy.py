"""
Module containging test code for the main ScrollPy object.
"""

import os, unittest, shutil

from Bio import SeqIO

cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
# cleaner to use realpath due to relative path
data_dir = os.path.realpath(os.path.join(cur_dir, '../../fixtures')) # /tests/


from scrollpy.scrollsaw._scrollpy import ScrollPy


class TestScrollPyOneFile(unittest.TestCase):
    """Tests generic methods that don't invoke any downstream calls"""

    def setUp(self):
        """Creates a new ScrollPy Object"""
        self.tmpdir = os.path.join(data_dir, 'ss-tmp')
        try:
            os.makedirs(self.tmpdir)
        except FileExistsError:
            pass
        #######################################
        self.infile = 'Hsap_AP1G_FourSeqs.fa' # CHANGE ME TO CHANGE TEST
        #######################################

        self.infile_base = self.infile.split('.')[0]
        self.inpath = os.path.join(data_dir, self.infile)

        self.sp = ScrollPy(
                self.tmpdir, # target_dir
                'Mafft', # align_method
                'RAxML', # dist_method
                self.inpath)


    # Testing Utility function(s)
    def test_group_naming_nonoverlap(self):
        """Tests to ensure that naming is normal if unique"""
        self.sp._groups.append("group1")
        self.sp._groups.append(
            self.sp._unique_group_name("group2"))
        self.assertEqual(self.sp._groups, ["group1", "group2"])


    def test_group_naming_overlap(self):
        """Tests that the group naming convention works"""
        self.sp._groups.append("group1")
        self.sp._groups.append(
            self.sp._unique_group_name("group1"))
        self.assertEqual(self.sp._groups, ["group1", "group1.1"])


    def test_group_naming_overlap_integers(self):
        """Tests that group naming works if names are ints"""
        self.sp._groups.append("1") # These should always be strings
        self.sp._groups.append(
            self.sp._unique_group_name("1")) # Always strings!
        self.assertEqual(self.sp._groups, ["1", "1.1"])


    def test_group_naming_overlap_floats(self):
        """Tests that group naming works if names are float-ish"""
        self.sp._groups.append("1.1")
        self.sp._groups.append(
            self.sp._unique_group_name("1.1")) # Always strings
        self.assertEqual(self.sp._groups, ["1.1", "1.1.1"])


    # Testing actual data-based functions
    def test_infile_parsing(self):
        """Tests that infile parsing is fine"""
        self.sp._parse_infiles()
        self.assertEqual(self.sp._groups[0], self.infile_base)
        self.assertTrue(self.infile_base in self.sp._seq_dict.keys())
        self.assertEqual(len(self.sp._seq_dict[self.infile_base]), 4)


    def test_make_scroll_seqs(self):
        """Tests that records are transformed to ScrollSeqs"""
        with open(self.sp.infiles[0]) as i:
            records = [r for r in SeqIO.parse(i, "fasta")]
        ss = self.sp._make_scroll_seqs(
            self.sp.infiles[0], # infile
            "one", # group; arbitrary
            records)
        self.assertEqual(len(ss), 4)
        self.assertEqual(ss[0].id_num, 1)
        self.assertEqual(ss[1].id_num, 2)


    def test_make_collections_with_one(self):
        """Tests that collection are made ok"""
        with open(self.sp.infiles[0]) as i:
            records = [r for r in SeqIO.parse(i, "fasta")]
        self.sp._groups.append("one") # need to have _groups
        self.sp._seq_dict["one"] = records
        self.sp._make_scroll_seqs(
            self.sp.infiles[0],
            "one",
            records)
        self.sp._make_collections()
        self.assertEqual(len(self.sp._collections), 1)


    def test_sort_distances_in_order(self):
        """Tests sorting when objects are already in order"""
        self.sp._parse_infiles() # Should populate all groups
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
        self.sp._parse_infiles() # Should populate all groups
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


    def tearDown(self):
        """Remove tmp dir and all files"""
        shutil.rmtree(self.tmpdir)


class TestScrollPyTwoFiles(unittest.TestCase):
    """Tests each individual method with two files"""

    def setUp(self):
        """Creates a new ScrollPy Object"""
        self.tmpdir = os.path.join(data_dir, 'ss-tmp2')
        try:
            os.makedirs(self.tmpdir)
        except FileExistsError:
            pass

        ########################################
        self.infile1 = 'Hsap_AP1G_FourSeqs.fa' # CHANGE ME TO CHANGE TEST
        self.infile2 = 'Tgon_AP1_FourSeqs.fa'  # CHANGE ME TO CHANGE TEST
        ########################################

        self.infile1_base = self.infile1.split('.',1)[0]
        self.inpath1 = os.path.join(data_dir, self.infile1)

        self.infile2_base = self.infile2.split('.',1)[0]
        self.inpath2 = os.path.join(data_dir, self.infile2)

        self.sp = ScrollPy(
                self.tmpdir, # target_dir
                'Mafft', # align_method
                'RAxML', # dist_method
                *(self.inpath1,self.inpath2))


    def test_infile_parsing(self):
        """Tests that the infiles are correctly parsed"""
        self.sp._parse_infiles()
        self.assertEqual(self.sp._groups,
            [self.infile1_base, self.infile2_base])
        file1_ids = [o.id_num for o in self.sp._seq_dict[self.infile1_base]]
        file2_ids = [o.id_num for o in self.sp._seq_dict[self.infile2_base]]
        self.assertEqual(file1_ids, [1,2,3,4])
        self.assertEqual(file2_ids, [5,6,7,8])


    def test_actual_call(self):
        """Tests whether a call to ScrollPy with two objects works"""
        self.sp()
        self.assertEqual(len(self.sp._ordered_seqs), 8)


    def tearDown(self):
        """Remove tmp dir and all files"""
        shutil.rmtree(self.tmpdir)


#class TestScrollPyThreeFiles(unittest.TestCase):
#    """Tests each individual method with three files"""
#    pass
