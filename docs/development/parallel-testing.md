# Parallel Test Execution Guide

This document describes the parallel test execution infrastructure for the FQCN Converter project, including setup, configuration, and best practices.

## Overview

The FQCN Converter project supports parallel test execution using pytest-xdist, which allows tests to run concurrently across multiple worker processes. This significantly reduces test execution time while maintaining test reliability and isolation.

## Features

- **Automatic Worker Detection**: Automatically detects optimal number of workers based on CPU cores
- **Resource Isolation**: Each worker gets isolated temporary directories and environment variables
- **Load Balancing**: Intelligent test distribution across workers using different strategies
- **Flexible Configuration**: Support for both sequential and parallel execution modes
- **Comprehensive Reporting**: Detailed coverage and performance reporting for parallel execution

## Configuration Files

### pytest.ini
The main pytest configuration file with sequential execution defaults:
- Standard test discovery and execution settings
- Coverage configuration
- Markers for test categorization
- Logging configuration

### pytest-parallel.ini
Specialized configuration for parallel execution:
- pytest-xdist configuration with automatic worker detection
- Parallel-specific coverage reporting
- Enhanced logging with worker identification
- Load balancing and distribution strategies

### pytest_xdist_config.py
Advanced configuration for pytest-xdist:
- Worker node setup and teardown
- Resource management and cleanup
- Custom load balancing (if needed)
- Worker communication configuration

## Usage

### Command Line Interface

#### Using the Test Runner Script

```bash
# Run tests sequentially
python scripts/run_tests.py sequential

# Run tests in parallel (auto-detect workers)
python scripts/run_tests.py parallel

# Run tests in parallel with specific number of workers
python scripts/run_tests.py parallel --workers 4

# Run tests with coverage in parallel
python scripts/run_tests.py parallel --coverage

# Run specific test categories in parallel
python scripts/run_tests.py parallel --markers "unit"
python scripts/run_tests.py parallel --markers "integration"

# Run performance tests
python scripts/run_tests.py performance

# Validate parallel setup
python scripts/run_tests.py validate
```

#### Using Makefile Targets

```bash
# Sequential execution
make test
make test-cov

# Parallel execution
make test-parallel
make test-parallel-cov

# Specific test categories
make test-unit-parallel
make test-integration-parallel

# Performance tests
make test-performance

# Validate setup
make test-validate-parallel
```

#### Direct pytest Commands

```bash
# Sequential execution
pytest -c pytest.ini

# Parallel execution with auto-detection
pytest -c pytest-parallel.ini

# Parallel execution with specific workers
pytest -c pytest-parallel.ini --numprocesses=4

# Parallel execution with different distribution strategies
pytest -c pytest-parallel.ini --dist=loadscope  # Default
pytest -c pytest-parallel.ini --dist=loadfile   # File-based distribution
pytest -c pytest-parallel.ini --dist=worksteal  # Work-stealing distribution
```

## Test Markers

### Parallel Execution Markers

- `@pytest.mark.parallel_safe`: Tests that are safe to run in parallel
- `@pytest.mark.serial`: Tests that must run serially (not in parallel)
- `@pytest.mark.resource_intensive`: Tests that use significant system resources

### Example Usage

```python
import pytest

@pytest.mark.parallel_safe
def test_safe_for_parallel():
    """This test can run safely in parallel."""
    pass

@pytest.mark.serial
def test_requires_serial_execution():
    """This test must run serially."""
    pass

@pytest.mark.resource_intensive
@pytest.mark.parallel_safe
def test_heavy_computation():
    """This test is resource-intensive but parallel-safe."""
    pass
```

## Fixtures for Parallel Execution

### Core Fixtures

#### `worker_id`
Provides the current worker ID:
```python
def test_worker_identification(worker_id):
    assert worker_id in ['master', 'gw0', 'gw1', 'gw2', ...]
```

#### `isolated_temp_dir`
Provides worker-specific temporary directory:
```python
def test_file_operations(isolated_temp_dir):
    test_file = isolated_temp_dir / "test.txt"
    test_file.write_text("test content")
    assert test_file.exists()
```

#### `parallel_safe_environment`
Sets up isolated environment variables:
```python
def test_environment_setup(parallel_safe_environment):
    env = parallel_safe_environment
    assert env['worker_id'] == os.environ['FQCN_TEST_WORKER_ID']
```

#### `test_execution_context`
Provides comprehensive execution context:
```python
def test_execution_info(test_execution_context):
    context = test_execution_context
    print(f"Worker: {context['worker_id']}")
    print(f"Thread: {context['thread_id']}")
    print(f"Process: {context['process_id']}")
```

### Advanced Fixtures

#### `serial_test_lock`
Provides a lock for tests that need exclusive access:
```python
@pytest.mark.serial
def test_exclusive_resource(serial_test_lock):
    with serial_test_lock:
        # Code that needs exclusive access
        pass
```

#### `mock_config_manager`
Thread-safe configuration manager mock:
```python
def test_config_operations(mock_config_manager):
    mappings = mock_config_manager.load_default_mappings()
    assert isinstance(mappings, dict)
```

## Best Practices

### Writing Parallel-Safe Tests

