#!/usr/bin/env python3
"""
Test module for CLI validate command.
"""

import json
import os
import tempfile
import xml.etree.ElementTree as ET
from argparse import Namespace
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, call, mock_open, patch

import pytest

from fqcn_converter.cli.validate import ValidateCommand, add_validate_arguments, main
from fqcn_converter.core.validator import ValidationIssue, ValidationResult
from fqcn_converter.exceptions import FQCNConverterError, ValidationError


class TestValidateParser:
    """Test validate command parser."""

    def test_add_validate_arguments(self):
        """Test that validate arguments are added correctly."""
        import argparse

        parser = argparse.ArgumentParser()
        add_validate_arguments(parser)

        assert parser is not None
        assert hasattr(parser, "parse_args")

    def test_validate_parser_required_args(self):
        """Test validate parser with required arguments."""
        import argparse

        parser = argparse.ArgumentParser()
        add_validate_arguments(parser)

        # Test with files argument
        args = parser.parse_args(["test.yml"])
        assert args.files == ["test.yml"]

    def test_validate_parser_optional_args(self):
        """Test validate parser with optional arguments."""
        import argparse

        parser = argparse.ArgumentParser()
        add_validate_arguments(parser)

        # Test with various optional arguments
        args = parser.parse_args(
            [
                "test.yml",
                "--strict",
                "--config",
                "custom_config.yml",
                "--format",
                "json",
            ]
        )

        assert args.files == ["test.yml"]
        assert args.strict is True
        assert args.config == "custom_config.yml"
        assert args.format == "json"

    def test_validate_parser_help(self):
        """Test that validate parser shows help."""
        import argparse

        parser = argparse.ArgumentParser()
        add_validate_arguments(parser)

        with pytest.raises(SystemExit):
            parser.parse_args(["--help"])


class TestValidateCommand:
    """Test validate command handling."""

    @patch("fqcn_converter.cli.validate.ValidateCommand")
    def test_main_validate_command_basic(self, mock_command_class):
        """Test basic validate command handling."""
        # Mock command instance
        mock_command = MagicMock()
        mock_command.run.return_value = 0
        mock_command_class.return_value = mock_command

        # Create test arguments
        args = Namespace(files=["test.yml"], strict=False, config=None, format="text")

        # Should not raise exception
        result = main(args)

        # Verify command was called
        mock_command_class.assert_called_once_with(args)
        mock_command.run.assert_called_once()
        assert result == 0

    def test_validate_parser_all_arguments(self):
        """Test validate parser with all arguments."""
        import argparse

        parser = argparse.ArgumentParser()
        add_validate_arguments(parser)

        args = parser.parse_args(
            [
                "file1.yml",
                "file2.yml",
                "--config",
                "config.yml",
                "--strict",
                "--score",
                "--lint",
                "--report",
                "report.json",
                "--format",
                "junit",
                "--exclude",
                "pattern1",
                "--exclude",
                "pattern2",
                "--include-warnings",
                "--parallel",
                "--workers",
                "8",
            ]
        )

        assert args.files == ["file1.yml", "file2.yml"]
        assert args.config == "config.yml"
        assert args.strict is True
        assert args.score is True
        assert args.lint is True
        assert args.report == "report.json"
        assert args.format == "junit"
        assert args.exclude == ["pattern1", "pattern2"]
        assert args.include_warnings is True
        assert args.parallel is True
        assert args.workers == 8

    def test_validate_parser_defaults(self):
        """Test validate parser default values."""
        import argparse

        parser = argparse.ArgumentParser()
        add_validate_arguments(parser)

        args = parser.parse_args([])

        assert args.files == ["."]
        assert args.config is None
        assert args.strict is False
        assert args.score is False
        assert args.lint is False
        assert args.report is None
        assert args.format == "text"
        assert args.exclude is None
        assert args.include_warnings is False
        assert args.parallel is False
        assert args.workers == 4

    def test_validate_module_imports(self):
        """Test that validate module functions can be imported."""
        from fqcn_converter.cli.validate import add_validate_arguments, main

        assert callable(add_validate_arguments)
        assert callable(main)


