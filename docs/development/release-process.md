# Release Process

This document outlines the complete release process for the FQCN Converter project.

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
2.0.0  - Breaking changes requiring migration
```

### Pre-release Versions
```
0.2.0-alpha.1  - Alpha release for early testing
0.2.0-beta.1   - Beta release for broader testing
0.2.0-rc.1     - Release candidate for final testing
```

## Release Types

### Patch Releases (0.1.x)
- Bug fixes, security updates, minor improvements
- No breaking changes or new features
- Backward compatible

### Minor Releases (0.x.0)
- New features, enhancements, deprecations
- Backward compatible
- New functionality and feature enhancements

### Major Releases (x.0.0)
- Breaking changes, API redesigns, major features
- Breaking changes allowed
- API modifications and removal of deprecated features

## Release Schedule

- **Patch releases**: As needed (typically weekly for critical fixes)
- **Minor releases**: Monthly (first Tuesday of each month)
- **Major releases**: Quarterly or as needed for breaking changes
- **Emergency releases**: Within 24-48 hours for critical issues

## Release Process

### Pre-Release Planning
**Feature Freeze**: 1 week before release
- No new features merged
- Focus on bug fixes and testing
- Documentation updates
- Release preparation

### Release Preparation
```bash
# Create release branch
git checkout main
git pull origin main
git checkout -b release/0.2.0

# Update version information
# Update _version.py, pyproject.toml, CHANGELOG.md

# Commit release preparations
git add .
git commit -m "chore: prepare release 0.2.0"
git push origin release/0.2.0
```

### Quality Assurance
```bash
# Run comprehensive test suite
pytest tests/ -v --cov=fqcn_converter --cov-report=html

# Run performance and integration tests
pytest tests/performance/ tests/integration/ -v

# Security scanning
bandit -r src/
safety check
```

**Manual Testing**:
- Fresh installation and upgrade testing
- CLI and API functionality testing
- Edge cases and error handling
- Multi-platform compatibility

### Release Candidate
```bash
# Tag release candidate
git tag -a v0.2.0-rc.1 -m "Release candidate 0.2.0-rc.1"
git push origin v0.2.0-rc.1

# Build and test packages
python -m build
twine check dist/*
```

**Community Testing**: 3-7 days for feedback and bug reports

### Final Release
```bash
# Merge release branch to main
git checkout main
git merge release/0.2.0
git push origin main

# Create release tag
git tag -a v0.2.0 -m "Release 0.2.0"
git push origin v0.2.0

# Build and publish packages
python -m build
twine upload dist/*

# Create GitHub release
gh release create v0.2.0 --title "FQCN Converter v0.2.0" --notes-file RELEASE_NOTES.md dist/*
```

### Post-Release Activities
```bash
# Update development version
git commit --allow-empty -m "chore: post-release 0.2.0"

# Bump version for development
# _version.py: __version__ = "0.3.0-dev"
git add .
git commit -m "chore: bump version to 0.3.0-dev"
git push origin main
```

## Release Automation

### GitHub Actions Workflow
```yaml
name: Release
on:
  push:
    tags: ['v*']

jobs:
  test-and-publish:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    - name: Run tests
      run: pytest --cov=fqcn_converter --cov-report=term-missing
    - name: Run linting
      run: |
        flake8 src tests
        black --check src tests
        mypy src
    - name: Build package
      run: |
        python -m pip install build
        python -m build
    - name: Publish to PyPI
      run: twine upload dist/*
      env:
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
```

## Rollback Procedures

### Emergency Rollback
If a critical issue is discovered after release:

```bash
# Yank problematic release from PyPI
pip yank fqcn-converter==0.2.0 --reason "Critical bug in conversion logic"

# Create hotfix branch
git checkout v0.1.9  # Last known good version
git checkout -b hotfix/0.1.10

# Apply minimal fix
git commit -m "fix: critical issue in conversion logic"
git tag v0.1.10
git push origin v0.1.10
```

## Quality Gates

### Automated Quality Gates
- [ ] All tests pass with coverage reporting
- [ ] Code coverage ≥ 80%
- [ ] No linting errors (flake8, black, mypy)
- [ ] Package builds successfully
- [ ] Installation verification passes

### Manual Quality Gates
- [ ] Manual testing completed
- [ ] Security review approved
- [ ] Documentation review completed
- [ ] Maintainer approval obtained
- [ ] Community testing feedback addressed

## Monitoring and Metrics

### Release Metrics
- Test coverage percentage
- Number of bugs found in testing
- Time from feature freeze to release
- Download statistics from PyPI
- Community feedback sentiment

### Post-Release Monitoring
- Monitor GitHub issues for bug reports
- Check PyPI download statistics
- Monitor community feedback
- Track performance metrics
- Watch for security alerts

---

This release process ensures consistent, high-quality releases while maintaining community trust and project stability.