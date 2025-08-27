"""Interactive CLI mode for FQCN Converter.

This module provides an interactive command-line interface that guides users
through the conversion process with confirmations, previews, and step-by-step
workflows.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import click
from colorama import Fore, Style, init

from ..core.converter import FQCNConverter
from ..core.validator import FQCNValidator
from ..utils.logging import get_logger

# Initialize colorama for cross-platform colored output
init(autoreset=True)

logger = get_logger(__name__)


class InteractiveMode:
    """Interactive mode handler for guided FQCN conversion."""
    
    def __init__(self, converter: Optional[FQCNConverter] = None):
        """Initialize interactive mode.
        
        Args:
            converter: Optional FQCNConverter instance. If None, creates default.
        """
        self.converter = converter or FQCNConverter()
        self.validator = FQCNValidator()
        self.changes_made = []
        self.session_stats = {
            'files_processed': 0,
            'conversions_made': 0,
            'files_skipped': 0,
            'errors_encountered': 0
        }
    
    def start_interactive_session(self, target_path: Path) -> bool:
        """Start an interactive conversion session.
        
        Args:
            target_path: Path to file or directory to convert
            
        Returns:
            True if session completed successfully, False otherwise
        """
        try:
            self._print_welcome()
            
            if not self._confirm_start(target_path):
                self._print_info("Interactive session cancelled by user.")
                return False
            
            if target_path.is_file():
                return self._process_single_file_interactive(target_path)
            elif target_path.is_dir():
                return self._process_directory_interactive(target_path)
            else:
                self._print_error(f"Path does not exist: {target_path}")
                return False
                
        except KeyboardInterrupt:
            self._print_warning("\nInteractive session interrupted by user.")
            return False
        except Exception as e:
            self._print_error(f"Unexpected error in interactive session: {e}")
            logger.exception("Interactive session error")
            return False
        finally:
            self._print_session_summary()
    
    def _print_welcome(self) -> None:
        """Print welcome message for interactive mode."""
        click.echo(f"\n{Fore.CYAN}{'='*60}")
        click.echo(f"{Fore.CYAN}  FQCN Converter - Interactive Mode")
        click.echo(f"{Fore.CYAN}{'='*60}")
        click.echo(f"{Fore.GREEN}Welcome to the interactive FQCN conversion wizard!")
        click.echo(f"{Fore.YELLOW}This mode will guide you through the conversion process")
        click.echo(f"{Fore.YELLOW}with previews and confirmations for each change.")
        click.echo()
    
    def _confirm_start(self, target_path: Path) -> bool:
        """Confirm the start of interactive session.
        
        Args:
            target_path: Target path for conversion
            
        Returns:
            True if user confirms, False otherwise
        """
        path_type = "directory" if target_path.is_dir() else "file"
        click.echo(f"Target {path_type}: {Fore.CYAN}{target_path}")
        
        if target_path.is_dir():
            # Count potential files
            yaml_files = list(target_path.rglob("*.yml")) + list(target_path.rglob("*.yaml"))
            click.echo(f"Found {Fore.YELLOW}{len(yaml_files)}{Style.RESET_ALL} YAML files to process")
        
        return click.confirm(f"\nProceed with interactive conversion?", default=True)
    
    def _process_single_file_interactive(self, file_path: Path) -> bool:
        """Process a single file interactively.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            True if processing completed successfully
        """
        try:
            self._print_info(f"Processing file: {file_path}")
            
            # Validate file first
            if not self._validate_file_interactive(file_path):
                return False
            
            # Show preview of changes
            preview_data = self._generate_preview(file_path)
            if not preview_data:
                self._print_info("No FQCN conversions needed for this file.")
                return True
            
            # Show preview and get confirmation
            if not self._show_preview_and_confirm(file_path, preview_data):
                self._print_info("File conversion skipped by user.")
                self.session_stats['files_skipped'] += 1
                return True
            
            # Perform conversion
            result = self.converter.convert_file(file_path)
            if result.success:
                self._print_success(f"Successfully converted: {file_path}")
                self.session_stats['files_processed'] += 1
                self.session_stats['conversions_made'] += len(result.conversions)
                self.changes_made.append((file_path, result))
            else:
                self._print_error(f"Conversion failed: {result.error}")
                self.session_stats['errors_encountered'] += 1
                return False
            
            return True
            
        except Exception as e:
            self._print_error(f"Error processing file {file_path}: {e}")
            logger.exception(f"Error processing file {file_path}")
            self.session_stats['errors_encountered'] += 1
            return False
    
    def _process_directory_interactive(self, dir_path: Path) -> bool:
        """Process a directory interactively.
        
        Args:
            dir_path: Path to the directory to process
            
        Returns:
            True if processing completed successfully
        """
        try:
            # Find all YAML files
            yaml_files = list(dir_path.rglob("*.yml")) + list(dir_path.rglob("*.yaml"))
            
            if not yaml_files:
                self._print_warning("No YAML files found in directory.")
                return True
            
            self._print_info(f"Found {len(yaml_files)} YAML files to process")
            
            # Process each file
            for i, file_path in enumerate(yaml_files, 1):
                click.echo(f"\n{Fore.CYAN}[{i}/{len(yaml_files)}] Processing: {file_path.name}")
                
                if not self._process_single_file_interactive(file_path):
                    if not click.confirm("Continue with remaining files?", default=True):
                        break
            
            return True
            
        except Exception as e:
            self._print_error(f"Error processing directory {dir_path}: {e}")
            logger.exception(f"Error processing directory {dir_path}")
            return False
    
    def _validate_file_interactive(self, file_path: Path) -> bool:
        """Validate a file interactively.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if file is valid or has non-critical issues
        """
        try:
            validation_result = self.validator.validate_file(file_path)
            
            if validation_result.valid:
                self._print_success("File validation passed")
                return True
            else:
                self._print_warning("File validation issues found (proceeding with conversion):")
                for issue in validation_result.issues:
                    click.echo(f"  - {issue}")
                
                # Continue automatically - validation issues are informational only
                return True
                
        except Exception as e:
            self._print_error(f"Validation error: {e}")
            self._print_warning("Proceeding without validation")
            return True
    
    def _generate_preview(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Generate preview of changes for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Preview data dictionary or None if no changes
        """
        try:
            # Use converter's dry-run mode to get potential changes
            result = self.converter.convert_file(file_path, dry_run=True)
            
            if not result.success or result.changes_made == 0:
                return None
            
            return {
                'file_path': file_path,
                'conversions': [{'original': 'module', 'fqcn': 'collection.module'}] * result.changes_made,  # Simplified
                'original_content': file_path.read_text(encoding='utf-8'),
                'converted_content': result.converted_content or file_path.read_text(encoding='utf-8')
            }
            
        except Exception as e:
            logger.exception(f"Error generating preview for {file_path}")
            return None
    
    def _show_preview_and_confirm(self, file_path: Path, preview_data: Dict[str, Any]) -> bool:
        """Show preview of changes and get user confirmation.
        
        Args:
            file_path: Path to the file
            preview_data: Preview data from _generate_preview
            
        Returns:
            True if user confirms the changes
        """
        try:
            conversions = preview_data['conversions']
            
            click.echo(f"\n{Fore.YELLOW}Preview of changes for: {file_path.name}")
            click.echo(f"{Fore.YELLOW}{'-' * 50}")
            
            # Show conversions summary
            click.echo(f"{Fore.GREEN}Found {len(conversions)} potential conversions:")
            
            for i, conversion in enumerate(conversions, 1):
                click.echo(f"  {i}. {Fore.RED}{conversion['original']}{Style.RESET_ALL} → "
                          f"{Fore.GREEN}{conversion['fqcn']}{Style.RESET_ALL}")
                if 'line' in conversion:
                    click.echo(f"     Line {conversion['line']}")
            
            # Show diff preview if requested
            if click.confirm("\nShow detailed diff?", default=False):
                self._show_detailed_diff(preview_data)
            
            return click.confirm(f"\nApply these {len(conversions)} conversions?", default=True)
            
        except Exception as e:
            self._print_error(f"Error showing preview: {e}")
            return False
    
    def _show_detailed_diff(self, preview_data: Dict[str, Any]) -> None:
        """Show detailed diff of changes.
        
        Args:
            preview_data: Preview data containing original and converted content
        """
        try:
            original_lines = preview_data['original_content'].splitlines()
            converted_lines = preview_data['converted_content'].splitlines()
            
            click.echo(f"\n{Fore.CYAN}Detailed diff:")
            click.echo(f"{Fore.CYAN}{'-' * 30}")
            
            # Simple line-by-line diff
            max_lines = max(len(original_lines), len(converted_lines))
            
            for i in range(min(max_lines, 20)):  # Limit to first 20 lines
                orig_line = original_lines[i] if i < len(original_lines) else ""
                conv_line = converted_lines[i] if i < len(converted_lines) else ""
                
                if orig_line != conv_line:
                    click.echo(f"{Fore.RED}- {orig_line}")
                    click.echo(f"{Fore.GREEN}+ {conv_line}")
                else:
                    click.echo(f"  {orig_line}")
            
            if max_lines > 20:
                click.echo(f"{Fore.YELLOW}... ({max_lines - 20} more lines)")
                
        except Exception as e:
            self._print_error(f"Error showing diff: {e}")
    
    def _print_session_summary(self) -> None:
        """Print summary of the interactive session."""
        click.echo(f"\n{Fore.CYAN}{'='*50}")
        click.echo(f"{Fore.CYAN}  Interactive Session Summary")
        click.echo(f"{Fore.CYAN}{'='*50}")
        
        stats = self.session_stats
        click.echo(f"Files processed: {Fore.GREEN}{stats['files_processed']}")
        click.echo(f"Conversions made: {Fore.GREEN}{stats['conversions_made']}")
        click.echo(f"Files skipped: {Fore.YELLOW}{stats['files_skipped']}")
        click.echo(f"Errors encountered: {Fore.RED}{stats['errors_encountered']}")
        
        if self.changes_made:
            click.echo(f"\n{Fore.GREEN}Successfully converted files:")
            for file_path, result in self.changes_made:
                click.echo(f"  - {file_path} ({len(result.conversions)} conversions)")
        
        click.echo(f"\n{Fore.CYAN}Thank you for using FQCN Converter Interactive Mode!")
    
    def _print_success(self, message: str) -> None:
        """Print success message."""
        click.echo(f"{Fore.GREEN}✓ {message}")
    
    def _print_info(self, message: str) -> None:
        """Print info message."""
        click.echo(f"{Fore.CYAN}ℹ {message}")
    
    def _print_warning(self, message: str) -> None:
        """Print warning message."""
        click.echo(f"{Fore.YELLOW}⚠ {message}")
    
    def _print_error(self, message: str) -> None:
        """Print error message."""
        click.echo(f"{Fore.RED}✗ {message}")


@click.command()
@click.argument('target', type=click.Path(exists=True, path_type=Path))
@click.option('--config', '-c', type=click.Path(exists=True, path_type=Path),
              help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def interactive(target: Path, config: Optional[Path], verbose: bool) -> None:
    """Start interactive FQCN conversion mode.
    
    TARGET: Path to file or directory to convert interactively
    """
    try:
        # Configure logging
        if verbose:
            import logging
            logging.getLogger('fqcn_converter').setLevel(logging.DEBUG)
        
        # Create converter with config if provided
        converter = None
        if config:
            # TODO: Implement config loading
            pass
        
        # Start interactive session
        interactive_mode = InteractiveMode(converter)
        success = interactive_mode.start_interactive_session(target)
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        click.echo(f"{Fore.RED}Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    interactive()