class TestValidateCommandInit:
    """Test ValidateCommand initialization."""

    def test_validate_command_init(self):
        """Test ValidateCommand initialization."""
        args = Namespace(files=["test.yml"])
        command = ValidateCommand(args)

        assert command.args == args
        assert command.validator is None
        assert command.results == []
        assert command.stats["files_validated"] == 0
        assert command.stats["files_passed"] == 0
        assert command.stats["files_failed"] == 0
        assert isinstance(command.stats["start_time"], datetime)


class TestValidateCommandRun:
    """Test ValidateCommand run method."""

    @patch("fqcn_converter.cli.validate.ValidationEngine")
    def test_run_success(self, mock_validator_class):
        """Test successful validation run."""
        # Setup mocks
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator

        mock_result = ValidationResult(
            file_path="test.yml", valid=True, score=95.0, issues=[]
        )
        mock_validator.validate_conversion.return_value = mock_result

        args = Namespace(
            files=["test.yml"], report=None, parallel=False, lint=False, format="text"
        )

        command = ValidateCommand(args)

        with patch.object(command, "_discover_files", return_value=[Path("test.yml")]):
            with patch.object(command, "_print_results"):
                result = command.run()

        assert result == 0
        assert len(command.results) == 1
        assert command.stats["files_validated"] == 1
        assert command.stats["files_passed"] == 1

    @patch("fqcn_converter.cli.validate.ValidationEngine")
    def test_run_validation_error(self, mock_validator_class):
        """Test run with validation error."""
        mock_validator_class.side_effect = ValidationError("Test error")

        args = Namespace(files=["test.yml"])
        command = ValidateCommand(args)

        result = command.run()
        assert result == 1

    @patch("fqcn_converter.cli.validate.ValidationEngine")
    def test_run_keyboard_interrupt(self, mock_validator_class):
        """Test run with keyboard interrupt."""
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator

        args = Namespace(files=["test.yml"])
        command = ValidateCommand(args)

        with patch.object(command, "_discover_files", side_effect=KeyboardInterrupt):
            result = command.run()

        assert result == 1

    @patch("fqcn_converter.cli.validate.ValidationEngine")
    def test_run_unexpected_exception(self, mock_validator_class):
        """Test run with unexpected exception."""
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator

        args = Namespace(files=["test.yml"], verbosity="verbose")
        command = ValidateCommand(args)

        with patch.object(
            command, "_discover_files", side_effect=RuntimeError("Unexpected")
        ):
            result = command.run()

        assert result == 1

    @patch("fqcn_converter.cli.validate.ValidationEngine")
    def test_run_no_files_found(self, mock_validator_class):
        """Test run when no files are found."""
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator

        args = Namespace(files=["nonexistent"])
        command = ValidateCommand(args)

        with patch.object(command, "_discover_files", return_value=[]):
            with patch.object(command, "_print_results"):
                result = command.run()

        assert result == 0

    @patch("fqcn_converter.cli.validate.ValidationEngine")
    def test_run_with_report_generation(self, mock_validator_class):
        """Test run with report generation."""
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator

        mock_result = ValidationResult(
            file_path="test.yml", valid=True, score=95.0, issues=[]
        )
        mock_validator.validate_conversion.return_value = mock_result

        args = Namespace(
            files=["test.yml"],
            report="report.json",
            format="json",
            parallel=False,
            lint=False,
        )

        command = ValidateCommand(args)

        with patch.object(command, "_discover_files", return_value=[Path("test.yml")]):
            with patch.object(command, "_generate_report"):
                with patch.object(command, "_print_results"):
                    result = command.run()

        assert result == 0


