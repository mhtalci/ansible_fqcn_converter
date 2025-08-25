"""
Sample Ansible content fixtures for testing.

This module provides a comprehensive library of sample Ansible content
including playbooks, roles, tasks, and various edge cases.
"""

from typing import Dict, List, Any


class SamplePlaybooks:
    """Collection of sample Ansible playbooks for testing."""
    
    @staticmethod
    def simple_web_server() -> str:
        """Simple web server playbook."""
        return """---
- name: Simple web server setup
  hosts: webservers
  become: yes
  
  tasks:
    - name: Install nginx
      package:
        name: nginx
        state: present
    
    - name: Start nginx service
      service:
        name: nginx
        state: started
        enabled: yes
    
    - name: Copy index page
      copy:
        content: "<h1>Hello World</h1>"
        dest: /var/www/html/index.html
        owner: www-data
        group: www-data
        mode: '0644'
"""
    
    @staticmethod
    def complex_multi_role() -> str:
        """Complex multi-role playbook."""
        return """---
- name: Infrastructure setup
  hosts: all
  become: yes
  gather_facts: yes
  
  vars:
    app_name: myapp
    app_version: "1.2.3"
    admin_users:
      - alice
      - bob
      - charlie
  
  pre_tasks:
    - name: Update package cache
      package:
        update_cache: yes
      when: ansible_os_family == "Debian"
    
    - name: Install common packages
      package:
        name: "{{ item }}"
        state: present
      loop:
        - curl
        - wget
        - vim
        - htop
  
  roles:
    - common
    - security
    - monitoring
  
  tasks:
    - name: Create application directory
      file:
        path: "/opt/{{ app_name }}"
        state: directory
        owner: root
        group: root
        mode: '0755'
    
    - name: Template application config
      template:
        src: "{{ app_name }}.conf.j2"
        dest: "/etc/{{ app_name }}/{{ app_name }}.conf"
        owner: "{{ app_name }}"
        group: "{{ app_name }}"
        mode: '0640'
        backup: yes
      notify: restart application
    
    - name: Create admin users
      user:
        name: "{{ item }}"
        groups: sudo
        shell: /bin/bash
        create_home: yes
      loop: "{{ admin_users }}"
    
    - name: Set up SSH keys for admin users
      authorized_key:
        user: "{{ item }}"
        key: "{{ lookup('file', 'keys/' + item + '.pub') }}"
        state: present
      loop: "{{ admin_users }}"
  
  handlers:
    - name: restart application
      systemd:
        name: "{{ app_name }}"
        state: restarted
        daemon_reload: yes
  
  post_tasks:
    - name: Verify application is running
      command: "systemctl is-active {{ app_name }}"
      register: app_status
      changed_when: false
    
    - name: Set deployment facts
      set_fact:
        deployment_complete: true
        deployment_timestamp: "{{ ansible_date_time.iso8601 }}"
        app_status: "{{ app_status.stdout }}"

- name: Database configuration
  hosts: databases
  become: yes
  
  vars:
    db_name: "{{ app_name }}_db"
    db_user: "{{ app_name }}_user"
  
  tasks:
    - name: Install database server
      package:
        name: "{{ db_package }}"
        state: present
      vars:
        db_package: "{{ 'postgresql' if ansible_os_family == 'Debian' else 'postgresql-server' }}"
    
    - name: Start database service
      service:
        name: "{{ db_service }}"
        state: started
        enabled: yes
      vars:
        db_service: "{{ 'postgresql' if ansible_os_family == 'Debian' else 'postgresql' }}"
    
    - name: Create database
      postgresql_db:
        name: "{{ db_name }}"
        state: present
      become_user: postgres
    
    - name: Create database user
      postgresql_user:
        name: "{{ db_user }}"
        password: "{{ db_password }}"
        db: "{{ db_name }}"
        priv: ALL
        state: present
      become_user: postgres
"""
    
    @staticmethod
    def legacy_syntax() -> str:
        """Playbook with legacy Ansible syntax."""
        return """---
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
    
    - name: ensure apache is running (and enable it at boot)
      service: name=httpd enabled=yes state=started
  
  handlers:
    - name: restart apache
      service: name=httpd state=restarted
"""
    
    @staticmethod
    def with_blocks_and_error_handling() -> str:
        """Playbook with blocks, rescue, and always sections."""
        return """---
- name: Error handling example
  hosts: all
  become: yes
  
  tasks:
    - name: Attempt risky operations
      block:
        - name: Download application
          get_url:
            url: "https://example.com/app.tar.gz"
            dest: "/tmp/app.tar.gz"
            timeout: 30
        
        - name: Extract application
          unarchive:
            src: "/tmp/app.tar.gz"
            dest: "/opt/"
            remote_src: yes
            owner: root
            group: root
        
        - name: Install application
          command: "/opt/app/install.sh"
          args:
            creates: "/opt/app/.installed"
      
      rescue:
        - name: Log failure
          debug:
            msg: "Application installation failed"
        
        - name: Clean up failed installation
          file:
            path: "{{ item }}"
            state: absent
          loop:
            - "/tmp/app.tar.gz"
            - "/opt/app"
        
        - name: Send failure notification
          mail:
            to: admin@example.com
            subject: "Application installation failed"
            body: "The application installation failed on {{ inventory_hostname }}"
      
      always:
        - name: Update package cache
          package:
            update_cache: yes
        
        - name: Ensure cleanup script is present
          copy:
            content: |
              #!/bin/bash
              # Cleanup script
              rm -f /tmp/app.tar.gz
            dest: "/usr/local/bin/cleanup.sh"
            mode: '0755'
"""
    
    @staticmethod
    def with_includes_and_imports() -> str:
        """Playbook with includes and imports."""
        return """---
- name: Modular playbook example
  hosts: all
  become: yes
  
  pre_tasks:
    - name: Include OS-specific variables
      include_vars: "{{ ansible_os_family }}.yml"
    
    - name: Import common tasks
      import_tasks: common/setup.yml
  
  tasks:
    - name: Include conditional tasks
      include_tasks: "{{ item }}"
      loop:
        - security/firewall.yml
        - monitoring/setup.yml
      when: enable_security | default(true)
    
    - name: Import role tasks directly
      import_tasks: roles/webserver/tasks/main.yml
      when: install_webserver | default(false)
    
    - name: Include dynamic tasks
      include_tasks: "dynamic/{{ service_type }}.yml"
      vars:
        service_type: "{{ ansible_service_mgr }}"
  
  post_tasks:
    - name: Import cleanup tasks
      import_tasks: common/cleanup.yml
"""


