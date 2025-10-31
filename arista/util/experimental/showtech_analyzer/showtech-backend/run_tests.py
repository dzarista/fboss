#!/usr/bin/env python3
"""
Enhanced test runner script for the showtech analyzer backend
"""
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    if description:
        print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)

    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run tests for showtech analyzer backend")
    parser.add_argument('--type', choices=['all', 'unit', 'integration', 'app', 'parsers', 'sanity', 'utils', 'upload'],
                       default='all', help='Type of tests to run')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--coverage', action='store_true', help='Run with coverage report')
    parser.add_argument('--no-coverage', action='store_true', help='Skip coverage report')
    parser.add_argument('--pattern', '-k', help='Run tests matching pattern')
    parser.add_argument('--file', help='Run tests from specific file')
    parser.add_argument('--fast', action='store_true', help='Run only fast tests (skip slow ones)')
    parser.add_argument('--html-coverage', action='store_true', help='Generate HTML coverage report')

    args = parser.parse_args()

    # Base command
    base_cmd = ['python', '-m', 'pytest']

    # Add verbosity
    if args.verbose:
        base_cmd.append('-v')
    else:
        base_cmd.extend(['--tb=short', '-q'])

    # Add coverage if requested
    if args.coverage or (not args.no_coverage and args.type == 'all'):
        base_cmd.extend(['--cov=utils', '--cov=app', '--cov-report=term-missing'])
        if args.html_coverage:
            base_cmd.append('--cov-report=html:htmlcov')

    # Add fast filter
    if args.fast:
        base_cmd.extend(['-m', 'not slow'])

    # Determine what to run
    if args.file:
        # Run specific file
        cmd = base_cmd + [args.file]
        success = run_command(cmd, f"Running tests from {args.file}")

    elif args.pattern:
        # Run tests matching pattern
        cmd = base_cmd + ['-k', args.pattern]
        success = run_command(cmd, f"Running tests matching pattern: {args.pattern}")

    elif args.type == 'all':
        # Run all tests
        cmd = base_cmd
        success = run_command(cmd, "Running all tests")

    elif args.type == 'unit':
        # Run unit tests
        cmd = base_cmd + ['-m', 'unit']
        success = run_command(cmd, "Running unit tests")

    elif args.type == 'integration':
        # Run integration tests
        cmd = base_cmd + ['-m', 'integration']
        success = run_command(cmd, "Running integration tests")

    elif args.type == 'app':
        # Run Flask app tests
        cmd = base_cmd + ['tests/test_app.py']
        success = run_command(cmd, "Running Flask app tests")

    elif args.type == 'parsers':
        # Run parser tests
        cmd = base_cmd + ['tests/test_section_parsers.py']
        success = run_command(cmd, "Running section parser tests")

    elif args.type == 'sanity':
        # Run sanity check tests
        cmd = base_cmd + ['tests/test_log_sanity.py']
        success = run_command(cmd, "Running log sanity tests")

    elif args.type == 'utils':
        # Run utility tests
        cmd = base_cmd + ['tests/test_section_utils.py']
        success = run_command(cmd, "Running utility tests")

    elif args.type == 'upload':
        # Run file upload tests
        cmd = base_cmd + ['tests/test_file_upload.py']
        success = run_command(cmd, "Running file upload tests")

    # Print summary
    print(f"\n{'='*60}")
    if success:
        print("✅ Tests completed successfully!")
        if args.coverage or (not args.no_coverage and args.type == 'all'):
            if args.html_coverage:
                print("📊 HTML coverage report generated in htmlcov/index.html")
    else:
        print("❌ Some tests failed!")
        sys.exit(1)
    print('='*60)


if __name__ == '__main__':
    # Make sure we're in the right directory
    script_dir = Path(__file__).parent
    if script_dir.name != 'showtech-backend':
        print("Error: This script must be run from the showtech-backend directory")
        sys.exit(1)

    main()
