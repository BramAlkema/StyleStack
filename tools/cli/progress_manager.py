"""
Progress management system with Rich progress bars and ETA calculations.
"""

import time
from typing import Optional, Dict, Any, List, Callable
from contextlib import contextmanager
from dataclasses import dataclass
from rich.console import Console
from rich.progress import (
    Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, 
    TimeElapsedColumn, TimeRemainingColumn, MofNCompleteColumn,
    FileSizeColumn, TransferSpeedColumn
)
from rich.live import Live
from rich.table import Table
from rich.text import Text


@dataclass
class ProgressTask:
    """Progress task information."""
    task_id: TaskID
    name: str
    total: Optional[int]
    completed: int = 0
    start_time: float = 0.0
    end_time: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.start_time == 0.0:
            self.start_time = time.time()


class ProgressManager:
    """Progress management with Rich progress bars and ETA calculations."""
    
    def __init__(self, console: Console):
        """Initialize progress manager with Rich console."""
        self.console = console
        self.active_tasks: Dict[TaskID, ProgressTask] = {}
        self.completed_tasks: List[ProgressTask] = []
        self.progress_callbacks: Dict[str, List[Callable]] = {}
        
    @contextmanager
    def create_progress(self, 
                       show_time: bool = True,
                       show_eta: bool = True,
                       show_percentage: bool = True):
        """Create a Rich progress context manager."""
        columns = [
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
        ]
        
        if show_percentage:
            columns.append(TextColumn("[progress.percentage]{task.percentage:>3.0f}%"))
            
        if show_time:
            columns.append(TimeElapsedColumn())
            
        if show_eta:
            columns.append(TimeRemainingColumn())
            
        progress = Progress(*columns, console=self.console)
        
        try:
            with progress:
                yield progress
        finally:
            # Clean up completed tasks
            self._cleanup_completed_tasks()
    
    @contextmanager
    def create_multi_progress(self, title: str = "Processing"):
        """Create multi-task progress display."""
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console
        )
        
        try:
            with progress:
                # Add main progress task
                main_task = progress.add_task(title, total=None)
                yield progress, main_task
        finally:
            self._cleanup_completed_tasks()
    
    @contextmanager
    def create_file_progress(self):
        """Create file transfer progress display."""
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            FileSizeColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=self.console
        )
        
        try:
            with progress:
                yield progress
        finally:
            self._cleanup_completed_tasks()
    
    def track_task(self, 
                   task_id: TaskID,
                   name: str,
                   total: Optional[int] = None,
                   **metadata) -> ProgressTask:
        """Track a progress task."""
        task = ProgressTask(
            task_id=task_id,
            name=name,
            total=total,
            metadata=metadata
        )
        
        self.active_tasks[task_id] = task
        return task
    
    def update_task_progress(self,
                            task_id: TaskID,
                            advance: int = 1,
                            completed: Optional[int] = None,
                            description: Optional[str] = None,
                            **metadata) -> None:
        """Update task progress."""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            
            if completed is not None:
                task.completed = completed
            else:
                task.completed += advance
            
            if description:
                task.name = description
                
            task.metadata.update(metadata)
            
            # Trigger progress callbacks
            self._trigger_callbacks(task)
            
            # Mark as completed if total reached
            if task.total and task.completed >= task.total:
                self._complete_task(task_id)
    
    def complete_task(self, task_id: TaskID) -> None:
        """Mark a task as completed."""
        self._complete_task(task_id)
    
    def _complete_task(self, task_id: TaskID) -> None:
        """Internal method to complete a task."""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.end_time = time.time()
            
            self.completed_tasks.append(task)
            del self.active_tasks[task_id]
            
            # Trigger completion callbacks
            self._trigger_callbacks(task, event='completed')
    
    def get_task_stats(self, task_id: TaskID) -> Dict[str, Any]:
        """Get task statistics."""
        task = self.active_tasks.get(task_id) or next(
            (t for t in self.completed_tasks if t.task_id == task_id), None
        )
        
        if not task:
            return {}
        
        stats = {
            'name': task.name,
            'completed': task.completed,
            'total': task.total,
            'start_time': task.start_time,
            'end_time': task.end_time
        }
        
        # Calculate derived statistics
        current_time = task.end_time or time.time()
        elapsed_time = current_time - task.start_time
        stats['elapsed_time'] = elapsed_time
        
        if task.completed > 0 and elapsed_time > 0:
            stats['rate'] = task.completed / elapsed_time
            
            if task.total:
                stats['progress_ratio'] = task.completed / task.total
                if task.completed < task.total and stats['rate'] > 0:
                    remaining = task.total - task.completed
                    stats['eta'] = remaining / stats['rate']
        
        return stats
    
    def register_callback(self,
                         event: str,
                         callback: Callable,
                         task_id: Optional[TaskID] = None) -> None:
        """Register progress callback."""
        key = f"{event}:{task_id}" if task_id else event
        
        if key not in self.progress_callbacks:
            self.progress_callbacks[key] = []
        
        self.progress_callbacks[key].append(callback)
    
    def _trigger_callbacks(self, task: ProgressTask, event: str = 'progress') -> None:
        """Trigger registered callbacks."""
        # Global callbacks
        for callback in self.progress_callbacks.get(event, []):
            try:
                callback(task)
            except Exception as e:
                self.console.print(f"[red]Callback error: {e}[/red]")
        
        # Task-specific callbacks
        task_key = f"{event}:{task.task_id}"
        for callback in self.progress_callbacks.get(task_key, []):
            try:
                callback(task)
            except Exception as e:
                self.console.print(f"[red]Task callback error: {e}[/red]")
    
    def display_progress_summary(self) -> None:
        """Display summary of all progress tasks."""
        if not self.completed_tasks and not self.active_tasks:
            return
        
        table = Table(title="Progress Summary", show_header=True)
        table.add_column("Task", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        table.add_column("Progress", style="blue")
        table.add_column("Duration", style="dim")
        table.add_column("Rate", style="dim")
        
        # Add completed tasks
        for task in self.completed_tasks:
            stats = self.get_task_stats(task.task_id)
            progress_text = f"{task.completed}"
            if task.total:
                progress_text += f"/{task.total}"
                
            duration = f"{stats.get('elapsed_time', 0):.1f}s"
            rate = f"{stats.get('rate', 0):.1f}/s" if 'rate' in stats else "N/A"
            
            table.add_row(
                task.name,
                "✅ Completed",
                progress_text,
                duration,
                rate
            )
        
        # Add active tasks
        for task in self.active_tasks.values():
            stats = self.get_task_stats(task.task_id)
            progress_text = f"{task.completed}"
            if task.total:
                progress_text += f"/{task.total}"
                
            duration = f"{stats.get('elapsed_time', 0):.1f}s"
            rate = f"{stats.get('rate', 0):.1f}/s" if 'rate' in stats else "N/A"
            eta = f"ETA: {stats.get('eta', 0):.1f}s" if 'eta' in stats else "N/A"
            
            table.add_row(
                task.name,
                f"🔄 In Progress ({eta})",
                progress_text,
                duration,
                rate
            )
        
        self.console.print(table)
    
    def create_milestone_tracker(self, milestones: List[Dict[str, Any]]):
        """Create milestone-based progress tracker."""
        return MilestoneTracker(self, milestones)
    
    def _cleanup_completed_tasks(self) -> None:
        """Clean up old completed tasks."""
        # Keep only recent completed tasks (last 10)
        if len(self.completed_tasks) > 10:
            self.completed_tasks = self.completed_tasks[-10:]


class MilestoneTracker:
    """Milestone-based progress tracking."""
    
    def __init__(self, progress_manager: ProgressManager, milestones: List[Dict[str, Any]]):
        """Initialize milestone tracker."""
        self.progress_manager = progress_manager
        self.milestones = milestones
        self.current_milestone = 0
        self.completed_milestones: List[Dict[str, Any]] = []
        
    def reach_milestone(self, milestone_name: str, **metadata) -> None:
        """Mark a milestone as reached."""
        milestone = next((m for m in self.milestones if m['name'] == milestone_name), None)
        if not milestone:
            return
        
        milestone['completed_time'] = time.time()
        milestone['metadata'] = metadata
        self.completed_milestones.append(milestone)
        
        # Display milestone notification
        self.progress_manager.console.print(
            f"✅ Milestone reached: [bold]{milestone_name}[/bold]",
            style="green"
        )
        
        # Update current milestone
        if self.current_milestone < len(self.milestones):
            self.current_milestone += 1
    
    def get_progress_percentage(self) -> float:
        """Get overall progress percentage based on milestones."""
        if not self.milestones:
            return 0.0
        return (len(self.completed_milestones) / len(self.milestones)) * 100
    
    def display_milestone_progress(self) -> None:
        """Display milestone progress table."""
        table = Table(title="Milestone Progress", show_header=True)
        table.add_column("Milestone", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Completed", style="dim")
        
        for i, milestone in enumerate(self.milestones):
            status = "✅ Completed" if milestone in self.completed_milestones else "⏳ Pending"
            completed_time = ""
            
            if milestone in self.completed_milestones:
                import datetime
                dt = datetime.datetime.fromtimestamp(milestone.get('completed_time', 0))
                completed_time = dt.strftime("%H:%M:%S")
            
            table.add_row(milestone['name'], status, completed_time)
        
        self.progress_manager.console.print(table)


class InteractiveProgress:
    """Interactive progress display with user controls."""
    
    def __init__(self, console: Console):
        """Initialize interactive progress."""
        self.console = console
        self.paused = False
        self.cancelled = False
        
    def start_interactive_progress(self, task_generator):
        """Start interactive progress with user controls."""
        # This would implement interactive features like pause/resume/cancel
        # For now, it's a placeholder for the enhanced functionality
        pass