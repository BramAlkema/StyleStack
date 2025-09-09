#!/usr/bin/env python3
"""
StyleStack OOXML Extension Variable System - Template Analyzer (Compatibility Module)

This module maintains backward compatibility after splitting the monolithic
template_analyzer.py into focused analyzer modules.

New code should import from the specific modules:
- tools.analyzer.types for data types and enums
- tools.analyzer.discovery for element discovery
- tools.analyzer.coverage for coverage analysis  
- tools.analyzer.complexity for complexity analysis
"""

import json
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set, Union
import hashlib
import time
from collections import defaultdict

try:
    import lxml.etree as lxml_ET
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False

import sys
import os
sys.path.append(os.path.dirname(__file__))

from ooxml_processor import OOXMLProcessor
from theme_resolver import ThemeResolver

# Import from split modules
from tools.analyzer.types import (
    DesignElementType, AnalysisLevel, PriorityLevel,
    DesignElement, VariableCoverage, ComplexityScore,
    AnalysisResult, CoverageReport, AnalysisConfig, AnalysisContext
)
from tools.analyzer.discovery import ElementDiscoveryEngine
from tools.analyzer.coverage import CoverageAnalyzer
from tools.analyzer.complexity import ComplexityAnalyzer

# Backward compatibility aliases
TemplateComplexity = ComplexityScore


