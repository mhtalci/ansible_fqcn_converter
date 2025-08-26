"""
Validate command implementation for CLI.

This module handles the validate subcommand with comprehensive
validation reporting and scoring.
"""

import argparse
import json
import logging
import subprocess
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.validator import ValidationEngine, ValidationIssue, ValidationResult
from ..exceptions import FileAccessError, FQCNConverterError, ValidationError


def add_validate_arguments(parser: argparse.ArgumentParser) -> None:
    """Add validate command arguments to parser."""
    # Positional arguments
    parser.add_argument(
        "files",
        nargs="*",
        default=["."],
        help="Ansible files or directories to validate (default: current directory)",
    )

    # Configuration options
    parser.add_argument(
        "--config", "-c", help="Path to custom FQCN mapping configuration file"
    )

    # Verbosity is handled by the main parser

    # Validation options
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Use strict validation mode with enhanced checks",
    )

    parser.add_argument(
        "--score",
        action="store_true",
        help="Calculate and display FQCN conversion completeness score",
    )

    parser.add_argument(
        "--lint",
        action="store_true",
        help="Run ansible-lint validation in addition to FQCN checks",
    )

    # Reporting options
    parser.add_argument(
        "--report", help="Generate detailed validation report to specified file"
    )

    parser.add_argument(
        "--format",
        choices=["text", "json", "junit"],
        default="text",
        help="Output format for validation results (default: text)",
    )

    # Filtering options
    parser.add_argument(
        "--exclude",
        action="append",
        help="Exclude files/directories matching pattern (can be used multiple times)",
    )

    parser.add_argument(
        "--include-warnings",
        action="store_true",
        help="Include warnings in validation results",
    )

    # Batch validation options
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Enable parallel validation for multiple files",
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers for validation (default: 4)",
    )


