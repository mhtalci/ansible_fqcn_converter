"""
Convert command implementation for CLI.

This module handles the convert subcommand with options for dry-run,
verbosity, and custom configuration.
"""

import argparse
import json
import logging
import shutil
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..core.converter import FQCNConverter, ConversionResult
from ..exceptions import (
    FQCNConverterError,
    ConfigurationError,
    ConversionError,
    FileAccessError,
)


def add_convert_arguments(parser: argparse.ArgumentParser) -> None:
    """Add convert command arguments to parser."""
    # Positional arguments
    parser.add_argument(
        "files", nargs="+", help="Ansible files or directories to convert"
    )

    # Configuration options
    parser.add_argument(
        "--config", "-c", help="Path to custom FQCN mapping configuration file"
    )

    # Conversion options
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be converted without making changes",
    )

    parser.add_argument(
        "--backup",
        "-b",
        action="store_true",
        help="Create backup files before conversion",
    )

    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup files (overrides default backup behavior)",
    )

    # Progress and reporting
    parser.add_argument(
        "--progress", action="store_true", help="Show progress bar for large operations"
    )

    parser.add_argument(
        "--report", help="Generate detailed conversion report to specified file"
    )

    # Validation options
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip YAML syntax validation after conversion",
    )

    parser.add_argument(
        "--lint",
        action="store_true",
        help="Run ansible-lint validation after conversion",
    )

    # Advanced options
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force conversion even if files appear already converted",
    )

    parser.add_argument(
        "--exclude",
        action="append",
        help="Exclude files/directories matching pattern (can be used multiple times)",
    )


