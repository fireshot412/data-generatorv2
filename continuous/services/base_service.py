#!/usr/bin/env python3
"""
Base service class defining the interface for continuous data generation services.
Provides abstraction for different platform types (Asana, Okta, etc.).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import asyncio

from continuous.state_manager import StateManager
from continuous.llm_generator import LLMGenerator
from continuous.scheduler import ActivityScheduler
from continuous.connections.base_connection import BaseClientPool


class BaseService(ABC):
    """
    Abstract base class for continuous generation services.
    All service implementations must inherit from this class.
    """

    def __init__(self, config: Dict[str, Any], state_manager: StateManager,
                 llm_generator: LLMGenerator, client_pool: BaseClientPool):
        """
        Initialize continuous service.

        Args:
            config: Job configuration
            state_manager: State manager instance
            llm_generator: LLM generator instance
            client_pool: Pool of platform clients
        """
        self.config = config
        self.state_manager = state_manager
        self.llm = llm_generator
        self.client_pool = client_pool
        self.scheduler = ActivityScheduler(config)

        # Create job state
        self.job_id = state_manager.create_new_job(config)
        self.state = state_manager.load_state(self.job_id)

        self.running = False
        self.paused = False
        self.deleted = False  # Flag to prevent state saves after deletion

        print(f"✓ Service initialized - Job ID: {self.job_id}")

    @abstractmethod
    async def run(self):
        """
        Main loop - runs continuously until stopped.
        Each platform implements its own generation logic.
        """
        pass

    @abstractmethod
    async def _create_project(self) -> Optional[Dict[str, Any]]:
        """
        Create a new project with initial data.

        Returns:
            Created project data or None on error
        """
        pass

    @abstractmethod
    async def _create_task(self, project_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Create a new task in a project.

        Args:
            project_id: Project ID
            **kwargs: Platform-specific parameters

        Returns:
            Created task data or None on error
        """
        pass

    @abstractmethod
    async def _generate_activity(self):
        """Generate a single activity based on current state."""
        pass

    @abstractmethod
    async def cleanup_platform_data(self, progress_callback=None) -> Dict[str, Any]:
        """
        Delete all platform data created by this job.

        Args:
            progress_callback: Optional callback function(current, total, message)

        Returns:
            Dict with cleanup results
        """
        pass

    def _should_continue(self) -> bool:
        """
        Check if job should continue running.

        Returns:
            True if should continue, False otherwise
        """
        if self.config.get("duration_days") == "indefinite":
            return True

        # Check duration
        from datetime import datetime, timezone
        started_at = datetime.fromisoformat(self.state["started_at"])
        duration_days = self.config.get("duration_days", 30)
        elapsed_days = (datetime.now(timezone.utc) - started_at).days

        return elapsed_days < duration_days

    def pause(self):
        """Pause the service."""
        self.paused = True
        self.state_manager.update_job_status(self.job_id, "paused")
        print(f"Service paused for job {self.job_id}")

    def resume(self):
        """Resume the service."""
        from datetime import datetime, timezone

        self.paused = False
        self.state_manager.update_job_status(self.job_id, "running")

        # Check if next_activity_time is in the past
        next_activity_time_str = self.state.get("next_activity_time")
        if next_activity_time_str:
            next_activity_time = datetime.fromisoformat(next_activity_time_str)
            if next_activity_time.tzinfo is None:
                next_activity_time = next_activity_time.replace(tzinfo=timezone.utc)

            current_time = datetime.now(timezone.utc)

            if current_time > next_activity_time:
                # Scheduled time is in the past, recalculate based on current time
                print(f"Scheduled activity time was in the past, recalculating...")
                new_next_time = self.scheduler.get_next_activity_time(current_time)
                self.state_manager.update_next_activity_time(self.job_id, new_next_time.isoformat())
                print(f"New next activity time: {new_next_time.strftime('%Y-%m-%d %I:%M %p %Z')}")

        print(f"Service resumed for job {self.job_id}")

    def stop(self):
        """Stop the service (pause activity but keep it resumable)."""
        self.paused = True
        self.state_manager.update_job_status(self.job_id, "stopped")
        print(f"Service stopped (paused) for job {self.job_id}")
