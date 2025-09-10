#!/usr/bin/env python3
"""
Centralized Mock System for External Dependencies

Provides standardized, high-quality mocks for external systems and libraries
used throughout StyleStack. This reduces test duplication and ensures consistency
across the test suite.

Key Features:
- Standardized mock behaviors for common libraries
- Configurable mock responses for different test scenarios
- Performance-optimized mock implementations
- Thread-safe mock state management
- Automatic cleanup and reset mechanisms

Part of StyleStack 90% Coverage Initiative - Phase 1: Foundation Testing
"""

import os
import json
import time
import tempfile
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from collections import defaultdict
from datetime import datetime, timedelta
import weakref


class MockRegistry:
    """Central registry for managing all mock objects and their state"""
    
    def __init__(self):
        self._mocks: Dict[str, Mock] = {}
        self._patches: Dict[str, Any] = {}
        self._configurations: Dict[str, Dict] = {}
        self._call_history: Dict[str, List] = defaultdict(list)
        self._reset_callbacks: List[Callable] = []
        self._lock = threading.RLock()
    
    def register_mock(self, name: str, mock_obj: Mock, config: Dict = None):
        """Register a mock object with optional configuration"""
        with self._lock:
            self._mocks[name] = mock_obj
            self._configurations[name] = config or {}
            
            # Add call tracking
            original_call = mock_obj.__call__ if hasattr(mock_obj, '__call__') else None
            
            def tracked_call(*args, **kwargs):
                self._call_history[name].append({
                    'timestamp': time.time(),
                    'args': args,
                    'kwargs': kwargs
                })
                if original_call:
                    return original_call(*args, **kwargs)
            
            if hasattr(mock_obj, '__call__'):
                mock_obj.side_effect = tracked_call
    
    def get_mock(self, name: str) -> Optional[Mock]:
        """Get a registered mock by name"""
        with self._lock:
            return self._mocks.get(name)
    
    def reset_mock(self, name: str = None):
        """Reset specific mock or all mocks"""
        with self._lock:
            if name:
                if name in self._mocks:
                    self._mocks[name].reset_mock()
                    self._call_history[name].clear()
            else:
                for mock_obj in self._mocks.values():
                    mock_obj.reset_mock()
                self._call_history.clear()
                
                # Execute reset callbacks
                for callback in self._reset_callbacks:
                    try:
                        callback()
                    except Exception as e:
                        print(f"Warning: Reset callback failed: {e}")
    
    def get_call_history(self, name: str) -> List[Dict]:
        """Get call history for a specific mock"""
        with self._lock:
            return self._call_history.get(name, []).copy()
    
    def add_reset_callback(self, callback: Callable):
        """Add callback to execute on reset"""
        self._reset_callbacks.append(callback)


# Global mock registry
_mock_registry = MockRegistry()


class FileSystemMocker:
    """Mock file system operations for testing"""
    
    def __init__(self):
        self.temp_roots = []
        self.mock_files = {}
        self.mock_dirs = set()
        
    def create_mock_file_structure(self, structure: Dict[str, Any], root: Path = None) -> Path:
        """Create mock file structure from dictionary specification"""
        if root is None:
            root = Path(tempfile.mkdtemp(prefix='stylestack_mock_'))
            self.temp_roots.append(root)
        
        for path, content in structure.items():
            full_path = root / path
            
            if isinstance(content, dict):
                # Directory with contents
                full_path.mkdir(parents=True, exist_ok=True)
                self.create_mock_file_structure(content, full_path)
            elif isinstance(content, str):
                # Text file
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
                self.mock_files[str(full_path)] = content
            elif isinstance(content, bytes):
                # Binary file
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_bytes(content)
                self.mock_files[str(full_path)] = content
            elif content is None:
                # Empty directory
                full_path.mkdir(parents=True, exist_ok=True)
                self.mock_dirs.add(str(full_path))
        
        return root
    
    def cleanup(self):
        """Clean up all temporary file structures"""
        import shutil
        for temp_root in self.temp_roots:
            if temp_root.exists():
                shutil.rmtree(temp_root, ignore_errors=True)
        self.temp_roots.clear()
        self.mock_files.clear()
        self.mock_dirs.clear()


