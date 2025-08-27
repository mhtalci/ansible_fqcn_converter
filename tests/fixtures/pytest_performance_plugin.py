"""
Pytest plugin for performance monitoring integration.

This plugin automatically monitors performance of tests marked with
@pytest.mark.performance and integrates with the baseline system.
"""

import pytest
import time
from typing import Dict, Any

from .performance_monitor import get_performance_monitor
from .performance_baselines import PerformanceBaselineManager
from .performance_reporter import PerformanceReporter


class PerformanceTestPlugin:
    """Pytest plugin for performance monitoring."""
    
    def __init__(self):
        """Initialize the plugin."""
        self.monitor = get_performance_monitor()
        self.test_results = {}
        self.start_times = {}
    
    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_setup(self, item):
        """Called before each test runs."""
        if item.get_closest_marker("performance"):
            # Record start time for performance tests
            self.start_times[item.nodeid] = time.time()
    
    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_teardown(self, item, nextitem):
        """Called after each test runs."""
        if item.nodeid in self.start_times:
            # Calculate test duration
            duration = time.time() - self.start_times[item.nodeid]
            
            # Extract test information
            test_name = item.name
            test_class = item.cls.__name__ if item.cls else "standalone"
            operation_name = f"{test_class}.{test_name}"
            
            # Extract parameters from test
            parameters = self._extract_test_parameters(item)
            
            # Record measurement
            success = not hasattr(item, "rep_call") or item.rep_call.passed
            self.monitor.baseline_manager.record_measurement(
                operation_name, duration, parameters, success
            )
            
            # Store result for reporting
            self.test_results[item.nodeid] = {
                "operation_name": operation_name,
                "duration": duration,
                "parameters": parameters,
                "success": success
            }
            
            # Clean up
            del self.start_times[item.nodeid]
    
    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        """Hook to capture test results."""
        outcome = yield
        rep = outcome.get_result()
        
        # Store the report for later use
        setattr(item, f"rep_{rep.when}", rep)
    
    def pytest_sessionfinish(self, session, exitstatus):
        """Called when the test session finishes."""
        if self.test_results:
            print(f"\nPerformance monitoring captured {len(self.test_results)} performance tests")
            
            # Generate performance summary
            self._generate_session_summary()
    
    def _extract_test_parameters(self, item) -> Dict[str, Any]:
        """Extract meaningful parameters from test item."""
        parameters = {}
        
        # Extract parametrize values
        if hasattr(item, "callspec"):
            parameters.update(item.callspec.params)
        
        # Extract from test name if it contains parameter info
        if "[" in item.name and "]" in item.name:
            param_str = item.name[item.name.find("[")+1:item.name.find("]")]
            # Simple parameter extraction for common patterns
            if "-" in param_str:
                parts = param_str.split("-")
                for i, part in enumerate(parts):
                    if part.isdigit():
                        parameters[f"param_{i}"] = int(part)
                    else:
                        try:
                            parameters[f"param_{i}"] = float(part)
                        except ValueError:
                            parameters[f"param_{i}"] = part
        
        return parameters
    
    def _generate_session_summary(self):
        """Generate summary of performance test session."""
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result["success"])
        
        print(f"Performance Summary:")
        print(f"  Total performance tests: {total_tests}")
        print(f"  Successful tests: {successful_tests}")
        print(f"  Failed tests: {total_tests - successful_tests}")
        
        if successful_tests > 0:
            # Calculate average duration by operation
            operations = {}
            for result in self.test_results.values():
                if result["success"]:
                    op_name = result["operation_name"]
                    if op_name not in operations:
                        operations[op_name] = []
                    operations[op_name].append(result["duration"])
            
            print(f"  Average durations:")
            for op_name, durations in operations.items():
                avg_duration = sum(durations) / len(durations)
                print(f"    {op_name}: {avg_duration:.3f}s")


# Plugin registration
def pytest_configure(config):
    """Register the performance plugin."""
    if not hasattr(config, "_performance_plugin"):
        config._performance_plugin = PerformanceTestPlugin()
        config.pluginmanager.register(config._performance_plugin, "performance_monitor")


def pytest_unconfigure(config):
    """Unregister the performance plugin."""
    if hasattr(config, "_performance_plugin"):
        config.pluginmanager.unregister(config._performance_plugin)
        del config._performance_plugin