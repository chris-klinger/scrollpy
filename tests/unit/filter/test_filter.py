"""
This module contains code for testing sequence filtering.
"""


import unittest
from copy import deepcopy


from numpy import mean,median,std
from numpy import append as np_append
from numpy.random import seed,randn

from scrollpy.filter._filter import Filter

# Need to mock some data
class MockSeq:
    def __init__(self, obj_id, value):
        self._id = obj_id
        self.value = value

    def __len__(self):
        return self.value


def _mock_data():
    # seed generator to get same results
    seed(1)
    # generate 200 random values with mean 500 and stddev 10
    lengths = 10 * randn(200) + 500  # This does not have natural outliers!
    return lengths
data = _mock_data()


class TestFilterZScore(unittest.TestCase):
    """Tests the base implementation with Z-scores"""

    @classmethod
    def setUpClass(cls):
        # Mock unifrom distance objects and outliers
        cls.length_dict = {}
        for i in range(4):
            label = "group" + str(i+1)
            cls.length_dict[label] = data
        outliers = [300, 400, 600, 700]
        # Make ScrollSeq objects and add outliers
        cls.seq_dict = {}
        cls.len_list = []
        group_counter = 0
        for group_id,((k,v),new_val) in enumerate(zip(
                cls.length_dict.items(),
                outliers,
                )):
            length_list = list(np_append(v,[new_val]))
            for val_id,length in enumerate(length_list):
                cls.len_list.append(int(length))
                seq_obj = MockSeq(
                        obj_id = "{}.{}".format(
                            group_id,
                            val_id),
                        value=int(length),
                        )
                try:
                    cls.seq_dict[k].append(seq_obj)
                except KeyError:
                    cls.seq_dict[k] = []
                    cls.seq_dict[k].append(seq_obj)
        # Finally, set up single class instance`
        cls.z_obj = Filter(cls.seq_dict, filter_method='zscore')


    def test_create_lengths_unordered(self):
        """Tests whether Filter._lengths is the same as cls.seq_dict lists"""
        z_obj = type(self).z_obj
        z_obj._create_lengths()
        self.assertEqual(z_obj._lengths,type(self).len_list)


    def test_remove_by_index(self):
        """Test removing a value by index"""
        z_obj = type(self).z_obj
        index = 10
        # Get refs to the old values
        old_indices = z_obj._indices[:]
        old_lengths = z_obj._lengths[:]
        old_seq_dict = z_obj._seq_dict.copy()
        group,mock_obj,length = z_obj._indices[index]
        #print("Group, ID, and length are {},{},{}".format(
        #    group, mock_obj._id, length))  # group1, 0.10, and 514
        # Actually remove stuff
        z_obj._remove_by_index(index)
        # Now test that the new items are old - obj
        # INDICES
        del old_indices[index]
        self.assertEqual(z_obj._indices, old_indices)
        # LENGTHS
        del old_lengths[index]
        self.assertEqual(z_obj._lengths, old_lengths)
        # DICT
        old_seq_dict[group].pop(index)
        self.assertEqual(z_obj._seq_dict, old_seq_dict)
        # REMOVED DICTIONARY
        removed = {group:[mock_obj]}
        self.assertEqual(z_obj._removed, removed)


    def test_remove_by_indices(self):
        """Test removing a bunch of indices"""
        z_obj = type(self).z_obj
        other_z_obj = deepcopy(z_obj)
        indices = [2, 23]
        z_obj._remove_by_indices(indices)
        for index in indices:
            other_z_obj._remove_by_index(index)
        # Just checking lengths is probably fine
        self.assertEqual(z_obj._lengths,other_z_obj._lengths)


    def calculate_zscores(self):
        """Test calculating zscores"""
        pass


    def test_remove_by_zscores(self):
        """Test removing by zscore"""
        pass


if __name__ == '__main__':
    lengths = _mock_data()
    m,s = mean(lengths),std(lengths)
    # Original data set does not contain any outliers by Z-score
    # Add some extreme values
    zlengths = np_append(lengths,[300, 400, 600, 700])
    outlier_vals = [l for l in zlengths if abs(l-m)/s >= 3]
    print(outlier_vals)
