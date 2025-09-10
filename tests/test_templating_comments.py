#!/usr/bin/env python3
"""
Test Suite for Templating Explanatory Comments

This test suite validates that the StyleStack codebase contains proper
explanatory comments for templating functionality, ensuring code maintainability
and developer understanding of the OOXML template processing system.

Test Categories:
1. Variable processing comments
2. Template transformation comments  
3. OOXML manipulation comments
4. Token resolution comments
5. Extension system comments
"""


from typing import Any, Dict, List
import pytest
import ast
import re
from pathlib import Path
from dataclasses import dataclass


@dataclass
class CommentRequirement:
    """Requirements for explanatory comments in specific contexts."""
    pattern: str  # Regex pattern to match code constructs
    required_keywords: List[str]  # Keywords that should appear in nearby comments
    description: str  # Human description of the requirement
    severity: str = "error"  # "error", "warning", or "info"


@dataclass
class CommentAnalysisResult:
    """Result of analyzing comments in a file."""
    file_path: str
    total_functions: int
    commented_functions: int
    total_classes: int
    commented_classes: int
    templating_functions: int
    properly_commented_templating: int
    violations: List[Dict[str, Any]]
    score: float


class TemplatingCommentAnalyzer:
    """Analyzer for templating explanatory comments in Python code."""
    
    # Comment requirements for different templating contexts
    COMMENT_REQUIREMENTS = [
        CommentRequirement(
            pattern=r"def.*(?:variable|token|template).*\(",
            required_keywords=["variable", "token", "template", "OOXML", "resolve", "process"],
            description="Variable/token processing functions need explanatory comments",
            severity="error"
        ),
        CommentRequirement(
            pattern=r"def.*(?:apply|transform|substitute|replace).*\(",
            required_keywords=["apply", "transform", "XML", "OOXML", "template", "element"],
            description="Template transformation functions need explanatory comments", 
            severity="error"
        ),
        CommentRequirement(
            pattern=r"def.*(?:xpath|find|select).*\(",
            required_keywords=["XPath", "XML", "OOXML", "element", "namespace", "select"],
            description="OOXML XPath functions need explanatory comments",
            severity="error"
        ),
        CommentRequirement(
            pattern=r"def.*(?:extension|schema|validate).*\(",
            required_keywords=["extension", "schema", "validate", "OOXML", "structure"],
            description="Extension/schema functions need explanatory comments",
            severity="warning"
        ),
        CommentRequirement(
            pattern=r"class.*(?:Processor|Handler|Manager|Resolver).*:",
            required_keywords=["process", "handle", "manage", "resolve", "OOXML", "template"],
            description="Template processing classes need explanatory comments",
            severity="error"
        )
    ]
    
    # Keywords that indicate templating functionality
    TEMPLATING_KEYWORDS = {
        "variable", "token", "template", "ooxml", "xpath", "xml", "schema",
        "extension", "resolve", "substitute", "transform", "apply", "process",
        "namespace", "element", "attribute", "design", "theme"
    }
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results = []
        
    def analyze_file(self, file_path: Path) -> CommentAnalysisResult:
        """Analyze templating comments in a single Python file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except (SyntaxError, UnicodeDecodeError):
            return CommentAnalysisResult(
                file_path=str(file_path),
                total_functions=0, commented_functions=0,
                total_classes=0, commented_classes=0,
                templating_functions=0, properly_commented_templating=0,
                violations=[], score=0.0
            )
        
        # Extract comments and their line numbers
        comments = self._extract_comments(content)
        
        # Analyze AST nodes
        result = CommentAnalysisResult(
            file_path=str(file_path),
            total_functions=0, commented_functions=0,
            total_classes=0, commented_classes=0,
            templating_functions=0, properly_commented_templating=0,
            violations=[], score=0.0
        )
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                result.total_functions += 1
                self._analyze_function_comments(node, content, comments, result)
                
            elif isinstance(node, ast.ClassDef):
                result.total_classes += 1
                self._analyze_class_comments(node, content, comments, result)
        
        # Calculate overall score
        total_templating = max(1, result.templating_functions)
        result.score = (result.properly_commented_templating / total_templating) * 100
        
        return result
    
    def _extract_comments(self, content: str) -> Dict[int, str]:
        """Extract comments and their line numbers from Python source."""
        comments = {}
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('#'):
                # Extract comment text without the # prefix
                comment_text = stripped[1:].strip()
                comments[line_num] = comment_text
                
            # Also capture docstrings
            if '"""' in line or "'''" in line:
                # Simple docstring detection
                comments[line_num] = line.strip()
        
        return comments
    
    def _analyze_function_comments(self, node: ast.FunctionDef, content: str, 
                                 comments: Dict[int, str], result: CommentAnalysisResult):
        """Analyze comments for a function definition."""
        func_name = node.name
        start_line = node.lineno
        
        # Check if this is a templating-related function
        is_templating = self._is_templating_function(func_name, node)
        if is_templating:
            result.templating_functions += 1
        
        # Look for comments in the surrounding area (3 lines before to 5 lines after)
        nearby_comments = []
        for line_num in range(max(1, start_line - 3), start_line + 6):
            if line_num in comments:
                nearby_comments.append(comments[line_num])
        
        # Check for docstring
        has_docstring = (ast.get_docstring(node) is not None)
        
        # Combine all comments
        all_comment_text = ' '.join(nearby_comments).lower()
        if has_docstring:
            all_comment_text += ' ' + (ast.get_docstring(node) or '').lower()
        
        has_meaningful_comment = len(all_comment_text.strip()) > 10
        if has_meaningful_comment:
            result.commented_functions += 1
        
        # Check templating function requirements
        if is_templating:
            violation = self._check_templating_requirements(
                func_name, all_comment_text, start_line, "function"
            )
            
            if not violation:
                result.properly_commented_templating += 1
            else:
                result.violations.append(violation)
    
    def _analyze_class_comments(self, node: ast.ClassDef, content: str,
                              comments: Dict[int, str], result: CommentAnalysisResult):
        """Analyze comments for a class definition."""
        class_name = node.name
        start_line = node.lineno
        
        # Check if this is a templating-related class
        is_templating = self._is_templating_class(class_name)
        
        # Look for comments around class definition
        nearby_comments = []
        for line_num in range(max(1, start_line - 3), start_line + 6):
            if line_num in comments:
                nearby_comments.append(comments[line_num])
        
        # Check for docstring
        has_docstring = (ast.get_docstring(node) is not None)
        
        # Combine all comments
        all_comment_text = ' '.join(nearby_comments).lower()
        if has_docstring:
            all_comment_text += ' ' + (ast.get_docstring(node) or '').lower()
        
        has_meaningful_comment = len(all_comment_text.strip()) > 10
        if has_meaningful_comment:
            result.commented_classes += 1
        
        # Check templating class requirements  
        if is_templating:
            violation = self._check_templating_requirements(
                class_name, all_comment_text, start_line, "class"
            )
            
            if violation:
                result.violations.append(violation)
    
    def _is_templating_function(self, func_name: str, node: ast.FunctionDef) -> bool:
        """Check if a function is related to templating functionality."""
        func_name_lower = func_name.lower()
        
        # Check function name for templating keywords
        if any(keyword in func_name_lower for keyword in self.TEMPLATING_KEYWORDS):
            return True
        
        # Check function body for templating operations
        for child in ast.walk(node):
            if isinstance(child, ast.Str):
                if any(keyword in child.s.lower() for keyword in ["xpath", "xml", "template", "ooxml"]):
                    return True
            elif isinstance(child, ast.Name):
                if any(keyword in child.id.lower() for keyword in ["xml", "xpath", "template"]):
                    return True
        
        return False
    
    def _is_templating_class(self, class_name: str) -> bool:
        """Check if a class is related to templating functionality."""
        class_name_lower = class_name.lower()
        return any(keyword in class_name_lower for keyword in self.TEMPLATING_KEYWORDS)
    
    def _check_templating_requirements(self, name: str, comment_text: str, 
                                     line_num: int, node_type: str) -> Dict[str, Any]:
        """Check if templating function/class meets comment requirements."""
        name_lower = name.lower()
        
        # Find matching requirements
        for req in self.COMMENT_REQUIREMENTS:
            if re.search(req.pattern, f"{node_type} {name}(", re.IGNORECASE):
                # Check if required keywords are present in comments
                missing_keywords = []
                for keyword in req.required_keywords:
                    if keyword.lower() not in comment_text:
                        missing_keywords.append(keyword)
                
                if missing_keywords:
                    return {
                        "type": "missing_templating_comments",
                        "name": name,
                        "node_type": node_type,
                        "line": line_num,
                        "severity": req.severity,
                        "description": req.description,
                        "missing_keywords": missing_keywords,
                        "has_any_comment": len(comment_text.strip()) > 0
                    }
        
        return None
    
    def analyze_project(self, max_files: int = 50) -> Dict[str, Any]:
        """Analyze templating comments across the project."""
        python_files = list(self.project_root.glob("**/*.py"))
        python_files = [f for f in python_files if not any(excluded in str(f) for excluded in [
            ".venv", "venv", "__pycache__", ".git", "node_modules", "build", "dist"
        ])]
        
        print(f"📝 Analyzing templating comments in up to {max_files} Python files...")
        
        total_violations = []
        total_templating_functions = 0
        properly_commented_templating = 0
        
        for file_path in python_files[:max_files]:
            result = self.analyze_file(file_path)
            self.results.append(result)
            
            total_violations.extend(result.violations)
            total_templating_functions += result.templating_functions
            properly_commented_templating += result.properly_commented_templating
        
        # Calculate overall statistics
        overall_score = 0
        if total_templating_functions > 0:
            overall_score = (properly_commented_templating / total_templating_functions) * 100
        
        return {
            "files_analyzed": len(self.results),
            "total_templating_functions": total_templating_functions,
            "properly_commented_templating": properly_commented_templating,
            "total_violations": len(total_violations),
            "violations_by_severity": self._group_violations_by_severity(total_violations),
            "overall_score": overall_score,
            "violations": total_violations[:20]  # Top 20 violations
        }
    
    def _group_violations_by_severity(self, violations: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group violations by severity level."""
        counts = {"error": 0, "warning": 0, "info": 0}
        for violation in violations:
            severity = violation.get("severity", "info")
            counts[severity] = counts.get(severity, 0) + 1
        return counts
    
    def generate_comment_report(self, analysis: Dict[str, Any]) -> str:
        """Generate a detailed comment analysis report."""
        lines = []
        lines.append("StyleStack Templating Comment Analysis Report")
        lines.append("=" * 60)
        
        # Summary statistics
        lines.append(f"\n📊 COMMENT ANALYSIS SUMMARY")
        lines.append("-" * 30)
        lines.append(f"Files analyzed: {analysis['files_analyzed']}")
        lines.append(f"Templating functions found: {analysis['total_templating_functions']}")
        lines.append(f"Properly commented: {analysis['properly_commented_templating']}")
        lines.append(f"Overall comment quality score: {analysis['overall_score']:.1f}%")
        
        # Violations by severity
        violations_by_severity = analysis['violations_by_severity']
        lines.append(f"\n🚨 VIOLATIONS BY SEVERITY")
        lines.append("-" * 25)
        lines.append(f"🔴 Errors: {violations_by_severity.get('error', 0)}")
        lines.append(f"🟡 Warnings: {violations_by_severity.get('warning', 0)}")
        lines.append(f"🔵 Info: {violations_by_severity.get('info', 0)}")
        
        # Top violations
        if analysis['violations']:
            lines.append(f"\n🔍 TOP COMMENT VIOLATIONS")
            lines.append("-" * 30)
            
            for i, violation in enumerate(analysis['violations'][:10], 1):
                severity_emoji = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(
                    violation['severity'], "🔵"
                )
                lines.append(f"{i:2d}. {severity_emoji} {violation['name']} ({violation['node_type']}) "
                           f"- Line {violation['line']}")
                lines.append(f"     Missing: {', '.join(violation['missing_keywords'])}")
        
        # Recommendations
        lines.append(f"\n💡 RECOMMENDATIONS")
        lines.append("-" * 20)
        
        score = analysis['overall_score']
        if score < 60:
            lines.append("❌ Poor comment quality. Focus on adding explanatory comments to:")
            lines.append("   • Variable processing functions")
            lines.append("   • OOXML manipulation methods")
            lines.append("   • Template transformation logic")
        elif score < 80:
            lines.append("⚠️  Moderate comment quality. Consider improving:")
            lines.append("   • Function-level documentation")
            lines.append("   • Complex algorithm explanations")
        else:
            lines.append("✅ Good comment quality! Minor improvements:")
            lines.append("   • Add inline comments for complex logic")
            lines.append("   • Document edge cases and assumptions")
        
        return '\n'.join(lines)


@pytest.mark.unit
@pytest.mark.parallel_safe  
class TestTemplatingComments:
    """Test suite for templating explanatory comments."""
    
    def setup_method(self):
        """Set up test environment."""
        self.project_root = Path(__file__).parent.parent
        self.analyzer = TemplatingCommentAnalyzer(self.project_root)
    
    def test_comment_analyzer_initialization(self):
        """Test that the comment analyzer initializes correctly."""
        assert self.analyzer.project_root.exists()
        assert len(self.analyzer.COMMENT_REQUIREMENTS) > 0
        assert len(self.analyzer.TEMPLATING_KEYWORDS) > 0
    
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
        
        assert len(comments) > 0
        assert 1 in comments  # Header comment
        assert comments[1] == "This is a file header comment"
    
    def test_templating_function_detection(self):
        """Test detection of templating-related functions."""
        # Create a mock function node
        func_node = ast.FunctionDef(
            name="apply_template_variables",
            args=ast.arguments(
                posonlyargs=[], args=[], vararg=None, kwonlyargs=[],
                kw_defaults=[], kwarg=None, defaults=[]
            ),
            body=[],
            decorator_list=[],
            returns=None
        )
        
        is_templating = self.analyzer._is_templating_function("apply_template_variables", func_node)
        assert is_templating, "Should detect templating function by name"
        
        is_not_templating = self.analyzer._is_templating_function("helper_function", func_node)
        # This might be False depending on the function body analysis
    
    def test_templating_class_detection(self):
        """Test detection of templating-related classes."""
        assert self.analyzer._is_templating_class("TemplateProcessor")
        assert self.analyzer._is_templating_class("OOXMLHandler")
        assert self.analyzer._is_templating_class("VariableResolver")
        assert not self.analyzer._is_templating_class("UtilityHelper")
    
    def test_comment_requirement_matching(self):
        """Test that comment requirements match appropriate code patterns."""
        # Test variable processing function pattern
        matches_variable = any(
            re.search(req.pattern, "def process_variables(", re.IGNORECASE)
            for req in self.analyzer.COMMENT_REQUIREMENTS
        )
        assert matches_variable, "Should match variable processing functions"
        
        # Test class pattern
        matches_processor = any(
            re.search(req.pattern, "class TemplateProcessor:", re.IGNORECASE)
            for req in self.analyzer.COMMENT_REQUIREMENTS
        )
        assert matches_processor, "Should match processor classes"
    
    def test_analyze_sample_file(self):
        """Test analysis of a sample Python file with templating code."""
        # Find a real file from the tools directory to analyze
        tools_dir = self.project_root / "tools"
        if tools_dir.exists():
            python_files = list(tools_dir.glob("*.py"))
            if python_files:
                sample_file = python_files[0]
                result = self.analyzer.analyze_file(sample_file)
                
                assert isinstance(result, CommentAnalysisResult)
                assert result.file_path == str(sample_file)
                assert result.total_functions >= 0
                assert result.total_classes >= 0
                assert 0 <= result.score <= 100
    
    def test_project_analysis(self):
        """Test full project comment analysis."""
        analysis = self.analyzer.analyze_project(max_files=10)  # Limit for test speed
        
        assert "files_analyzed" in analysis
        assert "total_templating_functions" in analysis
        assert "overall_score" in analysis
        assert "violations" in analysis
        assert isinstance(analysis["violations"], list)
        
        # Score should be a valid percentage
        assert 0 <= analysis["overall_score"] <= 100
    
    def test_violation_severity_grouping(self):
        """Test grouping of violations by severity."""
        sample_violations = [
            {"severity": "error", "name": "test1"},
            {"severity": "warning", "name": "test2"},
            {"severity": "error", "name": "test3"},
        ]
        
        grouped = self.analyzer._group_violations_by_severity(sample_violations)
        
        assert grouped["error"] == 2
        assert grouped["warning"] == 1
        assert grouped["info"] == 0
    
    def test_report_generation(self):
        """Test comment analysis report generation."""
        # Run a small analysis
        analysis = self.analyzer.analyze_project(max_files=5)
        report = self.analyzer.generate_comment_report(analysis)
        
        assert "StyleStack Templating Comment Analysis Report" in report
        assert "COMMENT ANALYSIS SUMMARY" in report
        assert "VIOLATIONS BY SEVERITY" in report
        assert "RECOMMENDATIONS" in report
    
    @pytest.mark.slow
    def test_full_project_comment_analysis(self):
        """Test comprehensive comment analysis of the entire project."""
        analysis = self.analyzer.analyze_project(max_files=30)
        report = self.analyzer.generate_comment_report(analysis)
        
        # Save report to file for manual inspection
        reports_dir = self.project_root / "reports"
        reports_dir.mkdir(exist_ok=True)
        report_file = reports_dir / "templating_comment_analysis.txt"
        report_file.write_text(report)
        
        print(f"\n📋 Comment analysis report saved to: {report_file}")
        
        # Assertions for minimum code quality
        assert analysis["files_analyzed"] > 0, "Should analyze at least some files"
        
        if analysis["total_templating_functions"] > 0:
            # At least 50% of templating functions should have proper comments
            min_expected_score = 50.0
            actual_score = analysis["overall_score"]
            
            if actual_score < min_expected_score:
                print(f"⚠️  Comment quality below expectations: {actual_score:.1f}% < {min_expected_score}%")
                print("Top violations:")
                for violation in analysis["violations"][:5]:
                    print(f"  - {violation['name']} ({violation['severity']})")
            
            # This assertion might fail initially - that's the point!
            # It identifies where we need to add better comments
            assert actual_score >= min_expected_score or len(analysis["violations"]) < 20, (
                f"Templating comment quality too low: {actual_score:.1f}%. "
                f"Found {len(analysis['violations'])} violations. "
                "Consider adding explanatory comments to templating functions."
            )


if __name__ == "__main__":
    # Run comment analysis as a standalone script
    project_root = Path(__file__).parent.parent
    analyzer = TemplatingCommentAnalyzer(project_root)
    
    print("🔍 StyleStack Templating Comment Analyzer")
    print("=" * 50)
    
    analysis = analyzer.analyze_project(max_files=25)
    report = analyzer.generate_comment_report(analysis)
    
    print(report)
    
    # Save detailed report
    reports_dir = project_root / "reports"
    reports_dir.mkdir(exist_ok=True)
    report_file = reports_dir / "templating_comment_analysis.txt"
    report_file.write_text(report)
    
    print(f"\n📋 Detailed report saved to: {report_file}")