class TestValidateCommandFileDiscovery:
    """Test file discovery methods."""

    def test_discover_files_single_file(self):
        """Test discovering a single file."""
        args = Namespace(files=["test.yml"], exclude=None)
        command = ValidateCommand(args)

        with patch("pathlib.Path.is_file", return_value=True):
            with patch.object(command, "_should_process_file", return_value=True):
                files = command._discover_files()

        assert len(files) == 1
        assert files[0] == Path("test.yml")

    def test_discover_files_directory(self):
        """Test discovering files in directory."""
        args = Namespace(files=["."], exclude=None)
        command = ValidateCommand(args)

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
        command = ValidateCommand(args)

        with patch("pathlib.Path.is_file", return_value=False):
            with patch("pathlib.Path.is_dir", return_value=False):
                files = command._discover_files()

        assert len(files) == 0

    def test_find_ansible_files(self):
        """Test finding Ansible files in directory."""
        args = Namespace()
        command = ValidateCommand(args)

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
        command = ValidateCommand(args)

        # Test exclusion
        result = command._should_process_file(Path("test.yml"), ["test"])
        assert result is False

        # Test inclusion
        result = command._should_process_file(Path("playbook.yml"), ["test"])
        assert result is True

    def test_should_process_file_skip_dirs(self):
        """Test file processing skips common directories."""
        args = Namespace()
        command = ValidateCommand(args)

        # Test skipping .git directory
        result = command._should_process_file(Path(".git/config"), [])
        assert result is False

        # Test skipping __pycache__ directory
        result = command._should_process_file(Path("src/__pycache__/test.pyc"), [])
        assert result is False

    def test_is_ansible_file_by_extension(self):
        """Test Ansible file detection by extension."""
        args = Namespace()
        command = ValidateCommand(args)

        # Test valid extensions
        assert command._is_ansible_file(Path("test.yml")) is False  # Need content check
        assert (
            command._is_ansible_file(Path("test.yaml")) is False
        )  # Need content check

        # Test invalid extension
        assert command._is_ansible_file(Path("test.txt")) is False

    def test_is_ansible_file_by_name(self):
        """Test Ansible file detection by filename."""
        args = Namespace()
        command = ValidateCommand(args)

        # Test common Ansible filenames
        assert command._is_ansible_file(Path("site.yml")) is True
        assert command._is_ansible_file(Path("main.yml")) is True
        assert command._is_ansible_file(Path("playbook.yml")) is True

    def test_is_ansible_file_by_content(self):
        """Test Ansible file detection by content."""
        args = Namespace()
        command = ValidateCommand(args)

        ansible_content = "---\nhosts: all\ntasks:\n  - name: test"

        with patch("builtins.open", mock_open(read_data=ansible_content)):
            result = command._is_ansible_file(Path("test.yml"))

        assert result is True

    def test_is_ansible_file_read_error(self):
        """Test Ansible file detection with read error."""
        args = Namespace()
        command = ValidateCommand(args)

        with patch("builtins.open", side_effect=IOError("Permission denied")):
            result = command._is_ansible_file(Path("test.yml"))

        assert result is False


