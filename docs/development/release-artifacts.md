# Release Artifacts

This document describes the artifacts generated for each FQCN Converter release and their validation processes.

## Artifact Types

### Source Distribution (sdist)
**File**: `fqcn-converter-{VERSION}.tar.gz`

**Contents**:
- Complete source code
- Configuration files
- Documentation
- Tests
- Build scripts and metadata

**Generation**:
```bash
python -m build --sdist
```

### Wheel Distribution (bdist_wheel)
**File**: `fqcn_converter-{VERSION}-py3-none-any.whl`

**Contents**:
- Compiled Python packages
- Package metadata
- Entry points
- Dependencies specification

**Generation**:
```bash
python -m build --wheel
```

### Documentation Archive
**File**: `fqcn-converter-docs-{VERSION}.tar.gz`

**Contents**:
- Complete HTML documentation
- API reference
- User guides
- Examples and tutorials

**Generation**:
```bash
sphinx-build -b html docs docs/_build/html
tar -czf fqcn-converter-docs-{VERSION}.tar.gz -C docs/_build html
```

### Release Notes
**File**: `RELEASE_NOTES_v{VERSION}.md`

**Contents**:
- Formatted release notes
- Migration guides (for breaking changes)
- Installation instructions
- Acknowledgments

### Checksums and Signatures
**Files**:
- `SHA256SUMS`: SHA256 checksums for all artifacts
- `SHA256SUMS.asc`: GPG signature of checksums file (if available)

**Generation**:
```bash
sha256sum *.tar.gz *.whl > SHA256SUMS
gpg --armor --detach-sign SHA256SUMS  # If GPG key available
```

## Validation Process

### Automated Validation

#### Package Validation
```bash
# Validate wheel format
python -m wheel unpack fqcn_converter-{VERSION}-py3-none-any.whl
python -c "import fqcn_converter; print(fqcn_converter.__version__)"

# Validate source distribution
tar -tzf fqcn-converter-{VERSION}.tar.gz | head -20
```

#### Installation Testing
```bash
# Test installation in clean environment
python -m venv test_env
source test_env/bin/activate
pip install dist/fqcn_converter-{VERSION}-py3-none-any.whl

# Test CLI functionality
fqcn-converter --version
fqcn-converter --help

# Test Python API
python -c "
from fqcn_converter import FQCNConverter
converter = FQCNConverter()
print('API import successful')
"
```

#### Metadata Validation
```bash
# Check package metadata
python -m twine check dist/*

# Validate pyproject.toml
python -c "
import tomllib
with open('pyproject.toml', 'rb') as f:
    config = tomllib.load(f)
print('pyproject.toml is valid')
"
```

### Manual Validation Checklist

#### Pre-Release Checklist
- [ ] Version numbers are consistent across all files
- [ ] CHANGELOG.md is updated with release notes
- [ ] All tests pass in CI/CD pipeline
- [ ] Documentation builds without errors
- [ ] Security scan shows no critical issues
- [ ] Performance benchmarks are acceptable

#### Artifact Quality Checklist
- [ ] Source distribution includes all necessary files
- [ ] Wheel distribution installs and imports correctly
- [ ] Documentation is complete and accurate
- [ ] Release notes are comprehensive
- [ ] All links in documentation work
- [ ] Examples in documentation execute successfully

## Distribution Channels

### GitHub Releases
**Primary Distribution Channel**

All release artifacts are attached to GitHub releases:
- Source and wheel distributions
- Documentation archives
- Release notes
- Checksums and signatures

**Access**: `https://github.com/mhtalci/ansible_fqcn_converter/releases/tag/v{VERSION}`

### Documentation Hosting
**GitHub Pages**

Documentation is automatically deployed to GitHub Pages:
- Latest version at root path
- Versioned documentation in subdirectories
- API reference and user guides

## Artifact Verification

### For Users
```bash
# Download release artifacts
wget https://github.com/mhtalci/ansible_fqcn_converter/releases/download/v{VERSION}/fqcn_converter-{VERSION}-py3-none-any.whl
wget https://github.com/mhtalci/ansible_fqcn_converter/releases/download/v{VERSION}/SHA256SUMS

# Verify checksum
sha256sum -c SHA256SUMS --ignore-missing
```

### For Developers
```bash
# Clone repository at release tag
git clone --branch v{VERSION} https://github.com/mhtalci/ansible_fqcn_converter.git
cd ansible-fqcn-converter

# Reproduce build
python -m build

# Compare with released artifacts
sha256sum dist/* > local_checksums.txt
diff local_checksums.txt SHA256SUMS
```

## Automation Scripts

### Build Script
```bash
#!/bin/bash
# scripts/build_release.sh

VERSION=$1
echo "Building release artifacts for version $VERSION"

# Clean previous builds
rm -rf dist/ build/

# Build packages
python -m build

# Build documentation
sphinx-build -b html docs docs/_build/html
tar -czf "fqcn-converter-docs-$VERSION.tar.gz" -C docs/_build html

# Generate checksums
sha256sum dist/* *.tar.gz > SHA256SUMS

echo "Release artifacts built successfully"
```

### Validation Script
```bash
#!/bin/bash
# scripts/validate_release.sh

VERSION=$1
echo "Validating release artifacts for version $VERSION"

# Validate packages
python -m twine check dist/*

# Test installation
python -m venv temp_test_env
source temp_test_env/bin/activate
pip install "dist/fqcn_converter-$VERSION-py3-none-any.whl"

# Test functionality
fqcn-converter --version | grep "$VERSION"
python -c "import fqcn_converter; assert fqcn_converter.__version__ == '$VERSION'"

# Cleanup
deactivate
rm -rf temp_test_env

# Verify checksums
sha256sum -c SHA256SUMS

echo "All validations passed for version $VERSION"
```

## Security Considerations

### Artifact Integrity
- All artifacts include SHA256 checksums
- GPG signatures for critical releases
- Reproducible builds when possible
- Secure distribution channels

### Access Control
- Release creation requires maintainer permissions
- Artifact signing uses protected keys
- Distribution channels use secure protocols
- Audit trail for all release activities

## Troubleshooting

### Common Build Issues
```bash
# Build fails with missing dependencies
pip install build twine sphinx

# Documentation build fails
sphinx-build -W -b html docs docs/_build/html

# Wheel validation fails
python -m wheel unpack dist/*.whl
```

### Validation Failures
```bash
# Checksum mismatch
rm -rf dist/ && python -m build
sha256sum dist/* > SHA256SUMS

# Import test fails
pip install --force-reinstall dist/*.whl
python -c "import fqcn_converter"
```

---

This artifact system ensures that every release is properly validated, documented, and distributed with full traceability and verification capabilities.