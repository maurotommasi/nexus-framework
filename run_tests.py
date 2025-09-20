# run_tests.py - Test runner script
#!/usr/bin/env python3
"""
Comprehensive test runner for the Nexus Framework utilities.
Provides multiple test execution modes and detailed reporting.
"""
import sys
import subprocess
import argparse
from pathlib import Path
import time

def run_command(cmd, description=""):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description or ' '.join(cmd)}")
    print(f"{'='*60}")
    
    start_time = time.time()
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        duration = time.time() - start_time
        print(f"\n✅ {description} completed successfully in {duration:.2f}s")
        return True
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        print(f"\n❌ {description} failed after {duration:.2f}s with exit code {e.returncode}")
        return False

def run_all_tests():
    """Run all test categories."""
    print("🧪 Running Complete Test Suite for Nexus Framework")
    
    test_commands = [
        (["python", "-m", "pytest", "tests/", "-v"], "All Unit Tests"),
        (["python", "-m", "pytest", "tests/", "-m", "integration", "-v"], "Integration Tests"),
        (["python", "-m", "pytest", "tests/", "--cov=framework", "--cov-report=html"], "Coverage Report"),
    ]
    
    results = []
    for cmd, description in test_commands:
        success = run_command(cmd, description)
        results.append((description, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    for description, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{description:<30} {status}")
    
    failed_count = sum(1 for _, success in results if not success)
    if failed_count == 0:
        print(f"\n🎉 All test suites passed!")
        return True
    else:
        print(f"\n💥 {failed_count} test suite(s) failed!")
        return False

def run_specific_tests(test_pattern):
    """Run tests matching a specific pattern."""
    cmd = ["python", "-m", "pytest", f"tests/{test_pattern}", "-v"]
    return run_command(cmd, f"Tests matching '{test_pattern}'")

def run_performance_tests():
    """Run performance benchmark tests."""
    cmd = ["python", "-m", "pytest", "tests/", "-m", "performance", "--benchmark-only", "-v"]
    return run_command(cmd, "Performance Benchmark Tests")

def run_quick_tests():
    """Run quick smoke tests."""
    cmd = ["python", "-m", "pytest", "tests/", "-m", "not slow", "-x", "--tb=short"]
    return run_command(cmd, "Quick Smoke Tests")

def run_coverage_report():
    """Generate detailed coverage report."""
    commands = [
        (["python", "-m", "pytest", "tests/", "--cov=framework", "--cov-report=html", "--cov-report=term"], 
         "Coverage Analysis"),
        (["python", "-m", "coverage", "report", "--show-missing"], 
         "Missing Coverage Report")
    ]
    
    for cmd, description in commands:
        if not run_command(cmd, description):
            return False
    
    print("\n📊 Coverage report generated in htmlcov/index.html")
    return True

def validate_environment():
    """Validate test environment setup."""
    print("🔍 Validating Test Environment")
    
    required_packages = ["pytest", "pytest-cov", "pyyaml", "psutil", "requests"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} - OK")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n💥 Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    # Check framework structure
    framework_path = Path("framework")
    if not framework_path.exists():
        print("❌ Framework directory not found!")
        return False
    
    required_modules = [
        "framework/core/utils/io.py",
        "framework/core/utils/system.py", 
        "framework/core/utils/data.py",
        "framework/core/utils/wrapper.py"
    ]
    
    for module_path in required_modules:
        if not Path(module_path).exists():
            print(f"❌ {module_path} - MISSING")
            return False
        print(f"✅ {module_path} - OK")
    
    print("\n✅ Environment validation passed!")
    return True

def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(description="Nexus Framework Test Runner")
    parser.add_argument(
        "mode", 
        nargs="?", 
        default="all",
        choices=["all", "quick", "performance", "coverage", "validate"],
        help="Test mode to run"
    )
    parser.add_argument(
        "--pattern", 
        help="Run tests matching specific pattern (e.g., 'test_file_manager.py')"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Validate environment first
    if not validate_environment():
        sys.exit(1)
    
    success = False
    
    if args.pattern:
        success = run_specific_tests(args.pattern)
    elif args.mode == "all":
        success = run_all_tests()
    elif args.mode == "quick":
        success = run_quick_tests()
    elif args.mode == "performance":
        success = run_performance_tests()
    elif args.mode == "coverage":
        success = run_coverage_report()
    elif args.mode == "validate":
        success = True  # Already validated above
    
    if success:
        print(f"\n🎉 Test execution completed successfully!")
        sys.exit(0)
    else:
        print(f"\n💥 Test execution failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()