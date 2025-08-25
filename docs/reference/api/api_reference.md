# FQCN Converter API Reference

Complete API reference for the Ansible FQCN Converter library

**Version:** 0.1.0

## Table of Contents

- [Classes](#classes)
- [Data Classes](#data-classes)
- [Usage Examples](#usage-examples)
- [Type Hints Reference](#type-hints-reference)

## Classes

### FQCNConverter

Core conversion engine

```
Main FQCN conversion engine with configurable mappings and robust error handling.

The FQCNConverter class provides the core functionality for converting Ansible
playbooks and task files from short module names to Fully Qualified Collection
Names (FQCNs). It supports custom configuration, backup creation, and comprehensive
error handling.

Features:
    - Intelligent module detection and conversion
    - Configurable FQCN mappings
    - Backup file creation for safety
    - Dry-run mode for previewing changes
    - Comprehensive error reporting
    - Support for various Ansible file formats

Example:
    >>> converter = FQCNConverter()
    >>> result = converter.convert_file("playbook.yml")
    >>> if result.success:
    ...     print(f"Successfully converted {result.changes_made} modules")
    
    >>> # Using custom mappings
    >>> custom_mappings = {"my_module": "my.collection.my_module"}
    >>> converter = FQCNConverter(custom_mappings=custom_mappings)
    
    >>> # Dry run to preview changes
    >>> result = converter.convert_file("playbook.yml", dry_run=True)
    >>> print(f"Would convert {result.changes_made} modules")
```

#### Methods

##### `__init__(self, config_path: Union[str, pathlib._local.Path, NoneType] = None, custom_mappings: Optional[Dict[str, str]] = None, create_backups: bool = True, backup_suffix: str = '.fqcn_backup') -> None`

Initialize converter with configuration and settings.

The converter loads default FQCN mappings and optionally merges them with
custom configuration and mappings. It supports various configuration sources
and provides fallback mechanisms for robust operation.

Args:
    config_path: Path to custom configuration file (YAML format).
                If provided, mappings from this file will be merged with defaults.
    custom_mappings: Dictionary of custom module mappings in the format
                   {"short_name": "namespace.collection.module_name"}.
                   These take precedence over config file mappings.
    create_backups: Whether to create backup files before conversion.
                  Defaults to True for safety.
    backup_suffix: Suffix to append to backup files. Defaults to ".fqcn_backup".
    
Raises:
    ConfigurationError: If configuration loading fails or contains invalid data.
                      The converter will attempt to use default mappings as fallback.

Example:
    >>> # Basic initialization with defaults
    >>> converter = FQCNConverter()
    
    >>> # With custom configuration file
    >>> converter = FQCNConverter(config_path="my_config.yml")
    
    >>> # With custom mappings
    >>> mappings = {"my_module": "my.collection.my_module"}
    >>> converter = FQCNConverter(custom_mappings=mappings)
    
    >>> # Disable backups for testing
    >>> converter = FQCNConverter(create_backups=False)

**Parameters:**

- `config_path` (typing.Union[str, pathlib._local.Path, NoneType]) = None: Path to custom configuration file (YAML format).
- `custom_mappings` (typing.Optional[typing.Dict[str, str]]) = None: Dictionary of custom module mappings in the format
- `create_backups` (<class 'bool'>) = True: Whether to create backup files before conversion.
- `backup_suffix` (<class 'str'>) = .fqcn_backup: Suffix to append to backup files. Defaults to ".fqcn_backup".

**Raises:**

- `ConfigurationError`: If configuration loading fails or contains invalid data.

##### `convert_content(self, content: str, file_type: str = 'yaml') -> fqcn_converter.core.converter.ConversionResult`

Convert Ansible content string to FQCN format.

Args:
    content: The content to convert
    file_type: Type of content ('yaml' supported)
    
Returns:
    ConversionResult with conversion details

**Parameters:**

- `content` (<class 'str'>): The content to convert
- `file_type` (<class 'str'>) = yaml: Type of content ('yaml' supported)

**Returns:** ConversionResult with conversion details

##### `convert_file(self, file_path: Union[str, pathlib._local.Path], dry_run: bool = False) -> fqcn_converter.core.converter.ConversionResult`

Convert a single Ansible file to FQCN format.

Args:
    file_path: Path to the Ansible file to convert
    dry_run: If True, perform conversion without writing changes
    
Returns:
    ConversionResult with conversion details
    
Raises:
    FileAccessError: If file cannot be read or written
    ConversionError: If conversion fails

**Parameters:**

- `file_path` (typing.Union[str, pathlib._local.Path]): Path to the Ansible file to convert
- `dry_run` (<class 'bool'>) = False: If True, perform conversion without writing changes

**Returns:** ConversionResult with conversion details

**Raises:**

- `FileAccessError`: If file cannot be read or written
- `ConversionError`: If conversion fails

---

### ValidationEngine

Validation and compliance checking

```
Handles validation of FQCN conversions with comprehensive validation logic.

The ValidationEngine analyzes Ansible files to ensure proper FQCN usage,
identifies conversion issues, and provides detailed compliance scoring.
It supports various validation modes and provides actionable feedback.

Features:
    - Comprehensive FQCN compliance checking
    - Detailed issue reporting with line numbers
    - Compliance scoring (0.0 to 1.0)
    - Support for multiple Ansible file formats
    - Configurable validation strictness
    - Performance metrics and timing

Example:
    >>> validator = ValidationEngine()
    >>> result = validator.validate_file("playbook.yml")
    >>> 
    >>> if result.valid:
    ...     print(f"✅ File is compliant (score: {result.score:.1%})")
    ... else:
    ...     print(f"❌ Found {len(result.issues)} issues")
    ...     for issue in result.issues:
    ...         print(f"  Line {issue.line_number}: {issue.message}")
    
    >>> # Validate content directly
    >>> yaml_content = "- copy: {src: file, dest: /tmp/file}"
    >>> result = validator.validate_content(yaml_content)
```

#### Methods

##### `__init__(self) -> None`

Initialize validation engine.

**Parameters:**


##### `validate_content(self, content: str, file_path: str = '<content>') -> fqcn_converter.core.validator.ValidationResult`

Validate content string for FQCN compliance.

Args:
    content: The content to validate
    file_path: Optional file path for reporting
    
Returns:
    ValidationResult with validation details

**Parameters:**

- `content` (<class 'str'>): The content to validate
- `file_path` (<class 'str'>) = <content>: Optional file path for reporting

**Returns:** ValidationResult with validation details

##### `validate_conversion(self, file_path: Union[str, pathlib._local.Path]) -> fqcn_converter.core.validator.ValidationResult`

Validate that a file has been properly converted.

Args:
    file_path: Path to the file to validate
    
Returns:
    ValidationResult with validation details
    
Raises:
    FileAccessError: If file cannot be read
    ValidationError: If validation process fails

**Parameters:**

- `file_path` (typing.Union[str, pathlib._local.Path]): Path to the file to validate

**Returns:** ValidationResult with validation details

**Raises:**

- `FileAccessError`: If file cannot be read
- `ValidationError`: If validation process fails

---

### BatchProcessor

Batch processing operations

```
Handles batch conversion of multiple Ansible projects with parallel processing.

The BatchProcessor provides efficient processing of multiple Ansible projects
using parallel workers, comprehensive error handling, and detailed reporting.
It automatically discovers projects and handles failures gracefully.

Features:
    - Parallel processing with configurable worker count
    - Automatic project discovery
    - Comprehensive error handling and recovery
    - Detailed progress reporting
    - Performance metrics and timing
    - Graceful handling of individual project failures

Example:
    >>> processor = BatchProcessor(max_workers=4)
    >>> projects = processor.discover_projects("/path/to/ansible/repos")
    >>> result = processor.process_projects(projects)
    >>> 
    >>> print(f"Processed {result.total_projects} projects")
    >>> print(f"Success rate: {result.success_rate:.1%}")
    >>> 
    >>> # With progress callback
    >>> def progress_callback(completed, total, current):
    ...     print(f"Progress: {completed}/{total} - {current}")
    >>> 
    >>> processor = BatchProcessor(
    ...     max_workers=4,
    ...     progress_callback=progress_callback
    ... )
```

#### Methods

##### `__init__(self, max_workers: int = 4, config_path: Union[str, pathlib._local.Path, NoneType] = None, progress_callback: Optional[<built-in function callable>] = None) -> None`

Initialize batch processor with worker configuration.

Args:
    max_workers: Maximum number of parallel workers to use.
                Defaults to 4. Set to 1 for sequential processing.
    config_path: Optional path to configuration file for conversions.
    progress_callback: Optional callback function for progress updates.
                     Called with (completed_count, total_count, current_project).

Example:
    >>> # Basic initialization
    >>> processor = BatchProcessor()
    
    >>> # With custom worker count
    >>> processor = BatchProcessor(max_workers=8)
    
    >>> # With progress tracking
    >>> def track_progress(done, total, current):
    ...     print(f"{done}/{total}: {current}")
    >>> processor = BatchProcessor(progress_callback=track_progress)

**Parameters:**

- `max_workers` (<class 'int'>) = 4: Maximum number of parallel workers to use.
- `config_path` (typing.Union[str, pathlib._local.Path, NoneType]) = None: Optional path to configuration file for conversions.
- `progress_callback` (typing.Optional[<built-in function callable>]) = None: Optional callback function for progress updates.

##### `discover_projects(self, root_dir: Union[str, pathlib._local.Path], project_patterns: Optional[List[str]] = None, exclude_patterns: Optional[List[str]] = None) -> List[str]`

Discover Ansible projects in directory tree.

Recursively searches for Ansible projects based on common indicators
such as playbook files, inventory files, and directory structure.

Args:
    root_dir: Root directory to search for projects
    project_patterns: Optional list of patterns to identify projects.
                    Defaults to common Ansible project indicators.
    exclude_patterns: Optional list of patterns to exclude directories.
                    Defaults to common non-project directories.

Returns:
    List of discovered project directory paths

Example:
    >>> processor = BatchProcessor()
    >>> projects = processor.discover_projects("/path/to/repos")
    >>> print(f"Found {len(projects)} Ansible projects")
    
    >>> # With custom patterns
    >>> projects = processor.discover_projects(
    ...     "/path/to/repos",
    ...     project_patterns=["**/playbooks", "**/roles"],
    ...     exclude_patterns=["**/archive/**", "**/.git/**"]
    ... )

**Parameters:**

- `root_dir` (typing.Union[str, pathlib._local.Path]): Root directory to search for projects
- `project_patterns` (typing.Optional[typing.List[str]]) = None: Optional list of patterns to identify projects.
- `exclude_patterns` (typing.Optional[typing.List[str]]) = None: Optional list of patterns to exclude directories.

**Returns:** List of discovered project directory paths

##### `process_projects(self, projects: List[str], dry_run: bool = False, continue_on_error: bool = True) -> fqcn_converter.core.batch.BatchResult`

Process multiple projects with parallel execution.

Converts multiple Ansible projects using parallel workers with
comprehensive error handling and detailed reporting.

Args:
    projects: List of project directory paths to process
    dry_run: If True, perform conversion preview without making changes
    continue_on_error: If True, continue processing other projects
                     when individual projects fail

Returns:
    BatchResult containing processing statistics and individual results

Raises:
    BatchProcessingError: If batch processing fails critically

Example:
    >>> processor = BatchProcessor(max_workers=4)
    >>> projects = ["/path/to/project1", "/path/to/project2"]
    >>> 
    >>> # Dry run to preview changes
    >>> result = processor.process_projects(projects, dry_run=True)
    >>> print(f"Would convert {result.total_modules_converted} modules")
    >>> 
    >>> # Actual processing
    >>> result = processor.process_projects(projects)
    >>> if result.success_rate > 0.8:
    ...     print("Batch processing successful!")

**Parameters:**

- `projects` (typing.List[str]): List of project directory paths to process
- `dry_run` (<class 'bool'>) = False: If True, perform conversion preview without making changes
- `continue_on_error` (<class 'bool'>) = True: If True, continue processing other projects

**Returns:** BatchResult containing processing statistics and individual results

**Raises:**

- `BatchProcessingError`: If batch processing fails critically

---

### ConfigurationManager

Configuration management

```
Manages FQCN mappings and converter settings.
```

#### Methods

##### `__init__(self) -> None`

Initialize configuration manager.

**Parameters:**


##### `load_custom_mappings(self, config_path: Union[str, pathlib._local.Path]) -> Dict[str, str]`

Load custom mappings from user-provided file.

Args:
    config_path: Path to custom configuration file
    
Returns:
    Dictionary mapping short module names to FQCNs
    
Raises:
    ConfigurationError: If custom configuration cannot be loaded

**Parameters:**

- `config_path` (typing.Union[str, pathlib._local.Path]): Path to custom configuration file

**Returns:** Dictionary mapping short module names to FQCNs

**Raises:**

- `ConfigurationError`: If custom configuration cannot be loaded

##### `load_default_mappings(self) -> Dict[str, str]`

Load default FQCN mappings from bundled configuration.

Returns:
    Dictionary mapping short module names to FQCNs
    
Raises:
    ConfigurationError: If default configuration cannot be loaded

**Parameters:**


**Returns:** Dictionary mapping short module names to FQCNs

**Raises:**

- `ConfigurationError`: If default configuration cannot be loaded

##### `load_settings(self, config_path: Union[str, pathlib._local.Path, NoneType] = None) -> fqcn_converter.config.manager.ConversionSettings`

Load conversion settings from configuration.

Args:
    config_path: Optional path to custom configuration file
    
Returns:
    ConversionSettings object with loaded settings

**Parameters:**

- `config_path` (typing.Union[str, pathlib._local.Path, NoneType]) = None: Optional path to custom configuration file

**Returns:** ConversionSettings object with loaded settings

##### `merge_mappings(self, *mapping_dicts: Dict[str, str]) -> Dict[str, str]`

Merge multiple mapping dictionaries with precedence rules.

Args:
    *mapping_dicts: Variable number of mapping dictionaries
    
Returns:
    Merged dictionary with later dictionaries taking precedence
    
Note:
    Later dictionaries in the argument list take precedence over earlier ones.
    This allows for: base_mappings -> custom_mappings -> user_overrides

**Parameters:**

- `mapping_dicts` (typing.Dict[str, str])

**Returns:** Merged dictionary with later dictionaries taking precedence Note: Later dictionaries in the argument list take precedence over earlier ones. This allows for: base_mappings -> custom_mappings -> user_overrides

##### `validate_configuration(self, config_data: Dict[str, Any]) -> bool`

Validate configuration data against schema.

Args:
    config_data: Configuration data to validate
    
Returns:
    True if valid, False otherwise

**Parameters:**

- `config_data` (typing.Dict[str, typing.Any]): Configuration data to validate

**Returns:** True if valid, False otherwise

---

## Data Classes

### ConversionResult

Conversion operation results

```
Result of a single file conversion operation.

This class encapsulates all information about a conversion operation,
including success status, changes made, and any errors or warnings
encountered during the process.

Attributes:
    success: Whether the conversion operation completed successfully
    file_path: Path to the file that was converted (or attempted)
    changes_made: Number of module conversions performed
    errors: List of error messages encountered during conversion
    warnings: List of warning messages from the conversion process
    original_content: Original file content before conversion (optional)
    converted_content: File content after conversion (optional)
    processing_time: Time taken for the conversion operation in seconds
    backup_path: Path to backup file if one was created (optional)

Example:
    >>> result = converter.convert_file("playbook.yml")
    >>> if result.success:
    ...     print(f"Converted {result.changes_made} modules")
    ... else:
    ...     print(f"Conversion failed: {result.errors}")
```

#### Fields

- `success` (<class 'bool'>): Whether the conversion operation completed successfully
- `file_path` (<class 'str'>): Path to the file that was converted (or attempted)
- `changes_made` (<class 'int'>): Number of module conversions performed
- `errors` (typing.List[str]): List of error messages encountered during conversion
- `warnings` (typing.List[str]): List of warning messages from the conversion process
- `original_content` (typing.Optional[str]): Original file content before conversion (optional)
- `converted_content` (typing.Optional[str]): File content after conversion (optional)
- `processing_time` (<class 'float'>): Time taken for the conversion operation in seconds
- `backup_path` (typing.Optional[str]): Path to backup file if one was created (optional)

---

### ValidationResult

Validation operation results

```
Result of validation operation.

This class contains comprehensive information about the validation of an
Ansible file, including compliance score, issues found, and statistics.

Attributes:
    valid: Whether the file passes validation (no critical errors)
    file_path: Path to the validated file
    issues: List of validation issues found in the file
    score: FQCN completeness score from 0.0 (no compliance) to 1.0 (fully compliant)
    total_modules: Total number of modules found in the file
    fqcn_modules: Number of modules already using FQCN format
    short_modules: Number of modules using short names
    processing_time: Time taken for validation in seconds

Example:
    >>> result = validator.validate_file("playbook.yml")
    >>> print(f"Validation score: {result.score:.1%}")
    >>> if not result.valid:
    ...     for issue in result.issues:
    ...         print(f"Line {issue.line_number}: {issue.message}")
```

#### Fields

- `valid` (<class 'bool'>): Whether the file passes validation (no critical errors)
- `file_path` (<class 'str'>): Path to the validated file
- `issues` (typing.List[fqcn_converter.core.validator.ValidationIssue]): List of validation issues found in the file
- `score` (<class 'float'>): FQCN completeness score from 0.0 (no compliance) to 1.0 (fully compliant)
- `total_modules` (<class 'int'>): Total number of modules found in the file
- `fqcn_modules` (<class 'int'>): Number of modules already using FQCN format
- `short_modules` (<class 'int'>): Number of modules using short names
- `processing_time` (<class 'float'>): Time taken for validation in seconds

---

### ValidationIssue

Individual validation issues

```
Represents a validation issue found in a file.

This class encapsulates information about a specific validation problem,
including its location, severity, and suggested remediation.

Attributes:
    line_number: Line number where the issue occurs (1-based)
    column: Column number where the issue occurs (1-based)
    severity: Severity level of the issue ('error', 'warning', 'info')
    message: Human-readable description of the issue
    suggestion: Suggested fix or remediation for the issue
    module_name: Name of the module related to this issue (optional)
    expected_fqcn: Expected FQCN for the module (optional)

Example:
    >>> issue = ValidationIssue(
    ...     line_number=15,
    ...     column=5,
    ...     severity='error',
    ...     message="Short module name 'copy' should use FQCN",
    ...     suggestion="Replace 'copy' with 'ansible.builtin.copy'"
    ... )
```

#### Fields

- `line_number` (<class 'int'>): Line number where the issue occurs (1-based)
- `column` (<class 'int'>): Column number where the issue occurs (1-based)
- `severity` (<class 'str'>): Severity level of the issue ('error', 'warning', 'info')
- `message` (<class 'str'>): Human-readable description of the issue
- `suggestion` (<class 'str'>): Suggested fix or remediation for the issue
- `module_name` (<class 'str'>): Name of the module related to this issue (optional)
- `expected_fqcn` (<class 'str'>): Expected FQCN for the module (optional)

---

### BatchResult

Batch processing results

```
Result of batch processing operation.

This class encapsulates the results of processing multiple Ansible projects
in a batch operation, including success/failure statistics, individual results,
and performance metrics.

Attributes:
    total_projects: Total number of projects processed
    successful_conversions: Number of projects converted successfully
    failed_conversions: Number of projects that failed conversion
    project_results: List of individual ConversionResult objects for each project
    execution_time: Total time taken for batch processing in seconds
    summary_report: Human-readable summary of the batch operation
    total_files_processed: Total number of files processed across all projects
    total_modules_converted: Total number of modules converted across all projects
    success_rate: Success rate as a percentage (0.0 to 1.0)
    average_processing_time: Average processing time per project in seconds

Example:
    >>> result = processor.process_projects(project_paths)
    >>> print(f"Processed {result.total_projects} projects")
    >>> print(f"Success rate: {result.success_rate:.1%}")
    >>> print(f"Total modules converted: {result.total_modules_converted}")
```

#### Fields

- `total_projects` (<class 'int'>): Total number of projects processed
- `successful_conversions` (<class 'int'>): Number of projects converted successfully
- `failed_conversions` (<class 'int'>): Number of projects that failed conversion
- `project_results` (typing.List[fqcn_converter.core.converter.ConversionResult]): List of individual ConversionResult objects for each project
- `execution_time` (<class 'float'>): Total time taken for batch processing in seconds
- `summary_report` (<class 'str'>): Human-readable summary of the batch operation
- `total_files_processed` (<class 'int'>): Total number of files processed across all projects
- `total_modules_converted` (<class 'int'>): Total number of modules converted across all projects
- `success_rate` (<class 'float'>): Success rate as a percentage (0.0 to 1.0)
- `average_processing_time` (<class 'float'>): Average processing time per project in seconds

---

## Usage Examples

### Basic Conversion

Convert a single Ansible file to FQCN format

```python
from fqcn_converter import FQCNConverter

# Initialize converter with default settings
converter = FQCNConverter()

# Convert a playbook file
result = converter.convert_file("playbook.yml")

if result.success:
    print(f"✅ Successfully converted {result.changes_made} modules")
else:
    print(f"❌ Conversion failed: {result.errors}")
```

### Custom Configuration

Use custom FQCN mappings and configuration

```python
from fqcn_converter import FQCNConverter

# Custom mappings for specific modules
custom_mappings = {
    "my_module": "my.collection.my_module",
    "custom_action": "company.internal.custom_action"
}

# Initialize with custom configuration
converter = FQCNConverter(
    config_path="custom_config.yml",
    custom_mappings=custom_mappings,
    create_backups=True
)

# Convert with dry run to preview changes
result = converter.convert_file("playbook.yml", dry_run=True)
print(f"Would convert {result.changes_made} modules")
```

### Validation and Compliance

Validate FQCN compliance and get detailed reports

```python
from fqcn_converter import ValidationEngine

# Initialize validation engine
validator = ValidationEngine()

# Validate a file
result = validator.validate_conversion("playbook.yml")

print(f"Validation score: {result.score:.1%}")
print(f"Total modules: {result.total_modules}")
print(f"FQCN modules: {result.fqcn_modules}")

if not result.valid:
    print("Issues found:")
    for issue in result.issues:
        print(f"  Line {issue.line_number}: {issue.message}")
        if issue.suggestion:
            print(f"    💡 {issue.suggestion}")
```

### Batch Processing

Process multiple Ansible projects in parallel

```python
from fqcn_converter import BatchProcessor

# Initialize batch processor
processor = BatchProcessor(max_workers=4)

# Discover Ansible projects
projects = processor.discover_projects("/path/to/ansible/projects")
print(f"Found {len(projects)} Ansible projects")

# Process all projects
result = processor.process_projects(projects, dry_run=False)

print(f"Processed {result.total_projects} projects")
print(f"Successful: {result.successful_conversions}")
print(f"Failed: {result.failed_conversions}")
print(f"Execution time: {result.execution_time:.2f}s")
```

### Content Processing

Process Ansible content directly from strings

```python
from fqcn_converter import FQCNConverter

converter = FQCNConverter()

# YAML content with short module names
yaml_content = """
- name: Copy file
  copy:
    src: /tmp/source
    dest: /tmp/dest

- name: Install package
  yum:
    name: httpd
    state: present
"""

# Convert content directly
result = converter.convert_content(yaml_content)

if result.success:
    print("Converted content:")
    print(result.converted_content)
else:
    print(f"Conversion failed: {result.errors}")
```

## Type Hints Reference

### Common Types

- `Union[str, Path]`: String or Path object
- `Optional[str]`: String or None
- `Dict[str, str]`: Dictionary with string keys and values
- `List[str]`: List of strings
- `List[ValidationIssue]`: List of validation issue objects

### Return Types

- `ConversionResult`: Object containing conversion operation results
- `ValidationResult`: Object containing validation results and compliance score
- `BatchResult`: Object containing batch processing results and statistics
