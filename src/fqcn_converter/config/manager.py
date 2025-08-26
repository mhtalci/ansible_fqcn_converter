"""
Configuration management system for FQCN Converter.

This module handles loading, merging, and managing FQCN mappings and
converter settings from various sources.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from ..exceptions import ConfigurationError
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ConversionSettings:
    """
    Configuration settings for FQCN conversion operations.

    This dataclass defines the various settings that control how FQCN conversion
    is performed, including backup behavior, validation levels, and conflict resolution.

    Attributes:
        backup_files: Whether to create backup files before conversion
        backup_suffix: File extension for backup files
        backup_directory: Directory to store backup files
        validation_level: Level of validation to perform ("minimal", "standard", "strict")
        conflict_resolution: How to handle conflicts ("strict", "permissive", "context_aware")
        create_rollback: Whether to create rollback files
        rollback_suffix: File extension for rollback files

    Example:
        >>> settings = ConversionSettings(backup_files=True, validation_level="strict")
        >>> settings.backup_files
        True
    """

    backup_files: bool = True
    backup_suffix: str = ".fqcn_backup"
    backup_directory: str = ".fqcn_backups"
    validation_level: str = "standard"  # "minimal", "standard", "strict"
    conflict_resolution: str = (
        "context_aware"  # "strict", "permissive", "context_aware"
    )
    create_rollback: bool = True
    rollback_suffix: str = ".fqcn_rollback"


@dataclass
class ConfigurationSchema:
    """Schema for configuration validation."""

    version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    mappings: Dict[str, str] = field(default_factory=dict)
    settings: ConversionSettings = field(default_factory=ConversionSettings)
    collection_dependencies: Dict[str, List[Dict[str, str]]] = field(
        default_factory=dict
    )
    validation_patterns: Dict[str, Any] = field(default_factory=dict)
    conversion_rules: Dict[str, Any] = field(default_factory=dict)


class ConfigurationManager:
    """
    Manages FQCN mappings and converter settings.

    This class provides centralized configuration management for the FQCN converter,
    handling loading, merging, and validation of configuration files and mappings.

    Features:
        - Load default and custom FQCN mappings
        - Merge configurations with precedence rules
        - Validate configuration schemas
        - Support multiple configuration formats

    Example:
        >>> config_manager = ConfigurationManager()
        >>> mappings = config_manager.load_default_mappings()
        >>> custom_mappings = config_manager.load_custom_mappings("custom.yml")
        >>> merged = config_manager.merge_mappings(mappings, custom_mappings)
    """

    def __init__(self) -> None:
        """
        Initialize configuration manager.

        Sets up the configuration manager with default settings and locates
        the default configuration file if available.
        """
        self._default_config_path = self._find_default_config()
        self._schema = ConfigurationSchema()

        logger.debug(
            f"Initialized ConfigurationManager with default config: {self._default_config_path}"
        )

    def load_default_mappings(self) -> Dict[str, str]:
        """
        Load default FQCN mappings from bundled configuration.

        Returns:
            Dictionary mapping short module names to FQCNs

        Raises:
            ConfigurationError: If default configuration cannot be loaded
        """
        try:
            if not self._default_config_path or not self._default_config_path.exists():
                logger.warning(
                    "Default configuration file not found, using minimal built-in mappings"
                )
                return self._get_minimal_builtin_mappings()

            with open(self._default_config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            if not config_data:
                logger.warning(
                    "Default configuration file is empty, using minimal built-in mappings"
                )
                return self._get_minimal_builtin_mappings()

            # Extract mappings from the configuration structure using the proper method
            mappings = self._extract_mappings_from_config(config_data)

            logger.info(f"Loaded {len(mappings)} default module mappings")
            return mappings

        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Failed to parse default configuration YAML: {self._default_config_path}",
                details=str(e),
            ) from e
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load default configuration: {self._default_config_path}",
                details=str(e),
            ) from e

    def load_custom_mappings(self, config_path: Union[str, Path]) -> Dict[str, str]:
        """
        Load custom mappings from user-provided file.

        Args:
            config_path: Path to custom configuration file

        Returns:
            Dictionary mapping short module names to FQCNs

        Raises:
            ConfigurationError: If custom configuration cannot be loaded
        """
        config_path = Path(config_path)

        try:
            if not config_path.exists():
                raise ConfigurationError(
                    f"Custom configuration file not found: {config_path}",
                    details="Ensure the file path is correct and accessible",
                )

            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            if not config_data:
                logger.warning(f"Custom configuration file is empty: {config_path}")
                return {}

            # Validate and extract mappings
            mappings = self._extract_mappings_from_config(config_data)

            logger.info(
                f"Loaded {len(mappings)} custom module mappings from {config_path}"
            )
            return mappings

        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Failed to parse custom configuration YAML: {config_path}",
                details=str(e),
            ) from e
        except ConfigurationError:
            # Re-raise configuration errors
            raise
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load custom configuration: {config_path}", details=str(e)
            ) from e

    def merge_mappings(self, *mapping_dicts: Dict[str, str]) -> Dict[str, str]:
        """
        Merge multiple mapping dictionaries with precedence rules.

        Args:
            *mapping_dicts: Variable number of mapping dictionaries

        Returns:
            Merged dictionary with later dictionaries taking precedence

        Note:
            Later dictionaries in the argument list take precedence over earlier ones.
            This allows for: base_mappings -> custom_mappings -> user_overrides
        """
        if not mapping_dicts:
            return {}

        merged = {}
        conflicts = []

        for i, mapping_dict in enumerate(mapping_dicts):
            if not isinstance(mapping_dict, dict):
                logger.warning(
                    f"Skipping non-dict mapping at index {i}: {type(mapping_dict)}"
                )
                continue

            for key, value in mapping_dict.items():
                if key in merged and merged[key] != value:
                    conflicts.append(
                        {
                            "key": key,
                            "old_value": merged[key],
                            "new_value": value,
                            "source_index": i,
                        }
                    )

                merged[key] = value

        if conflicts:
            logger.debug(f"Resolved {len(conflicts)} mapping conflicts during merge")
            for conflict in conflicts:
                logger.debug(
                    f"  {conflict['key']}: {conflict['old_value']} -> {conflict['new_value']}"
                )

        logger.debug(
            f"Merged {len(mapping_dicts)} mapping dictionaries into {len(merged)} total mappings"
        )
        return merged

    def load_settings(
        self, config_path: Optional[Union[str, Path]] = None
    ) -> ConversionSettings:
        """
        Load conversion settings from configuration.

        Args:
            config_path: Optional path to custom configuration file

        Returns:
            ConversionSettings object with loaded settings
        """
        settings = ConversionSettings()

        try:
            # Load from default config first
            if self._default_config_path and self._default_config_path.exists():
                default_settings = self._load_settings_from_file(
                    self._default_config_path
                )
                settings = self._merge_settings(settings, default_settings)

            # Load from custom config if provided
            if config_path:
                custom_path = Path(config_path)
                if custom_path.exists():
                    custom_settings = self._load_settings_from_file(custom_path)
                    settings = self._merge_settings(settings, custom_settings)

            return settings

        except Exception as e:
            logger.warning(f"Failed to load settings, using defaults: {e}")
            return ConversionSettings()

    def validate_configuration(self, config_data: Dict[str, Any]) -> bool:
        """
        Validate configuration data against schema.

        Args:
            config_data: Configuration data to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Basic structure validation
            if not isinstance(config_data, dict):
                logger.error("Configuration must be a dictionary")
                return False

            # Validate mappings sections
            valid_sections = {
                "ansible_builtin",
                "community_general",
                "community_mysql",
                "community_postgresql",
                "community_mongodb",
                "collection_dependencies",
                "validation_patterns",
                "conversion_rules",
                "backup_config",
                "rollback_config",
            }

            for section_name, section_data in config_data.items():
                if section_name not in valid_sections:
                    logger.warning(f"Unknown configuration section: {section_name}")

                if (
                    section_name.startswith("community_")
                    or section_name == "ansible_builtin"
                ):
                    if not isinstance(section_data, dict):
                        logger.error(f"Section {section_name} must be a dictionary")
                        return False

                    # Validate FQCN format in mappings
                    for module_name, fqcn in section_data.items():
                        if not isinstance(fqcn, str):
                            logger.error(f"FQCN for {module_name} must be a string")
                            return False

                        if not self._is_valid_fqcn(fqcn):
                            logger.warning(f"Invalid FQCN format: {fqcn}")

            return True

        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False

    def _find_default_config(self) -> Optional[Path]:
        """Find the default configuration file."""
        # Look for config in several locations
        possible_paths = [
            Path(__file__).parent.parent.parent.parent / "config" / "fqcn_mapping.yml",
            Path("config") / "fqcn_mapping.yml",
            Path("fqcn_mapping.yml"),
        ]

        for path in possible_paths:
            if path.exists():
                return path

        return None

    def _get_minimal_builtin_mappings(self) -> Dict[str, str]:
        """Get minimal built-in mappings as fallback."""
        return {
            # Essential builtin modules
            "copy": "ansible.builtin.copy",
            "file": "ansible.builtin.file",
            "template": "ansible.builtin.template",
            "service": "ansible.builtin.service",
            "command": "ansible.builtin.command",
            "shell": "ansible.builtin.shell",
            "user": "ansible.builtin.user",
            "group": "ansible.builtin.group",
            "package": "ansible.builtin.package",
            "apt": "ansible.builtin.apt",
            "yum": "ansible.builtin.yum",
            "systemd": "ansible.builtin.systemd",
            "debug": "ansible.builtin.debug",
            "set_fact": "ansible.builtin.set_fact",
            "include_tasks": "ansible.builtin.include_tasks",
            "import_tasks": "ansible.builtin.import_tasks",
        }

    def _extract_mappings_from_config(
        self, config_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Extract mappings from configuration data structure."""
        mappings = {}

        # Handle different configuration formats
        if "mappings" in config_data:
            # Simple format with direct mappings section
            if isinstance(config_data["mappings"], dict):
                mappings.update(config_data["mappings"])
        else:
            # Complex format with multiple sections
            # Process in priority order: builtin first, then others
            priority_sections = ["ansible_builtin", "ansible_posix"]
            other_sections = []

            for section_name, section_data in config_data.items():
                if isinstance(section_data, dict) and section_name not in [
                    "collection_dependencies",
                    "validation_patterns",
                    "conversion_rules",
                    "backup_config",
                    "rollback_config",
                ]:
                    if section_name in priority_sections:
                        # Process priority sections first
                        mappings.update(section_data)
                    else:
                        other_sections.append((section_name, section_data))

            # Process other sections, but don't override existing mappings
            for section_name, section_data in other_sections:
                for key, value in section_data.items():
                    if key not in mappings:  # Only add if not already present
                        mappings[key] = value

        return mappings

    def _load_settings_from_file(self, config_path: Path) -> ConversionSettings:
        """Load settings from a configuration file."""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            settings = ConversionSettings()

            # Extract settings from various possible locations
            settings_data = {}
            if "settings" in config_data:
                settings_data = config_data["settings"]
            elif "backup_config" in config_data:
                backup_config = config_data["backup_config"]
                settings_data.update(
                    {
                        "backup_files": backup_config.get("create_backup", True),
                        "backup_suffix": backup_config.get(
                            "backup_suffix", ".fqcn_backup"
                        ),
                        "backup_directory": backup_config.get(
                            "backup_directory", ".fqcn_backups"
                        ),
                    }
                )

            # Apply settings
            for key, value in settings_data.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)

            return settings

        except Exception as e:
            logger.warning(f"Failed to load settings from {config_path}: {e}")
            return ConversionSettings()

    def _merge_settings(
        self, base: ConversionSettings, override: ConversionSettings
    ) -> ConversionSettings:
        """Merge two ConversionSettings objects."""
        # Create a new settings object with base values
        merged = ConversionSettings(
            backup_files=(
                override.backup_files
                if override.backup_files != base.backup_files
                else base.backup_files
            ),
            backup_suffix=(
                override.backup_suffix
                if override.backup_suffix != base.backup_suffix
                else base.backup_suffix
            ),
            backup_directory=(
                override.backup_directory
                if override.backup_directory != base.backup_directory
                else base.backup_directory
            ),
            validation_level=(
                override.validation_level
                if override.validation_level != base.validation_level
                else base.validation_level
            ),
            conflict_resolution=(
                override.conflict_resolution
                if override.conflict_resolution != base.conflict_resolution
                else base.conflict_resolution
            ),
            create_rollback=(
                override.create_rollback
                if override.create_rollback != base.create_rollback
                else base.create_rollback
            ),
            rollback_suffix=(
                override.rollback_suffix
                if override.rollback_suffix != base.rollback_suffix
                else base.rollback_suffix
            ),
        )

        return merged

    def _is_valid_fqcn(self, fqcn: str) -> bool:
        """Validate FQCN format."""
        # Basic FQCN format: namespace.collection.module
        parts = fqcn.split(".")
        return len(parts) >= 3 and all(part.isidentifier() for part in parts)
