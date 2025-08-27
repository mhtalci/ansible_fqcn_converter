# Coverage Improvement Strategies

## Overview

This document provides comprehensive strategies for improving test coverage in the FQCN Converter project, including systematic approaches to identify coverage gaps, implement targeted tests, and maintain high coverage standards.

## Current Coverage Analysis

### Coverage Status by Module

| Module | Current Coverage | Target Coverage | Priority | Status |
|--------|------------------|-----------------|----------|---------|
| `core/converter.py` | 95% | 95% | ✅ | Met |
| `core/validator.py` | 92% | 92% | ✅ | Met |
| `core/batch.py` | 76% | 90% | 🔴 | Critical |
| `cli/batch.py` | 0% | 90% | 🔴 | Critical |
| `utils/logging.py` | 70% | 90% | 🔴 | High |
| `cli/convert.py` | 85% | 90% | 🟡 | Medium |
| `cli/validate.py` | 88% | 90% | 🟡 | Low |
| `config/manager.py` | 94% | 95% | 🟡 | Low |

### Coverage Gap Analysis

#### Critical Gaps (< 80% coverage)
1. **`cli/batch.py`** - 0% coverage (322 lines uncovered)
   - No existing tests for CLI batch functionality
   - Command-line argument parsing untested
   - Batch execution workflow untested

2. **`core/batch.py`** - 76% coverage (69 lines uncovered)
   - Error handling paths not covered
   - Edge cases in batch processing
   - Parallel processing scenarios

3. **`utils/logging.py`** - 70% coverage (46 lines uncovered)
   - Logger configuration scenarios
   - Different log levels and formatters
   - Error handling in logging setup

## Systematic Coverage Improvement Process

### Phase 1: Coverage Assessment and Planning

#### 1.1 Generate Detailed Coverage Reports
```bash
# Generate comprehensive coverage report
pytest --cov=src/fqcn_converter --cov-report=html --cov-report=xml --cov-branch

# Analyze specific modules
pytest tests/unit/test_batch.py --cov=src/fqcn_converter/core/batch.py --cov-report=term-missing

# Generate coverage data for analysis
pytest --cov=src/fqcn_converter --cov-report=json:coverage.json
```

#### 1.2 Identify Coverage Gaps
```python
# scripts/analyze_coverage_gaps.py
import json
import sys
from pathlib import Path

def analyze_coverage_gaps(coverage_file):
    """Analyze coverage gaps and prioritize improvements"""
    with open(coverage_file) as f:
        coverage_data = json.load(f)
    
    gaps = []
    for filename, file_data in coverage_data['files'].items():
        if 'src/fqcn_converter' in filename:
            missing_lines = file_data.get('missing_lines', [])
            excluded_lines = file_data.get('excluded_lines', [])
            
            if missing_lines:
                gaps.append({
                    'file': filename,
                    'missing_lines': missing_lines,
                    'coverage_percent': file_data['summary']['percent_covered'],
                    'priority': calculate_priority(file_data)
                })
    
    return sorted(gaps, key=lambda x: x['priority'], reverse=True)

def calculate_priority(file_data):
    """Calculate priority based on coverage percentage and file importance"""
    coverage_percent = file_data['summary']['percent_covered']
    num_statements = file_data['summary']['num_statements']
    
    # Higher priority for lower coverage and more statements
    priority = (100 - coverage_percent) * (num_statements / 100)
    return priority

if __name__ == "__main__":
    gaps = analyze_coverage_gaps('coverage.json')
    for gap in gaps[:10]:  # Top 10 priority gaps
        print(f"File: {gap['file']}")
        print(f"Coverage: {gap['coverage_percent']:.1f}%")
        print(f"Missing lines: {gap['missing_lines']}")
        print(f"Priority: {gap['priority']:.2f}")
        print("-" * 50)
```

#### 1.3 Create Coverage Improvement Plan
```python
# scripts/create_coverage_plan.py
def create_improvement_plan(gaps):
    """Create structured improvement plan"""
    plan = {
        'critical': [],  # < 80% coverage
        'high': [],      # 80-85% coverage
        'medium': [],    # 85-90% coverage
        'low': []        # 90-95% coverage
    }
    
    for gap in gaps:
        coverage = gap['coverage_percent']
        if coverage < 80:
            plan['critical'].append(gap)
        elif coverage < 85:
            plan['high'].append(gap)
        elif coverage < 90:
            plan['medium'].append(gap)
        else:
            plan['low'].append(gap)
    
    return plan
```

