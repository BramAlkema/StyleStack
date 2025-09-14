"""OOXML package extraction and XML part isolation."""

import zipfile
from pathlib import Path
from typing import Dict
from ..core.exceptions import AnalysisError


class PackageExtractor:
    """Extracts and processes OOXML package contents."""
    
    def extract_package(self, ooxml_file: Path) -> Dict[str, bytes]:
        """
        Extract all parts from an OOXML package.
        
        Args:
            ooxml_file: Path to OOXML file (.docx, .pptx, .xlsx)
            
        Returns:
            Dictionary mapping part names to their binary content
            
        Raises:
            AnalysisError: If file cannot be processed
        """
        if not ooxml_file.exists():
            raise AnalysisError(f"File does not exist: {ooxml_file}")
        
        try:
            with zipfile.ZipFile(ooxml_file, 'r') as zf:
                parts = {}
                for name in zf.namelist():
                    try:
                        parts[name] = zf.read(name)
                    except Exception as e:
                        # Skip problematic parts but continue
                        continue
                return parts
        except zipfile.BadZipFile:
            raise AnalysisError(f"Invalid OOXML package: {ooxml_file}")
        except Exception as e:
            raise AnalysisError(f"Failed to extract package: {e}")
    
    def filter_xml_parts(self, parts: Dict[str, bytes]) -> Dict[str, bytes]:
        """
        Filter only XML parts from extracted package.
        
        Args:
            parts: Dictionary of all package parts
            
        Returns:
            Dictionary containing only XML parts
        """
        xml_parts = {}
        
        for name, content in parts.items():
            # Check if it's an XML file by extension or content
            if (name.endswith('.xml') or 
                name.endswith('.rels') or
                self._is_xml_content(content)):
                xml_parts[name] = content
        
        return xml_parts
    
    def _is_xml_content(self, content: bytes) -> bool:
        """
        Check if content appears to be XML.
        
        Args:
            content: Binary content to check
            
        Returns:
            True if content appears to be XML
        """
        try:
            # Check for XML declaration or opening tag
            text = content.decode('utf-8', errors='ignore')[:100]
            return (text.strip().startswith('<?xml') or 
                   text.strip().startswith('<'))
        except:
            return False
    
    def get_core_xml_parts(self, parts: Dict[str, bytes], 
                          document_type: str) -> Dict[str, bytes]:
        """
        Get core XML parts for specific document type.
        
        Args:
            parts: All extracted parts
            document_type: Type of document ('word', 'powerpoint', 'excel')
            
        Returns:
            Dictionary of core XML parts for the document type
        """
        core_parts = {}
        xml_parts = self.filter_xml_parts(parts)
        
        if document_type.lower() == 'word':
            core_patterns = [
                'word/document.xml',
                'word/styles.xml',
                'word/numbering.xml',
                'word/theme/',
                'word/fontTable.xml'
            ]
        elif document_type.lower() == 'powerpoint':
            core_patterns = [
                'ppt/presentation.xml',
                'ppt/slides/',
                'ppt/slideLayouts/',
                'ppt/slideMasters/',
                'ppt/theme/'
            ]
        elif document_type.lower() == 'excel':
            core_patterns = [
                'xl/workbook.xml',
                'xl/styles.xml',
                'xl/worksheets/',
                'xl/theme/'
            ]
        else:
            # Return all XML parts if type unknown
            return xml_parts
        
        # Filter parts based on patterns
        for part_name, content in xml_parts.items():
            for pattern in core_patterns:
                if part_name.startswith(pattern):
                    core_parts[part_name] = content
                    break
        
        # Always include content types and relationships
        for part_name, content in xml_parts.items():
            if ('[Content_Types].xml' in part_name or 
                '.rels' in part_name):
                core_parts[part_name] = content
        
        return core_parts