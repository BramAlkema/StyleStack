"""Carrier-specific analysis mapping OOXML paths to StyleStack design tokens."""

from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import re
from lxml import etree


class CarrierType(Enum):
    """Types of StyleStack design token carriers."""
    COLOR_SCHEME = "color_scheme"           # Color theme definitions
    FONT_SCHEME = "font_scheme"             # Font theme definitions  
    PARAGRAPH_STYLE = "paragraph_style"     # Paragraph formatting
    CHARACTER_STYLE = "character_style"     # Character formatting
    TABLE_STYLE = "table_style"             # Table formatting
    LIST_STYLE = "list_style"               # List/numbering formatting
    THEME_VARIANT = "theme_variant"         # Theme color variants
    LAYOUT_MASTER = "layout_master"         # Slide/page layouts
    CELL_STYLE = "cell_style"               # Spreadsheet cell formatting


class CarrierCategory(Enum):
    """Categories of carriers by importance."""
    CRITICAL = "critical"      # Core design system elements
    IMPORTANT = "important"    # Secondary design elements
    OPTIONAL = "optional"      # Nice-to-have design elements


@dataclass
class CarrierMapping:
    """Maps OOXML path to StyleStack design token."""
    xpath_pattern: str              # XPath pattern to match
    carrier_type: CarrierType       # Type of carrier
    category: CarrierCategory       # Importance category
    design_token_path: str          # Path in design tokens JSON
    description: str                # Human description
    office_apps: Set[str]           # Which apps this applies to ('word', 'powerpoint', 'excel')
    namespace_prefixes: Set[str]    # Required namespace prefixes
    
    def matches_xpath(self, xpath: str) -> bool:
        """Check if XPath matches this mapping pattern."""
        # Normalize both pattern and xpath for comparison
        normalized_pattern = self._normalize_xpath_for_matching(self.xpath_pattern)
        normalized_xpath = self._normalize_xpath_for_matching(xpath)
        
        # Convert pattern to regex
        pattern = normalized_pattern.replace('*', '.*').replace('//', '/.*/').replace('[', r'\[').replace(']', r'\]')
        return bool(re.search(pattern, normalized_xpath))
    
    def _normalize_xpath_for_matching(self, xpath: str) -> str:
        """Normalize XPath by removing namespace URIs for pattern matching."""
        # Replace namespace URIs with prefixes and remove namespace prefixes for matching
        normalized = re.sub(r'\{[^}]+\}(\w+)', r'\1', xpath)  # Remove namespace URIs
        normalized = re.sub(r'\w+:(\w+)', r'\1', normalized)  # Remove namespace prefixes
        return normalized
    
    def extract_token_value(self, element) -> Optional[str]:
        """Extract design token value from XML element."""
        if element is None:
            return None
        
        # Try common attribute patterns
        for attr in ['val', 'value', 'w:val', 'a:val']:
            if attr in element.attrib:
                return element.attrib[attr]
        
        # Try text content
        if element.text:
            return element.text.strip()
        
        return None


@dataclass 
class CarrierAnalysisResult:
    """Result of analyzing carriers in a document."""
    detected_carriers: List[Tuple[CarrierMapping, str, Optional[str]]]  # (mapping, xpath, value)
    missing_carriers: List[CarrierMapping]                              # Expected but not found
    survival_rate: float                                                # Percentage preserved
    critical_failures: List[str]                                       # Critical carriers lost
    category_breakdown: Dict[CarrierCategory, Dict[str, int]]          # Stats by category


