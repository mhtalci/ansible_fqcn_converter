"""
Unit tests for CLI main module.

Comprehensive test suite covering CLI argument parsing, logging setup,
and command routing with mock file system operations.
"""

import pytest
import argparse
import logging
import sys
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from fqcn_converter.cli.main import (
    setup_logging,
    create_parser,
    main
)


class TestSetupLogging:
    """Test cases for logging setup functionality."""
    
    def test_setup_logging_quiet(self):
        """Test logging setup with quiet verbosity."""
        with patch('logging.basicConfig') as mock_config:
            setup_logging('quiet')
            
            mock_config.assert_called_once()
            args, kwargs = mock_config.call_args
            assert kwargs['level'] == logging.ERROR
    
    def test_setup_logging_normal(self):
        """Test logging setup with normal verbosity."""
        with patch('logging.basicConfig') as mock_config:
            setup_logging('normal')
            
            mock_config.assert_called_once()
            args, kwargs = mock_config.call_args
            assert kwargs['level'] == logging.INFO
    
    def test_setup_logging_verbose(self):
        """Test logging setup with verbose verbosity."""
        with patch('logging.basicConfig') as mock_config:
            setup_logging('verbose')
            
            mock_config.assert_called_once()
            args, kwargs = mock_config.call_args
            assert kwargs['level'] == logging.DEBUG
    
    def test_setup_logging_invalid_level(self):
        """Test logging setup with invalid verbosity level."""
        with patch('logging.basicConfig') as mock_config:
            setup_logging('invalid')
            
            mock_config.assert_called_once()
            args, kwargs = mock_config.call_args
            assert kwargs['level'] == logging.INFO  # Default to INFO
    
    def test_setup_logging_third_party_suppression(self):
        """Test that third-party library logging is suppressed in non-debug mode."""
        with patch('logging.basicConfig'), \
             patch('logging.getLogger') as mock_get_logger:
            
            mock_urllib3_logger = Mock()
            mock_requests_logger = Mock()
            mock_get_logger.side_effect = lambda name: {
                'urllib3': mock_urllib3_logger,
                'requests': mock_requests_logger
            }.get(name, Mock())
            
            setup_logging('normal')
            
            # Should suppress third-party loggers
            mock_urllib3_logger.setLevel.assert_called_with(logging.WARNING)
            mock_requests_logger.setLevel.assert_called_with(logging.WARNING)
    
    def test_setup_logging_debug_no_suppression(self):
        """Test that third-party library logging is not suppressed in debug mode."""
        with patch('logging.basicConfig'), \
             patch('logging.getLogger') as mock_get_logger:
            
            mock_urllib3_logger = Mock()
            mock_requests_logger = Mock()
            mock_get_logger.side_effect = lambda name: {
                'urllib3': mock_urllib3_logger,
                'requests': mock_requests_logger
            }.get(name, Mock())
            
            setup_logging('verbose')
            
            # Should not suppress third-party loggers in debug mode
            mock_urllib3_logger.setLevel.assert_not_called()
            mock_requests_logger.setLevel.assert_not_called()


