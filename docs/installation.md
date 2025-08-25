# Installation Guide

🎉 **Production Ready - All Tests Passing (277/277)**

This guide provides comprehensive installation instructions for the production-ready FQCN Converter across different environments and use cases.

## System Requirements

### Minimum Requirements
- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, or Windows
- **Memory**: 512 MB RAM
- **Disk Space**: 50 MB for installation

### Recommended Requirements
- **Python**: 3.9 or higher
- **Memory**: 1 GB RAM (for large projects)
- **Disk Space**: 100 MB (including development dependencies)

## Installation Methods

### 1. GitHub Installation (Only Available Method)

**Updated: August 26, 2025**

FQCN Converter is only available for installation directly from GitHub and is NOT published on PyPI or other package repositories:

```bash
# Install latest version from GitHub
pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git

# Install specific version/tag
pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git@v0.1.0

# Upgrade to latest version
pip install --upgrade git+https://github.com/mhtalci/ansible_fqcn_converter.git
```

#### Verify Installation
```bash
# Check version
fqcn-converter --version

# Run help to see available commands
fqcn-converter --help

# Test with a simple command
fqcn-converter convert --help
```

### 2. Development Installation

For contributors or users who want the latest features:

```bash
# Clone the repository
git clone https://github.com/mhtalci/ansible_fqcn_converter.git
cd fqcn-converter

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Verify installation by running tests
pytest
```

#### Development Dependencies
The development installation includes additional tools:
- **pytest**: Testing framework
- **black**: Code formatting
- **flake8**: Linting
- **mypy**: Type checking
- **pre-commit**: Git hooks

### 3. Virtual Environment Installation

Recommended for isolated environments:

```bash
# Create virtual environment
python -m venv fqcn-env

# Activate virtual environment
# On Linux/macOS:
source fqcn-env/bin/activate
# On Windows:
fqcn-env\Scripts\activate

# Install fqcn-converter from GitHub
pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git

# Deactivate when done
deactivate
```

### 4. pipx Installation (Isolated CLI)

For users who only need the CLI tools:

```bash
# Install pipx if not already installed
pip install pipx

# Install fqcn-converter in isolated environment from GitHub
pipx install git+https://github.com/mhtalci/ansible_fqcn_converter.git

# Use the CLI directly
fqcn-converter --help

# Upgrade when needed
pipx upgrade fqcn-converter
```

### 5. GitHub Installation

Install directly from GitHub repository:

```bash
# Install from main branch (latest development)
pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git

# Install from specific tag/release
pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git@v0.1.0

# Install from specific branch
pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git@feature-branch
```

### 6. Docker Installation

For containerized environments:

```bash
# Pull the official image
docker pull your-org/fqcn-converter:latest

# Run with volume mount
docker run -v $(pwd):/workspace your-org/fqcn-converter:latest convert /workspace

# Use docker-compose for development
curl -O https://raw.githubusercontent.com/your-org/fqcn-converter/main/docker-compose.yml
docker-compose up fqcn-converter
```

## Platform-Specific Instructions

### Linux

#### Ubuntu/Debian
```bash
# Update package list
sudo apt update

# Install Python and pip if not already installed
sudo apt install python3 python3-pip

# Install fqcn-converter
pip3 install fqcn-converter
```

#### CentOS/RHEL/Fedora
```bash
# Install Python and pip
sudo dnf install python3 python3-pip  # Fedora
# or
sudo yum install python3 python3-pip  # CentOS/RHEL

# Install fqcn-converter
pip3 install fqcn-converter
```

#### Arch Linux
```bash
# Install Python and pip
sudo pacman -S python python-pip

# Install fqcn-converter from GitHub
pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git
```

### macOS

#### Using Homebrew (Recommended)
```bash
# Install Python if not already installed
brew install python

# Install fqcn-converter
pip3 install fqcn-converter
```

