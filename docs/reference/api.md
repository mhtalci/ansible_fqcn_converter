# API Reference

This document provides comprehensive API reference documentation for the FQCN Converter Python package.

## Core Classes

### FQCNConverter

The main converter class for FQCN conversion operations.

#### Class Definition

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

##### `convert_file(file_path, dry_run=False)`

Convert a single Ansible file to FQCN format.

**Parameters:**
- `file_path` (str | Path): Path to the Ansible file to convert
- `dry_run` (bool): If True, perform conversion without writing changes

**Returns:**
- `ConversionResult`: Object containing conversion details

**Raises:**
- `FileAccessError`: If file cannot be read or written
- `ConversionError`: If conversion fails

**Example:**
```python
from fqcn_converter import FQCNConverter

converter = FQCNConverter()
result = converter.convert_file("playbook.yml")

if result.success:
    print(f"Converted {result.changes_made} modules")
else:
    print(f"Errors: {result.errors}")
```

##### `convert_content(content, file_type="yaml")`

Convert YAML content string to FQCN format.

**Parameters:**
- `content` (str): The content to convert
- `file_type` (str): Type of content ('yaml' supported)

**Returns:**
- `ConversionResult`: Object containing conversion details

**Example:**
```python
yaml_content = """
- name: Install package
  package:
    name: nginx
"""

result = converter.convert_content(yaml_content)
print(result.converted_content)
```

##### `convert_directory(directory_path, recursive=True, dry_run=False)`

Convert all Ansible files in a directory.

**Parameters:**
- `directory_path` (str | Path): Directory to process
- `recursive` (bool): Include subdirectories
- `dry_run` (bool): Preview changes without modification

**Returns:**
- `BatchResult`: Object containing batch processing results

### ValidationEngine

Validates FQCN usage in Ansible files.

#### Class Definition

```python
class ValidationEngine:
    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        strict_mode: bool = False
    ) -> None
```

#### Methods

##### `validate_file(file_path)`

Validate a single file for proper FQCN usage.

**Parameters:**
- `file_path` (str | Path): Path to file to validate

**Returns:**
- `ValidationResult`: Object containing validation details

**Example:**
```python
from fqcn_converter import ValidationEngine

validator = ValidationEngine()
result = validator.validate_file("playbook.yml")

if result.valid:
    print(f"✅ Valid (score: {result.score:.1%})")
else:
    for issue in result.issues:
        print(f"Line {issue.line_number}: {issue.message}")
```

##### `validate_content(content, file_path="<content>")`

Validate YAML content string.

**Parameters:**
- `content` (str): Content to validate
- `file_path` (str): Optional file path for reporting

**Returns:**
- `ValidationResult`: Object containing validation details

### BatchProcessor

Process multiple Ansible projects in parallel.

#### Class Definition

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

##### `discover_projects(root_dir, project_patterns=None, exclude_patterns=None)`

Discover Ansible projects in directory tree.

**Parameters:**
- `root_dir` (str | Path): Root directory to search
- `project_patterns` (List[str], optional): Patterns to identify projects
- `exclude_patterns` (List[str], optional): Patterns to exclude

**Returns:**
- `List[str]`: List of discovered project paths

##### `process_projects(projects, dry_run=False, continue_on_error=True)`

Process multiple projects with parallel execution.

**Parameters:**
- `projects` (List[str]): Project paths to process
- `dry_run` (bool): Preview changes without modification
- `continue_on_error` (bool): Continue on individual failures

**Returns:**
- `BatchResult`: Object containing batch processing results

## Data Classes

### ConversionResult

Result of a conversion operation.

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

Result of a validation operation.

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

A single validation issue.

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

Result of batch processing.

```python
@dataclass
class BatchResult:
    total_projects: int
    successful_conversions: int
    failed_conversions: int
    project_results: List[ConversionResult]
    execution_time: float
    summary_report: str
    total_files_processed: int
    total_modules_converted: int
    success_rate: float
    average_processing_time: float
```

## Configuration Management

### ConfigurationManager

