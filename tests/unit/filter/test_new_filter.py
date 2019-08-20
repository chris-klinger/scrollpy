"""
This module contains code for testing sequence filtering.
"""

import os
import unittest
import contextlib
from copy import deepcopy


from numpy import mean,median,std
from numpy import append as np_append
from numpy.random import seed,randn

from scrollpy.config._config import config,load_config_file
from scrollpy.filter._new_filter import Filter,LengthFilter,IdentityFilter


cur_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.realpath(os.path.join(cur_dir, '../../fixtures'))
load_config_file()

####################################
# Global mock objects for ScrollSeq #
####################################
class MockLengthSeq:
    def __init__(self, obj_id, value):
        self._id = obj_id
        self.value = value

    def __len__(self):
        return self.value


class MockSeq:
    def __init__(self, obj_id, sequence):
        self._id = obj_id
        self._seq = sequence


    def __len__(self):
        return len(self._seq)


    def _write_by_id(self, file_obj):
        """Mocks ScrollSeq _write_by_id() function"""
        from scrollpy.util._util import split_input  # imports cached on subsequent calls
        header = '>' + str(self._id)
        file_obj.write(header + '\n')
        for chunk in split_input(self._seq):
            file_obj.write(chunk + '\n')


class TestFilter(unittest.TestCase):
    pass


# Mock some uniform length data
def _mock_length_data():
    # seed generator to get same results
    seed(1)
    # generate 200 random values with mean 500 and stddev 10
    lengths = 10 * randn(200) + 500  # This does not have natural outliers!
    return lengths
length_data = _mock_length_data()


class TestLengthFilter(unittest.TestCase):
    """Tests length filtering implementation"""

    @classmethod
    def setUpClass(cls):
        # Mock unifrom distance objects and outliers
        cls.length_dict = {}
        for i in range(4):
            label = "group" + str(i+1)
            cls.length_dict[label] = length_data
        outliers = [300, 400, 600, 700]
        # Make ScrollSeq objects and add outliers
        cls.len_list = []
        cls.seq_list = []
        group_counter = 0
        for group_id,((k,v),new_val) in enumerate(zip(
                cls.length_dict.items(),
                outliers,
                )):
            length_list = list(np_append(v,[new_val]))
            for val_id,length in enumerate(length_list):
                cls.len_list.append(int(length))
                seq_obj = MockLengthSeq(
                        obj_id = "{}.{}".format(
                            group_id,
                            val_id),
                        value=int(length),
                        )
                cls.seq_list.append(seq_obj)
        # Finally, set up single class instance`
        cls.z_obj = LengthFilter(
                seq_list=cls.seq_list,
                method='zscore',
                filter_score=2,
                )


    def test_create_lengths_unordered(self):
        """Tests whether Filter._lengths is the same as cls.seq_dict lists"""
        z_obj = type(self).z_obj
        z_obj._create_lengths()
        self.assertEqual(z_obj._lengths,type(self).len_list)


    def test_get_removal_indices(self):
        """Tests logic for removal function"""
        z_obj = type(self).z_obj
        z_obj._indices = [("seq1","_"),("seq2","_"),("seq3","_")]
        values = [0.9,3,1.2]
        z_obj._get_removal_indices(values)
        self.assertEqual(z_obj._to_remove,[("seq2",3)])


    def test_calculate_zscores(self):
        """Test calculating zscores"""
        lengths = _mock_length_data()
        m,s = mean(lengths),std(lengths)
        zscores = [((abs(x-m))/s) for x in lengths]
        z_obj = type(self).z_obj
        z_zscores = z_obj.calculate_zscore(lengths)
        self.assertEqual(zscores,z_zscores)


class TestIdentityFilter(unittest.TestCase):
    """Tests alignment and removal by sequence identity"""

    @classmethod
    def setUpClass(cls):
        # Mock several sequences, two groups of similar
        cls.seq_list = []
        seqs = [
                'AGTCGTCAGTAGTCGAGTCTCAGTCTCC',  # 1 is similar to 2
                'AGTCGTCAGTAGTCGAGTCTCAGTCTCCG',  # 2 is similar to 1
                'ATGCTAGCGCTATAGATAGCTCGATAG',  # 3 is similar to 4 and 5
                'ATGCTAGCGCTATAGATAGCTCGATAGC',
                'ATGCTAGCGCTATAGATAGCTCGATAGCCC',
                ]
        # Make ScrollSeq objects and add outliers
        for i,seq in enumerate(seqs):
            seq_obj = MockSeq(
                    obj_id="seq{}".format(i),
                    sequence=seq,
                    )
            cls.seq_list.append(seq_obj)
        # Finally, set up single class instance`
        cls.z_obj = IdentityFilter(
                seq_list=cls.seq_list,
                method='identity',
                filter_score=98,
                outdir=data_dir,
                align_method='Mafft',
                )


    def test_get_filter_output(self):
        """Tests that function returns the right paths"""
        z_obj = type(self).z_obj
        self.assertEqual('/Users/cklinger/git/scrollpy/tests/fixtures/filter_seqs.fa',
                z_obj._get_filter_outpath('seqs'))
        self.assertEqual('/Users/cklinger/git/scrollpy/tests/fixtures/filter_seqs.mfa',
                z_obj._get_filter_outpath('align'))


    def test_make_tmp_seqfile(self):
        """Tests whether Filter._lengths is the same as cls.seq_dict lists"""
        z_obj = type(self).z_obj
        z_obj._make_tmp_seqfile()
        tmp_seq_dict = {}
        with open(os.path.join(data_dir, 'filter_seqs.fa'),'r') as i:
            for line in i:
                if line.startswith('>'):
                    header = line.strip('>').strip('\n')
                    tmp_seq_dict[header] = ''
                else:
                    tmp_seq_dict[header] = line.strip('\n')
        for k,v in tmp_seq_dict.items():
            index = int(k[-1])
            self.assertEqual(v, self.seq_list[index]._seq)


    def test_align_seqs(self):
        """Test that sequences are aligned as expected"""
        z_obj = type(self).z_obj
        z_obj._make_tmp_seqfile()
        z_obj._align_seqs()


    def test_build_identity_list(self):
        z_obj = type(self).z_obj
        identity_set = z_obj._build_identity_set()
        self.assertEqual(identity_set,
                {('seq0','seq1'),('seq2','seq3'),
                    ('seq2','seq4'),('seq3','seq4')})


    def test_remove_by_identity(self):
        z_obj = type(self).z_obj
        z_obj._remove_by_identity()
        self.assertEqual(len(z_obj._to_remove),3)


    @classmethod
    def tearDownClass(cls):
        """Remove all created files"""
        z_obj = cls.z_obj
        for created_file in ('_seq_path', '_align_path'):
            try:
                pathname = getattr(z_obj, created_file)
            except AttributeError:
                break
            with contextlib.suppress(FileNotFoundError):
                os.remove(pathname)


if __name__ == '__main__':
    lengths = _mock_length_data()
    m,s = mean(lengths),std(lengths)
    print([((abs(x-m))/s) for x in lengths])
    # Original data set does not contain any outliers by Z-score
    # Add some extreme values
    #zlengths = np_append(lengths,[300, 400, 600, 700])
    #outlier_vals = [l for l in zlengths if abs(l-m)/s >= 3]
    #print(outlier_vals)
