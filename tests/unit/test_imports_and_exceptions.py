"""
Tests for basic imports and exception handling to improve coverage.
"""

from pathlib import Path

import pytest


def test_package_imports():
    """Test that all main package components can be imported."""
    # Test main package import
    import fqcn_converter

    assert hasattr(fqcn_converter, "__version__")

    # Test core imports
    # Test exception imports
    from fqcn_converter import exceptions

    # Test CLI imports
    from fqcn_converter.cli import batch as cli_batch
    from fqcn_converter.cli import convert, main, validate

    # Test config imports
    from fqcn_converter.config import manager
    from fqcn_converter.config.manager import ConfigurationManager
    from fqcn_converter.core import batch, converter, validator
    from fqcn_converter.core.batch import BatchProcessor, BatchResult
    from fqcn_converter.core.converter import ConversionResult, FQCNConverter
    from fqcn_converter.core.validator import (
        ValidationEngine,
        ValidationIssue,
        ValidationResult,
    )
    from fqcn_converter.exceptions import (
        BatchProcessingError,
        ConfigurationError,
        ConversionError,
        FileAccessError,
        FQCNConverterError,
        ValidationError,
        YAMLParsingError,
    )

    # Test utils imports
    from fqcn_converter.utils import logging, yaml_handler


def test_exception_hierarchy():
    """Test exception class hierarchy and basic functionality."""
    from fqcn_converter.exceptions import (
        BatchProcessingError,
        ConfigurationError,
        ConversionError,
        FileAccessError,
        FQCNConverterError,
        ValidationError,
        YAMLParsingError,
    )

    # Test base exception
    base_error = FQCNConverterError("Base error")
    assert str(base_error) == "Base error"
    assert isinstance(base_error, Exception)

    # Test specific exceptions
    conv_error = ConversionError("Conversion failed")
    assert isinstance(conv_error, FQCNConverterError)

    val_error = ValidationError("Validation failed")
    assert isinstance(val_error, FQCNConverterError)

    file_error = FileAccessError("File not found")
    assert isinstance(file_error, FQCNConverterError)

    config_error = ConfigurationError("Config error")
    assert isinstance(config_error, FQCNConverterError)

    yaml_error = YAMLParsingError("YAML error")
    assert isinstance(yaml_error, FQCNConverterError)

    batch_error = BatchProcessingError("Batch error")
    assert isinstance(batch_error, FQCNConverterError)


def test_logging_utils():
    """Test logging utilities."""
    from fqcn_converter.utils.logging import get_logger

    logger = get_logger(__name__)
    assert logger is not None
    assert logger.name == __name__


def test_yaml_handler_utils():
    """Test YAML handler utilities."""
    from fqcn_converter.utils.yaml_handler import safe_dump, safe_load

    # Test basic YAML operations
    test_data = {"test": "value", "number": 42}
    yaml_str = safe_dump(test_data)
    assert isinstance(yaml_str, str)
    assert "test: value" in yaml_str

    loaded_data = safe_load(yaml_str)
    assert loaded_data == test_data


def test_config_manager_basic():
    """Test basic ConfigurationManager functionality."""
    from fqcn_converter.config.manager import ConfigurationManager

    # Test initialization
    config_manager = ConfigurationManager()
    assert config_manager is not None

    # Test loading default mappings
    mappings = config_manager.load_default_mappings()
    assert isinstance(mappings, dict)
    assert len(mappings) > 0

    # Test that common modules are in mappings
    assert "copy" in mappings
    assert "file" in mappings
    assert "service" in mappings


def test_validation_result_classes():
    """Test validation result classes."""
    from fqcn_converter.core.validator import ValidationIssue, ValidationResult

    # Test ValidationIssue
    issue = ValidationIssue(
        severity="error", message="Test error", line_number=10, column=5
    )
    assert issue.severity == "error"
    assert issue.message == "Test error"
    assert issue.line_number == 10
    assert issue.column == 5

    # Test ValidationResult
    result = ValidationResult(valid=False, file_path="test.yml", issues=[issue])
    assert result.valid is False
    assert result.file_path == "test.yml"
    assert len(result.issues) == 1
    assert result.issues[0] == issue


def test_conversion_result_class():
    """Test ConversionResult class."""
    from fqcn_converter.core.converter import ConversionResult

    result = ConversionResult(
        success=True,
        file_path="test.yml",
        changes_made=5,
        errors=[],
        warnings=["Warning message"],
        original_content="original",
        converted_content="converted",
        processing_time=1.5,
    )

    assert result.success is True
    assert result.file_path == "test.yml"
    assert result.changes_made == 5
    assert result.errors == []
    assert result.warnings == ["Warning message"]
    assert result.original_content == "original"
    assert result.converted_content == "converted"
    assert result.processing_time == 1.5


def test_batch_result_class():
    """Test BatchResult class."""
    from fqcn_converter.core.batch import BatchResult
    from fqcn_converter.core.converter import ConversionResult

    # Create a sample conversion result
    conv_result = ConversionResult(
        success=True, file_path="test.yml", changes_made=3, processing_time=0.5
    )

    batch_result = BatchResult(
        total_projects=1,
        successful_conversions=1,
        failed_conversions=0,
        project_results=[conv_result],
        execution_time=1.0,
        summary_report="Test summary",
    )

    assert batch_result.total_projects == 1
    assert batch_result.successful_conversions == 1
    assert batch_result.failed_conversions == 0
    assert len(batch_result.project_results) == 1
    assert batch_result.execution_time == 1.0
    assert batch_result.summary_report == "Test summary"

    # Test __len__ method
    assert len(batch_result) == 1

    # Test iteration
    results_list = list(batch_result)
    assert len(results_list) == 1
    assert results_list[0]["success"] is True
    assert results_list[0]["project_path"] == "test.yml"

    # Test indexing
    first_result = batch_result[0]
    assert first_result["success"] is True
    assert first_result["project_path"] == "test.yml"
