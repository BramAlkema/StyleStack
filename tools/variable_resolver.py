"""
StyleStack Variable Resolution Engine

Unified resolution system that bridges:
1. Existing 5-layer token system (YAML files) 
2. New OOXML extension variables (embedded in templates)
3. XPath-based OOXML manipulation

Provides comprehensive variable resolution with hierarchy precedence:
Core → Fork → Org → Group → Personal → Channel → Extension Variables

Integrates with existing token_resolver.py while adding OOXML-native capabilities.
"""

import yaml
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field
import xml.etree.ElementTree as ET
import logging

# Import existing components
from token_resolver import TokenResolver
from token_parser import TokenParser, VariableToken, TokenScope, TokenType
from ooxml_extension_manager import OOXMLExtensionManager, StyleStackExtension

logger = logging.getLogger(__name__)


@dataclass
class ResolvedVariable:
    """Represents a fully resolved variable with source tracking"""
    id: str
    value: str
    type: TokenType
    scope: TokenScope
    source: str  # 'yaml_tokens', 'extension_variables', 'computed'
    xpath: Optional[str] = None
    ooxml_mapping: Optional[Dict[str, Any]] = None
    hierarchy_level: int = 0  # Higher = more specific
    dependencies: List[str] = field(default_factory=list)
    
    @property
    def is_ooxml_native(self) -> bool:
        """True if variable has OOXML XPath mapping"""
        return self.xpath is not None
    
    @property
    def precedence_key(self) -> Tuple[int, int]:
        """Key for sorting by precedence (hierarchy_level, scope precedence)"""
        scope_precedence = {
            TokenScope.USER: 5,
            TokenScope.GROUP: 4, 
            TokenScope.ORG: 3,
            TokenScope.FORK: 2,
            TokenScope.CORE: 1,
            TokenScope.THEME: 0
        }
        return (self.hierarchy_level, scope_precedence.get(self.scope, 0))


