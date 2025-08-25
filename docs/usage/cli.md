# CLI Usage Guide

**Last Updated: August 26, 2025**

🎉 **Production Ready - All Tests Passing (277/277)**

This guide covers all command-line interface (CLI) functionality of the production-ready FQCN Converter, including commands, options, and practical examples.

## Overview

The FQCN Converter provides a comprehensive CLI with three main commands:
- **`convert`**: Convert Ansible files to use FQCN format
- **`validate`**: Validate FQCN usage in Ansible files
- **`batch`**: Process multiple Ansible projects in parallel

## Global Options

These options are available for all commands:

```bash
fqcn-converter [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

### Global Options
- `--version`: Show version information
- `--help`: Show help message
- `--verbose, -v`: Enable verbose logging
- `--quiet, -q`: Suppress all output except errors
- `--debug`: Enable debug logging (most verbose)

### Examples
```bash
# Show version
fqcn-converter --version

# Get help for any command
fqcn-converter convert --help
fqcn-converter validate --help
fqcn-converter batch --help

# Global flags (--verbose, --debug, --quiet) can be placed anywhere
fqcn-converter --verbose convert --dry-run
fqcn-converter convert --dry-run --verbose
fqcn-converter convert --verbose --dry-run
fqcn-converter --debug validate --strict
```

## Global Flags Flexibility

Global flags (`--verbose`, `-v`, `--quiet`, `-q`, `--debug`) can be placed anywhere in the command line for convenience:

```bash
# All of these are equivalent:
fqcn-converter --verbose convert --dry-run playbook.yml
fqcn-converter convert --verbose --dry-run playbook.yml
fqcn-converter convert --dry-run --verbose playbook.yml
fqcn-converter convert --dry-run playbook.yml --verbose

# Short form also works anywhere:
fqcn-converter convert -v --dry-run playbook.yml
fqcn-converter convert --dry-run -v playbook.yml
```

## Convert Command

Convert Ansible files to use Fully Qualified Collection Names (FQCN).

### Syntax
```bash
fqcn-converter convert [OPTIONS] [PATH]
```

### Options
- `--dry-run, -n`: Preview changes without modifying files
- `--config, -c PATH`: Use custom configuration file
- `--backup/--no-backup`: Create backup files (default: enabled)
- `--output, -o PATH`: Write results to specific directory
- `--report PATH`: Generate detailed conversion report
- `--include PATTERN`: Include files matching pattern
- `--exclude PATTERN`: Exclude files matching pattern

### Basic Usage

#### Convert Current Directory
```bash
# Preview changes (recommended first step)
fqcn-converter convert --dry-run

# Apply conversion
fqcn-converter convert
```

#### Convert Specific Directory
```bash
# Convert all Ansible files in a directory
fqcn-converter convert /path/to/ansible/project

# Convert with dry run first
fqcn-converter convert --dry-run /path/to/ansible/project
```

#### Convert Specific Files
```bash
# Convert specific files
fqcn-converter convert playbook.yml roles/web/tasks/main.yml

# Convert with pattern matching
fqcn-converter convert --include "*.yml" --exclude "*test*"
```

### Advanced Usage

#### Custom Configuration
```bash
# Use custom mapping configuration
fqcn-converter convert --config custom_mappings.yml

# Generate and use project-specific config
fqcn-converter convert --config /path/to/project/fqcn_config.yml
```

#### Backup Management
```bash
# Convert without creating backups
fqcn-converter convert --no-backup

# Convert with backups (default behavior)
fqcn-converter convert --backup
```

#### Reporting
```bash
# Generate detailed conversion report
fqcn-converter convert --report conversion_report.json

# Convert with verbose output and report
fqcn-converter --verbose convert --report detailed_report.json
```

### Output Examples

#### Dry Run Output
```
$ fqcn-converter convert --dry-run
🔍 Scanning for Ansible files...
📁 Found 15 files to process

📝 Preview of changes:
  playbook.yml:
    Line 12: package → ansible.builtin.package
    Line 18: service → ansible.builtin.service
  
  roles/web/tasks/main.yml:
    Line 5: copy → ansible.builtin.copy
    Line 12: template → ansible.builtin.template

