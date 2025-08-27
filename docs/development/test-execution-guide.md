# Test Execution Guide

## Overview

This guide provides comprehensive documentation for executing tests in the FQCN Converter project, including parallel execution procedures, troubleshooting, coverage improvement strategies, and CI/CD integration.

## Quick Start

### Basic Test Execution

```bash
# Run all tests
make test

# Run specific test categories
pytest tests/unit/                    # Unit tests only
pytest tests/integration/             # Integration tests only
pytest tests/performance/             # Performance tests only

# Run with coverage
pytest --cov=src/fqcn_converter --cov-report=html
```

### Parallel Test Execution

```bash
# Auto-detect CPU cores and run in parallel
pytest --numprocesses=auto

# Specify number of workers
pytest --numprocesses=4

# Use specific distribution strategy
pytest --numprocesses=auto --dist=loadscope
```

## Parallel Test Execution Procedures

### Configuration

The project supports parallel test execution using `pytest-xdist`. Configuration is managed through multiple pytest configuration files:

- `pytest.ini` - Base configuration
- `pytest-parallel.ini` - Parallel-specific settings
- `pytest-comprehensive.ini` - Comprehensive test suite settings

### Best Practices

#### 1. Test Isolation
- Use isolated temporary directories for each test
- Avoid shared global state between tests
- Use proper fixtures for resource management

```python
@pytest.fixture
def isolated_temp_dir():
    """Provides isolated temporary directory per test worker"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir
```

#### 2. Resource Management
- Mock external dependencies to avoid conflicts
- Use worker-specific configuration when needed
- Ensure proper cleanup in test teardown

```python
@pytest.fixture(autouse=True)
def setup_test_environment(worker_id):
    """Setup isolated environment per worker"""
    if worker_id != "master":
        # Worker-specific setup
        os.environ["TEST_WORKER_ID"] = worker_id
    yield
    # Cleanup
```

#### 3. Test Distribution Strategies

**loadscope** (Recommended)
- Distributes test classes/modules to workers
- Good for tests with similar execution time
- Maintains test isolation at class level

**loadfile**
- Distributes entire test files to workers
- Good for large test files
- Better for integration tests

**worksteal**
- Dynamic work distribution
- Good for tests with varying execution times
- Optimal resource utilization

### Execution Commands

```bash
# Recommended parallel execution
pytest --numprocesses=auto --dist=loadscope --maxfail=5

# For integration tests
pytest tests/integration/ --numprocesses=2 --dist=loadfile

# For performance tests (sequential recommended)
pytest tests/performance/ --numprocesses=1

# With comprehensive reporting
pytest --numprocesses=auto --cov=src/fqcn_converter \
       --cov-report=html --cov-report=xml \
       --junit-xml=test_reports/junit/results.xml
```

## Test Categories and Execution

### Unit Tests
- **Location**: `tests/unit/`
- **Execution Time**: Fast (< 1 second per test)
- **Parallel Safe**: Yes
- **Coverage Target**: >95%

```bash
# Run unit tests in parallel
pytest tests/unit/ --numprocesses=auto --dist=loadscope
```

### Integration Tests
- **Location**: `tests/integration/`
- **Execution Time**: Medium (1-10 seconds per test)
- **Parallel Safe**: Limited (use fewer workers)
- **Coverage Target**: >90%

```bash
# Run integration tests with limited parallelism
pytest tests/integration/ --numprocesses=2 --dist=loadfile
```

### Performance Tests
- **Location**: `tests/performance/`
- **Execution Time**: Variable (can be slow)
- **Parallel Safe**: No (run sequentially)
- **Coverage Target**: N/A (focused on performance)

```bash
# Run performance tests sequentially
pytest tests/performance/ --numprocesses=1 -v
```

## Coverage Improvement Strategies

### Current Coverage Status

| Module | Current Coverage | Target | Priority |
|--------|------------------|---------|----------|
| `core/converter.py` | 95% | 95% | ✅ Met |
| `core/validator.py` | 92% | 92% | ✅ Met |
| `core/batch.py` | 76% | 90% | 🔴 High |
| `cli/batch.py` | 0% | 90% | 🔴 Critical |
| `utils/logging.py` | 70% | 90% | 🔴 High |

### Coverage Analysis Commands

```bash
# Generate detailed coverage report
pytest --cov=src/fqcn_converter --cov-report=html --cov-report=term-missing

# Coverage with branch analysis
pytest --cov=src/fqcn_converter --cov-branch --cov-report=html

# Fail if coverage below threshold
pytest --cov=src/fqcn_converter --cov-fail-under=90

# Generate XML report for CI/CD
pytest --cov=src/fqcn_converter --cov-report=xml:coverage.xml
```

### Identifying Coverage Gaps

1. **Review HTML Coverage Report**
   ```bash
   pytest --cov=src/fqcn_converter --cov-report=html
   open htmlcov/index.html
   ```

2. **Analyze Missing Lines**
   ```bash
   # Show missing lines in terminal
   pytest --cov=src/fqcn_converter --cov-report=term-missing
   ```

3. **Focus on Uncovered Branches**
   ```bash
   # Include branch coverage
   pytest --cov=src/fqcn_converter --cov-branch --cov-report=term-missing
   ```

### Coverage Improvement Process

#### 1. Analyze Current Coverage
```bash
# Generate baseline coverage report
pytest --cov=src/fqcn_converter --cov-report=html --cov-report=json

# Review coverage.json for programmatic analysis
python scripts/analyze_coverage.py coverage.json
```

