# FQCN Converter CLI Reference

Complete command-line interface reference for the Ansible FQCN Converter

**Version:** 0.1.0

## Table of Contents

- [Main Command](#main-command)
- [Subcommands](#subcommands)
- [Usage Examples](#usage-examples)
- [Common Options](#common-options)
- [Troubleshooting](#troubleshooting)

## Main Command

### fqcn-converter

Convert Ansible playbooks and roles to use Fully Qualified Collection Names (FQCN)

**Usage:** `fqcn-converter [global-options] <command> [command-options] [arguments]`

> **Note:** Global options can be placed anywhere in the command line for flexibility.

#### Global Options

- `--version`: show program's version number and exit
- `--quiet`, `-q`: Suppress all output except errors
- `--verbose`, `-v`: Enable verbose output with debug information
- `--debug`: Enable debug output (same as --verbose)

**Examples of flexible flag placement:**
```bash
fqcn-converter --verbose convert --dry-run
fqcn-converter convert --verbose --dry-run
fqcn-converter convert --dry-run --verbose
```

#### Available Subcommands

- `convert`: Convert Ansible playbooks, roles, and tasks to use Fully Qualified Collection Names
- `validate`: Validate that Ansible files have been properly converted to use FQCN
- `batch`: Discover and convert multiple Ansible projects in parallel

## Subcommands

### convert

Convert Ansible playbooks, roles, and tasks to use Fully Qualified Collection Names

**Usage:** `fqcn-converter convert [options] [arguments]`

#### Options

- `-h`, `--help`: show this help message and exit
- `files`: Ansible files or directories to convert
- `--config`, `-c`: Path to custom FQCN mapping configuration file
- `--dry-run`, `-n`: Show what would be converted without making changes
- `--backup`, `-b`: Create backup files before conversion
- `--no-backup`: Skip creating backup files (overrides default backup behavior)
- `--progress`: Show progress bar for large operations
- `--report`: Generate detailed conversion report to specified file
- `--skip-validation`: Skip YAML syntax validation after conversion
- `--lint`: Run ansible-lint validation after conversion
- `--force`: Force conversion even if files appear already converted
- `--exclude`: Exclude files/directories matching pattern (can be used multiple times)

#### Examples

**Convert a single playbook**
```bash
fqcn-converter convert playbook.yml
```
Converts all short module names in playbook.yml to FQCN format

**Dry run conversion to preview changes**
```bash
fqcn-converter convert --dry-run playbook.yml
```
Shows what changes would be made without modifying files

**Convert with custom configuration**
```bash
fqcn-converter convert --config custom_mappings.yml playbook.yml
```
Uses custom FQCN mappings from configuration file

**Convert directory with backup**
```bash
fqcn-converter convert --backup roles/
```
Converts all Ansible files in roles/ directory and creates backups

**Convert with progress reporting**
```bash
fqcn-converter convert --progress --report report.json roles/
```
Shows progress and generates detailed conversion report

#### Common Use Cases

**Migrating Legacy Playbooks**

Convert existing Ansible playbooks to use FQCN format for Ansible 2.10+ compatibility

*Workflow:* 1. Backup files, 2. Run dry-run, 3. Convert with validation, 4. Test playbooks

**CI/CD Integration**

Integrate FQCN conversion into CI/CD pipelines for automated compliance

*Workflow:* 1. Add pre-commit hook, 2. Run in CI validation, 3. Generate reports

**Large-Scale Conversion**

Convert multiple Ansible projects across an organization

*Workflow:* 1. Use batch command, 2. Parallel processing, 3. Centralized reporting

---

### validate

Validate that Ansible files have been properly converted to use FQCN

**Usage:** `fqcn-converter validate [options] [arguments]`

#### Options

- `-h`, `--help`: show this help message and exit
- `files`: Ansible files or directories to validate (default: current directory)
- `--strict`: Use strict validation mode with enhanced checks
- `--score`: Calculate and display FQCN conversion completeness score
- `--lint`: Run ansible-lint validation in addition to FQCN checks
- `--report`: Generate detailed validation report to specified file
- `--format`: Output format for validation results (default: text)
- `--exclude`: Exclude files/directories matching pattern (can be used multiple times)
- `--include-warnings`: Include warnings in validation results
- `--parallel`: Enable parallel validation for multiple files
- `--workers`: Number of parallel workers for validation (default: 4)

#### Examples

**Validate a single file**
```bash
fqcn-converter validate playbook.yml
```
Checks if playbook.yml properly uses FQCN format

**Validate with scoring**
```bash
fqcn-converter validate --score roles/
```
Validates files and shows FQCN compliance scores

**Validate with ansible-lint**
```bash
fqcn-converter validate --lint --include-warnings playbook.yml
```
Runs both FQCN validation and ansible-lint checks

**Generate validation report**
```bash
fqcn-converter validate --report validation.json --format json roles/
```
Creates detailed JSON validation report

**Parallel validation**
```bash
fqcn-converter validate --parallel --workers 8 /path/to/projects
```
Validates multiple files in parallel for faster processing

#### Common Use Cases

**Compliance Checking**

Ensure Ansible code meets FQCN compliance standards

*Workflow:* 1. Run validation, 2. Check scores, 3. Fix issues, 4. Re-validate

**CI Integration**

Use validation in CI/CD pipelines for automated compliance checking

*Workflow:* 1. Validate on PR, 2. Block merge if failed, 3. Generate reports

**Migration Progress Tracking**

Track progress of FQCN migration across projects

*Workflow:* 1. Baseline validation, 2. Regular scoring, 3. Progress reporting

---

### batch

Discover and convert multiple Ansible projects in parallel

**Usage:** `fqcn-converter batch [options] [arguments]`

#### Options

- `-h`, `--help`: show this help message and exit
- `root_directory`: Root directory to discover Ansible projects
- `--projects`: Specific project directories to convert (alternative to root_directory)
- `--discover-only`: Only discover projects without converting them
- `--config`, `-c`: Path to custom FQCN mapping configuration file
- `--workers`, `-w`: Number of parallel workers for batch processing (default: 4)
- `--dry-run`, `-n`: Show what would be converted without making changes
- `--continue-on-error`: Continue processing other projects if one fails
- `--patterns`: Custom patterns to identify Ansible projects
- `--exclude`: Exclude directories matching pattern (can be used multiple times)
- `--max-depth`: Maximum directory depth for project discovery (default: 5)
- `--report`, `-r`: Generate detailed batch processing report to specified file
- `--summary-only`: Show only summary statistics, not individual project details
- `--validate`: Validate converted files after batch processing
- `--lint`: Run ansible-lint validation after conversion

#### Examples

**Batch convert multiple projects**
```bash
fqcn-converter batch /path/to/ansible/projects
```
Discovers and converts all Ansible projects in the directory

**Batch convert with custom workers**
```bash
fqcn-converter batch --workers 8 /path/to/projects
```
Uses 8 parallel workers for faster batch processing

**Batch dry run with report**
```bash
fqcn-converter batch --dry-run --report batch_report.json /path/to/projects
```
Previews batch conversion and generates detailed report

#### Common Use Cases

**Organization-wide Migration**

Convert all Ansible projects across multiple teams

*Workflow:* 1. Discover projects, 2. Batch convert, 3. Validate results, 4. Report status

**Continuous Compliance**

Regularly check and convert new Ansible content

*Workflow:* 1. Scheduled batch runs, 2. Automated reporting, 3. Alert on issues

---

## Usage Examples

### Basic Usage

#### Convert Single File

Convert a single Ansible playbook to FQCN format

```bash
fqcn-converter convert playbook.yml
```

**Expected Output:**
```
✅ Successfully converted 3 modules in playbook.yml
```

#### Validate Conversion

Check if a file properly uses FQCN format

```bash
fqcn-converter validate playbook.yml
```

**Expected Output:**
```
✅ File is compliant (score: 100%)
```

### Advanced Usage

#### Batch Processing

Process multiple projects in parallel

```bash
fqcn-converter batch --workers 4 /ansible/projects
```

**Expected Output:**
```
Processed 15 projects, 12 successful, 3 failed
```

#### Custom Configuration

Use custom mappings and create backups

```bash
fqcn-converter convert --config custom.yml --backup roles/
```

**Expected Output:**
```
Converted 25 files with custom mappings
```

### Reporting and Analysis

#### Detailed Reporting

Generate comprehensive validation report

```bash
fqcn-converter validate --score --report report.json --format json .
```

**Expected Output:**
```
Validation report saved to report.json
```

#### Progress Tracking

Preview changes with progress indication

```bash
fqcn-converter convert --progress --dry-run large_project/
```

**Expected Output:**
```
Processing 150/200 files... Would convert 45 modules
```

## Common Options

### Verbosity

**Options:** `--quiet`, `--verbose`, `--debug`

Control output verbosity level

**Usage:** Use --quiet for minimal output, --verbose for detailed information

### Configuration

**Options:** `--config`

Specify custom FQCN mapping configuration

**Usage:** Point to YAML file with custom module mappings

### Dry Run

**Options:** `--dry-run`, `-n`

Preview changes without modifying files

**Usage:** Always test with dry-run before actual conversion

### Reporting

**Options:** `--report`, `--format`

Generate detailed operation reports

**Usage:** Use for audit trails and compliance documentation

## Troubleshooting

### Command not found: fqcn-converter

**Cause:** Package not installed or not in PATH

**Solution:** Install with 'pip install fqcn-converter' or run from project directory

### Permission denied when converting files

**Cause:** Insufficient file permissions

**Solution:** Check file permissions or run with appropriate user privileges

### YAML parsing errors during conversion

**Cause:** Invalid YAML syntax in source files

**Solution:** Fix YAML syntax errors before conversion, use --skip-validation to bypass

### No files found to convert

**Cause:** No Ansible files detected in specified path

**Solution:** Check path contains .yml/.yaml files with Ansible content

### Conversion fails with configuration error

**Cause:** Invalid or missing configuration file

**Solution:** Verify configuration file format and path, use default if unsure

### Batch processing hangs or is very slow

**Cause:** Too many parallel workers or large files

**Solution:** Reduce --workers count or process smaller batches

