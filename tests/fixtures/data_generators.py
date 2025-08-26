"""
Data generators for edge case validation and testing.

This module provides generators for creating test data with various
edge cases, boundary conditions, and stress testing scenarios.
"""

import itertools
import random
import string
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple


class PlaybookGenerator:
    """Generator for Ansible playbooks with various characteristics."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize generator with optional random seed."""
        if seed is not None:
            random.seed(seed)

    def generate_simple_playbook(self, num_tasks: int = 5) -> str:
        """Generate a simple playbook with specified number of tasks."""
        modules = [
            "package",
            "service",
            "copy",
            "file",
            "user",
            "group",
            "command",
            "template",
            "debug",
        ]

        tasks = []
        for i in range(num_tasks):
            module = random.choice(modules)
            task_name = f"Task {i + 1} - {module}"

            if module == "package":
                task = f"""  - name: {task_name}
    {module}:
      name: "package_{i}"
      state: present"""
            elif module == "service":
                task = f"""  - name: {task_name}
    {module}:
      name: "service_{i}"
      state: started
      enabled: yes"""
            elif module == "copy":
                task = f"""  - name: {task_name}
    {module}:
      src: "source_{i}.txt"
      dest: "/tmp/dest_{i}.txt"
      mode: '0644'"""
            elif module == "file":
                task = f"""  - name: {task_name}
    {module}:
      path: "/tmp/file_{i}"
      state: touch
      mode: '0644'"""
            elif module == "user":
                task = f"""  - name: {task_name}
    {module}:
      name: "user_{i}"
      state: present
      shell: /bin/bash"""
            elif module == "group":
                task = f"""  - name: {task_name}
    {module}:
      name: "group_{i}"
      state: present"""
            elif module == "command":
                task = f"""  - name: {task_name}
    {module}: "echo 'Command {i}'"
    changed_when: false"""
            elif module == "template":
                task = f"""  - name: {task_name}
    {module}:
      src: "template_{i}.j2"
      dest: "/etc/config_{i}.conf"
      mode: '0644'"""
            elif module == "debug":
                task = f"""  - name: {task_name}
    {module}:
      msg: "Debug message {i}\""""

            tasks.append(task)

        return f"""---
- name: Generated playbook with {num_tasks} tasks
  hosts: all
  become: yes
  
  tasks:
{chr(10).join(tasks)}
"""

    def generate_complex_playbook(
        self, num_plays: int = 3, tasks_per_play: int = 5
    ) -> str:
        """Generate a complex multi-play playbook."""
        plays = []

        for play_num in range(num_plays):
            host_groups = ["webservers", "databases", "loadbalancers", "monitoring"]
            host_group = random.choice(host_groups)

            play = f"""- name: Play {play_num + 1} - {host_group}
  hosts: {host_group}
  become: yes
  gather_facts: yes
  
  vars:
    play_number: {play_num + 1}
    target_group: {host_group}
  
  pre_tasks:
    - name: Pre-task for play {play_num + 1}
      debug:
        msg: "Starting play {{{{ play_number }}}} for {{{{ target_group }}}}"
  
  tasks:
{chr(10).join(self._generate_tasks_for_play(tasks_per_play, play_num))}
  
  post_tasks:
    - name: Post-task for play {play_num + 1}
      debug:
        msg: "Completed play {{{{ play_number }}}} for {{{{ target_group }}}}"
"""
            plays.append(play)

        return f"""---
{chr(10).join(plays)}
"""

    def _generate_tasks_for_play(self, num_tasks: int, play_num: int) -> List[str]:
        """Generate tasks for a specific play."""
        modules = ["package", "service", "copy", "file", "user", "template", "command"]
        tasks = []

        for i in range(num_tasks):
            module = random.choice(modules)
            task = f"""    - name: Play {play_num + 1} Task {i + 1}
      {module}:
        name: "play_{play_num}_item_{i}"
        state: present"""
            tasks.append(task)

        return tasks

    def generate_with_variables(self, complexity: str = "medium") -> str:
        """Generate playbook with various variable complexity levels."""
        if complexity == "simple":
            return self._generate_simple_variables_playbook()
        elif complexity == "medium":
            return self._generate_medium_variables_playbook()
        elif complexity == "complex":
            return self._generate_complex_variables_playbook()
        else:
            raise ValueError("Complexity must be 'simple', 'medium', or 'complex'")

    def _generate_simple_variables_playbook(self) -> str:
        """Generate playbook with simple variables."""
        return """---
- name: Simple variables playbook
  hosts: all
  vars:
    app_name: myapp
    app_version: "1.0.0"
    app_port: 8080
  
  tasks:
    - name: Install application
      package:
        name: "{{ app_name }}"
        state: present
    
    - name: Start application service
      service:
        name: "{{ app_name }}"
        state: started
        enabled: yes
    
    - name: Create config file
      copy:
        content: |
          app_name={{ app_name }}
          app_version={{ app_version }}
          app_port={{ app_port }}
        dest: "/etc/{{ app_name }}/config"
        mode: '0644'
"""

    def _generate_medium_variables_playbook(self) -> str:
        """Generate playbook with medium complexity variables."""
        return """---
- name: Medium complexity variables playbook
  hosts: all
  vars:
    app:
      name: myapp
      version: "1.0.0"
      port: 8080
      user: myapp
      group: myapp
    
    packages:
      - name: nginx
        state: present
      - name: python3
        state: present
      - name: python3-pip
        state: present
    
    services:
      - name: nginx
        enabled: yes
      - name: "{{ app.name }}"
        enabled: yes
  
  tasks:
    - name: Install packages
      package:
        name: "{{ item.name }}"
        state: "{{ item.state }}"
      loop: "{{ packages }}"
    
    - name: Create application user
      user:
        name: "{{ app.user }}"
        group: "{{ app.group }}"
        system: yes
        shell: /bin/false
    
    - name: Create application group
      group:
        name: "{{ app.group }}"
        state: present
    
    - name: Template configuration
      template:
        src: "{{ app.name }}.conf.j2"
        dest: "/etc/{{ app.name }}/{{ app.name }}.conf"
        owner: "{{ app.user }}"
        group: "{{ app.group }}"
        mode: '0640'
    
    - name: Start services
      service:
        name: "{{ item.name }}"
        state: started
        enabled: "{{ item.enabled }}"
      loop: "{{ services }}"
"""

    def _generate_complex_variables_playbook(self) -> str:
        """Generate playbook with complex nested variables."""
        return """---
- name: Complex variables playbook
  hosts: all
  vars:
    environment: production
    
    app_config:
      name: myapp
      version: "{{ app_version | default('1.0.0') }}"
      instances:
        web:
          count: "{{ web_instances | default(2) }}"
          port: 8080
          memory: "{{ web_memory | default('512m') }}"
        worker:
          count: "{{ worker_instances | default(4) }}"
          memory: "{{ worker_memory | default('256m') }}"
      
      database:
        host: "{{ groups['databases'][0] if groups['databases'] is defined else 'localhost' }}"
        port: 5432
        name: "{{ app_config.name }}_{{ environment }}"
        user: "{{ app_config.name }}_user"
        pool_size: "{{ db_pool_size | default(10) }}"
      
      cache:
        enabled: "{{ enable_cache | default(true) }}"
        host: "{{ groups['cache'][0] if groups['cache'] is defined else 'localhost' }}"
        port: 6379
        ttl: "{{ cache_ttl | default(3600) }}"
    
    deployment:
      strategy: "{{ deploy_strategy | default('rolling') }}"
      max_parallel: "{{ max_parallel_deploys | default(1) }}"
      health_check:
        enabled: true
        endpoint: "/health"
        timeout: 30
        retries: 3
  
  tasks:
    - name: Create application directories
      file:
        path: "{{ item }}"
        state: directory
        owner: "{{ app_config.name }}"
        group: "{{ app_config.name }}"
        mode: '0755'
      loop:
        - "/opt/{{ app_config.name }}"
        - "/var/log/{{ app_config.name }}"
        - "/etc/{{ app_config.name }}"
    
    - name: Template complex configuration
      template:
        src: "{{ app_config.name }}.yml.j2"
        dest: "/etc/{{ app_config.name }}/config.yml"
        owner: "{{ app_config.name }}"
        group: "{{ app_config.name }}"
        mode: '0640'
      vars:
        config_data:
          app: "{{ app_config }}"
          deployment: "{{ deployment }}"
          environment: "{{ environment }}"
    
    - name: Deploy application instances
      command: >
        /opt/{{ app_config.name }}/deploy.sh
        --type {{ item.key }}
        --count {{ item.value.count }}
        --memory {{ item.value.memory }}
        --port {{ item.value.port | default('auto') }}
      loop: "{{ app_config.instances | dict2items }}"
      register: deploy_results
    
    - name: Verify deployment
      uri:
        url: "http://localhost:{{ app_config.instances.web.port }}{{ deployment.health_check.endpoint }}"
        method: GET
        timeout: "{{ deployment.health_check.timeout }}"
      retries: "{{ deployment.health_check.retries }}"
      delay: 5
      when: deployment.health_check.enabled
"""


