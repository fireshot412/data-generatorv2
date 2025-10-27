#!/usr/bin/env python3
"""
Activity Scheduler for generating realistic work patterns.
Handles timing of activities based on work hours, burst patterns, etc.
"""

import random
from datetime import datetime, time, timedelta, timezone
from typing import Dict, List, Optional, Any
from enum import Enum


class ActivityType(Enum):
    """Types of activities that can be generated."""
    COMMENT_START_WORK = "comment_start_work"
    COMMENT_PROGRESS = "comment_progress"
    COMMENT_BLOCKED = "comment_blocked"
    COMMENT_UNBLOCKED = "comment_unblocked"
    COMMENT_COMPLETED = "comment_completed"
    COMMENT_CONVERSATION = "comment_conversation"
    COMMENT_OOO = "comment_ooo"
    TASK_STATUS_CHANGE = "task_status_change"
    TASK_REASSIGNMENT = "task_reassignment"
    CREATE_TASK = "create_task"
    CREATE_SUBTASK = "create_subtask"
    CREATE_PROJECT = "create_project"
    COMPLETE_TASK = "complete_task"


class WorkingHoursType(Enum):
    """Types of working hours patterns."""
    US_WORKFORCE = "us_workforce"  # 9am-6pm PT, Mon-Fri
    GLOBAL = "global"  # 24-hour coverage with regional peaks


