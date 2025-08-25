# Contributing Guidelines

Thank you for your interest in contributing to the FQCN Converter! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Community](#community)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of background, experience level, or identity.

### Expected Behavior

- **Be respectful**: Treat all community members with respect and kindness
- **Be collaborative**: Work together constructively and help others learn
- **Be inclusive**: Welcome newcomers and help them get started
- **Be patient**: Remember that everyone has different experience levels
- **Be constructive**: Provide helpful feedback and suggestions

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Personal attacks or inflammatory language
- Spam, trolling, or disruptive behavior
- Sharing private information without consent
- Any behavior that creates an unwelcoming environment

### Reporting

If you experience or witness unacceptable behavior, please report it to the maintainers at [hello@mehmetalci.com](mailto:hello@mehmetalci.com).

## Getting Started

### Prerequisites

Before contributing, ensure you have:

1. **GitHub Account**: [Create one](https://github.com/join) if you don't have it
2. **Git Knowledge**: Basic understanding of Git workflows
3. **Python Experience**: Familiarity with Python 3.8+ development
4. **Development Environment**: Set up following our [Development Setup Guide](setup.md)

### First Contribution

Looking for your first contribution? Check out:

- [Good First Issues](https://github.com/mhtalci/ansible_fqcn_converter/labels/good%20first%20issue)
- [Help Wanted](https://github.com/mhtalci/ansible_fqcn_converter/labels/help%20wanted)
- [Documentation](https://github.com/mhtalci/ansible_fqcn_converter/labels/documentation)

### Types of Contributions

We welcome various types of contributions:

#### Code Contributions
- **Bug fixes**: Fix reported issues
- **New features**: Implement requested features
- **Performance improvements**: Optimize existing code
- **Refactoring**: Improve code structure and maintainability

#### Documentation
- **User guides**: Improve installation and usage documentation
- **API documentation**: Enhance code documentation and examples
- **Tutorials**: Create learning materials and examples
- **Translation**: Translate documentation to other languages

#### Testing
- **Test coverage**: Add tests for untested code
- **Test improvements**: Enhance existing test quality
- **Performance tests**: Add benchmarking and load tests
- **Integration tests**: Test real-world scenarios

#### Community
- **Issue triage**: Help categorize and prioritize issues
- **User support**: Answer questions and help users
- **Code review**: Review pull requests from other contributors
- **Mentoring**: Help new contributors get started

## Development Process

### Workflow Overview

1. **Fork and Clone**: Fork the repository and clone your fork
2. **Create Branch**: Create a feature branch for your changes
3. **Develop**: Make your changes following our standards
4. **Test**: Ensure all tests pass and add new tests
5. **Document**: Update documentation as needed
6. **Submit**: Create a pull request for review

### Detailed Steps

#### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/fqcn-converter.git
cd fqcn-converter

# Add upstream remote
git remote add upstream https://github.com/mhtalci/ansible_fqcn_converter.git
```

#### 2. Set Up Development Environment

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install development dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install
```

#### 3. Create Feature Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-number-description
```

#### 4. Make Changes

Follow our [code standards](#code-standards) and:

- Write clear, readable code
- Add appropriate comments and docstrings
- Follow existing patterns and conventions
- Keep changes focused and atomic

#### 5. Test Your Changes

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/

# Check test coverage
pytest --cov=fqcn_converter --cov-report=html

# Run quality checks
flake8 src tests
black --check src tests
mypy src
```

#### 6. Commit Changes

Use clear, descriptive commit messages following [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Stage your changes
git add .

# Commit with descriptive message
git commit -m "feat: add support for custom validation rules

- Add CustomValidator abstract base class
- Implement plugin system for validators
- Add comprehensive tests for validator plugins
- Update documentation with plugin examples

Closes #123"
```

**Commit Message Format**:
```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

#### 7. Push and Create Pull Request

```bash
# Push feature branch
git push origin feature/your-feature-name

# Create pull request on GitHub
# Fill out the PR template completely
```

## Code Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

#### Formatting
- **Line length**: 88 characters (Black default)
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings, single quotes for string literals in code
- **Imports**: Organized using isort with Black profile

#### Code Quality Tools

We use automated tools to maintain code quality:

```bash
# Code formatting
black src tests

# Import sorting
isort src tests

# Linting
flake8 src tests

# Type checking
mypy src

# Security scanning
bandit -r src
```

#### Configuration Files

Our quality tools are configured in:
- `pyproject.toml`: Black, isort, pytest configuration
- `.flake8`: Flake8 linting rules
- `mypy.ini`: MyPy type checking configuration
- `.pre-commit-config.yaml`: Pre-commit hook configuration

### Code Structure

#### File Organization
```python
"""
Module docstring describing the module's purpose.

This module provides functionality for...
"""

# Standard library imports
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Third-party imports
import yaml
import click

# Local imports
from ..config.manager import ConfigurationManager
from ..exceptions import ConversionError
from ..utils.logging import get_logger

# Module-level constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# Module-level variables
logger = get_logger(__name__)
```

#### Class Structure
```python
class ExampleClass:
    """
    Brief description of the class.
    
    Longer description explaining the class purpose,
    usage patterns, and important considerations.
    
    Attributes:
        public_attr: Description of public attribute
        
    Example:
        >>> example = ExampleClass()
        >>> result = example.method()
    """
    
    def __init__(self, param: str) -> None:
        """
        Initialize the class.
        
        Args:
            param: Description of parameter
            
        Raises:
            ValueError: If param is invalid
        """
        self._private_attr = param
        self.public_attr = self._process_param(param)
    
    def public_method(self, arg: int) -> str:
        """
        Public method with clear documentation.
        
        Args:
            arg: Description of argument
            
        Returns:
            Description of return value
            
        Raises:
            TypeError: If arg is not an integer
        """
        return self._private_method(arg)
    
    def _private_method(self, arg: int) -> str:
        """Private method for internal use."""
        return str(arg)
```

#### Function Structure
```python
def example_function(
    required_param: str,
    optional_param: Optional[int] = None,
    *args: Any,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Brief description of the function.
    
    Longer description explaining the function's purpose,
    behavior, and any important considerations.
    
    Args:
        required_param: Description of required parameter
        optional_param: Description of optional parameter
        *args: Variable positional arguments
        **kwargs: Variable keyword arguments
        
    Returns:
        Dictionary containing the results with keys:
        - 'success': Boolean indicating success
        - 'data': The processed data
        
    Raises:
        ValueError: If required_param is empty
        TypeError: If optional_param is not an integer
        
    Example:
        >>> result = example_function("test", optional_param=42)
        >>> print(result['success'])
        True
    """
    if not required_param:
        raise ValueError("required_param cannot be empty")
    
    # Implementation here
    return {"success": True, "data": processed_data}
```

### Type Hints

Use comprehensive type hints for all public APIs:

```python
from typing import Dict, List, Optional, Union, Any, Callable, TypeVar, Generic

# Type aliases for clarity
FilePath = Union[str, Path]
MappingDict = Dict[str, str]
ProgressCallback = Callable[[int, int, str], None]

# Generic types
T = TypeVar('T')

class Container(Generic[T]):
    def __init__(self, item: T) -> None:
        self.item = item
    
    def get_item(self) -> T:
        return self.item
```

### Error Handling

Follow our exception hierarchy and provide actionable error messages:

```python
try:
    result = risky_operation()
except SpecificError as e:
    # Handle specific error with recovery
    logger.warning(f"Operation failed: {e}")
    result = fallback_operation()
except Exception as e:
    # Handle unexpected errors
    logger.error(f"Unexpected error: {e}")
    raise ConversionError(
        "Operation failed unexpectedly",
        details=str(e),
        suggestions=["Check input parameters", "Verify file permissions"],
        recovery_actions=["Retry with different parameters"]
    ) from e
```

## Testing Requirements

### Test Coverage

- **Minimum coverage**: 95% for new code
- **Critical paths**: 100% coverage for core conversion logic
- **Edge cases**: Comprehensive testing of error conditions
- **Integration**: End-to-end workflow testing

### Test Categories

#### Unit Tests
```python
# tests/unit/test_converter.py
import pytest
from unittest.mock import Mock, patch
from fqcn_converter import FQCNConverter, ConversionError

class TestFQCNConverter:
    """Test suite for FQCNConverter class."""
    
    def test_convert_content_success(self):
        """Test successful content conversion."""
        converter = FQCNConverter()
        content = "- package: {name: nginx}"
        
        result = converter.convert_content(content)
        
        assert result.success
        assert result.changes_made == 1
        assert "ansible.builtin.package" in result.converted_content
    
    def test_convert_content_invalid_yaml(self):
        """Test handling of invalid YAML content."""
        converter = FQCNConverter()
        content = "invalid: yaml: content:"
        
        result = converter.convert_content(content)
        
        assert not result.success
        assert len(result.errors) > 0
    
    @pytest.mark.parametrize("module_name,expected_fqcn", [
        ("copy", "ansible.builtin.copy"),
        ("service", "ansible.builtin.service"),
        ("package", "ansible.builtin.package"),
    ])
    def test_builtin_module_conversion(self, module_name, expected_fqcn):
        """Test conversion of built-in modules."""
        converter = FQCNConverter()
        content = f"- {module_name}: {{name: test}}"
        
        result = converter.convert_content(content)
        
        assert result.success
        assert expected_fqcn in result.converted_content
```

#### Integration Tests
```python
# tests/integration/test_end_to_end.py
import tempfile
import os
from pathlib import Path
from fqcn_converter import FQCNConverter

class TestEndToEnd:
    """End-to-end integration tests."""
    
    def test_complete_playbook_conversion(self):
        """Test complete playbook conversion workflow."""
        playbook_content = """
---
- name: Web server setup
  hosts: webservers
  tasks:
    - name: Install nginx
      package:
        name: nginx
        state: present
    
    - name: Start nginx
      service:
        name: nginx
        state: started
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(playbook_content)
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
            
            # Verify converted content
            with open(temp_file, 'r') as f:
                converted_content = f.read()
            
            assert "ansible.builtin.package" in converted_content
            assert "ansible.builtin.service" in converted_content
            
        finally:
            os.unlink(temp_file)
            backup_file = temp_file + ".fqcn_backup"
            if os.path.exists(backup_file):
                os.unlink(backup_file)
```

#### Performance Tests
```python
# tests/performance/test_benchmarks.py
import pytest
import time
from fqcn_converter import FQCNConverter

class TestPerformance:
    """Performance benchmarking tests."""
    
    def test_large_file_conversion_performance(self):
        """Test conversion performance with large files."""
        # Generate large playbook content
        large_content = self._generate_large_playbook(1000)  # 1000 tasks
        
        converter = FQCNConverter()
        start_time = time.time()
        
        result = converter.convert_content(large_content)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert result.success
        assert processing_time < 5.0  # Should complete within 5 seconds
        
    @pytest.mark.benchmark
    def test_conversion_benchmark(self, benchmark):
        """Benchmark conversion performance."""
        converter = FQCNConverter()
        content = "- package: {name: nginx}"
        
        result = benchmark(converter.convert_content, content)
        
        assert result.success
```

### Test Fixtures

Create reusable test data and utilities:

```python
# tests/conftest.py
import pytest
import tempfile
import os
from pathlib import Path
from fqcn_converter import FQCNConverter

@pytest.fixture
def sample_converter():
    """Provide a configured converter for testing."""
    return FQCNConverter()

@pytest.fixture
def temp_playbook():
    """Create a temporary playbook file."""
    content = """
---
- name: Test playbook
  hosts: localhost
  tasks:
    - package: {name: nginx}
    - service: {name: nginx, state: started}
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write(content)
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)
    backup_file = temp_file + ".fqcn_backup"
    if os.path.exists(backup_file):
        os.unlink(backup_file)

@pytest.fixture
def sample_mappings():
    """Provide sample FQCN mappings for testing."""
    return {
        "test_module": "test.collection.test_module",
        "custom_module": "custom.collection.custom_module"
    }
```

## Documentation

### Documentation Standards

#### Code Documentation
- **Docstrings**: All public classes, methods, and functions must have docstrings
- **Type hints**: Use comprehensive type hints for all public APIs
- **Examples**: Include usage examples in docstrings
- **Parameters**: Document all parameters, return values, and exceptions

#### User Documentation
- **Clear language**: Write for users of all experience levels
- **Examples**: Provide practical, working examples
- **Screenshots**: Include screenshots for UI-related documentation
- **Updates**: Keep documentation synchronized with code changes

#### API Documentation
- **Comprehensive**: Document all public APIs
- **Auto-generated**: Use tools to generate API docs from code
- **Interactive**: Provide interactive examples where possible
- **Versioned**: Maintain documentation for different versions

### Documentation Tools

We use these tools for documentation:

- **Sphinx**: API documentation generation
- **MkDocs**: User documentation site
- **Context7**: Enhanced documentation with examples
- **Mermaid**: Diagrams and flowcharts

### Writing Guidelines

#### Style Guide
- **Tone**: Professional but friendly
- **Voice**: Active voice preferred
- **Tense**: Present tense for current functionality
- **Clarity**: Short sentences and paragraphs
- **Consistency**: Use consistent terminology

#### Structure
```markdown
# Title (H1)

Brief introduction paragraph explaining the purpose.

## Overview (H2)

More detailed explanation of the topic.

### Subsection (H3)

Specific details and examples.

#### Code Example (H4)

```python
# Code example with comments
example_code()
```

## Next Steps

Links to related documentation.
```

## Pull Request Process

### Before Submitting

Ensure your pull request meets these requirements:

- [ ] **Tests pass**: All existing and new tests pass
- [ ] **Code quality**: Passes all linting and formatting checks
- [ ] **Documentation**: Updated relevant documentation
- [ ] **Changelog**: Added entry to CHANGELOG.md if applicable
- [ ] **Issue reference**: References related issue(s)

### Pull Request Template

Use our PR template to provide complete information:

```markdown
## Description

Brief description of the changes and their purpose.

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Related Issues

Closes #123
Related to #456

## Testing

Describe the tests you ran and how to reproduce them:

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing performed

## Checklist

- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes

## Screenshots (if applicable)

Add screenshots to help explain your changes.

## Additional Notes

Any additional information that reviewers should know.
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs automated tests and quality checks
2. **Code Review**: At least one maintainer reviews the code
3. **Feedback**: Address any feedback or requested changes
4. **Approval**: Maintainer approves the pull request
5. **Merge**: Pull request is merged into the main branch

### Review Criteria

Reviewers will check for:

- **Functionality**: Does the code work as intended?
- **Quality**: Is the code well-written and maintainable?
- **Testing**: Are there adequate tests for the changes?
- **Documentation**: Is documentation updated appropriately?
- **Standards**: Does the code follow project standards?
- **Security**: Are there any security concerns?

## Issue Guidelines

### Reporting Bugs

Use the bug report template and include:

- **Environment**: OS, Python version, package version
- **Steps to reproduce**: Clear, numbered steps
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Error messages**: Complete error messages and stack traces
- **Additional context**: Any other relevant information

### Feature Requests

Use the feature request template and include:

- **Problem description**: What problem does this solve?
- **Proposed solution**: How should it work?
- **Alternatives**: Other solutions you've considered
- **Use cases**: Real-world scenarios where this would be useful
- **Implementation ideas**: Technical approach (if you have ideas)

### Issue Labels

We use these labels to categorize issues:

- **Type**: `bug`, `enhancement`, `documentation`, `question`
- **Priority**: `critical`, `high`, `medium`, `low`
- **Difficulty**: `good first issue`, `help wanted`, `expert needed`
- **Status**: `needs triage`, `in progress`, `blocked`, `ready for review`
- **Component**: `cli`, `core`, `validation`, `batch`, `config`

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and community discussions
- **Discord/Slack**: Real-time chat (link in README)
- **Mailing List**: Announcements and important updates

### Getting Help

If you need help:

1. **Search existing issues**: Your question might already be answered
2. **Check documentation**: Review our comprehensive documentation
3. **Ask in discussions**: Use GitHub Discussions for questions
4. **Join chat**: Connect with the community in real-time
5. **Create an issue**: If you found a bug or have a specific problem

### Recognition

We recognize contributors in several ways:

- **Contributors file**: Listed in CONTRIBUTORS.md
- **Release notes**: Mentioned in release announcements
- **Hall of fame**: Featured on project website
- **Badges**: GitHub achievement badges
- **Swag**: Project stickers and merchandise (for significant contributions)

### Mentorship

We offer mentorship for new contributors:

- **Pairing sessions**: Work with experienced contributors
- **Code reviews**: Detailed feedback on your contributions
- **Learning resources**: Curated list of helpful resources
- **Office hours**: Regular sessions for questions and help

---

Thank you for contributing to the FQCN Converter! Your contributions help make Ansible automation better for everyone. 🚀