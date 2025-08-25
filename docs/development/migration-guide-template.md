# Migration Guide Template

This document provides templates for creating migration guides when breaking changes are introduced in FQCN Converter releases.

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
- [ ] Review your current usage patterns
- [ ] Test the migration in a development environment
- [ ] Update your CI/CD pipelines
- [ ] Inform your team about the changes

## Step-by-Step Migration

### 1. Update Installation

**Before:**
```bash
pip install fqcn-converter=={OLD_VERSION}
```

**After:**
```bash
pip install fqcn-converter=={NEW_VERSION}
```

### 2. Configuration Changes

#### Change 1: {Configuration Change Name}

**What Changed**: Description of the configuration change

**Before (v{OLD_VERSION}):**
```yaml
# Old configuration format
old_setting: value
deprecated_option: true
```

**After (v{NEW_VERSION}):**
```yaml
# New configuration format
new_setting: value
improved_option: 
  enabled: true
  mode: "enhanced"
```

**Migration Steps:**
1. Locate your configuration file (usually `config/fqcn_mapping.yml`)
2. Update the setting names as shown above
3. Remove deprecated options
4. Test the new configuration

#### Change 2: {Another Configuration Change}

[Similar format for each configuration change]

### 3. API Changes

#### Change 1: {API Change Name}

**What Changed**: Description of the API change

**Before (v{OLD_VERSION}):**
```python
from fqcn_converter import FQCNConverter

# Old API usage
converter = FQCNConverter()
result = converter.convert_file("playbook.yml", backup=True)
if result.success:
    print("Conversion successful")
```

**After (v{NEW_VERSION}):**
```python
from fqcn_converter import FQCNConverter
from fqcn_converter.core import ConversionOptions

# New API usage
converter = FQCNConverter()
options = ConversionOptions(create_backup=True)
result = converter.convert_file("playbook.yml", options=options)
if result.is_successful:
    print("Conversion successful")
```

**Migration Steps:**
1. Update import statements
2. Replace old method calls with new API
3. Update result handling code
4. Test your integration

#### Change 2: {Another API Change}

[Similar format for each API change]

### 4. CLI Changes

#### Change 1: {CLI Change Name}

**What Changed**: Description of the CLI change

**Before (v{OLD_VERSION}):**
```bash
fqcn-converter --verbose convert --backup playbook.yml
```

**After (v{NEW_VERSION}):**
```bash
fqcn-converter convert --create-backup --verbosity=2 playbook.yml
```

**Migration Steps:**
1. Update your scripts and documentation
2. Update CI/CD pipeline commands
3. Inform team members about new CLI syntax

### 5. Output Format Changes

#### Change 1: {Output Format Change}

**What Changed**: Description of output format changes

**Before (v{OLD_VERSION}):**
```json
{
  "status": "success",
  "changes": 5,
  "errors": []
}
```

**After (v{NEW_VERSION}):**
```json
{
  "result": {
    "success": true,
    "changes_made": 5,
    "issues": []
  },
  "metadata": {
    "version": "2.0.0",
    "timestamp": "2025-01-25T10:00:00Z"
  }
}
```

**Migration Steps:**
1. Update parsing logic in your applications
2. Handle the new metadata fields
3. Update error handling for new issue format

## Automated Migration Tools

### Migration Script

We provide a migration script to help automate some of the migration process:

```bash
# Download migration script
curl -O https://raw.githubusercontent.com/mhtalci/ansible_fqcn_converter/main/scripts/migrate_v{OLD_MAJOR}_to_v{NEW_MAJOR}.py

# Run migration script
python migrate_v{OLD_MAJOR}_to_v{NEW_MAJOR}.py --help
python migrate_v{OLD_MAJOR}_to_v{NEW_MAJOR}.py --config-dir ./config --dry-run
python migrate_v{OLD_MAJOR}_to_v{NEW_MAJOR}.py --config-dir ./config
```

### Configuration Converter

For configuration file migration:

```bash
# Convert old configuration format
fqcn-converter config migrate --from-version {OLD_VERSION} --input old_config.yml --output new_config.yml

# Validate new configuration
fqcn-converter config validate new_config.yml
```

## Testing Your Migration

### 1. Functional Testing

Test that your existing workflows still work:

```bash
# Test basic conversion
fqcn-converter convert --dry-run test_playbook.yml

# Test batch processing
fqcn-converter batch convert ./playbooks/ --dry-run

# Test validation
fqcn-converter validate ./playbooks/
```

### 2. Integration Testing

Test your application integration:

```python
# Test script for API integration
import sys
from fqcn_converter import FQCNConverter

def test_migration():
    """Test that migration was successful."""
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
    sys.exit(0 if success else 1)
```

### 3. Performance Testing

Verify that performance is acceptable:

```bash
# Benchmark conversion performance
time fqcn-converter convert large_playbook.yml

# Compare with previous version results
# (Document expected performance characteristics)
```

