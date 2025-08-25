# Release Artifacts Documentation

This document describes the artifacts generated for each FQCN Converter release and their validation processes.

## Overview

Each release of FQCN Converter produces a standardized set of artifacts that are validated, signed, and distributed through multiple channels. This ensures users can verify the integrity and authenticity of releases.

## Artifact Types

### 1. Source Distribution (sdist)

**File**: `fqcn-converter-{VERSION}.tar.gz`

**Contents**:
- Complete source code
- Configuration files
- Documentation
- Tests (excluded from wheel)
- Build scripts and metadata

**Generation**:
```bash
python -m build --sdist
```

**Validation**:
- Source completeness check
- License file inclusion
- Metadata validation
- Build reproducibility test

### 2. Wheel Distribution (bdist_wheel)

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

**Validation**:
- Wheel format validation
- Import testing
- Entry point verification
- Dependency resolution check

### 3. Documentation Archive

**File**: `fqcn-converter-docs-{VERSION}.tar.gz`

**Contents**:
- Complete HTML documentation
- API reference
- User guides
- Examples and tutorials

**Generation**:
```bash
# Build documentation
sphinx-build -b html docs docs/_build/html

# Create archive
tar -czf fqcn-converter-docs-{VERSION}.tar.gz -C docs/_build html
```

**Validation**:
- Link checking
- HTML validation
- Content completeness
- Cross-reference verification

### 4. Release Notes

**File**: `RELEASE_NOTES_v{VERSION}.md`

**Contents**:
- Formatted release notes
- Migration guides (for breaking changes)
- Installation instructions
- Acknowledgments

**Generation**:
```bash
python scripts/changelog_generator.py release-notes v{VERSION} --output RELEASE_NOTES_v{VERSION}.md
```

**Validation**:
- Markdown format validation
- Link verification
- Content accuracy review

### 5. Checksums and Signatures

**Files**:
- `SHA256SUMS`: SHA256 checksums for all artifacts
- `SHA256SUMS.asc`: GPG signature of checksums file

**Generation**:
```bash
# Generate checksums
sha256sum *.tar.gz *.whl > SHA256SUMS

# Sign checksums (if GPG key available)
gpg --armor --detach-sign SHA256SUMS
```

**Validation**:
- Checksum verification
- GPG signature validation (if available)
- File integrity confirmation

## Artifact Validation Process

### Automated Validation

The following validations are performed automatically during the build process:

#### 1. Package Validation

```bash
# Validate wheel format
python -m wheel unpack fqcn_converter-{VERSION}-py3-none-any.whl
python -c "import fqcn_converter; print(fqcn_converter.__version__)"

# Validate source distribution
tar -tzf fqcn-converter-{VERSION}.tar.gz | head -20
python -m build --sdist --outdir temp_build/
```

#### 2. Installation Testing

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

#### 3. Metadata Validation

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

Before each release, the following manual validations should be performed:

#### Pre-Release Checklist

- [ ] Version numbers are consistent across all files
- [ ] CHANGELOG.md is updated with release notes
- [ ] All tests pass in CI/CD pipeline
- [ ] Documentation builds without errors
- [ ] Security scan shows no critical issues
- [ ] Performance benchmarks are acceptable
- [ ] Breaking changes are documented
- [ ] Migration guides are complete (if applicable)

#### Artifact Quality Checklist

- [ ] Source distribution includes all necessary files
- [ ] Wheel distribution installs and imports correctly
- [ ] Documentation is complete and accurate
- [ ] Release notes are comprehensive
- [ ] All links in documentation work
- [ ] Examples in documentation execute successfully
- [ ] CLI help text is accurate and complete

#### Distribution Checklist

- [ ] All artifacts are generated successfully
- [ ] Checksums are calculated and verified
- [ ] GPG signatures are created (if applicable)
- [ ] GitHub release is created with all artifacts
- [ ] Documentation is deployed to hosting platform
- [ ] Release announcement is prepared

## Artifact Storage and Distribution

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

**Access**: `https://ansible-fqcn-converter.github.io/`

### Package Registries (Future)

**PyPI (Planned)**

When ready for public distribution:

- Wheel and source distributions
- Automatic installation via pip
- Version history and metadata

**Access**: `https://pypi.org/project/fqcn-converter/`

## Artifact Verification

### For Users

Users can verify artifact integrity using the provided checksums:

```bash
# Download release artifacts
wget https://github.com/mhtalci/ansible_fqcn_converter/releases/download/v{VERSION}/fqcn_converter-{VERSION}-py3-none-any.whl
wget https://github.com/mhtalci/ansible_fqcn_converter/releases/download/v{VERSION}/SHA256SUMS

# Verify checksum
sha256sum -c SHA256SUMS --ignore-missing
```

### For Developers

Developers can verify the complete build process:

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

set -e

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

echo "Building release artifacts for version $VERSION"

# Clean previous builds
rm -rf dist/ build/

# Build packages
python -m build

# Build documentation
sphinx-build -b html docs docs/_build/html
tar -czf "fqcn-converter-docs-$VERSION.tar.gz" -C docs/_build html

# Generate release notes
python scripts/changelog_generator.py release-notes "v$VERSION" --output "RELEASE_NOTES_v$VERSION.md"

# Generate checksums
sha256sum dist/* *.tar.gz *.md > SHA256SUMS

echo "Release artifacts built successfully:"
ls -la dist/ *.tar.gz *.md SHA256SUMS
```

### Validation Script

```bash
#!/bin/bash
# scripts/validate_release.sh

set -e

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

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

## Release Artifact Lifecycle

### Creation Phase

1. **Automated Build**: CI/CD pipeline builds artifacts
2. **Validation**: Automated and manual validation
3. **Signing**: Generate checksums and signatures
4. **Staging**: Upload to staging area for final review

### Distribution Phase

1. **GitHub Release**: Create release with all artifacts
2. **Documentation**: Deploy documentation to hosting
3. **Announcements**: Notify community of new release
4. **Registry**: Upload to package registries (future)

### Maintenance Phase

1. **Monitoring**: Track download statistics and issues
2. **Support**: Provide support for released versions
3. **Security**: Monitor for security issues
4. **Deprecation**: Plan deprecation timeline for old versions

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

### Vulnerability Response

- Process for handling security issues in releases
- Rapid response for critical vulnerabilities
- Clear communication about security updates
- Coordinated disclosure timeline

## Troubleshooting

### Common Build Issues

**Issue**: Build fails with missing dependencies
**Solution**: Ensure all build dependencies are installed
```bash
pip install build twine sphinx
```

**Issue**: Documentation build fails
**Solution**: Check for broken links or missing files
```bash
sphinx-build -W -b html docs docs/_build/html
```

**Issue**: Wheel validation fails
**Solution**: Check package structure and metadata
```bash
python -m wheel unpack dist/*.whl
```

### Validation Failures

**Issue**: Checksum mismatch
**Solution**: Rebuild artifacts and regenerate checksums
```bash
rm -rf dist/ && python -m build
sha256sum dist/* > SHA256SUMS
```

**Issue**: Import test fails
**Solution**: Check package installation and dependencies
```bash
pip install --force-reinstall dist/*.whl
python -c "import fqcn_converter"
```

This comprehensive artifact system ensures that every release is properly validated, documented, and distributed with full traceability and verification capabilities.