# Test Troubleshooting Guide

## Common Test Execution Issues

### Parallel Test Execution Problems

#### Issue: Tests Fail in Parallel but Pass Sequentially

**Symptoms:**
- Tests pass when run with `pytest tests/`
- Tests fail when run with `pytest --numprocesses=auto`
- Intermittent failures in parallel mode

**Causes:**
- Shared global state between tests
- Race conditions in file operations
- Conflicting temporary file usage
- Database connection conflicts

**Solutions:**

1. **Isolate Test State**
   ```python
   # Bad: Shared global state
   GLOBAL_CONFIG = {}
   
   def test_something():
       GLOBAL_CONFIG['key'] = 'value'  # Affects other tests
   
   # Good: Isolated state
   @pytest.fixture
   def isolated_config():
       return {'key': 'value'}
   
   def test_something(isolated_config):
       # Use isolated config
   ```

2. **Use Worker-Specific Resources**
   ```python
   @pytest.fixture
   def worker_temp_dir(worker_id):
       """Create worker-specific temporary directory"""
       if worker_id == "master":
           # Sequential execution
           temp_dir = tempfile.mkdtemp()
       else:
           # Parallel execution
           temp_dir = tempfile.mkdtemp(prefix=f"worker_{worker_id}_")
       
       yield temp_dir
       shutil.rmtree(temp_dir, ignore_errors=True)
   ```

3. **Mock External Dependencies**
   ```python
   @pytest.fixture(autouse=True)
   def mock_external_services():
       """Mock external services to avoid conflicts"""
       with patch('requests.get') as mock_get:
           mock_get.return_value.status_code = 200
           yield mock_get
   ```

#### Issue: Resource Conflicts in Parallel Execution

**Symptoms:**
- `PermissionError` or `FileExistsError` in parallel mode
- Database lock errors
- Port binding conflicts

**Solutions:**

1. **Use Unique Resource Names**
   ```python
   import uuid
   
   @pytest.fixture
   def unique_filename():
       """Generate unique filename per test"""
       return f"test_file_{uuid.uuid4().hex[:8]}.yml"
   ```

2. **Implement Resource Locking**
   ```python
   import fcntl
   
   @pytest.fixture
   def file_lock():
       """Provide file locking for shared resources"""
       lock_file = "/tmp/test_lock"
       with open(lock_file, 'w') as f:
           fcntl.flock(f.fileno(), fcntl.LOCK_EX)
           yield
           fcntl.flock(f.fileno(), fcntl.LOCK_UN)
   ```

3. **Use Process-Safe Operations**
   ```python
   def create_temp_file_safely():
       """Create temporary file with process safety"""
       fd, path = tempfile.mkstemp(prefix=f"test_{os.getpid()}_")
       try:
           with os.fdopen(fd, 'w') as f:
               f.write("test content")
           return path
       except:
           os.unlink(path)
           raise
   ```

### Coverage Issues

#### Issue: Coverage Reports Show Incorrect Results

**Symptoms:**
- Coverage percentage doesn't match expectations
- Missing lines not highlighted correctly
- Branch coverage inconsistencies

**Diagnosis:**
```bash
# Check coverage configuration
pytest --cov-config=.coveragerc --cov=src/fqcn_converter --cov-report=term-missing

# Verify source paths
pytest --cov=src/fqcn_converter --cov-report=term-missing -v

# Debug coverage collection
pytest --cov=src/fqcn_converter --cov-report=term-missing --cov-debug=trace
```

**Solutions:**

1. **Fix Coverage Configuration**
   ```ini
   # .coveragerc
   [run]
   source = src/fqcn_converter
   omit = 
       */tests/*
       */venv/*
       */__pycache__/*
   
   [report]
   exclude_lines =
       pragma: no cover
       def __repr__
       raise AssertionError
       raise NotImplementedError
   ```

