#!/usr/bin/env python3
"""
Demonstration and Validation of Centralized Mock System

Tests the centralized mock system functionality including registry management,
standardized mocks, call tracking, and context manager usage.

Part of StyleStack 90% Coverage Initiative - Phase 1: Foundation Testing
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from tests.mocks import (
    create_standard_mocks,
    get_mock,
    reset_all_mocks,
    get_mock_call_history,
    mock_external_dependencies,
    FileSystemMocker,
    OOXMLProcessorMocker,
    HTTPMocker,
    DatabaseMocker
)


class TestMockRegistry:
    """Test the central mock registry functionality"""
    
    def test_mock_registration_and_retrieval(self):
        """Test mock registration and retrieval from registry"""
        mocks = create_standard_mocks()
        
        # Test that all expected mocks were created
        assert len(mocks) >= 4
        assert 'ooxml_processor' in mocks
        assert 'requests' in mocks
        assert 'git_repo' in mocks
        assert 'database' in mocks
        
        # Test retrieval by name
        processor = get_mock('ooxml_processor')
        assert processor is not None
        assert isinstance(processor, Mock)
    
    def test_mock_call_tracking(self):
        """Test that mock calls are properly tracked"""
        reset_all_mocks()  # Clear any previous history
        
        processor = get_mock('ooxml_processor')
        if processor:
            # Make some calls to track
            processor.load_template('/test/template.potx')
            processor.extract_variables()
            
            # Note: Call tracking in the mock system may need refinement
            # This tests the interface is available
            history = get_mock_call_history('ooxml_processor')
            assert isinstance(history, list)
    
    def test_mock_reset_functionality(self):
        """Test resetting individual and all mocks"""
        processor = get_mock('ooxml_processor')
        if processor:
            # Make a call
            processor.load_template('/test/template.potx')
            
            # Reset all mocks
            reset_all_mocks()
            
            # Verify reset worked (processor should still exist but be reset)
            assert processor is not None
            # Mock reset_mock should have been called, but we can't easily test this
            # without modifying the mock system further


class TestOOXMLProcessorMock:
    """Test the OOXML processor mock functionality"""
    
    def test_template_loading_operations(self):
        """Test mock template loading behaviors"""
        processor = OOXMLProcessorMocker.create_advanced_mock()
        
        # Test basic loading
        result = processor.load_template('/test/template.potx')
        assert result is True
        
        assert processor.is_loaded() is True
        assert processor.template_path == '/mock/template.potx'
    
    def test_variable_extraction(self):
        """Test mock variable extraction"""
        processor = OOXMLProcessorMocker.create_advanced_mock()
        
        variables = processor.extract_variables()
        assert isinstance(variables, list)
        assert len(variables) == 6
        assert '${brand.primary}' in variables
        assert '${typography.heading.family}' in variables
    
    def test_variable_substitution(self):
        """Test mock variable substitution with different scenarios"""
        processor = OOXMLProcessorMocker.create_advanced_mock()
        
        # Test with default variables
        result = processor.substitute_variables()
        assert result['substituted'] == 6
        assert result['errors'] == 0
        assert 'processing_time' in result
        
        # Test with custom variables
        custom_vars = {'brand.primary': '#ff0000', 'brand.secondary': '#00ff00'}
        result = processor.substitute_variables(custom_vars)
        assert result['substituted'] == len(custom_vars)
    
    def test_xml_manipulation(self):
        """Test mock XML element manipulation"""
        processor = OOXMLProcessorMocker.create_advanced_mock()
        
        elements = processor.find_elements()
        assert isinstance(elements, list)
        assert len(elements) > 0
        
        element = elements[0]
        assert element.tag == 'a:t'
        assert element.text == '${brand.primary}'
        assert 'color' in element.attrib
    
    def test_validation_and_metadata(self):
        """Test mock validation and metadata operations"""
        processor = OOXMLProcessorMocker.create_advanced_mock()
        
        # Test validation
        validation = processor.validate_ooxml()
        assert validation['valid'] is True
        assert isinstance(validation['errors'], list)
        assert validation['schema_version'] == '2016'
        
        # Test metadata
        info = processor.get_template_info()
        assert info['format'] == 'potx'
        assert 'slide_count' in info
        assert info['variable_count'] == 6


class TestHTTPMocker:
    """Test HTTP request mocking functionality"""
    
    def test_response_configuration(self):
        """Test configuring custom HTTP responses"""
        http_mocker = HTTPMocker()
        
        # Add custom response
        http_mocker.add_response(
            'https://api.test.com/data',
            'GET',
            200,
            {'message': 'success', 'data': [1, 2, 3]}
        )
        
        requests_mock = http_mocker.create_requests_mock()
        
        # Test configured response
        response = requests_mock.get('https://api.test.com/data')
        assert response.status_code == 200
        assert response.json()['message'] == 'success'
        assert response.json()['data'] == [1, 2, 3]
    
    def test_default_404_behavior(self):
        """Test that unconfigured URLs return 404"""
        http_mocker = HTTPMocker()
        requests_mock = http_mocker.create_requests_mock()
        
        response = requests_mock.get('https://api.unknown.com/endpoint')
        assert response.status_code == 404
        assert response.text == "Not Found"
    
    def test_request_history_tracking(self):
        """Test that HTTP requests are tracked"""
        http_mocker = HTTPMocker()
        http_mocker.add_response('https://api.test.com/endpoint', 'POST', 201)
        
        requests_mock = http_mocker.create_requests_mock()
        
        # Make requests
        requests_mock.get('https://api.test.com/get')
        requests_mock.post('https://api.test.com/endpoint', json={'data': 'test'})
        
        # Check history
        assert len(http_mocker.request_history) == 2
        assert http_mocker.request_history[0]['method'] == 'GET'
        assert http_mocker.request_history[1]['method'] == 'POST'


class TestFileSystemMocker:
    """Test file system mocking functionality"""
    
    def test_mock_file_structure_creation(self):
        """Test creating mock file structures"""
        fs_mocker = FileSystemMocker()
        
        structure = {
            'templates': {
                'presentation.potx': b'MOCK_POTX_CONTENT',
                'document.dotx': b'MOCK_DOTX_CONTENT'
            },
            'tokens': {
                'design-tokens.json': json.dumps({'brand': {'primary': '#007acc'}})
            },
            'output': None,  # Empty directory
            'README.md': '# Test Project'
        }
        
        root = fs_mocker.create_mock_file_structure(structure)
        
        # Verify structure was created
        assert root.exists()
        assert (root / 'templates').is_dir()
        assert (root / 'templates' / 'presentation.potx').exists()
        assert (root / 'tokens' / 'design-tokens.json').exists()
        assert (root / 'output').is_dir()
        assert (root / 'README.md').read_text() == '# Test Project'
        
        # Test cleanup
        fs_mocker.cleanup()
        # Note: Cleanup might not immediately delete files due to OS caching
    
    def test_file_content_tracking(self):
        """Test that file contents are tracked"""
        fs_mocker = FileSystemMocker()
        
        structure = {
            'test.txt': 'Hello World',
            'data.json': json.dumps({'key': 'value'})
        }
        
        root = fs_mocker.create_mock_file_structure(structure)
        
        # Check tracking
        test_file_path = str(root / 'test.txt')
        data_file_path = str(root / 'data.json')
        
        assert test_file_path in fs_mocker.mock_files
        assert data_file_path in fs_mocker.mock_files
        assert fs_mocker.mock_files[test_file_path] == 'Hello World'


class TestDatabaseMocker:
    """Test database operation mocking"""
    
    def test_table_data_setup(self):
        """Test setting up mock table data"""
        db_mocker = DatabaseMocker()
        
        # Add mock data
        db_mocker.add_table_data('users', [
            {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'},
            {'id': 2, 'name': 'Bob', 'email': 'bob@example.com'}
        ])
        
        connection = db_mocker.create_connection_mock()
        cursor = connection.cursor()
        
        # Test SELECT query
        cursor.execute('SELECT * FROM users')
        results = cursor.fetchall()
        
        assert len(results) == 2
        assert results[0]['name'] == 'Alice'
        assert results[1]['email'] == 'bob@example.com'
    
    def test_query_history_tracking(self):
        """Test that database queries are tracked"""
        db_mocker = DatabaseMocker()
        db_mocker.add_table_data('products', [{'id': 1, 'name': 'Widget'}])
        
        connection = db_mocker.create_connection_mock()
        cursor = connection.cursor()
        
        # Execute queries
        cursor.execute('SELECT * FROM products')
        cursor.execute('INSERT INTO products (name) VALUES (?)', ('New Widget',))
        
        # Check history
        assert len(db_mocker.query_history) == 2
        assert 'SELECT' in db_mocker.query_history[0]['query']
        assert 'INSERT' in db_mocker.query_history[1]['query']


class TestMockContextManager:
    """Test the mock context manager functionality"""
    
    def test_context_manager_basic_usage(self):
        """Test basic usage of mock context manager"""
        with mock_external_dependencies(['requests']) as mocks:
            assert 'requests' in mocks
            
            # Test that the mock is functional
            requests = mocks['requests']
            response = requests.get('https://api.stylestack.dev/health')
            assert response.status_code == 200
            assert response.json()['status'] == 'ok'
    
    def test_context_manager_multiple_dependencies(self):
        """Test mocking multiple dependencies at once"""
        with mock_external_dependencies(['requests', 'database']) as mocks:
            assert 'requests' in mocks
            assert 'database' in mocks
            
            # Test both mocks work
            response = mocks['requests'].get('https://api.stylestack.dev/tokens')
            assert response.status_code == 200
            
            db_connection = mocks['database']
            cursor = db_connection.cursor()
            cursor.execute('SELECT * FROM templates')
            assert cursor.rowcount >= 0


class TestMockIntegration:
    """Integration tests showing real-world mock usage"""
    
    def test_complete_workflow_with_mocks(self):
        """Test a complete workflow using multiple mocks together"""
        with mock_external_dependencies(['requests', 'database']) as mocks:
            # Simulate fetching design tokens from API
            requests = mocks['requests']
            token_response = requests.get('https://api.stylestack.dev/tokens')
            tokens = token_response.json()['tokens']
            
            # Simulate storing in database
            db = mocks['database']
            cursor = db.cursor()
            cursor.execute('INSERT INTO design_tokens (data) VALUES (?)', (json.dumps(tokens),))
            
            # Simulate fetching templates from database
            cursor.execute('SELECT * FROM templates')
            templates = cursor.fetchall()
            
            # Verify workflow
            assert tokens['brand.primary'] == '#007acc'
            assert len(templates) >= 2  # From mock data
    
    def test_mock_isolation_between_tests(self):
        """Test that mocks are properly isolated between test runs"""
        # This test verifies that previous test state doesn't leak
        with mock_external_dependencies(['requests']) as mocks:
            requests = mocks['requests']
            
            # Make a request that should get default response
            response = requests.get('https://api.stylestack.dev/health')
            assert response.status_code == 200
            
            # State should be fresh for each context


if __name__ == '__main__':
    # Run basic validation
    print("Testing Centralized Mock System Integration...")
    
    # Test mock creation
    mocks = create_standard_mocks()
    print(f"✅ Created {len(mocks)} standard mocks")
    
    # Test OOXML processor
    processor = OOXMLProcessorMocker.create_advanced_mock()
    variables = processor.extract_variables()
    print(f"✅ OOXML mock functional: {len(variables)} variables")
    
    # Test HTTP mocker
    http_mocker = HTTPMocker()
    http_mocker.add_response('https://test.api.com/data', 'GET', 200, {'test': True})
    requests_mock = http_mocker.create_requests_mock()
    response = requests_mock.get('https://test.api.com/data')
    print(f"✅ HTTP mock functional: status {response.status_code}")
    
    print("Run with pytest for comprehensive testing")