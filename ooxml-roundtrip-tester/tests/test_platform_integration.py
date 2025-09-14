"""Tests for platform integration and document conversion."""

import pytest
import tempfile
import platform
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from ooxml_tester.convert.engine import ConversionEngine
from ooxml_tester.convert.platforms import (
    Platform, MicrosoftOfficePlatform, LibreOfficePlatform, GoogleWorkspacePlatform
)
from ooxml_tester.convert.adapters import (
    ConversionAdapter, OfficeAdapter, LibreOfficeAdapter, GoogleAdapter
)
from ooxml_tester.core.config import Config
from ooxml_tester.core.exceptions import ConversionError, PlatformError
from ooxml_tester.probe.generator import ProbeGenerator


class TestPlatformDetection:
    """Test platform detection and Office suite discovery."""
    
    @pytest.fixture
    def conversion_engine(self):
        """Create conversion engine for testing."""
        config = Config()
        return ConversionEngine(config)
    
    def test_platform_detection(self, conversion_engine):
        """Test automatic platform detection."""
        detected_platform = conversion_engine.detect_platform()
        
        current_system = platform.system()
        if current_system == "Windows":
            assert "windows" in detected_platform.lower()
        elif current_system == "Darwin":
            assert "macos" in detected_platform.lower() or "darwin" in detected_platform.lower()
        else:
            assert "linux" in detected_platform.lower()
    
    def test_office_suite_discovery(self, conversion_engine):
        """Test automatic Office suite discovery."""
        discovered_suites = conversion_engine.discover_office_suites()
        
        # Should return a dictionary of available suites
        assert isinstance(discovered_suites, dict)
        
        # Each suite should have platform info
        for suite_name, suite_info in discovered_suites.items():
            assert "available" in suite_info
            assert "path" in suite_info
            assert "version" in suite_info
    
    @patch('ooxml_tester.convert.platforms.find_executable')
    def test_libreoffice_detection(self, mock_find_executable, conversion_engine):
        """Test LibreOffice detection."""
        # Mock LibreOffice being found
        mock_find_executable.return_value = Path("/usr/bin/libreoffice")
        
        libreoffice_platform = LibreOfficePlatform()
        is_available = libreoffice_platform.is_available()
        
        assert is_available
        mock_find_executable.assert_called()
    
    @patch('ooxml_tester.convert.platforms.find_executable')
    def test_libreoffice_not_found(self, mock_find_executable, conversion_engine):
        """Test LibreOffice not available."""
        # Mock LibreOffice not found
        mock_find_executable.return_value = None
        
        libreoffice_platform = LibreOfficePlatform()
        is_available = libreoffice_platform.is_available()
        
        assert not is_available
    
    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific test")
    def test_microsoft_office_macos_detection(self, conversion_engine):
        """Test Microsoft Office detection on macOS."""
        office_platform = MicrosoftOfficePlatform()
        
        # Check if Word app exists
        word_path = Path("/Applications/Microsoft Word.app")
        if word_path.exists():
            assert office_platform.is_available()
        else:
            assert not office_platform.is_available()
    
    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific test")
    def test_microsoft_office_windows_detection(self, conversion_engine):
        """Test Microsoft Office detection on Windows."""
        office_platform = MicrosoftOfficePlatform()
        
        # This would require COM interface testing
        # For now, just test the platform creation
        assert office_platform is not None


