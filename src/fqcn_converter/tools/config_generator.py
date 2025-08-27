"""Configuration generator for FQCN Converter."""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ProjectConfig:
    """Project configuration for FQCN conversion."""
    
    # Basic settings
    project_name: str = "ansible-project"
    ansible_version: str = ">=2.9"
    
    # Conversion settings
    backup_files: bool = True
    validate_syntax: bool = True
    preserve_comments: bool = True
    
    # Collection settings
    preferred_collections: List[str] = None
    collection_mappings: Dict[str, str] = None
    
    # File patterns
    include_patterns: List[str] = None
    exclude_patterns: List[str] = None
    
    # Output settings
    report_format: str = "console"
    log_level: str = "INFO"
    
    def __post_init__(self):
        """Initialize default values."""
        if self.preferred_collections is None:
            self.preferred_collections = [
                "ansible.posix",
                "community.general",
                "ansible.builtin"
            ]
        
        if self.collection_mappings is None:
            self.collection_mappings = {}
        
        if self.include_patterns is None:
            self.include_patterns = ["*.yml", "*.yaml"]
        
        if self.exclude_patterns is None:
            self.exclude_patterns = [
                "venv/**",
                ".git/**",
                "node_modules/**",
                "*.backup"
            ]


class ConfigurationGenerator:
    """Generates configuration files for different scenarios."""
    
    def __init__(self):
        """Initialize configuration generator."""
        self.templates = {
            'basic': self._get_basic_template,
            'advanced': self._get_advanced_template,
            'ci_cd': self._get_cicd_template,
            'enterprise': self._get_enterprise_template
        }
    
    def generate_config(self, template_name: str, **kwargs) -> ProjectConfig:
        """Generate configuration from template.
        
        Args:
            template_name: Name of the template to use
            **kwargs: Template-specific parameters
            
        Returns:
            Generated project configuration
        """
        if template_name not in self.templates:
            raise ValueError(f"Unknown template: {template_name}")
        
        template_func = self.templates[template_name]
        return template_func(**kwargs)
    
    def save_config(self, config: ProjectConfig, output_path: Path, 
                   format_type: str = 'yaml') -> None:
        """Save configuration to file.
        
        Args:
            config: Configuration to save
            output_path: Path to save the configuration
            format_type: Format type ('yaml' or 'json')
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = asdict(config)
        
        if format_type.lower() == 'yaml':
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        elif format_type.lower() == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        
        logger.info(f"Saved configuration to {output_path}")
    
    def _get_basic_template(self, project_name: str = "my-ansible-project") -> ProjectConfig:
        """Get basic configuration template."""
        return ProjectConfig(
            project_name=project_name,
            backup_files=True,
            validate_syntax=True,
            preserve_comments=True,
            report_format="console",
            log_level="INFO"
        )
    
    def _get_advanced_template(self, project_name: str = "advanced-ansible-project",
                              collections: List[str] = None) -> ProjectConfig:
        """Get advanced configuration template."""
        if collections is None:
            collections = [
                "ansible.posix",
                "community.general", 
                "community.crypto",
                "community.docker",
                "ansible.builtin"
            ]
        
        return ProjectConfig(
            project_name=project_name,
            preferred_collections=collections,
            collection_mappings={
                "shell": "ansible.builtin.shell",
                "command": "ansible.builtin.command",
                "copy": "ansible.builtin.copy",
                "template": "ansible.builtin.template",
                "docker_container": "community.docker.docker_container",
                "docker_image": "community.docker.docker_image"
            },
            backup_files=True,
            validate_syntax=True,
            preserve_comments=True,
            include_patterns=["*.yml", "*.yaml", "playbooks/**/*.yml"],
            exclude_patterns=[
                "venv/**", ".git/**", "node_modules/**", "*.backup",
                "test/**", "tests/**", ".pytest_cache/**"
            ],
            report_format="markdown",
            log_level="DEBUG"
        )
    
    def _get_cicd_template(self, project_name: str = "cicd-ansible-project") -> ProjectConfig:
        """Get CI/CD configuration template."""
        return ProjectConfig(
            project_name=project_name,
            backup_files=False,  # Don't create backups in CI/CD
            validate_syntax=True,
            preserve_comments=True,
            preferred_collections=[
                "ansible.builtin",
                "ansible.posix", 
                "community.general"
            ],
            include_patterns=["*.yml", "*.yaml"],
            exclude_patterns=[
                ".git/**", "venv/**", "*.backup", "*.tmp",
                ".github/**", ".gitlab-ci.yml", "Jenkinsfile"
            ],
            report_format="json",  # Machine-readable format for CI/CD
            log_level="WARNING"  # Reduce noise in CI/CD logs
        )
    
    def _get_enterprise_template(self, project_name: str = "enterprise-ansible-project",
                               custom_collections: List[str] = None) -> ProjectConfig:
        """Get enterprise configuration template."""
        collections = [
            "ansible.builtin",
            "ansible.posix",
            "community.general",
            "community.crypto",
            "community.docker",
            "community.kubernetes",
            "community.vmware",
            "amazon.aws",
            "azure.azcollection",
            "google.cloud"
        ]
        
        if custom_collections:
            collections.extend(custom_collections)
        
        return ProjectConfig(
            project_name=project_name,
            preferred_collections=collections,
            collection_mappings={
                # Common enterprise mappings
                "shell": "ansible.builtin.shell",
                "command": "ansible.builtin.command",
                "copy": "ansible.builtin.copy",
                "template": "ansible.builtin.template",
                "service": "ansible.builtin.service",
                "systemd": "ansible.builtin.systemd",
                "user": "ansible.builtin.user",
                "group": "ansible.builtin.group",
                "file": "ansible.builtin.file",
                "lineinfile": "ansible.builtin.lineinfile",
                "replace": "ansible.builtin.replace",
                "blockinfile": "ansible.builtin.blockinfile",
                # Cloud-specific
                "ec2": "amazon.aws.ec2",
                "s3_bucket": "amazon.aws.s3_bucket",
                "azure_rm_virtualmachine": "azure.azcollection.azure_rm_virtualmachine",
                "gcp_compute_instance": "google.cloud.gcp_compute_instance",
                # Container/K8s
                "docker_container": "community.docker.docker_container",
                "k8s": "community.kubernetes.k8s"
            },
            backup_files=True,
            validate_syntax=True,
            preserve_comments=True,
            include_patterns=[
                "*.yml", "*.yaml",
                "playbooks/**/*.yml", "playbooks/**/*.yaml",
                "roles/**/*.yml", "roles/**/*.yaml",
                "group_vars/**/*.yml", "host_vars/**/*.yml"
            ],
            exclude_patterns=[
                "venv/**", ".git/**", "node_modules/**", "*.backup",
                "test/**", "tests/**", ".pytest_cache/**",
                "inventory/**", "*.retry", "*.log"
            ],
            report_format="html",  # Rich reporting for enterprise
            log_level="INFO"
        )
    
    def generate_precommit_config(self, output_path: Path, 
                                 auto_fix: bool = False,
                                 strict_mode: bool = False) -> None:
        """Generate pre-commit configuration file.
        
        Args:
            output_path: Path to save the pre-commit config
            auto_fix: Whether to enable auto-fix
            strict_mode: Whether to enable strict mode
        """
        config = {
            'repos': [
                {
                    'repo': 'local',
                    'hooks': [
                        {
                            'id': 'fqcn-converter',
                            'name': 'FQCN Converter',
                            'entry': 'fqcn-converter-precommit',
                            'language': 'python',
                            'files': r'\.(yml|yaml)$',
                            'args': []
                        }
                    ]
                }
            ]
        }
        
        # Add arguments based on options
        if auto_fix:
            config['repos'][0]['hooks'][0]['args'].append('--auto-fix')
        
        if strict_mode:
            config['repos'][0]['hooks'][0]['args'].append('--strict')
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        logger.info(f"Generated pre-commit config at {output_path}")
    
    def generate_github_workflow(self, output_path: Path,
                                python_version: str = "3.9") -> None:
        """Generate GitHub Actions workflow for FQCN validation.
        
        Args:
            output_path: Path to save the workflow file
            python_version: Python version to use
        """
        workflow = {
            'name': 'FQCN Validation',
            'on': {
                'push': {
                    'branches': ['main', 'develop']
                },
                'pull_request': {
                    'branches': ['main', 'develop']
                }
            },
            'jobs': {
                'fqcn-validation': {
                    'runs-on': 'ubuntu-latest',
                    'steps': [
                        {
                            'name': 'Checkout code',
                            'uses': 'actions/checkout@v3'
                        },
                        {
                            'name': 'Set up Python',
                            'uses': 'actions/setup-python@v4',
                            'with': {
                                'python-version': python_version
                            }
                        },
                        {
                            'name': 'Install FQCN Converter',
                            'run': 'pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git'
                        },
                        {
                            'name': 'Validate FQCN compliance',
                            'run': 'fqcn-validator --strict .'
                        },
                        {
                            'name': 'Generate validation report',
                            'run': 'fqcn-converter --report-format json --output-dir reports .',
                            'if': 'always()'
                        },
                        {
                            'name': 'Upload validation report',
                            'uses': 'actions/upload-artifact@v3',
                            'with': {
                                'name': 'fqcn-validation-report',
                                'path': 'reports/'
                            },
                            'if': 'always()'
                        }
                    ]
                }
            }
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(workflow, f, default_flow_style=False, indent=2)
        
        logger.info(f"Generated GitHub workflow at {output_path}")
    
    def detect_project_type(self, project_path: Path) -> str:
        """Detect the type of Ansible project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Detected project type
        """
        # Check for common files and directories
        indicators = {
            'enterprise': [
                'requirements.yml',
                'ansible.cfg',
                'group_vars',
                'host_vars',
                'roles',
                'playbooks'
            ],
            'cicd': [
                '.github/workflows',
                '.gitlab-ci.yml',
                'Jenkinsfile',
                '.travis.yml'
            ],
            'advanced': [
                'roles',
                'group_vars',
                'requirements.yml'
            ],
            'basic': [
                '*.yml',
                '*.yaml'
            ]
        }
        
        scores = {}
        
        for project_type, files in indicators.items():
            score = 0
            for pattern in files:
                if '*' in pattern:
                    # Glob pattern
                    matches = list(project_path.glob(pattern))
                    if matches:
                        score += len(matches)
                else:
                    # Direct path
                    if (project_path / pattern).exists():
                        score += 1
            
            scores[project_type] = score
        
        # Return the type with the highest score
        return max(scores, key=scores.get) if scores else 'basic'
    
    def generate_project_config(self, project_path: Path, 
                               output_path: Optional[Path] = None,
                               template_override: Optional[str] = None) -> ProjectConfig:
        """Generate configuration for a specific project.
        
        Args:
            project_path: Path to the project directory
            output_path: Optional path to save the configuration
            template_override: Optional template name to override detection
            
        Returns:
            Generated project configuration
        """
        # Detect project type
        project_type = template_override or self.detect_project_type(project_path)
        project_name = project_path.name
        
        logger.info(f"Detected project type: {project_type} for {project_name}")
        
        # Generate configuration
        config = self.generate_config(project_type, project_name=project_name)
        
        # Save if output path provided
        if output_path:
            self.save_config(config, output_path)
        
        return config


def main():
    """CLI entry point for configuration generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description='FQCN Configuration Generator')
    parser.add_argument('--template', choices=['basic', 'advanced', 'cicd', 'enterprise'],
                       default='basic', help='Configuration template')
    parser.add_argument('--project-name', default='my-ansible-project',
                       help='Project name')
    parser.add_argument('--output', '-o', type=Path, default=Path('fqcn-config.yml'),
                       help='Output file path')
    parser.add_argument('--format', choices=['yaml', 'json'], default='yaml',
                       help='Output format')
    parser.add_argument('--detect', type=Path, help='Auto-detect configuration for project')
    parser.add_argument('--precommit', type=Path, help='Generate pre-commit config')
    parser.add_argument('--github-workflow', type=Path, help='Generate GitHub workflow')
    
    args = parser.parse_args()
    
    generator = ConfigurationGenerator()
    
    if args.detect:
        config = generator.generate_project_config(args.detect, args.output)
        print(f"Generated configuration for {args.detect} -> {args.output}")
    elif args.precommit:
        generator.generate_precommit_config(args.precommit)
        print(f"Generated pre-commit config -> {args.precommit}")
    elif args.github_workflow:
        generator.generate_github_workflow(args.github_workflow)
        print(f"Generated GitHub workflow -> {args.github_workflow}")
    else:
        config = generator.generate_config(args.template, project_name=args.project_name)
        generator.save_config(config, args.output, args.format)
        print(f"Generated {args.template} configuration -> {args.output}")


if __name__ == '__main__':
    main()