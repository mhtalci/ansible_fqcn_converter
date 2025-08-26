#!/usr/bin/env python3
"""
Test module for CLI convert command.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from argparse import Namespace

from fqcn_converter.cli.convert import (
    add_convert_arguments,
    main
)


class TestConvertParser:
    """Test convert command parser."""

    def test_add_convert_arguments(self):
        """Test that convert arguments are added correctly."""
        import argparse
        parser = argparse.ArgumentParser()
        add_convert_arguments(parser)
        
        assert parser is not None
        assert hasattr(parser, 'parse_args')

    def test_convert_parser_required_args(self):
        """Test convert parser with required arguments."""
        import argparse
        parser = argparse.ArgumentParser()
        add_convert_arguments(parser)
        
        # Test with files argument
        args = parser.parse_args(['test.yml'])
        assert args.files == ['test.yml']

    def test_convert_parser_optional_args(self):
        """Test convert parser with optional arguments."""
        import argparse
        parser = argparse.ArgumentParser()
        add_convert_arguments(parser)
        
        # Test with various optional arguments
        args = parser.parse_args([
            'test.yml',
            '--dry-run',
            '--config', 'custom_config.yml',
            '--backup'
        ])
        
        assert args.files == ['test.yml']
        assert args.dry_run is True
        assert args.config == 'custom_config.yml'
        assert args.backup is True

    def test_convert_parser_help(self):
        """Test that convert parser shows help."""
        import argparse
        parser = argparse.ArgumentParser()
        add_convert_arguments(parser)
        
        with pytest.raises(SystemExit):
            parser.parse_args(['--help'])


class TestConvertCommand:
    """Test convert command handling."""

    @patch('fqcn_converter.cli.convert.ConvertCommand')
    def test_main_convert_command_basic(self, mock_command_class):
        """Test basic convert command handling."""
        # Mock command instance
        mock_command = MagicMock()
        mock_command.run.return_value = 0
        mock_command_class.return_value = mock_command
        
        # Create test arguments
        args = Namespace(
            files=['test.yml'],
            dry_run=False,
            config=None,
            backup=False
        )
        
        # Should not raise exception
        result = main(args)
        
        # Verify command was called
        mock_command_class.assert_called_once_with(args)
        mock_command.run.assert_called_once()
        assert result == 0

    def test_convert_module_imports(self):
        """Test that convert module functions can be imported."""
        from fqcn_converter.cli.convert import add_convert_arguments, main
        
        assert callable(add_convert_arguments)
        assert callable(main)