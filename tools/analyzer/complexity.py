"""
Template Complexity Analysis System

This module provides comprehensive complexity analysis for OOXML templates,
scoring and categorizing templates based on various complexity factors.
"""

from typing import Dict, List, Any, Optional
import math
from collections import Counter

from .types import DesignElement, DesignElementType, ComplexityScore, AnalysisContext


class ComplexityAnalyzer:
    """
    Analyzes template complexity and provides scoring and categorization.
    
    Considers factors like element diversity, customization depth,
    cross-platform complexity, and accessibility requirements.
    """
    
    def __init__(self, context: AnalysisContext):
        self.context = context
        
        # Complexity scoring weights
        self.complexity_weights = {
            'element_count': 0.2,
            'element_diversity': 0.25,
            'customization_depth': 0.2,
            'cross_platform_complexity': 0.15,
            'accessibility_complexity': 0.1,
            'interaction_complexity': 0.1
        }
        
        # Element type complexity scores (0-10 scale)
        self.element_type_complexity = {
            DesignElementType.COLOR: 2.0,
            DesignElementType.FONT: 3.0,
            DesignElementType.TEXT_FORMAT: 4.0,
            DesignElementType.GRADIENT: 6.0,
            DesignElementType.EFFECT: 7.0,
            DesignElementType.ANIMATION: 9.0,
            DesignElementType.CHART: 8.0,
            DesignElementType.TABLE: 5.0,
            DesignElementType.SHAPE: 4.0,
            DesignElementType.IMAGE: 3.0,
            DesignElementType.BORDER: 2.0,
            DesignElementType.FILL: 3.0,
            DesignElementType.DIMENSION: 4.0,
            DesignElementType.SPACING: 3.0,
            DesignElementType.POSITION: 5.0
        }
        
        # Complexity categories and thresholds
        self.complexity_categories = {
            'Simple': (0.0, 3.0),
            'Moderate': (3.0, 5.5),
            'Complex': (5.5, 7.5),
            'Expert': (7.5, 10.0)
        }
    
    def analyze_complexity(self, design_elements: List[DesignElement]) -> ComplexityScore:
        """
        Analyze the complexity of a template based on its design elements.
        
        Args:
            design_elements: List of discovered design elements
            
        Returns:
            ComplexityScore with detailed analysis
        """
        if not design_elements:
            return ComplexityScore(
                complexity_score=0.0,
                total_elements=0,
                customizable_elements=0,
                element_diversity=0,
                factors={},
                category='Simple',
                metadata={'analysis_method': 'empty_template'}
            )
        
        # Calculate complexity factors
        factors = {}
        
        # Factor 1: Element count complexity
        factors['element_count'] = self._calculate_element_count_complexity(design_elements)
        
        # Factor 2: Element diversity complexity
        factors['element_diversity'] = self._calculate_element_diversity_complexity(design_elements)
        
        # Factor 3: Customization depth complexity
        factors['customization_depth'] = self._calculate_customization_depth_complexity(design_elements)
        
        # Factor 4: Cross-platform complexity
        factors['cross_platform_complexity'] = self._calculate_cross_platform_complexity(design_elements)
        
        # Factor 5: Accessibility complexity
        factors['accessibility_complexity'] = self._calculate_accessibility_complexity(design_elements)
        
        # Factor 6: Element interaction complexity
        factors['interaction_complexity'] = self._calculate_interaction_complexity(design_elements)
        
        # Calculate weighted overall score
        complexity_score = sum(
            factors[factor] * self.complexity_weights.get(factor, 0.0)
            for factor in factors
        )
        
        # Ensure score is within 0-10 range
        complexity_score = max(0.0, min(10.0, complexity_score))
        
        # Determine category
        category = self._determine_complexity_category(complexity_score)
        
        # Count elements
        total_elements = len(design_elements)
        customizable_elements = sum(1 for elem in design_elements if elem.is_customizable)
        element_diversity = len(set(elem.element_type for elem in design_elements))
        
        return ComplexityScore(
            complexity_score=complexity_score,
            total_elements=total_elements,
            customizable_elements=customizable_elements,
            element_diversity=element_diversity,
            factors=factors,
            category=category,
            metadata={
                'analysis_method': 'weighted_factors',
                'template_type': self.context.template_type,
                'files_analyzed': len(self.context.files_to_analyze),
                'complexity_distribution': self._get_complexity_distribution(design_elements)
            }
        )
    
    def _calculate_element_count_complexity(self, design_elements: List[DesignElement]) -> float:
        """Calculate complexity based on total number of elements."""
        count = len(design_elements)
        
        # Logarithmic scaling to prevent extreme scores
        if count == 0:
            return 0.0
        elif count <= 10:
            return 1.0 + (count / 10.0) * 2.0  # 1.0 - 3.0
        elif count <= 50:
            return 3.0 + ((count - 10) / 40.0) * 3.0  # 3.0 - 6.0
        elif count <= 100:
            return 6.0 + ((count - 50) / 50.0) * 2.0  # 6.0 - 8.0
        else:
            return min(10.0, 8.0 + math.log(count / 100.0) * 2.0)
    
    def _calculate_element_diversity_complexity(self, design_elements: List[DesignElement]) -> float:
        """Calculate complexity based on diversity of element types."""
        if not design_elements:
            return 0.0
        
        # Count unique element types
        element_types = set(elem.element_type for elem in design_elements)
        diversity_count = len(element_types)
        
        # Weight by complexity of individual element types
        type_complexity_sum = sum(
            self.element_type_complexity.get(elem_type, 5.0) 
            for elem_type in element_types
        )
        
        # Normalize by number of types
        avg_type_complexity = type_complexity_sum / diversity_count if diversity_count > 0 else 0.0
        
        # Scale based on diversity count
        diversity_factor = min(1.0, diversity_count / len(DesignElementType))
        
        return avg_type_complexity * diversity_factor
    
    def _calculate_customization_depth_complexity(self, design_elements: List[DesignElement]) -> float:
        """Calculate complexity based on depth of customization required."""
        if not design_elements:
            return 0.0
        
        complexity_scores = []
        
        for element in design_elements:
            element_complexity = 0.0
            
            # Base complexity from element type
            element_complexity += self.element_type_complexity.get(element.element_type, 5.0)
            
            # Add complexity based on priority score (higher priority = more complex to implement well)
            element_complexity += (element.priority_score / 10.0) * 2.0
            
            # Add complexity based on brand relevance
            element_complexity += (element.brand_relevance / 10.0) * 1.5
            
            # Add complexity for accessibility requirements
            element_complexity += (element.accessibility_impact / 10.0) * 1.0
            
            # Add complexity for dependencies
            if element.dependencies:
                element_complexity += len(element.dependencies) * 0.5
            
            complexity_scores.append(element_complexity)
        
        # Return average complexity, capped at 10.0
        return min(10.0, sum(complexity_scores) / len(complexity_scores))
    
    def _calculate_cross_platform_complexity(self, design_elements: List[DesignElement]) -> float:
        """Calculate complexity related to cross-platform compatibility."""
        if not design_elements:
            return 0.0
        
        # Count elements that may have cross-platform issues
        cross_platform_issues = 0
        total_customizable = 0
        
        for element in design_elements:
            if element.is_customizable:
                total_customizable += 1
                
                # Check for potential cross-platform issues
                if not element.cross_platform_compatible:
                    cross_platform_issues += 1
                
                # Check Office version support
                supported_versions = element.office_versions_supported
                if supported_versions and len(supported_versions) < 3:
                    cross_platform_issues += 0.5
                
                # Certain element types are inherently more complex cross-platform
                complex_types = [
                    DesignElementType.ANIMATION,
                    DesignElementType.EFFECT,
                    DesignElementType.CHART
                ]
                if element.element_type in complex_types:
                    cross_platform_issues += 0.3
        
        if total_customizable == 0:
            return 0.0
        
        # Calculate complexity as percentage of problematic elements
        complexity_ratio = cross_platform_issues / total_customizable
        return min(10.0, complexity_ratio * 8.0)  # Scale to 0-8 range, cap at 10
    
    def _calculate_accessibility_complexity(self, design_elements: List[DesignElement]) -> float:
        """Calculate complexity related to accessibility requirements."""
        if not design_elements:
            return 0.0
        
        accessibility_scores = []
        
        for element in design_elements:
            if element.is_customizable:
                # Elements that affect accessibility are more complex
                accessibility_score = element.accessibility_impact
                
                # Color and font elements require careful accessibility consideration
                if element.element_type in [DesignElementType.COLOR, DesignElementType.FONT]:
                    accessibility_score *= 1.5
                
                # Text formatting affects readability
                if element.element_type == DesignElementType.TEXT_FORMAT:
                    accessibility_score *= 1.3
                
                accessibility_scores.append(accessibility_score)
        
        if not accessibility_scores:
            return 0.0
        
        # Return average accessibility complexity
        return min(10.0, sum(accessibility_scores) / len(accessibility_scores))
    
    def _calculate_interaction_complexity(self, design_elements: List[DesignElement]) -> float:
        """Calculate complexity based on element interactions and dependencies."""
        if not design_elements:
            return 0.0
        
        total_dependencies = 0
        elements_with_dependencies = 0
        circular_dependencies = 0
        
        # Create dependency map
        dependency_map = {}
        for element in design_elements:
            dependency_map[element.id] = element.dependencies
            
            if element.dependencies:
                elements_with_dependencies += 1
                total_dependencies += len(element.dependencies)
        
        # Check for circular dependencies (simplified)
        circular_dependencies = self._detect_circular_dependencies(dependency_map)
        
        # Calculate interaction complexity
        if len(design_elements) == 0:
            return 0.0
        
        dependency_ratio = elements_with_dependencies / len(design_elements)
        avg_dependencies = total_dependencies / max(elements_with_dependencies, 1)
        
        interaction_score = 0.0
        interaction_score += dependency_ratio * 5.0  # Base complexity from having dependencies
        interaction_score += min(3.0, avg_dependencies * 0.5)  # Additional complexity per dependency
        interaction_score += circular_dependencies * 2.0  # Penalty for circular dependencies
        
        return min(10.0, interaction_score)
    
    def _detect_circular_dependencies(self, dependency_map: Dict[str, List[str]]) -> int:
        """Detect circular dependencies in the element dependency graph."""
        # Simple cycle detection - count potential cycles
        cycles = 0
        
        for element_id, deps in dependency_map.items():
            if not deps:
                continue
                
            # Check if any dependency also depends on this element (direct cycle)
            for dep_id in deps:
                if dep_id in dependency_map:
                    dep_deps = dependency_map[dep_id]
                    if element_id in dep_deps:
                        cycles += 1
        
        return cycles // 2  # Each cycle is counted twice
    
    def _determine_complexity_category(self, score: float) -> str:
        """Determine complexity category based on score."""
        for category, (min_score, max_score) in self.complexity_categories.items():
            if min_score <= score < max_score:
                return category
        
        return 'Expert'  # Default for scores >= 7.5
    
    def _get_complexity_distribution(self, design_elements: List[DesignElement]) -> Dict[str, Any]:
        """Get distribution of complexity across different aspects."""
        if not design_elements:
            return {}
        
        # Element type distribution
        type_counts = Counter(elem.element_type.value for elem in design_elements)
        
        # Priority distribution
        priority_ranges = {
            'high_priority': len([e for e in design_elements if e.priority_score >= 8.0]),
            'medium_priority': len([e for e in design_elements if 5.0 <= e.priority_score < 8.0]),
            'low_priority': len([e for e in design_elements if e.priority_score < 5.0])
        }
        
        # Customization distribution
        customization_stats = {
            'customizable': len([e for e in design_elements if e.is_customizable]),
            'non_customizable': len([e for e in design_elements if not e.is_customizable]),
            'high_impact': len([e for e in design_elements if e.customization_impact >= 7.0]),
            'medium_impact': len([e for e in design_elements if 4.0 <= e.customization_impact < 7.0]),
            'low_impact': len([e for e in design_elements if e.customization_impact < 4.0])
        }
        
        return {
            'element_type_distribution': dict(type_counts),
            'priority_distribution': priority_ranges,
            'customization_distribution': customization_stats,
            'total_elements': len(design_elements),
            'avg_priority_score': sum(e.priority_score for e in design_elements) / len(design_elements),
            'avg_impact_score': sum(e.customization_impact for e in design_elements) / len(design_elements)
        }
    
    def get_complexity_recommendations(self, complexity_score: ComplexityScore) -> List[Dict[str, Any]]:
        """Generate recommendations based on complexity analysis."""
        recommendations = []
        
        # Recommendations based on overall complexity
        if complexity_score.category == 'Expert':
            recommendations.append({
                'type': 'complexity_management',
                'title': 'Consider Phased Implementation',
                'description': 'This template has expert-level complexity. Consider implementing customization in phases.',
                'priority': 8.0,
                'effort': 'high'
            })
        
        # Recommendations based on specific factors
        factors = complexity_score.factors
        
        if factors.get('element_diversity', 0) > 7.0:
            recommendations.append({
                'type': 'element_diversity',
                'title': 'Simplify Element Types',
                'description': 'Consider reducing the variety of customizable element types to improve maintainability.',
                'priority': 6.0,
                'effort': 'medium'
            })
        
        if factors.get('cross_platform_complexity', 0) > 6.0:
            recommendations.append({
                'type': 'cross_platform',
                'title': 'Review Cross-Platform Compatibility',
                'description': 'Several elements may have cross-platform compatibility issues.',
                'priority': 7.0,
                'effort': 'medium'
            })
        
        if factors.get('accessibility_complexity', 0) > 7.0:
            recommendations.append({
                'type': 'accessibility',
                'title': 'Accessibility Review Required',
                'description': 'High accessibility complexity detected. Consider accessibility audit.',
                'priority': 8.5,
                'effort': 'medium'
            })
        
        if factors.get('interaction_complexity', 0) > 5.0:
            recommendations.append({
                'type': 'dependencies',
                'title': 'Simplify Element Dependencies',
                'description': 'Complex element dependencies detected. Consider reducing interdependencies.',
                'priority': 5.5,
                'effort': 'low'
            })
        
        return sorted(recommendations, key=lambda x: x['priority'], reverse=True)