### Phase 2: Targeted Test Implementation

#### 2.1 Error Handling Path Coverage

**Strategy**: Systematically test all error conditions and exception paths.

```python
# Example: Comprehensive error handling tests for batch.py
class TestBatchProcessorErrorHandling:
    """Test error handling scenarios in batch processing"""
    
    def test_file_not_found_error(self, batch_processor):
        """Test handling of missing input files"""
        with pytest.raises(FileNotFoundError) as exc_info:
            batch_processor.process_file("/nonexistent/file.yml")
        
        assert "file.yml" in str(exc_info.value)
    
    def test_permission_error_handling(self, batch_processor, tmp_path):
        """Test handling of permission errors"""
        # Create file with restricted permissions
        restricted_file = tmp_path / "restricted.yml"
        restricted_file.write_text("test: content")
        restricted_file.chmod(0o000)  # No permissions
        
        try:
            with pytest.raises(PermissionError):
                batch_processor.process_file(str(restricted_file))
        finally:
            restricted_file.chmod(0o644)  # Restore permissions for cleanup
    
    def test_yaml_parsing_error_handling(self, batch_processor, tmp_path):
        """Test handling of invalid YAML content"""
        invalid_yaml = tmp_path / "invalid.yml"
        invalid_yaml.write_text("invalid: yaml: content: [")
        
        with pytest.raises(YAMLParsingError):
            batch_processor.process_file(str(invalid_yaml))
    
    def test_disk_space_error_handling(self, batch_processor, tmp_path, monkeypatch):
        """Test handling of disk space errors"""
        def mock_write_error(*args, **kwargs):
            raise OSError("No space left on device")
        
        monkeypatch.setattr("builtins.open", mock_write_error)
        
        with pytest.raises(OSError) as exc_info:
            batch_processor.process_file("test.yml")
        
        assert "No space left on device" in str(exc_info.value)
```

#### 2.2 Edge Case Coverage

**Strategy**: Test boundary conditions, empty inputs, and unusual scenarios.

```python
class TestBatchProcessorEdgeCases:
    """Test edge cases and boundary conditions"""
    
    @pytest.mark.parametrize("file_content,expected_result", [
        ("", "empty_file_handling"),
        ("   \n\t  ", "whitespace_only_handling"),
        ("# Only comments\n# More comments", "comments_only_handling"),
        ("---\n", "yaml_separator_only"),
    ])
    def test_edge_case_file_contents(self, batch_processor, tmp_path, file_content, expected_result):
        """Test processing of edge case file contents"""
        edge_case_file = tmp_path / "edge_case.yml"
        edge_case_file.write_text(file_content)
        
        result = batch_processor.process_file(str(edge_case_file))
        # Verify appropriate handling based on expected_result
        assert result is not None
    
    def test_very_large_file_processing(self, batch_processor, tmp_path):
        """Test processing of very large files"""
        large_file = tmp_path / "large.yml"
        
        # Generate large YAML content
        large_content = []
        for i in range(10000):
            large_content.append(f"key_{i}: value_{i}")
        
        large_file.write_text("\n".join(large_content))
        
        result = batch_processor.process_file(str(large_file))
        assert result is not None
    
    def test_deeply_nested_yaml_structure(self, batch_processor, tmp_path):
        """Test processing of deeply nested YAML structures"""
        nested_content = "level0:\n"
        for i in range(1, 50):  # 50 levels deep
            nested_content += "  " * i + f"level{i}:\n"
        nested_content += "  " * 50 + "value: deep_value"
        
        nested_file = tmp_path / "nested.yml"
        nested_file.write_text(nested_content)
        
        result = batch_processor.process_file(str(nested_file))
        assert result is not None
    
    def test_unicode_and_special_characters(self, batch_processor, tmp_path):
        """Test processing files with unicode and special characters"""
        unicode_content = """
        unicode_test: "Hello 世界 🌍"
        special_chars: "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        emoji: "🚀 🎉 ✅ ❌"
        """
        
        unicode_file = tmp_path / "unicode.yml"
        unicode_file.write_text(unicode_content, encoding='utf-8')
        
        result = batch_processor.process_file(str(unicode_file))
        assert result is not None
```

#### 2.3 Branch Coverage Improvement

**Strategy**: Ensure all conditional branches are tested.

