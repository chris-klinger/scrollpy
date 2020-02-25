"""
Tests all classes in applications/runner.py

"""

import os
import unittest
from subprocess import SubprocessError
from unittest.mock import Mock
from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import mock_open

from Bio.Application import ApplicationError

from scrollpy.applications import runner as r
from scrollpy.util._logging import BraceMessage
from scrollpy.util._exceptions import FatalScrollPyError
from scrollpy.util._exceptions import ValidationError


cur_dir = os.path.dirname(os.path.realpath(__file__)) # /files/
data_dir = os.path.join(cur_dir, '../../fixtures') # /tests/


class TestRunner(unittest.TestCase):
    """Tests the Runner BaseClass"""

    @classmethod
    def setUpClass(cls):
        """Set up a single instance for all tests"""
        with patch.object(r.Runner, '_validate') as mock_validate:
            mock_validate = True  # All __init__ validation calls pass
            cls.run_obj = r.Runner(
                    'method',  # I.e. method name
                    'cmd',     # Cmd string
                    'inpath',  # Input file path
                    'outpath', # Output file path
                    )

    @patch('scrollpy.applications.runner.file_logger')
    @patch('scrollpy.applications.runner.console_logger')
    @patch('scrollpy.applications.runner.BraceMessage')
    @patch('scrollpy.util._logging.log_message')
    def test_init_error_call(self, mock_log, mock_bmsg, mock_cl, mock_fl):
        """Tests that a new obj call with failed validate logs an error"""
        mock_bmsg.return_value = "Mock message"
        with patch.object(r.Runner, '_validate') as mock_validate:
            raised_error = ValidationError('_','_')
            mock_validate.side_effect = raised_error
            with self.assertRaises(FatalScrollPyError):
                fail_run = r.Runner(
                    'method',  # I.e. method name
                    'cmd',     # Cmd string
                    'inpath',  # Input file path
                    'outpath', # Output file path
                    )
        mock_log.assert_called_once_with(
                "Mock message",
                1,
                'ERROR',
                mock_cl, mock_fl,
                exc_obj=raised_error,
                )

    def test_repr(self):
        """Tests the Runner classes' __repr__ method"""
        self.assertEqual(
                repr(self.run_obj),
                # Single quotes, as str() repr adds quotes
                "Runner('method', 'cmd', 'inpath', 'outpath', None, **{})",
                )

    def test_str(self):
        """Tests the Runner classes' __str__ method"""
        self.assertEqual(
                str(self.run_obj),
                "Runner for running method",
                )

    def test_dunder_call(self):
        """Tests the Runner classes' __call__ method"""
        # First test with default
        with self.assertRaises(NotImplementedError):
            self.run_obj()
        # Override _call() to raise other errors
        with patch.object(r.Runner, '_call') as mock_call:
            mock_call.side_effect = ApplicationError(1, 'cmd')  # Required args
            with self.assertRaises(FatalScrollPyError):
                self.run_obj()
        with patch.object(r.Runner, '_call') as mock_call:
            mock_call.side_effect = SubprocessError()  # No required args
            with self.assertRaises(FatalScrollPyError):
                self.run_obj()

    def test_call(self):
        """Tests the Runner classes' _call method"""
        with self.assertRaises(NotImplementedError):
            self.run_obj._call()

    @patch('scrollpy.applications.runner.file_logger')
    @patch('scrollpy.applications.runner.console_logger')
    @patch('scrollpy.applications.runner.BraceMessage')
    @patch('scrollpy.util._logging.log_message')
    def test_validate(self, mock_log, mock_bmsg, mock_cl, mock_fl):
        """Tests the Runner classes' _validate method"""
        mock_bmsg.return_value = "Mock message"
        # First test when validation_method not provided
        with self.assertRaises(ValidationError):
            self.run_obj._validate('method', 'value', None)
        # For now, just test with one of the validation methods
        with patch.object(r.Runner, '_validate_method') as mock_validate:
            # Bind the right value for the method call
            to_call = self.run_obj._validate_method  # Passed method
            # Test when method raises FileNotFoundError
            raised_error = FileNotFoundError()
            mock_validate.side_effect = raised_error
            with self.assertRaises(ValidationError):
                self.run_obj._validate('method', 'value', to_call)
            mock_log.assert_called_with(
                    "Mock message",
                    1,
                    'ERROR',
                    mock_cl, mock_fl,
                    exc_obj=raised_error,
                    )
            # Test when method raises AttributeError
            raised_error = AttributeError()
            mock_validate.side_effect = raised_error
            with self.assertRaises(ValidationError):
                self.run_obj._validate('method', 'value', to_call)
            mock_log.assert_called_with(
                    "Mock message",
                    1,
                    'ERROR',
                    mock_cl, mock_fl,
                    exc_obj=raised_error,
                    )
            # Test when validation function gives a weird value
            mock_validate.return_value = 'WeirdValue'
            mock_validate.side_effect = None  # Remove side effect
            # Next line needed because application code calls validation_method.__name__
            mock_validate.configure_mock(**{'__name__':'_validate_method'})
            with self.assertRaises(ValidationError):
                self.run_obj._validate('method', 'value', to_call)
            mock_log.assert_called_with(
                    "Mock message",
                    1,
                    'ERROR',
                    mock_cl, mock_fl,
                    )
            # Finally, test when validation works
            mock_validate.return_value = True
            self.assertTrue(self.run_obj._validate('method','value',to_call))

    def test_validate_method(self):
        """Tests the Runner classes' _validate_method function"""
        # Test the base case, no methods
        with self.assertRaises(NotImplementedError):
            self.run_obj._validate_method('method')
        # Method name is valid
        self.run_obj._methods = ['method']
        self.assertTrue(self.run_obj._validate_method('method'))
        # Method name not valid
        self.assertFalse(self.run_obj._validate_method('other_method'))

    def test_validate_command(self):
        """Ensure BaseClass command raises NotImplementedError"""
        with self.assertRaises(NotImplementedError):
            self.run_obj._validate_command('cmd')

    @patch('scrollpy.applications.runner.file_logger')
    @patch('scrollpy.applications.runner.BraceMessage')
    @patch('scrollpy.util._logging.log_message')
    @patch('scrollpy.applications.runner.os.path')
    def test_validate_inpath(self, mock_path, mock_log, mock_bmsg, mock_fl):
        """Tests the Runner classes' _validate_inpath method"""
        # Tests when no file exists
        mock_path.exists.return_value = False
        with self.assertRaises(FileNotFoundError):
            self.run_obj._validate_inpath('_')
        # Tests when the path is a dir
        mock_path.exists.return_value = True
        mock_path.isdir.return_value = True
        with self.assertRaises(AttributeError):
            self.run_obj._validate_inpath('_')
        # Test otherwise
        mock_path.isdir.return_value = False
        mock_bmsg.return_value = "Mock message"
        self.assertTrue(self.run_obj._validate_inpath('_'))
        # Validate logging call
        mock_log.assert_called_once_with(
                "Mock message",
                2,
                'INFO',
                mock_fl,
                )

    @patch('scrollpy.applications.runner.file_logger')
    @patch('scrollpy.applications.runner.BraceMessage')
    @patch('scrollpy.util._logging.log_message')
    @patch('scrollpy.util._util.get_nonredundant_filepath')
    @patch('scrollpy.util._util.ensure_dir_exists')
    @patch('scrollpy.applications.runner.config')
    @patch('scrollpy.applications.runner.os.path.exists')
    def test_validate_outpath(self, mock_pexists, mock_config, mock_dexists,
            mock_rpath, mock_log, mock_bmsg, mock_fl):
        """Tests the Runner classes' _validate_outpath method"""
        # Make a fake path
        test_path = os.path.join('testdir','testname')
        # Make a fake log message
        mock_bmsg.return_value = "Mock message"
        # Test the method from top-down
        mock_config.__getitem__.return_value = {
                'no_create' : True, 'no_clobber' : True}
        mock_pexists.return_value = False
        with self.assertRaises(FileNotFoundError):
            self.run_obj._validate_outpath(test_path)
        # Same, but now no_create is False
        mock_config.__getitem__.return_value = {
                'no_create' : False, 'no_clobber' : True}
        # However, raise an error
        mock_dexists.side_effect = OSError()
        with self.assertRaises(FileNotFoundError):
            self.run_obj._validate_outpath(test_path)
        # Now, actually do something good
        mock_dexists.side_effect = None
        mock_dexists.return_value = True
        self.assertTrue(self.run_obj._validate_outpath(test_path))
        # Skip to elif block
        mock_pexists.return_value = True
        self.assertTrue(self.run_obj._validate_outpath(test_path))
        mock_rpath.assert_called_once_with('testdir','testname')
        # Now test when no_clobber is False
        mock_config.__getitem__.return_value = {
                'no_create' : False, 'no_clobber' : False}
        self.assertTrue(self.run_obj._validate_outpath(test_path))
        mock_log.assert_called_with(
                "Mock message",
                2,
                'INFO',
                mock_fl,
                )
        # Finally, test when the path is fine
        mock_pexists.return_value = False
        self.assertTrue(self.run_obj._validate_outpath(test_path))
        mock_log.assert_called_with(
                "Mock message",
                2,
                'INFO',
                mock_fl,
                )