✅ Would convert 4 modules across 2 files
💡 Run without --dry-run to apply changes
```

#### Actual Conversion Output
```
$ fqcn-converter convert
🔍 Scanning for Ansible files...
📁 Found 15 files to process

🔄 Converting files...
✅ playbook.yml (2 modules converted)
✅ roles/web/tasks/main.yml (2 modules converted)
✅ roles/web/handlers/main.yml (1 module converted)

📊 Conversion Summary:
  Files processed: 15
  Files modified: 3
  Modules converted: 5
  Backup files created: 3

🎉 Conversion completed successfully!
```

## Validate Command

Validate that Ansible files properly use FQCN format and identify any issues.

### Syntax
```bash
fqcn-converter validate [OPTIONS] [PATH]
```

### Options
- `--report PATH`: Generate detailed validation report
- `--strict`: Use strict validation rules
- `--config, -c PATH`: Use custom configuration file
- `--format FORMAT`: Output format (text, json, yaml)

### Basic Usage

#### Validate Current Directory
```bash
# Basic validation
fqcn-converter validate

# Strict validation with detailed output
fqcn-converter --verbose validate --strict
```

#### Validate Specific Path
```bash
# Validate specific directory
fqcn-converter validate /path/to/ansible/project

# Validate with custom configuration
fqcn-converter validate --config custom_rules.yml
```

### Advanced Usage

#### Generate Reports
```bash
# Generate JSON validation report
fqcn-converter validate --report validation_report.json

# Generate YAML report with strict rules
fqcn-converter validate --strict --report report.yaml --format yaml
```

#### Different Output Formats
```bash
# JSON output
fqcn-converter validate --format json

# YAML output  
fqcn-converter validate --format yaml

# Default text output
fqcn-converter validate --format text
```

### Output Examples

#### Successful Validation
```
$ fqcn-converter validate
🔍 Validating FQCN usage...
📁 Found 15 Ansible files

✅ All files are using proper FQCN format
📊 Validation Summary:
  Files checked: 15
  FQCN modules found: 45
  Issues found: 0
  Compliance score: 100%

🎉 Validation passed!
```

#### Validation with Issues
```
$ fqcn-converter validate
🔍 Validating FQCN usage...
📁 Found 15 Ansible files

⚠️  Issues found:

playbook.yml:
  Line 12: 'package' should be 'ansible.builtin.package'
  Line 18: 'service' should be 'ansible.builtin.service'

roles/db/tasks/main.yml:
  Line 8: 'mysql_user' should be 'community.mysql.mysql_user'

📊 Validation Summary:
  Files checked: 15
  FQCN modules found: 42
  Issues found: 3
  Compliance score: 93%

💡 Run 'fqcn-converter convert' to fix these issues
```

## Batch Command

Process multiple Ansible projects in parallel for large-scale conversions.

### Syntax
```bash
fqcn-converter batch [OPTIONS] ROOT_PATH
```

### Options
- `--workers, -w NUM`: Number of parallel workers (default: 4)
- `--dry-run, -n`: Preview changes without modifying files
- `--config, -c PATH`: Use custom configuration file
- `--report PATH`: Generate detailed batch report
- `--project-pattern PATTERN`: Pattern to identify project directories
- `--exclude-pattern PATTERN`: Pattern to exclude directories

### Basic Usage

#### Process Multiple Projects
```bash
# Process all projects in directory with 4 workers
fqcn-converter batch /path/to/ansible/projects

# Preview changes across all projects
fqcn-converter batch --dry-run /path/to/ansible/projects
```

#### Parallel Processing
```bash
# Use 8 parallel workers for faster processing
fqcn-converter batch --workers 8 /path/to/projects

# Use single worker for debugging
fqcn-converter batch --workers 1 /path/to/projects
```

### Advanced Usage

#### Custom Project Detection
```bash
# Custom pattern to identify Ansible projects
fqcn-converter batch --project-pattern "**/playbooks" /path/to/repos

# Exclude certain directories
fqcn-converter batch --exclude-pattern "**/archive/**" /path/to/projects
```

#### Comprehensive Batch Processing
```bash
# Full batch processing with reporting
fqcn-converter batch \
  --workers 6 \
  --config enterprise_config.yml \
  --report batch_conversion_report.json \
  --verbose \
  /path/to/ansible/projects
