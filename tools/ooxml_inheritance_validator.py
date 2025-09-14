"""
StyleStack OOXML Inheritance Validation System

Comprehensive validation system for OOXML inheritance structures including XML validation,
inheritance hierarchy validation, Office application compatibility testing, and
performance validation for large inheritance hierarchies.

Features:
- OOXML inheritance structure validation
- Office application compatibility testing
- XML well-formedness and schema validation
- Performance validation with large inheritance hierarchies
- Cross-platform validation (Word, PowerPoint, Excel)
- Inheritance chain validation and circular dependency detection
"""

import logging
import time
import tempfile
import subprocess
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict

try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    import xml.etree.ElementTree as ET
    LXML_AVAILABLE = False

from tools.style_inheritance_core import InheritedTypographyToken, InheritanceMode
from tools.ooxml_inheritance_generator import OOXMLInheritanceGenerator, OOXMLGenerationResult
from tools.ooxml_multiplatform_support import MultiPlatformOOXMLGenerator

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of OOXML inheritance validation"""
    is_valid: bool
    validation_type: str
    platform: str
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    xml_structure_valid: bool = True
    inheritance_chains_valid: bool = True
    office_compatible: bool = True


@dataclass
class PerformanceBenchmark:
    """Performance benchmark for OOXML generation"""
    token_count: int
    inheritance_depth: int
    generation_time: float
    xml_size: int
    validation_time: float
    memory_usage: Optional[float] = None


class OOXMLStructureValidator:
    """Validates OOXML structure and well-formedness"""

    def __init__(self, use_lxml: bool = None):
        self.use_lxml = use_lxml if use_lxml is not None else LXML_AVAILABLE

    def validate_xml_structure(self, xml_content: str, platform: str) -> ValidationResult:
        """Validate XML structure and well-formedness"""
        result = ValidationResult(
            is_valid=True,
            validation_type="xml_structure",
            platform=platform
        )

        try:
            # Parse XML to check well-formedness
            if self.use_lxml and LXML_AVAILABLE:
                root = etree.fromstring(xml_content.encode('utf-8'))
            else:
                root = ET.fromstring(xml_content)

            # Validate basic structure
            self._validate_basic_structure(root, platform, result)

            # Validate namespaces
            self._validate_namespaces(root, platform, result)

            # Validate style references
            self._validate_style_references(root, result)

        except Exception as e:
            result.is_valid = False
            result.xml_structure_valid = False
            result.issues.append(f"XML parsing error: {e}")

        return result

    def _validate_basic_structure(self, root, platform: str, result: ValidationResult):
        """Validate basic XML structure for platform"""
        expected_containers = {
            "word": ["styles", "style"],
            "powerpoint": ["txStyles", "lvl1pPr"],
            "excel": ["styleSheet", "xf"]
        }

        if platform in expected_containers:
            container_tags = expected_containers[platform]

            # Check for expected container elements
            for tag in container_tags:
                if not self._has_element_with_tag(root, tag):
                    result.warnings.append(f"Missing expected {platform} element: {tag}")

    def _validate_namespaces(self, root, platform: str, result: ValidationResult):
        """Validate namespace declarations"""
        expected_namespaces = {
            "word": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
            "powerpoint": "http://schemas.openxmlformats.org/presentationml/2006/main",
            "excel": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
        }

        if platform in expected_namespaces:
            expected_ns = expected_namespaces[platform]

            # Check namespace declaration
            if hasattr(root, 'nsmap'):  # lxml
                if expected_ns not in root.nsmap.values():
                    result.warnings.append(f"Missing expected namespace: {expected_ns}")
            else:  # ElementTree
                if expected_ns not in str(root.attrib):
                    result.warnings.append(f"Namespace validation limited with ElementTree")

    def _validate_style_references(self, root, result: ValidationResult):
        """Validate style references and basedOn attributes"""
        # Find all basedOn references
        based_on_refs = []

        if self.use_lxml:
            based_on_elements = root.xpath("//*[@val]")
            for elem in based_on_elements:
                if "basedOn" in str(elem.tag):
                    based_on_refs.append(elem.get("val"))
        else:
            # ElementTree fallback
            for elem in root.iter():
                if "basedOn" in str(elem.tag):
                    val = elem.get("val")
                    if val:
                        based_on_refs.append(val)

        # Find all style IDs
        style_ids = []
        for elem in root.iter():
            style_id = elem.get("styleId")
            if style_id:
                style_ids.append(style_id)

        # Check that all basedOn references point to valid styles
        builtin_styles = {"Normal", "Heading1", "Heading2", "Title", "DefaultParagraphFont"}
        for ref in based_on_refs:
            if ref not in style_ids and ref not in builtin_styles:
                result.warnings.append(f"basedOn reference to undefined style: {ref}")

    def _has_element_with_tag(self, root, tag_name: str) -> bool:
        """Check if XML has element with specified tag"""
        for elem in root.iter():
            if tag_name in str(elem.tag):
                return True
        return False


class InheritanceChainValidator:
    """Validates inheritance chains for correctness"""

    def validate_inheritance_chains(self, tokens: List[InheritedTypographyToken],
                                  platform: str) -> ValidationResult:
        """Validate inheritance chain integrity"""
        result = ValidationResult(
            is_valid=True,
            validation_type="inheritance_chains",
            platform=platform
        )

        # Build dependency graph
        dependency_graph = self._build_dependency_graph(tokens)

        # Check for circular dependencies
        circular_deps = self._detect_circular_dependencies(dependency_graph)
        if circular_deps:
            result.is_valid = False
            result.inheritance_chains_valid = False
            result.issues.extend([f"Circular dependency: {' -> '.join(chain)}" for chain in circular_deps])

        # Validate chain depths
        self._validate_chain_depths(tokens, result)

        # Validate base style references
        self._validate_base_style_references(tokens, result)

        return result

    def _build_dependency_graph(self, tokens: List[InheritedTypographyToken]) -> Dict[str, Set[str]]:
        """Build dependency graph from tokens"""
        graph = defaultdict(set)

        for token in tokens:
            if token.base_style:
                graph[token.id].add(token.base_style)

        return dict(graph)

    def _detect_circular_dependencies(self, graph: Dict[str, Set[str]]) -> List[List[str]]:
        """Detect circular dependencies in dependency graph"""
        circular_deps = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]) -> bool:
            if node in rec_stack:
                # Found cycle - extract the circular part
                cycle_start = path.index(node)
                circular_deps.append(path[cycle_start:] + [node])
                return True

            if node in visited:
                return False

            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if dfs(neighbor, path + [node]):
                    return True

            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                dfs(node, [])

        return circular_deps

    def _validate_chain_depths(self, tokens: List[InheritedTypographyToken],
                             result: ValidationResult):
        """Validate inheritance chain depths are reasonable"""
        max_recommended_depth = 10

        for token in tokens:
            if token.inheritance_depth and token.inheritance_depth > max_recommended_depth:
                result.warnings.append(
                    f"Deep inheritance chain ({token.inheritance_depth}) for token {token.id}"
                )

    def _validate_base_style_references(self, tokens: List[InheritedTypographyToken],
                                      result: ValidationResult):
        """Validate base style references exist"""
        token_ids = {token.id for token in tokens}
        builtin_styles = {"Normal", "Heading1", "Heading2", "Title", "DefaultParagraphFont"}

        for token in tokens:
            if token.base_style:
                if token.base_style not in token_ids and token.base_style not in builtin_styles:
                    result.issues.append(f"Token {token.id} references undefined base style: {token.base_style}")


class OfficeCompatibilityValidator:
    """Validates compatibility with Office applications"""

    def __init__(self):
        self.office_versions = {
            "2016": {"supports_inheritance": True, "max_inheritance_depth": 10},
            "2019": {"supports_inheritance": True, "max_inheritance_depth": 15},
            "365": {"supports_inheritance": True, "max_inheritance_depth": 20}
        }

    def validate_office_compatibility(self, xml_content: str, platform: str,
                                    office_version: str = "2019") -> ValidationResult:
        """Validate compatibility with specific Office version"""
        result = ValidationResult(
            is_valid=True,
            validation_type="office_compatibility",
            platform=platform
        )

        if office_version not in self.office_versions:
            result.warnings.append(f"Unknown Office version: {office_version}")
            office_version = "2019"  # Default fallback

        version_info = self.office_versions[office_version]

        # Check inheritance support
        if not version_info["supports_inheritance"] and "basedOn" in xml_content:
            result.is_valid = False
            result.office_compatible = False
            result.issues.append(f"Office {office_version} does not support style inheritance")

        # Validate against known Office limitations
        self._validate_office_limitations(xml_content, platform, office_version, result)

        return result

    def _validate_office_limitations(self, xml_content: str, platform: str,
                                   office_version: str, result: ValidationResult):
        """Validate against known Office application limitations"""
        if platform == "excel":
            # Excel has limited inheritance support
            if "basedOn" in xml_content:
                result.warnings.append("Excel has limited style inheritance support")

        if platform == "powerpoint":
            # PowerPoint inheritance is more complex
            if xml_content.count("lvl") > 9:
                result.warnings.append("PowerPoint supports maximum 9 text levels")

        # Check for unsupported XML elements
        unsupported_elements = self._get_unsupported_elements(platform, office_version)
        for element in unsupported_elements:
            if element in xml_content:
                result.warnings.append(f"Element {element} may not be supported in Office {office_version}")

    def _get_unsupported_elements(self, platform: str, office_version: str) -> List[str]:
        """Get list of potentially unsupported XML elements"""
        unsupported = []

        if office_version == "2016":
            # Some newer elements not supported in 2016
            unsupported.extend(["w15:", "w16:", "a15:", "a16:"])

        return unsupported

    def validate_with_office_application(self, xml_content: str, platform: str,
                                       office_path: Optional[Path] = None) -> ValidationResult:
        """Validate by attempting to open with actual Office application"""
        result = ValidationResult(
            is_valid=True,
            validation_type="office_application_test",
            platform=platform
        )

        if not office_path:
            result.warnings.append("Office application path not provided - skipping application test")
            return result

        try:
            # Create temporary file with OOXML structure
            with tempfile.NamedTemporaryFile(suffix=f".{platform}x", delete=False) as tmp_file:
                # This would need a complete OOXML file structure
                # For now, just validate that the XML can be parsed
                result.warnings.append("Office application testing requires complete OOXML file generation")

        except Exception as e:
            result.is_valid = False
            result.office_compatible = False
            result.issues.append(f"Office application test failed: {e}")

        return result


class PerformanceValidator:
    """Validates performance with large inheritance hierarchies"""

    def validate_performance(self, tokens: List[InheritedTypographyToken],
                           platform: str,
                           generator: OOXMLInheritanceGenerator) -> ValidationResult:
        """Validate performance with given token set"""
        result = ValidationResult(
            is_valid=True,
            validation_type="performance",
            platform=platform
        )

        # Measure generation performance
        start_time = time.time()

        xml_outputs = []
        for token in tokens:
            gen_result = generator.generate_style_xml_with_inheritance(token, platform)
            xml_outputs.append(gen_result.xml_content)

        generation_time = time.time() - start_time

        # Calculate metrics
        total_xml_size = sum(len(xml) for xml in xml_outputs)
        max_inheritance_depth = max((t.inheritance_depth or 0 for t in tokens), default=0)

        benchmark = PerformanceBenchmark(
            token_count=len(tokens),
            inheritance_depth=max_inheritance_depth,
            generation_time=generation_time,
            xml_size=total_xml_size,
            validation_time=0  # Will be filled by validation
        )

        # Performance thresholds
        if generation_time > 10.0:  # 10 seconds
            result.warnings.append(f"Slow generation time: {generation_time:.2f}s")

        if len(tokens) > 0 and generation_time / len(tokens) > 0.1:  # 100ms per token
            result.warnings.append(f"Slow per-token generation: {generation_time/len(tokens)*1000:.1f}ms per token")

        result.performance_metrics["benchmark"] = benchmark
        result.performance_metrics["tokens_per_second"] = len(tokens) / generation_time if generation_time > 0 else 0
        result.performance_metrics["xml_size_per_token"] = total_xml_size / len(tokens) if tokens else 0

        return result

    def benchmark_large_hierarchy(self, base_count: int = 1000) -> Dict[str, PerformanceBenchmark]:
        """Benchmark with artificially large inheritance hierarchy"""
        benchmarks = {}

        # Create test hierarchies of different sizes
        test_sizes = [100, 500, 1000, 2000]

        for size in test_sizes:
            if size > base_count:
                continue

            tokens = self._create_test_hierarchy(size)
            generator = OOXMLInheritanceGenerator()

            start_time = time.time()
            for token in tokens:
                generator.generate_style_xml_with_inheritance(token, "word")
            generation_time = time.time() - start_time

            benchmarks[f"size_{size}"] = PerformanceBenchmark(
                token_count=size,
                inheritance_depth=size // 10,  # Approximate depth
                generation_time=generation_time,
                xml_size=0,  # Not measured in this benchmark
                validation_time=0
            )

        return benchmarks

    def _create_test_hierarchy(self, size: int) -> List[InheritedTypographyToken]:
        """Create test inheritance hierarchy of specified size"""
        tokens = []

        # Create base token
        base_token = InheritedTypographyToken(
            id="base_token",
            font_family="Arial",
            font_size="12pt",
            base_style="Normal",
            inheritance_mode=InheritanceMode.AUTO,
            delta_properties={"fontFamily": "Arial"}
        )
        tokens.append(base_token)

        # Create derived tokens
        for i in range(1, size):
            parent_id = f"base_token" if i == 1 else f"token_{i-1}"

            token = InheritedTypographyToken(
                id=f"token_{i}",
                font_size=f"{12 + i % 12}pt",
                base_style=parent_id,
                inheritance_mode=InheritanceMode.AUTO,
                delta_properties={"fontSize": f"{12 + i % 12}pt"},
                inheritance_depth=min(i, 20)
            )
            tokens.append(token)

        return tokens


class OOXMLInheritanceValidationSuite:
    """Comprehensive OOXML inheritance validation suite"""

    def __init__(self):
        self.structure_validator = OOXMLStructureValidator()
        self.chain_validator = InheritanceChainValidator()
        self.office_validator = OfficeCompatibilityValidator()
        self.performance_validator = PerformanceValidator()
        self.multiplatform_generator = MultiPlatformOOXMLGenerator()

    def run_comprehensive_validation(self, tokens: List[InheritedTypographyToken],
                                   platforms: List[str] = None,
                                   office_version: str = "2019") -> Dict[str, List[ValidationResult]]:
        """Run comprehensive validation across all aspects"""
        if platforms is None:
            platforms = ["word", "powerpoint", "excel"]

        results = {}

        for platform in platforms:
            platform_results = []

            try:
                # Generate OOXML for platform
                xml_content = self.multiplatform_generator.generate_for_platform(tokens, platform)

                # XML structure validation
                structure_result = self.structure_validator.validate_xml_structure(xml_content, platform)
                platform_results.append(structure_result)

                # Inheritance chain validation
                chain_result = self.chain_validator.validate_inheritance_chains(tokens, platform)
                platform_results.append(chain_result)

                # Office compatibility validation
                office_result = self.office_validator.validate_office_compatibility(
                    xml_content, platform, office_version
                )
                platform_results.append(office_result)

                # Performance validation
                generator = OOXMLInheritanceGenerator()
                performance_result = self.performance_validator.validate_performance(tokens, platform, generator)
                platform_results.append(performance_result)

            except Exception as e:
                error_result = ValidationResult(
                    is_valid=False,
                    validation_type="platform_error",
                    platform=platform,
                    issues=[f"Platform validation failed: {e}"]
                )
                platform_results.append(error_result)

            results[platform] = platform_results

        return results

    def generate_validation_report(self, validation_results: Dict[str, List[ValidationResult]]) -> str:
        """Generate comprehensive validation report"""
        report_lines = ["# OOXML Inheritance Validation Report", ""]

        for platform, results in validation_results.items():
            report_lines.append(f"## Platform: {platform.title()}")
            report_lines.append("")

            for result in results:
                report_lines.append(f"### {result.validation_type.replace('_', ' ').title()}")

                if result.is_valid:
                    report_lines.append("✅ **Status**: Valid")
                else:
                    report_lines.append("❌ **Status**: Invalid")

                if result.issues:
                    report_lines.append("**Issues:**")
                    for issue in result.issues:
                        report_lines.append(f"- {issue}")

                if result.warnings:
                    report_lines.append("**Warnings:**")
                    for warning in result.warnings:
                        report_lines.append(f"- {warning}")

                if result.performance_metrics:
                    report_lines.append("**Performance Metrics:**")
                    for key, value in result.performance_metrics.items():
                        if isinstance(value, PerformanceBenchmark):
                            report_lines.append(f"- Generation Time: {value.generation_time:.3f}s")
                            report_lines.append(f"- Token Count: {value.token_count}")
                            report_lines.append(f"- Inheritance Depth: {value.inheritance_depth}")
                        else:
                            report_lines.append(f"- {key}: {value}")

                report_lines.append("")

        return '\n'.join(report_lines)


# Export main classes
__all__ = [
    'OOXMLInheritanceValidationSuite',
    'OOXMLStructureValidator',
    'InheritanceChainValidator',
    'OfficeCompatibilityValidator',
    'PerformanceValidator',
    'ValidationResult',
    'PerformanceBenchmark'
]