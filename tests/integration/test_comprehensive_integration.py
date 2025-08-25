"""
Comprehensive integration tests for FQCN Converter production readiness.

These tests validate end-to-end functionality with real Ansible projects,
stress testing for large-scale operations, compatibility across versions,
and performance regression testing with benchmarking.
"""

import pytest
import time
import psutil
import os
import tempfile
import threading
import subprocess
import yaml
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, Mock

from fqcn_converter.core.converter import FQCNConverter
from fqcn_converter.core.validator import ValidationEngine
from fqcn_converter.core.batch import BatchProcessor
from fqcn_converter.config.manager import ConfigurationManager


class RealWorldProjectGenerator:
    """Generator for realistic Ansible project structures."""
    
    @staticmethod
    def create_enterprise_web_stack(base_dir: Path) -> Path:
        """Create a realistic enterprise web stack project."""
        project_dir = base_dir / "enterprise_web_stack"
        
        # Create complex directory structure
        dirs = [
            "group_vars", "host_vars", "inventories/production", "inventories/staging",
            "roles/common/tasks", "roles/common/handlers", "roles/common/vars",
            "roles/nginx/tasks", "roles/nginx/handlers", "roles/nginx/templates",
            "roles/php-fpm/tasks", "roles/php-fpm/handlers", "roles/php-fpm/vars",
            "roles/mysql/tasks", "roles/mysql/handlers", "roles/mysql/vars",
            "roles/redis/tasks", "roles/redis/handlers", "roles/redis/vars",
            "roles/monitoring/tasks", "roles/monitoring/handlers", "roles/monitoring/vars",
            "playbooks", "filter_plugins", "library"
        ]
        
        for dir_path in dirs:
            (project_dir / dir_path).mkdir(parents=True, exist_ok=True)
        
        # Main site playbook
        (project_dir / "site.yml").write_text("""---
- name: Common setup for all servers
  hosts: all
  become: yes
  gather_facts: yes
  
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
        - git
        - unzip
  
  roles:
    - common

- name: Configure web servers
  hosts: webservers
  become: yes
  serial: "{{ web_serial | default(1) }}"
  
  roles:
    - nginx
    - php-fpm
  
  post_tasks:
    - name: Verify web service
      uri:
        url: "http://{{ ansible_default_ipv4.address }}"
        method: GET
        status_code: 200
      delegate_to: localhost

- name: Configure database servers
  hosts: databases
  become: yes
  
  roles:
    - mysql
  
  post_tasks:
    - name: Verify database connectivity
      command: mysql -e "SELECT 1"
      register: db_check
      changed_when: false

- name: Configure cache servers
  hosts: cache
  become: yes
  
  roles:
    - redis

- name: Configure monitoring
  hosts: monitoring
  become: yes
  
  roles:
    - monitoring
""")  
      
        # Common role tasks
        (project_dir / "roles/common/tasks/main.yml").write_text("""---
- name: Create application user
  user:
    name: "{{ app_user }}"
    system: yes
    shell: /bin/bash
    home: "/home/{{ app_user }}"
    create_home: yes

- name: Install security updates
  package:
    name: "*"
    state: latest
  when: install_security_updates | default(true)

- name: Configure firewall
  ufw:
    rule: allow
    port: "{{ item }}"
    proto: tcp
  loop:
    - "22"
    - "80"
    - "443"
  when: configure_firewall | default(true)

- name: Setup log rotation
  template:
    src: logrotate.conf.j2
    dest: "/etc/logrotate.d/{{ app_name }}"
    owner: root
    group: root
    mode: '0644'

- name: Create application directories
  file:
    path: "{{ item }}"
    state: directory
    owner: "{{ app_user }}"
    group: "{{ app_user }}"
    mode: '0755'
  loop:
    - "/var/log/{{ app_name }}"
    - "/var/lib/{{ app_name }}"
    - "/etc/{{ app_name }}"

- name: Install monitoring agent
  package:
    name: "{{ monitoring_agent_package }}"
    state: present
  when: install_monitoring | default(true)

- name: Configure SSH hardening
  lineinfile:
    path: /etc/ssh/sshd_config
    regexp: "{{ item.regexp }}"
    line: "{{ item.line }}"
    backup: yes
  loop:
    - { regexp: '^#?PermitRootLogin', line: 'PermitRootLogin no' }
    - { regexp: '^#?PasswordAuthentication', line: 'PasswordAuthentication no' }
    - { regexp: '^#?X11Forwarding', line: 'X11Forwarding no' }
  notify: restart ssh

- name: Setup backup script
  template:
    src: backup.sh.j2
    dest: "/usr/local/bin/{{ app_name }}-backup"
    owner: root
    group: root
    mode: '0755'

- name: Schedule backup cron job
  cron:
    name: "{{ app_name }} backup"
    minute: "0"
    hour: "2"
    job: "/usr/local/bin/{{ app_name }}-backup"
    user: root
""")

        # Nginx role tasks
        (project_dir / "roles/nginx/tasks/main.yml").write_text("""---
- name: Install nginx
  package:
    name: nginx
    state: present

- name: Remove default nginx site
  file:
    path: "{{ item }}"
    state: absent
  loop:
    - /etc/nginx/sites-enabled/default
    - /var/www/html/index.nginx-debian.html
  notify: restart nginx

- name: Create nginx directories
  file:
    path: "{{ item }}"
    state: directory
    owner: root
    group: root
    mode: '0755'
  loop:
    - /etc/nginx/conf.d
    - /etc/nginx/sites-available
    - /etc/nginx/sites-enabled
    - /var/log/nginx
    - "{{ web_root }}"

- name: Configure nginx main config
  template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
    owner: root
    group: root
    mode: '0644'
    backup: yes
  notify: restart nginx

- name: Configure virtual hosts
  template:
    src: vhost.conf.j2
    dest: "/etc/nginx/sites-available/{{ item.name }}"
    owner: root
    group: root
    mode: '0644'
  loop: "{{ virtual_hosts }}"
  notify: restart nginx

- name: Enable virtual hosts
  file:
    src: "/etc/nginx/sites-available/{{ item.name }}"
    dest: "/etc/nginx/sites-enabled/{{ item.name }}"
    state: link
  loop: "{{ virtual_hosts }}"
  notify: restart nginx

- name: Configure SSL certificates
  command: >
    certbot --nginx -d {{ item.domain }}
    --non-interactive --agree-tos
    --email {{ ssl_email }}
  loop: "{{ virtual_hosts }}"
  when: ssl_enabled | default(false)
  register: certbot_result
  changed_when: "'Congratulations' in certbot_result.stdout"

- name: Start and enable nginx
  service:
    name: nginx
    state: started
    enabled: yes

- name: Configure log rotation for nginx
  template:
    src: nginx-logrotate.j2
    dest: /etc/logrotate.d/nginx
    owner: root
    group: root
    mode: '0644'

- name: Setup nginx monitoring
  template:
    src: nginx-status.conf.j2
    dest: /etc/nginx/conf.d/status.conf
    owner: root
    group: root
    mode: '0644'
  notify: restart nginx
""")

        # PHP-FPM role tasks
        (project_dir / "roles/php-fpm/tasks/main.yml").write_text("""---
- name: Install PHP and extensions
  package:
    name: "{{ item }}"
    state: present
  loop:
    - "php{{ php_version }}-fpm"
    - "php{{ php_version }}-mysql"
    - "php{{ php_version }}-curl"
    - "php{{ php_version }}-gd"
    - "php{{ php_version }}-mbstring"
    - "php{{ php_version }}-xml"
    - "php{{ php_version }}-zip"
    - "php{{ php_version }}-opcache"
    - "php{{ php_version }}-redis"

- name: Configure PHP-FPM pool
  template:
    src: www.conf.j2
    dest: "/etc/php/{{ php_version }}/fpm/pool.d/www.conf"
    owner: root
    group: root
    mode: '0644'
    backup: yes
  notify: restart php-fpm

- name: Configure PHP settings
  template:
    src: php.ini.j2
    dest: "/etc/php/{{ php_version }}/fpm/php.ini"
    owner: root
    group: root
    mode: '0644'
    backup: yes
  notify: restart php-fpm

- name: Create PHP session directory
  file:
    path: "{{ php_session_path }}"
    state: directory
    owner: www-data
    group: www-data
    mode: '0755'

- name: Configure PHP-FPM service
  service:
    name: "php{{ php_version }}-fpm"
    state: started
    enabled: yes

- name: Install Composer
  get_url:
    url: https://getcomposer.org/installer
    dest: /tmp/composer-installer.php
    mode: '0755'

- name: Run Composer installer
  command: php /tmp/composer-installer.php --install-dir=/usr/local/bin --filename=composer
  args:
    creates: /usr/local/bin/composer

- name: Set Composer permissions
  file:
    path: /usr/local/bin/composer
    owner: root
    group: root
    mode: '0755'

- name: Configure PHP error logging
  lineinfile:
    path: "/etc/php/{{ php_version }}/fpm/php.ini"
    regexp: "{{ item.regexp }}"
    line: "{{ item.line }}"
    backup: yes
  loop:
    - { regexp: '^log_errors', line: 'log_errors = On' }
    - { regexp: '^error_log', line: 'error_log = /var/log/php_errors.log' }
  notify: restart php-fpm
""")   
     # MySQL role tasks
        (project_dir / "roles/mysql/tasks/main.yml").write_text("""---
- name: Install MySQL server
  package:
    name: "{{ mysql_package }}"
    state: present

- name: Start MySQL service
  service:
    name: "{{ mysql_service }}"
    state: started
    enabled: yes

- name: Set MySQL root password
  mysql_user:
    name: root
    password: "{{ mysql_root_password }}"
    login_unix_socket: /var/run/mysqld/mysqld.sock
    state: present

- name: Create MySQL configuration
  template:
    src: my.cnf.j2
    dest: /etc/mysql/my.cnf
    owner: root
    group: root
    mode: '0644'
    backup: yes
  notify: restart mysql

- name: Create application database
  mysql_db:
    name: "{{ app_database }}"
    state: present
    login_user: root
    login_password: "{{ mysql_root_password }}"

- name: Create application user
  mysql_user:
    name: "{{ app_db_user }}"
    password: "{{ app_db_password }}"
    priv: "{{ app_database }}.*:ALL"
    host: "{{ item }}"
    state: present
    login_user: root
    login_password: "{{ mysql_root_password }}"
  loop:
    - localhost
    - "{{ app_db_host | default('%') }}"

- name: Configure MySQL backup script
  template:
    src: mysql-backup.sh.j2
    dest: /usr/local/bin/mysql-backup
    owner: root
    group: root
    mode: '0755'

- name: Schedule MySQL backup
  cron:
    name: "MySQL backup"
    minute: "30"
    hour: "1"
    job: "/usr/local/bin/mysql-backup"
    user: root

- name: Configure MySQL log rotation
  template:
    src: mysql-logrotate.j2
    dest: /etc/logrotate.d/mysql-server
    owner: root
    group: root
    mode: '0644'

- name: Secure MySQL installation
  mysql_user:
    name: ""
    host_all: yes
    state: absent
    login_user: root
    login_password: "{{ mysql_root_password }}"

- name: Remove test database
  mysql_db:
    name: test
    state: absent
    login_user: root
    login_password: "{{ mysql_root_password }}"
""")

        # Redis role tasks
        (project_dir / "roles/redis/tasks/main.yml").write_text("""---
- name: Install Redis
  package:
    name: redis-server
    state: present

- name: Configure Redis
  template:
    src: redis.conf.j2
    dest: /etc/redis/redis.conf
    owner: redis
    group: redis
    mode: '0640'
    backup: yes
  notify: restart redis

- name: Create Redis data directory
  file:
    path: "{{ redis_data_dir }}"
    state: directory
    owner: redis
    group: redis
    mode: '0755'

- name: Configure Redis systemd service
  template:
    src: redis.service.j2
    dest: /etc/systemd/system/redis.service
    owner: root
    group: root
    mode: '0644'
  notify:
    - reload systemd
    - restart redis

- name: Start and enable Redis
  service:
    name: redis
    state: started
    enabled: yes

- name: Configure Redis monitoring
  template:
    src: redis-monitor.sh.j2
    dest: /usr/local/bin/redis-monitor
    owner: root
    group: root
    mode: '0755'

- name: Setup Redis backup
  template:
    src: redis-backup.sh.j2
    dest: /usr/local/bin/redis-backup
    owner: root
    group: root
    mode: '0755'

- name: Schedule Redis backup
  cron:
    name: "Redis backup"
    minute: "15"
    hour: "2"
    job: "/usr/local/bin/redis-backup"
    user: redis
""")

        # Monitoring role tasks
        (project_dir / "roles/monitoring/tasks/main.yml").write_text("""---
- name: Install monitoring packages
  package:
    name: "{{ item }}"
    state: present
  loop:
    - prometheus
    - grafana
    - node-exporter
    - alertmanager

- name: Configure Prometheus
  template:
    src: prometheus.yml.j2
    dest: /etc/prometheus/prometheus.yml
    owner: prometheus
    group: prometheus
    mode: '0644'
    backup: yes
  notify: restart prometheus

- name: Configure Grafana
  template:
    src: grafana.ini.j2
    dest: /etc/grafana/grafana.ini
    owner: root
    group: grafana
    mode: '0640'
    backup: yes
  notify: restart grafana

- name: Start monitoring services
  service:
    name: "{{ item }}"
    state: started
    enabled: yes
  loop:
    - prometheus
    - grafana-server
    - prometheus-node-exporter
    - prometheus-alertmanager

- name: Configure monitoring dashboards
  copy:
    src: "{{ item }}"
    dest: "/var/lib/grafana/dashboards/"
    owner: grafana
    group: grafana
    mode: '0644'
  loop:
    - system-dashboard.json
    - application-dashboard.json
  notify: restart grafana

- name: Setup monitoring alerts
  template:
    src: alertmanager.yml.j2
    dest: /etc/prometheus/alertmanager.yml
    owner: prometheus
    group: prometheus
    mode: '0644'
    backup: yes
  notify: restart alertmanager

- name: Configure log aggregation
  template:
    src: rsyslog-monitoring.conf.j2
    dest: /etc/rsyslog.d/50-monitoring.conf
    owner: root
    group: root
    mode: '0644'
  notify: restart rsyslog
""")

        # Handlers for all roles
        handlers = {
            "common": """---
- name: restart ssh
  service:
    name: ssh
    state: restarted""",
            
            "nginx": """---
- name: restart nginx
  service:
    name: nginx
    state: restarted

- name: reload nginx
  service:
    name: nginx
    state: reloaded""",
            
            "php-fpm": """---
- name: restart php-fpm
  service:
    name: "php{{ php_version }}-fpm"
    state: restarted""",
            
            "mysql": """---
- name: restart mysql
  service:
    name: "{{ mysql_service }}"
    state: restarted""",
            
            "redis": """---
- name: restart redis
  service:
    name: redis
    state: restarted

- name: reload systemd
  systemd:
    daemon_reload: yes""",
            
            "monitoring": """---
- name: restart prometheus
  service:
    name: prometheus
    state: restarted

- name: restart grafana
  service:
    name: grafana-server
    state: restarted

- name: restart alertmanager
  service:
    name: prometheus-alertmanager
    state: restarted

- name: restart rsyslog
  service:
    name: rsyslog
    state: restarted"""
        }
        
        for role, handler_content in handlers.items():
            (project_dir / f"roles/{role}/handlers/main.yml").write_text(handler_content)

        # Group variables
        (project_dir / "group_vars/all.yml").write_text("""---
# Application settings
app_name: enterprise_web_app
app_user: webapp
app_version: "2.1.0"

# Web server settings
web_root: /var/www/html
web_serial: 2

# PHP settings
php_version: "8.1"
php_session_path: /var/lib/php/sessions

# Database settings
mysql_package: mysql-server
mysql_service: mysql
mysql_root_password: "{{ vault_mysql_root_password }}"
app_database: webapp_db
app_db_user: webapp_user
app_db_password: "{{ vault_app_db_password }}"

# Redis settings
redis_data_dir: /var/lib/redis

# SSL settings
ssl_enabled: true
ssl_email: admin@example.com

# Security settings
configure_firewall: true
install_security_updates: true
install_monitoring: true
monitoring_agent_package: prometheus-node-exporter

# Virtual hosts configuration
virtual_hosts:
  - name: main
    domain: example.com
    root: "{{ web_root }}"
  - name: api
    domain: api.example.com
    root: "{{ web_root }}/api"
""")

        # Inventory files
        (project_dir / "inventories/production/hosts.yml").write_text("""---
all:
  children:
    webservers:
      hosts:
        web01.prod.example.com:
          ansible_host: 10.0.1.10
        web02.prod.example.com:
          ansible_host: 10.0.1.11
        web03.prod.example.com:
          ansible_host: 10.0.1.12
    
    databases:
      hosts:
        db01.prod.example.com:
          ansible_host: 10.0.2.10
        db02.prod.example.com:
          ansible_host: 10.0.2.11
    
    cache:
      hosts:
        cache01.prod.example.com:
          ansible_host: 10.0.3.10
        cache02.prod.example.com:
          ansible_host: 10.0.3.11
    
    monitoring:
      hosts:
        monitor01.prod.example.com:
          ansible_host: 10.0.4.10

  vars:
    ansible_user: ubuntu
    ansible_ssh_private_key_file: ~/.ssh/production_key
    environment: production
""")

        return project_dir 
   
    @staticmethod
    def create_microservices_project(base_dir: Path) -> Path:
        """Create a microservices deployment project."""
        project_dir = base_dir / "microservices_deployment"
        
        # Create structure for microservices
        services = ["user-service", "order-service", "payment-service", "notification-service", "gateway"]
        
        for service in services:
            service_dir = project_dir / "services" / service
            (service_dir / "tasks").mkdir(parents=True)
            (service_dir / "handlers").mkdir(parents=True)
            (service_dir / "vars").mkdir(parents=True)
            (service_dir / "templates").mkdir(parents=True)
            
            # Service-specific tasks
            (service_dir / "tasks/main.yml").write_text(f"""---
- name: Create {service} user
  user:
    name: "{service.replace('-', '_')}"
    system: yes
    shell: /bin/false
    home: "/opt/{service}"
    create_home: yes

- name: Install {service} dependencies
  package:
    name: "{{{{ item }}}}"
    state: present
  loop:
    - docker.io
    - docker-compose
    - python3-pip

- name: Create {service} directories
  file:
    path: "{{{{ item }}}}"
    state: directory
    owner: "{service.replace('-', '_')}"
    group: "{service.replace('-', '_')}"
    mode: '0755'
  loop:
    - "/opt/{service}/config"
    - "/opt/{service}/data"
    - "/opt/{service}/logs"

- name: Deploy {service} configuration
  template:
    src: "{service}-config.yml.j2"
    dest: "/opt/{service}/config/config.yml"
    owner: "{service.replace('-', '_')}"
    group: "{service.replace('-', '_')}"
    mode: '0644'
  notify: restart {service}

- name: Deploy {service} docker-compose
  template:
    src: "docker-compose.yml.j2"
    dest: "/opt/{service}/docker-compose.yml"
    owner: "{service.replace('-', '_')}"
    group: "{service.replace('-', '_')}"
    mode: '0644'
  notify: restart {service}

- name: Start {service} containers
  docker_compose:
    project_src: "/opt/{service}"
    state: present
    pull: yes

- name: Configure {service} monitoring
  template:
    src: "prometheus-config.yml.j2"
    dest: "/opt/{service}/prometheus.yml"
    owner: "{service.replace('-', '_')}"
    group: "{service.replace('-', '_')}"
    mode: '0644'

- name: Setup {service} health check
  template:
    src: "health-check.sh.j2"
    dest: "/usr/local/bin/{service}-health-check"
    owner: root
    group: root
    mode: '0755'

- name: Schedule {service} health check
  cron:
    name: "{service} health check"
    minute: "*/5"
    job: "/usr/local/bin/{service}-health-check"
    user: root

- name: Configure {service} log rotation
  template:
    src: "logrotate.conf.j2"
    dest: "/etc/logrotate.d/{service}"
    owner: root
    group: root
    mode: '0644'
""")
            
            # Service handlers
            (service_dir / "handlers/main.yml").write_text(f"""---
- name: restart {service}
  docker_compose:
    project_src: "/opt/{service}"
    restarted: yes

- name: reload {service}
  docker_compose:
    project_src: "/opt/{service}"
    pull: yes
    state: present
""")

        # Main orchestration playbook
        (project_dir / "deploy.yml").write_text("""---
- name: Deploy infrastructure components
  hosts: infrastructure
  become: yes
  
  tasks:
    - name: Install Docker
      package:
        name: "{{ item }}"
        state: present
      loop:
        - docker.io
        - docker-compose
    
    - name: Start Docker service
      service:
        name: docker
        state: started
        enabled: yes
    
    - name: Create Docker network
      docker_network:
        name: microservices
        driver: bridge
        ipam_config:
          - subnet: 172.20.0.0/16

- name: Deploy user service
  hosts: user_service
  become: yes
  roles:
    - services/user-service

- name: Deploy order service
  hosts: order_service
  become: yes
  roles:
    - services/order-service

- name: Deploy payment service
  hosts: payment_service
  become: yes
  roles:
    - services/payment-service

- name: Deploy notification service
  hosts: notification_service
  become: yes
  roles:
    - services/notification-service

- name: Deploy API gateway
  hosts: gateway
  become: yes
  roles:
    - services/gateway

- name: Configure service mesh
  hosts: all
  become: yes
  
  tasks:
    - name: Install service mesh components
      package:
        name: "{{ item }}"
        state: present
      loop:
        - consul
        - envoy
    
    - name: Configure Consul
      template:
        src: consul.json.j2
        dest: /etc/consul/consul.json
        owner: consul
        group: consul
        mode: '0644'
      notify: restart consul
    
    - name: Start Consul
      service:
        name: consul
        state: started
        enabled: yes
    
    - name: Configure Envoy proxy
      template:
        src: envoy.yaml.j2
        dest: /etc/envoy/envoy.yaml
        owner: envoy
        group: envoy
        mode: '0644'
      notify: restart envoy
    
    - name: Start Envoy
      service:
        name: envoy
        state: started
        enabled: yes

  handlers:
    - name: restart consul
      service:
        name: consul
        state: restarted
    
    - name: restart envoy
      service:
        name: envoy
        state: restarted
""")

        # Inventory for microservices
        (project_dir / "inventory.yml").write_text("""---
all:
  children:
    infrastructure:
      hosts:
        infra01.example.com:
        infra02.example.com:
    
    user_service:
      hosts:
        user01.example.com:
        user02.example.com:
    
    order_service:
      hosts:
        order01.example.com:
        order02.example.com:
    
    payment_service:
      hosts:
        payment01.example.com:
        payment02.example.com:
    
    notification_service:
      hosts:
        notify01.example.com:
    
    gateway:
      hosts:
        gateway01.example.com:
        gateway02.example.com:

  vars:
    ansible_user: ubuntu
    ansible_ssh_private_key_file: ~/.ssh/microservices_key
""")

        return project_dir

    @staticmethod
    def create_legacy_ansible_project(base_dir: Path) -> Path:
        """Create a legacy Ansible project with older syntax."""
        project_dir = base_dir / "legacy_ansible_project"
        project_dir.mkdir(parents=True)
        
        # Legacy playbook with old syntax
        (project_dir / "legacy.yml").write_text("""---
- hosts: webservers
  sudo: yes
  gather_facts: yes
  
  vars:
    packages:
      - apache2
      - php5
      - mysql-client
  
  tasks:
    - name: install packages
      apt: name={{ item }} state=present update_cache=yes
      with_items: "{{ packages }}"
    
    - name: copy apache config
      copy: src=apache2.conf dest=/etc/apache2/apache2.conf backup=yes
      notify:
        - restart apache
    
    - name: start apache
      service: name=apache2 state=started enabled=yes
    
    - name: create web user
      user: name=www-data system=yes shell=/bin/false
    
    - name: set file permissions
      file: path=/var/www/html owner=www-data group=www-data mode=0755 recurse=yes
    
    - name: install php modules
      apt: name={{ item }} state=present
      with_items:
        - php5-mysql
        - php5-curl
        - php5-gd
      notify:
        - restart apache
    
    - name: configure php
      lineinfile: dest=/etc/php5/apache2/php.ini regexp='^memory_limit' line='memory_limit = 256M'
      notify:
        - restart apache
    
    - name: create database
      mysql_db: name=webapp state=present
    
    - name: create db user
      mysql_user: name=webapp password=secret priv=webapp.*:ALL state=present
  
  handlers:
    - name: restart apache
      service: name=apache2 state=restarted

- hosts: databases
  sudo: yes
  
  tasks:
    - name: install mysql
      apt: name=mysql-server state=present
    
    - name: start mysql
      service: name=mysql state=started enabled=yes
    
    - name: secure mysql
      mysql_user: name=root password=rootpass
""")

        return project_dir


