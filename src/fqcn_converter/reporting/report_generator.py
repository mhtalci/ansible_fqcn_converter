"""Report generator for FQCN conversion operations."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union

from .models import ConversionReport, FileChangeRecord, ConversionStatus
from .formatters import JSONReportFormatter, ConsoleReportFormatter
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    """Generates comprehensive conversion reports."""
    
    def __init__(self, session_id: Optional[str] = None):
        """Initialize report generator."""
        self.session_id = session_id or str(uuid.uuid4())
        self.report = ConversionReport(
            session_id=self.session_id,
            start_time=datetime.now()
        )
        self.formatters = {
            'json': JSONReportFormatter(),
            'console': ConsoleReportFormatter()
        }
    
    def start_session(self, target_path: Path, configuration: Dict[str, Any] = None) -> None:
        """Start a new conversion session."""
        self.report.target_path = target_path
        logger.info(f"Started conversion session {self.session_id} for {target_path}")
    
    def add_file_result(self, file_path: Path, result: Any, processing_time: float) -> None:
        """Add a file conversion result to the report."""
        try:
            # Get file size
            file_size = file_path.stat().st_size if file_path.exists() else 0
            
            # Determine status
            if hasattr(result, 'success') and result.success:
                status = ConversionStatus.SUCCESS
                conversions_made = getattr(result, 'changes_made', 0)
                conversions_attempted = conversions_made
                error_message = None
            elif hasattr(result, 'errors') and result.errors:
                status = ConversionStatus.FAILED
                conversions_made = 0
                conversions_attempted = getattr(result, 'changes_made', 0)
                error_message = '; '.join(result.errors)
            else:
                status = ConversionStatus.SKIPPED
                conversions_made = 0
                conversions_attempted = 0
                error_message = None
            
            # Create file record
            record = FileChangeRecord(
                file_path=file_path,
                status=status,
                conversions_made=conversions_made,
                conversions_attempted=conversions_attempted,
                processing_time=processing_time,
                file_size_bytes=file_size,
                backup_created=getattr(result, 'backup_created', False),
                error_message=error_message,
                warnings=getattr(result, 'warnings', []),
                conversions=[]  # We don't have detailed conversion info in current result
            )
            
            self.report.add_file_record(record)
            logger.debug(f"Added file result for {file_path}: {status.value}")
            
        except Exception as e:
            logger.exception(f"Error adding file result for {file_path}")
            self.add_error(f"Failed to add file result: {e}")
    
    def add_error(self, error: str) -> None:
        """Add an error to the report."""
        self.report.add_error(error)
        logger.error(f"Added error to report: {error}")
    
    def add_warning(self, warning: str) -> None:
        """Add a warning to the report."""
        self.report.add_warning(warning)
        logger.warning(f"Added warning to report: {warning}")
    
    def finalize_session(self) -> ConversionReport:
        """Finalize the conversion session and return the report."""
        self.report.finalize()
        
        logger.info(f"Finalized conversion session {self.session_id}")
        logger.info(f"Session summary: {self.report.statistics.total_files_processed} files, "
                   f"{self.report.statistics.success_rate:.1%} success rate, "
                   f"{self.report.statistics.total_conversions_made} conversions")
        
        return self.report
    
    def generate_report(self, format_type: str, output_path: Optional[Path] = None) -> str:
        """Generate a formatted report."""
        try:
            # Get formatter
            formatter = self.formatters.get(format_type)
            if not formatter:
                raise ValueError(f"Unsupported report format: {format_type}")
            
            # Generate report
            formatted_report = formatter.format_report(self.report)
            
            # Save to file if path provided
            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(formatted_report, encoding='utf-8')
                logger.info(f"Saved {format_type} report to {output_path}")
            
            return formatted_report
            
        except Exception as e:
            logger.exception(f"Error generating {format_type} report")
            raise
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for the current session."""
        stats = self.report.statistics
        
        return {
            'session_id': self.session_id,
            'files_processed': stats.total_files_processed,
            'files_successful': stats.total_files_successful,
            'files_failed': stats.total_files_failed,
            'success_rate': stats.success_rate,
            'conversions_made': stats.total_conversions_made,
            'conversion_efficiency': stats.conversion_efficiency,
            'processing_speed': stats.processing_speed,
            'total_time': stats.total_processing_time,
            'has_errors': self.report.has_errors,
            'has_warnings': self.report.has_warnings,
            'is_completed': self.report.is_completed
        }