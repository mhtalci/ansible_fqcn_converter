"""
Performance monitoring decorators and context managers.

This module provides easy-to-use decorators and context managers
for monitoring performance in tests and production code.
"""

import time
import functools
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager

from .performance_baselines import PerformanceBaselineManager


class PerformanceMonitor:
    """Performance monitoring utility with baseline integration."""
    
    def __init__(self, baseline_manager: Optional[PerformanceBaselineManager] = None):
        """Initialize performance monitor."""
        self.baseline_manager = baseline_manager or PerformanceBaselineManager()
    
    def monitor_performance(self, operation_name: str, 
                          parameters: Optional[Dict[str, Any]] = None,
                          validate_against_baseline: bool = True,
                          tolerance_factor: float = 2.0):
        """Decorator to monitor function performance."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Extract parameters for monitoring
                monitor_params = parameters or {}
                if not monitor_params:
                    # Try to extract meaningful parameters from function arguments
                    monitor_params = self._extract_parameters(func, args, kwargs)
                
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    success = True
                except Exception as e:
                    success = False
                    raise
                finally:
                    duration = time.time() - start_time
                    
                    # Record measurement
                    self.baseline_manager.record_measurement(
                        operation_name, duration, monitor_params, success
                    )
                    
                    # Validate against baseline if requested and successful
                    if success and validate_against_baseline:
                        is_valid, message = self.baseline_manager.validate_performance(
                            operation_name, duration, tolerance_factor
                        )
                        if not is_valid:
                            print(f"Performance warning for {operation_name}: {message}")
                
                return result
            return wrapper
        return decorator
    
    @contextmanager
    def measure_operation(self, operation_name: str,
                         parameters: Optional[Dict[str, Any]] = None,
                         validate_against_baseline: bool = True,
                         tolerance_factor: float = 2.0):
        """Context manager to measure operation performance."""
        start_time = time.time()
        success = True
        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            duration = time.time() - start_time
            
            # Record measurement
            self.baseline_manager.record_measurement(
                operation_name, duration, parameters or {}, success
            )
            
            # Validate against baseline if requested and successful
            if success and validate_against_baseline:
                is_valid, message = self.baseline_manager.validate_performance(
                    operation_name, duration, tolerance_factor
                )
                if not is_valid:
                    print(f"Performance warning for {operation_name}: {message}")
    
    def _extract_parameters(self, func: Callable, args: tuple, kwargs: dict) -> Dict[str, Any]:
        """Extract meaningful parameters from function call."""
        import inspect
        
        try:
            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Extract parameters that might be relevant for performance
            relevant_params = {}
            for param_name, param_value in bound_args.arguments.items():
                # Include numeric parameters and string lengths
                if isinstance(param_value, (int, float)):
                    relevant_params[param_name] = param_value
                elif isinstance(param_value, str):
                    relevant_params[f"{param_name}_length"] = len(param_value)
                elif hasattr(param_value, '__len__'):
                    try:
                        relevant_params[f"{param_name}_length"] = len(param_value)
                    except (TypeError, AttributeError):
                        pass
            
            return relevant_params
        except Exception:
            # If parameter extraction fails, return empty dict
            return {}
    
    def establish_baseline_for_function(self, func: Callable, operation_name: str,
                                      parameter_sets: list,
                                      min_samples: int = 5) -> None:
        """Establish baseline for a function with different parameter sets."""
        def measurement_func(**params):
            return func(**params)
        
        self.baseline_manager.establish_baseline(
            operation_name, measurement_func, parameter_sets, min_samples
        )
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        return self.baseline_manager.generate_performance_report()


# Global performance monitor instance
_global_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def monitor_performance(operation_name: str, 
                       parameters: Optional[Dict[str, Any]] = None,
                       validate_against_baseline: bool = True,
                       tolerance_factor: float = 2.0):
    """Convenience decorator using global monitor."""
    return get_performance_monitor().monitor_performance(
        operation_name, parameters, validate_against_baseline, tolerance_factor
    )


@contextmanager
def measure_operation(operation_name: str,
                     parameters: Optional[Dict[str, Any]] = None,
                     validate_against_baseline: bool = True,
                     tolerance_factor: float = 2.0):
    """Convenience context manager using global monitor."""
    with get_performance_monitor().measure_operation(
        operation_name, parameters, validate_against_baseline, tolerance_factor
    ):
        yield