class ConvertCommand:
    """Handler for the convert command."""

    def __init__(self, args: argparse.Namespace):
        """Initialize convert command handler."""
        self.args = args
        self.logger = logging.getLogger(__name__)
        self.converter: Optional[FQCNConverter] = None
        self.results: List[ConversionResult] = []
        self.stats = {
            "files_processed": 0,
            "files_converted": 0,
            "files_failed": 0,
            "total_changes": 0,
            "start_time": datetime.now(),
            "end_time": None,
        }

    def run(self) -> int:
        """Execute the convert command."""
        try:
            # Initialize converter
            self._initialize_converter()

            # Discover files to convert
            files_to_convert = self._discover_files()

            if not files_to_convert:
                self.logger.warning("No Ansible files found to convert")
                return 0

            self.logger.info(f"Found {len(files_to_convert)} files to convert")

            if self.args.dry_run:
                self.logger.info("DRY RUN MODE - No files will be modified")

            # Convert files
            success = self._convert_files(files_to_convert)

            # Generate report if requested
            if self.args.report:
                self._generate_report()

            # Print summary
            self._print_summary()

            return 0 if success else 1

        except FQCNConverterError as e:
            self.logger.error(f"Conversion failed: {e}")
            if hasattr(self.args, "verbosity") and self.args.verbosity == "verbose":
                self.logger.exception("Full traceback:")
            return 1
        except KeyboardInterrupt:
            self.logger.info("Conversion interrupted by user")
            return 1
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            if hasattr(self.args, "verbosity") and self.args.verbosity == "verbose":
                self.logger.exception("Full traceback:")
            return 1

    def _initialize_converter(self) -> None:
        """Initialize the FQCN converter."""
        try:
            self.converter = FQCNConverter(config_path=self.args.config)
            self.logger.debug("Converter initialized successfully")
        except ConfigurationError as e:
            raise ConfigurationError(f"Failed to initialize converter: {e}")

    def _discover_files(self) -> List[Path]:
        """Discover Ansible files to convert."""
        files_to_convert = []
        exclude_patterns = self.args.exclude or []

        for file_arg in self.args.files:
            path = Path(file_arg)

            if path.is_file():
                if self._should_process_file(path, exclude_patterns):
                    files_to_convert.append(path)
            elif path.is_dir():
                # Recursively find Ansible files
                ansible_files = self._find_ansible_files(path, exclude_patterns)
                files_to_convert.extend(ansible_files)
            else:
                self.logger.warning(f"Path not found: {path}")

        return sorted(files_to_convert)

    def _find_ansible_files(
        self, directory: Path, exclude_patterns: List[str]
    ) -> List[Path]:
        """Find Ansible files in a directory."""
        ansible_files = []

        # Common Ansible file patterns
        patterns = ["**/*.yml", "**/*.yaml"]

        for pattern in patterns:
            for file_path in directory.glob(pattern):
                if file_path.is_file() and self._should_process_file(
                    file_path, exclude_patterns
                ):
                    # Additional checks for Ansible files
                    if self._is_ansible_file(file_path):
                        ansible_files.append(file_path)

        return ansible_files

    def _should_process_file(
        self, file_path: Path, exclude_patterns: List[str]
    ) -> bool:
        """Check if a file should be processed."""
        file_str = str(file_path)

        # Check exclude patterns
        for pattern in exclude_patterns:
            if pattern in file_str:
                self.logger.debug(
                    f"Excluding file due to pattern '{pattern}': {file_path}"
                )
                return False

        # Skip common non-Ansible directories
        skip_dirs = {
            ".git",
            ".github",
            "__pycache__",
            ".pytest_cache",
            "node_modules",
            ".venv",
            "venv",
            ".tox",
            "build",
            "dist",
        }

        for part in file_path.parts:
            if part in skip_dirs:
                return False

        return True

    def _is_ansible_file(self, file_path: Path) -> bool:
        """Check if a file appears to be an Ansible file."""
        # Check file extension
        if file_path.suffix not in [".yml", ".yaml"]:
            return False

        # Check for common Ansible file indicators
        ansible_indicators = [
            "tasks",
            "handlers",
            "vars",
            "defaults",
            "meta",
            "playbook",
            "site.yml",
            "main.yml",
        ]

        file_name = file_path.name.lower()
        file_path_str = str(file_path).lower()

        # Check filename and path for Ansible indicators
        for indicator in ansible_indicators:
            if indicator in file_name or indicator in file_path_str:
                return True

        # Check file content for Ansible keywords (first few lines)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read(1024)  # Read first 1KB
                ansible_keywords = [
                    "hosts:",
                    "tasks:",
                    "handlers:",
                    "vars:",
                    "name:",
                    "become:",
                    "gather_facts:",
                    "roles:",
                    "include:",
                    "import_tasks:",
                    "include_tasks:",
                ]

                for keyword in ansible_keywords:
                    if keyword in content:
                        return True
        except Exception:
            # If we can't read the file, skip it
            return False

        return False

    def _convert_files(self, files: List[Path]) -> bool:
        """Convert the discovered files."""
        success = True

        for i, file_path in enumerate(files, 1):
            if self.args.progress:
                print(f"Processing {i}/{len(files)}: {file_path}", file=sys.stderr)

            try:
                # Create backup if requested and not dry run
                if (
                    self.args.backup
                    and not self.args.dry_run
                    and not self.args.no_backup
                ):
                    self._create_backup(file_path)

                # Convert the file
                result = self.converter.convert_file(
                    file_path, dry_run=self.args.dry_run
                )
                self.results.append(result)

                # Update statistics
                self.stats["files_processed"] += 1
                if result.success:
                    if result.changes_made > 0:
                        self.stats["files_converted"] += 1
                        self.stats["total_changes"] += result.changes_made

                        if self.args.dry_run:
                            self.logger.info(
                                f"Would convert {result.changes_made} modules in {file_path}"
                            )
                        else:
                            self.logger.info(
                                f"Converted {result.changes_made} modules in {file_path}"
                            )
                    else:
                        self.logger.debug(f"No changes needed for {file_path}")
                else:
                    self.stats["files_failed"] += 1
                    success = False
                    self.logger.error(
                        f"Failed to convert {file_path}: {'; '.join(result.errors)}"
                    )

                # Show warnings if any
                for warning in result.warnings:
                    self.logger.warning(f"{file_path}: {warning}")

            except Exception as e:
                self.stats["files_processed"] += 1
                self.stats["files_failed"] += 1
                success = False
                self.logger.error(f"Error processing {file_path}: {e}")

        self.stats["end_time"] = datetime.now()
        return success

    def _create_backup(self, file_path: Path) -> None:
        """Create a backup of the file."""
        backup_path = file_path.with_suffix(file_path.suffix + ".fqcn_backup")

        try:
            shutil.copy2(file_path, backup_path)
            self.logger.debug(f"Created backup: {backup_path}")
        except Exception as e:
            self.logger.warning(f"Failed to create backup for {file_path}: {e}")

    def _generate_report(self) -> None:
        """Generate detailed conversion report."""
        try:
            duration = (
                self.stats["end_time"] - self.stats["start_time"]
            ).total_seconds()

            report = {
                "conversion_report": {
                    "timestamp": self.stats["start_time"].isoformat(),
                    "duration_seconds": duration,
                    "command_args": {
                        "files": self.args.files,
                        "config": self.args.config,
                        "dry_run": self.args.dry_run,
                        "backup": self.args.backup,
                        "force": self.args.force,
                    },
                    "summary": {
                        "files_processed": self.stats["files_processed"],
                        "files_converted": self.stats["files_converted"],
                        "files_failed": self.stats["files_failed"],
                        "total_changes": self.stats["total_changes"],
                        "success_rate": f"{(self.stats['files_converted']/max(self.stats['files_processed'], 1))*100:.1f}%",
                    },
                    "results": [
                        {
                            "file_path": result.file_path,
                            "success": result.success,
                            "changes_made": result.changes_made,
                            "errors": result.errors,
                            "warnings": result.warnings,
                        }
                        for result in self.results
                    ],
                }
            }

            with open(self.args.report, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)

            self.logger.info(f"Conversion report saved to: {self.args.report}")

        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}")

    def _print_summary(self) -> None:
        """Print conversion summary."""
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

        print("\n" + "=" * 60)
        print("FQCN CONVERSION SUMMARY")
        print("=" * 60)
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Files converted: {self.stats['files_converted']}")
        print(f"Files failed: {self.stats['files_failed']}")
        print(f"Total changes: {self.stats['total_changes']}")
        print(f"Duration: {duration:.2f} seconds")

        if self.stats["files_failed"] > 0:
            print(f"\nFailed files:")
            for result in self.results:
                if not result.success:
                    print(f"  - {result.file_path}: {'; '.join(result.errors)}")

        if self.args.dry_run:
            print("\nDRY RUN - No files were modified")

        print("=" * 60)


def main(args: argparse.Namespace) -> int:
    """Handle convert subcommand."""
    command = ConvertCommand(args)
    return command.run()
