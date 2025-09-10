#!/usr/bin/env python3
"""
StyleStack Performance Benchmarking Suite

Comprehensive benchmarking system for the JSON-to-OOXML processing pipeline.
Provides realistic workload patterns to test small templates, large templates, 
batch operations, and concurrent processing scenarios.
"""


from typing import Any, Dict, List, NamedTuple, Optional
import os
import sys
import time
import json
import tempfile
import concurrent.futures
import threading
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import statistics
import zipfile
import random
from lxml import etree

# Import StyleStack components
try:
    from .json_patch_parser import JSONPatchParser
    from .performance_profiler import PerformanceProfiler
except ImportError:
    # Handle relative import issues for standalone execution
    from tools.json_patch_parser import JSONPatchParser
    from tools.performance_profiler import PerformanceProfiler

import logging
logger = logging.getLogger(__name__)


class WorkloadType(Enum):
    """Types of workloads for benchmarking."""
    SMALL_TEMPLATE = "small_template"
    MEDIUM_TEMPLATE = "medium_template"
    LARGE_TEMPLATE = "large_template"
    COMPLEX_TEMPLATE = "complex_template"
    BATCH_SMALL = "batch_small"
    BATCH_MEDIUM = "batch_medium"
    BATCH_LARGE = "batch_large"
    CONCURRENT_PROCESSING = "concurrent_processing"
    MEMORY_INTENSIVE = "memory_intensive"
    CPU_INTENSIVE = "cpu_intensive"


class BenchmarkResult(NamedTuple):
    """Result of a single benchmark run."""
    workload_type: WorkloadType
    execution_time: float
    memory_peak_mb: float
    cpu_usage_percent: float
    throughput_ops_per_sec: float
    error_count: int
    success: bool
    metadata: Dict[str, Any]


@dataclass
class WorkloadConfig:
    """Configuration for a benchmark workload."""
    workload_type: WorkloadType
    iterations: int = 1
    concurrent_workers: int = 1
    template_count: int = 1
    patch_count: int = 10
    complexity_level: int = 1  # 1-5 scale
    memory_limit_mb: Optional[int] = None
    time_limit_seconds: Optional[float] = None
    warmup_iterations: int = 1
    
    # Template characteristics
    slide_count: int = 10
    element_count_per_slide: int = 20
    nested_element_depth: int = 3
    
    # Patch operation characteristics
    xpath_complexity: int = 1  # 1-5 scale
    value_size_bytes: int = 1024
    operation_types: List[str] = field(default_factory=lambda: ["set", "insert", "merge"])


