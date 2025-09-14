"""Semantic diff engine for identifying meaningful changes vs ignorable noise."""

from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from lxml import etree
from .xml_parser import XMLNormalizer, XMLDifference, ComparisonResult


class DiffCategory(Enum):
    """Categories of differences for filtering."""
    PRESERVED = "preserved"       # Content preserved exactly
    MODIFIED = "modified"         # Content modified but semantically similar
    DROPPED = "dropped"          # Content removed entirely  
    ADDED = "added"              # New content added
    NOISE = "noise"              # Ignorable differences (formatting, metadata)


class DiffSeverity(Enum):
    """Severity levels for differences."""
    CRITICAL = "critical"        # Major structural or content changes
    MAJOR = "major"             # Significant formatting or style changes
    MINOR = "minor"             # Small changes that don't affect meaning
    IGNORABLE = "ignorable"     # Changes that can be safely ignored


@dataclass
class SemanticDifference:
    """Enhanced difference with semantic analysis."""
    xpath: str
    category: DiffCategory
    severity: DiffSeverity
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    element_name: Optional[str] = None
    description: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class DiffSummary:
    """Summary of differences by category and severity."""
    total_differences: int
    by_category: Dict[DiffCategory, int]
    by_severity: Dict[DiffSeverity, int]
    critical_changes: List[SemanticDifference]
    preservation_rate: float  # Percentage of content preserved


