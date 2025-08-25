# Installation Guide

This guide provides installation instructions for the FQCN Converter.

## Prerequisites

- **Python 3.8+** (Python 3.9+ recommended)
- **Git** (for GitHub installation)

## Installation Methods

### Standard Installation (Recommended)

```bash
# Install from GitHub (only available method)
pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git

# Verify installation
fqcn-converter --version
```

### Development Installation

```bash
# Clone repository
git clone https://github.com/mhtalci/ansible_fqcn_converter.git
cd ansible_fqcn_converter

# Install in development mode
pip install -e ".[dev]"

# Verify with tests
pytest
```

### Virtual Environment (Recommended)

```bash
# Create and activate virtual environment
python -m venv fqcn-env
source fqcn-env/bin/activate  # Linux/macOS
# fqcn-env\Scripts\activate   # Windows

# Install package
pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git
```

### Using pipx (Isolated CLI)

```bash
# Install pipx
pip install pipx

# Install fqcn-converter
pipx install git+https://github.com/mhtalci/ansible_fqcn_converter.git
```

## Verification

```bash
# Check installation
fqcn-converter --version

# Test basic functionality
fqcn-converter convert --help

# Python API test
python -c "from fqcn_converter import FQCNConverter; print('✓ Success')"
```

## Troubleshooting

### Permission Errors
```bash
# Use user installation
pip install --user git+https://github.com/mhtalci/ansible_fqcn_converter.git
```

### Command Not Found
```bash
# Add to PATH (Linux/macOS)
export PATH="$HOME/.local/bin:$PATH"

# Or use python module syntax
python -m fqcn_converter.cli convert --help
```

### Python Version Issues
```bash
# Use specific Python version
python3.9 -m pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git
```

## Why GitHub-Only?

This project is intentionally distributed only through GitHub for:
- **Security**: Direct source control
- **Transparency**: Verifiable source code
- **Simplicity**: Single distribution channel

## Next Steps

- **[CLI Usage Guide](usage/cli.md)** - Command-line usage
- **[Python API Guide](usage/api.md)** - Programmatic usage
- **[Troubleshooting](troubleshooting.md)** - Common issues

---

**Need help?** Check [GitHub Issues](https://github.com/mhtalci/ansible_fqcn_converter/issues) or [Discussions](https://github.com/mhtalci/ansible_fqcn_converter/discussions).