@dataclass
class BenchmarkSuite:
    """Complete benchmark suite configuration."""
    name: str
    description: str
    workloads: List[WorkloadConfig]
    output_directory: Path
    enable_profiling: bool = True
    enable_monitoring: bool = True
    parallel_execution: bool = False
    
    @classmethod
    def create_standard_suite(cls) -> 'BenchmarkSuite':
        """Create a standard benchmark suite with typical workloads."""
        return cls(
            name="StyleStack Standard Performance Suite",
            description="Comprehensive performance testing covering all major use cases",
            workloads=[
                # Small template tests
                WorkloadConfig(
                    workload_type=WorkloadType.SMALL_TEMPLATE,
                    iterations=100,
                    patch_count=5,
                    slide_count=3,
                    element_count_per_slide=5
                ),
                
                # Medium template tests
                WorkloadConfig(
                    workload_type=WorkloadType.MEDIUM_TEMPLATE,
                    iterations=50,
                    patch_count=25,
                    slide_count=10,
                    element_count_per_slide=15
                ),
                
                # Large template tests
                WorkloadConfig(
                    workload_type=WorkloadType.LARGE_TEMPLATE,
                    iterations=10,
                    patch_count=100,
                    slide_count=50,
                    element_count_per_slide=30,
                    nested_element_depth=5
                ),
                
                # Complex template tests
                WorkloadConfig(
                    workload_type=WorkloadType.COMPLEX_TEMPLATE,
                    iterations=5,
                    patch_count=200,
                    slide_count=25,
                    element_count_per_slide=50,
                    nested_element_depth=8,
                    xpath_complexity=5,
                    value_size_bytes=8192
                ),
                
                # Batch processing tests
                WorkloadConfig(
                    workload_type=WorkloadType.BATCH_SMALL,
                    iterations=10,
                    template_count=50,
                    patch_count=10,
                    slide_count=5,
                    element_count_per_slide=10
                ),
                
                WorkloadConfig(
                    workload_type=WorkloadType.BATCH_MEDIUM,
                    iterations=5,
                    template_count=20,
                    patch_count=50,
                    slide_count=15,
                    element_count_per_slide=20
                ),
                
                WorkloadConfig(
                    workload_type=WorkloadType.BATCH_LARGE,
                    iterations=2,
                    template_count=5,
                    patch_count=100,
                    slide_count=30,
                    element_count_per_slide=40
                ),
                
                # Concurrent processing tests
                WorkloadConfig(
                    workload_type=WorkloadType.CONCURRENT_PROCESSING,
                    iterations=20,
                    concurrent_workers=4,
                    template_count=20,
                    patch_count=25,
                    slide_count=10,
                    element_count_per_slide=15
                ),
                
                # Memory-intensive tests
                WorkloadConfig(
                    workload_type=WorkloadType.MEMORY_INTENSIVE,
                    iterations=3,
                    patch_count=500,
                    slide_count=100,
                    element_count_per_slide=100,
                    nested_element_depth=10,
                    value_size_bytes=32768
                ),
                
                # CPU-intensive tests
                WorkloadConfig(
                    workload_type=WorkloadType.CPU_INTENSIVE,
                    iterations=5,
                    patch_count=1000,
                    slide_count=20,
                    element_count_per_slide=50,
                    xpath_complexity=5,
                    operation_types=["set", "insert", "merge", "extend"]
                )
            ],
            output_directory=Path("benchmark_results")
        )
    
    @classmethod
    def create_quick_suite(cls) -> 'BenchmarkSuite':
        """Create a quick benchmark suite for CI/CD or development."""
        return cls(
            name="StyleStack Quick Performance Suite",
            description="Fast performance testing for development and CI",
            workloads=[
                WorkloadConfig(
                    workload_type=WorkloadType.SMALL_TEMPLATE,
                    iterations=10,
                    patch_count=5
                ),
                WorkloadConfig(
                    workload_type=WorkloadType.MEDIUM_TEMPLATE,
                    iterations=5,
                    patch_count=15
                ),
                WorkloadConfig(
                    workload_type=WorkloadType.BATCH_SMALL,
                    iterations=3,
                    template_count=10,
                    patch_count=10
                ),
                WorkloadConfig(
                    workload_type=WorkloadType.CONCURRENT_PROCESSING,
                    iterations=5,
                    concurrent_workers=2,
                    template_count=5
                )
            ],
            output_directory=Path("quick_benchmark_results")
        )


