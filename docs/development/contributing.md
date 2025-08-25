# Contributing Guidelines

Thank you for your interest in contributing to the FQCN Converter!

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors.

### Expected Behavior
- Be respectful and collaborative
- Welcome newcomers and help them learn
- Provide constructive feedback
- Be patient with different experience levels

### Reporting
Report unacceptable behavior to maintainers at [hello@mehmetalci.com](mailto:hello@mehmetalci.com).

## Getting Started

### Prerequisites
- GitHub account and basic Git knowledge
- Python 3.8+ development experience
- Development environment (see [Setup Guide](setup.md))

### First Contribution
Look for issues labeled:
- [Good First Issues](https://github.com/mhtalci/ansible_fqcn_converter/labels/good%20first%20issue)
- [Help Wanted](https://github.com/mhtalci/ansible_fqcn_converter/labels/help%20wanted)
- [Documentation](https://github.com/mhtalci/ansible_fqcn_converter/labels/documentation)

### Types of Contributions
- **Code**: Bug fixes, new features, performance improvements
- **Documentation**: User guides, API docs, tutorials
- **Testing**: Test coverage, performance tests, integration tests
- **Community**: Issue triage, user support, code review

## Development Process

### Workflow
1. Fork and clone the repository
2. Create a feature branch
3. Make changes following code standards
4. Add tests and update documentation
5. Submit a pull request

### Setup
```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/fqcn-converter.git
cd fqcn-converter

# Set up development environment
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install
```

### Branch Naming
- `feature/description` for new features
- `fix/issue-description` for bug fixes
- `docs/description` for documentation updates

## Code Standards

### Python Style
- Follow PEP 8 with 88-character line length (Black)
- Use type hints for all public APIs
- Write comprehensive docstrings
- Follow existing patterns and conventions

### Quality Tools
```bash
# Format code
black src tests

# Sort imports
isort src tests

# Linting
flake8 src tests

# Type checking
mypy src

# Security scanning
bandit -r src
```

### Commit Messages
Use [Conventional Commits](https://www.conventionalcommits.org/) format:
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat(converter): add support for custom validation rules

- Add CustomValidator abstract base class
- Implement plugin system for validators
- Add comprehensive tests for validator plugins

Closes #123
```

## Testing Requirements

### Test Coverage
- Minimum 95% coverage for new code
- 100% coverage for core conversion logic
- Comprehensive edge case testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=fqcn_converter --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
```

### Writing Tests
```python
import pytest
from fqcn_converter import FQCNConverter

class TestFQCNConverter:
    def test_convert_content_success(self):
        """Test successful content conversion."""
        converter = FQCNConverter()
        content = "- package: {name: nginx}"

        result = converter.convert_content(content)

        assert result.success
        assert result.changes_made == 1
        assert "ansible.builtin.package" in result.converted_content
```

## Documentation

### Standards
- Clear, concise language for all experience levels
- Include practical examples
- Keep documentation synchronized with code
- Use consistent terminology

### API Documentation
- Comprehensive docstrings for all public APIs
- Include usage examples
- Document parameters, return values, and exceptions

## Pull Request Process

### Before Submitting
- [ ] Tests pass and coverage is maintained
- [ ] Code quality checks pass
- [ ] Documentation is updated
- [ ] Commit messages follow conventions

### PR Template
```markdown
## Description
Brief description of changes and their purpose.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added for new functionality
```

### Review Process
1. Automated checks run (CI/CD)
2. Code review by maintainers
3. Address feedback
4. Approval and merge

## Issue Guidelines

### Bug Reports
Include:
- Environment details (OS, Python version)
- Steps to reproduce
- Expected vs actual behavior
- Error messages and stack traces

### Feature Requests
Include:
- Problem description
- Proposed solution
- Use cases and examples
- Implementation ideas (if any)

## Community

### Communication
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community discussions
- **Email**: Direct contact with maintainers

### Recognition
Contributors are recognized through:
- CONTRIBUTORS.md file
- Release notes mentions
- Project website features

---

Thank you for contributing to the FQCN Converter! 🚀