class TestLibreOfficeIntegration:
    """Test LibreOffice UNO API integration."""
    
    @pytest.fixture
    def libreoffice_adapter(self):
        """Create LibreOffice adapter for testing."""
        config = Config()
        return LibreOfficeAdapter(config)
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)
    
    @pytest.fixture
    def sample_docx(self, temp_dir):
        """Create a sample DOCX file for testing."""
        probe_generator = ProbeGenerator(Config())
        return probe_generator.generate_docx_probe(
            output_dir=temp_dir,
            features=['themes', 'styles'],
            filename='test_document.docx'
        )
    
    def test_libreoffice_adapter_initialization(self, libreoffice_adapter):
        """Test LibreOffice adapter initialization."""
        assert libreoffice_adapter is not None
        assert libreoffice_adapter.platform_name == "LibreOffice"
    
    @patch('ooxml_tester.convert.adapters.subprocess.run')
    @patch('ooxml_tester.convert.adapters.LibreOfficeAdapter._get_soffice_path')
    def test_headless_conversion_docx_to_odt(self, mock_get_path, mock_subprocess, libreoffice_adapter, sample_docx, temp_dir):
        """Test headless DOCX to ODT conversion."""
        # Mock LibreOffice executable found
        mock_get_path.return_value = Path("/usr/bin/soffice")
        
        # Mock subprocess call and create the expected output file
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")
        
        output_file = temp_dir / "converted.odt"
        
        # Create the file that LibreOffice would create
        temp_converted = temp_dir / f"{sample_docx.stem}.odt"
        temp_converted.touch()
        
        with patch('tempfile.TemporaryDirectory') as mock_temp:
            mock_temp.return_value.__enter__.return_value = str(temp_dir)
            mock_temp.return_value.__exit__.return_value = None
            
            result = libreoffice_adapter.convert_document(
                input_file=sample_docx,
                output_file=output_file,
                target_format="odt"
            )
        
        assert result.success
        assert result.output_file == output_file
        mock_subprocess.assert_called_once()
    
    @patch('ooxml_tester.convert.adapters.subprocess.run')
    @patch('ooxml_tester.convert.adapters.LibreOfficeAdapter._get_soffice_path')
    def test_headless_conversion_odt_to_docx(self, mock_get_path, mock_subprocess, libreoffice_adapter, temp_dir):
        """Test headless ODT to DOCX conversion."""
        # Mock LibreOffice executable found
        mock_get_path.return_value = Path("/usr/bin/soffice")
        
        # Create mock ODT file
        odt_file = temp_dir / "test.odt"
        odt_file.write_bytes(b"mock odt content")
        
        # Mock subprocess call
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")
        
        output_file = temp_dir / "converted.docx"
        
        # Create the file that LibreOffice would create
        temp_converted = temp_dir / f"{odt_file.stem}.docx"
        temp_converted.touch()
        
        with patch('tempfile.TemporaryDirectory') as mock_temp:
            mock_temp.return_value.__enter__.return_value = str(temp_dir)
            mock_temp.return_value.__exit__.return_value = None
            
            result = libreoffice_adapter.convert_document(
                input_file=odt_file,
                output_file=output_file,
                target_format="docx"
            )
        
        assert result.success
        assert result.output_file == output_file
        mock_subprocess.assert_called_once()
    
    @patch('ooxml_tester.convert.adapters.subprocess.run')
    def test_conversion_timeout(self, mock_subprocess, libreoffice_adapter, sample_docx, temp_dir):
        """Test conversion timeout handling."""
        # Mock subprocess timeout
        from subprocess import TimeoutExpired
        mock_subprocess.side_effect = TimeoutExpired("soffice", 30)
        
        output_file = temp_dir / "converted.odt"
        
        # LibreOffice adapter returns AdapterResult, not raising exception
        result = libreoffice_adapter.convert_document(
            input_file=sample_docx,
            output_file=output_file,
            target_format="odt",
            timeout=30
        )
        
        assert not result.success
        assert "timeout" in result.error_message.lower()
    
    @patch('ooxml_tester.convert.adapters.subprocess.run')
    def test_conversion_failure(self, mock_subprocess, libreoffice_adapter, sample_docx, temp_dir):
        """Test conversion failure handling."""
        # Mock subprocess failure
        mock_subprocess.return_value = Mock(
            returncode=1, 
            stdout="", 
            stderr="Conversion failed"
        )
        
        output_file = temp_dir / "converted.odt"
        
        result = libreoffice_adapter.convert_document(
            input_file=sample_docx,
            output_file=output_file,
            target_format="odt"
        )
        
        assert not result.success
        assert "Conversion failed" in result.error_message
    
    def test_supported_formats(self, libreoffice_adapter):
        """Test that LibreOffice adapter supports expected formats."""
        supported_formats = libreoffice_adapter.get_supported_formats()
        
        # LibreOffice should support these key formats
        expected_formats = [
            'docx', 'odt', 'doc', 'rtf',  # Word formats
            'pptx', 'odp', 'ppt',         # PowerPoint formats
            'xlsx', 'ods', 'xls', 'csv'   # Excel formats
        ]
        
        for format in expected_formats:
            assert format in supported_formats