class TestValidateCommandValidation:
    """Test validation methods."""

    @patch("fqcn_converter.cli.validate.ValidationEngine")
    def test_validate_files_sequential(self, mock_validator_class):
        """Test sequential file validation."""
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator

        mock_result = ValidationResult(
            file_path="test.yml", valid=True, score=95.0, issues=[]
        )
        mock_validator.validate_conversion.return_value = mock_result

        args = Namespace(format="text", lint=False)
        command = ValidateCommand(args)
        command.validator = mock_validator

        with patch("sys.stderr"):
            success = command._validate_files_sequential([Path("test.yml")])

        assert success is True
        assert len(command.results) == 1
        assert command.stats["files_validated"] == 1

    @patch("fqcn_converter.cli.validate.ValidationEngine")
    def test_validate_files_sequential_with_failure(self, mock_validator_class):
        """Test sequential validation with failure."""
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator

        mock_result = ValidationResult(
            file_path="test.yml",
            valid=False,
            score=50.0,
            issues=[ValidationIssue(1, 1, "error", "Test error", "Fix it")],
        )
        mock_validator.validate_conversion.return_value = mock_result

        args = Namespace(format="text", lint=False)
        command = ValidateCommand(args)
        command.validator = mock_validator

        with patch("sys.stderr"):
            success = command._validate_files_sequential([Path("test.yml")])

        assert success is False
        assert len(command.results) == 1
        assert command.stats["files_failed"] == 1

    @patch("fqcn_converter.cli.validate.ValidationEngine")
    def test_validate_files_sequential_with_exception(self, mock_validator_class):
        """Test sequential validation with exception."""
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_validator.validate_conversion.side_effect = Exception("Test error")

        args = Namespace(format="text", lint=False)
        command = ValidateCommand(args)
        command.validator = mock_validator

        with patch("sys.stderr"):
            success = command._validate_files_sequential([Path("test.yml")])

        assert success is False

    @patch("fqcn_converter.cli.validate.ValidationEngine")
    @patch("fqcn_converter.cli.validate.ThreadPoolExecutor")
    def test_validate_files_parallel(self, mock_executor_class, mock_validator_class):
        """Test parallel file validation."""
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator

        mock_result = ValidationResult(
            file_path="test.yml", valid=True, score=95.0, issues=[]
        )

        # Mock executor and futures
        mock_executor = MagicMock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor

        mock_future = MagicMock()
        mock_future.result.return_value = mock_result
        mock_executor.submit.return_value = mock_future

        # Mock as_completed
        with patch(
            "fqcn_converter.cli.validate.as_completed", return_value=[mock_future]
        ):
            args = Namespace(workers=2)
            command = ValidateCommand(args)
            command.validator = mock_validator

            success = command._validate_files_parallel([Path("test.yml")])

        assert success is True

    @patch("fqcn_converter.cli.validate.ValidationEngine")
    def test_validate_single_file(self, mock_validator_class):
        """Test single file validation."""
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator

        mock_result = ValidationResult(
            file_path="test.yml", valid=True, score=95.0, issues=[]
        )
        mock_validator.validate_conversion.return_value = mock_result

        args = Namespace(lint=False)
        command = ValidateCommand(args)
        command.validator = mock_validator

        result = command._validate_single_file(Path("test.yml"))

        assert result == mock_result

    @patch("fqcn_converter.cli.validate.ValidationEngine")
    def test_validate_single_file_with_exception(self, mock_validator_class):
        """Test single file validation with exception."""
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_validator.validate_conversion.side_effect = Exception("Test error")

        args = Namespace(lint=False)
        command = ValidateCommand(args)
        command.validator = mock_validator

        result = command._validate_single_file(Path("test.yml"))

        assert result is None


class TestValidateCommandStats:
    """Test statistics methods."""

    def test_update_stats_valid_result(self):
        """Test updating stats with valid result."""
        args = Namespace()
        command = ValidateCommand(args)

        result = ValidationResult(
            file_path="test.yml", valid=True, score=95.0, issues=[]
        )

        command._update_stats(result)

        assert command.stats["files_validated"] == 1
        assert command.stats["files_passed"] == 1
        assert command.stats["files_failed"] == 0
        assert command.stats["average_score"] == 95.0

    def test_update_stats_invalid_result(self):
        """Test updating stats with invalid result."""
        args = Namespace()
        command = ValidateCommand(args)

        issues = [
            ValidationIssue(1, 1, "error", "Error message", "Fix it"),
            ValidationIssue(2, 1, "warning", "Warning message", "Consider fixing"),
        ]

        result = ValidationResult(
            file_path="test.yml", valid=False, score=50.0, issues=issues
        )

        command._update_stats(result)

        assert command.stats["files_validated"] == 1
        assert command.stats["files_passed"] == 0
        assert command.stats["files_failed"] == 1
        assert command.stats["total_issues"] == 2
        assert command.stats["total_errors"] == 1
        assert command.stats["total_warnings"] == 1
        assert command.stats["average_score"] == 50.0

    def test_update_stats_multiple_results(self):
        """Test updating stats with multiple results."""
        args = Namespace()
        command = ValidateCommand(args)

        # First result
        result1 = ValidationResult(
            file_path="test1.yml", valid=True, score=90.0, issues=[]
        )
        command._update_stats(result1)

        # Second result
        result2 = ValidationResult(
            file_path="test2.yml",
            valid=False,
            score=60.0,
            issues=[ValidationIssue(1, 1, "error", "Error", "Fix")],
        )
        command._update_stats(result2)

        assert command.stats["files_validated"] == 2
        assert command.stats["files_passed"] == 1
        assert command.stats["files_failed"] == 1
        assert command.stats["average_score"] == 75.0  # (90 + 60) / 2


