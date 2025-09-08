"""
Small test coverage for src/ai_guard/analyzer.py
"""
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os

# Import the analyzer module
from src.ai_guard.analyzer import (
    run,
    main,
    CodeAnalyzer,
)


class TestRunQualityGates(unittest.TestCase):
    """Test run_quality_gates function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('src.ai_guard.analyzer.subprocess.call')
    def test_run_quality_gates_lint_success(self, mock_call):
        """Test run_quality_gates with successful lint check."""
        mock_call.return_value = 0
        
        result = run_quality_gates("src", "output.json")
        
        self.assertTrue(result["lint"]["passed"])
        self.assertEqual(result["lint"]["exit_code"], 0)
        self.assertIn("flake8", result["lint"]["command"])
    
    @patch('src.ai_guard.analyzer.subprocess.call')
    def test_run_quality_gates_lint_failure(self, mock_call):
        """Test run_quality_gates with failed lint check."""
        mock_call.return_value = 1
        
        result = run_quality_gates("src", "output.json")
        
        self.assertFalse(result["lint"]["passed"])
        self.assertEqual(result["lint"]["exit_code"], 1)
        self.assertIn("flake8", result["lint"]["command"])
    
    @patch('src.ai_guard.analyzer.subprocess.call')
    def test_run_quality_gates_static_types_success(self, mock_call):
        """Test run_quality_gates with successful static types check."""
        mock_call.return_value = 0
        
        result = run_quality_gates("src", "output.json")
        
        self.assertTrue(result["static_types"]["passed"])
        self.assertEqual(result["static_types"]["exit_code"], 0)
        self.assertIn("mypy", result["static_types"]["command"])
    
    @patch('src.ai_guard.analyzer.subprocess.call')
    def test_run_quality_gates_static_types_failure(self, mock_call):
        """Test run_quality_gates with failed static types check."""
        mock_call.return_value = 1
        
        result = run_quality_gates("src", "output.json")
        
        self.assertFalse(result["static_types"]["passed"])
        self.assertEqual(result["static_types"]["exit_code"], 1)
        self.assertIn("mypy", result["static_types"]["command"])
    
    @patch('src.ai_guard.analyzer.subprocess.call')
    def test_run_quality_gates_security_success(self, mock_call):
        """Test run_quality_gates with successful security check."""
        mock_call.return_value = 0
        
        result = run_quality_gates("src", "output.json")
        
        self.assertTrue(result["security"]["passed"])
        self.assertEqual(result["security"]["exit_code"], 0)
        self.assertIn("bandit", result["security"]["command"])
    
    @patch('src.ai_guard.analyzer.subprocess.call')
    def test_run_quality_gates_security_failure(self, mock_call):
        """Test run_quality_gates with failed security check."""
        mock_call.return_value = 1
        
        result = run_quality_gates("src", "output.json")
        
        self.assertFalse(result["security"]["passed"])
        self.assertEqual(result["security"]["exit_code"], 1)
        self.assertIn("bandit", result["security"]["command"])
    
    @patch('src.ai_guard.analyzer.subprocess.call')
    def test_run_quality_gates_coverage_success(self, mock_call):
        """Test run_quality_gates with successful coverage check."""
        mock_call.return_value = 0
        
        result = run_quality_gates("src", "output.json")
        
        self.assertTrue(result["coverage"]["passed"])
        self.assertEqual(result["coverage"]["exit_code"], 0)
        self.assertIn("pytest", result["coverage"]["command"])
    
    @patch('src.ai_guard.analyzer.subprocess.call')
    def test_run_quality_gates_coverage_failure(self, mock_call):
        """Test run_quality_gates with failed coverage check."""
        mock_call.return_value = 1
        
        result = run_quality_gates("src", "output.json")
        
        self.assertFalse(result["coverage"]["passed"])
        self.assertEqual(result["coverage"]["exit_code"], 1)
        self.assertIn("pytest", result["coverage"]["command"])
    
    @patch('src.ai_guard.analyzer.subprocess.call')
    def test_run_quality_gates_all_checks(self, mock_call):
        """Test run_quality_gates with all checks."""
        mock_call.return_value = 0
        
        result = run_quality_gates("src", "output.json")
        
        # Check that all quality gates are present
        self.assertIn("lint", result)
        self.assertIn("static_types", result)
        self.assertIn("security", result)
        self.assertIn("coverage", result)
        
        # Check that all checks passed
        self.assertTrue(result["lint"]["passed"])
        self.assertTrue(result["static_types"]["passed"])
        self.assertTrue(result["security"]["passed"])
        self.assertTrue(result["coverage"]["passed"])
        
        # Check that subprocess.call was called for each check
        self.assertEqual(mock_call.call_count, 4)
    
    @patch('src.ai_guard.analyzer.subprocess.call')
    def test_run_quality_gates_mixed_results(self, mock_call):
        """Test run_quality_gates with mixed results."""
        # Mock different return values for different calls
        mock_call.side_effect = [0, 1, 0, 1]  # lint pass, static_types fail, security pass, coverage fail
        
        result = run_quality_gates("src", "output.json")
        
        # Check individual results
        self.assertTrue(result["lint"]["passed"])
        self.assertFalse(result["static_types"]["passed"])
        self.assertTrue(result["security"]["passed"])
        self.assertFalse(result["coverage"]["passed"])
        
        # Check exit codes
        self.assertEqual(result["lint"]["exit_code"], 0)
        self.assertEqual(result["static_types"]["exit_code"], 1)
        self.assertEqual(result["security"]["exit_code"], 0)
        self.assertEqual(result["coverage"]["exit_code"], 1)
    
    @patch('src.ai_guard.analyzer.subprocess.call')
    def test_run_quality_gates_custom_paths(self, mock_call):
        """Test run_quality_gates with custom paths."""
        mock_call.return_value = 0
        
        result = run_quality_gates("custom_src", "custom_output.json")
        
        # Check that custom paths are used in commands
        for check in ["lint", "static_types", "security", "coverage"]:
            self.assertIn("custom_src", result[check]["command"])
            self.assertIn("custom_output.json", result[check]["command"])
    
    @patch('src.ai_guard.analyzer.subprocess.call')
    def test_run_quality_gates_command_format(self, mock_call):
        """Test run_quality_gates command format."""
        mock_call.return_value = 0
        
        result = run_quality_gates("src", "output.json")
        
        # Check lint command format
        self.assertIn("flake8", result["lint"]["command"])
        self.assertIn("src", result["lint"]["command"])
        self.assertIn("--output-file=output.json", result["lint"]["command"])
        
        # Check static_types command format
        self.assertIn("mypy", result["static_types"]["command"])
        self.assertIn("src", result["static_types"]["command"])
        self.assertIn("--junit-xml=output.json", result["static_types"]["command"])
        
        # Check security command format
        self.assertIn("bandit", result["security"]["command"])
        self.assertIn("src", result["security"]["command"])
        self.assertIn("--format=json", result["security"]["command"])
        self.assertIn("--output=output.json", result["security"]["command"])
        
        # Check coverage command format
        self.assertIn("pytest", result["coverage"]["command"])
        self.assertIn("--cov=src", result["coverage"]["command"])
        self.assertIn("--cov-report=xml:output.json", result["coverage"]["command"])
    
    @patch('src.ai_guard.analyzer.subprocess.call')
    def test_run_quality_gates_exception_handling(self, mock_call):
        """Test run_quality_gates exception handling."""
        mock_call.side_effect = Exception("Subprocess error")
        
        result = run_quality_gates("src", "output.json")
        
        # Check that all checks failed due to exception
        for check in ["lint", "static_types", "security", "coverage"]:
            self.assertFalse(result[check]["passed"])
            self.assertEqual(result[check]["exit_code"], -1)
            self.assertIn("Subprocess error", result[check]["error"])


class TestRunSarifReport(unittest.TestCase):
    """Test run_sarif_report function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('src.ai_guard.analyzer.subprocess.call')
    def test_run_sarif_report_success(self, mock_call):
        """Test run_sarif_report with successful execution."""
        mock_call.return_value = 0
        
        result = run_sarif_report("src", "output.sarif")
        
        self.assertTrue(result["passed"])
        self.assertEqual(result["exit_code"], 0)
        self.assertIn("ai-guard", result["command"])
        self.assertIn("src", result["command"])
        self.assertIn("output.sarif", result["command"])
    
    @patch('src.ai_guard.analyzer.subprocess.call')
    def test_run_sarif_report_failure(self, mock_call):
        """Test run_sarif_report with failed execution."""
        mock_call.return_value = 1
        
        result = run_sarif_report("src", "output.sarif")
        
        self.assertFalse(result["passed"])
        self.assertEqual(result["exit_code"], 1)
        self.assertIn("ai-guard", result["command"])
        self.assertIn("src", result["command"])
        self.assertIn("output.sarif", result["command"])
    
    @patch('src.ai_guard.analyzer.subprocess.call')
    def test_run_sarif_report_custom_paths(self, mock_call):
        """Test run_sarif_report with custom paths."""
        mock_call.return_value = 0
        
        result = run_sarif_report("custom_src", "custom_output.sarif")
        
        self.assertIn("custom_src", result["command"])
        self.assertIn("custom_output.sarif", result["command"])
    
    @patch('src.ai_guard.analyzer.subprocess.call')
    def test_run_sarif_report_exception_handling(self, mock_call):
        """Test run_sarif_report exception handling."""
        mock_call.side_effect = Exception("Subprocess error")
        
        result = run_sarif_report("src", "output.sarif")
        
        self.assertFalse(result["passed"])
        self.assertEqual(result["exit_code"], -1)
        self.assertIn("Subprocess error", result["error"])


