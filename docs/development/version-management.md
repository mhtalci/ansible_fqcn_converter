# Version Management

This document describes the semantic versioning system and version management processes for the FQCN Converter project.

## Semantic Versioning

Version numbers follow the `MAJOR.MINOR.PATCH` format:

- **MAJOR**: Incremented for incompatible API changes (breaking changes)
- **MINOR**: Incremented for new functionality in a backward-compatible manner
- **PATCH**: Incremented for backward-compatible bug fixes

### Pre-release Versions
- `1.0.0-alpha.1`: Alpha release
- `1.0.0-beta.1`: Beta release
- `1.0.0-rc.1`: Release candidate

## Conventional Commits

The project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages, enabling automatic version bumping and changelog generation.

### Commit Message Format
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Commit Types and Version Impact

| Type | Description | Version Impact |
|------|-------------|----------------|
| `feat` | New feature | MINOR |
| `fix` | Bug fix | PATCH |
| `docs` | Documentation changes | PATCH |
| `style` | Code style changes | PATCH |
| `refactor` | Code refactoring | PATCH |
| `perf` | Performance improvements | PATCH |
| `test` | Adding or updating tests | PATCH |
| `build` | Build system changes | PATCH |
| `ci` | CI/CD changes | PATCH |
| `chore` | Other changes | PATCH |

### Breaking Changes
Breaking changes trigger a MAJOR version bump:

```bash
# Using exclamation mark
feat!: remove deprecated API

# Using footer
feat: add new conversion method

BREAKING CHANGE: The convert_legacy method has been removed.
Use convert_file with legacy=True parameter instead.
```

### Examples
```bash
# Feature addition (MINOR bump)
feat(converter): add support for custom mapping files

# Bug fix (PATCH bump)
fix(cli): handle missing configuration file gracefully

# Breaking change (MAJOR bump)
feat!: remove deprecated convert_legacy method

# Documentation update (PATCH bump)
docs: update installation instructions for Python 3.12
```

## Version Management Tools

### CLI Tool
The project includes a version management CLI tool at `scripts/version_manager.py`:

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
```

### Makefile Targets
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

## Configuration Files

### Commitizen Configuration (`.cz.toml`)
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
- `pyproject.toml`: Package metadata

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

## Troubleshooting

### Common Issues

**Version Inconsistency**
```bash
# Check version files are synchronized
make version-validate

# Update version files
python scripts/version_manager.py bump --dry-run
```

**Invalid Commit Messages**
```bash
# Analyze commit compliance
make version-analyze

# Use commitizen for guided commits
cz commit
```

**Missing Git Tags**
```bash
# Show version history
make version-history

# Create initial tag
git tag -a v0.1.0 -m "Initial release"
```

### Manual Version Override
```bash
# Force specific version type
python scripts/version_manager.py bump --type major --force

# Validate after manual changes
make version-validate
```

## Best Practices

1. **Always Use Conventional Commits**: Enables automated version management
2. **Validate Before Releases**: Run `make release-check` before creating releases
3. **Tag Releases**: Always create git tags for releases
4. **Document Breaking Changes**: Clearly describe breaking changes in commit messages
5. **Review Version Bumps**: Verify calculated version bumps make sense
6. **Keep Changelog Updated**: Ensure CHANGELOG.md reflects all changes

---

This version management system ensures consistent and predictable versioning while maintaining clear communication about the nature of changes.