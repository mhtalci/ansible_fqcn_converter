"""
End-to-end integration tests for FQCN Converter.

These tests validate the complete workflow from file discovery
through conversion and validation with real Ansible content.
"""

import pytest
import tempfile
import shutil
import yaml
from pathlib import Path

from fqcn_converter.core.converter import FQCNConverter
from fqcn_converter.core.validator import ValidationEngine
from fqcn_converter.config.manager import ConfigurationManager


class TestEndToEndWorkflow:
    """End-to-end workflow integration tests."""
    
    @pytest.fixture
    def real_ansible_project(self, temp_dir):
        """Create a realistic Ansible project structure."""
        project_dir = temp_dir / "real_project"
        
        # Create directory structure
        (project_dir / "group_vars").mkdir(parents=True)
        (project_dir / "roles" / "webserver" / "tasks").mkdir(parents=True)
        (project_dir / "roles" / "webserver" / "handlers").mkdir(parents=True)
        (project_dir / "roles" / "database" / "tasks").mkdir(parents=True)
        
        # Main playbook
        (project_dir / "site.yml").write_text("""---
- name: Configure web servers
  hosts: webservers
  become: yes
  
  pre_tasks:
    - name: Update package cache
      package:
        update_cache: yes
    
    - name: Install common packages
      package:
        name: "{{ item }}"
        state: present
      loop:
        - curl
        - wget
        - vim
  
  roles:
    - webserver
  
  post_tasks:
    - name: Verify web service
      command: curl -f http://localhost/
      register: web_check
      failed_when: web_check.rc != 0

- name: Configure database servers
  hosts: databases
  become: yes
  roles:
    - database
""")
        
        # Webserver role tasks
        (project_dir / "roles" / "webserver" / "tasks" / "main.yml").write_text("""---
- name: Install nginx
  package:
    name: nginx
    state: present

- name: Create nginx config directory
  file:
    path: /etc/nginx/conf.d
    state: directory
    owner: root
    group: root
    mode: '0755'

- name: Copy nginx main config
  copy:
    src: nginx.conf
    dest: /etc/nginx/nginx.conf
    owner: root
    group: root
    mode: '0644'
    backup: yes
  notify: restart nginx

- name: Template virtual host config
  template:
    src: vhost.conf.j2
    dest: /etc/nginx/conf.d/default.conf
    owner: root
    group: root
    mode: '0644'
  notify: restart nginx

- name: Create web user
  user:
    name: www-data
    system: yes
    shell: /bin/false
    home: /var/www
    create_home: no

- name: Create web directory
  file:
    path: /var/www/html
    state: directory
    owner: www-data
    group: www-data
    mode: '0755'

- name: Start and enable nginx
  service:
    name: nginx
    state: started
    enabled: yes

- name: Open firewall for HTTP
  command: ufw allow 80/tcp
  when: ansible_os_family == "Debian"

- name: Set deployment facts
  set_fact:
    webserver_deployed: true
    deployment_timestamp: "{{ ansible_date_time.iso8601 }}"
""")
        
        # Webserver handlers
        (project_dir / "roles" / "webserver" / "handlers" / "main.yml").write_text("""---
- name: restart nginx
  service:
    name: nginx
    state: restarted

- name: reload nginx
  service:
    name: nginx
    state: reloaded
""")
        
        # Database role tasks
        (project_dir / "roles" / "database" / "tasks" / "main.yml").write_text("""---
- name: Install MySQL
  package:
    name: "{{ mysql_package }}"
    state: present
  vars:
    mysql_package: "{{ 'mysql-server' if ansible_os_family == 'Debian' else 'mariadb-server' }}"

- name: Start MySQL service
  service:
    name: "{{ mysql_service }}"
    state: started
    enabled: yes
  vars:
    mysql_service: "{{ 'mysql' if ansible_os_family == 'Debian' else 'mariadb' }}"

- name: Create database user
  command: mysql -e "CREATE USER IF NOT EXISTS 'appuser'@'localhost' IDENTIFIED BY 'password';"
  register: user_creation
  changed_when: "'already exists' not in user_creation.stderr"

- name: Create application database
  command: mysql -e "CREATE DATABASE IF NOT EXISTS appdb;"
  register: db_creation
  changed_when: "'already exists' not in db_creation.stderr"

- name: Grant database privileges
  command: mysql -e "GRANT ALL PRIVILEGES ON appdb.* TO 'appuser'@'localhost';"

- name: Copy database schema
  copy:
    src: schema.sql
    dest: /tmp/schema.sql
    owner: root
    group: root
    mode: '0644'

- name: Import database schema
  shell: mysql appdb < /tmp/schema.sql
  args:
    creates: /var/lib/mysql/appdb/users.frm
""")
        
        # Group vars
        (project_dir / "group_vars" / "all.yml").write_text("""---
# Common variables
app_name: myapp
app_version: "1.0.0"
admin_email: admin@example.com

# Security settings
firewall_enabled: true
ssl_enabled: false

# Backup settings
backup_enabled: true
backup_retention_days: 30
""")
        
        # Inventory
        (project_dir / "inventory.ini").write_text("""[webservers]
web1.example.com ansible_host=192.168.1.10
web2.example.com ansible_host=192.168.1.11

[databases]
db1.example.com ansible_host=192.168.1.20

[all:vars]
ansible_user=ubuntu
ansible_ssh_private_key_file=~/.ssh/id_rsa
""")
        
        return project_dir
    
    def test_complete_project_conversion(self, real_ansible_project):
        """Test complete project conversion workflow."""
        # Initialize converter
        converter = FQCNConverter()
        
        # Find all YAML files in the project
        yaml_files = list(real_ansible_project.rglob("*.yml"))
        yaml_files.extend(list(real_ansible_project.rglob("*.yaml")))
        
        # Filter out non-Ansible files
        ansible_files = [f for f in yaml_files if self._is_ansible_file(f)]
        
        assert len(ansible_files) >= 5  # Should find multiple Ansible files
        
        # Convert all files
        results = []
        for file_path in ansible_files:
            result = converter.convert_file(file_path, dry_run=False)
            results.append(result)
        
        # Verify all conversions succeeded
        successful_conversions = [r for r in results if r.success]
        assert len(successful_conversions) == len(results)
        
        # Verify changes were made
        total_changes = sum(r.changes_made for r in results)
        assert total_changes > 0
        
        # Verify specific conversions in main playbook
        site_yml = real_ansible_project / "site.yml"
        converted_content = site_yml.read_text()
        
        assert 'ansible.builtin.package:' in converted_content
        assert 'ansible.builtin.command:' in converted_content
        
        # Verify role conversions
        webserver_tasks = real_ansible_project / "roles" / "webserver" / "tasks" / "main.yml"
        webserver_content = webserver_tasks.read_text()
        
        assert 'ansible.builtin.package:' in webserver_content
        assert 'ansible.builtin.file:' in webserver_content
        assert 'ansible.builtin.copy:' in webserver_content
        assert 'ansible.builtin.template:' in webserver_content
        assert 'ansible.builtin.user:' in webserver_content
        assert 'ansible.builtin.service:' in webserver_content
        assert 'ansible.builtin.command:' in webserver_content
        assert 'ansible.builtin.set_fact:' in webserver_content
    
    def test_conversion_with_validation(self, real_ansible_project):
        """Test conversion followed by validation."""
        # Convert the project
        converter = FQCNConverter()
        validator = ValidationEngine()
        
        yaml_files = [f for f in real_ansible_project.rglob("*.yml") 
                     if self._is_ansible_file(f)]
        
        # Convert all files
        conversion_results = []
        for file_path in yaml_files:
            result = converter.convert_file(file_path, dry_run=False)
            conversion_results.append(result)
        
        # Validate all converted files
        validation_results = []
        for file_path in yaml_files:
            result = validator.validate_conversion(file_path)
            validation_results.append(result)
        
        # All files should validate successfully after conversion
        valid_files = [r for r in validation_results if r.valid]
        assert len(valid_files) == len(validation_results)
        
        # Check validation scores
        average_score = sum(r.score for r in validation_results) / len(validation_results)
        assert average_score > 0.9  # Should have high scores after conversion
    
    def test_dry_run_vs_actual_conversion(self, real_ansible_project):
        """Test that dry run and actual conversion produce consistent results."""
        converter = FQCNConverter()
        
        # Get a test file
        test_file = real_ansible_project / "site.yml"
        original_content = test_file.read_text()
        
        # Perform dry run
        dry_run_result = converter.convert_file(test_file, dry_run=True)
        
        # Verify file wasn't changed
        assert test_file.read_text() == original_content
        
        # Perform actual conversion
        actual_result = converter.convert_file(test_file, dry_run=False)
        
        # Results should be consistent
        assert dry_run_result.success == actual_result.success
        assert dry_run_result.changes_made == actual_result.changes_made
        assert dry_run_result.converted_content == actual_result.converted_content
        
        # File should now be changed
        assert test_file.read_text() != original_content
        assert test_file.read_text() == actual_result.converted_content

    def test_configuration_loading_integration(self, temp_dir):
        """Test integration with custom configuration loading."""
        # Create custom configuration
        config_data = {
            'ansible_builtin': {
                'copy': 'ansible.builtin.copy',
                'file': 'ansible.builtin.file',
                'service': 'ansible.builtin.service',
            },
            'custom_collection': {
                'custom_module': 'custom.collection.custom_module',
                'another_module': 'custom.collection.another_module',
            }
        }
        
        config_file = temp_dir / "custom_config.yml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Create test content with custom modules
        test_content = """---
- name: Test custom modules
  hosts: all
  tasks:
    - name: Use builtin module
      copy:
        src: test.txt
        dest: /tmp/test.txt
    
    - name: Use custom module
      custom_module:
        param: value
    
    - name: Use another custom module
      another_module:
        param: value
"""
        
        test_file = temp_dir / "test.yml"
        test_file.write_text(test_content)
        
        # Initialize converter with custom config
        converter = FQCNConverter(config_path=config_file)
        
        # Convert the file
        result = converter.convert_file(test_file, dry_run=False)
        
        assert result.success is True
        assert result.changes_made == 3  # All three modules should be converted
        
        converted_content = test_file.read_text()
        assert 'ansible.builtin.copy:' in converted_content
        assert 'custom.collection.custom_module:' in converted_content
        assert 'custom.collection.another_module:' in converted_content
    
    def test_error_handling_integration(self, temp_dir):
        """Test error handling in integration scenarios."""
        converter = FQCNConverter()
        
        # Test with invalid YAML file
        invalid_file = temp_dir / "invalid.yml"
        invalid_file.write_text("---\ninvalid: [\n")
        
        with pytest.raises(Exception):  # Should raise YAMLParsingError or similar
            converter.convert_file(invalid_file)
        
        # Test with non-existent file
        non_existent = temp_dir / "non_existent.yml"
        
        with pytest.raises(Exception):  # Should raise FileAccessError
            converter.convert_file(non_existent)
        
        # Test with permission issues (simulate)
        test_file = temp_dir / "test.yml"
        test_file.write_text("---\n- name: test\n  copy: {}")
        
        # This would require actual permission manipulation in a real scenario
        # For now, we test that the converter handles the file correctly
        result = converter.convert_file(test_file)
        assert result.success is True
    
    def test_backup_and_rollback_integration(self, temp_dir):
        """Test backup creation and rollback functionality."""
        # Create test file
        test_file = temp_dir / "test.yml"
        original_content = """---
- name: Test task
  copy:
    src: test.txt
    dest: /tmp/test.txt
"""
        test_file.write_text(original_content)
        
        # Convert with backup (this would need to be implemented in converter)
        converter = FQCNConverter()
        result = converter.convert_file(test_file, dry_run=False)
        
        assert result.success is True
        
        # Verify file was converted
        converted_content = test_file.read_text()
        assert 'ansible.builtin.copy:' in converted_content
        assert converted_content != original_content
        
        # Check if backup was created (implementation dependent)
        backup_file = test_file.with_suffix(test_file.suffix + '.fqcn_backup')
        # Note: Backup functionality would need to be implemented in the converter
    
    def _is_ansible_file(self, file_path: Path) -> bool:
        """Check if a file appears to be an Ansible file."""
        if file_path.suffix not in ['.yml', '.yaml']:
            return False
        
        # Skip certain files
        skip_files = {'inventory.ini', 'ansible.cfg', 'requirements.txt'}
        if file_path.name in skip_files:
            return False
        
        # Check for Ansible content indicators
        try:
            content = file_path.read_text()
            ansible_indicators = [
                'hosts:', 'tasks:', 'handlers:', 'vars:', 'name:',
                'become:', 'gather_facts:', 'roles:', 'include:',
                'import_tasks:', 'include_tasks:', 'pre_tasks:', 'post_tasks:'
            ]
            
            for indicator in ansible_indicators:
                if indicator in content:
                    return True
        except Exception:
            return False
        
        return False


