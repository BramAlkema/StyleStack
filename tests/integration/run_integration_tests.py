#!/usr/bin/env python3
"""
StyleStack Integration Test Runner

Comprehensive test runner for the StyleStack JSON-to-OOXML Processing Engine integration tests.
Provides options for running different test suites, performance monitoring, and detailed reporting.
"""

import os
import sys
import argparse
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegrationTestRunner:
    """Manages execution of integration tests with various options."""
    
    def __init__(self, test_dir: Path):
        self.test_dir = test_dir
        self.fixtures_dir = test_dir / "fixtures"
        self.templates_dir = self.fixtures_dir / "templates"
        
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are available for running tests."""
        logger.info("Checking integration test prerequisites...")
        
        # Check if test templates exist
        required_templates = [
            "test_presentation.potx",
            "test_document.dotx", 
            "test_workbook.xltx",
            "large_test_presentation.potx"
        ]
        
        missing_templates = []
        for template in required_templates:
            if not (self.templates_dir / template).exists():
                missing_templates.append(template)
        
        if missing_templates:
            logger.error(f"Missing required test templates: {missing_templates}")
            logger.info("Run create_test_templates.py to generate required templates.")
            return False
        
        # Check if required Python packages are available
        required_packages = ["pytest", "lxml", "psutil"]
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"Missing required Python packages: {missing_packages}")
            logger.info(f"Install with: pip install {' '.join(missing_packages)}")
            return False
        
        logger.info("All prerequisites are available.")
        return True
    
    def create_test_templates(self) -> bool:
        """Create test templates if they don't exist."""
        logger.info("Creating test templates...")
        
        create_script = self.fixtures_dir / "create_test_templates.py"
        if not create_script.exists():
            logger.error(f"Template creation script not found: {create_script}")
            return False
        
        try:
            result = subprocess.run(
                [sys.executable, str(create_script)],
                cwd=self.fixtures_dir,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode != 0:
                logger.error(f"Template creation failed: {result.stderr}")
                return False
            
            logger.info("Test templates created successfully.")
            logger.info(result.stdout)
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Template creation timed out.")
            return False
        except Exception as e:
            logger.error(f"Error creating templates: {e}")
            return False
    
    def run_basic_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run basic integration tests."""
        logger.info("Running basic integration tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir / "test_e2e_ooxml_processing.py"),
            "-v" if verbose else "",
            "--tb=short",
            "--json-report",
            "--json-report-file=/tmp/basic_test_report.json"
        ]
        cmd = [arg for arg in cmd if arg]  # Remove empty strings
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = time.time() - start_time
        
        # Parse results
        try:
            with open("/tmp/basic_test_report.json", "r") as f:
                test_report = json.load(f)
        except:
            test_report = {}
        
        return {
            "success": result.returncode == 0,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "report": test_report
        }
    
    def run_advanced_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run advanced integration tests."""
        logger.info("Running advanced integration tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir / "test_advanced_integration_scenarios.py"),
            "-v" if verbose else "",
            "--tb=short", 
            "-m", "not stress",  # Skip stress tests by default
            "--json-report",
            "--json-report-file=/tmp/advanced_test_report.json"
        ]
        cmd = [arg for arg in cmd if arg]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = time.time() - start_time
        
        try:
            with open("/tmp/advanced_test_report.json", "r") as f:
                test_report = json.load(f)
        except:
            test_report = {}
        
        return {
            "success": result.returncode == 0,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "report": test_report
        }
    
    def run_stress_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run stress and performance tests."""
        logger.info("Running stress and performance tests...")
        
        cmd = [
            sys.executable, "-m", "pytest", 
            str(self.test_dir / "test_advanced_integration_scenarios.py"),
            "-v" if verbose else "",
            "--tb=short",
            "-m", "stress",
            "--json-report",
            "--json-report-file=/tmp/stress_test_report.json"
        ]
        cmd = [arg for arg in cmd if arg]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # 10 minute timeout
        duration = time.time() - start_time
        
        try:
            with open("/tmp/stress_test_report.json", "r") as f:
                test_report = json.load(f)
        except:
            test_report = {}
        
        return {
            "success": result.returncode == 0,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "report": test_report
        }
    
    def run_all_tests(self, verbose: bool = False, include_stress: bool = False) -> Dict[str, Any]:
        """Run all integration tests."""
        logger.info("Running comprehensive integration test suite...")
        
        test_files = [
            "test_e2e_ooxml_processing.py",
            "test_advanced_integration_scenarios.py"
        ]
        
        markers = []
        if not include_stress:
            markers.append("not stress")
        
        cmd = [
            sys.executable, "-m", "pytest"
        ] + [str(self.test_dir / f) for f in test_files] + [
            "-v" if verbose else "",
            "--tb=short",
            "-m", " and ".join(markers) if markers else "",
            "--json-report",
            "--json-report-file=/tmp/all_tests_report.json"
        ]
        cmd = [arg for arg in cmd if arg]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)  # 15 minute timeout
        duration = time.time() - start_time
        
        try:
            with open("/tmp/all_tests_report.json", "r") as f:
                test_report = json.load(f)
        except:
            test_report = {}
        
        return {
            "success": result.returncode == 0,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "report": test_report
        }
    
    def generate_summary_report(self, test_results: Dict[str, Dict[str, Any]]) -> str:
        """Generate a summary report of test results."""
        report_lines = [
            "=" * 80,
            "StyleStack Integration Test Summary Report", 
            "=" * 80,
            f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        total_duration = 0
        total_tests = 0
        total_passed = 0
        total_failed = 0
        
        for suite_name, results in test_results.items():
            report_lines.extend([
                f"Test Suite: {suite_name}",
                "-" * 40,
                f"Status: {'PASSED' if results['success'] else 'FAILED'}",
                f"Duration: {results['duration']:.2f}s",
            ])
            
            # Extract test statistics from report if available
            if 'report' in results and 'summary' in results['report']:
                summary = results['report']['summary']
                passed = summary.get('passed', 0)
                failed = summary.get('failed', 0)
                total = passed + failed
                
                report_lines.extend([
                    f"Tests Run: {total}",
                    f"Passed: {passed}",
                    f"Failed: {failed}",
                ])
                
                total_tests += total
                total_passed += passed
                total_failed += failed
            
            total_duration += results['duration']
            report_lines.append("")
        
        # Overall summary
        report_lines.extend([
            "=" * 40,
            "OVERALL SUMMARY",
            "=" * 40,
            f"Total Test Suites: {len(test_results)}",
            f"Total Tests: {total_tests}",
            f"Total Passed: {total_passed}", 
            f"Total Failed: {total_failed}",
            f"Total Duration: {total_duration:.2f}s",
            f"Success Rate: {(total_passed/total_tests*100):.1f}%" if total_tests > 0 else "N/A",
            ""
        ])
        
        # Add failure details if any
        for suite_name, results in test_results.items():
            if not results['success'] and results['stderr']:
                report_lines.extend([
                    f"FAILURES IN {suite_name}:",
                    "-" * 40,
                    results['stderr'][:2000],  # Limit error output
                    ""
                ])
        
        return "\n".join(report_lines)


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description="StyleStack Integration Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "test_suite", 
        nargs="?",
        choices=["basic", "advanced", "stress", "all"],
        default="basic",
        help="Test suite to run (default: basic)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--create-templates",
        action="store_true", 
        help="Create test templates before running tests"
    )
    
    parser.add_argument(
        "--include-stress",
        action="store_true",
        help="Include stress tests when running 'all' suite"
    )
    
    parser.add_argument(
        "--report-file",
        type=str,
        help="Save summary report to file"
    )
    
    args = parser.parse_args()
    
    # Initialize test runner
    test_dir = Path(__file__).parent
    runner = IntegrationTestRunner(test_dir)
    
    # Check prerequisites
    if not runner.check_prerequisites():
        if args.create_templates:
            if not runner.create_test_templates():
                sys.exit(1)
            # Recheck after creating templates
            if not runner.check_prerequisites():
                sys.exit(1)
        else:
            logger.error("Prerequisites not met. Use --create-templates to generate missing templates.")
            sys.exit(1)
    
    # Run selected test suite
    logger.info(f"Starting {args.test_suite} test suite...")
    test_results = {}
    
    try:
        if args.test_suite == "basic":
            test_results["basic"] = runner.run_basic_tests(args.verbose)
        elif args.test_suite == "advanced":
            test_results["advanced"] = runner.run_advanced_tests(args.verbose)
        elif args.test_suite == "stress":
            test_results["stress"] = runner.run_stress_tests(args.verbose)
        elif args.test_suite == "all":
            test_results["basic"] = runner.run_basic_tests(args.verbose)
            if test_results["basic"]["success"]:
                test_results["advanced"] = runner.run_advanced_tests(args.verbose)
                if args.include_stress:
                    test_results["stress"] = runner.run_stress_tests(args.verbose)
            else:
                logger.warning("Basic tests failed, skipping advanced tests.")
    
    except KeyboardInterrupt:
        logger.info("Test execution interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)
    
    # Generate and display summary report
    summary_report = runner.generate_summary_report(test_results)
    print("\n" + summary_report)
    
    # Save report to file if requested
    if args.report_file:
        with open(args.report_file, "w") as f:
            f.write(summary_report)
        logger.info(f"Summary report saved to: {args.report_file}")
    
    # Determine exit code
    overall_success = all(result["success"] for result in test_results.values())
    if overall_success:
        logger.info("All integration tests PASSED!")
        sys.exit(0)
    else:
        logger.error("Some integration tests FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    main()