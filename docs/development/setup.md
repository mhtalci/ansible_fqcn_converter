# Development Setup Guide

This guide helps you set up a development environment for contributing to the FQCN Converter project.

## Prerequisites

### System Requirements

- **Python 3.8+** (Python 3.9+ recommended for development)
- **Git** for version control
- **Make** (optional, for convenience commands)

### Recommended Tools

- **VS Code** or **PyCharm** for IDE
- **Docker** (optional, for containerized development)
- **pyenv** or **conda** for Python version management

## Quick Setup

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/mhtalci/ansible_fqcn_converter.git
cd fqcn-converter

# Or fork first and clone your fork
git clone https://github.com/YOUR_USERNAME/fqcn-converter.git
cd fqcn-converter
```

### 2. Set Up Python Environment

#### Option A: Using venv (Recommended)

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

#### Option B: Using conda

```bash
# Create conda environment
conda create -n fqcn-converter python=3.9
conda activate fqcn-converter
```

#### Option C: Using pyenv

```bash
# Install specific Python version
pyenv install 3.9.18
pyenv local 3.9.18

# Create virtual environment
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Development Dependencies

```bash
# Install package in development mode with all dependencies
pip install -e ".[dev]"

# Verify installation
fqcn-converter --version
pytest --version
```

### 4. Set Up Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Test pre-commit hooks
pre-commit run --all-files
```

### 5. Verify Setup

```bash
# Run tests to verify everything works
pytest

# Run linting
flake8 src tests

# Run type checking
mypy src

# Run formatting check
black --check src tests
```

## Detailed Setup

### Development Dependencies

The development installation includes these tools:

#### Testing
- **pytest**: Test framework
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking utilities
- **pytest-xdist**: Parallel test execution

#### Code Quality
- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting and style checking
- **mypy**: Static type checking
- **bandit**: Security analysis

#### Development Tools
- **pre-commit**: Git hooks for quality checks
- **tox**: Testing across multiple environments
- **build**: Package building
- **twine**: Package publishing

### IDE Configuration

#### VS Code

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": [
        "tests"
    ]
}
```

Create `.vscode/launch.json` for debugging:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal"
        },
        {
            "name": "FQCN Converter CLI",
            "type": "python",
            "request": "launch",
            "module": "fqcn_converter.cli.main",
            "args": ["convert", "--dry-run", "test_files/"],
            "console": "integratedTerminal"
        },
        {
            "name": "Run Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/", "-v"],
            "console": "integratedTerminal"
        }
    ]
}
```

#### PyCharm

1. Open the project directory in PyCharm
2. Configure Python interpreter:
   - File → Settings → Project → Python Interpreter
   - Add interpreter → Existing environment
   - Select `.venv/bin/python`
3. Configure code style:
   - File → Settings → Editor → Code Style → Python
   - Set line length to 88 (Black standard)
4. Enable pytest:
   - File → Settings → Tools → Python Integrated Tools
   - Set Default test runner to pytest

### Environment Variables

Create `.env` file for development (optional):

```bash
# Development settings
FQCN_CONVERTER_DEBUG=true
FQCN_CONVERTER_LOG_LEVEL=DEBUG

# Test settings
PYTEST_CURRENT_TEST=true

# Coverage settings
COVERAGE_PROCESS_START=.coveragerc
```

Load with:

```bash
# Install python-dotenv
pip install python-dotenv

# Load in your scripts
from dotenv import load_dotenv
load_dotenv()
```

## Development Workflow

### 1. Create Feature Branch

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-description
```

### 2. Make Changes

```bash
# Make your changes
# Edit files, add features, fix bugs

# Run tests frequently
pytest tests/unit/test_your_module.py -v

# Run specific test
pytest tests/unit/test_converter.py::test_convert_file -v
```

### 3. Quality Checks

```bash
# Format code
black src tests

# Sort imports
isort src tests

# Run linting
flake8 src tests

# Type checking
mypy src

# Security check
bandit -r src

# Run all tests
pytest

# Check coverage
pytest --cov=fqcn_converter --cov-report=html
```

### 4. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add support for custom module mappings

- Add ConfigurationManager.merge_mappings method
- Update FQCNConverter to accept custom mappings
- Add comprehensive tests for mapping functionality
- Update documentation with examples

Closes #123"
```

### 5. Push and Create PR

```bash
# Push feature branch
git push origin feature/your-feature-name

# Create pull request on GitHub
# Fill out PR template with description and testing notes
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=fqcn_converter

# Run specific test file
pytest tests/unit/test_converter.py

# Run specific test
pytest tests/unit/test_converter.py::test_convert_file

# Run tests in parallel
pytest -n auto

# Run tests with verbose output
pytest -v

# Run only failed tests from last run
pytest --lf
```

### Test Categories

```bash
# Unit tests (fast)
pytest tests/unit/

# Integration tests (slower)
pytest tests/integration/

# Performance tests
pytest tests/performance/

