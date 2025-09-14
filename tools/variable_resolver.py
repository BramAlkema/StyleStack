"""
StyleStack Variable Resolution Engine

Unified resolution system that bridges:
1. Existing 5-layer token system (JSON files) 
2. New OOXML extension variables (embedded in templates)
3. XPath-based OOXML manipulation

Provides comprehensive variable resolution with hierarchy precedence:
Core → Fork → Org → Group → Personal → Channel → Extension Variables

Integrates with existing token_resolver.py while adding OOXML-native capabilities.
"""


from typing import Dict, Any, List, Optional, Union, Tuple
import re
from pathlib import Path
from dataclasses import dataclass, field
import xml.etree.ElementTree as ET
import hashlib
import time

from tools.token_parser import TokenType, TokenScope, TokenParser
import logging

# Import existing components
from tools.token_resolver import TokenResolver
from tools.ooxml_extension_manager import OOXMLExtensionManager, StyleStackExtension
from tools.aspect_ratio_resolver import AspectRatioResolver, AspectRatioTokenError

logger = logging.getLogger(__name__)


class CircularReferenceError(Exception):
    """Exception raised when circular references are detected in nested resolution"""
    pass


@dataclass
class ResolvedVariable:
    """Represents a fully resolved variable with source tracking"""
    id: str
    value: str
    type: TokenType
    scope: TokenScope
    source: str  # 'json_tokens', 'extension_variables', 'computed'
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
    Advanced variable resolution engine that unifies JSON tokens with OOXML extension variables.
    
    Features:
    - 5-layer hierarchy resolution (existing + extensions)
    - XPath-based OOXML manipulation
    - Dependency graph resolution
    - Type validation and coercion
    - Performance optimization for large variable sets
    """
    
    def __init__(self, verbose: bool = False, enable_cache: bool = True, strict_mode: bool = True):
        self.verbose = verbose
        self.enable_cache = enable_cache
        self.strict_mode = strict_mode
        self.token_resolver = TokenResolver(verbose=verbose)
        self.token_parser = TokenParser()
        self.extension_manager = OOXMLExtensionManager()
        self.aspect_ratio_resolver = AspectRatioResolver(verbose=verbose, enable_cache=enable_cache)
        
        # Resolution caches
        self._json_tokens_cache: Dict[str, Dict[str, str]] = {}
        self._extension_variables_cache: Dict[str, List[StyleStackExtension]] = {}
        self._resolved_cache: Dict[str, ResolvedVariable] = {}
        
        # Nested reference resolution
        self._nested_resolution_cache: Dict[str, str] = {}
        self._resolution_depth_limit = 5
        self._max_cache_size = 1000
        
        # Regex patterns for nested reference detection
        self._nested_reference_regex = re.compile(
            r'\{([a-zA-Z][a-zA-Z0-9._]*|\s*)\.\{([a-zA-Z][a-zA-Z0-9._]*|\s*)\}\.([a-zA-Z][a-zA-Z0-9._]*|\s*)\}'
        )
        self._multi_nested_regex = re.compile(
            r'\{([a-zA-Z][a-zA-Z0-9._]*|\s*)\.\{([a-zA-Z][a-zA-Z0-9._]*|\s*)\}\.\{([a-zA-Z][a-zA-Z0-9._]*|\s*)\}\.([a-zA-Z][a-zA-Z0-9._]*|\s*)\}'
        )
        
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
                            extension_sources: Optional[List[Union[str, Path]]] = None,
                            context: Optional[Dict[str, Any]] = None
                            ) -> Dict[str, ResolvedVariable]:
        """
        Resolve all variables from both JSON tokens and OOXML extensions.
        
        Args:
            fork, org, group, personal, channel: JSON token layers
            extension_sources: OOXML files or XML content with extension variables
            context: Additional context including aspect ratio, design variant, etc.
            
        Returns:
            Dictionary of resolved variables with precedence applied
        """
        if self.verbose:
            logger.info("🔧 Starting unified variable resolution")
            
        resolved_variables = {}
        
        # 1. Resolve JSON tokens (existing system)
        json_variables = self._resolve_json_tokens(
            fork=fork, org=org, group=group, personal=personal, channel=channel
        )
        resolved_variables.update(json_variables)
        
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
    
    def _resolve_json_tokens(self, **layer_args) -> Dict[str, ResolvedVariable]:
        """Resolve variables from existing JSON token system"""
        if self.verbose:
            logger.info("📄 Resolving JSON tokens...")
            
        # Use existing token resolver
        resolved_tokens = self.token_resolver.resolve_tokens(**layer_args)
        
        json_variables = {}
        
        for token_path, value in resolved_tokens.items():
            # Parse token path to determine scope and type
            scope, token_type = self._infer_scope_and_type_from_path(token_path)
            hierarchy_level = self._get_hierarchy_level_for_json_token(token_path, **layer_args)
            
            variable = ResolvedVariable(
                id=token_path.replace('.', '_'),  # Convert to valid identifier
                value=str(value),
                type=token_type,
                scope=scope,
                source='json_tokens',
                hierarchy_level=hierarchy_level
            )
            
            json_variables[variable.id] = variable
            
        if self.verbose:
            logger.info(f"   Found {len(json_variables)} JSON token variables")
            
        return json_variables
    
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
        """Infer scope and type from JSON token path"""
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
        
        # Default scope (JSON tokens are typically core-level)
        scope = TokenScope.CORE
        
        return scope, token_type
    
    def _get_hierarchy_level_for_json_token(self, token_path: str, **layer_args) -> int:
        """Determine hierarchy level for JSON token based on which layers are active"""
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

    # ========================================================================
    # Nested Reference Resolution Methods
    # ========================================================================

    def _is_nested_reference(self, pattern: str) -> bool:
        """Check if a pattern contains nested references like {color.{theme}.primary}"""
        return bool(self._nested_reference_regex.search(pattern) or 
                   self._multi_nested_regex.search(pattern))

    def _parse_nested_reference(self, pattern: str) -> Dict[str, str]:
        """Parse nested reference pattern into its components"""
        # Try multi-nested pattern first
        multi_match = self._multi_nested_regex.match(pattern)
        if multi_match:
            return {
                'base': multi_match.group(1),
                'dynamic': multi_match.group(2),
                'nested_dynamic': multi_match.group(3),
                'property': multi_match.group(4),
                'full_pattern': pattern
            }
        
        # Try basic nested pattern
        basic_match = self._nested_reference_regex.match(pattern)
        if basic_match:
            return {
                'base': basic_match.group(1),
                'dynamic': basic_match.group(2),
                'property': basic_match.group(3),
                'full_pattern': pattern
            }
        
        raise ValueError(f"Invalid nested reference pattern: {pattern}")

    def _validate_nested_pattern(self, pattern: str) -> None:
        """Validate nested reference pattern structure"""
        if not pattern.strip():
            raise ValueError("Empty nested reference pattern")
        
        parts = self._parse_nested_reference(pattern)
        
        if not parts['base']:
            raise ValueError("Empty base path")
        if not parts['dynamic']:
            raise ValueError("Empty dynamic variable")
        if not parts['property']:
            raise ValueError("Empty property")
        
        # Check for invalid characters
        invalid_chars = set('{}[]()<>@#$%^&*+=|\\`~')
        for part_name, part_value in parts.items():
            if part_name == 'full_pattern':
                continue
            if any(char in invalid_chars for char in part_value):
                raise ValueError(f"Invalid characters in {part_name}: {part_value}")

    def resolve_nested_reference(self, pattern: str, context: Dict[str, ResolvedVariable]) -> str:
        """
        Resolve nested reference pattern with dynamic path construction.
        
        Args:
            pattern: Pattern like {color.{theme}.primary}
            context: Dictionary of available variables
            
        Returns:
            Fully resolved token value
            
        Raises:
            KeyError: If referenced variables don't exist
            CircularReferenceError: If circular references detected
            ValueError: If pattern is invalid or depth limit exceeded
        """
        # Check cache first
        if self.enable_cache:
            cache_key = self._generate_cache_key(pattern, context)
            if cache_key in self._nested_resolution_cache:
                return self._nested_resolution_cache[cache_key]
        
        # Validate pattern
        self._validate_nested_pattern(pattern)
        
        # Resolve with depth tracking
        result = self._resolve_nested_reference_recursive(
            pattern, context, depth=0, resolution_path=[]
        )
        
        # Cache result
        if self.enable_cache:
            self._update_cache(cache_key, result)
        
        return result

    def _resolve_nested_reference_recursive(self, pattern: str, context: Dict[str, ResolvedVariable], 
                                          depth: int, resolution_path: List[str]) -> str:
        """Recursive resolution with circular reference and depth checking"""
        
        # Check depth limit
        if depth >= self._resolution_depth_limit:
            raise ValueError("Maximum nesting depth exceeded")
        
        # Check for circular references
        if pattern in resolution_path:
            raise CircularReferenceError(f"Circular reference detected: {' -> '.join(resolution_path + [pattern])}")
        
        # Parse the pattern
        parts = self._parse_nested_reference(pattern)
        
        # Resolve dynamic variable(s)
        try:
            dynamic_value = self._resolve_dynamic_variable(parts['dynamic'], context)
            
            # Handle multi-level nesting
            if 'nested_dynamic' in parts:
                nested_dynamic_value = self._resolve_dynamic_variable(parts['nested_dynamic'], context)
                constructed_path = f"{parts['base']}.{dynamic_value}.{nested_dynamic_value}.{parts['property']}"
            else:
                constructed_path = f"{parts['base']}.{dynamic_value}.{parts['property']}"
            
            # Look for the constructed token
            target_token = self._find_token_by_path(constructed_path, context)
            
            if target_token is None:
                error_msg = f"Token '{constructed_path}' not found (constructed from pattern '{pattern}')"
                if self.strict_mode:
                    raise KeyError(error_msg)
                else:
                    if self.verbose:
                        logger.warning(f"⚠️  {error_msg}, returning original pattern")
                    return pattern
            
            # If the target token itself contains references, resolve them recursively
            if self._contains_references(target_token.value):
                return self._resolve_token_references_in_value(
                    target_token.value, context, depth + 1, resolution_path + [pattern]
                )
            
            return target_token.value
            
        except KeyError as e:
            if self.strict_mode:
                raise KeyError(f"Dynamic variable '{parts['dynamic']}' not found in pattern '{pattern}'") from e
            else:
                return pattern

    def _resolve_dynamic_variable(self, var_name: str, context: Dict[str, ResolvedVariable]) -> str:
        """Resolve a dynamic variable name to its value"""
        if var_name not in context:
            raise KeyError(f"Dynamic variable '{var_name}' not found")
        
        dynamic_var = context[var_name]
        
        # If the dynamic variable itself contains references, resolve them first
        if self._contains_references(dynamic_var.value):
            return self._resolve_token_references_in_value(dynamic_var.value, context)
        
        return dynamic_var.value

    def _find_token_by_path(self, path: str, context: Dict[str, ResolvedVariable]) -> Optional[ResolvedVariable]:
        """Find a token by its path, trying various ID formats"""
        # Try exact match first
        if path in context:
            return context[path]
        
        # Try with underscores (JSON token format)
        underscore_path = path.replace('.', '_')
        if underscore_path in context:
            return context[underscore_path]
        
        # Try searching by partial match
        for token_id, token in context.items():
            if token_id.endswith(path.split('.')[-1]):  # Match by final component
                # Additional validation could go here
                return token
        
        return None

    def _contains_references(self, value: str) -> bool:
        """Check if a value contains any type of token references"""
        simple_ref_pattern = r'\{[a-zA-Z][a-zA-Z0-9._]*\}'
        return bool(re.search(simple_ref_pattern, value) or self._is_nested_reference(value))

    def _resolve_token_references_in_value(self, value: str, context: Dict[str, ResolvedVariable], 
                                         depth: int = 0, resolution_path: List[str] = None) -> str:
        """Enhanced version that handles both simple and nested references"""
        if resolution_path is None:
            resolution_path = []
        
        if depth >= self._resolution_depth_limit:
            raise ValueError("Maximum resolution depth exceeded")
        
        # Handle nested references first
        for match in self._nested_reference_regex.finditer(value):
            pattern = match.group(0)
            try:
                resolved_value = self._resolve_nested_reference_recursive(
                    pattern, context, depth + 1, resolution_path
                )
                value = value.replace(pattern, resolved_value)
            except (KeyError, CircularReferenceError) as e:
                if self.strict_mode:
                    raise
                else:
                    if self.verbose:
                        logger.warning(f"⚠️  Failed to resolve nested reference '{pattern}': {e}")
        
        # Handle simple references with existing logic
        simple_pattern = re.compile(r'\{([a-zA-Z][a-zA-Z0-9._]*)\}')
        for match in simple_pattern.finditer(value):
            ref_name = match.group(1)
            full_pattern = match.group(0)
            
            if ref_name in context:
                resolved_ref = context[ref_name].value
                
                # Check for recursive references
                if self._contains_references(resolved_ref) and depth < self._resolution_depth_limit:
                    resolved_ref = self._resolve_token_references_in_value(
                        resolved_ref, context, depth + 1, resolution_path
                    )
                
                value = value.replace(full_pattern, resolved_ref)
        
        return value

    def _generate_cache_key(self, pattern: str, context: Dict[str, ResolvedVariable]) -> str:
        """Generate cache key based on pattern and context state"""
        # Create hash of context values that could affect resolution
        context_hash = hashlib.md5()
        
        # Sort by key for consistent hashing
        for key in sorted(context.keys()):
            var = context[key]
            context_hash.update(f"{key}:{var.value}:{var.hierarchy_level}".encode())
        
        return f"{pattern}:{context_hash.hexdigest()[:8]}"

    def _update_cache(self, cache_key: str, result: str) -> None:
        """Update cache with size limiting"""
        if len(self._nested_resolution_cache) >= self._max_cache_size:
            # Simple LRU: remove oldest entries (first 10%)
            items_to_remove = list(self._nested_resolution_cache.keys())[:self._max_cache_size // 10]
            for key in items_to_remove:
                del self._nested_resolution_cache[key]
        
        self._nested_resolution_cache[cache_key] = result

    def clear_nested_cache(self) -> None:
        """Clear the nested resolution cache"""
        self._nested_resolution_cache.clear()
        if self.verbose:
            logger.info("🧹 Cleared nested reference resolution cache")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'nested_cache_size': len(self._nested_resolution_cache),
            'nested_cache_limit': self._max_cache_size,
            'resolution_depth_limit': self._resolution_depth_limit
        }

    def resolve_all(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, ResolvedVariable]:
        """Enhanced resolve_all method that handles nested references"""
        if context is None:
            context = {}
        
        # Convert context to ResolvedVariable format if needed
        resolved_context = {}
        for key, value in context.items():
            if isinstance(value, ResolvedVariable):
                resolved_context[key] = value
            else:
                # Convert to ResolvedVariable
                resolved_context[key] = ResolvedVariable(
                    id=key,
                    value=str(value),
                    type=TokenType.TEXT,  # Default type
                    scope=TokenScope.THEME,
                    source='manual'
                )
        
        # Resolve any nested references in values
        for var_id, variable in resolved_context.items():
            if self._contains_references(variable.value):
                try:
                    resolved_value = self._resolve_token_references_in_value(variable.value, resolved_context)
                    # Create new variable with resolved value
                    resolved_context[var_id] = ResolvedVariable(
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
                except (KeyError, CircularReferenceError) as e:
                    if self.verbose:
                        logger.warning(f"⚠️  Failed to resolve references in '{var_id}': {e}")
        
        return resolved_context

    def resolve_aspect_ratio_conditional_tokens(self, 
                                              base_tokens: Dict[str, Any], 
                                              aspect_ratio_token: str,
                                              context: Optional[Dict[str, Any]] = None) -> Dict[str, ResolvedVariable]:
        """
        Resolve tokens with aspect ratio conditional values using token-defined aspect ratios.
        
        Args:
            base_tokens: Token structure with aspectRatios definitions and $aspectRatio conditions
            aspect_ratio_token: Token path to aspect ratio (e.g., "aspectRatios.widescreen") 
            context: Additional resolution context
            
        Returns:
            Dictionary of resolved variables with aspect ratio conditional values resolved
            
        Raises:
            AspectRatioTokenError: If aspect ratio token not found or malformed
        """
        if self.verbose:
            logger.info(f"🖥️ Resolving aspect ratio conditional tokens for: {aspect_ratio_token}")
        
        try:
            # Use AspectRatioResolver to resolve conditional tokens
            resolved_tokens = self.aspect_ratio_resolver.resolve_aspect_ratio_tokens(
                base_tokens, aspect_ratio_token
            )
            
            # Convert resolved tokens to ResolvedVariable format
            resolved_variables = {}
            
            for token_path, value in self._flatten_resolved_tokens(resolved_tokens).items():
                # Determine token type and scope
                scope, token_type = self._infer_scope_and_type_from_path(token_path)
                
                # Create ResolvedVariable
                variable = ResolvedVariable(
                    id=token_path.replace('.', '_'),
                    value=str(value),
                    type=token_type,
                    scope=scope,
                    source='aspect_ratio_conditional',
                    hierarchy_level=self.hierarchy_levels['extension_theme'],  # High priority
                    dependencies=[aspect_ratio_token] if aspect_ratio_token not in token_path else []
                )
                
                resolved_variables[variable.id] = variable
            
            if self.verbose:
                logger.info(f"   Resolved {len(resolved_variables)} aspect ratio conditional tokens")
            
            return resolved_variables
            
        except AspectRatioTokenError as e:
            if self.strict_mode:
                raise
            else:
                if self.verbose:
                    logger.warning(f"⚠️ Aspect ratio resolution failed: {e}")
                return {}

    def convert_to_token_structure(self, variables: Dict[str, ResolvedVariable]) -> Dict[str, Any]:
        """
        Convert ResolvedVariable dictionary back to nested token structure.
        
        Args:
            variables: Dictionary of resolved variables
            
        Returns:
            Nested token structure suitable for further processing
        """
        token_structure = {}
        
        for var_id, variable in variables.items():
            # Convert underscored ID back to dot notation path
            token_path = var_id.replace('_', '.')
            
            # Set nested value in structure
            self._set_nested_token_value(token_structure, token_path, variable.value)
        
        return token_structure

    def _flatten_resolved_tokens(self, tokens: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Flatten nested token structure to dot-notation paths"""
        flattened = {}
        
        for key, value in tokens.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict) and not self._is_token_definition(value):
                # Recursively flatten nested objects
                flattened.update(self._flatten_resolved_tokens(value, full_key))
            else:
                # Leaf value
                flattened[full_key] = value
        
        return flattened

    def _is_token_definition(self, value: Dict[str, Any]) -> bool:
        """Check if a dictionary is a token definition (has $type, $value, etc.)"""
        return (
            isinstance(value, dict) and
            ("$type" in value or "$value" in value or "$aspectRatio" in value)
        )

    def _set_nested_token_value(self, obj: Dict[str, Any], path: str, value: Any):
        """Set nested dictionary value using dot notation path"""
        keys = path.split('.')
        current = obj
        
        # Navigate to parent of target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value

    def get_available_aspect_ratios(self, tokens: Dict[str, Any]) -> List[str]:
        """
        Get list of available aspect ratio tokens from token structure.
        
        Args:
            tokens: Token structure containing aspectRatios definitions
            
        Returns:
            List of aspect ratio token paths (e.g., ["aspectRatios.widescreen", "aspectRatios.a4_landscape"])
        """
        aspect_ratio_tokens = self.aspect_ratio_resolver.list_available_aspect_ratios(tokens)
        return [ratio.token_path for ratio in aspect_ratio_tokens]


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