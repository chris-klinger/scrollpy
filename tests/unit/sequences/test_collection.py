"""
Tests /sequences/_collection.py
"""

import os, unittest, shutil
from unittest.mock import Mock
from unittest.mock import MagicMock
from unittest.mock import patch
from configparser import DuplicateSectionError

from scrollpy import config
from scrollpy import load_config_file
from scrollpy.sequences._scrollseq import ScrollSeq
from scrollpy.sequences._collection import ScrollCollection
from scrollpy.files import sequence_file as sf

cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
# cleaner to use realpath due to relative path
data_dir = os.path.realpath(os.path.join(cur_dir, '../../fixtures')) # /tests/


class TestScrollCollection(unittest.TestCase):
    """Create a ScrollCollection object and test its methods"""

    @classmethod
    def setUpClass(cls):
        """Set up some external values across runs"""
        # Populate ARGS values of config file
        load_config_file()
        try:
            config.add_section('ARGS')
        except DuplicateSectionError:
            pass
        # Now provide sufficient arg defaults
        config['ARGS']['align_method'] = 'Mafft'
        config['ARGS']['align_matrix'] = 'Blosum62'
        config['ARGS']['dist_method'] = 'RAxML'
        config['ARGS']['dist_matrix'] = 'LG'
        # Mock some sequences to test
        mseq1 = Mock()
        mseq2 = Mock()
        mseq3 = Mock()
        cls.seq_list = [mseq1, mseq2, mseq3]

    def setUp(self):
        """Create an instance for each test"""
        # Create an instance for the class
        self.collection = ScrollCollection(
                'test_outdir',
                self.seq_list,
                'group1',
                )

    def test_repr(self):
        """Tests the ScrollCollection classes' __repr__ method"""
        expected = "ScrollCollection({!r}, {!r}, 'group1', None, **{})".format(
                self.collection._outdir,
                self.collection.seq_list,
                self.collection.kwargs,
                )
        self.assertEqual(expected, repr(self.collection))

    def test_str(self):
        """Tests the ScrollCollection classes' __str__ method"""
        # Test first without an opt_group
        expected = "ScrollCollection with one group: group1"
        self.assertEqual(expected, str(self.collection))
        # Now test with an opt_group
        self.collection._opt_group = 'group2'
        expected = "ScrollCollection with two groups: group1 and group2"
        self.assertEqual(expected, str(self.collection))

    @patch.object(ScrollCollection, '_increment_seq_distances')
    @patch.object(ScrollCollection, '_parse_distances')
    @patch.object(ScrollCollection, '_get_distances')
    @patch.object(ScrollCollection, '_get_alignment')
    @patch.object(ScrollCollection, '_get_sequence_file')
    def test_call(self, mock_getsf, mock_getaf, mock_getdf, mock_pdist, mock_incr):
        """Tests the ScrollCollection classes' __call__ method"""
        self.collection()
        # Test all assertions
        mock_getsf.assert_any_call()
        mock_getaf.assert_any_call()
        mock_getdf.assert_any_call()
        mock_pdist.assert_any_call()
        mock_incr.assert_any_call()

    @patch('scrollpy.sequences._collection.sf._sequence_list_to_file_by_id')
    @patch('scrollpy.util._util.get_filepath')
    def test_get_sequence_file(self, mock_path, mock_sltf):
        """Tests the _get_sequence_file method"""
        # Run
        self.collection._get_sequence_file()
        # Check assertions
        mock_path.assert_called_once_with(
                'test_outdir',
                'group1',
                'sequence',
                extra=None,
                seqfmt='fasta',
                )
        mock_sltf.assert_called_once_with(
                self.seq_list, mock_path.return_value)

    @patch('scrollpy.sequences._collection.Aligner')
    @patch('scrollpy.util._util.get_filepath')
    def test_get_alignment(self, mock_path, mock_align):
        """Tests the _get_alignment method"""
        config['ALIGNMENT']['Mafft'] = 'path/to/mafft'
        self.collection._seq_path = 'path/to/seqs'
        # Run
        self.collection._get_alignment()
        # Check assertions
        mock_path.assert_called_once_with(
                'test_outdir',
                'group1',
                'alignment',
                extra=None,
                alignfmt='fasta',
                )
        mock_align.assert_called_once_with(
                'Mafft',
                'path/to/mafft',
                inpath='path/to/seqs',
                outpath=mock_path.return_value,
                )
        mock_align.return_value.assert_called_once()  # Instance called

    @patch('scrollpy.sequences._collection.os.path')
    @patch('scrollpy.sequences._collection.DistanceCalc')
    @patch('scrollpy.util._util.get_filepath')
    def test_get_distances(self, mock_path, mock_dist, mock_os):
        """Tests the _get_distances method"""
        config['DISTANCE']['RAxML'] = 'path/to/raxml'
        self.collection._align_path = 'path/to/align'
        # Run
        self.collection._get_distances()
        # Check assertions
        mock_path.assert_called_once_with(
                'test_outdir',
                'group1',
                'distance',
                extra=None,
                distfmt='raxml',
                )
        mock_dist.assert_called_once_with(
                'RAxML',
                'path/to/raxml',
                inpath='path/to/align',
                outpath=mock_path.return_value,
                model='LG',
                )
        mock_dist.return_value.assert_called_once()  # Instance called

    @patch('scrollpy.sequences._collection.df.parse_distance_file')
    def test_parse_distances(self, mock_parse):
        """Tests the _parse_distances method"""
        self.collection._dist_path = 'path/to/dists'
        self.collection._parse_distances()
        # Check assertions
        mock_parse.assert_called_once_with(
                'path/to/dists',
                'RAxML',
                )

    def test_increment_seq_distances(self):
        """Tests the _increment_seq_distances method"""
        # Mock some sequences first
        mseq1 = MagicMock(**{'id_num' : 1})
        mseq2 = MagicMock(**{'id_num' : 2})
        mseq3 = MagicMock(**{'id_num' : 3})
        self.collection.seq_list = [mseq1, mseq2, mseq3]
        # Mock a dict
        self.collection._dist_dict = {
                '1' : 5, '2' : 6, '3': 7}
        # Call
        self.collection._increment_seq_distances()
        # Check assertions
        mseq1.__iadd__.assert_called_once_with(5)
        mseq2.__iadd__.assert_called_once_with(6)
        mseq3.__iadd__.assert_called_once_with(7)

