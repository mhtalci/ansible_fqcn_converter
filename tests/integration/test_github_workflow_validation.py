"""
GitHub Workflow Testing and Validation for FQCN Converter.

This module provides comprehensive testing of GitHub Actions workflows,
including CI/CD pipeline validation, linting and security workflow testing,
build and deployment verification, and artifact collection validation.
"""

import pytest
import subprocess
import json
import yaml
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import requests


class GitHubWorkflowValidator:
    """Validator for GitHub Actions workflows."""
    
    def __init__(self, workflows_dir: Path = None):
        self.workflows_dir = workflows_dir or Path(".github/workflows")
        self.validation_results = {}
    
    def validate_all_workflows(self) -> dict:
        """Validate all GitHub Actions workflows."""
        results = {
            'valid_workflows': [],
            'invalid_workflows': [],
            'validation_errors': {},
            'workflow_analysis': {}
        }
        
        if not self.workflows_dir.exists():
            results['validation_errors']['directory'] = f"Workflows directory not found: {self.workflows_dir}"
            return results
        
        workflow_files = list(self.workflows_dir.glob("*.yml")) + list(self.workflows_dir.glob("*.yaml"))
        
        for workflow_file in workflow_files:
            try:
                validation_result = self.validate_workflow_file(workflow_file)
                
                if validation_result['valid']:
                    results['valid_workflows'].append(str(workflow_file))
                else:
                    results['invalid_workflows'].append(str(workflow_file))
                    results['validation_errors'][str(workflow_file)] = validation_result['errors']
                
                results['workflow_analysis'][str(workflow_file)] = validation_result['analysis']
                
            except Exception as e:
                results['invalid_workflows'].append(str(workflow_file))
                results['validation_errors'][str(workflow_file)] = [f"Exception during validation: {str(e)}"]
        
        return results
    
    def validate_workflow_file(self, workflow_file: Path) -> dict:
        """Validate a single workflow file."""
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'analysis': {}
        }
        
        try:
            # Parse YAML
            with open(workflow_file, 'r', encoding='utf-8') as f:
                workflow_data = yaml.safe_load(f)
            
            # Basic structure validation
            structure_validation = self._validate_workflow_structure(workflow_data)
            result['errors'].extend(structure_validation['errors'])
            result['warnings'].extend(structure_validation['warnings'])
            
            # Job validation
            jobs_validation = self._validate_jobs(workflow_data.get('jobs', {}))
            result['errors'].extend(jobs_validation['errors'])
            result['warnings'].extend(jobs_validation['warnings'])
            
            # Security validation
            security_validation = self._validate_security_practices(workflow_data)
            result['errors'].extend(security_validation['errors'])
            result['warnings'].extend(security_validation['warnings'])
            
            # Performance validation
            performance_validation = self._validate_performance_practices(workflow_data)
            result['warnings'].extend(performance_validation['warnings'])
            
            # Analysis
            on_data = workflow_data.get('on') or workflow_data.get(True)
            result['analysis'] = {
                'job_count': len(workflow_data.get('jobs', {})),
                'trigger_events': list(on_data.keys()) if isinstance(on_data, dict) else [on_data] if on_data else [],
                'uses_matrix': any('matrix' in job.get('strategy', {}) for job in workflow_data.get('jobs', {}).values()),
                'has_caching': self._check_caching_usage(workflow_data),
                'has_artifacts': self._check_artifact_usage(workflow_data),
                'estimated_runtime': self._estimate_workflow_runtime(workflow_data)
            }
            
            if result['errors']:
                result['valid'] = False
            
        except yaml.YAMLError as e:
            result['valid'] = False
            result['errors'].append(f"YAML parsing error: {str(e)}")
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Validation error: {str(e)}")
        
        return result
    
    def _validate_workflow_structure(self, workflow_data: dict) -> dict:
        """Validate basic workflow structure."""
        errors = []
        warnings = []
        
        # Required fields
        if 'name' not in workflow_data:
            warnings.append("Workflow name is missing")
        
        # Check for 'on' key (which might be parsed as boolean True)
        has_on_trigger = 'on' in workflow_data or True in workflow_data
        if not has_on_trigger:
            errors.append("Workflow trigger ('on') is missing")
        
        if 'jobs' not in workflow_data:
            errors.append("Jobs section is missing")
        elif not workflow_data['jobs']:
            errors.append("Jobs section is empty")
        
        # Validate trigger events (handle both 'on' string key and True boolean key)
        on_events = workflow_data.get('on') or workflow_data.get(True)
        if on_events:
            if isinstance(on_events, dict):
                for event, config in on_events.items():
                    if event not in ['push', 'pull_request', 'schedule', 'workflow_dispatch', 'release', 'workflow_call']:
                        warnings.append(f"Uncommon trigger event: {event}")
            elif isinstance(on_events, str):
                if on_events not in ['push', 'pull_request', 'schedule', 'workflow_dispatch']:
                    warnings.append(f"Uncommon trigger event: {on_events}")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _validate_jobs(self, jobs: dict) -> dict:
        """Validate job configurations."""
        errors = []
        warnings = []
        
        for job_name, job_config in jobs.items():
            # Required fields
            if 'runs-on' not in job_config:
                errors.append(f"Job '{job_name}' missing 'runs-on'")
            
            if 'steps' not in job_config:
                errors.append(f"Job '{job_name}' missing 'steps'")
            elif not job_config['steps']:
                warnings.append(f"Job '{job_name}' has no steps")
            
            # Validate steps
            if 'steps' in job_config:
                for i, step in enumerate(job_config['steps']):
                    step_validation = self._validate_step(step, job_name, i)
                    errors.extend(step_validation['errors'])
                    warnings.extend(step_validation['warnings'])
            
            # Check for common patterns
            if 'strategy' in job_config and 'matrix' in job_config['strategy']:
                matrix = job_config['strategy']['matrix']
                if isinstance(matrix, dict):
                    for key, values in matrix.items():
                        if isinstance(values, list) and len(values) > 10:
                            warnings.append(f"Job '{job_name}' has large matrix ({len(values)} values for {key})")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _validate_step(self, step: dict, job_name: str, step_index: int) -> dict:
        """Validate individual step configuration."""
        errors = []
        warnings = []
        
        step_id = step.get('name', f"step-{step_index}")
        
        # Must have either 'uses' or 'run'
        if 'uses' not in step and 'run' not in step:
            errors.append(f"Step '{step_id}' in job '{job_name}' must have either 'uses' or 'run'")
        
        if 'uses' in step and 'run' in step:
            errors.append(f"Step '{step_id}' in job '{job_name}' cannot have both 'uses' and 'run'")
        
        # Validate action versions
        if 'uses' in step:
            action = step['uses']
            if '@' not in action:
                warnings.append(f"Step '{step_id}' uses action without version: {action}")
            elif action.endswith('@main') or action.endswith('@master'):
                warnings.append(f"Step '{step_id}' uses unstable action version: {action}")
        
        # Check for security issues
        if 'run' in step:
            run_command = step['run']
            if 'curl' in run_command and 'http://' in run_command:
                warnings.append(f"Step '{step_id}' uses insecure HTTP in curl command")
            if 'sudo' in run_command:
                warnings.append(f"Step '{step_id}' uses sudo - consider if necessary")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _validate_security_practices(self, workflow_data: dict) -> dict:
        """Validate security practices in workflow."""
        errors = []
        warnings = []
        
        # Check permissions
        if 'permissions' not in workflow_data:
            warnings.append("Workflow permissions not explicitly set")
        
        # Check for secrets usage
        workflow_str = str(workflow_data)
        if '${{ secrets.' in workflow_str:
            # This is expected, but we should validate proper usage
            pass
        
        # Check for hardcoded tokens or keys
        sensitive_patterns = ['token', 'key', 'password', 'secret']
        for pattern in sensitive_patterns:
            if f'"{pattern}"' in workflow_str.lower() or f"'{pattern}'" in workflow_str.lower():
                warnings.append(f"Potential hardcoded {pattern} found - verify it's properly secured")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _validate_performance_practices(self, workflow_data: dict) -> dict:
        """Validate performance best practices."""
        warnings = []
        
        jobs = workflow_data.get('jobs', {})
        
        # Check for caching
        has_cache = False
        for job in jobs.values():
            for step in job.get('steps', []):
                if step.get('uses', '').startswith('actions/cache'):
                    has_cache = True
                    break
        
        if not has_cache:
            warnings.append("No caching detected - consider adding cache steps for dependencies")
        
        # Check for parallel execution
        if len(jobs) > 1:
            has_dependencies = any('needs' in job for job in jobs.values())
            if not has_dependencies:
                # All jobs run in parallel - good
                pass
            else:
                # Check for unnecessary serialization
                pass
        
        return {'warnings': warnings}
    
    def _check_caching_usage(self, workflow_data: dict) -> bool:
        """Check if workflow uses caching."""
        for job in workflow_data.get('jobs', {}).values():
            for step in job.get('steps', []):
                # Check for explicit cache actions
                if step.get('uses', '').startswith('actions/cache'):
                    return True
                # Check for built-in caching in setup actions
                if 'with' in step and 'cache' in step['with']:
                    return True
        return False
    
    def _check_artifact_usage(self, workflow_data: dict) -> bool:
        """Check if workflow uses artifacts."""
        for job in workflow_data.get('jobs', {}).values():
            for step in job.get('steps', []):
                uses = step.get('uses', '')
                if 'upload-artifact' in uses or 'download-artifact' in uses:
                    return True
        return False
    
    def _estimate_workflow_runtime(self, workflow_data: dict) -> str:
        """Estimate workflow runtime based on job complexity."""
        jobs = workflow_data.get('jobs', {})
        
        # Simple heuristic based on job count and matrix size
        total_jobs = len(jobs)
        max_matrix_size = 1
        
        for job in jobs.values():
            if 'strategy' in job and 'matrix' in job['strategy']:
                matrix = job['strategy']['matrix']
                if isinstance(matrix, dict):
                    matrix_size = 1
                    for values in matrix.values():
                        if isinstance(values, list):
                            matrix_size *= len(values)
                    max_matrix_size = max(max_matrix_size, matrix_size)
        
        estimated_minutes = total_jobs * 5 + max_matrix_size * 2
        
        if estimated_minutes < 10:
            return "< 10 minutes"
        elif estimated_minutes < 30:
            return "10-30 minutes"
        elif estimated_minutes < 60:
            return "30-60 minutes"
        else:
            return "> 1 hour"