class TestAligner(unittest.TestCase):
    """Tests the Aligner ConcreteClass"""

    @classmethod
    def setUpClass(cls):
        """Set up a single instance for all tests"""
        with patch.object(r.Aligner, '_validate') as mock_validate:
            mock_validate = True  # All __init__ validation calls pass
            cls.run_obj = r.Aligner(
                    'method',  # I.e. method name
                    'cmd',     # Cmd string
                    'inpath',  # Input file path
                    'outpath', # Output file path
                    )

    def test_call(self):
        """Tests the Aligner classes' _call method"""
        with patch.object(r.Aligner, '_run_mafft') as mock_mafft:
            self.run_obj.method = 'Mafft'
            self.run_obj._call()
            mock_mafft.assert_called_once()
        with patch.object(r.Aligner, '_run_mafftadd') as mock_mafftadd:
            self.run_obj.method = 'MafftAdd'
            self.run_obj._call()
            mock_mafftadd.assert_called_once()

    def test_validate_command(self):
        """Tests the Aligner classes' _validate_command method"""
        # Test if method is None
        self.assertFalse(self.run_obj._validate_command('_'))
        # Check for mafft
        self.assertTrue(self.run_obj._validate_command('mafft','Mafft'))
        self.assertTrue(self.run_obj._validate_command('mafft-linsi','Mafft'))
        # Check for mafft with bad command
        self.assertFalse(self.run_obj._validate_command('bad','Mafft'))
        # TO-DO: tests for other methods!

    @patch('scrollpy.applications.runner.AA')
    @patch('scrollpy.applications.runner.output_logger')
    @patch('scrollpy.applications.runner.console_logger')
    @patch('scrollpy.applications.runner.file_logger')
    @patch('scrollpy.applications.runner.BraceMessage')
    @patch('scrollpy.util._logging.log_message')
    def test_run_mafft(self, mock_log, mock_bmsg, mock_fl, mock_cl,
            mock_ol, mock_bioaa):
        """Tests the Aligner classes' _run_mafft method"""
        # Mock a bmsg
        mock_bmsg.return_value = "Mock message"
        # Test when the run raises an error
        test_err = ApplicationError(1, 'cmd')
        # Return value is the instance, side effect calls the instance
        mock_bioaa.MafftCommandline.return_value.side_effect = test_err
        with self.assertRaises(ApplicationError):
            self.run_obj._run_mafft()
        mock_log.assert_called_with(
                "Mock message",
                1,
                'ERROR',
                mock_cl, mock_fl,
                exc_obj=test_err,
                )
        # Check when no error is raised
        mock_bioaa.MafftCommandline.return_value.side_effect = None
        mock_bioaa.MafftCommandline.return_value.return_value = (
                'stdout',  # Expects a 2-member tuple
                'stderr',
                )
        # Patch open
        with patch('scrollpy.applications.runner.open', mock_open()) as o:
            self.run_obj._run_mafft()
            o.return_value.write.assert_called_with('stdout')
        # mock_bmsg.assert_called_with('stderr')
        # mock_log.assert_called_with(
        #         "Mock message",
        #         3,
        #         'INFO',
        #         mock_ol,
        #         )

    @patch('scrollpy.util._logging.log_message')
    @patch('scrollpy.applications.runner.subprocess.run')
    def test_run_mafftadd(self, mock_run, mock_log):
        """Like previous test, but only check for raised Error"""
        # Test when the run raises an error
        test_err = SubprocessError()
        # Return value is the instance, side effect calls the instance
        self.run_obj.cmd_list = []  # List gets value inserted
        mock_run.side_effect = test_err
        with self.assertRaises(SubprocessError):
            self.run_obj._run_mafftadd()

