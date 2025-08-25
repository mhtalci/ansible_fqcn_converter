# Python API Guide

**Last Updated: August 26, 2025**

🎉 **Production Ready - All Tests Passing (277/277)**

This guide covers how to use the production-ready FQCN Converter as a Python library in your applications.

## Overview

The FQCN Converter provides a clean Python API for programmatic conversion and validation of Ansible files. This is useful for:

- **Custom automation scripts**
- **Integration with existing tools**
- **Batch processing workflows**
- **CI/CD pipeline integration**
- **Custom validation rules**

## Quick Start

### Basic Import and Usage

```python
from fqcn_converter import FQCNConverter

# Initialize converter with default settings
converter = FQCNConverter()

# Convert a file
result = converter.convert_file("playbook.yml")

# Check results
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
---
- name: Install and start nginx
  hosts: webservers
  tasks:
    - name: Install nginx
      package:
        name: nginx
        state: present
    
    - name: Start nginx service
      service:
        name: nginx
        state: started
"""

# Convert content
result = converter.convert_content(content)

if result.success:
    print("Converted content:")
    print(result.converted_content)
```

## Core Classes

### FQCNConverter

The main converter class that handles FQCN conversion operations.

#### Constructor

```python
from fqcn_converter import FQCNConverter

converter = FQCNConverter(
    config_path=None,           # Path to custom configuration file
    custom_mappings=None,       # Dictionary of custom module mappings
    create_backups=True,        # Whether to create backup files
    backup_suffix=".fqcn_backup"  # Suffix for backup files
)
```

#### Methods

##### `convert_file(file_path, dry_run=False)`

Convert a single Ansible file to FQCN format.

```python
from fqcn_converter import FQCNConverter

converter = FQCNConverter()

# Convert with dry run (preview only)
result = converter.convert_file("playbook.yml", dry_run=True)
print(f"Would convert {result.changes_made} modules")

# Actually convert the file
result = converter.convert_file("playbook.yml")
if result.success:
    print(f"Successfully converted {result.changes_made} modules")
    print(f"Backup created: {result.backup_path}")
```

##### `convert_content(content, file_type="yaml")`

Convert YAML content string to FQCN format.

```python
yaml_content = """
- name: Copy file
  copy:
    src: /tmp/file
    dest: /etc/file
"""

result = converter.convert_content(yaml_content)
print(result.converted_content)
# Output:
# - name: Copy file
#   ansible.builtin.copy:
#     src: /tmp/file
#     dest: /etc/file
```

##### `convert_directory(directory_path, recursive=True, dry_run=False)`

Convert all Ansible files in a directory.

```python
# Convert all files in directory
result = converter.convert_directory("/path/to/ansible/project")

# Convert with options
result = converter.convert_directory(
    "/path/to/project",
    recursive=True,      # Include subdirectories
    dry_run=False,       # Actually perform conversion
    include_patterns=["*.yml", "*.yaml"],
    exclude_patterns=["**/test/**"]
)

print(f"Processed {result.files_processed} files")
print(f"Modified {result.files_modified} files")
```

### ValidationEngine

Validate FQCN usage in Ansible files.

#### Constructor

```python
from fqcn_converter import ValidationEngine

validator = ValidationEngine(
    config_path=None,     # Path to custom configuration
    strict_mode=False     # Enable strict validation rules
)
```

#### Methods

##### `validate_file(file_path)`

Validate a single file for proper FQCN usage.

```python
from fqcn_converter import ValidationEngine

validator = ValidationEngine()

result = validator.validate_file("playbook.yml")

if result.valid:
    print(f"✅ File is valid (score: {result.score:.1%})")
else:
    print(f"❌ Found {len(result.issues)} issues:")
    for issue in result.issues:
        print(f"  Line {issue.line}: {issue.message}")
```

##### `validate_content(content)`

Validate YAML content string.

```python
yaml_content = """
- name: Install package
  package:  # Should be ansible.builtin.package
    name: nginx
"""

result = validator.validate_content(yaml_content)
for issue in result.issues:
    print(f"Issue: {issue.message} at line {issue.line}")
```

### BatchProcessor

