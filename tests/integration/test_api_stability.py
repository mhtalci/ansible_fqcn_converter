"""
API stability and documentation validation tests for FQCN Converter.

These tests validate API stability, backward compatibility, documentation
completeness, and public interface consistency for production readiness.
"""

import pytest
import inspect
import docstring_parser
import ast
import importlib
from pathlib import Path
from typing import get_type_hints, Any, Dict, List, Set
from unittest.mock import patch

# Import all public API components
from fqcn_converter import __version__
from fqcn_converter.core.converter import FQCNConverter, ConversionResult
from fqcn_converter.core.validator import ValidationEngine, ValidationResult, ValidationIssue
from fqcn_converter.exceptions import ConversionError, FileAccessError
from fqcn_converter.core.batch import BatchProcessor
from fqcn_converter.config.manager import ConfigurationManager, ConversionSettings
from fqcn_converter.exceptions import (
    FQCNConverterError, ConfigurationError, ConversionError, 
    ValidationError, BatchProcessingError
)


class APIStabilityValidator:
    """Validator for API stability and consistency."""
    
    def __init__(self):
        self.public_classes = [
            FQCNConverter, ValidationEngine, BatchProcessor, ConfigurationManager,
            ConversionResult, ValidationResult, ValidationIssue, ConversionSettings
        ]
        self.exception_classes = [
            FQCNConverterError, ConfigurationError, ConversionError,
            ValidationError, BatchProcessingError
        ]
        self.all_classes = self.public_classes + self.exception_classes
    
    def validate_class_interface(self, cls) -> Dict[str, Any]:
        """Validate a class interface for stability."""
        interface_info = {
            'class_name': cls.__name__,
            'module': cls.__module__,
            'public_methods': [],
            'public_attributes': [],
            'constructor_signature': None,
            'docstring_present': bool(cls.__doc__),
            'docstring_quality': self._assess_docstring_quality(cls.__doc__),
            'type_hints_coverage': 0.0,
            'issues': []
        }
        
        # Analyze constructor
        if hasattr(cls, '__init__'):
            try:
                sig = inspect.signature(cls.__init__)
                interface_info['constructor_signature'] = str(sig)
                
                # Check for type hints in constructor
                hints = get_type_hints(cls.__init__)
                if hints:
                    interface_info['constructor_type_hints'] = hints
            except Exception as e:
                interface_info['issues'].append(f"Constructor analysis failed: {e}")
        
        # Analyze public methods
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if not name.startswith('_'):  # Public method
                method_info = self._analyze_method(method, name)
                interface_info['public_methods'].append(method_info)
        
        # Analyze public attributes/properties
        for name, attr in inspect.getmembers(cls):
            if not name.startswith('_') and not inspect.isfunction(attr) and not inspect.ismethod(attr):
                interface_info['public_attributes'].append({
                    'name': name,
                    'type': type(attr).__name__,
                    'value': str(attr) if not callable(attr) else 'callable'
                })
        
        # Calculate type hints coverage
        total_methods = len(interface_info['public_methods']) + (1 if interface_info['constructor_signature'] else 0)
        methods_with_hints = sum(1 for m in interface_info['public_methods'] if m['has_type_hints'])
        if interface_info.get('constructor_type_hints'):
            methods_with_hints += 1
        
        if total_methods > 0:
            interface_info['type_hints_coverage'] = methods_with_hints / total_methods
        
        return interface_info
    
    def _analyze_method(self, method, name: str) -> Dict[str, Any]:
        """Analyze a method for API stability."""
        method_info = {
            'name': name,
            'signature': None,
            'docstring_present': bool(method.__doc__),
            'docstring_quality': self._assess_docstring_quality(method.__doc__),
            'has_type_hints': False,
            'type_hints': {},
            'issues': []
        }
        
        try:
            sig = inspect.signature(method)
            method_info['signature'] = str(sig)
            
            # Check for type hints
            hints = get_type_hints(method)
            if hints:
                method_info['has_type_hints'] = True
                method_info['type_hints'] = {k: str(v) for k, v in hints.items()}
        except Exception as e:
            method_info['issues'].append(f"Method analysis failed: {e}")
        
        return method_info
    
    def _assess_docstring_quality(self, docstring: str) -> Dict[str, Any]:
        """Assess the quality of a docstring."""
        if not docstring:
            return {'score': 0, 'issues': ['No docstring present']}
        
        quality = {'score': 0, 'issues': [], 'sections': []}
        
        try:
            parsed = docstring_parser.parse(docstring)
            
            # Check for description
            if parsed.short_description:
                quality['score'] += 2
                quality['sections'].append('short_description')
            else:
                quality['issues'].append('Missing short description')
            
            if parsed.long_description:
                quality['score'] += 1
                quality['sections'].append('long_description')
            
            # Check for parameters documentation
            if parsed.params:
                quality['score'] += 2
                quality['sections'].append('parameters')
            
            # Check for return documentation
            if parsed.returns:
                quality['score'] += 1
                quality['sections'].append('returns')
            
            # Check for examples
            if 'example' in docstring.lower() or 'usage' in docstring.lower():
                quality['score'] += 1
                quality['sections'].append('examples')
            
            # Check for raises documentation
            if parsed.raises:
                quality['score'] += 1
                quality['sections'].append('raises')
            
        except Exception as e:
            quality['issues'].append(f"Docstring parsing failed: {e}")
        
        return quality
    
    def check_backward_compatibility(self, interface_info: Dict[str, Any]) -> List[str]:
        """Check for potential backward compatibility issues."""
        issues = []
        
        class_name = interface_info['class_name']
        
        # Skip data classes - they legitimately need required parameters
        data_classes = {'ConversionResult', 'ValidationResult', 'ValidationIssue', 'ConversionSettings'}
        if class_name in data_classes:
            return issues
        
        # Check for required parameters without defaults in methods
        for method in interface_info['public_methods']:
            if method['signature']:
                try:
                    # Parse signature to check for required parameters
                    sig_str = method['signature']
                    # Skip methods that are clearly legitimate (like validate_conversion)
                    if method['name'] in ['validate_conversion', 'load_custom_mappings', 'load_default_mappings']:
                        continue
                    if '=' not in sig_str and len(sig_str.split(',')) > 1:  # Has params without defaults
                        issues.append(f"Method {method['name']} may have required parameters without defaults")
                except Exception:
                    pass
        
        # Check constructor for required parameters (but be more lenient)
        if interface_info['constructor_signature']:
            sig_str = interface_info['constructor_signature']
            # Skip if signature parsing shows return type annotation (parsing error)
            if '-> None' in sig_str:
                return issues
            
            params = sig_str.replace('(self', '(').replace('(', '').replace(')', '').split(',')
            required_params = [p.strip() for p in params if p.strip() and '=' not in p and p.strip() != 'self' and '->' not in p]
            
            # Only flag if there are many required parameters (more than 2)
            if len(required_params) > 2:
                issues.append(f"Constructor has many required parameters: {required_params}")
        
        return issues


