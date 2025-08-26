"""
Ansible version compatibility tests for FQCN Converter.

These tests validate compatibility across different Ansible versions,
collection formats, and syntax variations to ensure broad compatibility.
"""

import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from fqcn_converter.core.converter import FQCNConverter
from fqcn_converter.core.validator import ValidationEngine


class AnsibleVersionTestData:
    """Test data for different Ansible versions and formats."""

    @staticmethod
    def get_ansible_2_9_playbook() -> str:
        """Ansible 2.9 style playbook with legacy syntax."""
        return """---
- hosts: webservers
  sudo: yes
  gather_facts: yes
  
  vars:
    packages:
      - httpd
      - php
      - mysql-client
    
  tasks:
    - name: update package cache
      yum: update_cache=yes
      when: ansible_os_family == "RedHat"
    
    - name: install packages
      yum: name={{ item }} state=present
      with_items: "{{ packages }}"
    
    - name: copy apache config
      copy: src=httpd.conf dest=/etc/httpd/conf/httpd.conf backup=yes
      notify:
        - restart httpd
    
    - name: start apache
      service: name=httpd state=started enabled=yes
    
    - name: create web user
      user: name=apache system=yes shell=/sbin/nologin
    
    - name: set permissions
      file: path=/var/www/html owner=apache group=apache mode=0755 recurse=yes
    
    - name: configure firewall
      command: firewall-cmd --permanent --add-service=http
      register: firewall_result
      changed_when: "'ALREADY_ENABLED' not in firewall_result.stderr"
    
    - name: reload firewall
      command: firewall-cmd --reload
      when: firewall_result.changed
  
  handlers:
    - name: restart httpd
      service: name=httpd state=restarted

- hosts: databases
  sudo: yes
  
  tasks:
    - name: install mysql
      yum: name=mysql-server state=present
    
    - name: start mysql
      service: name=mysqld state=started enabled=yes
    
    - name: create database
      mysql_db: name=webapp state=present
    
    - name: create db user
      mysql_user: name=webapp password=secret priv=webapp.*:ALL state=present
"""

    @staticmethod
    def get_ansible_2_10_playbook() -> str:
        """Ansible 2.10 style with collections awareness."""
        return """---
- name: Web server setup (Ansible 2.10)
  hosts: webservers
  become: yes
  gather_facts: yes
  
  vars:
    web_packages:
      - httpd
      - php
      - php-mysql
  
  tasks:
    - name: Install web packages
      package:
        name: "{{ item }}"
        state: present
      loop: "{{ web_packages }}"
    
    - name: Configure Apache
      template:
        src: httpd.conf.j2
        dest: /etc/httpd/conf/httpd.conf
        backup: yes
      notify: restart apache
    
    - name: Start and enable Apache
      systemd:
        name: httpd
        state: started
        enabled: yes
    
    - name: Create web directories
      file:
        path: "{{ item }}"
        state: directory
        owner: apache
        group: apache
        mode: '0755'
      loop:
        - /var/www/html/app
        - /var/log/webapp
    
    - name: Configure SELinux for web
      sefcontext:
        target: '/var/www/html/app(/.*)?'
        setype: httpd_exec_t
        state: present
      register: selinux_context
    
    - name: Apply SELinux context
      command: restorecon -R /var/www/html/app
      when: selinux_context.changed
    
    - name: Configure firewall
      firewalld:
        service: http
        permanent: yes
        state: enabled
        immediate: yes
  
  handlers:
    - name: restart apache
      systemd:
        name: httpd
        state: restarted

- name: Database setup (Ansible 2.10)
  hosts: databases
  become: yes
  
  tasks:
    - name: Install MySQL
      package:
        name: mysql-server
        state: present
    
    - name: Start MySQL
      systemd:
        name: mysqld
        state: started
        enabled: yes
    
    - name: Create application database
      mysql_db:
        name: webapp_db
        state: present
        login_unix_socket: /var/lib/mysql/mysql.sock
    
    - name: Create application user
      mysql_user:
        name: webapp_user
        password: "{{ vault_db_password }}"
        priv: 'webapp_db.*:ALL'
        state: present
        login_unix_socket: /var/lib/mysql/mysql.sock
"""

    @staticmethod
    def get_ansible_core_2_12_playbook() -> str:
        """Modern ansible-core 2.12+ style playbook."""
        return """---
- name: Modern web application deployment
  hosts: webservers
  become: true
  gather_facts: true
  
  vars:
    app_name: modern_webapp
    app_version: "2.1.0"
    web_packages:
      - nginx
      - python3
      - python3-pip
      - python3-venv
  
  pre_tasks:
    - name: Update package cache
      package:
        update_cache: yes
      when: ansible_os_family == "Debian"
    
    - name: Ensure system is up to date
      package:
        name: "*"
        state: latest
      when: update_system | default(false)
  
  tasks:
    - name: Install web server packages
      package:
        name: "{{ web_packages }}"
        state: present
    
    - name: Create application user
      user:
        name: "{{ app_name }}"
        system: yes
        shell: /bin/bash
        home: "/opt/{{ app_name }}"
        create_home: yes
    
    - name: Create application directories
      file:
        path: "{{ item }}"
        state: directory
        owner: "{{ app_name }}"
        group: "{{ app_name }}"
        mode: '0755'
      loop:
        - "/opt/{{ app_name }}/app"
        - "/opt/{{ app_name }}/logs"
        - "/opt/{{ app_name }}/config"
        - "/var/log/{{ app_name }}"
    
    - name: Install Python dependencies
      pip:
        requirements: "/opt/{{ app_name }}/requirements.txt"
        virtualenv: "/opt/{{ app_name }}/venv"
        virtualenv_command: python3 -m venv
      become_user: "{{ app_name }}"
    
    - name: Configure Nginx
      template:
        src: "{{ app_name }}.nginx.conf.j2"
        dest: "/etc/nginx/sites-available/{{ app_name }}"
        owner: root
        group: root
        mode: '0644'
      notify:
        - restart nginx
        - reload nginx
    
    - name: Enable Nginx site
      file:
        src: "/etc/nginx/sites-available/{{ app_name }}"
        dest: "/etc/nginx/sites-enabled/{{ app_name }}"
        state: link
      notify: reload nginx
    
    - name: Configure systemd service
      template:
        src: "{{ app_name }}.service.j2"
        dest: "/etc/systemd/system/{{ app_name }}.service"
        owner: root
        group: root
        mode: '0644'
      notify:
        - reload systemd
        - restart app service
    
    - name: Start and enable services
      systemd:
        name: "{{ item }}"
        state: started
        enabled: yes
        daemon_reload: yes
      loop:
        - nginx
        - "{{ app_name }}"
    
    - name: Configure log rotation
      template:
        src: "{{ app_name }}.logrotate.j2"
        dest: "/etc/logrotate.d/{{ app_name }}"
        owner: root
        group: root
        mode: '0644'
    
    - name: Set up monitoring
      block:
        - name: Install monitoring agent
          package:
            name: prometheus-node-exporter
            state: present
        
        - name: Configure monitoring
          template:
            src: node-exporter.service.j2
            dest: /etc/systemd/system/node-exporter.service
            owner: root
            group: root
            mode: '0644'
          notify: restart node-exporter
        
        - name: Start monitoring
          systemd:
            name: node-exporter
            state: started
            enabled: yes
      when: enable_monitoring | default(true)
  
  post_tasks:
    - name: Verify application is running
      uri:
        url: "http://{{ ansible_default_ipv4.address }}/health"
        method: GET
        status_code: 200
      delegate_to: localhost
      retries: 3
      delay: 10
    
    - name: Set deployment facts
      set_fact:
        deployment_timestamp: "{{ ansible_date_time.iso8601 }}"
        deployment_version: "{{ app_version }}"
        deployment_success: true
  
  handlers:
    - name: restart nginx
      systemd:
        name: nginx
        state: restarted
    
    - name: reload nginx
      systemd:
        name: nginx
        state: reloaded
    
    - name: reload systemd
      systemd:
        daemon_reload: yes
    
    - name: restart app service
      systemd:
        name: "{{ app_name }}"
        state: restarted
    
    - name: restart node-exporter
      systemd:
        name: node-exporter
        state: restarted

- name: Database configuration
  hosts: databases
  become: true
  
  vars:
    db_name: "{{ app_name }}_db"
    db_user: "{{ app_name }}_user"
  
  tasks:
    - name: Install PostgreSQL
      package:
        name:
          - postgresql
          - postgresql-contrib
          - python3-psycopg2
        state: present
    
    - name: Start PostgreSQL
      systemd:
        name: postgresql
        state: started
        enabled: yes
    
    - name: Create application database
      postgresql_db:
        name: "{{ db_name }}"
        state: present
      become_user: postgres
    
    - name: Create application user
      postgresql_user:
        name: "{{ db_user }}"
        password: "{{ vault_db_password }}"
        db: "{{ db_name }}"
        priv: ALL
        state: present
      become_user: postgres
    
    - name: Configure PostgreSQL
      template:
        src: postgresql.conf.j2
        dest: /etc/postgresql/13/main/postgresql.conf
        owner: postgres
        group: postgres
        mode: '0644'
        backup: yes
      notify: restart postgresql
    
    - name: Configure pg_hba
      template:
        src: pg_hba.conf.j2
        dest: /etc/postgresql/13/main/pg_hba.conf
        owner: postgres
        group: postgres
        mode: '0640'
        backup: yes
      notify: restart postgresql
  
  handlers:
    - name: restart postgresql
      systemd:
        name: postgresql
        state: restarted
"""

    @staticmethod
    def get_collections_playbook() -> str:
        """Playbook using various Ansible collections."""
        return """---
- name: Collections compatibility test
  hosts: all
  become: yes
  
  tasks:
    # Builtin modules (should be converted)
    - name: Install packages
      package:
        name: "{{ item }}"
        state: present
      loop:
        - docker.io
        - python3-pip
    
    - name: Start Docker service
      service:
        name: docker
        state: started
        enabled: yes
    
    - name: Create directories
      file:
        path: "{{ item }}"
        state: directory
        mode: '0755'
      loop:
        - /opt/app
        - /var/log/app
    
    # Community collections (already FQCN - should remain unchanged)
    - name: Create Docker network
      community.docker.docker_network:
        name: app_network
        driver: bridge
    
    - name: Run application container
      community.docker.docker_container:
        name: app
        image: nginx:latest
        state: started
        networks:
          - name: app_network
        ports:
          - "80:80"
    
    - name: Configure firewall
      ansible.posix.firewalld:
        service: http
        permanent: yes
        state: enabled
        immediate: yes
    
    # Mix of short names and FQCN
    - name: Copy configuration (short name)
      copy:
        src: app.conf
        dest: /opt/app/app.conf
        owner: root
        group: root
        mode: '0644'
    
    - name: Template file (short name)
      template:
        src: config.j2
        dest: /opt/app/config.yml
        owner: root
        group: root
        mode: '0644'
    
    # Already FQCN community modules
    - name: Manage MySQL database
      community.mysql.mysql_db:
        name: app_db
        state: present
    
    - name: Create MySQL user
      community.mysql.mysql_user:
        name: app_user
        password: secret
        priv: 'app_db.*:ALL'
        state: present
    
    # Short names that should be converted
    - name: Create cron job
      cron:
        name: "app backup"
        minute: "0"
        hour: "2"
        job: "/opt/app/backup.sh"
    
    - name: Set facts
      set_fact:
        app_configured: true
        config_timestamp: "{{ ansible_date_time.iso8601 }}"
"""

    @staticmethod
    def get_legacy_syntax_variations() -> dict:
        """Various legacy syntax patterns that should be converted."""
        return {
            "key_value_syntax": """---
- hosts: all
  tasks:
    - name: legacy key=value syntax
      yum: name=httpd state=present
    - service: name=httpd state=started enabled=yes
    - copy: src=file.txt dest=/tmp/file.txt mode=0644
""",
            "with_items_syntax": """---
- hosts: all
  tasks:
    - name: with_items syntax
      package: name={{ item }} state=present
      with_items:
        - nginx
        - php
        - mysql-client
    
    - name: with_dict syntax
      user: name={{ item.key }} group={{ item.value }}
      with_dict:
        alice: admin
        bob: users
""",
            "sudo_syntax": """---
- hosts: all
  sudo: yes
  sudo_user: root
  
  tasks:
    - name: old sudo syntax
      package: name=vim state=present
    - service: name=sshd state=restarted
""",
            "bare_variables": """---
- hosts: all
  vars:
    packages: [nginx, php, mysql-client]
  
  tasks:
    - yum: name={{ packages }} state=present
    - service: name=nginx state=started
""",
        }


