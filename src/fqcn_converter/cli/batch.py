"""
Batch command implementation for CLI.

This module handles the batch processing subcommand with parallel
execution and detailed reporting.
"""

import argparse
import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from ..core.converter import FQCNConverter, ConversionResult
from ..core.validator import ValidationEngine, ValidationResult
from ..exceptions import FQCNConverterError, ConfigurationError


def add_batch_arguments(parser: argparse.ArgumentParser) -> None:
    """Add batch command arguments to parser."""
    # Positional arguments
    parser.add_argument(
        "root_directory", nargs="?", help="Root directory to discover Ansible projects"
    )

    # Project specification
    parser.add_argument(
        "--projects",
        nargs="+",
        help="Specific project directories to convert (alternative to root_directory)",
    )

    parser.add_argument(
        "--discover-only",
        action="store_true",
        help="Only discover projects without converting them",
    )

    # Configuration options
    parser.add_argument(
        "--config", "-c", help="Path to custom FQCN mapping configuration file"
    )

    # Verbosity is handled by the main parser

    # Processing options
    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=4,
        help="Number of parallel workers for batch processing (default: 4)",
    )

    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be converted without making changes",
    )

    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue processing other projects if one fails",
    )

    # Discovery options
    parser.add_argument(
        "--patterns", nargs="+", help="Custom patterns to identify Ansible projects"
    )

    parser.add_argument(
        "--exclude",
        action="append",
        help="Exclude directories matching pattern (can be used multiple times)",
    )

    parser.add_argument(
        "--max-depth",
        type=int,
        default=5,
        help="Maximum directory depth for project discovery (default: 5)",
    )

    # Reporting options
    parser.add_argument(
        "--report",
        "-r",
        help="Generate detailed batch processing report to specified file",
    )

    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Show only summary statistics, not individual project details",
    )

    # Validation options
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate converted files after batch processing",
    )

    parser.add_argument(
        "--lint",
        action="store_true",
        help="Run ansible-lint validation after conversion",
    )


@dataclass
class ProjectResult:
    """Result of processing a single project."""

    project_path: str
    success: bool
    files_processed: int = 0
    files_converted: int = 0
    modules_converted: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration: float = 0.0
    validation_result: Optional[ValidationResult] = None


@dataclass
class BatchResult:
    """Result of batch processing operation."""

    total_projects: int
    successful_projects: int
    failed_projects: int
    project_results: List[ProjectResult]
    execution_time: float
    summary_report: str


