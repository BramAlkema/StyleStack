#!/usr/bin/env python3
"""
Standalone Test Runner for Templating Comment Analysis

Validates that StyleStack has proper explanatory comments for templating functions
without requiring pytest installation.
"""

import sys
from pathlib import Path
from analyze_templating_comments import TemplatingCommentAnalyzer


class TemplatingCommentTester:
    """Test runner for templating comment analysis."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.analyzer = TemplatingCommentAnalyzer(self.project_root)
        self.test_results = []
        
    def run_test(self, test_name: str, test_func):
        """Run a single test and record results."""
        try:
            test_func()
            self.test_results.append((test_name, "PASS", ""))
            print(f"✅ {test_name}")
        except AssertionError as e:
            self.test_results.append((test_name, "FAIL", str(e)))
            print(f"❌ {test_name}: {e}")
        except Exception as e:
            self.test_results.append((test_name, "ERROR", str(e)))
            print(f"💥 {test_name}: {e}")
    
    def test_comment_analyzer_initialization(self):
        """Test that the comment analyzer initializes correctly."""
        assert self.analyzer.project_root.exists(), "Project root should exist"
        assert len(self.analyzer.COMMENT_REQUIREMENTS) > 0, "Should have comment requirements"
        assert len(self.analyzer.TEMPLATING_KEYWORDS) > 0, "Should have templating keywords"
    
    def test_templating_function_detection(self):
        """Test detection of templating-related functions."""
        import ast
        
        # Create mock function nodes for testing
        mock_node = ast.FunctionDef(
            name="test_func",
            args=ast.arguments(
                posonlyargs=[], args=[], vararg=None, kwonlyargs=[],
                kw_defaults=[], kwarg=None, defaults=[]
            ),
            body=[],
            decorator_list=[],
            returns=None,
            lineno=1
        )
        
        # Test that function names with templating keywords are detected
        assert self.analyzer._is_templating_function("apply_template_variables", mock_node)
        assert self.analyzer._is_templating_function("process_ooxml_content", mock_node)
        assert self.analyzer._is_templating_function("resolve_token_hierarchy", mock_node)
        
        # Test that non-templating functions are not detected
        assert not self.analyzer._is_templating_function("helper_function", mock_node)
    
    def test_templating_class_detection(self):
        """Test detection of templating-related classes."""
        assert self.analyzer._is_templating_class("TemplateProcessor")
        assert self.analyzer._is_templating_class("OOXMLHandler")
        assert self.analyzer._is_templating_class("VariableResolver")
        assert not self.analyzer._is_templating_class("UtilityHelper")
    
    def test_comment_extraction(self):
        """Test comment extraction from Python source code."""
        test_content = '''# This is a file header comment
def example_function():
    """This is a docstring."""
    # This is an inline comment
    x = 1  # End of line comment
    return x
'''
        comments = self.analyzer._extract_comments(test_content)
        
        assert len(comments) > 0, "Should extract at least one comment"
        assert 1 in comments, "Should extract header comment"
        assert comments[1] == "This is a file header comment", "Should extract correct comment text"
    
    def test_project_analysis_quality(self):
        """Test that the project has reasonable comment quality."""
        analysis = self.analyzer.analyze_project(max_files=20)  # Limit for test speed
        
        assert "files_analyzed" in analysis, "Analysis should include files_analyzed"
        assert "total_templating_functions" in analysis, "Analysis should include function count"
        assert "overall_score" in analysis, "Analysis should include overall score"
        assert 0 <= analysis["overall_score"] <= 100, "Score should be valid percentage"
        
        # The StyleStack codebase should have decent comment quality
        if analysis["total_templating_functions"] > 0:
            min_expected_score = 70.0  # Set reasonable expectations
            actual_score = analysis["overall_score"]
            
            print(f"  📊 Found {analysis['total_templating_functions']} templating functions")
            print(f"  📈 Comment quality score: {actual_score:.1f}%")
            
            assert actual_score >= min_expected_score, (
                f"Comment quality too low: {actual_score:.1f}% < {min_expected_score}%. "
                f"Consider improving templating function documentation."
            )
    
    def test_real_files_analysis(self):
        """Test analysis of actual StyleStack files."""
        tools_dir = self.project_root / "tools"
        if tools_dir.exists():
            # Find a file that should have templating functions
            ooxml_files = list(tools_dir.glob("*ooxml*.py")) + list(tools_dir.glob("*template*.py"))
            
            if ooxml_files:
                sample_file = ooxml_files[0]
                result = self.analyzer.analyze_file(sample_file)
                
                assert isinstance(result.file_path, str), "Should return file path"
                assert result.total_functions >= 0, "Should count functions"
                assert result.total_classes >= 0, "Should count classes"
                assert 0 <= result.score <= 100, "Score should be valid"
                
                print(f"  🔍 Analyzed {sample_file.name}: "
                      f"{result.templating_functions} templating functions, "
                      f"score: {result.score:.1f}%")
    
    def test_report_generation(self):
        """Test that comment analysis reports are generated correctly."""
        analysis = self.analyzer.analyze_project(max_files=10)
        report = self.analyzer.generate_comment_report(analysis)
        
        assert "StyleStack Templating Comment Analysis Report" in report
        assert "COMMENT ANALYSIS SUMMARY" in report
        assert "VIOLATIONS BY SEVERITY" in report
        assert "RECOMMENDATIONS" in report
        assert len(report) > 100, "Report should be substantial"
    
    def run_all_tests(self):
        """Run all templating comment tests."""
        print("🧪 Running StyleStack Templating Comment Tests")
        print("=" * 60)
        
        test_methods = [
            ("Comment Analyzer Initialization", self.test_comment_analyzer_initialization),
            ("Templating Function Detection", self.test_templating_function_detection),
            ("Templating Class Detection", self.test_templating_class_detection),
            ("Comment Extraction", self.test_comment_extraction),
            ("Project Analysis Quality", self.test_project_analysis_quality),
            ("Real Files Analysis", self.test_real_files_analysis),
            ("Report Generation", self.test_report_generation),
        ]
        
        for test_name, test_func in test_methods:
            self.run_test(test_name, test_func)
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, status, _ in self.test_results if status == "PASS")
        failed_tests = sum(1 for _, status, _ in self.test_results if status == "FAIL")
        error_tests = sum(1 for _, status, _ in self.test_results if status == "ERROR")
        
        print(f"\n📊 TEST SUMMARY")
        print(f"-" * 20)
        print(f"Total tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"💥 Errors: {error_tests}")
        
        if failed_tests > 0 or error_tests > 0:
            print(f"\n📋 FAILURES/ERRORS:")
            for test_name, status, message in self.test_results:
                if status in ["FAIL", "ERROR"]:
                    print(f"  {status}: {test_name}")
                    if message:
                        print(f"    {message}")
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        print(f"\n🎯 Success Rate: {success_rate:.1f}%")
        
        return failed_tests == 0 and error_tests == 0


def main():
    """Run templating comment tests."""
    tester = TemplatingCommentTester()
    
    success = tester.run_all_tests()
    
    if success:
        print(f"\n🎉 All templating comment tests passed!")
        print("StyleStack has proper explanatory comments for templating functions.")
        return 0
    else:
        print(f"\n⚠️  Some templating comment tests failed.")
        print("Consider improving explanatory comments for templating functions.")
        return 1


if __name__ == "__main__":
    exit(main())