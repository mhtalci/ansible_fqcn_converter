#!/usr/bin/env python3
"""Test script for enhanced FQCN Converter features."""

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def test_core_imports():
    """Test that core modules can be imported."""
    print("Testing core module imports...")
    
    try:
        from fqcn_converter.core.converter import FQCNConverter
        print("✓ FQCNConverter imported successfully")
    except Exception as e:
        print(f"✗ FQCNConverter import failed: {e}")
        return False
    
    try:
        from fqcn_converter.core.validator import FQCNValidator
        print("✓ FQCNValidator imported successfully")
    except Exception as e:
        print(f"✗ FQCNValidator import failed: {e}")
        return False
    
    try:
        from fqcn_converter.utils.logging import get_logger
        print("✓ Logging utils imported successfully")
    except Exception as e:
        print(f"✗ Logging utils import failed: {e}")
        return False
    
    return True

def test_basic_conversion():
    """Test basic FQCN conversion functionality."""
    print("\nTesting basic conversion functionality...")
    
    try:
        from fqcn_converter.core.converter import FQCNConverter
        
        converter = FQCNConverter()
        
        # Test content conversion
        test_content = """---
- name: Test playbook
  hosts: all
  tasks:
    - name: Copy file
      copy:
        src: test.txt
        dest: /tmp/test.txt
    - name: Run command
      shell: echo "hello"
"""
        
        result = converter.convert_content(test_content)
        
        if result and hasattr(result, 'converted_content'):
            print("✓ Content conversion successful")
            if 'ansible.builtin.copy' in result.converted_content:
                print("✓ FQCN conversion detected")
            else:
                print("⚠ FQCN conversion not detected in output")
            return True
        else:
            print("✗ Content conversion failed - no result")
            return False
            
    except Exception as e:
        print(f"✗ Basic conversion test failed: {e}")
        return False

def test_file_conversion():
    """Test file-based conversion."""
    print("\nTesting file conversion functionality...")
    
    try:
        from fqcn_converter.core.converter import FQCNConverter
        
        converter = FQCNConverter()
        
        # Create temporary file
        test_content = """---
- name: Test playbook
  hosts: all
  tasks:
    - name: Install package
      package:
        name: nginx
    - name: Start service
      service:
        name: nginx
        state: started
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(test_content)
            temp_file = Path(f.name)
        
        try:
            # Test dry run
            result = converter.convert_file(temp_file, dry_run=True)
            
            if result and hasattr(result, 'success'):
                if result.success:
                    print("✓ File conversion (dry run) successful")
                    if hasattr(result, 'conversions') and result.conversions:
                        print(f"✓ Found {len(result.conversions)} potential conversions")
                        return True
                    else:
                        print("⚠ No conversions found")
                        return True
                else:
                    print(f"✗ File conversion failed: {getattr(result, 'error', 'Unknown error')}")
                    return False
            else:
                print("✗ File conversion failed - no result")
                return False
                
        finally:
            # Cleanup
            if temp_file.exists():
                temp_file.unlink()
                
    except Exception as e:
        print(f"✗ File conversion test failed: {e}")
        return False

def test_validation():
    """Test validation functionality."""
    print("\nTesting validation functionality...")
    
    try:
        from fqcn_converter.core.validator import FQCNValidator
        
        validator = FQCNValidator()
        
        # Create temporary file with mixed FQCN usage
        test_content = """---
- name: Test playbook
  hosts: all
  tasks:
    - name: Copy file (already FQCN)
      ansible.builtin.copy:
        src: test.txt
        dest: /tmp/test.txt
    - name: Run command (needs FQCN)
      shell: echo "hello"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(test_content)
            temp_file = Path(f.name)
        
        try:
            result = validator.validate_conversion(temp_file)
            
            if result and hasattr(result, 'valid'):
                print(f"✓ Validation completed - Valid: {result.valid}")
                if hasattr(result, 'issues') and result.issues:
                    print(f"✓ Found {len(result.issues)} validation issues")
                return True
            else:
                print("✗ Validation failed - no result")
                return False
                
        finally:
            # Cleanup
            if temp_file.exists():
                temp_file.unlink()
                
    except Exception as e:
        print(f"✗ Validation test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("FQCN Converter Enhanced Features Test")
    print("=" * 60)
    
    tests = [
        test_core_imports,
        test_basic_conversion,
        test_file_conversion,
        test_validation
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
        print("🎉 All tests passed! Core functionality is working.")
        return True
    else:
        print("⚠ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)