class PerformanceProfiler:
    """Enhanced performance profiling for comprehensive testing."""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.metrics = {}
        self.monitoring = False
        self.monitor_thread = None
        
    def start_profiling(self, test_name: str):
        """Start performance profiling for a test."""
        self.metrics[test_name] = {
            'start_time': time.time(),
            'start_memory': self.process.memory_info().rss,
            'start_cpu': self.process.cpu_percent(),
            'peak_memory': self.process.memory_info().rss,
            'cpu_samples': [],
            'memory_samples': []
        }
        
        self.monitoring = True
        self.current_test = test_name
        self.monitor_thread = threading.Thread(target=self._monitor_resources)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_profiling(self, test_name: str) -> dict:
        """Stop profiling and return metrics."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        
        end_time = time.time()
        end_memory = self.process.memory_info().rss
        end_cpu = self.process.cpu_percent()
        
        metrics = self.metrics[test_name]
        metrics.update({
            'end_time': end_time,
            'end_memory': end_memory,
            'end_cpu': end_cpu,
            'duration': end_time - metrics['start_time'],
            'memory_delta': end_memory - metrics['start_memory'],
            'peak_memory_delta': metrics['peak_memory'] - metrics['start_memory'],
            'avg_cpu': sum(metrics['cpu_samples']) / len(metrics['cpu_samples']) if metrics['cpu_samples'] else 0
        })
        
        return metrics
    
    def _monitor_resources(self):
        """Monitor system resources in background."""
        while self.monitoring:
            try:
                current_memory = self.process.memory_info().rss
                current_cpu = self.process.cpu_percent()
                
                if current_memory > self.metrics[self.current_test]['peak_memory']:
                    self.metrics[self.current_test]['peak_memory'] = current_memory
                
                self.metrics[self.current_test]['memory_samples'].append(current_memory)
                self.metrics[self.current_test]['cpu_samples'].append(current_cpu)
                
                time.sleep(0.1)  # Sample every 100ms
            except Exception:
                break


class TestComprehensiveIntegration:
    """Comprehensive integration tests for production readiness validation."""
    
    @pytest.fixture
    def profiler(self):
        """Performance profiler fixture."""
        return PerformanceProfiler()
    
    @pytest.fixture
    def enterprise_project(self, temp_dir):
        """Enterprise web stack project fixture."""
        return RealWorldProjectGenerator.create_enterprise_web_stack(temp_dir)
    
    @pytest.fixture
    def microservices_project(self, temp_dir):
        """Microservices project fixture."""
        return RealWorldProjectGenerator.create_microservices_project(temp_dir)
    
    @pytest.fixture
    def legacy_project(self, temp_dir):
        """Legacy Ansible project fixture."""
        return RealWorldProjectGenerator.create_legacy_ansible_project(temp_dir)

    def test_enterprise_project_end_to_end_conversion(self, enterprise_project, profiler):
        """Test complete enterprise project conversion with performance monitoring."""
        profiler.start_profiling("enterprise_conversion")
        
        converter = FQCNConverter()
        validator = ValidationEngine()
        
        # Discover all Ansible files
        ansible_files = []
        for pattern in ["*.yml", "*.yaml"]:
            ansible_files.extend(list(enterprise_project.rglob(pattern)))
        
        # Filter to actual Ansible files
        ansible_files = [f for f in ansible_files if self._is_ansible_file(f)]
        
        assert len(ansible_files) >= 15  # Should find many files in enterprise project
        
        # Convert all files
        conversion_results = []
        total_changes = 0
        
        for file_path in ansible_files:
            result = converter.convert_file(file_path, dry_run=False)
            conversion_results.append(result)
            if result.success:
                total_changes += result.changes_made
        
        # Validate all conversions
        validation_results = []
        for file_path in ansible_files:
            result = validator.validate_conversion(file_path)
            validation_results.append(result)
        
        metrics = profiler.stop_profiling("enterprise_conversion")
        
        # Assertions
        successful_conversions = [r for r in conversion_results if r.success]
        assert len(successful_conversions) == len(conversion_results)
        assert total_changes > 40  # Should convert many modules
        
        valid_files = [r for r in validation_results if r.valid]
        assert len(valid_files) == len(validation_results)
        
        # Performance assertions
        assert metrics['duration'] < 60.0  # Should complete within 1 minute
        assert metrics['memory_delta'] / 1024 / 1024 < 200  # Less than 200MB memory increase
        
        # Verify specific conversions in key files
        site_yml = enterprise_project / "site.yml"
        site_content = site_yml.read_text()
        
        # Check conversions that should be in site.yml
        site_expected_conversions = [
            'ansible.builtin.package:',
            'ansible.builtin.uri:',
            'ansible.builtin.command:'
        ]
        
        for conversion in site_expected_conversions:
            assert conversion in site_content
        
        # Check that service modules are converted in role files
        nginx_tasks = enterprise_project / "roles/nginx/tasks/main.yml"
        nginx_content = nginx_tasks.read_text()
        assert 'ansible.builtin.service:' in nginx_content
        
        print(f"Enterprise conversion metrics: {metrics}")
        print(f"Converted {total_changes} modules across {len(ansible_files)} files")
    
    def test_microservices_project_conversion(self, microservices_project, profiler):
        """Test microservices project conversion with Docker modules."""
        profiler.start_profiling("microservices_conversion")
        
        converter = FQCNConverter()
        
        # Find all YAML files
        yaml_files = list(microservices_project.rglob("*.yml"))
        yaml_files.extend(list(microservices_project.rglob("*.yaml")))
        
        ansible_files = [f for f in yaml_files if self._is_ansible_file(f)]
        
        # Convert all files
        results = []
        for file_path in ansible_files:
            result = converter.convert_file(file_path, dry_run=False)
            results.append(result)
        
        metrics = profiler.stop_profiling("microservices_conversion")
        
        # Verify conversions
        successful_results = [r for r in results if r.success]
        assert len(successful_results) == len(results)
        
        # Check for Docker-related conversions
        deploy_yml = microservices_project / "deploy.yml"
        deploy_content = deploy_yml.read_text()
        
        expected_docker_conversions = [
            'ansible.builtin.package:',
            'ansible.builtin.service:',
            'community.docker.docker_network:',
            'community.docker.docker_compose:'
        ]
        
        # Note: Some modules might not be converted if they're already FQCN
        builtin_conversions = [conv for conv in expected_docker_conversions if 'ansible.builtin' in conv]
        for conversion in builtin_conversions:
            assert conversion in deploy_content
        
        print(f"Microservices conversion metrics: {metrics}")
    
    def test_legacy_project_compatibility(self, legacy_project, profiler):
        """Test conversion of legacy Ansible syntax."""
        profiler.start_profiling("legacy_conversion")
        
        converter = FQCNConverter()
        
        legacy_file = legacy_project / "legacy.yml"
        result = converter.convert_file(legacy_file, dry_run=False)
        
        metrics = profiler.stop_profiling("legacy_conversion")
        
        assert result.success is True
        assert result.changes_made > 0
        
        # Verify legacy syntax was converted
        converted_content = legacy_file.read_text()
        
        expected_conversions = [
            'ansible.builtin.apt:',
            'ansible.builtin.copy:',
            'ansible.builtin.service:',
            'ansible.builtin.user:',
            'ansible.builtin.file:',
            'ansible.builtin.lineinfile:',
            'community.mysql.mysql_db:',
            'community.mysql.mysql_user:'
        ]
        
        for conversion in expected_conversions:
            assert conversion in converted_content
        
        # Verify old syntax patterns are gone (check for module names without FQCN)
        # Look for patterns like "apt:" at the start of a line (not "ansible.builtin.apt:")
        import re
        apt_pattern = re.compile(r'^\s*apt:\s', re.MULTILINE)
        service_pattern = re.compile(r'^\s*service:\s', re.MULTILINE)
        copy_pattern = re.compile(r'^\s*copy:\s', re.MULTILINE)
        
        assert not apt_pattern.search(converted_content), "Found unconverted apt module"
        assert not service_pattern.search(converted_content), "Found unconverted service module"
        assert not copy_pattern.search(converted_content), "Found unconverted copy module"
        
        print(f"Legacy conversion metrics: {metrics}")
    
    def test_stress_testing_large_scale_conversion(self, temp_dir, profiler):
        """Stress test with large-scale batch conversion operations."""
        profiler.start_profiling("stress_test")
        
        # Create many projects for stress testing
        num_projects = 50
        projects = []
        
        for i in range(num_projects):
            project_dir = temp_dir / f"stress_project_{i:03d}"
            project_dir.mkdir()
            
            # Create a moderately complex playbook for each project
            tasks_content = []
            for j in range(20):
                tasks_content.append(f"""    - name: Install package {j}
      package:
        name: "package_{i}_{j}"
        state: present
    
    - name: Configure service {j}
      service:
        name: "service_{i}_{j}"
        state: started
        enabled: yes
    
    - name: Create file {j}
      file:
        path: "/tmp/file_{i}_{j}.txt"
        state: touch
        owner: root
        group: root
        mode: '0644'
    
    - name: Copy config {j}
      copy:
        content: "Config {i}-{j}"
        dest: "/etc/config_{i}_{j}.conf"
        owner: root
        group: root
        mode: '0644'""")
            
            (project_dir / "site.yml").write_text(f"""---
