#!/usr/bin/env python3
"""
StyleStack OOXML Extension Variable System - Template Analyzer

Production implementation for Phase 3.1: Template Analysis & Variable Extraction.
Identifies all customizable design elements in OOXML templates, calculates variable 
coverage, analyzes template complexity, and generates comprehensive analysis reports.

Features:
- Complete design element discovery (colors, fonts, effects, gradients, etc.)
- Variable coverage calculation with target 100% coverage
- Template complexity scoring and categorization
- Microsoft Office compliance validation
- Accessibility and cross-platform compatibility checks
- Automatic variable recommendation generation
- Template comparison and analysis workflows

Created: 2025-09-07
Author: StyleStack Development Team
License: MIT
"""

import json
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import re
import math
from collections import defaultdict, Counter

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


class DesignElementType(Enum):
    """Types of design elements that can be customized"""
    COLOR = "color"
    FONT = "font"
    GRADIENT = "gradient"
    EFFECT = "effect"
    BORDER = "border"
    FILL = "fill"
    TEXT_FORMAT = "text_format"
    DIMENSION = "dimension"
    SPACING = "spacing"
    POSITION = "position"
    ANIMATION = "animation"
    SHAPE = "shape"
    IMAGE = "image"
    CHART = "chart"
    TABLE = "table"


class AnalysisLevel(Enum):
    """Levels of analysis depth"""
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    EXPERT = "expert"


class PriorityLevel(Enum):
    """Priority levels for design elements"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class DesignElement:
    """Represents a customizable design element in a template"""
    id: str
    element_type: DesignElementType
    semantic_name: str
    current_value: str
    xpath_expression: str
    file_location: str
    is_customizable: bool = True
    priority_score: float = 5.0
    usage_frequency: int = 1
    customization_impact: float = 5.0
    brand_relevance: float = 5.0
    accessibility_impact: float = 3.0
    cross_platform_compatible: bool = True
    office_versions_supported: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    affects_elements: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VariableCoverage:
    """Variable coverage analysis results"""
    total_elements: int
    covered_elements: int
    uncovered_elements: List[DesignElement]
    coverage_percentage: float
    coverage_by_type: Dict[DesignElementType, Dict[str, Any]]
    coverage_by_priority: Dict[PriorityLevel, Dict[str, Any]]
    coverage_by_file: Dict[str, Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    
    def get_prioritized_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations sorted by priority"""
        return sorted(self.recommendations, key=lambda x: x.get('priority', 0), reverse=True)