```python
def test_all_conditional_branches():
    """Test all conditional branches in the code"""
    
    # Test if-else branches
    def test_condition_true_branch():
        # Setup condition to be True
        result = function_with_condition(condition=True)
        assert result == expected_true_result
    
    def test_condition_false_branch():
        # Setup condition to be False
        result = function_with_condition(condition=False)
        assert result == expected_false_result
    
    # Test try-except branches
    def test_try_success_branch():
        # Setup for successful execution
        result = function_with_try_except(valid_input)
        assert result == expected_success_result
    
    def test_except_branch():
        # Setup for exception
        with pytest.raises(ExpectedException):
            function_with_try_except(invalid_input)
    
    # Test loop branches
    def test_loop_empty_iteration():
        # Test loop with empty collection
        result = function_with_loop([])
        assert result == expected_empty_result
    
    def test_loop_single_iteration():
        # Test loop with single item
        result = function_with_loop([single_item])
        assert result == expected_single_result
    
    def test_loop_multiple_iterations():
        # Test loop with multiple items
        result = function_with_loop([item1, item2, item3])
        assert result == expected_multiple_result
```

### Phase 3: CLI Coverage Implementation

#### 3.1 CLI Batch Module Coverage (`cli/batch.py`)

**Current Status**: 0% coverage (322 lines uncovered)

**Implementation Strategy**:

```python
# tests/unit/test_cli_batch_comprehensive.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
from fqcn_converter.cli.batch import batch_command, BatchCLI

class TestBatchCLIExecution:
    """Test CLI batch command execution flow"""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_batch_command_basic_execution(self):
        """Test basic batch command execution"""
        with self.runner.isolated_filesystem():
            # Create test files
            with open('input.yml', 'w') as f:
                f.write('test: content')
            
            result = self.runner.invoke(batch_command, [
                '--input-dir', '.',
                '--output-dir', 'output',
                '--pattern', '*.yml'
            ])
            
            assert result.exit_code == 0
    
    def test_batch_command_with_all_options(self):
        """Test batch command with all CLI options"""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(batch_command, [
                '--input-dir', 'input',
                '--output-dir', 'output',
                '--pattern', '*.yml',
                '--recursive',
                '--backup',
                '--dry-run',
                '--parallel',
                '--workers', '4',
                '--verbose'
            ])
            
            # Should handle missing input directory gracefully
            assert result.exit_code != 0  # Expected to fail with missing input
            assert 'input directory' in result.output.lower()
    
    @pytest.mark.parametrize("option,value,expected_behavior", [
        ('--workers', '0', 'error'),
        ('--workers', '-1', 'error'),
        ('--workers', 'abc', 'error'),
        ('--workers', '1', 'success'),
        ('--workers', '8', 'success'),
    ])
    def test_workers_option_validation(self, option, value, expected_behavior):
        """Test validation of workers option"""
        result = self.runner.invoke(batch_command, [
            '--input-dir', '.',
            option, value
        ])
        
        if expected_behavior == 'error':
            assert result.exit_code != 0
        else:
            # May still fail due to missing files, but option should be valid
            assert 'workers' not in result.output.lower() or result.exit_code == 0

class TestBatchCLIErrorHandling:
    """Test CLI error handling scenarios"""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_missing_input_directory(self):
        """Test handling of missing input directory"""
        result = self.runner.invoke(batch_command, [
            '--input-dir', '/nonexistent/directory'
        ])
        
        assert result.exit_code != 0
        assert 'not found' in result.output.lower() or 'does not exist' in result.output.lower()
    
    def test_invalid_output_directory_permissions(self):
        """Test handling of output directory permission errors"""
        with self.runner.isolated_filesystem():
            # Create input file
            with open('input.yml', 'w') as f:
                f.write('test: content')
            
            # Mock permission error
            with patch('os.makedirs', side_effect=PermissionError("Permission denied")):
                result = self.runner.invoke(batch_command, [
                    '--input-dir', '.',
                    '--output-dir', '/restricted/path'
                ])
                
                assert result.exit_code != 0
                assert 'permission' in result.output.lower()
    
    def test_invalid_pattern_handling(self):
        """Test handling of invalid file patterns"""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(batch_command, [
                '--input-dir', '.',
                '--pattern', '[invalid-regex'
            ])
            
            # Should handle invalid regex gracefully
            assert result.exit_code != 0 or 'error' in result.output.lower()
    
    def test_keyboard_interrupt_handling(self):
        """Test handling of keyboard interrupt during processing"""
        with patch('fqcn_converter.core.batch.BatchProcessor.process_directory') as mock_process:
            mock_process.side_effect = KeyboardInterrupt()
            
            result = self.runner.invoke(batch_command, [
                '--input-dir', '.'
            ])
            
            assert result.exit_code != 0
            assert 'interrupted' in result.output.lower() or 'cancelled' in result.output.lower()

class TestBatchCLIArgumentParsing:
    """Test CLI argument parsing and validation"""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_help_output(self):
        """Test help output contains all expected options"""
        result = self.runner.invoke(batch_command, ['--help'])
        
        assert result.exit_code == 0
        expected_options = [
            '--input-dir',
            '--output-dir', 
            '--pattern',
            '--recursive',
            '--backup',
            '--dry-run',
            '--parallel',
            '--workers',
            '--verbose'
        ]
        
        for option in expected_options:
            assert option in result.output
    
    def test_conflicting_options_handling(self):
        """Test handling of conflicting CLI options"""
        # Test dry-run with backup (might be conflicting)
        result = self.runner.invoke(batch_command, [
            '--input-dir', '.',
            '--dry-run',
            '--backup'
        ])
        
        # Should either work or provide clear error message
        if result.exit_code != 0:
            assert 'conflict' in result.output.lower() or result.exit_code == 0
    
    @pytest.mark.parametrize("verbose_flag", ['-v', '--verbose'])
    def test_verbose_flag_variations(self, verbose_flag):
        """Test different verbose flag formats"""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(batch_command, [
                '--input-dir', '.',
                verbose_flag
            ])
            
            # Verbose flag should be accepted (may fail due to missing files)
            assert verbose_flag not in result.output or result.exit_code == 0
```

