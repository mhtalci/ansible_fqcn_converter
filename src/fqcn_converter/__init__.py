"""
FQCN Converter - A tool for converting Ansible playbooks to use Fully Qualified Collection Names (FQCN).

This package provides both CLI tools and a Python API for converting Ansible playbooks
from short module names to fully qualified collection names (FQCNs) with robust error
handling, configurable mappings, and comprehensive validation.
"""

# Import version information from dedicated module
from ._version import __version__, __version_tuple__

# Package metadata
__title__ = "fqcn-converter"
__description__ = "A tool for converting Ansible playbooks to use Fully Qualified Collection Names (FQCNs)"
__author__ = "mhtalci"
__author_email__ = "hello@mehmetalci.com"
__license__ = "MIT"
__url__ = "https://github.com/mhtalci/ansible_fqcn_converter"
__version_info__ = __version_tuple__

# Public API exports
from .core.converter import FQCNConverter, ConversionResult
from .core.validator import ValidationEngine, ValidationResult, ValidationIssue
from .core.batch import BatchProcessor, BatchResult
from .config.manager import ConfigurationManager
from .exceptions import (
    FQCNConverterError,
    ConfigurationError,
    ConversionError,
    ValidationError,
    BatchProcessingError,
    YAMLParsingError,
    FileAccessError,
)

__all__ = [
    # Version information
    "__version__",
    "__version_info__",
    "__title__",
    "__description__",
    "__author__",
    "__author_email__",
    "__license__",
    "__url__",
    # Core classes
    "FQCNConverter",
    "ConversionResult",
    "ValidationEngine",
    "ValidationResult",
    "ValidationIssue",
    "BatchProcessor",
    "BatchResult",
    "ConfigurationManager",
    # Exceptions
    "FQCNConverterError",
    "ConfigurationError",
    "ConversionError",
    "ValidationError",
    "BatchProcessingError",
    "YAMLParsingError",
    "FileAccessError",
]