## Rollback Plan

If you encounter issues with the migration:

### 1. Immediate Rollback

```bash
# Rollback to previous version
pip install fqcn-converter=={OLD_VERSION}

# Restore configuration files from backup
cp config/fqcn_mapping.yml.backup config/fqcn_mapping.yml
```

### 2. Partial Rollback

If only some features are problematic:

```bash
# Use compatibility mode (if available)
fqcn-converter convert --compatibility-mode=v{OLD_MAJOR} playbook.yml

# Or use specific legacy options
fqcn-converter convert --legacy-api playbook.yml
```

## Common Issues and Solutions

### Issue 1: {Common Issue Name}

**Problem**: Description of the issue
**Symptoms**: How to identify this issue
**Solution**: Step-by-step solution
**Prevention**: How to avoid this issue

### Issue 2: {Another Common Issue}

[Similar format for each common issue]

## Getting Help

If you encounter issues during migration:

1. **Check the FAQ**: [Link to FAQ section]
2. **Search existing issues**: [Link to GitHub issues]
3. **Ask for help**: [Link to discussions or support channels]
4. **Report bugs**: [Link to bug report template]

### Support Channels

- **GitHub Discussions**: For general questions and community support
- **GitHub Issues**: For bug reports and feature requests
- **Documentation**: For detailed guides and API reference
- **Community Chat**: For real-time help and discussions

## Post-Migration Checklist

After completing the migration:

- [ ] All tests pass with the new version
- [ ] Configuration files are updated and validated
- [ ] CI/CD pipelines are updated
- [ ] Team members are informed about changes
- [ ] Documentation is updated
- [ ] Monitoring and alerting are updated (if applicable)
- [ ] Performance is acceptable
- [ ] Rollback plan is documented and tested

## Feedback

Help us improve future migrations:

- **Migration Experience Survey**: [Link to survey]
- **Documentation Feedback**: [Link to feedback form]
- **Feature Requests**: [Link to feature request template]

Your feedback helps us make future migrations smoother for everyone.

---

**Need Help?** If you're stuck or have questions, don't hesitate to reach out to the community or maintainers.
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

The following features deprecated in v{OLD_MAJOR}.x have been removed:

| Feature | Deprecated In | Removed In | Replacement |
|---------|---------------|------------|-------------|
| Old API method | v{DEPRECATION_VERSION} | v{NEW_MAJOR}.0 | New API method |
| Legacy CLI option | v{DEPRECATION_VERSION} | v{NEW_MAJOR}.0 | New CLI option |

## Architecture Changes

### New Architecture Overview

Brief description of the new architecture and its benefits:

- Improved performance
- Better error handling
- Enhanced extensibility
- Cleaner API design

### Migration Impact

- **Low Impact**: Basic usage patterns remain similar
- **Medium Impact**: Advanced configurations need updates
- **High Impact**: Custom integrations require significant changes

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

### New Feature 1: {Feature Name}

**Benefit**: Why you should consider adopting this feature
**Migration**: How to start using it
**Compatibility**: Works alongside existing functionality

[Continue with optional migration steps...]
```

## Patch Version Migration Template (X.Y.Z)

```markdown
# Migration Guide: v{OLD_VERSION} to v{NEW_VERSION}

This patch release includes bug fixes and minor improvements.

## Summary

- **Bug Fixes**: {COUNT} bugs fixed
- **Security Fixes**: {COUNT} security issues resolved
- **Breaking Changes**: None
- **Migration Required**: No

## Automatic Migration

This patch release requires no manual migration steps. Simply update your installation:

```bash
pip install --upgrade fqcn-converter
```

## Verification

Verify the update was successful:

```bash
fqcn-converter --version  # Should show v{NEW_VERSION}
```

## Fixed Issues

This release fixes the following issues:

- Issue #{NUMBER}: {Description}
- Issue #{NUMBER}: {Description}

No configuration or code changes are required.
```

## Best Practices for Migration Guides

### Writing Guidelines

1. **Clear Structure**: Use consistent headings and formatting
2. **Step-by-Step**: Break complex migrations into clear steps
3. **Examples**: Provide before/after code examples
4. **Testing**: Include testing instructions
5. **Rollback**: Always provide rollback instructions

### Technical Guidelines

1. **Version Specificity**: Be specific about version numbers
2. **Code Examples**: Test all code examples
3. **Links**: Include links to relevant documentation
4. **Automation**: Provide migration scripts when possible
5. **Support**: Include clear support channels

### User Experience Guidelines

1. **Difficulty Assessment**: Clearly indicate migration complexity
2. **Time Estimates**: Provide realistic time estimates
3. **Prerequisites**: List all prerequisites clearly
4. **Common Issues**: Document known issues and solutions
5. **Success Criteria**: Define what successful migration looks like

This template system ensures that users have clear, comprehensive guidance for migrating between versions, reducing friction and improving adoption of new releases.