#!/usr/bin/env python3
"""
Tool Installation Checker

This script checks if all required quality assurance tools are properly
installed and configured.
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class ToolChecker:
    """Check if quality assurance tools are properly installed."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results: Dict[str, Tuple[bool, str]] = {}

    def run_command(self, command: List[str]) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"
        except FileNotFoundError:
            return 1, "", "Command not found"

    def check_python(self) -> Tuple[bool, str]:
        """Check Python installation and version."""
        exit_code, stdout, stderr = self.run_command(["python", "--version"])
        if exit_code != 0:
            exit_code, stdout, stderr = self.run_command(["python3", "--version"])

        if exit_code == 0:
            version = stdout.strip()
            # Check if version is 3.8+
            try:
                version_parts = version.split()[1].split(".")
                major, minor = int(version_parts[0]), int(version_parts[1])
                if major >= 3 and minor >= 8:
                    return True, f"✅ {version}"
                else:
                    return False, f"❌ {version} (requires Python 3.8+)"
            except (IndexError, ValueError):
                return False, f"❌ Could not parse version: {version}"
        else:
            return False, "❌ Python not found"

    def check_pip(self) -> Tuple[bool, str]:
        """Check pip installation."""
        exit_code, stdout, stderr = self.run_command(["pip", "--version"])
        if exit_code != 0:
            exit_code, stdout, stderr = self.run_command(["pip3", "--version"])

        if exit_code == 0:
            version = stdout.strip().split()[1]
            return True, f"✅ pip {version}"
        else:
            return False, "❌ pip not found"

    def check_tool(
        self, tool_name: str, command: List[str], version_flag: str = "--version"
    ) -> Tuple[bool, str]:
        """Check if a tool is installed and get its version."""
        cmd = command + [version_flag]
        exit_code, stdout, stderr = self.run_command(cmd)

        if exit_code == 0:
            # Extract version from output
            lines = stdout.strip().split("\n")
            version_line = lines[0] if lines else "unknown version"
            return True, f"✅ {version_line}"
        else:
            return False, f"❌ {tool_name} not found"

    def check_config_files(self) -> Tuple[bool, str]:
        """Check if configuration files exist."""
        config_files = [
            "setup.cfg",
            "pyproject.toml",
            ".flake8",
            "mypy.ini",
            ".pre-commit-config.yaml",
            "tox.ini",
        ]

        missing_files = []
        for config_file in config_files:
            if not (self.project_root / config_file).exists():
                missing_files.append(config_file)

        if missing_files:
            return False, f"❌ Missing config files: {', '.join(missing_files)}"
        else:
            return True, f"✅ All config files present ({len(config_files)} files)"

    def check_github_workflows(self) -> Tuple[bool, str]:
        """Check if GitHub workflows exist."""
        workflow_dir = self.project_root / ".github" / "workflows"
        if not workflow_dir.exists():
            return False, "❌ .github/workflows directory not found"

        expected_workflows = [
            "ci.yml",
        ]

        missing_workflows = []
        for workflow in expected_workflows:
            if not (workflow_dir / workflow).exists():
                missing_workflows.append(workflow)

        if missing_workflows:
            return False, f"❌ Missing workflows: {', '.join(missing_workflows)}"
        else:
            return (
                True,
                f"✅ All workflows present ({len(expected_workflows)} workflows)",
            )

    def run_all_checks(self) -> bool:
        """Run all tool checks."""
        print("🔍 Checking quality assurance tools installation...\n")

        # Core tools
        self.results["Python"] = self.check_python()
        self.results["pip"] = self.check_pip()

        # Quality tools
        tools_to_check = [
            ("Black", ["black"]),
            ("isort", ["isort"]),
            ("Flake8", ["flake8"]),
            ("MyPy", ["mypy"]),
            ("Bandit", ["bandit"]),
            ("Safety", ["safety"]),
            ("pytest", ["pytest"]),
            ("pre-commit", ["pre-commit"]),
            ("tox", ["tox"]),
        ]

        for tool_name, command in tools_to_check:
            self.results[tool_name] = self.check_tool(tool_name, command)

        # Configuration checks
        self.results["Config Files"] = self.check_config_files()
        self.results["GitHub Workflows"] = self.check_github_workflows()

        # Print results
        all_good = True
        for tool, (success, message) in self.results.items():
            print(f"{tool:<20} {message}")
            if not success:
                all_good = False

        return all_good

    def print_installation_guide(self) -> None:
        """Print installation guide for missing tools."""
        print("\n" + "=" * 60)
        print("INSTALLATION GUIDE")
        print("=" * 60)

        failed_tools = [
            tool for tool, (success, _) in self.results.items() if not success
        ]

        if not failed_tools:
            print("✅ All tools are properly installed!")
            return

        print("To install missing tools, run:")
        print()

        if "pip" in failed_tools:
            print("# Install pip first:")
            print("curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py")
            print("python get-pip.py")
            print()

        print("# Install development dependencies:")
        print('pip install -e ".[dev]"')
        print()

        print("# Or install tools individually:")
        tool_commands = {
            "Black": "pip install black",
            "isort": "pip install isort",
            "Flake8": "pip install flake8",
            "MyPy": "pip install mypy",
            "Bandit": "pip install bandit[toml]",
            "Safety": "pip install safety",
            "pytest": "pip install pytest",
            "pre-commit": "pip install pre-commit",
            "tox": "pip install tox",
        }

        for tool in failed_tools:
            if tool in tool_commands:
                print(f"pip install {tool.lower()}")

        print()
        print("# Set up pre-commit hooks:")
        print("pre-commit install")
        print()
        print("# Run setup script:")
        print("./scripts/setup-dev.sh  # Linux/macOS")
        print("scripts\\setup-dev.bat   # Windows")


def main():
    """Main entry point."""
    checker = ToolChecker()

    try:
        all_good = checker.run_all_checks()

        if all_good:
            print("\n🎉 All quality assurance tools are properly installed!")
            print("\nYou can now run:")
            print("  make dev-check     - Run all development checks")
            print("  make quality-gate  - Run complete quality gate")
            print("  make help          - Show all available commands")
        else:
            checker.print_installation_guide()
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n❌ Tool check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Tool check failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
