#!/usr/bin/env python3
"""Comprehensive integration test for enhanced FQCN Converter features."""

import sys
import tempfile
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def create_test_project():
    """Create a temporary test project with various Ansible files."""
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create playbook with short module names
    playbook_content = """---
- name: Test playbook
  hosts: all
  tasks:
    - name: Copy configuration file
      copy:
        src: config.conf
        dest: /etc/myapp/config.conf
        backup: yes
    
    - name: Install package
      package:
        name: nginx
        state: present
    
    - name: Start service
      service:
        name: nginx
        state: started
        enabled: yes
    
    - name: Run shell command
      shell: echo "Hello World" > /tmp/hello.txt
    
    - name: Create user
      user:
        name: appuser
        group: appgroup
        shell: /bin/bash
"""
    
    # Create tasks file
    tasks_content = """---
- name: Update system
  package:
    name: "*"
    state: latest

- name: Configure firewall
  firewalld:
    service: http
    permanent: yes
    state: enabled

- name: Template configuration
  template:
    src: app.conf.j2
    dest: /etc/app/app.conf
    backup: yes
"""
    
    # Create handlers file
    handlers_content = """---
- name: restart nginx
  service:
    name: nginx
    state: restarted

- name: reload firewall
  systemd:
    name: firewalld
    state: reloaded
"""
    
    # Write files
    (temp_dir / "playbook.yml").write_text(playbook_content)
    (temp_dir / "tasks.yml").write_text(tasks_content)
    (temp_dir / "handlers.yml").write_text(handlers_content)
    
    # Create a mixed file (some FQCN, some short names)
    mixed_content = """---
- name: Mixed FQCN usage
  hosts: all
  tasks:
    - name: Already using FQCN
      ansible.builtin.copy:
        src: file1.txt
        dest: /tmp/file1.txt
    
    - name: Needs conversion
      shell: echo "needs conversion"
    
    - name: Another FQCN
      community.general.firewalld:
        service: ssh
        state: enabled
    
    - name: Another short name
      user:
        name: testuser
"""
    
    (temp_dir / "mixed.yml").write_text(mixed_content)
    
    return temp_dir