class TemplateAnalyzer:
    """
    Comprehensive template analyzer for OOXML templates - Main Interface.
    
    Coordinates the discovery, coverage, and complexity analysis components
    to provide complete template analysis capabilities.
    """
    
    def __init__(self,
                 analysis_level: AnalysisLevel = AnalysisLevel.STANDARD,
                 target_coverage: float = 100.0,
                 enable_complexity_scoring: bool = True,
                 enable_validation: bool = True):
        """
        Initialize the template analyzer.
        
        Args:
            analysis_level: Depth of analysis to perform
            target_coverage: Target variable coverage percentage
            enable_complexity_scoring: Enable template complexity analysis
            enable_validation: Enable compliance validation
        """
        self.analysis_level = analysis_level
        self.target_coverage = target_coverage
        self.enable_complexity_scoring = enable_complexity_scoring
        self.enable_validation = enable_validation
        
        # Initialize component processors
        self.ooxml_processor = OOXMLProcessor()
        self.theme_resolver = ThemeResolver()
        
        # Configuration
        self.config = AnalysisConfig(
            analysis_level=analysis_level,
            target_coverage=target_coverage,
            enable_complexity_scoring=enable_complexity_scoring,
            enable_validation=enable_validation
        )
        
        # Statistics tracking
        self.statistics = {
            'templates_analyzed': 0,
            'elements_discovered': 0,
            'variables_recommended': 0,
            'coverage_reports_generated': 0
        }
    
    def analyze_complete_template(self, template_path: str) -> AnalysisResult:
        """
        Analyze a complete OOXML template file (.potx, .dotx, .xltx).
        
        Args:
            template_path: Path to the template file
            
        Returns:
            Complete analysis results
        """
        start_time = time.time()
        template_name = Path(template_path).stem
        template_type = Path(template_path).suffix.lower()
        
        try:
            # Create analysis context
            context = AnalysisContext(
                template_path=template_path,
                template_type=template_type
            )
            
            # Extract and analyze template files
            files_analyzed, design_elements = self._extract_and_analyze_files(template_path, context)
            
            # Perform coverage analysis
            coverage_analysis = None
            if design_elements:
                coverage_analyzer = CoverageAnalyzer(context, self.target_coverage)
                coverage_analysis = coverage_analyzer.analyze_coverage(design_elements)
            
            # Perform complexity analysis
            complexity_analysis = None
            if self.enable_complexity_scoring and design_elements:
                complexity_analyzer = ComplexityAnalyzer(context)
                complexity_analysis = complexity_analyzer.analyze_complexity(design_elements)
            
            # Perform validation if enabled
            validation_results = {}
            if self.enable_validation:
                validation_results = self._perform_validation(template_path, design_elements)
            
            # Update statistics
            self.statistics['templates_analyzed'] += 1
            self.statistics['elements_discovered'] += len(design_elements)
            
            processing_time = time.time() - start_time
            
            return AnalysisResult(
                success=True,
                template_name=template_name,
                template_type=template_type,
                files_analyzed=files_analyzed,
                design_elements=design_elements,
                total_elements=len(design_elements),
                customizable_elements=len([e for e in design_elements if e.is_customizable]),
                processing_time=processing_time,
                coverage_analysis=coverage_analysis,
                complexity_analysis=complexity_analysis,
                validation_results=validation_results,
                metadata={
                    'analysis_level': self.analysis_level.value,
                    'lxml_available': LXML_AVAILABLE,
                    'analysis_timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            return AnalysisResult(
                success=False,
                template_name=template_name,
                template_type=template_type,
                files_analyzed=[],
                design_elements=[],
                total_elements=0,
                customizable_elements=0,
                processing_time=processing_time,
                errors=[f"Analysis failed: {str(e)}"],
                metadata={
                    'analysis_level': self.analysis_level.value,
                    'error_type': type(e).__name__
                }
            )
    
    def _extract_and_analyze_files(self, template_path: str, 
                                  context: AnalysisContext) -> Tuple[List[str], List[DesignElement]]:
        """Extract and analyze files from the template."""
        files_analyzed = []
        all_design_elements = []
        
        try:
            with zipfile.ZipFile(template_path, 'r') as zip_file:
                # Get list of XML files to analyze
                xml_files = [f for f in zip_file.namelist() if f.endswith('.xml')]
                context.files_to_analyze = xml_files
                
                # Initialize discovery engine
                discovery_engine = ElementDiscoveryEngine(context)
                
                # Analyze each XML file
                for xml_file in xml_files:
                    try:
                        xml_content = zip_file.read(xml_file).decode('utf-8')
                        context.current_file = xml_file
                        
                        # Discover elements in this file
                        elements = discovery_engine.discover_elements_in_file(xml_file, xml_content)
                        all_design_elements.extend(elements)
                        files_analyzed.append(xml_file)
                        
                    except Exception as e:
                        # Log file processing error but continue
                        context.processing_stats.setdefault('file_errors', []).append(
                            {'file': xml_file, 'error': str(e)}
                        )
                
        except Exception as e:
            context.processing_stats.setdefault('extraction_errors', []).append(str(e))
        
        return files_analyzed, all_design_elements
    
    def _perform_validation(self, template_path: str, 
                           design_elements: List[DesignElement]) -> Dict[str, Any]:
        """Perform validation checks on the template."""
        validation_results = {
            'file_structure_valid': True,
            'xml_well_formed': True,
            'namespace_consistency': True,
            'element_accessibility': True,
            'cross_platform_compatibility': True,
            'issues': []
        }
        
        try:
            # Basic file structure validation
            with zipfile.ZipFile(template_path, 'r') as zip_file:
                required_files = self._get_required_files_for_type(Path(template_path).suffix)
                for required_file in required_files:
                    if not any(f.endswith(required_file) for f in zip_file.namelist()):
                        validation_results['file_structure_valid'] = False
                        validation_results['issues'].append(f"Missing required file: {required_file}")
            
            # Element-based validation
            cross_platform_issues = []
            accessibility_issues = []
            
            for element in design_elements:
                if not element.cross_platform_compatible:
                    cross_platform_issues.append(element.id)
                
                if element.accessibility_impact < 3.0 and element.element_type in [
                    DesignElementType.COLOR, DesignElementType.FONT
                ]:
                    accessibility_issues.append(element.id)
            
            if cross_platform_issues:
                validation_results['cross_platform_compatibility'] = False
                validation_results['issues'].append(
                    f"Cross-platform issues in {len(cross_platform_issues)} elements"
                )
            
            if accessibility_issues:
                validation_results['element_accessibility'] = False
                validation_results['issues'].append(
                    f"Potential accessibility issues in {len(accessibility_issues)} elements"
                )
                
        except Exception as e:
            validation_results['issues'].append(f"Validation error: {str(e)}")
        
        return validation_results
    
    def _get_required_files_for_type(self, template_type: str) -> List[str]:
        """Get required files for a specific template type."""
        required_files = {
            '.potx': ['presentation.xml', 'theme1.xml'],
            '.dotx': ['document.xml', 'styles.xml'],
            '.xltx': ['workbook.xml', 'styles.xml']
        }
        
        return required_files.get(template_type.lower(), [])
    
    def generate_coverage_report(self, analysis_result: AnalysisResult,
                                existing_variables: Optional[Dict[str, Any]] = None) -> Optional[CoverageReport]:
        """Generate a comprehensive coverage report."""
        if not analysis_result.coverage_analysis:
            return None
        
        context = AnalysisContext(
            template_path=analysis_result.template_name,
            template_type=analysis_result.template_type
        )
        
        coverage_analyzer = CoverageAnalyzer(context, self.target_coverage)
        coverage_report = coverage_analyzer.generate_coverage_report(
            analysis_result.coverage_analysis,
            analysis_result.template_name
        )
        
        self.statistics['coverage_reports_generated'] += 1
        return coverage_report
    
    def export_analysis_results(self, analysis_result: AnalysisResult,
                               output_path: str, format: str = 'json') -> bool:
        """Export analysis results to file."""
        try:
            if format.lower() == 'json':
                # Convert to JSON-serializable format
                export_data = {
                    'template_name': analysis_result.template_name,
                    'template_type': analysis_result.template_type,
                    'success': analysis_result.success,
                    'total_elements': analysis_result.total_elements,
                    'customizable_elements': analysis_result.customizable_elements,
                    'processing_time': analysis_result.processing_time,
                    'files_analyzed': analysis_result.files_analyzed,
                    'design_elements': [
                        {
                            'id': elem.id,
                            'type': elem.element_type.value,
                            'semantic_name': elem.semantic_name,
                            'current_value': elem.current_value,
                            'xpath_expression': elem.xpath_expression,
                            'file_location': elem.file_location,
                            'is_customizable': elem.is_customizable,
                            'priority_score': elem.priority_score,
                            'brand_relevance': elem.brand_relevance,
                            'accessibility_impact': elem.accessibility_impact
                        }
                        for elem in analysis_result.design_elements
                    ],
                    'coverage_analysis': self._serialize_coverage_analysis(analysis_result.coverage_analysis),
                    'complexity_analysis': self._serialize_complexity_analysis(analysis_result.complexity_analysis),
                    'validation_results': analysis_result.validation_results,
                    'errors': analysis_result.errors,
                    'warnings': analysis_result.warnings,
                    'metadata': analysis_result.metadata
                }
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                return True
                
        except Exception as e:
            return False
        
        return False
    
    def _serialize_coverage_analysis(self, coverage: Optional[VariableCoverage]) -> Optional[Dict[str, Any]]:
        """Serialize coverage analysis for JSON export."""
        if not coverage:
            return None
        
        return {
            'total_elements': coverage.total_elements,
            'covered_elements': coverage.covered_elements,
            'coverage_percentage': coverage.coverage_percentage,
            'uncovered_count': len(coverage.uncovered_elements),
            'recommendations_count': len(coverage.recommendations),
            'coverage_by_type': {
                k.value if hasattr(k, 'value') else str(k): v 
                for k, v in coverage.coverage_by_type.items()
            },
            'coverage_by_priority': {
                k.value if hasattr(k, 'value') else str(k): v 
                for k, v in coverage.coverage_by_priority.items()
            }
        }
    
    def _serialize_complexity_analysis(self, complexity: Optional[ComplexityScore]) -> Optional[Dict[str, Any]]:
        """Serialize complexity analysis for JSON export."""
        if not complexity:
            return None
        
        return {
            'complexity_score': complexity.complexity_score,
            'category': complexity.category,
            'total_elements': complexity.total_elements,
            'customizable_elements': complexity.customizable_elements,
            'element_diversity': complexity.element_diversity,
            'factors': complexity.factors,
            'metadata': complexity.metadata
        }
    
    def get_analysis_statistics(self) -> Dict[str, int]:
        """Get analysis statistics."""
        return dict(self.statistics)


# Backward compatibility exports
__all__ = [
    # Main class
    'TemplateAnalyzer',
    
    # Types from analyzer modules
    'DesignElementType',
    'AnalysisLevel', 
    'PriorityLevel',
    'DesignElement',
    'VariableCoverage',
    'ComplexityScore',
    'TemplateComplexity',  # Backward compatibility alias
    'AnalysisResult',
    'CoverageReport',
    'AnalysisConfig',
    'AnalysisContext',
    
    # Analyzer components
    'ElementDiscoveryEngine',
    'CoverageAnalyzer',
    'ComplexityAnalyzer'
]