class TestValidateCommandAnsibleLint:
    """Test ansible-lint integration."""

    @patch("subprocess.run")
    def test_run_ansible_lint_success(self, mock_run):
        """Test successful ansible-lint execution."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = (
            "test.yml:5:10: [E301] Commands should not change things"
        )

        args = Namespace()
        command = ValidateCommand(args)

        result = ValidationResult(
            file_path="test.yml", valid=True, score=95.0, issues=[]
        )

        command._run_ansible_lint(Path("test.yml"), result)

        assert len(result.issues) == 1
        assert result.issues[0].line_number == 5
        assert result.issues[0].column == 10
        assert result.issues[0].severity == "warning"
        assert "ansible-lint" in result.issues[0].message

    @patch("subprocess.run")
    def test_run_ansible_lint_timeout(self, mock_run):
        """Test ansible-lint timeout."""
        from subprocess import TimeoutExpired

        mock_run.side_effect = TimeoutExpired("ansible-lint", 30)

        args = Namespace()
        command = ValidateCommand(args)

        result = ValidationResult(
            file_path="test.yml", valid=True, score=95.0, issues=[]
        )

        command._run_ansible_lint(Path("test.yml"), result)

        # Should not add issues on timeout
        assert len(result.issues) == 0

    @patch("subprocess.run")
    def test_run_ansible_lint_not_found(self, mock_run):
        """Test ansible-lint not found."""
        mock_run.side_effect = FileNotFoundError()

        args = Namespace()
        command = ValidateCommand(args)

        result = ValidationResult(
            file_path="test.yml", valid=True, score=95.0, issues=[]
        )

        command._run_ansible_lint(Path("test.yml"), result)

        # Should not add issues when ansible-lint not found
        assert len(result.issues) == 0

    @patch("subprocess.run")
    def test_run_ansible_lint_parse_error(self, mock_run):
        """Test ansible-lint output parsing error."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = "test.yml:invalid:format:message"

        args = Namespace()
        command = ValidateCommand(args)

        result = ValidationResult(
            file_path="test.yml", valid=True, score=95.0, issues=[]
        )

        command._run_ansible_lint(Path("test.yml"), result)

        # Should add generic issue for unparseable output (when line number parsing fails)
        assert len(result.issues) == 1
        assert result.issues[0].line_number == 1
        assert result.issues[0].column == 1
        assert "ansible-lint" in result.issues[0].message


