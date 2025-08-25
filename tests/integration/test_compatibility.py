"""
Compatibility tests for FQCN Converter.

These tests validate compatibility across different Python versions,
Ansible versions, and operating system environments.
"""

import pytest
import sys
import platform
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

from fqcn_converter.core.converter import FQCNConverter
from fqcn_converter.core.validator import ValidationEngine


class TestPythonVersionCompatibility:
    """Test compatibility across Python versions."""
    
    def test_python_version_support(self):
        """Test that we're running on a supported Python version."""
        version_info = sys.version_info
        
        # Should support Python 3.8+
        assert version_info.major == 3
        assert version_info.minor >= 8
        
        print(f"Running on Python {version_info.major}.{version_info.minor}.{version_info.micro}")
    
    def test_pathlib_compatibility(self, temp_dir):
        """Test pathlib compatibility across Python versions."""
        converter = FQCNConverter()
        
        # Create test file using pathlib
        test_file = temp_dir / "pathlib_test.yml"
        test_file.write_text("""---
- name: Pathlib compatibility test
  hosts: all
  tasks:
    - name: Install package
      package:
        name: nginx
        state: present
""")
        
        # Test with Path object
        result = converter.convert_file(test_file, dry_run=True)
        assert result.success is True
        
        # Test with string path
        result = converter.convert_file(str(test_file), dry_run=True)
        assert result.success is True
    
    def test_typing_compatibility(self):
        """Test typing annotations compatibility."""
        # Import modules to ensure typing works
        from fqcn_converter.core.converter import ConversionResult
        from fqcn_converter.core.validator import ValidationResult, ValidationIssue
        from fqcn_converter.config.manager import ConversionSettings
        
        # Create instances to test dataclass compatibility
        conversion_result = ConversionResult(
            success=True,
            file_path="/test/path",
            changes_made=1
        )
        assert conversion_result.success is True
        
        validation_result = ValidationResult(
            valid=True,
            file_path="/test/path"
        )
        assert validation_result.valid is True
        
        settings = ConversionSettings()
        assert settings.backup_files is True


class TestOperatingSystemCompatibility:
    """Test compatibility across different operating systems."""
    
    def test_os_detection(self):
        """Test OS detection and compatibility."""
        os_name = platform.system()
        print(f"Running on {os_name}")
        
        # Should work on major operating systems
        supported_os = ['Linux', 'Darwin', 'Windows']
        assert os_name in supported_os
    
    def test_file_path_handling(self, temp_dir):
        """Test file path handling across operating systems."""
        converter = FQCNConverter()
        
        # Create test file with OS-appropriate path
        test_file = temp_dir / "os_test.yml"
        test_file.write_text("""---
- name: OS compatibility test
  hosts: all
  tasks:
    - name: Create directory
      file:
        path: /tmp/test
        state: directory
""")
        
        result = converter.convert_file(test_file, dry_run=True)
        assert result.success is True
        assert 'ansible.builtin.file:' in result.converted_content
    
    def test_line_ending_compatibility(self, temp_dir):
        """Test handling of different line endings."""
        converter = FQCNConverter()
        
        # Test with Unix line endings (LF)
        unix_file = temp_dir / "unix_endings.yml"
        unix_content = "---\n- name: Unix test\n  hosts: all\n  tasks:\n    - name: Test\n      copy:\n        src: test\n        dest: /tmp/test\n"
        unix_file.write_text(unix_content)
        
        result = converter.convert_file(unix_file, dry_run=True)
        assert result.success is True
        
        # Test with Windows line endings (CRLF)
        windows_file = temp_dir / "windows_endings.yml"
        windows_content = unix_content.replace('\n', '\r\n')
        windows_file.write_bytes(windows_content.encode('utf-8'))
        
        result = converter.convert_file(windows_file, dry_run=True)
        assert result.success is True
    
    def test_file_permissions_handling(self, temp_dir):
        """Test file permission handling across OS."""
        converter = FQCNConverter()
        
        test_file = temp_dir / "permissions_test.yml"
        test_file.write_text("""---
- name: Permissions test
  hosts: all
  tasks:
    - name: Install package
      package:
        name: nginx
        state: present
""")
        
        # Test reading and writing with different permissions
        if platform.system() != 'Windows':
            # Set read-only permissions
            test_file.chmod(0o444)
            
            # Should still be able to read
            result = converter.convert_file(test_file, dry_run=True)
            assert result.success is True
            
            # Restore write permissions for cleanup
            test_file.chmod(0o644)


