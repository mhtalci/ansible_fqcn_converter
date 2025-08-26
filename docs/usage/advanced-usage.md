# Advanced Usage Guide

[![Production Ready](https://img.shields.io/badge/status-production--ready-brightgreen)](https://github.com/mhtalci/ansible_fqcn_converter)
[![Test Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/mhtalci/ansible_fqcn_converter/actions)

Comprehensive guide for advanced usage patterns, enterprise features, and complex scenarios with the FQCN Converter.

## Advanced CLI Usage

### Complex Batch Operations

#### Multi-Project Processing with Custom Patterns

```bash
# Process multiple project types with different patterns
fqcn-converter batch \
  --project-pattern "**/ansible/**" \
  --project-pattern "**/playbooks/**" \
  --exclude-pattern "**/test/**" \
  --exclude-pattern "**/archive/**" \
  --workers 8 \
  --report comprehensive_report.json \
  /enterprise/infrastructure

# Process with custom configuration per project type
fqcn-converter batch \
  --config enterprise_config.yml \
  --project-pattern "**/production/**" \
  --workers 4 \
  --continue-on-error \
  --validate \
  /production/ansible/projects
```

#### Advanced Filtering and Selection

```bash
# Process only recently modified files
find /ansible/projects -name "*.yml" -mtime -7 | \
  xargs fqcn-converter convert --report recent_changes.json

# Process files based on content analysis
grep -l "hosts:" /ansible/**/*.yml | \
  xargs fqcn-converter convert --dry-run --verbose

# Selective processing with complex patterns
fqcn-converter convert \
  --include "playbooks/**/*.yml" \
  --include "roles/**/tasks/*.yml" \
  --exclude "**/test_*.yml" \
  --exclude "**/molecule/**" \
  --config production_mappings.yml \
  /enterprise/ansible
```

### Performance Optimization

#### Memory-Optimized Processing

```bash
# Process large projects with memory constraints
export PYTHONOPTIMIZE=1
export FQCN_MEMORY_LIMIT=100MB

fqcn-converter batch \
  --workers 2 \
  --chunk-size 50 \
  --memory-efficient \
  /large/ansible/infrastructure

# Stream processing for very large files
fqcn-converter convert \
  --stream-mode \
  --buffer-size 8192 \
  large_playbook.yml
```

#### High-Performance Batch Processing

```bash
# Maximize throughput for large-scale operations
fqcn-converter batch \
  --workers $(nproc) \
  --parallel-io \
  --cache-mappings \
  --skip-validation \
  --report performance_metrics.json \
  /massive/ansible/codebase

# Distributed processing across multiple machines
fqcn-converter batch \
  --distributed \
  --coordinator-host coordinator.example.com \
  --worker-id worker-01 \
  --shard 1/4 \
  /distributed/ansible/projects
```

## Advanced Python API Usage

### Enterprise Integration Patterns

#### Custom Converter with Enterprise Features

```python
from fqcn_converter import FQCNConverter, ValidationEngine, BatchProcessor
from fqcn_converter.config.manager import ConfigurationManager
import logging
import json
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from pathlib import Path

@dataclass
class EnterpriseConfig:
    """Enterprise configuration settings."""
    audit_logging: bool = True
    compliance_reporting: bool = True
    custom_mappings_path: str = "/etc/fqcn/enterprise_mappings.yml"
    approval_workflow: bool = False
    backup_retention_days: int = 30
    notification_webhooks: List[str] = None

class EnterpriseConverter:
    """Enterprise-grade FQCN converter with advanced features."""
    
    def __init__(self, config: EnterpriseConfig):
        self.config = config
        self.converter = FQCNConverter(config_path=config.custom_mappings_path)
        self.validator = ValidationEngine(strict_mode=True)
        self.audit_logger = self._setup_audit_logging()
        self.compliance_tracker = ComplianceTracker()
    
    def _setup_audit_logging(self) -> logging.Logger:
        """Setup enterprise audit logging."""
        logger = logging.getLogger("fqcn_converter.enterprise.audit")
        handler = logging.FileHandler("/var/log/fqcn/audit.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(user)s - %(action)s - %(details)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
    
    def convert_with_approval(self, file_path: str, 
                            approver: str = None) -> ConversionResult:
        """Convert file with approval workflow."""
        # Pre-conversion validation
        validation_result = self.validator.validate_file(file_path)
        
        if self.config.approval_workflow and validation_result.score < 0.8:
            approval = self._request_approval(file_path, validation_result, approver)
            if not approval.approved:
                return ConversionResult(
                    success=False,
                    errors=[f"Approval required but not granted: {approval.reason}"]
                )
        
        # Perform conversion
        result = self.converter.convert_file(file_path)
        
        # Audit logging
        if self.config.audit_logging:
            self._log_conversion_audit(file_path, result, approver)
        
        # Compliance tracking
        if self.config.compliance_reporting:
            self.compliance_tracker.track_conversion(file_path, result)
        
        return result
    
    def _request_approval(self, file_path: str, validation_result: ValidationResult,
                         approver: str) -> ApprovalResult:
        """Request approval for conversion."""
        approval_request = {
            "file_path": file_path,
            "compliance_score": validation_result.score,
            "issues": [issue.message for issue in validation_result.issues],
            "approver": approver,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to approval system (webhook, API, etc.)
        response = self._send_approval_request(approval_request)
        
        return ApprovalResult(
            approved=response.get("approved", False),
            reason=response.get("reason", "No reason provided"),
            approver=response.get("approver", approver)
        )
    
    def _log_conversion_audit(self, file_path: str, result: ConversionResult,
                            approver: str = None):
        """Log conversion for audit purposes."""
        audit_entry = {
            "action": "fqcn_conversion",
            "file_path": file_path,
            "success": result.success,
            "changes_made": result.changes_made,
            "approver": approver,
            "timestamp": datetime.utcnow().isoformat(),
            "user": os.getenv("USER", "unknown")
        }
        
        self.audit_logger.info(json.dumps(audit_entry))

class ComplianceTracker:
    """Track FQCN compliance across the organization."""
    
    def __init__(self):
        self.compliance_db = ComplianceDatabase()
    
    def track_conversion(self, file_path: str, result: ConversionResult):
        """Track conversion for compliance reporting."""
        compliance_record = {
            "file_path": file_path,
            "conversion_date": datetime.utcnow(),
            "success": result.success,
            "changes_made": result.changes_made,
            "compliance_improved": result.changes_made > 0
        }
        
        self.compliance_db.insert_record(compliance_record)
    
    def generate_compliance_report(self, start_date: datetime, 
                                 end_date: datetime) -> ComplianceReport:
        """Generate compliance report for specified period."""
        records = self.compliance_db.get_records(start_date, end_date)
        
        return ComplianceReport(
            total_files_processed=len(records),
            successful_conversions=sum(1 for r in records if r["success"]),
            total_changes_made=sum(r["changes_made"] for r in records),
            compliance_improvement_rate=self._calculate_improvement_rate(records),
            period_start=start_date,
            period_end=end_date
        )
```

#### Advanced Batch Processing with Monitoring

```python
import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import AsyncGenerator, Dict, List
import psutil
import time

class AdvancedBatchProcessor:
    """Advanced batch processor with monitoring and optimization."""
    
    def __init__(self, max_workers: int = None, 
                 memory_limit_mb: int = 500,
                 progress_callback: Callable = None):
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.memory_limit_mb = memory_limit_mb
        self.progress_callback = progress_callback
        self.metrics = ProcessingMetrics()
        self.resource_monitor = ResourceMonitor(memory_limit_mb)
    
    async def process_projects_async(self, project_paths: List[str]) -> BatchResult:
        """Process projects asynchronously with resource monitoring."""
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def process_single_project(project_path: str) -> ConversionResult:
            async with semaphore:
                # Check resource usage before processing
                if not await self.resource_monitor.check_resources():
                    await self.resource_monitor.wait_for_resources()
                
                return await self._process_project_async(project_path)
        
        # Start resource monitoring
        monitor_task = asyncio.create_task(self.resource_monitor.start_monitoring())
        
        try:
            # Process all projects
            tasks = [process_single_project(path) for path in project_paths]
            results = []
            
            for i, task in enumerate(asyncio.as_completed(tasks)):
                result = await task
                results.append(result)
                
                # Update progress
                if self.progress_callback:
                    self.progress_callback(i + 1, len(tasks), result.file_path)
                
                # Update metrics
                self.metrics.record_result(result)
            
            return BatchResult(
                total_projects=len(project_paths),
                successful_projects=sum(1 for r in results if r.success),
                failed_projects=sum(1 for r in results if not r.success),
                project_results={r.file_path: r for r in results},
                processing_time=self.metrics.total_processing_time,
                total_changes=sum(r.changes_made for r in results)
            )
        
        finally:
            # Stop resource monitoring
            monitor_task.cancel()
    
    async def _process_project_async(self, project_path: str) -> ConversionResult:
        """Process single project asynchronously."""
        loop = asyncio.get_event_loop()
        
        # Run CPU-intensive work in thread pool
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._process_project_sync, project_path)
            return await loop.run_in_executor(None, future.result)
    
    def _process_project_sync(self, project_path: str) -> ConversionResult:
        """Synchronous project processing."""
        converter = FQCNConverter()
        return converter.convert_directory(project_path)

class ResourceMonitor:
    """Monitor system resources during processing."""
    
    def __init__(self, memory_limit_mb: int):
        self.memory_limit_mb = memory_limit_mb
        self.monitoring = False
        self.metrics_history = []
    
    async def check_resources(self) -> bool:
        """Check if resources are available for processing."""
        memory_usage = psutil.virtual_memory().percent
        cpu_usage = psutil.cpu_percent(interval=1)
        
        return (memory_usage < 80 and  # Less than 80% memory usage
                cpu_usage < 90)        # Less than 90% CPU usage
    
    async def wait_for_resources(self, timeout: int = 300):
        """Wait for resources to become available."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if await self.check_resources():
                return
            
            await asyncio.sleep(5)  # Check every 5 seconds
        
        raise ResourceError("Timeout waiting for resources")
    
    async def start_monitoring(self):
        """Start continuous resource monitoring."""
        self.monitoring = True
        
        while self.monitoring:
            metrics = {
                "timestamp": time.time(),
                "memory_percent": psutil.virtual_memory().percent,
                "memory_mb": psutil.virtual_memory().used / 1024 / 1024,
                "cpu_percent": psutil.cpu_percent(),
                "disk_io": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {}
            }
            
            self.metrics_history.append(metrics)
            
            # Keep only last hour of metrics
            cutoff_time = time.time() - 3600
            self.metrics_history = [
                m for m in self.metrics_history 
                if m["timestamp"] > cutoff_time
            ]
            
            await asyncio.sleep(10)  # Monitor every 10 seconds
```

### Custom Validation and Rules

#### Enterprise Validation Rules

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import re

class ValidationRule(ABC):
    """Abstract base class for custom validation rules."""
    
    @abstractmethod
    def validate(self, content: str, file_path: str) -> List[ValidationIssue]:
        """Validate content against this rule."""
        pass
    
    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Unique identifier for this rule."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of this rule."""
        pass

class EnterpriseSecurityRule(ValidationRule):
    """Validate security-related FQCN usage."""
    
    @property
    def rule_id(self) -> str:
        return "enterprise_security_001"
    
    @property
    def description(self) -> str:
        return "Ensure security-sensitive modules use FQCN"
    
    def validate(self, content: str, file_path: str) -> List[ValidationIssue]:
        """Validate security module usage."""
        issues = []
        security_modules = [
            "user", "group", "authorized_key", "sudo", "selinux",
            "firewalld", "iptables", "ufw", "ssh_config"
        ]
        
        lines = content.splitlines()
        for line_num, line in enumerate(lines, 1):
            for module in security_modules:
                # Check for short name usage
                pattern = rf'^\s*-\s*{module}:'
                if re.match(pattern, line.strip()):
                    # Check if it's already FQCN
                    if not any(collection in line for collection in 
                              ["ansible.builtin", "community.", "ansible.posix"]):
                        issues.append(ValidationIssue(
                            line=line_num,
                            column=line.find(module),
                            severity="error",
                            message=f"Security module '{module}' must use FQCN",
                            rule_id=self.rule_id,
                            suggested_fix=f"Use ansible.builtin.{module} or appropriate collection FQCN"
                        ))
        
        return issues

class ComplianceValidationRule(ValidationRule):
    """Validate compliance with organizational standards."""
    
    def __init__(self, compliance_config: Dict[str, Any]):
        self.compliance_config = compliance_config
    
    @property
    def rule_id(self) -> str:
        return "compliance_001"
    
    @property
    def description(self) -> str:
        return "Validate compliance with organizational FQCN standards"
    
    def validate(self, content: str, file_path: str) -> List[ValidationIssue]:
        """Validate organizational compliance."""
        issues = []
        
        # Check for required collections
        required_collections = self.compliance_config.get("required_collections", [])
        forbidden_collections = self.compliance_config.get("forbidden_collections", [])
        
        for line_num, line in enumerate(content.splitlines(), 1):
            # Check for forbidden collections
            for forbidden in forbidden_collections:
                if forbidden in line:
                    issues.append(ValidationIssue(
                        line=line_num,
                        column=line.find(forbidden),
                        severity="error",
                        message=f"Forbidden collection '{forbidden}' detected",
                        rule_id=self.rule_id,
                        suggested_fix="Use approved collections only"
                    ))
        
        return issues

class CustomValidationEngine(ValidationEngine):
    """Extended validation engine with custom rules."""
    
    def __init__(self, custom_rules: List[ValidationRule] = None):
        super().__init__()
        self.custom_rules = custom_rules or []
    
    def validate_with_custom_rules(self, content: str, 
                                 file_path: str) -> ValidationResult:
        """Validate content with both standard and custom rules."""
        # Run standard validation
        standard_result = self.validate_content(content, file_path)
        
        # Run custom rules
        custom_issues = []
        for rule in self.custom_rules:
            try:
                rule_issues = rule.validate(content, file_path)
                custom_issues.extend(rule_issues)
            except Exception as e:
                # Log rule execution error but continue
                logging.warning(f"Custom rule {rule.rule_id} failed: {e}")
        
        # Combine results
        all_issues = standard_result.issues + custom_issues
        
        return ValidationResult(
            valid=len([i for i in all_issues if i.severity == "error"]) == 0,
            score=self._calculate_score_with_custom_issues(all_issues),
            issues=all_issues,
            total_modules=standard_result.total_modules,
            fqcn_modules=standard_result.fqcn_modules,
            file_path=file_path,
            processing_time=standard_result.processing_time
        )
```

## Enterprise Configuration Management

### Centralized Configuration

```yaml
# /etc/fqcn/enterprise_config.yml
enterprise:
  organization: "ACME Corp"
  compliance_level: "strict"
  audit_logging: true
  approval_workflow: true
  
mappings:
  # Standard mappings
  package: "ansible.builtin.package"
  service: "ansible.builtin.service"
  
  # Organization-specific mappings
  acme_deploy: "acme.internal.deploy"
  acme_monitor: "acme.internal.monitor"
  
  # Third-party integrations
  datadog_monitor: "datadog.datadog.monitor"
  newrelic_deployment: "newrelic.newrelic.deployment"

collections:
  approved:
    - "ansible.builtin"
    - "ansible.posix"
    - "community.general"
    - "acme.internal"
    - "datadog.datadog"
  
  forbidden:
    - "community.crypto"  # Security policy
    - "community.docker"  # Use internal container solution

validation:
  rules:
    - rule_id: "security_001"
      enabled: true
      severity: "error"
      description: "Security modules must use FQCN"
    
    - rule_id: "compliance_001"
      enabled: true
      severity: "warning"
      description: "Organizational compliance check"

reporting:
  compliance_reports: true
  audit_retention_days: 365
  notification_webhooks:
    - "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
    - "https://api.pagerduty.com/integration_keys/XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

performance:
  max_workers: 8
  memory_limit_mb: 1000
  timeout_seconds: 300
  cache_enabled: true
```

### Dynamic Configuration Loading

```python
import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path

class EnterpriseConfigManager:
    """Manage enterprise configuration with multiple sources."""
    
    def __init__(self):
        self.config_sources = [
            "/etc/fqcn/enterprise_config.yml",
            "~/.fqcn/config.yml",
            "./fqcn_config.yml",
            os.getenv("FQCN_CONFIG_PATH")
        ]
        self.config = self._load_merged_config()
    
    def _load_merged_config(self) -> Dict[str, Any]:
        """Load and merge configuration from multiple sources."""
        merged_config = {}
        
        for config_path in self.config_sources:
            if config_path and Path(config_path).exists():
                try:
                    with open(config_path) as f:
                        config = yaml.safe_load(f)
                    
                    # Deep merge configurations
                    merged_config = self._deep_merge(merged_config, config)
                    
                except Exception as e:
                    logging.warning(f"Failed to load config {config_path}: {e}")
        
        # Apply environment variable overrides
        self._apply_env_overrides(merged_config)
        
        return merged_config
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self, config: Dict[str, Any]):
        """Apply environment variable overrides."""
        env_mappings = {
            "FQCN_MAX_WORKERS": ("performance", "max_workers"),
            "FQCN_MEMORY_LIMIT": ("performance", "memory_limit_mb"),
            "FQCN_AUDIT_ENABLED": ("enterprise", "audit_logging"),
            "FQCN_COMPLIANCE_LEVEL": ("enterprise", "compliance_level")
        }
        
        for env_var, (section, key) in env_mappings.items():
            if env_var in os.environ:
                if section not in config:
                    config[section] = {}
                
                value = os.environ[env_var]
                # Type conversion
                if key in ["max_workers", "memory_limit_mb"]:
                    value = int(value)
                elif key in ["audit_logging"]:
                    value = value.lower() in ["true", "1", "yes"]
                
                config[section][key] = value
    
    def get_mappings(self) -> Dict[str, str]:
        """Get module mappings from configuration."""
        return self.config.get("mappings", {})
    
    def get_validation_rules(self) -> List[Dict[str, Any]]:
        """Get validation rules configuration."""
        return self.config.get("validation", {}).get("rules", [])
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration."""
        return self.config.get("performance", {})
    
    def is_collection_approved(self, collection_name: str) -> bool:
        """Check if collection is approved for use."""
        approved = self.config.get("collections", {}).get("approved", [])
        forbidden = self.config.get("collections", {}).get("forbidden", [])
        
        if collection_name in forbidden:
            return False
        
        if not approved:  # No restrictions if no approved list
            return True
        
        return collection_name in approved
```

## CI/CD Integration Patterns

### Advanced GitHub Actions Integration

```yaml
# .github/workflows/enterprise-fqcn-validation.yml
name: Enterprise FQCN Validation

on:
  push:
    branches: [ main, develop, 'release/*' ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * 1'  # Weekly compliance check

env:
  FQCN_CONFIG_PATH: .github/fqcn-enterprise-config.yml
  FQCN_COMPLIANCE_LEVEL: strict
  FQCN_AUDIT_ENABLED: true

jobs:
  compliance-check:
    runs-on: ubuntu-latest
    outputs:
      compliance-score: ${{ steps.validate.outputs.compliance-score }}
      changes-needed: ${{ steps.validate.outputs.changes-needed }}
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0  # Full history for compliance tracking
    
    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install FQCN Converter
      run: |
        python -m pip install --upgrade pip
        pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git
    
    - name: Validate FQCN Compliance
      id: validate
      run: |
        # Run validation with enterprise config
        fqcn-converter validate \
          --config $FQCN_CONFIG_PATH \
          --strict \
          --report compliance-report.json \
          --format json \
          .
        
        # Extract metrics
        COMPLIANCE_SCORE=$(jq -r '.overall_score' compliance-report.json)
        CHANGES_NEEDED=$(jq -r '.total_issues' compliance-report.json)
        
        echo "compliance-score=$COMPLIANCE_SCORE" >> $GITHUB_OUTPUT
        echo "changes-needed=$CHANGES_NEEDED" >> $GITHUB_OUTPUT
        
        # Set status based on compliance
        if (( $(echo "$COMPLIANCE_SCORE < 0.95" | bc -l) )); then
          echo "❌ Compliance check failed: $COMPLIANCE_SCORE < 95%"
          exit 1
        else
          echo "✅ Compliance check passed: $COMPLIANCE_SCORE >= 95%"
        fi
    
    - name: Upload Compliance Report
      uses: actions/upload-artifact@v4
      with:
        name: compliance-report
        path: compliance-report.json
        retention-days: 90
    
    - name: Comment PR with Compliance Status
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v7
      with:
        script: |
          const fs = require('fs');
          const report = JSON.parse(fs.readFileSync('compliance-report.json', 'utf8'));
          
          const comment = `## 🔍 FQCN Compliance Report
          
          **Compliance Score:** ${(report.overall_score * 100).toFixed(1)}%
          **Issues Found:** ${report.total_issues}
          **Files Processed:** ${report.files_processed}
          
          ${report.overall_score >= 0.95 ? '✅ **PASSED**' : '❌ **FAILED**'} - Minimum 95% compliance required
          
          ### Summary by Severity
          - **Errors:** ${report.issues_by_severity.error || 0}
          - **Warnings:** ${report.issues_by_severity.warning || 0}
          - **Info:** ${report.issues_by_severity.info || 0}
          
          <details>
          <summary>View Detailed Report</summary>
          
          \`\`\`json
          ${JSON.stringify(report, null, 2)}
          \`\`\`
          </details>`;
          
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: comment
          });

  auto-conversion:
    runs-on: ubuntu-latest
    needs: compliance-check
    if: needs.compliance-check.outputs.changes-needed > 0 && github.event_name == 'pull_request'
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        token: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install FQCN Converter
      run: |
        pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git
    
    - name: Auto-convert FQCN Issues
      run: |
        # Convert with enterprise configuration
        fqcn-converter convert \
          --config $FQCN_CONFIG_PATH \
          --report auto-conversion-report.json \
          .
    
    - name: Commit Auto-conversion Changes
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        
        if [[ -n $(git status --porcelain) ]]; then
          git add .
          git commit -m "🤖 Auto-convert to FQCN format
          
          - Applied enterprise FQCN conversion rules
          - Improved compliance score
          - Automated by GitHub Actions"
          
          git push
        else
          echo "No changes to commit"
        fi

  security-scan:
    runs-on: ubuntu-latest
    needs: compliance-check
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Security Scan for FQCN Usage
      run: |
        # Custom security scan for FQCN compliance
        python .github/scripts/security-fqcn-scan.py \
          --report security-fqcn-report.json \
          --fail-on-issues
    
    - name: Upload Security Report
      uses: actions/upload-artifact@v4
      with:
        name: security-fqcn-report
        path: security-fqcn-report.json

  notification:
    runs-on: ubuntu-latest
    needs: [compliance-check, auto-conversion, security-scan]
    if: always()
    
    steps:
    - name: Notify Compliance Team
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        channel: '#ansible-compliance'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
        fields: repo,message,commit,author,action,eventName,ref,workflow
        custom_payload: |
          {
            "text": "FQCN Compliance Check Complete",
            "attachments": [{
              "color": "${{ needs.compliance-check.outputs.compliance-score >= 0.95 && 'good' || 'danger' }}",
              "fields": [{
                "title": "Compliance Score",
                "value": "${{ needs.compliance-check.outputs.compliance-score }}%",
                "short": true
              }, {
                "title": "Changes Needed",
                "value": "${{ needs.compliance-check.outputs.changes-needed }}",
                "short": true
              }]
            }]
          }
```

### Jenkins Pipeline Integration

```groovy
// Jenkinsfile for Enterprise FQCN Validation
pipeline {
    agent any
    
    environment {
        FQCN_CONFIG_PATH = 'jenkins/fqcn-enterprise-config.yml'
        FQCN_COMPLIANCE_THRESHOLD = '95'
        PYTHON_VERSION = '3.11'
    }
    
    stages {
        stage('Setup') {
            steps {
                script {
                    // Setup Python environment
                    sh '''
                        python${PYTHON_VERSION} -m venv fqcn-env
                        . fqcn-env/bin/activate
                        pip install --upgrade pip
                        pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git
                    '''
                }
            }
        }
        
        stage('FQCN Compliance Check') {
            steps {
                script {
                    sh '''
                        . fqcn-env/bin/activate
                        
                        # Run compliance validation
                        fqcn-converter validate \
                            --config ${FQCN_CONFIG_PATH} \
                            --strict \
                            --report compliance-report.json \
                            --format json \
                            .
                        
                        # Check compliance threshold
                        COMPLIANCE_SCORE=$(jq -r '.overall_score * 100' compliance-report.json)
                        
                        if (( $(echo "$COMPLIANCE_SCORE < $FQCN_COMPLIANCE_THRESHOLD" | bc -l) )); then
                            echo "❌ Compliance check failed: $COMPLIANCE_SCORE% < $FQCN_COMPLIANCE_THRESHOLD%"
                            exit 1
                        else
                            echo "✅ Compliance check passed: $COMPLIANCE_SCORE% >= $FQCN_COMPLIANCE_THRESHOLD%"
                        fi
                    '''
                }
            }
            
            post {
                always {
                    // Archive compliance report
                    archiveArtifacts artifacts: 'compliance-report.json', fingerprint: true
                    
                    // Publish test results
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: '.',
                        reportFiles: 'compliance-report.json',
                        reportName: 'FQCN Compliance Report'
                    ])
                }
            }
        }
        
        stage('Auto-Conversion') {
            when {
                anyOf {
                    branch 'develop'
                    changeRequest()
                }
            }
            
            steps {
                script {
                    sh '''
                        . fqcn-env/bin/activate
                        
                        # Perform auto-conversion
                        fqcn-converter convert \
                            --config ${FQCN_CONFIG_PATH} \
                            --report conversion-report.json \
                            .
                        
                        # Check if changes were made
                        CHANGES_MADE=$(jq -r '.total_changes' conversion-report.json)
                        
                        if [ "$CHANGES_MADE" -gt 0 ]; then
                            echo "✅ Auto-conversion completed: $CHANGES_MADE changes made"
                            
                            # Commit changes if on develop branch
                            if [ "$BRANCH_NAME" = "develop" ]; then
                                git config user.email "jenkins@company.com"
                                git config user.name "Jenkins CI"
                                git add .
                                git commit -m "🤖 Auto-convert to FQCN format [skip ci]"
                                git push origin develop
                            fi
                        else
                            echo "ℹ️ No auto-conversion needed"
                        fi
                    '''
                }
            }
        }
        
        stage('Security Validation') {
            steps {
                script {
                    sh '''
                        . fqcn-env/bin/activate
                        
                        # Run security-focused validation
                        python jenkins/scripts/security-fqcn-validation.py \
                            --config ${FQCN_CONFIG_PATH} \
                            --report security-validation-report.json
                    '''
                }
            }
            
            post {
                always {
                    archiveArtifacts artifacts: 'security-validation-report.json'
                }
            }
        }
    }
    
    post {
        always {
            // Clean up
            sh 'rm -rf fqcn-env'
        }
        
        success {
            // Notify success
            slackSend(
                channel: '#ansible-compliance',
                color: 'good',
                message: "✅ FQCN Compliance check passed for ${env.JOB_NAME} - ${env.BUILD_NUMBER}"
            )
        }
        
        failure {
            // Notify failure
            slackSend(
                channel: '#ansible-compliance',
                color: 'danger',
                message: "❌ FQCN Compliance check failed for ${env.JOB_NAME} - ${env.BUILD_NUMBER}"
            )
        }
    }
}
```

## Monitoring and Observability

### Metrics Collection

```python
import time
import json
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

@dataclass
class ConversionMetrics:
    """Comprehensive conversion metrics."""
    timestamp: datetime
    operation_type: str  # 'convert', 'validate', 'batch'
    files_processed: int
    changes_made: int
    processing_time_seconds: float
    memory_usage_mb: float
    cpu_usage_percent: float
    success_rate: float
    error_count: int
    warning_count: int

class MetricsCollector:
    """Collect and export metrics for monitoring."""
    
    def __init__(self, export_interval: int = 300):  # 5 minutes
        self.metrics_buffer: List[ConversionMetrics] = []
        self.export_interval = export_interval
        self.last_export = time.time()
    
    def record_conversion(self, operation_type: str, files_processed: int,
                         changes_made: int, processing_time: float,
                         memory_usage: float, cpu_usage: float,
                         errors: int = 0, warnings: int = 0):
        """Record conversion metrics."""
        metrics = ConversionMetrics(
            timestamp=datetime.utcnow(),
            operation_type=operation_type,
            files_processed=files_processed,
            changes_made=changes_made,
            processing_time_seconds=processing_time,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            success_rate=1.0 if errors == 0 else 0.0,
            error_count=errors,
            warning_count=warnings
        )
        
        self.metrics_buffer.append(metrics)
        
        # Export if interval reached
        if time.time() - self.last_export > self.export_interval:
            self.export_metrics()
    
    def export_metrics(self):
        """Export metrics to monitoring system."""
        if not self.metrics_buffer:
            return
        
        # Export to Prometheus
        self._export_to_prometheus()
        
        # Export to DataDog
        self._export_to_datadog()
        
        # Export to CloudWatch
        self._export_to_cloudwatch()
        
        # Clear buffer
        self.metrics_buffer.clear()
        self.last_export = time.time()
    
    def _export_to_prometheus(self):
        """Export metrics to Prometheus."""
        try:
            from prometheus_client import CollectorRegistry, Gauge, Counter, push_to_gateway
            
            registry = CollectorRegistry()
            
            # Define metrics
            files_processed = Gauge('fqcn_files_processed_total', 
                                  'Total files processed', registry=registry)
            changes_made = Gauge('fqcn_changes_made_total',
                               'Total changes made', registry=registry)
            processing_time = Gauge('fqcn_processing_time_seconds',
                                  'Processing time in seconds', registry=registry)
            memory_usage = Gauge('fqcn_memory_usage_mb',
                               'Memory usage in MB', registry=registry)
            
            # Aggregate metrics
            total_files = sum(m.files_processed for m in self.metrics_buffer)
            total_changes = sum(m.changes_made for m in self.metrics_buffer)
            avg_processing_time = sum(m.processing_time_seconds for m in self.metrics_buffer) / len(self.metrics_buffer)
            avg_memory = sum(m.memory_usage_mb for m in self.metrics_buffer) / len(self.metrics_buffer)
            
            # Set values
            files_processed.set(total_files)
            changes_made.set(total_changes)
            processing_time.set(avg_processing_time)
            memory_usage.set(avg_memory)
            
            # Push to gateway
            push_to_gateway('prometheus-pushgateway:9091', job='fqcn-converter', registry=registry)
            
        except ImportError:
            logging.warning("Prometheus client not available")
        except Exception as e:
            logging.error(f"Failed to export to Prometheus: {e}")
    
    def _export_to_datadog(self):
        """Export metrics to DataDog."""
        try:
            from datadog import initialize, statsd
            
            # Initialize DataDog
            initialize()
            
            for metrics in self.metrics_buffer:
                # Send metrics
                statsd.gauge('fqcn.files_processed', metrics.files_processed)
                statsd.gauge('fqcn.changes_made', metrics.changes_made)
                statsd.gauge('fqcn.processing_time', metrics.processing_time_seconds)
                statsd.gauge('fqcn.memory_usage', metrics.memory_usage_mb)
                statsd.gauge('fqcn.success_rate', metrics.success_rate)
                
                # Send with tags
                tags = [f'operation:{metrics.operation_type}']
                statsd.increment('fqcn.operations_total', tags=tags)
                
        except ImportError:
            logging.warning("DataDog client not available")
        except Exception as e:
            logging.error(f"Failed to export to DataDog: {e}")
    
    def _export_to_cloudwatch(self):
        """Export metrics to AWS CloudWatch."""
        try:
            import boto3
            
            cloudwatch = boto3.client('cloudwatch')
            
            metric_data = []
            for metrics in self.metrics_buffer:
                metric_data.extend([
                    {
                        'MetricName': 'FilesProcessed',
                        'Value': metrics.files_processed,
                        'Unit': 'Count',
                        'Timestamp': metrics.timestamp
                    },
                    {
                        'MetricName': 'ChangesMade',
                        'Value': metrics.changes_made,
                        'Unit': 'Count',
                        'Timestamp': metrics.timestamp
                    },
                    {
                        'MetricName': 'ProcessingTime',
                        'Value': metrics.processing_time_seconds,
                        'Unit': 'Seconds',
                        'Timestamp': metrics.timestamp
                    },
                    {
                        'MetricName': 'MemoryUsage',
                        'Value': metrics.memory_usage_mb,
                        'Unit': 'Megabytes',
                        'Timestamp': metrics.timestamp
                    }
                ])
            
            # Send metrics in batches
            for i in range(0, len(metric_data), 20):  # CloudWatch limit
                batch = metric_data[i:i+20]
                cloudwatch.put_metric_data(
                    Namespace='FQCN/Converter',
                    MetricData=batch
                )
                
        except ImportError:
            logging.warning("Boto3 not available for CloudWatch")
        except Exception as e:
            logging.error(f"Failed to export to CloudWatch: {e}")
```

## Conclusion

This advanced usage guide covers enterprise-grade features and patterns for the FQCN Converter, including:

- **Complex batch operations** with custom patterns and filtering
- **Enterprise integration patterns** with audit logging and compliance tracking
- **Custom validation rules** for organizational standards
- **Centralized configuration management** with multiple sources
- **Advanced CI/CD integration** for automated compliance
- **Comprehensive monitoring** with metrics collection and export

These patterns enable organizations to deploy the FQCN Converter at scale while maintaining security, compliance, and operational visibility.

For additional enterprise features or custom integration support, please contact our team or open a discussion in our [GitHub repository](https://github.com/mhtalci/ansible_fqcn_converter/discussions).