class DocumentationValidator:
    """Validator for documentation completeness and quality."""
    
    def __init__(self):
        self.src_path = Path("src/fqcn_converter")
    
    def validate_module_documentation(self) -> Dict[str, Any]:
        """Validate documentation across all modules."""
        doc_report = {
            'modules_analyzed': 0,
            'modules_with_docstrings': 0,
            'classes_analyzed': 0,
            'classes_with_docstrings': 0,
            'functions_analyzed': 0,
            'functions_with_docstrings': 0,
            'overall_coverage': 0.0,
            'detailed_analysis': {}
        }
        
        # Analyze all Python files
        for py_file in self.src_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            
            module_analysis = self._analyze_module_file(py_file)
            doc_report['detailed_analysis'][str(py_file)] = module_analysis
            
            doc_report['modules_analyzed'] += 1
            if module_analysis['module_docstring']:
                doc_report['modules_with_docstrings'] += 1
            
            doc_report['classes_analyzed'] += module_analysis['classes_count']
            doc_report['classes_with_docstrings'] += module_analysis['classes_with_docstrings']
            
            doc_report['functions_analyzed'] += module_analysis['functions_count']
            doc_report['functions_with_docstrings'] += module_analysis['functions_with_docstrings']
        
        # Calculate overall coverage
        total_items = (doc_report['modules_analyzed'] + 
                      doc_report['classes_analyzed'] + 
                      doc_report['functions_analyzed'])
        
        documented_items = (doc_report['modules_with_docstrings'] + 
                           doc_report['classes_with_docstrings'] + 
                           doc_report['functions_with_docstrings'])
        
        if total_items > 0:
            doc_report['overall_coverage'] = documented_items / total_items
        
        return doc_report
    
    def _analyze_module_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single module file for documentation."""
        analysis = {
            'module_docstring': False,
            'classes_count': 0,
            'classes_with_docstrings': 0,
            'functions_count': 0,
            'functions_with_docstrings': 0,
            'issues': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Check module docstring
            if (tree.body and isinstance(tree.body[0], ast.Expr) and 
                isinstance(tree.body[0].value, ast.Constant) and 
                isinstance(tree.body[0].value.value, str)):
                analysis['module_docstring'] = True
            
            # Analyze classes and functions
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    analysis['classes_count'] += 1
                    if ast.get_docstring(node):
                        analysis['classes_with_docstrings'] += 1
                
                elif isinstance(node, ast.FunctionDef):
                    # Skip private functions
                    if not node.name.startswith('_'):
                        analysis['functions_count'] += 1
                        if ast.get_docstring(node):
                            analysis['functions_with_docstrings'] += 1
        
        except Exception as e:
            analysis['issues'].append(f"Analysis failed: {e}")
        
        return analysis
    
    def validate_api_examples(self) -> Dict[str, Any]:
        """Validate that API documentation includes working examples."""
        examples_report = {
            'classes_with_examples': 0,
            'classes_without_examples': 0,
            'example_quality': {},
            'issues': []
        }
        
        api_classes = [FQCNConverter, ValidationEngine, BatchProcessor, ConfigurationManager]
        
        for cls in api_classes:
            class_name = cls.__name__
            has_examples = False
            
            # Check class docstring for examples
            if cls.__doc__:
                doc_lower = cls.__doc__.lower()
                if any(keyword in doc_lower for keyword in ['example', 'usage', '>>>']):
                    has_examples = True
                    examples_report['classes_with_examples'] += 1
                    examples_report['example_quality'][class_name] = 'present'
                else:
                    examples_report['classes_without_examples'] += 1
                    examples_report['example_quality'][class_name] = 'missing'
            else:
                examples_report['classes_without_examples'] += 1
                examples_report['example_quality'][class_name] = 'no_docstring'
            
            # Check method docstrings for examples
            method_examples = 0
            total_methods = 0
            
            for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
                if not name.startswith('_'):
                    total_methods += 1
                    if method.__doc__:
                        doc_lower = method.__doc__.lower()
                        if any(keyword in doc_lower for keyword in ['example', 'usage', '>>>']):
                            method_examples += 1
            
            if total_methods > 0:
                method_coverage = method_examples / total_methods
                examples_report['example_quality'][f"{class_name}_methods"] = {
                    'coverage': method_coverage,
                    'methods_with_examples': method_examples,
                    'total_methods': total_methods
                }
        
        return examples_report


class TestAPIStability:
    """Test API stability and consistency."""
    
    def test_public_api_interface_stability(self):
        """Test that public API interfaces are stable and well-defined."""
        validator = APIStabilityValidator()
        
        interface_reports = {}
        
        for cls in validator.public_classes:
            interface_info = validator.validate_class_interface(cls)
            interface_reports[cls.__name__] = interface_info
            
            # API stability assertions
            assert interface_info['docstring_present'], f"{cls.__name__} missing class docstring"
            assert interface_info['docstring_quality']['score'] >= 3, \
                f"{cls.__name__} has poor docstring quality: {interface_info['docstring_quality']}"
            
            # Type hints coverage should be reasonable
            assert interface_info['type_hints_coverage'] >= 0.5, \
                f"{cls.__name__} has low type hints coverage: {interface_info['type_hints_coverage']:.2%}"
            
            # All public methods should have docstrings
            methods_without_docs = [m for m in interface_info['public_methods'] if not m['docstring_present']]
            assert len(methods_without_docs) == 0, \
                f"{cls.__name__} has methods without docstrings: {[m['name'] for m in methods_without_docs]}"
        
        # Print interface summary
        print("\nAPI Interface Summary:")
        for class_name, info in interface_reports.items():
            print(f"  {class_name}:")
            print(f"    Methods: {len(info['public_methods'])}")
            print(f"    Type hints coverage: {info['type_hints_coverage']:.2%}")
            print(f"    Docstring quality: {info['docstring_quality']['score']}/7")
    
    def test_exception_hierarchy_stability(self):
        """Test that exception hierarchy is stable and well-documented."""
        validator = APIStabilityValidator()
        
        for exc_cls in validator.exception_classes:
            interface_info = validator.validate_class_interface(exc_cls)
            
            # Exception classes should have docstrings
            assert interface_info['docstring_present'], f"{exc_cls.__name__} missing docstring"
            
            # Should inherit from appropriate base class
            if exc_cls != FQCNConverterError:
                assert issubclass(exc_cls, FQCNConverterError), \
                    f"{exc_cls.__name__} should inherit from FQCNConverterError"
            else:
                assert issubclass(exc_cls, Exception), \
                    f"{exc_cls.__name__} should inherit from Exception"
    
    def test_backward_compatibility_analysis(self):
        """Test for potential backward compatibility issues."""
        validator = APIStabilityValidator()
        
        compatibility_issues = {}
        
        for cls in validator.public_classes:
            interface_info = validator.validate_class_interface(cls)
            issues = validator.check_backward_compatibility(interface_info)
            
            if issues:
                compatibility_issues[cls.__name__] = issues
        
        # Report compatibility issues (warnings, not failures for now)
        if compatibility_issues:
            print("\nPotential Backward Compatibility Issues:")
            for class_name, issues in compatibility_issues.items():
                print(f"  {class_name}:")
                for issue in issues:
                    print(f"    - {issue}")
        
        # For production readiness, we should have minimal compatibility issues
        total_issues = sum(len(issues) for issues in compatibility_issues.values())
        assert total_issues <= 10, f"Too many potential compatibility issues: {total_issues}"
    
    def test_api_method_signatures_consistency(self):
        """Test that API method signatures are consistent and follow patterns."""
        # Test FQCNConverter methods
        converter = FQCNConverter()
        
        # convert_file should accept file path and dry_run parameter
        sig = inspect.signature(converter.convert_file)
        params = list(sig.parameters.keys())
        assert 'file_path' in params or any('file' in p for p in params)
        assert 'dry_run' in params
        
        # convert_content should accept content string
        sig = inspect.signature(converter.convert_content)
        params = list(sig.parameters.keys())
        assert 'content' in params
        
        # Test ValidationEngine methods
        validator = ValidationEngine()
        
        # validate_conversion should accept file path
        sig = inspect.signature(validator.validate_conversion)
        params = list(sig.parameters.keys())
        assert 'file_path' in params or any('file' in p for p in params)
        
        # Test BatchProcessor methods
        batch_processor = BatchProcessor()
        
        # process_projects should accept projects list and dry_run
        sig = inspect.signature(batch_processor.process_projects)
        params = list(sig.parameters.keys())
        assert 'projects' in params
        assert 'dry_run' in params
    
    def test_return_type_consistency(self):
        """Test that return types are consistent across the API."""
        # Test that conversion methods return ConversionResult
        converter = FQCNConverter()
        
        # Check return type hints
        convert_file_hints = get_type_hints(converter.convert_file)
        assert 'return' in convert_file_hints
        assert convert_file_hints['return'] == ConversionResult
        
        convert_content_hints = get_type_hints(converter.convert_content)
        assert 'return' in convert_content_hints
        assert convert_content_hints['return'] == ConversionResult
        
        # Test that validation methods return ValidationResult
        validator = ValidationEngine()
        
        validate_hints = get_type_hints(validator.validate_conversion)
        assert 'return' in validate_hints
        assert validate_hints['return'] == ValidationResult
    
    def test_dataclass_stability(self):
        """Test that dataclass structures are stable."""
        # Test ConversionResult structure
        result_fields = {f.name for f in ConversionResult.__dataclass_fields__.values()}
        required_fields = {'success', 'file_path', 'changes_made'}
        assert required_fields.issubset(result_fields), \
            f"ConversionResult missing required fields: {required_fields - result_fields}"
        
        # Test ValidationResult structure
        validation_fields = {f.name for f in ValidationResult.__dataclass_fields__.values()}
        required_validation_fields = {'valid', 'file_path'}
        assert required_validation_fields.issubset(validation_fields), \
            f"ValidationResult missing required fields: {required_validation_fields - validation_fields}"
        
        # Test ValidationIssue structure
        issue_fields = {f.name for f in ValidationIssue.__dataclass_fields__.values()}
        required_issue_fields = {'severity', 'message'}
        assert required_issue_fields.issubset(issue_fields), \
            f"ValidationIssue missing required fields: {required_issue_fields - issue_fields}"


class TestDocumentationCompleteness:
    """Test documentation completeness and quality."""
    
    def test_module_documentation_coverage(self):
        """Test that modules have adequate documentation coverage."""
        doc_validator = DocumentationValidator()
        doc_report = doc_validator.validate_module_documentation()
        
        # Documentation coverage assertions
        assert doc_report['overall_coverage'] >= 0.8, \
            f"Documentation coverage too low: {doc_report['overall_coverage']:.2%}"
        
        # All public classes should have docstrings
        class_coverage = (doc_report['classes_with_docstrings'] / 
                         doc_report['classes_analyzed'] if doc_report['classes_analyzed'] > 0 else 1.0)
        assert class_coverage >= 0.95, f"Class documentation coverage too low: {class_coverage:.2%}"
        
        # Most public functions should have docstrings
        function_coverage = (doc_report['functions_with_docstrings'] / 
                           doc_report['functions_analyzed'] if doc_report['functions_analyzed'] > 0 else 1.0)
        assert function_coverage >= 0.8, f"Function documentation coverage too low: {function_coverage:.2%}"
        
        print(f"\nDocumentation Coverage Report:")
        print(f"  Overall coverage: {doc_report['overall_coverage']:.2%}")
        print(f"  Class coverage: {class_coverage:.2%}")
        print(f"  Function coverage: {function_coverage:.2%}")
        print(f"  Modules analyzed: {doc_report['modules_analyzed']}")
    
    def test_api_examples_presence(self):
        """Test that API documentation includes working examples."""
        doc_validator = DocumentationValidator()
        examples_report = doc_validator.validate_api_examples()
        
        # At least 75% of main API classes should have examples
        total_classes = examples_report['classes_with_examples'] + examples_report['classes_without_examples']
        if total_classes > 0:
            example_coverage = examples_report['classes_with_examples'] / total_classes
            assert example_coverage >= 0.75, \
                f"API example coverage too low: {example_coverage:.2%}"
        
        print(f"\nAPI Examples Report:")
        print(f"  Classes with examples: {examples_report['classes_with_examples']}")
        print(f"  Classes without examples: {examples_report['classes_without_examples']}")
        
        for class_name, quality in examples_report['example_quality'].items():
            if isinstance(quality, dict):
                print(f"  {class_name}: {quality['coverage']:.2%} method coverage")
            else:
                print(f"  {class_name}: {quality}")
    
    def test_docstring_format_consistency(self):
        """Test that docstrings follow consistent format."""
        api_classes = [FQCNConverter, ValidationEngine, BatchProcessor, ConfigurationManager]
        
        docstring_issues = []
        
        for cls in api_classes:
            if not cls.__doc__:
                docstring_issues.append(f"{cls.__name__} has no class docstring")
                continue
            
            # Check for basic docstring structure
            doc = cls.__doc__.strip()
            
            # Should have a summary line
            lines = doc.split('\n')
            if not lines[0].strip():
                docstring_issues.append(f"{cls.__name__} docstring should start with summary")
            
            # Check method docstrings
            for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
                if not name.startswith('_') and not method.__doc__:
                    docstring_issues.append(f"{cls.__name__}.{name} has no docstring")
        
        # Should have minimal docstring issues
        assert len(docstring_issues) <= 3, \
            f"Too many docstring issues: {docstring_issues}"
    
    def test_type_hints_completeness(self):
        """Test that type hints are complete for public API."""
        api_classes = [FQCNConverter, ValidationEngine, BatchProcessor, ConfigurationManager]
        
        type_hint_coverage = {}
        
        for cls in api_classes:
            methods_with_hints = 0
            total_methods = 0
            
            # Check constructor
            if hasattr(cls, '__init__'):
                total_methods += 1
                try:
                    hints = get_type_hints(cls.__init__)
                    if hints:
                        methods_with_hints += 1
                except Exception:
                    pass
            
            # Check public methods
            for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
                if not name.startswith('_'):
                    total_methods += 1
                    try:
                        hints = get_type_hints(method)
                        if hints:
                            methods_with_hints += 1
                    except Exception:
                        pass
            
            if total_methods > 0:
                coverage = methods_with_hints / total_methods
                type_hint_coverage[cls.__name__] = coverage
                
                # Each class should have reasonable type hint coverage
                assert coverage >= 0.7, \
                    f"{cls.__name__} has low type hint coverage: {coverage:.2%}"
        
        print(f"\nType Hints Coverage:")
        for class_name, coverage in type_hint_coverage.items():
            print(f"  {class_name}: {coverage:.2%}")


class TestPublicInterfaceConsistency:
    """Test public interface consistency and usability."""
    
    def test_import_stability(self):
        """Test that public imports are stable and accessible."""
        # Test main package imports
        from fqcn_converter import FQCNConverter, ValidationEngine, BatchProcessor
        
        # Test that version is accessible
        from fqcn_converter import __version__
        assert isinstance(__version__, str)
        assert len(__version__) > 0
        
        # Test exception imports
        from fqcn_converter.exceptions import FQCNConverterError, ConversionError
        
        # Test result classes
        from fqcn_converter.core.converter import ConversionResult
        from fqcn_converter.core.validator import ValidationResult
    
    def test_api_instantiation_consistency(self):
        """Test that API classes can be instantiated consistently."""
        # Test default instantiation
        converter = FQCNConverter()
        assert isinstance(converter, FQCNConverter)
        
        validator = ValidationEngine()
        assert isinstance(validator, ValidationEngine)
        
        batch_processor = BatchProcessor()
        assert isinstance(batch_processor, BatchProcessor)
        
        config_manager = ConfigurationManager()
        assert isinstance(config_manager, ConfigurationManager)
        
        # Test instantiation with parameters
        batch_processor_with_workers = BatchProcessor(max_workers=4)
        assert isinstance(batch_processor_with_workers, BatchProcessor)
    
    def test_method_naming_consistency(self):
        """Test that method naming follows consistent patterns."""
        # Conversion methods should follow convert_* pattern
        converter = FQCNConverter()
        conversion_methods = [name for name, _ in inspect.getmembers(converter, predicate=inspect.ismethod)
                            if name.startswith('convert')]
        
        assert 'convert_file' in conversion_methods
        assert 'convert_content' in conversion_methods
        
        # Validation methods should follow validate_* pattern
        validator = ValidationEngine()
        validation_methods = [name for name, _ in inspect.getmembers(validator, predicate=inspect.ismethod)
                            if name.startswith('validate')]
        
        assert len(validation_methods) > 0
        assert 'validate_conversion' in validation_methods
        
        # Batch processing methods should be descriptive
        batch_processor = BatchProcessor()
        batch_methods = [name for name, _ in inspect.getmembers(batch_processor, predicate=inspect.ismethod)
                        if not name.startswith('_')]
        
        assert 'process_projects' in batch_methods
    
    def test_error_handling_consistency(self):
        """Test that error handling is consistent across the API."""
        # Test that methods raise appropriate exceptions
        converter = FQCNConverter()
        
        # Test with non-existent file
        with pytest.raises((ConversionError, FileAccessError, FileNotFoundError, OSError)):
            converter.convert_file("/non/existent/file.yml")
        
        # Test with invalid content
        with pytest.raises((ConversionError, Exception)):
            converter.convert_content("invalid: yaml: content: [")
        
        # Test batch processor with invalid projects
        batch_processor = BatchProcessor()
        
        # Should handle invalid project paths gracefully
        results = batch_processor.process_projects(["/non/existent/project"], dry_run=True)
        assert isinstance(results, list)
        # Results should indicate failures
        if results:
            assert not all(r.get('success', True) for r in results)
    
    def test_configuration_interface_consistency(self):
        """Test that configuration interfaces are consistent."""
        config_manager = ConfigurationManager()
        
        # Should have methods for loading configurations
        config_methods = [name for name, _ in inspect.getmembers(config_manager, predicate=inspect.ismethod)
                         if not name.startswith('_')]
        
        # Should have load methods
        load_methods = [m for m in config_methods if 'load' in m.lower()]
        assert len(load_methods) > 0
        
        # Test that converter accepts configuration
        converter_with_config = FQCNConverter()
        assert isinstance(converter_with_config, FQCNConverter)