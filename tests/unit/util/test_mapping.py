"""
Tests /util/_mapping.py
"""

import os, unittest, shutil
import warnings


from scrollpy import config
from scrollpy import load_config_file
from scrollpy.util import _mapping


cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
# cleaner to use realpath due to relative path
data_dir = os.path.realpath(os.path.join(cur_dir, '../../fixtures')) # /tests/

###################################
# Test standalone functions first #
###################################

class TestUniqueGroupName(unittest.TestCase):
    """Tests the _unique_group_name function"""

    def test_one_name(self):
        """Tests that name is returned unchanged"""
        name = _mapping._unique_group_name('Name')
        self.assertEqual(name, 'Name')


    def test_repeat_name(self):
        """Tests that repeat names adds suffix"""
        name1 = _mapping._unique_group_name('Other')
        name2 = _mapping._unique_group_name('Other')
        self.assertEqual(name1, 'Other')
        self.assertEqual(name2, 'Other.1')


    def test_multiple_redundant_groups(self):
        """Tests that function differentiates between groups"""
        name1 = _mapping._unique_group_name('One')
        name2 = _mapping._unique_group_name('Two')
        name3 = _mapping._unique_group_name('One')
        name4 = _mapping._unique_group_name('Two')
        # Check that it worked
        self.assertEqual(name1, 'One')
        self.assertEqual(name2, 'Two')
        self.assertEqual(name3, 'One.1')
        self.assertEqual(name4, 'Two.1')


    def test_repeat_multiple_times(self):
        """Tests that multiple repeats adds appropriate suffix"""
        name1 = _mapping._unique_group_name('Three')
        name2 = _mapping._unique_group_name('Three')
        name3 = _mapping._unique_group_name('Three')
        name4 = _mapping._unique_group_name('Three')
        # Check that it worked
        self.assertEqual(name1, 'Three')
        self.assertEqual(name2, 'Three.1')
        self.assertEqual(name3, 'Three.2')
        self.assertEqual(name4, 'Three.3')


class TestMakeAlignedSeqPairs(unittest.TestCase):
    """Tests the _make_aligned_seq_pairs function"""

    def test_align_equal_length(self):
        """Tests that equal length pairs are returned as-is"""
        # Here use a list instead of a set to keep order
        name_set = ['Homo sapiens','Bodo lentars']
        seq_pairs = [
                ('Homo sapiens','Homo sapiens'),
                ('Homo sapiens','Bodo lentars'),
                ]
        unaligned,aligned = _mapping._make_aligned_seq_pairs(
                'Homo sapiens',  # target_name
                name_set,
                )
        self.assertEqual(unaligned,seq_pairs)
        self.assertEqual(aligned,seq_pairs)


    def test_align_numbers(self):
        """Easiest case; check whether align works with numbers"""
        # Here use a list instead of a set to keep order
        name_set = ['123789','456789','123456']  # Set instead of list to keep order
        seq_pairs = [
                ('123456789','123---789'),
                ('123456789','4---56789'),  # First char won't be a gap
                ('123456789','123456---'),
                ]
        unaligned,aligned = _mapping._make_aligned_seq_pairs(
                '123456789',  # target_name
                name_set,
                )
        self.assertEqual(aligned,seq_pairs)


    def test_align_names(self):
        """Tests whether align works with letters"""
        # Here use a list instead of a set to keep order
        name_set = ['Homsapns','Homoiens','Homosaiens']
        seq_pairs = [
                ('Homosapiens','Hom---sapns'),  # Internal gaps here are hard
                ('Homosapiens','Homo---iens'),
                ('Homosapiens','Homosa-iens'),
                ]
        unaligned,aligned = _mapping._make_aligned_seq_pairs(
                'Homosapiens',  # target_name
                name_set,
                )
        self.assertEqual(aligned,seq_pairs)


