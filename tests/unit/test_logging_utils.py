#!/usr/bin/env python3
"""
Comprehensive test module for logging utilities.
"""

import json
import logging
import logging.config
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, call, mock_open, patch

import pytest

from fqcn_converter.utils.logging import (
    ColoredFormatter,
    ContextFilter,
    JSONFormatter,
    PerformanceFilter,
    _current_config,
    _logger_registry,
    configure_logger_for_module,
    create_file_logger,
    create_rotating_file_handler,
    create_timed_rotating_handler,
    get_current_config,
    get_default_config,
    get_logger,
    log_performance_metrics,
    reset_logging,
    setup_logging,
    setup_simple_logging,
)


class TestPerformanceFilter:
    """Test PerformanceFilter class."""

    def test_performance_filter_init(self):
        """Test PerformanceFilter initialization."""
        filter_obj = PerformanceFilter()
        assert hasattr(filter_obj, "start_time")
        assert isinstance(filter_obj.start_time, float)

    def test_performance_filter_adds_metrics(self):
        """Test that PerformanceFilter adds performance metrics to log records."""
        filter_obj = PerformanceFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )

        result = filter_obj.filter(record)

        assert result is True
        assert hasattr(record, "elapsed_time")
        assert hasattr(record, "memory_usage")
        assert isinstance(record.elapsed_time, float)
        assert isinstance(record.memory_usage, float)

    def test_get_memory_usage_with_psutil(self):
        """Test memory usage calculation with psutil available."""
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 1024 * 1024 * 50  # 50MB

        with patch("psutil.Process", return_value=mock_process):
            filter_obj = PerformanceFilter()
            memory_usage = filter_obj._get_memory_usage()

            assert memory_usage == 50.0  # 50MB

    def test_get_memory_usage_without_psutil(self):
        """Test memory usage calculation without psutil."""
        with patch.dict("sys.modules", {"psutil": None}):
            filter_obj = PerformanceFilter()
            memory_usage = filter_obj._get_memory_usage()

            assert memory_usage == 0.0


class TestContextFilter:
    """Test ContextFilter class."""

    def test_context_filter_init_default(self):
        """Test ContextFilter initialization with default context."""
        filter_obj = ContextFilter()
        assert filter_obj.context == {}

    def test_context_filter_init_with_context(self):
        """Test ContextFilter initialization with custom context."""
        context = {"user": "test_user", "session": "12345"}
        filter_obj = ContextFilter(context)
        assert filter_obj.context == context

    def test_context_filter_adds_context(self):
        """Test that ContextFilter adds context to log records."""
        context = {"user": "test_user", "operation": "test_op"}
        filter_obj = ContextFilter(context)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )

        result = filter_obj.filter(record)

        assert result is True
        assert record.user == "test_user"
        assert record.operation == "test_op"
        assert hasattr(record, "pid")
        assert hasattr(record, "timestamp_iso")


