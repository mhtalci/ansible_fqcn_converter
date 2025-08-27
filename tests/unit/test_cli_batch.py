#!/usr/bin/env python3
"""
Test module for CLI batch command.
"""

import os
import tempfile
from argparse import Namespace
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fqcn_converter.cli.batch import add_batch_arguments, main


class TestBatchParser:
    """Test batch command parser."""

    def test_add_batch_arguments(self):
        """Test that batch arguments are added correctly."""
        import argparse

        parser = argparse.ArgumentParser()
        add_batch_arguments(parser)

        assert parser is not None
        assert hasattr(parser, "parse_args")

    def test_batch_parser_required_args(self):
        """Test batch parser with required arguments."""
        import argparse

        parser = argparse.ArgumentParser()
        add_batch_arguments(parser)

        # Test with directory argument
        args = parser.parse_args(["/path/to/projects"])
        assert args.root_directory == "/path/to/projects"

    def test_batch_parser_optional_args(self):
        """Test batch parser with optional arguments."""
        import argparse

        parser = argparse.ArgumentParser()
        add_batch_arguments(parser)

        # Test with various optional arguments
        args = parser.parse_args(
            [
                "/path/to/projects",
                "--dry-run",
                "--config",
                "custom_config.yml",
                "--workers",
                "4",
            ]
        )

        assert args.root_directory == "/path/to/projects"
        assert args.dry_run is True
        assert args.config == "custom_config.yml"
        assert args.workers == 4

    def test_batch_parser_help(self):
        """Test that batch parser shows help."""
        import argparse

        parser = argparse.ArgumentParser()
        add_batch_arguments(parser)

        with pytest.raises(SystemExit):
            parser.parse_args(["--help"])