class TestComparePairs(unittest.TestCase):
    """Tests the 'compare_pairs' function"""

    def test_compare_pairs_same(self):
        """Tests that an exact match is returned"""
        seq_pairs = [
                ('Homo sapiens','Arabidopsis thaliana'),
                ('Homo sapiens','Homo erectus'),
                ('Homo sapiens','Homo sapiens'),
                ]
        self.assertEqual(
                _mapping.compare_pairs(seq_pairs),
                ('Homo sapiens','Homo sapiens'),
                )


    def test_compare_pairs_close(self):
        """Tests that a close match is returned"""
        seq_pairs = [
                ('Homo sapiens','Arabidopsis thaliana'),
                ('Homo sapiens','Homo erectus'),
                ('Homo sapiens','Homo sap'),
                ]
        self.assertEqual(
                _mapping.compare_pairs(seq_pairs),
                ('Homo sapiens','Homo sap'),
                )


    def test_compare_pairs_duplicate(self):
        """Tests that the first match is returned by default"""
        seq_pairs = [
                ('Homo sapiens','Arabidopsis thaliana'),
                ('Homo sapiens','Homo erectus'),
                ('Homo sapiens','Homo sopitns'),
                ('Homo sapiens','Homo saliets'),
                ]
        self.assertEqual(
                _mapping.compare_pairs(seq_pairs),
                ('Homo sapiens','Homo sopitns'),
                )


class TestGetBestNameMatch(unittest.TestCase):
    """Tests the 'get_best_name_match' function"""

    @classmethod
    def setUpClass(cls):
        """Create a set of names to use for searching"""
        # Create a list instead of a set for order
        cls.test_names = [
                'Homo sapiens',
                'Homo erectus',
                'Arabidopsis thaliana',
                'Toxoplasma gondii',
                ]


    def test_get_best_name_match_exact(self):
        """Tests that the function performs membership testing correctly"""
        self.assertEqual(_mapping.get_best_name_match(
            'Homo sapiens',  # target_name
            self.test_names,  # name_set
            ),
            'Homo sapiens',
            )


    def test_get_best_name_match_partial(self):
        """Tests that the function matches partial strings correctly"""
        self.assertEqual(_mapping.get_best_name_match(
            'Homo sap',  # target_name
            self.test_names,  # name_set
            ),
            'Homo sapiens',
            )


    def test_get_best_name_match_same(self):
        """Tests that 'Homo' returns either 'Homo sapiens' or 'Homo erectus'"""
        self.assertEqual(_mapping.get_best_name_match(
            'Homo',  # target_name; could match either H. sap or H. ere
            self.test_names,  # name_set
            ),
            'Homo sapiens',
            )


#################################
# Test main Mapping class after #
#################################

