#!/usr/bin/env python3
"""
Test module for CLI batch command.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from argparse import Namespace

from fqcn_converter.cli.batch import (
    add_batch_arguments,
    main
)


class TestBatchParser:
    """Test batch command parser."""

    def test_add_batch_arguments(self):
        """Test that batch arguments are added correctly."""
        import argparse
        parser = argparse.ArgumentParser()
        add_batch_arguments(parser)
        
        assert parser is not None
        assert hasattr(parser, 'parse_args')

    def test_batch_parser_required_args(self):
        """Test batch parser with required arguments."""
        import argparse
        parser = argparse.ArgumentParser()
        add_batch_arguments(parser)
        
        # Test with directory argument
        args = parser.parse_args(['/path/to/projects'])
        assert args.root_directory == '/path/to/projects'

    def test_batch_parser_optional_args(self):
        """Test batch parser with optional arguments."""
        import argparse
        parser = argparse.ArgumentParser()
        add_batch_arguments(parser)
        
        # Test with various optional arguments
        args = parser.parse_args([
            '/path/to/projects',
            '--dry-run',
            '--config', 'custom_config.yml',
            '--workers', '4'
        ])
        
        assert args.root_directory == '/path/to/projects'
        assert args.dry_run is True
        assert args.config == 'custom_config.yml'
        assert args.workers == 4

    def test_batch_parser_help(self):
        """Test that batch parser shows help."""
        import argparse
        parser = argparse.ArgumentParser()
        add_batch_arguments(parser)
        
        with pytest.raises(SystemExit):
            parser.parse_args(['--help'])


class TestBatchCommand:
    """Test batch command handling."""

    @patch('fqcn_converter.cli.batch.BatchCommand')
    def test_main_batch_command_basic(self, mock_command_class):
        """Test basic batch command handling."""
        # Mock command instance
        mock_command = MagicMock()
        mock_command.run.return_value = 0
        mock_command_class.return_value = mock_command
        
        # Create test arguments
        args = Namespace(
            root_directory='/path/to/projects',
            projects=None,
            dry_run=False,
            config=None,
            workers=None
        )
        
        # Should not raise exception
        result = main(args)
        
        # Verify command was called
        mock_command_class.assert_called_once_with(args)
        mock_command.run.assert_called_once()
        assert result == 0

    def test_batch_module_imports(self):
        """Test that batch module functions can be imported."""
        from fqcn_converter.cli.batch import add_batch_arguments, main
        
        assert callable(add_batch_arguments)
        assert callable(main)