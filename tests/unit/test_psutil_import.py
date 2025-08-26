#!/usr/bin/env python3
"""
Test psutil import error handling.
"""

import sys
from unittest.mock import patch
import pytest

from fqcn_converter.utils.logging import PerformanceFilter


class TestPsutilImportError:
    """Test psutil import error handling."""

    def test_memory_usage_without_psutil(self):
        """Test memory usage calculation when psutil import fails."""
        filter_obj = PerformanceFilter()
        
        # Mock the import to fail
        original_import = __builtins__['__import__']
        
        def mock_import(name, *args, **kwargs):
            if name == 'psutil':
                raise ImportError("No module named 'psutil'")
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            # This should trigger the ImportError path
            memory_usage = filter_obj._get_memory_usage()
            assert memory_usage == 0.0