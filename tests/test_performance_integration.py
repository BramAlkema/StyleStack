#!/usr/bin/env python3
"""
Performance Integration Tests for YAML-to-OOXML Processing Engine

Tests performance optimization features in realistic scenarios:
- Operation result caching effectiveness
- Batch processing optimization
- Patch order optimization
- XPath precompilation benefits
- Comprehensive performance statistics

Part of the StyleStack YAML-to-OOXML Processing Engine test suite.
"""

import unittest
import time
from lxml import etree
from tools.yaml_ooxml_processor import YAMLPatchProcessor, RecoveryStrategy


class PerformanceIntegrationTestCase(unittest.TestCase):
    """Integration tests for performance optimization features."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = YAMLPatchProcessor(RecoveryStrategy.RETRY_WITH_FALLBACK)
        
        # Sample OOXML content for performance testing
        self.large_sample_xml = '''<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" 
                                          xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
            <p:cSld>
                <p:spTree>
                    <p:sp>
                        <p:spPr>
                            <a:solidFill>
                                <a:srgbClr val="FF0000"/>
                            </a:solidFill>
                        </p:spPr>
                    </p:sp>
                    <p:sp>
                        <p:spPr>
                            <a:solidFill>
                                <a:srgbClr val="00FF00"/>
                            </a:solidFill>
                        </p:spPr>
                    </p:sp>
                    <p:sp>
                        <p:spPr>
                            <a:solidFill>
                                <a:srgbClr val="0000FF"/>
                            </a:solidFill>
                        </p:spPr>
                    </p:sp>
                </p:spTree>
            </p:cSld>
        </p:sld>'''
    
    def test_cache_performance_improvement(self):
        """Test that caching improves performance for repeated operations."""
        xml_doc = etree.fromstring(self.large_sample_xml)
        
        # Create patches with repeated operations
        patches = [
            {'operation': 'set', 'target': '//a:srgbClr/@val', 'value': 'AAAAAA'},
            {'operation': 'set', 'target': '//a:srgbClr/@val', 'value': 'BBBBBB'},
            {'operation': 'set', 'target': '//a:srgbClr/@val', 'value': 'CCCCCC'},
        ]
        
        # First run to populate cache
        start_time = time.time()
        results1 = self.processor.apply_patches(xml_doc, patches)
        first_run_time = time.time() - start_time
        
        # Second run should benefit from caching
        start_time = time.time()
        results2 = self.processor.apply_patches(xml_doc, patches)
        second_run_time = time.time() - start_time
        
        # Get performance stats
        stats = self.processor.get_comprehensive_stats()
        
        # Verify cache effectiveness
        self.assertGreater(stats.get('perf_cache_hits', 0), 0, "Should have cache hits")
        self.assertGreater(stats.get('perf_cache_hit_rate', 0), 0, "Should have positive cache hit rate")
        
        print(f"Performance test: First run: {first_run_time:.4f}s, Second run: {second_run_time:.4f}s")
        print(f"Cache hit rate: {stats.get('perf_cache_hit_rate', 0):.2%}")
    
    def test_batch_optimization_detection(self):
        """Test that batch processing optimizations are detected."""
        xml_doc = etree.fromstring(self.large_sample_xml)
        
        # Create patches with batch optimization opportunities
        patches = [
            {'operation': 'set', 'target': '//a:srgbClr/@val', 'value': 'FF0000'},
            {'operation': 'set', 'target': '//a:srgbClr/@val', 'value': 'FF1111'},
            {'operation': 'set', 'target': '//a:srgbClr/@val', 'value': 'FF2222'},
            {'operation': 'insert', 'target': '//p:spTree', 'value': '<p:sp></p:sp>'},
            {'operation': 'insert', 'target': '//p:spTree', 'value': '<p:sp></p:sp>'},
        ]
        
        # Process patches and verify batch detection
        results = self.processor.apply_patches(xml_doc, patches)
        stats = self.processor.get_comprehensive_stats()
        
        # Should detect batch opportunities
        self.assertGreater(stats.get('batch_operations', 0), 0, "Should detect batch opportunities")
        self.assertEqual(len(results), len(patches), "Should process all patches")
        
        print(f"Batch optimizations detected: {stats.get('batch_operations', 0)}")
    
    def test_patch_order_optimization(self):
        """Test that patch order optimization is applied."""
        xml_doc = etree.fromstring(self.large_sample_xml)
        
        # Create patches with different complexity levels (in suboptimal order)
        patches = [
            {'operation': 'extend', 'target': '//p:spTree', 'value': ['<p:sp></p:sp>', '<p:sp></p:sp>']},  # Complex
            {'operation': 'set', 'target': '//a:srgbClr/@val', 'value': 'FF0000'},  # Simple
            {'operation': 'merge', 'target': '//p:sp', 'value': {'attr': 'value'}},  # Medium
            {'operation': 'set', 'target': '//a:srgbClr[2]/@val', 'value': '00FF00'},  # Simple
        ]
        
        # Process patches
        results = self.processor.apply_patches(xml_doc, patches)
        stats = self.processor.get_comprehensive_stats()
        
        # Should apply order optimization
        self.assertGreater(stats.get('performance_optimizations', 0), 0, "Should apply order optimization")
        
        print(f"Performance optimizations applied: {stats.get('performance_optimizations', 0)}")
    
    def test_xpath_precompilation_effectiveness(self):
        """Test XPath precompilation effectiveness."""
        xml_doc = etree.fromstring(self.large_sample_xml)
        
        # Create patches with various XPath expressions
        patches = [
            {'operation': 'set', 'target': '//a:srgbClr/@val', 'value': 'AAAAAA'},
            {'operation': 'set', 'target': '//p:sp[1]//a:srgbClr/@val', 'value': 'BBBBBB'},
            {'operation': 'set', 'target': '//p:sp[2]//a:srgbClr/@val', 'value': 'CCCCCC'},
            {'operation': 'set', 'target': '//p:sp[3]//a:srgbClr/@val', 'value': 'DDDDDD'},
        ]
        
        # Process patches
        results = self.processor.apply_patches(xml_doc, patches)
        stats = self.processor.get_comprehensive_stats()
        
        # Should have compiled XPaths
        self.assertGreater(stats.get('perf_compiled_xpaths', 0), 0, "Should have precompiled XPaths")
        
        print(f"Compiled XPaths: {stats.get('perf_compiled_xpaths', 0)}")
    
    def test_comprehensive_performance_statistics(self):
        """Test comprehensive performance statistics collection."""
        xml_doc = etree.fromstring(self.large_sample_xml)
        
        # Create a mix of operations
        patches = [
            {'operation': 'set', 'target': '//a:srgbClr/@val', 'value': 'AA0000'},
            {'operation': 'set', 'target': '//nonexistent/@attr', 'value': 'test'},  # Will fail
            {'operation': 'set', 'target': '//a:srgbClr[2]/@val', 'value': 'BB0000'},
        ]
        
        # Process patches
        results = self.processor.apply_patches(xml_doc, patches)
        stats = self.processor.get_comprehensive_stats()
        
        # Verify comprehensive stats are collected
        expected_stats = [
            'patches_applied', 'errors_encountered', 'success_rate', 'error_rate',
            'perf_cache_hits', 'perf_cache_misses', 'perf_cache_hit_rate',
            'batch_operations', 'performance_optimizations'
        ]
        
        for stat_key in expected_stats:
            self.assertIn(stat_key, stats, f"Should include {stat_key} in stats")
        
        # Verify derived metrics
        self.assertIsInstance(stats.get('success_rate', 0), float, "Success rate should be a float")
        self.assertIsInstance(stats.get('error_rate', 0), float, "Error rate should be a float")
        
        print(f"Comprehensive stats collected: {len(stats)} metrics")
        print(f"Success rate: {stats.get('success_rate', 0):.2%}")
        print(f"Cache efficiency: {stats.get('perf_cache_hit_rate', 0):.2%}")
    
    def test_performance_stats_reset(self):
        """Test performance statistics reset functionality."""
        xml_doc = etree.fromstring(self.large_sample_xml)
        
        # Process some patches to generate stats
        patches = [{'operation': 'set', 'target': '//a:srgbClr/@val', 'value': 'FF0000'}]
        self.processor.apply_patches(xml_doc, patches)
        
        # Verify stats exist
        stats_before = self.processor.get_comprehensive_stats()
        non_zero_stats = [k for k, v in stats_before.items() if isinstance(v, (int, float)) and v > 0]
        self.assertGreater(len(non_zero_stats), 0, "Should have some non-zero stats")
        
        # Reset stats
        self.processor.reset_stats()
        
        # Verify stats are reset
        stats_after = self.processor.get_comprehensive_stats()
        numeric_stats = [v for v in stats_after.values() if isinstance(v, (int, float))]
        self.assertTrue(all(v == 0 for v in numeric_stats), "All numeric stats should be reset to 0")
        
        print("Performance stats reset successfully")


if __name__ == "__main__":
    # Run with verbose output for CI
    unittest.main(verbosity=2)