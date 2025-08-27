"""Tests for interactive mode functionality."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

from fqcn_converter.cli.interactive import InteractiveMode
from fqcn_converter.core.converter import FQCNConverter
from fqcn_converter.core.validator import FQCNValidator


class TestInteractiveMode:
    """Test cases for InteractiveMode class."""
    
    @pytest.fixture
    def interactive_mode(self):
        """Create InteractiveMode instance for testing."""
        return InteractiveMode()
    
    @pytest.fixture
    def temp_yaml_file(self):
        """Create temporary YAML file for testing."""
        content = """---
- name: Test playbook
  hosts: all
  tasks:
    - name: Copy file
      copy:
        src: test.txt
        dest: /tmp/test.txt
    - name: Run command
      shell: echo "hello"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
    
    @pytest.fixture
    def temp_directory(self):
        """Create temporary directory with YAML files."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create test files
        (temp_dir / "playbook1.yml").write_text("""---
- name: Test playbook 1
  hosts: all
  tasks:
    - name: Copy file
      copy:
        src: test1.txt
        dest: /tmp/test1.txt
""")
        
        (temp_dir / "playbook2.yaml").write_text("""---
- name: Test playbook 2
  hosts: all
  tasks:
    - name: Run shell command
      shell: echo "test2"
""")
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_initialization(self, interactive_mode):
        """Test InteractiveMode initialization."""
        assert interactive_mode.converter is not None
        assert interactive_mode.validator is not None
        assert interactive_mode.changes_made == []
        assert interactive_mode.session_stats['files_processed'] == 0
        assert interactive_mode.session_stats['conversions_made'] == 0
        assert interactive_mode.session_stats['files_skipped'] == 0
        assert interactive_mode.session_stats['errors_encountered'] == 0
    
    def test_initialization_with_converter(self):
        """Test InteractiveMode initialization with custom converter."""
        custom_converter = Mock(spec=FQCNConverter)
        interactive_mode = InteractiveMode(custom_converter)
        
        assert interactive_mode.converter is custom_converter
        assert interactive_mode.validator is not None
    
    @patch('click.confirm')
    @patch('click.echo')
    def test_confirm_start_file(self, mock_echo, mock_confirm, interactive_mode, temp_yaml_file):
        """Test confirmation for single file."""
        mock_confirm.return_value = True
        
        result = interactive_mode._confirm_start(temp_yaml_file)
        
        assert result is True
        mock_confirm.assert_called_once()
        mock_echo.assert_called()
    
    @patch('click.confirm')
    @patch('click.echo')
    def test_confirm_start_directory(self, mock_echo, mock_confirm, interactive_mode, temp_directory):
        """Test confirmation for directory."""
        mock_confirm.return_value = True
        
        result = interactive_mode._confirm_start(temp_directory)
        
        assert result is True
        mock_confirm.assert_called_once()
        mock_echo.assert_called()
    
    @patch('click.confirm')
    def test_confirm_start_declined(self, mock_confirm, interactive_mode, temp_yaml_file):
        """Test when user declines to start."""
        mock_confirm.return_value = False
        
        result = interactive_mode._confirm_start(temp_yaml_file)
        
        assert result is False
    
    @patch('fqcn_converter.cli.interactive.InteractiveMode._confirm_start')
    @patch('fqcn_converter.cli.interactive.InteractiveMode._process_single_file_interactive')
    @patch('fqcn_converter.cli.interactive.InteractiveMode._print_welcome')
    @patch('fqcn_converter.cli.interactive.InteractiveMode._print_session_summary')
    def test_start_interactive_session_file(self, mock_summary, mock_welcome, 
                                          mock_process_file, mock_confirm,
                                          interactive_mode, temp_yaml_file):
        """Test starting interactive session with file."""
        mock_confirm.return_value = True
        mock_process_file.return_value = True
        
        result = interactive_mode.start_interactive_session(temp_yaml_file)
        
        assert result is True
        mock_welcome.assert_called_once()
        mock_confirm.assert_called_once_with(temp_yaml_file)
        mock_process_file.assert_called_once_with(temp_yaml_file)
        mock_summary.assert_called_once()
    
    @patch('fqcn_converter.cli.interactive.InteractiveMode._confirm_start')
    @patch('fqcn_converter.cli.interactive.InteractiveMode._process_directory_interactive')
    @patch('fqcn_converter.cli.interactive.InteractiveMode._print_welcome')
    @patch('fqcn_converter.cli.interactive.InteractiveMode._print_session_summary')
    def test_start_interactive_session_directory(self, mock_summary, mock_welcome,
                                               mock_process_dir, mock_confirm,
                                               interactive_mode, temp_directory):
        """Test starting interactive session with directory."""
        mock_confirm.return_value = True
        mock_process_dir.return_value = True
        
        result = interactive_mode.start_interactive_session(temp_directory)
        
        assert result is True
        mock_welcome.assert_called_once()
        mock_confirm.assert_called_once_with(temp_directory)
        mock_process_dir.assert_called_once_with(temp_directory)
        mock_summary.assert_called_once()
    
    @patch('fqcn_converter.cli.interactive.InteractiveMode._confirm_start')
    @patch('fqcn_converter.cli.interactive.InteractiveMode._print_welcome')
    @patch('fqcn_converter.cli.interactive.InteractiveMode._print_session_summary')
    def test_start_interactive_session_cancelled(self, mock_summary, mock_welcome,
                                                mock_confirm, interactive_mode, temp_yaml_file):
        """Test when user cancels interactive session."""
        mock_confirm.return_value = False
        
        result = interactive_mode.start_interactive_session(temp_yaml_file)
        
        assert result is False
        mock_welcome.assert_called_once()
        mock_confirm.assert_called_once_with(temp_yaml_file)
        mock_summary.assert_called_once()
    
    def test_start_interactive_session_nonexistent_path(self, interactive_mode):
        """Test with non-existent path."""
        nonexistent_path = Path("/nonexistent/path")
        
        with patch('fqcn_converter.cli.interactive.InteractiveMode._print_welcome'), \
             patch('fqcn_converter.cli.interactive.InteractiveMode._print_session_summary'), \
             patch('fqcn_converter.cli.interactive.InteractiveMode._print_error') as mock_error:
            
            result = interactive_mode.start_interactive_session(nonexistent_path)
            
            assert result is False
            mock_error.assert_called()
    
    @patch('fqcn_converter.cli.interactive.InteractiveMode._validate_file_interactive')
    @patch('fqcn_converter.cli.interactive.InteractiveMode._generate_preview')
    @patch('fqcn_converter.cli.interactive.InteractiveMode._show_preview_and_confirm')
    def test_process_single_file_no_conversions(self, mock_confirm, mock_preview, 
                                              mock_validate, interactive_mode, temp_yaml_file):
        """Test processing file with no conversions needed."""
        mock_validate.return_value = True
        mock_preview.return_value = None  # No conversions needed
        
        result = interactive_mode._process_single_file_interactive(temp_yaml_file)
        
        assert result is True
        mock_validate.assert_called_once_with(temp_yaml_file)
        mock_preview.assert_called_once_with(temp_yaml_file)
        mock_confirm.assert_not_called()
    
    @patch('fqcn_converter.cli.interactive.InteractiveMode._validate_file_interactive')
    @patch('fqcn_converter.cli.interactive.InteractiveMode._generate_preview')
    @patch('fqcn_converter.cli.interactive.InteractiveMode._show_preview_and_confirm')
    def test_process_single_file_user_skips(self, mock_confirm, mock_preview,
                                          mock_validate, interactive_mode, temp_yaml_file):
        """Test processing file when user skips conversion."""
        mock_validate.return_value = True
        mock_preview.return_value = {'conversions': [{'original': 'copy', 'fqcn': 'ansible.builtin.copy'}]}
        mock_confirm.return_value = False
        
        result = interactive_mode._process_single_file_interactive(temp_yaml_file)
        
        assert result is True
        assert interactive_mode.session_stats['files_skipped'] == 1
    
    @patch('fqcn_converter.cli.interactive.InteractiveMode._validate_file_interactive')
    @patch('fqcn_converter.cli.interactive.InteractiveMode._generate_preview')
    @patch('fqcn_converter.cli.interactive.InteractiveMode._show_preview_and_confirm')
    def test_process_single_file_successful_conversion(self, mock_confirm, mock_preview,
                                                     mock_validate, interactive_mode, temp_yaml_file):
        """Test successful file conversion."""
        mock_validate.return_value = True
        mock_preview.return_value = {'conversions': [{'original': 'copy', 'fqcn': 'ansible.builtin.copy'}]}
        mock_confirm.return_value = True
        
        # Mock converter result
        mock_result = Mock()
        mock_result.success = True
        mock_result.conversions = [{'original': 'copy', 'fqcn': 'ansible.builtin.copy'}]
        interactive_mode.converter.convert_file = Mock(return_value=mock_result)
        
        result = interactive_mode._process_single_file_interactive(temp_yaml_file)
        
        assert result is True
        assert interactive_mode.session_stats['files_processed'] == 1
        assert interactive_mode.session_stats['conversions_made'] == 1
        assert len(interactive_mode.changes_made) == 1
    
    def test_process_directory_no_yaml_files(self, interactive_mode):
        """Test processing directory with no YAML files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create non-YAML file
            (temp_path / "test.txt").write_text("not yaml")
            
            with patch('fqcn_converter.cli.interactive.InteractiveMode._print_warning') as mock_warning:
                result = interactive_mode._process_directory_interactive(temp_path)
                
                assert result is True
                mock_warning.assert_called_with("No YAML files found in directory.")
    
    @patch('fqcn_converter.cli.interactive.InteractiveMode._process_single_file_interactive')
    def test_process_directory_with_files(self, mock_process_file, interactive_mode, temp_directory):
        """Test processing directory with YAML files."""
        mock_process_file.return_value = True
        
        result = interactive_mode._process_directory_interactive(temp_directory)
        
        assert result is True
        # Should be called twice (for playbook1.yml and playbook2.yaml)
        assert mock_process_file.call_count == 2
    
    def test_validate_file_interactive_valid(self, interactive_mode, temp_yaml_file):
        """Test file validation when file is valid."""
        mock_result = Mock()
        mock_result.is_valid = True
        interactive_mode.validator.validate_file = Mock(return_value=mock_result)
        
        result = interactive_mode._validate_file_interactive(temp_yaml_file)
        
        assert result is True
    
    @patch('click.confirm')
    def test_validate_file_interactive_invalid_continue(self, mock_confirm, interactive_mode, temp_yaml_file):
        """Test file validation when file is invalid but user continues."""
        mock_result = Mock()
        mock_result.is_valid = False
        mock_result.issues = ["Issue 1", "Issue 2"]
        interactive_mode.validator.validate_file = Mock(return_value=mock_result)
        mock_confirm.return_value = True
        
        result = interactive_mode._validate_file_interactive(temp_yaml_file)
        
        assert result is True
        mock_confirm.assert_called_once()
    
    @patch('click.confirm')
    def test_validate_file_interactive_invalid_stop(self, mock_confirm, interactive_mode, temp_yaml_file):
        """Test file validation when file is invalid and user stops."""
        mock_result = Mock()
        mock_result.is_valid = False
        mock_result.issues = ["Issue 1", "Issue 2"]
        interactive_mode.validator.validate_file = Mock(return_value=mock_result)
        mock_confirm.return_value = False
        
        result = interactive_mode._validate_file_interactive(temp_yaml_file)
        
        assert result is False
    
    def test_generate_preview_successful(self, interactive_mode, temp_yaml_file):
        """Test generating preview with conversions."""
        mock_result = Mock()
        mock_result.success = True
        mock_result.conversions = [{'original': 'copy', 'fqcn': 'ansible.builtin.copy'}]
        mock_result.converted_content = "converted content"
        
        interactive_mode.converter.convert_file = Mock(return_value=mock_result)
        
        preview = interactive_mode._generate_preview(temp_yaml_file)
        
        assert preview is not None
        assert 'conversions' in preview
        assert 'converted_content' in preview
        assert len(preview['conversions']) == 1
    
    def test_generate_preview_no_conversions(self, interactive_mode, temp_yaml_file):
        """Test generating preview with no conversions."""
        mock_result = Mock()
        mock_result.success = True
        mock_result.conversions = []
        
        interactive_mode.converter.convert_file = Mock(return_value=mock_result)
        
        preview = interactive_mode._generate_preview(temp_yaml_file)
        
        assert preview is None
    
    @patch('click.confirm')
    @patch('click.echo')
    def test_show_preview_and_confirm_accept(self, mock_echo, mock_confirm, interactive_mode, temp_yaml_file):
        """Test showing preview and user accepts."""
        preview_data = {
            'conversions': [
                {'original': 'copy', 'fqcn': 'ansible.builtin.copy', 'line': 5},
                {'original': 'shell', 'fqcn': 'ansible.builtin.shell', 'line': 8}
            ],
            'original_content': 'original',
            'converted_content': 'converted'
        }
        
        mock_confirm.side_effect = [False, True]  # No detailed diff, yes to apply
        
        result = interactive_mode._show_preview_and_confirm(temp_yaml_file, preview_data)
        
        assert result is True
        assert mock_confirm.call_count == 2
    
    @patch('click.confirm')
    @patch('click.echo')
    def test_show_preview_and_confirm_reject(self, mock_echo, mock_confirm, interactive_mode, temp_yaml_file):
        """Test showing preview and user rejects."""
        preview_data = {
            'conversions': [{'original': 'copy', 'fqcn': 'ansible.builtin.copy'}],
            'original_content': 'original',
            'converted_content': 'converted'
        }
        
        mock_confirm.side_effect = [False, False]  # No detailed diff, no to apply
        
        result = interactive_mode._show_preview_and_confirm(temp_yaml_file, preview_data)
        
        assert result is False
    
    @patch('click.confirm')
    @patch('click.echo')
    def test_show_preview_with_detailed_diff(self, mock_echo, mock_confirm, interactive_mode, temp_yaml_file):
        """Test showing preview with detailed diff."""
        preview_data = {
            'conversions': [{'original': 'copy', 'fqcn': 'ansible.builtin.copy'}],
            'original_content': 'line1\nline2\nline3',
            'converted_content': 'line1\nmodified line2\nline3'
        }
        
        mock_confirm.side_effect = [True, True]  # Yes to detailed diff, yes to apply
        
        result = interactive_mode._show_preview_and_confirm(temp_yaml_file, preview_data)
        
        assert result is True
        assert mock_confirm.call_count == 2
    
    def test_session_stats_tracking(self, interactive_mode):
        """Test that session statistics are properly tracked."""
        # Initial state
        assert interactive_mode.session_stats['files_processed'] == 0
        assert interactive_mode.session_stats['conversions_made'] == 0
        assert interactive_mode.session_stats['files_skipped'] == 0
        assert interactive_mode.session_stats['errors_encountered'] == 0
        
        # Simulate processing files
        interactive_mode.session_stats['files_processed'] = 3
        interactive_mode.session_stats['conversions_made'] = 5
        interactive_mode.session_stats['files_skipped'] = 1
        interactive_mode.session_stats['errors_encountered'] = 1
        
        assert interactive_mode.session_stats['files_processed'] == 3
        assert interactive_mode.session_stats['conversions_made'] == 5
        assert interactive_mode.session_stats['files_skipped'] == 1
        assert interactive_mode.session_stats['errors_encountered'] == 1
    
    @patch('click.echo')
    def test_print_methods(self, mock_echo, interactive_mode):
        """Test various print methods."""
        interactive_mode._print_success("Success message")
        interactive_mode._print_info("Info message")
        interactive_mode._print_warning("Warning message")
        interactive_mode._print_error("Error message")
        
        assert mock_echo.call_count == 4
    
    @patch('click.echo')
    def test_print_session_summary(self, mock_echo, interactive_mode):
        """Test session summary printing."""
        # Set up some stats
        interactive_mode.session_stats = {
            'files_processed': 5,
            'conversions_made': 10,
            'files_skipped': 2,
            'errors_encountered': 1
        }
        
        # Add some changes
        mock_result = Mock()
        mock_result.conversions = [{'original': 'copy', 'fqcn': 'ansible.builtin.copy'}]
        interactive_mode.changes_made = [(Path("test.yml"), mock_result)]
        
        interactive_mode._print_session_summary()
        
        # Should print multiple lines
        assert mock_echo.call_count > 5