#### 3.2 Logging Utils Coverage (`utils/logging.py`)

**Current Status**: 70% coverage (46 lines uncovered)

**Implementation Strategy**:

```python
# tests/unit/test_logging_utils_comprehensive.py
import pytest
import logging
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from fqcn_converter.utils.logging import (
    setup_logging, 
    get_logger, 
    LoggingConfiguration,
    CustomFormatter
)

class TestLoggingConfiguration:
    """Test logging configuration scenarios"""
    
    def test_default_logging_setup(self):
        """Test default logging configuration"""
        logger = setup_logging()
        
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0
    
    def test_debug_level_logging_setup(self):
        """Test debug level logging configuration"""
        logger = setup_logging(level=logging.DEBUG)
        
        assert logger.level == logging.DEBUG
    
    def test_file_logging_setup(self, tmp_path):
        """Test file-based logging configuration"""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file=str(log_file))
        
        # Test that file handler is added
        file_handlers = [h for h in logger.handlers if hasattr(h, 'baseFilename')]
        assert len(file_handlers) > 0
        assert str(log_file) in file_handlers[0].baseFilename
    
    def test_console_and_file_logging(self, tmp_path):
        """Test combined console and file logging"""
        log_file = tmp_path / "combined.log"
        logger = setup_logging(
            level=logging.DEBUG,
            log_file=str(log_file),
            console_output=True
        )
        
        # Should have both console and file handlers
        assert len(logger.handlers) >= 2
    
    def test_logging_with_custom_format(self):
        """Test logging with custom format string"""
        custom_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logger = setup_logging(format_string=custom_format)
        
        # Verify format is applied to handlers
        for handler in logger.handlers:
            if hasattr(handler, 'formatter') and handler.formatter:
                assert custom_format in str(handler.formatter._fmt)

class TestLoggingFormatters:
    """Test logging formatters and handlers"""
    
    def test_custom_formatter_creation(self):
        """Test custom formatter creation and configuration"""
        formatter = CustomFormatter()
        
        # Test different log levels
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert "Test message" in formatted
        assert "INFO" in formatted
    
    def test_formatter_with_exception_info(self):
        """Test formatter handling of exception information"""
        formatter = CustomFormatter()
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Error occurred",
                args=(),
                exc_info=True
            )
            
            formatted = formatter.format(record)
            assert "Error occurred" in formatted
            assert "ValueError" in formatted
            assert "Test exception" in formatted
    
    def test_different_log_levels_formatting(self):
        """Test formatting of different log levels"""
        formatter = CustomFormatter()
        
        levels = [
            (logging.DEBUG, "DEBUG"),
            (logging.INFO, "INFO"),
            (logging.WARNING, "WARNING"),
            (logging.ERROR, "ERROR"),
            (logging.CRITICAL, "CRITICAL")
        ]
        
        for level, level_name in levels:
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="test.py",
                lineno=1,
                msg=f"Test {level_name} message",
                args=(),
                exc_info=None
            )
            
            formatted = formatter.format(record)
            assert level_name in formatted
            assert f"Test {level_name} message" in formatted

class TestLoggingErrorHandling:
    """Test logging error handling scenarios"""
    
    def test_invalid_log_file_path(self):
        """Test handling of invalid log file paths"""
        with pytest.raises((OSError, PermissionError, FileNotFoundError)):
            setup_logging(log_file="/invalid/path/that/does/not/exist/test.log")
    
    def test_permission_denied_log_file(self, tmp_path):
        """Test handling of permission denied for log file"""
        # Create directory with no write permissions
        restricted_dir = tmp_path / "restricted"
        restricted_dir.mkdir()
        restricted_dir.chmod(0o444)  # Read-only
        
        log_file = restricted_dir / "test.log"
        
        try:
            with pytest.raises(PermissionError):
                setup_logging(log_file=str(log_file))
        finally:
            restricted_dir.chmod(0o755)  # Restore permissions for cleanup
    
    def test_disk_full_simulation(self, tmp_path, monkeypatch):
        """Test handling of disk full scenarios"""
        log_file = tmp_path / "test.log"
        
        # Mock file write to simulate disk full
        original_write = open.__enter__
        
        def mock_write_error(*args, **kwargs):
            raise OSError("No space left on device")
        
        with patch('builtins.open', side_effect=mock_write_error):
            with pytest.raises(OSError):
                logger = setup_logging(log_file=str(log_file))
                logger.info("Test message")
    
    def test_concurrent_logging_access(self, tmp_path):
        """Test concurrent access to log files"""
        log_file = tmp_path / "concurrent.log"
        
        # Setup multiple loggers pointing to same file
        logger1 = setup_logging(log_file=str(log_file), logger_name="logger1")
        logger2 = setup_logging(log_file=str(log_file), logger_name="logger2")
        
        # Both should be able to log without conflicts
        logger1.info("Message from logger1")
        logger2.info("Message from logger2")
        
        # Verify both messages are in the file
        if log_file.exists():
            content = log_file.read_text()
            assert "Message from logger1" in content
            assert "Message from logger2" in content

class TestLoggingIntegration:
    """Test logging integration with other components"""
    
    def test_logger_hierarchy(self):
        """Test logger hierarchy and inheritance"""
        parent_logger = get_logger("parent")
        child_logger = get_logger("parent.child")
        
        # Child should inherit from parent
        assert child_logger.parent == parent_logger or child_logger.name.startswith(parent_logger.name)
    
    def test_logging_in_multiprocessing_context(self):
        """Test logging behavior in multiprocessing context"""
        import multiprocessing
        
        def log_from_process(message):
            logger = get_logger("multiprocess_test")
            logger.info(message)
            return True
        
        # Test that logging works in subprocess
        with multiprocessing.Pool(1) as pool:
            result = pool.apply(log_from_process, ("Test multiprocess message",))
            assert result is True
    
    def test_logging_configuration_persistence(self):
        """Test that logging configuration persists across module imports"""
        # Setup logging
        logger1 = setup_logging(level=logging.DEBUG)
        
        # Get logger from different context
        logger2 = get_logger("test_persistence")
        
        # Configuration should be consistent
        assert logger2.level <= logging.DEBUG or logger2.parent.level <= logging.DEBUG
    
    @pytest.mark.parametrize("log_level,should_output", [
        (logging.DEBUG, True),
        (logging.INFO, True),
        (logging.WARNING, False),
        (logging.ERROR, False),
    ])
    def test_log_level_filtering(self, log_level, should_output, caplog):
        """Test log level filtering works correctly"""
        logger = setup_logging(level=logging.WARNING)
        
        with caplog.at_level(logging.DEBUG):
            logger.log(log_level, "Test message")
        
        if should_output:
            assert "Test message" in caplog.text
        else:
            assert "Test message" not in caplog.text or len(caplog.records) == 0
```