class TestAnsibleVersionCompatibility:
    """Test compatibility with different Ansible versions and formats."""
    
    def test_ansible_2_9_format(self, temp_dir):
        """Test compatibility with Ansible 2.9 playbook format."""
        converter = FQCNConverter()
        
        # Ansible 2.9 style playbook
        ansible_29_file = temp_dir / "ansible_29.yml"
        ansible_29_file.write_text("""---
- hosts: all
  become: true
  gather_facts: yes
  
  vars:
    packages:
      - nginx
      - php7.4-fpm
  
  tasks:
    - name: Update apt cache
      apt:
        update_cache: yes
      when: ansible_os_family == "Debian"
    
    - name: Install packages
      package:
        name: "{{ item }}"
        state: present
      with_items: "{{ packages }}"
    
    - name: Start services
      service:
        name: "{{ item }}"
        state: started
        enabled: yes
      with_items:
        - nginx
        - php7.4-fpm
""")
        
        result = converter.convert_file(ansible_29_file, dry_run=False)
        assert result.success is True
        
        converted_content = ansible_29_file.read_text()
        assert 'ansible.builtin.apt:' in converted_content
        assert 'ansible.builtin.package:' in converted_content
        assert 'ansible.builtin.service:' in converted_content
    
    def test_ansible_core_format(self, temp_dir):
        """Test compatibility with ansible-core format."""
        converter = FQCNConverter()
        
        # Modern ansible-core style playbook
        ansible_core_file = temp_dir / "ansible_core.yml"
        ansible_core_file.write_text("""---
- name: Modern Ansible playbook
  hosts: all
  become: true
  gather_facts: true
  
  vars:
    app_name: myapp
    app_version: "1.0.0"
  
  tasks:
    - name: Install packages
      package:
        name: "{{ item }}"
        state: present
      loop:
        - nginx
        - python3
        - python3-pip
    
    - name: Create application user
      user:
        name: "{{ app_name }}"
        system: yes
        shell: /bin/false
        home: "/opt/{{ app_name }}"
        create_home: yes
    
    - name: Template configuration
      template:
        src: "{{ app_name }}.conf.j2"
        dest: "/etc/{{ app_name }}/{{ app_name }}.conf"
        owner: "{{ app_name }}"
        group: "{{ app_name }}"
        mode: '0640'
      notify: restart application
  
  handlers:
    - name: restart application
      systemd:
        name: "{{ app_name }}"
        state: restarted
        daemon_reload: yes
""")
        
        result = converter.convert_file(ansible_core_file, dry_run=False)
        assert result.success is True
        
        converted_content = ansible_core_file.read_text()
        assert 'ansible.builtin.package:' in converted_content
        assert 'ansible.builtin.user:' in converted_content
        assert 'ansible.builtin.template:' in converted_content
        assert 'ansible.builtin.systemd:' in converted_content
    
    def test_collection_format_compatibility(self, temp_dir):
        """Test compatibility with collection-based playbooks."""
        converter = FQCNConverter()
        
        # Playbook already using some collections
        collection_file = temp_dir / "collections.yml"
        collection_file.write_text("""---
- name: Mixed collection usage
  hosts: all
  
  tasks:
    # Already using FQCN
    - name: Copy file with FQCN
      ansible.builtin.copy:
        src: test.txt
        dest: /tmp/test.txt
    
    # Short name that needs conversion
    - name: Install package with short name
      package:
        name: nginx
        state: present
    
    # Community collection (already FQCN)
    - name: Docker container
      community.docker.docker_container:
        name: nginx
        image: nginx:latest
        state: started
    
    # Short name that needs conversion
    - name: Start service
      service:
        name: nginx
        state: started
""")
        
        result = converter.convert_file(collection_file, dry_run=False)
        assert result.success is True
        
        converted_content = collection_file.read_text()
        
        # Already FQCN modules should remain unchanged
        assert 'ansible.builtin.copy:' in converted_content
        assert 'community.docker.docker_container:' in converted_content
        
        # Short names should be converted
        assert 'ansible.builtin.package:' in converted_content
        assert 'ansible.builtin.service:' in converted_content
    
    def test_legacy_syntax_compatibility(self, temp_dir):
        """Test compatibility with legacy Ansible syntax."""
        converter = FQCNConverter()
        
        # Legacy syntax playbook
        legacy_file = temp_dir / "legacy.yml"
        legacy_file.write_text("""---
- hosts: webservers
  sudo: yes
  
  vars:
    http_port: 80
    max_clients: 200
  
  tasks:
    - name: ensure apache is at the latest version
      yum: name=httpd state=latest
    
    - name: write the apache config file
      template: src=/srv/httpd.j2 dest=/etc/httpd.conf
      notify:
        - restart apache
    
    - name: ensure apache is running
      service: name=httpd state=started
  
  handlers:
    - name: restart apache
      service: name=httpd state=restarted
""")
        
        result = converter.convert_file(legacy_file, dry_run=False)
        assert result.success is True
        
        converted_content = legacy_file.read_text()
        assert 'ansible.builtin.yum:' in converted_content
        assert 'ansible.builtin.template:' in converted_content
        assert 'ansible.builtin.service:' in converted_content


