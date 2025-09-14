"""Cross-platform document conversion engine."""

import platform
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core.config import Config
from ..core.exceptions import ConversionError, PlatformError
from ..core.utils import normalize_path, create_temp_directory, cleanup_temp_files
from .platforms import MicrosoftOfficePlatform, LibreOfficePlatform, GoogleWorkspacePlatform
from .adapters import OfficeAdapter, LibreOfficeAdapter, GoogleAdapter


@dataclass
class ConversionStep:
    """Represents a single conversion step in a workflow."""
    platform: str
    input_format: str
    output_format: str
    input_file: Path
    output_file: Path
    adapter: 'ConversionAdapter'
    timeout: int = 120


@dataclass
class ConversionResult:
    """Result of a document conversion operation."""
    success: bool
    input_file: Path
    output_file: Path
    platform: str
    duration: float
    error_message: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


@dataclass
class RoundTripResult:
    """Result of a complete round-trip conversion workflow."""
    success: bool
    original_file: Path
    final_file: Path
    conversion_steps: List[ConversionResult]
    total_duration: float
    platforms_used: List[str]
    error_message: Optional[str] = None


@dataclass
class ConversionWorkflow:
    """Represents a complete conversion workflow."""
    input_file: Path
    output_dir: Path
    steps: List[ConversionStep]
    start_time: Optional[float] = None
    
    def track_conversion_step(self, step: ConversionStep, result: ConversionResult):
        """Track completion of a conversion step."""
        pass  # Implementation for metrics tracking
    
    def get_metrics(self) -> Dict[str, float]:
        """Get workflow performance metrics."""
        return {
            'total_steps': len(self.steps),
            'elapsed_time': time.time() - (self.start_time or time.time())
        }


