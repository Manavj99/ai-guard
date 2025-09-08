"""Basic tests for security_scanner.py."""

from unittest.mock import patch, mock_open
from ai_guard.security_scanner import SecurityScanner


def test_security_scanner_init():
    """Test SecurityScanner initialization."""
    scanner = SecurityScanner()
    assert scanner is not None


def test_scan_file_basic():
    """Test basic file scanning."""
    scanner = SecurityScanner()

    with patch("builtins.open", mock_open(read_data="import os")):
        result = scanner.scan_file("test.py")
        assert result is not None


def test_scan_file_with_vulnerability():
    """Test scanning file with potential vulnerability."""
    scanner = SecurityScanner()

    # File with potential security issue
    content = "password = 'hardcoded_password'"

    with patch("builtins.open", mock_open(read_data=content)):
        result = scanner.scan_file("test.py")
        assert result is not None


def test_scan_directory():
    """Test scanning directory."""
    scanner = SecurityScanner()

    with patch("os.walk") as mock_walk:
        mock_walk.return_value = [("", [], ["test.py"])]
        with patch.object(scanner, "scan_file", return_value={"issues": []}):
            result = scanner.scan_directory("test_dir")
            assert result is not None
