"""
Template Analyzer Core Types and Data Structures

This module contains the core data types, enums, and dataclasses
used throughout the template analysis system.
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone


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


@dataclass
class AnalysisConfig:
    """Configuration for template analysis"""
    analysis_level: AnalysisLevel = AnalysisLevel.STANDARD
    target_coverage: float = 100.0
    enable_complexity_scoring: bool = True
    enable_validation: bool = True
    priority_weights: Dict[str, float] = field(default_factory=dict)
    custom_patterns: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    output_format: str = "json"
    
    def __post_init__(self):
        if not self.priority_weights:
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


@dataclass
class AnalysisContext:
    """Context information for analysis operations"""
    template_path: str
    template_type: str
    files_to_analyze: List[str] = field(default_factory=list)
    namespaces: Dict[str, str] = field(default_factory=dict)
    current_file: Optional[str] = None
    processing_stats: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.namespaces:
            self.namespaces = {
                'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
                'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
                'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
                'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
                'xl': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
            }