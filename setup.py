#!/usr/bin/env python3
"""
Setup script for backward compatibility with older pip versions.

This file provides backward compatibility for pip versions that don't fully
support PEP 517/518 build systems. For modern installations, pyproject.toml
is the preferred configuration method.

IMPORTANT: This project is distributed ONLY through GitHub and is NOT
published on PyPI or other package repositories. Install using:
pip install git+https://github.com/mhtalci/ansible_fqcn_converter.git
"""

from setuptools import setup

if __name__ == "__main__":
    setup()