Process multiple Ansible projects in parallel.

#### Constructor

```python
from fqcn_converter import BatchProcessor

processor = BatchProcessor(
    max_workers=4,        # Number of parallel workers
    config_path=None,     # Path to configuration file
    progress_callback=None  # Optional progress callback function
)
```

#### Methods

##### `process_projects(project_paths, dry_run=False)`

Process multiple projects in parallel.

```python
from fqcn_converter import BatchProcessor

processor = BatchProcessor(max_workers=4)

project_paths = [
    "/path/to/project1",
    "/path/to/project2", 
    "/path/to/project3"
]

# Process with progress callback
def progress_callback(completed, total, current_project):
    print(f"Progress: {completed}/{total} - Processing {current_project}")

processor = BatchProcessor(
    max_workers=4,
    progress_callback=progress_callback
)

result = processor.process_projects(project_paths)

print(f"Processed {result.total_projects} projects")
print(f"Success rate: {result.success_rate:.1%}")
```

## Data Classes

### ConversionResult

Represents the result of a conversion operation.

```python
@dataclass
class ConversionResult:
    success: bool                    # Whether conversion succeeded
    file_path: str                   # Path to the converted file
    changes_made: int                # Number of modules converted
    errors: List[str]                # List of error messages
    warnings: List[str]              # List of warning messages
    backup_path: Optional[str]       # Path to backup file (if created)
    original_content: Optional[str]  # Original file content
    converted_content: Optional[str] # Converted file content
    processing_time: float           # Time taken for conversion
```

#### Usage Example

```python
result = converter.convert_file("playbook.yml")

# Check success
if result.success:
    print(f"✅ Success: {result.changes_made} modules converted")
    if result.backup_path:
        print(f"📁 Backup saved to: {result.backup_path}")
else:
    print("❌ Conversion failed:")
    for error in result.errors:
        print(f"  - {error}")

# Show warnings if any
if result.warnings:
    print("⚠️  Warnings:")
    for warning in result.warnings:
        print(f"  - {warning}")

print(f"⏱️  Processing time: {result.processing_time:.2f}s")
```

### ValidationResult

Represents the result of a validation operation.

```python
@dataclass
class ValidationResult:
    valid: bool                      # Whether file is valid
    file_path: str                   # Path to validated file
    issues: List[ValidationIssue]    # List of validation issues
    score: float                     # Compliance score (0.0-1.0)
    total_modules: int               # Total modules found
    fqcn_modules: int               # Modules using FQCN
    processing_time: float           # Time taken for validation
```

### ValidationIssue

Represents a single validation issue.

```python
@dataclass
class ValidationIssue:
    line: int           # Line number where issue occurs
    column: int         # Column number (if available)
    message: str        # Description of the issue
    severity: str       # 'error', 'warning', or 'info'
    module_name: str    # Name of the problematic module
    suggested_fix: str  # Suggested FQCN replacement
```

### BatchResult

Represents the result of batch processing.

```python
@dataclass
class BatchResult:
    total_projects: int                    # Total projects processed
    successful_projects: int               # Successfully processed projects
    failed_projects: int                   # Failed projects
    project_results: List[ConversionResult] # Individual project results
    total_files_processed: int             # Total files across all projects
    total_modules_converted: int           # Total modules converted
    processing_time: float                 # Total processing time
    success_rate: float                    # Success rate (0.0-1.0)
```

## Advanced Usage

### Custom Configuration

```python
from fqcn_converter import FQCNConverter

# Custom mappings dictionary
custom_mappings = {
    "my_custom_module": "my_namespace.my_collection.my_custom_module",
    "legacy_module": "community.general.legacy_module"
}

# Initialize with custom mappings
converter = FQCNConverter(custom_mappings=custom_mappings)

# Or use configuration file
converter = FQCNConverter(config_path="custom_config.yml")
```

### Error Handling