class TestMicrosoftOfficeIntegration:
    """Test Microsoft Office automation."""
    
    @pytest.fixture
    def office_adapter(self):
        """Create Office adapter for testing."""
        config = Config()
        return OfficeAdapter(config)
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)
    
    def test_office_adapter_initialization(self, office_adapter):
        """Test Office adapter initialization."""
        assert office_adapter is not None
        assert office_adapter.platform_name == "Microsoft Office"
    
    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows COM test")
    @patch('ooxml_tester.convert.adapters.win32com.client.Dispatch')
    def test_windows_com_automation(self, mock_dispatch, office_adapter):
        """Test Windows COM automation."""
        # Mock Word application
        mock_word_app = Mock()
        mock_document = Mock()
        mock_word_app.Documents.Open.return_value = mock_document
        mock_dispatch.return_value = mock_word_app
        
        # Test opening a document
        result = office_adapter.open_document("test.docx", "word")
        
        assert result is not None
        mock_dispatch.assert_called_with("Word.Application")
        mock_word_app.Documents.Open.assert_called_once()
    
    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS AppleScript test")
    @patch('ooxml_tester.convert.adapters.subprocess.run')
    def test_macos_applescript_automation(self, mock_subprocess, office_adapter, temp_dir):
        """Test macOS AppleScript automation."""
        # Mock AppleScript execution
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")
        
        sample_file = temp_dir / "test.docx"
        sample_file.write_bytes(b"mock docx content")
        
        result = office_adapter.convert_via_applescript(
            input_file=sample_file,
            output_file=temp_dir / "converted.pdf",
            application="Microsoft Word"
        )
        
        assert result.success
        mock_subprocess.assert_called_once()
    
    def test_process_management(self, office_adapter):
        """Test Office process management."""
        # Test process cleanup functionality
        process_manager = office_adapter.get_process_manager()
        
        assert process_manager is not None
        assert hasattr(process_manager, 'cleanup_processes')
        assert hasattr(process_manager, 'kill_hanging_processes')
    
    def test_supported_applications(self, office_adapter):
        """Test supported Microsoft Office applications."""
        supported_apps = office_adapter.get_supported_applications()
        
        expected_apps = ['word', 'powerpoint', 'excel']
        for app in expected_apps:
            assert app in supported_apps


class TestConversionWorkflow:
    """Test complete conversion workflows."""
    
    @pytest.fixture
    def conversion_engine(self):
        """Create conversion engine for testing."""
        config = Config()
        return ConversionEngine(config)
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)
    
    @pytest.fixture
    def sample_docx(self, temp_dir):
        """Create a sample DOCX file for testing."""
        probe_generator = ProbeGenerator(Config())
        return probe_generator.generate_docx_probe(
            output_dir=temp_dir,
            features=['themes', 'styles', 'tables'],
            filename='workflow_test.docx'
        )
    
    @patch('ooxml_tester.convert.engine.ConversionEngine.get_platform')
    @patch('ooxml_tester.convert.engine.ConversionEngine.get_adapter')
    def test_round_trip_workflow_creation(self, mock_get_adapter, mock_get_platform, conversion_engine, sample_docx, temp_dir):
        """Test creation of round-trip conversion workflow."""
        # Mock platform and adapter
        mock_platform = Mock()
        mock_adapter = Mock()
        mock_get_platform.return_value = mock_platform
        mock_get_adapter.return_value = mock_adapter
        
        workflow = conversion_engine.create_round_trip_workflow(
            input_file=sample_docx,
            platforms=['libreoffice'],
            output_dir=temp_dir
        )
        
        assert workflow is not None
        assert len(workflow.steps) > 0
        # Use resolve() to handle path normalization differences
        assert workflow.input_file.resolve() == sample_docx.resolve()
    
    @patch('ooxml_tester.convert.adapters.LibreOfficeAdapter.convert_document')
    def test_ooxml_to_odf_to_ooxml_cycle(self, mock_convert, conversion_engine, sample_docx, temp_dir):
        """Test complete OOXML → ODF → OOXML round-trip cycle."""
        # Mock successful conversions
        def mock_conversion_side_effect(*args, **kwargs):
            result = Mock()
            result.success = True
            result.output_file = kwargs.get('output_file')
            result.error_message = None
            return result
        
        mock_convert.side_effect = mock_conversion_side_effect
        
        # Execute round-trip
        result = conversion_engine.execute_round_trip(
            input_file=sample_docx,
            platforms=['libreoffice'],
            output_dir=temp_dir
        )
        
        assert result.success
        assert len(result.conversion_steps) > 0
        # Should have converted DOCX → ODT → DOCX
        assert mock_convert.call_count >= 2
    
    def test_multi_platform_workflow(self, conversion_engine, sample_docx, temp_dir):
        """Test workflow with multiple platforms."""
        workflow = conversion_engine.create_round_trip_workflow(
            input_file=sample_docx,
            platforms=['libreoffice', 'office'],
            output_dir=temp_dir
        )
        
        # Should create steps for both platforms
        platform_names = [step.platform for step in workflow.steps]
        assert 'libreoffice' in platform_names
        assert 'office' in platform_names
    
    def test_parallel_conversion_support(self, conversion_engine):
        """Test parallel conversion capability."""
        parallel_manager = conversion_engine.get_parallel_manager()
        
        assert parallel_manager is not None
        assert hasattr(parallel_manager, 'execute_parallel')
        assert hasattr(parallel_manager, 'max_workers')
    
    def test_conversion_result_tracking(self, conversion_engine, sample_docx, temp_dir):
        """Test conversion result tracking and metrics."""
        # Create a workflow
        workflow = conversion_engine.create_round_trip_workflow(
            input_file=sample_docx,
            platforms=['libreoffice'],
            output_dir=temp_dir
        )
        
        # Should track conversion metrics
        assert hasattr(workflow, 'start_time')
        assert hasattr(workflow, 'track_conversion_step')
        assert hasattr(workflow, 'get_metrics')