class TestAlignEvaluator(unittest.TestCase):
    """Tests the AlignEvaluator ConcreteClass"""

    @classmethod
    def setUpClass(cls):
        """Set up a single instance for all tests"""
        with patch.object(r.AlignEvaluator, '_validate') as mock_validate:
            mock_validate = True  # All __init__ validation calls pass
            cls.run_obj = r.AlignEvaluator(
                    'method',  # I.e. method name
                    'cmd',     # Cmd string
                    'inpath',  # Input file path
                    'outpath', # Output file path
                    )

    def test_call(self):
        """Tests the Aligner classes' _call method"""
        with patch.object(r.AlignEvaluator, '_run_zorro') as mock_zorro:
            self.run_obj.method = 'zorro'
            self.run_obj._call()
            mock_zorro.assert_called_once()

    def test_validate_command(self):
        """Tests the Aligner classes' _validate_command method"""
        # Test if method is None
        self.assertFalse(self.run_obj._validate_command('_'))
        # Check for zorro
        self.assertTrue(self.run_obj._validate_command('zorro','zorro'))
        self.assertTrue(self.run_obj._validate_command('zorro_mac','zorro'))
        # Check for mafft with bad command
        self.assertFalse(self.run_obj._validate_command('bad','zorro'))
        # TO-DO: tests for other methods!

    @patch('scrollpy.applications.runner.subprocess.run')
    @patch('scrollpy.applications.runner.output_logger')
    @patch('scrollpy.applications.runner.console_logger')
    @patch('scrollpy.applications.runner.file_logger')
    @patch('scrollpy.applications.runner.BraceMessage')
    @patch('scrollpy.util._logging.log_message')
    def test_run_mafft(self, mock_log, mock_bmsg, mock_fl, mock_cl,
            mock_ol, mock_run):
        """Tests the Aligner classes' _run_mafft method"""
        # Mock a bmsg
        mock_bmsg.return_value = "Mock message"
        # Add an instance list for cmds
        self.run_obj.cmd_list = []
        # Test when the run raises an error
        test_err = SubprocessError()
        # Return value is the instance, side effect calls the instance
        mock_run.side_effect = test_err
        with self.assertRaises(SubprocessError):
            self.run_obj._run_zorro()
        mock_log.assert_called_with(
                "Mock message",
                1,
                'ERROR',
                mock_cl, mock_fl,
                exc_obj=test_err,
                )
        # Check when no error is raised
        mock_run.side_effect = None
        mock_run.return_value = Mock()
        mock_run.return_value.configure_mock(**{
            'stdout' : Mock(), 'stderr' : Mock()})
        mock_run.return_value.stdout.decode.return_value = 'decoded stdout'
        mock_run.return_value.stderr.decode.return_value = 'decoded stderr'
        # Patch open
        with patch('scrollpy.applications.runner.open', mock_open()) as o:
            self.run_obj._run_zorro()
            o.return_value.write.assert_called_with('decoded stdout')
        # mock_bmsg.assert_called_with('decoded stderr')
        # mock_log.assert_called_with(
        #         "Mock message",
        #         3,
        #         'INFO',
        #         mock_ol,
        #         )