```python
from fqcn_converter import FQCNConverter, FQCNConverterError
from fqcn_converter.exceptions import (
    ConversionError,
    ValidationError,
    ConfigurationError
)

converter = FQCNConverter()

try:
    result = converter.convert_file("playbook.yml")
    if not result.success:
        print("Conversion completed with issues:")
        for error in result.errors:
            print(f"  Error: {error}")
        for warning in result.warnings:
            print(f"  Warning: {warning}")
            
except ConversionError as e:
    print(f"Conversion failed: {e}")
except ValidationError as e:
    print(f"Validation failed: {e}")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
except FQCNConverterError as e:
    print(f"General error: {e}")
```

### Progress Tracking

```python
from fqcn_converter import BatchProcessor
import time

def progress_callback(completed, total, current_item):
    """Custom progress callback"""
    percentage = (completed / total) * 100
    print(f"\rProgress: {percentage:.1f}% ({completed}/{total}) - {current_item}", end="")
    
    # Update progress bar, send to monitoring system, etc.
    # update_progress_bar(percentage)
    # send_metrics(completed, total)

processor = BatchProcessor(
    max_workers=4,
    progress_callback=progress_callback
)

projects = ["/path/to/project1", "/path/to/project2"]
result = processor.process_projects(projects)
print(f"\n✅ Completed: {result.success_rate:.1%} success rate")
```

### Logging Integration

```python
import logging
from fqcn_converter import FQCNConverter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# The converter will use the configured logger
converter = FQCNConverter()

# Enable debug logging for detailed output
logging.getLogger('fqcn_converter').setLevel(logging.DEBUG)

result = converter.convert_file("playbook.yml")
```

### Integration with Other Tools

#### Ansible Lint Integration

```python
from fqcn_converter import FQCNConverter, ValidationEngine
import subprocess
import json

def convert_and_lint(file_path):
    """Convert file and run ansible-lint validation"""
    
    # Convert to FQCN
    converter = FQCNConverter()
    conv_result = converter.convert_file(file_path, dry_run=True)
    
    if not conv_result.success:
        return {"status": "conversion_failed", "errors": conv_result.errors}
    
    # Apply conversion
    conv_result = converter.convert_file(file_path)
    
    # Run ansible-lint
    try:
        result = subprocess.run(
            ["ansible-lint", "--format", "json", file_path],
            capture_output=True,
            text=True
        )
        lint_issues = json.loads(result.stdout) if result.stdout else []
        
        return {
            "status": "success",
            "conversion": conv_result,
            "lint_issues": lint_issues
        }
    except Exception as e:
        return {"status": "lint_failed", "error": str(e)}

# Usage
result = convert_and_lint("playbook.yml")
print(f"Status: {result['status']}")
```

#### Git Integration

```python
from fqcn_converter import FQCNConverter
import git
import os

def convert_git_repository(repo_path, branch="main"):
    """Convert all Ansible files in a Git repository"""
    
    # Open repository
    repo = git.Repo(repo_path)
    
    # Create new branch for conversion
    conversion_branch = f"fqcn-conversion-{int(time.time())}"
    repo.git.checkout("-b", conversion_branch)
    
    try:
        # Convert files
        converter = FQCNConverter()
        result = converter.convert_directory(repo_path)
        
        if result.files_modified > 0:
            # Stage changes
            repo.git.add("*.yml", "*.yaml")
            
            # Commit changes
            commit_message = f"Convert to FQCN format\n\n" \
                           f"Files modified: {result.files_modified}\n" \
                           f"Modules converted: {result.total_modules_converted}"
            
            repo.index.commit(commit_message)
            
            return {
                "status": "success",
                "branch": conversion_branch,
                "result": result
            }
        else:
            # No changes needed, delete branch
            repo.git.checkout(branch)
            repo.git.branch("-D", conversion_branch)
            
            return {
                "status": "no_changes_needed",
                "result": result
            }
            
    except Exception as e:
        # Rollback on error
        repo.git.checkout(branch)
        repo.git.branch("-D", conversion_branch)
        raise e

# Usage
result = convert_git_repository("/path/to/ansible/repo")
print(f"Conversion status: {result['status']}")
```

## Testing Your Integration

### Unit Testing

