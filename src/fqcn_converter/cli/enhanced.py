"""Enhanced CLI with new features for FQCN Converter."""

import sys
import click
from pathlib import Path
from typing import Optional

from ..core.converter import FQCNConverter
from ..utils.logging import setup_logging, get_logger
from ..reporting.report_generator import ReportGenerator
from ..reporting.models import ReportFormat
from ..tools.precommit import PreCommitHook
from ..tools.config_generator import ConfigurationGenerator
from .interactive import interactive

logger = get_logger(__name__)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Suppress output except errors')
@click.pass_context
def cli(ctx, verbose, quiet):
    """Enhanced FQCN Converter with interactive mode and advanced reporting."""
    # Ensure that ctx.obj exists and is a dict
    ctx.ensure_object(dict)
    
    # Set up logging
    if verbose:
        level = 'DEBUG'
    elif quiet:
        level = 'ERROR'
    else:
        level = 'INFO'
    
    setup_logging(level)
    ctx.obj['verbose'] = verbose


@cli.command()
@click.argument('target', type=click.Path(exists=True, path_type=Path))
@click.option('--config', '-c', type=click.Path(exists=True, path_type=Path),
              help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def interactive(ctx, target: Path, config: Optional[Path], verbose: bool):
    """Start interactive FQCN conversion mode."""
    from .interactive import InteractiveMode
    
    try:
        # Configure logging
        if verbose or ctx.obj.get('verbose'):
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
        click.echo(f"Error: {e}", err=True)
        if verbose or ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument('target', type=click.Path(exists=True, path_type=Path))
@click.option('--format', 'report_format', 
              type=click.Choice(['json', 'html', 'markdown', 'console']),
              default='console', help='Report output format')
@click.option('--output', '-o', type=click.Path(path_type=Path),
              help='Output file for report')
@click.option('--all-formats', is_flag=True, 
              help='Generate reports in all formats')
@click.option('--output-dir', type=click.Path(path_type=Path),
              help='Output directory for all formats')
@click.pass_context
def convert_with_report(ctx, target: Path, report_format: str, output: Optional[Path],
                       all_formats: bool, output_dir: Optional[Path]):
    """Convert files with enhanced reporting."""
    try:
        # Create report generator
        report_gen = ReportGenerator()
        report_gen.start_session(target)
        
        # Create converter
        converter = FQCNConverter()
        
        # Process files
        if target.is_file():
            files_to_process = [target]
        else:
            files_to_process = list(target.rglob("*.yml")) + list(target.rglob("*.yaml"))
        
        for file_path in files_to_process:
            import time
            start_time = time.time()
            
            try:
                result = converter.convert_file(file_path)
                processing_time = time.time() - start_time
                report_gen.add_file_result(file_path, result, processing_time)
                
            except Exception as e:
                processing_time = time.time() - start_time
                report_gen.add_error(
                    error_type="ConversionError",
                    error_message=str(e),
                    file_path=file_path
                )
        
        # Finalize report
        report = report_gen.finalize_session()
        
        # Generate reports
        if all_formats:
            if not output_dir:
                output_dir = Path('reports')
            
            generated_files = report_gen.generate_all_formats(output_dir)
            click.echo(f"Generated reports in {len(generated_files)} formats:")
            for format_type, file_path in generated_files.items():
                click.echo(f"  {format_type.value}: {file_path}")
        else:
            formatted_report = report_gen.generate_report(report_format, output)
            
            if output:
                click.echo(f"Report saved to: {output}")
            else:
                click.echo(formatted_report)
        
        # Print summary
        stats = report_gen.get_summary_stats()
        click.echo(f"\nSummary: {stats['files_processed']} files processed, "
                  f"{stats['success_rate']:.1%} success rate")
        
        sys.exit(0 if not report.has_errors else 1)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.group()
def tools():
    """Developer tools and utilities."""
    pass


@tools.command()
@click.argument('repo_path', type=click.Path(exists=True, path_type=Path))
@click.option('--auto-fix', is_flag=True, help='Enable automatic fixing')
@click.option('--strict', is_flag=True, help='Enable strict mode')
@click.option('--uninstall', is_flag=True, help='Uninstall the hook')
def precommit(repo_path: Path, auto_fix: bool, strict: bool, uninstall: bool):
    """Install or manage pre-commit hooks."""
    try:
        if uninstall:
            success = PreCommitHook.uninstall_hook(repo_path)
            if success:
                click.echo("Pre-commit hook uninstalled successfully")
            else:
                click.echo("Failed to uninstall pre-commit hook", err=True)
                sys.exit(1)
        else:
            config = {'auto_fix': auto_fix, 'strict_mode': strict}
            success = PreCommitHook.install_hook(repo_path, config)
            
            if success:
                click.echo("Pre-commit hook installed successfully")
                if auto_fix:
                    click.echo("  - Auto-fix enabled")
                if strict:
                    click.echo("  - Strict mode enabled")
            else:
                click.echo("Failed to install pre-commit hook", err=True)
                sys.exit(1)
                
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@tools.command()
@click.option('--template', type=click.Choice(['basic', 'advanced', 'cicd', 'enterprise']),
              default='basic', help='Configuration template')
@click.option('--project-name', default='my-ansible-project', help='Project name')
@click.option('--output', '-o', type=click.Path(path_type=Path), 
              default=Path('fqcn-config.yml'), help='Output file path')
@click.option('--format', 'config_format', type=click.Choice(['yaml', 'json']), 
              default='yaml', help='Output format')
@click.option('--detect', type=click.Path(exists=True, path_type=Path), 
              help='Auto-detect configuration for project')
def config(template: str, project_name: str, output: Path, config_format: str, 
          detect: Optional[Path]):
    """Generate configuration files."""
    try:
        generator = ConfigurationGenerator()
        
        if detect:
            config_obj = generator.generate_project_config(detect, output)
            click.echo(f"Generated configuration for {detect} -> {output}")
        else:
            config_obj = generator.generate_config(template, project_name=project_name)
            generator.save_config(config_obj, output, config_format)
            click.echo(f"Generated {template} configuration -> {output}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@tools.command()
@click.argument('output_path', type=click.Path(path_type=Path))
@click.option('--auto-fix', is_flag=True, help='Enable auto-fix in hook')
@click.option('--strict', is_flag=True, help='Enable strict mode in hook')
def generate_precommit_config(output_path: Path, auto_fix: bool, strict: bool):
    """Generate pre-commit configuration file."""
    try:
        generator = ConfigurationGenerator()
        generator.generate_precommit_config(output_path, auto_fix, strict)
        click.echo(f"Generated pre-commit config -> {output_path}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@tools.command()
@click.argument('output_path', type=click.Path(path_type=Path))
@click.option('--python-version', default='3.9', help='Python version for workflow')
def generate_github_workflow(output_path: Path, python_version: str):
    """Generate GitHub Actions workflow."""
    try:
        generator = ConfigurationGenerator()
        generator.generate_github_workflow(output_path, python_version)
        click.echo(f"Generated GitHub workflow -> {output_path}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('reports_dir', type=click.Path(exists=True, path_type=Path))
@click.option('--output', '-o', type=click.Path(path_type=Path),
              help='Output file for comparison report')
def compare_reports(reports_dir: Path, output: Optional[Path]):
    """Compare multiple conversion reports."""
    try:
        # Load all JSON reports from directory
        report_files = list(reports_dir.glob("*.json"))
        
        if not report_files:
            click.echo("No JSON report files found in directory", err=True)
            sys.exit(1)
        
        reports = []
        for report_file in report_files:
            try:
                report = ReportGenerator.load_report(report_file)
                reports.append(report)
            except Exception as e:
                click.echo(f"Warning: Could not load {report_file}: {e}", err=True)
        
        if not reports:
            click.echo("No valid reports found", err=True)
            sys.exit(1)
        
        # Generate comparison
        comparison = ReportGenerator.create_comparison_report(reports)
        
        if output:
            import json
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(comparison, f, indent=2, default=str)
            click.echo(f"Comparison report saved to: {output}")
        else:
            import json
            click.echo(json.dumps(comparison, indent=2, default=str))
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()