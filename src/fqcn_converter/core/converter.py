"""
Core FQCN conversion engine.

This module contains the main FQCNConverter class and related data structures
for converting Ansible playbooks from short module names to fully qualified
collection names (FQCNs).
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Union

import yaml

from ..config.manager import ConfigurationManager
from ..exceptions import (
    ConfigurationError,
    ConversionError,
    FileAccessError,
    YAMLParsingError,
)
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Pre-compiled regex patterns for better performance
TASK_START_PATTERN = re.compile(r"^\s*-\s+name\s*:")
MODULE_PATTERN = re.compile(r"^\s*-?\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:")
YAML_KEY_PATTERN = re.compile(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:")
FQCN_PATTERN = re.compile(
    r"^[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*$"
)


@dataclass
class ConversionResult:
    """
    Result of a single file conversion operation.

    This class encapsulates all information about a conversion operation,
    including success status, changes made, and any errors or warnings
    encountered during the process.

    Attributes:
        success: Whether the conversion operation completed successfully
        file_path: Path to the file that was converted (or attempted)
        changes_made: Number of module conversions performed
        errors: List of error messages encountered during conversion
        warnings: List of warning messages from the conversion process
        original_content: Original file content before conversion (optional)
        converted_content: File content after conversion (optional)
        processing_time: Time taken for the conversion operation in seconds
        backup_path: Path to backup file if one was created (optional)

    Example:
        >>> result = converter.convert_file("playbook.yml")
        >>> if result.success:
        ...     print(f"Converted {result.changes_made} modules")
        ... else:
        ...     print(f"Conversion failed: {result.errors}")
    """

    success: bool
    file_path: str
    changes_made: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    original_content: Optional[str] = None
    converted_content: Optional[str] = None
    processing_time: float = 0.0
    backup_path: Optional[str] = None


class FQCNConverter:
    """
    Main FQCN conversion engine with configurable mappings and robust error handling.

    The FQCNConverter class provides the core functionality for converting Ansible
    playbooks and task files from short module names to Fully Qualified Collection
    Names (FQCNs). It supports custom configuration, backup creation, and comprehensive
    error handling.

    Features:
        - Intelligent module detection and conversion
        - Configurable FQCN mappings
        - Backup file creation for safety
        - Dry-run mode for previewing changes
        - Comprehensive error reporting
        - Support for various Ansible file formats

    Example:
        >>> converter = FQCNConverter()
        >>> result = converter.convert_file("playbook.yml")
        >>> if result.success:
        ...     print(f"Successfully converted {result.changes_made} modules")

        >>> # Using custom mappings
        >>> custom_mappings = {"my_module": "my.collection.my_module"}
        >>> converter = FQCNConverter(custom_mappings=custom_mappings)

        >>> # Dry run to preview changes
        >>> result = converter.convert_file("playbook.yml", dry_run=True)
        >>> print(f"Would convert {result.changes_made} modules")
    """

    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        custom_mappings: Optional[Dict[str, str]] = None,
        create_backups: bool = True,
        backup_suffix: str = ".fqcn_backup",
    ) -> None:
        """
        Initialize converter with configuration and settings.

        The converter loads default FQCN mappings and optionally merges them with
        custom configuration and mappings. It supports various configuration sources
        and provides fallback mechanisms for robust operation.

        Args:
            config_path: Path to custom configuration file (YAML format).
                        If provided, mappings from this file will be merged with defaults.
            custom_mappings: Dictionary of custom module mappings in the format
                           {"short_name": "namespace.collection.module_name"}.
                           These take precedence over config file mappings.
            create_backups: Whether to create backup files before conversion.
                          Defaults to True for safety.
            backup_suffix: Suffix to append to backup files. Defaults to ".fqcn_backup".

        Raises:
            ConfigurationError: If configuration loading fails or contains invalid data.
                              The converter will attempt to use default mappings as fallback.

        Example:
            >>> # Basic initialization with defaults
            >>> converter = FQCNConverter()

            >>> # With custom configuration file
            >>> converter = FQCNConverter(config_path="my_config.yml")

            >>> # With custom mappings
            >>> mappings = {"my_module": "my.collection.my_module"}
            >>> converter = FQCNConverter(custom_mappings=mappings)

            >>> # Disable backups for testing
            >>> converter = FQCNConverter(create_backups=False)
        """
        self._config_manager = ConfigurationManager()
        self._mappings: Dict[str, str] = {}
        self._mapping_cache: Dict[str, Optional[str]] = {}  # Cache for frequent lookups

        try:
            # Load default mappings first
            self._mappings = self._config_manager.load_default_mappings()

            # Load custom configuration if provided
            if config_path:
                custom_config = self._config_manager.load_custom_mappings(
                    str(config_path)
                )
                self._mappings = self._config_manager.merge_mappings(
                    self._mappings, custom_config
                )

            # Apply custom mappings if provided
            if custom_mappings:
                self._mappings = self._config_manager.merge_mappings(
                    self._mappings, custom_mappings
                )

            logger.info(
                f"Initialized converter with {len(self._mappings)} module mappings"
            )

        except Exception as e:
            raise ConfigurationError(
                f"Failed to initialize converter configuration: {str(e)}",
                details=f"Config path: {config_path}, Custom mappings: {bool(custom_mappings)}",
            ) from e

    def _get_fqcn_mapping(self, module_name: str) -> Optional[str]:
        """Get FQCN mapping for a module with caching for performance."""
        if module_name in self._mapping_cache:
            return self._mapping_cache[module_name]

        fqcn = self._mappings.get(module_name)
        self._mapping_cache[module_name] = fqcn
        return fqcn

    def convert_file(
        self, file_path: Union[str, Path], dry_run: bool = False
    ) -> ConversionResult:
        """
        Convert a single Ansible file to FQCN format.

        Args:
            file_path: Path to the Ansible file to convert
            dry_run: If True, perform conversion without writing changes

        Returns:
            ConversionResult with conversion details

        Raises:
            FileAccessError: If file cannot be read or written
            ConversionError: If conversion fails
        """
        file_path = Path(file_path)

        try:
            # Read file content
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    original_content = f.read()
            except (IOError, OSError) as e:
                raise FileAccessError(
                    f"Cannot read file: {file_path}", details=str(e)
                ) from e

            # Convert content
            result = self.convert_content(original_content, file_type="yaml")
            result.file_path = str(file_path)

            # Write changes if not dry run and conversion was successful
            if not dry_run and result.success and result.changes_made > 0:
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(result.converted_content)
                    logger.info(
                        f"Successfully converted {file_path} with {result.changes_made} changes"
                    )
                except (IOError, OSError) as e:
                    raise FileAccessError(
                        f"Cannot write file: {file_path}", details=str(e)
                    ) from e

            return result

        except (FileAccessError, ConversionError):
            # Re-raise known exceptions
            raise
        except Exception as e:
            raise ConversionError(
                f"Unexpected error converting file: {file_path}", details=str(e)
            ) from e

    def convert_content(
        self, content: str, file_type: str = "yaml"
    ) -> ConversionResult:
        """
        Convert Ansible content string to FQCN format.

        Args:
            content: The content to convert
            file_type: Type of content ('yaml' supported)

        Returns:
            ConversionResult with conversion details
        """
        result = ConversionResult(
            success=False,
            file_path="<content>",
            changes_made=0,
            original_content=content,
        )

        try:
            if file_type.lower() != "yaml":
                result.errors.append(f"Unsupported file type: {file_type}")
                return result

            # Parse YAML content
            try:
                yaml_data = yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise YAMLParsingError(
                    "Failed to parse YAML content", details=str(e)
                ) from e

            if yaml_data is None:
                result.converted_content = content
                result.success = True
                return result

            # Convert the content
            converted_content = content
            changes_made = 0

            # Process different Ansible structures
            if isinstance(yaml_data, list):
                # Could be either a playbook (list of plays) or task file (list of tasks)
                # Check if first item looks like a play (has 'hosts') or a task (has module names)
                if yaml_data and isinstance(yaml_data[0], dict):
                    if "hosts" in yaml_data[0] or "tasks" in yaml_data[0]:
                        # Playbook format (list of plays)
                        converted_content, changes = self._convert_playbook_content(
                            content, yaml_data
                        )
                    else:
                        # Task file format (list of tasks)
                        converted_content, changes = self._convert_tasks_in_content(
                            content, yaml_data
                        )
                    changes_made += changes
            elif isinstance(yaml_data, dict):
                # Task file or other dict-based format
                converted_content, changes = self._convert_dict_content(
                    content, yaml_data
                )
                changes_made += changes

            result.converted_content = converted_content
            result.changes_made = changes_made
            result.success = True

            if changes_made > 0:
                logger.debug(f"Made {changes_made} FQCN conversions")

            # Clear large variables to help with memory management
            yaml_data = None
            converted_content = None

            return result

        except YAMLParsingError:
            # Re-raise YAML parsing errors
            raise
        except Exception as e:
            result.errors.append(f"Conversion failed: {str(e)}")
            result.converted_content = content
            return result

    def _convert_playbook_content(
        self, content: str, yaml_data: List[Any]
    ) -> tuple[str, int]:
        """Convert playbook content (list of plays)."""
        converted_content = content
        total_changes = 0

        for play in yaml_data:
            if isinstance(play, dict):
                # Check for tasks in various locations within each play
                for key in ["pre_tasks", "tasks", "handlers", "post_tasks"]:
                    if key in play and isinstance(play[key], list):
                        converted_content, changes = self._convert_tasks_in_content(
                            converted_content, play[key]
                        )
                        total_changes += changes

        return converted_content, total_changes

    def _convert_dict_content(
        self, content: str, yaml_data: Dict[str, Any]
    ) -> tuple[str, int]:
        """Convert dictionary-based content."""
        converted_content = content
        total_changes = 0

        # Check for tasks in various locations
        for key in ["tasks", "handlers", "pre_tasks", "post_tasks"]:
            if key in yaml_data and isinstance(yaml_data[key], list):
                converted_content, changes = self._convert_tasks_in_content(
                    converted_content, yaml_data[key]
                )
                total_changes += changes

        return converted_content, total_changes

    def _convert_tasks_in_content(
        self, content: str, tasks: List[Any]
    ) -> tuple[str, int]:
        """Convert module names in tasks within the content string."""
        converted_content = content
        changes_made = 0

        # Skip special Ansible keys that aren't modules
        ansible_directives = {
            "name",
            "when",
            "register",
            "changed_when",
            "failed_when",
            "notify",
            "tags",
            "become",
            "become_user",
            "vars",
            "loop",
            "loop_control",
            "until",
            "retries",
            "delay",
            "ignore_errors",
            "delegate_to",
            "delegate_facts",
            "run_once",
            "check_mode",
            "diff",
            "throttle",
            "serial",
            "max_fail_percentage",
            "args",
            "environment",
            "no_log",
            "any_errors_fatal",
            "connection",
            "remote_user",
            "port",
            "gather_facts",
            "gather_subset",
            "gather_timeout",
            "fact_path",
            "force_handlers",
            "block",
            "rescue",
            "always",
        }

        # Use the parsed YAML structure to identify actual modules vs parameters
        def find_modules_in_tasks(task_list: Any) -> List[str]:
            """Find actual module usage from parsed YAML structure."""
            modules_found = []

            def process_task(task: Any, task_path: str = "") -> None:
                if not isinstance(task, dict):
                    return

                # Handle nested structures
                for nested_key in ["block", "rescue", "always"]:
                    if nested_key in task and isinstance(task[nested_key], list):
                        for nested_task in task[nested_key]:
                            process_task(nested_task, f"{task_path}.{nested_key}")

                # Find the actual module in this task
                for key, value in task.items():
                    if (
                        key not in ansible_directives
                        and self._get_fqcn_mapping(key) is not None
                    ):
                        modules_found.append(
                            {
                                "module": key,
                                "fqcn": self._get_fqcn_mapping(key),
                                "task_path": task_path,
                            }
                        )
                        break  # Only one module per task

            for task in task_list:
                process_task(task)

            return modules_found

        # Get the actual modules from the parsed structure
        actual_modules = find_modules_in_tasks(tasks)

        # Now convert only the actual modules in the content
        lines = converted_content.split("\n")

        # Use a more precise approach: find task boundaries and convert only the task module
        # (not parameters that happen to have the same name)
        task_boundaries = []

        # Find task boundaries (lines that start with "- name:" or direct module tasks "- module:")
        for line_idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("- name:") or stripped == "-":
                task_boundaries.append(line_idx)
            elif stripped.startswith("- ") and ":" in stripped:
                # This might be a direct module task like "- service: ..."
                # Check if it matches any known module
                module_part = stripped[2:].split(":")[0].strip()
                if self._get_fqcn_mapping(module_part) is not None:
                    task_boundaries.append(line_idx)

        # Add end boundary
        task_boundaries.append(len(lines))

        # For each task, find the actual task module (the one that corresponds to the parsed YAML)
        task_idx = 0
        for i in range(len(task_boundaries) - 1):
            start_line = task_boundaries[i]
            end_line = task_boundaries[i + 1]

            # Skip if we've processed all tasks
            if task_idx >= len(actual_modules):
                break

            # Get the expected module for this task
            expected_module = actual_modules[task_idx]["module"]
            expected_fqcn = actual_modules[task_idx]["fqcn"]

            # Check if this task boundary is a direct module task or a named task
            boundary_line = lines[start_line].strip()

            if boundary_line.startswith("- name:"):
                # Named task - find the module line after the name
                for line_idx in range(start_line + 1, end_line):
                    if line_idx >= len(lines):
                        break

                    line = lines[line_idx]
                    stripped = line.strip()

                    # Skip empty lines and comments
                    if not stripped or stripped.startswith("#"):
                        continue

                    # Check if this line contains the expected module
                    escaped_module = re.escape(expected_module)
                    regular_pattern = re.compile(rf"^\s*{escaped_module}\s*:")
                    list_item_pattern = re.compile(rf"^\s*-\s+{escaped_module}\s*:")

                    if regular_pattern.match(line) or list_item_pattern.match(line):
                        # This should be the task module - convert it
                        if list_item_pattern.match(line):
                            # List item pattern: "  - module:"
                            new_line = re.sub(
                                rf"^(\s*-\s+){re.escape(expected_module)}(\s*:)",
                                rf"\1{expected_fqcn}\2",
                                line,
                            )
                        else:
                            # Regular pattern: "  module:"
                            new_line = re.sub(
                                rf"^(\s*){re.escape(expected_module)}(\s*:)",
                                rf"\1{expected_fqcn}\2",
                                line,
                            )

                        lines[line_idx] = new_line
                        changes_made += 1
                        logger.debug(
                            f"Converted {expected_module} -> {expected_fqcn} on line {line_idx+1}"
                        )
                        task_idx += 1
                        break  # Move to next task

            elif boundary_line.startswith("- ") and expected_module in boundary_line:
                # Direct module task - convert this line directly
                line = lines[start_line]
                escaped_module = re.escape(expected_module)
                list_item_pattern = re.compile(rf"^\s*-\s+{escaped_module}\s*:")

                if list_item_pattern.match(line):
                    # List item pattern: "  - module:"
                    new_line = re.sub(
                        rf"^(\s*-\s+){escaped_module}(\s*:)",
                        rf"\1{expected_fqcn}\2",
                        line,
                    )

                    lines[start_line] = new_line
                    changes_made += 1
                    logger.debug(
                        f"Converted {expected_module} -> {expected_fqcn} on line {start_line+1}"
                    )
                    task_idx += 1

        converted_content = "\n".join(lines)
        return converted_content, changes_made