class TestJSONFormatter:
    """Test JSONFormatter class."""

    def test_json_formatter_init(self):
        """Test JSONFormatter initialization."""
        formatter = JSONFormatter()
        assert hasattr(formatter, "hostname")
        assert isinstance(formatter.hostname, str)

    @patch("os.uname")
    def test_json_formatter_hostname_with_uname(self, mock_uname):
        """Test hostname detection with os.uname available."""
        mock_uname.return_value.nodename = "test-host"
        formatter = JSONFormatter()
        assert formatter.hostname == "test-host"

    def test_json_formatter_hostname_fallback(self):
        """Test hostname fallback when os.uname not available."""
        with patch("os.uname", side_effect=AttributeError):
            formatter = JSONFormatter()
            assert formatter.hostname == "unknown"

    def test_json_formatter_format_basic(self):
        """Test basic JSON formatting."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.module = "test_module"
        record.funcName = "test_function"
        record.process = 12345
        record.thread = 67890

        result = formatter.format(record)

        # Parse JSON to verify structure
        log_data = json.loads(result)
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test.logger"
        assert log_data["message"] == "Test message"
        assert log_data["module"] == "test_module"
        assert log_data["function"] == "test_function"
        assert log_data["line"] == 42
        assert log_data["process_id"] == 12345
        assert log_data["thread_id"] == 67890

    def test_json_formatter_with_exception(self):
        """Test JSON formatting with exception information."""
        formatter = JSONFormatter()

        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="/test/path.py",
            lineno=42,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )
        record.module = "test_module"
        record.funcName = "test_function"
        record.process = 12345
        record.thread = 67890

        result = formatter.format(record)

        log_data = json.loads(result)
        assert "exception" in log_data
        assert log_data["exception"]["type"] == "ValueError"
        assert log_data["exception"]["message"] == "Test exception"
        assert "traceback" in log_data["exception"]

    def test_json_formatter_with_performance_metrics(self):
        """Test JSON formatting with performance metrics."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Performance test",
            args=(),
            exc_info=None,
        )
        record.module = "test_module"
        record.funcName = "test_function"
        record.process = 12345
        record.thread = 67890
        record.elapsed_time = 1.5
        record.memory_usage = 25.0

        result = formatter.format(record)

        log_data = json.loads(result)
        assert "performance" in log_data
        assert log_data["performance"]["elapsed_time"] == 1.5
        assert log_data["performance"]["memory_usage_mb"] == 25.0

    def test_json_formatter_with_custom_context(self):
        """Test JSON formatting with custom context attributes."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Context test",
            args=(),
            exc_info=None,
        )
        record.module = "test_module"
        record.funcName = "test_function"
        record.process = 12345
        record.thread = 67890
        record.user_id = "user123"
        record.operation = "test_operation"
        record.timestamp_iso = "2023-01-01T12:00:00"

        result = formatter.format(record)

        log_data = json.loads(result)
        assert log_data["timestamp_iso"] == "2023-01-01T12:00:00"
        assert "context" in log_data
        assert log_data["context"]["user_id"] == "user123"
        assert log_data["context"]["operation"] == "test_operation"


class TestColoredFormatter:
    """Test ColoredFormatter class."""

    def test_colored_formatter_format_info(self):
        """Test colored formatting for INFO level."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Info message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert "\033[32m" in result  # Green color for INFO
        assert "\033[0m" in result  # Reset color
        assert "Info message" in result

    def test_colored_formatter_format_error(self):
        """Test colored formatting for ERROR level."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Error message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert "\033[31m" in result  # Red color for ERROR
        assert "\033[0m" in result  # Reset color
        assert "Error message" in result

    def test_colored_formatter_unknown_level(self):
        """Test colored formatting for unknown level."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test",
            level=99,
            pathname="",
            lineno=0,
            msg="Unknown level",
            args=(),
            exc_info=None,
        )
        record.levelname = "UNKNOWN"

        result = formatter.format(record)

        # Should not add color for unknown levels
        assert "\033[" not in result or result.count("\033[") == 0
        assert "Unknown level" in result


