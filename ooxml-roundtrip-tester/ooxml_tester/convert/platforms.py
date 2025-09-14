"""Platform detection and Office suite discovery."""

import platform
import subprocess
from pathlib import Path
from typing import Optional
from abc import ABC, abstractmethod

from ..core.utils import find_executable
from ..core.exceptions import PlatformError


class Platform(ABC):
    """Base class for Office platform detection."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Platform name."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if platform is available on current system."""
        pass
    
    @abstractmethod
    def get_executable_path(self) -> Optional[Path]:
        """Get path to main executable."""
        pass
    
    @abstractmethod
    def get_version(self) -> Optional[str]:
        """Get platform version."""
        pass


class MicrosoftOfficePlatform(Platform):
    """Microsoft Office platform detection."""
    
    @property
    def name(self) -> str:
        return "Microsoft Office"
    
    def is_available(self) -> bool:
        """Check if Microsoft Office is available."""
        system = platform.system()
        
        if system == "Windows":
            return self._check_windows_office()
        elif system == "Darwin":  # macOS
            return self._check_macos_office()
        else:
            # Microsoft Office not available on Linux
            return False
    
    def _check_windows_office(self) -> bool:
        """Check for Microsoft Office on Windows."""
        try:
            # Try to import COM interface
            import win32com.client
            
            # Try to create Word application
            try:
                word_app = win32com.client.Dispatch("Word.Application")
                word_app.Quit()
                return True
            except:
                pass
            
            # Check common installation paths
            office_paths = [
                r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
                r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE",
                r"C:\Program Files\Microsoft Office\Office16\WINWORD.EXE",
                r"C:\Program Files (x86)\Microsoft Office\Office16\WINWORD.EXE"
            ]
            
            for office_path in office_paths:
                if Path(office_path).exists():
                    return True
            
            return False
            
        except ImportError:
            # win32com not available
            return False
    
    def _check_macos_office(self) -> bool:
        """Check for Microsoft Office on macOS."""
        office_apps = [
            "/Applications/Microsoft Word.app",
            "/Applications/Microsoft PowerPoint.app",
            "/Applications/Microsoft Excel.app"
        ]
        
        # Check if any Office app exists
        for app_path in office_apps:
            if Path(app_path).exists():
                return True
        
        return False
    
    def get_executable_path(self) -> Optional[Path]:
        """Get path to Microsoft Office executable."""
        if not self.is_available():
            return None
        
        system = platform.system()
        
        if system == "Windows":
            # Return Word as primary executable
            office_paths = [
                r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
                r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE",
                r"C:\Program Files\Microsoft Office\Office16\WINWORD.EXE",
                r"C:\Program Files (x86)\Microsoft Office\Office16\WINWORD.EXE"
            ]
            
            for office_path in office_paths:
                path = Path(office_path)
                if path.exists():
                    return path
        
        elif system == "Darwin":
            # Return Word app on macOS
            word_app = Path("/Applications/Microsoft Word.app")
            if word_app.exists():
                return word_app
        
        return None
    
    def get_version(self) -> Optional[str]:
        """Get Microsoft Office version."""
        system = platform.system()
        
        if system == "Windows":
            try:
                import win32com.client
                word_app = win32com.client.Dispatch("Word.Application")
                version = word_app.Version
                word_app.Quit()
                return version
            except:
                return None
        
        elif system == "Darwin":
            try:
                # Use AppleScript to get version
                script = '''
                tell application "Microsoft Word"
                    get version
                end tell
                '''
                result = subprocess.run(
                    ['osascript', '-e', script],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except:
                pass
        
        return None


class LibreOfficePlatform(Platform):
    """LibreOffice platform detection."""
    
    @property
    def name(self) -> str:
        return "LibreOffice"
    
    def is_available(self) -> bool:
        """Check if LibreOffice is available."""
        return self.get_executable_path() is not None
    
    def get_executable_path(self) -> Optional[Path]:
        """Get path to LibreOffice executable."""
        # Try common executable names
        executable_names = ['libreoffice', 'soffice']
        
        for exe_name in executable_names:
            exe_path = find_executable(exe_name)
            if exe_path:
                return exe_path
        
        # Try common installation paths
        system = platform.system()
        
        if system == "Windows":
            common_paths = [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
            ]
        elif system == "Darwin":  # macOS
            common_paths = [
                "/Applications/LibreOffice.app/Contents/MacOS/soffice"
            ]
        else:  # Linux
            common_paths = [
                "/usr/bin/libreoffice",
                "/usr/bin/soffice",
                "/usr/local/bin/libreoffice",
                "/opt/libreoffice/program/soffice"
            ]
        
        for path_str in common_paths:
            path = Path(path_str)
            if path.exists():
                return path
        
        return None
    
    def get_version(self) -> Optional[str]:
        """Get LibreOffice version."""
        exe_path = self.get_executable_path()
        if not exe_path:
            return None
        
        try:
            result = subprocess.run(
                [str(exe_path), '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse version from output like "LibreOffice 7.4.2.3 20220812..."
                output = result.stdout.strip()
                if "LibreOffice" in output:
                    parts = output.split()
                    for i, part in enumerate(parts):
                        if part == "LibreOffice" and i + 1 < len(parts):
                            return parts[i + 1]
                
                return output
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass
        
        return None


class GoogleWorkspacePlatform(Platform):
    """Google Workspace platform detection (API-based)."""
    
    @property
    def name(self) -> str:
        return "Google Workspace"
    
    def is_available(self) -> bool:
        """Check if Google Workspace API is available."""
        try:
            # Try to import Google API client
            import googleapiclient.discovery
            import google.auth
            
            # Check if credentials are available
            # This is a basic check - full implementation would verify API access
            return True
        except ImportError:
            return False
    
    def get_executable_path(self) -> Optional[Path]:
        """Google Workspace doesn't have a local executable."""
        return None
    
    def get_version(self) -> Optional[str]:
        """Get Google Workspace API version."""
        try:
            import googleapiclient
            return googleapiclient.__version__
        except ImportError:
            return None