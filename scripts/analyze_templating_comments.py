#!/usr/bin/env python3
"""
Standalone Templating Comment Analyzer

Analyzes StyleStack codebase for proper templating explanatory comments
without requiring pytest or other testing dependencies.
"""


from typing import Any, Dict, List
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
            if isinstance(child, ast.Constant) and isinstance(child.value, str):
                if any(keyword in child.value.lower() for keyword in ["xpath", "xml", "template", "ooxml"]):
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
                # More strict checking - require at least 2 keywords from the requirement list
                matched_keywords = []
                missing_keywords = []
                
                for keyword in req.required_keywords:
                    if keyword.lower() in comment_text:
                        matched_keywords.append(keyword)
                    else:
                        missing_keywords.append(keyword)
                
                # Require at least 3 matching keywords for proper documentation
                min_required = max(3, len(req.required_keywords) // 2)
                
                if len(matched_keywords) < min_required:
                    # Check if comment is substantial enough (more than just a docstring template)
                    has_substantial_comment = (
                        len(comment_text.strip()) > 80 and
                        any(explain_word in comment_text for explain_word in [
                            "applies", "processes", "transforms", "manipulates", "resolves",
                            "extracts", "validates", "handles", "parses", "generates"
                        ])
                    )
                    
                    # Debug output
                    print(f"  DEBUG: {name} - matched: {matched_keywords}, missing: {missing_keywords[:3]}")
                    print(f"         comment length: {len(comment_text.strip())}, substantial: {has_substantial_comment}")
                    
                    if not has_substantial_comment:
                        return {
                            "type": "insufficient_templating_comments",
                            "name": name,
                            "node_type": node_type,
                            "line": line_num,
                            "severity": req.severity,
                            "description": req.description,
                            "missing_keywords": missing_keywords[:3],  # Show top 3 missing
                            "matched_keywords": matched_keywords,
                            "has_any_comment": len(comment_text.strip()) > 0,
                            "comment_length": len(comment_text.strip())
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
            
            for i, violation in enumerate(analysis['violations'][:15], 1):
                severity_emoji = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(
                    violation['severity'], "🔵"
                )
                file_path = violation.get('file_path', 'Unknown')
                rel_path = str(Path(file_path).name) if file_path != 'Unknown' else 'Unknown'
                
                lines.append(f"{i:2d}. {severity_emoji} {violation['name']} ({violation['node_type']}) "
                           f"- Line {violation['line']}")
                lines.append(f"     Missing: {', '.join(violation['missing_keywords'])}")
                lines.append(f"     File: {rel_path}")
                lines.append("")
        
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


def main():
    """Run templating comment analysis."""
    project_root = Path(__file__).parent
    analyzer = TemplatingCommentAnalyzer(project_root)
    
    print("🔍 StyleStack Templating Comment Analyzer")
    print("=" * 50)
    
    # Test on our example file first
    test_file = project_root / "test_comment_examples.py"
    if test_file.exists():
        print(f"\n🧪 Testing comment detection on example file...")
        result = analyzer.analyze_file(test_file)
        print(f"Example file analysis:")
        print(f"  Templating functions: {result.templating_functions}")
        print(f"  Properly commented: {result.properly_commented_templating}")
        print(f"  Violations: {len(result.violations)}")
        
        if result.violations:
            print("  Detected violations:")
            for v in result.violations:
                print(f"    - {v['name']} ({v['severity']}): {v['description']}")
        print()
    
    analysis = analyzer.analyze_project(max_files=30)
    report = analyzer.generate_comment_report(analysis)
    
    print(report)
    
    # Save detailed report
    reports_dir = project_root / "reports"
    reports_dir.mkdir(exist_ok=True)
    report_file = reports_dir / "templating_comment_analysis.txt"
    report_file.write_text(report)
    
    print(f"\n📋 Detailed report saved to: {report_file}")
    
    return 0


if __name__ == "__main__":
    exit(main())