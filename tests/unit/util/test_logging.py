"""
Tests /util/_logging.py

"""

import os
import unittest
import datetime
from unittest.mock import Mock
from unittest.mock import MagicMock
from unittest.mock import patch
import logging

from scrollpy.util import _logging as scroll_log


cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
# cleaner to use realpath due to relative path
data_dir = os.path.realpath(os.path.join(cur_dir, '../../fixtures')) # /tests/


class TestStandAloneFunctions(unittest.TestCase):
    """Tests functions in logging module"""

    @patch('scrollpy.util._logging.shutil')
    def test_get_current_terminal_width(self, mock_shutil):
        """Tests that the function returns right value"""
        mock_shutil.get_terminal_size.return_value = (20,10)
        self.assertEqual(
                scroll_log._get_current_terminal_width(),
                20,
                )

    def test_get_console_logger(self):
        """Tests that the name is correct"""
        cl = scroll_log.get_console_logger("scrollpy")
        self.assertIsInstance(cl, logging.Logger)
        self.assertEqual(cl.name, "C.scrollpy")

    def test_get_status_logger(self):
        """Tests that the name is correct"""
        sl = scroll_log.get_status_logger("scrollpy")
        self.assertIsInstance(sl, logging.Logger)
        self.assertEqual(sl.name, "S.scrollpy")

    def test_get_file_logger(self):
        """Tests that the name is correct"""
        fl = scroll_log.get_file_logger("scrollpy")
        self.assertIsInstance(fl, logging.Logger)
        self.assertEqual(fl.name, "F.scrollpy")

    def test_get_output_logger(self):
        """Tests that the name is correct"""
        ol = scroll_log.get_output_logger("scrollpy")
        self.assertIsInstance(ol, logging.Logger)
        self.assertEqual(ol.name, "O.scrollpy")

    @patch('scrollpy.util._logging.get_output_logger')
    @patch('scrollpy.util._logging.get_file_logger')
    @patch('scrollpy.util._logging.get_status_logger')
    @patch('scrollpy.util._logging.get_console_logger')
    def test_get_module_loggers(self, cl, sl, fl, ol):
        """Tests that the others are called correctly"""
        cl.return_value = "C.scrollpy"
        sl.return_value = "S.scrollpy"
        fl.return_value = "F.scrollpy"
        ol.return_value = "O.scrollpy"
        # Actually call function
        result = scroll_log.get_module_loggers("scrollpy")
        # Assert internal calls work
        cl.assert_called_once_with("scrollpy")
        sl.assert_called_once_with("scrollpy")
        fl.assert_called_once_with("scrollpy")
        ol.assert_called_once_with("scrollpy")
        # Check actual return value
        self.assertEqual(result,
                ("C.scrollpy","S.scrollpy","F.scrollpy","O.scrollpy"),
                )

    @patch('scrollpy.util._logging._get_temp_log_path')
    def test_get_logfile_not_logging(self, mock_tmp):
        """Tests that no log returns a temporary file"""
        mock_tmp.return_value = 'temp_log_path'
        self.assertEqual(
                scroll_log.get_logfile(not_logging=True),
                'temp_log_path',
                )
        mock_tmp.assert_called_once()

    @patch('scrollpy.util._logging.os.path.isfile')
    @patch('scrollpy.util._util.dir_exists')
    @patch('scrollpy.util._logging.os.path.join')
    @patch('scrollpy.util._util.is_value_ok_with_path')
    @patch('scrollpy.util._logging._get_real_logpath')
    def test_get_logfile_simple(self, mock_path, mock_isok, mock_join,
            mock_isdir, mock_isfile):
        """Tests that the right path is returned"""
        # Set the right return values
        mock_path.return_value = ('dir1','some_file.txt')
        mock_isok.return_value = True
        mock_join.return_value = 'dir1/some_file.txt'
        mock_isdir.return_value = True
        mock_isfile.return_value = False
        # Some actual things now
        expected_out = 'dir1/some_file.txt'
        # Feed these in
        path = scroll_log.get_logfile(
                logpath='some_file.txt',
                outdir='dir1',
                )
        # Check path
        self.assertEqual(path, expected_out)

    @patch('scrollpy.util._logging.os.path.isfile')
    @patch('scrollpy.util._util.dir_exists')
    @patch('scrollpy.util._logging.os.path.join')
    @patch('scrollpy.util._util.make_ok_with_path')
    @patch('scrollpy.util._util.is_value_ok_with_path')
    @patch('scrollpy.util._logging._get_real_logpath')
    def test_get_logfile_not_ok(self, mock_path, mock_isok, mock_makeok,
            mock_join, mock_isdir, mock_isfile):
        """Tests that the name is modified when not ok"""
        # Set the right return values
        mock_path.return_value = ('dir1','some_file.txt')
        mock_isok.return_value = False
        mock_makeok.return_value = 'some_file_ok.txt'
        mock_join.return_value = 'dir1/some_file_ok.txt'
        mock_isdir.return_value = True
        mock_isfile.return_value = False
        # Some actual things now
        expected_out = 'dir1/some_file_ok.txt'
        # Feed these in
        path = scroll_log.get_logfile(
                logpath='some_file.txt',
                outdir='dir1',
                )
        # Check path
        self.assertEqual(path, expected_out)

    @patch('scrollpy.util._logging._get_temp_log_path')
    @patch('scrollpy.util._util.dir_exists')
    @patch('scrollpy.util._logging.os.path.join')
    @patch('scrollpy.util._util.is_value_ok_with_path')
    @patch('scrollpy.util._logging._get_real_logpath')
    def test_get_logfile_dir_exists_no_create(self, mock_path, mock_isok,
            mock_join, mock_isdir, mock_tmp):
        """Tests that a temp logpath is created when no_create is True"""
        # Set the right return values
        mock_path.return_value = ('dir1','some_file.txt')
        mock_isok.return_value = True
        mock_join.return_value = 'dir1/some_file.txt'
        mock_isdir.return_value = False
        mock_tmp.return_value = 'tmp_logfile.txt'
        # Some actual things now
        expected_out = 'tmp_logfile.txt'
        # Feed these in
        path = scroll_log.get_logfile(
                logpath='some_file.txt',
                outdir='dir1',
                no_create=True,
                )
        # Check path
        self.assertEqual(path, expected_out)

    @patch('scrollpy.util._logging.os.path.isfile')
    @patch('scrollpy.util._util.ensure_dir_exists')
    @patch('scrollpy.util._util.dir_exists')
    @patch('scrollpy.util._logging.os.path.join')
    @patch('scrollpy.util._util.is_value_ok_with_path')
    @patch('scrollpy.util._logging._get_real_logpath')
    def test_get_logfile_dir_exists(self, mock_path, mock_isok,
            mock_join, mock_isdir, mock_exists, mock_isfile):
        """Tests that ensure_dir_exists is called"""
        # Set the right return values
        mock_path.return_value = ('dir1','some_file.txt')
        mock_isok.return_value = True
        mock_join.return_value = 'dir1/some_file.txt'
        mock_isdir.return_value = False
        mock_exists.return_value = None
        mock_isfile.return_value = False
        # Some actual things now
        expected_out = 'dir1/some_file.txt'
        # Feed these in
        path = scroll_log.get_logfile(
                logpath='some_file.txt',
                outdir='dir1',
                )
        # Check path
        self.assertEqual(path, expected_out)
        mock_exists.assert_called_once_with('dir1')

    @patch('scrollpy.util._util.get_nonredundant_filepath')
    @patch('scrollpy.util._logging.os.path.isfile')
    @patch('scrollpy.util._util.dir_exists')
    @patch('scrollpy.util._logging.os.path.join')
    @patch('scrollpy.util._util.is_value_ok_with_path')
    @patch('scrollpy.util._logging._get_real_logpath')
    def test_get_logfile_isfile_no_clobber(self, mock_path, mock_isok,
            mock_join, mock_exists, mock_isfile, mock_get_path):
        """Tests that get_nonredundant_filepath is called"""
        # Set the right return values
        mock_path.return_value = ('dir1','some_file.txt')
        mock_isok.return_value = True
        mock_join.return_value = 'dir1/some_file.txt'
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_get_path.return_value = 'dir1/some_file1.txt'
        # Some actual things now
        expected_out = 'dir1/some_file1.txt'
        # Feed these in
        path = scroll_log.get_logfile(
                logpath='some_file.txt',
                outdir='dir1',
                no_clobber = True
                )
        # Check path
        self.assertEqual(path, expected_out)
        mock_get_path.assert_called_once_with('dir1','some_file.txt')

    @patch('scrollpy.util._logging.os.remove')
    @patch('scrollpy.util._logging.os.path.isfile')
    @patch('scrollpy.util._util.dir_exists')
    @patch('scrollpy.util._logging.os.path.join')
    @patch('scrollpy.util._util.is_value_ok_with_path')
    @patch('scrollpy.util._logging._get_real_logpath')
    def test_get_logfile_isfile(self, mock_path, mock_isok,
            mock_join, mock_exists, mock_isfile, mock_rm):
        """Tests that os.remove is called"""
        # Set the right return values
        mock_path.return_value = ('dir1','some_file.txt')
        mock_isok.return_value = True
        mock_join.return_value = 'dir1/some_file.txt'
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_rm.side_effect = [None, OSError]
        # Some actual things now
        expected_out = 'dir1/some_file.txt'
        # Feed these in
        path = scroll_log.get_logfile(
                logpath='some_file.txt',
                outdir='dir1',
                )
        # Check path
        self.assertEqual(path, expected_out)
        mock_rm.assert_called_once_with('dir1/some_file.txt')
        # Check that the error is raised
        with self.assertRaises(SystemExit):
            scroll_log.get_logfile(logpath='')  # Args not important

    @patch('scrollpy.util._logging.os.path.split')
    @patch('scrollpy.util._logging.os.path.join')
    @patch('scrollpy.util._util.file_exists')
    def test_get_real_logpath_file_exists(self, mock_file_exists,
            mock_join, mock_split):
        """Tests that logfile as a file returns correctly"""
        # Set the right return values
        mock_file_exists.return_value = True
        mock_split.return_value = ('dir1','some_file.txt')
        mock_join.return_value = 'dir1/some_file.txt'
        # Some actual things now
        expected_out = ('dir1', 'some_file.txt')
        # Feed these in
        out_tup = scroll_log._get_real_logpath(
                logpath='some_file.txt',
                outdir='dir1',
                )
        # Check path
        self.assertEqual(out_tup, expected_out)
        mock_file_exists.assert_called_once_with('dir1/some_file.txt')

    @patch('scrollpy.util._logging._get_generic_logname')
    @patch('scrollpy.util._logging.os.path.join')
    @patch('scrollpy.util._util.dir_exists')
    @patch('scrollpy.util._util.file_exists')
    def test_get_real_logpath_dir_exists(self, mock_file_exists,
            mock_dir_exists, mock_join, mock_gname):
        """Tests that logfile as a dir returns correctly"""
        # Set the right return values
        mock_file_exists.return_value = False
        mock_dir_exists.return_value = True
        mock_join.return_value = 'dir1/'
        mock_gname.return_value = 'generic_logfile.txt'
        # Some actual things now
        expected_out = ('dir1/', 'generic_logfile.txt')
        # Feed these in
        out_tup = scroll_log._get_real_logpath(
                logpath='dir1/',
                outdir=None,
                )
        # Check path
        self.assertEqual(out_tup, expected_out)
        mock_dir_exists.assert_called_once_with('dir1/')

    @patch('scrollpy.util._logging._get_generic_logname')
    @patch('scrollpy.util._util.dir_exists')
    @patch('scrollpy.util._util.file_exists')
    def test_get_real_logpath_neither_exists(self, mock_file_exists,
            mock_dir_exists, mock_gname):
        """Tests that a nonexistent logpath returns correctly"""
        # Set the right return values
        mock_file_exists.return_value = False
        mock_dir_exists.return_value = False
        mock_gname.return_value = 'generic_logfile.txt'
        # Filename is
        with patch('scrollpy.util._logging.os.path.split') as mock_split1:
            mock_split1.return_value = ('dir1/', '')
            out_tup = scroll_log._get_real_logpath(
                    logpath='dir1/',
                    outdir='_',
                    )
            # Check path
            self.assertEqual(out_tup, ('dir1/', 'generic_logfile.txt'))
        # Filename is not ''
        with patch('scrollpy.util._logging.os.path.split') as mock_split2:
            mock_split2.return_value = ('dir1/', 'some_file.txt')
            out_tup = scroll_log._get_real_logpath(
                    logpath='dir1/',
                    outdir='_',
                    )
            # Check path
            self.assertEqual(out_tup, ('dir1/', 'some_file.txt'))

    @patch('scrollpy.util._logging._get_generic_logname')
    def test_get_real_logpath_neither_exists(self, mock_gname):
        """Tests that no logpath, but outdir, returns correctly"""
        # Set the right return values
        mock_gname.return_value = 'generic_logfile.txt'
        # Run the actual code
        out_tup = scroll_log._get_real_logpath(
                logpath=None,
                outdir='dir1/',
                )
        # Check path
        self.assertEqual(out_tup, ('dir1/', 'generic_logfile.txt'))

    @patch('scrollpy.util._logging.tempfile.NamedTemporaryFile')
    def test_get_temp_log_path(self, mock_tmpfile):
        """Tests that the right calls are invoked"""
        # Bind instance call to a mock
        tmp_instance = mock_tmpfile.return_value  # I.e. NamedTemporaryFile()
        tmp_instance.configure_mock(**{'name':'TempFile'})
        # Call function -> instantiates an instance
        tmp_name = scroll_log._get_temp_log_path()
        # Test assertions
        tmp_instance.close.assert_called_once()
        self.assertEqual(tmp_name, 'TempFile')

    @patch('scrollpy.util._logging.datetime')
    def test_get_generic_logname(self, mock_date):
        """Tests getting a generic logfile name"""
        # Module datetime is not mocked
        test_now = datetime.datetime(2020, 2, 6, 14, 25, 25, 188191)
        # Set the mock value to be the test value
        mock_date.datetime.now.return_value = test_now
        name = scroll_log._get_generic_logname()
        self.assertEqual(name,
                'scrollpy_2020-02-06-14-25-25_log.txt')

    @patch('scrollpy.util._logging.traceback.extract_tb')
    @patch('logging.Logger')
    def test_log_message(self, mock_logger, mock_stack):
        """Tests log_message with all levels"""
        mock_logger.side_effect = Mock  # Creates new mock instances
        l1 = mock_logger()
        l2 = mock_logger()
        loggers = (l1, l2)
        m_obj = Mock()
        # Call for DEBUG
        scroll_log.log_message(m_obj, 2, 'DEBUG', *loggers)
        l1.debug.assert_called_once_with(m_obj, extra={'vlevel':2})
        l2.debug.assert_called_once_with(m_obj, extra={'vlevel':2})
        # Call for INFO
        scroll_log.log_message(m_obj, 2, 'INFO', *loggers)
        l1.info.assert_called_once_with(m_obj, extra={'vlevel':2})
        l2.info.assert_called_once_with(m_obj, extra={'vlevel':2})
        # Call for WARNING
        scroll_log.log_message(m_obj, 2, 'WARNING', *loggers)
        l1.warning.assert_called_once_with(m_obj, extra={'vlevel':2})
        l2.warning.assert_called_once_with(m_obj, extra={'vlevel':2})
        # Call for ERROR
        scroll_log.log_message(m_obj, 2, 'ERROR', *loggers)
        l1.error.assert_called_once_with(m_obj, extra={'vlevel':2})
        l2.error.assert_called_once_with(m_obj, extra={'vlevel':2})
        # Call for EXCEPTION -> complicated
        # Set up the actual exception object
        e_attrs = {'__class__.__name__':'TypeError','__str__()':'Some error'}
        e_obj = MagicMock(**e_attrs)
        e_obj.__traceback__ = Mock()
        # Set up the traceback call and returns
        attrs = {'filename':'test_file','lineno':10}
        tb_stack = Mock(**attrs)
        tb_stack.configure_mock(name='some_func')  # Add name AFTER instantiation
        mock_stack.return_value = (tb_stack, '_')  # Second value doesn't matter
        # Call and assert good
        scroll_log.log_message(m_obj, 1, 'ERROR', *loggers, exc_obj=e_obj)
        l1.error.assert_called_with(m_obj, extra={'vlevel':1})
        l2.error.assert_called_with(m_obj, extra={'vlevel':1})
        # Now check the message object
        self.assertTrue(m_obj.exception)

    def test_log_newlines_low_nums(self):
        """Tests logging newlines when args are bad"""
        with self.assertRaises(ValueError):
            scroll_log.log_newlines(['l1','l2'],number=0)  # Number < 1
        with self.assertRaises(ValueError):
            scroll_log.log_newlines(['l1','l2'],number=-1)

    @patch('scrollpy.util._logging.BraceMessage')
    @patch('logging.Logger')
    def test_log_newlines(self, mock_logger, mock_msg):
        """Tests logging newlines when args are good"""
        mock_logger.side_effect = Mock  # Creates new mock instances
        l1 = mock_logger(handlers=[])
        l1.configure_mock(name='logger1')
        l2 = mock_logger(handlers=[])
        l2.configure_mock(name='logger2')
        loggers = (l1, l2)
        # Mock the BraceMessage again
        mock_msg.return_value = Mock
        # Log it
        scroll_log.log_newlines(*loggers, number=1)
        l1.info.assert_called_once_with(mock_msg(newline=True), extra={'vlevel':1})
        l2.info.assert_called_once_with(mock_msg(newline=True), extra={'vlevel':1})