```python
import unittest
from unittest.mock import patch, mock_open
from fqcn_converter import FQCNConverter

class TestFQCNConverter(unittest.TestCase):
    
    def setUp(self):
        self.converter = FQCNConverter()
    
    def test_convert_content(self):
        """Test content conversion"""
        input_content = """
        - name: Install package
          package:
            name: nginx
        """
        
        result = self.converter.convert_content(input_content)
        
        self.assertTrue(result.success)
        self.assertIn("ansible.builtin.package", result.converted_content)
        self.assertEqual(result.changes_made, 1)
    
    @patch("builtins.open", new_callable=mock_open, read_data="- package: {name: nginx}")
    def test_convert_file(self, mock_file):
        """Test file conversion with mocked file"""
        result = self.converter.convert_file("test.yml")
        
        self.assertTrue(result.success)
        mock_file.assert_called()

if __name__ == "__main__":
    unittest.main()
```

### Integration Testing

```python
import tempfile
import os
from fqcn_converter import FQCNConverter

def test_full_workflow():
    """Test complete conversion workflow"""
    
    # Create temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write("""
---
- name: Test playbook
  hosts: localhost
  tasks:
    - name: Install package
      package:
        name: nginx
    - name: Start service
      service:
        name: nginx
        state: started
""")
        temp_file = f.name
    
    try:
        converter = FQCNConverter()
        
        # Test dry run
        dry_result = converter.convert_file(temp_file, dry_run=True)
        assert dry_result.success
        assert dry_result.changes_made == 2
        
        # Test actual conversion
        result = converter.convert_file(temp_file)
        assert result.success
        assert result.changes_made == 2
        
        # Verify content
        with open(temp_file, 'r') as f:
            content = f.read()
            assert "ansible.builtin.package" in content
            assert "ansible.builtin.service" in content
        
        print("✅ Full workflow test passed")
        
    finally:
        # Clean up
        os.unlink(temp_file)
        if os.path.exists(temp_file + ".fqcn_backup"):
            os.unlink(temp_file + ".fqcn_backup")

# Run test
test_full_workflow()
```

## Best Practices

### 1. Always Handle Errors

```python
from fqcn_converter import FQCNConverter, FQCNConverterError

converter = FQCNConverter()

try:
    result = converter.convert_file("playbook.yml")
    if result.success:
        # Handle success
        pass
    else:
        # Handle conversion issues
        for error in result.errors:
            logging.error(f"Conversion error: {error}")
except FQCNConverterError as e:
    # Handle exceptions
    logging.exception(f"Converter failed: {e}")
```

### 2. Use Dry Run for Validation

```python
# Always preview changes first
dry_result = converter.convert_file("playbook.yml", dry_run=True)

if dry_result.success and dry_result.changes_made > 0:
    # User confirmation or automated approval logic
    if confirm_changes(dry_result):
        actual_result = converter.convert_file("playbook.yml")
```

### 3. Implement Progress Tracking

```python
def convert_multiple_files(file_paths):
    """Convert multiple files with progress tracking"""
    results = []
    total = len(file_paths)
    
    for i, file_path in enumerate(file_paths):
        print(f"Processing {i+1}/{total}: {file_path}")
        
        result = converter.convert_file(file_path)
        results.append(result)
        
        if not result.success:
            print(f"  ❌ Failed: {result.errors}")
        else:
            print(f"  ✅ Success: {result.changes_made} changes")
    
    return results
```

### 4. Use Configuration Files

```python
# Create reusable configuration
config = {
    "mappings": {
        "custom_module": "my.collection.custom_module"
    },
    "settings": {
        "create_backups": True,
        "strict_mode": False
    }
}

# Save configuration
import yaml
with open("fqcn_config.yml", "w") as f:
    yaml.dump(config, f)

# Use configuration
converter = FQCNConverter(config_path="fqcn_config.yml")
```

## Next Steps

- **[CLI Usage Guide](cli.md)**: Learn command-line usage
- **[Configuration Guide](../configuration.md)**: Customize converter behavior  
- **[Examples](../examples/)**: See real-world integration examples
- **[Contributing](../development/contributing.md)**: Contribute to the project

---

**Need help?** Check our [API Reference](../reference/api.md) or [open an issue](https://github.com/mhtalci/ansible_fqcn_converter/issues).