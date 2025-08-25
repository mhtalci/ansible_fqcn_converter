# Development Setup

This guide helps you set up a development environment for contributing to the FQCN Converter.

## Prerequisites

- **Python 3.8+** (Python 3.9+ recommended)
- **Git** for version control
- **IDE**: VS Code or PyCharm recommended

## Quick Setup

### Clone Repository

```bash
# Fork and clone your fork
git clone https://github.com/YOUR_USERNAME/fqcn-converter.git
cd fqcn-converter

# Add upstream remote
git remote add upstream https://github.com/mhtalci/ansible_fqcn_converter.git
```

### Set Up Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install development dependencies
pip install -e ".[dev]"
```

### Set Up Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Test hooks
pre-commit run --all-files
```

### Verify Setup

```bash
# Run tests
pytest

# Check code quality
flake8 src tests
black --check src tests
mypy src
```

## IDE Configuration

### VS Code

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"]
}
```

### PyCharm

1. Open project directory
2. Configure Python interpreter: `.venv/bin/python`
3. Set line length to 88 (Black standard)
4. Enable pytest as default test runner

## Development Workflow

### Create Feature Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

### Make Changes and Test

```bash
# Run tests frequently
pytest tests/unit/test_your_module.py -v

# Run quality checks
black src tests
flake8 src tests
mypy src
```

### Commit and Push

```bash
# Stage and commit changes
git add .
git commit -m "feat: add support for custom module mappings

- Add ConfigurationManager.merge_mappings method
- Update FQCNConverter to accept custom mappings
- Add comprehensive tests

Closes #123"

# Push and create PR
git push origin feature/your-feature-name
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=fqcn_converter --cov-report=html

# Run specific tests
pytest tests/unit/test_converter.py
pytest tests/unit/test_converter.py::test_convert_file
```

### Writing Tests

```python
# tests/unit/test_example.py
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

## Code Quality Tools

```bash
# Format code
black src tests

# Sort imports
isort src tests

# Linting
flake8 src tests

# Type checking
mypy src

# Security check
bandit -r src
```

## Debugging

### VS Code Debugging
1. Set breakpoints in code
2. Press F5 to start debugging
3. Select appropriate configuration

### Command Line Debugging
```bash
# Using pdb
python -m pdb -m fqcn_converter.cli.main convert test.yml

# Add breakpoint in code
import pdb; pdb.set_trace()
```

## Troubleshooting

### Common Issues

```bash
# Import errors - ensure package is installed
pip install -e .

# Test failures - run with verbose output
pytest -vvv --tb=long

# Pre-commit issues - reinstall hooks
pre-commit uninstall
pre-commit install

# Virtual environment issues - recreate
deactivate
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Next Steps

1. Read the [Contributing Guidelines](contributing.md)
2. Look at [Good First Issues](https://github.com/mhtalci/ansible_fqcn_converter/labels/good%20first%20issue)
3. Join the community discussions

---

**Happy coding!** 🚀