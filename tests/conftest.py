"""
Pytest configuration and shared fixtures for FQCN Converter tests.

This module provides common fixtures and configuration for all test modules
to ensure consistent test setup and teardown.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_playbook_content():
    """Sample Ansible playbook content for testing."""
    return """---
- name: Test playbook
  hosts: all
  become: yes
  
  vars:
    nginx_port: 80
    user_name: testuser
  
  pre_tasks:
    - name: Update package cache
      package:
        update_cache: yes
  
  tasks:
    - name: Install nginx
      package:
        name: nginx
        state: present
    
    - name: Copy nginx config
      copy:
        src: nginx.conf
        dest: /etc/nginx/nginx.conf
        owner: root
        group: root
        mode: '0644'
      notify: restart nginx
    
    - name: Create nginx user
      user:
        name: nginx
        system: yes
        shell: /bin/false
        home: /var/lib/nginx
        create_home: no
    
    - name: Start and enable nginx
      service:
        name: nginx
        state: started
        enabled: yes
    
    - name: Debug message
      debug:
        msg: "Nginx installation completed"
  
  handlers:
    - name: restart nginx
      service:
        name: nginx
        state: restarted
  
  post_tasks:
    - name: Set deployment fact
      set_fact:
        deployment_complete: true
        deployment_time: "{{ ansible_date_time.iso8601 }}"
"""


@pytest.fixture
def sample_task_file_content():
    """Sample Ansible task file content for testing."""
    return """---
- name: Create application directory
  file:
    path: /opt/myapp
    state: directory
    owner: root
    group: root
    mode: '0755'

- name: Template application config
  template:
    src: app.conf.j2
    dest: /opt/myapp/app.conf
    owner: myapp
    group: myapp
    mode: '0640'

- name: Install application packages
  package:
    name: "{{ item }}"
    state: present
  loop:
    - python3
    - python3-pip
    - python3-venv

- name: Run application setup command
  command: /opt/myapp/setup.sh
  args:
    creates: /opt/myapp/.setup_complete

- name: Create systemd service file
  copy:
    content: |
      [Unit]
      Description=My Application
      After=network.target
      
      [Service]
      Type=simple
      User=myapp
      Group=myapp
      ExecStart=/opt/myapp/start.sh
      Restart=always
      
      [Install]
      WantedBy=multi-user.target
    dest: /etc/systemd/system/myapp.service
    owner: root
    group: root
    mode: '0644'
  notify: reload systemd

- name: Enable and start myapp service
  service:
    name: myapp
    enabled: yes
    state: started
"""


@pytest.fixture
def sample_converted_content():
    """Sample converted Ansible content for validation testing."""
    return """---
- name: Test playbook
  hosts: all
  tasks:
    - name: Copy file
      ansible.builtin.copy:
        src: test.txt
        dest: /tmp/test.txt
    
    - name: Start service
      ansible.builtin.service:
        name: nginx
        state: started
    
    - name: Create user
      ansible.builtin.user:
        name: testuser
        state: present
"""


@pytest.fixture
def sample_fqcn_mappings():
    """Sample FQCN mappings for testing."""
    return {
        # Ansible builtin modules
        "copy": "ansible.builtin.copy",
        "file": "ansible.builtin.file",
        "template": "ansible.builtin.template",
        "service": "ansible.builtin.service",
        "systemd": "ansible.builtin.systemd",
        "user": "ansible.builtin.user",
        "group": "ansible.builtin.group",
        "package": "ansible.builtin.package",
        "apt": "ansible.builtin.apt",
        "yum": "ansible.builtin.yum",
        "command": "ansible.builtin.command",
        "shell": "ansible.builtin.shell",
        "debug": "ansible.builtin.debug",
        "set_fact": "ansible.builtin.set_fact",
        "include_tasks": "ansible.builtin.include_tasks",
        "import_tasks": "ansible.builtin.import_tasks",
        "mount": "ansible.builtin.mount",
        "cron": "ansible.builtin.cron",
        "lineinfile": "ansible.builtin.lineinfile",
        "replace": "ansible.builtin.replace",
        # Community modules
        "docker_container": "community.docker.docker_container",
        "docker_image": "community.docker.docker_image",
        "mysql_user": "community.mysql.mysql_user",
        "mysql_db": "community.mysql.mysql_db",
        "postgresql_user": "community.postgresql.postgresql_user",
        "postgresql_db": "community.postgresql.postgresql_db",
        "git": "ansible.builtin.git",
        "unarchive": "ansible.builtin.unarchive",
    }


@pytest.fixture
def mock_config_manager(sample_fqcn_mappings):
    """Mock ConfigurationManager for testing."""
    with patch("fqcn_converter.config.manager.ConfigurationManager") as mock_class:
        mock_instance = Mock()
        mock_instance.load_default_mappings.return_value = sample_fqcn_mappings
        mock_instance.load_custom_mappings.return_value = {}
        mock_instance.merge_mappings.return_value = sample_fqcn_mappings
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def ansible_project_structure(temp_dir):
    """Create a complete Ansible project structure for testing."""
    project_dir = temp_dir / "test_project"

    # Create directory structure
    (project_dir / "group_vars").mkdir(parents=True)
    (project_dir / "host_vars").mkdir(parents=True)
    (project_dir / "roles" / "nginx" / "tasks").mkdir(parents=True)
    (project_dir / "roles" / "nginx" / "handlers").mkdir(parents=True)
    (project_dir / "roles" / "nginx" / "templates").mkdir(parents=True)
    (project_dir / "roles" / "nginx" / "vars").mkdir(parents=True)
    (project_dir / "roles" / "nginx" / "defaults").mkdir(parents=True)

    # Create playbook files
    (project_dir / "site.yml").write_text(
        """---
- name: Main site playbook
  hosts: all
  roles:
    - nginx
"""
    )

    (project_dir / "webservers.yml").write_text(
        """---
- name: Configure web servers
  hosts: webservers
  tasks:
    - name: Install nginx
      package:
        name: nginx
        state: present
"""
    )

    # Create role files
    (project_dir / "roles" / "nginx" / "tasks" / "main.yml").write_text(
        """---
- name: Install nginx
  package:
    name: nginx
    state: present

- name: Start nginx
  service:
    name: nginx
    state: started
"""
    )

    (project_dir / "roles" / "nginx" / "handlers" / "main.yml").write_text(
        """---
- name: restart nginx
  service:
    name: nginx
    state: restarted
"""
    )

    # Create inventory
    (project_dir / "inventory.ini").write_text(
        """[webservers]
web1.example.com
web2.example.com

[databases]
db1.example.com
"""
    )

    return project_dir


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration after each test."""
    yield
    # Reset logging to avoid interference between tests
    import logging

    logging.getLogger().handlers.clear()
    logging.getLogger().setLevel(logging.WARNING)


@pytest.fixture
def cli_args():
    """Factory fixture for creating CLI argument objects."""

    def _create_args(**kwargs):
        """Create an argparse.Namespace object with default CLI arguments."""
        defaults = {
            "verbosity": "normal",
            "files": ["test.yml"],
            "config": None,
            "dry_run": False,
            "backup": False,
            "no_backup": False,
            "progress": False,
            "report": None,
            "skip_validation": False,
            "lint": False,
            "force": False,
            "exclude": None,
        }
        defaults.update(kwargs)

        from argparse import Namespace

        return Namespace(**defaults)

    return _create_args
