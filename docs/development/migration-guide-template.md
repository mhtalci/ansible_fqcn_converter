# Migration Guide Template

This document provides templates for creating migration guides when breaking changes are introduced.

## Standard Migration Guide Template

```markdown
# Migration Guide: v{OLD_VERSION} to v{NEW_VERSION}

This guide helps you migrate from FQCN Converter v{OLD_VERSION} to v{NEW_VERSION}.

## Overview

Brief summary of the major changes and why they were made.

**Migration Difficulty**: {Easy|Moderate|Complex}
**Estimated Time**: {X minutes|X hours}
**Automation Available**: {Yes|No|Partial}

## Breaking Changes Summary

| Change | Impact | Migration Required |
|--------|--------|-------------------|
| Change 1 | High | Yes |
| Change 2 | Medium | Yes |
| Change 3 | Low | No |

## Pre-Migration Checklist

- [ ] Backup your current configuration files
- [ ] Test the migration in a development environment
- [ ] Update your CI/CD pipelines
- [ ] Inform your team about the changes

## Step-by-Step Migration

### Update Installation

```bash
# Before
pip install fqcn-converter=={OLD_VERSION}

# After
pip install fqcn-converter=={NEW_VERSION}
```

### Configuration Changes

**Before (v{OLD_VERSION}):**
```yaml
old_setting: value
deprecated_option: true
```

**After (v{NEW_VERSION}):**
```yaml
new_setting: value
improved_option:
  enabled: true
  mode: "enhanced"
```

### API Changes

**Before (v{OLD_VERSION}):**
```python
from fqcn_converter import FQCNConverter

converter = FQCNConverter()
result = converter.convert_file("playbook.yml", backup=True)
if result.success:
    print("Conversion successful")
```

**After (v{NEW_VERSION}):**
```python
from fqcn_converter import FQCNConverter

converter = FQCNConverter()
result = converter.convert_file("playbook.yml", create_backup=True)
if result.is_successful:
    print("Conversion successful")
```

### CLI Changes

**Before (v{OLD_VERSION}):**
```bash
fqcn-converter --verbose convert --backup playbook.yml
```

**After (v{NEW_VERSION}):**
```bash
fqcn-converter convert --create-backup --verbosity=2 playbook.yml
```

## Testing Your Migration

### Functional Testing
```bash
# Test basic conversion
fqcn-converter convert --dry-run test_playbook.yml

# Test batch processing
fqcn-converter batch ./playbooks/ --dry-run

# Test validation
fqcn-converter validate ./playbooks/
```

### Integration Testing
```python
# Test script for API integration
from fqcn_converter import FQCNConverter

def test_migration():
    try:
        converter = FQCNConverter()
        result = converter.convert_content("- name: Test\n  user: name=test")
        assert result.is_successful
        print("✓ Migration test passed")
        return True
    except Exception as e:
        print(f"✗ Migration test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_migration()
```

## Rollback Plan

If you encounter issues:

```bash
# Rollback to previous version
pip install fqcn-converter=={OLD_VERSION}

# Restore configuration files from backup
cp config/fqcn_mapping.yml.backup config/fqcn_mapping.yml
```

## Getting Help

- **GitHub Issues**: For bug reports and questions
- **GitHub Discussions**: For community support
- **Documentation**: For detailed guides and API reference

## Post-Migration Checklist

- [ ] All tests pass with the new version
- [ ] Configuration files are updated and validated
- [ ] CI/CD pipelines are updated
- [ ] Team members are informed about changes
- [ ] Documentation is updated
- [ ] Performance is acceptable
```

## Major Version Migration Template (X.0.0)

```markdown
# Major Migration Guide: v{OLD_MAJOR}.x to v{NEW_MAJOR}.0

This is a major version upgrade with significant breaking changes.

## ⚠️ Important Notice

This major version includes breaking changes that require careful migration planning:

- **API Changes**: Significant API restructuring
- **Configuration Changes**: New configuration format
- **Behavior Changes**: Some default behaviors have changed
- **Dependency Changes**: Updated minimum requirements

**Recommendation**: Test thoroughly in a development environment before upgrading production systems.

## New Requirements

### System Requirements
- Python {MIN_PYTHON_VERSION}+ (was {OLD_MIN_PYTHON_VERSION}+)
- {NEW_DEPENDENCY} {MIN_VERSION}+ (new requirement)

### Deprecated Feature Removal

| Feature | Deprecated In | Removed In | Replacement |
|---------|---------------|------------|-------------|
| Old API method | v{DEPRECATION_VERSION} | v{NEW_MAJOR}.0 | New API method |
| Legacy CLI option | v{DEPRECATION_VERSION} | v{NEW_MAJOR}.0 | New CLI option |

[Continue with detailed migration steps...]
```

## Minor Version Migration Template (X.Y.0)

```markdown
# Migration Guide: v{OLD_VERSION} to v{NEW_VERSION}

This minor version update includes new features and improvements with minimal breaking changes.

## Summary

- **New Features**: {COUNT} new features added
- **Improvements**: {COUNT} existing features enhanced
- **Breaking Changes**: {COUNT} minor breaking changes
- **Migration Required**: {Yes|No|Optional}

## Optional Migrations

While this version is largely backward compatible, you may want to adopt new features:

### New Feature: {Feature Name}

**Benefit**: Why you should consider adopting this feature
**Migration**: How to start using it
**Compatibility**: Works alongside existing functionality

[Continue with optional migration steps...]
```

## Best Practices

### Writing Guidelines
1. **Clear Structure**: Use consistent headings and formatting
2. **Step-by-Step**: Break complex migrations into clear steps
3. **Examples**: Provide before/after code examples
4. **Testing**: Include testing instructions
5. **Rollback**: Always provide rollback instructions

### User Experience Guidelines
1. **Difficulty Assessment**: Clearly indicate migration complexity
2. **Time Estimates**: Provide realistic time estimates
3. **Prerequisites**: List all prerequisites clearly
4. **Common Issues**: Document known issues and solutions
5. **Success Criteria**: Define what successful migration looks like

---

This template system ensures that users have clear, comprehensive guidance for migrating between versions.