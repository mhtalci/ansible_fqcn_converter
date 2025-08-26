#!/usr/bin/env python3
"""
Test module for CLI convert command.
"""

import json
import os
import shutil
import tempfile
from argparse import Namespace
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, call, mock_open, patch

import pytest

from fqcn_converter.cli.convert import ConvertCommand, add_convert_arguments, main
from fqcn_converter.core.converter import ConversionResult
from fqcn_converter.exceptions import (
    ConfigurationError,
    ConversionError,
    FileAccessError,
    FQCNConverterError,
)


class TestConvertParser:
    """Test convert command parser."""

    def test_add_convert_arguments(self):
        """Test that convert arguments are added correctly."""
        import argparse

        parser = argparse.ArgumentParser()
        add_convert_arguments(parser)

        assert parser is not None
        assert hasattr(parser, "parse_args")

    def test_convert_parser_required_args(self):
        """Test convert parser with required arguments."""
        import argparse

        parser = argparse.ArgumentParser()
        add_convert_arguments(parser)

        # Test with files argument
        args = parser.parse_args(["test.yml"])
        assert args.files == ["test.yml"]

    def test_convert_parser_optional_args(self):
        """Test convert parser with optional arguments."""
        import argparse

        parser = argparse.ArgumentParser()
        add_convert_arguments(parser)

        # Test with various optional arguments
        args = parser.parse_args(
            ["test.yml", "--dry-run", "--config", "custom_config.yml", "--backup"]
        )

        assert args.files == ["test.yml"]
        assert args.dry_run is True
        assert args.config == "custom_config.yml"
        assert args.backup is True

    def test_convert_parser_help(self):
        """Test that convert parser shows help."""
        import argparse

        parser = argparse.ArgumentParser()
        add_convert_arguments(parser)

        with pytest.raises(SystemExit):
            parser.parse_args(["--help"])


class TestConvertCommand:
    """Test convert command handling."""

    @patch("fqcn_converter.cli.convert.ConvertCommand")
    def test_main_convert_command_basic(self, mock_command_class):
        """Test basic convert command handling."""
        # Mock command instance
        mock_command = MagicMock()
        mock_command.run.return_value = 0
        mock_command_class.return_value = mock_command

        # Create test arguments
        args = Namespace(files=["test.yml"], dry_run=False, config=None, backup=False)

        # Should not raise exception
        result = main(args)

        # Verify command was called
        mock_command_class.assert_called_once_with(args)
        mock_command.run.assert_called_once()
        assert result == 0

    def test_convert_parser_all_arguments(self):
        """Test convert parser with all arguments."""
        import argparse

        parser = argparse.ArgumentParser()
        add_convert_arguments(parser)

        args = parser.parse_args(
            [
                "file1.yml",
                "file2.yml",
                "--config",
                "config.yml",
                "--dry-run",
                "--backup",
                "--no-backup",
                "--progress",
                "--report",
                "report.json",
                "--skip-validation",
                "--lint",
                "--force",
                "--exclude",
                "pattern1",
                "--exclude",
                "pattern2",
            ]
        )

        assert args.files == ["file1.yml", "file2.yml"]
        assert args.config == "config.yml"
        assert args.dry_run is True
        assert args.backup is True
        assert args.no_backup is True
        assert args.progress is True
        assert args.report == "report.json"
        assert args.skip_validation is True
        assert args.lint is True
        assert args.force is True
        assert args.exclude == ["pattern1", "pattern2"]

    def test_convert_parser_defaults(self):
        """Test convert parser default values."""
        import argparse

        parser = argparse.ArgumentParser()
        add_convert_arguments(parser)

        args = parser.parse_args(["test.yml"])

        assert args.files == ["test.yml"]
        assert args.config is None
        assert args.dry_run is False
        assert args.backup is False
        assert args.no_backup is False
        assert args.progress is False
        assert args.report is None
        assert args.skip_validation is False
        assert args.lint is False
        assert args.force is False
        assert args.exclude is None

    def test_convert_module_imports(self):
        """Test that convert module functions can be imported."""
        from fqcn_converter.cli.convert import add_convert_arguments, main

        assert callable(add_convert_arguments)
        assert callable(main)


