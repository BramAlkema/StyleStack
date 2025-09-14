#!/usr/bin/env python3
"""
StyleStack Coverage Analysis

This script provides detailed coverage analysis including gap identification,
trend tracking, and recommendations for improving test coverage.
"""


from typing import Any, Dict, List, Optional
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import subprocess
import sys
import argparse
from datetime import datetime
import csv


class CoverageAnalyzer:
    """Analyze test coverage data and provide insights."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.tools_dir = self.project_root / "tools"
        self.coverage_dir = self.project_root / "htmlcov"
        self.reports_dir = self.project_root / "reports"
        
    def discover_modules(self) -> List[Dict[str, Any]]:
        """Discover all Python modules in the tools directory."""
        modules = []
        
        if not self.tools_dir.exists():
            return modules
            
        for py_file in self.tools_dir.glob("**/*.py"):
            if py_file.name == "__init__.py":
                continue
                
            # Calculate relative path and module info
            relative_path = py_file.relative_to(self.tools_dir)
            module_path = str(relative_path.with_suffix(""))
            
            # Get file stats
            stats = py_file.stat()
            
            modules.append({
                "file_path": str(py_file),
                "relative_path": str(relative_path),
                "module_path": module_path.replace("/", "."),
                "name": py_file.stem,
                "size_bytes": stats.st_size,
                "modified_time": datetime.fromtimestamp(stats.st_mtime),
                "category": self._categorize_module(py_file)
            })
        
        return sorted(modules, key=lambda x: x["relative_path"])
    
    def _categorize_module(self, py_file: Path) -> str:
        """Categorize module based on name and location."""
        name = py_file.stem.lower()
        
        if any(keyword in name for keyword in ["test", "tests"]):
            return "test"
        elif any(keyword in name for keyword in ["ooxml", "processor", "parser"]):
            return "core"
        elif any(keyword in name for keyword in ["token", "design", "variable"]):
            return "tokens"
        elif any(keyword in name for keyword in ["template", "patch"]):
            return "templates"
        elif any(keyword in name for keyword in ["integration", "pipeline"]):
            return "integration"
        else:
            return "utility"
    
    def load_coverage_data(self) -> Optional[Dict[str, Any]]:
        """Load coverage data from various sources."""
        coverage_data = {}
        
        # Try to load JSON coverage report
        json_file = self.project_root / "coverage.json"
        if json_file.exists():
            try:
                with open(json_file, "r") as f:
                    json_data = json.load(f)
                    coverage_data["json"] = json_data
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Try to load XML coverage report
        xml_file = self.project_root / "coverage.xml"
        if xml_file.exists():
            try:
                tree = ET.parse(xml_file)
                coverage_data["xml"] = tree
            except ET.ParseError:
                pass
        
        # Check for HTML coverage report
        if self.coverage_dir.exists():
            coverage_data["html_available"] = True
            coverage_data["html_index"] = self.coverage_dir / "index.html"
        
        return coverage_data if coverage_data else None
    
    def analyze_coverage_gaps(self, coverage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze coverage gaps and identify untested modules."""
        
        modules = self.discover_modules()
        analysis = {
            "total_modules": len(modules),
            "covered_modules": 0,
            "uncovered_modules": [],
            "low_coverage_modules": [],
            "coverage_by_category": {},
            "recommendations": []
        }
        
        # Extract file coverage information
        covered_files = set()
        file_coverage = {}
        
        if "json" in coverage_data:
            json_data = coverage_data["json"]
            if "files" in json_data:
                for file_path, file_data in json_data["files"].items():
                    covered_files.add(file_path)
                    if "summary" in file_data:
                        coverage_percent = file_data["summary"].get("percent_covered", 0)
                        file_coverage[file_path] = coverage_percent
        
        elif "xml" in coverage_data:
            root = coverage_data["xml"].getroot()
            for package in root.findall(".//package"):
                for class_elem in package.findall(".//class"):
                    filename = class_elem.get("filename", "")
                    if filename:
                        covered_files.add(filename)
                        
                        line_rate = class_elem.get("line-rate", "0")
                        coverage_percent = float(line_rate) * 100
                        file_coverage[filename] = coverage_percent
        
        # Analyze each module
        for module in modules:
            file_path = module["file_path"]
            category = module["category"]
            
            # Initialize category tracking
            if category not in analysis["coverage_by_category"]:
                analysis["coverage_by_category"][category] = {
                    "total": 0,
                    "covered": 0,
                    "avg_coverage": 0,
                    "files": []
                }
            
            analysis["coverage_by_category"][category]["total"] += 1
            
            # Check if module is covered
            is_covered = any(file_path in covered_file or covered_file in file_path 
                           for covered_file in covered_files)
            
            if is_covered:
                analysis["covered_modules"] += 1
                analysis["coverage_by_category"][category]["covered"] += 1
                
                # Find coverage percentage
                coverage_percent = 0
                for covered_file, percent in file_coverage.items():
                    if file_path in covered_file or covered_file in file_path:
                        coverage_percent = percent
                        break
                
                analysis["coverage_by_category"][category]["files"].append({
                    "name": module["name"],
                    "path": file_path,
                    "coverage": coverage_percent
                })
                
                # Check for low coverage
                if coverage_percent < 70:
                    analysis["low_coverage_modules"].append({
                        "name": module["name"],
                        "path": file_path,
                        "coverage": coverage_percent,
                        "category": category
                    })
            else:
                analysis["uncovered_modules"].append({
                    "name": module["name"],
                    "path": file_path,
                    "category": category,
                    "size_bytes": module["size_bytes"]
                })
        
        # Calculate average coverage by category
        for category_data in analysis["coverage_by_category"].values():
            if category_data["files"]:
                total_coverage = sum(f["coverage"] for f in category_data["files"])
                category_data["avg_coverage"] = total_coverage / len(category_data["files"])
        
        # Generate recommendations
        analysis["recommendations"] = self._generate_coverage_recommendations(analysis)
        
        return analysis
    
    def _generate_coverage_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate coverage improvement recommendations."""
        recommendations = []
        
        # Overall coverage
        total_modules = analysis["total_modules"]
        covered_modules = analysis["covered_modules"]
        
        if total_modules > 0:
            coverage_ratio = covered_modules / total_modules
            if coverage_ratio < 0.7:
                recommendations.append(
                    f"Overall module coverage is {coverage_ratio:.1%}. "
                    f"Consider adding tests for {total_modules - covered_modules} uncovered modules."
                )
        
        # Category-specific recommendations
        for category, data in analysis["coverage_by_category"].items():
            if data["total"] > 0:
                category_ratio = data["covered"] / data["total"]
                if category_ratio < 0.8:
                    recommendations.append(
                        f"{category.capitalize()} modules have {category_ratio:.1%} coverage. "
                        f"Focus on testing {category} functionality."
                    )
        
        # Low coverage recommendations
        if analysis["low_coverage_modules"]:
            low_count = len(analysis["low_coverage_modules"])
            recommendations.append(
                f"{low_count} modules have coverage below 70%. "
                f"Prioritize improving tests for these modules."
            )
        
        # Large uncovered modules
        large_uncovered = [
            m for m in analysis["uncovered_modules"] 
            if m["size_bytes"] > 2000  # Files larger than 2KB
        ]
        
        if large_uncovered:
            recommendations.append(
                f"{len(large_uncovered)} large modules lack test coverage. "
                f"These should be high priority for test creation."
            )
        
        return recommendations
    
    def generate_coverage_report(self, analysis: Dict[str, Any]) -> str:
        """Generate a formatted coverage analysis report."""
        
        report = []
        report.append("StyleStack Coverage Analysis Report")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}")
        report.append("")
        
        # Summary statistics
        report.append("SUMMARY")
        report.append("-" * 20)
        report.append(f"Total modules: {analysis["total_modules"]}")
        report.append(f"Covered modules: {analysis["covered_modules"]}")
        report.append(f"Uncovered modules: {len(analysis["uncovered_modules"])}")
        report.append(f"Low coverage modules (<70%): {len(analysis["low_coverage_modules"])}")
        
        if analysis["total_modules"] > 0:
            overall_ratio = analysis["covered_modules"] / analysis["total_modules"]
            report.append(f"Overall coverage ratio: {overall_ratio:.1%}")
        
        report.append("")
        
        # Coverage by category
        report.append("COVERAGE BY CATEGORY")
        report.append("-" * 30)
        
        for category, data in analysis["coverage_by_category"].items():
            if data["total"] > 0:
                ratio = data["covered"] / data["total"]
                report.append(f"{category.capitalize():>12}: "
                            f"{data["covered"]:>2}/{data["total"]:>2} "
                            f"({ratio:>6.1%}) "
                            f"avg: {data["avg_coverage"]:>5.1f}%")
        
        report.append("")
        
        # Uncovered modules
        if analysis["uncovered_modules"]:
            report.append("UNCOVERED MODULES")
            report.append("-" * 25)
            
            for module in analysis["uncovered_modules"][:10]:  # Show top 10
                size_kb = module["size_bytes"] / 1024
                report.append(f"  {module["name"]:30} "
                            f"({module["category"]:>10}) "
                            f"{size_kb:>6.1f}KB")
            
            if len(analysis["uncovered_modules"]) > 10:
                remaining = len(analysis["uncovered_modules"]) - 10
                report.append(f"  ... and {remaining} more modules")
            
            report.append("")
        
        # Low coverage modules
        if analysis["low_coverage_modules"]:
            report.append("LOW COVERAGE MODULES (<70%)")
            report.append("-" * 35)
            
            sorted_low = sorted(analysis["low_coverage_modules"], 
                              key=lambda x: x["coverage"])
            
            for module in sorted_low[:10]:  # Show worst 10
                report.append(f"  {module["name"]:30} "
                            f"({module["category"]:>10}) "
                            f"{module["coverage"]:>5.1f}%")
            
            if len(sorted_low) > 10:
                remaining = len(sorted_low) - 10
                report.append(f"  ... and {remaining} more modules")
            
            report.append("")
        
        # Recommendations
        if analysis["recommendations"]:
            report.append("RECOMMENDATIONS")
            report.append("-" * 20)
            
            for i, rec in enumerate(analysis["recommendations"], 1):
                report.append(f"{i}. {rec}")
            
            report.append("")
        
        return '\n'.join(report)
    
    def export_coverage_data(self, analysis: Dict[str, Any], output_format: str = "json") -> Path:
        """Export coverage analysis data."""
        
        self.reports_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_format.lower() == "json":
            output_file = self.reports_dir / f"coverage_analysis_{timestamp}.json"
            with open(output_file, "w") as f:
                json.dump(analysis, f, indent=2, default=str)
        
        elif output_format.lower() == "csv":
            output_file = self.reports_dir / f"coverage_analysis_{timestamp}.csv"
            
            # Export uncovered modules
            with open(output_file, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Module", "Category", "Path", "Size (KB)", "Status"])
                
                for module in analysis["uncovered_modules"]:
                    writer.writerow([
                        module["name"],
                        module["category"],
                        module["path"],
                        f"{module["size_bytes"] / 1024:.1f}",
                        "Uncovered"
                    ])
                
                for module in analysis["low_coverage_modules"]:
                    writer.writerow([
                        module["name"],
                        module["category"],
                        module["path"],
                        "",
                        f'Low Coverage ({module["coverage"]:.1f}%)'
                    ])
        
        else:  # text format
            output_file = self.reports_dir / f"coverage_analysis_{timestamp}.txt"
            report = self.generate_coverage_report(analysis)
            output_file.write_text(report)
        
        return output_file
    
    def run_coverage_and_analyze(self, test_type: str = "all") -> Dict[str, Any]:
        """Run coverage measurement and analysis."""
        
        print("Running coverage measurement...")
        
        # Run tests with coverage
        cmd = [
            sys.executable, "-m", "pytest",
            "--cov=tools",
            "--cov-branch",
            "--cov-report=json:coverage.json",
            "--cov-report=xml:coverage.xml",
            "--cov-report=html:htmlcov",
        ]
        
        if test_type != "all":
            cmd.extend(["-m", test_type])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=self.project_root
            )
            
            print(f"Coverage measurement completed (exit code: {result.returncode})")
            
        except subprocess.TimeoutExpired:
            print("Coverage measurement timed out")
            return {}
        
        # Load and analyze coverage data
        coverage_data = self.load_coverage_data()
        if not coverage_data:
            print("No coverage data found")
            return {}
        
        analysis = self.analyze_coverage_gaps(coverage_data)
        return analysis


def main():
    """Main function for coverage analysis."""
    
    parser = argparse.ArgumentParser(description="StyleStack Coverage Analysis")
    parser.add_argument("--run-tests", action="store_true", 
                       help="Run tests with coverage before analysis")
    parser.add_argument("--test-type", choices=["all", "unit", "integration", "system"],
                       default="all", help="Type of tests to run")
    parser.add_argument("--export", choices=["json", "csv", "txt"], 
                       help="Export analysis data")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    analyzer = CoverageAnalyzer()
    
    if args.run_tests:
        analysis = analyzer.run_coverage_and_analyze(args.test_type)
    else:
        coverage_data = analyzer.load_coverage_data()
        if coverage_data:
            analysis = analyzer.analyze_coverage_gaps(coverage_data)
        else:
            print("No coverage data found. Run with --run-tests to generate coverage data.")
            return 1
    
    if not analysis:
        print("No analysis data available")
        return 1
    
    # Generate and display report
    report = analyzer.generate_coverage_report(analysis)
    print(report)
    
    # Export data if requested
    if args.export:
        output_file = analyzer.export_coverage_data(analysis, args.export)
        print(f"\nAnalysis data exported to: {output_file}")
    
    # Save report if output specified
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report)
        print(f"Report saved to: {output_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())