"""
Logging configuration for FQCN Converter.

This module provides centralized logging configuration with support for
configurable log levels, structured JSON output, log rotation, file output,
and performance metrics logging for optimization.
"""

import json
import logging
import logging.config
import logging.handlers
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional, Union

# Global logger registry and configuration lock
_logger_registry: Dict[str, logging.Logger] = {}
_config_lock = Lock()
_current_config: Optional[Dict[str, Any]] = None


class PerformanceFilter(logging.Filter):
    """Filter that adds performance metrics to log records."""

    def __init__(self) -> None:
        super().__init__()
        self.start_time = time.time()

    def filter(self, record: logging.LogRecord) -> bool:
        """Add performance metrics to the log record."""
        record.elapsed_time = time.time() - self.start_time
        record.memory_usage = self._get_memory_usage()
        return True

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil

            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except ImportError:
            return 0.0


class ContextFilter(logging.Filter):
    """Filter that adds contextual information to log records."""

    def __init__(self, context: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.context = context or {}

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context information to the log record."""
        for key, value in self.context.items():
            setattr(record, key, value)

        # Add standard context
        record.pid = os.getpid()
        record.timestamp_iso = datetime.utcnow().isoformat()

        return True


class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs log records as JSON for structured logging.

    Useful for automation, log aggregation, and analysis tools.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        try:
            self.hostname = os.uname().nodename if hasattr(os, "uname") else "unknown"
        except (AttributeError, OSError):
            self.hostname = "unknown"

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
            "hostname": self.hostname,
        }

        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        # Add performance metrics if available
        if hasattr(record, "elapsed_time"):
            log_entry["performance"] = {
                "elapsed_time": record.elapsed_time,
                "memory_usage_mb": getattr(record, "memory_usage", 0.0),
            }

        # Add context information
        if hasattr(record, "timestamp_iso"):
            log_entry["timestamp_iso"] = record.timestamp_iso

        # Add any custom attributes
        for key, value in record.__dict__.items():
            if key not in log_entry and not key.startswith("_"):
                if key not in [
                    "name",
                    "msg",
                    "args",
                    "levelname",
                    "levelno",
                    "pathname",
                    "filename",
                    "module",
                    "lineno",
                    "funcName",
                    "created",
                    "msecs",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "processName",
                    "process",
                    "getMessage",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                ]:
                    log_entry["context"] = log_entry.get("context", {})
                    log_entry["context"][key] = value

        return json.dumps(log_entry, default=str, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Formatter that adds color coding to console output."""

    # Color codes for different log levels
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with color coding."""
        # Add color to the level name
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
            )

        return super().format(record)


def create_rotating_file_handler(
    log_file: str,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    encoding: str = "utf-8",
) -> logging.handlers.RotatingFileHandler:
    """Create a rotating file handler with specified parameters."""
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding=encoding,
    )

    return handler


def create_timed_rotating_handler(
    log_file: str,
    when: str = "midnight",
    interval: int = 1,
    backup_count: int = 30,
    encoding: str = "utf-8",
) -> logging.handlers.TimedRotatingFileHandler:
    """Create a time-based rotating file handler."""
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_file,
        when=when,
        interval=interval,
        backupCount=backup_count,
        encoding=encoding,
    )

    return handler


def get_default_config(
    level: str = "INFO",
    format_json: bool = False,
    log_file: Optional[str] = None,
    enable_performance_logging: bool = False,
    enable_colors: bool = True,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Get default logging configuration dictionary.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_json: Whether to use JSON formatting
        log_file: Optional file path for file logging
        enable_performance_logging: Whether to include performance metrics
        enable_colors: Whether to use colored console output
        context: Additional context to include in logs

    Returns:
        Dictionary configuration for logging.config.dictConfig
    """
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": (
                    "%(asctime)s - %(name)s - %(levelname)s - "
                    "%(module)s:%(funcName)s:%(lineno)d - %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": JSONFormatter,
            },
            "colored": {
                "()": ColoredFormatter,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "filters": {"context_filter": {"()": ContextFilter, "context": context or {}}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": (
                    "json"
                    if format_json
                    else ("colored" if enable_colors else "standard")
                ),
                "stream": "ext://sys.stdout",
                "filters": ["context_filter"],
            }
        },
        "root": {"level": level, "handlers": ["console"]},
        "loggers": {
            "fqcn_converter": {
                "level": level,
                "handlers": ["console"],
                "propagate": False,
            }
        },
    }

    # Add performance filter if enabled
    if enable_performance_logging:
        config["filters"]["performance_filter"] = {"()": PerformanceFilter}
        config["handlers"]["console"]["filters"].append("performance_filter")

    # Add file handler if log_file is specified
    if log_file:
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": level,
            "formatter": "json" if format_json else "detailed",
            "filename": log_file,
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8",
            "filters": ["context_filter"],
        }

        if enable_performance_logging:
            config["handlers"]["file"]["filters"].append("performance_filter")

        # Add file handler to root and fqcn_converter loggers
        config["root"]["handlers"].append("file")
        config["loggers"]["fqcn_converter"]["handlers"].append("file")

    return config