class TestYAMLFormatCompatibility:
    """Test compatibility with different YAML formats and styles."""
    
    def test_yaml_flow_style(self, temp_dir):
        """Test handling of YAML flow style."""
        converter = FQCNConverter()
        
        flow_style_file = temp_dir / "flow_style.yml"
        flow_style_file.write_text("""---
- name: Flow style test
  hosts: all
  tasks:
    - {name: Install nginx, package: {name: nginx, state: present}}
    - {name: Start nginx, service: {name: nginx, state: started}}
""")
        
        result = converter.convert_file(flow_style_file, dry_run=True)
        assert result.success is True
        # Note: The exact format of converted flow style may vary
        # The important thing is that conversion succeeds
    
    def test_yaml_multiline_strings(self, temp_dir):
        """Test handling of YAML multiline strings."""
        converter = FQCNConverter()
        
        multiline_file = temp_dir / "multiline.yml"
        multiline_file.write_text("""---
- name: Multiline string test
  hosts: all
  tasks:
    - name: Create script with multiline content
      copy:
        content: |
          #!/bin/bash
          echo "This is a multiline script"
          echo "With multiple lines"
          exit 0
        dest: /tmp/script.sh
        mode: '0755'
    
    - name: Run command with folded string
      command: >
        echo "This is a very long command line
        that spans multiple lines in YAML
        but should be on one line when executed"
""")
        
        result = converter.convert_file(multiline_file, dry_run=False)
        assert result.success is True
        
        converted_content = multiline_file.read_text()
        assert 'ansible.builtin.copy:' in converted_content
        assert 'ansible.builtin.command:' in converted_content
        
        # Multiline strings should be preserved
        assert '#!/bin/bash' in converted_content
        assert 'echo "This is a very long command line' in converted_content
    
    def test_yaml_anchors_and_aliases(self, temp_dir):
        """Test handling of YAML anchors and aliases."""
        converter = FQCNConverter()
        
        anchors_file = temp_dir / "anchors.yml"
        anchors_file.write_text("""---
- name: YAML anchors test
  hosts: all
  
  vars:
    common_package_params: &common_params
      state: present
      update_cache: yes
  
  tasks:
    - name: Install nginx
      package:
        name: nginx
        <<: *common_params
    
    - name: Install apache
      package:
        name: apache2
        <<: *common_params
""")
        
        result = converter.convert_file(anchors_file, dry_run=False)
        assert result.success is True
        
        converted_content = anchors_file.read_text()
        assert 'ansible.builtin.package:' in converted_content
        
        # Anchors and aliases should be preserved
        assert '&common_params' in converted_content
        assert '*common_params' in converted_content
    
    def test_yaml_comments_preservation(self, temp_dir):
        """Test that YAML comments are preserved during conversion."""
        converter = FQCNConverter()
        
        comments_file = temp_dir / "comments.yml"
        comments_file.write_text("""---
# Main playbook for web server setup
- name: Web server configuration
  hosts: webservers  # Target web server hosts
  become: yes        # Run with sudo privileges
  
  tasks:
    # Install web server package
    - name: Install nginx
      package:  # Use package module for cross-platform compatibility
        name: nginx
        state: present
    
    # Start and enable the service
    - name: Start nginx service
      service:  # Manage system services
        name: nginx
        state: started
        enabled: yes  # Enable on boot
""")
        
        result = converter.convert_file(comments_file, dry_run=False)
        assert result.success is True
        
        converted_content = comments_file.read_text()
        
        # Modules should be converted
        assert 'ansible.builtin.package:' in converted_content
        assert 'ansible.builtin.service:' in converted_content
        
        # Comments should be preserved
        assert '# Main playbook for web server setup' in converted_content
        assert '# Target web server hosts' in converted_content
        assert '# Install web server package' in converted_content
        assert '# Use package module for cross-platform compatibility' in converted_content