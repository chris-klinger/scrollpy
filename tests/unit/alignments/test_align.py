"""
Tests different alignment options in align.py.

To start, tests should probably just align the file, write to tmp, and
then attemp to re-read the file and obtain a non-zero length for some
attribute of the BioPython AlignIO object.
"""

import os, unittest, shutil

from Bio import AlignIO

from scrollpy.alignments import align

cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
data_dir = os.path.join(cur_dir, '../../fixtures') # /tests/

class TestAlignment(unittest.TestCase):
    """Tests each alignment using an example file"""

    def setUp(self):
        """Makes a temporary directory in 'tests/fixtures'"""
        self.tmpdir = os.path.join(data_dir, 'tmp-align')
        os.makedirs(self.tmpdir)
        # Always use the same input file
        self.inpath = os.path.join(data_dir, 'Hsap_AP_EGADEZ.fa')

    def test_mafft_egadez(self):
        """Tests Mafft call if data is appropriate"""
        method = "Mafft"
        cmd = "mafft-linsi"
        outpath = os.path.join(self.tmpdir, 'mafft_test.afa')
        mafft_align = align.Aligner(method, cmd, self.inpath, outpath)
        mafft_align()
        # To test, re-parse file and check to ensure MSA object is not empty
        with open(outpath,'r') as i:
            test_alignment = AlignIO.read(i, "fasta")
        self.assertTrue(len(test_alignment) > 0)

    def tearDown(self):
        """Remove the directory"""
        shutil.rmtree(self.tmpdir)


if __name__ == '__main__':
    unittest.main()
