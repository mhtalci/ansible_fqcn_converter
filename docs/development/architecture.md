# Architecture Overview

The FQCN Converter is designed as a modular system for converting Ansible playbooks to use Fully Qualified Collection Names (FQCNs).

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   CLI Interface │    │   Python API    │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │    Core Engine        │
         │  ┌─────────────────┐  │
         │  │ Converter       │  │
         │  │ Validator       │  │
         │  │ Batch Processor │  │
         │  └─────────────────┘  │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │   Configuration       │
         │   YAML Handler        │
         │   File System         │
         └───────────────────────┘
```

## Package Structure

```
src/fqcn_converter/
├── __init__.py              # Public API exports
├── cli/                     # Command-line interface
│   ├── main.py             # CLI entry point
│   ├── convert.py          # Convert command
│   ├── validate.py         # Validate command
│   └── batch.py            # Batch command
├── core/                    # Core conversion logic
│   ├── converter.py        # Main conversion engine
│   ├── validator.py        # Validation engine
│   └── batch.py            # Batch processing
├── config/                  # Configuration management
│   └── manager.py          # Configuration manager
├── utils/                   # Utility modules
│   ├── yaml_handler.py     # YAML processing
│   └── logging.py          # Logging configuration
└── exceptions.py           # Exception hierarchy
```

## Core Components

### Converter Engine (`core/converter.py`)

**FQCNConverter**: Main conversion engine
- Loads FQCN mappings from configuration
- Parses Ansible YAML files safely
- Identifies module usage patterns
- Applies FQCN mappings with conflict resolution
- Creates backups and handles dry-run mode

**ConversionResult**: Encapsulates operation results
- Success/failure status and metrics
- Error and warning messages
- Original and converted content

### Validation Engine (`core/validator.py`)

**ValidationEngine**: FQCN compliance validation
- Analyzes files for FQCN compliance
- Generates detailed issue reports
- Calculates compliance scores
- Provides remediation suggestions

**ValidationResult & ValidationIssue**: Structured validation results

### Batch Processor (`core/batch.py`)

**BatchProcessor**: Parallel processing of multiple projects
- Discovers Ansible projects automatically
- Coordinates parallel worker processes
- Aggregates results and generates reports
- Handles individual project failures gracefully

### Configuration Manager (`config/manager.py`)

**ConfigurationManager**: Centralized configuration management
- Loads default FQCN mappings
- Merges custom configurations
- Validates configuration data
- Provides fallback mechanisms

## Design Patterns

### Strategy Pattern
Different conversion strategies for different file types (playbooks, task files, handlers).

### Builder Pattern
Flexible configuration building with method chaining.

### Observer Pattern
Progress tracking and event handling for batch operations.

### Factory Pattern
Creating appropriate processors based on configuration.

## Error Handling

### Exception Hierarchy
```
FQCNConverterError (Base)
├── ConfigurationError
├── ConversionError
├── ValidationError
├── BatchProcessingError
└── FileAccessError
```

### Recovery Mechanisms
- **Graceful Degradation**: Continue with available mappings
- **User Guidance**: Actionable error messages and suggestions
- **Batch Resilience**: Continue processing other projects on individual failures

## Performance Considerations

### Memory Management
- Process files individually to minimize memory usage
- Lazy loading of configurations and mappings
- Proper cleanup of temporary files and resources

### Parallel Processing
- ThreadPoolExecutor for I/O-bound operations
- Automatic worker scaling based on system resources
- Progress tracking and monitoring

### Caching
- Configuration and mapping caching
- Memory-efficient storage with TTL
- Optional persistent cache for validation results

## Testing Architecture

### Test Structure
```
tests/
├── unit/                    # Fast, isolated tests
├── integration/             # End-to-end workflow tests
├── performance/             # Performance and load tests
└── fixtures/                # Test data and utilities
```

### Test Patterns
- **Arrange-Act-Assert**: Standard test structure
- **Fixtures**: Reusable test data and setup
- **Parameterized Tests**: Multiple scenario testing
- **Mocking**: Component isolation
- **Property-Based Testing**: Automated test case generation

## Security Considerations

### Input Validation
- Use `yaml.safe_load()` to prevent code execution
- Validate file paths to prevent directory traversal
- Sanitize user-provided content

### File Operations
- Atomic file operations where possible
- Permission checks before operations
- Secure backup file creation and management

## Extensibility

### Plugin Architecture
Support for custom conversion plugins and validators through abstract base classes.

### Configuration Flexibility
Multiple configuration sources with clear precedence hierarchy.

---

This modular architecture provides a solid foundation for the FQCN Converter while maintaining flexibility for future enhancements.