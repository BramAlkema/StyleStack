"""
Batch processing system with parallel execution, queue management, and resume capability.
"""

import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from queue import PriorityQueue, Queue
import hashlib
import uuid

from .progress_manager import ProgressManager
from .error_handler import EnhancedErrorHandler, StyleStackCliError


@dataclass
class BatchTemplate:
    """Batch processing template configuration."""
    name: str
    src: str
    out: str
    org: Optional[str] = None
    channel: Optional[str] = None
    priority: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    template_id: Optional[str] = None
    
    def __post_init__(self):
        if self.template_id is None:
            # Generate unique ID based on template configuration
            content = f"{self.src}{self.out}{self.org}{self.channel}"
            self.template_id = hashlib.md5(content.encode()).hexdigest()[:12]


@dataclass
class BatchResult:
    """Batch processing result."""
    template: BatchTemplate
    status: str  # 'completed', 'failed', 'skipped', 'retrying'
    start_time: float
    end_time: Optional[float] = None
    error: Optional[Exception] = None
    output_size: Optional[int] = None
    processing_time: Optional[float] = None
    retry_count: int = 0


@dataclass
class BatchCheckpoint:
    """Batch processing checkpoint for resume capability."""
    batch_id: str
    timestamp: str
    batch_file: str
    total_templates: int
    completed: List[Dict[str, Any]] = field(default_factory=list)
    failed: List[Dict[str, Any]] = field(default_factory=list)
    remaining: List[Dict[str, Any]] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)


class BatchQueue:
    """Priority queue for batch processing."""
    
    def __init__(self):
        """Initialize batch queue."""
        self.queue = PriorityQueue()
        self.completed_count = 0
        self.failed_count = 0
        self.total_count = 0
        self._lock = threading.Lock()
    
    def add_template(self, template: BatchTemplate) -> None:
        """Add template to processing queue."""
        # Use negative priority for correct ordering (lower number = higher priority)
        self.queue.put((-template.priority, template))
        with self._lock:
            self.total_count += 1
    
    def get_next_template(self, timeout: Optional[float] = None) -> Optional[BatchTemplate]:
        """Get next template from queue."""
        try:
            _, template = self.queue.get(timeout=timeout)
            return template
        except:
            return None
    
    def mark_completed(self) -> None:
        """Mark a template as completed."""
        with self._lock:
            self.completed_count += 1
        self.queue.task_done()
    
    def mark_failed(self) -> None:
        """Mark a template as failed."""
        with self._lock:
            self.failed_count += 1
        self.queue.task_done()
    
    def get_stats(self) -> Dict[str, int]:
        """Get queue statistics."""
        with self._lock:
            return {
                'total': self.total_count,
                'completed': self.completed_count,
                'failed': self.failed_count,
                'remaining': self.total_count - self.completed_count - self.failed_count,
                'queued': self.queue.qsize()
            }
    
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return self.queue.empty()


