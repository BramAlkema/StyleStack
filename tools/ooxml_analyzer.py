#!/usr/bin/env python3
"""
OOXML Structure Analysis Tool for StyleStack

Analyzes OOXML template structure and identifies potential corruption points.
IMPORTANT: Run with activated venv - this is Brew Python!

Usage:
    source venv/bin/activate
    python tools/ooxml_analyzer.py --template path/to/template.potx --analyze structure
"""


from typing import Any, Dict
import argparse
import sys
import zipfile
import json
from pathlib import Path
import xml.etree.ElementTree as ET

try:
    import lxml.etree as lxml_ET
    from lxml.etree import XMLSyntaxError
    import xmltodict
except ImportError as e:
    print(f"ERROR: Required dependencies not found. Did you activate venv?")
    print(f"Run: source venv/bin/activate")
    print(f"Missing: {e}")
    sys.exit(1)


class OOXMLAnalyzer:
    """Analyzes OOXML template structure for debugging"""
    
    def __init__(self, template_path: str):
        self.template_path = Path(template_path)
        self.format = self.template_path.suffix.lower()
        self.zip_contents = {}
        self.xml_structure = {}
        
    def analyze_structure(self) -> Dict[str, Any]:
        """Analyze complete OOXML structure"""
        print(f"🔍 Analyzing OOXML structure: {self.template_path}")
        
        if not self.template_path.exists():
            return {'error': 'Template file not found'}
            
        analysis = {
            'template': str(self.template_path),
            'format': self.format,
            'zip_contents': self._analyze_zip_contents(),
            'content_types': self._analyze_content_types(),
            'relationships': self._analyze_relationships(),
            'document_structure': self._analyze_document_structure(),
            'extension_variables': self._analyze_extension_variables(),
            'potential_issues': []
        }
        
        return analysis
        
    def _analyze_zip_contents(self) -> Dict[str, Any]:
        """Analyze ZIP archive contents"""
        contents = {
            'total_files': 0,
            'xml_files': [],
            'rels_files': [],
            'media_files': [],
            'other_files': [],
            'directory_structure': {}
        }
        
        try:
            with zipfile.ZipFile(self.template_path, 'r') as zip_file:
                files = zip_file.namelist()
                contents['total_files'] = len(files)
                
                for file in files:
                    if file.endswith('.xml'):
                        contents['xml_files'].append(file)
                    elif file.endswith('.rels'):
                        contents['rels_files'].append(file)
                    elif any(file.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.wmf', '.emf']):
                        contents['media_files'].append(file)
                    else:
                        contents['other_files'].append(file)
                        
                # Build directory structure
                for file in files:
                    parts = file.split('/')
                    current = contents['directory_structure']
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    if parts[-1]:  # Not a directory
                        current[parts[-1]] = 'file'
                        
        except Exception as e:
            contents['error'] = str(e)
            
        return contents
        
    def _analyze_content_types(self) -> Dict[str, Any]:
        """Analyze [Content_Types].xml"""
        content_types = {
            'valid': False,
            'defaults': {},
            'overrides': {},
            'issues': []
        }
        
        try:
            with zipfile.ZipFile(self.template_path, 'r') as zip_file:
                ct_xml = zip_file.read('[Content_Types].xml')
                root = ET.fromstring(ct_xml)
                content_types['valid'] = True
                
                # Parse defaults
                for default in root.findall('.//{http://schemas.openxmlformats.org/package/2006/content-types}Default'):
                    extension = default.get('Extension')
                    content_type = default.get('ContentType')
                    content_types['defaults'][extension] = content_type
                    
                # Parse overrides
                for override in root.findall('.//{http://schemas.openxmlformats.org/package/2006/content-types}Override'):
                    part_name = override.get('PartName')
                    content_type = override.get('ContentType')
                    content_types['overrides'][part_name] = content_type
                    
        except Exception as e:
            content_types['issues'].append(f'Failed to parse: {str(e)}')
            
        return content_types
        
    def _analyze_relationships(self) -> Dict[str, Any]:
        """Analyze relationship files"""
        relationships = {
            'main_rels': {},
            'document_rels': {},
            'issues': []
        }
        
        try:
            with zipfile.ZipFile(self.template_path, 'r') as zip_file:
                # Main relationships
                if '_rels/.rels' in zip_file.namelist():
                    rels_xml = zip_file.read('_rels/.rels')
                    root = ET.fromstring(rels_xml)
                    
                    for rel in root.findall('.//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'):
                        rel_id = rel.get('Id')
                        rel_type = rel.get('Type')
                        target = rel.get('Target')
                        relationships['main_rels'][rel_id] = {
                            'type': rel_type,
                            'target': target
                        }
                        
                # Document-specific relationships
                rels_files = [f for f in zip_file.namelist() if f.endswith('.rels') and f != '_rels/.rels']
                for rels_file in rels_files:
                    try:
                        rels_xml = zip_file.read(rels_file)
                        root = ET.fromstring(rels_xml)
                        
                        file_rels = {}
                        for rel in root.findall('.//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'):
                            rel_id = rel.get('Id')
                            rel_type = rel.get('Type')
                            target = rel.get('Target')
                            file_rels[rel_id] = {
                                'type': rel_type,
                                'target': target
                            }
                            
                        relationships['document_rels'][rels_file] = file_rels
                        
                    except Exception as e:
                        relationships['issues'].append(f'Failed to parse {rels_file}: {str(e)}')
                        
        except Exception as e:
            relationships['issues'].append(f'Failed to analyze relationships: {str(e)}')
            
        return relationships
        
    def _analyze_document_structure(self) -> Dict[str, Any]:
        """Analyze document-specific structure"""
        structure = {
            'main_document': None,
            'styles': {},
            'themes': {},
            'custom_xml': [],
            'issues': []
        }
        
        try:
            with zipfile.ZipFile(self.template_path, 'r') as zip_file:
                files = zip_file.namelist()
                
                # Find main document file based on format
                main_files = {
                    '.docx': 'word/document.xml',
                    '.dotx': 'word/document.xml',
                    '.xlsx': 'xl/workbook.xml',
                    '.xltx': 'xl/workbook.xml',
                    '.pptx': 'ppt/presentation.xml',
                    '.potx': 'ppt/presentation.xml'
                }
                
                main_file = main_files.get(self.format)
                if main_file and main_file in files:
                    structure['main_document'] = main_file
                    
                    # Analyze main document
                    try:
                        doc_xml = zip_file.read(main_file)
                        # Convert to dict for easier analysis
                        doc_dict = xmltodict.parse(doc_xml)
                        structure['main_document_structure'] = self._summarize_xml_structure(doc_dict)
                    except Exception as e:
                        structure['issues'].append(f'Failed to parse main document: {str(e)}')
                        
                # Find styles
                style_files = [f for f in files if 'styles' in f.lower() and f.endswith('.xml')]
                for style_file in style_files:
                    try:
                        styles_xml = zip_file.read(style_file)
                        styles_dict = xmltodict.parse(styles_xml)
                        structure['styles'][style_file] = self._summarize_xml_structure(styles_dict)
                    except Exception as e:
                        structure['issues'].append(f'Failed to parse {style_file}: {str(e)}')
                        
                # Find themes
                theme_files = [f for f in files if 'theme' in f.lower() and f.endswith('.xml')]
                for theme_file in theme_files:
                    try:
                        theme_xml = zip_file.read(theme_file)
                        theme_dict = xmltodict.parse(theme_xml)
                        structure['themes'][theme_file] = self._summarize_xml_structure(theme_dict)
                    except Exception as e:
                        structure['issues'].append(f'Failed to parse {theme_file}: {str(e)}')
                        
                # Find custom XML
                structure['custom_xml'] = [f for f in files if 'customXml' in f]
                
        except Exception as e:
            structure['issues'].append(f'Failed to analyze document structure: {str(e)}')
            
        return structure
        
    def _analyze_extension_variables(self) -> Dict[str, Any]:
        """Analyze extension variables and StyleStack customizations"""
        variables = {
            'files_with_variables': [],
            'variable_definitions': {},
            'substitution_patterns': [],
            'issues': []
        }
        
        try:
            with zipfile.ZipFile(self.template_path, 'r') as zip_file:
                files = zip_file.namelist()
                
                # Look for StyleStack-specific files
                stylestack_files = [f for f in files if 'stylestack' in f.lower() or 'extensionvariables' in f.lower()]
                variables['stylestack_files'] = stylestack_files
                
                # Search all XML files for variables
                xml_files = [f for f in files if f.endswith('.xml')]
                
                for xml_file in xml_files:
                    try:
                        content = zip_file.read(xml_file).decode('utf-8')
                        
                        # Look for variable patterns
                        import re
                        
                        # StyleStack variable patterns
                        patterns = [
                            r'\{([^}]+)\}',  # {variable}
                            r'stylestack[._-](\w+)',  # stylestack.variable
                            r'extensionvariables',  # extension variables
                        ]
                        
                        found_variables = []
                        for pattern in patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            found_variables.extend(matches)
                            
                        if found_variables:
                            variables['files_with_variables'].append(xml_file)
                            variables['variable_definitions'][xml_file] = list(set(found_variables))
                            
                        # Look for substitution patterns that might cause corruption
                        corruption_patterns = [
                            r'&lt;[^&]*&gt;',  # Escaped XML
                            r'&amp;[^;]*;',   # Double-escaped entities
                            r'xmlns:\w*=""',   # Empty namespace declarations
                        ]
                        
                        for pattern in corruption_patterns:
                            matches = re.findall(pattern, content)
                            if matches:
                                variables['substitution_patterns'].extend([
                                    {'file': xml_file, 'pattern': pattern, 'matches': matches[:5]}  # Limit to first 5
                                ])
                                
                    except Exception as e:
                        variables['issues'].append(f'Failed to analyze {xml_file}: {str(e)}')
                        
        except Exception as e:
            variables['issues'].append(f'Failed to analyze extension variables: {str(e)}')
            
        return variables
        
    def _summarize_xml_structure(self, xml_dict: Dict[str, Any], max_depth: int = 3) -> Dict[str, Any]:
        """Summarize XML structure without full content"""
        def summarize_recursive(obj, depth=0):
            if depth >= max_depth:
                return "..."
                
            if isinstance(obj, dict):
                result = {}
                for key, value in obj.items():
                    if key.startswith('@'):  # Attributes
                        result[key] = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                    else:
                        result[key] = summarize_recursive(value, depth + 1)
                return result
            elif isinstance(obj, list):
                if len(obj) > 3:
                    return [summarize_recursive(obj[0], depth + 1), "...", f"({len(obj)} items total)"]
                else:
                    return [summarize_recursive(item, depth + 1) for item in obj]
            else:
                # Truncate long strings
                str_val = str(obj)
                return str_val[:100] + "..." if len(str_val) > 100 else str_val
                
        return summarize_recursive(xml_dict)
        
    def compare_before_after(self, original_path: str, processed_path: str) -> Dict[str, Any]:
        """Compare template before and after processing"""
        print(f"🔄 Comparing templates:")
        print(f"   Original: {original_path}")
        print(f"   Processed: {processed_path}")
        
        original_analyzer = OOXMLAnalyzer(original_path)
        processed_analyzer = OOXMLAnalyzer(processed_path)
        
        original_analysis = original_analyzer.analyze_structure()
        processed_analysis = processed_analyzer.analyze_structure()
        
        comparison = {
            'original': original_analysis,
            'processed': processed_analysis,
            'differences': self._find_differences(original_analysis, processed_analysis)
        }
        
        return comparison
        
    def _find_differences(self, original: Dict[str, Any], processed: Dict[str, Any]) -> Dict[str, Any]:
        """Find differences between original and processed templates"""
        differences = {
            'file_count_changed': False,
            'new_files': [],
            'removed_files': [],
            'modified_files': [],
            'structure_changes': []
        }
        
        # Compare file counts
        orig_files = set(original.get('zip_contents', {}).get('xml_files', []))
        proc_files = set(processed.get('zip_contents', {}).get('xml_files', []))
        
        differences['new_files'] = list(proc_files - orig_files)
        differences['removed_files'] = list(orig_files - proc_files)
        differences['file_count_changed'] = len(differences['new_files']) > 0 or len(differences['removed_files']) > 0
        
        # Compare variable presence
        orig_vars = original.get('extension_variables', {}).get('files_with_variables', [])
        proc_vars = processed.get('extension_variables', {}).get('files_with_variables', [])
        
        if set(orig_vars) != set(proc_vars):
            differences['structure_changes'].append({
                'type': 'variable_files_changed',
                'original': orig_vars,
                'processed': proc_vars
            })
            
        return differences
        
    def print_analysis(self, analysis: Dict[str, Any]):
        """Print detailed analysis"""
        print("\n" + "="*60)
        print("🔍 OOXML STRUCTURE ANALYSIS")
        print("="*60)
        
        # ZIP contents
        zip_contents = analysis.get('zip_contents', {})
        print(f"\n📦 ZIP Archive:")
        print(f"   Total files: {zip_contents.get('total_files', 0)}")
        print(f"   XML files: {len(zip_contents.get('xml_files', []))}")
        print(f"   Relationship files: {len(zip_contents.get('rels_files', []))}")
        print(f"   Media files: {len(zip_contents.get('media_files', []))}")
        
        # Content types
        content_types = analysis.get('content_types', {})
        print(f"\n📄 Content Types:")
        print(f"   Valid: {content_types.get('valid', False)}")
        print(f"   Default types: {len(content_types.get('defaults', {}))}")
        print(f"   Override types: {len(content_types.get('overrides', {}))}")
        
        # Document structure
        doc_structure = analysis.get('document_structure', {})
        print(f"\n📋 Document Structure:")
        print(f"   Main document: {doc_structure.get('main_document', 'Not found')}")
        print(f"   Style files: {len(doc_structure.get('styles', {}))}")
        print(f"   Theme files: {len(doc_structure.get('themes', {}))}")
        print(f"   Custom XML: {len(doc_structure.get('custom_xml', []))}")
        
        # Extension variables
        ext_vars = analysis.get('extension_variables', {})
        print(f"\n🔧 Extension Variables:")
        print(f"   Files with variables: {len(ext_vars.get('files_with_variables', []))}")
        if ext_vars.get('files_with_variables'):
            for file in ext_vars['files_with_variables']:
                var_count = len(ext_vars.get('variable_definitions', {}).get(file, []))
                print(f"     {file}: {var_count} variables")
                
        # Issues
        all_issues = []
        for section in ['content_types', 'relationships', 'document_structure', 'extension_variables']:
            section_data = analysis.get(section, {})
            all_issues.extend(section_data.get('issues', []))
            
        if all_issues:
            print(f"\n⚠️  Issues Found: {len(all_issues)}")
            for issue in all_issues:
                print(f"     {issue}")
                
        print("\n" + "="*60)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='Analyze OOXML template structure')
    parser.add_argument('--template', '-t', required=True,
                       help='Path to template file')
    parser.add_argument('--analyze', choices=['structure', 'compare'], default='structure',
                       help='Analysis type')
    parser.add_argument('--compare-with', help='Second template for comparison')
    parser.add_argument('--output', '-o', help='Output JSON file for results')
    
    args = parser.parse_args()
    
    print("🔍 StyleStack OOXML Analyzer")
    print("⚠️  IMPORTANT: Ensure venv is activated (source venv/bin/activate)")
    print()
    
    analyzer = OOXMLAnalyzer(args.template)
    
    if args.analyze == 'structure':
        analysis = analyzer.analyze_structure()
        analyzer.print_analysis(analysis)
    elif args.analyze == 'compare' and args.compare_with:
        comparison = analyzer.compare_before_after(args.template, args.compare_with)
        analyzer.print_analysis(comparison['original'])
        print("\n" + "🔄 COMPARISON RESULTS" + "\n")
        # TODO: Implement comparison printing
        
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"\n💾 Results saved to {args.output}")


if __name__ == '__main__':
    main()