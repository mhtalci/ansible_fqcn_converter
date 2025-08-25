# Release Notes Template

This document provides templates and guidelines for creating consistent release notes for the FQCN Converter project.

## Standard Release Notes Template

```markdown
# FQCN Converter v{VERSION} Release Notes

Released on {DATE}

## Overview

Brief description of the release, highlighting the most important changes and their impact on users.

## 🚀 New Features

### Feature Name
- **Description**: What the feature does and why it's useful
- **Usage**: How to use the new feature
- **Example**: Code or CLI examples if applicable

## 📝 Changes

### Change Category
- **What Changed**: Description of the change
- **Impact**: How this affects existing users
- **Migration**: Steps needed to adapt (if any)

## 🐛 Bug Fixes

### Bug Category
- **Issue**: Description of the bug that was fixed
- **Impact**: Who was affected and how
- **Fix**: What was done to resolve it

## 📚 Documentation

- Documentation improvements and additions
- New guides or updated existing ones
- API documentation changes

## ⚠️ Breaking Changes

### Breaking Change Name
- **What Changed**: Detailed description of the breaking change
- **Reason**: Why this change was necessary
- **Migration Path**: Step-by-step instructions for updating code
- **Timeline**: When the old behavior will be completely removed (if applicable)

## 🔒 Security

- Security improvements and fixes
- Vulnerability patches
- Security-related configuration changes

## 📊 Performance

- Performance improvements and optimizations
- Benchmark results (if applicable)
- Memory usage improvements

## 📦 Dependencies

### Updated Dependencies
- List of updated dependencies with version changes
- Reason for updates (security, features, bug fixes)

### New Dependencies
- New dependencies added and why
- Impact on installation size or requirements

## 🔗 Links

- [Full Changelog](https://github.com/mhtalci/ansible_fqcn_converter/compare/v{PREVIOUS_VERSION}...v{VERSION})
- [GitHub Release](https://github.com/mhtalci/ansible_fqcn_converter/releases/tag/v{VERSION})
- [Documentation](https://github.com/mhtalci/ansible_fqcn_converter#readme)

## 📈 Statistics

- Total commits: {COMMIT_COUNT}
- Contributors: {CONTRIBUTOR_COUNT}
- Files changed: {FILES_CHANGED}

## 🙏 Acknowledgments

Special thanks to all contributors who made this release possible:

- @contributor1 for feature X
- @contributor2 for bug fix Y
- Community members who reported issues and provided feedback

---

**Installation Instructions:**

```bash
# Install via pip
pip install fqcn-converter=={VERSION}

# Upgrade existing installation
pip install --upgrade fqcn-converter

# Verify installation
fqcn-converter --version
```
```

## Major Release Template (X.0.0)

```markdown
# FQCN Converter v{VERSION} - Major Release

Released on {DATE}

## 🎉 Major Release Highlights

This major release brings significant improvements and new capabilities to FQCN Converter:

- **Key Feature 1**: Brief description
- **Key Feature 2**: Brief description
- **Key Improvement**: Brief description

## ⚠️ Breaking Changes and Migration Guide

### Breaking Change 1
**What Changed**: Detailed description
**Migration Steps**:
1. Step 1
2. Step 2
3. Step 3

**Before (v{PREVIOUS_MAJOR}.x)**:
```python
# Old code example
```

**After (v{VERSION})**:
```python
# New code example
```

### API Changes
- Removed deprecated methods (deprecated since v{DEPRECATION_VERSION})
- Changed method signatures
- Updated return types

## 🚀 New Features

[Standard new features section]

## 📝 Improvements

[Standard improvements section]

## 📚 Updated Documentation

- Complete API reference update
- New user guides
- Migration documentation
- Updated examples

---

**Important**: This is a major release with breaking changes. Please review the migration guide carefully before upgrading.
```

## Minor Release Template (X.Y.0)

```markdown
# FQCN Converter v{VERSION} - Feature Release

Released on {DATE}

## 🚀 New Features

[Focus on new features and capabilities]

## 📝 Improvements

[Enhancements to existing features]

## 🐛 Bug Fixes

[Bug fixes and stability improvements]

## 📚 Documentation

[Documentation updates]

---

This minor release is fully backward compatible with v{MAJOR}.{PREVIOUS_MINOR}.x.
```

## Patch Release Template (X.Y.Z)

```markdown
# FQCN Converter v{VERSION} - Patch Release

Released on {DATE}

## 🐛 Bug Fixes

[List of bug fixes with issue references]

## 🔒 Security

[Security fixes if applicable]

## 📚 Documentation

[Minor documentation updates]

---

This patch release is fully backward compatible and recommended for all users of v{MAJOR}.{MINOR}.x.
```

## Pre-release Template (X.Y.Z-alpha/beta/rc)

```markdown
# FQCN Converter v{VERSION} - {PRERELEASE_TYPE} Release

Released on {DATE}

## ⚠️ Pre-release Notice

This is a {PRERELEASE_TYPE} release intended for testing and feedback. **Not recommended for production use.**

## 🧪 What's Being Tested

- New feature X (feedback needed on API design)
- Performance improvements (testing needed on large projects)
- Bug fixes (verification needed)

## 🚀 New Features (Preview)

[Features being tested]

## 🐛 Known Issues

- Issue 1: Description and workaround
- Issue 2: Description and expected fix timeline

## 🧪 How to Test

1. Installation: `pip install fqcn-converter=={VERSION}`
2. Test scenarios:
   - Scenario 1: Steps to test
   - Scenario 2: Steps to test
3. Provide feedback: Link to feedback form or issue tracker

---

**Feedback Welcome**: Please test this pre-release and report any issues or suggestions.
```

## Automated Generation

The release notes can be automatically generated using the changelog generator:

```bash
# Generate release notes for a version
python scripts/changelog_generator.py release-notes v1.2.3

# Generate with custom output file
python scripts/changelog_generator.py release-notes v1.2.3 --output RELEASE_NOTES.md

# Generate from specific tag
python scripts/changelog_generator.py release-notes v1.2.3 --from-tag v1.2.0
```

## Best Practices

### Content Guidelines
1. **User-Focused**: Write from the user's perspective
2. **Clear Impact**: Explain how changes affect users
3. **Migration Help**: Provide clear upgrade instructions
4. **Examples**: Include code examples for new features
5. **Links**: Reference relevant documentation and issues

### Formatting Guidelines
1. **Consistent Structure**: Use the same sections across releases
2. **Emoji Usage**: Use emojis consistently for visual organization
3. **Code Blocks**: Format code examples properly
4. **Links**: Include relevant links to documentation and issues
5. **Acknowledgments**: Credit contributors and community members

### Review Process
1. **Technical Review**: Ensure accuracy of technical details
2. **User Experience Review**: Check clarity for end users
3. **Community Review**: Get feedback from key community members

---

This template system ensures consistent, professional release notes that help users understand and adopt new versions effectively.