class SampleRoles:
    """Collection of sample Ansible roles for testing."""
    
    @staticmethod
    def webserver_role() -> Dict[str, str]:
        """Complete webserver role files."""
        return {
            'tasks/main.yml': """---
# Main tasks for webserver role
- name: Include OS-specific variables
  include_vars: "{{ ansible_os_family }}.yml"

- name: Install web server package
  package:
    name: "{{ webserver_package }}"
    state: present

- name: Create web server user
  user:
    name: "{{ webserver_user }}"
    system: yes
    shell: /bin/false
    home: "{{ webserver_home }}"
    create_home: no

- name: Create web directories
  file:
    path: "{{ item }}"
    state: directory
    owner: "{{ webserver_user }}"
    group: "{{ webserver_group }}"
    mode: '0755'
  loop:
    - "{{ webserver_document_root }}"
    - "{{ webserver_log_dir }}"
    - "{{ webserver_config_dir }}"

- name: Template main configuration
  template:
    src: "{{ webserver_package }}.conf.j2"
    dest: "{{ webserver_config_dir }}/{{ webserver_package }}.conf"
    owner: root
    group: root
    mode: '0644'
    backup: yes
  notify: restart webserver

- name: Template virtual host configuration
  template:
    src: vhost.conf.j2
    dest: "{{ webserver_config_dir }}/sites-available/{{ item.name }}.conf"
    owner: root
    group: root
    mode: '0644'
  loop: "{{ webserver_vhosts }}"
  notify: restart webserver

- name: Enable virtual hosts
  file:
    src: "{{ webserver_config_dir }}/sites-available/{{ item.name }}.conf"
    dest: "{{ webserver_config_dir }}/sites-enabled/{{ item.name }}.conf"
    state: link
  loop: "{{ webserver_vhosts }}"
  notify: restart webserver

- name: Start and enable web server
  service:
    name: "{{ webserver_service }}"
    state: started
    enabled: yes

- name: Configure firewall
  ufw:
    rule: allow
    port: "{{ item }}"
    proto: tcp
  loop:
    - 80
    - 443
  when: configure_firewall | default(true)
""",
            
            'handlers/main.yml': """---
- name: restart webserver
  service:
    name: "{{ webserver_service }}"
    state: restarted

- name: reload webserver
  service:
    name: "{{ webserver_service }}"
    state: reloaded

- name: restart firewall
  service:
    name: ufw
    state: restarted
""",
            
            'vars/main.yml': """---
webserver_document_root: /var/www/html
webserver_log_dir: /var/log/webserver
webserver_config_dir: /etc/webserver
webserver_user: www-data
webserver_group: www-data

webserver_vhosts:
  - name: default
    document_root: "{{ webserver_document_root }}"
    server_name: localhost
  - name: example
    document_root: "{{ webserver_document_root }}/example"
    server_name: example.com
""",
            
            'defaults/main.yml': """---
webserver_package: nginx
webserver_service: nginx
webserver_home: /var/www
configure_firewall: true
enable_ssl: false
""",
            
            'meta/main.yml': """---
galaxy_info:
  author: Test Author
  description: Web server configuration role
  company: Test Company
  license: MIT
  min_ansible_version: 2.9
  
  platforms:
    - name: Ubuntu
      versions:
        - bionic
        - focal
    - name: CentOS
      versions:
        - 7
        - 8

  galaxy_tags:
    - webserver
    - nginx
    - apache

dependencies: []
"""
        }
    
    @staticmethod
    def database_role() -> Dict[str, str]:
        """Complete database role files."""
        return {
            'tasks/main.yml': """---
- name: Install database packages
  package:
    name: "{{ item }}"
    state: present
  loop: "{{ database_packages }}"

- name: Create database user
  user:
    name: "{{ database_user }}"
    system: yes
    shell: /bin/false
    home: "{{ database_home }}"
    create_home: yes

- name: Create database directories
  file:
    path: "{{ item }}"
    state: directory
    owner: "{{ database_user }}"
    group: "{{ database_group }}"
    mode: '0755'
  loop:
    - "{{ database_data_dir }}"
    - "{{ database_log_dir }}"
    - "{{ database_config_dir }}"

- name: Initialize database
  command: "{{ database_init_command }}"
  args:
    creates: "{{ database_data_dir }}/{{ database_init_marker }}"
  become_user: "{{ database_user }}"

- name: Template database configuration
  template:
    src: "{{ database_type }}.conf.j2"
    dest: "{{ database_config_dir }}/{{ database_type }}.conf"
    owner: "{{ database_user }}"
    group: "{{ database_group }}"
    mode: '0600'
    backup: yes
  notify: restart database

- name: Start and enable database service
  service:
    name: "{{ database_service }}"
    state: started
    enabled: yes

- name: Create application databases
  mysql_db:
    name: "{{ item.name }}"
    state: present
    login_user: root
    login_password: "{{ mysql_root_password }}"
  loop: "{{ application_databases }}"
  when: database_type == "mysql"

- name: Create application users
  mysql_user:
    name: "{{ item.user }}"
    password: "{{ item.password }}"
    priv: "{{ item.name }}.*:ALL"
    state: present
    login_user: root
    login_password: "{{ mysql_root_password }}"
  loop: "{{ application_databases }}"
  when: database_type == "mysql"
""",
            
            'handlers/main.yml': """---
- name: restart database
  service:
    name: "{{ database_service }}"
    state: restarted

- name: reload database
  service:
    name: "{{ database_service }}"
    state: reloaded
""",
            
            'defaults/main.yml': """---
database_type: mysql
database_user: mysql
database_group: mysql
database_home: /var/lib/mysql
database_data_dir: /var/lib/mysql
database_log_dir: /var/log/mysql
database_config_dir: /etc/mysql

database_packages:
  - mysql-server
  - mysql-client
  - python3-pymysql

database_service: mysql
database_init_command: mysql_install_db
database_init_marker: mysql

mysql_root_password: "{{ vault_mysql_root_password | default('changeme') }}"

application_databases: []
"""
        }