2. **Ensure Proper Import Paths**
   ```python
   # Ensure tests import from source, not installed package
   import sys
   sys.path.insert(0, 'src')
   
   from fqcn_converter.core.converter import Converter
   ```

3. **Use Absolute Coverage Paths**
   ```bash
   # Use absolute paths for consistent coverage
   pytest --cov=$(pwd)/src/fqcn_converter --cov-report=html
   ```

#### Issue: Low Coverage Despite Comprehensive Tests

**Symptoms:**
- Tests cover functionality but coverage reports low percentage
- Missing coverage in error handling paths
- Unreachable code showing as uncovered

**Investigation:**
```bash
# Generate detailed coverage report
pytest --cov=src/fqcn_converter --cov-branch --cov-report=html

# Analyze specific module
pytest tests/unit/test_converter.py --cov=src/fqcn_converter/core/converter.py --cov-report=term-missing

# Check for dead code
vulture src/fqcn_converter/
```

**Solutions:**

1. **Add Error Path Testing**
   ```python
   def test_error_handling_paths():
       """Test all error handling branches"""
       converter = Converter()
       
       # Test file not found
       with pytest.raises(FileNotFoundError):
           converter.convert_file("/nonexistent/file.yml")
       
       # Test permission error
       with patch('builtins.open', side_effect=PermissionError):
           with pytest.raises(PermissionError):
               converter.convert_file("test.yml")
   ```

2. **Test Edge Cases**
   ```python
   @pytest.mark.parametrize("input_data,expected_error", [
       ("", YAMLParsingError),
       ("invalid: yaml: content", YAMLParsingError),
       (None, ValueError),
   ])
   def test_edge_cases(input_data, expected_error):
       converter = Converter()
       with pytest.raises(expected_error):
           converter.convert_content(input_data)
   ```

3. **Remove Dead Code**
   ```python
   # Remove unreachable code or add pragma
   def some_function():
       if condition:
           return result
       else:
           raise NotImplementedError  # pragma: no cover
   ```

### Performance Test Issues

#### Issue: Performance Tests Fail on Different Hardware

**Symptoms:**
- Tests pass on development machine but fail in CI
- Inconsistent timing results
- Hardware-dependent performance expectations

**Solutions:**

1. **Implement Adaptive Thresholds**
   ```python
   import psutil
   
   def get_performance_threshold():
       """Calculate performance threshold based on hardware"""
       cpu_count = os.cpu_count()
       memory_gb = psutil.virtual_memory().total / (1024**3)
       
       # Base threshold
       base_time = 0.1
       
       # Adjust for CPU
       if cpu_count < 4:
           base_time *= 1.5
       elif cpu_count > 8:
           base_time *= 0.8
       
       # Adjust for memory
       if memory_gb < 8:
           base_time *= 1.3
       elif memory_gb > 16:
           base_time *= 0.9
       
       return base_time
   
   def test_performance_adaptive():
       threshold = get_performance_threshold()
       start_time = time.time()
       # ... perform operation
       execution_time = time.time() - start_time
       assert execution_time < threshold
   ```

2. **Use Statistical Analysis**
   ```python
   def test_performance_statistical():
       """Use statistical analysis for performance validation"""
       times = []
       for _ in range(10):
           start_time = time.time()
           # ... perform operation
           times.append(time.time() - start_time)
       
       # Use median and percentiles
       median_time = statistics.median(times)
       p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile
       
       assert median_time < 0.1, f"Median time too high: {median_time}"
       assert p95_time < 0.2, f"95th percentile too high: {p95_time}"
   ```

3. **Environment-Specific Baselines**
   ```python
   # conftest.py
   @pytest.fixture(scope="session")
   def performance_baseline():
       """Establish performance baseline for current environment"""
       # Run calibration test
       start_time = time.time()
       # Standard operation for calibration
       for i in range(1000):
           _ = i ** 2
       calibration_time = time.time() - start_time
       
       # Calculate baseline multiplier
       baseline_multiplier = max(1.0, calibration_time / 0.001)  # Expected 1ms
       
       return {
           'multiplier': baseline_multiplier,
           'cpu_count': os.cpu_count(),
           'memory_gb': psutil.virtual_memory().total / (1024**3)
       }
   ```