class TestConvertCommandInit:
    """Test ConvertCommand initialization."""

    def test_convert_command_init(self):
        """Test ConvertCommand initialization."""
        args = Namespace(files=["test.yml"])
        command = ConvertCommand(args)

        assert command.args == args
        assert command.converter is None
        assert command.results == []
        assert command.stats["files_processed"] == 0
        assert command.stats["files_converted"] == 0
        assert command.stats["files_failed"] == 0
        assert isinstance(command.stats["start_time"], datetime)


class TestConvertCommandRun:
    """Test ConvertCommand run method."""

    @patch("fqcn_converter.cli.convert.FQCNConverter")
    def test_run_success(self, mock_converter_class):
        """Test successful conversion run."""
        # Setup mocks
        mock_converter = MagicMock()
        mock_converter_class.return_value = mock_converter

        mock_result = ConversionResult(
            file_path="test.yml", success=True, changes_made=2, errors=[], warnings=[]
        )
        mock_converter.convert_file.return_value = mock_result

        args = Namespace(
            files=["test.yml"],
            config=None,
            dry_run=False,
            report=None,
            progress=False,
            backup=False,
            no_backup=False,
        )

        command = ConvertCommand(args)

        with patch.object(command, "_discover_files", return_value=[Path("test.yml")]):
            with patch.object(command, "_print_summary"):
                result = command.run()

        assert result == 0
        assert len(command.results) == 1
        assert command.stats["files_processed"] == 1
        assert command.stats["files_converted"] == 1

    @patch("fqcn_converter.cli.convert.FQCNConverter")
    def test_run_configuration_error(self, mock_converter_class):
        """Test run with configuration error."""
        mock_converter_class.side_effect = ConfigurationError("Test error")

        args = Namespace(files=["test.yml"], config=None)
        command = ConvertCommand(args)

        result = command.run()
        assert result == 1

    @patch("fqcn_converter.cli.convert.FQCNConverter")
    def test_run_keyboard_interrupt(self, mock_converter_class):
        """Test run with keyboard interrupt."""
        mock_converter = MagicMock()
        mock_converter_class.return_value = mock_converter

        args = Namespace(files=["test.yml"], config=None)
        command = ConvertCommand(args)

        with patch.object(command, "_discover_files", side_effect=KeyboardInterrupt):
            result = command.run()

        assert result == 1

    @patch("fqcn_converter.cli.convert.FQCNConverter")
    def test_run_unexpected_exception(self, mock_converter_class):
        """Test run with unexpected exception."""
        mock_converter = MagicMock()
        mock_converter_class.return_value = mock_converter

        args = Namespace(files=["test.yml"], config=None, verbosity="verbose")
        command = ConvertCommand(args)

        with patch.object(
            command, "_discover_files", side_effect=RuntimeError("Unexpected")
        ):
            result = command.run()

        assert result == 1

    @patch("fqcn_converter.cli.convert.FQCNConverter")
    def test_run_no_files_found(self, mock_converter_class):
        """Test run when no files are found."""
        mock_converter = MagicMock()
        mock_converter_class.return_value = mock_converter

        args = Namespace(files=["nonexistent"], config=None)
        command = ConvertCommand(args)

        with patch.object(command, "_discover_files", return_value=[]):
            with patch.object(command, "_print_summary"):
                result = command.run()

        assert result == 0

    @patch("fqcn_converter.cli.convert.FQCNConverter")
    def test_run_dry_run_mode(self, mock_converter_class):
        """Test run in dry-run mode."""
        mock_converter = MagicMock()
        mock_converter_class.return_value = mock_converter

        mock_result = ConversionResult(
            file_path="test.yml", success=True, changes_made=2, errors=[], warnings=[]
        )
        mock_converter.convert_file.return_value = mock_result

        args = Namespace(
            files=["test.yml"],
            config=None,
            dry_run=True,
            report=None,
            progress=False,
            backup=False,
            no_backup=False,
        )

        command = ConvertCommand(args)

        with patch.object(command, "_discover_files", return_value=[Path("test.yml")]):
            with patch.object(command, "_print_summary"):
                result = command.run()

        assert result == 0
        mock_converter.convert_file.assert_called_with(Path("test.yml"), dry_run=True)

    @patch("fqcn_converter.cli.convert.FQCNConverter")
    def test_run_with_report_generation(self, mock_converter_class):
        """Test run with report generation."""
        mock_converter = MagicMock()
        mock_converter_class.return_value = mock_converter

        mock_result = ConversionResult(
            file_path="test.yml", success=True, changes_made=1, errors=[], warnings=[]
        )
        mock_converter.convert_file.return_value = mock_result

        args = Namespace(
            files=["test.yml"],
            config=None,
            dry_run=False,
            report="report.json",
            progress=False,
            backup=False,
            no_backup=False,
        )

        command = ConvertCommand(args)

        with patch.object(command, "_discover_files", return_value=[Path("test.yml")]):
            with patch.object(command, "_generate_report"):
                with patch.object(command, "_print_summary"):
                    result = command.run()

        assert result == 0