class SampleTaskFiles:
    """Collection of sample task files for testing."""
    
    @staticmethod
    def system_setup() -> str:
        """System setup tasks."""
        return """---
- name: Update package cache
  package:
    update_cache: yes
  when: ansible_os_family == "Debian"

- name: Install essential packages
  package:
    name: "{{ item }}"
    state: present
  loop:
    - curl
    - wget
    - vim
    - htop
    - git
    - unzip

- name: Create system users
  user:
    name: "{{ item.name }}"
    uid: "{{ item.uid | default(omit) }}"
    groups: "{{ item.groups | default([]) }}"
    shell: "{{ item.shell | default('/bin/bash') }}"
    create_home: "{{ item.create_home | default(true) }}"
    system: "{{ item.system | default(false) }}"
  loop: "{{ system_users }}"

- name: Configure sudo access
  lineinfile:
    path: /etc/sudoers.d/{{ item.name }}
    line: "{{ item.name }} ALL=(ALL) NOPASSWD:ALL"
    create: yes
    mode: '0440'
    validate: 'visudo -cf %s'
  loop: "{{ system_users }}"
  when: item.sudo | default(false)

- name: Set up SSH keys
  authorized_key:
    user: "{{ item.0.name }}"
    key: "{{ item.1 }}"
    state: present
  loop: "{{ system_users | subelements('ssh_keys', skip_missing=True) }}"

- name: Configure system timezone
  timezone:
    name: "{{ system_timezone | default('UTC') }}"

- name: Configure system hostname
  hostname:
    name: "{{ inventory_hostname }}"

- name: Update /etc/hosts
  lineinfile:
    path: /etc/hosts
    line: "127.0.1.1 {{ inventory_hostname }}"
    regexp: "^127\\.0\\.1\\.1"
"""
    
    @staticmethod
    def security_hardening() -> str:
        """Security hardening tasks."""
        return """---
- name: Install security packages
  package:
    name: "{{ item }}"
    state: present
  loop:
    - fail2ban
    - ufw
    - unattended-upgrades
    - aide

- name: Configure SSH security
  lineinfile:
    path: /etc/ssh/sshd_config
    regexp: "{{ item.regexp }}"
    line: "{{ item.line }}"
    backup: yes
  loop:
    - { regexp: '^#?PermitRootLogin', line: 'PermitRootLogin no' }
    - { regexp: '^#?PasswordAuthentication', line: 'PasswordAuthentication no' }
    - { regexp: '^#?PubkeyAuthentication', line: 'PubkeyAuthentication yes' }
    - { regexp: '^#?Port', line: 'Port {{ ssh_port | default(22) }}' }
  notify: restart ssh

- name: Configure firewall default policies
  ufw:
    direction: "{{ item.direction }}"
    policy: "{{ item.policy }}"
  loop:
    - { direction: incoming, policy: deny }
    - { direction: outgoing, policy: allow }

- name: Allow SSH through firewall
  ufw:
    rule: allow
    port: "{{ ssh_port | default(22) }}"
    proto: tcp

- name: Enable firewall
  ufw:
    state: enabled

- name: Configure fail2ban
  template:
    src: jail.local.j2
    dest: /etc/fail2ban/jail.local
    owner: root
    group: root
    mode: '0644'
    backup: yes
  notify: restart fail2ban

- name: Start and enable security services
  service:
    name: "{{ item }}"
    state: started
    enabled: yes
  loop:
    - fail2ban
    - ufw

- name: Configure automatic updates
  template:
    src: 50unattended-upgrades.j2
    dest: /etc/apt/apt.conf.d/50unattended-upgrades
    owner: root
    group: root
    mode: '0644'
  when: ansible_os_family == "Debian"

- name: Initialize AIDE database
  command: aide --init
  args:
    creates: /var/lib/aide/aide.db.new

- name: Move AIDE database
  command: mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db
  args:
    creates: /var/lib/aide/aide.db
"""