class ConversionEngine:
    """Cross-platform document conversion engine."""
    
    def __init__(self, config: Config):
        """Initialize conversion engine with configuration."""
        self.config = config
        self._platforms = {}
        self._adapters = {}
        self._temp_dirs = []
        
        # Initialize platforms and adapters
        self._initialize_platforms()
        self._initialize_adapters()
    
    def _initialize_platforms(self):
        """Initialize available platforms."""
        self._platforms = {
            'office': MicrosoftOfficePlatform(),
            'libreoffice': LibreOfficePlatform(),
            'google': GoogleWorkspacePlatform()
        }
    
    def _initialize_adapters(self):
        """Initialize conversion adapters."""
        self._adapters = {
            'office': OfficeAdapter(self.config),
            'libreoffice': LibreOfficeAdapter(self.config),
            'google': GoogleAdapter(self.config)
        }
    
    def detect_platform(self) -> str:
        """Detect current operating system platform."""
        system = platform.system()
        
        if system == "Windows":
            return "windows"
        elif system == "Darwin":
            return "macos"
        elif system == "Linux":
            return "linux"
        else:
            return f"unknown_{system.lower()}"
    
    def discover_office_suites(self) -> Dict[str, Dict[str, Union[bool, str]]]:
        """Discover available Office suites on the system."""
        discovered = {}
        
        for platform_name, platform in self._platforms.items():
            try:
                is_available = platform.is_available()
                suite_info = {
                    'available': is_available,
                    'path': platform.get_executable_path() if is_available else None,
                    'version': platform.get_version() if is_available else None
                }
                discovered[platform_name] = suite_info
            except Exception as e:
                discovered[platform_name] = {
                    'available': False,
                    'path': None,
                    'version': None,
                    'error': str(e)
                }
        
        return discovered
    
    def get_platform(self, platform_name: str):
        """Get platform instance by name."""
        if platform_name not in self._platforms:
            raise PlatformError(f"Platform '{platform_name}' not available")
        
        platform = self._platforms[platform_name]
        if not platform.is_available():
            raise PlatformError(f"Platform '{platform_name}' is not available on this system")
        
        return platform
    
    def get_adapter(self, platform_name: str):
        """Get conversion adapter by platform name."""
        if platform_name not in self._adapters:
            raise PlatformError(f"Adapter for platform '{platform_name}' not available")
        
        return self._adapters[platform_name]
    
    def create_round_trip_workflow(self, input_file: Path, platforms: List[str], 
                                 output_dir: Path) -> ConversionWorkflow:
        """Create a round-trip conversion workflow."""
        input_file = normalize_path(input_file)
        output_dir = normalize_path(output_dir)
        
        if not input_file.exists():
            raise ConversionError(f"Input file does not exist: {input_file}")
        
        # Determine file format
        input_format = input_file.suffix.lower().lstrip('.')
        
        steps = []
        current_file = input_file
        
        for i, platform_name in enumerate(platforms):
            # Validate platform
            platform = self.get_platform(platform_name)
            adapter = self.get_adapter(platform_name)
            
            # Determine conversion path
            if platform_name == 'libreoffice':
                # OOXML → ODF → OOXML cycle
                if input_format in ['docx', 'doc']:
                    intermediate_format = 'odt'
                    final_format = 'docx'
                elif input_format in ['pptx', 'ppt']:
                    intermediate_format = 'odp'
                    final_format = 'pptx'
                elif input_format in ['xlsx', 'xls']:
                    intermediate_format = 'ods'
                    final_format = 'xlsx'
                else:
                    raise ConversionError(f"Unsupported format for LibreOffice: {input_format}")
                
                # Step 1: OOXML → ODF
                intermediate_file = output_dir / f"{current_file.stem}_intermediate_{i}.{intermediate_format}"
                steps.append(ConversionStep(
                    platform=platform_name,
                    input_format=input_format,
                    output_format=intermediate_format,
                    input_file=current_file,
                    output_file=intermediate_file,
                    adapter=adapter
                ))
                
                # Step 2: ODF → OOXML
                final_file = output_dir / f"{current_file.stem}_roundtrip_{i}.{final_format}"
                steps.append(ConversionStep(
                    platform=platform_name,
                    input_format=intermediate_format,
                    output_format=final_format,
                    input_file=intermediate_file,
                    output_file=final_file,
                    adapter=adapter
                ))
                
                current_file = final_file
                input_format = final_format
            
            elif platform_name == 'office':
                # Microsoft Office round-trip (typically same format)
                output_file = output_dir / f"{current_file.stem}_office_{i}.{input_format}"
                steps.append(ConversionStep(
                    platform=platform_name,
                    input_format=input_format,
                    output_format=input_format,
                    input_file=current_file,
                    output_file=output_file,
                    adapter=adapter
                ))
                
                current_file = output_file
        
        return ConversionWorkflow(
            input_file=input_file,
            output_dir=output_dir,
            steps=steps,
            start_time=time.time()
        )
    
    def execute_round_trip(self, input_file: Path, platforms: List[str], 
                          output_dir: Path, parallel: bool = False) -> RoundTripResult:
        """Execute a complete round-trip conversion workflow."""
        workflow = self.create_round_trip_workflow(input_file, platforms, output_dir)
        
        conversion_results = []
        start_time = time.time()
        
        try:
            if parallel and len(workflow.steps) > 1:
                # Execute steps in parallel where possible
                conversion_results = self._execute_parallel_workflow(workflow)
            else:
                # Execute steps sequentially
                conversion_results = self._execute_sequential_workflow(workflow)
            
            # Determine overall success
            success = all(result.success for result in conversion_results)
            
            # Get final file
            final_file = conversion_results[-1].output_file if conversion_results else input_file
            
            # Collect platforms used
            platforms_used = list(set(result.platform for result in conversion_results))
            
            return RoundTripResult(
                success=success,
                original_file=input_file,
                final_file=final_file,
                conversion_steps=conversion_results,
                total_duration=time.time() - start_time,
                platforms_used=platforms_used,
                error_message=None if success else "One or more conversion steps failed"
            )
            
        except Exception as e:
            return RoundTripResult(
                success=False,
                original_file=input_file,
                final_file=input_file,
                conversion_steps=conversion_results,
                total_duration=time.time() - start_time,
                platforms_used=[],
                error_message=str(e)
            )
    
    def _execute_sequential_workflow(self, workflow: ConversionWorkflow) -> List[ConversionResult]:
        """Execute workflow steps sequentially."""
        results = []
        
        for step in workflow.steps:
            try:
                start_time = time.time()
                
                # Execute conversion
                adapter_result = step.adapter.convert_document(
                    input_file=step.input_file,
                    output_file=step.output_file,
                    target_format=step.output_format,
                    timeout=step.timeout
                )
                
                duration = time.time() - start_time
                
                # Create result
                result = ConversionResult(
                    success=adapter_result.success,
                    input_file=step.input_file,
                    output_file=step.output_file,
                    platform=step.platform,
                    duration=duration,
                    error_message=adapter_result.error_message if not adapter_result.success else None
                )
                
                results.append(result)
                workflow.track_conversion_step(step, result)
                
                # Stop on failure
                if not result.success:
                    break
                    
            except Exception as e:
                result = ConversionResult(
                    success=False,
                    input_file=step.input_file,
                    output_file=step.output_file,
                    platform=step.platform,
                    duration=0,
                    error_message=str(e)
                )
                results.append(result)
                break
        
        return results
    
    def _execute_parallel_workflow(self, workflow: ConversionWorkflow) -> List[ConversionResult]:
        """Execute workflow steps in parallel where possible."""
        # For now, fall back to sequential execution
        # Parallel execution would require dependency analysis
        return self._execute_sequential_workflow(workflow)
    
    def convert_roundtrip(self, input_file: Path, platforms: List[str], 
                         output_dir: Path, parallel: bool = False) -> List[ConversionResult]:
        """Convert documents through platforms (legacy interface for CLI)."""
        result = self.execute_round_trip(input_file, platforms, output_dir, parallel)
        return result.conversion_steps
    
    def cleanup(self):
        """Clean up temporary files and resources."""
        cleanup_temp_files(self._temp_dirs)
        
        # Cleanup adapters
        for adapter in self._adapters.values():
            if hasattr(adapter, 'cleanup'):
                adapter.cleanup()
    
    # Manager interface methods for testing
    def get_parallel_manager(self):
        """Get parallel execution manager."""
        class ParallelManager:
            def __init__(self):
                self.max_workers = 4
            
            def execute_parallel(self, tasks):
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    return list(executor.map(lambda task: task(), tasks))
        
        return ParallelManager()
    
    def get_retry_manager(self):
        """Get retry mechanism manager."""
        class RetryManager:
            def __init__(self):
                self.max_retries = 3
                self.retry_delay = 1.0
            
            def execute_with_retry(self, func, *args, **kwargs):
                for attempt in range(self.max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if attempt == self.max_retries - 1:
                            raise e
                        time.sleep(self.retry_delay)
        
        return RetryManager()
    
    def get_cleanup_manager(self):
        """Get file cleanup manager."""
        class CleanupManager:
            def __init__(self):
                self.temp_files = []
            
            def register_temp_file(self, file_path):
                self.temp_files.append(file_path)
            
            def cleanup_temp_files(self):
                cleanup_temp_files(self.temp_files)
                self.temp_files.clear()
        
        return CleanupManager()
    
    def get_timeout_manager(self):
        """Get timeout management."""
        class TimeoutManager:
            def __init__(self):
                self.default_timeout = 120
                self.kill_on_timeout = True
        
        return TimeoutManager()
    
    def get_batch_manager(self):
        """Get batch processing manager."""
        class BatchManager:
            def __init__(self):
                self.max_concurrent_conversions = 4
            
            def process_batch(self, files, conversion_func):
                results = []
                with ThreadPoolExecutor(max_workers=self.max_concurrent_conversions) as executor:
                    future_to_file = {
                        executor.submit(conversion_func, file): file 
                        for file in files
                    }
                    
                    for future in as_completed(future_to_file):
                        file = future_to_file[future]
                        try:
                            result = future.result()
                            results.append(result)
                        except Exception as e:
                            results.append({'file': file, 'error': str(e)})
                
                return results
        
        return BatchManager()
    
    def get_memory_manager(self):
        """Get memory management."""
        class MemoryManager:
            def monitor_memory_usage(self):
                # Implementation would monitor memory usage
                pass
            
            def cleanup_on_memory_pressure(self):
                # Implementation would cleanup on memory pressure
                pass
        
        return MemoryManager()
    
    def get_progress_tracker(self):
        """Get progress tracking."""
        class ProgressTracker:
            def __init__(self):
                self.current_step = 0
                self.total_steps = 0
            
            def update_progress(self, step, total):
                self.current_step = step
                self.total_steps = total
            
            def get_completion_percentage(self):
                if self.total_steps == 0:
                    return 0
                return (self.current_step / self.total_steps) * 100
        
        return ProgressTracker()