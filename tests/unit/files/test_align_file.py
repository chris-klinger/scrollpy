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

from scrollpy.files import align_file
from scrollpy.util._exceptions import FatalScrollPyError


class TestStandAloneFunctions(unittest.TestCase):
    """Tests all module functions"""

    @patch('scrollpy.files.align_file.file_logger')
    @patch('scrollpy.files.align_file.console_logger')
    @patch('scrollpy.util._logging.BraceMessage')
    @patch('scrollpy.util._logging.log_message')
    @patch('scrollpy.files.align_file._bio_align_to_dict')
    @patch('scrollpy.files.align_file.AlignIO')
    def test_parse_alignment_file(self, mock_align, mock_todict,
            mock_log, mock_bmsg, mock_cl, mock_fl):
        """Tests parsing file using BioPython"""
        # Default logged message
        mock_bmsg.return_value = "Mock Message"
        # Test most basic case
        mock_align.read.return_value = 'alignment'
        self.assertEqual(
                align_file.parse_alignment_file('_','_',to_dict=False),
                'alignment',
                )
        # Test when to_dict is True
        mock_todict.return_value = 'alignment as dict'
        self.assertEqual(
                align_file.parse_alignment_file('_','_'),
                'alignment as dict',
                )
        # Finally, check when it raises an error
        test_err = ValueError()
        mock_align.read.side_effect = test_err
        with self.assertRaises(FatalScrollPyError):
            align_file.parse_alignment_file('_','_')
        mock_bmsg.assert_called_with(
                "Could not read alignment from {}", '_')
        mock_log.assert_called_with(
                "Mock Message",
                1,
                'ERROR',
                mock_cl, mock_fl,
                exc_obj=test_err,
                )

    def test_bio_align_to_dict(self):
        """Tests transforming an AlignObj to a dict"""
        # Mock some records
        mock_record1 = Mock()
        mock_record2 = Mock()
        mock_record3 = Mock()
        mock_record1.configure_mock(**{'id' : 'id1', 'seq' : 'AGTC'})
        mock_record2.configure_mock(**{'id' : 'id2', 'seq' : 'GTAT'})
        mock_record3.configure_mock(**{'id' : 'id3', 'seq' : 'TTCA'})
        records = [mock_record1, mock_record2, mock_record3]
        # Mock an alignment object and iter over records
        mock_obj = MagicMock()
        mock_obj.__iter__.return_value = iter(records)
        # Test return value
        self.assertEqual(
                align_file._bio_align_to_dict(mock_obj),
                {'id1' : 'AGTC', 'id2' : 'GTAT', 'id3' : 'TTCA'},
                )

    @patch('scrollpy.files.align_file.AlignIO')
    def test_write_alignment_file(self, mock_align):
        """Tests writing an alignment file"""
        align_file.write_alignment_file(
                'alignment object',
                'some path',
                'fasta',
                )
        # Test that the call was good
        mock_align.write.assert_called_once_with(
                'alignment object',
                'some path',
                'fasta',
                )

    # SKIP CONVERSION FUNCTIONS FOR NOW!!!
