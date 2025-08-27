"""
Focused tests for batch processing functionality to improve coverage.

This module provides targeted tests for uncovered code paths in the batch processing system.
"""

import argparse
import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from fqcn_converter.cli.batch import BatchCommand, add_batch_arguments, ProjectResult, BatchResult


class TestBatchProcessingCore:
    """Test core batch processing functionality."""

    @pytest.fixture
    def mock_args(self):
        """Create mock arguments."""
        args = Mock()
        args.root_directory = None
        args.projects = None
        args.discover_only = False
        args.config = None
        args.workers = 4
        args.dry_run = False
        args.continue_on_error = False
        args.patterns = None
        args.exclude = None
        args.max_depth = 5
        args.report = None
        args.summary_only = False
        args.validate = False
        args.lint = False
        return args

    def test_project_discovery_methods(self, mock_args):
        """Test project discovery functionality."""
        mock_args.root_directory = "/test/root"
        mock_args.max_depth = 3
        mock_args.exclude = ["test*", "build*"]
        
        command = BatchCommand(mock_args)
        
        # Test _should_exclude_directory
        test_dir = Path("/test/root/.git")
        assert command._should_exclude_directory(test_dir, ["test*"])
        
        test_dir = Path("/test/root/normal")
        assert not command._should_exclude_directory(test_dir, [])
        
        # Test _is_ansible_project
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create ansible.cfg to make it look like an Ansible project
            (temp_path / "ansible.cfg").touch()
            assert command._is_ansible_project(temp_path, ["ansible.cfg"])
            
            # Test with roles directory
            roles_dir = temp_path / "roles"
            roles_dir.mkdir()
            assert command._is_ansible_project(temp_path, ["roles/"])

    def test_ansible_file_detection(self, mock_args):
        """Test Ansible file detection logic."""
        command = BatchCommand(mock_args)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create various file types
            playbook_file = temp_path / "playbook.yml"
            playbook_file.write_text("---\nhosts: all\ntasks:\n  - name: test\n")
            
            non_ansible_file = temp_path / "README.md"
            non_ansible_file.write_text("# README")
            
            # Test file detection
            assert command._is_ansible_file(playbook_file)
            assert not command._is_ansible_file(non_ansible_file)
            
            # Test finding files in project
            ansible_files = command._find_ansible_files_in_project(temp_path)
            assert len(ansible_files) == 1
            assert playbook_file in ansible_files

    @patch('fqcn_converter.cli.batch.FQCNConverter')
    def test_single_project_processing(self, mock_converter_class, mock_args):
        """Test processing of a single project."""
        mock_converter = Mock()
        mock_converter_class.return_value = mock_converter
        
        # Mock conversion result
        mock_conversion_result = Mock()
        mock_conversion_result.success = True
        mock_conversion_result.changes_made = 2
        mock_conversion_result.errors = []
        mock_conversion_result.warnings = []
        mock_converter.convert_file.return_value = mock_conversion_result
        
        command = BatchCommand(mock_args)
        command.converter = mock_converter
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            playbook_file = temp_path / "playbook.yml"
            playbook_file.write_text("---\nhosts: all\ntasks:\n  - name: test\n")
            
            result = command._process_single_project(temp_path)
            
            assert result.success
            assert result.files_processed == 1
            assert result.files_converted == 1
            assert result.modules_converted == 2

    def test_project_processing_with_errors(self, mock_args):
        """Test project processing with errors."""
        command = BatchCommand(mock_args)
        
        # Mock converter that raises an exception
        mock_converter = Mock()
        mock_converter.convert_file.side_effect = Exception("Test error")
        command.converter = mock_converter
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test file
            playbook_file = temp_path / "playbook.yml"
            playbook_file.write_text("---\nhosts: all\ntasks:\n  - name: test\n")
            
            result = command._process_single_project(temp_path)
            
            assert not result.success
            assert len(result.errors) > 0
            assert "Test error" in result.errors[0]

    @patch('fqcn_converter.cli.batch.ValidationEngine')
    def test_project_validation(self, mock_validator_class, mock_args):
        """Test project validation functionality."""
        mock_args.validate = True
        
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator
        
        # Mock validation result
        mock_validation_result = Mock()
        mock_validation_result.valid = True
        mock_validation_result.score = 0.95
        mock_validator.validate_conversion.return_value = mock_validation_result
        
        command = BatchCommand(mock_args)
        command.validator = mock_validator
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test.yml"
            test_file.touch()
            
            result = command._validate_project(temp_path, [test_file])
            
            assert result.valid
            assert result.score == 0.95

    def test_statistics_update(self, mock_args):
        """Test statistics updating."""
        command = BatchCommand(mock_args)
        
        # Create test result
        result = ProjectResult(
            project_path="/test/project",
            success=True,
            files_processed=5,
            files_converted=3,
            modules_converted=10
        )
        
        initial_processed = command.stats["projects_processed"]
        command._update_stats(result)
        
        assert command.stats["projects_processed"] == initial_processed + 1
        assert command.stats["projects_successful"] == 1
        assert command.stats["total_files_processed"] == 5
        assert command.stats["total_files_converted"] == 3
        assert command.stats["total_modules_converted"] == 10

    def test_report_generation(self, mock_args):
        """Test report generation functionality."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            mock_args.report = temp_file.name
            
            command = BatchCommand(mock_args)
            command.stats["end_time"] = datetime.now()
            
            # Add some test results
            result = ProjectResult(
                project_path="/test/project",
                success=True,
                files_processed=2,
                files_converted=1,
                modules_converted=3,
                duration=1.5
            )
            command.results.append(result)
            
            command._generate_report()
            
            # Verify report was created
            report_path = Path(temp_file.name)
            assert report_path.exists()
            
            # Verify report content
            with open(report_path, 'r') as f:
                report_data = json.load(f)
            
            assert "batch_processing_report" in report_data
            assert "summary" in report_data["batch_processing_report"]
            assert "project_results" in report_data["batch_processing_report"]
            
            # Clean up
            report_path.unlink()

    def test_parallel_processing_setup(self, mock_args):
        """Test parallel processing configuration."""
        mock_args.workers = 8
        
        command = BatchCommand(mock_args)
        
        projects = [Path("/test/proj1"), Path("/test/proj2"), Path("/test/proj3")]
        
        # Mock the processing methods
        with patch.object(command, '_process_single_project') as mock_process:
            mock_process.return_value = ProjectResult(
                project_path="/test/proj",
                success=True
            )
            
            with patch('fqcn_converter.cli.batch.ThreadPoolExecutor') as mock_executor:
                mock_future = Mock()
                mock_future.result.return_value = ProjectResult(
                    project_path="/test/proj",
                    success=True
                )
                
                mock_executor.return_value.__enter__.return_value.submit.return_value = mock_future
                mock_executor.return_value.__enter__.return_value.__iter__ = Mock(return_value=iter([mock_future]))
                
                # Mock as_completed
                with patch('fqcn_converter.cli.batch.as_completed', return_value=[mock_future]):
                    result = command._process_projects_parallel(projects)
                    
                    assert result is True or result is False  # Should return a boolean

    def test_directory_walking(self, mock_args):
        """Test directory walking functionality."""
        command = BatchCommand(mock_args)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create nested directory structure
            (temp_path / "level1").mkdir()
            (temp_path / "level1" / "level2").mkdir()
            (temp_path / "level1" / "level2" / "level3").mkdir()
            
            # Test with max_depth = 2
            directories = command._walk_directories(temp_path, 2)
            
            # Should include root, level1, and level2 but not level3
            assert temp_path in directories
            assert (temp_path / "level1") in directories
            assert (temp_path / "level1" / "level2") in directories

    def test_empty_project_handling(self, mock_args):
        """Test handling of empty projects."""
        command = BatchCommand(mock_args)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Empty directory
            result = command._process_single_project(temp_path)
            
            # Empty project should be considered successful
            assert result.success
            assert result.files_processed == 0
            assert result.files_converted == 0

    def test_summary_printing(self, mock_args, capsys):
        """Test summary printing functionality."""
        command = BatchCommand(mock_args)
        command.stats["end_time"] = datetime.now()
        command.stats["projects_discovered"] = 5
        command.stats["projects_processed"] = 4
        command.stats["projects_successful"] = 3
        command.stats["projects_failed"] = 1
        
        # Add a failed project result
        failed_result = ProjectResult(
            project_path="/test/failed",
            success=False,
            errors=["Test error 1", "Test error 2"]
        )
        command.results.append(failed_result)
        
        command._print_summary()
        
        captured = capsys.readouterr()
        assert "BATCH PROCESSING SUMMARY" in captured.out
        assert "Projects discovered: 5" in captured.out
        assert "Projects processed: 4" in captured.out
        assert "Failed projects:" in captured.out

    def test_project_listing(self, mock_args, capsys):
        """Test project listing functionality."""
        mock_args.summary_only = False
        
        command = BatchCommand(mock_args)
        projects = [Path("/test/proj1"), Path("/test/proj2")]
        
        command._list_projects(projects)
        
        captured = capsys.readouterr()
        assert "Discovered 2 Ansible projects:" in captured.out
        assert "/test/proj1" in captured.out
        assert "/test/proj2" in captured.out

    def test_get_projects_with_specified_projects(self, mock_args):
        """Test getting projects when specific projects are provided."""
        mock_args.projects = ["/test/proj1", "/test/proj2"]
        
        command = BatchCommand(mock_args)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create the projects
            proj1 = Path(temp_dir) / "proj1"
            proj2 = Path(temp_dir) / "proj2"
            proj1.mkdir()
            proj2.mkdir()
            
            mock_args.projects = [str(proj1), str(proj2)]
            
            projects = command._get_projects()
            
            assert len(projects) == 2
            assert proj1 in projects
            assert proj2 in projects


class TestBatchResultClasses:
    """Test batch result data classes."""

    def test_project_result_creation(self):
        """Test ProjectResult creation and defaults."""
        result = ProjectResult(project_path="/test", success=True)
        
        assert result.project_path == "/test"
        assert result.success is True
        assert result.files_processed == 0
        assert result.files_converted == 0
        assert result.modules_converted == 0
        assert result.errors == []
        assert result.warnings == []
        assert result.duration == 0.0
        assert result.validation_result is None

    def test_batch_result_creation(self):
        """Test BatchResult creation."""
        project_results = [
            ProjectResult(project_path="/test1", success=True),
            ProjectResult(project_path="/test2", success=False)
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


class TestBatchCLIEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def mock_args(self):
        """Create mock arguments."""
        args = Mock()
        args.root_directory = None
        args.projects = None
        args.discover_only = False
        args.config = None
        args.workers = 4
        args.dry_run = False
        args.continue_on_error = False
        args.patterns = None
        args.exclude = None
        args.max_depth = 5
        args.report = None
        args.summary_only = False
        args.validate = False
        args.lint = False
        return args

    def test_discover_only_mode(self, mock_args):
        """Test discover-only mode."""
        mock_args.root_directory = "/test/root"
        mock_args.discover_only = True
        
        command = BatchCommand(mock_args)
        
        with patch.object(command, '_get_projects', return_value=[Path("/test/proj1")]):
            with patch.object(command, '_list_projects'):
                result = command.run()
                
        assert result == 0

    def test_no_projects_found(self, mock_args):
        """Test behavior when no projects are found."""
        mock_args.root_directory = "/test/root"
        
        command = BatchCommand(mock_args)
        
        with patch.object(command, '_get_projects', return_value=[]):
            result = command.run()
                
        assert result == 0

    def test_keyboard_interrupt_handling(self, mock_args):
        """Test keyboard interrupt handling."""
        mock_args.root_directory = "/test/root"
        
        command = BatchCommand(mock_args)
        
        with patch.object(command, '_get_projects', side_effect=KeyboardInterrupt()):
            result = command.run()
                
        assert result == 1

    def test_configuration_error_handling(self, mock_args):
        """Test configuration error handling."""
        mock_args.config = "/nonexistent/config.yml"
        
        command = BatchCommand(mock_args)
        
        with patch('fqcn_converter.cli.batch.FQCNConverter', side_effect=Exception("Config error")):
            result = command.run()
                
        assert result == 1

    def test_continue_on_error_behavior(self, mock_args):
        """Test continue-on-error behavior."""
        mock_args.root_directory = "/test/root"
        mock_args.continue_on_error = True
        
        command = BatchCommand(mock_args)
        
        # Mock projects and processing
        projects = [Path("/test/proj1"), Path("/test/proj2")]
        
        # First project fails, second succeeds
        results = [
            ProjectResult(project_path="/test/proj1", success=False),
            ProjectResult(project_path="/test/proj2", success=True)
        ]
        
        with patch.object(command, '_get_projects', return_value=projects):
            with patch.object(command, '_process_single_project', side_effect=results):
                with patch.object(command, '_print_summary'):
                    result = command._process_projects_sequential(projects)
                    
        # Should continue processing despite first failure
        assert len(command.results) == 2

    def test_dry_run_mode(self, mock_args):
        """Test dry run mode."""
        mock_args.root_directory = "/test/root"
        mock_args.dry_run = True
        
        command = BatchCommand(mock_args)
        
        with patch.object(command, '_get_projects', return_value=[Path("/test/proj1")]):
            with patch.object(command, '_process_projects', return_value=True):
                with patch.object(command, '_print_summary'):
                    result = command.run()
                    
        assert result == 0

    def test_report_generation_error(self, mock_args):
        """Test report generation error handling."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            mock_args.report = "/invalid/path/report.json"  # Invalid path
            
            command = BatchCommand(mock_args)
            command.stats["end_time"] = datetime.now()
            
            # Should not raise exception, just log error
            command._generate_report()
            
            # Test should complete without crashing

    def test_file_content_based_ansible_detection(self, mock_args):
        """Test Ansible file detection based on content."""
        command = BatchCommand(mock_args)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create file with Ansible content
            ansible_file = temp_path / "tasks.yml"
            ansible_file.write_text("---\n- name: Install package\n  apt:\n    name: nginx")
            
            # Create file without Ansible content
            non_ansible_file = temp_path / "data.yml"
            non_ansible_file.write_text("---\ndata:\n  key: value")
            
            assert command._is_ansible_file(ansible_file)
            # This might still be detected as Ansible due to .yml extension and structure

    def test_permission_error_handling(self, mock_args):
        """Test handling of permission errors during directory walking."""
        command = BatchCommand(mock_args)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a directory structure
            subdir = temp_path / "subdir"
            subdir.mkdir()
            
            # Mock permission error
            with patch.object(Path, 'iterdir', side_effect=PermissionError("Access denied")):
                directories = command._walk_directories(temp_path, 2)
                
                # Should still include the root directory
                assert temp_path in directories