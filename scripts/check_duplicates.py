#!/usr/bin/env python3
"""
Quick Duplicate Code Hunter

Standalone script to quickly hunt for orphaned doubled code
and inconsistencies in the StyleStack codebase.
"""


from typing import Dict, List
import sys
from pathlib import Path
import ast
import hashlib
import difflib
import re
from collections import defaultdict

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

class CodeBlock(NamedTuple):
    """Represents a block of code with metadata."""
    file_path: str
    start_line: int
    end_line: int
    content: str
    hash: str

class DuplicationDetector:
    """Standalone duplicate code detection without pytest dependency."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.exact_duplicates = []
        self.similar_blocks = []
        self.orphaned_imports = {}
        self.inconsistencies = {}
        
    def analyze_codebase(self) -> Dict[str, int]:
        """Analyze codebase for duplicates and inconsistencies."""
        python_files = list(self.project_root.glob("**/*.py"))
        python_files = [f for f in python_files if not any(excluded in str(f) for excluded in [
            ".venv", "venv", "__pycache__", ".git", "node_modules", "build", "dist"
        ])]
        
        print(f"Analyzing {len(python_files)} Python files...")
        
        # Find exact duplicates
        self._find_exact_duplicates(python_files)
        
        # Find similar blocks
        self._find_similar_blocks(python_files)
        
        # Find orphaned imports
        self._find_orphaned_imports(python_files)
        
        # Check coding inconsistencies
        self._check_coding_inconsistencies(python_files)
        
        return {
            "exact_duplicates": len(self.exact_duplicates),
            "similar_blocks": len(self.similar_blocks),
            "files_with_orphaned_imports": len(self.orphaned_imports),
            "inconsistency_types": len(self.inconsistencies)
        }
    
    def _find_exact_duplicates(self, python_files: List[Path]):
        """Find exact code duplicates using AST and hashing."""
        blocks_by_hash = defaultdict(list)
        
        for file_path in python_files:
            try:
                content = file_path.read_text(encoding="utf-8")
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                        start_line = node.lineno
                        end_line = getattr(node, "end_lineno", start_line + 10)
                        
                        if end_line - start_line >= 5:  # Only check blocks >= 5 lines
                            lines = content.split('\n')[start_line-1:end_line]
                            block_content = '\n'.join(lines).strip()
                            
                            # Normalize whitespace for comparison
                            normalized = re.sub(r'\s+', ' ', block_content)
                            block_hash = hashlib.md5(normalized.encode()).hexdigest()
                            
                            block = CodeBlock(
                                file_path=str(file_path),
                                start_line=start_line,
                                end_line=end_line,
                                content=block_content,
                                hash=block_hash
                            )
                            
                            blocks_by_hash[block_hash].append(block)
                            
            except (SyntaxError, UnicodeDecodeError):
                continue
        
        # Find duplicates
        for block_hash, blocks in blocks_by_hash.items():
            if len(blocks) > 1:
                for i in range(len(blocks)):
                    for j in range(i + 1, len(blocks)):
                        self.exact_duplicates.append((blocks[i], blocks[j]))
    
    def _find_similar_blocks(self, python_files: List[Path]):
        """Find similar code blocks using fuzzy matching (optimized for speed)."""
        all_blocks = []
        
        print("Collecting code blocks...")
        for file_path in python_files[:20]:  # Limit files for faster analysis
            try:
                content = file_path.read_text(encoding="utf-8")
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                        start_line = node.lineno
                        end_line = getattr(node, "end_lineno", start_line + 10)
                        
                        if 10 <= end_line - start_line <= 50:  # Focus on medium-sized blocks
                            lines = content.split('\n')[start_line-1:end_line]
                            block_content = '\n'.join(lines).strip()
                            
                            block = CodeBlock(
                                file_path=str(file_path),
                                start_line=start_line,
                                end_line=end_line,
                                content=block_content,
                                hash=""
                            )
                            all_blocks.append(block)
                            
            except (SyntaxError, UnicodeDecodeError):
                continue
        
        print(f"Comparing {len(all_blocks)} blocks for similarity...")
        # Compare blocks for similarity (limit comparisons)
        comparisons = 0
        max_comparisons = 1000  # Limit total comparisons
        
        for i in range(len(all_blocks)):
            for j in range(i + 1, len(all_blocks)):
                if comparisons >= max_comparisons:
                    break
                    
                block1, block2 = all_blocks[i], all_blocks[j]
                
                if block1.file_path != block2.file_path:
                    similarity = difflib.SequenceMatcher(
                        None, block1.content, block2.content
                    ).ratio()
                    
                    if similarity > 0.85:  # Higher threshold for faster processing
                        self.similar_blocks.append((block1, block2, similarity))
                
                comparisons += 1
            
            if comparisons >= max_comparisons:
                break
    
    def _find_orphaned_imports(self, python_files: List[Path]):
        """Find potentially unused imports."""
        for file_path in python_files:
            try:
                content = file_path.read_text(encoding="utf-8")
                tree = ast.parse(content)
                
                imports = set()
                used_names = set()
                
                # Collect imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.asname or alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        for alias in node.names:
                            imports.add(alias.asname or alias.name)
                    elif isinstance(node, ast.Name):
                        used_names.add(node.id)
                    elif isinstance(node, ast.Attribute):
                        used_names.add(node.attr)
                
                # Find potentially orphaned imports
                potentially_orphaned = []
                for imp in imports:
                    base_name = imp.split(".")[0]
                    if base_name not in used_names and imp not in used_names:
                        potentially_orphaned.append(imp)
                
                if potentially_orphaned:
                    self.orphaned_imports[str(file_path)] = potentially_orphaned
                    
            except (SyntaxError, UnicodeDecodeError):
                continue
    
    def _check_coding_inconsistencies(self, python_files: List[Path]):
        """Check for coding style inconsistencies."""
        inconsistencies = defaultdict(list)
        
        for file_path in python_files:
            try:
                content = file_path.read_text(encoding="utf-8")
                
                # Check quote style consistency
                single_quotes = content.count("'")
                double_quotes = content.count('"')
                
                if single_quotes > 0 and double_quotes > 0:
                    ratio = min(single_quotes, double_quotes) / max(single_quotes, double_quotes)
                    if ratio > 0.3:  # Mixed usage
                        inconsistencies["mixed_quotes"].append(str(file_path))
                
                # Check indentation consistency
                lines = content.split('\n')
                tab_lines = sum(1 for line in lines if line.startswith('\t'))
                space_lines = sum(1 for line in lines if re.match(r"^ +", line))
                
                if tab_lines > 0 and space_lines > 0:
                    inconsistencies["mixed_indentation"].append(str(file_path))
                
            except UnicodeDecodeError:
                continue
        
        self.inconsistencies = dict(inconsistencies)
    
    def generate_report(self) -> str:
        """Generate detailed analysis report."""
        lines = []
        lines.append("StyleStack Duplicate Code Analysis Report")
        lines.append("=" * 50)
        
        # Exact duplicates
        if self.exact_duplicates:
            lines.append(f"\n🔴 EXACT DUPLICATES ({len(self.exact_duplicates)} pairs)")
            lines.append("-" * 30)
            for i, (block1, block2) in enumerate(self.exact_duplicates[:10]):
                size = block1.end_line - block1.start_line + 1
                lines.append(f"{i+1:2d}. {block1.file_path}:{block1.start_line} ↔ {block2.file_path}:{block2.start_line} ({size} lines)")
        
        # Similar blocks
        if self.similar_blocks:
            very_similar = [s for s in self.similar_blocks if s[2] > 0.9]
            if very_similar:
                lines.append(f"\n🟡 VERY SIMILAR BLOCKS ({len(very_similar)} pairs)")
                lines.append("-" * 30)
                for i, (block1, block2, similarity) in enumerate(very_similar[:10]):
                    lines.append(f"{i+1:2d}. {block1.file_path}:{block1.start_line} ↔ {block2.file_path}:{block2.start_line} ({similarity:.1%})")
        
        # Orphaned imports
        if self.orphaned_imports:
            lines.append(f"\n🟠 POTENTIALLY UNUSED IMPORTS")
            lines.append("-" * 35)
            for file_path, imports in list(self.orphaned_imports.items())[:10]:
                rel_path = str(Path(file_path).relative_to(self.project_root))
                lines.append(f"  {rel_path}: {", ".join(imports[:5])}")
        
        # Inconsistencies
        if self.inconsistencies:
            lines.append(f"\n🔵 CODING INCONSISTENCIES")
            lines.append("-" * 25)
            for inconsistency_type, files in self.inconsistencies.items():
                lines.append(f"  {inconsistency_type.replace("_", " ").title()}: {len(files)} files")
        
        return '\n'.join(lines)


def main():
    """Run duplicate code detection and generate report."""
    
    print("🔍 StyleStack Duplicate Code Hunter")
    print("=" * 40)
    
    project_root = Path(__file__).parent
    detector = DuplicationDetector(project_root)
    
    try:
        # Run analysis
        print("Analyzing codebase for duplicates and inconsistencies...")
        summary = detector.analyze_codebase()
        
        print("\n📊 QUICK SUMMARY")
        print("-" * 20)
        for key, value in summary.items():
            emoji = "🔴" if value > 10 else "🟡" if value > 5 else "🟢"
            print(f"{emoji} {key.replace("_", " ").title()}: {value}")
        
        # Generate detailed report
        report = detector.generate_report()
        
        # Save to file
        reports_dir = project_root / "reports"
        reports_dir.mkdir(exist_ok=True)
        report_file = reports_dir / "duplicate_code_analysis.txt"
        report_file.write_text(report)
        
        print(f"\n📋 Full report saved to: {report_file}")
        
        # Show critical findings
        if detector.exact_duplicates:
            print(f"\n🔴 CRITICAL: Found {len(detector.exact_duplicates)} exact duplicates!")
            print("Top duplicates:")
            for i, (block1, block2) in enumerate(detector.exact_duplicates[:3]):
                lines = block1.end_line - block1.start_line + 1
                print(f"  {i+1}. {block1.file_path}:{block1.start_line} ↔ {block2.file_path}:{block2.start_line} ({lines} lines)")
        
        if detector.similar_blocks:
            very_similar = [s for s in detector.similar_blocks if s[2] > 0.95]
            if very_similar:
                print(f"\n🟡 WARNING: Found {len(very_similar)} nearly identical blocks!")
                for block1, block2, similarity in very_similar[:3]:
                    print(f"     {block1.file_path}:{block1.start_line} ↔ {block2.file_path}:{block2.start_line} ({similarity:.1%})")
        
        if detector.orphaned_imports:
            total_orphans = sum(len(imports) for imports in detector.orphaned_imports.values())
            if total_orphans > 20:
                print(f"\n🟡 INFO: Found {total_orphans} potentially unused imports across {len(detector.orphaned_imports)} files")
        
        # Overall health score
        health_score = calculate_health_score(summary)
        health_emoji = "🟢" if health_score > 80 else "🟡" if health_score > 60 else "🔴"
        print(f"\n{health_emoji} Codebase Health Score: {health_score}/100")
        
        if health_score < 70:
            print("   Consider refactoring to reduce duplication and improve consistency")
        elif health_score < 85:
            print("   Good code quality with minor improvement opportunities")
        else:
            print("   Excellent code consistency!")
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


def calculate_health_score(summary: dict) -> int:
    """Calculate overall codebase health score (0-100)."""
    score = 100
    
    # Penalize exact duplicates heavily
    exact_duplicates = summary.get("exact_duplicates", 0)
    score -= min(exact_duplicates * 5, 30)  # Up to -30 points
    
    # Penalize similar blocks moderately
    similar_blocks = summary.get("similar_blocks", 0)
    score -= min(similar_blocks * 2, 20)  # Up to -20 points
    
    # Penalize orphaned imports lightly
    orphaned_files = summary.get("files_with_orphaned_imports", 0)
    score -= min(orphaned_files * 1, 15)  # Up to -15 points
    
    # Penalize inconsistencies
    inconsistencies = summary.get("inconsistency_types", 0)
    score -= min(inconsistencies * 3, 15)  # Up to -15 points
    
    return max(0, score)


if __name__ == "__main__":
    sys.exit(main())