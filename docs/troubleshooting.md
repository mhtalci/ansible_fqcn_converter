# Troubleshooting Guide

This guide helps you diagnose and resolve common issues when using the FQCN Converter.

## Quick Diagnostics

```bash
# Verify installation
fqcn-converter --version

# Test basic functionality
fqcn-converter convert --help

# Check Python import
python -c "import fqcn_converter; print('✓ Import successful')"

# Enable debug mode for troubleshooting
fqcn-converter --debug convert --dry-run
```

## Installation Issues

### Python Version Compatibility
```bash
# Check Python version (requires 3.8+)
python --version

# Use specific Python version
python3.9 -m pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git
```

### Permission Errors
```bash
# User installation (recommended)
pip install --user git+https://github.com/mhtalci/ansible_fqcn_converter.git

# Virtual environment (recommended)
python -m venv fqcn-env
source fqcn-env/bin/activate
pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git
```

### Command Not Found
```bash
# Add to PATH
export PATH="$HOME/.local/bin:$PATH"

# Alternative: use python module syntax
python -m fqcn_converter.cli convert --help
```

## Runtime Issues

### No Files Found
```bash
# Check current directory
ls -la *.yml *.yaml

# Use debug mode to see file discovery
fqcn-converter --debug convert --dry-run

# Specify custom patterns
fqcn-converter convert --include "*.yml" --include "*.yaml"
```

### YAML Parsing Errors
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('playbook.yml'))"

# Use yamllint for detailed validation
pip install yamllint
yamllint playbook.yml

# Skip problematic files
fqcn-converter convert --exclude "problematic_file.yml"
```

### Permission Errors
```bash
# Check and fix file permissions
ls -la playbook.yml
chmod 644 playbook.yml

# Check directory permissions
chmod 755 /path/to/directory
```

### Backup File Conflicts
```bash
# Remove existing backups
rm *.fqcn_backup

# Disable backup creation
fqcn-converter convert --no-backup
```

## Configuration Issues

### Invalid Configuration File
```bash
# Validate configuration syntax
python -c "import yaml; print(yaml.safe_load(open('config.yml')))"

# Use debug mode
fqcn-converter --debug convert --config config.yml --dry-run

# Use default configuration
fqcn-converter convert  # Uses built-in defaults
```

### Module Mapping Issues
```bash
# Add custom mappings to configuration
cat >> custom_config.yml << EOF
mappings:
  custom_module: "namespace.collection.custom_module"
EOF

# Use custom configuration
fqcn-converter convert --config custom_config.yml
```

## Performance Issues

### Slow Processing
```bash
# Use batch processing with multiple workers
fqcn-converter batch --workers 4 /path/to/projects

# Process smaller chunks
fqcn-converter convert roles/
fqcn-converter convert playbooks/

# Exclude unnecessary files
fqcn-converter convert --exclude "**/test/**" --exclude "**/.git/**"
```

### Memory Issues
```bash
# Process files individually
for file in *.yml; do
    fqcn-converter convert "$file"
done

# Check available memory
free -h
```

## Validation Issues

### False Positives
```bash
# Use less strict validation
fqcn-converter validate  # Instead of --strict

# Check context around reported line
sed -n '10,20p' playbook.yml  # Show lines 10-20

# Update to latest version
pip install --upgrade git+https://github.com/mhtalci/ansible_fqcn_converter.git
```

### Missing Modules
```bash
# Update module mappings
pip install --upgrade git+https://github.com/mhtalci/ansible_fqcn_converter.git

# Add custom mappings
fqcn-converter validate --config custom_mappings.yml
```

## Integration Issues

### CI/CD Pipeline Failures
```yaml
# GitHub Actions - ensure proper setup
- name: Setup Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'

- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git

- name: Verify Installation
  run: fqcn-converter --version
```

### Pre-commit Hook Issues
```yaml
# .pre-commit-config.yaml - add timeout for large repos
repos:
  - repo: local
    hooks:
      - id: fqcn-validation
        name: Validate FQCN usage
        entry: fqcn-converter validate --strict
        language: system
        files: \.(yml|yaml)$
        timeout: 300
```

## Getting Help

### Debug Information
When reporting issues, include:

```bash
# System and package information
uname -a
python --version
fqcn-converter --version

# Debug output
fqcn-converter --debug convert --dry-run > debug.log 2>&1
```

### Common Error Messages

- **`ModuleNotFoundError: No module named 'fqcn_converter'`**: Package not installed or wrong environment
- **`FileNotFoundError`**: File path doesn't exist or incorrect directory
- **`PermissionError`**: Insufficient permissions to read/write files
- **`yaml.scanner.ScannerError`**: Invalid YAML syntax in input files
- **`UnicodeDecodeError`**: Non-UTF-8 encoded files

## Prevention Tips

1. **Always use `--dry-run` first** to preview changes
2. **Keep backups enabled** until confident in results
3. **Test in development environment** before production
4. **Use version control** to track changes
5. **Validate YAML syntax** before conversion
6. **Keep the tool updated** for latest fixes

## Still Need Help?

1. **Search existing issues**: [GitHub Issues](https://github.com/mhtalci/ansible_fqcn_converter/issues)
2. **Check discussions**: [GitHub Discussions](https://github.com/mhtalci/ansible_fqcn_converter/discussions)
3. **Create new issue**: Include debug information and minimal reproduction case

---

**Remember**: When reporting issues, include your OS, Python version, package version, and complete error messages.