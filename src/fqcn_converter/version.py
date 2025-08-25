"""
Semantic versioning and version management utilities.

This module provides utilities for managing semantic versions, validating
version consistency, and integrating with conventional commits for automatic
version bumping.
"""

import re
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from ._version import __version__


class VersionBumpType(Enum):
    """Types of version bumps based on conventional commits."""

    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    PRERELEASE = "prerelease"


class ConventionalCommitType(Enum):
    """Conventional commit types and their version impact."""

    FEAT = ("feat", VersionBumpType.MINOR)
    FIX = ("fix", VersionBumpType.PATCH)
    DOCS = ("docs", VersionBumpType.PATCH)
    STYLE = ("style", VersionBumpType.PATCH)
    REFACTOR = ("refactor", VersionBumpType.PATCH)
    PERF = ("perf", VersionBumpType.PATCH)
    TEST = ("test", VersionBumpType.PATCH)
    CHORE = ("chore", VersionBumpType.PATCH)
    CI = ("ci", VersionBumpType.PATCH)
    BUILD = ("build", VersionBumpType.PATCH)

    def __init__(self, commit_type: str, bump_type: VersionBumpType):
        self.commit_type = commit_type
        self.bump_type = bump_type


@dataclass
class SemanticVersion:
    """Represents a semantic version with major.minor.patch format."""

    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None

    @classmethod
    def from_string(cls, version_str: str) -> "SemanticVersion":
        """Parse a semantic version from string format."""
        # Remove 'v' prefix if present
        version_str = version_str.lstrip("v")

        # Regex pattern for semantic version
        pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
        match = re.match(pattern, version_str)

        if not match:
            raise ValueError(f"Invalid semantic version format: {version_str}")

        major, minor, patch, prerelease, build = match.groups()

        return cls(
            major=int(major),
            minor=int(minor),
            patch=int(patch),
            prerelease=prerelease,
            build=build,
        )

    def __str__(self) -> str:
        """Return string representation of the version."""
        version = f"{self.major}.{self.minor}.{self.patch}"

        if self.prerelease:
            version += f"-{self.prerelease}"

        if self.build:
            version += f"+{self.build}"

        return version

    def __lt__(self, other: "SemanticVersion") -> bool:
        """Compare versions for sorting."""
        if not isinstance(other, SemanticVersion):
            return NotImplemented

        # Compare major.minor.patch
        self_tuple = (self.major, self.minor, self.patch)
        other_tuple = (other.major, other.minor, other.patch)

        if self_tuple != other_tuple:
            return self_tuple < other_tuple

        # Handle prerelease comparison
        if self.prerelease is None and other.prerelease is None:
            return False
        if self.prerelease is None:
            return False  # Release version > prerelease
        if other.prerelease is None:
            return True  # Prerelease < release version

        return self.prerelease < other.prerelease

    def bump(self, bump_type: VersionBumpType) -> "SemanticVersion":
        """Create a new version with the specified bump type."""
        if bump_type == VersionBumpType.MAJOR:
            return SemanticVersion(self.major + 1, 0, 0)
        elif bump_type == VersionBumpType.MINOR:
            return SemanticVersion(self.major, self.minor + 1, 0)
        elif bump_type == VersionBumpType.PATCH:
            return SemanticVersion(self.major, self.minor, self.patch + 1)
        elif bump_type == VersionBumpType.PRERELEASE:
            if self.prerelease:
                # Increment existing prerelease
                parts = self.prerelease.split(".")
                if parts[-1].isdigit():
                    parts[-1] = str(int(parts[-1]) + 1)
                else:
                    parts.append("1")
                prerelease = ".".join(parts)
            else:
                prerelease = "alpha.1"

            return SemanticVersion(self.major, self.minor, self.patch, prerelease)
        else:
            raise ValueError(f"Unknown bump type: {bump_type}")


@dataclass
class ConventionalCommit:
    """Represents a parsed conventional commit."""

    type: str
    scope: Optional[str]
    description: str
    body: Optional[str]
    footer: Optional[str]
    breaking_change: bool

    @classmethod
    def parse(cls, commit_message: str) -> Optional["ConventionalCommit"]:
        """Parse a conventional commit message."""
        lines = commit_message.strip().split("\n")
        if not lines:
            return None

        header = lines[0]
        body = "\n".join(lines[1:]).strip() if len(lines) > 1 else None

        # Parse header: type(scope): description
        header_pattern = r"^(\w+)(?:\(([^)]+)\))?\s*:\s*(.+)$"
        match = re.match(header_pattern, header)

        if not match:
            return None

        commit_type, scope, description = match.groups()

        # Check for breaking changes
        breaking_change = (
            "!" in header
            or (body and "BREAKING CHANGE:" in body)
            or (body and "BREAKING-CHANGE:" in body)
        )

        # Extract footer (lines starting with token:)
        footer = None
        if body:
            footer_lines = []
            for line in body.split("\n"):
                if re.match(r"^\w+(-\w+)*\s*:", line):
                    footer_lines.append(line)
            footer = "\n".join(footer_lines) if footer_lines else None

        return cls(
            type=commit_type.lower(),
            scope=scope,
            description=description,
            body=body,
            footer=footer,
            breaking_change=breaking_change,
        )