class TestBatchCommand:
    """Test batch command handling."""

    @patch("fqcn_converter.cli.batch.BatchCommand")
    def test_main_batch_command_basic(self, mock_command_class):
        """Test basic batch command handling."""
        # Mock command instance
        mock_command = MagicMock()
        mock_command.run.return_value = 0
        mock_command_class.return_value = mock_command

        # Create test arguments
        args = Namespace(
            root_directory="/path/to/projects",
            projects=None,
            dry_run=False,
            config=None,
            workers=None,
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


class TestBatchCLIExecution:
    """Test batch CLI command execution flow."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create mock args
        self.mock_args = Namespace(
            root_directory=str(self.temp_path),
            projects=None,
            discover_only=False,
            config=None,
            workers=1,
            dry_run=False,
            continue_on_error=False,
            patterns=None,
            exclude=None,
            max_depth=5,
            report=None,
            summary_only=False,
            validate=False,
            lint=False,
            verbosity="normal"
        )

    def test_batch_command_initialization(self):
        """Test BatchCommand initialization."""
        from fqcn_converter.cli.batch import BatchCommand
        
        # Create a real instance to test initialization
        command = BatchCommand(self.mock_args)
        
        assert command.args == self.mock_args
        assert command.logger is not None
        assert command.converter is None
        assert command.validator is None
        assert command.results == []
        assert "projects_discovered" in command.stats
        assert "start_time" in command.stats

    @patch('fqcn_converter.cli.batch.FQCNConverter')
    def test_initialize_components_success(self, mock_converter_class):
        """Test successful component initialization."""
        from fqcn_converter.cli.batch import BatchCommand
        
        mock_converter = MagicMock()
        mock_converter_class.return_value = mock_converter
        
        command = BatchCommand(self.mock_args)
        command._initialize_components()
        
        assert command.converter == mock_converter
        mock_converter_class.assert_called_once_with(config_path=None)

    @patch('fqcn_converter.cli.batch.FQCNConverter')
    @patch('fqcn_converter.cli.batch.ValidationEngine')
    def test_initialize_components_with_validator(self, mock_validator_class, mock_converter_class):
        """Test component initialization with validator."""
        from fqcn_converter.cli.batch import BatchCommand
        
        self.mock_args.validate = True
        mock_converter = MagicMock()
        mock_validator = MagicMock()
        mock_converter_class.return_value = mock_converter
        mock_validator_class.return_value = mock_validator
        
        command = BatchCommand(self.mock_args)
        command._initialize_components()
        
        assert command.converter == mock_converter
        assert command.validator == mock_validator
        mock_validator_class.assert_called_once()

    def test_get_projects_with_specified_projects(self):
        """Test getting projects when projects are specified."""
        from fqcn_converter.cli.batch import BatchCommand
        
        project1 = self.temp_path / "project1"
        project2 = self.temp_path / "project2"
        project1.mkdir()
        project2.mkdir()
        
        self.mock_args.projects = [str(project1), str(project2)]
        
        command = BatchCommand(self.mock_args)
        projects = command._get_projects()
        
        assert len(projects) == 2
        assert project1 in projects
        assert project2 in projects

    def test_get_projects_with_nonexistent_projects(self):
        """Test getting projects with non-existent project paths."""
        from fqcn_converter.cli.batch import BatchCommand
        
        nonexistent = self.temp_path / "nonexistent"
        self.mock_args.projects = [str(nonexistent)]
        
        command = BatchCommand(self.mock_args)
        projects = command._get_projects()
        
        assert len(projects) == 0

    def test_discover_projects_basic(self):
        """Test basic project discovery."""
        from fqcn_converter.cli.batch import BatchCommand
        
        # Create a project with ansible indicators
        project_dir = self.temp_path / "ansible_project"
        project_dir.mkdir()
        (project_dir / "playbook.yml").touch()
        
        command = BatchCommand(self.mock_args)
        projects = command._discover_projects(self.temp_path)
        
        assert len(projects) >= 1
        assert project_dir in projects

    def test_discover_projects_with_exclude_patterns(self):
        """Test project discovery with exclude patterns."""
        from fqcn_converter.cli.batch import BatchCommand
        
        # Create projects
        project_dir = self.temp_path / "ansible_project"
        excluded_dir = self.temp_path / "excluded_project"
        project_dir.mkdir()
        excluded_dir.mkdir()
        (project_dir / "playbook.yml").touch()
        (excluded_dir / "playbook.yml").touch()
        
        self.mock_args.exclude = ["excluded"]
        
        command = BatchCommand(self.mock_args)
        projects = command._discover_projects(self.temp_path)
        
        assert project_dir in projects
        assert excluded_dir not in projects

    def test_walk_directories_max_depth(self):
        """Test directory walking with max depth limit."""
        from fqcn_converter.cli.batch import BatchCommand
        
        # Create nested directory structure
        level1 = self.temp_path / "level1"
        level2 = level1 / "level2"
        level3 = level2 / "level3"
        level1.mkdir()
        level2.mkdir()
        level3.mkdir()
        
        command = BatchCommand(self.mock_args)
        directories = command._walk_directories(self.temp_path, max_depth=2)
        
        assert self.temp_path in directories
        assert level1 in directories
        assert level2 in directories

    def test_should_exclude_directory_patterns(self):
        """Test directory exclusion based on patterns."""
        from fqcn_converter.cli.batch import BatchCommand
        
        command = BatchCommand(self.mock_args)
        
        test_dir = Path("/path/to/excluded_dir")
        exclude_patterns = ["excluded"]
        
        result = command._should_exclude_directory(test_dir, exclude_patterns)
        assert result is True

    def test_should_exclude_directory_skip_dirs(self):
        """Test directory exclusion for common skip directories."""
        from fqcn_converter.cli.batch import BatchCommand
        
        command = BatchCommand(self.mock_args)
        
        skip_dirs = [".git", "__pycache__", "node_modules", ".venv"]
        
        for skip_dir in skip_dirs:
            test_dir = Path(f"/path/to/{skip_dir}")
            result = command._should_exclude_directory(test_dir, [])
            assert result is True

    def test_is_ansible_project_directory_pattern(self):
        """Test Ansible project detection with directory patterns."""
        from fqcn_converter.cli.batch import BatchCommand
        
        project_dir = self.temp_path / "test_project"
        roles_dir = project_dir / "roles"
        project_dir.mkdir()
        roles_dir.mkdir()
        
        command = BatchCommand(self.mock_args)
        patterns = ["roles/"]
        
        result = command._is_ansible_project(project_dir, patterns)
        assert result is True

    def test_is_ansible_project_file_pattern(self):
        """Test Ansible project detection with file patterns."""
        from fqcn_converter.cli.batch import BatchCommand
        
        project_dir = self.temp_path / "test_project"
        project_dir.mkdir()
        (project_dir / "playbook.yml").touch()
        
        command = BatchCommand(self.mock_args)
        patterns = ["playbook*.yml"]
        
        result = command._is_ansible_project(project_dir, patterns)
        assert result is True

    def test_is_ansible_project_no_match(self):
        """Test Ansible project detection with no matches."""
        from fqcn_converter.cli.batch import BatchCommand
        
        project_dir = self.temp_path / "test_project"
        project_dir.mkdir()
        
        command = BatchCommand(self.mock_args)
        patterns = ["nonexistent.yml"]
        
        result = command._is_ansible_project(project_dir, patterns)
        assert result is False

    def test_list_projects_summary_only(self):
        """Test project listing with summary only."""
        from fqcn_converter.cli.batch import BatchCommand
        
        self.mock_args.summary_only = True
        projects = [Path("/project1"), Path("/project2")]
        
        command = BatchCommand(self.mock_args)
        
        # Should not raise exception
        command._list_projects(projects)

    @patch.object(Path, 'iterdir')
    def test_walk_directories_permission_error(self, mock_iterdir):
        """Test directory walking with permission errors."""
        from fqcn_converter.cli.batch import BatchCommand
        
        mock_iterdir.side_effect = PermissionError("Access denied")
        
        command = BatchCommand(self.mock_args)
        
        # Should not raise exception, just log and continue
        directories = command._walk_directories(self.temp_path, max_depth=1)
        assert self.temp_path in directories

    def test_find_ansible_files_in_project(self):
        """Test finding Ansible files in a project."""
        from fqcn_converter.cli.batch import BatchCommand
        
        project_dir = self.temp_path / "test_project"
        project_dir.mkdir()
        
        # Create test files
        (project_dir / "playbook.yml").write_text("---\nhosts: all\ntasks: []")
        (project_dir / "inventory.ini").touch()  # Not a YAML file
        (project_dir / "tasks.yaml").write_text("---\n- name: test task")
        
        subdir = project_dir / "roles" / "test_role" / "tasks"
        subdir.mkdir(parents=True)
        (subdir / "main.yml").write_text("---\n- name: role task")
        
        command = BatchCommand(self.mock_args)
        files = command._find_ansible_files_in_project(project_dir)
        
        # Should find YAML files that appear to be Ansible files
        assert len(files) >= 2  # At least playbook.yml and tasks.yaml

    def test_is_ansible_file_by_name(self):
        """Test Ansible file detection by filename."""
        from fqcn_converter.cli.batch import BatchCommand
        
        command = BatchCommand(self.mock_args)
        
        # Test files that should be detected as Ansible files
        ansible_files = [
            Path("/project/playbook.yml"),
            Path("/project/site.yml"),
            Path("/project/main.yml"),
            Path("/project/roles/test/tasks/main.yml"),
        ]
        
        for file_path in ansible_files:
            result = command._is_ansible_file(file_path)
            assert result is True, f"Failed to detect {file_path} as Ansible file"

    def test_is_ansible_file_by_content(self):
        """Test Ansible file detection by content."""
        from fqcn_converter.cli.batch import BatchCommand
        
        test_file = self.temp_path / "test.yml"
        test_file.write_text("---\nhosts: all\ntasks:\n  - name: test")
        
        command = BatchCommand(self.mock_args)
        result = command._is_ansible_file(test_file)
        
        assert result is True

    def test_is_ansible_file_skip_patterns(self):
        """Test Ansible file detection skips certain patterns."""
        from fqcn_converter.cli.batch import BatchCommand
        
        command = BatchCommand(self.mock_args)
        
        # Test files that should be skipped
        skip_files = [
            Path("/project/.git/config.yml"),
            Path("/project/__pycache__/test.yml"),
            Path("/project/node_modules/package.yml"),
        ]
        
        for file_path in skip_files:
            result = command._is_ansible_file(file_path)
            assert result is False, f"Should skip {file_path}"

    def test_update_stats_success(self):
        """Test statistics update for successful project."""
        from fqcn_converter.cli.batch import BatchCommand, ProjectResult
        
        command = BatchCommand(self.mock_args)
        
        result = ProjectResult(
            project_path="/test/project",
            success=True,
            files_processed=5,
            files_converted=3,
            modules_converted=10
        )
        
        command._update_stats(result)
        
        assert command.stats["projects_processed"] == 1
        assert command.stats["projects_successful"] == 1
        assert command.stats["projects_failed"] == 0
        assert command.stats["total_files_processed"] == 5
        assert command.stats["total_files_converted"] == 3
        assert command.stats["total_modules_converted"] == 10

    def test_print_summary_basic(self):
        """Test basic summary printing."""
        from fqcn_converter.cli.batch import BatchCommand
        from datetime import datetime
        
        command = BatchCommand(self.mock_args)
        command.stats["end_time"] = datetime.now()
        
        # Should not raise exception
        command._print_summary()

    def test_print_summary_dry_run(self):
        """Test summary printing in dry run mode."""
        from fqcn_converter.cli.batch import BatchCommand
        from datetime import datetime
        
        self.mock_args.dry_run = True
        
        command = BatchCommand(self.mock_args)
        command.stats["end_time"] = datetime.now()
        
        # Should not raise exception and show dry run message
        command._print_summary()


class TestBatchCLIErrorHandling:
    """Test batch CLI error handling scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create mock args
        self.mock_args = Namespace(
            root_directory=None,
            projects=None,
            discover_only=False,
            config=None,
            workers=1,
            dry_run=False,
            continue_on_error=False,
            patterns=None,
            exclude=None,
            max_depth=5,
            report=None,
            summary_only=False,
            validate=False,
            lint=False,
            verbosity="normal"
        )

    def test_run_missing_arguments(self):
        """Test run with missing required arguments."""
        from fqcn_converter.cli.batch import BatchCommand
        
        command = BatchCommand(self.mock_args)
        
        result = command.run()
        
        assert result == 1  # Error exit code

    @patch('fqcn_converter.cli.batch.BatchCommand._initialize_components')
    def test_run_initialization_error(self, mock_init):
        """Test run with component initialization error."""
        from fqcn_converter.cli.batch import BatchCommand
        from fqcn_converter.exceptions import FQCNConverterError
        
        self.mock_args.root_directory = str(self.temp_path)
        mock_init.side_effect = FQCNConverterError("Init error")
        
        command = BatchCommand(self.mock_args)
        result = command.run()
        
        assert result == 1

    @patch('fqcn_converter.cli.batch.BatchCommand._initialize_components')
    @patch('fqcn_converter.cli.batch.BatchCommand._get_projects')
    def test_run_no_projects_found(self, mock_get_projects, mock_init):
        """Test run when no projects are found."""
        from fqcn_converter.cli.batch import BatchCommand
        
        self.mock_args.root_directory = str(self.temp_path)
        mock_get_projects.return_value = []
        
        command = BatchCommand(self.mock_args)
        result = command.run()
        
        assert result == 0  # Success when no projects found

    @patch('fqcn_converter.cli.batch.BatchCommand._initialize_components')
    @patch('fqcn_converter.cli.batch.BatchCommand._get_projects')
    def test_run_keyboard_interrupt(self, mock_get_projects, mock_init):
        """Test run with keyboard interrupt."""
        from fqcn_converter.cli.batch import BatchCommand
        
        self.mock_args.root_directory = str(self.temp_path)
        mock_get_projects.side_effect = KeyboardInterrupt()
        
        command = BatchCommand(self.mock_args)
        result = command.run()
        
        assert result == 1

    @patch('fqcn_converter.cli.batch.FQCNConverter')
    def test_initialize_components_configuration_error(self, mock_converter_class):
        """Test component initialization with configuration error."""
        from fqcn_converter.cli.batch import BatchCommand
        from fqcn_converter.exceptions import ConfigurationError
        
        mock_converter_class.side_effect = ConfigurationError("Config error")
        
        command = BatchCommand(self.mock_args)
        
        with pytest.raises(ConfigurationError, match="Failed to initialize components"):
            command._initialize_components()

    def test_is_ansible_file_read_error(self):
        """Test Ansible file detection with file read error."""
        from fqcn_converter.cli.batch import BatchCommand
        
        # Create a file that will cause read error
        test_file = self.temp_path / "test.yml"
        test_file.touch()
        
        command = BatchCommand(self.mock_args)
        
        with patch('builtins.open', side_effect=IOError("Read error")):
            # Should not raise exception, just return False
            result = command._is_ansible_file(test_file)
            assert result is False

    def test_generate_report_error(self):
        """Test report generation with file error."""
        from fqcn_converter.cli.batch import BatchCommand
        from datetime import datetime
        
        self.mock_args.report = "/invalid/path/report.json"
        
        command = BatchCommand(self.mock_args)
        command.stats["end_time"] = datetime.now()
        
        # Should not raise exception, just log error
        command._generate_report()


    def test_find_ansible_files_in_project_empty_directory(self):
        """Test finding Ansible files in empty directory."""
        from fqcn_converter.cli.batch import BatchCommand
        
        project_dir = self.temp_path / "empty_project"
        project_dir.mkdir()
        
        command = BatchCommand(self.mock_args)
        files = command._find_ansible_files_in_project(project_dir)
        
        # Should return empty list for empty directory
        assert files == []

    def test_validate_project_no_files(self):
        """Test project validation with no files."""
        from fqcn_converter.cli.batch import BatchCommand
        
        command = BatchCommand(self.mock_args)
        
        result = command._validate_project(Path("/test/project"), [])
        
        assert result.valid is True
        assert result.score == 1.0

    @patch('fqcn_converter.cli.batch.ValidationEngine')
    def test_validate_project_with_files(self, mock_validator_class):
        """Test project validation with files."""
        from fqcn_converter.cli.batch import BatchCommand
        from fqcn_converter.core.validator import ValidationResult
        
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        
        mock_validation_result = ValidationResult(valid=True, file_path="/test/file.yml", score=0.9)
        mock_validator.validate_conversion.return_value = mock_validation_result
        
        command = BatchCommand(self.mock_args)
        command.validator = mock_validator
        
        files = [Path("/test/file.yml")]
        result = command._validate_project(Path("/test/project"), files)
        
        assert result == mock_validation_result

    def test_generate_report_success(self):
        """Test successful report generation."""
        from fqcn_converter.cli.batch import BatchCommand, ProjectResult
        from datetime import datetime
        import json
        
        report_file = self.temp_path / "report.json"
        self.mock_args.report = str(report_file)
        
        command = BatchCommand(self.mock_args)
        command.stats["end_time"] = datetime.now()
        
        # Add some test results
        result = ProjectResult(
            project_path="/test/project",
            success=True,
            files_processed=2,
            files_converted=1,
            modules_converted=3
        )
        command.results.append(result)
        command._update_stats(result)
        
        command._generate_report()
        
        assert report_file.exists()
        
        # Verify report content
        with open(report_file) as f:
            report_data = json.load(f)
        
        assert "batch_processing_report" in report_data
        assert "summary" in report_data["batch_processing_report"]
        assert "project_results" in report_data["batch_processing_report"]

    def test_print_summary_with_failures(self):
        """Test summary printing with failed projects."""
        from fqcn_converter.cli.batch import BatchCommand, ProjectResult
        from datetime import datetime
        
        command = BatchCommand(self.mock_args)
        command.stats["end_time"] = datetime.now()
        command.stats["projects_failed"] = 1
        
        # Add failed result
        failed_result = ProjectResult(
            project_path="/test/failed_project",
            success=False,
            errors=["Error 1", "Error 2", "Error 3", "Error 4"]  # More than 3 errors
        )
        command.results.append(failed_result)
        
        # Should not raise exception
        command._print_summary()

    @patch.object(Path, 'exists')
    @patch.object(Path, 'is_dir')
    def test_get_projects_mixed_existence(self, mock_is_dir, mock_exists):
        """Test getting projects with mixed existence."""
        from fqcn_converter.cli.batch import BatchCommand
        
        # Mock one existing, one non-existing
        mock_exists.side_effect = [True, False]
        mock_is_dir.side_effect = [True, False]
        
        self.mock_args.projects = ["/existing/project", "/nonexistent/project"]
        
        command = BatchCommand(self.mock_args)
        projects = command._get_projects()
        
        # Should only return the existing project
        assert len(projects) == 1
        assert projects[0] == Path("/existing/project")

    @patch('fqcn_converter.cli.batch.BatchCommand._process_single_project')
    def test_process_projects_sequential_failure_stop(self, mock_process_single):
        """Test sequential project processing with failure and stop on error."""
        from fqcn_converter.cli.batch import BatchCommand, ProjectResult
        
        self.mock_args.continue_on_error = False
        projects = [Path("/project1"), Path("/project2")]
        
        # Mock failure on first project
        mock_result1 = ProjectResult(project_path="/project1", success=False)
        mock_process_single.return_value = mock_result1
        
        command = BatchCommand(self.mock_args)
        result = command._process_projects_sequential(projects)
        
        assert result is False
        assert len(command.results) == 1  # Only first project processed

    @patch('fqcn_converter.cli.batch.ThreadPoolExecutor')
    def test_process_projects_parallel_exception(self, mock_executor_class):
        """Test parallel project processing with exception."""
        from fqcn_converter.cli.batch import BatchCommand
        
        projects = [Path("/project1")]
        
        # Mock executor and future with exception
        mock_executor = MagicMock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        mock_future = MagicMock()
        mock_future.result.side_effect = Exception("Processing error")
        mock_executor.submit.return_value = mock_future
        
        # Mock as_completed
        with patch('fqcn_converter.cli.batch.as_completed', return_value=[mock_future]):
            command = BatchCommand(self.mock_args)
            result = command._process_projects_parallel(projects)
        
        assert result is False

    @patch('fqcn_converter.cli.batch.BatchCommand._find_ansible_files_in_project')
    @patch('fqcn_converter.cli.batch.FQCNConverter')
    def test_process_single_project_conversion_error(self, mock_converter_class, mock_find_files):
        """Test processing a project with conversion errors."""
        from fqcn_converter.cli.batch import BatchCommand
        
        project_path = Path("/test/project")
        
        # Mock converter
        mock_converter = MagicMock()
        mock_converter_class.return_value = mock_converter
        
        # Mock files
        mock_files = [Path("/test/project/playbook.yml")]
        mock_find_files.return_value = mock_files
        
        # Mock conversion failure
        mock_converter.convert_file.side_effect = Exception("Conversion error")
        
        command = BatchCommand(self.mock_args)
        command.converter = mock_converter
        
        result = command._process_single_project(project_path)
        
        assert result.success is False
        assert len(result.errors) > 0

    @patch('fqcn_converter.cli.batch.BatchCommand._find_ansible_files_in_project')
    @patch('fqcn_converter.cli.batch.BatchCommand._validate_project')
    @patch('fqcn_converter.cli.batch.FQCNConverter')
    @patch('fqcn_converter.cli.batch.ValidationEngine')
    def test_process_single_project_with_validation(self, mock_validator_class, mock_converter_class, mock_validate, mock_find_files):
        """Test processing a project with validation enabled."""
        from fqcn_converter.cli.batch import BatchCommand
        from fqcn_converter.core.converter import ConversionResult
        from fqcn_converter.core.validator import ValidationResult
        
        self.mock_args.validate = True
        project_path = Path("/test/project")
        
        # Mock components
        mock_converter = MagicMock()
        mock_validator = MagicMock()
        mock_converter_class.return_value = mock_converter
        mock_validator_class.return_value = mock_validator
        
        # Mock files and results
        mock_files = [Path("/test/project/playbook.yml")]
        mock_find_files.return_value = mock_files
        
        mock_conversion_result = ConversionResult(success=True, file_path="/test/project/playbook.yml", changes_made=1, errors=[], warnings=[])
        mock_converter.convert_file.return_value = mock_conversion_result
        
        mock_validation_result = ValidationResult(valid=True, file_path=str(project_path), score=0.95)
        mock_validate.return_value = mock_validation_result
        
        command = BatchCommand(self.mock_args)
        command.converter = mock_converter
        command.validator = mock_validator
        
        result = command._process_single_project(project_path)
        
        assert result.success is True
        assert result.validation_result == mock_validation_result

    @patch('fqcn_converter.cli.batch.BatchCommand._find_ansible_files_in_project')
    @patch('fqcn_converter.cli.batch.BatchCommand._validate_project')
    @patch('fqcn_converter.cli.batch.FQCNConverter')
    def test_process_single_project_validation_error(self, mock_converter_class, mock_validate, mock_find_files):
        """Test single project processing with validation error."""
        from fqcn_converter.cli.batch import BatchCommand
        from fqcn_converter.core.converter import ConversionResult
        
        self.mock_args.validate = True
        project_path = Path("/test/project")
        
        # Mock converter and files
        mock_converter = MagicMock()
        mock_converter_class.return_value = mock_converter
        mock_find_files.return_value = [Path("/test/project/playbook.yml")]
        
        mock_conversion_result = ConversionResult(success=True, file_path="/test/project/playbook.yml", changes_made=1, errors=[], warnings=[])
        mock_converter.convert_file.return_value = mock_conversion_result
        
        # Mock validation error
        mock_validate.side_effect = Exception("Validation error")
        
        command = BatchCommand(self.mock_args)
        command.converter = mock_converter
        command.validator = MagicMock()
        
        result = command._process_single_project(project_path)
        
        assert result.success is True  # Should still succeed despite validation error
        assert len(result.warnings) > 0  # Should have validation warning

    @patch('fqcn_converter.cli.batch.BatchCommand._find_ansible_files_in_project')
    def test_process_single_project_unexpected_error(self, mock_find_files):
        """Test single project processing with unexpected error."""
        from fqcn_converter.cli.batch import BatchCommand
        
        project_path = Path("/test/project")
        mock_find_files.side_effect = RuntimeError("Unexpected error")
        
        command = BatchCommand(self.mock_args)
        result = command._process_single_project(project_path)
        
        assert result.success is False
        assert len(result.errors) > 0

    def test_update_stats_failure(self):
        """Test statistics update for failed project."""
        from fqcn_converter.cli.batch import BatchCommand, ProjectResult
        
        command = BatchCommand(self.mock_args)
        
        result = ProjectResult(
            project_path="/test/project",
            success=False,
            files_processed=2,
            files_converted=0,
            modules_converted=0
        )
        
        command._update_stats(result)
        
        assert command.stats["projects_processed"] == 1
        assert command.stats["projects_successful"] == 0
        assert command.stats["projects_failed"] == 1

    @patch('fqcn_converter.cli.batch.BatchCommand._initialize_components')
    @patch('fqcn_converter.cli.batch.BatchCommand._get_projects')
    @patch('fqcn_converter.cli.batch.BatchCommand._process_projects')
    def test_run_processing_failure(self, mock_process, mock_get_projects, mock_init):
        """Test run with project processing failure."""
        from fqcn_converter.cli.batch import BatchCommand
        
        self.mock_args.root_directory = str(self.temp_path)
        mock_get_projects.return_value = [Path("/test/project")]
        mock_process.return_value = False  # Processing failed
        
        command = BatchCommand(self.mock_args)
        result = command.run()
        
        assert result == 1

    @patch('fqcn_converter.cli.batch.BatchCommand._initialize_components')
    @patch('fqcn_converter.cli.batch.BatchCommand._get_projects')
    def test_run_unexpected_exception_verbose(self, mock_get_projects, mock_init):
        """Test run with unexpected exception in verbose mode."""
        from fqcn_converter.cli.batch import BatchCommand
        
        self.mock_args.root_directory = str(self.temp_path)
        self.mock_args.verbosity = "verbose"
        mock_get_projects.side_effect = RuntimeError("Unexpected error")
        
        command = BatchCommand(self.mock_args)
        result = command.run()
        
        assert result == 1

    def test_run_discover_only_mode(self):
        """Test run in discover-only mode."""
        from fqcn_converter.cli.batch import BatchCommand
        
        # Create a project with ansible indicators
        project_dir = self.temp_path / "ansible_project"
        project_dir.mkdir()
        (project_dir / "playbook.yml").touch()
        
        self.mock_args.discover_only = True
        self.mock_args.root_directory = str(self.temp_path)  # Set root directory
        
        command = BatchCommand(self.mock_args)
        
        with patch.object(command, '_initialize_components'):
            result = command.run()
        
        assert result == 0  # Should succeed in discover-only mode

    @patch('fqcn_converter.cli.batch.BatchCommand._initialize_components')
    @patch('fqcn_converter.cli.batch.BatchCommand._get_projects')
    @patch('fqcn_converter.cli.batch.BatchCommand._process_projects')
    @patch('fqcn_converter.cli.batch.BatchCommand._generate_report')
    @patch('fqcn_converter.cli.batch.BatchCommand._print_summary')
    def test_run_with_report_generation(self, mock_print_summary, mock_generate_report, mock_process, mock_get_projects, mock_init):
        """Test run with report generation."""
        from fqcn_converter.cli.batch import BatchCommand
        from datetime import datetime
        
        self.mock_args.root_directory = str(self.temp_path)
        self.mock_args.report = "/tmp/report.json"
        mock_get_projects.return_value = [Path("/test/project")]
        mock_process.return_value = True
        
        command = BatchCommand(self.mock_args)
        # Set end_time to avoid the datetime subtraction error
        command.stats["end_time"] = datetime.now()
        
        result = command.run()
        
        assert result == 0
        mock_generate_report.assert_called_once()

    def test_project_result_with_data(self):
        """Test ProjectResult with data."""
        from fqcn_converter.cli.batch import ProjectResult
        from fqcn_converter.core.validator import ValidationResult
        
        validation_result = ValidationResult(valid=True, file_path="/test/file.yml", score=0.9)
        
        result = ProjectResult(
            project_path="/test/project",
            success=True,
            files_processed=5,
            files_converted=3,
            modules_converted=10,
            errors=["Error 1"],
            warnings=["Warning 1"],
            duration=1.5,
            validation_result=validation_result
        )
        
        assert result.files_processed == 5
        assert result.files_converted == 3
        assert result.modules_converted == 10
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert result.duration == 1.5
        assert result.validation_result == validation_result


class TestBatchDataClasses:
    """Test batch-related data classes."""

    def test_project_result_initialization(self):
        """Test ProjectResult initialization."""
        from fqcn_converter.cli.batch import ProjectResult
        
        result = ProjectResult(project_path="/test/project", success=True)
        
        assert result.project_path == "/test/project"
        assert result.success is True
        assert result.files_processed == 0
        assert result.files_converted == 0
        assert result.modules_converted == 0
        assert result.errors == []
        assert result.warnings == []
        assert result.duration == 0.0
        assert result.validation_result is None

    def test_batch_result_initialization(self):
        """Test BatchResult initialization."""
        from fqcn_converter.cli.batch import BatchResult, ProjectResult
        
        project_results = [
            ProjectResult(project_path="/project1", success=True),
            ProjectResult(project_path="/project2", success=False)
        ]
        
        result = BatchResult(
            total_projects=2,
            successful_projects=1,
            failed_projects=1,
            project_results=project_results,
            execution_time=10.5,
            summary_report="Test summary"
        )
        
        assert result.total_projects == 2
        assert result.successful_projects == 1
        assert result.failed_projects == 1
        assert len(result.project_results) == 2
        assert result.execution_time == 10.5
        assert result.summary_report == "Test summary"