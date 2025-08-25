#!/usr/bin/env python3
"""
Automatic CHANGELOG.md generator for FQCN Converter.

This script generates changelog entries from conventional commits and
maintains the CHANGELOG.md file with proper formatting and categorization.
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fqcn_converter.version import ConventionalCommit, SemanticVersion, VersionManager


class ChangelogEntry:
    """Represents a single changelog entry."""

    def __init__(self, commit: ConventionalCommit, commit_hash: str = ""):
        self.commit = commit
        self.commit_hash = commit_hash
        self.category = self._determine_category()

    def _determine_category(self) -> str:
        """Determine the changelog category for this commit."""
        if self.commit.breaking_change:
            return "breaking"
        elif self.commit.type == "feat":
            return "added"
        elif self.commit.type == "fix":
            return "fixed"
        elif self.commit.type == "docs":
            return "documentation"
        elif self.commit.type in [
            "perf",
            "refactor",
            "style",
            "test",
            "build",
            "ci",
            "chore",
        ]:
            return "internal"
        else:
            return "changed"

    def format_entry(self, include_hash: bool = False) -> str:
        """Format the entry for the changelog."""
        description = self.commit.description.capitalize()

        # Add scope if present
        if self.commit.scope:
            description = f"**{self.commit.scope}**: {description}"

        # Add commit hash if requested
        if include_hash and self.commit_hash:
            description += f" ({self.commit_hash[:8]})"

        return f"- {description}"


class ChangelogGenerator:
    """Generates and maintains CHANGELOG.md file."""

    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = repo_path or Path.cwd()
        self.changelog_path = self.repo_path / "CHANGELOG.md"
        self.vm = VersionManager(repo_path)

    def get_commits_between_tags(
        self, from_tag: Optional[str] = None, to_tag: str = "HEAD"
    ) -> List[Tuple[str, str]]:
        """Get commits between two tags with their hashes."""
        try:
            if from_tag:
                cmd = [
                    "git",
                    "log",
                    f"{from_tag}..{to_tag}",
                    "--oneline",
                    "--no-merges",
                ]
            else:
                cmd = ["git", "log", f"{to_tag}", "--oneline", "--no-merges"]

            result = subprocess.run(
                cmd, cwd=self.repo_path, capture_output=True, text=True, check=True
            )

            commits = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    parts = line.split(" ", 1)
                    if len(parts) == 2:
                        commit_hash, message = parts
                        commits.append((commit_hash, message))

            return commits

        except subprocess.CalledProcessError:
            return []

    def parse_commits_to_entries(
        self, commits: List[Tuple[str, str]]
    ) -> Dict[str, List[ChangelogEntry]]:
        """Parse commits into categorized changelog entries."""
        categories = {
            "breaking": [],
            "added": [],
            "changed": [],
            "fixed": [],
            "documentation": [],
            "internal": [],
        }

        for commit_hash, commit_msg in commits:
            commit = ConventionalCommit.parse(commit_msg)
            if commit:
                entry = ChangelogEntry(commit, commit_hash)
                categories[entry.category].append(entry)

        # Remove empty categories
        return {k: v for k, v in categories.items() if v}

    def format_changelog_section(
        self,
        version: str,
        date: str,
        categories: Dict[str, List[ChangelogEntry]],
        include_hashes: bool = False,
    ) -> str:
        """Format a complete changelog section for a version."""
        lines = [f"## [{version}] - {date}", ""]

        # Category mapping for display
        category_headers = {
            "breaking": "⚠️ Breaking Changes",
            "added": "🚀 Added",
            "changed": "📝 Changed",
            "fixed": "🐛 Fixed",
            "documentation": "📚 Documentation",
            "internal": "🔧 Internal",
        }

        # Add entries by category
        for category, entries in categories.items():
            if entries:
                header = category_headers.get(category, category.title())
                lines.append(f"### {header}")
                lines.append("")

                for entry in entries:
                    lines.append(entry.format_entry(include_hashes))

                lines.append("")

        return "\n".join(lines)

    def read_existing_changelog(self) -> str:
        """Read the existing CHANGELOG.md content."""
        if self.changelog_path.exists():
            return self.changelog_path.read_text()
        return ""

    def update_changelog(
        self,
        version: str,
        date: Optional[str] = None,
        from_tag: Optional[str] = None,
        include_hashes: bool = False,
    ) -> bool:
        """Update CHANGELOG.md with new version entry."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        # Get commits for this version
        commits = self.get_commits_between_tags(from_tag, "HEAD")
        if not commits:
            print(f"No commits found for version {version}")
            return False

        # Parse commits into categories
        categories = self.parse_commits_to_entries(commits)
        if not categories:
            print(f"No conventional commits found for version {version}")
            return False

        # Generate new section
        new_section = self.format_changelog_section(
            version, date, categories, include_hashes
        )

        # Read existing changelog
        existing_content = self.read_existing_changelog()

        # Find insertion point (after [Unreleased] section)
        lines = existing_content.split("\n")
        insert_index = 0

        # Find the end of the unreleased section
        in_unreleased = False
        for i, line in enumerate(lines):
            if line.startswith("## [Unreleased]"):
                in_unreleased = True
            elif in_unreleased and line.startswith("## ["):
                insert_index = i
                break
            elif in_unreleased and i == len(lines) - 1:
                insert_index = len(lines)
                break

        # Insert new section
        if insert_index > 0:
            lines.insert(insert_index, new_section)
            lines.insert(insert_index + 1, "")
        else:
            # No existing sections, add after unreleased
            unreleased_end = 0
            for i, line in enumerate(lines):
                if line.startswith("## [Unreleased]"):
                    # Find the end of unreleased section
                    for j in range(i + 1, len(lines)):
                        if lines[j].startswith("## ") or j == len(lines) - 1:
                            unreleased_end = j
                            break
                    break

            if unreleased_end > 0:
                lines.insert(unreleased_end, "")
                lines.insert(unreleased_end + 1, new_section)

        # Write updated changelog
        self.changelog_path.write_text("\n".join(lines))
        return True

    def generate_release_notes(
        self, version: str, from_tag: Optional[str] = None
    ) -> str:
        """Generate release notes for a specific version."""
        commits = self.get_commits_between_tags(from_tag, "HEAD")
        if not commits:
            return f"No changes found for version {version}"

        categories = self.parse_commits_to_entries(commits)
        if not categories:
            return f"No conventional commits found for version {version}"

        # Generate release notes format
        lines = [f"# Release Notes - {version}", ""]

        # Add summary
        total_commits = len(commits)
        conventional_commits = sum(len(entries) for entries in categories.values())
        lines.append(
            f"This release includes {conventional_commits} changes from {total_commits} commits."
        )
        lines.append("")

        # Add categories
        category_headers = {
            "breaking": "⚠️ Breaking Changes",
            "added": "🚀 New Features",
            "changed": "📝 Changes",
            "fixed": "🐛 Bug Fixes",
            "documentation": "📚 Documentation",
            "internal": "🔧 Internal Changes",
        }

        for category, entries in categories.items():
            if entries:
                header = category_headers.get(category, category.title())
                lines.append(f"## {header}")
                lines.append("")

                for entry in entries:
                    lines.append(entry.format_entry())

                lines.append("")

        # Add migration notes for breaking changes
        if "breaking" in categories:
            lines.append("## Migration Guide")
            lines.append("")
            lines.append(
                "This release contains breaking changes. Please review the changes above and update your code accordingly."
            )
            lines.append("")
            lines.append(
                "For detailed migration instructions, see the [CHANGELOG.md](CHANGELOG.md) file."
            )
            lines.append("")

        return "\n".join(lines)

    def validate_changelog_format(self) -> Dict[str, any]:
        """Validate the CHANGELOG.md format and structure."""
        results = {"valid": True, "issues": [], "warnings": []}

        if not self.changelog_path.exists():
            results["valid"] = False
            results["issues"].append("CHANGELOG.md file does not exist")
            return results

        content = self.changelog_path.read_text()
        lines = content.split("\n")

        # Check for required sections
        has_title = False
        has_unreleased = False
        version_sections = []

        for line in lines:
            if line.strip() == "# Changelog":
                has_title = True
            elif line.startswith("## [Unreleased]"):
                has_unreleased = True
            elif re.match(r"^## \[(\d+\.\d+\.\d+)\] - \d{4}-\d{2}-\d{2}$", line):
                version_match = re.match(
                    r"^## \[(\d+\.\d+\.\d+)\] - (\d{4}-\d{2}-\d{2})$", line
                )
                if version_match:
                    version_sections.append(
                        (version_match.group(1), version_match.group(2))
                    )

        if not has_title:
            results["issues"].append("Missing main title '# Changelog'")
            results["valid"] = False

        if not has_unreleased:
            results["warnings"].append("Missing [Unreleased] section")

        if not version_sections:
            results["warnings"].append("No version sections found")

        # Validate version order (should be descending)
        if len(version_sections) > 1:
            for i in range(len(version_sections) - 1):
                current_version = SemanticVersion.from_string(version_sections[i][0])
                next_version = SemanticVersion.from_string(version_sections[i + 1][0])

                if current_version < next_version:
                    results["issues"].append(
                        f"Version order incorrect: {current_version} should come after {next_version}"
                    )
                    results["valid"] = False

        return results


