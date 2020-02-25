"""
Tests scrollpy/files/align_file.py

"""

import os
import unittest
from subprocess import SubprocessError
from unittest.mock import Mock
from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import mock_open

from scrollpy.files import distance_file
from scrollpy.util._exceptions import FatalScrollPyError


cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
# cleaner to use realpath due to relative path
data_dir = os.path.realpath(os.path.join(cur_dir, '../../fixtures')) # /tests/

class TestStandAloneFunctions(unittest.TestCase):
    """Tests all module functions"""

    @patch('scrollpy.files.distance_file._parse_phyml_distances')
    @patch('scrollpy.files.distance_file._parse_raxml_distances')
    def test_parse_distance_file(self, mock_praxml, mock_pphyml):
        """Tests the parse_distance_file function"""
        # Call with RAxML
        distance_file.parse_distance_file('_', 'RAxML')
        mock_praxml.assert_called_once_with('_')
        # Call with PhyML
        distance_file.parse_distance_file('_', 'PhyML')
        mock_pphyml.assert_called_once_with('_')

    @patch('scrollpy.files.distance_file.file_logger')
    @patch('scrollpy.files.distance_file.console_logger')
    @patch('scrollpy.files.distance_file.BraceMessage')
    @patch('scrollpy.util._logging.log_message')
    def test_parse_alignment_file(self, mock_log, mock_bmsg, mock_cl, mock_fl):
        """Tests parsing file using BioPython"""
        # Default logged message
        mock_bmsg.return_value = "Mock Message"
        # Test with a real file first!
        test_inpath = os.path.join(data_dir, 'RAxML_distances.test_dist')
        expected = {
                'NP_001025178.1' : 10.721104,
                'NP_001229766.1' : 10.498028,
                'NP_003929.4'    : 12.769862999999999,
                'NP_031373.2'    : 11.398717,
                'NP_055670.1'    : 15.439106,
                }
        self.assertEqual(
                distance_file._parse_raxml_distances(test_inpath),
                expected,
                )
        # Finally, check when it raises an error
        with patch('scrollpy.util._util.non_blank_lines') as mock_nbl:
            mock_nbl.return_value = []  # Just an empty list
            with self.assertRaises(FatalScrollPyError):
                distance_file._parse_raxml_distances(test_inpath)
            mock_bmsg.assert_called_with(
                    "Could not read distances from {}", test_inpath)
            mock_log.assert_called_with(
                    "Mock Message",
                    1,
                    'ERROR',
                    mock_cl, mock_fl,
                    )