class EdgeCaseGenerator:
    """Generator for edge cases and boundary conditions."""

    @staticmethod
    def generate_malformed_yaml_cases() -> List[Tuple[str, str]]:
        """Generate various malformed YAML cases."""
        cases = [
            (
                "unclosed_list",
                """---
- name: Unclosed list
  hosts: all
  tasks:
    - name: Test
      package:
        name: [nginx, apache
""",
            ),
            (
                "unclosed_dict",
                """---
- name: Unclosed dict
  hosts: all
  tasks:
    - name: Test
      package: {name: nginx, state: present
""",
            ),
            (
                "invalid_indentation",
                """---
- name: Invalid indentation
  hosts: all
  tasks:
    - name: Test
      package:
        name: nginx
      state: present
""",
            ),
            (
                "mixed_tabs_spaces",
                """---
- name: Mixed tabs and spaces
  hosts: all
  tasks:
\t- name: Test
      package:
        name: nginx
\t\tstate: present
""",
            ),
            (
                "invalid_yaml_syntax",
                """---
- name: Invalid syntax
  hosts: all
  tasks:
    - name: Test
      package:
        name: nginx
        state: present
      invalid: [
""",
            ),
        ]

        return cases

    @staticmethod
    def generate_unicode_cases() -> List[Tuple[str, str]]:
        """Generate Unicode and encoding edge cases."""
        cases = [
            (
                "basic_unicode",
                """---
- name: Unicode test 🚀
  hosts: all
  vars:
    message: "Hello, 世界!"
  tasks:
    - name: Create file with Unicode
      copy:
        content: "{{ message }}"
        dest: /tmp/unicode.txt
""",
            ),
            (
                "emoji_heavy",
                """---
- name: Emoji heavy playbook 🎭🎪🎨
  hosts: all
  tasks:
    - name: Install packages 📦
      package:
        name: nginx
        state: present
    
    - name: Start service 🚀
      service:
        name: nginx
        state: started
""",
            ),
            (
                "mixed_scripts",
                """---
- name: Mixed scripts test
  hosts: all
  vars:
    messages:
      english: "Hello World"
      chinese: "你好世界"
      arabic: "مرحبا بالعالم"
      russian: "Привет мир"
      japanese: "こんにちは世界"
  tasks:
    - name: Debug messages
      debug:
        msg: "{{ item.value }}"
      loop: "{{ messages | dict2items }}"
""",
            ),
        ]

        return cases

    @staticmethod
    def generate_large_content_cases() -> List[Tuple[str, str]]:
        """Generate cases with large content for performance testing."""
        cases = []

        # Very long lines
        long_line = "a" * 1000
        cases.append(
            (
                "very_long_line",
                f"""---
- name: Very long line test
  hosts: all
  tasks:
    - name: Task with very long parameter
      copy:
        content: "{long_line}"
        dest: /tmp/long_content.txt
""",
            )
        )

        # Many tasks
        many_tasks = []
        for i in range(100):
            many_tasks.append(
                f"""    - name: Task {i}
      package:
        name: "package_{i}"
        state: present"""
            )

        cases.append(
            (
                "many_tasks",
                f"""---
- name: Many tasks playbook
  hosts: all
  tasks:
{chr(10).join(many_tasks)}
""",
            )
        )

        # Deep nesting
        cases.append(
            (
                "deep_nesting",
                """---
- name: Deep nesting test
  hosts: all
  vars:
    level1:
      level2:
        level3:
          level4:
            level5:
              level6:
                level7:
                  level8:
                    level9:
                      level10:
                        value: "deeply nested"
  tasks:
    - name: Access deeply nested value
      debug:
        msg: "{{ level1.level2.level3.level4.level5.level6.level7.level8.level9.level10.value }}"
""",
            )
        )

        return cases

    @staticmethod
    def generate_boundary_conditions() -> List[Tuple[str, str]]:
        """Generate boundary condition test cases."""
        cases = [
            ("empty_playbook", "---\n"),
            (
                "only_comments",
                """# This is a comment-only file
# No actual Ansible content
# Should be handled gracefully
""",
            ),
            (
                "minimal_playbook",
                """---
- hosts: all
""",
            ),
            (
                "no_tasks",
                """---
- name: No tasks playbook
  hosts: all
  vars:
    test_var: value
""",
            ),
            (
                "empty_tasks",
                """---
- name: Empty tasks
  hosts: all
  tasks: []
""",
            ),
            (
                "single_character_names",
                """---
- name: Single character test
  hosts: all
  tasks:
    - name: A
      package:
        name: a
        state: present
    
    - name: B
      service:
        name: b
        state: started
""",
            ),
        ]

        return cases


