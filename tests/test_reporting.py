"""Tests for the enhanced reporting system."""

import pytest
import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from fqcn_converter.reporting.models import (
    ConversionReport, ConversionStatistics, FileChangeRecord, 
    ErrorReport, ConversionStatus, ReportFormat
)
from fqcn_converter.reporting.report_generator import ReportGenerator
from fqcn_converter.reporting.formatters import (
    JSONReportFormatter, MarkdownReportFormatter, 
    HTMLReportFormatter, ConsoleReportFormatter
)


class TestConversionModels:
    """Test cases for conversion report models."""
    
    def test_file_change_record_creation(self):
        """Test FileChangeRecord creation and properties."""
        record = FileChangeRecord(
            file_path=Path("test.yml"),
            status=ConversionStatus.SUCCESS,
            conversions_made=3,
            conversions_attempted=3,
            processing_time=0.5,
            file_size_bytes=1024,
            backup_created=True
        )
        
        assert record.file_path == Path("test.yml")
        assert record.status == ConversionStatus.SUCCESS
        assert record.success_rate == 1.0
        assert not record.has_errors
        assert not record.has_warnings
    
    def test_file_change_record_with_errors(self):
        """Test FileChangeRecord with errors."""
        record = FileChangeRecord(
            file_path=Path("test.yml"),
            status=ConversionStatus.FAILED,
            conversions_made=0,
            conversions_attempted=2,
            processing_time=0.3,
            file_size_bytes=512,
            backup_created=False,
            error_message="Conversion failed",
            warnings=["Warning 1", "Warning 2"]
        )
        
        assert record.success_rate == 0.0
        assert record.has_errors
        assert record.has_warnings
        assert len(record.warnings) == 2
    
    def test_file_change_record_serialization(self):
        """Test FileChangeRecord serialization."""
        record = FileChangeRecord(
            file_path=Path("test.yml"),
            status=ConversionStatus.SUCCESS,
            conversions_made=2,
            conversions_attempted=2,
            processing_time=0.4,
            file_size_bytes=2048,
            backup_created=True
        )
        
        data = record.to_dict()
        
        assert data['file_path'] == 'test.yml'
        assert data['status'] == 'success'
        assert data['conversions_made'] == 2
        assert data['processing_time'] == 0.4
    
    def test_error_report_creation(self):
        """Test ErrorReport creation."""
        error = ErrorReport(
            error_type="ValidationError",
            error_message="Invalid YAML syntax",
            file_path=Path("bad.yml"),
            line_number=5,
            context="Invalid indentation"
        )
        
        assert error.error_type == "ValidationError"
        assert error.file_path == Path("bad.yml")
        assert error.line_number == 5
        assert isinstance(error.timestamp, datetime)
    
    def test_conversion_statistics_initialization(self):
        """Test ConversionStatistics initialization."""
        stats = ConversionStatistics()
        
        assert stats.total_files_processed == 0
        assert stats.success_rate == 0.0
        assert stats.conversion_efficiency == 1.0
        assert stats.processing_speed == 0.0
    
    def test_conversion_statistics_update(self):
        """Test ConversionStatistics update from file record."""
        stats = ConversionStatistics()
        
        record = FileChangeRecord(
            file_path=Path("test.yml"),
            status=ConversionStatus.SUCCESS,
            conversions_made=3,
            conversions_attempted=3,
            processing_time=0.5,
            file_size_bytes=1024,
            backup_created=True
        )
        
        stats.update_from_file_record(record)
        
        assert stats.total_files_processed == 1
        assert stats.total_files_successful == 1
        assert stats.total_conversions_made == 3
        assert stats.success_rate == 1.0
        assert stats.average_processing_time == 0.5
    
    def test_conversion_report_creation(self):
        """Test ConversionReport creation."""
        report = ConversionReport(
            session_id="test-session",
            start_time=datetime.now(),
            target_path=Path("/test/path")
        )
        
        assert report.session_id == "test-session"
        assert report.target_path == Path("/test/path")
        assert not report.is_completed
        assert not report.has_errors
        assert not report.has_warnings
    
    def test_conversion_report_add_records(self):
        """Test adding records to ConversionReport."""
        report = ConversionReport(
            session_id="test-session",
            start_time=datetime.now()
        )
        
        record = FileChangeRecord(
            file_path=Path("test.yml"),
            status=ConversionStatus.SUCCESS,
            conversions_made=2,
            conversions_attempted=2,
            processing_time=0.3,
            file_size_bytes=512,
            backup_created=True
        )
        
        report.add_file_record(record)
        
        assert len(report.file_records) == 1
        assert report.statistics.total_files_processed == 1
        assert report.statistics.total_conversions_made == 2
    
    def test_conversion_report_serialization(self):
        """Test ConversionReport serialization."""
        report = ConversionReport(
            session_id="test-session",
            start_time=datetime.now(),
            target_path=Path("/test/path")
        )
        
        report.finalize()
        
        # Test to_dict
        data = report.to_dict()
        assert data['session_id'] == "test-session"
        assert data['is_completed'] is True
        assert 'duration' in data
        
        # Test to_json
        json_str = report.to_json()
        parsed = json.loads(json_str)
        assert parsed['session_id'] == "test-session"
    
    def test_conversion_report_from_dict(self):
        """Test ConversionReport deserialization."""
        original_report = ConversionReport(
            session_id="test-session",
            start_time=datetime.now(),
            target_path=Path("/test/path")
        )
        original_report.finalize()
        
        # Serialize and deserialize
        data = original_report.to_dict()
        restored_report = ConversionReport.from_dict(data)
        
        assert restored_report.session_id == original_report.session_id
        assert restored_report.target_path == original_report.target_path
        assert restored_report.is_completed == original_report.is_completed


