#!/usr/bin/env python3
"""
Release preparation script for FQCN Converter.

This script automates the release preparation process including version bumping,
changelog generation, and validation checks.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fqcn_converter.version import VersionManager, VersionBumpType


class ReleasePreparator:
    """Handles release preparation tasks."""

    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = repo_path or Path.cwd()
        self.vm = VersionManager(repo_path)

    def validate_pre_release_conditions(self) -> bool:
        """Validate that all conditions are met for a release."""
        print("🔍 Validating pre-release conditions...")

        issues = []

        # Check git status
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            if result.stdout.strip():
                issues.append("Working directory has uncommitted changes")

        except subprocess.CalledProcessError:
            issues.append("Failed to check git status")

        # Check current branch
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            current_branch = result.stdout.strip()
            if current_branch != "main":
                issues.append(f"Not on main branch (currently on: {current_branch})")

        except subprocess.CalledProcessError:
            issues.append("Failed to check current branch")

        # Check version consistency
        validation_result = self.vm.validate_version_consistency()
        if not validation_result["consistent"]:
            issues.extend(validation_result["issues"])

        # Check if there are commits since last tag
        commits = self.vm.get_git_commits_since_tag()
        if not commits:
            issues.append("No commits found since last tag")

        if issues:
            print("❌ Pre-release validation failed:")
            for issue in issues:
                print(f"  - {issue}")
            return False

        print("✅ Pre-release validation passed")
        return True

    def calculate_next_version(self, bump_type: Optional[str] = None) -> str:
        """Calculate the next version number."""
        if bump_type:
            try:
                bump_enum = VersionBumpType(bump_type)
                next_version = self.vm.get_current_version().bump(bump_enum)
            except ValueError:
                print(f"Invalid bump type: {bump_type}")
                return None
        else:
            next_version = self.vm.calculate_next_version()

        return str(next_version)

    def update_version(self, new_version: str) -> bool:
        """Update version files with new version."""
        print(f"📝 Updating version to {new_version}...")

        try:
            from fqcn_converter.version import SemanticVersion

            version_obj = SemanticVersion.from_string(new_version)
            self.vm.update_version_file(version_obj)
            print(f"✅ Version updated to {new_version}")
            return True

        except Exception as e:
            print(f"❌ Failed to update version: {e}")
            return False

    def generate_changelog(self, version: str) -> bool:
        """Generate changelog entry for the version."""
        print(f"📚 Generating changelog for {version}...")

        try:
            result = subprocess.run(
                ["python", "scripts/changelog_generator.py", "generate", version],
                cwd=self.repo_path,
                check=True,
            )

            print("✅ Changelog generated")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to generate changelog: {e}")
            return False

    def run_quality_checks(self) -> bool:
        """Run quality checks to ensure release readiness."""
        print("🔍 Running quality checks...")

        try:
            result = subprocess.run(
                ["make", "quality-gate"], cwd=self.repo_path, check=True
            )

            print("✅ Quality checks passed")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Quality checks failed: {e}")
            return False

    def create_git_tag(self, version: str, message: Optional[str] = None) -> bool:
        """Create and push git tag for the release."""
        print(f"🏷️ Creating git tag for {version}...")

        tag_name = f"v{version}" if not version.startswith("v") else version
        tag_message = message or f"Release {tag_name}"

        try:
            # Create tag
            subprocess.run(
                ["git", "tag", "-a", tag_name, "-m", tag_message],
                cwd=self.repo_path,
                check=True,
            )

            print(f"✅ Git tag {tag_name} created")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create git tag: {e}")
            return False

    def commit_release_changes(self, version: str) -> bool:
        """Commit release preparation changes."""
        print(f"💾 Committing release changes for {version}...")

        try:
            # Add changed files
            subprocess.run(
                [
                    "git",
                    "add",
                    "src/fqcn_converter/_version.py",
                    "CHANGELOG.md",
                    "ROADMAP.md",
                ],
                cwd=self.repo_path,
                check=True,
            )

            # Commit changes
            commit_message = f"chore: prepare release {version}"
            subprocess.run(
                ["git", "commit", "-m", commit_message], cwd=self.repo_path, check=True
            )

            print("✅ Release changes committed")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to commit changes: {e}")
            return False

    def push_release(self, version: str) -> bool:
        """Push release commit and tag to remote."""
        print(f"🚀 Pushing release {version} to remote...")

        try:
            # Push commits
            subprocess.run(
                ["git", "push", "origin", "main"], cwd=self.repo_path, check=True
            )

            # Push tags
            tag_name = f"v{version}" if not version.startswith("v") else version
            subprocess.run(
                ["git", "push", "origin", tag_name], cwd=self.repo_path, check=True
            )

            print("✅ Release pushed to remote")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to push release: {e}")
            return False

    def prepare_release(
        self,
        bump_type: Optional[str] = None,
        version: Optional[str] = None,
        dry_run: bool = False,
        skip_checks: bool = False,
        auto_push: bool = False,
    ) -> bool:
        """Complete release preparation workflow."""
        print("🚀 Starting release preparation...")

        # Validate pre-conditions
        if not skip_checks and not self.validate_pre_release_conditions():
            return False

        # Calculate version
        if version:
            next_version = version.lstrip("v")
        else:
            next_version = self.calculate_next_version(bump_type)
            if not next_version:
                return False

        print(f"📋 Preparing release for version: {next_version}")

        if dry_run:
            print("🔍 DRY RUN - No changes will be made")
            print(f"Would prepare release {next_version}")
            return True

        # Update version
        if not self.update_version(next_version):
            return False

        # Generate changelog
        if not self.generate_changelog(next_version):
            return False

        # Run quality checks
        if not skip_checks and not self.run_quality_checks():
            return False

        # Commit changes
        if not self.commit_release_changes(next_version):
            return False

        # Create tag
        if not self.create_git_tag(next_version):
            return False

        # Push if requested
        if auto_push:
            if not self.push_release(next_version):
                return False
        else:
            print(f"🎯 Release {next_version} prepared locally")
            print("Run the following to push:")
            print(f"  git push origin main")
            print(f"  git push origin v{next_version}")

        print(f"🎉 Release {next_version} preparation completed!")
        return True


def cmd_prepare(args: argparse.Namespace) -> int:
    """Prepare a release."""
    preparator = ReleasePreparator()

    success = preparator.prepare_release(
        bump_type=args.bump_type,
        version=args.version,
        dry_run=args.dry_run,
        skip_checks=args.skip_checks,
        auto_push=args.push,
    )

    return 0 if success else 1


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate release readiness."""
    preparator = ReleasePreparator()

    if preparator.validate_pre_release_conditions():
        print("✅ Ready for release")
        return 0
    else:
        print("❌ Not ready for release")
        return 1


