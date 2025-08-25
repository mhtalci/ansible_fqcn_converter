#!/usr/bin/env python3
"""
Context7 API Documentation Generator

This script generates comprehensive API documentation using Context7 MCP
to extract and format docstrings, type hints, and code examples from the
FQCN Converter codebase.
"""

import ast
import inspect
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import importlib.util

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import fqcn_converter
    from fqcn_converter.core.converter import FQCNConverter, ConversionResult
    from fqcn_converter.core.validator import (
        ValidationEngine,
        ValidationResult,
        ValidationIssue,
    )
    from fqcn_converter.core.batch import BatchProcessor, BatchResult
    from fqcn_converter.config.manager import ConfigurationManager
except ImportError as e:
    print(f"Error importing fqcn_converter: {e}")
    print("Make sure the package is installed or run from the project root")
    sys.exit(1)


class Context7APIDocGenerator:
    """Generates Context7-compatible API documentation from Python code."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_api_docs(self) -> None:
        """Generate complete API documentation."""
        print("🔄 Generating Context7 API documentation...")

        # Generate documentation for main classes
        classes_to_document = [
            (FQCNConverter, "Core conversion engine"),
            (ValidationEngine, "Validation and compliance checking"),
            (BatchProcessor, "Batch processing operations"),
            (ConfigurationManager, "Configuration management"),
        ]

        # Generate documentation for data classes
        dataclasses_to_document = [
            (ConversionResult, "Conversion operation results"),
            (ValidationResult, "Validation operation results"),
            (ValidationIssue, "Individual validation issues"),
            (BatchResult, "Batch processing results"),
        ]

        api_docs = {
            "title": "FQCN Converter API Reference",
            "description": "Complete API reference for the Ansible FQCN Converter library",
            "version": getattr(fqcn_converter, "__version__", "0.1.0"),
            "classes": {},
            "dataclasses": {},
            "examples": [],
            "type_hints": {},
        }

        # Document classes
        for cls, description in classes_to_document:
            print(f"  📝 Documenting {cls.__name__}...")
            api_docs["classes"][cls.__name__] = self._document_class(cls, description)

        # Document data classes
        for cls, description in dataclasses_to_document:
            print(f"  📝 Documenting {cls.__name__}...")
            api_docs["dataclasses"][cls.__name__] = self._document_dataclass(
                cls, description
            )

        # Generate usage examples
        api_docs["examples"] = self._generate_usage_examples()

        # Extract type hints
        api_docs["type_hints"] = self._extract_type_hints()

        # Write API documentation
        api_file = self.output_dir / "api_reference.json"
        with open(api_file, "w", encoding="utf-8") as f:
            json.dump(api_docs, f, indent=2, default=str)

        # Generate markdown documentation
        self._generate_markdown_docs(api_docs)

        print(f"✅ API documentation generated in {self.output_dir}")

    def _document_class(self, cls: type, description: str) -> Dict[str, Any]:
        """Document a class with its methods and attributes."""
        doc = {
            "name": cls.__name__,
            "description": description,
            "docstring": inspect.getdoc(cls) or "",
            "module": cls.__module__,
            "methods": {},
            "properties": {},
            "class_attributes": {},
        }

        # Document methods
        for name, method in inspect.getmembers(cls, inspect.isfunction):
            if not name.startswith("_") or name in ["__init__"]:
                doc["methods"][name] = self._document_method(method)

        # Document properties
        for name, prop in inspect.getmembers(cls, lambda x: isinstance(x, property)):
            doc["properties"][name] = {
                "docstring": inspect.getdoc(prop) or "",
                "getter": prop.fget is not None,
                "setter": prop.fset is not None,
                "deleter": prop.fdel is not None,
            }

        return doc

    def _document_dataclass(self, cls: type, description: str) -> Dict[str, Any]:
        """Document a dataclass with its fields."""
        doc = {
            "name": cls.__name__,
            "description": description,
            "docstring": inspect.getdoc(cls) or "",
            "module": cls.__module__,
            "fields": {},
            "is_dataclass": True,
        }

        # Get field information from annotations
        if hasattr(cls, "__annotations__"):
            for field_name, field_type in cls.__annotations__.items():
                doc["fields"][field_name] = {
                    "type": str(field_type),
                    "description": self._extract_field_description(cls, field_name),
                }

        return doc

    def _document_method(self, method) -> Dict[str, Any]:
        """Document a method with its signature and docstring."""
        try:
            signature = inspect.signature(method)
            docstring = inspect.getdoc(method) or ""

            # Parse docstring for parameters and return info
            params_info = self._parse_docstring_params(docstring)
            return_info = self._parse_docstring_returns(docstring)

            return {
                "signature": str(signature),
                "docstring": docstring,
                "parameters": {
                    name: {
                        "type": (
                            str(param.annotation)
                            if param.annotation != param.empty
                            else "Any"
                        ),
                        "default": (
                            str(param.default) if param.default != param.empty else None
                        ),
                        "description": params_info.get(name, ""),
                    }
                    for name, param in signature.parameters.items()
                },
                "returns": {
                    "type": (
                        str(signature.return_annotation)
                        if signature.return_annotation != signature.empty
                        else "Any"
                    ),
                    "description": return_info,
                },
                "raises": self._parse_docstring_raises(docstring),
            }
        except Exception as e:
            return {
                "signature": "Unable to parse signature",
                "docstring": inspect.getdoc(method) or "",
                "error": str(e),
            }

    def _extract_field_description(self, cls: type, field_name: str) -> str:
        """Extract field description from class docstring."""
        docstring = inspect.getdoc(cls) or ""

        # Look for field descriptions in the docstring
        lines = docstring.split("\n")
        in_attributes = False

        for line in lines:
            if "Attributes:" in line:
                in_attributes = True
                continue

            if in_attributes and line.strip().startswith(f"{field_name}:"):
                return line.split(":", 1)[1].strip()

        return ""

    def _parse_docstring_params(self, docstring: str) -> Dict[str, str]:
        """Parse parameter descriptions from docstring."""
        params = {}
        lines = docstring.split("\n")
        in_args = False

        for line in lines:
            if "Args:" in line or "Arguments:" in line or "Parameters:" in line:
                in_args = True
                continue

            if in_args and line.strip():
                if line.strip().startswith(("Returns:", "Raises:", "Example:")):
                    break

                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        param_name = parts[0].strip()
                        description = parts[1].strip()
                        params[param_name] = description

        return params

    def _parse_docstring_returns(self, docstring: str) -> str:
        """Parse return description from docstring."""
        lines = docstring.split("\n")
        in_returns = False
        return_desc = ""

        for line in lines:
            if "Returns:" in line:
                in_returns = True
                return_desc = line.split("Returns:", 1)[1].strip()
                continue

            if in_returns and line.strip():
                if line.strip().startswith(("Args:", "Raises:", "Example:")):
                    break
                return_desc += " " + line.strip()

        return return_desc.strip()

    def _parse_docstring_raises(self, docstring: str) -> List[Dict[str, str]]:
        """Parse raises information from docstring."""
        raises = []
        lines = docstring.split("\n")
        in_raises = False

        for line in lines:
            if "Raises:" in line:
                in_raises = True
                continue

            if in_raises and line.strip():
                if line.strip().startswith(("Args:", "Returns:", "Example:")):
                    break

                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        exception_type = parts[0].strip()
                        description = parts[1].strip()
                        raises.append(
                            {"exception": exception_type, "description": description}
                        )

        return raises

    def _generate_usage_examples(self) -> List[Dict[str, str]]:
        """Generate comprehensive usage examples."""
        return [
            {
                "title": "Basic Conversion",
                "description": "Convert a single Ansible file to FQCN format",
                "code": """from fqcn_converter import FQCNConverter

