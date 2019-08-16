"""
This module contains test code for distance.py
"""

import os, unittest, shutil

from scrollpy.distances import distance

cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
data_dir = os.path.join(cur_dir, '../../fixtures') # /tests/


class TestDistance(unittest.TestCase):
    """Tests each distance method using an example file"""

    def setUp(self):
        """Makes a temporary directory in 'tests/fixtures'"""
        self.tmpdir = os.path.join(data_dir, 'tmp-dist')
        os.makedirs(self.tmpdir)
        # Always use the same input file (ALIGNED!)
        self.inpath = os.path.join(data_dir, 'Hsap_AP_EGADEZ.mfa')


    def test_raxml_egadez(self):
        """Tests raxml call if data is appropriate"""
        method = "RAxML"
        cmd = "raxmlHPC-PTHREADS-AVX"
        outpath = os.path.join(self.tmpdir, 'test')
        options = {'-f':'x', # calculate distance
                '-p':12345, # parsimony seed
                '-m':'PROTGAMMALG'} # LG model
        raxml_dist = distance.DistanceCalc(method, cmd, 'LG', self.inpath,
                outpath, **options)
        raxml_dist()
        # To test, make sure file is not empty
        # Note: RAxML appends -n name to standard file name
        out_file = 'RAxML_distances.test'
        final_out = os.path.join(self.tmpdir, out_file)
        self.assertTrue(os.stat(final_out).st_size > 0)

    def tearDown(self):
        """Remove the directory"""
        shutil.rmtree(self.tmpdir)


if __name__ == '__main__':
    unittest.main()