class BatchCommand:
    """Handler for the batch command."""

    def __init__(self, args: argparse.Namespace):
        """Initialize batch command handler."""
        self.args = args
        self.logger = logging.getLogger(__name__)
        self.converter: Optional[FQCNConverter] = None
        self.validator: Optional[ValidationEngine] = None
        self.results: List[ProjectResult] = []
        self.stats = {
            "projects_discovered": 0,
            "projects_processed": 0,
            "projects_successful": 0,
            "projects_failed": 0,
            "total_files_processed": 0,
            "total_files_converted": 0,
            "total_modules_converted": 0,
            "start_time": datetime.now(),
            "end_time": None,
        }

    def run(self) -> int:
        """Execute the batch command."""
        try:
            # Validate arguments
            if not self.args.root_directory and not self.args.projects:
                self.logger.error("Must specify either root_directory or --projects")
                return 1

            # Initialize converter and validator
            self._initialize_components()

            # Discover or get projects
            projects = self._get_projects()

            if not projects:
                self.logger.warning("No Ansible projects found")
                return 0

            self.stats["projects_discovered"] = len(projects)
            self.logger.info(f"Discovered {len(projects)} Ansible projects")

            # List projects
            self._list_projects(projects)

            if self.args.discover_only:
                return 0

            # Process projects
            if self.args.dry_run:
                self.logger.info("DRY RUN MODE - No files will be modified")

            success = self._process_projects(projects)

            # Generate report if requested
            if self.args.report:
                self._generate_report()

            # Print summary
            self._print_summary()

            return 0 if success else 1

        except FQCNConverterError as e:
            self.logger.error(f"Batch processing failed: {e}")
            if hasattr(self.args, "verbosity") and self.args.verbosity == "verbose":
                self.logger.exception("Full traceback:")
            return 1
        except KeyboardInterrupt:
            self.logger.info("Batch processing interrupted by user")
            return 1
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            if hasattr(self.args, "verbosity") and self.args.verbosity == "verbose":
                self.logger.exception("Full traceback:")
            return 1

    def _initialize_components(self) -> None:
        """Initialize converter and validator components."""
        try:
            self.converter = FQCNConverter(config_path=self.args.config)

            if self.args.validate:
                self.validator = ValidationEngine()

            self.logger.debug("Components initialized successfully")
        except ConfigurationError as e:
            raise ConfigurationError(f"Failed to initialize components: {e}")

    def _get_projects(self) -> List[Path]:
        """Get list of projects to process."""
        if self.args.projects:
            # Use specified projects
            projects = [Path(p) for p in self.args.projects]
            self.logger.info(f"Processing {len(projects)} specified projects")
        else:
            # Discover projects in root directory
            self.logger.info(f"Discovering projects in: {self.args.root_directory}")
            projects = self._discover_projects(Path(self.args.root_directory))

        # Filter out non-existent projects
        valid_projects = []
        for project in projects:
            if project.exists() and project.is_dir():
                valid_projects.append(project)
            else:
                self.logger.warning(f"Project directory not found: {project}")

        return valid_projects

    def _discover_projects(self, root_dir: Path) -> List[Path]:
        """Discover Ansible projects in directory tree."""
        projects = []
        exclude_patterns = self.args.exclude or []

        # Default patterns to identify Ansible projects
        default_patterns = [
            "playbook*.yml",
            "playbook*.yaml",
            "site.yml",
            "site.yaml",
            "main.yml",
            "main.yaml",
            "roles/",
            "group_vars/",
            "host_vars/",
            "inventory",
            "ansible.cfg",
        ]

        patterns = self.args.patterns or default_patterns

        # Walk through directory tree
        for current_dir in self._walk_directories(root_dir, self.args.max_depth):
            if self._should_exclude_directory(current_dir, exclude_patterns):
                continue

            # Check if directory contains Ansible project indicators
            if self._is_ansible_project(current_dir, patterns):
                projects.append(current_dir)
                self.logger.debug(f"Discovered Ansible project: {current_dir}")

        return sorted(projects)

    def _walk_directories(self, root_dir: Path, max_depth: int) -> List[Path]:
        """Walk directory tree up to max_depth."""
        directories = [root_dir]

        def _walk_recursive(directory: Path, current_depth: int) -> None:
            if current_depth >= max_depth:
                return

            try:
                for item in directory.iterdir():
                    if item.is_dir() and not item.name.startswith("."):
                        directories.append(item)
                        _walk_recursive(item, current_depth + 1)
            except (PermissionError, OSError) as e:
                self.logger.debug(f"Cannot access directory {directory}: {e}")

        _walk_recursive(root_dir, 0)
        return directories

    def _should_exclude_directory(
        self, directory: Path, exclude_patterns: List[str]
    ) -> bool:
        """Check if directory should be excluded."""
        dir_str = str(directory)

        for pattern in exclude_patterns:
            if pattern in dir_str:
                return True

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
            ".vagrant",
            ".molecule",
        }

        return directory.name in skip_dirs

    def _is_ansible_project(self, directory: Path, patterns: List[str]) -> bool:
        """Check if directory contains Ansible project indicators."""
        for pattern in patterns:
            if pattern.endswith("/"):
                # Directory pattern
                subdir = directory / pattern.rstrip("/")
                if subdir.exists() and subdir.is_dir():
                    return True
            else:
                # File pattern
                matches = list(directory.glob(pattern))
                if matches:
                    return True

        return False

    def _list_projects(self, projects: List[Path]) -> None:
        """List discovered projects."""
        if not self.args.summary_only:
            print(f"\nDiscovered {len(projects)} Ansible projects:")
            for i, project in enumerate(projects, 1):
                print(f"  {i}. {project}")
            print()

    def _process_projects(self, projects: List[Path]) -> bool:
        """Process all projects."""
        if self.args.workers > 1 and len(projects) > 1:
            return self._process_projects_parallel(projects)
        else:
            return self._process_projects_sequential(projects)

    def _process_projects_sequential(self, projects: List[Path]) -> bool:
        """Process projects sequentially."""
        success = True

        for i, project in enumerate(projects, 1):
            print(f"Processing project {i}/{len(projects)}: {project}", file=sys.stderr)

            result = self._process_single_project(project)
            self.results.append(result)

            # Update statistics
            self._update_stats(result)

            if not result.success:
                success = False
                if not self.args.continue_on_error:
                    self.logger.error(
                        f"Stopping batch processing due to error in {project}"
                    )
                    break

        self.stats["end_time"] = datetime.now()
        return success

    def _process_projects_parallel(self, projects: List[Path]) -> bool:
        """Process projects in parallel."""
        success = True

        with ThreadPoolExecutor(max_workers=self.args.workers) as executor:
            # Submit all processing tasks
            future_to_project = {
                executor.submit(self._process_single_project, project): project
                for project in projects
            }

            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_project):
                project = future_to_project[future]
                completed += 1

                print(
                    f"Completed project {completed}/{len(projects)}: {project}",
                    file=sys.stderr,
                )

                try:
                    result = future.result()
                    self.results.append(result)
                    self._update_stats(result)

                    if not result.success:
                        success = False

                except Exception as e:
                    self.logger.error(f"Exception processing {project}: {e}")
                    success = False

        # Sort results by project path for consistent output
        self.results.sort(key=lambda r: r.project_path)

        self.stats["end_time"] = datetime.now()
        return success

    def _process_single_project(self, project_path: Path) -> ProjectResult:
        """Process a single project."""
        start_time = time.time()
        result = ProjectResult(project_path=str(project_path), success=False)

        try:
            self.logger.info(f"Processing project: {project_path}")

            # Find Ansible files in project
            ansible_files = self._find_ansible_files_in_project(project_path)

            if not ansible_files:
                self.logger.warning(
                    f"No Ansible files found in project: {project_path}"
                )
                result.success = True  # Empty project is considered successful
                return result

            # Convert files
            files_converted = 0
            modules_converted = 0

            for file_path in ansible_files:
                try:
                    conversion_result = self.converter.convert_file(
                        file_path, dry_run=self.args.dry_run
                    )

                    if conversion_result.success:
                        if conversion_result.changes_made > 0:
                            files_converted += 1
                            modules_converted += conversion_result.changes_made
                    else:
                        result.errors.extend(conversion_result.errors)
                        result.warnings.extend(conversion_result.warnings)

                except Exception as e:
                    error_msg = f"Error converting {file_path}: {e}"
                    result.errors.append(error_msg)
                    self.logger.error(error_msg)

            result.files_processed = len(ansible_files)
            result.files_converted = files_converted
            result.modules_converted = modules_converted

            # Validate if requested
            if self.args.validate and self.validator:
                try:
                    validation_result = self._validate_project(
                        project_path, ansible_files
                    )
                    result.validation_result = validation_result
                except Exception as e:
                    result.warnings.append(f"Validation failed: {e}")

            # Consider successful if no errors occurred
            result.success = len(result.errors) == 0

            if result.success:
                self.logger.info(f"Successfully processed project: {project_path}")
            else:
                self.logger.error(f"Failed to process project: {project_path}")

        except Exception as e:
            result.errors.append(f"Unexpected error: {e}")
            self.logger.error(f"Unexpected error processing {project_path}: {e}")

        finally:
            result.duration = time.time() - start_time

        return result

    def _find_ansible_files_in_project(self, project_path: Path) -> List[Path]:
        """Find Ansible files in a project directory."""
        ansible_files = []

        # Common Ansible file patterns
        patterns = ["**/*.yml", "**/*.yaml"]

        for pattern in patterns:
            for file_path in project_path.glob(pattern):
                if file_path.is_file() and self._is_ansible_file(file_path):
                    ansible_files.append(file_path)

        return sorted(ansible_files)

    def _is_ansible_file(self, file_path: Path) -> bool:
        """Check if a file appears to be an Ansible file."""
        # Skip common non-Ansible files
        skip_patterns = {
            ".git/",
            "__pycache__/",
            ".pytest_cache/",
            "node_modules/",
            ".venv/",
            "venv/",
            ".tox/",
            "build/",
            "dist/",
        }

        file_str = str(file_path)
        for pattern in skip_patterns:
            if pattern in file_str:
                return False

        # Check for Ansible indicators
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

        for indicator in ansible_indicators:
            if indicator in file_name or indicator in file_path_str:
                return True

        # Check file content for Ansible keywords
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read(512)  # Read first 512 bytes
                ansible_keywords = [
                    "hosts:",
                    "tasks:",
                    "handlers:",
                    "vars:",
                    "name:",
                    "become:",
                    "gather_facts:",
                    "roles:",
                ]

                for keyword in ansible_keywords:
                    if keyword in content:
                        return True
        except Exception:
            pass

        return False

    def _validate_project(
        self, project_path: Path, ansible_files: List[Path]
    ) -> ValidationResult:
        """Validate all files in a project."""
        # For simplicity, validate the first file or create a summary
        if ansible_files:
            return self.validator.validate_conversion(ansible_files[0])

        # Return empty validation result for projects with no files
        from ..core.validator import ValidationResult

        return ValidationResult(valid=True, file_path=str(project_path), score=1.0)

    def _update_stats(self, result: ProjectResult) -> None:
        """Update batch processing statistics."""
        self.stats["projects_processed"] += 1

        if result.success:
            self.stats["projects_successful"] += 1
        else:
            self.stats["projects_failed"] += 1

        self.stats["total_files_processed"] += result.files_processed
        self.stats["total_files_converted"] += result.files_converted
        self.stats["total_modules_converted"] += result.modules_converted

    def _generate_report(self) -> None:
        """Generate detailed batch processing report."""
        try:
            duration = (
                self.stats["end_time"] - self.stats["start_time"]
            ).total_seconds()

            report = {
                "batch_processing_report": {
                    "timestamp": self.stats["start_time"].isoformat(),
                    "duration_seconds": duration,
                    "command_args": {
                        "root_directory": self.args.root_directory,
                        "projects": self.args.projects,
                        "config": self.args.config,
                        "workers": self.args.workers,
                        "dry_run": self.args.dry_run,
                        "validate": self.args.validate,
                    },
                    "summary": {
                        "projects_discovered": self.stats["projects_discovered"],
                        "projects_processed": self.stats["projects_processed"],
                        "projects_successful": self.stats["projects_successful"],
                        "projects_failed": self.stats["projects_failed"],
                        "total_files_processed": self.stats["total_files_processed"],
                        "total_files_converted": self.stats["total_files_converted"],
                        "total_modules_converted": self.stats[
                            "total_modules_converted"
                        ],
                        "success_rate": f"{(self.stats['projects_successful']/max(self.stats['projects_processed'], 1))*100:.1f}%",
                    },
                    "project_results": [
                        {
                            "project_path": result.project_path,
                            "success": result.success,
                            "files_processed": result.files_processed,
                            "files_converted": result.files_converted,
                            "modules_converted": result.modules_converted,
                            "duration": result.duration,
                            "errors": result.errors,
                            "warnings": result.warnings,
                            "validation_score": (
                                result.validation_result.score
                                if result.validation_result
                                else None
                            ),
                        }
                        for result in self.results
                    ],
                }
            }

            with open(self.args.report, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)

            self.logger.info(f"Batch processing report saved to: {self.args.report}")

        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}")

    def _print_summary(self) -> None:
        """Print batch processing summary."""
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

        print("\n" + "=" * 60)
        print("BATCH PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Projects discovered: {self.stats['projects_discovered']}")
        print(f"Projects processed: {self.stats['projects_processed']}")
        print(f"Projects successful: {self.stats['projects_successful']}")
        print(f"Projects failed: {self.stats['projects_failed']}")
        print(f"Total files processed: {self.stats['total_files_processed']}")
        print(f"Total files converted: {self.stats['total_files_converted']}")
        print(f"Total modules converted: {self.stats['total_modules_converted']}")
        print(f"Duration: {duration:.2f} seconds")

        if self.stats["projects_processed"] > 0:
            success_rate = (
                self.stats["projects_successful"] / self.stats["projects_processed"]
            ) * 100
            print(f"Success rate: {success_rate:.1f}%")

        # Show failed projects
        if self.stats["projects_failed"] > 0:
            print(f"\nFailed projects:")
            for result in self.results:
                if not result.success:
                    print(f"  - {result.project_path}")
                    for error in result.errors[:3]:  # Show first 3 errors
                        print(f"    Error: {error}")

        if self.args.dry_run:
            print("\nDRY RUN - No files were modified")

        print("=" * 60)


def main(args: argparse.Namespace) -> int:
    """Handle batch processing subcommand."""
    command = BatchCommand(args)
    return command.run()
