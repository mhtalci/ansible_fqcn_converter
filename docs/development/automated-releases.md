# Automated Release Process

This document describes the automated release workflow for FQCN Converter.

## Overview

The FQCN Converter uses a fully automated release process that handles version bumping, changelog generation, quality validation, and GitHub release creation.

## Release Types

### Automatic Releases (Recommended)
**Triggered by**: Git tags pushed to the repository

```bash
# Prepare release (automatic version bump)
make release-prepare-auto

# Or prepare specific version type
make release-prepare-major    # Breaking changes
make release-prepare-minor    # New features
make release-prepare-patch    # Bug fixes
```

### Manual Releases
**Triggered by**: Manual workflow dispatch in GitHub Actions

Use for hotfixes, pre-releases, or emergency releases.

### Pre-releases
- Alpha: `v1.0.0-alpha.1`
- Beta: `v1.0.0-beta.1`
- Release Candidate: `v1.0.0-rc.1`

## Release Workflow

### Local Preparation
```bash
# Validate release readiness
make release-validate

# Calculate next version
make release-version

# Dry run (see what would happen)
make release-dry-run

# Prepare and push release
make release-push
```

### Automated Validation
- Git status checks (clean working directory, main branch)
- Version consistency validation
- Quality assurance (tests, code quality, security scans)
- Changelog format validation

### Version Calculation
Version numbers are calculated automatically based on conventional commits:
- `feat:` → Minor version bump
- `fix:` → Patch version bump
- `BREAKING CHANGE:` → Major version bump

### GitHub Actions Workflow
The release workflow includes:
- **Validation Phase**: Pre-release checks and quality gates
- **Build Phase**: Package building and documentation generation
- **Testing Phase**: Multi-platform installation and functionality testing
- **Release Phase**: GitHub release creation and asset attachment
- **Notification Phase**: Community discussion creation

## Release Artifacts

Each release produces:
- **Python Packages**: Wheel and source distributions
- **Documentation**: Complete documentation archive
- **Release Information**: Formatted release notes and checksums

All artifacts are tested on multiple platforms and checksums are verified.

## Community Notifications

**Automatic Notifications**:
- GitHub Discussions announcement post
- Release highlights and installation instructions
- Links to documentation and support

## Troubleshooting

### Common Issues
```bash
# Release preparation fails
git status                    # Check git status
make version-validate        # Validate version consistency
make quality-gate           # Run quality checks

# Version conflicts
python scripts/version_manager.py validate
python scripts/version_manager.py bump --type patch
```

### Recovery Procedures
**Failed Release**:
1. Identify failure point from workflow logs
2. Fix the underlying issue
3. Delete failed tag: `git tag -d v1.0.0`
4. Re-run release preparation
5. Push corrected tag

**Emergency Hotfix**:
```bash
# Create hotfix branch from release tag
git checkout -b hotfix/v1.0.1 v1.0.0

# Make minimal fix and commit
git commit -m "fix: critical security issue"

# Prepare emergency release
python scripts/prepare_release.py prepare --bump-type patch --push
```

## Best Practices

### For Maintainers
- Plan releases around milestone completion
- Never skip quality checks for releases
- Test releases in staging environments
- Monitor community feedback post-release

### For Contributors
- Use conventional commit format consistently
- Test changes thoroughly before committing
- Test pre-releases and provide feedback
- Report issues promptly and clearly

## Security Considerations

### Release Security
- All artifacts include SHA256 checksums
- Checksums are verified during testing
- Secure distribution channels used
- Audit trail maintained for all releases

### Vulnerability Response
1. Security issue identified and validated
2. Fix developed in private repository
3. Coordinated disclosure timeline established
4. Security release prepared and tested
5. Public release with security advisory

---

This automated release process ensures consistent, high-quality releases while minimizing manual effort and reducing the potential for human error.