class SemanticDiffEngine:
    """Engine for identifying meaningful changes vs ignorable noise."""
    
    def __init__(self):
        self.normalizer = XMLNormalizer()
        self._setup_ignore_patterns()
        self._setup_significance_rules()
    
    def _setup_ignore_patterns(self):
        """Configure patterns for ignorable differences."""
        # Attributes that are typically ignorable
        self.ignorable_attributes = {
            'rsidR', 'rsidRPr', 'rsidP', 'rsidRDefault', 'rsidSect',  # Word revision IDs
            'created', 'modified', 'lastPrinted',                      # Metadata timestamps
            'uniqueId', 'id', 'objectId',                              # Generated IDs
            'lang', 'langId',                                          # Language settings (context dependent)
        }
        
        # Elements that are typically ignorable
        self.ignorable_elements = {
            'lastRenderedPageBreak',    # Page layout artifacts
            'proofErr',                 # Spell check artifacts
            'bookmarkStart', 'bookmarkEnd',  # Bookmark markers (unless content-critical)
        }
        
        # Namespace prefixes that indicate metadata
        self.metadata_namespaces = {
            'dcterms:', 'dc:', 'cp:',   # Dublin Core metadata
            'app:', 'vt:',              # Application properties
        }
    
    def _setup_significance_rules(self):
        """Configure rules for determining significance of changes."""
        # Content that is always critical
        self.critical_content_patterns = {
            '//w:t',                    # Text content in Word
            '//a:t',                    # Text content in PowerPoint
            '//v',                      # Cell values in Excel
            '//f',                      # Formulas in Excel
        }
        
        # Style-related patterns by significance
        self.style_significance = {
            'critical': {
                'color', 'sz', 'b', 'i', 'u',           # Font formatting
                'spacing', 'ind', 'jc',                  # Paragraph formatting
                'fill', 'solidFill',                     # Background fills
            },
            'major': {
                'rFonts', 'ascii', 'hAnsi',             # Font families
                'pStyle', 'rStyle',                      # Style references
                'numPr', 'ilvl',                        # Numbering
            },
            'minor': {
                'lang', 'kern', 'position',             # Typography details
                'w', 'wrap', 'vAlign',                   # Layout details
            }
        }
    
    def analyze_differences(self, original_xml: bytes, converted_xml: bytes,
                          document_type: str = 'word') -> Tuple[List[SemanticDifference], DiffSummary]:
        """
        Analyze differences between original and converted XML.
        
        Args:
            original_xml: Original XML content
            converted_xml: Converted XML content  
            document_type: Type of document (word, powerpoint, excel)
            
        Returns:
            Tuple of (semantic differences list, summary)
        """
        # First get raw differences
        from .xml_parser import SemanticComparator
        comparator = SemanticComparator()
        raw_result = comparator.compare(original_xml, converted_xml)
        
        # Enhance differences with semantic analysis
        semantic_differences = []
        for raw_diff in raw_result.differences:
            semantic_diff = self._enhance_difference(raw_diff, document_type)
            semantic_differences.append(semantic_diff)
        
        # Generate summary
        summary = self._generate_summary(semantic_differences, raw_result)
        
        return semantic_differences, summary
    
    def _enhance_difference(self, raw_diff: XMLDifference, 
                          document_type: str) -> SemanticDifference:
        """Enhance a raw difference with semantic analysis."""
        # Determine category based on diff type
        category = self._categorize_difference(raw_diff)
        
        # Determine severity based on content and context
        severity = self._assess_severity(raw_diff, document_type)
        
        # Generate human-readable description
        description = self._generate_description(raw_diff, category, severity)
        
        # Extract additional context
        context = self._extract_context(raw_diff, document_type)
        
        return SemanticDifference(
            xpath=raw_diff.xpath,
            category=category,
            severity=severity,
            old_value=raw_diff.old_value,
            new_value=raw_diff.new_value,
            element_name=raw_diff.element_name,
            description=description,
            context=context
        )
    
    def _categorize_difference(self, diff: XMLDifference) -> DiffCategory:
        """Categorize difference type."""
        if diff.diff_type == 'element_added':
            return DiffCategory.ADDED
        elif diff.diff_type == 'element_removed':
            return DiffCategory.DROPPED
        elif diff.diff_type in ['text_content', 'attribute_changed']:
            if diff.old_value and diff.new_value:
                return DiffCategory.MODIFIED
            elif diff.old_value:
                return DiffCategory.DROPPED
            else:
                return DiffCategory.ADDED
        else:
            return DiffCategory.MODIFIED
    
    def _assess_severity(self, diff: XMLDifference, document_type: str) -> DiffSeverity:
        """Assess the severity of a difference."""
        # Check if it's ignorable noise
        if self._is_ignorable_difference(diff):
            return DiffSeverity.IGNORABLE
        
        # Check if it affects critical content
        if self._affects_critical_content(diff, document_type):
            return DiffSeverity.CRITICAL
        
        # Check style significance
        style_level = self._assess_style_significance(diff)
        if style_level == 'critical':
            return DiffSeverity.CRITICAL
        elif style_level == 'major':
            return DiffSeverity.MAJOR
        elif style_level == 'minor':
            return DiffSeverity.MINOR
        
        # Default assessment based on change magnitude
        if diff.diff_type == 'text_content':
            if diff.old_value and diff.new_value:
                # Text content change - usually critical
                return DiffSeverity.CRITICAL
            else:
                # Text added/removed - critical
                return DiffSeverity.CRITICAL
        elif diff.diff_type in ['element_added', 'element_removed']:
            # Structural changes - major by default
            return DiffSeverity.MAJOR
        else:
            # Attribute changes - minor by default
            return DiffSeverity.MINOR
    
    def _is_ignorable_difference(self, diff: XMLDifference) -> bool:
        """Check if difference is ignorable noise."""
        # Check ignorable attributes
        if diff.attribute_name and diff.attribute_name in self.ignorable_attributes:
            return True
        
        # Check ignorable elements
        if diff.element_name and diff.element_name in self.ignorable_elements:
            return True
        
        # Check metadata namespaces
        for ns_prefix in self.metadata_namespaces:
            if diff.xpath.startswith(f'//{ns_prefix}'):
                return True
        
        # Check for revision tracking elements
        if 'rsid' in diff.xpath.lower():
            return True
        
        return False
    
    def _affects_critical_content(self, diff: XMLDifference, document_type: str) -> bool:
        """Check if difference affects critical content."""
        # Check against critical content patterns
        for pattern in self.critical_content_patterns:
            if pattern.replace('//', '').replace(':', '') in diff.xpath:
                return True
        
        # Document-specific critical content
        if document_type == 'word':
            critical_elements = {'t', 'p', 'r', 'tbl'}  # Text, paragraphs, runs, tables
        elif document_type == 'powerpoint':
            critical_elements = {'t', 'p', 'r', 'sp'}   # Text, paragraphs, runs, shapes
        elif document_type == 'excel':
            critical_elements = {'v', 'f', 'c', 'row'}  # Values, formulas, cells, rows
        else:
            critical_elements = {'t', 'p', 'r'}         # Default text elements
        
        # Check if any critical element is in the xpath
        for element in critical_elements:
            if f'/{element}' in diff.xpath or diff.element_name == element:
                return True
        
        return False
    
    def _assess_style_significance(self, diff: XMLDifference) -> Optional[str]:
        """Assess significance of style-related changes."""
        attr_name = diff.attribute_name or diff.element_name or ''
        
        for level, patterns in self.style_significance.items():
            if any(pattern in attr_name for pattern in patterns):
                return level
        
        return None
    
    def _generate_description(self, diff: XMLDifference, 
                            category: DiffCategory, severity: DiffSeverity) -> str:
        """Generate human-readable description of difference."""
        element = diff.element_name or 'element'
        attr = diff.attribute_name or ''
        
        if diff.diff_type == 'text_content':
            if category == DiffCategory.MODIFIED:
                return f"Text content changed from '{diff.old_value}' to '{diff.new_value}'"
            elif category == DiffCategory.ADDED:
                return f"Text content added: '{diff.new_value}'"
            elif category == DiffCategory.DROPPED:
                return f"Text content removed: '{diff.old_value}'"
        
        elif diff.diff_type == 'attribute_changed':
            return f"Attribute '{attr}' changed from '{diff.old_value}' to '{diff.new_value}'"
        
        elif diff.diff_type == 'element_added':
            return f"Element '{element}' was added"
        
        elif diff.diff_type == 'element_removed':
            return f"Element '{element}' was removed"
        
        return f"{diff.diff_type.replace('_', ' ').title()} in {element}"
    
    def _extract_context(self, diff: XMLDifference, document_type: str) -> Dict[str, Any]:
        """Extract additional context for the difference."""
        context = {
            'document_type': document_type,
            'xpath_depth': len(diff.xpath.split('/')),
            'is_root_level': len(diff.xpath.split('/')) <= 3,
        }
        
        # Add document-specific context
        if 'style' in diff.xpath.lower():
            context['affects_styling'] = True
        
        if any(text_marker in diff.xpath for text_marker in ['/t', '/v', '/f']):
            context['affects_content'] = True
        
        if any(struct_marker in diff.xpath for struct_marker in ['/p', '/tbl', '/sp']):
            context['affects_structure'] = True
        
        return context
    
    def _generate_summary(self, differences: List[SemanticDifference], 
                         raw_result: ComparisonResult) -> DiffSummary:
        """Generate summary of differences."""
        total_diffs = len(differences)
        
        # Count by category
        by_category = {}
        for category in DiffCategory:
            by_category[category] = len([d for d in differences if d.category == category])
        
        # Count by severity
        by_severity = {}
        for severity in DiffSeverity:
            by_severity[severity] = len([d for d in differences if d.severity == severity])
        
        # Extract critical changes
        critical_changes = [d for d in differences if d.severity == DiffSeverity.CRITICAL]
        
        # Calculate preservation rate
        preserved_count = by_category.get(DiffCategory.PRESERVED, 0)
        ignorable_count = by_severity.get(DiffSeverity.IGNORABLE, 0)
        preservation_rate = (preserved_count + ignorable_count) / max(total_diffs, 1) * 100
        
        return DiffSummary(
            total_differences=total_diffs,
            by_category=by_category,
            by_severity=by_severity,
            critical_changes=critical_changes,
            preservation_rate=preservation_rate
        )
    
    def filter_differences(self, differences: List[SemanticDifference],
                          min_severity: DiffSeverity = DiffSeverity.MINOR,
                          categories: Optional[Set[DiffCategory]] = None) -> List[SemanticDifference]:
        """Filter differences by severity and category."""
        severity_order = {
            DiffSeverity.IGNORABLE: 0,
            DiffSeverity.MINOR: 1,
            DiffSeverity.MAJOR: 2,
            DiffSeverity.CRITICAL: 3
        }
        
        min_level = severity_order[min_severity]
        
        filtered = []
        for diff in differences:
            # Check severity threshold
            if severity_order[diff.severity] < min_level:
                continue
            
            # Check category filter
            if categories and diff.category not in categories:
                continue
            
            filtered.append(diff)
        
        return filtered
    
    def get_preservation_metrics(self, differences: List[SemanticDifference],
                               original_element_count: int) -> Dict[str, float]:
        """Calculate preservation metrics."""
        total_changes = len(differences)
        
        # Count changes by type
        content_changes = len([d for d in differences 
                              if d.context and d.context.get('affects_content')])
        style_changes = len([d for d in differences 
                            if d.context and d.context.get('affects_styling')])
        structure_changes = len([d for d in differences 
                               if d.context and d.context.get('affects_structure')])
        
        # Calculate rates
        total_rate = (original_element_count - total_changes) / max(original_element_count, 1)
        content_preservation = 1.0 - (content_changes / max(original_element_count, 1))
        style_preservation = 1.0 - (style_changes / max(original_element_count, 1))
        structure_preservation = 1.0 - (structure_changes / max(original_element_count, 1))
        
        return {
            'overall_preservation': max(0, total_rate),
            'content_preservation': max(0, content_preservation),
            'style_preservation': max(0, style_preservation),
            'structure_preservation': max(0, structure_preservation),
            'change_ratio': total_changes / max(original_element_count, 1)
        }