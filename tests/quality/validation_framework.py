#!/usr/bin/env python3
"""
Test Quality Validation Framework

Ensures that tests added to the StyleStack test suite maintain high quality,
provide meaningful coverage, and follow established best practices.

Key Features:
- Test coverage quality analysis
- Test performance validation
- Best practice adherence checking
- Regression detection
- Test maintainability scoring

Part of StyleStack 90% Coverage Initiative - Phase 1: Foundation Testing
"""

import ast
import time
import re
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict
import json


@dataclass
class TestQualityMetrics:
    """Metrics for test quality assessment"""
    coverage_increase: float = 0.0
    test_count: int = 0
    assertion_count: int = 0
    mock_usage_count: int = 0
    fixture_usage_count: int = 0
    execution_time: float = 0.0
    cyclomatic_complexity: int = 0
    maintainability_score: float = 0.0
    best_practices_score: float = 0.0
    regression_risk: str = "low"


@dataclass
class TestValidationResult:
    """Result of test quality validation"""
    test_file: str
    passed: bool
    metrics: TestQualityMetrics
    issues: List[str]
    recommendations: List[str]
    coverage_report: Dict[str, Any]


class TestAnalyzer:
    """Analyzes test files for quality metrics"""
    
    def __init__(self):
        self.python_ast_patterns = {
            'assertions': ['assert', 'assertEqual', 'assertTrue', 'assertFalse', 'assertIn'],
            'mocks': ['Mock', 'MagicMock', 'patch', '@patch', 'mock_', '.mock'],
            'fixtures': ['fixture', '@pytest.fixture', 'get_fixture'],
            'test_methods': ['def test_', 'class Test']
        }
    
    def analyze_test_file(self, test_file: Path) -> TestQualityMetrics:
        """Analyze a single test file for quality metrics"""
        if not test_file.exists():
            return TestQualityMetrics()
        
        content = test_file.read_text()
        tree = ast.parse(content)
        
        metrics = TestQualityMetrics()
        
        # Count test methods and classes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                metrics.test_count += 1
                metrics.cyclomatic_complexity += self._calculate_complexity(node)
            
            elif isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
                # Count methods in test class
                test_methods = [n for n in node.body if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]
                metrics.test_count += len(test_methods)
            
            elif isinstance(node, ast.Assert):
                metrics.assertion_count += 1
        
        # Count pattern usage in content
        for pattern_type, patterns in self.python_ast_patterns.items():
            for pattern in patterns:
                count = content.count(pattern)
                if pattern_type == 'mocks':
                    metrics.mock_usage_count += count
                elif pattern_type == 'fixtures':
                    metrics.fixture_usage_count += count
        
        # Calculate maintainability score
        metrics.maintainability_score = self._calculate_maintainability(content, metrics)
        
        return metrics
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _calculate_maintainability(self, content: str, metrics: TestQualityMetrics) -> float:
        """Calculate maintainability score based on various factors"""
        score = 100.0  # Start with perfect score
        
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        # Penalize for lack of documentation
        docstring_lines = len([line for line in lines if '"""' in line or "'''" in line])
        if docstring_lines < metrics.test_count * 2:  # Each test should have docstring
            score -= 10.0
        
        # Penalize for very long functions
        avg_function_length = len(non_empty_lines) / max(metrics.test_count, 1)
        if avg_function_length > 20:
            score -= 15.0
        
        # Penalize for high complexity
        if metrics.cyclomatic_complexity > metrics.test_count * 3:
            score -= 20.0
        
        # Reward for good assertion coverage
        if metrics.assertion_count >= metrics.test_count * 2:
            score += 5.0
        
        # Reward for fixture usage (indicates good test structure)
        if metrics.fixture_usage_count > 0:
            score += 5.0
        
        return max(0.0, min(100.0, score))