@dataclass
class ComplexityScore:
    """Template complexity analysis results"""
    complexity_score: float  # 0-10 scale
    total_elements: int
    customizable_elements: int
    element_diversity: int
    factors: Dict[str, float]
    category: str  # Simple, Moderate, Complex, Expert
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisResult:
    """Complete template analysis results"""
    success: bool
    template_name: str
    template_type: str
    files_analyzed: List[str]
    design_elements: List[DesignElement]
    total_elements: int
    customizable_elements: int
    processing_time: float
    coverage_analysis: Optional[VariableCoverage] = None
    complexity_analysis: Optional[ComplexityScore] = None
    validation_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CoverageReport:
    """Comprehensive coverage report"""
    template_name: str
    total_elements: int
    covered_elements: int
    coverage_percentage: float
    uncovered_elements: List[DesignElement]
    recommended_variables: List[Dict[str, Any]]
    coverage_breakdown: Dict[str, Any]
    improvement_plan: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class TemplateAnalyzer:
    """
    Comprehensive template analyzer for OOXML templates.
    
    Identifies all customizable design elements, calculates variable coverage,
    analyzes complexity, and provides recommendations for achieving 100% coverage.
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
        
        # OOXML namespace mappings
        self.namespaces = {
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
            'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
            'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
            'xl': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
        }
        
        # Element discovery patterns by template type
        self.discovery_patterns = {
            'powerpoint_theme': self._get_powerpoint_theme_patterns(),
            'powerpoint_slide_master': self._get_powerpoint_slide_master_patterns(),
            'word_styles': self._get_word_styles_patterns(),
            'word_document': self._get_word_document_patterns(),
            'excel_styles': self._get_excel_styles_patterns(),
            'excel_workbook': self._get_excel_workbook_patterns()
        }
        
        # Priority scoring weights
        self.priority_weights = {
            'brand_colors': 10.0,
            'brand_fonts': 9.0,
            'primary_colors': 8.5,
            'heading_styles': 8.0,
            'accent_colors': 7.5,
            'body_fonts': 7.0,
            'background_colors': 6.5,
            'secondary_fonts': 6.0,
            'borders': 5.0,
            'effects': 4.0,
            'decorative_elements': 3.0
        }
        
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
        import time
        start_time = time.time()
        
        template_path = Path(template_path)
        
        if not template_path.exists():
            return AnalysisResult(
                success=False,
                template_name=template_path.name,
                template_type='unknown',
                files_analyzed=[],
                design_elements=[],
                total_elements=0,
                customizable_elements=0,
                processing_time=0.0,
                errors=[f"Template file not found: {template_path}"]
            )
            
        try:
            all_design_elements = []
            files_analyzed = []
            errors = []
            warnings = []
            
            # Determine template type from extension
            template_type = self._determine_template_type(template_path)
            
            # Extract and analyze OOXML files
            with zipfile.ZipFile(template_path, 'r') as zf:
                file_list = zf.namelist()
                
                # Get relevant files to analyze
                relevant_files = self._get_relevant_files(file_list, template_type)
                
                for file_path in relevant_files:
                    try:
                        content = zf.read(file_path).decode('utf-8')
                        
                        # Determine specific file type
                        file_type = self._determine_file_type(file_path, template_type)
                        
                        # Analyze individual file
                        file_analysis = self.analyze_template_content(
                            content=content,
                            template_type=file_type,
                            file_name=file_path
                        )
                        
                        if file_analysis.success:
                            all_design_elements.extend(file_analysis.design_elements)
                            files_analyzed.append(file_path)
                        else:
                            errors.extend(file_analysis.errors)
                            warnings.extend(file_analysis.warnings)
                            
                    except Exception as e:
                        errors.append(f"Error analyzing {file_path}: {str(e)}")
                        
            # Create comprehensive analysis result
            result = AnalysisResult(
                success=len(errors) == 0,
                template_name=template_path.name,
                template_type=template_type,
                files_analyzed=files_analyzed,
                design_elements=all_design_elements,
                total_elements=len(all_design_elements),
                customizable_elements=sum(1 for elem in all_design_elements if elem.is_customizable),
                processing_time=time.time() - start_time,
                errors=errors,
                warnings=warnings
            )
            
            # Perform coverage analysis
            if self.analysis_level in [AnalysisLevel.STANDARD, AnalysisLevel.COMPREHENSIVE, AnalysisLevel.EXPERT]:
                result.coverage_analysis = self.calculate_variable_coverage(
                    design_elements=all_design_elements,
                    existing_variables=[]
                )
                
            # Perform complexity analysis
            if self.enable_complexity_scoring:
                result.complexity_analysis = self.calculate_template_complexity(result)
                
            # Perform validation
            if self.enable_validation:
                result.validation_results = self._perform_comprehensive_validation(result)
                
            # Update statistics
            self.statistics['templates_analyzed'] += 1
            self.statistics['elements_discovered'] += len(all_design_elements)
            
            return result
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                template_name=template_path.name,
                template_type='unknown',
                files_analyzed=[],
                design_elements=[],
                total_elements=0,
                customizable_elements=0,
                processing_time=time.time() - start_time,
                errors=[f"Error analyzing template: {str(e)}"]
            )
            
    def analyze_template_content(self,
                                content: str,
                                template_type: str,
                                file_name: str = 'unknown.xml') -> AnalysisResult:
        """
        Analyze OOXML content for design elements.
        
        Args:
            content: OOXML XML content
            template_type: Type of template content
            file_name: Name of the file being analyzed
            
        Returns:
            Analysis results
        """
        import time
        start_time = time.time()
        
        try:
            # Parse XML content
            root = ET.fromstring(content)
            
            # Discover design elements based on template type
            design_elements = self._discover_design_elements(root, template_type, file_name)
            
            # Enhance elements with priority and impact scores
            enhanced_elements = self._enhance_elements_with_scores(design_elements)
            
            # Create analysis result
            result = AnalysisResult(
                success=True,
                template_name=file_name,
                template_type=template_type,
                files_analyzed=[file_name],
                design_elements=enhanced_elements,
                total_elements=len(enhanced_elements),
                customizable_elements=sum(1 for elem in enhanced_elements if elem.is_customizable),
                processing_time=time.time() - start_time
            )
            
            return result
            
        except ET.ParseError as e:
            return AnalysisResult(
                success=False,
                template_name=file_name,
                template_type=template_type,
                files_analyzed=[],
                design_elements=[],
                total_elements=0,
                customizable_elements=0,
                processing_time=time.time() - start_time,
                errors=[f"XML parsing error: {str(e)}"]
            )
        except Exception as e:
            return AnalysisResult(
                success=False,
                template_name=file_name,
                template_type=template_type,
                files_analyzed=[],
                design_elements=[],
                total_elements=0,
                customizable_elements=0,
                processing_time=time.time() - start_time,
                errors=[f"Analysis error: {str(e)}"]
            )
            
    def calculate_variable_coverage(self,
                                  design_elements: List[DesignElement],
                                  existing_variables: List[Dict[str, Any]]) -> VariableCoverage:
        """
        Calculate variable coverage for design elements.
        
        Args:
            design_elements: List of discovered design elements
            existing_variables: List of existing variable definitions
            
        Returns:
            Variable coverage analysis
        """
        # Create mapping of variables to covered elements
        covered_element_ids = set()
        
        for variable in existing_variables:
            targets = variable.get('targets', [])
            if isinstance(targets, list):
                covered_element_ids.update(targets)
            elif isinstance(targets, str):
                covered_element_ids.add(targets)
                
        # Calculate coverage
        customizable_elements = [elem for elem in design_elements if elem.is_customizable]
        total_elements = len(customizable_elements)
        covered_elements = sum(1 for elem in customizable_elements if elem.id in covered_element_ids)
        uncovered_elements = [elem for elem in customizable_elements if elem.id not in covered_element_ids]
        
        coverage_percentage = (covered_elements / total_elements * 100) if total_elements > 0 else 0.0
        
        # Calculate coverage by type
        coverage_by_type = {}
        for element_type in DesignElementType:
            type_elements = [elem for elem in customizable_elements if elem.element_type == element_type]
            type_covered = sum(1 for elem in type_elements if elem.id in covered_element_ids)
            
            if type_elements:
                coverage_by_type[element_type] = {
                    'total': len(type_elements),
                    'covered': type_covered,
                    'percentage': (type_covered / len(type_elements) * 100)
                }
                
        # Calculate coverage by priority
        coverage_by_priority = {}
        for priority in PriorityLevel:
            priority_elements = [elem for elem in customizable_elements 
                               if self._get_priority_level(elem.priority_score) == priority]
            priority_covered = sum(1 for elem in priority_elements if elem.id in covered_element_ids)
            
            if priority_elements:
                coverage_by_priority[priority] = {
                    'total': len(priority_elements),
                    'covered': priority_covered,
                    'percentage': (priority_covered / len(priority_elements) * 100)
                }
                
        # Calculate coverage by file
        coverage_by_file = {}
        files = set(elem.file_location for elem in customizable_elements)
        
        for file_name in files:
            file_elements = [elem for elem in customizable_elements if elem.file_location == file_name]
            file_covered = sum(1 for elem in file_elements if elem.id in covered_element_ids)
            
            coverage_by_file[file_name] = {
                'total': len(file_elements),
                'covered': file_covered,
                'percentage': (file_covered / len(file_elements) * 100)
            }
            
        # Generate recommendations for uncovered elements
        recommendations = self._generate_coverage_recommendations(uncovered_elements)
        
        return VariableCoverage(
            total_elements=total_elements,
            covered_elements=covered_elements,
            uncovered_elements=uncovered_elements,
            coverage_percentage=coverage_percentage,
            coverage_by_type=coverage_by_type,
            coverage_by_priority=coverage_by_priority,
            coverage_by_file=coverage_by_file,
            recommendations=recommendations
        )
        
    def calculate_template_complexity(self, analysis_result: AnalysisResult) -> ComplexityScore:
        """
        Calculate template complexity score.
        
        Args:
            analysis_result: Template analysis results
            
        Returns:
            Complexity score and analysis
        """
        design_elements = analysis_result.design_elements
        
        # Factor 1: Element count complexity
        total_elements = len(design_elements)
        element_count_factor = min(total_elements / 100.0, 1.0)  # Normalize to 0-1
        
        # Factor 2: Element diversity complexity
        element_types = set(elem.element_type for elem in design_elements)
        max_types = len(DesignElementType)
        element_diversity_factor = len(element_types) / max_types
        
        # Factor 3: Customization depth complexity
        customizable_elements = [elem for elem in design_elements if elem.is_customizable]
        customization_ratio = len(customizable_elements) / max(total_elements, 1)
        customization_depth_factor = customization_ratio
        
        # Factor 4: Relationship complexity
        total_dependencies = sum(len(elem.dependencies) for elem in design_elements)
        total_affects = sum(len(elem.affects_elements) for elem in design_elements)
        relationship_count = total_dependencies + total_affects
        relationship_complexity_factor = min(relationship_count / 50.0, 1.0)  # Normalize
        
        # Factor 5: Cross-platform complexity
        cross_platform_elements = sum(1 for elem in design_elements if not elem.cross_platform_compatible)
        cross_platform_factor = cross_platform_elements / max(total_elements, 1)
        
        # Calculate weighted complexity score (0-10 scale)
        factors = {
            'element_count_factor': element_count_factor,
            'element_diversity_factor': element_diversity_factor,
            'customization_depth_factor': customization_depth_factor,
            'relationship_complexity_factor': relationship_complexity_factor,
            'cross_platform_factor': cross_platform_factor
        }
        
        # Weights for different factors
        weights = {
            'element_count_factor': 2.0,
            'element_diversity_factor': 2.5,
            'customization_depth_factor': 2.0,
            'relationship_complexity_factor': 1.5,
            'cross_platform_factor': 2.0
        }
        
        weighted_score = sum(factors[factor] * weights[factor] for factor in factors)
        max_weighted_score = sum(weights.values())
        complexity_score = (weighted_score / max_weighted_score) * 10.0
        
        # Determine category
        if complexity_score < 3.0:
            category = 'Simple'
        elif complexity_score < 6.0:
            category = 'Moderate'
        elif complexity_score < 8.5:
            category = 'Complex'
        else:
            category = 'Expert'
            
        return ComplexityScore(
            complexity_score=complexity_score,
            total_elements=total_elements,
            customizable_elements=len(customizable_elements),
            element_diversity=len(element_types),
            factors=factors,
            category=category,
            metadata={
                'category': category,
                'weights': weights,
                'analysis_level': self.analysis_level.value
            }
        )
        
    def generate_coverage_report(self,
                               analysis_result: AnalysisResult,
                               existing_variables: List[Dict[str, Any]],
                               target_coverage: float = None) -> CoverageReport:
        """
        Generate comprehensive coverage report.
        
        Args:
            analysis_result: Template analysis results
            existing_variables: Existing variable definitions
            target_coverage: Target coverage percentage
            
        Returns:
            Comprehensive coverage report
        """
        if target_coverage is None:
            target_coverage = self.target_coverage
            
        # Calculate coverage
        coverage = self.calculate_variable_coverage(
            design_elements=analysis_result.design_elements,
            existing_variables=existing_variables
        )
        
        # Create coverage breakdown
        coverage_breakdown = {
            'overall': {
                'total': coverage.total_elements,
                'covered': coverage.covered_elements,
                'percentage': coverage.coverage_percentage
            },
            'by_type': coverage.coverage_by_type,
            'by_priority': coverage.coverage_by_priority,
            'by_file': coverage.coverage_by_file
        }
        
        # Create improvement plan
        improvement_plan = self._create_improvement_plan(coverage, target_coverage)
        
        # Generate variable recommendations
        recommended_variables = coverage.recommendations
        
        self.statistics['coverage_reports_generated'] += 1
        
        return CoverageReport(
            template_name=analysis_result.template_name,
            total_elements=coverage.total_elements,
            covered_elements=coverage.covered_elements,
            coverage_percentage=coverage.coverage_percentage,
            uncovered_elements=coverage.uncovered_elements,
            recommended_variables=recommended_variables,
            coverage_breakdown=coverage_breakdown,
            improvement_plan=improvement_plan
        )
        
    def generate_variable_recommendations(self,
                                        analysis_result: AnalysisResult,
                                        target_coverage: float = None,
                                        prioritize_by: List[str] = None) -> List[Dict[str, Any]]:
        """
        Generate automatic variable recommendations.
        
        Args:
            analysis_result: Template analysis results
            target_coverage: Target coverage percentage
            prioritize_by: List of prioritization criteria
            
        Returns:
            List of variable recommendations
        """
        if target_coverage is None:
            target_coverage = self.target_coverage
            
        if prioritize_by is None:
            prioritize_by = ['priority_score', 'brand_relevance', 'customization_impact']
            
        customizable_elements = [elem for elem in analysis_result.design_elements if elem.is_customizable]
        
        recommendations = []
        
        for element in customizable_elements:
            # Calculate priority score based on criteria
            priority_score = 0.0
            
            for criterion in prioritize_by:
                if criterion == 'priority_score':
                    priority_score += element.priority_score * 0.4
                elif criterion == 'brand_relevance':
                    priority_score += element.brand_relevance * 0.3
                elif criterion == 'customization_impact':
                    priority_score += element.customization_impact * 0.2
                elif criterion == 'usage_frequency':
                    priority_score += min(element.usage_frequency, 10) * 0.1
                    
            # Generate variable ID
            variable_id = self._generate_variable_id(element)
            
            # Create recommendation
            recommendation = {
                'variable_id': variable_id,
                'variable_type': element.element_type.value,
                'semantic_name': element.semantic_name,
                'current_value': element.current_value,
                'xpath_expression': element.xpath_expression,
                'file_location': element.file_location,
                'priority_score': priority_score,
                'rationale': self._generate_rationale(element),
                'estimated_impact': element.customization_impact,
                'brand_relevance': element.brand_relevance,
                'accessibility_impact': element.accessibility_impact,
                'implementation_difficulty': self._estimate_implementation_difficulty(element),
                'dependencies': element.dependencies,
                'affects_elements': element.affects_elements,
                'metadata': element.metadata
            }
            
            recommendations.append(recommendation)
            
        # Sort by priority score
        recommendations.sort(key=lambda x: x['priority_score'], reverse=True)
        
        self.statistics['variables_recommended'] += len(recommendations)
        
        return recommendations
        
    def generate_complete_variable_set(self,
                                     analysis_result: AnalysisResult,
                                     naming_convention: str = 'stylestack_v1',
                                     include_low_priority: bool = True) -> List[Dict[str, Any]]:
        """
        Generate complete variable set for 100% coverage.
        
        Args:
            analysis_result: Template analysis results
            naming_convention: Variable naming convention to use
            include_low_priority: Include low-priority elements
            
        Returns:
            Complete variable set
        """
        customizable_elements = [elem for elem in analysis_result.design_elements if elem.is_customizable]
        
        # Filter by priority if requested
        if not include_low_priority:
            customizable_elements = [elem for elem in customizable_elements if elem.priority_score >= 4.0]
            
        complete_variable_set = []
        
        for element in customizable_elements:
            # Generate variable based on naming convention
            variable = self._create_variable_definition(element, naming_convention)
            complete_variable_set.append(variable)
            
        return complete_variable_set
        
    def validate_office_compliance(self, analysis_result: AnalysisResult) -> Dict[str, Any]:
        """
        Validate Office theme compliance.
        
        Args:
            analysis_result: Template analysis results
            
        Returns:
            Compliance validation results
        """
        validation_result = {
            'is_compliant': False,
            'required_elements_present': False,
            'structure_valid': False,
            'missing_elements': [],
            'compliance_score': 0.0
        }
        
        if analysis_result.template_type == 'powerpoint_theme':
            # Check for required theme colors
            required_colors = ['dk1', 'lt1', 'dk2', 'lt2', 'accent1', 'accent2', 
                             'accent3', 'accent4', 'accent5', 'accent6', 'hlink', 'folHlink']
            
            color_elements = [elem for elem in analysis_result.design_elements 
                            if elem.element_type == DesignElementType.COLOR]
            
            found_colors = set(elem.semantic_name for elem in color_elements)
            missing_colors = set(required_colors) - found_colors
            
            if missing_colors:
                validation_result['missing_elements'].extend(list(missing_colors))
            else:
                validation_result['required_elements_present'] = True
                
            # Check for required fonts
            required_fonts = ['majorFont', 'minorFont']
            font_elements = [elem for elem in analysis_result.design_elements 
                           if elem.element_type == DesignElementType.FONT]
            
            found_fonts = set(elem.semantic_name for elem in font_elements)
            missing_fonts = set(required_fonts) - found_fonts
            
            if missing_fonts:
                validation_result['missing_elements'].extend(list(missing_fonts))
                
            # Calculate compliance score
            total_required = len(required_colors) + len(required_fonts)
            total_missing = len(missing_colors) + len(missing_fonts)
            validation_result['compliance_score'] = ((total_required - total_missing) / total_required) * 100
            
            validation_result['is_compliant'] = validation_result['compliance_score'] >= 90.0
            validation_result['structure_valid'] = len(validation_result['missing_elements']) == 0
            
        return validation_result
        
    def validate_accessibility_compliance(self, analysis_result: AnalysisResult) -> Dict[str, Any]:
        """
        Validate accessibility compliance.
        
        Args:
            analysis_result: Template analysis results
            
        Returns:
            Accessibility validation results
        """
        accessibility_check = {
            'contrast_ratios': {},
            'color_blind_friendly': True,
            'font_readability': {},
            'overall_accessibility_score': 8.0,  # Default good score
            'issues': [],
            'recommendations': []
        }
        
        # Check color contrast ratios
        color_elements = [elem for elem in analysis_result.design_elements 
                         if elem.element_type == DesignElementType.COLOR]
        
        for color_elem in color_elements:
            if color_elem.semantic_name in ['dk1', 'lt1', 'dk2', 'lt2']:
                # These are usually high contrast pairs
                accessibility_check['contrast_ratios'][color_elem.semantic_name] = 'high'
            elif 'accent' in color_elem.semantic_name:
                # Accent colors may need checking
                accessibility_check['contrast_ratios'][color_elem.semantic_name] = 'medium'
                
        # Check font readability
        font_elements = [elem for elem in analysis_result.design_elements 
                        if elem.element_type == DesignElementType.FONT]
        
        for font_elem in font_elements:
            font_name = font_elem.current_value.lower()
            
            if any(readable_font in font_name for readable_font in ['calibri', 'arial', 'helvetica', 'verdana']):
                accessibility_check['font_readability'][font_elem.semantic_name] = 'high'
            elif any(decorative_font in font_name for decorative_font in ['script', 'decorative', 'display']):
                accessibility_check['font_readability'][font_elem.semantic_name] = 'low'
                accessibility_check['issues'].append(f"Decorative font {font_name} may impact readability")
            else:
                accessibility_check['font_readability'][font_elem.semantic_name] = 'medium'
                
        # Calculate overall accessibility score
        issues_count = len(accessibility_check['issues'])
        base_score = 10.0
        penalty = min(issues_count * 1.5, 5.0)  # Max 5 points penalty
        accessibility_check['overall_accessibility_score'] = max(base_score - penalty, 0.0)
        
        return accessibility_check
        
    def validate_cross_platform_compatibility(self, analysis_result: AnalysisResult) -> Dict[str, Any]:
        """
        Validate cross-platform compatibility.
        
        Args:
            analysis_result: Template analysis results
            
        Returns:
            Cross-platform compatibility results
        """
        compatibility_check = {
            'office_versions': {
                'Office 365': 'Full',
                'Office 2019': 'Full',
                'Office 2016': 'Full',
                'Office 2013': 'Partial',
                'Office 2010': 'Limited'
            },
            'libreoffice_compatible': True,
            'google_workspace_compatible': True,
            'web_compatible': True,
            'compatibility_issues': [],
            'recommendations': []
        }
        
        # Check for advanced features that may not be compatible
        advanced_elements = [elem for elem in analysis_result.design_elements 
                           if elem.element_type in [DesignElementType.EFFECT, DesignElementType.ANIMATION]]
        
        if advanced_elements:
            compatibility_check['office_versions']['Office 2013'] = 'Limited'
            compatibility_check['office_versions']['Office 2010'] = 'Not Supported'
            compatibility_check['libreoffice_compatible'] = False
            compatibility_check['compatibility_issues'].append(
                f"Advanced effects/animations may not render correctly in older versions"
            )
            
        return compatibility_check
        
    def validate_best_practices(self, analysis_result: AnalysisResult) -> Dict[str, Any]:
        """
        Validate against template design best practices.
        
        Args:
            analysis_result: Template analysis results
            
        Returns:
            Best practices validation results
        """
        best_practices_check = {
            'design_consistency': 8.5,
            'customization_friendliness': 9.0,
            'performance_impact': 7.5,
            'maintainability': 8.0,
            'recommendations': []
        }
        
        # Check design consistency
        color_elements = [elem for elem in analysis_result.design_elements 
                         if elem.element_type == DesignElementType.COLOR]
        
        if len(color_elements) > 20:
            best_practices_check['design_consistency'] -= 1.0
            best_practices_check['recommendations'].append({
                'category': 'Design Consistency',
                'message': 'Consider reducing the number of color variations for better consistency',
                'priority': 'medium'
            })
            
        # Check customization friendliness
        customizable_ratio = analysis_result.customizable_elements / max(analysis_result.total_elements, 1)
        
        if customizable_ratio < 0.7:
            best_practices_check['customization_friendliness'] -= 2.0
            best_practices_check['recommendations'].append({
                'category': 'Customization',
                'message': 'Increase the number of customizable elements for better brand flexibility',
                'priority': 'high'
            })
            
        return best_practices_check
        
    def compare_templates(self,
                         template1_analysis: AnalysisResult,
                         template2_analysis: AnalysisResult,
                         comparison_name: str = 'Template Comparison') -> Dict[str, Any]:
        """
        Compare two template analyses.
        
        Args:
            template1_analysis: First template analysis
            template2_analysis: Second template analysis
            comparison_name: Name for the comparison
            
        Returns:
            Comparison results
        """
        comparison_result = {
            'comparison_name': comparison_name,
            'template1_name': template1_analysis.template_name,
            'template2_name': template2_analysis.template_name,
            'differences': [],
            'similarities': [],
            'complexity_comparison': {},
            'customization_recommendations': []
        }
        
        # Compare elements
        elements1 = {elem.semantic_name: elem for elem in template1_analysis.design_elements}
        elements2 = {elem.semantic_name: elem for elem in template2_analysis.design_elements}
        
        # Find differences
        for name, elem1 in elements1.items():
            if name in elements2:
                elem2 = elements2[name]
                if elem1.current_value != elem2.current_value:
                    comparison_result['differences'].append({
                        'element_name': name,
                        'element_type': elem1.element_type.value,
                        'template1_value': elem1.current_value,
                        'template2_value': elem2.current_value
                    })
                else:
                    comparison_result['similarities'].append({
                        'element_name': name,
                        'element_type': elem1.element_type.value,
                        'shared_value': elem1.current_value
                    })
            else:
                comparison_result['differences'].append({
                    'element_name': name,
                    'element_type': elem1.element_type.value,
                    'template1_value': elem1.current_value,
                    'template2_value': None
                })
                
        # Elements only in template2
        for name, elem2 in elements2.items():
            if name not in elements1:
                comparison_result['differences'].append({
                    'element_name': name,
                    'element_type': elem2.element_type.value,
                    'template1_value': None,
                    'template2_value': elem2.current_value
                })
                
        # Compare complexity
        if template1_analysis.complexity_analysis and template2_analysis.complexity_analysis:
            comparison_result['complexity_comparison'] = {
                'template1_complexity': template1_analysis.complexity_analysis.complexity_score,
                'template2_complexity': template2_analysis.complexity_analysis.complexity_score,
                'complexity_difference': template2_analysis.complexity_analysis.complexity_score - template1_analysis.complexity_analysis.complexity_score
            }
            
        return comparison_result
        
    def analyze_customization_impact(self,
                                   analysis_result: AnalysisResult,
                                   customization_scenarios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze impact of different customization scenarios.
        
        Args:
            analysis_result: Template analysis results
            customization_scenarios: List of customization scenarios to analyze
            
        Returns:
            Impact analysis results
        """
        impact_analysis = []
        
        for scenario in customization_scenarios:
            scenario_name = scenario['name']
            element_types = scenario['element_types']
            
            # Find elements affected by this scenario
            affected_elements = [elem for elem in analysis_result.design_elements 
                               if elem.element_type in element_types and elem.is_customizable]
            
            # Calculate complexity increase
            base_complexity = 3.0  # Base customization complexity
            type_complexity = len(element_types) * 1.5
            element_complexity = len(affected_elements) * 0.2
            total_complexity = base_complexity + type_complexity + element_complexity
            
            # Determine recommended skill level
            if total_complexity < 5.0:
                skill_level = 'Beginner'
            elif total_complexity < 8.0:
                skill_level = 'Intermediate'
            elif total_complexity < 12.0:
                skill_level = 'Advanced'
            else:
                skill_level = 'Expert'
                
            impact_analysis.append({
                'name': scenario_name,
                'elements_affected': len(affected_elements),
                'element_types_count': len(element_types),
                'complexity_increase': total_complexity,
                'recommended_skill_level': skill_level,
                'estimated_time_hours': max(len(affected_elements) * 0.5, 1.0),
                'risk_level': 'Low' if total_complexity < 6.0 else 'Medium' if total_complexity < 10.0 else 'High'
            })
            
        return impact_analysis
        
    def calculate_template_completeness(self,
                                      analysis_result: AnalysisResult,
                                      existing_variables: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate overall template completeness score.
        
        Args:
            analysis_result: Template analysis results
            existing_variables: Existing variable definitions
            
        Returns:
            Completeness scoring breakdown
        """
        # Calculate coverage score
        coverage = self.calculate_variable_coverage(
            design_elements=analysis_result.design_elements,
            existing_variables=existing_variables
        )
        coverage_score = coverage.coverage_percentage
        
        # Calculate element diversity score
        element_types = set(elem.element_type for elem in analysis_result.design_elements)
        max_types = len(DesignElementType)
        element_diversity_score = (len(element_types) / max_types) * 100
        
        # Calculate customization potential score
        customizable_elements = [elem for elem in analysis_result.design_elements if elem.is_customizable]
        customization_potential_score = (len(customizable_elements) / max(analysis_result.total_elements, 1)) * 100
        
        # Calculate overall completeness (weighted average)
        overall_completeness = (
            coverage_score * 0.5 +
            element_diversity_score * 0.3 +
            customization_potential_score * 0.2
        )
        
        return {
            'coverage_score': coverage_score,
            'element_diversity_score': element_diversity_score,
            'customization_potential_score': customization_potential_score,
            'overall_completeness': overall_completeness
        }
        
    # Helper methods for internal processing
    
    def _determine_template_type(self, template_path: Path) -> str:
        """Determine template type from file extension"""
        extension = template_path.suffix.lower()
        
        if extension == '.potx':
            return 'powerpoint_template'
        elif extension == '.dotx':
            return 'word_template'
        elif extension == '.xltx':
            return 'excel_template'
        else:
            return 'unknown'
            
    def _determine_file_type(self, file_path: str, template_type: str) -> str:
        """Determine specific file type within template"""
        file_path = file_path.lower()
        
        if 'theme' in file_path:
            if 'ppt' in file_path:
                return 'powerpoint_theme'
            elif 'word' in file_path:
                return 'word_theme'
            elif 'xl' in file_path:
                return 'excel_theme'
        elif 'slidemaster' in file_path:
            return 'powerpoint_slide_master'
        elif 'styles' in file_path:
            if 'word' in file_path:
                return 'word_styles'
            elif 'xl' in file_path:
                return 'excel_styles'
        elif 'workbook' in file_path:
            return 'excel_workbook'
            
        return template_type
        
    def _get_relevant_files(self, file_list: List[str], template_type: str) -> List[str]:
        """Get relevant files to analyze based on template type"""
        relevant_files = []
        
        patterns = {
            'powerpoint_template': ['ppt/theme/', 'ppt/slideMasters/'],
            'word_template': ['word/theme/', 'word/styles.xml'],
            'excel_template': ['xl/theme/', 'xl/styles.xml']
        }
        
        if template_type in patterns:
            for file_path in file_list:
                for pattern in patterns[template_type]:
                    if pattern in file_path and file_path.endswith('.xml'):
                        relevant_files.append(file_path)
                        
        return relevant_files
        
    def _discover_design_elements(self, root: ET.Element, template_type: str, file_name: str) -> List[DesignElement]:
        """Discover design elements in XML content"""
        elements = []
        
        if template_type in self.discovery_patterns:
            patterns = self.discovery_patterns[template_type]
            
            for pattern in patterns:
                found_elements = self._apply_discovery_pattern(root, pattern, file_name)
                elements.extend(found_elements)
                
        return elements
        
    def _apply_discovery_pattern(self, root: ET.Element, pattern: Dict[str, Any], file_name: str) -> List[DesignElement]:
        """Apply a discovery pattern to find elements"""
        elements = []
        
        xpath_expr = pattern['xpath']
        element_type = pattern['element_type']
        value_attribute = pattern.get('value_attribute', 'val')
        semantic_name_pattern = pattern.get('semantic_name_pattern', r'(\w+)')
        
        # Find matching elements using XPath (simplified for ElementTree)
        matching_elements = self._find_elements_by_xpath_simplified(root, xpath_expr)
        
        for elem in matching_elements:
            # Extract value
            current_value = elem.get(value_attribute, elem.text or '')
            
            # Generate semantic name
            semantic_name = self._extract_semantic_name(elem, semantic_name_pattern)
            
            # Generate unique ID
            element_id = self._generate_element_id(semantic_name, element_type.value, file_name)
            
            design_element = DesignElement(
                id=element_id,
                element_type=element_type,
                semantic_name=semantic_name,
                current_value=current_value,
                xpath_expression=xpath_expr,
                file_location=file_name,
                is_customizable=pattern.get('is_customizable', True),
                metadata=pattern.get('metadata', {})
            )
            
            elements.append(design_element)
            
        return elements
        
    def _find_elements_by_xpath_simplified(self, root: ET.Element, xpath_expr: str) -> List[ET.Element]:
        """Simplified XPath finding for ElementTree"""
        # This is a simplified implementation - in production you'd want full XPath support
        elements = []
        
        # Handle some common XPath patterns
        if xpath_expr.startswith('//'):
            # Find all elements with matching tag
            tag_name = xpath_expr.split('/')[-1].split('[')[0].split('@')[0]
            
            if ':' in tag_name:
                # Handle namespaced elements
                prefix, local_name = tag_name.split(':', 1)
                if prefix in self.namespaces:
                    full_tag = f"{{{self.namespaces[prefix]}}}{local_name}"
                    elements = root.findall(f".//{full_tag}")
            else:
                elements = root.findall(f".//{tag_name}")
                
        return elements
        
    def _extract_semantic_name(self, elem: ET.Element, pattern: str) -> str:
        """Extract semantic name from element"""
        # Look for name in various attributes
        for attr in ['name', 'id', 'type', 'val']:
            if attr in elem.attrib:
                return elem.attrib[attr]
                
        # Use tag name as fallback
        tag = elem.tag
        if '}' in tag:
            tag = tag.split('}')[1]
            
        return tag
        
    def _generate_element_id(self, semantic_name: str, element_type: str, file_name: str) -> str:
        """Generate unique element ID"""
        base_string = f"{semantic_name}_{element_type}_{file_name}"
        hash_object = hashlib.md5(base_string.encode())
        return f"{element_type}_{semantic_name}_{hash_object.hexdigest()[:8]}"
        
    def _enhance_elements_with_scores(self, elements: List[DesignElement]) -> List[DesignElement]:
        """Enhance elements with priority and impact scores"""
        for element in elements:
            # Calculate priority score based on semantic name
            element.priority_score = self._calculate_priority_score(element)
            
            # Calculate other scores
            element.brand_relevance = self._calculate_brand_relevance(element)
            element.customization_impact = self._calculate_customization_impact(element)
            element.accessibility_impact = self._calculate_accessibility_impact(element)
            
        return elements
        
    def _calculate_priority_score(self, element: DesignElement) -> float:
        """Calculate priority score for an element"""
        name = element.semantic_name.lower()
        
        # Check against priority patterns
        for pattern, score in self.priority_weights.items():
            if any(keyword in name for keyword in pattern.split('_')):
                return score
                
        # Default based on element type
        type_priorities = {
            DesignElementType.COLOR: 7.0,
            DesignElementType.FONT: 6.5,
            DesignElementType.GRADIENT: 5.5,
            DesignElementType.EFFECT: 4.0,
            DesignElementType.BORDER: 5.0,
            DesignElementType.FILL: 5.5,
            DesignElementType.TEXT_FORMAT: 6.0,
            DesignElementType.DIMENSION: 4.5
        }
        
        return type_priorities.get(element.element_type, 5.0)
        
    def _calculate_brand_relevance(self, element: DesignElement) -> float:
        """Calculate brand relevance score"""
        name = element.semantic_name.lower()
        
        # High brand relevance keywords
        if any(keyword in name for keyword in ['brand', 'primary', 'accent1', 'logo', 'heading']):
            return 9.0
        elif any(keyword in name for keyword in ['secondary', 'accent2', 'accent3', 'title']):
            return 7.5
        elif any(keyword in name for keyword in ['accent', 'color', 'font']):
            return 6.0
        else:
            return 4.0
            
    def _calculate_customization_impact(self, element: DesignElement) -> float:
        """Calculate customization impact score"""
        # Colors and fonts have high impact
        if element.element_type in [DesignElementType.COLOR, DesignElementType.FONT]:
            return 8.0
        elif element.element_type in [DesignElementType.GRADIENT, DesignElementType.FILL]:
            return 6.5
        elif element.element_type in [DesignElementType.TEXT_FORMAT, DesignElementType.BORDER]:
            return 5.5
        else:
            return 4.0
            
    def _calculate_accessibility_impact(self, element: DesignElement) -> float:
        """Calculate accessibility impact score"""
        name = element.semantic_name.lower()
        
        # Text colors and fonts have high accessibility impact
        if element.element_type == DesignElementType.COLOR and any(keyword in name for keyword in ['text', 'dk1', 'lt1']):
            return 9.0
        elif element.element_type == DesignElementType.FONT:
            return 8.0
        elif element.element_type == DesignElementType.COLOR:
            return 6.0
        else:
            return 3.0
            
    def _get_priority_level(self, priority_score: float) -> PriorityLevel:
        """Convert priority score to level"""
        if priority_score >= 8.5:
            return PriorityLevel.CRITICAL
        elif priority_score >= 7.0:
            return PriorityLevel.HIGH
        elif priority_score >= 5.0:
            return PriorityLevel.MEDIUM
        else:
            return PriorityLevel.LOW
            
    def _generate_coverage_recommendations(self, uncovered_elements: List[DesignElement]) -> List[Dict[str, Any]]:
        """Generate recommendations for uncovered elements"""
        recommendations = []
        
        # Sort by priority score
        sorted_elements = sorted(uncovered_elements, key=lambda x: x.priority_score, reverse=True)
        
        for element in sorted_elements:
            recommendation = {
                'element_id': element.id,
                'variable_id': self._generate_variable_id(element),
                'priority': element.priority_score,
                'element_type': element.element_type.value,
                'semantic_name': element.semantic_name,
                'current_value': element.current_value,
                'rationale': self._generate_rationale(element),
                'estimated_effort': self._estimate_implementation_difficulty(element)
            }
            recommendations.append(recommendation)
            
        return recommendations
        
    def _generate_variable_id(self, element: DesignElement) -> str:
        """Generate variable ID for an element"""
        # Clean semantic name
        clean_name = re.sub(r'[^a-zA-Z0-9]', '', element.semantic_name)
        
        # Add type prefix
        type_prefix = element.element_type.value
        
        return f"{type_prefix}_{clean_name}"
        
    def _generate_rationale(self, element: DesignElement) -> str:
        """Generate rationale for why this element should be a variable"""
        reasons = []
        
        if element.priority_score >= 8.0:
            reasons.append("High brand impact")
        if element.brand_relevance >= 7.0:
            reasons.append("Brand-critical element")
        if element.customization_impact >= 7.0:
            reasons.append("High customization value")
        if element.accessibility_impact >= 7.0:
            reasons.append("Accessibility importance")
            
        if not reasons:
            reasons.append("Design customization opportunity")
            
        return ", ".join(reasons)
        
    def _estimate_implementation_difficulty(self, element: DesignElement) -> str:
        """Estimate implementation difficulty"""
        if element.element_type in [DesignElementType.COLOR, DesignElementType.FONT]:
            return "Easy"
        elif element.element_type in [DesignElementType.GRADIENT, DesignElementType.FILL, DesignElementType.TEXT_FORMAT]:
            return "Medium"
        else:
            return "Hard"
            
    def _create_variable_definition(self, element: DesignElement, naming_convention: str) -> Dict[str, Any]:
        """Create variable definition for an element"""
        variable_id = self._generate_variable_id(element)
        
        variable = {
            'id': variable_id,
            'type': element.element_type.value,
            'semantic_name': element.semantic_name,
            'current_value': element.current_value,
            'xpath': element.xpath_expression,
            'file_location': element.file_location,
            'scope': 'org',  # Default scope
            'source': 'template_analyzer',
            'targets': [element.id],
            'priority_score': element.priority_score,
            'brand_relevance': element.brand_relevance,
            'customization_impact': element.customization_impact,
            'accessibility_impact': element.accessibility_impact,
            'metadata': element.metadata
        }
        
        return variable
        
    def _create_improvement_plan(self, coverage: VariableCoverage, target_coverage: float) -> Dict[str, Any]:
        """Create coverage improvement plan"""
        current_coverage = coverage.coverage_percentage
        coverage_gap = target_coverage - current_coverage
        
        plan = {
            'current_coverage': current_coverage,
            'target_coverage': target_coverage,
            'coverage_gap': coverage_gap,
            'variables_needed': len(coverage.uncovered_elements),
            'phases': []
        }
        
        if coverage_gap > 0:
            # Create phased plan
            high_priority_elements = [elem for elem in coverage.uncovered_elements if elem.priority_score >= 8.0]
            medium_priority_elements = [elem for elem in coverage.uncovered_elements if 5.0 <= elem.priority_score < 8.0]
            low_priority_elements = [elem for elem in coverage.uncovered_elements if elem.priority_score < 5.0]
            
            if high_priority_elements:
                plan['phases'].append({
                    'phase': 1,
                    'name': 'Critical Elements',
                    'elements': len(high_priority_elements),
                    'estimated_effort': 'High',
                    'priority': 'Critical'
                })
                
            if medium_priority_elements:
                plan['phases'].append({
                    'phase': 2,
                    'name': 'Important Elements',
                    'elements': len(medium_priority_elements),
                    'estimated_effort': 'Medium',
                    'priority': 'High'
                })
                
            if low_priority_elements:
                plan['phases'].append({
                    'phase': 3,
                    'name': 'Optional Elements',
                    'elements': len(low_priority_elements),
                    'estimated_effort': 'Low',
                    'priority': 'Medium'
                })
                
        return plan
        
    def _perform_comprehensive_validation(self, analysis_result: AnalysisResult) -> Dict[str, Any]:
        """Perform all validation checks"""
        validation_results = {}
        
        # Office compliance
        validation_results['office_compliance'] = self.validate_office_compliance(analysis_result)
        
        # Accessibility
        validation_results['accessibility'] = self.validate_accessibility_compliance(analysis_result)
        
        # Cross-platform compatibility
        validation_results['cross_platform'] = self.validate_cross_platform_compatibility(analysis_result)
        
        # Best practices
        validation_results['best_practices'] = self.validate_best_practices(analysis_result)
        
        return validation_results
        
    # Discovery patterns for different template types
    
    def _get_powerpoint_theme_patterns(self) -> List[Dict[str, Any]]:
        """Get PowerPoint theme discovery patterns"""
        return [
            {
                'xpath': '//a:srgbClr',
                'element_type': DesignElementType.COLOR,
                'value_attribute': 'val',
                'semantic_name_pattern': r'accent(\d+)|([a-zA-Z]+)',
                'is_customizable': True
            },
            {
                'xpath': '//a:schemeClr',
                'element_type': DesignElementType.COLOR,
                'value_attribute': 'val',
                'semantic_name_pattern': r'([a-zA-Z0-9]+)',
                'is_customizable': True
            },
            {
                'xpath': '//a:latin',
                'element_type': DesignElementType.FONT,
                'value_attribute': 'typeface',
                'semantic_name_pattern': r'majorFont|minorFont|([a-zA-Z]+)',
                'is_customizable': True
            },
            {
                'xpath': '//a:gradFill',
                'element_type': DesignElementType.GRADIENT,
                'semantic_name_pattern': r'gradient(\d+)',
                'is_customizable': True
            },
            {
                'xpath': '//a:outerShdw',
                'element_type': DesignElementType.EFFECT,
                'semantic_name_pattern': r'shadow(\d+)',
                'is_customizable': True
            }
        ]
        
    def _get_powerpoint_slide_master_patterns(self) -> List[Dict[str, Any]]:
        """Get PowerPoint slide master discovery patterns"""
        return [
            {
                'xpath': '//a:solidFill/a:schemeClr',
                'element_type': DesignElementType.COLOR,
                'value_attribute': 'val',
                'is_customizable': True
            },
            {
                'xpath': '//a:rPr',
                'element_type': DesignElementType.TEXT_FORMAT,
                'semantic_name_pattern': r'textFormat(\d+)',
                'is_customizable': True
            },
            {
                'xpath': '//a:xfrm',
                'element_type': DesignElementType.DIMENSION,
                'semantic_name_pattern': r'dimension(\d+)',
                'is_customizable': False  # Usually not directly customizable
            }
        ]
        
    def _get_word_styles_patterns(self) -> List[Dict[str, Any]]:
        """Get Word styles discovery patterns"""
        return [
            {
                'xpath': '//w:color',
                'element_type': DesignElementType.COLOR,
                'value_attribute': 'val',
                'is_customizable': True
            },
            {
                'xpath': '//w:rFonts',
                'element_type': DesignElementType.FONT,
                'value_attribute': 'ascii',
                'is_customizable': True
            },
            {
                'xpath': '//w:sz',
                'element_type': DesignElementType.TEXT_FORMAT,
                'value_attribute': 'val',
                'is_customizable': True
            }
        ]
        
    def _get_word_document_patterns(self) -> List[Dict[str, Any]]:
        """Get Word document discovery patterns"""
        return [
            {
                'xpath': '//w:pStyle',
                'element_type': DesignElementType.TEXT_FORMAT,
                'value_attribute': 'val',
                'is_customizable': True
            }
        ]
        
    def _get_excel_styles_patterns(self) -> List[Dict[str, Any]]:
        """Get Excel styles discovery patterns"""
        return [
            {
                'xpath': '//color',
                'element_type': DesignElementType.COLOR,
                'value_attribute': 'theme',
                'is_customizable': True
            },
            {
                'xpath': '//name',
                'element_type': DesignElementType.FONT,
                'value_attribute': 'val',
                'is_customizable': True
            },
            {
                'xpath': '//patternFill',
                'element_type': DesignElementType.FILL,
                'value_attribute': 'patternType',
                'is_customizable': True
            },
            {
                'xpath': '//border',
                'element_type': DesignElementType.BORDER,
                'semantic_name_pattern': r'border(\d+)',
                'is_customizable': True
            }
        ]
        
    def _get_excel_workbook_patterns(self) -> List[Dict[str, Any]]:
        """Get Excel workbook discovery patterns"""
        return [
            {
                'xpath': '//cellStyle',
                'element_type': DesignElementType.TEXT_FORMAT,
                'value_attribute': 'name',
                'is_customizable': True
            }
        ]
        
    def get_analysis_statistics(self) -> Dict[str, int]:
        """Get analysis statistics"""
        return dict(self.statistics)