class TestCreateParser:
    """Test cases for argument parser creation."""
    
    def test_create_parser_basic(self):
        """Test basic parser creation."""
        parser = create_parser()
        
        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.prog == 'fqcn-converter'
    
    def test_parser_version_argument(self):
        """Test version argument parsing."""
        parser = create_parser()
        
        # Test version argument exists
        with pytest.raises(SystemExit):
            parser.parse_args(['--version'])
    
    def test_parser_verbosity_arguments(self):
        """Test verbosity argument parsing."""
        parser = create_parser()
        
        # Test quiet argument
        args = parser.parse_args(['--quiet', 'convert', 'test.yml'])
        assert args.verbosity == 'quiet'
        
        # Test verbose argument
        args = parser.parse_args(['--verbose', 'convert', 'test.yml'])
        assert args.verbosity == 'verbose'
        
        # Test debug argument
        args = parser.parse_args(['--debug', 'convert', 'test.yml'])
        assert args.verbosity == 'verbose'
        
        # Test default verbosity
        args = parser.parse_args(['convert', 'test.yml'])
        assert args.verbosity == 'normal'
    
    def test_parser_mutually_exclusive_verbosity(self):
        """Test that verbosity arguments are mutually exclusive."""
        parser = create_parser()
        
        # Should raise error for conflicting verbosity options
        with pytest.raises(SystemExit):
            parser.parse_args(['--quiet', '--verbose', 'convert', 'test.yml'])
    
    def test_parser_subcommands(self):
        """Test subcommand parsing."""
        parser = create_parser()
        
        # Test convert subcommand
        args = parser.parse_args(['convert', 'test.yml'])
        assert args.command == 'convert'
        
        # Test validate subcommand
        args = parser.parse_args(['validate', 'test.yml'])
        assert args.command == 'validate'
        
        # Test batch subcommand
        args = parser.parse_args(['batch', '/path/to/projects'])
        assert args.command == 'batch'
    
    def test_parser_no_command(self):
        """Test parser with no command specified."""
        parser = create_parser()
        
        args = parser.parse_args([])
        assert args.command is None