class TestConvertCommandFileDiscovery:
    """Test file discovery methods."""

    def test_discover_files_single_file(self):
        """Test discovering a single file."""
        args = Namespace(files=["test.yml"], exclude=None)
        command = ConvertCommand(args)

        with patch("pathlib.Path.is_file", return_value=True):
            with patch.object(command, "_should_process_file", return_value=True):
                files = command._discover_files()

        assert len(files) == 1
        assert files[0] == Path("test.yml")

    def test_discover_files_directory(self):
        """Test discovering files in directory."""
        args = Namespace(files=["."], exclude=None)
        command = ConvertCommand(args)

        with patch("pathlib.Path.is_file", return_value=False):
            with patch("pathlib.Path.is_dir", return_value=True):
                with patch.object(
                    command, "_find_ansible_files", return_value=[Path("test.yml")]
                ):
                    files = command._discover_files()

        assert len(files) == 1
        assert files[0] == Path("test.yml")

    def test_discover_files_nonexistent_path(self):
        """Test discovering files with nonexistent path."""
        args = Namespace(files=["nonexistent"], exclude=None)
        command = ConvertCommand(args)

        with patch("pathlib.Path.is_file", return_value=False):
            with patch("pathlib.Path.is_dir", return_value=False):
                files = command._discover_files()

        assert len(files) == 0

    def test_find_ansible_files(self):
        """Test finding Ansible files in directory."""
        args = Namespace()
        command = ConvertCommand(args)

        # Mock different files for different patterns to avoid duplicates
        def mock_glob(pattern):
            if pattern == "**/*.yml":
                return [Path("test.yml")]
            elif pattern == "**/*.yaml":
                return [Path("playbook.yaml")]
            return []

        with patch("pathlib.Path.glob", side_effect=mock_glob):
            with patch("pathlib.Path.is_file", return_value=True):
                with patch.object(command, "_should_process_file", return_value=True):
                    with patch.object(command, "_is_ansible_file", return_value=True):
                        files = command._find_ansible_files(Path("."), [])

        assert len(files) == 2

    def test_should_process_file_exclude_patterns(self):
        """Test file processing with exclude patterns."""
        args = Namespace()
        command = ConvertCommand(args)

        # Test exclusion
        result = command._should_process_file(Path("test.yml"), ["test"])
        assert result is False

        # Test inclusion
        result = command._should_process_file(Path("playbook.yml"), ["test"])
        assert result is True

    def test_should_process_file_skip_dirs(self):
        """Test file processing skips common directories."""
        args = Namespace()
        command = ConvertCommand(args)

        # Test skipping .git directory
        result = command._should_process_file(Path(".git/config"), [])
        assert result is False

        # Test skipping __pycache__ directory
        result = command._should_process_file(Path("src/__pycache__/test.pyc"), [])
        assert result is False

    def test_is_ansible_file_by_extension(self):
        """Test Ansible file detection by extension."""
        args = Namespace()
        command = ConvertCommand(args)

        # Test invalid extension
        assert command._is_ansible_file(Path("test.txt")) is False

    def test_is_ansible_file_by_name(self):
        """Test Ansible file detection by filename."""
        args = Namespace()
        command = ConvertCommand(args)

        # Test common Ansible filenames
        assert command._is_ansible_file(Path("site.yml")) is True
        assert command._is_ansible_file(Path("main.yml")) is True
        assert command._is_ansible_file(Path("playbook.yml")) is True

    def test_is_ansible_file_by_content(self):
        """Test Ansible file detection by content."""
        args = Namespace()
        command = ConvertCommand(args)

        ansible_content = "---\nhosts: all\ntasks:\n  - name: test"

        with patch("builtins.open", mock_open(read_data=ansible_content)):
            result = command._is_ansible_file(Path("test.yml"))

        assert result is True

    def test_is_ansible_file_read_error(self):
        """Test Ansible file detection with read error."""
        args = Namespace()
        command = ConvertCommand(args)

        with patch("builtins.open", side_effect=IOError("Permission denied")):
            result = command._is_ansible_file(Path("test.yml"))

        assert result is False