class TemplateGenerator:
    """Generates synthetic OOXML templates for benchmarking."""
    
    def __init__(self):
        self.namespaces = {
            'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
            'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
        }
    
    def generate_pptx_template(self, config: WorkloadConfig, temp_dir: Path) -> Path:
        """Generate a synthetic PowerPoint template for benchmarking."""
        template_path = temp_dir / f"benchmark_template_{config.workload_type.value}.pptx"
        
        # Create a minimal OOXML structure
        with zipfile.ZipFile(template_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add [Content_Types].xml
            content_types = self._generate_content_types()
            zf.writestr("[Content_Types].xml", content_types)
            
            # Add _rels/.rels
            main_rels = self._generate_main_rels()
            zf.writestr("_rels/.rels", main_rels)
            
            # Add ppt/presentation.xml
            presentation = self._generate_presentation(config)
            zf.writestr("ppt/presentation.xml", presentation)
            
            # Add ppt/_rels/presentation.xml.rels
            pres_rels = self._generate_presentation_rels(config)
            zf.writestr("ppt/_rels/presentation.xml.rels", pres_rels)
            
            # Add slide masters and layouts
            slide_master = self._generate_slide_master()
            zf.writestr("ppt/slideMasters/slideMaster1.xml", slide_master)
            
            slide_layout = self._generate_slide_layout()
            zf.writestr("ppt/slideLayouts/slideLayout1.xml", slide_layout)
            
            # Add individual slides
            for i in range(config.slide_count):
                slide = self._generate_slide(config, i + 1)
                zf.writestr(f"ppt/slides/slide{i + 1}.xml", slide)
                
                # Add slide relationships
                slide_rels = self._generate_slide_rels()
                zf.writestr(f"ppt/slides/_rels/slide{i + 1}.xml.rels", slide_rels)
            
            # Add theme
            theme = self._generate_theme()
            zf.writestr("ppt/theme/theme1.xml", theme)
        
        return template_path
    
    def _generate_content_types(self) -> str:
        """Generate [Content_Types].xml content."""
        return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-presentationml.presentation.main+xml"/>
    <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-presentationml.slideMaster+xml"/>
    <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-presentationml.slideLayout+xml"/>
    <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
</Types>'''
    
    def _generate_main_rels(self) -> str:
        """Generate main relationships file."""
        return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>'''
    
    def _generate_presentation(self, config: WorkloadConfig) -> str:
        """Generate presentation.xml with specified number of slides."""
        slide_refs = '\n'.join([
            f'<p:sldId id="{256 + i}" r:id="rId{i + 1}"/>'
            for i in range(config.slide_count)
        ])
        
        return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" 
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <p:sldMasterIdLst>
        <p:sldMasterId id="2147483648" r:id="rId{config.slide_count + 1}"/>
    </p:sldMasterIdLst>
    <p:sldIdLst>
        {slide_refs}
    </p:sldIdLst>
    <p:sldSz cx="9144000" cy="6858000"/>
</p:presentation>'''
    
    def _generate_presentation_rels(self, config: WorkloadConfig) -> str:
        """Generate presentation relationships."""
        slide_rels = '\n'.join([
            f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i + 1}.xml"/>'
            for i in range(config.slide_count)
        ])
        
        return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    {slide_rels}
    <Relationship Id="rId{config.slide_count + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
    <Relationship Id="rId{config.slide_count + 2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>
</Relationships>'''
    
    def _generate_slide_master(self) -> str:
        """Generate slide master."""
        return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" 
             xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <p:cSld>
        <p:spTree>
            <p:nvGrpSpPr>
                <p:cNvPr id="1" name=""/>
                <p:cNvGrpSpPr/>
                <p:nvPr/>
            </p:nvGrpSpPr>
            <p:grpSpPr>
                <a:xfrm>
                    <a:off x="0" y="0"/>
                    <a:ext cx="0" cy="0"/>
                    <a:chOff x="0" y="0"/>
                    <a:chExt cx="0" cy="0"/>
                </a:xfrm>
            </p:grpSpPr>
        </p:spTree>
    </p:cSld>
    <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
    <p:sldLayoutIdLst>
        <p:sldLayoutId id="2147483649" r:id="rId1"/>
    </p:sldLayoutIdLst>
</p:sldMaster>'''
    
    def _generate_slide_layout(self) -> str:
        """Generate slide layout."""
        return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" 
             xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
    <p:cSld name="Title Slide">
        <p:spTree>
            <p:nvGrpSpPr>
                <p:cNvPr id="1" name=""/>
                <p:cNvGrpSpPr/>
                <p:nvPr/>
            </p:nvGrpSpPr>
            <p:grpSpPr>
                <a:xfrm>
                    <a:off x="0" y="0"/>
                    <a:ext cx="0" cy="0"/>
                    <a:chOff x="0" y="0"/>
                    <a:chExt cx="0" cy="0"/>
                </a:xfrm>
            </p:grpSpPr>
        </p:spTree>
    </p:cSld>
</p:sldLayout>'''
    
    def _generate_slide(self, config: WorkloadConfig, slide_number: int) -> str:
        """Generate individual slide with specified complexity."""
        elements = []
        
        for i in range(config.element_count_per_slide):
            element_id = (slide_number - 1) * config.element_count_per_slide + i + 2
            
            if config.nested_element_depth > 1:
                # Create nested structure for complexity
                nested_content = self._generate_nested_elements(config.nested_element_depth)
                element = f'''
                <p:sp>
                    <p:nvSpPr>
                        <p:cNvPr id="{element_id}" name="Element{element_id}"/>
                        <p:cNvSpPr/>
                        <p:nvPr/>
                    </p:nvSpPr>
                    <p:spPr>
                        <a:xfrm>
                            <a:off x="{i * 100000}" y="{i * 50000}"/>
                            <a:ext cx="1000000" cy="500000"/>
                        </a:xfrm>
                        <a:prstGeom prst="rect"/>
                        {nested_content}
                    </p:spPr>
                    <p:txBody>
                        <a:bodyPr/>
                        <a:lstStyle/>
                        <a:p>
                            <a:r>
                                <a:t>Element {element_id} Content</a:t>
                            </a:r>
                        </a:p>
                    </p:txBody>
                </p:sp>'''
            else:
                # Simple element
                element = f'''
                <p:sp>
                    <p:nvSpPr>
                        <p:cNvPr id="{element_id}" name="Element{element_id}"/>
                        <p:cNvSpPr/>
                        <p:nvPr/>
                    </p:nvSpPr>
                    <p:spPr>
                        <a:xfrm>
                            <a:off x="{i * 100000}" y="{i * 50000}"/>
                            <a:ext cx="1000000" cy="500000"/>
                        </a:xfrm>
                        <a:prstGeom prst="rect"/>
                    </p:spPr>
                    <p:txBody>
                        <a:bodyPr/>
                        <a:p>
                            <a:r>
                                <a:t>Element {element_id}</a:t>
                            </a:r>
                        </a:p>
                    </p:txBody>
                </p:sp>'''
            
            elements.append(element)
        
        elements_xml = '\n'.join(elements)
        
        return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" 
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <p:cSld>
        <p:spTree>
            <p:nvGrpSpPr>
                <p:cNvPr id="1" name=""/>
                <p:cNvGrpSpPr/>
                <p:nvPr/>
            </p:nvGrpSpPr>
            <p:grpSpPr>
                <a:xfrm>
                    <a:off x="0" y="0"/>
                    <a:ext cx="0" cy="0"/>
                    <a:chOff x="0" y="0"/>
                    <a:chExt cx="0" cy="0"/>
                </a:xfrm>
            </p:grpSpPr>
            {elements_xml}
        </p:spTree>
    </p:cSld>
</p:sld>'''
    
    def _generate_nested_elements(self, depth: int) -> str:
        """Generate nested XML elements for complexity testing."""
        if depth <= 1:
            return "<a:noFill/>"
        
        nested = self._generate_nested_elements(depth - 1)
        return f'''
        <a:effectLst>
            <a:glow rad="40000">
                <a:srgbClr val="00FF00">
                    <a:alpha val="60000"/>
                    {nested}
                </a:srgbClr>
            </a:glow>
        </a:effectLst>'''
    
    def _generate_slide_rels(self) -> str:
        """Generate slide relationships."""
        return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>'''
    
    def _generate_theme(self) -> str:
        """Generate theme file."""
        return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="StyleStack Test Theme">
    <a:themeElements>
        <a:clrScheme name="StyleStack">
            <a:dk1><a:sysClr val="windowText"/></a:dk1>
            <a:lt1><a:sysClr val="window"/></a:lt1>
            <a:dk2><a:srgbClr val="44546A"/></a:dk2>
            <a:lt2><a:srgbClr val="E7E6E6"/></a:lt2>
            <a:accent1><a:srgbClr val="4472C4"/></a:accent1>
            <a:accent2><a:srgbClr val="70AD47"/></a:accent2>
            <a:accent3><a:srgbClr val="FFC000"/></a:accent3>
            <a:accent4><a:srgbClr val="ED7D31"/></a:accent4>
            <a:accent5><a:srgbClr val="A5A5A5"/></a:accent5>
            <a:accent6><a:srgbClr val="264478"/></a:accent6>
            <a:hlink><a:srgbClr val="0563C1"/></a:hlink>
            <a:folHlink><a:srgbClr val="954F72"/></a:folHlink>
        </a:clrScheme>
        <a:fontScheme name="StyleStack">
            <a:majorFont>
                <a:latin typeface="Calibri Light"/>
            </a:majorFont>
            <a:minorFont>
                <a:latin typeface="Calibri"/>
            </a:minorFont>
        </a:fontScheme>
        <a:fmtScheme name="StyleStack">
            <a:fillStyleLst>
                <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
            </a:fillStyleLst>
            <a:lnStyleLst>
                <a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>
            </a:lnStyleLst>
            <a:effectStyleLst>
                <a:effectStyle><a:effectLst/></a:effectStyle>
            </a:effectStyleLst>
            <a:bgFillStyleLst>
                <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
            </a:bgFillStyleLst>
        </a:fmtScheme>
    </a:themeElements>
</a:theme>'''


class PatchGenerator:
    """Generates synthetic JSON patches for benchmarking."""
    
    def generate_patches(self, config: WorkloadConfig) -> List[Dict[str, Any]]:
        """Generate patches based on workload configuration."""
        patches = []
        
        for i in range(config.patch_count):
            patch_type = random.choice(config.operation_types)
            
            if patch_type == "set":
                patches.append(self._generate_set_patch(config, i))
            elif patch_type == "insert":
                patches.append(self._generate_insert_patch(config, i))
            elif patch_type == "merge":
                patches.append(self._generate_merge_patch(config, i))
            elif patch_type == "extend":
                patches.append(self._generate_extend_patch(config, i))
        
        return patches
    
    def _generate_set_patch(self, config: WorkloadConfig, index: int) -> Dict[str, Any]:
        """Generate a 'set' operation patch."""
        complexity = config.xpath_complexity
        
        if complexity <= 2:
            target = f"//p:sp[@id='{index + 2}']//a:t"
        else:
            target = f"//p:sld[{(index % config.slide_count) + 1}]//p:sp[position()={(index % config.element_count_per_slide) + 1}]//a:t"
        
        value = self._generate_value(config.value_size_bytes)
        
        return {
            "operation": "set",
            "target": target,
            "value": value,
            "metadata": {
                "complexity": complexity,
                "index": index
            }
        }
    
    def _generate_insert_patch(self, config: WorkloadConfig, index: int) -> Dict[str, Any]:
        """Generate an 'insert' operation patch."""
        target = f"//p:sld[{(index % config.slide_count) + 1}]//p:spTree"
        
        new_element = {
            "p:sp": {
                "p:nvSpPr": {
                    "p:cNvPr": {"@id": str(1000 + index), "@name": f"NewElement{index}"}
                },
                "p:spPr": {
                    "a:xfrm": {
                        "a:off": {"@x": str(index * 100000), "@y": str(index * 50000)},
                        "a:ext": {"@cx": "1000000", "@cy": "500000"}
                    }
                },
                "p:txBody": {
                    "a:p": {
                        "a:r": {
                            "a:t": f"Inserted Element {index}"
                        }
                    }
                }
            }
        }
        
        return {
            "operation": "insert",
            "target": target,
            "value": new_element,
            "position": "append"
        }
    
    def _generate_merge_patch(self, config: WorkloadConfig, index: int) -> Dict[str, Any]:
        """Generate a 'merge' operation patch."""
        target = f"//p:sp[@id='{(index % 10) + 2}']//p:spPr"
        
        merge_content = {
            "a:solidFill": {
                "a:srgbClr": {
                    "@val": f"{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}"
                }
            }
        }
        
        return {
            "operation": "merge",
            "target": target,
            "value": merge_content,
            "merge_strategy": "deep"
        }
    
    def _generate_extend_patch(self, config: WorkloadConfig, index: int) -> Dict[str, Any]:
        """Generate an 'extend' operation patch."""
        target = f"//p:sld[{(index % config.slide_count) + 1}]//p:spTree"
        
        elements = []
        for i in range(3):  # Add 3 elements
            elements.append({
                "p:sp": {
                    "p:nvSpPr": {
                        "p:cNvPr": {"@id": str(2000 + index * 10 + i), "@name": f"ExtendedElement{index}_{i}"}
                    },
                    "p:spPr": {
                        "a:xfrm": {
                            "a:off": {"@x": str((index * 10 + i) * 100000), "@y": str(i * 50000)},
                            "a:ext": {"@cx": "500000", "@cy": "250000"}
                        }
                    }
                }
            })
        
        return {
            "operation": "extend",
            "target": target,
            "value": elements
        }
    
    def _generate_value(self, size_bytes: int) -> str:
        """Generate a value of specified size."""
        if size_bytes <= 100:
            return f"Benchmark Value {random.randint(1, 1000)}"
        else:
            # Generate larger content
            base_text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
            repeat_count = size_bytes // len(base_text) + 1
            return (base_text * repeat_count)[:size_bytes]


class PerformanceBenchmark:
    """Main benchmark runner for StyleStack performance testing."""
    
    def __init__(self, profiler: Optional[PerformanceProfiler] = None):
        """Initialize the benchmark runner."""
        self.profiler = profiler or PerformanceProfiler()
        self.template_generator = TemplateGenerator()
        self.patch_generator = PatchGenerator()
        self.processor = JSONPatchParser()
        
        # Results storage
        self.results: List[BenchmarkResult] = []
        self.detailed_logs: List[Dict[str, Any]] = []
        
        logger.info("Performance benchmark initialized")
    
    def run_suite(self, suite: BenchmarkSuite) -> Dict[str, Any]:
        """Run a complete benchmark suite."""
        logger.info(f"Starting benchmark suite: {suite.name}")
        
        # Ensure output directory exists
        suite.output_directory.mkdir(parents=True, exist_ok=True)
        
        # Start profiling session
        session_id = f"benchmark_suite_{int(time.time())}"
        if suite.enable_profiling:
            self.profiler.start_session(session_id)
        
        # Start continuous monitoring if enabled
        if suite.enable_monitoring:
            self.profiler.start_continuous_monitoring(interval=0.5)
        
        suite_results = {
            'suite_name': suite.name,
            'description': suite.description,
            'start_time': time.time(),
            'workload_results': [],
            'summary_statistics': {},
            'performance_analysis': {}
        }
        
        try:
            # Run workloads
            if suite.parallel_execution:
                suite_results['workload_results'] = self._run_workloads_parallel(suite.workloads)
            else:
                suite_results['workload_results'] = self._run_workloads_sequential(suite.workloads)
            
            # Calculate summary statistics
            suite_results['summary_statistics'] = self._calculate_summary_stats(suite_results['workload_results'])
            
        except Exception as e:
            logger.error(f"Benchmark suite failed: {e}")
            suite_results['error'] = str(e)
        
        finally:
            suite_results['end_time'] = time.time()
            suite_results['duration'] = suite_results['end_time'] - suite_results['start_time']
            
            # Stop monitoring and profiling
            if suite.enable_monitoring:
                self.profiler.stop_continuous_monitoring()
            
            if suite.enable_profiling:
                profiling_session = self.profiler.end_session(session_id)
                suite_results['performance_analysis'] = self._analyze_profiling_data(profiling_session)
        
        # Save results
        self._save_results(suite_results, suite.output_directory)
        
        logger.info(f"Benchmark suite completed in {suite_results['duration']:.2f} seconds")
        return suite_results
    
    def _run_workloads_sequential(self, workloads: List[WorkloadConfig]) -> List[Dict[str, Any]]:
        """Run workloads sequentially."""
        results = []
        
        for workload in workloads:
            logger.info(f"Running workload: {workload.workload_type.value}")
            result = self._run_single_workload(workload)
            results.append(result)
        
        return results
    
    def _run_workloads_parallel(self, workloads: List[WorkloadConfig]) -> List[Dict[str, Any]]:
        """Run workloads in parallel."""
        results = []
        
        with ThreadPoolExecutor(max_workers=min(4, len(workloads))) as executor:
            future_to_workload = {
                executor.submit(self._run_single_workload, workload): workload
                for workload in workloads
            }
            
            for future in concurrent.futures.as_completed(future_to_workload):
                workload = future_to_workload[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Workload {workload.workload_type.value} failed: {e}")
                    results.append({
                        'workload_type': workload.workload_type.value,
                        'success': False,
                        'error': str(e)
                    })
        
        return results
    
    def _run_single_workload(self, config: WorkloadConfig) -> Dict[str, Any]:
        """Run a single workload configuration."""
        workload_results = []
        
        # Create temporary directory for this workload
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            try:
                # Generate templates and patches once
                templates = []
                patches_list = []
                
                for template_idx in range(config.template_count):
                    template_path = self.template_generator.generate_pptx_template(config, temp_path)
                    templates.append(template_path)
                    
                    patches = self.patch_generator.generate_patches(config)
                    patches_list.append(patches)
                
                # Run warmup iterations
                for _ in range(config.warmup_iterations):
                    self._execute_single_iteration(templates[0], patches_list[0], config)
                
                # Run actual benchmark iterations
                for iteration in range(config.iterations):
                    template_idx = iteration % len(templates)
                    patches_idx = iteration % len(patches_list)
                    
                    result = self._execute_single_iteration(
                        templates[template_idx], 
                        patches_list[patches_idx], 
                        config,
                        iteration_number=iteration
                    )
                    workload_results.append(result)
                
                # Calculate workload statistics
                successful_results = [r for r in workload_results if r.success]
                
                if successful_results:
                    return {
                        'workload_type': config.workload_type.value,
                        'config': {
                            'iterations': config.iterations,
                            'template_count': config.template_count,
                            'patch_count': config.patch_count,
                            'concurrent_workers': config.concurrent_workers,
                            'complexity_level': config.complexity_level
                        },
                        'success': True,
                        'iterations_completed': len(successful_results),
                        'statistics': {
                            'execution_time': {
                                'mean': statistics.mean([r.execution_time for r in successful_results]),
                                'median': statistics.median([r.execution_time for r in successful_results]),
                                'std_dev': statistics.stdev([r.execution_time for r in successful_results]) if len(successful_results) > 1 else 0,
                                'min': min([r.execution_time for r in successful_results]),
                                'max': max([r.execution_time for r in successful_results])
                            },
                            'memory_usage_mb': {
                                'mean': statistics.mean([r.memory_peak_mb for r in successful_results]),
                                'median': statistics.median([r.memory_peak_mb for r in successful_results]),
                                'std_dev': statistics.stdev([r.memory_peak_mb for r in successful_results]) if len(successful_results) > 1 else 0,
                                'min': min([r.memory_peak_mb for r in successful_results]),
                                'max': max([r.memory_peak_mb for r in successful_results])
                            },
                            'throughput_ops_per_sec': {
                                'mean': statistics.mean([r.throughput_ops_per_sec for r in successful_results]),
                                'median': statistics.median([r.throughput_ops_per_sec for r in successful_results]),
                                'std_dev': statistics.stdev([r.throughput_ops_per_sec for r in successful_results]) if len(successful_results) > 1 else 0,
                                'min': min([r.throughput_ops_per_sec for r in successful_results]),
                                'max': max([r.throughput_ops_per_sec for r in successful_results])
                            }
                        },
                        'error_count': sum(1 for r in workload_results if not r.success),
                        'raw_results': [r._asdict() for r in workload_results]
                    }
                else:
                    return {
                        'workload_type': config.workload_type.value,
                        'success': False,
                        'error': 'All iterations failed',
                        'failed_iterations': len(workload_results)
                    }
                
            except Exception as e:
                logger.error(f"Workload {config.workload_type.value} failed: {e}")
                return {
                    'workload_type': config.workload_type.value,
                    'success': False,
                    'error': str(e)
                }
    
    def _execute_single_iteration(self, template_path: Path, patches: List[Dict[str, Any]], 
                                 config: WorkloadConfig, iteration_number: int = 0) -> BenchmarkResult:
        """Execute a single benchmark iteration."""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        error_count = 0
        success = True
        metadata = {
            'iteration': iteration_number,
            'template_path': str(template_path),
            'patch_count': len(patches)
        }
        
        try:
            # Load and process template
            with zipfile.ZipFile(template_path, 'r') as zf:
                # Process each file that needs patching
                for file_name in ['ppt/presentation.xml', 'ppt/slides/slide1.xml']:
                    try:
                        if file_name in zf.namelist():
                            xml_content = zf.read(file_name)
                            xml_doc = etree.fromstring(xml_content)
                            
                            # Apply patches
                            for patch in patches:
                                try:
                                    result = self.processor.apply_patch(xml_doc, patch)
                                    if not result.success:
                                        error_count += 1
                                except Exception as e:
                                    logger.debug(f"Patch failed: {e}")
                                    error_count += 1
                    except Exception as e:
                        logger.debug(f"File processing failed for {file_name}: {e}")
                        error_count += 1
                        
        except Exception as e:
            logger.error(f"Template processing failed: {e}")
            success = False
            error_count += 1
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        execution_time = end_time - start_time
        memory_peak_mb = max(start_memory, end_memory)
        throughput = len(patches) / execution_time if execution_time > 0 else 0
        
        return BenchmarkResult(
            workload_type=config.workload_type,
            execution_time=execution_time,
            memory_peak_mb=memory_peak_mb,
            cpu_usage_percent=0.0,  # Would need separate monitoring for accurate CPU usage
            throughput_ops_per_sec=throughput,
            error_count=error_count,
            success=success and error_count == 0,
            metadata=metadata
        )
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            return psutil.Process().memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0
    
    def _calculate_summary_stats(self, workload_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics across all workloads."""
        successful_workloads = [w for w in workload_results if w.get('success', False)]
        
        if not successful_workloads:
            return {'error': 'No successful workloads'}
        
        # Collect execution times across all workloads
        all_execution_times = []
        all_memory_usage = []
        all_throughput = []
        
        for workload in successful_workloads:
            stats = workload.get('statistics', {})
            if 'execution_time' in stats:
                # Use mean values from each workload
                all_execution_times.append(stats['execution_time']['mean'])
            if 'memory_usage_mb' in stats:
                all_memory_usage.append(stats['memory_usage_mb']['mean'])
            if 'throughput_ops_per_sec' in stats:
                all_throughput.append(stats['throughput_ops_per_sec']['mean'])
        
        summary = {
            'total_workloads': len(workload_results),
            'successful_workloads': len(successful_workloads),
            'failed_workloads': len(workload_results) - len(successful_workloads)
        }
        
        if all_execution_times:
            summary['overall_execution_time'] = {
                'mean': statistics.mean(all_execution_times),
                'median': statistics.median(all_execution_times),
                'min': min(all_execution_times),
                'max': max(all_execution_times)
            }
        
        if all_memory_usage:
            summary['overall_memory_usage'] = {
                'mean': statistics.mean(all_memory_usage),
                'median': statistics.median(all_memory_usage),
                'min': min(all_memory_usage),
                'max': max(all_memory_usage)
            }
        
        if all_throughput:
            summary['overall_throughput'] = {
                'mean': statistics.mean(all_throughput),
                'median': statistics.median(all_throughput),
                'min': min(all_throughput),
                'max': max(all_throughput)
            }
        
        return summary
    
    def _analyze_profiling_data(self, session) -> Dict[str, Any]:
        """Analyze profiling data for performance insights."""
        # Generate bottleneck report
        bottleneck_report = self.profiler.generate_bottleneck_report(session.session_id)
        
        # Add custom analysis
        analysis = {
            'bottleneck_report': bottleneck_report,
            'session_summary': {
                'duration': session.duration,
                'peak_memory_mb': session.peak_memory_mb,
                'average_cpu_percent': session.average_cpu_percent,
                'functions_profiled': len(session.function_profiles)
            }
        }
        
        return analysis
    
    def _save_results(self, results: Dict[str, Any], output_dir: Path) -> None:
        """Save benchmark results to files."""
        timestamp = int(time.time())
        
        # Save main results
        results_file = output_dir / f"benchmark_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save summary report
        summary_file = output_dir / f"benchmark_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            self._write_summary_report(f, results)
        
        logger.info(f"Results saved to {results_file}")
        logger.info(f"Summary saved to {summary_file}")
    
    def _write_summary_report(self, file, results: Dict[str, Any]) -> None:
        """Write a human-readable summary report."""
        file.write(f"StyleStack Performance Benchmark Report\n")
        file.write(f"=" * 50 + "\n\n")
        
        file.write(f"Suite: {results['suite_name']}\n")
        file.write(f"Description: {results['description']}\n")
        file.write(f"Duration: {results['duration']:.2f} seconds\n")
        file.write(f"Completed: {datetime.fromtimestamp(results['end_time'])}\n\n")
        
        # Summary statistics
        if 'summary_statistics' in results:
            stats = results['summary_statistics']
            file.write("Overall Performance Summary:\n")
            file.write("-" * 30 + "\n")
            file.write(f"Total Workloads: {stats.get('total_workloads', 0)}\n")
            file.write(f"Successful: {stats.get('successful_workloads', 0)}\n")
            file.write(f"Failed: {stats.get('failed_workloads', 0)}\n\n")
            
            if 'overall_execution_time' in stats:
                exec_stats = stats['overall_execution_time']
                file.write(f"Execution Time - Mean: {exec_stats['mean']:.3f}s, "
                          f"Min: {exec_stats['min']:.3f}s, Max: {exec_stats['max']:.3f}s\n")
            
            if 'overall_memory_usage' in stats:
                mem_stats = stats['overall_memory_usage']
                file.write(f"Memory Usage - Mean: {mem_stats['mean']:.1f}MB, "
                          f"Min: {mem_stats['min']:.1f}MB, Max: {mem_stats['max']:.1f}MB\n")
            
            if 'overall_throughput' in stats:
                thr_stats = stats['overall_throughput']
                file.write(f"Throughput - Mean: {thr_stats['mean']:.1f} ops/sec, "
                          f"Min: {thr_stats['min']:.1f}, Max: {thr_stats['max']:.1f}\n")
        
        # Individual workload results
        file.write("\n\nIndividual Workload Results:\n")
        file.write("-" * 40 + "\n")
        
        for workload in results.get('workload_results', []):
            if workload.get('success'):
                file.write(f"\nWorkload: {workload['workload_type']}\n")
                file.write(f"Iterations: {workload['iterations_completed']}\n")
                
                stats = workload.get('statistics', {})
                if 'execution_time' in stats:
                    exec_time = stats['execution_time']
                    file.write(f"  Execution Time: {exec_time['mean']:.3f}s ± {exec_time['std_dev']:.3f}s\n")
                
                if 'memory_usage_mb' in stats:
                    memory = stats['memory_usage_mb']
                    file.write(f"  Memory Usage: {memory['mean']:.1f}MB ± {memory['std_dev']:.1f}MB\n")
                
                if 'throughput_ops_per_sec' in stats:
                    throughput = stats['throughput_ops_per_sec']
                    file.write(f"  Throughput: {throughput['mean']:.1f} ops/sec\n")
                
                if workload.get('error_count', 0) > 0:
                    file.write(f"  Errors: {workload['error_count']}\n")
            else:
                file.write(f"\nWorkload: {workload['workload_type']} - FAILED\n")
                file.write(f"  Error: {workload.get('error', 'Unknown')}\n")


def main():
    """Main function for standalone benchmark execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='StyleStack Performance Benchmarks')
    parser.add_argument('--suite', choices=['standard', 'quick'], default='quick',
                       help='Benchmark suite to run')
    parser.add_argument('--output', type=Path, default=Path('benchmark_results'),
                       help='Output directory for results')
    parser.add_argument('--parallel', action='store_true',
                       help='Run workloads in parallel')
    parser.add_argument('--no-profiling', action='store_true',
                       help='Disable detailed profiling')
    parser.add_argument('--no-monitoring', action='store_true',
                       help='Disable continuous monitoring')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create benchmark suite
    if args.suite == 'standard':
        suite = BenchmarkSuite.create_standard_suite()
    else:
        suite = BenchmarkSuite.create_quick_suite()
    
    # Override configuration with command line arguments
    suite.output_directory = args.output
    suite.parallel_execution = args.parallel
    suite.enable_profiling = not args.no_profiling
    suite.enable_monitoring = not args.no_monitoring
    
    # Run benchmarks
    benchmark = PerformanceBenchmark()
    results = benchmark.run_suite(suite)
    
    # Print summary
    print("\nBenchmark Suite Completed!")
    print(f"Duration: {results['duration']:.2f} seconds")
    
    if 'summary_statistics' in results:
        stats = results['summary_statistics']
        print(f"Workloads: {stats.get('successful_workloads', 0)}/{stats.get('total_workloads', 0)} successful")
        
        if 'overall_execution_time' in stats:
            exec_stats = stats['overall_execution_time']
            print(f"Average execution time: {exec_stats['mean']:.3f} seconds")
        
        if 'overall_throughput' in stats:
            thr_stats = stats['overall_throughput']
            print(f"Average throughput: {thr_stats['mean']:.1f} operations/second")
    
    print(f"\nDetailed results saved to: {suite.output_directory}")


if __name__ == "__main__":
    main()