class TestMainFunction:
    """Test cases for main CLI function."""
    
    @patch('fqcn_converter.cli.main.preprocess_args')
    @patch('fqcn_converter.cli.main.create_parser')
    @patch('fqcn_converter.cli.main.setup_logging')
    def test_main_no_command(self, mock_setup_logging, mock_create_parser, mock_preprocess_args):
        """Test main function with no command specified."""
        mock_parser = Mock()
        mock_parser.parse_args.return_value = Mock(command=None, verbosity='normal')
        mock_parser.print_help = Mock()
        mock_create_parser.return_value = mock_parser
        mock_preprocess_args.return_value = ([], 'normal')
        
        result = main()
        
        assert result == 1
        mock_parser.print_help.assert_called_once()
        mock_setup_logging.assert_called_once_with('normal')
    
    @patch('fqcn_converter.cli.main.preprocess_args')
    @patch('fqcn_converter.cli.main.create_parser')
    @patch('fqcn_converter.cli.main.setup_logging')
    @patch('fqcn_converter.cli.convert.main')
    def test_main_convert_command(self, mock_convert_main, mock_setup_logging, mock_create_parser, mock_preprocess_args):
        """Test main function with convert command."""
        mock_args = Mock(command='convert', verbosity='normal')
        mock_parser = Mock()
        mock_parser.parse_args.return_value = mock_args
        mock_create_parser.return_value = mock_parser
        mock_convert_main.return_value = 0
        mock_preprocess_args.return_value = (['convert'], 'normal')
        
        result = main()
        
        assert result == 0
        mock_convert_main.assert_called_once_with(mock_args)
        mock_setup_logging.assert_called_once_with('normal')
    
    @patch('fqcn_converter.cli.main.create_parser')
    @patch('fqcn_converter.cli.main.setup_logging')
    @patch('fqcn_converter.cli.validate.main')
    def test_main_validate_command(self, mock_validate_main, mock_setup_logging, mock_create_parser):
        """Test main function with validate command."""
        mock_args = Mock(command='validate', verbosity='verbose')
        mock_parser = Mock()
        mock_parser.parse_args.return_value = mock_args
        mock_create_parser.return_value = mock_parser
        mock_validate_main.return_value = 0
        
        result = main()
        
        assert result == 0
        mock_validate_main.assert_called_once_with(mock_args)
        mock_setup_logging.assert_called_once_with('verbose')
    
    @patch('fqcn_converter.cli.main.preprocess_args')
    @patch('fqcn_converter.cli.main.create_parser')
    @patch('fqcn_converter.cli.main.setup_logging')
    @patch('fqcn_converter.cli.batch.main')
    def test_main_batch_command(self, mock_batch_main, mock_setup_logging, mock_create_parser, mock_preprocess_args):
        """Test main function with batch command."""
        mock_args = Mock(command='batch', verbosity='quiet')
        mock_parser = Mock()
        mock_parser.parse_args.return_value = mock_args
        mock_create_parser.return_value = mock_parser
        mock_batch_main.return_value = 0
        mock_preprocess_args.return_value = (['batch'], 'quiet')
        
        result = main()
        
        assert result == 0
        mock_batch_main.assert_called_once_with(mock_args)
        mock_setup_logging.assert_called_once_with('quiet')
    
    @patch('fqcn_converter.cli.main.create_parser')
    @patch('fqcn_converter.cli.main.setup_logging')
    def test_main_unknown_command(self, mock_setup_logging, mock_create_parser):
        """Test main function with unknown command."""
        mock_args = Mock(command='unknown', verbosity='normal')
        mock_parser = Mock()
        mock_parser.parse_args.return_value = mock_args
        mock_create_parser.return_value = mock_parser
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            result = main()
            
            assert result == 1
            mock_logger.error.assert_called_once_with("Unknown command: unknown")
    
    @patch('fqcn_converter.cli.main.create_parser')
    @patch('fqcn_converter.cli.main.setup_logging')
    @patch('fqcn_converter.cli.convert.main')
    def test_main_keyboard_interrupt(self, mock_convert_main, mock_setup_logging, mock_create_parser):
        """Test main function with keyboard interrupt."""
        mock_args = Mock(command='convert', verbosity='normal')
        mock_parser = Mock()
        mock_parser.parse_args.return_value = mock_args
        mock_create_parser.return_value = mock_parser
        mock_convert_main.side_effect = KeyboardInterrupt()
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            result = main()
            
            assert result == 1
            mock_logger.info.assert_called_once_with("Operation interrupted by user")
    
    @patch('fqcn_converter.cli.main.create_parser')
    @patch('fqcn_converter.cli.main.setup_logging')
    @patch('fqcn_converter.cli.convert.main')
    def test_main_unexpected_exception(self, mock_convert_main, mock_setup_logging, mock_create_parser):
        """Test main function with unexpected exception."""
        mock_args = Mock(command='convert', verbosity='normal')
        mock_parser = Mock()
        mock_parser.parse_args.return_value = mock_args
        mock_create_parser.return_value = mock_parser
        mock_convert_main.side_effect = Exception("Unexpected error")
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            result = main()
            
            assert result == 1
            mock_logger.error.assert_called_once_with("Unexpected error: Unexpected error")
    
    @patch('fqcn_converter.cli.main.create_parser')
    @patch('fqcn_converter.cli.main.setup_logging')
    @patch('fqcn_converter.cli.convert.main')
    def test_main_exception_with_verbose_logging(self, mock_convert_main, mock_setup_logging, mock_create_parser):
        """Test main function exception handling with verbose logging."""
        mock_args = Mock(command='convert', verbosity='verbose')
        mock_parser = Mock()
        mock_parser.parse_args.return_value = mock_args
        mock_create_parser.return_value = mock_parser
        mock_convert_main.side_effect = Exception("Unexpected error")
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            result = main()
            
            assert result == 1
            mock_logger.error.assert_called_once_with("Unexpected error: Unexpected error")
            mock_logger.exception.assert_called_once_with("Full traceback:")
    
    @patch('sys.argv', ['fqcn-converter'])
    @patch('fqcn_converter.cli.main.main')
    def test_main_entry_point(self, mock_main):
        """Test main entry point when run as script."""
        mock_main.return_value = 0
        
        # Import and run the main module
        with patch('sys.exit') as mock_exit:
            import fqcn_converter.cli.main
            # Simulate running as __main__
            if hasattr(fqcn_converter.cli.main, '__name__'):
                fqcn_converter.cli.main.__name__ = '__main__'
            
            mock_exit.assert_not_called()  # Should not be called in test