"""
Main CLI entry point for FQCN Converter.

This module provides the main command-line interface with subcommands
for convert, validate, and batch operations.
"""

import argparse
import logging
import sys
from typing import List, Optional, Tuple

from . import batch, convert, validate


def setup_logging(verbosity: str) -> None:
    """Configure logging based on verbosity level."""
    levels = {"quiet": logging.ERROR, "normal": logging.INFO, "verbose": logging.DEBUG}

    level = levels.get(verbosity, logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Suppress verbose output from third-party libraries unless in debug mode
    if level != logging.DEBUG:
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="fqcn-converter",
        description="Convert Ansible playbooks and roles to use Fully Qualified Collection Names (FQCN)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a single file
  fqcn-converter convert playbook.yml
  
  # Dry run to preview changes
  fqcn-converter convert --dry-run playbook.yml
  
  # Validate converted files
  fqcn-converter validate roles/
  
  # Batch convert multiple projects
  fqcn-converter batch /path/to/ansible/projects
  
  # Use custom mapping configuration
  fqcn-converter convert --config custom_mappings.yml playbook.yml
  
  # Global flags can be placed anywhere:
  fqcn-converter --verbose convert --dry-run playbook.yml
  fqcn-converter convert --verbose --dry-run playbook.yml
  fqcn-converter convert --dry-run playbook.yml --verbose

For more help on specific commands, use:
  fqcn-converter <command> --help
        """,
    )

    # Global options
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    # Verbosity group (mutually exclusive)
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        "--quiet",
        "-q",
        action="store_const",
        const="quiet",
        dest="verbosity",
        help="Suppress all output except errors",
    )
    verbosity_group.add_argument(
        "--verbose",
        "-v",
        action="store_const",
        const="verbose",
        dest="verbosity",
        help="Enable verbose output with debug information",
    )
    verbosity_group.add_argument(
        "--debug",
        action="store_const",
        const="verbose",
        dest="verbosity",
        help="Enable debug output (same as --verbose)",
    )

    # Set default verbosity
    parser.set_defaults(verbosity="normal")

    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        title="Commands",
        description="Available commands for FQCN conversion",
        dest="command",
        help='Use "fqcn-converter <command> --help" for command-specific help',
    )

    # Convert command
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert Ansible files to use FQCN",
        description="Convert Ansible playbooks, roles, and tasks to use Fully Qualified Collection Names",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a single file
  fqcn-converter convert playbook.yml
  
  # Convert with dry run
  fqcn-converter convert --dry-run roles/nginx/tasks/main.yml
  
  # Convert with custom configuration
  fqcn-converter convert --config custom_mappings.yml playbook.yml
  
  # Convert and create backup
  fqcn-converter convert --backup playbook.yml
        """,
    )
    convert.add_convert_arguments(convert_parser)

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate FQCN conversion results",
        description="Validate that Ansible files have been properly converted to use FQCN",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a single file
  fqcn-converter validate playbook.yml
  
  # Validate all files in directory
  fqcn-converter validate roles/
  
  # Generate validation report
  fqcn-converter validate --report validation_report.json roles/
        """,
    )
    validate.add_validate_arguments(validate_parser)

    # Batch command
    batch_parser = subparsers.add_parser(
        "batch",
        help="Batch process multiple Ansible projects",
        description="Discover and convert multiple Ansible projects in parallel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discover and convert all projects
  fqcn-converter batch /path/to/ansible/projects
  
  # Batch convert with 8 workers
  fqcn-converter batch --workers 8 /path/to/projects
  
  # Generate batch report
  fqcn-converter batch --report batch_report.json /path/to/projects
        """,
    )
    batch.add_batch_arguments(batch_parser)

    return parser


def preprocess_args(args: List[str]) -> Tuple[List[str], str]:
    """
    Preprocess command line arguments to extract global flags and reorder them.

    This allows global flags like --verbose, --quiet, --debug to be placed anywhere
    in the command line, including after the subcommand.

    Args:
        args: Raw command line arguments

    Returns:
        Tuple of (reordered_args, verbosity_level)
    """
    global_flags = {"--verbose", "-v", "--quiet", "-q", "--debug", "--version"}

    verbosity = "normal"
    reordered_args = []
    global_args = []
    i = 0

    while i < len(args):
        arg = args[i]

        if arg in ["--verbose", "-v"]:
            verbosity = "verbose"
            global_args.append(arg)
        elif arg in ["--quiet", "-q"]:
            verbosity = "quiet"
            global_args.append(arg)
        elif arg == "--debug":
            verbosity = "verbose"
            global_args.append(arg)
        elif arg == "--version":
            global_args.append(arg)
        else:
            reordered_args.append(arg)

        i += 1

    # Put global args first, then the rest
    final_args = global_args + reordered_args

    return final_args, verbosity


def main() -> Optional[int]:
    """Main CLI entry point with subcommands."""
    # Preprocess arguments to handle global flags in any position
    raw_args = sys.argv[1:]
    processed_args, verbosity = preprocess_args(raw_args)

    parser = create_parser()

    # Parse the reordered arguments
    try:
        args = parser.parse_args(processed_args)
    except SystemExit as e:
        # Handle --version and --help exits gracefully
        return e.code

    # Override verbosity if it was detected in preprocessing
    if verbosity != "normal":
        args.verbosity = verbosity

    # Setup logging based on verbosity
    setup_logging(args.verbosity)

    # Get logger after setup
    logger = logging.getLogger(__name__)

    # If no command specified, show help
    if not args.command:
        parser.print_help()
        return 1

    try:
        # Route to appropriate command handler
        if args.command == "convert":
            return convert.main(args)
        elif args.command == "validate":
            return validate.main(args)
        elif args.command == "batch":
            return batch.main(args)
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1

    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbosity == "verbose":
            logger.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
