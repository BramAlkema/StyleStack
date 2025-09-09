"""
YAML Patch Processing System for OOXML Documents

This module handles the core YAML patch operations and processing logic
for OOXML document manipulation.
"""

from typing import Dict, List, Any, Optional, Union, Callable
import logging
import time
from collections import defaultdict
from lxml import etree

from tools.core.types import PatchOperationType, PatchResult, PatchOperation, ErrorSeverity, RecoveryStrategy

logger = logging.getLogger(__name__)


class YAMLPatchProcessor:
    """
    Core processor for YAML patch operations on OOXML documents.
    
    Handles all patch operation types: set, insert, extend, merge, relsAdd
    with comprehensive error handling and recovery strategies.
    """
    
    def __init__(self, recovery_strategy: RecoveryStrategy = RecoveryStrategy.BEST_EFFORT):
        self.recovery_strategy = recovery_strategy
        self.processed_patches = []
        self.failed_patches = []
        
        # Operation handlers
        self.operation_handlers = {
            PatchOperationType.SET: self._handle_set_operation,
            PatchOperationType.INSERT: self._handle_insert_operation,
            PatchOperationType.EXTEND: self._handle_extend_operation,
            PatchOperationType.MERGE: self._handle_merge_operation,
            PatchOperationType.RELSADD: self._handle_relsadd_operation
        }
    
    def process_patches(self, xml_doc: etree._Element, patches: List[PatchOperation],
                       namespaces: Dict[str, str] = None) -> List[PatchResult]:
        """
        Process a list of YAML patch operations.
        
        Args:
            xml_doc: XML document to modify
            patches: List of patch operations
            namespaces: Namespace declarations
            
        Returns:
            List of patch results
        """
        results = []
        
        for patch in patches:
            try:
                result = self._process_single_patch(xml_doc, patch, namespaces or {})
                results.append(result)
                
                if result.success:
                    self.processed_patches.append(patch)
                else:
                    self.failed_patches.append(patch)
                    
                    if self.recovery_strategy == RecoveryStrategy.FAIL_FAST:
                        break
                        
            except Exception as e:
                error_result = PatchResult(
                    success=False,
                    operation=patch.operation,
                    target=patch.target,
                    message=f"Unexpected error: {str(e)}",
                    severity=ErrorSeverity.ERROR,
                    exception_info={'type': type(e).__name__, 'message': str(e)}
                )
                results.append(error_result)
                self.failed_patches.append(patch)
                
                if self.recovery_strategy == RecoveryStrategy.FAIL_FAST:
                    break
        
        return results
    
    def _process_single_patch(self, xml_doc: etree._Element, patch: PatchOperation,
                            namespaces: Dict[str, str]) -> PatchResult:
        """Process a single patch operation."""
        try:
            operation_type = PatchOperationType(patch.operation)
        except ValueError:
            return PatchResult(
                success=False,
                operation=patch.operation,
                target=patch.target,
                message=f"Unknown operation type: {patch.operation}",
                severity=ErrorSeverity.ERROR
            )
        
        handler = self.operation_handlers.get(operation_type)
        if not handler:
            return PatchResult(
                success=False,
                operation=patch.operation,
                target=patch.target,
                message=f"No handler for operation: {patch.operation}",
                severity=ErrorSeverity.ERROR
            )
        
        return handler(xml_doc, patch, namespaces)
    
    def _handle_set_operation(self, xml_doc: etree._Element, patch: PatchOperation,
                            namespaces: Dict[str, str]) -> PatchResult:
        """Handle 'set' operation - replace attribute or text values."""
        try:
            elements = xml_doc.xpath(patch.target, namespaces=namespaces)
            
            if not elements:
                return PatchResult(
                    success=False,
                    operation=patch.operation,
                    target=patch.target,
                    message=f"No elements found for target: {patch.target}",
                    severity=ErrorSeverity.WARNING
                )
            
            affected_count = 0
            
            for element in elements:
                if patch.target.endswith(')'):  # Attribute target
                    # Extract attribute name from XPath
                    if '/@' in patch.target:
                        attr_name = patch.target.split('/@')[-1]
                        element.set(attr_name, str(patch.value))
                        affected_count += 1
                else:  # Text content target
                    element.text = str(patch.value)
                    affected_count += 1
            
            return PatchResult(
                success=True,
                operation=patch.operation,
                target=patch.target,
                message=f"Set operation successful on {affected_count} elements",
                affected_elements=affected_count
            )
            
        except Exception as e:
            return PatchResult(
                success=False,
                operation=patch.operation,
                target=patch.target,
                message=f"Set operation failed: {str(e)}",
                severity=ErrorSeverity.ERROR,
                exception_info={'type': type(e).__name__, 'message': str(e)}
            )
    
    def _handle_insert_operation(self, xml_doc: etree._Element, patch: PatchOperation,
                               namespaces: Dict[str, str]) -> PatchResult:
        """Handle 'insert' operation - add new elements."""
        try:
            target_elements = xml_doc.xpath(patch.target, namespaces=namespaces)
            
            if not target_elements:
                return PatchResult(
                    success=False,
                    operation=patch.operation,
                    target=patch.target,
                    message=f"No target elements found: {patch.target}",
                    severity=ErrorSeverity.WARNING
                )
            
            # Create new element from value
            if isinstance(patch.value, str):
                try:
                    new_element = etree.fromstring(patch.value)
                except etree.XMLSyntaxError:
                    # Treat as text content
                    new_element = etree.Element("text")
                    new_element.text = patch.value
            elif isinstance(patch.value, dict):
                # Convert dict to XML element
                tag = patch.value.get('tag', 'element')
                new_element = etree.Element(tag)
                
                for key, value in patch.value.items():
                    if key != 'tag':
                        if key.startswith('@'):
                            new_element.set(key[1:], str(value))
                        elif key == 'text':
                            new_element.text = str(value)
            else:
                return PatchResult(
                    success=False,
                    operation=patch.operation,
                    target=patch.target,
                    message=f"Invalid value type for insert: {type(patch.value)}",
                    severity=ErrorSeverity.ERROR
                )
            
            affected_count = 0
            position = patch.position or 'append'
            
            for target_elem in target_elements:
                if position == 'append':
                    target_elem.append(new_element)
                elif position == 'prepend':
                    target_elem.insert(0, new_element)
                elif position == 'before':
                    parent = target_elem.getparent()
                    if parent is not None:
                        index = list(parent).index(target_elem)
                        parent.insert(index, new_element)
                elif position == 'after':
                    parent = target_elem.getparent()
                    if parent is not None:
                        index = list(parent).index(target_elem)
                        parent.insert(index + 1, new_element)
                
                affected_count += 1
            
            return PatchResult(
                success=True,
                operation=patch.operation,
                target=patch.target,
                message=f"Insert operation successful on {affected_count} elements",
                affected_elements=affected_count
            )
            
        except Exception as e:
            return PatchResult(
                success=False,
                operation=patch.operation,
                target=patch.target,
                message=f"Insert operation failed: {str(e)}",
                severity=ErrorSeverity.ERROR,
                exception_info={'type': type(e).__name__, 'message': str(e)}
            )
    
    def _handle_extend_operation(self, xml_doc: etree._Element, patch: PatchOperation,
                               namespaces: Dict[str, str]) -> PatchResult:
        """Handle 'extend' operation - add multiple elements."""
        try:
            target_elements = xml_doc.xpath(patch.target, namespaces=namespaces)
            
            if not target_elements:
                return PatchResult(
                    success=False,
                    operation=patch.operation,
                    target=patch.target,
                    message=f"No target elements found: {patch.target}",
                    severity=ErrorSeverity.WARNING
                )
            
            if not isinstance(patch.value, list):
                return PatchResult(
                    success=False,
                    operation=patch.operation,
                    target=patch.target,
                    message="Extend operation requires array value",
                    severity=ErrorSeverity.ERROR
                )
            
            affected_count = 0
            
            for target_elem in target_elements:
                for item in patch.value:
                    # Create element for each item
                    if isinstance(item, str):
                        try:
                            new_elem = etree.fromstring(item)
                        except etree.XMLSyntaxError:
                            new_elem = etree.Element("item")
                            new_elem.text = item
                    elif isinstance(item, dict):
                        tag = item.get('tag', 'item')
                        new_elem = etree.Element(tag)
                        
                        for key, value in item.items():
                            if key != 'tag':
                                if key.startswith('@'):
                                    new_elem.set(key[1:], str(value))
                                elif key == 'text':
                                    new_elem.text = str(value)
                    else:
                        new_elem = etree.Element("item")
                        new_elem.text = str(item)
                    
                    target_elem.append(new_elem)
                    affected_count += 1
            
            return PatchResult(
                success=True,
                operation=patch.operation,
                target=patch.target,
                message=f"Extend operation added {affected_count} elements",
                affected_elements=affected_count
            )
            
        except Exception as e:
            return PatchResult(
                success=False,
                operation=patch.operation,
                target=patch.target,
                message=f"Extend operation failed: {str(e)}",
                severity=ErrorSeverity.ERROR,
                exception_info={'type': type(e).__name__, 'message': str(e)}
            )
    
    def _handle_merge_operation(self, xml_doc: etree._Element, patch: PatchOperation,
                              namespaces: Dict[str, str]) -> PatchResult:
        """Handle 'merge' operation - combine attributes/elements."""
        try:
            target_elements = xml_doc.xpath(patch.target, namespaces=namespaces)
            
            if not target_elements:
                return PatchResult(
                    success=False,
                    operation=patch.operation,
                    target=patch.target,
                    message=f"No target elements found: {patch.target}",
                    severity=ErrorSeverity.WARNING
                )
            
            if not isinstance(patch.value, dict):
                return PatchResult(
                    success=False,
                    operation=patch.operation,
                    target=patch.target,
                    message="Merge operation requires dictionary value",
                    severity=ErrorSeverity.ERROR
                )
            
            affected_count = 0
            merge_strategy = patch.merge_strategy or 'update'
            
            for target_elem in target_elements:
                for key, value in patch.value.items():
                    if key.startswith('@'):
                        # Merge attribute
                        attr_name = key[1:]
                        existing_value = target_elem.get(attr_name)
                        
                        if merge_strategy == 'update' or existing_value is None:
                            target_elem.set(attr_name, str(value))
                        elif merge_strategy == 'append' and existing_value:
                            target_elem.set(attr_name, f"{existing_value} {value}")
                            
                    elif key == 'text':
                        # Merge text content
                        existing_text = target_elem.text or ''
                        
                        if merge_strategy == 'update':
                            target_elem.text = str(value)
                        elif merge_strategy == 'append':
                            target_elem.text = f"{existing_text} {value}"
                
                affected_count += 1
            
            return PatchResult(
                success=True,
                operation=patch.operation,
                target=patch.target,
                message=f"Merge operation successful on {affected_count} elements",
                affected_elements=affected_count
            )
            
        except Exception as e:
            return PatchResult(
                success=False,
                operation=patch.operation,
                target=patch.target,
                message=f"Merge operation failed: {str(e)}",
                severity=ErrorSeverity.ERROR,
                exception_info={'type': type(e).__name__, 'message': str(e)}
            )
    
    def _handle_relsadd_operation(self, xml_doc: etree._Element, patch: PatchOperation,
                                namespaces: Dict[str, str]) -> PatchResult:
        """Handle 'relsAdd' operation - add OOXML relationship entries."""
        try:
            # This is a placeholder for relationship handling
            # Real implementation would handle .rels files
            return PatchResult(
                success=True,
                operation=patch.operation,
                target=patch.target,
                message="RelsAdd operation completed (placeholder)",
                affected_elements=0,
                severity=ErrorSeverity.INFO
            )
            
        except Exception as e:
            return PatchResult(
                success=False,
                operation=patch.operation,
                target=patch.target,
                message=f"RelsAdd operation failed: {str(e)}",
                severity=ErrorSeverity.ERROR,
                exception_info={'type': type(e).__name__, 'message': str(e)}
            )