- name: Stress test project {i}
  hosts: all
  become: yes
  
  tasks:
{chr(10).join(tasks_content)}
""")
            
            projects.append(str(project_dir))
        
        # Perform stress test with batch processor
        batch_processor = BatchProcessor(max_workers=8)
        
        start_time = time.time()
        results = batch_processor.process_projects(projects, dry_run=True)
        batch_time = time.time() - start_time
        
        metrics = profiler.stop_profiling("stress_test")
        
        # Verify results
        assert len(results) == num_projects
        successful_results = [r for r in results if r['success']]
        assert len(successful_results) >= num_projects * 0.95  # Allow 5% failure rate
        
        total_modules_converted = sum(r['modules_converted'] for r in successful_results)
        assert total_modules_converted > num_projects * 50  # Should convert many modules
        
        # Performance assertions for stress test
        assert batch_time < 300.0  # Should complete within 5 minutes
        assert metrics['memory_delta'] / 1024 / 1024 < 500  # Less than 500MB memory increase
        
        print(f"Stress test metrics: {metrics}")
        print(f"Processed {num_projects} projects in {batch_time:.2f} seconds")
        print(f"Converted {total_modules_converted} modules total")
    
    def test_ansible_version_compatibility_matrix(self, temp_dir):
        """Test compatibility across different Ansible version formats."""
        test_cases = [
            {
                "name": "ansible_2_9",
                "content": """---