#### 2. Identify Priority Areas
- Focus on modules with <90% coverage
- Prioritize error handling paths
- Target complex business logic
- Cover edge cases and boundary conditions

#### 3. Write Targeted Tests
```python
# Example: Testing error handling paths
def test_batch_processor_file_not_found():
    """Test batch processor handles missing files gracefully"""
    processor = BatchProcessor()
    with pytest.raises(FileNotFoundError):
        processor.process_file("/nonexistent/file.yml")

def test_batch_processor_permission_error():
    """Test batch processor handles permission errors"""
    # Create file with restricted permissions
    # Test error handling
```

#### 4. Validate Coverage Improvements
```bash
# Run tests and verify coverage increase
pytest tests/unit/test_batch_core_complete.py --cov=src/fqcn_converter/core/batch.py --cov-report=term-missing
```

### Maintenance Procedures

#### Daily Coverage Monitoring
```bash
# Quick coverage check
make test-coverage-quick

# Generate coverage badge
python scripts/generate_coverage_badge.py
```

#### Weekly Coverage Review
```bash
# Comprehensive coverage analysis
make test-coverage-comprehensive

# Generate coverage trend report
python scripts/coverage_trend_analysis.py
```

#### Coverage Quality Gates
- **Pre-commit**: Minimum 85% coverage for changed files
- **PR Review**: No decrease in overall coverage
- **Release**: Minimum 90% overall coverage

## Performance Monitoring

### Performance Test Execution

```bash
# Run performance tests with profiling
pytest tests/performance/ --profile --profile-svg

# Run with memory profiling
pytest tests/performance/ --memray

# Generate performance report
python scripts/performance_reporter.py
```

### Performance Baselines

Current performance baselines (adjust based on hardware):

| Test Category | Baseline | Tolerance | Hardware |
|---------------|----------|-----------|----------|
| Small files (< 1KB) | 50ms | ±20ms | Standard CI |
| Medium files (1-10KB) | 150ms | ±50ms | Standard CI |
| Large files (> 10KB) | 400ms | ±100ms | Standard CI |
| Batch processing (100 files) | 800ms | ±200ms | Standard CI |

### Adaptive Performance Testing

```python
# Example: Hardware-adaptive performance testing
@pytest.mark.performance
def test_validation_performance_adaptive():
    """Performance test that adapts to hardware capabilities"""
    # Detect system capabilities
    cpu_count = os.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    # Adjust expectations based on hardware
    if cpu_count >= 8 and memory_gb >= 16:
        max_time = 0.1  # High-end system
    elif cpu_count >= 4 and memory_gb >= 8:
        max_time = 0.2  # Standard system
    else:
        max_time = 0.4  # Lower-end system
    
    # Run performance test with adaptive threshold
    start_time = time.time()
    result = validate_large_dataset()
    execution_time = time.time() - start_time
    
    assert execution_time < max_time, f"Performance test failed: {execution_time}s > {max_time}s"
```

## Test Environment Setup

### Local Development Environment

```bash
# Install test dependencies
pip install -r requirements.txt
pip install -r test-requirements.txt

# Setup pre-commit hooks
pre-commit install

# Verify test environment
python scripts/check-tools.py
```

### Docker Test Environment

```bash
# Build test container
docker build -f Dockerfile.test -t fqcn-converter-test .

# Run tests in container
docker run --rm -v $(pwd):/app fqcn-converter-test pytest

# Run with coverage
docker run --rm -v $(pwd):/app fqcn-converter-test \
    pytest --cov=src/fqcn_converter --cov-report=html
```

### Virtual Environment Setup

```bash
# Create isolated test environment
python -m venv test-env
source test-env/bin/activate  # Linux/Mac
# test-env\Scripts\activate  # Windows

# Install dependencies
pip install -e .
pip install -r test-requirements.txt

# Verify installation
pytest --version
pytest --collect-only tests/
```

## Test Data Management

### Test Fixtures and Data

```python
# Shared test data
@pytest.fixture(scope="session")
def sample_ansible_content():
    """Provides sample Ansible content for testing"""
    return {
        "playbook": "tests/fixtures/sample_playbook.yml",
        "inventory": "tests/fixtures/sample_inventory.yml",
        "roles": "tests/fixtures/sample_roles/"
    }

# Temporary test data
@pytest.fixture
def temp_test_files(tmp_path):
    """Creates temporary test files"""
    test_files = []
    for i in range(5):
        file_path = tmp_path / f"test_file_{i}.yml"
        file_path.write_text(f"test_content_{i}")
        test_files.append(file_path)
    return test_files
```

### Test Data Cleanup

```python
@pytest.fixture(autouse=True)
def cleanup_test_environment():
    """Ensures clean test environment"""
    # Pre-test cleanup
    cleanup_temp_files()
    reset_global_state()
    
    yield
    
    # Post-test cleanup
    cleanup_temp_files()
    reset_logging_configuration()
    clear_caches()
```

## Next Steps

1. **Review Current Test Status**: Run `make test-status` to see current test health
2. **Identify Priority Areas**: Focus on modules with low coverage
3. **Implement Missing Tests**: Use this guide to add comprehensive test coverage
4. **Setup CI/CD Integration**: Follow the CI/CD integration examples
5. **Monitor and Maintain**: Use the maintenance procedures for ongoing test health

For specific implementation examples and troubleshooting, see the following sections in this guide.