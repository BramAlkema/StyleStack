#!/usr/bin/env python3
"""
Test Quality Validation Package

Provides comprehensive test quality validation capabilities including:
- Coverage quality analysis
- Best practice adherence checking
- Test maintainability scoring
- Performance validation
- Regression detection

Key components:
- TestQualityValidator: Main validation orchestrator
- TestAnalyzer: Analyzes test structure and metrics
- CoverageAnalyzer: Measures and validates coverage improvements
- BestPracticeChecker: Validates adherence to testing best practices

Usage:
    from tests.quality import TestQualityValidator
    
    validator = TestQualityValidator(Path.cwd())
    result = validator.validate_test_file(test_file)
    
    if result.passed:
        print(f"Test quality validation passed: +{result.metrics.coverage_increase:.2f}% coverage")

Part of StyleStack 90% Coverage Initiative - Phase 1: Foundation Testing
"""

from .validation_framework import (
    # Data structures
    TestQualityMetrics,
    TestValidationResult,
    
    # Core analyzers
    TestAnalyzer,
    CoverageAnalyzer, 
    BestPracticeChecker,
    
    # Main validator
    TestQualityValidator,
)

__all__ = [
    'TestQualityMetrics',
    'TestValidationResult',
    'TestAnalyzer',
    'CoverageAnalyzer',
    'BestPracticeChecker',
    'TestQualityValidator',
]