# Initialize converter with default settings
converter = FQCNConverter()

# Convert a playbook file
result = converter.convert_file("playbook.yml")

if result.success:
    print(f"✅ Successfully converted {result.changes_made} modules")
else:
    print(f"❌ Conversion failed: {result.errors}")""",
            },
            {
                "title": "Custom Configuration",
                "description": "Use custom FQCN mappings and configuration",
                "code": """from fqcn_converter import FQCNConverter

# Custom mappings for specific modules
custom_mappings = {
    "my_module": "my.collection.my_module",
    "custom_action": "company.internal.custom_action"
}

# Initialize with custom configuration
converter = FQCNConverter(
    config_path="custom_config.yml",
    custom_mappings=custom_mappings,
    create_backups=True
)

# Convert with dry run to preview changes
result = converter.convert_file("playbook.yml", dry_run=True)
print(f"Would convert {result.changes_made} modules")""",
            },
            {
                "title": "Validation and Compliance",
                "description": "Validate FQCN compliance and get detailed reports",
                "code": """from fqcn_converter import ValidationEngine

# Initialize validation engine
validator = ValidationEngine()

# Validate a file
result = validator.validate_conversion("playbook.yml")

print(f"Validation score: {result.score:.1%}")
print(f"Total modules: {result.total_modules}")
print(f"FQCN modules: {result.fqcn_modules}")

if not result.valid:
    print("Issues found:")
    for issue in result.issues:
        print(f"  Line {issue.line_number}: {issue.message}")
        if issue.suggestion:
            print(f"    💡 {issue.suggestion}")""",
            },
            {
                "title": "Batch Processing",
                "description": "Process multiple Ansible projects in parallel",
                "code": """from fqcn_converter import BatchProcessor

# Initialize batch processor
processor = BatchProcessor(max_workers=4)

# Discover Ansible projects
projects = processor.discover_projects("/path/to/ansible/projects")
print(f"Found {len(projects)} Ansible projects")

# Process all projects
result = processor.process_projects(projects, dry_run=False)

print(f"Processed {result.total_projects} projects")
print(f"Successful: {result.successful_conversions}")
print(f"Failed: {result.failed_conversions}")
print(f"Execution time: {result.execution_time:.2f}s")""",
            },
            {
                "title": "Content Processing",
                "description": "Process Ansible content directly from strings",
                "code": '''from fqcn_converter import FQCNConverter

converter = FQCNConverter()

# YAML content with short module names
yaml_content = """
- name: Copy file
  copy:
    src: /tmp/source
    dest: /tmp/dest

