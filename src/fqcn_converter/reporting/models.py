"""Data models for enhanced reporting system."""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from enum import Enum


class ConversionStatus(Enum):
    """Status of a conversion operation."""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    PARTIAL = "partial"


class ReportFormat(Enum):
    """Available report output formats."""
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"
    CONSOLE = "console"


@dataclass
class FileChangeRecord:
    """Record of changes made to a single file."""
    
    file_path: Path
    status: ConversionStatus
    conversions_made: int
    conversions_attempted: int
    processing_time: float
    file_size_bytes: int
    backup_created: bool
    error_message: Optional[str] = None
    warnings: List[str] = None
    conversions: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.warnings is None:
            self.warnings = []
        if self.conversions is None:
            self.conversions = []
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate for this file."""
        if self.conversions_attempted == 0:
            return 1.0
        return self.conversions_made / self.conversions_attempted
    
    @property
    def has_errors(self) -> bool:
        """Check if file has errors."""
        return self.error_message is not None
    
    @property
    def has_warnings(self) -> bool:
        """Check if file has warnings."""
        return len(self.warnings) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['file_path'] = str(self.file_path)
        data['status'] = self.status.value
        return data


@dataclass
class ErrorReport:
    """Detailed error information."""
    
    error_type: str
    error_message: str
    file_path: Optional[Path] = None
    line_number: Optional[int] = None
    context: Optional[str] = None
    stack_trace: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['file_path'] = str(self.file_path) if self.file_path else None
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class ConversionStatistics:
    """Comprehensive statistics for conversion operations."""
    
    total_files_processed: int = 0
    total_files_successful: int = 0
    total_files_failed: int = 0
    total_files_skipped: int = 0
    total_conversions_made: int = 0
    total_conversions_attempted: int = 0
    total_processing_time: float = 0.0
    total_bytes_processed: int = 0
    average_processing_time: float = 0.0
    average_file_size: float = 0.0
    peak_memory_usage: Optional[int] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate overall success rate."""
        if self.total_files_processed == 0:
            return 0.0
        return self.total_files_successful / self.total_files_processed
    
    @property
    def conversion_efficiency(self) -> float:
        """Calculate conversion efficiency."""
        if self.total_conversions_attempted == 0:
            return 1.0
        return self.total_conversions_made / self.total_conversions_attempted
    
    @property
    def processing_speed(self) -> float:
        """Calculate files per second."""
        if self.total_processing_time == 0:
            return 0.0
        return self.total_files_processed / self.total_processing_time
    
    def update_from_file_record(self, record: FileChangeRecord) -> None:
        """Update statistics from a file change record."""
        self.total_files_processed += 1
        self.total_conversions_made += record.conversions_made
        self.total_conversions_attempted += record.conversions_attempted
        self.total_processing_time += record.processing_time
        self.total_bytes_processed += record.file_size_bytes
        
        if record.status == ConversionStatus.SUCCESS:
            self.total_files_successful += 1
        elif record.status == ConversionStatus.FAILED:
            self.total_files_failed += 1
        elif record.status == ConversionStatus.SKIPPED:
            self.total_files_skipped += 1
        
        # Update averages
        if self.total_files_processed > 0:
            self.average_processing_time = self.total_processing_time / self.total_files_processed
            self.average_file_size = self.total_bytes_processed / self.total_files_processed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class ConversionReport:
    """Comprehensive conversion report."""
    
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    target_path: Optional[Path] = None
    configuration: Dict[str, Any] = None
    statistics: ConversionStatistics = None
    file_records: List[FileChangeRecord] = None
    errors: List[ErrorReport] = None
    warnings: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.configuration is None:
            self.configuration = {}
        if self.statistics is None:
            self.statistics = ConversionStatistics()
        if self.file_records is None:
            self.file_records = []
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate session duration in seconds."""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def is_completed(self) -> bool:
        """Check if report is completed."""
        return self.end_time is not None
    
    @property
    def has_errors(self) -> bool:
        """Check if report has errors."""
        return len(self.errors) > 0 or any(record.has_errors for record in self.file_records)
    
    @property
    def has_warnings(self) -> bool:
        """Check if report has warnings."""
        return len(self.warnings) > 0 or any(record.has_warnings for record in self.file_records)
    
    def add_file_record(self, record: FileChangeRecord) -> None:
        """Add a file change record and update statistics."""
        self.file_records.append(record)
        self.statistics.update_from_file_record(record)
    
    def add_error(self, error: ErrorReport) -> None:
        """Add an error report."""
        self.errors.append(error)
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
    
    def finalize(self) -> None:
        """Finalize the report by setting end time."""
        self.end_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'target_path': str(self.target_path) if self.target_path else None,
            'configuration': self.configuration,
            'statistics': self.statistics.to_dict(),
            'file_records': [record.to_dict() for record in self.file_records],
            'errors': [error.to_dict() for error in self.errors],
            'warnings': self.warnings,
            'metadata': self.metadata,
            'duration': self.duration,
            'is_completed': self.is_completed,
            'has_errors': self.has_errors,
            'has_warnings': self.has_warnings
        }
        return data
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversionReport':
        """Create report from dictionary."""
        # Convert string timestamps back to datetime
        start_time = datetime.fromisoformat(data['start_time'])
        end_time = datetime.fromisoformat(data['end_time']) if data['end_time'] else None
        
        # Convert path strings back to Path objects
        target_path = Path(data['target_path']) if data['target_path'] else None
        
        # Reconstruct statistics
        statistics = ConversionStatistics(**data['statistics'])
        
        # Reconstruct file records
        file_records = []
        for record_data in data['file_records']:
            record_data['file_path'] = Path(record_data['file_path'])
            record_data['status'] = ConversionStatus(record_data['status'])
            file_records.append(FileChangeRecord(**record_data))
        
        # Reconstruct errors
        errors = []
        for error_data in data['errors']:
            error_data['file_path'] = Path(error_data['file_path']) if error_data['file_path'] else None
            error_data['timestamp'] = datetime.fromisoformat(error_data['timestamp'])
            errors.append(ErrorReport(**error_data))
        
        return cls(
            session_id=data['session_id'],
            start_time=start_time,
            end_time=end_time,
            target_path=target_path,
            configuration=data['configuration'],
            statistics=statistics,
            file_records=file_records,
            errors=errors,
            warnings=data['warnings'],
            metadata=data['metadata']
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ConversionReport':
        """Create report from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)