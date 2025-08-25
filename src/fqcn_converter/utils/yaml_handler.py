"""
YAML processing utilities for FQCN Converter.

This module provides safe YAML loading and processing functionality
with proper error handling and validation.
"""

from typing import Any, Dict, Union
from pathlib import Path
import yaml


def safe_load(content: str) -> Any:
    """Safely load YAML content."""
    return yaml.safe_load(content)


def safe_dump(data: Any, **kwargs) -> str:
    """Safely dump data to YAML string."""
    return yaml.safe_dump(data, **kwargs)


def load_yaml_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Load YAML file safely with error handling."""
    with open(file_path, "r", encoding="utf-8") as f:
        return safe_load(f.read())


def save_yaml_file(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
    """Save data to YAML file with proper formatting."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(safe_dump(data))
