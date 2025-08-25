#!/usr/bin/env python3
"""
Milestone tracking and progress reporting for FQCN Converter roadmap.

This script helps track progress on roadmap milestones, generate progress reports,
and maintain the roadmap documentation with current status.
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import subprocess


@dataclass
class Milestone:
    """Represents a roadmap milestone."""

    name: str
    version: str
    target_date: str
    status: str  # planned, in_progress, completed, delayed
    progress: int  # 0-100
    description: str
    features: List[str]
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class Feature:
    """Represents a feature within a milestone."""

    name: str
    description: str
    status: str  # planned, in_progress, completed, blocked
    assignee: Optional[str] = None
    github_issue: Optional[str] = None
    progress: int = 0
    estimated_effort: Optional[str] = None  # small, medium, large
    actual_effort: Optional[str] = None


class MilestoneTracker:
    """Tracks and manages roadmap milestones."""

    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = repo_path or Path.cwd()
        self.roadmap_path = self.repo_path / "ROADMAP.md"
        self.milestones_data_path = self.repo_path / ".github" / "milestones.json"

        # Ensure data directory exists
        self.milestones_data_path.parent.mkdir(parents=True, exist_ok=True)

    def load_milestones(self) -> Dict[str, Milestone]:
        """Load milestones from JSON data file."""
        if not self.milestones_data_path.exists():
            return self._create_default_milestones()

        try:
            with open(self.milestones_data_path, "r") as f:
                data = json.load(f)

            milestones = {}
            for key, milestone_data in data.items():
                milestones[key] = Milestone(**milestone_data)

            return milestones

        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error loading milestones: {e}")
            return self._create_default_milestones()

    def save_milestones(self, milestones: Dict[str, Milestone]) -> None:
        """Save milestones to JSON data file."""
        data = {}
        for key, milestone in milestones.items():
            data[key] = asdict(milestone)

        with open(self.milestones_data_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _create_default_milestones(self) -> Dict[str, Milestone]:
        """Create default milestone structure."""
        milestones = {
            "v0.1.0": Milestone(
                name="Production Ready Release",
                version="v0.1.0",
                target_date="2025-08-26",
                status="completed",
                progress=100,
                description="Initial production-ready release with core functionality",
                features=[
                    "Core FQCN conversion functionality",
                    "CLI interface with convert, validate, and batch commands",
                    "Python package API",
                    "Comprehensive test suite",
                    "Quality assurance tools",
                    "Documentation system",
                    "CI/CD pipeline",
                ],
            ),
            "v0.2.0": Milestone(
                name="Enhanced User Experience",
                version="v0.2.0",
                target_date="2025-06-30",
                status="planned",
                progress=15,
                description="Improving usability and developer experience",
                features=[
                    "Interactive CLI wizard",
                    "Enhanced reporting and visualization",
                    "Developer tools and integrations",
                    "Web interface (experimental)",
                    "Performance optimizations",
                ],
                dependencies=["v0.1.0"],
            ),
            "v0.3.0": Milestone(
                name="Advanced Conversion Features",
                version="v0.3.0",
                target_date="2025-09-30",
                status="planned",
                progress=0,
                description="Supporting complex conversion scenarios",
                features=[
                    "AI-assisted module detection",
                    "Advanced analysis capabilities",
                    "Collection management integration",
                    "Bidirectional conversion support",
                    "Enterprise integrations",
                ],
                dependencies=["v0.2.0"],
            ),
            "v1.0.0": Milestone(
                name="Stable API and Enterprise Features",
                version="v1.0.0",
                target_date="2025-12-31",
                status="planned",
                progress=0,
                description="Production-grade stability and enterprise readiness",
                features=[
                    "Stable public API",
                    "Enterprise features (RBAC, audit logging)",
                    "Scalability improvements",
                    "Security enhancements",
                    "Comprehensive documentation",
                ],
                dependencies=["v0.3.0"],
            ),
        }

        self.save_milestones(milestones)
        return milestones

    def update_milestone_progress(
        self, version: str, progress: int, status: Optional[str] = None
    ) -> bool:
        """Update progress for a specific milestone."""
        milestones = self.load_milestones()

        if version not in milestones:
            print(f"Milestone {version} not found")
            return False

        milestones[version].progress = max(0, min(100, progress))

        if status:
            milestones[version].status = status

        # Auto-update status based on progress
        if progress == 100 and milestones[version].status != "completed":
            milestones[version].status = "completed"
        elif progress > 0 and milestones[version].status == "planned":
            milestones[version].status = "in_progress"

        self.save_milestones(milestones)
        return True

    def get_milestone_status(self, version: str) -> Optional[Milestone]:
        """Get status of a specific milestone."""
        milestones = self.load_milestones()
        return milestones.get(version)

    def generate_progress_report(self, format_type: str = "text") -> str:
        """Generate a progress report for all milestones."""
        milestones = self.load_milestones()

        if format_type == "json":
            return json.dumps(
                {k: asdict(v) for k, v in milestones.items()}, indent=2, default=str
            )

        # Text format
        lines = ["# Milestone Progress Report", ""]
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Summary table
        lines.append("## Summary")
        lines.append("")
        lines.append("| Milestone | Target Date | Status | Progress |")
        lines.append("|-----------|-------------|--------|----------|")

        for version in sorted(milestones.keys()):
            milestone = milestones[version]
            status_emoji = {
                "completed": "✅",
                "in_progress": "🔄",
                "planned": "📋",
                "delayed": "⚠️",
            }.get(milestone.status, "❓")

            lines.append(
                f"| {milestone.name} ({version}) | {milestone.target_date} | {status_emoji} {milestone.status.title()} | {milestone.progress}% |"
            )

        lines.append("")

        # Detailed sections
        lines.append("## Detailed Status")
        lines.append("")

        for version in sorted(milestones.keys()):
            milestone = milestones[version]
            lines.append(f"### {milestone.name} ({version})")
            lines.append("")
            lines.append(f"**Target Date**: {milestone.target_date}")
            lines.append(f"**Status**: {milestone.status.title()}")
            lines.append(f"**Progress**: {milestone.progress}%")
            lines.append("")
            lines.append(f"**Description**: {milestone.description}")
            lines.append("")

            if milestone.features:
                lines.append("**Features**:")
                for feature in milestone.features:
                    lines.append(f"- {feature}")
                lines.append("")

            if milestone.dependencies:
                lines.append("**Dependencies**: " + ", ".join(milestone.dependencies))
                lines.append("")

        return "\n".join(lines)

    def update_roadmap_file(self) -> bool:
        """Update the ROADMAP.md file with current milestone status."""
        if not self.roadmap_path.exists():
            print("ROADMAP.md file not found")
            return False

        milestones = self.load_milestones()
        content = self.roadmap_path.read_text()

        # Update milestone table
        table_pattern = r"(\| Milestone \| Target Date \| Status \| Progress \|\n\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|\n)(.*?)(\n\n)"

        # Generate new table rows
        new_rows = []
        for version in sorted(milestones.keys()):
            milestone = milestones[version]
            status_emoji = {
                "completed": "✅",
                "in_progress": "🔄",
                "planned": "📋",
                "delayed": "⚠️",
            }.get(milestone.status, "❓")

            new_rows.append(
                f"| {milestone.name} ({version}) | {milestone.target_date} | {status_emoji} {milestone.status.title()} | {milestone.progress}% |"
            )

        new_table_content = "\n".join(new_rows)

        # Replace table content
        def replace_table(match):
            return match.group(1) + new_table_content + match.group(3)

        updated_content = re.sub(table_pattern, replace_table, content, flags=re.DOTALL)

        # Update last updated date
        date_pattern = r"(\*\*Last Updated\*\*: )[^*\n]+"
        current_date = datetime.now().strftime("%B %Y")
        updated_content = re.sub(date_pattern, f"\\1{current_date}", updated_content)

        self.roadmap_path.write_text(updated_content)
        return True

    def get_github_issues_for_milestone(self, version: str) -> List[Dict]:
        """Get GitHub issues associated with a milestone."""
        try:
            # Use GitHub CLI if available
            result = subprocess.run(
                [
                    "gh",
                    "issue",
                    "list",
                    "--milestone",
                    version,
                    "--json",
                    "number,title,state,assignees,labels",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            return json.loads(result.stdout)

        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
            return []

    def sync_with_github(self, version: str) -> bool:
        """Sync milestone progress with GitHub issues."""
        issues = self.get_github_issues_for_milestone(version)
        if not issues:
            return False

        total_issues = len(issues)
        closed_issues = len([i for i in issues if i["state"] == "closed"])

        if total_issues > 0:
            progress = int((closed_issues / total_issues) * 100)
            return self.update_milestone_progress(version, progress)

        return False

    def create_milestone_report(self, version: str) -> str:
        """Create a detailed report for a specific milestone."""
        milestone = self.get_milestone_status(version)
        if not milestone:
            return f"Milestone {version} not found"

        lines = [f"# {milestone.name} ({version}) - Progress Report", ""]
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Target Date**: {milestone.target_date}")
        lines.append(f"**Status**: {milestone.status.title()}")
        lines.append(f"**Progress**: {milestone.progress}%")
        lines.append("")

        # Progress bar
        progress_bar = "█" * (milestone.progress // 5) + "░" * (
            20 - milestone.progress // 5
        )
        lines.append(f"Progress: [{progress_bar}] {milestone.progress}%")
        lines.append("")

        lines.append("## Description")
        lines.append(milestone.description)
        lines.append("")

        if milestone.features:
            lines.append("## Features")
            for feature in milestone.features:
                lines.append(f"- {feature}")
            lines.append("")

        # GitHub issues (if available)
        issues = self.get_github_issues_for_milestone(version)
        if issues:
            lines.append("## GitHub Issues")
            lines.append("")
            for issue in issues:
                status_emoji = "✅" if issue["state"] == "closed" else "🔄"
                assignee = (
                    issue["assignees"][0]["login"]
                    if issue["assignees"]
                    else "Unassigned"
                )
                lines.append(
                    f"- {status_emoji} #{issue['number']}: {issue['title']} (@{assignee})"
                )
            lines.append("")

        if milestone.dependencies:
            lines.append("## Dependencies")
            for dep in milestone.dependencies:
                dep_milestone = self.get_milestone_status(dep)
                if dep_milestone:
                    status_emoji = "✅" if dep_milestone.status == "completed" else "🔄"
                    lines.append(f"- {status_emoji} {dep} ({dep_milestone.status})")
                else:
                    lines.append(f"- ❓ {dep} (unknown)")
            lines.append("")

        return "\n".join(lines)


def cmd_list_milestones(args: argparse.Namespace) -> int:
    """List all milestones."""
    tracker = MilestoneTracker()
    milestones = tracker.load_milestones()

    if args.json:
        print(
            json.dumps(
                {k: asdict(v) for k, v in milestones.items()}, indent=2, default=str
            )
        )
    else:
        print("Roadmap Milestones:")
        print("=" * 50)
        for version in sorted(milestones.keys()):
            milestone = milestones[version]
            status_emoji = {
                "completed": "✅",
                "in_progress": "🔄",
                "planned": "📋",
                "delayed": "⚠️",
            }.get(milestone.status, "❓")

            print(f"{status_emoji} {milestone.name} ({version})")
            print(f"   Target: {milestone.target_date}")
            print(f"   Status: {milestone.status.title()}")
            print(f"   Progress: {milestone.progress}%")
            print()

    return 0


def cmd_update_progress(args: argparse.Namespace) -> int:
    """Update milestone progress."""
    tracker = MilestoneTracker()

    if tracker.update_milestone_progress(args.version, args.progress, args.status):
        print(f"✓ Updated {args.version} progress to {args.progress}%")

        if args.update_roadmap:
            if tracker.update_roadmap_file():
                print("✓ Updated ROADMAP.md file")
            else:
                print("✗ Failed to update ROADMAP.md file")

        return 0
    else:
        print(f"✗ Failed to update {args.version}")
        return 1


def cmd_generate_report(args: argparse.Namespace) -> int:
    """Generate progress report."""
    tracker = MilestoneTracker()

    if args.milestone:
        report = tracker.create_milestone_report(args.milestone)
    else:
        report = tracker.generate_progress_report(args.format)

    if args.output:
        Path(args.output).write_text(report)
        print(f"✓ Report written to {args.output}")
    else:
        print(report)

    return 0


def cmd_sync_github(args: argparse.Namespace) -> int:
    """Sync with GitHub milestones."""
    tracker = MilestoneTracker()

    if tracker.sync_with_github(args.version):
        print(f"✓ Synced {args.version} with GitHub issues")
        return 0
    else:
        print(f"✗ Failed to sync {args.version} with GitHub")
        return 1


def cmd_update_roadmap(args: argparse.Namespace) -> int:
    """Update ROADMAP.md file."""
    tracker = MilestoneTracker()

    if tracker.update_roadmap_file():
        print("✓ Updated ROADMAP.md file")
        return 0
    else:
        print("✗ Failed to update ROADMAP.md file")
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Milestone tracking for FQCN Converter roadmap",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List milestones command
    list_parser = subparsers.add_parser("list", help="List all milestones")
    list_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format"
    )
    list_parser.set_defaults(func=cmd_list_milestones)

    # Update progress command
    update_parser = subparsers.add_parser("update", help="Update milestone progress")
    update_parser.add_argument("version", help="Milestone version (e.g., v0.2.0)")
    update_parser.add_argument("progress", type=int, help="Progress percentage (0-100)")
    update_parser.add_argument(
        "--status", help="Update status (planned, in_progress, completed, delayed)"
    )
    update_parser.add_argument(
        "--update-roadmap", action="store_true", help="Also update ROADMAP.md"
    )
    update_parser.set_defaults(func=cmd_update_progress)

    # Generate report command
    report_parser = subparsers.add_parser("report", help="Generate progress report")
    report_parser.add_argument(
        "--milestone", help="Generate report for specific milestone"
    )
    report_parser.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format"
    )
    report_parser.add_argument("--output", help="Output file path")
    report_parser.set_defaults(func=cmd_generate_report)

    # Sync with GitHub command
    sync_parser = subparsers.add_parser("sync", help="Sync with GitHub milestones")
    sync_parser.add_argument("version", help="Milestone version to sync")
    sync_parser.set_defaults(func=cmd_sync_github)

    # Update roadmap command
    roadmap_parser = subparsers.add_parser("roadmap", help="Update ROADMAP.md file")
    roadmap_parser.set_defaults(func=cmd_update_roadmap)

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
