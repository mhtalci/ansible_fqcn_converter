#!/usr/bin/env python3
"""
Basic Usage Examples for FQCN Converter

This script demonstrates basic usage patterns for the FQCN Converter
Python API with practical examples and error handling.

Run this script to see the converter in action:
    python examples/basic_usage.py
"""

import tempfile
import os
from pathlib import Path
from fqcn_converter import (
    FQCNConverter, 
    ValidationEngine, 
    BatchProcessor,
    ConversionError,
    ValidationError
)


def example_1_basic_conversion():
    """Example 1: Basic file conversion with error handling."""
    print("=" * 60)
    print("Example 1: Basic File Conversion")
    print("=" * 60)
    
    # Create a sample Ansible playbook
    sample_playbook = """---
- name: Sample playbook
  hosts: webservers
  tasks:
    - name: Install nginx
      package:
        name: nginx
        state: present
    
    - name: Copy configuration
      copy:
        src: nginx.conf
        dest: /etc/nginx/nginx.conf
        backup: yes
    
    - name: Start nginx service
      service:
        name: nginx
        state: started
        enabled: yes
"""
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write(sample_playbook)
        temp_file = f.name
    
    try:
        # Initialize converter
        converter = FQCNConverter()
        
        print(f"📁 Created sample file: {temp_file}")
        print("\n📋 Original content:")
        print(sample_playbook)
        
        # Perform dry run first (recommended)
        print("\n🔍 Performing dry run...")
        dry_result = converter.convert_file(temp_file, dry_run=True)
        
        if dry_result.success:
            print(f"✅ Dry run successful!")
            print(f"   Would convert {dry_result.changes_made} modules")
        else:
            print(f"❌ Dry run failed: {dry_result.errors}")
            return
        
        # Perform actual conversion
        print("\n🔄 Performing actual conversion...")
        result = converter.convert_file(temp_file)
        
        if result.success:
            print(f"✅ Conversion successful!")
            print(f"   Converted {result.changes_made} modules")
            print(f"   Processing time: {result.processing_time:.3f}s")
            
            # Show converted content
            print("\n📋 Converted content:")
            with open(temp_file, 'r') as f:
                print(f.read())
        else:
            print(f"❌ Conversion failed:")
            for error in result.errors:
                print(f"   - {error}")
    
    except ConversionError as e:
        print(f"❌ Conversion error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.unlink(temp_file)
        backup_file = temp_file + ".fqcn_backup"
        if os.path.exists(backup_file):
            os.unlink(backup_file)


def example_2_content_conversion():
    """Example 2: Converting content directly without files."""
    print("\n" + "=" * 60)
    print("Example 2: Direct Content Conversion")
    print("=" * 60)
    
    # Sample YAML content with short module names
    yaml_content = """
- name: Database setup tasks
  block:
    - name: Create database user
      user:
        name: dbuser
        password: secret
        groups: database
    
    - name: Install MySQL
      package:
        name: mysql-server
        state: present
    
    - name: Start MySQL service
      service:
        name: mysql
        state: started
"""
    
    try:
        converter = FQCNConverter()
        
        print("📋 Original content:")
        print(yaml_content)
        
        # Convert content directly
        print("\n🔄 Converting content...")
        result = converter.convert_content(yaml_content)
        
        if result.success:
            print(f"✅ Content conversion successful!")
            print(f"   Converted {result.changes_made} modules")
            
            print("\n📋 Converted content:")
            print(result.converted_content)
        else:
            print(f"❌ Content conversion failed:")
            for error in result.errors:
                print(f"   - {error}")
    
    except Exception as e:
        print(f"❌ Error: {e}")


def example_3_custom_mappings():
    """Example 3: Using custom module mappings."""
    print("\n" + "=" * 60)
    print("Example 3: Custom Module Mappings")
    print("=" * 60)
    
    # Define custom mappings for specialized modules
    custom_mappings = {
        "docker_container": "community.docker.docker_container",
        "mysql_user": "community.mysql.mysql_user",
        "postgresql_db": "community.postgresql.postgresql_db",
        "custom_module": "my.collection.custom_module"
    }
    
    yaml_content = """
- name: Container and database setup
  tasks:
    - name: Start web container
      docker_container:
        name: webapp
        image: nginx:latest
        state: started
    
    - name: Create MySQL user
      mysql_user:
        name: webapp
        password: secret
        priv: "webapp.*:ALL"
    
    - name: Create PostgreSQL database
      postgresql_db:
        name: webapp
        state: present
    
    - name: Run custom module
      custom_module:
        param1: value1
        param2: value2
"""
    
    try:
        # Initialize converter with custom mappings
        converter = FQCNConverter(custom_mappings=custom_mappings)
        
        print("🔧 Using custom mappings:")
        for short_name, fqcn in custom_mappings.items():
            print(f"   {short_name} → {fqcn}")
        
        print("\n📋 Original content:")
        print(yaml_content)
        
        # Convert with custom mappings
        result = converter.convert_content(yaml_content)
        
        if result.success:
            print(f"\n✅ Conversion with custom mappings successful!")
            print(f"   Converted {result.changes_made} modules")
            
            print("\n📋 Converted content:")
            print(result.converted_content)
        else:
            print(f"❌ Conversion failed:")
            for error in result.errors:
                print(f"   - {error}")
    
    except Exception as e:
        print(f"❌ Error: {e}")


def example_4_validation():
    """Example 4: Validating FQCN usage."""
    print("\n" + "=" * 60)
    print("Example 4: FQCN Validation")
    print("=" * 60)
    
    # Sample content with mixed FQCN usage
    mixed_content = """
- name: Mixed FQCN usage example
  tasks:
    - name: Good - using FQCN
      ansible.builtin.copy:
        src: file.txt
        dest: /tmp/file.txt
    
    - name: Bad - using short name
      package:
        name: nginx
        state: present
    
    - name: Good - using FQCN
      ansible.builtin.service:
        name: nginx
        state: started
    
    - name: Bad - using short name
      user:
        name: nginx
        system: yes
"""
    
    try:
        validator = ValidationEngine()
        
        print("📋 Content to validate:")
        print(mixed_content)
        
        # Validate content
        print("\n🔍 Validating FQCN usage...")
        result = validator.validate_content(mixed_content)
        
        print(f"\n📊 Validation Results:")
        print(f"   Valid: {result.valid}")
        print(f"   Compliance Score: {result.score:.1%}")
        print(f"   Total Modules: {result.total_modules}")
        print(f"   FQCN Modules: {result.fqcn_modules}")
        print(f"   Short Modules: {result.short_modules}")
        
        if result.issues:
            print(f"\n⚠️  Found {len(result.issues)} issues:")
            for issue in result.issues:
                severity_icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}
                icon = severity_icon.get(issue.severity, "•")
                print(f"   {icon} Line {issue.line_number}: {issue.message}")
                if issue.suggestion:
                    print(f"      💡 Suggestion: {issue.suggestion}")
        else:
            print("\n✅ No validation issues found!")
    
    except ValidationError as e:
        print(f"❌ Validation error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_5_error_handling():
    """Example 5: Comprehensive error handling."""
    print("\n" + "=" * 60)
    print("Example 5: Error Handling")
    print("=" * 60)
    
    # Invalid YAML content to demonstrate error handling
    invalid_yaml = """
- name: Invalid YAML example
  tasks:
    - name: Missing colon after package
      package
        name: nginx
        state: present
    
    - name: Incorrect indentation
  copy:
    src: file.txt
    dest: /tmp/file.txt
"""
    
    try:
        converter = FQCNConverter()
        
        print("📋 Invalid YAML content:")
        print(invalid_yaml)
        
        print("\n🔄 Attempting conversion...")
        result = converter.convert_content(invalid_yaml)
        
        if result.success:
            print("✅ Conversion successful (unexpected!)")
        else:
            print("❌ Conversion failed as expected:")
            for error in result.errors:
                print(f"   - {error}")
            
            if result.warnings:
                print("\n⚠️  Warnings:")
                for warning in result.warnings:
                    print(f"   - {warning}")
    
    except Exception as e:
        print(f"❌ Exception caught: {type(e).__name__}: {e}")
        
        # Demonstrate error recovery
        if hasattr(e, 'get_recovery_suggestions'):
            suggestions = e.get_recovery_suggestions()
            if suggestions:
                print("\n💡 Recovery suggestions:")
                for suggestion in suggestions:
                    print(f"   - {suggestion}")


def example_6_batch_processing():
    """Example 6: Batch processing simulation."""
    print("\n" + "=" * 60)
    print("Example 6: Batch Processing Simulation")
    print("=" * 60)
    
    # Create multiple temporary files to simulate batch processing
    sample_files = {
        "playbook1.yml": """
- name: Web server setup
  tasks:
    - package: {name: nginx, state: present}
    - service: {name: nginx, state: started}
""",
        "playbook2.yml": """
- name: Database setup
  tasks:
    - user: {name: postgres, system: yes}
    - package: {name: postgresql, state: present}
""",
        "tasks.yml": """
- copy: {src: config.conf, dest: /etc/app/config.conf}
- template: {src: service.j2, dest: /etc/systemd/system/app.service}
- systemd: {name: app, state: started, enabled: yes}
"""
    }
    
    temp_files = []
    
    try:
        # Create temporary files
        temp_dir = tempfile.mkdtemp()
        print(f"📁 Created temporary directory: {temp_dir}")
        
        for filename, content in sample_files.items():
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write(content)
            temp_files.append(file_path)
            print(f"   Created: {filename}")
        
        # Simulate batch processing
        converter = FQCNConverter()
        total_changes = 0
        successful_files = 0
        
        print(f"\n🔄 Processing {len(temp_files)} files...")
        
        for file_path in temp_files:
            filename = os.path.basename(file_path)
            try:
                result = converter.convert_file(file_path)
                if result.success:
                    print(f"   ✅ {filename}: {result.changes_made} changes")
                    total_changes += result.changes_made
                    successful_files += 1
                else:
                    print(f"   ❌ {filename}: {result.errors}")
            except Exception as e:
                print(f"   ❌ {filename}: {e}")
        
        print(f"\n📊 Batch Processing Summary:")
        print(f"   Files processed: {len(temp_files)}")
        print(f"   Successful: {successful_files}")
        print(f"   Total changes: {total_changes}")
        print(f"   Success rate: {successful_files/len(temp_files):.1%}")
    
    except Exception as e:
        print(f"❌ Batch processing error: {e}")
    
    finally:
        # Clean up temporary files
        for file_path in temp_files:
            if os.path.exists(file_path):
                os.unlink(file_path)
            backup_path = file_path + ".fqcn_backup"
            if os.path.exists(backup_path):
                os.unlink(backup_path)
        
        if temp_files and os.path.exists(temp_dir):
            os.rmdir(temp_dir)


def main():
    """Run all examples."""
    print("🚀 FQCN Converter - Basic Usage Examples")
    print("=" * 60)
    print("This script demonstrates basic usage patterns for the FQCN Converter.")
    print("Each example shows different aspects of the converter functionality.")
    
    try:
        example_1_basic_conversion()
        example_2_content_conversion()
        example_3_custom_mappings()
        example_4_validation()
        example_5_error_handling()
        example_6_batch_processing()
        
        print("\n" + "=" * 60)
        print("🎉 All examples completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("- Check the API documentation: docs/reference/api.md")
        print("- See advanced examples: docs/examples/")
        print("- Read the CLI guide: docs/usage/cli.md")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Examples interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error running examples: {e}")


if __name__ == "__main__":
    main()