# TO-DO
# class TestStreamOverwriter(unittest.TestCase):
#     """Tests the StreamOverwriter class"""

#     @classmethod
#     def setUpClass(cls):
#         """Use a single instance"""
#         cls.overwriter = scroll_log.StreamOverwriter()

#     @patch('scrollpy.util._logging._get_current_terminal_width')
#     @patch('logging.LogRecord')
#     def test_emit(self, mock_record, mock_width):
#         """Tests the emit method"""
#         record_attrs = {'msg':'A message to be logged'}
#         test_record = mock_record()
#         test_record.msg = "A message to be logged"
#         test_record.configure_mock(name="logger")
#         mock_width.return_value = 80
#         self.overwriter.emit(test_record)


class TestBraceMessage(unittest.TestCase):
    """Tests the BraceMessage class"""

    def setUp(self):
        """Create a new instance each test"""
        self.b_msg = scroll_log.BraceMessage(
                "A message with {} blank and {two} blank",
                'one',
                **{'two':'another'},
                )

    def test_string_wrapped(self):
        """Set the wrapped attribute and call __str__"""
        self.b_msg.wrapped = "A wrapped message"
        self.assertEqual(
                str(self.b_msg),
                "A wrapped message",
                )

    def test_string_not_wrapped(self):
        """Assume there is no wrapped attribute and call __str__"""
        self.assertEqual(
                str(self.b_msg),
                "A message with one blank and another blank",
                )

    def test_format_string(self):
        """Test string formatting; should return same as str()"""
        self.assertEqual(
                self.b_msg.format_string(self.b_msg.msg),
                "A message with one blank and another blank",
                )

    def test_get_msg(self):
        """Tests simple access method"""
        self.assertEqual(
                self.b_msg.get_msg(),
                self.b_msg.msg,
                )

    def test_add_wrapped(self):
        """Tests adding a wrapped msg"""
        wrapped_msg = "This is a wrapped msg"
        self.b_msg.add_wrapped(wrapped_msg)
        self.assertEqual(
                self.b_msg.wrapped,
                wrapped_msg,
                )

    def test_has_lines_no_lines(self):
        """Tests that a message with no lines returns False"""
        self.assertFalse(self.b_msg.has_lines())

    def test_has_lines_with_lines(self):
        """Tests that a message with lines returns True"""
        self.b_msg.lines = ["Some","lines","here"]
        self.assertTrue(self.b_msg.has_lines())

    def test_get_lines(self):
        """Tests simple access method"""
        lines = ["Some","lines","here"]
        self.b_msg.lines = lines
        self.assertEqual(
                self.b_msg.get_lines(),
                lines,
                )


