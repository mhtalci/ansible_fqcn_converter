#!/usr/bin/env python3
"""Test script for interactive mode."""

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def test_interactive_import():
    """Test that interactive mode can be imported."""
    print("Testing interactive mode import...")
    
    try:
        from fqcn_converter.cli.interactive import InteractiveMode
        print("✓ InteractiveMode imported successfully")
        return True
    except Exception as e:
        print(f"✗ InteractiveMode import failed: {e}")
        return False

def test_interactive_initialization():
    """Test interactive mode initialization."""
    print("\nTesting interactive mode initialization...")
    
    try:
        from fqcn_converter.cli.interactive import InteractiveMode
        
        interactive_mode = InteractiveMode()
        
        # Check basic attributes
        assert hasattr(interactive_mode, 'converter')
        assert hasattr(interactive_mode, 'validator')
        assert hasattr(interactive_mode, 'session_stats')
        
        print("✓ InteractiveMode initialized successfully")
        print(f"✓ Session stats: {interactive_mode.session_stats}")
        return True
        
    except Exception as e:
        print(f"✗ InteractiveMode initialization failed: {e}")
        return False

def test_interactive_methods():
    """Test interactive mode methods."""
    print("\nTesting interactive mode methods...")
    
    try:
        from fqcn_converter.cli.interactive import InteractiveMode
        
        interactive_mode = InteractiveMode()
        
        # Test print methods (they should not raise exceptions)
        interactive_mode._print_success("Test success message")
        interactive_mode._print_info("Test info message")
        interactive_mode._print_warning("Test warning message")
        interactive_mode._print_error("Test error message")
        
        print("✓ Print methods work correctly")
        
        # Test session summary
        interactive_mode._print_session_summary()
        print("✓ Session summary works correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Interactive mode methods test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("FQCN Converter Interactive Mode Test")
    print("=" * 60)
    
    tests = [
        test_interactive_import,
        test_interactive_initialization,
        test_interactive_methods
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All interactive mode tests passed!")
        return True
    else:
        print("⚠ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)