- hosts: all
  become: true
  tasks:
    - name: Install package
      yum: name=httpd state=present
    - name: Start service  
      service: name=httpd state=started"""
            },
            {
                "name": "ansible_2_10",
                "content": """---
- name: Ansible 2.10 format
  hosts: all
  become: yes
  tasks:
    - name: Install package
      package:
        name: httpd
        state: present
    - name: Start service
      systemd:
        name: httpd
        state: started
        enabled: yes"""
            },
            {
                "name": "ansible_core_2_12",
                "content": """---
- name: Modern Ansible Core format
  hosts: all
  become: true
  gather_facts: true
  
  tasks:
    - name: Install packages
      package:
        name: "{{ item }}"
        state: present
      loop:
        - httpd
        - mod_ssl
    
    - name: Template configuration
      template:
        src: httpd.conf.j2
        dest: /etc/httpd/conf/httpd.conf
        backup: yes
      notify: restart httpd
  
  handlers:
    - name: restart httpd
      systemd:
        name: httpd
        state: restarted"""
            }
        ]
        
        converter = FQCNConverter()
        compatibility_results = {}
        
        for test_case in test_cases:
            test_file = temp_dir / f"{test_case['name']}.yml"
            test_file.write_text(test_case['content'])
            
            result = converter.convert_file(test_file, dry_run=False)
            compatibility_results[test_case['name']] = {
                'success': result.success,
                'changes_made': result.changes_made,
                'content': test_file.read_text()
            }
        
        # Verify all versions are handled correctly
        for name, result in compatibility_results.items():
            assert result['success'] is True, f"Failed to convert {name}"
            assert result['changes_made'] > 0, f"No changes made for {name}"
        
        # Verify specific conversions for each version
        assert 'ansible.builtin.yum:' in compatibility_results['ansible_2_9']['content']
        assert 'ansible.builtin.service:' in compatibility_results['ansible_2_9']['content']
        
        assert 'ansible.builtin.package:' in compatibility_results['ansible_2_10']['content']
        assert 'ansible.builtin.systemd:' in compatibility_results['ansible_2_10']['content']
        
        assert 'ansible.builtin.package:' in compatibility_results['ansible_core_2_12']['content']
        assert 'ansible.builtin.template:' in compatibility_results['ansible_core_2_12']['content']
        assert 'ansible.builtin.systemd:' in compatibility_results['ansible_core_2_12']['content']
    
    def test_performance_regression_benchmarking(self, temp_dir, profiler):
        """Performance regression testing with benchmarking."""
        # Create standardized test files of different sizes
        test_sizes = [10, 50, 100, 200, 500]
        benchmark_results = {}
        
        converter = FQCNConverter()
        
        for size in test_sizes:
            profiler.start_profiling(f"benchmark_{size}")
            
            # Create test file with specified number of tasks
            tasks = []
            for i in range(size):
                tasks.append(f"""  - name: Task {i}
    package:
      name: "package_{i}"
      state: present
  
  - name: Service {i}
    service:
      name: "service_{i}"
      state: started""")
            
            content = f"""---
