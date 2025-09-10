#!/usr/bin/env python3
"""
StyleStack Parallel Test Runner

This script provides comprehensive test execution with parallel processing,
performance monitoring, and detailed reporting capabilities.
"""


from typing import Any, Dict, Optional
import os
import sys
import subprocess
import argparse
import time
import json
from pathlib import Path
import multiprocessing
import platform


def get_optimal_worker_count() -> int:
    """Calculate optimal number of test workers based on system resources."""
    cpu_count = multiprocessing.cpu_count()
    
    # Conservative approach: use 75% of available CPUs
    # but ensure minimum of 2 and maximum reasonable limit
    optimal = max(2, min(cpu_count * 3 // 4, 8))
    
    print(f"System has {cpu_count} CPUs, using {optimal} parallel workers")
    return optimal


def create_reports_directory() -> Path:
    """Create reports directory if it doesn't exist."""
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    return reports_dir


def run_test_suite(
    test_type: str = "all",
    parallel_workers: Optional[int] = None,
    coverage_threshold: int = 80,
    max_failures: int = 5,
    timeout: int = 300,
    verbose: bool = True,
    generate_html_report: bool = True
) -> Dict[str, Any]:
    """
    Run test suite with specified configuration.
    
    Args:
        test_type: Type of tests to run ("unit", "integration", "system", "all")
        parallel_workers: Number of parallel workers (None for auto)
        coverage_threshold: Minimum coverage percentage required
        max_failures: Maximum failures before stopping
        timeout: Timeout per test in seconds
        verbose: Enable verbose output
        generate_html_report: Generate HTML test report
    
    Returns:
        Dict containing test results and metrics
    """
    
    # Ensure reports directory exists
    reports_dir = create_reports_directory()
    
    # Determine worker count
    if parallel_workers is None:
        parallel_workers = get_optimal_worker_count()
    
    # Build pytest command
    cmd = [
        sys.executable, "-m", "pytest",
        f"--config-file=pytest-parallel.ini",
        f"-n", str(parallel_workers),
        f"--maxfail={max_failures}",
        f"--timeout={timeout}",
        f"--cov-fail-under={coverage_threshold}",
    ]
    
    # Add test type selection
    if test_type != "all":
        if test_type == "unit":
            cmd.extend(["-m", "unit"])
        elif test_type == "integration":
            cmd.extend(["-m", "integration"])
        elif test_type == "system":
            cmd.extend(["-m", "system"])
        elif test_type == "fast":
            cmd.extend(["-m", "unit or (integration and not slow)"])
        elif test_type == "slow":
            cmd.extend(["-m", "slow or stress or system"])
    
    # Add verbosity
    if verbose:
        cmd.append("--verbose")
    else:
        cmd.append("--quiet")
    
    # Add HTML report generation
    if generate_html_report:
        cmd.extend([
            "--html", str(reports_dir / "test-report.html"),
            "--self-contained-html"
        ])
    
    # Add JSON report
    cmd.extend([
        "--json-report",
        "--json-report-file", str(reports_dir / "test-results.json")
    ])
    
    print(f"Running command: {" ".join(cmd)}")
    print(f"Test type: {test_type}")
    print(f"Parallel workers: {parallel_workers}")
    print(f"Coverage threshold: {coverage_threshold}%")
    print("-" * 60)
    
    # Execute tests
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=False,  # Show output in real-time
            text=True,
            cwd=Path.cwd(),
            env=dict(os.environ, PYTHONPATH=str(Path.cwd()))
        )
        
        execution_time = time.time() - start_time
        
        # Parse results
        results = {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "execution_time": execution_time,
            "test_type": test_type,
            "parallel_workers": parallel_workers,
            "coverage_threshold": coverage_threshold
        }
        
        # Try to load JSON results if available
        json_results_file = reports_dir / "test-results.json"
        if json_results_file.exists():
            try:
                with open(json_results_file, "r") as f:
                    json_results = json.load(f)
                    results["detailed_results"] = json_results
                    
                    # Extract key metrics
                    if "summary" in json_results:
                        summary = json_results["summary"]
                        results.update({
                            "total_tests": summary.get("total", 0),
                            "passed_tests": summary.get("passed", 0),
                            "failed_tests": summary.get("failed", 0),
                            "skipped_tests": summary.get("skipped", 0),
                            "error_tests": summary.get("error", 0)
                        })
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not parse JSON results: {e}")
        
        return results
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "return_code": -1,
            "execution_time": timeout,
            "error": "Test execution timed out",
            "test_type": test_type,
            "parallel_workers": parallel_workers
        }
    
    except Exception as e:
        return {
            "success": False,
            "return_code": -2,
            "execution_time": time.time() - start_time,
            "error": str(e),
            "test_type": test_type,
            "parallel_workers": parallel_workers
        }