class BatchProcessor:
    """Batch processing system with parallel execution and resume capability."""
    
    def __init__(self, context):
        """Initialize batch processor."""
        self.context = context
        self.progress_manager = context.progress_manager
        self.error_handler = context.error_handler
        self.console = context.console
        
        self.batch_queue = BatchQueue()
        self.results: List[BatchResult] = []
        self.checkpoint_manager = CheckpointManager(context)
        self.retry_manager = RetryManager(context)
        
        # Configuration
        self.max_workers = context.config.get('defaults', {}).get('max_workers', 4)
        self.parallel = context.config.get('defaults', {}).get('parallel', True)
        self.checkpoint_interval = context.config.get('batch', {}).get('checkpoint_interval', 10)
        self.enable_retries = context.config.get('batch', {}).get('retry_failed', True)
        self.max_retries = context.config.get('batch', {}).get('max_retries', 3)
    
    def process_batch_file(self, batch_file: str, **kwargs) -> bool:
        """Process batch configuration file."""
        try:
            # Load batch configuration
            batch_config = self._load_batch_config(batch_file)
            
            # Validate configuration
            self._validate_batch_config(batch_config)
            
            # Process batch
            return self._process_batch_config(batch_config, **kwargs)
            
        except Exception as e:
            self.error_handler.handle_processing_error(e, self.context)
            return False
    
    def _load_batch_config(self, batch_file: str) -> Dict[str, Any]:
        """Load and parse batch configuration file."""
        batch_path = Path(batch_file)
        if not batch_path.exists():
            raise StyleStackCliError(
                f"Batch configuration file not found: {batch_file}",
                error_code="BATCH001",
                suggestions=[
                    "Check if the batch file path is correct",
                    "Ensure the batch file exists and is accessible",
                    "Create a batch configuration file using --create-batch-template"
                ]
            )
        
        try:
            with open(batch_path, 'r', encoding='utf-8') as f:
                if batch_path.suffix.lower() == '.json':
                    config = json.load(f)
                elif batch_path.suffix.lower() in ['.yml', '.yaml']:
                    import yaml
                    config = yaml.safe_load(f)
                else:
                    # Try JSON first, then YAML
                    content = f.read()
                    try:
                        config = json.loads(content)
                    except json.JSONDecodeError:
                        import yaml
                        config = yaml.safe_load(content)
                        
        except Exception as e:
            raise StyleStackCliError(
                f"Failed to parse batch configuration: {e}",
                error_code="BATCH002",
                suggestions=[
                    "Check configuration file syntax",
                    "Validate JSON/YAML format",
                    "Ensure proper encoding (UTF-8)"
                ]
            )
        
        return config
    
    def _validate_batch_config(self, config: Dict[str, Any]) -> None:
        """Validate batch configuration."""
        required_fields = ['templates']
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            raise StyleStackCliError(
                f"Missing required fields in batch configuration: {missing_fields}",
                error_code="BATCH003",
                suggestions=[
                    "Add required fields to batch configuration",
                    "Use --create-batch-template to generate sample configuration",
                    "Check batch configuration documentation"
                ]
            )
        
        # Validate templates
        if not isinstance(config['templates'], list) or not config['templates']:
            raise StyleStackCliError(
                "Batch configuration must contain a non-empty list of templates",
                error_code="BATCH004"
            )
        
        # Validate each template
        for i, template_config in enumerate(config['templates']):
            self._validate_template_config(template_config, i)
    
    def _validate_template_config(self, template_config: Dict[str, Any], index: int) -> None:
        """Validate individual template configuration."""
        required_fields = ['src', 'out']
        missing_fields = [field for field in required_fields if field not in template_config]
        
        if missing_fields:
            raise StyleStackCliError(
                f"Template {index + 1} missing required fields: {missing_fields}",
                error_code="BATCH005"
            )
        
        # Check if source file exists
        src_path = Path(template_config['src'])
        if not src_path.exists():
            self.context.add_warning(f"Template {index + 1}: Source file not found: {src_path}")
    
    def _process_batch_config(self, config: Dict[str, Any], **kwargs) -> bool:
        """Process batch configuration."""
        batch_id = str(uuid.uuid4())[:8]
        
        # Create batch templates
        templates = []
        for template_config in config['templates']:
            template = BatchTemplate(
                name=template_config.get('name', f"Template {len(templates) + 1}"),
                src=template_config['src'],
                out=template_config['out'],
                org=template_config.get('org'),
                channel=template_config.get('channel'),
                priority=template_config.get('priority', 1),
                metadata=template_config.get('metadata', {})
            )
            templates.append(template)
        
        # Sort templates by priority
        templates.sort(key=lambda t: t.priority)
        
        # Add templates to queue
        for template in templates:
            self.batch_queue.add_template(template)
        
        # Apply batch settings
        batch_settings = config.get('settings', {})
        if 'parallel' in batch_settings:
            self.parallel = batch_settings['parallel']
        if 'max_workers' in batch_settings:
            self.max_workers = batch_settings['max_workers']
        
        # Display batch summary
        self._display_batch_summary(templates, batch_settings)
        
        # Process templates
        if kwargs.get('dry_run'):
            return self._dry_run_batch(templates)
        else:
            return self._execute_batch(templates, batch_id)
    
    def _display_batch_summary(self, templates: List[BatchTemplate], settings: Dict[str, Any]) -> None:
        """Display batch processing summary."""
        if self.context.quiet:
            return
        
        from rich.table import Table
        from rich.panel import Panel
        
        # Create summary table
        table = Table(title="Batch Processing Summary", show_header=True)
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        
        table.add_row("Templates", str(len(templates)))
        table.add_row("Parallel Processing", str(self.parallel))
        table.add_row("Max Workers", str(self.max_workers))
        table.add_row("Checkpoint Interval", str(self.checkpoint_interval))
        table.add_row("Retry Failed", str(self.enable_retries))
        
        self.console.print(table)
        
        # Show template list if verbose
        if self.context.verbose:
            template_table = Table(title="Templates to Process", show_header=True)
            template_table.add_column("Priority", style="dim")
            template_table.add_column("Name", style="cyan")
            template_table.add_column("Source", style="blue")
            template_table.add_column("Output", style="green")
            template_table.add_column("Org", style="yellow")
            template_table.add_column("Channel", style="magenta")
            
            for template in templates:
                template_table.add_row(
                    str(template.priority),
                    template.name,
                    template.src,
                    template.out,
                    template.org or "-",
                    template.channel or "-"
                )
            
            self.console.print(template_table)
    
    def _dry_run_batch(self, templates: List[BatchTemplate]) -> bool:
        """Perform dry run of batch processing."""
        self.console.print("\n[bold yellow]🔍 Batch Processing Dry Run[/bold yellow]\n")
        
        # Estimate processing time and space
        estimated_time = len(templates) * 30  # 30 seconds per template average
        if self.parallel:
            estimated_time = estimated_time / min(self.max_workers, len(templates))
        
        estimated_space = len(templates) * 50 * 1024 * 1024  # 50MB per template average
        
        dry_run_info = {
            'templates_to_process': len(templates),
            'estimated_time': f"{estimated_time:.0f}s ({estimated_time/60:.1f}m)",
            'estimated_space': f"{estimated_space / (1024*1024):.0f}MB",
            'parallel_workers': self.max_workers if self.parallel else 1
        }
        
        # Display dry run results
        from rich.panel import Panel
        
        content = f"""
[bold]Would process {dry_run_info['templates_to_process']} templates[/bold]

Estimated time: {dry_run_info['estimated_time']}
Estimated space: {dry_run_info['estimated_space']}
Workers: {dry_run_info['parallel_workers']}

Processing order:
""" + '\n'.join(f"  {i+1}. {t.name} (Priority {t.priority})" for i, t in enumerate(templates[:5]))
        
        if len(templates) > 5:
            content += f"\n  ... and {len(templates) - 5} more"
        
        panel = Panel(content.strip(), title="Dry Run Results", border_style="yellow")
        self.console.print(panel)
        
        return True
    
    def _execute_batch(self, templates: List[BatchTemplate], batch_id: str) -> bool:
        """Execute batch processing."""
        start_time = time.time()
        
        try:
            with self.progress_manager.create_multi_progress("Batch Processing") as (progress, main_task):
                progress.update(main_task, total=len(templates))
                
                if self.parallel:
                    success = self._execute_parallel_batch(templates, progress, main_task)
                else:
                    success = self._execute_sequential_batch(templates, progress, main_task)
                
                # Create checkpoint after completion
                self.checkpoint_manager.create_final_checkpoint(
                    batch_id, templates, self.results
                )
                
        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠️  Batch processing interrupted by user[/yellow]")
            # Save checkpoint for resume
            self.checkpoint_manager.save_interrupt_checkpoint(
                batch_id, templates, self.results
            )
            return False
        except Exception as e:
            self.error_handler.handle_processing_error(e, self.context)
            return False
        
        # Display final results
        end_time = time.time()
        self._display_batch_results(templates, end_time - start_time)
        
        return success
    
    def _execute_parallel_batch(self, templates: List[BatchTemplate], progress, main_task) -> bool:
        """Execute batch processing in parallel."""
        completed_count = 0
        failed_count = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all templates for processing
            future_to_template = {
                executor.submit(self._process_single_template, template): template
                for template in templates
            }
            
            # Process completed tasks
            for future in as_completed(future_to_template):
                template = future_to_template[future]
                
                try:
                    result = future.result()
                    self.results.append(result)
                    
                    if result.status == 'completed':
                        completed_count += 1
                        progress.update(main_task, advance=1, 
                                      description=f"✅ Completed: {template.name}")
                    else:
                        failed_count += 1
                        progress.update(main_task, advance=1,
                                      description=f"❌ Failed: {template.name}")
                        
                except Exception as e:
                    failed_count += 1
                    result = BatchResult(
                        template=template,
                        status='failed',
                        start_time=time.time(),
                        error=e
                    )
                    self.results.append(result)
                    
                    progress.update(main_task, advance=1,
                                  description=f"❌ Error: {template.name}")
                
                # Create checkpoint periodically
                if (completed_count + failed_count) % self.checkpoint_interval == 0:
                    self.checkpoint_manager.update_checkpoint(templates, self.results)
        
        return failed_count == 0
    
    def _execute_sequential_batch(self, templates: List[BatchTemplate], progress, main_task) -> bool:
        """Execute batch processing sequentially."""
        completed_count = 0
        failed_count = 0
        
        for i, template in enumerate(templates):
            try:
                result = self._process_single_template(template)
                self.results.append(result)
                
                if result.status == 'completed':
                    completed_count += 1
                    progress.update(main_task, advance=1,
                                  description=f"✅ Completed: {template.name}")
                else:
                    failed_count += 1
                    progress.update(main_task, advance=1,
                                  description=f"❌ Failed: {template.name}")
                
            except Exception as e:
                failed_count += 1
                result = BatchResult(
                    template=template,
                    status='failed',
                    start_time=time.time(),
                    error=e
                )
                self.results.append(result)
                
                progress.update(main_task, advance=1,
                              description=f"❌ Error: {template.name}")
            
            # Create checkpoint periodically
            if (i + 1) % self.checkpoint_interval == 0:
                self.checkpoint_manager.update_checkpoint(templates, self.results)
        
        return failed_count == 0
    
    def _process_single_template(self, template: BatchTemplate) -> BatchResult:
        """Process a single template."""
        start_time = time.time()
        
        try:
            # Import the main processing function
            from build import process_single_template
            
            # Process the template
            success = process_single_template(
                src=template.src,
                out=template.out,
                org=template.org,
                channel=template.channel,
                verbose=False  # Suppress individual verbose output in batch mode
            )
            
            end_time = time.time()
            
            # Check if output file was created and get its size
            output_path = Path(template.out)
            output_size = output_path.stat().st_size if output_path.exists() else None
            
            return BatchResult(
                template=template,
                status='completed' if success else 'failed',
                start_time=start_time,
                end_time=end_time,
                output_size=output_size,
                processing_time=end_time - start_time
            )
            
        except Exception as e:
            return BatchResult(
                template=template,
                status='failed',
                start_time=start_time,
                end_time=time.time(),
                error=e,
                processing_time=time.time() - start_time
            )
    
    def _display_batch_results(self, templates: List[BatchTemplate], total_time: float) -> None:
        """Display batch processing results."""
        if self.context.quiet:
            return
        
        from rich.table import Table
        from rich.panel import Panel
        
        # Calculate statistics
        completed = sum(1 for r in self.results if r.status == 'completed')
        failed = sum(1 for r in self.results if r.status == 'failed')
        total_size = sum(r.output_size or 0 for r in self.results if r.output_size)
        avg_time = sum(r.processing_time or 0 for r in self.results) / len(self.results)
        
        # Create results summary
        summary_content = f"""
[bold green]✅ Batch Processing Complete[/bold green]

[bold]Results Summary:[/bold]
• Completed: {completed}/{len(templates)} templates
• Failed: {failed}/{len(templates)} templates
• Success Rate: {(completed/len(templates)*100):.1f}%
• Total Time: {total_time:.1f}s ({total_time/60:.1f}m)
• Average Time per Template: {avg_time:.1f}s
• Total Output Size: {total_size/(1024*1024):.1f}MB
• Processing Rate: {completed/total_time:.1f} templates/sec
"""
        
        if self.parallel:
            summary_content += f"• Workers Used: {self.max_workers}\n"
        
        panel = Panel(summary_content.strip(), title="Batch Results", border_style="green")
        self.console.print(panel)
        
        # Show failed templates if any
        if failed > 0 and self.context.verbose:
            failed_table = Table(title="Failed Templates", show_header=True)
            failed_table.add_column("Template", style="red")
            failed_table.add_column("Error", style="dim red")
            
            for result in self.results:
                if result.status == 'failed':
                    error_msg = str(result.error) if result.error else "Unknown error"
                    failed_table.add_row(result.template.name, error_msg[:50] + "...")
            
            self.console.print(failed_table)