class EdgeCaseContent:
    """Edge case content for testing converter robustness."""
    
    @staticmethod
    def malformed_yaml() -> str:
        """Malformed YAML content."""
        return """---
- name: Malformed YAML
  hosts: all
  tasks:
    - name: Invalid structure
      invalid: [
"""
    
    @staticmethod
    def empty_file() -> str:
        """Empty file content."""
        return ""
    
    @staticmethod
    def comments_only() -> str:
        """File with only comments."""
        return """# This file contains only comments
# No actual Ansible content
# Should be handled gracefully
"""
    
    @staticmethod
    def mixed_indentation() -> str:
        """Content with mixed indentation."""
        return """---
- name: Mixed indentation test
  hosts: all
  tasks:
    - name: Normal indentation
      package:
        name: nginx
        state: present
	- name: Tab indentation (problematic)
	  service:
	    name: nginx
	    state: started
"""
    
    @staticmethod
    def unicode_content() -> str:
        """Content with Unicode characters."""
        return """---
- name: Unicode test playbook 🚀
  hosts: all
  vars:
    message: "Hello, 世界! Здравствуй мир! مرحبا بالعالم!"
  
  tasks:
    - name: Create file with Unicode content
      copy:
        content: "{{ message }}"
        dest: /tmp/unicode_test.txt
        mode: '0644'
    
    - name: Debug Unicode message
      debug:
        msg: "Processing: {{ message }}"
"""
    
    @staticmethod
    def very_long_lines() -> str:
        """Content with very long lines."""
        return """---
- name: Very long lines test
  hosts: all
  tasks:
    - name: Task with extremely long command line that goes on and on and on and should test how the converter handles very long lines that might cause issues with parsing or processing
      command: echo "This is a very long command line that contains many words and should test the converter's ability to handle long lines without breaking or causing issues with the YAML parsing or the conversion process itself"
    
    - name: Package with long name
      package:
        name: "this-is-a-very-long-package-name-that-might-be-used-in-some-enterprise-environments-where-package-names-can-be-quite-verbose-and-descriptive"
        state: present
"""
    
    @staticmethod
    def nested_variables() -> str:
        """Content with deeply nested variables."""
        return """---
- name: Nested variables test
  hosts: all
  vars:
    app:
      name: myapp
      config:
        database:
          host: "{{ groups['databases'][0] }}"
          port: 5432
          name: "{{ app.name }}_db"
          user: "{{ app.name }}_user"
        web:
          port: "{{ app.config.web.port | default(8080) }}"
          workers: "{{ ansible_processor_vcpus * 2 }}"
  
  tasks:
    - name: Create config directory
      file:
        path: "/etc/{{ app.name }}"
        state: directory
        mode: '0755'
    
    - name: Template complex configuration
      template:
        src: "{{ app.name }}.conf.j2"
        dest: "/etc/{{ app.name }}/{{ app.name }}.conf"
        owner: "{{ app.name }}"
        group: "{{ app.name }}"
        mode: '0640'
      vars:
        db_connection_string: "postgresql://{{ app.config.database.user }}:{{ vault_db_password }}@{{ app.config.database.host }}:{{ app.config.database.port }}/{{ app.config.database.name }}"
"""


