#!/usr/bin/env python
"""
Test runner for Health Check Dashboard
"""

import unittest
import sys
import os

# Add the project directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_tests():
    """Discover and run all tests in the test file."""
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir='.', pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success/failure
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)