class OOXMLProcessorMocker:
    """Advanced OOXML processor mock with realistic behaviors"""
    
    @staticmethod
    def create_advanced_mock() -> Mock:
        """Create comprehensive OOXML processor mock"""
        mock = Mock()
        
        # Template loading
        mock.load_template.return_value = True
        mock.is_loaded.return_value = True
        mock.template_path = '/mock/template.potx'
        
        # Variable extraction
        mock.extract_variables.return_value = [
            '${brand.primary}',
            '${brand.secondary}',
            '${typography.heading.family}',
            '${typography.body.size}',
            '${spacing.medium}',
            '${layout.margin}'
        ]
        
        # Variable substitution
        def mock_substitute(variables=None, **kwargs):
            var_count = len(variables) if variables else 6
            return {
                'substituted': var_count,
                'errors': 0,
                'warnings': [],
                'processing_time': 0.05
            }
        
        mock.substitute_variables.side_effect = mock_substitute
        
        # XML manipulation
        mock_element = Mock()
        mock_element.tag = 'a:t'
        mock_element.text = '${brand.primary}'
        mock_element.attrib = {'color': 'auto'}
        
        mock.find_elements.return_value = [mock_element]
        mock.update_element.return_value = True
        mock.create_element.return_value = mock_element
        
        # Validation
        mock.validate_ooxml.return_value = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'schema_version': '2016'
        }
        
        # Save operations
        mock.save_template.return_value = True
        mock.export_to_format.return_value = '/mock/output.potx'
        
        # Metadata
        mock.get_template_info.return_value = {
            'format': 'potx',
            'app_version': 'Microsoft PowerPoint 16.0',
            'created': datetime.now().isoformat(),
            'slide_count': 5,
            'variable_count': 6
        }
        
        return mock


class GitMocker:
    """Mock Git operations for testing build workflows"""
    
    @staticmethod
    def create_repo_mock() -> Mock:
        """Create mock Git repository"""
        repo_mock = Mock()
        
        # Repository properties
        repo_mock.working_dir = '/mock/repo'
        repo_mock.git_dir = '/mock/repo/.git'
        repo_mock.bare = False
        
        # Branch info
        branch_mock = Mock()
        branch_mock.name = 'main'
        repo_mock.active_branch = branch_mock
        repo_mock.branches = [branch_mock]
        
        # Commit info
        commit_mock = Mock()
        commit_mock.hexsha = 'abc123def456'
        commit_mock.message = 'Mock commit message'
        commit_mock.author.name = 'Test Author'
        commit_mock.author.email = 'test@example.com'
        commit_mock.committed_datetime = datetime.now()
        
        repo_mock.head.commit = commit_mock
        repo_mock.commits = Mock()
        repo_mock.commits.__iter__ = lambda: iter([commit_mock])
        
        # Repository operations
        repo_mock.is_dirty.return_value = False
        repo_mock.untracked_files = []
        
        def mock_git_command(*args, **kwargs):
            if args[0] == 'status':
                return 'On branch main\nnothing to commit, working tree clean'
            elif args[0] == 'log':
                return f"{commit_mock.hexsha[:7]} {commit_mock.message}"
            return "Mock git output"
        
        repo_mock.git.side_effect = mock_git_command
        
        return repo_mock


class HTTPMocker:
    """Mock HTTP requests for API testing"""
    
    def __init__(self):
        self.responses = {}
        self.request_history = []
    
    def add_response(self, url: str, method: str = 'GET', status_code: int = 200, 
                    json_data: Dict = None, text: str = None, headers: Dict = None):
        """Add a mock HTTP response"""
        key = f"{method.upper()}:{url}"
        response_mock = Mock()
        response_mock.status_code = status_code
        response_mock.headers = headers or {}
        
        if json_data:
            response_mock.json.return_value = json_data
            response_mock.text = json.dumps(json_data)
        elif text:
            response_mock.text = text
            response_mock.json.side_effect = ValueError("No JSON object could be decoded")
        
        self.responses[key] = response_mock
    
    def create_requests_mock(self) -> Mock:
        """Create mock requests module"""
        requests_mock = Mock()
        
        def mock_request(method, url, **kwargs):
            key = f"{method.upper()}:{url}"
            
            # Record request
            self.request_history.append({
                'method': method,
                'url': url,
                'timestamp': time.time(),
                'kwargs': kwargs
            })
            
            # Return configured response or default
            if key in self.responses:
                return self.responses[key]
            else:
                # Default 404 response
                response = Mock()
                response.status_code = 404
                response.text = "Not Found"
                response.json.side_effect = ValueError("No JSON object could be decoded")
                return response
        
        requests_mock.request.side_effect = mock_request
        requests_mock.get.side_effect = lambda url, **kwargs: mock_request('GET', url, **kwargs)
        requests_mock.post.side_effect = lambda url, **kwargs: mock_request('POST', url, **kwargs)
        requests_mock.put.side_effect = lambda url, **kwargs: mock_request('PUT', url, **kwargs)
        requests_mock.delete.side_effect = lambda url, **kwargs: mock_request('DELETE', url, **kwargs)
        
        return requests_mock


