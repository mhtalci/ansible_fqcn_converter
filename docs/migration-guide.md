# Migration Guide

[![Version](https://img.shields.io/badge/version-0.1.0-blue)](https://github.com/mhtalci/ansible_fqcn_converter/releases)
[![Production Ready](https://img.shields.io/badge/status-production--ready-brightgreen)](https://github.com/mhtalci/ansible_fqcn_converter)

Complete guide for migrating your Ansible projects to use Fully Qualified Collection Names (FQCN) with the FQCN Converter.

## Overview

This guide walks you through the complete process of migrating your Ansible infrastructure from short module names to FQCN format, ensuring compatibility with Ansible 2.10+ and modern best practices.

## Why Migrate to FQCN?

### Benefits
- **Future Compatibility**: Required for Ansible 2.10+ and newer versions
- **Explicit Dependencies**: Clear collection requirements and dependencies
- **Namespace Clarity**: Avoid module name conflicts between collections
- **Better Performance**: Faster module resolution and execution
- **Enhanced Security**: Explicit collection sources reduce supply chain risks

### Timeline
- **Ansible 2.9**: FQCN supported but optional
- **Ansible 2.10+**: FQCN required for non-builtin modules
- **Ansible 4.0+**: Deprecation warnings for short names
- **Future Versions**: Short names will be removed entirely

## Pre-Migration Assessment

### 1. Inventory Your Ansible Content

```bash
# Discover all Ansible files in your infrastructure
find /path/to/ansible -name "*.yml" -o -name "*.yaml" | grep -E "(playbook|task|handler|role)" > ansible_files.txt

# Count total files
wc -l ansible_files.txt
```

### 2. Assess Current FQCN Usage

```bash
# Check current FQCN compliance
fqcn-converter validate --report assessment.json /path/to/ansible

# View compliance scores
fqcn-converter validate --score /path/to/ansible
```

### 3. Identify Dependencies

```bash
# Generate dependency report
fqcn-converter convert --dry-run --report dependencies.json /path/to/ansible

# Review required collections
grep -o '"collection": "[^"]*"' dependencies.json | sort | uniq
```

## Migration Strategy

### Small Projects (< 50 files)
**Recommended Approach**: Direct conversion with validation

```bash
# 1. Backup your project
cp -r /path/to/project /path/to/project.backup

# 2. Preview changes
fqcn-converter convert --dry-run --report preview.json /path/to/project

# 3. Apply conversion
fqcn-converter convert --report conversion.json /path/to/project

# 4. Validate results
fqcn-converter validate --strict --report validation.json /path/to/project
```

### Medium Projects (50-500 files)
**Recommended Approach**: Phased migration with batch processing

```bash
# 1. Process by directory/role
fqcn-converter convert --dry-run roles/
fqcn-converter convert --dry-run playbooks/
fqcn-converter convert --dry-run group_vars/

# 2. Apply changes incrementally
fqcn-converter convert roles/
fqcn-converter convert playbooks/

# 3. Batch validate
fqcn-converter validate --parallel --workers 4 /path/to/project
```

### Large Projects (500+ files)
**Recommended Approach**: Automated batch processing with parallel execution

```bash
# 1. Discover all projects
fqcn-converter batch --discover-only /path/to/infrastructure > projects.txt

# 2. Batch process with high parallelism
fqcn-converter batch --workers 8 --report batch_report.json /path/to/infrastructure

# 3. Review and fix any failures
fqcn-converter validate --parallel --workers 8 /path/to/infrastructure
```

## Step-by-Step Migration Process

### Phase 1: Preparation

#### 1.1 Install FQCN Converter
```bash
# Install from GitHub
pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git

# Verify installation
fqcn-converter --version
```

#### 1.2 Create Backups
```bash
# Full project backup
tar -czf ansible_backup_$(date +%Y%m%d).tar.gz /path/to/ansible

# Git backup (if using version control)
git add -A && git commit -m "Pre-FQCN migration backup"
```

#### 1.3 Document Current State
```bash
# Generate baseline report
fqcn-converter validate --report baseline.json /path/to/ansible

# Document collection requirements
ansible-galaxy collection list > current_collections.txt
```

### Phase 2: Analysis and Planning

#### 2.1 Assess Impact
```bash
# Dry run conversion
fqcn-converter convert --dry-run --report impact_analysis.json /path/to/ansible

# Review changes
python -c "
import json
with open('impact_analysis.json') as f:
    data = json.load(f)
    print(f'Files to change: {data[\"files_to_change\"]}')
    print(f'Total modules to convert: {data[\"total_changes\"]}')
    print(f'Collections required: {len(data[\"collections_needed\"])}')
"
```

#### 2.2 Plan Collection Installation
```bash
# Extract required collections from analysis
grep -o '"collection": "[^"]*"' impact_analysis.json | sort | uniq > required_collections.txt

# Create requirements file
cat > requirements.yml << EOF
---
collections:
$(cat required_collections.txt | sed 's/"collection": "//g' | sed 's/"//g' | sed 's/^/  - name: /')
EOF
```

#### 2.3 Test Environment Setup
```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate

# Install required collections
ansible-galaxy collection install -r requirements.yml

# Test basic functionality
ansible-playbook --syntax-check test_playbook.yml
```

### Phase 3: Conversion

#### 3.1 Install Required Collections
```bash
# Install collections in production environment
ansible-galaxy collection install -r requirements.yml

# Verify installation
ansible-galaxy collection list
```

#### 3.2 Perform Conversion
```bash
# Convert with progress tracking
fqcn-converter convert --progress --report conversion_report.json /path/to/ansible

# Check for any failures
grep -i "error\|failed" conversion_report.json
```

#### 3.3 Handle Edge Cases
```bash
# Review files that couldn't be converted
fqcn-converter validate --report validation.json /path/to/ansible
python -c "
import json
with open('validation.json') as f:
    data = json.load(f)
    for file_path, result in data['file_results'].items():
        if not result['valid']:
            print(f'Manual review needed: {file_path}')
            for issue in result['issues']:
                print(f'  - {issue[\"message\"]}')
"
```

### Phase 4: Validation and Testing

#### 4.1 Comprehensive Validation
```bash
# Strict validation
fqcn-converter validate --strict --report final_validation.json /path/to/ansible

# Check compliance score
fqcn-converter validate --score /path/to/ansible
```

#### 4.2 Syntax Validation
```bash
# Validate all playbooks
find /path/to/ansible -name "*.yml" -exec ansible-playbook --syntax-check {} \;

# Run ansible-lint if available
ansible-lint /path/to/ansible
```

#### 4.3 Functional Testing
```bash
# Test critical playbooks in staging
ansible-playbook --check --diff critical_playbook.yml

# Run integration tests
ansible-playbook test_suite.yml
```

### Phase 5: Deployment and Monitoring

#### 5.1 Gradual Rollout
```bash
# Deploy to staging first
ansible-playbook --limit staging site.yml

# Monitor for issues
tail -f /var/log/ansible.log

# Deploy to production in phases
ansible-playbook --limit "production:&webservers" site.yml
ansible-playbook --limit "production:&databases" site.yml
```

#### 5.2 Post-Migration Validation
```bash
# Verify all systems are functioning
ansible all -m ping

# Run health checks
ansible-playbook health_check.yml

# Generate final compliance report
fqcn-converter validate --report post_migration.json /path/to/ansible
```

## Common Migration Scenarios

### Scenario 1: Legacy Playbooks with Custom Modules

**Challenge**: Custom modules mixed with standard modules
**Solution**: Use custom configuration

```yaml
# custom_mappings.yml
mappings:
  my_custom_module: "my.collection.my_custom_module"
  legacy_module: "community.general.legacy_module"
```

```bash
fqcn-converter convert --config custom_mappings.yml /path/to/playbooks
```

### Scenario 2: Multi-Team Environment

**Challenge**: Different teams with different migration timelines
**Solution**: Incremental migration by team/project

```bash
# Team A migration
fqcn-converter batch team_a_projects/

# Team B migration (later)
fqcn-converter batch team_b_projects/

# Validate organization-wide compliance
fqcn-converter validate --report org_compliance.json /all/projects
```

### Scenario 3: CI/CD Integration

**Challenge**: Ensure all new code uses FQCN
**Solution**: Add validation to CI/CD pipeline

```yaml
# .github/workflows/ansible-validation.yml
name: Ansible FQCN Validation
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install FQCN Converter
        run: pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git
      - name: Validate FQCN Usage
        run: fqcn-converter validate --strict --format json
```

## Troubleshooting Common Issues

### Issue 1: Module Not Found After Conversion

**Symptoms**: `ERROR! couldn't resolve module/action 'ansible.builtin.package'`

**Cause**: Collection not installed or incorrect FQCN mapping

**Solution**:
```bash
# Install missing collection
ansible-galaxy collection install ansible.builtin

# Verify collection installation
ansible-galaxy collection list | grep ansible.builtin

# Check FQCN mapping
fqcn-converter validate --debug problematic_file.yml
```

### Issue 2: Performance Degradation

**Symptoms**: Playbooks run slower after conversion

**Cause**: Collection loading overhead or inefficient task structure

**Solution**:
```bash
# Profile playbook execution
ansible-playbook --start-at-task="slow task" playbook.yml -vvv

# Optimize task structure
# Before: Multiple small tasks
# After: Use loops and blocks for efficiency
```

### Issue 3: Validation Failures

**Symptoms**: `fqcn-converter validate` reports issues after conversion

**Cause**: Edge cases or custom modules not in mapping

**Solution**:
```bash
# Generate detailed validation report
fqcn-converter validate --report detailed.json problematic_files/

# Review and fix manually
# Add custom mappings if needed
```

## Best Practices

### During Migration
1. **Always backup** before making changes
2. **Use dry-run mode** to preview changes
3. **Migrate incrementally** for large projects
4. **Test thoroughly** in staging environments
5. **Document custom mappings** for team reference

### Post-Migration
1. **Set up CI/CD validation** to prevent regression
2. **Regular compliance checks** with scheduled validation
3. **Team training** on FQCN best practices
4. **Update documentation** and runbooks
5. **Monitor performance** and optimize as needed

### Long-term Maintenance
1. **Keep collections updated** with regular updates
2. **Review new modules** and add to mappings
3. **Periodic compliance audits** across all projects
4. **Community contribution** of new mappings and improvements

## Migration Checklist

### Pre-Migration
- [ ] Install FQCN Converter
- [ ] Create comprehensive backups
- [ ] Generate baseline compliance report
- [ ] Identify required collections
- [ ] Set up test environment
- [ ] Plan migration phases

### During Migration
- [ ] Install required collections
- [ ] Run dry-run conversion
- [ ] Apply conversion with progress tracking
- [ ] Handle edge cases and failures
- [ ] Validate syntax and functionality
- [ ] Test in staging environment

### Post-Migration
- [ ] Deploy to production incrementally
- [ ] Monitor system health
- [ ] Generate final compliance report
- [ ] Update documentation
- [ ] Set up ongoing validation
- [ ] Train team members

## Success Metrics

### Technical Metrics
- **FQCN Compliance**: Target 100% for all production code
- **Conversion Success Rate**: >95% automated conversion
- **Performance Impact**: <10% execution time increase
- **Error Rate**: <1% post-migration errors

### Process Metrics
- **Migration Time**: Complete within planned timeline
- **Team Productivity**: Minimal disruption to development
- **Knowledge Transfer**: All team members trained
- **Documentation**: All processes documented

## Support and Resources

### Getting Help
- **GitHub Issues**: [Report problems](https://github.com/mhtalci/ansible_fqcn_converter/issues)
- **GitHub Discussions**: [Ask questions](https://github.com/mhtalci/ansible_fqcn_converter/discussions)
- **Documentation**: [Complete guides](docs/)

### Additional Resources
- **Ansible Collections Guide**: [Official documentation](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html)
- **FQCN Best Practices**: [Community guidelines](https://docs.ansible.com/ansible/latest/dev_guide/developing_collections.html)
- **Migration Examples**: [Sample projects](docs/examples/)

---

**Need help with your migration?** Join our community discussions or open an issue for personalized assistance.

*This migration guide is continuously updated based on community feedback and real-world migration experiences.*