class TestDistanceCalc(unittest.TestCase):
    """Tests the DistanceCalc ConcreteClass"""

    @classmethod
    def setUpClass(cls):
        """Set up a single instance for all tests"""
        with patch.object(r.DistanceCalc, '_validate') as mock_validate:
            mock_validate.return_value = True  # All __init__ validation calls pass
            cls.run_obj = r.DistanceCalc(
                    'method',    # I.e. method name
                    'cmd',       # Cmd string
                    'inpath',    # Input file path
                    'outpath',   # Output file path
                    model='LG',  # Necessary model kwarg
                    )

    @patch('scrollpy.applications.runner.ValidationError')
    @patch('scrollpy.applications.runner.file_logger')
    @patch('scrollpy.applications.runner.console_logger')
    @patch('scrollpy.applications.runner.BraceMessage')
    @patch('scrollpy.util._logging.log_message')
    def test_init_error_call(self, mock_log, mock_bmsg, mock_cl,
            mock_fl, mock_valerr):
        """Tests that a new obj call with no model logs an error"""
        mock_bmsg.return_value = "Mock message"
        with patch.object(r.DistanceCalc, '_validate') as mock_validate:
            mock_valerr.return_value = ValidationError('_','_','')
            mock_validate.return_value = True
            with self.assertRaises(ValidationError):
                fail_run = r.DistanceCalc(
                    'method',  # I.e. method name
                    'cmd',     # Cmd string
                    'inpath',  # Input file path
                    'outpath', # Output file path
                    # No model or cmd_list!
                    )

    def test_call(self):
        """Tests the DistanceCalc classes' _call method"""
        with patch.object(r.DistanceCalc, '_run_raxml') as mock_raxml:
            self.run_obj.method = 'RAxML'
            self.run_obj._call()
            mock_raxml.assert_called_once()

    def test_validate_command(self):
        """Tests the DistanceCalc classes' _validate_command method"""
        # Test if method is None
        self.assertFalse(self.run_obj._validate_command('_'))
        # Check for zorro
        self.assertTrue(self.run_obj._validate_command('raxmlHPC-AVX','RAxML'))
        self.assertTrue(self.run_obj._validate_command('raxml-AVX','RAxML'))
        # Check for mafft with bad command
        self.assertFalse(self.run_obj._validate_command('bad','RAxML'))
        # TO-DO: tests for other methods!

    @patch('scrollpy.applications.runner.PA')
    @patch('scrollpy.applications.runner.output_logger')
    @patch('scrollpy.applications.runner.console_logger')
    @patch('scrollpy.applications.runner.file_logger')
    @patch('scrollpy.applications.runner.BraceMessage')
    @patch('scrollpy.util._logging.log_message')
    def test_run_raxml(self, mock_log, mock_bmsg, mock_fl, mock_cl,
            mock_ol, mock_biopa):
        """Tests the DistanceCalc classes' _run_raxml method"""
        # Mock a bmsg
        mock_bmsg.return_value = "Mock message"
        # Test when the run raises an error
        test_err = ApplicationError(1, 'cmd')
        # Return value is the instance, side effect calls the instance
        mock_biopa.RaxmlCommandline.return_value.side_effect = test_err
        with self.assertRaises(ApplicationError):
            self.run_obj._run_raxml()
        mock_log.assert_called_with(
                "Mock message",
                1,
                'ERROR',
                mock_cl, mock_fl,
                exc_obj=test_err,
                )
        # Check when no error is raised
        mock_biopa.RaxmlCommandline.return_value.side_effect = None
        mock_biopa.RaxmlCommandline.return_value.return_value = (
                'stdout',  # Expects a 2-member tuple
                'stderr',
                )
        # Patch open
        with patch('scrollpy.applications.runner.open', mock_open()) as o:
            self.run_obj._run_raxml()
            o.return_value.write.assert_called_with('stdout')
        # mock_bmsg.assert_called_with('stderr')
        # mock_log.assert_called_with(
        #         "Mock message",
        #         3,
        #         'INFO',
        #         mock_ol,
        #         )