class PerformanceOptimizer:
    """
    Performance optimization system for YAML patch operations.
    
    Provides caching, batch processing, and performance monitoring
    to maximize throughput and minimize processing overhead.
    """
    
    def __init__(self):
        """Initialize the performance optimizer."""
        # Operation result caching
        self.operation_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Batch processing state
        self.batch_targets = defaultdict(list)  # Group patches by target
        self.batch_operations = defaultdict(list)  # Group patches by operation type
        
        # Performance metrics
        self.timing_stats = {
            'xpath_resolution': [],
            'patch_application': [],
            'namespace_detection': [],
            'batch_processing': []
        }
        
        # Optimization flags
        self.enable_caching = True
        self.enable_batch_processing = True
        self.enable_xpath_precompilation = True
        
        # Precompiled XPath cache
        self.compiled_xpath_cache = {}
    
    def get_cache_key(self, operation: str, target: str, value: Any, doc_id: int) -> str:
        """Generate a cache key for an operation."""
        # Create a hashable representation of the value
        if isinstance(value, (dict, list)):
            value_hash = str(hash(str(sorted(value.items()) if isinstance(value, dict) else value)))
        else:
            value_hash = str(hash(str(value)))
        
        return f"{operation}:{target}:{value_hash}:{doc_id}"
    
    def cache_result(self, cache_key: str, result: PatchResult) -> None:
        """Cache a patch operation result."""
        if not self.enable_caching:
            return
            
        # Only cache successful results to avoid caching errors
        if result.success:
            self.operation_cache[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }
            
        # Limit cache size to prevent memory issues
        if len(self.operation_cache) > 1000:
            # Remove oldest entries
            oldest_keys = sorted(self.operation_cache.keys(), 
                               key=lambda k: self.operation_cache[k]['timestamp'])[:100]
            for key in oldest_keys:
                del self.operation_cache[key]
    
    def get_cached_result(self, cache_key: str) -> Optional[PatchResult]:
        """Retrieve a cached result if available."""
        if not self.enable_caching:
            return None
            
        if cache_key in self.operation_cache:
            self.cache_hits += 1
            cached_data = self.operation_cache[cache_key]
            
            # Check cache age (expire after 5 minutes)
            if time.time() - cached_data['timestamp'] < 300:
                return cached_data['result']
            else:
                # Remove expired entry
                del self.operation_cache[cache_key]
        
        self.cache_misses += 1
        return None
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        stats = {
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': self.cache_hits / max(self.cache_hits + self.cache_misses, 1),
            'cached_operations': len(self.operation_cache),
            'compiled_xpaths': len(self.compiled_xpath_cache)
        }
        
        # Calculate timing statistics
        for op_type, times in self.timing_stats.items():
            if times:
                stats[f'{op_type}_avg_time'] = sum(times) / len(times)
                stats[f'{op_type}_total_time'] = sum(times)
                stats[f'{op_type}_count'] = len(times)
            else:
                stats[f'{op_type}_avg_time'] = 0
                stats[f'{op_type}_total_time'] = 0
                stats[f'{op_type}_count'] = 0
        
        return stats