class TestReportFormatters:
    """Test cases for report formatters."""
    
    @pytest.fixture
    def sample_report(self):
        """Create a sample report for testing."""
        report = ConversionReport(
            session_id="test-session",
            start_time=datetime(2023, 1, 1, 12, 0, 0),
            target_path=Path("/test/project")
        )
        
        # Add file records
        record1 = FileChangeRecord(
            file_path=Path("playbook1.yml"),
            status=ConversionStatus.SUCCESS,
            conversions_made=3,
            conversions_attempted=3,
            processing_time=0.5,
            file_size_bytes=1024,
            backup_created=True
        )
        
        record2 = FileChangeRecord(
            file_path=Path("playbook2.yml"),
            status=ConversionStatus.FAILED,
            conversions_made=0,
            conversions_attempted=2,
            processing_time=0.3,
            file_size_bytes=512,
            backup_created=False,
            error_message="Conversion failed"
        )
        
        report.add_file_record(record1)
        report.add_file_record(record2)
        
        # Add error
        error = ErrorReport(
            error_type="ValidationError",
            error_message="Invalid syntax",
            file_path=Path("bad.yml")
        )
        report.add_error(error)
        
        # Add warning
        report.add_warning("This is a warning")
        
        report.finalize()
        return report
    
    def test_json_formatter(self, sample_report):
        """Test JSON formatter."""
        formatter = JSONReportFormatter()
        result = formatter.format_report(sample_report)
        
        # Should be valid JSON
        data = json.loads(result)
        assert data['session_id'] == "test-session"
        assert len(data['file_records']) == 2
        assert len(data['errors']) == 1
        assert len(data['warnings']) == 1
    
    def test_json_formatter_no_metadata(self, sample_report):
        """Test JSON formatter without metadata."""
        formatter = JSONReportFormatter(include_metadata=False)
        result = formatter.format_report(sample_report)
        
        data = json.loads(result)
        assert 'metadata' not in data
    
    def test_markdown_formatter(self, sample_report):
        """Test Markdown formatter."""
        formatter = MarkdownReportFormatter()
        result = formatter.format_report(sample_report)
        
        assert "# FQCN Conversion Report" in result
        assert "test-session" in result
        assert "## Summary" in result
        assert "| Metric | Value |" in result
        assert "## File Details" in result
        assert "## Errors" in result
    
    def test_markdown_formatter_minimal(self, sample_report):
        """Test Markdown formatter with minimal options."""
        formatter = MarkdownReportFormatter(include_details=False, include_errors=False)
        result = formatter.format_report(sample_report)
        
        assert "# FQCN Conversion Report" in result
        assert "## Summary" in result
        assert "## File Details" not in result
        assert "## Errors" not in result
    
    def test_html_formatter(self, sample_report):
        """Test HTML formatter."""
        formatter = HTMLReportFormatter()
        result = formatter.format_report(sample_report)
        
        assert "<!DOCTYPE html>" in result
        assert "<title>FQCN Conversion Report - test-session</title>" in result
        assert "<h1>FQCN Conversion Report</h1>" in result
        assert "test-session" in result
        assert "<table" in result
    
    def test_html_formatter_no_css(self, sample_report):
        """Test HTML formatter without CSS."""
        formatter = HTMLReportFormatter(include_css=False)
        result = formatter.format_report(sample_report)
        
        assert "<!DOCTYPE html>" in result
        assert "<style>" not in result
    
    def test_console_formatter(self, sample_report):
        """Test console formatter."""
        formatter = ConsoleReportFormatter()
        result = formatter.format_report(sample_report)
        
        assert "FQCN Conversion Report" in result
        assert "test-session" in result
        assert "Summary:" in result
        assert "File Details:" in result
        assert "Errors:" in result
    
    def test_console_formatter_no_colors(self, sample_report):
        """Test console formatter without colors."""
        formatter = ConsoleReportFormatter(use_colors=False)
        result = formatter.format_report(sample_report)
        
        assert "FQCN Conversion Report" in result
        assert "\x1b[" not in result  # No ANSI color codes
    
    def test_console_formatter_compact(self, sample_report):
        """Test console formatter in compact mode."""
        formatter = ConsoleReportFormatter(compact=True)
        result = formatter.format_report(sample_report)
        
        assert "FQCN Conversion Report" in result
        assert "File Details:" not in result  # Compact mode excludes details