class TestGenericFilter(unittest.TestCase):
    """Tests the GenericFilter class"""

    def setUp(self):
        """Create a new instance each test"""
        self.gfilter = scroll_log.GenericFilter(
                2,  # verbosity, the only required arg
                )

    def test_filter_silent(self):
        """Tests filtering when silent is True"""
        self.gfilter.silent = True
        self.assertFalse(self.gfilter.filter(""))

    def test_filter_no_silent_verbosity_ok(self):
        """Tests filtering when silent is False and message has low level"""
        mock_record = Mock()
        mock_record.vlevel = 1
        with self.assertRaises(AttributeError):
            self.gfilter.filter(mock_record)

    def test_filter_no_silent_verbosity_not_ok(self):
        """Tests filtering when silent is False and message has high level"""
        mock_record = Mock()
        mock_record.vlevel = 3
        self.assertFalse(self.gfilter.filter(mock_record))

    def test_modify_message(self):
        """Ensures subclass method raises AttributeError"""
        with self.assertRaises(AttributeError):
            self.gfilter._modify_message("")

    def test_format_message(self):
        """Ensures subclass method raises AttributeError"""
        with self.assertRaises(AttributeError):
            self.gfilter._format_message("")

    @patch('scrollpy.util._logging.textwrap.TextWrapper')
    def test_get_text_wrapper_no_width(self, mock_wrapper):
        """Tests the expected call to TextWrapper with no specified width"""
        self.gfilter._get_text_wrapper()
        mock_wrapper.assert_called_once_with(
                width=78,
                initial_indent='',
                subsequent_indent='          ',
                )

    @patch('scrollpy.util._logging.textwrap.TextWrapper')
    def test_get_text_wrapper_width(self, mock_wrapper):
        """Tests the expected call to TextWrapper with specified width"""
        self.gfilter._get_text_wrapper(width=20)
        mock_wrapper.assert_called_once_with(
                width=20,
                initial_indent='',
                subsequent_indent='          ',
                )

    def test_format_lines(self):
        """Ensures subclass method raises AttributeError"""
        with self.assertRaises(AttributeError):
            self.gfilter._format_lines("")

    def test_format_exception(self):
        """Ensures subclass method raises AttributeError"""
        with self.assertRaises(AttributeError):
            self.gfilter._format_exception("")