### Phase 4: Maintenance and Monitoring

#### 4.1 Automated Coverage Monitoring

```python
# scripts/coverage_monitor.py
import json
import sys
from pathlib import Path
from datetime import datetime

class CoverageMonitor:
    """Monitor and track coverage trends"""
    
    def __init__(self, coverage_file="coverage.json", history_file="coverage_history.json"):
        self.coverage_file = coverage_file
        self.history_file = history_file
    
    def record_coverage(self):
        """Record current coverage in history"""
        if not Path(self.coverage_file).exists():
            print(f"Coverage file {self.coverage_file} not found")
            return
        
        with open(self.coverage_file) as f:
            coverage_data = json.load(f)
        
        # Extract overall coverage
        overall_coverage = coverage_data['totals']['percent_covered']
        
        # Load history
        history = self.load_history()
        
        # Add current record
        history.append({
            'timestamp': datetime.now().isoformat(),
            'overall_coverage': overall_coverage,
            'files': {
                filename: file_data['summary']['percent_covered']
                for filename, file_data in coverage_data['files'].items()
                if 'src/fqcn_converter' in filename
            }
        })
        
        # Save updated history
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        print(f"Recorded coverage: {overall_coverage:.1f}%")
    
    def load_history(self):
        """Load coverage history"""
        if Path(self.history_file).exists():
            with open(self.history_file) as f:
                return json.load(f)
        return []
    
    def check_coverage_regression(self, threshold=1.0):
        """Check for coverage regression"""
        history = self.load_history()
        if len(history) < 2:
            return True  # Not enough data
        
        current = history[-1]['overall_coverage']
        previous = history[-2]['overall_coverage']
        
        regression = previous - current
        if regression > threshold:
            print(f"Coverage regression detected: {regression:.1f}% decrease")
            return False
        
        return True
    
    def generate_trend_report(self):
        """Generate coverage trend report"""
        history = self.load_history()
        if not history:
            print("No coverage history available")
            return
        
        print("Coverage Trend Report")
        print("=" * 50)
        
        for record in history[-10:]:  # Last 10 records
            timestamp = record['timestamp'][:19]  # Remove microseconds
            coverage = record['overall_coverage']
            print(f"{timestamp}: {coverage:.1f}%")
```

