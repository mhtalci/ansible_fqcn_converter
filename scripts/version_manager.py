#!/usr/bin/env python3
"""
Version management CLI tool for FQCN Converter.

This script provides utilities for managing semantic versions, analyzing
conventional commits, and automating version bumps.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fqcn_converter.version import (
    VersionManager,
    SemanticVersion,
    VersionBumpType,
    ConventionalCommit,
)


def cmd_current_version(args: argparse.Namespace) -> int:
    """Show the current version."""
    vm = VersionManager()
    current = vm.get_current_version()

    if args.json:
        output = {
            "version": str(current),
            "major": current.major,
            "minor": current.minor,
            "patch": current.patch,
            "prerelease": current.prerelease,
            "build": current.build,
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Current version: {current}")

    return 0


def cmd_next_version(args: argparse.Namespace) -> int:
    """Calculate the next version based on commits."""
    vm = VersionManager()

    # Get commits since last tag or all commits
    commits = vm.get_git_commits_since_tag(args.since_tag)

    if not commits and not args.force:
        print("No commits found since last tag. Use --force to calculate anyway.")
        return 1

    next_version = vm.calculate_next_version(commits)
    bump_type = vm.analyze_commits_for_version_bump(commits)

    if args.json:
        output = {
            "current_version": str(vm.get_current_version()),
            "next_version": str(next_version),
            "bump_type": bump_type.value,
            "commits_analyzed": len(commits),
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Current version: {vm.get_current_version()}")
        print(f"Next version: {next_version}")
        print(f"Bump type: {bump_type.value}")
        print(f"Commits analyzed: {len(commits)}")

    return 0


def cmd_bump_version(args: argparse.Namespace) -> int:
    """Bump the version and update files."""
    vm = VersionManager()

    if args.type:
        # Manual bump type
        try:
            bump_type = VersionBumpType(args.type)
        except ValueError:
            print(f"Invalid bump type: {args.type}")
            print(f"Valid types: {[t.value for t in VersionBumpType]}")
            return 1

        new_version = vm.get_current_version().bump(bump_type)
    else:
        # Automatic bump based on commits
        commits = vm.get_git_commits_since_tag(args.since_tag)
        if not commits and not args.force:
            print("No commits found since last tag. Use --force or specify --type.")
            return 1

        new_version = vm.calculate_next_version(commits)

    if not args.dry_run:
        # Update version file
        vm.update_version_file(new_version)
        print(f"Updated version to {new_version}")

        # Create git tag if requested
        if args.tag:
            if vm.create_git_tag(new_version, args.tag_message):
                print(f"Created git tag v{new_version}")
            else:
                print("Failed to create git tag")
                return 1
    else:
        print(f"Would update version to {new_version} (dry run)")

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate version consistency across project files."""
    vm = VersionManager()
    results = vm.validate_version_consistency()

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        if results["consistent"]:
            print("✓ Version consistency validation passed")
        else:
            print("✗ Version consistency validation failed")
            for issue in results["issues"]:
                print(f"  - {issue}")

    return 0 if results["consistent"] else 1


def cmd_history(args: argparse.Namespace) -> int:
    """Show version history from git tags."""
    vm = VersionManager()
    history = vm.get_version_history()

    if args.json:
        output = [{"tag": tag, "date": date} for tag, date in history]
        print(json.dumps(output, indent=2))
    else:
        if history:
            print("Version history:")
            for tag, date in history:
                print(f"  {tag:<12} {date}")
        else:
            print("No version tags found")

    return 0


def cmd_analyze_commits(args: argparse.Namespace) -> int:
    """Analyze commits for conventional commit compliance."""
    vm = VersionManager()
    commits = vm.get_git_commits_since_tag(args.since_tag)

    if not commits:
        print("No commits found")
        return 0

    analysis = {
        "total_commits": len(commits),
        "conventional_commits": 0,
        "breaking_changes": 0,
        "features": 0,
        "fixes": 0,
        "other": 0,
        "non_conventional": [],
    }

    for commit_msg in commits:
        commit = ConventionalCommit.parse(commit_msg)
        if commit:
            analysis["conventional_commits"] += 1
            if commit.breaking_change:
                analysis["breaking_changes"] += 1
            elif commit.type == "feat":
                analysis["features"] += 1
            elif commit.type == "fix":
                analysis["fixes"] += 1
            else:
                analysis["other"] += 1
        else:
            analysis["non_conventional"].append(commit_msg)

    if args.json:
        print(json.dumps(analysis, indent=2))
    else:
        print(f"Commit Analysis (since {args.since_tag or 'beginning'}):")
        print(f"  Total commits: {analysis['total_commits']}")
        print(f"  Conventional commits: {analysis['conventional_commits']}")
        print(f"  Breaking changes: {analysis['breaking_changes']}")
        print(f"  Features: {analysis['features']}")
        print(f"  Fixes: {analysis['fixes']}")
        print(f"  Other: {analysis['other']}")

        if analysis["non_conventional"]:
            print(f"  Non-conventional commits: {len(analysis['non_conventional'])}")
            if args.verbose:
                for commit in analysis["non_conventional"]:
                    print(f"    - {commit}")

    return 0


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Version management for FQCN Converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Current version command
    current_parser = subparsers.add_parser("current", help="Show current version")
    current_parser.set_defaults(func=cmd_current_version)

    # Next version command
    next_parser = subparsers.add_parser(
        "next", help="Calculate next version based on commits"
    )
    next_parser.add_argument(
        "--since-tag", help="Calculate since specific tag (default: last tag)"
    )
    next_parser.add_argument(
        "--force", action="store_true", help="Calculate even if no commits found"
    )
    next_parser.set_defaults(func=cmd_next_version)

    # Bump version command
    bump_parser = subparsers.add_parser("bump", help="Bump version and update files")
    bump_parser.add_argument(
        "--type",
        choices=[t.value for t in VersionBumpType],
        help="Manual bump type (overrides automatic detection)",
    )
    bump_parser.add_argument("--since-tag", help="Analyze commits since specific tag")
    bump_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    bump_parser.add_argument(
        "--tag", action="store_true", help="Create git tag after version bump"
    )
    bump_parser.add_argument("--tag-message", help="Custom message for git tag")
    bump_parser.add_argument(
        "--force", action="store_true", help="Bump even if no commits found"
    )
    bump_parser.set_defaults(func=cmd_bump_version)

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate version consistency"
    )
    validate_parser.set_defaults(func=cmd_validate)

    # History command
    history_parser = subparsers.add_parser("history", help="Show version history")
    history_parser.set_defaults(func=cmd_history)

    # Analyze commits command
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze commits for conventional commit compliance"
    )
    analyze_parser.add_argument(
        "--since-tag", help="Analyze commits since specific tag"
    )
    analyze_parser.add_argument(
        "--verbose", action="store_true", help="Show detailed analysis"
    )
    analyze_parser.set_defaults(func=cmd_analyze_commits)

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
