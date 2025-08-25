# CLI Usage Guide

This guide covers the command-line interface functionality of the FQCN Converter.

## Overview

The FQCN Converter provides three main commands:
- **`convert`**: Convert Ansible files to use FQCN format
- **`validate`**: Validate FQCN usage in Ansible files
- **`batch`**: Process multiple Ansible projects in parallel

## Global Options

```bash
fqcn-converter [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

- `--version`: Show version information
- `--verbose, -v`: Enable verbose logging
- `--quiet, -q`: Suppress all output except errors
- `--debug`: Enable debug logging

Global flags can be placed anywhere in the command line:
```bash
fqcn-converter --verbose convert --dry-run
fqcn-converter convert --verbose --dry-run
fqcn-converter convert --dry-run --verbose
```

## Convert Command

Convert Ansible files to use Fully Qualified Collection Names (FQCN).

### Basic Usage

```bash
# Preview changes (recommended first step)
fqcn-converter convert --dry-run

# Apply conversion
fqcn-converter convert

# Convert specific directory
fqcn-converter convert /path/to/ansible/project

# Convert specific files
fqcn-converter convert playbook.yml roles/web/tasks/main.yml
```

### Key Options

- `--dry-run, -n`: Preview changes without modifying files
- `--config, -c PATH`: Use custom configuration file
- `--backup/--no-backup`: Create backup files (default: enabled)
- `--report PATH`: Generate detailed conversion report
- `--include PATTERN`: Include files matching pattern
- `--exclude PATTERN`: Exclude files matching pattern

### Examples

```bash
# Use custom configuration
fqcn-converter convert --config custom_mappings.yml

# Convert without backups
fqcn-converter convert --no-backup

# Generate report
fqcn-converter convert --report conversion_report.json

# Pattern matching
fqcn-converter convert --include "*.yml" --exclude "*test*"
```

## Validate Command

Validate that Ansible files properly use FQCN format.

### Basic Usage

```bash
# Basic validation
fqcn-converter validate

# Strict validation
fqcn-converter validate --strict

# Validate specific directory
fqcn-converter validate /path/to/ansible/project
```

### Key Options

- `--strict`: Use strict validation rules
- `--report PATH`: Generate detailed validation report
- `--config, -c PATH`: Use custom configuration file
- `--format FORMAT`: Output format (text, json, yaml)

### Examples

```bash
# Generate JSON report
fqcn-converter validate --report validation_report.json

# Use custom configuration
fqcn-converter validate --config custom_rules.yml

# JSON output format
fqcn-converter validate --format json
```

## Batch Command

Process multiple Ansible projects in parallel.

### Basic Usage

```bash
# Process all projects in directory
fqcn-converter batch /path/to/ansible/projects

# Preview changes across all projects
fqcn-converter batch --dry-run /path/to/ansible/projects

# Use 8 parallel workers
fqcn-converter batch --workers 8 /path/to/projects
```

### Key Options

- `--workers, -w NUM`: Number of parallel workers (default: 4)
- `--dry-run, -n`: Preview changes without modifying files
- `--config, -c PATH`: Use custom configuration file
- `--report PATH`: Generate detailed batch report
- `--project-pattern PATTERN`: Pattern to identify project directories
- `--exclude-pattern PATTERN`: Pattern to exclude directories

### Examples

```bash
# Custom project pattern
fqcn-converter batch --project-pattern "**/playbooks" /path/to/repos

# Exclude directories
fqcn-converter batch --exclude-pattern "**/archive/**" /path/to/projects

# Full batch with reporting
fqcn-converter batch --workers 6 --config config.yml --report report.json /path/to/projects
```

## Configuration

### Custom Configuration File

```yaml
# fqcn_config.yml
mappings:
  package: "ansible.builtin.package"
  service: "ansible.builtin.service"
  custom_module: "my.collection.custom_module"

patterns:
  include: ["*.yml", "*.yaml"]
  exclude: ["**/test/**", "**/.git/**"]

settings:
  create_backups: true
  strict_mode: false
```

Use with: `fqcn-converter convert --config fqcn_config.yml`

## Integration Examples

### GitHub Actions

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
        run: pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git
      - name: Validate FQCN Usage
        run: fqcn-converter validate --strict
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
```

## Best Practices

1. **Always use `--dry-run` first** to preview changes
2. **Keep backups enabled** until confident in results
3. **Test converted playbooks** before committing
4. **Use validation** to ensure compliance
5. **Generate reports** for audit trails

## Next Steps

- **[Python API Guide](api.md)** - Programmatic usage
- **[CLI Reference](cli_reference.md)** - Complete command reference
- **[Troubleshooting](../troubleshooting.md)** - Common issues

---

**Need help?** Check [GitHub Issues](https://github.com/mhtalci/ansible_fqcn_converter/issues) or [Discussions](https://github.com/mhtalci/ansible_fqcn_converter/discussions).