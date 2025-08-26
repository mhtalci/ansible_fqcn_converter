#!/usr/bin/env python3
"""
Test module for YAML handler utilities.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from fqcn_converter.utils.yaml_handler import (
    safe_load,
    safe_dump,
    load_yaml_file,
    save_yaml_file
)


class TestYAMLHandler:
    """Test YAML handler utilities."""

    def test_safe_load_valid_yaml(self):
        """Test safe_load with valid YAML content."""
        yaml_content = """
        name: test
        items:
          - item1
          - item2
        config:
          enabled: true
          count: 42
        """
        
        result = safe_load(yaml_content)
        
        assert isinstance(result, dict)
        assert result['name'] == 'test'
        assert result['items'] == ['item1', 'item2']
        assert result['config']['enabled'] is True
        assert result['config']['count'] == 42

    def test_safe_load_empty_content(self):
        """Test safe_load with empty content."""
        result = safe_load("")
        assert result is None

    def test_safe_load_none_content(self):
        """Test safe_load with None content."""
        result = safe_load(None)
        assert result is None

    def test_safe_load_invalid_yaml(self):
        """Test safe_load with invalid YAML content."""
        invalid_yaml = """
        name: test
        items: [
          - item1
          - item2
        # Missing closing bracket
        """
        
        with pytest.raises(Exception):  # Should raise YAML parsing error
            safe_load(invalid_yaml)

    def test_safe_dump_dict(self):
        """Test safe_dump with dictionary data."""
        data = {
            'name': 'test',
            'items': ['item1', 'item2'],
            'config': {
                'enabled': True,
                'count': 42
            }
        }
        
        result = safe_dump(data)
        
        assert isinstance(result, str)
        assert 'name: test' in result
        assert 'item1' in result
        assert 'item2' in result
        assert 'enabled: true' in result
        assert 'count: 42' in result

    def test_safe_dump_list(self):
        """Test safe_dump with list data."""
        data = ['item1', 'item2', 'item3']
        
        result = safe_dump(data)
        
        assert isinstance(result, str)
        assert 'item1' in result
        assert 'item2' in result
        assert 'item3' in result

    def test_safe_dump_with_kwargs(self):
        """Test safe_dump with additional kwargs."""
        data = {'name': 'test', 'value': 42}
        
        result = safe_dump(data, default_flow_style=False, indent=2)
        
        assert isinstance(result, str)
        assert 'name: test' in result
        assert 'value: 42' in result

    def test_load_yaml_file_success(self):
        """Test load_yaml_file with valid file."""
        yaml_content = """
        name: test_file
        version: 1.0
        features:
          - feature1
          - feature2
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            result = load_yaml_file(temp_path)
            
            assert isinstance(result, dict)
            assert result['name'] == 'test_file'
            assert result['version'] == 1.0
            assert result['features'] == ['feature1', 'feature2']
        finally:
            os.unlink(temp_path)

    def test_load_yaml_file_with_pathlib(self):
        """Test load_yaml_file with pathlib.Path object."""
        yaml_content = "name: pathlib_test\nvalue: 123"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)
        
        try:
            result = load_yaml_file(temp_path)
            
            assert isinstance(result, dict)
            assert result['name'] == 'pathlib_test'
            assert result['value'] == 123
        finally:
            os.unlink(temp_path)

    def test_load_yaml_file_not_found(self):
        """Test load_yaml_file with non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_yaml_file('/nonexistent/file.yml')

    def test_save_yaml_file_success(self):
        """Test save_yaml_file with valid data."""
        data = {
            'name': 'saved_test',
            'items': ['a', 'b', 'c'],
            'config': {'debug': True}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            temp_path = f.name
        
        try:
            save_yaml_file(data, temp_path)
            
            # Verify file was created and contains expected content
            assert os.path.exists(temp_path)
            
            # Load it back and verify
            loaded_data = load_yaml_file(temp_path)
            assert loaded_data == data
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_yaml_file_with_pathlib(self):
        """Test save_yaml_file with pathlib.Path object."""
        data = {'pathlib_save': True, 'number': 456}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            save_yaml_file(data, temp_path)
            
            # Verify file was created
            assert temp_path.exists()
            
            # Load it back and verify
            loaded_data = load_yaml_file(temp_path)
            assert loaded_data == data
        finally:
            if temp_path.exists():
                os.unlink(temp_path)

    def test_roundtrip_yaml_processing(self):
        """Test complete roundtrip: data -> YAML string -> data."""
        original_data = {
            'name': 'roundtrip_test',
            'version': '2.1.0',
            'features': ['auth', 'logging', 'metrics'],
            'config': {
                'timeout': 30,
                'retries': 3,
                'debug': False
            }
        }
        
        # Convert to YAML string
        yaml_string = safe_dump(original_data)
        
        # Convert back to data
        loaded_data = safe_load(yaml_string)
        
        # Should be identical
        assert loaded_data == original_data

    def test_yaml_handler_module_imports(self):
        """Test that all YAML handler functions can be imported."""
        from fqcn_converter.utils.yaml_handler import (
            safe_load, safe_dump, load_yaml_file, save_yaml_file
        )
        
        assert callable(safe_load)
        assert callable(safe_dump)
        assert callable(load_yaml_file)
        assert callable(save_yaml_file)