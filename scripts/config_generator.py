#!/usr/bin/env python3
"""
FQCN Configuration Generator

This script generates and updates FQCN mapping configurations by analyzing
installed Ansible collections and their modules.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Set


class ConfigGenerator:
    """Generator for FQCN mapping configurations."""

    def __init__(self):
        """Initialize configuration generator."""
        self.logger = logging.getLogger(__name__)
        self.collections_info = {}
        self.module_mappings = {}

    def get_installed_collections(self) -> List[Dict]:
        """
        Get list of installed Ansible collections.

        Returns:
            List of collection information dictionaries
        """
        try:
            result = subprocess.run(
                ["ansible-galaxy", "collection", "list", "--format", "json"],
                capture_output=True,
                text=True,
                check=True,
            )

            collections_data = json.loads(result.stdout)
            collections = []

            for path, path_collections in collections_data.items():
                for collection_name, collection_info in path_collections.items():
                    collections.append(
                        {
                            "name": collection_name,
                            "version": collection_info.get("version", "unknown"),
                            "path": path,
                        }
                    )

            self.logger.info(f"Found {len(collections)} installed collections")
            return collections

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to get collection list: {e}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse collection list JSON: {e}")
            return []

    def get_collection_modules(self, collection_name: str) -> List[str]:
        """
        Get modules for a specific collection.

        Args:
            collection_name: Name of the collection (e.g., 'ansible.builtin')

        Returns:
            List of module names
        """
        try:
            # Use ansible-doc to list modules in collection
            result = subprocess.run(
                ["ansible-doc", "-l", "-t", "module", collection_name],
                capture_output=True,
                text=True,
                check=True,
            )

            modules = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    # Extract module name (first part before description)
                    module_full_name = line.split()[0]
                    if module_full_name.startswith(collection_name + "."):
                        # Extract short name
                        module_short_name = module_full_name.replace(
                            collection_name + ".", ""
                        )
                        modules.append(module_short_name)

            self.logger.debug(f"Found {len(modules)} modules in {collection_name}")
            return modules

        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Failed to get modules for {collection_name}: {e}")
            return []

    def analyze_existing_playbooks(self, directory: str) -> Set[str]:
        """
        Analyze existing playbooks to find used modules.

        Args:
            directory: Directory to analyze

        Returns:
            Set of module names found in playbooks
        """
        modules_found = set()

        for yaml_file in Path(directory).rglob("*.yml"):
            try:
                with open(yaml_file, "r") as f:
                    content = yaml.safe_load(f)

                if isinstance(content, list):
                    for play in content:
                        if isinstance(play, dict) and "tasks" in play:
                            modules_found.update(
                                self._extract_modules_from_tasks(play["tasks"])
                            )
                elif isinstance(content, dict):
                    if "tasks" in content:
                        modules_found.update(
                            self._extract_modules_from_tasks(content["tasks"])
                        )

            except Exception as e:
                self.logger.debug(f"Could not analyze {yaml_file}: {e}")

        self.logger.info(
            f"Found {len(modules_found)} unique modules in existing playbooks"
        )
        return modules_found

    def _extract_modules_from_tasks(self, tasks: List) -> Set[str]:
        """Extract module names from task list."""
        modules = set()

        for task in tasks:
            if isinstance(task, dict):
                for key in task.keys():
                    # Skip common task keys
                    if key not in [
                        "name",
                        "when",
                        "tags",
                        "become",
                        "become_user",
                        "vars",
                        "register",
                        "ignore_errors",
                        "changed_when",
                        "failed_when",
                        "until",
                        "retries",
                        "delay",
                        "notify",
                        "listen",
                        "delegate_to",
                        "run_once",
                        "local_action",
                        "block",
                        "rescue",
                        "always",
                        "include",
                        "include_tasks",
                        "import_tasks",
                        "include_role",
                        "import_role",
                    ]:
                        # This might be a module name
                        if not key.startswith("ansible.") and "." not in key:
                            modules.add(key)

        return modules

    def generate_mapping_config(
        self,
        collections: List[str] = None,
        analyze_directory: str = None,
        include_all: bool = False,
    ) -> Dict:
        """
        Generate FQCN mapping configuration.

        Args:
            collections: Specific collections to include
            analyze_directory: Directory to analyze for used modules
            include_all: Include all available modules

        Returns:
            Configuration dictionary
        """
        config = {
            "fqcn_mappings": {},
            "metadata": {
                "generated_by": "FQCN Config Generator",
                "collections_analyzed": [],
                "total_modules": 0,
            },
        }

        # Get installed collections
        installed_collections = self.get_installed_collections()

        # Filter collections if specified
        if collections:
            installed_collections = [
                c for c in installed_collections if c["name"] in collections
            ]

        # Analyze existing playbooks if directory provided
        used_modules = set()
        if analyze_directory:
            used_modules = self.analyze_existing_playbooks(analyze_directory)

        # Generate mappings for each collection
        for collection in installed_collections:
            collection_name = collection["name"]
            self.logger.info(f"Processing collection: {collection_name}")

            modules = self.get_collection_modules(collection_name)

            for module in modules:
                # Include module if:
                # 1. include_all is True, or
                # 2. module is found in existing playbooks, or
                # 3. no directory analysis was done
                if include_all or not analyze_directory or module in used_modules:
                    config["fqcn_mappings"][module] = f"{collection_name}.{module}"

            config["metadata"]["collections_analyzed"].append(
                {
                    "name": collection_name,
                    "version": collection["version"],
                    "modules_count": len(modules),
                }
            )

        config["metadata"]["total_modules"] = len(config["fqcn_mappings"])

        self.logger.info(
            f"Generated mappings for {config['metadata']['total_modules']} modules"
        )
        return config

    def update_existing_config(
        self, config_file: str, new_mappings: Dict[str, str], backup: bool = True
    ) -> bool:
        """
        Update existing configuration file with new mappings.

        Args:
            config_file: Path to existing config file
            new_mappings: New mappings to add
            backup: Whether to create backup

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create backup if requested
            if backup and os.path.exists(config_file):
                backup_file = f"{config_file}.backup"
                import shutil

                shutil.copy2(config_file, backup_file)
                self.logger.info(f"Created backup: {backup_file}")

            # Load existing config
            existing_config = {}
            if os.path.exists(config_file):
                with open(config_file, "r") as f:
                    existing_config = yaml.safe_load(f) or {}

            # Merge configurations
            if "fqcn_mappings" not in existing_config:
                existing_config["fqcn_mappings"] = {}

            # Add new mappings
            added_count = 0
            updated_count = 0

            for module, fqcn in new_mappings.items():
                if module in existing_config["fqcn_mappings"]:
                    if existing_config["fqcn_mappings"][module] != fqcn:
                        existing_config["fqcn_mappings"][module] = fqcn
                        updated_count += 1
                else:
                    existing_config["fqcn_mappings"][module] = fqcn
                    added_count += 1

            # Update metadata
            if "metadata" not in existing_config:
                existing_config["metadata"] = {}

            existing_config["metadata"].update(
                {
                    "last_updated": subprocess.run(
                        ["date"], capture_output=True, text=True
                    ).stdout.strip(),
                    "total_modules": len(existing_config["fqcn_mappings"]),
                }
            )

            # Save updated config
            with open(config_file, "w") as f:
                yaml.dump(existing_config, f, default_flow_style=False, sort_keys=True)

            self.logger.info(
                f"Updated config: {added_count} added, {updated_count} updated"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to update config: {e}")
            return False

    def validate_config(self, config_file: str) -> Dict:
        """
        Validate FQCN configuration file.

        Args:
            config_file: Path to config file

        Returns:
            Validation results dictionary
        """
        results = {"valid": True, "errors": [], "warnings": [], "statistics": {}}

        try:
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)

            # Check structure
            if not isinstance(config, dict):
                results["errors"].append("Config must be a dictionary")
                results["valid"] = False
                return results

            if "fqcn_mappings" not in config:
                results["errors"].append("Missing 'fqcn_mappings' section")
                results["valid"] = False
                return results

            mappings = config["fqcn_mappings"]
            if not isinstance(mappings, dict):
                results["errors"].append("'fqcn_mappings' must be a dictionary")
                results["valid"] = False
                return results

            # Validate mappings
            collections = set()
            invalid_mappings = []

            for module, fqcn in mappings.items():
                if not isinstance(fqcn, str):
                    invalid_mappings.append(f"{module}: FQCN must be string")
                    continue

                if "." not in fqcn:
                    invalid_mappings.append(f"{module}: Invalid FQCN format '{fqcn}'")
                    continue

                collection = ".".join(fqcn.split(".")[:-1])
                collections.add(collection)

            if invalid_mappings:
                results["errors"].extend(invalid_mappings)
                results["valid"] = False

            # Statistics
            results["statistics"] = {
                "total_modules": len(mappings),
                "collections_used": len(collections),
                "collections": sorted(list(collections)),
            }

            self.logger.info(
                f"Validation complete: {len(mappings)} modules, {len(collections)} collections"
            )

        except Exception as e:
            results["errors"].append(f"Failed to load config: {e}")
            results["valid"] = False

        return results


