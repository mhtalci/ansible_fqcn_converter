"""
Unit tests for ConfigurationManager class.

Comprehensive test suite covering configuration loading, merging,
and validation with various config scenarios.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from fqcn_converter.config.manager import (
    ConfigurationManager,
    ConversionSettings,
    ConfigurationSchema
)
from fqcn_converter.exceptions import ConfigurationError


class TestConfigurationManager:
    """Test cases for ConfigurationManager class."""
    
    @pytest.fixture
    def sample_config_data(self):
        """Sample configuration data for testing."""
        return {
            'ansible_builtin': {
                'copy': 'ansible.builtin.copy',
                'file': 'ansible.builtin.file',
                'service': 'ansible.builtin.service',
            },
            'community_general': {
                'docker_container': 'community.docker.docker_container',
                'mysql_user': 'community.mysql.mysql_user',
            },
            'backup_config': {
                'create_backup': True,
                'backup_suffix': '.fqcn_backup',
                'backup_directory': '.fqcn_backups'
            }
        }
    
    @pytest.fixture
    def config_manager(self):
        """Create ConfigurationManager instance."""
        with patch.object(ConfigurationManager, '_find_default_config', return_value=None):
            return ConfigurationManager()
    
    def test_init_with_default_config(self):
        """Test initialization with default config found."""
        mock_path = Path("/mock/config.yml")
        with patch.object(ConfigurationManager, '_find_default_config', return_value=mock_path):
            manager = ConfigurationManager()
            assert manager._default_config_path == mock_path
    
    def test_init_without_default_config(self):
        """Test initialization without default config."""
        with patch.object(ConfigurationManager, '_find_default_config', return_value=None):
            manager = ConfigurationManager()
            assert manager._default_config_path is None
    
    def test_load_default_mappings_success(self, config_manager, sample_config_data, tmp_path):
        """Test successful loading of default mappings."""
        config_file = tmp_path / "config.yml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config_data, f)
        
        config_manager._default_config_path = config_file
        
        mappings = config_manager.load_default_mappings()
        
        expected_mappings = {
            'copy': 'ansible.builtin.copy',
            'file': 'ansible.builtin.file',
            'service': 'ansible.builtin.service',
            'docker_container': 'community.docker.docker_container',
            'mysql_user': 'community.mysql.mysql_user',
        }
        
        assert mappings == expected_mappings
    
    def test_load_default_mappings_file_not_found(self, config_manager):
        """Test loading default mappings when file not found."""
        config_manager._default_config_path = Path("/non/existent/config.yml")
        
        mappings = config_manager.load_default_mappings()
        
        # Should return minimal built-in mappings
        assert 'copy' in mappings
        assert 'file' in mappings
        assert 'service' in mappings
        assert mappings['copy'] == 'ansible.builtin.copy'
    
    def test_load_default_mappings_empty_file(self, config_manager, tmp_path):
        """Test loading default mappings from empty file."""
        config_file = tmp_path / "empty_config.yml"
        config_file.write_text("")
        
        config_manager._default_config_path = config_file
        
        mappings = config_manager.load_default_mappings()
        
        # Should return minimal built-in mappings
        assert 'copy' in mappings
        assert mappings['copy'] == 'ansible.builtin.copy'
    
    def test_load_default_mappings_invalid_yaml(self, config_manager, tmp_path):
        """Test loading default mappings with invalid YAML."""
        config_file = tmp_path / "invalid_config.yml"
        config_file.write_text("---\ninvalid: [\n")
        
        config_manager._default_config_path = config_file
        
        with pytest.raises(ConfigurationError) as exc_info:
            config_manager.load_default_mappings()
        
        assert "Failed to parse default configuration YAML" in str(exc_info.value)
    
    def test_load_custom_mappings_success(self, config_manager, sample_config_data, tmp_path):
        """Test successful loading of custom mappings."""
        config_file = tmp_path / "custom_config.yml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config_data, f)
        
        mappings = config_manager.load_custom_mappings(config_file)
        
        expected_mappings = {
            'copy': 'ansible.builtin.copy',
            'file': 'ansible.builtin.file',
            'service': 'ansible.builtin.service',
            'docker_container': 'community.docker.docker_container',
            'mysql_user': 'community.mysql.mysql_user',
        }
        
        assert mappings == expected_mappings
    
    def test_load_custom_mappings_file_not_found(self, config_manager):
        """Test loading custom mappings when file not found."""
        non_existent_file = Path("/non/existent/config.yml")
        
        with pytest.raises(ConfigurationError) as exc_info:
            config_manager.load_custom_mappings(non_existent_file)
        
        assert "Custom configuration file not found" in str(exc_info.value)
    
    def test_load_custom_mappings_empty_file(self, config_manager, tmp_path):
        """Test loading custom mappings from empty file."""
        config_file = tmp_path / "empty_config.yml"
        config_file.write_text("")
        
        mappings = config_manager.load_custom_mappings(config_file)
        
        assert mappings == {}
    
    def test_load_custom_mappings_invalid_yaml(self, config_manager, tmp_path):
        """Test loading custom mappings with invalid YAML."""
        config_file = tmp_path / "invalid_config.yml"
        config_file.write_text("---\ninvalid: [\n")
        
        with pytest.raises(ConfigurationError) as exc_info:
            config_manager.load_custom_mappings(config_file)
        
        assert "Failed to parse custom configuration YAML" in str(exc_info.value)
    
    def test_load_custom_mappings_simple_format(self, config_manager, tmp_path):
        """Test loading custom mappings with simple format."""
        config_data = {
            'mappings': {
                'custom_module': 'custom.collection.module',
                'another_module': 'another.collection.module'
            }
        }
        
        config_file = tmp_path / "simple_config.yml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        mappings = config_manager.load_custom_mappings(config_file)
        
        expected_mappings = {
            'custom_module': 'custom.collection.module',
            'another_module': 'another.collection.module'
        }
        
        assert mappings == expected_mappings
    
    def test_merge_mappings_simple(self, config_manager):
        """Test merging simple mapping dictionaries."""
        mapping1 = {'module1': 'collection1.module1', 'module2': 'collection1.module2'}
        mapping2 = {'module3': 'collection2.module3', 'module4': 'collection2.module4'}
        
        merged = config_manager.merge_mappings(mapping1, mapping2)
        
        expected = {
            'module1': 'collection1.module1',
            'module2': 'collection1.module2',
            'module3': 'collection2.module3',
            'module4': 'collection2.module4'
        }
        
        assert merged == expected
    
    def test_merge_mappings_with_conflicts(self, config_manager):
        """Test merging mappings with conflicts (later takes precedence)."""
        mapping1 = {'module1': 'collection1.module1', 'module2': 'collection1.module2'}
        mapping2 = {'module1': 'collection2.module1', 'module3': 'collection2.module3'}
        
        merged = config_manager.merge_mappings(mapping1, mapping2)
        
        expected = {
            'module1': 'collection2.module1',  # Later mapping takes precedence
            'module2': 'collection1.module2',
            'module3': 'collection2.module3'
        }
        
        assert merged == expected
    
    def test_merge_mappings_empty_input(self, config_manager):
        """Test merging with empty input."""
        # No mappings
        merged = config_manager.merge_mappings()
        assert merged == {}
        
        # Empty mapping
        merged = config_manager.merge_mappings({})
        assert merged == {}
    
    def test_merge_mappings_invalid_input(self, config_manager):
        """Test merging with invalid input types."""
        mapping1 = {'module1': 'collection1.module1'}
        invalid_mapping = "not a dict"
        
        merged = config_manager.merge_mappings(mapping1, invalid_mapping)
        
        # Should skip invalid mapping and continue with valid ones
        assert merged == mapping1
    
    def test_load_settings_success(self, config_manager, tmp_path):
        """Test successful loading of settings."""
        config_data = {
            'settings': {
                'backup_files': False,
                'backup_suffix': '.custom_backup',
                'validation_level': 'strict'
            }
        }
        
        config_file = tmp_path / "settings_config.yml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        settings = config_manager.load_settings(config_file)
        
        assert settings.backup_files is False
        assert settings.backup_suffix == '.custom_backup'
        assert settings.validation_level == 'strict'
    
    def test_load_settings_backup_config_format(self, config_manager, tmp_path):
        """Test loading settings from backup_config format."""
        config_data = {
            'backup_config': {
                'create_backup': False,
                'backup_suffix': '.old_backup',
                'backup_directory': '.old_backups'
            }
        }
        
        config_file = tmp_path / "backup_config.yml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        settings = config_manager.load_settings(config_file)
        
        assert settings.backup_files is False
        assert settings.backup_suffix == '.old_backup'
        assert settings.backup_directory == '.old_backups'
    
    def test_load_settings_file_not_found(self, config_manager):
        """Test loading settings when file not found."""
        settings = config_manager.load_settings("/non/existent/config.yml")
        
        # Should return default settings
        assert isinstance(settings, ConversionSettings)
        assert settings.backup_files is True  # Default value
    
    def test_load_settings_with_defaults(self, config_manager, tmp_path):
        """Test loading settings with default config."""
        # Create default config
        default_config = {
            'settings': {
                'backup_files': False,
                'validation_level': 'minimal'
            }
        }
        
        default_file = tmp_path / "default_config.yml"
        with open(default_file, 'w') as f:
            yaml.dump(default_config, f)
        
        config_manager._default_config_path = default_file
        
        # Create custom config that overrides some settings
        custom_config = {
            'settings': {
                'backup_files': True,
                'backup_suffix': '.custom'
            }
        }
        
        custom_file = tmp_path / "custom_config.yml"
        with open(custom_file, 'w') as f:
            yaml.dump(custom_config, f)
        
        settings = config_manager.load_settings(custom_file)
        
        # Custom settings should override defaults
        assert settings.backup_files is True  # From custom
        assert settings.backup_suffix == '.custom'  # From custom
        assert settings.validation_level == 'standard'  # Uses built-in default since not in custom config
    
    def test_validate_configuration_valid(self, config_manager, sample_config_data):
        """Test validation of valid configuration."""
        is_valid = config_manager.validate_configuration(sample_config_data)
        
        assert is_valid is True
    
    def test_validate_configuration_invalid_structure(self, config_manager):
        """Test validation of invalid configuration structure."""
        invalid_config = "not a dictionary"
        
        is_valid = config_manager.validate_configuration(invalid_config)
        
        assert is_valid is False
    
    def test_validate_configuration_invalid_section(self, config_manager):
        """Test validation with invalid section structure."""
        invalid_config = {
            'ansible_builtin': "not a dictionary"
        }
        
        is_valid = config_manager.validate_configuration(invalid_config)
        
        assert is_valid is False
    
    def test_validate_configuration_invalid_fqcn(self, config_manager):
        """Test validation with invalid FQCN format."""
        invalid_config = {
            'ansible_builtin': {
                'copy': 'invalid_fqcn'  # Missing proper namespace.collection.module format
            }
        }
        
        is_valid = config_manager.validate_configuration(invalid_config)
        
        # Should still be valid but log warning
        assert is_valid is True
    
    def test_find_default_config_method(self):
        """Test the _find_default_config method."""
        manager = ConfigurationManager()
        
        # Test with mocked file existence
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.side_effect = lambda: True  # First path exists
            
            result = manager._find_default_config()
            
            assert result is not None
            assert isinstance(result, Path)
    
    def test_get_minimal_builtin_mappings(self, config_manager):
        """Test the _get_minimal_builtin_mappings method."""
        mappings = config_manager._get_minimal_builtin_mappings()
        
        # Should contain essential modules
        essential_modules = ['copy', 'file', 'service', 'user', 'group', 'package']
        
        for module in essential_modules:
            assert module in mappings
            assert mappings[module].startswith('ansible.builtin.')
    
    def test_extract_mappings_from_config_complex_format(self, config_manager, sample_config_data):
        """Test extracting mappings from complex configuration format."""
        mappings = config_manager._extract_mappings_from_config(sample_config_data)
        
        expected_mappings = {
            'copy': 'ansible.builtin.copy',
            'file': 'ansible.builtin.file',
            'service': 'ansible.builtin.service',
            'docker_container': 'community.docker.docker_container',
            'mysql_user': 'community.mysql.mysql_user',
        }
        
        assert mappings == expected_mappings
    
    def test_extract_mappings_from_config_simple_format(self, config_manager):
        """Test extracting mappings from simple configuration format."""
        config_data = {
            'mappings': {
                'module1': 'collection1.module1',
                'module2': 'collection2.module2'
            }
        }
        
        mappings = config_manager._extract_mappings_from_config(config_data)
        
        expected_mappings = {
            'module1': 'collection1.module1',
            'module2': 'collection2.module2'
        }
        
        assert mappings == expected_mappings
    
    def test_is_valid_fqcn_method(self, config_manager):
        """Test the _is_valid_fqcn method."""
        # Valid FQCNs
        assert config_manager._is_valid_fqcn('ansible.builtin.copy') is True
        assert config_manager._is_valid_fqcn('community.general.docker_container') is True
        assert config_manager._is_valid_fqcn('namespace.collection.module') is True
        
        # Invalid FQCNs
        assert config_manager._is_valid_fqcn('copy') is False  # Too short
        assert config_manager._is_valid_fqcn('ansible.copy') is False  # Too short
        assert config_manager._is_valid_fqcn('ansible.builtin.') is False  # Empty module
        assert config_manager._is_valid_fqcn('ansible..copy') is False  # Empty collection
        assert config_manager._is_valid_fqcn('123.invalid.module') is False  # Invalid identifier


class TestConversionSettings:
    """Test cases for ConversionSettings dataclass."""
    
    def test_conversion_settings_defaults(self):
        """Test ConversionSettings with default values."""
        settings = ConversionSettings()
        
        assert settings.backup_files is True
        assert settings.backup_suffix == ".fqcn_backup"
        assert settings.backup_directory == ".fqcn_backups"
        assert settings.validation_level == "standard"
        assert settings.conflict_resolution == "context_aware"
        assert settings.create_rollback is True
        assert settings.rollback_suffix == ".fqcn_rollback"
    
    def test_conversion_settings_custom_values(self):
        """Test ConversionSettings with custom values."""
        settings = ConversionSettings(
            backup_files=False,
            backup_suffix=".custom_backup",
            backup_directory=".custom_backups",
            validation_level="strict",
            conflict_resolution="permissive",
            create_rollback=False,
            rollback_suffix=".custom_rollback"
        )
        
        assert settings.backup_files is False
        assert settings.backup_suffix == ".custom_backup"
        assert settings.backup_directory == ".custom_backups"
        assert settings.validation_level == "strict"
        assert settings.conflict_resolution == "permissive"
        assert settings.create_rollback is False
        assert settings.rollback_suffix == ".custom_rollback"


class TestConfigurationSchema:
    """Test cases for ConfigurationSchema dataclass."""
    
    def test_configuration_schema_defaults(self):
        """Test ConfigurationSchema with default values."""
        schema = ConfigurationSchema()
        
        assert schema.version == "1.0"
        assert schema.metadata == {}
        assert schema.mappings == {}
        assert isinstance(schema.settings, ConversionSettings)
        assert schema.collection_dependencies == {}
        assert schema.validation_patterns == {}
        assert schema.conversion_rules == {}
    
    def test_configuration_schema_custom_values(self):
        """Test ConfigurationSchema with custom values."""
        custom_settings = ConversionSettings(backup_files=False)
        custom_mappings = {'module1': 'collection1.module1'}
        custom_metadata = {'author': 'test', 'version': '1.0'}
        
        schema = ConfigurationSchema(
            version="2.0",
            metadata=custom_metadata,
            mappings=custom_mappings,
            settings=custom_settings
        )
        
        assert schema.version == "2.0"
        assert schema.metadata == custom_metadata
        assert schema.mappings == custom_mappings
        assert schema.settings.backup_files is False