- name: Install package
  yum:
    name: httpd
    state: present
"""

# Convert content directly
result = converter.convert_content(yaml_content)

if result.success:
    print("Converted content:")
    print(result.converted_content)
else:
    print(f"Conversion failed: {result.errors}")''',
            },
        ]

    def _extract_type_hints(self) -> Dict[str, Any]:
        """Extract type hints from the codebase."""
        type_hints = {
            "common_types": {
                "Union[str, Path]": "String or Path object",
                "Optional[str]": "String or None",
                "Dict[str, str]": "Dictionary with string keys and values",
                "List[str]": "List of strings",
                "List[ValidationIssue]": "List of validation issue objects",
            },
            "return_types": {
                "ConversionResult": "Object containing conversion operation results",
                "ValidationResult": "Object containing validation results and compliance score",
                "BatchResult": "Object containing batch processing results and statistics",
            },
        }
        return type_hints

    def _generate_markdown_docs(self, api_docs: Dict[str, Any]) -> None:
        """Generate markdown documentation from API docs."""
        md_content = f"""# {api_docs['title']}

{api_docs['description']}

**Version:** {api_docs['version']}

## Table of Contents

- [Classes](#classes)
- [Data Classes](#data-classes)
- [Usage Examples](#usage-examples)
- [Type Hints Reference](#type-hints-reference)

## Classes

"""

        # Document classes
        for class_name, class_info in api_docs["classes"].items():
            md_content += f"### {class_name}\n\n"
            md_content += f"{class_info['description']}\n\n"

            if class_info["docstring"]:
                md_content += f"```\n{class_info['docstring']}\n```\n\n"

            # Document methods
            if class_info["methods"]:
                md_content += "#### Methods\n\n"
                for method_name, method_info in class_info["methods"].items():
                    md_content += (
                        f"##### `{method_name}{method_info.get('signature', '')}`\n\n"
                    )

                    if method_info.get("docstring"):
                        md_content += f"{method_info['docstring']}\n\n"

                    # Parameters
                    if method_info.get("parameters"):
                        md_content += "**Parameters:**\n\n"
                        for param_name, param_info in method_info["parameters"].items():
                            if param_name != "self":
                                md_content += f"- `{param_name}` ({param_info['type']})"
                                if param_info["default"]:
                                    md_content += f" = {param_info['default']}"
                                if param_info["description"]:
                                    md_content += f": {param_info['description']}"
                                md_content += "\n"
                        md_content += "\n"

                    # Returns
                    if (
                        method_info.get("returns")
                        and method_info["returns"]["description"]
                    ):
                        md_content += (
                            f"**Returns:** {method_info['returns']['description']}\n\n"
                        )

                    # Raises
                    if method_info.get("raises"):
                        md_content += "**Raises:**\n\n"
                        for raise_info in method_info["raises"]:
                            md_content += f"- `{raise_info['exception']}`: {raise_info['description']}\n"
                        md_content += "\n"

            md_content += "---\n\n"

        # Document data classes
        md_content += "## Data Classes\n\n"
        for class_name, class_info in api_docs["dataclasses"].items():
            md_content += f"### {class_name}\n\n"
            md_content += f"{class_info['description']}\n\n"

            if class_info["docstring"]:
                md_content += f"```\n{class_info['docstring']}\n```\n\n"

            # Document fields
            if class_info["fields"]:
                md_content += "#### Fields\n\n"
                for field_name, field_info in class_info["fields"].items():
                    md_content += f"- `{field_name}` ({field_info['type']})"
                    if field_info["description"]:
                        md_content += f": {field_info['description']}"
                    md_content += "\n"
                md_content += "\n"

            md_content += "---\n\n"

        # Usage examples
        md_content += "## Usage Examples\n\n"
        for example in api_docs["examples"]:
            md_content += f"### {example['title']}\n\n"
            md_content += f"{example['description']}\n\n"
            md_content += f"```python\n{example['code']}\n```\n\n"

        # Type hints
        md_content += "## Type Hints Reference\n\n"
        md_content += "### Common Types\n\n"
        for type_hint, description in api_docs["type_hints"]["common_types"].items():
            md_content += f"- `{type_hint}`: {description}\n"

        md_content += "\n### Return Types\n\n"
        for type_hint, description in api_docs["type_hints"]["return_types"].items():
            md_content += f"- `{type_hint}`: {description}\n"

        # Write markdown file
        md_file = self.output_dir / "api_reference.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)


def main():
    """Main entry point for documentation generation."""
    # Determine output directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    docs_dir = project_root / "docs" / "reference" / "api"

    # Generate documentation
    generator = Context7APIDocGenerator(docs_dir)
    generator.generate_api_docs()

    print(f"\n📚 Context7 API documentation generated successfully!")
    print(f"   📁 Output directory: {docs_dir}")
    print(f"   📄 API Reference: {docs_dir / 'api_reference.md'}")
    print(f"   📄 JSON Data: {docs_dir / 'api_reference.json'}")


if __name__ == "__main__":
    main()