class StressTestGenerator:
    """Generator for stress testing scenarios."""

    @staticmethod
    def generate_large_project(
        num_roles: int = 50, tasks_per_role: int = 20
    ) -> Dict[str, Dict[str, str]]:
        """Generate a large project structure for stress testing."""
        project = {}

        # Generate main playbooks
        project["playbooks"] = {}

        # Site playbook
        role_list = [f"role_{i:03d}" for i in range(num_roles)]
        project["playbooks"][
            "site.yml"
        ] = f"""---
- name: Main site deployment
  hosts: all
  become: yes
  roles:
{chr(10).join(f'    - {role}' for role in role_list)}
"""

        # Group-specific playbooks
        for i in range(0, num_roles, 10):
            group_roles = role_list[i : i + 10]
            project["playbooks"][
                f"group_{i//10}.yml"
            ] = f"""---
- name: Group {i//10} deployment
  hosts: "group_{i//10}"
  become: yes
  roles:
{chr(10).join(f'    - {role}' for role in group_roles)}
"""

        # Generate roles
        project["roles"] = {}
        modules = [
            "package",
            "service",
            "copy",
            "file",
            "user",
            "group",
            "template",
            "command",
            "shell",
            "debug",
        ]

        for i in range(num_roles):
            role_name = f"role_{i:03d}"

            # Generate tasks
            tasks = []
            for j in range(tasks_per_role):
                module = modules[j % len(modules)]
                tasks.append(
                    f"""- name: Task {j} for {role_name}
  {module}:
    name: "{role_name}_item_{j}"
    state: present"""
                )

            project["roles"][role_name] = {
                "tasks/main.yml": f"---\n{chr(10).join(tasks)}",
                "handlers/main.yml": f"""---
- name: restart {role_name}
  service:
    name: "{role_name}"
    state: restarted""",
                "vars/main.yml": f"""---
{role_name}_enabled: true
{role_name}_port: {8000 + i}
{role_name}_config:
  setting1: value1
  setting2: value2""",
                "defaults/main.yml": f"""---
{role_name}_package: "{role_name}-package"
{role_name}_service: "{role_name}-service"
{role_name}_user: "{role_name}-user"
{role_name}_group: "{role_name}-group"
""",
            }

        return project

    @staticmethod
    def generate_memory_stress_content(size_mb: int = 10) -> str:
        """Generate content designed to stress memory usage."""
        # Calculate approximate content size
        target_size = size_mb * 1024 * 1024  # Convert to bytes

        # Generate large variable content
        large_string = "x" * 1000  # 1KB string
        num_vars = target_size // 2000  # Approximate number of variables needed

        vars_section = []
        for i in range(num_vars):
            vars_section.append(f'  large_var_{i}: "{large_string}_{i}"')

        return f"""---
- name: Memory stress test playbook
  hosts: all
  vars:
{chr(10).join(vars_section)}
  
  tasks:
    - name: Use large variables
      debug:
        msg: "Processing large data set"
    
    - name: Create files with large content
      copy:
        content: "{{{{ large_var_{i} }}}}"
        dest: "/tmp/large_file_{i}.txt"
      loop: "{{{{ range(0, {min(100, num_vars)}) | list }}}}"
"""

    @staticmethod
    def generate_concurrent_test_files(num_files: int = 100) -> List[Tuple[str, str]]:
        """Generate multiple files for concurrent processing tests."""
        files = []

        for i in range(num_files):
            filename = f"concurrent_test_{i:03d}.yml"
            content = f"""---
- name: Concurrent test file {i}
  hosts: all
  tasks:
    - name: Install package {i}
      package:
        name: "package_{i}"
        state: present
    
    - name: Start service {i}
      service:
        name: "service_{i}"
        state: started
    
    - name: Create file {i}
      copy:
        content: "Content for file {i}"
        dest: "/tmp/test_{i}.txt"
        mode: '0644'
    
    - name: Debug message {i}
      debug:
        msg: "Processing file {i}"
"""
            files.append((filename, content))

        return files


