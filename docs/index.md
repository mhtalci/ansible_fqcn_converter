# FQCN Converter Documentation

**Production Ready - All Tests Passing (277/277)**

Welcome to the FQCN Converter documentation. This tool converts Ansible playbooks to use Fully Qualified Collection Names (FQCN) with intelligent conflict resolution and comprehensive validation.

## Quick Start

### Installation
```bash
# Install from GitHub (only available method)
pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git

# Verify installation
fqcn-converter --version
```

### Basic Usage
```bash
# Preview changes
fqcn-converter convert --dry-run

# Convert files
fqcn-converter convert

# Validate results
fqcn-converter validate
```

## Documentation Sections

### User Guides
- **[Installation](installation.md)** - Installation instructions and troubleshooting
- **[CLI Usage](usage/cli.md)** - Command-line interface guide
- **[Python API](usage/api.md)** - Programmatic usage
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

### Examples
- **[Basic Usage](examples/basic_usage.py)** - Python API examples
- **[CLI Examples](usage/cli_examples.sh)** - Command-line examples

### Development
- **[Contributing](development/contributing.md)** - Contribution guidelines
- **[Development Setup](development/setup.md)** - Development environment
- **[Architecture](development/architecture.md)** - Technical architecture

### Reference
- **[API Reference](reference/api.md)** - Complete API documentation
- **[CLI Reference](usage/cli_reference.md)** - Command reference

## Key Features

- **Smart Conversion**: Distinguishes modules from parameters
- **Batch Processing**: Parallel processing of multiple projects
- **Comprehensive Validation**: Built-in validation engine
- **240+ Modules**: Support for major Ansible collections

## Support

- **Issues**: [GitHub Issues](https://github.com/mhtalci/ansible_fqcn_converter/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mhtalci/ansible_fqcn_converter/discussions)

---

*Transform your Ansible projects to FQCN with confidence!*