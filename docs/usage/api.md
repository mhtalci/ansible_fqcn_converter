# Python API Guide

This guide covers how to use the FQCN Converter as a Python library in your applications.

## Quick Start

### Basic Usage

```python
from fqcn_converter import FQCNConverter

# Initialize converter
converter = FQCNConverter()

# Convert a file
result = converter.convert_file("playbook.yml")
if result.success:
    print(f"✅ Converted {result.changes_made} modules")
else:
    print(f"❌ Conversion failed: {result.errors}")
```

### Convert Content Directly

```python
from fqcn_converter import FQCNConverter

converter = FQCNConverter()

# YAML content as string
content = """
- name: Install nginx
  package:
    name: nginx
    state: present
"""

# Convert content
result = converter.convert_content(content)
if result.success:
    print(result.converted_content)
```

## Core Classes

### FQCNConverter

Main converter class for FQCN conversion operations with intelligent conflict resolution.

```python
from fqcn_converter import FQCNConverter

# Initialize with default settings
converter = FQCNConverter()

# Initialize with custom configuration
converter = FQCNConverter(config_path="custom_config.yml")

# Initialize with specific options
converter = FQCNConverter(
    create_backups=True,
    strict_mode=False,
    dry_run=False
)
```

#### Constructor Parameters

- `config_path` (Optional[str]): Path to custom configuration file
- `create_backups` (bool): Whether to create backup files (default: True)
- `strict_mode` (bool): Enable strict validation mode (default: False)
- `dry_run` (bool): Preview mode without making changes (default: False)

#### Key Methods

**File Conversion**
```python
# Convert single file
result = converter.convert_file("playbook.yml")

# Dry run (preview only)
result = converter.convert_file("playbook.yml", dry_run=True)

# Convert directory
result = converter.convert_directory("/path/to/project")
```

**Content Conversion**
```python
yaml_content = "- package: {name: nginx}"
result = converter.convert_content(yaml_content)
print(result.converted_content)
```

### ValidationEngine

Comprehensive validation engine for FQCN usage in Ansible files.

```python
from fqcn_converter import ValidationEngine

# Initialize validator
validator = ValidationEngine()

# Validate single file
result = validator.validate_file("playbook.yml")

if result.valid:
    print(f"✅ Valid (score: {result.score:.1%})")
    print(f"FQCN modules: {result.fqcn_modules}/{result.total_modules}")
else:
    print(f"❌ Validation failed with {len(result.issues)} issues:")
    for issue in result.issues:
        print(f"  Line {issue.line}: {issue.message} [{issue.severity}]")
        if issue.suggested_fix:
            print(f"    Suggestion: {issue.suggested_fix}")

# Validate directory
results = validator.validate_directory("/path/to/project")
for file_path, result in results.items():
    print(f"{file_path}: {'✅' if result.valid else '❌'}")
```

#### Key Methods

- `validate_file(file_path)`: Validate single file
- `validate_directory(directory_path)`: Validate all files in directory
- `validate_content(yaml_content)`: Validate YAML content string

### BatchProcessor

High-performance batch processing for multiple Ansible projects with parallel execution.

```python
from fqcn_converter import BatchProcessor

def progress_callback(completed, total, current_project):
    percentage = (completed / total) * 100
    print(f"Progress: {percentage:.1f}% - Processing: {current_project}")

# Initialize batch processor
processor = BatchProcessor(
    max_workers=4,
    progress_callback=progress_callback,
    dry_run=False
)

# Process multiple projects
projects = ["/path/to/project1", "/path/to/project2", "/path/to/project3"]
batch_result = processor.process_projects(projects)

# Check results
print(f"Processed: {batch_result.total_projects}")
print(f"Successful: {batch_result.successful_projects}")
print(f"Failed: {batch_result.failed_projects}")

# Access individual results
for project_path, result in batch_result.project_results.items():
    if result.success:
        print(f"✅ {project_path}: {result.changes_made} modules converted")
    else:
        print(f"❌ {project_path}: {', '.join(result.errors)}")
```

#### Constructor Parameters

- `max_workers` (int): Number of parallel workers (default: 4)
- `progress_callback` (Optional[Callable]): Progress tracking function
- `dry_run` (bool): Preview mode without making changes (default: False)
- `config_path` (Optional[str]): Path to configuration file

## Result Objects

### ConversionResult

Comprehensive result object returned by conversion operations.

```python
result = converter.convert_file("playbook.yml")

# Key attributes
result.success          # bool: Whether conversion succeeded
result.changes_made     # int: Number of modules converted
result.errors          # List[str]: Error messages
result.warnings        # List[str]: Warning messages
result.backup_path     # Optional[str]: Path to backup file
result.processing_time # float: Time taken for conversion (seconds)
result.file_path       # str: Path to the processed file
result.original_content # str: Original file content (if requested)
result.converted_content # str: Converted content

# Usage examples
if result.success:
    print(f"✅ Successfully converted {result.changes_made} modules in {result.processing_time:.2f}s")
    if result.backup_path:
        print(f"📁 Backup created: {result.backup_path}")
else:
    print(f"❌ Conversion failed:")
    for error in result.errors:
        print(f"  • {error}")
```