```

### Output Examples

#### Batch Processing Output
```
$ fqcn-converter batch --workers 4 /path/to/projects
🔍 Discovering Ansible projects...
📁 Found 12 projects to process

🚀 Starting batch processing with 4 workers...

✅ project-web (5 files, 12 modules converted)
✅ project-db (3 files, 8 modules converted)  
✅ project-api (7 files, 15 modules converted)
⚠️  project-legacy (2 files, 3 modules converted, 1 warning)
✅ project-monitoring (4 files, 9 modules converted)
...

📊 Batch Processing Summary:
  Projects processed: 12
  Total files modified: 45
  Total modules converted: 127
  Processing time: 2m 34s
  Success rate: 100%

🎉 Batch processing completed!
```

## Configuration Files

### Default Configuration
The converter uses built-in configuration by default, but you can customize it:

```bash
# Generate default configuration file
fqcn-converter convert --config-template > fqcn_config.yml

# Use custom configuration
fqcn-converter convert --config fqcn_config.yml
```

### Configuration File Format
```yaml
# fqcn_config.yml
version: "1.0"

# Module mappings
mappings:
  package: "ansible.builtin.package"
  service: "ansible.builtin.service"
  copy: "ansible.builtin.copy"
  # Add custom mappings...

# File patterns
patterns:
  include:
    - "*.yml"
    - "*.yaml"
  exclude:
    - "**/test/**"
    - "**/.git/**"

# Conversion settings
settings:
  create_backups: true
  backup_suffix: ".fqcn_backup"
  strict_mode: false
```

## Integration Examples

### CI/CD Pipeline Integration

#### GitHub Actions
```yaml
name: FQCN Validation
on: [push, pull_request]

jobs:
  validate-fqcn:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install FQCN Converter
        run: pip install fqcn-converter
      - name: Validate FQCN Usage
        run: fqcn-converter validate --strict --report fqcn_report.json
      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: fqcn-report
          path: fqcn_report.json
```

#### GitLab CI
```yaml
fqcn-validation:
  image: python:3.9
  script:
    - pip install fqcn-converter
    - fqcn-converter validate --strict --format json
  artifacts:
    reports:
      junit: fqcn_report.json
```

### Pre-commit Hook
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: fqcn-validation
        name: Validate FQCN usage
        entry: fqcn-converter validate --strict
        language: system
        files: \.(yml|yaml)$
        pass_filenames: false
```

### Makefile Integration
```makefile
# Makefile
.PHONY: fqcn-check fqcn-convert fqcn-validate

fqcn-check:
	fqcn-converter validate --strict

fqcn-convert:
	fqcn-converter convert --dry-run
	@read -p "Apply changes? [y/N] " confirm && [ "$$confirm" = "y" ]
	fqcn-converter convert

fqcn-validate:
	fqcn-converter validate --report validation_report.json
```

## Troubleshooting

### Common Issues

#### No Files Found
```bash
# Check file patterns
fqcn-converter --verbose convert --dry-run

# Use custom patterns
fqcn-converter convert --include "**/*.yml"
```

#### Permission Errors
```bash
# Check file permissions
ls -la *.yml

# Run with appropriate permissions
sudo fqcn-converter convert  # Not recommended
# Better: fix file permissions first
```

#### Configuration Issues
```bash
# Validate configuration file
fqcn-converter --verbose convert --config myconfig.yml --dry-run

# Use default configuration
fqcn-converter convert  # Uses built-in defaults
```

### Debug Mode
```bash
# Enable maximum verbosity for troubleshooting
fqcn-converter --debug convert --dry-run
```

## Best Practices

1. **Always use `--dry-run` first** to preview changes
2. **Keep backups enabled** until you're confident in the results
3. **Test converted playbooks** before committing changes
4. **Use validation** to ensure compliance
5. **Generate reports** for audit trails
6. **Use version control** to track changes

## Next Steps

- **[Python API Guide](api.md)**: Learn to use FQCN Converter programmatically
- **[Configuration Guide](../configuration.md)**: Customize conversion behavior
- **[Examples](../examples/)**: See real-world usage scenarios
- **[Troubleshooting](../troubleshooting.md)**: Solve common issues

---

**Need help?** Check our [FAQ](../faq.md) or [open an issue](https://github.com/mhtalci/ansible_fqcn_converter/issues).