def cmd_version(args: argparse.Namespace) -> int:
    """Calculate next version."""
    preparator = ReleasePreparator()

    next_version = preparator.calculate_next_version(args.bump_type)
    if next_version:
        if args.json:
            output = {
                "current_version": str(preparator.vm.get_current_version()),
                "next_version": next_version,
                "bump_type": args.bump_type or "auto",
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"Next version: {next_version}")
        return 0
    else:
        print("Failed to calculate next version")
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Release preparation for FQCN Converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Prepare command
    prepare_parser = subparsers.add_parser("prepare", help="Prepare a release")
    prepare_parser.add_argument(
        "--bump-type",
        choices=[t.value for t in VersionBumpType],
        help="Version bump type (overrides automatic detection)",
    )
    prepare_parser.add_argument(
        "--version", help="Specific version to release (overrides bump type)"
    )
    prepare_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    prepare_parser.add_argument(
        "--skip-checks", action="store_true", help="Skip pre-release validation checks"
    )
    prepare_parser.add_argument(
        "--push", action="store_true", help="Automatically push release to remote"
    )
    prepare_parser.set_defaults(func=cmd_prepare)

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate release readiness"
    )
    validate_parser.set_defaults(func=cmd_validate)

    # Version command
    version_parser = subparsers.add_parser("version", help="Calculate next version")
    version_parser.add_argument(
        "--bump-type",
        choices=[t.value for t in VersionBumpType],
        help="Version bump type",
    )
    version_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format"
    )
    version_parser.set_defaults(func=cmd_version)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