### ValidationResult

Detailed validation result with compliance scoring and issue tracking.

```python
result = validator.validate_file("playbook.yml")

# Key attributes
result.valid           # bool: Whether file is valid
result.score          # float: Compliance score (0.0-1.0)
result.issues         # List[ValidationIssue]: Validation issues
result.total_modules  # int: Total modules found
result.fqcn_modules   # int: Modules using FQCN
result.file_path      # str: Path to validated file
result.processing_time # float: Validation time (seconds)

# Usage examples
print(f"Validation Score: {result.score:.1%}")
print(f"FQCN Usage: {result.fqcn_modules}/{result.total_modules} modules")

if not result.valid:
    print(f"Issues found ({len(result.issues)}):")
    for issue in result.issues:
        print(f"  Line {issue.line}: {issue.message} [{issue.severity}]")
```

### ValidationIssue

Individual validation issue with detailed information and suggestions.

```python
for issue in result.issues:
    print(f"Line {issue.line}: {issue.message}")
    print(f"Severity: {issue.severity}")  # 'error', 'warning', 'info'
    print(f"Module: {issue.module_name}")
    print(f"Expected FQCN: {issue.expected_fqcn}")
    if issue.suggested_fix:
        print(f"Suggestion: {issue.suggested_fix}")
    print(f"Context: {issue.context}")
```

### BatchResult

Comprehensive batch processing result with per-project details.

```python
batch_result = processor.process_projects(project_paths)

# Key attributes
batch_result.total_projects      # int: Total projects processed
batch_result.successful_projects # int: Successfully processed projects
batch_result.failed_projects    # int: Failed projects
batch_result.total_changes      # int: Total modules converted across all projects
batch_result.processing_time    # float: Total processing time
batch_result.project_results    # Dict[str, ConversionResult]: Per-project results

# Usage examples
success_rate = (batch_result.successful_projects / batch_result.total_projects) * 100
print(f"Batch Processing Complete:")
print(f"  Success Rate: {success_rate:.1f}%")
print(f"  Total Changes: {batch_result.total_changes}")
print(f"  Processing Time: {batch_result.processing_time:.2f}s")

# Access individual project results
for project_path, result in batch_result.project_results.items():
    status = "✅" if result.success else "❌"
    print(f"{status} {project_path}: {result.changes_made} changes")
```

## Common Patterns

### Custom Configuration

```python
# Custom mappings
custom_mappings = {
    "my_module": "my.collection.my_module",
    "legacy_module": "community.general.legacy_module"
}
converter = FQCNConverter(custom_mappings=custom_mappings)

# Configuration file
converter = FQCNConverter(config_path="custom_config.yml")
```

### Error Handling

```python
from fqcn_converter import FQCNConverter, ConversionError

converter = FQCNConverter()

try:
    result = converter.convert_file("playbook.yml")
    if not result.success:
        for error in result.errors:
            print(f"Error: {error}")
except ConversionError as e:
    print(f"Conversion failed: {e}")
```

### Progress Tracking

```python
def progress_callback(completed, total, current_item):
    percentage = (completed / total) * 100
    print(f"Progress: {percentage:.1f}% - {current_item}")

processor = BatchProcessor(
    max_workers=4,
    progress_callback=progress_callback
)
```

## Integration Examples

### Basic Workflow

```python
import tempfile
import os
from fqcn_converter import FQCNConverter

def convert_and_validate():
    """Complete conversion workflow"""
    converter = FQCNConverter()

    # Test dry run first
    dry_result = converter.convert_file("playbook.yml", dry_run=True)
    if dry_result.success and dry_result.changes_made > 0:
        # Apply conversion
        result = converter.convert_file("playbook.yml")
        return result
    return dry_result
```

### Batch Processing

```python
def convert_multiple_files(file_paths):
    """Convert multiple files with progress tracking"""
    converter = FQCNConverter()
    results = []

    for i, file_path in enumerate(file_paths):
        print(f"Processing {i+1}/{len(file_paths)}: {file_path}")
        result = converter.convert_file(file_path)
        results.append(result)

    return results
```

## Best Practices

1. **Always use dry run first** to preview changes
2. **Handle errors gracefully** with try/except blocks
3. **Use progress tracking** for multiple files
4. **Create configuration files** for reusable settings

## Next Steps

- **[CLI Usage Guide](cli.md)** - Command-line interface
- **[API Reference](../reference/api.md)** - Complete API documentation
- **[Examples](../examples/)** - More usage examples

---

**Need help?** Check [GitHub Issues](https://github.com/mhtalci/ansible_fqcn_converter/issues) or [Discussions](https://github.com/mhtalci/ansible_fqcn_converter/discussions).