class TestReportGenerator:
    """Test cases for ReportGenerator."""
    
    @pytest.fixture
    def report_generator(self):
        """Create ReportGenerator for testing."""
        return ReportGenerator("test-session")
    
    def test_initialization(self, report_generator):
        """Test ReportGenerator initialization."""
        assert report_generator.session_id == "test-session"
        assert report_generator.report.session_id == "test-session"
        assert len(report_generator.formatters) == 4
    
    def test_start_session(self, report_generator):
        """Test starting a session."""
        target_path = Path("/test/project")
        config = {"backup": True, "validate": True}
        
        report_generator.start_session(target_path, config)
        
        assert report_generator.report.target_path == target_path
        assert report_generator.report.configuration == config
        assert 'python_version' in report_generator.report.metadata
    
    def test_add_file_result_success(self, report_generator):
        """Test adding successful file result."""
        file_path = Path("test.yml")
        
        # Mock result object
        result = Mock()
        result.success = True
        result.conversions = [{"original": "copy", "fqcn": "ansible.builtin.copy"}]
        result.backup_created = True
        result.warnings = []
        
        with patch.object(file_path, 'stat') as mock_stat, \
             patch.object(file_path, 'exists', return_value=True):
            mock_stat.return_value.st_size = 1024
            
            report_generator.add_file_result(file_path, result, 0.5)
        
        assert len(report_generator.report.file_records) == 1
        record = report_generator.report.file_records[0]
        assert record.status == ConversionStatus.SUCCESS
        assert record.conversions_made == 1
        assert record.processing_time == 0.5
    
    def test_add_file_result_failure(self, report_generator):
        """Test adding failed file result."""
        file_path = Path("test.yml")
        
        # Mock result object
        result = Mock()
        result.success = False
        result.error = "Conversion failed"
        result.attempted_conversions = [{"original": "copy"}]
        
        with patch.object(file_path, 'stat') as mock_stat, \
             patch.object(file_path, 'exists', return_value=True):
            mock_stat.return_value.st_size = 512
            
            report_generator.add_file_result(file_path, result, 0.3)
        
        assert len(report_generator.report.file_records) == 1
        record = report_generator.report.file_records[0]
        assert record.status == ConversionStatus.FAILED
        assert record.conversions_made == 0
        assert record.error_message == "Conversion failed"
    
    def test_add_error(self, report_generator):
        """Test adding error to report."""
        report_generator.add_error(
            error_type="ValidationError",
            error_message="Invalid syntax",
            file_path=Path("bad.yml"),
            line_number=5
        )
        
        assert len(report_generator.report.errors) == 1
        error = report_generator.report.errors[0]
        assert error.error_type == "ValidationError"
        assert error.file_path == Path("bad.yml")
        assert error.line_number == 5
    
    def test_add_warning(self, report_generator):
        """Test adding warning to report."""
        report_generator.add_warning("This is a warning")
        
        assert len(report_generator.report.warnings) == 1
        assert report_generator.report.warnings[0] == "This is a warning"
    
    def test_finalize_session(self, report_generator):
        """Test finalizing session."""
        report = report_generator.finalize_session()
        
        assert report.is_completed
        assert report.end_time is not None
        assert 'final_memory_mb' in report.metadata
    
    def test_generate_report_json(self, report_generator):
        """Test generating JSON report."""
        report_generator.finalize_session()
        
        result = report_generator.generate_report(ReportFormat.JSON)
        
        # Should be valid JSON
        data = json.loads(result)
        assert data['session_id'] == "test-session"
    
    def test_generate_report_with_file(self, report_generator):
        """Test generating report and saving to file."""
        report_generator.finalize_session()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            result = report_generator.generate_report(ReportFormat.JSON, output_path)
            
            assert output_path.exists()
            
            # Verify file content
            saved_data = json.loads(output_path.read_text())
            assert saved_data['session_id'] == "test-session"
            
        finally:
            if output_path.exists():
                output_path.unlink()
    
    def test_generate_all_formats(self, report_generator):
        """Test generating all report formats."""
        report_generator.finalize_session()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            generated_files = report_generator.generate_all_formats(output_dir)
            
            assert len(generated_files) == 4
            assert ReportFormat.JSON in generated_files
            assert ReportFormat.HTML in generated_files
            assert ReportFormat.MARKDOWN in generated_files
            assert ReportFormat.CONSOLE in generated_files
            
            # Verify files exist
            for file_path in generated_files.values():
                assert file_path.exists()
                assert file_path.stat().st_size > 0
    
    def test_get_summary_stats(self, report_generator):
        """Test getting summary statistics."""
        # Add some data
        file_path = Path("test.yml")
        result = Mock()
        result.success = True
        result.conversions = [{"original": "copy", "fqcn": "ansible.builtin.copy"}]
        result.backup_created = True
        result.warnings = []
        
        with patch.object(file_path, 'stat') as mock_stat, \
             patch.object(file_path, 'exists', return_value=True):
            mock_stat.return_value.st_size = 1024
            report_generator.add_file_result(file_path, result, 0.5)
        
        report_generator.finalize_session()
        
        stats = report_generator.get_summary_stats()
        
        assert stats['session_id'] == "test-session"
        assert stats['files_processed'] == 1
        assert stats['files_successful'] == 1
        assert stats['success_rate'] == 1.0
        assert stats['conversions_made'] == 1
        assert stats['is_completed'] is True
    
    def test_export_raw_data(self, report_generator):
        """Test exporting raw report data."""
        report_generator.finalize_session()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            report_generator.export_raw_data(output_path)
            
            assert output_path.exists()
            
            # Verify content
            data = json.loads(output_path.read_text())
            assert data['session_id'] == "test-session"
            assert 'statistics' in data
            
        finally:
            if output_path.exists():
                output_path.unlink()
    
    def test_load_report(self, report_generator):
        """Test loading report from file."""
        report_generator.finalize_session()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            # Export data
            report_generator.export_raw_data(output_path)
            
            # Load report
            loaded_report = ReportGenerator.load_report(output_path)
            
            assert loaded_report.session_id == "test-session"
            assert loaded_report.is_completed
            
        finally:
            if output_path.exists():
                output_path.unlink()
    
    def test_create_comparison_report(self):
        """Test creating comparison report."""
        # Create multiple reports
        reports = []
        
        for i in range(3):
            report = ConversionReport(
                session_id=f"session-{i}",
                start_time=datetime(2023, 1, i+1, 12, 0, 0)
            )
            report.statistics.total_files_processed = i + 1
            report.statistics.total_conversions_made = (i + 1) * 2
            report.statistics.total_processing_time = (i + 1) * 0.5
            report.finalize()
            reports.append(report)
        
        comparison = ReportGenerator.create_comparison_report(reports)
        
        assert comparison['report_count'] == 3
        assert 'date_range' in comparison
        assert 'aggregate_stats' in comparison
        assert comparison['aggregate_stats']['total_files_processed'] == 6  # 1+2+3
        assert comparison['aggregate_stats']['total_conversions_made'] == 12  # 2+4+6
        assert len(comparison['individual_reports']) == 3