class VariableResolver:
    """
    Advanced variable resolution engine that unifies YAML tokens with OOXML extension variables.
    
    Features:
    - 5-layer hierarchy resolution (existing + extensions)
    - XPath-based OOXML manipulation
    - Dependency graph resolution
    - Type validation and coercion
    - Performance optimization for large variable sets
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.token_resolver = TokenResolver(verbose=verbose)
        self.token_parser = TokenParser()
        self.extension_manager = OOXMLExtensionManager()
        
        # Resolution caches
        self._yaml_tokens_cache: Dict[str, Dict[str, str]] = {}
        self._extension_variables_cache: Dict[str, List[StyleStackExtension]] = {}
        self._resolved_cache: Dict[str, ResolvedVariable] = {}
        
        # Hierarchy levels for different sources
        self.hierarchy_levels = {
            'core': 1,
            'fork': 2, 
            'org': 3,
            'group': 4,
            'personal': 5,
            'channel': 6,
            'extension_core': 7,
            'extension_fork': 8,
            'extension_org': 9,
            'extension_group': 10,
            'extension_personal': 11,
            'extension_theme': 12  # Highest priority for theme references
        }
    
    def resolve_all_variables(self,
                            fork: Optional[str] = None,
                            org: Optional[str] = None,
                            group: Optional[str] = None, 
                            personal: Optional[str] = None,
                            channel: Optional[str] = None,
                            extension_sources: Optional[List[Union[str, Path]]] = None
                            ) -> Dict[str, ResolvedVariable]:
        """
        Resolve all variables from both YAML tokens and OOXML extensions.
        
        Args:
            fork, org, group, personal, channel: YAML token layers
            extension_sources: OOXML files or XML content with extension variables
            
        Returns:
            Dictionary of resolved variables with precedence applied
        """
        if self.verbose:
            logger.info("🔧 Starting unified variable resolution")
            
        resolved_variables = {}
        
        # 1. Resolve YAML tokens (existing system)
        yaml_variables = self._resolve_yaml_tokens(
            fork=fork, org=org, group=group, personal=personal, channel=channel
        )
        resolved_variables.update(yaml_variables)
        
        # 2. Resolve extension variables (new system) 
        if extension_sources:
            extension_variables = self._resolve_extension_variables(
                extension_sources, org=org, group=group, personal=personal
            )
            resolved_variables.update(extension_variables)
        
        # 3. Apply hierarchy precedence resolution
        final_resolved = self._apply_hierarchy_precedence(resolved_variables)
        
        # 4. Resolve dependencies and references
        final_resolved = self._resolve_dependencies(final_resolved)
        
        if self.verbose:
            logger.info(f"✅ Resolved {len(final_resolved)} variables from {len(resolved_variables)} sources")
            
        return final_resolved
    
    def _resolve_yaml_tokens(self, **layer_args) -> Dict[str, ResolvedVariable]:
        """Resolve variables from existing YAML token system"""
        if self.verbose:
            logger.info("📄 Resolving YAML tokens...")
            
        # Use existing token resolver
        resolved_tokens = self.token_resolver.resolve_tokens(**layer_args)
        
        yaml_variables = {}
        
        for token_path, value in resolved_tokens.items():
            # Parse token path to determine scope and type
            scope, token_type = self._infer_scope_and_type_from_path(token_path)
            hierarchy_level = self._get_hierarchy_level_for_yaml_token(token_path, **layer_args)
            
            variable = ResolvedVariable(
                id=token_path.replace('.', '_'),  # Convert to valid identifier
                value=str(value),
                type=token_type,
                scope=scope,
                source='yaml_tokens',
                hierarchy_level=hierarchy_level
            )
            
            yaml_variables[variable.id] = variable
            
        if self.verbose:
            logger.info(f"   Found {len(yaml_variables)} YAML token variables")
            
        return yaml_variables
    
    def _resolve_extension_variables(self, extension_sources: List[Union[str, Path]], 
                                   **context) -> Dict[str, ResolvedVariable]:
        """Resolve variables from OOXML extension sources"""
        if self.verbose:
            logger.info("🔧 Resolving extension variables...")
            
        extension_variables = {}
        
        for source in extension_sources:
            try:
                if isinstance(source, (str, Path)) and Path(source).suffix in ['.potx', '.dotx', '.xltx']:
                    # OOXML file
                    extensions_by_file = self.extension_manager.read_extensions_from_ooxml_file(source)
                    for file_path, extensions in extensions_by_file.items():
                        for extension in extensions:
                            vars_from_ext = self._process_extension_variables(extension, context)
                            extension_variables.update(vars_from_ext)
                            
                elif isinstance(source, str) and source.startswith('<?xml'):
                    # Raw XML content
                    extensions = self.extension_manager.read_extensions_from_xml(source)
                    for extension in extensions:
                        vars_from_ext = self._process_extension_variables(extension, context)
                        extension_variables.update(vars_from_ext)
                        
            except Exception as e:
                if self.verbose:
                    logger.warning(f"Could not process extension source {source}: {e}")
                continue
                
        if self.verbose:
            logger.info(f"   Found {len(extension_variables)} extension variables")
            
        return extension_variables
    
    def _process_extension_variables(self, extension: StyleStackExtension, 
                                   context: Dict[str, Any]) -> Dict[str, ResolvedVariable]:
        """Process variables from a single extension"""
        variables = {}
        
        for var_data in extension.variables:
            try:
                # Create resolved variable from extension data
                variable_id = var_data.get('id', 'unknown')
                variable_type = TokenType(var_data.get('type', 'text'))
                variable_scope = TokenScope(var_data.get('scope', 'core'))
                
                # Determine hierarchy level based on scope and context
                hierarchy_level = self._get_hierarchy_level_for_extension_variable(
                    variable_scope, context
                )
                
                variable = ResolvedVariable(
                    id=variable_id,
                    value=var_data.get('defaultValue', ''),
                    type=variable_type,
                    scope=variable_scope,
                    source='extension_variables',
                    xpath=var_data.get('xpath'),
                    ooxml_mapping=var_data.get('ooxml'),
                    hierarchy_level=hierarchy_level,
                    dependencies=var_data.get('dependencies', [])
                )
                
                variables[variable_id] = variable
                
            except (ValueError, KeyError) as e:
                if self.verbose:
                    logger.warning(f"Skipping invalid variable in extension: {e}")
                continue
                
        return variables
    
    def _apply_hierarchy_precedence(self, variables: Dict[str, ResolvedVariable]) -> Dict[str, ResolvedVariable]:
        """Apply hierarchy precedence when multiple variables have same ID"""
        if self.verbose:
            logger.info("🏗️ Applying hierarchy precedence...")
            
        # Group variables by ID
        variable_groups = {}
        for var_id, variable in variables.items():
            base_id = variable.id
            if base_id not in variable_groups:
                variable_groups[base_id] = []
            variable_groups[base_id].append(variable)
        
        # Resolve conflicts using precedence
        resolved = {}
        conflicts_resolved = 0
        
        for base_id, variable_list in variable_groups.items():
            if len(variable_list) == 1:
                resolved[base_id] = variable_list[0]
            else:
                # Sort by precedence (highest first)
                sorted_vars = sorted(variable_list, key=lambda v: v.precedence_key, reverse=True)
                resolved[base_id] = sorted_vars[0]
                conflicts_resolved += len(variable_list) - 1
                
                if self.verbose:
                    logger.debug(f"Resolved conflict for '{base_id}': "
                               f"{sorted_vars[0].scope.value} ({sorted_vars[0].source}) wins")
        
        if self.verbose and conflicts_resolved > 0:
            logger.info(f"   Resolved {conflicts_resolved} hierarchy conflicts")
            
        return resolved
    
    def _resolve_dependencies(self, variables: Dict[str, ResolvedVariable]) -> Dict[str, ResolvedVariable]:
        """Resolve variable dependencies and references"""
        if self.verbose:
            logger.info("🔄 Resolving variable dependencies...")
            
        # Build dependency graph
        dependency_graph = {var_id: var.dependencies for var_id, var in variables.items()}
        
        # Topological sort to resolve dependencies
        resolved_order = self._topological_sort(dependency_graph)
        
        # Resolve variables in dependency order
        for var_id in resolved_order:
            if var_id in variables:
                variable = variables[var_id]
                
                # Resolve token references in value
                if '{' in variable.value:
                    resolved_value = self._resolve_token_references_in_value(
                        variable.value, variables
                    )
                    if resolved_value != variable.value:
                        # Create new variable with resolved value
                        variables[var_id] = ResolvedVariable(
                            id=variable.id,
                            value=resolved_value,
                            type=variable.type,
                            scope=variable.scope,
                            source=variable.source,
                            xpath=variable.xpath,
                            ooxml_mapping=variable.ooxml_mapping,
                            hierarchy_level=variable.hierarchy_level,
                            dependencies=variable.dependencies
                        )
        
        return variables
    
    def _topological_sort(self, dependency_graph: Dict[str, List[str]]) -> List[str]:
        """Topological sort for dependency resolution"""
        visited = set()
        temp_visited = set()
        result = []
        
        def visit(node: str):
            if node in temp_visited:
                # Circular dependency detected
                if self.verbose:
                    logger.warning(f"Circular dependency detected involving: {node}")
                return
                
            if node not in visited:
                temp_visited.add(node)
                
                for dependency in dependency_graph.get(node, []):
                    visit(dependency)
                    
                temp_visited.remove(node)
                visited.add(node)
                result.append(node)
        
        for node in dependency_graph:
            if node not in visited:
                visit(node)
        
        return result
    
    def _resolve_token_references_in_value(self, value: str, 
                                         variables: Dict[str, ResolvedVariable]) -> str:
        """Resolve {token.references} in variable values"""
        pattern = r'\{([^}]+)\}'
        
        def replace_reference(match):
            reference = match.group(1)
            
            # Try direct lookup first
            if reference in variables:
                return variables[reference].value
            
            # Try with scope prefix lookup
            for var_id, variable in variables.items():
                if var_id.endswith(reference) or variable.id == reference:
                    return variable.value
            
            # Return original if not found
            if self.verbose:
                logger.warning(f"Unresolved variable reference: {reference}")
            return match.group(0)
        
        return re.sub(pattern, replace_reference, value)
    
    def _infer_scope_and_type_from_path(self, token_path: str) -> Tuple[TokenScope, TokenType]:
        """Infer scope and type from YAML token path"""
        parts = token_path.split('.')
        
        # Infer type from path
        if 'color' in token_path.lower():
            token_type = TokenType.COLOR
        elif 'font' in token_path.lower():
            token_type = TokenType.FONT  
        elif 'size' in token_path.lower() or 'width' in token_path.lower() or 'height' in token_path.lower():
            token_type = TokenType.DIMENSION
        elif any(num_word in token_path.lower() for num_word in ['spacing', 'margin', 'padding']):
            token_type = TokenType.NUMBER
        else:
            token_type = TokenType.TEXT
        
        # Default scope (YAML tokens are typically core-level)
        scope = TokenScope.CORE
        
        return scope, token_type
    
    def _get_hierarchy_level_for_yaml_token(self, token_path: str, **layer_args) -> int:
        """Determine hierarchy level for YAML token based on which layers are active"""
        # Highest active layer determines the level
        if layer_args.get('channel'):
            return self.hierarchy_levels['channel']
        elif layer_args.get('personal'):
            return self.hierarchy_levels['personal']
        elif layer_args.get('group'):
            return self.hierarchy_levels['group']
        elif layer_args.get('org'):
            return self.hierarchy_levels['org']
        elif layer_args.get('fork'):
            return self.hierarchy_levels['fork']
        else:
            return self.hierarchy_levels['core']
    
    def _get_hierarchy_level_for_extension_variable(self, scope: TokenScope, 
                                                   context: Dict[str, Any]) -> int:
        """Determine hierarchy level for extension variable"""
        if scope == TokenScope.THEME:
            return self.hierarchy_levels['extension_theme']
        elif scope == TokenScope.USER:
            return self.hierarchy_levels['extension_personal']
        elif scope == TokenScope.GROUP:
            return self.hierarchy_levels['extension_group']
        elif scope == TokenScope.ORG:
            return self.hierarchy_levels['extension_org']
        elif scope == TokenScope.FORK:
            return self.hierarchy_levels['extension_fork']
        else:
            return self.hierarchy_levels['extension_core']
    
    def apply_variables_to_ooxml(self, xml_content: str, 
                               variables: Dict[str, ResolvedVariable]) -> str:
        """Apply resolved variables to OOXML content using XPath"""
        if self.verbose:
            logger.info("📝 Applying variables to OOXML content...")
            
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML content: {e}")
        
        applied_count = 0
        
        # Apply variables with XPath mappings
        for var_id, variable in variables.items():
            if variable.is_ooxml_native and variable.xpath:
                try:
                    # Find elements using XPath (simplified - full implementation would use lxml)
                    elements = self._find_elements_by_simple_xpath(root, variable.xpath)
                    
                    for element in elements:
                        self._apply_variable_to_element(element, variable)
                        applied_count += 1
                        
                except Exception as e:
                    if self.verbose:
                        logger.warning(f"Could not apply variable {var_id}: {e}")
                    continue
        
        if self.verbose:
            logger.info(f"   Applied {applied_count} variables to OOXML")
            
        return ET.tostring(root, encoding='unicode')
    
    def _find_elements_by_simple_xpath(self, root: ET.Element, xpath: str) -> List[ET.Element]:
        """Simple XPath implementation for common patterns"""
        # This is a simplified version - production would use lxml for full XPath support
        if xpath.startswith('//'):
            # Find all descendants with matching tag
            tag_name = xpath[2:].split('/')[-1].split('[')[0].split('@')[0]
            return root.findall(f'.//{{{root.nsmap[None] if hasattr(root, "nsmap") else "*"}}}{tag_name}')
        else:
            # Simple path
            return root.findall(xpath)
    
    def _apply_variable_to_element(self, element: ET.Element, variable: ResolvedVariable):
        """Apply variable value to XML element"""
        if variable.ooxml_mapping:
            # Use OOXML mapping if available
            mapping = variable.ooxml_mapping
            if 'attribute' in mapping:
                element.set(mapping['attribute'], variable.value)
            elif 'text' in mapping:
                element.text = variable.value
        else:
            # Default application based on type
            if variable.type == TokenType.COLOR:
                # Apply color value to appropriate attributes
                if 'val' in element.attrib:
                    element.set('val', variable.value.lstrip('#'))
                elif 'rgb' in element.attrib:
                    element.set('rgb', variable.value.lstrip('#'))
            elif variable.type == TokenType.FONT:
                # Apply font value
                if 'typeface' in element.attrib:
                    element.set('typeface', variable.value)
            else:
                # Generic application
                if element.text is not None:
                    element.text = variable.value
                elif 'val' in element.attrib:
                    element.set('val', variable.value)
    
    def generate_resolution_report(self, variables: Dict[str, ResolvedVariable]) -> Dict[str, Any]:
        """Generate comprehensive resolution report"""
        # Count by source
        source_counts = {}
        type_counts = {}
        scope_counts = {}
        
        for variable in variables.values():
            source_counts[variable.source] = source_counts.get(variable.source, 0) + 1
            type_counts[variable.type.value] = type_counts.get(variable.type.value, 0) + 1
            scope_counts[variable.scope.value] = scope_counts.get(variable.scope.value, 0) + 1
        
        # Find variables with OOXML mappings
        ooxml_native_count = sum(1 for v in variables.values() if v.is_ooxml_native)
        
        return {
            'summary': {
                'total_variables': len(variables),
                'source_breakdown': source_counts,
                'type_breakdown': type_counts, 
                'scope_breakdown': scope_counts,
                'ooxml_native_variables': ooxml_native_count
            },
            'variables': [
                {
                    'id': v.id,
                    'value': v.value,
                    'type': v.type.value,
                    'scope': v.scope.value,
                    'source': v.source,
                    'hierarchy_level': v.hierarchy_level,
                    'has_xpath': v.xpath is not None,
                    'has_ooxml_mapping': v.ooxml_mapping is not None
                }
                for v in variables.values()
            ]
        }


if __name__ == "__main__":
    # Demo usage
    resolver = VariableResolver(verbose=True)
    
    # Example resolution
    variables = resolver.resolve_all_variables(
        org='acme',
        channel='present'
        # extension_sources=['example.potx']  # Would include OOXML files
    )
    
    print(f"✅ Resolved {len(variables)} variables")
    
    # Generate report
    report = resolver.generate_resolution_report(variables)
    print(f"📊 Resolution Report:")
    print(f"   Total variables: {report['summary']['total_variables']}")
    print(f"   Sources: {report['summary']['source_breakdown']}")
    print(f"   OOXML-native: {report['summary']['ooxml_native_variables']}")