#!/usr/bin/env python3
"""
Code Archival Analysis Tool

Identifies safe candidates for archiving old code based on:
1. File modification dates
2. Usage patterns and imports
3. Deprecated functionality markers
4. Test coverage and validation
5. Duplicate or superseded implementations
"""


from typing import Any, Dict, List
import ast
import os
import re
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timedelta
import subprocess


@dataclass
class ArchivalCandidate:
    """Represents a file or directory candidate for archiving."""
    path: Path
    reason: str
    confidence: str  # "high", "medium", "low"
    last_modified: datetime
    size_bytes: int
    dependencies: List[str]
    dependents: List[str]
    notes: str = ""


class CodeArchivalAnalyzer:
    """Analyzer for identifying safe archival candidates."""
    
    # Patterns that suggest old/deprecated code
    DEPRECATION_PATTERNS = [
        r"# ?deprecated",
        r"# ?obsolete", 
        r"# ?legacy",
        r"# ?old",
        r"# ?unused",
        r"# ?todo.*remove",
        r"# ?fixme.*remove",
        r"@deprecated",
        r"warnings\.warn.*deprecat",
        r"# ?replaced by",
        r"# ?superseded by"
    ]
    
    # File name patterns that suggest old code
    OLD_FILE_PATTERNS = [
        r".*_old\.py$",
        r".*_legacy\.py$", 
        r".*_deprecated\.py$",
        r".*_backup\.py$",
        r".*_v\d+\.py$",
        r".*_original\.py$",
        r".*_test\.py$",  # Sometimes old test files
        r".*\.bak$",
        r".*\.orig$"
    ]
    
    # Directories that often contain archival candidates
    ARCHIVAL_CANDIDATE_DIRS = [
        "backup", "old", "legacy", "deprecated", "archive", "tmp", "temp",
        "experiments", "prototypes", "sandbox", "scratch", "draft"
    ]
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.candidates = []
        self.file_dependencies = {}
        self.import_graph = {}
        
    def analyze_file_age(self, days_threshold: int = 180) -> List[Path]:
        """Find files not modified recently."""
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        old_files = []
        
        for py_file in self.project_root.glob("**/*.py"):
            if any(excluded in str(py_file) for excluded in [
                ".venv", "venv", "__pycache__", ".git", "node_modules"
            ]):
                continue
                
            stat = py_file.stat()
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            
            if modified_time < cutoff_date:
                old_files.append(py_file)
        
        return old_files
    
    def analyze_import_usage(self) -> Dict[str, Dict[str, Any]]:
        """Analyze import patterns to find unused modules."""
        usage_map = {}
        
        # First pass: collect all Python files and their imports
        for py_file in self.project_root.glob("**/*.py"):
            if any(excluded in str(py_file) for excluded in [
                ".venv", "venv", "__pycache__", ".git"
            ]):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                tree = ast.parse(content)
                
                file_key = str(py_file.relative_to(self.project_root))
                usage_map[file_key] = {
                    'imports': [],
                    'imported_by': [],
                    'size': py_file.stat().st_size,
                    'modified': datetime.fromtimestamp(py_file.stat().st_mtime)
                }
                
                # Collect imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            usage_map[file_key]['imports'].append(alias.name)
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        usage_map[file_key]['imports'].append(node.module)
                        
            except (SyntaxError, UnicodeDecodeError):
                continue
        
        # Second pass: build reverse dependency map
        for file_path, info in usage_map.items():
            for imported_module in info['imports']:
                # Try to map import to file
                potential_files = [
                    f"{imported_module.replace('.', '/')}.py",
                    f"{imported_module.replace('.', '/')}/__init__.py",
                    f"tools/{imported_module.replace('.', '/')}.py",
                ]
                
                for potential_file in potential_files:
                    if potential_file in usage_map:
                        usage_map[potential_file]['imported_by'].append(file_path)
                        break
        
        return usage_map
    
    def find_deprecated_code(self) -> List[Path]:
        """Find files with deprecation markers."""
        deprecated_files = []
        
        for py_file in self.project_root.glob("**/*.py"):
            if any(excluded in str(py_file) for excluded in [
                ".venv", "venv", "__pycache__", ".git"
            ]):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8').lower()
                
                # Check for deprecation patterns
                for pattern in self.DEPRECATION_PATTERNS:
                    if re.search(pattern, content, re.IGNORECASE):
                        deprecated_files.append(py_file)
                        break
                        
                # Check filename patterns
                filename = py_file.name.lower()
                for pattern in self.OLD_FILE_PATTERNS:
                    if re.match(pattern, filename):
                        deprecated_files.append(py_file)
                        break
                        
            except UnicodeDecodeError:
                continue
        
        return deprecated_files
    
    def find_duplicate_implementations(self) -> List[tuple]:
        """Find files with similar functionality that might be duplicates."""
        similar_files = []
        
        # Group files by similar names
        name_groups = {}
        for py_file in self.project_root.glob("**/*.py"):
            if any(excluded in str(py_file) for excluded in [
                ".venv", "venv", "__pycache__", ".git"
            ]):
                continue
            
            # Extract base name without version/variation suffixes
            base_name = re.sub(r'(_v\d+|_old|_new|_legacy|_modern|_\d+)$', '', py_file.stem)
            
            if base_name not in name_groups:
                name_groups[base_name] = []
            name_groups[base_name].append(py_file)
        
        # Find groups with multiple files
        for base_name, files in name_groups.items():
            if len(files) > 1:
                # Sort by modification time to identify newer vs older versions
                files_with_time = [(f, datetime.fromtimestamp(f.stat().st_mtime)) for f in files]
                files_with_time.sort(key=lambda x: x[1], reverse=True)  # Newest first
                
                similar_files.append((base_name, files_with_time))
        
        return similar_files
    
    def find_archival_directories(self) -> List[Path]:
        """Find directories that are likely archival candidates."""
        archival_dirs = []
        
        for dir_path in self.project_root.rglob("*"):
            if not dir_path.is_dir():
                continue
                
            dir_name = dir_path.name.lower()
            
            # Check if directory name suggests archival content
            if any(keyword in dir_name for keyword in self.ARCHIVAL_CANDIDATE_DIRS):
                archival_dirs.append(dir_path)
                continue
            
            # Check if directory contains only old files
            py_files = list(dir_path.glob("*.py"))
            if py_files:
                old_threshold = datetime.now() - timedelta(days=365)  # 1 year
                all_old = all(
                    datetime.fromtimestamp(f.stat().st_mtime) < old_threshold
                    for f in py_files
                )
                
                if all_old:
                    archival_dirs.append(dir_path)
        
        return archival_dirs
    
    def analyze_test_coverage(self, file_path: Path) -> Dict[str, Any]:
        """Analyze if a file has corresponding tests."""
        file_stem = file_path.stem
        file_dir = file_path.parent
        
        # Look for corresponding test files
        test_patterns = [
            f"test_{file_stem}.py",
            f"{file_stem}_test.py",
            f"test_{file_stem}_*.py",
        ]
        
        test_files = []
        for pattern in test_patterns:
            test_files.extend(file_dir.glob(pattern))
            # Also check tests/ directory
            tests_dir = self.project_root / "tests"
            if tests_dir.exists():
                test_files.extend(tests_dir.glob(pattern))
                test_files.extend(tests_dir.glob(f"**/{pattern}"))
        
        return {
            'has_tests': len(test_files) > 0,
            'test_files': [str(f) for f in test_files],
            'test_count': len(test_files)
        }
    
    def analyze_git_history(self, file_path: Path) -> Dict[str, Any]:
        """Analyze git history for a file."""
        try:
            # Get last commit date
            result = subprocess.run([
                'git', 'log', '-1', '--format=%ct', str(file_path)
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0 and result.stdout.strip():
                last_commit = datetime.fromtimestamp(int(result.stdout.strip()))
            else:
                last_commit = None
                
            # Get commit count
            result = subprocess.run([
                'git', 'rev-list', '--count', 'HEAD', '--', str(file_path)
            ], capture_output=True, text=True, cwd=self.project_root)
            
            commit_count = int(result.stdout.strip()) if result.returncode == 0 else 0
            
            return {
                'last_commit': last_commit,
                'commit_count': commit_count,
                'has_git_history': commit_count > 0
            }
            
        except (subprocess.SubprocessError, ValueError):
            return {
                'last_commit': None,
                'commit_count': 0,
                'has_git_history': False
            }
    
    def generate_archival_recommendations(self) -> List[ArchivalCandidate]:
        """Generate comprehensive archival recommendations."""
        candidates = []
        
        print("🔍 Analyzing code for archival candidates...")
        
        # 1. Find old files
        print("  📅 Checking file ages...")
        old_files = self.analyze_file_age(days_threshold=365)  # 1 year
        
        # 2. Analyze import usage
        print("  📦 Analyzing import usage...")
        usage_map = self.analyze_import_usage()
        
        # 3. Find deprecated code
        print("  🗂️  Finding deprecated code...")
        deprecated_files = self.find_deprecated_code()
        
        # 4. Find duplicates
        print("  🔄 Finding duplicate implementations...")
        duplicate_groups = self.find_duplicate_implementations()
        
        # 5. Find archival directories
        print("  📁 Finding archival directories...")
        archival_dirs = self.find_archival_directories()
        
        # Process old files
        for file_path in old_files:
            rel_path = str(file_path.relative_to(self.project_root))
            usage_info = usage_map.get(rel_path, {})
            
            # Skip if heavily imported
            imported_by_count = len(usage_info.get('imported_by', []))
            if imported_by_count > 3:
                continue
            
            stat = file_path.stat()
            git_info = self.analyze_git_history(file_path)
            test_info = self.analyze_test_coverage(file_path)
            
            confidence = "high" if imported_by_count == 0 else "medium"
            
            candidates.append(ArchivalCandidate(
                path=file_path,
                reason=f"Not modified in 1+ year, {imported_by_count} imports",
                confidence=confidence,
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                size_bytes=stat.st_size,
                dependencies=usage_info.get('imports', []),
                dependents=usage_info.get('imported_by', []),
                notes=f"Git commits: {git_info['commit_count']}, Has tests: {test_info['has_tests']}"
            ))
        
        # Process deprecated files
        for file_path in deprecated_files:
            stat = file_path.stat()
            rel_path = str(file_path.relative_to(self.project_root))
            usage_info = usage_map.get(rel_path, {})
            
            candidates.append(ArchivalCandidate(
                path=file_path,
                reason="Contains deprecation markers or deprecated filename",
                confidence="high",
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                size_bytes=stat.st_size,
                dependencies=usage_info.get('imports', []),
                dependents=usage_info.get('imported_by', []),
                notes="Contains explicit deprecation markers"
            ))
        
        # Process duplicate implementations
        for base_name, files_with_time in duplicate_groups:
            if len(files_with_time) > 1:
                # Keep the newest, consider archiving older versions
                newest_file, newest_time = files_with_time[0]
                
                for older_file, older_time in files_with_time[1:]:
                    age_diff = newest_time - older_time
                    
                    if age_diff.days > 90:  # More than 3 months older
                        stat = older_file.stat()
                        rel_path = str(older_file.relative_to(self.project_root))
                        usage_info = usage_map.get(rel_path, {})
                        
                        candidates.append(ArchivalCandidate(
                            path=older_file,
                            reason=f"Older version of {base_name} (newer: {newest_file.name})",
                            confidence="medium",
                            last_modified=older_time,
                            size_bytes=stat.st_size,
                            dependencies=usage_info.get('imports', []),
                            dependents=usage_info.get('imported_by', []),
                            notes=f"Age difference: {age_diff.days} days"
                        ))
        
        # Process archival directories
        for dir_path in archival_dirs:
            candidates.append(ArchivalCandidate(
                path=dir_path,
                reason=f"Directory name suggests archival content: {dir_path.name}",
                confidence="medium",
                last_modified=datetime.fromtimestamp(dir_path.stat().st_mtime),
                size_bytes=sum(f.stat().st_size for f in dir_path.rglob("*") if f.is_file()),
                dependencies=[],
                dependents=[],
                notes=f"Contains {len(list(dir_path.rglob('*.py')))} Python files"
            ))
        
        # Remove duplicates and sort by confidence
        unique_candidates = {}
        for candidate in candidates:
            key = str(candidate.path)
            if key not in unique_candidates or candidate.confidence == "high":
                unique_candidates[key] = candidate
        
        final_candidates = list(unique_candidates.values())
        final_candidates.sort(key=lambda x: (x.confidence == "high", -x.size_bytes), reverse=True)
        
        return final_candidates
    
    def generate_archival_report(self, candidates: List[ArchivalCandidate]) -> str:
        """Generate detailed archival recommendations report."""
        lines = []
        lines.append("StyleStack Code Archival Analysis Report")
        lines.append("=" * 60)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Summary
        high_confidence = [c for c in candidates if c.confidence == "high"]
        medium_confidence = [c for c in candidates if c.confidence == "medium"]
        low_confidence = [c for c in candidates if c.confidence == "low"]
        
        total_size = sum(c.size_bytes for c in candidates) / (1024 * 1024)  # MB
        
        lines.append("📊 ARCHIVAL SUMMARY")
        lines.append("-" * 25)
        lines.append(f"Total candidates: {len(candidates)}")
        lines.append(f"🔴 High confidence: {len(high_confidence)}")
        lines.append(f"🟡 Medium confidence: {len(medium_confidence)}")
        lines.append(f"🟢 Low confidence: {len(low_confidence)}")
        lines.append(f"Total size: {total_size:.1f} MB")
        lines.append("")
        
        # High confidence recommendations
        if high_confidence:
            lines.append("🔴 HIGH CONFIDENCE ARCHIVAL CANDIDATES")
            lines.append("-" * 45)
            
            for candidate in high_confidence[:15]:  # Top 15
                size_kb = candidate.size_bytes / 1024
                age_days = (datetime.now() - candidate.last_modified).days
                
                lines.append(f"📁 {candidate.path.name}")
                lines.append(f"   Path: {candidate.path.relative_to(self.project_root)}")
                lines.append(f"   Reason: {candidate.reason}")
                lines.append(f"   Size: {size_kb:.1f} KB, Age: {age_days} days")
                lines.append(f"   Dependencies: {len(candidate.dependencies)}, Dependents: {len(candidate.dependents)}")
                if candidate.notes:
                    lines.append(f"   Notes: {candidate.notes}")
                lines.append("")
        
        # Medium confidence recommendations  
        if medium_confidence:
            lines.append("🟡 MEDIUM CONFIDENCE ARCHIVAL CANDIDATES")
            lines.append("-" * 47)
            
            for candidate in medium_confidence[:10]:  # Top 10
                size_kb = candidate.size_bytes / 1024
                age_days = (datetime.now() - candidate.last_modified).days
                
                lines.append(f"📁 {candidate.path.name}")
                lines.append(f"   Reason: {candidate.reason}")
                lines.append(f"   Size: {size_kb:.1f} KB, Age: {age_days} days")
                if candidate.dependents:
                    lines.append(f"   ⚠️  Still imported by: {', '.join(candidate.dependents[:3])}")
                lines.append("")
        
        # Archival recommendations
        lines.append("💡 ARCHIVAL RECOMMENDATIONS")
        lines.append("-" * 30)
        
        if high_confidence:
            lines.append("1. **SAFE TO ARCHIVE** - High confidence candidates:")
            lines.append("   • Files with explicit deprecation markers")
            lines.append("   • Files not imported by any other modules")
            lines.append("   • Files not modified in 1+ years with no dependencies")
            lines.append("")
            
        if medium_confidence:
            lines.append("2. **REVIEW BEFORE ARCHIVING** - Medium confidence candidates:")
            lines.append("   • Files with few dependencies but still in use")
            lines.append("   • Older versions of duplicate implementations")
            lines.append("   • Directories with archival-suggesting names")
            lines.append("")
        
        lines.append("3. **ARCHIVAL PROCESS**:")
        lines.append("   • Create 'archive/' directory")
        lines.append("   • Move candidates maintaining directory structure")
        lines.append("   • Update any remaining imports")
        lines.append("   • Test that nothing breaks")
        lines.append("   • Commit changes with clear archival message")
        
        return '\n'.join(lines)


def main():
    """Run code archival analysis."""
    project_root = Path(__file__).parent
    analyzer = CodeArchivalAnalyzer(project_root)
    
    print("🗄️  StyleStack Code Archival Analyzer")
    print("=" * 50)
    
    candidates = analyzer.generate_archival_recommendations()
    report = analyzer.generate_archival_report(candidates)
    
    print(report)
    
    # Save report
    reports_dir = project_root / "reports"
    reports_dir.mkdir(exist_ok=True)
    report_file = reports_dir / "code_archival_analysis.txt"
    report_file.write_text(report)
    
    print(f"\n📋 Detailed report saved to: {report_file}")
    
    # Show immediate actions
    high_confidence = [c for c in candidates if c.confidence == "high"]
    if high_confidence:
        print(f"\n🎯 IMMEDIATE ARCHIVAL CANDIDATES ({len(high_confidence)} files):")
        for candidate in high_confidence[:5]:
            print(f"  📁 {candidate.path.relative_to(project_root)}")
            print(f"     {candidate.reason}")
    else:
        print(f"\n✅ No high-confidence archival candidates found.")
        print("The codebase appears well-maintained with minimal legacy code.")
    
    return 0


if __name__ == "__main__":
    exit(main())