class TestMappingOneFile(unittest.TestCase):
    """Tests Mapping class with one sequence file"""

    def setUp(self):
        """Creates a Mapping object based on an input file"""
        seq_file = os.path.join(data_dir, 'Hsap_AP_EGADEZ.fa')
        # Create necessary object
        self.mapping = _mapping.Mapping(
                seq_file,  # *infiles
                infmt='fasta',
                treefmt='newick',
                )


    def tearDown(self):
        """Removes Mapping object"""
        self.mapping = None


    def test_parse_infiles(self):
        """Tests parse with one infile

        Check that function correctly updates:
            mapping._records
            mapping._record_list
            mapping._seq_descriptions
        """
        self.mapping._parse_infiles(_test=True)
        expected_record_dict = {'Hsap_AP_EGADEZ': [
            'NP_001025178.1 AP-1 complex subunit gamma-1 isoform a [Homo sapiens]',
            'NP_001229766.1 AP-2 complex subunit alpha-2 isoform 1 [Homo sapiens]',
            'NP_003929.4 AP-3 complex subunit delta-1 isoform 2 [Homo sapiens]',
            'NP_031373.2 AP-4 complex subunit epsilon-1 isoform 1 [Homo sapiens]',
            'NP_055670.1 AP-5 complex subunit zeta-1 isoform 1 [Homo sapiens]',
            ]}
        expected_descriptions = [
            'NP_001025178.1 AP-1 complex subunit gamma-1 isoform a [Homo sapiens]',
            'NP_001229766.1 AP-2 complex subunit alpha-2 isoform 1 [Homo sapiens]',
            'NP_003929.4 AP-3 complex subunit delta-1 isoform 2 [Homo sapiens]',
            'NP_031373.2 AP-4 complex subunit epsilon-1 isoform 1 [Homo sapiens]',
            'NP_055670.1 AP-5 complex subunit zeta-1 isoform 1 [Homo sapiens]',
            ]
        self.assertEqual(self.mapping._records,expected_record_dict)
        self.assertEqual(self.mapping._seq_descriptions,expected_descriptions)


    def test_create_mapping_from_seq(self):
        """Tests _create_mapping_from_seqs with one file"""
        self.mapping._create_mapping_from_seqs()
        self.assertEqual(self.mapping._records,self.mapping._mapping)


    def test_get_scrollseq(self):
        """Tests _get_scrollseq function"""
        self.mapping._parse_infiles(_test=True)  # Populate object
        test_group = 'Hsap_AP_EGADEZ'
        test_label = 'NP_001025178.1 AP-1 complex subunit gamma-1 isoform a [Homo sapiens]'
        seq_obj = self.mapping._get_scrollseq(
                test_group,
                test_label,
                )
        self.assertEqual(seq_obj._group,test_group)
        self.assertEqual(seq_obj.description,test_label)


    def test_create_seq_dict(self):
        """Tests _create_seq_dict function"""
        self.mapping._parse_infiles(_test=True)  # Populate object
        self.mapping._create_mapping_from_seqs()  # Create mapping
        self.mapping._create_seq_dict()
        self.assertEqual(
                len(self.mapping._seq_dict['Hsap_AP_EGADEZ']), 5)


    def test_call(self):
        """Tests that all steps run fine with call"""
        self.mapping()
        self.assertEqual(
                len(self.mapping._seq_dict['Hsap_AP_EGADEZ']), 5)


class TestMappingTwoFiles(unittest.TestCase):
    """Tests Mapping class with two sequence files"""

    def setUp(self):
        """Creates a Mapping object based on an input file"""
        seq_file1 = os.path.join(data_dir, 'Hsap_AP_GA.fa')
        seq_file2 = os.path.join(data_dir, 'Hsap_AP_EDZ.fa')
        seq_files = (seq_file1, seq_file2)
        # Create necessary object
        self.mapping = _mapping.Mapping(
                *seq_files,  # *infiles
                infmt='fasta',
                treefmt='newick',
                )


    def tearDown(self):
        """Removes Mapping object"""
        self.mapping = None


    def test_parse_infiles(self):
        """Tests parse with one infile

        Check that function correctly updates:
            mapping._records
            mapping._record_list
            mapping._seq_descriptions
        """
        self.mapping._parse_infiles(_test=True)
        expected_record_dict = {
            'Hsap_AP_GA': [
            'NP_001025178.1 AP-1 complex subunit gamma-1 isoform a [Homo sapiens]',
            'NP_001229766.1 AP-2 complex subunit alpha-2 isoform 1 [Homo sapiens]',
            ],
            'Hsap_AP_EDZ': [
            'NP_003929.4 AP-3 complex subunit delta-1 isoform 2 [Homo sapiens]',
            'NP_031373.2 AP-4 complex subunit epsilon-1 isoform 1 [Homo sapiens]',
            'NP_055670.1 AP-5 complex subunit zeta-1 isoform 1 [Homo sapiens]',
            ]
            }
        expected_descriptions = [
            'NP_001025178.1 AP-1 complex subunit gamma-1 isoform a [Homo sapiens]',
            'NP_001229766.1 AP-2 complex subunit alpha-2 isoform 1 [Homo sapiens]',
            'NP_003929.4 AP-3 complex subunit delta-1 isoform 2 [Homo sapiens]',
            'NP_031373.2 AP-4 complex subunit epsilon-1 isoform 1 [Homo sapiens]',
            'NP_055670.1 AP-5 complex subunit zeta-1 isoform 1 [Homo sapiens]',
            ]
        self.assertEqual(self.mapping._records,expected_record_dict)


    def test_create_mapping_from_seqs(self):
        """Tests _create_mapping_from_seqs with one file"""
        self.mapping._create_mapping_from_seqs()
        self.assertEqual(self.mapping._records,self.mapping._mapping)