class TestFileHandlers:
    """Test file handler creation functions."""

    def test_create_rotating_file_handler(self):
        """Test creating rotating file handler."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")

            handler = create_rotating_file_handler(
                log_file=log_file, max_bytes=1024, backup_count=3
            )

            assert isinstance(handler, logging.handlers.RotatingFileHandler)
            assert handler.maxBytes == 1024
            assert handler.backupCount == 3

    def test_create_rotating_file_handler_creates_directory(self):
        """Test that rotating file handler creates directory if needed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = os.path.join(temp_dir, "logs", "subdir")
            log_file = os.path.join(log_dir, "test.log")

            handler = create_rotating_file_handler(log_file)

            assert os.path.exists(log_dir)
            assert isinstance(handler, logging.handlers.RotatingFileHandler)

    def test_create_timed_rotating_handler(self):
        """Test creating timed rotating file handler."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")

            handler = create_timed_rotating_handler(
                log_file=log_file,
                when="H",  # Use 'H' for hourly to test interval properly
                interval=2,
                backup_count=7,
            )

            assert isinstance(handler, logging.handlers.TimedRotatingFileHandler)
            assert handler.when == "H"
            assert handler.interval == 7200  # 2 hours in seconds
            assert handler.backupCount == 7


class TestDefaultConfig:
    """Test default configuration generation."""

    def test_get_default_config_basic(self):
        """Test basic default configuration."""
        config = get_default_config()

        assert config["version"] == 1
        assert config["disable_existing_loggers"] is False
        assert "formatters" in config
        assert "handlers" in config
        assert "root" in config
        assert "loggers" in config

    def test_get_default_config_with_json(self):
        """Test default configuration with JSON formatting."""
        config = get_default_config(format_json=True)

        assert config["handlers"]["console"]["formatter"] == "json"

    def test_get_default_config_with_file(self):
        """Test default configuration with file logging."""
        config = get_default_config(log_file="/tmp/test.log")

        assert "file" in config["handlers"]
        assert config["handlers"]["file"]["filename"] == "/tmp/test.log"
        assert "file" in config["root"]["handlers"]

    def test_get_default_config_with_performance(self):
        """Test default configuration with performance logging."""
        config = get_default_config(enable_performance_logging=True)

        assert "performance_filter" in config["filters"]
        assert "performance_filter" in config["handlers"]["console"]["filters"]

    def test_get_default_config_with_context(self):
        """Test default configuration with context."""
        context = {"app": "test_app", "version": "1.0"}
        config = get_default_config(context=context)

        assert config["filters"]["context_filter"]["context"] == context

    def test_get_default_config_no_colors_with_json(self):
        """Test that colors are disabled when JSON formatting is enabled."""
        config = get_default_config(format_json=True, enable_colors=True)

        # Should use JSON formatter, not colored
        assert config["handlers"]["console"]["formatter"] == "json"

    def test_get_default_config_file_with_performance(self):
        """Test default configuration with file logging and performance enabled."""
        config = get_default_config(
            log_file="/tmp/test.log", enable_performance_logging=True
        )

        assert "file" in config["handlers"]
        assert "performance_filter" in config["handlers"]["file"]["filters"]
        assert "file" in config["root"]["handlers"]
        assert "file" in config["loggers"]["fqcn_converter"]["handlers"]


class TestSetupLogging:
    """Test setup_logging function."""

    def setup_method(self):
        """Reset logging state before each test."""
        reset_logging()

    def test_setup_logging_basic(self):
        """Test basic logging setup."""
        with patch("logging.config.dictConfig") as mock_dict_config:
            setup_logging(level="INFO")

            mock_dict_config.assert_called_once()
            config = mock_dict_config.call_args[0][0]
            assert config["root"]["level"] == "INFO"

    def test_setup_logging_invalid_level(self):
        """Test setup_logging with invalid level."""
        with pytest.raises(ValueError, match="Invalid log level"):
            setup_logging(level="INVALID")

    def test_setup_logging_with_file(self):
        """Test logging setup with file output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")

            with patch("logging.config.dictConfig") as mock_dict_config:
                setup_logging(level="DEBUG", log_file=log_file)

                config = mock_dict_config.call_args[0][0]
                assert "file" in config["handlers"]
                assert config["handlers"]["file"]["filename"] == log_file

    def test_setup_logging_with_custom_config(self):
        """Test logging setup with custom configuration."""
        custom_config = {
            "version": 1,
            "handlers": {"custom": {"class": "logging.StreamHandler"}},
            "root": {"handlers": ["custom"]},
        }

        with patch("logging.config.dictConfig") as mock_dict_config:
            setup_logging(config_dict=custom_config)

            mock_dict_config.assert_called_once_with(custom_config)

    def test_setup_logging_json_format(self):
        """Test logging setup with JSON formatting."""
        with patch("logging.config.dictConfig") as mock_dict_config:
            setup_logging(format_json=True)

            config = mock_dict_config.call_args[0][0]
            assert config["handlers"]["console"]["formatter"] == "json"

    def test_setup_logging_performance_enabled(self):
        """Test logging setup with performance logging."""
        with patch("logging.config.dictConfig") as mock_dict_config:
            setup_logging(enable_performance_logging=True)

            config = mock_dict_config.call_args[0][0]
            assert "performance_filter" in config["filters"]

    def test_setup_logging_with_context(self):
        """Test logging setup with context."""
        context = {"service": "test_service"}

        with patch("logging.config.dictConfig") as mock_dict_config:
            setup_logging(context=context)

            config = mock_dict_config.call_args[0][0]
            assert config["filters"]["context_filter"]["context"] == context

    def test_setup_logging_already_configured(self):
        """Test that setup_logging skips if already configured."""
        with patch("logging.config.dictConfig") as mock_dict_config:
            # First call should configure
            setup_logging()
            assert mock_dict_config.call_count == 1

            # Second call should be skipped
            setup_logging()
            assert mock_dict_config.call_count == 1

    def test_setup_logging_force_reconfigure(self):
        """Test force reconfiguration."""
        with patch("logging.config.dictConfig") as mock_dict_config:
            # First call
            setup_logging()
            assert mock_dict_config.call_count == 1

            # Force reconfigure
            setup_logging(force_reconfigure=True)
            assert mock_dict_config.call_count == 2

    def test_setup_logging_config_failure(self):
        """Test logging setup failure fallback."""
        with patch("logging.config.dictConfig", side_effect=Exception("Config failed")):
            with patch("logging.basicConfig") as mock_basic_config:
                with pytest.raises(Exception, match="Config failed"):
                    setup_logging()

                mock_basic_config.assert_called_once()

    def test_setup_logging_file_permission_error(self):
        """Test logging setup with file permission error."""
        with patch(
            "logging.config.dictConfig",
            side_effect=PermissionError("Permission denied"),
        ):
            with patch("logging.basicConfig") as mock_basic_config:
                with pytest.raises(PermissionError):
                    setup_logging(log_file="/root/test.log")

                mock_basic_config.assert_called_once()


