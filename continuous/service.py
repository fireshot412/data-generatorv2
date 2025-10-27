#!/usr/bin/env python3
"""
Continuous Generation Service - Main orchestrator for realistic ongoing data generation.
"""

import asyncio
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from continuous.llm_generator import LLMGenerator
from continuous.state_manager import StateManager
from continuous.scheduler import ActivityScheduler, ActivityType
from continuous.asana_client import AsanaClientPool, AsanaClient, AsanaAPIError, AsanaRateLimitError
from continuous.industry_templates import INDUSTRY_TEMPLATES, get_random_use_case


class ContinuousService:
    """Main service for continuous data generation."""

    def __init__(self, config: Dict[str, Any], state_manager: StateManager,
                 llm_generator: LLMGenerator, client_pool: AsanaClientPool):
        """
        Initialize continuous service.

        Args:
            config: Job configuration
            state_manager: State manager instance
            llm_generator: LLM generator instance
            client_pool: Pool of Asana clients
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

        # Cache workspace-level Asana objects to avoid recreating them
        self.workspace_custom_fields = {}  # {field_name: field_gid}
        self.workspace_tags = {}  # {tag_name: tag_gid}
        self.workspace_portfolios = {}  # {portfolio_name: portfolio_gid}

        print(f"✓ Continuous service initialized - Job ID: {self.job_id}")

    async def run(self):
        """Main loop - runs continuously until stopped."""
        self.running = True

        # IMPROVED: Set status to "initializing" during initial data generation
        # This will be changed to "running" after bootstrap completes
        initial_generation = len(self.state["projects"]) == 0
        if initial_generation:
            self.state_manager.update_job_status(self.job_id, "initializing")
        else:
            self.state_manager.update_job_status(self.job_id, "running")

        print(f"Starting continuous generation for {self.config.get('industry')} workspace...")
        print(f"Duration: {self.config.get('duration_days', 'indefinite')} days")

        # Initialize with initial projects if none exist
        if initial_generation:
            await self._create_initial_projects()
            # Bootstrap with initial activity to provide immediate data
            await self._bootstrap_initial_activity()
            # CRITICAL: Transition to "running" after initial generation completes
            self.state_manager.update_job_status(self.job_id, "running")
            print("✓ Initial generation complete - job is now running")
        else:
            # Check if we missed any scheduled activities (catch-up logic)
            await self._catch_up_missed_activities()

        # Main loop
        while self.running and self._should_continue():
            try:
                if self.paused:
                    await asyncio.sleep(60)  # Check every minute if paused
                    continue

                # Check if it's time for activity
                current_time = datetime.now(timezone.utc)

                if self.scheduler.should_generate_activity(current_time):
                    await self._generate_activity()

                    # Update next activity time after generating activity
                    next_time = self.scheduler.get_next_activity_time(current_time)
                    self.state_manager.update_next_activity_time(self.job_id, next_time.isoformat())
                else:
                    # Update next activity time if not set
                    if not self.state.get("next_activity_time"):
                        next_time = self.scheduler.get_next_activity_time(current_time)
                        self.state_manager.update_next_activity_time(self.job_id, next_time.isoformat())

                # Reload state from disk to respect external changes (like deletion)
                # DO NOT save after reloading - this would overwrite deletion markers!
                if not self.deleted:
                    disk_state = self.state_manager.load_state(self.job_id)

                    # CRITICAL: Check for deletion marker FIRST (atomic flag beats all other checks)
                    if disk_state is None or disk_state.get("_deleting"):
                        print(f"[Job {self.job_id}] Deletion marker detected - exiting immediately")
                        self.running = False
                        self.deleted = True
                        return

                    # Then check for stopped status (manual stop operation)
                    if disk_state.get("status") == "stopped":
                        print(f"[Job {self.job_id}] Job stopped - exiting")
                        self.running = False
                        self.deleted = True
                        return

                    # Update our in-memory state with the disk version
                    self.state = disk_state

                    # NOTE: We do NOT save here! Saving would overwrite any external changes
                    # (like deletion markers) that were made between our reload and save.
                    # State is already persisted by other operations (task creation, status updates, etc.)

                # Sleep for a bit before next check
                await asyncio.sleep(random.randint(30, 90))  # 30-90 seconds

            except AsanaRateLimitError as e:
                print(f"⚠ Rate limit hit: {e}")
                self.state_manager.log_error(self.job_id, "rate_limit", str(e))

                # Generate OOO message
                await self._handle_rate_limit_pause()

                # Pause for retry period
                await asyncio.sleep(3600)  # 1 hour

            except Exception as e:
                print(f"✗ Error in main loop: {e}")
                self.state_manager.log_error(self.job_id, "general", str(e))
                await asyncio.sleep(300)  # 5 minutes before retry

        # Clean shutdown
        self.state_manager.update_job_status(self.job_id, "stopped")
        print(f"Continuous generation stopped for job {self.job_id}")

    def _should_continue(self) -> bool:
        """Check if job should continue running."""
        if self.config.get("duration_days") == "indefinite":
            return True

        # Check duration
        started_at = datetime.fromisoformat(self.state["started_at"])
        duration_days = self.config.get("duration_days", 30)
        elapsed_days = (datetime.now(timezone.utc) - started_at).days

        return elapsed_days < duration_days

    async def _create_initial_projects(self):
        """Create initial projects to start with."""
        num_projects = self.config.get("initial_projects", 3)

        print(f"Creating {num_projects} initial projects...")

        for i in range(num_projects):
            try:
                await self._create_project()
                await asyncio.sleep(2)  # Space out creations
            except Exception as e:
                print(f"Error creating initial project {i+1}: {e}")

    async def _bootstrap_initial_activity(self):
        """
        Bootstrap with additional activity on tasks that were just created.
        Subtasks and initial comments are now created during project setup (depth-first).
        This adds a few more comments and task state changes for variety.
        """
        print("Bootstrapping additional activity...")

        # Reload state to get latest tasks
        self.state = self.state_manager.load_state(self.job_id)

        # Generate a few additional activities across tasks (3-6 activities)
        num_activities = random.randint(3, 6)

        for i in range(num_activities):
            try:
                # Select random activity types that make sense for new tasks
                activity_types = [
                    ActivityType.COMMENT_START_WORK,
                    ActivityType.COMMENT_PROGRESS,
                ]

                activity_type = random.choice(activity_types)

                if activity_type == ActivityType.COMMENT_START_WORK:
                    await self._handle_start_work()
                elif activity_type == ActivityType.COMMENT_PROGRESS:
                    await self._handle_progress_update()

                # Small delay between activities
                await asyncio.sleep(1)

            except Exception as e:
                print(f"Error in bootstrap activity {i+1}: {e}")

        print(f"✓ Bootstrapped {num_activities} additional activities")

        # Log the next scheduled activity time
        next_time = self.scheduler.get_next_activity_time(datetime.now(timezone.utc))
        print(f"Next scheduled activity: {next_time.strftime('%Y-%m-%d %I:%M %p %Z')}")

        # Store next activity time in state
        self.state_manager.update_next_activity_time(self.job_id, next_time.isoformat())

    async def _catch_up_missed_activities(self):
        """
        Check if scheduled activity was missed while server was down.
        If so, generate activity immediately to catch up.
        """
        next_activity_time_str = self.state.get("next_activity_time")

        if not next_activity_time_str:
            # No scheduled time set, calculate it now
            next_time = self.scheduler.get_next_activity_time(datetime.now(timezone.utc))
            self.state_manager.update_next_activity_time(self.job_id, next_time.isoformat())
            print(f"No scheduled time found. Next activity: {next_time.strftime('%Y-%m-%d %I:%M %p %Z')}")
            return

        next_activity_time = datetime.fromisoformat(next_activity_time_str)
        # Ensure both datetimes are timezone-aware for comparison
        if next_activity_time.tzinfo is None:
            next_activity_time = next_activity_time.replace(tzinfo=timezone.utc)
        current_time = datetime.now(timezone.utc)

        if current_time > next_activity_time:
            # We missed the scheduled time - catch up now!
            time_diff = current_time - next_activity_time
            hours_late = time_diff.total_seconds() / 3600

            print(f"⚠ Missed scheduled activity by {hours_late:.1f} hours - catching up now...")

            # Generate the missed activity
            await self._generate_activity()

            # Calculate and set next activity time
            next_time = self.scheduler.get_next_activity_time(current_time)
            self.state_manager.update_next_activity_time(self.job_id, next_time.isoformat())
            print(f"✓ Catch-up complete. Next activity: {next_time.strftime('%Y-%m-%d %I:%M %p %Z')}")
        else:
            # We're on schedule
            time_until = next_activity_time - current_time
            minutes_until = time_until.total_seconds() / 60
            print(f"✓ On schedule. Next activity in {minutes_until:.0f} minutes at {next_activity_time.strftime('%Y-%m-%d %I:%M %p %Z')}")

    async def _create_project(self) -> Optional[Dict[str, Any]]:
        """Create a new project with initial tasks using industry templates."""
        client = self.client_pool.get_random_client()
        if not client:
            print("✗ No valid clients available")
            return None

        industry = self.config.get("industry", "technology")

        # Get all available scenarios for this industry
        from continuous.industry_templates import get_all_use_cases
        all_use_cases = get_all_use_cases(industry)

        if not all_use_cases:
            # Fallback to old method if no template found
            print(f"⚠ No templates found for industry '{industry}', using legacy generation")
            return await self._create_project_legacy()

        # Get list of used scenario names
        used_scenarios = self.state.get("used_scenarios", [])

        # Filter out already-used scenarios
        available_use_cases = [uc for uc in all_use_cases if uc["name"] not in used_scenarios]

        # If all scenarios have been used, generate a NEW project via LLM instead of cycling
        if not available_use_cases:
            print(f"  ℹ All predefined scenarios exhausted - generating new project via LLM")
            return await self._create_project_llm_generated()

        # Randomly select from available scenarios
        use_case = random.choice(available_use_cases)

        # Mark this scenario as used and SAVE IT immediately
        used_scenarios.append(use_case["name"])
        self.state["used_scenarios"] = used_scenarios
        self.state_manager.save_state(self.job_id, self.state)

        # Generate unique project name from use case
        base_project_name = use_case["name"]
        project_description = use_case["description"]

        # Check if this project name already exists
        existing_project_names = [p.get("name") for p in self.state.get("projects", [])]
        project_name = base_project_name

        # If name exists, add a counter suffix to make it unique
        if project_name in existing_project_names:
            counter = 2
            while f"{base_project_name} #{counter}" in existing_project_names:
                counter += 1
            project_name = f"{base_project_name} #{counter}"

        print(f"Creating project: {project_name} (scenario: {use_case['name']})")

        try:
            # Create project in Asana
            project = client.create_project(
                workspace_gid=self.config["workspace_gid"],
                name=project_name,
                notes=project_description,
                color=random.choice(["light-green", "light-blue", "light-purple",
                                   "light-pink", "light-orange"]),
                privacy=self.config.get("privacy", "private")
            )

            project_gid = project["gid"]
            print(f"  ✓ Created project: {project_name}")

            # Add all users as members so everyone can see all projects
            try:
                users = client.get_workspace_users(self.config["workspace_gid"])
                user_gids = [user["gid"] for user in users]
                if user_gids:
                    client.add_members_to_project(project_gid, user_gids)
                    print(f"    ✓ Added {len(user_gids)} member(s) to project as admins")
                    # CRITICAL: Wait for Asana to process membership additions
                    # Without this delay, task assignments will fail because users aren't yet members
                    print(f"    → Waiting 2s for memberships to propagate in Asana...")
                    await asyncio.sleep(2)
            except Exception as e:
                print(f"    ⚠ Could not add members to project: {e}")

            # Create custom fields for this use case
            await self._setup_custom_fields(client, project_gid, use_case)

            # Create sections for this use case
            await self._setup_sections(client, project_gid, use_case)

            # Create tags for this use case
            await self._setup_tags(client, use_case)

            # Create/add to portfolio if specified
            await self._setup_portfolio(client, project_gid, use_case)

            # Save state with updated stats from object creation
            self.state_manager.save_state(self.job_id, self.state)

            # Add to state
            self.state_manager.add_project(self.job_id, project)

            # IMPORTANT: Give Asana a moment to fully create the project before adding tasks
            # This prevents "Unknown object" errors
            await asyncio.sleep(2)

            # Log activity
            self.state_manager.log_activity(self.job_id, "project_created", {
                "project_id": project_gid,
                "project_name": project_name,
                "use_case": use_case["name"],
                "user": client.user_name
            })

            # Create initial tasks for this project using DEPTH-FIRST approach
            # This means: create task → create its subtasks → add comments → move to next task
            num_tasks = random.randint(5, 12)
            sections = use_case.get("sections", [])

            tasks_created = 0
            subtasks_created = 0
            comments_created = 0

            # Track if we've created at least one of each type (for demonstration)
            has_subtask = False
            has_comment = False

            for task_idx in range(num_tasks):
                # Create the task
                task = await self._create_task(project_gid, use_case=use_case, sections=sections)
                if not task:
                    print(f"      ⚠ Task creation failed for task_idx={task_idx}, skipping...")
                    continue

                tasks_created += 1
                task_gid = task["gid"]
                print(f"      → Task {task_idx+1}/{num_tasks} created: {task_gid}")

                # CRITICAL: Give Asana time to propagate the task before adding subtasks/comments
                # Without this delay, we get "Unknown object" errors
                print(f"      → Waiting 3s for task to propagate in Asana...")
                await asyncio.sleep(3)

                # GUARANTEE: First task always gets subtasks (at least 1 of this type)
                # After that, 30% chance for other tasks
                should_add_subtasks = (task_idx == 0 and not has_subtask) or random.random() < 0.3
                print(f"      → should_add_subtasks = {should_add_subtasks} (task_idx={task_idx}, has_subtask={has_subtask})")

                if should_add_subtasks:
                    num_subtasks = random.randint(2, 4)
                    print(f"      → Attempting to create {num_subtasks} subtasks for task {task_gid}...")
                    for subtask_idx in range(num_subtasks):
                        print(f"        → Creating subtask {subtask_idx+1}/{num_subtasks}...")
                        subtask = await self._create_subtask(task_gid, project_gid)
                        if subtask:
                            subtasks_created += 1
                            has_subtask = True
                            print(f"        ✓ Subtask created successfully (total: {subtasks_created})")
                        else:
                            print(f"        ✗ Subtask creation returned None")
                        await asyncio.sleep(0.5)
                else:
                    print(f"      → Skipping subtasks for task {task_idx+1}")

                # GUARANTEE: First or second task always gets comments (at least 1 of this type)
                # After that, 40% chance for other tasks
                should_add_comments = (task_idx <= 1 and not has_comment) or random.random() < 0.4

                if should_add_comments:
                    num_comments = random.randint(1, 2)
                    for _ in range(num_comments):
                        comment_added = await self._add_initial_comment(task_gid, task.get("name", "Task"))
                        if comment_added:
                            comments_created += 1
                            has_comment = True
                        await asyncio.sleep(0.5)

                # Note: No additional delay needed here since we already waited 2s after task creation

            # Reload state
            self.state = self.state_manager.load_state(self.job_id)

            print(f"  ✓ Project setup complete: {tasks_created} tasks, {subtasks_created} subtasks, {comments_created} comments")

            return project

        except Exception as e:
            print(f"✗ Error creating project: {e}")
            self.state_manager.log_error(self.job_id, "project_creation", str(e))
            return None

    async def _create_project_legacy(self) -> Optional[Dict[str, Any]]:
        """Legacy project creation method (fallback)."""
        client = self.client_pool.get_random_client()
        if not client:
            return None

        industry = self.config.get("industry", "technology")

        # Generate project name and description
        project_name = self.llm.generate_project_name(industry)
        project_description = self.llm.generate_project_description(industry, project_name)

        try:
            # Create project in Asana
            project = client.create_project(
                workspace_gid=self.config["workspace_gid"],
                name=project_name,
                notes=project_description,
                color=random.choice(["light-green", "light-blue", "light-purple",
                                   "light-pink", "light-orange"]),
                privacy=self.config.get("privacy", "private")
            )

            # Add to state
            self.state_manager.add_project(self.job_id, project)

            # Log activity
            self.state_manager.log_activity(self.job_id, "project_created", {
                "project_id": project["gid"],
                "project_name": project_name,
                "user": client.user_name
            })

            print(f"✓ Created project: {project_name}")

            # Create initial tasks for this project
            num_tasks = random.randint(5, 12)
            for _ in range(num_tasks):
                await self._create_task(project["gid"])
                await asyncio.sleep(1)

            # Reload state
            self.state = self.state_manager.load_state(self.job_id)

            return project

        except Exception as e:
            print(f"✗ Error creating project: {e}")
            self.state_manager.log_error(self.job_id, "project_creation", str(e))
            return None

    async def _create_project_llm_generated(self) -> Optional[Dict[str, Any]]:
        """
        Generate a NEW unique project via LLM when all predefined scenarios are exhausted.
        This ensures continuous mode can generate unlimited unique content.
        """
        client = self.client_pool.get_random_client()
        if not client:
            return None

        industry = self.config.get("industry", "technology")

        # Get existing project names to avoid duplicates
        existing_project_names = [p.get("name") for p in self.state.get("projects", [])]

        # Generate a new, unique project name via LLM
        max_attempts = 5
        project_name = None
        project_description = None

        for attempt in range(max_attempts):
            # Generate project name
            generated_name = self.llm.generate_project_name(industry)

            # Check if it's unique
            if generated_name not in existing_project_names:
                project_name = generated_name
                project_description = self.llm.generate_project_description(industry, project_name)
                break
            else:
                print(f"    ⚠ Generated duplicate name '{generated_name}', retrying... ({attempt + 1}/{max_attempts})")

        # If we couldn't generate a unique name after max attempts, add a suffix
        if not project_name:
            base_name = self.llm.generate_project_name(industry)
            counter = 2
            while f"{base_name} #{counter}" in existing_project_names:
                counter += 1
            project_name = f"{base_name} #{counter}"
            project_description = self.llm.generate_project_description(industry, project_name)

        print(f"Creating LLM-generated project: {project_name}")

        try:
            # Create project in Asana
            project = client.create_project(
                workspace_gid=self.config["workspace_gid"],
                name=project_name,
                notes=project_description,
                color=random.choice(["light-green", "light-blue", "light-purple",
                                   "light-pink", "light-orange"]),
                privacy=self.config.get("privacy", "private")
            )

            # Add to state
            self.state_manager.add_project(self.job_id, project)

            # Log activity
            self.state_manager.log_activity(self.job_id, "project_created", {
                "project_id": project["gid"],
                "project_name": project_name,
                "user": client.user_name,
                "generation_method": "llm_generated"
            })

            print(f"  ✓ Created LLM-generated project: {project_name}")

            # Create initial tasks for this project
            num_tasks = random.randint(5, 12)
            for _ in range(num_tasks):
                await self._create_task(project["gid"])
                await asyncio.sleep(1)

            # Reload state
            self.state = self.state_manager.load_state(self.job_id)

            return project

        except Exception as e:
            print(f"✗ Error creating LLM-generated project: {e}")
            self.state_manager.log_error(self.job_id, "project_creation_llm", str(e))
            return None

    async def _setup_custom_fields(self, client: AsanaClient, project_gid: str,
                                   use_case: Dict[str, Any]):
        """Create and attach custom fields to a project."""
        custom_field_defs = use_case.get("custom_fields", [])
        if not custom_field_defs:
            return

        workspace_gid = self.config["workspace_gid"]

        for field_def in custom_field_defs:
            field_name = field_def["name"]
            field_type = field_def["type"]

            try:
                # Check if we already created this field
                if field_name in self.workspace_custom_fields:
                    field_gid = self.workspace_custom_fields[field_name]
                    print(f"    ↳ Using existing custom field: {field_name}")
                else:
                    # Create the custom field
                    kwargs = {}
                    if "precision" in field_def:
                        kwargs["precision"] = field_def["precision"]
                    # Templates use "options" key, convert to "enum_options" for API
                    if "options" in field_def:
                        kwargs["enum_options"] = [{"name": opt} for opt in field_def["options"]]

                    field = client.create_custom_field(
                        workspace_gid=workspace_gid,
                        name=field_name,
                        field_type=field_type,
                        description=field_def.get("description", ""),
                        **kwargs
                    )
                    field_gid = field["gid"]
                    self.workspace_custom_fields[field_name] = field_gid
                    self.state["stats"]["custom_fields_created"] += 1
                    print(f"    ✓ Created custom field: {field_name} ({field_type})")

                # Add field to project
                client.add_custom_field_to_project(project_gid, field_gid)

            except Exception as e:
                # Graceful failure - log but continue
                print(f"    ⚠ Could not create custom field '{field_name}': {e}")
                self.state_manager.log_activity(self.job_id, "custom_field_failed", {
                    "field_name": field_name,
                    "project_id": project_gid,
                    "error": str(e)
                })

    async def _setup_sections(self, client: AsanaClient, project_gid: str,
                             use_case: Dict[str, Any]):
        """Create sections in a project."""
        section_names = use_case.get("sections", [])
        if not section_names:
            return

        for section_name in section_names:
            try:
                section = client.create_section(project_gid, section_name)
                self.state["stats"]["sections_created"] += 1
                print(f"    ✓ Created section: {section_name}")
            except Exception as e:
                # Graceful failure
                print(f"    ⚠ Could not create section '{section_name}': {e}")
                self.state_manager.log_activity(self.job_id, "section_failed", {
                    "section_name": section_name,
                    "project_id": project_gid,
                    "error": str(e)
                })

    async def _setup_tags(self, client: AsanaClient, use_case: Dict[str, Any]):
        """Create workspace-level tags for a use case."""
        tag_names = use_case.get("tags", [])
        if not tag_names:
            return

        workspace_gid = self.config["workspace_gid"]

        for tag_name in tag_names:
            try:
                # Check if we already created this tag
                if tag_name in self.workspace_tags:
                    print(f"    ↳ Tag already exists: {tag_name}")
                    continue

                # Create the tag
                tag = client.create_tag(
                    workspace_gid=workspace_gid,
                    name=tag_name,
                    color=random.choice(["dark-pink", "dark-purple", "dark-blue",
                                       "dark-teal", "dark-green", "dark-orange", "dark-red"])
                )
                self.workspace_tags[tag_name] = tag["gid"]
                self.state["stats"]["tags_created"] += 1
                print(f"    ✓ Created tag: {tag_name}")

            except Exception as e:
                # Graceful failure
                print(f"    ⚠ Could not create tag '{tag_name}': {e}")
                self.state_manager.log_activity(self.job_id, "tag_failed", {
                    "tag_name": tag_name,
                    "error": str(e)
                })

    async def _setup_portfolio(self, client: AsanaClient, project_gid: str,
                              use_case: Dict[str, Any]):
        """Create/add project to a portfolio if specified."""
        if not use_case.get("portfolios"):
            return

        portfolio_name = use_case.get("portfolio_name", f"{use_case['name']} Portfolio")
        workspace_gid = self.config["workspace_gid"]

        try:
            # Check if we already created this portfolio
            if portfolio_name in self.workspace_portfolios:
                portfolio_gid = self.workspace_portfolios[portfolio_name]
                print(f"    ↳ Using existing portfolio: {portfolio_name}")
            else:
                # Create the portfolio
                portfolio = client.create_portfolio(
                    workspace_gid=workspace_gid,
                    name=portfolio_name,
                    color=random.choice(["light-green", "light-blue", "light-purple"]),
                    public=False
                )
                portfolio_gid = portfolio["gid"]
                self.workspace_portfolios[portfolio_name] = portfolio_gid
                self.state["stats"]["portfolios_created"] += 1
                print(f"    ✓ Created portfolio: {portfolio_name}")

            # Add project to portfolio
            client.add_project_to_portfolio(portfolio_gid, project_gid)
            print(f"    ✓ Added project to portfolio: {portfolio_name}")

        except Exception as e:
            # Graceful failure
            print(f"    ⚠ Could not create/add to portfolio '{portfolio_name}': {e}")
            self.state_manager.log_activity(self.job_id, "portfolio_failed", {
                "portfolio_name": portfolio_name,
                "project_id": project_gid,
                "error": str(e)
            })

    async def _set_task_custom_field_values(self, client: AsanaClient, task_gid: str,
                                            use_case: Dict[str, Any]):
        """Set realistic custom field values on a task based on use case."""
        custom_field_defs = use_case.get("custom_fields", [])
        if not custom_field_defs:
            return

        for field_def in custom_field_defs:
            field_name = field_def["name"]
            field_type = field_def["type"]

            # Skip if field wasn't created
            if field_name not in self.workspace_custom_fields:
                continue

            field_gid = self.workspace_custom_fields[field_name]

            try:
                # Generate realistic value based on field type
                value = None

                if field_type == "text":
                    # Generate realistic text values
                    if "email" in field_name.lower():
                        value = f"user{random.randint(100, 999)}@example.com"
                    elif "phone" in field_name.lower():
                        value = f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
                    elif "number" in field_name.lower() or "store" in field_name.lower():
                        value = f"{random.randint(1000, 9999)}"
                    else:
                        value = f"Value-{random.randint(1, 100)}"

                elif field_type == "number":
                    # Generate realistic numbers based on field name context
                    if "budget" in field_name.lower() or "cost" in field_name.lower() or "revenue" in field_name.lower():
                        value = random.randint(10000, 500000)
                    elif "percent" in field_name.lower() or "rate" in field_name.lower():
                        value = random.randint(1, 100)
                    elif "footage" in field_name.lower() or "capacity" in field_name.lower():
                        value = random.randint(1000, 50000)
                    else:
                        value = random.randint(1, 1000)

                elif field_type == "enum":
                    # Pick a random option from the enum
                    options = field_def.get("options", [])
                    if options:
                        # Get the full custom field data to get enum_options with GIDs
                        workspace_fields = client.get_workspace_custom_fields(self.config["workspace_gid"])
                        for wf in workspace_fields:
                            if wf["gid"] == field_gid:
                                enum_options = wf.get("enum_options", [])
                                if enum_options:
                                    selected_option = random.choice(enum_options)
                                    value = selected_option["gid"]
                                break

                elif field_type == "multi_enum":
                    # Pick 1-3 random options from the multi_enum
                    options = field_def.get("options", [])
                    if options:
                        # Get the full custom field data to get enum_options with GIDs
                        workspace_fields = client.get_workspace_custom_fields(self.config["workspace_gid"])
                        for wf in workspace_fields:
                            if wf["gid"] == field_gid:
                                enum_options = wf.get("enum_options", [])
                                if enum_options:
                                    num_selections = random.randint(1, min(3, len(enum_options)))
                                    selected_options = random.sample(enum_options, num_selections)
                                    value = [opt["gid"] for opt in selected_options]
                                break

                elif field_type == "date":
                    # Generate a date within the next 90 days
                    days_offset = random.randint(1, 90)
                    value = (datetime.now(timezone.utc) + timedelta(days=days_offset)).strftime('%Y-%m-%d')

                # Set the custom field value
                if value is not None:
                    client.create_custom_field_value(task_gid, field_gid, value)

            except Exception as e:
                # Graceful failure - some fields might not be settable
                print(f"    ⚠ Could not set custom field '{field_name}': {e}")

    async def _create_task(self, project_id: str, use_case: Optional[Dict[str, Any]] = None,
                          sections: Optional[List[str]] = None, task_index: int = 0) -> Optional[Dict[str, Any]]:
        """Create a new task in a project with realistic attributes."""
        client = self.client_pool.get_random_client()
        if not client:
            return None

        industry = self.config.get("industry", "technology")

        # Find project name, creation date, and count existing tasks for serialized dates
        project_name = "Unknown Project"
        project_created_at = datetime.now(timezone.utc)
        existing_tasks_count = 0
        for proj in self.state.get("projects", []):
            if proj["id"] == project_id:
                project_name = proj["name"]
                # Get project creation time from state
                created_str = proj.get("created_at")
                if created_str:
                    project_created_at = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                # Count existing tasks for serialization
                existing_tasks_count = len(proj.get("tasks", []))
                break

        # Generate task name and description
        task_name = self.llm.generate_task_name(industry, project_name)

        try:
            # Randomly assign to a user
            assignee = random.choice(self.client_pool.get_valid_user_names())
            assignee_client = self.client_pool.get_client(assignee)

            # CRITICAL FIX: Get assignee GID from cached mapping (initialized during client pool setup)
            # This is more reliable than searching workspace users by name matching
            assignee_gid = self.client_pool.get_user_gid(assignee)

            # SERIALIZED DATES: Each task starts after the previous one for timeline view
            # Generate realistic date range with varying durations
            # Short tasks: 1-7 days, Medium tasks: 7-21 days, Long tasks: 21-60 days
            task_length_category = random.choices(
                ["short", "medium", "long"],
                weights=[0.5, 0.35, 0.15]  # 50% short, 35% medium, 15% long
            )[0]

            if task_length_category == "short":
                task_duration = random.randint(1, 7)
            elif task_length_category == "medium":
                task_duration = random.randint(7, 21)
            else:  # long
                task_duration = random.randint(21, 60)

            # IMPROVED: Serialize task dates so they span out over time in timeline view
            # First task starts 0-2 days from project creation
            # Each subsequent task starts 1-3 days after the previous task's start
            if existing_tasks_count == 0:
                days_until_start = random.randint(0, 2)
            else:
                # Tasks are serialized: each starts 1-3 days after the previous
                days_until_start = random.randint(0, 2) + (existing_tasks_count * random.randint(1, 3))

            start_date = (project_created_at + timedelta(days=days_until_start)).strftime('%Y-%m-%d')

            # Due date: start_date + task_duration
            due_date = (project_created_at + timedelta(days=days_until_start + task_duration)).strftime('%Y-%m-%d')

            # ATOMIC CREATION: Create task with ALL attributes from the start
            # This is more mature than create-then-update pattern which has race conditions
            print(f"    → Creating task in project {project_id} for {assignee} (GID: {assignee_gid})")

            # Create task with assignee directly (atomic operation)
            task = client.create_task(
                project_gid=project_id,
                name=task_name,
                notes=self.llm.generate_task_description(industry, project_name, task_name),
                assignee=assignee_gid,  # Pass assignee during creation (atomic)
                due_date=due_date,
                start_date=start_date
            )

            task_gid = task["gid"]

            if assignee_gid:
                print(f"    ✓ Task created and assigned to {assignee}: {task_name[:40]}...")
            else:
                print(f"    ⚠ Could not find Asana user for {assignee}, task created unassigned")

            # Add task to a section if sections are available
            if sections:
                try:
                    # Get project sections
                    project_sections = client.get_project_sections(project_id)
                    if project_sections:
                        # Pick a random section from the use case sections
                        target_section_name = random.choice(sections)
                        # Find matching section GID
                        for section in project_sections:
                            if section["name"] == target_section_name:
                                client.add_task_to_section(task_gid, section["gid"])
                                break
                except Exception as e:
                    print(f"    ⚠ Could not add task to section: {e}")

            # Add tags to task if available
            if use_case:
                tag_names = use_case.get("tags", [])
                if tag_names and random.random() < 0.6:  # 60% chance to add tags
                    try:
                        # Pick 1-3 random tags
                        num_tags = random.randint(1, min(3, len(tag_names)))
                        selected_tags = random.sample(tag_names, num_tags)

                        for tag_name in selected_tags:
                            if tag_name in self.workspace_tags:
                                tag_gid = self.workspace_tags[tag_name]
                                client.add_tag_to_task(task_gid, tag_gid)
                    except Exception as e:
                        print(f"    ⚠ Could not add tags to task: {e}")

            # Set custom field values if available
            if use_case and use_case.get("custom_fields"):
                await self._set_task_custom_field_values(client, task_gid, use_case)

            # Add to state
            self.state_manager.add_task(self.job_id, project_id, task)

            # Log activity
            self.state_manager.log_activity(self.job_id, "task_created", {
                "task_id": task_gid,
                "task_name": task_name,
                "project_id": project_id,
                "assignee": assignee,
                "user": client.user_name
            })

            # Track API usage
            self.state_manager.increment_api_usage(self.job_id, "asana", 1)

            # Reload state
            self.state = self.state_manager.load_state(self.job_id)

            return task

        except Exception as e:
            print(f"✗ Error creating task: {e}")
            self.state_manager.log_error(self.job_id, "task_creation", str(e))
            return None

    async def _create_subtask(self, parent_task_id: str, project_id: str) -> Optional[Dict[str, Any]]:
        """Create a subtask under a parent task."""
        client = self.client_pool.get_random_client()
        if not client:
            return None

        industry = self.config.get("industry", "technology")

        # Generate subtask name
        subtask_name = self.llm.generate_task_name(industry, "subtask")

        try:
            # IMPROVED: Randomly assign to a user (should distribute across all users)
            assignee = random.choice(self.client_pool.get_valid_user_names())

            # CRITICAL FIX: Get assignee GID from cached mapping (initialized during client pool setup)
            # This is more reliable than searching workspace users by name matching
            assignee_gid = self.client_pool.get_user_gid(assignee)

            # Create subtask using the proper API endpoint
            # IMPROVED: If assignee lookup fails, still create subtask unassigned
            subtask = client.create_subtask(
                parent_task_gid=parent_task_id,
                name=subtask_name,
                notes="",
                assignee=assignee_gid
            )

            if assignee_gid:
                print(f"      ✓ Created subtask assigned to {assignee}: {subtask_name[:35]}...")
            else:
                print(f"      ✓ Created subtask (unassigned): {subtask_name[:35]}...")
                print(f"        ⚠ Could not find Asana user for {assignee}")

            # Track in state
            self.state_manager.increment_api_usage(self.job_id, "asana", 1)

            return subtask

        except Exception as e:
            print(f"      ⚠ Error creating subtask: {e}")
            self.state_manager.log_error(self.job_id, "subtask_creation", str(e))
            return None

    async def _add_initial_comment(self, task_gid: str, task_name: str) -> bool:
        """
        Add an initial comment to a task during bootstrap.
        MATURE APPROACH: Uses LLM with task context to generate realistic, unique comments.
        Queries existing comments first, then generates contextual responses.
        """
        client = self.client_pool.get_random_client()
        if not client:
            return False

        try:
            # Get all users for potential conversation
            all_users = self.client_pool.get_valid_user_names()
            if not all_users:
                return False

            # CRITICAL: Query existing comments from activity log for context
            existing_comments = []
            for activity in reversed(self.state.get("activity_log", [])):
                if (activity.get("action") == "comment_added" and
                    activity.get("details", {}).get("task_id") == task_gid):
                    existing_comments.append({
                        "user": activity["details"].get("user"),
                        "comment": activity["details"].get("comment"),
                        "type": activity["details"].get("type")
                    })

            # Select commenter (prefer different user from last commenter for variety)
            if existing_comments:
                last_commenter = existing_comments[0].get("user")
                # 70% chance to pick a different user for conversation
                if random.random() < 0.7:
                    available_users = [u for u in all_users if u != last_commenter]
                    commenter = random.choice(available_users) if available_users else random.choice(all_users)
                else:
                    commenter = last_commenter  # Same user adds progress update
            else:
                commenter = random.choice(all_users)

            commenter_client = self.client_pool.get_client(commenter)
            if not commenter_client:
                return False

            # Find project name for context
            project_name = "Unknown Project"
            industry = self.config.get("industry", "technology")
            for proj in self.state.get("projects", []):
                for task in proj.get("tasks", []):
                    if task.get("id") == task_gid:
                        project_name = proj.get("name", "Unknown Project")
                        break

            # MATURE APPROACH: Generate contextual comment using LLM
            comment_text = self.llm.generate_contextual_initial_comment(
                user_name=commenter,
                task_name=task_name,
                project_name=project_name,
                industry=industry,
                existing_comments=existing_comments
            )

            # Determine comment type
            if not existing_comments:
                comment_type = "initial"
            elif existing_comments and existing_comments[0].get("user") == commenter:
                comment_type = "progress_self"
            else:
                comment_type = "conversation_response"

            # Add comment to Asana
            commenter_client.add_comment(task_gid, comment_text)

            # Update state
            self.state_manager.add_comment(self.job_id, task_gid, {"text": comment_text})
            self.state_manager.log_activity(self.job_id, "comment_added", {
                "task_id": task_gid,
                "task_name": task_name,
                "user": commenter,
                "comment": comment_text,
                "type": comment_type
            })

            # Track API usage (Asana + LLM)
            self.state_manager.increment_api_usage(self.job_id, "asana", 1)
            llm_stats = self.llm.get_usage_stats()
            self.state_manager.increment_api_usage(self.job_id, "llm", 1, llm_stats["total_tokens"])

            if comment_type == "initial":
                print(f"      ✓ Added LLM-generated initial comment by {commenter}")
            elif comment_type == "progress_self":
                print(f"      ✓ Added LLM-generated progress update by {commenter}")
            else:
                last_commenter = existing_comments[0].get("user") if existing_comments else "someone"
                print(f"      ✓ Added LLM-generated response by {commenter} → {last_commenter}")

            return True

        except Exception as e:
            print(f"      ⚠ Error adding comment: {e}")
            self.state_manager.log_error(self.job_id, "comment_creation", str(e))
            return False

    async def _generate_activity(self):
        """Generate a single activity based on current state."""
        # Check if we should create a new project
        if self.scheduler.should_create_new_project(self.state):
            await self._create_project()
            return

        # Select activity type
        activity_type = self.scheduler.select_activity_type(self.state)

        # Execute activity
        if activity_type == ActivityType.CREATE_TASK:
            # Pick a random project
            if self.state.get("projects"):
                project = random.choice(self.state["projects"])
                await self._create_task(project["id"])

        elif activity_type == ActivityType.COMMENT_START_WORK:
            await self._handle_start_work()

        elif activity_type == ActivityType.COMMENT_PROGRESS:
            await self._handle_progress_update()

        elif activity_type == ActivityType.COMMENT_BLOCKED:
            await self._handle_block_task()

        elif activity_type == ActivityType.COMMENT_UNBLOCKED:
            await self._handle_unblock_task()

        elif activity_type == ActivityType.COMPLETE_TASK:
            await self._handle_complete_task()

        elif activity_type == ActivityType.COMMENT_CONVERSATION:
            await self._handle_conversation()

        elif activity_type == ActivityType.COMMENT_OOO:
            await self._handle_ooo_comment()

        elif activity_type == ActivityType.TASK_REASSIGNMENT:
            await self._handle_task_reassignment()

        # Update timestamp
        self.state_manager.update_last_activity(self.job_id)

    async def _handle_start_work(self):
        """Handle starting work on a task."""
        task = self.scheduler.select_task_for_activity(self.state,
                                                       ActivityType.COMMENT_START_WORK)
        if not task:
            return

        assignee = task.get("assignee_name", "Unknown")
        client = self.client_pool.get_client(assignee)
        if not client:
            return

        # Generate comment with time context
        current_time = datetime.now(timezone.utc)
        comment_text = self.llm.generate_comment_starting_work(assignee, task["name"], current_time)

        try:
            # Add comment to Asana
            client.add_comment(task["id"], comment_text)

            # Update task status to in_progress
            client.update_task(task["id"], {"completed": False})

            # Update state
            self.state_manager.update_task_status(self.job_id, task["id"], "in_progress")
            self.state_manager.add_comment(self.job_id, task["id"], {"text": comment_text})

            # Log activity
            self.state_manager.log_activity(self.job_id, "comment_added", {
                "task_id": task["id"],
                "task_name": task["name"],
                "user": assignee,
                "comment": comment_text,
                "type": "start_work"
            })

            # Track API usage
            self.state_manager.increment_api_usage(self.job_id, "asana", 2)
            llm_stats = self.llm.get_usage_stats()
            self.state_manager.increment_api_usage(self.job_id, "llm", 1,
                                                   llm_stats["total_tokens"])

            print(f"  {assignee} started work on: {task['name'][:50]}...")

        except Exception as e:
            print(f"✗ Error in start_work: {e}")
            self.state_manager.log_error(self.job_id, "start_work", str(e))

    async def _handle_progress_update(self):
        """Handle progress update on a task."""
        task = self.scheduler.select_task_for_activity(self.state,
                                                       ActivityType.COMMENT_PROGRESS)
        if not task:
            return

        assignee = task.get("assignee_name", "Unknown")
        client = self.client_pool.get_client(assignee)
        if not client:
            return

        industry = self.config.get("industry", "technology")
        current_time = datetime.now(timezone.utc)
        comment_text = self.llm.generate_comment_progress_update(assignee, task["name"],
                                                                 industry, current_time)

        try:
            client.add_comment(task["id"], comment_text)

            self.state_manager.add_comment(self.job_id, task["id"], {"text": comment_text})
            self.state_manager.log_activity(self.job_id, "comment_added", {
                "task_id": task["id"],
                "task_name": task.get("name", "Unknown task"),
                "user": assignee,
                "type": "progress"
            })

            self.state_manager.increment_api_usage(self.job_id, "asana", 1)

            print(f"  {assignee} posted progress on: {task['name'][:50]}...")

        except Exception as e:
            print(f"✗ Error in progress_update: {e}")

    async def _handle_block_task(self):
        """Handle blocking a task."""
        task = self.scheduler.select_task_for_activity(self.state,
                                                       ActivityType.COMMENT_BLOCKED)
        if not task or not self.scheduler.should_task_be_blocked(task):
            return

        assignee = task.get("assignee_name", "Unknown")
        client = self.client_pool.get_client(assignee)
        if not client:
            return

        industry = self.config.get("industry", "technology")
        comment_text = self.llm.generate_comment_blocked(assignee, task["name"], industry)

        try:
            client.add_comment(task["id"], comment_text)

            self.state_manager.update_task_status(self.job_id, task["id"], "blocked",
                                                  {"blocker_reason": comment_text})
            self.state_manager.add_comment(self.job_id, task["id"], {"text": comment_text})
            self.state_manager.log_activity(self.job_id, "task_blocked", {
                "task_id": task["id"],
                "task_name": task.get("name", "Unknown task"),
                "user": assignee,
                "reason": comment_text
            })

            self.state_manager.increment_api_usage(self.job_id, "asana", 1)

            print(f"  {assignee} blocked task: {task['name'][:50]}...")

        except Exception as e:
            print(f"✗ Error in block_task: {e}")

    async def _handle_unblock_task(self):
        """Handle unblocking a task."""
        task = self.scheduler.select_task_for_activity(self.state,
                                                       ActivityType.COMMENT_UNBLOCKED)
        if not task or not self.scheduler.should_task_be_unblocked(task):
            return

        assignee = task.get("assignee_name", "Unknown")
        client = self.client_pool.get_client(assignee)
        if not client:
            return

        blocker_reason = task.get("blocker_reason")
        comment_text = self.llm.generate_comment_unblocked(assignee, blocker_reason)

        try:
            client.add_comment(task["id"], comment_text)

            self.state_manager.update_task_status(self.job_id, task["id"], "in_progress")
            self.state_manager.add_comment(self.job_id, task["id"], {"text": comment_text})
            self.state_manager.log_activity(self.job_id, "task_unblocked", {
                "task_id": task["id"],
                "task_name": task.get("name", "Unknown task"),
                "user": assignee
            })

            self.state_manager.increment_api_usage(self.job_id, "asana", 1)

            print(f"  {assignee} unblocked task: {task['name'][:50]}...")

        except Exception as e:
            print(f"✗ Error in unblock_task: {e}")

    async def _handle_complete_task(self):
        """Handle completing a task."""
        task = self.scheduler.select_task_for_activity(self.state,
                                                       ActivityType.COMPLETE_TASK)
        if not task:
            return

        assignee = task.get("assignee_name", "Unknown")
        client = self.client_pool.get_client(assignee)
        if not client:
            return

        industry = self.config.get("industry", "technology")
        current_time = datetime.now(timezone.utc)
        comment_text = self.llm.generate_comment_completed(assignee, task["name"], industry, current_time)

        try:
            # Add comment
            client.add_comment(task["id"], comment_text)

            # Complete task
            client.complete_task(task["id"])

            self.state_manager.update_task_status(self.job_id, task["id"], "completed")
            self.state_manager.add_comment(self.job_id, task["id"], {"text": comment_text})
            self.state_manager.log_activity(self.job_id, "task_completed", {
                "task_id": task["id"],
                "task_name": task.get("name", "Unknown task"),
                "user": assignee
            })

            self.state_manager.increment_api_usage(self.job_id, "asana", 2)

            print(f"  ✓ {assignee} completed: {task['name'][:50]}...")

        except Exception as e:
            print(f"✗ Error in complete_task: {e}")

    async def _handle_conversation(self):
        """Handle conversational comment."""
        # Pick any task with comments
        all_tasks = []
        for project in self.state.get("projects", []):
            for task in project.get("tasks", []):
                if task.get("comment_count", 0) > 0:
                    all_tasks.append(task)

        if not all_tasks:
            return

        task = random.choice(all_tasks)

        # Pick two different users
        users = self.client_pool.get_valid_user_names()
        if len(users) < 2:
            return

        user1, user2 = random.sample(users, 2)
        client = self.client_pool.get_client(user2)
        if not client:
            return

        # Generate conversational comment
        comment_text = self.llm.generate_comment_conversation(
            user2, user1, "earlier comment", task["name"]
        )

        try:
            client.add_comment(task["id"], comment_text)

            self.state_manager.add_comment(self.job_id, task["id"], {"text": comment_text})
            self.state_manager.log_activity(self.job_id, "comment_added", {
                "task_id": task["id"],
                "task_name": task.get("name", "Unknown task"),
                "user": user2,
                "type": "conversation"
            })

            self.state_manager.increment_api_usage(self.job_id, "asana", 1)

            print(f"  {user2} replied on: {task['name'][:50]}...")

        except Exception as e:
            print(f"✗ Error in conversation: {e}")

    async def _handle_ooo_comment(self):
        """Handle out-of-office comment."""
        user = random.choice(self.client_pool.get_valid_user_names())
        client = self.client_pool.get_client(user)
        if not client:
            return

        # Pick a task assigned to this user
        user_tasks = []
        for project in self.state.get("projects", []):
            for task in project.get("tasks", []):
                if task.get("assignee_name") == user:
                    user_tasks.append(task)

        if not user_tasks:
            return

        task = random.choice(user_tasks)

        reason = random.choice(["sick", "pto", "busy"])
        comment_text = self.llm.generate_comment_out_of_office(user, reason)

        try:
            client.add_comment(task["id"], comment_text)

            self.state_manager.add_comment(self.job_id, task["id"], {"text": comment_text})
            self.state_manager.log_activity(self.job_id, "comment_added", {
                "task_id": task["id"],
                "task_name": task.get("name", "Unknown task"),
                "user": user,
                "type": "ooo"
            })

            print(f"  {user} posted OOO message")

        except Exception as e:
            print(f"✗ Error in ooo_comment: {e}")

    async def _handle_task_reassignment(self):
        """Handle reassigning a task."""
        # Implementation similar to above
        pass

    async def _handle_rate_limit_pause(self):
        """Handle rate limit by generating realistic pause comments."""
        print("  Generating realistic pause due to rate limits...")
        # Users would post OOO messages
        for user in self.client_pool.get_valid_user_names():
            if random.random() < 0.3:  # 30% of users post OOO
                await self._handle_ooo_comment()

    async def cleanup_asana_data(self, progress_callback=None):
        """
        Delete all Asana data created by this job.
        Deletes tasks, subtasks, projects, and workspace-level objects in proper order.

        Deletion order:
        1. Subtasks (children of tasks)
        2. Tasks (children of projects)
        3. Projects (containers)
        4. Portfolios (workspace-level, contain projects)
        5. Custom Fields (workspace-level, attached to projects)
        6. Tags (workspace-level, attached to tasks)

        Args:
            progress_callback: Optional callback function(current, total, message)

        Returns:
            Dict with cleanup results
        """
        print(f"\n{'='*60}")
        print(f"Starting cleanup for job {self.job_id}")
        print(f"{'='*60}\n")

        # Reload state to ensure we have latest data
        self.state = self.state_manager.load_state(self.job_id)

        projects = self.state.get("projects", [])
        total_projects = len(projects)
        deleted_projects = 0
        deleted_tasks = 0
        deleted_subtasks = 0
        deleted_portfolios = 0
        deleted_custom_fields = 0
        deleted_tags = 0
        failed_projects = []

        if total_projects == 0:
            print("No projects to delete")
            return {
                "success": True,
                "deleted_projects": 0,
                "deleted_tasks": 0,
                "deleted_subtasks": 0,
                "deleted_portfolios": 0,
                "deleted_custom_fields": 0,
                "deleted_tags": 0,
                "failed_projects": []
            }

        print(f"Found {total_projects} project(s) to delete")

        # Get all available clients - we'll try each one for deletions that fail with permission errors
        all_clients = self.client_pool.get_valid_clients()
        if not all_clients:
            print(f"✗ No valid clients available for deletion")
            return {
                "success": False,
                "deleted_projects": 0,
                "deleted_tasks": 0,
                "deleted_subtasks": 0,
                "deleted_portfolios": 0,
                "deleted_custom_fields": 0,
                "deleted_tags": 0,
                "failed_projects": [{
                    "id": "all",
                    "name": "All projects",
                    "error": "No valid clients available"
                }]
            }

        # Helper function to try deletion with each client until one succeeds
        def try_delete_with_clients(delete_func, item_description: str) -> bool:
            """Try deletion with each available client until one succeeds."""
            for client in all_clients:
                try:
                    delete_func(client)
                    return True
                except Exception as e:
                    error_str = str(e)
                    # If it's a permission error (403), try next client
                    if "403" in error_str or "permission" in error_str.lower() or "Forbidden" in error_str:
                        continue
                    else:
                        # For non-permission errors, raise immediately
                        raise e
            # If we tried all clients and all failed with permission errors
            return False

        # Delete each project's tasks, then the project itself
        for idx, project in enumerate(projects):
            project_id = project.get("id")
            project_name = project.get("name", "Unknown Project")

            try:
                print(f"  [{idx+1}/{total_projects}] Processing project: {project_name}")

                if progress_callback:
                    progress_callback(idx + 1, total_projects,
                                    f"Processing project: {project_name}")

                # Get all tasks in this project (use first client for reading)
                client = all_clients[0]
                try:
                    tasks = client.get_project_tasks(project_id)
                    print(f"    Found {len(tasks)} task(s) to delete")

                    # Delete each task (and its subtasks)
                    for task in tasks:
                        task_id = task.get("gid")
                        task_name = task.get("name", "Unknown Task")

                        try:
                            # Get and delete subtasks first
                            subtasks = client.get_task_subtasks(task_id)
                            for subtask in subtasks:
                                subtask_id = subtask.get("gid")
                                try:
                                    # Try deletion with each client until one succeeds
                                    success = try_delete_with_clients(
                                        lambda c: c.delete_task(subtask_id),
                                        f"subtask {subtask_id}"
                                    )
                                    if success:
                                        deleted_subtasks += 1
                                        await asyncio.sleep(0.2)  # Small delay
                                    else:
                                        print(f"      ⚠ No client has permission to delete subtask {subtask_id}")
                                except Exception as e:
                                    print(f"      ⚠ Error deleting subtask {subtask_id}: {e}")

                            # Delete the parent task
                            success = try_delete_with_clients(
                                lambda c: c.delete_task(task_id),
                                f"task {task_id}"
                            )
                            if success:
                                deleted_tasks += 1
                                await asyncio.sleep(0.2)  # Small delay
                            else:
                                print(f"      ⚠ No client has permission to delete task {task_name}")

                        except Exception as e:
                            print(f"      ⚠ Error deleting task {task_name}: {e}")

                except Exception as e:
                    print(f"    ⚠ Error fetching tasks for project: {e}")

                # Finally, delete the project - try with each client
                success = try_delete_with_clients(
                    lambda c: c.delete_project(project_id),
                    f"project {project_id}"
                )
                if success:
                    deleted_projects += 1
                    print(f"    ✓ Deleted project: {project_name}")
                else:
                    raise Exception(f"No client has permission to delete project {project_name}")

                # Delay between projects to avoid rate limits
                await asyncio.sleep(0.5)

            except Exception as e:
                print(f"    ✗ Error deleting project {project_name}: {e}")
                failed_projects.append({
                    "id": project_id,
                    "name": project_name,
                    "error": str(e)
                })

        # Step 4: Delete portfolios (workspace-level)
        # Query Asana directly for all portfolios in workspace (don't rely on in-memory cache)
        print(f"\n  Deleting portfolios...")
        try:
            workspace_gid = self.config.get("workspace_gid")
            client = all_clients[0]  # Use first client for reading
            portfolios = client.get_workspace_portfolios(workspace_gid)
            print(f"    Found {len(portfolios)} portfolio(s) in workspace")

            for portfolio in portfolios:
                portfolio_gid = portfolio.get("gid")
                portfolio_name = portfolio.get("name", "Unknown Portfolio")
                try:
                    success = try_delete_with_clients(
                        lambda c: c.delete_portfolio(portfolio_gid),
                        f"portfolio {portfolio_name}"
                    )
                    if success:
                        deleted_portfolios += 1
                        print(f"    ✓ Deleted portfolio: {portfolio_name}")
                    else:
                        print(f"    ⚠ No client has permission to delete portfolio '{portfolio_name}'")
                    await asyncio.sleep(0.2)
                except Exception as e:
                    print(f"    ⚠ Error deleting portfolio '{portfolio_name}': {e}")
        except Exception as e:
            print(f"    ⚠ Error fetching portfolios from workspace: {e}")

        # Step 5: Delete custom fields (workspace-level)
        # Query Asana directly for all custom fields in workspace (don't rely on in-memory cache)
        print(f"\n  Deleting custom fields...")
        try:
            workspace_gid = self.config.get("workspace_gid")
            client = all_clients[0]  # Use first client for reading
            custom_fields = client.get_workspace_custom_fields(workspace_gid)
            print(f"    Found {len(custom_fields)} custom field(s) in workspace")

            for field in custom_fields:
                field_gid = field.get("gid")
                field_name = field.get("name", "Unknown Field")
                try:
                    success = try_delete_with_clients(
                        lambda c: c.delete_custom_field(field_gid),
                        f"custom field {field_name}"
                    )
                    if success:
                        deleted_custom_fields += 1
                        print(f"    ✓ Deleted custom field: {field_name}")
                    else:
                        print(f"    ⚠ No client has permission to delete custom field '{field_name}'")
                    await asyncio.sleep(0.2)
                except Exception as e:
                    print(f"    ⚠ Error deleting custom field '{field_name}': {e}")
        except Exception as e:
            print(f"    ⚠ Error fetching custom fields from workspace: {e}")

        # Step 6: Delete tags (workspace-level)
        # Query Asana directly for all tags in workspace (don't rely on in-memory cache)
        print(f"\n  Deleting tags...")
        try:
            workspace_gid = self.config.get("workspace_gid")
            client = all_clients[0]  # Use first client for reading
            tags = client.get_workspace_tags(workspace_gid)
            print(f"    Found {len(tags)} tag(s) in workspace")

            for tag in tags:
                tag_gid = tag.get("gid")
                tag_name = tag.get("name", "Unknown Tag")
                try:
                    success = try_delete_with_clients(
                        lambda c: c.delete_tag(tag_gid),
                        f"tag {tag_name}"
                    )
                    if success:
                        deleted_tags += 1
                        print(f"    ✓ Deleted tag: {tag_name}")
                    else:
                        print(f"    ⚠ No client has permission to delete tag '{tag_name}'")
                    await asyncio.sleep(0.2)
                except Exception as e:
                    print(f"    ⚠ Error deleting tag '{tag_name}': {e}")
        except Exception as e:
            print(f"    ⚠ Error fetching tags from workspace: {e}")

        print(f"\n{'='*60}")
        print(f"Cleanup Summary:")
        print(f"  Total projects: {total_projects}")
        print(f"  Deleted projects: {deleted_projects}")
        print(f"  Deleted tasks: {deleted_tasks}")
        print(f"  Deleted subtasks: {deleted_subtasks}")
        print(f"  Deleted portfolios: {deleted_portfolios}")
        print(f"  Deleted custom fields: {deleted_custom_fields}")
        print(f"  Deleted tags: {deleted_tags}")
        print(f"  Failed: {len(failed_projects)}")
        print(f"{'='*60}\n")

        return {
            "success": len(failed_projects) == 0,
            "deleted_projects": deleted_projects,
            "deleted_tasks": deleted_tasks,
            "deleted_subtasks": deleted_subtasks,
            "deleted_portfolios": deleted_portfolios,
            "deleted_custom_fields": deleted_custom_fields,
            "deleted_tags": deleted_tags,
            "total_projects": total_projects,
            "failed_projects": failed_projects
        }

    def pause(self):
        """Pause the service."""
        self.paused = True
        self.state_manager.update_job_status(self.job_id, "paused")
        print(f"Service paused for job {self.job_id}")

    def resume(self):
        """Resume the service."""
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


# Example usage / CLI
if __name__ == "__main__":
    print("Continuous Asana Data Generator")
    print("=" * 60)

    # This would normally be loaded from config
    config = {
        "industry": "healthcare",
        "duration_days": 7,
        "workspace_gid": "YOUR_WORKSPACE_GID",
        "workspace_name": "Test Workspace",
        "initial_projects": 2,
        "activity_level": "medium",
        "working_hours": "us_workforce",
        "burst_factor": 0.3,
        "comment_frequency": 0.5,
        "task_completion_rate": 20,
        "blocked_task_frequency": 15,
        "blocked_task_duration": 2,
        "privacy": "private"
    }

    # Initialize components
    state_manager = StateManager(".")
    llm_generator = LLMGenerator(os.getenv("ANTHROPIC_API_KEY"))

    # Create client pool (would need actual tokens)
    user_tokens = {
        "Alice": os.getenv("ASANA_TOKEN_ALICE"),
        "Bob": os.getenv("ASANA_TOKEN_BOB"),
    }
    client_pool = AsanaClientPool(user_tokens)

    # Create and run service
    service = ContinuousService(config, state_manager, llm_generator, client_pool)

    # Run async
    try:
        asyncio.run(service.run())
    except KeyboardInterrupt:
        print("\nStopping service...")
        service.stop()