class TestMappingTreeFile(unittest.TestCase):
    """Tests Mapping class with a tree file"""

    def setUp(self):
        """Creates a Mapping object based on an input file"""
        tree_file = os.path.join(data_dir, 'Hsap_AP_EGADEZ.mfa.contree')
        # Create necessary object
        self.mapping = _mapping.Mapping(
                treefile=tree_file,
                infmt='fasta',
                treefmt='newick',
                )


    def tearDown(self):
        """Removes Mapping object"""
        self.mapping = None


    def test_parse_treefile(self):
        """Tests parsing a single tree file"""
        self.mapping._parse_treefile()
        # Expected leaf names - note, shortneded from input
        expected_labels = [
            'NP_001025178.1', 'NP_001229766.1', 'NP_003929.4',
            'NP_031373.2', 'NP_055670.1',
            ]
        # Actual tests
        self.assertEqual(len(self.mapping._leaves),5)  # Leaf objects
        self.assertEqual(self.mapping._leaf_names,expected_labels)


    def test_create_mapping_from_tree(self):
        """Tests creating a mapping from tree labels"""
        # Populate object
        self.mapping._parse_treefile()
        # Create mapping
        self.mapping._create_mapping_from_tree()
        # Expected values
        expected_dict = {'Hsap_AP_EGADEZ': [
            'NP_001025178.1', 'NP_001229766.1', 'NP_003929.4',
            'NP_031373.2', 'NP_055670.1',
            ]}
        # Actual tests
        self.assertEqual(self.mapping._mapping,expected_dict)


    def test_get_leafseq_exact_match(self):
        """Tests that leafseq objects are attained correctly"""
        # Populate object
        self.mapping._parse_treefile()
        # Get the actual object itself
        leaf_obj = self.mapping._get_leafseq(
                'Hsap_AP_EGADEZ',  # group name
                'NP_001025178.1',  # label name
                )
        # Test the retrieved object
        self.assertEqual(leaf_obj._group,'Hsap_AP_EGADEZ')
        self.assertEqual(leaf_obj._node.name,'NP_001025178.1')


    def test_get_leafseq_not_match(self):
        """Tests getting a leafseq when the label is not exactly the same"""
        # Populate object
        self.mapping._parse_treefile()
        # Get the actual object itself
        leaf_obj = self.mapping._get_leafseq(
                'Hsap_AP_EGADEZ',  # group name
                # Label name below; full name to match
                'NP_001025178.1 AP-1 complex subunit gamma-1 isoform a [Homo sapiens]',
                )
        # Test the retrieved object
        self.assertEqual(leaf_obj._group,'Hsap_AP_EGADEZ')
        self.assertEqual(leaf_obj._node.name,'NP_001025178.1')


    def test_create_seq_dict(self):
        """Tests creating a sequence dict with leaves only"""
        # Populate object
        self.mapping._parse_treefile()
        self.mapping._create_mapping_from_tree()
        # Expected labels
        expected_labels = [
            'NP_001025178.1', 'NP_001229766.1', 'NP_003929.4',
            'NP_031373.2', 'NP_055670.1',
            ]
        # Create the dict
        self.mapping._create_seq_dict()
        # Items to compare
        key = list(self.mapping._seq_dict.keys())[0]  # First and only entry
        obj_list = self.mapping._seq_dict[key]
        obtained_labels = [obj._node.name for obj in obj_list]
        # Actual tests
        self.assertEqual(key,'Hsap_AP_EGADEZ')
        self.assertEqual(obtained_labels,expected_labels)