#### Using System Python
```bash
# Install fqcn-converter (may require --user flag)
pip3 install --user fqcn-converter

# Add to PATH if needed
echo 'export PATH="$HOME/Library/Python/3.x/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Windows

#### Using Python from python.org
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Install Python (ensure "Add to PATH" is checked)
3. Open Command Prompt or PowerShell:
```cmd
# Install fqcn-converter from GitHub
pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git
```

#### Using Windows Subsystem for Linux (WSL)
```bash
# Install in WSL environment from GitHub
pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git

# Use from Windows via WSL
wsl fqcn-converter --help
```

## Dependency Management

### Core Dependencies
The package automatically installs these required dependencies:
- **PyYAML**: YAML file processing
- **click**: Command-line interface framework
- **colorama**: Cross-platform colored terminal output
- **typing-extensions**: Type hints for older Python versions

### Optional Dependencies
Install additional features with:
```bash
# Performance optimizations
pip install "git+https://github.com/mhtalci/ansible_fqcn_converter.git[performance]"

# Development tools
pip install "git+https://github.com/mhtalci/ansible_fqcn_converter.git[dev]"

# All optional dependencies
pip install "git+https://github.com/mhtalci/ansible_fqcn_converter.git[all]"
```

## Verification and Testing

### Basic Verification
```bash
# Check installation
fqcn-converter --version

# Test CLI functionality
fqcn-converter convert --help
fqcn-converter validate --help
fqcn-converter batch --help
```

### Python API Verification
```python
# Test Python import
try:
    from fqcn_converter import FQCNConverter
    print("✓ FQCN Converter imported successfully")
    
    converter = FQCNConverter()
    print("✓ Converter initialized successfully")
except ImportError as e:
    print(f"✗ Import failed: {e}")
```

### Run Test Suite (Development Installation)
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=fqcn_converter

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
```

## Troubleshooting

### Common Issues

#### Permission Errors
```bash
# Use --user flag for user-level installation
pip install --user fqcn-converter

# Or use virtual environment (recommended)
python -m venv myenv
source myenv/bin/activate  # Linux/macOS
# myenv\Scripts\activate   # Windows
pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git
```

#### Python Version Issues
```bash
# Check Python version
python --version

# Use specific Python version
python3.9 -m pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git
```

#### PATH Issues
```bash
# Find where pip installs packages
python -m site --user-base

# Add to PATH (Linux/macOS)
export PATH="$HOME/.local/bin:$PATH"

# Add to PATH (Windows)
set PATH=%APPDATA%\Python\Python39\Scripts;%PATH%
```

#### SSL Certificate Issues
```bash
# Upgrade pip and certificates
pip install --upgrade pip certifi

# Use trusted hosts if needed
pip install --trusted-host pypi.org --trusted-host pypi.python.org fqcn-converter
```

### Getting Help

If you encounter issues not covered here:

1. **Check the logs**: Run with `--verbose` flag for detailed output
2. **Search existing issues**: Check [GitHub Issues](https://github.com/mhtalci/ansible_fqcn_converter/issues)
3. **Create a new issue**: Include your OS, Python version, and error messages
4. **Join discussions**: Use [GitHub Discussions](https://github.com/mhtalci/ansible_fqcn_converter/discussions)

## Uninstallation

### Remove Package
```bash
# Uninstall fqcn-converter
pip uninstall fqcn-converter

# Remove with dependencies (if installed separately)
pip uninstall fqcn-converter PyYAML click colorama
```

### Clean Virtual Environment
```bash
# Remove entire virtual environment
rm -rf fqcn-env  # Linux/macOS
rmdir /s fqcn-env  # Windows
```

### Remove pipx Installation
```bash
# Remove pipx installation
pipx uninstall fqcn-converter
```

## Next Steps

After successful installation:

1. **Read the [CLI Usage Guide](usage/cli.md)** for command-line usage
2. **Check the [Python API Guide](usage/api.md)** for programmatic usage
3. **Review [Configuration Options](configuration.md)** for customization
4. **See [Examples](examples/)** for real-world usage scenarios

---

**Need help?** Check our [Troubleshooting Guide](troubleshooting.md) or [open an issue](https://github.com/mhtalci/ansible_fqcn_converter/issues).