class ValidateCommand:
    """Handler for the validate command."""

    def __init__(self, args: argparse.Namespace):
        """Initialize validate command handler."""
        self.args = args
        self.logger = logging.getLogger(__name__)
        self.validator: Optional[ValidationEngine] = None
        self.results: List[ValidationResult] = []
        self.stats = {
            "files_validated": 0,
            "files_passed": 0,
            "files_failed": 0,
            "total_issues": 0,
            "total_errors": 0,
            "total_warnings": 0,
            "average_score": 0.0,
            "start_time": datetime.now(),
            "end_time": None,
        }

    def run(self) -> int:
        """Execute the validate command."""
        try:
            # Initialize validator
            self._initialize_validator()

            # Discover files to validate
            files_to_validate = self._discover_files()

            if not files_to_validate:
                self.logger.warning("No Ansible files found to validate")
                return 0

            self.logger.info(f"Found {len(files_to_validate)} files to validate")

            # Validate files
            success = self._validate_files(files_to_validate)

            # Generate report if requested
            if self.args.report:
                self._generate_report()

            # Print results
            self._print_results()

            return 0 if success else 1

        except FQCNConverterError as e:
            self.logger.error(f"Validation failed: {e}")
            if hasattr(self.args, "verbosity") and self.args.verbosity == "verbose":
                self.logger.exception("Full traceback:")
            return 1
        except KeyboardInterrupt:
            self.logger.info("Validation interrupted by user")
            return 1
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            if hasattr(self.args, "verbosity") and self.args.verbosity == "verbose":
                self.logger.exception("Full traceback:")
            return 1

    def _initialize_validator(self) -> None:
        """Initialize the validation engine."""
        try:
            self.validator = ValidationEngine()
            self.logger.debug("Validator initialized successfully")
        except Exception as e:
            raise ValidationError(f"Failed to initialize validator: {e}")

    def _discover_files(self) -> List[Path]:
        """Discover Ansible files to validate."""
        files_to_validate = []
        exclude_patterns = self.args.exclude or []

        for file_arg in self.args.files:
            path = Path(file_arg)

            if path.is_file():
                if self._should_process_file(path, exclude_patterns):
                    files_to_validate.append(path)
            elif path.is_dir():
                # Recursively find Ansible files
                ansible_files = self._find_ansible_files(path, exclude_patterns)
                files_to_validate.extend(ansible_files)
            else:
                self.logger.warning(f"Path not found: {path}")

        return sorted(files_to_validate)

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

    def _validate_files(self, files: List[Path]) -> bool:
        """Validate the discovered files."""
        if self.args.parallel and len(files) > 1:
            return self._validate_files_parallel(files)
        else:
            return self._validate_files_sequential(files)

    def _validate_files_sequential(self, files: List[Path]) -> bool:
        """Validate files sequentially."""
        success = True

        for i, file_path in enumerate(files, 1):
            if self.args.format == "text":
                print(f"Validating {i}/{len(files)}: {file_path}", file=sys.stderr)

            try:
                result = self.validator.validate_conversion(file_path)
                self.results.append(result)

                # Update statistics
                self._update_stats(result)

                # Run ansible-lint if requested
                if self.args.lint:
                    self._run_ansible_lint(file_path, result)

                if not result.valid:
                    success = False

            except Exception as e:
                self.logger.error(f"Error validating {file_path}: {e}")
                success = False

        self.stats["end_time"] = datetime.now()
        return success

    def _validate_files_parallel(self, files: List[Path]) -> bool:
        """Validate files in parallel."""
        success = True

        with ThreadPoolExecutor(max_workers=self.args.workers) as executor:
            # Submit all validation tasks
            future_to_file = {
                executor.submit(self._validate_single_file, file_path): file_path
                for file_path in files
            }

            # Collect results as they complete
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    if result:
                        self.results.append(result)
                        self._update_stats(result)

                        if not result.valid:
                            success = False
                    else:
                        success = False

                except Exception as e:
                    self.logger.error(f"Exception validating {file_path}: {e}")
                    success = False

        # Sort results by file path for consistent output
        self.results.sort(key=lambda r: r.file_path)

        self.stats["end_time"] = datetime.now()
        return success

    def _validate_single_file(self, file_path: Path) -> Optional[ValidationResult]:
        """Validate a single file (for parallel processing)."""
        try:
            result = self.validator.validate_conversion(file_path)

            # Run ansible-lint if requested
            if self.args.lint:
                self._run_ansible_lint(file_path, result)

            return result

        except Exception as e:
            self.logger.error(f"Error validating {file_path}: {e}")
            return None

    def _update_stats(self, result: ValidationResult) -> None:
        """Update validation statistics."""
        self.stats["files_validated"] += 1

        if result.valid:
            self.stats["files_passed"] += 1
        else:
            self.stats["files_failed"] += 1

        self.stats["total_issues"] += len(result.issues)
        self.stats["total_errors"] += sum(
            1 for issue in result.issues if issue.severity == "error"
        )
        self.stats["total_warnings"] += sum(
            1 for issue in result.issues if issue.severity == "warning"
        )

        # Update average score
        total_score = (
            self.stats["average_score"] * (self.stats["files_validated"] - 1)
            + result.score
        )
        self.stats["average_score"] = total_score / self.stats["files_validated"]

    def _run_ansible_lint(self, file_path: Path, result: ValidationResult) -> None:
        """Run ansible-lint on a file and add results to validation result."""
        try:
            lint_result = subprocess.run(
                ["ansible-lint", "--parseable", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if lint_result.returncode != 0 and lint_result.stdout:
                # Parse ansible-lint output and add as issues
                for line in lint_result.stdout.strip().split("\n"):
                    if line.strip():
                        # Parse ansible-lint format: filename:line:column: [severity] message
                        parts = line.split(":", 3)
                        if len(parts) >= 4:
                            try:
                                line_num = int(parts[1])
                                col_num = int(parts[2]) if parts[2].isdigit() else 1
                                message = parts[3].strip()

                                result.issues.append(
                                    ValidationIssue(
                                        line_number=line_num,
                                        column=col_num,
                                        severity="warning",
                                        message=f"ansible-lint: {message}",
                                        suggestion="Fix ansible-lint issues",
                                    )
                                )
                            except (ValueError, IndexError):
                                # If parsing fails, add as generic issue
                                result.issues.append(
                                    ValidationIssue(
                                        line_number=1,
                                        column=1,
                                        severity="warning",
                                        message=f"ansible-lint: {line}",
                                        suggestion="Fix ansible-lint issues",
                                    )
                                )

        except subprocess.TimeoutExpired:
            self.logger.warning(f"ansible-lint timeout for {file_path}")
        except FileNotFoundError:
            self.logger.debug("ansible-lint not found, skipping lint validation")
        except Exception as e:
            self.logger.warning(f"Error running ansible-lint on {file_path}: {e}")

    def _generate_report(self) -> None:
        """Generate detailed validation report."""
        try:
            if self.args.format == "json":
                self._generate_json_report()
            elif self.args.format == "junit":
                self._generate_junit_report()
            else:
                self._generate_text_report()

        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}")

    def _generate_json_report(self) -> None:
        """Generate JSON format report."""
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

        report = {
            "validation_report": {
                "timestamp": self.stats["start_time"].isoformat(),
                "duration_seconds": duration,
                "command_args": {
                    "files": self.args.files,
                    "strict": self.args.strict,
                    "score": self.args.score,
                    "lint": self.args.lint,
                    "include_warnings": self.args.include_warnings,
                },
                "summary": {
                    "files_validated": self.stats["files_validated"],
                    "files_passed": self.stats["files_passed"],
                    "files_failed": self.stats["files_failed"],
                    "total_issues": self.stats["total_issues"],
                    "total_errors": self.stats["total_errors"],
                    "total_warnings": self.stats["total_warnings"],
                    "average_score": self.stats["average_score"],
                    "success_rate": f"{(self.stats['files_passed']/max(self.stats['files_validated'], 1))*100:.1f}%",
                },
                "results": [
                    {
                        "file_path": result.file_path,
                        "valid": result.valid,
                        "score": result.score,
                        "issues": [
                            {
                                "line_number": issue.line_number,
                                "column": issue.column,
                                "severity": issue.severity,
                                "message": issue.message,
                                "suggestion": issue.suggestion,
                            }
                            for issue in result.issues
                            if self.args.include_warnings or issue.severity == "error"
                        ],
                    }
                    for result in self.results
                ],
            }
        }

        with open(self.args.report, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"JSON validation report saved to: {self.args.report}")

    def _generate_junit_report(self) -> None:
        """Generate JUnit XML format report."""
        root = ET.Element("testsuite")
        root.set("name", "FQCN Validation")
        root.set("tests", str(self.stats["files_validated"]))
        root.set("failures", str(self.stats["files_failed"]))
        root.set("errors", "0")
        root.set(
            "time",
            str((self.stats["end_time"] - self.stats["start_time"]).total_seconds()),
        )

        for result in self.results:
            testcase = ET.SubElement(root, "testcase")
            testcase.set("classname", "FQCN")
            testcase.set("name", result.file_path)
            testcase.set("time", "0")

            if not result.valid:
                failure = ET.SubElement(testcase, "failure")
                failure.set(
                    "message", f"Validation failed with {len(result.issues)} issues"
                )

                failure_text = []
                for issue in result.issues:
                    if self.args.include_warnings or issue.severity == "error":
                        failure_text.append(
                            f"Line {issue.line_number}: [{issue.severity.upper()}] {issue.message}"
                        )

                failure.text = "\n".join(failure_text)

        tree = ET.ElementTree(root)
        tree.write(self.args.report, encoding="utf-8", xml_declaration=True)

        self.logger.info(f"JUnit validation report saved to: {self.args.report}")

    def _generate_text_report(self) -> None:
        """Generate text format report."""
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

        with open(self.args.report, "w", encoding="utf-8") as f:
            f.write("FQCN VALIDATION REPORT\n")
            f.write("=" * 60 + "\n\n")

            f.write(f"Timestamp: {self.stats['start_time'].isoformat()}\n")
            f.write(f"Duration: {duration:.2f} seconds\n\n")

            f.write("SUMMARY\n")
            f.write("-" * 20 + "\n")
            f.write(f"Files validated: {self.stats['files_validated']}\n")
            f.write(f"Files passed: {self.stats['files_passed']}\n")
            f.write(f"Files failed: {self.stats['files_failed']}\n")
            f.write(f"Total issues: {self.stats['total_issues']}\n")
            f.write(f"Total errors: {self.stats['total_errors']}\n")
            f.write(f"Total warnings: {self.stats['total_warnings']}\n")
            f.write(f"Average score: {self.stats['average_score']:.2f}\n\n")

            f.write("DETAILED RESULTS\n")
            f.write("-" * 20 + "\n\n")

            for result in self.results:
                f.write(f"File: {result.file_path}\n")
                f.write(f"Valid: {result.valid}\n")
                f.write(f"Score: {result.score:.2f}\n")

                if result.issues:
                    f.write("Issues:\n")
                    for issue in result.issues:
                        if self.args.include_warnings or issue.severity == "error":
                            f.write(
                                f"  Line {issue.line_number}: [{issue.severity.upper()}] {issue.message}\n"
                            )
                            if issue.suggestion:
                                f.write(f"    Suggestion: {issue.suggestion}\n")

                f.write("\n")

        self.logger.info(f"Text validation report saved to: {self.args.report}")

    def _print_results(self) -> None:
        """Print validation results to console."""
        if self.args.format == "json":
            self._print_json_results()
        else:
            self._print_text_results()

    def _print_json_results(self) -> None:
        """Print results in JSON format."""
        results = []
        for result in self.results:
            result_dict = {
                "file_path": result.file_path,
                "valid": result.valid,
                "score": result.score if self.args.score else None,
                "issues": [
                    {
                        "line_number": issue.line_number,
                        "severity": issue.severity,
                        "message": issue.message,
                    }
                    for issue in result.issues
                    if self.args.include_warnings or issue.severity == "error"
                ],
            }
            results.append(result_dict)

        print(json.dumps(results, indent=2))

    def _print_text_results(self) -> None:
        """Print results in text format."""
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

        print("\n" + "=" * 60)
        print("FQCN VALIDATION RESULTS")
        print("=" * 60)

        # Print summary
        print(f"Files validated: {self.stats['files_validated']}")
        print(f"Files passed: {self.stats['files_passed']}")
        print(f"Files failed: {self.stats['files_failed']}")
        print(f"Total issues: {self.stats['total_issues']}")
        print(f"Duration: {duration:.2f} seconds")

        if self.args.score:
            print(f"Average FQCN score: {self.stats['average_score']:.2f}")

        # Print detailed results for failed files
        if self.stats["files_failed"] > 0:
            print(f"\nFAILED FILES:")
            for result in self.results:
                if not result.valid:
                    print(f"\n{result.file_path}:")
                    if self.args.score:
                        print(f"  Score: {result.score:.2f}")

                    for issue in result.issues:
                        if self.args.include_warnings or issue.severity == "error":
                            print(
                                f"  Line {issue.line_number}: [{issue.severity.upper()}] {issue.message}"
                            )

        # Print score details if requested
        if self.args.score and self.results:
            print(f"\nSCORE DETAILS:")
            for result in self.results:
                status = "PASS" if result.valid else "FAIL"
                print(f"  {result.file_path}: {result.score:.2f} ({status})")

        print("=" * 60)


def main(args: argparse.Namespace) -> int:
    """Handle validate subcommand."""
    command = ValidateCommand(args)
    return command.run()