class CoverageAnalyzer:
    """Analyzes test coverage quality and improvement"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
    
    def measure_coverage_before_after(self, test_file: Path) -> Tuple[float, float, Dict]:
        """Measure coverage before and after adding a test file"""
        # Temporarily rename test file to measure baseline
        temp_name = test_file.with_suffix('.py.temp')
        coverage_before = 0.0
        coverage_after = 0.0
        detailed_report = {}
        
        try:
            if test_file.exists():
                test_file.rename(temp_name)
            
            # Measure coverage without the test
            coverage_before = self._run_coverage_measurement()
            
            # Restore test file and measure with it
            if temp_name.exists():
                temp_name.rename(test_file)
            coverage_after = self._run_coverage_measurement()
            
            # Get detailed coverage report
            detailed_report = self._get_detailed_coverage()
        
        except Exception as e:
            print(f"Warning: Coverage measurement failed: {e}")
            # Restore file if something went wrong
            if temp_name.exists():
                temp_name.rename(test_file)
        
        return coverage_before, coverage_after, detailed_report
    
    def _run_coverage_measurement(self) -> float:
        """Run pytest with coverage and return overall percentage"""
        try:
            result = subprocess.run([
                'python', '-m', 'pytest', '--cov=tools', '--cov-report=term', 
                '--tb=no', '-q', '--disable-warnings'
            ], cwd=self.project_root, capture_output=True, text=True, timeout=30)
            
            # Parse coverage percentage from output
            for line in result.stdout.split('\n'):
                if 'TOTAL' in line and '%' in line:
                    # Extract percentage (e.g., "TOTAL    1234    567    89%")
                    parts = line.split()
                    for part in parts:
                        if part.endswith('%'):
                            return float(part[:-1])
            
            return 0.0
        except (subprocess.TimeoutExpired, ValueError, subprocess.CalledProcessError):
            return 0.0
    
    def _get_detailed_coverage(self) -> Dict[str, Any]:
        """Get detailed coverage report"""
        try:
            result = subprocess.run([
                'python', '-m', 'pytest', '--cov=tools', '--cov-report=json', 
                '--tb=no', '-q', '--disable-warnings'
            ], cwd=self.project_root, capture_output=True, text=True, timeout=30)
            
            # Look for coverage.json file
            coverage_file = self.project_root / 'coverage.json'
            if coverage_file.exists():
                with open(coverage_file) as f:
                    return json.load(f)
        
        except Exception:
            pass
        
        return {}


class BestPracticeChecker:
    """Checks test files for adherence to best practices"""
    
    def __init__(self):
        self.best_practices = {
            'descriptive_names': self._check_descriptive_names,
            'single_assertion_focus': self._check_single_assertion_focus,
            'proper_setup_teardown': self._check_setup_teardown,
            'avoid_hardcoded_values': self._check_hardcoded_values,
            'mock_external_dependencies': self._check_mock_usage,
            'test_isolation': self._check_test_isolation,
            'documentation': self._check_documentation
        }
    
    def check_test_file(self, test_file: Path) -> Tuple[float, List[str]]:
        """Check test file against best practices"""
        if not test_file.exists():
            return 0.0, ["Test file does not exist"]
        
        content = test_file.read_text()
        issues = []
        score = 0.0
        
        for practice_name, checker in self.best_practices.items():
            try:
                passed, specific_issues = checker(content, test_file)
                if passed:
                    score += (100.0 / len(self.best_practices))
                else:
                    issues.extend([f"{practice_name}: {issue}" for issue in specific_issues])
            except Exception as e:
                issues.append(f"{practice_name}: Check failed - {e}")
        
        return score, issues
    
    def _check_descriptive_names(self, content: str, test_file: Path) -> Tuple[bool, List[str]]:
        """Check for descriptive test names"""
        issues = []
        
        # Find test method names
        test_methods = re.findall(r'def (test_\w+)', content)
        
        for method in test_methods:
            if len(method) < 15:  # Very short names
                issues.append(f"Test method '{method}' name too short (< 15 chars)")
            
            if '_' not in method[5:]:  # Only 'test_' prefix, no descriptive words
                issues.append(f"Test method '{method}' lacks descriptive name")
        
        return len(issues) == 0, issues
    
    def _check_single_assertion_focus(self, content: str, test_file: Path) -> Tuple[bool, List[str]]:
        """Check that tests focus on single concerns"""
        issues = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    assert_count = sum(1 for child in ast.walk(node) if isinstance(child, ast.Assert))
                    
                    if assert_count > 5:  # Too many assertions might indicate unfocused test
                        issues.append(f"Test '{node.name}' has {assert_count} assertions (consider splitting)")
        
        except SyntaxError:
            issues.append("Could not parse test file for assertion analysis")
        
        return len(issues) == 0, issues
    
    def _check_setup_teardown(self, content: str, test_file: Path) -> Tuple[bool, List[str]]:
        """Check for proper setup and teardown patterns"""
        issues = []
        
        has_fixtures = 'fixture' in content or '@pytest.fixture' in content
        has_setup_methods = 'def setup_' in content or 'def teardown_' in content
        has_temp_resources = any(pattern in content for pattern in ['tempfile', 'temp_dir', 'mkdtemp'])
        
        if has_temp_resources and not (has_fixtures or has_setup_methods):
            issues.append("Test creates temporary resources but lacks proper cleanup mechanisms")
        
        # Check for direct file system operations without cleanup
        if 'open(' in content and 'close()' not in content and 'with open(' not in content:
            issues.append("Test opens files without ensuring proper closure")
        
        return len(issues) == 0, issues
    
    def _check_hardcoded_values(self, content: str, test_file: Path) -> Tuple[bool, List[str]]:
        """Check for excessive hardcoded values"""
        issues = []
        
        # Look for suspicious hardcoded patterns
        suspicious_patterns = [
            (r'\b\d{4}-\d{2}-\d{2}\b', 'hardcoded dates'),
            (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', 'hardcoded IP addresses'),
            (r'(?i)password\s*=\s*["\'][^"\']+["\']', 'hardcoded passwords'),
            (r'/[^/\s]+/[^/\s]+/[^/\s]+/', 'hardcoded paths')
        ]
        
        for pattern, description in suspicious_patterns:
            matches = re.findall(pattern, content)
            if matches:
                issues.append(f"Found potential {description}: {len(matches)} occurrences")
        
        return len(issues) == 0, issues
    
    def _check_mock_usage(self, content: str, test_file: Path) -> Tuple[bool, List[str]]:
        """Check for appropriate mock usage"""
        issues = []
        
        # Check for external dependencies that should be mocked
        external_patterns = ['requests.', 'urllib.', 'subprocess.', 'os.system', 'git.Repo']
        mock_patterns = ['Mock', 'patch', '@patch', 'mock_']
        
        has_external = any(pattern in content for pattern in external_patterns)
        has_mocks = any(pattern in content for pattern in mock_patterns)
        
        if has_external and not has_mocks:
            issues.append("Test uses external dependencies but lacks proper mocking")
        
        return len(issues) == 0, issues
    
    def _check_test_isolation(self, content: str, test_file: Path) -> Tuple[bool, List[str]]:
        """Check for test isolation issues"""
        issues = []
        
        # Check for global state modifications
        global_patterns = ['global ', 'os.environ[', 'sys.path.']
        
        for pattern in global_patterns:
            if pattern in content and 'patch' not in content:
                issues.append(f"Test modifies global state ({pattern}) without proper isolation")
        
        return len(issues) == 0, issues
    
    def _check_documentation(self, content: str, test_file: Path) -> Tuple[bool, List[str]]:
        """Check for adequate documentation"""
        issues = []
        
        lines = content.split('\n')
        docstring_lines = [line for line in lines if '"""' in line or "'''" in line]
        test_methods = re.findall(r'def (test_\w+)', content)
        
        if len(docstring_lines) < len(test_methods):
            issues.append(f"Only {len(docstring_lines)} docstrings for {len(test_methods)} test methods")
        
        # Check for class-level documentation
        if 'class Test' in content and not any('class' in line and '"""' in content[content.index(line):content.index(line)+200] for line in lines if 'class Test' in line):
            issues.append("Test classes lack documentation")
        
        return len(issues) == 0, issues


