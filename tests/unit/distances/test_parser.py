"""
Tests functions found in the /distances/parser.py module.
"""

import os, unittest

from scrollpy.distances import parser

cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
data_dir = os.path.join(cur_dir, '../../fixtures') # /tests/


class TestParser(unittest.TestCase):
    """Tests parsing of different files"""

    def setUp(self):
        """Points to example files"""
        # Point to relevant files
        self._raxml_file = os.path.join(data_dir, 'RAxML_distances.test_dist')

        # Create lists to hold expected values for comparison
        self._raxml_dists = [
            ('NP_001025178.1','NP_001229766.1','1.804111'),
            ('NP_001025178.1','NP_003929.4','2.637399'),
            ('NP_001025178.1','NP_031373.2','2.298187'),
            ('NP_001025178.1','NP_055670.1','3.981407'),
            ('NP_001229766.1','NP_003929.4','2.826401'),
            ('NP_001229766.1','NP_031373.2','2.441114'),
            ('NP_001229766.1','NP_055670.1','3.426402'),
            ('NP_003929.4','NP_031373.2','2.967091'),
            ('NP_003929.4','NP_055670.1','4.338972'),
            ('NP_031373.2','NP_055670.1','3.692325')
            ]

    def test_raxml_parser(self):
        """Test RAxML parsing with direct call"""
        self.assertEqual(
            parser._parse_raxml_distances(self._raxml_file), # Calculated
            self._raxml_dists) # Taken straight from target file


    def test_toplevel_raxml(self):
        """Tests that the main function delegates correctly"""
        self.assertEqual(
            parser.parse_distance_file(
                self._raxml_file, # Same as before
                'RAxML'), # Specifies using _parse_raxml_distances
            self._raxml_dists)


if __name__ == '__main__':
    unittest.main()