Manages FQCN mappings and converter settings.

```python
class ConfigurationManager:
    def load_default_mappings(self) -> Dict[str, str]
    def load_custom_mappings(self, config_path: str) -> Dict[str, str]
    def merge_mappings(self, *mapping_dicts: Dict[str, str]) -> Dict[str, str]
    def validate_configuration(self, config_data: Dict[str, Any]) -> bool
```

## Exception Hierarchy

### Base Exception

```python
class FQCNConverterError(Exception):
    """Base exception for all converter errors."""
    
    def __init__(
        self, 
        message: str, 
        details: str = "", 
        suggestions: Optional[List[str]] = None,
        recovery_actions: Optional[List[str]] = None,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None
```

### Specific Exceptions

- `ConfigurationError`: Configuration loading or validation failures
- `ConversionError`: File conversion failures
- `ValidationError`: Validation process failures
- `BatchProcessingError`: Batch operation failures
- `YAMLParsingError`: YAML syntax errors
- `FileAccessError`: File system access errors
- `MappingError`: FQCN mapping issues

## Type Hints

The package provides comprehensive type hints for all public APIs:

```python
from typing import Dict, List, Optional, Union, Any, Callable
from pathlib import Path

# Common type aliases used throughout the package
FilePath = Union[str, Path]
MappingDict = Dict[str, str]
ProgressCallback = Callable[[int, int, str], None]
```

## Constants and Enums

### Severity Levels

```python
class Severity:
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
```

### File Types

```python
class FileType:
    YAML = "yaml"
    YML = "yml"
```

### Validation Modes

```python
class ValidationMode:
    MINIMAL = "minimal"
    STANDARD = "standard"
    STRICT = "strict"
```

## Utility Functions

### Error Recovery

```python
class ErrorRecovery:
    @staticmethod
    def can_continue_batch(error: FQCNConverterError) -> bool
    
    @staticmethod
    def get_fallback_config() -> Dict[str, str]
    
    @staticmethod
    def suggest_module_mapping(module_name: str) -> Optional[str]
```

## Usage Patterns

### Basic Conversion

```python
from fqcn_converter import FQCNConverter

# Initialize converter
converter = FQCNConverter()

# Convert single file
result = converter.convert_file("playbook.yml")
print(f"Success: {result.success}, Changes: {result.changes_made}")
```

### Custom Configuration

```python
# With custom mappings
custom_mappings = {
    "my_module": "my.collection.my_module"
}
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
    print(f"Found {len(result.issues)} issues:")
    for issue in result.issues:
        print(f"  {issue.severity}: {issue.message}")
```

### Batch Processing

```python
from fqcn_converter import BatchProcessor

def progress_callback(completed, total, current):
    print(f"Progress: {completed}/{total} - {current}")

processor = BatchProcessor(
    max_workers=4,
    progress_callback=progress_callback
)

projects = processor.discover_projects("/path/to/repos")
result = processor.process_projects(projects)

print(f"Success rate: {result.success_rate:.1%}")
```

### Error Handling

```python
from fqcn_converter import (
    FQCNConverter, 
    ConversionError, 
    FileAccessError
)

converter = FQCNConverter()

try:
    result = converter.convert_file("playbook.yml")
except FileAccessError as e:
    print(f"File access error: {e}")
    # Handle file permission issues
except ConversionError as e:
    print(f"Conversion error: {e}")
    # Handle conversion-specific issues
```

## Performance Considerations

### Memory Usage

- The converter processes files individually to minimize memory usage
- Large batch operations use streaming processing where possible
- Backup files are created incrementally to avoid memory spikes

### Parallel Processing

- BatchProcessor uses thread pools for I/O-bound operations
- Worker count should be tuned based on system resources
- Progress callbacks are called from worker threads

### Caching

- Configuration and mappings are cached after first load
- YAML parsing results are not cached to minimize memory usage
- Validation results can be cached for repeated validations

---

For more examples and usage patterns, see the [Python API Guide](../usage/api.md) and [Examples](../examples/) directory.