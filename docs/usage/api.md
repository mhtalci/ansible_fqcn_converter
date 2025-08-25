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

Main converter class for FQCN conversion operations.

```python
from fqcn_converter import FQCNConverter

# Initialize with default settings
converter = FQCNConverter()

# Initialize with custom mappings
custom_mappings = {"my_module": "my.collection.my_module"}
converter = FQCNConverter(custom_mappings=custom_mappings)

# Initialize with configuration file
converter = FQCNConverter(config_path="custom_config.yml")
```

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

Validate FQCN usage in Ansible files.

```python
from fqcn_converter import ValidationEngine

validator = ValidationEngine()
result = validator.validate_file("playbook.yml")

if result.valid:
    print(f"✅ Valid (score: {result.score:.1%})")
else:
    for issue in result.issues:
        print(f"Line {issue.line}: {issue.message}")
```

### BatchProcessor

Process multiple projects in parallel.

```python
from fqcn_converter import BatchProcessor

def progress_callback(completed, total, current):
    print(f"Progress: {completed}/{total} - {current}")

processor = BatchProcessor(max_workers=4, progress_callback=progress_callback)
result = processor.process_projects(["/path/to/project1", "/path/to/project2"])
```

## Result Objects

### ConversionResult

```python
result = converter.convert_file("playbook.yml")

# Key attributes
result.success          # bool: Whether conversion succeeded
result.changes_made     # int: Number of modules converted
result.errors          # List[str]: Error messages
result.warnings        # List[str]: Warning messages
result.backup_path     # Optional[str]: Path to backup file
result.processing_time # float: Time taken for conversion
```

### ValidationResult

```python
result = validator.validate_file("playbook.yml")

# Key attributes
result.valid           # bool: Whether file is valid
result.score          # float: Compliance score (0.0-1.0)
result.issues         # List[ValidationIssue]: Validation issues
result.total_modules  # int: Total modules found
result.fqcn_modules   # int: Modules using FQCN
```

### ValidationIssue

```python
for issue in result.issues:
    print(f"Line {issue.line}: {issue.message}")
    print(f"Severity: {issue.severity}")  # 'error', 'warning', 'info'
    print(f"Suggestion: {issue.suggested_fix}")
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