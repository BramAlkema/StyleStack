#!/usr/bin/env python3
"""
StyleStack Performance Benchmarking System

Comprehensive performance testing and optimization framework for the modular architecture.
Measures performance across all core components and identifies optimization opportunities.
"""


from typing import Any, Dict, List, Optional
import time
import statistics
import tempfile
import zipfile
import json
import threading
from pathlib import Path
from dataclasses import dataclass, field
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import core components for benchmarking
from tools.template_analyzer import TemplateAnalyzer
from tools.substitution.pipeline import SubstitutionPipeline
from tools.handlers.types import OOXMLFormat
from tools.handlers.formats import FormatRegistry
from tools.multi_format_ooxml_handler import MultiFormatOOXMLHandler


@dataclass
class BenchmarkResult:
    """Result of a performance benchmark."""
    name: str
    duration: float
    operations_per_second: float
    memory_usage: Optional[int] = None
    success_rate: float = 100.0
    error_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkSuite:
    """Collection of benchmark results."""
    name: str
    results: List[BenchmarkResult] = field(default_factory=list)
    total_duration: float = 0.0
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    
    def add_result(self, result: BenchmarkResult):
        """Add a benchmark result."""
        self.results.append(result)
        self.total_duration += result.duration
    
    def get_summary(self) -> Dict[str, Any]:
        """Get benchmark suite summary."""
        return {
            'name': self.name,
            'total_benchmarks': len(self.results),
            'total_duration': self.total_duration,
            'average_duration': self.total_duration / len(self.results) if self.results else 0,
            'fastest_operation': min(self.results, key=lambda r: r.duration).name if self.results else None,
            'slowest_operation': max(self.results, key=lambda r: r.duration).name if self.results else None,
            'overall_success_rate': statistics.mean([r.success_rate for r in self.results]) if self.results else 0,
            'timestamp': self.timestamp
        }