# Run tests by marker
pytest -m "not slow"
pytest -m "integration"
```

### Writing Tests

Create test files following the pattern `test_*.py`:

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
    
    def test_convert_content_invalid_yaml(self):
        """Test handling of invalid YAML."""
        converter = FQCNConverter()
        content = "invalid: yaml: content:"
        
        result = converter.convert_content(content)
        
        assert not result.success
        assert len(result.errors) > 0
    
    @pytest.fixture
    def sample_converter(self):
        """Fixture providing a configured converter."""
        return FQCNConverter(custom_mappings={"test": "test.collection.test"})
```

## Code Style and Standards

### Code Formatting

We use **Black** for consistent code formatting:

```bash
# Format all code
black src tests

# Check formatting without changes
black --check src tests

# Format specific file
black src/fqcn_converter/core/converter.py
```

### Import Sorting

We use **isort** with Black compatibility:

```bash
# Sort imports
isort src tests

# Check import sorting
isort --check-only src tests
```

Configuration in `pyproject.toml`:

```toml
[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
```

### Linting

We use **flake8** for linting:

```bash
# Run linting
flake8 src tests

# Show statistics
flake8 --statistics src tests
```

Configuration in `.flake8`:

```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,build,dist,.venv
```

### Type Checking

We use **mypy** for static type checking:

```bash
# Run type checking
mypy src

# Check specific file
mypy src/fqcn_converter/core/converter.py
```

Configuration in `mypy.ini`:

```ini
[mypy]
python_version = 3.8
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

## Debugging

### Using Debugger

#### VS Code Debugging

1. Set breakpoints in code
2. Press F5 or use Debug → Start Debugging
3. Select appropriate configuration

#### Command Line Debugging

```bash
# Using pdb
python -m pdb -m fqcn_converter.cli.main convert test.yml

# Using ipdb (install with: pip install ipdb)
python -c "import ipdb; ipdb.set_trace()" -m fqcn_converter.cli.main
```

#### Adding Debug Points

```python
# Add to code for debugging
import pdb; pdb.set_trace()

# Or with ipdb
import ipdb; ipdb.set_trace()

# Or with breakpoint() (Python 3.7+)
breakpoint()
```

### Logging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
export FQCN_CONVERTER_LOG_LEVEL=DEBUG
```

### Performance Profiling

```bash
# Profile with cProfile
python -m cProfile -o profile.stats -m fqcn_converter.cli.main convert large_project/

# Analyze profile
python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative').print_stats(20)
"

# Memory profiling (install memory_profiler)
pip install memory_profiler
python -m memory_profiler examples/basic_usage.py
```

## Docker Development

### Development Container

Create `Dockerfile.dev`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy source code
COPY . .

# Install package in development mode
RUN pip install -e .

# Set up git (for pre-commit)
RUN git config --global --add safe.directory /app

CMD ["bash"]
```

Build and run:

```bash
# Build development image
docker build -f Dockerfile.dev -t fqcn-converter:dev .

# Run development container
docker run -it --rm -v $(pwd):/app fqcn-converter:dev

# Run tests in container
docker run --rm -v $(pwd):/app fqcn-converter:dev pytest
```

### Docker Compose for Development

Create `docker-compose.dev.yml`:

```yaml
version: '3.8'

services:
  dev:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - .:/app
      - /app/.venv  # Exclude venv from mount
    working_dir: /app
    command: bash
    stdin_open: true
    tty: true
    environment:
      - PYTHONPATH=/app/src
      - FQCN_CONVERTER_DEBUG=true

  test:
    extends: dev
    command: pytest -v
    profiles: ["test"]

  lint:
    extends: dev
    command: flake8 src tests
    profiles: ["lint"]
```

Usage:

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up dev

# Run tests
docker-compose -f docker-compose.dev.yml run --rm test

# Run linting
docker-compose -f docker-compose.dev.yml run --rm lint
```

## Troubleshooting

### Common Issues

#### Import Errors

```bash
# Ensure package is installed in development mode
pip install -e .

# Check Python path
python -c "import sys; print(sys.path)"

# Verify installation
python -c "import fqcn_converter; print(fqcn_converter.__file__)"
```

#### Test Failures

```bash
# Run tests with more verbose output
pytest -vvv --tb=long

# Run single test with debugging
pytest tests/unit/test_converter.py::test_convert_file -vvv -s

# Clear pytest cache
pytest --cache-clear
```

#### Pre-commit Issues

```bash
# Update pre-commit hooks
pre-commit autoupdate

# Clear pre-commit cache
pre-commit clean

# Reinstall hooks
pre-commit uninstall
pre-commit install
```

#### Virtual Environment Issues

```bash
# Recreate virtual environment
deactivate
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Getting Help

1. **Check existing issues**: [GitHub Issues](https://github.com/mhtalci/ansible_fqcn_converter/issues)
2. **Search discussions**: [GitHub Discussions](https://github.com/mhtalci/ansible_fqcn_converter/discussions)
3. **Ask in development channel**: Join our development chat
4. **Create detailed issue**: Include environment details and error messages

## Next Steps

After setting up your development environment:

1. **Read the [Architecture Guide](architecture.md)** to understand the codebase
2. **Check [Contributing Guidelines](contributing.md)** for contribution process
3. **Look at [Good First Issues](https://github.com/mhtalci/ansible_fqcn_converter/labels/good%20first%20issue)**
4. **Join the community** and introduce yourself

---

**Happy coding!** 🚀