### Test Discovery and Collection Issues

#### Issue: Tests Not Being Discovered

**Symptoms:**
- `pytest --collect-only` shows fewer tests than expected
- Specific test files not being run
- Test functions not being collected

**Diagnosis:**
```bash
# Check test discovery
pytest --collect-only -v

# Check specific directory
pytest --collect-only tests/unit/ -v

# Debug collection issues
pytest --collect-only --tb=short -v
```

**Solutions:**

1. **Fix Naming Conventions**
   ```python
   # Ensure proper naming
   # File: test_*.py or *_test.py
   # Class: Test*
   # Function: test_*
   
   # Good
   def test_converter_functionality():
       pass
   
   class TestConverter:
       def test_convert_file(self):
           pass
   
   # Bad - won't be discovered
   def converter_test():  # Missing 'test_' prefix
       pass
   ```

2. **Check Import Errors**
   ```bash
   # Check for import errors preventing collection
   python -m pytest --collect-only --tb=line
   
   # Test imports manually
   python -c "import tests.unit.test_converter"
   ```

3. **Verify pytest Configuration**
   ```ini
   # pytest.ini
   [tool:pytest]
   testpaths = tests
   python_files = test_*.py *_test.py
   python_classes = Test*
   python_functions = test_*
   ```

### Memory and Resource Issues

#### Issue: Tests Consume Excessive Memory

**Symptoms:**
- Tests killed by OS (OOM killer)
- Slow test execution due to memory pressure
- Memory leaks in test execution

**Diagnosis:**
```bash
# Monitor memory usage during tests
pytest --memray tests/

# Profile memory usage
python -m memory_profiler pytest tests/unit/

# Check for memory leaks
pytest --tb=short -v --capture=no
```

**Solutions:**

1. **Implement Proper Cleanup**
   ```python
   @pytest.fixture
   def large_dataset():
       """Provide large dataset with proper cleanup"""
       data = generate_large_dataset()
       yield data
       # Explicit cleanup
       del data
       gc.collect()
   ```

2. **Use Memory-Efficient Patterns**
   ```python
   def test_large_file_processing():
       """Process large files efficiently"""
       # Use generators instead of loading everything into memory
       def process_lines(filename):
           with open(filename, 'r') as f:
               for line in f:
                   yield process_line(line)
       
       # Process in chunks
       for chunk in process_lines("large_file.txt"):
           assert validate_chunk(chunk)
   ```

3. **Limit Concurrent Resource Usage**
   ```python
   # conftest.py
   @pytest.fixture(scope="session")
   def resource_semaphore():
       """Limit concurrent resource-intensive tests"""
       return threading.Semaphore(2)  # Max 2 concurrent
   
   def test_resource_intensive(resource_semaphore):
       with resource_semaphore:
           # Resource-intensive operation
           pass
   ```

## Debugging Test Failures

### Debugging Strategies

#### 1. Increase Verbosity
```bash
# Maximum verbosity
pytest -vvv --tb=long

# Show local variables in tracebacks
pytest --tb=long --showlocals

# Capture and show output
pytest -s --capture=no
```

#### 2. Run Specific Tests
```bash
# Run single test
pytest tests/unit/test_converter.py::test_specific_function -v

# Run test class
pytest tests/unit/test_converter.py::TestConverter -v

# Run with keyword matching
pytest -k "test_converter and not slow" -v
```

#### 3. Use Debugging Tools
```python
# Add breakpoints in tests
def test_debug_example():
    import pdb; pdb.set_trace()  # Debugger breakpoint
    # or
    breakpoint()  # Python 3.7+
    
    result = function_under_test()
    assert result == expected
```

