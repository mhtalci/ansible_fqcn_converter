"""
Exception hierarchy for FQCN Converter.

This module defines all custom exceptions used throughout the package
with clear error categorization, actionable error messages, and recovery mechanisms.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Union


class FQCNConverterError(Exception):
    """
    Base exception for all converter errors.

    Provides structured error information with actionable guidance
    and recovery suggestions for graceful degradation.
    """

    def __init__(
        self,
        message: str,
        details: str = "",
        suggestions: Optional[List[str]] = None,
        recovery_actions: Optional[List[str]] = None,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.details = details
        self.suggestions = suggestions or []
        self.recovery_actions = recovery_actions or []
        self.error_code = error_code
        self.context = context or {}

        # Build comprehensive error message
        full_message = self._build_error_message()
        super().__init__(full_message)

    def _build_error_message(self) -> str:
        """Build a comprehensive error message with actionable guidance."""
        parts = [self.message]

        if self.details:
            parts.append(f"\nDetails: {self.details}")

        if self.error_code:
            parts.append(f"\nError Code: {self.error_code}")

        if self.suggestions:
            parts.append("\nSuggestions:")
            for i, suggestion in enumerate(self.suggestions, 1):
                parts.append(f"  {i}. {suggestion}")

        if self.recovery_actions:
            parts.append("\nRecovery Actions:")
            for i, action in enumerate(self.recovery_actions, 1):
                parts.append(f"  {i}. {action}")

        if self.context:
            parts.append(f"\nContext: {self.context}")

        return "".join(parts)

    def get_recovery_suggestions(self) -> List[str]:
        """Get list of recovery suggestions for graceful degradation."""
        return self.recovery_actions

    def can_recover(self) -> bool:
        """Check if this error has recovery actions available."""
        return bool(self.recovery_actions)


class ConfigurationError(FQCNConverterError):
    """
    Raised when configuration is invalid or missing.

    Provides specific guidance for configuration issues and fallback options.
    """

    def __init__(
        self,
        message: str,
        config_path: Optional[str] = None,
        missing_keys: Optional[List[str]] = None,
        invalid_values: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> None:
        # Build detailed error information
        details_parts = []
        suggestions = []
        recovery_actions = []

        if config_path:
            details_parts.append(f"Configuration file: {config_path}")
            if not os.path.exists(config_path):
                suggestions.append(f"Create configuration file at: {config_path}")
                recovery_actions.append("Use default configuration mappings")
            else:
                suggestions.append(f"Check file permissions for: {config_path}")

        if missing_keys:
            details_parts.append(f"Missing required keys: {', '.join(missing_keys)}")
            suggestions.extend(
                [f"Add missing key '{key}' to configuration" for key in missing_keys]
            )

        if invalid_values:
            for key, issue in invalid_values.items():
                details_parts.append(f"Invalid value for '{key}': {issue}")
                suggestions.append(f"Fix value for '{key}' in configuration")

        # Always provide recovery actions
        recovery_actions.extend(
            [
                "Continue with default FQCN mappings",
                "Skip custom configuration and use built-in mappings",
                "Generate a sample configuration file",
            ]
        )

        # Filter out conflicting parameters from kwargs
        filtered_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "message",
                "details",
                "suggestions",
                "recovery_actions",
                "error_code",
                "context",
            ]
        }

        super().__init__(
            message=message,
            details="; ".join(details_parts),
            suggestions=suggestions,
            recovery_actions=recovery_actions,
            error_code="CONFIG_ERROR",
            context={"config_path": config_path, "missing_keys": missing_keys},
            **filtered_kwargs,
        )


class ConversionError(FQCNConverterError):
    """
    Raised when conversion fails for a specific file.

    Provides file-specific error information and recovery strategies.
    """

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        column_number: Optional[int] = None,
        original_content: Optional[str] = None,
        **kwargs,
    ) -> None:
        details_parts = []
        suggestions = []
        recovery_actions = []

        if file_path:
            details_parts.append(f"File: {file_path}")
            suggestions.extend(
                [
                    f"Check file syntax and format: {file_path}",
                    f"Verify file is a valid Ansible playbook or task file",
                ]
            )

        if line_number is not None:
            location = f"Line {line_number}"
            if column_number is not None:
                location += f", Column {column_number}"
            details_parts.append(f"Location: {location}")
            suggestions.append(f"Review content at {location}")

        if original_content:
            # Show snippet of problematic content
            lines = original_content.split("\n")
            if line_number and 1 <= line_number <= len(lines):
                snippet_start = max(0, line_number - 3)
                snippet_end = min(len(lines), line_number + 2)
                snippet = "\n".join(
                    f"{i+1:3}: {lines[i]}" for i in range(snippet_start, snippet_end)
                )
                details_parts.append(f"Content snippet:\n{snippet}")

        # Recovery actions for conversion errors
        recovery_actions.extend(
            [
                "Skip this file and continue with remaining files",
                "Create backup and attempt manual conversion",
                "Use dry-run mode to preview changes",
                "Check file against Ansible syntax validator",
            ]
        )

        # Filter out conflicting parameters from kwargs
        filtered_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "message",
                "details",
                "suggestions",
                "recovery_actions",
                "error_code",
                "context",
            ]
        }

        super().__init__(
            message=message,
            details="; ".join(details_parts),
            suggestions=suggestions,
            recovery_actions=recovery_actions,
            error_code="CONVERSION_ERROR",
            context={
                "file_path": file_path,
                "line_number": line_number,
                "column_number": column_number,
            },
            **filtered_kwargs,
        )


class ValidationError(FQCNConverterError):
    """
    Raised when validation fails or finds critical issues.

    Provides detailed validation results and remediation steps.
    """

    def __init__(
        self,
        message: str,
        validation_issues: Optional[List[Dict[str, Any]]] = None,
        file_path: Optional[str] = None,
        **kwargs,
    ) -> None:
        details_parts = []
        suggestions = []
        recovery_actions = []

        if file_path:
            details_parts.append(f"File: {file_path}")

        if validation_issues:
            details_parts.append(f"Found {len(validation_issues)} validation issues")

            # Categorize issues
            critical_issues = [
                i for i in validation_issues if i.get("severity") == "critical"
            ]
            warning_issues = [
                i for i in validation_issues if i.get("severity") == "warning"
            ]

            if critical_issues:
                details_parts.append(f"Critical issues: {len(critical_issues)}")
                for issue in critical_issues[:3]:  # Show first 3 critical issues
                    details_parts.append(
                        f"  - {issue.get('description', 'Unknown issue')}"
                    )

            if warning_issues:
                details_parts.append(f"Warning issues: {len(warning_issues)}")

            # Generate specific suggestions based on issues
            for issue in validation_issues[:5]:  # Limit to first 5 issues
                if "suggestion" in issue:
                    suggestions.append(issue["suggestion"])

        # Default suggestions if none provided
        if not suggestions:
            suggestions.extend(
                [
                    "Review the validation report for specific issues",
                    "Check that all modules use FQCN format",
                    "Verify Ansible collection dependencies are available",
                ]
            )

        recovery_actions.extend(
            [
                "Continue with partial validation results",
                "Re-run conversion with updated mappings",
                "Generate detailed validation report",
                "Skip validation and proceed with conversion",
            ]
        )

        # Filter out conflicting parameters from kwargs
        filtered_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "message",
                "details",
                "suggestions",
                "recovery_actions",
                "error_code",
                "context",
            ]
        }

        super().__init__(
            message=message,
            details="; ".join(details_parts),
            suggestions=suggestions,
            recovery_actions=recovery_actions,
            error_code="VALIDATION_ERROR",
            context={
                "file_path": file_path,
                "issues_count": len(validation_issues or []),
            },
            **filtered_kwargs,
        )


class BatchProcessingError(FQCNConverterError):
    """
    Raised when batch processing encounters errors.

    Provides batch operation context and partial success information.
    """

    def __init__(
        self,
        message: str,
        failed_files: Optional[List[str]] = None,
        successful_files: Optional[List[str]] = None,
        total_files: Optional[int] = None,
        **kwargs,
    ) -> None:
        details_parts = []
        suggestions = []
        recovery_actions = []

        if total_files is not None:
            success_count = len(successful_files) if successful_files else 0
            failure_count = len(failed_files) if failed_files else 0
            details_parts.append(
                f"Processed {total_files} files: {success_count} successful, {failure_count} failed"
            )

        if failed_files:
            details_parts.append(f"Failed files: {', '.join(failed_files[:5])}")
            if len(failed_files) > 5:
                details_parts.append(f"... and {len(failed_files) - 5} more")

            suggestions.extend(
                [
                    "Review individual file errors in the detailed log",
                    "Check file permissions and syntax for failed files",
                    "Consider processing failed files individually",
                ]
            )

        if successful_files:
            details_parts.append(
                f"Successfully processed {len(successful_files)} files"
            )
            recovery_actions.append("Continue with successfully processed files")

        recovery_actions.extend(
            [
                "Retry failed files with different settings",
                "Generate detailed error report for failed files",
                "Process remaining files in smaller batches",
                "Skip failed files and complete batch operation",
            ]
        )

        super().__init__(
            message=message,
            details="; ".join(details_parts),
            suggestions=suggestions,
            recovery_actions=recovery_actions,
            error_code="BATCH_ERROR",
            context={
                "total_files": total_files,
                "failed_count": len(failed_files) if failed_files else 0,
                "success_count": len(successful_files) if successful_files else 0,
            },
            **kwargs,
        )


class YAMLParsingError(ConversionError):
    """
    Raised when YAML parsing fails.

    Provides YAML-specific error information and syntax guidance.
    """

    def __init__(
        self, message: str, yaml_error: Optional[Exception] = None, **kwargs
    ) -> None:
        suggestions = []
        recovery_actions = []

        # Extract YAML-specific error information
        if yaml_error:
            yaml_details = str(yaml_error)
            suggestions.extend(
                [
                    "Check YAML syntax and indentation",
                    "Verify proper quoting of strings with special characters",
                    "Ensure consistent use of spaces (not tabs) for indentation",
                    "Validate YAML structure with a YAML linter",
                ]
            )
        else:
            suggestions.extend(
                [
                    "Verify file contains valid YAML syntax",
                    "Check for proper YAML document structure",
                ]
            )

        recovery_actions.extend(
            [
                "Skip this file and continue processing",
                "Attempt to fix common YAML syntax issues automatically",
                "Create a backup and manually fix YAML syntax",
                "Use a YAML formatter to fix indentation issues",
            ]
        )

        super().__init__(
            message=message,
            suggestions=suggestions,
            recovery_actions=recovery_actions,
            error_code="YAML_PARSE_ERROR",
            **kwargs,
        )


class FileAccessError(FQCNConverterError):
    """
    Raised when file access operations fail.

    Provides file system error context and permission guidance.
    """

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        os_error: Optional[OSError] = None,
        **kwargs,
    ) -> None:
        details_parts = []
        suggestions = []
        recovery_actions = []

        if file_path:
            details_parts.append(f"File: {file_path}")

            # Check file/directory existence and permissions
            path_obj = Path(file_path)
            if not path_obj.exists():
                suggestions.append(f"Verify that the file exists: {file_path}")
                recovery_actions.append("Skip missing files and continue")
            elif not path_obj.is_file():
                suggestions.append(f"Path is not a file: {file_path}")
            else:
                # Check permissions
                if operation == "read" and not os.access(file_path, os.R_OK):
                    suggestions.append(f"Grant read permissions to file: {file_path}")
                elif operation == "write" and not os.access(file_path, os.W_OK):
                    suggestions.append(f"Grant write permissions to file: {file_path}")

        if operation:
            details_parts.append(f"Operation: {operation}")

        if os_error:
            details_parts.append(f"System error: {os_error}")

            # Provide OS-specific suggestions
            if os_error.errno == 13:  # Permission denied
                suggestions.extend(
                    [
                        "Check file and directory permissions",
                        "Run with appropriate user privileges",
                        "Ensure the file is not locked by another process",
                    ]
                )
            elif os_error.errno == 2:  # File not found
                suggestions.extend(
                    [
                        "Verify the file path is correct",
                        "Check if the file was moved or deleted",
                    ]
                )

        # Default recovery actions
        recovery_actions.extend(
            [
                "Skip inaccessible files and continue processing",
                "Create missing directories if needed",
                "Use dry-run mode to avoid file modifications",
                "Check and fix file permissions",
            ]
        )

        # Filter out conflicting parameters from kwargs
        filtered_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "message",
                "details",
                "suggestions",
                "recovery_actions",
                "error_code",
                "context",
            ]
        }

        super().__init__(
            message=message,
            details="; ".join(details_parts),
            suggestions=suggestions,
            recovery_actions=recovery_actions,
            error_code="FILE_ACCESS_ERROR",
            context={"file_path": file_path, "operation": operation},
            **filtered_kwargs,
        )


class MappingError(ConfigurationError):
    """
    Raised when FQCN mapping issues are encountered.

    Provides mapping-specific error information and resolution steps.
    """

    def __init__(
        self,
        message: str,
        module_name: Optional[str] = None,
        available_mappings: Optional[List[str]] = None,
        **kwargs,
    ) -> None:
        suggestions = []
        recovery_actions = []

        if module_name:
            suggestions.extend(
                [
                    f"Add mapping for module '{module_name}' to configuration",
                    f"Check if '{module_name}' is a valid Ansible module name",
                    f"Verify the correct collection for module '{module_name}'",
                ]
            )

        if available_mappings:
            suggestions.append(
                f"Available mappings: {', '.join(available_mappings[:10])}"
            )
            if len(available_mappings) > 10:
                suggestions.append(f"... and {len(available_mappings) - 10} more")

        recovery_actions.extend(
            [
                "Continue with available mappings",
                "Use default mapping patterns for unknown modules",
                "Generate mapping suggestions based on module names",
                "Skip unmapped modules and continue conversion",
            ]
        )

        super().__init__(
            message=message,
            suggestions=suggestions,
            recovery_actions=recovery_actions,
            error_code="MAPPING_ERROR",
            context={"module_name": module_name},
            **kwargs,
        )


# Error recovery utilities
class ErrorRecovery:
    """Utility class for implementing error recovery mechanisms."""

    @staticmethod
    def can_continue_batch(error: FQCNConverterError) -> bool:
        """Determine if batch processing can continue after an error."""
        # File-level errors shouldn't stop batch processing
        return isinstance(error, (ConversionError, FileAccessError, YAMLParsingError))

    @staticmethod
    def get_fallback_config() -> Dict[str, str]:
        """Get fallback configuration when config loading fails."""
        return {
            # Core Ansible modules
            "user": "ansible.builtin.user",
            "group": "ansible.builtin.group",
            "file": "ansible.builtin.file",
            "copy": "ansible.builtin.copy",
            "template": "ansible.builtin.template",
            "service": "ansible.builtin.service",
            "systemd": "ansible.builtin.systemd",
            "command": "ansible.builtin.command",
            "shell": "ansible.builtin.shell",
            "debug": "ansible.builtin.debug",
            "set_fact": "ansible.builtin.set_fact",
            "include_tasks": "ansible.builtin.include_tasks",
            "import_tasks": "ansible.builtin.import_tasks",
        }

    @staticmethod
    def suggest_module_mapping(module_name: str) -> Optional[str]:
        """Suggest FQCN mapping for unknown module."""
        # Common patterns for module mapping suggestions
        common_collections = {
            "docker": "community.docker",
            "mysql": "community.mysql",
            "postgresql": "community.postgresql",
            "mongodb": "community.mongodb",
            "aws": "amazon.aws",
            "azure": "azure.azcollection",
            "gcp": "google.cloud",
            "k8s": "kubernetes.core",
            "openshift": "kubernetes.core",
            "win": "ansible.windows",
        }

        for prefix, collection in common_collections.items():
            if module_name.startswith(prefix):
                return f"{collection}.{module_name}"

        # Default suggestion for unknown modules
        return f"community.general.{module_name}"
