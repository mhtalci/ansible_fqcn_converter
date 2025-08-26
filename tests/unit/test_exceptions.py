#!/usr/bin/env python3
"""
Test module for exception hierarchy.
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from fqcn_converter.exceptions import (
    FQCNConverterError,
    ConfigurationError
)


class TestFQCNConverterError:
    """Test base FQCNConverterError class."""

    def test_basic_error_creation(self):
        """Test basic error creation with just message."""
        error = FQCNConverterError("Test error message")
        
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.details == ""
        assert error.suggestions == []
        assert error.recovery_actions == []
        assert error.error_code is None
        assert error.context == {}

    def test_error_with_all_parameters(self):
        """Test error creation with all parameters."""
        error = FQCNConverterError(
            message="Test error",
            details="Detailed error information",
            suggestions=["Try this", "Or this"],
            recovery_actions=["Do this", "Then this"],
            error_code="E001",
            context={"file": "test.yml", "line": 10}
        )
        
        assert error.message == "Test error"
        assert error.details == "Detailed error information"
        assert error.suggestions == ["Try this", "Or this"]
        assert error.recovery_actions == ["Do this", "Then this"]
        assert error.error_code == "E001"
        assert error.context == {"file": "test.yml", "line": 10}

    def test_error_message_building(self):
        """Test that error message is built correctly."""
        error = FQCNConverterError(
            message="Test error",
            details="More details",
            suggestions=["Suggestion 1"],
            recovery_actions=["Action 1"],
            error_code="E001"
        )
        
        error_str = str(error)
        assert "Test error" in error_str
        assert "Details: More details" in error_str
        assert "Error Code: E001" in error_str
        assert "Suggestions:" in error_str
        assert "1. Suggestion 1" in error_str
        assert "Recovery Actions:" in error_str
        assert "1. Action 1" in error_str

    def test_get_recovery_suggestions(self):
        """Test get_recovery_suggestions method."""
        error = FQCNConverterError(
            "Test error",
            recovery_actions=["Action 1", "Action 2"]
        )
        
        suggestions = error.get_recovery_suggestions()
        assert suggestions == ["Action 1", "Action 2"]

    def test_can_recover_with_actions(self):
        """Test can_recover method when recovery actions exist."""
        error = FQCNConverterError(
            "Test error",
            recovery_actions=["Action 1"]
        )
        
        assert error.can_recover() is True

    def test_can_recover_without_actions(self):
        """Test can_recover method when no recovery actions exist."""
        error = FQCNConverterError("Test error")
        
        assert error.can_recover() is False

    def test_error_with_context(self):
        """Test error with context information."""
        context = {
            "file_path": "/path/to/file.yml",
            "line_number": 42,
            "module_name": "copy"
        }
        
        error = FQCNConverterError(
            "Test error",
            context=context
        )
        
        assert error.context == context
        error_str = str(error)
        assert "Context:" in error_str


class TestConfigurationError:
    """Test ConfigurationError class."""

    def test_basic_configuration_error(self):
        """Test basic configuration error creation."""
        error = ConfigurationError("Configuration is invalid")
        
        assert isinstance(error, FQCNConverterError)
        assert "Configuration is invalid" in str(error)

    def test_configuration_error_with_path(self):
        """Test configuration error with config path."""
        config_path = "/path/to/config.yml"
        error = ConfigurationError(
            "Configuration file not found",
            config_path=config_path
        )
        
        assert isinstance(error, FQCNConverterError)
        error_str = str(error)
        assert config_path in error_str

    @patch('os.path.exists')
    def test_configuration_error_missing_file(self, mock_exists):
        """Test configuration error when file doesn't exist."""
        mock_exists.return_value = False
        config_path = "/nonexistent/config.yml"
        
        error = ConfigurationError(
            "Configuration file not found",
            config_path=config_path
        )
        
        error_str = str(error)
        assert config_path in error_str
        # Should suggest creating the file
        assert "Create configuration file" in error_str or "configuration" in error_str.lower()

    def test_configuration_error_with_missing_keys(self):
        """Test configuration error with missing keys."""
        error = ConfigurationError(
            "Missing required configuration",
            missing_keys=["key1", "key2"]
        )
        
        assert isinstance(error, FQCNConverterError)
        # The error should be created successfully
        assert "Missing required configuration" in str(error)

    def test_configuration_error_with_invalid_values(self):
        """Test configuration error with invalid values."""
        error = ConfigurationError(
            "Invalid configuration values",
            invalid_values={"key1": "invalid_value", "key2": "another_invalid"}
        )
        
        assert isinstance(error, FQCNConverterError)
        assert "Invalid configuration values" in str(error)

    def test_configuration_error_inheritance(self):
        """Test that ConfigurationError properly inherits from FQCNConverterError."""
        error = ConfigurationError("Test config error")
        
        assert isinstance(error, FQCNConverterError)
        assert isinstance(error, Exception)
        
        # Should have all base class methods
        assert hasattr(error, 'get_recovery_suggestions')
        assert hasattr(error, 'can_recover')
        assert hasattr(error, 'message')
        assert hasattr(error, 'context')


class TestExceptionModule:
    """Test exception module functionality."""

    def test_exception_imports(self):
        """Test that exceptions can be imported."""
        from fqcn_converter.exceptions import FQCNConverterError, ConfigurationError
        
        assert FQCNConverterError is not None
        assert ConfigurationError is not None

    def test_exception_hierarchy(self):
        """Test exception hierarchy is correct."""
        # ConfigurationError should inherit from FQCNConverterError
        assert issubclass(ConfigurationError, FQCNConverterError)
        
        # FQCNConverterError should inherit from Exception
        assert issubclass(FQCNConverterError, Exception)

    def test_exception_raising_and_catching(self):
        """Test that exceptions can be raised and caught properly."""
        # Test raising and catching base exception
        with pytest.raises(FQCNConverterError) as exc_info:
            raise FQCNConverterError("Test error")
        
        assert "Test error" in str(exc_info.value)
        
        # Test raising and catching configuration exception
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError("Config error")
        
        assert "Config error" in str(exc_info.value)
        
        # Test that ConfigurationError can be caught as FQCNConverterError
        with pytest.raises(FQCNConverterError):
            raise ConfigurationError("Config error")

    def test_exception_with_none_values(self):
        """Test exception handling with None values."""
        error = FQCNConverterError(
            "Test error",
            details=None,
            suggestions=None,
            recovery_actions=None,
            error_code=None,
            context=None
        )
        
        # Should handle None values gracefully
        assert error.details == ""
        assert error.suggestions == []
        assert error.recovery_actions == []
        assert error.error_code is None
        assert error.context == {}
        assert error.can_recover() is False