class RandomContentGenerator:
    """Generator for random content with controlled characteristics."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize with optional random seed for reproducible results."""
        if seed is not None:
            random.seed(seed)

    def generate_random_playbook(
        self,
        min_tasks: int = 1,
        max_tasks: int = 10,
        include_vars: bool = True,
        include_handlers: bool = True,
    ) -> str:
        """Generate a random playbook with specified constraints."""
        num_tasks = random.randint(min_tasks, max_tasks)

        # Random playbook name
        adjectives = ["simple", "complex", "advanced", "basic", "custom", "special"]
        nouns = ["deployment", "setup", "configuration", "installation", "management"]
        playbook_name = f"{random.choice(adjectives).title()} {random.choice(nouns)}"

        # Random host group
        host_groups = ["all", "webservers", "databases", "loadbalancers", "workers"]
        hosts = random.choice(host_groups)

        playbook = f"""---
- name: {playbook_name}
  hosts: {hosts}
  become: {random.choice(['yes', 'no'])}
  gather_facts: {random.choice(['yes', 'no'])}
"""

        # Add variables if requested
        if include_vars:
            playbook += self._generate_random_vars()

        # Add tasks
        playbook += "\n  tasks:\n"
        for i in range(num_tasks):
            playbook += self._generate_random_task(i)

        # Add handlers if requested
        if include_handlers and random.choice([True, False]):
            playbook += self._generate_random_handlers()

        return playbook

    def _generate_random_vars(self) -> str:
        """Generate random variables section."""
        var_types = [
            ("string", lambda: f'"{self._random_string()}"'),
            ("number", lambda: str(random.randint(1, 1000))),
            ("boolean", lambda: random.choice(["true", "false"])),
            (
                "list",
                lambda: f"[{', '.join([f'item_{i}' for i in range(random.randint(1, 5))])}]",
            ),
        ]

        num_vars = random.randint(1, 5)
        vars_section = "\n  vars:\n"

        for i in range(num_vars):
            var_name = f"var_{i}"
            var_type, generator = random.choice(var_types)
            var_value = generator()
            vars_section += f"    {var_name}: {var_value}\n"

        return vars_section

    def _generate_random_task(self, task_num: int) -> str:
        """Generate a random task."""
        modules = [
            ("package", self._generate_package_task),
            ("service", self._generate_service_task),
            ("copy", self._generate_copy_task),
            ("file", self._generate_file_task),
            ("user", self._generate_user_task),
            ("group", self._generate_group_task),
            ("command", self._generate_command_task),
            ("debug", self._generate_debug_task),
        ]

        module_name, generator = random.choice(modules)
        return generator(task_num)

    def _generate_package_task(self, task_num: int) -> str:
        """Generate random package task."""
        packages = [
            "nginx",
            "apache2",
            "mysql-server",
            "postgresql",
            "redis",
            "nodejs",
            "python3",
        ]
        package = random.choice(packages)
        state = random.choice(["present", "latest", "absent"])

        return f"""    - name: Task {task_num} - Manage package {package}
      package:
        name: {package}
        state: {state}
"""

    def _generate_service_task(self, task_num: int) -> str:
        """Generate random service task."""
        services = ["nginx", "apache2", "mysql", "postgresql", "redis", "ssh"]
        service = random.choice(services)
        state = random.choice(["started", "stopped", "restarted"])
        enabled = random.choice(["yes", "no"])

        return f"""    - name: Task {task_num} - Manage service {service}
      service:
        name: {service}
        state: {state}
        enabled: {enabled}
"""

    def _generate_copy_task(self, task_num: int) -> str:
        """Generate random copy task."""
        src = f"source_{task_num}.txt"
        dest = f"/tmp/dest_{task_num}.txt"
        mode = random.choice(["0644", "0755", "0600", "0640"])

        return f"""    - name: Task {task_num} - Copy file
      copy:
        src: {src}
        dest: {dest}
        mode: '{mode}'
"""

    def _generate_file_task(self, task_num: int) -> str:
        """Generate random file task."""
        path = f"/tmp/file_{task_num}"
        state = random.choice(["touch", "directory", "absent"])
        mode = random.choice(["0644", "0755", "0700"])

        return f"""    - name: Task {task_num} - Manage file
      file:
        path: {path}
        state: {state}
        mode: '{mode}'
"""

    def _generate_user_task(self, task_num: int) -> str:
        """Generate random user task."""
        username = f"user_{task_num}"
        state = random.choice(["present", "absent"])
        shell = random.choice(["/bin/bash", "/bin/sh", "/bin/false"])

        return f"""    - name: Task {task_num} - Manage user {username}
      user:
        name: {username}
        state: {state}
        shell: {shell}
"""

    def _generate_group_task(self, task_num: int) -> str:
        """Generate random group task."""
        groupname = f"group_{task_num}"
        state = random.choice(["present", "absent"])

        return f"""    - name: Task {task_num} - Manage group {groupname}
      group:
        name: {groupname}
        state: {state}
"""

    def _generate_command_task(self, task_num: int) -> str:
        """Generate random command task."""
        commands = ['echo "Hello World"', "ls -la /tmp", "whoami", "date", "uptime"]
        command = random.choice(commands)

        return f"""    - name: Task {task_num} - Run command
      command: {command}
      changed_when: false
"""

    def _generate_debug_task(self, task_num: int) -> str:
        """Generate random debug task."""
        messages = [
            f"Debug message {task_num}",
            f"Task {task_num} executed",
            f"Processing item {task_num}",
            f"Status update {task_num}",
        ]
        message = random.choice(messages)

        return f"""    - name: Task {task_num} - Debug message
      debug:
        msg: "{message}"
"""

    def _generate_random_handlers(self) -> str:
        """Generate random handlers section."""
        handlers = ["restart nginx", "reload apache", "restart mysql", "reload systemd"]

        num_handlers = random.randint(1, 3)
        handlers_section = "\n  handlers:\n"

        for i in range(num_handlers):
            handler_name = random.choice(handlers)
            service_name = handler_name.split()[-1]  # Extract service name

            handlers_section += f"""    - name: {handler_name}
      service:
        name: {service_name}
        state: restarted
"""

        return handlers_section

    def _random_string(self, length: int = 8) -> str:
        """Generate random string of specified length."""
        return "".join(random.choices(string.ascii_lowercase, k=length))