#### 4.2 Coverage Quality Gates

```python
# scripts/coverage_quality_gate.py
def check_coverage_quality_gates():
    """Check coverage quality gates"""
    gates = {
        'overall_minimum': 90.0,
        'file_minimum': 85.0,
        'new_code_minimum': 95.0,
        'regression_threshold': 1.0
    }
    
    # Load current coverage
    with open('coverage.json') as f:
        coverage_data = json.load(f)
    
    overall_coverage = coverage_data['totals']['percent_covered']
    
    # Check overall coverage
    if overall_coverage < gates['overall_minimum']:
        print(f"FAIL: Overall coverage {overall_coverage:.1f}% below minimum {gates['overall_minimum']}%")
        return False
    
    # Check individual file coverage
    failed_files = []
    for filename, file_data in coverage_data['files'].items():
        if 'src/fqcn_converter' in filename:
            file_coverage = file_data['summary']['percent_covered']
            if file_coverage < gates['file_minimum']:
                failed_files.append((filename, file_coverage))
    
    if failed_files:
        print("FAIL: Files below minimum coverage:")
        for filename, coverage in failed_files:
            print(f"  {filename}: {coverage:.1f}%")
        return False
    
    print(f"PASS: All coverage quality gates met (Overall: {overall_coverage:.1f}%)")
    return True

if __name__ == "__main__":
    success = check_coverage_quality_gates()
    sys.exit(0 if success else 1)
```

#### 4.3 Pre-commit Coverage Hooks

```yaml
# .pre-commit-config.yaml (coverage section)
repos:
  - repo: local
    hooks:
      - id: coverage-check
        name: Coverage Check
        entry: python scripts/coverage_quality_gate.py
        language: system
        pass_filenames: false
        always_run: true
        
      - id: coverage-diff
        name: Coverage Diff Check
        entry: python scripts/check_coverage_diff.py
        language: system
        pass_filenames: false
        always_run: true
```

## Best Practices for Coverage Improvement

### 1. Systematic Approach
- Start with modules having the lowest coverage
- Focus on error handling and edge cases first
- Use coverage reports to guide test development
- Implement tests incrementally

### 2. Quality over Quantity
- Aim for meaningful tests, not just coverage percentage
- Test behavior, not just code execution
- Include both positive and negative test cases
- Verify error messages and exception types

### 3. Maintainable Test Code
- Use descriptive test names that explain the scenario
- Group related tests in classes
- Use parametrized tests for similar scenarios
- Keep tests independent and isolated

### 4. Continuous Monitoring
- Track coverage trends over time
- Set up automated coverage reporting
- Implement coverage quality gates in CI/CD
- Regular review of coverage gaps

### 5. Team Collaboration
- Share coverage improvement strategies
- Code review for test quality
- Document testing patterns and conventions
- Regular coverage review meetings

This comprehensive coverage improvement strategy provides a systematic approach to achieving and maintaining high test coverage while ensuring test quality and maintainability.