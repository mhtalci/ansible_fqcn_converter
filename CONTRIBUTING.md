# Contributing to FQCN Converter

[![CI/CD Pipeline](https://github.com/mhtalci/ansible_fqcn_converter/workflows/CI/badge.svg)](https://github.com/mhtalci/ansible_fqcn_converter/actions)
[![Production Ready](https://img.shields.io/badge/status-production--ready-brightgreen)](https://github.com/mhtalci/ansible_fqcn_converter)
[![Test Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/mhtalci/ansible_fqcn_converter/actions)

Thank you for your interest in contributing to the FQCN Converter project! This production-ready tool (v0.1.0) with 277/277 tests passing welcomes contributions from the community.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Process](#contributing-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Community](#community)

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic understanding of Ansible and YAML
- Familiarity with Python packaging and development tools

### Development Setup

1. **Fork and Clone the Repository**
   ```bash
   git clone https://github.com/your-username/ansible_fqcn_converter.git
   cd ansible_fqcn_converter
   ```

2. **Set Up Development Environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install development dependencies
   pip install -e ".[dev]"
   
   # Install pre-commit hooks
   pre-commit install
   ```

3. **Verify Installation**
   ```bash
   # Run tests to ensure everything works (should see 277/277 passing)
   pytest
   
   # Run linting
   flake8 src/ tests/
   
   # Check formatting
   black --check src/ tests/
   
   # Verify CLI works
   fqcn-converter --version
   ```

## Contributing Process

### 1. Choose an Issue

- Look for issues labeled `good first issue` for newcomers
- Check existing issues and discussions before starting work
- Comment on the issue to indicate you're working on it
- For new features, create an issue first to discuss the approach

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 3. Make Changes

- Follow the coding standards outlined below
- Write tests for new functionality
- Update documentation as needed
- Ensure all tests pass locally

### 4. Commit Changes

Use conventional commit messages:

```bash
git commit -m "feat: add support for custom mapping validation"
git commit -m "fix: handle malformed YAML gracefully"
git commit -m "docs: update CLI usage examples"
```

Commit types:
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `style`: Code style changes
- `ci`: CI/CD changes
- `chore`: Maintenance tasks

## Coding Standards

### Python Code Style

- **Formatting**: Use `black` for code formatting
- **Linting**: Follow `flake8` rules with project configuration
- **Type Hints**: Use type hints for all public functions and methods
- **Docstrings**: Use Google-style docstrings for all public APIs

Example:

```python
def convert_file(file_path: str, dry_run: bool = False) -> ConversionResult:
    """Convert a single Ansible file to FQCN format.
    
    Args:
        file_path: Path to the Ansible file to convert.
        dry_run: If True, perform conversion without writing changes.
        
    Returns:
        ConversionResult containing conversion details and status.
        
    Raises:
        ConversionError: If the file cannot be converted.
        FileNotFoundError: If the specified file does not exist.
    """
```

### Code Organization

- Keep functions focused and single-purpose
- Use meaningful variable and function names
- Organize imports: standard library, third-party, local imports
- Maximum line length: 88 characters (black default)

### Error Handling

- Use specific exception types from the project's exception hierarchy
- Provide clear, actionable error messages
- Log errors appropriately with context
- Handle edge cases gracefully

## Testing Guidelines

### Test Structure

```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for workflows
├── fixtures/       # Test data and sample files
└── performance/    # Performance and benchmark tests
```

### Writing Tests

- **Coverage**: Aim for 95%+ test coverage for new code
- **Test Names**: Use descriptive test names that explain the scenario
- **Fixtures**: Use pytest fixtures for reusable test data
- **Mocking**: Mock external dependencies and file system operations

Example test:

```python
def test_convert_file_with_custom_mappings(tmp_path, sample_playbook):
    """Test file conversion with custom FQCN mappings."""
    # Arrange
    config = {"user": "custom.collection.user"}
    converter = FQCNConverter(custom_mappings=config)
    
    # Act
    result = converter.convert_file(sample_playbook)
    
    # Assert
    assert result.success
    assert result.changes_made > 0
    assert "custom.collection.user" in result.converted_content
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/fqcn_converter --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/

# Run performance tests
pytest tests/performance/ -m performance
```

## Documentation

### Types of Documentation

1. **Code Documentation**: Docstrings for all public APIs
2. **User Documentation**: Usage guides and examples
3. **Developer Documentation**: Architecture and setup guides
4. **API Reference**: Auto-generated from docstrings

### Documentation Standards

- Use clear, concise language
- Provide practical examples
- Keep documentation up-to-date with code changes
- Include troubleshooting information for common issues

### Building Documentation

```bash
# Generate API documentation
python scripts/generate_context7_docs.py

# Build documentation site (if applicable)
mkdocs serve
```

## Submitting Changes

### Pull Request Process

1. **Ensure Quality**
   - All tests pass
   - Code coverage meets requirements
   - Linting and formatting checks pass
   - Documentation is updated

2. **Create Pull Request**
   - Use the pull request template
   - Provide clear description of changes
   - Reference related issues
   - Include screenshots for UI changes (if applicable)

3. **Review Process**
   - Address reviewer feedback promptly
   - Keep discussions focused and constructive
   - Update PR based on feedback

### Pull Request Checklist

- [ ] Tests added/updated for new functionality
- [ ] Documentation updated (if applicable)
- [ ] CHANGELOG.md updated (for significant changes)
- [ ] Code follows project style guidelines
- [ ] All CI checks pass
- [ ] PR description clearly explains the changes

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and community discussions
- **Pull Requests**: Code review and collaboration

### Getting Help

- Check existing documentation and issues first
- Use GitHub Discussions for questions
- Be specific when asking for help
- Provide minimal reproducible examples

### Recognition

Contributors are recognized in:
- CHANGELOG.md for significant contributions
- README.md contributors section
- GitHub contributor statistics
- Release notes for major contributions

## Release Process

### Version Management

- Follow semantic versioning (semver)
- Versions are managed automatically based on conventional commits
- Breaking changes require major version bump

### Release Workflow

1. Changes merged to main branch
2. Automated testing and quality checks
3. Version bump and changelog generation
4. GitHub release creation
5. Package distribution (future)

## Security

### Reporting Security Issues

Please report security vulnerabilities privately by:

1. **Email**: Send details to the project maintainers
2. **GitHub Security**: Use GitHub's security advisory feature
3. **Response Time**: We aim to respond within 48 hours

### Security Guidelines

- Never commit secrets or credentials
- Validate all user inputs
- Follow secure coding practices
- Keep dependencies updated

## Questions?

If you have questions not covered in this guide:

1. Check the [documentation](docs/)
2. Search existing [GitHub issues](../../issues)
3. Start a [GitHub discussion](../../discussions)
4. Contact the maintainers

Thank you for contributing to FQCN Converter!