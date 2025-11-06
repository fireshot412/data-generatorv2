#!/usr/bin/env python3
"""
State Manager for persisting continuous generation job state.
Handles saving/loading job state to/from JSON files.

Supports multiple connection types (Asana, Okta, and future platforms).
Each connection type can have its own data structure and statistics.
Maintains backward compatibility with legacy Asana-only job files.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path
import uuid


class StateManager:
    """
    Manages persistent state for continuous generation jobs.

    Supports multiple connection types:
    - Asana: Projects, tasks, comments, custom fields
    - Okta: Users, groups, applications, assignments
    - Future: Other platforms can be added

    Each connection type maintains its own data structures and statistics
    while sharing common lifecycle management (status, timestamps, logs).
    """

    def __init__(self, state_dir: str = "."):
        """
        Initialize state manager.

        Args:
            state_dir: Directory where state files will be stored
        """
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)

    def create_new_job(self, config: Dict[str, Any]) -> str:
        """
        Create a new job with initial state.

        Extracts connection_type from config and initializes appropriate data structures.
        Supports: 'asana' (projects/tasks) and 'okta' (users/groups).

        Args:
            config: Job configuration dictionary (must include 'connection_type')

        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())[:8]  # Short UUID
        now = datetime.now(timezone.utc).isoformat()
        connection_type = config.get("connection_type", "asana")  # Default to asana for backward compatibility

        # Common state structure (connection-agnostic)
        state = {
            "job_id": job_id,
            "connection_type": connection_type,  # NEW: Connection type identifier
            "job_name": config.get("job_name"),
            "status": "running",
            "created_at": now,
            "started_at": now,
            "last_activity": now,
            "last_saved": now,
            "config": config,
            "activity_log": [],
            "errors": []
        }

        # Connection-specific initialization
        if connection_type == "asana":
            state.update({
                "projects": [],
                "used_scenarios": [],  # Track which scenarios have been used to ensure variety
                "created_object_ids": {  # Track all created workspace-level objects for cleanup
                    "portfolios": [],  # List of portfolio GIDs
                    "custom_fields": [],  # List of custom field GIDs
                    "tags": [],  # List of tag GIDs
                    "sections": []  # List of section GIDs
                },
                "stats": {
                    "projects_created": 0,
                    "tasks_created": 0,
                    "subtasks_created": 0,
                    "comments_added": 0,
                    "task_state_changes": 0,
                    "tasks_completed": 0,
                    "custom_fields_created": 0,
                    "sections_created": 0,
                    "tags_created": 0,
                    "portfolios_created": 0,
                    "errors": 0
                },
                "api_usage": {
                    "asana_calls_today": 0,
                    "llm_calls_today": 0,
                    "llm_tokens_today": 0,
                    "last_reset": now
                }
            })
        elif connection_type == "okta":
            state.update({
                "users": [],
                "groups": [],
                "app_assignments": [],
                "stats": {
                    "users_created": 0,
                    "groups_created": 0,
                    "app_assignments_created": 0,
                    "user_group_assignments": 0,
                    "user_activations": 0,
                    "user_deactivations": 0,
                    "errors": 0
                },
                "api_usage": {
                    "okta_calls_today": 0,
                    "llm_calls_today": 0,
                    "llm_tokens_today": 0,
                    "last_reset": now
                }
            })
        else:
            # Generic fallback for unknown connection types
            state.update({
                "stats": {
                    "errors": 0
                },
                "api_usage": {
                    "api_calls_today": 0,
                    "llm_calls_today": 0,
                    "llm_tokens_today": 0,
                    "last_reset": now
                }
            })

        self.save_state(job_id, state)
        return job_id

    def _migrate_legacy_job(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate legacy job state to current format.

        Adds connection_type field for jobs created before multi-connection support.
        Legacy jobs are assumed to be Asana jobs.

        Args:
            state: Job state dictionary

        Returns:
            Migrated state dictionary
        """
        if "connection_type" not in state:
            state["connection_type"] = "asana"  # Legacy jobs are Asana
        return state

    def load_state(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Load state for a job.

        Automatically migrates legacy job files that don't have connection_type.

        Args:
            job_id: Job ID to load

        Returns:
            State dictionary or None if not found
        """
        state_file = self.state_dir / f"job_{job_id}.json"

        if not state_file.exists():
            return None

        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
            # Migrate legacy jobs to current format
            state = self._migrate_legacy_job(state)
            return state
        except Exception as e:
            print(f"Error loading state for job {job_id}: {e}")
            return None

    def save_state(self, job_id: str, state: Dict[str, Any]):
        """
        Save state for a job.

        Args:
            job_id: Job ID
            state: State dictionary to save
        """
        state_file = self.state_dir / f"job_{job_id}.json"
        state["last_saved"] = datetime.now(timezone.utc).isoformat()

        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Error saving state for job {job_id}: {e}")

    def update_last_activity(self, job_id: str):
        """
        Update last activity timestamp.

        Args:
            job_id: Job ID
        """
        state = self.load_state(job_id)
        if state:
            state["last_activity"] = datetime.now(timezone.utc).isoformat()
            self.save_state(job_id, state)

    def add_project(self, job_id: str, project: Dict[str, Any]):
        """
        Add a project to the state.

        Args:
            job_id: Job ID
            project: Project data dictionary
        """
        state = self.load_state(job_id)
        if state:
            project_entry = {
                "id": project.get("gid"),
                "name": project.get("name"),
                "status": "in_progress",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "tasks": []
            }
            state["projects"].append(project_entry)
            state["stats"]["projects_created"] += 1

            # Update initialization progress if plan exists
            if "initialization_plan" in state:
                state["initialization_plan"]["completed_projects"] += 1

            self.save_state(job_id, state)

    def add_task(self, job_id: str, project_id: str, task: Dict[str, Any]):
        """
        Add a task to a project in the state.

        Args:
            job_id: Job ID
            project_id: Project GID
            task: Task data dictionary
        """
        state = self.load_state(job_id)
        if state:
            # Find the project
            for project in state["projects"]:
                if project["id"] == project_id:
                    task_entry = {
                        "id": task.get("gid"),
                        "name": task.get("name"),
                        "status": "new",
                        "assignee": task.get("assignee", {}).get("gid") if task.get("assignee") else None,
                        "assignee_name": task.get("assignee", {}).get("name") if task.get("assignee") else None,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "started_at": None,
                        "blocked_at": None,
                        "blocker_reason": None,
                        "completed_at": None,
                        "subtasks": [],
                        "comment_count": 0,
                        "last_comment_at": None
                    }
                    project["tasks"].append(task_entry)
                    state["stats"]["tasks_created"] += 1

                    # Update initialization progress if plan exists
                    if "initialization_plan" in state:
                        state["initialization_plan"]["completed_tasks"] += 1

                    break
            self.save_state(job_id, state)

    def update_task_status(self, job_id: str, task_id: str, new_status: str,
                          additional_data: Optional[Dict] = None):
        """
        Update task status in state.

        Args:
            job_id: Job ID
            task_id: Task GID
            new_status: New status ('in_progress', 'blocked', 'completed')
            additional_data: Optional additional data to update
        """
        state = self.load_state(job_id)
        if state:
            now = datetime.now(timezone.utc).isoformat()

            # Find the task across all projects
            for project in state["projects"]:
                for task in project["tasks"]:
                    if task["id"] == task_id:
                        task["status"] = new_status

                        if new_status == "in_progress" and not task["started_at"]:
                            task["started_at"] = now
                        elif new_status == "blocked":
                            task["blocked_at"] = now
                            if additional_data and "blocker_reason" in additional_data:
                                task["blocker_reason"] = additional_data["blocker_reason"]
                        elif new_status == "completed":
                            task["completed_at"] = now
                            state["stats"]["tasks_completed"] += 1

                        if additional_data:
                            task.update(additional_data)

                        state["stats"]["task_state_changes"] += 1
                        self.save_state(job_id, state)
                        return

    def add_comment(self, job_id: str, task_id: str, comment: Dict[str, Any]):
        """
        Record a comment in the state.

        Args:
            job_id: Job ID
            task_id: Task GID
            comment: Comment data
        """
        state = self.load_state(job_id)
        if state:
            now = datetime.now(timezone.utc).isoformat()

            # Update task comment count
            for project in state["projects"]:
                for task in project["tasks"]:
                    if task["id"] == task_id:
                        task["comment_count"] += 1
                        task["last_comment_at"] = now
                        break

            state["stats"]["comments_added"] += 1

            # Update initialization progress if plan exists
            if "initialization_plan" in state:
                state["initialization_plan"]["completed_comments"] += 1

            self.save_state(job_id, state)

    def log_activity(self, job_id: str, action: str, details: Dict[str, Any]):
        """
        Log an activity to the activity log.

        Args:
            job_id: Job ID
            action: Type of action (e.g., 'comment_added', 'task_created')
            details: Details about the action
        """
        state = self.load_state(job_id)
        if state:
            activity_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": action,
                "details": details
            }
            state["activity_log"].append(activity_entry)

            # Keep only last 1000 activities to prevent file from growing too large
            if len(state["activity_log"]) > 1000:
                state["activity_log"] = state["activity_log"][-1000:]

            self.save_state(job_id, state)

    def log_error(self, job_id: str, error_type: str, error_message: str):
        """
        Log an error.

        Args:
            job_id: Job ID
            error_type: Type of error
            error_message: Error message
        """
        state = self.load_state(job_id)
        if state:
            error_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": error_type,
                "message": error_message
            }
            state["errors"].append(error_entry)
            state["stats"]["errors"] += 1

            # Keep only last 100 errors
            if len(state["errors"]) > 100:
                state["errors"] = state["errors"][-100:]

            self.save_state(job_id, state)

    def increment_api_usage(self, job_id: str, api_type: str, count: int = 1,
                           tokens: int = 0):
        """
        Increment API usage counters.

        Args:
            job_id: Job ID
            api_type: Type of API ('asana' or 'llm')
            count: Number of calls to add
            tokens: Number of tokens (for LLM calls)
        """
        state = self.load_state(job_id)
        if state:
            now = datetime.now(timezone.utc).isoformat()

            # Check if we need to reset daily counters
            last_reset = datetime.fromisoformat(state["api_usage"]["last_reset"])
            current_time = datetime.now(timezone.utc)

            if current_time.date() > last_reset.date():
                # New day - reset counters
                state["api_usage"]["asana_calls_today"] = 0
                state["api_usage"]["llm_calls_today"] = 0
                state["api_usage"]["llm_tokens_today"] = 0
                state["api_usage"]["last_reset"] = now

            # Increment appropriate counter
            if api_type == "asana":
                state["api_usage"]["asana_calls_today"] += count
            elif api_type == "llm":
                state["api_usage"]["llm_calls_today"] += count
                state["api_usage"]["llm_tokens_today"] += tokens

            self.save_state(job_id, state)

    def update_job_status(self, job_id: str, status: str):
        """
        Update job status.

        Args:
            job_id: Job ID
            status: New status ('running', 'paused', 'stopped', 'error')
        """
        state = self.load_state(job_id)
        if state:
            state["status"] = status
            self.save_state(job_id, state)

    def update_next_activity_time(self, job_id: str, next_time: str):
        """
        Update the next scheduled activity time.

        Args:
            job_id: Job ID
            next_time: ISO format datetime string for next activity
        """
        state = self.load_state(job_id)
        if state:
            state["next_activity_time"] = next_time
            self.save_state(job_id, state)

    def get_all_jobs(self, connection_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of all jobs with basic info.

        IMPORTANT: Filters out jobs marked for deletion (_deleting=True).
        These are tombstone files that prevent race conditions during deletion.

        Args:
            connection_type: Optional filter by connection type ('asana', 'okta', etc.)

        Returns:
            List of job summaries (excluding jobs marked for deletion)
        """
        jobs = []

        for state_file in self.state_dir.glob("job_*.json"):
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)

                    # CRITICAL: Skip jobs marked for deletion (tombstone pattern)
                    if state.get("_deleting"):
                        continue

                    # Migrate legacy jobs
                    state = self._migrate_legacy_job(state)

                    # Filter by connection type if specified
                    if connection_type and state.get("connection_type") != connection_type:
                        continue

                    jobs.append({
                        "job_id": state["job_id"],
                        "job_name": state.get("job_name"),
                        "connection_type": state.get("connection_type", "asana"),  # NEW
                        "status": state["status"],
                        "started_at": state["started_at"],
                        "last_activity": state["last_activity"],
                        "next_activity_time": state.get("next_activity_time"),
                        "vendor": state["config"].get("vendor", "asana"),
                        "industry": state["config"].get("industry", "Unknown"),
                        "workspace_name": state["config"].get("workspace_name", "Unknown"),
                        "stats": state["stats"]
                    })
            except Exception as e:
                print(f"Error loading {state_file}: {e}")

        # Sort by last activity (most recent first)
        jobs.sort(key=lambda x: x["last_activity"], reverse=True)
        return jobs

    def get_task_by_id(self, job_id: str, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Find and return a task by its ID.

        Args:
            job_id: Job ID
            task_id: Task GID

        Returns:
            Task dictionary or None if not found
        """
        state = self.load_state(job_id)
        if state:
            for project in state["projects"]:
                for task in project["tasks"]:
                    if task["id"] == task_id:
                        return task
        return None

    def get_tasks_by_status(self, job_id: str, status: str) -> List[Dict[str, Any]]:
        """
        Get all tasks with a specific status.

        Args:
            job_id: Job ID
            status: Status to filter by

        Returns:
            List of tasks with that status
        """
        tasks = []
        state = self.load_state(job_id)
        if state:
            for project in state["projects"]:
                for task in project["tasks"]:
                    if task["status"] == status:
                        tasks.append(task)
        return tasks

    def get_jobs_by_connection_type(self, connection_type: str) -> List[Dict[str, Any]]:
        """
        Get all jobs for a specific connection type.

        Convenience method that wraps get_all_jobs with filtering.

        Args:
            connection_type: Connection type to filter by ('asana', 'okta', etc.)

        Returns:
            List of job summaries for the specified connection type
        """
        return self.get_all_jobs(connection_type=connection_type)

    def get_connection_type(self, job_id: str) -> Optional[str]:
        """
        Get the connection type for a job.

        Args:
            job_id: Job ID

        Returns:
            Connection type string ('asana', 'okta', etc.) or None if job not found
        """
        state = self.load_state(job_id)
        if state:
            return state.get("connection_type", "asana")  # Default to asana for legacy jobs
        return None

    def validate_state_structure(self, state: Dict[str, Any]) -> bool:
        """
        Validate state has required fields for its connection type.

        Checks for:
        - Common fields: job_id, connection_type, status, config
        - Connection-specific fields based on connection_type

        Args:
            state: State dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        # Check common required fields
        required_common = ["job_id", "status", "config"]
        for field in required_common:
            if field not in state:
                return False

        # Connection type should exist (or be migratable)
        connection_type = state.get("connection_type")
        if not connection_type:
            # Check if this is a legacy Asana job (has 'projects' field)
            if "projects" in state:
                return True  # Valid legacy job
            return False

        # Validate connection-specific fields
        if connection_type == "asana":
            required_asana = ["projects", "stats"]
            return all(field in state for field in required_asana)
        elif connection_type == "okta":
            required_okta = ["users", "groups", "stats"]
            return all(field in state for field in required_okta)

        # Unknown connection types are valid if they have stats
        return "stats" in state

    def mark_for_deletion(self, job_id: str) -> bool:
        """
        Mark a job for deletion with an atomic flag.
        This prevents background threads from saving state after deletion starts.

        Works for all connection types.

        Args:
            job_id: Job ID to mark

        Returns:
            True if marked successfully, False if job not found
        """
        state = self.load_state(job_id)
        if not state:
            return False

        state["_deleting"] = True
        state["_deletion_timestamp"] = datetime.now(timezone.utc).isoformat()
        self.save_state(job_id, state)
        return True

    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job state file.

        Args:
            job_id: Job ID to delete

        Returns:
            True if deleted, False if not found
        """
        state_file = self.state_dir / f"job_{job_id}.json"
        if state_file.exists():
            try:
                os.remove(state_file)
                return True
            except Exception as e:
                print(f"Error deleting job {job_id}: {e}")
                return False
        return False


# Example usage
if __name__ == "__main__":
    # Test the state manager with multiple connection types
    manager = StateManager("./test_states")

    # ========== Example 1: Asana Job ==========
    print("=== Creating Asana Job ===")
    asana_config = {
        "connection_type": "asana",
        "industry": "healthcare",
        "duration_days": 30,
        "workspace_gid": "123456",
        "workspace_name": "Test Workspace"
    }

    asana_job_id = manager.create_new_job(asana_config)
    print(f"Created Asana job: {asana_job_id}")

    # Add a project
    project = {
        "gid": "proj_001",
        "name": "Electronic Health Records Migration"
    }
    manager.add_project(asana_job_id, project)

    # Add a task
    task = {
        "gid": "task_001",
        "name": "Update HIPAA documentation",
        "assignee": {"gid": "user_001", "name": "Alice"}
    }
    manager.add_task(asana_job_id, "proj_001", task)

    # Update task status
    manager.update_task_status(asana_job_id, "task_001", "in_progress")

    # Add a comment
    comment = {"text": "Starting work on this"}
    manager.add_comment(asana_job_id, "task_001", comment)

    # Log activity
    manager.log_activity(asana_job_id, "comment_added", {
        "task_id": "task_001",
        "user": "Alice"
    })

    # ========== Example 2: Okta Job ==========
    print("\n=== Creating Okta Job ===")
    okta_config = {
        "connection_type": "okta",
        "job_name": "Okta User Management",
        "domain": "dev-123456.okta.com"
    }

    okta_job_id = manager.create_new_job(okta_config)
    print(f"Created Okta job: {okta_job_id}")

    # Log some Okta activities
    manager.log_activity(okta_job_id, "create_user", {
        "user_id": "user_001",
        "email": "john.doe@example.com"
    })

    manager.log_activity(okta_job_id, "create_group", {
        "group_id": "group_001",
        "name": "Engineering Team"
    })

    # ========== Example 3: Query Jobs ==========
    print("\n=== All Jobs ===")
    all_jobs = manager.get_all_jobs()
    print(f"Total jobs: {len(all_jobs)}")
    for job in all_jobs:
        print(f"  {job['job_id']}: {job['connection_type']} - {job['status']}")

    print("\n=== Asana Jobs Only ===")
    asana_jobs = manager.get_jobs_by_connection_type("asana")
    print(f"Asana jobs: {len(asana_jobs)}")
    for job in asana_jobs:
        print(f"  {job['job_id']}: {job.get('industry', 'N/A')}")

    print("\n=== Okta Jobs Only ===")
    okta_jobs = manager.get_jobs_by_connection_type("okta")
    print(f"Okta jobs: {len(okta_jobs)}")
    for job in okta_jobs:
        print(f"  {job['job_id']}: {job.get('job_name', 'N/A')}")

    # ========== Example 4: Helper Methods ==========
    print("\n=== Helper Methods ===")
    print(f"Asana job connection type: {manager.get_connection_type(asana_job_id)}")
    print(f"Okta job connection type: {manager.get_connection_type(okta_job_id)}")

    # Validate states
    asana_state = manager.load_state(asana_job_id)
    okta_state = manager.load_state(okta_job_id)
    print(f"Asana state valid: {manager.validate_state_structure(asana_state)}")
    print(f"Okta state valid: {manager.validate_state_structure(okta_state)}")

    # ========== Example 5: Display Stats ==========
    print("\n=== Asana Job Stats ===")
    print(f"  Projects: {asana_state['stats']['projects_created']}")
    print(f"  Tasks: {asana_state['stats']['tasks_created']}")
    print(f"  Comments: {asana_state['stats']['comments_added']}")

    print("\n=== Okta Job Stats ===")
    print(f"  Users: {okta_state['stats']['users_created']}")
    print(f"  Groups: {okta_state['stats']['groups_created']}")

    # ========== Example 6: Legacy Migration ==========
    print("\n=== Testing Legacy Migration ===")
    # Simulate loading a legacy job (without connection_type)
    legacy_state = {
        "job_id": "legacy123",
        "status": "running",
        "config": {"industry": "finance"},
        "projects": [],
        "stats": {"projects_created": 5}
    }
    migrated = manager._migrate_legacy_job(legacy_state)
    print(f"Legacy job migrated: connection_type = {migrated.get('connection_type')}")