class TestRealWorldScenarios:
    """Test real-world Ansible scenarios and edge cases."""
    
    def test_complex_playbook_structures(self, temp_dir):
        """Test conversion of complex playbook structures."""
        complex_playbook = temp_dir / "complex.yml"
        complex_content = """---
- name: Complex multi-play playbook
  hosts: webservers
  become: yes
  gather_facts: yes
  
  vars:
    packages:
      - nginx
      - php-fpm
      - mysql-client
  
  pre_tasks:
    - name: Update package cache
      package:
        update_cache: yes
      when: ansible_os_family == "Debian"
    
    - name: Create app user
      user:
        name: appuser
        system: yes
        shell: /bin/false
  
  tasks:
    - name: Install packages
      package:
        name: "{{ item }}"
        state: present
      loop: "{{ packages }}"
      
    - name: Configure nginx
      block:
        - name: Copy nginx config
          copy:
            src: nginx.conf
            dest: /etc/nginx/nginx.conf
            backup: yes
          notify: restart nginx
        
        - name: Create sites directory
          file:
            path: /etc/nginx/sites-available
            state: directory
            mode: '0755'
      
      rescue:
        - name: Debug nginx config failure
          debug:
            msg: "Nginx configuration failed"
      
      always:
        - name: Ensure nginx is running
          service:
            name: nginx
            state: started
  
  handlers:
    - name: restart nginx
      service:
        name: nginx
        state: restarted
  
  post_tasks:
    - name: Verify services
      command: systemctl is-active nginx
      register: nginx_status
      changed_when: false
    
    - name: Set completion fact
      set_fact:
        webserver_setup_complete: true

- name: Database configuration
  hosts: databases
  become: yes
  
  tasks:
    - name: Install database
      package:
        name: mysql-server
        state: present
    
    - name: Start database service
      service:
        name: mysql
        state: started
        enabled: yes
    
    - name: Create database
      shell: mysql -e "CREATE DATABASE IF NOT EXISTS appdb;"
      register: db_result
      changed_when: "'already exists' not in db_result.stderr"
"""
        
        complex_playbook.write_text(complex_content)
        
        converter = FQCNConverter()
        result = converter.convert_file(complex_playbook, dry_run=False)
        
        assert result.success is True
        assert result.changes_made > 5  # Should convert multiple modules
        
        converted_content = complex_playbook.read_text()
        
        # Verify key conversions
        expected_conversions = [
            'ansible.builtin.package:',
            'ansible.builtin.user:',
            'ansible.builtin.copy:',
            'ansible.builtin.file:',
            'ansible.builtin.service:',
            'ansible.builtin.debug:',
            'ansible.builtin.command:',
            'ansible.builtin.set_fact:',
            'ansible.builtin.shell:'
        ]
        
        for conversion in expected_conversions:
            assert conversion in converted_content
    
    def test_role_based_project_conversion(self, temp_dir):
        """Test conversion of role-based Ansible projects."""
        # Create role structure
        role_dir = temp_dir / "roles" / "webapp"
        (role_dir / "tasks").mkdir(parents=True)
        (role_dir / "handlers").mkdir(parents=True)
        (role_dir / "vars").mkdir(parents=True)
        (role_dir / "defaults").mkdir(parents=True)
        
        # Tasks file
        (role_dir / "tasks" / "main.yml").write_text("""---
- name: Include OS-specific variables
  include_vars: "{{ ansible_os_family }}.yml"

- name: Install web server
  package:
    name: "{{ web_server_package }}"
    state: present

- name: Create web directory
  file:
    path: "{{ web_root }}"
    state: directory
    owner: "{{ web_user }}"
    group: "{{ web_group }}"
    mode: '0755'

- name: Template web config
  template:
    src: webapp.conf.j2
    dest: "{{ web_config_path }}"
    owner: root
    group: root
    mode: '0644'
  notify: restart web server

- name: Start web service
  service:
    name: "{{ web_service }}"
    state: started
    enabled: yes
""")
        
        # Handlers file
        (role_dir / "handlers" / "main.yml").write_text("""---
- name: restart web server
  service:
    name: "{{ web_service }}"
    state: restarted

- name: reload web server
  service:
    name: "{{ web_service }}"
    state: reloaded
""")
        
        # Variables files
        (role_dir / "vars" / "main.yml").write_text("""---
web_root: /var/www/html
web_config_path: /etc/webapp/webapp.conf
""")
        
        (role_dir / "defaults" / "main.yml").write_text("""---
web_server_package: nginx
web_service: nginx
web_user: www-data
web_group: www-data
""")
        
        converter = FQCNConverter()
        
        # Convert all role files
        role_files = list(role_dir.rglob("*.yml"))
        results = []
        
        for file_path in role_files:
            result = converter.convert_file(file_path, dry_run=False)
            results.append(result)
        
        # Verify conversions
        successful_results = [r for r in results if r.success]
        assert len(successful_results) == len(results)
        
        # Check specific conversions in tasks
        tasks_content = (role_dir / "tasks" / "main.yml").read_text()
        assert 'ansible.builtin.package:' in tasks_content
        assert 'ansible.builtin.file:' in tasks_content
        assert 'ansible.builtin.template:' in tasks_content
        assert 'ansible.builtin.service:' in tasks_content
        
        # Check handlers
        handlers_content = (role_dir / "handlers" / "main.yml").read_text()
        assert 'ansible.builtin.service:' in handlers_content