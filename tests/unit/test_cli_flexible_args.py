"""
Test flexible argument parsing for global flags.

This module tests that global flags like --verbose, --quiet, --debug
can be placed anywhere in the command line.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys

from fqcn_converter.cli.main import preprocess_args, main


class TestFlexibleArgParsing:
    """Test flexible argument parsing functionality."""

    def test_preprocess_args_verbose_at_end(self):
        """Test that --verbose at the end is handled correctly."""
        args = ["convert", "playbook.yml", "--verbose"]
        processed_args, verbosity = preprocess_args(args)
        
        assert verbosity == "verbose"
        assert "--verbose" in processed_args
        assert "convert" in processed_args
        assert "playbook.yml" in processed_args

    def test_preprocess_args_verbose_at_beginning(self):
        """Test that --verbose at the beginning is handled correctly."""
        args = ["--verbose", "convert", "playbook.yml"]
        processed_args, verbosity = preprocess_args(args)
        
        assert verbosity == "verbose"
        assert "--verbose" in processed_args
        assert "convert" in processed_args
        assert "playbook.yml" in processed_args

    def test_preprocess_args_verbose_in_middle(self):
        """Test that --verbose in the middle is handled correctly."""
        args = ["convert", "--verbose", "--dry-run", "playbook.yml"]
        processed_args, verbosity = preprocess_args(args)
        
        assert verbosity == "verbose"
        assert "--verbose" in processed_args
        assert "convert" in processed_args
        assert "--dry-run" in processed_args
        assert "playbook.yml" in processed_args

    def test_preprocess_args_short_verbose(self):
        """Test that -v works in any position."""
        args = ["convert", "playbook.yml", "-v"]
        processed_args, verbosity = preprocess_args(args)
        
        assert verbosity == "verbose"
        assert "-v" in processed_args

    def test_preprocess_args_quiet_flag(self):
        """Test that --quiet works in any position."""
        args = ["convert", "--quiet", "playbook.yml"]
        processed_args, verbosity = preprocess_args(args)
        
        assert verbosity == "quiet"
        assert "--quiet" in processed_args

    def test_preprocess_args_debug_flag(self):
        """Test that --debug works in any position."""
        args = ["convert", "playbook.yml", "--debug"]
        processed_args, verbosity = preprocess_args(args)
        
        assert verbosity == "verbose"  # debug maps to verbose
        assert "--debug" in processed_args

    def test_preprocess_args_no_global_flags(self):
        """Test that commands without global flags work normally."""
        args = ["convert", "--dry-run", "playbook.yml"]
        processed_args, verbosity = preprocess_args(args)
        
        assert verbosity == "normal"
        assert processed_args == ["convert", "--dry-run", "playbook.yml"]

    def test_preprocess_args_version_flag(self):
        """Test that --version is preserved."""
        args = ["--version"]
        processed_args, verbosity = preprocess_args(args)
        
        assert "--version" in processed_args
        assert verbosity == "normal"

    @patch('fqcn_converter.cli.main.convert.main')
    @patch('fqcn_converter.cli.main.setup_logging')
    def test_main_with_flexible_verbose(self, mock_setup_logging, mock_convert_main):
        """Test that main() handles flexible verbose positioning."""
        mock_convert_main.return_value = 0
        
        # Test with verbose at the end
        with patch.object(sys, 'argv', ['fqcn-converter', 'convert', 'test.yml', '--verbose']):
            result = main()
            
        assert result == 0
        mock_setup_logging.assert_called_with("verbose")
        mock_convert_main.assert_called_once()

    @patch('fqcn_converter.cli.main.validate.main')
    @patch('fqcn_converter.cli.main.setup_logging')
    def test_main_with_flexible_quiet(self, mock_setup_logging, mock_validate_main):
        """Test that main() handles flexible quiet positioning."""
        mock_validate_main.return_value = 0
        
        # Test with quiet in the middle
        with patch.object(sys, 'argv', ['fqcn-converter', 'validate', '--quiet', 'test.yml']):
            result = main()
            
        assert result == 0
        mock_setup_logging.assert_called_with("quiet")
        mock_validate_main.assert_called_once()

    def test_preprocess_args_preserves_order(self):
        """Test that non-global arguments maintain their relative order."""
        args = ["convert", "--config", "custom.yml", "--verbose", "--dry-run", "playbook.yml"]
        processed_args, verbosity = preprocess_args(args)
        
        assert verbosity == "verbose"
        
        # Remove global flags and check order of remaining args
        non_global = [arg for arg in processed_args if arg not in ['--verbose', '-v', '--quiet', '-q', '--debug', '--version']]
        expected_order = ["convert", "--config", "custom.yml", "--dry-run", "playbook.yml"]
        assert non_global == expected_order