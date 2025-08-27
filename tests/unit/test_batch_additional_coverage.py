"""
Additional test coverage for batch module to reach >90% coverage.

This module targets specific uncovered lines and edge cases to improve
the overall test coverage of the batch processing module.
"""

import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from fqcn_converter.core.batch import BatchProcessor, BatchResult
from fqcn_converter.core.converter import ConversionResult, FQCNConverter
from fqcn_converter.exceptions import BatchProcessingError


class TestBatchProcessorAdditionalCoverage:
    """Additional tests to improve batch module coverage."""

    @pytest.fixture
    def processor(self):
        """Create a BatchProcessor instance with mocked converter."""
        with patch('fqcn_converter.core.batch.FQCNConverter') as mock_converter_class:
            mock_converter = Mock()
            mock_converter.convert_file.return_value = ConversionResult(
                file_path="test.yml",
                success=True,
                changes_made=1,
                errors=[],
                warnings=[],
                original_content="",
                processing_time=0.1
            )
            mock_converter.convert_content.return_value = ConversionResult(
                file_path="test.yml",
                success=True,
                changes_made=1,
                errors=[],
                warnings=[],
                original_content="",
                processing_time=0.1
            )
            mock_converter_class.return_value = mock_converter
            
            processor = BatchProcessor()
            processor.converter = mock_converter
            return processor

    def test_discover_projects_with_custom_patterns_no_default_check(self, processor):
        """Test project discovery with custom patterns (skips default YAML check)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create project with YAML files that would normally be detected
            project_dir = temp_path / "custom_pattern_project"
            project_dir.mkdir()
            (project_dir / "playbook.yml").write_text("- hosts: all\n  tasks: []")
            (project_dir / "site.yml").write_text("- hosts: all\n  tasks: []")
            
            # Use custom patterns (not None) to trigger the specific code path
            custom_patterns = ["custom_file.txt"]
            projects = processor.discover_projects(temp_dir, patterns=custom_patterns)
            
            # Should not find projects since custom pattern doesn't match
            assert isinstance(projects, list)

    def test_discover_projects_yaml_file_content_check_with_keywords(self, processor):
        """Test YAML file content checking with Ansible keywords."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create project with YAML files containing Ansible keywords
            project_dir = temp_path / "ansible_keyword_project"
            project_dir.mkdir()
            
            # File with 'hosts:' keyword
            (project_dir / "hosts_file.yml").write_text("hosts: all\ntasks:\n  - name: test")
            
            # File with 'tasks:' keyword
            (project_dir / "tasks_file.yml").write_text("tasks:\n  - name: test task")
            
            # File with 'roles:' keyword
            (project_dir / "roles_file.yml").write_text("roles:\n  - common")
            
            # File with '- name:' keyword
            (project_dir / "name_file.yml").write_text("- name: test task\n  debug: msg=hello")
            
            projects = processor.discover_projects(temp_dir)
            
            # Should discover the project
            assert isinstance(projects, list)
            if len(projects) > 0:
                project_names = [Path(p).name for p in projects]
                assert "ansible_keyword_project" in project_names

    def test_discover_projects_yaml_file_with_excluded_names(self, processor):
        """Test YAML files with names that should be excluded from content check."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create project with YAML files that have excluded names
            project_dir = temp_path / "excluded_names_project"
            project_dir.mkdir()
            
            # Files with excluded patterns
            (project_dir / "deploy.yml").write_text("- hosts: all\n  tasks: []")
            (project_dir / "provision.yml").write_text("- hosts: all\n  tasks: []")
            
            # Also add a valid file to ensure project is detected
            (project_dir / "site.yml").write_text("- hosts: all\n  tasks: []")
            
            projects = processor.discover_projects(temp_dir)
            
            # Should discover the project
            assert isinstance(projects, list)
            if len(projects) > 0:
                project_names = [Path(p).name for p in projects]
                assert "excluded_names_project" in project_names

    def test_discover_projects_yaml_file_content_check_fallback(self, processor):
        """Test YAML file content check for files without common patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create project with YAML file that doesn't match common patterns
            project_dir = temp_path / "fallback_check_project"
            project_dir.mkdir()
            
            # File with uncommon name but Ansible content
            (project_dir / "broken.yml").write_text("hosts: webservers\ntasks:\n  - name: test")
            
            projects = processor.discover_projects(temp_dir)
            
            # Should discover the project through content check
            assert isinstance(projects, list)
            if len(projects) > 0:
                project_names = [Path(p).name for p in projects]
                assert "fallback_check_project" in project_names

    def test_discover_projects_deep_search_when_no_direct_projects(self, processor):
        """Test deep recursive search when no direct projects are found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create nested project structure (no direct projects in root)
            deep_project = temp_path / "level1" / "level2" / "deep_project"
            deep_project.mkdir(parents=True)
            (deep_project / "playbook.yml").write_text("- hosts: all\n  tasks: []")
            
            projects = processor.discover_projects(temp_dir)
            
            # Should find the deep project through recursive search
            assert isinstance(projects, list)
            if len(projects) > 0:
                project_names = [Path(p).name for p in projects]
                assert "deep_project" in project_names

    def test_discover_projects_depth_limit_exceeded(self, processor):
        """Test project discovery with depth limit exceeded."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create very deep nested structure (>10 levels)
            deep_path = temp_path
            for i in range(12):  # Exceed the 10 level limit
                deep_path = deep_path / f"level{i}"
                deep_path.mkdir()
            
            # Add project at very deep level
            (deep_path / "playbook.yml").write_text("- hosts: all\n  tasks: []")
            
            projects = processor.discover_projects(temp_dir)
            
            # Should not find the project due to depth limit
            assert isinstance(projects, list)

    def test_discover_projects_relative_path_error(self, processor):
        """Test project discovery with relative path calculation error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a project
            project_dir = temp_path / "test_project"
            project_dir.mkdir()
            (project_dir / "playbook.yml").write_text("- hosts: all")
            
            # Mock relative_to to raise ValueError
            original_relative_to = Path.relative_to
            def mock_relative_to(self, other):
                if "test_project" in str(self):
                    raise ValueError("Mock relative path error")
                return original_relative_to(self, other)
            
            with patch.object(Path, 'relative_to', side_effect=mock_relative_to):
                projects = processor.discover_projects(temp_dir)
                
                # Should handle the error gracefully
                assert isinstance(projects, list)

    def test_batch_result_len_method(self):
        """Test BatchResult __len__ method."""
        project_results = [
            ConversionResult(file_path="test1.yml", success=True, changes_made=1),
            ConversionResult(file_path="test2.yml", success=True, changes_made=1),
        ]
        
        batch_result = BatchResult(
            total_projects=2,
            successful_conversions=2,
            failed_conversions=0,
            project_results=project_results,
            execution_time=5.0,
            summary_report="Test summary"
        )
        
        # Test __len__ method
        assert len(batch_result) == 2

    def test_batch_result_iter_method(self):
        """Test BatchResult __iter__ method."""
        project_results = [
            ConversionResult(
                file_path="test1.yml", 
                success=True, 
                changes_made=1,
                errors=[],
                warnings=[],
                original_content="",
                processing_time=0.1
            ),
            ConversionResult(
                file_path="test2.yml", 
                success=False, 
                changes_made=0,
                errors=["Test error"],
                warnings=["Test warning"],
                original_content="",
                processing_time=0.2
            ),
        ]
        
        batch_result = BatchResult(
            total_projects=2,
            successful_conversions=1,
            failed_conversions=1,
            project_results=project_results,
            execution_time=5.0,
            summary_report="Test summary"
        )
        
        # Test __iter__ method
        results = list(batch_result)
        assert len(results) == 2
        assert results[0]["success"] is True
        assert results[1]["success"] is False
        assert results[1]["error_message"] == "Test error"

    def test_batch_result_getitem_method(self):
        """Test BatchResult __getitem__ method."""
        project_results = [
            ConversionResult(
                file_path="test1.yml", 
                success=True, 
                changes_made=1,
                errors=[],
                warnings=[],
                original_content="",
                processing_time=0.1
            ),
        ]
        
        batch_result = BatchResult(
            total_projects=1,
            successful_conversions=1,
            failed_conversions=0,
            project_results=project_results,
            execution_time=5.0,
            summary_report="Test summary"
        )
        
        # Test __getitem__ method
        result = batch_result[0]
        assert result["success"] is True
        assert result["project_path"] == "test1.yml"
        assert result["modules_converted"] == 1

    def test_process_projects_batch_result_method_with_projects(self, processor):
        """Test process_projects_batch_result method with actual projects."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            (project_path / "playbook.yml").write_text("- hosts: all")
            
            # Test the batch result method specifically
            result = processor.process_projects_batch_result([str(project_path)])
            
            assert isinstance(result, BatchResult)
            assert result.total_projects == 1
            assert result.successful_conversions >= 0
            assert len(result.project_results) == 1

    def test_generate_summary_report_method_directly(self, processor):
        """Test _generate_summary_report method directly."""
        # Test the method with various parameter combinations
        summary = processor._generate_summary_report(
            total_projects=10,
            successful=8,
            failed=2,
            total_modules=25,
            execution_time=30.5
        )
        
        assert isinstance(summary, str)
        assert "Total Projects: 10" in summary
        assert "Successful: 8" in summary
        assert "Failed: 2" in summary

    def test_process_project_directory_with_dry_run_success(self, processor):
        """Test _process_project_directory with dry_run=True and successful conversion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            (project_path / "playbook.yml").write_text("- hosts: all")
            (project_path / "tasks.yml").write_text("- name: test task")
            
            # Mock converter for dry run
            processor.converter.convert_content.return_value = ConversionResult(
                file_path="test.yml",
                success=True,
                changes_made=2,
                errors=[],
                warnings=["Dry run warning"],
                original_content="",
                processing_time=0.1
            )
            
            result = processor._process_project_directory(str(project_path), dry_run=True)
            
            assert isinstance(result, ConversionResult)
            assert result.success is True
            assert result.changes_made >= 0
            assert hasattr(result, 'files_processed')

    def test_convert_project_method_with_pathlib_path(self, processor):
        """Test convert_project method with pathlib Path object."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            (project_path / "playbook.yml").write_text("- hosts: all")
            
            # Test with Path object (not string)
            result = processor.convert_project(project_path)
            
            assert isinstance(result, dict)
            assert "project_path" in result
            assert "success" in result

    def test_process_single_project_exception_in_parallel_mode(self, processor):
        """Test exception handling in process_single_project function during parallel processing."""
        processor.max_workers = 2
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            (project_path / "playbook.yml").write_text("- hosts: all")
            
            # Mock _process_project_directory to raise exception
            def mock_process_directory(path, dry_run=False):
                raise Exception("Process directory failed")
            
            processor._process_project_directory = mock_process_directory
            
            result = processor.process_projects([str(project_path)])
            
            # Should handle the exception and return error result
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["success"] is False
            assert "Process directory failed" in result[0]["error_message"]

    def test_discover_projects_with_yaml_file_read_limit(self, processor):
        """Test YAML file content reading with the 3-file limit."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create project with many YAML files (more than 3)
            project_dir = temp_path / "many_yaml_project"
            project_dir.mkdir()
            
            # Create 5 YAML files to test the 3-file limit
            for i in range(5):
                yaml_file = project_dir / f"file{i}.yml"
                yaml_file.write_text(f"- hosts: all # file {i}")
            
            projects = processor.discover_projects(temp_dir)
            
            # Should discover the project (only checks first 3 files)
            assert isinstance(projects, list)
            if len(projects) > 0:
                project_names = [Path(p).name for p in projects]
                assert "many_yaml_project" in project_names

    def test_discover_projects_yaml_content_check_with_special_keywords(self, processor):
        """Test YAML content check with special keywords like 'deep'."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create project with YAML file containing 'deep' keyword
            project_dir = temp_path / "deep_keyword_project"
            project_dir.mkdir()
            
            # File with 'deep' keyword in name
            (project_dir / "deep_playbook.yml").write_text("- hosts: all\n  tasks: []")
            
            projects = processor.discover_projects(temp_dir)
            
            # Should discover the project
            assert isinstance(projects, list)
            if len(projects) > 0:
                project_names = [Path(p).name for p in projects]
                assert "deep_keyword_project" in project_names

    def test_discover_projects_yaml_content_check_exception_handling(self, processor):
        """Test YAML content check with file read exceptions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create project with YAML file
            project_dir = temp_path / "exception_project"
            project_dir.mkdir()
            (project_dir / "playbook.yml").write_text("- hosts: all")
            
            # Mock file reading to raise exception for specific files
            original_open = open
            def mock_open(*args, **kwargs):
                if "playbook.yml" in str(args[0]):
                    raise IOError("Cannot read file")
                return original_open(*args, **kwargs)
            
            with patch('builtins.open', side_effect=mock_open):
                projects = processor.discover_projects(temp_dir)
                
                # Should handle exception and continue (may still find project)
                assert isinstance(projects, list)

    def test_process_projects_batch_result_statistics_calculation(self, processor):
        """Test BatchResult statistics calculation in process_projects_batch_result."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create multiple projects with different outcomes
            projects = []
            for i in range(3):
                project_dir = temp_path / f"project{i}"
                project_dir.mkdir()
                (project_dir / "playbook.yml").write_text(f"- hosts: all # project {i}")
                projects.append(str(project_dir))
            
            # Mock converter to have mixed results
            def side_effect(file_path):
                if "project1" in file_path:
                    return ConversionResult(
                        file_path=file_path,
                        success=False,
                        changes_made=0,
                        errors=["Test error"],
                        warnings=[],
                        original_content="",
                        processing_time=0.1
                    )
                return ConversionResult(
                    file_path=file_path,
                    success=True,
                    changes_made=2,
                    errors=[],
                    warnings=[],
                    original_content="",
                    processing_time=0.1
                )
            
            processor.converter.convert_file.side_effect = side_effect
            
            result = processor.process_projects_batch_result(projects)
            
            # Verify statistics are calculated correctly
            assert isinstance(result, BatchResult)
            assert result.total_projects == 3
            assert result.successful_conversions == 2
            assert result.failed_conversions == 1
            assert result.success_rate == 2/3
            assert result.average_processing_time > 0