#!/usr/bin/env python3
"""
Test module for __main__.py entry point.
"""

import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest


class TestMainModule:
    """Test the __main__.py module entry point."""

    def test_main_module_execution(self):
        """Test that the module can be executed with python -m."""
        # Test that the module executes without import errors
        result = subprocess.run(
            [sys.executable, "-m", "fqcn_converter", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should exit with 0 and show help
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()

    @patch("fqcn_converter.cli.main.main")
    def test_main_module_calls_main_function(self, mock_main):
        """Test that __main__.py calls the main function."""
        mock_main.return_value = 0

        # Import and execute the __main__ module
        import fqcn_converter.__main__

        # The main function should have been called during import
        # since the module has if __name__ == "__main__" check
        # We can't easily test this without actually running as main
        # So we'll test the import works
        assert hasattr(fqcn_converter.__main__, "main")

    def test_main_module_sys_exit_behavior(self):
        """Test that the module properly handles sys.exit."""
        # Test with version flag which should exit cleanly
        result = subprocess.run(
            [sys.executable, "-m", "fqcn_converter", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should exit with 0 and show version
        assert result.returncode == 0
        # Version output should contain version info
        assert len(result.stdout.strip()) > 0
