"""
Variable Coverage Analysis System

This module provides comprehensive analysis of variable coverage
in OOXML templates with recommendations for achieving 100% coverage.
"""

from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import math

from .types import (
    DesignElement, DesignElementType, PriorityLevel, VariableCoverage,
    CoverageReport, AnalysisContext
)


class CoverageAnalyzer:
    """
    Analyzes variable coverage in templates and generates recommendations
    for achieving target coverage levels.
    """
    
    def __init__(self, context: AnalysisContext, target_coverage: float = 100.0):
        self.context = context
        self.target_coverage = target_coverage
        
        # Coverage calculation weights
        self.coverage_weights = {
            'priority_multiplier': 1.5,
            'frequency_multiplier': 1.2,
            'brand_relevance_multiplier': 1.8,
            'accessibility_multiplier': 1.3
        }
        
        # Priority level thresholds
        self.priority_thresholds = {
            PriorityLevel.CRITICAL: 9.0,
            PriorityLevel.HIGH: 7.0,
            PriorityLevel.MEDIUM: 5.0,
            PriorityLevel.LOW: 0.0
        }
    
    def analyze_coverage(self, design_elements: List[DesignElement],
                        existing_variables: Optional[Dict[str, Any]] = None) -> VariableCoverage:
        """
        Analyze variable coverage for a set of design elements.
        
        Args:
            design_elements: List of discovered design elements
            existing_variables: Dictionary of existing extension variables
            
        Returns:
            VariableCoverage analysis results
        """
        if not existing_variables:
            existing_variables = {}
        
        # Calculate basic coverage metrics
        total_elements = len(design_elements)
        covered_elements = self._count_covered_elements(design_elements, existing_variables)
        uncovered_elements = self._identify_uncovered_elements(design_elements, existing_variables)
        
        coverage_percentage = (covered_elements / total_elements * 100) if total_elements > 0 else 0.0
        
        # Analyze coverage by type
        coverage_by_type = self._analyze_coverage_by_type(design_elements, existing_variables)
        
        # Analyze coverage by priority
        coverage_by_priority = self._analyze_coverage_by_priority(design_elements, existing_variables)
        
        # Analyze coverage by file
        coverage_by_file = self._analyze_coverage_by_file(design_elements, existing_variables)
        
        # Generate recommendations
        recommendations = self._generate_coverage_recommendations(
            uncovered_elements, existing_variables
        )
        
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
    
    def _count_covered_elements(self, design_elements: List[DesignElement],
                               existing_variables: Dict[str, Any]) -> int:
        """Count elements that are covered by existing variables."""
        covered = 0
        
        for element in design_elements:
            if self._is_element_covered(element, existing_variables):
                covered += 1
        
        return covered
    
    def _is_element_covered(self, element: DesignElement,
                           existing_variables: Dict[str, Any]) -> bool:
        """Check if a design element is covered by existing variables."""
        # Simple heuristic - check if there's a variable that could target this element
        element_key = f"{element.file_location}:{element.xpath_expression}"
        
        # Check direct matches
        for var_name, var_data in existing_variables.items():
            if isinstance(var_data, dict):
                var_xpath = var_data.get('xpath', '')
                var_file = var_data.get('file', '')
                
                # Check for xpath and file matches
                if (var_xpath == element.xpath_expression and 
                    var_file in element.file_location):
                    return True
                
                # Check for semantic name matches
                if element.semantic_name.lower() in var_name.lower():
                    return True
        
        return False
    
    def _identify_uncovered_elements(self, design_elements: List[DesignElement],
                                   existing_variables: Dict[str, Any]) -> List[DesignElement]:
        """Identify elements not covered by existing variables."""
        uncovered = []
        
        for element in design_elements:
            if not self._is_element_covered(element, existing_variables):
                uncovered.append(element)
        
        return uncovered
    
    def _analyze_coverage_by_type(self, design_elements: List[DesignElement],
                                 existing_variables: Dict[str, Any]) -> Dict[DesignElementType, Dict[str, Any]]:
        """Analyze coverage breakdown by element type."""
        coverage_by_type = {}
        
        # Group elements by type
        elements_by_type = defaultdict(list)
        for element in design_elements:
            elements_by_type[element.element_type].append(element)
        
        # Calculate coverage for each type
        for element_type, type_elements in elements_by_type.items():
            total = len(type_elements)
            covered = sum(1 for elem in type_elements 
                         if self._is_element_covered(elem, existing_variables))
            
            coverage_percentage = (covered / total * 100) if total > 0 else 0.0
            
            coverage_by_type[element_type] = {
                'total_elements': total,
                'covered_elements': covered,
                'coverage_percentage': coverage_percentage,
                'uncovered_count': total - covered,
                'priority_distribution': self._get_priority_distribution(type_elements)
            }
        
        return coverage_by_type
    
    def _analyze_coverage_by_priority(self, design_elements: List[DesignElement],
                                     existing_variables: Dict[str, Any]) -> Dict[PriorityLevel, Dict[str, Any]]:
        """Analyze coverage breakdown by priority level."""
        coverage_by_priority = {}
        
        # Group elements by priority
        elements_by_priority = defaultdict(list)
        for element in design_elements:
            priority = self._get_element_priority_level(element)
            elements_by_priority[priority].append(element)
        
        # Calculate coverage for each priority level
        for priority_level, priority_elements in elements_by_priority.items():
            total = len(priority_elements)
            covered = sum(1 for elem in priority_elements 
                         if self._is_element_covered(elem, existing_variables))
            
            coverage_percentage = (covered / total * 100) if total > 0 else 0.0
            
            coverage_by_priority[priority_level] = {
                'total_elements': total,
                'covered_elements': covered,
                'coverage_percentage': coverage_percentage,
                'uncovered_count': total - covered,
                'avg_priority_score': sum(elem.priority_score for elem in priority_elements) / total
            }
        
        return coverage_by_priority
    
    def _analyze_coverage_by_file(self, design_elements: List[DesignElement],
                                 existing_variables: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Analyze coverage breakdown by file."""
        coverage_by_file = {}
        
        # Group elements by file
        elements_by_file = defaultdict(list)
        for element in design_elements:
            elements_by_file[element.file_location].append(element)
        
        # Calculate coverage for each file
        for file_path, file_elements in elements_by_file.items():
            total = len(file_elements)
            covered = sum(1 for elem in file_elements 
                         if self._is_element_covered(elem, existing_variables))
            
            coverage_percentage = (covered / total * 100) if total > 0 else 0.0
            
            coverage_by_file[file_path] = {
                'total_elements': total,
                'covered_elements': covered,
                'coverage_percentage': coverage_percentage,
                'uncovered_count': total - covered,
                'file_type': self._determine_file_type(file_path),
                'element_types': list(set(elem.element_type for elem in file_elements))
            }
        
        return coverage_by_file
    
    def _generate_coverage_recommendations(self, uncovered_elements: List[DesignElement],
                                         existing_variables: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations for improving coverage."""
        recommendations = []
        
        # Sort uncovered elements by priority
        sorted_uncovered = sorted(uncovered_elements, 
                                key=lambda x: x.priority_score, reverse=True)
        
        # Group by similar elements for batch recommendations
        element_groups = self._group_similar_elements(sorted_uncovered)
        
        # Generate recommendations for each group
        for group_key, group_elements in element_groups.items():
            recommendation = self._create_group_recommendation(group_elements, existing_variables)
            if recommendation:
                recommendations.append(recommendation)
        
        # Add high-impact individual recommendations
        high_impact_elements = [elem for elem in sorted_uncovered 
                               if elem.priority_score >= 8.0]
        
        for element in high_impact_elements[:5]:  # Top 5 high-impact elements
            individual_rec = self._create_individual_recommendation(element, existing_variables)
            if individual_rec:
                recommendations.append(individual_rec)
        
        return sorted(recommendations, key=lambda x: x.get('priority', 0), reverse=True)
    
    def _group_similar_elements(self, elements: List[DesignElement]) -> Dict[str, List[DesignElement]]:
        """Group similar elements for batch recommendations."""
        groups = defaultdict(list)
        
        for element in elements:
            # Group by type and semantic similarity
            group_key = f"{element.element_type.value}_{self._get_semantic_group(element.semantic_name)}"
            groups[group_key].append(element)
        
        return groups
    
    def _get_semantic_group(self, semantic_name: str) -> str:
        """Get semantic group for similar element names."""
        name_lower = semantic_name.lower()
        
        if any(word in name_lower for word in ['brand', 'primary', 'main']):
            return 'brand'
        elif any(word in name_lower for word in ['accent', 'secondary']):
            return 'accent'
        elif any(word in name_lower for word in ['background', 'bg']):
            return 'background'
        elif any(word in name_lower for word in ['heading', 'title', 'h1', 'h2']):
            return 'heading'
        elif any(word in name_lower for word in ['body', 'text', 'paragraph']):
            return 'body'
        else:
            return 'other'
    
    def _create_group_recommendation(self, elements: List[DesignElement],
                                   existing_variables: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create recommendation for a group of similar elements."""
        if not elements:
            return None
        
        element_type = elements[0].element_type
        semantic_group = self._get_semantic_group(elements[0].semantic_name)
        
        # Calculate group priority
        avg_priority = sum(elem.priority_score for elem in elements) / len(elements)
        total_impact = sum(elem.customization_impact for elem in elements)
        
        return {
            'type': 'group_recommendation',
            'title': f'Add {semantic_group} {element_type.value} variables',
            'description': f'Create {len(elements)} variables for {semantic_group} {element_type.value} elements',
            'priority': avg_priority,
            'impact_score': total_impact,
            'element_count': len(elements),
            'elements': [elem.id for elem in elements],
            'suggested_variable_names': [
                f"{semantic_group}_{element_type.value}_{i+1}" 
                for i in range(len(elements))
            ],
            'implementation_effort': self._estimate_implementation_effort(elements),
            'files_affected': list(set(elem.file_location for elem in elements))
        }
    
    def _create_individual_recommendation(self, element: DesignElement,
                                        existing_variables: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create recommendation for a single high-priority element."""
        suggested_name = f"{element.semantic_name}_{element.element_type.value}"
        
        return {
            'type': 'individual_recommendation',
            'title': f'Add variable for {element.semantic_name}',
            'description': f'High-priority {element.element_type.value} element with score {element.priority_score:.1f}',
            'priority': element.priority_score,
            'impact_score': element.customization_impact,
            'element_count': 1,
            'elements': [element.id],
            'suggested_variable_name': suggested_name,
            'xpath_expression': element.xpath_expression,
            'file_location': element.file_location,
            'current_value': element.current_value,
            'implementation_effort': 'low',
            'brand_relevance': element.brand_relevance,
            'accessibility_impact': element.accessibility_impact
        }
    
    def _estimate_implementation_effort(self, elements: List[DesignElement]) -> str:
        """Estimate implementation effort for a group of elements."""
        if len(elements) <= 2:
            return 'low'
        elif len(elements) <= 5:
            return 'medium'
        else:
            return 'high'
    
    def _get_element_priority_level(self, element: DesignElement) -> PriorityLevel:
        """Get priority level enum for an element based on its score."""
        score = element.priority_score
        
        if score >= self.priority_thresholds[PriorityLevel.CRITICAL]:
            return PriorityLevel.CRITICAL
        elif score >= self.priority_thresholds[PriorityLevel.HIGH]:
            return PriorityLevel.HIGH
        elif score >= self.priority_thresholds[PriorityLevel.MEDIUM]:
            return PriorityLevel.MEDIUM
        else:
            return PriorityLevel.LOW
    
    def _get_priority_distribution(self, elements: List[DesignElement]) -> Dict[str, int]:
        """Get distribution of elements by priority level."""
        distribution = Counter()
        
        for element in elements:
            priority_level = self._get_element_priority_level(element)
            distribution[priority_level.value] += 1
        
        return dict(distribution)
    
    def _determine_file_type(self, file_path: str) -> str:
        """Determine the type of file for analysis."""
        path_lower = file_path.lower()
        
        if 'theme' in path_lower:
            return 'theme'
        elif 'master' in path_lower:
            return 'master'
        elif 'styles' in path_lower:
            return 'styles'
        elif 'slide' in path_lower:
            return 'slide'
        elif 'document' in path_lower:
            return 'document'
        elif 'workbook' in path_lower:
            return 'workbook'
        else:
            return 'other'
    
    def generate_coverage_report(self, coverage_analysis: VariableCoverage,
                                template_name: str) -> CoverageReport:
        """Generate a comprehensive coverage report."""
        # Calculate improvement plan
        improvement_plan = self._create_improvement_plan(coverage_analysis)
        
        # Create coverage breakdown
        coverage_breakdown = {
            'by_type': coverage_analysis.coverage_by_type,
            'by_priority': coverage_analysis.coverage_by_priority,
            'by_file': coverage_analysis.coverage_by_file
        }
        
        return CoverageReport(
            template_name=template_name,
            total_elements=coverage_analysis.total_elements,
            covered_elements=coverage_analysis.covered_elements,
            coverage_percentage=coverage_analysis.coverage_percentage,
            uncovered_elements=coverage_analysis.uncovered_elements,
            recommended_variables=coverage_analysis.get_prioritized_recommendations(),
            coverage_breakdown=coverage_breakdown,
            improvement_plan=improvement_plan
        )
    
    def _create_improvement_plan(self, coverage_analysis: VariableCoverage) -> Dict[str, Any]:
        """Create an improvement plan to reach target coverage."""
        current_coverage = coverage_analysis.coverage_percentage
        gap_to_target = self.target_coverage - current_coverage
        
        # Prioritize recommendations by impact
        high_priority_recs = [
            rec for rec in coverage_analysis.recommendations 
            if rec.get('priority', 0) >= 8.0
        ]
        
        medium_priority_recs = [
            rec for rec in coverage_analysis.recommendations 
            if 5.0 <= rec.get('priority', 0) < 8.0
        ]
        
        return {
            'current_coverage': current_coverage,
            'target_coverage': self.target_coverage,
            'gap_to_target': gap_to_target,
            'total_recommendations': len(coverage_analysis.recommendations),
            'high_priority_count': len(high_priority_recs),
            'medium_priority_count': len(medium_priority_recs),
            'estimated_effort': self._estimate_total_effort(coverage_analysis.recommendations),
            'recommended_phases': self._create_implementation_phases(coverage_analysis.recommendations)
        }
    
    def _estimate_total_effort(self, recommendations: List[Dict[str, Any]]) -> str:
        """Estimate total implementation effort."""
        total_elements = sum(rec.get('element_count', 1) for rec in recommendations)
        
        if total_elements <= 10:
            return 'low'
        elif total_elements <= 25:
            return 'medium'
        else:
            return 'high'
    
    def _create_implementation_phases(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create phased implementation plan."""
        phases = []
        
        # Phase 1: Critical and high-priority elements
        phase1_recs = [rec for rec in recommendations if rec.get('priority', 0) >= 8.0]
        if phase1_recs:
            phases.append({
                'phase': 1,
                'title': 'Critical Elements',
                'description': 'Address highest priority design elements',
                'recommendations': phase1_recs[:5],  # Limit to top 5
                'estimated_effort': 'medium'
            })
        
        # Phase 2: Medium priority elements
        phase2_recs = [rec for rec in recommendations if 5.0 <= rec.get('priority', 0) < 8.0]
        if phase2_recs:
            phases.append({
                'phase': 2,
                'title': 'Medium Priority Elements',
                'description': 'Improve coverage with medium priority elements',
                'recommendations': phase2_recs[:10],  # Limit to top 10
                'estimated_effort': 'medium'
            })
        
        # Phase 3: Remaining elements
        remaining_recs = [rec for rec in recommendations if rec.get('priority', 0) < 5.0]
        if remaining_recs:
            phases.append({
                'phase': 3,
                'title': 'Complete Coverage',
                'description': 'Address remaining elements for 100% coverage',
                'recommendations': remaining_recs,
                'estimated_effort': 'low'
            })
        
        return phases