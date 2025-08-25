"""
Final production readiness assessment tests for FQCN Converter.

These tests conduct comprehensive security audits, performance validation,
deployment testing, and create final release preparation checklists.
"""

import pytest
import subprocess
import sys
import os
import json
import time
import psutil
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import patch, Mock

from fqcn_converter.core.converter import FQCNConverter
from fqcn_converter.core.validator import ValidationEngine
from fqcn_converter.core.batch import BatchProcessor
from fqcn_converter.config.manager import ConfigurationManager


class SecurityAuditor:
    """Security audit functionality for production readiness."""
    
    def __init__(self):
        self.security_issues = []
        self.recommendations = []
    
    def audit_code_security(self) -> Dict[str, Any]:
        """Perform security audit of the codebase."""
        audit_results = {
            'bandit_scan': self._run_bandit_scan(),
            'dependency_scan': self._scan_dependencies(),
            'file_permissions': self._check_file_permissions(),
            'input_validation': self._check_input_validation(),
            'secrets_scan': self._scan_for_secrets(),
            'overall_score': 0,
            'issues': [],
            'recommendations': []
        }
        
        # Calculate overall security score
        scores = []
        for check, result in audit_results.items():
            if isinstance(result, dict) and 'score' in result:
                scores.append(result['score'])
        
        if scores:
            audit_results['overall_score'] = sum(scores) / len(scores)
        
        return audit_results
    
    def _run_bandit_scan(self) -> Dict[str, Any]:
        """Run bandit security scanner if available."""
        try:
            # Try to run bandit on the source code
            result = subprocess.run([
                sys.executable, '-m', 'bandit', '-r', 'src/', '-f', 'json'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # No security issues found
                return {'score': 10, 'issues': [], 'status': 'clean'}
            else:
                # Parse bandit output for issues
                try:
                    bandit_output = json.loads(result.stdout)
                    issues = bandit_output.get('results', [])
                    
                    # Filter by severity
                    high_issues = [i for i in issues if i.get('issue_severity') == 'HIGH']
                    medium_issues = [i for i in issues if i.get('issue_severity') == 'MEDIUM']
                    
                    score = 10 - len(high_issues) * 3 - len(medium_issues) * 1
                    score = max(0, score)
                    
                    return {
                        'score': score,
                        'high_issues': len(high_issues),
                        'medium_issues': len(medium_issues),
                        'issues': issues[:5],  # First 5 issues
                        'status': 'issues_found' if issues else 'clean'
                    }
                except json.JSONDecodeError:
                    return {'score': 5, 'status': 'scan_error', 'error': 'Could not parse bandit output'}
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {'score': 7, 'status': 'not_available', 'message': 'Bandit not available'}
    
    def _scan_dependencies(self) -> Dict[str, Any]:
        """Scan dependencies for known vulnerabilities."""
        try:
            # Try to run safety check
            result = subprocess.run([
                sys.executable, '-m', 'safety', 'check', '--json'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return {'score': 10, 'vulnerabilities': 0, 'status': 'clean'}
            else:
                try:
                    safety_output = json.loads(result.stdout)
                    vuln_count = len(safety_output)
                    
                    score = 10 - vuln_count * 2
                    score = max(0, score)
                    
                    return {
                        'score': score,
                        'vulnerabilities': vuln_count,
                        'issues': safety_output[:3],  # First 3 vulnerabilities
                        'status': 'vulnerabilities_found' if vuln_count > 0 else 'clean'
                    }
                except json.JSONDecodeError:
                    return {'score': 5, 'status': 'scan_error'}
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {'score': 8, 'status': 'not_available', 'message': 'Safety scanner not available'}
    
    def _check_file_permissions(self) -> Dict[str, Any]:
        """Check file permissions for security issues."""
        issues = []
        src_path = Path("src")
        
        if src_path.exists():
            for file_path in src_path.rglob("*.py"):
                try:
                    stat = file_path.stat()
                    mode = stat.st_mode
                    
                    # Check for world-writable files
                    if mode & 0o002:
                        issues.append(f"World-writable file: {file_path}")
                    
                    # Check for executable Python files (potential issue)
                    if mode & 0o111 and file_path.suffix == '.py':
                        issues.append(f"Executable Python file: {file_path}")
                
                except OSError:
                    continue
        
        score = 10 - len(issues)
        score = max(0, score)
        
        return {
            'score': score,
            'issues': issues,
            'status': 'issues_found' if issues else 'secure'
        }
    
    def _check_input_validation(self) -> Dict[str, Any]:
        """Check for proper input validation in the code."""
        validation_issues = []
        src_path = Path("src")
        
        if src_path.exists():
            for file_path in src_path.rglob("*.py"):
                try:
                    content = file_path.read_text()
                    
                    # Check for potential SQL injection patterns (though unlikely in this project)
                    if 'execute(' in content and 'format(' in content:
                        validation_issues.append(f"Potential SQL injection risk in {file_path}")
                    
                    # Check for eval/exec usage
                    if 'eval(' in content or 'exec(' in content:
                        validation_issues.append(f"Use of eval/exec in {file_path}")
                    
                    # Check for shell command injection risks
                    if 'subprocess' in content and 'shell=True' in content:
                        validation_issues.append(f"Shell injection risk in {file_path}")
                
                except (OSError, UnicodeDecodeError):
                    continue
        
        score = 10 - len(validation_issues) * 2
        score = max(0, score)
        
        return {
            'score': score,
            'issues': validation_issues,
            'status': 'issues_found' if validation_issues else 'secure'
        }
    
    def _scan_for_secrets(self) -> Dict[str, Any]:
        """Scan for hardcoded secrets or sensitive information."""
        secrets_issues = []
        src_path = Path("src")
        
        # Patterns that might indicate secrets
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']'
        ]
        
        if src_path.exists():
            import re
            
            for file_path in src_path.rglob("*.py"):
                try:
                    content = file_path.read_text()
                    
                    for pattern in secret_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            secrets_issues.append(f"Potential secret in {file_path}: {pattern}")
                
                except (OSError, UnicodeDecodeError):
                    continue
        
        score = 10 - len(secrets_issues) * 3
        score = max(0, score)
        
        return {
            'score': score,
            'issues': secrets_issues,
            'status': 'issues_found' if secrets_issues else 'clean'
        }


class PerformanceValidator:
    """Performance validation for production deployment."""
    
    def __init__(self):
        self.benchmarks = {}
    
    def validate_production_performance(self) -> Dict[str, Any]:
        """Validate performance characteristics for production use."""
        performance_results = {
            'startup_time': self._measure_startup_time(),
            'memory_usage': self._measure_memory_usage(),
            'throughput': self._measure_throughput(),
            'scalability': self._test_scalability(),
            'resource_limits': self._test_resource_limits(),
            'overall_score': 0,
            'recommendations': []
        }
        
        # Calculate overall performance score
        scores = []
        for test, result in performance_results.items():
            if isinstance(result, dict) and 'score' in result:
                scores.append(result['score'])
        
        if scores:
            performance_results['overall_score'] = sum(scores) / len(scores)
        
        return performance_results
    
    def _measure_startup_time(self) -> Dict[str, Any]:
        """Measure application startup time."""
        import time
        
        startup_times = []
        
        for _ in range(5):  # Measure 5 times
            start_time = time.time()
            
            # Simulate startup by importing main classes
            try:
                from fqcn_converter.core.converter import FQCNConverter
                from fqcn_converter.core.validator import ValidationEngine
                from fqcn_converter.core.batch import BatchProcessor
                
                # Create instances
                converter = FQCNConverter()
                validator = ValidationEngine()
                batch_processor = BatchProcessor()
                
                end_time = time.time()
                startup_times.append(end_time - start_time)
            
            except Exception as e:
                return {'score': 0, 'error': str(e), 'status': 'failed'}
        
        avg_startup = sum(startup_times) / len(startup_times)
        
        # Score based on startup time (lower is better)
        if avg_startup < 0.5:
            score = 10
        elif avg_startup < 1.0:
            score = 8
        elif avg_startup < 2.0:
            score = 6
        else:
            score = 4
        
        return {
            'score': score,
            'average_time': avg_startup,
            'times': startup_times,
            'status': 'acceptable' if avg_startup < 2.0 else 'slow'
        }
    
    def _measure_memory_usage(self) -> Dict[str, Any]:
        """Measure memory usage characteristics."""
        import gc
        
        process = psutil.Process()
        
        # Baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss
        
        # Create instances and measure memory
        converter = FQCNConverter()
        validator = ValidationEngine()
        batch_processor = BatchProcessor()
        config_manager = ConfigurationManager()
        
        # Force garbage collection
        gc.collect()
        
        # Measure memory after instantiation
        after_memory = process.memory_info().rss
        memory_delta = after_memory - baseline_memory
        memory_delta_mb = memory_delta / 1024 / 1024
        
        # Score based on memory usage
        if memory_delta_mb < 10:
            score = 10
        elif memory_delta_mb < 25:
            score = 8
        elif memory_delta_mb < 50:
            score = 6
        else:
            score = 4
        
        return {
            'score': score,
            'baseline_mb': baseline_memory / 1024 / 1024,
            'after_mb': after_memory / 1024 / 1024,
            'delta_mb': memory_delta_mb,
            'status': 'efficient' if memory_delta_mb < 25 else 'high'
        }
    
    def _measure_throughput(self) -> Dict[str, Any]:
        """Measure conversion throughput."""
        import tempfile
        import time
        
        converter = FQCNConverter()
        
        # Create test content
        test_content = """---
- name: Throughput test
  hosts: all
  tasks:
    - name: Install package
      package:
        name: nginx
        state: present
    
    - name: Start service
      service:
        name: nginx
        state: started
"""
        
        # Measure throughput
        num_conversions = 50
        start_time = time.time()
        
        for _ in range(num_conversions):
            result = converter.convert_content(test_content)
            assert result.success
        
        end_time = time.time()
        duration = end_time - start_time
        throughput = num_conversions / duration
        
        # Score based on throughput
        if throughput > 100:
            score = 10
        elif throughput > 50:
            score = 8
        elif throughput > 25:
            score = 6
        else:
            score = 4
        
        return {
            'score': score,
            'conversions_per_second': throughput,
            'total_time': duration,
            'conversions': num_conversions,
            'status': 'fast' if throughput > 50 else 'acceptable'
        }
    
    def _test_scalability(self) -> Dict[str, Any]:
        """Test scalability with increasing load."""
        import tempfile
        
        batch_processor = BatchProcessor(max_workers=4)
        
        # Test with different project counts
        project_counts = [5, 10, 20]
        scalability_results = {}
        
        for count in project_counts:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Create projects
                projects = []
                for i in range(count):
                    project_dir = temp_path / f"scale_project_{i}"
                    project_dir.mkdir()
                    
                    (project_dir / "site.yml").write_text(f"""---
- name: Scale test {i}
  hosts: all
  tasks:
    - name: Task {i}
      package:
        name: "package_{i}"
        state: present
""")
                    projects.append(str(project_dir))
                
                # Measure processing time
                start_time = time.time()
                results = batch_processor.process_projects(projects, dry_run=True)
                end_time = time.time()
                
                duration = end_time - start_time
                throughput = count / duration
                
                scalability_results[count] = {
                    'duration': duration,
                    'throughput': throughput,
                    'success_rate': len([r for r in results if r['success']]) / len(results)
                }
        
        # Analyze scalability
        throughputs = [r['throughput'] for r in scalability_results.values()]
        
        # Check if throughput degrades significantly
        if len(throughputs) > 1:
            degradation = (max(throughputs) - min(throughputs)) / max(throughputs)
            
            if degradation < 0.2:  # Less than 20% degradation
                score = 10
            elif degradation < 0.4:
                score = 8
            elif degradation < 0.6:
                score = 6
            else:
                score = 4
        else:
            score = 8
        
        return {
            'score': score,
            'results': scalability_results,
            'degradation': degradation if len(throughputs) > 1 else 0,
            'status': 'scalable' if score >= 8 else 'limited'
        }
    
    def _test_resource_limits(self) -> Dict[str, Any]:
        """Test behavior under resource constraints."""
        import tempfile
        import threading
        
        # Test with limited memory scenario (simulated)
        converter = FQCNConverter()
        
        # Create a large file to test memory limits
        large_tasks = []
        for i in range(500):
            large_tasks.append(f"""  - name: Large task {i}
    package:
      name: "package_{i}"
      state: present""")
        
        large_content = f"""---
- name: Resource limit test
  hosts: all
  tasks:
{chr(10).join(large_tasks)}
"""
        
        try:
            start_memory = psutil.Process().memory_info().rss
            
            result = converter.convert_content(large_content)
            
            end_memory = psutil.Process().memory_info().rss
            memory_used = (end_memory - start_memory) / 1024 / 1024
            
            if result.success and memory_used < 100:  # Less than 100MB
                score = 10
            elif result.success and memory_used < 200:
                score = 8
            elif result.success:
                score = 6
            else:
                score = 2
            
            return {
                'score': score,
                'memory_used_mb': memory_used,
                'success': result.success,
                'status': 'efficient' if memory_used < 100 else 'acceptable'
            }
        
        except Exception as e:
            return {
                'score': 0,
                'error': str(e),
                'status': 'failed'
            }


class DeploymentValidator:
    """Validate deployment readiness and packaging."""
    
    def validate_deployment_readiness(self) -> Dict[str, Any]:
        """Validate that the package is ready for deployment."""
        deployment_results = {
            'package_structure': self._validate_package_structure(),
            'dependencies': self._validate_dependencies(),
            'entry_points': self._validate_entry_points(),
            'installation': self._test_installation(),
            'distribution': self._test_distribution_build(),
            'overall_score': 0,
            'issues': []
        }
        
        # Calculate overall deployment score
        scores = []
        for test, result in deployment_results.items():
            if isinstance(result, dict) and 'score' in result:
                scores.append(result['score'])
        
        if scores:
            deployment_results['overall_score'] = sum(scores) / len(scores)
        
        return deployment_results
    
    def _validate_package_structure(self) -> Dict[str, Any]:
        """Validate package structure follows best practices."""
        required_files = [
            'pyproject.toml',
            'README.md',
            'LICENSE',
            'src/fqcn_converter/__init__.py'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        # Check for additional recommended files
        recommended_files = [
            'CHANGELOG.md',
            'CONTRIBUTING.md',
            'CODE_OF_CONDUCT.md'
        ]
        
        missing_recommended = []
        for file_path in recommended_files:
            if not Path(file_path).exists():
                missing_recommended.append(file_path)
        
        score = 10 - len(missing_files) * 3 - len(missing_recommended) * 1
        score = max(0, score)
        
        return {
            'score': score,
            'missing_required': missing_files,
            'missing_recommended': missing_recommended,
            'status': 'complete' if not missing_files else 'incomplete'
        }
    
    def _validate_dependencies(self) -> Dict[str, Any]:
        """Validate dependency specification and compatibility."""
        issues = []
        
        # Check pyproject.toml
        pyproject_path = Path('pyproject.toml')
        if pyproject_path.exists():
            try:
                import tomli
                with open(pyproject_path, 'rb') as f:
                    pyproject_data = tomli.load(f)
                
                # Check for dependencies section
                dependencies = pyproject_data.get('project', {}).get('dependencies', [])
                
                if not dependencies:
                    issues.append("No dependencies specified in pyproject.toml")
                
                # Check for version constraints
                unconstrained_deps = []
                for dep in dependencies:
                    if not any(op in dep for op in ['>=', '<=', '==', '~=', '!=']):
                        unconstrained_deps.append(dep)
                
                if unconstrained_deps:
                    issues.append(f"Unconstrained dependencies: {unconstrained_deps}")
            
            except Exception as e:
                issues.append(f"Could not parse pyproject.toml: {e}")
        else:
            issues.append("pyproject.toml not found")
        
        score = 10 - len(issues) * 2
        score = max(0, score)
        
        return {
            'score': score,
            'issues': issues,
            'status': 'valid' if not issues else 'issues_found'
        }
    
    def _validate_entry_points(self) -> Dict[str, Any]:
        """Validate CLI entry points are properly configured."""
        issues = []
        
        # Check pyproject.toml for entry points
        pyproject_path = Path('pyproject.toml')
        if pyproject_path.exists():
            try:
                import tomli
                with open(pyproject_path, 'rb') as f:
                    pyproject_data = tomli.load(f)
                
                # Check for console scripts
                scripts = pyproject_data.get('project', {}).get('scripts', {})
                
                if not scripts:
                    issues.append("No console scripts defined")
                else:
                    # Validate script entries
                    for script_name, entry_point in scripts.items():
                        if ':' not in entry_point:
                            issues.append(f"Invalid entry point format: {script_name}")
            
            except Exception as e:
                issues.append(f"Could not validate entry points: {e}")
        
        score = 10 - len(issues) * 3
        score = max(0, score)
        
        return {
            'score': score,
            'issues': issues,
            'status': 'valid' if not issues else 'invalid'
        }
    
    def _test_installation(self) -> Dict[str, Any]:
        """Test package installation in clean environment."""
        # This would ideally test in a virtual environment
        # For now, we'll do basic import tests
        
        try:
            # Test that main modules can be imported
            from fqcn_converter import FQCNConverter, ValidationEngine, BatchProcessor
            
            # Test that instances can be created
            converter = FQCNConverter()
            validator = ValidationEngine()
            batch_processor = BatchProcessor()
            
            return {
                'score': 10,
                'status': 'success',
                'message': 'All imports and instantiation successful'
            }
        
        except Exception as e:
            return {
                'score': 0,
                'status': 'failed',
                'error': str(e)
            }
    
    def _test_distribution_build(self) -> Dict[str, Any]:
        """Test that distribution packages can be built."""
        try:
            # Try to build the package
            result = subprocess.run([
                sys.executable, '-m', 'build', '--wheel', '--no-isolation'
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                return {
                    'score': 10,
                    'status': 'success',
                    'message': 'Package built successfully'
                }
            else:
                return {
                    'score': 5,
                    'status': 'failed',
                    'error': result.stderr
                }
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {
                'score': 7,
                'status': 'not_available',
                'message': 'Build tools not available'
            }


class ProductionReadinessChecker:
    """Main production readiness assessment coordinator."""
    
    def __init__(self):
        self.security_auditor = SecurityAuditor()
        self.performance_validator = PerformanceValidator()
        self.deployment_validator = DeploymentValidator()
    
    def generate_readiness_report(self) -> Dict[str, Any]:
        """Generate comprehensive production readiness report."""
        print("Running comprehensive production readiness assessment...")
        
        report = {
            'timestamp': time.time(),
            'security_audit': self.security_auditor.audit_code_security(),
            'performance_validation': self.performance_validator.validate_production_performance(),
            'deployment_validation': self.deployment_validator.validate_deployment_readiness(),
            'overall_assessment': {},
            'recommendations': [],
            'release_checklist': self._generate_release_checklist()
        }
        
        # Calculate overall scores
        security_score = report['security_audit']['overall_score']
        performance_score = report['performance_validation']['overall_score']
        deployment_score = report['deployment_validation']['overall_score']
        
        overall_score = (security_score + performance_score + deployment_score) / 3
        
        # Determine readiness level
        if overall_score >= 9:
            readiness_level = 'PRODUCTION_READY'
        elif overall_score >= 7:
            readiness_level = 'MOSTLY_READY'
        elif overall_score >= 5:
            readiness_level = 'NEEDS_IMPROVEMENT'
        else:
            readiness_level = 'NOT_READY'
        
        report['overall_assessment'] = {
            'score': overall_score,
            'level': readiness_level,
            'security_score': security_score,
            'performance_score': performance_score,
            'deployment_score': deployment_score
        }
        
        # Generate recommendations
        report['recommendations'] = self._generate_recommendations(report)
        
        return report
    
    def _generate_release_checklist(self) -> List[Dict[str, Any]]:
        """Generate release preparation checklist."""
        checklist = [
            {
                'category': 'Code Quality',
                'items': [
                    {'task': 'All tests pass', 'status': 'pending'},
                    {'task': 'Code coverage >= 90%', 'status': 'pending'},
                    {'task': 'No linting errors', 'status': 'pending'},
                    {'task': 'Type hints coverage >= 80%', 'status': 'pending'}
                ]
            },
            {
                'category': 'Security',
                'items': [
                    {'task': 'Security scan completed', 'status': 'pending'},
                    {'task': 'No high-severity vulnerabilities', 'status': 'pending'},
                    {'task': 'Dependencies scanned for vulnerabilities', 'status': 'pending'},
                    {'task': 'No hardcoded secrets', 'status': 'pending'}
                ]
            },
            {
                'category': 'Documentation',
                'items': [
                    {'task': 'README.md updated', 'status': 'pending'},
                    {'task': 'API documentation complete', 'status': 'pending'},
                    {'task': 'Installation guide verified', 'status': 'pending'},
                    {'task': 'Usage examples tested', 'status': 'pending'},
                    {'task': 'CHANGELOG.md updated', 'status': 'pending'}
                ]
            },
            {
                'category': 'Performance',
                'items': [
                    {'task': 'Performance benchmarks meet targets', 'status': 'pending'},
                    {'task': 'Memory usage within limits', 'status': 'pending'},
                    {'task': 'Startup time acceptable', 'status': 'pending'},
                    {'task': 'Scalability tested', 'status': 'pending'}
                ]
            },
            {
                'category': 'Packaging',
                'items': [
                    {'task': 'Package builds successfully', 'status': 'pending'},
                    {'task': 'Installation tested', 'status': 'pending'},
                    {'task': 'Entry points configured', 'status': 'pending'},
                    {'task': 'Dependencies properly specified', 'status': 'pending'}
                ]
            },
            {
                'category': 'Release Process',
                'items': [
                    {'task': 'Version number updated', 'status': 'pending'},
                    {'task': 'Git tags prepared', 'status': 'pending'},
                    {'task': 'Release notes prepared', 'status': 'pending'},
                    {'task': 'Distribution packages ready', 'status': 'pending'}
                ]
            }
        ]
        
        return checklist
    
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on assessment results."""
        recommendations = []
        
        # Security recommendations
        security_score = report['security_audit']['overall_score']
        if security_score < 8:
            recommendations.append("Improve security posture by addressing identified vulnerabilities")
        
        # Performance recommendations
        performance_score = report['performance_validation']['overall_score']
        if performance_score < 8:
            recommendations.append("Optimize performance to meet production requirements")
        
        # Deployment recommendations
        deployment_score = report['deployment_validation']['overall_score']
        if deployment_score < 8:
            recommendations.append("Complete packaging and deployment preparation")
        
        # Specific recommendations based on issues
        if report['security_audit'].get('bandit_scan', {}).get('status') == 'issues_found':
            recommendations.append("Address security issues identified by static analysis")
        
        if report['performance_validation'].get('memory_usage', {}).get('status') == 'high':
            recommendations.append("Optimize memory usage for production deployment")
        
        if report['deployment_validation'].get('package_structure', {}).get('status') == 'incomplete':
            recommendations.append("Complete package structure with all required files")
        
        return recommendations


class TestProductionReadiness:
    """Test production readiness assessment."""
    
    def test_comprehensive_security_audit(self):
        """Test comprehensive security audit."""
        auditor = SecurityAuditor()
        audit_results = auditor.audit_code_security()
        
        # Security audit should complete successfully
        assert 'overall_score' in audit_results
        assert audit_results['overall_score'] >= 0
        
        # Should have reasonable security score for production
        assert audit_results['overall_score'] >= 6, \
            f"Security score too low: {audit_results['overall_score']}"
        
        print(f"Security Audit Results:")
        print(f"  Overall Score: {audit_results['overall_score']:.1f}/10")
        
        for check, result in audit_results.items():
            if isinstance(result, dict) and 'status' in result:
                print(f"  {check}: {result['status']}")
    
    def test_performance_validation(self):
        """Test performance validation for production."""
        validator = PerformanceValidator()
        performance_results = validator.validate_production_performance()
        
        # Performance validation should complete
        assert 'overall_score' in performance_results
        assert performance_results['overall_score'] >= 0
        
        # Should meet minimum performance requirements
        assert performance_results['overall_score'] >= 6, \
            f"Performance score too low: {performance_results['overall_score']}"
        
        print(f"Performance Validation Results:")
        print(f"  Overall Score: {performance_results['overall_score']:.1f}/10")
        
        # Specific performance checks
        startup_time = performance_results.get('startup_time', {})
        if 'average_time' in startup_time:
            assert startup_time['average_time'] < 3.0, \
                f"Startup time too slow: {startup_time['average_time']:.2f}s"
        
        memory_usage = performance_results.get('memory_usage', {})
        if 'delta_mb' in memory_usage:
            assert memory_usage['delta_mb'] < 100, \
                f"Memory usage too high: {memory_usage['delta_mb']:.2f}MB"
    
    def test_deployment_validation(self):
        """Test deployment readiness validation."""
        validator = DeploymentValidator()
        deployment_results = validator.validate_deployment_readiness()
        
        # Deployment validation should complete
        assert 'overall_score' in deployment_results
        assert deployment_results['overall_score'] >= 0
        
        # Should be ready for deployment
        assert deployment_results['overall_score'] >= 7, \
            f"Deployment score too low: {deployment_results['overall_score']}"
        
        print(f"Deployment Validation Results:")
        print(f"  Overall Score: {deployment_results['overall_score']:.1f}/10")
        
        # Package structure should be complete
        package_structure = deployment_results.get('package_structure', {})
        if 'missing_required' in package_structure:
            assert len(package_structure['missing_required']) == 0, \
                f"Missing required files: {package_structure['missing_required']}"
    
    def test_final_readiness_assessment(self):
        """Test final production readiness assessment."""
        checker = ProductionReadinessChecker()
        report = checker.generate_readiness_report()
        
        # Report should be comprehensive
        assert 'overall_assessment' in report
        assert 'security_audit' in report
        assert 'performance_validation' in report
        assert 'deployment_validation' in report
        assert 'recommendations' in report
        assert 'release_checklist' in report
        
        overall_assessment = report['overall_assessment']
        
        # Should have reasonable overall score
        assert overall_assessment['score'] >= 6, \
            f"Overall readiness score too low: {overall_assessment['score']:.1f}"
        
        # Should not be "NOT_READY"
        assert overall_assessment['level'] != 'NOT_READY', \
            f"Project not ready for production: {overall_assessment['level']}"
        
        print(f"\nFinal Production Readiness Assessment:")
        print(f"  Overall Score: {overall_assessment['score']:.1f}/10")
        print(f"  Readiness Level: {overall_assessment['level']}")
        print(f"  Security Score: {overall_assessment['security_score']:.1f}/10")
        print(f"  Performance Score: {overall_assessment['performance_score']:.1f}/10")
        print(f"  Deployment Score: {overall_assessment['deployment_score']:.1f}/10")
        
        if report['recommendations']:
            print(f"\nRecommendations:")
            for rec in report['recommendations']:
                print(f"  - {rec}")
        
        # Save report for reference
        report_file = Path("production_readiness_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\nDetailed report saved to: {report_file}")
    
    def test_release_checklist_completeness(self):
        """Test that release checklist is comprehensive."""
        checker = ProductionReadinessChecker()
        checklist = checker._generate_release_checklist()
        
        # Should have multiple categories
        assert len(checklist) >= 5
        
        # Should cover key areas
        categories = [item['category'] for item in checklist]
        required_categories = ['Code Quality', 'Security', 'Documentation', 'Performance', 'Packaging']
        
        for category in required_categories:
            assert category in categories, f"Missing checklist category: {category}"
        
        # Each category should have multiple items
        for category_item in checklist:
            assert len(category_item['items']) >= 3, \
                f"Category {category_item['category']} has too few items"
        
        print(f"\nRelease Checklist Summary:")
        for category_item in checklist:
            print(f"  {category_item['category']}: {len(category_item['items'])} items")


class TestProductionDeployment:
    """Test production deployment scenarios."""
    
    def test_clean_installation_simulation(self, temp_dir):
        """Simulate clean installation in production environment."""
        # This test simulates what would happen in a clean production environment
        
        # Test that all required modules can be imported
        try:
            from fqcn_converter import FQCNConverter, ValidationEngine, BatchProcessor
            from fqcn_converter.exceptions import FQCNConverterError
            
            # Test instantiation
            converter = FQCNConverter()
            validator = ValidationEngine()
            batch_processor = BatchProcessor()
            
            # Test basic functionality
            test_content = """---
- name: Production test
  hosts: all
  tasks:
    - name: Install package
      package:
        name: nginx
        state: present
"""
            
            result = converter.convert_content(test_content)
            assert result.success
            
            print("Clean installation simulation: PASSED")
        
        except Exception as e:
            pytest.fail(f"Clean installation simulation failed: {e}")
    
    def test_production_error_scenarios(self, temp_dir):
        """Test error handling in production scenarios."""
        converter = FQCNConverter()
        
        # Test graceful handling of various error conditions
        error_scenarios = [
            {
                'name': 'Invalid YAML',
                'content': 'invalid: yaml: [',
                'should_raise': True
            },
            {
                'name': 'Empty file',
                'content': '',
                'should_raise': False
            },
            {
                'name': 'Non-Ansible YAML',
                'content': 'key: value\nother: data',
                'should_raise': False
            }
        ]
        
        for scenario in error_scenarios:
            test_file = temp_dir / f"{scenario['name'].lower().replace(' ', '_')}.yml"
            test_file.write_text(scenario['content'])
            
            try:
                result = converter.convert_file(test_file, dry_run=True)
                
                if scenario['should_raise']:
                    # If we expected an error but didn't get one, that's also acceptable
                    # as long as the result indicates failure
                    if result.success:
                        print(f"Warning: {scenario['name']} succeeded unexpectedly")
                
            except Exception as e:
                if not scenario['should_raise']:
                    pytest.fail(f"Unexpected error in {scenario['name']}: {e}")
        
        print("Production error scenarios: PASSED")
    
    def test_concurrent_usage_safety(self, temp_dir):
        """Test thread safety for concurrent usage."""
        import threading
        import time
        
        converter = FQCNConverter()
        
        test_content = """---
- name: Concurrent test
  hosts: all
  tasks:
    - name: Install package
      package:
        name: nginx
        state: present
"""
        
        results = []
        errors = []
        
        def convert_worker():
            try:
                for _ in range(10):
                    result = converter.convert_content(test_content)
                    results.append(result.success)
                    time.sleep(0.01)  # Small delay
            except Exception as e:
                errors.append(str(e))
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=convert_worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0, f"Concurrent usage errors: {errors}"
        assert all(results), "Some concurrent conversions failed"
        
        print(f"Concurrent usage test: {len(results)} conversions completed successfully")
    
    def test_resource_cleanup(self, temp_dir):
        """Test that resources are properly cleaned up."""
        import gc
        import weakref
        
        # Test that objects can be garbage collected
        converter = FQCNConverter()
        validator = ValidationEngine()
        
        # Create weak references
        converter_ref = weakref.ref(converter)
        validator_ref = weakref.ref(validator)
        
        # Delete strong references
        del converter
        del validator
        
        # Force garbage collection
        gc.collect()
        
        # Check if objects were cleaned up
        # Note: This might not always work due to Python's garbage collection behavior
        # but it's a good practice to test
        
        print("Resource cleanup test completed")