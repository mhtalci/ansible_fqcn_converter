"""
Entry point for running FQCN Converter as a module.

This allows the package to be executed with:
    python -m fqcn_converter
"""

import sys
from .cli.main import main

if __name__ == "__main__":
    sys.exit(main())
