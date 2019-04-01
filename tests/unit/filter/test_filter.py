"""
This module contains code for testing sequence filtering.
"""


import unittest


from numpy import mean,median,std
from numpy import append as np_append
from numpy.random import seed,randn



# Need to mock some data
class MockSeq:
    def __init__(self, value):
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
    def setUpClass(TestFilterZScore):
        """Mock data and call an instance"""
        seq_dict = {}
        for i in range(4):
            label = "group" + str(i+1)
            seq_dict[label] = data



if __name__ == '__main__':
    lengths = _mock_data()
    m,s = mean(lengths),std(lengths)
    # Original data set does not contain any outliers by Z-score
    # Add some extreme values
    zlengths = np_append(lengths,[300, 400, 600, 700])
    outlier_vals = [l for l in zlengths if abs(l-m)/s >= 3]
    print(outlier_vals)
