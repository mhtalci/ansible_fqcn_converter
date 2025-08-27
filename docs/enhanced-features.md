# Enhanced Features Guide

This guide covers the new enhanced features introduced in FQCN Converter v0.2.0, including interactive mode, advanced reporting, and developer tools.

## Table of Contents

1. [Interactive Mode](#interactive-mode)
2. [Enhanced Reporting](#enhanced-reporting)
3. [Developer Tools](#developer-tools)
4. [Pre-commit Hooks](#pre-commit-hooks)
5. [Configuration Generator](#configuration-generator)
6. [Performance Improvements](#performance-improvements)

## Interactive Mode

Interactive mode provides a guided conversion experience with previews and confirmations for each change.

### Features

- **Step-by-step conversion** with user confirmation
- **Preview changes** before applying them
- **File-by-file processing** with detailed feedback
- **Session statistics** and summary reporting
- **Error handling** with recovery options

### Usage

```bash
# Start interactive mode for a single file
fqcn-interactive playbook.yml

# Interactive mode for a directory
fqcn-interactive roles/

# With verbose output
fqcn-interactive --verbose playbooks/

# With custom configuration
fqcn-interactive --config custom-config.yml project/
```

### Interactive Workflow

1. **Welcome Screen**: Overview of files to be processed
2. **File Validation**: Check each file for syntax issues (informational only)
3. **Preview Changes**: Show potential FQCN conversions
4. **User Confirmation**: Accept or skip each file
5. **Conversion**: Apply approved changes
6. **Summary Report**: Session statistics and results

### Example Session

```
==============================================================
  FQCN Converter - Interactive Mode
==============================================================
Welcome to the interactive FQCN conversion wizard!
This mode will guide you through the conversion process
with previews and confirmations for each change.

Target directory: /path/to/ansible/project
Found 5 YAML files to process

Proceed with interactive conversion? [Y/n]: y

[1/5] Processing: playbook.yml
✓ File validation passed

Preview of changes for: playbook.yml
--------------------------------------------------
Found 3 potential conversions:
  1. copy → ansible.builtin.copy
     Line 15
  2. shell → ansible.builtin.shell
     Line 23
  3. service → ansible.builtin.service
     Line 31

Show detailed diff? [y/N]: n

Apply these 3 conversions? [Y/n]: y
✓ Successfully converted: playbook.yml

[2/5] Processing: tasks.yml
...

==================================================
  Interactive Session Summary
==================================================
Files processed: 5
Conversions made: 12
Files skipped: 1
Errors encountered: 0

Successfully converted files:
  - playbook.yml (3 conversions)
  - tasks.yml (4 conversions)
  - handlers.yml (2 conversions)
  - vars.yml (3 conversions)

Thank you for using FQCN Converter Interactive Mode!
```

## Enhanced Reporting

The enhanced reporting system provides comprehensive conversion reports in multiple formats with detailed statistics and analysis.

### Report Formats

- **JSON**: Machine-readable format for automation
- **HTML**: Rich web-based reports with styling
- **Markdown**: Documentation-friendly format
- **Console**: Colored terminal output

### Features

- **Detailed statistics** with success rates and performance metrics
- **File-by-file breakdown** with conversion details
- **Error and warning tracking** with context
- **Visual diffs** showing before/after changes
- **Performance monitoring** with timing and memory usage
- **Comparison reports** across multiple sessions

### Usage

```bash
# Convert with enhanced reporting
fqcn-enhanced convert-with-report project/ --format html --output report.html

# Generate all report formats
fqcn-enhanced convert-with-report project/ --all-formats --output-dir reports/

# Console report with statistics
fqcn-enhanced convert-with-report project/ --format console

# JSON report for automation
fqcn-enhanced convert-with-report project/ --format json --output results.json
```

### Report Contents

#### Summary Statistics
- Files processed, successful, failed, skipped
- Success rate and conversion efficiency
- Processing speed (files per second)
- Total processing time and memory usage

#### File Details
- Individual file status and conversion counts
- Processing time per file
- File sizes and backup status
- Error messages and warnings

#### Performance Metrics
- Memory usage tracking
- Processing speed analysis
- Resource utilization statistics
- Performance trends over time

#### Error Analysis
- Detailed error messages with context
- File-specific error tracking
- Stack traces for debugging
- Recovery suggestions

### Sample HTML Report

The HTML reports include:
- Interactive charts and graphs
- Sortable tables with file details
- Color-coded status indicators
- Responsive design for mobile viewing
- Embedded CSS for standalone viewing

### Sample JSON Report Structure

```json
{
  "session_id": "uuid-string",
  "start_time": "2023-01-01T12:00:00",
  "end_time": "2023-01-01T12:05:30",
  "duration": 330.5,
  "target_path": "/path/to/project",
  "statistics": {
    "total_files_processed": 25,
    "total_files_successful": 23,
    "total_files_failed": 1,
    "total_files_skipped": 1,
    "success_rate": 0.92,
    "total_conversions_made": 87,
    "conversion_efficiency": 0.95,
    "processing_speed": 4.5,
    "total_processing_time": 5.5,
    "peak_memory_usage": 45000000
  },
  "file_records": [...],
  "errors": [...],
  "warnings": [...]
}
```

## Developer Tools

The developer tools package provides utilities for integrating FQCN conversion into development workflows.

### Available Tools

- **Pre-commit hooks** for automatic validation
- **Configuration generators** for different project types
- **Git integration** utilities
- **CI/CD templates** for popular platforms

### Pre-commit Hook Installation

```bash
# Install pre-commit hook in current repository
fqcn-enhanced tools precommit .

# Install with auto-fix enabled
fqcn-enhanced tools precommit --auto-fix .

# Install with strict mode (fail on any issues)
fqcn-enhanced tools precommit --strict .

# Uninstall hook
fqcn-enhanced tools precommit --uninstall .
```

### Configuration Generation

```bash
# Generate basic configuration
fqcn-enhanced tools config --template basic --output fqcn-config.yml

# Generate advanced configuration
fqcn-enhanced tools config --template advanced --project-name my-project

# Auto-detect project type and generate config
fqcn-enhanced tools config --detect /path/to/project

# Generate CI/CD configuration
fqcn-enhanced tools config --template cicd --format json

# Generate enterprise configuration
fqcn-enhanced tools config --template enterprise --project-name corp-ansible
```

### GitHub Actions Workflow

```bash
# Generate GitHub Actions workflow
fqcn-enhanced tools generate-github-workflow .github/workflows/fqcn-validation.yml

# With custom Python version
fqcn-enhanced tools generate-github-workflow --python-version 3.11 .github/workflows/fqcn.yml
```

### Pre-commit Configuration

```bash
# Generate .pre-commit-config.yaml
fqcn-enhanced tools generate-precommit-config .pre-commit-config.yaml

# With auto-fix enabled
fqcn-enhanced tools generate-precommit-config --auto-fix .pre-commit-config.yaml

# With strict mode
fqcn-enhanced tools generate-precommit-config --strict .pre-commit-config.yaml
```

## Pre-commit Hooks

Pre-commit hooks automatically validate FQCN compliance before commits are made.

### Features

- **Automatic validation** of staged YAML files
- **Auto-fix capability** for common issues
- **Strict mode** for enforcing compliance
- **Bypass mechanisms** for emergency commits
- **Integration** with popular pre-commit frameworks

### Hook Configuration

The generated `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: fqcn-converter
        name: FQCN Converter
        entry: fqcn-converter-precommit
        language: python
        files: \.(yml|yaml)$
        args: []  # Add --auto-fix or --strict as needed
```

### Manual Hook Usage

```bash
# Run hook on specific files
fqcn-precommit playbook.yml tasks.yml

# Run with auto-fix
fqcn-precommit --auto-fix *.yml

# Run in strict mode
fqcn-precommit --strict roles/

# Install hook in repository
fqcn-precommit --install /path/to/repo

# Uninstall hook
fqcn-precommit --uninstall /path/to/repo
```

### Hook Behavior

1. **File Detection**: Identifies staged YAML files
2. **Validation**: Checks for FQCN compliance
3. **Auto-fix** (if enabled): Attempts to fix issues automatically
4. **Reporting**: Shows validation results
5. **Exit Code**: Returns 0 for success, 1 for failure

## Configuration Generator

The configuration generator creates project-specific configurations for different scenarios.

### Project Templates

#### Basic Template
- Simple configuration for small projects
- Essential settings only
- Suitable for learning and testing

#### Advanced Template
- Comprehensive configuration options
- Custom collection mappings
- Advanced file patterns and exclusions

#### CI/CD Template
- Optimized for continuous integration
- Machine-readable output formats
- Reduced logging for clean CI logs

#### Enterprise Template
- Full-featured configuration
- Support for multiple cloud providers
- Comprehensive collection mappings
- Advanced reporting and monitoring

### Configuration Options

```yaml
# Example generated configuration
project_name: "my-ansible-project"
ansible_version: ">=2.9"

# Conversion settings
backup_files: true
validate_syntax: true
preserve_comments: true

# Collection preferences
preferred_collections:
  - "ansible.builtin"
  - "ansible.posix"
  - "community.general"

# Custom mappings
collection_mappings:
  shell: "ansible.builtin.shell"
  copy: "ansible.builtin.copy"
  service: "ansible.builtin.service"

# File patterns
include_patterns:
  - "*.yml"
  - "*.yaml"
  - "playbooks/**/*.yml"

exclude_patterns:
  - "venv/**"
  - ".git/**"
  - "*.backup"

# Output settings
report_format: "console"
log_level: "INFO"
```

### Auto-detection

The configuration generator can automatically detect project types based on:

- **File structure**: Presence of roles/, playbooks/, group_vars/
- **Configuration files**: ansible.cfg, requirements.yml
- **CI/CD indicators**: .github/, .gitlab-ci.yml, Jenkinsfile
- **File patterns**: Number and types of YAML files

## Performance Improvements

The enhanced version includes several performance optimizations:

### Memory Optimization

- **Streaming processing** for large files
- **Memory usage monitoring** and reporting
- **Garbage collection** optimization
- **Resource cleanup** after processing

### Processing Speed

- **Parallel processing** capabilities
- **Caching strategies** for repeated operations
- **Optimized YAML parsing** with ruamel.yaml
- **Efficient file I/O** operations

### Monitoring

- **Real-time performance tracking**
- **Memory usage alerts**
- **Processing speed metrics**
- **Resource utilization reporting**

### Benchmarking

```bash
# Performance monitoring during conversion
fqcn-enhanced convert-with-report --format json large-project/ | jq '.statistics'

# Memory usage tracking
{
  "peak_memory_usage": 67108864,
  "initial_memory_mb": 25.5,
  "final_memory_mb": 28.2,
  "memory_delta_mb": 2.7
}

# Processing speed metrics
{
  "processing_speed": 12.5,  # files per second
  "average_processing_time": 0.08,  # seconds per file
  "total_processing_time": 4.2  # total seconds
}
```

## Integration Examples

### GitHub Actions

```yaml
name: FQCN Validation
on: [push, pull_request]

jobs:
  fqcn-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install FQCN Converter
        run: pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git
      - name: Validate FQCN compliance
        run: fqcn-validator --strict .
      - name: Generate validation report
        run: fqcn-enhanced convert-with-report --format json --output-dir reports .
        if: always()
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: fqcn-validation-report
          path: reports/
        if: always()
```

### GitLab CI

```yaml
fqcn-validation:
  stage: test
  image: python:3.9
  script:
    - pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git
    - fqcn-validator --strict .
    - fqcn-enhanced convert-with-report --format html --output-dir reports .
  artifacts:
    when: always
    paths:
      - reports/
    reports:
      junit: reports/*.xml
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    stages {
        stage('FQCN Validation') {
            steps {
                sh 'pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git'
                sh 'fqcn-validator --strict .'
                sh 'fqcn-enhanced convert-with-report --format json --output reports.json .'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports.json', fingerprint: true
                }
            }
        }
    }
}
```

## Best Practices

### Interactive Mode

1. **Start with validation** to identify issues early
2. **Use preview mode** to understand changes before applying
3. **Process small batches** for better control
4. **Keep backups** of important files
5. **Review session summaries** for insights

### Reporting

1. **Use appropriate formats** for your audience
2. **Archive reports** for historical analysis
3. **Monitor performance trends** over time
4. **Set up automated reporting** in CI/CD
5. **Share reports** with team members

### Developer Tools

1. **Install pre-commit hooks** early in development
2. **Use auto-fix judiciously** - review changes
3. **Configure strict mode** for critical projects
4. **Generate project-specific configs** for consistency
5. **Integrate with existing workflows** gradually

### Performance

1. **Monitor memory usage** for large projects
2. **Use parallel processing** when available
3. **Profile performance** to identify bottlenecks
4. **Optimize file patterns** to reduce processing
5. **Clean up resources** after processing

## Troubleshooting

### Common Issues

#### Interactive Mode Not Starting
- Check file permissions
- Verify Python environment
- Ensure colorama is installed

#### Reports Not Generating
- Check output directory permissions
- Verify disk space availability
- Check for file path issues

#### Pre-commit Hook Failures
- Verify git repository status
- Check hook installation
- Review file staging

#### Performance Issues
- Monitor memory usage
- Check file sizes and counts
- Review system resources

### Getting Help

- Check the [FAQ](faq.md) for common questions
- Review [troubleshooting guide](troubleshooting.md) for detailed solutions
- Open an issue on GitHub for bugs
- Join community discussions for support

## What's Next

The enhanced features in v0.2.0 lay the foundation for future improvements:

- **Web interface** for browser-based conversion
- **API client libraries** for integration
- **Machine learning** for smarter conversions
- **Advanced analytics** and insights
- **Multi-language support** for documentation

Stay tuned for more exciting features in upcoming releases!