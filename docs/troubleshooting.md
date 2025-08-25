# Troubleshooting Guide

**Last Updated: August 26, 2025**

This guide helps you diagnose and resolve common issues when using the FQCN Converter.

## Quick Diagnostics

### Check Installation
```bash
# Verify installation
fqcn-converter --version

# Test basic functionality
fqcn-converter convert --help

# Check Python environment
python -c "import fqcn_converter; print('✓ Import successful')"
```

### Enable Debug Mode
```bash
# Maximum verbosity for troubleshooting
fqcn-converter --debug convert --dry-run

# Verbose output with detailed logging
fqcn-converter --verbose convert --dry-run
```

## Installation Issues

### Python Version Compatibility

**Problem**: `fqcn-converter` fails to install or run
```
ERROR: Package requires Python >=3.8
```

**Solution**:
```bash
# Check Python version
python --version

# Use specific Python version
python3.9 -m pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git

# Update Python if needed (Ubuntu/Debian)
sudo apt update && sudo apt install python3.9
```

### Permission Errors

**Problem**: Permission denied during installation
```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied
```

**Solutions**:
```bash
# Option 1: User installation (recommended)
pip install --user fqcn-converter

# Option 2: Virtual environment (recommended)
python -m venv fqcn-env
source fqcn-env/bin/activate  # Linux/macOS
pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git

# Option 3: System installation (not recommended)
sudo pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git
```

### Package Not Found

**Problem**: `fqcn-converter` command not found after installation
```
bash: fqcn-converter: command not found
```

**Solutions**:
```bash
# Check if installed in user directory
python -m pip show fqcn-converter

# Find installation path
python -c "import fqcn_converter; print(fqcn_converter.__file__)"

# Add to PATH (Linux/macOS)
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# Use python -m syntax as alternative
python -m fqcn_converter.cli convert --help
```

### SSL Certificate Issues

**Problem**: SSL certificate verification errors during installation
```
SSL: CERTIFICATE_VERIFY_FAILED
```

**Solutions**:
```bash
# Upgrade certificates
pip install --upgrade certifi

# Use trusted hosts (temporary solution) - Note: This project is GitHub-only
pip install --trusted-host github.com git+https://github.com/mhtalci/ansible_fqcn_converter.git

# Update pip and try again
pip install --upgrade pip
pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git
```

## Runtime Issues

### No Files Found

**Problem**: Converter reports "No files found" in directory with YAML files
```
🔍 Scanning for Ansible files...
📁 Found 0 files to process
```

**Diagnosis**:
```bash
# Check current directory contents
ls -la *.yml *.yaml 2>/dev/null || echo "No YAML files found"

# Check file patterns with debug mode
fqcn-converter --debug convert --dry-run
```

**Solutions**:
```bash
# Specify custom file patterns
fqcn-converter convert --include "*.yml" --include "*.yaml"

# Check subdirectories
fqcn-converter convert --include "**/*.yml"

# Verify you're in the right directory
pwd
ls -la
```

### YAML Parsing Errors

**Problem**: Converter fails to parse YAML files
```
ERROR: Failed to parse YAML file: playbook.yml
yaml.scanner.ScannerError: mapping values are not allowed here
```

**Diagnosis**:
```bash
# Validate YAML syntax manually
python -c "import yaml; yaml.safe_load(open('playbook.yml'))"

# Use yamllint for detailed validation
pip install yamllint
yamllint playbook.yml
```

**Solutions**:
```bash
# Fix YAML syntax errors first
# Common issues:
# - Incorrect indentation
# - Missing colons
# - Unquoted special characters

# Skip problematic files temporarily
fqcn-converter convert --exclude "problematic_file.yml"

# Process files individually to isolate issues
fqcn-converter convert specific_file.yml
```

### Permission Denied on Files

**Problem**: Cannot read or write files during conversion
```
ERROR: Permission denied: /path/to/playbook.yml
```

**Solutions**:
```bash
# Check file permissions
ls -la playbook.yml

# Fix permissions
chmod 644 playbook.yml  # Read/write for owner, read for others

# Check directory permissions
ls -ld /path/to/directory
chmod 755 /path/to/directory  # If needed

# Run with appropriate user permissions
# Avoid using sudo unless absolutely necessary
```

### Backup File Conflicts

**Problem**: Backup files already exist
```
ERROR: Backup file already exists: playbook.yml.fqcn_backup
```

**Solutions**:
```bash
# Remove existing backup files
rm *.fqcn_backup

# Disable backup creation
fqcn-converter convert --no-backup

# Use different backup suffix
fqcn-converter convert --backup-suffix ".backup.$(date +%Y%m%d)"
```

## Configuration Issues

### Invalid Configuration File

**Problem**: Custom configuration file causes errors
```
ERROR: Invalid configuration file: config.yml
```

**Diagnosis**:
```bash
# Validate configuration file syntax
python -c "import yaml; print(yaml.safe_load(open('config.yml')))"

# Check configuration with debug mode
fqcn-converter --debug convert --config config.yml --dry-run
```

**Solutions**:
```bash
# Generate template configuration
fqcn-converter convert --config-template > new_config.yml

# Validate against schema
# Check docs/configuration.md for proper format

# Use default configuration temporarily
fqcn-converter convert  # Uses built-in defaults
```

### Module Mapping Issues

**Problem**: Modules not being converted as expected
```
Module 'custom_module' not found in mappings
```

**Solutions**:
```bash
# Add custom mappings to configuration
cat >> custom_config.yml << EOF
mappings:
  custom_module: "namespace.collection.custom_module"
EOF

# Use custom configuration
fqcn-converter convert --config custom_config.yml

# Check available mappings
fqcn-converter convert --list-mappings
```

