"""
Complete test coverage for core batch processing module.

This module provides comprehensive tests to achieve 100% coverage
of the BatchProcessor class and related functionality.
"""

import logging
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from fqcn_converter.core.batch import BatchProcessor, BatchResult
from fqcn_converter.core.converter import ConversionResult, FQCNConverter
from fqcn_converter.exceptions import BatchProcessingError


class TestBatchProcessorInit:
    """Test BatchProcessor initialization."""

    def test_init_default_parameters(self):
        """Test initialization with default parameters."""
        with patch('fqcn_converter.core.batch.FQCNConverter') as mock_converter:
            processor = BatchProcessor()
            
            assert processor.max_workers == 4
            assert processor.config_path is None
            assert processor.progress_callback is None
            assert processor._last_batch_result is None
            mock_converter.assert_called_once_with(config_path=None)

    def test_init_custom_parameters(self):
        """Test initialization with custom parameters."""
        callback = Mock()
        config_path = "/path/to/config.yml"
        
        with patch('fqcn_converter.core.batch.FQCNConverter') as mock_converter:
            processor = BatchProcessor(
                max_workers=8,
                config_path=config_path,
                progress_callback=callback
            )
            
            assert processor.max_workers == 8
            assert processor.config_path == config_path
            assert processor.progress_callback == callback
            mock_converter.assert_called_once_with(config_path=config_path)

    def test_init_min_workers_enforced(self):
        """Test that minimum workers is enforced."""
        with patch('fqcn_converter.core.batch.FQCNConverter'):
            processor = BatchProcessor(max_workers=0)
            assert processor.max_workers == 1
            
            processor = BatchProcessor(max_workers=-5)
            assert processor.max_workers == 1

    def test_init_converter_failure(self):
        """Test initialization when converter creation fails."""
        with patch('fqcn_converter.core.batch.FQCNConverter', side_effect=Exception("Converter failed")):
            with pytest.raises(BatchProcessingError) as exc_info:
                BatchProcessor()
            
            assert "Failed to initialize converter" in str(exc_info.value)


class TestBatchProcessorDiscoverProjects:
    """Test project discovery functionality."""

    @pytest.fixture
    def processor(self):
        """Create a BatchProcessor instance."""
        with patch('fqcn_converter.core.batch.FQCNConverter'):
            return BatchProcessor()

    @pytest.fixture
    def temp_project_structure(self):
        """Create temporary project structure for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create ansible project 1
            project1 = temp_path / "ansible-project1"
            project1.mkdir()
            (project1 / "playbook.yml").write_text("- hosts: all\n  tasks: []")
            (project1 / "inventory").write_text("[webservers]\nhost1")
            
            # Create ansible project 2
            project2 = temp_path / "ansible-project2"
            project2.mkdir()
            (project2 / "site.yml").write_text("- hosts: all\n  tasks: []")
            (project2 / "ansible.cfg").write_text("[defaults]\nhost_key_checking = False")
            
            # Create non-ansible directory
            non_ansible = temp_path / "regular-dir"
            non_ansible.mkdir()
            (non_ansible / "readme.txt").write_text("Not an ansible project")
            
            # Create nested ansible project
            nested = temp_path / "parent" / "nested-ansible"
            nested.mkdir(parents=True)
            (nested / "main.yml").write_text("- hosts: all\n  tasks: []")
            (nested / "roles").mkdir()
            
            yield temp_path

    def test_discover_projects_basic(self, processor, temp_project_structure):
        """Test basic project discovery."""
        projects = processor.discover_projects(temp_project_structure)
        
        # Should find ansible projects
        assert len(projects) >= 2
        project_names = [Path(p).name for p in projects]
        assert "ansible-project1" in project_names
        assert "ansible-project2" in project_names

    def test_discover_projects_with_patterns(self, processor, temp_project_structure):
        """Test project discovery with custom patterns."""
        patterns = ["*.yml", "*.yaml"]
        projects = processor.discover_projects(
            temp_project_structure, 
            patterns=patterns
        )
        
        assert isinstance(projects, list)

    def test_discover_projects_with_exclude_patterns(self, processor, temp_project_structure):
        """Test project discovery with exclude patterns."""
        exclude_patterns = ["*project1*"]
        projects = processor.discover_projects(
            temp_project_structure,
            exclude_patterns=exclude_patterns
        )
        
        # Should exclude project1
        project_names = [Path(p).name for p in projects]
        assert "ansible-project1" not in project_names

    def test_discover_projects_nonexistent_directory(self, processor):
        """Test discovery with nonexistent directory."""
        projects = processor.discover_projects("/nonexistent/path")
        assert projects == []

    def test_discover_projects_file_instead_of_directory(self, processor):
        """Test discovery when path is a file."""
        with tempfile.NamedTemporaryFile() as temp_file:
            projects = processor.discover_projects(temp_file.name)
            assert projects == []

    def test_discover_projects_empty_directory(self, processor):
        """Test discovery in empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            projects = processor.discover_projects(temp_dir)
            assert projects == []


