# Version Management

This document describes the semantic versioning system and version management processes for the FQCN Converter project.

## Overview

The project uses [Semantic Versioning (SemVer)](https://semver.org/) with automated version bumping based on [Conventional Commits](https://www.conventionalcommits.org/). This ensures consistent and predictable version management while maintaining clear communication about the nature of changes.

## Semantic Versioning

Version numbers follow the `MAJOR.MINOR.PATCH` format:

- **MAJOR**: Incremented for incompatible API changes (breaking changes)
- **MINOR**: Incremented for new functionality in a backward-compatible manner
- **PATCH**: Incremented for backward-compatible bug fixes

### Pre-release Versions

Pre-release versions can be created using the format `MAJOR.MINOR.PATCH-prerelease`:

- `1.0.0-alpha.1`: Alpha release
- `1.0.0-beta.1`: Beta release  
- `1.0.0-rc.1`: Release candidate

## Conventional Commits

The project follows the Conventional Commits specification for commit messages. This enables automatic version bumping and changelog generation.

### Commit Message Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Commit Types

| Type | Description | Version Impact |
|------|-------------|----------------|
| `feat` | New feature | MINOR |
| `fix` | Bug fix | PATCH |
| `docs` | Documentation changes | PATCH |
| `style` | Code style changes (formatting, etc.) | PATCH |
| `refactor` | Code refactoring | PATCH |
| `perf` | Performance improvements | PATCH |
| `test` | Adding or updating tests | PATCH |
| `build` | Build system changes | PATCH |
| `ci` | CI/CD changes | PATCH |
| `chore` | Other changes | PATCH |
| `revert` | Reverting previous commits | PATCH |

### Breaking Changes

Breaking changes trigger a MAJOR version bump and can be indicated in two ways:

1. **Exclamation mark**: `feat!: remove deprecated API`
2. **Footer**: Include `BREAKING CHANGE:` in the commit body or footer

### Examples

```bash
# Feature addition (MINOR bump)
feat(converter): add support for custom mapping files

# Bug fix (PATCH bump)
fix(cli): handle missing configuration file gracefully

# Breaking change (MAJOR bump)
feat!: remove deprecated convert_legacy method

BREAKING CHANGE: The convert_legacy method has been removed. 
Use convert_file with legacy=True parameter instead.

# Documentation update (PATCH bump)
docs: update installation instructions for Python 3.12

# Scoped change (PATCH bump)
refactor(validator): improve error message formatting
```

## Version Management Tools

### CLI Tool

The project includes a comprehensive version management CLI tool at `scripts/version_manager.py`:

```bash
# Show current version
python scripts/version_manager.py current

# Calculate next version based on commits
python scripts/version_manager.py next

# Bump version automatically
python scripts/version_manager.py bump --tag

# Manual version bumps
python scripts/version_manager.py bump --type major --tag
python scripts/version_manager.py bump --type minor --tag
python scripts/version_manager.py bump --type patch --tag

# Validate version consistency
python scripts/version_manager.py validate

# Show version history
python scripts/version_manager.py history

# Analyze commit compliance
python scripts/version_manager.py analyze --verbose
```

### Makefile Targets

Convenient Makefile targets are available for common version management tasks:

```bash
# Version information
make version-current        # Show current version
make version-next          # Calculate next version
make version-history       # Show version history

# Version bumping
make version-bump          # Auto-bump based on commits
make version-bump-major    # Manual major bump
make version-bump-minor    # Manual minor bump
make version-bump-patch    # Manual patch bump

# Validation and analysis
make version-validate      # Check version consistency
make version-analyze       # Analyze commit compliance

# Release preparation
make release-prepare       # Bump version and create tag
```

## Automated Workflows

### Pre-commit Hooks

Version consistency is automatically validated via pre-commit hooks:

- **Commitizen**: Validates commit message format
- **Version Consistency**: Ensures version files are synchronized

### CI/CD Integration

The version management system integrates with CI/CD workflows:

1. **Pull Request Validation**: Checks commit message format
2. **Version Calculation**: Determines next version for releases
3. **Automated Tagging**: Creates git tags for releases
4. **Changelog Generation**: Updates CHANGELOG.md automatically

## Configuration Files

### Commitizen Configuration (`.cz.toml`)

Configures conventional commit validation and version bumping:

```toml
[tool.commitizen]
name = "cz_conventional_commits"
version = "0.1.0"
tag_format = "v$version"
version_files = [
    "src/fqcn_converter/_version.py:__version__",
    "pyproject.toml:version"
]
```

### Version Files

Version information is maintained in:

- `src/fqcn_converter/_version.py`: Primary version definition
- `pyproject.toml`: Package metadata (uses setuptools_scm)

## Development Workflow

### Making Changes

1. **Create Feature Branch**: `git checkout -b feature/new-feature`
2. **Make Changes**: Implement your changes
3. **Commit with Conventional Format**: 
   ```bash
   git commit -m "feat(converter): add new conversion method"
   ```
4. **Push and Create PR**: Submit for review

### Preparing Releases

1. **Validate Readiness**: `make release-check`
2. **Prepare Release**: `make release-prepare`
3. **Push Tags**: `git push --tags`
4. **Create GitHub Release**: Automated via CI/CD

### Version Validation

Before releases, ensure version consistency:

```bash
# Check all version files are synchronized
make version-validate

# Analyze commit history for proper formatting
make version-analyze

# Preview next version
make version-next
```

## Troubleshooting

### Common Issues

**Version Inconsistency**
```bash
# Problem: Version files out of sync
make version-validate

# Solution: Update version files
python scripts/version_manager.py bump --dry-run
```

**Invalid Commit Messages**
```bash
# Problem: Commits don't follow conventional format
make version-analyze

# Solution: Use commitizen for guided commits
cz commit
```

**Missing Git Tags**
```bash
# Problem: No version history
make version-history

# Solution: Create initial tag
git tag -a v0.1.0 -m "Initial release"
```

### Manual Version Override

In exceptional cases, you can manually override version bumping:

```bash
# Force specific version type
python scripts/version_manager.py bump --type major --force

# Update version file directly (not recommended)
# Edit src/fqcn_converter/_version.py
make version-validate
```

## Best Practices

1. **Always Use Conventional Commits**: Enables automated version management
2. **Validate Before Releases**: Run `make release-check` before creating releases
3. **Tag Releases**: Always create git tags for releases
4. **Document Breaking Changes**: Clearly describe breaking changes in commit messages
5. **Review Version Bumps**: Verify calculated version bumps make sense
6. **Keep Changelog Updated**: Ensure CHANGELOG.md reflects all changes

## Integration with Context7

The version management system integrates with Context7 documentation generation:

- Version information is automatically included in generated documentation
- API documentation reflects the current version
- Release notes can be generated from conventional commits
- Version history is available in documentation

This ensures that documentation always reflects the correct version information and provides users with accurate release information.