#!/usr/bin/env python3
"""
Test consolidation analyzer for identifying test file duplication and overlap.
"""

import pytest
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
import ast
import re
from unittest.mock import patch, mock_open


class TestConsolidationAnalyzer:
    """Test analyzer for consolidation assessment"""
    
    def __init__(self, tests_directory: str = "tests"):
        self.tests_dir = Path(tests_directory)
        self.test_files = []
        self.duplication_patterns = {}
        self.coverage_map = {}
        self.performance_metrics = {}
    
    def discover_test_files(self) -> List[Path]:
        """Discover all test files in the test directory"""
        test_files = []
        for pattern in ["test_*.py", "*_test.py"]:
            test_files.extend(self.tests_dir.rglob(pattern))
        return [f for f in test_files if f.is_file() and not f.name.startswith('__')]
    
    def analyze_imports(self, file_path: Path) -> Set[str]:
        """Analyze imports in a test file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            imports = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
            
            return imports
        except Exception:
            return set()
    
    def analyze_test_functions(self, file_path: Path) -> Set[str]:
        """Analyze test functions in a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            test_functions = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name.startswith('test_'):
                        test_functions.add(node.name)
            
            return test_functions
        except Exception:
            return set()
    
    def detect_duplication_patterns(self) -> Dict[str, List[Path]]:
        """Detect duplication patterns across test files"""
        patterns = {}
        
        # Group by base name patterns
        base_names = {}
        for file_path in self.test_files:
            base_name = self._extract_base_name(file_path.name)
            if base_name not in base_names:
                base_names[base_name] = []
            base_names[base_name].append(file_path)
        
        # Identify groups with multiple files
        for base_name, files in base_names.items():
            if len(files) > 1:
                patterns[base_name] = files
        
        return patterns
    
    def _extract_base_name(self, filename: str) -> str:
        """Extract base name from test file"""
        # Remove test_ prefix and .py suffix
        base = filename.replace('test_', '').replace('.py', '')
        
        # Remove common suffixes that indicate variations
        suffixes = ['_comprehensive', '_modern', '_simple', '_methods', 
                   '_missing_coverage', '_phase4', '_basic', '_advanced']
        
        for suffix in suffixes:
            base = base.replace(suffix, '')
        
        return base
    
    def analyze_coverage_overlap(self) -> Dict[str, Dict[str, float]]:
        """Analyze test coverage overlap between files"""
        overlap_matrix = {}
        
        for file1 in self.test_files:
            imports1 = self.analyze_imports(file1)
            functions1 = self.analyze_test_functions(file1)
            
            overlap_matrix[str(file1)] = {}
            
            for file2 in self.test_files:
                if file1 == file2:
                    continue
                
                imports2 = self.analyze_imports(file2)
                functions2 = self.analyze_test_functions(file2)
                
                # Calculate overlap percentage
                import_overlap = len(imports1 & imports2) / max(len(imports1 | imports2), 1)
                function_overlap = len(functions1 & functions2) / max(len(functions1 | functions2), 1)
                
                total_overlap = (import_overlap + function_overlap) / 2
                overlap_matrix[str(file1)][str(file2)] = total_overlap
        
        return overlap_matrix
    
    def generate_consolidation_matrix(self) -> Dict[str, Dict[str, any]]:
        """Generate consolidation priority matrix"""
        matrix = {}
        
        for pattern_name, files in self.duplication_patterns.items():
            total_size = sum(f.stat().st_size for f in files)
            file_count = len(files)
            
            # Priority scoring (higher = more urgent)
            priority_score = file_count * 10 + (total_size / 1000)  # Size in KB
            
            matrix[pattern_name] = {
                'files': [str(f) for f in files],
                'file_count': file_count,
                'total_size_bytes': total_size,
                'priority_score': priority_score,
                'consolidation_potential': 'HIGH' if file_count >= 3 else 'MEDIUM'
            }
        
        return matrix


class TestConsolidationAnalyzerTests:
    """Tests for the test consolidation analyzer"""
    
    @pytest.fixture
    def analyzer(self, tmp_path):
        """Create analyzer instance with temporary test directory"""
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        
        # Create mock test files
        (test_dir / "test_ooxml_processor.py").write_text("""
import pytest
from tools.ooxml_processor import OOXMLProcessor

def test_basic_processing():
    processor = OOXMLProcessor()
    assert processor is not None

def test_xml_validation():
    pass
        """)
        
        (test_dir / "test_ooxml_processor_comprehensive.py").write_text("""
import pytest
from tools.ooxml_processor import OOXMLProcessor
from unittest.mock import Mock

def test_advanced_processing():
    processor = OOXMLProcessor()
    assert processor is not None

def test_comprehensive_validation():
    pass
        """)
        
        (test_dir / "test_theme_resolver.py").write_text("""
import pytest
from tools.theme_resolver import ThemeResolver

def test_theme_resolution():
    resolver = ThemeResolver()
    assert resolver is not None
        """)
        
        return TestConsolidationAnalyzer(str(test_dir))
    
    def test_discover_test_files(self, analyzer):
        """Test that test files are discovered correctly"""
        files = analyzer.discover_test_files()
        assert len(files) == 3
        assert all(f.name.startswith('test_') for f in files)
    
    def test_analyze_imports(self, analyzer):
        """Test import analysis"""
        files = analyzer.discover_test_files()
        ooxml_file = next(f for f in files if 'test_ooxml_processor.py' == f.name)
        
        imports = analyzer.analyze_imports(ooxml_file)
        assert 'pytest' in imports
        assert 'tools.ooxml_processor' in imports
    
    def test_analyze_test_functions(self, analyzer):
        """Test function analysis"""
        files = analyzer.discover_test_files()
        ooxml_file = next(f for f in files if 'test_ooxml_processor.py' == f.name)
        
        functions = analyzer.analyze_test_functions(ooxml_file)
        assert 'test_basic_processing' in functions
        assert 'test_xml_validation' in functions
    
    def test_detect_duplication_patterns(self, analyzer):
        """Test duplication pattern detection"""
        analyzer.test_files = analyzer.discover_test_files()
        patterns = analyzer.detect_duplication_patterns()
        
        assert 'ooxml_processor' in patterns
        assert len(patterns['ooxml_processor']) == 2
    
    def test_extract_base_name(self, analyzer):
        """Test base name extraction"""
        assert analyzer._extract_base_name('test_ooxml_processor.py') == 'ooxml_processor'
        assert analyzer._extract_base_name('test_ooxml_processor_comprehensive.py') == 'ooxml_processor'
        assert analyzer._extract_base_name('test_theme_resolver_phase4.py') == 'theme_resolver'
    
    def test_analyze_coverage_overlap(self, analyzer):
        """Test coverage overlap analysis"""
        analyzer.test_files = analyzer.discover_test_files()
        overlap = analyzer.analyze_coverage_overlap()
        
        assert isinstance(overlap, dict)
        assert len(overlap) == len(analyzer.test_files)
    
    def test_generate_consolidation_matrix(self, analyzer):
        """Test consolidation matrix generation"""
        analyzer.test_files = analyzer.discover_test_files()
        analyzer.duplication_patterns = analyzer.detect_duplication_patterns()
        
        matrix = analyzer.generate_consolidation_matrix()
        
        assert 'ooxml_processor' in matrix
        assert matrix['ooxml_processor']['file_count'] == 2
        assert 'priority_score' in matrix['ooxml_processor']
        assert 'consolidation_potential' in matrix['ooxml_processor']


if __name__ == "__main__":
    pytest.main([__file__])