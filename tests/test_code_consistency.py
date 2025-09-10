#!/usr/bin/env python3
"""
Code Consistency and Duplication Detection Tests

This module detects orphaned doubled code, inconsistent patterns,
and maintains codebase consistency across the StyleStack project.
"""


from typing import Any, Dict, List, Tuple
import pytest
import ast
import hashlib
import difflib
from pathlib import Path
from collections import defaultdict, Counter
import re
import json


class CodeBlock:
    """Represents a block of code for duplication analysis."""
    
    def __init__(self, content: str, file_path: str, start_line: int, end_line: int, block_type: str = "function"):
        self.content = content.strip()
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.block_type = block_type
        self.hash = self._compute_hash()
        self.normalized = self._normalize_content()
        
    def _compute_hash(self) -> str:
        """Compute hash of the code block content."""
        return hashlib.md5(self.content.encode()).hexdigest()
    
    def _normalize_content(self) -> str:
        """Normalize content for fuzzy matching (remove whitespace, comments)."""
        lines = []
        for line in self.content.split('\n'):
            # Remove comments and extra whitespace
            line = re.sub(r'#.*$', '', line)  # Remove comments
            line = re.sub(r'\s+', ' ', line.strip())  # Normalize whitespace
            if line:  # Skip empty lines
                lines.append(line)
        return '\n'.join(lines)
    
    def similarity_to(self, other: 'CodeBlock') -> float:
        """Calculate similarity ratio to another code block."""
        if self.block_type != other.block_type:
            return 0.0
        
        # Use difflib to calculate similarity
        similarity = difflib.SequenceMatcher(None, self.normalized, other.normalized)
        return similarity.ratio()
    
    def __repr__(self):
        return f"CodeBlock({self.file_path}:{self.start_line}-{self.end_line}, {self.block_type})"