class ActivityScheduler:
    """Schedules realistic activity generation based on work patterns."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize scheduler with configuration.

        Args:
            config: Configuration dictionary with:
                - activity_level: 'low', 'medium', 'high'
                - working_hours: 'us_workforce' or 'global'
                - burst_factor: 0.0-1.0 (0=bursty, 1=steady)
                - comment_frequency: comments per task per day
                - task_completion_rate: % of tasks completed per week
                - blocked_task_frequency: % of tasks that get blocked
                - blocked_task_duration: average days blocked
        """
        self.config = config

        # Activity level multipliers
        self.activity_multipliers = {
            "low": 0.3,
            "medium": 1.0,
            "high": 2.0
        }

        # Parse config
        self.activity_level = config.get("activity_level", "medium")
        self.working_hours_type = WorkingHoursType(config.get("working_hours", "us_workforce"))
        self.burst_factor = config.get("burst_factor", 0.5)  # 0=bursty, 1=steady
        self.comment_frequency = config.get("comment_frequency", 0.5)  # per task per day
        self.task_completion_rate = config.get("task_completion_rate", 20)  # % per week
        self.blocked_frequency = config.get("blocked_task_frequency", 15)  # % of tasks
        self.blocked_duration = config.get("blocked_task_duration", 2)  # days

        # Activity base rates (per hour during work hours)
        self.base_activity_rate = self.activity_multipliers.get(self.activity_level, 1.0)

    def is_working_hours(self, dt: datetime) -> bool:
        """
        Check if given datetime is within working hours.

        Args:
            dt: Datetime to check (should be timezone-aware)

        Returns:
            True if within working hours
        """
        # Weekend check (universal)
        if dt.weekday() >= 5:  # Saturday=5, Sunday=6
            # 5% chance of activity on weekends for urgent issues
            return random.random() < 0.05

        if self.working_hours_type == WorkingHoursType.US_WORKFORCE:
            # 9am-6pm Pacific Time (Mon-Fri)
            # Convert to Pacific Time for checking
            # Note: This is simplified - real implementation would handle timezones properly
            hour = dt.hour

            # Assuming dt is in local timezone
            # Core hours: 9am-6pm
            if 9 <= hour < 18:
                return True

            # Early birds (7-9am): 20% chance
            if 7 <= hour < 9:
                return random.random() < 0.2

            # Night owls (6-9pm): 15% chance
            if 18 <= hour < 21:
                return random.random() < 0.15

            return False

        elif self.working_hours_type == WorkingHoursType.GLOBAL:
            # 24-hour coverage with peaks at regional start times
            # Higher activity during typical business hours (6am-8pm in any timezone)
            hour = dt.hour

            # Peak hours (8am-6pm local): full activity
            if 8 <= hour < 18:
                return True

            # Early/late hours (6-8am, 6-10pm): 50% activity
            if (6 <= hour < 8) or (18 <= hour < 22):
                return random.random() < 0.5

            # Night shift (10pm-6am): 20% activity
            return random.random() < 0.2

        return True

    def is_burst_time(self, dt: datetime) -> bool:
        """
        Check if this is a burst activity time (e.g., 9am, post-lunch).

        Args:
            dt: Datetime to check

        Returns:
            True if this is a burst time
        """
        hour = dt.hour

        # Burst times: 9am (start of day), 1pm (post-lunch), 4pm (pre-EOD push)
        burst_hours = [9, 13, 16]

        if hour in burst_hours:
            # More likely to be burst time if burst_factor is low (bursty)
            return random.random() < (1.0 - self.burst_factor * 0.7)

        return False

    def should_generate_activity(self, current_time: datetime) -> bool:
        """
        Determine if activity should be generated at this time.

        Args:
            current_time: Current datetime

        Returns:
            True if activity should be generated
        """
        # Check if in working hours
        if not self.is_working_hours(current_time):
            return False

        # Base probability of activity per minute
        base_prob = self.base_activity_rate * 0.1  # 10% base per minute during work hours

        # Increase probability during burst times
        if self.is_burst_time(current_time):
            base_prob *= 2.0

        # Adjust based on burst factor (steady vs bursty)
        # Lower burst_factor means more concentrated activity
        if self.burst_factor < 0.5:
            # Bursty - if we're generating, generate more
            if random.random() < base_prob:
                base_prob *= 1.5

        return random.random() < base_prob

    def get_next_activity_time(self, current_time: datetime) -> datetime:
        """
        Calculate when next activity should occur.

        Args:
            current_time: Current datetime

        Returns:
            Datetime for next activity
        """
        # Start checking from next minute
        check_time = current_time + timedelta(minutes=1)

        # Keep checking until we find a time for activity
        max_checks = 60 * 24  # Check up to 24 hours ahead
        for _ in range(max_checks):
            if self.should_generate_activity(check_time):
                return check_time

            # Increment by 1-5 minutes randomly
            check_time += timedelta(minutes=random.randint(1, 5))

        # Fallback: return time 1 hour from now
        return current_time + timedelta(hours=1)

    def select_activity_type(self, state: Dict[str, Any]) -> ActivityType:
        """
        Select what type of activity to generate based on current state.

        Args:
            state: Current job state

        Returns:
            ActivityType to generate
        """
        weights = []
        activity_types = []

        # Count tasks by status
        task_counts = {"new": 0, "in_progress": 0, "blocked": 0, "completed": 0}
        total_tasks = 0

        for project in state.get("projects", []):
            for task in project.get("tasks", []):
                status = task.get("status", "new")
                task_counts[status] = task_counts.get(status, 0) + 1
                total_tasks += 1

        if total_tasks == 0:
            # No tasks yet - create initial tasks
            return ActivityType.CREATE_TASK

        # Calculate probabilities based on state

        # Start work on new tasks
        if task_counts["new"] > 0:
            activity_types.append(ActivityType.COMMENT_START_WORK)
            weights.append(30)  # High priority

        # Progress updates on in-progress tasks
        if task_counts["in_progress"] > 0:
            activity_types.append(ActivityType.COMMENT_PROGRESS)
            weights.append(20)

        # Block some in-progress tasks
        if task_counts["in_progress"] > 0:
            block_prob = self.blocked_frequency / 100.0
            activity_types.append(ActivityType.COMMENT_BLOCKED)
            weights.append(block_prob * 100)

        # Unblock blocked tasks
        if task_counts["blocked"] > 0:
            activity_types.append(ActivityType.COMMENT_UNBLOCKED)
            weights.append(25)

        # Complete in-progress tasks
        if task_counts["in_progress"] > 0:
            activity_types.append(ActivityType.COMPLETE_TASK)
            weights.append(15)

        # Conversational comments (responses)
        if total_tasks > 0:
            activity_types.append(ActivityType.COMMENT_CONVERSATION)
            weights.append(25)

        # Create new tasks occasionally
        activity_types.append(ActivityType.CREATE_TASK)
        weights.append(10)

        # Create subtasks occasionally
        if total_tasks > 0:
            activity_types.append(ActivityType.CREATE_SUBTASK)
            weights.append(5)

        # Reassign tasks occasionally
        if task_counts["in_progress"] > 0:
            activity_types.append(ActivityType.TASK_REASSIGNMENT)
            weights.append(3)

        # Out of office comments (rare)
        activity_types.append(ActivityType.COMMENT_OOO)
        weights.append(2)

        # Weighted random selection
        if not activity_types:
            return ActivityType.CREATE_TASK

        return random.choices(activity_types, weights=weights)[0]

    def should_create_new_project(self, state: Dict[str, Any]) -> bool:
        """
        Determine if a new project should be created.

        Args:
            state: Current job state

        Returns:
            True if new project should be created
        """
        projects = state.get("projects", [])

        if len(projects) == 0:
            # Always create first project
            return True

        # Check if last project is mostly complete
        if projects:
            last_project = projects[-1]
            tasks = last_project.get("tasks", [])

            if not tasks:
                # Empty project, don't create another yet
                return False

            completed = sum(1 for t in tasks if t.get("status") == "completed")
            completion_rate = completed / len(tasks) if tasks else 0

            # Create new project if last one is >80% complete
            if completion_rate > 0.8:
                return random.random() < 0.3  # 30% chance

        # Also create new project based on config
        project_frequency = self.config.get("new_project_frequency_days", 14)
        if len(projects) > 0:
            last_created = datetime.fromisoformat(projects[-1]["created_at"])
            days_since = (datetime.now(timezone.utc) - last_created).days

            if days_since >= project_frequency:
                return random.random() < 0.5  # 50% chance if enough time passed

        return False

    def should_task_be_blocked(self, task: Dict[str, Any]) -> bool:
        """
        Determine if a task should become blocked.

        Args:
            task: Task data

        Returns:
            True if task should be blocked
        """
        # Only block in-progress tasks
        if task.get("status") != "in_progress":
            return False

        # Check if already been blocked before
        if task.get("blocked_at"):
            # Don't block again
            return False

        # Use configured frequency
        return random.random() < (self.blocked_frequency / 100.0)

    def should_task_be_unblocked(self, task: Dict[str, Any]) -> bool:
        """
        Determine if a blocked task should be unblocked.

        Args:
            task: Task data

        Returns:
            True if task should be unblocked
        """
        if task.get("status") != "blocked":
            return False

        if not task.get("blocked_at"):
            # No blocked timestamp, unblock it
            return True

        # Check how long it's been blocked
        blocked_at = datetime.fromisoformat(task["blocked_at"])
        days_blocked = (datetime.now(timezone.utc) - blocked_at).days

        # Probability increases with time
        if days_blocked >= self.blocked_duration:
            return random.random() < 0.7  # 70% chance if at average duration

        # Lower probability before average duration
        prob = days_blocked / self.blocked_duration * 0.3  # Up to 30% before target
        return random.random() < prob

    def select_task_for_activity(self, state: Dict[str, Any],
                                 activity_type: ActivityType) -> Optional[Dict[str, Any]]:
        """
        Select an appropriate task for the activity type.

        Args:
            state: Current job state
            activity_type: Type of activity

        Returns:
            Task dict or None if no suitable task
        """
        all_tasks = []
        for project in state.get("projects", []):
            for task in project.get("tasks", []):
                task["_project_id"] = project["id"]  # Add project reference
                all_tasks.append(task)

        if not all_tasks:
            return None

        # Filter based on activity type
        if activity_type == ActivityType.COMMENT_START_WORK:
            candidates = [t for t in all_tasks if t.get("status") == "new"]
        elif activity_type == ActivityType.COMMENT_PROGRESS:
            candidates = [t for t in all_tasks if t.get("status") == "in_progress"]
        elif activity_type == ActivityType.COMMENT_BLOCKED:
            candidates = [t for t in all_tasks
                         if t.get("status") == "in_progress" and not t.get("blocked_at")]
        elif activity_type == ActivityType.COMMENT_UNBLOCKED:
            candidates = [t for t in all_tasks if t.get("status") == "blocked"]
        elif activity_type == ActivityType.COMPLETE_TASK:
            candidates = [t for t in all_tasks
                         if t.get("status") == "in_progress" and not t.get("blocked_at")]
        else:
            # Any task
            candidates = all_tasks

        if not candidates:
            return None

        return random.choice(candidates)

    def get_activity_stats(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get statistics about current activity state.

        Args:
            state: Current job state

        Returns:
            Statistics dictionary
        """
        task_counts = {"new": 0, "in_progress": 0, "blocked": 0, "completed": 0}
        total_tasks = 0

        for project in state.get("projects", []):
            for task in project.get("tasks", []):
                status = task.get("status", "new")
                task_counts[status] = task_counts.get(status, 0) + 1
                total_tasks += 1

        return {
            "total_tasks": total_tasks,
            "task_counts": task_counts,
            "projects": len(state.get("projects", [])),
            "activity_rate": self.base_activity_rate,
            "is_working_hours": self.is_working_hours(datetime.now(timezone.utc))
        }


# Example usage
if __name__ == "__main__":
    # Test scheduler
    config = {
        "activity_level": "medium",
        "working_hours": "us_workforce",
        "burst_factor": 0.3,  # Bursty
        "comment_frequency": 0.5,
        "task_completion_rate": 20,
        "blocked_task_frequency": 15,
        "blocked_task_duration": 2
    }

    scheduler = ActivityScheduler(config)

    print("Testing Activity Scheduler")
    print("=" * 60)

    # Test different times
    test_times = [
        datetime(2024, 10, 15, 9, 0),   # 9am Tuesday - should be burst time
        datetime(2024, 10, 15, 14, 30), # 2:30pm Tuesday - normal work
        datetime(2024, 10, 15, 19, 0),  # 7pm Tuesday - after hours
        datetime(2024, 10, 19, 10, 0),  # 10am Saturday - weekend
    ]

    for dt in test_times:
        print(f"\nTime: {dt.strftime('%A %I:%M %p')}")
        print(f"  Working hours: {scheduler.is_working_hours(dt)}")
        print(f"  Burst time: {scheduler.is_burst_time(dt)}")
        print(f"  Should generate: {scheduler.should_generate_activity(dt)}")

    # Test activity selection
    print("\n" + "=" * 60)
    print("Testing activity selection")

    mock_state = {
        "projects": [{
            "id": "proj1",
            "tasks": [
                {"id": "task1", "status": "new"},
                {"id": "task2", "status": "in_progress"},
                {"id": "task3", "status": "in_progress"},
                {"id": "task4", "status": "blocked", "blocked_at": "2024-10-13T10:00:00+00:00"},
            ]
        }]
    }

    for i in range(10):
        activity = scheduler.select_activity_type(mock_state)
        print(f"  Activity {i+1}: {activity.value}")