class PerformanceBenchmark:
    """Main benchmarking system for StyleStack components."""
    
    def __init__(self):
        self.suites: List[BenchmarkSuite] = []
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create test data
        self._create_test_templates()
        self._create_test_variables()
    
    def __del__(self):
        """Clean up temporary files."""
        import shutil
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def benchmark_timer(self, name: str):
        """Create a benchmark timer context manager."""
        class BenchmarkTimer:
            def __init__(self, benchmark_instance, name):
                self.benchmark = benchmark_instance
                self.name = name
                self.result = None
            
            def __enter__(self):
                self.start_time = time.perf_counter()
                self.start_memory = self.benchmark._get_memory_usage()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                end_time = time.perf_counter()
                end_memory = self.benchmark._get_memory_usage()
                
                duration = end_time - self.start_time
                memory_delta = (end_memory - self.start_memory) if (self.start_memory and end_memory) else None
                
                success = exc_type is None
                error_count = 0 if success else 1
                
                if exc_type is not None:
                    print(f"Error in benchmark {self.name}: {exc_val}")
                
                self.result = BenchmarkResult(
                    name=self.name,
                    duration=duration,
                    operations_per_second=1.0 / duration if duration > 0 else 0,
                    memory_usage=memory_delta,
                    success_rate=100.0 if success else 0.0,
                    error_count=error_count
                )
        
        return BenchmarkTimer(self, name)
    
    def _get_memory_usage(self) -> Optional[int]:
        """Get current memory usage in bytes."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss
        except ImportError:
            return None
    
    def _create_test_templates(self):
        """Create test templates of various sizes."""
        self.test_templates = {}
        
        # Small template
        small_template = self.temp_dir / "small_template.potx"
        self._create_template(small_template, slides=1, complexity="basic")
        self.test_templates['small'] = small_template
        
        # Medium template
        medium_template = self.temp_dir / "medium_template.potx"
        self._create_template(medium_template, slides=5, complexity="standard")
        self.test_templates['medium'] = medium_template
        
        # Large template
        large_template = self.temp_dir / "large_template.potx"
        self._create_template(large_template, slides=20, complexity="complex")
        self.test_templates['large'] = large_template
    
    def _create_template(self, path: Path, slides: int = 1, complexity: str = "basic"):
        """Create a test template with specified characteristics."""
        with zipfile.ZipFile(path, 'w') as zf:
            # Content types
            zf.writestr('[Content_Types].xml', '''<?xml version="1.0"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-presentationml.presentation.main+xml"/>
    <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
</Types>''')
            
            # Main presentation
            slide_refs = ""
            for i in range(1, slides + 1):
                slide_refs += f'<p:sldId id="{i + 255}" r:id="rId{i + 1}"/>'
            
            zf.writestr('ppt/presentation.xml', f'''<?xml version="1.0"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <p:sldMasterIdLst>
        <p:sldMasterId id="2147483648" r:id="rId1"/>
    </p:sldMasterIdLst>
    <p:sldIdLst>
        {slide_refs}
    </p:sldIdLst>
</p:presentation>''')
            
            # Theme
            theme_complexity = self._get_theme_content(complexity)
            zf.writestr('ppt/theme/theme1.xml', theme_complexity)
            
            # Slides
            for i in range(1, slides + 1):
                slide_content = self._get_slide_content(i, complexity)
                zf.writestr(f'ppt/slides/slide{i}.xml', slide_content)
    
    def _get_theme_content(self, complexity: str) -> str:
        """Get theme content based on complexity level."""
        base_theme = '''<?xml version="1.0"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="StyleStack Theme">
    <a:themeElements>
        <a:clrScheme name="Professional">
            <a:dk1><a:sysClr val="windowText"/></a:dk1>
            <a:lt1><a:sysClr val="window"/></a:lt1>'''
        
        if complexity == "complex":
            # Add more color scheme entries for complex theme
            base_theme += '''
            <a:dk2><a:srgbClr val="44546A"/></a:dk2>
            <a:lt2><a:srgbClr val="E7E6E6"/></a:lt2>
            <a:accent1><a:srgbClr val="5B9BD5"/></a:accent1>
            <a:accent2><a:srgbClr val="70AD47"/></a:accent2>
            <a:accent3><a:srgbClr val="FFC000"/></a:accent3>
            <a:accent4><a:srgbClr val="ED7D31"/></a:accent4>
            <a:accent5><a:srgbClr val="A5A5A5"/></a:accent5>
            <a:accent6><a:srgbClr val="264478"/></a:accent6>'''
        
        base_theme += '''
        </a:clrScheme>
        <a:fontScheme name="Professional">
            <a:majorFont>
                <a:latin typeface="Calibri Light"/>
            </a:majorFont>
            <a:minorFont>
                <a:latin typeface="Calibri"/>
            </a:minorFont>
        </a:fontScheme>
    </a:themeElements>
</a:theme>'''
        
        return base_theme
    
    def _get_slide_content(self, slide_num: int, complexity: str) -> str:
        """Get slide content based on complexity level."""
        shapes = ""
        
        if complexity == "complex":
            # Add multiple shapes for complex slides
            for i in range(1, 6):  # 5 shapes per slide
                shapes += f'''
                <p:sp>
                    <p:nvSpPr>
                        <p:cNvPr id="{i}" name="Shape {i}"/>
                        <p:cNvSpPr/>
                        <p:nvPr/>
                    </p:nvSpPr>
                    <p:spPr/>
                    <p:txBody>
                        <a:bodyPr/>
                        <a:p><a:r><a:t>Content {i} on slide {slide_num}</a:t></a:r></a:p>
                    </p:txBody>
                </p:sp>'''
        else:
            # Simple slide with one shape
            shapes = f'''
            <p:sp>
                <p:nvSpPr>
                    <p:cNvPr id="1" name="Title"/>
                    <p:cNvSpPr/>
                    <p:nvPr/>
                </p:nvSpPr>
                <p:spPr/>
                <p:txBody>
                    <a:bodyPr/>
                    <a:p><a:r><a:t>Slide {slide_num}</a:t></a:r></a:p>
                </p:txBody>
            </p:sp>'''
        
        return f'''<?xml version="1.0"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
    <p:cSld>
        <p:spTree>
            <p:nvGrpSpPr>
                <p:cNvPr id="1" name=""/>
                <p:cNvGrpSpPr/>
                <p:nvPr/>
            </p:nvGrpSpPr>
            <p:grpSpPr/>
            {shapes}
        </p:spTree>
    </p:cSld>
</p:sld>'''
    
    def _create_test_variables(self):
        """Create test variable sets of various sizes."""
        self.test_variables = {
            'small': {
                'primary_color': 'FF0000',
                'heading_font': 'Arial'
            },
            'medium': {
                'primary_color': 'FF0000',
                'secondary_color': '00FF00', 
                'accent_color': '0000FF',
                'heading_font': 'Arial',
                'body_font': 'Calibri',
                'title_text': 'Sample Title'
            },
            'large': {
                **{f'color_{i}': f'{i:02d}0000' for i in range(1, 21)},
                **{f'font_{i}': f'Font{i}' for i in range(1, 11)},
                **{f'text_{i}': f'Text Content {i}' for i in range(1, 31)}
            }
        }
    
    def benchmark_template_analyzer(self) -> BenchmarkSuite:
        """Benchmark the template analyzer component."""
        suite = BenchmarkSuite("Template Analyzer")
        analyzer = TemplateAnalyzer()
        
        # Test initialization performance
        with self.benchmark_timer("analyzer_initialization") as timer:
            for _ in range(100):
                test_analyzer = TemplateAnalyzer()
        suite.add_result(timer.result)
        
        # Test statistics retrieval
        with self.benchmark_timer("get_analysis_statistics") as timer:
            for _ in range(1000):
                stats = analyzer.get_analysis_statistics()
        suite.add_result(timer.result)
        
        return suite
    
    def benchmark_substitution_pipeline(self) -> BenchmarkSuite:
        """Benchmark the substitution pipeline component."""
        suite = BenchmarkSuite("Substitution Pipeline")
        pipeline = SubstitutionPipeline()
        
        # Test pipeline initialization
        with self.benchmark_timer("pipeline_initialization") as timer:
            for _ in range(50):
                test_pipeline = SubstitutionPipeline()
        suite.add_result(timer.result)
        
        # Test variable substitution with different payload sizes
        for size in ['small', 'medium', 'large']:
            xml_content = f'''<?xml version="1.0"?>
<root>
    <data>{json.dumps(self.test_variables[size])}</data>
</root>'''
            
            with self.benchmark_timer(f"substitute_variables_{size}") as timer:
                for _ in range(10):
                    try:
                        result_obj = pipeline.substitute_variables(xml_content, self.test_variables[size])
                    except Exception:
                        pass  # Some methods may not be fully implemented
            suite.add_result(timer.result)
        
        return suite
    
    def benchmark_format_registry(self) -> BenchmarkSuite:
        """Benchmark the format registry component."""
        suite = BenchmarkSuite("Format Registry")
        
        # Test format detection
        test_paths = ['test.potx', 'test.dotx', 'test.xltx'] * 100
        
        with self.benchmark_timer("format_detection") as timer:
            for path in test_paths:
                format_type = FormatRegistry.detect_format(path)
        suite.add_result(timer.result)
        
        # Test structure retrieval
        formats = [OOXMLFormat.POWERPOINT, OOXMLFormat.WORD, OOXMLFormat.EXCEL]
        
        with self.benchmark_timer("structure_retrieval") as timer:
            for _ in range(1000):
                for format_type in formats:
                    structure = FormatRegistry.get_structure(format_type)
        suite.add_result(timer.result)
        
        return suite
    
    def benchmark_multi_format_handler(self) -> BenchmarkSuite:
        """Benchmark the multi-format OOXML handler."""
        suite = BenchmarkSuite("Multi-Format Handler")
        
        # Test handler initialization
        with self.benchmark_timer("handler_initialization") as timer:
            for _ in range(20):
                handler = MultiFormatOOXMLHandler()
        suite.add_result(timer.result)
        
        return suite
    
    def benchmark_file_operations(self) -> BenchmarkSuite:
        """Benchmark file I/O operations."""
        suite = BenchmarkSuite("File Operations")
        
        # Test template reading performance
        for size in ['small', 'medium', 'large']:
            template_path = self.test_templates[size]
            
            with self.benchmark_timer(f"read_template_{size}") as timer:
                for _ in range(10):
                    with zipfile.ZipFile(template_path, 'r') as zf:
                        files = zf.namelist()
                        for file in files[:3]:  # Read first 3 files
                            content = zf.read(file)
            suite.add_result(timer.result)
        
        return suite
    
    def benchmark_concurrent_operations(self) -> BenchmarkSuite:
        """Benchmark concurrent operations."""
        suite = BenchmarkSuite("Concurrent Operations")
        
        def worker_task():
            analyzer = TemplateAnalyzer()
            for _ in range(10):
                stats = analyzer.get_analysis_statistics()
        
        # Test concurrent analyzer usage
        with self.benchmark_timer("concurrent_analyzer_access") as timer:
            threads = []
            for _ in range(10):
                thread = threading.Thread(target=worker_task)
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
        suite.add_result(timer.result)
        
        return suite
    
    def run_full_benchmark(self) -> List[BenchmarkSuite]:
        """Run complete performance benchmark suite."""
        print("🚀 Starting StyleStack Performance Benchmarks...")
        
        benchmarks = [
            self.benchmark_template_analyzer,
            self.benchmark_substitution_pipeline,
            self.benchmark_format_registry,
            self.benchmark_multi_format_handler,
            self.benchmark_file_operations,
            self.benchmark_concurrent_operations
        ]
        
        results = []
        for benchmark_func in benchmarks:
            print(f"⏱️  Running {benchmark_func.__name__}...")
            suite = benchmark_func()
            results.append(suite)
            self.suites.append(suite)
            
            # Print summary
            summary = suite.get_summary()
            print(f"   ✅ {summary['name']}: {summary['total_benchmarks']} tests, "
                  f"{summary['total_duration']:.3f}s total")
        
        return results
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        report = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'system_info': self._get_system_info(),
            'benchmarks': [],
            'recommendations': []
        }
        
        total_duration = 0
        for suite in self.suites:
            suite_summary = suite.get_summary()
            report['benchmarks'].append({
                'suite': suite_summary,
                'results': [
                    {
                        'name': r.name,
                        'duration': r.duration,
                        'ops_per_sec': r.operations_per_second,
                        'success_rate': r.success_rate
                    } for r in suite.results
                ]
            })
            total_duration += suite.total_duration
        
        # Generate recommendations
        report['recommendations'] = self._generate_recommendations()
        report['total_benchmark_time'] = total_duration
        
        return report
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for the report."""
        info = {
            'python_version': sys.version,
            'platform': sys.platform
        }
        
        try:
            import psutil
            info.update({
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available
            })
        except ImportError:
            info['psutil_available'] = False
        
        return info
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        # Analyze results for optimization opportunities
        for suite in self.suites:
            slow_operations = [r for r in suite.results if r.duration > 0.1]
            if slow_operations:
                recommendations.append(
                    f"Consider optimizing slow operations in {suite.name}: "
                    f"{', '.join(r.name for r in slow_operations)}"
                )
        
        # Generic recommendations
        recommendations.extend([
            "Consider implementing caching for frequently accessed data",
            "Evaluate lazy loading for heavy imports",
            "Consider connection pooling for concurrent operations",
            "Implement result memoization for expensive computations"
        ])
        
        return recommendations


def main():
    """Run performance benchmarks and generate report."""
    benchmark = PerformanceBenchmark()
    
    try:
        # Run benchmarks
        results = benchmark.run_full_benchmark()
        
        # Generate report
        report = benchmark.generate_performance_report()
        
        # Save report
        report_path = Path('performance_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 Performance Report Summary:")
        print(f"   Total Suites: {len(results)}")
        print(f"   Total Duration: {report['total_benchmark_time']:.3f}s")
        print(f"   Report saved to: {report_path}")
        
        # Print top recommendations
        print(f"\n💡 Top Recommendations:")
        for i, rec in enumerate(report['recommendations'][:3], 1):
            print(f"   {i}. {rec}")
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        raise


if __name__ == '__main__':
    main()