class TestQualityValidator:
    """Main validator that orchestrates all quality checks"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.analyzer = TestAnalyzer()
        self.coverage_analyzer = CoverageAnalyzer(project_root)
        self.best_practice_checker = BestPracticeChecker()
    
    def validate_test_file(self, test_file: Path) -> TestValidationResult:
        """Perform comprehensive validation of a test file"""
        print(f"🔍 Validating test quality: {test_file.name}")
        
        start_time = time.time()
        
        # Analyze test structure and metrics
        metrics = self.analyzer.analyze_test_file(test_file)
        
        # Measure coverage impact
        coverage_before, coverage_after, detailed_coverage = self.coverage_analyzer.measure_coverage_before_after(test_file)
        metrics.coverage_increase = coverage_after - coverage_before
        
        # Check best practices
        best_practices_score, best_practice_issues = self.best_practice_checker.check_test_file(test_file)
        metrics.best_practices_score = best_practices_score
        
        # Calculate execution time
        metrics.execution_time = time.time() - start_time
        
        # Determine overall pass/fail
        issues = best_practice_issues.copy()
        recommendations = []
        
        # Add recommendations based on metrics
        if metrics.coverage_increase < 1.0:
            recommendations.append(f"Coverage increase is only {metrics.coverage_increase:.2f}% - consider adding more comprehensive tests")
        
        if metrics.assertion_count < metrics.test_count:
            recommendations.append("Consider adding more assertions to increase test thoroughness")
        
        if metrics.mock_usage_count == 0 and any(pattern in test_file.read_text() for pattern in ['requests', 'subprocess', 'git']):
            recommendations.append("Consider mocking external dependencies for better test isolation")
        
        if metrics.maintainability_score < 70:
            recommendations.append("Consider refactoring tests for better maintainability")
        
        # Determine pass/fail criteria
        passed = (
            metrics.coverage_increase > 0.1 or  # Some coverage improvement OR
            len(issues) == 0  # No best practice violations
        )
        
        return TestValidationResult(
            test_file=str(test_file),
            passed=passed,
            metrics=metrics,
            issues=issues,
            recommendations=recommendations,
            coverage_report=detailed_coverage
        )
    
    def validate_test_directory(self, test_dir: Path) -> List[TestValidationResult]:
        """Validate all test files in a directory"""
        results = []
        
        test_files = list(test_dir.glob('test_*.py'))
        if not test_files:
            print(f"⚠️  No test files found in {test_dir}")
            return results
        
        print(f"🔍 Validating {len(test_files)} test files in {test_dir}")
        
        for test_file in test_files:
            try:
                result = self.validate_test_file(test_file)
                results.append(result)
                
                # Print summary
                status = "✅ PASS" if result.passed else "❌ FAIL"
                print(f"  {status} {test_file.name} (+{result.metrics.coverage_increase:.2f}% coverage)")
                
            except Exception as e:
                print(f"  ❌ ERROR validating {test_file.name}: {e}")
                results.append(TestValidationResult(
                    test_file=str(test_file),
                    passed=False,
                    metrics=TestQualityMetrics(),
                    issues=[f"Validation error: {e}"],
                    recommendations=[],
                    coverage_report={}
                ))
        
        return results
    
    def generate_quality_report(self, results: List[TestValidationResult]) -> Dict[str, Any]:
        """Generate comprehensive quality report"""
        total_tests = sum(r.metrics.test_count for r in results)
        total_assertions = sum(r.metrics.assertion_count for r in results)
        total_coverage_increase = sum(r.metrics.coverage_increase for r in results)
        passed_validations = len([r for r in results if r.passed])
        
        return {
            'summary': {
                'total_test_files': len(results),
                'total_test_methods': total_tests,
                'total_assertions': total_assertions,
                'total_coverage_increase': round(total_coverage_increase, 2),
                'passed_validations': passed_validations,
                'validation_success_rate': round(passed_validations / len(results) * 100, 1) if results else 0
            },
            'metrics': {
                'avg_maintainability_score': round(sum(r.metrics.maintainability_score for r in results) / len(results), 1) if results else 0,
                'avg_best_practices_score': round(sum(r.metrics.best_practices_score for r in results) / len(results), 1) if results else 0,
                'avg_coverage_increase': round(total_coverage_increase / len(results), 2) if results else 0
            },
            'detailed_results': [
                {
                    'file': r.test_file,
                    'passed': r.passed,
                    'coverage_increase': r.metrics.coverage_increase,
                    'test_count': r.metrics.test_count,
                    'maintainability_score': r.metrics.maintainability_score,
                    'issues_count': len(r.issues),
                    'recommendations_count': len(r.recommendations)
                }
                for r in results
            ]
        }


if __name__ == '__main__':
    # Demonstrate the validation framework
    print("Testing Test Quality Validation Framework...")
    
    project_root = Path.cwd()
    validator = TestQualityValidator(project_root)
    
    # Test on a sample test file
    sample_test = project_root / 'tests' / 'test_concurrent_processing_validator_comprehensive.py'
    if sample_test.exists():
        result = validator.validate_test_file(sample_test)
        print(f"✅ Sample validation complete:")
        print(f"   Coverage increase: +{result.metrics.coverage_increase:.2f}%")
        print(f"   Test count: {result.metrics.test_count}")
        print(f"   Maintainability: {result.metrics.maintainability_score:.1f}/100")
        print(f"   Best practices: {result.metrics.best_practices_score:.1f}/100")
        print(f"   Status: {'PASS' if result.passed else 'FAIL'}")
    
    print("✅ Test Quality Validation Framework operational")