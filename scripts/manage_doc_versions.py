#!/usr/bin/env python3
"""
Documentation Version Management Script

This script manages documentation versions for GitHub Pages deployment,
including version switching and archiving.
"""

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class DocumentationVersionManager:
    """Manages documentation versions and deployment."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.docs_dir = self.project_root / "docs"
        self.config_file = self.docs_dir / "config.json"
        self.versions_dir = self.docs_dir / "versions"

        # Load configuration
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load documentation configuration."""
        if self.config_file.exists():
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            return self._create_default_config()

    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration."""
        config = {
            "site": {
                "name": "Ansible FQCN Converter Documentation",
                "version": "0.1.0",
            },
            "versions": [],
            "deployment": {"provider": "github-pages"},
        }

        self._save_config(config)
        return config

    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

    def create_version(self, version: str, title: Optional[str] = None) -> None:
        """Create a new documentation version."""
        print(f"🔄 Creating documentation version {version}...")

        # Create version directory
        version_dir = self.versions_dir / version
        version_dir.mkdir(parents=True, exist_ok=True)

        # Copy current documentation to version directory
        self._copy_current_docs(version_dir)

        # Update configuration
        version_info = {
            "version": version,
            "title": title or f"Version {version}",
            "path": f"/versions/{version}",
            "created": datetime.now().isoformat(),
            "status": "stable",
        }

        # Add to versions list
        self.config["versions"].append(version_info)

        # Update current version
        self.config["site"]["version"] = version

        self._save_config(self.config)

        print(f"✅ Created documentation version {version}")

    def _copy_current_docs(self, version_dir: Path) -> None:
        """Copy current documentation to version directory."""
        # Copy API reference
        api_src = self.docs_dir / "reference" / "api"
        if api_src.exists():
            api_dst = version_dir / "api"
            shutil.copytree(api_src, api_dst, dirs_exist_ok=True)

        # Copy CLI reference
        cli_src = self.docs_dir / "usage"
        if cli_src.exists():
            cli_dst = version_dir / "cli"
            shutil.copytree(cli_src, cli_dst, dirs_exist_ok=True)

        # Copy other documentation files
        for doc_file in self.docs_dir.glob("*.md"):
            shutil.copy2(doc_file, version_dir)

    def list_versions(self) -> None:
        """List all available documentation versions."""
        print("📚 Available documentation versions:")
        print()

        if not self.config.get("versions"):
            print("  No versions found.")
            return

        for version_info in self.config["versions"]:
            status_icon = "🟢" if version_info.get("status") == "stable" else "🟡"
            default_marker = " (default)" if version_info.get("default") else ""

            print(f"  {status_icon} {version_info['version']}{default_marker}")
            print(f"     Title: {version_info.get('title', 'N/A')}")
            print(f"     Path: {version_info.get('path', 'N/A')}")
            print(f"     Created: {version_info.get('created', 'N/A')}")
            print()

    def set_default_version(self, version: str) -> None:
        """Set the default documentation version."""
        print(f"🔄 Setting default version to {version}...")

        # Find version in config
        version_found = False
        for version_info in self.config["versions"]:
            if version_info["version"] == version:
                version_info["default"] = True
                version_found = True
            else:
                version_info.pop("default", None)

        if not version_found:
            print(f"❌ Version {version} not found")
            return

        self._save_config(self.config)
        print(f"✅ Set {version} as default version")

    def archive_version(self, version: str) -> None:
        """Archive a documentation version."""
        print(f"🔄 Archiving version {version}...")

        # Find and update version status
        for version_info in self.config["versions"]:
            if version_info["version"] == version:
                version_info["status"] = "archived"
                break
        else:
            print(f"❌ Version {version} not found")
            return

        self._save_config(self.config)
        print(f"✅ Archived version {version}")

    def generate_version_switcher(self) -> str:
        """Generate HTML for version switcher."""
        if not self.config.get("versions"):
            return ""

        html = """
        <div class="version-switcher">
            <select onchange="switchVersion(this.value)" class="form-select">
        """

        for version_info in self.config["versions"]:
            selected = "selected" if version_info.get("default") else ""
            status = version_info.get("status", "stable")
            title = version_info.get("title", version_info["version"])

            html += f"""
                <option value="{version_info['path']}" {selected}>
                    {title} ({status})
                </option>
            """

        html += """
            </select>
        </div>
        <script>
            function switchVersion(path) {
                if (path !== window.location.pathname) {
                    window.location.href = path;
                }
            }
        </script>
        """

        return html

    def cleanup_old_versions(self, keep_count: int = 5) -> None:
        """Clean up old documentation versions."""
        print(f"🔄 Cleaning up old versions (keeping {keep_count} most recent)...")

        versions = self.config.get("versions", [])
        if len(versions) <= keep_count:
            print("  No cleanup needed.")
            return

        # Sort by creation date (newest first)
        versions.sort(key=lambda v: v.get("created", ""), reverse=True)

        # Keep the most recent versions and default version
        versions_to_keep = set()

        # Always keep default version
        for version_info in versions:
            if version_info.get("default"):
                versions_to_keep.add(version_info["version"])

        # Keep most recent versions
        for version_info in versions[:keep_count]:
            versions_to_keep.add(version_info["version"])

        # Remove old versions
        versions_to_remove = []
        for version_info in versions:
            if version_info["version"] not in versions_to_keep:
                versions_to_remove.append(version_info)

        for version_info in versions_to_remove:
            version = version_info["version"]
            print(f"  Removing version {version}...")

            # Remove from filesystem
            version_dir = self.versions_dir / version
            if version_dir.exists():
                shutil.rmtree(version_dir)

            # Remove from config
            self.config["versions"] = [
                v for v in self.config["versions"] if v["version"] != version
            ]

        self._save_config(self.config)
        print(f"✅ Cleaned up {len(versions_to_remove)} old versions")


def main():
    """Main CLI interface for documentation version management."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Manage documentation versions for GitHub Pages deployment"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create version command
    create_parser = subparsers.add_parser(
        "create", help="Create a new documentation version"
    )
    create_parser.add_argument("version", help="Version number (e.g., 0.1.0)")
    create_parser.add_argument("--title", help="Version title")

    # List versions command
    subparsers.add_parser("list", help="List all documentation versions")

    # Set default command
    default_parser = subparsers.add_parser("set-default", help="Set default version")
    default_parser.add_argument("version", help="Version to set as default")

    # Archive command
    archive_parser = subparsers.add_parser("archive", help="Archive a version")
    archive_parser.add_argument("version", help="Version to archive")

    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old versions")
    cleanup_parser.add_argument(
        "--keep", type=int, default=5, help="Number of versions to keep"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize version manager
    project_root = Path(__file__).parent.parent
    manager = DocumentationVersionManager(project_root)

    try:
        if args.command == "create":
            manager.create_version(args.version, args.title)
        elif args.command == "list":
            manager.list_versions()
        elif args.command == "set-default":
            manager.set_default_version(args.version)
        elif args.command == "archive":
            manager.archive_version(args.version)
        elif args.command == "cleanup":
            manager.cleanup_old_versions(args.keep)

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