class TestAnsibleVersionCompatibility:
    """Test compatibility across different Ansible versions."""

    def test_ansible_2_9_compatibility(self, temp_dir):
        """Test conversion of Ansible 2.9 style playbooks."""
        converter = FQCNConverter()

        playbook_file = temp_dir / "ansible_2_9.yml"
        playbook_file.write_text(AnsibleVersionTestData.get_ansible_2_9_playbook())

        result = converter.convert_file(playbook_file, dry_run=False)

        assert result.success is True
        assert result.changes_made > 0

        converted_content = playbook_file.read_text()

        # Verify key conversions
        expected_conversions = [
            "ansible.builtin.yum:",
            "ansible.builtin.copy:",
            "ansible.builtin.service:",
            "ansible.builtin.user:",
            "ansible.builtin.file:",
            "ansible.builtin.command:",
            "community.mysql.mysql_db:",
            "community.mysql.mysql_user:",
        ]

        for conversion in expected_conversions:
            assert conversion in converted_content, f"Missing conversion: {conversion}"

        # Verify FQCN conversion occurred (syntax modernization is separate concern)
        assert "ansible.builtin.yum: update_cache=" in converted_content
        assert "ansible.builtin.yum: name=" in converted_content
        assert "ansible.builtin.service: name=" in converted_content
        assert "ansible.builtin.copy: src=" in converted_content

    def test_ansible_2_10_compatibility(self, temp_dir):
        """Test conversion of Ansible 2.10 style playbooks."""
        converter = FQCNConverter()

        playbook_file = temp_dir / "ansible_2_10.yml"
        playbook_file.write_text(AnsibleVersionTestData.get_ansible_2_10_playbook())

        result = converter.convert_file(playbook_file, dry_run=False)

        assert result.success is True
        assert result.changes_made > 0

        converted_content = playbook_file.read_text()

        # Verify conversions
        expected_conversions = [
            "ansible.builtin.package:",
            "ansible.builtin.template:",
            "ansible.builtin.systemd:",
            "ansible.builtin.file:",
            "ansible.builtin.command:",
            "community.general.sefcontext:",
            "ansible.posix.firewalld:",
            "community.mysql.mysql_db:",
            "community.mysql.mysql_user:",
        ]

        for conversion in expected_conversions:
            assert conversion in converted_content, f"Missing conversion: {conversion}"

    def test_ansible_core_2_12_compatibility(self, temp_dir):
        """Test conversion of modern ansible-core playbooks."""
        converter = FQCNConverter()

        playbook_file = temp_dir / "ansible_core_2_12.yml"
        playbook_file.write_text(
            AnsibleVersionTestData.get_ansible_core_2_12_playbook()
        )

        result = converter.convert_file(playbook_file, dry_run=False)

        assert result.success is True
        assert result.changes_made > 0

        converted_content = playbook_file.read_text()

        # Verify modern module conversions
        expected_conversions = [
            "ansible.builtin.package:",
            "ansible.builtin.user:",
            "ansible.builtin.file:",
            "ansible.builtin.pip:",
            "ansible.builtin.template:",
            "ansible.builtin.systemd:",
            "ansible.builtin.uri:",
            "ansible.builtin.set_fact:",
            "community.postgresql.postgresql_db:",
            "community.postgresql.postgresql_user:",
        ]

        for conversion in expected_conversions:
            assert conversion in converted_content, f"Missing conversion: {conversion}"

    def test_collections_compatibility(self, temp_dir):
        """Test compatibility with Ansible collections format."""
        converter = FQCNConverter()

        playbook_file = temp_dir / "collections_test.yml"
        playbook_file.write_text(AnsibleVersionTestData.get_collections_playbook())

        result = converter.convert_file(playbook_file, dry_run=False)

        assert result.success is True
        assert result.changes_made > 0

        converted_content = playbook_file.read_text()

        # Short names should be converted
        builtin_conversions = [
            "ansible.builtin.package:",
            "ansible.builtin.service:",
            "ansible.builtin.file:",
            "ansible.builtin.copy:",
            "ansible.builtin.template:",
            "ansible.builtin.cron:",
            "ansible.builtin.set_fact:",
        ]

        for conversion in builtin_conversions:
            assert (
                conversion in converted_content
            ), f"Missing builtin conversion: {conversion}"

        # FQCN modules should remain unchanged
        fqcn_modules = [
            "community.docker.docker_network:",
            "community.docker.docker_container:",
            "ansible.posix.firewalld:",
            "community.mysql.mysql_db:",
            "community.mysql.mysql_user:",
        ]

        for module in fqcn_modules:
            assert module in converted_content, f"FQCN module changed: {module}"

    def test_legacy_syntax_variations(self, temp_dir):
        """Test conversion of various legacy syntax patterns."""
        converter = FQCNConverter()

        legacy_variations = AnsibleVersionTestData.get_legacy_syntax_variations()

        for variation_name, content in legacy_variations.items():
            test_file = temp_dir / f"legacy_{variation_name}.yml"
            test_file.write_text(content)

            result = converter.convert_file(test_file, dry_run=False)

            assert result.success is True, f"Failed to convert {variation_name}"
            assert result.changes_made > 0, f"No changes made for {variation_name}"

            converted_content = test_file.read_text()

            # Verify specific conversions based on variation
            if variation_name == "key_value_syntax":
                assert "ansible.builtin.yum:" in converted_content
                assert "ansible.builtin.service:" in converted_content
                assert "ansible.builtin.copy:" in converted_content
                assert "ansible.builtin.yum: name=" in converted_content

            elif variation_name == "with_items_syntax":
                assert "ansible.builtin.package:" in converted_content
                assert "ansible.builtin.user:" in converted_content

            elif variation_name == "sudo_syntax":
                assert "ansible.builtin.package:" in converted_content
                assert "ansible.builtin.service:" in converted_content

            elif variation_name == "bare_variables":
                assert "ansible.builtin.yum:" in converted_content
                assert "ansible.builtin.service:" in converted_content

    def test_mixed_version_compatibility(self, temp_dir):
        """Test handling of mixed version syntax in single playbook."""
        mixed_content = """---
# Mixed syntax from different Ansible versions
- hosts: webservers
  sudo: yes  # Old syntax
  become: yes  # New syntax
  
  tasks:
    # Ansible 2.9 style
    - name: install package old style
      yum: name=httpd state=present
    
    # Ansible 2.10+ style
    - name: Install package new style
      package:
        name: nginx
        state: present
    
    # Already FQCN
    - name: Docker container
      community.docker.docker_container:
        name: web
        image: nginx
        state: started
    
    # Legacy service syntax
    - service: name=httpd state=started enabled=yes
    
    # Modern service syntax
    - name: Start nginx
      systemd:
        name: nginx
        state: started
        enabled: yes
    
    # Mixed file operations
    - copy: src=old.conf dest=/etc/old.conf
    - name: Template new config
      template:
        src: new.conf.j2
        dest: /etc/new.conf
"""

        converter = FQCNConverter()

        mixed_file = temp_dir / "mixed_versions.yml"
        mixed_file.write_text(mixed_content)

        result = converter.convert_file(mixed_file, dry_run=False)

        assert result.success is True
        assert result.changes_made > 0

        converted_content = mixed_file.read_text()

        # All short names should be converted
        expected_conversions = [
            "ansible.builtin.yum:",
            "ansible.builtin.package:",
            "ansible.builtin.service:",
            "ansible.builtin.systemd:",
            "ansible.builtin.copy:",
            "ansible.builtin.template:",
        ]

        for conversion in expected_conversions:
            assert conversion in converted_content

        # FQCN should remain unchanged
        assert "community.docker.docker_container:" in converted_content

        # FQCN conversion should have occurred
        assert "ansible.builtin.yum: name=" in converted_content
        assert "ansible.builtin.service: name=" in converted_content
        assert "ansible.builtin.copy: src=" in converted_content


