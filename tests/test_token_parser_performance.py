"""
Performance Tests for StyleStack Token Parser

Tests parser performance with large token sets to ensure scalability
for enterprise-scale template processing with 1000+ variables.

Validates:
- Parsing performance with large token counts
- Memory usage optimization
- Circular dependency detection efficiency 
- Error reporting performance
- Validation report generation speed
"""


from typing import Dict
import pytest
import time
import random
import sys
import os

# Add tools directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))



class TestTokenParserPerformance:
    """Performance test suite for token parser scalability"""
    
    def generate_large_token_content(self, token_count: int = 1000) -> str:
        """Generate content with large number of tokens for performance testing"""
        tokens = []
        scopes = [scope.value for scope in TokenScope if scope != TokenScope.THEME]
        
        for i in range(token_count):
            scope = random.choice(scopes)
            identifier = f"token_{i}_{random.choice(['color', 'font', 'size', 'margin', 'padding'])}"
            tokens.append(f"{{tokens.{scope}.{identifier}}}")
        
        # Mix tokens with realistic OOXML content
        content_chunks = []
        for i, token in enumerate(tokens):
            if i % 50 == 0:
                content_chunks.append(f'''
                <a:solidFill>
                  <a:srgbClr val="{token}"/>
                </a:solidFill>
                ''')
            elif i % 30 == 0:
                content_chunks.append(f'''
                <a:latin typeface="{token}"/>
                ''')
            else:
                content_chunks.append(f'Property: {token}\n')
        
        return ''.join(content_chunks)
    
    def generate_variable_definitions(self, token_count: int = 1000) -> Dict[str, Dict]:
        """Generate variable definitions for performance testing"""
        definitions = {}
        types = [t.value for t in TokenType]
        scopes = [scope.value for scope in TokenScope if scope != TokenScope.THEME]
        
        for i in range(token_count):
            scope = random.choice(scopes)
            identifier = f"token_{i}_{random.choice(['color', 'font', 'size', 'margin', 'padding'])}"
            token_type = random.choice(types)
            
            key = f"{scope}.{identifier}"
            definitions[key] = {
                'type': token_type,
                'scope': scope,
                'id': identifier,
                'defaultValue': self._generate_default_value(token_type),
                'xpath': f"//a:element[@attr='{identifier}']",
                'description': f"Generated test token {i}"
            }
        
        return definitions
    
    def _generate_default_value(self, token_type: str) -> str:
        """Generate appropriate default value for token type"""
        if token_type == 'color':
            return f"#{random.randint(0, 16777215):06x}"
        elif token_type == 'font':
            return random.choice(['Arial', 'Helvetica', 'Times New Roman', 'Calibri'])
        elif token_type == 'number':
            return str(random.randint(1, 100))
        elif token_type == 'dimension':
            return f"{random.randint(8, 72)}pt"
        else:
            return f"test_value_{random.randint(1, 1000)}"
    
    def test_parse_1000_tokens_performance(self):
        """Test parsing 1000 tokens within performance threshold"""
        parser = TokenParser()
        content = self.generate_large_token_content(1000)
        
        start_time = time.time()
        tokens = parser.parse(content)
        end_time = time.time()
        
        parse_time = end_time - start_time
        
        # Performance assertions
        assert len(tokens) == 1000, f"Expected 1000 tokens, got {len(tokens)}"
        assert parse_time < 2.0, f"Parsing took {parse_time:.2f}s, expected < 2.0s"
        assert len(parser.errors) == 0, f"Unexpected parsing errors: {len(parser.errors)}"
        
        print(f"✅ Parsed {len(tokens)} tokens in {parse_time:.3f}s")
        print(f"   Performance: {len(tokens)/parse_time:.0f} tokens/second")
    
    def test_parse_5000_tokens_performance(self):
        """Test parsing 5000 tokens for enterprise-scale performance"""
        parser = TokenParser()
        content = self.generate_large_token_content(5000)
        
        start_time = time.time()
        tokens = parser.parse(content)
        end_time = time.time()
        
        parse_time = end_time - start_time
        
        # Performance assertions - more lenient for larger set
        assert len(tokens) == 5000, f"Expected 5000 tokens, got {len(tokens)}"
        assert parse_time < 10.0, f"Parsing took {parse_time:.2f}s, expected < 10.0s"
        
        print(f"✅ Parsed {len(tokens)} tokens in {parse_time:.3f}s")
        print(f"   Performance: {len(tokens)/parse_time:.0f} tokens/second")
    
    def test_validation_with_large_definitions(self):
        """Test validation performance with large variable definitions"""
        token_count = 1000
        definitions = self.generate_variable_definitions(token_count)
        parser = TokenParser(definitions)
        content = self.generate_large_token_content(token_count)
        
        start_time = time.time()
        tokens = parser.parse(content)
        end_time = time.time()
        
        parse_time = end_time - start_time
        
        # Validation should still be fast with definitions
        assert len(tokens) == token_count
        assert parse_time < 5.0, f"Validation took {parse_time:.2f}s, expected < 5.0s"
        
        # Check that types were assigned from definitions
        typed_tokens = [t for t in tokens if t.type is not None]
        assert len(typed_tokens) > 0, "No tokens were assigned types from definitions"
        
        print(f"✅ Validated {len(tokens)} tokens with definitions in {parse_time:.3f}s")
        print(f"   Typed tokens: {len(typed_tokens)}/{len(tokens)}")
    
    def test_circular_dependency_detection_performance(self):
        """Test circular dependency detection with large dependency graph"""
        # Create complex dependency graph with some circular refs
        definitions = {}
        token_count = 500  # Smaller for dependency graph complexity
        
        for i in range(token_count):
            key = f"org.token_{i}"
            dependencies = []
            
            # Add some dependencies to create complex graph
            if i > 0:
                dependencies.append(f"org.token_{i-1}")
            if i > 10:
                dependencies.append(f"core.token_{i-10}")
            
            # Add circular dependency every 100 tokens
            if i % 100 == 99 and i > 0:
                dependencies.append(f"org.token_{i-50}")
                # Also make token_i-50 depend on this one (circular)
                if f"org.token_{i-50}" in definitions:
                    definitions[f"org.token_{i-50}"]["dependencies"].append(key)
            
            definitions[key] = {
                'type': 'color',
                'scope': 'org',
                'id': f'token_{i}',
                'dependencies': dependencies
            }
        
        # Create content with these tokens
        content = ' '.join([f"{{tokens.org.token_{i}}}" for i in range(token_count)])
        
        parser = TokenParser(definitions)
        
        start_time = time.time()
        tokens = parser.parse(content)
        end_time = time.time()
        
        parse_time = end_time - start_time
        
        # Should detect circular dependencies efficiently
        assert parse_time < 3.0, f"Dependency detection took {parse_time:.2f}s, expected < 3.0s"
        
        circular_errors = [e for e in parser.errors if e.error_type == 'dependency']
        assert len(circular_errors) > 0, "Should have detected circular dependencies"
        
        print(f"✅ Processed {len(tokens)} tokens with dependency checking in {parse_time:.3f}s")
        print(f"   Detected {len(circular_errors)} circular dependencies")
    
    def test_validation_report_generation_performance(self):
        """Test validation report generation performance with large token set"""
        token_count = 2000
        definitions = self.generate_variable_definitions(token_count)
        parser = TokenParser(definitions)
        content = self.generate_large_token_content(token_count)
        
        # Parse tokens first
        tokens = parser.parse(content)
        
        # Time report generation
        start_time = time.time()
        report = parser.generate_validation_report()
        end_time = time.time()
        
        report_time = end_time - start_time
        
        # Report generation should be fast
        assert report_time < 1.0, f"Report generation took {report_time:.2f}s, expected < 1.0s"
        
        # Verify report completeness
        assert report['summary']['total_tokens'] == len(tokens)
        assert len(report['tokens']) == len(tokens)
        assert 'hierarchy_analysis' in report
        
        print(f"✅ Generated validation report for {len(tokens)} tokens in {report_time:.3f}s")
        print(f"   Report sections: {list(report.keys())}")
    
    def test_memory_usage_with_large_token_set(self):
        """Test memory usage doesn't grow excessively with large token sets"""
        import tracemalloc
        
        tracemalloc.start()
        
        # Parse progressively larger token sets
        sizes = [100, 500, 1000, 2000]
        memory_usage = []
        
        for size in sizes:
            parser = TokenParser()
            content = self.generate_large_token_content(size)
            
            current, peak = tracemalloc.get_traced_memory()
            tokens = parser.parse(content)
            current_after, peak_after = tracemalloc.get_traced_memory()
            
            memory_increase = (current_after - current) / 1024  # KB
            memory_usage.append(memory_increase)
            
            print(f"   {size} tokens: {memory_increase:.1f} KB memory increase")
        
        tracemalloc.stop()
        
        # Memory growth should be roughly linear, not exponential
        # Check that doubling tokens doesn't quadruple memory
        ratio_1000_to_500 = memory_usage[2] / memory_usage[1] if memory_usage[1] > 0 else 0
        ratio_2000_to_1000 = memory_usage[3] / memory_usage[2] if memory_usage[2] > 0 else 0
        
        assert ratio_1000_to_500 < 3.0, f"Memory growth too high: {ratio_1000_to_500:.2f}x"
        assert ratio_2000_to_1000 < 3.0, f"Memory growth too high: {ratio_2000_to_1000:.2f}x"
        
        print(f"✅ Memory usage scales linearly with token count")
    
    def test_error_reporting_performance(self):
        """Test error reporting performance with many malformed tokens"""
        # Create content with mix of valid and invalid tokens
        valid_tokens = []
        invalid_tokens = []
        
        for i in range(500):
            valid_tokens.append(f"{{tokens.org.valid_{i}}}")
            # Add various malformed tokens
            invalid_tokens.extend([
                f"{{tokens.invalid_scope.token_{i}}}",
                f"{{tokens.org.123invalid_{i}}}",  # Invalid identifier
                f"{{tokens.org.token-{i}}}",        # Invalid character
            ])
        
        # Mix valid and invalid tokens
        all_tokens = valid_tokens + invalid_tokens
        random.shuffle(all_tokens)
        content = ' '.join(all_tokens)
        
        parser = TokenParser()
        
        start_time = time.time()
        tokens = parser.parse(content)
        end_time = time.time()
        
        parse_time = end_time - start_time
        
        # Should handle errors efficiently
        assert parse_time < 3.0, f"Error handling took {parse_time:.2f}s, expected < 3.0s"
        assert len(tokens) == 500, f"Expected 500 valid tokens, got {len(tokens)}"
        assert len(parser.errors) == 1500, f"Expected 1500 errors, got {len(parser.errors)}"
        
        print(f"✅ Processed {len(all_tokens)} tokens with {len(parser.errors)} errors in {parse_time:.3f}s")
        print(f"   Error handling rate: {len(parser.errors)/parse_time:.0f} errors/second")
    
    def test_hierarchy_resolution_performance(self):
        """Test hierarchy resolution performance with many override levels"""
        # Create tokens with same identifier across all hierarchy levels
        identifiers = [f"token_{i}" for i in range(200)]
        scopes = [scope.value for scope in TokenScope if scope != TokenScope.THEME]
        
        content_parts = []
        for identifier in identifiers:
            for scope in scopes:
                content_parts.append(f"{{tokens.{scope}.{identifier}}}")
        
        content = ' '.join(content_parts)
        parser = TokenParser()
        
        start_time = time.time()
        tokens = parser.parse(content)
        
        # Test hierarchy resolution for each identifier
        resolution_times = []
        for identifier in identifiers:
            res_start = time.time()
            resolved = parser.resolve_token_hierarchy(identifier)
            res_end = time.time()
            resolution_times.append(res_end - res_start)
            
            # Should resolve to highest precedence (USER)
            assert resolved is not None
            assert resolved.scope == TokenScope.USER
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_resolution_time = sum(resolution_times) / len(resolution_times)
        
        # Performance assertions
        assert total_time < 5.0, f"Total processing took {total_time:.2f}s, expected < 5.0s"
        assert avg_resolution_time < 0.001, f"Avg resolution time {avg_resolution_time:.4f}s too slow"
        
        print(f"✅ Processed {len(tokens)} tokens with hierarchy resolution in {total_time:.3f}s")
        print(f"   Average resolution time: {avg_resolution_time*1000:.2f}ms per identifier")