#### 4. Temporary Debug Output
```python
def test_with_debug_output(capfd):
    """Test with debug output capture"""
    print("Debug: Starting test")
    result = function_under_test()
    print(f"Debug: Result is {result}")
    
    # Capture output if needed
    captured = capfd.readouterr()
    print(f"Captured stdout: {captured.out}")
    
    assert result == expected
```

### Common Error Patterns

#### 1. Import Errors
```python
# Error: ModuleNotFoundError
# Solution: Fix Python path
import sys
sys.path.insert(0, 'src')

# Or use proper package installation
pip install -e .
```

#### 2. Fixture Scope Issues
```python
# Error: Fixture scope conflicts
# Solution: Match fixture scopes appropriately
@pytest.fixture(scope="function")  # Default, new instance per test
def temp_file():
    pass

@pytest.fixture(scope="class")  # Shared within test class
def database_connection():
    pass

@pytest.fixture(scope="session")  # Shared across entire test session
def expensive_setup():
    pass
```

#### 3. Async Test Issues
```python
# Error: RuntimeError: This event loop is already running
# Solution: Use pytest-asyncio
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```

## Performance Optimization

### Test Execution Speed

#### 1. Optimize Test Discovery
```bash
# Cache test discovery
pytest --cache-clear  # Clear cache if needed
pytest --collect-only  # Fast collection check
```

#### 2. Use Appropriate Test Markers
```python
# Mark slow tests
@pytest.mark.slow
def test_slow_operation():
    pass

# Skip slow tests in development
pytest -m "not slow"
```

#### 3. Optimize Fixtures
```python
# Use session-scoped fixtures for expensive setup
@pytest.fixture(scope="session")
def expensive_database_setup():
    # Expensive setup once per session
    db = create_test_database()
    yield db
    cleanup_database(db)
```

### Resource Usage Optimization

#### 1. Limit Parallel Workers
```bash
# Adjust based on system resources
pytest --numprocesses=2  # Limit to 2 workers

# Auto-detect but limit
pytest --numprocesses=auto --maxprocesses=4
```

#### 2. Use Test Markers for Resource Management
```python
# Mark resource-intensive tests
@pytest.mark.resource_intensive
def test_memory_heavy():
    pass

# Run resource-intensive tests sequentially
pytest -m "resource_intensive" --numprocesses=1
```

## Continuous Integration Considerations

### CI-Specific Issues

#### 1. Timeout Issues
```yaml
# GitHub Actions example
- name: Run tests with timeout
  run: |
    timeout 30m pytest --numprocesses=auto
  timeout-minutes: 35
```

#### 2. Resource Constraints
```bash
# Adjust for CI environment
if [ "$CI" = "true" ]; then
    # Reduce parallelism in CI
    pytest --numprocesses=2
else
    # Full parallelism locally
    pytest --numprocesses=auto
fi
```

#### 3. Artifact Collection
```bash
# Collect test artifacts on failure
pytest --junit-xml=test-results.xml \
       --cov-report=xml:coverage.xml \
       --html=test-report.html
```

## Getting Help

### Internal Resources
- Review existing test patterns in `tests/unit/`
- Check fixture definitions in `tests/conftest.py`
- Examine CI configuration in `.github/workflows/`

### External Resources
- [pytest documentation](https://docs.pytest.org/)
- [pytest-xdist documentation](https://pytest-xdist.readthedocs.io/)
- [coverage.py documentation](https://coverage.readthedocs.io/)

### Reporting Issues
When reporting test issues, include:
1. Full error message and traceback
2. pytest version and configuration
3. System information (OS, Python version)
4. Steps to reproduce
5. Expected vs actual behavior

```bash
# Collect system information
pytest --version
python --version
pip list | grep pytest
uname -a  # Linux/Mac
systeminfo  # Windows
```