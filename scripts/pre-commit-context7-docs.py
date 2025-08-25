#!/usr/bin/env python3
"""
Pre-commit hook for Context7 documentation generation.

This script runs as a pre-commit hook to automatically regenerate
API documentation when Python source files are modified.
"""

import subprocess
import sys
from pathlib import Path


def has_python_changes():
    """Check if any Python files in src/ have been modified."""
    try:
        # Get list of staged files
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )

        staged_files = result.stdout.strip().split("\n")

        # Check if any Python files in src/ are staged
        for file_path in staged_files:
            if file_path.startswith("src/") and file_path.endswith(".py"):
                return True

        return False

    except subprocess.CalledProcessError:
        # If git command fails, assume changes exist to be safe
        return True


def regenerate_docs():
    """Regenerate Context7 API and CLI documentation."""
    api_script_path = Path(__file__).parent / "generate_context7_docs.py"
    cli_script_path = Path(__file__).parent / "generate_context7_cli_docs.py"

    try:
        print("🔄 Regenerating Context7 API documentation...")

        result = subprocess.run(
            [sys.executable, str(api_script_path)],
            capture_output=True,
            text=True,
            check=True,
        )

        print("✅ Context7 API documentation regenerated successfully")

        print("🔄 Regenerating Context7 CLI documentation...")

        result = subprocess.run(
            [sys.executable, str(cli_script_path)],
            capture_output=True,
            text=True,
            check=True,
        )

        print("✅ Context7 CLI documentation regenerated successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to regenerate documentation: {e}")
        print(f"   stdout: {e.stdout}")
        print(f"   stderr: {e.stderr}")
        return False


def stage_doc_changes():
    """Stage any changes to documentation files."""
    try:
        # Add generated documentation files to staging
        doc_files = [
            "docs/reference/api/api_reference.md",
            "docs/reference/api/api_reference.json",
            "docs/usage/cli_reference.md",
            "docs/usage/cli_reference.json",
            "docs/usage/cli_examples.sh",
        ]

        for doc_file in doc_files:
            if Path(doc_file).exists():
                subprocess.run(["git", "add", doc_file], check=True)

        print("📝 Staged documentation changes")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to stage documentation changes: {e}")
        return False


def main():
    """Main pre-commit hook logic."""
    # Check if we're in a git repository
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"], capture_output=True, check=True
        )
    except subprocess.CalledProcessError:
        print("⚠️  Not in a git repository, skipping documentation generation")
        return 0

    # Check if Python files have changed
    if not has_python_changes():
        print("ℹ️  No Python source changes detected, skipping documentation generation")
        return 0

    print("🔍 Python source changes detected, regenerating documentation...")

    # Regenerate documentation
    if not regenerate_docs():
        print("❌ Documentation generation failed")
        return 1

    # Stage documentation changes
    if not stage_doc_changes():
        print("❌ Failed to stage documentation changes")
        return 1

    print("✅ Context7 documentation updated and staged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