## Performance Issues

### Slow Processing

**Problem**: Conversion takes too long on large projects

**Diagnosis**:
```bash
# Profile with verbose output
time fqcn-converter --verbose convert --dry-run

# Check system resources
top
df -h  # Check disk space
```

**Solutions**:
```bash
# Use batch processing for multiple projects
fqcn-converter batch --workers 4 /path/to/projects

# Process smaller chunks
fqcn-converter convert roles/
fqcn-converter convert playbooks/

# Exclude unnecessary files
fqcn-converter convert --exclude "**/test/**" --exclude "**/.git/**"
```

### Memory Issues

**Problem**: Out of memory errors with large files
```
MemoryError: Unable to allocate memory
```

**Solutions**:
```bash
# Process files individually
for file in *.yml; do
    fqcn-converter convert "$file"
done

# Increase system memory or use swap
# Check available memory
free -h

# Use streaming processing (if available)
fqcn-converter convert --stream-processing
```

## Validation Issues

### False Positives

**Problem**: Validator reports issues that aren't actually problems
```
WARNING: 'user' should be 'ansible.builtin.user' at line 15
# But line 15 is actually a parameter, not a module
```

**Solutions**:
```bash
# Use less strict validation
fqcn-converter validate  # Instead of --strict

# Check context around reported line
sed -n '10,20p' playbook.yml  # Show lines 10-20

# Update to latest version (may have improved detection)
pip install --upgrade fqcn-converter
```

### Missing Modules

**Problem**: Validator doesn't recognize valid FQCN modules
```
Unknown module: 'community.general.alternatives'
```

**Solutions**:
```bash
# Update module mappings
pip install --upgrade fqcn-converter

# Add custom mappings
fqcn-converter validate --config custom_mappings.yml

# Check if collection is installed
ansible-galaxy collection list | grep community.general
```

## Integration Issues

### CI/CD Pipeline Failures

**Problem**: FQCN Converter fails in CI/CD environment

**Common Issues and Solutions**:

#### GitHub Actions
```yaml
# Ensure proper Python setup
- name: Setup Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.9'
    
# Install with explicit upgrade
- name: Install FQCN Converter
  run: |
    python -m pip install --upgrade pip
    pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git
    
# Verify installation
- name: Verify Installation
  run: fqcn-converter --version
```

#### Docker Issues
```dockerfile
# Use specific Python version
FROM python:3.9-slim

# Install system dependencies if needed
RUN apt-get update && apt-get install -y git

# Install fqcn-converter from GitHub
RUN pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git

# Verify installation
RUN fqcn-converter --version
```

### Pre-commit Hook Issues

**Problem**: Pre-commit hook fails or is too slow

**Solutions**:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: fqcn-validation
        name: Validate FQCN usage
        entry: fqcn-converter validate --strict
        language: system
        files: \.(yml|yaml)$
        pass_filenames: false
        # Add timeout for large repositories
        timeout: 300
```

## Getting Help

### Collect Debug Information

When reporting issues, include:

```bash
# System information
uname -a
python --version
pip --version

# Package information
pip show fqcn-converter
fqcn-converter --version

# Debug output
fqcn-converter --debug convert --dry-run > debug.log 2>&1
```

### Log Analysis

```bash
# Check for common error patterns
grep -i error debug.log
grep -i warning debug.log
grep -i exception debug.log

# Check file processing
grep "Processing file" debug.log
grep "Converted" debug.log
```

### Create Minimal Reproduction

```bash
# Create minimal test case
mkdir test-case
cd test-case

# Create simple playbook
cat > playbook.yml << EOF
---
- name: Test playbook
  hosts: localhost
  tasks:
    - name: Install package
      package:
        name: nginx
EOF

# Test with minimal case
fqcn-converter --debug convert --dry-run
```

## Common Error Messages

### `ModuleNotFoundError: No module named 'fqcn_converter'`
- **Cause**: Package not installed or wrong Python environment
- **Solution**: Reinstall package or activate correct environment

### `FileNotFoundError: [Errno 2] No such file or directory`
- **Cause**: File path doesn't exist or incorrect working directory
- **Solution**: Check file paths and current directory

### `PermissionError: [Errno 13] Permission denied`
- **Cause**: Insufficient permissions to read/write files
- **Solution**: Fix file permissions or run with appropriate user

### `yaml.scanner.ScannerError: mapping values are not allowed here`
- **Cause**: Invalid YAML syntax in input files
- **Solution**: Fix YAML syntax errors before conversion

### `UnicodeDecodeError: 'utf-8' codec can't decode byte`
- **Cause**: Non-UTF-8 encoded files
- **Solution**: Convert files to UTF-8 encoding

## Prevention Tips

1. **Always use `--dry-run` first** to preview changes
2. **Keep backups enabled** until confident in results
3. **Test in development environment** before production
4. **Use version control** to track changes
5. **Validate YAML syntax** before conversion
6. **Keep the tool updated** for latest fixes
7. **Use virtual environments** to avoid conflicts

## Still Need Help?

If this guide doesn't solve your issue:

1. **Search existing issues**: [GitHub Issues](https://github.com/mhtalci/ansible_fqcn_converter/issues)
2. **Check discussions**: [GitHub Discussions](https://github.com/mhtalci/ansible_fqcn_converter/discussions)
3. **Create new issue**: Include debug information and minimal reproduction case
4. **Join community**: Connect with other users and maintainers

---

**Remember**: When reporting issues, always include your operating system, Python version, package version, and the complete error message with stack trace.