class VersionManager:
    """Manages semantic versioning and conventional commits."""

    def __init__(self, repo_path: Optional[Path] = None):
        """Initialize version manager."""
        self.repo_path = repo_path or Path.cwd()
        self.current_version = SemanticVersion.from_string(__version__)

    def get_current_version(self) -> SemanticVersion:
        """Get the current version from _version.py."""
        return self.current_version

    def get_git_commits_since_tag(self, tag: Optional[str] = None) -> List[str]:
        """Get git commits since the specified tag or all commits if no tag."""
        try:
            if tag:
                cmd = ["git", "log", f"{tag}..HEAD", "--oneline", "--no-merges"]
            else:
                cmd = ["git", "log", "--oneline", "--no-merges"]

            result = subprocess.run(
                cmd, cwd=self.repo_path, capture_output=True, text=True, check=True
            )

            commits = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    # Extract commit message (everything after the hash)
                    parts = line.split(" ", 1)
                    if len(parts) > 1:
                        commits.append(parts[1])

            return commits

        except subprocess.CalledProcessError:
            return []

    def analyze_commits_for_version_bump(self, commits: List[str]) -> VersionBumpType:
        """Analyze commits to determine the appropriate version bump."""
        has_breaking = False
        has_feature = False
        has_fix = False

        for commit_msg in commits:
            commit = ConventionalCommit.parse(commit_msg)
            if not commit:
                continue

            if commit.breaking_change:
                has_breaking = True
            elif commit.type == "feat":
                has_feature = True
            elif commit.type == "fix":
                has_fix = True

        # Determine bump type based on conventional commit rules
        if has_breaking:
            return VersionBumpType.MAJOR
        elif has_feature:
            return VersionBumpType.MINOR
        elif has_fix:
            return VersionBumpType.PATCH
        else:
            return VersionBumpType.PATCH  # Default for other changes

    def calculate_next_version(
        self, commits: Optional[List[str]] = None
    ) -> SemanticVersion:
        """Calculate the next version based on conventional commits."""
        if commits is None:
            # Get commits since last tag
            commits = self.get_git_commits_since_tag()

        if not commits:
            # No commits, return current version
            return self.current_version

        bump_type = self.analyze_commits_for_version_bump(commits)
        return self.current_version.bump(bump_type)

    def validate_version_consistency(self) -> Dict[str, Union[bool, str]]:
        """Validate version consistency across project files."""
        results = {"consistent": True, "issues": []}

        # Check pyproject.toml dynamic version
        pyproject_path = self.repo_path / "pyproject.toml"
        if pyproject_path.exists():
            content = pyproject_path.read_text()
            if 'dynamic = ["version"]' not in content:
                results["consistent"] = False
                results["issues"].append("pyproject.toml should use dynamic versioning")

        # Check _version.py exists and has correct format
        version_file = self.repo_path / "src" / "fqcn_converter" / "_version.py"
        if not version_file.exists():
            results["consistent"] = False
            results["issues"].append("_version.py file is missing")
        else:
            try:
                content = version_file.read_text()
                if f'__version__ = "{self.current_version}"' not in content:
                    results["consistent"] = False
                    results["issues"].append(
                        f"_version.py version does not match expected {self.current_version}"
                    )
            except Exception as e:
                results["consistent"] = False
                results["issues"].append(f"Error reading _version.py: {e}")

        return results

    def update_version_file(self, new_version: SemanticVersion) -> None:
        """Update the _version.py file with the new version."""
        version_file = self.repo_path / "src" / "fqcn_converter" / "_version.py"

        # Read current content
        if version_file.exists():
            content = version_file.read_text()
        else:
            content = '"""Version information for FQCN Converter."""\n\n'

        # Update version strings
        version_str = str(new_version)
        version_tuple = (
            f"({new_version.major}, {new_version.minor}, {new_version.patch})"
        )

        # Replace or add version information
        lines = content.split("\n")
        new_lines = []
        version_updated = False
        version_info_updated = False

        for line in lines:
            if line.startswith("__version__ = "):
                new_lines.append(f'__version__ = "{version_str}"')
                version_updated = True
            elif line.startswith("__version_info__ = "):
                new_lines.append(f"__version_info__ = {version_tuple}")
                version_info_updated = True
            else:
                new_lines.append(line)

        # Add version info if not found
        if not version_updated:
            new_lines.insert(-1, f'__version__ = "{version_str}"')
        if not version_info_updated:
            new_lines.insert(-1, f"__version_info__ = {version_tuple}")

        # Write updated content
        version_file.write_text("\n".join(new_lines))

    def create_git_tag(
        self, version: SemanticVersion, message: Optional[str] = None
    ) -> bool:
        """Create a git tag for the version."""
        try:
            tag_name = f"v{version}"
            tag_message = message or f"Release {tag_name}"

            subprocess.run(
                ["git", "tag", "-a", tag_name, "-m", tag_message],
                cwd=self.repo_path,
                check=True,
            )

            return True

        except subprocess.CalledProcessError:
            return False

    def get_version_history(self) -> List[Tuple[str, str]]:
        """Get version history from git tags."""
        try:
            result = subprocess.run(
                ["git", "tag", "-l", "--sort=-version:refname"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            tags = []
            for line in result.stdout.strip().split("\n"):
                if line.strip() and line.startswith("v"):
                    # Get tag date
                    date_result = subprocess.run(
                        ["git", "log", "-1", "--format=%ai", line.strip()],
                        cwd=self.repo_path,
                        capture_output=True,
                        text=True,
                        check=True,
                    )

                    date = (
                        date_result.stdout.strip().split()[0]
                        if date_result.stdout.strip()
                        else "unknown"
                    )
                    tags.append((line.strip(), date))

            return tags

        except subprocess.CalledProcessError:
            return []


def get_version_manager() -> VersionManager:
    """Get a configured version manager instance."""
    return VersionManager()
