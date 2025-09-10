"""
Token Integration and Cross-Format Compatibility

This module provides token integration capabilities and cross-format
compatibility checks for multi-format OOXML processing.
"""


from typing import Any, Dict, List, Tuple
import logging
from pathlib import Path

from .types import OOXMLFormat


logger = logging.getLogger(__name__)


class TokenIntegrationManager:
    """
    Manages token integration across different OOXML formats.
    
    Provides unified token resolution and format-specific token
    handling for cross-format compatibility.
    """
    
    def __init__(self):
        self.format_tokens = {}
        self.token_mappings = {}
        
        # Initialize format-specific token handlers
        self._initialize_format_tokens()
    
    def register_format_tokens(self, format_type: OOXMLFormat, 
                              variables: Dict[str, Any], 
                              metadata: Dict[str, Any]):
        """Register format-specific tokens."""
        format_tokens = {}
        
        # Extract format-specific tokens based on format type
        if format_type == OOXMLFormat.POWERPOINT:
            format_tokens.update(self._extract_powerpoint_tokens(variables, metadata))
        elif format_type == OOXMLFormat.WORD:
            format_tokens.update(self._extract_word_tokens(variables, metadata))
        elif format_type == OOXMLFormat.EXCEL:
            format_tokens.update(self._extract_excel_tokens(variables, metadata))
        
        self.format_tokens[format_type] = format_tokens
        
        logger.debug(f"Registered {len(format_tokens)} tokens for {format_type.value}")
    
    def resolve_cross_format_tokens(self, source_format: OOXMLFormat, 
                                   target_format: OOXMLFormat,
                                   tokens: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve tokens for cross-format compatibility."""
        if source_format == target_format:
            return tokens
        
        resolved_tokens = {}
        
        # Get format-specific mappings
        mapping_key = f"{source_format.value}_to_{target_format.value}"
        mappings = self.token_mappings.get(mapping_key, {})
        
        for token_name, token_value in tokens.items():
            # Check if there's a specific mapping
            if token_name in mappings:
                mapped_name = mappings[token_name]
                resolved_tokens[mapped_name] = self._convert_token_value(
                    token_value, source_format, target_format
                )
            else:
                # Use default mapping logic
                resolved_tokens[token_name] = self._convert_token_value(
                    token_value, source_format, target_format
                )
        
        return resolved_tokens
    
    def _initialize_format_tokens(self):
        """Initialize format-specific token configurations."""
        # PowerPoint to Word mappings
        self.token_mappings['potx_to_dotx'] = {
            'slide_background': 'page_background',
            'title_font': 'heading1_font',
            'subtitle_font': 'heading2_font',
            'body_font': 'normal_font'
        }
        
        # Word to PowerPoint mappings
        self.token_mappings['dotx_to_potx'] = {
            'page_background': 'slide_background',
            'heading1_font': 'title_font',
            'heading2_font': 'subtitle_font',
            'normal_font': 'body_font'
        }
        
        # PowerPoint to Excel mappings
        self.token_mappings['potx_to_xltx'] = {
            'slide_background': 'sheet_background',
            'title_font': 'header_font',
            'body_font': 'cell_font'
        }
        
        # Excel to PowerPoint mappings
        self.token_mappings['xltx_to_potx'] = {
            'sheet_background': 'slide_background',
            'header_font': 'title_font',
            'cell_font': 'body_font'
        }
        
        # Word to Excel mappings
        self.token_mappings['dotx_to_xltx'] = {
            'page_background': 'sheet_background',
            'heading1_font': 'header_font',
            'normal_font': 'cell_font'
        }
        
        # Excel to Word mappings
        self.token_mappings['xltx_to_dotx'] = {
            'sheet_background': 'page_background',
            'header_font': 'heading1_font',
            'cell_font': 'normal_font'
        }
    
    def _extract_powerpoint_tokens(self, variables: Dict[str, Any], 
                                  metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract PowerPoint-specific tokens."""
        tokens = {}
        
        # Common PowerPoint tokens
        powerpoint_keys = [
            'slide_background', 'title_font', 'subtitle_font', 'body_font',
            'accent_color', 'slide_layout', 'master_slide'
        ]
        
        for key in powerpoint_keys:
            if key in variables:
                tokens[key] = variables[key]
        
        # Extract from metadata
        if 'powerpoint' in metadata:
            tokens.update(metadata['powerpoint'])
        
        return tokens
    
    def _extract_word_tokens(self, variables: Dict[str, Any], 
                            metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract Word-specific tokens."""
        tokens = {}
        
        # Common Word tokens
        word_keys = [
            'page_background', 'heading1_font', 'heading2_font', 'normal_font',
            'page_margins', 'document_style', 'paragraph_spacing'
        ]
        
        for key in word_keys:
            if key in variables:
                tokens[key] = variables[key]
        
        # Extract from metadata
        if 'word' in metadata:
            tokens.update(metadata['word'])
        
        return tokens
    
    def _extract_excel_tokens(self, variables: Dict[str, Any], 
                             metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract Excel-specific tokens."""
        tokens = {}
        
        # Common Excel tokens
        excel_keys = [
            'sheet_background', 'header_font', 'cell_font', 'grid_lines',
            'column_width', 'row_height', 'chart_style'
        ]
        
        for key in excel_keys:
            if key in variables:
                tokens[key] = variables[key]
        
        # Extract from metadata
        if 'excel' in metadata:
            tokens.update(metadata['excel'])
        
        return tokens
    
    def _convert_token_value(self, value: Any, source_format: OOXMLFormat, 
                           target_format: OOXMLFormat) -> Any:
        """Convert token value between formats."""
        # Color conversion
        if isinstance(value, str) and (value.startswith('#') or value.startswith('rgb')):
            return self._convert_color_value(value, source_format, target_format)
        
        # Font conversion
        if isinstance(value, dict) and 'font_family' in value:
            return self._convert_font_value(value, source_format, target_format)
        
        # Dimension conversion
        if isinstance(value, str) and any(unit in value for unit in ['pt', 'px', 'in', 'cm']):
            return self._convert_dimension_value(value, source_format, target_format)
        
        # Default: return as-is
        return value
    
    def _convert_color_value(self, color: str, source_format: OOXMLFormat, 
                           target_format: OOXMLFormat) -> str:
        """Convert color values between formats."""
        # Different formats may prefer different color representations
        if target_format == OOXMLFormat.EXCEL:
            # Excel prefers RGB values
            if color.startswith('#'):
                return f"rgb{tuple(int(color[i:i+2], 16) for i in (1, 3, 5))}"
        
        elif target_format in [OOXMLFormat.POWERPOINT, OOXMLFormat.WORD]:
            # PowerPoint and Word prefer hex values
            if color.startswith('rgb'):
                # Convert RGB to hex (simplified)
                return color  # Would implement proper RGB to hex conversion
        
        return color
    
    def _convert_font_value(self, font_data: Dict[str, Any], source_format: OOXMLFormat, 
                          target_format: OOXMLFormat) -> Dict[str, Any]:
        """Convert font values between formats."""
        converted = dict(font_data)
        
        # Format-specific font size adjustments
        if 'font_size' in converted:
            if source_format == OOXMLFormat.POWERPOINT and target_format == OOXMLFormat.WORD:
                # PowerPoint often uses larger fonts
                converted['font_size'] = str(int(float(converted['font_size']) * 0.9))
            elif source_format == OOXMLFormat.WORD and target_format == OOXMLFormat.POWERPOINT:
                # Scale up for PowerPoint
                converted['font_size'] = str(int(float(converted['font_size']) * 1.1))
        
        return converted
    
    def _convert_dimension_value(self, dimension: str, source_format: OOXMLFormat, 
                               target_format: OOXMLFormat) -> str:
        """Convert dimension values between formats."""
        # Different formats may prefer different units
        if 'pt' in dimension and target_format == OOXMLFormat.EXCEL:
            # Excel often prefers pixels
            pt_value = float(dimension.replace('pt', ''))
            px_value = pt_value * 1.33  # Approximate conversion
            return f"{px_value:.1f}px"
        
        elif 'px' in dimension and target_format in [OOXMLFormat.POWERPOINT, OOXMLFormat.WORD]:
            # PowerPoint/Word prefer points
            px_value = float(dimension.replace('px', ''))
            pt_value = px_value * 0.75  # Approximate conversion
            return f"{pt_value:.1f}pt"
        
        return dimension
    
    def get_format_tokens(self, format_type: OOXMLFormat) -> Dict[str, Any]:
        """Get registered tokens for a specific format."""
        return self.format_tokens.get(format_type, {})
    
    def get_all_tokens(self) -> Dict[OOXMLFormat, Dict[str, Any]]:
        """Get all registered format tokens."""
        return dict(self.format_tokens)


class CompatibilityMatrix:
    """
    Manages compatibility information between different OOXML formats.
    
    Provides compatibility checks and recommendations for cross-format
    operations and token usage.
    """
    
    def __init__(self):
        self.compatibility_data = self._build_compatibility_matrix()
    
    def _build_compatibility_matrix(self) -> Dict[Tuple[OOXMLFormat, OOXMLFormat], Dict[str, Any]]:
        """Build the compatibility matrix between formats."""
        matrix = {}
        
        # PowerPoint <-> Word compatibility
        matrix[(OOXMLFormat.POWERPOINT, OOXMLFormat.WORD)] = {
            'compatibility_score': 0.8,  # 80% compatible
            'common_features': ['fonts', 'colors', 'themes', 'text_formatting'],
            'incompatible_features': ['slide_transitions', 'animations', 'slide_layouts'],
            'conversion_notes': 'Slide content can be converted to document sections'
        }
        
        matrix[(OOXMLFormat.WORD, OOXMLFormat.POWERPOINT)] = {
            'compatibility_score': 0.7,  # 70% compatible
            'common_features': ['fonts', 'colors', 'themes', 'text_formatting'],
            'incompatible_features': ['page_breaks', 'headers_footers', 'table_of_contents'],
            'conversion_notes': 'Document sections can be converted to slides'
        }
        
        # PowerPoint <-> Excel compatibility
        matrix[(OOXMLFormat.POWERPOINT, OOXMLFormat.EXCEL)] = {
            'compatibility_score': 0.6,  # 60% compatible
            'common_features': ['colors', 'themes', 'charts'],
            'incompatible_features': ['slide_layouts', 'animations', 'text_formatting'],
            'conversion_notes': 'Charts and themes transfer well, text formatting may be lost'
        }
        
        matrix[(OOXMLFormat.EXCEL, OOXMLFormat.POWERPOINT)] = {
            'compatibility_score': 0.6,  # 60% compatible
            'common_features': ['colors', 'themes', 'charts'],
            'incompatible_features': ['cell_formatting', 'formulas', 'data_validation'],
            'conversion_notes': 'Data visualization elements transfer well'
        }
        
        # Word <-> Excel compatibility
        matrix[(OOXMLFormat.WORD, OOXMLFormat.EXCEL)] = {
            'compatibility_score': 0.5,  # 50% compatible
            'common_features': ['fonts', 'colors', 'themes'],
            'incompatible_features': ['paragraphs', 'page_layout', 'document_structure'],
            'conversion_notes': 'Limited compatibility, mainly theme and color information'
        }
        
        matrix[(OOXMLFormat.EXCEL, OOXMLFormat.WORD)] = {
            'compatibility_score': 0.5,  # 50% compatible
            'common_features': ['fonts', 'colors', 'themes'],
            'incompatible_features': ['cell_structure', 'formulas', 'worksheets'],
            'conversion_notes': 'Limited compatibility, mainly theme and color information'
        }
        
        return matrix
    
    def get_compatibility_info(self, source_format: OOXMLFormat, 
                              target_format: OOXMLFormat) -> Dict[str, Any]:
        """Get compatibility information between two formats."""
        if source_format == target_format:
            return {
                'compatibility_score': 1.0,
                'common_features': ['all'],
                'incompatible_features': [],
                'conversion_notes': 'Same format - fully compatible'
            }
        
        return self.compatibility_data.get((source_format, target_format), {
            'compatibility_score': 0.0,
            'common_features': [],
            'incompatible_features': ['all'],
            'conversion_notes': 'No compatibility information available'
        })
    
    def is_compatible(self, source_format: OOXMLFormat, target_format: OOXMLFormat,
                     threshold: float = 0.5) -> bool:
        """Check if formats are compatible above a threshold."""
        info = self.get_compatibility_info(source_format, target_format)
        return info.get('compatibility_score', 0.0) >= threshold
    
    def get_compatible_formats(self, source_format: OOXMLFormat, 
                              threshold: float = 0.5) -> List[OOXMLFormat]:
        """Get list of compatible formats for a source format."""
        compatible = []
        
        for target_format in OOXMLFormat:
            if self.is_compatible(source_format, target_format, threshold):
                compatible.append(target_format)
        
        return compatible
    
    def get_conversion_recommendations(self, source_format: OOXMLFormat, 
                                     target_format: OOXMLFormat) -> List[str]:
        """Get recommendations for format conversion."""
        info = self.get_compatibility_info(source_format, target_format)
        
        recommendations = []
        
        # Add general recommendations based on compatibility score
        score = info.get('compatibility_score', 0.0)
        if score >= 0.8:
            recommendations.append("High compatibility - conversion should work well")
        elif score >= 0.6:
            recommendations.append("Medium compatibility - some features may not transfer")
        elif score >= 0.4:
            recommendations.append("Low compatibility - significant feature loss expected")
        else:
            recommendations.append("Very low compatibility - conversion not recommended")
        
        # Add specific feature recommendations
        common_features = info.get('common_features', [])
        if common_features:
            recommendations.append(f"Compatible features: {', '.join(common_features)}")
        
        incompatible_features = info.get('incompatible_features', [])
        if incompatible_features:
            recommendations.append(f"Incompatible features: {', '.join(incompatible_features)}")
        
        # Add conversion notes
        notes = info.get('conversion_notes')
        if notes:
            recommendations.append(f"Notes: {notes}")
        
        return recommendations