class TestGetLogger:
    """Test get_logger function."""

    def setup_method(self):
        """Reset logging state before each test."""
        reset_logging()

    def test_get_logger_basic(self):
        """Test basic logger creation."""
        logger = get_logger("test.module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"
        assert "test.module" in _logger_registry

    def test_get_logger_with_context(self):
        """Test logger creation with context."""
        context = {"user": "test_user"}
        logger = get_logger("test.module", context=context)

        assert isinstance(logger, logging.Logger)
        # Check that context filter was added
        assert len(logger.filters) > 0

    def test_get_logger_with_performance_tracking(self):
        """Test logger creation with performance tracking."""
        logger = get_logger("test.module", performance_tracking=True)

        assert isinstance(logger, logging.Logger)
        # Check that performance filter was added
        assert len(logger.filters) > 0

    def test_get_logger_cached(self):
        """Test that loggers are cached in registry."""
        logger1 = get_logger("test.module")
        logger2 = get_logger("test.module")

        assert logger1 is logger2
        assert len(_logger_registry) == 1

    def test_get_logger_different_names(self):
        """Test creating loggers with different names."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        assert logger1 is not logger2
        assert logger1.name == "module1"
        assert logger2.name == "module2"
        assert len(_logger_registry) == 2


class TestConfigureLoggerForModule:
    """Test configure_logger_for_module function."""

    def setup_method(self):
        """Reset logging state before each test."""
        reset_logging()

    def test_configure_logger_for_module_basic(self):
        """Test basic module logger configuration."""
        logger = configure_logger_for_module("test.module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_configure_logger_for_module_with_level(self):
        """Test module logger configuration with custom level."""
        logger = configure_logger_for_module("test.module", level="DEBUG")

        assert logger.level == logging.DEBUG

    def test_configure_logger_for_module_invalid_level(self):
        """Test module logger configuration with invalid level."""
        logger = configure_logger_for_module("test.module", level="INVALID")

        # Should not change level for invalid level
        assert logger.level != logging.NOTSET or logger.level == logging.NOTSET

    def test_configure_logger_for_module_with_context(self):
        """Test module logger configuration with context."""
        context = {"module": "test_module"}
        logger = configure_logger_for_module("test.module", context=context)

        assert isinstance(logger, logging.Logger)
        assert len(logger.filters) > 0


class TestLogPerformanceMetrics:
    """Test log_performance_metrics function."""

    def test_log_performance_metrics(self):
        """Test logging performance metrics."""
        logger = MagicMock()
        start_time = time.time() - 1.5  # 1.5 seconds ago

        log_performance_metrics(
            logger, "test_operation", start_time, custom_metric=42, status="success"
        )

        logger.info.assert_called_once()
        call_args = logger.info.call_args

        assert "Performance metrics for test_operation" in call_args[0][0]
        extra = call_args[1]["extra"]
        assert extra["operation"] == "test_operation"
        assert "duration_seconds" in extra
        assert extra["custom_metric"] == 42
        assert extra["status"] == "success"


class TestCreateFileLogger:
    """Test create_file_logger function."""

    def test_create_file_logger_basic(self):
        """Test basic file logger creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")

            logger = create_file_logger("test.file.logger", log_file)

            assert isinstance(logger, logging.Logger)
            assert logger.name == "test.file.logger"
            assert len(logger.handlers) == 1
            assert isinstance(logger.handlers[0], logging.handlers.RotatingFileHandler)

    def test_create_file_logger_with_json(self):
        """Test file logger creation with JSON formatting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")

            logger = create_file_logger(
                "test.file.logger.json", log_file, format_json=True
            )

            assert len(logger.handlers) > 0
            handler = logger.handlers[0]
            assert isinstance(handler.formatter, JSONFormatter)

    def test_create_file_logger_custom_params(self):
        """Test file logger creation with custom parameters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test_custom.log")

            logger = create_file_logger(
                "test.file.logger.custom",
                log_file,
                level="DEBUG",
                max_bytes=2048,
                backup_count=10,
            )

            assert logger.level == logging.DEBUG
            assert len(logger.handlers) > 0
            handler = logger.handlers[0]
            assert handler.maxBytes == 2048
            assert handler.backupCount == 10


class TestUtilityFunctions:
    """Test utility functions."""

    def setup_method(self):
        """Reset logging state before each test."""
        reset_logging()

    def test_get_current_config_none(self):
        """Test get_current_config when no config is set."""
        config = get_current_config()
        assert config is None

    def test_get_current_config_after_setup(self):
        """Test get_current_config after setup_logging."""
        with patch("logging.config.dictConfig"):
            setup_logging()
            config = get_current_config()
            assert config is not None
            assert isinstance(config, dict)

    def test_reset_logging(self):
        """Test reset_logging function."""
        # Setup some state
        with patch("logging.config.dictConfig"):
            setup_logging()
            get_logger("test.logger")

        assert get_current_config() is not None
        assert len(_logger_registry) > 0

        # Reset
        with patch("logging.basicConfig") as mock_basic:
            reset_logging()

        assert get_current_config() is None
        assert len(_logger_registry) == 0
        mock_basic.assert_called_once_with(force=True)

    def test_setup_simple_logging_basic(self):
        """Test setup_simple_logging basic usage."""
        with patch("fqcn_converter.utils.logging.setup_logging") as mock_setup:
            with patch("fqcn_converter.utils.logging.get_logger") as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger

                result = setup_simple_logging()

                mock_setup.assert_called_once_with(
                    level="INFO", log_file=None, enable_colors=True
                )
                mock_get_logger.assert_called_once_with("fqcn_converter")
                assert result is mock_logger

    def test_setup_simple_logging_with_file(self):
        """Test setup_simple_logging with file logging."""
        with patch("fqcn_converter.utils.logging.setup_logging") as mock_setup:
            with patch("fqcn_converter.utils.logging.get_logger") as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger

                result = setup_simple_logging(
                    level="DEBUG", log_to_file=True, log_file="custom.log"
                )

                mock_setup.assert_called_once_with(
                    level="DEBUG", log_file="custom.log", enable_colors=True
                )
                assert result is mock_logger

    def test_setup_simple_logging_no_file(self):
        """Test setup_simple_logging without file logging."""
        with patch("fqcn_converter.utils.logging.setup_logging") as mock_setup:
            with patch("fqcn_converter.utils.logging.get_logger") as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger

                result = setup_simple_logging(log_to_file=False)

                mock_setup.assert_called_once_with(
                    level="INFO", log_file=None, enable_colors=True
                )
                assert result is mock_logger


class TestThreadSafety:
    """Test thread safety of logging utilities."""

    def setup_method(self):
        """Reset logging state before each test."""
        reset_logging()

    def test_concurrent_logger_creation(self):
        """Test that concurrent logger creation is thread-safe."""
        import threading
        import time

        loggers = []
        errors = []

        def create_logger(name):
            try:
                logger = get_logger(f"test.{name}")
                loggers.append(logger)
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_logger, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0
        assert len(loggers) == 10
        assert len(_logger_registry) == 10

    def test_concurrent_setup_logging(self):
        """Test that concurrent setup_logging calls are thread-safe."""
        import threading

        setup_calls = []
        errors = []

        def setup_logging_thread():
            try:
                with patch("logging.config.dictConfig") as mock_config:
                    setup_logging()
                    setup_calls.append(mock_config.call_count)
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(5):
            thread = threading.Thread(target=setup_logging_thread)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0
        # Only one thread should actually configure logging
        assert sum(setup_calls) == 1