class StyleStackCarrierAnalyzer:
    """Analyzes OOXML documents for StyleStack design token carriers."""
    
    def __init__(self):
        self.carrier_mappings = self._initialize_carrier_mappings()
        self.namespace_map = self._initialize_namespaces()
    
    def _initialize_namespaces(self) -> Dict[str, str]:
        """Initialize namespace mappings for OOXML."""
        return {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
            'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
            'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
            'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
            'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
            'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
            'xdr': 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing'
        }
    
    def _initialize_carrier_mappings(self) -> List[CarrierMapping]:
        """Initialize carrier mappings for StyleStack design tokens."""
        mappings = []
        
        # Color Scheme Carriers (Critical)
        mappings.extend([
            CarrierMapping(
                xpath_pattern="//a:clrScheme//a:srgbClr/@val",
                carrier_type=CarrierType.COLOR_SCHEME,
                category=CarrierCategory.CRITICAL,
                design_token_path="tokens.color.primary",
                description="Primary theme colors",
                office_apps={'word', 'powerpoint', 'excel'},
                namespace_prefixes={'a'}
            ),
            CarrierMapping(
                xpath_pattern="//a:clrScheme//a:sysClr/@val",
                carrier_type=CarrierType.COLOR_SCHEME,
                category=CarrierCategory.CRITICAL,
                design_token_path="tokens.color.system",
                description="System theme colors",
                office_apps={'word', 'powerpoint', 'excel'},
                namespace_prefixes={'a'}
            ),
            CarrierMapping(
                xpath_pattern="//w:color/@w:val",
                carrier_type=CarrierType.CHARACTER_STYLE,
                category=CarrierCategory.IMPORTANT,
                design_token_path="tokens.color.text",
                description="Text color formatting",
                office_apps={'word'},
                namespace_prefixes={'w'}
            )
        ])
        
        # Font Scheme Carriers (Critical)
        mappings.extend([
            CarrierMapping(
                xpath_pattern="//a:fontScheme//a:latin/@typeface",
                carrier_type=CarrierType.FONT_SCHEME,
                category=CarrierCategory.CRITICAL,
                design_token_path="tokens.typography.fontFamily.primary",
                description="Primary font family",
                office_apps={'word', 'powerpoint', 'excel'},
                namespace_prefixes={'a'}
            ),
            CarrierMapping(
                xpath_pattern="//a:fontScheme//a:ea/@typeface",
                carrier_type=CarrierType.FONT_SCHEME,
                category=CarrierCategory.CRITICAL,
                design_token_path="tokens.typography.fontFamily.eastAsian",
                description="East Asian font family",
                office_apps={'word', 'powerpoint', 'excel'},
                namespace_prefixes={'a'}
            ),
            CarrierMapping(
                xpath_pattern="//w:rFonts/@w:ascii",
                carrier_type=CarrierType.CHARACTER_STYLE,
                category=CarrierCategory.IMPORTANT,
                design_token_path="tokens.typography.fontFamily.body",
                description="Body text font family",
                office_apps={'word'},
                namespace_prefixes={'w'}
            )
        ])
        
        # Paragraph Style Carriers (Important)
        mappings.extend([
            CarrierMapping(
                xpath_pattern="//w:pStyle/@w:val",
                carrier_type=CarrierType.PARAGRAPH_STYLE,
                category=CarrierCategory.IMPORTANT,
                design_token_path="tokens.typography.styles",
                description="Paragraph style references",
                office_apps={'word'},
                namespace_prefixes={'w'}
            ),
            CarrierMapping(
                xpath_pattern="//w:spacing/@w:before",
                carrier_type=CarrierType.PARAGRAPH_STYLE,
                category=CarrierCategory.IMPORTANT,
                design_token_path="tokens.spacing.paragraph.before",
                description="Paragraph spacing before",
                office_apps={'word'},
                namespace_prefixes={'w'}
            ),
            CarrierMapping(
                xpath_pattern="//w:spacing/@w:after",
                carrier_type=CarrierType.PARAGRAPH_STYLE,
                category=CarrierCategory.IMPORTANT,
                design_token_path="tokens.spacing.paragraph.after",
                description="Paragraph spacing after",
                office_apps={'word'},
                namespace_prefixes={'w'}
            ),
            CarrierMapping(
                xpath_pattern="//w:ind/@w:left",
                carrier_type=CarrierType.PARAGRAPH_STYLE,
                category=CarrierCategory.IMPORTANT,
                design_token_path="tokens.spacing.indentation.left",
                description="Left indentation",
                office_apps={'word'},
                namespace_prefixes={'w'}
            )
        ])
        
        # Character Style Carriers (Important)
        mappings.extend([
            CarrierMapping(
                xpath_pattern="//w:sz/@w:val",
                carrier_type=CarrierType.CHARACTER_STYLE,
                category=CarrierCategory.IMPORTANT,
                design_token_path="tokens.typography.fontSize",
                description="Font size",
                office_apps={'word'},
                namespace_prefixes={'w'}
            ),
            CarrierMapping(
                xpath_pattern="//w:b",
                carrier_type=CarrierType.CHARACTER_STYLE,
                category=CarrierCategory.IMPORTANT,
                design_token_path="tokens.typography.fontWeight.bold",
                description="Bold formatting",
                office_apps={'word'},
                namespace_prefixes={'w'}
            ),
            CarrierMapping(
                xpath_pattern="//w:i",
                carrier_type=CarrierType.CHARACTER_STYLE,
                category=CarrierCategory.IMPORTANT,
                design_token_path="tokens.typography.fontStyle.italic",
                description="Italic formatting",
                office_apps={'word'},
                namespace_prefixes={'w'}
            )
        ])
        
        # Table Style Carriers (Important)
        mappings.extend([
            CarrierMapping(
                xpath_pattern="//w:tblStyle/@w:val",
                carrier_type=CarrierType.TABLE_STYLE,
                category=CarrierCategory.IMPORTANT,
                design_token_path="tokens.table.style",
                description="Table style reference",
                office_apps={'word'},
                namespace_prefixes={'w'}
            ),
            CarrierMapping(
                xpath_pattern="//w:tcPr//w:shd/@w:fill",
                carrier_type=CarrierType.TABLE_STYLE,
                category=CarrierCategory.IMPORTANT,
                design_token_path="tokens.table.cell.background",
                description="Table cell background color",
                office_apps={'word'},
                namespace_prefixes={'w'}
            )
        ])
        
        # List Style Carriers (Important)
        mappings.extend([
            CarrierMapping(
                xpath_pattern="//w:numPr//w:numId/@w:val",
                carrier_type=CarrierType.LIST_STYLE,
                category=CarrierCategory.IMPORTANT,
                design_token_path="tokens.list.numbering.id",
                description="Numbering list ID",
                office_apps={'word'},
                namespace_prefixes={'w'}
            ),
            CarrierMapping(
                xpath_pattern="//w:numPr//w:ilvl/@w:val",
                carrier_type=CarrierType.LIST_STYLE,
                category=CarrierCategory.IMPORTANT,
                design_token_path="tokens.list.level",
                description="List indentation level",
                office_apps={'word'},
                namespace_prefixes={'w'}
            )
        ])
        
        # PowerPoint Specific Carriers
        mappings.extend([
            CarrierMapping(
                xpath_pattern="//p:sldLayout/@type",
                carrier_type=CarrierType.LAYOUT_MASTER,
                category=CarrierCategory.CRITICAL,
                design_token_path="tokens.layout.slideLayout",
                description="Slide layout type",
                office_apps={'powerpoint'},
                namespace_prefixes={'p'}
            ),
            CarrierMapping(
                xpath_pattern="//a:solidFill//a:srgbClr/@val",
                carrier_type=CarrierType.COLOR_SCHEME,
                category=CarrierCategory.IMPORTANT,
                design_token_path="tokens.color.fill",
                description="Shape fill colors",
                office_apps={'powerpoint'},
                namespace_prefixes={'a'}
            )
        ])
        
        # Excel Specific Carriers
        mappings.extend([
            CarrierMapping(
                xpath_pattern="//cellXfs//xf/@numFmtId",
                carrier_type=CarrierType.CELL_STYLE,
                category=CarrierCategory.IMPORTANT,
                design_token_path="tokens.cell.numberFormat",
                description="Cell number format",
                office_apps={'excel'},
                namespace_prefixes=set()
            ),
            CarrierMapping(
                xpath_pattern="//fills//fill//fgColor/@rgb",
                carrier_type=CarrierType.CELL_STYLE,
                category=CarrierCategory.IMPORTANT,
                design_token_path="tokens.cell.background",
                description="Cell background color",
                office_apps={'excel'},
                namespace_prefixes=set()
            )
        ])
        
        return mappings
    
    def analyze_carriers(self, xml_content: bytes, document_type: str) -> CarrierAnalysisResult:
        """
        Analyze document for StyleStack design token carriers.
        
        Args:
            xml_content: XML content to analyze
            document_type: Type of document ('word', 'powerpoint', 'excel')
            
        Returns:
            Analysis result with detected carriers and survival metrics
        """
        try:
            root = etree.fromstring(xml_content)
        except Exception as e:
            # Return empty result for invalid XML
            return CarrierAnalysisResult(
                detected_carriers=[],
                missing_carriers=[],
                survival_rate=0.0,
                critical_failures=[],
                category_breakdown={}
            )
        
        # Filter mappings for this document type
        relevant_mappings = [m for m in self.carrier_mappings 
                           if document_type in m.office_apps]
        
        detected_carriers = []
        missing_carriers = []
        
        for mapping in relevant_mappings:
            # Convert XPath pattern to actual XPath query
            xpath_query = self._convert_pattern_to_xpath(mapping.xpath_pattern)
            
            try:
                # Find matching elements
                elements = root.xpath(xpath_query, namespaces=self.namespace_map)
                
                if elements:
                    # Extract values from found elements
                    for element in elements:
                        if isinstance(element, str):
                            # Attribute value
                            detected_carriers.append((mapping, xpath_query, element))
                        else:
                            # Element
                            value = mapping.extract_token_value(element)
                            detected_carriers.append((mapping, xpath_query, value))
                else:
                    missing_carriers.append(mapping)
            except Exception:
                # XPath query failed - consider as missing
                missing_carriers.append(mapping)
        
        # Calculate metrics
        total_mappings = len(relevant_mappings)
        detected_count = len(detected_carriers)
        survival_rate = (detected_count / max(total_mappings, 1)) * 100
        
        # Identify critical failures
        critical_failures = [
            mapping.description for mapping in missing_carriers 
            if mapping.category == CarrierCategory.CRITICAL
        ]
        
        # Generate category breakdown
        category_breakdown = self._generate_category_breakdown(
            detected_carriers, missing_carriers
        )
        
        return CarrierAnalysisResult(
            detected_carriers=detected_carriers,
            missing_carriers=missing_carriers,
            survival_rate=survival_rate,
            critical_failures=critical_failures,
            category_breakdown=category_breakdown
        )
    
    def _convert_pattern_to_xpath(self, pattern: str) -> str:
        """Convert simplified pattern to proper XPath query."""
        # Handle attribute patterns
        if pattern.endswith('/@val') or pattern.endswith('/@w:val') or pattern.endswith('/@a:val'):
            return pattern
        elif '/@' in pattern:
            return pattern
        
        # Handle element patterns
        return pattern
    
    def _generate_category_breakdown(self, detected_carriers: List[Tuple], 
                                   missing_carriers: List[CarrierMapping]) -> Dict[CarrierCategory, Dict[str, int]]:
        """Generate breakdown of carriers by category."""
        breakdown = {}
        
        for category in CarrierCategory:
            detected_count = len([
                dc for dc in detected_carriers 
                if dc[0].category == category
            ])
            missing_count = len([
                mc for mc in missing_carriers 
                if mc.category == category
            ])
            
            breakdown[category] = {
                'detected': detected_count,
                'missing': missing_count,
                'total': detected_count + missing_count,
                'survival_rate': (detected_count / max(detected_count + missing_count, 1)) * 100
            }
        
        return breakdown
    
    def compare_carriers(self, original_xml: bytes, converted_xml: bytes, 
                        document_type: str) -> Dict[str, Any]:
        """
        Compare carriers between original and converted documents.
        
        Args:
            original_xml: Original document XML
            converted_xml: Converted document XML
            document_type: Type of document
            
        Returns:
            Comparison results with preservation metrics
        """
        original_result = self.analyze_carriers(original_xml, document_type)
        converted_result = self.analyze_carriers(converted_xml, document_type)
        
        # Map detected carriers by design token path for comparison
        original_tokens = {
            dc[0].design_token_path: dc[2] 
            for dc in original_result.detected_carriers
        }
        converted_tokens = {
            dc[0].design_token_path: dc[2] 
            for dc in converted_result.detected_carriers
        }
        
        # Analyze preservation
        preserved_tokens = {}
        modified_tokens = {}
        lost_tokens = {}
        gained_tokens = {}
        
        all_token_paths = set(original_tokens.keys()) | set(converted_tokens.keys())
        
        for token_path in all_token_paths:
            original_value = original_tokens.get(token_path)
            converted_value = converted_tokens.get(token_path)
            
            if original_value and converted_value:
                if original_value == converted_value:
                    preserved_tokens[token_path] = original_value
                else:
                    modified_tokens[token_path] = {
                        'original': original_value,
                        'converted': converted_value
                    }
            elif original_value and not converted_value:
                lost_tokens[token_path] = original_value
            elif not original_value and converted_value:
                gained_tokens[token_path] = converted_value
        
        # Calculate preservation metrics
        total_original = len(original_tokens)
        preservation_rate = (len(preserved_tokens) / max(total_original, 1)) * 100
        modification_rate = (len(modified_tokens) / max(total_original, 1)) * 100
        loss_rate = (len(lost_tokens) / max(total_original, 1)) * 100
        
        return {
            'original_analysis': original_result,
            'converted_analysis': converted_result,
            'preservation_metrics': {
                'total_original_tokens': total_original,
                'preserved_tokens': len(preserved_tokens),
                'modified_tokens': len(modified_tokens),
                'lost_tokens': len(lost_tokens),
                'gained_tokens': len(gained_tokens),
                'preservation_rate': preservation_rate,
                'modification_rate': modification_rate,
                'loss_rate': loss_rate
            },
            'token_changes': {
                'preserved': preserved_tokens,
                'modified': modified_tokens,
                'lost': lost_tokens,
                'gained': gained_tokens
            }
        }
    
    def get_critical_carrier_survival(self, analysis_result: CarrierAnalysisResult) -> Dict[str, Any]:
        """Get survival metrics for critical carriers only."""
        critical_stats = analysis_result.category_breakdown.get(CarrierCategory.CRITICAL, {})
        
        critical_carriers = [
            dc for dc in analysis_result.detected_carriers 
            if dc[0].category == CarrierCategory.CRITICAL
        ]
        
        critical_missing = [
            mc for mc in analysis_result.missing_carriers 
            if mc.category == CarrierCategory.CRITICAL
        ]
        
        return {
            'detected_count': len(critical_carriers),
            'missing_count': len(critical_missing),
            'survival_rate': critical_stats.get('survival_rate', 0.0),
            'detected_tokens': [
                {
                    'type': dc[0].carrier_type.value,
                    'token_path': dc[0].design_token_path,
                    'value': dc[2],
                    'description': dc[0].description
                }
                for dc in critical_carriers
            ],
            'missing_tokens': [
                {
                    'type': mc.carrier_type.value,
                    'token_path': mc.design_token_path,
                    'description': mc.description
                }
                for mc in critical_missing
            ]
        }
    
    def generate_carrier_report(self, comparison_result: Dict[str, Any]) -> str:
        """Generate human-readable report of carrier analysis."""
        lines = []
        lines.append("StyleStack Design Token Carrier Analysis")
        lines.append("=" * 45)
        lines.append("")
        
        metrics = comparison_result['preservation_metrics']
        lines.append(f"Total Original Tokens: {metrics['total_original_tokens']}")
        lines.append(f"Preservation Rate: {metrics['preservation_rate']:.1f}%")
        lines.append(f"Modification Rate: {metrics['modification_rate']:.1f}%")
        lines.append(f"Loss Rate: {metrics['loss_rate']:.1f}%")
        lines.append("")
        
        # Category breakdown
        original_breakdown = comparison_result['original_analysis'].category_breakdown
        converted_breakdown = comparison_result['converted_analysis'].category_breakdown
        
        lines.append("Category Breakdown:")
        lines.append("-" * 18)
        for category in CarrierCategory:
            orig_stats = original_breakdown.get(category, {})
            conv_stats = converted_breakdown.get(category, {})
            
            lines.append(f"{category.value.title()}:")
            lines.append(f"  Original: {orig_stats.get('detected', 0)}/{orig_stats.get('total', 0)} carriers")
            lines.append(f"  Converted: {conv_stats.get('detected', 0)}/{conv_stats.get('total', 0)} carriers")
            lines.append(f"  Survival: {conv_stats.get('survival_rate', 0):.1f}%")
            lines.append("")
        
        # Critical failures
        critical_failures = comparison_result['converted_analysis'].critical_failures
        if critical_failures:
            lines.append("Critical Failures:")
            lines.append("-" * 17)
            for failure in critical_failures:
                lines.append(f"  • {failure}")
            lines.append("")
        
        return "\n".join(lines)