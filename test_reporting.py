#!/usr/bin/env python3
"""Test script for reporting system."""

import sys
import tempfile
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

def test_reporting_imports():
    """Test that reporting modules can be imported."""
    print("Testing reporting system imports...")
    
    try:
        from fqcn_converter.reporting.models import ConversionReport, ConversionStatistics, FileChangeRecord, ConversionStatus
        print("✓ Reporting models imported successfully")
    except Exception as e:
        print(f"✗ Reporting models import failed: {e}")
        return False
    
    try:
        from fqcn_converter.reporting.formatters import JSONReportFormatter, ConsoleReportFormatter
        print("✓ Report formatters imported successfully")
    except Exception as e:
        print(f"✗ Report formatters import failed: {e}")
        return False
    
    try:
        from fqcn_converter.reporting.report_generator import ReportGenerator
        print("✓ Report generator imported successfully")
    except Exception as e:
        print(f"✗ Report generator import failed: {e}")
        return False
    
    return True

def test_report_models():
    """Test report model creation and functionality."""
    print("\nTesting report models...")
    
    try:
        from fqcn_converter.reporting.models import ConversionReport, ConversionStatistics, FileChangeRecord, ConversionStatus
        
        # Test FileChangeRecord
        record = FileChangeRecord(
            file_path=Path("test.yml"),
            status=ConversionStatus.SUCCESS,
            conversions_made=3,
            conversions_attempted=3,
            processing_time=0.5,
            file_size_bytes=1024,
            backup_created=True
        )
        
        assert record.success_rate == 1.0
        assert not record.has_errors
        assert not record.has_warnings
        print("✓ FileChangeRecord created and tested successfully")
        
        # Test ConversionStatistics
        stats = ConversionStatistics()
        stats.update_from_file_record(record)
        
        assert stats.total_files_processed == 1
        assert stats.total_files_successful == 1
        assert stats.success_rate == 1.0
        print("✓ ConversionStatistics created and updated successfully")
        
        # Test ConversionReport
        report = ConversionReport(
            session_id="test-session",
            start_time=datetime.now(),
            target_path=Path("/test/path")
        )
        
        report.add_file_record(record)
        report.finalize()
        
        assert len(report.file_records) == 1
        assert report.is_completed
        assert report.duration is not None
        print("✓ ConversionReport created and tested successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Report models test failed: {e}")
        return False

def test_report_formatters():
    """Test report formatters."""
    print("\nTesting report formatters...")
    
    try:
        from fqcn_converter.reporting.models import ConversionReport, FileChangeRecord, ConversionStatus
        from fqcn_converter.reporting.formatters import JSONReportFormatter, ConsoleReportFormatter
        
        # Create sample report
        report = ConversionReport(
            session_id="test-session",
            start_time=datetime.now(),
            target_path=Path("/test/project")
        )
        
        record = FileChangeRecord(
            file_path=Path("playbook.yml"),
            status=ConversionStatus.SUCCESS,
            conversions_made=2,
            conversions_attempted=2,
            processing_time=0.3,
            file_size_bytes=512,
            backup_created=True
        )
        
        report.add_file_record(record)
        report.finalize()
        
        # Test JSON formatter
        json_formatter = JSONReportFormatter()
        json_output = json_formatter.format_report(report)
        
        assert "test-session" in json_output
        assert "playbook.yml" in json_output
        print("✓ JSON formatter works correctly")
        
        # Test Console formatter
        console_formatter = ConsoleReportFormatter()
        console_output = console_formatter.format_report(report)
        
        assert "FQCN Conversion Report" in console_output
        assert "test-session" in console_output
        print("✓ Console formatter works correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Report formatters test failed: {e}")
        return False

def test_report_generator():
    """Test report generator."""
    print("\nTesting report generator...")
    
    try:
        from fqcn_converter.reporting.report_generator import ReportGenerator
        
        # Create report generator
        generator = ReportGenerator("test-session")
        
        # Start session
        generator.start_session(Path("/test/project"))
        
        # Add mock file result
        class MockResult:
            success = True
            conversions = [{"original": "copy", "fqcn": "ansible.builtin.copy"}]
            backup_created = True
            warnings = []
        
        generator.add_file_result(Path("test.yml"), MockResult(), 0.5)
        
        # Finalize session
        report = generator.finalize_session()
        
        assert report.session_id == "test-session"
        assert len(report.file_records) == 1
        assert report.is_completed
        print("✓ Report generator works correctly")
        
        # Test report generation
        json_report = generator.generate_report('json')
        assert "test-session" in json_report
        print("✓ JSON report generation works")
        
        console_report = generator.generate_report('console')
        assert "FQCN Conversion Report" in console_report
        print("✓ Console report generation works")
        
        # Test summary stats
        stats = generator.get_summary_stats()
        assert stats['session_id'] == "test-session"
        assert stats['files_processed'] == 1
        print("✓ Summary statistics work correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Report generator test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("FQCN Converter Reporting System Test")
    print("=" * 60)
    
    tests = [
        test_reporting_imports,
        test_report_models,
        test_report_formatters,
        test_report_generator
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All reporting system tests passed!")
        return True
    else:
        print("⚠ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)