class TestCollectionCompatibility:
    """Test compatibility with Ansible collections ecosystem."""

    def test_community_collections_preservation(self, temp_dir):
        """Test that community collection modules are preserved."""
        community_modules_content = """---
- name: Community collections test
  hosts: all
  
  tasks:
    # Community.general modules
    - name: Manage timezone
      community.general.timezone:
        name: America/New_York
    
    - name: Configure sudoers
      community.general.sudoers:
        name: webapp
        user: webapp
        commands: ALL
    
    # Community.docker modules
    - name: Docker login
      community.docker.docker_login:
        username: user
        password: pass
        registry: registry.example.com
    
    - name: Docker compose
      community.docker.docker_compose:
        project_src: /opt/app
        state: present
    
    # Community.mysql modules
    - name: MySQL database
      community.mysql.mysql_db:
        name: webapp
        state: present
    
    - name: MySQL replication
      community.mysql.mysql_replication:
        mode: getmaster
    
    # Community.postgresql modules
    - name: PostgreSQL database
      community.postgresql.postgresql_db:
        name: webapp
        state: present
    
    - name: PostgreSQL extension
      community.postgresql.postgresql_ext:
        name: uuid-ossp
        db: webapp
    
    # Ansible.posix modules
    - name: Configure firewall
      ansible.posix.firewalld:
        service: http
        permanent: yes
        state: enabled
    
    - name: Mount filesystem
      ansible.posix.mount:
        path: /mnt/data
        src: /dev/sdb1
        fstype: ext4
        state: mounted
    
    # Mix with builtin modules (should be converted)
    - name: Install packages
      package:
        name: "{{ item }}"
        state: present
      loop:
        - docker.io
        - postgresql-client
    
    - name: Start services
      service:
        name: "{{ item }}"
        state: started
      loop:
        - docker
        - postgresql
"""

        converter = FQCNConverter()

        test_file = temp_dir / "community_collections.yml"
        test_file.write_text(community_modules_content)

        result = converter.convert_file(test_file, dry_run=False)

        assert result.success is True

        converted_content = test_file.read_text()

        # Community collection modules should remain unchanged
        community_modules = [
            "community.general.timezone:",
            "community.general.sudoers:",
            "community.docker.docker_login:",
            "community.docker.docker_compose:",
            "community.mysql.mysql_db:",
            "community.mysql.mysql_replication:",
            "community.postgresql.postgresql_db:",
            "community.postgresql.postgresql_ext:",
            "ansible.posix.firewalld:",
            "ansible.posix.mount:",
        ]

        for module in community_modules:
            assert module in converted_content, f"Community module changed: {module}"

        # Builtin modules should be converted
        assert "ansible.builtin.package:" in converted_content
        assert "ansible.builtin.service:" in converted_content

    def test_custom_collections_handling(self, temp_dir):
        """Test handling of custom/unknown collections."""
        custom_collections_content = """---
- name: Custom collections test
  hosts: all
  
  tasks:
    # Custom collection modules (should remain unchanged)
    - name: Custom module 1
      mycompany.myapp.deploy:
        version: "1.2.3"
        environment: production
    
    - name: Custom module 2
      internal.tools.backup:
        source: /opt/app
        destination: /backup
    
    # Unknown collection (should remain unchanged)
    - name: Unknown collection module
      unknown.collection.module:
        param: value
    
    # Builtin modules mixed in (should be converted)
    - name: Create directory
      file:
        path: /opt/custom
        state: directory
    
    - name: Install package
      package:
        name: custom-tool
        state: present
    
    # Potential false positive (looks like FQCN but isn't)
    - name: Task with dots in name
      command: echo "test.example.com"
    
    - name: Variable with dots
      debug:
        var: ansible_facts.networking.default_ipv4.address
"""

        converter = FQCNConverter()

        test_file = temp_dir / "custom_collections.yml"
        test_file.write_text(custom_collections_content)

        result = converter.convert_file(test_file, dry_run=False)

        assert result.success is True

        converted_content = test_file.read_text()

        # Custom collection modules should remain unchanged
        custom_modules = [
            "mycompany.myapp.deploy:",
            "internal.tools.backup:",
            "unknown.collection.module:",
        ]

        for module in custom_modules:
            assert module in converted_content, f"Custom module changed: {module}"

        # Builtin modules should be converted
        assert "ansible.builtin.file:" in converted_content
        assert "ansible.builtin.package:" in converted_content
        assert "ansible.builtin.command:" in converted_content
        assert "ansible.builtin.debug:" in converted_content

        # Content with dots should not be affected
        assert 'echo "test.example.com"' in converted_content
        assert "ansible_facts.networking.default_ipv4.address" in converted_content
