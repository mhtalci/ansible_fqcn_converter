# FQCN Converter Documentation

[![CI/CD Pipeline](https://github.com/mhtalci/ansible_fqcn_converter/workflows/CI/badge.svg)](https://github.com/mhtalci/ansible_fqcn_converter/actions)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Test Coverage](https://img.shields.io/badge/coverage-86.17%25-brightgreen)](https://github.com/mhtalci/ansible_fqcn_converter/actions)

**Production Ready - All Tests Passing (526/526)**

Welcome to the comprehensive documentation for FQCN Converter, a production-ready tool that converts Ansible playbooks to use Fully Qualified Collection Names (FQCN) with intelligent conflict resolution, comprehensive validation, and robust error handling.

## 🎉 What's New in Latest Release

- ✅ **Comprehensive Test Suite** - 526 tests with 86.17% coverage (420 unit + 92 integration + 14 performance)
- ✅ **Performance Testing** - Automated benchmarks for large files, memory usage, and scaling
- ✅ **Scenario-Based Testing** - Molecule-inspired test patterns for real-world workflows
- ✅ **Code Quality Excellence** - All linting issues resolved, full type annotations, consistent formatting
- ✅ **Smart Conflict Resolution** - Correctly handles parameters vs modules with 100% accuracy
- ✅ **Batch Processing** - Efficient parallel processing of multiple projects
- ✅ **Memory Optimized** - Performance validated with automated memory efficiency tests
- ✅ **Production Quality** - Enterprise-grade code quality with comprehensive validation

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
# Preview changes (always recommended first)
fqcn-converter convert --dry-run

# Convert files in current directory
fqcn-converter convert

# Convert specific directory
fqcn-converter convert /path/to/ansible/project

# Validate results
fqcn-converter validate

# Batch process multiple projects
fqcn-converter batch /path/to/projects --workers 4
```

## Documentation Sections

### 📚 User Guides
- **[Installation Guide](installation.md)** - Installation instructions and troubleshooting
- **[Migration Guide](migration-guide.md)** - Complete migration process from start to finish
- **[CLI Usage Guide](usage/cli.md)** - Command-line interface comprehensive guide
- **[Advanced Usage Guide](usage/advanced-usage.md)** - Enterprise patterns and complex scenarios
- **[Python API Guide](usage/api.md)** - Programmatic usage and integration
- **[Troubleshooting Guide](troubleshooting.md)** - Common issues and solutions
- **[FAQ](faq.md)** - Frequently asked questions and answers

### 💡 Examples and Tutorials
- **[Basic Usage Examples](examples/basic_usage.py)** - Python API examples with error handling
- **[CLI Examples](usage/cli_examples.sh)** - Interactive command-line examples
- **[Migration Scenarios](migration-guide.md#common-migration-scenarios)** - Real-world migration examples

### 🔧 Development and Contributing
- **[Contributing Guidelines](development/contributing.md)** - How to contribute to the project
- **[Development Setup](development/setup.md)** - Setting up development environment
- **[Architecture Overview](development/architecture.md)** - Technical architecture and design
- **[Testing Strategy](development/testing-strategy.md)** - Comprehensive testing approach and best practices
- **[Performance Guide](development/performance.md)** - Performance benchmarks, optimization, and monitoring
- **[Release Process](development/release-process.md)** - Release management and versioning

### 📖 Reference Documentation
- **[API Reference](reference/api.md)** - Complete Python API documentation
- **[CLI Reference](usage/cli_reference.md)** - Complete command-line reference
- **[Configuration Reference](usage/cli_reference.md#configuration)** - Configuration options and examples

### 🔒 Security and Deployment
- **[Security Guide](security/security-guide.md)** - Comprehensive security documentation
- **[Deployment Guide](deployment/deployment-guide.md)** - Production deployment patterns

### 🌟 Community and Support
- **[Community Guidelines](community/feedback-integration.md)** - Community feedback and integration
- **[Support Channels](faq.md#community-and-support)** - Getting help and support

## ✨ Key Features

### 🎯 **Smart FQCN Conversion**
- **Intelligent Detection**: Automatically identifies and converts 240+ Ansible modules to FQCN format
- **Context-Aware Processing**: Distinguishes between module declarations and parameters with 100% accuracy
- **Collection Support**: Covers `ansible.builtin`, `community.general`, `community.docker`, and more
- **Safe Operations**: Creates backups and provides rollback capabilities

### 🛠️ **Multiple Usage Patterns**
- **CLI Tools**: Command-line interface for interactive and automated workflows
- **Python Package**: Import and use as a library in your Python applications
- **Batch Processing**: Process multiple Ansible projects with parallel execution
- **CI/CD Integration**: Seamlessly integrate into your automation pipelines

### 🔒 **Production-Ready Quality**
- **Comprehensive Testing**: 526 tests with 86.17% coverage including unit, integration, and performance tests
- **Performance Validation**: Automated benchmarks for large files (500+ tasks), memory usage, and scaling
- **Scenario-Based Testing**: Molecule-inspired test patterns covering real-world workflows
- **Type Safety**: Full type hints and static analysis with mypy (all issues resolved)
- **Code Quality**: All linting issues fixed, consistent Black formatting, organized imports
- **Error Handling**: Robust exception handling with detailed error messages
- **Logging**: Configurable logging with structured output options

### 📚 **Developer Experience**
- **Rich Documentation**: Comprehensive guides, API reference, and examples
- **Modern Python**: Built with Python 3.8+ using modern packaging standards
- **Extensible**: Plugin architecture for custom conversion rules
- **Standards Compliant**: Follows PEP 8, Black formatting, and Ansible best practices

## Support

- **Issues**: [GitHub Issues](https://github.com/mhtalci/ansible_fqcn_converter/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mhtalci/ansible_fqcn_converter/discussions)

---

*Transform your Ansible projects to FQCN with confidence!*