class TestMappingTreePlusFiles(unittest.TestCase):
    """Tests Mapping class with both tree and sequence files"""

    def setUp(self):
        """Creates a Mapping object based on an input file"""
        seq_file1 = os.path.join(data_dir, 'Hsap_AP_GA.fa')
        seq_file2 = os.path.join(data_dir, 'Hsap_AP_EDZ.fa')
        seq_files = (seq_file1, seq_file2)
        tree_file = os.path.join(data_dir, 'Hsap_AP_EGADEZ.mfa.contree')
        # Create necessary object
        self.mapping = _mapping.Mapping(
                *seq_files,
                treefile=tree_file,
                infmt='fasta',
                treefmt='newick',
                )


    def tearDown(self):
        """Removes Mapping object"""
        self.mapping = None


    def test_create_seq_dict(self):
        """Tests seq_dict creation when both sequences and a tree are
        present. Need to ensure LeafSeq objects have ScrollSeqs"""
        # First populate object
        self.mapping._parse_infiles(_test=True)
        self.mapping._parse_treefile()
        self.mapping._create_mapping_from_seqs()
        # Run seq_dict funtion
        self.mapping._create_seq_dict()
        # Actual tests
        # print()
        # print(self.mapping._seq_dict)
        # print()
        self.assertEqual(len(self.mapping._seq_dict.keys()),2)
        for _,obj_list in self.mapping._seq_dict.items():
            for leaf_obj in obj_list:
                leaf_label = leaf_obj._node.name
                seq_label = leaf_obj._seq.name
                # Labels need to match!!!
                self.assertEqual(leaf_label,seq_label)


class TestMappingAllPlusMapping(unittest.TestCase):
    """Tests Mapping class with tree, sequence, and mapping files"""

    def setUp(self):
        """Creates a Mapping object based on an input file"""
        seq_file1 = os.path.join(data_dir, 'Hsap_AP_GA.fa')
        seq_file2 = os.path.join(data_dir, 'Hsap_AP_EDZ.fa')
        seq_files = (seq_file1, seq_file2)
        tree_file = os.path.join(data_dir, 'Hsap_AP_EGADEZ.mfa.contree')
        map_file = os.path.join(data_dir, 'Hsap_AP_mapping.txt')
        # Create necessary object
        self.mapping = _mapping.Mapping(
                *seq_files,
                treefile=tree_file,
                mapfile=map_file,
                infmt='fasta',
                treefmt='newick',
                )


    def tearDown(self):
        """Removes Mapping object"""
        self.mapping = None


    def test_create_mapping_from_mapfile(self):
        """Tests parsing of the mapfile"""
        self.mapping._create_mapping_from_mapfile()
        expected_dict = {'Hsap_AP': [
            'NP_001025178.1 AP-1 complex subunit gamma-1 isoform a [Homo sapiens]',
            'NP_001229766.1 AP-2 complex subunit alpha-2 isoform 1 [Homo sapiens]',
            'NP_003929.4 AP-3 complex subunit delta-1 isoform 2 [Homo sapiens]',
            'NP_031373.2 AP-4 complex subunit epsilon-1 isoform 1 [Homo sapiens]',
            'NP_055670.1 AP-5 complex subunit zeta-1 isoform 1 [Homo sapiens]',
            ]}
        self.assertEqual(self.mapping._mapping,expected_dict)


    def test_create_seq_dict(self):
        """Tests creating a seq dict when all files are present"""
        # First populate object
        self.mapping._parse_infiles(_test=True)
        self.mapping._parse_treefile()
        self.mapping._create_mapping_from_mapfile()
        # Create sequence dict
        self.mapping._create_seq_dict()
        # Test for accuracy
        self.assertEqual(len(self.mapping._seq_dict.keys()),1)
        for _,obj_list in self.mapping._seq_dict.items():
            for leaf_obj in obj_list:
                leaf_label = leaf_obj._node.name
                seq_label = leaf_obj._seq.name
                # Labels need to match!!!
                self.assertEqual(leaf_label,seq_label)

    def test_call(self):
        """Tests that calling the object works as expected"""
        self.mapping()
        for _,obj_list in self.mapping._seq_dict.items():
            for leaf_obj in obj_list:
                leaf_label = leaf_obj._node.name
                seq_label = leaf_obj._seq.name
                # Labels need to match!!!
                self.assertEqual(leaf_label,seq_label)

