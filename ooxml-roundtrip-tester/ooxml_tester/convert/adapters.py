"""Document conversion adapters for different platforms."""

import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass
from abc import ABC, abstractmethod

from ..core.config import Config
from ..core.exceptions import ConversionError, PlatformError
from ..core.utils import normalize_path, create_temp_directory


@dataclass
class AdapterResult:
    """Result of a conversion operation."""
    success: bool
    output_file: Path
    error_message: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class ConversionAdapter(ABC):
    """Base class for document conversion adapters."""
    
    def __init__(self, config: Config):
        """Initialize adapter with configuration."""
        self.config = config
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Name of the platform this adapter supports."""
        pass
    
    @abstractmethod
    def convert_document(self, input_file: Path, output_file: Path, 
                        target_format: str, timeout: int = 120) -> AdapterResult:
        """Convert document to target format."""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        pass
    
    def cleanup(self):
        """Clean up any resources used by the adapter."""
        pass


class LibreOfficeAdapter(ConversionAdapter):
    """Adapter for LibreOffice headless conversion."""
    
    @property
    def platform_name(self) -> str:
        return "LibreOffice"
    
    def convert_document(self, input_file: Path, output_file: Path, 
                        target_format: str, timeout: int = 120) -> AdapterResult:
        """Convert document using LibreOffice headless mode."""
        input_file = normalize_path(input_file)
        output_file = normalize_path(output_file)
        
        if not input_file.exists():
            return AdapterResult(
                success=False,
                output_file=output_file,
                error_message=f"Input file does not exist: {input_file}"
            )
        
        # Get LibreOffice executable
        soffice_path = self._get_soffice_path()
        if not soffice_path:
            return AdapterResult(
                success=False,
                output_file=output_file,
                error_message="LibreOffice executable not found"
            )
        
        try:
            # Create output directory
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create temporary directory for conversion
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # LibreOffice command for headless conversion
                cmd = [
                    str(soffice_path),
                    '--headless',
                    '--convert-to', target_format,
                    '--outdir', str(temp_path),
                    str(input_file)
                ]
                
                # Execute conversion
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                if result.returncode != 0:
                    return AdapterResult(
                        success=False,
                        output_file=output_file,
                        error_message=f"LibreOffice conversion failed: {result.stderr}"
                    )
                
                # Find the converted file
                expected_name = f"{input_file.stem}.{target_format}"
                converted_file = temp_path / expected_name
                
                if not converted_file.exists():
                    # Try to find any file with the target extension
                    converted_files = list(temp_path.glob(f"*.{target_format}"))
                    if converted_files:
                        converted_file = converted_files[0]
                    else:
                        return AdapterResult(
                            success=False,
                            output_file=output_file,
                            error_message=f"Converted file not found: {expected_name}"
                        )
                
                # Move converted file to final location
                converted_file.rename(output_file)
                
                return AdapterResult(
                    success=True,
                    output_file=output_file
                )
                
        except subprocess.TimeoutExpired:
            return AdapterResult(
                success=False,
                output_file=output_file,
                error_message=f"LibreOffice conversion timeout after {timeout} seconds"
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                output_file=output_file,
                error_message=f"LibreOffice conversion error: {str(e)}"
            )
    
    def _get_soffice_path(self) -> Optional[Path]:
        """Get path to LibreOffice soffice executable."""
        from .platforms import LibreOfficePlatform
        platform = LibreOfficePlatform()
        return platform.get_executable_path()
    
    def get_supported_formats(self) -> List[str]:
        """Get list of formats supported by LibreOffice."""
        return [
            # Writer formats
            'odt', 'docx', 'doc', 'rtf', 'txt', 'html', 'pdf',
            # Calc formats  
            'ods', 'xlsx', 'xls', 'csv', 'html', 'pdf',
            # Impress formats
            'odp', 'pptx', 'ppt', 'pdf',
            # Other formats
            'odg', 'svg', 'eps'
        ]


class OfficeAdapter(ConversionAdapter):
    """Adapter for Microsoft Office automation."""
    
    @property
    def platform_name(self) -> str:
        return "Microsoft Office"
    
    def convert_document(self, input_file: Path, output_file: Path, 
                        target_format: str, timeout: int = 120) -> AdapterResult:
        """Convert document using Microsoft Office automation."""
        input_file = normalize_path(input_file)
        output_file = normalize_path(output_file)
        
        if not input_file.exists():
            return AdapterResult(
                success=False,
                output_file=output_file,
                error_message=f"Input file does not exist: {input_file}"
            )
        
        system = platform.system()
        
        if system == "Windows":
            return self._convert_windows_com(input_file, output_file, target_format, timeout)
        elif system == "Darwin":
            return self._convert_macos_applescript(input_file, output_file, target_format, timeout)
        else:
            return AdapterResult(
                success=False,
                output_file=output_file,
                error_message="Microsoft Office not supported on this platform"
            )
    
    def _convert_windows_com(self, input_file: Path, output_file: Path, 
                           target_format: str, timeout: int) -> AdapterResult:
        """Convert using Windows COM automation."""
        try:
            import win32com.client
            import pythoncom
            
            # Initialize COM
            pythoncom.CoInitialize()
            
            try:
                # Determine application based on file format
                input_ext = input_file.suffix.lower()
                app_name = self._get_office_app_for_format(input_ext)
                
                if app_name == "Word":
                    return self._convert_word_com(input_file, output_file, target_format)
                elif app_name == "PowerPoint":
                    return self._convert_powerpoint_com(input_file, output_file, target_format)
                elif app_name == "Excel":
                    return self._convert_excel_com(input_file, output_file, target_format)
                else:
                    return AdapterResult(
                        success=False,
                        output_file=output_file,
                        error_message=f"Unsupported format for Office: {input_ext}"
                    )
                    
            finally:
                pythoncom.CoUninitialize()
                
        except ImportError:
            return AdapterResult(
                success=False,
                output_file=output_file,
                error_message="win32com not available for Windows COM automation"
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                output_file=output_file,
                error_message=f"Windows COM conversion error: {str(e)}"
            )
    
    def _convert_word_com(self, input_file: Path, output_file: Path, target_format: str) -> AdapterResult:
        """Convert using Word COM automation."""
        import win32com.client
        
        word_app = None
        try:
            word_app = win32com.client.Dispatch("Word.Application")
            word_app.Visible = False
            
            # Open document
            doc = word_app.Documents.Open(str(input_file))
            
            # Create output directory
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save in target format
            if target_format.lower() == 'pdf':
                doc.SaveAs2(str(output_file), FileFormat=17)  # wdFormatPDF
            elif target_format.lower() == 'docx':
                doc.SaveAs2(str(output_file), FileFormat=16)  # wdFormatXMLDocument
            else:
                doc.SaveAs2(str(output_file))
            
            doc.Close()
            
            return AdapterResult(
                success=True,
                output_file=output_file
            )
            
        finally:
            if word_app:
                word_app.Quit()
    
    def _convert_powerpoint_com(self, input_file: Path, output_file: Path, target_format: str) -> AdapterResult:
        """Convert using PowerPoint COM automation."""
        import win32com.client
        
        ppt_app = None
        try:
            ppt_app = win32com.client.Dispatch("PowerPoint.Application")
            ppt_app.Visible = 1
            
            # Open presentation
            pres = ppt_app.Presentations.Open(str(input_file))
            
            # Create output directory
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save in target format
            if target_format.lower() == 'pdf':
                pres.SaveAs(str(output_file), 32)  # ppSaveAsPDF
            elif target_format.lower() == 'pptx':
                pres.SaveAs(str(output_file), 24)  # ppSaveAsOpenXMLPresentation
            else:
                pres.SaveAs(str(output_file))
            
            pres.Close()
            
            return AdapterResult(
                success=True,
                output_file=output_file
            )
            
        finally:
            if ppt_app:
                ppt_app.Quit()
    
    def _convert_excel_com(self, input_file: Path, output_file: Path, target_format: str) -> AdapterResult:
        """Convert using Excel COM automation."""
        import win32com.client
        
        excel_app = None
        try:
            excel_app = win32com.client.Dispatch("Excel.Application")
            excel_app.Visible = False
            
            # Open workbook
            wb = excel_app.Workbooks.Open(str(input_file))
            
            # Create output directory
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save in target format
            if target_format.lower() == 'pdf':
                wb.SaveAs(str(output_file), 57)  # xlTypePDF
            elif target_format.lower() == 'xlsx':
                wb.SaveAs(str(output_file), 51)  # xlOpenXMLWorkbook
            else:
                wb.SaveAs(str(output_file))
            
            wb.Close()
            
            return AdapterResult(
                success=True,
                output_file=output_file
            )
            
        finally:
            if excel_app:
                excel_app.Quit()
    
    def _convert_macos_applescript(self, input_file: Path, output_file: Path, 
                                 target_format: str, timeout: int) -> AdapterResult:
        """Convert using macOS AppleScript automation."""
        try:
            # Determine application
            input_ext = input_file.suffix.lower()
            app_name = self._get_office_app_for_format(input_ext)
            
            if app_name == "Word":
                return self._convert_word_applescript(input_file, output_file, target_format, timeout)
            elif app_name == "PowerPoint":
                return self._convert_powerpoint_applescript(input_file, output_file, target_format, timeout)
            elif app_name == "Excel":
                return self._convert_excel_applescript(input_file, output_file, target_format, timeout)
            else:
                return AdapterResult(
                    success=False,
                    output_file=output_file,
                    error_message=f"Unsupported format for Office: {input_ext}"
                )
                
        except Exception as e:
            return AdapterResult(
                success=False,
                output_file=output_file,
                error_message=f"AppleScript conversion error: {str(e)}"
            )
    
    def _convert_word_applescript(self, input_file: Path, output_file: Path, 
                                target_format: str, timeout: int) -> AdapterResult:
        """Convert using Word AppleScript."""
        script = f'''
        tell application "Microsoft Word"
            open "{input_file}"
            save as active document file name "{output_file}"
            close active document
        end tell
        '''
        
        return self._execute_applescript(script, output_file, timeout)
    
    def _convert_powerpoint_applescript(self, input_file: Path, output_file: Path, 
                                      target_format: str, timeout: int) -> AdapterResult:
        """Convert using PowerPoint AppleScript."""
        script = f'''
        tell application "Microsoft PowerPoint"
            open "{input_file}"
            save active presentation in "{output_file}"
            close active presentation
        end tell
        '''
        
        return self._execute_applescript(script, output_file, timeout)
    
    def _convert_excel_applescript(self, input_file: Path, output_file: Path, 
                                 target_format: str, timeout: int) -> AdapterResult:
        """Convert using Excel AppleScript."""
        script = f'''
        tell application "Microsoft Excel"
            open "{input_file}"
            save active workbook in "{output_file}"
            close active workbook
        end tell
        '''
        
        return self._execute_applescript(script, output_file, timeout)
    
    def _execute_applescript(self, script: str, output_file: Path, timeout: int) -> AdapterResult:
        """Execute AppleScript and return result."""
        try:
            # Create output directory
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                return AdapterResult(
                    success=True,
                    output_file=output_file
                )
            else:
                return AdapterResult(
                    success=False,
                    output_file=output_file,
                    error_message=f"AppleScript error: {result.stderr}"
                )
                
        except subprocess.TimeoutExpired:
            return AdapterResult(
                success=False,
                output_file=output_file,
                error_message=f"AppleScript timeout after {timeout} seconds"
            )
    
    def convert_via_applescript(self, input_file: Path, output_file: Path, 
                              application: str) -> AdapterResult:
        """Convert via AppleScript (for testing)."""
        return self._convert_macos_applescript(input_file, output_file, 
                                             output_file.suffix.lstrip('.'), 120)
    
    def open_document(self, file_path: str, application: str):
        """Open document in specified application (for testing)."""
        system = platform.system()
        
        if system == "Windows":
            try:
                import win32com.client
                if application.lower() == "word":
                    app = win32com.client.Dispatch("Word.Application")
                    return app.Documents.Open(file_path)
                elif application.lower() == "powerpoint":
                    app = win32com.client.Dispatch("PowerPoint.Application")
                    return app.Presentations.Open(file_path)
                elif application.lower() == "excel":
                    app = win32com.client.Dispatch("Excel.Application")
                    return app.Workbooks.Open(file_path)
            except ImportError:
                return None
        
        return None
    
    def get_process_manager(self):
        """Get process manager for Office applications."""
        class ProcessManager:
            def cleanup_processes(self):
                # Implementation would cleanup Office processes
                pass
            
            def kill_hanging_processes(self):
                # Implementation would kill hanging Office processes
                pass
        
        return ProcessManager()
    
    def _get_office_app_for_format(self, file_extension: str) -> str:
        """Get Office application name for file format."""
        word_formats = ['.docx', '.doc', '.rtf', '.txt']
        powerpoint_formats = ['.pptx', '.ppt']
        excel_formats = ['.xlsx', '.xls', '.csv']
        
        if file_extension in word_formats:
            return "Word"
        elif file_extension in powerpoint_formats:
            return "PowerPoint"
        elif file_extension in excel_formats:
            return "Excel"
        else:
            return "Unknown"
    
    def get_supported_formats(self) -> List[str]:
        """Get list of formats supported by Microsoft Office."""
        return [
            # Word formats
            'docx', 'doc', 'rtf', 'txt', 'pdf',
            # PowerPoint formats
            'pptx', 'ppt', 'pdf',
            # Excel formats
            'xlsx', 'xls', 'csv', 'pdf'
        ]
    
    def get_supported_applications(self) -> List[str]:
        """Get list of supported Office applications."""
        return ['word', 'powerpoint', 'excel']


class GoogleAdapter(ConversionAdapter):
    """Adapter for Google Workspace API conversion."""
    
    @property
    def platform_name(self) -> str:
        return "Google Workspace"
    
    def convert_document(self, input_file: Path, output_file: Path, 
                        target_format: str, timeout: int = 120) -> AdapterResult:
        """Convert document using Google Workspace API."""
        # This would require Google Drive API implementation
        # For now, return not implemented
        return AdapterResult(
            success=False,
            output_file=output_file,
            error_message="Google Workspace conversion not yet implemented"
        )
    
    def get_supported_formats(self) -> List[str]:
        """Get list of formats supported by Google Workspace."""
        return [
            'docx', 'odt', 'pdf', 'txt', 'html',  # Docs
            'xlsx', 'ods', 'csv', 'pdf',          # Sheets
            'pptx', 'odp', 'pdf', 'txt'           # Slides
        ]