class DatabaseMocker:
    """Mock database operations for testing"""
    
    def __init__(self):
        self.data = {}
        self.query_history = []
    
    def add_table_data(self, table: str, rows: List[Dict]):
        """Add mock data for a table"""
        self.data[table] = rows.copy()
    
    def create_connection_mock(self) -> Mock:
        """Create mock database connection"""
        connection_mock = Mock()
        cursor_mock = Mock()
        
        def mock_execute(query, params=None):
            self.query_history.append({
                'query': query,
                'params': params,
                'timestamp': time.time()
            })
            
            # Simple query parsing for testing
            query_lower = query.lower().strip()
            
            if query_lower.startswith('select'):
                # Mock SELECT results
                if 'from' in query_lower:
                    table_part = query_lower.split('from')[1].strip().split()[0]
                    table_data = self.data.get(table_part, [])
                    cursor_mock.fetchall.return_value = table_data
                    cursor_mock.fetchone.return_value = table_data[0] if table_data else None
                    cursor_mock.rowcount = len(table_data)
            elif query_lower.startswith(('insert', 'update', 'delete')):
                # Mock modification results
                cursor_mock.rowcount = 1
            
        cursor_mock.execute.side_effect = mock_execute
        cursor_mock.fetchall.return_value = []
        cursor_mock.fetchone.return_value = None
        cursor_mock.rowcount = 0
        
        connection_mock.cursor.return_value = cursor_mock
        connection_mock.commit.return_value = None
        connection_mock.rollback.return_value = None
        connection_mock.close.return_value = None
        
        return connection_mock


# Pre-configured mock factories
def create_standard_mocks() -> Dict[str, Mock]:
    """Create standard set of mocks used across tests"""
    mocks = {}
    
    # File system mocks
    fs_mocker = FileSystemMocker()
    _mock_registry.add_reset_callback(fs_mocker.cleanup)
    
    # OOXML processor
    mocks['ooxml_processor'] = OOXMLProcessorMocker.create_advanced_mock()
    
    # Git repository
    mocks['git_repo'] = GitMocker.create_repo_mock()
    
    # HTTP requests
    http_mocker = HTTPMocker()
    http_mocker.add_response('https://api.stylestack.dev/health', 'GET', 200, {'status': 'ok'})
    http_mocker.add_response('https://api.stylestack.dev/tokens', 'GET', 200, {
        'tokens': {'brand.primary': '#007acc', 'typography.family': 'Segoe UI'}
    })
    mocks['requests'] = http_mocker.create_requests_mock()
    
    # Database connection
    db_mocker = DatabaseMocker()
    db_mocker.add_table_data('templates', [
        {'id': 1, 'name': 'corporate_presentation', 'format': 'potx'},
        {'id': 2, 'name': 'financial_report', 'format': 'dotx'}
    ])
    mocks['database'] = db_mocker.create_connection_mock()
    
    # Register all mocks
    for name, mock_obj in mocks.items():
        _mock_registry.register_mock(name, mock_obj)
    
    return mocks


def get_mock(name: str) -> Optional[Mock]:
    """Get a registered mock by name"""
    return _mock_registry.get_mock(name)


def reset_all_mocks():
    """Reset all registered mocks"""
    _mock_registry.reset_mock()


def get_mock_call_history(name: str) -> List[Dict]:
    """Get call history for a specific mock"""
    return _mock_registry.get_call_history(name)


# Context managers for temporary mocking
class mock_external_dependencies:
    """Context manager to temporarily mock external dependencies"""
    
    def __init__(self, dependencies: List[str] = None):
        self.dependencies = dependencies or ['requests', 'git', 'database']
        self.patches = {}
        self.mocks = {}
    
    def __enter__(self):
        # Create and apply patches
        standard_mocks = create_standard_mocks()
        
        for dep in self.dependencies:
            if dep in standard_mocks:
                self.mocks[dep] = standard_mocks[dep]
                
                if dep == 'requests':
                    self.patches[dep] = patch('requests', self.mocks[dep])
                elif dep == 'git':
                    self.patches[dep] = patch('git.Repo', return_value=self.mocks[dep])
                elif dep == 'database':
                    self.patches[dep] = patch('sqlite3.connect', return_value=self.mocks[dep])
                
                if dep in self.patches:
                    self.patches[dep].__enter__()
        
        return self.mocks
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Remove patches in reverse order
        for patch_obj in reversed(list(self.patches.values())):
            patch_obj.__exit__(exc_type, exc_val, exc_tb)
        
        # Reset mocks
        reset_all_mocks()


if __name__ == '__main__':
    # Demonstrate the mock system
    print("Testing Centralized Mock System...")
    
    # Create standard mocks
    mocks = create_standard_mocks()
    print(f"✅ Created {len(mocks)} standard mocks")
    
    # Test OOXML processor mock
    processor = get_mock('ooxml_processor')
    processor.load_template('/test/template.potx')
    variables = processor.extract_variables()
    print(f"✅ OOXML processor mock: extracted {len(variables)} variables")
    
    # Test HTTP mock
    requests_mock = get_mock('requests')
    response = requests_mock.get('https://api.stylestack.dev/health')
    print(f"✅ HTTP mock: status {response.status_code}, response {response.json()}")
    
    # Test call history
    history = get_mock_call_history('ooxml_processor')
    print(f"✅ Call history: {len(history)} calls recorded")
    
    # Reset and verify
    reset_all_mocks()
    print("✅ Mock system reset successfully")
    
    print("✅ Centralized mock system operational")