class DuplicationDetector:
    """Detects code duplication and consistency issues."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tools_dir = project_root / "tools"
        self.tests_dir = project_root / "tests"
        
        # Configuration
        self.min_lines = 5  # Minimum lines to consider for duplication
        self.similarity_threshold = 0.85  # Similarity threshold for fuzzy matching
        self.exact_match_min_lines = 3  # Minimum lines for exact match detection
        
        # Results storage
        self.code_blocks: List[CodeBlock] = []
        self.exact_duplicates: List[Tuple[CodeBlock, CodeBlock]] = []
        self.similar_blocks: List[Tuple[CodeBlock, CodeBlock, float]] = []
        self.orphaned_imports: Dict[str, List[str]] = {}
        self.inconsistent_patterns: Dict[str, List[Dict]] = {}
    
    def extract_code_blocks(self, file_path: Path) -> List[CodeBlock]:
        """Extract code blocks (functions, classes) from a Python file."""
        blocks = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content, filename=str(file_path))
            
            lines = content.split('\n')
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    start_line = node.lineno
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 10
                    
                    # Extract the actual code block
                    block_lines = lines[start_line-1:end_line]
                    block_content = '\n'.join(block_lines)
                    
                    # Skip very small blocks
                    if len(block_lines) >= self.min_lines:
                        block_type = "class" if isinstance(node, ast.ClassDef) else "function"
                        
                        block = CodeBlock(
                            content=block_content,
                            file_path=str(file_path.relative_to(self.project_root)),
                            start_line=start_line,
                            end_line=end_line,
                            block_type=block_type
                        )
                        blocks.append(block)
        
        except (SyntaxError, UnicodeDecodeError, FileNotFoundError) as e:
            print(f"Warning: Could not parse {file_path}: {e}")
        
        return blocks
    
    def find_exact_duplicates(self) -> List[Tuple[CodeBlock, CodeBlock]]:
        """Find blocks with identical content."""
        duplicates = []
        hash_to_blocks = defaultdict(list)
        
        # Group blocks by hash
        for block in self.code_blocks:
            hash_to_blocks[block.hash].append(block)
        
        # Find groups with multiple blocks (duplicates)
        for hash_key, blocks in hash_to_blocks.items():
            if len(blocks) > 1:
                # Create pairs of duplicates
                for i in range(len(blocks)):
                    for j in range(i + 1, len(blocks)):
                        duplicates.append((blocks[i], blocks[j]))
        
        return duplicates
    
    def find_similar_blocks(self) -> List[Tuple[CodeBlock, CodeBlock, float]]:
        """Find blocks with similar content using fuzzy matching."""
        similar_blocks = []
        
        # Compare each block with every other block
        for i, block1 in enumerate(self.code_blocks):
            for j, block2 in enumerate(self.code_blocks[i + 1:], i + 1):
                # Skip identical blocks (already found in exact duplicates)
                if block1.hash == block2.hash:
                    continue
                
                # Skip if from the same file (might be legitimate patterns)
                if block1.file_path == block2.file_path:
                    continue
                
                similarity = block1.similarity_to(block2)
                if similarity >= self.similarity_threshold:
                    similar_blocks.append((block1, block2, similarity))
        
        return similar_blocks
    
    def find_orphaned_imports(self) -> Dict[str, List[str]]:
        """Find imported modules that are not used in the file."""
        orphaned_imports = {}
        
        for py_file in self.tools_dir.glob("**/*.py"):
            try:
                content = py_file.read_text(encoding='utf-8')
                tree = ast.parse(content, filename=str(py_file))
                
                # Extract imports
                imports = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.add(node.module.split('.')[0])
                        for alias in node.names:
                            imports.add(alias.name)
                
                # Check usage in content
                unused_imports = []
                for import_name in imports:
                    # Simple heuristic: check if import name appears in content
                    # (excluding the import statement itself)
                    import_pattern = rf'\b{re.escape(import_name)}\b'
                    matches = re.findall(import_pattern, content)
                    
                    # If only appears in import statements, it might be unused
                    if len(matches) <= 1:  # Only the import statement itself
                        unused_imports.append(import_name)
                
                if unused_imports:
                    relative_path = str(py_file.relative_to(self.project_root))
                    orphaned_imports[relative_path] = unused_imports
                    
            except (SyntaxError, UnicodeDecodeError) as e:
                print(f"Warning: Could not analyze imports in {py_file}: {e}")
        
        return orphaned_imports
    
    def find_inconsistent_patterns(self) -> Dict[str, List[Dict]]:
        """Find inconsistent coding patterns across the codebase."""
        inconsistencies = defaultdict(list)
        
        # Pattern 1: Inconsistent error handling
        error_patterns = []
        
        # Pattern 2: Inconsistent logging
        logging_patterns = []
        
        # Pattern 3: Inconsistent docstring styles
        docstring_patterns = []
        
        for py_file in self.tools_dir.glob("**/*.py"):
            try:
                content = py_file.read_text(encoding='utf-8')
                tree = ast.parse(content, filename=str(py_file))
                relative_path = str(py_file.relative_to(self.project_root))
                
                # Check error handling patterns
                try_blocks = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Try):
                        handlers = [type(handler.type).__name__ if handler.type else "bare" 
                                  for handler in node.handlers]
                        try_blocks.append({
                            'file': relative_path,
                            'line': node.lineno,
                            'handlers': handlers,
                            'has_finally': len(node.finalbody) > 0
                        })
                
                if try_blocks:
                    error_patterns.extend(try_blocks)
                
                # Check logging patterns
                logging_calls = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Attribute):
                            if any(log_level in node.func.attr.lower() 
                                  for log_level in ['debug', 'info', 'warning', 'error', 'critical']):
                                logging_calls.append({
                                    'file': relative_path,
                                    'line': node.lineno,
                                    'level': node.func.attr,
                                    'logger': ast.dump(node.func.value) if hasattr(node.func, 'value') else 'unknown'
                                })
                
                if logging_calls:
                    logging_patterns.extend(logging_calls)
                
                # Check docstring patterns
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        docstring = ast.get_docstring(node)
                        if docstring:
                            docstring_patterns.append({
                                'file': relative_path,
                                'line': node.lineno,
                                'type': type(node).__name__,
                                'name': node.name,
                                'style': self._analyze_docstring_style(docstring)
                            })
                            
            except (SyntaxError, UnicodeDecodeError) as e:
                print(f"Warning: Could not analyze patterns in {py_file}: {e}")
        
        # Analyze for inconsistencies
        if error_patterns:
            inconsistencies['error_handling'] = self._find_error_handling_inconsistencies(error_patterns)
        
        if logging_patterns:
            inconsistencies['logging'] = self._find_logging_inconsistencies(logging_patterns)
        
        if docstring_patterns:
            inconsistencies['docstrings'] = self._find_docstring_inconsistencies(docstring_patterns)
        
        return dict(inconsistencies)
    
    def _analyze_docstring_style(self, docstring: str) -> str:
        """Analyze docstring style (Google, NumPy, Sphinx, etc.)."""
        if 'Args:' in docstring and 'Returns:' in docstring:
            return 'google'
        elif 'Parameters' in docstring and '----------' in docstring:
            return 'numpy'
        elif ':param' in docstring and ':return' in docstring:
            return 'sphinx'
        else:
            return 'basic'
    
    def _find_error_handling_inconsistencies(self, patterns: List[Dict]) -> List[Dict]:
        """Find inconsistencies in error handling patterns."""
        inconsistencies = []
        
        # Group by file
        files_patterns = defaultdict(list)
        for pattern in patterns:
            files_patterns[pattern['file']].append(pattern)
        
        # Check for mixed exception handling styles
        for file_path, file_patterns in files_patterns.items():
            has_bare_except = any('bare' in p['handlers'] for p in file_patterns)
            has_specific_except = any('bare' not in p['handlers'] for p in file_patterns)
            
            if has_bare_except and has_specific_except:
                inconsistencies.append({
                    'type': 'mixed_exception_handling',
                    'file': file_path,
                    'issue': 'File uses both bare except and specific exception handling'
                })
        
        return inconsistencies
    
    def _find_logging_inconsistencies(self, patterns: List[Dict]) -> List[Dict]:
        """Find inconsistencies in logging patterns."""
        inconsistencies = []
        
        # Check for different logger instances
        loggers = set(p['logger'] for p in patterns)
        if len(loggers) > 3:  # Allow some variation, but flag excessive diversity
            inconsistencies.append({
                'type': 'multiple_logger_patterns',
                'issue': f'Found {len(loggers)} different logger patterns across codebase',
                'loggers': list(loggers)[:5]  # Show first 5
            })
        
        return inconsistencies
    
    def _find_docstring_inconsistencies(self, patterns: List[Dict]) -> List[Dict]:
        """Find inconsistencies in docstring styles."""
        inconsistencies = []
        
        # Count docstring styles
        style_counts = Counter(p['style'] for p in patterns)
        
        if len(style_counts) > 2:  # More than 2 different styles
            inconsistencies.append({
                'type': 'mixed_docstring_styles',
                'issue': 'Multiple docstring styles found in codebase',
                'styles': dict(style_counts)
            })
        
        return inconsistencies
    
    def analyze_codebase(self) -> Dict[str, Any]:
        """Run complete codebase consistency analysis."""
        print("Extracting code blocks...")
        
        # Extract all code blocks
        for py_file in self.tools_dir.glob("**/*.py"):
            blocks = self.extract_code_blocks(py_file)
            self.code_blocks.extend(blocks)
        
        print(f"Found {len(self.code_blocks)} code blocks")
        
        # Find duplicates
        print("Finding exact duplicates...")
        self.exact_duplicates = self.find_exact_duplicates()
        
        print("Finding similar blocks...")
        self.similar_blocks = self.find_similar_blocks()
        
        print("Finding orphaned imports...")
        self.orphaned_imports = self.find_orphaned_imports()
        
        print("Finding inconsistent patterns...")
        self.inconsistent_patterns = self.find_inconsistent_patterns()
        
        return {
            'total_code_blocks': len(self.code_blocks),
            'exact_duplicates': len(self.exact_duplicates),
            'similar_blocks': len(self.similar_blocks),
            'files_with_orphaned_imports': len(self.orphaned_imports),
            'inconsistency_types': len(self.inconsistent_patterns)
        }
    
    def generate_report(self) -> str:
        """Generate a detailed consistency report."""
        report = []
        report.append("StyleStack Code Consistency Report")
        report.append("=" * 50)
        
        # Summary
        report.append(f"Total code blocks analyzed: {len(self.code_blocks)}")
        report.append(f"Exact duplicates found: {len(self.exact_duplicates)}")
        report.append(f"Similar blocks found: {len(self.similar_blocks)}")
        report.append(f"Files with orphaned imports: {len(self.orphaned_imports)}")
        report.append(f"Inconsistency categories: {len(self.inconsistent_patterns)}")
        report.append("")
        
        # Exact duplicates
        if self.exact_duplicates:
            report.append("EXACT DUPLICATES")
            report.append("-" * 20)
            for i, (block1, block2) in enumerate(self.exact_duplicates[:10]):
                report.append(f"{i+1}. {block1.file_path}:{block1.start_line}")
                report.append(f"   {block2.file_path}:{block2.start_line}")
                report.append(f"   Lines: {block1.end_line - block1.start_line + 1}")
                report.append("")
            
            if len(self.exact_duplicates) > 10:
                report.append(f"... and {len(self.exact_duplicates) - 10} more duplicates")
            report.append("")
        
        # Similar blocks
        if self.similar_blocks:
            report.append("SIMILAR BLOCKS (>85% similarity)")
            report.append("-" * 35)
            for i, (block1, block2, similarity) in enumerate(self.similar_blocks[:10]):
                report.append(f"{i+1}. {block1.file_path}:{block1.start_line}")
                report.append(f"   {block2.file_path}:{block2.start_line}")
                report.append(f"   Similarity: {similarity:.1%}")
                report.append("")
            
            if len(self.similar_blocks) > 10:
                report.append(f"... and {len(self.similar_blocks) - 10} more similar blocks")
            report.append("")
        
        # Orphaned imports
        if self.orphaned_imports:
            report.append("ORPHANED IMPORTS")
            report.append("-" * 20)
            for file_path, imports in list(self.orphaned_imports.items())[:10]:
                report.append(f"{file_path}:")
                for imp in imports:
                    report.append(f"  - {imp}")
                report.append("")
            
            if len(self.orphaned_imports) > 10:
                report.append(f"... and {len(self.orphaned_imports) - 10} more files")
            report.append("")
        
        # Inconsistent patterns
        if self.inconsistent_patterns:
            report.append("INCONSISTENT PATTERNS")
            report.append("-" * 25)
            for category, issues in self.inconsistent_patterns.items():
                report.append(f"{category.upper()}:")
                for issue in issues[:5]:
                    report.append(f"  - {issue.get('issue', issue)}")
                report.append("")
        
        return '\n'.join(report)


@pytest.mark.integration
@pytest.mark.slow
class TestCodeConsistency:
    """Test code consistency and duplication detection."""
    
    @pytest.fixture(scope="class")
    def detector(self):
        """Create duplication detector instance."""
        project_root = Path(__file__).parent.parent
        detector = DuplicationDetector(project_root)
        detector.analyze_codebase()
        return detector
    
    def test_no_excessive_exact_duplicates(self, detector):
        """Test that there are not too many exact code duplicates."""
        duplicates = detector.exact_duplicates
        
        # Allow some duplicates (common patterns), but flag excessive duplication
        max_allowed_duplicates = 10  # Adjust based on project needs
        
        assert len(duplicates) <= max_allowed_duplicates, \
            f"Found {len(duplicates)} exact duplicates. Consider refactoring common code into shared utilities."
        
        # If duplicates found, provide details for investigation
        if duplicates:
            print(f"\nFound {len(duplicates)} exact duplicates:")
            for i, (block1, block2) in enumerate(duplicates[:5]):
                print(f"  {i+1}. {block1.file_path}:{block1.start_line} <-> {block2.file_path}:{block2.start_line}")
    
    def test_similarity_threshold_compliance(self, detector):
        """Test that similar blocks don't exceed reasonable thresholds."""
        similar_blocks = detector.similar_blocks
        
        # Allow some similar blocks, but flag excessive similarity
        max_allowed_similar = 20
        high_similarity_threshold = 0.95
        
        assert len(similar_blocks) <= max_allowed_similar, \
            f"Found {len(similar_blocks)} similar blocks. Consider extracting common patterns."
        
        # Check for very high similarity (might be near-duplicates)
        very_similar = [s for s in similar_blocks if s[2] >= high_similarity_threshold]
        
        assert len(very_similar) <= 5, \
            f"Found {len(very_similar)} blocks with >95% similarity. These are likely duplicates."
        
        if very_similar:
            print(f"\nFound {len(very_similar)} very similar blocks:")
            for block1, block2, similarity in very_similar[:3]:
                print(f"  {block1.file_path}:{block1.start_line} <-> {block2.file_path}:{block2.start_line} ({similarity:.1%})")
    
    def test_minimal_orphaned_imports(self, detector):
        """Test that orphaned imports are minimal."""
        orphaned_imports = detector.orphaned_imports
        
        # Allow some orphaned imports (might be intentional), but flag excessive ones
        max_files_with_orphans = 15
        max_orphans_per_file = 5
        
        assert len(orphaned_imports) <= max_files_with_orphans, \
            f"Found orphaned imports in {len(orphaned_imports)} files. Consider cleaning up unused imports."
        
        # Check individual files
        excessive_orphans = {
            file_path: imports for file_path, imports in orphaned_imports.items()
            if len(imports) > max_orphans_per_file
        }
        
        assert len(excessive_orphans) == 0, \
            f"Files with excessive orphaned imports: {list(excessive_orphans.keys())}"
        
        if orphaned_imports:
            total_orphans = sum(len(imports) for imports in orphaned_imports.values())
            print(f"\nFound {total_orphans} orphaned imports across {len(orphaned_imports)} files")
    
    def test_consistent_coding_patterns(self, detector):
        """Test that coding patterns are reasonably consistent."""
        inconsistencies = detector.inconsistent_patterns
        
        # Check each type of inconsistency
        if 'error_handling' in inconsistencies:
            error_issues = inconsistencies['error_handling']
            assert len(error_issues) <= 3, \
                f"Found {len(error_issues)} error handling inconsistencies"
        
        if 'logging' in inconsistencies:
            logging_issues = inconsistencies['logging']
            assert len(logging_issues) <= 2, \
                f"Found {len(logging_issues)} logging inconsistencies"
        
        if 'docstrings' in inconsistencies:
            docstring_issues = inconsistencies['docstrings']
            # Allow some docstring style variation
            assert len(docstring_issues) <= 1, \
                f"Found {len(docstring_issues)} docstring style inconsistencies"
    
    def test_generate_consistency_report(self, detector):
        """Test that consistency report can be generated."""
        report = detector.generate_report()
        
        assert isinstance(report, str), "Report should be a string"
        assert len(report) > 0, "Report should not be empty"
        assert "StyleStack Code Consistency Report" in report, "Report should have proper header"
        
        # Save report for manual review
        reports_dir = Path(__file__).parent.parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        report_file = reports_dir / "code_consistency_report.txt"
        report_file.write_text(report)
        
        print(f"\nCode consistency report saved to: {report_file}")
    
    def test_codebase_metrics_reasonable(self, detector):
        """Test that overall codebase metrics are reasonable."""
        total_blocks = len(detector.code_blocks)
        
        # Should have found reasonable number of code blocks
        assert total_blocks >= 50, f"Should find reasonable number of code blocks, found {total_blocks}"
        assert total_blocks <= 1000, f"Code block count seems excessive: {total_blocks}"
        
        # Calculate duplication ratio
        if total_blocks > 0:
            exact_dup_ratio = len(detector.exact_duplicates) / total_blocks
            similar_ratio = len(detector.similar_blocks) / total_blocks
            
            assert exact_dup_ratio <= 0.1, f"Exact duplication ratio too high: {exact_dup_ratio:.1%}"
            assert similar_ratio <= 0.15, f"Similarity ratio too high: {similar_ratio:.1%}"
    
    @pytest.mark.slow
    def test_specific_duplication_patterns(self, detector):
        """Test for specific types of duplication patterns."""
        
        # Look for duplicated error handling patterns
        error_handling_blocks = []
        logging_blocks = []
        import_blocks = []
        
        for block in detector.code_blocks:
            content_lower = block.content.lower()
            
            # Error handling patterns
            if any(pattern in content_lower for pattern in ['try:', 'except', 'raise']):
                error_handling_blocks.append(block)
            
            # Logging patterns
            if any(pattern in content_lower for pattern in ['log.', 'logger.', 'logging.']):
                logging_blocks.append(block)
            
            # Import validation patterns
            if any(pattern in content_lower for pattern in ['import ', 'from ']):
                import_blocks.append(block)
        
        # Check for excessive duplication in specific patterns
        if error_handling_blocks:
            # Find duplicates within error handling blocks
            error_duplicates = []
            for i, block1 in enumerate(error_handling_blocks):
                for block2 in error_handling_blocks[i+1:]:
                    if block1.similarity_to(block2) > 0.9:
                        error_duplicates.append((block1, block2))
            
            assert len(error_duplicates) <= 5, \
                f"Too many duplicated error handling patterns: {len(error_duplicates)}"
        
        print(f"\nPattern analysis:")
        print(f"  Error handling blocks: {len(error_handling_blocks)}")
        print(f"  Logging blocks: {len(logging_blocks)}")
        print(f"  Import blocks: {len(import_blocks)}")


