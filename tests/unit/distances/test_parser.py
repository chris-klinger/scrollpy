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
        self._raxml_dists = {
            'NP_001025178.1': 10.721104,
            'NP_001229766.1': 10.498028,
            'NP_003929.4': 12.769862999999999,
            'NP_031373.2': 11.398717}


    def test_raxml_parser(self):
        """Test RAxML parsing with direct call"""
        parsed_dict = parser._parse_raxml_distances(self._raxml_file)
        self.assertEqual(parsed_dict['NP_001025178.1'],
                self._raxml_dists['NP_001025178.1'])
        self.assertEqual(parsed_dict['NP_001229766.1'],
                self._raxml_dists['NP_001229766.1'])
        self.assertEqual(parsed_dict['NP_003929.4'],
                self._raxml_dists['NP_003929.4'])
        self.assertEqual(parsed_dict['NP_031373.2'],
                self._raxml_dists['NP_031373.2'])


    @unittest.skip("")
    def test_toplevel_raxml(self):
        """Tests that the main function delegates correctly"""
        parsed_dict = parser.parse_distance_file(
                self._raxml_file, # Same as before
                'RAxML'), # Specifies using _parse_raxml_distances
        self.assertEqual(parsed_dict['NP_001025178.1'],
                self._raxml_dists['NP_001025178.1'])
        self.assertEqual(parsed_dict['NP_001229766.1'],
                self._raxml_dists['NP_001229766.1'])
        self.assertEqual(parsed_dict['NP_003929.4'],
                self._raxml_dists['NP_003929.4'])
        self.assertEqual(parsed_dict['NP_031373.2'],
                self._raxml_dists['NP_031373.2'])


if __name__ == '__main__':
    unittest.main()