class CheckpointManager:
    """Checkpoint management for resumable batch processing."""
    
    def __init__(self, context):
        """Initialize checkpoint manager."""
        self.context = context
        self.checkpoint_dir = Path.cwd() / ".stylestack_checkpoints"
        self.checkpoint_dir.mkdir(exist_ok=True)
    
    def save_checkpoint(self, batch_id: str, templates: List[BatchTemplate], 
                       results: List[BatchResult]) -> None:
        """Save processing checkpoint."""
        checkpoint_file = self.checkpoint_dir / f"checkpoint_{batch_id}.json"
        
        # Prepare checkpoint data
        completed = [self._result_to_dict(r) for r in results if r.status == 'completed']
        failed = [self._result_to_dict(r) for r in results if r.status == 'failed']
        
        processed_ids = {r.template.template_id for r in results}
        remaining = [self._template_to_dict(t) for t in templates if t.template_id not in processed_ids]
        
        checkpoint = BatchCheckpoint(
            batch_id=batch_id,
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
            batch_file="",  # Would be filled in by caller
            total_templates=len(templates),
            completed=completed,
            failed=failed,
            remaining=remaining,
            settings={
                'parallel': self.context.config.get('defaults', {}).get('parallel', True),
                'max_workers': self.context.config.get('defaults', {}).get('max_workers', 4)
            }
        )
        
        # Save checkpoint
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint.__dict__, f, indent=2, default=str)
    
    def load_checkpoint(self, checkpoint_file: str) -> BatchCheckpoint:
        """Load processing checkpoint."""
        with open(checkpoint_file, 'r') as f:
            data = json.load(f)
        
        return BatchCheckpoint(**data)
    
    def _result_to_dict(self, result: BatchResult) -> Dict[str, Any]:
        """Convert batch result to dictionary."""
        return {
            'template': self._template_to_dict(result.template),
            'status': result.status,
            'processing_time': result.processing_time,
            'output_size': result.output_size,
            'error': str(result.error) if result.error else None
        }
    
    def _template_to_dict(self, template: BatchTemplate) -> Dict[str, Any]:
        """Convert batch template to dictionary."""
        return {
            'name': template.name,
            'src': template.src,
            'out': template.out,
            'org': template.org,
            'channel': template.channel,
            'priority': template.priority,
            'template_id': template.template_id,
            'metadata': template.metadata
        }


class RetryManager:
    """Retry management for failed templates."""
    
    def __init__(self, context):
        """Initialize retry manager."""
        self.context = context
        self.max_retries = context.config.get('batch', {}).get('max_retries', 3)
        self.retry_delay = 1.0  # seconds
    
    def should_retry(self, result: BatchResult) -> bool:
        """Check if a failed result should be retried."""
        if result.status != 'failed':
            return False
        
        if result.retry_count >= self.max_retries:
            return False
        
        # Don't retry certain error types
        if result.error and isinstance(result.error, FileNotFoundError):
            return False
        
        return True
    
    def schedule_retry(self, result: BatchResult) -> None:
        """Schedule a template for retry."""
        result.retry_count += 1
        result.status = 'retrying'
        
        # Add delay before retry
        time.sleep(self.retry_delay * result.retry_count)