class TestErrorHandling:
    """Test error handling and recovery mechanisms."""
    
    @pytest.fixture
    def conversion_engine(self):
        """Create conversion engine for testing."""
        config = Config()
        return ConversionEngine(config)
    
    def test_platform_unavailable_error(self, conversion_engine):
        """Test error when platform is unavailable."""
        with pytest.raises(PlatformError) as exc_info:
            conversion_engine.get_platform("nonexistent_platform")
        
        assert "not available" in str(exc_info.value).lower()
    
    def test_conversion_retry_mechanism(self, conversion_engine):
        """Test conversion retry on failure."""
        retry_manager = conversion_engine.get_retry_manager()
        
        assert retry_manager is not None
        assert hasattr(retry_manager, 'max_retries')
        assert hasattr(retry_manager, 'retry_delay')
        assert hasattr(retry_manager, 'execute_with_retry')
    
    def test_file_cleanup_on_error(self, conversion_engine):
        """Test file cleanup when conversion fails."""
        cleanup_manager = conversion_engine.get_cleanup_manager()
        
        assert cleanup_manager is not None
        assert hasattr(cleanup_manager, 'cleanup_temp_files')
        assert hasattr(cleanup_manager, 'register_temp_file')
    
    def test_process_timeout_handling(self, conversion_engine):
        """Test handling of process timeouts."""
        timeout_manager = conversion_engine.get_timeout_manager()
        
        assert timeout_manager is not None
        assert hasattr(timeout_manager, 'default_timeout')
        assert hasattr(timeout_manager, 'kill_on_timeout')


class TestPerformanceAndScaling:
    """Test performance and scaling capabilities."""
    
    @pytest.fixture
    def conversion_engine(self):
        """Create conversion engine for testing."""
        config = Config()
        return ConversionEngine(config)
    
    def test_batch_conversion_capability(self, conversion_engine):
        """Test batch conversion of multiple files."""
        batch_manager = conversion_engine.get_batch_manager()
        
        assert batch_manager is not None
        assert hasattr(batch_manager, 'process_batch')
        assert hasattr(batch_manager, 'max_concurrent_conversions')
    
    def test_memory_management(self, conversion_engine):
        """Test memory management during conversions."""
        memory_manager = conversion_engine.get_memory_manager()
        
        assert memory_manager is not None
        assert hasattr(memory_manager, 'monitor_memory_usage')
        assert hasattr(memory_manager, 'cleanup_on_memory_pressure')
    
    def test_progress_tracking(self, conversion_engine):
        """Test conversion progress tracking."""
        progress_tracker = conversion_engine.get_progress_tracker()
        
        assert progress_tracker is not None
        assert hasattr(progress_tracker, 'update_progress')
        assert hasattr(progress_tracker, 'get_completion_percentage')