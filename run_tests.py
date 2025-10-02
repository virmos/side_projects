#!/usr/bin/env python3
"""
Test runner script for the orders service.

This script provides convenient commands to run different types of tests
and generate coverage reports.
"""
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"\n❌ Command not found: {cmd[0]}")
        print("Make sure pytest is installed: pip install pytest pytest-asyncio pytest-cov")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Test runner for orders service")
    parser.add_argument(
        "command",
        choices=[
            "all", "unit", "integration", "coverage", "lint", "format",
            "quick", "pricing", "orders", "auth", "loader", "schemas"
        ],
        help="Test command to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Run with verbose output"
    )
    parser.add_argument(
        "--fail-fast", "-x",
        action="store_true",
        help="Stop on first failure"
    )
    parser.add_argument(
        "--parallel", "-n",
        type=int,
        help="Run tests in parallel with specified number of workers"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    base_cmd = ["python", "-m", "pytest"]
    
    if args.verbose:
        base_cmd.append("-v")
    
    if args.fail_fast:
        base_cmd.append("-x")
    
    if args.parallel:
        base_cmd.extend(["-n", str(args.parallel)])
    
    # Command-specific configurations
    commands = {
        "all": {
            "cmd": base_cmd + ["tests/"],
            "desc": "All tests"
        },
        "unit": {
            "cmd": base_cmd + ["tests/", "-m", "unit"],
            "desc": "Unit tests only"
        },
        "integration": {
            "cmd": base_cmd + ["tests/", "-m", "integration"],
            "desc": "Integration tests only"
        },
        "coverage": {
            "cmd": base_cmd + ["tests/", "--cov=.", "--cov-report=html", "--cov-report=term"],
            "desc": "Tests with coverage report"
        },
        "quick": {
            "cmd": base_cmd + ["tests/", "-m", "not slow", "--tb=short"],
            "desc": "Quick tests (excluding slow tests)"
        },
        "pricing": {
            "cmd": base_cmd + ["tests/test_pricing.py"],
            "desc": "Pricing tests"
        },
        "orders": {
            "cmd": base_cmd + ["tests/test_orders.py"],
            "desc": "Orders tests"
        },
        "auth": {
            "cmd": base_cmd + ["tests/test_auth.py"],
            "desc": "Auth tests"
        },
        "loader": {
            "cmd": base_cmd + ["tests/test_price_loader.py"],
            "desc": "Price loader tests"
        },
        "schemas": {
            "cmd": base_cmd + ["tests/test_schemas.py"],
            "desc": "Schema tests"
        },
        "lint": {
            "cmd": ["python", "-m", "flake8", "api/", "models/", "repository/", "services/", "securities/"],
            "desc": "Code linting"
        },
        "format": {
            "cmd": ["python", "-m", "black", "api/", "models/", "repository/", "services/", "securities/", "tests/"],
            "desc": "Code formatting"
        }
    }
    
    if args.command not in commands:
        print(f"❌ Unknown command: {args.command}")
        sys.exit(1)
    
    command_config = commands[args.command]
    success = run_command(command_config["cmd"], command_config["desc"])
    
    if not success:
        sys.exit(1)
    
    # Additional information for coverage command
    if args.command == "coverage":
        print(f"\n📊 Coverage report generated!")
        print(f"   HTML report: htmlcov/index.html")
        print(f"   Terminal report: See output above")
    
    print(f"\n🎉 All tests completed successfully!")


if __name__ == "__main__":
    main()
