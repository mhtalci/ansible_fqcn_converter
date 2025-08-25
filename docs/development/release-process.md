# Release Process Documentation

This document outlines the complete release process for the FQCN Converter project, including version management, quality gates, and deployment procedures.

## Overview

The FQCN Converter follows semantic versioning and uses automated CI/CD pipelines for consistent, reliable releases. Our release process ensures high quality, comprehensive testing, and proper documentation for each release.

## Versioning Strategy

### Semantic Versioning

We follow [Semantic Versioning (SemVer)](https://semver.org/) with the format `MAJOR.MINOR.PATCH`:

- **MAJOR**: Breaking changes that require user action
- **MINOR**: New features that are backward compatible
- **PATCH**: Bug fixes and minor improvements

### Version Examples

```
0.1.0  - Initial production release
0.1.1  - Bug fix release
0.2.0  - New features added
1.0.0  - First stable release with API guarantees
1.1.0  - New features in stable API
2.0.0  - Breaking changes requiring migration
```

### Pre-release Versions

For development and testing:

```
0.2.0-alpha.1  - Alpha release for early testing
0.2.0-beta.1   - Beta release for broader testing
0.2.0-rc.1     - Release candidate for final testing
```

## Release Types

### Patch Releases (0.1.x)

**Purpose**: Bug fixes, security updates, minor improvements

**Criteria**:
- No breaking changes
- No new features
- Backward compatible
- Focused on stability

**Examples**:
- Fix conversion errors
- Improve error messages
- Update dependencies
- Documentation corrections

### Minor Releases (0.x.0)

**Purpose**: New features, enhancements, deprecations

**Criteria**:
- Backward compatible
- New functionality
- Feature enhancements
- Deprecation notices (not removals)

**Examples**:
- New CLI commands
- Additional validation rules
- Performance improvements
- New configuration options

### Major Releases (x.0.0)

**Purpose**: Breaking changes, API redesigns, major features

**Criteria**:
- Breaking changes allowed
- API modifications
- Removal of deprecated features
- Significant architectural changes

**Examples**:
- CLI interface changes
- Configuration format changes
- Removal of deprecated features
- Major API redesign

## Release Schedule

### Regular Schedule

- **Patch releases**: As needed (typically weekly for critical fixes)
- **Minor releases**: Monthly (first Tuesday of each month)
- **Major releases**: Quarterly or as needed for breaking changes

### Emergency Releases

For critical security issues or major bugs:
- **Timeline**: Within 24-48 hours
- **Process**: Expedited review and testing
- **Communication**: Immediate notification to users

## Release Process

### 1. Pre-Release Planning

#### Version Planning Meeting

**Participants**: Maintainers, core contributors
**Frequency**: 2 weeks before minor/major releases
**Agenda**:
- Review planned features and fixes
- Assess breaking changes
- Determine version number
- Set release timeline
- Assign responsibilities

#### Feature Freeze

**Timeline**: 1 week before release
**Actions**:
- No new features merged
- Focus on bug fixes and testing
- Documentation updates
- Release preparation

### 2. Release Preparation

#### Update Version Information

```bash
# Update version in _version.py
# src/fqcn_converter/_version.py
__version__ = "0.2.0"
__version_info__ = (0, 2, 0)

# Update pyproject.toml
[project]
version = "0.2.0"

# Update package metadata
[project]
name = "fqcn-converter"
version = "0.2.0"
description = "Convert Ansible playbooks to use FQCN"
```

#### Update Documentation

```bash
# Update CHANGELOG.md
## [0.2.0] - 2025-01-15

### Added
- New batch processing command
- Custom validation rules support
- Performance improvements

### Changed
- Improved error messages
- Updated CLI help text

### Fixed
- Fixed YAML parsing edge cases
- Resolved configuration loading issues

### Deprecated
- Old configuration format (will be removed in 1.0.0)

# Update README.md
- Version badges
- Installation instructions
- Feature descriptions
- Examples and usage
```

#### Create Release Branch

```bash
# Create release branch
git checkout main
git pull origin main
git checkout -b release/0.2.0

# Make release preparations
git add .
git commit -m "chore: prepare release 0.2.0

- Update version to 0.2.0
- Update CHANGELOG.md
- Update documentation
- Prepare release notes"

git push origin release/0.2.0
```

### 3. Quality Assurance

#### Automated Testing

```bash
# Run comprehensive test suite
pytest tests/ -v --cov=fqcn_converter --cov-report=html

# Run performance tests
pytest tests/performance/ -v

# Run integration tests
pytest tests/integration/ -v

# Run compatibility tests
tox
```

#### Manual Testing

**Test Scenarios**:
1. **Fresh Installation**: Test installation from scratch
2. **Upgrade Testing**: Test upgrade from previous version
3. **CLI Testing**: Test all CLI commands and options
4. **API Testing**: Test Python API functionality
5. **Edge Cases**: Test with various Ansible file formats
6. **Error Handling**: Test error conditions and recovery

**Test Environments**:
- Multiple Python versions (3.8, 3.9, 3.10, 3.11, 3.12)
- Different operating systems (Linux, macOS, Windows)
- Various Ansible versions
- Different project structures

#### Security Review

```bash
# Security scanning
bandit -r src/

# Dependency vulnerability check
safety check

# License compliance check
pip-licenses --format=table

# Code quality review
sonarqube-scanner  # If configured
```

### 4. Release Candidate

#### Create Release Candidate

```bash
# Tag release candidate
git tag -a v0.2.0-rc.1 -m "Release candidate 0.2.0-rc.1"
git push origin v0.2.0-rc.1

# Build and test packages
python -m build
twine check dist/*

# Test installation from built package
pip install dist/fqcn_converter-0.2.0-py3-none-any.whl
```

#### Community Testing

**Duration**: 3-7 days depending on release type
**Process**:
1. Announce RC in community channels
2. Provide testing instructions
3. Collect feedback and bug reports
4. Address critical issues
5. Create new RC if needed

### 5. Final Release

#### Release Approval

**Criteria for Release**:
- [ ] All tests pass
- [ ] No critical bugs reported
- [ ] Documentation is complete and accurate
- [ ] Security review completed
- [ ] Community testing feedback addressed
- [ ] Maintainer approval obtained

#### Create Release

```bash
# Merge release branch to main
git checkout main
git merge release/0.2.0
git push origin main

# Create release tag
git tag -a v0.2.0 -m "Release 0.2.0

## What's New
- New batch processing command for handling multiple projects
- Custom validation rules support for organization-specific requirements
- Significant performance improvements for large projects

## Breaking Changes
None

## Migration Guide
No migration required for this release.

## Full Changelog
See CHANGELOG.md for complete details."

git push origin v0.2.0
```

#### Build and Publish

```bash
# Clean previous builds
rm -rf dist/ build/

# Build packages
python -m build

# Verify packages
twine check dist/*

# Upload to PyPI (production)
twine upload dist/*

# Upload to GitHub Releases
gh release create v0.2.0 \
  --title "FQCN Converter v0.2.0" \
  --notes-file RELEASE_NOTES.md \
  dist/*
```

### 6. Post-Release Activities

#### Update Development Branch

```bash
# Update main branch
git checkout main
git pull origin main

# Create post-release commit
git commit --allow-empty -m "chore: post-release 0.2.0

- Release 0.2.0 completed
- Begin development for 0.3.0"

# Update version for development
# _version.py: __version__ = "0.3.0-dev"
git add .
git commit -m "chore: bump version to 0.3.0-dev"
git push origin main
```

#### Communication

**Announcement Channels**:
- GitHub Releases page
- Project documentation
- Community Discord/Slack
- Mailing list
- Social media
- Ansible community forums

**Announcement Template**:
```markdown
# FQCN Converter v0.2.0 Released! 🎉

We're excited to announce the release of FQCN Converter v0.2.0!

## 🚀 What's New

### New Features
- **Batch Processing**: Process multiple Ansible projects in parallel
- **Custom Validation**: Define organization-specific validation rules
- **Performance Boost**: 3x faster processing for large projects

### Improvements
- Better error messages with actionable suggestions
- Enhanced CLI help and documentation
- Improved YAML parsing reliability

## 📦 Installation

```bash
# Upgrade existing installation
pip install --upgrade fqcn-converter

# Fresh installation
pip install fqcn-converter==0.2.0
```

## 📚 Documentation

- [Installation Guide](docs/installation.md)
- [CLI Usage](docs/usage/cli.md)
- [Python API](docs/usage/api.md)
- [Release Notes](CHANGELOG.md)

## 🙏 Thanks

Special thanks to our contributors: @contributor1, @contributor2, @contributor3

## 🐛 Found an Issue?

Report bugs at: https://github.com/mhtalci/ansible_fqcn_converter/issues

Happy converting! 🔄
```

#### Monitoring

**Post-Release Monitoring**:
- Monitor GitHub issues for bug reports
- Check PyPI download statistics
- Monitor community feedback
- Track performance metrics
- Watch for security alerts

## Release Automation

### GitHub Actions Workflow

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', 3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Run tests
      run: |
        pytest --cov=fqcn_converter --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install build dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    
    - name: Build packages
      run: python -m build
    
    - name: Check packages
      run: twine check dist/*
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: packages
        path: dist/

  publish:
    needs: build
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')
    
    steps:
    - name: Download artifacts
      uses: actions/download-artifact@v3
      with:
        name: packages
        path: dist/
    
    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        password: ${{ secrets.PYPI_API_TOKEN }}
    
    - name: Create GitHub Release
      uses: softprops/action-gh-release@v1
      with:
        files: dist/*
        generate_release_notes: true
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Automated Version Bumping

```bash
# Install bump2version
pip install bump2version

# Configure .bumpversion.cfg
[bumpversion]
current_version = 0.1.0
commit = True
tag = True
tag_name = v{new_version}

[bumpversion:file:src/fqcn_converter/_version.py]
[bumpversion:file:pyproject.toml]

# Bump version
bump2version patch  # 0.1.0 -> 0.1.1
bump2version minor  # 0.1.1 -> 0.2.0
bump2version major  # 0.2.0 -> 1.0.0
```

## Rollback Procedures

### Emergency Rollback

If a critical issue is discovered after release:

#### 1. Immediate Actions

```bash
# Remove problematic release from PyPI (if possible)
# Note: PyPI doesn't allow deletion, only yanking
pip yank fqcn-converter==0.2.0 --reason "Critical bug in conversion logic"

# Create hotfix branch
git checkout v0.1.9  # Last known good version
git checkout -b hotfix/0.1.10

# Apply minimal fix
# ... make necessary changes ...

git commit -m "fix: critical issue in conversion logic"
git tag v0.1.10
git push origin v0.1.10
```

#### 2. Communication

```markdown
# Emergency Notice: FQCN Converter v0.2.0

⚠️ **URGENT**: We've identified a critical issue in v0.2.0 that may cause data loss.

## Immediate Actions Required

1. **Do not upgrade** to v0.2.0 if you haven't already
2. **Downgrade immediately** if you're using v0.2.0:
   ```bash
   pip install fqcn-converter==0.1.9
   ```
3. **Check your conversions** if you used v0.2.0

## What Happened

Brief description of the issue and its impact.

## Resolution

We've released v0.1.10 with a fix. We're working on v0.2.1 with the same fix.

## Timeline

- Issue discovered: 2025-01-15 14:30 UTC
- v0.2.0 yanked: 2025-01-15 15:00 UTC
- v0.1.10 released: 2025-01-15 16:00 UTC
- v0.2.1 ETA: 2025-01-16 12:00 UTC

We apologize for the inconvenience and are implementing additional safeguards.
```

### Rollback Testing

Regular rollback testing ensures procedures work:

```bash
# Test rollback scenarios
1. Install previous version
2. Verify functionality
3. Test upgrade path
4. Verify data integrity
5. Test configuration compatibility
```

## Quality Gates

### Automated Quality Gates

**Pre-Release Gates**:
- [ ] All tests pass (unit, integration, performance)
- [ ] Code coverage ≥ 95%
- [ ] No critical security vulnerabilities
- [ ] No linting errors
- [ ] Documentation builds successfully
- [ ] All dependencies are up to date

**Release Gates**:
- [ ] Manual testing completed
- [ ] Security review approved
- [ ] Documentation review completed
- [ ] Maintainer approval obtained
- [ ] Community testing feedback addressed

### Manual Quality Gates

**Code Review Checklist**:
- [ ] Breaking changes documented
- [ ] Migration guide provided (if needed)
- [ ] Performance impact assessed
- [ ] Security implications reviewed
- [ ] Backward compatibility verified
- [ ] Error handling improved
- [ ] Logging and monitoring adequate

## Metrics and Monitoring

### Release Metrics

**Quality Metrics**:
- Test coverage percentage
- Number of bugs found in testing
- Time from feature freeze to release
- Number of rollbacks required

**Adoption Metrics**:
- Download statistics from PyPI
- GitHub star/fork growth
- Community feedback sentiment
- Issue resolution time

**Performance Metrics**:
- Package size and install time
- Runtime performance benchmarks
- Memory usage patterns
- Startup time measurements

### Monitoring Dashboard

Track key metrics:
- Release frequency and success rate
- Bug discovery rate post-release
- Community engagement metrics
- Security vulnerability response time

## Continuous Improvement

### Release Retrospectives

**After Each Release**:
- What went well?
- What could be improved?
- What should we do differently?
- Process improvements to implement

**Quarterly Reviews**:
- Release process effectiveness
- Quality gate effectiveness
- Community feedback integration
- Tool and automation improvements

### Process Evolution

Regular updates to release process based on:
- Industry best practices
- Community feedback
- Tool improvements
- Lessons learned

---

This release process ensures consistent, high-quality releases while maintaining community trust and project stability.