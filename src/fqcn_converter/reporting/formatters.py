"""Report formatters for different output formats."""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any
from colorama import Fore, Style, init

from .models import ConversionReport, FileChangeRecord, ConversionStatus

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class ReportFormatter(ABC):
    """Abstract base class for report formatters."""
    
    @abstractmethod
    def format_report(self, report: ConversionReport) -> str:
        """Format a conversion report."""
        pass


class JSONReportFormatter(ReportFormatter):
    """JSON report formatter."""
    
    def __init__(self, indent: int = 2):
        """Initialize JSON formatter."""
        self.indent = indent
    
    def format_report(self, report: ConversionReport) -> str:
        """Format report as JSON."""
        return report.to_json(indent=self.indent)


class ConsoleReportFormatter(ReportFormatter):
    """Console report formatter with colors."""
    
    def __init__(self, use_colors: bool = True, compact: bool = False):
        """Initialize console formatter."""
        self.use_colors = use_colors
        self.compact = compact
    
    def format_report(self, report: ConversionReport) -> str:
        """Format report for console output."""
        lines = []
        
        # Header
        if self.use_colors:
            lines.append(f"{Fore.CYAN}{'='*60}")
            lines.append(f"{Fore.CYAN}  FQCN Conversion Report")
            lines.append(f"{Fore.CYAN}{'='*60}")
        else:
            lines.append("="*60)
            lines.append("  FQCN Conversion Report")
            lines.append("="*60)
        
        lines.append(f"Session ID: {report.session_id}")
        lines.append(f"Start Time: {report.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if report.end_time:
            lines.append(f"End Time: {report.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"Duration: {report.duration:.2f} seconds")
        
        if report.target_path:
            lines.append(f"Target: {report.target_path}")
        
        lines.append("")
        
        # Summary
        if self.use_colors:
            lines.append(f"{Fore.YELLOW}Summary:")
        else:
            lines.append("Summary:")
        
        stats = report.statistics
        
        if not self.compact:
            lines.append(f"  Files Processed: {stats.total_files_processed}")
            lines.append(f"  Files Successful: {self._colorize_number(stats.total_files_successful, 'green')}")
            lines.append(f"  Files Failed: {self._colorize_number(stats.total_files_failed, 'red')}")
            lines.append(f"  Files Skipped: {self._colorize_number(stats.total_files_skipped, 'yellow')}")
            lines.append(f"  Success Rate: {self._colorize_percentage(stats.success_rate)}")
            lines.append(f"  Conversions Made: {stats.total_conversions_made}")
            lines.append(f"  Conversion Efficiency: {self._colorize_percentage(stats.conversion_efficiency)}")
            lines.append(f"  Processing Speed: {stats.processing_speed:.1f} files/sec")
        else:
            lines.append(f"  {stats.total_files_processed} files, "
                        f"{self._colorize_percentage(stats.success_rate)} success, "
                        f"{stats.total_conversions_made} conversions")
        
        lines.append("")
        
        # File details (if not compact)
        if not self.compact and report.file_records:
            if self.use_colors:
                lines.append(f"{Fore.YELLOW}File Details:")
            else:
                lines.append("File Details:")
            
            for record in report.file_records:
                status_color = self._get_status_color(record.status)
                status_text = record.status.value.upper()
                
                if self.use_colors:
                    lines.append(f"  {status_color}{status_text:<8}{Style.RESET_ALL} "
                               f"{record.file_path.name} "
                               f"({record.conversions_made}/{record.conversions_attempted} conversions, "
                               f"{record.processing_time:.3f}s)")
                else:
                    lines.append(f"  {status_text:<8} {record.file_path.name} "
                               f"({record.conversions_made}/{record.conversions_attempted} conversions, "
                               f"{record.processing_time:.3f}s)")
            
            lines.append("")
        
        # Errors and warnings
        if report.has_errors:
            if self.use_colors:
                lines.append(f"{Fore.RED}Errors:")
            else:
                lines.append("Errors:")
            
            for error in report.errors:
                lines.append(f"  - {error}")
            
            lines.append("")
        
        if report.has_warnings:
            if self.use_colors:
                lines.append(f"{Fore.YELLOW}Warnings:")
            else:
                lines.append("Warnings:")
            
            for warning in report.warnings:
                lines.append(f"  - {warning}")
            
            lines.append("")
        
        # Footer
        if self.use_colors:
            lines.append(f"{Fore.CYAN}{'-'*60}")
        else:
            lines.append("-"*60)
        
        return "\n".join(lines)
    
    def _colorize_number(self, number: int, color: str) -> str:
        """Colorize a number based on its value."""
        if not self.use_colors:
            return str(number)
        
        color_map = {
            'green': Fore.GREEN,
            'red': Fore.RED,
            'yellow': Fore.YELLOW
        }
        
        if number == 0:
            return str(number)
        
        return f"{color_map.get(color, '')}{number}{Style.RESET_ALL}"
    
    def _colorize_percentage(self, percentage: float) -> str:
        """Colorize a percentage based on its value."""
        if not self.use_colors:
            return f"{percentage:.1%}"
        
        if percentage >= 0.9:
            color = Fore.GREEN
        elif percentage >= 0.7:
            color = Fore.YELLOW
        else:
            color = Fore.RED
        
        return f"{color}{percentage:.1%}{Style.RESET_ALL}"
    
    def _get_status_color(self, status: ConversionStatus) -> str:
        """Get color for status."""
        if not self.use_colors:
            return ""
        
        color_map = {
            ConversionStatus.SUCCESS: Fore.GREEN,
            ConversionStatus.FAILED: Fore.RED,
            ConversionStatus.SKIPPED: Fore.YELLOW
        }
        
        return color_map.get(status, "")