def setup_logging(
    level: str = "INFO",
    format_json: bool = False,
    log_file: Optional[str] = None,
    config_dict: Optional[Dict[str, Any]] = None,
    enable_performance_logging: bool = False,
    enable_colors: bool = True,
    context: Optional[Dict[str, Any]] = None,
    force_reconfigure: bool = False,
) -> None:
    """
    Configure logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_json: Whether to use JSON formatting for structured logging
        log_file: Optional file path for file logging with rotation
        config_dict: Optional custom logging configuration dictionary
        enable_performance_logging: Whether to include performance metrics
        enable_colors: Whether to use colored console output (ignored if format_json=True)
        context: Additional context to include in all log messages
        force_reconfigure: Whether to force reconfiguration even if already configured

    Raises:
        ValueError: If invalid logging level is provided
        OSError: If log file cannot be created or accessed
    """
    global _current_config

    with _config_lock:
        # Check if already configured and not forcing reconfiguration
        if _current_config is not None and not force_reconfigure:
            return

        # Validate logging level
        numeric_level = getattr(logging, level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Invalid log level: {level}")

        # Use custom config or generate default
        if config_dict:
            config = config_dict.copy()
        else:
            config = get_default_config(
                level=level,
                format_json=format_json,
                log_file=log_file,
                enable_performance_logging=enable_performance_logging,
                enable_colors=enable_colors and not format_json,  # No colors with JSON
                context=context,
            )

        try:
            # Apply the configuration
            logging.config.dictConfig(config)
            _current_config = config

            # Log successful configuration
            logger = logging.getLogger("fqcn_converter.logging")
            logger.info(
                "Logging configured successfully",
                extra={
                    "level": level,
                    "format_json": format_json,
                    "log_file": log_file,
                    "performance_logging": enable_performance_logging,
                },
            )

        except Exception as e:
            # Fallback to basic configuration
            logging.basicConfig(
                level=numeric_level,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                stream=sys.stdout,
            )
            logger = logging.getLogger("fqcn_converter.logging")
            logger.error(f"Failed to configure logging, using basic configuration: {e}")
            raise


def get_logger(
    name: str,
    context: Optional[Dict[str, Any]] = None,
    performance_tracking: bool = False,
) -> logging.Logger:
    """
    Get a configured logger instance with optional context and performance tracking.

    Args:
        name: Logger name (typically __name__)
        context: Additional context to include in log messages
        performance_tracking: Whether to enable performance tracking for this logger

    Returns:
        Configured logger instance
    """
    global _logger_registry

    with _config_lock:
        # Check if logger already exists in registry
        if name in _logger_registry:
            return _logger_registry[name]

        # Create new logger
        logger = logging.getLogger(name)

        # Add context filter if context is provided
        if context:
            context_filter = ContextFilter(context)
            logger.addFilter(context_filter)

        # Add performance filter if requested
        if performance_tracking:
            performance_filter = PerformanceFilter()
            logger.addFilter(performance_filter)

        # Register logger
        _logger_registry[name] = logger

        return logger


def configure_logger_for_module(
    module_name: str,
    level: Optional[str] = None,
    handlers: Optional[list] = None,
    context: Optional[Dict[str, Any]] = None,
) -> logging.Logger:
    """
    Configure a specific logger for a module with custom settings.

    Args:
        module_name: Name of the module/logger
        level: Optional custom log level for this logger
        handlers: Optional list of handler names to use
        context: Additional context for this logger

    Returns:
        Configured logger instance
    """
    logger = get_logger(module_name, context=context)

    if level:
        numeric_level = getattr(logging, level.upper(), None)
        if isinstance(numeric_level, int):
            logger.setLevel(numeric_level)

    # Note: Handler configuration would typically be done through
    # the main logging configuration, but this allows for runtime changes

    return logger


def log_performance_metrics(
    logger: logging.Logger, operation: str, start_time: float, **kwargs: Any
) -> None:
    """
    Log performance metrics for an operation.

    Args:
        logger: Logger instance to use
        operation: Name of the operation being measured
        start_time: Start time from time.time()
        **kwargs: Additional metrics to log
    """
    end_time = time.time()
    duration = end_time - start_time

    metrics = {
        "operation": operation,
        "duration_seconds": duration,
        "start_time": start_time,
        "end_time": end_time,
        **kwargs,
    }

    logger.info(f"Performance metrics for {operation}", extra=metrics)


def create_file_logger(
    name: str,
    log_file: str,
    level: str = "INFO",
    format_json: bool = False,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> logging.Logger:
    """
    Create a dedicated file logger with rotation.

    Args:
        name: Logger name
        log_file: Path to log file
        level: Logging level
        format_json: Whether to use JSON formatting
        max_bytes: Maximum file size before rotation
        backup_count: Number of backup files to keep

    Returns:
        Configured file logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Create rotating file handler
    handler = create_rotating_file_handler(
        log_file=log_file, max_bytes=max_bytes, backup_count=backup_count
    )

    # Set formatter
    if format_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s"
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def get_current_config() -> Optional[Dict[str, Any]]:
    """Get the current logging configuration."""
    return _current_config


def reset_logging() -> None:
    """Reset logging configuration and clear registry."""
    global _current_config, _logger_registry

    with _config_lock:
        _current_config = None
        _logger_registry.clear()

        # Reset to basic configuration
        logging.basicConfig(force=True)


# Convenience function for common use cases
def setup_simple_logging(
    level: str = "INFO", log_to_file: bool = False, log_file: str = "fqcn_converter.log"
) -> logging.Logger:
    """
    Set up simple logging configuration for basic use cases.

    Args:
        level: Logging level
        log_to_file: Whether to log to file
        log_file: Log file name (only used if log_to_file=True)

    Returns:
        Main application logger
    """
    setup_logging(
        level=level, log_file=log_file if log_to_file else None, enable_colors=True
    )

    return get_logger("fqcn_converter")