class ConversionTestCases:
    """Test cases for specific conversion scenarios."""
    
    @staticmethod
    def parameter_vs_module_conflicts() -> str:
        """Content that tests parameter vs module name conflicts."""
        return """---
- name: Parameter vs module conflict test
  hosts: all
  tasks:
    - name: User task with group parameter (group parameter should NOT be converted)
      user:
        name: johnd
        group: admin
        shell: /bin/bash
    
    - name: Group task (group module SHOULD be converted)
      group:
        name: admin
        state: present
    
    - name: Copy task with owner/group parameters (parameters should NOT be converted)
      copy:
        src: test.conf
        dest: /etc/test.conf
        owner: root
        group: wheel
        mode: '0644'
    
    - name: Set fact with variable names (variables should NOT be converted)
      set_fact:
        my_user: johnd
        my_group: admin
        service_name: nginx
        copy_source: /tmp/file
    
    - name: Service task (service module SHOULD be converted)
      service:
        name: nginx
        state: started
"""
    
    @staticmethod
    def already_converted_mixed() -> str:
        """Content with mix of converted and unconverted modules."""
        return """---
- name: Mixed conversion state
  hosts: all
  tasks:
    - name: Already converted copy
      ansible.builtin.copy:
        src: test.txt
        dest: /tmp/test.txt
    
    - name: Not converted package
      package:
        name: nginx
        state: present
    
    - name: Already converted service
      ansible.builtin.service:
        name: nginx
        state: started
    
    - name: Not converted user
      user:
        name: testuser
        state: present
    
    - name: Community collection (should remain unchanged)
      community.docker.docker_container:
        name: nginx
        image: nginx:latest
        state: started
"""
    
    @staticmethod
    def complex_jinja_expressions() -> str:
        """Content with complex Jinja2 expressions."""
        return """---
- name: Complex Jinja expressions
  hosts: all
  tasks:
    - name: Complex package installation
      package:
        name: "{{ item.name if item.version is undefined else item.name + '=' + item.version }}"
        state: "{{ item.state | default('present') }}"
      loop: "{{ packages | selectattr('enabled', 'equalto', true) | list }}"
      when: >
        (ansible_os_family == "Debian" and item.debian_supported | default(true)) or
        (ansible_os_family == "RedHat" and item.redhat_supported | default(true))
    
    - name: Conditional service management
      service:
        name: "{{ service_name }}"
        state: "{{ 'started' if enable_service | bool else 'stopped' }}"
        enabled: "{{ enable_service | bool }}"
      vars:
        service_name: "{{ app_services[ansible_os_family] | default('nginx') }}"
        enable_service: "{{ (inventory_hostname in groups['webservers']) and (deploy_env != 'development') }}"
"""