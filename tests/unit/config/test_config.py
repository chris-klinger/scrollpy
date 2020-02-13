"""
Tests the config module.

"""


import os
import unittest
from unittest.mock import Mock
from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import mock_open
from configparser import DuplicateSectionError
from configparser import DuplicateOptionError

from Bio.Application import ApplicationError

from scrollpy.config import _config
from scrollpy import load_config_file
from scrollpy.util._logging import BraceMessage
from scrollpy.util._exceptions import FatalScrollPyError

class TestConfig(unittest.TestCase):
    """Tests config module standalone functions"""

    @patch.object(_config, 'file_logger')  # Lookup path confused, patch on import
    @patch.object(_config, 'console_logger')
    @patch('scrollpy.util._logging.BraceMessage')
    @patch('scrollpy.util._logging.log_message')
    @patch.object(_config, 'config')
    def test_load_config_file(self, mock_config, mock_log,
            mock_bmsg, mock_cl, mock_fl):
        """Tests loading the config file"""
        mock_bmsg.return_value = "Mock Message"
        with patch.object(_config, 'open', mock_open()) as o:
            # Test when it raises IOError
            ioe = IOError()
            mock_config.read_file.side_effect = ioe
            with self.assertRaises(FatalScrollPyError):
                load_config_file()
            mock_bmsg.assert_called_with(
                    "Could not find or open config file")
            mock_log.assert_called_with(
                    "Mock Message",
                    1,
                    'ERROR',
                    mock_cl, mock_fl,
                    exc_obj=ioe,
                    )
            # Test with duplicate sections
            dse = DuplicateSectionError('dup_section')
            mock_config.read_file.side_effect = dse
            with self.assertRaises(FatalScrollPyError):
                load_config_file()
            mock_bmsg.assert_called_with(
                    "Duplicate config section {} detected",
                    'dup_section',
                    )
            mock_log.assert_called_with(
                    "Mock Message",
                    1,
                    'ERROR',
                    mock_cl, mock_fl,
                    exc_obj=dse,
                    )
            # Test with duplicate options
            doe = DuplicateOptionError('_','dup_option')
            mock_config.read_file.side_effect = doe
            with self.assertRaises(FatalScrollPyError):
                load_config_file()
            mock_bmsg.assert_called_with(
                    "Duplicate config option {} detected",
                    'dup_option',
                    )
            mock_log.assert_called_with(
                    "Mock Message",
                    1,
                    'ERROR',
                    mock_cl, mock_fl,
                    exc_obj=doe,
                    )