def run_performance_benchmark() -> Dict[str, Any]:
    """Run performance benchmarks to validate parallel execution improvements."""
    
    print("\n" + "="*60)
    print("PERFORMANCE BENCHMARK")
    print("="*60)
    
    benchmarks = []
    
    # Test configurations
    configurations = [
        {"workers": 1, "name": "Sequential"},
        {"workers": 2, "name": "Parallel (2 workers)"},
        {"workers": get_optimal_worker_count(), "name": f"Optimal ({get_optimal_worker_count()} workers)"}
    ]
    
    for config in configurations:
        print(f"\nRunning benchmark: {config["name"]}")
        print("-" * 40)
        
        result = run_test_suite(
            test_type="unit",  # Fast tests for benchmarking
            parallel_workers=config["workers"],
            verbose=False,
            generate_html_report=False,
            max_failures=50  # Allow more failures for benchmarking
        )
        
        benchmark_data = {
            "configuration": config["name"],
            "workers": config["workers"],
            "execution_time": result["execution_time"],
            "success": result["success"],
            "tests_run": result.get("total_tests", 0)
        }
        
        benchmarks.append(benchmark_data)
        
        print(f"Execution time: {result["execution_time"]:.2f} seconds")
        if result.get("total_tests"):
            print(f"Tests run: {result["total_tests"]}")
            print(f"Tests/second: {result["total_tests"] / result["execution_time"]:.2f}")
    
    # Calculate performance improvements
    if len(benchmarks) >= 2:
        sequential_time = benchmarks[0]["execution_time"]
        for i, benchmark in enumerate(benchmarks[1:], 1):
            if sequential_time > 0:
                improvement = ((sequential_time - benchmark["execution_time"]) / sequential_time) * 100
                benchmark["improvement_percentage"] = improvement
                print(f"\n{benchmark["configuration"]} improvement: {improvement:.1f}%")
    
    return {
        "benchmarks": benchmarks,
        "optimal_workers": get_optimal_worker_count(),
        "platform_info": {
            "system": platform.system(),
            "machine": platform.machine(),
            "cpu_count": multiprocessing.cpu_count()
        }
    }


def generate_summary_report(results: Dict[str, Any]):
    """Generate a summary report of test execution."""
    
    print("\n" + "="*60)
    print("TEST EXECUTION SUMMARY")
    print("="*60)
    
    print(f"Status: {"✅ PASSED" if results["success"] else "❌ FAILED"}")
    print(f"Execution time: {results["execution_time"]:.2f} seconds")
    print(f"Test type: {results["test_type"]}")
    print(f"Parallel workers: {results["parallel_workers"]}")
    
    if "total_tests" in results:
        print(f"Total tests: {results["total_tests"]}")
        print(f"Passed: {results.get("passed_tests", 0)}")
        print(f"Failed: {results.get("failed_tests", 0)}")
        print(f"Skipped: {results.get("skipped_tests", 0)}")
        
        if results["total_tests"] > 0:
            pass_rate = (results.get("passed_tests", 0) / results["total_tests"]) * 100
            print(f"Pass rate: {pass_rate:.1f}%")
    
    # Coverage information (if available)
    reports_dir = Path("reports")
    coverage_file = reports_dir / "coverage.xml"
    if coverage_file.exists():
        print(f"Coverage report: {coverage_file}")
    
    # HTML report
    html_report = reports_dir / "test-report.html"
    if html_report.exists():
        print(f"HTML report: {html_report}")
    
    if "error" in results:
        print(f"Error: {results["error"]}")


def main():
    """Main function for parallel test execution."""
    
    parser = argparse.ArgumentParser(
        description="StyleStack Parallel Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_parallel_tests.py                    # Run all tests with optimal parallelism
  python run_parallel_tests.py --type unit        # Run only unit tests
  python run_parallel_tests.py --workers 4        # Use 4 parallel workers
  python run_parallel_tests.py --benchmark        # Run performance benchmark
  python run_parallel_tests.py --type fast        # Run fast tests only
        """
    )
    
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration", "system", "fast", "slow"],
        default="all",
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "--workers", "-n",
        type=int,
        help="Number of parallel workers (default: auto-detect)"
    )
    
    parser.add_argument(
        "--coverage-threshold",
        type=int,
        default=80,
        help="Minimum coverage percentage (default: 80)"
    )
    
    parser.add_argument(
        "--max-failures",
        type=int,
        default=5,
        help="Maximum failures before stopping (default: 5)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout per test in seconds (default: 300)"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Reduce output verbosity"
    )
    
    parser.add_argument(
        "--no-html",
        action="store_true",
        help="Skip HTML report generation"
    )
    
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run performance benchmark comparing different worker counts"
    )
    
    args = parser.parse_args()
    
    print("StyleStack Parallel Test Runner")
    print("=" * 60)
    print(f"Platform: {platform.system()} {platform.machine()}")
    print(f"CPUs available: {multiprocessing.cpu_count()}")
    print(f"Python version: {sys.version}")
    
    try:
        if args.benchmark:
            # Run performance benchmark
            benchmark_results = run_performance_benchmark()
            
            # Also run regular tests
            print(f"\nRunning full test suite with optimal configuration...")
            test_results = run_test_suite(
                test_type=args.type,
                parallel_workers=args.workers,
                coverage_threshold=args.coverage_threshold,
                max_failures=args.max_failures,
                timeout=args.timeout,
                verbose=not args.quiet,
                generate_html_report=not args.no_html
            )
            
            generate_summary_report(test_results)
            
            # Save benchmark results
            reports_dir = create_reports_directory()
            benchmark_file = reports_dir / "benchmark-results.json"
            with open(benchmark_file, "w") as f:
                json.dump(benchmark_results, f, indent=2)
            
            print(f"\nBenchmark results saved to: {benchmark_file}")
            
        else:
            # Run regular tests
            results = run_test_suite(
                test_type=args.type,
                parallel_workers=args.workers,
                coverage_threshold=args.coverage_threshold,
                max_failures=args.max_failures,
                timeout=args.timeout,
                verbose=not args.quiet,
                generate_html_report=not args.no_html
            )
            
            generate_summary_report(results)
        
        # Exit with appropriate code
        if "success" in results:
            sys.exit(0 if results["success"] else 1)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nTest execution interrupted by user")
        sys.exit(130)
    
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()