class TestValidateCommandReporting:
    """Test report generation methods."""

    def test_generate_json_report(self):
        """Test JSON report generation."""
        args = Namespace(
            files=["test.yml"],
            strict=False,
            score=True,
            lint=False,
            include_warnings=True,
            report="report.json",
        )
        command = ValidateCommand(args)
        command.stats["end_time"] = datetime.now()

        result = ValidationResult(
            file_path="test.yml",
            valid=True,
            score=95.0,
            issues=[ValidationIssue(1, 1, "warning", "Test warning", "Fix it")],
        )
        command.results = [result]

        with patch("builtins.open", mock_open()) as mock_file:
            with patch("json.dump") as mock_json_dump:
                command._generate_json_report()

        mock_file.assert_called_once_with("report.json", "w", encoding="utf-8")
        mock_json_dump.assert_called_once()

    def test_generate_junit_report(self):
        """Test JUnit XML report generation."""
        args = Namespace(include_warnings=True, report="report.xml")
        command = ValidateCommand(args)
        command.stats["end_time"] = datetime.now()

        result = ValidationResult(
            file_path="test.yml",
            valid=False,
            score=50.0,
            issues=[ValidationIssue(1, 1, "error", "Test error", "Fix it")],
        )
        command.results = [result]

        with patch("xml.etree.ElementTree.ElementTree.write") as mock_write:
            command._generate_junit_report()

        mock_write.assert_called_once_with(
            "report.xml", encoding="utf-8", xml_declaration=True
        )

    def test_generate_text_report(self):
        """Test text report generation."""
        args = Namespace(include_warnings=True, report="report.txt")
        command = ValidateCommand(args)
        command.stats["end_time"] = datetime.now()

        result = ValidationResult(
            file_path="test.yml",
            valid=True,
            score=95.0,
            issues=[ValidationIssue(1, 1, "warning", "Test warning", "Fix it")],
        )
        command.results = [result]

        with patch("builtins.open", mock_open()) as mock_file:
            command._generate_text_report()

        mock_file.assert_called_once_with("report.txt", "w", encoding="utf-8")

    def test_generate_report_json_format(self):
        """Test report generation with JSON format."""
        args = Namespace(format="json", report="report.json")
        command = ValidateCommand(args)

        with patch.object(command, "_generate_json_report") as mock_json:
            command._generate_report()

        mock_json.assert_called_once()

    def test_generate_report_junit_format(self):
        """Test report generation with JUnit format."""
        args = Namespace(format="junit", report="report.xml")
        command = ValidateCommand(args)

        with patch.object(command, "_generate_junit_report") as mock_junit:
            command._generate_report()

        mock_junit.assert_called_once()

    def test_generate_report_text_format(self):
        """Test report generation with text format."""
        args = Namespace(format="text", report="report.txt")
        command = ValidateCommand(args)

        with patch.object(command, "_generate_text_report") as mock_text:
            command._generate_report()

        mock_text.assert_called_once()

    def test_generate_report_exception(self):
        """Test report generation with exception."""
        args = Namespace(format="json", report="report.json")
        command = ValidateCommand(args)

        with patch.object(
            command, "_generate_json_report", side_effect=Exception("Test error")
        ):
            command._generate_report()  # Should not raise exception


class TestValidateCommandOutput:
    """Test output methods."""

    def test_print_json_results(self):
        """Test printing results in JSON format."""
        args = Namespace(score=True, include_warnings=True)
        command = ValidateCommand(args)

        result = ValidationResult(
            file_path="test.yml",
            valid=True,
            score=95.0,
            issues=[ValidationIssue(1, 1, "warning", "Test warning", "Fix it")],
        )
        command.results = [result]

        with patch("builtins.print") as mock_print:
            with patch("json.dumps", return_value='{"test": "json"}') as mock_dumps:
                command._print_json_results()

        mock_dumps.assert_called_once()
        mock_print.assert_called_once_with('{"test": "json"}')

    def test_print_text_results_success(self):
        """Test printing text results for successful validation."""
        args = Namespace(score=True, include_warnings=True)
        command = ValidateCommand(args)
        command.stats["end_time"] = datetime.now()

        result = ValidationResult(
            file_path="test.yml", valid=True, score=95.0, issues=[]
        )
        command.results = [result]

        with patch("builtins.print") as mock_print:
            command._print_text_results()

        # Should print summary and score details
        assert mock_print.call_count > 5

    def test_print_text_results_with_failures(self):
        """Test printing text results with failures."""
        args = Namespace(score=True, include_warnings=True)
        command = ValidateCommand(args)
        command.stats["end_time"] = datetime.now()
        command.stats["files_failed"] = 1

        result = ValidationResult(
            file_path="test.yml",
            valid=False,
            score=50.0,
            issues=[ValidationIssue(1, 1, "error", "Test error", "Fix it")],
        )
        command.results = [result]

        with patch("builtins.print") as mock_print:
            command._print_text_results()

        # Should print summary, failed files, and score details
        assert mock_print.call_count > 8

    def test_print_results_json_format(self):
        """Test print results with JSON format."""
        args = Namespace(format="json")
        command = ValidateCommand(args)

        with patch.object(command, "_print_json_results") as mock_json:
            command._print_results()

        mock_json.assert_called_once()

    def test_print_results_text_format(self):
        """Test print results with text format."""
        args = Namespace(format="text")
        command = ValidateCommand(args)

        with patch.object(command, "_print_text_results") as mock_text:
            command._print_results()

        mock_text.assert_called_once()