class TestMain(unittest.TestCase):
    """Test main function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('src.ai_guard.analyzer.run_quality_gates')
    @patch('src.ai_guard.analyzer.run_sarif_report')
    def test_main_quality_gates_only(self, mock_sarif, mock_quality):
        """Test main function with quality gates only."""
        mock_quality.return_value = {
            "lint": {"passed": True, "exit_code": 0, "command": "flake8 src"},
            "static_types": {"passed": True, "exit_code": 0, "command": "mypy src"},
            "security": {"passed": True, "exit_code": 0, "command": "bandit src"},
            "coverage": {"passed": True, "exit_code": 0, "command": "pytest --cov=src"}
        }
        
        with patch('sys.argv', ['analyzer.py', '--quality-gates', '--src', 'src', '--output', 'output.json']):
            result = main()
        
        self.assertEqual(result, 0)
        mock_quality.assert_called_once_with("src", "output.json")
        mock_sarif.assert_not_called()
    
    @patch('src.ai_guard.analyzer.run_quality_gates')
    @patch('src.ai_guard.analyzer.run_sarif_report')
    def test_main_sarif_only(self, mock_sarif, mock_quality):
        """Test main function with SARIF report only."""
        mock_sarif.return_value = {
            "passed": True,
            "exit_code": 0,
            "command": "ai-guard src output.sarif"
        }
        
        with patch('sys.argv', ['analyzer.py', '--sarif', '--src', 'src', '--output', 'output.sarif']):
            result = main()
        
        self.assertEqual(result, 0)
        mock_sarif.assert_called_once_with("src", "output.sarif")
        mock_quality.assert_not_called()
    
    @patch('src.ai_guard.analyzer.run_quality_gates')
    @patch('src.ai_guard.analyzer.run_sarif_report')
    def test_main_both_quality_gates_and_sarif(self, mock_sarif, mock_quality):
        """Test main function with both quality gates and SARIF report."""
        mock_quality.return_value = {
            "lint": {"passed": True, "exit_code": 0, "command": "flake8 src"},
            "static_types": {"passed": True, "exit_code": 0, "command": "mypy src"},
            "security": {"passed": True, "exit_code": 0, "command": "bandit src"},
            "coverage": {"passed": True, "exit_code": 0, "command": "pytest --cov=src"}
        }
        mock_sarif.return_value = {
            "passed": True,
            "exit_code": 0,
            "command": "ai-guard src output.sarif"
        }
        
        with patch('sys.argv', ['analyzer.py', '--quality-gates', '--sarif', '--src', 'src', '--output', 'output.json']):
            result = main()
        
        self.assertEqual(result, 0)
        mock_quality.assert_called_once_with("src", "output.json")
        mock_sarif.assert_called_once_with("src", "output.json")
    
    @patch('src.ai_guard.analyzer.run_quality_gates')
    @patch('src.ai_guard.analyzer.run_sarif_report')
    def test_main_quality_gates_failure(self, mock_sarif, mock_quality):
        """Test main function with quality gates failure."""
        mock_quality.return_value = {
            "lint": {"passed": False, "exit_code": 1, "command": "flake8 src"},
            "static_types": {"passed": True, "exit_code": 0, "command": "mypy src"},
            "security": {"passed": True, "exit_code": 0, "command": "bandit src"},
            "coverage": {"passed": True, "exit_code": 0, "command": "pytest --cov=src"}
        }
        
        with patch('sys.argv', ['analyzer.py', '--quality-gates', '--src', 'src', '--output', 'output.json']):
            result = main()
        
        self.assertEqual(result, 1)
        mock_quality.assert_called_once_with("src", "output.json")
        mock_sarif.assert_not_called()
    
    @patch('src.ai_guard.analyzer.run_quality_gates')
    @patch('src.ai_guard.analyzer.run_sarif_report')
    def test_main_sarif_failure(self, mock_sarif, mock_quality):
        """Test main function with SARIF report failure."""
        mock_sarif.return_value = {
            "passed": False,
            "exit_code": 1,
            "command": "ai-guard src output.sarif"
        }
        
        with patch('sys.argv', ['analyzer.py', '--sarif', '--src', 'src', '--output', 'output.sarif']):
            result = main()
        
        self.assertEqual(result, 1)
        mock_sarif.assert_called_once_with("src", "output.sarif")
        mock_quality.assert_not_called()
    
    @patch('src.ai_guard.analyzer.run_quality_gates')
    @patch('src.ai_guard.analyzer.run_sarif_report')
    def test_main_both_failure(self, mock_sarif, mock_quality):
        """Test main function with both quality gates and SARIF report failure."""
        mock_quality.return_value = {
            "lint": {"passed": False, "exit_code": 1, "command": "flake8 src"},
            "static_types": {"passed": True, "exit_code": 0, "command": "mypy src"},
            "security": {"passed": True, "exit_code": 0, "command": "bandit src"},
            "coverage": {"passed": True, "exit_code": 0, "command": "pytest --cov=src"}
        }
        mock_sarif.return_value = {
            "passed": False,
            "exit_code": 1,
            "command": "ai-guard src output.sarif"
        }
        
        with patch('sys.argv', ['analyzer.py', '--quality-gates', '--sarif', '--src', 'src', '--output', 'output.json']):
            result = main()
        
        self.assertEqual(result, 1)
        mock_quality.assert_called_once_with("src", "output.json")
        mock_sarif.assert_called_once_with("src", "output.json")
    
    @patch('src.ai_guard.analyzer.run_quality_gates')
    @patch('src.ai_guard.analyzer.run_sarif_report')
    def test_main_no_arguments(self, mock_sarif, mock_quality):
        """Test main function with no arguments."""
        with patch('sys.argv', ['analyzer.py']):
            result = main()
        
        self.assertEqual(result, 1)
        mock_quality.assert_not_called()
        mock_sarif.assert_not_called()
    
    @patch('src.ai_guard.analyzer.run_quality_gates')
    @patch('src.ai_guard.analyzer.run_sarif_report')
    def test_main_help(self, mock_sarif, mock_quality):
        """Test main function with help argument."""
        with patch('sys.argv', ['analyzer.py', '--help']):
            result = main()
        
        self.assertEqual(result, 0)
        mock_quality.assert_not_called()
        mock_sarif.assert_not_called()
    
    @patch('src.ai_guard.analyzer.run_quality_gates')
    @patch('src.ai_guard.analyzer.run_sarif_report')
    def test_main_version(self, mock_sarif, mock_quality):
        """Test main function with version argument."""
        with patch('sys.argv', ['analyzer.py', '--version']):
            result = main()
        
        self.assertEqual(result, 0)
        mock_quality.assert_not_called()
        mock_sarif.assert_not_called()
    
    @patch('src.ai_guard.analyzer.run_quality_gates')
    @patch('src.ai_guard.analyzer.run_sarif_report')
    def test_main_custom_paths(self, mock_sarif, mock_quality):
        """Test main function with custom paths."""
        mock_quality.return_value = {
            "lint": {"passed": True, "exit_code": 0, "command": "flake8 custom_src"},
            "static_types": {"passed": True, "exit_code": 0, "command": "mypy custom_src"},
            "security": {"passed": True, "exit_code": 0, "command": "bandit custom_src"},
            "coverage": {"passed": True, "exit_code": 0, "command": "pytest --cov=custom_src"}
        }
        
        with patch('sys.argv', ['analyzer.py', '--quality-gates', '--src', 'custom_src', '--output', 'custom_output.json']):
            result = main()
        
        self.assertEqual(result, 0)
        mock_quality.assert_called_once_with("custom_src", "custom_output.json")
        mock_sarif.assert_not_called()


if __name__ == '__main__':
    unittest.main()