def cmd_generate(args: argparse.Namespace) -> int:
    """Generate changelog entry for a version."""
    generator = ChangelogGenerator()

    if generator.update_changelog(
        args.version, args.date, args.from_tag, args.include_hashes
    ):
        print(f"✓ Updated CHANGELOG.md with version {args.version}")
        return 0
    else:
        print(f"✗ Failed to update CHANGELOG.md")
        return 1


def cmd_release_notes(args: argparse.Namespace) -> int:
    """Generate release notes for a version."""
    generator = ChangelogGenerator()

    notes = generator.generate_release_notes(args.version, args.from_tag)

    if args.output:
        Path(args.output).write_text(notes)
        print(f"✓ Release notes written to {args.output}")
    else:
        print(notes)

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate CHANGELOG.md format."""
    generator = ChangelogGenerator()
    results = generator.validate_changelog_format()

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        if results["valid"]:
            print("✓ CHANGELOG.md format is valid")
        else:
            print("✗ CHANGELOG.md format has issues:")
            for issue in results["issues"]:
                print(f"  - {issue}")

        if results["warnings"]:
            print("⚠ Warnings:")
            for warning in results["warnings"]:
                print(f"  - {warning}")

    return 0 if results["valid"] else 1


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CHANGELOG.md generator and manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    generate_parser = subparsers.add_parser(
        "generate", help="Generate changelog entry for a version"
    )
    generate_parser.add_argument("version", help="Version to generate changelog for")
    generate_parser.add_argument("--date", help="Release date (default: today)")
    generate_parser.add_argument("--from-tag", help="Generate from specific tag")
    generate_parser.add_argument(
        "--include-hashes", action="store_true", help="Include commit hashes in entries"
    )
    generate_parser.set_defaults(func=cmd_generate)

    # Release notes command
    notes_parser = subparsers.add_parser(
        "release-notes", help="Generate release notes for a version"
    )
    notes_parser.add_argument("version", help="Version to generate release notes for")
    notes_parser.add_argument("--from-tag", help="Generate from specific tag")
    notes_parser.add_argument("--output", help="Output file for release notes")
    notes_parser.set_defaults(func=cmd_release_notes)

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate CHANGELOG.md format"
    )
    validate_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format"
    )
    validate_parser.set_defaults(func=cmd_validate)

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