class TestConvertCommandConversion:
    """Test conversion methods."""

    @patch("fqcn_converter.cli.convert.FQCNConverter")
    def test_convert_files_success(self, mock_converter_class):
        """Test successful file conversion."""
        mock_converter = MagicMock()
        mock_converter_class.return_value = mock_converter

        mock_result = ConversionResult(
            file_path="test.yml", success=True, changes_made=2, errors=[], warnings=[]
        )
        mock_converter.convert_file.return_value = mock_result

        args = Namespace(progress=False, backup=False, dry_run=False, no_backup=False)
        command = ConvertCommand(args)
        command.converter = mock_converter

        success = command._convert_files([Path("test.yml")])

        assert success is True
        assert len(command.results) == 1
        assert command.stats["files_processed"] == 1
        assert command.stats["files_converted"] == 1
        assert command.stats["total_changes"] == 2

    @patch("fqcn_converter.cli.convert.FQCNConverter")
    def test_convert_files_with_progress(self, mock_converter_class):
        """Test file conversion with progress display."""
        mock_converter = MagicMock()
        mock_converter_class.return_value = mock_converter

        mock_result = ConversionResult(
            file_path="test.yml", success=True, changes_made=1, errors=[], warnings=[]
        )
        mock_converter.convert_file.return_value = mock_result

        args = Namespace(progress=True, backup=False, dry_run=False, no_backup=False)
        command = ConvertCommand(args)
        command.converter = mock_converter

        with patch("sys.stderr"):
            success = command._convert_files([Path("test.yml")])

        assert success is True

    @patch("fqcn_converter.cli.convert.FQCNConverter")
    def test_convert_files_with_backup(self, mock_converter_class):
        """Test file conversion with backup creation."""
        mock_converter = MagicMock()
        mock_converter_class.return_value = mock_converter

        mock_result = ConversionResult(
            file_path="test.yml", success=True, changes_made=1, errors=[], warnings=[]
        )
        mock_converter.convert_file.return_value = mock_result

        args = Namespace(progress=False, backup=True, dry_run=False, no_backup=False)
        command = ConvertCommand(args)
        command.converter = mock_converter

        with patch.object(command, "_create_backup") as mock_backup:
            success = command._convert_files([Path("test.yml")])

        assert success is True
        mock_backup.assert_called_once_with(Path("test.yml"))

    @patch("fqcn_converter.cli.convert.FQCNConverter")
    def test_convert_files_no_changes(self, mock_converter_class):
        """Test file conversion with no changes needed."""
        mock_converter = MagicMock()
        mock_converter_class.return_value = mock_converter

        mock_result = ConversionResult(
            file_path="test.yml", success=True, changes_made=0, errors=[], warnings=[]
        )
        mock_converter.convert_file.return_value = mock_result

        args = Namespace(progress=False, backup=False, dry_run=False, no_backup=False)
        command = ConvertCommand(args)
        command.converter = mock_converter

        success = command._convert_files([Path("test.yml")])

        assert success is True
        assert command.stats["files_converted"] == 0  # No changes made

    @patch("fqcn_converter.cli.convert.FQCNConverter")
    def test_convert_files_with_failure(self, mock_converter_class):
        """Test file conversion with failure."""
        mock_converter = MagicMock()
        mock_converter_class.return_value = mock_converter

        mock_result = ConversionResult(
            file_path="test.yml",
            success=False,
            changes_made=0,
            errors=["Conversion failed"],
            warnings=[],
        )
        mock_converter.convert_file.return_value = mock_result

        args = Namespace(progress=False, backup=False, dry_run=False, no_backup=False)
        command = ConvertCommand(args)
        command.converter = mock_converter

        success = command._convert_files([Path("test.yml")])

        assert success is False
        assert command.stats["files_failed"] == 1

    @patch("fqcn_converter.cli.convert.FQCNConverter")
    def test_convert_files_with_warnings(self, mock_converter_class):
        """Test file conversion with warnings."""
        mock_converter = MagicMock()
        mock_converter_class.return_value = mock_converter

        mock_result = ConversionResult(
            file_path="test.yml",
            success=True,
            changes_made=1,
            errors=[],
            warnings=["Warning message"],
        )
        mock_converter.convert_file.return_value = mock_result

        args = Namespace(progress=False, backup=False, dry_run=False, no_backup=False)
        command = ConvertCommand(args)
        command.converter = mock_converter

        success = command._convert_files([Path("test.yml")])

        assert success is True

    @patch("fqcn_converter.cli.convert.FQCNConverter")
    def test_convert_files_with_exception(self, mock_converter_class):
        """Test file conversion with exception."""
        mock_converter = MagicMock()
        mock_converter_class.return_value = mock_converter
        mock_converter.convert_file.side_effect = Exception("Test error")

        args = Namespace(progress=False, backup=False, dry_run=False, no_backup=False)
        command = ConvertCommand(args)
        command.converter = mock_converter

        success = command._convert_files([Path("test.yml")])

        assert success is False
        assert command.stats["files_failed"] == 1

    def test_create_backup_success(self):
        """Test successful backup creation."""
        args = Namespace()
        command = ConvertCommand(args)

        with patch("shutil.copy2") as mock_copy:
            command._create_backup(Path("test.yml"))

            mock_copy.assert_called_once_with(
                Path("test.yml"), Path("test.yml.fqcn_backup")
            )

    def test_create_backup_failure(self):
        """Test backup creation failure."""
        args = Namespace()
        command = ConvertCommand(args)

        with patch("shutil.copy2", side_effect=Exception("Permission denied")):
            command._create_backup(Path("test.yml"))  # Should not raise exception