def main():
    """Main entry point for config generator."""
    parser = argparse.ArgumentParser(
        description="Generate and manage FQCN mapping configurations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate config for all installed collections
  python3 config_generator.py --output fqcn_mapping.yml --include-all
  
  # Generate config based on existing playbooks
  python3 config_generator.py --analyze /path/to/playbooks --output custom_mapping.yml
  
  # Update existing config with new collections
  python3 config_generator.py --update existing_config.yml --collections ansible.posix community.general
  
  # Validate existing configuration
  python3 config_generator.py --validate fqcn_mapping.yml
        """,
    )

    parser.add_argument("--output", "-o", help="Output configuration file path")

    parser.add_argument(
        "--collections", "-c", nargs="+", help="Specific collections to include"
    )

    parser.add_argument("--analyze", "-a", help="Directory to analyze for used modules")

    parser.add_argument(
        "--include-all",
        action="store_true",
        help="Include all available modules (not just used ones)",
    )

    parser.add_argument("--update", "-u", help="Update existing configuration file")

    parser.add_argument("--validate", "-v", help="Validate configuration file")

    parser.add_argument(
        "--no-backup", action="store_true", help="Do not create backup when updating"
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    generator = ConfigGenerator()

    # Validate configuration
    if args.validate:
        results = generator.validate_config(args.validate)

        print(f"Validation Results for: {args.validate}")
        print("=" * 50)

        if results["valid"]:
            print("✅ Configuration is valid")
        else:
            print("❌ Configuration has errors:")
            for error in results["errors"]:
                print(f"  - {error}")

        if results["warnings"]:
            print("⚠️  Warnings:")
            for warning in results["warnings"]:
                print(f"  - {warning}")

        if results["statistics"]:
            stats = results["statistics"]
            print(f"\nStatistics:")
            print(f"  Total modules: {stats['total_modules']}")
            print(f"  Collections: {stats['collections_used']}")
            for collection in stats["collections"]:
                print(f"    - {collection}")

        return 0 if results["valid"] else 1

    # Generate new configuration
    if args.output or args.update:
        config = generator.generate_mapping_config(
            collections=args.collections,
            analyze_directory=args.analyze,
            include_all=args.include_all,
        )

        if args.update:
            # Update existing configuration
            success = generator.update_existing_config(
                args.update, config["fqcn_mappings"], backup=not args.no_backup
            )
            return 0 if success else 1
        else:
            # Save new configuration
            with open(args.output, "w") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=True)

            print(f"Generated configuration saved to: {args.output}")
            print(f"Total modules: {config['metadata']['total_modules']}")
            print(
                f"Collections analyzed: {len(config['metadata']['collections_analyzed'])}"
            )

            return 0

    # No action specified
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
