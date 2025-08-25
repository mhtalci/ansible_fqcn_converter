# Installation Guide

**Last Updated: August 26, 2025**

## GitHub-Only Distribution Policy

**IMPORTANT**: This project is intentionally distributed **ONLY** through GitHub and is **NOT** available on PyPI, conda-forge, or any other package repositories.

This policy ensures:
- **Direct source control**: All installations come from the official repository
- **Version transparency**: Users can verify the exact source code being installed
- **Security**: Reduced supply chain attack surface
- **Simplified maintenance**: Single distribution channel to maintain

## Installation Methods

### Method 1: Direct from GitHub (Recommended)

```bash
# Install latest version from main branch
pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git

# Verify installation
fqcn-converter --version
```

### Method 2: Install Specific Version

```bash
# Install specific release tag
pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git@v0.1.0

# Install from specific branch
pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git@feature-branch

# Install from specific commit
pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git@abc1234
```

### Method 3: Development Installation

```bash
# Clone repository
git clone https://github.com/mhtalci/ansible_fqcn_converter.git
cd ansible_fqcn_converter

# Install in development mode
pip install -e ".[dev]"

# Run tests to verify
pytest
```

### Method 4: Using pipx (Isolated Environment)

```bash
# Install pipx if not available
pip install pipx

# Install fqcn-converter in isolated environment
pipx install git+https://github.com/mhtalci/ansible_fqcn_converter.git

# Use the CLI
fqcn-converter --help
```

## Prerequisites

- **Python 3.8+** (Python 3.9+ recommended)
- **pip** (latest version recommended)
- **git** (for cloning repository)

## Verification

After installation, verify that the tool is working correctly:

```bash
# Check version
fqcn-converter --version

# Run help command
fqcn-converter --help

# Test with dry run
fqcn-converter convert --dry-run --help
```

## Troubleshooting

### Common Issues

1. **Git not found**: Ensure git is installed and available in PATH
2. **Permission errors**: Use `--user` flag with pip or use virtual environment
3. **Python version**: Ensure Python 3.8+ is being used

### Alternative Installation Commands

```bash
# Install with user flag (no admin rights needed)
pip install --user git+https://github.com/mhtalci/ansible_fqcn_converter.git

# Install in virtual environment (recommended)
python -m venv fqcn-env
source fqcn-env/bin/activate  # On Windows: fqcn-env\Scripts\activate
pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git
```

## Upgrading

To upgrade to the latest version:

```bash
# Upgrade to latest
pip install --upgrade git+https://github.com/mhtalci/ansible_fqcn_converter.git

# Force reinstall
pip install --force-reinstall git+https://github.com/mhtalci/ansible_fqcn_converter.git
```

## Uninstallation

```bash
# Uninstall the package
pip uninstall fqcn-converter
```

## Why Not PyPI?

This project deliberately avoids PyPI distribution for several reasons:

1. **Security**: Direct GitHub installation reduces supply chain attack vectors
2. **Transparency**: Users can inspect the exact source code being installed
3. **Simplicity**: Single distribution channel reduces maintenance overhead
4. **Control**: Direct control over distribution without third-party dependencies

For enterprise users who require internal package repositories, you can:
1. Fork the repository to your internal Git server
2. Build wheels locally using `python -m build`
3. Host wheels in your internal package index

## Support

If you encounter installation issues:

1. Check the [GitHub Issues](https://github.com/mhtalci/ansible_fqcn_converter/issues)
2. Review the troubleshooting section above
3. Create a new issue with your system details and error messages

---

**Last Updated: August 26, 2025**