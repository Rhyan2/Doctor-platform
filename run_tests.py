#!/usr/bin/env python3
"""
Test runner for the Drug Inventory Management System.
"""
import pytest
import sys
import os

def main():
    """Run the test suite."""
    # Add the current directory to Python path so we can import app and models
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    # Run pytest with verbose output
    args = [
        '-v',
        '--tb=short',  # Short traceback format
        '--color=yes',
        'tests/'
    ]
    
    # Add coverage if available
    try:
        import pytest_cov
        args.extend([
            '--cov=app',
            '--cov=models',
            '--cov-report=term-missing',
            '--cov-report=html'
        ])
        print("Running tests with coverage...")
    except ImportError:
        print("pytest-cov not installed. Running without coverage.")
    
    print("Running test suite...")
    exit_code = pytest.main(args)
    sys.exit(exit_code)

if __name__ == '__main__':
    main()