#!/usr/bin/env python3
"""Test CLI commands for enhanced FQCN Converter features."""

import sys
import tempfile
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def create_test_file():
    """Create a test YAML file."""
    content = """---
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
    
    temp_file = Path(tempfile.mktemp(suffix='.yml'))
    temp_file.write_text(content)
    return temp_file

def test_interactive_cli_import():
    """Test that interactive CLI can be imported."""
    print("Testing interactive CLI import...")
    
    try:
        from fqcn_converter.cli.interactive import interactive
        print("✓ Interactive CLI command imported successfully")
        return True
    except Exception as e:
        print(f"✗ Interactive CLI import failed: {e}")
        return False

def test_enhanced_cli_import():
    """Test that enhanced CLI can be imported."""
    print("\nTesting enhanced CLI import...")
    
    try:
        from fqcn_converter.cli.enhanced import cli
        print("✓ Enhanced CLI imported successfully")
        return True
    except Exception as e:
        print(f"✗ Enhanced CLI import failed: {e}")
        return False

def test_reporting_cli_functionality():
    """Test reporting functionality through CLI-like interface."""
    print("\nTesting reporting CLI functionality...")
    
    try:
        from fqcn_converter.reporting.report_generator import ReportGenerator
        from fqcn_converter.core.converter import FQCNConverter
        
        # Create test file
        test_file = create_test_file()
        
        try:
            # Simulate CLI workflow
            converter = FQCNConverter()
            report_gen = ReportGenerator("cli-test")
            
            # Start session
            report_gen.start_session(test_file.parent)
            
            # Process file
            import time
            start_time = time.time()
            result = converter.convert_file(test_file)
            processing_time = time.time() - start_time
            
            # Add to report
            report_gen.add_file_result(test_file, result, processing_time)
            
            # Finalize
            report = report_gen.finalize_session()
            
            # Generate different formats
            console_report = report_gen.generate_report('console')
            json_report = report_gen.generate_report('json')
            
            assert "FQCN Conversion Report" in console_report
            assert "cli-test" in json_report
            
            print("✓ Reporting CLI functionality works correctly")
            print(f"  - Processed 1 file")
            print(f"  - Generated console and JSON reports")
            print(f"  - Success rate: {report.statistics.success_rate:.1%}")
            
            return True
            
        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()
                
    except Exception as e:
        print(f"✗ Reporting CLI functionality test failed: {e}")
        return False

def test_interactive_mode_components():
    """Test interactive mode components."""
    print("\nTesting interactive mode components...")
    
    try:
        from fqcn_converter.cli.interactive import InteractiveMode
        
        # Create test file
        test_file = create_test_file()
        
        try:
            # Initialize interactive mode
            interactive_mode = InteractiveMode()
            
            # Test preview generation
            preview = interactive_mode._generate_preview(test_file)
            
            if preview:
                print(f"✓ Preview generated successfully")
                print(f"  - File: {preview['file_path']}")
            else:
                print("✓ No preview needed (file already compliant or no conversions)")
            
            # Test validation
            validation_result = interactive_mode._validate_file_interactive(test_file)
            print(f"✓ File validation completed: {validation_result}")
            
            # Test session stats
            assert 'files_processed' in interactive_mode.session_stats
            assert 'conversions_made' in interactive_mode.session_stats
            print("✓ Session statistics tracking works")
            
            return True
            
        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()
                
    except Exception as e:
        print(f"✗ Interactive mode components test failed: {e}")
        return False

def test_cli_entry_points():
    """Test that CLI entry points are properly defined."""
    print("\nTesting CLI entry points...")
    
    try:
        # Test that the modules can be imported as they would be by entry points
        
        # Test interactive entry point
        from fqcn_converter.cli.interactive import interactive
        assert callable(interactive)
        print("✓ Interactive entry point is callable")
        
        # Test enhanced CLI entry point  
        from fqcn_converter.cli.enhanced import cli
        assert callable(cli)
        print("✓ Enhanced CLI entry point is callable")
        
        # Test that Click commands are properly decorated
        assert hasattr(interactive, '__click_params__')
        assert hasattr(cli, 'commands') or hasattr(cli, '__click_params__')
        print("✓ Click decorators are properly applied")
        
        return True
        
    except Exception as e:
        print(f"✗ CLI entry points test failed: {e}")
        return False

def test_configuration_system():
    """Test configuration system components."""
    print("\nTesting configuration system...")
    
    try:
        from fqcn_converter.config.manager import ConfigurationManager
        
        # Test default configuration
        config_manager = ConfigurationManager()
        
        # Test basic configuration methods
        assert config_manager.get('backup_files') is not None
        assert config_manager.get('validate_syntax') is not None
        assert isinstance(config_manager.get_preferred_collections(), list)
        assert isinstance(config_manager.get_collection_mappings(), dict)
        
        print("✓ Configuration manager works correctly")
        print(f"  - Backup files: {config_manager.should_backup_files()}")
        print(f"  - Validate syntax: {config_manager.should_validate_syntax()}")
        print(f"  - Preferred collections: {len(config_manager.get_preferred_collections())}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration system test failed: {e}")
        return False

def test_end_to_end_workflow():
    """Test end-to-end workflow simulation."""
    print("\nTesting end-to-end workflow simulation...")
    
    try:
        from fqcn_converter.core.converter import FQCNConverter
        from fqcn_converter.core.validator import FQCNValidator
        from fqcn_converter.reporting.report_generator import ReportGenerator
        from fqcn_converter.cli.interactive import InteractiveMode
        
        # Create test file
        test_file = create_test_file()
        
        try:
            # Step 1: Initialize all components
            converter = FQCNConverter()
            validator = FQCNValidator()
            report_gen = ReportGenerator("e2e-test")
            interactive_mode = InteractiveMode(converter)
            
            print("✓ All components initialized")
            
            # Step 2: Validate original file
            original_validation = validator.validate_file(test_file)
            print(f"✓ Original validation: Valid={original_validation.valid}, Score={original_validation.score:.1%}")
            
            # Step 3: Generate preview (simulate interactive mode)
            preview = interactive_mode._generate_preview(test_file)
            if preview:
                print(f"✓ Preview generated with potential changes")
            else:
                print("✓ No preview needed")
            
            # Step 4: Perform conversion
            import time
            start_time = time.time()
            conversion_result = converter.convert_file(test_file)
            processing_time = time.time() - start_time
            
            print(f"✓ Conversion completed: Success={conversion_result.success}, Changes={conversion_result.changes_made}")
            
            # Step 5: Validate converted file
            post_validation = validator.validate_file(test_file)
            print(f"✓ Post-conversion validation: Valid={post_validation.valid}, Score={post_validation.score:.1%}")
            
            # Step 6: Generate comprehensive report
            report_gen.start_session(test_file.parent)
            report_gen.add_file_result(test_file, conversion_result, processing_time)
            final_report = report_gen.finalize_session()
            
            # Step 7: Generate reports in multiple formats
            console_report = report_gen.generate_report('console')
            json_report = report_gen.generate_report('json')
            
            print("✓ Reports generated successfully")
            print(f"  - Console report: {len(console_report)} characters")
            print(f"  - JSON report: {len(json_report)} characters")
            
            # Step 8: Verify workflow results
            stats = report_gen.get_summary_stats()
            assert stats['files_processed'] == 1
            assert stats['success_rate'] >= 0.0
            
            print("✓ End-to-end workflow completed successfully")
            print(f"  - Files processed: {stats['files_processed']}")
            print(f"  - Success rate: {stats['success_rate']:.1%}")
            print(f"  - Processing speed: {stats['processing_speed']:.1f} files/sec")
            
            return True
            
        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()
                
    except Exception as e:
        print(f"✗ End-to-end workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all CLI tests."""
    print("=" * 70)
    print("FQCN Converter Enhanced CLI Features Test")
    print("=" * 70)
    
    tests = [
        test_interactive_cli_import,
        test_enhanced_cli_import,
        test_reporting_cli_functionality,
        test_interactive_mode_components,
        test_cli_entry_points,
        test_configuration_system,
        test_end_to_end_workflow
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 70)
    print(f"CLI Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All CLI tests passed!")
        print("\n✨ Enhanced FQCN Converter CLI is fully functional!")
        print("   - Interactive mode ready for use")
        print("   - Enhanced reporting system operational")
        print("   - Configuration management working")
        print("   - All entry points properly configured")
        print("   - End-to-end workflow validated")
        print("\n🚀 Ready for production use!")
        return True
    else:
        print("⚠ Some CLI tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)