1. **Use Isolated Resources**: Always use `isolated_temp_dir` instead of shared temporary directories
2. **Avoid Global State**: Don't modify global variables or shared state
3. **Use Worker-Specific Identifiers**: Include worker ID in file names and identifiers
4. **Clean Up Resources**: Ensure proper cleanup in test teardown
5. **Mark Tests Appropriately**: Use `@pytest.mark.parallel_safe` for safe tests

### Example of Parallel-Safe Test

```python
@pytest.mark.parallel_safe
def test_file_conversion(isolated_temp_dir, mock_config_manager, worker_id):
    """Example of a properly written parallel-safe test."""
    # Use isolated temp directory
    input_file = isolated_temp_dir / f"input_{worker_id}.yml"
    output_file = isolated_temp_dir / f"output_{worker_id}.yml"
    
    # Create test content
    input_file.write_text("""
    - name: Test task
      copy:
        src: test.txt
        dest: /tmp/test.txt
    """)
    
    # Perform conversion (using mocked config)
    converter = FQCNConverter(config_manager=mock_config_manager)
    result = converter.convert_file(input_file, output_file)
    
    # Verify results
    assert result.success
    assert output_file.exists()
    
    # Cleanup is handled by fixture teardown
```

### Tests That Should Be Serial

Mark tests as serial if they:
- Modify global configuration
- Use exclusive system resources (ports, files)
- Depend on specific timing or order
- Modify environment variables globally
- Use external services without proper isolation

```python
@pytest.mark.serial
def test_global_configuration():
    """Test that modifies global configuration."""
    # This test needs exclusive access
    pass
```

## Performance Considerations

### Worker Count Optimization

- **Auto-detection**: Use `--numprocesses=auto` for automatic optimization
- **CPU-bound tests**: Use number of CPU cores
- **I/O-bound tests**: Can use more workers than CPU cores
- **Memory-intensive tests**: Use fewer workers to avoid memory pressure

### Distribution Strategies

- **loadscope** (default): Distributes tests by scope (class, module)
- **loadfile**: Distributes entire test files to workers
- **worksteal**: Dynamic work stealing for better load balancing

### Memory Management

- Monitor memory usage with multiple workers
- Use `isolated_temp_dir` to prevent disk space issues
- Clean up resources promptly in test teardown

## Troubleshooting

### Common Issues

#### Tests Failing Only in Parallel Mode

1. Check for shared state or global variables
2. Verify proper use of `isolated_temp_dir`
3. Look for race conditions or timing dependencies
4. Ensure mocks are thread-safe

#### Resource Conflicts

1. Use worker-specific file names
2. Avoid hardcoded ports or paths
3. Use proper fixture isolation
4. Check for environment variable conflicts

#### Performance Issues

1. Reduce number of workers if memory-constrained
2. Use appropriate distribution strategy
3. Profile tests to identify bottlenecks
4. Consider marking slow tests with `@pytest.mark.slow`

### Debugging Parallel Execution

```bash
# Run with verbose output
python scripts/run_tests.py parallel --workers 2 -v

# Run specific test in parallel mode
pytest -c pytest-parallel.ini tests/test_specific.py -v

# Check worker isolation
pytest -c pytest-parallel.ini tests/test_parallel_execution.py -v

# Run with coverage to identify issues
python scripts/run_tests.py parallel --coverage
```

### Validation Commands

```bash
# Validate parallel setup
python scripts/run_tests.py validate

# Test parallel execution with minimal workers
pytest -c pytest-parallel.ini --numprocesses=2 tests/test_parallel_execution.py

# Compare sequential vs parallel results
make test-cov
make test-parallel-cov
# Compare coverage reports
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Run tests in parallel
  run: |
    python scripts/run_tests.py parallel --coverage
    
- name: Upload parallel coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage-parallel.xml
    flags: parallel-tests
```

### Local Development

```bash
# Quick parallel test run
make test-parallel

# Full quality gate with parallel tests
make quality-gate

# Performance comparison
time make test
time make test-parallel
```

## Configuration Reference

### Environment Variables

- `FQCN_TEST_WORKER_ID`: Current worker ID
- `FQCN_TEST_TEMP_DIR`: Worker-specific temporary directory
- `FQCN_TEST_MODE`: 'parallel' or 'sequential'
- `FQCN_CONFIG_DIR`: Worker-specific config directory
- `FQCN_CACHE_DIR`: Worker-specific cache directory

### pytest-xdist Options

- `--numprocesses=N`: Number of worker processes
- `--numprocesses=auto`: Auto-detect optimal worker count
- `--dist=STRATEGY`: Distribution strategy (loadscope, loadfile, worksteal)
- `--maxfail=N`: Stop after N failures across all workers
- `--forked`: Use forked processes for better isolation

### Coverage Configuration

Parallel execution generates separate coverage files:
- `coverage-parallel.xml`: XML format for CI/CD
- `coverage-parallel.json`: JSON format for analysis
- `htmlcov/parallel/`: HTML coverage report

## Future Enhancements

- Custom load balancing based on test execution time
- Integration with test result caching
- Advanced resource monitoring and optimization
- Automatic test categorization for optimal distribution
- Integration with distributed testing across multiple machines