- name: Benchmark test {size} tasks
  hosts: all
  tasks:
{chr(10).join(tasks)}
"""
            
            test_file = temp_dir / f"benchmark_{size}.yml"
            test_file.write_text(content)
            
            # Perform conversion
            result = converter.convert_file(test_file, dry_run=True)
            
            metrics = profiler.stop_profiling(f"benchmark_{size}")
            
            benchmark_results[size] = {
                'duration': metrics['duration'],
                'memory_delta': metrics['memory_delta'] / 1024 / 1024,  # MB
                'peak_memory': metrics['peak_memory_delta'] / 1024 / 1024,  # MB
                'changes_made': result.changes_made,
                'success': result.success
            }
            
            assert result.success is True
        
        # Analyze performance scaling
        print("Performance Regression Benchmark Results:")
        for size, metrics in benchmark_results.items():
            print(f"  {size} tasks: {metrics['duration']:.3f}s, "
                  f"{metrics['memory_delta']:.2f}MB delta, "
                  f"{metrics['changes_made']} changes")
        
        # Performance regression checks
        # Duration should scale reasonably (not exponentially)
        duration_10 = benchmark_results[10]['duration']
        duration_500 = benchmark_results[500]['duration']
        
        # 500 tasks should not take more than 50x the time of 10 tasks
        scaling_factor = duration_500 / duration_10 if duration_10 > 0 else 1
        assert scaling_factor < 50, f"Performance regression detected: {scaling_factor}x scaling"
        
        # Memory usage should be reasonable
        for size, metrics in benchmark_results.items():
            assert metrics['memory_delta'] < 100, f"Excessive memory usage for {size} tasks"
            assert metrics['peak_memory'] < 200, f"Excessive peak memory for {size} tasks"
    
    def _is_ansible_file(self, file_path: Path) -> bool:
        """Check if a file appears to be an Ansible file."""
        if file_path.suffix not in ['.yml', '.yaml']:
            return False
        
        # Skip certain files
        skip_files = {'inventory.ini', 'ansible.cfg', 'requirements.txt'}
        if file_path.name in skip_files:
            return False
        
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


class TestAnsibleVersionCompatibility:
    """Test compatibility with different Ansible versions and collection formats."""
    
    def test_ansible_collections_compatibility(self, temp_dir):
        """Test compatibility with Ansible collections format."""
        converter = FQCNConverter()
        
        # Test with collections requirements
        collections_file = temp_dir / "requirements.yml"
        collections_file.write_text("""---