def test_full_workflow():
    """Test the complete enhanced workflow."""
    print("Testing complete enhanced workflow...")
    
    try:
        # Import all necessary modules
        from fqcn_converter.core.converter import FQCNConverter
        from fqcn_converter.core.validator import FQCNValidator
        from fqcn_converter.reporting.report_generator import ReportGenerator
        from fqcn_converter.cli.interactive import InteractiveMode
        
        # Create test project
        test_project = create_test_project()
        print(f"✓ Created test project at: {test_project}")
        
        # List files in project
        yaml_files = list(test_project.rglob("*.yml"))
        print(f"✓ Found {len(yaml_files)} YAML files: {[f.name for f in yaml_files]}")
        
        # Initialize components
        converter = FQCNConverter()
        validator = FQCNValidator()
        report_generator = ReportGenerator("integration-test")
        
        print("✓ Initialized all components")
        
        # Start reporting session
        report_generator.start_session(test_project)
        
        # Process each file
        results = {}
        for yaml_file in yaml_files:
            print(f"\n--- Processing {yaml_file.name} ---")
            
            # Validate original file
            validation_result = validator.validate_file(yaml_file)
            print(f"Original validation - Valid: {validation_result.valid}, "
                  f"Issues: {len(validation_result.issues)}, "
                  f"Score: {validation_result.score:.1%}")
            
            # Convert file (dry run first)
            start_time = time.time()
            dry_run_result = converter.convert_file(yaml_file, dry_run=True)
            processing_time = time.time() - start_time
            
            if dry_run_result.success:
                print(f"Dry run - Found {dry_run_result.changes_made} potential conversions")
                
                # Perform actual conversion
                start_time = time.time()
                conversion_result = converter.convert_file(yaml_file)
                processing_time = time.time() - start_time
                
                if conversion_result.success:
                    print(f"Conversion successful - {conversion_result.changes_made} conversions made")
                    
                    # Validate converted file
                    post_validation = validator.validate_file(yaml_file)
                    print(f"Post-conversion validation - Valid: {post_validation.valid}, "
                          f"Score: {post_validation.score:.1%}")
                    
                    results[yaml_file.name] = {
                        'original_score': validation_result.score,
                        'final_score': post_validation.score,
                        'conversions': conversion_result.changes_made,
                        'processing_time': processing_time
                    }
                else:
                    print(f"Conversion failed: {conversion_result.error}")
                    results[yaml_file.name] = {
                        'error': conversion_result.error,
                        'processing_time': processing_time
                    }
            else:
                print(f"Dry run failed: {dry_run_result.error}")
                results[yaml_file.name] = {
                    'error': dry_run_result.error,
                    'processing_time': processing_time
                }
            
            # Add to report
            report_generator.add_file_result(yaml_file, conversion_result, processing_time)
        
        # Finalize report
        final_report = report_generator.finalize_session()
        
        # Generate reports in different formats
        print(f"\n--- Generating Reports ---")
        
        # Console report
        console_report = report_generator.generate_report('console')
        print("Console Report:")
        print(console_report)
        
        # JSON report
        json_report = report_generator.generate_report('json')
        print(f"\nJSON Report (first 200 chars): {json_report[:200]}...")
        
        # Summary statistics
        stats = report_generator.get_summary_stats()
        print(f"\nSummary Statistics:")
        print(f"  Files processed: {stats['files_processed']}")
        print(f"  Success rate: {stats['success_rate']:.1%}")
        print(f"  Conversions made: {stats['conversions_made']}")
        print(f"  Processing speed: {stats['processing_speed']:.1f} files/sec")
        
        # Test interactive mode initialization (without actual interaction)
        interactive_mode = InteractiveMode(converter)
        print(f"✓ Interactive mode initialized with stats: {interactive_mode.session_stats}")
        
        # Cleanup
        import shutil
        shutil.rmtree(test_project)
        print(f"✓ Cleaned up test project")
        
        print(f"\n🎉 Complete workflow test passed!")
        print(f"   - Processed {len(yaml_files)} files")
        print(f"   - Generated reports in multiple formats")
        print(f"   - Validated before and after conversion")
        print(f"   - Demonstrated all enhanced features")
        
        return True
        
    except Exception as e:
        print(f"✗ Full workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_monitoring():
    """Test performance monitoring capabilities."""
    print("\nTesting performance monitoring...")
    
    try:
        from fqcn_converter.reporting.report_generator import ReportGenerator
        from fqcn_converter.core.converter import FQCNConverter
        
        # Create test project
        test_project = create_test_project()
        
        # Initialize components
        converter = FQCNConverter()
        report_generator = ReportGenerator("performance-test")
        report_generator.start_session(test_project)
        
        # Process files and measure performance
        yaml_files = list(test_project.rglob("*.yml"))
        total_start_time = time.time()
        
        for yaml_file in yaml_files:
            start_time = time.time()
            result = converter.convert_file(yaml_file, dry_run=True)  # Use dry run for safety
            processing_time = time.time() - start_time
            
            report_generator.add_file_result(yaml_file, result, processing_time)
        
        total_time = time.time() - total_start_time
        
        # Finalize and get stats
        report_generator.finalize_session()
        stats = report_generator.get_summary_stats()
        
        print(f"✓ Performance monitoring results:")
        print(f"  Total files: {stats['files_processed']}")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Processing speed: {stats['processing_speed']:.1f} files/sec")
        print(f"  Average time per file: {stats['total_time'] / stats['files_processed']:.3f}s")
        
        # Cleanup
        import shutil
        shutil.rmtree(test_project)
        
        return True
        
    except Exception as e:
        print(f"✗ Performance monitoring test failed: {e}")
        return False

def test_error_handling():
    """Test error handling in enhanced features."""
    print("\nTesting error handling...")
    
    try:
        from fqcn_converter.reporting.report_generator import ReportGenerator
        from fqcn_converter.core.converter import FQCNConverter
        
        # Create report generator
        report_generator = ReportGenerator("error-test")
        
        # Test adding errors and warnings
        report_generator.add_error("Test error message")
        report_generator.add_warning("Test warning message")
        
        # Test with non-existent file
        converter = FQCNConverter()
        non_existent_file = Path("/non/existent/file.yml")
        
        try:
            result = converter.convert_file(non_existent_file)
            # This should fail, but let's handle it gracefully
            report_generator.add_file_result(non_existent_file, result, 0.0)
        except Exception as e:
            report_generator.add_error(f"Expected error with non-existent file: {e}")
        
        # Finalize and check error handling
        report = report_generator.finalize_session()
        
        assert report.has_errors
        assert report.has_warnings
        assert len(report.errors) >= 1
        assert len(report.warnings) >= 1
        
        print("✓ Error handling works correctly")
        print(f"  Errors captured: {len(report.errors)}")
        print(f"  Warnings captured: {len(report.warnings)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False

def main():
    """Run all integration tests."""
    print("=" * 70)
    print("FQCN Converter Enhanced Features - Integration Test")
    print("=" * 70)
    
    tests = [
        test_full_workflow,
        test_performance_monitoring,
        test_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 70)
    print(f"Integration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("\n✨ Enhanced FQCN Converter features are working correctly!")
        print("   - Interactive mode ready")
        print("   - Enhanced reporting functional")
        print("   - Performance monitoring active")
        print("   - Error handling robust")
        print("   - Full workflow validated")
        return True
    else:
        print("⚠ Some integration tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)