@pytest.mark.unit
class TestDuplicationDetector:
    """Unit tests for the DuplicationDetector class."""
    
    def test_code_block_creation(self):
        """Test CodeBlock creation and properties."""
        content = '''def example_function():
    """Example function."""
    return True'''
        
        block = CodeBlock(content, "test.py", 1, 3, "function")
        
        assert block.content == content
        assert block.file_path == "test.py"
        assert block.start_line == 1
        assert block.end_line == 3
        assert block.block_type == "function"
        assert len(block.hash) == 32  # MD5 hash length
        assert block.normalized != content  # Should be normalized
    
    def test_code_block_similarity(self):
        """Test similarity calculation between code blocks."""
        content1 = '''def func1():
    x = 1
    return x + 1'''
        
        content2 = '''def func2():
    y = 1
    return y + 1'''
        
        content3 = '''def completely_different():
    print("Hello world")
    return "different"'''
        
        block1 = CodeBlock(content1, "test1.py", 1, 3, "function")
        block2 = CodeBlock(content2, "test2.py", 1, 3, "function")
        block3 = CodeBlock(content3, "test3.py", 1, 3, "function")
        
        # Similar blocks should have high similarity
        similarity_12 = block1.similarity_to(block2)
        assert similarity_12 > 0.7, f"Similar blocks should have high similarity: {similarity_12}"
        
        # Different blocks should have low similarity
        similarity_13 = block1.similarity_to(block3)
        assert similarity_13 < 0.3, f"Different blocks should have low similarity: {similarity_13}"
    
    def test_duplication_detector_initialization(self):
        """Test DuplicationDetector initialization."""
        project_root = Path(__file__).parent.parent
        detector = DuplicationDetector(project_root)
        
        assert detector.project_root == project_root
        assert detector.tools_dir == project_root / "tools"
        assert detector.min_lines == 5
        assert detector.similarity_threshold == 0.85
        assert isinstance(detector.code_blocks, list)


if __name__ == "__main__":
    # Can be run directly for analysis
    project_root = Path(__file__).parent.parent
    detector = DuplicationDetector(project_root)
    
    print("Running code consistency analysis...")
    summary = detector.analyze_codebase()
    
    print("\nSummary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    report = detector.generate_report()
    print("\n" + report)
    
    # Save report
    reports_dir = project_root / "reports"
    reports_dir.mkdir(exist_ok=True)
    report_file = reports_dir / "consistency_analysis.txt"
    report_file.write_text(report)
    print(f"\nFull report saved to: {report_file}")