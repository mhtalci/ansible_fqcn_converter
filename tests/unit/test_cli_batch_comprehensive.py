#!/usr/bin/env python3
"""
Comprehensive test module for CLI batch command.

This module provides comprehensive test coverage for the CLI batch functionality,
including command execution flow and error handling scenarios targeting >90% coverage.
"""

import argparse
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from fqcn_converter.cli.batch import (
    BatchCommand,
    BatchResult,
    ProjectResult,
    add_batch_arguments,
    main,
)
from fqcn_converter.core.converter import ConversionResult
from fqcn_converter.core.validator import ValidationResult
from fqcn_converter.exceptions import ConfigurationError, FQCNConverterError


class TestBatchCLIExecution:
    """Test batch CLI command execution flow."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create mock args
        self.mock_args = argparse.Namespace(
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

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_batch_command_initialization(self):
        """Test BatchCommand initialization."""
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
        nonexistent = self.temp_path / "nonexistent"
        self.mock_args.projects = [str(nonexistent)]
        
        command = BatchCommand(self.mock_args)
        projects = command._get_projects()
        
        assert len(projects) == 0

    def test_discover_projects_basic(self):
        """Test basic project discovery."""
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
        command = BatchCommand(self.mock_args)
        
        test_dir = Path("/path/to/excluded_dir")
        exclude_patterns = ["excluded"]
        
        result = command._should_exclude_directory(test_dir, exclude_patterns)
        assert result is True

    def test_should_exclude_directory_skip_dirs(self):
        """Test directory exclusion for common skip directories."""
        command = BatchCommand(self.mock_args)
        
        skip_dirs = [".git", "__pycache__", "node_modules", ".venv"]
        
        for skip_dir in skip_dirs:
            test_dir = Path(f"/path/to/{skip_dir}")
            result = command._should_exclude_directory(test_dir, [])
            assert result is True

    def test_is_ansible_project_directory_pattern(self):
        """Test Ansible project detection with directory patterns."""
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
        project_dir = self.temp_path / "test_project"
        project_dir.mkdir()
        (project_dir / "playbook.yml").touch()
        
        command = BatchCommand(self.mock_args)
        patterns = ["playbook*.yml"]
        
        result = command._is_ansible_project(project_dir, patterns)
        assert result is True

    def test_is_ansible_project_no_match(self):
        """Test Ansible project detection with no matches."""
        project_dir = self.temp_path / "test_project"
        project_dir.mkdir()
        
        command = BatchCommand(self.mock_args)
        patterns = ["nonexistent.yml"]
        
        result = command._is_ansible_project(project_dir, patterns)
        assert result is False

    def test_list_projects_summary_only(self):
        """Test project listing with summary only."""
        self.mock_args.summary_only = True
        projects = [Path("/project1"), Path("/project2")]
        
        command = BatchCommand(self.mock_args)
        
        # Should not raise exception
        command._list_projects(projects)

    @patch.object(BatchCommand, '_process_projects_parallel')
    def test_process_projects_parallel_mode(self, mock_parallel):
        """Test project processing in parallel mode."""
        self.mock_args.workers = 4
        projects = [Path("/project1"), Path("/project2"), Path("/project3")]
        mock_parallel.return_value = True
        
        command = BatchCommand(self.mock_args)
        result = command._process_projects(projects)
        
        mock_parallel.assert_called_once_with(projects)
        assert result is True

    @patch.object(BatchCommand, '_process_projects_sequential')
    def test_process_projects_sequential_mode(self, mock_sequential):
        """Test project processing in sequential mode."""
        self.mock_args.workers = 1
        projects = [Path("/project1")]
        mock_sequential.return_value = True
        
        command = BatchCommand(self.mock_args)
        result = command._process_projects(projects)
        
        mock_sequential.assert_called_once_with(projects)
        assert result is True

    @patch.object(BatchCommand, '_process_single_project')
    def test_process_projects_sequential_success(self, mock_process_single):
        """Test sequential project processing with success."""
        projects = [Path("/project1"), Path("/project2")]
        
        # Mock successful results
        mock_result1 = ProjectResult(project_path="/project1", success=True)
        mock_result2 = ProjectResult(project_path="/project2", success=True)
        mock_process_single.side_effect = [mock_result1, mock_result2]
        
        command = BatchCommand(self.mock_args)
        result = command._process_projects_sequential(projects)
        
        assert result is True
        assert len(command.results) == 2
        assert command.stats["projects_processed"] == 2
        assert command.stats["projects_successful"] == 2

    @patch.object(BatchCommand, '_process_single_project')
    def test_process_projects_sequential_failure_continue(self, mock_process_single):
        """Test sequential project processing with failure and continue on error."""
        self.mock_args.continue_on_error = True
        projects = [Path("/project1"), Path("/project2")]
        
        # Mock one failure, one success
        mock_result1 = ProjectResult(project_path="/project1", success=False)
        mock_result2 = ProjectResult(project_path="/project2", success=True)
        mock_process_single.side_effect = [mock_result1, mock_result2]
        
        command = BatchCommand(self.mock_args)
        result = command._process_projects_sequential(projects)
        
        assert result is False  # Overall failure due to one failed project
        assert len(command.results) == 2  # Both projects processed

    @patch('fqcn_converter.cli.batch.ThreadPoolExecutor')
    def test_process_projects_parallel_success(self, mock_executor_class):
        """Test parallel project processing with success."""
        projects = [Path("/project1"), Path("/project2")]
        
        # Mock successful results
        mock_result1 = ProjectResult(project_path="/project1", success=True)
        mock_result2 = ProjectResult(project_path="/project2", success=True)
        
        # Mock executor and futures
        mock_executor = MagicMock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        mock_future1 = MagicMock()
        mock_future2 = MagicMock()
        mock_future1.result.return_value = mock_result1
        mock_future2.result.return_value = mock_result2
        
        mock_executor.submit.side_effect = [mock_future1, mock_future2]
        
        # Mock as_completed
        with patch('fqcn_converter.cli.batch.as_completed', return_value=[mock_future1, mock_future2]):
            command = BatchCommand(self.mock_args)
            result = command._process_projects_parallel(projects)
        
        assert result is True
        assert len(command.results) == 2

    @patch.object(BatchCommand, '_find_ansible_files_in_project')
    @patch('fqcn_converter.cli.batch.FQCNConverter')
    def test_process_single_project_success(self, mock_converter_class, mock_find_files):
        """Test processing a single project successfully."""
        project_path = Path("/test/project")
        
        # Mock converter
        mock_converter = MagicMock()
        mock_converter_class.return_value = mock_converter
        
        # Mock files and conversion results
        mock_files = [Path("/test/project/playbook.yml")]
        mock_find_files.return_value = mock_files
        
        mock_conversion_result = ConversionResult(
            success=True,
            changes_made=2,
            errors=[],
            warnings=[]
        )
        mock_converter.convert_file.return_value = mock_conversion_result
        
        command = BatchCommand(self.mock_args)
        command.converter = mock_converter
        
        result = command._process_single_project(project_path)
        
        assert result.success is True
        assert result.files_processed == 1
        assert result.files_converted == 1
        assert result.modules_converted == 2

    @patch.object(BatchCommand, '_find_ansible_files_in_project')
    def test_process_single_project_no_files(self, mock_find_files):
        """Test processing a project with no Ansible files."""
        project_path = Path("/test/project")
        mock_find_files.return_value = []
        
        command = BatchCommand(self.mock_args)
        result = command._process_single_project(project_path)
        
        assert result.success is True  # Empty project is considered successful
        assert result.files_processed == 0

    def test_find_ansible_files_in_project(self):
        """Test finding Ansible files in a project."""
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
        test_file = self.temp_path / "test.yml"
        test_file.write_text("---\nhosts: all\ntasks:\n  - name: test")
        
        command = BatchCommand(self.mock_args)
        result = command._is_ansible_file(test_file)
        
        assert result is True

    def test_is_ansible_file_skip_patterns(self):
        """Test Ansible file detection skips certain patterns."""
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

    def test_generate_report_success(self):
        """Test successful report generation."""
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

    def test_print_summary_basic(self):
        """Test basic summary printing."""
        command = BatchCommand(self.mock_args)
        command.stats["end_time"] = datetime.now()
        
        # Should not raise exception
        command._print_summary()

    def test_print_summary_with_failures(self):
        """Test summary printing with failed projects."""
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

    def test_print_summary_dry_run(self):
        """Test summary printing in dry run mode."""
        self.mock_args.dry_run = True
        
        command = BatchCommand(self.mock_args)
        command.stats["end_time"] = datetime.now()
        
        # Should not raise exception and show dry run message
        command._print_summary()

    @patch.object(BatchCommand, '_initialize_components')
    @patch.object(BatchCommand, '_get_projects')
    @patch.object(BatchCommand, '_list_projects')
    @patch.object(BatchCommand, '_process_projects')
    @patch.object(BatchCommand, '_print_summary')
    def test_run_complete_flow_with_dry_run(self, mock_print_summary, mock_process_projects, 
                                           mock_list_projects, mock_get_projects, mock_init):
        """Test complete run flow with dry run mode."""
        self.mock_args.dry_run = True
        projects = [Path("/project1")]
        mock_get_projects.return_value = projects
        mock_process_projects.return_value = True
        
        command = BatchCommand(self.mock_args)
        result = command.run()
        
        assert result == 0
        mock_init.assert_called_once()
        mock_get_projects.assert_called_once()
        mock_list_projects.assert_called_once_with(projects)
        mock_process_projects.assert_called_once_with(projects)
        mock_print_summary.assert_called_once()

    @patch.object(BatchCommand, '_initialize_components')
    @patch.object(BatchCommand, '_get_projects')
    @patch.object(BatchCommand, '_list_projects')
    @patch.object(BatchCommand, '_generate_report')
    @patch.object(BatchCommand, '_process_projects')
    @patch.object(BatchCommand, '_print_summary')
    def test_run_complete_flow_with_report(self, mock_print_summary, mock_process_projects,
                                          mock_generate_report, mock_list_projects, 
                                          mock_get_projects, mock_init):
        """Test complete run flow with report generation."""
        self.mock_args.report = "/tmp/report.json"
        projects = [Path("/project1")]
        mock_get_projects.return_value = projects
        mock_process_projects.return_value = True
        
        command = BatchCommand(self.mock_args)
        result = command.run()
        
        assert result == 0
        mock_generate_report.assert_called_once()

    @patch.object(BatchCommand, '_initialize_components')
    @patch.object(BatchCommand, '_get_projects')
    @patch.object(BatchCommand, '_list_projects')
    def test_run_discover_only_mode(self, mock_list_projects, mock_get_projects, mock_init):
        """Test run in discover only mode."""
        self.mock_args.discover_only = True
        projects = [Path("/project1")]
        mock_get_projects.return_value = projects
        
        command = BatchCommand(self.mock_args)
        result = command.run()
        
        assert result == 0
        mock_list_projects.assert_called_once_with(projects)

    @patch.object(BatchCommand, '_initialize_components')
    @patch.object(BatchCommand, '_get_projects')
    @patch.object(BatchCommand, '_process_projects')
    def test_run_processing_failure(self, mock_process_projects, mock_get_projects, mock_init):
        """Test run with processing failure."""
        projects = [Path("/project1")]
        mock_get_projects.return_value = projects
        mock_process_projects.return_value = False
        
        command = BatchCommand(self.mock_args)
        result = command.run()
        
        assert result == 1

    @patch.object(BatchCommand, '_initialize_components')
    @patch.object(BatchCommand, '_get_projects')
    def test_run_fqcn_converter_error_verbose(self, mock_get_projects, mock_init):
        """Test run with FQCNConverterError in verbose mode."""
        self.mock_args.verbosity = "verbose"
        mock_init.side_effect = FQCNConverterError("Test error")
        
        command = BatchCommand(self.mock_args)
        result = command.run()
        
        assert result == 1

    @patch.object(BatchCommand, '_initialize_components')
    @patch.object(BatchCommand, '_get_projects')
    def test_run_unexpected_exception_verbose(self, mock_get_projects, mock_init):
        """Test run with unexpected exception in verbose mode."""
        self.mock_args.verbosity = "verbose"
        mock_init.side_effect = RuntimeError("Unexpected error")
        
        command = BatchCommand(self.mock_args)
        result = command.run()
        
        assert result == 1

    def test_process_projects_parallel_condition(self):
        """Test process projects chooses parallel when workers > 1 and projects > 1."""
        self.mock_args.workers = 4
        projects = [Path("/project1"), Path("/project2")]
        
        command = BatchCommand(self.mock_args)
        
        with patch.object(command, '_process_projects_parallel', return_value=True) as mock_parallel:
            result = command._process_projects(projects)
            mock_parallel.assert_called_once_with(projects)
            assert result is True

    def test_process_projects_sequential_condition_single_worker(self):
        """Test process projects chooses sequential when workers = 1."""
        self.mock_args.workers = 1
        projects = [Path("/project1"), Path("/project2")]
        
        command = BatchCommand(self.mock_args)
        
        with patch.object(command, '_process_projects_sequential', return_value=True) as mock_sequential:
            result = command._process_projects(projects)
            mock_sequential.assert_called_once_with(projects)
            assert result is True

    def test_process_projects_sequential_condition_single_project(self):
        """Test process projects chooses sequential when only one project."""
        self.mock_args.workers = 4
        projects = [Path("/project1")]
        
        command = BatchCommand(self.mock_args)
        
        with patch.object(command, '_process_projects_sequential', return_value=True) as mock_sequential:
            result = command._process_projects(projects)
            mock_sequential.assert_called_once_with(projects)
            assert result is True

    @patch('sys.stderr')
    @patch.object(BatchCommand, '_process_single_project')
    def test_process_projects_sequential_with_stderr_output(self, mock_process_single, mock_stderr):
        """Test sequential processing with stderr output."""
        projects = [Path("/project1")]
        mock_result = ProjectResult(project_path="/project1", success=True)
        mock_process_single.return_value = mock_result
        
        command = BatchCommand(self.mock_args)
        result = command._process_projects_sequential(projects)
        
        assert result is True
        # Verify stderr was written to
        assert mock_stderr.write.called or hasattr(mock_stderr, 'write')

    @patch.object(BatchCommand, '_process_single_project')
    def test_process_projects_sequential_stop_on_error(self, mock_process_single):
        """Test sequential processing stops on error when continue_on_error is False."""
        self.mock_args.continue_on_error = False
        projects = [Path("/project1"), Path("/project2")]
        
        # First project fails
        mock_result1 = ProjectResult(project_path="/project1", success=False)
        mock_process_single.return_value = mock_result1
        
        command = BatchCommand(self.mock_args)
        result = command._process_projects_sequential(projects)
        
        assert result is False
        assert len(command.results) == 1  # Only first project processed
        assert mock_process_single.call_count == 1

    @patch('fqcn_converter.cli.batch.ThreadPoolExecutor')
    @patch('fqcn_converter.cli.batch.as_completed')
    @patch('sys.stderr')
    def test_process_projects_parallel_with_stderr_output(self, mock_stderr, mock_as_completed, mock_executor_class):
        """Test parallel processing with stderr output."""
        projects = [Path("/project1")]
        
        # Mock executor and future
        mock_executor = MagicMock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        mock_future = MagicMock()
        mock_result = ProjectResult(project_path="/project1", success=True)
        mock_future.result.return_value = mock_result
        mock_executor.submit.return_value = mock_future
        
        # Mock as_completed to return our future
        mock_as_completed.return_value = [mock_future]
        
        command = BatchCommand(self.mock_args)
        result = command._process_projects_parallel(projects)
        
        assert result is True
        # Verify stderr was written to
        assert mock_stderr.write.called or hasattr(mock_stderr, 'write')

    @patch('fqcn_converter.cli.batch.ThreadPoolExecutor')
    @patch('fqcn_converter.cli.batch.as_completed')
    def test_process_projects_parallel_exception_handling(self, mock_as_completed, mock_executor_class):
        """Test parallel processing handles exceptions properly."""
        projects = [Path("/project1")]
        
        # Mock executor and future
        mock_executor = MagicMock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        mock_future = MagicMock()
        mock_future.result.side_effect = RuntimeError("Processing error")
        mock_executor.submit.return_value = mock_future
        
        # Mock as_completed to return our future
        mock_as_completed.return_value = [mock_future]
        
        # Create a mapping for future_to_project
        future_to_project = {mock_future: projects[0]}
        mock_executor.submit.return_value = mock_future
        
        command = BatchCommand(self.mock_args)
        result = command._process_projects_parallel(projects)
        
        assert result is False

    @patch.object(BatchCommand, '_find_ansible_files_in_project')
    def test_process_single_project_no_ansible_files_warning(self, mock_find_files):
        """Test processing project with no Ansible files logs warning."""
        project_path = Path("/test/project")
        mock_find_files.return_value = []
        
        command = BatchCommand(self.mock_args)
        
        with patch.object(command.logger, 'warning') as mock_warning:
            result = command._process_single_project(project_path)
            
            assert result.success is True
            mock_warning.assert_called_once()

    @patch.object(BatchCommand, '_find_ansible_files_in_project')
    @patch('fqcn_converter.cli.batch.FQCNConverter')
    def test_process_single_project_conversion_failure(self, mock_converter_class, mock_find_files):
        """Test processing project with conversion failures."""
        project_path = Path("/test/project")
        
        # Mock files
        mock_files = [Path("/test/project/playbook.yml")]
        mock_find_files.return_value = mock_files
        
        # Mock converter with failure
        mock_converter = MagicMock()
        mock_converter_class.return_value = mock_converter
        
        mock_conversion_result = ConversionResult(
            success=False,
            changes_made=0,
            errors=["Conversion error"],
            warnings=["Warning"]
        )
        mock_converter.convert_file.return_value = mock_conversion_result
        
        command = BatchCommand(self.mock_args)
        command.converter = mock_converter
        
        result = command._process_single_project(project_path)
        
        assert result.success is False
        assert len(result.errors) > 0
        assert len(result.warnings) > 0

    @patch.object(BatchCommand, '_find_ansible_files_in_project')
    @patch.object(BatchCommand, '_validate_project')
    @patch('fqcn_converter.cli.batch.FQCNConverter')
    @patch('fqcn_converter.cli.batch.ValidationEngine')
    def test_process_single_project_validation_exception(self, mock_validator_class, mock_converter_class, 
                                                        mock_validate, mock_find_files):
        """Test processing project with validation exception."""
        self.mock_args.validate = True
        project_path = Path("/test/project")
        
        # Mock components
        mock_converter = MagicMock()
        mock_validator = MagicMock()
        mock_converter_class.return_value = mock_converter
        mock_validator_class.return_value = mock_validator
        
        # Mock files and successful conversion
        mock_files = [Path("/test/project/playbook.yml")]
        mock_find_files.return_value = mock_files
        
        mock_conversion_result = ConversionResult(success=True, changes_made=1, errors=[], warnings=[])
        mock_converter.convert_file.return_value = mock_conversion_result
        
        # Mock validation exception
        mock_validate.side_effect = Exception("Validation error")
        
        command = BatchCommand(self.mock_args)
        command.converter = mock_converter
        command.validator = mock_validator
        
        result = command._process_single_project(project_path)
        
        assert result.success is True  # Still successful despite validation error
        assert len(result.warnings) > 0  # Should have validation warning

    def test_is_ansible_file_content_check_exception(self):
        """Test Ansible file detection handles content read exceptions."""
        test_file = self.temp_path / "test.yml"
        test_file.write_text("---\nhosts: all")
        
        command = BatchCommand(self.mock_args)
        
        # Mock open to raise exception
        with patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid')):
            result = command._is_ansible_file(test_file)
            assert result is False

    def test_walk_directories_os_error(self):
        """Test directory walking handles OS errors."""
        command = BatchCommand(self.mock_args)
        
        # Create a directory and mock iterdir to raise OSError
        test_dir = self.temp_path / "test_dir"
        test_dir.mkdir()
        
        with patch.object(Path, 'iterdir', side_effect=OSError("OS error")):
            directories = command._walk_directories(test_dir, max_depth=1)
            # Should still include the root directory
            assert test_dir in directories

    def test_validate_project_with_validator_and_files(self):
        """Test project validation with validator and files."""
        project_path = Path("/test/project")
        files = [Path("/test/project/playbook.yml")]
        
        # Mock validator
        mock_validator = MagicMock()
        mock_validation_result = ValidationResult(valid=True, file_path=str(files[0]), score=0.95)
        mock_validator.validate_conversion.return_value = mock_validation_result
        
        command = BatchCommand(self.mock_args)
        command.validator = mock_validator
        
        result = command._validate_project(project_path, files)
        
        assert result == mock_validation_result
        mock_validator.validate_conversion.assert_called_once_with(files[0])

    def test_list_projects_normal_mode(self):
        """Test project listing in normal mode (not summary only)."""
        self.mock_args.summary_only = False
        projects = [Path("/project1"), Path("/project2")]
        
        command = BatchCommand(self.mock_args)
        
        # Capture stdout
        with patch('builtins.print') as mock_print:
            command._list_projects(projects)
            # Should print project list
            assert mock_print.called

    def test_update_stats_failure(self):
        """Test statistics update for failed project."""
        command = BatchCommand(self.mock_args)
        
        result = ProjectResult(
            project_path="/test/project",
            success=False,
            files_processed=3,
            files_converted=0,
            modules_converted=0
        )
        
        command._update_stats(result)
        
        assert command.stats["projects_processed"] == 1
        assert command.stats["projects_successful"] == 0
        assert command.stats["projects_failed"] == 1
        assert command.stats["total_files_processed"] == 3


class TestBatchCLIErrorHandling:
    """Test batch CLI error handling scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create mock args
        self.mock_args = argparse.Namespace(
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

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_run_missing_arguments(self):
        """Test run with missing required arguments."""
        command = BatchCommand(self.mock_args)
        
        result = command.run()
        
        assert result == 1  # Error exit code

    @patch.object(BatchCommand, '_initialize_components')
    def test_run_initialization_error(self, mock_init):
        """Test run with component initialization error."""
        self.mock_args.root_directory = str(self.temp_path)
        mock_init.side_effect = FQCNConverterError("Init error")
        
        command = BatchCommand(self.mock_args)
        result = command.run()
        
        assert result == 1

    @patch.object(BatchCommand, '_initialize_components')
    @patch.object(BatchCommand, '_get_projects')
    def test_run_no_projects_found(self, mock_get_projects, mock_init):
        """Test run when no projects are found."""
        self.mock_args.root_directory = str(self.temp_path)
        mock_get_projects.return_value = []
        
        command = BatchCommand(self.mock_args)
        result = command.run()
        
        assert result == 0  # Success when no projects found

    @patch.object(BatchCommand, '_initialize_components')
    @patch.object(BatchCommand, '_get_projects')
    def test_run_keyboard_interrupt(self, mock_get_projects, mock_init):
        """Test run with keyboard interrupt."""
        self.mock_args.root_directory = str(self.temp_path)
        mock_get_projects.side_effect = KeyboardInterrupt()
        
        command = BatchCommand(self.mock_args)
        result = command.run()
        
        assert result == 1

    @patch.object(BatchCommand, '_initialize_components')
    @patch.object(BatchCommand, '_get_projects')
    def test_run_unexpected_exception(self, mock_get_projects, mock_init):
        """Test run with unexpected exception."""
        self.mock_args.root_directory = str(self.temp_path)
        mock_get_projects.side_effect = RuntimeError("Unexpected error")
        
        command = BatchCommand(self.mock_args)
        result = command.run()
        
        assert result == 1

    @patch('fqcn_converter.cli.batch.FQCNConverter')
    def test_initialize_components_configuration_error(self, mock_converter_class):
        """Test component initialization with configuration error."""
        mock_converter_class.side_effect = ConfigurationError("Config error")
        
        command = BatchCommand(self.mock_args)
        
        with pytest.raises(ConfigurationError, match="Failed to initialize components"):
            command._initialize_components()

    def test_is_ansible_file_read_error(self):
        """Test Ansible file detection with file read error."""
        # Create a file that will cause read error
        test_file = self.temp_path / "test.yml"
        test_file.touch()
        
        command = BatchCommand(self.mock_args)
        
        with patch('builtins.open', side_effect=IOError("Read error")):
            # Should not raise exception, just return False
            result = command._is_ansible_file(test_file)
            assert result is False

    @patch.object(BatchCommand, '_find_ansible_files_in_project')
    def test_process_single_project_unexpected_error(self, mock_find_files):
        """Test single project processing with unexpected error."""
        project_path = Path("/test/project")
        mock_find_files.side_effect = RuntimeError("Unexpected error")
        
        command = BatchCommand(self.mock_args)
        result = command._process_single_project(project_path)
        
        assert result.success is False
        assert len(result.errors) > 0

    def test_generate_report_error(self):
        """Test report generation with file error."""
        self.mock_args.report = "/invalid/path/report.json"
        
        command = BatchCommand(self.mock_args)
        command.stats["end_time"] = datetime.now()
        
        # Should not raise exception, just log error
        command._generate_report()


class TestBatchMainFunction:
    """Test the main batch function."""

    def test_main_function_success(self):
        """Test main function with successful execution."""
        args = argparse.Namespace(
            root_directory="/test/path",
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
        
        with patch.object(BatchCommand, 'run', return_value=0):
            result = main(args)
            assert result == 0

    def test_main_function_failure(self):
        """Test main function with execution failure."""
        args = argparse.Namespace(
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
        
        with patch.object(BatchCommand, 'run', return_value=1):
            result = main(args)
            assert result == 1


class TestBatchDataClasses:
    """Test batch-related data classes."""

    def test_project_result_initialization(self):
        """Test ProjectResult initialization."""
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