class TestConsoleFilter(unittest.TestCase):
    """Tests the ConsoleFilter class"""

    @patch('scrollpy.util._logging._get_current_terminal_width')
    def setUp(self, mock_width):
        """Create a new instance each test"""
        mock_width.return_value = 80  # Terminal width
        self.cfilter = scroll_log.ConsoleFilter(
                2,  # verbosity, the only required arg
                )

    def test_modify_message_exception(self):
        """Tests _modify_message when it has exception info"""
        # Patch with context manager to access self variables
        with patch.object(self.cfilter, '_format_exception') as mock_format:
            mock_format.return_value = None
            mock_record = Mock()
            mock_record.msg.exception = True  # Mock exc info
            # Call and check call
            self.cfilter._modify_message(mock_record)
            mock_format.assert_called_once_with(mock_record)

    def test_modify_message_lines(self):
        """Tests _modify_message when it has lines"""
        # Patch with context manager to access self variables
        with patch.object(self.cfilter, '_format_lines') as mock_format:
            mock_format.return_value = None
            mock_record = Mock()
            mock_record.msg.exception = False  # Otherwise created
            mock_record.msg.has_lines.return_value = True  # Mock having lines
            # Call and check call
            self.cfilter._modify_message(mock_record)
            mock_format.assert_called_once_with(mock_record)

    def test_modify_message_only(self):
        """Tests _modify_message when it has only a message"""
        # Patch with context manager to access self variables
        with patch.object(self.cfilter, '_format_message') as mock_format:
            mock_format.return_value = None
            mock_record = Mock()
            mock_record.msg.exception = False  # Otherwise created
            mock_record.msg.has_lines.return_value = False  # No lines
            # Call and check call
            self.cfilter._modify_message(mock_record)
            mock_format.assert_called_once_with(mock_record)

    def test_format_message_newlines(self):
        """Tests formatting a message with newlines"""
        mock_record = Mock()  # The record
        mock_msg = Mock()  # The record's msg
        mock_msg.newline = True  # Will be a newline
        mock_msg.get_msg.return_value = ""  # No actual message
        mock_record.msg = mock_msg  # Attach to parent mock
        # Call and check call
        self.cfilter._format_message(mock_record)
        mock_msg.add_wrapped.assert_called_once_with("")

    def test_format_message_normal(self):
        """Tests formatting a message with a normal message"""
        mock_record = Mock()  # The record
        mock_msg = Mock()  # The record's msg
        mock_msg.newline = False  # Not a newline
        mock_msg.get_msg.return_value = "A logged message"  # Message
        mock_msg.format_string.return_value = "Formatted message"
        mock_record.msg = mock_msg  # Attach to parent mock
        # Patch ConsoleFilter._add_header method
        with patch.object(self.cfilter, '_add_header') as mock_header:
            # Patch ConsoleFilter._add_header method
            # with patch.object(self.cfilter, '_get_text_wrapper.fill') as mock_wrapper:
            with patch('scrollpy.util._logging.textwrap.TextWrapper') as mock_wrapper:
                # Set return values
                mock_header.return_value = ('ScrollPy', 'Formatted message')
                mock_wrapper.return_value = Mock()  # Return value as a new mock
                # Set the fill() on the instance, not the class
                mock_wrapper().fill.return_value = 'ScrollPy: Formatted message'
                # Call and check call
                self.cfilter._format_message(mock_record)
                mock_msg.add_wrapped.assert_called_once_with(
                        'ScrollPy: Formatted message')

    def test_add_header(self):
        """Tests adding header"""
        string = 'A message.'
        # Test for level='INFO'
        self.assertEqual(
                self.cfilter._add_header('INFO', string),
                ('ScrollPy: ', 'ScrollPy: A message.'),  # header, formatted
                )
        # Test for level='WARNING'
        self.assertEqual(
                self.cfilter._add_header('WARNING', string),
                ('ScrollPy [WARNING]: ', 'ScrollPy [WARNING]: A message.'),
                )
        # Test for level='ERROR'
        self.assertEqual(
                self.cfilter._add_header('ERROR', string),
                ('ScrollPy [ERROR]: ', 'ScrollPy [ERROR]: A message.'),
                )

    # Not currently used, skip
    # def test_format_lines(self):
    #     """Tests formatting message lines"""
    #     pass

    def test_format_exception(self):
        """Tests formatting message with exception information"""
        mock_record = Mock()  # The record
        mock_msg = Mock()  # The record's msg
        # exc_msg is the last element of msg.lines
        mock_msg.get_lines.return_value = ['', 'An exception message']
        mock_msg.get_msg.return_value = ""  # Message, usually None
        mock_record.msg = mock_msg  # Attach to parent mock
        with patch.object(self.cfilter, '_format_message') as mock_format:
            mock_format.return_value = None
            # Call and check
            self.cfilter._format_exception(mock_record)
            self.assertEqual(mock_msg.msg, 'An exception message')
            mock_format.assert_called_once_with(mock_record)


