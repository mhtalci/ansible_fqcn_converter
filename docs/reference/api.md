# API Reference

Complete Python API reference for the FQCN Converter package.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![Test Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/mhtalci/ansible_fqcn_converter/actions)

## Package Overview

The `fqcn_converter` package provides a comprehensive API for converting Ansible playbooks to use Fully Qualified Collection Names (FQCN) with intelligent conflict resolution and validation.

### Main Modules

- **`fqcn_converter.core.converter`** - Core conversion functionality
- **`fqcn_converter.core.validator`** - Validation engine
- **`fqcn_converter.core.batch`** - Batch processing
- **`fqcn_converter.config.manager`** - Configuration management
- **`fqcn_converter.exceptions`** - Exception hierarchy

## Core Classes

### FQCNConverter

Main converter class for FQCN conversion operations.

```python
class FQCNConverter:
    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        custom_mappings: Optional[Dict[str, str]] = None,
        create_backups: bool = True,
        backup_suffix: str = ".fqcn_backup"
    ) -> None
```

#### Methods

**`convert_file(file_path, dry_run=False)`**

Convert a single Ansible file to FQCN format.

```python
converter = FQCNConverter()
result = converter.convert_file("playbook.yml")
if result.success:
    print(f"Converted {result.changes_made} modules")
```

**`convert_content(content, file_type="yaml")`**

Convert YAML content string to FQCN format.

```python
yaml_content = "- package: {name: nginx}"
result = converter.convert_content(yaml_content)
print(result.converted_content)
```

**`convert_directory(directory_path, recursive=True, dry_run=False)`**

Convert all Ansible files in a directory.

### ValidationEngine

Validates FQCN usage in Ansible files.

```python
class ValidationEngine:
    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        strict_mode: bool = False
    ) -> None
```

#### Methods

**`validate_file(file_path)`**

Validate a single file for proper FQCN usage.

```python
validator = ValidationEngine()
result = validator.validate_file("playbook.yml")
if not result.valid:
    for issue in result.issues:
        print(f"Line {issue.line_number}: {issue.message}")
```

**`validate_content(content, file_path="<content>")`**

Validate YAML content string.

### BatchProcessor

Process multiple Ansible projects in parallel.

```python
class BatchProcessor:
    def __init__(
        self,
        max_workers: int = 4,
        config_path: Optional[Union[str, Path]] = None,
        progress_callback: Optional[callable] = None
    ) -> None
```

#### Methods

**`discover_projects(root_dir, project_patterns=None, exclude_patterns=None)`**

Discover Ansible projects in directory tree.

**`process_projects(projects, dry_run=False, continue_on_error=True)`**

Process multiple projects with parallel execution.

## Data Classes

### ConversionResult

```python
@dataclass
class ConversionResult:
    success: bool
    file_path: str
    changes_made: int
    errors: List[str]
    warnings: List[str]
    original_content: Optional[str]
    converted_content: Optional[str]
    processing_time: float
    backup_path: Optional[str]
```

### ValidationResult

```python
@dataclass
class ValidationResult:
    valid: bool
    file_path: str
    issues: List[ValidationIssue]
    score: float  # 0.0 to 1.0
    total_modules: int
    fqcn_modules: int
    short_modules: int
    processing_time: float
```

### ValidationIssue

```python
@dataclass
class ValidationIssue:
    line_number: int
    column: int
    severity: str  # 'error', 'warning', 'info'
    message: str
    suggestion: str
    module_name: str
    expected_fqcn: str
```

### BatchResult

```python
@dataclass
class BatchResult:
    total_projects: int
    successful_conversions: int
    failed_conversions: int
    project_results: List[ConversionResult]
    execution_time: float
    total_files_processed: int
    total_modules_converted: int
    success_rate: float
```

## Exception Hierarchy

### Base Exception

```python
class FQCNConverterError(Exception):
    """Base exception for all converter errors."""
```

### Specific Exceptions

- `ConfigurationError`: Configuration loading or validation failures
- `ConversionError`: File conversion failures
- `ValidationError`: Validation process failures
- `BatchProcessingError`: Batch operation failures
- `YAMLParsingError`: YAML syntax errors
- `FileAccessError`: File system access errors

## Usage Examples

### Basic Conversion

```python
from fqcn_converter import FQCNConverter

converter = FQCNConverter()
result = converter.convert_file("playbook.yml")
print(f"Success: {result.success}, Changes: {result.changes_made}")
```

### Custom Configuration

```python
# With custom mappings
custom_mappings = {"my_module": "my.collection.my_module"}
converter = FQCNConverter(custom_mappings=custom_mappings)

# With configuration file
converter = FQCNConverter(config_path="custom_config.yml")
```

### Validation Workflow

```python
from fqcn_converter import ValidationEngine

validator = ValidationEngine(strict_mode=True)
result = validator.validate_file("playbook.yml")

if not result.valid:
    for issue in result.issues:
        print(f"{issue.severity}: {issue.message}")
```

### Batch Processing

```python
from fqcn_converter import BatchProcessor

def progress_callback(completed, total, current):
    print(f"Progress: {completed}/{total} - {current}")

processor = BatchProcessor(max_workers=4, progress_callback=progress_callback)
projects = processor.discover_projects("/path/to/repos")
result = processor.process_projects(projects)
```

### Error Handling

```python
from fqcn_converter import FQCNConverter, ConversionError

converter = FQCNConverter()
try:
    result = converter.convert_file("playbook.yml")
except ConversionError as e:
    print(f"Conversion error: {e}")
```

## Type Hints

```python
from typing import Dict, List, Optional, Union, Callable
from pathlib import Path

FilePath = Union[str, Path]
MappingDict = Dict[str, str]
ProgressCallback = Callable[[int, int, str], None]
```

---

For usage examples and tutorials, see the [Python API Guide](../usage/api.md).