class TestConvertCommandReporting:
    """Test reporting methods."""

    def test_generate_report(self):
        """Test report generation."""
        args = Namespace(
            files=["test.yml"],
            config=None,
            dry_run=False,
            backup=False,
            force=False,
            report="report.json",
        )
        command = ConvertCommand(args)
        command.stats["end_time"] = datetime.now()

        result = ConversionResult(
            file_path="test.yml",
            success=True,
            changes_made=2,
            errors=[],
            warnings=["Warning message"],
        )
        command.results = [result]

        with patch("builtins.open", mock_open()) as mock_file:
            with patch("json.dump") as mock_json_dump:
                command._generate_report()

        mock_file.assert_called_once_with("report.json", "w", encoding="utf-8")
        mock_json_dump.assert_called_once()

    def test_generate_report_exception(self):
        """Test report generation with exception."""
        args = Namespace(report="report.json")
        command = ConvertCommand(args)

        with patch("builtins.open", side_effect=Exception("Permission denied")):
            command._generate_report()  # Should not raise exception

    def test_print_summary_success(self):
        """Test printing summary for successful conversion."""
        args = Namespace(dry_run=False)
        command = ConvertCommand(args)
        command.stats["end_time"] = datetime.now()
        command.stats["files_processed"] = 2
        command.stats["files_converted"] = 2
        command.stats["files_failed"] = 0
        command.stats["total_changes"] = 5

        with patch("builtins.print") as mock_print:
            command._print_summary()

        # Should print summary information
        assert mock_print.call_count > 5

    def test_print_summary_with_failures(self):
        """Test printing summary with failures."""
        args = Namespace(dry_run=False)
        command = ConvertCommand(args)
        command.stats["end_time"] = datetime.now()
        command.stats["files_processed"] = 2
        command.stats["files_converted"] = 1
        command.stats["files_failed"] = 1
        command.stats["total_changes"] = 2

        failed_result = ConversionResult(
            file_path="failed.yml",
            success=False,
            changes_made=0,
            errors=["Conversion error"],
            warnings=[],
        )
        command.results = [failed_result]

        with patch("builtins.print") as mock_print:
            command._print_summary()

        # Should print summary and failed files
        assert mock_print.call_count > 8

    def test_print_summary_dry_run(self):
        """Test printing summary for dry run."""
        args = Namespace(dry_run=True)
        command = ConvertCommand(args)
        command.stats["end_time"] = datetime.now()
        command.stats["files_processed"] = 1
        command.stats["files_converted"] = 1
        command.stats["files_failed"] = 0
        command.stats["total_changes"] = 3

        with patch("builtins.print") as mock_print:
            command._print_summary()

        # Should mention dry run
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        dry_run_mentioned = any("DRY RUN" in str(call) for call in print_calls)
        assert dry_run_mentioned