class TestFileFilter(unittest.TestCase):
    """Tests the FileFilter class"""

    def setUp(self):
        """Create a new instance each test"""
        self.ffilter = scroll_log.FileFilter(
                2,  # verbosity, the only required arg
                )

    # FileFilter._modify_message same as ConsoleFilter, don't test
    # FileFilter._format_message same as ConsoleFilter, don't test

    @patch('scrollpy.util._logging.datetime')
    def test_get_header(self, mock_date):
        """Tests that the header is obtained correctly"""
        # Module datetime is not mocked
        test_now = datetime.datetime(2020, 2, 6, 14, 25, 25, 188191)
        # Set the mock value to be the test value
        mock_date.datetime.now.return_value = test_now
        # Mock a record
        mock_record = Mock()
        # Set the name AFTER instantiation
        mock_record.configure_mock(**{'name':'F.Scrollpy'})
        # Expected result
        fmtnow = ("{0:%Y-%m-%d-%H-%M-%S}".format(test_now))
        expected_header = "{asctime} | {name:^35} | {levelname:^10} |".format(
                asctime=fmtnow,
                name=mock_record.name,
                levelname='WARNING',  # Longest levelname option
                )
        self.assertEqual(
                self.ffilter._get_header(mock_record),
                expected_header,
                )

    def test_format_lines(self):
        """Tests formatting message lines"""
        mock_record = Mock()
        mock_msg = Mock()
        mock_msg.get_lines.return_value = ['A', 'message', 'in', 'lines']
        mock_record.msg = mock_msg
        with patch.object(self.ffilter, '_get_header') as mock_header:
            with patch('scrollpy.util._logging.textwrap.TextWrapper') as mock_wrapper:
                # Set return values
                mock_header.return_value = ('ScrollPy: ')
                mock_wrapper.return_value = Mock()  # Return value as a new mock
                # Set the fill() on the instance, not the class
                mock_wrapper().fill.return_value = 'ScrollPy: A message in lines'
                # Call and check call
                self.ffilter._format_lines(mock_record)
                mock_msg.add_wrapped.assert_called_once_with(
                        'ScrollPy: A message in lines')

    def test_format_exception(self):
        """Very simple -> tests that self._format_lines is called"""
        with patch.object(self.ffilter, '_format_lines') as mock_lines:
            self.ffilter._format_exception("")
            mock_lines.assert_called_once_with("")
