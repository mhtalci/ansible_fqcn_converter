#!/usr/bin/env python3
"""
Context7 CLI Documentation Generator

This script generates comprehensive CLI documentation using Context7 MCP
to extract command help text, options, and usage examples from the
FQCN Converter CLI interface.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import re

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from fqcn_converter.cli.main import create_parser
    from fqcn_converter.cli import convert, validate, batch
except ImportError as e:
    print(f"Error importing fqcn_converter CLI: {e}")
    print("Make sure the package is installed or run from the project root")
    sys.exit(1)


class Context7CLIDocGenerator:
    """Generates Context7-compatible CLI documentation from command help."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_cli_docs(self) -> None:
        """Generate complete CLI documentation."""
        print("🔄 Generating Context7 CLI documentation...")

        # Generate documentation structure
        cli_docs = {
            "title": "FQCN Converter CLI Reference",
            "description": "Complete command-line interface reference for the Ansible FQCN Converter",
            "version": "0.1.0",
            "main_command": {},
            "subcommands": {},
            "usage_examples": [],
            "common_options": {},
            "troubleshooting": [],
        }

        # Document main command
        print("  📝 Documenting main command...")
        cli_docs["main_command"] = self._document_main_command()

        # Document subcommands
        subcommands = ["convert", "validate", "batch"]
        for subcommand in subcommands:
            print(f"  📝 Documenting {subcommand} subcommand...")
            cli_docs["subcommands"][subcommand] = self._document_subcommand(subcommand)

        # Generate usage examples
        cli_docs["usage_examples"] = self._generate_cli_examples()

        # Extract common options
        cli_docs["common_options"] = self._extract_common_options()

        # Add troubleshooting guide
        cli_docs["troubleshooting"] = self._generate_troubleshooting_guide()

        # Write CLI documentation
        cli_file = self.output_dir / "cli_reference.json"
        with open(cli_file, "w", encoding="utf-8") as f:
            json.dump(cli_docs, f, indent=2, default=str)

        # Generate markdown documentation
        self._generate_cli_markdown(cli_docs)

        # Generate interactive examples
        self._generate_interactive_examples(cli_docs)

        print(f"✅ CLI documentation generated in {self.output_dir}")

    def _document_main_command(self) -> Dict[str, Any]:
        """Document the main fqcn-converter command."""
        parser = create_parser()

        # Get help text
        help_text = self._get_parser_help(parser)

        return {
            "name": "fqcn-converter",
            "description": "Convert Ansible playbooks and roles to use Fully Qualified Collection Names (FQCN)",
            "help_text": help_text,
            "global_options": self._extract_global_options(parser),
            "subcommands_list": ["convert", "validate", "batch"],
            "usage": "fqcn-converter [global-options] <command> [command-options] [arguments]",
            "examples": [
                {
                    "description": "Show help for main command",
                    "command": "fqcn-converter --help",
                },
                {
                    "description": "Show version information",
                    "command": "fqcn-converter --version",
                },
                {
                    "description": "Convert with verbose output",
                    "command": "fqcn-converter --verbose convert playbook.yml",
                },
            ],
        }

    def _document_subcommand(self, subcommand: str) -> Dict[str, Any]:
        """Document a specific subcommand."""
        # Create a temporary parser to get subcommand help
        main_parser = create_parser()

        # Get the subparser for this command
        subparsers_actions = [
            action
            for action in main_parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]

        if not subparsers_actions:
            return {"error": "No subparsers found"}

        subparsers = subparsers_actions[0]
        subparser = subparsers.choices.get(subcommand)

        if not subparser:
            return {"error": f"Subcommand {subcommand} not found"}

        # Get help text
        help_text = self._get_parser_help(subparser)

        # Extract options
        options = self._extract_command_options(subparser)

        # Get command-specific examples
        examples = self._get_command_examples(subcommand)

        return {
            "name": subcommand,
            "description": subparser.description or f"{subcommand.title()} command",
            "help_text": help_text,
            "usage": f"fqcn-converter {subcommand} [options] [arguments]",
            "options": options,
            "examples": examples,
            "common_use_cases": self._get_common_use_cases(subcommand),
        }

    def _get_parser_help(self, parser: argparse.ArgumentParser) -> str:
        """Get formatted help text from an argument parser."""
        try:
            return parser.format_help()
        except Exception as e:
            return f"Error getting help text: {e}"

    def _extract_global_options(
        self, parser: argparse.ArgumentParser
    ) -> List[Dict[str, Any]]:
        """Extract global options from the main parser."""
        options = []

        for action in parser._actions:
            if action.option_strings and action.dest not in ["help", "command"]:
                option_info = {
                    "flags": action.option_strings,
                    "dest": action.dest,
                    "help": action.help or "",
                    "type": str(action.type) if action.type else "str",
                    "default": action.default,
                    "choices": action.choices,
                    "required": getattr(action, "required", False),
                }
                options.append(option_info)

        return options

    def _extract_command_options(
        self, parser: argparse.ArgumentParser
    ) -> List[Dict[str, Any]]:
        """Extract options from a command parser."""
        options = []

        for action in parser._actions:
            if action.option_strings:
                option_info = {
                    "flags": action.option_strings,
                    "dest": action.dest,
                    "help": action.help or "",
                    "type": str(action.type) if action.type else "str",
                    "default": action.default,
                    "choices": action.choices,
                    "required": getattr(action, "required", False),
                    "action": str(action.__class__.__name__),
                }
                options.append(option_info)
            elif hasattr(action, "dest") and action.dest not in ["help"]:
                # Positional arguments
                option_info = {
                    "name": action.dest,
                    "help": action.help or "",
                    "nargs": action.nargs,
                    "type": str(action.type) if action.type else "str",
                    "positional": True,
                }
                options.append(option_info)

        return options

    def _get_command_examples(self, subcommand: str) -> List[Dict[str, str]]:
        """Get examples for a specific command."""
        examples_map = {
            "convert": [
                {
                    "description": "Convert a single playbook",
                    "command": "fqcn-converter convert playbook.yml",
                    "explanation": "Converts all short module names in playbook.yml to FQCN format",
                },
                {
                    "description": "Dry run conversion to preview changes",
                    "command": "fqcn-converter convert --dry-run playbook.yml",
                    "explanation": "Shows what changes would be made without modifying files",
                },
                {
                    "description": "Convert with custom configuration",
                    "command": "fqcn-converter convert --config custom_mappings.yml playbook.yml",
                    "explanation": "Uses custom FQCN mappings from configuration file",
                },
                {
                    "description": "Convert directory with backup",
                    "command": "fqcn-converter convert --backup roles/",
                    "explanation": "Converts all Ansible files in roles/ directory and creates backups",
                },
                {
                    "description": "Convert with progress reporting",
                    "command": "fqcn-converter convert --progress --report report.json roles/",
                    "explanation": "Shows progress and generates detailed conversion report",
                },
            ],
            "validate": [
                {
                    "description": "Validate a single file",
                    "command": "fqcn-converter validate playbook.yml",
                    "explanation": "Checks if playbook.yml properly uses FQCN format",
                },
                {
                    "description": "Validate with scoring",
                    "command": "fqcn-converter validate --score roles/",
                    "explanation": "Validates files and shows FQCN compliance scores",
                },
                {
                    "description": "Validate with ansible-lint",
                    "command": "fqcn-converter validate --lint --include-warnings playbook.yml",
                    "explanation": "Runs both FQCN validation and ansible-lint checks",
                },
                {
                    "description": "Generate validation report",
                    "command": "fqcn-converter validate --report validation.json --format json roles/",
                    "explanation": "Creates detailed JSON validation report",
                },
                {
                    "description": "Parallel validation",
                    "command": "fqcn-converter validate --parallel --workers 8 /path/to/projects",
                    "explanation": "Validates multiple files in parallel for faster processing",
                },
            ],
            "batch": [
                {
                    "description": "Batch convert multiple projects",
                    "command": "fqcn-converter batch /path/to/ansible/projects",
                    "explanation": "Discovers and converts all Ansible projects in the directory",
                },
                {
                    "description": "Batch convert with custom workers",
                    "command": "fqcn-converter batch --workers 8 /path/to/projects",
                    "explanation": "Uses 8 parallel workers for faster batch processing",
                },
                {
                    "description": "Batch dry run with report",
                    "command": "fqcn-converter batch --dry-run --report batch_report.json /path/to/projects",
                    "explanation": "Previews batch conversion and generates detailed report",
                },
            ],
        }

        return examples_map.get(subcommand, [])

    def _get_common_use_cases(self, subcommand: str) -> List[Dict[str, str]]:
        """Get common use cases for a command."""
        use_cases_map = {
            "convert": [
                {
                    "title": "Migrating Legacy Playbooks",
                    "description": "Convert existing Ansible playbooks to use FQCN format for Ansible 2.10+ compatibility",
                    "workflow": "1. Backup files, 2. Run dry-run, 3. Convert with validation, 4. Test playbooks",
                },
                {
                    "title": "CI/CD Integration",
                    "description": "Integrate FQCN conversion into CI/CD pipelines for automated compliance",
                    "workflow": "1. Add pre-commit hook, 2. Run in CI validation, 3. Generate reports",
                },
                {
                    "title": "Large-Scale Conversion",
                    "description": "Convert multiple Ansible projects across an organization",
                    "workflow": "1. Use batch command, 2. Parallel processing, 3. Centralized reporting",
                },
            ],
            "validate": [
                {
                    "title": "Compliance Checking",
                    "description": "Ensure Ansible code meets FQCN compliance standards",
                    "workflow": "1. Run validation, 2. Check scores, 3. Fix issues, 4. Re-validate",
                },
                {
                    "title": "Quality Gates",
                    "description": "Use validation in CI/CD as quality gates before deployment",
                    "workflow": "1. Validate on PR, 2. Block merge if failed, 3. Generate reports",
                },
                {
                    "title": "Migration Progress Tracking",
                    "description": "Track progress of FQCN migration across projects",
                    "workflow": "1. Baseline validation, 2. Regular scoring, 3. Progress reporting",
                },
            ],
            "batch": [
                {
                    "title": "Organization-wide Migration",
                    "description": "Convert all Ansible projects across multiple teams",
                    "workflow": "1. Discover projects, 2. Batch convert, 3. Validate results, 4. Report status",
                },
                {
                    "title": "Continuous Compliance",
                    "description": "Regularly check and convert new Ansible content",
                    "workflow": "1. Scheduled batch runs, 2. Automated reporting, 3. Alert on issues",
                },
            ],
        }

        return use_cases_map.get(subcommand, [])

    def _generate_cli_examples(self) -> List[Dict[str, Any]]:
        """Generate comprehensive CLI usage examples."""
        return [
            {
                "category": "Basic Usage",
                "examples": [
                    {
                        "title": "Convert Single File",
                        "command": "fqcn-converter convert playbook.yml",
                        "description": "Convert a single Ansible playbook to FQCN format",
                        "expected_output": "✅ Successfully converted 3 modules in playbook.yml",
                    },
                    {
                        "title": "Validate Conversion",
                        "command": "fqcn-converter validate playbook.yml",
                        "description": "Check if a file properly uses FQCN format",
                        "expected_output": "✅ File is compliant (score: 100%)",
                    },
                ],
            },
            {
                "category": "Advanced Usage",
                "examples": [
                    {
                        "title": "Batch Processing",
                        "command": "fqcn-converter batch --workers 4 /ansible/projects",
                        "description": "Process multiple projects in parallel",
                        "expected_output": "Processed 15 projects, 12 successful, 3 failed",
                    },
                    {
                        "title": "Custom Configuration",
                        "command": "fqcn-converter convert --config custom.yml --backup roles/",
                        "description": "Use custom mappings and create backups",
                        "expected_output": "Converted 25 files with custom mappings",
                    },
                ],
            },
            {
                "category": "Reporting and Analysis",
                "examples": [
                    {
                        "title": "Detailed Reporting",
                        "command": "fqcn-converter validate --score --report report.json --format json .",
                        "description": "Generate comprehensive validation report",
                        "expected_output": "Validation report saved to report.json",
                    },
                    {
                        "title": "Progress Tracking",
                        "command": "fqcn-converter convert --progress --dry-run large_project/",
                        "description": "Preview changes with progress indication",
                        "expected_output": "Processing 150/200 files... Would convert 45 modules",
                    },
                ],
            },
        ]

    def _extract_common_options(self) -> Dict[str, Any]:
        """Extract common options used across commands."""
        return {
            "verbosity": {
                "options": ["--quiet", "--verbose", "--debug"],
                "description": "Control output verbosity level",
                "usage": "Use --quiet for minimal output, --verbose for detailed information",
            },
            "configuration": {
                "options": ["--config"],
                "description": "Specify custom FQCN mapping configuration",
                "usage": "Point to YAML file with custom module mappings",
            },
            "dry_run": {
                "options": ["--dry-run", "-n"],
                "description": "Preview changes without modifying files",
                "usage": "Always test with dry-run before actual conversion",
            },
            "reporting": {
                "options": ["--report", "--format"],
                "description": "Generate detailed operation reports",
                "usage": "Use for audit trails and compliance documentation",
            },
        }

    def _generate_troubleshooting_guide(self) -> List[Dict[str, str]]:
        """Generate troubleshooting guide for common CLI issues."""
        return [
            {
                "issue": "Command not found: fqcn-converter",
                "cause": "Package not installed or not in PATH",
                "solution": "Install with 'pip install fqcn-converter' or run from project directory",
            },
            {
                "issue": "Permission denied when converting files",
                "cause": "Insufficient file permissions",
                "solution": "Check file permissions or run with appropriate user privileges",
            },
            {
                "issue": "YAML parsing errors during conversion",
                "cause": "Invalid YAML syntax in source files",
                "solution": "Fix YAML syntax errors before conversion, use --skip-validation to bypass",
            },
            {
                "issue": "No files found to convert",
                "cause": "No Ansible files detected in specified path",
                "solution": "Check path contains .yml/.yaml files with Ansible content",
            },
            {
                "issue": "Conversion fails with configuration error",
                "cause": "Invalid or missing configuration file",
                "solution": "Verify configuration file format and path, use default if unsure",
            },
            {
                "issue": "Batch processing hangs or is very slow",
                "cause": "Too many parallel workers or large files",
                "solution": "Reduce --workers count or process smaller batches",
            },
        ]

    def _generate_cli_markdown(self, cli_docs: Dict[str, Any]) -> None:
        """Generate markdown documentation from CLI docs."""
        md_content = f"""# {cli_docs['title']}

{cli_docs['description']}

**Version:** {cli_docs['version']}

## Table of Contents

- [Main Command](#main-command)
- [Subcommands](#subcommands)
- [Usage Examples](#usage-examples)
- [Common Options](#common-options)
- [Troubleshooting](#troubleshooting)

## Main Command

### {cli_docs['main_command']['name']}

{cli_docs['main_command']['description']}

**Usage:** `{cli_docs['main_command']['usage']}`

#### Global Options

"""

        # Document global options
        for option in cli_docs["main_command"]["global_options"]:
            flags = ", ".join(f"`{flag}`" for flag in option["flags"])
            md_content += f"- {flags}: {option['help']}\n"

        md_content += "\n#### Available Subcommands\n\n"
        for subcommand in cli_docs["main_command"]["subcommands_list"]:
            md_content += f"- `{subcommand}`: {cli_docs['subcommands'][subcommand]['description']}\n"

        # Document subcommands
        md_content += "\n## Subcommands\n\n"

        for subcommand_name, subcommand_info in cli_docs["subcommands"].items():
            md_content += f"### {subcommand_name}\n\n"
            md_content += f"{subcommand_info['description']}\n\n"
            md_content += f"**Usage:** `{subcommand_info['usage']}`\n\n"

            # Options
            if subcommand_info["options"]:
                md_content += "#### Options\n\n"
                for option in subcommand_info["options"]:
                    if option.get("positional"):
                        md_content += f"- `{option['name']}`: {option['help']}\n"
                    else:
                        flags = ", ".join(f"`{flag}`" for flag in option["flags"])
                        md_content += f"- {flags}: {option['help']}\n"
                md_content += "\n"

            # Examples
            if subcommand_info["examples"]:
                md_content += "#### Examples\n\n"
                for example in subcommand_info["examples"]:
                    md_content += f"**{example['description']}**\n"
                    md_content += f"```bash\n{example['command']}\n```\n"
                    if "explanation" in example:
                        md_content += f"{example['explanation']}\n"
                    md_content += "\n"

            # Common use cases
            if subcommand_info["common_use_cases"]:
                md_content += "#### Common Use Cases\n\n"
                for use_case in subcommand_info["common_use_cases"]:
                    md_content += f"**{use_case['title']}**\n\n"
                    md_content += f"{use_case['description']}\n\n"
                    md_content += f"*Workflow:* {use_case['workflow']}\n\n"

            md_content += "---\n\n"

        # Usage examples
        md_content += "## Usage Examples\n\n"
        for category in cli_docs["usage_examples"]:
            md_content += f"### {category['category']}\n\n"
            for example in category["examples"]:
                md_content += f"#### {example['title']}\n\n"
                md_content += f"{example['description']}\n\n"
                md_content += f"```bash\n{example['command']}\n```\n\n"
                if "expected_output" in example:
                    md_content += f"**Expected Output:**\n```\n{example['expected_output']}\n```\n\n"

        # Common options
        md_content += "## Common Options\n\n"
        for option_name, option_info in cli_docs["common_options"].items():
            md_content += f"### {option_name.replace('_', ' ').title()}\n\n"
            options = ", ".join(f"`{opt}`" for opt in option_info["options"])
            md_content += f"**Options:** {options}\n\n"
            md_content += f"{option_info['description']}\n\n"
            md_content += f"**Usage:** {option_info['usage']}\n\n"

        # Troubleshooting
        md_content += "## Troubleshooting\n\n"
        for issue in cli_docs["troubleshooting"]:
            md_content += f"### {issue['issue']}\n\n"
            md_content += f"**Cause:** {issue['cause']}\n\n"
            md_content += f"**Solution:** {issue['solution']}\n\n"

        # Write markdown file
        md_file = self.output_dir / "cli_reference.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)

    def _generate_interactive_examples(self, cli_docs: Dict[str, Any]) -> None:
        """Generate interactive CLI examples for testing."""
        examples_script = """#!/bin/bash
# Interactive FQCN Converter CLI Examples
# This script demonstrates various CLI usage patterns

set -e

echo "🚀 FQCN Converter CLI Examples"
echo "=============================="

# Function to run example with explanation
run_example() {
    local title="$1"
    local command="$2"
    local explanation="$3"
    
    echo ""
    echo "📝 $title"
    echo "Command: $command"
    echo "Explanation: $explanation"
    echo ""
    
    if [[ "$DRY_RUN" != "false" ]]; then
        echo "💡 Add DRY_RUN=false to actually run commands"
        echo "   Example: DRY_RUN=false ./cli_examples.sh"
    else
        echo "▶️  Running: $command"
        eval "$command"
    fi
    
    echo "----------------------------------------"
}

# Set default to dry run unless specified
DRY_RUN=${DRY_RUN:-true}

if [[ "$DRY_RUN" == "true" ]]; then
    echo "🔍 DRY RUN MODE - Commands will be shown but not executed"
    echo "   Set DRY_RUN=false to actually run commands"
fi

"""

        # Add examples from documentation
        for category in cli_docs["usage_examples"]:
            examples_script += f'\necho ""\necho "=== {category["category"]} ==="\n'

            for example in category["examples"]:
                examples_script += f"""
run_example "{example['title']}" \\
    "{example['command']}" \\
    "{example['description']}"
"""

        examples_script += """
echo ""
echo "✅ All examples completed!"
echo ""
echo "💡 Tips:"
echo "  - Use --help with any command for detailed information"
echo "  - Always test with --dry-run before making changes"
echo "  - Check the generated reports for detailed analysis"
echo "  - Use --verbose for debugging issues"
"""

        # Write interactive examples script
        examples_file = self.output_dir / "cli_examples.sh"
        with open(examples_file, "w", encoding="utf-8") as f:
            f.write(examples_script)

        # Make executable
        examples_file.chmod(0o755)


def main():
    """Main entry point for CLI documentation generation."""
    # Determine output directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    docs_dir = project_root / "docs" / "usage"

    # Generate documentation
    generator = Context7CLIDocGenerator(docs_dir)
    generator.generate_cli_docs()

    print(f"\n📚 Context7 CLI documentation generated successfully!")
    print(f"   📁 Output directory: {docs_dir}")
    print(f"   📄 CLI Reference: {docs_dir / 'cli_reference.md'}")
    print(f"   📄 JSON Data: {docs_dir / 'cli_reference.json'}")
    print(f"   🔧 Interactive Examples: {docs_dir / 'cli_examples.sh'}")


if __name__ == "__main__":
    main()
