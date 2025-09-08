"""Comprehensive tests for __main__.py module to achieve high coverage."""

import unittest
from unittest.mock import patch, MagicMock
import sys
import argparse
from io import StringIO

from src.ai_guard.__main__ import main


class TestMainComprehensive(unittest.TestCase):
    """Comprehensive tests for the main CLI entry point."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_argv = sys.argv.copy()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

    def tearDown(self):
        """Clean up after tests."""
        sys.argv = self.original_argv
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

    @patch('src.ai_guard.__main__.run_analyzer')
    def test_main_basic_args(self, mock_run_analyzer):
        """Test main function with basic arguments."""
        sys.argv = ['ai-guard', '--min-cov', '85', '--skip-tests']
        
        main()
        
        # Verify run_analyzer was called
        mock_run_analyzer.assert_called_once()
        
        # Check that sys.argv was modified correctly
        expected_args = [
            'ai-guard',
            '--report-format', 'sarif',
            '--report-path', 'ai-guard.sarif',
            '--min-cov', '85',
            '--skip-tests'
        ]
        self.assertEqual(sys.argv, expected_args)

    @patch('src.ai_guard.__main__.run_analyzer')
    def test_main_with_event(self, mock_run_analyzer):
        """Test main function with event argument."""
        sys.argv = ['ai-guard', '--event', 'event.json']
        
        main()
        
        mock_run_analyzer.assert_called_once()
        
        expected_args = [
            'ai-guard',
            '--report-format', 'sarif',
            '--report-path', 'ai-guard.sarif',
            '--event', 'event.json'
        ]
        self.assertEqual(sys.argv, expected_args)

    @patch('src.ai_guard.__main__.run_analyzer')
    def test_main_with_report_format_json(self, mock_run_analyzer):
        """Test main function with JSON report format."""
        sys.argv = ['ai-guard', '--report-format', 'json']
        
        main()
        
        mock_run_analyzer.assert_called_once()
        
        expected_args = [
            'ai-guard',
            '--report-format', 'json',
            '--report-path', 'ai-guard.json'
        ]
        self.assertEqual(sys.argv, expected_args)

    @patch('src.ai_guard.__main__.run_analyzer')
    def test_main_with_report_format_html(self, mock_run_analyzer):
        """Test main function with HTML report format."""
        sys.argv = ['ai-guard', '--report-format', 'html']
        
        main()
        
        mock_run_analyzer.assert_called_once()
        
        expected_args = [
            'ai-guard',
            '--report-format', 'html',
            '--report-path', 'ai-guard.html'
        ]
        self.assertEqual(sys.argv, expected_args)

    @patch('src.ai_guard.__main__.run_analyzer')
    def test_main_with_custom_report_path(self, mock_run_analyzer):
        """Test main function with custom report path."""
        sys.argv = ['ai-guard', '--report-path', 'custom.sarif']
        
        main()
        
        mock_run_analyzer.assert_called_once()
        
        expected_args = [
            'ai-guard',
            '--report-format', 'sarif',
            '--report-path', 'custom.sarif'
        ]
        self.assertEqual(sys.argv, expected_args)

    @patch('src.ai_guard.__main__.run_analyzer')
    def test_main_with_deprecated_sarif_arg(self, mock_run_analyzer):
        """Test main function with deprecated --sarif argument."""
        sys.argv = ['ai-guard', '--sarif', 'deprecated.sarif']
        
        # Capture stderr output
        stderr_capture = StringIO()
        sys.stderr = stderr_capture
        
        main()
        
        mock_run_analyzer.assert_called_once()
        
        # Check warning message
        stderr_output = stderr_capture.getvalue()
        self.assertIn("--sarif is deprecated", stderr_output)
        self.assertIn("Use --report-format sarif --report-path PATH", stderr_output)
        
        # Check that arguments were set correctly
        expected_args = [
            'ai-guard',
            '--report-format', 'sarif',
            '--report-path', 'deprecated.sarif'
        ]
        self.assertEqual(sys.argv, expected_args)

    @patch('src.ai_guard.__main__.run_analyzer')
    def test_main_with_sarif_and_report_path(self, mock_run_analyzer):
        """Test main function with both --sarif and --report-path (report-path should take precedence)."""
        sys.argv = ['ai-guard', '--sarif', 'deprecated.sarif', '--report-path', 'preferred.sarif']
        
        main()
        
        mock_run_analyzer.assert_called_once()
        
        # Should use report-path, not sarif
        expected_args = [
            'ai-guard',
            '--report-format', 'sarif',
            '--report-path', 'preferred.sarif'
        ]
        self.assertEqual(sys.argv, expected_args)

    @patch('src.ai_guard.__main__.run_analyzer')
    def test_main_all_arguments(self, mock_run_analyzer):
        """Test main function with all possible arguments."""
        sys.argv = [
            'ai-guard',
            '--min-cov', '90',
            '--skip-tests',
            '--event', 'event.json',
            '--report-format', 'json',
            '--report-path', 'all-args.json'
        ]
        
        main()
        
        mock_run_analyzer.assert_called_once()
        
        expected_args = [
            'ai-guard',
            '--report-format', 'json',
            '--report-path', 'all-args.json',
            '--min-cov', '90',
            '--skip-tests',
            '--event', 'event.json'
        ]
        self.assertEqual(sys.argv, expected_args)

    @patch('src.ai_guard.__main__.run_analyzer')
    def test_main_no_arguments(self, mock_run_analyzer):
        """Test main function with no arguments."""
        sys.argv = ['ai-guard']
        
        main()
        
        mock_run_analyzer.assert_called_once()
        
        expected_args = [
            'ai-guard',
            '--report-format', 'sarif',
            '--report-path', 'ai-guard.sarif'
        ]
        self.assertEqual(sys.argv, expected_args)

    @patch('src.ai_guard.__main__.run_analyzer')
    def test_main_min_cov_none(self, mock_run_analyzer):
        """Test main function when min_cov is None (should not be added to args)."""
        sys.argv = ['ai-guard']
        
        main()
        
        mock_run_analyzer.assert_called_once()
        
        # Should not include --min-cov in args
        expected_args = [
            'ai-guard',
            '--report-format', 'sarif',
            '--report-path', 'ai-guard.sarif'
        ]
        self.assertEqual(sys.argv, expected_args)

    def test_argument_parser_creation(self):
        """Test that argument parser is created with correct configuration."""
        with patch('src.ai_guard.__main__.run_analyzer'):
            # We can't easily test the parser directly, but we can test that
            # the main function doesn't crash with various argument combinations
            test_cases = [
                ['ai-guard'],
                ['ai-guard', '--help'],
                ['ai-guard', '--min-cov', '80'],
                ['ai-guard', '--skip-tests'],
                ['ai-guard', '--event', 'test.json'],
                ['ai-guard', '--report-format', 'json'],
                ['ai-guard', '--report-path', 'test.sarif'],
                ['ai-guard', '--sarif', 'test.sarif'],
            ]
            
            for args in test_cases:
                with self.subTest(args=args):
                    sys.argv = args
                    try:
                        main()
                    except SystemExit:
                        # --help causes SystemExit, which is expected
                        pass

    @patch('src.ai_guard.__main__.run_analyzer')
    def test_main_sys_argv_preservation(self, mock_run_analyzer):
        """Test that sys.argv[0] is preserved when building analyzer arguments."""
        original_argv0 = 'original_script.py'
        sys.argv = [original_argv0, '--min-cov', '85']
        
        main()
        
        # Check that the first argument (script name) is preserved
        self.assertEqual(sys.argv[0], original_argv0)
        
        expected_args = [
            original_argv0,
            '--report-format', 'sarif',
            '--report-path', 'ai-guard.sarif',
            '--min-cov', '85'
        ]
        self.assertEqual(sys.argv, expected_args)


if __name__ == '__main__':
    unittest.main()