class WorkflowTestRunner:
    """Runner for testing workflow functionality."""
    
    def __init__(self):
        self.test_results = {}
    
    def test_workflow_syntax(self, workflow_file: Path) -> dict:
        """Test workflow syntax using GitHub CLI or act."""
        result = {
            'syntax_valid': False,
            'errors': [],
            'method': 'yaml_parse'
        }
        
        try:
            # First, try basic YAML parsing
            with open(workflow_file, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
            
            result['syntax_valid'] = True
            
            # Try to use GitHub CLI if available
            try:
                gh_result = subprocess.run([
                    'gh', 'workflow', 'view', str(workflow_file)
                ], capture_output=True, text=True, timeout=30)
                
                if gh_result.returncode == 0:
                    result['method'] = 'github_cli'
                else:
                    result['errors'].append(f"GitHub CLI validation failed: {gh_result.stderr}")
            
            except (subprocess.TimeoutExpired, FileNotFoundError):
                # GitHub CLI not available or timed out
                pass
            
            # Try to use act if available (for local testing)
            try:
                act_result = subprocess.run([
                    'act', '--list', '--workflows', str(workflow_file)
                ], capture_output=True, text=True, timeout=30)
                
                if act_result.returncode == 0:
                    result['method'] = 'act'
                    result['act_jobs'] = act_result.stdout.strip().split('\n')
                
            except (subprocess.TimeoutExpired, FileNotFoundError):
                # act not available or timed out
                pass
        
        except yaml.YAMLError as e:
            result['syntax_valid'] = False
            result['errors'].append(f"YAML syntax error: {str(e)}")
        except Exception as e:
            result['syntax_valid'] = False
            result['errors'].append(f"Validation error: {str(e)}")
        
        return result
    
    def simulate_workflow_execution(self, workflow_file: Path, job_name: str = None) -> dict:
        """Simulate workflow execution for testing."""
        result = {
            'simulation_successful': False,
            'simulated_jobs': [],
            'errors': [],
            'warnings': []
        }
        
        try:
            with open(workflow_file, 'r', encoding='utf-8') as f:
                workflow_data = yaml.safe_load(f)
            
            jobs = workflow_data.get('jobs', {})
            
            if job_name and job_name not in jobs:
                result['errors'].append(f"Job '{job_name}' not found in workflow")
                return result
            
            jobs_to_simulate = {job_name: jobs[job_name]} if job_name else jobs
            
            for job_id, job_config in jobs_to_simulate.items():
                job_result = self._simulate_job_execution(job_id, job_config)
                result['simulated_jobs'].append(job_result)
                
                if not job_result['success']:
                    result['errors'].extend(job_result['errors'])
                
                result['warnings'].extend(job_result['warnings'])
            
            result['simulation_successful'] = all(job['success'] for job in result['simulated_jobs'])
        
        except Exception as e:
            result['errors'].append(f"Simulation error: {str(e)}")
        
        return result
    
    def _simulate_job_execution(self, job_id: str, job_config: dict) -> dict:
        """Simulate execution of a single job."""
        result = {
            'job_id': job_id,
            'success': True,
            'errors': [],
            'warnings': [],
            'simulated_steps': []
        }
        
        # Check runner availability
        runner = job_config.get('runs-on', 'ubuntu-latest')
        if not self._is_runner_available(runner):
            result['warnings'].append(f"Runner '{runner}' may not be available")
        
        # Simulate steps
        steps = job_config.get('steps', [])
        for i, step in enumerate(steps):
            step_result = self._simulate_step_execution(step, i)
            result['simulated_steps'].append(step_result)
            
            if not step_result['success']:
                result['success'] = False
                result['errors'].extend(step_result['errors'])
            
            result['warnings'].extend(step_result['warnings'])
        
        return result
    
    def _simulate_step_execution(self, step: dict, step_index: int) -> dict:
        """Simulate execution of a single step."""
        result = {
            'step_name': step.get('name', f'Step {step_index + 1}'),
            'success': True,
            'errors': [],
            'warnings': []
        }
        
        # Check action availability
        if 'uses' in step:
            action = step['uses']
            if not self._is_action_available(action):
                result['warnings'].append(f"Action '{action}' availability not verified")
        
        # Check command validity
        if 'run' in step:
            command = step['run']
            command_check = self._validate_command(command)
            if not command_check['valid']:
                result['success'] = False
                result['errors'].extend(command_check['errors'])
            result['warnings'].extend(command_check['warnings'])
        
        return result
    
    def _is_runner_available(self, runner: str) -> bool:
        """Check if runner is available (simplified check)."""
        common_runners = [
            'ubuntu-latest', 'ubuntu-20.04', 'ubuntu-18.04',
            'windows-latest', 'windows-2019', 'windows-2022',
            'macos-latest', 'macos-11', 'macos-12'
        ]
        return runner in common_runners
    
    def _is_action_available(self, action: str) -> bool:
        """Check if GitHub Action is available (simplified check)."""
        # Common actions that should always be available
        common_actions = [
            'actions/checkout', 'actions/setup-python', 'actions/setup-node',
            'actions/cache', 'actions/upload-artifact', 'actions/download-artifact'
        ]
        
        action_name = action.split('@')[0]
        return action_name in common_actions
    
    def _validate_command(self, command: str) -> dict:
        """Validate shell command (basic validation)."""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check for common issues
        if 'rm -rf /' in command:
            result['valid'] = False
            result['errors'].append("Dangerous command detected: rm -rf /")
        
        if 'sudo' in command and 'apt' not in command and 'yum' not in command:
            result['warnings'].append("Sudo usage detected - verify necessity")
        
        if 'curl' in command and 'http://' in command:
            result['warnings'].append("Insecure HTTP detected in curl command")
        
        return result


class TestGitHubWorkflowValidation:
    """Comprehensive GitHub workflow validation tests."""
    
    @pytest.fixture
    def workflow_validator(self):
        """Workflow validator fixture."""
        return GitHubWorkflowValidator()
    
    @pytest.fixture
    def workflow_test_runner(self):
        """Workflow test runner fixture."""
        return WorkflowTestRunner()
    
    @pytest.fixture
    def workflows_dir(self):
        """Workflows directory fixture."""
        workflows_dir = Path(".github/workflows")
        if not workflows_dir.exists():
            pytest.skip("GitHub workflows directory not found")
        return workflows_dir
    
    def test_all_workflows_syntax_validation(self, workflow_validator, workflows_dir):
        """Test syntax validation of all GitHub workflows."""
        validation_results = workflow_validator.validate_all_workflows()
        
        # Print validation summary
        print(f"\nWorkflow Validation Summary:")
        print(f"Valid workflows: {len(validation_results['valid_workflows'])}")
        print(f"Invalid workflows: {len(validation_results['invalid_workflows'])}")
        
        if validation_results['invalid_workflows']:
            print("\nInvalid workflows:")
            for workflow in validation_results['invalid_workflows']:
                print(f"  - {workflow}")
                errors = validation_results['validation_errors'].get(workflow, [])
                for error in errors:
                    print(f"    Error: {error}")
        
        # All workflows should be valid
        assert len(validation_results['invalid_workflows']) == 0, \
            f"Invalid workflows found: {validation_results['invalid_workflows']}"
        
        # Should have at least some workflows
        assert len(validation_results['valid_workflows']) > 0, \
            "No valid workflows found"
    
    def test_ci_workflow_validation(self, workflow_validator, workflows_dir):
        """Test CI workflow specifically."""
        ci_workflow = workflows_dir / "ci.yml"
        
        if not ci_workflow.exists():
            pytest.skip("CI workflow not found")
        
        validation_result = workflow_validator.validate_workflow_file(ci_workflow)
        
        assert validation_result['valid'], \
            f"CI workflow validation failed: {validation_result['errors']}"
        
        # Check CI-specific requirements
        analysis = validation_result['analysis']
        
        # Should have multiple jobs for comprehensive CI
        assert analysis['job_count'] >= 3, \
            f"CI workflow should have at least 3 jobs, found {analysis['job_count']}"
        
        # Should trigger on push and pull_request
        trigger_events = analysis['trigger_events']
        assert 'push' in trigger_events, "CI should trigger on push"
        assert 'pull_request' in trigger_events, "CI should trigger on pull_request"
        
        # Should use matrix for multi-environment testing
        assert analysis['uses_matrix'], "CI should use matrix strategy for multi-environment testing"
        
        # Should use caching for performance
        assert analysis['has_caching'], "CI should use caching for better performance"
        
        # Should collect artifacts
        assert analysis['has_artifacts'], "CI should collect test artifacts"
    
    def test_security_workflow_validation(self, workflow_validator, workflows_dir):
        """Test security workflow specifically."""
        security_workflow = workflows_dir / "security.yml"
        
        if not security_workflow.exists():
            pytest.skip("Security workflow not found")
        
        validation_result = workflow_validator.validate_workflow_file(security_workflow)
        
        assert validation_result['valid'], \
            f"Security workflow validation failed: {validation_result['errors']}"
        
        # Check security-specific requirements
        with open(security_workflow, 'r') as f:
            workflow_content = f.read()
        
        # Should include security scanning tools
        security_tools = ['bandit', 'safety', 'codeql']
        found_tools = [tool for tool in security_tools if tool in workflow_content.lower()]
        
        assert len(found_tools) >= 2, \
            f"Security workflow should use multiple security tools, found: {found_tools}"
        
        # Should have scheduled runs
        analysis = validation_result['analysis']
        assert 'schedule' in analysis['trigger_events'], \
            "Security workflow should have scheduled runs"
    
    def test_release_workflow_validation(self, workflow_validator, workflows_dir):
        """Test release workflow specifically."""
        release_workflow = workflows_dir / "release.yml"
        
        if not release_workflow.exists():
            pytest.skip("Release workflow not found")
        
        validation_result = workflow_validator.validate_workflow_file(release_workflow)
        
        assert validation_result['valid'], \
            f"Release workflow validation failed: {validation_result['errors']}"
        
        # Check release-specific requirements
        with open(release_workflow, 'r') as f:
            workflow_content = f.read()
        
        # Should trigger on tags
        workflow_data = yaml.safe_load(workflow_content)
        on_config = workflow_data.get('on', {})
        
        if isinstance(on_config, dict):
            assert 'push' in on_config and 'tags' in on_config.get('push', {}), \
                "Release workflow should trigger on tag pushes"
        
        # Should have build and release jobs
        jobs = workflow_data.get('jobs', {})
        job_names = list(jobs.keys())
        
        build_job_found = any('build' in job_name.lower() for job_name in job_names)
        release_job_found = any('release' in job_name.lower() for job_name in job_names)
        
        assert build_job_found, "Release workflow should have a build job"
        assert release_job_found, "Release workflow should have a release job"
    
    def test_lint_format_workflow_validation(self, workflow_validator, workflows_dir):
        """Test lint and format workflow specifically."""
        lint_workflow = workflows_dir / "lint-format.yml"
        
        if not lint_workflow.exists():
            pytest.skip("Lint-format workflow not found")
        
        validation_result = workflow_validator.validate_workflow_file(lint_workflow)
        
        assert validation_result['valid'], \
            f"Lint-format workflow validation failed: {validation_result['errors']}"
        
        # Check linting tools
        with open(lint_workflow, 'r') as f:
            workflow_content = f.read()
        
        linting_tools = ['flake8', 'black', 'isort', 'mypy']
        found_tools = [tool for tool in linting_tools if tool in workflow_content]
        
        assert len(found_tools) >= 3, \
            f"Lint workflow should use multiple linting tools, found: {found_tools}"
    
    def test_workflow_execution_simulation(self, workflow_test_runner, workflows_dir):
        """Test workflow execution simulation."""
        ci_workflow = workflows_dir / "ci.yml"
        
        if not ci_workflow.exists():
            pytest.skip("CI workflow not found for simulation")
        
        # Test syntax validation
        syntax_result = workflow_test_runner.test_workflow_syntax(ci_workflow)
        
        assert syntax_result['syntax_valid'], \
            f"Workflow syntax validation failed: {syntax_result['errors']}"
        
        # Test execution simulation
        simulation_result = workflow_test_runner.simulate_workflow_execution(ci_workflow)
        
        assert simulation_result['simulation_successful'], \
            f"Workflow simulation failed: {simulation_result['errors']}"
        
        # Should have simulated multiple jobs
        assert len(simulation_result['simulated_jobs']) > 0, \
            "No jobs were simulated"
        
        # Print simulation results
        print(f"\nWorkflow Simulation Results:")
        print(f"Jobs simulated: {len(simulation_result['simulated_jobs'])}")
        
        for job in simulation_result['simulated_jobs']:
            print(f"  Job '{job['job_id']}': {'✅' if job['success'] else '❌'}")
            if job['errors']:
                for error in job['errors']:
                    print(f"    Error: {error}")
    
    def test_workflow_performance_analysis(self, workflow_validator, workflows_dir):
        """Test workflow performance analysis."""
        workflow_files = list(workflows_dir.glob("*.yml"))
        
        performance_results = {}
        
        for workflow_file in workflow_files:
            validation_result = workflow_validator.validate_workflow_file(workflow_file)
            
            if validation_result['valid']:
                analysis = validation_result['analysis']
                performance_results[workflow_file.name] = {
                    'estimated_runtime': analysis['estimated_runtime'],
                    'job_count': analysis['job_count'],
                    'uses_matrix': analysis['uses_matrix'],
                    'has_caching': analysis['has_caching'],
                    'has_artifacts': analysis['has_artifacts']
                }
        
        # Print performance analysis
        print(f"\nWorkflow Performance Analysis:")
        for workflow_name, perf_data in performance_results.items():
            print(f"\n{workflow_name}:")
            print(f"  Estimated runtime: {perf_data['estimated_runtime']}")
            print(f"  Job count: {perf_data['job_count']}")
            print(f"  Uses matrix: {'✅' if perf_data['uses_matrix'] else '❌'}")
            print(f"  Has caching: {'✅' if perf_data['has_caching'] else '❌'}")
            print(f"  Has artifacts: {'✅' if perf_data['has_artifacts'] else '❌'}")
        
        # Performance assertions
        long_running_workflows = [
            name for name, data in performance_results.items()
            if data['estimated_runtime'] == "> 1 hour"
        ]
        
        if long_running_workflows:
            print(f"\nWarning: Long-running workflows detected: {long_running_workflows}")
        
        # Should have caching in CI workflows
        ci_workflows = [name for name in performance_results.keys() if 'ci' in name.lower()]
        for ci_workflow in ci_workflows:
            assert performance_results[ci_workflow]['has_caching'], \
                f"CI workflow '{ci_workflow}' should use caching"
    
    def test_workflow_security_practices(self, workflow_validator, workflows_dir):
        """Test workflow security practices."""
        workflow_files = list(workflows_dir.glob("*.yml"))
        
        security_issues = {}
        
        for workflow_file in workflow_files:
            validation_result = workflow_validator.validate_workflow_file(workflow_file)
            
            # Collect security warnings
            if validation_result['warnings']:
                security_warnings = [
                    warning for warning in validation_result['warnings']
                    if any(keyword in warning.lower() for keyword in ['security', 'token', 'secret', 'permission'])
                ]
                
                if security_warnings:
                    security_issues[workflow_file.name] = security_warnings
        
        # Print security analysis
        if security_issues:
            print(f"\nSecurity Issues Found:")
            for workflow_name, issues in security_issues.items():
                print(f"\n{workflow_name}:")
                for issue in issues:
                    print(f"  ⚠️ {issue}")
        else:
            print(f"\n✅ No security issues detected in workflows")
        
        # Check for specific security practices
        for workflow_file in workflow_files:
            with open(workflow_file, 'r') as f:
                content = f.read()
            
            # Should not have hardcoded secrets
            assert 'ghp_' not in content, f"Hardcoded GitHub token found in {workflow_file.name}"
            assert 'sk-' not in content, f"Hardcoded API key found in {workflow_file.name}"
    
    def test_workflow_artifact_collection(self, workflows_dir):
        """Test workflow artifact collection and reporting."""
        workflow_files = list(workflows_dir.glob("*.yml"))
        
        artifact_usage = {}
        
        for workflow_file in workflow_files:
            with open(workflow_file, 'r') as f:
                workflow_data = yaml.safe_load(f)
            
            artifacts = []
            
            for job_name, job_config in workflow_data.get('jobs', {}).items():
                for step in job_config.get('steps', []):
                    uses = step.get('uses', '')
                    
                    if 'upload-artifact' in uses:
                        artifact_name = step.get('with', {}).get('name', 'unnamed')
                        artifacts.append({
                            'type': 'upload',
                            'name': artifact_name,
                            'job': job_name,
                            'step': step.get('name', 'unnamed step')
                        })
                    
                    elif 'download-artifact' in uses:
                        artifact_name = step.get('with', {}).get('name', 'unnamed')
                        artifacts.append({
                            'type': 'download',
                            'name': artifact_name,
                            'job': job_name,
                            'step': step.get('name', 'unnamed step')
                        })
            
            if artifacts:
                artifact_usage[workflow_file.name] = artifacts
        
        # Print artifact analysis
        print(f"\nWorkflow Artifact Usage:")
        for workflow_name, artifacts in artifact_usage.items():
            print(f"\n{workflow_name}:")
            for artifact in artifacts:
                print(f"  {artifact['type'].upper()}: {artifact['name']} (Job: {artifact['job']})")
        
        # Verify CI workflow collects test artifacts
        ci_workflows = [name for name in artifact_usage.keys() if 'ci' in name.lower()]
        for ci_workflow in ci_workflows:
            ci_artifacts = artifact_usage[ci_workflow]
            upload_artifacts = [a for a in ci_artifacts if a['type'] == 'upload']
            
            assert len(upload_artifacts) > 0, \
                f"CI workflow '{ci_workflow}' should upload test artifacts"
    
    def test_workflow_coverage_reporting_integration(self, workflows_dir):
        """Test workflow integration with coverage reporting."""
        ci_workflow = workflows_dir / "ci.yml"
        
        if not ci_workflow.exists():
            pytest.skip("CI workflow not found")
        
        with open(ci_workflow, 'r') as f:
            workflow_content = f.read()
        
        # Should include coverage collection
        coverage_indicators = ['coverage', 'codecov', 'coveralls']
        found_coverage = [indicator for indicator in coverage_indicators if indicator in workflow_content.lower()]
        
        assert len(found_coverage) > 0, \
            f"CI workflow should include coverage reporting, found indicators: {found_coverage}"
        
        # Should upload coverage reports
        assert 'upload' in workflow_content.lower() and 'coverage' in workflow_content.lower(), \
            "CI workflow should upload coverage reports"
    
    def test_workflow_notification_systems(self, workflows_dir):
        """Test workflow notification and reporting systems."""
        workflow_files = list(workflows_dir.glob("*.yml"))
        
        notification_usage = {}
        
        for workflow_file in workflow_files:
            with open(workflow_file, 'r') as f:
                content = f.read()
            
            notifications = []
            
            # Check for various notification methods
            if 'slack' in content.lower():
                notifications.append('Slack')
            
            if 'discord' in content.lower():
                notifications.append('Discord')
            
            if 'email' in content.lower():
                notifications.append('Email')
            
            if 'github_step_summary' in content or 'GITHUB_STEP_SUMMARY' in content:
                notifications.append('GitHub Step Summary')
            
            if 'create-discussion' in content or 'issue' in content.lower():
                notifications.append('GitHub Issues/Discussions')
            
            if notifications:
                notification_usage[workflow_file.name] = notifications
        
        # Print notification analysis
        print(f"\nWorkflow Notification Systems:")
        for workflow_name, notifications in notification_usage.items():
            print(f"{workflow_name}: {', '.join(notifications)}")
        
        # Should have some form of notification in key workflows
        important_workflows = ['ci.yml', 'release.yml', 'security.yml']
        
        for important_workflow in important_workflows:
            if important_workflow in notification_usage:
                notifications = notification_usage[important_workflow]
                assert len(notifications) > 0, \
                    f"Important workflow '{important_workflow}' should have notification systems"


class TestWorkflowIntegration:
    """Test workflow integration with external systems."""
    
    @pytest.fixture
    def workflows_dir(self):
        """Workflows directory fixture."""
        workflows_dir = Path(".github/workflows")
        if not workflows_dir.exists():
            pytest.skip("GitHub workflows directory not found")
        return workflows_dir
    
    def test_github_actions_marketplace_integration(self, workflows_dir):
        """Test integration with GitHub Actions marketplace."""
        workflow_files = list(workflows_dir.glob("*.yml"))
        
        used_actions = set()
        
        for workflow_file in workflow_files:
            with open(workflow_file, 'r') as f:
                workflow_data = yaml.safe_load(f)
            
            for job in workflow_data.get('jobs', {}).values():
                for step in job.get('steps', []):
                    if 'uses' in step:
                        action = step['uses'].split('@')[0]
                        used_actions.add(action)
        
        # Print used actions
        print(f"\nUsed GitHub Actions:")
        for action in sorted(used_actions):
            print(f"  - {action}")
        
        # Verify common actions are used
        expected_actions = [
            'actions/checkout',
            'actions/setup-python',
            'actions/cache',
            'actions/upload-artifact'
        ]
        
        for expected_action in expected_actions:
            assert expected_action in used_actions, \
                f"Expected action '{expected_action}' not found in workflows"
    
    def test_dependency_management_integration(self, workflows_dir):
        """Test workflow integration with dependency management."""
        workflow_files = list(workflows_dir.glob("*.yml"))
        
        dependency_patterns = {
            'pip_cache': False,
            'pip_install': False,
            'requirements_file': False,
            'setup_py': False,
            'pyproject_toml': False
        }
        
        for workflow_file in workflow_files:
            with open(workflow_file, 'r') as f:
                content = f.read()
            
            if 'cache' in content and 'pip' in content:
                dependency_patterns['pip_cache'] = True
            
            if 'pip install' in content:
                dependency_patterns['pip_install'] = True
            
            if 'requirements.txt' in content:
                dependency_patterns['requirements_file'] = True
            
            if 'setup.py' in content:
                dependency_patterns['setup_py'] = True
            
            if 'pyproject.toml' in content:
                dependency_patterns['pyproject_toml'] = True
        
        # Print dependency management analysis
        print(f"\nDependency Management Integration:")
        for pattern, found in dependency_patterns.items():
            print(f"  {pattern}: {'✅' if found else '❌'}")
        
        # Should use pip caching
        assert dependency_patterns['pip_cache'], \
            "Workflows should use pip caching for better performance"
        
        # Should install dependencies
        assert dependency_patterns['pip_install'], \
            "Workflows should install Python dependencies"
    
    def test_quality_gate_integration(self, workflows_dir):
        """Test workflow integration with quality gates."""
        quality_workflow = workflows_dir / "quality-gate.yml"
        
        if quality_workflow.exists():
            with open(quality_workflow, 'r') as f:
                workflow_data = yaml.safe_load(f)
            
            # Should have quality checks
            jobs = workflow_data.get('jobs', {})
            
            quality_job_found = False
            for job_name, job_config in jobs.items():
                if 'quality' in job_name.lower() or 'gate' in job_name.lower():
                    quality_job_found = True
                    
                    # Should have dependencies on other jobs
                    assert 'needs' in job_config, \
                        f"Quality gate job '{job_name}' should depend on other jobs"
                    
                    needs = job_config['needs']
                    if isinstance(needs, list):
                        assert len(needs) > 1, \
                            f"Quality gate should depend on multiple jobs, found: {needs}"
            
            assert quality_job_found, \
                "Quality gate workflow should have a quality gate job"
        
        else:
            # Check if quality gates are integrated into CI workflow
            ci_workflow = workflows_dir / "ci.yml"
            
            if ci_workflow.exists():
                with open(ci_workflow, 'r') as f:
                    content = f.read()
                
                # Should have quality gate logic
                quality_indicators = ['quality', 'gate', 'threshold']
                found_indicators = [indicator for indicator in quality_indicators if indicator in content.lower()]
                
                assert len(found_indicators) > 0, \
                    "Workflows should include quality gate logic"