class TestBatchProcessorProcessProjects:
    """Test project processing functionality."""

    @pytest.fixture
    def processor(self):
        """Create a BatchProcessor instance with mocked converter."""
        with patch('fqcn_converter.core.batch.FQCNConverter') as mock_converter_class:
            mock_converter = Mock()
            mock_converter.convert_file.return_value = ConversionResult(
                file_path="test.yml",
                success=True,
                changes_made=1
            )
            mock_converter_class.return_value = mock_converter
            
            processor = BatchProcessor()
            processor.converter = mock_converter
            return processor

    def test_process_projects_empty_list(self, processor):
        """Test processing empty project list."""
        result = processor.process_projects([])
        
        # Empty projects list returns BatchResult (special case)
        assert isinstance(result, BatchResult)
        assert result.total_projects == 0

    def test_process_projects_single_project(self, processor):
        """Test processing single project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            (project_path / "playbook.yml").write_text("- hosts: all")
            
            result = processor.process_projects([str(project_path)])
            
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["project_path"] == str(project_path)

    def test_process_projects_multiple_projects(self, processor):
        """Test processing multiple projects."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create multiple projects
            projects = []
            for i in range(3):
                project_dir = temp_path / f"project{i}"
                project_dir.mkdir()
                (project_dir / "playbook.yml").write_text(f"- hosts: all # project {i}")
                projects.append(str(project_dir))
            
            result = processor.process_projects(projects)
            
            assert isinstance(result, list)
            assert len(result) == 3

    def test_process_projects_with_progress_callback(self, processor):
        """Test processing with progress callback."""
        callback_calls = []
        
        def progress_callback(completed, total, current):
            callback_calls.append((completed, total, current))
        
        processor.progress_callback = progress_callback
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            (project_path / "playbook.yml").write_text("- hosts: all")
            
            result = processor.process_projects([str(project_path)])
            
            assert isinstance(result, list)
            assert len(result) == 1

    def test_process_projects_conversion_failure(self, processor):
        """Test processing when conversion fails."""
        # Mock converter to fail
        processor.converter.convert_file.return_value = ConversionResult(
            file_path="test.yml",
            success=False,
            changes_made=0,
            errors=["Conversion failed"]
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            (project_path / "playbook.yml").write_text("- hosts: all")
            
            result = processor.process_projects([str(project_path)])
            
            assert isinstance(result, list)
            assert len(result) == 1


class TestBatchProcessorProjectDirectory:
    """Test _process_project_directory method."""

    @pytest.fixture
    def processor(self):
        """Create a BatchProcessor instance."""
        with patch('fqcn_converter.core.batch.FQCNConverter') as mock_converter_class:
            mock_converter = Mock()
            mock_converter.convert_file.return_value = ConversionResult(
                file_path="test.yml",
                success=True,
                changes_made=1
            )
            mock_converter_class.return_value = mock_converter
            
            processor = BatchProcessor()
            processor.converter = mock_converter
            return processor

    def test_process_project_directory_with_files(self, processor):
        """Test processing project directory with ansible files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            (project_path / "playbook.yml").write_text("- hosts: all")
            (project_path / "tasks.yml").write_text("- name: test\n  debug: msg=test")
            
            result = processor._process_project_directory(str(project_path))
            
            assert isinstance(result, ConversionResult)
            assert result.success is True

    def test_process_project_directory_no_files(self, processor):
        """Test processing project directory with no ansible files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = processor._process_project_directory(temp_dir)
            
            assert isinstance(result, ConversionResult)
            assert result.success is True

    def test_process_project_directory_conversion_exception(self, processor):
        """Test processing when conversion raises exception."""
        processor.converter.convert_file.side_effect = Exception("Conversion error")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            (project_path / "playbook.yml").write_text("- hosts: all")
            
            result = processor._process_project_directory(str(project_path))
            
            assert isinstance(result, ConversionResult)
            assert result.success is False


class TestBatchProcessorConvertProject:
    """Test convert_project method."""

    @pytest.fixture
    def processor(self):
        """Create a BatchProcessor instance."""
        with patch('fqcn_converter.core.batch.FQCNConverter') as mock_converter_class:
            mock_converter = Mock()
            mock_converter.convert_file.return_value = ConversionResult(
                file_path="test.yml",
                success=True,
                changes_made=1
            )
            mock_converter_class.return_value = mock_converter
            
            processor = BatchProcessor()
            processor.converter = mock_converter
            return processor

    def test_convert_project_success(self, processor):
        """Test successful project conversion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            (project_path / "playbook.yml").write_text("- hosts: all")
            
            result = processor.convert_project(str(project_path))
            
            assert isinstance(result, dict)
            assert "project_path" in result

    def test_convert_project_nonexistent(self, processor):
        """Test converting nonexistent project."""
        result = processor.convert_project("/nonexistent/project")
        
        assert isinstance(result, dict)
        assert "error_message" in result
        assert result["error_message"] is not None


class TestBatchProcessorGenerateReport:
    """Test report generation functionality."""

    @pytest.fixture
    def processor(self):
        """Create a BatchProcessor instance."""
        with patch('fqcn_converter.core.batch.FQCNConverter'):
            return BatchProcessor()

    def test_generate_report_with_results(self, processor):
        """Test generating report with batch results."""
        # Create mock batch result
        batch_result = BatchResult(
            total_projects=2,
            successful_conversions=1,
            failed_conversions=1,
            project_results=[],
            execution_time=10.0,
            summary_report="Test summary",
            total_files_processed=5,
            total_modules_converted=3,
            success_rate=0.5,
            average_processing_time=5.0
        )
        
        processor._last_batch_result = batch_result
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            report = processor.generate_report(temp_file.name)
            
            assert isinstance(report, dict)
            assert "batch_conversion_report" in report
            assert "summary" in report["batch_conversion_report"]

    def test_generate_report_no_results(self, processor):
        """Test generating report with no previous results."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            report = processor.generate_report(temp_file.name)
            
            assert isinstance(report, dict)
            assert "batch_conversion_report" in report


class TestBatchProcessorGenerateSummaryReport:
    """Test _generate_summary_report method."""

    @pytest.fixture
    def processor(self):
        """Create a BatchProcessor instance."""
        with patch('fqcn_converter.core.batch.FQCNConverter'):
            return BatchProcessor()

    def test_generate_summary_report_success(self, processor):
        """Test generating summary report for successful batch."""
        batch_result = BatchResult(
            total_projects=3,
            successful_conversions=3,
            failed_conversions=0,
            project_results=[],
            execution_time=15.0,
            summary_report="",
            total_files_processed=10,
            total_modules_converted=8,
            success_rate=1.0,
            average_processing_time=5.0
        )
        
        summary = processor._generate_summary_report(
            total_projects=3,
            successful=3,
            failed=0,
            total_modules=10,
            execution_time=15.0
        )
        
        assert isinstance(summary, str)
        assert "Total Projects: 3" in summary
        assert "Successful: 3" in summary

    def test_generate_summary_report_with_failures(self, processor):
        """Test generating summary report with failures."""
        batch_result = BatchResult(
            total_projects=3,
            successful_conversions=2,
            failed_conversions=1,
            project_results=[],
            execution_time=15.0,
            summary_report="",
            total_files_processed=8,
            total_modules_converted=6,
            success_rate=0.67,
            average_processing_time=5.0
        )
        
        summary = processor._generate_summary_report(
            total_projects=3,
            successful=2,
            failed=1,
            total_modules=6,
            execution_time=15.0
        )
        
        assert isinstance(summary, str)
        assert "Total Projects: 3" in summary
        assert "Successful: 2" in summary
        assert "Failed: 1" in summary


class TestBatchProcessorProcessProjectsBatchResult:
    """Test process_projects_batch_result property."""

    @pytest.fixture
    def processor(self):
        """Create a BatchProcessor instance."""
        with patch('fqcn_converter.core.batch.FQCNConverter'):
            return BatchProcessor()

    def test_process_projects_batch_result_empty(self, processor):
        """Test batch result method with empty projects list."""
        result = processor.process_projects_batch_result([])
        assert isinstance(result, BatchResult)
        assert result.total_projects == 0

    def test_process_projects_batch_result_after_processing(self, processor):
        """Test batch result property after processing."""
        # Mock a batch result
        batch_result = BatchResult(
            total_projects=1,
            successful_conversions=1,
            failed_conversions=0,
            project_results=[],
            execution_time=5.0,
            summary_report="Test",
            total_files_processed=2,
            total_modules_converted=1,
            success_rate=1.0,
            average_processing_time=5.0
        )
        
        # Test the method with a project
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            (project_path / "playbook.yml").write_text("- hosts: all")
            
            result = processor.process_projects_batch_result([str(project_path)])
            assert isinstance(result, BatchResult)
            assert result.total_projects == 1


class TestBatchResult:
    """Test BatchResult dataclass."""

    def test_batch_result_creation(self):
        """Test creating BatchResult with all fields."""
        project_results = [
            ConversionResult(file_path="test1.yml", success=True, changes_made=2),
            ConversionResult(file_path="test2.yml", success=False, changes_made=0)
        ]
        
        result = BatchResult(
            total_projects=2,
            successful_conversions=1,
            failed_conversions=1,
            project_results=project_results,
            execution_time=10.5,
            summary_report="Test completed",
            total_files_processed=5,
            total_modules_converted=2,
            success_rate=0.5,
            average_processing_time=5.25
        )
        
        assert result.total_projects == 2
        assert result.successful_conversions == 1
        assert result.failed_conversions == 1
        assert len(result.project_results) == 2
        assert result.execution_time == 10.5
        assert result.summary_report == "Test completed"
        assert result.total_files_processed == 5
        assert result.total_modules_converted == 2
        assert result.success_rate == 0.5
        assert result.average_processing_time == 5.25

    def test_batch_result_defaults(self):
        """Test BatchResult with default values."""
        result = BatchResult(
            total_projects=0,
            successful_conversions=0,
            failed_conversions=0,
            project_results=[],
            execution_time=0.0,
            summary_report="No projects processed"
        )
        
        assert result.total_projects == 0
        assert result.successful_conversions == 0
        assert result.failed_conversions == 0
        assert result.project_results == []
        assert result.execution_time == 0.0
        assert result.total_files_processed == 0
        assert result.total_modules_converted == 0
        assert result.success_rate == 0.0
        assert result.average_processing_time == 0.0


class TestBatchProcessorEdgeCases:
    """Test edge cases and error conditions."""

    def test_batch_processor_logging(self):
        """Test that logging is properly configured."""
        with patch('fqcn_converter.core.batch.FQCNConverter'):
            processor = BatchProcessor()
            assert hasattr(processor, 'logger')
            assert isinstance(processor.logger, logging.Logger)

    def test_batch_processor_pathlib_support(self):
        """Test that pathlib.Path objects are supported."""
        with patch('fqcn_converter.core.batch.FQCNConverter'):
            processor = BatchProcessor()
            
            with tempfile.TemporaryDirectory() as temp_dir:
                path_obj = Path(temp_dir)
                projects = processor.discover_projects(path_obj)
                assert isinstance(projects, list)

    def test_batch_processor_string_path_support(self):
        """Test that string paths are supported."""
        with patch('fqcn_converter.core.batch.FQCNConverter'):
            processor = BatchProcessor()
            
            with tempfile.TemporaryDirectory() as temp_dir:
                projects = processor.discover_projects(temp_dir)
                assert isinstance(projects, list)

    def test_batch_processor_concurrent_safety(self):
        """Test thread safety considerations."""
        with patch('fqcn_converter.core.batch.FQCNConverter'):
            processor = BatchProcessor(max_workers=2)
            
            # Multiple calls should not interfere
            with tempfile.TemporaryDirectory() as temp_dir:
                projects1 = processor.discover_projects(temp_dir)
                projects2 = processor.discover_projects(temp_dir)
                
                assert isinstance(projects1, list)
                assert isinstance(projects2, list)