class TestTokenParserStressTests:
    """Stress tests for extreme scenarios"""
    
    def test_extremely_long_token_identifiers(self):
        """Test parser with very long token identifiers"""
        long_identifier = 'a' * 1000  # 1000 character identifier
        content = f"{{tokens.org.{long_identifier}}}"
        
        parser = TokenParser()
        
        start_time = time.time()
        tokens = parser.parse(content)
        end_time = time.time()
        
        parse_time = end_time - start_time
        
        # Should handle long identifiers efficiently
        assert parse_time < 0.1, f"Long identifier parsing took {parse_time:.3f}s"
        assert len(tokens) == 1
        assert tokens[0].identifier == long_identifier
        
        print(f"✅ Handled {len(long_identifier)}-character identifier in {parse_time:.3f}s")
    
    def test_deeply_nested_dependencies(self):
        """Test deeply nested dependency chains"""
        chain_length = 100
        definitions = {}
        
        # Create chain: token_0 → token_1 → token_2 → ... → token_99
        for i in range(chain_length):
            dependencies = [f"org.token_{i+1}"] if i < chain_length - 1 else []
            definitions[f"org.token_{i}"] = {
                'type': 'color',
                'scope': 'org',
                'id': f'token_{i}',
                'dependencies': dependencies
            }
        
        content = ' '.join([f"{{tokens.org.token_{i}}}" for i in range(chain_length)])
        parser = TokenParser(definitions)
        
        start_time = time.time()
        tokens = parser.parse(content)
        end_time = time.time()
        
        parse_time = end_time - start_time
        
        # Should handle deep dependency chains efficiently
        assert parse_time < 2.0, f"Deep dependency parsing took {parse_time:.2f}s"
        assert len(tokens) == chain_length
        
        # Should not detect circular dependencies (it's a chain, not a cycle)
        circular_errors = [e for e in parser.errors if e.error_type == 'dependency']
        assert len(circular_errors) == 0, f"False positive circular dependencies: {len(circular_errors)}"
        
        print(f"✅ Processed {chain_length}-deep dependency chain in {parse_time:.3f}s")


if __name__ == "__main__":
    # Run performance tests manually
    print("🚀 Running StyleStack Token Parser Performance Tests")
    
    perf_tests = TestTokenParserPerformance()
    
    # Basic performance test
    try:
        print("\n📊 Testing 1000 token parsing performance...")
        perf_tests.test_parse_1000_tokens_performance()
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
    
    # Memory usage test
    try:
        print("\n💾 Testing memory usage scaling...")
        perf_tests.test_memory_usage_with_large_token_set()
    except Exception as e:
        print(f"❌ Memory test failed: {e}")
    
    # Dependency detection test
    try:
        print("\n🔄 Testing circular dependency detection performance...")
        perf_tests.test_circular_dependency_detection_performance()
    except Exception as e:
        print(f"❌ Dependency test failed: {e}")
    
    print("\n✅ Performance testing completed!")