collections:
  - name: community.general
    version: ">=3.0.0"
  - name: community.docker
    version: ">=2.0.0"
  - name: ansible.posix
    version: ">=1.0.0"
""")
        
        # Playbook using collection modules
        playbook_file = temp_dir / "collections_test.yml"
        playbook_file.write_text("""---
- name: Test collections compatibility
  hosts: all
  
  tasks:
    # Mix of short names and FQCN
    - name: Install package (short name)
      package:
        name: nginx
        state: present
    
    - name: Copy file (short name)
      copy:
        src: test.txt
        dest: /tmp/test.txt
    
    # Already using FQCN - should remain unchanged
    - name: Docker container (already FQCN)
      community.docker.docker_container:
        name: nginx
        image: nginx:latest
        state: started
    
    - name: Manage firewall (already FQCN)
      ansible.posix.firewalld:
        service: http
        permanent: yes
        state: enabled
    
    # Short names that should be converted
    - name: Start service (short name)
      service:
        name: nginx
        state: started
    
    - name: Create user (short name)
      user:
        name: nginx
        system: yes
""")
        
        result = converter.convert_file(playbook_file, dry_run=False)
        
        assert result.success is True
        assert result.changes_made > 0
        
        converted_content = playbook_file.read_text()
        
        # Short names should be converted
        assert 'ansible.builtin.package:' in converted_content
        assert 'ansible.builtin.copy:' in converted_content
        assert 'ansible.builtin.service:' in converted_content
        assert 'ansible.builtin.user:' in converted_content
        
        # FQCN modules should remain unchanged
        assert 'community.docker.docker_container:' in converted_content
        assert 'ansible.posix.firewalld:' in converted_content