class TestTreeBuilder(unittest.TestCase):
    """Tests the TreeBuilder ConcreteClass"""

    @classmethod
    def setUpClass(cls):
        """Set up a single instance for all tests"""
        with patch.object(r.TreeBuilder, '_validate') as mock_validate:
            mock_validate.return_value = True  # All __init__ validation calls pass
            cls.run_obj = r.TreeBuilder(
                    'method',    # I.e. method name
                    'cmd',       # Cmd string
                    'inpath',    # Input file path
                    'outpath',   # Output file path
                    model='LG',  # Necessary model kwarg
                    )

    @patch('scrollpy.applications.runner.ValidationError')
    @patch('scrollpy.applications.runner.file_logger')
    @patch('scrollpy.applications.runner.console_logger')
    @patch('scrollpy.applications.runner.BraceMessage')
    @patch('scrollpy.util._logging.log_message')
    def test_init_error_call(self, mock_log, mock_bmsg, mock_cl,
            mock_fl, mock_valerr):
        """Tests that a new obj call with no model logs an error"""
        mock_bmsg.return_value = "Mock message"
        with patch.object(r.TreeBuilder, '_validate') as mock_validate:
            mock_valerr.return_value = ValidationError('_','_','')
            mock_validate.return_value = True
            with self.assertRaises(ValidationError):
                fail_run = r.TreeBuilder(
                    'method',  # I.e. method name
                    'cmd',     # Cmd string
                    'inpath',  # Input file path
                    'outpath', # Output file path
                    # No model or cmd_list!
                    )

    def test_call(self):
        """Tests the TreeBuilder classes' _call method"""
        with patch.object(r.TreeBuilder, '_run_iqtree') as mock_iqtree:
            self.run_obj.method = 'Iqtree'
            self.run_obj._call()
            mock_iqtree.assert_called_once()
        with patch.object(r.TreeBuilder, '_run_raxml') as mock_raxml:
            self.run_obj.method = 'RAxML'
            self.run_obj._call()
            mock_raxml.assert_called_once()

    def test_validate_command(self):
        """Tests the DistanceCalc classes' _validate_command method"""
        # Test if method is None
        self.assertFalse(self.run_obj._validate_command('_'))
        # Check for Iqtree -> good command(s)
        self.assertTrue(self.run_obj._validate_command('iqtree','Iqtree'))
        # Check for Iqtree -> bad command
        self.assertFalse(self.run_obj._validate_command('bad','Iqtree'))
        # Check for RAxML -> good command(s)
        self.assertTrue(self.run_obj._validate_command('raxmlHPC-AVX','RAxML'))
        self.assertTrue(self.run_obj._validate_command('raxml-AVX','RAxML'))
        # Check for RAxML -> bad command
        self.assertFalse(self.run_obj._validate_command('bad','RAxML'))
        # TO-DO: tests for other methods!

    @patch('scrollpy.applications.runner.subprocess.run')
    @patch('scrollpy.applications.runner.output_logger')
    @patch('scrollpy.applications.runner.console_logger')
    @patch('scrollpy.applications.runner.file_logger')
    @patch('scrollpy.applications.runner.BraceMessage')
    @patch('scrollpy.util._logging.log_message')
    def test_run_iqtree(self, mock_log, mock_bmsg, mock_fl, mock_cl,
            mock_ol, mock_run):
        """Tests the Aligner classes' _run_mafft method"""
        # Mock a bmsg
        mock_bmsg.return_value = "Mock message"
        # Add an instance list for cmds
        self.run_obj.cmd_list = []
        # Test when the run raises an error
        test_err = SubprocessError()
        # Return value is the instance, side effect calls the instance
        mock_run.side_effect = test_err
        with self.assertRaises(SubprocessError):
            self.run_obj._run_iqtree()
        mock_log.assert_called_with(
                "Mock message",
                1,
                'ERROR',
                mock_cl, mock_fl,
                exc_obj=test_err,
                )
        # Check when no error is raised
        mock_run.side_effect = None
        mock_run.return_value = Mock()
        mock_run.return_value.configure_mock(**{
            'stdout' : Mock(), 'stderr' : Mock()})
        mock_run.return_value.stdout.decode.return_value = 'decoded stdout'
        mock_run.return_value.stderr.decode.return_value = 'decoded stderr'
        # Actually run method
        self.run_obj._run_iqtree()
        # Check logged output
        # mock_bmsg.assert_called_with('decoded stderr')
        # mock_log.assert_called_with(
        #         "Mock message",
        #         3,
        #         'INFO',
        #         mock_ol,
        #         )

    @patch('scrollpy.applications.runner.PA')
    @patch('scrollpy.applications.runner.output_logger')
    @patch('scrollpy.applications.runner.console_logger')
    @patch('scrollpy.applications.runner.file_logger')
    @patch('scrollpy.applications.runner.BraceMessage')
    @patch('scrollpy.util._logging.log_message')
    def test_run_raxml(self, mock_log, mock_bmsg, mock_fl, mock_cl,
            mock_ol, mock_biopa):
        """Tests the DistanceCalc classes' _run_raxml method"""
        # Mock a bmsg
        mock_bmsg.return_value = "Mock message"
        # Test when the run raises an error
        test_err = ApplicationError(1, 'cmd')
        # Return value is the instance, side effect calls the instance
        mock_biopa.RaxmlCommandline.return_value.side_effect = test_err
        with self.assertRaises(ApplicationError):
            self.run_obj._run_raxml()
        mock_log.assert_called_with(
                "Mock message",
                1,
                'ERROR',
                mock_cl, mock_fl,
                exc_obj=test_err,
                )
        # Check when no error is raised
        mock_biopa.RaxmlCommandline.return_value.side_effect = None
        mock_biopa.RaxmlCommandline.return_value.return_value = (
                'stdout',  # Expects a 2-member tuple
                'stderr',
                )
        # Patch open
        with patch('scrollpy.applications.runner.open', mock_open()) as o:
            self.run_obj._run_raxml()
            o.return_value.write.assert_called_with('stdout')
        # mock_bmsg.assert_called_with('stderr')
        # mock_log.assert_called_with(
        #         "Mock message",
        #         3,
        #         'INFO',
        #         mock_ol,
        #         )
