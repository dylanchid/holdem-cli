"""
Test utilities for Holdem CLI.

This module provides common utilities and standardized setup for all test files.
"""

import sys
from pathlib import Path


def setup_test_imports():
    """
    Standardized import path setup for test files.

    This function ensures that the src directory is properly added to Python's
    path for importing holdem_cli modules from any test file location.

    Returns:
        Path: The src directory path that was added to sys.path
    """
    # Get the current file's absolute path
    current_file = Path(__file__).resolve()

    # Navigate to project root (tests -> project_root)
    project_root = current_file.parent.parent
    src_dir = project_root / 'src'

    # Ensure src directory exists
    if not src_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {src_dir}")

    # Add to path if not already present (avoid duplicates)
    src_str = str(src_dir)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)

    return src_dir


def get_test_data_path():
    """Get the path to the test data directory."""
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    return project_root / 'tests' / 'data'


def get_project_root():
    """Get the project root directory."""
    current_file = Path(__file__).resolve()
    return current_file.parent.parent
